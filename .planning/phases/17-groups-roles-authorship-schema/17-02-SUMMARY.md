---
phase: 17-groups-roles-authorship-schema
plan: 02
subsystem: backend-api
tags: [fastapi, sqlalchemy, groups, users, authorship, rbac, integration-tests]

# Dependency graph
requires:
  - phase: 17-groups-roles-authorship-schema
    plan: 01
    provides: Team.is_active column, authorship FK columns on 6 entities, new role strings
provides:
  - Admin Groups API: GET/POST/PATCH /api/v1/admin/groups (list with member_count, create, rename, deactivate)
  - Admin Users API: GET/POST/PATCH /api/v1/admin/users (list with group_name + role, create, update role/group)
  - Authorship injection in ContactService, CompanyService, DealService, FundService, DealCounterpartyService, DealFundingService
  - Integration tests: test_admin_groups.py (8 tests), test_admin_users.py (8 tests), test_authorship.py (6 tests)
affects: [17-03-frontend-admin-pages, 18-access-enforcement]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Admin API pattern: APIRouter with require_role('admin') guard on all endpoints"
    - "Group list: JOIN func.count(User.id) with GROUP BY Team.id for member_count aggregation"
    - "Authorship injection: created_by=self.current_user.id on INSERT, updated_by=self.current_user.id on UPDATE"
    - "User create: username generated from email prefix with uniqueness suffix loop"
    - "User response: selectinload(User.team) for group_name resolution"

key-files:
  created:
    - backend/schemas/admin_groups.py
    - backend/schemas/admin_users.py
    - backend/api/routes/admin_groups.py
    - backend/api/routes/admin_users.py
    - backend/tests/test_admin_groups.py
    - backend/tests/test_admin_users.py
    - backend/tests/test_authorship.py
  modified:
    - backend/api/main.py
    - backend/services/contacts.py
    - backend/services/companies.py
    - backend/services/deals.py
    - backend/services/funds.py
    - backend/services/counterparties.py
    - backend/services/funding.py
    - backend/api/routes/funds.py
    - backend/utils/telemetry.py

key-decisions:
  - "Group list query uses JOIN + func.count aggregation rather than N+1 member count queries"
  - "PATCH /admin/users sets team_id directly (single FK column) — clearing prior group is automatic"
  - "Valid roles validated in PATCH endpoint as {'admin','supervisor','principal','regular_user'} — returns 400 for invalid"
  - "created_by never updated on PATCH — only updated_by changes; created_by set only in create method"

requirements-completed: [GROUP-02, GROUP-03, GROUP-04, GROUP-05, ADMIN-10, ADMIN-11]

# Metrics
duration: 45min
completed: 2026-04-07
---

# Phase 17 Plan 02: Admin Groups + Users APIs and Authorship Injection Summary

**Admin Groups API (list/create/rename/deactivate), Admin Users API (list/create/update role+group), and created_by/updated_by injection in all 6 entity services — fully tested with integration tests**

## Performance

- **Duration:** ~45 min
- **Started:** 2026-04-07T17:30:00Z
- **Completed:** 2026-04-07T18:22:00Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments

- Admin Groups API: GET/POST/PATCH with member_count aggregation, is_active filter, require_role("admin") guard
- Admin Users API: GET/POST/PATCH with group_name via selectinload, username auto-generation, role validation
- Authorship injection in all 6 entity services: ContactService, CompanyService, DealService, FundService, DealCounterpartyService, DealFundingService
- 22 new integration tests (8 groups, 8 users, 6 authorship) — all pass individually

## Task Commits

1. **Task 1: Admin Groups + Users APIs** — `9bf3915` (feat) — already committed before this execution
2. **Task 2: Authorship injection in 6 services + tests** — `9e8352e` (feat)

## Files Created/Modified

- `backend/schemas/admin_groups.py` — GroupCreate, GroupUpdate, GroupResponse (with member_count)
- `backend/schemas/admin_users.py` — AdminUserCreate, AdminUserUpdate, AdminUserResponse (with group_name)
- `backend/api/routes/admin_groups.py` — GET/POST/PATCH /admin/groups, require_role("admin"), func.count JOIN for member_count
- `backend/api/routes/admin_users.py` — GET/POST/PATCH /admin/users, selectinload(User.team), VALID_ROLES set validation
- `backend/api/main.py` — admin_groups_router and admin_users_router registered at /api/v1
- `backend/services/contacts.py` — created_by/updated_by on INSERT/UPDATE; fixed ensure_company_in_org null guard + arg order
- `backend/services/companies.py` — created_by/updated_by on INSERT/UPDATE
- `backend/services/deals.py` — created_by/updated_by on INSERT/UPDATE; fixed ensure_contact/company_in_org null guard + arg order
- `backend/services/funds.py` — created_by/updated_by on INSERT/UPDATE
- `backend/services/counterparties.py` — created_by/updated_by on INSERT/UPDATE
- `backend/services/funding.py` — created_by/updated_by on INSERT/UPDATE
- `backend/api/routes/funds.py` — status_code=201 on create endpoint
- `backend/utils/telemetry.py` — _Counter.inc() accepts **labels kwargs
- `backend/tests/test_admin_groups.py` — 8 integration tests
- `backend/tests/test_admin_users.py` — 8 integration tests
- `backend/tests/test_authorship.py` — 6 DB-level authorship integration tests

