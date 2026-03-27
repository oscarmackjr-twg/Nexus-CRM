# Codebase Concerns

**Analysis Date:** 2026-03-26

---

## Security

### SECRET_KEY default is "change-me-in-production"
- **Severity:** HIGH
- Issue: `SECRET_KEY` defaults to the literal string `"change-me-in-production"` in `backend/config.py:13`. The same key is used for both JWT signing and the Fernet cipher that encrypts LinkedIn OAuth tokens (`backend/auth/security.py:45-46`). If `.env` is absent or incomplete in any environment, all tokens issued are trivially forgeable and all stored LinkedIn tokens are decryptable by anyone who reads the source.
- Files: `backend/config.py:13`, `backend/auth/security.py:44-46`
- Fix approach: Add a startup assertion that `SECRET_KEY != "change-me-in-production"` when `ENVIRONMENT == "production"`. Rotate the key and re-encrypt stored LinkedIn tokens on first valid deploy.

### No rate limiting on `/auth/login` or `/auth/register`
- **Severity:** HIGH
- Issue: The slowapi `Limiter` is conditionally installed at the app level (`backend/api/main.py:71-75`), but no `@limiter.limit(...)` decorator is applied to `POST /auth/login` or `POST /auth/register` in `backend/api/routes/auth.py`. The custom `check_rate_limit` utility (`backend/auth/rate_limiter.py`) is only wired in `backend/api/routes/ai_query.py`. Brute-force and credential-stuffing attacks against the login endpoint are entirely unrestricted.
- Files: `backend/api/routes/auth.py:136-149`, `backend/api/routes/auth.py:152-193`, `backend/api/main.py:71-75`
- Fix approach: Apply `@limiter.limit("10/minute")` (or equivalent) to `login` and `register`, or call `check_rate_limit` from those endpoints the same way `ai_query.py` does.

### JWT tokens stored in `localStorage`
- **Severity:** MEDIUM
- Issue: Both the access token and refresh token are persisted to `localStorage` (`frontend/src/store/useAuthStore.js:20-27`). A duplicate write also lands in `localStorage.setItem('nexus_token', ...)` at line 27. `localStorage` is readable by any same-origin JavaScript, including injected third-party scripts. XSS compromises both tokens simultaneously.
- Files: `frontend/src/store/useAuthStore.js:19-27`
- Fix approach: Store the refresh token in an `HttpOnly` cookie (set by the server). Keep the short-lived access token in memory only (Zustand state, not persisted), and rely on the silent-refresh flow to rehydrate on page load.

### CSP allows `unsafe-inline` scripts and styles
- **Severity:** MEDIUM
- Issue: `SecurityHeadersMiddleware` sets `script-src 'self' 'unsafe-inline'` and `style-src 'self' 'unsafe-inline'` (`backend/api/middleware.py:48-50`). This effectively disables the XSS mitigation that a strict CSP provides.
- Files: `backend/api/middleware.py:45-51`
- Fix approach: Use a nonce-based or hash-based CSP for scripts. Inline styles driven by Tailwind can use a build-time hash list or be replaced with stylesheet classes.

### Inbound webhook endpoint has no authentication
- **Severity:** MEDIUM
- Issue: `POST /api/v1/webhooks/inbound/{automation_id}` accepts arbitrary JSON payloads and immediately queues an automation run (`backend/api/routes/webhooks.py:13-21`). There is no HMAC signature check, shared secret, or IP allowlist. Any caller who knows (or can enumerate) a valid automation UUID can trigger automation runs against any org.
- Files: `backend/api/routes/webhooks.py:13-21`
- Fix approach: Add an `X-Webhook-Secret` header check against a per-automation secret stored in `trigger_config`, or require a signed JWT as a query parameter.

### `METRICS_API_KEY` has a hardcoded default value
- **Severity:** LOW
- Issue: `METRICS_API_KEY` defaults to `"internal-metrics-key"` (`backend/config.py:31`). In production the gate at `backend/api/main.py:169-170` compares against this default, meaning anyone who reads the source can poll `/metrics` and enumerate internal counters.
- Files: `backend/config.py:31`, `backend/api/main.py:168-173`
- Fix approach: Require `METRICS_API_KEY` to be set explicitly in production, same as `SECRET_KEY`.

---

## Unimplemented Stubs

