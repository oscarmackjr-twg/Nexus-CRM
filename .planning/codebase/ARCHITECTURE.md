# Architecture

**Analysis Date:** 2026-03-26

## High-Level System Diagram

```
                          ┌─────────────────────────────┐
                          │     React SPA (Vite)         │
                          │  frontend/src/               │
                          │  axios client → /api/v1      │
                          └────────────┬────────────────-┘
                                       │ HTTP + Bearer token
                                       │ X-Org-ID header
                          ┌────────────▼────────────────-┐
                          │     FastAPI App               │
                          │  backend/api/main.py          │
                          │  ── Middleware stack ──       │
                          │  ── 14 route modules ──       │
                          │  ── Service layer ──          │
                          └──────┬─────────────┬──────────┘
                                 │             │
               ┌─────────────────▼──┐   ┌──────▼──────────────┐
               │  PostgreSQL / SQLite│   │  Redis               │
               │  (async SQLAlchemy) │   │  • Refresh tokens    │
               │  alembic migrations │   │  • Celery broker     │
               └────────────────────┘   │  • Rate limiting      │
                                        └──────────────────────┘
                                                  │
                          ┌───────────────────────▼──────────┐
                          │  Celery Worker                    │
                          │  deploy/Dockerfile.worker         │
                          │  • linkedin.sync_contact/company  │
                          │  • ai.enrichment.batch            │
                          │  • automation.run                 │
                          └───────────────────────────────────┘

         React Native Mobile (mobile/) ──► same /api/v1 endpoints
```

---

## Backend: FastAPI Application

### Entry Point

`backend/api/main.py` bootstraps the app via an async `lifespan` context manager that:
1. Initialises structured logging
2. Creates the async SQLAlchemy engine and auto-creates tables
3. Connects the Redis client (stored on `app.state.redis_client`)
4. Sets up OpenTelemetry tracing
5. Installs graceful-shutdown signal handlers tied to the Celery app

### Middleware Stack (applied bottom-up at registration, top-down at execution)

| Middleware | File | Purpose |
|---|---|---|
| `HTTPSRedirectMiddleware` (prod only) | starlette stdlib | Force HTTPS |
| `OrgScopingMiddleware` | `backend/api/middleware.py` | Extracts `X-Org-ID` header into `request.state.org_id` |
| `RequestIDMiddleware` | `backend/api/middleware.py` | Attaches/generates `X-Request-ID`, binds to structured log context |
| `AuditLogMiddleware` | `backend/api/middleware.py` | Appends mutating requests (POST/PUT/PATCH/DELETE) to in-memory per-org audit log |
| `RequestLoggingMiddleware` | `backend/api/middleware.py` | Logs completed requests with latency; sets `X-Response-Time-Ms` |
| `SecurityHeadersMiddleware` | `backend/api/middleware.py` | Sets CSP, HSTS, X-Frame-Options, etc. |
| `CORSMiddleware` | fastapi stdlib | Allows configured origins + credentials |
| `slowapi` rate limiter | optional dependency | Per-IP rate limiting backed by Redis |

### Route Organisation

All routers mount at `/api/v1` prefix. Each module is a single file under `backend/api/routes/`:

| Route module | Prefix | Key resource |
|---|---|---|
| `auth.py` | `/auth` | Login, register, refresh, LinkedIn OAuth |
| `orgs.py` | `/orgs` | Organization CRUD |
| `teams.py` | `/teams` | Team hierarchy management |
| `contacts.py` | `/contacts` | Contact CRUD + bulk import |
| `companies.py` | `/companies` | Company CRUD |
| `pipelines.py` | `/pipelines` | Pipeline and stage management |
| `deals.py` | `/deals` | Deal CRUD, stage moves, activities |
| `boards.py` | `/boards` | Kanban boards and columns |
| `tasks.py` | `/tasks` | Task CRUD within boards |
| `pages.py` | `/pages` | Notion-style document pages |
| `automations.py` | `/automations` | Automation rules |
| `ai_query.py` | `/ai` | Natural-language → SQL queries, deal scoring, forecasting |
| `linkedin.py` | `/linkedin` | OAuth flow, profile enrichment |
| `webhooks.py` | `/webhooks` | Inbound webhook receivers |
| `analytics.py` | `/analytics` | Aggregate dashboard metrics |

