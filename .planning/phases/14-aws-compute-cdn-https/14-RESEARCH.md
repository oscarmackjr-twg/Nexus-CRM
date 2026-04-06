# Phase 14: AWS Compute, CDN & HTTPS — Research

**Researched:** 2026-04-06
**Domain:** AWS ECS Fargate, ALB, CloudFront, S3, ACM, Route 53, Terraform HCL
**Confidence:** HIGH (all findings verified against existing codebase + official AWS/Terraform docs)

---

## Summary

Phase 14 provisions the compute and delivery layer that makes Nexus CRM publicly accessible. All network, IAM, secrets, and ECR infrastructure is already live from Phase 13. This phase creates four new Terraform modules (ecs, alb, cloudfront, acm) and expands the two environment main.tf files to wire them together. After `terraform apply`, the API will be reachable at `https://<app_domain>/api/v1/health` and the React SPA will be served from CloudFront backed by S3.

The key architectural constraints are already locked in STATE.md and must be treated as non-negotiable inputs:
- `lifecycle { ignore_changes = [task_definition] }` on all ECS services — Terraform owns infra, CI owns image versions
- ACM certificate for CloudFront must be provisioned in `us-east-1` via a provider alias, regardless of the deployment region (ap-southeast-1)
- Secrets injected via the `secrets[]` block only — never the `environment[]` block
- ECS services use rolling deploy with `minimum_healthy_percent = 100`, `maximum_percent = 200`, and the deployment circuit breaker enabled

The phase has no application code changes (entrypoint.sh migration removal was completed in Phase 13 Plan 03). All work is Terraform HCL plus one S3 bucket policy, one CloudFront OAC, and Route 53 alias records.

**Primary recommendation:** Create four focused modules (acm, alb, ecs, cloudfront) and extend the IAM module with the three new Phase 14 bucket ARNs. Wire everything in environment main.tf files. Split execution into three PLAN.md files: (1) ACM + S3 + ALB, (2) ECS cluster + services, (3) CloudFront + Route 53 + IAM wiring.

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-05 | ALB with HTTPS listener, ACM cert (DNS validation), Route 53 A-record alias to ALB | ACM module, ALB module, Route 53 alias A-record |
| INFRA-06 | CloudFront distribution backed by S3 for React SPA; `/api/*` path behavior routes to ALB | CloudFront module, S3 frontend bucket, OAC |
| INFRA-08 | ECS Fargate cluster with API service, Celery worker service, and migration runner task definition; secrets via `secrets[]` only | ECS module with three service/task definitions |
| INFRA-09 | ElastiCache Redis provisioned — already done in Phase 13, no new work | — (prerequisite satisfied) |
| INFRA-10 | IAM role updated with frontend_bucket_arn and assets_bucket_arn once buckets exist | IAM module extension |

---

## Module Breakdown

### New Modules to Create

```
terraform/modules/
├── acm/          NEW — ACM certificate + DNS validation records (us-east-1 cert for CloudFront)
├── alb/          NEW — ALB, HTTP listener, HTTPS listener, target groups
├── ecs/          NEW — ECS cluster, log groups, 3 task definitions, 2 services
└── cloudfront/   NEW — CloudFront distribution, S3 frontend bucket, OAC
```

### Modules to Extend (not rewrite)

```
terraform/modules/iam/   EXTEND — add assets_bucket_arn and frontend_bucket_arn to task/github_actions policies
                                   (variables already exist with default = ""; just needs wiring in environment main.tf)
```

### Modules Already Complete (no changes)

```
terraform/modules/networking/    DONE — alb_security_group_id, api_security_group_id, worker_security_group_id already exported
terraform/modules/rds_proxy/     DONE — proxy_endpoint exported
terraform/modules/elasticache/   DONE — endpoint exported
terraform/modules/secrets/       DONE — all secret ARNs exported (database_url, redis_url, jwt_secret, etc.)
```

---

## Resource Inventory Per Module

### Module: `acm`

**Purpose:** Issue TLS certificate for the custom domain; create DNS validation CNAME records in Route 53.

| Resource | Name pattern | Notes |
|----------|-------------|-------|
| `aws_acm_certificate` | `nexus-crm-{env}-cert` | `domain_name = var.app_domain`; add SAN for `*.{app_domain}` to cover both api and static subdomains if needed |
| `aws_route53_record` (validation) | Auto-named by ACM | `for_each = aws_acm_certificate.this.domain_validation_options` |
| `aws_acm_certificate_validation` | — | Blocks until cert is ISSUED |

**Critical constraint:** CloudFront certificates MUST be in `us-east-1`. This module must use a separate provider alias:

```hcl
# In environment main.tf (provider block, not in the module itself):
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  # Inherits default_tags from the root provider
  default_tags { ... }
}

# In module call:
module "acm" {
  source    = "../../modules/acm"
  providers = { aws = aws.us_east_1 }
  ...
}
```

The ACM module itself does NOT declare the provider alias — it uses `aws` implicitly. The calling environment main.tf passes the aliased provider via `providers` argument. This is the correct Terraform provider alias pattern.

**ALB cert note:** The ALB HTTPS listener needs a separate ACM cert in the deployment region (ap-southeast-1). Options:
- Option A (recommended): Create one cert in ap-southeast-1 covering both `app_domain` and `static_domain`, used by ALB. Create a second cert in us-east-1 for CloudFront. Two `aws_acm_certificate` resources in the same module using different provider aliases — this gets complex.
- Option B (simpler): Split into two modules: `acm_regional` (ap-southeast-1, for ALB) and `acm_cloudfront` (us-east-1, for CloudFront). Both validate against the same Route 53 hosted zone.

**Recommendation:** Option B — two separate ACM module calls, one per region. Keep the module code identical; differentiate only by which provider alias is passed. This is cleaner than managing two providers inside one module.

**Variables:**
```hcl
variable "app_name"    { type = string }
variable "environment" { type = string }
variable "app_domain"  { type = string }    # e.g. "crm.twgasia.com"
variable "route53_zone_id" { type = string }
```

**Outputs:**
```hcl
output "certificate_arn"         # ARN of issued cert (passed to ALB or CloudFront)
output "certificate_domain"      # The domain the cert covers
```

