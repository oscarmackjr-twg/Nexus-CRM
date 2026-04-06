---
updated: 2026-04-06
focus: concerns
---

# Codebase Concerns

**Analysis Date:** 2026-04-06

---

## Ghost Files — Backend Cannot Start

The single most critical finding is that `backend/api/main.py` imports **17 modules that do not exist on disk**. The application cannot be imported, the test suite cannot load, and the Docker image would fail at startup. These are all forward-declared stubs for features not yet implemented.

### Missing route modules (imported in `backend/api/main.py` line 19)

- **Files:** `backend/api/main.py:19`
- **Missing:** `backend/api/routes/ai_query`, `backend/api/routes/analytics`, `backend/api/routes/automations`, `backend/api/routes/boards`, `backend/api/routes/linkedin`, `backend/api/routes/orgs`, `backend/api/routes/pages`, `backend/api/routes/pipelines`, `backend/api/routes/tasks`, `backend/api/routes/teams`, `backend/api/routes/webhooks`
- **Present on disk:** Only `admin`, `auth`, `companies`, `contacts`, `counterparties`, `deals`, `funding`, `funds`
- **Impact:** `import backend.api.main` raises `ModuleNotFoundError` immediately. The FastAPI app never loads.
- **Fix approach:** Either stub each missing route file with an empty `APIRouter` (`router = APIRouter()`), or remove the import until the feature is implemented.

### Missing infrastructure modules (imported throughout backend)

- **Files:** Referenced across all route, service, and test files
- **Missing:** `backend/config` (settings), `backend/database` (Base, get_engine, get_session_maker, get_db_session), `backend/auth/schemas`, `backend/auth/security`, `backend/api/middleware`, `backend/api/dependencies`, `backend/utils/graceful_shutdown`, `backend/utils/structured_logging`, `backend/utils/telemetry`, `backend/workers/celery_app`, `backend/workers/automation_trigger`, `backend/services/_crm`
- **Impact:** Every backend file that imports these modules is also broken. The entire backend is non-functional without them.
- **Fix approach:** These modules must exist and are presumably being developed. They must be created before any integration testing is possible.

### Missing frontend entry point

- **Files:** `frontend/index.html:12`
- `index.html` references `<script type="module" src="/src/main.jsx">` but `frontend/src/main.jsx` does not exist.
- **Impact:** The frontend cannot boot in a browser. Vite dev server will 404 on the module.
- **Fix approach:** Create `frontend/src/main.jsx` with the React root rendering (`createRoot(document.getElementById('root')).render(...)`).

### Missing frontend API client

- **Files:** `frontend/src/api/*.js` (all 6 files, line 1 each)
- Every frontend API module imports `from './client'` but `frontend/src/api/client.js` does not exist.
- **Impact:** All API calls fail immediately with a module resolution error.
- **Fix approach:** Create `frontend/src/api/client.js` as an Axios or fetch wrapper with auth header injection.

### Missing frontend API modules

- **Files:** `frontend/src/pages/ContactDetailPage.jsx`, `frontend/src/pages/DashboardPage.jsx`, `frontend/src/pages/DealDetailPage.jsx`
- **Missing:** `@/api/deals`, `@/api/boards`, `@/api/ai`, `@/api/funds`
- **Impact:** Three of five pages cannot load; every deal-related and AI-related frontend call fails.

### Missing frontend components and hooks

- **Files:** Multiple pages and `frontend/src/components/Layout.jsx`
- **Missing:** `@/components/ui/badge`, `@/components/ui/button`, `@/components/ui/card`, `@/components/ui/dialog`, `@/components/ui/input`, `@/components/ui/label`, `@/components/ui/skeleton`, `@/components/ui/table`, `@/components/ui/tabs`, `@/components/ui/select`, `@/components/ui/switch`, `@/components/ui/textarea`, `@/components/LinkedInPanel`, `@/components/AIQueryBar`, `@/hooks/useAuth`, `@/lib/utils` (cn, formatCurrency, formatDate)
- **Impact:** All page components fail to render. The shadow/UI library (shadcn/ui) components are expected but none are installed.
- **Fix approach:** Install shadcn/ui components or create the missing component files. Create `@/hooks/useAuth` and `@/lib/utils`.

