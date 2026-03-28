---
phase: 05-deal-counterparty-deal-funding
plan: 02
subsystem: backend-api
tags: [fastapi, sqlalchemy, pydantic, deal-counterparty, api-routes, service-layer]

# Dependency graph
requires:
  - phase: 05-deal-counterparty-deal-funding
    plan: 01
    provides: DealCounterparty ORM model + deal_counterparties table
provides:
  - DealCounterpartyService with aliased join list/create/update/delete
  - Pydantic schemas: DealCounterpartyCreate, Update, Response, ListResponse
  - Nested CRUD routes at /api/v1/deals/{deal_id}/counterparties
affects: [05-03, 05-04, frontend deal detail counterparty tab]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TierRef/InvestorTypeRef/CpartyCompany aliased join pattern — single-query label resolution, no N+1"
    - "Decimal->float conversion in _counterparty_response (same as DealService pattern)"
    - "clamp_pagination/count_rows/page_count from _crm — consistent pagination across all list endpoints"

key-files:
  created:
    - backend/schemas/counterparties.py
    - backend/services/counterparties.py
    - backend/api/routes/counterparties.py
  modified:
    - backend/api/main.py

key-decisions:
  - "DealCounterpartyCreate includes all non-date fields (company_id required per D-06) — stage dates only settable via Update"
  - "list_for_deal orders by position ASC NULLS LAST then created_at ASC — matches TWG tracker row ordering intent"
  - "create() uses model_dump(exclude_unset=False) to send all fields including explicit None values to DB"

# Metrics
duration: 16min
completed: 2026-03-28
---

# Phase 5 Plan 2: DealCounterparty Service + API Routes Summary

**DealCounterpartyService with aliased single-query joins (company_name, tier_label, investor_type_label) and nested CRUD routes at /api/v1/deals/{deal_id}/counterparties**

## Performance

- **Duration:** 16 min
- **Started:** 2026-03-28T12:33:23Z
- **Completed:** 2026-03-28T12:49:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `backend/schemas/counterparties.py` with DealCounterpartyCreate, DealCounterpartyUpdate, DealCounterpartyResponse, DealCounterpartyListResponse
- Created `backend/services/counterparties.py` with DealCounterpartyService: TierRef/InvestorTypeRef/CpartyCompany aliased joins, list_for_deal (default size=50), create, update, delete
- Created `backend/api/routes/counterparties.py` with 4 endpoints: GET / (list), POST / (create 201), PATCH /{id} (update), DELETE /{id} (204)
- Updated `backend/api/main.py` to import counterparties and register counterparties.router after deals.router

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic schemas + DealCounterpartyService** - `fc6a91b` (feat)
2. **Task 2: Counterparty API routes + main.py registration** - `d447f56` (feat)

## Files Created/Modified

- `backend/schemas/counterparties.py` — 4 Pydantic classes with company_name, tier_label, investor_type_label response fields
- `backend/services/counterparties.py` — DealCounterpartyService with _base_stmt aliased joins, _counterparty_response mapper, CRUD methods
- `backend/api/routes/counterparties.py` — 4 CRUD endpoints nested under /deals/{deal_id}/counterparties
- `backend/api/main.py` — counterparties import + router registration

## Decisions Made

- DealCounterpartyCreate includes all non-date fields (stage dates only settable via Update, matching PE workflow where dates are tracked as milestones, not set on creation)
- list_for_deal orders by position ASC NULLS LAST then created_at ASC — enables manual ordering matching TWG tracker row layout
- create() uses model_dump(exclude_unset=False) to pass explicit None values to DB (ensures fields not provided in payload are explicitly null, not omitted)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None — all 4 CRUD endpoints are fully wired to DealCounterpartyService.

## Self-Check: PASSED

- FOUND: backend/schemas/counterparties.py
- FOUND: backend/services/counterparties.py
- FOUND: backend/api/routes/counterparties.py
- FOUND: backend/api/main.py (contains counterparties.router)
- FOUND: commit fc6a91b (Task 1 — schemas + service)
- FOUND: commit d447f56 (Task 2 — routes + main.py)

---
*Phase: 05-deal-counterparty-deal-funding*
*Completed: 2026-03-28*
