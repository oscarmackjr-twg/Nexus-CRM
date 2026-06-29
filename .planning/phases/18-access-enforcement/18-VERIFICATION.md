---
phase: 18-access-enforcement
verified: 2026-06-29T00:00:00Z
status: human_needed
score: 6/6 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Navigate to a deal owned by a different group as a Regular User in the running app"
    expected: "The deal detail page renders 'You don't have permission to view this deal.' — NOT 'Could not load deal. It may have been removed.'"
    why_human: "The 3-line JSX change (lines 946-953 of DealDetailPage.jsx) is confirmed present in source, but the Axios/React Query error shape (error.response?.status) can only be proven to resolve to the integer 403 — rather than undefined — in an actual browser session with a live backend."
  - test: "Navigate to a non-existent deal UUID in the running app"
    expected: "The deal detail page renders 'Could not load deal. It may have been removed.' — the 404 message, not the 403 message."
    why_human: "Same JSX branch — need to confirm the else-path also renders correctly in browser."
---

# Phase 18: Access Enforcement Verification Report

**Phase Goal:** Every API endpoint enforces group-scoped visibility and role-based write permissions — out-of-scope record requests return 403, not 404.
**Verified:** 2026-06-29
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Regular User can read all Contacts and Companies regardless of group; Deals visible only to same-group members, Supervisor, Principals, and Admins | VERIFIED | `visible_deal_team_ids` returns `[user.team_id]` for regular_user; `can_read_deal` blocks cross-team access; `test_contacts_globally_readable` confirms 200 on contacts/companies for all roles; `test_beta_rep_sees_only_beta_deals` confirms list scoping |
| 2 | Regular User can CRUD own Deals; editing/deleting another group's Deal returns 403 | VERIFIED | `update_deal` and `delete_deal` both call `require_deal_readable` (403 on cross-group) then `can_write_deal`/`can_delete_deal` (403 on non-owner); proven by `test_regular_user_update_own_deal_returns_200`, `test_regular_user_update_team_member_deal_returns_403`, `test_owner_delete_own_deal_returns_204` |
| 3 | Supervisor can read and edit same-group Deals; receives 403 when deleting another member's Deal | VERIFIED | `can_write_deal` returns True for supervisor when `deal.team_id == user.team_id`; `can_delete_deal` is owner-or-admin only; proven by `test_supervisor_update_same_team_deal_returns_200`, `test_supervisor_delete_team_member_deal_returns_403`, `test_supervisor_update_cross_team_deal_returns_403` |
| 4 | Principal reads Deals across all groups; Regular User from different group receives 403 for same request | VERIFIED | `visible_deal_team_ids` returns `None` for principal (all teams visible); `can_read_deal` short-circuits True for principal; `test_principal_sees_all_teams_in_list` and `test_cross_team_deal_get_returns_403` confirm both sides |
| 5 | Admin performs full CRUD on any Deal across any group with no 403 | VERIFIED | `can_write_deal` and `can_delete_deal` both short-circuit True for admin; `test_admin_update_both_team_deals_returns_200`, `test_admin_move_stage_both_team_deals_returns_200`, `test_admin_delete_cross_team_deal_returns_204`, `test_admin_owner_id_change_returns_200` all pass |
| 6 | Authenticated request for out-of-scope record returns 403 (not 404) — backend enforcement | VERIFIED | `require_deal_readable` loads by `org_id` only (no team filter) then checks `can_read_deal`; raises 403 if forbidden, 404 only if absent; applies to deal detail, activities, counterparties, funding; proven by `test_cross_team_deal_get_returns_403`, `test_nonexistent_deal_get_returns_404`, `test_activities_cross_team_returns_403`, and 4 child-entity 403 tests |
| 6-FE | Deal detail page shows distinct 403 vs 404 message in browser | HUMAN NEEDED | Code confirmed at DealDetailPage.jsx lines 946-953 (`status === 403` branch present, correct messages present); browser rendering requires human confirmation |

