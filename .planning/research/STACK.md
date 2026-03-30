# Stack Research: Cloud Deployment

**Project:** Nexus CRM — v1.2 Cloud Deployment
**Researched:** 2026-03-29
**Scope:** Terraform providers + modules for AWS ECS Fargate, RDS, ElastiCache, ALB, ACM, Secrets Manager, ECR, Route 53, and Azure warm failover (PostgreSQL Flexible Server + ACI).
**Overall Confidence:** MEDIUM-HIGH — provider major versions confirmed; module patch versions change frequently, pin to minor (`~> X.Y`) not exact.

---

## Terraform Providers & Versions

| Provider | Version Constraint | Latest Confirmed | Purpose |
|----------|--------------------|-----------------|---------|
| `hashicorp/aws` | `~> 6.0` | 6.38.0 (Mar 2026) | All AWS resources |
| `hashicorp/azurerm` | `~> 4.0` | 4.66.0 (Mar 2026) | All Azure resources |
| `hashicorp/random` | `~> 3.6` | 3.6.x | Random suffixes for globally unique resource names |
| `hashicorp/tls` | `~> 4.0` | 4.0.x | TLS helpers if needed for local cert generation |

**Terraform CLI:** Pin to `~> 1.10` (stable 1.x series, widely supported by all modules). Use `.terraform-version` file or `required_version = ">= 1.10, < 2.0"` in every root module. Terraform 1.14.x is the latest stable as of research date.

**Decision — Terraform vs OpenTofu:** Use HashiCorp Terraform `~> 1.10`. The BSL license does not restrict internal/private-use deployments. The module ecosystem, GitHub Actions integrations, and all official AWS docs are Terraform-first. OpenTofu `1.11.x` is a valid fork but adds operational risk for a first cloud deployment with no team experience on it.

**Shared provider block (both providers live in separate root modules — see Workspace Structure below):**

```hcl
terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "nexus-crm"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
```

---

## AWS Resources (Terraform)

Use the `terraform-aws-modules` collection throughout. These are the de facto community standard — maintained, Fargate-aware, and production-tested. Rolling equivalent resources by hand adds 150–300 lines of boilerplate per service with no upside.

### VPC

| Item | Value |
|------|-------|
| Module | `terraform-aws-modules/vpc/aws` |
| Version constraint | `~> 6.6` |
| Latest confirmed | 6.6.0 (published Jan 8 2026) |
| Key config | 3 AZs minimum; public subnets for ALB; private subnets for ECS tasks, RDS, ElastiCache; no direct internet egress on private subnets (NAT gateway) |

The module handles NAT gateways, route tables, DB subnet groups, and subnet tagging (required for ECS service discovery and ALB target group registration) in a single call.

### ECS Fargate

| Item | Value |
|------|-------|
| Module | `terraform-aws-modules/ecs/aws` |
| Version constraint | `~> 7.5` |
| Latest confirmed | 7.5.0 (published Mar 18 2026) |
| Capacity provider | `FARGATE` for backend + frontend; `FARGATE_SPOT` for Celery worker (60-80% cost reduction, acceptable for async tasks) |
| Services | `backend` (FastAPI on port 8000), `frontend` (nginx serving Vite build on port 80), `celery` (Celery worker, no inbound port) |

**Secret injection pattern — use `secrets` block, not `environment`:**

```hcl
container_definitions = {
  backend = {
    image = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
    port_mappings = [{ containerPort = 8000, protocol = "tcp" }]
    environment = [
      { name = "ENV", value = var.environment }
    ]
    secrets = [
      { name = "DATABASE_URL",    valueFrom = aws_secretsmanager_secret.db_url.arn },
      { name = "REDIS_URL",       valueFrom = "${aws_secretsmanager_secret.app.arn}:REDIS_URL::" },
      { name = "JWT_SECRET_KEY",  valueFrom = "${aws_secretsmanager_secret.app.arn}:JWT_SECRET_KEY::" }
    ]
  }
}
```

The ECS **execution role** (not the task role) needs `secretsmanager:GetSecretValue` scoped to those ARNs. Values in `environment` blocks appear in the AWS console and CloudWatch logs — never put credentials there.

**Alembic migration task:** Run as a one-off ECS task before deploying services. Same backend image, command overridden to `["alembic", "upgrade", "head"]`. The CI pipeline waits for the task to exit 0 before proceeding with the rolling service deploy.

