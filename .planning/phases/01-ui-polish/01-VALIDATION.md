---
phase: 1
slug: ui-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (frontend) |
| **Config file** | `frontend/vite.config.js` |
| **Quick run command** | `cd frontend && npm test -- --run` |
| **Full suite command** | `cd frontend && npm test -- --run --reporter=verbose` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm test -- --run`
- **After every plan wave:** Run `cd frontend && npm test -- --run --reporter=verbose`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01-01 | 1 | UI-01 | manual | visual browser check | ✅ | ⬜ pending |
| 1-01-02 | 01-01 | 1 | UI-01 | unit | `cd frontend && npm test -- --run` | ✅ | ⬜ pending |
| 1-02-01 | 01-02 | 1 | UI-02 | manual | visual browser check | ✅ | ⬜ pending |
| 1-03-01 | 01-03 | 1 | UI-03 | unit | `cd frontend && npm test -- --run` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Confirm `vitest` is installed and test runner resolves — run `cd frontend && npm test -- --run` once before executing tasks

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Login page visual layout (logo, staging banner, backend status indicator) | UI-01 | DOM rendering / visual; not unit-testable | Open http://localhost:5173 in browser, verify staging banner visible, TWG GLOBAL text present, Connected/Unavailable indicator shows |
| Dark mode lock — no light mode visible on any screen | UI-01, UI-02 | Visual; theme class on `<html>` | Inspect `document.documentElement.classList` includes `dark`; navigate all screens |
| Spacing/typography consistency across Contact/Company/Deal/Dashboard | UI-02 | Visual pixel-level check | Side-by-side comparison of heading sizes, card padding, and input spacing across all list + detail views |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