Health/observability endpoints live directly on the app root: `/health`, `/health/ready`, `/health/live`, `/metrics`.

### Dependencies

`backend/api/dependencies.py` provides FastAPI `Depends` factories:
- `get_db()` — yields an `AsyncSession` from the session factory
- `get_current_user()` — delegates to `backend/auth/security.py`; injects `User` into handlers
- `require_role(*roles)` — wraps `get_current_user` with role enforcement
- `get_org()` — resolves `Organization` from `X-Org-ID` header or user's `org_id`

### Service Layer

Every domain resource has a paired service class in `backend/services/`:

| Service | File |
|---|---|
| `DealService` | `backend/services/deals.py` |
| `ContactService` | `backend/services/contacts.py` |
| `CompanyService` | `backend/services/companies.py` |
| `PipelineService` | `backend/services/pipelines.py` |
| `BoardService` | `backend/services/boards.py` |
| `PageService` | `backend/services/pages.py` |
| `AutomationService` | `backend/services/automations.py` |
| `AIService` | `backend/services/ai_service.py` |
| `LinkedInService` | `backend/services/linkedin_service.py` |

Services receive `(db: AsyncSession, current_user: User)` in their constructor. All database access happens inside services; routes are kept thin (validate input, instantiate service, return response).

`backend/services/_crm.py` is a shared internal module providing reusable helpers: `accessible_team_ids`, `is_admin`, `is_manager_plus`, `clamp_pagination`, `merge_custom_fields`, `private_deal_predicate`, and SQL expression builders for computed columns (`user_name_expr`, `contact_name_expr`, `deal_activity_subqueries`).

### ORM / Database Layer

- `backend/database.py` — lazy singleton engine and session factory via `create_async_engine` + `async_sessionmaker`
- `backend/models.py` — all SQLAlchemy 2.x `Mapped`/`mapped_column` model definitions (single file)
- Migrations managed by Alembic (`alembic/versions/`)
- Development default: SQLite via `aiosqlite`. Production target: PostgreSQL 15 (dialect-specific JSONB and ARRAY types activate automatically)

---

## Frontend: React SPA

### Bootstrap

`frontend/src/main.jsx` → `frontend/src/App.jsx`

Provider tree (outer to inner):
```
QueryClientProvider (TanStack Query)
  AuthProvider (context/AuthContext.jsx)
    OrgProvider (context/OrgContext.jsx)
      BrowserRouter
        Routes (all routes below)
```

All protected routes are wrapped in `AuthGuard` → `Layout`.

### Routing

Flat route hierarchy in `App.jsx`. Two tiers:
- Public: `/login`
- Protected (inside `AuthGuard` + `Layout`): all other routes

Notable patterns:
- `/pipelines` and `/pipelines/:id` render the same `PipelinePage` component
- Detail pages exist for contacts, companies, deals, boards, and pages

### State Management

Two separate concerns handled by different tools:

**Zustand stores** (in `frontend/src/store/`) — synchronous, persisted client state:
- `useAuthStore.js` — JWT tokens, current user object, `setAuth`/`logout` actions; persisted to `localStorage` under key `nexus-auth`
- `usePipelineStore.js` — active pipeline selection, optimistic deal moves (`moveDeal`)
- `useUIStore.js` — sidebar collapsed state, theme; persisted to `localStorage`
- `useContactStore.js` — contact list cache (lightweight)

