---
updated: 2026-04-06
focus: quality
---

# Coding Conventions

## Naming Patterns

**Python files:**
- Modules use `snake_case`: `contacts.py`, `deal_scoring.py`, `ref_data.py`, `funds.py`
- Test files are prefixed `test_`: `test_deals_pe.py`, `test_funds.py`, `test_ref_data.py`
- Service classes match their domain noun: `ContactService`, `DealService`, `FundService`, `RefDataService`

**Python functions and methods:**
- `snake_case` for all functions: `list_contacts`, `create_access_token`, `hash_password`, `list_funds`
- Private helpers prefixed with underscore: `_base_deal_stmt`, `_visible_team_ids`, `_contact_response`, `_utcnow`
- Static helpers on service classes use `@staticmethod` decorator

**Python variables:**
- `snake_case` throughout: `org_id`, `hashed_password`, `lifecycle_stage`, `fund_name`
- Boolean columns prefixed `is_`: `is_active`, `is_archived`, `is_private`
- Timestamps use `_at` suffix: `created_at`, `updated_at`, `occurred_at`, `last_login`
- Foreign key columns use `_id` suffix: `org_id`, `team_id`, `owner_id`, `fundraise_status_id`
- Reference-data label fields use `_label` suffix: `transaction_type_label`, `fundraise_status_label`

**Python types:**
- `PascalCase` for Pydantic models and SQLAlchemy model classes: `FundCreate`, `FundResponse`, `RefDataResponse`
- Type aliases at module level: `JSONVariant`, `StringList` in `backend/models.py`

**Frontend files:**
- React components: `PascalCase.jsx` — `Layout.jsx`, `RefSelect.jsx`, `StagingBanner.jsx`, `DealDetailPage.jsx`
- Hooks: `camelCase.js` prefixed with `use` — `useRefData.js`, `useAuth.js`, `useDebounce.js`
- API modules: `camelCase.js` matching domain — `contacts.js`, `deals.js`, `funds.js`, `refData.js`, `counterparties.js`
- Zustand stores: `useNounStore.js` — `useAuthStore.js`, `useUIStore.js`
- UI primitives: `kebab-case.jsx` under `frontend/src/components/ui/` — `button.jsx`, `select.jsx`
- Utility modules: `camelCase.js` — `refCategories.js`, `utils.js`

**Frontend variables and functions:**
- `camelCase` for all JS identifiers: `getContacts`, `createFund`, `debouncedSearch`
- React components export as default with `PascalCase` function name (page/layout components) or as named exports with `PascalCase` (shared components, e.g., `export function RefSelect`)
- Custom hooks return objects, not arrays (except `useState` mirroring)

---

## Python Style

**`from __future__ import annotations`:**
Required in all Python files — enables PEP 563 postponed evaluation so forward references resolve without quoting. Currently present in 20 of 29 backend files. The following do **not** yet have it and must be added when they are next modified:
- `backend/api/main.py`
- `backend/api/routes/auth.py`
- `backend/api/routes/companies.py`
- `backend/api/routes/contacts.py`
- `backend/api/routes/deals.py`
- `backend/schemas/companies.py`
- `backend/schemas/contacts.py`
- `backend/schemas/deals.py`
- `backend/seed_data.py`

**Typing:**
- Use `X | Y` union syntax — not `Optional[X]` or `Union[X, Y]`: e.g., `str | None`, `int | None`, `UUID | None`
- `Optional` from `typing` is not used in new code
- `Mapped[...]` for all SQLAlchemy column and relationship declarations
- Full type annotations on function signatures — return types always annotated
- Example from `backend/api/routes/funds.py`:
  ```python
  async def list_funds(
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db_session),
  ) -> list[FundResponse]:
  ```

**Async patterns:**
- All route handlers, service methods, and database operations are `async def`
- SQLAlchemy operations use `await session.execute(stmt)`, `await session.commit()`, `await session.flush()`
- Background work dispatched via FastAPI `BackgroundTasks` for lightweight triggers, Celery for heavy work
- Route handlers that mutate state call `await db.commit()` directly after service call (see `backend/api/routes/funds.py`):
  ```python
  result = await FundService(db, current_user).create_fund(payload)
  await db.commit()
  return result
  ```