### Missing test utilities

- **Files:** `frontend/src/__tests__/Layout.test.jsx:4`, `frontend/src/__tests__/LoginPage.test.jsx:4`
- `test-utils.jsx` is imported from `./test-utils` but does not exist in the `__tests__` directory.
- **Impact:** All three frontend test files fail to import.

### Missing frontend package.json

- **Files:** `frontend/` directory
- There is no `package.json`, no `package-lock.json`, and no `node_modules` directory in the `frontend/` folder.
- **Impact:** `npm install` / `npm run dev` / `npm run build` all fail immediately. Dependency versions are unknown.
- **Fix approach:** Create `frontend/package.json` with all required dependencies (React, Vite, shadcn/ui, zustand, react-query, react-hook-form, zod, axios, etc.).

### Missing Dockerfile and docker-compose.yml

- **Files:** `deploy/` directory (only `entrypoint.sh` present), Makefile references
- The Makefile's `dev`, `test`, `migrate`, `seed`, `docker-up`, `docker-down` targets all reference `deploy/docker-compose.yml` which does not exist. No `Dockerfile` exists anywhere in the repository.
- **Impact:** `make dev` fails. Local development, CI, and the described ECS deployment are all blocked.
- **Fix approach:** Create `deploy/docker-compose.yml` for local dev and `Dockerfile` (or separate `Dockerfile.api` / `Dockerfile.worker`) for container builds.

---

## Ghost Files — Backend Tests Cannot Run

The test suite imports ghost modules on load, so `pytest` fails before any test executes.

### conftest.py patches non-existent modules

- **Files:** `backend/tests/conftest.py:134-135`, `conftest.py:253`
- `monkeypatch.setattr("backend.api.routes.ai_query.redis_async...")` and `monkeypatch.setattr("backend.services.ai_service.redis_async...")` and `monkeypatch.setattr("backend.api.routes.linkedin._client...")` all reference modules that do not exist.
- Also references `backend/schemas/linkedin` inside mock fixtures (lines 228, 240).
- **Impact:** The `fake_redis` fixture fails to monkeypatch, and any test using it errors out before execution.

### Missing initial alembic migration

- **Files:** `alembic/versions/` directory
- Migration `0002_pe_ref_data.py` sets `down_revision = "0001_initial"` but no file with `revision = "0001_initial"` exists in the versions directory.
- **Impact:** `alembic upgrade head` fails with an unknown revision error. The database cannot be initialised from scratch.
- **Fix approach:** Create `alembic/versions/0001_initial.py` with the base schema (organizations, teams, users, contacts, companies, pipelines, pipeline_stages, deals, deal_activities, ref_data tables).

---

## Infrastructure — Incomplete Deployment Layer

Phase 13 provisioned only the data/security layer. The infrastructure cannot serve any traffic yet.

### No ECS, ALB, or compute modules in Terraform

- **Files:** `terraform/environments/prod/main.tf`, `terraform/environments/staging/main.tf`
- Terraform provisions: VPC/subnets, ECR repos, RDS (PostgreSQL 17), RDS Proxy, ElastiCache (Redis 7), Secrets Manager shells, IAM roles.
- Missing: ECS cluster, ECS task definitions, ECS services (API + worker), ALB, ALB listener rules, CloudFront distribution, S3 frontend bucket, Route 53 records, ACM certificate wiring.
- **Impact:** The ECR images have nowhere to run. The ALB security group is defined but no ALB exists. The `app_domain` and `acm_certificate_arn` variables are already declared as Phase 14 placeholders, confirming this is planned but not yet built.
- **Operational risk:** The `github_repository` OIDC role is fully provisioned, so GitHub Actions can push images to ECR, but cannot deploy them anywhere.

### Networking module outputs ALB security group with no ALB

- **Files:** `terraform/modules/networking/outputs.tf:13-14`, `terraform/modules/networking/main.tf:115-142`
- `alb_security_group_id` is exported but consumed by nothing yet. The security group allows port 80 and 443 from `0.0.0.0/0` — it exists in the VPC but is unused.
- **Impact:** Not blocking, but dead infrastructure. Risk is that Phase 14 adds an ALB relying on the exact SG definition and discovers it needs modification.

