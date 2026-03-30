---
phase: 13
slug: aws-core-infrastructure
status: draft
nyquist_compliant: false
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

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | INFRA-01 | structural | `terraform validate` | ❌ W0 | ⬜ pending |
| 13-01-02 | 01 | 1 | INFRA-02 | structural | `terraform validate` | ❌ W0 | ⬜ pending |
| 13-02-01 | 02 | 1 | INFRA-03 | structural | `terraform validate` | ❌ W0 | ⬜ pending |
| 13-02-02 | 02 | 1 | INFRA-04 | structural | `terraform validate` | ❌ W0 | ⬜ pending |
| 13-03-01 | 03 | 2 | INFRA-07 | structural | `terraform validate` | ❌ W0 | ⬜ pending |
| 13-04-01 | 04 | 2 | INFRA-09 | structural | `terraform validate` | ❌ W0 | ⬜ pending |
| 13-04-02 | 04 | 2 | INFRA-10 | manual | `aws sts get-caller-identity` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `environments/staging/` directory with main.tf, variables.tf, outputs.tf, backend.tf
- [ ] `environments/prod/` directory with main.tf, variables.tf, outputs.tf, backend.tf
- [ ] Terraform initialized in both environment directories

*Wave 0 creates the Terraform environment directory structure before modules can be validated.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RDS reachable from private subnet | INFRA-03 | Requires live AWS resources | Connect via bastion/ECS task: `psql -h <rds-endpoint> -U postgres` |
| ElastiCache reachable from ECS SG | INFRA-04 | Requires live AWS resources | Connect via ECS task: `redis-cli -h <redis-endpoint> ping` |
| ECR test push succeeds | INFRA-09 | Requires ECR repo and Docker | `docker push <ecr-uri>:<sha-tag>` then verify in console |
| OIDC role can read Secrets Manager | INFRA-10 | Requires live AWS + GitHub Actions | Run workflow job, check it reads secrets without error |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
