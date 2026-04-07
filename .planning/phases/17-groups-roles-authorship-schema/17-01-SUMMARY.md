---
phase: 17-groups-roles-authorship-schema
plan: 01
subsystem: database
tags: [alembic, sqlalchemy, rbac, postgresql, authorship, migration]

# Dependency graph
requires:
  - phase: 05-deal-counterparty-deal-funding
    provides: DealCounterparty and DealFunding ORM models (targets for authorship columns)
  - phase: 04-deal-model-expansion-fund-entity
    provides: Fund ORM model (needs updated_at + authorship columns)
provides:
  - Alembic migration 0012 adding Team.is_active, authorship columns on 6 entities, role rename data migration
  - ORM models updated with created_by/updated_by nullable FKs on Contact, Company, Deal, Fund, DealCounterparty, DealFunding
  - All route guards and role checks using new role strings (admin, supervisor, principal, regular_user)
  - Fund.updated_at column (was previously missing)
  - Team.is_active column
affects: [18-access-enforcement, 19-call-note-entities, 20-audit-history, 21-principal-reports]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Authorship pattern: nullable created_by/updated_by UUID FKs with ondelete=SET NULL"
    - "Role rename via Alembic data migration (UPDATE users SET role = ...)"
    - "entrypoint.sh passes $@ args allowing docker-compose run --rm backend pytest to work"

key-files:
  created:
    - alembic/versions/0012_v13_groups_roles_authorship.py
  modified:
    - backend/models.py
    - backend/auth/security.py
    - backend/api/routes/admin.py
    - backend/api/routes/auth.py
    - backend/services/_crm.py
    - backend/seed_data.py
    - backend/tests/conftest.py
    - backend/tests/test_deals_pe.py
    - backend/tests/test_funds.py
    - backend/tests/test_ref_data.py
    - frontend/src/pages/AdminPage.jsx
    - frontend/src/__tests__/Layout.test.jsx
    - deploy/entrypoint.sh

key-decisions:
  - "Use sa.types.Uuid() (not postgresql.UUID) for authorship FK columns in migration — SQLite compat for tests"
  - "Authorship columns are nullable with ondelete=SET NULL — NULL means created before Phase 17"
  - "require_org_admin kept as function name (backward compat) but updated to check admin role only"
  - "entrypoint.sh fixed to pass $@ args — enables docker-compose run --rm backend pytest"
  - "pre-existing test failures (ai_query monkeypatch, event loop) confirmed pre-17 and out of scope"

patterns-established:
  - "New role strings: admin (was super_admin/org_admin), supervisor (was team_manager), regular_user (was rep/member/viewer), principal (new)"
  - "require_role('admin') replaces require_org_admin() in route guards"
  - "is_admin() checks ('admin',) only; is_manager_plus() checks ('supervisor', 'admin')"

requirements-completed: [GROUP-01, AUDIT-01, AUDIT-02, GROUP-06]

# Metrics
duration: 35min
completed: 2026-04-07
---

# Phase 17 Plan 01: Groups, Roles & Authorship Schema — Foundation Summary

**Alembic migration 0012 adds Team.is_active, authorship columns (created_by/updated_by) to 6 entities, and renames all role strings (super_admin/org_admin→admin, team_manager→supervisor, rep/member/viewer→regular_user) via data migration**

## Performance

- **Duration:** 35 min
- **Started:** 2026-04-07T17:51:32Z
- **Completed:** 2026-04-07T18:27:00Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments

- Created migration 0012 with DDL for is_active on teams, created_by/updated_by on 6 entities, updated_at on funds, and data migration renaming all role values
- Updated all 6 ORM models with nullable authorship FK columns; User.role default changed to regular_user
- Eliminated all old role strings (super_admin, org_admin, team_manager, rep, viewer) from production code, test fixtures, seed data, and frontend

## Task Commits

1. **Task 1: Alembic migration + ORM model updates** - `25d498b` (feat)
2. **Task 2: Role string updates across backend, frontend, tests, and seed data** - `93fa6f4` (feat)

## Files Created/Modified

