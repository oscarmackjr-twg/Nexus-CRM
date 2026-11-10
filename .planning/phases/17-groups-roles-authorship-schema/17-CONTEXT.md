# Phase 17: Groups, Roles & Authorship Schema - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Lay the data foundation for v1.3 Access Control & Audit Trails:
- Map existing RBAC roles to the four-role model (Admin / Supervisor / Principal / Regular User)
- Enforce group membership (exactly one group per user) using the existing Team model
- Add `created_by`, `created_at`, `updated_by`, `updated_at` authorship fields to all entities that lack them
- Admin UI: dedicated User Management page (`/admin/users`) and Group Management page (`/admin/groups`)

Access enforcement (403 rules, group-scoped queries) is Phase 18. Call and Note entities are Phase 19.

</domain>

<decisions>
## Implementation Decisions

### Group Model — Reuse Team table
- **D-01:** Do NOT create a new `groups` table. Repurpose the existing `teams` table as the Group concept.
- **D-02:** `User.team_id` is the group membership FK — enforce "exactly one group" at application layer (moving a user to a new group clears their previous `team_id`). No DB constraint needed.
- **D-03:** `Deal.team_id` already exists and already scopes deals to a group — no schema change needed for deals. Phase 18 enforcement will read this column directly.
- **D-04:** The Team model's hierarchical fields (`parent_team_id`, `sub_teams`) remain in the schema but are unused by the Group concept — do not remove them, do not expose them in Group admin UI.

### Role Migration — In-place rename via Alembic
- **D-05:** Rename existing role string values in-place via Alembic data migration:
  - `super_admin` → `admin`
  - `org_admin` → `admin`
  - `team_manager` → `supervisor`
  - `rep` (or `member`) → `regular_user`
  - New value `principal` is additive — no existing rows map to it
- **D-06:** Update ALL existing route guards in `backend/auth/security.py` and all routes that call `require_role()` or `require_org_admin` to use the new role strings in this phase.
- **D-07:** The `require_org_admin` dependency should be updated or replaced to check for `admin` role.

### Authorship Fields — Nullable, no backfill
- **D-08:** Add `created_by` (UUID FK → users.id), `created_at` (timestamp), `updated_by` (UUID FK → users.id, nullable), `updated_at` (timestamp) to all entities that lack them.
  - Entities already covered (skip): Pipeline, Board, Task, Page, Automation
  - Entities needing new columns: Contact, Company, Deal, Fund, DealCounterparty, DealFunding
- **D-09:** New columns are `NULLABLE`. Existing rows get `NULL` — no backfill. `NULL` means "created before authorship tracking." Detail views show "—" for null values (AUDIT-03, Phase 18+).
- **D-10:** `created_by` and `created_at` are set on INSERT and never updated. `updated_by` and `updated_at` are set on every write operation.
- **D-11:** Entities that already have `created_by` as non-nullable (Pipeline, Board, Task, Page, Automation) are left unchanged.

### Admin UI — Separate sub-routes
- **D-12:** User Management and Group Management land as dedicated pages at `/admin/users` and `/admin/groups`, NOT as tabs inside the existing `AdminPage.jsx`.
- **D-13:** Add nav entries for "Users" and "Groups" under the existing ADMIN section in the sidebar (`Layout.jsx`).
- **D-14:** The existing `/admin` route (Reference Data) remains unchanged. The existing Users tab inside `AdminPage.jsx` may be left as-is or removed if superseded by the new `/admin/users` page — planner's call.
- **D-15:** User Management page (`/admin/users`): list all users with their group and effective role visible; support adding new users, editing role/group assignment.
- **D-16:** Group Management page (`/admin/groups`): list groups with member count; support create group, rename group, view and reassign members.
- **D-17:** This page structure sets the pattern for Phase 20 (audit history viewer) and Phase 21 (Principal reports) — each will be its own sub-route under `/admin/`.

### Claude's Discretion
- Exact form/modal design for user and group edit flows
- Whether role dropdown on user edit shows friendly labels ("Supervisor") or raw values
- Pagination strategy for user and group lists
- Loading skeleton and error state handling in new admin pages

</decisions>

<specifics>
## Specific Ideas

- No specific UI references provided — standard admin list+modal pattern consistent with existing AdminPage.jsx style (DataGrid + Dialog components already in codebase)
- Role values in DB should be lowercase snake_case (`regular_user`, `supervisor`, `principal`, `admin`) for consistency with existing pattern

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — GROUP-01 to GROUP-06, AUDIT-01 to AUDIT-02, ADMIN-10 to ADMIN-11 (full requirement definitions)

### Roadmap
- `.planning/ROADMAP.md` §Phase 17 — Goal, success criteria, and dependency note (builds on existing RBAC; Phase 18 depends on this phase's schema)

### Existing models and auth
- `backend/models.py` — Team model (lines ~45–67), User model (lines ~70–105), Deal.team_id, existing `created_by` patterns on Pipeline/Board/Task/Page/Automation
- `backend/auth/security.py` — `get_current_user`, `require_org_admin` — these guards need updating to new role strings
- `backend/api/routes/admin.py` — Existing reference data admin routes (pattern to follow for new user/group routes)
- `backend/api/routes/auth.py` — Existing user list/update routes (lines ~130–370) — may be extended or referenced for user management

### Frontend patterns
- `frontend/src/pages/AdminPage.jsx` — Existing admin page with Users + Reference Data tabs — pattern for new admin pages; DataGrid + Dialog usage
- `frontend/src/components/Layout.jsx` — Sidebar nav — where new ADMIN nav entries are added
- `frontend/src/components/DataGrid.jsx` — Reusable grid component for user and group lists

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DataGrid.jsx` + `Pagination.jsx`: use for user list and group list tables
- `Dialog` (shadcn/ui): use for create/edit modals in both admin pages
- `RefSelect.jsx`: may be useful for role/group dropdowns in user edit form
- `useAuth` hook: provides current user context for role-gating the admin pages

### Established Patterns
- Route guards: `require_role("org_admin", "super_admin")` pattern — update callers to new role strings
- Admin page gate: `AdminPage.jsx` checks `user?.role in {'org_admin', 'super_admin'}` — new pages gate on `admin` role
- Alembic migrations: existing migrations in `backend/` — new migration adds columns and renames role values
- `created_by` pattern (Board, Task, etc.): non-nullable UUID FK with `Depends(get_current_user)` injection — new columns are nullable variant of this same pattern

### Integration Points
- `backend/api/routes/auth.py`: existing user CRUD — new `/admin/users` backend routes may extend or call these
- `frontend/src/components/Layout.jsx`: sidebar nav group — add "Users" and "Groups" links under ADMIN section
- TanStack Query keys: new queries `['admin', 'users']` (already used in AdminPage.jsx) and `['admin', 'groups']`

</code_context>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope. Access enforcement (403 rules) is Phase 18. Row-level security at DB layer is explicitly out of scope per REQUIREMENTS.md.

</deferred>

---

*Phase: 17-groups-roles-authorship-schema*
*Context gathered: 2026-04-06*
