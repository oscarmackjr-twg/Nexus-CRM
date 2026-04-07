---
phase: 17-groups-roles-authorship-schema
verified: 2026-04-07T00:00:00Z
status: human_needed
score: 11/11 must-haves verified
re_verification: false
human_verification:
  - test: "Navigate to /admin/users as admin, verify user list shows group_name and role badge, then edit a user's role and confirm badge updates in the list without page reload"
    expected: "List renders with all columns; PATCH succeeds and query cache invalidation causes the row to update in place with the new role badge"
    why_human: "React Query cache invalidation and DOM update on mutation success cannot be verified programmatically without a running browser"
  - test: "Navigate to /admin/groups as admin, create a group, rename it, then deactivate it; toggle Show Inactive to confirm it reappears"
    expected: "All four operations succeed with toast confirmations; deactivated group disappears from the default list and reappears when includeInactive=true"
    why_human: "Multi-step UI flow with window.confirm dialog and query invalidation across two query keys requires a running browser"
  - test: "Log in as a regular_user and navigate directly to /admin/users and /admin/groups"
    expected: "Both pages show the access-restricted card ('Admin access is restricted to admins.') rather than the data table"
    why_human: "Access gate rendering depends on useAuth hook providing the user role at runtime"
  - test: "Verify the sidebar shows 'Users' and 'Groups' nav entries under the ADMIN section and that clicking each routes to the correct page"
    expected: "Two entries visible below 'Reference Data'; clicking 'Users' loads AdminUsersPage, clicking 'Groups' loads AdminGroupsPage"
    why_human: "Sidebar active-state logic and route matching require a running browser"
---

# Phase 17: Groups, Roles & Authorship Schema — Verification Report

**Phase Goal:** The four-role model and group membership structure exist in the database, all entities carry authorship fields, and admins can manage users and groups through a dedicated UI
**Verified:** 2026-04-07
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Role values in DB are admin/supervisor/principal/regular_user after migration | VERIFIED | Migration 0012 has `UPDATE users SET role = 'admin'`, `'supervisor'`, `'regular_user'`; `User.role` default=`regular_user`; conftest fixtures use new strings exclusively |
| 2 | All six entities have created_by, updated_by columns in ORM and DB | VERIFIED | Contact, Company, Deal, Fund, DealCounterparty, DealFunding all carry `created_by: Mapped[Optional[UUID]]` and `updated_by: Mapped[Optional[UUID]]` with `ForeignKey("users.id", ondelete="SET NULL")`; migration adds corresponding DDL |
| 3 | Team model has is_active column for group deactivation | VERIFIED | `Team.is_active: Mapped[bool]` present in models.py line 58; migration adds `op.add_column("teams", sa.Column("is_active", ...))`  |
| 4 | All route guards and role checks use new role strings | VERIFIED | `require_org_admin` now checks `("admin",)` only; `admin.py`, `auth.py`, `_crm.py`, `seed_data.py` all use `admin`, `supervisor`, `regular_user`; zero occurrences of `org_admin`, `super_admin`, `team_manager` in production code |
| 5 | Admin can list, create, rename, and deactivate groups via API | VERIFIED | `admin_groups.py` router: GET with member_count aggregation (`func.count(User.id)`), POST returning 201, PATCH updating name and/or is_active; guarded with `require_role("admin")` |
| 6 | Admin can list users with group and role, create users, update role and group | VERIFIED | `admin_users.py` router: GET with `selectinload(User.team)` for group_name, POST with username generation + role validation, PATCH with VALID_ROLES check and team_id single-FK update |
| 7 | Group list includes member_count | VERIFIED | Query uses `func.count(User.id).label("member_count")` with `outerjoin(User, User.team_id == Team.id).group_by(Team.id)`; `GroupResponse` schema has `member_count: int` |
| 8 | Moving a user to a new group clears prior group (exactly one group) | VERIFIED | `team_id` is a single FK column on User; PATCH sets `user.team_id = payload.team_id` directly — prior value is overwritten automatically |
| 9 | created_by is set on INSERT for all 6 entities | VERIFIED | All six services inject `created_by=self.current_user.id` in their create methods: contacts.py:193, companies.py:191, deals.py:363, funds.py:40, counterparties.py:123, funding.py:116 |
| 10 | updated_by is set on UPDATE for all 6 entities | VERIFIED | All six services set `entity.updated_by = self.current_user.id` in their update methods: contacts.py:279, companies.py:254, deals.py:434, funds.py:58, counterparties.py:155, funding.py:147 |
| 11 | Frontend admin pages exist, route, and connect to APIs | VERIFIED | AdminUsersPage and AdminGroupsPage use `useQuery`/`useMutation` wired to real API clients; routes registered in main.jsx; sidebar entries present in Layout.jsx |