### RDS PostgreSQL

| Item | Value |
|------|-------|
| Module | `terraform-aws-modules/rds/aws` |
| Version constraint | `~> 6.10` |
| Latest confirmed | Updated Mar 27 2026 (exact patch — check registry at deploy time) |
| Engine | `postgres`, version `17` (use `postgres17` parameter group family) |
| Instance class | `db.t4g.medium` (staging) / `db.r8g.large` (prod) — Graviton for cost |
| Storage type | `gp3` (not gp2 — better baseline IOPS at same cost) |
| Multi-AZ | `true` for prod; `false` for staging |
| Backup retention | 7 days (prod); 1 day (staging) |
| Parameter group | `rds.logical_replication = 1` is **required** — enables the PostgreSQL WAL slot that Azure DMS uses for cross-cloud replication to the warm failover. Also set `max_wal_senders = 10`, `max_replication_slots = 5`. These require an RDS reboot on first apply. |

### ElastiCache Redis

| Item | Value |
|------|-------|
| Module | `terraform-aws-modules/elasticache/aws` |
| Version constraint | `~> 1.0` (check registry — module was refactored in late 2024; confirm 1.x is latest stable) |
| Engine | Redis OSS 7.x (latest LTS available on ElastiCache) |
| Node type | `cache.t4g.small` (staging) / `cache.r7g.large` (prod) |
| Mode | Single-node replication group with 1 read replica (prod); single node (staging) |
| Encryption | `transit_encryption_enabled = true`; store auth token in Secrets Manager |

Alternative: Use `aws_elasticache_replication_group` directly if the module abstraction adds complexity. Both are valid — module is preferred for consistency.

### ALB (Application Load Balancer)

| Item | Value |
|------|-------|
| Module | `terraform-aws-modules/alb/aws` |
| Version constraint | `~> 9.0` |
| Listeners | Port 80 → permanent redirect to 443; Port 443 → forward to target groups |
| Target groups | `backend` (port 8000, path `/health`); `frontend` (port 80, path `/`) |
| ALB handles TLS | ECS containers communicate over HTTP internally — no end-to-end TLS complexity |

### ACM (TLS Certificate)

| Item | Value |
|------|-------|
| Module | `terraform-aws-modules/acm/aws` |
| Version constraint | `~> 5.0` |
| Latest confirmed | 5.x published Jan 8 2026 |
| Validation method | DNS (automated via Route 53 — no email dependency, certificate auto-renews) |
| Coverage | `nexus-crm.example.com` + `*.nexus-crm.example.com` in a single cert |

### Route 53

| Resource | Purpose |
|----------|---------|
| `aws_route53_zone` | One hosted zone per environment OR a shared zone with environment-prefixed A records |
| `aws_route53_record` (A alias) | Points app domain to ALB DNS name |
| `aws_route53_health_check` | HTTP/HTTPS check on ALB; feeds failover routing policy |
| `aws_route53_record` (failover PRIMARY) | Primary record with `health_check_id` attached |
| `aws_route53_record` (failover SECONDARY) | Secondary record pointing to Azure ACI public IP |

Configuring Route 53 failover routing is the mechanism that makes the Azure warm standby near-automatic — if the ALB health check fails for 3 consecutive intervals (default 30s each = ~90s detection), DNS flips to Azure without manual intervention.

### ECR (Container Registry)

| Resource | Notes |
|----------|-------|
| `aws_ecr_repository` | One per image: `nexus-crm-backend`, `nexus-crm-frontend`, `nexus-crm-celery` |
| `aws_ecr_lifecycle_policy` | Keep last 10 tagged images; expire untagged images after 1 day — prevents unbounded storage cost |
| `image_scanning_configuration` | `scan_on_push = true` for basic vulnerability awareness |

No module needed — `aws_ecr_repository` is a simple resource with few attributes.

### Secrets Manager

| Resource | Notes |
|----------|-------|
| `aws_secretsmanager_secret` | One logical secret per group: `nexus-crm/{env}/app` (JWT secret, etc.), `nexus-crm/{env}/db`, `nexus-crm/{env}/redis` |
| `aws_secretsmanager_secret_version` | **Do not set secret values in Terraform if you want them out of state.** Create the `aws_secretsmanager_secret` resource (gets ARN into state), populate values via AWS CLI or CI post-apply. |

