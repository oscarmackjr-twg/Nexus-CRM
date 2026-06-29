---
phase: 18-access-enforcement
plan: "02"
subsystem: backend-deals
tags: [authz, access-control, deal-service, 403-vs-404, tdd, write-guard, delete-guard]
dependency_graph:
  requires: [18-01 (backend/auth/access.py)]
  provides: [deal CRUD access enforcement, 403/404 split on all deal actions]
  affects: [backend/services/deals.py, backend/tests/test_access_enforcement.py]
tech_stack:
  added: []
  patterns: [load-then-decide, can_write_deal, can_delete_deal, require_deal_readable]
key_files:
  created: []
  modified:
    - backend/services/deals.py
    - backend/tests/test_access_enforcement.py
decisions:
  - "require_deal_readable replaces _get_deal_or_404 body entirely — single source for 403/404 split on all deal-scoped actions"
  - "get_deal uses two-step load-then-decide: require_deal_readable for gate, then _base_deal_stmt join for full response"
  - "update_deal and move_stage drop is_manager_plus entirely — can_write_deal enforces team-scoped supervisor writes"
  - "delete_deal uses can_delete_deal (owner-or-admin) with require_deal_readable for correct 404/403 split"
  - "owner_id guard in update_deal changed from is_manager_plus to is_admin (D-13: admin-only reassignment)"
  - "_get_pipeline_and_stage fixed: visible_team_ids=None means all-visible (admin/principal), not no-visibility"
metrics:
  duration: "15min"
  completed: "2026-06-29"
  tasks: 3
  files: 2
---

# Phase 18 Plan 02: Deal Service Access Enforcement Summary

Threaded `require_deal_readable`, `can_write_deal`, and `can_delete_deal` guards from `backend/auth/access.py` through every `DealService` CRUD method. The 403-vs-404 split now works correctly for `get_deal`, `_get_deal_or_404`, `update_deal`, `move_stage`, `delete_deal`, and deal activities. Supervisor cross-team edit bug (Bugs 4 and 6) closed. Owner-id reassignment gated to admin-only (Bug 5). Full 28-test matrix green including admin full-CRUD and CREATE team_id forcing.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Failing 403/404 split tests for get_deal + activities | 4d8405b | backend/tests/test_access_enforcement.py |
| 1 (GREEN) | load-then-decide get_deal + _get_deal_or_404 via require_deal_readable | 9cc06be | backend/services/deals.py |
| 2 (RED) | Failing write/delete guard tests | 92dbf41 | backend/tests/test_access_enforcement.py |
| 2 (GREEN) | can_write_deal/can_delete_deal guards in update_deal, move_stage, delete_deal | 918c8c5 | backend/services/deals.py |
| 3 | Admin full-CRUD + CREATE team_id matrix tests + Rule 1 pipeline fix | 792364b | backend/tests/test_access_enforcement.py, backend/services/deals.py |

## Verification

- `pytest backend/tests/test_access_enforcement.py -x -q` — 28 passed
- `pytest backend/tests/ -q` (excluding test_access_enforcement.py) — 32 passed, 4 xpassed, 1 pre-existing failure in test_ref_data.py (unrelated fund_status category count)
- Grep confirms `update_deal`/`move_stage` guards reference `can_write_deal`, not `is_manager_plus`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _get_pipeline_and_stage for principal create**
- **Found during:** Task 3 — `test_create_deal_principal_forces_own_team_id` returned 403
- **Issue:** `_get_pipeline_and_stage` checked `visible_team_ids is None or pipeline.team_id not in visible_team_ids` to gate pipeline access. Before Plan 18-01, `visible_team_ids` was never `None`. After Plan 18-01 changed `accessible_team_ids` semantics (None = all-visible for admin/principal), this check treated `None` as "no teams" and raised 403 for principals. The old `is_admin` bypass only covered admins.
- **Fix:** Changed condition to `visible_team_ids is not None and pipeline.team_id not in visible_team_ids`. `None` now correctly means "all teams visible — no restriction". Removed the separate `is_admin` guard (covered by `None`).
- **Files modified:** backend/services/deals.py (lines ~253-258)
- **Commit:** 792364b

## Decisions Made

1. `require_deal_readable` replaces `_get_deal_or_404` body entirely — one delegation line. This means `get_deal_activities` and `log_activity` inherit the correct 403/404 split automatically (Bug 9 closed).

2. `get_deal` uses a two-step approach: first `require_deal_readable` (existence + authz gate), then the full `_base_deal_stmt` join for the response body. The second query does not raise 404 — existence is already confirmed.

3. `is_manager_plus` is intentionally retained in `create_deal`'s pipeline team check (line 327). This check gates pipeline access during creation, not deal ownership. Its behavior is acceptable there and falls outside the plan's scope.

4. `_get_pipeline_and_stage` fix — `visible_team_ids is None` means all-visible: Principal now creates deals on their own team's pipeline without 403. Admin behavior unchanged (was already bypassed by old `is_admin` guard).

## Threat Surface Scan

All mitigations from the plan's threat register are in place:

| Threat ID | Mitigation Applied |
|-----------|-------------------|
| T-18-05 | `get_deal` + `_get_deal_or_404` use load-then-decide → 403 for in-org out-of-scope, 404 for absent |
| T-18-06 | `update_deal`/`move_stage` use `can_write_deal` (team check for supervisors) → supervisor cross-team edit closed |
| T-18-07 | `delete_deal` uses `can_delete_deal` (owner-or-admin only) → supervisor delete of others' deals → 403 |
| T-18-08 | `update_deal` owner_id guard uses `is_admin` → supervisor owner_id reassignment → 403 |
| T-18-09 | DealUpdate schema has no `team_id` field → structurally impossible to reassign team via payload |

No new network endpoints or trust boundaries introduced.

## Self-Check: PASSED

- [x] backend/services/deals.py — modified (verified: `can_write_deal`, `can_delete_deal`, `require_deal_readable` in CRUD guards)
- [x] backend/tests/test_access_enforcement.py — 28 tests, all green
- [x] Commits 4d8405b, 9cc06be, 92dbf41, 918c8c5, 792364b — all exist in git log
- [x] `pytest backend/tests/test_access_enforcement.py -x -q` exits 0 (28 passed)
