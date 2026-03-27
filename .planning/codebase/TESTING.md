# Testing Patterns

**Analysis Date:** 2026-03-26

## Test Frameworks

**Backend:**
- Runner: `pytest` 8.x with `pytest-asyncio` 0.23.x
- Coverage: `pytest-cov` 5.x
- HTTP client: `httpx.AsyncClient` with `ASGITransport` (in-process, no real server)
- Config in `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  testpaths = ["backend/tests"]
  ```
- Also mirrored in `backend/tests/pytest.ini`:
  ```ini
  [pytest]
  asyncio_mode = auto
  ```

**Frontend:**
- Runner: Vitest 2.x (configured inside `frontend/vite.config.js`)
- DOM environment: jsdom
- Component rendering: `@testing-library/react` 16.x
- User interactions: `@testing-library/user-event` 14.x
- Matchers: `@testing-library/jest-dom` (imported in `frontend/src/test/setup.js`)
- Globals enabled: `vi`, `describe`, `it`, `expect`, `beforeEach`, `afterEach` — no imports needed in test files

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

---

## Coverage Requirements

**Backend:** 85% minimum enforced. `--cov-fail-under=85` in `make test` causes the command to exit non-zero if coverage drops below this threshold. Coverage report is written to `htmlcov/`.

**Frontend:** No coverage target configured. Vitest runs without `--coverage` flag.

---

## Test File Organization

**Backend:** All tests are in `backend/tests/`. They are a sibling package to the application, not co-located with source files.

```
backend/tests/
├── conftest.py                       # Shared fixtures, FakeRedis, DB lifecycle, seeded data
├── pytest.ini                        # asyncio_mode = auto
├── test_auth.py                      # Auth endpoints: login, refresh, logout, me, user CRUD
├── test_crm_core.py                  # CRUD flows: contacts, companies, pipelines, deals
├── test_permissions.py               # RBAC matrix — parametrized by role
├── test_security.py                  # JWT expiry, token blacklist, cross-org rejection, SQL injection
├── test_boards_pages_automations.py  # Boards, board columns, pages, automations
├── test_linkedin_ai.py               # LinkedIn sync routes and AI lead scoring
├── test_integration.py               # Full end-to-end sales workflow (multi-step)
├── test_performance.py               # Query count budgets and latency assertions
└── test_health.py                    # Health check and metrics endpoints
```

**Frontend:** Test files are in `frontend/src/__tests__/`, separate from source files.

```
frontend/src/__tests__/
├── test-utils.jsx           # Shared renderWithProviders helper
├── LoginPage.test.jsx
├── ContactsPage.test.jsx
├── DealDetailPage.test.jsx
├── KanbanBoard.test.jsx
├── PipelinePage.test.jsx
└── AIQueryPage.test.jsx
```

Frontend test files are named `ComponentName.test.jsx`.

---

## Backend Test Structure

**Async tests:**
Every test function that touches the database or HTTP client is `async def` and decorated with `@pytest.mark.asyncio`. With `asyncio_mode = "auto"`, the decorator is optional but is still used explicitly in most files for clarity.

**Class grouping:**
Related tests that share setup or form a permission matrix are grouped into classes:
- `TestPermissionMatrix` in `test_permissions.py`
- `TestPerformance` in `test_performance.py`
- `TestSalesWorkflow` in `test_integration.py`
- `TestSecurity` in `test_security.py`

Standalone scenario tests use module-level functions (most of `test_auth.py`, `test_crm_core.py`).

**Assertion style:**
- Assert `response.status_code` before accessing `.json()`
- Use specific key access, not bulk dict equality: `response.json()["id"]`, `response.json()["total"]`
- Boolean flags: `assert x is True` / `assert x is False` (not `== True`)

```python
@pytest.mark.asyncio
async def test_login_valid_credentials_returns_token(client, seeded_users):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
```

**Parametrize pattern** (permissions matrix):
```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("username", "expected_status"),
    [
        ("super", 201),
        ("admin", 201),
        ("alpha-manager", 201),
        ("alpha-rep", 403),
        ("viewer", 403),
    ],
)
async def test_pipeline_create_permissions(self, async_client, seeded_org, username, expected_status):
    response = await async_client.post(
        "/api/v1/pipelines",
        json={"name": f"Pipeline-{username}", ...},
        headers=auth_header(seeded_org[username]),
    )
    assert response.status_code == expected_status
```

