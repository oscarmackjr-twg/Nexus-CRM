---
phase: 05-deal-counterparty-deal-funding
plan: 03
subsystem: database
tags: [alembic, sqlalchemy, fastapi, postgresql, deal-funding, migration]

# Dependency graph
requires:
  - phase: 05-deal-counterparty-deal-funding
    provides: deal_counterparties migration 0010, DealCounterparty ORM pattern (lazy=raise, aliased RefData join)
  - phase: 04-deal-model-expansion-fund-entity
    provides: Fund entity, aliased(RefData) label-join pattern, Deal ORM model
provides:
  - deal_funding table in PostgreSQL (migration 0011)
  - deal_funding_status ref_data seeded (5 values: Soft Circle, Hard Circle, Committed, Funded, Declined)
  - DealCounterparty ORM class in backend.models (backfilled from 05-01 gap)
  - DealFunding ORM class importable from backend.models
  - Deal.counterparties + Deal.funding_entries relationships with cascade delete-orphan
  - DealFundingService with list_for_deal, create, update, delete — aliased Company+RefData joins
  - 4 CRUD endpoints at /api/v1/deals/{deal_id}/funding — GET, POST 201, PATCH, DELETE 204
affects: [05-04, frontend deal detail, DealDetailPage funding tab]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DealFunding uses StatusRef=aliased(RefData) + ProviderCompany=aliased(Company) — same pattern as FundService"
    - "_funding_response static method maps ORM row + joined labels, converts Decimal to float with None guard"
    - "math.ceil for pages calculation, default size=50 per D-16"
    - "Route handler commits after service flush — service does flush only, route owns transaction"

key-files:
  created:
    - alembic/versions/0011_deal_funding.py
    - backend/schemas/funding.py
    - backend/services/funding.py
    - backend/api/routes/funding.py
  modified:
    - backend/models.py
    - backend/api/main.py

key-decisions:
  - "DealCounterparty ORM backfilled into models.py (Rule 3 fix) — 05-01 git commit only had migration file, ORM class was never committed"
  - "DealFunding placed between DealTeamMember and Deal — consistent with DealCounterparty ordering"
  - "funding router added to main.py import+router list after funds.router — counterparties router deferred to 05-02"
  - "Route handlers own commit(), service does flush() only — consistent with funds.py pattern"

patterns-established:
  - "DealFunding lazy=raise on both .deal and .capital_provider — service controls all loading via _base_stmt"
  - "Aliased Company join for capital_provider_name mirrors DealCounterparty company_name pattern in 05-02"

requirements-completed: [FUNDING-01, FUNDING-02, FUNDING-03, FUNDING-04, FUNDING-05, FUNDING-06, FUNDING-07]

# Metrics
duration: 12min
completed: 2026-03-28
---

# Phase 5 Plan 3: DealFunding Migration & Full API Summary

**deal_funding table (Alembic 0011), 5 deal_funding_status ref_data seeds, DealFunding ORM, schemas, aliased-join service, and 4 CRUD endpoints at /api/v1/deals/{deal_id}/funding**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-28T12:33:24Z
- **Completed:** 2026-03-28T12:45:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created migration 0011_deal_funding.py with DDL (12 columns, 2 indexes, 4 FK cascades) and 5 deal_funding_status ref_data seeds (Soft Circle, Hard Circle, Committed, Funded, Declined)
- Added DealCounterparty ORM class and DealFunding ORM class to backend/models.py with Deal.counterparties and Deal.funding_entries back-references
- Built DealFundingService with aliased Company+RefData joins, paginated list, create, update, delete methods
- Registered /api/v1/deals/{deal_id}/funding CRUD endpoints (GET, POST 201, PATCH, DELETE 204) in FastAPI app

## Task Commits

Each task was committed atomically:

1. **Task 1: Migration 0011 + DealCounterparty/DealFunding ORM + Deal relationships** - `fdeaa91` (feat)
2. **Task 2: DealFunding schemas, service, routes, main.py registration** - `ed55559` (feat)

## Files Created/Modified
- `alembic/versions/0011_deal_funding.py` - Migration creating deal_funding table + deal_funding_status seed (5 values)
- `backend/models.py` - DealCounterparty ORM class (backfilled) + DealFunding ORM class + Deal.counterparties/funding_entries relationships
- `backend/schemas/funding.py` - DealFundingCreate, DealFundingUpdate, DealFundingResponse (with capital_provider_name/status_label), DealFundingListResponse
- `backend/services/funding.py` - DealFundingService with StatusRef/ProviderCompany aliased joins, list_for_deal (default size 50), create, update, delete
- `backend/api/routes/funding.py` - 4 endpoints: GET list, POST 201, PATCH, DELETE 204
- `backend/api/main.py` - Added funding import + funding.router after funds.router

## Decisions Made
- Backfilled DealCounterparty ORM class into models.py alongside DealFunding (05-01 only committed the migration, not the ORM model)
- Used same transaction pattern as funds.py: service.flush() only, route handler owns db.commit()
- Default page size 50 matching D-16 requirement

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] DealCounterparty ORM class missing from models.py**
- **Found during:** Task 1 (migration 0011 + DealFunding ORM)
- **Issue:** Plan 05-01 SUMMARY claimed DealCounterparty was added to models.py but git log shows the 05-01 commit (`0047258`) only created the migration file. DealCounterparty class was absent, blocking Deal.counterparties relationship (required by DealFunding's funding_entries sibling pattern).
- **Fix:** Added DealCounterparty ORM class in the same commit as DealFunding ORM, inserted between DealTeamMember and Deal per the 05-01 spec. Also added Deal.counterparties cascade relationship.
- **Files modified:** backend/models.py
- **Verification:** `from backend.models import DealCounterparty` succeeds; `DealCounterparty.__tablename__ == 'deal_counterparties'`
- **Committed in:** fdeaa91 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Required for correctness — DealFunding's Deal.funding_entries needed to be added alongside Deal.counterparties. No scope creep.

## Issues Encountered
- Docker Compose `run --rm backend alembic upgrade head` command started the full app server (including metadata.create_all in lifespan handler) rather than just running alembic. The deal_funding table was created via metadata.create_all but alembic revision was correctly tracked at 0011_deal_funding. Verified via `docker exec deploy-postgres-1 psql -c "SELECT version_num FROM alembic_version"`.
- Multiple parallel docker-compose run containers left running from other agents — confirmed no interference.

## Next Phase Readiness
- deal_funding table at migration head 0011_deal_funding
- DealFundingService + 4 CRUD endpoints operational at /api/v1/deals/{deal_id}/funding
- DealCounterparty ORM class now in models.py — Plan 05-02 (counterparties service) can proceed without the backfill blocker
- Ready for Plan 05-04: DealDetailPage funding tab UI

## Self-Check: PASSED

- FOUND: alembic/versions/0011_deal_funding.py
- FOUND: backend/models.py (contains DealCounterparty + DealFunding classes)
- FOUND: backend/schemas/funding.py
- FOUND: backend/services/funding.py
- FOUND: backend/api/routes/funding.py
- FOUND: backend/api/main.py (contains funding import + funding.router)
- FOUND: commit fdeaa91 (Task 1 — migration + ORM)
- FOUND: commit ed55559 (Task 2 — schemas, service, routes, main.py)
- DB VERIFIED: deal_funding table exists, alembic version = 0011_deal_funding
- DB VERIFIED: deal_funding_status seeded with 5 values (Soft Circle, Hard Circle, Committed, Funded, Declined)

---
*Phase: 05-deal-counterparty-deal-funding*
*Completed: 2026-03-28*