**TanStack Query** (in `frontend/src/hooks/`) — server state, caching, invalidation:
- `useDeals.js`, `useContacts.js`, `useAuth.js`, `useAIQuery.js`, `useTeamScope.js`
- Query keys follow `[resource, params]` pattern
- `AuthContext` uses TanStack Query for the `/auth/me` bootstrap call

### API Client

`frontend/src/api/client.js` — single Axios instance with `baseURL: '/api/v1'`.

Two interceptors at request time:
1. Attaches `Authorization: Bearer <token>` from Zustand auth store
2. Attaches `X-Org-ID` from the current user's `org_id`

Domain API modules in `frontend/src/api/` mirror backend routes one-to-one (e.g., `deals.js`, `contacts.js`, `pipelines.js`).

### Auth Flow (Frontend)

1. `AuthProvider` mounts; checks `localStorage` for saved token
2. If token present, fires `GET /api/v1/auth/me` via TanStack Query
3. On success: writes user to Zustand store, sets `bootstrapped = true`
4. On error: calls `clearAuth()`, redirects to `/login`
5. Login mutation hits `POST /api/v1/auth/login`, stores tokens + user via `setAuth`
6. Logout mutation hits `POST /api/v1/auth/logout` (sends refresh token), then calls `queryClient.clear()` + `clearAuth()`

---

## Backend: Auth Flow

1. `POST /api/v1/auth/login` — verifies password with bcrypt, issues access token (HS256 JWT, 8h) + refresh token (30d), stores refresh token in Redis with TTL
2. Bearer token sent on all subsequent requests
3. `get_current_user` in `backend/auth/security.py` — validates JWT, checks `type == "access"`, loads `User` from DB, sets `request.state.current_user`
4. `OrgScopingMiddleware` copies `X-Org-ID` to `request.state.org_id` (middleware runs before auth)
5. After auth, `get_current_user` overwrites `request.state.org_id` with the authenticated user's `org_id`
6. `POST /api/v1/auth/refresh` — validates refresh token against Redis, issues new access token
7. `POST /api/v1/auth/logout` — blacklists refresh token in Redis; client clears localStorage

### Role Hierarchy

Roles stored on `User.role` (string): `super_admin` > `org_admin` > `team_manager` > `rep`

Enforcement via `backend/auth/security.py` guards: `require_org_admin`, `require_team_manager`, and `require_role(*roles)` in `dependencies.py`.

---

## Org Scoping

Every domain model carries `org_id: UUID` as a FK to `organizations`. Services enforce org scope by filtering all queries with `Model.org_id == current_user.org_id`. Multi-tenant isolation is done at query level, not at row-level security.

The `X-Org-ID` header allows switching org context (used for admin/super_admin scenarios). `get_org()` dependency in `dependencies.py` resolves the effective org from either the header or the user's own `org_id`.

---

## Worker: Celery Tasks

Celery app configured in `backend/workers/celery_app.py` — uses Redis as both broker and result backend, `task_acks_late=True`.

| Task name | File | Trigger |
|---|---|---|
| `linkedin.sync_contact` | `backend/workers/linkedin_sync.py` | On-demand from LinkedIn route |
| `linkedin.sync_company` | `backend/workers/linkedin_sync.py` | On-demand from LinkedIn route |
| `ai.enrichment.batch` | `backend/workers/ai_enrichment.py` | Periodic / admin trigger |
| `automation.run` | `backend/workers/automation_runner.py` | Fired by `fire_trigger()` |

Automation triggering: `backend/workers/automation_trigger.py` exposes `fire_trigger(trigger_type, payload, org_id)`. Routes call this after mutating state (e.g., after `create_deal`, `move_stage`). It queries active automations matching the trigger type and enqueues `run_automation.delay()` for each.

All async task bodies use `asyncio.run()` to bridge the sync Celery worker into async SQLAlchemy sessions. Max retries: 3, with exponential backoff and jitter.

---

## Data Flow: Request Lifecycle