---

## Conftest and Fixtures

All shared backend fixtures live in `backend/tests/conftest.py`.

**Database lifecycle:**

`setup_db` (session-scoped, autouse) — creates all tables once per test session using SQLite. The `DATABASE_URL` and `DATABASE_URL_SYNC` env vars are set to SQLite paths before any imports run:

```python
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_nexus.db")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///./test_nexus.db")
```

`clean_db` (function-scoped, autouse) — truncates all tables between every test using `delete(table)` in reverse dependency order. This ensures full isolation without re-creating the schema on each test.

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

**Key fixtures:**

| Fixture | Scope | What it provides |
|---|---|---|
| `db_session` | function | Open `AsyncSession` for direct DB manipulation |
| `async_client` | function | `httpx.AsyncClient` bound to the FastAPI ASGI app |
| `client` | function | Alias for `async_client` |
| `fake_redis` | function | In-memory `FakeRedis` patched into all Redis call sites |
| `seeded_org` | function | One org, two teams (alpha/beta), eight users across all roles |
| `pipeline` | function | Sales pipeline with 4 stages (depends on `seeded_org`) |
| `stages` | function | List of 4 `PipelineStage` objects (depends on `pipeline`) |
| `seed_50_deals` | function | 50 deals spread across stages (for performance tests) |
| `seed_100_contacts` | function | 100 contacts, alternating lifecycle stages |
| `seed_50_pages` | function | 50 pages with parent-child nesting (for tree query tests) |
| `seed_1000_activities` | function | 1 deal with 1000 activities (for pagination latency tests) |
| `query_counter` | function | SQLAlchemy `before_cursor_execute` event listener; `counts["count"]` |
| `mock_linkedin` | function | Monkeypatches `_client` with a `MockLinkedIn` returning fixed data |

**`seeded_org` user set** — referenced across all permission and CRUD tests by key:

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

**`auth_header` helper** (defined in `conftest.py`, re-exported by convention):
```python
def auth_header(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id), "org_id": str(user.org_id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}
```
Always use this helper to produce headers for authenticated requests; never construct JWT strings manually in tests.

---

## Mocking

### Backend — Redis

`FakeRedis` is an in-memory async class in `conftest.py` that implements the full Redis interface used by the app, including sorted-set operations needed by the rate limiter. It is patched via `monkeypatch.setattr` at all call sites in the `fake_redis` fixture:

```python
@pytest.fixture
def fake_redis(monkeypatch) -> FakeRedis:
    client = FakeRedis()
    monkeypatch.setattr("backend.api.main.redis_async.from_url", lambda *args, **kwargs: client)
    monkeypatch.setattr("backend.api.routes.auth.redis_async.from_url", lambda *args, **kwargs: client)
    monkeypatch.setattr("backend.api.routes.ai_query.redis_async.from_url", lambda *args, **kwargs: client)
    monkeypatch.setattr("backend.services.ai_service.redis_async.from_url", lambda *args, **kwargs: client)
    return client
```

`async_client` depends on `fake_redis`, so all HTTP tests automatically get a patched Redis.

### Backend — Storage

`check_storage` is monkeypatched to a no-op coroutine in the `async_client` fixture so tests do not require S3 or a local disk path:

```python
async def fake_check_storage() -> None:
    return None

monkeypatch.setattr("backend.api.main.check_storage", fake_check_storage)
```

### Backend — LinkedIn

The `mock_linkedin` fixture patches `backend.api.routes.linkedin._client` with a `MockLinkedIn` class that returns fixed `LinkedInPersonResult` and `LinkedInCompanyResult` objects. Tests that exercise LinkedIn routes must include this fixture.

### Backend — Celery

In `test_integration.py`, `backend.workers.automation_runner.run_automation.delay` is monkeypatched to run inline as an asyncio task, so automation workflows execute synchronously within the test:

```python
def run_inline(automation_id: str, payload: dict):
    _pending.append(asyncio.get_running_loop().create_task(
        execute_automation_by_id(automation_id, payload)
    ))

monkeypatch.setattr("backend.workers.automation_runner.run_automation.delay", run_inline)
```

### Frontend — API modules

Every frontend test mocks the entire API module with `vi.mock`. Mock functions are created with `vi.fn()` at the top of the file and configured with `.mockResolvedValue(...)` in `beforeEach`:

