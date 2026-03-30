# Pitfalls Research: Cloud Deployment

**Project:** Nexus CRM — v1.2 Cloud Deployment
**Stack:** FastAPI + SQLAlchemy 2.0 async + PostgreSQL + Redis + Celery, migrating from Docker Compose to ECS Fargate (multi-service: api, frontend, worker), RDS PostgreSQL + ElastiCache Redis, Azure PostgreSQL Flexible Server warm failover, GitHub Actions CI/CD, Terraform IaC, AWS Secrets Manager
**Researched:** 2026-03-29
**Confidence:** MEDIUM-HIGH (AWS/ECS/Alembic findings verified with official docs and multiple sources; Azure cross-cloud replication findings MEDIUM — fewer authoritative independent sources)

---

## ECS Fargate / Container Pitfalls

### Pitfall 1: `latest` Image Tag Causes Silent Stale Deployments

**What goes wrong:** Since June 2024, ECS enforces software version consistency by caching the image digest from the first task in a deployment. If you push a new image to ECR under the same `latest` tag and redeploy, ECS reports success but continues running the old image. The tag moved, but ECS's cached digest did not update.

**Why it happens:** ECS resolves image tags to SHA256 digests at task launch and pins that digest for the deployment lifetime. A tag re-assignment in ECR does not update the pinned digest in the running service.

**Consequences:** Pipeline shows green. App silently runs stale code. Extremely difficult to diagnose without inspecting the task's image digest directly.

**Prevention:**
- Enable ECR tag immutability on all repositories. This forces each push to use a new tag.
- Tag every image with the Git commit SHA (`$GITHUB_SHA`), not `latest`. Update the task definition image reference to the new commit-SHA tag in each pipeline run.
- Never use floating tags (`latest`, `stable`, `current`) for any task definition in staging or production.

**Detection:** `aws ecs describe-tasks --tasks <task-arn>` — inspect `containers[].imageDigest` and compare against what ECR shows for the expected tag.

---

### Pitfall 2: Docker Compose `volumes`, `build`, and `restart` Directives Are Silently Dropped

**What goes wrong:** Nexus CRM currently runs via `make dev` with Docker Compose. `services.build`, host-path volume mounts (`./config:/app/config`), and `restart: always` are not supported by ECS Fargate. The Docker Compose CLI generates warnings but proceeds. The resulting task definition has no persistent storage and no restart policy.

**Why it happens:** Fargate uses `awsvpc` networking and an ephemeral task filesystem. Host paths do not exist. Compose-to-ECS translation is lossy.

**Consequences:** Config files or assets mounted via bind-mount in Compose are absent in ECS containers. Any file written to the container filesystem is lost when the task restarts. `restart: always` becomes an ECS service restart policy, which behaves differently.

**Prevention:**
- Write native ECS task definitions in Terraform (`aws_ecs_task_definition`) rather than converting from Compose. Treat `docker-compose.yml` as the local dev contract and the Terraform task definition as the production contract — they are separate artifacts.
- Audit `docker-compose.yml` for any bind-mounted files that the app reads at runtime. Those files must be baked into the Docker image or fetched from S3/Secrets Manager at startup.
- For Nexus CRM specifically: confirm no `.env`-adjacent config files are bind-mounted. Seed data scripts must not rely on host-path files.

---

### Pitfall 3: Health Check Grace Period Mismatch Causes Infinite Deployment Loop

**What goes wrong:** FastAPI starts, but the SQLAlchemy async connection pool has not yet connected to RDS (cold start, security group propagation, or the Alembic migration runner is still executing). The ALB health check fires immediately, fails, ECS marks the task unhealthy, terminates it, and starts a replacement — indefinitely.

**Why it happens:** The default `healthCheckGracePeriodSeconds` is 0. ECS begins ALB health checks the moment the container is running, not when the app is ready.

**Consequences:** New service version never reaches healthy state. Rolling deployment stalls. Old tasks remain in service (not updated) if minimum healthy percent is set correctly; if not set, downtime occurs.

**Prevention:**
- Set `healthCheckGracePeriodSeconds = 60` (minimum) on every ECS service behind an ALB. 120 seconds is safer for first-deploy scenarios.
- Implement a `/health` endpoint in FastAPI that checks database connectivity (a lightweight `SELECT 1`) and returns 200 only when the app is fully ready.
- Set ALB target group deregistration delay to 30 seconds (not the 300-second default) to accelerate rolling deployments. 300 seconds × 3 services = 15 minutes of unnecessary waiting per deployment.

---

### Pitfall 4: SIGTERM Not Handled — In-Flight Requests and Celery Tasks Are Killed Mid-Execution

