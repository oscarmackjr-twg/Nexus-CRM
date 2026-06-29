# Nexus CRM

**A Private Equity–focused CRM for deal teams.** Nexus CRM tracks companies, contacts, deals, counterparty (investor) pipelines, and capital funding commitments through the full investment lifecycle — from initial outreach through diligence, NDA, LOI, and close.

Built for PE deal advisory and capital markets firms (e.g. TWG Asia), the core workflow is tracking every counterparty touchpoint across every live deal: who signed the NDA, who got the VDR, who gave feedback, and what's next — without leaving the CRM.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python, FastAPI, SQLAlchemy 2.0 (async), Pydantic |
| **Database** | PostgreSQL (via Alembic migrations) |
| **Cache / Queue** | Redis + Celery (background workers) |
| **Auth** | JWT (access + refresh tokens), role-based access control |
| **Frontend** | React 18, Vite, TanStack Query, Zustand, React Router, React Hook Form + Zod |
| **UI** | Tailwind CSS, Radix UI primitives, Lucide icons, Recharts, TWG Global branding |
| **Local dev** | Docker Compose (`make dev`) |
| **Cloud** | AWS (Terraform IaC) with warm Azure failover; GitHub Actions CI/CD |

---

## Project Structure

```
Nexus-CRM/
├── backend/              FastAPI application
│   ├── api/
│   │   ├── main.py       App entrypoint — mounts routers under /api/v1
│   │   ├── routes/       Endpoint modules (auth, contacts, deals, admin, …)
│   │   ├── dependencies.py
│   │   └── middleware.py
│   ├── auth/             JWT auth & RBAC
│   ├── schemas/          Pydantic request/response models
│   ├── services/         Business logic / data access
│   ├── workers/          Celery background tasks
│   ├── models.py         SQLAlchemy ORM models
│   ├── database.py       Async DB session
│   ├── config.py         Settings
│   ├── seed_data.py      Demo data seeding
│   └── tests/            pytest suite (coverage gate: 85%)
├── frontend/             React + Vite SPA
│   └── src/
│       ├── api/          API clients (axios)
│       ├── pages/        Route pages (Dashboard, Deals, Contacts, Admin, …)
│       ├── components/   Shared UI (DataGrid, FieldRow, RefSelect, ui/ primitives)
│       ├── hooks/        Custom hooks (useRefData, …)
│       └── store/        Zustand state
├── alembic/              Database migrations
├── deploy/              Docker Compose + Dockerfiles + entrypoint
├── terraform/           AWS infra (bootstrap, modules, environments/staging|prod)
└── Makefile             Dev, test, migrate, seed, and Terraform commands
```

---

## Getting Started

### Prerequisites
- Docker & Docker Compose
- `make`

### Run locally

```bash
# Start the full stack (backend, frontend, PostgreSQL, Redis) with hot reload
make dev

# Apply database migrations
make migrate

# Seed demo data (or set RUN_SEED_DATA=true in .env)
make seed
```

The backend serves its API under `/api/v1`; the frontend runs on Vite's dev server.

### Demo credentials
```
admin@demo.local / password123
```
(Seeded when `RUN_SEED_DATA=true` is set in `.env`.)

### Common commands

```bash
make test          # Run backend pytest suite with coverage (fails under 85%)
make lint          # ruff + mypy
make format        # ruff format + black
make docker-up     # Start stack detached
make docker-down   # Stop stack and remove volumes
```

Frontend (from `frontend/`):
```bash
npm run dev        # Vite dev server
npm run build      # Production build
npm run test       # Vitest
```

---

## Current Functionality

### Core CRM
- **Companies** — industry, size, website, country, plus a full PE Blueprint expansion (financials, investment preferences, self-referencing parent company).
- **Contacts** — lifecycle stages, lead scoring, owner assignment, coverage persons (M2M), PE Blueprint fields, and LinkedIn import.
- **Deals** — pipeline with stages, kanban view, win/loss tracking, deal team (M2M), financial metrics with currencies, and date milestones.
- **Deal Counterparties** — per-deal investor pipeline tracking (NDA → signed → VDR → feedback → next step), the central PE workflow.
- **Deal Funding** — capital commitment tracking with provider company and status.
- **Funds** — Fund CRUD with inline-create on the deal detail page.
- **Tasks / Boards** — Kanban task boards with columns and due dates.
- **Pipelines, Teams, Orgs** — pipeline configuration, team management, multi-tenant org scoping.