### Secrets Manager shells are empty

- **Files:** `terraform/modules/secrets/main.tf`
- Terraform creates Secret ARNs but explicitly populates no values (`put-secret-value` must be run out-of-band via `make tf-secrets-staging` / `make tf-secrets-prod`).
- **Impact:** Any ECS task that tries to inject secrets from Secrets Manager will fail with an empty secret value until the Makefile populate commands are run. There is no automated check that secrets are populated before a task definition is deployed.
- **Fix approach:** Add a deployment pre-flight check or CI step that asserts all required secrets have non-empty values before deploying task definitions.

### No monitoring, alerting, or logging infrastructure

- **Files:** Entire `terraform/` tree
- No CloudWatch alarms, no SNS topics, no log groups with retention, no X-Ray tracing, no Datadog/Sentry terraform resources.
- **Impact:** Failures in production (OOM, high latency, DB connection exhaustion) are silent until a user reports them. The `/health/ready` endpoint exists but nothing polls it.
- **Fix approach:** Phase 15+ should add CloudWatch metric alarms for ECS task CPU/memory, RDS FreeStorageSpace, and 5xx ALB error rate, plus a log group for ECS task stdout/stderr.

### RDS backup retention is 7 days — no cross-region backup

- **Files:** `terraform/modules/rds/main.tf:48`
- Production has 7-day automated backups but no cross-region replication. A region-level failure means up to 7 days of potential data loss window for point-in-time recovery.
- **Impact:** Low probability, high severity. Acceptable for MVP but should be addressed before significant data is in the system.

---

## Security Concerns

### Open self-registration creates unlimited orgs and users

- **Files:** `backend/api/routes/auth.py:152-193`
- `POST /api/v1/auth/register` requires no invitation, no email verification, no admin approval. Any anonymous caller can create a new Organisation and admin user. There is no limit on how many orgs can be created.
- **Impact:** Spam org creation, resource exhaustion, abuse of trial tier.
- **Fix approach:** Add email domain allowlisting, invite-only registration, or CAPTCHA. At minimum, rate-limit the endpoint.

### Rate limiting is entirely optional (slowapi may not be installed)

- **Files:** `backend/api/main.py:27-35`, `backend/api/routes/auth.py`
- `slowapi` is imported in a `try/except ModuleNotFoundError` block. If the package is not in the container image, `Limiter` is `None` and no rate limiting is applied anywhere. No `@limiter.limit(...)` decorators are present on the login or register routes regardless.
- **Impact:** Without `slowapi` in `requirements.txt` (which does not exist), rate limiting is silently absent.

### `/metrics` endpoint is unprotected in non-production environments

- **Files:** `backend/api/main.py:171-177`
- The `X-API-Key` check only applies when `settings.ENVIRONMENT == "production"`. In staging, `/metrics` is fully public.
- **Impact:** Internal Prometheus counters (org IDs, deal counts, error rates) are readable without authentication on staging.

### LinkedIn OAuth redirect uses `CORS_ORIGINS[0]` without validation

- **Files:** `backend/api/routes/auth.py:447-449`
- The LinkedIn callback redirects to `f"{settings.CORS_ORIGINS[0]}/linkedin/connected"`. If `CORS_ORIGINS` is misconfigured, the OAuth flow redirects the browser there with the user's session context.
- **Impact:** Low risk given `CORS_ORIGINS` is server-side config, but fragile. Prefer a hardcoded `FRONTEND_URL` setting.

### Health endpoints expose version and environment to anonymous callers

- **Files:** `backend/api/main.py:106-109`
- `GET /health` returns `{"status": "ok", "version": __version__, "environment": "production"}`. Leaking environment name and version aids reconnaissance.
- **Impact:** Low severity. Standard practice for health checks but worth noting for hardened deployments.

---

## Data Model Concerns

### `DealActivity.contact_id` uses `String(36)` instead of `Uuid()`

