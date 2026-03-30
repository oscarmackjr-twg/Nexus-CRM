# Features Research: Cloud Deployment

**Project:** Nexus CRM v1.2 Cloud Deployment
**Researched:** 2026-03-29
**Overall confidence:** MEDIUM-HIGH (AWS patterns HIGH, cross-cloud Azure failover MEDIUM)

---

## Core AWS Deployment

### Table Stakes

Users of a production ECS Fargate deployment expect the following to work without manual intervention:

| Behavior | Why Expected | Complexity |
|----------|--------------|------------|
| Each service (API, Celery worker) runs as a separate ECS service | Allows independent scaling and restarts; workers cannot be behind an ALB | Low |
| API and frontend served via ALB on port 443 | All public traffic HTTPS-only; ALB terminates TLS | Low |
| Containers in private subnets; ALB in public subnets | Security baseline; tasks are not publicly addressable | Medium |
| NAT Gateway for outbound calls from private subnets | Tasks need to pull images, call AWS APIs, send emails | Low |
| CloudWatch log groups per container | Without this, log debugging is blind | Low |
| ECR repository per service | Immutable image tags tied to git SHA; no "latest" in prod | Low |
| Health check endpoint on `/health` or `/healthz` | ALB needs a 200 response to consider a task healthy | Low |
| Task execution role with ECR pull + Secrets Manager read | ECS agent cannot start a task without these permissions | Medium |

### Services Required for This Stack

The Nexus CRM stack maps to three ECS services and one one-shot task:

```
nexus-api        → FastAPI, behind ALB, desired_count >= 2 in prod
nexus-worker     → Celery, NOT behind ALB, same image as api, command override
nexus-frontend   → Nginx serving compiled React build, behind ALB
nexus-migrate    → One-shot ECS task, runs alembic upgrade head, exits 0
```

The frontend can alternatively be served from S3 + CloudFront, which is simpler and cheaper for a static React build. For parity with the Docker Compose setup, nginx-in-ECS is valid but adds container lifecycle overhead. S3+CloudFront is the more idiomatic AWS pattern for React SPAs.

**Important (MEDIUM confidence from AWS re:Post 2025):** ElastiCache Serverless for Redis has documented compatibility issues with Celery 5.3+ as a broker. Use a provisioned ElastiCache Redis cluster (cache.t3.micro for staging, cache.r6g.large for prod), not Serverless. Source: AWS re:Post discussion confirmed in mid-2025.

### Architecture Constraint

All ECS tasks must use `platform linux/amd64`. If images are built on Apple Silicon (M1/M2/M3), build with:
```
docker buildx build --platform linux/amd64 -t ...
```
Fargate does not support ARM64 tasks in all regions. Build for amd64 regardless of local machine.

---

## Multi-Environment (Staging + Prod)

### How It Typically Works

