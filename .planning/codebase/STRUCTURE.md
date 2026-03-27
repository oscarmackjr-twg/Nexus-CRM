# Codebase Structure

**Analysis Date:** 2026-03-26

## Directory Layout

```
nexus-crm/
├── backend/                    # Python FastAPI application
│   ├── api/                    # HTTP layer (routes, middleware, deps)
│   │   ├── main.py             # FastAPI app factory + lifespan
│   │   ├── middleware.py       # Custom Starlette middlewares
│   │   ├── dependencies.py     # Reusable FastAPI Depends factories
│   │   └── routes/             # One file per domain resource
│   │       ├── auth.py
│   │       ├── contacts.py
│   │       ├── companies.py
│   │       ├── deals.py
│   │       ├── pipelines.py
│   │       ├── boards.py
│   │       ├── tasks.py
│   │       ├── pages.py
│   │       ├── automations.py
│   │       ├── ai_query.py
│   │       ├── linkedin.py
│   │       ├── orgs.py
│   │       ├── teams.py
│   │       ├── webhooks.py
│   │       └── analytics.py
│   ├── auth/                   # Auth utilities (JWT, bcrypt, OAuth)
│   │   ├── security.py         # Token creation/verification, get_current_user
│   │   ├── schemas.py          # UserRole enum, Token/UserCreate Pydantic models
│   │   ├── validators.py       # Input validators (email, password strength)
│   │   ├── rate_limiter.py     # Auth-specific rate limit helpers
│   │   └── create_admin.py     # CLI script to seed admin user
│   ├── services/               # Business logic layer (one class per domain)
│   │   ├── _crm.py             # Shared helpers: org scoping, pagination, SQL exprs
│   │   ├── deals.py            # DealService
│   │   ├── contacts.py         # ContactService
│   │   ├── companies.py        # CompanyService
│   │   ├── pipelines.py        # PipelineService
│   │   ├── boards.py           # BoardService
│   │   ├── pages.py            # PageService
│   │   ├── automations.py      # AutomationService
│   │   ├── ai_service.py       # AIService (LLM queries, scoring, forecasting)
│   │   ├── linkedin_service.py # LinkedInService (OAuth, profile enrichment)
│   │   ├── analytics_service.py
│   │   └── email_service.py
│   ├── schemas/                # Pydantic request/response models (per domain)
│   │   ├── deals.py
│   │   ├── contacts.py
│   │   ├── companies.py
│   │   ├── pipelines.py
│   │   ├── boards.py
│   │   ├── pages.py
│   │   ├── automations.py
│   │   ├── ai.py
│   │   ├── linkedin.py
│   │   ├── analytics.py
│   │   └── tasks.py
│   ├── workers/                # Celery async task definitions
│   │   ├── celery_app.py       # Celery app + config (broker=Redis)
│   │   ├── ai_enrichment.py    # ai.enrichment.batch task
│   │   ├── automation_runner.py # automation.run task
│   │   ├── automation_trigger.py # fire_trigger() helper (async)
│   │   ├── linkedin_sync.py    # linkedin.sync_contact/company tasks
│   │   └── email_sync.py       # email sync stub
│   ├── math/                   # Pure-Python scoring algorithms (no DB deps)
│   │   ├── deal_scoring.py     # compute_win_probability (sigmoid model)
│   │   ├── lead_scoring.py     # compute_lead_score
│   │   └── pipeline_forecast.py # compute_forecast
│   ├── storage/                # Pluggable file storage abstraction
│   │   ├── base.py             # StorageBackend ABC
│   │   ├── local.py            # Filesystem implementation
│   │   └── s3.py               # AWS S3 implementation
│   ├── utils/                  # Cross-cutting utilities
│   │   ├── structured_logging.py # structlog setup, request context binding
│   │   ├── telemetry.py        # OpenTelemetry + Prometheus CounterMetric
│   │   ├── graceful_shutdown.py # Signal handlers for clean shutdown
│   │   ├── sql_validator.py    # AI-query SQL sanitiser/validator
│   │   └── db_constraints.py   # Constraint helper utilities
│   ├── tests/                  # pytest test suite (see TESTING.md)
│   ├── models.py               # All SQLAlchemy ORM models (single file)
│   ├── database.py             # Async engine + session factory
│   ├── config.py               # Pydantic Settings (env-driven config)
│   ├── seed_data.py            # Development seed script
│   └── requirements.txt        # Python dependencies (duplicates pyproject.toml)
│
├── frontend/                   # React SPA (Vite + JSX)
│   └── src/
│       ├── main.jsx            # Vite entry point
│       ├── App.jsx             # Provider tree + BrowserRouter + all Routes
│       ├── styles.css          # Global CSS
│       ├── api/                # Axios API modules (one per domain)
│       │   ├── client.js       # Shared axios instance with auth interceptors
│       │   ├── auth.js
│       │   ├── contacts.js
│       │   ├── companies.js
│       │   ├── deals.js
│       │   ├── pipelines.js
│       │   ├── boards.js
│       │   ├── pages.js
│       │   ├── automations.js
│       │   ├── ai.js
│       │   ├── linkedin.js
│       │   ├── analytics.js
│       │   ├── search.js
│       │   ├── teams.js
│       │   └── users.js
│       ├── store/              # Zustand stores (synchronous client state)
│       │   ├── useAuthStore.js       # JWT tokens + user; localStorage persisted
│       │   ├── usePipelineStore.js   # Active pipeline + optimistic deal moves
│       │   ├── useUIStore.js         # Sidebar + theme; localStorage persisted
│       │   └── useContactStore.js    # Contact list cache
│       ├── context/            # React contexts (bridge Zustand <-> TanStack Query)
│       │   ├── AuthContext.jsx # Login/logout mutations + /me bootstrap query
│       │   └── OrgContext.jsx  # Current org resolution
│       ├── hooks/              # TanStack Query wrappers (server state)
│       │   ├── useDeals.js
│       │   ├── useContacts.js
│       │   ├── useAuth.js
│       │   ├── useAIQuery.js
│       │   ├── useTeamScope.js
│       │   └── useDebounce.js
│       ├── pages/              # Route-level page components
│       │   ├── LoginPage.jsx
│       │   ├── DashboardPage.jsx
│       │   ├── ContactsPage.jsx
│       │   ├── ContactDetailPage.jsx
│       │   ├── CompaniesPage.jsx
│       │   ├── CompanyDetailPage.jsx
│       │   ├── PipelinePage.jsx
│       │   ├── DealDetailPage.jsx
│       │   ├── BoardsPage.jsx
│       │   ├── BoardDetailPage.jsx
│       │   ├── PagesPage.jsx
│       │   ├── PageDetailPage.jsx
│       │   ├── AutomationsPage.jsx
│       │   ├── AnalyticsPage.jsx
│       │   ├── AIQueryPage.jsx
│       │   ├── LinkedInPage.jsx
│       │   ├── TeamSettingsPage.jsx
│       │   └── AdminPage.jsx
│       ├── components/         # Reusable UI components
│       │   ├── Layout.jsx      # App shell with sidebar and nav
│       │   ├── AuthGuard.jsx   # Redirects unauthenticated users to /login
│       │   ├── KanbanBoard.jsx # Drag-and-drop kanban implementation
│       │   ├── PipelineView.jsx
│       │   ├── DealCard.jsx
│       │   ├── ContactCard.jsx
│       │   ├── ActivityFeed.jsx
│       │   ├── AutomationBuilder.jsx
│       │   ├── RichTextEditor.jsx
│       │   ├── AIQueryBar.jsx
│       │   ├── LinkedInPanel.jsx
│       │   ├── TeamSelector.jsx
│       │   └── ui/             # Generic UI primitives (shadcn/radix wrappers)
│       │       ├── avatar.jsx, badge.jsx, button.jsx, card.jsx
│       │       ├── dialog.jsx, dropdown-menu.jsx, input.jsx
│       │       ├── label.jsx, select.jsx, sheet.jsx, skeleton.jsx
│       │       ├── switch.jsx, table.jsx, tabs.jsx, textarea.jsx
│       ├── lib/                # Shared utilities (utils.js — clsx/tw merge helper)
│       ├── test/               # Vitest setup file (setup.js)
│       └── __tests__/          # Component/hook tests
│
├── mobile/                     # React Native app (no tests)
│   └── src/
│       ├── screens/            # Screen components
│       │   ├── HomeScreen.jsx
│       │   ├── ContactsScreen.jsx
│       │   ├── DealsScreen.jsx
│       │   ├── ActivityScreen.jsx
│       │   └── AIQueryScreen.jsx
│       ├── navigation/         # AppNavigator.jsx (React Navigation)
│       └── api/                # client.js (mirrors frontend API client)
│
├── alembic/                    # Database migrations
│   ├── env.py                  # Alembic env (points to backend.database)
│   └── versions/
│       └── 0001_initial.py     # Initial full schema migration
│
├── deploy/                     # Deployment configuration
│   ├── Dockerfile              # Backend image (FastAPI + uvicorn)
│   ├── Dockerfile.worker       # Celery worker image
│   ├── docker-compose.yml      # Full local dev stack (postgres, redis, backend, worker, frontend)
│   ├── entrypoint.sh           # Container entrypoint (runs migrations then uvicorn)
│   └── .dockerignore
│
├── terraform/                  # AWS infrastructure as code
│   ├── main.tf                 # Root module, wires sub-modules together
│   ├── variables.tf / outputs.tf / terraform.tfvars
│   └── modules/
│       ├── alb/                # Application Load Balancer
│       ├── cloudfront/         # CDN for frontend static assets
│       ├── ecs/                # ECS Fargate service (API)
│       ├── ecs_worker/         # ECS Fargate service (Celery worker)
│       ├── elasticache/        # Redis (ElastiCache)
│       ├── iam/                # IAM roles and policies
│       ├── networking/         # VPC, subnets, security groups
│       ├── rds/                # PostgreSQL (RDS)
│       └── secrets/            # Secrets Manager
│
├── specs/                      # Product/feature specifications (YAML + JSON)
│   ├── nexus-crm-spec.yaml
│   └── openapi-spec.json
├── docs/                       # Developer documentation
│   └── RUNBOOK.md
├── .github/workflows/
│   └── deploy.yml              # CI/CD pipeline
├── .env.example                # Required environment variables template
├── alembic.ini                 # Alembic config
├── pyproject.toml              # Python tooling config + pytest settings
├── Makefile                    # Dev task shortcuts (test, lint, format, migrate, seed)
└── test_nexus.db               # SQLite file created at test/dev runtime
```

