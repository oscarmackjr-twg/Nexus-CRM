---
phase: 06-admin-reference-data-ui
plan: 02
subsystem: ui
tags: [react, ref-data, dropdowns, audit, refselect]

# Dependency graph
requires:
  - phase: 02-reference-data-system
    provides: RefSelect component + useRefData hook with ['ref', category] query keys
  - phase: 03-contact-company-model-expansion
    provides: ContactDetailPage and CompanyDetailPage with RefSelect wired for PE fields
  - phase: 04-deal-model-expansion-fund-entity
    provides: DealDetailPage with RefSelect wired for deal fields
  - phase: 05-deal-counterparty-deal-funding
    provides: Counterparty and Funding tab modals in DealDetailPage with RefSelect for tier/investor_type
provides:
  - Confirmed: no hardcoded ref_data option arrays across Contact, Company, Deal, DealCounterparty, or DealFunding pages
  - Verified: all 10 ref_data categories use RefSelect with ['ref', category] query keys
  - ADMIN-07 audit complete — admin ref_data changes propagate to all form dropdowns automatically
affects: [admin-reference-data-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ADMIN-07 pattern: all ref_data category dropdowns use RefSelect not native <select> with hardcoded options"
    - "Entity selectors (companies, contacts, users, funds) intentionally remain native <select> — these are NOT ref_data"
    - "App enums (activity_type, lifecycle_stage, platform/addon) intentionally remain hardcoded — these are model enums not ref_data"

key-files:
  created: []
  modified: []

key-decisions:
  - "ADMIN-07 audit: ContactDetailPage, CompanyDetailPage, DealDetailPage all confirmed clean — no ref_data dropdowns were hardcoded"
  - "Coverage person selectors (users from /users endpoint) are correctly NOT using RefSelect — they are entity selectors"
  - "Activity type dropdown (call/meeting/email/note) is an app enum, NOT a ref_data category — correctly left as hardcoded"
  - "Lifecycle stage dropdown (lead/mql/sql/opportunity/customer) is a Contact model enum, NOT ref_data — correctly left as hardcoded"
  - "platform/addon selector in DealDetailPage is a Deal model enum — correctly left as hardcoded"

patterns-established:
  - "Boundary rule: 10 ref_data categories use RefSelect; entity selectors + app model enums use native <select>"

requirements-completed: [ADMIN-07]

# Metrics
duration: 5min
completed: 2026-03-28
---

# Phase 6 Plan 02: Ref Data Dropdown Audit Summary

**ADMIN-07 audit confirmed: all 10 ref_data category dropdowns across Contact, Company, Deal, and DealCounterparty/DealFunding pages use RefSelect — zero hardcoded option lists for ref_data categories**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T17:48:51Z
- **Completed:** 2026-03-28T17:53:00Z
- **Tasks:** 1
- **Files modified:** 0

## Accomplishments

- Systematically audited all `<select>` and `<Select>` elements across ContactDetailPage, CompanyDetailPage, DealDetailPage, and ContactsPage
- Confirmed all 10 ref_data categories (sector, sub_sector, transaction_type, tier, contact_type, company_type, company_sub_type, deal_source_type, passed_dead_reason, investor_type) are wired to RefSelect with `['ref', category]` query keys
- Verified Vite build succeeds (2637 modules, no errors)
- No code changes required — previous phases already completed full wiring

## Audit Findings by Page

**ContactDetailPage.jsx** — 4 RefSelect usages (import + contact_type + sector + sub_sector)
- Coverage person selector: native `<select>` fetching from `/users` — CORRECT (entity selector, not ref_data)
- Activity type selector: hardcoded call/meeting/email/note — CORRECT (app enum, not ref_data)
- Linked deal selector: native `<select>` from deal list — CORRECT (entity selector, not ref_data)

**CompanyDetailPage.jsx** — 9 RefSelect usages (import + company_type + company_sub_type + tier + sector + sub_sector + transaction_type + sector preferences + sub_sector preferences)
- Coverage person selector: native `<Select>` fetching from `/users` — CORRECT (entity selector, not ref_data)

**DealDetailPage.jsx** — 10 RefSelect usages (import + tier + investor_type x2 + transaction_type + deal_source_type + passed_dead_reason x2 + counterparty tier + counterparty investor_type)
- Company selectors: native `<select>` fetching from `/companies` — CORRECT (entity selector)
- Fund selector: native `<select>` fetching from `/funds` — CORRECT (entity selector)
- Platform/addon selector: hardcoded "platform"/"addon" — CORRECT (Deal model enum)
- Team member / originator selectors: native `<select>` from `/users` — CORRECT (entity selectors)
- Source company/individual selectors: entity selectors — CORRECT

**ContactsPage.jsx** — 0 RefSelect usages needed
- Lifecycle stage filter: hardcoded stages array — CORRECT (Contact model enum, not ref_data)
- Owner filter: native `<Select>` from `/users` — CORRECT (entity selector)

## Task Commits

No code changes were required — all ref_data dropdowns were already correctly wired from previous phases.

1. **Task 1: Audit ref_data dropdowns** — no commit needed (read-only audit, all dropdowns already correct)

**Plan metadata:** see final docs commit

## Files Created/Modified

None — audit confirmed existing implementation is correct.

## Decisions Made

- ADMIN-07 boundary confirmed: the 10 ref_data categories (sector, sub_sector, transaction_type, tier, contact_type, company_type, company_sub_type, deal_source_type, passed_dead_reason, investor_type) all use RefSelect. Entity selectors and app model enums correctly remain as native selects.

## Deviations from Plan

None - plan executed exactly as written. The plan anticipated that no code changes would be needed and provided explicit verdicts for each page. Those verdicts were verified correct.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- ADMIN-07 confirmed complete — admin changes to any of the 10 ref_data categories will propagate to all form dropdowns across all pages
- Phase 6 Plan 03 (admin UI for managing ref_data from the frontend) can proceed — downstream wiring is confirmed ready

---
*Phase: 06-admin-reference-data-ui*
*Completed: 2026-03-28*