The standard pattern (HIGH confidence, from HashiCorp's own guidance) is **separate Terraform directories per environment**, not Terraform workspaces. Workspaces share backend configuration and don't support per-environment credential isolation — HashiCorp explicitly states workspaces are not a suitable isolation mechanism for staging vs production.

```
terraform/
  modules/
    ecs-service/
    rds/
    elasticache/
    acm/
  environments/
    staging/
      main.tf        # calls modules, passes staging var values
      terraform.tfvars
      backend.tf     # separate S3 bucket + DynamoDB lock table
    prod/
      main.tf
      terraform.tfvars
      backend.tf
```

### Config Separation

| Parameter | Staging | Prod |
|-----------|---------|------|
| ECS desired count | 1 | 2+ |
| RDS instance class | db.t3.micro | db.t3.medium or larger |
| ElastiCache instance | cache.t3.micro | cache.r6g.large |
| Secrets Manager paths | `/nexus/staging/...` | `/nexus/prod/...` |
| ACM certificate domain | staging.crm.twgasia.com | crm.twgasia.com |
| ALB access logs | Optional | Required |
| Deletion protection (RDS) | Off | On |
| Multi-AZ RDS | Off | On |

### GitHub Actions Environment Targeting

Use GitHub Environments (`staging`, `production`) with branch rules:
- Pushes to `main` branch trigger deploy to `staging` automatically
- Deploy to `production` requires manual approval (GitHub environment protection rule)

Both environments share the same workflow file, parameterized by the `environment` input and environment-scoped secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` scoped per GitHub environment).

---

## Secrets Management

### ECS + Secrets Manager Integration Pattern (HIGH confidence)

ECS injects secrets at task start time. The task definition's `secrets` array references Secrets Manager ARNs. The container sees them as plain environment variables — no SDK calls needed in application code. FastAPI reads them via `os.environ["DATABASE_URL"]` as usual.

```json
"secrets": [
  {
    "name": "DATABASE_URL",
    "valueFrom": "arn:aws:secretsmanager:ap-southeast-1:ACCOUNT:secret:/nexus/prod/db-url-AbCdEf"
  },
  {
    "name": "SECRET_KEY",
    "valueFrom": "arn:aws:secretsmanager:ap-southeast-1:ACCOUNT:secret:/nexus/prod/app-secrets-XyZaB:secret_key::"
  }
]
```

Referencing a specific JSON key from a secret uses the suffix `:key_name::`. This allows one Secrets Manager object (e.g., `app-secrets`) to hold multiple values, each injected as a separate environment variable.

### IAM Permissions Required

The **task execution role** (not the task role) needs:
```json
{
  "Action": ["secretsmanager:GetSecretValue", "kms:Decrypt"],
  "Resource": "arn:aws:secretsmanager:*:*:secret:/nexus/prod/*"
}
```

Scope to the environment path prefix, not `*`. Staging tasks only read `/nexus/staging/*`.

### Critical Behavior

Secrets are fetched once at task startup. If a secret is rotated in Secrets Manager, running tasks do not see the new value. A forced ECS service redeployment is required to pick up rotated secrets. Secret rotation therefore requires a coordinated deploy — plan for this in operational runbooks.

### What Goes in Secrets Manager vs Environment Variables

| Value | Where |
|-------|-------|
| `DATABASE_URL` | Secrets Manager |
| `REDIS_URL` | Secrets Manager |
| `SECRET_KEY` (JWT signing) | Secrets Manager |
| `OPENAI_API_KEY` (AI scoring) | Secrets Manager |
| `APP_ENV` (staging/prod) | Task definition `environment` array (plaintext) |
| `LOG_LEVEL` | Task definition `environment` array (plaintext) |

---

## Zero-Downtime Deployments

### Rolling Update Strategy (HIGH confidence)

ECS rolling deployments replace tasks incrementally. The two governing parameters:

| Parameter | Recommended Value | Effect |
|-----------|-------------------|--------|
| `minimum_healthy_percent` | 100 | Never kill old tasks before new ones are healthy |
| `maximum_percent` | 200 | Allows launching new tasks while old ones still run |
| `health_check_grace_period_seconds` | 60 | Ignores ALB health checks for 60s after a task starts |

With `desired_count = 2`, `minimum_healthy_percent = 100`, `maximum_percent = 200`:
1. ECS launches 2 new tasks alongside the 2 existing ones (total = 4)
2. Waits for the 2 new tasks to pass ALB health checks
3. Drains and stops the 2 old tasks

This means sufficient ECS capacity must be available to momentarily run 2x the normal task count. With Fargate this is usually not a constraint since you are not managing EC2 instances.

### Health Check Configuration

Two independent checks must both pass for a task to be considered healthy:

**Container health check** (in task definition):
```json
"healthCheck": {
  "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
  "interval": 30,
  "timeout": 5,
  "retries": 3,
  "startPeriod": 60
}
```

**ALB target group health check:**
```
path:                 /health
healthy_threshold:    2
unhealthy_threshold:  3
interval:             30
timeout:              10
```

The FastAPI backend must expose `GET /health` returning HTTP 200 with a JSON body. The Celery worker does not register with the ALB; container health checks alone govern worker task health.

### Deployment Circuit Breaker

As of July 2025, ECS supports native blue/green deployments directly within ECS without requiring CodeDeploy. For this project, **rolling update with deployment circuit breaker** is the correct choice for its simplicity:

```hcl
deployment_circuit_breaker {
  enable   = true
  rollback = true
}
```

If the new task revision fails to become healthy within the deployment timeout, ECS automatically rolls back to the previous task definition revision. Failed deploys self-revert without operator intervention.

### ALB Connection Draining

When ECS deregisters a task from the ALB target group, the ALB drains in-flight requests before the container stops. The `deregistration_delay` defaults to 300 seconds but should be reduced for fast deployments:

```hcl
deregistration_delay = 30
```

This ensures a stopped task is removed cleanly from rotation within 30 seconds of being marked for replacement.

---

## Database Migrations in Pipeline

### Pattern: One-Shot ECS Task Before Service Update (MEDIUM confidence)

The established ECS pattern for Alembic migrations is a throwaway ECS task that runs `alembic upgrade head`, exits 0 on success, and exits non-zero on failure — halting the pipeline before any ECS service is updated.

```
CI/CD pipeline order:
  1. Build + push Docker images to ECR (git SHA as image tag)
  2. Run migration ECS task (same image as api, command override)
     → aws ecs run-task --task-definition nexus-migrate:LATEST
     → aws ecs wait tasks-stopped (poll until exit)
     → check exitCode == 0, fail pipeline if not
  3. If migration exits 0: update ECS services (api, worker, frontend)
  4. If migration exits non-0: pipeline fails, ECS services remain on old revision
```

The migration task uses the same Docker image as the API (Alembic migrations live in the same codebase) but overrides the container command:

```json
"command": ["alembic", "upgrade", "head"]
```

It runs in the same VPC and security group as RDS. It inherits `DATABASE_URL` from Secrets Manager. It is not part of any ECS Service — it is a one-shot `run-task` invocation from GitHub Actions.

### Dependency Chain

```
Migration task depends on:
  - RDS instance available and accepting connections
  - DATABASE_URL secret present in Secrets Manager
  - ECS task execution role has secretsmanager:GetSecretValue
  - Security group allows TCP 5432 from the task's subnet to RDS

ECS service update depends on:
  - Migration task exit code = 0
  - New ECR image available
  - Task definition updated with new image SHA
```

### Gotchas (MEDIUM-HIGH confidence from community sources)

| Gotcha | What Happens | Prevention |
|--------|-------------|------------|
| Adding a `NOT NULL` column to a table with existing rows | Migration fails or causes lock contention during migration | Add as nullable first, backfill data, then add NOT NULL constraint in a separate migration |
| Long-running migrations holding table locks | API requests time out during the migration window | Keep migrations additive; move destructive DDL (DROP COLUMN) to a separate deploy after all code references are removed |
| Migration task exit code not checked | Pipeline continues to deploy with wrong schema | Always `wait tasks-stopped` and check `containers[0].exitCode == 0` explicitly |
| Two pipeline runs executing migrations concurrently | Race condition on `alembic_version` table, one run will fail | Use GitHub Actions concurrency groups: `concurrency: group: deploy-${{ github.ref }}` |
| Autogenerate detects false positives | Alembic generates unnecessary migrations for sequences or unnamed constraints | Always review autogenerate output; never apply unreviewed migrations to prod |
| `alembic upgrade head` on a fresh database | Runs all migrations from scratch; correct behavior | No special handling needed |

### Backward Compatibility Window

Because the migration task runs before the new ECS service version starts, there is a window where the **new schema is live but the old application code is still running** (ECS is replacing tasks one by one during the rolling update). Migrations must be backward compatible with the N-1 application version:

- Never drop a column that the current (running) application reads
- Never rename a column without an aliasing step
- New columns: always add as `nullable` or with a `server_default`
- Dropping old columns: deferred to a separate deploy after all references are removed from code

---

## Azure Warm Failover

### What "Warm" Means Operationally

"Warm" means the Azure environment is **pre-deployed and idle** — containers are running (or can be started in under a minute), the database is up to date, but no public DNS points to it and it is not serving traffic. This is distinct from:

| Tier | Definition | Time to Take Traffic |
|------|-----------|----------------------|
| Cold | Nothing deployed; must Terraform apply first | 20-45 minutes |
| Warm | Deployed and idle; DNS cutover is the only operator action | 5-15 minutes (DNS TTL drain) |
| Hot | Active-active; traffic already going to both clouds | Near-instant, but requires write conflict resolution |

Warm is the correct tier for this project. Hot active-active requires write conflict resolution and session synchronization that is not justified for a PE CRM with a small user base.

### Architecture of the Warm Standby

```
AWS (primary, live traffic):
  Route 53: crm.twgasia.com → AWS ALB
  ALB → ECS Fargate (nexus-api, nexus-frontend, nexus-worker)
  RDS PostgreSQL (primary, read-write)
  ElastiCache Redis

Azure (warm standby, no public traffic):
  Azure Application Gateway or ACI public IP (pre-configured, no DNS pointing here yet)
  ACI containers: nexus-api, nexus-frontend, nexus-worker (running or startable in < 1 min)
  Azure Database for PostgreSQL Flexible Server (receiving data sync from RDS)
  Azure Cache for Redis (pre-provisioned, minimal tier)
```

### PostgreSQL Sync: RDS to Azure

Native RDS physical replication cannot cross cloud boundaries. Two viable options:

**Option A: Logical replication (PostgreSQL native)**
- RDS primary publishes via a logical replication slot (`rds.logical_replication = 1`)
- Azure PostgreSQL Flexible Server subscribes to it over a TLS connection
- WAL changes stream continuously; typical lag is seconds to minutes at low write volume
- Requires a network path between AWS and Azure (VPN or NAT-accessible public endpoint on RDS)
- If the slot falls behind or is dropped (e.g., RDS restart), full re-sync required

**Option B: Periodic dump + restore (pgdump/psql)**
- A scheduled Lambda or GitHub Actions cron job runs `pg_dump` on RDS and restores to Azure
- RPO = time since last successful restore (e.g., 4 hours on a 4-hour schedule)
- No persistent replication slot to manage; simpler operationally
- Acceptable for a warm DR scenario where the priority is application availability over zero-RPO

**Recommendation:** Start with Option B (pgdump + restore every 4 hours). Logical replication across clouds requires maintaining a stable network path and monitoring replication slot health — if the slot lags (e.g., due to low RDS WAL retention), replication silently falls behind. For a PE CRM with low write volume, 4-hour RPO is acceptable. Upgrade to Option A if RPO requirements tighten.

### Container Images: ECR to ACR

The same images pushed to ECR must also be pushed to Azure Container Registry (ACR) in the same GitHub Actions workflow:

```yaml
# On push to main: push to both registries
- aws ecr: push nexus-api:$SHA, nexus-frontend:$SHA, nexus-worker:$SHA
- az acr: push nexus-api:$SHA, nexus-frontend:$SHA, nexus-worker:$SHA
```

ACI container definitions reference the ACR images. They should be pre-deployed (Terraform-managed) and running idle. Running idle ACI containers at minimum CPU/memory allocation costs approximately $15-40/month — acceptable for warm standby.

### What the Azure Side Actually Runs

ACI containers run with environment variables pointing to Azure resources:

```
DATABASE_URL    → Azure PostgreSQL Flexible Server connection string
REDIS_URL       → Azure Cache for Redis endpoint
SECRET_KEY      → Same value as AWS (mirrored to Azure Key Vault)
APP_ENV         → production
```

The Celery worker runs idle in Azure, connected to the Azure Redis broker. With no traffic, it processes no tasks. On failover, it will immediately begin processing tasks queued by the API.

---

## Manual Failover Runbook

### Decision Trigger

Initiate failover when:
- AWS region or specific services (RDS, ECS, ALB) are experiencing an outage
- Estimated recovery time exceeds the team's acceptable downtime threshold (suggested: > 30 minutes)
- Decision made by on-call person; confirm with at least one other team member before proceeding

### Step 1: Assess Replication Lag (< 5 minutes)

- If using logical replication: connect to Azure PostgreSQL and run:
  ```sql
  SELECT * FROM pg_stat_subscription;
  ```
  Check `received_lsn` vs `latest_end_lsn`. A lag of 0 bytes means fully caught up.
- If using pgdump schedule: check timestamp of the most recent restore log. Document estimated data loss window.
- If RDS is completely unavailable: note that no further sync is possible; accept the data loss from the last successful sync.

### Step 2: Stop Writes to AWS (< 5 minutes)

Scale the AWS ECS `nexus-api` service to `desired_count = 0`:
```bash
aws ecs update-service \
  --cluster nexus-prod \
  --service nexus-api \
  --desired-count 0
```
This prevents split-brain writes. Active users will see connection failures during DNS propagation.

### Step 3: Final Data Sync (5-20 minutes)

- Logical replication path: wait for lag to reach 0 bytes, then stop the subscription on Azure: `DROP SUBSCRIPTION nexus_sub;`
- pgdump path: run one final manual dump/restore if RDS is accessible
- If RDS is unreachable: skip this step; accept the data loss window from Step 1

### Step 4: Promote Azure PostgreSQL to Writable (< 2 minutes)

If logical replication was running, the `DROP SUBSCRIPTION` in Step 3 severs the link and makes Azure the standalone primary. If periodic dump was used, Azure is already standalone.

Reset sequences to values safely above RDS last known values (prevents PK conflicts if both ever come online):
```sql
-- Repeat for every table with a serial/identity column
SELECT setval('contacts_id_seq', (SELECT MAX(id) FROM contacts) + 100000);
SELECT setval('companies_id_seq', (SELECT MAX(id) FROM companies) + 100000);
-- etc.
```

### Step 5: Verify Azure Stack Health (< 5 minutes)

- Confirm ACI containers are running:
  ```bash
  az container show --resource-group nexus-failover --name nexus-api --query instanceView.state
  ```
- Smoke-test against the Azure internal URL (before DNS change):
  ```bash
  curl -f https://<azure-aci-fqdn>/health
  ```
- Check Celery worker logs for Redis connection confirmation

### Step 6: DNS Cutover (TTL-dependent: 5-10 minutes)

Update the DNS record for `crm.twgasia.com` to point to the Azure ACI public IP or Azure Application Gateway IP.

**Pre-condition:** The DNS TTL for `crm.twgasia.com` should be 60-300 seconds. If it is currently set to 3600 seconds or higher, reduce it at the start of the outage and wait one TTL period before cutting over. Set the TTL permanently to 300 seconds as a standing operational practice.

In Route 53:
```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id ZONE_ID \
  --change-batch '{"Changes": [{"Action": "UPSERT", "ResourceRecordSet": {"Name": "crm.twgasia.com", "Type": "A", "TTL": 60, "ResourceRecords": [{"Value": "<azure-ip>"}]}}]}'
```

Confirm propagation:
```bash
dig crm.twgasia.com +short  # repeat until Azure IP is returned
```

### Step 7: Verify End-to-End (< 10 minutes)

- Log in via the production URL (`crm.twgasia.com`)
- Verify data is present up to the estimated cutover point
- Verify a write completes: create a test contact
- Verify Celery tasks process: trigger an AI scoring task, confirm it completes within expected time
- Notify team that failover is complete; log the cutover time and data loss window

### Step 8: Post-Failover Housekeeping

- Disable or destroy the AWS ECS services to prevent accidental restart writing to stale RDS
- Monitor Azure infrastructure costs (ACI + Flexible Server now running at full load)
- Document a post-mortem: root cause, timeline, data loss window, lessons learned
- Plan a failback window (minimum 2-hour maintenance window; not covered in this runbook)

---

## Feature Dependencies

```
ACM Certificate
  └─ required by: ALB HTTPS listener (must exist before listener can be created)

ALB HTTPS listener
  └─ required by: ECS API service (receives public traffic)
  └─ required by: ECS Frontend service (receives public traffic)

ECS task definition (nexus-api image)
  └─ required by: ECS API service
  └─ required by: Migration task (same image, command override)
  └─ required by: ECS Worker service (same image, celery command)
  └─ requires: ECR image (must be pushed before task def registered)
  └─ requires: Secrets Manager secrets (DATABASE_URL, SECRET_KEY, REDIS_URL)

Secrets Manager secrets
  └─ required by: all ECS task definitions
  └─ required by: Azure ACI containers (mirrored to Azure Key Vault)

RDS PostgreSQL
  └─ required by: Migration task (must run BEFORE api service starts)
  └─ required by: ECS API service
  └─ required by: Azure warm standby (replication or dump source)

Migration task (one-shot)
  └─ must complete with exit 0 BEFORE ECS service update
  └─ requires: RDS reachable
  └─ requires: DATABASE_URL secret present

ElastiCache Redis
  └─ required by: ECS Worker service (Celery broker)
  └─ required by: ECS API service (caching, session state)

Azure ACI + Azure PostgreSQL
  └─ required by: Manual failover runbook
  └─ requires: Docker images pushed to ACR (same pipeline as ECR push)
  └─ requires: Azure Key Vault secrets mirrored from Secrets Manager
```

---

## Anti-Features

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Automated DNS failover to Azure (Route 53 health checks auto-cutting over) | Cross-cloud health checks cause false positives; automated failover to another cloud without human judgment is high risk | Manual runbook only; use Route 53 health checks for alerting via CloudWatch alarm |
| `alembic upgrade head` in the application container entrypoint (`CMD alembic upgrade head && uvicorn ...`) | If multiple tasks start simultaneously they race on `alembic_version`; a migration failure kills the app container before it serves any traffic | Separate one-shot migration task in pipeline, runs once, exits before service update |
| Terraform workspaces for staging vs prod isolation | Workspaces share backend credentials; HashiCorp explicitly discourages this pattern for environment isolation | Separate Terraform directories per environment with separate S3 backends |
| ElastiCache Serverless as Celery broker | Documented compatibility issues with Celery 5.3+ as of 2025 | Provisioned ElastiCache Redis cluster |
| Deploying app code when a migration fails | App code expects new schema that does not exist yet | Strict pipeline ordering: migration exit 0 required before service update |
| Active-active cross-cloud (Azure also accepts writes) | Write conflict resolution and sequence management are complex; not needed for this scale | Warm standby only; Azure is read-only until manual promotion during failover |
| Using `latest` image tag in ECS task definitions | Can't tell which version is running; rollback is ambiguous | Use git SHA as image tag; every deploy creates a unique tag |

---

## Sources

- [Deploy Amazon ECS services — rolling update type](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html) — HIGH confidence
- [Amazon ECS improves service availability during rolling deployments (Nov 2025)](https://aws.amazon.com/about-aws/whats-new/2025/11/amazon-ecs-service-availability-rolling-deployments/) — HIGH confidence
- [Choosing between ECS Blue/Green Native or CodeDeploy (July 2025 launch)](https://aws.amazon.com/blogs/devops/choosing-between-amazon-ecs-blue-green-native-or-aws-codedeploy-in-aws-cdk/) — HIGH confidence
- [Pass Secrets from Secrets Manager to ECS Tasks](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html) — HIGH confidence
- [RDS DB Migrations Using ECS and Fargate (AWS re:Post)](https://repost.aws/questions/QUGsow-U-jSUyNcTcHOCst6g/rds-db-migrations-using-ecs-and-fargate) — MEDIUM confidence
- [Alembic Migrations Without Downtime (Exness Tech Blog)](https://medium.com/exness-blog/alembic-migrations-without-downtime-a3507d5da24d) — MEDIUM confidence
- [GitHub Actions ECS Deploy Task Definition Action](https://github.com/aws-actions/amazon-ecs-deploy-task-definition) — HIGH confidence
- [How to Manage Multiple Terraform Environments (Spacelift)](https://spacelift.io/blog/terraform-environments) — MEDIUM confidence
- [HashiCorp on Terraform workspaces for environments (Gruntwork)](https://www.gruntwork.io/blog/how-to-manage-multiple-environments-with-terraform-using-workspaces) — HIGH confidence
- [Azure PostgreSQL Flexible Server — Logical Replication](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-logical) — MEDIUM confidence
- [RDS PostgreSQL Cross-Region Read Replicas Best Practices (AWS Blog)](https://aws.amazon.com/blogs/database/best-practices-for-amazon-rds-for-postgresql-cross-region-read-replicas/) — MEDIUM confidence
- [ElastiCache Serverless + Celery compatibility (AWS re:Post, 2025)](https://repost.aws/questions/QUixEOtU-gS9eOWV68QyJVnw/does-aws-elasticache-redis-serverless-support-celery-as-a-redis-broker-workers-connect-but-never-consume-tasks) — MEDIUM confidence
- [ACM Certificate Terraform DNS Validation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate_validation) — HIGH confidence
- [Azure Container Instances Standby Pools](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-standby-pool-overview) — MEDIUM confidence