**What goes wrong:** When ECS replaces a task during rolling deployment, it sends SIGTERM, waits `stopTimeout` (default 30 seconds), then sends SIGKILL. If FastAPI/Uvicorn does not handle SIGTERM gracefully, open HTTP requests are dropped mid-response. If the Celery worker does not handle SIGTERM, in-flight tasks (AI scoring, async operations) are interrupted with no retry.

**Why it happens:** Uvicorn's default SIGTERM behavior is immediate shutdown. Celery workers similarly do not complete in-progress tasks unless configured with warm shutdown.

**Consequences:** Rolling deployments produce 5xx errors for API clients. Celery tasks that were mid-execution are lost and may leave partial state in the database (e.g., a half-updated deal score).

**Prevention:**
- Configure Uvicorn with `--timeout-graceful-shutdown 30`. Set the ECS API task definition `stopTimeout` to 60 seconds.
- For Celery workers: configure `REMAP_SIGTERM = "SIGQUIT"` or use `--max-tasks-per-child` to ensure tasks complete before shutdown. Set the ECS worker task definition `stopTimeout` to 120 seconds. This allows long AI scoring tasks to finish before the container is killed.
- Set the ALB target group deregistration delay to match the API graceful shutdown window (30 seconds) so new requests stop arriving before SIGTERM is sent.

---

### Pitfall 5: `somaxconn` Is Fixed at 128 on Fargate — Cannot Be Changed

**What goes wrong:** Fargate does not allow changing kernel parameters. The TCP listen queue (`net.core.somaxconn`) is locked at 128. Under burst load, connection attempts beyond this queue are silently dropped.

**Why it happens:** Fargate is managed serverless compute — the host kernel is shared and locked. `--ulimit` directives in Docker or `sysctl` calls in container startup have no effect.

**Consequences:** Intermittent connection-refused errors under load spikes that do not appear in local Docker Compose testing. This is a hard ceiling on concurrent incoming connections, not a configurable limit.

**Prevention:**
- Use RDS Proxy or PgBouncer to limit actual database connections per task well below this ceiling.
- Set SQLAlchemy `pool_size` and `max_overflow` conservatively — the bottleneck is Fargate's kernel limit, not the database's.
- Design for horizontal scaling (more tasks) rather than higher per-task connection counts.

---

## RDS PostgreSQL Pitfalls

### Pitfall 1: Connection Exhaustion When ECS Services Scale Out

**What goes wrong:** Each ECS task opens a SQLAlchemy async connection pool. At default settings (`pool_size=5`, `max_overflow=10`), each task can open 15 connections. At 10 API tasks + 5 worker tasks = 225 potential connections. RDS PostgreSQL `db.t3.medium` `max_connections` defaults to approximately 170 (calculated from instance memory). Scale event triggers `FATAL: sorry, too many clients already` errors across all tasks simultaneously.

**Why it happens:** PostgreSQL uses one OS process per connection. The default RDS `max_connections` formula (`LEAST({DBInstanceClassMemory/9531392}, 5000)`) yields surprisingly low values on small/medium instances.

**Consequences:** Sudden 500 errors across the entire API under any load spike. This failure mode does not appear in single-container local testing and is often first discovered during the first real traffic event.

**Prevention:**
- Deploy **RDS Proxy** in Terraform between ECS and RDS. RDS Proxy multiplexes hundreds of application connections into a small pool of actual database connections. This is the AWS-native solution and avoids running PgBouncer as a sidecar service.
- With RDS Proxy: set SQLAlchemy `pool_size=2`, `max_overflow=3` per task. RDS Proxy handles the pooling.
- Without RDS Proxy: `pool_size` must be sized as `floor(max_connections / expected_task_count) - 5` (leaving a buffer for migration runner and admin connections).
- In Terraform, set `max_connections` explicitly in an RDS parameter group rather than relying on the formula default. Monitor `DatabaseConnections` CloudWatch metric. Alert at 80% of `max_connections`.

---

### Pitfall 2: Multi-AZ Failover Drops All Existing Connections for 30–120 Seconds

**What goes wrong:** RDS Multi-AZ automatic failover (triggered on instance failure or maintenance) takes 30–120 seconds. All existing TCP connections to the primary are dropped. SQLAlchemy's connection pool holds stale connections that will raise errors on next checkout.

**Prevention:**
- Set `pool_pre_ping=True` on the SQLAlchemy async engine. This issues `SELECT 1` before each connection checkout, discarding stale connections and reconnecting transparently.
- Set `pool_recycle=300` to periodically recycle connections before they go stale.
- With RDS Proxy: Proxy handles failover reconnection transparently, significantly reducing app-visible downtime. This is the strongest mitigation.

---

### Pitfall 3: RDS Parameter Group Must Be Custom — Default Group Cannot Be Modified

**What goes wrong:** Terraform provisions RDS with the default parameter group (`default.postgres15`). This group cannot be modified. Any attempt to change `rds.logical_replication`, `max_connections`, `log_min_duration_statement`, or `idle_in_transaction_session_timeout` fails because default parameter groups are AWS-managed and read-only.

