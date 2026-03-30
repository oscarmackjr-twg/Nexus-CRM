---
phase: 13-aws-core-infrastructure
verified: 2026-03-29T00:00:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Run `make tf-apply-staging` against a live AWS account"
    expected: "All resources provision successfully; state stored in nexus-crm-terraform-state S3 bucket"
    why_human: "Requires live AWS credentials and a provisioned S3 state bucket; cannot be verified statically"
  - test: "Verify `make tf-plan` and `make tf-apply` targets still behave correctly"
    expected: "These legacy Makefile targets reference the deleted `terraform/terraform.tfvars` and will fail if run. Confirm whether they should be removed or left as-is."
    why_human: "Static check found the targets exist but reference a deleted file; runtime impact cannot be confirmed without execution"
---

# Phase 13: AWS Core Infrastructure Verification Report

**Phase Goal:** Build and validate the complete AWS infrastructure Terraform configuration — Bootstrap (S3 state backend), Networking (VPC, subnets, SGs, NAT), RDS (PostgreSQL 17, parameter group), ElastiCache (Redis replication group), Secrets Manager (shell pattern), IAM (OIDC, ECS roles), RDS Proxy, and ECR — so the team can deploy NexusCRM to staging with a single `make tf-apply-staging`.
**Verified:** 2026-03-29
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | S3 state backend with versioning, KMS encryption, and public access block exists | VERIFIED | `terraform/bootstrap/main.tf` contains `aws_s3_bucket`, `aws_kms_key` (enable_key_rotation=true), `aws_s3_bucket_versioning`, `aws_s3_bucket_server_side_encryption_configuration`, `aws_s3_bucket_public_access_block` |
| 2 | Both environment backend.tf files use `use_lockfile = true` with no DynamoDB table | VERIFIED | `terraform/environments/staging/backend.tf` and `terraform/environments/prod/backend.tf` both contain `use_lockfile = true`; grep for `dynamodb_table` returns no matches |
| 3 | Old flat root terraform files are deleted | VERIFIED | `terraform/main.tf`, `terraform/variables.tf`, `terraform/outputs.tf`, `terraform/terraform.tfvars` all absent; `ls terraform/*.tf` returns no matches |
| 4 | Networking module has RDS Proxy SG and configurable NAT gateway count | VERIFIED | `terraform/modules/networking/main.tf` contains `aws_security_group.rds_proxy` (ingress port 5432 from api+worker SGs, egress to rds SG); `variables.tf` has `variable "nat_gateway_count"`; private route tables use `count.index % var.nat_gateway_count` |
| 5 | RDS module provisions PostgreSQL 17 with custom parameter group (logical replication) | VERIFIED | `terraform/modules/rds/main.tf` has `engine_version = "17"`, `aws_db_parameter_group` with `family = "postgres17"`, `rds.logical_replication = "1"` (pending-reboot), `idle_in_transaction_session_timeout = "30000"`, `wal_sender_timeout = "0"`, and `parameter_group_name = aws_db_parameter_group.this.name` on the db instance |
| 6 | ElastiCache module uses `aws_elasticache_replication_group` with encryption | VERIFIED | `terraform/modules/elasticache/main.tf` contains `aws_elasticache_replication_group`, `at_rest_encryption_enabled = true`, `transit_encryption_enabled = true`, `engine_version = "7.1"`, lifecycle with `ignore_changes = [num_cache_clusters]`; no `aws_elasticache_cluster` present |
| 7 | Secrets module creates shell resources at `/nexus/{env}/` with no plaintext in state | VERIFIED | `terraform/modules/secrets/main.tf` contains 8 `aws_secretsmanager_secret` resources at `/nexus/${var.environment}/` paths; no `aws_secretsmanager_secret_version` present; `variables.tf` contains only `app_name`, `environment`, `recovery_window_in_days` — no sensitive variable inputs |
| 8 | RDS Proxy module exists with `aws_db_proxy`, target group, target, and IAM role | VERIFIED | `terraform/modules/rds_proxy/main.tf` contains `aws_db_proxy` (engine_family=POSTGRESQL, require_tls=true), `aws_db_proxy_default_target_group` (max_connections_percent=100), `aws_db_proxy_target`, and `aws_iam_role.rds_proxy` with Secrets Manager GetSecretValue policy |
| 9 | IAM module has conditional OIDC provider, StringLike sub claim, and ECS RunTask/DescribeTasks/StopTask | VERIFIED | `terraform/modules/iam/main.tf` uses `count = var.create_oidc_provider ? 1 : 0` on the OIDC provider resource, `StringLike` condition for `sub` claim (`repo:${var.github_repository}:*`), and includes `ecs:RunTask`, `ecs:DescribeTasks`, `ecs:StopTask` in the GitHub Actions policy |

