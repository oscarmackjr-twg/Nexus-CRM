---
phase: 18-access-enforcement
reviewed: 2026-06-29T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - backend/auth/access.py
  - backend/services/_crm.py
  - backend/services/deals.py
  - backend/services/counterparties.py
  - backend/services/funding.py
  - backend/tests/conftest.py
  - backend/tests/test_access_enforcement.py
  - frontend/src/pages/DealDetailPage.jsx
findings:
  critical: 0
  warning: 4
  info: 8
  total: 12
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-06-29
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

This is the access-enforcement phase. I traced the authorization chain end-to-end:
`require_deal_readable` / `require_deal_writable` (auth/access.py) → deals/counterparties/funding
services → routes. To resolve open questions I also read `backend/api/routes/funding.py`,
`backend/api/routes/counterparties.py`, `backend/database.py`, and the counterparty/funding
schemas.

**The core authz is sound.** The 403-vs-404 split is implemented correctly (load-scoped-to-org,
then decide), the role write/delete matrix in `can_write_deal`/`can_delete_deal` matches the
stated decisions, and the IDOR surface on deal-child resources is closed: counterparties and
funding gate every read on `require_deal_readable` and every mutation on `require_deal_writable`,
and they additionally constrain child rows by `deal_id` + `org_id` in the WHERE clause. List
endpoints silently filter (never 403) and detail endpoints return 403 for in-org-but-out-of-scope
deals. The seeded test matrix exercises the headline cases and they look correct.

No BLOCKER-class authz hole was found. The findings below are an authorization *inconsistency*
(activity logging gated on read, not write), a robustness gap that can produce a 500, a React
side-effect anti-pattern, and a notable test-coverage gap on the child-entity write/IDOR matrix.

## Warnings

### WR-01: Activity logging is gated on READ access, not WRITE — non-owner can mutate a teammate's deal

**File:** `backend/services/deals.py:498-518` (and `get_deal_activities` at 468)
**Issue:** `log_activity` calls `_get_deal_or_404` → `require_deal_readable` only. Counterparties
and funding correctly require `require_deal_writable` for create/update/delete, but activity
creation (a mutation that inserts a `DealActivity`, including `is_private` rows attributed to the
caller) is permitted to any user who can merely *read* the deal. A same-team `regular_user` who is
not the owner — who is explicitly blocked from editing the deal (`can_write_deal` → owner-only) and
from adding counterparties/funding — can still write activity records onto that deal. This is an
authorization inconsistency for a phase whose entire purpose is enforcing the write matrix. (Scope
is limited to same-team readers, since cross-team callers get 403 from the read guard, which is why
this is a WARNING and not a BLOCKER — but the policy gap is real and should be an explicit decision.)
**Fix:** If logging an interaction is meant to require edit rights, gate it on write:
```python
async def log_activity(self, deal_id, data):
    deal = await require_deal_writable(self.db, deal_id, self.current_user)
    ...
```
If read-level logging is intentional, document the decision and add a test asserting a same-team
non-owner can POST `/activities` so the policy is pinned.

### WR-02: `get_deal` can raise 500 when the joined response row is absent

**File:** `backend/services/deals.py:309-317`
**Issue:** After `require_deal_readable` confirms the deal exists and is readable, `get_deal`
re-runs `_base_deal_stmt(...).where(Deal.id == deal_id)` and does `row = (...).first()` with **no
None guard**, then passes `row` to `_deal_response`, which immediately dereferences `row[0]`.
`_base_deal_stmt` uses INNER joins on `Pipeline`, `PipelineStage`, and `User` (owner). If the
deal's `owner_id`/`pipeline_id`/`stage_id` points at a row that has been removed, or the private
predicate diverges from `can_read_deal`, `first()` returns `None` and the request 500s instead of
returning a clean response. The readable check passed against the `Deal` table alone, so the two
queries are not guaranteed to agree. WR-02 also applies to the same pattern reachable via
`create_deal`/`update_deal`/`move_stage` (all end in `return await self.get_deal(...)`).
**Fix:** Guard the row:
```python
row = (await self.db.execute(stmt)).first()
if row is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
```

### WR-03: Frontend syncs form state via `useMemo` side-effects — stale forms after refetch

**File:** `frontend/src/pages/DealDetailPage.jsx:837-895`
**Issue:** Form state is initialised by calling `setIdentityForm(...)` (and four siblings) **inside a
`useMemo`**. Running `setState` during render from `useMemo` is a React anti-pattern (the eslint
disable on line 894 suppresses the warning rather than fixing it). Each setter only fires when its
form is still `null`, so once initialised the forms **never re-sync** when `deal` changes — e.g.
after a successful save invalidates `['deal', id]` and refetches, or when another user's edit lands.
Re-opening a card then shows stale local values instead of the server's current state.
**Fix:** Use `useEffect` keyed on the deal identity and reset the relevant form when the source data
changes:
```jsx
useEffect(() => {
  if (!deal) return;
  setIdentityForm({ transaction_type_id: deal.transaction_type_id || '', /* ... */ });
  // ...the other four forms
}, [deal]);
```
(Reset on cancel/save close so re-opening reflects the latest server data.)

### WR-04: No tests for the child-entity write/IDOR matrix (update & delete)