### Analytics routes return `not_implemented`
- **Severity:** HIGH
- Issue: Three analytics endpoints that the frontend actively calls return `{"status": "not_implemented", "phase": 0}` with a 200 status, causing silent UI failures. `AnalyticsPage.jsx` renders "Forecast endpoint returned fallback status: not_implemented" and the velocity card shows "N/A" because the response body never contains real data.
  - `GET /api/v1/analytics/pipeline-velocity` — `backend/api/routes/analytics.py:36-38`
  - `GET /api/v1/analytics/forecast` — `backend/api/routes/analytics.py:40-42`
  - `GET /api/v1/analytics/leaderboard` — `backend/api/routes/analytics.py:44-46`
- Files: `backend/api/routes/analytics.py:36-46`, `frontend/src/pages/AnalyticsPage.jsx:18`, `frontend/src/pages/AnalyticsPage.jsx:24-25`
- Fix approach: Implement using `backend/services/analytics_service.py` (currently an empty class). The math primitives in `backend/math/pipeline_forecast.py` and `backend/math/deal_scoring.py` already exist; leaderboard and velocity are SQL aggregates.

### Email sync Celery task is a stub
- **Severity:** HIGH
- Issue: `backend/workers/email_sync.py` contains a single task that returns `{"status": "not_implemented"}`. Any automation action that depends on email sync, or any future email workflow, silently does nothing.
- Files: `backend/workers/email_sync.py:4-6`
- Fix approach: Implement SendGrid inbound parsing or polling. `settings.SENDGRID_API_KEY` is already defined in `backend/config.py:30`.

### `EmailService` class body is empty
- **Severity:** MEDIUM
- Issue: `backend/services/email_service.py` defines `EmailService` with only `self.name = "email_service"`. Nothing can be sent or received through it.
- Files: `backend/services/email_service.py:1-3`
- Fix approach: Implement send/receive methods using the SendGrid SDK before wiring into automations.

### `AnalyticsService` class body is empty
- **Severity:** MEDIUM
- Issue: `backend/services/analytics_service.py` contains only `self.name = "analytics_service"`. The stub analytics routes above have no service to delegate to.
- Files: `backend/services/analytics_service.py:1-3`
- Fix approach: Implement once the analytics route stubs are being filled.

### Win/loss chart uses static hardcoded data
- **Severity:** LOW
- Issue: `AnalyticsPage.jsx` renders a "Win / loss rate over time" line chart from a hardcoded 4-month array (`frontend/src/pages/AnalyticsPage.jsx:36-43`). This data is never fetched and never changes regardless of actual deal outcomes.
- Files: `frontend/src/pages/AnalyticsPage.jsx:36-43`
- Fix approach: Derive from real deal data grouped by `actual_close_date` month, or add a dedicated backend endpoint.

---

## Infrastructure and Deployment

### Docker Compose has no healthcheck — backend may start before postgres is ready
- **Severity:** HIGH
- Issue: `deploy/docker-compose.yml` uses `depends_on: postgres` without a `condition: service_healthy` clause. No `healthcheck` block is defined for the `postgres` or `redis` services. `entrypoint.sh` runs `alembic upgrade head` immediately on startup, which fails with a connection error if postgres is still initialising. The same race applies to the worker container.
- Files: `deploy/docker-compose.yml:3-62`, `deploy/entrypoint.sh:9`
- Fix approach: Add a `healthcheck` block to the `postgres` service (e.g. `pg_isready -U nexus`) and change the `backend` and `worker` `depends_on` entries to `condition: service_healthy`.

### Postgres credentials hardcoded in `docker-compose.yml`
- **Severity:** MEDIUM
- Issue: `deploy/docker-compose.yml:8-10` sets `POSTGRES_PASSWORD: nexus` in plain text. Even as a dev-only default, committing credentials to source control normalises the practice and risks a copy-paste into production environments.
- Files: `deploy/docker-compose.yml:8-10`
- Fix approach: Replace with `${POSTGRES_PASSWORD}` referencing the existing `.env` file (which is already mounted via `env_file`), or add a clear comment marking this as dev-only and assert a non-default password at deploy time.

### Frontend container runs `npm install` on every startup
- **Severity:** LOW
- Issue: `deploy/docker-compose.yml:53` uses `command: sh -c "npm install && npm run dev"`. This re-downloads all packages on every container start, making local restarts slow and dependent on network availability.
- Files: `deploy/docker-compose.yml:49-59`
- Fix approach: Move `npm install` into a Dockerfile build stage so the layer is cached between runs.

---

## Frontend Architecture