- `alembic/versions/0012_v13_groups_roles_authorship.py` - New migration: Team.is_active, authorship columns, role rename data migration
- `backend/models.py` - Team.is_active, Contact/Company/Deal/DealCounterparty/DealFunding authorship columns, Fund.updated_at, User.role default=regular_user
- `backend/auth/security.py` - require_org_admin now checks admin role only
- `backend/api/routes/admin.py` - require_role("admin") replaces org_admin/super_admin guards
- `backend/api/routes/auth.py` - require_org_admin replaced with require_role("admin") on create/delete user endpoints; super_admin→admin in role checks
- `backend/services/_crm.py` - is_admin() and is_manager_plus() updated to new role strings
- `backend/seed_data.py` - Admin seed user uses role="admin"
- `backend/tests/conftest.py` - seeded_org fixture uses new role values
- `backend/tests/test_deals_pe.py` - supervisor/regular_user role strings
- `backend/tests/test_funds.py` - admin role string
- `backend/tests/test_ref_data.py` - docstring updates (REFDATA-12/13)
- `frontend/src/pages/AdminPage.jsx` - Gated on admin role, org snapshot uses new role list
- `frontend/src/__tests__/Layout.test.jsx` - Mock uses admin role
- `deploy/entrypoint.sh` - Passes $@ args through (enables pytest via docker-compose run)

## Decisions Made

- Used `sa.types.Uuid()` (not `postgresql.UUID`) for authorship FK columns in migration — required for SQLite test compatibility (per plan Pitfall 1)
- All authorship columns are nullable with `ondelete=SET NULL` per D-09 — NULL means "created before authorship tracking"
- `require_org_admin` function retained as convenience alias but now checks `("admin",)` per D-07
- `is_admin()` and `is_manager_plus()` in `_crm.py` reduced to new role strings; old transitional values (manager, owner) removed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed entrypoint.sh to pass command args through**
- **Found during:** Task 2 verification (running backend tests)
- **Issue:** `deploy/entrypoint.sh` always ran `exec uvicorn ...` regardless of CMD args, so `docker-compose run --rm backend pytest ...` silently started uvicorn instead of pytest
- **Fix:** Added `if [ "$#" -gt 0 ]; then exec "$@"; fi` before the uvicorn fallback
- **Files modified:** deploy/entrypoint.sh
- **Verification:** `docker-compose run --rm -e RUN_SEED_DATA=false backend pytest backend/tests/ -q` now runs pytest and exits
- **Committed in:** 93fa6f4 (Task 2 commit)

**2. [Rule 2 - Auto-fix] Updated test_ref_data.py docstrings**
- **Found during:** Task 2 (grep for old role strings)
- **Issue:** Two docstrings in test_ref_data.py contained "org_admin" as text references to old requirement IDs
- **Fix:** Updated to "admin" in docstring text
- **Files modified:** backend/tests/test_ref_data.py
- **Committed in:** 93fa6f4 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking infrastructure, 1 docstring cleanup)
**Impact on plan:** Both auto-fixes necessary for test execution and code cleanliness. No scope creep.

## Issues Encountered

**Pre-existing test failures (NOT caused by this plan):**
- `backend/tests/test_funds.py` and `backend/tests/test_deals_pe.py`: 9 errors pre-existing before Phase 17 (identical error set before and after our changes). Root cause: conftest monkeypatch `backend.api.routes.ai_query.redis_async.from_url` fails because `ai_query` is a `.py` file not a package. Logged as deferred.
- `backend/tests/test_ref_data.py::test_all_categories_seeded`: RuntimeError: Event loop closed — pre-existing
- Test suite result: 2 passed, 4 xfailed, 9 errors — **identical before and after Phase 17 changes**

## Known Stubs

None — no UI built in this plan.

## Next Phase Readiness

- Migration 0012 is ready to apply (`alembic upgrade head`)
- Phase 18 (access enforcement) can now use `admin`, `supervisor`, `principal`, `regular_user` role strings directly
- Phase 19+ authorship tracking can populate `created_by`/`updated_by` via `Depends(get_current_user)` injection
- Fund entity now has `updated_at` making it consistent with other entities

---
*Phase: 17-groups-roles-authorship-schema*
*Completed: 2026-04-07*
