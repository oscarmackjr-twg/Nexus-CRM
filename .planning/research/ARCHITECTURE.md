# Architecture Research: Cloud Deployment

**Project:** Nexus CRM v1.2 — AWS Primary + Azure Warm Failover
**Researched:** 2026-03-29
**Overall confidence:** HIGH (existing Terraform modules read directly; AWS/Azure patterns verified against official docs and current sources)

---

## System Diagram (text)

### AWS Primary (normal operations)

```
Internet
   |
   v
Route 53 (crm.example.com)
   |
   v
CloudFront Distribution
   |
   +--[/api/*]--> ALB (public subnets, 2 AZs) ---> ECS Fargate: api service
   |                                                   (private subnets, port 8000)
   |                                                        |
   +--[/*]---> S3: frontend bucket (static Vite build)      +---> RDS PostgreSQL
                                                            |     (private subnets, Multi-AZ prod)
                                                            |
ECS Fargate: worker service (private subnets)              +---> ElastiCache Redis
   (Celery, queues: default,linkedin,ai)                         (private subnets)
   |
   +---> RDS PostgreSQL
   +---> ElastiCache Redis

GitHub Actions (CI/CD)
   |
   +--[OIDC]--> ECR (nexus-crm-{env}-api, nexus-crm-{env}-worker)
   |
   +--[1]--> run migration task (ECS one-off: alembic upgrade head)
   +--[2]--> update ECS service: api (rolling deploy)
   +--[3]--> update ECS service: worker (rolling deploy)
   +--[4]--> s3 sync: frontend/dist --> S3 frontend bucket
   +--[5]--> CloudFront invalidation

AWS Secrets Manager
   /nexus-crm/{env}/DATABASE_URL
   /nexus-crm/{env}/SECRET_KEY
   /nexus-crm/{env}/REDIS_URL
   /nexus-crm/{env}/LINKEDIN_CLIENT_ID
   /nexus-crm/{env}/LINKEDIN_CLIENT_SECRET
   /nexus-crm/{env}/OPENCLAW_API_KEY
   /nexus-crm/{env}/SENDGRID_API_KEY
   (injected into ECS tasks at startup via execution role; never in task def plaintext)
```

### Azure Warm Failover (idle, no live traffic)

```
Azure Resource Group: nexus-crm-failover
   |
   +---> Azure Database for PostgreSQL (Flexible Server)
   |        Logical replication subscriber from RDS primary
   |        pglogical extension; receives WAL stream continuously
   |        READ-ONLY until manual cutover
   |
   +---> Azure Container Instances (ACI) — api + worker
            Pre-deployed, stopped (deallocated)
            Image: mirrored from ECR to Azure Container Registry
            Env vars: Azure Key Vault references
            NOT receiving traffic until cutover

Manual Cutover (operator action):
   1. Promote Azure PostgreSQL from replica to standalone (break replication)
   2. Start ACI container groups (api + worker)
   3. Update DNS: Route 53 / external DNS A record points to Azure ACI IP or Azure Application Gateway
   4. Monitor Azure logs
```

---

## New Components