**Prevention:**
- Always create a custom `aws_db_parameter_group` in Terraform and assign it to the RDS instance at creation time. Changing the parameter group after creation requires a reboot.
- For Nexus CRM v1.2: include the following parameters from the start:
  - `rds.logical_replication = 1` (required for Azure replication — enables without needing a later reboot)
  - `wal_sender_timeout = 0` (prevents replication slot disconnection during cross-cloud network hiccups)
  - `idle_in_transaction_session_timeout = 30000` (kills sessions idle in transaction after 30s — prevents migration lock cascades)

---

## Alembic Migrations in Pipeline

### Pitfall 1: App Containers Start Before Migration Runner Completes

**What goes wrong:** GitHub Actions calls `aws ecs run-task` for the migration runner, then immediately calls `aws ecs update-service` for the API service. ECS is asynchronous — the migration runner may still be executing when the first API task starts. The API task boots against an un-migrated schema. SQLAlchemy models reference columns that do not exist yet.

**Why it happens:** `aws ecs run-task` returns immediately after task submission, not after task completion. Without explicit polling, the pipeline does not wait.

**Consequences:** API task boots, makes a query using a new column, gets `UndefinedColumn` from PostgreSQL, fails the health check, gets killed, creates a new task — migration loop.

**Prevention:**
- After `aws ecs run-task`, poll using `aws ecs wait tasks-stopped --tasks <task-arn>`. This blocks the pipeline step until the task exits.
- Assert the task exit code is 0 before proceeding: `aws ecs describe-tasks --tasks <task-arn> --query 'tasks[0].containers[0].exitCode'`. If non-zero, fail the pipeline immediately.
- Only after successful migration does the pipeline proceed to `aws ecs update-service`.
- The migration runner must use the **same image** as the API container (same ECR image, different `command` override: `["alembic", "upgrade", "head"]`). Never maintain a separate migration image — version skew between migration and app schemas is a common cause of mysterious failures.

---

### Pitfall 2: `alembic upgrade head` Holds ACCESS EXCLUSIVE Locks and Blocks the Entire Table

**What goes wrong:** Common Alembic operations on active tables — `ADD COLUMN NOT NULL DEFAULT`, `CREATE INDEX` (without CONCURRENTLY), `DROP COLUMN`, `ALTER TYPE` — acquire `ACCESS EXCLUSIVE` locks in PostgreSQL. Any open query on the table queues behind this lock. If one long-running application transaction is open when the migration starts, every subsequent query on that table queues behind both the lock request and that transaction. Under load, this exhausts all available connections within seconds.

**Why it happens:** PostgreSQL MVCC requires exclusive locks for schema changes. The migration acquires the lock, but if it cannot immediately get it (due to an existing open transaction), it waits — and all subsequent queries on the table wait behind it.

**Consequences:** Full application outage cascading from a single open transaction. The database appears healthy (no errors) but no queries complete. Connection pool fills with waiting connections.

**Prevention:**
- Set `lock_timeout = '5s'` and `statement_timeout = '30s'` as session variables at the start of every migration runner execution. In the Alembic `env.py` `run_migrations_online()` function, add: `connection.execute(text("SET lock_timeout = '5s'"))`. This causes the migration to fail fast rather than block indefinitely.
- Use `CREATE INDEX CONCURRENTLY` for all new index operations. In Alembic: `op.create_index(..., postgresql_concurrently=True)`. Note: this cannot run inside a transaction — wrap with `with op.get_context().autocommit_block():`.
- Set `idle_in_transaction_session_timeout = 30000` in the RDS parameter group (see above) to auto-kill idle-in-transaction sessions that would otherwise hold open transactions during migration.
- For Nexus CRM: this project has 11+ migrations with frequent `ADD COLUMN` operations, and new phases continue this pattern. Establish the `lock_timeout` session variable convention in `env.py` before the first ECS migration run.

---

### Pitfall 3: No Rollback Path for Destructive Migrations

**What goes wrong:** A migration drops a column or changes a column type. The new ECS deploy fails health checks. Rolling back the ECS service to the previous task definition (old app image) now runs against an incompatible schema — the old app code expects the dropped column.

**Prevention:**
- Write `downgrade()` functions in every Alembic migration file. Test them locally with `alembic downgrade -1`.
- Before any migration that includes a destructive operation, take an RDS snapshot in the pipeline: `aws rds create-db-snapshot --db-snapshot-identifier nexus-pre-migration-$(date +%Y%m%d%H%M%S)`. Insert this as a pipeline step before `alembic upgrade head`.
- Enforce the expand-contract pattern for column changes: (1) add new column alongside old, (2) deploy app that writes both, (3) backfill, (4) drop old column in a separate, later deploy. Never drop a column in the same migration that adds its replacement.

