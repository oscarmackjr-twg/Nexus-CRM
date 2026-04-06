---
updated: 2026-04-06
focus: quality
---

# Testing Patterns

## Test Frameworks

**Backend:**
- Runner: `pytest` with `pytest-asyncio`
- Coverage: `pytest-cov`
- HTTP client: `httpx.AsyncClient` with `ASGITransport` (in-process, no real server)
- Async mode configured in `backend/tests/conftest.py` via `os.environ` and pytest-asyncio
- Asyncio mode: `asyncio_mode = "auto"` (tests are `async def`, `@pytest.mark.asyncio` decorator is explicit on most test functions)

**Frontend:**
- Runner: Vitest (configured inside `frontend/vite.config.js`)
- DOM environment: jsdom
- Component rendering: `@testing-library/react`
- User interactions: `@testing-library/user-event`
- Matchers: `@testing-library/jest-dom` (imported via setup file `frontend/src/test/setup.js`)
- Globals enabled: `vi`, `describe`, `it`, `expect`, `beforeEach`, `afterEach` — some test files import them explicitly (`import { describe, it, expect, vi, beforeEach } from 'vitest'`), others rely on globals

---

## Running Tests

```bash
# Backend — full suite with coverage (85% minimum enforced)
make test

# Equivalent to:
docker-compose -f deploy/docker-compose.yml run --rm backend \
  pytest backend/tests/ -v --cov=backend --cov-report=html --cov-fail-under=85

# Backend — lint and type check
make lint   # runs: ruff check backend/ && mypy backend/ --ignore-missing-imports

# Backend — auto-format
make format  # runs: ruff format backend/ && black backend/

# Frontend — single run (CI mode)
cd frontend && npm test          # vitest run

# Frontend — watch mode (development)
cd frontend && npm run test:watch  # vitest
```

Note: `make test` runs tests inside the Docker container. The SQLite test database (`test_nexus.db`) is created on disk and ignored by `.gitignore`.

---

## Coverage Requirements

**Backend:** 85% minimum enforced. `--cov-fail-under=85` in `make test` causes exit non-zero if coverage drops below threshold. Coverage HTML report written to `htmlcov/`.

**Frontend:** No coverage target configured. Vitest runs without `--coverage` flag.

---

## Test File Organization

**Backend:** All tests live in `backend/tests/`. Sibling package to the application, not co-located with source.

```
backend/tests/
├── conftest.py        # Shared fixtures, FakeRedis, DB lifecycle, seeded data
├── test_deals_pe.py   # PE field persistence, label resolution, deal_team CRUD
├── test_funds.py      # Fund CRUD API — /api/v1/funds
└── test_ref_data.py   # Reference data ORM and API (REFDATA-01 through REFDATA-14)
```

**Important:** The test suite was substantially reduced during Phase 4–8 development. The earlier suite contained tests for auth, CRM core, permissions, security, boards/pages/automations, LinkedIn/AI, integration, performance, and health. These files no longer exist on disk. Only the three domain-specific test files listed above remain.

**Frontend:** Test files in `frontend/src/__tests__/`, separate from source files.

```
frontend/src/__tests__/
├── Layout.test.jsx      # Sidebar structure, nav items, user footer, staging banner
├── LoginPage.test.jsx   # Form submission, error handling, backend status, staging banner
└── RefSelect.test.jsx   # RefSelect component — loading, error, options, placeholder states
```

Frontend test files are named `ComponentName.test.jsx`.

**Missing test-utils file:** `Layout.test.jsx` and `LoginPage.test.jsx` import `./test-utils` (`renderWithProviders`), but `frontend/src/__tests__/test-utils.jsx` does **not exist on disk**. These two test files will fail to run until this file is created. `RefSelect.test.jsx` uses bare `render` from `@testing-library/react` and does not depend on `test-utils`.

---

## Backend Test Structure

**Async tests:**
Every test that touches the database or HTTP client is `async def`. With `asyncio_mode = "auto"` in pytest-asyncio, the `@pytest.mark.asyncio` decorator is redundant but is used explicitly on all test functions in the current test files for clarity.

**Local fixtures vs. conftest fixtures:**
New test files (`test_deals_pe.py`, `test_funds.py`) define their own seed fixtures (`pe_seed`, `fund_seed`) instead of using `seeded_org` from `conftest.py`. Both approaches are valid; the local pattern avoids fixture coupling but duplicates setup logic.

