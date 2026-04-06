---
updated: 2026-04-06
focus: tech
---

# Technology Stack

**Analysis Date:** 2026-04-06

## Languages

**Primary:**
- Python 3.12 — Backend API, Celery worker, database migrations. Docker base image `python:3.12-slim`.
- JavaScript (ES2022+, JSX) — Frontend SPA. No TypeScript in use.

**Infrastructure:**
- HCL (Terraform) — All cloud infrastructure definitions in `terraform/`.

## Runtime

**Backend:**
- CPython 3.12 — confirmed via Docker base image reference (`python:3.12-slim`) in planning research.
- Uvicorn — ASGI server. Production entry point in `deploy/entrypoint.sh`: `exec uvicorn backend.api.main:app --host 0.0.0.0 --port 8000`.

**Frontend:**
- Node.js 22 — build-time only (Vite bundle). Docker build stage: `node:22-alpine`.
- nginx 1.27-alpine — production static file server serving the compiled Vite dist.

**Package Manager:**
- Python: pip (assumed). No `requirements.txt` committed — managed inside Docker image layer.
- Node: npm (assumed). `package.json` not committed. `frontend/node_modules/` is gitignored.
- Lockfiles: not tracked in repository.

## Frameworks

### Backend

**Core:**
- FastAPI — async REST API framework. Entry point: `backend/api/main.py`. All routers mounted at `/api/v1` prefix.
- SQLAlchemy 2.x (async ORM) — `AsyncSession`, fully typed `Mapped`/`mapped_column` column definitions throughout `backend/models.py`.
- Pydantic v2 — request/response schema validation. `model_validate()` call pattern confirms v2. Schema files in `backend/schemas/`.
- Alembic — database migration management. Migrations in `alembic/versions/` (11 revisions: 0001–0011).

**Async / Worker:**
- Celery — async task queue. Worker entrypoint: `backend/workers/celery_app.py` (not tracked in git). Lifecycle managed in `backend/api/main.py` lifespan handler.
- redis-py (asyncio) — async Redis client (`redis.asyncio`). Used for JWT token store, rate limiting, and as Celery broker.

**Security / Auth:**
- Custom JWT implementation — `backend/auth/security.py` (not tracked). `create_access_token`, `create_refresh_token`, `verify_token`, `get_current_user`, `require_org_admin` all imported from there.
- bcrypt / passlib — password hashing via `hash_password` / `verify_password`.
- cryptography — LinkedIn access token encryption via `encrypt_linkedin_token`.
- slowapi — rate limiting middleware. Conditionally imported in `backend/api/main.py` with graceful fallback if module absent.

**HTTP Client:**
- httpx — async HTTP client. Used in `backend/api/routes/auth.py` for LinkedIn OAuth token exchange and profile API calls.

**Observability:**
- Prometheus — metrics scrape endpoint at `/metrics` (`backend/api/main.py`). Gated by `METRICS_API_KEY` in production.
- Structured logging — `backend/utils/structured_logging.py` (not tracked). Called from app lifespan via `setup_logging(settings)`.
- OpenTelemetry — `backend/utils/telemetry.py` (not tracked). Called via `setup_telemetry(app, settings)`.

**Other Backend:**
- boto3 — AWS SDK. Conditionally imported in `backend/api/main.py` for S3 readiness check when `STORAGE_TYPE == "s3"`.

### Frontend

**Core:**
- React 18+ — UI framework. All component files use `.jsx` extension.
- react-router-dom — client-side routing. `NavLink`, `Outlet`, `useNavigate`, `useParams` used across components.
- @tanstack/react-query — server state / data fetching. `useQuery`, `useMutation`, `useQueryClient` used on every page.
- Zustand — lightweight client state. Single store at `frontend/src/store/useUIStore.js` (sidebar collapsed state).

**Forms:**
- react-hook-form — form state management. Used in `frontend/src/pages/LoginPage.jsx` and `frontend/src/pages/ContactDetailPage.jsx`.
- zod — schema validation. Used with `@hookform/resolvers/zod`.

**UI Components:**
- Tailwind CSS — utility-first CSS framework. Config: `frontend/tailwind.config.js`. Dark mode via `class` strategy. CSS variables used for all brand color tokens.
- shadcn/ui — component library built on Radix UI primitives + Tailwind. Components referenced from `frontend/src/components/ui/` (badge, button, card, dialog, input, label, select, skeleton, switch, table, tabs, textarea). Source files not tracked in git.
- Lucide React — SVG icon library (`lucide-react`). Used in `frontend/src/components/Layout.jsx` and all page components.
- sonner — toast notifications. `toast.error()` / `toast.success()` used site-wide.
- recharts — charting. `PieChart`, `ResponsiveContainer`, `Cell`, `Tooltip` used in `frontend/src/pages/DashboardPage.jsx`.

**Build:**
- Vite — dev server and production bundler. Config: `frontend/vite.config.js`. Dev server port 5173. Path alias: `@` → `./src`. Proxy: `/api` and `/health` → `http://backend:8000`.
- @vitejs/plugin-react — Vite JSX/React Fast Refresh plugin.

