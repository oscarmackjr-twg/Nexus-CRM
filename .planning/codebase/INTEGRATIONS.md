---
updated: 2026-04-06
focus: tech
---

# External Integrations

**Analysis Date:** 2026-04-06

---

## LinkedIn API

**Purpose:** Contact and company enrichment; prospecting search; direct messaging.

**Integration type:** OAuth 2.0 Authorization Code flow + REST API calls

**Client:** Custom `LinkedInService` class — `backend/services/linkedin_service.py`

**API base URL:** `https://api.linkedin.com/v2`

**Scopes requested:** `openid profile email` (configured in OAuth redirect, `backend/api/routes/auth.py` line ~398)

### OAuth Flow

1. User hits `POST /api/v1/auth/linkedin/connect` — server generates a signed JWT state token and returns an `auth_url` pointing to `https://www.linkedin.com/oauth/v2/authorization`
2. LinkedIn redirects to `GET /api/v1/auth/linkedin/callback?code=...&state=...`
3. Server exchanges the code for an access token at `https://www.linkedin.com/oauth/v2/accessToken`
4. Server fetches `https://api.linkedin.com/v2/me` to obtain `linkedin_member_id`
5. Access token is **Fernet-encrypted** (AES-128-CBC) before being stored in the `users` table (`linkedin_access_token` column); key derived from `SECRET_KEY` via SHA-256
6. After completion, user is redirected to `{CORS_ORIGINS[0]}/linkedin/connected`

**Token expiry:** stored in `users.linkedin_token_expiry`; requests made with an expired token receive HTTP 403 with detail `"LinkedIn token expired, please reconnect"`

### API Endpoints Called

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/me` | Fetch own profile |
| GET | `/people` | Search people by keyword/company/title |
| GET | `/people/{id}` | Fetch a person's profile |
| GET | `/organizations` | Search companies |
| GET | `/organizations/{id}` | Fetch company detail |
| GET | `/connections` | List connections |
| POST | `/messages` | Send a direct message |

### Background Sync Tasks (Celery)

- `linkedin.sync_contact` — `backend/workers/linkedin_sync.py`: enriches a single `Contact` from LinkedIn profile data
- `linkedin.sync_company` — `backend/workers/linkedin_sync.py`: enriches a single `Company` from LinkedIn organization data
- Both tasks: `max_retries=3`, exponential backoff with jitter, run on the `linkedin` Celery queue

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `LINKEDIN_CLIENT_ID` | OAuth app client ID |
| `LINKEDIN_CLIENT_SECRET` | OAuth app client secret |
| `LINKEDIN_REDIRECT_URI` | Callback URL (default: `http://localhost:8000/api/v1/auth/linkedin/callback`) |

---

## OpenClaw AI

**Purpose:** Natural-language-to-SQL query engine — converts plain-English CRM queries into SQL that is executed against the database and returned as structured table data.

**Integration type:** REST HTTP (POST) — called from `backend/services/ai_service.py`

**Client:** `httpx.AsyncClient` with 20-second timeout

### Request Flow

1. User submits a natural-language query via `POST /api/v1/ai/query`
2. `AIService.natural_language_query()` sends the query plus a full schema context (5 virtual views: `my_deals`, `my_contacts`, `my_companies`, `pipeline_summary`, `activity_feed`) to `{OPENCLAW_API_URL}/query`
3. OpenClaw returns `{ sql, columns, rows, summary, model_used }`
4. SQL is validated by `backend/utils/sql_validator.py` (`validate_openclaw_sql`) before execution
5. Query is executed against the live database; results are sanitized by `sanitize_query_result`
6. Every query is logged to the `ai_queries` table regardless of success/failure

**Graceful degradation:** if `OPENCLAW_API_URL` is empty or the request fails, the endpoint returns `status="ai_unavailable"` with a human-readable message instead of raising an error.

**AI suggestions cache:** proactive deal/contact/task suggestions generated locally (no OpenClaw call) are cached in Redis for 15 minutes per user (`ai:suggestions:{user_id}`).

**Batch enrichment task:** `ai.enrichment.batch` (`backend/workers/ai_enrichment.py`) — scores all open deals for an org that haven't been scored in 24 hours; runs Python-side weighted scoring model (no OpenClaw call), not the NL query flow.

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENCLAW_API_URL` | Base URL for the OpenClaw service (e.g. `https://api.openclaw.ai`) |
| `OPENCLAW_API_KEY` | API key sent in the JSON body as `"api_key"` field |
| `OPENCLAW_MODEL` | Model identifier string (default: `"auto"`) |

