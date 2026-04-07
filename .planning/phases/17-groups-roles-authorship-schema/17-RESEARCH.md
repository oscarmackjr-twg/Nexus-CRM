# Phase 17: Groups, Roles & Authorship Schema - Research

**Researched:** 2026-04-06
**Domain:** FastAPI/SQLAlchemy RBAC migration, Alembic data migrations, React admin UI (TanStack Query + shadcn/ui)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Group Model — Reuse Team table**
- D-01: Do NOT create a new `groups` table. Repurpose the existing `teams` table as the Group concept.
- D-02: `User.team_id` is the group membership FK — enforce "exactly one group" at application layer (moving a user to a new group clears their previous `team_id`). No DB constraint needed.
- D-03: `Deal.team_id` already exists and already scopes deals to a group — no schema change needed for deals. Phase 18 enforcement will read this column directly.
- D-04: The Team model's hierarchical fields (`parent_team_id`, `sub_teams`) remain in the schema but are unused by the Group concept — do not remove them, do not expose them in Group admin UI.

**Role Migration — In-place rename via Alembic**
- D-05: Rename existing role string values in-place via Alembic data migration:
  - `super_admin` → `admin`
  - `org_admin` → `admin`
  - `team_manager` → `supervisor`
  - `rep` (or `member`) → `regular_user`
  - New value `principal` is additive — no existing rows map to it
- D-06: Update ALL existing route guards in `backend/auth/security.py` and all routes that call `require_role()` or `require_org_admin` to use the new role strings in this phase.
- D-07: The `require_org_admin` dependency should be updated or replaced to check for `admin` role.

**Authorship Fields — Nullable, no backfill**
- D-08: Add `created_by` (UUID FK → users.id), `created_at` (timestamp), `updated_by` (UUID FK → users.id, nullable), `updated_at` (timestamp) to all entities that lack them.
  - Entities already covered (skip): Pipeline, Board, Task, Page, Automation
  - Entities needing new columns: Contact, Company, Deal, Fund, DealCounterparty, DealFunding
- D-09: New columns are `NULLABLE`. Existing rows get `NULL` — no backfill. `NULL` means "created before authorship tracking."
- D-10: `created_by` and `created_at` are set on INSERT and never updated. `updated_by` and `updated_at` are set on every write operation.
- D-11: Entities that already have `created_by` as non-nullable (Pipeline, Board, Task, Page, Automation) are left unchanged.

**Admin UI — Separate sub-routes**
- D-12: User Management and Group Management land as dedicated pages at `/admin/users` and `/admin/groups`, NOT as tabs inside the existing `AdminPage.jsx`.
- D-13: Add nav entries for "Users" and "Groups" under the existing ADMIN section in the sidebar (`Layout.jsx`).
- D-14: The existing `/admin` route (Reference Data) remains unchanged. The existing Users tab inside `AdminPage.jsx` may be left as-is or removed if superseded — planner's call.
- D-15: User Management page (`/admin/users`): list all users with their group and effective role visible; support adding new users, editing role/group assignment.
- D-16: Group Management page (`/admin/groups`): list groups with member count; support create group, rename group, view and reassign members.
- D-17: This page structure sets the pattern for Phase 20 and Phase 21 — each will be its own sub-route under `/admin/`.