**Testing:**
- Vitest — test runner (configured inline in `frontend/vite.config.js` under `test:`). jsdom environment, globals enabled.
- @testing-library/react — component rendering and querying.
- @testing-library/user-event — user interaction simulation.

## Build / Dev Tooling

**Backend Code Quality:**
- ruff — linting and formatting. Invoked via `make lint` and `make format`.
- mypy — static type checking. `mypy backend/ --ignore-missing-imports`.
- black — secondary Python formatter (invoked alongside ruff in `make format`).

**Backend Testing:**
- pytest — test runner. Coverage threshold: 85% (`--cov-fail-under=85`). Tests in `backend/tests/`.
- pytest-asyncio — async test fixtures. Used throughout `backend/tests/conftest.py`.
- pytest-cov — coverage reporting with HTML output.
- httpx ASGITransport — in-process test client for FastAPI (no live server required).

**Infrastructure:**
- Terraform >= 1.10, < 2.0 — IaC tooling. Workspace structure in `terraform/`.
- hashicorp/aws provider ~> 6.0
- hashicorp/random provider ~> 3.6 — RDS password generation
- Docker Compose — local dev environment (`deploy/docker-compose.yml`, gitignored). Invoked via `make dev` / `make docker-up`.
- GNU Make — developer task runner. `Makefile` at project root.

## Database Technologies

**Production database:**
- PostgreSQL 17 — AWS RDS (`db.t4g.medium` staging / `db.t4g.large` prod). Parameter group family: `postgres17`. Logical replication enabled (`rds.logical_replication = 1`).
- asyncpg — async PostgreSQL driver. Connection URL: `postgresql+asyncpg://`.
- psycopg (v3) — sync driver for Alembic migrations only. Auto-derived URL in `deploy/entrypoint.sh`: `postgresql+asyncpg://` → `postgresql+psycopg://`.
- RDS Proxy — connection pooling layer between ECS tasks and RDS. TLS required. Auth via Secrets Manager.

**Test database:**
- SQLite + aiosqlite — in-process async SQLite for tests. Set in `backend/tests/conftest.py`: `sqlite+aiosqlite:///./test_nexus.db`.

**Caching / Session / Broker:**
- Redis 7.1 — AWS ElastiCache replication group. Uses: JWT refresh token storage (`auth:refresh:{token}`), access token blacklist (`auth:blacklist:{token}`), rate limiting (slowapi), Celery broker and result backend. Encryption: at-rest + in-transit (TLS required).

## Infrastructure / Cloud

**IaC:** Terraform >= 1.10, < 2.0

**Primary cloud:** AWS, region `ap-southeast-1` (Singapore)

**AWS services provisioned (Phase 13 — complete):**
- VPC, subnets, NAT gateway, Internet Gateway, security groups — `terraform/modules/networking/`
- RDS PostgreSQL 17 (`db.t4g.medium` / `db.t4g.large`) — `terraform/modules/rds/`
- RDS Proxy — `terraform/modules/rds_proxy/`
- ElastiCache Redis 7.1 replication group — `terraform/modules/elasticache/`
- Secrets Manager (shell resources only, values populated out-of-band) — `terraform/modules/secrets/`
- IAM: ECS execution role, ECS task role, GitHub Actions OIDC role — `terraform/modules/iam/`
- ECR repositories (api + worker, IMMUTABLE tags, lifecycle 10-image retention) — inline in environment `main.tf` files
- S3 state bucket (KMS-encrypted, versioned) — `terraform/bootstrap/main.tf`

**AWS services planned (Phase 14+, not yet provisioned):**
- ECS Fargate (API container + Celery worker container)
- ALB with HTTP→HTTPS redirect
- CloudFront + S3 (frontend static hosting — no container for frontend)
- ACM TLS certificate
- Route 53 with health-check-based failover routing

**Warm failover cloud:** Azure (planned, not yet implemented in committed code)
- Azure PostgreSQL Flexible Server 17 (replica of RDS via logical replication)
- Azure Container Instances (ACI) for API/worker
- Azure Container Registry (ACR)
- Azure Key Vault

**Terraform state:**
- Bucket: `nexus-crm-terraform-state` (ap-southeast-1), KMS-encrypted, native file locking
- Keys: `staging/terraform.tfstate`, `prod/terraform.tfstate`

## Environments

| Variable | Staging | Prod |
|---|---|---|
| RDS instance | `db.t4g.medium` | `db.t4g.large` |
| RDS storage | 20 GB (max 40) | 50 GB (max 100) |
| RDS Multi-AZ | false | true |
| Redis node | `cache.t4g.small` | `cache.t4g.medium` |
| NAT gateways | 1 | 2 |
| Deletion protection | false | true |

## Platform Requirements

**Development:**
- Docker + Docker Compose (local dev via `make dev`)
- AWS CLI (for `make tf-secrets-staging` / `make tf-secrets-prod`)
- Terraform >= 1.10 (for infra work)

**Production deployment target:**
- AWS ECS Fargate (Phase 14)
- Frontend: S3 + CloudFront (no container)

---

*Stack analysis: 2026-04-06*
