---
phase: 04-deal-model-expansion-fund-entity
plan: 01
subsystem: database, api
tags: [fastapi, sqlalchemy, alembic, pydantic, fund, ref_data, sqlite]

# Dependency graph
requires:
  - phase: 02-reference-data-system
    provides: ref_data table and REFDATA-15 FK pattern (ondelete=SET NULL)
  - phase: 03-contact-company-model-expansion
    provides: alembic migration chain (0006_activity_deal_id_nullable is down_revision)
provides:
  - funds table with 7 columns (id, org_id, fund_name, fundraise_status_id, target_fund_size_amount, target_fund_size_currency, vintage_year)
  - fund_status ref_data category seeded with 4 values (Fundraising, Closed, Deployed, Returning Capital)
  - Fund ORM model with org/deals relationships
  - FundService with list/create/update and fundraise_status_label join
  - GET/POST/PATCH /api/v1/funds endpoints
  - fund_id FK column on Deal model (prerequisite for Plan 02)
affects:
  - 04-02 — deal model expansion needs fund_id FK and Fund ORM (now available)
  - 04-03 — DealCounterparty entity
  - 04-04 — frontend deal detail page

# Tech tracking
tech-stack:
  added: []
  patterns:
    - FundService(db, current_user) constructor pattern (mirrors DealService)
    - list_funds_by_ids() helper for post-write label resolution
    - aliased(RefData) pattern for ref_data label joins (FundStatusRef)
    - UUID column comparisons use UUID type directly (not str) for SQLite compat

key-files:
  created:
    - alembic/versions/0007_fund.py
    - backend/schemas/funds.py
    - backend/services/funds.py
    - backend/api/routes/funds.py
    - backend/tests/test_funds.py
  modified:
    - backend/models.py
    - backend/api/main.py
    - backend/tests/conftest.py

key-decisions:
  - "Fund ORM id/org_id comparisons use UUID type directly (not str) — SQLite stores UUIDs without hyphens; str conversion breaks IN queries"
  - "list_funds_by_ids() re-queries after flush to resolve fundraise_status_label join — avoids session state stale reads"
  - "fund_id FK added to Deal model in this plan (not Plan 02) so migration chain stays clean"

patterns-established:
  - "FundService pattern: list/create/update with label join via aliased(RefData) — use for DealCounterparty and DealFunding services in Phase 5"
  - "conftest.py seed_ref_data fixture extended per plan — add new categories as new ref_data categories are seeded"

requirements-completed: [FUND-01, FUND-02, FUND-03, FUND-04]

# Metrics
duration: 2min
completed: 2026-03-27
---

# Phase 4 Plan 01: Fund Entity Summary

**Fund CRUD API at /api/v1/funds with Alembic migration, Fund ORM model, FundService label-join pattern, and fund_status ref_data seeded with 4 TWG values**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-27T23:10:21Z
- **Completed:** 2026-03-27T23:12:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- funds table created via Alembic migration 0007_fund with org_id, fund_name, fundraise_status_id, target_fund_size_amount, target_fund_size_currency, vintage_year, created_at
- fund_status ref_data seeded: Fundraising, Closed, Deployed, Returning Capital (system defaults, org_id=None)
- Fund ORM model added to backend/models.py with Organization.funds relationship and Fund.deals back-ref
- fund_id FK column added to Deal model (prerequisite for Plan 02 deal expansion)
- FundService implementing list (with label join), create, and update operations
- GET /api/v1/funds, POST /api/v1/funds, PATCH /api/v1/funds/{id} — all passing tests
- 4 test cases pass: create, list, update, 404 not-found

## Task Commits

Each task was committed atomically:

1. **Task 1: Fund migration, ORM model, and test stubs** - `1e9be10` (feat)
2. **Task 2: Fund service, schemas, API routes, and main.py registration** - `f9f6143` (feat)

## Files Created/Modified

- `alembic/versions/0007_fund.py` - funds table DDL + fund_status ref_data seed (4 rows)
- `backend/models.py` - Fund ORM class, funds relationship on Organization, fund_id FK on Deal
- `backend/schemas/funds.py` - FundCreate, FundUpdate, FundResponse Pydantic schemas
- `backend/services/funds.py` - FundService with list/create/update and aliased(RefData) label join
- `backend/api/routes/funds.py` - GET /funds, POST /funds, PATCH /funds/{id}
- `backend/api/main.py` - funds_router registered alongside deals_router
- `backend/tests/test_funds.py` - 4 CRUD test cases (create, list, update, 404)
- `backend/tests/conftest.py` - seed_ref_data fixture extended with fund_status entries

## Decisions Made

- UUID column comparisons use UUID type objects directly (not `str()`) — SQLite stores UUIDs without hyphens; passing hyphenated string to a `Uuid()` column breaks SQLAlchemy's type processor
- `list_funds_by_ids()` helper re-queries after flush to resolve `fundraise_status_label` via join — simpler than building the label resolution inline in `create_fund`/`update_fund`
- `fund_id` FK added to Deal model in this plan rather than Plan 02, so the migration chain remains clean (one migration per conceptual change)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed UUID type mismatch in list_funds_by_ids SQLAlchemy query**
- **Found during:** Task 2 (running test suite)
- **Issue:** Plan specified `Fund.id.in_([str(i) for i in ids])` — SQLite stores UUIDs without hyphens but `str(uuid_obj)` returns hyphenated form, causing SQLAlchemy Uuid() type processor to fail with `AttributeError: 'str' object has no attribute 'hex'`
- **Fix:** Changed to `Fund.id.in_(ids)` passing UUID objects directly; also removed `str(fund_id)` cast in `update_fund` comparison
- **Files modified:** backend/services/funds.py
- **Verification:** All 4 fund tests pass
- **Committed in:** f9f6143 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug in plan-specified code)
**Impact on plan:** Required fix for SQLite test compatibility. In PostgreSQL the string cast would work, but SQLite requires native UUID objects. Production (PostgreSQL) behavior unaffected.

## Issues Encountered

None beyond the UUID type mismatch documented above.

## Next Phase Readiness

- Fund entity complete and tested — Plan 02 (deal model expansion) can now add `fund_id` FK to existing deals
- fund_id FK column already on Deal ORM model; Plan 02 migration only needs to ADD COLUMN
- FundService aliased(RefData) label-join pattern is established — reuse in DealCounterparty and DealFunding services

## Self-Check: PASSED

All created files exist on disk. Both task commits (1e9be10, f9f6143) confirmed in git log.

---
*Phase: 04-deal-model-expansion-fund-entity*
*Completed: 2026-03-27*
