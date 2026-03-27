---
phase: 02-reference-data-system
plan: 02
subsystem: api
tags: [fastapi, sqlalchemy, pydantic, ref-data, rbac, pytest]

# Dependency graph
requires:
  - phase: 02-reference-data-system/02-01
    provides: RefData ORM model; ref_data table with 10 categories; test scaffold with 4 xfail Wave 2 tests
provides:
  - GET /api/v1/admin/ref-data?category= endpoint (all authenticated users)
  - POST /api/v1/admin/ref-data endpoint (org_admin/super_admin only)
  - PATCH /api/v1/admin/ref-data/{id} endpoint (org_admin/super_admin only, supports soft-delete)
  - RefDataService with list_by_category (union org+system defaults), create, update
  - RefDataCreate, RefDataUpdate, RefDataResponse Pydantic schemas
  - admin router registered in main.py at /api/v1
affects: [03-contact-company-expansion, 04-deal-expansion, 05-dealcounterparty-dealfunding, 06-admin-ref-data-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "RefDataService constructor: (db: AsyncSession, current_user: User) — matches ContactService pattern"
    - "org union query: or_(RefData.org_id == current_user.org_id, RefData.org_id.is_(None)) — org items + system defaults"
    - "GET open to all authenticated users via get_current_user; POST/PATCH gated by require_role"
    - "Soft-delete via PATCH is_active=False — no DELETE endpoint; GET always filters is_active=True"
    - "RefDataCreate intentionally omits org_id — service assigns current_user.org_id on create"

key-files:
  created:
    - backend/schemas/ref_data.py
    - backend/services/ref_data.py
    - backend/api/routes/admin.py
  modified:
    - backend/api/main.py

key-decisions:
  - "GET /admin/ref-data open to all authenticated roles (D-03) — downstream phases need sector dropdowns for all users, not just admins"
  - "update() rejects modifications to another org's items (403) but allows editing system defaults (org_id=None)"
  - "REFDATA-15 pattern documented: downstream FK columns to ref_data.id use ForeignKey('ref_data.id', ondelete='SET NULL')"

patterns-established:
  - "Pattern 4: Route auth split — GET uses Depends(get_current_user), POST/PATCH use Depends(require_role('org_admin','super_admin'))"
  - "Pattern 5: Admin router registered first in main.py router list at /api/v1 prefix"
  - "Pattern 6: Service update() uses model_dump(exclude_unset=True) for partial updates — only specified fields written"

requirements-completed: [REFDATA-11, REFDATA-12, REFDATA-13, REFDATA-14, REFDATA-15]

# Metrics
duration: 3min
completed: 2026-03-27
---

# Phase 2 Plan 02: Reference Data System Summary

**FastAPI ref-data CRUD endpoints (GET/POST/PATCH /api/v1/admin/ref-data) with RefDataService union query, RBAC split, and soft-delete; all 7 test_ref_data.py tests green**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-27T12:40:44Z
- **Completed:** 2026-03-27T12:43:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `backend/schemas/ref_data.py` with RefDataCreate, RefDataUpdate, RefDataResponse; RefDataCreate intentionally excludes org_id (assigned by service)
- Created `backend/services/ref_data.py` with RefDataService implementing list_by_category (org+system defaults union, is_active filter, position/label ordering), create (assigns org_id from current_user), update (partial patch with 403 guard for cross-org modifications)
- Created `backend/api/routes/admin.py` with GET (get_current_user), POST and PATCH (require_role org_admin/super_admin); router prefix /admin/ref-data
- Registered admin.router in `backend/api/main.py` — 4 previously xfail Wave 2 tests now pass green (7/7 total)

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic schemas for ref_data** - `df86add` (feat)
2. **Task 2: RefDataService + admin routes + main.py registration** - `b88cafd` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/schemas/ref_data.py` - RefDataCreate, RefDataUpdate, RefDataResponse Pydantic schemas
- `backend/services/ref_data.py` - RefDataService: list_by_category, create, update methods
- `backend/api/routes/admin.py` - GET/POST/PATCH handlers at /admin/ref-data with RBAC split
- `backend/api/main.py` - admin module imported; admin.router added to registration loop

## Decisions Made

- GET endpoint uses `get_current_user` only (not `require_role`) per D-03 design decision — all authenticated roles (including rep, viewer) need dropdown data for Phases 3–5 form rendering
- `update()` method allows modifying system defaults (org_id=None) for org admins — enables per-org override pattern if needed; rejects changes to other orgs' items with 403
- REFDATA-15 pattern: downstream phases (3–5) MUST use `ForeignKey("ref_data.id", ondelete="SET NULL")` to match the RefData.org_id FK pattern established in 02-01

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three ref-data endpoints operational at /api/v1/admin/ref-data
- RefDataService ready for consumption — downstream phases import via `from backend.services.ref_data import RefDataService`
- Phase 02-03 (frontend RefSelect component) can proceed: GET /api/v1/admin/ref-data?category= is live
- Phase 06 (Admin Reference Data UI): POST/PATCH endpoints ready for admin management screens
- No blockers

## Self-Check: PASSED

- FOUND: backend/schemas/ref_data.py
- FOUND: backend/services/ref_data.py
- FOUND: backend/api/routes/admin.py
- FOUND: backend/api/main.py (admin.router registered)
- FOUND commit: df86add (schemas)
- FOUND commit: b88cafd (service + routes + main.py)
- pytest backend/tests/test_ref_data.py: 3 passed, 4 xpassed (all 7 green)

---
*Phase: 02-reference-data-system*
*Completed: 2026-03-27*