### Claude's Discretion
- Exact form/modal design for user and group edit flows
- Whether role dropdown on user edit shows friendly labels ("Supervisor") or raw values
- Pagination strategy for user and group lists
- Loading skeleton and error state handling in new admin pages

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope. Access enforcement (403 rules) is Phase 18. Row-level security at DB layer is explicitly out of scope per REQUIREMENTS.md.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GROUP-01 | Admin can create, rename, and deactivate groups | Backend: new `/admin/groups` CRUD routes; Frontend: GroupsAdminPage with create + rename dialog, deactivate action; requires `is_active` column added to `teams` table |
| GROUP-02 | Admin can assign any user to exactly one group | Backend: PUT `/admin/users/{id}` updates `team_id`, clears previous; Frontend: group dropdown in user edit modal |
| GROUP-03 | Admin can grant Supervisor role within a group | Backend: role update in user PATCH; Frontend: role dropdown in user edit modal includes `supervisor` |
| GROUP-04 | Admin can grant Principal role | Backend: role update in user PATCH; Frontend: role dropdown includes `principal` |
| GROUP-05 | Admin can grant Admin role | Backend: role update in user PATCH; Frontend: role dropdown includes `admin` |
| GROUP-06 | Effective role visible in profile and admin user list | Frontend: UserResponse must include `team_id`/group name; role shown with friendly label in both `/admin/users` and `/auth/me` response |
| AUDIT-01 | created_by + created_at on all objects, set on INSERT | Alembic migration adds nullable columns; service layer sets on INSERT via `Depends(get_current_user)` |
| AUDIT-02 | updated_by + updated_at on all objects, set on every write | Same migration; service layer sets on UPDATE |
| ADMIN-10 | Admin User Management screen | New `/admin/users` React page + backend routes |
| ADMIN-11 | Admin Group Management screen | New `/admin/groups` React page + backend routes |
</phase_requirements>

---

## Summary

Phase 17 is a schema + admin UI foundation phase with three parallel work streams: (1) Role string migration via Alembic data migration and guard updates, (2) Authorship column additions across six entities, and (3) two new React admin pages backed by new FastAPI routes.

The existing codebase provides a clear template for every piece of work. The `teams` table is already present and fully relational; no DDL changes are needed to the groups concept beyond adding an `is_active` boolean (required for GROUP-01 deactivate). The `require_role` / `require_org_admin` pattern in `backend/api/dependencies.py` and `backend/auth/security.py` needs role-string updates at ~8 callsites. Authorship column additions are purely additive nullable columns following the established `Pipeline.created_by` (non-nullable) pattern but with nullable variants. The frontend already imports `DataGrid`, `Dialog`, shadcn/ui `Table` and TanStack Query — new admin pages are composition of existing components.

The two highest-risk areas are: (a) the role data migration — the seed data creates users with `org_admin` and `rep` roles; all tests use `super_admin` / `org_admin` / `team_manager` / `rep` role strings, so tests must be updated at the same time as the migration; (b) the `is_active` deactivation for groups requires a `teams` schema column addition and the backend query for the Group list must filter on it correctly.

**Primary recommendation:** Execute in three sequential waves — Wave 1: Alembic migration (role rename + authorship columns + `teams.is_active`), Wave 2: Backend service/route/guard updates, Wave 3: Frontend admin pages. This ordering prevents frontend changes from running against stale role strings.

---

## Standard Stack

### Core (already in project — no new installs)

| Layer | Component | Version | Purpose |
|-------|-----------|---------|---------|
| ORM | SQLAlchemy 2.0 | Mapped columns | Model definitions and relationships |
| Migrations | Alembic | 1.x | DDL + data migrations |
| API | FastAPI | 0.x | Route definitions, dependency injection |
| Auth | `backend/api/dependencies.py` | project | `require_role()`, `get_current_user` |
| Frontend | TanStack Query | v5 | Server state, mutations, cache invalidation |
| Frontend | shadcn/ui | project | Dialog, Table, Button, Input, Label, Select |
| Frontend | `DataGrid.jsx` | project | Paginated table component |
| Frontend | `Pagination.jsx` | project | Page controls |
| Frontend | React Router | v6 | Sub-route registration in `main.jsx` |

### No New Dependencies Required
All tooling for this phase exists in the project. No `npm install` or `pip install` steps needed.

---

## Architecture Patterns

### Recommended Project Structure (new files only)

```
backend/
├── api/routes/
│   ├── admin_users.py      # GET/POST /admin/users, PUT/PATCH /admin/users/{id}
│   └── admin_groups.py     # GET/POST /admin/groups, PATCH /admin/groups/{id}
├── schemas/
│   ├── admin_users.py      # AdminUserResponse, AdminUserUpdate, AdminUserCreate
│   └── admin_groups.py     # GroupResponse, GroupCreate, GroupUpdate
└── services/
│   └── admin.py            # AdminUserService, AdminGroupService (optional — may inline in routes)
alembic/versions/
└── 0012_v13_groups_roles_authorship.py   # All DDL + data changes for Phase 17

frontend/src/
├── pages/
│   ├── AdminUsersPage.jsx   # /admin/users
│   └── AdminGroupsPage.jsx  # /admin/groups
└── api/
    ├── adminUsers.js        # API client functions for /admin/users
    └── adminGroups.js       # API client functions for /admin/groups
```

