---
updated: 2026-04-06
focus: arch
---

# Architecture

**Analysis Date:** 2026-04-06

## Pattern Overview

**Overall:** Three-tier monolithic web application deployed as containerised services on AWS ECS Fargate, with a statically-hosted SPA frontend.

**Key Characteristics:**
- Backend is a single FastAPI application (`backend/api/main.py`) serving all routes under `/api/v1`
- Frontend is a React SPA built with Vite, served from S3 + CloudFront (no container)
- Async Python throughout: SQLAlchemy async, Redis async, httpx async
- Multi-tenant by design: every resource is scoped to `org_id`; enforced by `OrgScopingMiddleware`
- Background work delegated to a Celery worker (separate ECS container, shared codebase image)

## Layers

**API Layer:**
- Purpose: Accept HTTP requests, validate inputs, route to service layer, return responses
- Location: `backend/api/routes/`
- Contains: FastAPI routers — one file per domain (auth, companies, contacts, deals, funds, funding, counterparties, admin, ai_query, analytics, automations, boards, linkedin, orgs, pages, pipelines, tasks, teams, webhooks)
- Depends on: Service layer, SQLAlchemy sessions, Redis, Pydantic schemas
- Used by: Frontend SPA, external webhook callers

**Service Layer:**
- Purpose: Business logic — queries, mutations, domain rules
- Location: `backend/services/`
- Contains: Service classes (`RefDataService`, `DealsService`, etc.) instantiated with `(db, current_user)`
- Depends on: `backend/models.py`, `backend/schemas/`
- Used by: API routes

**Data Layer:**
- Purpose: ORM model definitions and database session management
- Location: `backend/models.py`, `backend/database` (module imported by routes; provides `Base`, `get_engine`, `get_session_maker`, `get_db_session`)
- Contains: 20+ SQLAlchemy ORM models
- Depends on: PostgreSQL via RDS Proxy, SQLAlchemy async
- Used by: Service layer, some routes directly

**Frontend Layer:**
- Purpose: Browser-side SPA — views, API calls, local state
- Location: `frontend/src/`
- Contains: React pages, components, API client modules, Zustand store, React Query hooks
- Depends on: Backend REST API at `/api/v1`
- Used by: End users in browser

**Worker Layer:**
- Purpose: Asynchronous background tasks (Celery)
- Location: `backend/workers/celery_app` (module imported by `backend/api/main.py`)
- Contains: Celery application, task definitions
- Depends on: Redis (broker), PostgreSQL
- Used by: API layer enqueues tasks; Celery worker container executes them

## Data Flow

**Standard API Request:**
1. Browser sends HTTPS request to CloudFront/ALB
2. ALB routes to ECS API container (port 8000)
3. Middleware chain runs: `SecurityHeaders` → `RequestID` → `RequestLogging` → `AuditLog` → `OrgScoping`
4. FastAPI router matches route, injects dependencies (`get_db_session`, `get_current_user`)
5. Route handler calls service class method
6. Service queries PostgreSQL via SQLAlchemy async through RDS Proxy
7. Response serialised through Pydantic schema and returned

**Authentication Flow:**
1. Client POST `/api/v1/auth/login` with username + password (OAuth2PasswordRequestForm)
2. Route verifies bcrypt hash; on success calls `_issue_token_pair(user)`
3. Short-lived JWT access token (HS256, payload: `sub`, `org_id`, `role`) and long-lived refresh token issued
4. Refresh token stored in Redis at key `auth:refresh:{token}` with TTL = `REFRESH_TOKEN_EXPIRE_DAYS * 86400`
5. Subsequent requests include Bearer access token in `Authorization` header
6. `get_current_user` dependency decodes JWT; `OrgScopingMiddleware` extracts `org_id` for row-level scoping
7. Token refresh: POST `/api/v1/auth/refresh` — old refresh token revoked (blacklisted in Redis), new pair issued
8. Logout: refresh token added to Redis blacklist key `auth:blacklist:{token}`

**LinkedIn OAuth Flow:**
1. GET `/api/v1/auth/linkedin/connect` — generates short-lived state JWT, returns LinkedIn auth URL
2. LinkedIn redirects to GET `/api/v1/auth/linkedin/callback?code=...&state=...`
3. Backend exchanges code for LinkedIn access token (httpx); encrypts and stores on `User` record
4. Redirects browser to `{CORS_ORIGINS[0]}/linkedin/connected`

