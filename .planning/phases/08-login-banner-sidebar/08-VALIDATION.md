---
phase: 08
slug: login-banner-sidebar
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest |
| **Config file** | `frontend/vite.config.js` (vitest config inline) |
| **Quick run command** | `cd frontend && npm test -- --run src/__tests__/LoginPage.test.jsx` |
| **Full suite command** | `cd frontend && npm test -- --run` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm test -- --run`
- **After every plan wave:** Run `cd frontend && npm test -- --run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 8-01-01 | 01 | 1 | NAV-01, NAV-02, NAV-03, NAV-04, NAV-05 | grep + unit | `grep -q "bg-white border-r" frontend/src/components/Layout.jsx && grep -q "StagingBanner" frontend/src/components/Layout.jsx && cd frontend && npm test -- --run 2>&1 \| tail -5` | ❌ W0 | ⬜ pending |
| 8-01-02 | 01 | 1 | BANNER-01 | unit | `test -f frontend/src/components/StagingBanner.jsx && grep -q "bg-amber-400" frontend/src/components/StagingBanner.jsx && grep -q "VITE_APP_ENV" frontend/src/components/StagingBanner.jsx` | ✅ | ⬜ pending |
| 8-01-03 | 01 | 1 | LOGIN-01, LOGIN-02, LOGIN-03, LOGIN-04 | unit | `grep -q "twg-logo" frontend/src/pages/LoginPage.jsx && grep -q "StagingBanner" frontend/src/pages/LoginPage.jsx && grep -q "bg-primary" frontend/src/pages/LoginPage.jsx && cd frontend && npm test -- --run src/__tests__/LoginPage.test.jsx 2>&1 \| tail -5` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/__tests__/LoginPage.test.jsx` — UPDATE existing test: line 59 asserts `/environment/i` against old inline banner text "DEVELOPMENT ENVIRONMENT". After swap to `StagingBanner` component (renders "STAGING -- Not Production"), assertion must change to `/staging/i` or `/not production/i`
- [ ] `frontend/src/__tests__/Layout.test.jsx` — NEW stub: verify sidebar renders `bg-white`, StagingBanner is present, at least one `border-l-4` nav item exists

*Wave 0 note: LoginPage test update is MANDATORY before Task 3 executes — the test currently passes but will fail after the StagingBanner swap. Layout test is a new file.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| TWG logo renders visually in sidebar | NAV-02 | Image rendering requires browser | Run `make dev`, navigate to any authenticated page, verify logo image appears at sidebar top |
| TWG logo renders on login page | LOGIN-01 | Image rendering requires browser | Run `make dev`, navigate to `/login`, verify logo image is centered above form |
| Staging banner displays amber-400 | BANNER-01 | Color rendering requires browser | Run `make dev` with `VITE_APP_ENV` unset or non-production, confirm amber banner at page top |
| Active nav item shows navy left bar | NAV-03 | Visual border color requires browser | Click each nav item, confirm navy `border-l-4` appears on active item |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
