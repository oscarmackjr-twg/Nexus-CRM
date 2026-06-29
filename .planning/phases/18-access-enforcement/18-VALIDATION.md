---
phase: 18
slug: access-enforcement
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-29
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `backend/tests/conftest.py` (session-scoped SQLite DB; `seeded_org` fixture) |
| **Quick run command** | `cd backend && python -m pytest tests/test_access_enforcement.py -x -q` |
| **Full suite command** | `cd backend && python -m pytest tests/ -q` |
| **Estimated runtime** | ~TBD seconds (confirm in Wave 0) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && python -m pytest tests/test_access_enforcement.py -x -q`
- **After every plan wave:** Run `cd backend && python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** TBD seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | ACCESS-02, ACCESS-05 | T-18-01, T-18-03 | `access.py` authz module exposes the role × action contract (visible_deal_team_ids, can_read/write/delete_deal, require_deal_readable/writable) | unit/import | `cd backend && python -c "from backend.auth import access; assert hasattr(access,'visible_deal_team_ids') and hasattr(access,'require_deal_readable') and hasattr(access,'can_write_deal') and hasattr(access,'is_oversight_role')"` | ✅ created by task | ⬜ pending |
| 18-01-02 | 01 | 1 | ACCESS-02, ACCESS-05 | T-18-01, T-18-02 | `_crm.py` helpers delegate to access.py; admin/principal get no team filter, regular/supervisor scoped to own team | unit/import | `cd backend && python -c "from backend.services._crm import accessible_team_ids, private_deal_predicate; from backend.auth import access; import inspect; assert 'visible_deal_team_ids' in inspect.getsource(accessible_team_ids); assert inspect.iscoroutinefunction(accessible_team_ids)"` | ✅ created by task | ⬜ pending |
| 18-01-03 | 01 | 1 | ACCESS-01, ACCESS-02, ACCESS-05 | T-18-01, T-18-02, T-18-03, T-18-04 | List scoping silently filters other-group deals (no 403); private-deal nuance for oversight roles; contacts/companies global-read | integration | `cd backend && python -m pytest tests/test_access_enforcement.py -x -q` | ❌ W0 (created this task) | ⬜ pending |
| 18-02-01 | 02 | 2 | ACCESS-07 | T-18-05 | get_deal / _get_deal_or_404 load-then-decide: in-org out-of-scope -> 403, absent -> 404, activities inherit | integration | `cd backend && python -m pytest tests/test_access_enforcement.py -x -q -k "403 or 404 or get"` | ❌ W0 | ⬜ pending |
| 18-02-02 | 02 | 2 | ACCESS-03, ACCESS-04 | T-18-06, T-18-07, T-18-08 | Write/delete guards: can_write_deal (no is_manager_plus), can_delete_deal owner-or-admin, owner_id reassign admin-only | integration | `cd backend && python -m pytest tests/test_access_enforcement.py -x -q -k "update or delete or move or supervisor or owner"` | ❌ W0 | ⬜ pending |
| 18-02-03 | 02 | 2 | ACCESS-06 | T-18-06, T-18-07 | Admin full CRUD cross-group never 403; CREATE forces team_id to creator team (D-12) | integration | `cd backend && python -m pytest tests/test_access_enforcement.py -x -q` | ❌ W0 | ⬜ pending |
| 18-03-01 | 03 | 3 | ACCESS-02, ACCESS-07 | T-18-10, T-18-11, T-18-13 | counterparties.py + funding.py gate every method on parent-deal access; writes use require_deal_writable (IDOR closed) | unit/import | `cd backend && python -c "import inspect, backend.services.counterparties as c, backend.services.funding as f; assert 'require_deal_writable' in inspect.getsource(c) and 'require_deal_readable' in inspect.getsource(c); assert 'require_deal_writable' in inspect.getsource(f) and 'require_deal_readable' in inspect.getsource(f)"` | ✅ created by task | ⬜ pending |
| 18-03-02 | 03 | 3 | ACCESS-02, ACCESS-07 | T-18-10, T-18-11, T-18-12 | Cross-team child GET/POST -> 403 (counterparties + funding); owner/admin -> 200; DealDetailPage distinguishes 403 from 404 | integration + grep | `cd backend && python -m pytest tests/test_access_enforcement.py -x -q && grep -q "status === 403" ../frontend/src/pages/DealDetailPage.jsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Note: Plan 03 Task 3 (`checkpoint:human-verify`) is a manual frontend 403/404 verification — see Manual-Only Verifications below; it has no automated row.*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_access_enforcement.py` — created by Plan 01 Task 3; covers ACCESS-01..ACCESS-07 role × action matrix (extended by Plans 02 and 03)
- [ ] `backend/tests/conftest.py` — add a `principal` user to the `seeded_org` fixture (gap found in research — required for ACCESS-05 coverage)
- [ ] `deal_fixtures` fixture in `test_access_enforcement.py` — alpha-team deal, beta-team deal, and an alpha-team `is_private` deal for the cross-matrix

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Frontend distinguishes 403 ("no access") from 404 ("not found") in deal detail error UI | ACCESS-07 | Visual/UX behavior in `DealDetailPage.jsx` (Plan 03 Task 3 checkpoint) | Load a deal id outside the user's scope; confirm "You don't have permission to view this deal." message, not "may have been removed". Load a nonexistent uuid; confirm the "may have been removed" 404 message |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < TBDs
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