**Critical:** Terraform state stores any `secret_string` value in plaintext. Use remote state in S3 with KMS encryption and strict IAM policies. Alternatively, create the secret shell in Terraform and populate values out-of-band.

### S3 + DynamoDB (Terraform Remote State — Bootstrap First)

| Resource | Notes |
|----------|-------|
| `aws_s3_bucket` | Versioned, KMS-encrypted; key pattern: `aws/{env}/terraform.tfstate` |
| `aws_dynamodb_table` | `LockID` hash key, `PAY_PER_REQUEST` billing — state locking |

Bootstrap this with a separate throwaway local-state Terraform config before standing up the main infrastructure. Once created, migrate to S3 backend.

```hcl
terraform {
  backend "s3" {
    bucket         = "nexus-crm-tfstate-{aws-account-id}"
    key            = "aws/prod/terraform.tfstate"
    region         = "ap-southeast-1"
    encrypt        = true
    kms_key_id     = "alias/terraform-state"
    dynamodb_table = "nexus-crm-tfstate-lock"
  }
}
```

---

## Azure Resources (Terraform)

Azure is warm standby only — pre-deployed and idle. It receives no traffic until cutover. Size everything at minimum SKU; upgrade at failover if load demands it.

### Resource Group

```hcl
resource "azurerm_resource_group" "failover" {
  name     = "nexus-crm-failover-${var.environment}"
  location = "Southeast Asia"  # Singapore — matches AWS ap-southeast-1
}
```

### Azure PostgreSQL Flexible Server

| Item | Value |
|------|-------|
| Resource | `azurerm_postgresql_flexible_server` |
| SKU | `GP_Standard_D2s_v3` (2 vCPU / 8 GB RAM) — upgrade to D4s_v3 at cutover |
| PostgreSQL version | `17` (must match AWS RDS primary) |
| Storage | 32 GB minimum, auto-grow enabled |
| Backup retention | 7 days |
| Replication source | Replica fed from AWS RDS via Azure DMS logical replication (see Integration Points) |
| **Do NOT use** | Azure PostgreSQL Single Server — retired March 2025, unavailable for new deployments |

No battle-tested community module exists for Flexible Server comparable to `terraform-aws-modules/rds`. Use `azurerm_postgresql_flexible_server` directly. The Azure Verified Module (`Azure/terraform-azurerm-avm-res-dbforpostgresql-flexibleserver`) exists but is newer and less widely tested.

```hcl
resource "azurerm_postgresql_flexible_server" "failover" {
  name                   = "nexus-crm-pg-failover-${var.environment}"
  resource_group_name    = azurerm_resource_group.failover.name
  location               = azurerm_resource_group.failover.location
  version                = "17"
  delegated_subnet_id    = azurerm_subnet.pg.id
  private_dns_zone_id    = azurerm_private_dns_zone.pg.id
  administrator_login    = var.pg_admin_user
  administrator_password = var.pg_admin_password  # inject from Key Vault post-apply
  storage_mb             = 32768
  sku_name               = "GP_Standard_D2s_v3"
  backup_retention_days  = 7
  geo_redundant_backup_enabled = false  # warm standby, not geo-HA
}
```

### Azure Container Instances (ACI)

| Item | Value |
|------|-------|
| Resource | `azurerm_container_group` |
| Containers | `backend` (FastAPI), `frontend` (nginx), `celery` (Celery worker) |
| Image source | Azure Container Registry (ACR) — see Integration Points |
| CPU / Memory (standby) | 0.5 vCPU / 1 GB per container — scale up at cutover |
| Restart policy | `Always` |
| OS type | `Linux` |

ACI is the right choice for warm standby: no cluster overhead, per-second billing, simple Terraform resource. AKS is overkill for a container group that may never receive production traffic.

### Azure Container Registry (ACR)

| Resource | Notes |
|----------|-------|
| `azurerm_container_registry` | `Basic` SKU for warm standby — upgrade to `Standard` at cutover |
| Admin enabled | `false` — use managed identity for ACI pull |

Push images to ACR from CI on every merge (alongside pushing to ECR). ACI pulls from ACR using managed identity — no cross-cloud credential rotation required.

### Azure Key Vault

| Resource | Notes |
|----------|-------|
| `azurerm_key_vault` | Stores connection strings, JWT secret, Redis URL for ACI containers |
| `azurerm_key_vault_secret` | One secret per env var; structure mirrors AWS Secrets Manager |

