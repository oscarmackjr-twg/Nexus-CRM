---
phase: 18-access-enforcement
plan: "01"
subsystem: backend-auth
tags: [authz, access-control, four-role-model, deal-scoping, tdd]
dependency_graph:
  requires: [17-groups-roles-authorship-schema]
  provides: [access.py authz contract, fixed list scoping, principal fixture]
  affects: [backend/services/deals.py, backend/services/counterparties.py, backend/services/funding.py]
tech_stack:
  added: []
  patterns: [centralized-authz-module, load-then-decide, delegation-wrappers, sql-predicate-composition]
key_files:
  created:
    - backend/auth/access.py
    - backend/tests/test_access_enforcement.py
  modified:
    - backend/services/_crm.py
    - backend/tests/conftest.py
decisions:
  - "visible_deal_team_ids returns None (not empty list) for admin/principal — None means no team WHERE clause in _base_deal_stmt"
  - "private_deal_predicate returns Python True (not SQLAlchemy true()) for oversight roles — SQLAlchemy accepts bare True as no-op WHERE clause"
  - "accessible_team_ids kept async with session param for zero call-site disruption (Pitfall 6 per RESEARCH.md)"
  - "clean_db fixture now calls engine.dispose() after yield to reset asyncpg connection pool between tests (fixes pre-existing STRICT mode cross-loop reuse bug)"
metrics:
  duration: "19min"
  completed: "2026-06-29"
  tasks: 3
  files: 4
---

# Phase 18 Plan 01: Authz Module + List Scoping Summary

Centralized authorization module with JWT role predicates, SQL scoping helpers, and deal visibility/write/delete guards. Rewrote two broken `_crm.py` helpers so admin and principal now see cross-group deals in list results. Full list/visibility/global-read test matrix proven green, including the previously-untested `principal` role.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create backend/auth/access.py authz module | 821ad21 | backend/auth/access.py |
| 2 | Rewrite _crm.py to delegate to access.py | 0b75ac7 | backend/services/_crm.py |
| 3 (RED) | Add failing tests for list/visibility matrix | f518985 | backend/tests/test_access_enforcement.py |
| 3 (GREEN) | Add principal fixture + fix pool isolation | 1849253 | backend/tests/conftest.py |

## Verification

- `pytest backend/tests/test_access_enforcement.py -x -q` — 7 passed
- `pytest backend/tests/test_authorship.py -q` — 6 passed (no regression; pre-existing 3/6 error also fixed)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Infrastructure] Fixed asyncpg connection pool cross-loop reuse in tests**
- **Found during:** Task 3 (GREEN phase — tests failed intermittently in sequence)
- **Issue:** pytest-asyncio STRICT mode creates a per-function event loop for each test. The global SQLAlchemy engine's asyncpg connections get bound to the first test's event loop. Subsequent tests' event loops cannot reuse those connections, causing `RuntimeError: Event loop is closed` during pool cleanup. This pre-existing bug affected test_authorship.py (3/6 were erroring before this fix).
- **Fix:** Added `await get_engine().dispose()` teardown to `clean_db` fixture. This closes idle asyncpg connections after each test so the next test's event loop creates fresh connections. No production code changed.
- **Files modified:** backend/tests/conftest.py
- **Commit:** 1849253

## Decisions Made

1. `visible_deal_team_ids` returns `None` (not empty list) for admin/principal — `None` signals the existing `_base_deal_stmt` branch to skip the `Deal.team_id.in_(...)` WHERE clause entirely, enabling cross-group visibility.

2. `private_deal_predicate` returns Python `True` (a literal, not `sqlalchemy.true()`) for oversight roles. SQLAlchemy composes `True` as a no-op in the WHERE clause, keeping `_base_deal_stmt` structurally consistent.

3. `accessible_team_ids` kept as `async def` with both `session` and `user` params for zero call-site disruption — matching Pitfall 6 guidance from RESEARCH.md. The function no longer uses `session` but keeping it avoids touching the call in `DealService._visible_team_ids()`.

4. `can_read_deal` uses direct `==` comparison for `deal.team_id != user.team_id`. SQLAlchemy 2.0 with `Uuid()` type returns Python `UUID` objects, so direct comparison works (no str() wrapping needed per Pitfall 3 in RESEARCH.md).

## Access Contract Created (for Plans 02 and 03)

Plans 02 and 03 import these verbatim from `backend.auth.access`:

```python
from backend.auth.access import (
    is_admin, is_principal, is_supervisor, is_oversight_role,
    visible_deal_team_ids, private_deal_predicate,
    can_read_deal, can_write_deal, can_delete_deal,
    require_deal_readable, require_deal_writable,
)
```

## Threat Surface Scan

No new network endpoints introduced. All changes are pure Python (authz helpers + test fixtures). Threats addressed:

| Threat | Mitigation |
|--------|------------|
| T-18-01: admin/principal seeing only own team (broken) | `visible_deal_team_ids` returns `None` for these roles → no team WHERE clause |
| T-18-02: regular_user sees teammate's private deal in list | `private_deal_predicate` returns `or_(is_private==False, owner==user)` for `regular_user` |
| T-18-03: unassigned user sees all deals | `visible_deal_team_ids` returns `[]` → `_base_deal_stmt` applies `WHERE False` |

## Self-Check: PASSED

- [x] backend/auth/access.py — EXISTS
- [x] backend/services/_crm.py — modified with delegation
- [x] backend/tests/test_access_enforcement.py — EXISTS, 7 tests green
- [x] backend/tests/conftest.py — principal user added
- [x] Commits 821ad21, 0b75ac7, f518985, 1849253 — all exist in git log
