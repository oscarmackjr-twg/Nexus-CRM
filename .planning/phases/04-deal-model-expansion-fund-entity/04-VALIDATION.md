---
phase: 4
slug: deal-model-expansion-fund-entity
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `backend/tests/pytest.ini` |
| **Quick run command** | `cd backend && python -m pytest tests/test_crm_core.py tests/test_health.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_crm_core.py tests/test_health.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | FUND-01 | migration | `cd backend && python -m pytest tests/test_crm_core.py -k fund -x -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | FUND-02 | api | `cd backend && python -m pytest tests/test_crm_core.py -k fund -x -q` | ❌ W0 | ⬜ pending |
| 4-01-03 | 01 | 1 | FUND-03 | api | `cd backend && python -m pytest tests/test_crm_core.py -k fund -x -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 1 | DEAL-01 | migration | `cd backend && python -m pytest tests/test_crm_core.py -k deal_pe -x -q` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 1 | DEAL-07 | migration | `cd backend && python -m pytest tests/test_crm_core.py -k deal_team -x -q` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 2 | DEAL-02 | api | `cd backend && python -m pytest tests/test_crm_core.py -k deal -x -q` | ❌ W0 | ⬜ pending |
| 4-03-02 | 03 | 2 | DEAL-04 | api | `cd backend && python -m pytest tests/test_crm_core.py -k deal -x -q` | ❌ W0 | ⬜ pending |
| 4-03-03 | 03 | 2 | DEAL-10 | api | `cd backend && python -m pytest tests/test_crm_core.py -k deal -x -q` | ❌ W0 | ⬜ pending |
| 4-04-01 | 04 | 3 | DEAL-11 | manual | N/A — frontend visual | N/A | ⬜ pending |
| 4-04-02 | 04 | 3 | DEAL-12 | manual | N/A — frontend visual | N/A | ⬜ pending |
| 4-04-03 | 04 | 3 | FUND-05 | manual | N/A — frontend visual | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_crm_core.py` — add stubs for fund CRUD (FUND-01, FUND-02, FUND-03), deal PE fields (DEAL-01, DEAL-02), deal team M2M (DEAL-07), financial validators (DEAL-04), date milestones (DEAL-10)
- [ ] `backend/tests/conftest.py` — verify `seed_ref_data` fixture includes `fund_status` category entries

*If no new framework: "Existing pytest infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Deal detail 4-tab layout renders correctly | DEAL-11 | Frontend visual layout | Open DealDetailPage, confirm 4 tabs: Deal Identity, Financials, Process Milestones, Source & Team / Passed & Dead |
| Fund selector dropdown in deal edit | FUND-05 | Frontend interaction | Open deal edit form, confirm fund selector dropdown appears and lists funds |
| Date picker inputs for milestones | DEAL-12 | Frontend input type | Open deal edit, confirm all 8 date milestone fields use date picker inputs |
| RefSelect dropdowns resolve labels | DEAL-09 | Frontend display | View deal detail, confirm transaction_type, source_type show labels not UUIDs |
| Deal team multi-user selector | DEAL-07 | Frontend interaction | Open deal edit, add 2 users to deal team, save, confirm both names appear |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