---

### Module: `alb`

**Purpose:** Application Load Balancer that accepts public HTTPS traffic and forwards to ECS API tasks.

| Resource | Notes |
|----------|-------|
| `aws_lb` | `internal = false`; `load_balancer_type = "application"`; placed in public subnets; security group = `alb_security_group_id` from networking module |
| `aws_lb_listener` (HTTP 80) | `default_action` = redirect to HTTPS with `status_code = "HTTP_301"` |
| `aws_lb_listener` (HTTPS 443) | `default_action` = forward to target group; `certificate_arn` = ACM cert ARN (ap-southeast-1 cert) |
| `aws_lb_target_group` | `port = 8000`; `protocol = "HTTP"`; `target_type = "ip"` (required for Fargate); health check on `/health` |
| `aws_lb_listener_rule` | Optional: forward `/api/*` path pattern to the target group (only needed if CloudFront's default origin is S3 and `/api/*` goes to ALB — otherwise the ALB's default action is sufficient) |

**Health check configuration** (critical for ECS rolling deploy success):

```hcl
health_check {
  path                = "/health"          # FastAPI /health endpoint
  port                = "traffic-port"     # 8000
  protocol            = "HTTP"
  healthy_threshold   = 3
  unhealthy_threshold = 3
  timeout             = 5
  interval            = 30
  matcher             = "200"
}
```

The `/health` endpoint exists in FastAPI (`backend/api/main.py`) and returns 200. Do NOT use `/health/ready` as the ALB health check — it checks DB + Redis + S3 and may briefly return non-200 during deploys.

**Variables:**
```hcl
variable "app_name"            { type = string }
variable "environment"         { type = string }
variable "vpc_id"              { type = string }
variable "public_subnet_ids"   { type = list(string) }
variable "alb_security_group_id" { type = string }
variable "acm_certificate_arn" { type = string }  # ap-southeast-1 cert
```

**Outputs:**
```hcl
output "alb_arn"               # Used by ECS target group attachment
output "alb_dns_name"          # Route 53 alias target
output "alb_zone_id"           # Route 53 alias hosted_zone_id (ALB canonical zone)
output "target_group_arn"      # Passed to ECS service load_balancer block
output "https_listener_arn"    # Available for additional listener rules if needed
```

---

### Module: `ecs`

**Purpose:** ECS cluster, CloudWatch log groups, task definitions for API + worker + migration runner, and ECS services for API + worker.

| Resource | Notes |
|----------|-------|
| `aws_ecs_cluster` | `name = "${name_prefix}-cluster"`; enable Container Insights via `setting { name="containerInsights" value="enabled" }` |
| `aws_cloudwatch_log_group` (api) | `/ecs/${name_prefix}-api`; `retention_in_days = 30` |
| `aws_cloudwatch_log_group` (worker) | `/ecs/${name_prefix}-worker`; `retention_in_days = 30` |
| `aws_ecs_task_definition` (api) | See task definition section below |
| `aws_ecs_task_definition` (worker) | Same image as API; command override to celery worker |
| `aws_ecs_task_definition` (migration) | Same image as API; command override to alembic upgrade head |
| `aws_ecs_service` (api) | `desired_count = 1`; load balancer block; `lifecycle { ignore_changes = [task_definition] }` |
| `aws_ecs_service` (worker) | `desired_count = 1`; no load balancer; `lifecycle { ignore_changes = [task_definition] }` |

**ECS task definition — API container:**

```hcl
resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name_prefix}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512    # 0.5 vCPU (staging); var.api_cpu for prod
  memory                   = 1024   # 1 GB (staging); var.api_memory for prod

  execution_role_arn = var.execution_role_arn
  task_role_arn      = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = "${var.api_ecr_repository_url}:placeholder"
      # NOTE: "placeholder" is intentional — ECS will fail to pull this tag.
      # The first real deploy via CI (Phase 15) replaces this with a SHA-tagged image.
      # lifecycle { ignore_changes = [task_definition] } prevents Terraform from
      # ever reverting CI's image update.
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      secrets = [
        { name = "DATABASE_URL",           valueFrom = var.database_url_secret_arn },
        { name = "REDIS_URL",              valueFrom = var.redis_url_secret_arn },
        { name = "SECRET_KEY",             valueFrom = var.jwt_secret_arn },
        { name = "LINKEDIN_CLIENT_ID",     valueFrom = var.linkedin_client_id_secret_arn },
        { name = "LINKEDIN_CLIENT_SECRET", valueFrom = var.linkedin_client_secret_arn }
      ]

      environment = [
        { name = "ENVIRONMENT",    value = var.environment },
        { name = "STORAGE_TYPE",   value = "s3" },
        { name = "CORS_ORIGINS",   value = "https://${var.app_domain}" },
        { name = "METRICS_API_KEY", value = "" }
        # Non-sensitive config only — credentials MUST go in secrets[]
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${local.name_prefix}-api"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health/live || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}
```

**ECS task definition — Worker container:**

```hcl
resource "aws_ecs_task_definition" "worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512

  execution_role_arn = var.execution_role_arn
  task_role_arn      = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = "${var.worker_ecr_repository_url}:placeholder"
      essential = true

      # Override the entrypoint to run celery instead of uvicorn
      command = ["celery", "-A", "backend.workers.celery_app", "worker",
                 "--loglevel=info", "--concurrency=2"]

      secrets = [
        { name = "DATABASE_URL", valueFrom = var.database_url_secret_arn },
        { name = "REDIS_URL",    valueFrom = var.redis_url_secret_arn },
        { name = "SECRET_KEY",   valueFrom = var.jwt_secret_arn }
      ]

      environment = [
        { name = "ENVIRONMENT", value = var.environment }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${local.name_prefix}-worker"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])
}
```

**ECS task definition — Migration runner (one-shot, used by Phase 15 CI):**