**Score:** 11/11 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `alembic/versions/0012_v13_groups_roles_authorship.py` | DDL + data migration for Phase 17 | VERIFIED | revision=0012, down_revision=0011_deal_funding, adds is_active, authorship columns, role data migration, no postgresql.UUID |
| `backend/models.py` | ORM columns for authorship + Team.is_active | VERIFIED | All 6 entities have nullable created_by/updated_by; Team.is_active: Mapped[bool]; User.role default="regular_user" |
| `backend/api/routes/admin_groups.py` | Group CRUD API | VERIFIED | GET/POST/PATCH, require_role("admin"), member_count aggregation, is_active filter, 104 lines — substantive |
| `backend/api/routes/admin_users.py` | User admin API | VERIFIED | GET/POST/PATCH, selectinload(User.team), VALID_ROLES validation, username generation, 153 lines — substantive |
| `backend/schemas/admin_groups.py` | Group Pydantic schemas | VERIFIED | GroupCreate, GroupUpdate, GroupResponse with `member_count: int` |
| `backend/schemas/admin_users.py` | User admin Pydantic schemas | VERIFIED | AdminUserCreate, AdminUserUpdate, AdminUserResponse with `group_name: Optional[str]` |
| `backend/tests/test_admin_groups.py` | Group API integration tests | VERIFIED | 8 tests: list, list_excludes_inactive, list_includes_inactive, non_admin_forbidden_list, create_group, non_admin_forbidden_create, rename_group, deactivate_group |
| `backend/tests/test_admin_users.py` | User admin API integration tests | VERIFIED | 8 tests: list_users, non_admin_forbidden_list, user_list_includes_role, create_user, non_admin_forbidden_create, update_user_role, group_assignment |
| `backend/tests/test_authorship.py` | Authorship injection tests | VERIFIED | 6 tests: contact_created_by_set_on_insert, contact_updated_by_set_on_update, company_created_by_set_on_insert, deal_created_by_set_on_insert, fund_created_by_set_on_insert, created_by_never_changes_on_update |
| `frontend/src/pages/AdminUsersPage.jsx` | User Management admin page | VERIFIED | "User Management" title, admin gate, useQuery wired to adminUsersApi.list(), ROLE_LABELS badge display, Add User CTA |
| `frontend/src/pages/AdminGroupsPage.jsx` | Group Management admin page | VERIFIED | "Group Management" title, admin gate, useQuery wired to adminGroupsApi.list(), includeInactive toggle, Add Group / Create Group / Rename Group CTAs |
| `frontend/src/api/adminUsers.js` | API client for /admin/users | VERIFIED | list/create/update methods calling `/admin/users` via shared client |
| `frontend/src/api/adminGroups.js` | API client for /admin/groups | VERIFIED | list (with includeInactive param) / create / update methods calling `/admin/groups` |
| `frontend/src/lib/roles.js` | Role label constants | VERIFIED | ROLE_LABELS with 4 entries (admin, supervisor, principal, regular_user); ROLE_OPTIONS exported |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `alembic/versions/0012_v13_groups_roles_authorship.py` | `backend/models.py` | Column definitions match ORM | VERIFIED | Migration adds `created_by` FK columns using `sa.types.Uuid()` (not postgresql.UUID); ORM uses same `ForeignKey("users.id", ondelete="SET NULL")` pattern |
| `backend/auth/security.py` | `backend/api/routes/admin.py` | require_org_admin replaced with require_role('admin') | VERIFIED | admin.py imports `require_role` from `backend.api.dependencies` and uses `Depends(require_role("admin"))` on both POST/PATCH endpoints |
| `backend/api/routes/admin_groups.py` | `backend/models.py` | Team model queries with is_active filter and member_count | VERIFIED | `func.count(User.id)` JOIN with `Team.is_active == True` filter at lines 23-29 |
| `backend/services/contacts.py` | `backend/models.py` | created_by=self.current_user.id on Contact INSERT | VERIFIED | Line 193-194: `created_by=self.current_user.id, updated_by=self.current_user.id` in Contact constructor |
| `backend/api/main.py` | `backend/api/routes/admin_groups.py` + `admin_users.py` | Router registration at /api/v1 | VERIFIED | Line 19 imports both routers; lines 79-80 register them in the include_router loop |
| `frontend/src/pages/AdminUsersPage.jsx` | `frontend/src/api/adminUsers.js` | useQuery with queryKey ['admin', 'users'] | VERIFIED | `queryKey: ['admin', 'users'], queryFn: () => adminUsersApi.list()` at line 49-50 |
| `frontend/src/pages/AdminGroupsPage.jsx` | `frontend/src/api/adminGroups.js` | useQuery with queryKey ['admin', 'groups'] | VERIFIED | `queryKey: ['admin', 'groups', includeInactive], queryFn: () => adminGroupsApi.list(includeInactive)` at lines 36-37 |
| `frontend/src/main.jsx` | `frontend/src/pages/AdminUsersPage.jsx` | Route registration at /admin/users | VERIFIED | Line 46: `<Route path="admin/users" element={<AdminUsersPage />} />` |
| `frontend/src/components/Layout.jsx` | `/admin/users` and `/admin/groups` | Sidebar nav entry under ADMIN group | VERIFIED | Lines 54-55: `{ name: 'Users', href: '/admin/users', icon: Users }` and `{ name: 'Groups', href: '/admin/groups', icon: UsersRound }` |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `AdminUsersPage.jsx` | `usersQuery.data` | `adminUsersApi.list()` → `GET /admin/users` → SQLAlchemy query with `selectinload(User.team)` | Yes — live DB query | FLOWING |
| `AdminGroupsPage.jsx` | `groupsQuery.data` | `adminGroupsApi.list()` → `GET /admin/groups` → JOIN query with `func.count(User.id)` | Yes — live DB query | FLOWING |
| `admin_groups.py GET /` | rows from DB | `select(Team, func.count(User.id)).outerjoin(User).where(org_id).group_by(Team.id)` | Yes — real aggregate query | FLOWING |
| `admin_users.py GET /` | users from DB | `select(User).where(org_id).options(selectinload(User.team))` | Yes — real DB query with eager load | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Migration file syntax valid | `python -c "import ast; ast.parse(...)"` | `Migration syntax OK` | PASS |
| ORM models syntax valid | `python -c "import ast; ast.parse(...)"` | `Models syntax OK` | PASS |
| Migration has no postgresql.UUID | `grep postgresql alembic/versions/0012_v13_groups_roles_authorship.py` | no output | PASS |
| Zero old role strings in backend production code | `grep -r "org_admin\|super_admin\|team_manager" backend/ --include="*.py"` | only `require_org_admin` function name (kept as alias, now checks "admin") | PASS |
| Zero old role strings in frontend | `grep -r "org_admin\|super_admin\|team_manager" frontend/src/` | no output | PASS |
| All 6 services inject created_by on INSERT | `grep "created_by=self.current_user.id"` across 6 service files | 6 matches (one per file) | PASS |
| All 6 services inject updated_by on UPDATE | `grep "updated_by = self.current_user.id"` across 6 service files | 6 matches (one per file) | PASS |
| AdminUsersPage wired to real API | `grep "queryFn.*adminUsersApi.list"` | line 50 | PASS |
| AdminGroupsPage wired to real API | `grep "queryFn.*adminGroupsApi.list"` | line 37 | PASS |
| Admin routes registered in main.py | `grep "admin_groups_router\|admin_users_router" backend/api/main.py` | lines 79-80 | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| GROUP-01 | 17-01, 17-02, 17-03 | Admin can create, rename, and deactivate groups | SATISFIED | `admin_groups.py` POST/PATCH endpoints; `AdminGroupsPage.jsx` with Create Group dialog, Rename Group dialog, deactivate PATCH |
| GROUP-02 | 17-02, 17-03 | Admin can assign any user to exactly one group (moving user removes from prior group) | SATISFIED | PATCH /admin/users sets `user.team_id` (single FK — prior value overwritten); `AdminUsersPage.jsx` Edit User dialog with Group select |
| GROUP-03 | 17-02, 17-03 | Admin can grant a user the Supervisor role | SATISFIED | PATCH /admin/users accepts `role: "supervisor"`; VALID_ROLES includes "supervisor"; Edit User dialog includes Supervisor in ROLE_OPTIONS |
| GROUP-04 | 17-02, 17-03 | Admin can grant a user the Principal role | SATISFIED | VALID_ROLES includes "principal"; ROLE_LABELS has principal entry; role selectable in Edit User dialog |
| GROUP-05 | 17-02, 17-03 | Admin can grant a user the Admin role | SATISFIED | VALID_ROLES includes "admin"; Admin selectable in Edit User dialog |
| GROUP-06 | 17-01, 17-02, 17-03 | User's effective role visible in profile and admin user list | SATISFIED | `AdminUserResponse` includes `role` field; `AdminUsersPage.jsx` renders role as Badge with ROLE_LABELS display |
| AUDIT-01 | 17-01, 17-02 | All in-scope objects store created_by + created_at, set on insert, never updated | SATISFIED (6/8 entities) | Contact, Company, Deal, Fund, DealCounterparty, DealFunding all have `created_by`; `created_by` never updated in service UPDATE methods. Call and Note entities do not yet exist (Phase 19) — deferred by design |
| AUDIT-02 | 17-01, 17-02 | All in-scope objects store updated_by + updated_at, updated on every write | SATISFIED (6/8 entities) | All 6 services set `updated_by` on UPDATE; Fund gets new `updated_at` column; Call/Note deferred to Phase 19 |
| ADMIN-10 | 17-02, 17-03 | Admin has a User Management screen: list users, see group+role, add users, edit role/group | SATISFIED | `AdminUsersPage.jsx` with DataGrid columns Name/Email/Group/Role/Status, Add User dialog, Edit User dialog |
| ADMIN-11 | 17-02, 17-03 | Admin has a Group Management screen: list groups with member count, create, rename, view/change members | SATISFIED | `AdminGroupsPage.jsx` with DataGrid columns Name/Members/Status/Actions, Add Group dialog, Rename Group dialog, member_count from API |

