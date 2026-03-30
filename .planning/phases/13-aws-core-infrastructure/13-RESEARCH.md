# Phase 13: AWS Core Infrastructure - Research

**Researched:** 2026-03-29
**Domain:** Terraform AWS infrastructure (VPC, RDS, ElastiCache, ECR, Secrets Manager, IAM OIDC)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Refactor from the current flat `terraform/` layout to `environments/staging/` and `environments/prod/` directories. Each environment directory contains its own `main.tf`, `backend.tf` (or `backend.tfvars`), `variables.tf`, `outputs.tf`, and `terraform.tfvars`. This matches DEPLOY-04 exactly (separate state files per environment).

**D-02:** Shared module code stays in `terraform/modules/` — no relocation. Environment directories reference modules via relative paths (e.g., `source = "../../modules/networking"`).

**D-03:** The existing flat root wiring files (`terraform/main.tf`, `terraform/variables.tf`, `terraform/outputs.tf`, `terraform/terraform.tfvars`) are deleted/replaced once the `environments/` structure is in place. No two competing entry points.

### Claude's Discretion

- **State backend bootstrap:** Create the S3 state bucket (versioned, KMS-encrypted, native locking via `use_lockfile = true`) before `terraform init`. Recommended: a Makefile target or `terraform/bootstrap/` config that uses a local backend, creates the bucket, then is discarded. Document the one-time operator steps clearly.
- **Secret values strategy:** Preferred approach: create AWS Secrets Manager "shell" resources in Terraform (name + KMS key only), populate values out-of-band via AWS CLI or console, so plaintext never lives in tfstate. If this adds complexity, document the mitigation (state encryption + IAM policy restricting state bucket access).
- **Module fixes vs community modules:** Extend and fix the existing custom modules rather than migrating to terraform-aws-modules community modules (less churn). Required fixes: RDS PG15→17, add custom parameter group (logical replication), add RDS Proxy module, change ECR to IMMUTABLE tags + add lifecycle policies, change ElastiCache from `aws_elasticache_cluster` to `aws_elasticache_replication_group`.
- **AWS provider version:** Upgrade from `~> 5.0` to `~> 6.0` (research-recommended 6.38.0 confirmed) and Terraform to `~> 1.10`. Do this in the same PR as the structure refactor.
- **entrypoint.sh migration removal:** The existing `deploy/entrypoint.sh` runs `alembic upgrade head` at container start (DEPLOY-05 violation). This must be removed as part of Phase 13 work (it's a precondition for safe Phase 15 pipeline). It's a one-line deletion.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INFRA-01 | VPC with public/private subnets, NAT gateway, and security groups for all services | Networking module verified — structure correct, security group egress rules confirmed sufficient. No changes needed beyond adding RDS Proxy SG if RDS Proxy is added. |
| INFRA-02 | RDS PostgreSQL with parameter group configured for logical replication readiness | RDS module needs: engine_version "15"→"17", new `aws_db_parameter_group` resource with 3 params, `parameter_group_name` reference added to `aws_db_instance`. |
| INFRA-03 | RDS Proxy provisioned alongside RDS for connection pooling | New `terraform/modules/rds_proxy/` module required. Resources: `aws_db_proxy`, `aws_db_proxy_default_target_group`, `aws_db_proxy_target`. Requires IAM auth + Secrets Manager secret ARN. |
| INFRA-04 | ECR repositories with immutable tags and lifecycle policies | Two ECR repos in `terraform/main.tf` need `image_tag_mutability = "IMMUTABLE"` (currently MUTABLE) and `aws_ecr_lifecycle_policy` resources added. |
| INFRA-07 | AWS Secrets Manager secrets at `/nexus/staging/` and `/nexus/prod/` paths | Secrets module path format `/${var.app_name}/${var.environment}/${each.key}` resolves to `/nexus-crm/staging/DATABASE_URL` — needs path prefix change to `/nexus/staging/` and `/nexus/prod/`. Shell-resource pattern (name only, no secret_version) is the planner's discretion call. |
| INFRA-09 | ElastiCache provisioned Redis replication group (not Serverless) | ElastiCache module must replace `aws_elasticache_cluster` with `aws_elasticache_replication_group`. Output reference changes from `cache_nodes[0].address` to `primary_endpoint_address`. |
| INFRA-10 | IAM OIDC provider and GitHub Actions role with least-privilege ECS/ECR/Secrets permissions | IAM module OIDC subject claim is `StringEquals` on `refs/heads/main` — this will break when GitHub Actions environment is used (sub claim changes). Must use `StringLike` with `repo:ORG/REPO:*` or list all expected subject formats. GitHub Actions role also needs `ecs:RunTask`, `ecs:DescribeTasks`, `ecs:StopTask`, and `iam:PassRole` for the migration runner task (Phase 15 prerequisite). |
</phase_requirements>

---

## Summary

Phase 13 is a Terraform refactor-and-fix phase, not a greenfield build. The codebase already has all modules and most resources; the work is (1) restructuring from a flat root into `environments/staging/` and `environments/prod/` directories, (2) upgrading the AWS provider from `~> 5.0` to `~> 6.0`, (3) fixing four concrete module deficiencies, and (4) adding one new module (RDS Proxy). No compute (ECS, ALB, CloudFront) is provisioned in this phase — those are Phase 14.

The environment restructuring must happen atomically with the provider upgrade because the flat `terraform/main.tf` root would need significant rework either way. The safest approach: create the `environments/` tree first with a local backend, validate with `terraform validate`, then wire the S3 remote backend, then run `terraform apply`. The existing state in the flat root (if any) should be treated as disposable since no live infrastructure exists yet.

Four module fixes are required: RDS engine version upgrade (15→17) plus custom parameter group; ECR mutability change (MUTABLE→IMMUTABLE) plus lifecycle policies; ElastiCache resource type change (`aws_elasticache_cluster` → `aws_elasticache_replication_group`); secrets path prefix correction (`/nexus-crm/{env}/` → `/nexus/{env}/`). One new module must be created: RDS Proxy (three resources: `aws_db_proxy`, `aws_db_proxy_default_target_group`, `aws_db_proxy_target`).

**Primary recommendation:** Execute in five sequential tasks: (1) S3 bootstrap + provider upgrade + environment directory structure, (2) module fixes (RDS, ECR, ElastiCache, Secrets path), (3) new RDS Proxy module, (4) IAM OIDC subject claim fix + GitHub Actions role policy additions, (5) `entrypoint.sh` Alembic removal + smoke-test `terraform validate` in both environments.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Terraform CLI | `>= 1.10, < 2.0` | Infrastructure provisioning | Installed at 1.14.8 (verified). `use_lockfile` for S3 native locking arrived in 1.10. |
| `hashicorp/aws` provider | `~> 6.0` | All AWS resource management | v6.0 GA April 2025; adds per-resource `region` attribute. Current code is `~> 5.0` — upgrade required per CONTEXT.md D-01. |
| `hashicorp/random` provider | `~> 3.6` | DB password generation | Already present in `terraform/main.tf`; keep. |

### Modules (custom, kept in-tree per D-02)

| Module | Path | Changes Required |
|--------|------|-----------------|
| networking | `terraform/modules/networking/` | No structural changes. Verify security group completeness after RDS Proxy is added. |
| rds | `terraform/modules/rds/` | engine_version 15→17, add `aws_db_parameter_group`, wire `parameter_group_name`. |
| rds_proxy | `terraform/modules/rds_proxy/` | New module. Three resources. |
| elasticache | `terraform/modules/elasticache/` | Replace `aws_elasticache_cluster` with `aws_elasticache_replication_group`. Update outputs. |
| secrets | `terraform/modules/secrets/` | Fix path prefix. Shell-resource pattern (optional — planner decision). |
| iam | `terraform/modules/iam/` | Fix OIDC subject claim condition. Add ECS run-task permissions. Remove `frontend_bucket_arn` dependency (Phase 14 concern). |
| ecr (inline in main.tf) | `environments/{env}/main.tf` | Change `image_tag_mutability` to `IMMUTABLE`. Add `aws_ecr_lifecycle_policy`. |

### Supporting — Bootstrap Only

| Tool | Version | Purpose |
|------|---------|---------|
| AWS CLI | 2.33.24 (verified) | Out-of-band secret population (`aws secretsmanager put-secret-value`), bootstrap bucket creation |

**Installation:** Terraform 1.14.8 is already installed. AWS CLI 2.33.24 is already installed.

---

## Architecture Patterns

### Recommended Project Structure (post-refactor)

```
terraform/
├── bootstrap/           # One-time S3 state bucket + KMS key (local backend, discarded after use)
│   ├── main.tf
│   └── outputs.tf
├── modules/
│   ├── networking/      # VPC, subnets, NAT, security groups (existing — unchanged)
│   ├── rds/             # RDS instance + parameter group (fix engine version + param group)
│   ├── rds_proxy/       # NEW: aws_db_proxy + target group + target
│   ├── elasticache/     # Redis replication group (fix resource type)
│   ├── secrets/         # Secrets Manager shells (fix path prefix)
│   ├── iam/             # OIDC provider + roles (fix subject claim)
│   ├── alb/             # Phase 14 — do not touch
│   ├── cloudfront/      # Phase 14 — do not touch
│   ├── ecs/             # Phase 14 — do not touch
│   └── ecs_worker/      # Phase 14 — do not touch
└── environments/
    ├── staging/
    │   ├── main.tf          # Wire all Phase 13 modules
    │   ├── backend.tf       # S3 backend config (key = staging/terraform.tfstate)
    │   ├── variables.tf     # All variable declarations
    │   ├── outputs.tf       # All outputs Phase 14 will consume
    │   └── terraform.tfvars # Staging-specific values (db.t4g.medium, cache.t4g.small, multi_az=false)
    └── prod/
        ├── main.tf
        ├── backend.tf       # S3 backend config (key = prod/terraform.tfstate)
        ├── variables.tf
        ├── outputs.tf
        └── terraform.tfvars # Prod-specific values (db.r8g.large or db.t4g.large, multi_az=true)
```

### Pattern 1: S3 Backend with Native Locking (no DynamoDB)

**What:** Terraform 1.10+ supports S3 conditional writes for state locking via `use_lockfile = true`. DynamoDB is deprecated and will be removed in a future minor version.

**When to use:** All new Terraform configurations. Do not create a DynamoDB table.

**Example:**
```hcl
# environments/staging/backend.tf
terraform {
  backend "s3" {
    bucket       = "nexus-crm-terraform-state"
    key          = "staging/terraform.tfstate"
    region       = "ap-southeast-1"
    encrypt      = true
    use_lockfile = true
    # No dynamodb_table — native S3 locking only
  }
}
```

Source: [Terraform S3 Backend docs](https://developer.hashicorp.com/terraform/language/backend/s3)

### Pattern 2: Bootstrap Config (one-time, local backend)

**What:** A minimal `terraform/bootstrap/` config with a local backend that creates the S3 state bucket and KMS key. Run once by an operator with admin credentials, then discard (do not commit tfstate).

**Example:**
```hcl
# terraform/bootstrap/main.tf
terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  # local backend — state file stays local, not committed
}

resource "aws_kms_key" "terraform_state" {
  description             = "KMS key for Terraform state bucket"
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "nexus-crm-terraform-state"
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
  }
}
```

### Pattern 3: RDS Custom Parameter Group for Logical Replication

**What:** The default RDS parameter group is read-only and cannot be changed. A custom `aws_db_parameter_group` must be created and referenced at initial provisioning. Changing it post-creation forces a reboot.

**Example:**
```hcl
# terraform/modules/rds/main.tf (additions)
resource "aws_db_parameter_group" "this" {
  name   = "${var.app_name}-${var.environment}-pg17"
  family = "postgres17"

  parameter {
    name         = "rds.logical_replication"
    value        = "1"
    apply_method = "pending-reboot"
  }

  parameter {
    name         = "idle_in_transaction_session_timeout"
    value        = "30000"
    apply_method = "immediate"
  }

  parameter {
    name         = "wal_sender_timeout"
    value        = "0"
    apply_method = "immediate"
  }
}

# In aws_db_instance.this:
#   engine_version       = "17"
#   parameter_group_name = aws_db_parameter_group.this.name
```

### Pattern 4: ElastiCache Replication Group (not Cluster)

**What:** `aws_elasticache_cluster` with `engine = "redis"` creates a single-node cluster mode disabled instance. For a proper replication group (Celery requires reliable Redis, not a single node), use `aws_elasticache_replication_group`. The output attribute changes from `cache_nodes[0].address` to `primary_endpoint_address`.

**Example:**
```hcl
# terraform/modules/elasticache/main.tf (replacement)
resource "aws_elasticache_replication_group" "this" {
  replication_group_id = "${var.app_name}-${var.environment}-redis"
  description          = "Redis replication group for ${var.app_name} ${var.environment}"

  node_type            = var.redis_node_type
  num_cache_clusters   = 1           # staging: 1 node; prod: 2+ for HA
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.this.name
  security_group_ids   = [var.redis_security_group_id]

  engine_version       = "7.1"
  parameter_group_name = "default.redis7"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  transit_encryption_mode    = "required"

  automatic_failover_enabled = false  # true requires num_cache_clusters >= 2
  multi_az_enabled           = false  # true requires automatic_failover_enabled

  apply_immediately = false

  lifecycle {
    ignore_changes = [num_cache_clusters]
  }
}

# outputs.tf: primary_endpoint_address and port
```

Source: [aws_elasticache_replication_group docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/elasticache_replication_group)

### Pattern 5: ECR IMMUTABLE Tags + Lifecycle Policy

**What:** ECR repositories currently have `image_tag_mutability = "MUTABLE"`. This must be changed to `"IMMUTABLE"` and lifecycle policies added to prevent unbounded storage accumulation.

**Example:**
```hcl
# In environments/{env}/main.tf (replacing inline resources)
resource "aws_ecr_repository" "api" {
  name                 = "${local.name_prefix}-api"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}
```

### Pattern 6: RDS Proxy Module (new)

**What:** RDS Proxy sits between ECS tasks and RDS, pools connections, and prevents connection exhaustion under Fargate autoscaling. Requires IAM authentication (Proxy fetches DB credentials from Secrets Manager).

**Example:**
```hcl
# terraform/modules/rds_proxy/main.tf
resource "aws_db_proxy" "this" {
  name                   = "${var.app_name}-${var.environment}-proxy"
  debug_logging          = false
  engine_family          = "POSTGRESQL"
  idle_client_timeout    = 1800
  require_tls            = true
  role_arn               = aws_iam_role.rds_proxy.arn
  vpc_security_group_ids = [var.rds_proxy_security_group_id]
  vpc_subnet_ids         = var.private_subnet_ids

  auth {
    auth_scheme = "SECRETS"
    iam_auth    = "DISABLED"
    secret_arn  = var.db_password_secret_arn
  }
}

resource "aws_db_proxy_default_target_group" "this" {
  db_proxy_name = aws_db_proxy.this.name

  connection_pool_config {
    max_connections_percent      = 100
    max_idle_connections_percent = 50
    connection_borrow_timeout    = 120
  }
}

resource "aws_db_proxy_target" "this" {
  db_instance_identifier = var.db_instance_identifier
  db_proxy_name          = aws_db_proxy.this.name
  target_group_name      = aws_db_proxy_default_target_group.this.name
}
```

Note: RDS Proxy requires a **dedicated security group** separate from the RDS SG (allow port 5432 inbound from ECS SGs → Proxy SG, allow port 5432 inbound from Proxy SG → RDS SG). Add `rds_proxy_security_group_id` to networking module outputs.

Source: [aws_db_proxy Terraform docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_proxy)

### Pattern 7: IAM OIDC Subject Claim Fix

**What:** The current IAM module uses `StringEquals` on `repo:OWNER/REPO:ref:refs/heads/main`. When a GitHub Actions job uses an environment (e.g., `environment: prod`), the OIDC subject claim changes to `repo:OWNER/REPO:environment:prod` — which does not match `StringEquals` on the branch sub. This causes auth failures in Phase 15.

**Fix:** Use `StringLike` with a wildcard, or use a list of all expected sub formats.

**Example:**
```hcl
Condition = {
  StringLike = {
    "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
    "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:*"
  }
}
```

This is broader than strictly required but is the standard pattern. For tighter scoping, use a `StringLike` list with specific branch/environment patterns.

Source: [GitHub OIDC reference](https://docs.github.com/en/actions/concepts/security/openid-connect), [configure-aws-credentials OIDC issue #454](https://github.com/aws-actions/configure-aws-credentials/issues/454)

### Pattern 8: Secrets Manager Shell Resources (no plaintext in state)

**What:** The current secrets module stores actual secret values in `aws_secretsmanager_secret_version` resources, which means plaintext values appear in Terraform state. The preferred approach: create only the secret name (shell resource) in Terraform, then populate values out-of-band.

**Example:**
```hcl
# terraform/modules/secrets/main.tf — shell-only approach
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "/nexus/${var.environment}/db_password"
  recovery_window_in_days = 7
  # No aws_secretsmanager_secret_version resource
}

# Output ARNs for use by ECS task definitions and RDS Proxy
output "db_password_secret_arn" {
  value = aws_secretsmanager_secret.db_password.arn
}
```

**Out-of-band population (operator step, documented in Makefile):**
```bash
aws secretsmanager put-secret-value \
  --secret-id /nexus/staging/db_password \
  --secret-string "$(openssl rand -base64 32)"
```

**Alternative (acceptable if shell pattern adds too much complexity):** Keep `aws_secretsmanager_secret_version` but ensure state bucket is KMS-encrypted and access is restricted via IAM. The existing S3 KMS encryption + `use_lockfile` provides adequate protection for a small team — document the tradeoff clearly.

### Anti-Patterns to Avoid

- **Two competing Terraform entry points:** The flat `terraform/main.tf` root and the new `environments/` directories must not coexist after this phase. Delete the root wiring files per D-03.
- **Committing `terraform.tfvars` with secrets:** Variable files that contain `secret_key`, DB passwords, or API keys must be in `.gitignore`. Use environment variables (`TF_VAR_secret_key`) or AWS Secrets Manager out-of-band population instead.
- **`aws_elasticache_cluster` for Redis:** Single-node cluster mode cannot be converted to a replication group in place — it requires destroy + recreate. Make the switch now while there is no live data.
- **`apply_immediately = true` on RDS parameter group changes:** Changing `rds.logical_replication` requires a reboot. Setting `apply_method = "immediate"` for this parameter will be silently ignored; it requires `pending-reboot`. The instance will reboot at the next maintenance window, which is acceptable for initial provisioning.
- **OIDC `aws_iam_openid_connect_provider` created twice:** If both staging and prod environments create the OIDC provider for the same GitHub Actions URL, Terraform will error on the second apply. The OIDC provider is account-scoped, not environment-scoped. Create it once in a shared location (e.g., only in the IAM module called from prod, or as a standalone `environments/shared/` config) or use a `data` source lookup after the first creation.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Connection pooling | Custom PgBouncer ECS task | `aws_db_proxy` (RDS Proxy) | RDS Proxy is AWS-managed, handles credential rotation automatically, costs ~$0.015/hr, avoids managing a separate container |
| State locking | DynamoDB table | `use_lockfile = true` on S3 backend | DynamoDB is deprecated for this use case in Terraform 1.10+; S3 native locking is the current standard |
| Redis HA | `aws_elasticache_cluster` with manual failover | `aws_elasticache_replication_group` | Replication group provides automatic primary failover; required for Celery broker reliability |
| Secret rotation | Lambda rotation function | AWS Secrets Manager native rotation or out-of-band CLI population | Secret rotation is out of scope for v1.2; shell resources with manual population are simpler and correct for now |

---

## Common Pitfalls

### Pitfall 1: OIDC Subject Claim Mismatch with GitHub Environments

**What goes wrong:** The GitHub Actions OIDC `sub` claim includes the environment name (`repo:ORG/REPO:environment:prod`) when a job targets a GitHub Environment. The current IAM module uses `StringEquals` on the branch-based sub (`repo:ORG/REPO:ref:refs/heads/main`). Phase 15 CI jobs targeting the `prod` environment will receive an `Access Denied` from STS.

**Why it happens:** GitHub changes the subject claim format when `environment:` is set in a workflow job. The trust policy must anticipate both formats.

**How to avoid:** Change `StringEquals` to `StringLike` with `repo:${github_repository}:*` as the sub value. Document that this grants any branch/environment in the repo the ability to assume the role — which is appropriate given the repo is private and ECR/ECS permissions are the only grants.

**Warning signs:** `AssumeRoleWithWebIdentity` errors in Phase 15 CI logs; "Not authorized to perform sts:AssumeRoleWithWebIdentity" errors.

### Pitfall 2: OIDC Provider Created Twice (Account-Scoped)

**What goes wrong:** If both `environments/staging/` and `environments/prod/` each instantiate the `iam` module, and the `iam` module creates `aws_iam_openid_connect_provider`, the second `terraform apply` fails: "An OpenID Connect provider with url https://token.actions.githubusercontent.com already exists in your AWS account."

**Why it happens:** OIDC providers are account-scoped, not region/environment-scoped.

**How to avoid:** Create the OIDC provider only once. Options: (a) create it only in the prod environment module and use a `data "aws_iam_openid_connect_provider"` lookup in staging; (b) use a `var.create_oidc_provider` boolean flag in the IAM module, default `true` for prod, `false` for staging; (c) extract OIDC creation into a separate `environments/shared/` config (adds complexity, not recommended for this project size). Option (b) is simplest.

**Warning signs:** `EntityAlreadyExists` on `terraform apply` for the second environment.

### Pitfall 3: RDS Parameter Group Requires Reboot

**What goes wrong:** `rds.logical_replication = 1` is a static parameter. Changing it on an existing instance requires a reboot. If applied with `apply_immediately = false` (the current default), the reboot will happen at the next maintenance window, leaving the parameter in a pending state until then.

**Why it happens:** AWS RDS distinguishes between dynamic parameters (applied immediately) and static parameters (requires reboot). `rds.logical_replication` is static.

**How to avoid:** This is acceptable for initial provisioning — the reboot happens during the maintenance window before any production traffic exists. The key is setting the parameter group at creation time, not post-launch. If this phase deploys to a fresh RDS instance, the reboot will be automatic on first start.

**Warning signs:** After `terraform apply`, `aws rds describe-db-instances --query 'DBInstances[*].PendingModifiedValues'` shows pending parameter group changes.

### Pitfall 4: Secrets in Terraform State

**What goes wrong:** The current `aws_secretsmanager_secret_version` resources store plaintext values (DB passwords, JWT secrets, API keys) in the Terraform state file. Any IAM principal with `s3:GetObject` on the state bucket can read all secrets.

**Why it happens:** The existing secrets module was designed for convenience — it generates the DB password from `random_password` and writes it into Secrets Manager in one step. The side effect is that the password also lives in `terraform.tfstate`.

**How to avoid:** Use the shell-resource pattern: create only `aws_secretsmanager_secret` in Terraform (name + KMS key), populate the actual value with `aws secretsmanager put-secret-value` out-of-band. If keeping the full resource approach, ensure the S3 bucket has KMS encryption with a restricted key policy (only CI role and operator principals can decrypt).

**Warning signs:** Running `terraform show` displays secret values in plaintext; state bucket access logs show reads from unexpected principals.

### Pitfall 5: ElastiCache Cluster Cannot Be Converted In Place

**What goes wrong:** An existing `aws_elasticache_cluster` resource cannot be converted to `aws_elasticache_replication_group` via a plan/apply — Terraform will error or attempt to destroy and recreate. If there is live data in the cluster, this destroys it.

**Why it happens:** These are different AWS resource types with different ARN formats and different state representations in Terraform.

**How to avoid:** Phase 13 creates this infrastructure from scratch (no live data exists yet). Rename the resource in the module immediately rather than adding a `moved {}` block. Since no `terraform.tfstate` exists for the new environment directories, there is nothing to migrate.

**Warning signs:** `terraform plan` shows a destroy + create for the ElastiCache resource.

### Pitfall 6: NAT Gateway Count = 2 for Staging

**What goes wrong:** The current networking module creates 2 NAT gateways (`count = 2`), one per AZ. At ~$0.045/hour each, 2 NAT gateways cost ~$65/month in staging for no HA benefit (staging can tolerate AZ failure).

**Why it happens:** The networking module was built for production parity.

**How to avoid:** Add a `nat_gateway_count` variable to the networking module, default `1` for staging, `2` for prod. A single NAT gateway with a private route table pointing all private subnets to it is correct for staging.

**Warning signs:** Unexpectedly high AWS bills in staging; 2 EIPs allocated where 1 would suffice.

### Pitfall 7: ECR IMMUTABLE Tag Cannot Be Changed In Place

**What goes wrong:** Changing `image_tag_mutability` from `MUTABLE` to `IMMUTABLE` on an existing ECR repository fails with: "The immutability of an existing image tag cannot be changed."

**Why it happens:** AWS does not allow toggling tag mutability on a repository that already has images.

**How to avoid:** Since Phase 13 creates ECR repositories from scratch in the new `environments/` directories (no existing repos in the new Terraform state), set `IMMUTABLE` at creation time. The old repos from the flat root `terraform/main.tf` are separate resources and are out of scope.

---

## Code Examples

### environments/staging/main.tf skeleton

```hcl
# Source: derived from existing terraform/main.tf, scoped to Phase 13 modules only
terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 6.0" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name_prefix   = "${var.app_name}-${var.environment}"
  is_production = var.environment == "prod"
}

# ECR repositories (Phase 13 — inline in environments, not in a module)
resource "aws_ecr_repository" "api" {
  name                 = "${local.name_prefix}-api"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_repository" "worker" {
  name                 = "${local.name_prefix}-worker"
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name
  policy = jsonencode({ rules = [{ rulePriority = 1, description = "Keep last 10 images",
    selection = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 10 },
    action = { type = "expire" } }] })
}

resource "aws_ecr_lifecycle_policy" "worker" {
  repository = aws_ecr_repository.worker.name
  policy     = jsonencode({ rules = [{ rulePriority = 1, description = "Keep last 10 images",
    selection = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 10 },
    action = { type = "expire" } }] })
}

module "networking" {
  source      = "../../modules/networking"
  app_name    = var.app_name
  environment = var.environment
}

module "rds" {
  source                     = "../../modules/rds"
  app_name                   = var.app_name
  environment                = var.environment
  private_subnet_ids         = module.networking.private_subnet_ids
  rds_security_group_id      = module.networking.rds_security_group_id
  db_instance_class          = var.db_instance_class
  db_storage_gb              = var.db_storage_gb
  db_multi_az                = var.db_multi_az
  enable_deletion_protection = local.is_production
}

module "rds_proxy" {
  source                      = "../../modules/rds_proxy"
  app_name                    = var.app_name
  environment                 = var.environment
  private_subnet_ids          = module.networking.private_subnet_ids
  rds_proxy_security_group_id = module.networking.rds_proxy_security_group_id
  db_instance_identifier      = module.rds.db_instance_identifier
  db_password_secret_arn      = module.secrets.db_password_secret_arn
}

module "elasticache" {
  source                  = "../../modules/elasticache"
  app_name                = var.app_name
  environment             = var.environment
  private_subnet_ids      = module.networking.private_subnet_ids
  redis_security_group_id = module.networking.redis_security_group_id
  redis_node_type         = var.redis_node_type
}

module "secrets" {
  source      = "../../modules/secrets"
  app_name    = var.app_name
  environment = var.environment
}

module "iam" {
  source             = "../../modules/iam"
  app_name           = var.app_name
  environment        = var.environment
  aws_region         = var.aws_region
  github_repository  = var.github_repository
  create_oidc_provider = true   # staging creates it; prod uses data source or same flag
}
```

### Makefile targets for operator bootstrap

```makefile
# Source: recommended pattern from research
bootstrap-state:
	cd terraform/bootstrap && terraform init && terraform apply -auto-approve
	@echo "State bucket created. Run 'make init-staging' next."

init-staging:
	cd environments/staging && terraform init -backend-config=backend.tfvars

init-prod:
	cd environments/prod && terraform init -backend-config=backend.tfvars

apply-staging:
	cd environments/staging && terraform apply -var-file=terraform.tfvars

plan-prod:
	cd environments/prod && terraform plan -var-file=terraform.tfvars

secrets-staging:
	aws secretsmanager put-secret-value --secret-id /nexus/staging/db_password --secret-string "$$(openssl rand -base64 32)"
	aws secretsmanager put-secret-value --secret-id /nexus/staging/jwt_secret --secret-string "$$(openssl rand -base64 48)"
	@echo "Populate redis_url after ElastiCache endpoint is available from terraform output"
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Terraform CLI | All IaC provisioning | Yes | 1.14.8 | — |
| AWS CLI | Bootstrap, secret population, smoke tests | Yes | 2.23.24 | — |
| AWS account + credentials | All provisioning | Assumed (operator step) | — | Cannot proceed without |
| AWS ECR | INFRA-04 | Provisioned by Terraform | — | — |
| AWS RDS PostgreSQL 17 | INFRA-02 | Provisioned by Terraform | — | — |

**Missing dependencies with no fallback:**

- AWS account credentials with sufficient permissions (AdministratorAccess or a scoped policy covering VPC, RDS, ElastiCache, ECR, Secrets Manager, IAM, KMS, S3). This is an operator prerequisite before any Terraform work can begin.

**Missing dependencies with fallback:**

- None beyond credentials.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Terraform built-in (`terraform validate`, `terraform plan`) + AWS CLI smoke tests |
| Config file | `environments/staging/` and `environments/prod/` directory roots |
| Quick run command | `cd environments/staging && terraform validate` |
| Full suite command | `cd environments/staging && terraform plan -out=tfplan && terraform show tfplan` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INFRA-01 | VPC exists with correct subnets, NAT, SGs | smoke (aws cli) | `aws ec2 describe-vpcs --filters "Name=tag:Project,Values=nexus-crm"` | No — post-apply |
| INFRA-02 | RDS PG17 reachable with custom param group | smoke (aws cli) | `aws rds describe-db-instances --query 'DBInstances[*].DBParameterGroups'` | No — post-apply |
| INFRA-03 | RDS Proxy reachable from private subnet | smoke (aws cli) | `aws rds describe-db-proxies --query 'DBProxies[*].Endpoint'` | No — post-apply |
| INFRA-04 | ECR repos with IMMUTABLE tags exist | smoke (aws cli) | `aws ecr describe-repositories --query 'repositories[*].imageTagMutability'` | No — post-apply |
| INFRA-07 | Secrets exist at correct paths | smoke (aws cli) | `aws secretsmanager list-secrets --filter Key=name,Values=/nexus/staging/` | No — post-apply |
| INFRA-09 | Redis replication group reachable from ECS SG | smoke (aws cli) | `aws elasticache describe-replication-groups` | No — post-apply |
| INFRA-10 | GitHub Actions role can assume via OIDC | integration (manual) | Trigger test GHA workflow with `aws sts get-caller-identity` | No — Phase 15 |

Terraform IaC phases do not have unit tests in the traditional sense. The Nyquist validation gate for this phase is:

1. `terraform validate` passes in both `environments/staging/` and `environments/prod/`
2. `terraform plan` produces no errors in both environments
3. `terraform apply` completes without error in `environments/staging/`
4. Each success criterion from the phase definition is verified via `aws` CLI after apply

### Sampling Rate

- **Per task commit:** `terraform validate && terraform fmt -check` in the relevant environment directory
- **Per wave merge:** `terraform plan` (dry-run, no apply) in staging
- **Phase gate:** Full `terraform apply` in staging + all 7 AWS CLI smoke checks green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `terraform/bootstrap/main.tf` — does not exist yet; must be created before any init
- [ ] `environments/staging/` directory — does not exist; entire tree to be created
- [ ] `environments/prod/` directory — does not exist; entire tree to be created
- [ ] `terraform/modules/rds_proxy/` — does not exist; new module required for INFRA-03

---

## Module Fix Summary (Planner Reference)

| Module | File | Current State | Required Change |
|--------|------|---------------|-----------------|
| `rds` | `main.tf` | `engine_version = "15"`, no parameter group | Change to `"17"`, add `aws_db_parameter_group`, wire `parameter_group_name` |
| `rds` | `outputs.tf` | Missing `db_instance_identifier` output | Add `output "db_instance_identifier"` for RDS Proxy module to consume |
| `rds_proxy` | (new module) | Does not exist | Create 3-file module: `main.tf`, `variables.tf`, `outputs.tf` |
| `elasticache` | `main.tf` | `aws_elasticache_cluster` | Replace with `aws_elasticache_replication_group` |
| `elasticache` | `outputs.tf` | `cache_nodes[0].address` | Replace with `primary_endpoint_address` |
| `secrets` | `main.tf` | Path: `/${var.app_name}/${var.environment}/KEY` (= `/nexus-crm/staging/DATABASE_URL`) | Change to `/nexus/${var.environment}/KEY` to match INFRA-07 acceptance criteria |
| `secrets` | `main.tf` | Stores actual values in `aws_secretsmanager_secret_version` | Planner decision: shell-resource pattern (preferred) or keep with documented mitigation |
| `secrets` | `variables.tf` + `outputs.tf` | Missing `db_password_secret_arn`, `jwt_secret_arn`, `redis_url_secret_arn` outputs | Add individual ARN outputs for RDS Proxy and ECS (Phase 14) consumption |
| `iam` | `main.tf` | `StringEquals` on branch sub claim | Change to `StringLike` with `repo:${var.github_repository}:*` |
| `iam` | `main.tf` | GitHub Actions policy missing `ecs:RunTask`, `ecs:DescribeTasks` | Add for migration runner task (Phase 15 prep) |
| `iam` | `main.tf` | `frontend_bucket_arn` variable (Phase 14 concern) | Remove from Phase 13 IAM module — frontend bucket does not exist in Phase 13. Use a `var.frontend_bucket_arn` with a default of `""` and conditional policy statement. |
| `networking` | `main.tf` | No RDS Proxy security group | Add `aws_security_group.rds_proxy` (inbound 5432 from ECS SGs, outbound 5432 to RDS SG) |
| `networking` | `outputs.tf` | Missing `rds_proxy_security_group_id` | Add output |
| ECR (inline) | `terraform/main.tf` (root) | `image_tag_mutability = "MUTABLE"`, no lifecycle policy | Move to `environments/{env}/main.tf` with `IMMUTABLE` + lifecycle policy |
| `deploy/entrypoint.sh` | — | Line 9: `alembic upgrade head` | Delete line 9 (one-line change per DEPLOY-05) |

---

## Open Questions

1. **OIDC provider deduplication strategy**
   - What we know: OIDC provider is account-scoped; both environments would try to create the same provider
   - What's unclear: Planner must pick one approach — boolean flag, shared config, or data source lookup for staging
   - Recommendation: Add `var.create_oidc_provider = true` to IAM module; prod creates it, staging uses `data "aws_iam_openid_connect_provider"` lookup. Document clearly.

2. **Shell-resource vs full-resource for Secrets Manager**
   - What we know: Full resource puts plaintext in state; shell resource requires operator out-of-band steps
   - What's unclear: How much operational complexity is acceptable for the team
   - Recommendation: Shell-resource pattern. The Makefile `secrets-staging` and `secrets-prod` targets make the out-of-band population step explicit and reproducible.

3. **NAT gateway count for staging**
   - What we know: Current module always creates 2 NAT gateways (~$65/month overhead for staging)
   - What's unclear: Whether cost optimization was discussed and accepted
   - Recommendation: Add `nat_gateway_count` variable to networking module; default `1` for staging, `2` for prod. This is a ~$32/month saving with no reliability impact for staging.

4. **RDS instance class for prod**
   - What we know: Current default is `db.t3.medium`; research suggested `db.t4g.medium` staging / `db.r8g.large` prod
   - What's unclear: Budget approval for `db.r8g.large` (~$210/month)
   - Recommendation: Default to `db.t4g.large` for prod initially (~$100/month) with the option to scale up. Document the upgrade path.

---

## Sources

### Primary (HIGH confidence)

- Terraform S3 Backend official docs — `use_lockfile` feature, DynamoDB deprecation: https://developer.hashicorp.com/terraform/language/backend/s3
- `aws_elasticache_replication_group` Terraform Registry docs: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/elasticache_replication_group
- `aws_db_proxy` Terraform Registry docs: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_proxy
- GitHub Actions OIDC reference: https://docs.github.com/en/actions/concepts/security/openid-connect
- HashiCorp blog — AWS provider 6.0 GA: https://www.hashicorp.com/en/blog/terraform-aws-provider-6-0-now-generally-available
- Existing codebase — all `terraform/modules/*/main.tf`, `terraform/main.tf`, `terraform/variables.tf` — read directly

### Secondary (MEDIUM confidence)

- Scalr — AWS Provider v6 breaking changes overview: https://scalr.com/learning-center/aws-provider-v6-0-whats-breaking-in-april-2025/
- configure-aws-credentials OIDC environment sub claim issue #454: https://github.com/aws-actions/configure-aws-credentials/issues/454
- Medium — S3 native state locking no DynamoDB: https://rafaelmedeiros94.medium.com/goodbye-dynamodb-terraform-s3-backend-now-supports-native-locking-06f74037ad39

### Tertiary (LOW confidence)

- None — all critical claims are backed by official documentation or direct code inspection.

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — Terraform 1.14.8 and AWS CLI 2.33.24 verified on this machine; AWS provider v6 GA confirmed via HashiCorp blog
- Architecture: HIGH — all existing modules read directly; all required changes identified from code inspection
- Pitfalls: HIGH — OIDC subject claim issue and ElastiCache cluster-vs-replication-group issues verified via official docs and GitHub issue tracker
- Module fix list: HIGH — derived from direct code inspection of each module file against the phase acceptance criteria

**Research date:** 2026-03-29
**Valid until:** 2026-06-30 (AWS provider patch versions change frequently — re-verify before upgrading from ~> 6.0 to a specific patch)
