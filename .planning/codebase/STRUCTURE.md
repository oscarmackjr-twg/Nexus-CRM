---
updated: 2026-04-06
focus: arch
---

# Codebase Structure

**Analysis Date:** 2026-04-06

## Directory Layout

```
Nexus-CRM/
├── alembic/                    # Database migration runner config
│   └── versions/               # Sequential migration scripts (0002–0011)
├── backend/                    # Python FastAPI application (monorepo package)
│   ├── api/                    # HTTP layer
│   │   ├── main.py             # FastAPI app factory, lifespan, middleware, router registration
│   │   └── routes/             # One router module per domain
│   ├── models.py               # All SQLAlchemy ORM models (single file, ~700 lines)
│   ├── schemas/                # Pydantic v2 request/response schemas per domain
│   ├── services/               # Business logic service classes per domain
│   ├── seed_data.py            # Development seed data script
│   └── tests/                  # Pytest test suite
├── deploy/                     # Runtime deployment artifacts
│   └── entrypoint.sh           # Container start script (migration + uvicorn)
├── frontend/                   # React SPA (Vite)
│   ├── index.html              # HTML entry point
│   ├── vite.config.js          # Vite + Vitest config; dev proxy to backend:8000
│   ├── tailwind.config.js      # Tailwind CSS config
│   └── src/
│       ├── api/                # Axios API client modules per domain
│       ├── assets/             # Static assets (logo, images)
│       ├── components/         # Shared React components
│       ├── hooks/              # Custom React hooks
│       ├── lib/                # Pure utility functions and constants
│       ├── pages/              # Page-level React components (route targets)
│       ├── store/              # Zustand state stores
│       ├── __tests__/          # Frontend unit/component tests
│       └── styles.css          # Global CSS (Tailwind base)
├── terraform/                  # Infrastructure-as-code (Terraform)
│   ├── bootstrap/              # One-time state bucket + KMS key setup
│   ├── environments/
│   │   ├── staging/            # Staging environment root module
│   │   └── prod/               # Production environment root module
│   └── modules/                # Reusable Terraform modules
│       ├── networking/         # VPC, subnets, IGW, NAT, route tables, security groups
│       ├── rds/                # RDS PostgreSQL instance + parameter group
│       ├── rds_proxy/          # AWS RDS Proxy + IAM role for Secrets Manager
│       ├── elasticache/        # ElastiCache Redis replication group
│       ├── secrets/            # AWS Secrets Manager shell resources
│       └── iam/                # ECS execution/task roles, GitHub OIDC role
├── .planning/                  # Project planning and GSD docs (not shipped)
├── Makefile                    # Developer workflow shortcuts
└── .gitignore
```

## Directory Purposes

**`backend/api/`:**
- Purpose: HTTP entry point — FastAPI app, middleware, router mounting
- Contains: `main.py` (app factory), `routes/` (19 domain router files), `middleware` (imported package — not committed individually but provides `AuditLogMiddleware`, `OrgScopingMiddleware`, `RequestIDMiddleware`, `RequestLoggingMiddleware`, `SecurityHeadersMiddleware`), `dependencies` (imported package — provides `get_current_user`, `get_db`, `require_role`)
- Key files: `backend/api/main.py`

**`backend/api/routes/`:**
- Purpose: One FastAPI `APIRouter` per domain; thin layer that validates inputs and delegates to services
- Contains: `admin.py`, `ai_query.py`, `analytics.py`, `auth.py`, `automations.py`, `boards.py`, `companies.py`, `contacts.py`, `counterparties.py`, `deals.py`, `funding.py`, `funds.py`, `linkedin.py`, `orgs.py`, `pages.py`, `pipelines.py`, `tasks.py`, `teams.py`, `webhooks.py`
- Note: `auth.py` is the exception — it contains non-trivial auth logic directly rather than delegating to a service

**`backend/models.py`:**
- Purpose: Single file containing all SQLAlchemy ORM model classes (~700 lines)
- Contains: `Organization`, `Team`, `User`, `ContactCoveragePerson`, `Contact`, `Company`, `Pipeline`, `PipelineStage`, `Fund`, `DealTeamMember`, `DealCounterparty`, `DealFunding`, `Deal`, `DealActivity`, `Board`, `BoardColumn`, `Task`, `Page`, `Automation`, `AutomationRun`, `AIQuery`, `RefData`

