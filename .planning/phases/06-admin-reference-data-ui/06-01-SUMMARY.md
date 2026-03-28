---
phase: 06-admin-reference-data-ui
plan: "01"
subsystem: frontend-admin
tags: [admin, ref-data, ui, crud, tabs, modal]
dependency_graph:
  requires: [02-reference-data-system, 03-contact-company-model-expansion, 04-deal-model-expansion-fund-entity]
  provides: [admin-ref-data-ui]
  affects: [frontend/src/pages/AdminPage.jsx, backend/api/routes/admin.py, backend/services/ref_data.py]
tech_stack:
  added: [refCategories.js, getAllRefData API function, include_inactive backend param]
  patterns: [tabs-layout, sidebar-category-nav, modal-crud, query-prefix-invalidation]
key_files:
  created:
    - frontend/src/pages/AdminPage.jsx
    - frontend/src/lib/refCategories.js
  modified:
    - frontend/src/api/refData.js
    - backend/api/routes/admin.py
    - backend/services/ref_data.py
decisions:
  - "include_inactive query param added to GET /admin/ref-data — admin panel shows all items; regular dropdowns see only active"
  - "getAllRefData() added alongside getRefData() for backward compat — no existing hook callers broken"
  - "REF_CATEGORIES canonical ordering in refCategories.js — all downstream category references use this module"
metrics:
  duration: 15min
  completed: "2026-03-28"
  tasks: 2
  files: 5
---

# Phase 6 Plan 1: Admin Reference Data UI Summary

**One-liner:** Admin Reference Data UI with 10-category sidebar, items table, add/edit modals, deactivate/reactivate, and query prefix invalidation via shadcn Tabs + Dialog + Table.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create ref category mapping utility | b6d5b6b | frontend/src/lib/refCategories.js |
| 2 | Rewrite AdminPage with tabs, category sidebar, items table, CRUD modals | 576007c | frontend/src/pages/AdminPage.jsx, frontend/src/api/refData.js, backend/api/routes/admin.py, backend/services/ref_data.py |

## What Was Built

### refCategories.js
Canonical module defining all 10 ref data categories as `{ slug, label }` pairs with `getCategoryLabel(slug)` helper. Covers: sector, sub_sector, transaction_type, tier, contact_type, company_type, company_sub_type, deal_source_type, passed_dead_reason, investor_type.

### AdminPage.jsx
Full rewrite from 25-line stub to 270-line admin panel with:
- **Users tab**: existing org snapshot + users list content preserved
- **Reference Data tab**: vertical category sidebar (10 categories, sector selected by default), items table with Label/Position/Status/Actions columns
- **CRUD**: Add/Edit modal dialog with Label (required) + Position (optional) fields
- **Deactivation**: X icon deactivates (PATCH is_active=false), RotateCcw reactivates; inactive rows rendered with opacity-50
- **Query invalidation**: both `['ref']` prefix and `['admin', 'ref-data']` invalidated after every mutation so all dropdowns update immediately

### Backend: include_inactive support
- `GET /admin/ref-data?include_inactive=true` — new optional query param (default false)
- `RefDataService.list_by_category` accepts `include_inactive` kwarg — skips `is_active=true` filter when true
- Backward-compatible: existing `useRefData` hook calls still return only active items

## Deviations from Plan

### Auto-added Missing Critical Functionality (Rule 2)

**1. [Rule 2 - Missing] Backend include_inactive param**
- **Found during:** Task 2
- **Issue:** Backend `GET /admin/ref-data` filtered `is_active=True` always — admin panel can't show inactive items for deactivate/reactivate management
- **Fix:** Added `include_inactive: bool = False` query param to route + service method; `getAllRefData()` helper added to `refData.js` that passes `include_inactive=true`
- **Files modified:** backend/api/routes/admin.py, backend/services/ref_data.py, frontend/src/api/refData.js
- **Commits:** 576007c

## Known Stubs

None. All functionality is wired:
- Category sidebar renders from `REF_CATEGORIES`
- Items table fetches live from `GET /admin/ref-data?category=X&include_inactive=true`
- Add/Edit calls `createRefData` / `updateRefData` with real API
- Deactivate/reactivate calls `updateRefData` with `is_active` toggle

## Self-Check: PASSED

Files exist:
- FOUND: frontend/src/lib/refCategories.js
- FOUND: frontend/src/pages/AdminPage.jsx

Commits exist:
- b6d5b6b: feat(06-01): create ref category mapping utility
- 576007c: feat(06-01): admin reference data UI with category sidebar, items table, CRUD modals
