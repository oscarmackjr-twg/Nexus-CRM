# Research Summary: v1.2 Cloud Deployment

**Project:** Nexus CRM — v1.2 Cloud Deployment
**Scope:** AWS ECS Fargate primary + Azure warm failover, Terraform IaC, GitHub Actions CI/CD
**Researched:** 2026-03-29
**Overall Confidence:** MEDIUM-HIGH

---

## Stack Additions

New tools and services introduced by this milestone (not part of the existing Docker Compose stack):

| Tool / Service | Version / Tier | Purpose |
|----------------|----------------|---------|
| Terraform CLI | `~> 1.10` (pin `>= 1.10, < 2.0`) | IaC for all AWS and Azure resources |
| `hashicorp/aws` provider | `~> 6.0` (6.38.0 confirmed) | All AWS resource management |
| `hashicorp/azurerm` provider | `~> 4.0` (4.66.0 confirmed) | All Azure resource management |
| `terraform-aws-modules/vpc` | `~> 6.6` | VPC, subnets, NAT gateways |
| `terraform-aws-modules/ecs` | `~> 7.5` | ECS cluster, services, task definitions |
| `terraform-aws-modules/rds` | `~> 6.10` | RDS PostgreSQL 17, Multi-AZ, parameter group |
| `terraform-aws-modules/elasticache` | `~> 1.0` | Provisioned Redis OSS 7.x |
| `terraform-aws-modules/alb` | `~> 9.0` | ALB, listeners, target groups |
| `terraform-aws-modules/acm` | `~> 5.0` | ACM TLS cert with Route 53 DNS validation |
| AWS ECR | — | Container image registry (3 repos: api, worker; + frontend if needed) |
| AWS Secrets Manager | — | Secret injection into ECS tasks at startup |
| AWS CloudFront + S3 | — | Static frontend hosting (preferred over nginx-in-ECS) |
| AWS Route 53 | — | DNS, health checks, failover routing policy |
| Azure PostgreSQL Flexible Server | PG 17, `GP_Standard_D2s_v3` | Warm failover database (logical replication subscriber) |
| Azure Container Instances (ACI) | Basic tier standby | Warm failover compute (pre-deployed, stopped) |
| Azure Container Registry (ACR) | Basic SKU | Mirror of ECR images for ACI pull |
| Azure Key Vault | — | Mirrors Secrets Manager values for ACI containers |
| GitHub Actions OIDC | — | Keyless AWS + Azure auth (no stored long-lived credentials) |
| `actions/checkout` | `v4` | Source checkout |
| `aws-actions/configure-aws-credentials` | `v4` | OIDC-based AWS auth |
| `aws-actions/amazon-ecr-login` | `v2` | Docker → ECR authentication |
| `docker/build-push-action` | `v6` | Multi-platform image build and push |
| `aws-actions/amazon-ecs-deploy-task-definition` | `v1` | Rolling ECS service deploy |
| `azure/login` | `v2` | OIDC-based Azure auth |

---

## Critical Constraints

Non-negotiable facts that must shape every requirement and task:

1. **RDS parameter group must be custom and set at initial provisioning.** `rds.logical_replication = 1` requires an instance reboot — acceptable once at creation, disruptive later. Also set `wal_sender_timeout = 0` and `idle_in_transaction_session_timeout = 30000` from day one.

2. **Alembic migration must run as a separate one-off ECS task before any service update.** Running `alembic upgrade head` inside the app entrypoint causes concurrent migration races across ECS tasks. The pipeline must: (a) run migration task, (b) wait for exit 0, (c) only then deploy services.

3. **ECS secrets must use the `secrets` block, never `environment`.** Values placed in the `environment` block appear in CloudWatch logs and the AWS console in plaintext. All credentials go in Secrets Manager and are referenced via ARN.

4. **Image tags must use the Git commit SHA, not `latest`.** Since mid-2024, ECS pins image digests at deployment start — floating tags silently run stale code. Enable ECR tag immutability.

5. **Terraform must use separate environment directories (`environments/staging/`, `environments/prod/`), not workspaces.** Workspaces share one state file and one set of credentials; HashiCorp explicitly discourages them for environment isolation.

6. **Logical replication does not replicate DDL.** Every Alembic migration that runs on RDS must also be applied to the Azure Flexible Server before or alongside the AWS migration. Schema parity is a required pipeline step, not an afterthought.