---

## AWS S3

**Purpose:** File/asset storage (uploaded attachments, page content, exported reports).

**Client:** boto3 `>=1.34,<2.0` — `backend/storage/s3.py`

**Abstraction:** `StorageBackend` interface in `backend/storage/base.py`; activated when `STORAGE_TYPE=s3`

**Operations used:**
- `put_object` — write bytes to bucket
- `head_bucket` — readiness check at startup

**In production:** S3 bucket named `{app_name}-{environment}-assets` provisioned by Terraform with AES-256 server-side encryption, versioning enabled, all public access blocked.

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `STORAGE_TYPE` | Set to `s3` to activate (default: `local`) |
| `S3_BUCKET_NAME` | Target bucket name |
| `S3_REGION` | AWS region (default: `us-east-1`) |
| `AWS_ACCESS_KEY_ID` | IAM credentials (optional; uses instance role in production) |
| `AWS_SECRET_ACCESS_KEY` | IAM credentials (optional; uses instance role in production) |

---

## SendGrid (Email)

**Purpose:** Transactional email delivery.

**Current state:** `backend/services/email_service.py` contains only a stub class (`EmailService` with a single `__init__` setting `self.name`). No SendGrid SDK calls are implemented yet. The `SENDGRID_API_KEY` setting is wired up in `backend/config.py` and Terraform secrets, but sending is not functional.

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `SENDGRID_API_KEY` | SendGrid API key (provisioned in AWS Secrets Manager) |

---

## Redis (Multi-purpose)

**Purpose:** Celery message broker, task result backend, auth token store, rate limiter, AI suggestions cache.

**Client:** `redis>=5.0,<6.0` with asyncio support (`redis.asyncio`)

**Connection:** single `REDIS_URL` used by all subsystems (e.g. `redis://redis:6379/0`)

**Key namespaces in use:**

| Prefix | Purpose | TTL |
|--------|---------|-----|
| `auth:refresh:{token}` | Refresh token → user ID mapping | `REFRESH_TOKEN_EXPIRE_DAYS` × 86400 s |
| `auth:blacklist:{token}` | Revoked refresh tokens | `REFRESH_TOKEN_EXPIRE_DAYS` × 86400 s |
| `ai:suggestions:{user_id}` | Cached proactive AI suggestions | 900 s (15 min) |
| Celery internal keys | Task queue and results | Celery-managed |
| SlowAPI keys | Rate limit counters | SlowAPI-managed |

---

## Internal Auth (JWT)

**Purpose:** Stateless access tokens + stateful refresh tokens for all API calls.

**Library:** `python-jose[cryptography]>=3.3,<4.0` — `backend/auth/security.py`

**Algorithm:** HS256 (symmetric; key = `SECRET_KEY` env var)

**Token types:**

| Type | TTL | Storage |
|------|-----|---------|
| Access token | `ACCESS_TOKEN_EXPIRE_MINUTES` (default 480 min / 8 h) | Client only (Bearer header) |
| Refresh token | `REFRESH_TOKEN_EXPIRE_DAYS` (default 30 days) | Client + Redis store |