```
Client Request
  → CORS middleware
  → SecurityHeaders middleware
  → RequestLogging middleware
  → AuditLog middleware
  → RequestID middleware (generates/reads X-Request-ID, binds log context)
  → OrgScoping middleware (reads X-Org-ID header → request.state.org_id)
  → Route handler
      → get_current_user dependency
          → verify JWT
          → load User from DB
          → overwrite request.state.org_id with user.org_id
      → get_db dependency (yields AsyncSession)
      → instantiate Service(db, current_user)
      → service executes org-scoped query
      → Pydantic schema validates response
  ← JSON response with X-Request-ID, X-Response-Time-Ms headers
```

---

## Math / Scoring Modules

Pure-Python, dependency-free scoring functions in `backend/math/`:

| Module | File | Purpose |
|---|---|---|
| `compute_win_probability` | `backend/math/deal_scoring.py` | Sigmoid-based win probability from 11 engineered features |
| `compute_lead_score` | `backend/math/lead_scoring.py` | Contact lead score computation |
| `compute_forecast` | `backend/math/pipeline_forecast.py` | Pipeline revenue forecasting |

`AIService` in `backend/services/ai_service.py` orchestrates these functions alongside calls to the external OpenClaw LLM API (natural-language → SQL queries).

---

## Database Schema Overview

All models defined in `backend/models.py`. UUIDs as primary keys throughout.

```
Organization
  ├── Team (self-referential parent_team_id, supports hierarchy)
  │    └── User (org_id + team_id)
  ├── Contact (org_id, owner_id → User, company_id → Company)
  ├── Company (org_id, owner_id → User)
  ├── Pipeline (org_id, team_id)
  │    └── PipelineStage (pipeline_id, position UNIQUE per pipeline)
  ├── Deal (org_id, team_id, pipeline_id, stage_id, owner_id, contact_id, company_id)
  │    └── DealActivity (deal_id, user_id)
  ├── Board (org_id, team_id, linked_pipeline_id)
  │    └── BoardColumn (board_id, position UNIQUE per board)
  │         └── Task (board_id, column_id, assignee_id, deal_id, contact_id)
  ├── Page (org_id, team_id, parent_page_id — self-referential tree)
  ├── Automation (org_id, team_id, trigger_type, trigger_config, conditions, actions as JSON)
  │    └── AutomationRun (automation_id, status, result)
  └── AIQuery (org_id, user_id — query audit log)
```

Key constraints:
- `PipelineStage`: `UNIQUE(pipeline_id, position)` — enforces ordered stage positions
- `BoardColumn`: `UNIQUE(board_id, position)` — same for kanban columns
- `Deal.pipeline_id` / `stage_id` / `team_id`: `ondelete=RESTRICT` — prevents orphan deals
- All org-owned models: `ondelete=CASCADE` from `organizations`
- JSON/JSONB columns: `custom_fields` (Contact, Company, Deal, Task), `settings` (Org, Team), `content` (Page), automation `trigger_config`/`conditions`/`actions`

---

## Storage Abstraction

`backend/storage/base.py` defines `StorageBackend` ABC with `save_bytes` / `get_path`. Two implementations:
- `backend/storage/local.py` — filesystem storage (default, `STORAGE_TYPE=local`)
- `backend/storage/s3.py` — AWS S3 (`STORAGE_TYPE=s3`)

Switched via `settings.STORAGE_TYPE`.

---

## Observability

- **Structured logging**: `backend/utils/structured_logging.py` — binds `request_id`, `user_id`, `org_id` to log context per-request
- **Prometheus metrics**: `GET /metrics` endpoint; custom `CounterMetric` in `backend/utils/telemetry.py`; `deal_created_total` and `deal_won_total` counters
- **OpenTelemetry**: optional tracing via `backend/utils/telemetry.py`; activated by `setup_telemetry()` at startup
- **Audit log**: in-memory per-org ring buffer (last 10,000 entries) in `backend/api/middleware.py`

---

*Architecture analysis: 2026-03-26*
