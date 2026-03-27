---
phase: 03-contact-company-model-expansion
plan: "04"
subsystem: backend
tags: [company, api, schemas, service, pydantic, sqlalchemy, ref-data, pe-blueprint]
dependency_graph:
  requires: ["03-03"]
  provides: ["03-05", "03-06"]
  affects: ["backend/schemas/companies.py", "backend/services/companies.py"]
tech_stack:
  added: []
  patterns: ["aliased(RefData) multi-join pattern", "Decimal->float conversion in _company_response"]
key_files:
  created:
    - backend/schemas/companies.py
    - backend/services/companies.py
  modified: []
decisions:
  - "Loop-based field assignment in update_company and create_company for PE scalar fields (avoids repetitive if/setattr blocks)"
  - "CoverageUser aliased User join uses func.coalesce(CoverageUser.full_name, CoverageUser.username) matching user_name_expr() pattern"
  - "JSONB list fields (company_sub_type_ids, sector_preferences, sub_sector_preferences, transaction_types) handled separately from scalar loop — direct assignment replaces array"
metrics:
  duration: "2 minutes"
  completed: "2026-03-27"
  tasks: 2
  files: 2
---

# Phase 3 Plan 04: Company Service and API Summary

**One-liner:** Company API expanded with 4 aliased RefData joins resolving company_type, tier, sector, and sub_sector labels plus coverage_person_name, PATCH accepting all 32 PE Blueprint fields.

## What Was Built

- `backend/schemas/companies.py` — CompanyCreate and CompanyUpdate now accept all 32 PE Blueprint fields (all optional); CompanyResponse includes resolved labels: `company_type_label`, `tier_label`, `sector_label`, `sub_sector_label`, `coverage_person_name`; JSONB list fields use `Field(default_factory=list)`; Decimal financial fields typed as `float | None`

- `backend/services/companies.py` — CompanyService._base_stmt() updated with 4 aliased(RefData) outerjoins (CompanyTypeRef, TierRef, SectorRef, SubSectorRef) plus 1 aliased(User) outerjoin (CoverageUser) for coverage_person_name; _company_response() maps all 32 new PE fields with Decimal->float coercion; create_company() and update_company() handle all new fields including JSONB lists

## Requirements Satisfied

- COMPANY-10: Company API responses include resolved labels for all FK ref_data fields and coverage person display name

## Deviations from Plan

None — plan executed exactly as written. The loop-based field assignment pattern (for field in [...]: getattr/setattr) was used instead of individual if-blocks, which is equivalent and more maintainable.

## Self-Check

### Files Exist
- backend/schemas/companies.py — FOUND
- backend/services/companies.py — FOUND

### Commits Exist
- 1aee565 feat(03-04): expand CompanyCreate/Update/Response schemas — FOUND
- 8ad985b feat(03-04): expand CompanyService with PE Blueprint field support — FOUND

## Self-Check: PASSED