| Component | AWS/Azure Service | Integrates With | Notes |
|-----------|------------------|-----------------|-------|
| VPC | AWS VPC | All AWS resources | 10.0.0.0/16, 2 public subnets (ALB), 2 private subnets (ECS/RDS/Redis), 2 NAT gateways |
| Application Load Balancer | AWS ALB | CloudFront (origin), ECS api | HTTPS listener (port 443) with ACM cert; HTTP → HTTPS redirect; target type = ip (awsvpc mode) |
| CloudFront Distribution | AWS CloudFront | S3 frontend bucket, ALB | Default behavior: S3 (static). /api/* behavior: ALB (cache disabled). SPA error 403/404 → index.html |
| ECS Cluster | AWS ECS Fargate | VPC private subnets | Regional; api service + worker service share cluster |
| API Task Definition | AWS ECS Fargate | ALB target group, Secrets Manager | Family: nexus-crm-{env}-api; port 8000; health check: GET /health; execution role pulls secrets |
| Worker Task Definition | AWS ECS Fargate | Redis, RDS, Secrets Manager | Family: nexus-crm-{env}-worker; no ALB; Celery queues: default,linkedin,ai |
| Migration Task Definition | AWS ECS Fargate | RDS | One-off, same image as API; override command: alembic upgrade head; runs before service updates |
| ECR Repositories | AWS ECR | GitHub Actions, ECS | nexus-crm-{env}-api, nexus-crm-{env}-worker; scan on push enabled |
| RDS PostgreSQL 15 | AWS RDS | ECS api + worker tasks | Private subnet group; Multi-AZ in prod; backup retention 7d; logical replication enabled for Azure replica |
| ElastiCache Redis | AWS ElastiCache | ECS api + worker tasks | Private subnet group; Celery broker + result backend |
| AWS Secrets Manager | AWS Secrets Manager | ECS execution role | 7-secret set per environment under /nexus-crm/{env}/ prefix |
| S3 Assets Bucket | AWS S3 | ECS task role | User-uploaded files; server-side encryption AES256; versioning enabled |
| S3 Frontend Bucket | AWS S3 | CloudFront OAC | Vite build output; no public access; bucket policy allows CloudFront OAC only |
| ACM Certificate | AWS ACM | ALB listener, CloudFront | Wildcard or exact domain; must be in us-east-1 for CloudFront; ALB cert in deployment region |
| Route 53 | AWS Route 53 | CloudFront, ACM validation | A/AAAA alias to CloudFront; CNAME for ACM DNS validation |
| IAM OIDC Provider | AWS IAM | GitHub Actions | Trusts token.actions.githubusercontent.com; no long-lived AWS credentials stored in GitHub |
| GitHub Actions Role | AWS IAM | ECR, ECS, S3, CloudFront | Scoped to main branch of the repo; can push to ECR, register task defs, update ECS services |
| Azure PostgreSQL Flexible Server | Azure | RDS (replication source) | pglogical subscriber; wal_level=logical on RDS; shared_preload_libraries=pglogical on both ends |
| Azure Container Instances | Azure | Azure Key Vault, Azure PostgreSQL | Container groups for api + worker; stopped until cutover; images from Azure Container Registry |
| Azure Container Registry | Azure | ACI, GitHub Actions (secondary push) | Mirror of ECR images pushed on each deploy |
| Azure Key Vault | Azure | ACI container definitions | Mirrors of Secrets Manager secrets; provides env vars to ACI at startup |

---

## Modified Components

These are existing app components that require changes for cloud operation. The app code itself is Docker-agnostic (reads env vars), so most changes are operational rather than code changes.

### 1. entrypoint.sh — Migration Separation (CRITICAL)

**Current behavior:** `entrypoint.sh` runs `alembic upgrade head` then starts uvicorn in the same container startup.

**Problem:** In ECS rolling deployments, multiple api task instances start in parallel. All of them run `alembic upgrade head` simultaneously. This causes concurrent migration races and can corrupt migration state.

**Required change:** The deploy pipeline must run migrations as a separate one-off ECS task before any service update. The entrypoint should detect whether it is running as a migration task (e.g., via `MIGRATION_ONLY=true` env var) and exit after migration, OR the migration step should override the container command entirely (`["alembic", "upgrade", "head"]`) in the one-off task definition rather than using the default entrypoint.

**Simplest approach:** Create a separate `migration` task definition (same image as api) that overrides the command with `["sh", "-c", "alembic upgrade head"]` and does not start uvicorn. The `entrypoint.sh` in the api service task can keep or remove the `alembic upgrade head` call — removing it is cleaner and prevents the race condition.

### 2. FastAPI app — /health endpoint (ALREADY PRESENT, verify)

The ECS task definition and ALB target group both depend on `GET /health` returning HTTP 200. Confirm this endpoint exists in `backend/api/main.py`. The ALB health check is configured with path `/health`, matcher `200`, interval 30s, timeout 5s, thresholds 2 healthy / 3 unhealthy.

### 3. Backend config — STORAGE_TYPE env var

**Current:** Docker Compose runs with local filesystem or unset storage.

**Cloud:** ECS tasks receive `STORAGE_TYPE=s3` and `S3_BUCKET_NAME={assets-bucket}` as plain environment variables (not secrets). The `backend/config.py` and `backend/storage/` module must handle `STORAGE_TYPE=s3` branching. This is already handled in the existing ECS task definitions (`container_environment` local in modules/ecs/main.tf and modules/ecs_worker/main.tf).

### 4. DATABASE_URL format — async vs sync driver

**Current:** `entrypoint.sh` already handles this: if `DATABASE_URL` uses `postgresql+asyncpg://` it derives `DATABASE_URL_SYNC` with `postgresql+psycopg://` for Alembic. This pattern must be preserved when the Alembic migration runs as a one-off ECS task — it needs `DATABASE_URL_SYNC` or the same derivation logic in its entrypoint.

### 5. RDS parameter group — logical replication for Azure replica

**Required RDS parameter group changes** (applied via Terraform, triggers instance restart):
- `rds.logical_replication = 1`
- `max_wal_senders = 10`
- `max_replication_slots = 10`
- `shared_preload_libraries = pglogical` (add to existing value)

This is a **modification to the existing RDS module** — add an `aws_db_parameter_group` resource with these parameters, and reference it in `aws_db_instance.this`. Without this, the Azure PostgreSQL replica cannot subscribe via pglogical.

### 6. GitHub Actions workflow — new file needed

A `.github/workflows/deploy.yml` does not yet exist. It must be created. Key steps (see Build Order section for sequencing):
- Trigger: push to `main`
- Auth: `aws-actions/configure-aws-credentials` with OIDC (role ARN from Terraform output `github_actions_role_arn`)
- Build: `docker build` api image, tag with `git sha` and `latest`
- Push: `aws-actions/amazon-ecr-login` + `docker push` to ECR
- Migrate: run one-off ECS task with `alembic upgrade head` command; wait for it to stop successfully
- Deploy api: `aws-actions/amazon-ecs-deploy-task-definition` (renders new image URI into task def, updates service, waits for stability)
- Deploy worker: same pattern for worker service
- Deploy frontend: `npm run build`, `aws s3 sync`, `aws cloudfront create-invalidation`

---

## Terraform Structure

### Current State (what exists)

The existing Terraform lives in `/terraform/` as a **single root module** with environment distinguished by `var.environment` and separate `terraform.tfvars` files. This is a functional approach for a two-environment setup.

```
terraform/
  main.tf                   # root: providers, ECR, S3 assets, module calls
  variables.tf
  outputs.tf
  terraform.tfvars          # currently staging values
  modules/
    networking/             # VPC, subnets, NAT, security groups
    alb/                    # ALB, target group, listeners
    cloudfront/             # CloudFront dist, S3 frontend bucket, OAC
    ecs/                    # ECS cluster, api task def, api service, autoscaling
    ecs_worker/             # worker task def, worker service
    elasticache/            # Redis subnet group, cluster
    iam/                    # execution role, task role, GitHub OIDC role
    rds/                    # RDS instance, subnet group, parameter group
    secrets/                # Secrets Manager secrets
```

### Recommended Structure for Multi-Environment + Azure

Add two new directories and a dedicated Azure module alongside the existing modules:

```
terraform/
  modules/
    networking/             # (existing)
    alb/                    # (existing)
    cloudfront/             # (existing)
    ecs/                    # (existing)
    ecs_worker/             # (existing)
    elasticache/            # (existing)
    iam/                    # (existing)
    rds/                    # (existing) — add parameter group for pglogical
    secrets/                # (existing)
    azure_failover/         # NEW: Azure PostgreSQL + ACI + ACR + Key Vault
      main.tf
      variables.tf
      outputs.tf
  environments/
    staging/
      main.tf               # calls all modules with staging vars
      variables.tf
      terraform.tfvars      # staging-specific (non-secret) values
      backend.tfvars        # bucket=..., key=staging/terraform.tfstate, region=...
    prod/
      main.tf               # calls all modules with prod vars
      variables.tf
      terraform.tfvars      # prod-specific (non-secret) values
      backend.tfvars        # bucket=..., key=prod/terraform.tfstate, region=...
```

**Why environments/ directories instead of workspaces:**

Workspaces share one root module and use `terraform.workspace` to branch variable values. This creates a single `terraform plan` blast radius — a mistake in staging vars can plan against prod state. Separate environment directories are the AWS Prescriptive Guidance recommendation: each has its own state file path, its own `backend.tfvars`, and its own variable overrides. Teams can restrict prod backend access to CI only.

**State Backend Strategy:**

- **AWS state:** S3 bucket (`nexus-crm-terraform-state`) + native S3 locking (`use_lockfile = true` — DynamoDB locking is deprecated in Terraform's S3 backend). Separate keys per environment: `staging/terraform.tfstate`, `prod/terraform.tfstate`.
- **Azure state:** Can share the same S3 bucket with a different key path (`azure-failover/terraform.tfstate`), OR use a separate Azure Storage Account backend. Sharing the S3 bucket is simpler to bootstrap because the S3 bucket is already managed by the AWS deploy pipeline.
- **Bootstrap order:** S3 state bucket and DynamoDB table (if you keep it for legacy reasons) must exist before `terraform init`. Create them manually once, or with a separate `bootstrap/` Terraform root that uses local state.

**Backend initialization:**

```bash
# staging
cd terraform/environments/staging
terraform init -backend-config=backend.tfvars

# prod
cd terraform/environments/prod
terraform init -backend-config=backend.tfvars
```

**Variable file pattern:**

```
# terraform.tfvars (non-sensitive, committed)
app_name        = "nexus-crm"
environment     = "staging"
aws_region      = "us-east-1"
db_instance_class = "db.t3.micro"
api_cpu         = 512
...

# Sensitive vars passed via CI environment or -var flag — never committed:
secret_key, linkedin_client_secret, openclaw_api_key, sendgrid_api_key
```

**azure_failover module inputs:**

```
azure_region          = "eastasia"            # co-located with AWS us-east-1 is acceptable; choose by data residency requirement
rds_endpoint          = module.rds.endpoint   # replication source
rds_replication_slot  = "azure_replica"
db_admin_password     = var.azure_db_password
acr_name              = "${local.name_prefix}-acr"
api_image_uri         = "${module.ecs.api_image_uri}"  # or ECR URI for cross-registry push
```

---

## Data Flow: Normal Operations

### HTTPS Request (browser to API)

```
1. Browser: GET https://crm.example.com/api/v1/deals
2. Route 53: resolves crm.example.com → CloudFront distribution CNAME
3. CloudFront: matches /api/* behavior → origin: ALB (caching disabled, AllViewer request policy)
4. ALB: HTTPS listener (port 443, ACM cert) → HTTP forward to target group (port 8000, target type ip)
5. ALB health check: confirmed healthy ECS task IPs in target group
6. ECS Fargate api task: receives request on port 8000 → uvicorn → FastAPI router
7. FastAPI: reads DATABASE_URL from env (injected by Secrets Manager at task startup)
8. FastAPI → asyncpg → RDS PostgreSQL (private subnet, port 5432)
9. Response flows back: RDS → FastAPI → uvicorn → ALB → CloudFront → browser
```

### HTTPS Request (browser to frontend)

```
1. Browser: GET https://crm.example.com/
2. CloudFront: matches default behavior → origin: S3 frontend bucket (via OAC)
3. S3: returns index.html (or hashed static asset)
4. React app: hydrates, makes /api/* calls (same CloudFront domain, cached /api/* behavior)
```

### Celery Task Dispatch

```
1. FastAPI handler: enqueues task → Redis broker (ElastiCache, private subnet, port 6379)
   DATABASE_URL / REDIS_URL injected by Secrets Manager at task startup
2. Celery worker ECS task: polls Redis → receives task → executes (e.g., AI deal scoring, LinkedIn import)
3. Worker → RDS (read/write) + Redis (result backend)
4. Worker → S3 assets bucket (if storing files, via task role s3:PutObject)
```

### Secret Injection Flow

```
ECS task startup (execution role):
1. ECS agent: reads task definition container_definitions.secrets[]
   Each entry: { name: "DATABASE_URL", valueFrom: "arn:aws:secretsmanager:..." }
2. Execution role: secretsmanager:GetSecretValue on /nexus-crm/{env}/* ARN pattern
3. ECS agent: fetches secret string, injects as env var into container process
4. Container: reads os.environ["DATABASE_URL"] — no awareness of Secrets Manager
```

### GitHub Actions Deploy Flow

```
Push to main branch:
1. GitHub Actions: requests OIDC token from token.actions.githubusercontent.com
2. aws-actions/configure-aws-credentials: exchanges OIDC token for temporary AWS credentials
   (AssumeRoleWithWebIdentity → github-actions-role, constrained to repo + main branch)
3. docker build api image → tag with ${GITHUB_SHA:0:7} and "latest"
4. aws ecr get-login-password | docker login → ECR
5. docker push → ECR nexus-crm-{env}-api repo
6. docker build worker image → push → ECR nexus-crm-{env}-worker repo
7. Run one-off ECS migration task:
   - Register task definition (api image, command override: ["sh", "-c", "alembic upgrade head"])
   - ecs run-task --launch-type FARGATE --wait-for-task-stopped
   - Check exit code — fail pipeline if non-zero
8. Render api task definition with new image URI (amazon-ecs-render-task-definition)
9. Deploy api service (amazon-ecs-deploy-task-definition, wait-for-service-stability: true)
10. Render worker task definition with new image URI
11. Deploy worker service (wait-for-service-stability: true)
12. npm run build (frontend)
13. aws s3 sync frontend/dist s3://{frontend-bucket} --delete
14. aws cloudfront create-invalidation --paths "/*"
```

---

## Data Flow: Failover

### What Changes During Cutover

Failover is **manual** — it is a deliberate operator action, not automatic. Azure is in warm standby: containers are pre-deployed (stopped/deallocated), database is a live read-only replica. RTO is estimated 15-30 minutes.

### Pre-cutover State (warm standby running)

```
RDS primary (us-east-1, port 5432)
   |
   +--[pglogical logical replication]-->  Azure PostgreSQL Flexible Server (eastasia)
                                          - wal_level=logical on RDS
                                          - pglogical subscriber on Azure
                                          - receives WAL continuously, ~seconds behind
                                          - READ-ONLY (replica mode)

Azure Container Instances (ACI):
   - Container groups defined, images current (mirrored from ECR on each deploy)
   - Status: STOPPED (zero cost for compute)
   - Key Vault: populated with failover env vars pointing to Azure PostgreSQL endpoint
```

### Cutover Procedure (step by step)

```
Step 1 — Stop writes to AWS
   a. Update ECS api service desired_count = 0 (stops new requests)
      OR set Route 53 health check failure to stop routing to ALB
   b. Wait for in-flight requests to drain (ALB connection draining, ~30s)

Step 2 — Promote Azure PostgreSQL
   a. Break pglogical subscription on Azure: SELECT pglogical.drop_subscription('aws_primary')
   b. Confirm replication lag is near-zero before stopping (check pg_stat_replication on RDS)
   c. Azure PostgreSQL becomes a standalone writable instance

Step 3 — Start ACI containers
   a. az container start --resource-group nexus-crm-failover --name nexus-crm-api
   b. az container start --resource-group nexus-crm-failover --name nexus-crm-worker
   c. Wait for health checks to pass (ACI → Azure PostgreSQL connection verified)

Step 4 — Cut DNS
   a. Route 53: update A record (or CNAME) for crm.example.com
      FROM: CloudFront distribution (→ ALB → ECS)
      TO:   Azure ACI public IP or Azure Application Gateway IP
   b. Set low TTL (60s) before cutover to minimize caching impact
   c. DNS propagation: 1-5 minutes globally given low TTL

Step 5 — Verify
   a. Smoke test: GET https://crm.example.com/health → 200
   b. Test authenticated API call
   c. Monitor Azure Container Instances logs

Step 6 (post-incident) — Fail back to AWS
   a. Restore RDS primary (if failed) or confirm it is still running
   b. Re-establish replication (Azure → RDS or fresh pg_dump/restore)
   c. Drain ACI, cut DNS back to CloudFront
```

### What Does NOT Change During Failover

- The application code — same Docker images (mirrored to ACR)
- The secret values — Azure Key Vault mirrors Secrets Manager contents
- The database schema — Azure replica is schema-identical via logical replication
- The frontend — S3/CloudFront static assets are independent; optionally mirror to Azure Blob + Azure CDN, or keep on AWS CloudFront (frontend calls will still work if API DNS is updated)

### Failover Data Flow

```
Browser: GET https://crm.example.com/api/v1/deals
DNS: crm.example.com → Azure ACI public IP (or Azure Application Gateway)
ACI api container: uvicorn → FastAPI
FastAPI → psycopg (sync) / asyncpg (async) → Azure PostgreSQL Flexible Server (standalone, writable)
Response: ACI → browser
```

---

## Recommended Build Order

Each phase has a dependency that must be satisfied before the next can proceed. Networking must exist before compute references subnet IDs. Compute must exist before the CI/CD pipeline can reference cluster names and service names. Azure failover is last because it depends on a live RDS instance as replication source.

### Phase 1 — State Backend Bootstrap (prerequisite, one-time manual)

**What:** Create the S3 bucket and enable S3 native locking that will hold Terraform state.

**Why first:** Terraform cannot `init` with an S3 backend until that bucket exists. This is a chicken-and-egg problem. The bucket is created manually (AWS console or CLI) once, then all subsequent Terraform operations use it.

**Tasks:**
- Create S3 bucket `nexus-crm-terraform-state` with versioning enabled, SSE-AES256, block public access
- Enable `use_lockfile = true` in backend config (replaces DynamoDB)
- Create `environments/staging/backend.tfvars` and `environments/prod/backend.tfvars` with distinct key paths
- Run `terraform init -backend-config=backend.tfvars` in each environment directory

**Dependencies:** None (manual AWS console or CLI)

---

### Phase 2 — AWS Core Infrastructure (networking, data, secrets)

**What:** VPC, subnets, NAT gateways, security groups, RDS, ElastiCache, Secrets Manager, IAM roles, ECR repositories.

**Why second:** ECS and ALB depend on subnet IDs and security group IDs from networking. ECS depends on secrets ARNs. GitHub Actions depends on IAM role ARN. All compute depends on data stores existing first.

**Terraform apply order** (modules have implicit dependency via references, but conceptual order):
1. `module.networking` — VPC, subnets, security groups, NAT
2. `module.rds` — uses `private_subnet_ids`, `rds_security_group_id`
3. `module.elasticache` — uses `private_subnet_ids`, `redis_security_group_id`
4. `module.secrets` — uses database_url (RDS endpoint output), redis_url (ElastiCache endpoint output)
5. `module.iam` + ECR repositories — independent of data stores; uses `assets_bucket_arn`

**Key output values needed by later phases:**
- `module.networking.vpc_id`
- `module.networking.private_subnet_ids`
- `module.networking.public_subnet_ids`
- `module.networking.*_security_group_id` (api, worker, rds, redis, alb)
- `module.rds.endpoint` (needed for DATABASE_URL secret and Azure replication)
- `module.elasticache.endpoint`
- `module.secrets.secret_arns` (map passed to ECS task definitions)
- `module.iam.execution_role_arn`, `module.iam.task_role_arn`, `module.iam.github_actions_role_arn`
- `aws_ecr_repository.api.repository_url`, `aws_ecr_repository.worker.repository_url`

**RDS parameter group addition (required for Azure replica, do it now):**
Add `aws_db_parameter_group` with `rds.logical_replication=1`, `max_wal_senders=10`, `max_replication_slots=10`, `shared_preload_libraries=pglogical`. Apply requires RDS restart — acceptable at initial provisioning, disruptive in production later.

---

### Phase 3 — AWS Compute and CDN (ALB, ECS, CloudFront)

**What:** ALB, target groups, listeners, ECS cluster, api service, worker service, CloudFront distribution, S3 frontend bucket.

**Why third:** Depends on Phase 2 outputs (subnet IDs, security groups, secrets ARNs, ECR URIs).

**Note on first deploy:** At initial `terraform apply`, `ecr_api_image_uri` and `ecr_worker_image_uri` are empty in `terraform.tfvars`. The existing `main.tf` handles this with a fallback: `var.ecr_api_image_uri != "" ? var.ecr_api_image_uri : "${aws_ecr_repository.api.repository_url}:latest"`. However, there is no `latest` image in ECR yet at this point — ECS service will be in a pending state until Phase 4 pushes the first image. This is expected behavior; ECS will retry.

**For ACM + HTTPS:** The ACM certificate ARN must be provided before the ALB HTTPS listener and CloudFront aliases are usable. ACM DNS validation requires a Route 53 record. Either:
- (a) Create the ACM cert manually in AWS console, validate via Route 53, then pass the ARN to Terraform
- (b) Add `aws_acm_certificate` + `aws_route53_record` (validation) + `aws_acm_certificate_validation` to Terraform — this works but adds ~2-3 minutes for DNS propagation during `apply`

Option (a) is simpler for initial bootstrap. Option (b) is more repeatable for staging.

---

### Phase 4 — First Image Build and Pipeline Bootstrap

**What:** Push the first Docker images to ECR so ECS services can start. Set up GitHub Actions workflow. Add GitHub repository secrets (AWS role ARN, ECR URIs, ECS cluster/service names from Terraform outputs).

**Why fourth:** ECR repos must exist (Phase 2) before images can be pushed. ECS services must exist (Phase 3) before the deploy workflow can reference them.

**Steps:**
1. Build `deploy/Dockerfile` (api + frontend bundled) locally: `docker build -f deploy/Dockerfile -t {ecr-api-uri}:latest .`
2. Push: `docker push {ecr-api-uri}:latest`
3. Build `deploy/Dockerfile.worker`: `docker build -f deploy/Dockerfile.worker -t {ecr-worker-uri}:latest .`
4. Push: `docker push {ecr-worker-uri}:latest`
5. Force ECS service update: `aws ecs update-service --cluster ... --service ... --force-new-deployment`
6. Create `.github/workflows/deploy.yml` with full pipeline (build → ECR push → migration task → ECS deploy → frontend sync)
7. Add GitHub secrets: `AWS_ROLE_ARN`, `AWS_REGION`, `ECR_API_URI`, `ECR_WORKER_URI`, `ECS_CLUSTER`, `ECS_API_SERVICE`, `ECS_WORKER_SERVICE`, `CLOUDFRONT_DISTRIBUTION_ID`, `S3_FRONTEND_BUCKET`

**Migration task on first deploy:**
The one-off migration ECS task runs `alembic upgrade head`. At first deploy this runs all 11 existing migrations (0001 through 0011) against the fresh RDS instance. This is the only time seed data should be considered — set `RUN_SEED_DATA=true` on the migration task or run seed separately if needed for staging.

---

### Phase 5 — HTTPS, DNS, Custom Domain

**What:** Route 53 hosted zone records, ACM certificate activation, CloudFront alias.

**Why fifth:** Requires Phase 3 (CloudFront distribution ARN, ALB DNS name) to be complete. ACM validation can overlap with Phase 3 but HTTPS is not usable until cert is issued.

**Key wiring:**
- Route 53 A alias: `crm.example.com` → CloudFront distribution domain
- Route 53 CNAME: `_acme-challenge.crm.example.com` → ACM validation CNAME
- ALB listener 443: ACM cert ARN → target group (api, port 8000)
- CloudFront aliases: `[crm.example.com]` with `acm_certificate_arn` (cert must be in us-east-1)
- HTTP → HTTPS redirect: ALB listener 80 redirects to 443

**Testing before DNS cutover:** Access via CloudFront default domain (`*.cloudfront.net`) to verify API and frontend work end-to-end before routing custom domain.

---

### Phase 6 — Azure Warm Failover Infrastructure

**What:** Azure resource group, Azure PostgreSQL Flexible Server, pglogical replication setup, Azure Container Registry, ACI container groups, Azure Key Vault.

**Why last:** Depends on RDS endpoint (Phase 2) as replication source. Depends on ECR image URIs (Phase 4) to mirror images to ACR. Must be done after RDS parameter group changes (Phase 2) take effect.

**Terraform:** New `azure_failover` module called from `environments/prod/main.tf` (not staging — failover is prod-only). Uses `azurerm` provider alongside `aws` provider. State stored at `prod/azure-failover/terraform.tfstate` in the same S3 state bucket (separate key).

**pglogical setup sequence (partially outside Terraform, requires SQL):**
1. Terraform provisions Azure PostgreSQL with `pglogical` in `shared_preload_libraries`
2. Manual step on RDS primary (or run via `null_resource` provisioner):
   ```sql
   CREATE EXTENSION pglogical;
   SELECT pglogical.create_node(node_name := 'provider', dsn := 'host=... dbname=nexuscrm user=nexuscrm password=...');
   SELECT pglogical.create_replication_set('default');
   SELECT pglogical.replication_set_add_all_tables('default', ARRAY['public']);
   ```
3. Manual step on Azure PostgreSQL:
   ```sql
   CREATE EXTENSION pglogical;
   SELECT pglogical.create_node(node_name := 'subscriber', dsn := 'host=azure-host dbname=nexuscrm user=...');
   SELECT pglogical.create_subscription('from_aws', 'host=rds-host dbname=nexuscrm user=...', ARRAY['default']);
   ```
4. Verify replication lag: `SELECT * FROM pglogical.show_subscription_status()`

**Important pglogical constraint:** pglogical does not replicate DDL automatically. Every Alembic migration that runs on RDS must be replicated manually to Azure PostgreSQL **before** the schema change is applied on RDS, or the replication slot will error. The recommended mitigation: run `pglogical.replicate_ddl_command()` for each DDL statement, OR run the migration on both sides simultaneously (apply to Azure first, then RDS).

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| AWS networking pattern | HIGH | Verified against existing terraform/modules/networking/main.tf; matches AWS docs for ECS Fargate private subnet pattern |
| ECS Fargate + Secrets Manager | HIGH | Existing task definitions verified; platform version 1.4.0+ confirmed for JSON key injection |
| CloudFront + ALB + S3 pattern | HIGH | Read cloudfront/main.tf directly; /api/* path routing to ALB, default to S3 is implemented |
| GitHub Actions OIDC | HIGH | IAM OIDC provider and role already provisioned in iam/main.tf |
| Terraform state backend (S3 native locking) | HIGH | DynamoDB locking deprecated; use_lockfile=true confirmed from HashiCorp docs |
| Terraform multi-env directory structure | MEDIUM | Workspaces vs directories is a matter of team convention; directory approach is AWS Prescriptive Guidance recommendation |
| pglogical cross-cloud replication | MEDIUM | RDS logical replication + Azure pglogical subscriber is the supported pattern; DDL replication constraint is a known limitation requiring operational discipline |
| Azure ACI warm failover | MEDIUM | ACI standby pool feature exists but is preview; stopped container groups are the safe approach; manual DNS cutover pattern verified |
| Migration one-off task pattern | MEDIUM | Community actions (geekcell/github-action-aws-ecs-run-task) are well-established; AWS native support via run-task + wait is confirmed |

---

## Sources

- AWS ECS Fargate task networking: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/fargate-task-networking.html
- ECS Secrets Manager injection: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html
- RDS logical replication + pglogical setup: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.pglogical.setup-replication.html
- Terraform S3 backend (use_lockfile): https://developer.hashicorp.com/terraform/language/backend/s3
- Terraform backend best practices (AWS): https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/backend.html
- Azure PostgreSQL logical replication: https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/concepts-logical
- Azure DNS manual failover pattern: https://learn.microsoft.com/en-us/azure/reliability/reliability-dns
- GitHub Actions OIDC AWS integration: https://aws.amazon.com/blogs/security/use-iam-roles-to-connect-github-actions-to-actions-in-aws/
- ECS one-off migration task action: https://github.com/geekcell/github-action-aws-ecs-run-task
- ALB shared across multiple ECS services: https://containersonaws.com/pattern/cdk-shared-alb-for-amazon-ecs-fargate-service/
- RDS PostgreSQL cross-region/cross-cloud replication best practices: https://aws.amazon.com/blogs/database/best-practices-for-amazon-rds-for-postgresql-cross-region-read-replicas/
