# Phase 8: Login, Banner & Sidebar - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the current horizontal top-nav (`Layout.jsx`) with a white left sidebar matching the POC (`Intrepid-POC/frontend/src/components/Layout.tsx`) pattern. Polish the login page with the real TWG logo and navy primary button. Extract the staging banner into a standalone `StagingBanner` component used on all authenticated pages.

Files in scope: `frontend/src/components/Layout.jsx`, `frontend/src/pages/LoginPage.jsx`, new `frontend/src/components/StagingBanner.jsx`, `frontend/src/assets/twg-logo.png` (copy from POC).

</domain>

<decisions>
## Implementation Decisions

### Sidebar layout architecture
- **D-01:** Switch from horizontal top-bar to left sidebar layout, matching the POC `Layout.tsx` exactly. Structure: `<div className="flex flex-col min-h-screen">` → `<StagingBanner />` → `<div className="flex flex-1">` → `<aside>` sidebar + `<main>` content.
- **D-02:** Sidebar: `w-60 min-h-full flex flex-col bg-white border-r border-gray-200 sticky top-0 h-screen`.
- **D-03:** Main content: `flex-1 bg-[#f8fafc] min-h-screen`, inner `<div className="p-6">` wrapping `<Outlet />`.
- **D-04:** Remove the dark `<header>` (slate-900 top bar) and all top-bar UI (Bell, Search button, notification icons). Keep AIQueryBar component wired to `⌘K` keyboard shortcut only — no visible trigger button in the sidebar this phase.

### Nav icons
- **D-05:** Keep Lucide icons alongside labels in all nav items. Format: `<item.icon className="h-4 w-4 shrink-0" />` + `<span>{item.name}</span>` per item.

### Nav section grouping
- **D-06:** Four groups (one ungrouped + three labeled sections):
  - **Ungrouped (top):** Dashboard
  - **Section: DEALS** — Contacts, Companies, Pipelines, Boards
  - **Section: TOOLS** — Pages, Automations, Analytics, AI, LinkedIn
  - **Section: ADMIN** — Admin, Team Settings
- **D-07:** Section labels styled per POC: `px-5 pt-4 pb-1 text-xs font-bold tracking-widest text-[#94a3b8] uppercase select-none block`.

### Active / inactive nav item styles
- **D-08:** Active item: `border-l-4 border-[#1a3868] text-[#1a3868] font-semibold bg-gray-50`.
- **D-09:** Inactive item: `border-l-4 border-transparent text-[#475569] hover:text-[#1a3868] hover:bg-gray-50`.
- **D-10:** Nav item wrapper class (all items): `px-5 py-2 text-sm flex items-center gap-2 border-l-4 transition-colors`.

### Sidebar header (logo)
- **D-11:** Copy `twg-logo.png` from `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/assets/twg-logo.png` to `frontend/src/assets/twg-logo.png`.
- **D-12:** Sidebar header: `<img src={twgLogo} alt="TWG Global" className="h-8 w-auto" />` + `<p className="mt-1 text-xs font-semibold tracking-widest text-[#1a3868] uppercase">Nexus CRM</p>`. Container: `px-5 py-5 border-b border-gray-200`.

### Sidebar user footer
- **D-13:** Footer per POC pattern: `px-5 py-4 border-t border-gray-200 mt-auto`. Shows `user.full_name || user.username` + `user.role` in muted style + `Sign out` button (`text-xs text-[#475569] hover:text-[#1a3868] font-medium`).
- **D-14:** Use `useAuth()` hook already available in `Layout.jsx` for `{ user, logout }`.

### StagingBanner component
- **D-15:** Create `frontend/src/components/StagingBanner.jsx` — exact POC pattern:
  ```jsx
  export default function StagingBanner() {
    if (import.meta.env.VITE_APP_ENV === 'production') return null
    return (
      <div className="w-full bg-amber-400 text-gray-900 text-center text-sm font-bold py-2 px-4 sticky top-0 z-50">
        STAGING -- Not Production
      </div>
    )
  }
  ```
- **D-16:** Import and render `<StagingBanner />` at the top of `Layout.jsx` (before the `flex` wrapper containing sidebar + main). This covers all authenticated pages.
- **D-17:** Use `VITE_APP_ENV` as the env variable (matches POC and REQUIREMENTS.md). The login page currently uses `import.meta.env.MODE !== 'production'` — update it to use the StagingBanner component instead.

