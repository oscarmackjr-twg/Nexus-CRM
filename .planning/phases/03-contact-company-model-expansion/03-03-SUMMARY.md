---
phase: 03-contact-company-model-expansion
plan: 03
subsystem: database
tags: [alembic, sqlalchemy, postgresql, pe-blueprint, company-model]

# Dependency graph
requires:
  - phase: 02-reference-data-system
    provides: ref_data table with id (UUID) as FK target for company_type, tier, sector, sub_sector, target_deal_size
provides:
  - Alembic migration 0005 adding 33 PE Blueprint columns to companies table
  - Company ORM model with all PE fields, self-referential parent_company relationship, org-scoped legacy_id unique constraint
affects:
  - 03-contact-company-model-expansion (plans 04-06 — Company API, schemas, UI need these columns)
  - 04-deal-expansion — deal-company joins gain PE-enriched company data

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Parallel Alembic branch — 0005 branches from 0002 (not from 0003/0004 contact chain); merge migration needed after Phase 3 completes"
    - "Self-referential ORM relationship: remote_side='Company.id', foreign_keys=[parent_company_id]"
    - "All ref_data FKs: ondelete=SET NULL per REFDATA-15 pattern"
    - "Numeric(18,2) for all financial columns (aum, ebitda, bite_size)"

key-files:
  created:
    - alembic/versions/0005_company_pe_fields.py
  modified:
    - backend/models.py

key-decisions:
  - "0005 migration branches from 0002_pe_ref_data (not 0003/0004) because parallel execution — merge migration required once all Phase 3 chains complete"
  - "parent_company_id uses String(36) not UUID to match ref_data FK pattern used elsewhere in migration; remote_side='Company.id' (string form) for forward-ref compatibility"
  - "UniqueConstraint(org_id, legacy_id) added to both migration AND ORM __table_args__ for consistency"

patterns-established:
  - "Company self-ref pattern: parent_company_id String(36) FK + relationship(remote_side='Company.id', foreign_keys=[parent_company_id])"
  - "PE financial column pattern: amount Numeric(18,2) + currency String(3) paired columns"

requirements-completed: [COMPANY-01, COMPANY-02, COMPANY-03, COMPANY-04, COMPANY-05, COMPANY-06, COMPANY-07, COMPANY-08, COMPANY-09]

# Metrics
duration: 2min
completed: 2026-03-27
---

# Phase 3 Plan 03: Company PE Fields Summary

**Alembic migration 0005 + Company ORM model expanded with 33 PE Blueprint columns — type/tier/sector FKs, financials (AUM/EBITDA/bite-size), investment preferences, watchlist, coverage_person, self-referential parent_company**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-27T20:15:10Z
- **Completed:** 2026-03-27T20:17:01Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `alembic/versions/0005_company_pe_fields.py` with 33 `op.add_column` calls covering all COMPANY-01 through COMPANY-09 requirements, plus explicit downgrade
- Updated `backend/models.py` Company class with all 33 new mapped columns, a UniqueConstraint on (org_id, legacy_id), and a self-referential `parent_company` relationship
- All 5 ref_data FK columns (company_type, tier, sector, sub_sector, target_deal_size) use `ondelete="SET NULL"` per REFDATA-15 pattern
- Python import verification confirms 49 total columns and all constraints present

## Task Commits

1. **Task 1: Alembic migration 0005 — Company PE columns** - `463e2a3` (feat)
2. **Task 2: Company ORM model update** - `024e92b` (feat)

## Files Created/Modified

- `alembic/versions/0005_company_pe_fields.py` — Migration adding 33 Company PE columns with FK constraints, Numeric(18,2) financials, unique constraint on org_id+legacy_id, explicit downgrade
- `backend/models.py` — Company class expanded: UniqueConstraint in __table_args__, 33 new Mapped columns, self-referential parent_company relationship

## Decisions Made

- Migration branches from `0002_pe_ref_data` because 0003/0004 (Contact migrations from plan 03-01) ran in parallel — a merge migration will resolve the branched Alembic history after all Phase 3 plans complete
- `parent_company_id` uses `String(36)` (matching the migration FK style) with `remote_side="Company.id"` string form for forward-reference compatibility in SQLAlchemy
- `UniqueConstraint("org_id", "legacy_id", name="uq_companies_org_legacy_id")` placed in both the migration file and the ORM `__table_args__` for single source of truth at both layers

## Deviations from Plan

None — plan executed exactly as written. The down_revision choice (`0002_pe_ref_data` instead of `0004_contact_coverage_persons`) was anticipated by the plan's conditional guidance for parallel execution.

## Issues Encountered

None — models.py had been modified by a parallel 03-01 agent (Contact PE fields added above Company class) but Company class itself was unchanged, making the edit clean.

## Next Phase Readiness

- Company table ready for Phase 3 Plan 04 (Company API + Pydantic schemas) — all columns exist in both DB schema and ORM model
- `company_type_id`, `tier_id`, `sector_id`, `sub_sector_id`, `target_deal_size_id` all reference `ref_data.id` — RefSelect component from Phase 2 can be used directly in Company UI
- Merge migration needed (separate plan or 03-06) to join 0005 branch with 0003/0004 Contact branch before running `alembic upgrade head`

---
*Phase: 03-contact-company-model-expansion*
*Completed: 2026-03-27*
