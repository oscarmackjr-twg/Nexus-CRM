---
phase: 7
slug: brand-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 2.1.8 |
| **Config file** | `frontend/vite.config.js` (`test` block, `environment: 'jsdom'`, `css: true`) |
| **Quick run command** | `cd frontend && npm test -- --run` |
| **Full suite command** | `cd frontend && npm test` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Visual inspection — open browser at `http://localhost:5173`, verify primary button background is navy (`rgb(26, 56, 104)`) and font-family includes Montserrat
- **After every plan wave:** Run `cd frontend && npm test -- --run` (existing suite must stay green)
- **Before `/gsd:verify-work`:** Full suite must be green + visual confirmation of all 3 success criteria

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 7-01-01 | 01 | 1 | BRAND-01, BRAND-03 | unit/smoke | `cd frontend && npm test -- --run src/__tests__/brand.test.jsx` | ❌ W0 | ⬜ pending |
| 7-01-02 | 01 | 1 | BRAND-02 | unit/smoke | included in brand.test.jsx | ❌ W0 | ⬜ pending |
| 7-01-03 | 01 | 1 | BRAND-01 | manual | Inspect button computed color in browser DevTools = `rgb(26, 56, 104)` | N/A | ⬜ pending |
| 7-01-04 | 01 | 1 | BRAND-01 | manual | `grep -r "indigo\|purple\|violet" frontend/src/` returns zero matches | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/__tests__/brand.test.jsx` — CSS variable smoke tests for BRAND-01, BRAND-02, BRAND-03

*Optional: visual verification is the canonical acceptance method for this pure-CSS phase. Wave 0 test is a nice-to-have, not a hard gate.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Primary buttons render navy | BRAND-01 | jsdom CSS custom property resolution via `getComputedStyle` can be inconsistent | Open `http://localhost:5173`, inspect any primary button, verify `background-color: rgb(26, 56, 104)` in DevTools |
| Body text renders in Montserrat | BRAND-02 | Visual font rendering is browser-only | Open any page, inspect `<body>`, verify font-family shows Montserrat in DevTools computed styles |
| surface-grid uses navy tint | BRAND-01 | Background gradient rgba is not a CSS var — not caught by automated var checks | Navigate to dashboard, inspect `.surface-grid` element, verify `rgba(26, 56, 104, 0.06)` not `rgba(99, 102, 241, 0.06)` |
| indigo/purple sweep clean | BRAND-01 | Confirms no regressions in JSX files | Run `grep -r "indigo\|purple\|violet" frontend/src/` — must return zero matches |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