7. **The JWT secret must be identical in both clouds.** Sessions started on AWS must decode on Azure after failover. A single JWT secret is generated once, stored in both AWS Secrets Manager and Azure Key Vault.

8. **ECS platform must target `linux/amd64`.** Fargate does not support ARM64 in all regions. Build images with `--platform linux/amd64` regardless of local machine architecture.

9. **ElastiCache Serverless must not be used as a Celery broker.** Documented compatibility issues with Celery 5.3+ (AWS re:Post, 2025). Use a provisioned ElastiCache replication group.

10. **Azure failover is manual-only.** Automated Route 53 health-check-triggered DNS cutover to Azure is an anti-feature — cross-cloud health checks have false positive rates that make auto-cutover dangerous. Route 53 health checks are for alerting; the actual cutover follows a human-executed runbook.

---

## Feature Table Stakes

Minimum behaviors required for "done" at each area:

### AWS Core Deployment

| Behavior | "Done" Looks Like |
|----------|------------------|
| API reachable over HTTPS | `GET https://crm.twgasia.com/api/v1/health` returns 200 |
| Frontend served statically | React SPA loads from CloudFront/S3; `/api/*` routes to ALB |
| ECS tasks in private subnets | No task has a public IP; ALB is the only public ingress |
| Secrets injected at task start | `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY` present as env vars in running tasks |
| Database migrations run before deploy | Pipeline: migration exit 0 → service update; never simultaneously |
| Zero-downtime rolling deploy | `minimum_healthy_percent = 100`, `maximum_percent = 200`, circuit breaker enabled with auto-rollback |
| ECS deployment circuit breaker | Failed deploy reverts to previous task def revision without operator action |
| Health check on `/health` | FastAPI returns 200 with DB connectivity check; ALB and container health checks both pass |
| CloudWatch logs per container | Each service has a named log group; no log output is lost |

### Multi-Environment

| Behavior | "Done" Looks Like |
|----------|------------------|
| Staging auto-deploys on push to `main` | GitHub Actions triggers staging deploy on merge |
| Production requires manual approval | GitHub Environment protection rule gates prod deploy |
| Environments use separate state files | `staging/terraform.tfstate` and `prod/terraform.tfstate` in same S3 bucket, distinct keys |
| Staging uses smaller instance classes | `db.t4g.medium`, `cache.t4g.small`, ECS desired count 1 |

### Azure Warm Failover

| Behavior | "Done" Looks Like |
|----------|------------------|
| Azure infrastructure pre-deployed | `terraform apply` for azure module succeeds; ACI containers stopped/idle |
| Images mirrored to ACR on every deploy | CI pushes to ECR and ACR in same workflow run |
| Azure DB schema matches RDS | Alembic runs against Azure after every RDS migration |
| Azure DB receives data sync | Logical replication active (continuous) OR scheduled pg_dump/restore documented with RPO |
| Failover runbook exists and is tested | Runbook is documented and has been executed once against staging |
| JWT secret mirrors in Azure Key Vault | Same value as Secrets Manager; ACI containers boot and accept existing sessions |

---

## Watch Out For

Top pitfalls with the highest impact/likelihood for this build:

1. **Alembic migration race (CRITICAL).** If the entrypoint runs `alembic upgrade head` and uvicorn together, ECS rolling deploys start multiple migration runners concurrently against the same `alembic_version` table. Fix: strip `alembic upgrade head` from `entrypoint.sh`; run it exclusively as a one-off ECS task in CI before any service update. Also add `concurrency: group: deploy-${{ github.ref }}` in GitHub Actions to prevent parallel pipeline runs.

2. **RDS parameter group locked at default.** The default parameter group (`default.postgres17`) is read-only — cannot set `rds.logical_replication`, `max_connections`, or `idle_in_transaction_session_timeout`. A custom `aws_db_parameter_group` must be created and assigned at initial `terraform apply`. Changing it post-creation requires a reboot. Do not skip this.

3. **Azure logical replication slot lost on Flexible Server HA failover.** When Azure Flexible Server fails over to its standby, logical replication slots are destroyed. Install the `pg_failover_slots` extension and set `pg_failover_slots.enabled = on` in `azurerm_postgresql_flexible_server_configuration`. Monitor replication lag via CloudWatch and Azure Monitor; alert if lag exceeds 5 minutes.