### Pattern 1: Alembic Data Migration (role rename)

The migration must use explicit `op.execute()` SQL UPDATE statements. Do NOT use `op.alter_column()` — that changes DDL, not row values. The column stays `String(20)`.

```python
# Source: established pattern from alembic/versions/0001_initial.py + Alembic docs
def upgrade() -> None:
    # 1. Add is_active to teams
    op.add_column("teams", sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"))

    # 2. Add authorship columns to Contact, Company, Deal, Fund, DealCounterparty, DealFunding
    for table in ("contacts", "companies", "deals", "funds", "deal_counterparties", "deal_funding"):
        op.add_column(table, sa.Column("created_by", postgresql.UUID(as_uuid=True),
                                       sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
        op.add_column(table, sa.Column("updated_by", postgresql.UUID(as_uuid=True),
                                       sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True))
    # Note: created_at and updated_at already exist on Contact, Company, Deal
    # Fund only has created_at — add updated_at
    # DealCounterparty and DealFunding already have created_at + updated_at

    # 3. Data migration: rename role values
    op.execute("UPDATE users SET role = 'admin' WHERE role IN ('super_admin', 'org_admin')")
    op.execute("UPDATE users SET role = 'supervisor' WHERE role = 'team_manager'")
    op.execute("UPDATE users SET role = 'regular_user' WHERE role IN ('rep', 'member')")

def downgrade() -> None:
    op.execute("UPDATE users SET role = 'org_admin' WHERE role = 'admin'")
    op.execute("UPDATE users SET role = 'team_manager' WHERE role = 'supervisor'")
    op.execute("UPDATE users SET role = 'rep' WHERE role = 'regular_user'")
    # Remove authorship columns
    ...
```

**CRITICAL authorship columns audit:**
- `Contact`: has `created_at`, `updated_at` — needs `created_by`, `updated_by` only
- `Company`: has `created_at`, `updated_at` — needs `created_by`, `updated_by` only
- `Deal`: has `created_at`, `updated_at` — needs `created_by`, `updated_by` only
- `Fund`: has `created_at` — needs `created_by`, `updated_by`, `updated_at`
- `DealCounterparty`: has `created_at`, `updated_at` — needs `created_by`, `updated_by` only
- `DealFunding`: has `created_at`, `updated_at` — needs `created_by`, `updated_by` only

### Pattern 2: SQLite compatibility for UUID columns in migration

The test suite runs against SQLite (see `conftest.py`: `DATABASE_URL = "sqlite+aiosqlite:///./test_nexus.db"`). The migration cannot use `postgresql.UUID` directly — it must use `sa.types.Uuid()` or a dialect-conditional approach. The established pattern in the codebase (see `models.py` line 9-10) is `from sqlalchemy.types import Uuid` with `Uuid()` type which handles both SQLite and PostgreSQL.

```python
# Correct for SQLite+PostgreSQL compat in Alembic migration:
from sqlalchemy.types import Uuid as SaUuid

op.add_column("contacts", sa.Column("created_by", SaUuid(), nullable=True))
```

Do NOT use `postgresql.UUID(as_uuid=True)` in new Phase 17 columns because tests use SQLite. Check existing `0010_deal_counterparties.py` and `0011_deal_funding.py` to see whether they used `postgresql.UUID` — if they did and tests still pass, it may be that FK columns are excluded from test validation. Verify before writing the migration.

### Pattern 3: Backend route guards — update require_role callsites

**Files with old role strings to update (confirmed by grep):**

