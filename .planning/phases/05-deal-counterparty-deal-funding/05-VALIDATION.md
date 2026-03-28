---
phase: 5
slug: deal-counterparty-deal-funding
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend), vitest (frontend) |
| **Config file** | `backend/tests/pytest.ini`, `frontend/vite.config.js` |
| **Quick run command** | `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/test_crm_core.py -v -x 2>&1 \| tail -20` |
| **Full suite command** | `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/ -v 2>&1 \| tail -30` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 05-01-01 | 01 | 1 | CPARTY-01,02,03,04 | migration | `docker-compose -f deploy/docker-compose.yml run --rm backend alembic upgrade head 2>&1 \| tail -5` | ⬜ pending |
| 05-02-01 | 02 | 2 | CPARTY-05,06,07,08 | unit | `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/test_crm_core.py -k counterparty -v` | ⬜ pending |
| 05-03-01 | 03 | 3 | FUNDING-01,02,03,04,05,06,07 | unit | `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/test_crm_core.py -k funding -v` | ⬜ pending |
| 05-04-01 | 04 | 4 | CPARTY-09,10,11,12,FUNDING-08,09 | build | `cd frontend && npx vite build 2>&1 \| tail -5` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_crm_core.py` — add stubs for counterparty and funding CRUD (CPARTY-05 through CPARTY-12, FUNDING-04 through FUNDING-09)

*Frontend: vitest tests are in `frontend/src/__tests__/`. Existing DealDetailPage test should be extended for new tabs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stage date click → date picker opens in grid | CPARTY-11 | Browser interaction | Open deal, Counterparties tab, click any date cell, confirm date picker appears |
| Company column remains sticky on scroll | CPARTY-09 | Visual/scroll | Open deal with 5+ counterparties, scroll grid right, confirm Company column stays visible |
| Add counterparty modal auto-closes on success | CPARTY-10 | UI interaction | Add counterparty, confirm modal closes and row appears in grid |
| Deactivated tier label shows "---" | CPARTY-05 | Requires DB manipulation | Deactivate a tier ref_data item, reload counterparties tab, confirm label shows "---" |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
