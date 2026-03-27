---
phase: 04-deal-model-expansion-fund-entity
plan: 03
subsystem: api
tags: [fastapi, sqlalchemy, pydantic, aliased-joins, deal-team]

requires:
  - phase: 04-deal-model-expansion-fund-entity
    plan: 02
    provides: Deal ORM model with all PE columns and DealTeamMember table via migration 0004

provides:
  - DealResponse with all PE resolved label fields (transaction_type_label, source_type_label, fund_name, source_company_name, platform_company_name, source_individual_name, originator_name)
  - DealResponse.deal_team list[dict] loaded on GET detail, empty on GET list
  - PATCH /api/v1/deals/{id} endpoint accepting all new PE fields and deal_team_ids
  - DealService._load_deal_team and _set_deal_team helpers for deal team management
  - test_deals_pe.py with 4 tests covering PE field persistence, label resolution, and deal_team CRUD

affects:
  - 04-04 (Deal detail UI — reads DealResponse with all PE labels and deal_team)

tech-stack:
  added: []
  patterns:
    - aliased RefData joins for label resolution (TxnType/SourceType = aliased(RefData))
    - Module-level ORM aliases for multi-join disambiguation
    - deal_team loaded only on get_deal (detail view) — not list_deals — to avoid N+1
    - String(36) FK columns in SQLite use hex UUID format (no hyphens) for joins to work

key-files:
  created:
    - backend/tests/test_deals_pe.py
    - backend/api/routes/deals.py
    - backend/services/deals.py
  modified:
    - backend/schemas/deals.py

key-decisions:
  - "04-03: deal_team loaded only on get_deal (detail), not list_deals — avoids N+1 query per deal"
  - "04-03: PATCH /deals/{id} added alongside existing PUT — same service method, needed for PE field updates"
  - "04-03: source_individual_name uses func.trim + literal() concatenation matching existing contact_name_expr pattern"
  - "04-03: Test UUIDs use .hex format to match SQLite UUID storage (no hyphens) for FK join correctness"

patterns-established:
  - "PE label resolution: TxnType = aliased(RefData); stmt.add_columns(TxnType.label.label('transaction_type_label')).outerjoin(TxnType, TxnType.id == Deal.transaction_type_id)"
  - "Deal team CRUD: _set_deal_team deletes all then re-inserts; _load_deal_team SELECT+JOIN users on deal_id"
  - "_deal_response signature extended: _deal_response(row, deal_team=None) — optional deal_team injection"

requirements-completed: [DEAL-10]

duration: 30min
completed: 2026-03-27
---

# Phase 04 Plan 03: Deal Service & Schema Expansion Summary

**DealResponse expanded with 7 resolved label fields + deal_team list, all PE scalar fields flow through PATCH, and aliased RefData joins eliminate N+1 label lookups**

## Performance

- **Duration:** 30 min
- **Started:** 2026-03-27T23:00:00Z
- **Completed:** 2026-03-27T23:33:23Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Expanded `DealResponse` and `DealUpdate` schemas with all 35+ PE fields (identity, source tracking, 6 financial pairs, 8 date milestones, passed/dead, legacy_id, deal_team)
- Expanded `DealService._base_deal_stmt` with 7 aliased outerjoin columns resolving labels in a single query — no extra lookups per deal
- Added `_load_deal_team` (query deal_team_members+users by deal_id) and `_set_deal_team` (atomic delete+insert) helpers
- Added PATCH route alongside PUT for deal updates, including deal_team_ids handling
- Created `test_deals_pe.py` with 4 tests: PE field persistence, label resolution (transaction_type_label), deal_team CRUD (assign+clear), and backward compatibility (null defaults for legacy deals)

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand DealResponse/DealUpdate schemas with all PE fields** - `f871ba5` (feat)
2. **Task 2: Expand DealService with aliased joins, deal_team loading, and test file** - `930c861` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `backend/schemas/deals.py` - DealCreate/DealUpdate/DealResponse expanded with all PE fields; deal_team_ids in Create+Update; deal_team list[dict] + resolved label fields in Response
- `backend/services/deals.py` - Module-level aliases (TxnType, SourceType, SourceCompany, PlatformCompany, SourceContact, OriginatorUser); expanded _base_deal_stmt; _load_deal_team, _set_deal_team helpers; update_deal handles PE scalars + deal_team_ids
- `backend/api/routes/deals.py` - Added PATCH /{deal_id} endpoint (same service method as PUT)
- `backend/tests/test_deals_pe.py` - 4 tests: test_deal_pe_fields_persist, test_deal_labels_resolved, test_deal_team_crud, test_existing_deals_backward_compatible