| File | Line(s) | Old value | New value |
|------|---------|-----------|-----------|
| `backend/auth/security.py` | 88 | `"admin", "owner"` in `require_org_admin` | `"admin"` |
| `backend/api/routes/admin.py` | 31, 43 | `require_role("org_admin", "super_admin")` | `require_role("admin")` |
| `backend/api/routes/auth.py` | 132 | `actor.role != "super_admin"` in `_ensure_same_org` | `actor.role != "admin"` |
| `backend/api/routes/auth.py` | 170 | `role = "org_admin"` (register new org) | `role = "admin"` |
| `backend/api/routes/auth.py` | 296 | `Depends(require_org_admin)` create_user | `Depends(require_role("admin"))` |
| `backend/api/routes/auth.py` | 331 | `{"super_admin", "org_admin"}` is_admin check | `{"admin"}` |
| `backend/api/routes/auth.py` | 371 | `Depends(require_org_admin)` deactivate_user | `Depends(require_role("admin"))` |
| `backend/services/_crm.py` | 113, 117 | `"org_admin", "super_admin"` | `"admin"` |
| `frontend/src/pages/AdminPage.jsx` | 29, 66 | `'org_admin', 'super_admin'` role checks | `'admin'` |

### Pattern 4: Authorship injection in service layer

The established pattern (Board, Pipeline, Task) injects `created_by` via `Depends(get_current_user)`. For the six target entities, adopt the same pattern on create operations:

```python
# Source: backend/models.py Pipeline model + existing route patterns
# On INSERT:
entity = Contact(
    ...
    created_by=current_user.id,   # new nullable FK
    # created_at is set by server_default=func.now()
    updated_by=current_user.id,   # new nullable FK
    # updated_at is set by server_default=func.now()
)

# On UPDATE (service layer patch):
entity.updated_by = current_user.id
# updated_at is set by onupdate=func.now() on the ORM column
```

**Important:** `updated_at` on `Contact`, `Company`, `Deal`, `DealCounterparty`, `DealFunding` already has `onupdate=func.now()` in the ORM. Only `Fund` lacks `updated_at` entirely — it needs both the column added in migration AND the ORM mapped column updated.

### Pattern 5: New Admin Routes

Follow the `backend/api/routes/admin.py` pattern exactly. New routes live in separate files to avoid cluttering the existing admin.py.

```python
# backend/api/routes/admin_groups.py
router = APIRouter(prefix="/admin/groups", tags=["admin"])

@router.get("/", response_model=list[GroupResponse])
async def list_groups(
    include_inactive: bool = False,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> list[GroupResponse]: ...

@router.post("/", response_model=GroupResponse, status_code=201)
async def create_group(...): ...

@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(...): ...  # rename and/or deactivate
```

Group list response must include `member_count`. Use a subquery or joined aggregate:
```python
# SQLAlchemy 2.0 pattern for member count
from sqlalchemy import func, select, outerjoin
stmt = (
    select(Team, func.count(User.id).label("member_count"))
    .outerjoin(User, User.team_id == Team.id)
    .where(Team.org_id == current_user.org_id)
    .group_by(Team.id)
)
```

### Pattern 6: Frontend Admin Pages

Both new pages follow the same composition as `AdminPage.jsx`:

```jsx
// Pattern: AdminUsersPage.jsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataGrid } from '@/components/DataGrid';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAuth } from '@/hooks/useAuth';

export default function AdminUsersPage() {
  const { user } = useAuth();
  // Gate: redirect or show error if user.role !== 'admin'

  const usersQuery = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminUsersApi.list(),
    enabled: user?.role === 'admin',
  });
  // ... modal state, mutation, DataGrid render
}
```

**Route registration** in `main.jsx` — add two new `<Route>` entries under the Layout route:
```jsx
<Route path="admin/users" element={<AdminUsersPage />} />
<Route path="admin/groups" element={<AdminGroupsPage />} />
```

**Sidebar** — add to `Layout.jsx` navGroups ADMIN section:
```js
{ name: 'Users', href: '/admin/users', icon: Users },
{ name: 'Groups', href: '/admin/groups', icon: UsersRound },
```

### Anti-Patterns to Avoid

