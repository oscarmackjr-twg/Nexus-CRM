# Technology Stack

**Analysis Date:** 2026-03-26

---

## Languages

**Primary:**
- Python 3.11 — backend API server and Celery worker (pinned in `pyproject.toml` via `requires-python = ">=3.11"` and hardcoded in `deploy/Dockerfile` as `python:3.11-slim`)
- TypeScript/JavaScript (ESM) — React frontend (`frontend/package.json` `"type": "module"`)

**Secondary:**
- HCL — infrastructure-as-code in `terraform/` (Terraform ≥ 1.6)

---

## Runtime

**Backend:**
- CPython 3.11 (slim Docker image in production, local `.venv` for development)
- Uvicorn `>=0.29,<1.0` — ASGI server with `[standard]` extras (WebSocket + lifespan support)

**Frontend:**
- Node.js 20 (pinned in `deploy/docker-compose.yml` as `node:20-alpine` and in CI via `actions/setup-node@v4` with `node-version: "20"`)

**Mobile:**
- Expo SDK 52 with React Native 0.76.1

**Package Managers:**
- pip — Python backend (no lockfile; `requirements.txt` + `pyproject.toml` specify version ranges)
- npm — frontend (`frontend/package.json`); `package-lock.json` expected but not read
- npm — mobile (`mobile/package.json`)

---

## Frameworks

**Backend Core:**
- FastAPI `>=0.110,<1.0` — async HTTP API framework; all routes under `/api/v1` prefix; entry point `backend/api/main.py`
- Pydantic v2 `>=2.6,<3.0` — request/response validation and settings management
- pydantic-settings `>=2.2,<3.0` — environment-variable-backed `Settings` class in `backend/config.py`

**Frontend Core:**
- React 18.3.1 — UI library (`frontend/src/`)
- React Router DOM 6.28.0 — client-side routing
- Vite 5.4.10 — dev server (port 5173) and production bundler; config at `frontend/vite.config.js`
- Tailwind CSS 3.4.15 — utility-first styling; config at `frontend/tailwind.config.js`

**Mobile Core:**
- Expo 52 — managed React Native workflow (`mobile/`)
- React Navigation 6 — stack and bottom-tab navigation (`mobile/src/navigation/`)

**State Management (Frontend):**
- Zustand 5.0.2 — global client state (`frontend/src/store/`)
- TanStack Query 5.64.2 — server state / data fetching (`frontend/src/api/`)

**Forms (Frontend):**
- React Hook Form 7.54.2 + `@hookform/resolvers` 3.10.0
- Zod 3.24.1 — schema validation shared with form resolvers