---

### Pitfall 4: Parallel Pipeline Runs Create Migration Version Conflicts

**What goes wrong:** Two GitHub Actions runs execute simultaneously (hotfix merge and feature branch merge to staging). Both reach the migration runner step. The first runner applies `head`. The second runner sees head is already applied and exits 0 silently — but the head it applied may be from a different migration branch if two developers created migration files with the same base revision.

**Prevention:**
- Use `alembic check` (or `alembic heads` asserting a single head) as a validation step in the CI test stage before deployment. Fail the pipeline if the migration graph has multiple heads.
- Use GitHub Actions `concurrency: group: deploy-staging` to serialize deployments to staging. Never allow two deploys to the same environment to run simultaneously.

---

## Cross-Cloud DB Replication (AWS RDS to Azure PostgreSQL Flexible Server)

### Pitfall 1: Enabling Logical Replication Requires an RDS Parameter Change and Instance Reboot

**What goes wrong:** Logical replication (required to stream WAL changes from RDS to Azure) is controlled by `rds.logical_replication = 1` in the RDS parameter group. Changing this parameter is not hot-applied — it requires an instance reboot. Applying this to an already-deployed production instance causes a maintenance-window disruption.

**Why it happens:** PostgreSQL WAL level must change from `replica` to `logical` at startup. It cannot change on a running instance.

**Consequences:** A future reboot disruption on a live production database, which was not anticipated if the parameter was not set at initial provisioning.

**Prevention:**
- Set `rds.logical_replication = 1` in the Terraform custom parameter group at initial RDS provisioning, even if replication is not configured yet. The instance is rebooted once at creation — this avoids a future unplanned reboot.
- Also set `wal_sender_timeout = 0` from the start to prevent cross-cloud replication slots from disconnecting during network hiccups.

---

### Pitfall 2: Azure PostgreSQL Flexible Server Drops Logical Replication Slots on HA Failover (PostgreSQL 16 and Earlier)

**What goes wrong:** Azure Flexible Server HA uses synchronous physical replication to a standby. When the server fails over to the standby, logical replication slots — including the slot pointing from AWS RDS — are **not** transferred. The replication slot is destroyed on the standby. The "warm" Azure failover database silently diverges from AWS and accumulates lag from that point.

**Why it happens:** Logical replication slots are local to the primary instance. Standard Flexible Server HA does not migrate them.

**Consequences:** After any Azure HA event (even routine maintenance failover), the warm failover database is hours or days stale. You discover this at the worst possible moment: when you need the failover and attempt cutover.

**Prevention:**
- Install the **`pg_failover_slots`** extension on Azure Flexible Server before starting replication. This Microsoft-supported extension replicates logical slots to the standby before failover.
- In Terraform (`azurerm_postgresql_flexible_server_configuration`): set `pg_failover_slots.enabled = on`.
- Monitor replication lag continuously via RDS `ReplicaLag` metric (CloudWatch) and Azure Monitor metrics on the Flexible Server. Alert if lag exceeds 5 minutes.

---

### Pitfall 3: Cross-Cloud WAL Egress Costs Are Ongoing and Growth-Proportional

**What goes wrong:** Logical replication streams WAL changes from AWS to Azure continuously. AWS charges $0.09/GB for data leaving a region. For a write-active CRM, even moderate write volume produces meaningful ongoing monthly egress costs.

**Why it happens:** AWS treats cross-cloud replication as outbound internet data transfer.

**Consequences:** Budget surprise in month 2–3 as WAL volume becomes apparent.

**Prevention:**
- Before committing to continuous logical replication, establish a WAL generation baseline: run `SELECT pg_current_wal_lsn()` at hourly intervals on the existing database to estimate daily WAL volume.
- Consider whether the warm failover SLA requires continuous replication or whether a daily RDS snapshot restore to Azure is sufficient. For Nexus CRM (a PE CRM with moderate write volume), a daily snapshot restore may provide acceptable RTO (~1–2 hours) at significantly lower cost than continuous streaming.
- Document this decision and the chosen RTO/RPO explicitly in the deployment plan.

---

### Pitfall 4: SSL Configuration Mismatch Between RDS Publisher and Azure Subscriber

**What goes wrong:** Recent RDS instances enforce SSL (`rds.force_ssl = 1` by default). The `CREATE SUBSCRIPTION` command on the Azure side must include explicit SSL parameters (`sslmode`, `sslrootcert`). Omitting these causes a confusing "could not connect to the PostgreSQL server" error on the Azure side, not an SSL error message.

**Prevention:**
- Download the AWS RDS CA certificate bundle and configure it as a trusted CA on the Azure Flexible Server before creating the subscription.
- Use `sslmode=verify-full` in the `CREATE SUBSCRIPTION` connection string. Never use `sslmode=disable` for cross-cloud database replication.
- Test the TCP connection from Azure to RDS port 5432 manually (via `psql` from an Azure VM in the same VNet) before automating the subscription in Terraform. Rule out network ACLs and security group rules first.

