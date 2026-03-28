---
phase: 05-deal-counterparty-deal-funding
plan: "04"
subsystem: frontend
tags: [counterparties, funding, deal-detail, tabs, react, tanstack-query]
dependency_graph:
  requires: ["05-02", "05-03"]
  provides: ["CPARTY-09", "CPARTY-10", "CPARTY-11", "CPARTY-12", "FUNDING-08", "FUNDING-09"]
  affects: ["frontend/src/pages/DealDetailPage.jsx"]
tech_stack:
  added: []
  patterns:
    - "useMutation + invalidateQueries per-tab CRUD pattern"
    - "inline date input via editingCell state key format: row.id + '-' + fieldName"
    - "sticky left-0 z-10 bg-white for grid column pinning"
    - "cleanFormData: empty string -> null coercion before API calls"
key_files:
  created:
    - frontend/src/api/counterparties.js
    - frontend/src/api/funding.js
  modified:
    - frontend/src/pages/DealDetailPage.jsx
decisions:
  - "CounterpartiesTab and FundingTab defined as module-level components (not inline) to avoid hook rules violations in conditional JSX"
  - "stageDateCols defined inside CounterpartiesTab to colocate config with usage"
  - "editingCell state uses `${rowId}-${fieldName}` composite key to identify which cell is active without a 2D data structure"
  - "cleanFormData helper converts empty strings to null before PATCH to avoid sending empty string to server (backend expects null for optional fields)"
metrics:
  duration: "8min"
  completed_date: "2026-03-28"
  tasks_completed: 1
  tasks_total: 2
  files_modified: 3
  checkpoint_reached: true
  checkpoint_type: human-verify
---

# Phase 05 Plan 04: Counterparties & Funding Tabs Summary

**One-liner:** DealDetailPage expanded from 4 to 6 tabs with full Counterparties grid (inline date editing, sticky column, CRUD modals) and Funding table (modal-based CRUD, commitment tracking).

## Status

**PAUSED AT CHECKPOINT** — Task 1 complete and committed. Task 2 is a `checkpoint:human-verify` requiring visual confirmation in the browser.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | API modules + Counterparties tab + Funding tab | 8a7539a | counterparties.js, funding.js, DealDetailPage.jsx |

## Task 2 (Checkpoint)

**Type:** human-verify
**Blocked by:** Visual verification of Counterparties and Funding tabs in browser

## What Was Built

### frontend/src/api/counterparties.js
- `getCounterparties(dealId, params)` — GET /deals/{id}/counterparties
- `createCounterparty(dealId, data)` — POST /deals/{id}/counterparties
- `updateCounterparty(dealId, id, data)` — PATCH /deals/{id}/counterparties/{cid}
- `deleteCounterparty(dealId, id)` — DELETE /deals/{id}/counterparties/{cid}

### frontend/src/api/funding.js
- `getFunding(dealId, params)` — GET /deals/{id}/funding
- `createFunding(dealId, data)` — POST /deals/{id}/funding
- `updateFunding(dealId, id, data)` — PATCH /deals/{id}/funding/{fid}
- `deleteFunding(dealId, id)` — DELETE /deals/{id}/funding/{fid}

### frontend/src/pages/DealDetailPage.jsx
- Added `Trash2` to lucide-react imports
- Imported both new API modules
- Expanded tab strip: Profile | Counterparties | Funding | Activity | Tasks | AI Insights
- `CounterpartiesTab` component:
  - Horizontally scrollable grid (`overflow-x-auto`) with sticky Company column (`sticky left-0 z-10 bg-white`)
  - Grid columns: Company, Tier, Investor Type, NDA Sent, NDA Signed, NRL, Materials, VDR, Feedback, Next Steps, Actions
  - Inline date editing via `editingCell` state — click cell to activate `<input type="date">`, blur to deactivate
  - Abbreviated date display: "Mar 15" format
  - Add modal: Company (required), Tier, Investor Type, Primary Contact Name, Check Size, Next Steps
  - Edit modal: all fields including AUM, email, phone, notes, all 6 stage dates
  - Delete with toast feedback
  - Empty state per D-08
  - Null labels render as `'---'` per D-21
- `FundingTab` component:
  - Standard table (no horizontal scroll)
  - Columns: Provider, Status, Projected, Actual, Date, Terms (truncated), Actions
  - Single modal for add + edit (pre-populated in edit mode)
  - Fields: Capital Provider (company select), Status (RefSelect deal_funding_status), Projected/Actual commitment amount+currency, Commitment Date, Terms, Comments/Next Steps
  - Delete with toast feedback
  - Empty state per D-12

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — both tabs are fully wired to real API endpoints.

## Self-Check: PENDING

Will be completed after checkpoint approval.
