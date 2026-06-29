---
phase: 18-access-enforcement
plan: "03"
subsystem: backend-counterparties-funding, frontend-deal-detail
tags: [authz, access-control, idor-close, deal-child-entities, 403-vs-404, tdd]
dependency_graph:
  requires: [18-02 (require_deal_readable/writable in backend/auth/access.py)]
  provides: [child-entity IDOR close, child cross-team 403, DealDetailPage 403 UX distinction]
  affects: [backend/services/counterparties.py, backend/services/funding.py, backend/tests/test_access_enforcement.py, frontend/src/pages/DealDetailPage.jsx]
tech_stack:
  added: []
  patterns: [require_deal_readable (read gate), require_deal_writable (write gate), load-then-decide child inheritance]
key_files:
  created: []
  modified:
    - backend/services/counterparties.py
    - backend/services/funding.py
    - backend/tests/test_access_enforcement.py
    - frontend/src/pages/DealDetailPage.jsx
decisions:
  - "require_deal_readable used for list_for_deal in both child services — inherits 403/404 split from parent deal guard"
  - "require_deal_writable used for create/update/delete in both child services — read-only parent access does not grant child mutation (Pitfall 7)"
  - "counterparties.py update/delete had NO deal gate at all — gate explicitly added (key observation #3 from PATTERNS.md)"
  - "funding.py raw integer 404 literals fixed to status.HTTP_404_NOT_FOUND for consistency"
  - "DealDetailPage isError branch reads error.response?.status — 403 shows permission message, any other error shows generic removed message"
  - "_get_deal_or_404 removed from both child services after guard replacement — single authz source in access.py"
metrics:
  duration: "~8min"
  completed: "2026-06-29"
  tasks: 2
  files: 4
---

# Phase 18 Plan 03: Deal Child Entity Guards + Frontend 403/404 Patch Summary

Closed the IDOR side-door (D-19) by wiring `require_deal_readable` and `require_deal_writable` through every `DealCounterpartyService` and `DealFundingService` method. A beta-team user can no longer read or mutate counterparties or funding entries belonging to an alpha-team deal. The `DealDetailPage.jsx` isError branch now distinguishes a 403 ("no permission") from a 404 ("may have been removed"). Full 36-test phase matrix is green.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Parent-deal guards on counterparties.py and funding.py | bba072a | backend/services/counterparties.py, backend/services/funding.py |
| 2 | Child-entity cross-team tests + DealDetailPage 403/404 patch | 1f2b2fd | backend/tests/test_access_enforcement.py, frontend/src/pages/DealDetailPage.jsx |
| 3 | Human verify 403 vs 404 messaging | (checkpoint) | — |

## Verification

- `pytest backend/tests/test_access_enforcement.py -x -q` — 36 passed (28 from waves 1+2, 8 new child-entity tests)
- `pytest backend/tests/ -q` — 68 passed, 4 xpassed, 1 pre-existing failure (test_ref_data.py fund_status count — unrelated)
- `grep "status === 403" frontend/src/pages/DealDetailPage.jsx` — matches line 949

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Fix] Fixed raw integer 404 literals in funding.py**
- **Found during:** Task 1 — `update` and `delete` methods used `HTTPException(status_code=404, ...)` raw integers
- **Issue:** `_get_deal_or_404` used `status_code=404` (raw integer) instead of `status.HTTP_404_NOT_FOUND`. After removing that method, two remaining raw 404s in `update` and `delete` (for the funding entry not-found case) also used raw integers.
- **Fix:** Added `status` to the `from fastapi import` line; replaced both raw `404` literals with `status.HTTP_404_NOT_FOUND`.
- **Files modified:** backend/services/funding.py
- **Commit:** bba072a

## Decisions Made

1. `require_deal_readable` (not `require_deal_writable`) for `list_for_deal` in both services — listing children is a read operation; the write guard would incorrectly block supervisors who can READ but not WRITE the parent deal from listing children.

2. `require_deal_writable` for `create`/`update`/`delete` in both child services — prevents read-only users (e.g. a Supervisor on a cross-group deal visible via Principal oversight) from mutating children (Pitfall 7 enforcement).

3. `DealCounterpartyService.update` and `.delete` previously had **no deal gate at all** — the plan identified this as "key observation #3". Gates added explicitly; no refactoring of the existing child-record select logic was needed.

4. `_get_deal_or_404` removed from both services — the shared guards in `access.py` are the single source of truth for 403/404 split. Removing the old method eliminates the dead org-only-scoped code path.

5. POST cross-team tests send a minimal valid body (`company_id` dummy UUID for counterparties, `{}` for funding) — the 403 is raised by `require_deal_writable` in the service before any DB insert, so body content is irrelevant to the access check.

## Threat Surface Scan

All mitigations from the plan's threat register applied:

| Threat ID | Mitigation Applied |
|-----------|-------------------|
| T-18-10 | `DealCounterpartyService` all methods gated by `require_deal_readable`/`require_deal_writable` |
| T-18-11 | `DealFundingService` all methods gated identically |
| T-18-12 | Child guards reuse the 403-vs-404 split from `require_deal_readable` — out-of-scope parent returns 403 |
| T-18-13 | create/update/delete use `require_deal_writable` (can_write_deal) not the read gate |

No new network endpoints or trust boundaries introduced.

## Known Stubs

None — all changes wire to live guards with real DB checks.

## Self-Check: PASSED

- [x] backend/services/counterparties.py — `require_deal_readable` in list, `require_deal_writable` in create/update/delete
- [x] backend/services/funding.py — same pattern; no raw 404 literals in deal-existence path
- [x] backend/tests/test_access_enforcement.py — 36 tests, all green
- [x] frontend/src/pages/DealDetailPage.jsx — `status === 403` on line 949
- [x] Commits bba072a, 1f2b2fd — verified in git log
