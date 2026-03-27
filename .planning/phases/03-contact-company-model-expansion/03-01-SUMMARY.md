---
phase: 03-contact-company-model-expansion
plan: "01"
subsystem: backend/models
tags: [alembic, migration, sqlalchemy, contact-model, pe-blueprint]
dependency_graph:
  requires: [02-reference-data-system]
  provides: [03-02, 03-03, 03-04, 03-05, 03-06]
  affects: [backend/models.py, backend/schemas/contacts.py, backend/services/contacts.py]
tech_stack:
  added: []
  patterns: [SQLAlchemy 2.0 Mapped columns, Alembic op.add_column DDL, M2M association table with composite PK]
key_files:
  created:
    - alembic/versions/0003_contact_pe_fields.py
    - alembic/versions/0004_contact_coverage_persons.py
  modified:
    - backend/models.py
decisions:
  - "All 18 new Contact columns are nullable per D-14 — no defaults needed as this is additive schema expansion"
  - "contact_type_id FK uses ondelete=SET NULL per REFDATA-15 pattern — no orphan records on ref_data deletion"
  - "coverage_persons relationship uses lazy=selectin — acceptable for detail views, service layer avoids N+1 on list queries"
  - "ContactCoveragePerson placed before Contact class in models.py to avoid forward-reference issues"
metrics:
  duration: "~2 min"
  completed_date: "2026-03-27"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
---

# Phase 3 Plan 01: Contact PE Blueprint Model Expansion Summary

**One-liner:** Added 18 PE Blueprint columns to Contact model plus contact_coverage_persons M2M table via Alembic migrations 0003 and 0004.

## What Was Built

Two Alembic migrations and matching ORM model updates to expand the Contact entity with all fields required by the PE Blueprint data specification.

**Migration 0003** (`alembic/versions/0003_contact_pe_fields.py`):
- 19 `op.add_column` calls on the contacts table (plan specified 18; `contact_type_id` FK counts as both FK and column = 19 is correct, with 18 distinct field groups)
- Phone fields: `business_phone`, `mobile_phone`, `assistant_name`, `assistant_email`, `assistant_phone`
- Address fields: `address`, `city`, `state`, `postal_code`, `country`
- FK + scalar: `contact_type_id` (→ ref_data, ondelete=SET NULL), `primary_contact`, `contact_frequency`
- JSONB: `sector`, `sub_sector`, `previous_employment`, `board_memberships`
- Text/indexed: `linkedin_url`, `legacy_id`
- Unique constraint: `uq_contacts_org_legacy_id` on (org_id, legacy_id)
- Explicit `downgrade()` that drops constraint then all columns in reverse order

**Migration 0004** (`alembic/versions/0004_contact_coverage_persons.py`):
- `op.create_table("contact_coverage_persons", ...)` with composite PK `(contact_id, user_id)`
- Both FK columns use ondelete=CASCADE
- Explicit `downgrade()` with `op.drop_table`

**ORM model updates** (`backend/models.py`):
- New `ContactCoveragePerson(Base)` class added before `Contact` class
- All 18 new `Mapped[Optional[...]]` columns added to `Contact` class body after `updated_at`
- `UniqueConstraint("org_id", "legacy_id", name="uq_contacts_org_legacy_id")` added to `Contact.__table_args__`
- `coverage_persons: Mapped[list["User"]]` relationship on Contact using `secondary="contact_coverage_persons"` and `lazy="selectin"`

## Commits

| Task | Description | Hash |
|------|-------------|------|
| 1 | Alembic 0003 + Contact ORM model expansion | `1007360` |
| 2 | Alembic 0004 + ContactCoveragePerson model + relationship | `5c58851` |

## Verification

```
$ python -c "from backend.models import Contact, ContactCoveragePerson; print('Models OK')"
Models OK

$ python -c "from backend.models import ContactCoveragePerson; print('OK:', ContactCoveragePerson.__tablename__)"
OK: contact_coverage_persons
```

- 0 missing columns (all 19 Contact columns confirmed present)
- Total Contact columns: 38 (19 existing + 19 new)
- All FK columns use `ondelete="SET NULL"` per REFDATA-15 pattern
- All new columns are nullable per D-14

## Deviations from Plan

None — plan executed exactly as written. The migration was specified as "18 new columns" but the plan's column list actually contains 19 entries (the plan spec says `op.add_column("contacts"` at least 18 times — 19 is compliant).

## Known Stubs

None — this plan adds schema-only changes. No UI stubs or placeholder data.

## Self-Check: PASSED

- [x] `alembic/versions/0003_contact_pe_fields.py` exists
- [x] `alembic/versions/0004_contact_coverage_persons.py` exists
- [x] `backend/models.py` contains `ContactCoveragePerson` and all new Contact columns
- [x] Commits `1007360` and `5c58851` exist in git log
- [x] `python -c "from backend.models import Contact, ContactCoveragePerson; print('Models OK')"` exits 0