---

## Key Files and Their Purpose

| File | Purpose |
|---|---|
| `backend/api/main.py` | FastAPI app definition, middleware registration, router mounting, health/metrics endpoints |
| `backend/models.py` | Single file with all SQLAlchemy ORM models — edit here when adding columns or tables |
| `backend/config.py` | All environment-driven config via Pydantic `Settings`; `settings` singleton via `lru_cache` |
| `backend/database.py` | Engine and session factory; `DATABASE_URL` env var swapped to SQLite during tests |
| `backend/services/_crm.py` | Shared internal utilities consumed by all service classes: pagination, role checks, SQL helpers |
| `backend/auth/security.py` | `create_access_token`, `get_current_user` FastAPI dependency, `hash_password`, `encrypt_linkedin_token` |
| `backend/utils/sql_validator.py` | Validates and sanitises AI-generated SQL before execution |
| `frontend/src/api/client.js` | The single Axios instance; add global request/response interceptors here |
| `frontend/src/App.jsx` | All route definitions live here; add new routes by importing a page and adding a `<Route>` |
| `frontend/src/store/useAuthStore.js` | Source of truth for the JWT token; read by `client.js` interceptor |
| `frontend/src/__tests__/test-utils.jsx` | `renderWithProviders` helper used by all frontend tests |
| `deploy/docker-compose.yml` | Full local dev stack definition — postgres, redis, backend, worker, frontend |
| `Makefile` | Primary developer interface: `make test`, `make lint`, `make dev`, `make migrate`, `make seed` |