**UI Components (Frontend):**
- Radix UI — headless components: `@radix-ui/react-dialog`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-tabs`
- `@dnd-kit/core` 6.3.1 + `@dnd-kit/sortable` 10.0.0 — drag-and-drop for Kanban boards
- Recharts 2.15.0 — charting / analytics visualisations
- Lucide React 0.468.0 — icon library
- Sonner 1.7.1 — toast notifications

**HTTP Client:**
- Axios 1.7.2 — frontend and mobile HTTP client
- httpx `>=0.27,<1.0` — async HTTP client used in backend services (LinkedIn API calls, OpenClaw API calls)

---

## Database

**Production:**
- PostgreSQL 15 (Docker image `postgres:15-alpine` in dev; AWS RDS provisioned via `terraform/modules/rds/`)
- Driver: asyncpg `>=0.29,<1.0` (async) + psycopg `>=3.1,<4.0` (sync, used by Alembic)

**Development / Testing Fallback:**
- SQLite via aiosqlite `>=0.20,<1.0` — default `DATABASE_URL` in `backend/config.py` falls back to SQLite when no env var is set; test suite uses this path

**ORM:**
- SQLAlchemy 2.0 async (`create_async_engine`, `async_sessionmaker`) — `backend/database.py`
- All models defined in `backend/models.py` using `DeclarativeBase`

**Migrations:**
- Alembic `>=1.13,<2.0` — migration scripts in `alembic/versions/`; run via `make migrate`

---

## Cache & Message Broker

**Redis 7:**
- Docker image `redis:7-alpine` in dev; AWS ElastiCache provisioned via `terraform/modules/elasticache/`
- Uses:
  1. Celery broker and result backend (`backend/workers/celery_app.py`)
  2. Auth refresh-token store and blacklist (`backend/api/routes/auth.py`)
  3. AI suggestions cache with 15-minute TTL (`backend/services/ai_service.py`)
  4. Rate-limiter storage (`slowapi` in `backend/api/main.py`)
- Client: `redis[asyncio]` from `redis>=5.0,<6.0` package

---

## Background Jobs

- Celery `>=5.4,<6.0` — task queue with Redis broker
- Worker process defined separately: `deploy/Dockerfile.worker`
- Three queues: `default`, `linkedin`, `ai` (set in `Dockerfile.worker` CMD)
- Tasks:
  - `backend/workers/linkedin_sync.py` — `linkedin.sync_contact`, `linkedin.sync_company`
  - `backend/workers/ai_enrichment.py` — `ai.enrichment.batch`
  - `backend/workers/automation_runner.py` — `run_automation`
  - `backend/workers/email_sync.py`, `backend/workers/automation_trigger.py`

---

## Authentication

- JWT (HS256) via `python-jose[cryptography] >=3.3,<4.0` — access and refresh tokens
- bcrypt `>=4.1,<5.0` — password hashing (passlib CryptContext; falls back to raw bcrypt if passlib absent)
- Fernet symmetric encryption (from `cryptography` package, pulled in by python-jose) — encrypts stored LinkedIn access tokens at rest
- FastAPI `OAuth2PasswordBearer` — token extraction from `Authorization: Bearer` header

---

## Storage

- Pluggable storage backend pattern: `backend/storage/base.py` (abstract), `backend/storage/local.py`, `backend/storage/s3.py`
- Switched by `STORAGE_TYPE` env var (`local` default, `s3` for production)
- AWS S3 via boto3 `>=1.34,<2.0`; bucket + region configured by `S3_BUCKET_NAME` / `S3_REGION`

---

## Testing

**Backend:**
- pytest `>=8.1,<9.0` — test runner; config in `pyproject.toml` (`asyncio_mode = "auto"`, `testpaths = ["backend/tests"]`)
- pytest-asyncio `>=0.23,<1.0` — async test support (auto mode)
- pytest-cov `>=5.0,<6.0` — coverage; 85% minimum enforced via `make test`
- Test files: `backend/tests/` (conftest + 9 test modules)
- Run: `make test` (runs inside Docker) or `pytest` directly

**Frontend:**
- Vitest 2.1.8 — test runner integrated with Vite; config in `frontend/vite.config.js`
- `@testing-library/react` 16.1.0 + `@testing-library/user-event` 14.5.2 + `@testing-library/jest-dom` 6.6.3
- jsdom 25.0.1 — DOM environment for Vitest
- Test files: `frontend/src/__tests__/` and `frontend/src/test/`
- Run: `npm test` (single run) or `npm run test:watch`

---

## Build & Dev Tooling

**Container / Orchestration:**
- Docker — multi-stage build in `deploy/Dockerfile` (Node 20 build stage → Python 3.11 runtime; frontend dist bundled into API image)
- Docker Compose (`deploy/docker-compose.yml`) — local dev stack: postgres, redis, backend (port 8000), worker, frontend (port 5173)
- Make — top-level task runner (`Makefile`); targets: `dev`, `test`, `lint`, `format`, `migrate`, `seed`, `docker-up`, `docker-down`, `tf-plan`, `tf-apply`

**Backend Linting / Formatting:**
- Ruff — linting (`ruff check backend/`) and formatting (`ruff format backend/`)
- Black — secondary formatter (`black backend/`)
- mypy — static type checking (`mypy backend/ --ignore-missing-imports`)

**Infrastructure:**
- Terraform `>=1.6` — AWS infrastructure; modules in `terraform/modules/`; state stored in S3 backend

**Observability:**
- structlog `>=24.1,<26.0` — structured JSON logging (`backend/utils/structured_logging.py`)
- OpenTelemetry API + SDK `>=1.24,<2.0` — tracing instrumentation (`backend/utils/telemetry.py`)
- Custom Prometheus-format metrics endpoint (`GET /metrics`) built on in-process counters (`backend/utils/telemetry.py`)

**Rate Limiting:**
- slowapi `>=0.1.9,<1.0` — per-IP rate limiting backed by Redis; applied at app startup in `backend/api/main.py`

---

## Production Infrastructure (AWS)

Provisioned by Terraform (`terraform/`):

| Resource | Service |
|----------|---------|
| API container | ECS Fargate (`terraform/modules/ecs/`) |
| Worker container | ECS Fargate (`terraform/modules/ecs_worker/`) |
| Container registry | ECR (two repos: api, worker) |
| Database | RDS PostgreSQL (`terraform/modules/rds/`) |
| Cache / broker | ElastiCache Redis (`terraform/modules/elasticache/`) |
| Static assets | S3 + CloudFront (`terraform/modules/cloudfront/`) |
| Load balancer | ALB (`terraform/modules/alb/`) |
| Secrets | AWS Secrets Manager (`terraform/modules/secrets/`) |
| Networking | VPC, public/private subnets, security groups (`terraform/modules/networking/`) |
| IAM | Task roles, OIDC role for GitHub Actions OIDC (`terraform/modules/iam/`) |

---

*Stack analysis: 2026-03-26*