**Score:** 6/6 truths verified (backend); 1 human verification item for frontend UX

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/auth/access.py` | Single authz source of truth — role predicates, scoping helpers, action guards, async DB guards | VERIFIED | 121 lines; all 8 required functions present (`is_admin`, `is_principal`, `is_supervisor`, `is_oversight_role`, `visible_deal_team_ids`, `private_deal_predicate`, `can_read_deal`, `can_write_deal`, `can_delete_deal`, `require_deal_readable`, `require_deal_writable`); imports cleanly; no Call/Note code |
| `backend/services/_crm.py` | `accessible_team_ids` and `private_deal_predicate` delegate to access.py | VERIFIED | Line 41: `from backend.auth.access import visible_deal_team_ids` inside `accessible_team_ids`; line 152: delegation to `_authz_predicate`; function stays async with `(session, user)` params; all other helpers (`is_admin`, `is_manager_plus`, `ensure_owner_or_admin`, etc.) unchanged |
| `backend/services/deals.py` | Action guards threaded through get/update/move_stage/delete and `_get_deal_or_404` | VERIFIED | `can_write_deal`, `can_delete_deal`, `is_admin`, `require_deal_readable` imported at top; `_get_deal_or_404` is a single delegation call (line 235); `get_deal` uses two-step load-then-decide (line 311); `update_deal`, `move_stage`, `delete_deal` all use `require_deal_readable` + respective guard |
| `backend/services/counterparties.py` | Parent-deal scope guard on list/create/update/delete | VERIFIED | `require_deal_readable` on `list_for_deal` (line 88); `require_deal_writable` on `create` (109), `update` (133), `delete` (156); old `_get_deal_or_404` removed |
| `backend/services/funding.py` | Parent-deal scope guard on list/create/update/delete | VERIFIED | `require_deal_readable` on `list_for_deal` (line 75); `require_deal_writable` on `create` (101), `update` (123), `delete` (145); old `_get_deal_or_404` removed; no raw `404` literals in deal-existence path |
| `backend/tests/test_access_enforcement.py` | 36-test matrix covering full role x action grid | VERIFIED | 36 `async def test_` functions confirmed; covers list scoping, global read, 403/404 split, write/delete matrix, admin full-CRUD, CREATE team_id forcing, child-entity IDOR |
| `backend/tests/conftest.py` | `seeded_org` fixture includes `principal` role user | VERIFIED | Line 185: `("principal@example.com", "principal", "principal", alpha)` in user loop; `seeded_org["principal"]` resolves to user with role `"principal"` on alpha team |
| `frontend/src/pages/DealDetailPage.jsx` | 403-vs-404 distinct error message in `isError` branch | VERIFIED (code) | Lines 946-953: `const status = dealQuery.error?.response?.status;`; `status === 403` → permission message; else → removed message. Browser rendering: HUMAN NEEDED |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `_crm.py::accessible_team_ids` | `access.py::visible_deal_team_ids` | import + delegation | WIRED | Lines 41-42 of `_crm.py` |
| `_crm.py::private_deal_predicate` | `access.py::private_deal_predicate` | import + delegation | WIRED | Lines 152-153 of `_crm.py` |
| `deals.py::_base_deal_stmt` | `_crm.py::private_deal_predicate` | WHERE clause composition | WIRED | Line 113 of `deals.py` calls `private_deal_predicate(self.current_user, visible_team_ids)` |
| `deals.py::get_deal` | `access.py::require_deal_readable` | load-then-decide gate | WIRED | Line 311 of `deals.py` |
| `deals.py::update_deal` | `access.py::can_write_deal` | write guard | WIRED | Lines 375-377 of `deals.py` |
| `deals.py::move_stage` | `access.py::can_write_deal` | write guard | WIRED | Lines 431-433 of `deals.py` |
| `deals.py::delete_deal` | `access.py::can_delete_deal` | delete guard | WIRED | Lines 521-523 of `deals.py` |
| `deals.py::_get_deal_or_404` | `access.py::require_deal_readable` | single delegation | WIRED | Line 235 of `deals.py` — inherits 403/404 split to activities |
| `counterparties.py::list_for_deal` | `access.py::require_deal_readable` | read gate | WIRED | Line 88 of `counterparties.py` |
| `counterparties.py::create/update/delete` | `access.py::require_deal_writable` | write gate | WIRED | Lines 109, 133, 156 of `counterparties.py` |
| `funding.py::list_for_deal` | `access.py::require_deal_readable` | read gate | WIRED | Line 75 of `funding.py` |
| `funding.py::create/update/delete` | `access.py::require_deal_writable` | write gate | WIRED | Lines 101, 123, 145 of `funding.py` |
| `DealDetailPage.jsx::isError branch` | `deal GET 403 response` | `error.response?.status === 403` check | WIRED (code) | Lines 946-953; browser rendering requires human confirmation |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `access.py::require_deal_readable` | `deal` from `db.scalar(select(Deal).where(...))` | PostgreSQL via SQLAlchemy async session | Yes — real DB query scoped to `org_id` | FLOWING |
| `deals.py::_base_deal_stmt` | `visible_team_ids` from `accessible_team_ids` → `visible_deal_team_ids(user)` | Pure function on user object (no DB) | Yes — returns None / [] / [team_id] based on role | FLOWING |
| `deals.py::list_deals` | deal rows from `_base_deal_stmt` join query | Real DB query with team/private predicates | Yes — scoped WHERE clause from role-based predicates | FLOWING |

---

### Behavioral Spot-Checks

Step 7b SKIPPED for Docker-containerized backend — service is not runnable inline. Tests were run in Docker (36 passed per SUMMARY, corroborated by 36 `def test_` functions and full test file read). No inline behavioral execution possible.

---

### Probe Execution

No `scripts/*/tests/probe-*.sh` files declared or found for this phase. Phase uses pytest-based integration tests run in Docker.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| ACCESS-01 | 18-01 | Contacts and Companies readable by all authenticated users | SATISFIED | `test_contacts_globally_readable` asserts 200 for all roles; contacts/companies services have no group filter |
| ACCESS-02 | 18-01, 18-03 | Deals readable only by same-group members, Supervisor, Principals, Admins (Calls/Notes deferred to Phase 19 per D-21) | SATISFIED for Deals | List scoping via `visible_deal_team_ids`; detail via `require_deal_readable`; child entities inherit via `require_deal_readable` gate |
| ACCESS-03 | 18-02 | Regular User can CRUD own Deals | SATISFIED | `can_write_deal` owner check; `can_delete_deal` owner check; tests cover create/update/delete own deal |
| ACCESS-04 | 18-02 | Supervisor can read and edit (not delete) same-group Deals | SATISFIED | `can_write_deal` allows supervisor same-team; `can_delete_deal` owner-or-admin only; proven by supervisor tests |
| ACCESS-05 | 18-01 | Principal reads all Deals across all groups | SATISFIED | `visible_deal_team_ids` returns None for principal; `can_read_deal` short-circuits True for principal; `test_principal_sees_all_teams_in_list` green |
| ACCESS-06 | 18-02 | Admin full CRUD across all groups | SATISFIED | `can_write_deal` and `can_delete_deal` both short-circuit True for admin; all admin tests pass |
| ACCESS-07 | 18-02, 18-03 | Out-of-scope requests return 403 not 404 | SATISFIED (backend) | `require_deal_readable` load-then-decide; existence check org-only; forbidden = 403; absent = 404; all 403/404 tests green |

**Orphaned requirements check:** REQUIREMENTS.md Traceability maps `ACCESS-01 to ACCESS-07` to Phase 18 with Plan TBD. All 7 are claimed across the 3 phase plans and all are covered. No orphaned requirements.

**Note on ACCESS-02 scope:** REQUIREMENTS.md defines ACCESS-02 as covering "Calls, Notes, and Deals." Phase 18 implements Deals only — Call and Note endpoints do not exist yet. Decision D-21 (documented in 18-RESEARCH.md and honored in access.py) explicitly excludes Call/Note stubs. This is not a gap: there is nothing to guard. Call/Note access enforcement will be wired in Phase 19 when those endpoints are created.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/auth/access.py` | 43 | `return []` | Info | Intentional behavior: unassigned user (team_id is None) sees no deals. Not a stub — this is the T-18-04 mitigation documented in the threat model. |
| `backend/services/deals.py` | 327 | `is_manager_plus` retained in `create_deal` pipeline check | Info | Intentional per Plan 02 Decision #3: this gates pipeline team access during creation, not deal ownership. Outside the scope of the role-write matrix. |

No TBD, FIXME, or XXX markers in any file modified by this phase.

---

### Human Verification Required

#### 1. 403 vs 404 error message on deal detail page

**Test:** Log into the running app as a Regular User on one team (e.g., beta-team). Obtain the UUID of a deal owned by a different team (e.g., an alpha-team deal) and navigate directly to `/deals/{that-uuid}` in the browser address bar.

**Expected:** The deal detail page displays "You don't have permission to view this deal." — the permission-denied message, not the removal message.

**Why human:** The JSX at lines 946-953 of DealDetailPage.jsx reads `dealQuery.error?.response?.status` and branches on `=== 403`. This optional-chain path resolves to an integer only when the Axios error response is structured as `{ response: { status: 403 } }`. Grep confirms the code is correct, but the actual Axios error shape must be verified in a live browser session to confirm `response` is not `undefined` (which would cause the else-branch to fire instead).

#### 2. 404 message on non-existent deal UUID

**Test:** While logged in, navigate to `/deals/{random-nonexistent-uuid}` in the browser.

**Expected:** The deal detail page displays "Could not load deal. It may have been removed." — the 404 message, not the permission message.

**Why human:** Same JSX branch — must confirm the else-path renders the correct fallback in browser, not the 403 message.

---

### Gaps Summary

No automated gaps found. All 6 success criteria are verified in the backend codebase and backed by 36 integration tests. The single open item is the frontend UX rendering of the 403/404 message distinction — the code change is present but browser confirmation is pending (per-plan human checkpoint that was explicitly deferred from Task 3 of Plan 03).

---

### Commit Verification

All 11 commits documented in the SUMMARY files are present in git log:

| Commit | Plan | Description |
|--------|------|-------------|
| 821ad21 | 18-01 | Create backend/auth/access.py centralized authz module |
| 0b75ac7 | 18-01 | Rewrite _crm.py accessible_team_ids and private_deal_predicate to delegate |
| f518985 | 18-01 | Add failing tests for list/visibility/global-read matrix |
| 1849253 | 18-01 | Add principal fixture + fix connection pool isolation in tests |
| 4d8405b | 18-02 | RED — add failing 403/404 split tests |
| 9cc06be | 18-02 | GREEN — load-then-decide get_deal + _get_deal_or_404 |
| 92dbf41 | 18-02 | RED — add failing write/delete guard tests |
| 918c8c5 | 18-02 | GREEN — can_write_deal/can_delete_deal guards threaded through |
| 792364b | 18-02 | Admin full-CRUD + CREATE team_id matrix tests + pipeline fix |
| bba072a | 18-03 | Parent-deal access guards on counterparties.py and funding.py |
| 1f2b2fd | 18-03 | Child-entity cross-team tests + DealDetailPage 403/404 patch |

---

_Verified: 2026-06-29_
_Verifier: Claude (gsd-verifier)_