### Login page changes
- **D-18:** Replace the inline staging banner div in `LoginPage.jsx` with `<StagingBanner />` (import the new component).
- **D-19:** Replace the "TWG GLOBAL" text placeholder with `<img src={twgLogo} alt="TWG Global" className="h-10 w-auto" />` (import `twgLogo` from `@/assets/twg-logo.png`). Remove the `TODO` comment.
- **D-20:** Fix the Sign in button: change `className="w-full bg-slate-900 text-white hover:bg-slate-700"` to `className="w-full bg-primary text-primary-foreground hover:bg-primary/90"`. This uses the navy color via CSS variable cascade established in Phase 7.
- **D-21:** Background remains `bg-slate-50` — no change to login page background color.
- **D-22:** Backend status indicator stays as-is (already correct per LOGIN-03 requirements).

### Claude's Discretion
- Whether to use `NavLink` (current) or `Link` with manual active detection (POC approach) — either is fine; prefer whichever is cleaner given React Router v6.
- Exact Vite asset import syntax for the PNG logo.
- Whether `Team Settings` appears as a nav item or only in the user footer — planner can decide based on current routing.

</decisions>

<specifics>
## Specific Ideas

- POC `Layout.tsx` at `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/components/Layout.tsx` is the canonical reference — copy its structure directly, adapting nav items and app name.
- POC `StagingBanner.tsx` at `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/components/StagingBanner.tsx` is the canonical reference — copy exactly.
- The login page is already 80% done from Phase 1. The three changes needed are: replace text placeholder with logo image, replace inline banner with StagingBanner component, and fix button color.
- `⌘K` keyboard handler should remain in `Layout.jsx` (keep the `useState(commandOpen)` + `useEffect` keyboard handler and `<AIQueryBar>` render).

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase requirements
- `.planning/ROADMAP.md` — Phase 8 goal, success criteria, requirement IDs (LOGIN-01 through LOGIN-04, BANNER-01, NAV-01 through NAV-05)
- `.planning/REQUIREMENTS.md` — Full requirement definitions for LOGIN-*, BANNER-01, NAV-*

### POC reference implementation (source of truth for sidebar + banner)
- `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/components/Layout.tsx` — Sidebar structure, nav item classes, logo header, user footer, section labels
- `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/components/StagingBanner.tsx` — StagingBanner component (copy exactly)

### Files to modify
- `frontend/src/components/Layout.jsx` — Full replacement: top-bar → sidebar layout
- `frontend/src/pages/LoginPage.jsx` — Logo image, banner component swap, button color fix
- `frontend/src/App.jsx` — Review only; no changes expected (Layout wraps all auth routes already)

### Phase 7 output (brand foundation — already live)
- `frontend/src/styles.css` — `--primary: 217 60% 25%` navy, Montserrat font, POC CSS vars
- `frontend/tailwind.config.js` — `hsl(var(--primary))` wiring; `bg-primary` = navy

### Codebase conventions
- `.planning/codebase/CONVENTIONS.md` — naming conventions and patterns
- `.planning/codebase/STRUCTURE.md` — frontend directory layout

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/hooks/useAuth.js` — `{ user, logout }` already used in `Layout.jsx`, works as-is
- `frontend/src/components/ui/` — shadcn/ui primitives; `Button`, `Card`, `Input`, `Label` used on login
- `frontend/src/lib/utils.js` — `cn()` utility already imported in Layout for class merging
- Lucide icons already imported in `Layout.jsx` — reuse same imports in new sidebar

### Established Patterns
- `NavLink` from react-router-dom with `({ isActive }) =>` callback is the current active-state pattern
- `useAuth()` from `@/hooks/useAuth` is the canonical auth hook
- CSS variable cascade: `bg-primary` = navy `#1a3868` via `--primary: 217 60% 25%` in styles.css → tailwind.config.js

### Integration Points
- `App.jsx` wraps all authenticated routes in `<AuthGuard><Layout /></AuthGuard>` — `StagingBanner` inside `Layout.jsx` automatically covers all protected pages
- Login page is outside `Layout` (separate `<Route path="/login">`) — it needs its own `<StagingBanner />` import
- `AIQueryBar` is already imported in `Layout.jsx` — keep the render call and keyboard handler, just remove the top-bar container that housed the visible trigger button

</code_context>

<deferred>
## Deferred Ideas

- Visible ⌘K trigger button in sidebar — deferred to Phase 9 or 10 layout polish pass
- Admin-only nav item visibility (only showing Admin link to `super_admin`/`org_admin` roles) — planner can implement if straightforward, otherwise defer to Phase 10

</deferred>

---

*Phase: 08-login-banner-sidebar*
*Context gathered: 2026-03-29*
