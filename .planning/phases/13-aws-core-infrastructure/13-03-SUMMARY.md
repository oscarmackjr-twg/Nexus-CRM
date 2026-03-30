---
phase: 13-aws-core-infrastructure
plan: "03"
subsystem: infrastructure/terraform
tags: [terraform, rds-proxy, iam, ecr, entrypoint, environments]
dependency_graph:
  requires: ["13-02"]
  provides: ["complete-phase-13-terraform", "environment-wiring", "rds-proxy-module"]
  affects: ["14-ecs-fargate", "15-cicd"]
tech_stack:
  added: []
  patterns:
    - "RDS Proxy via aws_db_proxy + Secrets Manager IAM role"
    - "Conditional OIDC provider creation (count = var.create_oidc_provider ? 1 : 0)"
    - "StringLike wildcard sub claim for GitHub Actions OIDC"
    - "Inline ECR resources in environment main.tf (not a module)"
    - "concat() with conditional empty array for optional IAM policy statements"
key_files:
  created:
    - terraform/modules/rds_proxy/main.tf
    - terraform/modules/rds_proxy/variables.tf
    - terraform/modules/rds_proxy/outputs.tf
    - terraform/environments/staging/main.tf
    - terraform/environments/staging/outputs.tf
    - terraform/environments/prod/main.tf
    - terraform/environments/prod/outputs.tf
  modified:
    - terraform/modules/iam/main.tf
    - terraform/modules/iam/variables.tf
    - deploy/entrypoint.sh
    - Makefile
decisions:
  - "ECR repos inline in environment main.tf (not in a module) per INFRA-04 — only api and worker, frontend uses S3+CloudFront"
  - "RDS Proxy uses SECRETS auth scheme with IAM role for Secrets Manager access (not IAM database auth on the auth block)"
  - "IAM OIDC provider conditional on var.create_oidc_provider — prod sets false to reuse staging's account-scoped provider"
  - "secret_arn_pattern uses /nexus/environment/* not /app_name/environment/* — matches Makefile tf-secrets-* targets"
  - "Makefile tf-secrets-staging/prod write to /nexus/{env}/db_password and jwt_secret only — remaining secrets populated post-apply"
  - "terraform fmt applied to elasticache/main.tf to fix pre-existing alignment issue (whitespace only)"
metrics:
  duration: "3 min"
  completed: "2026-03-30"
  tasks_completed: 2
  files_changed: 11
---

# Phase 13 Plan 03: RDS Proxy + IAM Fixes + Environment Assembly Summary

RDS Proxy Terraform module created, IAM module fixed with conditional OIDC and ECS RunTask permissions, and both staging/prod environments fully wired with all 6 Phase 13 modules, inline ECR repos, and lifecycle policies. Entrypoint.sh stripped of Alembic (DEPLOY-05 satisfied).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create RDS Proxy module and fix IAM module | b46c17c | terraform/modules/rds_proxy/ (3 files), terraform/modules/iam/ (3 files) |
| 2 | Wire environment main.tf + outputs.tf, ECR inline, entrypoint fix, Makefile, validate | 019c401 | terraform/environments/staging/ (2 files), terraform/environments/prod/ (2 files), deploy/entrypoint.sh, Makefile, terraform/modules/elasticache/main.tf |

## Decisions Made

1. **ECR inline**: ECR repositories are inline in environment main.tf (not a module) per plan requirement INFRA-04 — only api and worker containers, frontend is served from S3+CloudFront.

2. **RDS Proxy auth**: Using SECRETS auth scheme with an IAM role that grants the proxy access to Secrets Manager. The `iam_auth = "DISABLED"` field refers to IAM database authentication on the proxy itself, not the Secrets Manager access (which is handled by the IAM role).

3. **Conditional OIDC**: Production environment sets `create_oidc_provider = false` in terraform.tfvars — the OIDC provider is account-scoped and only needs to exist once (staging creates it).

4. **Secret path pattern**: `secret_arn_pattern` uses `/nexus/${var.environment}/*` to match the Makefile tf-secrets-* targets which write to `/nexus/staging/db_password`, etc.

5. **Optional bucket ARNs**: `assets_bucket_arn` and `frontend_bucket_arn` default to `""` — the IAM policy uses `concat()` with conditional empty arrays so Phase 13 environments don't need Phase 14 bucket ARNs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing terraform fmt issue in elasticache/main.tf**
- **Found during:** Task 2 post-creation validation
- **Issue:** `terraform fmt -check -recursive` reported elasticache/main.tf had alignment formatting errors (extra spaces in attribute alignment)
- **Fix:** Ran `terraform fmt -recursive terraform/` — whitespace-only alignment change, no logic change
- **Files modified:** terraform/modules/elasticache/main.tf
- **Commit:** 019c401

## Verification Results

- All 6 modules referenced in environments/staging/main.tf: networking, rds, rds_proxy, elasticache, secrets, iam
- ECR repos have IMMUTABLE tags + lifecycle policies keeping last 10 images
- RDS Proxy module has aws_db_proxy + target group + target
- IAM OIDC uses StringLike with wildcard, conditional provider creation
- deploy/entrypoint.sh has no alembic reference
- `terraform fmt -check -recursive terraform/` reports no formatting issues
- All module source paths (../../modules/*) resolve to existing directories

## Known Stubs

None — all resources are complete infrastructure definitions. No stub data or placeholder values that would prevent Phase 14 from consuming these outputs.

## Self-Check: PASSED

Files verified:
- FOUND: terraform/modules/rds_proxy/main.tf
- FOUND: terraform/modules/rds_proxy/variables.tf
- FOUND: terraform/modules/rds_proxy/outputs.tf
- FOUND: terraform/environments/staging/main.tf
- FOUND: terraform/environments/staging/outputs.tf
- FOUND: terraform/environments/prod/main.tf
- FOUND: terraform/environments/prod/outputs.tf
- FOUND: terraform/modules/iam/main.tf (modified)
- FOUND: deploy/entrypoint.sh (modified)
- FOUND: Makefile (modified)

Commits verified:
- FOUND: b46c17c (feat(13-03): create RDS Proxy module and fix IAM module)
- FOUND: 019c401 (feat(13-03): wire environments, inline ECR, fix entrypoint, add Makefile targets)