**Assertion style:**
- Assert `response.status_code` before accessing `.json()`
- Use specific key access, not bulk dict equality: `response.json()["id"]`, `response.json()["fund_name"]`
- Boolean flags: `assert x is True` / `assert x is False` (not `== True`)
- `assert x in (200, 201)` used in new tests where create endpoints may return either status

```python
@pytest.mark.asyncio
async def test_create_fund(client, fund_seed):
    """POST /api/v1/funds creates a new fund"""
    headers = auth_header(fund_seed["admin"])
    response = await client.post("/api/v1/funds", json={"fund_name": "Test Fund I"}, headers=headers)
    assert response.status_code in (200, 201)
    data = response.json()
    assert "id" in data
    assert data["fund_name"] == "Test Fund I"
```

**Pending tests with `@pytest.mark.xfail`:**
`test_ref_data.py` contains four tests marked `@pytest.mark.xfail(strict=False, reason="Plan 02-02 implements the routes")`. These cover the admin ref-data API routes (REFDATA-11 through REFDATA-14) and will pass once those routes are implemented. They are currently expected to fail.

---

## Conftest and Fixtures

All shared backend fixtures live in `backend/tests/conftest.py`.

**Database lifecycle:**

`setup_db` (session-scoped, autouse) — creates all tables once per session using SQLite:

```python
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_nexus.db")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///./test_nexus.db")
```

`clean_db` (function-scoped, autouse) — truncates all tables between every test using `delete(table)` in reverse dependency order. Full isolation without schema re-creation on each test:

```python
@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    session_factory = get_session_maker()
    async with session_factory() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()
    yield
```

**Key fixtures in conftest.py:**

| Fixture | Scope | What it provides |
|---|---|---|
| `db_session` | function | Open `AsyncSession` for direct DB manipulation |
| `async_client` | function | `httpx.AsyncClient` bound to the FastAPI ASGI app |
| `client` | function | Alias for `async_client` |
| `fake_redis` | function | In-memory `FakeRedis` patched into all Redis call sites |
| `seeded_org` | function | One org, two teams (alpha/beta), eight users across all roles |
| `pipeline` | function | Sales pipeline with 4 stages (depends on `seeded_org`) |
| `stages` | function | List of 4 `PipelineStage` objects (depends on `pipeline`) |
| `seed_50_deals` | function | 50 deals spread across stages |
| `seed_100_contacts` | function | 100 contacts, alternating lifecycle stages |
| `seed_50_pages` | function | 50 pages with parent-child nesting |
| `seed_1000_activities` | function | 1 deal with 1000 activities (for pagination latency tests) |
| `seed_ref_data` | function | One row per category (sector, sub_sector, transaction_type, tier, etc.) |
| `query_counter` | function | SQLAlchemy `before_cursor_execute` event listener; `counts["count"]` |
| `mock_linkedin` | function | Monkeypatches `backend.api.routes.linkedin._client` |
| `admin_token` | function | Raw JWT string for the `admin` user |
| `rep_token` | function | Raw JWT string for the `alpha-rep` user |
| `auth_tokens` | function | Stub `{ access_token, refresh_token, token_type }` dict |

**`seeded_org` user set:**

| Key | Role | Team |
|---|---|---|
| `super` | `super_admin` | alpha |
| `admin` | `org_admin` | alpha |
| `alpha-manager` | `team_manager` | alpha |
| `alpha-rep` | `rep` | alpha |
| `alpha-peer` | `rep` | alpha |
| `beta-manager` | `team_manager` | beta |
| `beta-rep` | `rep` | beta |
| `viewer` | `viewer` | alpha |

**`auth_header` helper** (defined in `conftest.py` and also re-defined locally in new test files):
```python
def auth_header(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "org_id": str(user.org_id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}
```
Always use this helper — never construct JWT strings manually in tests.

---

## Mocking

### Backend — Redis

`FakeRedis` in `conftest.py` is an in-memory async class implementing the full Redis interface used by the app, including sorted-set operations for the rate limiter. Patched via `monkeypatch.setattr` at all call sites in the `fake_redis` fixture. `async_client` depends on `fake_redis`, so all HTTP tests automatically get a patched Redis.

### Backend — Storage

`check_storage` is monkeypatched to a no-op coroutine in the `async_client` fixture:

```python
async def fake_check_storage() -> None:
    return None
monkeypatch.setattr("backend.api.main.check_storage", fake_check_storage)
```

### Backend — LinkedIn

The `mock_linkedin` fixture patches `backend.api.routes.linkedin._client` with a `MockLinkedIn` class returning fixed `LinkedInPersonResult` and `LinkedInCompanyResult` objects. Include this fixture in any test exercising LinkedIn routes.