### Platform
- **Multi-tenant, org-scoped** backend.
- **JWT authentication** with access/refresh tokens.
- **Role-based access control** (super_admin, org_admin, team_manager, member).
- **Admin-configurable reference data** — 12 categories, 96+ seed values, soft-delete, org-scoped, surfaced via a `RefSelect` component and `useRefData` hook so no dropdown lists are hardcoded.
- **AI deal scoring & proactive suggestions**, plus an AI query endpoint.
- **Analytics & automations** endpoints (some analytics endpoints are stubs — see Known Gaps).
- **LinkedIn contact import**, **webhooks**, and **page** configuration endpoints.

### UI / Branding (v1.1)
- TWG Global brand foundation — `#1a3868` navy palette, Gotham typography, brand tokens applied globally; light theme.
- Branded login page with real logo, staging banner, and backend health indicator.
- White left sidebar with grouped navigation (DEALS / TOOLS / ADMIN) and navy active highlighting.
- Compact Salesforce-density data grids (shared `DataGrid` + pagination, sortable columns, status filters).
- Polished detail pages with shared `FieldRow`, navy underline tabs, and consistent card headers.

### Admin & Access Control (v1.3 — in progress)
- Admin UI for **user management** and **group management** (`AdminUsersPage`, `AdminGroupsPage`).
- Group/role/authorship schema with a four-role model and per-object `created_by` / `updated_by` tracking.

---

## Expected / Planned Functionality

### v1.1 UI Professionalism (remaining)
- Complete Contact and Company detail screens and API label resolution for all PE fields.
- Deal detail screen + edit form covering all new PE fields, with Fund selector on the deal edit form.

### v1.2 Cloud Deployment (in progress)
- ✅ AWS infrastructure via Terraform — networking, RDS PostgreSQL 17, ElastiCache Redis, Secrets Manager, IAM, RDS Proxy, ECR.
- ⬜ Azure warm failover (PostgreSQL read replica + idle ACI containers, manual cutover).
- ⬜ GitHub Actions CI/CD — build → push to ECR → deploy to ECS on merge to `main`.
- ⬜ Secrets injected from AWS Secrets Manager into ECS task definitions.
- ⬜ HTTPS via ACM + ALB + Route 53 DNS.
- ⬜ Multi-environment (staging + prod) support, with Alembic migrations baked into the deploy pipeline.

### v1.3 Access Control & Audit Trails (current milestone)
- **Group-based access scoping** — users belong to exactly one group; Calls, Notes, and Deals are group-scoped, while Contacts and Companies remain system-wide.
- **Call and Note** as new first-class, group-scoped entities with full CRUD.
- **Four-role model** — Regular User, Supervisor, Principal, Admin:
  - *Supervisor* — full read + edit (not delete) of group members' Calls, Notes, and Deals.
  - *Principal* — cross-group read access to all CRM data plus aggregate reports.
  - *Admin* — user management, group creation, and member/supervisor/principal assignment.
- **Full modification history** — per-table `_history` shadow tables for version preservation and recovery.
- **Principal reports** — activity by group, deal pipeline by group, and user activity.

---

## Known Gaps / Out of Scope

- Contact/Company detail UIs and the Deal detail screen do not yet display every expanded PE field.
- Analytics stub endpoints (pipeline-velocity, forecast, leaderboard) remain stubs.
- Data import/migration from the PE Blueprint template is deferred until the data model stabilizes.
- No database-layer row-level security — access is enforced in the application service layer.
- No multi-currency FX conversion (amounts stored with a currency code only).
- Audit history is stored plaintext (no field-level encryption); permission changes apply on the next request (no real-time notifications).

---

## Constraints

- **Tech stack is fixed** — Python/FastAPI backend, React/Vite frontend; no framework changes.
- **Database** — PostgreSQL via SQLAlchemy 2.0 async; all new entities use Alembic migrations.
- **Backward compatibility** — new API fields are additive; existing consumers must not break.
- **Docker** — everything runs in Docker Compose via `make dev`; no native dependencies.

---

*Nexus CRM is developed using the GSD planning workflow; see `.planning/PROJECT.md` for the authoritative roadmap and decision log.*