- **Using `op.alter_column()` for the role rename:** This changes DDL (column type/constraint), not row data. Use `op.execute("UPDATE users SET role = ...")`
- **PostgreSQL-specific migration types:** `postgresql.UUID(as_uuid=True)` in FK column additions will break SQLite tests. Use `sa.types.Uuid()`.
- **Double-setting `updated_at` manually:** For Contact/Company/Deal/DealCounterparty/DealFunding the ORM `onupdate=func.now()` handles `updated_at` automatically. Only `updated_by` needs manual injection. Do not set `updated_at` explicitly in service code — it will cause a conflict with the ORM trigger.
- **Not updating tests:** The `conftest.py` `seeded_org` fixture creates users with `super_admin`, `org_admin`, `team_manager`, `rep`, `viewer` role strings. After the migration, running tests against a fresh DB will fail if the fixture still creates old role strings. The fixture must be updated to use `admin`, `supervisor`, `regular_user` in the same PR as the migration.
- **Leaving `AdminPage.jsx` role check stale:** Line 29 and 66 check `['org_admin', 'super_admin'].includes(user?.role)` — this will block all admins from the existing reference data page after the migration. Update it to `user?.role === 'admin'`.
- **Missing `is_active` on Team for GROUP-01:** The existing `Team` model has no `is_active` column. GROUP-01 requires deactivation support. This column must be added in the migration.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Member count per group | Custom aggregation loop | SQLAlchemy `func.count` + `outerjoin` + `group_by` | One query, no N+1 |
| Role-gating new admin pages | Custom middleware | `require_role("admin")` dependency (already exists in `dependencies.py`) | Consistent with all other routes |
| Modal form for create/edit | Custom modal | shadcn/ui `Dialog` (already used in AdminPage.jsx) | Consistent UX, already imported |
| Pagination on user/group lists | Custom page logic | `DataGrid` + `Pagination` components (already exist) | Established pattern |
| Friendly role labels in UI | Custom role formatter | Inline `ROLE_LABELS` constant object | Simple 4-entry lookup, no library needed |

**Key insight:** Every UI primitive and backend pattern needed for this phase already exists in the codebase. This phase is composition and data migration, not novel construction.

---

## Runtime State Inventory

> This phase involves in-place role rename — a data migration. Runtime state audit is required.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data (DB) | `users.role` column: seed data creates 1 user with `org_admin`; tests create `super_admin`, `org_admin`, `team_manager`, `rep`, `viewer` | Alembic data migration (UPDATE statements in upgrade()); test fixture update |
| Live service config | None identified — no external services store role strings | None |
| OS-registered state | None — no cron/task scheduler entries reference role strings | None |
| Secrets/env vars | None — role strings are DB values, not env vars | None |
| Build artifacts | `backend/tests/conftest.py` `seeded_org` fixture hardcodes old role strings — not a build artifact but will cause test failures if not updated | Code edit: update fixture role strings to new values |

**The canonical question answered:** After all files are updated, the only remaining "old string" is in any database that was seeded before the migration runs. The Alembic migration's `op.execute` UPDATE statements handle that at migration time.

---

## Common Pitfalls