```hcl
resource "aws_ecs_task_definition" "migration" {
  family                   = "${local.name_prefix}-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512

  execution_role_arn = var.execution_role_arn
  task_role_arn      = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "migration"
      image     = "${var.api_ecr_repository_url}:placeholder"
      essential = true

      # Runs alembic against DATABASE_URL_SYNC (psycopg DSN derived by entrypoint.sh)
      # entrypoint.sh no longer runs alembic — this is the ONLY migration executor
      command = ["sh", "-c",
        "DATABASE_URL_SYNC=$(echo $DATABASE_URL | sed 's#postgresql+asyncpg://#postgresql+psycopg://#') && alembic upgrade head"
      ]

      secrets = [
        { name = "DATABASE_URL", valueFrom = var.database_url_secret_arn }
      ]

      environment = [
        { name = "ENVIRONMENT", value = var.environment }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${local.name_prefix}-api"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "migration"
        }
      }
    }
  ])
}
```

**ECS service — API:**

```hcl
resource "aws_ecs_service" "api" {
  name            = "${local.name_prefix}-api"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count   # 1 staging, 2 prod
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.api_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "api"
    container_port   = 8000
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [task_definition]
  }

  depends_on = [var.https_listener_arn]
  # depends_on on the listener prevents the service from registering targets
  # before the ALB listener exists (causes ECS service stuck in pending)
}
```

**ECS service — Worker:**

```hcl
resource "aws_ecs_service" "worker" {
  name            = "${local.name_prefix}-worker"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count   # 1 staging, 1 prod
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [var.worker_security_group_id]
    assign_public_ip = false
  }

  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [task_definition]
  }
}
```

**Variables for `ecs` module:**
```hcl
variable "app_name"                     { type = string }
variable "environment"                  { type = string }
variable "aws_region"                   { type = string }
variable "vpc_id"                       { type = string }
variable "private_subnet_ids"           { type = list(string) }
variable "api_security_group_id"        { type = string }
variable "worker_security_group_id"     { type = string }
variable "execution_role_arn"           { type = string }
variable "task_role_arn"                { type = string }
variable "api_ecr_repository_url"       { type = string }
variable "worker_ecr_repository_url"    { type = string }
variable "target_group_arn"             { type = string }
variable "https_listener_arn"           { type = string }
variable "database_url_secret_arn"      { type = string }
variable "redis_url_secret_arn"         { type = string }
variable "jwt_secret_arn"               { type = string }
variable "linkedin_client_id_secret_arn"  { type = string }
variable "linkedin_client_secret_arn"    { type = string }
variable "app_domain"                   { type = string }
variable "api_cpu"                      { type = number; default = 512 }
variable "api_memory"                   { type = number; default = 1024 }
variable "worker_cpu"                   { type = number; default = 256 }
variable "worker_memory"                { type = number; default = 512 }
variable "api_desired_count"            { type = number; default = 1 }
variable "worker_desired_count"         { type = number; default = 1 }
```

**Outputs for `ecs` module:**
```hcl
output "cluster_name"          # Used by Phase 15 CI (aws ecs update-service --cluster)
output "cluster_arn"
output "api_service_name"      # Used by Phase 15 CI (aws ecs update-service --service)
output "worker_service_name"
output "api_task_definition_arn"
output "worker_task_definition_arn"
output "migration_task_definition_arn"  # Used by Phase 15 CI (aws ecs run-task)
```

---

### Module: `cloudfront`

**Purpose:** S3 frontend bucket + CloudFront distribution with OAC (Origin Access Control), SPA routing, and `/api/*` behavior routing to ALB.