---

### Pitfall 5: The Azure Subscriber Needs the Schema Applied Separately — Logical Replication Is Data-Only

**What goes wrong:** PostgreSQL logical replication replicates DML (INSERT/UPDATE/DELETE), not DDL (CREATE TABLE, ALTER TABLE). The Azure Flexible Server receives row changes but has no tables to apply them to. Subscription creation succeeds, but replication worker errors appear immediately in the Azure logs.

**Why it happens:** This is standard PostgreSQL logical replication behavior, not an Azure limitation. Schema must exist on the subscriber before replication can start.

**Consequences:** The Azure warm failover database has no schema, cannot receive replicated rows, and silently lags from day one.

**Prevention:**
- Include a pipeline step that runs `pg_dump --schema-only` from RDS and applies it to Azure before the subscription is created.
- Every time Alembic runs a migration on the AWS side, the same migration must be applied to the Azure Flexible Server. Add an Azure migration propagation step to the pipeline: after the AWS migration runner completes, run a second migration runner against the Azure connection string using the same Alembic image.
- The Azure migration step must use read-write access to the Azure Flexible Server (the replication user is read-only for replication but a separate admin user is needed for DDL).

---

## Secrets Management Pitfalls

### Pitfall 1: Rotated Secrets Are Not Picked Up by Running Containers — Split-Brain Credential State

**What goes wrong:** ECS injects secrets from Secrets Manager at task **startup time**. The secret value is baked into the container's environment at launch. If a secret is rotated (database password, JWT signing key), running containers continue using the old value. New tasks (from the next deployment) use the new value. During the window where old and new tasks coexist (rolling deployment), different tasks use different credentials.

**Why it happens:** ECS resolves the Secrets Manager ARN to a plaintext value when the task starts. There is no live injection — ECS does not watch for secret changes.

**Consequences:** If the old and new credentials are incompatible (e.g., RDS password changed and the old password was immediately invalidated), old tasks fail all database queries while new tasks succeed — split behavior that is very difficult to diagnose.

**Prevention:**
- Coordinate secret rotation with a forced ECS deployment: after rotating any secret, immediately run `aws ecs update-service --force-new-deployment` on all affected services. If using automated rotation Lambdas, trigger this as part of the rotation Lambda's completion hook.
- For database credentials specifically, use **RDS Proxy** — RDS Proxy handles credential rotation transparently without requiring ECS task recycling.
- Use a rotation strategy where the old credential remains valid for a grace period (e.g., 24 hours) after the new one is issued, allowing old tasks to continue functioning through their natural replacement cycle.

---

### Pitfall 2: Adding a New Secret Requires a Task Definition Update — No Hot Injection

**What goes wrong:** A new external API key is added to Secrets Manager. Running ECS tasks do not receive it. The `secrets` block in the ECS task definition must be updated with the new secret ARN, a new task definition revision must be registered, and the service must be updated before any container sees the new secret.

**Prevention:**
- Treat the task definition `secrets` array as infrastructure code — manage it in Terraform. Adding a new secret = a Terraform change + a deploy.
- Never add secrets directly in the ECS console, bypassing Terraform. This creates state drift that is tedious to reconcile.

---

### Pitfall 3: Local Development Breaks If the App Requires Secrets Manager at Startup

**What goes wrong:** If the FastAPI app is modified to call `boto3.client('secretsmanager').get_secret_value(...)` at startup (replacing `.env` file loading), developers without AWS credentials or VPN access cannot start the stack locally with `make dev`.

**Prevention:**
- Do not change the app to call Secrets Manager directly. ECS injects secrets as **environment variables** before the container starts — the app never calls Secrets Manager SDK. This means the app remains cloud-agnostic: it reads env vars, which come from `.env` in dev and from Secrets Manager injection in ECS.
- Use `pydantic-settings` with `BaseSettings` reading from environment variables. In local dev, `.env` supplies the values. In ECS, Secrets Manager injection supplies them. Zero app code change required.

---

### Pitfall 4: IAM Task Execution Role Needs `secretsmanager:GetSecretValue` Scoped to Specific ARNs

**What goes wrong:** Using `Resource: "*"` for `secretsmanager:GetSecretValue` works but violates least-privilege. More practically: a typo in a secret name in the task definition results in a silent access error that is hard to diagnose because the wildcard masks the 404.

**Prevention:**
- Scope the IAM policy to specific ARN prefixes: `arn:aws:secretsmanager:ap-southeast-1:ACCOUNT_ID:secret:nexus-crm/prod/*`.
- This forces explicit enumeration of all secrets in Terraform, which serves as documentation of what secrets the app requires.
- Use separate secret paths for staging and production: `nexus-crm/staging/` and `nexus-crm/prod/`. This ensures a misconfigured staging task cannot read production secrets.