**Score:** 9/9 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `terraform/bootstrap/main.tf` | S3 state bucket + KMS key creation | VERIFIED | 62 lines; contains `aws_s3_bucket`, `aws_kms_key`, versioning, encryption, public access block; required_version >= 1.10, provider ~> 6.0 |
| `terraform/bootstrap/outputs.tf` | State bucket and KMS ARN outputs | VERIFIED | Exposes `state_bucket_name`, `state_bucket_arn`, `kms_key_arn` |
| `terraform/environments/staging/backend.tf` | S3 backend config with `use_lockfile = true` | VERIFIED | Correct bucket `nexus-crm-terraform-state`, key `staging/terraform.tfstate`, `use_lockfile = true` |
| `terraform/environments/prod/backend.tf` | S3 backend config with `use_lockfile = true` | VERIFIED | Correct bucket `nexus-crm-terraform-state`, key `prod/terraform.tfstate`, `use_lockfile = true` |
| `terraform/environments/staging/variables.tf` | All Phase 13 + forward-compat variables | VERIFIED | Contains `app_name`, `environment`, `aws_region`, `db_instance_class`, `db_storage_gb`, `db_multi_az`, `redis_node_type`, `github_repository`, `nat_gateway_count`, `create_oidc_provider`, `app_domain`, `acm_certificate_arn` |
| `terraform/environments/staging/terraform.tfvars` | Staging sizing values | VERIFIED | `db.t4g.medium`, `nat_gateway_count = 1`, `create_oidc_provider = true` |
| `terraform/environments/prod/terraform.tfvars` | Prod sizing values | VERIFIED | `db.t4g.large`, `db_multi_az = true`, `nat_gateway_count = 2`, `create_oidc_provider = false` |
| `terraform/modules/networking/main.tf` | VPC + RDS Proxy SG + configurable NAT | VERIFIED | RDS Proxy SG present; NAT count via `var.nat_gateway_count`; modulo routing; RDS SG ingress from rds_proxy SG only |
| `terraform/modules/rds/main.tf` | PostgreSQL 17 with parameter group | VERIFIED | engine_version 17, `aws_db_parameter_group` family postgres17, 3 parameters configured |
| `terraform/modules/rds/outputs.tf` | Includes `db_instance_identifier` | VERIFIED | `output "db_instance_identifier"` present |
| `terraform/modules/elasticache/main.tf` | Redis replication group with encryption | VERIFIED | `aws_elasticache_replication_group`, at-rest + in-transit encryption, lifecycle block |
| `terraform/modules/secrets/main.tf` | Shell resources at `/nexus/{env}/` paths | VERIFIED | 8 shell secrets, no `aws_secretsmanager_secret_version`, paths use `/nexus/` prefix |
| `terraform/modules/secrets/outputs.tf` | Individual ARN outputs | VERIFIED | `secret_arns` map + `db_password_secret_arn`, `jwt_secret_arn`, `redis_url_secret_arn`, `database_url_secret_arn` |
| `terraform/modules/rds_proxy/main.tf` | RDS Proxy with IAM auth to Secrets Manager | VERIFIED | `aws_db_proxy`, `aws_db_proxy_default_target_group`, `aws_db_proxy_target`, `aws_iam_role.rds_proxy` + policy |
| `terraform/modules/iam/main.tf` | Conditional OIDC + StringLike + ECS perms | VERIFIED | Conditional count on OIDC provider, `StringLike` sub claim, ECS RunTask/DescribeTasks/StopTask, optional S3/CloudFront via `concat()` |
| `terraform/environments/staging/main.tf` | Full Phase 13 module wiring | VERIFIED | 142 lines; 6 module blocks (networking, rds, rds_proxy, elasticache, secrets, iam); inline ECR with IMMUTABLE tags and lifecycle policies |
| `terraform/environments/staging/outputs.tf` | All Phase 14 consumption outputs | VERIFIED | vpc_id, public/private subnet ids, SG ids, rds_endpoint, rds_proxy_endpoint, redis_endpoint, api/worker ECR URLs, secret_arns, execution/task/github_actions role ARNs |
| `terraform/environments/prod/main.tf` | Identical wiring to staging | VERIFIED | 27 module+ECR resource references matching staging count |
| `terraform/environments/prod/outputs.tf` | Identical outputs to staging | VERIFIED | Same output set as staging |
| `deploy/entrypoint.sh` | Container entrypoint without Alembic | VERIFIED | 13 lines; no `alembic` string; contains `exec uvicorn` |
| `Makefile` | Terraform bootstrap, init, apply, validate, secrets targets | VERIFIED | `tf-bootstrap`, `tf-init-staging`, `tf-init-prod`, `tf-plan-staging`, `tf-plan-prod`, `tf-apply-staging`, `tf-validate`, `tf-secrets-staging`, `tf-secrets-prod` all present in .PHONY and as targets |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `terraform/environments/staging/backend.tf` | `terraform/bootstrap/main.tf` | S3 bucket name `nexus-crm-terraform-state` | WIRED | backend.tf `bucket = "nexus-crm-terraform-state"` matches bootstrap bucket resource name |
| `terraform/modules/rds/outputs.tf` | `terraform/modules/rds/main.tf` | `db_instance_identifier` output for RDS Proxy | WIRED | `output "db_instance_identifier" { value = aws_db_instance.this.identifier }` present |
| `terraform/modules/networking/outputs.tf` | `terraform/modules/networking/main.tf` | `rds_proxy_security_group_id` output | WIRED | `output "rds_proxy_security_group_id" { value = aws_security_group.rds_proxy.id }` present |
| `terraform/modules/secrets/outputs.tf` | `terraform/modules/secrets/main.tf` | `db_password_secret_arn` output | WIRED | `output "db_password_secret_arn" { value = aws_secretsmanager_secret.db_password.arn }` present |
| `terraform/environments/staging/main.tf` | `terraform/modules/rds_proxy/main.tf` | module rds_proxy source path | WIRED | `source = "../../modules/rds_proxy"` present in staging and prod |
| `terraform/environments/staging/main.tf` | `terraform/modules/secrets/outputs.tf` | `module.secrets.db_password_secret_arn` passed to rds_proxy | WIRED | `db_password_secret_arn = module.secrets.db_password_secret_arn` present in rds_proxy module block |
| `terraform/modules/iam/main.tf` | `terraform/modules/iam/variables.tf` | `create_oidc_provider` conditional | WIRED | `count = var.create_oidc_provider ? 1 : 0` in OIDC provider resource; variable declared with `default = true` |