ACI containers reference Key Vault secrets at startup via managed identity. The JWT secret must be identical between AWS Secrets Manager and Azure Key Vault (sessions started on AWS must decode on Azure after failover).

### Azure VNet + Private DNS

| Resource | Notes |
|----------|-------|
| `azurerm_virtual_network` | Private network for ACI and PostgreSQL Flexible Server |
| `azurerm_subnet` (delegated) | PostgreSQL Flexible Server requires a dedicated delegated subnet |
| `azurerm_subnet` (ACI) | Separate subnet for container group |
| `azurerm_private_dns_zone` | Required for Flexible Server private DNS resolution (`privatelink.postgres.database.azure.com`) |

---

## Supporting Tools

### GitHub Actions — CI/CD Pipeline

| Action | Version | Purpose |
|--------|---------|---------|
| `actions/checkout` | `v4` | Checkout source |
| `aws-actions/configure-aws-credentials` | `v4` | OIDC-based AWS auth (no stored access keys) |
| `aws-actions/amazon-ecr-login` | `v2` | Authenticate local Docker daemon to ECR |
| `docker/setup-buildx-action` | `v3` | Enable BuildKit and layer caching |
| `docker/build-push-action` | `v6` | Build + tag + push multi-platform images |
| `aws-actions/amazon-ecs-render-task-definition` | `v1` | Inject new image URI into task definition JSON template |
| `aws-actions/amazon-ecs-deploy-task-definition` | `v1` | Register task def revision + trigger ECS rolling deploy |
| `hashicorp/setup-terraform` | `v3` | Install pinned Terraform CLI version in runner |
| `azure/login` | `v2` | Azure login via OIDC (for ACR push step) |
| `azure/docker-login` | `v1` | Authenticate Docker to ACR |

**OIDC authentication is mandatory for AWS** — do not store long-lived AWS access keys in GitHub Secrets. Set up an IAM OIDC identity provider for `token.actions.githubusercontent.com` and assume an IAM role with a trust policy scoped to `repo:your-org/nexus-crm:ref:refs/heads/main`. Same pattern applies for Azure using a federated credential.

### Docker Base Images

| Image | Use |
|-------|-----|
| `python:3.12-slim` | FastAPI backend and Celery worker — multi-stage build, run as non-root user |
| `node:22-alpine` (build stage) | Vite build step — `npm run build` produces `dist/` |
| `nginx:1.27-alpine` (runtime stage) | Serve compiled React frontend; minimal attack surface |

Use multi-stage builds. Final images should be under 300 MB. Always create a non-root user in the Dockerfile — required if ECS task definition uses `readonlyRootFilesystem = true`.

### Alembic Migration in CI

Run `alembic upgrade head` as a one-off ECS task (not a sidecar) using the same backend image with a command override. The CI pipeline step:

1. Registers a migration task definition with `command = ["alembic", "upgrade", "head"]`
2. Runs `aws ecs run-task --launch-type FARGATE --task-definition nexus-crm-migrate`
3. Waits for the task to reach `STOPPED` with exit code 0
4. Only then deploys the updated backend service

This guarantees migrations complete before new application code starts serving traffic.

---

## What NOT to Use

| Anti-Pattern | Why Not | Use Instead |
|-------------|---------|-------------|
| AWS CodePipeline / CodeDeploy | Added complexity, cost, and IAM surface for a team already running GitHub Actions | GitHub Actions with OIDC |
| ECS EC2 launch type | Requires managing EC2 instances, AMI patching, capacity reservations | ECS Fargate |
| RDS Aurora Serverless v2 | Auto-pause causes cold-start query latency; Aurora per-ACU pricing is 2-3x standard RDS for a lightly loaded CRM | RDS for PostgreSQL on `db.t4g.medium` |
| ElastiCache Serverless | 2-4x cost overhead vs provisioned for a predictable Celery/JWT session workload | Provisioned ElastiCache replication group |
| Azure Kubernetes Service (AKS) | 30-minute cold start for cluster provisioning; cluster management overhead; overkill for a warm standby | Azure Container Instances (ACI) |
| Azure PostgreSQL Single Server | Retired March 2025 — no longer available for new deployments | Azure PostgreSQL Flexible Server |
| Secrets in ECS `environment` block | Values appear in CloudWatch logs and the AWS ECS console in plaintext | ECS `secrets` block with Secrets Manager ARN |
| `terraform workspace` for multi-env | Workspaces share a backend bucket prefix; subtle blast radius issues; harder to diff environments | Separate `staging/` and `prod/` Terraform root directories with separate state keys |
| Single monolithic Terraform root | One state file for all environments and all clouds — a failed plan blocks everything | Per-environment roots: `terraform/aws/staging/`, `terraform/aws/prod/`, `terraform/azure/staging/`, `terraform/azure/prod/` |
| CloudPosse modules | Heavier opinion layer, harder to debug, less community documentation than terraform-aws-modules | `terraform-aws-modules` collection |
| ECR image tags using `:latest` | Unpredictable deployments — `latest` can refer to any image | Tag images with Git commit SHA; also tag `staging` / `prod` as mutable convenience aliases |
| Storing Terraform secret values in `aws_secretsmanager_secret_version.secret_string` | Values end up in `.tfstate` in plaintext | Create the secret resource (ARN in state), populate value out-of-band via CLI/CI |

