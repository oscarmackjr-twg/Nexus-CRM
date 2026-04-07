---
phase: 17-groups-roles-authorship-schema
plan: "03"
subsystem: frontend
tags: [admin-ui, react, rbac, groups, users, sidebar]
dependency_graph:
  requires: ["17-02"]
  provides: ["admin-ui-complete", "group-management-ui", "user-management-ui"]
  affects: ["frontend/src/pages", "frontend/src/api", "frontend/src/components/Layout.jsx", "frontend/src/main.jsx"]
tech_stack:
  added: []
  patterns:
    - "DataGrid + useQuery for admin list pages"
    - "Dialog-based create/edit/deactivate with useMutation + invalidation"
    - "Role badge variants: admin=default, supervisor=secondary, principal/regular_user=outline"
    - "Admin gate: user?.role !== 'admin' guard at top of page"
    - "includeInactive toggle for soft-deleted group visibility"
key_files:
  created:
    - frontend/src/lib/roles.js
    - frontend/src/api/adminUsers.js
    - frontend/src/api/adminGroups.js
    - frontend/src/pages/AdminUsersPage.jsx
    - frontend/src/pages/AdminGroupsPage.jsx
  modified:
    - frontend/src/components/Layout.jsx
    - frontend/src/main.jsx
decisions:
  - "17-03: ROLE_LABELS extracted to shared lib/roles.js — avoids duplication across AdminUsersPage, future profile views, sidebar footer"
  - "17-03: Groups query on AdminUsersPage uses separate queryKey ['admin', 'groups'] (not parameterized) — group dropdown only needs active groups, no includeInactive flag needed there"
  - "17-03: Sidebar role display uses ROLE_LABELS[user?.role] for friendly label (Admin, Supervisor, etc.) — improves UX for renamed role strings from Plan 01"
metrics:
  duration: "~60min (including human checkpoint verification)"
  completed: "2026-04-07"
  tasks: 3
  files: 7
---

# Phase 17 Plan 03: Admin Users & Groups Frontend Summary

React admin pages for User Management and Group Management with DataGrid, create/edit/deactivate dialogs, role badges, sidebar nav entries, and route registration — completing the full-stack admin UI for Phase 17.

## What Was Built

### Task 1: API clients, role constants, Admin Users page, Admin Groups page

**Commits:** 9e8544f

- `frontend/src/lib/roles.js` — ROLE_LABELS and ROLE_OPTIONS constants for the four roles (admin, supervisor, principal, regular_user)
- `frontend/src/api/adminUsers.js` — API client with list/create/update methods targeting `/admin/users`
- `frontend/src/api/adminGroups.js` — API client with list/create/update methods targeting `/admin/groups`, includeInactive param
- `frontend/src/pages/AdminUsersPage.jsx` — User Management page: DataGrid with Name/Email/Group/Role badge/Status/Actions columns, Create User dialog (Name/Email/Password/Role/Group fields), Edit User dialog (Role/Group editable), deactivate with window.confirm, admin gate, loading skeletons, empty state, toast notifications
- `frontend/src/pages/AdminGroupsPage.jsx` — Group Management page: DataGrid with Group Name/Members/Status/Actions columns, Create Group dialog, Rename Group dialog, deactivate with window.confirm, Show Inactive toggle, admin gate, loading skeletons, empty state, toast notifications

### Task 2: Sidebar nav entries + route registration

**Commits:** 5471155

- `frontend/src/components/Layout.jsx` — Added UsersRound to lucide-react imports; added Users and Groups nav entries under ADMIN sidebar group; renamed existing "Admin" nav item to "Reference Data" for clarity; sidebar footer now uses ROLE_LABELS for friendly role display
- `frontend/src/main.jsx` — Added imports for AdminUsersPage and AdminGroupsPage; registered /admin/users and /admin/groups routes as siblings to existing /admin route

### Task 3: Human verification checkpoint — APPROVED

All 12 verification steps passed:
1. Sidebar shows Users and Groups under ADMIN
2. User Management page loads with correct columns and role badges
3. Add User dialog opens with all required fields
4. Edit User dialog changes role — toast confirms success, badge updates
5. Group Management page loads with member counts and status
6. Add Group creates group with 0 members
7. Rename Group updates name in list
8. Deactivate group removes it from active list
9. Show Inactive toggle restores deactivated group
10. Existing /admin Reference Data page unaffected

## Deviations from Plan

None — plan executed exactly as written. The optional ROLE_LABELS sidebar footer improvement (noted as "Claude's discretion" in the plan) was implemented as it improves UX consistency with the renamed role strings from Plan 01.

## Known Stubs

None — all data is live-wired to backend APIs. The admin pages query real data and mutations invalidate query cache on success.

## Self-Check: PASSED

- `frontend/src/lib/roles.js` — FOUND
- `frontend/src/api/adminUsers.js` — FOUND
- `frontend/src/api/adminGroups.js` — FOUND
- `frontend/src/pages/AdminUsersPage.jsx` — FOUND
- `frontend/src/pages/AdminGroupsPage.jsx` — FOUND
- Commit 9e8544f — FOUND
- Commit 5471155 — FOUND
