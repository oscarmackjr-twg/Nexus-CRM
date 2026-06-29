# Phase 18: Access Enforcement - Research

**Researched:** 2026-06-29
**Domain:** Python / FastAPI service-layer RBAC enforcement
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**403 / 404 Leakage Matrix**
- D-01: Out-of-scope existing record on detail GET `/{id}` → 403 Forbidden.
- D-02: Nonexistent ID → 404 Not Found. Clean split: 403 = "exists, forbidden", 404 = "no such record".
- D-03: LIST endpoints → out-of-scope records silently filtered out. No "hidden total" exposed.
- D-04: Out-of-scope WRITE/DELETE → 403.
- D-05: "Allowed-but-action-denied" (e.g., Supervisor deletes team member's deal) → 403, same status code as out-of-scope.

**Role Write/Delete Matrix**
- D-06: Principal = read-all across all groups + CRUD on own records only.
- D-07: Owner can always delete their own record (delete permission = owns-it OR is-admin).
- D-08: Supervisor = read + edit any deal in their group; cannot delete other members' deals (403); can delete own (D-07).
- D-09: Admin = full CRUD on any deal across any group; never receives 403.
- D-10: Regular User = CRUD own deals; read group-visible deals; 403 on other groups' deals.
- D-11: `is_private` hides from same-group peers only — Supervisor, Principal, Admin still see it.
- D-12: On CREATE, team_id forced server-side to creator's own group. Admin may override (planner discretion).
- D-13: Only Admin can reassign team_id or owner_id via update.

**Enforcement Architecture**
- D-14: Centralize four-role scoping in one reusable authz module (e.g., `backend/auth/access.py`).
- D-15: Two enforcement points: (a) SQL query predicate for list/read scoping; (b) action guard in get/update/delete that loads the record and raises 403/404.
- D-16: Full rewrite of `accessible_team_ids()` and reconciliation of `private_deal_predicate()`. Do it right once.

**Entity Scope**
- D-17: Enforce group-scoping on Deals. Contacts and Companies are global-read.
- D-18: Contacts/Companies writes remain open to any authenticated user.
- D-19: Deal child entities (DealActivity, DealCounterparty, DealFunding) inherit parent deal visibility.
- D-20: Funds are global / org-level reference data — no group scoping.
- D-21: Calls/Notes not wired in this phase. Authz module shaped for Phase 19 to register them in one line.

### Claude's Discretion
- Exact module name/location (`backend/auth/access.py` vs. expanding `_crm.py`).
- Whether 403 responses carry distinct detail messages.
- Admin-override path for create/reassign (D-12, D-13).
- SQL predicate vs. hybrid load-then-filter for list scoping.
- Test fixtures/strategy for the role × action matrix.

### Deferred Ideas (OUT OF SCOPE)
- Call and Note entity enforcement — Phase 19.
- Distinct 403 detail messages — optional; planner may include or skip.
- Tasks/Boards group scoping.
- PostgreSQL row-level security (RLS) — explicitly out of scope for v1.3.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ACCESS-01 | Contacts and Companies readable by all authenticated users regardless of group | Contact/Company have no `team_id` column — global-read is already enforced by org_id scoping; no code change needed for reads |
| ACCESS-02 | Deals readable only by same-group, Supervisors of that group, Principals, and Admins | Requires rewriting `accessible_team_ids()` and `private_deal_predicate()` in `_crm.py`; principal/admin must return `None` (no team filter) |
| ACCESS-03 | Regular User can create, edit, delete own Deals | Current create/delete logic is close; update_deal uses `is_manager_plus` (wrong for cross-team supervisor); needs `can_write_deal` guard |
| ACCESS-04 | Supervisor can read and edit (but NOT delete) any Deal of their group members | Needs `can_write_deal(supervisor, deal)` returning True for same-team deals; `can_delete_deal` returns False for non-owned deals |
| ACCESS-05 | Principal can read all Deals across all groups | `accessible_team_ids()` must return `None` for Principal (currently broken — returns `[user.team_id]`) |
| ACCESS-06 | Admin has full CRUD across all groups | `accessible_team_ids()` must return `None` for Admin (currently broken); delete guard must not block admin |
| ACCESS-07 | API endpoints return 403 (not 404) for out-of-scope records | `get_deal()` must use load-then-decide pattern; `_get_deal_or_404` used by activities must be updated |

</phase_requirements>

---

## Summary

Phase 18 is a **pure backend enforcement phase**: the schema from Phase 17 is already correct, and no new database columns or migrations are required. The work is entirely in the Python service layer — rewriting two broken helper functions, adding a new authz module, and threading access guards through every deal CRUD method and every deal-child service.

The most critical code finding: `accessible_team_ids()` in `_crm.py` currently returns `[user.team_id]` for ALL roles, including Admin and Principal — this means administrators and principals cannot see deals from other groups. Every feature that depends on role-based visibility is currently broken. This single chokepoint feeds `DealService._base_deal_stmt()`, so fixing it correctly propagates to all list/get operations automatically.

The second critical finding: `get_deal()` in `DealService` returns 404 for both "doesn't exist" and "exists but out-of-scope" — violating ACCESS-07 / D-01. The fix is a load-then-decide pattern: load the record without team-scoping (to detect existence), then apply the authz check to decide 403 vs 200.

The third finding: both `DealCounterpartyService` and `DealFundingService` have their own `_get_deal_or_404` methods that only apply org-level scoping — no team check. A user from team Beta can access counterparties and funding entries for team Alpha's deals. D-19 closes this side-door by requiring child services to call the shared authz guard.

**Primary recommendation:** Create `backend/auth/access.py` as the single authz source of truth. Rewrite `accessible_team_ids` and `private_deal_predicate` in `_crm.py` to delegate to it. Update all five deal CRUD methods in `DealService` plus both child services. Three plans: (1) authz module + list scoping, (2) action guards + deal CRUD, (3) child entity guards + frontend 403 handling.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Team visibility query predicate | API / Backend (`backend/auth/access.py`) | — | Pure SQL predicate logic; no DB schema change needed |
| 403 vs 404 decision for GET `/{id}` | API / Backend (`DealService.get_deal`) | — | Load-then-decide pattern; route layer is thin and stays thin |
| Write/delete permission guard | API / Backend (`DealService.update_deal`, `delete_deal`) | — | Service layer owns all business logic per existing pattern |
| Child entity parent-deal scope | API / Backend (`DealCounterpartyService`, `DealFundingService`) | — | Child services already call `_get_deal_or_404`; replace with authz-aware version |
| List scoping (silent filter) | API / Backend (`DealService._base_deal_stmt`) | — | SQL WHERE predicate; pagination/counts must reflect filtered result |
| 403 error display in frontend | Browser / Client (`DealDetailPage.jsx`) | — | `isError` branch currently shows generic "may have been removed"; needs status-code check |
| CREATE team_id enforcement | API / Backend (`DealService.create_deal`) | — | Already forces creator.team_id; admin override is additive |

---

## Standard Stack

### Core (no new packages — enforcement is pure Python logic)

| Component | Current Location | Role in Phase 18 |
|-----------|-----------------|-----------------|
| `backend/auth/access.py` | NEW FILE | Single authz source of truth — all role check functions |
| `backend/services/_crm.py` | Existing | Delegates to access.py; keeps pagination/utility helpers |
| `backend/services/deals.py` | Existing | Primary integration site — all CRUD methods updated |
| `backend/services/counterparties.py` | Existing | Replace `_get_deal_or_404` with authz-aware version |
| `backend/services/funding.py` | Existing | Replace `_get_deal_or_404` with authz-aware version |
| `backend/auth/security.py` | Existing | No changes required — `get_current_user` and `require_org_admin` already correct |
| `frontend/src/pages/DealDetailPage.jsx` | Existing | Minor: distinguish 403 from 404 in `isError` branch |

**No new pip packages are required for this phase.**

### Supporting

| Component | Purpose | When to Use |
|-----------|---------|-------------|
| `fastapi.HTTPException` | Raise 403/404 | Already the project standard for error responses |
| `sqlalchemy.or_` | Compose WHERE predicates | Already used in `private_deal_predicate` |
| `pytest-asyncio` | Test async service methods | Already installed and configured |

---

## Package Legitimacy Audit

No external packages are installed in this phase. All changes are to existing Python and JavaScript files.

---

## Architecture Patterns

### System Architecture Diagram

```
REQUEST
   |
   v
FastAPI Route (deals.py, counterparties.py, funding.py)
   |  [thin — Depends(get_current_user), delegates to service]
   v
DealService / DealCounterpartyService / DealFundingService
   |
   |--- [LIST/READ scoping] ──────────────────────────────────────────────────
   |        |                                                                  |
   |        v                                                                  v
   |  access.visible_deal_team_ids(user)           access.private_deal_predicate(user)
   |  returns None (admin/principal)               returns True OR or_(is_private==False, owner==user)
   |  returns [user.team_id] (supervisor/reg)      based on user.role
   |        |                                                                  |
   |        +──────────────────────> _base_deal_stmt(visible_teams) ←─────────+
   |                                 WHERE deal.org_id == user.org_id
   |                                 AND (team_id IN [...] OR no-filter)
   |                                 AND (is_private predicate)
   |
   |--- [DETAIL GET / ACTION GUARD] ──────────────────────────────────────────
   |        |
   |        v
   |  Step 1: SELECT deal WHERE id=X AND org_id=user.org_id  (no team filter)
   |        |
   |        +-- deal is None ──> 404 "Deal not found"
   |        |
   |        +-- deal exists ──> access.can_read_deal(user, deal)
   |                                  |
   |                                  +-- False ──> 403 "Forbidden"
   |                                  |
   |                                  +-- True ──> proceed to full response / mutation
   |
   |--- [WRITE / DELETE guards (after read confirmed)] ───────────────────────
   |        |
   |        +-- update_deal ──> access.can_write_deal(user, deal)  or 403
   |        |
   |        +-- move_stage  ──> access.can_write_deal(user, deal)  or 403
   |        |
   |        +-- delete_deal ──> access.can_delete_deal(user, deal) or 403
   |
   |--- [CHILD ENTITY guard (D-19)] ───────────────────────────────────────────
            |
            v
       access.require_deal_readable(db, deal_id, user) ──> Deal OR 404/403
            |
            (for writes) access.require_deal_writable(db, deal_id, user) ──> Deal OR 404/403
```

### Recommended Project Structure

```
backend/
├── auth/
│   ├── security.py           # unchanged: get_current_user, require_org_admin
│   └── access.py             # NEW: all authz functions (single source of truth)
├── services/
│   ├── _crm.py               # MODIFIED: accessible_team_ids, private_deal_predicate delegate to access.py
│   ├── deals.py              # MODIFIED: get_deal, _get_deal_or_404, update_deal, move_stage, delete_deal, create_deal
│   ├── counterparties.py     # MODIFIED: _get_deal_or_404 replaced with require_deal_readable/writable
│   └── funding.py            # MODIFIED: _get_deal_or_404 replaced with require_deal_readable/writable
frontend/
└── src/
    └── pages/
        └── DealDetailPage.jsx  # MODIFIED: isError branch checks error.response?.status
```

### Pattern 1: `backend/auth/access.py` — Authz Module API

```python
# Source: derived from D-06..D-13 decisions + existing _crm.py patterns

from __future__ import annotations
from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status


# ── Role helpers ────────────────────────────────────────────────────────────

def is_admin(user) -> bool:
    return getattr(user, "role", None) == "admin"

def is_principal(user) -> bool:
    return getattr(user, "role", None) == "principal"

def is_supervisor(user) -> bool:
    return getattr(user, "role", None) == "supervisor"

def is_oversight_role(user) -> bool:
    """Supervisor, Principal, or Admin — all can see private deals within their scope."""
    return getattr(user, "role", None) in ("supervisor", "principal", "admin")


# ── List/read scoping ────────────────────────────────────────────────────────

def visible_deal_team_ids(user) -> list[UUID] | None:
    """
    Return the set of team_ids for SQL WHERE scoping.
    - None  → no team filter (Admin and Principal see all teams)
    - list  → filter to Deal.team_id IN (list)
    - []    → no deals visible (user has no team assignment)
    """
    if is_admin(user) or is_principal(user):
        return None  # All teams visible
    if user.team_id is None:
        return []    # Unassigned user sees nothing
    return [user.team_id]


def private_deal_predicate(user):
    """
    Returns a SQLAlchemy clause restricting private deals.
    - Admin / Principal / Supervisor: no restriction (oversight roles see all private deals)
    - Regular User: can only see private deals they own
    """
    from backend.models import Deal
    if is_oversight_role(user):
        return True   # No restriction — SQLAlchemy accepts True as a no-op WHERE clause
    return or_(Deal.is_private.is_(False), Deal.owner_id == user.id)


# ── Action permission checks (pure bool, no DB) ─────────────────────────────

def can_read_deal(user, deal) -> bool:
    """True if user can read this specific deal."""
    if is_admin(user) or is_principal(user):
        return True
    if user.team_id is None or deal.team_id != user.team_id:
        return False
    # Same team — check is_private for regular_user
    if user.role == "regular_user" and deal.is_private and deal.owner_id != user.id:
        return False
    return True


def can_write_deal(user, deal) -> bool:
    """True if user can update this deal (field edits, stage moves)."""
    if is_admin(user):
        return True
    if is_supervisor(user):
        return user.team_id is not None and deal.team_id == user.team_id
    # Principal and Regular User: own deals only
    return deal.owner_id == user.id


def can_delete_deal(user, deal) -> bool:
    """True if user can delete this deal (owner or admin)."""
    if is_admin(user):
        return True
    return deal.owner_id == user.id  # All non-admin roles: own deals only


# ── Async guards (DB + 403/404 decision) ────────────────────────────────────

async def require_deal_readable(db: AsyncSession, deal_id: UUID, user) -> "Deal":
    """
    Load deal, return it if readable. Raises 404 if not found, 403 if forbidden.
    Use this in child services (counterparties, funding) and deal detail actions.
    """
    from backend.models import Deal
    deal = await db.scalar(
        select(Deal).where(Deal.id == deal_id, Deal.org_id == user.org_id)
    )
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    if not can_read_deal(user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return deal


async def require_deal_writable(db: AsyncSession, deal_id: UUID, user) -> "Deal":
    """
    Load deal, return it if user can write to it. Raises 404/403 as appropriate.
    """
    deal = await require_deal_readable(db, deal_id, user)
    if not can_write_deal(user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return deal
```

### Pattern 2: Updated `_crm.py` — Delegating Wrappers

```python
# backend/services/_crm.py — replace these two functions

async def accessible_team_ids(session, user) -> list | None:
    """Delegate to access module. Returns None for admin/principal (no filter)."""
    from backend.auth.access import visible_deal_team_ids
    return visible_deal_team_ids(user)

def private_deal_predicate(user, visible_team_ids=None):
    """Delegate to access module. The visible_team_ids param is kept for compat."""
    from backend.auth.access import private_deal_predicate as _authz_predicate
    return _authz_predicate(user)
```

Note: `accessible_team_ids` is currently `async` but does no DB work — it can be made sync, or kept async for signature compat. The return type changes from `list[UUID]` to `list[UUID] | None`.

### Pattern 3: `DealService.get_deal()` — Load-Then-Decide

```python
async def get_deal(self, deal_id: UUID) -> DealResponse:
    # Step 1: Load without team-scoping to separate 404 from 403
    deal_raw = await self.db.scalar(
        select(Deal).where(Deal.id == deal_id, Deal.org_id == self.current_user.org_id)
    )
    if deal_raw is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    if not can_read_deal(self.current_user, deal_raw):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    # Step 2: Run full join query for response (deal is readable, so this won't be None)
    visible_team_ids = visible_deal_team_ids(self.current_user)
    stmt = self._base_deal_stmt(visible_team_ids).where(Deal.id == deal_id)
    row = (await self.db.execute(stmt)).first()
    deal_team = await self._load_deal_team(deal_id)
    return self._deal_response(row, deal_team=deal_team)
```

### Pattern 4: `DealService.update_deal()` — Correct Write Guard

```python
async def update_deal(self, deal_id: UUID, data: DealUpdate) -> DealResponse:
    # Load with 403/404 distinction
    deal = await require_deal_readable(self.db, deal_id, self.current_user)
    # Permission check for updates
    if not can_write_deal(self.current_user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    # D-13: Only admin can reassign owner_id
    if data.owner_id is not None and not is_admin(self.current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    # ... rest of update logic unchanged ...
```

### Pattern 5: `DealService.delete_deal()` — Correct Delete Guard

```python
async def delete_deal(self, deal_id: UUID) -> None:
    # Load with 403/404 distinction  
    deal = await require_deal_readable(self.db, deal_id, self.current_user)
    # Permission: owner or admin (D-07)
    if not can_delete_deal(self.current_user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    await self.db.delete(deal)
    await self.db.commit()
```

### Pattern 6: Child Service Guard Replacement

```python
# backend/services/counterparties.py (and funding.py — same pattern)

# Replace the current _get_deal_or_404 with calls to the access module:

async def list_for_deal(self, deal_id, ...):
    await require_deal_readable(self.db, deal_id, self.current_user)  # 403/404 gate
    # ... rest of list logic unchanged ...

async def create(self, deal_id, data):
    await require_deal_writable(self.db, deal_id, self.current_user)  # write gate
    # ... rest of create logic unchanged ...

async def update(self, deal_id, counterparty_id, data):
    await require_deal_writable(self.db, deal_id, self.current_user)
    # ... rest unchanged ...

async def delete(self, deal_id, counterparty_id):
    await require_deal_writable(self.db, deal_id, self.current_user)
    # ... rest unchanged ...
```

### Pattern 7: Frontend 403 vs 404 Distinction

```javascript
// frontend/src/pages/DealDetailPage.jsx — update the isError branch
if (dealQuery.isError) {
  const status = dealQuery.error?.response?.status;
  return (
    <div className="p-6 text-center text-muted-foreground">
      {status === 403
        ? "You don't have permission to view this deal."
        : "Could not load deal. It may have been removed."}
    </div>
  );
}
```

### Anti-Patterns to Avoid

- **Layering on top of broken `accessible_team_ids`**: The broken function returns `[user.team_id]` for everyone. Do not add a conditional check on top of it — replace the function entirely per D-16.
- **Using `is_manager_plus` for team-scoped write guards**: `is_manager_plus` returns `True` for supervisors but does NOT check `deal.team_id == user.team_id`. A supervisor can currently edit Beta's deals through `update_deal()` via `is_manager_plus`. Replace with `can_write_deal(user, deal)`.
- **Applying team filter after org filter in detail GETs**: Filtering by team in `_base_deal_stmt` and returning 404 when the team filter excludes a record violates D-01 (should be 403). Always load unscoped for existence check, then apply authz.
- **Returning 403 for LIST endpoints**: D-03 explicitly says list results are silently filtered — never raise 403 from a list endpoint.
- **Removing `private_deal_predicate` entirely for oversight roles**: The predicate must still be composed — just return `True` (a no-op clause) rather than omitting it, so `_base_deal_stmt` remains structurally consistent.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Role permission logic | Per-service role checks scattered through each method | Centralized `can_write_deal`, `can_delete_deal` in `access.py` | D-14 explicit requirement; Phase 19 must reuse verbatim |
| 403/404 DB load pattern | Inline logic in each service method | `require_deal_readable`, `require_deal_writable` in `access.py` | Consistent error handling; child services need the same function |
| JWT / user loading | Custom auth middleware | Existing `get_current_user` FastAPI dependency | Already correct and tested |
| SQLAlchemy WHERE composition | Manual string building | `or_()`, `and_()`, `in_()` operators | Already used in `_base_deal_stmt`; type-safe |

**Key insight:** The existing `DealService(db, current_user)` constructor pattern and thin routes are exactly the right architecture for this phase. No structural refactoring needed — only the helper functions and guard calls inside service methods need changing.

---

## Role × Action Truth Table

This is the authoritative matrix the planner MUST turn into tests. Every cell is a required test case.

### Visibility / GET `/{id}` — 200 or 403 or 404

| Scenario | Regular User | Supervisor | Principal | Admin |
|----------|-------------|------------|-----------|-------|
| Own deal (owner_id == user.id) | **200** | **200** | **200** | **200** |
| Same-team member's deal (not own, not private) | **200** | **200** | **200** | **200** |
| Same-team deal, `is_private=True`, not owner | **403** | **200** (oversight) | **200** (oversight) | **200** |
| Other-team deal (deal.team_id != user.team_id) | **403** | **403** | **200** (cross-group) | **200** |
| Other-team deal, `is_private=True` | **403** | **403** | **200** (oversight) | **200** |
| Nonexistent ID (wrong UUID) | **404** | **404** | **404** | **404** |

### LIST — silent filter (no 403, ever)

| Scenario | Regular User | Supervisor | Principal | Admin |
|----------|-------------|------------|-----------|-------|
| Own-team deals in results | **yes** | **yes** | **yes** | **yes** |
| Other-team deals in results | **no** | **no** | **yes** | **yes** |
| is_private deals from teammate (not own) | **no** | **yes** | **yes** | **yes** |
| Pagination/count reflects only visible | **yes** | **yes** | **yes** | **yes** |

### CREATE — 201 or 400

| Scenario | Regular User | Supervisor | Principal | Admin |
|----------|-------------|------------|-----------|-------|
| Normal create | **201**, `team_id=user.team_id` | **201** | **201** | **201** |
| Payload includes `team_id` (non-admin) | **ignored** (forced to user.team_id) | **ignored** | **ignored** | **honor if provided** |
| User has no `team_id` | **400** "not assigned to a team" | **400** | **400** | n/a (admin always has team) |

### UPDATE (PUT/PATCH) — 200 or 403

| Deal ownership | Regular User | Supervisor | Principal | Admin |
|---------------|-------------|------------|-----------|-------|
| Own deal | **200** | **200** | **200** | **200** |
| Same-team member's deal | **403** | **200** | **403** | **200** |
| Other-team deal | **403** | **403** | **403** | **200** |
| Any deal — change `owner_id` to another user | **403** | **403** | **403** | **200** |
| Any deal — provide `team_id` to reassign | **ignored** | **ignored** | **ignored** | **honored** (planner discretion) |

### MOVE-STAGE — same rules as UPDATE

(Same `can_write_deal` guard applies to `move_stage` as to `update_deal`.)

### DELETE — 204 or 403

| Deal ownership | Regular User | Supervisor | Principal | Admin |
|---------------|-------------|------------|-----------|-------|
| Own deal | **204** | **204** | **204** | **204** |
| Same-team member's deal (not own) | **403** | **403** | **403** | **204** |
| Other-team deal | **403** | **403** | **403** | **204** |

### DEAL CHILD ENTITIES (counterparties, funding) — inherit parent

| Action | User can read parent | User cannot read parent |
|--------|---------------------|------------------------|
| GET children | **200** | **403** (D-19) |
| POST child | **200** (if can_write_deal) | **403** |
| PATCH child | **200** (if can_write_deal) | **403** |
| DELETE child | **200** (if can_write_deal) | **403** |

### DEAL ACTIVITIES — special visibility rule

DealActivities already have `is_private` at activity level (not just deal level). The existing visibility filter `or_(DealActivity.is_private.is_(False), DealActivity.user_id == current_user.id)` is **already correct** and does not need to change. The gate needed for Phase 18 is that `_get_deal_or_404` in `DealService` returns 403 (not 404) for out-of-scope deals — then the existing activity-level filtering continues to apply.

### CONTACTS / COMPANIES (ACCESS-01) — always 200

| Role | GET /contacts | GET /companies |
|------|-------------|----------------|
| Any authenticated role | **200** | **200** |

No code changes needed for Contact/Company reads. Confirm by inspection: neither `Contact` nor `Company` has a `team_id` column in `models.py`. `ensure_contact_in_org` / `ensure_company_in_org` already exist and scope to `org_id` only. D-17 confirmed.

---

## Existing Code Bugs Found (VERIFIED by code inspection)

### Bug 1: `accessible_team_ids` returns wrong value for Admin/Principal
**File:** `backend/services/_crm.py` lines 39-43
**Current code:**
```python
async def accessible_team_ids(session: AsyncSession, user) -> list[UUID]:
    if user.team_id:
        return [user.team_id]
    return []
```
**Bug:** Returns `[user.team_id]` for Admin and Principal. An Admin cannot see deals from other teams. This breaks ACCESS-05, ACCESS-06.
**Fix:** Return `None` when `user.role in ("admin", "principal")`.

### Bug 2: `private_deal_predicate` blinds Supervisors and Principals to private deals
**File:** `backend/services/_crm.py` lines 151-155
**Current code:**
```python
def private_deal_predicate(user, visible_team_ids=None):
    from sqlalchemy import or_
    from backend.models import Deal
    return or_(Deal.is_private == False, Deal.owner_id == user.id)
```
**Bug:** Applies owner-only filter to ALL roles. D-11 says Supervisors, Principals, and Admins must see private deals.
**Fix:** Return `True` (no filter) for oversight roles; keep owner-only filter for Regular Users only.

### Bug 3: `get_deal()` returns 404 for out-of-scope deals
**File:** `backend/services/deals.py` line 321
**Current code:**
```python
if row is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
```
**Bug:** `_base_deal_stmt(visible_team_ids)` filters by team, so an out-of-scope deal is indistinguishable from a nonexistent one — both return 404. ACCESS-07 / D-01 requires 403 for the former.
**Fix:** Load-then-decide pattern (Pattern 3 above).

### Bug 4: `update_deal()` allows Supervisor to edit any-org deal
**File:** `backend/services/deals.py` line 384
**Current code:**
```python
if not (deal.owner_id == self.current_user.id or is_manager_plus(self.current_user)):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
```
**Bug:** `is_manager_plus` is True for supervisors AND admins without team check. A supervisor from team Alpha can edit team Beta's deals.
**Fix:** Replace with `can_write_deal(user, deal)`.

### Bug 5: `update_deal()` allows Supervisor to reassign `owner_id` (violates D-13)
**File:** `backend/services/deals.py` line 386
**Current code:**
```python
if data.owner_id is not None and not is_manager_plus(self.current_user):
    raise HTTPException(...)
```
**Bug:** `is_manager_plus` allows supervisors to change `owner_id`. D-13 says only Admin can reassign.
**Fix:** Change `is_manager_plus` to `is_admin` for this guard.

### Bug 6: `move_stage()` allows Supervisor to move other-team deals
**File:** `backend/services/deals.py` line 443
**Current code:**
```python
if not (deal.owner_id == self.current_user.id or is_manager_plus(self.current_user)):
    raise HTTPException(...)
```
**Bug:** Same as Bug 4 — no team check for supervisors.
**Fix:** Replace with `can_write_deal(user, deal)` after load-then-decide.

### Bug 7: `DealCounterpartyService._get_deal_or_404` has no team scoping
**File:** `backend/services/counterparties.py` lines 81-91
**Bug:** Only checks `Deal.org_id == user.org_id`. User from team Beta can access Alpha's deal counterparties.
**Fix:** Replace with `require_deal_readable(db, deal_id, user)` from `access.py`.

### Bug 8: `DealFundingService._get_deal_or_404` has no team scoping
**File:** `backend/services/funding.py` lines 29-37
**Bug:** Same pattern as Bug 7 for funding entries.
**Fix:** Replace with `require_deal_readable(db, deal_id, user)` from `access.py`.

### Bug 9: `_get_deal_or_404` in `DealService` returns 404 for out-of-scope
**File:** `backend/services/deals.py` lines 229-241
**Bug:** Uses `private_deal_predicate` and team filtering — returns 404 for team-scoped out-of-scope deals. Used by `get_deal_activities()` and `log_activity()`.
**Fix:** Replace with `require_deal_readable` pattern.

---

## What is Already Correct (Do Not Break)

- `is_admin(user)` — correct, checks `role == "admin"` [VERIFIED by reading `_crm.py`]
- `is_manager_plus(user)` — correct as a boolean, but not sufficient alone for team-scoped write guards (keep but supplement with `can_write_deal`)
- `ensure_owner_or_admin` — correct; used in non-Deal contexts; keep as-is
- `create_deal()` team_id assignment — already forces `team_id=self.current_user.team_id` [VERIFIED]
- `delete_deal()` permission logic — `is_admin(user) or deal.owner_id == user.id` matches D-07 **but** the 404/403 distinction for the load needs fixing (Bug 3 pattern)
- `require_org_admin` in `security.py` — checks `role == "admin"`, correct after Phase 17 migration [VERIFIED]
- Contact/Company services — no `team_id` column exists; global-read is naturally enforced by org_id; no changes needed [VERIFIED by models.py inspection]
- `DealActivity.is_private` visibility filter — `or_(is_private == False, user_id == current_user.id)` is correct and intentional; keep as-is
- `DealService` constructor pattern `DealService(db, current_user)` — perfect for threading authz; no change
- Test conftest `seeded_org` fixture — has alpha/beta teams and multiple users; extend rather than replace

---

## Common Pitfalls

### Pitfall 1: Returning 404 from action guards when scope-checking
**What goes wrong:** Guard loads record with team-scoped WHERE; record is filtered out; raises 404. Violates ACCESS-07/D-01.
**Why it happens:** Natural instinct to add team filter to the existence check query.
**How to avoid:** Always do two-step: (1) load with `org_id` only, (2) apply authz check. The load step answers "does it exist?"; the authz step answers "can this user see it?".
**Warning signs:** Any `select(Deal).where(Deal.team_id.in_(...))` followed by a 404 raise.

### Pitfall 2: Forgetting the `is_private` nuance for same-team supervisors
**What goes wrong:** Supervisor from team Alpha is blocked from a private deal belonging to team Alpha.
**Why it happens:** Old `private_deal_predicate` applies owner-only filter regardless of role.
**How to avoid:** `is_oversight_role(user)` check before applying the private filter.
**Warning signs:** Test case "supervisor reads private deal of team member" returns 403.

### Pitfall 3: UUID comparison in Python vs. SQLAlchemy
**What goes wrong:** `deal.team_id != user.team_id` in Python fails because one is a `UUID` object and the other is a string representation.
**Why it happens:** SQLite stores UUIDs without hyphens; SQLAlchemy's `Uuid()` type may return plain UUID objects or strings depending on dialect.
**How to avoid:** Force comparison via `str(deal.team_id) == str(user.team_id)` OR ensure both sides use `UUID` objects. The existing codebase uses `Uuid()` type which returns Python `UUID` objects in SQLAlchemy 2.0 — direct `==` comparison should work. Verify with a test.
**Warning signs:** Team membership check returns False for identical teams in SQLite tests.

### Pitfall 4: Principal user missing from test fixtures
**What goes wrong:** No `principal` user in `seeded_org` fixture — cannot test ACCESS-05 at all.
**Why it happens:** Phase 17 added the `principal` role but `seeded_org` was written before Phase 18 test design.
**How to avoid:** Wave 0 gap — add `("principal@example.com", "principal", "principal", alpha)` to `seeded_org` fixture.
**Warning signs:** `KeyError: 'principal'` when accessing `seeded_org["principal"]` in tests.

### Pitfall 5: Supervisor with `team_id=None`
**What goes wrong:** `can_write_deal(user, deal)` for a supervisor with no team assignment: `user.team_id is None` → `False`. This is correct behavior (unassigned supervisor sees nothing), but tests must cover it.
**Why it happens:** Edge case. Supervisors should always have a team, but the column is nullable.
**How to avoid:** No code change needed — the `user.team_id is None` check in `can_write_deal` returns `False` correctly.

### Pitfall 6: `accessible_team_ids` is async but does no I/O
**What goes wrong:** Callers use `await accessible_team_ids(...)` but after the fix it's a pure sync computation.
**Why it happens:** Original function was designed async in case it queried the DB; it never did.
**How to avoid:** Either keep it `async` for zero disruption to callers, or change to sync and update all `await` call sites. Recommend keeping it `async` (zero call-site changes) while adding a note that it no longer needs the `session` parameter (can keep session param for API compat).

### Pitfall 7: Child service write guards for create/update/delete
**What goes wrong:** Child services call `require_deal_readable` (read gate) for write operations — a Supervisor from another team could create counterparties if they can read the deal.
**Why it happens:** Confusion between read access and write access.
**How to avoid:** CREATE/UPDATE/DELETE child operations must call `require_deal_writable` (which internally checks `can_write_deal`), not `require_deal_readable`.

---

## Frontend: 403 Handling Audit

**Current behavior** (`frontend/src/api/client.js` lines 19-43):
The Axios response interceptor handles **only 401** (triggers token refresh or redirects to login). It does NOT intercept 403. All other errors (including 403) are passed through as rejected promises with the full Axios error object.

**Impact of this gap:**
- `DealDetailPage.jsx` query error state (line 945): shows "Could not load deal. It may have been removed." for BOTH 403 and 404. A user who can't access a deal gets the same message as a user who typed the wrong UUID — no actionable feedback.
- Mutation `onError` handlers throughout `DealDetailPage.jsx` correctly show `e.response?.data?.detail` — the FastAPI `detail` message from a 403 is surfaced as a toast. **Mutations are already fine.**
- The gap is isolated to **initial load queries** (GET), not mutations.

**Required fix (minimal):** Update the `dealQuery.isError` branch in `DealDetailPage.jsx` to check `error.response?.status === 403` and show a distinct message. This is a 3-line change.

**Optional (planner discretion):** Add a global 403 interceptor in `client.js` to redirect to a `/forbidden` page or set a global toast. Not required by requirements; useful for consistency.

**No changes to `client.js` are strictly required** to meet ACCESS-01..ACCESS-07 — the requirements are backend enforcement requirements. The frontend change is a UX improvement.

---

## Runtime State Inventory

This phase is NOT a rename/refactor phase. No stored data keys, service names, or OS registrations reference concepts being changed.

**Nothing found in any category** — verified by examining Phase 17 completion (role strings already renamed in DB by Alembic migration 0012; no external service config stores deal access rules; no scheduled tasks reference the authz model).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python / pytest | Backend tests | ✓ | In Docker container | — |
| SQLite (aiosqlite) | Test database | ✓ | Confirmed by conftest.py | — |
| Docker / docker-compose | Test runner (`make test`) | ✓ | Confirmed by Makefile | Direct `pytest` also works |
| FastAPI / httpx | Integration tests | ✓ | Already in backend requirements | — |
| React / axios | Frontend change | ✓ | Already in frontend deps | — |

No missing dependencies. This phase is pure code changes.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (already installed) |
| Config file | `backend/tests/conftest.py` (session-scoped SQLite DB; per-test `clean_db` fixture) |
| Quick run command | `pytest backend/tests/test_access_enforcement.py -x -v` |
| Full suite command | `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ACCESS-01 | Contacts/Companies readable by all roles | integration | `pytest backend/tests/test_access_enforcement.py::test_contacts_globally_readable -x` | Wave 0 |
| ACCESS-02 | Deals not readable across groups | integration | `pytest backend/tests/test_access_enforcement.py::test_cross_team_deal_get_returns_403 -x` | Wave 0 |
| ACCESS-03 | Regular User CRUD own deals, 403 on others | integration | `pytest backend/tests/test_access_enforcement.py::test_regular_user_crud_matrix -x` | Wave 0 |
| ACCESS-04 | Supervisor read+edit, no delete on member deals | integration | `pytest backend/tests/test_access_enforcement.py::test_supervisor_write_delete_matrix -x` | Wave 0 |
| ACCESS-05 | Principal reads all groups | integration | `pytest backend/tests/test_access_enforcement.py::test_principal_reads_all_teams -x` | Wave 0 |
| ACCESS-06 | Admin full CRUD across all groups | integration | `pytest backend/tests/test_access_enforcement.py::test_admin_full_crud_cross_team -x` | Wave 0 |
| ACCESS-07 | 403 not 404 for out-of-scope records | integration | `pytest backend/tests/test_access_enforcement.py::test_403_not_404_semantics -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/test_access_enforcement.py -x`
- **Per wave merge:** `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/test_access_enforcement.py` — covers ALL ACCESS-01..ACCESS-07 via the role × action matrix
- [ ] `seeded_org` fixture in `conftest.py` — needs `principal` user added (currently missing)
- [ ] `deal_fixtures` helper or fixture — creates alpha-team and beta-team deals for cross-matrix testing

**Suggested seeded_org extension (add one entry):**
```python
("principal@example.com", "principal", "principal", alpha),
```
This user is in team Alpha but has Principal read-all privileges.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Already enforced via `get_current_user` JWT check (Phase auth) |
| V3 Session Management | No | JWT tokens, no change in this phase |
| V4 Access Control | **Yes** | Application service layer authz — `can_read_deal`, `can_write_deal`, `can_delete_deal` |
| V5 Input Validation | Partial | `team_id` forced server-side on create (D-12); payload `team_id` ignored for non-admins |
| V6 Cryptography | No | No cryptographic operations added |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Horizontal privilege escalation (user reads other team's deals) | Information Disclosure | `accessible_team_ids` returning `None` only for admin/principal; team filter in SQL |
| 404 information leakage (attacker probes deal IDs to discover org's deal count) | Information Disclosure | D-01: return 403 not 404 for in-org but out-of-scope records |
| Insecure direct object reference (IDOR) on deal-child endpoints | Elevation of Privilege | `require_deal_readable` / `require_deal_writable` as gate before child operations |
| Role escalation via `owner_id` reassignment | Tampering | D-13: `owner_id` changes gated to `is_admin(user)` only |
| Bypass via deal child side-door | Elevation of Privilege | D-19: child services must call same authz guards as parent deal service |

---

## Plan Structure Recommendation

Given the scope of changes, three plans are appropriate:

**Plan 1 — Authz Module + List Scoping** (~4 tasks)
- Create `backend/auth/access.py` with all role-check and predicate functions
- Rewrite `accessible_team_ids` and `private_deal_predicate` in `_crm.py` to delegate
- Update `DealService._visible_team_ids()` and `_base_deal_stmt()` to use new module
- Write `backend/tests/test_access_enforcement.py` — list/visibility test matrix; extend `seeded_org` with principal

**Plan 2 — Action Guards + Deal CRUD** (~4 tasks)
- Update `DealService.get_deal()` to load-then-decide (403 vs 404)
- Update `DealService._get_deal_or_404()` (used by activities) to use `require_deal_readable`
- Update `DealService.update_deal()` — `can_write_deal` guard + D-13 admin-only `owner_id`
- Update `DealService.move_stage()` — same `can_write_deal` guard
- Update `DealService.delete_deal()` — `can_delete_deal` guard; already close but needs 403/404 fix
- Expand test coverage: GET/UPDATE/DELETE role × action matrix

**Plan 3 — Child Entity Guards + Frontend** (~3 tasks)
- Update `DealCounterpartyService` — replace `_get_deal_or_404` with `require_deal_readable/writable`
- Update `DealFundingService` — same
- Update `DealDetailPage.jsx` — `isError` branch checks `error.response?.status === 403`
- Expand test coverage: child entity cross-team access

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `seeded_org` fixture does not include a `principal` user | Wave 0 Gaps | Low — verified by reading conftest.py lines 172-196; no principal user found |
| A2 | `Deal.team_id` is always non-null (model uses `nullable=False`) | Don't Hand-Roll | Low — verified by reading `models.py` line 420 |
| A3 | `DealUpdate` schema does not currently include `team_id` as a patchable field | Code Examples | Medium — did not read schemas/deals.py; assumption is safe since `update_deal` has no `team_id` update logic |
| A4 | `accessible_team_ids` can safely be changed from async to async-with-no-await without breaking callers | Standard Stack | Low — function body is a pure return after the fix; callers `await` it, which is valid even for coroutines that return immediately |

**If A3 is wrong:** `DealUpdate` already has `team_id` — planner must add admin-only guard for it in `update_deal`.

---

## Open Questions (RESOLVED)

1. **Admin team_id override on create (D-12)**
   - RESOLVED: DealCreate/DealUpdate have NO team_id field (verified) — payload team_id is structurally ignored; admin override not needed this phase.
   - What we know: D-12 locks that non-admins always get creator.team_id forced. Admin "may override — planner's discretion."
   - What's unclear: Does `DealCreate` schema have a `team_id` field? (Not verified; schemas/deals.py not read.)
   - Recommendation: If planner adds admin create override, add `Optional[UUID] = None` to `DealCreate` and only honor it when `is_admin(user)`.

2. **Principal's team_id on create**
   - RESOLVED: No special case — Principal uses user.team_id like all other non-admin roles.
   - What we know: Principal creates deals, `team_id` should be set to `user.team_id` (same as regular users).
   - What's unclear: D-06 says Principal CRUD on own records only — but "own" means owner_id, not team scoping. So a Principal in team Alpha creating a deal assigns it to Alpha's group.
   - Recommendation: No special case needed; Principal uses `user.team_id` like everyone else.

3. **Supervisor creating a counterparty on a team member's deal**
   - RESOLVED: require_deal_writable (Plan 03 Task 1) covers this via can_write_deal same-team check — no issue.
   - What we know: Supervisor can write any same-team deal (D-08).
   - What's unclear: `require_deal_writable` uses `can_write_deal` — a supervisor on Alpha editing Alpha-rep's deal → `can_write_deal` returns True (same team). Child create proceeds. This is correct.
   - Recommendation: No open issue; the matrix resolves cleanly.

---

## Sources

### Primary (HIGH confidence)
- Direct code reading: `backend/services/_crm.py` — all helper functions, current broken implementation
- Direct code reading: `backend/services/deals.py` — all DealService methods, full logic
- Direct code reading: `backend/auth/security.py` — get_current_user, require_org_admin
- Direct code reading: `backend/models.py` — Deal.team_id (nullable=False confirmed), User.team_id (nullable), DealCounterparty/DealFunding structure, Contact/Company lack team_id
- Direct code reading: `backend/services/counterparties.py` — _get_deal_or_404 org-only scoping bug
- Direct code reading: `backend/services/funding.py` — same bug
- Direct code reading: `backend/tests/conftest.py` — fixture structure, missing principal user
- Direct code reading: `frontend/src/api/client.js` — interceptor handles 401 only
- Direct code reading: `frontend/src/pages/DealDetailPage.jsx` — generic isError message confirmed
- Planning documents: `18-CONTEXT.md`, `REQUIREMENTS.md`, `ROADMAP.md` (Phase 18 success criteria)

### Secondary (MEDIUM confidence)
- Phase 17 CONTEXT.md — role string values confirmed (`regular_user`, `supervisor`, `principal`, `admin`)

### Tertiary (LOW confidence)
- None — all critical claims verified by direct source code inspection

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all files read directly; no external packages
- Architecture (authz module design): HIGH — derived from decision matrix D-06..D-16 and existing code patterns
- Bug identification: HIGH — verified by reading actual code
- Test matrix: HIGH — derived from locked decisions D-01..D-13
- Frontend gap: HIGH — confirmed by reading client.js and DealDetailPage.jsx

**Research date:** 2026-06-29
**Valid until:** Stable (no fast-moving dependencies; pure Python logic)
