---
phase: 13
slug: aws-core-infrastructure
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-29
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | terraform validate / terraform plan (dry-run) |
| **Config file** | environments/staging/main.tf, environments/prod/main.tf |
| **Quick run command** | `terraform validate` |
| **Full suite command** | `terraform plan -out=tfplan` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `terraform validate`
- **After every plan wave:** Run `terraform plan -out=tfplan`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 13-01-T1 | 01 | 1 | INFRA-01, INFRA-02 | structural | `ls terraform/bootstrap/main.tf terraform/environments/staging/backend.tf terraform/environments/prod/backend.tf && echo OK` | ⬜ pending |
| 13-01-T2 | 01 | 1 | INFRA-01 (D-03) | structural | `test ! -f terraform/main.tf && test -d terraform/modules && test -d terraform/environments && echo OK` | ⬜ pending |
| 13-02-T1 | 02 | 2 | INFRA-01, INFRA-02 | structural | `grep "rds_proxy" terraform/modules/networking/main.tf && grep 'engine_version.*"17"' terraform/modules/rds/main.tf && echo OK` | ⬜ pending |
| 13-02-T2 | 02 | 2 | INFRA-09, INFRA-07 | structural | `grep "aws_elasticache_replication_group" terraform/modules/elasticache/main.tf && grep "/nexus/" terraform/modules/secrets/main.tf && echo OK` | ⬜ pending |
| 13-03-T1 | 03 | 3 | INFRA-03, INFRA-10 | structural | `grep "aws_db_proxy" terraform/modules/rds_proxy/main.tf && grep "StringLike" terraform/modules/iam/main.tf && echo OK` | ⬜ pending |
| 13-03-T2 | 03 | 3 | INFRA-04, DEPLOY-05 | structural | `grep "IMMUTABLE" terraform/environments/staging/main.tf && test -f terraform/environments/prod/outputs.tf && grep "rds_proxy_endpoint" terraform/environments/prod/outputs.tf && ! grep "alembic" deploy/entrypoint.sh && echo OK` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `environments/staging/` directory with backend.tf, variables.tf, terraform.tfvars
- [ ] `environments/prod/` directory with backend.tf, variables.tf, terraform.tfvars
- [ ] `terraform/bootstrap/` directory with main.tf, outputs.tf

*Wave 0 (Plan 01) creates the Terraform environment directory structure before modules can be validated.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RDS reachable from private subnet via Proxy | INFRA-03 | Requires live AWS resources | Connect via bastion/ECS task: `psql -h <rds-proxy-endpoint> -U postgres` |
| ElastiCache reachable from ECS SG | INFRA-09 | Requires live AWS resources | Connect via ECS task: `redis-cli -h <redis-endpoint> ping` |
| ECR test push succeeds | INFRA-04 | Requires ECR repo and Docker | `docker push <ecr-uri>:<sha-tag>` then verify in console |
| OIDC role can assume via GitHub Actions | INFRA-10 | Requires live AWS + GitHub Actions | Run workflow job, check it assumes role without error |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all structural prerequisites
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