---

## Integration Points

### AWS Primary → Azure Warm Failover: Database Synchronisation

**Method:** PostgreSQL logical replication from RDS to Azure Flexible Server.

**Two tiers of implementation:**

| Tier | RPO | Complexity | When to use |
|------|-----|------------|------------|
| Nightly pg_dump → Azure Blob → restore | Up to 24h | Low — one cron job, no DMS | Acceptable if failover SLA is "within a business day" |
| Azure DMS online migration (continuous WAL replication) | < 5 minutes | Medium — DMS infrastructure, RDS parameter group reboot | Required if stricter RPO is needed |

**Recommendation for v1.2:** Start with nightly pg_dump. Document the DMS upgrade path. The nightly approach is runnable in < 1 hour of setup; DMS requires enabling logical replication on RDS (reboot), configuring a DMS replication instance, and ongoing monitoring.

**DMS setup when required:**
1. Enable `rds.logical_replication = 1` in the RDS parameter group (requires reboot — plan a maintenance window).
2. Set `max_wal_senders = 10`, `max_replication_slots = 5`.
3. Create Azure DMS project: source = AWS RDS PostgreSQL, target = Azure Flexible Server, mode = Online (LSN tracking).
4. Azure DMS continuously replicates WAL changes with < 5 minute RPO.
5. At cutover: stop DMS, promote Azure replica, update Key Vault app secrets, flip Route 53.

### AWS Primary → Azure Warm Failover: Container Images

CI pipeline pushes images to both ECR and ACR on every merge to main. ACI containers always reference the latest image in ACR. No additional pipeline logic needed beyond an extra `docker push` to the ACR endpoint after the ECR push:

```yaml
- name: Push to ACR
  run: |
    docker tag $ECR_REGISTRY/nexus-crm-backend:$SHA \
      $ACR_LOGIN_SERVER/nexus-crm-backend:$SHA
    docker push $ACR_LOGIN_SERVER/nexus-crm-backend:$SHA
```

This keeps Azure always current with no manual image sync step.

### Route 53 Failover Routing (Near-Automatic Cutover)

| Record | Routing | Target |
|--------|---------|--------|
| `app.nexus-crm.com` (primary) | Failover PRIMARY + health check | AWS ALB |
| `app.nexus-crm.com` (secondary) | Failover SECONDARY | Azure ACI public IP |

Route 53 monitors the ALB health check endpoint. If primary fails 3 consecutive checks (default 30s interval = ~90s detection), DNS automatically resolves to the Azure ACI IP. Recovery is symmetric — when the AWS health check passes again, DNS reverts to primary.

**Terraform resources:**
```hcl
resource "aws_route53_health_check" "primary" {
  fqdn              = aws_lb.main.dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
}

resource "aws_route53_record" "primary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "app.nexus-crm.example.com"
  type    = "A"
  alias { name = aws_lb.main.dns_name, zone_id = aws_lb.main.zone_id, evaluate_target_health = true }
  failover_routing_policy { type = "PRIMARY" }
  health_check_id = aws_route53_health_check.primary.id
  set_identifier  = "primary"
}

resource "aws_route53_record" "secondary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "app.nexus-crm.example.com"
  type    = "A"
  records = [azurerm_container_group.app.ip_address]
  ttl     = 60
  failover_routing_policy { type = "SECONDARY" }
  set_identifier = "secondary"
}
```

### Secrets Consistency Between Clouds