**Background Task Flow:**
1. API route enqueues Celery task via `celery_app`
2. Celery worker (separate ECS container) picks up task from Redis broker
3. Task executes with its own DB session
4. Results stored in DB or Redis as appropriate

**State Management (frontend):**
- Server state: React Query (`@tanstack/react-query`) — queries cached with `staleTime`
- UI state: Zustand (`useUIStore` at `frontend/src/store/useUIStore.js`) — sidebar collapse persisted to `localStorage`

## Key Abstractions

**Organization (tenant):**
- Purpose: Top-level multi-tenancy boundary; all CRM data is org-scoped
- Examples: `backend/models.py` (`Organization` model), `backend/api/routes/auth.py` (org auto-created on first user registration)
- Pattern: Every model has `org_id: ForeignKey("organizations.id", ondelete="CASCADE")`; `OrgScopingMiddleware` binds it to request state

**RefData:**
- Purpose: Configurable lookup tables (company tiers, deal transaction types, investor types, fundraise statuses, etc.) — org-scoped with global defaults where `org_id IS NULL`
- Examples: `backend/models.py` (`RefData` model), `backend/services/ref_data.py`, `backend/api/routes/admin.py`
- Pattern: `category` + `value` + `label` triples with org-scoped unique constraint. Frontend loads via `useRefData(category)` hook (`frontend/src/hooks/useRefData.js`) with 5-minute stale time.

**Service Classes:**
- Purpose: Domain logic encapsulation; receives `(db: AsyncSession, current_user: User)` at construction
- Examples: `backend/services/deals.py`, `backend/services/companies.py`, `backend/services/ref_data.py`
- Pattern: Instantiated inline in route handlers — `await RefDataService(db, current_user).list_by_category(...)`

**API Dependencies:**
- Purpose: FastAPI DI — session, current user, org admin guard
- Location: `backend/api/dependencies` (imported as `get_current_user`, `get_db`, `require_role`)
- Pattern: `Depends(get_current_user)` on protected routes; `Depends(require_role("org_admin"))` on admin routes

## Entry Points

**Backend API:**
- Location: `backend/api/main.py`
- Triggers: Invoked by uvicorn — `uvicorn backend.api.main:app --host 0.0.0.0 --port 8000`
- Responsibilities: Mounts all 19 routers at `/api/v1`, registers middleware stack, initialises DB engine and Redis on startup via `lifespan` context manager, configures rate limiter

**Container Entrypoint:**
- Location: `deploy/entrypoint.sh`
- Triggers: Docker container start
- Responsibilities: Converts `DATABASE_URL` asyncpg DSN to psycopg DSN for Alembic sync; optionally runs seed data if `RUN_SEED_DATA=true`; exec's uvicorn

**Frontend App:**
- Location: `frontend/index.html` (entry), `frontend/src/` (app code)
- Triggers: Browser request to CloudFront URL
- Responsibilities: React Router SPA; `LoginPage` is unauthenticated entry; `Layout` (`frontend/src/components/Layout.jsx`) wraps authenticated routes with sidebar nav

## Error Handling

**Strategy:** FastAPI `HTTPException` propagates naturally as JSON error responses. Rate limit errors handled via `slowapi` exception handler registered at app startup.

**Patterns:**
- 401: invalid/expired tokens, inactive users, invalid credentials, revoked refresh tokens
- 403: role boundary violations, org boundary violations, restricted field updates
- 404: resource not found
- 400: business rule violations (duplicate email/username, invalid team reference)
- 503: readiness probe returns `degraded` when DB, Redis, or S3 checks fail

**Health Endpoints:**
- `/health` — basic status + version + environment
- `/health/live` — liveness (immediate 200)
- `/health/ready` — readiness; independently checks DB, Redis, S3 with latency_ms reporting

## Cross-Cutting Concerns

