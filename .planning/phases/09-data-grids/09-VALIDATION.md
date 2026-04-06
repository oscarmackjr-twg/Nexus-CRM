---
phase: 9
slug: data-grids
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-06
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest (configured in `frontend/vite.config.js`) |
| **Config file** | `frontend/vite.config.js` (inline `test:` block) |
| **Quick run command** | `cd frontend && npm test` |
| **Full suite command** | `cd frontend && npm test` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm test`
- **After every plan wave:** Run `cd frontend && npm test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | GRID-04, GRID-06 | unit | `cd frontend && npm test -- DataGrid` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | GRID-06 | unit | `cd frontend && npm test -- Pagination` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | GRID-01, GRID-04, GRID-05 | smoke | `cd frontend && npm test -- ContactsPage` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | GRID-02, GRID-04, GRID-05 | smoke | `cd frontend && npm test -- CompaniesPage` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 3 | GRID-03, GRID-04, GRID-05 | smoke | `cd frontend && npm test -- DealsPage` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/__tests__/DataGrid.test.jsx` — unit tests for GRID-04 (header classes), GRID-06 (pagination rendering)
- [ ] `frontend/src/__tests__/Pagination.test.jsx` — unit tests for GRID-06 (prev/next disabled states, per-page selector)
- [ ] `frontend/src/__tests__/ContactsPage.test.jsx` — smoke render for GRID-01 (compact rows)
- [ ] `frontend/src/__tests__/CompaniesPage.test.jsx` — smoke render for GRID-02 (compact rows)
- [ ] `frontend/src/__tests__/DealsPage.test.jsx` — smoke render for GRID-03 (compact rows), status filter tabs

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Row hover shows "View" button | GRID-05 | CSS `group-hover:` is Tailwind — jsdom does not compute pseudo-class CSS | Open each list page in browser, hover a row, confirm "View" button appears; unhover, confirm it disappears |
| Row hover highlights `bg-gray-50` | GRID-05 | Same — CSS hover not testable in jsdom | Open each list page in browser, hover a row, confirm background changes to light gray |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