---

## Terraform State & Multi-Cloud Pitfalls

### Pitfall 1: Separate State Backends for AWS and Azure Create Cross-Reference Complexity

**What goes wrong:** AWS Terraform resources use an S3 + DynamoDB backend. Azure Terraform resources use an Azure Storage backend. When AWS outputs (RDS endpoint, VPC CIDR) are needed as inputs to Azure Terraform resources (subscription connection string, network peering), teams either hard-code values or use `terraform_remote_state` data sources. A change to AWS state does not automatically re-evaluate Azure resources.

**Prevention:**
- For Nexus CRM's scale, use a **single root Terraform module** with both `hashicorp/aws` and `hashicorp/azurerm` providers, backed by a single S3 backend. This keeps all infrastructure in one state file, eliminates cross-state references, and simplifies `terraform plan` output.
- Separate modules (subdirectories) for AWS and Azure within the single root module preserve organizational clarity without requiring separate state backends.
- If separate state backends become necessary later, use `terraform_remote_state` data sources — never hard-code cross-cloud values.

---

### Pitfall 2: `terraform apply` Touching the ECS Service Resource Triggers a Rolling Task Restart

**What goes wrong:** Terraform treats any change to the `aws_ecs_service` resource — even a tag update or description change — as requiring a service update. ECS implements service updates by launching new tasks, effectively causing a rolling restart on every `terraform apply` run, even when the application code has not changed.

**Why it happens:** Terraform's resource update mechanism is not aware that certain ECS service attribute changes are operationally harmless. It triggers a service update regardless.

**Consequences:** Infrastructure-only changes (adding a tag, updating a description) cause unnecessary application restarts. In a CI pipeline that runs `terraform apply` on every merge, this creates constant background churn.

**Prevention:**
- Use `lifecycle { ignore_changes = [task_definition] }` on `aws_ecs_service` in Terraform. This tells Terraform to never update the task definition reference on the service resource.
- Let the GitHub Actions pipeline (not Terraform) own task definition updates and service deploys. Terraform owns infra (VPC, RDS, IAM, ALB, security groups, ECR). GitHub Actions owns image builds and ECS service updates.
- This creates a clean separation: `terraform apply` only changes infrastructure, not running application versions.

---

### Pitfall 3: Terraform Import Without Matching HCL Attributes Causes Destroy-on-Next-Apply

**What goes wrong:** Any resource manually created before Terraform provisioning (e.g., an ECR repo created by hand to test image pushes) causes a conflict when Terraform tries to create it. The temptation is to `terraform import` the existing resource — but if the HCL block does not exactly match all the existing resource's attributes, Terraform plans destructive changes on the next run.

**Why it happens:** Terraform uses default values for any HCL attribute not explicitly specified. If the imported resource has non-default attributes, Terraform sees a diff and plans to "fix" it — which may mean destroy and recreate.

**Consequences:** Running `terraform apply` after an incomplete import destroys the imported resource.

**Prevention:**
- For a new project like Nexus CRM v1.2: provision everything through Terraform from the start. No manual console clicks on resources Terraform will manage.
- If any resource was manually created: use `terraform import`, then immediately run `terraform plan` and verify zero diff before any `terraform apply`. Use `terraform plan -generate-config-out=generated.tf` (Terraform >= 1.5) to generate the matching HCL automatically.
- Add `lifecycle { prevent_destroy = true }` to the RDS instance and the Terraform state S3 bucket immediately after first apply.

---

### Pitfall 4: Provider Version Drift Between Local Development and CI

**What goes wrong:** Developer runs `terraform init` locally and gets AWS provider 5.82.0. CI runs `terraform init` three weeks later and resolves 5.84.0. Provider minor version changes can alter plan output for the same HCL, causing CI apply to make unexpected changes.

**Prevention:**
- Pin provider versions exactly in `required_providers`: `version = "= 5.82.0"`, not `">= 5.0"`.
- Commit `.terraform.lock.hcl` to source control.
- In CI, use `terraform init -lockfile=readonly` to enforce the committed lock file. If providers need upgrading, do it deliberately and commit the updated lock file.

---

## GitHub Actions + ECR/ECS Pitfalls

### Pitfall 1: Three Services, One Pipeline — Migration / Deployment Race Condition

**What goes wrong:** Nexus CRM has three ECS services: `api`, `frontend`, `worker`. A naive pipeline builds all images in parallel and calls `aws ecs update-service` for all three simultaneously. If the migration runner and `update-service api` are not strictly sequenced, the API service starts before the schema migration completes. The API boots against an un-migrated schema.

