# Phase 18: Access Enforcement - Pattern Map

**Mapped:** 2026-06-29
**Files analyzed:** 10 (2 new, 8 modified)
**Analogs found:** 10 / 10

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/auth/access.py` | utility (authz) | request-response | `backend/auth/security.py` + `backend/services/_crm.py` | role-match (same pkg + same role-check style) |
| `backend/services/_crm.py` | utility | request-response | itself (lines 39-43, 151-155) | exact (rewrites two functions in-place) |
| `backend/services/deals.py` | service | CRUD | itself (existing DealService methods) | exact (modifies existing guards in-place) |
| `backend/services/counterparties.py` | service | CRUD | `backend/services/funding.py` | exact (mirror pattern; same `_get_deal_or_404` structure) |
| `backend/services/funding.py` | service | CRUD | `backend/services/counterparties.py` | exact (mirror pattern) |
| `backend/api/routes/deals.py` | route | request-response | itself | exact (no route changes; service call signatures unchanged) |
| `backend/api/routes/counterparties.py` | route | request-response | itself | exact (no route changes; service call signatures unchanged) |
| `backend/api/routes/funding.py` | route | request-response | itself | exact (no route changes; service call signatures unchanged) |
| `backend/tests/test_access_enforcement.py` | test | request-response | `backend/tests/test_authorship.py` | role-match (same async_client + seeded_org fixture pattern) |
| `frontend/src/pages/DealDetailPage.jsx` | component | request-response | itself (line 945) | exact (3-line patch to `isError` branch) |

---

## Pattern Assignments

### `backend/auth/access.py` (NEW — authz utility, request-response)

**Primary analog:** `backend/auth/security.py`
**Secondary analog:** `backend/services/_crm.py`

This file does not exist yet. It is the single source of truth for all role-check functions and async DB guards. Two analogs supply the patterns to copy from.

**Imports pattern** — copy module header from `backend/auth/security.py` lines 1-14:
```python
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
```

**Synchronous role-check pattern** — copy style from `backend/services/_crm.py` lines 112-117:
```python
def is_admin(user) -> bool:
    return getattr(user, "role", None) in ("admin",)

def is_manager_plus(user) -> bool:
    return getattr(user, "role", None) in ("supervisor", "admin")
```
New functions follow the same `getattr(user, "role", None) in (...)` tuple pattern:
```python
def is_principal(user) -> bool:
    return getattr(user, "role", None) == "principal"

def is_supervisor(user) -> bool:
    return getattr(user, "role", None) == "supervisor"

def is_oversight_role(user) -> bool:
    """Supervisor, Principal, or Admin — see private deals within their scope."""
    return getattr(user, "role", None) in ("supervisor", "principal", "admin")
```

**403 raise pattern** — copy from `backend/auth/security.py` lines 87-90 and `backend/services/_crm.py` lines 120-123:
```python
# security.py lines 87-90
async def require_org_admin(current_user=Depends(get_current_user)):
    if current_user.role not in ("admin",):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user

# _crm.py lines 120-123
def ensure_owner_or_admin(owner_id: UUID, user) -> None:
    from fastapi import HTTPException, status
    if not is_admin(user) and user.id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorised")