**Middleware Stack (applied in this order, `backend/api/main.py`):**
1. `SecurityHeadersMiddleware` — security HTTP response headers
2. `RequestIDMiddleware` — attaches `X-Request-ID` to each request
3. `AuditLogMiddleware` — records mutating operations for audit trail
4. `RequestLoggingMiddleware` — structured request/response logging
5. `OrgScopingMiddleware` — extracts `org_id` from JWT, binds to request state for tenant isolation
6. `CORSMiddleware` — configured from `settings.CORS_ORIGINS`
7. `HTTPSRedirectMiddleware` — production only

Middleware is defined in `backend/api/middleware` (imported package).

**Logging:** Structured logging configured via `backend/utils/structured_logging.py` (`setup_logging(settings)`).

**Telemetry:** OpenTelemetry setup via `backend/utils/telemetry.py` (`setup_telemetry(app, settings)`). Prometheus metrics at `/metrics` (API-key-gated in production via `settings.METRICS_API_KEY`).

**Validation:** Pydantic v2 schemas in `backend/schemas/` validate all request payloads. Zod used for frontend form validation (`frontend/src/pages/LoginPage.jsx`).

**Authentication:** JWT Bearer on all protected routes. `get_current_user` dependency validates token and returns `User` ORM object. Roles: `rep`, `org_admin`, `super_admin`.

**Rate Limiting:** `slowapi` with Redis storage backend, keyed by remote IP. Gracefully absent if `slowapi` not installed (handled with `try/except ModuleNotFoundError`).

**Graceful Shutdown:** `backend/utils/graceful_shutdown.py` (`install_signal_handlers`) registered at startup to drain connections cleanly.

## Database Architecture

**Engine:** PostgreSQL 17 (AWS RDS), database name `nexuscrm`

**Connection Pooling:** AWS RDS Proxy sits between ECS containers and RDS instance:
- Max connections: 100% of RDS instance capacity
- Max idle connections: 50%
- Borrow timeout: 120 seconds
- Idle client timeout: 1800 seconds
- TLS required (`require_tls = true`)
- Auth: Secrets Manager (password auth; IAM database auth disabled)

**ORM:** SQLAlchemy 2.x async with `AsyncSession`. Session factory created by `get_session_maker()` at startup.

**Migrations:** Alembic with sequential numbered files (`alembic/versions/0002_*.py` through `0011_*.py`). Run via `alembic upgrade head` using sync psycopg DSN derived from `DATABASE_URL` in `deploy/entrypoint.sh`.

**RDS Configuration:**
- Parameter group: `postgres17` family
- `rds.logical_replication = 1`
- `idle_in_transaction_session_timeout = 30000ms`
- `multi_az` configurable per environment; `true` in prod
- 7-day backup retention; backup window `03:00–04:00 UTC`; maintenance window `sun:05:00–06:00 UTC`
- Storage encrypted; Performance Insights enabled; auto minor version upgrade enabled

**Core Models (defined in `backend/models.py`):**
- `Organization` — tenant root; cascade-deletes all children
- `Team` — org-scoped; self-referential parent/child hierarchy
- `User` — roles: `rep` / `org_admin` / `super_admin`; stores encrypted LinkedIn token
- `Contact` — person; linked to Company, owner User, coverage persons (M2M via `contact_coverage_persons` join table); extensive PE-specific fields
- `Company` — firm; parent company self-ref; extensive PE financial + preference fields (AUM, bite size, co-invest, etc.)
- `Pipeline` + `PipelineStage` — deal flow configuration; stages have position + probability
- `Deal` — central PE record; 40+ fields covering financial metrics, bid amounts, milestone dates, source tracking; linked to Pipeline/Stage/Team/Owner/Contact/Company/Fund
- `DealTeamMember` — M2M join: Deal ↔ User
- `DealCounterparty` — LP/investor engagement per deal; tracks NDA/NRL/VDR dates + check size/AUM
- `DealFunding` — capital commitment tracking per deal per provider
- `Fund` — fund entity with vintage year and target size
- `Board` + `BoardColumn` + `Task` — Kanban task management; tasks linkable to Deals and Contacts
- `Page` — rich-content pages; hierarchical tree (`parent_page_id`)
- `Automation` + `AutomationRun` — trigger/condition/action rules with run history
- `AIQuery` — audit log of natural-language queries: generated SQL, latency, model, status
- `RefData` — lookup values; `org_id` nullable (NULL = global/system defaults)