- **Files:** `backend/models.py:499`
- `DealActivity.contact_id` is typed `Mapped[Optional[str]] = mapped_column(String(36), ...)` while every other UUID foreign key column uses `Uuid()` or `PG_UUID`. This inconsistency causes type mismatch errors when comparing `contact_id` with UUID values.
- **Impact:** Queries filtering by `contact_id` may behave differently across SQLite (tests) and PostgreSQL (production).
- **Fix approach:** Change to `Mapped[Optional[UUID]] = mapped_column(Uuid(), ForeignKey(...))`.

### Many model classes lack Alembic migrations

- **Files:** `alembic/versions/`, `backend/models.py`
- Models with no corresponding migration: `Board`, `BoardColumn`, `Task`, `Page`, `Automation`, `AutomationRun`, `AIQuery`, `Pipeline`, `PipelineStage`, `Organization`, `Team`, `User` (initial schema).
- `Base.metadata.create_all` in `backend/api/main.py:44` and `backend/seed_data.py:15` masks this by creating tables directly, bypassing migration tracking.
- **Impact:** A production database initialised from Alembic alone would be missing all these tables. `create_all` and Alembic are both running, creating schema drift.
- **Fix approach:** Remove `create_all` from the application lifespan. Write proper `op.create_table(...)` migrations for every table not yet covered.

### Text search uses `LIKE '%term%'` with no full-text index

- **Files:** `backend/services/contacts.py`, `backend/services/companies.py`, `backend/api/routes/auth.py:278`
- Contact, company, and user search all use `ilike(f"%{term}%")`. On PostgreSQL, this pattern cannot use a B-tree index and requires a full table scan.
- **Impact:** Search degrades to O(n) as record counts grow. Noticeable above ~10,000 contacts per org.
- **Fix approach:** Add a `tsvector` GIN index on concatenated name/email columns, or use `pg_trgm` trigram indexes.

---

## Performance Concerns

### `get_engine().dialect.name` called on every deal query

- **Files:** `backend/services/deals.py:60`
- `_base_deal_stmt` calls `get_engine().dialect.name` on every invocation to detect SQLite vs PostgreSQL. This re-evaluates dialect detection per request rather than once at startup.
- **Fix approach:** Cache `dialect_name` at service class instantiation time or at module import time.

### Dashboard fans out 4–7 parallel requests with no aggregation endpoint

- **Files:** `frontend/src/pages/DashboardPage.jsx`
- The dashboard issues at minimum 4 concurrent API calls and may chain additional per-board detail calls. Deals and contacts are fetched in bulk for client-side aggregation.
- **Impact:** Dashboard load time is gated on the slowest API call. At scale, fetching 100 deals and 100 contacts purely for count/value aggregation is wasteful.
- **Fix approach:** Add a `GET /api/v1/dashboard/summary` endpoint returning pre-aggregated stats.

---

## Technical Debt

### No `requirements.txt`, `pyproject.toml`, or `setup.py`

- **Files:** `backend/` root
- There is no Python dependency manifest anywhere in the repository. The exact versions of FastAPI, SQLAlchemy, slowapi, httpx, celery, and all other packages are unknown.
- **Impact:** Builds are not reproducible. `slowapi` may not be installed. `boto3` referenced in `main.py:129` may not be installed. Any dependency upgrade could silently break the app.
- **Fix approach:** Create `pyproject.toml` (or `requirements.txt` + `requirements-dev.txt`) with pinned versions. Add it to the Docker build.

### No `__init__.py` files — backend is not a proper Python package

- **Files:** `backend/`, `backend/api/`, `backend/api/routes/`, `backend/services/`, `backend/schemas/`, `backend/tests/`
- None of these directories contain `__init__.py`. Imports like `from backend.models import ...` only work if the project root is on `PYTHONPATH`. Without `__init__.py` and proper packaging, the import structure is fragile and tooling (mypy, pytest discovery, IDEs) may misbehave.
- **Fix approach:** Add empty `__init__.py` to each package directory, or switch to `pyproject.toml` with a `src/` layout.

### Seed data uses a weak hardcoded password