**Prevention:**
- Structure the pipeline with explicit sequential stages:
  1. Build and push all images to ECR in parallel (safe — images are not running yet)
  2. Run migration ECS task; poll `aws ecs wait tasks-stopped`; assert exit code 0
  3. Update `api` and `worker` services (both depend on migrated schema); wait for stability with `--wait-for-service-stability`
  4. Update `frontend` service (no schema dependency — can run in parallel with step 3)
- Use `needs:` in GitHub Actions job definitions to enforce this dependency graph explicitly.

---

### Pitfall 2: OIDC IAM Trust Policy Misconfiguration Silently Falls Back to Long-Lived Credentials

**What goes wrong:** The OIDC IAM role trust policy is scoped to `repo:org/repo:ref:refs/heads/main`. A manual workflow dispatch or a deploy from a `release/*` branch fails with `Error: No credentials`. If both OIDC and static `AWS_ACCESS_KEY_ID` secrets are configured in the repo, the pipeline falls back to the static credentials and continues — masking the OIDC misconfiguration.

**Prevention:**
- Configure OIDC only. Do not configure both OIDC and static IAM credentials in the same repository. If OIDC fails, the pipeline must fail — this is the intended behavior.
- Use a permissive trust condition for branch scope during initial setup: `repo:ORG/REPO:*` or scope to the specific branches that trigger deploys.
- Validate OIDC authentication with a no-op job (`aws sts get-caller-identity`) before wiring up the full deployment workflow.

---

### Pitfall 3: Task Definition Revisions Created by Pipeline Cause Terraform State Drift

**What goes wrong:** The `aws-actions/amazon-ecs-deploy-task-definition` GitHub Action registers a new task definition revision on every pipeline run. Terraform manages the ECS service by task definition ARN. After the pipeline runs, Terraform sees that the service is using a task definition revision it did not create, and on the next `terraform apply`, it updates the service back to its managed revision — rolling back the pipeline's deployment.

**Why it happens:** ECS task definitions are immutable and versioned. Every `register-task-definition` call creates a new revision. Terraform and the CI pipeline both believe they own the task definition.

**Prevention:**
- Use `lifecycle { ignore_changes = [task_definition] }` on `aws_ecs_service` in Terraform (same mitigation as Pitfall 2 in the Terraform section).
- Accept that Terraform owns the task definition **template** (first revision, with placeholder image). Subsequent revisions are owned by the CI pipeline. Tag pipeline-created revisions with the pipeline run ID for traceability.
- Never run `terraform apply` as part of the deploy pipeline unless you have explicitly verified it will not revert the task definition to an old revision.

---

### Pitfall 4: ECR Lifecycle Policies Not Set — Storage Costs Accumulate Rapidly

**What goes wrong:** Three ECR repositories × multiple deploys per day × no lifecycle policy = hundreds of stored images within weeks. ECR charges per GB stored. Images from active development accumulate quickly.

**Prevention:**
- Add `aws_ecr_lifecycle_policy` in Terraform for each ECR repository from day one:
  - Keep the last 10 images tagged with commit SHAs.
  - Expire untagged images after 1 day.
- Apply this at initial provisioning. Retroactively cleaning hundreds of images requires a manual CLI sweep.

---

### Pitfall 5: Staging and Production Share an ECR Repository — Wrong Image Deployed

**What goes wrong:** Both staging and prod pipelines push to the same ECR repository. A production deploy picks up a staging-only image, or vice versa. Especially risky if both use commit SHA tags (the same SHA exists in both envs) and the pipeline logic has a bug.

**Prevention:**
- Use separate ECR repositories per environment: `nexus-crm/staging/api` and `nexus-crm/prod/api`.
- Alternatively, use image promotion: build once and push to the staging repository. After staging validation, copy (promote) the image to the production repository using `aws ecr batch-get-image` + `aws ecr put-image`. Production deploys only ever pull from the production repository.
- Never allow feature branches to push to the production ECR repository.

---

## Phase-Specific Warnings

