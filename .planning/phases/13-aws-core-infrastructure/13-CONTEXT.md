# Phase 13: AWS Core Infrastructure - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Provision all foundational AWS networking, data stores, secrets, and access control via Terraform.
Phase 14 (compute, CDN, HTTPS) and Phase 15 (CI/CD) reference these outputs — nothing runs until Phase 13 is complete and `terraform apply` succeeds in both environments.

Scope (INFRA-01, -02, -03, -04, -07, -09, -10):
- VPC, subnets, NAT gateway, security groups (INFRA-01)
- RDS PostgreSQL with custom parameter group for logical replication readiness (INFRA-02)
- RDS Proxy for connection pooling (INFRA-03)
- ECR repositories — api and worker — with immutable tags and lifecycle policies (INFRA-04)
- AWS Secrets Manager secrets at `/nexus/staging/` and `/nexus/prod/` paths (INFRA-07)
- ElastiCache provisioned Redis replication group (not Serverless, not single-node cluster) (INFRA-09)
- IAM OIDC provider and GitHub Actions deployment role with least-privilege permissions (INFRA-10)

NOT in this phase: ALB, CloudFront, S3 frontend bucket, ECS cluster/task definitions, ACM cert, Route 53 (those are Phase 14).

</domain>

<decisions>
## Implementation Decisions

### Terraform Repository Structure
- **D-01:** Refactor from the current flat `terraform/` layout to `environments/staging/` and `environments/prod/` directories. Each environment directory contains its own `main.tf`, `backend.tf` (or `backend.tfvars`), `variables.tf`, `outputs.tf`, and `terraform.tfvars`. This matches DEPLOY-04 exactly (separate state files per environment).
- **D-02:** Shared module code stays in `terraform/modules/` — no relocation. Environment directories reference modules via relative paths (e.g., `source = "../../modules/networking"`).
- **D-03:** The existing flat root wiring files (`terraform/main.tf`, `terraform/variables.tf`, `terraform/outputs.tf`, `terraform/terraform.tfvars`) are deleted/replaced once the `environments/` structure is in place. No two competing entry points.

### Claude's Discretion
The following areas were not discussed — planner has full discretion:

- **State backend bootstrap:** Create the S3 state bucket (versioned, KMS-encrypted, native locking via `use_lockfile = true`) before `terraform init`. Recommended: a Makefile target or `terraform/bootstrap/` config that uses a local backend, creates the bucket, then is discarded. Document the one-time operator steps clearly.
- **Secret values strategy:** Existing modules store actual secret values in Terraform state. Preferred approach (from INFRA-07 + research): create AWS Secrets Manager "shell" resources in Terraform (name + KMS key only), populate values out-of-band via AWS CLI or console, so plaintext never lives in tfstate. If this adds complexity, document the mitigation (state encryption + IAM policy restricting state bucket access).
- **Module fixes vs community modules:** Extend and fix the existing custom modules rather than migrating to terraform-aws-modules community modules (less churn). Required fixes: RDS PG15→17, add custom parameter group (logical replication), add RDS Proxy module, change ECR to IMMUTABLE tags + add lifecycle policies, change ElastiCache from `aws_elasticache_cluster` to `aws_elasticache_replication_group`.
- **AWS provider version:** Upgrade from `~> 5.0` to `~> 6.0` (research-recommended 6.38.0 confirmed) and Terraform to `~> 1.10`. Do this in the same PR as the structure refactor.
- **entrypoint.sh migration removal:** The existing `deploy/entrypoint.sh` runs `alembic upgrade head` at container start (DEPLOY-05 violation). This must be removed as part of Phase 13 work (it's a precondition for safe Phase 15 pipeline). It's a one-line deletion.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §"AWS Infrastructure" — INFRA-01 through INFRA-10 with acceptance criteria
- `.planning/REQUIREMENTS.md` §"CI/CD Pipeline" — DEPLOY-04 and DEPLOY-05 (env separation + entrypoint removal)

### Research
- `.planning/research/SUMMARY.md` — critical constraints, recommended build order, open questions (RDS Proxy, ACM region note, secret injection pitfalls)

### Existing Terraform Code (to refactor, not start from scratch)
- `terraform/main.tf` — current root wiring (all modules wired here; this becomes the template for environments/staging/main.tf and environments/prod/main.tf)
- `terraform/modules/networking/main.tf` — VPC, subnets, NAT gateway (largely correct, verify security group rules)
- `terraform/modules/rds/main.tf` — RDS instance (needs: PG15→17, custom parameter group, RDS Proxy)
- `terraform/modules/elasticache/main.tf` — Redis (needs: cluster→replication_group)
- `terraform/modules/secrets/main.tf` — Secrets Manager (verify path format matches `/nexus/{env}/`)
- `terraform/modules/iam/main.tf` — OIDC provider + roles (verify subject claim scope)
- `deploy/entrypoint.sh` — contains Alembic call that must be removed (DEPLOY-05)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `terraform/modules/networking/` — VPC module is largely correct; security group CIDR rules need verification against Phase 13 success criteria (ALB → ECS, ECS → RDS/Redis only)
- `terraform/modules/iam/` — OIDC provider and execution/task roles exist; GitHub Actions role needs least-privilege ECS/ECR/Secrets permissions per INFRA-10
- `terraform/modules/secrets/` — Secret structure exists; path format and shell-resource pattern need verification
- `terraform/variables.tf` — Variables are well-defined; these migrate into per-environment `variables.tf` files with environment-specific defaults in `terraform.tfvars`

### Established Patterns
- All modules follow the same 3-file pattern: `main.tf`, `variables.tf`, `outputs.tf` — new RDS Proxy module should follow this
- `local.name_prefix = "${var.app_name}-${var.environment}"` naming convention is consistent throughout — keep it
- Default tags via AWS provider `default_tags` block — preserve this pattern in per-environment providers

### Integration Points
- Phase 14 modules (ALB, CloudFront, ECS) reference outputs from Phase 13 modules (subnet IDs, security group IDs, secret ARNs, ECR URIs) — outputs.tf files in environments/ must expose all of these
- Phase 15 CI/CD reads `ECR_API_URI`, `ECS_CLUSTER`, secrets ARNs from Phase 13 outputs (or hardcoded in GitHub vars)

</code_context>

<specifics>
## Specific Ideas

No specific references or "I want it like X" moments — standard infrastructure, follow the research recommendations and requirements.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-aws-core-infrastructure*
*Context gathered: 2026-03-29*