4. **ECS `terraform apply` triggers unnecessary rolling restarts.** Any Terraform change to `aws_ecs_service` (even a tag) causes ECS to replace tasks. Use `lifecycle { ignore_changes = [task_definition] }` on all ECS service resources. Terraform owns infrastructure; GitHub Actions owns image versions and service updates.

5. **`latest` image tag silently runs stale code.** Since June 2024, ECS caches image digests at deploy start — re-pushing to `latest` does not update running tasks. Tag all images with `$GITHUB_SHA`. Enable ECR tag immutability on all repositories.

6. **Logical replication does not replicate DDL.** Logical replication sends DML only. The Azure Flexible Server has no tables until the schema is applied separately. Add a pipeline step: after each successful RDS migration, run the same Alembic migration against the Azure connection string. If this step is skipped, the Azure DB silently falls behind and cannot receive replicated rows.

---

## Recommended Build Order

Derived from hard infrastructure dependencies identified across all four research files:

### Phase 1 — Terraform Bootstrap (state backend)
**Must come first because:** Terraform cannot `init` with an S3 backend until the bucket exists. This is a one-time manual step.
- Create S3 bucket (versioned, KMS-encrypted) for state
- Enable S3 native locking (`use_lockfile = true` — DynamoDB is deprecated for this)
- Create `environments/staging/backend.tfvars` and `environments/prod/backend.tfvars`
- Run `terraform init -backend-config=backend.tfvars` in each environment directory

### Phase 2 — AWS Core Infrastructure (networking + data stores + IAM + ECR)
**Must come before compute because:** ECS and ALB require subnet IDs, security group IDs, secrets ARNs, and ECR URIs. RDS parameter group changes require a reboot — acceptable at initial provisioning, not acceptable post-launch.
- VPC, subnets (public/private), NAT gateways, security groups
- RDS PostgreSQL with custom parameter group (`rds.logical_replication=1`, `idle_in_transaction_session_timeout=30000`, `wal_sender_timeout=0`)
- ElastiCache Redis (provisioned, not serverless)
- AWS Secrets Manager secrets (shell resources only — populate values out-of-band to keep them out of Terraform state)
- IAM: execution role, task role, GitHub Actions OIDC role
- ECR repositories (one per image: api, worker)
- S3 assets bucket and S3 frontend bucket

### Phase 3 — AWS Compute and CDN
**Depends on Phase 2 outputs** (subnet IDs, security group IDs, secrets ARNs, ECR URIs).
- ALB with HTTP→HTTPS redirect, target groups
- ACM certificate with Route 53 DNS validation
- ECS cluster + api service + worker service task definitions
- CloudFront distribution with S3 default behavior and `/api/*` ALB behavior
- Route 53 A alias record to CloudFront

### Phase 4 — First Image Push and GitHub Actions Pipeline
**Depends on Phase 2 (ECR repos exist) and Phase 3 (ECS services exist).**
- Build and push first Docker images to ECR (bootstraps ECS pending state)
- Create `.github/workflows/deploy.yml` with full pipeline: build → ECR push → migration task → ECS deploy → frontend S3 sync → CloudFront invalidation
- Add GitHub secrets/vars: `AWS_ROLE_ARN`, `ECR_API_URI`, `ECS_CLUSTER`, `ECS_API_SERVICE`, `ECS_WORKER_SERVICE`, `S3_FRONTEND_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`
- Verify end-to-end via CloudFront default domain before custom DNS

### Phase 5 — HTTPS and Custom Domain
**Depends on Phase 3 (CloudFront ARN and ALB DNS name).** ACM cert validation can overlap with Phase 3 but HTTPS is not usable until the cert is issued.
- Set DNS TTL to 300s on `crm.twgasia.com` before cutover
- Route 53 records: A alias to CloudFront, CNAME for ACM validation
- Smoke-test all routes through `crm.twgasia.com`

### Phase 6 — Azure Warm Failover Infrastructure
**Last because:** depends on a live RDS endpoint (Phase 2) as replication source, ECR image URIs (Phase 4) to mirror, and RDS parameter group changes (Phase 2) already applied. Prod-only; staging does not need a warm failover.
- Azure resource group, VNet, private DNS zones, delegated subnets
- Azure PostgreSQL Flexible Server (PG 17, matching RDS version)
- Apply schema to Azure DB via pg_dump --schema-only from RDS
- Configure pglogical subscription (AWS RDS publisher → Azure subscriber) with SSL
- Install and enable `pg_failover_slots` extension
- Azure Container Registry (Basic SKU), push initial images from CI
- Azure Container Instances (api + worker) referencing ACR images, stopped/idle
- Azure Key Vault with mirrored secrets (including matching JWT secret)
- Add Azure migration propagation step to GitHub Actions pipeline (run Alembic against Azure after each successful RDS migration)
- Execute failover runbook once against staging to validate procedure
- Add Route 53 health check and alerting (not auto-cutover)