**`backend/schemas/`:**
- Purpose: Pydantic v2 models for API request validation and response serialisation
- Contains: `companies.py`, `contacts.py`, `counterparties.py`, `deals.py`, `funding.py`, `funds.py`, `ref_data.py`
- Pattern: `{Entity}Create`, `{Entity}Update`, `{Entity}Response` per domain

**`backend/services/`:**
- Purpose: Business logic; all DB queries and mutations live here
- Contains: `companies.py`, `contacts.py`, `counterparties.py`, `deals.py`, `funding.py`, `funds.py`, `ref_data.py`
- Pattern: Service class with `__init__(self, db: AsyncSession, current_user: User)`, async methods

**`backend/tests/`:**
- Purpose: Pytest test suite
- Contains: `conftest.py` (fixtures, test DB setup), `test_deals_pe.py`, `test_funds.py`, `test_ref_data.py`
- Key files: `backend/tests/conftest.py`

**`alembic/versions/`:**
- Purpose: Database migration history
- Contains: Numbered scripts `0002_pe_ref_data.py` through `0011_deal_funding.py`
- Pattern: Sequential integers as prefix; descriptive name suffix

**`deploy/`:**
- Purpose: Runtime deployment scripts
- Contains: `entrypoint.sh` only — run at container start
- Generated: No. Committed: Yes.

**`frontend/src/api/`:**
- Purpose: Axios client wrappers — one module per backend domain
- Contains: `companies.js`, `contacts.js`, `counterparties.js`, `funding.js`, `refData.js`, `users.js`
- Pattern: Named exports of async functions that call a shared `client` (Axios instance): `export const getCompanies = async (params) => (await client.get('/companies', { params })).data`

**`frontend/src/components/`:**
- Purpose: Shared/reusable React components
- Contains: `Layout.jsx` (sidebar + nav shell), `RefSelect.jsx` (ref-data dropdown), `StagingBanner.jsx`, `AIQueryBar` (imported in Layout, not found as separate file — may be inline or missing)

**`frontend/src/hooks/`:**
- Purpose: Custom React hooks
- Contains: `useRefData.js` (React Query wrapper for ref data by category)

**`frontend/src/lib/`:**
- Purpose: Pure utilities and constants
- Contains: `refCategories.js` (list of valid ref-data category strings)

**`frontend/src/pages/`:**
- Purpose: Route-level page components mounted by React Router
- Contains: `LoginPage.jsx`, `DashboardPage.jsx`, `ContactDetailPage.jsx`, `CompanyDetailPage.jsx`, `DealDetailPage.jsx`, `AdminPage.jsx`

**`frontend/src/store/`:**
- Purpose: Zustand global state
- Contains: `useUIStore.js` — sidebar collapsed state, persisted to `localStorage`

**`terraform/modules/`:**
- Purpose: Reusable, parameterised Terraform modules — not deployed directly
- Each module follows the standard pattern: `main.tf`, `variables.tf`, `outputs.tf`

**`terraform/environments/staging/` and `terraform/environments/prod/`:**
- Purpose: Environment root modules — call all child modules with environment-specific variable values
- Both environments have identical module compositions; prod differs via variable values (multi-AZ, deletion protection)

**`terraform/bootstrap/`:**
- Purpose: One-time setup of Terraform remote state infrastructure (S3 + KMS)
- State: Managed locally (`.gitignore` covers bootstrap state files)

## Key File Locations

**Entry Points:**
- `backend/api/main.py` — FastAPI application factory and startup
- `deploy/entrypoint.sh` — Container start script
- `frontend/index.html` — SPA HTML shell
- `frontend/vite.config.js` — Frontend build and dev server config

**Configuration:**
- `backend/config` — Python settings module (imported as `from backend.config import settings`)
- `terraform/environments/staging/main.tf` — Staging infrastructure root
- `terraform/environments/prod/main.tf` — Production infrastructure root
- `terraform/bootstrap/main.tf` — State bucket bootstrap

**Core Business Logic:**
- `backend/models.py` — All ORM models
- `backend/services/deals.py` — Deal service (largest service, ~25KB)
- `backend/services/contacts.py` — Contact service (~16KB)
- `backend/services/companies.py` — Company service (~15KB)
- `backend/api/routes/auth.py` — Auth, token management, LinkedIn OAuth (~18KB)