- **Files:** `backend/seed_data.py:37`
- The demo admin user is created with `hash_password("password123")`. If seed data is ever run against a staging environment with public access (controlled by `RUN_SEED_DATA=true`), a known weak password exists on a real server.
- **Fix approach:** Read the seed password from an environment variable, or use a randomly generated value that is printed once and not committed.

### `Base.metadata.create_all` on every startup (production risk)

- **Files:** `backend/api/main.py:43-44`, `backend/seed_data.py:15`
- `create_all` runs at every application startup, including production. This can silently add columns that Alembic does not track, causing schema drift. It also adds startup latency proportional to metadata size.
- **Fix approach:** Remove from `lifespan`. Schema management should be exclusively through `alembic upgrade head` in `entrypoint.sh`.

### Audit log stored in process memory only

- **Files:** `backend/api/middleware.py` (ghost file — `AuditLogMiddleware` is imported but the file does not exist)
- The architecture intends an audit log in `AuditLogMiddleware`, but the middleware file does not exist. Even when implemented, in-process storage would be lost on restart.
- **Fix approach:** Write audit events to a `audit_logs` database table or structured log stream.

---

## Operational Concerns

### No CI/CD pipeline defined

- **Files:** No `.github/workflows/` directory
- The IAM OIDC trust for GitHub Actions is fully provisioned, but there is no workflow YAML in the repository. No automated tests, linting, image builds, or deployments are triggered on push.
- **Impact:** All deployments are manual. There is no gate preventing broken code from reaching staging.
- **Fix approach:** Add `.github/workflows/ci.yml` with test, lint, image build, and push steps. Add `.github/workflows/deploy-staging.yml` for automated staging deploys on main branch push.

### No Makefile target for running tests locally without Docker

- **Files:** `Makefile:test`
- The `test` target invokes `docker-compose -f deploy/docker-compose.yml run --rm backend pytest ...` but `docker-compose.yml` does not exist. Tests cannot be run via the documented interface.

### `make dev` is entirely broken

- **Files:** `Makefile:dev`
- `make dev` runs `cd deploy && docker-compose up --build` but `deploy/docker-compose.yml` does not exist. There is no local development workflow available.

### `tf-apply-staging` has no corresponding `tf-apply-prod`

- **Files:** `Makefile`
- There is a `tf-apply-staging` target but no `tf-apply-prod` target. Production applies must be run manually via `cd terraform/environments/prod && terraform apply`, bypassing any Makefile safeguards.

---

## Previously Identified Concerns (from 2026-03-26 audit)

The following concerns were documented in the previous audit. Their status cannot be confirmed given the missing ghost files, but they remain relevant:

- **SECRET_KEY default "change-me-in-production"** — `backend/config.py:13` (file is a ghost). HIGH severity.
- **JWT tokens in localStorage** — `frontend/src/store/useAuthStore.js` (ghost file). MEDIUM severity.
- **CSP allows `unsafe-inline`** — `backend/api/middleware.py` (ghost file). MEDIUM severity.
- **Inbound webhook has no authentication** — `backend/api/routes/webhooks.py` (ghost file). MEDIUM severity.
- **Analytics routes return `not_implemented`** — `backend/api/routes/analytics.py` (ghost file). HIGH severity.
- **Celery email sync task is a stub** — `backend/workers/email_sync.py` (ghost file). HIGH severity.
- **`apply_tag_filter` uses substring LIKE** — `backend/services/_crm.py` (ghost file). MEDIUM severity.
- **Audit log in process memory** — `backend/api/middleware.py` (ghost file). MEDIUM severity.
- **Cron automations lost on restart** — `backend/services/automations.py` (ghost file). LOW severity.
- **N+1 in `get_proactive_suggestions`** — `backend/services/ai_service.py` (ghost file). LOW severity.
- **No token refresh interceptor** — `frontend/src/api/client.js` (ghost file). MEDIUM severity.
- **Docker Compose healthcheck missing** — `deploy/docker-compose.yml` (ghost file). HIGH severity.

All of the above are blocked by the ghost-file situation. They should be re-verified once the missing modules are created.

---

*Concerns audit: 2026-04-06*
