---
phase: 04-deal-model-expansion-fund-entity
plan: 02
subsystem: database
tags: [sqlalchemy, alembic, deal, pe-fields, migrations, models]

# Dependency graph
requires:
  - phase: 04-deal-model-expansion-fund-entity
    plan: 01
    provides: Fund table (0007_fund), fund_id FK on Deal ORM model, migration chain ending at 0007
affects:
  - 04-03 — DealCounterparty entity uses Deal PE columns (transaction_type_id, fund_id)
  - 04-04 — frontend deal detail uses all new PE fields from this plan

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "add_column without inline FK, then create_foreign_key separately for named constraint — enables clean downgrade by dropping FK by name"
    - "UniqueConstraint in __table_args__ tuple matches migration op.create_unique_constraint — must be in sync"
    - "Multiple FKs to same table require foreign_keys= on ALL relationships from both sides (Contact.deals, Company.deals, Deal.contact, Deal.company)"

key-files:
  created:
    - alembic/versions/0008_deal_pe_fields.py
    - alembic/versions/0009_deal_team_members.py
  modified:
    - backend/models.py

key-decisions:
  - "fund_id already in Deal ORM from Plan 01 — 0008 migration adds it to DB table; ORM Mapped[Optional[UUID]] type kept (not changed to String(36)) for consistency with other UUID FKs"
  - "Separate create_foreign_key calls after add_column enables named FK constraints for clean downgrade — inline sa.ForeignKey() does not produce named constraints in Alembic"
  - "Multiple FK paths require foreign_keys= disambiguation on both sides of relationship: Contact.deals='Deal.contact_id', Company.deals='Deal.company_id', Deal.contact=[contact_id], Deal.company=[company_id]"

# Metrics
duration: 4min
completed: 2026-03-27
---

# Phase 4 Plan 02: Deal PE Fields Migration & ORM Expansion Summary

**32 PE Blueprint columns added to Deal model via migrations 0008/0009, DealTeamMember M2M class, named FK constraints for all ref_data/company/contact/user FK columns**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-27T23:16:22Z
- **Completed:** 2026-03-27T23:20:19Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Migration 0008_deal_pe_fields: adds 32 columns to deals table — description, new_deal_date, transaction_type_id, fund_id, platform_or_addon, platform_company_id, source_type_id, source_company_id, source_individual_id, originator_id, 4 financial pairs (revenue, EBITDA, EV, equity investment), 2 bid pairs (LOI, IOI), 8 date milestones (CIM, IOI due/submitted, management presentation, LOI due/submitted, live diligence, portfolio company), passed_dead_date/reasons/commentary, legacy_id with uq_deals_org_legacy_id unique constraint
- Migration 0009_deal_team_members: creates deal_team_members M2M table with composite PK (deal_id, user_id) and two lookup indexes
- Migration chain: 0007_fund -> 0008_deal_pe_fields -> 0009_deal_team_members
- DealTeamMember ORM class added to backend/models.py
- Deal.__table_args__ extended with UniqueConstraint("org_id", "legacy_id", name="uq_deals_org_legacy_id")
- All 32 new columns added to Deal class with correct types (Numeric(18,2), Date, Text, String, JSONVariant for passed_dead_reasons)
- New relationships: deal_team_members (cascade delete), platform_company, source_company, source_individual, originator (all with foreign_keys= specified)
- 17 existing tests pass — no regressions

## Task Commits

1. **Task 1: Deal PE fields migration (0008) and deal_team_members migration (0009)** - `32468da` (feat)
2. **Task 2: Deal ORM model expansion + DealTeamMember class** - `782c860` (feat)

## Files Created/Modified

- `alembic/versions/0008_deal_pe_fields.py` — adds 32 PE columns to deals table with named FK constraints
- `alembic/versions/0009_deal_team_members.py` — creates deal_team_members M2M association table
- `backend/models.py` — DealTeamMember class, UniqueConstraint in Deal.__table_args__, 32 new PE columns, new relationships with disambiguated foreign_keys

## Decisions Made

- fund_id was already added to the Deal ORM by Plan 01 — 0008 migration adds it to the actual DB table; the ORM type (Mapped[Optional[UUID]]) is consistent with other UUID FK columns on Deal
- Named FK constraints created via separate `create_foreign_key()` calls rather than inline `sa.ForeignKey()` — this enables targeted `drop_constraint()` by name in downgrade()
- All relationships with ambiguous FK paths explicitly specify `foreign_keys=` — required because Deal now has 3 FKs to companies, 2 to contacts, and 2 to users

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed AmbiguousForeignKeysError after adding multiple FK paths to same tables**
- **Found during:** Task 2 (running test_health.py after model expansion)
- **Issue:** Deal now has company_id + platform_company_id + source_company_id (3 FKs to companies) and contact_id + source_individual_id (2 FKs to contacts) and owner_id + originator_id (2 FKs to users). SQLAlchemy cannot auto-detect which FK to use for Contact.deals and Company.deals back-references.
- **Fix:** Added `foreign_keys="Deal.contact_id"` to Contact.deals, `foreign_keys="Deal.company_id"` to Company.deals, and `foreign_keys=[contact_id]` to Deal.contact, `foreign_keys=[company_id]` to Deal.company
- **Files modified:** backend/models.py
- **Verification:** All 17 tests pass after fix
- **Committed in:** 782c860 (Task 2 commit)

## Known Stubs

None — this plan only creates migrations and ORM model, no UI or service layer.

## Self-Check: PASSED

All created files exist on disk. Both task commits (32468da, 782c860) confirmed in git log.

---
*Phase: 04-deal-model-expansion-fund-entity*
*Completed: 2026-03-27*