### Dashboard makes 4+ parallel API calls with no dedicated endpoint
- **Severity:** MEDIUM
- Issue: `DashboardPage.jsx` issues at minimum 4 concurrent requests (`getDeals`, `getContacts`, `getBoards`, `getAISuggestions`) and then fans out to up to 3 additional `getBoard` detail calls (`frontend/src/pages/DashboardPage.jsx:34-42`). The deals and contacts calls request up to 100 records each purely for client-side aggregation. This is expensive at scale and causes the dashboard to be slow on first load.
- Files: `frontend/src/pages/DashboardPage.jsx:31-43`
- Fix approach: Add a `GET /api/v1/dashboard` endpoint that returns pre-aggregated stats in a single query (total open value, win rate, stage distribution, etc.) instead of shipping raw record sets to the client.

### No token refresh interceptor — expired access tokens are not auto-refreshed
- **Severity:** MEDIUM
- Issue: `frontend/src/api/client.js` has only a request interceptor that attaches the stored token. There is no response interceptor to catch `401` responses, call `POST /auth/refresh`, and retry the original request. When the 8-hour access token expires (`ACCESS_TOKEN_EXPIRE_MINUTES: 480` in `backend/config.py:15`), all API calls silently fail until the user manually logs out and back in.
- Files: `frontend/src/api/client.js:1-13`, `backend/config.py:15`
- Fix approach: Add an Axios response interceptor in `client.js` that detects `401`, calls `POST /api/v1/auth/refresh` with the stored `refreshToken`, updates the auth store, and retries the original request once.

### Mobile API client stores token on `globalThis` — no persistence or auth flow
- **Severity:** MEDIUM
- Issue: `mobile/src/api/client.js:8` reads the auth token from `globalThis.__NEXUS_MOBILE_TOKEN__`. This is a global variable with no documented write path in the mobile codebase. On app reload, the token is lost and no login flow is triggered. The mobile app has no auth screen and no token refresh logic.
- Files: `mobile/src/api/client.js:8`
- Fix approach: Implement token storage using `expo-secure-store`, add a `LoginScreen`, and add a 401-interceptor analogous to the web client fix described above.

---

## Tech Debt

### `Base.metadata.create_all` runs on every app startup alongside Alembic
- **Severity:** MEDIUM
- Issue: `backend/api/main.py:43-44` calls `await conn.run_sync(Base.metadata.create_all)` during the lifespan startup. In production, Alembic migrations (run by `entrypoint.sh:9`) are the source of truth for schema. Running `create_all` after migrations can silently add untracked columns or indexes that Alembic does not know about, causing drift between the migration history and the actual database schema.
- Files: `backend/api/main.py:43-44`, `deploy/entrypoint.sh:9`
- Fix approach: Remove the `create_all` call from `lifespan`. Rely entirely on `alembic upgrade head`. For dev/test convenience, use a pytest fixture or Makefile target to apply migrations on a fresh database.

### Alembic initial migration delegates entirely to `create_all`
- **Severity:** MEDIUM
- Issue: `alembic/versions/0001_initial.py` implements `upgrade()` by calling `models.Base.metadata.create_all(bind)`. This means the first migration is not idempotent, cannot be re-run safely on a partially-created schema, and gives Alembic no record of individual table definitions, making future auto-generated migrations unreliable.
- Files: `alembic/versions/0001_initial.py:14-16`
- Fix approach: Replace with explicit `op.create_table(...)` calls generated by `alembic revision --autogenerate` against a clean empty database.

### `apply_tag_filter` uses `LIKE '%tag%'` — not tag-exact
- **Severity:** MEDIUM
- Issue: Tag filtering in `backend/services/_crm.py:154-158` matches tags by casting the JSON/ARRAY column to text and using `LIKE '%tag%'`. A search for tag `"enterprise"` would match rows containing tags like `"enterprise-trial"` or any tag value that contains the substring. This makes tag filtering semantically incorrect.
- Files: `backend/services/_crm.py:154-158`, `backend/services/deals.py:204`, `backend/services/contacts.py:104`, `backend/services/companies.py:92`
- Fix approach: For PostgreSQL, use the `@>` array containment operator or `ANY`. For SQLite, use `JSON_EACH` with an exact match. Add a `dialect_name` branch as done in `deal_activity_subqueries` in the same file.