**Infrastructure:**
- `terraform/modules/networking/main.tf` — VPC, subnets, security groups
- `terraform/modules/rds/main.tf` — RDS PostgreSQL instance
- `terraform/modules/rds_proxy/main.tf` — RDS Proxy
- `terraform/modules/elasticache/main.tf` — Redis cluster
- `terraform/modules/iam/main.tf` — ECS roles, GitHub OIDC role
- `terraform/modules/secrets/main.tf` — Secrets Manager shell resources

**Testing:**
- `backend/tests/conftest.py` — Pytest fixtures and test DB
- `backend/tests/test_deals_pe.py` — Deal PE fields tests
- `frontend/src/__tests__/` — React component tests (Layout, LoginPage, RefSelect)

**Developer Workflow:**
- `Makefile` — `make dev`, `make test`, `make lint`, `make migrate`, `make seed`, `make tf-*`

## Naming Conventions

**Files:**
- Backend Python: `snake_case.py` — matches domain name (e.g., `companies.py`, `ref_data.py`)
- Frontend JS/JSX: `camelCase.js` for API/hooks/lib; `PascalCase.jsx` for React components and pages
- Terraform: `main.tf`, `variables.tf`, `outputs.tf` (standard)
- Alembic migrations: `{NNNN}_{description}.py` with zero-padded sequential number

**Backend Modules:**
- Route files: domain noun, singular or plural as appropriate (e.g., `contacts.py`, `auth.py`)
- Schema classes: `{Entity}Create`, `{Entity}Update`, `{Entity}Response`
- Service classes: `{Entity}Service`

**Frontend Modules:**
- API modules: domain noun, camelCase (e.g., `refData.js`, `companies.js`)
- Hooks: `use{Name}.js` (e.g., `useRefData.js`, `useAuth.js`)
- Stores: `use{Name}Store.js` (e.g., `useUIStore.js`)

## Where to Add New Code

**New API domain (backend):**
1. Add ORM model class to `backend/models.py`
2. Create Alembic migration: `alembic/versions/{NNNN}_{description}.py`
3. Create Pydantic schemas: `backend/schemas/{domain}.py`
4. Create service class: `backend/services/{domain}.py`
5. Create FastAPI router: `backend/api/routes/{domain}.py`
6. Register router in `backend/api/main.py` in the `for router in [...]` block

**New frontend page:**
1. Create page component: `frontend/src/pages/{Name}Page.jsx`
2. Add route to React Router config (location inferred — likely in main app entry or Layout)
3. Add nav entry to `navGroups` in `frontend/src/components/Layout.jsx` if it needs sidebar navigation
4. Add API client functions: `frontend/src/api/{domain}.js`

**New Terraform resource:**
- Add to the appropriate module under `terraform/modules/`
- Or add inline to the environment root (`terraform/environments/staging/main.tf` and `prod/main.tf`) for resources not worth modularising (ECR repositories follow this pattern)

**New Alembic migration:**
- Use next sequential number: current highest is `0011_deal_funding.py`
- Filename: `alembic/versions/{NNNN}_{description}.py`

**New RefData category:**
- Add category string to `frontend/src/lib/refCategories.js`
- Add seed data entries to `backend/seed_data.py`
- No migration needed — `RefData` table handles all categories via `category` column

**Utilities:**
- Shared backend helpers: `backend/utils/` (imported as `backend.utils.*`)
- Shared frontend helpers: `frontend/src/lib/`

## Special Directories

**`.planning/`:**
- Purpose: GSD project planning docs, phase plans, roadmap, codebase analysis
- Generated: No (human + AI-authored)
- Committed: Yes

**`alembic/versions/`:**
- Purpose: Migration history — every schema change tracked here
- Generated: Partially (Alembic generates boilerplate; developer writes upgrade/downgrade SQL)
- Committed: Yes — required for deployment

**`frontend/dist/` (gitignored):**
- Purpose: Vite production build output; deployed to S3
- Generated: Yes
- Committed: No

**`terraform/environments/*/.terraform/` (gitignored):**
- Purpose: Terraform provider cache and module downloads
- Generated: Yes (`terraform init`)
- Committed: No

**`terraform/environments/*/terraform.tfstate*` (gitignored):**
- Purpose: Terraform state (stored remotely in S3 after init)
- Generated: Yes
- Committed: No

---

*Structure analysis: 2026-04-06*