---

## Module Boundaries

The backend enforces a strict layered dependency direction. Never import in the reverse direction.

```
routes/ --> services/ --> models.py + schemas/
                 |
                 +--> math/    (pure functions, no DB or HTTP)
                 +--> storage/ (file I/O abstraction)
                 +--> utils/   (cross-cutting, no business logic)

workers/ --> services/        (same direction as routes)
          --> workers/celery_app.py

auth/ --> models.py (User model only)
       --> config.py

frontend/src/hooks/ --> frontend/src/api/
frontend/src/context/ --> frontend/src/store/ + frontend/src/hooks/
frontend/src/pages/ --> frontend/src/hooks/ + frontend/src/store/ + frontend/src/components/
```

**Rules to maintain:**
- `routes/` must not import from other `routes/` files
- `services/` must not import from `routes/`
- `models.py` must not import from `services/` or `routes/`
- `math/` must remain pure Python with zero database or HTTP dependencies
- Frontend `api/` modules must not import from `hooks/`, `store/`, or `context/`

---

## Notable Patterns

### Schema Separation

Request/response Pydantic models in `backend/schemas/` are separate from ORM models in `backend/models.py`. Response schemas include computed fields (e.g., `DealResponse.pipeline_name`, `owner_name`, `is_rotting`, `days_in_stage`) that are resolved by SQL joins in service query methods — not by loading ORM relationships.