**Note on AUDIT-01/AUDIT-02:** The requirement text lists "Call" and "Note" entities. These ORM models do not exist in Phase 17 — they are introduced in Phase 19. The Phase 17 plans correctly scoped authorship to the 6 entities that exist: Contact, Company, Deal, Fund, DealCounterparty, DealFunding. Call and Note authorship will be satisfied when those entities are created in Phase 19.

---

### Anti-Patterns Found

| File | Pattern | Severity | Assessment |
|------|---------|----------|------------|
| `frontend/src/pages/AdminUsersPage.jsx` | `placeholder="Full name"` etc. (7 occurrences) | Info | HTML input placeholder attributes — not code stubs. All data is live-wired via useQuery. |
| `backend/auth/security.py` | `async def require_org_admin` function name | Info | Kept as convenience alias for backward compatibility; implementation was updated to check `("admin",)` only. Not a role-string leak. |

No blocker anti-patterns found.

---

### Human Verification Required

#### 1. User Management page end-to-end flow

**Test:** Log in as admin, navigate to /admin/users. Verify the user list table shows Name, Email, Group, Role (as colored badge), Status, and action icons. Click pencil on a user, change their role to Supervisor, click "Update User".
**Expected:** Toast shows "User updated", the row in the DataGrid updates to show "Supervisor" badge without a full page reload.
**Why human:** React Query cache invalidation + DOM re-render on mutation success requires a running browser.

