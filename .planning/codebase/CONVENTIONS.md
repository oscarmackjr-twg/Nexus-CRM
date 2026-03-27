# Coding Conventions

**Analysis Date:** 2026-03-26

## Naming Patterns

**Python files:**
- Modules are `snake_case`: `contacts.py`, `deal_scoring.py`, `sql_validator.py`
- Test files are prefixed `test_`: `test_crm_core.py`, `test_permissions.py`
- Service classes match their domain noun: `ContactService`, `DealService`

**Python functions and methods:**
- `snake_case` for all functions: `list_contacts`, `create_access_token`, `hash_password`
- Private helpers prefixed with underscore: `_base_stmt`, `_contact_response`, `_utcnow`, `_build_fernet`
- Static helpers on service classes use `@staticmethod` decorator

**Python variables:**
- `snake_case` throughout: `org_id`, `hashed_password`, `lifecycle_stage`
- Boolean columns are prefixed `is_`: `is_active`, `is_archived`, `is_private`
- Timestamps use `_at` suffix: `created_at`, `updated_at`, `occurred_at`, `last_login`
- Foreign key columns use `_id` suffix: `org_id`, `team_id`, `owner_id`

**Python types:**
- `PascalCase` for Pydantic models and SQLAlchemy model classes: `ContactCreate`, `ContactResponse`, `ContactListResponse`
- Type aliases at module level: `JSONVariant`, `StringList` in `backend/models.py`

**Frontend files:**
- React components: `PascalCase.jsx` — `ContactsPage.jsx`, `KanbanBoard.jsx`, `DealCard.jsx`
- Hooks: `camelCase.js` prefixed with `use` — `useContacts.js`, `useDebounce.js`, `useTeamScope.js`
- API modules: `camelCase.js` matching domain — `contacts.js`, `deals.js`, `pipelines.js`
- Zustand stores: `useNounStore.js` — `useAuthStore.js`, `useContactStore.js`, `usePipelineStore.js`
- UI primitives: `kebab-case.jsx` under `components/ui/` — `button.jsx`, `dropdown-menu.jsx`

**Frontend variables and functions:**
- `camelCase` for all JS identifiers: `getContacts`, `createContact`, `debouncedSearch`
- React components export as default with `PascalCase` function name
- Custom hooks return objects, not arrays (except `useState` mirroring)

## Python Style

**Future annotations:**
All Python files open with `from __future__ import annotations` — this is mandatory. It enables PEP 563 postponed evaluation so `Mapped[list["Deal"]]` forward references resolve without quotes.

**Typing:**
- Use `X | Y` union syntax (not `Optional[X]` or `Union[X, Y]`) — e.g., `str | None`, `int | None`
- `Optional` from `typing` is only imported in legacy spots; new code uses `X | None`
- `Mapped[...]` for all SQLAlchemy column and relationship declarations
- Full type annotations on function signatures — return types always annotated
- Example from `backend/auth/security.py`:
  ```python
  def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
  ```

**Async patterns:**
- All route handlers, service methods, and database operations are `async def`
- SQLAlchemy operations use `await session.execute(stmt)`, `await session.commit()`, `await session.flush()`
- Background work is dispatched via FastAPI `BackgroundTasks` for lightweight triggers, Celery for heavy work
- Example pattern from `backend/api/routes/contacts.py`:
  ```python
  async def create_contact(
      payload: ContactCreate,
      background_tasks: BackgroundTasks,
      current_user: User = Depends(get_current_user),
      db: AsyncSession = Depends(get_db_session),
  ) -> ContactResponse:
      response = await ContactService(db, current_user).create_contact(payload)
      background_tasks.add_task(fire_trigger, "contact_created", {...}, str(current_user.org_id))
      return response
  ```

**Pydantic usage:**
- All request/response schemas live in `backend/schemas/` — one file per domain
- `Create` suffix for create payloads, `Update` for partial updates, `Response` for responses, `ListResponse` for paginated lists
- `ConfigDict(from_attributes=True)` on all `Response` models to enable ORM-mode serialization
- `Field(default_factory=list)` and `Field(default_factory=dict)` for mutable defaults — never bare `[]` or `{}`
- `EmailStr` used for validated email fields
- Validation done in schemas; services never re-validate Pydantic-parsed data
- Example from `backend/schemas/contacts.py`:
  ```python
  class ContactResponse(BaseModel):
      model_config = ConfigDict(from_attributes=True)
      id: UUID
      tags: list[str]
      custom_fields: dict = Field(default_factory=dict)
  ```

**pydantic-settings:**
- `Settings` in `backend/config.py` inherits `BaseSettings` and reads from `.env` via `SettingsConfigDict(env_file=".env", extra="ignore")`
- Accessed via the singleton `settings = get_settings()` — never instantiate `Settings()` directly

