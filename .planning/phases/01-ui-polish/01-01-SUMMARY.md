---
phase: 01-ui-polish
plan: 01
subsystem: ui
tags: [react, tailwind, vite, vitest, zustand, dark-mode, login]

# Dependency graph
requires: []
provides:
  - Tailwind darkMode: 'class' strategy enabled
  - Permanent dark class applied on document mount via Layout useEffect
  - Simplified useUIStore without theme state (sidebar only)
  - Redesigned LoginPage with TWG branding, staging banner, backend status indicator
affects: [all-frontend-phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dark mode locked via classList.add('dark') in Layout useEffect — no toggle, no state"
    - "vi.hoisted() pattern for vitest mock factories that reference top-level variables"

key-files:
  created:
    - frontend/src/pages/LoginPage.jsx
    - frontend/src/__tests__/LoginPage.test.jsx
  modified:
    - frontend/tailwind.config.js
    - frontend/index.html
    - frontend/src/store/useUIStore.js
    - frontend/src/components/Layout.jsx

key-decisions:
  - "Dark mode locked permanently via classList.add('dark') — no user toggle, no theme state in store"
  - "Email label (htmlFor=email) while keeping form.register('username') for API compatibility"
  - "vi.hoisted() used in tests so mock factories can reference variables declared at top level"

patterns-established:
  - "Pattern 1: Dark mode only — all new UI components assume dark: classes always active"
  - "Pattern 2: Login page health check via fetch('/health') proxied to backend"

requirements-completed: [UI-01]

# Metrics
duration: 2min
completed: 2026-03-26
---

# Phase 01 Plan 01: Dark Mode Lock and Login Redesign Summary

**Tailwind dark-mode-class strategy locked, useUIStore stripped of theme state, LoginPage redesigned with TWG GLOBAL branding, staging environment banner, and /health backend status indicator**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-27T02:41:04Z
- **Completed:** 2026-03-27T02:43:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- App permanently applies `.dark` class on mount — no theme toggle anywhere, no beige flash on load
- LoginPage shows TWG GLOBAL branding, Nexus CRM h1, staging environment banner (hidden in production), and color-coded backend status dot wired to `/health`
- All 4 LoginPage tests pass including new tests for status indicator and staging banner

## Task Commits

Each task was committed atomically:

1. **Task 1: Dark mode infrastructure lock** - `5c3eaff` (feat)
2. **Task 2: Login page redesign with branding and status indicator** - `664e283` (feat)

**Plan metadata:** (to be created in final commit)

## Files Created/Modified

- `frontend/tailwind.config.js` - Added `darkMode: 'class'` as top-level key
- `frontend/index.html` - Replaced beige body fallback with dark (#0f172a / #e2e8f0)
- `frontend/src/store/useUIStore.js` - Removed theme/setTheme state, sidebar only
- `frontend/src/components/Layout.jsx` - Permanent dark class lock, theme toggle removed from dropdown
- `frontend/src/pages/LoginPage.jsx` - Full redesign: TWG branding, staging banner, /health status indicator, Email label
- `frontend/src/__tests__/LoginPage.test.jsx` - Updated label queries, fixed vi.hoisted() pattern, added 2 new tests

## Decisions Made

- Used `vi.hoisted()` for vitest mock factories — the original test file had a pre-existing `Cannot access before initialization` bug from using top-level `vi.fn()` variables inside `vi.mock()` factories; vi.hoisted() is the correct vitest pattern
- Email label uses `htmlFor="email"` but `form.register('username')` stays unchanged — backend API expects `username` field, but the UI label shows "Email" for clarity to users

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed missing rollup native binary preventing test execution**
- **Found during:** Task 2 (running tests)
- **Issue:** `@rollup/rollup-darwin-x64` missing — known npm optional dependency bug
- **Fix:** Removed `node_modules` and `package-lock.json`, ran `npm install` fresh
- **Files modified:** `frontend/node_modules/` (not committed), `frontend/package-lock.json`
- **Verification:** Tests ran successfully after reinstall
- **Committed in:** Part of Task 2 flow (package-lock.json regenerated)

**2. [Rule 1 - Bug] Fixed vi.hoisted() pattern in LoginPage tests**
- **Found during:** Task 2 (test execution)
- **Issue:** Original test file used top-level `vi.fn()` variables inside `vi.mock()` factories — vitest hoists `vi.mock()` calls above variable declarations, causing `Cannot access 'error' before initialization`
- **Fix:** Replaced `const error = vi.fn()` pattern with `vi.hoisted(() => ({ ... }))` which is evaluated before mock hoisting
- **Files modified:** `frontend/src/__tests__/LoginPage.test.jsx`
- **Verification:** All 4 LoginPage tests pass
- **Committed in:** `664e283` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking environment issue, 1 pre-existing test bug)
**Impact on plan:** Both fixes necessary for tests to run. No scope creep.

## Issues Encountered

- Pre-existing vitest `vi.mock()` hoisting bug existed in the original test file (and appears to affect PipelinePage and DealDetailPage tests too — those are out of scope for this plan and logged to deferred items)

## Known Stubs

- `{/* TODO: replace with actual logo */}` in `frontend/src/pages/LoginPage.jsx` — TWG GLOBAL is currently rendered as a text span. The plan documents this intentionally. A future plan will replace with the actual logo asset once available.

## Next Phase Readiness

- Dark mode foundation is locked — all subsequent UI plans can safely use `dark:` Tailwind utilities
- LoginPage is the first user-facing screen and now matches branding requirements
- Pre-existing test failures in PipelinePage and DealDetailPage are out of scope; deferred

---
*Phase: 01-ui-polish*
*Completed: 2026-03-26*