## Decisions Made

- **deal_team not loaded on list view**: list_deals returns `deal_team=[]` for all deals. Loading team per deal in list context would cause N+1. Frontend should use GET /deals/{id} for the full deal_team.
- **PATCH endpoint added**: The existing routes only had PUT. PATCH /deals/{id} added as alias to same service method (DealUpdate has all fields optional).
- **SQLite UUID format**: Tests use `.hex` (no hyphens) for String(36) FK comparisons since SQLite stores UUID columns in hex without hyphens. PostgreSQL handles both formats natively — this is test-layer only.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed `func.literal` usage not supported in SQLite**
- **Found during:** Task 2 (running test_deals_pe.py)
- **Issue:** `func.literal("")` generates `literal("")` SQL function which doesn't exist in SQLite; the proper import is `from sqlalchemy import literal`
- **Fix:** Added `literal` to the sqlalchemy imports and changed `func.literal("")` to `literal("") ` in the source_individual_name expression
- **Files modified:** backend/services/deals.py
- **Verification:** Tests pass in SQLite-based test DB
- **Committed in:** 930c861 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed UUID format mismatch in test FK comparisons**
- **Found during:** Task 2 (test_deal_labels_resolved and test_deal_team_crud failing)
- **Issue:** SQLite stores UUID primary key columns as 32-char hex (no hyphens). String(36) FK columns store whatever the application sends. When tests used `str(uuid)` (hyphenated), the JOIN `ref_data.id = deals.transaction_type_id` failed because hex != hyphenated string.
- **Fix:** Tests use `.hex` property of UUID objects for FK values sent in PATCH bodies. Assertions on response IDs use `str(uuid)` since `_load_deal_team` returns `str(row.id)` which SQLAlchemy converts from UUID object to hyphenated string.
- **Files modified:** backend/tests/test_deals_pe.py
- **Verification:** All 4 test_deals_pe tests pass
- **Committed in:** 930c861 (Task 2 commit)

**3. [Rule 2 - Missing Critical] Added PATCH route to deals router**
- **Found during:** Task 2 (plan must_haves specify `PATCH /api/v1/deals/{id}`)
- **Issue:** Only PUT /{deal_id} existed; plan required PATCH for PE field updates
- **Fix:** Added `@router.patch("/{deal_id}")` that calls the same `update_deal` service method
- **Files modified:** backend/api/routes/deals.py
- **Verification:** Tests use PATCH and receive 200 responses
- **Committed in:** 930c861 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 bug, 1 missing critical)
**Impact on plan:** All auto-fixes required for correctness. No scope creep.

## Issues Encountered

- Pre-existing test failures in `test_auth.py::test_list_users_admin_sees_org_users_rep_gets_403` and `test_ref_data.py::test_all_categories_seeded` — confirmed pre-existing by git stash check, not caused by this plan.

## Next Phase Readiness

- DealResponse is fully populated with all PE fields and resolved labels — ready for Plan 04-04 (Deal detail UI)
- PATCH /deals/{id} accepts `deal_team_ids`, `transaction_type_id`, all financial fields, all date milestones
- deal_team members accessible via GET /deals/{id} with `{id, name}` objects
- No new dependencies introduced; all existing deal tests pass

## Self-Check: PASSED

- FOUND: backend/schemas/deals.py
- FOUND: backend/services/deals.py
- FOUND: backend/api/routes/deals.py
- FOUND: backend/tests/test_deals_pe.py
- FOUND: .planning/phases/04-deal-model-expansion-fund-entity/04-03-SUMMARY.md
- FOUND: commit f871ba5 (Task 1)
- FOUND: commit 930c861 (Task 2)

---
*Phase: 04-deal-model-expansion-fund-entity*
*Completed: 2026-03-27*
