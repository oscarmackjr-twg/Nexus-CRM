---
phase: 05-deal-counterparty-deal-funding
plan: 01
subsystem: database
tags: [alembic, sqlalchemy, postgresql, deal-counterparty, migration]

# Dependency graph
requires:
  - phase: 04-deal-model-expansion-fund-entity
    provides: Deal ORM model with fund_id FK and DealTeamMember M2M pattern
provides:
  - deal_counterparties table in PostgreSQL (migration 0010)
  - DealCounterparty ORM model importable from backend.models
  - Deal.counterparties relationship with cascade delete-orphan
affects: [05-02, 05-03, 05-04, service layer, API routes, frontend deal detail]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DealCounterparty follows FundService aliased(RefData) label-join pattern — reuse in plan 05-02"
    - "lazy=raise on all relationships prevents N+1 at ORM layer"
    - "Amount+currency pair columns pattern (Numeric(18,2) + String(3)) consistent with Fund/Deal"

key-files:
  created:
    - alembic/versions/0010_deal_counterparties.py
  modified:
    - backend/models.py

key-decisions:
  - "DealCounterparty placed between DealTeamMember and Deal in models.py — forward-ref string form used for Deal relationship"
  - "UniqueConstraint(deal_id, company_id) included inside create_table DDL and __table_args__ — prevents duplicate counterparty per deal"
  - "company_id FK uses ondelete=SET NULL — counterparty row preserved if counterparty company is deleted"
  - "deal_id FK uses ondelete=CASCADE — counterparty rows deleted when deal is deleted"

patterns-established:
  - "DealCounterparty relationship pattern: lazy=raise on both .deal and .company — service layer controls loading"

requirements-completed: [CPARTY-01, CPARTY-02, CPARTY-03, CPARTY-04]

# Metrics
duration: 6min
completed: 2026-03-28
---

# Phase 5 Plan 1: DealCounterparty Migration & ORM Summary

**deal_counterparties table via Alembic 0010 with 6 stage date columns, 2 ref_data FKs, financial fields, and DealCounterparty ORM model with Deal.counterparties cascade relationship**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-28T12:20:10Z
- **Completed:** 2026-03-28T12:26:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created migration 0010_deal_counterparties.py with full DDL: 22 columns, UniqueConstraint(deal_id, company_id), 2 indexes, 3 FK cascades
- Added DealCounterparty ORM class to backend/models.py with all stage date columns, ref_data FKs, financial fields, lazy=raise relationships
- Added Deal.counterparties back-reference with cascade=all,delete-orphan
- Ran `alembic upgrade head` — confirmed DB now at 0010_deal_counterparties (head)

## Task Commits

Each task was committed atomically:

1. **Task 1: Alembic migration 0010_deal_counterparties** - `f4217cd` (feat)
2. **Task 2: DealCounterparty ORM model + Deal relationship** - `ced0cba` (feat)

## Files Created/Modified
- `alembic/versions/0010_deal_counterparties.py` - Migration creating deal_counterparties table with UniqueConstraint, indexes, FKs
- `backend/models.py` - DealCounterparty ORM class (42 lines) + Deal.counterparties relationship

## Decisions Made
- DealCounterparty placed between DealTeamMember and Deal classes to maintain logical grouping of deal-related entities
- company_id uses ondelete=SET NULL (counterparty record preserved if investor company deleted); deal_id uses CASCADE (counterparty deleted with deal)
- UniqueConstraint(deal_id, company_id) prevents duplicate counterparty entries per deal — matches plan spec

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Docker Compose mounts main repo's `../alembic` not worktree — migration file copied to main repo path for `alembic upgrade head` verification. Worktree commit is authoritative.

## Next Phase Readiness
- deal_counterparties table exists in DB, DealCounterparty ORM importable
- Ready for Plan 05-02: DealCounterparty service layer and API routes
- FundService aliased(RefData) label-join pattern applies directly to tier_id and investor_type_id fields

## Self-Check: PASSED

- FOUND: alembic/versions/0010_deal_counterparties.py
- FOUND: backend/models.py (contains DealCounterparty class)
- FOUND: commit f4217cd (Task 1 — migration)
- FOUND: commit ced0cba (Task 2 — ORM model)

---
*Phase: 05-deal-counterparty-deal-funding*
*Completed: 2026-03-28*