```javascript
const getContacts = vi.fn();

vi.mock('@/api/contacts', () => ({
  getContacts,
  createContact
}));

beforeEach(() => {
  getContacts.mockResolvedValue({
    items: [{ id: 'c1', first_name: 'Taylor', ... }],
    total: 1
  });
});

afterEach(() => {
  vi.clearAllMocks();
});
```

### Frontend — Third-party libraries

Libraries that interact with pointer events or DOM APIs unavailable in jsdom are fully mocked. Example for `@dnd-kit/core` in `KanbanBoard.test.jsx`:

```javascript
vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children, onDragEnd }) => {
    dragEndHandler = onDragEnd;
    return <div>{children}</div>;
  },
  // ... rest of module
}));
```

---

## Frontend Test Utilities

**`renderWithProviders`** in `frontend/src/__tests__/test-utils.jsx`:

Wraps the component under test in a fresh `QueryClient` (with `retry: false`) and a `MemoryRouter` with the specified route/path. Every frontend test uses this helper instead of bare `render`.

```javascript
export function renderWithProviders(ui, { route = '/', path = '/' } = {}) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } }
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route path={path} element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}
```

**Setup file** `frontend/src/test/setup.js`:
- Imports `@testing-library/jest-dom/vitest` to extend `expect` with DOM matchers (`toBeInTheDocument`, `toHaveValue`, etc.)
- Polyfills `window.matchMedia` (jsdom does not implement it; many Radix components query it)

---

## Performance Tests

`backend/tests/test_performance.py` contains `TestPerformance` with two strategies:

**Query count budgets** — via the `query_counter` fixture (SQLAlchemy `before_cursor_execute` event):

```python
query_counter["count"] = 0
response = await async_client.get("/api/v1/contacts", ...)
assert query_counter["count"] <= 3   # N+1 detection
```

Enforced budgets:
- `GET /pipelines/{id}/kanban` with 50 deals — max **5 queries**
- `GET /contacts` with 100 contacts — max **3 queries**
- `GET /pages` with 50 pages — max **2 queries**

**Latency assertions** — wall-clock timing with `time.perf_counter`:

```python
started = time.perf_counter()
response = await async_client.get("/api/v1/deals/{id}/activities?page=1&size=25", ...)
elapsed_ms = (time.perf_counter() - started) * 1000
assert elapsed_ms < 100   # must respond in under 100ms
```

Used for the activity feed with 1000 activities to verify pagination performance.

---

## Test Types

**Backend integration tests (primary):**
The majority of backend tests are full HTTP integration tests — they exercise the complete request/response cycle through FastAPI routing, service layer, and SQLite. No unit tests mock the database layer.

**Backend permission/security tests:**
`test_permissions.py` and `test_security.py` are dedicated to confirming that role checks and org scoping are enforced at the API boundary. These are parametrized to cover all defined roles systematically.

**Backend end-to-end workflow test:**
`test_integration.py` — `TestSalesWorkflow.test_full_sales_cycle` — is a single long scenario that creates a board, pipeline, automation, deal, tasks, and verifies the automation fires. It is the closest to a true E2E test within the backend suite.

**Frontend component tests:**
Render a page/component with mocked API functions, then use Testing Library queries (`screen.findByText`, `screen.getByRole`, `screen.getByLabelText`) and `waitFor` for async assertions. Tests assert on visible UI output only, not internal component state.

---

## What Is Not Tested

- **Alembic migrations**: Schema correctness is tested implicitly through `Base.metadata.create_all` in SQLite; no tests run actual migrations
- **Frontend E2E**: No Playwright or Cypress; browser-level flows are untested
- **Frontend coverage**: No coverage threshold configured for Vitest
- **Mobile (`mobile/`)**: Zero tests; no test framework installed
- **Celery workers** (`backend/workers/`): Only `automation_runner` is tested indirectly via the integration test; `email_sync`, `linkedin_sync`, and `ai_enrichment` tasks are untested
- **Storage backends** (`backend/storage/`): `check_storage` is always mocked away; `LocalStorage` and `S3Storage` have no direct unit tests
- **Analytics service** (`backend/services/analytics_service.py`): No dedicated test file; covered only if a route test exercises it

---

*Testing analysis: 2026-03-26*