#### 2. Group Management page end-to-end flow

**Test:** Navigate to /admin/groups. Click "Add Group", enter "Test Group", click "Create Group". Then click pencil, rename to "Renamed Group". Then click X, confirm deactivation. Toggle "Show inactive".
**Expected:** Each operation shows a toast; group disappears from active list after deactivation; reappears when "Show inactive" is toggled on.
**Why human:** Multi-step flow with window.confirm dialog and cross-query invalidation requires a running browser.

#### 3. Non-admin access gate

**Test:** Log in as a regular_user (e.g., alpha-rep@example.com). Navigate directly to /admin/users and /admin/groups.
**Expected:** Both pages render a restricted-access card: "Admin access is restricted to admins." No data table is shown.
**Why human:** useAuth hook result and conditional rendering require a running browser.

#### 4. Sidebar navigation visibility

**Test:** Log in as admin. Verify the left sidebar ADMIN section shows "Reference Data", "Users", "Groups", "Team Settings". Click Users and Groups links.
**Expected:** Each link is active-highlighted when on its route; clicking routes to the correct page.
**Why human:** Active-state CSS and React Router link matching require a running browser.

---

### Gaps Summary

No automated gaps found. All 11 observable truths are verified by code evidence. Four items require human verification (UI rendering, mutation feedback, access gate, sidebar) which cannot be confirmed programmatically. The human verification checkpoint in Plan 03 Task 3 was reportedly executed and passed all 12 steps per the SUMMARY, but this verification cannot confirm that claim without a live browser session.

The AUDIT-01/AUDIT-02 requirement wording references "Call" and "Note" entities that do not exist in the codebase yet. This is intentional — Call and Note are Phase 19 entities. Phase 17 correctly adds authorship to all entities that currently exist. This is not a gap in Phase 17 execution.

---

_Verified: 2026-04-07_
_Verifier: Claude (gsd-verifier)_