**SQLAlchemy 2.0 patterns:**
- All models in `backend/models.py` — single file, all classes in dependency order
- Use `Mapped[T]` + `mapped_column(...)` for every column — no `Column(...)` without `mapped_column`
- Use `relationship(back_populates=...)` on both sides of every relationship
- Cascade deletes on child relationships: `cascade="all, delete-orphan"`
- Foreign key delete behavior declared on the `ForeignKey` itself: `ondelete="CASCADE"`, `ondelete="SET NULL"`, `ondelete="RESTRICT"`
- Composite indexes declared in `__table_args__` as `Index(...)` tuples
- `UniqueConstraint` with an explicit `name` parameter for every unique constraint
- Queries use SQLAlchemy Core `select(Model)` + `await session.execute(stmt)` — never `session.query()`
- Example from `backend/database.py`:
  ```python
  async def get_db_session() -> AsyncIterator[AsyncSession]:
      session_factory = get_session_maker()
      async with session_factory() as session:
          yield session
  ```

**Service layer:**
- Services are classes initialized with `(db: AsyncSession, current_user: User)` and stored as `self.db` / `self.current_user`
- Route handlers instantiate services inline: `ContactService(db, current_user).list_contacts(...)`
- Services raise `HTTPException` directly — no custom exception hierarchy

## Import Organization

**Python order (enforced by ruff):**
1. `from __future__ import annotations`
2. Standard library (`datetime`, `uuid`, `typing`, etc.)
3. Third-party (`fastapi`, `sqlalchemy`, `pydantic`, etc.)
4. Internal (`backend.models`, `backend.schemas.contacts`, etc.)

All internal imports use the full package path — no relative imports.

**Frontend order (consistent across files):**
1. React and React ecosystem (`react`, `react-router-dom`, `@tanstack/react-query`)
2. Form libraries (`react-hook-form`, `zod`, `@hookform/resolvers/zod`)
3. Icon and UI primitives (`lucide-react`, `sonner`)
4. Internal API modules (`@/api/contacts`)
5. Internal UI components (`@/components/ui/button`)
6. Internal hooks (`@/hooks/useDebounce`)
7. Internal store (`@/store/useContactStore`)
8. Internal utilities (`@/lib/utils`)

The `@` alias maps to `frontend/src/` (configured in `vite.config.js`).

## Error Handling

**Backend:**
- Services raise `fastapi.HTTPException` with explicit `status_code` and `detail` string
- `status.HTTP_404_NOT_FOUND`, `status.HTTP_403_FORBIDDEN`, `status.HTTP_400_BAD_REQUEST` are used from `fastapi`
- Org scoping: resources not belonging to the user's org return 404, not 403 (prevents information disclosure)
- No try/except in route handlers — let FastAPI propagate HTTPException
- Optional external dependencies wrapped in `try/except ImportError` with a runtime fallback class

**Frontend:**
- Mutations use `onError: (error) => toast.error(error.response?.data?.detail || 'Fallback message')`
- The Axios client in `frontend/src/api/client.js` attaches auth headers via a request interceptor
- No global error boundary in the codebase — errors surface via toast notifications

## Logging

**Backend:**
- Structured JSON logging via `structlog` (with `logging` stdlib fallback) — see `backend/utils/structured_logging.py`
- Every log entry carries `request_id`, `user_id`, `org_id` from `ContextVar` — set by middleware
- Log fields: `timestamp`, `level`, `logger`, `method`, `path`, `status_code`, `latency_ms`, `event`
- Use the module logger (`logging.getLogger(__name__)`) — never `print()`

## Comments

When to comment:
- Complex SQL joins or performance-sensitive queries
- Security enforcement logic (org scoping, role checks)
- Non-obvious fallback patterns (e.g., the `try/except ImportError` stubs)
- No JSDoc/TSDoc in the frontend — the codebase uses vanilla JSX without TypeScript

## Frontend Component Design

**Page components** (`frontend/src/pages/`):
- Own their data-fetching via `useQuery`/`useMutation` directly, or through thin wrapper hooks in `frontend/src/hooks/`
- Use `useSearchParams` for filter state that should be bookmarkable
- Use Zustand store for cross-page state (active filters, selected IDs)
- Form validation via `react-hook-form` + `zodResolver` — schema defined at module top-level

**Hooks:**
- Thin wrappers around `useQuery` live in `frontend/src/hooks/` — e.g., `useContacts(params)` simply calls `useQuery({ queryKey: ['contacts', params], queryFn: ... })`
- Complex hooks with multiple queries stay in-page

**State management split:**
- Server state: TanStack Query (queries + mutations with `queryClient.invalidateQueries`)
- Client/UI state: Zustand stores in `frontend/src/store/`
- Local ephemeral state: `useState` in-component

**TanStack Query patterns:**
- Query keys are arrays: `['contacts', params]`, `['users']`, `['deals', dealId]`
- Invalidate by prefix on mutation success: `queryClient.invalidateQueries({ queryKey: ['contacts'] })`
- `retry: false` in tests; production defaults used in app

## Linting and Formatting

**Python:**
- `ruff check backend/` — linter (replaces flake8/isort)
- `ruff format backend/` — formatter (replaces black for formatting pass)
- `black backend/` — additional formatting pass (both ruff format and black are run in `make format`)
- `mypy backend/ --ignore-missing-imports` — type checking
- Run via `make lint` and `make format`

**Frontend:**
- No ESLint or Prettier config files detected — no enforced frontend linting configured
- Vitest globals enabled (`globals: true` in `vite.config.js`) so `vi`, `describe`, `it`, `expect` are available without imports in test files