**Indexing Strategy:**
- Composite `(org_id, <discriminator>)` indexes on all tenant-scoped list queries
- Position indexes for ordered lists (pipeline stages, board columns, tasks)
- `lazy="raise"` on `Deal.counterparties` and `Deal.funding_entries` to prevent accidental N+1 loads

## Infrastructure Architecture

**AWS Region:** `ap-southeast-1` (Singapore) — from `terraform/bootstrap/main.tf`

**Network Layout (per environment):**
```
VPC 10.0.0.0/16
├── Public Subnets: 10.0.1.0/24, 10.0.2.0/24 (2 AZs)
│   ├── Internet Gateway
│   ├── NAT Gateways (1 staging / 2 prod, configurable via nat_gateway_count)
│   └── Application Load Balancer (ports 80+443 inbound)
└── Private Subnets: 10.0.10.0/24, 10.0.20.0/24 (2 AZs)
    ├── ECS Fargate: API container (port 8000)
    ├── ECS Fargate: Worker container (Celery, no inbound)
    ├── AWS RDS Proxy (PostgreSQL 5432)
    ├── AWS RDS Instance (PostgreSQL 17)
    └── AWS ElastiCache Redis 7.1 (port 6379, TLS required)
```

**Security Groups (least-privilege chain):**
- `alb-sg`: inbound 80/443 from `0.0.0.0/0`
- `api-sg`: inbound 8000 from `alb-sg` only
- `worker-sg`: egress-only (no inbound)
- `rds-proxy-sg`: inbound 5432 from `api-sg` + `worker-sg`; egress 5432 to `rds-sg` only
- `rds-sg`: inbound 5432 from `rds-proxy-sg` only
- `redis-sg`: inbound 6379 from `api-sg` + `worker-sg` only

**Container Registry:** AWS ECR — `{env}-api` and `{env}-worker` repositories; immutable image tags; scan on push; lifecycle policy retains last 10 images. Frontend has no ECR repository.

**Secrets Management:**
- AWS Secrets Manager path: `/nexus/{environment}/`
- Terraform creates shell secret resources only — values populated out-of-band (never stored in Terraform state)
- Secrets: `db_password`, `jwt_secret`, `redis_url`, `database_url`, `linkedin_client_id`, `linkedin_client_secret`, `openclaw_api_key`, `sendgrid_api_key`
- ECS execution role: `secretsmanager:GetSecretValue` on `/nexus/{environment}/*`
- ECS task role: CloudWatch Logs write; S3 read/write/delete on assets bucket (if configured)

**CI/CD:**
- GitHub Actions uses OIDC to assume `{env}-github-actions-role` (no long-lived AWS credentials)
- Role grants: ECR push, ECS service update + task definition registration, Secrets Manager read, S3 write (frontend bucket), CloudFront invalidation

**Terraform State:**
- S3 bucket: `nexus-crm-terraform-state` (KMS-encrypted with `alias/nexus-crm-terraform-state`, versioned)
- Bootstrap module at `terraform/bootstrap/` provisions bucket and KMS key once

**Environment Differences (staging vs prod):**
- `db_multi_az`: false (staging) / true (prod)
- `enable_deletion_protection`: false (staging) / true (prod); final snapshot taken in prod
- `nat_gateway_count`: 1 (staging) / 2 (prod) — controls HA for private subnet egress
- `num_cache_clusters`: configurable; ≥2 enables Redis automatic failover + multi-AZ

## Deployment Architecture

**Backend:**
1. Docker image built from repo root; pushed to ECR `{env}-api` repository
2. ECS task definition updated with new image digest
3. ECS service rolling update replaces running API tasks
4. Container runs `deploy/entrypoint.sh` → optional Alembic migration → uvicorn on port 8000

**Celery Worker:**
1. Same Docker image as API pushed to ECR `{env}-worker` repository
2. Container command overridden to launch Celery worker process instead of uvicorn

**Frontend:**
1. Vite builds static assets to `frontend/dist/`
2. Assets synced to S3 frontend bucket
3. CloudFront invalidation clears CDN cache

**Database Migrations:**
- Local: `make migrate` runs `alembic upgrade head` inside docker-compose
- Production: one-off ECS task using the API image

---

*Architecture analysis: 2026-04-06*