| Resource | Notes |
|----------|-------|
| `aws_s3_bucket` | `nexus-crm-{env}-frontend`; block all public access |
| `aws_s3_bucket_policy` | Allow CloudFront OAC read-only access via service principal |
| `aws_cloudfront_origin_access_control` | OAC preferred over legacy OAI since 2022 |
| `aws_cloudfront_distribution` | Two origins: S3 (default) and ALB (for /api/*) |
| `aws_route53_record` (optional) | Can live in its own route53 module, but can also be here |

**S3 bucket — do NOT enable static website hosting:**

Static website hosting is not needed when using CloudFront OAC. Disabling it means the bucket is not publicly accessible at all — only CloudFront can read it. This is the secure, recommended pattern.

```hcl
resource "aws_s3_bucket" "frontend" {
  bucket = "${local.name_prefix}-frontend"
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

**OAC (Origin Access Control) — preferred over OAI:**

OAC is the current AWS standard (OAI is considered legacy since 2022). OAC supports AWS Signature Version 4 which is more secure.

```hcl
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name_prefix}-frontend-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}
```

**S3 bucket policy for OAC:**

```hcl
data "aws_iam_policy_document" "frontend_bucket" {
  statement {
    sid     = "AllowCloudFrontServicePrincipal"
    effect  = "Allow"
    actions = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.this.arn]
    }
  }
}
```

**CloudFront distribution — two behaviors:**

```hcl
resource "aws_cloudfront_distribution" "this" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = [var.static_domain]   # e.g. "static.crm.twgasia.com" or same as app_domain

  # Origin 1: S3 bucket (for static assets)
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-${local.name_prefix}-frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # Origin 2: ALB (for /api/* paths)
  origin {
    domain_name = var.alb_dns_name
    origin_id   = "ALB-${local.name_prefix}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # Default behavior: serve from S3 (SPA assets)
  default_cache_behavior {
    target_origin_id       = "S3-${local.name_prefix}-frontend"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400

    # SPA 404 → serve index.html (handled via custom_error_response, see below)
  }

  # /api/* behavior: proxy to ALB
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    target_origin_id       = "ALB-${local.name_prefix}"
    viewer_protocol_policy = "https-only"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type", "X-Request-ID", "Origin"]
      cookies { forward = "all" }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
    compress     = false
  }

  # /health behavior: proxy to ALB (needed for ALB health checks and monitoring)
  ordered_cache_behavior {
    path_pattern           = "/health*"
    target_origin_id       = "ALB-${local.name_prefix}"
    viewer_protocol_policy = "https-only"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # SPA routing: all 403/404 from S3 → serve index.html
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    acm_certificate_arn      = var.cloudfront_certificate_arn   # us-east-1 cert
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

**Variables for `cloudfront` module:**
```hcl
variable "app_name"                   { type = string }
variable "environment"                { type = string }
variable "static_domain"              { type = string }   # CloudFront alias domain
variable "alb_dns_name"               { type = string }
variable "cloudfront_certificate_arn" { type = string }   # Must be us-east-1 cert
```

**Outputs for `cloudfront` module:**
```hcl
output "distribution_id"              # Phase 15 CI: CloudFront invalidation
output "distribution_domain_name"     # Route 53 alias target
output "distribution_hosted_zone_id"  # Route 53 alias hosted_zone_id (always "Z2FDTNDATAQYW2")
output "frontend_bucket_name"         # Phase 15 CI: S3 sync
output "frontend_bucket_arn"          # IAM module wiring
```

**Note on CloudFront hosted zone ID:** AWS CloudFront distributions always use the canonical hosted zone ID `Z2FDTNDATAQYW2` for Route 53 alias records, regardless of the distribution domain name. This is a hardcoded AWS constant, not an output of the resource. Use `aws_cloudfront_distribution.this.hosted_zone_id` which Terraform resolves to this value automatically.

---

### Route 53 Records

Route 53 records should be defined in the environment main.tf (not a dedicated module), as they require both the ALB outputs and the CloudFront outputs which span multiple modules:

```hcl
# Lookup the hosted zone (must already exist — Phase 14 does not create the zone)
data "aws_route53_zone" "this" {
  name         = var.hosted_zone_name   # e.g. "twgasia.com"
  private_zone = false
}

# app_domain → ALB (e.g. crm.twgasia.com → ALB DNS name)
resource "aws_route53_record" "app" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = var.app_domain
  type    = "A"

  alias {
    name                   = module.alb.alb_dns_name
    zone_id                = module.alb.alb_zone_id
    evaluate_target_health = true
  }
}

# static_domain → CloudFront (e.g. static.crm.twgasia.com or app_domain → CloudFront)
resource "aws_route53_record" "static" {
  zone_id = data.aws_route53_zone.this.zone_id
  name    = var.static_domain
  type    = "A"

  alias {
    name                   = module.cloudfront.distribution_domain_name
    zone_id                = module.cloudfront.distribution_hosted_zone_id
    evaluate_target_health = false
  }
}
```

**Note on domain topology:** The architecture document shows the SPA is served from CloudFront and `/api/*` paths route to ALB via CloudFront behavior. This means `app_domain` can point to CloudFront as the single entry point, with CloudFront proxying `/api/*` to the ALB. The ALB would then also have a separate DNS record (`api.crm.twgasia.com`) for direct access or monitoring. The current STATE.md says "app_domain → ALB, static_domain → CloudFront" which implies two separate domains. Either topology works — the research supports both. The planner should confirm the domain topology with the user before writing Plan 01.

---

## Cross-Module Dependencies

```
networking ──────────────────────────────────────────────────────────┐
  outputs: vpc_id, public_subnet_ids, private_subnet_ids             │
           alb_security_group_id, api_security_group_id              │
           worker_security_group_id                                  │
                                                                     │
secrets ──────────────────────────────────────────────────────────── │ ──┐
  outputs: database_url_secret_arn, redis_url_secret_arn,            │   │
           jwt_secret_arn, linkedin_client_id_secret_arn, etc.       │   │
                                                                     │   │
iam ─────────────────────────────────────────────────────────────── │ ── │ ──┐
  outputs: execution_role_arn, task_role_arn                         │   │   │
                                                                     ↓   ↓   ↓
acm_regional (ap-southeast-1) ──────────────────────→  alb ──────────────────────→ ecs
  outputs: certificate_arn                            outputs: alb_dns_name          ↑
                                                               alb_zone_id           │
acm_cloudfront (us-east-1) ──────────────────────────→ cloudfront                   │
  outputs: certificate_arn                            outputs: distribution_id        │
                                                               distribution_domain    │
                                                               frontend_bucket_arn ──→ iam (update)
                                                                                  
alb.target_group_arn ────────────────────────────────────────────→ ecs
alb.https_listener_arn ──────────────────────────────────────────→ ecs (depends_on)

ECR (inline in environment main.tf) ────────────────────────────→ ecs
  aws_ecr_repository.api.repository_url
  aws_ecr_repository.worker.repository_url

Route 53 records (inline in environment main.tf) consume:
  alb.alb_dns_name + alb.alb_zone_id
  cloudfront.distribution_domain_name + cloudfront.distribution_hosted_zone_id
```

**Apply order (Terraform resolves automatically, but explicit `depends_on` needed for):**
1. `module.acm_regional` and `module.acm_cloudfront` must complete (cert ISSUED) before ALB and CloudFront respectively
2. `aws_acm_certificate_validation` resource in the ACM module blocks until DNS validation completes — DNS validation records must exist in Route 53 first
3. `module.alb` must exist before `module.ecs` (ecs service needs target_group_arn)
4. `module.cloudfront` must exist before Route 53 static record (needs distribution_domain_name)

---

## Environment main.tf Additions

Both `environments/staging/main.tf` and `environments/prod/main.tf` need:

1. New `provider "aws" { alias = "us_east_1" ... }` block
2. New variables: `hosted_zone_name`, `static_domain`, `ecs_api_cpu`, `ecs_api_memory`, `ecs_api_desired_count`, `ecs_worker_desired_count`
3. New module calls: `module.acm_regional`, `module.acm_cloudfront`, `module.alb`, `module.ecs`, `module.cloudfront`
4. Inline Route 53 records: `aws_route53_record.app`, `aws_route53_record.static`
5. Updated `module.iam` call: pass `frontend_bucket_arn = module.cloudfront.frontend_bucket_arn`

**New variables for both environments:**

```hcl
variable "hosted_zone_name" {
  type        = string
  description = "Route 53 hosted zone name (e.g. twgasia.com). Zone must already exist."
}

variable "static_domain" {
  type        = string
  default     = ""
  description = "Domain for CloudFront/static frontend (e.g. static.crm.twgasia.com)"
}

variable "ecs_api_cpu" {
  type    = number
  default = 512
}

variable "ecs_api_memory" {
  type    = number
  default = 1024
}

variable "ecs_api_desired_count" {
  type    = number
  default = 1
}

variable "ecs_worker_desired_count" {
  type    = number
  default = 1
}
```

**Staging terraform.tfvars additions:**
```hcl
app_domain       = "crm-staging.twgasia.com"   # placeholder — confirm with user
hosted_zone_name = "twgasia.com"                # placeholder — confirm with user
static_domain    = "static-staging.twgasia.com" # placeholder
```

**Prod terraform.tfvars additions:**
```hcl
app_domain       = "crm.twgasia.com"
hosted_zone_name = "twgasia.com"
static_domain    = "static.crm.twgasia.com"
ecs_api_desired_count    = 2
ecs_worker_desired_count = 1
ecs_api_cpu    = 1024
ecs_api_memory = 2048
```

---

## Architecture Patterns

### Recommended Terraform Module Structure

```
terraform/modules/
├── acm/
│   ├── main.tf          # aws_acm_certificate, aws_route53_record (validation), aws_acm_certificate_validation
│   ├── variables.tf     # app_name, environment, app_domain, route53_zone_id
│   └── outputs.tf       # certificate_arn, certificate_domain
├── alb/
│   ├── main.tf          # aws_lb, aws_lb_listener x2, aws_lb_target_group
│   ├── variables.tf
│   └── outputs.tf       # alb_arn, alb_dns_name, alb_zone_id, target_group_arn, https_listener_arn
├── ecs/
│   ├── main.tf          # aws_ecs_cluster, log groups, 3 task defs, 2 services
│   ├── variables.tf
│   └── outputs.tf       # cluster_name, api_service_name, worker_service_name, migration_task_definition_arn
└── cloudfront/
    ├── main.tf          # aws_s3_bucket, OAC, aws_cloudfront_distribution, bucket policy
    ├── variables.tf
    └── outputs.tf       # distribution_id, distribution_domain_name, distribution_hosted_zone_id, frontend_bucket_name, frontend_bucket_arn
```

### Pattern: Provider Alias for Cross-Region ACM

The provider alias must be declared in the calling environment's main.tf, NOT inside the module. Modules must not declare provider aliases — they inherit from the caller.

```hcl
# environments/staging/main.tf

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "acm_cloudfront" {
  source    = "../../modules/acm"
  providers = { aws = aws.us_east_1 }
  app_name       = var.app_name
  environment    = var.environment
  app_domain     = var.app_domain
  route53_zone_id = data.aws_route53_zone.this.zone_id
}

module "acm_regional" {
  source    = "../../modules/acm"
  # No providers override — uses default provider (ap-southeast-1)
  app_name       = var.app_name
  environment    = var.environment
  app_domain     = var.app_domain
  route53_zone_id = data.aws_route53_zone.this.zone_id
}
```

**The two ACM certs are for the same domain but in different regions.** This is valid and expected. ACM deduplicates nothing across regions — both certs will be issued.

### Pattern: ECS Service `depends_on` via Variable

The ECS service needs the ALB HTTPS listener to exist before creating the service (otherwise ECS tries to register targets with no listener). Pass `https_listener_arn` as a variable and use `depends_on` in the service resource:

```hcl
# In module ecs/main.tf:
resource "aws_ecs_service" "api" {
  ...
  depends_on = [var.https_listener_arn]  # NOT valid — depends_on can't use variables
}
```

This does NOT work in Terraform — `depends_on` cannot reference module variables. The correct pattern is to pass the `https_listener_arn` value into the container definitions or as a comment, and handle ordering via the `aws_lb_listener_rule` or by using the target group ARN (which already implies the listener exists). The ALB listener registers the target group, and ECS service references the target group — Terraform's dependency graph handles this correctly without explicit `depends_on`.

**Correct approach:** Pass `target_group_arn` to the ECS module. Terraform will automatically create the ALB target group before the ECS service because the ECS service references it.

### Pattern: Secrets Injection via `secrets[]`

All credentials must use the `secrets[]` block. The `environment[]` block must be used ONLY for non-sensitive config.

```hcl
# CORRECT
secrets = [
  { name = "DATABASE_URL", valueFrom = "arn:aws:secretsmanager:..." }
]

# WRONG — exposes credentials in CloudWatch logs and AWS console
environment = [
  { name = "DATABASE_URL", value = "postgresql+asyncpg://user:pass@host/db" }
]
```

The IAM execution role already has `secretsmanager:GetSecretValue` permission for `/nexus/{environment}/*` (from Phase 13 IAM module). No new IAM changes needed for secrets injection — just ensure `valueFrom` references the correct ARN.

### Anti-Patterns to Avoid

- **OAI (Origin Access Identity):** Do not use `aws_cloudfront_origin_access_identity`. OAC is the current standard. OAI is legacy and does not support SigV4.
- **S3 static website hosting:** Do not enable `aws_s3_bucket_website`. CloudFront with OAC reads directly from the S3 REST API endpoint, not the website endpoint. The 404→index.html SPA routing is handled by `custom_error_response` in CloudFront, not the S3 website config.
- **Placing ACM cert in wrong region:** The CloudFront cert MUST be in us-east-1. Placing it in ap-southeast-1 will cause CloudFront to reject the cert with a cryptic "certificate not found" error during distribution creation.
- **`latest` image tag in task definition:** The placeholder image tag should not be `latest` — ECR has `IMMUTABLE` tags, and `latest` would also be pinned at task start anyway. Use `placeholder` as the tag string, making it obvious this is not a real runnable image. Phase 15 CI will replace it on first deploy.
- **ECS service triggering rolling restarts on every `terraform apply`:** The `lifecycle { ignore_changes = [task_definition] }` block is mandatory. Without it, any Terraform resource change (even tagging) causes ECS to start a rolling restart.
- **Circular dependency in OAC bucket policy:** The S3 bucket policy that allows CloudFront OAC access requires the CloudFront distribution ARN. But the CloudFront distribution requires the S3 bucket to exist. This is not circular — bucket policy can reference the distribution ARN after the distribution is created. Terraform resolves this correctly.
- **ALB health check on `/health/ready`:** The readiness check hits DB + Redis + S3. During a rolling deploy, new tasks may fail this check before their connections warm up, causing the deploy to stall. Use `/health/live` for the ALB health check (fast, no dependencies).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SPA 404 routing | Custom Lambda@Edge | CloudFront `custom_error_response` 403/404 → index.html | Lambda@Edge adds latency, cost, and complexity; `custom_error_response` is free and synchronous |
| ACM cert DNS validation | Manual CNAME management | `aws_acm_certificate_validation` with `for_each` over `domain_validation_options` | Handles multi-SAN validation automatically; auto-creates records |
| ALB access logs parsing | Custom log processors | CloudWatch Container Insights on ECS cluster | Container Insights already configured in `aws_ecs_cluster` |
| CloudFront cache invalidation | Custom Lambda | `aws cloudfront create-invalidation` in Phase 15 CI workflow | CLI is sufficient; Phase 14 creates the distribution, Phase 15 uses the distribution ID |
| ECS rolling deploy health gating | Custom polling scripts | ALB health check + ECS deployment circuit breaker | Circuit breaker (`enable=true, rollback=true`) handles this automatically |

---

## Common Pitfalls

### Pitfall 1: ACM Certificate in Wrong Region
**What goes wrong:** `aws_cloudfront_distribution` fails to create with error "The specified SSL certificate doesn't exist, isn't in us-east-1 region, isn't valid, or doesn't include a valid certificate chain."
**Why it happens:** CloudFront is a global service that only reads certificates from us-east-1.
**How to avoid:** Use provider alias `aws.us_east_1` for the CloudFront ACM module call. Verify by running `terraform plan` and confirming the certificate resource shows `provider: aws.us_east_1`.
**Warning signs:** Plan output shows the ACM cert being created in ap-southeast-1 for the cloudfront module.

### Pitfall 2: ECS Service Stuck in Pending / First Deploy Fails
**What goes wrong:** After `terraform apply`, ECS services show "pending" indefinitely. The `desired_count = 1` task cannot start because the placeholder image tag doesn't exist in ECR.
**Why it happens:** The task definition uses `{ecr_url}:placeholder` which does not exist as a real image in ECR.
**How to avoid:** This is expected behavior — Phase 15 CI will push the first real image and trigger the first deploy. To avoid confusion: (a) set `desired_count = 0` in Terraform (use `var.api_desired_count` and set it to 0 in tfvars for initial apply, then set to 1 once first image is pushed); OR (b) document that services will show "pending" until first CI run. Option (b) is simpler.
**Warning signs:** `aws ecs describe-services` shows `PENDING` count > 0 and `RUNNING` count = 0 with "CannotPullContainerError" in stopped tasks.

### Pitfall 3: ACM Certificate Validation Timeout
**What goes wrong:** `terraform apply` hangs for 30–60 minutes or times out waiting for ACM certificate validation.
**Why it happens:** ACM DNS validation requires the CNAME record to be present in the Route 53 hosted zone. If the domain's NS records don't point to Route 53, the CNAME will never be detected by ACM.
**How to avoid:** Confirm the Route 53 hosted zone controls DNS for the domain before running `terraform apply`. If the domain is registered with an external registrar (not Route 53), the NS records must be updated to point to the Route 53 zone's name servers.
**Warning signs:** `aws acm describe-certificate --certificate-arn <arn>` shows `DomainValidationOptions[].ValidationStatus = "PENDING_VALIDATION"` for more than 5 minutes after the CNAME record appears in Route 53.

### Pitfall 4: CloudFront `/api/*` Forwarding Strips Required Headers
**What goes wrong:** API calls return 401 even though the Authorization header is set.
**Why it happens:** CloudFront by default does NOT forward `Authorization` headers to origins. The default cache behavior caches based on the URL only.
**How to avoid:** The `/api/*` ordered_cache_behavior must explicitly forward `Authorization` in `forwarded_values.headers`. This is already included in the research example above.
**Warning signs:** API calls succeed when hitting the ALB directly (via ALB DNS name) but fail when routed through CloudFront.

### Pitfall 5: S3 Bucket Policy References Non-Existent Distribution ARN
**What goes wrong:** `terraform apply` fails with "Invalid principal in policy" or "MalformedPolicy" when creating the S3 bucket policy.
**Why it happens:** The bucket policy references `aws_cloudfront_distribution.this.arn`, but if Terraform tries to create the bucket policy before the distribution is created, the ARN is unknown.
**How to avoid:** Terraform resolves this via the dependency graph — the bucket policy resource has an implicit dependency on the distribution. Ensure the bucket policy resource is in the same module (cloudfront) or that the distribution ARN is passed as a variable. Do NOT use a `data` source to look up the distribution ARN in the bucket policy — use a direct resource reference.

### Pitfall 6: ECS Task Cannot Pull from ECR (NAT Gateway / VPC Endpoint)
**What goes wrong:** ECS Fargate tasks cannot pull images from ECR because private subnet tasks have no route to the internet.
**Why it happens:** ECS tasks in private subnets require either (a) a NAT gateway or (b) VPC endpoints for ECR (both `com.amazonaws.{region}.ecr.dkr` and `com.amazonaws.{region}.ecr.api` and `com.amazonaws.{region}.s3`).
**How to avoid:** Phase 13 already provisions NAT gateways (1 for staging, 2 for prod) via `nat_gateway_count`. Private subnets have routes to NAT gateway. This pitfall is ALREADY MITIGATED by the existing networking module. Document this for awareness.
**Warning signs:** ECS stopped tasks with reason `CannotPullContainerError: ... request canceled while waiting for connection`.

### Pitfall 7: Route 53 Hosted Zone Not Owned
**What goes wrong:** `data "aws_route53_zone"` fails with "no matching Route53 Hosted Zone found" or ACM validation records are created in the wrong zone.
**Why it happens:** The Route 53 hosted zone for the domain does not exist in the AWS account, or the `hosted_zone_name` variable has a trailing dot or incorrect casing.
**How to avoid:** Verify the zone exists before running `terraform apply`:
```bash
aws route53 list-hosted-zones --query 'HostedZones[?Name==`twgasia.com.`]'
```
Note: Route 53 zone names include a trailing dot in the AWS API — the `data "aws_route53_zone"` resource handles this automatically when you omit the dot.

---

## Secrets Injection Reference

The secrets module (Phase 13) already created shell secrets for all these paths. The ECS module needs their ARNs:

| Env var in container | Secrets Manager key | Secret ARN output |
|---------------------|--------------------|--------------------|
| `DATABASE_URL` | `/nexus/{env}/database_url` | `module.secrets.secret_arns.database_url` |
| `REDIS_URL` | `/nexus/{env}/redis_url` | `module.secrets.secret_arns.redis_url` |
| `SECRET_KEY` | `/nexus/{env}/jwt_secret` | `module.secrets.secret_arns.jwt_secret` |
| `LINKEDIN_CLIENT_ID` | `/nexus/{env}/linkedin_client_id` | `module.secrets.secret_arns.linkedin_client_id` |
| `LINKEDIN_CLIENT_SECRET` | `/nexus/{env}/linkedin_client_secret` | `module.secrets.secret_arns.linkedin_client_secret` |

**Important:** The `secrets[]` block `valueFrom` accepts the secret ARN, not the secret name. Use the ARN from `module.secrets.secret_arns.*`.

**Also important:** The `secrets[]` block fetches the secret value at task start. If the secret value is empty (the shell resource has no value set), ECS will fail to start the task with `ResourceInitializationError: unable to pull secrets or registry auth`. The ops runbook for Phase 14 must include populating all secret values before running `terraform apply` for ECS.

---

## Plan Structure Recommendation

Split Phase 14 into three PLAN.md files:

### Plan 14-01: ACM Certificates + S3 Frontend Bucket + ALB

**Why:** ACM certificates take time to validate (typically 5–30 minutes). Starting cert validation as early as possible prevents the overall apply from stalling. ALB depends on the regional cert. S3 frontend bucket has no dependencies — it can be created early.

**Files created:**
- `terraform/modules/acm/main.tf`, `variables.tf`, `outputs.tf`
- `terraform/modules/alb/main.tf`, `variables.tf`, `outputs.tf`
- `terraform/modules/cloudfront/main.tf` — S3 bucket and OAC only (no distribution yet; wait for cert)
- `terraform/environments/staging/main.tf` — add provider alias, acm_regional, acm_cloudfront, alb, Route 53 data source
- `terraform/environments/staging/variables.tf` — add hosted_zone_name, static_domain

**Must-have outputs from this plan:**
- `module.alb.target_group_arn` → consumed by Plan 14-02 (ECS)
- `module.alb.alb_dns_name` → consumed by Plan 14-03 (CloudFront origin) and Route 53
- `module.acm_cloudfront.certificate_arn` → consumed by Plan 14-03 (CloudFront viewer cert)

**Acceptance criteria:**
- `terraform validate` passes in both environments
- ALB listener on 80 redirects to HTTPS
- ALB health check returns 200 on `/health` (this will fail until ECS tasks are running — that's expected)

---

### Plan 14-02: ECS Cluster, Task Definitions, and Services

**Why:** ECS module is the most complex (3 task defs, 2 services, log groups, secrets injection). Isolating it allows focused review of the container definitions and secrets wiring.

**Files created:**
- `terraform/modules/ecs/main.tf`, `variables.tf`, `outputs.tf`
- `terraform/environments/staging/main.tf` — add module.ecs call
- `terraform/environments/staging/variables.tf` — add ecs_api_cpu, ecs_api_memory, etc.
- `terraform/environments/staging/outputs.tf` — add cluster_name, api_service_name, worker_service_name, migration_task_definition_arn
- Mirror all of the above for prod

**Must-have outputs from this plan:**
- `module.ecs.cluster_name` → Phase 15 CI
- `module.ecs.api_service_name` → Phase 15 CI
- `module.ecs.worker_service_name` → Phase 15 CI
- `module.ecs.migration_task_definition_arn` → Phase 15 CI

**Acceptance criteria:**
- ECS cluster exists and is visible in AWS console
- API and worker services created with `desired_count = 1` (tasks will be pending — expected)
- Migration task definition exists and is runnable via `aws ecs run-task`
- `terraform validate` still passes
- CloudWatch log groups exist for both services

---

### Plan 14-03: CloudFront Distribution + Route 53 Records + IAM Update

**Why:** CloudFront distribution depends on the us-east-1 ACM cert (from Plan 14-01) being in ISSUED state. Separating this allows explicit confirmation of cert issuance before creating the distribution. Route 53 records go last because they depend on both the ALB DNS name (Plan 14-01) and CloudFront distribution domain (this plan).

**Files created:**
- `terraform/modules/cloudfront/main.tf` — add distribution and bucket policy (bucket already exists from Plan 14-01)
- `terraform/environments/staging/main.tf` — wire CloudFront distribution, add Route 53 records inline, update module.iam with frontend_bucket_arn
- `terraform/environments/staging/outputs.tf` — add distribution_id, frontend_bucket_name, cloudfront_domain
- Mirror all of the above for prod

**Must-have outputs from this plan:**
- `module.cloudfront.distribution_id` → Phase 15 CI (CloudFront invalidation)
- `module.cloudfront.frontend_bucket_name` → Phase 15 CI (S3 sync)
- All Route 53 records exist pointing to ALB and CloudFront

**Acceptance criteria:**
- CloudFront distribution is in `Deployed` state
- `https://<app_domain>/health` returns 200 (via ALB, once tasks are running)
- `https://<static_domain>/` returns 200 (empty bucket returns 403 → index.html via custom_error_response → index.html doesn't exist yet, returns 200 with placeholder)
- Route 53 A records exist for app_domain and static_domain
- IAM github_actions role has S3 write + CloudFront invalidation permissions

---

## Environment Availability

| Dependency | Required By | Available | Notes |
|------------|-------------|-----------|-------|
| Route 53 hosted zone for `twgasia.com` | ACM validation, Route 53 records | Unknown — must confirm | Zone must exist and have NS authority before `terraform apply` |
| Domain registrar NS delegation | ACM DNS validation | Unknown — must confirm | NS records at registrar must point to Route 53 zone |
| Secret values populated in Secrets Manager | ECS task startup | Unknown — must confirm | `/nexus/staging/*` shell secrets from Phase 13; values must be populated before first ECS deploy |
| Terraform `>= 1.10` | All modules | Confirmed (from `required_version` in existing envs) | Already locked in codebase |
| AWS provider `~> 6.0` | All modules | Confirmed | Already locked in existing environments |
| NAT Gateways (private subnet egress) | ECS ECR pull | Confirmed (Phase 13) | `nat_gateway_count = 1` staging, `= 2` prod |
| ECR repositories | ECS task definitions | Confirmed (Phase 13) | Both api and worker repos exist with IMMUTABLE tags |

**Missing dependencies with no fallback:**
- Route 53 hosted zone authority (must be confirmed before Plan 14-01 apply)
- Secret values in Secrets Manager (must be populated before Plan 14-02 apply)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CloudFront OAI (Origin Access Identity) | CloudFront OAC (Origin Access Control) | AWS, Nov 2022 | OAC uses SigV4; OAI is legacy and no longer recommended. Use `aws_cloudfront_origin_access_control`. |
| S3 static website endpoint as CloudFront origin | S3 REST API endpoint (bucket_regional_domain_name) | Required for OAC | OAC only works with the REST API endpoint, not the website endpoint. `bucket_regional_domain_name` is the correct attribute. |
| `aws_ecs_task_definition` with ARN pinning | `lifecycle { ignore_changes = [task_definition] }` on service | ECS best practice, ~2022 | Prevents Terraform from reverting CI-managed image updates. |
| DynamoDB for Terraform state locking | S3 native file locking (`use_lockfile = true`) | Terraform 1.10 | Eliminates DynamoDB dependency. Already in use (Phase 13). |
| Manual ACM DNS validation | `aws_acm_certificate_validation` with `for_each` over `domain_validation_options` | Terraform AWS provider v4+ | Automates record creation and blocks until cert is issued. |

**Deprecated/outdated:**
- `aws_cloudfront_origin_access_identity`: legacy, replaced by OAC. Do not use.
- ECS `network_mode = "bridge"`: Not applicable to Fargate. Fargate requires `awsvpc`.
- ACM `validation_method = "EMAIL"`: DNS validation is strongly preferred — email validation requires access to domain admin mailbox and times out faster.

---

## Open Questions

1. **Domain topology: single domain vs. split domain**
   - What we know: STATE.md says "app_domain → ALB, static_domain → CloudFront". ARCHITECTURE.md shows CloudFront serves the SPA with /api/* behavior routing to ALB, suggesting a single-domain approach where everything goes through CloudFront.
   - What's unclear: Does the team want `crm.twgasia.com` to resolve to CloudFront (which internally routes /api/* to ALB), or does the team want two separate domains (`crm.twgasia.com` → ALB for API, `static.crm.twgasia.com` → CloudFront for SPA)?
   - Recommendation: Single-domain (all through CloudFront) is simpler for users and avoids CORS issues. But it adds CloudFront latency to API calls (~1–5ms). Confirm before writing Plan 14-01.

2. **Exact domain values**
   - What we know: Research used `crm.twgasia.com` as a placeholder.
   - What's unclear: Is `twgasia.com` the actual domain? Is the Route 53 hosted zone already created in the AWS account?
   - Recommendation: Confirm before Plan 14-01 creates Route 53 data sources and ACM certificates.

3. **ECS `desired_count` during initial Terraform apply**
   - What we know: With `desired_count = 1` and a placeholder image, ECS tasks will enter PENDING and fail with CannotPullContainerError.
   - What's unclear: Should `desired_count = 0` be the initial Terraform value (then CI sets it to 1), or should we accept the pending state?
   - Recommendation: `desired_count = 0` avoids confusion and alarms. Phase 15 CI sets it to the running value. Add `ignore_changes = [desired_count, task_definition]` if using this approach.

4. **Assets bucket (for S3 file uploads by the API)**
   - What we know: `backend/api/main.py` references `STORAGE_TYPE == "s3"` for a readiness check, and the IAM module has `assets_bucket_arn` variable. Phase 13 SUMMARY mentions an assets bucket.
   - What's unclear: Does Phase 14 need to create the assets bucket, or was it created in Phase 13? Check `terraform/modules/secrets/main.tf` and any Phase 13 S3 resources.
   - Recommendation: If no assets bucket exists in Phase 13, create it in Plan 14-01 alongside the frontend bucket.

---

## Sources

### Primary (HIGH confidence — derived from codebase)
- `terraform/modules/networking/main.tf` — exact security groups and their IDs; all outputs verified
- `terraform/modules/networking/outputs.tf` — exact output names consumed by new modules
- `terraform/environments/staging/outputs.tf` — exact outputs Phase 14 must extend
- `terraform/environments/staging/variables.tf` + `prod/variables.tf` — Phase 14 placeholder vars already declared
- `.planning/STATE.md` — locked architectural decisions (lifecycle ignore_changes, us-east-1 ACM, lifecycle block)
- `.planning/research/SUMMARY.md` — build order, pitfalls, and critical constraints
- `.planning/codebase/ARCHITECTURE.md` — health endpoints, middleware, container entrypoint
- `.planning/codebase/STACK.md` — confirmed platform choices

### Secondary (MEDIUM confidence — standard AWS/Terraform patterns)
- AWS docs: CloudFront OAC (`aws_cloudfront_origin_access_control`) — OAI replaced by OAC since Nov 2022
- AWS docs: ACM certificate regions — CloudFront requires us-east-1
- Terraform AWS provider docs: `aws_ecs_service` `lifecycle { ignore_changes }` pattern
- Terraform AWS provider docs: `aws_lb_target_group` with `target_type = "ip"` for Fargate

---

## Metadata

**Confidence breakdown:**
- Module structure: HIGH — derived directly from existing modules and codebase conventions
- ECS task definitions: HIGH — container definitions follow existing architecture (port 8000, /health endpoint, secrets manager paths all confirmed)
- ALB configuration: HIGH — security groups exist (networking module), health check path confirmed (/health in FastAPI)
- ACM + CloudFront: MEDIUM-HIGH — us-east-1 constraint confirmed; OAC pattern is current standard; specific Terraform resource attribute names verified against provider docs
- Route 53: MEDIUM — depends on hosted zone existing in account (not yet confirmed)
- Domain values: LOW — placeholder values used; must be confirmed with user

**Research date:** 2026-04-06
**Valid until:** 2026-05-06 (stable domain — AWS provider minor versions change; re-verify `~> 6.0` submodule versions if > 30 days elapse)