### Service Class Pattern

Every service receives `(db: AsyncSession, current_user: User)` at construction. All org-scope filtering, role checks, and pagination logic live in the service, not in route handlers. Routes are responsible only for input validation and response shaping.

```python
# Route (thin)
async def list_deals(...) -> DealListResponse:
    return await DealService(db, current_user).list_deals(...)

# Service (fat)
class DealService:
    def __init__(self, db: AsyncSession, current_user: User): ...
    async def list_deals(self, **filters) -> DealListResponse: ...
```

### Automation Trigger Pattern

After any mutating service operation that could trigger automations, the route fires `await fire_trigger(trigger_type, payload, org_id)` via FastAPI `BackgroundTasks`. This queries active automations and dispatches Celery tasks without blocking the HTTP response.

### Dual-DB Dialect Support

`backend/models.py` uses `JSONVariant` and `StringList` type aliases that resolve to `JSON`/`JSONB` and `JSON`/`ARRAY(Text)` depending on the dialect. This keeps the same model file working for both SQLite (tests/dev) and PostgreSQL (prod):

```python
JSONVariant = JSON().with_variant(JSONB, "postgresql")
StringList = MutableList.as_mutable(JSON()).with_variant(ARRAY(Text()), "postgresql")
```

### Frontend Query Key Convention

TanStack Query keys follow `[resource, params]`:
```js
queryKey: ['deals', { pipeline_id, page }]
queryKey: ['contacts', { search, page }]
queryKey: ['auth', 'me']
```
Invalidate with `queryClient.invalidateQueries({ queryKey: ['deals'] })` to bust all deal queries.

### `ui/` Component Layer

`frontend/src/components/ui/` contains thin wrappers around Radix UI primitives styled with Tailwind. These are generic, stateless, and should not import from `hooks/`, `store/`, or `api/`. Business-aware components live in `frontend/src/components/` (one level up).

---

## Where to Add New Code

**New domain resource (e.g., "notes"):**
1. Add ORM model to `backend/models.py`
2. Create `backend/schemas/notes.py` with Create/Update/Response Pydantic models
3. Create `backend/services/notes.py` with a `NoteService` class
4. Create `backend/api/routes/notes.py` with an `APIRouter`
5. Register router in `backend/api/main.py`
6. Create `frontend/src/api/notes.js` with API functions
7. Create `frontend/src/hooks/useNotes.js` as a TanStack Query wrapper
8. Create `frontend/src/pages/NotesPage.jsx`
9. Add route to `frontend/src/App.jsx`
10. Generate Alembic migration: `alembic revision --autogenerate -m "add_notes"`

**New Celery task:**
- Add task function to an existing file in `backend/workers/` or create a new one
- Decorate with `@celery_app.task(bind=True, max_retries=3, name="domain.action")`
- Use `asyncio.run()` or a sync session to bridge async DB code inside the task

**New middleware:**
- Add class to `backend/api/middleware.py`
- Register with `app.add_middleware(...)` in `backend/api/main.py`
- Middleware is applied in reverse registration order (last registered runs first on request)

**New Zustand store:**
- Add file `frontend/src/store/useXxxStore.js` using `create()` from `zustand`
- Persist to localStorage only if the state must survive page reloads

**New math/scoring function:**
- Add to `backend/math/` as a pure Python module with no imports from `backend.models` or `backend.services`

**New shadcn/Radix primitive:**
- Add wrapper component to `frontend/src/components/ui/`
- Keep it stateless; all behavior lives in the calling page or component

---

## Special Directories

**`.venv/`:**
- Purpose: Python virtual environment
- Generated: Yes
- Committed: No

**`alembic/versions/`:**
- Purpose: Database migration scripts
- Generated: Via `alembic revision --autogenerate`
- Committed: Yes — every migration file is committed

**`frontend/node_modules/`:**
- Purpose: npm packages
- Generated: Yes
- Committed: No

**`terraform/`:**
- Purpose: AWS infrastructure definitions (ECS, RDS, ElastiCache, ALB, CloudFront)
- Generated: No (hand-authored)
- Committed: Yes

**`test_nexus.db`:**
- Purpose: SQLite database file created during local testing (test suite target)
- Generated: Yes (at runtime by the test suite)
- Committed: No (should be in `.gitignore`)

**`specs/`:**
- Purpose: Product feature specifications and OpenAPI schema
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-03-26*
