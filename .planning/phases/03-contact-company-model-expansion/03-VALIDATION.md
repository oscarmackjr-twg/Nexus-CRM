---
phase: 3
slug: contact-company-model-expansion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) + vitest (frontend) |
| **Config file** | `backend/tests/pytest.ini` / `frontend/vite.config.js` |
| **Quick run command** | `cd backend && python -m pytest tests/test_crm_core.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x -q && cd ../frontend && npm test -- --run` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_crm_core.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -x -q && cd ../frontend && npm test -- --run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | CONTACT-01,02,03,04,05 | migration | `cd backend && alembic upgrade head` | ✅ | ⬜ pending |
| 3-01-02 | 01 | 1 | CONTACT-06 | migration | `cd backend && alembic upgrade head` | ✅ | ⬜ pending |
| 3-02-01 | 02 | 2 | CONTACT-01..10 | integration | `cd backend && python -m pytest tests/test_crm_core.py -k contact -x -q` | ✅ | ⬜ pending |
| 3-02-02 | 02 | 2 | CONTACT-07,08,09 | integration | `cd backend && python -m pytest tests/test_crm_core.py -k activity -x -q` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 1 | COMPANY-01..09 | migration | `cd backend && alembic upgrade head` | ✅ | ⬜ pending |
| 3-04-01 | 04 | 2 | COMPANY-01..12 | integration | `cd backend && python -m pytest tests/test_crm_core.py -k company -x -q` | ✅ | ⬜ pending |
| 3-05-01 | 05 | 3 | CONTACT-01..10 | frontend | `cd frontend && npm test -- --run` | ✅ | ⬜ pending |
| 3-05-02 | 05 | 3 | COMPANY-01..12 | frontend | `cd frontend && npm test -- --run` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_crm_core.py` — add stubs for contact activity log tests (D-08/D-10, CONTACT-07/08/09)

*All other phase behaviors covered by existing test infrastructure.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Profile tab visible first before Activities/Tasks | CONTACT-03, COMPANY-01 (D-01) | DOM tab ordering | Open ContactDetailPage and CompanyDetailPage — Profile tab must be first in tab bar |
| Chips + RefSelect add pattern for multi-selects | CONTACT-05, COMPANY-06 (D-04) | Visual interaction | Add a sector preference chip, verify it appears as removable badge; add another via RefSelect |
| Previous employment row add/remove | CONTACT-05 (D-06) | Interactive DOM state | Click "+ Add", fill row, click ×, verify row removed |
| Coverage persons 403 fix | CONTACT-06 (D-05) | Auth role check | Log in as non-admin, verify coverage persons dropdown loads without 403 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