### Pitfall 1: SQLite UUID FK in Alembic migration
**What goes wrong:** Using `postgresql.UUID(as_uuid=True)` in `op.add_column()` for the new `created_by`/`updated_by` FK columns causes `OperationalError` when pytest runs against SQLite.
**Why it happens:** `postgresql.UUID` is dialect-specific and SQLite does not support it. The existing 0001_initial.py migration uses `postgresql.UUID` throughout, but those columns were created before the SQLite test infrastructure was set up; tests work because the test DB is re-created from `Base.metadata.create_all()` which uses the ORM's `Uuid()` type.
**How to avoid:** Use `sa.types.Uuid()` (SQLAlchemy's cross-dialect UUID type) in any new column additions in the migration. Verify by running `pytest backend/tests/` after writing the migration.
**Warning signs:** `OperationalError: no such column` or `OperationalError: table "X" has no column named "created_by"` in test output.

### Pitfall 2: Test fixture role strings not updated
**What goes wrong:** Tests for ref_data, deals, funds use `org_admin` and `super_admin` role strings in the `seeded_org` fixture. After the migration, a fresh test DB will have users with old role strings inserted by the fixture, and route guards checking for `"admin"` will reject them.
**Why it happens:** The fixture bypasses the migration — it directly inserts `User` objects. It does not run the Alembic data migration.
**How to avoid:** In the same plan that updates route guards (Wave 2), update `conftest.py` `seeded_org` fixture role strings. Map: `super_admin`→`admin`, `org_admin`→`admin`, `team_manager`→`supervisor`, `rep`→`regular_user`. The `viewer` role has no mapping — decide whether to keep it or rename it to `regular_user`.
**Warning signs:** `403 Forbidden` errors in test assertions that previously expected `200`/`201`.

### Pitfall 3: `updated_at` double-set conflict
**What goes wrong:** If service code explicitly sets `entity.updated_at = datetime.utcnow()` in addition to the ORM `onupdate=func.now()`, SQLAlchemy may emit the column twice in the UPDATE statement, causing unexpected behavior or stale timestamps.
**Why it happens:** Contact, Company, Deal, DealCounterparty, DealFunding already have `updated_at` with `onupdate=func.now()`. Only `Fund` lacks `updated_at`.
**How to avoid:** Only set `entity.updated_by = current_user.id` in service code. Let the ORM `onupdate` handle `updated_at`. For `Fund`, add both the ORM mapped column (`onupdate=func.now()`) and the migration column.
**Warning signs:** `updated_at` not updating, or SQLAlchemy warning about duplicate column assignment.

### Pitfall 4: `is_active` filter missing on Group list
**What goes wrong:** The Group Management page shows deactivated groups in the main list, violating GROUP-01's "disappears from active views."
**Why it happens:** The default query fetches all teams with no filter.
**How to avoid:** Backend `/admin/groups` list endpoint defaults `include_inactive=False` and applies `Team.is_active == True` filter. The frontend can add "Show inactive" toggle (Claude's discretion). This mirrors the existing `include_inactive` pattern on `/admin/ref-data`.
**Warning signs:** Deactivated group still visible in the group list after calling PATCH to set `is_active=false`.

### Pitfall 5: Frontend role gate stale after role rename
**What goes wrong:** `AdminPage.jsx` checks `['org_admin', 'super_admin'].includes(user?.role)` — after the migration runs, every admin user has role `admin`, so this check fails and the existing Reference Data admin page shows "Admin access restricted."
**Why it happens:** The frontend role check is a hardcoded string comparison.
**How to avoid:** Update the `AdminPage.jsx` role check to `user?.role === 'admin'` in the same plan as the role migration. New pages use the same `'admin'` check from the start.
**Warning signs:** Admin user can no longer access the existing Reference Data page after deploy.

### Pitfall 6: `viewer` role orphaned after migration
**What goes wrong:** The test fixture creates a `viewer` role user. The D-05 mapping does not include `viewer`. After the data migration, this user still has `role = 'viewer'` in DB.
**Why it happens:** `viewer` was likely a legacy role not in active use.
**How to avoid:** Add `viewer` → `regular_user` to the data migration UPDATE: `UPDATE users SET role = 'regular_user' WHERE role = 'viewer'`. Confirm with the existing role values in seed_data.py and the production database before deploy.
**Warning signs:** User with `viewer` role cannot access any guarded routes.

---

## Code Examples

### Authorship ORM Column (nullable variant)

```python
# Source: backend/models.py Pipeline.created_by (non-nullable) — this is the nullable variant
# Add to Contact, Company, Deal, Fund, DealCounterparty, DealFunding:
created_by: Mapped[Optional[UUID]] = mapped_column(
    ForeignKey("users.id", ondelete="SET NULL"), nullable=True
)
updated_by: Mapped[Optional[UUID]] = mapped_column(
    ForeignKey("users.id", ondelete="SET NULL"), nullable=True
)
# Fund also needs:
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
)
```

### require_role dependency (existing, update callsites to use "admin")

```python
# Source: backend/api/dependencies.py — unchanged, already supports arbitrary role strings
def require_role(*roles: str):
    async def _check(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Role {current_user.role!r} not permitted")
        return current_user
    return _check

# Usage in new admin routes:
current_user: User = Depends(require_role("admin"))
```

### Group list with member count (SQLAlchemy 2.0)

```python
# Source: SQLAlchemy 2.0 docs — outerjoin + func.count + group_by pattern
from sqlalchemy import func, outerjoin, select
from backend.models import Team, User

stmt = (
    select(Team, func.count(User.id).label("member_count"))
    .outerjoin(User, User.team_id == Team.id)
    .where(Team.org_id == current_user.org_id)
    .where(Team.is_active == True)  # noqa: E712 — SQLAlchemy requires == not `is`
    .group_by(Team.id)
    .order_by(Team.name)
)
rows = await db.execute(stmt)
```

### Role label map (frontend constant)

```js
// Source: project pattern (no external library needed)
// In frontend/src/lib/roles.js or inline in AdminUsersPage.jsx
export const ROLE_LABELS = {
  admin: 'Admin',
  supervisor: 'Supervisor',
  principal: 'Principal',
  regular_user: 'Regular User',
};

export const ROLE_OPTIONS = Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label }));
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `super_admin` / `org_admin` / `team_manager` / `rep` role strings | `admin` / `supervisor` / `principal` / `regular_user` | Phase 17 (this phase) | All route guards and frontend role checks must update in same deploy |
| AdminPage.jsx role gate: `['org_admin', 'super_admin']` | `['admin']` | Phase 17 | Must update AdminPage.jsx role check string |
| No authorship on Contact/Company/Deal/Fund/DealCounterparty/DealFunding | `created_by`, `updated_by` nullable FKs on all six | Phase 17 | Phase 20 AUDIT-03 display depends on these columns existing |

**Deprecated/outdated after this phase:**
- `require_org_admin` dependency: should be replaced by `require_role("admin")`. The function may be kept as an alias or removed — if removed, update `admin.py` and `auth.py` import lists.

---

## Open Questions

1. **`viewer` role mapping**
   - What we know: `conftest.py` creates a `viewer` role user; D-05 mapping does not mention `viewer`
   - What's unclear: Is `viewer` in production data? What should it map to?
   - Recommendation: Map `viewer` → `regular_user` in the migration (same UPDATE) and update the test fixture. If the planner disagrees, document the decision.

2. **`users.role` column size: String(20)**
   - What we know: Column is `String(20)`; longest new value is `regular_user` (12 chars) — fits
   - What's unclear: No action needed, but worth noting
   - Recommendation: No migration needed; String(20) is sufficient for all new role values.

3. **`Deal.team_id` is non-nullable (`nullable=False` in ORM, `RESTRICT` on delete)**
   - What we know: Every deal must have a team. D-03 says no change needed.
   - What's unclear: When an admin creates a deal going forward, they must pick a group. The group dropdown on deal create/edit form currently shows all teams — after this phase, it should show only active groups. This is a minor UI update scope question.
   - Recommendation: Note this for the planner. The deal create form is not a Phase 17 deliverable, but filtering inactive groups from the team dropdown may be worth flagging as a task in the plan.

4. **`AdminPage.jsx` Users tab: remove or keep?**
   - What we know: D-14 says "may be left as-is or removed if superseded — planner's call"
   - What's unclear: The existing Users tab in AdminPage.jsx uses `getUsers({ size: 100 })` — a read-only list with no edit capability. The new `/admin/users` page will supersede it.
   - Recommendation: Remove the Users tab from AdminPage.jsx to avoid confusion. It adds no value once `/admin/users` exists.

---

## Environment Availability

Step 2.6: SKIPPED for this phase's external tooling (FastAPI, SQLAlchemy, React, Alembic are all already running in the Docker dev environment per `make dev`).

The migration target is the same PostgreSQL instance already provisioned. SQLite is used for tests and is already working.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio + httpx AsyncClient |
| Config file | none (run via Makefile: `pytest backend/tests/ -v`) |
| Quick run command | `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/ -v -x` |
| Full suite command | `docker-compose -f deploy/docker-compose.yml run --rm backend pytest backend/tests/ -v --cov=backend --cov-report=html --cov-fail-under=85` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GROUP-01 | Create/rename/deactivate group via API | integration | `pytest backend/tests/test_admin_groups.py -x` | ❌ Wave 0 |
| GROUP-02 | Assign user to group; previous group cleared | integration | `pytest backend/tests/test_admin_users.py::test_group_assignment -x` | ❌ Wave 0 |
| GROUP-03 | Grant supervisor role | integration | `pytest backend/tests/test_admin_users.py::test_role_update -x` | ❌ Wave 0 |
| GROUP-04 | Grant principal role | integration | included in test_role_update | ❌ Wave 0 |
| GROUP-05 | Grant admin role | integration | included in test_role_update | ❌ Wave 0 |
| GROUP-06 | Effective role visible in user list + profile | integration | `pytest backend/tests/test_admin_users.py::test_user_list_includes_role -x` | ❌ Wave 0 |
| AUDIT-01 | created_by + created_at set on INSERT | integration | `pytest backend/tests/test_authorship.py::test_created_by_set_on_insert -x` | ❌ Wave 0 |
| AUDIT-02 | updated_by + updated_at set on UPDATE | integration | `pytest backend/tests/test_authorship.py::test_updated_by_set_on_update -x` | ❌ Wave 0 |
| ADMIN-10 | Admin user list returns all users with group + role | integration | `pytest backend/tests/test_admin_users.py -x` | ❌ Wave 0 |
| ADMIN-11 | Admin group list returns groups with member count | integration | `pytest backend/tests/test_admin_groups.py -x` | ❌ Wave 0 |
| ROLE-MIGRATION | Old role strings no longer present in DB after migration | integration | `pytest backend/tests/test_role_migration.py -x` | ❌ Wave 0 |
| EXISTING TESTS | Existing ref_data, deals, funds tests still pass after role rename | regression | `pytest backend/tests/test_ref_data.py backend/tests/test_funds.py backend/tests/test_deals_pe.py -x` | ✅ Exists |

### Sampling Rate
- **Per task commit:** `pytest backend/tests/ -x -q` (stop on first failure)
- **Per wave merge:** `pytest backend/tests/ -v --cov=backend --cov-fail-under=85`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `backend/tests/test_admin_groups.py` — covers GROUP-01, ADMIN-11
- [ ] `backend/tests/test_admin_users.py` — covers GROUP-02 to GROUP-06, ADMIN-10
- [ ] `backend/tests/test_authorship.py` — covers AUDIT-01, AUDIT-02
- [ ] `backend/tests/test_role_migration.py` — verifies old role strings are gone, new ones present

---

## Sources

### Primary (HIGH confidence)
- Direct codebase inspection: `backend/models.py`, `backend/auth/security.py`, `backend/api/dependencies.py`, `backend/api/routes/admin.py`, `backend/api/routes/auth.py`, `backend/services/_crm.py`, `backend/tests/conftest.py`, `frontend/src/pages/AdminPage.jsx`, `frontend/src/components/Layout.jsx`, `frontend/src/main.jsx` — all patterns observed directly
- `alembic/versions/0001_initial.py` — migration structure and SQLite/PostgreSQL UUID handling

### Secondary (MEDIUM confidence)
- Alembic documentation pattern for data migrations via `op.execute()` — well-established practice
- SQLAlchemy 2.0 `func.count` + `outerjoin` aggregate pattern — standard ORM usage

### Tertiary (LOW confidence — not required, all answers found in codebase)
- None

---

## Metadata

**Confidence breakdown:**
- Role migration scope: HIGH — all callsites identified by grep, all role strings confirmed in code
- Authorship column gaps: HIGH — confirmed by reading every target model in models.py
- Frontend patterns: HIGH — AdminPage.jsx, Layout.jsx, DataGrid.jsx, main.jsx all read directly
- Test impact: HIGH — conftest.py seeded_org fixture role strings confirmed
- `viewer` role: MEDIUM — present in tests, unclear if in production data

**Research date:** 2026-04-06
**Valid until:** Stable domain — valid until codebase changes. Re-research not needed before planning.
