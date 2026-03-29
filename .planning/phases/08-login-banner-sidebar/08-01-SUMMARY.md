---
phase: 08-login-banner-sidebar
plan: "01"
subsystem: frontend/ui
tags: [login, branding, staging-banner, logo]
dependency_graph:
  requires: []
  provides: [StagingBanner component, TWG logo asset, branded login page]
  affects: [frontend/src/pages/LoginPage.jsx, frontend/src/components/StagingBanner.jsx]
tech_stack:
  added: []
  patterns: [VITE_APP_ENV env gate, bg-primary CSS variable button]
key_files:
  created:
    - frontend/src/assets/twg-logo.png
    - frontend/src/components/StagingBanner.jsx
  modified:
    - frontend/src/pages/LoginPage.jsx
    - frontend/src/__tests__/LoginPage.test.jsx
decisions:
  - "StagingBanner uses VITE_APP_ENV (not import.meta.env.MODE) per D-17 — explicit env flag, not build mode"
  - "Sign in button uses bg-primary CSS variable per D-20 — inherits navy (#1a3868) from Phase 7 theme"
  - "Logo uses h-10 w-auto sizing — preserves aspect ratio at fixed height"
metrics:
  duration: "~1 min"
  completed: "2026-03-29"
  tasks: 2
  files: 4
---

# Phase 08 Plan 01: Login Banner Sidebar — StagingBanner + Login Page Summary

TWG-branded login page with logo image, reusable StagingBanner component (VITE_APP_ENV-gated, amber-400, sticky), and navy primary button via bg-primary CSS variable.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Copy TWG logo asset and create StagingBanner component | 70cff5c | frontend/src/assets/twg-logo.png, frontend/src/components/StagingBanner.jsx |
| 2 | Update LoginPage with logo image, StagingBanner, and navy button + fix test | 89bc0ab | frontend/src/pages/LoginPage.jsx, frontend/src/__tests__/LoginPage.test.jsx |

## What Was Built

**StagingBanner.jsx** — reusable env-gated staging banner. Checks `import.meta.env.VITE_APP_ENV === 'production'`; returns null in production, renders amber-400 sticky banner with "STAGING -- Not Production" text in all other environments. Consumed by Plan 02 (Layout sidebar).

**twg-logo.png** — TWG Global logo asset (11,733 bytes PNG) copied from Intrepid-POC to frontend/src/assets/.

**LoginPage.jsx updates:**
- Replaced inline staging banner div with `<StagingBanner />`
- Replaced `<span>TWG GLOBAL</span>` placeholder with `<img src={twgLogo} alt="TWG Global" className="h-10 w-auto" />`
- Changed Sign in button from `bg-slate-900 text-white hover:bg-slate-700` to `bg-primary text-primary-foreground hover:bg-primary/90`
- Backend health indicator preserved unchanged

**LoginPage.test.jsx updates:**
- Added `vi.mock('@/components/StagingBanner', ...)` mock returning plain div
- Added `vi.mock('@/assets/twg-logo.png', ...)` mock for asset import
- Updated banner assertion from `getByText(/environment/i)` to `getByText(/staging/i)`
- All 4 tests pass

## Verification

All 5 overall checks pass:
1. `test -f frontend/src/assets/twg-logo.png` — PASS
2. `grep -q "VITE_APP_ENV" frontend/src/components/StagingBanner.jsx` — PASS
3. `grep -q "StagingBanner" frontend/src/pages/LoginPage.jsx` — PASS
4. `grep -q "bg-primary" frontend/src/pages/LoginPage.jsx` — PASS
5. `grep -q 'alt="TWG Global"' frontend/src/pages/LoginPage.jsx` — PASS

LoginPage tests: 4/4 pass in 312ms.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- frontend/src/assets/twg-logo.png — FOUND
- frontend/src/components/StagingBanner.jsx — FOUND
- frontend/src/pages/LoginPage.jsx — FOUND (modified)
- frontend/src/__tests__/LoginPage.test.jsx — FOUND (modified)
- Commit 70cff5c — FOUND (feat(08-01): add TWG logo asset and StagingBanner component)
- Commit 89bc0ab — FOUND (feat(08-01): update LoginPage with logo, StagingBanner, and navy button)