**Refresh token rotation:** on each `/auth/refresh` call the old token is blacklisted in Redis and a new pair is issued.

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/login` | Username/password → token pair |
| POST | `/api/v1/auth/register` | Create account → token pair |
| POST | `/api/v1/auth/refresh` | Rotate refresh token |
| POST | `/api/v1/auth/logout` | Blacklist refresh token |
| GET | `/api/v1/auth/me` | Current user profile |

---

## Celery / Redis Task Queue

**Purpose:** Offload slow I/O work (LinkedIn sync, AI enrichment, automation execution, email sync) from the API process.

**Broker + backend:** Redis (`REDIS_URL`)

**Celery app:** `backend/workers/celery_app.py`; imported into all worker modules

**Queues and workers:**

| Queue | Tasks |
|-------|-------|
| `default` | `run_automation`, `email_sync`, `automation_trigger` |
| `linkedin` | `linkedin.sync_contact`, `linkedin.sync_company` |
| `ai` | `ai.enrichment.batch` |

**Worker process:** separate Docker container (`deploy/Dockerfile.worker`); concurrency 4; command `celery -A backend.workers.celery_app.celery_app worker --loglevel=info --concurrency=4 -Q default,linkedin,ai`

**Task dispatch from API:** `run_automation.delay(...)` in `backend/api/routes/webhooks.py`

---

## Inbound Webhooks

**Purpose:** Allow external systems to trigger CRM automations via HTTP POST.

**Endpoint:** `POST /api/v1/webhooks/inbound/{automation_id}`

**Handler:** `backend/api/routes/webhooks.py`

**Flow:** Receives arbitrary JSON payload → looks up the `Automation` by ID → dispatches `run_automation.delay(automation_id, payload)` to the `default` Celery queue → returns `{"status": "queued"}` immediately.

**Auth:** No authentication check is present on this endpoint. Any caller with the automation UUID can trigger it.

---

## OpenTelemetry

**Purpose:** Distributed tracing instrumentation.

**Libraries:** `opentelemetry-api>=1.24,<2.0` + `opentelemetry-sdk>=1.24,<2.0`

**Current state:** SDK and TracerProvider are initialised in `backend/utils/telemetry.py` but no exporter (e.g. OTLP, Jaeger, Zipkin) is configured. Traces are collected in-process only; no external tracing backend is wired up.

---

## Prometheus Metrics

**Purpose:** Expose application counters for external scraping.

**Endpoint:** `GET /metrics` — returns Prometheus text format

**Auth:** In production, requires `X-Api-Key: {METRICS_API_KEY}` header (default key `internal-metrics-key`)

**Metrics exported:**

| Metric | Description |
|--------|-------------|
| `deal_created_total` | Deals created |
| `deal_won_total` | Deals won |
| `ai_query_total` | AI query requests |
| `automation_run_total` | Automation runs |
| `linkedin_import_total` | LinkedIn imports |

No external metrics backend (Prometheus server, Datadog agent, etc.) is configured in the repository.

---

## CI/CD — GitHub Actions + AWS

**Pipeline file:** `.github/workflows/deploy.yml`

**Trigger:** push to `main` branch

**Jobs (in order):**

1. `test` — runs pytest on Python 3.11 (bare pip install, no Docker)
2. `build-and-push` — builds API and worker Docker images, pushes to ECR (two repos)
3. `deploy-frontend` — `npm run build` → `aws s3 sync` to S3 frontend bucket → CloudFront cache invalidation
4. `deploy-api` — registers new ECS task definition with updated image URI, updates ECS service, waits for stability (10-minute timeout)
5. `deploy-worker` — same pattern as deploy-api for the worker service (runs after deploy-api)
6. `notify` — posts deploy success/failure to Slack via `SLACK_WEBHOOK` secret (skipped if secret is empty)

**AWS authentication:** OIDC via `aws-actions/configure-aws-credentials@v4` — no long-lived AWS keys stored in GitHub; role ARN in `AWS_ROLE_ARN` GitHub variable.

### Required GitHub Secrets / Variables

| Name | Type | Purpose |
|------|------|---------|
| `AWS_ROLE_ARN` | var | IAM role to assume via OIDC |
| `AWS_REGION` | var | AWS region (default `us-east-1`) |
| `ECS_CLUSTER_NAME` | var | ECS cluster name |
| `API_SERVICE_NAME` | var | ECS API service name |
| `WORKER_SERVICE_NAME` | var | ECS worker service name |
| `API_ECR_REPOSITORY` | var | ECR URI for API image |
| `WORKER_ECR_REPOSITORY` | var | ECR URI for worker image |
| `FRONTEND_BUCKET` | var | S3 bucket for frontend static files |
| `CLOUDFRONT_DISTRIBUTION_ID` | var | CloudFront distribution to invalidate |
| `SLACK_WEBHOOK` | secret | Slack incoming webhook URL (optional) |

---

## Slack (Notifications)

**Purpose:** Deploy success/failure notifications only.

**Integration type:** Incoming webhook (HTTP POST with JSON body)

**Implementation:** Single `curl` call in `.github/workflows/deploy.yml` notify job; no Slack SDK dependency in application code.

**Configuration:** `SLACK_WEBHOOK` GitHub secret; step is skipped when the secret is empty.

---

*Integration audit: 2026-04-06*