---

### Data-Flow Trace (Level 4)

Not applicable — this phase produces Terraform IaC configuration files, not application code that renders dynamic data. All resource definitions reference actual AWS API constructs with no hardcoded return values or stub data.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `make tf-apply-staging` target exists and points to correct directory | `grep "tf-apply-staging" Makefile` | `cd terraform/environments/staging && terraform apply` | PASS |
| No alembic in entrypoint | `grep alembic deploy/entrypoint.sh` | No output | PASS |
| No flat root `.tf` files remain | `ls terraform/*.tf` | No matches found | PASS |
| No `dynamodb_table` in new backend configs | `grep dynamodb_table environments/*/backend.tf` | No matches | PASS |
| No `aws_elasticache_cluster` in elasticache module | `grep aws_elasticache_cluster modules/elasticache/main.tf` | No matches | PASS |
| No `aws_secretsmanager_secret_version` in secrets module | `grep aws_secretsmanager_secret_version modules/secrets/main.tf` | No matches | PASS |
| `terraform validate` against live AWS | Requires `terraform init` with real AWS credentials | Cannot run statically | SKIP |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| INFRA-01 | 13-01, 13-02 | VPC with public/private subnets, NAT gateway, security groups | SATISFIED | `networking/main.tf` creates VPC, 2 public subnets, 2 private subnets, configurable NAT gateways, ALB/API/worker/RDS/RDS Proxy/Redis SGs |
| INFRA-02 | 13-01, 13-02 | RDS PostgreSQL with parameter group for logical replication | SATISFIED | `rds/main.tf` engine_version=17, `aws_db_parameter_group` family=postgres17 with `rds.logical_replication=1`, `idle_in_transaction_session_timeout=30000`, `wal_sender_timeout=0` |
| INFRA-03 | 13-03 | RDS Proxy for connection pooling | SATISFIED | `rds_proxy/main.tf` with `aws_db_proxy`, default target group, proxy target; RDS SG accepts only from rds_proxy SG |
| INFRA-04 | 13-03 | ECR repos with immutable tags and lifecycle policies | SATISFIED | `environments/staging/main.tf` (and prod) inline `aws_ecr_repository` with `image_tag_mutability = "IMMUTABLE"` + `aws_ecr_lifecycle_policy` keeping last 10 images |
| INFRA-07 | 13-02 | Secrets Manager secrets at `/nexus/staging/` and `/nexus/prod/` paths | SATISFIED | `secrets/main.tf` creates shell resources at `/nexus/${var.environment}/` paths; `db_password`, `jwt_secret`, `redis_url` (and 5 others) present; no plaintext in state |
| INFRA-09 | 13-02 | ElastiCache Redis provisioned cluster (not Serverless) | SATISFIED | `elasticache/main.tf` uses `aws_elasticache_replication_group` (not Serverless); engine 7.1 with encryption |
| INFRA-10 | 13-03 | IAM OIDC provider and GitHub Actions deployment role with least-privilege perms | SATISFIED | `iam/main.tf` conditional OIDC creation; `StringLike` sub claim; ECR push permissions; ECS DescribeServices/UpdateService/RunTask/DescribeTasks/StopTask; `secretsmanager:GetSecretValue` scoped to `/nexus/{env}/*` |

