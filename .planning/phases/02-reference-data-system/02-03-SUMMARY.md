---
phase: 02-reference-data-system
plan: 03
subsystem: ui
tags: [react, tanstack-query, vitest, testing-library, ref-data, dropdown]

# Dependency graph
requires:
  - phase: 02-reference-data-system/02-02
    provides: GET /api/v1/admin/ref-data?category= endpoint operational; RefDataResponse schema with id, label, value, category, position, is_active
provides:
  - getRefData, createRefData, updateRefData API functions in frontend/src/api/refData.js
  - useRefData(category) TanStack Query hook with queryKey ['ref', category] and staleTime 5min
  - RefSelect component wrapping Select primitive with loading/error/empty/normal states
  - 6 RefSelect component tests passing in RefSelect.test.jsx
affects: [03-contact-company-expansion, 04-deal-expansion, 05-dealcounterparty-dealfunding, 06-admin-ref-data-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "useRefData hook: queryKey ['ref', category] — canonical key for all downstream phases (3-6)"
    - "RefSelect: wraps Select primitive (not copy-pasted) — consistent UI via composition"
    - "Option value=item.id (UUID), not item.value (slug) — backend FK pattern"
    - "Loading state: opacity-50 wrapper + disabled select; Error state: border-danger class + disabled select"
    - "vi.mock('@/hooks/useRefData') then import after — Vitest module mock pattern for hooks"

key-files:
  created:
    - frontend/src/api/refData.js
    - frontend/src/hooks/useRefData.js
    - frontend/src/components/RefSelect.jsx
    - frontend/src/__tests__/RefSelect.test.jsx
  modified: []

key-decisions:
  - "Option value uses item.id (UUID) not item.value (slug) — aligns with backend FK references to ref_data.id"
  - "enabled: Boolean(category) guard prevents spurious fetches when category prop is undefined/null"
  - "updateRefData uses PATCH not PUT — matches backend /admin/ref-data/{id} endpoint method"

patterns-established:
  - "Pattern 7: useRefData queryKey ['ref', category] — ALL downstream phases must use this exact key for cache sharing"
  - "Pattern 8: RefSelect composition — wrap Select primitive, never copy-paste native select styles"
  - "Pattern 9: TDD for UI components — RED (test file) committed separately from GREEN (component)"

requirements-completed: [REFDATA-11]

# Metrics
duration: 5min
completed: 2026-03-27
---

# Phase 2 Plan 03: Reference Data System Summary

**TanStack Query hook (useRefData), API module (refData.js), and RefSelect dropdown component with 6 passing tests — canonical ref_data frontend infrastructure for Phases 3-6**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-27T12:44:35Z
- **Completed:** 2026-03-27T12:49:33Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `frontend/src/api/refData.js` with getRefData (GET /admin/ref-data?category=), createRefData (POST), updateRefData (PATCH) matching canonical API module pattern from contacts.js
- Created `frontend/src/hooks/useRefData.js` with queryKey ['ref', category], staleTime 5*60*1000, enabled Boolean(category) guard — canonical hook for all downstream phases
- Created `frontend/src/components/RefSelect.jsx` wrapping Select primitive with 4 states: loading (opacity-50 + disabled), error (border-danger + disabled), empty (no options available), normal (placeholder + UUID-valued options)
- Created `frontend/src/__tests__/RefSelect.test.jsx` with 6 tests covering all states — all pass green

## Task Commits

Each task was committed atomically:

1. **Task 1: API module + useRefData hook** - `221ac8a` (feat)
2. **Task 2 RED: Failing tests for RefSelect** - `db7071e` (test)
3. **Task 2 GREEN: RefSelect component implementation** - `3d9189f` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `frontend/src/api/refData.js` - getRefData/createRefData/updateRefData API functions against /admin/ref-data
- `frontend/src/hooks/useRefData.js` - useRefData(category) with queryKey ['ref', category], staleTime 5min, enabled guard
- `frontend/src/components/RefSelect.jsx` - Dropdown component with loading/error/empty/normal states; option value=item.id
- `frontend/src/__tests__/RefSelect.test.jsx` - 6 component tests mocking useRefData; all pass green

## Decisions Made

- Option value attribute uses `item.id` (UUID) not `item.value` (slug) — backend FK references use ref_data.id, so form submissions must send UUIDs
- `enabled: Boolean(category)` guard added per plan spec — prevents TanStack Query from fetching when category is undefined/null (e.g., during component mounting before category prop is set)
- `updateRefData` uses PATCH not PUT — matches the backend PATCH /admin/ref-data/{id} endpoint established in 02-02

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `useRefData(category)` ready for import in Phases 3-6 contact/company/deal forms
- `RefSelect` ready for use: `<RefSelect category="sector" value={val} onChange={fn} placeholder="Select sector" />`
- queryKey `['ref', category]` established — downstream phases should NOT use a different key pattern for ref_data queries
- All 6 RefSelect tests pass; 4 pre-existing test failures in other test files are unrelated to this plan

## Self-Check: PASSED

- FOUND: frontend/src/api/refData.js (worktree)
- FOUND: frontend/src/hooks/useRefData.js (worktree)
- FOUND: frontend/src/components/RefSelect.jsx (worktree)
- FOUND: frontend/src/__tests__/RefSelect.test.jsx (worktree)
- FOUND commit: 221ac8a (API module + hook)
- FOUND commit: db7071e (failing tests)
- FOUND commit: 3d9189f (RefSelect component)
- Tests: 6/6 passing in RefSelect.test.jsx

---
*Phase: 02-reference-data-system*
*Completed: 2026-03-27*