### `configure_database` mutates the lru_cache-frozen `Settings` object
- **Severity:** MEDIUM
- Issue: `backend/database.py:31-38` defines `configure_database(url)` which reassigns `current.DATABASE_URL` directly on the `Settings` instance returned by `get_settings()`. Because `get_settings` uses `@lru_cache(maxsize=1)`, this mutates the shared singleton and makes test isolation fragile — a test that calls `configure_database` affects all subsequent calls to `get_settings()` in the same process.
- Files: `backend/database.py:31-38`, `backend/config.py:37-42`
- Fix approach: Accept an explicit `AsyncEngine` parameter in functions that need a test database, rather than mutating global config. The test conftest already uses `configure_database`; the fix would require updating the conftest too.

### Audit log is stored in-process memory only
- **Severity:** MEDIUM
- Issue: `backend/api/middleware.py:14` defines `_AUDIT_LOGS` as a module-level `defaultdict`. All audit entries are stored in the API process's heap, capped at 10,000 per org. Entries are lost on process restart, invisible to the worker process, and not queryable by org admins. There is no admin-facing endpoint to retrieve them.
- Files: `backend/api/middleware.py:14`, `backend/api/middleware.py:74-96`
- Fix approach: Write audit events to a `audit_logs` database table or a structured log stream. Expose a paginated `GET /api/v1/orgs/{org_id}/audit` endpoint gated on `require_org_admin`.

### `_rate_limit_memory` in `ai_query.py` is per-process — not shared across replicas
- **Severity:** LOW
- Issue: `backend/api/routes/ai_query.py:30` defines `_rate_limit_memory` as a module-level dict used as the Redis fallback in `_enforce_query_rate_limit`. In a multi-process or multi-replica deployment, each process has its own counter, so the effective rate limit is `N * 30` requests per minute where N is the replica count.
- Files: `backend/api/routes/ai_query.py:30`, `backend/api/routes/ai_query.py:51-57`
- Fix approach: Treat Redis as a hard dependency for rate limiting. Surface a startup health-check failure if Redis is unreachable rather than silently degrading to a per-process counter.

### Cron automations registered in-process — lost on restart
- **Severity:** LOW
- Issue: Scheduled automation jobs are managed by an in-process APScheduler `BackgroundScheduler` instance (`backend/services/automations.py:55-57`). On process restart, no cron jobs are re-registered from the database, so any automation with `trigger_type == "schedule_cron"` stops firing silently after a redeploy.
- Files: `backend/services/automations.py:54-57`, `backend/services/automations.py:93-114`
- Fix approach: On startup, query all active automations with cron triggers and call `register_cron_job` for each, or replace APScheduler with Celery Beat which persists schedules externally.

### N+1 query in `get_proactive_suggestions`
- **Severity:** LOW
- Issue: `backend/services/ai_service.py:476-478` fetches stale deals in one query then loops over the results and issues an additional `SELECT Deal.team_id` per row to re-filter by `visible_team_ids`. This is an N+1 pattern adding one round-trip per stale deal returned.
- Files: `backend/services/ai_service.py:467-478`
- Fix approach: Push the `Deal.team_id.in_(visible_team_ids)` predicate into the original stale-deal query before execution, as is done in `backend/services/deals.py:73-78`.

---

## Test Coverage Gaps

### No tests for analytics routes or their stub state
- **Severity:** MEDIUM
- Issue: The test suite covers auth, CRM core, boards, LinkedIn, security, and permissions, but there are no tests in `backend/tests/` for `backend/api/routes/analytics.py`. Stub endpoints returning HTTP 200 with a `not_implemented` body would pass any naive existence test.
- Files: `backend/api/routes/analytics.py`, `backend/tests/` (absent file)
- Priority: Medium — add tests that assert stub routes are either implemented or explicitly flagged, and add contract tests for `overview`.

### Mobile app has no tests whatsoever
- **Severity:** LOW
- Issue: The `mobile/` directory contains no test files and no test configuration. All six screen components and the API client are entirely untested.
- Files: `mobile/` (all source files)
- Risk: Regressions in mobile screens or the `globalThis` token pattern would go undetected.

---

## Previously Fixed (Confirmed Resolved)

The following issues were identified as patched and are confirmed resolved in the current codebase:

- **`self.db.bind` SQLAlchemy 2.0 incompatibility** — Both `backend/services/deals.py:51` and `backend/services/ai_service.py:468` now call `get_engine().dialect.name` directly. No remaining `self.db.bind` references found.
- **DashboardPage toast fired on every render** — `frontend/src/pages/DashboardPage.jsx:45-49` correctly wraps the toast call in `useEffect` with `[dashboardQuery.isError]` as the dependency array, firing only on error state transitions.

---

*Concerns audit: 2026-03-26*