All 7 phase requirements satisfied. INFRA-05, INFRA-06, INFRA-08 are correctly deferred to Phase 14 and not claimed by Phase 13 plans.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `Makefile` | 33–36 | `tf-plan` and `tf-apply` legacy targets reference `terraform/terraform.tfvars` (deleted in Plan 01 Task 2) | Warning | These targets will fail with "No such file or directory" if run. Phase 13's goal target `tf-apply-staging` is unaffected — it points to `terraform/environments/staging`. Legacy targets are a cleanup item. |

No TODO/FIXME/placeholder comments found in Phase 13 Terraform files. No stub return values. No empty implementations.

---

### Human Verification Required

#### 1. Live apply against AWS account

**Test:** Run `make tf-bootstrap` followed by `make tf-init-staging` and `make tf-apply-staging` against a real AWS account with appropriate credentials.
**Expected:** All resources provision without error: VPC, 2 public + 2 private subnets, 1 NAT gateway, 6 SGs, RDS PG17 instance, RDS Proxy, ElastiCache Redis, 8 Secrets Manager shell secrets, 2 ECR repos (api + worker), OIDC provider, and 3 IAM roles. State file is written to `nexus-crm-terraform-state` S3 bucket at key `staging/terraform.tfstate`.
**Why human:** Requires live AWS credentials, S3 bucket pre-creation via bootstrap, and actual API provisioning. Static analysis cannot exercise AWS API calls.

#### 2. Legacy Makefile target cleanup confirmation

**Test:** Review `tf-plan` (line 33) and `tf-apply` (line 36) in `Makefile` — both reference `cd terraform && terraform plan/apply -var-file=terraform.tfvars` which points to the now-deleted flat root.
**Expected:** Either these targets are removed (they predate Phase 13 and are superseded by `tf-plan-staging` / `tf-apply-staging`), or they are updated to reference an environment directory.
**Why human:** Whether to remove or update these targets is a team decision. They do not block Phase 14 but would cause confusing failures if accidentally invoked.

---

### Gaps Summary

No gaps found. All 9 observable truths are verified against the actual codebase. All 7 phase requirements (INFRA-01, 02, 03, 04, 07, 09, 10) are satisfied with substantive, wired implementation. The one warning (legacy Makefile targets) does not affect the phase goal — `make tf-apply-staging` is correctly wired to `terraform/environments/staging`.

The only outstanding items require live AWS execution (human verification above), which is expected for an IaC phase.

---

_Verified: 2026-03-29_
_Verifier: Claude (gsd-verifier)_