| Deployment Phase | Likely Pitfall | Mitigation |
|------------------|---------------|------------|
| Initial Terraform provisioning | `prevent_destroy` not set — accidental RDS destroy on plan mistake | Add `lifecycle { prevent_destroy = true }` to RDS and state bucket before first apply |
| First ECR push + ECS service creation | `latest` tag used as placeholder | Implement commit-SHA tagging immediately; enable ECR tag immutability from first push |
| Alembic migration runner wiring | Pipeline deploys app before migration completes | Mandatory: `aws ecs wait tasks-stopped` + exit code assertion before `update-service` |
| RDS provisioning | Default parameter group cannot be modified | Create custom parameter group in Terraform with `rds.logical_replication=1` and `idle_in_transaction_session_timeout` set before first apply |
| First ECS scale test | Connection exhaustion at low task counts | Deploy RDS Proxy before enabling auto-scaling on ECS services |
| Secrets Manager wiring | App modified to call Secrets Manager SDK directly, breaking local dev | Keep env-var injection model; app must not call Secrets Manager SDK — only ECS task execution role calls it |
| Azure replication setup | Logical replication requires RDS reboot if parameter not pre-set | Set `rds.logical_replication=1` at initial provisioning |
| Azure HA configuration | Replication slot lost on Azure HA failover | Install `pg_failover_slots` extension and set `pg_failover_slots.enabled=on` before starting replication |
| Celery worker deployment | In-flight tasks killed on SIGTERM during rolling deployment | Set `stopTimeout=120s` on worker task definition; configure Celery warm shutdown |
| API deployment health checks | Deployment loop due to ALB health check firing before app is ready | Set `healthCheckGracePeriodSeconds=60` on API service; implement `/health` endpoint with DB connectivity check |
| Multi-env setup | Staging and prod share ECR repos | Separate ECR repos per environment from the start |
| Terraform in CI | Provider version drift between local and CI | Commit `.terraform.lock.hcl`; use `init -lockfile=readonly` in CI |
| Azure schema synchronization | Azure Flexible Server has no schema when replication starts | Pipeline must apply `pg_dump --schema-only` + Alembic migration to Azure before starting subscription |

---

## Sources

- [Docker Compose ECS Fargate subtle limitations (Medium)](https://medium.com/@defyrlt/docker-compose-with-aws-ecs-fargate-overview-of-subtle-limitations-24ccb8b320cf)
- [ECS latest image digest — AWS re:Post](https://repost.aws/knowledge-center/ecs-latest-image-digest)
- [ECR and ECS container image best practices — AWS ECS Developer Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/container-considerations.html)
- [ECS graceful shutdowns — AWS Containers Blog](https://aws.amazon.com/blogs/containers/graceful-shutdowns-with-ecs/)
- [ECS health check grace period — AWS re:Post](https://repost.aws/knowledge-center/fargate-alb-health-checks)
- [RDS Proxy production lessons (To The New)](https://www.tothenew.com/blog/rds-proxy-in-production-real-world-lessons-limitations-and-why-we-use-it/)
- [PgBouncer on AWS ECS (RevenueCat)](https://www.revenuecat.com/blog/engineering/pgbouncer-on-aws-ecs/)
- [Performance impact of idle PostgreSQL connections — AWS Database Blog](https://aws.amazon.com/blogs/database/performance-impact-of-idle-postgresql-connections/)
- [Alembic migrations without downtime (Exness)](https://medium.com/exness-blog/alembic-migrations-without-downtime-a3507d5da24d)
- [Zero-downtime Postgres migrations — lock_timeout and retries (PostgresAI)](https://postgres.ai/blog/20210923-zero-downtime-postgres-schema-migrations-lock-timeout-and-retries)
- [Zero-downtime upgrades with Alembic and SQLAlchemy (that.guru)](https://that.guru/blog/zero-downtime-upgrades-with-alembic-and-sqlalchemy/)
- [AWS RDS logical replication documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/PostgreSQL.Concepts.General.FeatureSupport.LogicalReplication.html)
- [Azure PostgreSQL Flexible Server logical replication (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/concepts-logical)
- [Logical replication problem with Azure PostgreSQL Flexible Server — Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/404797/logical-replication-problem-with-azure-postgresql)
- [Online migration: RDS PostgreSQL to Azure Database for PostgreSQL (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/dms/tutorial-rds-postgresql-server-azure-db-for-postgresql-online)
- [Azure DMS known issues — online PostgreSQL migration (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/dms/known-issues-azure-postgresql-online)
- [ECS Secrets Manager injection — AWS ECS Developer Guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/secrets-envvar-secrets-manager.html)
- [Secrets rotation ECS restart — AWS re:Post](https://repost.aws/questions/QUYHw--TXvTTewJeVsT2T5QA/automatically-restart-ecs-service-tasks-containers-after-secret-rotation)
- [Terraform state locking (Spacelift)](https://spacelift.io/blog/terraform-state-lock)
- [Terraform import and RDS drift (DEV Community)](https://dev.to/dm8ry/how-to-import-aws-rds-instances-into-terraform-and-safely-manage-drift-365e)
- [Terraform resource drift — HashiCorp Developer](https://developer.hashicorp.com/terraform/tutorials/state/resource-drift)
- [aws-actions/amazon-ecs-deploy-task-definition (GitHub)](https://github.com/aws-actions/amazon-ecs-deploy-task-definition)
- [Secure CI/CD for ECS with GitHub Actions (DEV Community)](https://dev.to/suzuki0430/building-a-secure-cicd-workflow-for-ecs-with-github-actions-gde)
- [ECS task image versioning and consistency (Xebia)](https://xebia.com/blog/ecs-version-consistency-ecs-task-definition-images/)