### Frontend — API modules

Every frontend test mocks the entire API module with `vi.mock`. Mock functions are created with `vi.fn()` at module top-level and configured with `.mockReturnValue(...)` or `.mockResolvedValue(...)`:

```javascript
vi.mock('@/hooks/useRefData');
import { useRefData } from '@/hooks/useRefData';

beforeEach(() => {
  useRefData.mockReturnValue({ data: mockItems, isLoading: false, isError: false });
});

afterEach(() => {
  vi.clearAllMocks();
});
```

### Frontend — Utility mocking

`vi.hoisted()` is used to hoist mock function creation before module-level `vi.mock()` calls:

```javascript
const { login, navigate, toastError } = vi.hoisted(() => ({
  login: vi.fn(),
  navigate: vi.fn(),
  toastError: vi.fn()
}));

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ login, isAuthenticated: false })
}));
```

Static assets are mocked inline: `vi.mock('@/assets/twg-logo.png', () => ({ default: 'twg-logo.png' }))`.

---

## Frontend Test Utilities

**`renderWithProviders`** — expected in `frontend/src/__tests__/test-utils.jsx` but this file does not currently exist on disk. The function wraps a component in a fresh `QueryClient` (with `retry: false`) and a `MemoryRouter`. `Layout.test.jsx` and `LoginPage.test.jsx` will fail until this file is created.

**`RefSelect.test.jsx`** uses bare `render` from `@testing-library/react` directly — no `renderWithProviders` dependency.

**Setup file** (`frontend/src/test/setup.js`):
- Referenced in `vite.config.js` as `setupFiles: './src/test/setup.js'`
- This file does not exist on disk — `@testing-library/jest-dom` matchers will not be available and `window.matchMedia` will not be polyfilled, causing Vitest to fail on any test using DOM matchers like `toBeInTheDocument`

---

## Test Types

**Backend — HTTP integration tests (primary):**
All three current backend test files are full HTTP integration tests — they exercise the complete request/response cycle through FastAPI routing, service layer, and SQLite. No unit tests mock the database layer.

**Backend — ORM/fixture tests:**
`test_ref_data.py` contains three tests (`test_ref_data_table_exists`, `test_all_categories_seeded`, `test_seed_values`) that directly query the database session without going through HTTP routes. These verify ORM model correctness.

**Backend — `xfail` placeholder tests:**
Four tests in `test_ref_data.py` are marked `@pytest.mark.xfail(strict=False)` for routes not yet implemented. They serve as TDD anchors for Phase 2 Wave 2 (REFDATA-11 through REFDATA-14).

**Frontend — Component/page tests:**
Render a component with mocked dependencies, then use Testing Library queries (`screen.getByText`, `screen.getByRole`, `screen.getByLabelText`) and `waitFor` for async assertions. Tests assert on visible UI output only — not internal component state.

---

## What Is Not Tested

**Broad gaps from test suite reduction:**
The following test files existed previously and have been removed. These areas have no backend test coverage:
- Auth endpoints (`/api/v1/auth/login`, `/api/v1/auth/refresh`, user CRUD)
- CRM core CRUD (contacts, companies, pipelines, deals general CRUD)
- RBAC permission matrix (role-based access across all endpoints)
- Security (JWT expiry, token blacklist, cross-org rejection, SQL injection)
- Boards, board columns, pages, automations
- LinkedIn sync routes and AI lead scoring
- Full sales workflow integration test
- Query count budgets and latency assertions (performance tests)
- Health check and metrics endpoints

**Additional gaps:**
- **Alembic migrations**: Schema correctness tested implicitly via `Base.metadata.create_all` in SQLite; no tests run actual migrations
- **Frontend E2E**: No Playwright or Cypress; browser-level flows untested
- **Frontend coverage**: No coverage threshold configured for Vitest; `frontend/src/test/setup.js` and `test-utils.jsx` are missing (tests will fail to run)
- **Celery workers** (`backend/workers/`): No test coverage for `email_sync`, `linkedin_sync`, `ai_enrichment`, or `automation_runner`
- **Storage backends** (`backend/storage/`): `check_storage` always mocked away; `LocalStorage` and `S3Storage` have no direct tests
- **Counterparties/Funding routes**: `backend/api/routes/counterparties.py` and `backend/api/routes/funding.py` have no test files
- **Admin ref-data API routes**: Covered only by `xfail` placeholders in `test_ref_data.py`

---

*Testing analysis: 2026-04-06*