**Pydantic schema conventions:**
- All request/response schemas live in `backend/schemas/` — one file per domain: `funds.py`, `ref_data.py`, `deals.py`
- `Create` suffix for create payloads, `Update` for partial updates, `Response` for responses, `ListResponse` for paginated lists
- `ConfigDict(from_attributes=True)` on all `Response` models to enable ORM-mode serialization
- `Field(default_factory=list)` / `Field(default_factory=dict)` for mutable defaults — never bare `[]` or `{}`
- `EmailStr` for validated email fields
- Validation done in schemas; services never re-validate Pydantic-parsed data
- `Update` schemas use all-optional fields (`str | None = None`) to support partial updates:
  ```python
  class FundUpdate(BaseModel):
      fund_name: str | None = None
      fundraise_status_id: str | None = None
  ```

**pydantic-settings:**
- `Settings` in `backend/config.py` inherits `BaseSettings` — reads from `.env` via `SettingsConfigDict(env_file=".env", extra="ignore")`
- Accessed via singleton `settings = get_settings()` — never instantiate `Settings()` directly

**SQLAlchemy 2.0 patterns:**
- All models in `backend/models.py` — single file, all classes in dependency order
- `Mapped[T]` + `mapped_column(...)` for every column — no bare `Column(...)`
- `relationship(back_populates=...)` on both sides of every relationship
- Cascade deletes on child relationships: `cascade="all, delete-orphan"`
- FK delete behavior on `ForeignKey` itself: `ondelete="CASCADE"`, `ondelete="SET NULL"`, `ondelete="RESTRICT"`
- Composite indexes in `__table_args__` as `Index(...)` tuples
- `UniqueConstraint` with explicit `name` parameter on every unique constraint
- Queries use SQLAlchemy Core `select(Model)` + `await session.execute(stmt)` — never `session.query()`
- Multi-join queries use `aliased(RefData)` for disambiguation:
  ```python
  FundStatusRef = aliased(RefData)
  TxnType = aliased(RefData)
  ```

**Service layer:**
- Services are classes initialized with `(db: AsyncSession, current_user: User)` — stored as `self.db` / `self.current_user`
- Route handlers instantiate services inline: `FundService(db, current_user).list_funds()`
- Services raise `HTTPException` directly — no custom exception hierarchy
- Org scoping via `Fund.org_id == self.current_user.org_id` in all queries
- Resources not belonging to user's org return `404`, not `403` (prevents org ID disclosure)

**Environment variable naming:**
- `SCREAMING_SNAKE_CASE` for all env vars
- Database: `DATABASE_URL`, `DATABASE_URL_SYNC`
- Auth: `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- Redis: `REDIS_URL`
- LinkedIn: `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`
- Frontend/Vite: `VITE_APP_ENV` (checked at runtime: `import.meta.env.VITE_APP_ENV === 'production'`)
- Secrets managed in AWS Secrets Manager under `/nexus/{env}/` prefix in production

---

## Import Organization

**Python order (enforced by ruff):**
1. `from __future__ import annotations`
2. Standard library (`datetime`, `uuid`, `typing`, etc.)
3. Third-party (`fastapi`, `sqlalchemy`, `pydantic`, etc.)
4. Internal (`backend.models`, `backend.schemas.funds`, etc.)

All internal imports use the full package path — no relative imports.

**Frontend import order (consistent across files):**
1. React and React ecosystem (`react`, `react-router-dom`, `@tanstack/react-query`)
2. Icon libraries (`lucide-react`)
3. Toast (`sonner`)
4. Internal API modules (`@/api/deals`, `@/api/funds`)
5. Internal shared components (`@/components/RefSelect`, `@/components/ui/button`)
6. Internal hooks (`@/hooks/useRefData`, `@/hooks/useAuth`)
7. Internal stores (`@/store/useUIStore`)
8. Internal utilities (`@/lib/utils`, `@/lib/refCategories`)

The `@` alias maps to `frontend/src/` (configured in `frontend/vite.config.js`).

---

## Error Handling

**Backend:**
- Services raise `fastapi.HTTPException` with explicit `status_code` and `detail` string
- `status.HTTP_404_NOT_FOUND`, `status.HTTP_403_FORBIDDEN`, `status.HTTP_400_BAD_REQUEST` used from `fastapi`
- Org scoping: resources not in the user's org return 404, not 403 (information disclosure prevention)
- No try/except in route handlers — FastAPI propagates `HTTPException` to response automatically
- Pattern from `backend/services/funds.py`:
  ```python
  if fund is None:
      raise HTTPException(status_code=404, detail="Fund not found")
  ```

**Frontend:**
- Mutations use `onError: (error) => toast.error(error.response?.data?.detail || 'Fallback message')`
- The Axios client in `frontend/src/api/client.js` attaches auth headers via a request interceptor
- No global error boundary — errors surface via `sonner` toast notifications

---

## Logging

**Backend:**
- Structured JSON logging via `structlog` (with `logging` stdlib fallback) — `backend/utils/structured_logging.py`
- Every log entry carries `request_id`, `user_id`, `org_id` from `ContextVar` set by middleware
- Log fields: `timestamp`, `level`, `logger`, `method`, `path`, `status_code`, `latency_ms`, `event`
- Use the module logger (`logging.getLogger(__name__)`) — never `print()`

---

## Git Conventions

**Branch naming:**
No enforced branch naming pattern found. All active work has been committed directly to `main`.

**Commit message format:**
Conventional Commits style — enforced by practice, not tooling:

```
<type>(<scope>): <description>
```

Types in active use:
- `feat` — new feature or component
- `fix` — bug fix or correction
- `docs` — planning documents, summaries, analysis
- `test` — new or modified test files
- `chore` — scaffolding, file moves, non-functional changes
- `refactor` — code restructuring without behavior change
- `style` — CSS/visual changes
- `context` — phase context capture (GSD-specific)
- `wip` — work-in-progress checkpoints

Scope is typically the phase number or feature area: `(13-03)`, `(phase-08)`, `(08-02)`.

Examples from git log:
```
feat(13-03): wire environments, inline ECR, fix entrypoint, add Makefile targets
test(08-02): add Layout.test.jsx smoke tests for sidebar structure
docs(13-01): complete terraform bootstrap and environment structure plan
chore(13-01): create terraform bootstrap and environment directory skeleton
fix(13): revise plans based on checker feedback
```

No `--no-verify` bypassing or commit signing suppression is used.

---

## Comments

**When to comment:**
- Complex SQL joins or query disambiguation (e.g., `# Aliases for multi-join disambiguation (PE fields)`)
- Security enforcement logic (org scoping, role checks)
- Non-obvious fallback patterns (e.g., `try/except ImportError` stubs)
- Test docstrings: one-line description of the scenario being tested, e.g.:
  ```python
  """PATCH with PE scalar fields — they persist and GET returns them correctly."""
  ```