The JWT secret used to sign access/refresh tokens must be identical in both clouds. Sessions started on AWS must decode on Azure after failover. Enforce this by:
1. Generating the JWT secret once.
2. Storing the same value in both `nexus-crm/{env}/app` (AWS Secrets Manager) and the Azure Key Vault equivalent.
3. Referencing the same Key Vault secret name in both the ECS task definition and the ACI container group.

---

## Terraform Workspace Structure

```
terraform/
  bootstrap/               # S3 bucket + DynamoDB table — run once with local state
    main.tf
  modules/                 # Shared local modules (optional)
    ecs-service/           # Reusable ECS service + target group + security group
    ecr/                   # ECR repo + lifecycle policy
  aws/
    staging/
      main.tf              # Calls terraform-aws-modules
      variables.tf
      outputs.tf
      terraform.tfvars
    prod/
      main.tf
      variables.tf
      outputs.tf
      terraform.tfvars
  azure/
    staging/
      main.tf
      variables.tf
      outputs.tf
      terraform.tfvars
    prod/
      main.tf
      variables.tf
      outputs.tf
      terraform.tfvars
```

Keep AWS and Azure in completely separate Terraform roots with separate state files. They share no Terraform-managed resources (the connection between them is application-level: DNS + DB replication + image mirroring). Combining them in one plan creates cross-provider dependency ordering issues and complicates targeted applies.

---

## Sources

- [hashicorp/terraform-provider-aws releases — v6.38.0](https://github.com/hashicorp/terraform-provider-aws/releases)
- [hashicorp/terraform-provider-azurerm releases — v4.66.0](https://github.com/hashicorp/terraform-provider-azurerm/releases)
- [terraform-aws-modules/ecs releases — v7.5.0 (Mar 18 2026)](https://github.com/terraform-aws-modules/terraform-aws-ecs/releases)
- [terraform-aws-modules/vpc on Terraform Registry — v6.6.0](https://registry.terraform.io/modules/terraform-aws-modules/vpc/aws/latest)
- [terraform-aws-modules/rds on Terraform Registry](https://registry.terraform.io/modules/terraform-aws-modules/rds/aws/latest)
- [terraform-aws-modules/elasticache on Terraform Registry](https://registry.terraform.io/modules/terraform-aws-modules/elasticache/aws/latest)
- [terraform-aws-modules/alb on Terraform Registry](https://registry.terraform.io/modules/terraform-aws-modules/alb/aws/latest)
- [terraform-aws-modules/acm on Terraform Registry — v5.x (Jan 8 2026)](https://registry.terraform.io/modules/terraform-aws-modules/acm/aws/latest)
- [terraform-aws-modules/secrets-manager on Terraform Registry](https://registry.terraform.io/modules/terraform-aws-modules/secrets-manager/aws/latest)
- [azurerm_postgresql_flexible_server — Terraform Registry](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/postgresql_flexible_server)
- [azurerm_container_group — Terraform Registry](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_group)
- [Azure PostgreSQL Resiliency Architecture (Terraform reference)](https://github.com/Azure-Samples/Azure-PostgreSQL-Resiliency-Architecture)
- [ECS secrets via Secrets Manager — AWS docs](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html)
- [GitHub Actions OIDC with AWS IAM roles](https://aws.amazon.com/blogs/security/use-iam-roles-to-connect-github-actions-to-actions-in-aws/)
- [aws-actions/amazon-ecr-login v2](https://github.com/aws-actions/amazon-ecr-login)
- [aws-actions/amazon-ecs-deploy-task-definition](https://github.com/aws-actions/amazon-ecs-deploy-task-definition)
- [FastAPI Docker deployment guide](https://fastapi.tiangolo.com/deployment/docker/)
- [RDS logical replication docs — AWS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_MultiAZDBCluster_LogicalRepl.html)
- [Migrate RDS PostgreSQL to Azure — Microsoft Learn](https://learn.microsoft.com/en-us/azure/dms/tutorial-rds-postgresql-server-azure-db-for-postgresql-online)
- [ECS health check pitfall — terraform-aws-modules/ecs issue #148](https://github.com/terraform-aws-modules/terraform-aws-ecs/issues/148)
- [Automated deployments with GitHub Actions for ECS Express Mode — AWS blog (Mar 2026)](https://aws.amazon.com/blogs/containers/automated-deployments-with-github-actions-for-amazon-ecs-express-mode/)