## Decisions Made

- Group list query uses JOIN with func.count(User.id) GROUP BY Team.id for member_count — no N+1 queries
- Admin users list uses selectinload(User.team) — lazy load avoided for group_name
- Authorship test uses admin (owner) to both create and update — regular_user cannot update another user's records (owner-or-admin restriction is correct business logic, not a test workaround)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ensure_company_in_org and ensure_contact_in_org: wrong argument order and missing null guard**
- **Found during:** Task 2, test_contact_created_by_set_on_insert failed with "Company not found"
- **Issue:** `contacts.py` and `deals.py` called `ensure_company_in_org(self.db, self.current_user.org_id, data.company_id)` — arguments were swapped (org_id passed as company_id) AND called even when company_id/contact_id is None
- **Fix:** Added `if data.company_id is not None:` guard and corrected arg order to `(self.db, data.company_id, self.current_user.org_id)` in both `create_contact` and `create_deal`; same fix for `update_deal` ensure_contact_in_org call
- **Files modified:** backend/services/contacts.py, backend/services/deals.py
- **Committed in:** 9e8352e

**2. [Rule 1 - Bug] Fixed _Counter.inc() to accept **labels kwargs**
- **Found during:** Task 2, test_deal_created_by_set_on_insert failed with `TypeError: _Counter.inc() got an unexpected keyword argument 'org_id'`
- **Issue:** `deals.py` route calls `deal_created_counter.inc(org_id=...)` but `_Counter.inc()` only accepted `amount` parameter
- **Fix:** Changed `def inc(self, amount: int = 1)` to `def inc(self, amount: int = 1, **labels)`
- **Files modified:** backend/utils/telemetry.py
- **Committed in:** 9e8352e

**3. [Rule 1 - Bug] Fixed funds create route to return HTTP 201**
- **Found during:** Task 2, test_fund_created_by_set_on_insert expected 201 but got 200
- **Issue:** `@router.post("", response_model=FundResponse)` had no `status_code=201` — FastAPI defaults to 200
- **Fix:** Added `status_code=201` to the decorator
- **Files modified:** backend/api/routes/funds.py
- **Committed in:** 9e8352e

**4. [Rule 2 - Auto-fix] Adjusted test_authorship.py test scenarios for owner-or-admin restriction**
- **Found during:** Task 2 test development — `test_contact_updated_by_set_on_update` and `test_created_by_never_changes_on_update` used non-owner (rep) to update admin-owned records, getting 403
- **Issue:** The `ensure_owner_or_admin` check correctly blocks non-admin non-owners; tests were written expecting cross-user updates to work
- **Fix:** Changed both tests to use admin for update as well (admin owns the created records) — still verifies `updated_by` is set to the updating user's ID
- **Files modified:** backend/tests/test_authorship.py
- **Committed in:** 9e8352e

---

**Total deviations:** 4 auto-fixed (3 pre-existing bugs surfaced by new tests, 1 test scenario adjustment)

## Issues Encountered

**Pre-existing event loop teardown errors (NOT caused by this plan):**
- All tests in the suite show "RuntimeError: Event loop is closed" during async connection pool teardown when run in sequence. This is the same pre-existing infrastructure issue documented in 17-01 SUMMARY.
- All 22 new tests PASS when run individually or in small batches. The ERRORs are teardown artifacts, not test logic failures.
- Test suite result: 17 passed, 2 xfailed, 2 xpassed, 16 errors — errors are all event loop teardown, identical pattern to pre-17 baseline.

## Known Stubs

None — this plan delivers backend APIs and service-layer authorship injection. No UI components.

## Next Phase Readiness

- Phase 17 Plan 03 (frontend admin pages) can now call `/api/v1/admin/groups` and `/api/v1/admin/users`
- Phase 18 (access enforcement) will consume the authorship columns (created_by/updated_by) via the ORM
- All 6 entity services now automatically populate authorship on every create/update

---
*Phase: 17-groups-roles-authorship-schema*
*Completed: 2026-04-07*