**What not to comment:**
- No JSDoc/TSDoc in the frontend — the codebase uses vanilla JSX without TypeScript
- No comments restating what the code obviously does

---

## Frontend Component Design

**Page components** (`frontend/src/pages/`):
- Own their data-fetching via `useQuery`/`useMutation` from `@tanstack/react-query` directly
- Use `useParams` for route-based IDs, `useSearchParams` for filter state
- Form validation via `react-hook-form` + `zodResolver` — schema defined at module top-level
- Multiple sub-queries kept in-page rather than extracted to hooks

**Shared components** (`frontend/src/components/`):
- Named exports with `PascalCase` function name (not default exports): `export function RefSelect(...)`
- Accept `className` prop and merge with `cn()` from `@/lib/utils`
- Handle loading, error, and empty states explicitly (see `RefSelect.jsx`)

**Hooks** (`frontend/src/hooks/`):
- Thin wrappers around `useQuery` — e.g., `useRefData(category)` calls `useQuery` with a `['ref', category]` query key and 5-minute `staleTime`
- Complex hooks with multiple queries stay in-page

**State management split:**
- Server state: TanStack Query (queries + mutations with `queryClient.invalidateQueries`)
- Client/UI state: Zustand stores in `frontend/src/store/` — currently `useUIStore.js` (sidebar collapse state)
- Local ephemeral state: `useState` in-component

**TanStack Query key patterns:**
- Arrays with domain prefix: `['ref', category]`, `['deals', dealId]`, `['deal-score', dealId]`
- Invalidate by prefix on mutation success: `queryClient.invalidateQueries({ queryKey: ['contacts'] })`
- `retry: false` in tests; production defaults used in app

---

## Linting and Formatting

**Python:**
- `ruff check backend/` — linter (replaces flake8/isort)
- `ruff format backend/` — formatter
- `black backend/` — additional formatting pass (both `ruff format` and `black` are run in `make format`)
- `mypy backend/ --ignore-missing-imports` — type checking
- Run via `make lint` and `make format`
- No `# noqa` or `# type: ignore` suppression comments found in the codebase

**Frontend:**
- No ESLint or Prettier config files in the repository
- No enforced frontend linting configured
- Vitest globals enabled (`globals: true` in `frontend/vite.config.js`) — `vi`, `describe`, `it`, `expect`, `beforeEach`, `afterEach` available without imports in most test files (some files import them explicitly — both styles appear)

---

*Convention analysis: 2026-04-06*
