---
phase: 17
slug: groups-roles-authorship-schema
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-06
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio + httpx AsyncClient |
| **Config file** | none — run via docker-compose |
| **Quick run command** | `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/ -x -q` |
| **Full suite command** | `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/ -v --cov=backend --cov-report=html --cov-fail-under=85` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/ -x -q`
- **After every plan wave:** Run full suite command above
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 17-W0-01 | 01 | 0 | GROUP-01, ADMIN-11 | stub | `pytest backend/tests/test_admin_groups.py -x` | ❌ W0 | ⬜ pending |
| 17-W0-02 | 01 | 0 | GROUP-02–06, ADMIN-10 | stub | `pytest backend/tests/test_admin_users.py -x` | ❌ W0 | ⬜ pending |
| 17-W0-03 | 01 | 0 | AUDIT-01, AUDIT-02 | stub | `pytest backend/tests/test_authorship.py -x` | ❌ W0 | ⬜ pending |
| 17-W0-04 | 01 | 0 | ROLE-MIGRATION | stub | `pytest backend/tests/test_role_migration.py -x` | ❌ W0 | ⬜ pending |
| 17-01-01 | migration | 1 | GROUP-01 | integration | `pytest backend/tests/test_admin_groups.py -x` | ❌ W0 | ⬜ pending |
| 17-01-02 | migration | 1 | GROUP-02–05 | integration | `pytest backend/tests/test_admin_users.py::test_group_assignment -x` | ❌ W0 | ⬜ pending |
| 17-01-03 | migration | 1 | AUDIT-01, AUDIT-02 | integration | `pytest backend/tests/test_authorship.py -x` | ❌ W0 | ⬜ pending |
| 17-02-01 | role callsites | 1 | GROUP-06 | integration | `pytest backend/tests/test_admin_users.py::test_user_list_includes_role -x` | ❌ W0 | ⬜ pending |
| 17-02-02 | role callsites | 1 | ROLE-MIGRATION | regression | `pytest backend/tests/test_role_migration.py -x` | ❌ W0 | ⬜ pending |
| 17-02-03 | role callsites | 1 | existing tests | regression | `pytest backend/tests/test_ref_data.py backend/tests/test_funds.py backend/tests/test_deals_pe.py -x` | ✅ Exists | ⬜ pending |
| 17-03-01 | admin API | 2 | ADMIN-10, ADMIN-11 | integration | `pytest backend/tests/test_admin_groups.py backend/tests/test_admin_users.py -x` | ❌ W0 | ⬜ pending |
| 17-04-01 | admin UI | 3 | ADMIN-10, ADMIN-11 | manual | UI smoke test (see Manual Verifications) | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_admin_groups.py` — stubs for GROUP-01, ADMIN-11
- [ ] `backend/tests/test_admin_users.py` — stubs for GROUP-02 through GROUP-06, ADMIN-10
- [ ] `backend/tests/test_authorship.py` — stubs for AUDIT-01, AUDIT-02
- [ ] `backend/tests/test_role_migration.py` — verifies old role strings are gone, new ones present

*Existing infrastructure (`pytest`, `conftest.py`, `docker-compose`) covers all framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin creates/renames/deactivates group in UI | GROUP-01 | React state update requires browser | Log in as admin → Group Management tab → create group, rename it, deactivate it; verify list updates immediately |
| Admin assigns user to group, role appears in user list | GROUP-02, GROUP-06 | Multi-step UI flow | Log in as admin → User Management → assign user to group and role; verify effective role shown in list |
| Moving user removes prior group membership | GROUP-03 | Requires checking DB via inspect | Assign user to group A, then reassign to group B; verify group A member count decrements |
| created_by/updated_by populated correctly | AUDIT-01, AUDIT-02 | Requires direct DB inspection after seed | Run seed script; inspect DB rows for Contact, Company, Deal, Fund, DealCounterparty, DealFunding |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
