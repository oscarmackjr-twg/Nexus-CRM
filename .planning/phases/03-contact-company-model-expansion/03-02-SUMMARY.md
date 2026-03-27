---
phase: 03-contact-company-model-expansion
plan: 02
subsystem: api
tags: [fastapi, sqlalchemy, pydantic, alembic, contacts, pe-blueprint]

requires:
  - phase: 03-01
    provides: Contact PE ORM columns (business_phone, mobile_phone, assistant_*, address, contact_type_id, JSONB fields, linkedin_url, legacy_id) + ContactCoveragePerson M2M table + migrations 0003/0004

provides:
  - Contact Pydantic schemas (Create/Update/Response) with all 20 PE Blueprint fields
  - contact_type_label resolved via aliased(RefData) join in ContactService._base_stmt
  - coverage_persons loaded as [{id, name}] on detail view via _load_coverage_persons
  - ContactService.update_contact handles PE scalar + JSONB + coverage_persons M2M delete+re-insert
  - ContactService.create_contact stores PE fields and initial coverage_persons
  - ContactActivityCreate schema for contact-level activity logging
  - ContactService.log_contact_activity creates DealActivity with deal_id=None
  - POST /contacts/{id}/activities route for contact-level activity logging
  - GET /users open to all authenticated users (not just org_admin)
  - Alembic migration 0006 merging 0004+0005 branches, deal_id nullable + contact_id FK

affects: [03-04, 03-05, 03-06, frontend-contact-detail, frontend-contact-list]

tech-stack:
  added: []
  patterns:
    - "aliased(RefData) pattern for join-resolved label in _base_stmt"
    - "coverage_persons=[] on list, coverage_persons loaded separately on detail (avoids N+1)"
    - "delete+re-insert pattern for M2M updates (ContactCoveragePerson)"
    - "Merge migration down_revision tuple for parallel branch resolution"

key-files:
  created:
    - backend/schemas/contacts.py
    - backend/services/contacts.py
    - backend/api/routes/contacts.py
    - backend/api/routes/auth.py
    - alembic/versions/0006_activity_deal_id_nullable.py
  modified:
    - backend/models.py

key-decisions:
  - "aliased(RefData) in _base_stmt() resolves contact_type_label server-side — no N+1"
  - "coverage_persons not loaded in list_contacts (passes []) — only loaded in get_contact to avoid N+1"
  - "0006 is a merge migration with down_revision tuple (0004, 0005) to resolve parallel branch heads"
  - "GET /users changed from require_org_admin to get_current_user — all roles need user list for coverage persons picker"
  - "ContactService.get_contact_activities updated with outerjoin(Deal) + OR filter to include contact-level activities"

patterns-established:
  - "aliased(RefData) outerjoin pattern — reuse in company/deal service for label resolution"
  - "Merge migration tuple syntax — use when multiple parallel migrations exist"
  - "contact-level DealActivity: deal_id=None, contact_id=str(contact_id)"

requirements-completed: [CONTACT-08, CONTACT-09, CONTACT-10]

duration: 20min
completed: 2026-03-27
---

# Phase 3 Plan 02: Contact API Expansion Summary

**Contact API fully expanded with 20 PE Blueprint fields, contact_type_label resolved server-side, coverage_persons M2M, contact-level activity logging, and deal_id nullable migration**

## Performance

- **Duration:** 20 min
- **Started:** 2026-03-27T20:00:00Z
- **Completed:** 2026-03-27T20:20:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- ContactResponse now exposes all 20 PE Blueprint fields (phones, assistant fields, address block, contact_type_id/label, primary_contact, contact_frequency, sector/sub_sector, previous_employment, board_memberships, linkedin_url, legacy_id, coverage_persons)
- contact_type_label resolved via aliased(RefData) outerjoin in _base_stmt — zero additional queries
- coverage_persons loaded as [{id, name}] only on detail view; list view passes [] to avoid N+1
- POST /contacts/{id}/activities route creates contact-level DealActivity with deal_id=None
- Migration 0006 merges the parallel 0004/0005 migration heads and makes deal_id nullable
- GET /users opened to all authenticated users to support coverage persons picker

## Task Commits

1. **Task 1: Contact schemas + service + label resolution + coverage_persons** - `c6d4c39` (feat)
2. **Task 2: Activity deal_id nullable migration + contact activity route + open /users** - `4e9c5d8` (feat)

## Files Created/Modified
- `backend/schemas/contacts.py` - ContactCreate/Update/Response with all PE fields, ContactActivityCreate schema
- `backend/services/contacts.py` - Full ContactService with aliased join, _load_coverage_persons, M2M update logic, log_contact_activity
- `backend/api/routes/contacts.py` - POST /{contact_id}/activities route added
- `backend/api/routes/auth.py` - GET /users changed to get_current_user
- `alembic/versions/0006_activity_deal_id_nullable.py` - Merge migration, deal_id nullable, contact_id FK
- `backend/models.py` - DealActivity.deal_id Optional[UUID], contact_id column added

## Decisions Made
- Used merge migration tuple `down_revision = ("0004_contact_coverage_persons", "0005_company_pe_fields")` to cleanly resolve parallel 0004/0005 heads from Wave 1 agents running concurrently
- coverage_persons loaded separately in get_contact() only — list_contacts() passes [] — avoids N+1 on list queries
- ContactService.get_contact_activities updated to use outerjoin(Deal) with OR filter to return both deal-tied and contact-level activities
- GET /users permission change: all authenticated users need user list to populate coverage persons picker (D-05 from 03-CONTEXT.md)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] get_contact_activities updated for nullable deal_id**
- **Found during:** Task 1 (Service implementation)
- **Issue:** Existing get_contact_activities used inner JOIN with Deal which would exclude contact-level activities (deal_id=None)
- **Fix:** Changed to outerjoin(Deal) and added OR filter: DealActivity.contact_id == contact_id OR Deal.contact_id == contact_id; added deal_id IS NULL handling in team scope filter
- **Files modified:** backend/services/contacts.py
- **Verification:** Service imports successfully, logic handles both activity types
- **Committed in:** c6d4c39 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Required fix for contact-level activities to work correctly after deal_id made nullable. No scope creep.

## Issues Encountered
- Worktree branch was behind main — fast-forwarded to bd24e37 to pick up 03-01 and 03-03 commits before starting
- Main repo files (contacts.py, auth.py etc.) were untracked, copied from main to worktree before modification

## Next Phase Readiness
- Contact API fully expanded — ready for 03-04 (Contact detail UI) and 03-05 (Company API expansion)
- coverage_persons picker can use GET /users (now open to all roles)
- contact_type RefSelect can use queryKey ['ref', 'contact_type'] per Phase 2 canonical pattern

---
*Phase: 03-contact-company-model-expansion*
*Completed: 2026-03-27*