---

## Open Questions

Decisions that need user input before or during planning:

1. **RPO/RTO target for Azure failover.** Continuous logical replication delivers RPO < 5 min but adds operational complexity (slot monitoring, `pg_failover_slots`, DDL propagation pipeline step, WAL egress cost ~$0.09/GB). Periodic pg_dump every 4 hours is much simpler but accepts up to 4-hour data loss. Which is acceptable? Research recommends starting with pg_dump and documenting the DMS/pglogical upgrade path.

2. **Frontend architecture: CloudFront + S3 vs nginx-in-ECS.** CloudFront + S3 is the more idiomatic AWS pattern for a React SPA, is cheaper, and eliminates a container from ECS. Nginx-in-ECS preserves parity with Docker Compose. Both are researched. Which does the team prefer?

3. **RDS instance size for production.** Research suggests `db.t4g.medium` (staging) / `db.r8g.large` (prod). Is `db.r8g.large` within budget, or should `db.t4g.large` be evaluated as a lower-cost prod option?

4. **Domain name and Route 53 hosted zone.** Research uses `crm.twgasia.com` as a placeholder. Is this the intended production domain? Does the team control Route 53 for this zone, or will DNS be delegated from an external registrar?

5. **AWS region.** Research references `ap-southeast-1` (Singapore) with Azure `Southeast Asia` as co-located failover region. Is this the confirmed primary region, or is another region preferred?

6. **Connection pooling strategy.** The RDS connection exhaustion pitfall strongly recommends RDS Proxy (AWS-native, transparent to the app). RDS Proxy adds ~$0.015/hour cost and ~3ms latency. Is this acceptable, or will the team manage `pool_size` per task manually?

7. **Existing Terraform structure migration.** The codebase currently has a single-root Terraform module (`terraform/`) with modules called from one `main.tf`. Research recommends migrating to `environments/staging/` and `environments/prod/` directories. This is a refactor step — when should it happen, and is there risk appetite for it before the first cloud deploy?

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack (Terraform providers and modules) | MEDIUM-HIGH | Provider major versions confirmed; module patch versions change frequently — pin to minor (`~> X.Y`) not exact |
| Features (ECS deployment behaviors) | HIGH | AWS deployment patterns well-documented in official docs; secrets injection and rolling deploy are verified |
| Features (Azure warm failover) | MEDIUM | ACI stopped-container standby pattern is verified; pglogical cross-cloud replication has fewer independent sources |
| Architecture (AWS side) | HIGH | Read existing Terraform modules directly; CloudFront+ALB+ECS+S3 pattern verified against current code |
| Architecture (Azure side) | MEDIUM | Azure Flexible Server + ACI pattern is documented; pglogical DDL constraint is a known limitation requiring operational discipline |
| Pitfalls (ECS/Alembic/Secrets) | MEDIUM-HIGH | Multiple independent sources confirm the migration race, tag staleness, and secret injection pitfalls |
| Pitfalls (cross-cloud replication) | MEDIUM | `pg_failover_slots` slot loss issue has Microsoft documentation; WAL egress cost is an estimate |

**Overall confidence: MEDIUM-HIGH**

### Gaps to Address During Planning

- **WAL egress cost baseline:** Before committing to continuous logical replication, measure actual WAL generation rate on the existing database. Decision between pg_dump and pglogical cannot be finalized without this data point.
- **RDS Proxy decision:** Must be resolved before ECS task definition pool_size parameters are set. This affects the IAM policy, the Terraform RDS module, and the task definition environment variables.
- **ACM certificate region for CloudFront:** ACM certificates for CloudFront distributions must be in `us-east-1`, not the deployment region. If the team deploys to a non-`us-east-1` region, a separate provider alias for `us-east-1` must be added to Terraform.
- **`entrypoint.sh` migration removal:** The existing entrypoint runs `alembic upgrade head` before uvicorn. This must be removed before the first ECS deploy or it will cause migration races on every rolling deploy. This is a code change, not a Terraform change.

---

*Research completed: 2026-03-29*
*Ready for roadmap: yes*