```

**Async DB load + 403/404 guard pattern** — copy structure from `backend/services/_crm.py` lines 54-61 (ensure_company_in_org):
```python
async def ensure_company_in_org(session: AsyncSession, company_id: UUID, org_id: UUID) -> None:
    from backend.models import Company
    from fastapi import HTTPException, status
    result = await session.execute(
        select(Company).where(Company.id == company_id, Company.org_id == org_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
```
The new `require_deal_readable` adds a two-step load (exist check → authz check) on top of this pattern:
```python
async def require_deal_readable(db: AsyncSession, deal_id: UUID, user) -> "Deal":
    from backend.models import Deal
    deal = await db.scalar(
        select(Deal).where(Deal.id == deal_id, Deal.org_id == user.org_id)
    )
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    if not can_read_deal(user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return deal
```

**`or_()` predicate composition pattern** — copy from `backend/services/_crm.py` lines 151-155:
```python
def private_deal_predicate(user, visible_team_ids=None):
    from sqlalchemy import or_
    from backend.models import Deal
    return or_(Deal.is_private == False, Deal.owner_id == user.id)  # noqa: E712
```
The new version adds the oversight-role gate before applying the filter (see RESEARCH.md Pattern 1 for full implementation).

---

### `backend/services/_crm.py` (MODIFIED — two function rewrites)

**Analog:** itself (current broken implementations)

**`accessible_team_ids` — current broken code** (`_crm.py` lines 39-43):
```python
async def accessible_team_ids(session: AsyncSession, user) -> list[UUID]:
    """Return team IDs visible to user — currently returns user's own team only."""
    if user.team_id:
        return [user.team_id]
    return []
```
Rewrite to delegate to `access.py`. Keep `async` and keep the `session` parameter for zero call-site disruption. Change return type to `list[UUID] | None` (None = no team filter):
```python
async def accessible_team_ids(session: AsyncSession, user) -> list[UUID] | None:
    from backend.auth.access import visible_deal_team_ids
    return visible_deal_team_ids(user)
```

**`private_deal_predicate` — current broken code** (`_crm.py` lines 151-155):
```python
def private_deal_predicate(user, visible_team_ids=None):
    from sqlalchemy import or_
    from backend.models import Deal
    return or_(Deal.is_private == False, Deal.owner_id == user.id)  # noqa: E712
```
Rewrite to delegate. Keep the `visible_team_ids` parameter for signature compatibility (it is unused but callers pass it):
```python
def private_deal_predicate(user, visible_team_ids=None):
    from backend.auth.access import private_deal_predicate as _authz_predicate
    return _authz_predicate(user)
```

**No other functions in `_crm.py` change.** `is_admin`, `is_manager_plus`, `ensure_owner_or_admin`, pagination helpers, etc. all remain as-is.

---

### `backend/services/deals.py` (MODIFIED — guard logic inside existing methods)

**Analog:** itself; route structure stays identical. All changes are surgical replacements inside service methods.

**Imports to add** at top of existing import block (lines 23-40). Add after current `_crm` imports:
```python
from backend.auth.access import (
    can_read_deal,
    can_write_deal,
    can_delete_deal,
    is_admin,
    require_deal_readable,
    visible_deal_team_ids,
)
```
Note: remove `is_manager_plus` from the `_crm` import line once the new guards replace it (or keep it for backward compat — planner's call).

**`_get_deal_or_404` — current broken code** (lines 229-241):
```python
async def _get_deal_or_404(self, deal_id: UUID) -> Deal:
    visible_team_ids = await self._visible_team_ids()
    stmt = select(Deal).where(Deal.id == deal_id, Deal.org_id == self.current_user.org_id)
    if visible_team_ids is not None:
        if not visible_team_ids:
            stmt = stmt.where(False)
        else:
            stmt = stmt.where(Deal.team_id.in_(visible_team_ids))
    stmt = stmt.where(private_deal_predicate(self.current_user, visible_team_ids))
    deal = await self.db.scalar(stmt)
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return deal
```
Replace body with a single call to `require_deal_readable` (import from `access.py`):
```python
async def _get_deal_or_404(self, deal_id: UUID) -> Deal:
    return await require_deal_readable(self.db, deal_id, self.current_user)
```

**`get_deal` — current broken code** (lines 316-323):
```python
async def get_deal(self, deal_id: UUID) -> DealResponse:
    visible_team_ids = await self._visible_team_ids()
    stmt = self._base_deal_stmt(visible_team_ids).where(Deal.id == deal_id)
    row = (await self.db.execute(stmt)).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    deal_team = await self._load_deal_team(deal_id)
    return self._deal_response(row, deal_team=deal_team)
```
Replace with load-then-decide pattern (existence check first, then full join for response):
```python
async def get_deal(self, deal_id: UUID) -> DealResponse:
    # Step 1: existence check + authz (raises 404 or 403)
    await require_deal_readable(self.db, deal_id, self.current_user)
    # Step 2: full join query for response (deal is confirmed readable)
    visible_team_ids = await self._visible_team_ids()
    stmt = self._base_deal_stmt(visible_team_ids).where(Deal.id == deal_id)
    row = (await self.db.execute(stmt)).first()
    deal_team = await self._load_deal_team(deal_id)
    return self._deal_response(row, deal_team=deal_team)
```

**`update_deal` — current broken guard** (lines 380-387):
```python
async def update_deal(self, deal_id: UUID, data: DealUpdate) -> DealResponse:
    deal = await self.db.scalar(select(Deal).where(Deal.id == deal_id, Deal.org_id == self.current_user.org_id))
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    if not (deal.owner_id == self.current_user.id or is_manager_plus(self.current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if data.owner_id is not None and not is_manager_plus(self.current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
```
Replace load + guards at top of method:
```python
async def update_deal(self, deal_id: UUID, data: DealUpdate) -> DealResponse:
    deal = await require_deal_readable(self.db, deal_id, self.current_user)  # 404/403
    if not can_write_deal(self.current_user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    if data.owner_id is not None and not is_admin(self.current_user):   # D-13: admin-only
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    # ... rest of update logic unchanged from line 388 onward ...
```

**`move_stage` — current broken guard** (lines 438-443):
```python
async def move_stage(self, deal_id: UUID, data: DealMoveStage) -> DealResponse:
    deal = await self.db.scalar(select(Deal).where(Deal.id == deal_id, Deal.org_id == self.current_user.org_id))
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    if not (deal.owner_id == self.current_user.id or is_manager_plus(self.current_user)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
```
Replace:
```python
async def move_stage(self, deal_id: UUID, data: DealMoveStage) -> DealResponse:
    deal = await require_deal_readable(self.db, deal_id, self.current_user)  # 404/403
    if not can_write_deal(self.current_user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    # ... rest of move_stage unchanged from old_stage lookup onward ...
```

**`delete_deal` — correct permission logic, wrong 404/403 split** (lines 530-537):
```python
async def delete_deal(self, deal_id: UUID) -> None:
    deal = await self.db.scalar(select(Deal).where(Deal.id == deal_id, Deal.org_id == self.current_user.org_id))
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    if not (is_admin(self.current_user) or deal.owner_id == self.current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    await self.db.delete(deal)
    await self.db.commit()
```
Replace load with `require_deal_readable` (keeps the 404/403 split); permission check uses `can_delete_deal` (which encodes the same `is_admin OR owner` logic):
```python
async def delete_deal(self, deal_id: UUID) -> None:
    deal = await require_deal_readable(self.db, deal_id, self.current_user)  # 404/403
    if not can_delete_deal(self.current_user, deal):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    await self.db.delete(deal)
    await self.db.commit()
```

**`_visible_team_ids` / `_base_deal_stmt`** — these are already structurally correct. They will work correctly once `accessible_team_ids` and `private_deal_predicate` in `_crm.py` are fixed. No structural change needed to `_base_deal_stmt` itself.

---

### `backend/services/counterparties.py` (MODIFIED — `_get_deal_or_404` replacement)

**Analog:** itself (current `_get_deal_or_404` at lines 81-91) + `backend/services/funding.py` (mirror)

**Current `_get_deal_or_404`** (lines 81-91):
```python
async def _get_deal_or_404(self, deal_id: UUID) -> Deal:
    result = await self.db.execute(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.org_id == self.current_user.org_id,
        )
    )
    deal = result.scalar_one_or_none()
    if deal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
    return deal
```

**All callers and the guard pattern to copy:**

`list_for_deal` (line 99) calls `self._base_stmt(deal_id)` directly — currently no deal gate; add read gate:
```python
async def list_for_deal(self, deal_id: UUID, page: int = 1, size: int = 50):
    await require_deal_readable(self.db, deal_id, self.current_user)  # 403/404 gate
    page, size = clamp_pagination(page, size)
    # ... rest unchanged ...
```

`create` (line 118-119) calls `await self._get_deal_or_404(deal_id)` — replace:
```python
async def create(self, deal_id: UUID, data: DealCounterpartyCreate):
    await require_deal_writable(self.db, deal_id, self.current_user)  # write gate
    # ... rest unchanged ...
```

`update` (lines 137-152) does not call `_get_deal_or_404` — add write gate at top:
```python
async def update(self, deal_id: UUID, counterparty_id: UUID, data: DealCounterpartyUpdate):
    await require_deal_writable(self.db, deal_id, self.current_user)  # write gate
    # ... existing select(DealCounterparty) logic unchanged ...
```

`delete` (lines 164-176) does not call `_get_deal_or_404` — add write gate at top:
```python
async def delete(self, deal_id: UUID, counterparty_id: UUID):
    await require_deal_writable(self.db, deal_id, self.current_user)  # write gate
    # ... existing select(DealCounterparty) logic unchanged ...
```

**Imports to add** (after existing `_crm` import at line 17):
```python
from backend.auth.access import require_deal_readable, require_deal_writable
```
Remove `Deal` from the `_get_deal_or_404` use — keep it in the model import since `_base_stmt` still selects from it.

---

### `backend/services/funding.py` (MODIFIED — identical pattern to counterparties.py)

**Analog:** `backend/services/counterparties.py` (exact mirror)

**Current `_get_deal_or_404`** (lines 29-37):
```python
async def _get_deal_or_404(self, deal_id: UUID) -> Deal:
    deal = await self.db.scalar(
        select(Deal).where(
            Deal.id == deal_id,
            Deal.org_id == self.current_user.org_id,
        )
    )
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal
```

Apply the identical replacement pattern as counterparties.py:

- `list_for_deal` (line 85): `await self._get_deal_or_404(deal_id)` → `await require_deal_readable(self.db, deal_id, self.current_user)`
- `create` (line 111): `await self._get_deal_or_404(deal_id)` → `await require_deal_writable(self.db, deal_id, self.current_user)`
- `update` (line 133): `await self._get_deal_or_404(deal_id)` → `await require_deal_writable(self.db, deal_id, self.current_user)`
- `delete` (line 155): `await self._get_deal_or_404(deal_id)` → `await require_deal_writable(self.db, deal_id, self.current_user)`

**Imports to add** (after line 18 — after existing service imports):
```python
from backend.auth.access import require_deal_readable, require_deal_writable
```

---

### `backend/api/routes/deals.py` (NO CODE CHANGES)

Routes are thin pass-throughs (confirmed by reading lines 1-147). All route handlers follow this pattern:
```python
@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DealResponse:
    return await DealService(db, current_user).get_deal(deal_id)
```
No changes needed. Enforcement is entirely in `DealService`.

---

### `backend/api/routes/counterparties.py` (NO CODE CHANGES)

Same thin-route pattern as deals.py. No changes needed.

---

### `backend/api/routes/funding.py` (NO CODE CHANGES)

Same thin-route pattern. No changes needed.

---

### `backend/tests/test_access_enforcement.py` (NEW — integration test file)

**Analog:** `backend/tests/test_authorship.py` (closest role match: same async_client + seeded_org fixture + status code assertions)
**Secondary analog:** `backend/tests/test_admin_groups.py` (403 assertion pattern for role-based endpoint tests)

**File header pattern** — copy from `test_authorship.py` lines 1-15:
```python
"""
Integration tests for access enforcement (Phase 18).

Covers ACCESS-01 through ACCESS-07: group-scoped deal visibility,
role × action matrix, 403-not-404 semantics, child entity inheritance.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import select

from backend.models import Deal, DealCounterparty
from backend.tests.conftest import auth_header
```

**Test function pattern** — copy from `test_authorship.py` lines 17-33 (pytest.mark.asyncio + async_client + assert on status_code):
```python
@pytest.mark.asyncio
async def test_cross_team_deal_get_returns_403(async_client, seeded_org, pipeline, stages):
    """GET /api/v1/deals/{id} with user from different team returns 403, not 404."""
    # Create a deal owned by alpha-rep
    alpha_rep = seeded_org["alpha-rep"]
    alpha_headers = auth_header(alpha_rep)
    create_resp = await async_client.post(
        "/api/v1/deals",
        headers=alpha_headers,
        json={"name": "Alpha Deal", "pipeline_id": str(pipeline.id), "stage_id": str(stages[0].id)},
    )
    assert create_resp.status_code == 201
    deal_id = create_resp.json()["id"]

    # beta-rep cannot see alpha's deal — must get 403, not 404
    beta_rep = seeded_org["beta-rep"]
    resp = await async_client.get(f"/api/v1/deals/{deal_id}", headers=auth_header(beta_rep))
    assert resp.status_code == 403
```

**403 assertion style** — copy from `test_admin_groups.py` line 71:
```python
assert response.status_code == 403
```

**`seeded_org` fixture extension** — add `principal` user to `conftest.py` `seeded_org` fixture at line 177-180 (inside the users loop):
```python
# Add after existing user tuples, before the closing bracket of the list:
("principal@example.com", "principal", "principal", alpha),
```
This adds `seeded_org["principal"]` for ACCESS-05 test cases.

**Deal fixture pattern for cross-team tests** — copy from `conftest.py` `seed_50_deals` (lines 281-298); create a simpler per-test fixture:
```python
@pytest_asyncio.fixture
async def deal_fixtures(db_session, seeded_org, pipeline, stages):
    """Creates one alpha-team deal and one beta-team deal for matrix tests."""
    alpha_deal = Deal(
        org_id=seeded_org["org"].id,
        team_id=seeded_org["alpha"].id,
        pipeline_id=pipeline.id,
        stage_id=stages[0].id,
        name="Alpha Deal",
        value=1000,
        probability=25,
        status="open",
        owner_id=seeded_org["alpha-rep"].id,
    )
    beta_deal = Deal(
        org_id=seeded_org["org"].id,
        team_id=seeded_org["beta"].id,
        pipeline_id=pipeline.id,
        stage_id=stages[0].id,
        name="Beta Deal",
        value=2000,
        probability=25,
        status="open",
        owner_id=seeded_org["beta-rep"].id,
    )
    db_session.add_all([alpha_deal, beta_deal])
    await db_session.commit()
    return {"alpha_deal": alpha_deal, "beta_deal": beta_deal}
```

---

### `frontend/src/pages/DealDetailPage.jsx` (MODIFIED — 3-line patch)

**Analog:** itself (line 945 — the `isError` branch)

**Current code** (lines 944-948):
```javascript
// ---- Error state ----
if (dealQuery.isError) {
  return (
    <div className="p-6 text-center text-muted-foreground">
      Could not load deal. It may have been removed.
```

**Replace** the `isError` branch body to distinguish 403 from 404:
```javascript
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
Note: mutation `onError` handlers elsewhere in `DealDetailPage.jsx` already use `e.response?.data?.detail` — that pattern is correct and does not change.

---

## Shared Patterns

### 403 / 404 Raising
**Source:** `backend/auth/security.py` lines 87-90 + `backend/services/_crm.py` lines 120-123
**Apply to:** `access.py` (all guard functions), `deals.py` (all service methods), `counterparties.py`, `funding.py`
```python
# Standard 403 raise (used in require_org_admin and ensure_owner_or_admin):
raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
# Standard 404 raise (used in ensure_company_in_org):
raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found")
```
Always import `status` from `fastapi` (not hardcode integer literals) — `funding.py` uses raw `404` (line 37); fix these to `status.HTTP_404_NOT_FOUND` for consistency.

### Service Constructor
**Source:** `backend/services/deals.py` lines 52-54
**Apply to:** `counterparties.py`, `funding.py` (already follow this pattern — keep it)
```python
class DealService:
    def __init__(self, db: AsyncSession, current_user: User) -> None:
        self.db = db
        self.current_user = current_user
```
The `current_user` is already threaded into every service — `access.py` guard functions consume `user` directly.

### Role Check Style
**Source:** `backend/services/_crm.py` lines 112-117
**Apply to:** All new role-check functions in `access.py`
```python
# Pattern: getattr with fallback + in() tuple check
def is_admin(user) -> bool:
    return getattr(user, "role", None) in ("admin",)
```

### Async Test Structure
**Source:** `backend/tests/test_authorship.py` lines 17-33
**Apply to:** `test_access_enforcement.py` (all test functions)
```python
@pytest.mark.asyncio
async def test_<name>(async_client, seeded_org, pipeline, stages):
    """Docstring describing the requirement being tested."""
    user = seeded_org["<username>"]
    response = await async_client.<method>("/api/v1/...", headers=auth_header(user), json={...})
    assert response.status_code == <expected>
```

### `from __future__ import annotations`
**Source:** All backend Python files (e.g., `deals.py` line 1, `_crm.py` line 1, `security.py` line 1)
**Apply to:** `access.py` (new file must include this as its first line)

---

## No Analog Found

All files have close analogs. No entries in this section.

---

## Metadata

**Analog search scope:** `backend/auth/`, `backend/services/`, `backend/api/routes/`, `backend/tests/`, `frontend/src/pages/`
**Files read:** 10 source files + conftest.py
**Pattern extraction date:** 2026-06-29

**Key observations for planner:**

1. The three route files (`deals.py`, `counterparties.py`, `funding.py`) require **zero route-level changes** — all enforcement is in the service layer. Do not add route tasks for them.

2. `funding.py` uses raw integer `404` in `_get_deal_or_404` (line 37) instead of `status.HTTP_404_NOT_FOUND`. Fix this as part of the guard replacement to keep the codebase consistent.

3. `DealCounterpartyService.update` and `DealCounterpartyService.delete` (lines 137, 164) currently do NOT call `_get_deal_or_404` at all — they query the child record directly. The write gate must be added to these methods explicitly.

4. `DealFundingService.update` (line 133) calls `await self._get_deal_or_404(deal_id)` first — the replacement is a one-line swap.

5. `seeded_org` in `conftest.py` does not have a `principal` user (confirmed by reading lines 172-196). The test file (or a conftest update) must add one before any ACCESS-05 test can run. This is the Wave 0 gap from RESEARCH.md.

6. `backend/auth/access.py` does not exist yet — the `backend/auth/` directory exists (`__init__.py`, `schemas.py`, `security.py` confirmed by glob). The new file drops in cleanly with no `__init__.py` changes needed (Python will find it via the existing package).
