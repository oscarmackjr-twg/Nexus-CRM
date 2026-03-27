---
phase: 03-contact-company-model-expansion
plan: "06"
subsystem: frontend
tags: [company, ui, profile-tab, per-card-editing, refselect, chips, switch, tabs, pe-blueprint]
dependency_graph:
  requires: ["03-04"]
  provides: []
  affects: ["frontend/src/pages/CompanyDetailPage.jsx", "frontend/src/api/companies.js", "frontend/src/api/users.js"]
tech_stack:
  added: []
  patterns: ["per-card editing (editingIdentity/editingProfile/editingInternal bool state)", "chips+RefSelect add pattern for JSONB multi-select", "amount+currency side-by-side flex pairs", "useEffect JSONB array init from server data"]
key_files:
  created:
    - frontend/src/api/companies.js
    - frontend/src/api/users.js
  modified:
    - frontend/src/pages/CompanyDetailPage.jsx
decisions:
  - "Added updateCompany PATCH to companies API (was missing) — blocked implementation without it (Rule 3 auto-fix)"
  - "Added users.js API module with getUsers — worktree had no tracked users.js; needed for coverage_person_id picker (Rule 3 auto-fix)"
  - "Removed getCompanies import from CompanyDetailPage (imported from plan spec but unused — parent company uses text input not typeahead per plan note)"
metrics:
  duration: "4 minutes"
  completed: "2026-03-27"
  tasks: 1
  files: 3
---

# Phase 3 Plan 06: Company Profile Tab UI Summary

**One-liner:** CompanyDetailPage rebuilt with Profile tab (default) containing Identity, Investment Profile, and Internal section cards — per-card editing, chips+RefSelect for multi-select JSONB fields, amount+currency side-by-side pairs, Switch for booleans.

## What Was Built

**`frontend/src/pages/CompanyDetailPage.jsx`** — Complete rebuild from 46-line stub to 754-line full detail page:

- `<Tabs defaultValue="profile">` with 4 tabs: Profile | Contacts | Deals | LinkedIn
- **Card 1 — Identity:** company_type_id (RefSelect), company_sub_type_ids (chips+RefSelect pattern), tier_id (RefSelect), sector_id (RefSelect), sub_sector_id (RefSelect), description (Textarea), main_phone (Input tel), parent_company_id (Input text), address/city/state/postal_code/country fields
- **Card 2 — Investment Profile:** AUM (amount+currency pair), EBITDA (amount+currency pair), EBITDA range (min+max+currency triple), bite size (low+high+currency triple), co_invest (Switch), transaction_types/sector_preferences/sub_sector_preferences (chips+RefSelect), preference_notes (Textarea)
- **Card 3 — Internal:** watchlist (Switch + accent Badge on name), coverage_person_id (native Select from /users), contact_frequency (Input number), legacy_id (Input)
- Per-card editing: `editingIdentity`, `editingProfile`, `editingInternal` boolean state with Edit3 icon toggle in CardHeader
- All aria-labels per UI-SPEC: "Edit Identity", "Edit Investment Profile", "Edit Internal", "Remove {value}" on chip × buttons
- JSONB arrays initialized from server data via `useEffect` on company load
- Watchlist Badge variant="accent" shown next to h1 company name when watchlist=true
- Contacts/Deals tabs preserve existing functionality (linked contacts/deals lists)
- LinkedIn tab wraps LinkedInPanel with sync capability

**`frontend/src/api/companies.js`** — Added `updateCompany` (PATCH /companies/{id}) alongside existing functions.

**`frontend/src/api/users.js`** — New module with `getUsers` for coverage person picker.

## Requirements Satisfied

- COMPANY-11: All PE Blueprint company fields surfaced in UI with editing capability
- COMPANY-12: Investment Profile fields (AUM, EBITDA, bite sizes, co-invest, preferences) editable in organized card

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing updateCompany in frontend API**
- **Found during:** Task 1
- **Issue:** `frontend/src/api/companies.js` had no `updateCompany` PATCH function — CompanyDetailPage couldn't save without it
- **Fix:** Added `updateCompany` export to companies API
- **Files modified:** `frontend/src/api/companies.js`
- **Commit:** 268e3de

**2. [Rule 3 - Blocking] Missing users.js API module in worktree**
- **Found during:** Task 1
- **Issue:** `frontend/src/api/users.js` did not exist in the worktree's git history — `getUsers` function needed for coverage person picker
- **Fix:** Created `frontend/src/api/users.js` with `getUsers` function
- **Files modified:** `frontend/src/api/users.js` (created)
- **Commit:** 268e3de

**3. [Rule 1 - Bug] Removed unused getCompanies import**
- **Found during:** Task 1 review
- **Issue:** Plan action imported `getCompanies` but parent company field uses a text Input (not typeahead), so the import was unused
- **Fix:** Removed `getCompanies` from import statement
- **Files modified:** `frontend/src/pages/CompanyDetailPage.jsx`
- **Commit:** 268e3de

## Known Stubs

- **Parent company field** (`identityForm.parent_company_id`): Uses a plain text Input instead of a typeahead company search. The plan explicitly notes: "For now, use a simple `<Input placeholder='Search parent company...' />`. Full typeahead search can be a future enhancement." This is intentional — the field stores/saves the ID from the API, display shows the raw value. Not a functional blocker for Phase 3.

## Self-Check

### Files Exist
- frontend/src/pages/CompanyDetailPage.jsx — FOUND
- frontend/src/api/companies.js — FOUND
- frontend/src/api/users.js — FOUND

### Commits Exist
- 268e3de feat(03-06): CompanyDetailPage Profile tab with 3 section cards and per-card editing — FOUND

## Self-Check: PASSED
