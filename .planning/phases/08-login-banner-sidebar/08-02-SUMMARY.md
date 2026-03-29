---
phase: 08-login-banner-sidebar
plan: "02"
subsystem: frontend-layout
tags: [sidebar, nav, layout, white-sidebar, nav-groups, user-footer]
dependency_graph:
  requires: ["08-01"]
  provides: ["white-sidebar-layout", "nav-groups", "user-footer", "staging-banner-in-layout"]
  affects: ["all-authenticated-pages"]
tech_stack:
  added: []
  patterns: ["NavLink with isActive callback", "navGroups data structure", "sticky sidebar", "user footer pattern"]
key_files:
  created:
    - frontend/src/__tests__/Layout.test.jsx
  modified:
    - frontend/src/components/Layout.jsx
decisions:
  - "NavGroups data structure replaces flat navItems — groups Dashboard (unlabeled), DEALS, TOOLS, ADMIN"
  - "overflow-y-auto on nav element prevents user footer from being clipped on short viewports"
  - "AIQueryBar placed as last child of outer flex-col div, outside flex-1 wrapper — avoids layout interference"
  - "Dashboard item uses end={true} (NavLink end prop) to prevent active highlight on nested routes"
  - "StagingBanner placed at top of outer flex-col div, above sidebar+main flex row"
metrics:
  duration: "2min"
  completed: "2026-03-29"
  tasks: 2
  files: 2
---

# Phase 08 Plan 02: Layout White Sidebar Summary

White sidebar layout replacing the dark horizontal top bar — TWG logo header, grouped nav sections (DEALS/TOOLS/ADMIN), navy active indicators, user footer with sign out, StagingBanner at top.

## What Was Built

**Task 1: Layout.jsx full rewrite**

Replaced the dark `bg-slate-900` fixed top bar with a professional white left sidebar:
- Sidebar: `w-60`, `bg-white border-r border-gray-200`, `sticky top-0 h-screen`
- Logo header: TWG logo image (`alt="TWG Global"`) + "Nexus CRM" subtext in navy uppercase
- Nav groups: Dashboard (unlabeled), DEALS (Contacts/Companies/Pipelines/Boards), TOOLS (Pages/Automations/Analytics/AI/LinkedIn), ADMIN (Admin/Team Settings)
- Section labels: `text-[#94a3b8] uppercase tracking-widest font-bold`
- Active nav item: `border-[#1a3868] text-[#1a3868] font-semibold bg-gray-50` with `border-l-4`
- Inactive nav item: `border-transparent text-[#475569]` with hover states
- User footer: `user?.full_name || user?.username`, `user?.role`, Sign out button
- StagingBanner at top of outer `flex flex-col min-h-screen`
- AIQueryBar with Cmd+K keyboard shortcut preserved (outside sidebar flex)

**Task 2: Layout.test.jsx smoke tests**

7 tests covering:
- NAV-02: TWG logo rendered with correct alt text and `<img>` tag
- NAV-02: "Nexus CRM" subtext in sidebar header
- NAV-04: Section labels DEALS, TOOLS, ADMIN present
- All 12 nav items present by name
- NAV-05: User footer shows full_name, role, Sign out
- NAV-05: Sign out click calls logout()
- BANNER-01: StagingBanner renders in Layout

## Verification Results

| Check | Status |
|-------|--------|
| White sidebar (NAV-01) | PASS |
| TWG logo alt="TWG Global" (NAV-02) | PASS |
| Navy active indicator border-[#1a3868] (NAV-03) | PASS |
| Section labels DEALS/TOOLS/ADMIN (NAV-04) | PASS |
| User footer + Sign out (NAV-05) | PASS |
| Layout.test.jsx 7 tests | PASS |

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | b60333e | feat(08-02): rewrite Layout.jsx as white sidebar with nav groups, logo header, user footer |
| 2 | 98b149e | test(08-02): add Layout.test.jsx smoke tests for sidebar structure |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all nav routes are real routes in the application. The `/admin` route is a new addition included in the ADMIN nav group; it links to an existing or future admin page but does not prevent the Layout goal from being achieved.

## Self-Check: PASSED

- `/Users/oscarmack/OpenClaw/nexus-crm/frontend/src/components/Layout.jsx` — exists, 125 lines
- `/Users/oscarmack/OpenClaw/nexus-crm/frontend/src/__tests__/Layout.test.jsx` — exists, 75 lines
- Commit b60333e — exists in git log
- Commit 98b149e — exists in git log