**File:** `backend/tests/test_access_enforcement.py:444-543`
**Issue:** The child-entity tests cover cross-team **list** and **create** 403s plus same-team/admin
200s, but there is **no** coverage for:
- counterparty/funding **UPDATE** and **DELETE** cross-team returning 403,
- the IDOR case where a counterparty/funding row belonging to deal A is targeted through deal B's
  URL (the code defends this with `deal_id == deal_id` in the WHERE clause, but it is untested),
- a same-team **non-owner** `regular_user` being blocked (403) from create/update/delete on a deal
  they can read but not write (the read/write distinction that WR-01 hinges on).
For a phase explicitly about access enforcement and IDOR on inherited child access, these are the
exact regressions most likely to slip in later unnoticed.
**Fix:** Add tests, e.g.:
```python
# beta-rep PATCH/DELETE a counterparty/funding row under an alpha deal -> 403
# alpha-peer (same team, not owner) POST/PATCH/DELETE under alpha_deal -> 403
# create cp under alpha_deal as alpha-rep, then PATCH it via beta_deal's URL -> 403/404
```

## Info

### IN-01: Dead conditional in `update_deal` owner reassignment

**File:** `backend/services/deals.py:378-396`
**Issue:** Line 378 already 403s any non-admin who supplies `owner_id`, so the `and not
is_admin(self.current_user)` on line 394 is unreachable — only admins ever reach it.
**Fix:** Drop the redundant `and not is_admin(...)` (or the early 403) and keep one consistent guard.

### IN-02: Admin owner reassignment can orphan read access

**File:** `backend/services/deals.py:390-396`
**Issue:** An admin may set `owner_id` to a user whose `team_id != deal.team_id` (admin bypasses the
400 on line 394) without changing `deal.team_id`. The new owner then fails `can_read_deal`'s team
check and cannot read or edit the deal they "own". Data-integrity edge.
**Fix:** When admin reassigns across teams, either also move `deal.team_id` to the new owner's team
or forbid cross-team reassignment unless `team_id` is updated in the same request.

### IN-03: Duplicated authz helpers across modules

**File:** `backend/services/_crm.py:111-112,150-153` vs `backend/auth/access.py:12-13,47-56`
**Issue:** `is_admin` and `private_deal_predicate` exist in both `_crm.py` and `auth/access.py`
(the `_crm` versions delegate or re-implement). Two sources of truth for authz primitives invite
drift.
**Fix:** Re-export the `auth/access` versions from `_crm` (or import directly) and delete the
local copies.

### IN-04: `.where(True)` / `.where(False)` rely on Python-bool coercion

**File:** `backend/auth/access.py:55` (returns `True`) and `backend/services/deals.py:110`
(`stmt.where(False)`)
**Issue:** Passing raw Python booleans into `.where()` depends on SQLAlchemy's bool coercion, which
is version-fragile and emits deprecation warnings in some releases. The intent is sound (no-op /
match-nothing) but brittle.
**Fix:** Use explicit clause elements: `from sqlalchemy import true, false` and return `true()` /
`stmt.where(false())`.

### IN-05: Inconsistent transaction boundaries between sibling services

**File:** `backend/services/counterparties.py` (commits inside the service) vs
`backend/services/funding.py` (only `flush()`, route commits)
**Issue:** Counterparty create/update/delete call `await self.db.commit()` internally; funding does
`flush()` and relies on the route (`funding.py:41,54,66`) to commit. Both are currently correct, but
the divergent pattern is a maintenance hazard — a future funding route added without an explicit
commit would silently lose writes.
**Fix:** Pick one unit-of-work convention (preferably commit-at-route for all child services) and
apply it uniformly.

### IN-06: `eval()` in test FakeRedis

**File:** `backend/tests/conftest.py:94,101`
**Issue:** `FakeRedis.lpush`/`ltrim` use `eval(current)` on stored `repr(...)` strings. Test-only and
the data originates from app code, so low risk, but `eval` on persisted state is a smell.
**Fix:** Store native Python lists in the dict (the fake controls its own storage), or use
`ast.literal_eval`.

### IN-07: Return-type annotations don't match returned type

**File:** `backend/services/deals.py:61` and `backend/services/_crm.py:39`
**Issue:** `_visible_team_ids`/`accessible_team_ids` are annotated `set[UUID] | None` but actually
return `list[UUID] | None` (from `visible_deal_team_ids`). Harmless at runtime (`.in_()` accepts a
list) but misleading.
**Fix:** Annotate `list[UUID] | None`.

### IN-08: No client-side permission gating; 403s surface as a generic toast

**File:** `frontend/src/pages/DealDetailPage.jsx:905, 1093-1104, 254-264, 657-667`
**Issue:** Edit/Save/Delete controls render for every viewer regardless of write permission; the
backend correctly enforces 403, but `updateDealMutation.onError` shows a generic "Failed to save
changes" even on 403, and counterparty/funding error toasts likewise don't distinguish forbidden
from failure. Defense-in-depth and UX are weak (users without rights can attempt edits and get an
unhelpful message). Backend enforcement makes this non-security, hence Info.
**Fix:** Surface the deal's effective permission (e.g., a `can_edit` flag from the API) to hide or
disable mutate controls, and special-case `error.response?.status === 403` in the toast text.

---

_Reviewed: 2026-06-29_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
