# Phase 08: Login, Banner & Sidebar - Research

**Researched:** 2026-03-28
**Domain:** React layout architecture, Vite static assets, React Router NavLink, Vitest component testing
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01:** Switch from horizontal top-bar to left sidebar layout, matching the POC `Layout.tsx` exactly. Structure: `<div className="flex flex-col min-h-screen">` → `<StagingBanner />` → `<div className="flex flex-1">` → `<aside>` sidebar + `<main>` content.

**D-02:** Sidebar: `w-60 min-h-full flex flex-col bg-white border-r border-gray-200 sticky top-0 h-screen`.

**D-03:** Main content: `flex-1 bg-[#f8fafc] min-h-screen`, inner `<div className="p-6">` wrapping `<Outlet />`.

**D-04:** Remove the dark `<header>` (slate-900 top bar) and all top-bar UI (Bell, Search button, notification icons). Keep AIQueryBar component wired to `⌘K` keyboard shortcut only — no visible trigger button in the sidebar this phase.

**D-05:** Keep Lucide icons alongside labels in all nav items. Format: `<item.icon className="h-4 w-4 shrink-0" />` + `<span>{item.name}</span>` per item.

**D-06:** Four groups (one ungrouped + three labeled sections):
- Ungrouped (top): Dashboard
- Section: DEALS — Contacts, Companies, Pipelines, Boards
- Section: TOOLS — Pages, Automations, Analytics, AI, LinkedIn
- Section: ADMIN — Admin, Team Settings

**D-07:** Section labels styled per POC: `px-5 pt-4 pb-1 text-xs font-bold tracking-widest text-[#94a3b8] uppercase select-none block`.

**D-08:** Active item: `border-l-4 border-[#1a3868] text-[#1a3868] font-semibold bg-gray-50`.

**D-09:** Inactive item: `border-l-4 border-transparent text-[#475569] hover:text-[#1a3868] hover:bg-gray-50`.

**D-10:** Nav item wrapper class (all items): `px-5 py-2 text-sm flex items-center gap-2 border-l-4 transition-colors`.

**D-11:** Copy `twg-logo.png` from `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/assets/twg-logo.png` to `frontend/src/assets/twg-logo.png`.

**D-12:** Sidebar header: `<img src={twgLogo} alt="TWG Global" className="h-8 w-auto" />` + `<p className="mt-1 text-xs font-semibold tracking-widest text-[#1a3868] uppercase">Nexus CRM</p>`. Container: `px-5 py-5 border-b border-gray-200`.

**D-13:** Footer per POC pattern: `px-5 py-4 border-t border-gray-200 mt-auto`. Shows `user.full_name || user.username` + `user.role` in muted style + `Sign out` button (`text-xs text-[#475569] hover:text-[#1a3868] font-medium`).

**D-14:** Use `useAuth()` hook already available in `Layout.jsx` for `{ user, logout }`.

**D-15:** Create `frontend/src/components/StagingBanner.jsx` with exact POC pattern:
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

**D-16:** Import and render `<StagingBanner />` at the top of `Layout.jsx` (before the `flex` wrapper containing sidebar + main). This covers all authenticated pages.

**D-17:** Use `VITE_APP_ENV` as the env variable (matches POC and REQUIREMENTS.md). The login page currently uses `import.meta.env.MODE !== 'production'` — update it to use the StagingBanner component instead.

**D-18:** Replace the inline staging banner div in `LoginPage.jsx` with `<StagingBanner />`.

**D-19:** Replace the "TWG GLOBAL" text placeholder with `<img src={twgLogo} alt="TWG Global" className="h-10 w-auto" />`. Remove the `TODO` comment.

**D-20:** Fix the Sign in button: change `className="w-full bg-slate-900 text-white hover:bg-slate-700"` to `className="w-full bg-primary text-primary-foreground hover:bg-primary/90"`.

**D-21:** Background remains `bg-slate-50` — no change to login page background color.

**D-22:** Backend status indicator stays as-is (already correct per LOGIN-03 requirements).

### Claude's Discretion

- Whether to use `NavLink` (current) or `Link` with manual active detection (POC approach) — either is fine; prefer whichever is cleaner given React Router v6.
- Exact Vite asset import syntax for the PNG logo.
- Whether `Team Settings` appears as a nav item or only in the user footer — planner can decide based on current routing.

### Deferred Ideas (OUT OF SCOPE)

- Visible ⌘K trigger button in sidebar — deferred to Phase 9 or 10 layout polish pass.
- Admin-only nav item visibility (only showing Admin link to `super_admin`/`org_admin` roles) — planner can implement if straightforward, otherwise defer to Phase 10.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LOGIN-01 | TWG logo (`twg-logo.png`) displayed centered above the login form | Asset copy from POC confirmed; Vite static PNG import via `import twgLogo from '@/assets/twg-logo.png'` is idiomatic |
| LOGIN-02 | Staging banner displayed on login page when `VITE_APP_ENV !== 'production'` (amber-400, sticky top) | StagingBanner component replaces existing inline div; env var key confirmed as `VITE_APP_ENV` |
| LOGIN-03 | Backend health status indicator shown on login page ("Backend connected" / "Backend unreachable") | Already implemented and correct — no changes needed; existing test covers this |
| LOGIN-04 | Login page button and focus rings use `#1a3868` navy primary color | CSS variable `--primary: 217 60% 25%` is live (Phase 7); `bg-primary text-primary-foreground` resolves to navy |
| BANNER-01 | `StagingBanner` component created and displayed on all authenticated pages (amber-400, sticky top, z-50, env-gated) | New `StagingBanner.jsx` created; placed inside `Layout.jsx` before the flex row covers all `<AuthGuard><Layout />` routes |
| NAV-01 | Sidebar redesigned with white background + `border-r` separator (replacing dark slate-900) | `bg-white border-r border-gray-200` replaces current `bg-slate-900` header |
| NAV-02 | TWG logo + "Nexus CRM" subtext displayed in sidebar header (matching POC Layout.tsx pattern) | Logo asset available in POC; sidebar header classes and content defined (D-12) |
| NAV-03 | Active nav items display navy `border-l-4` left indicator + `#1a3868` text + `bg-gray-50` background | NavLink `isActive` callback applies D-08 / D-09 classes; NavLink preferred over manual `useLocation` |
| NAV-04 | Nav section group labels styled with uppercase tracking-widest muted text (e.g., DEALS, ADMIN) | D-07 label class string confirmed from POC source (`text-[#94a3b8]`) |
| NAV-05 | Sidebar footer displays current username, role, and Sign out button in muted POC style | `useAuth()` already returns `{ user, logout }`; D-13 footer pattern confirmed from POC |
</phase_requirements>

---

## Summary

Phase 8 is a pure frontend layout swap with three tightly scoped changes: replace the dark horizontal top-nav with a white left sidebar, extract the staging banner into a reusable component, and polish the login page (logo image, button color, banner component swap). No backend work. No new dependencies required.

All source-of-truth CSS variables are already live from Phase 7 (`--primary: 217 60% 25%` navy, Montserrat font). The POC `Layout.tsx` and `StagingBanner.tsx` are verified readable at `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/components/`. The TWG logo PNG exists at `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/assets/twg-logo.png` and must be copied to `frontend/src/assets/twg-logo.png` (the assets directory does not yet exist in nexus-crm).

The existing `LoginPage.test.jsx` test checks for the staging banner with `screen.getByText(/environment/i)` — this will break once the inline div (which renders "DEVELOPMENT ENVIRONMENT") is replaced by `StagingBanner` (which renders "STAGING -- Not Production"). That test must be updated as part of this phase. A new `Layout.test.jsx` is needed to cover NAV-01 through NAV-05.

**Primary recommendation:** Implement as a single plan (08-01-PLAN.md). The work is linear with no parallelizable streams: copy asset → create StagingBanner → update Layout → update LoginPage → update/add tests.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-router-dom | 6.28.0 (installed) | NavLink active-state routing | Already in project; NavLink `({ isActive })` callback is idiomatic for per-item active classes |
| tailwindcss | 3.4.15 (installed) | Utility-class layout | All class strings in D-01 through D-13 are Tailwind utilities already configured |
| lucide-react | 0.468.0 (installed) | Nav item icons | Already imported in Layout.jsx; keep exact same icon set |
| vite | 5.4.10 (installed) | Static PNG import | `import logo from '@/assets/twg-logo.png'` compiles to a hashed URL — standard Vite pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| vitest | 2.1.8 (installed) | Component tests | Test sidebar render, active class, StagingBanner env gate |
| @testing-library/react | 16.1.0 (installed) | DOM assertions | `screen.getByRole`, `screen.getByAltText` for logo, `screen.getByText` for banner |

**No new installations required.** All needed libraries are already present.

---

## Architecture Patterns

### Recommended Project Structure (changes only)

```
frontend/src/
├── assets/
│   └── twg-logo.png          ← NEW (copy from POC)
├── components/
│   ├── Layout.jsx             ← REPLACE top-bar with sidebar
│   ├── StagingBanner.jsx      ← NEW component
│   └── ...
├── pages/
│   └── LoginPage.jsx          ← PATCH (logo, banner, button color)
└── __tests__/
    ├── LoginPage.test.jsx     ← UPDATE (banner text assertion)
    └── Layout.test.jsx        ← NEW (sidebar smoke tests)
```

### Pattern 1: Vite Static Asset Import (PNG logo)

Vite treats any non-JS file imported with a static `import` statement as a URL asset. The resolved value is the hashed public URL string.

```jsx
// Source: Vite docs / POC Layout.tsx
import twgLogo from '@/assets/twg-logo.png'

// Usage
<img src={twgLogo} alt="TWG Global" className="h-8 w-auto" />
```

The `@` alias maps to `frontend/src/` as configured in `vite.config.js` (`resolve.alias`). The `assets/` directory does not yet exist — it must be created by copying the logo file.

**Confidence:** HIGH (verified in vite.config.js and POC source)

### Pattern 2: NavLink with isActive callback (React Router v6)

The project already uses `NavLink` with `({ isActive }) =>` callbacks. This is the correct pattern for the sidebar — cleaner than the POC's `useLocation` + `startsWith` approach, and works out of the box with React Router v6.

```jsx
// Source: existing Layout.jsx pattern (confirmed working)
import { NavLink } from 'react-router-dom'

<NavLink
  to={item.href}
  end={item.exact}
  className={({ isActive }) =>
    cn(
      'px-5 py-2 text-sm flex items-center gap-2 border-l-4 transition-colors',
      isActive
        ? 'border-[#1a3868] text-[#1a3868] font-semibold bg-gray-50'
        : 'border-transparent text-[#475569] hover:text-[#1a3868] hover:bg-gray-50'
    )
  }
>
  <item.icon className="h-4 w-4 shrink-0" />
  <span>{item.name}</span>
</NavLink>
```

`end={true}` on the Dashboard item prevents `/contacts` from also marking Dashboard as active.

**Confidence:** HIGH (current codebase + React Router v6 docs)

### Pattern 3: StagingBanner env gate

```jsx
// Source: POC StagingBanner.tsx (exact copy)
export default function StagingBanner() {
  if (import.meta.env.VITE_APP_ENV === 'production') return null
  return (
    <div className="w-full bg-amber-400 text-gray-900 text-center text-sm font-bold py-2 px-4 sticky top-0 z-50">
      STAGING -- Not Production
    </div>
  )
}
```

`import.meta.env.VITE_APP_ENV` is the Vite idiom for accessing custom env vars (must be prefixed `VITE_`). When undefined (local dev with no `.env` setting), the condition `=== 'production'` is false, so the banner renders — correct safe-default behavior.

**Confidence:** HIGH (POC source + Vite env var docs)

### Pattern 4: Layout shell structure (full replacement)

```jsx
// Source: POC Layout.tsx adapted for nexus-crm
export default function Layout() {
  const { user, logout } = useAuth()
  const [commandOpen, setCommandOpen] = useState(false)

  // Keep ⌘K handler (D-04)
  useEffect(() => { /* keyboard handler */ }, [])

  return (
    <div className="flex flex-col min-h-screen">
      <StagingBanner />
      <div className="flex flex-1">
        <aside className="w-60 min-h-full flex flex-col bg-white border-r border-gray-200 sticky top-0 h-screen">
          {/* Logo header (D-12) */}
          {/* Nav list with section groups (D-06, D-07, D-08, D-09, D-10) */}
          {/* User footer (D-13) */}
        </aside>
        <main className="flex-1 bg-[#f8fafc] min-h-screen">
          <div className="p-6">
            <Outlet />
          </div>
        </main>
      </div>
      <AIQueryBar open={commandOpen} onOpenChange={setCommandOpen} />
    </div>
  )
}
```

Key difference from current layout: remove the `fixed inset-x-0 top-0` header and the `pt-14` offset on main. The sidebar is `sticky top-0 h-screen` (scrolls independently from main content).

### Pattern 5: Nav group structure (data-driven)

Instead of a flat `navItems` array, use a structured array with labeled sections to match D-06.

```jsx
const navGroups = [
  {
    label: null,
    items: [{ name: 'Dashboard', href: '/', icon: Home, exact: true }]
  },
  {
    label: 'DEALS',
    items: [
      { name: 'Contacts', href: '/contacts', icon: Users },
      { name: 'Companies', href: '/companies', icon: Building2 },
      { name: 'Pipelines', href: '/pipelines', icon: KanbanSquare },
      { name: 'Boards', href: '/boards', icon: Workflow },
    ]
  },
  {
    label: 'TOOLS',
    items: [
      { name: 'Pages', href: '/pages', icon: BookOpen },
      { name: 'Automations', href: '/automations', icon: Zap },
      { name: 'Analytics', href: '/analytics', icon: BarChart3 },
      { name: 'AI', href: '/ai', icon: Sparkles },
      { name: 'LinkedIn', href: '/linkedin', icon: Linkedin },
    ]
  },
  {
    label: 'ADMIN',
    items: [
      { name: 'Admin', href: '/admin', icon: Settings },
      { name: 'Team Settings', href: '/settings/team', icon: Settings },
    ]
  }
]
```

Section labels render only when `group.label !== null`. This is cleaner than POC's inline hardcoded links for the nexus-crm nav item count.

### Anti-Patterns to Avoid

- **Don't replicate the POC's `useLocation` + `startsWith` active detection:** The project already uses `NavLink`'s built-in `isActive` which handles nested routes correctly.
- **Don't add `position: fixed` to sidebar:** POC uses `sticky top-0 h-screen` — this keeps the sidebar in-flow (avoids content overlap that required `pt-14` on the current layout).
- **Don't forget to remove `pt-14` from main:** The current `<main className="pt-14 p-6">` offset was needed for the fixed header. After the layout swap main becomes `flex-1 bg-[#f8fafc] min-h-screen` with inner `p-6`.
- **Don't use `import.meta.env.MODE`:** Current LoginPage uses `MODE !== 'production'`. Replace with `VITE_APP_ENV === 'production'` via StagingBanner component per D-17.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Active nav state detection | Manual `useLocation().pathname.startsWith(...)` | `NavLink ({ isActive })` callback | React Router v6 handles nested route matching correctly; startsWith breaks on exact paths |
| Env-gated component visibility | Inline `{condition && <div>}` in Layout | `StagingBanner` component | Encapsulates env check; reusable across login and authenticated pages; matches POC contract |
| Logo URL resolution | Hardcoded `/twg-logo.png` in public/ | Vite `import twgLogo from '@/assets/twg-logo.png'` | Vite adds content hash for cache-busting; `@` alias resolves correctly in both dev and build |

---

## Common Pitfalls

### Pitfall 1: Assets directory does not exist yet

**What goes wrong:** `import twgLogo from '@/assets/twg-logo.png'` throws a Vite resolution error at dev server startup because `frontend/src/assets/` does not exist.

**Why it happens:** The nexus-crm project has no assets directory (verified: `ls frontend/src/assets/` returns nothing). The logo exists only in the POC.

**How to avoid:** The implementation task must `cp` the logo file AND create the directory in the same step (e.g., `mkdir -p frontend/src/assets && cp /path/to/twg-logo.png frontend/src/assets/twg-logo.png`).

**Warning signs:** Vite dev server emits a `Cannot resolve module '@/assets/twg-logo.png'` error at startup.

### Pitfall 2: Existing LoginPage test breaks on banner text

**What goes wrong:** `LoginPage.test.jsx` line 59 asserts `screen.getByText(/environment/i)` — this matches the current inline banner text "DEVELOPMENT ENVIRONMENT". After the swap to `StagingBanner`, the rendered text is "STAGING -- Not Production". The test will fail because `/environment/i` no longer matches.

**Why it happens:** The test was written against the inline banner string, not the StagingBanner component's text.

**How to avoid:** Update the LoginPage test to assert `screen.getByText(/staging/i)` or `screen.getByText(/not production/i)` to match StagingBanner's output.

**Warning signs:** `vitest run` after implementation shows "Unable to find an element with the text: /environment/i".

### Pitfall 3: Sidebar overflow on short viewports

**What goes wrong:** With many nav items (12+), the sidebar exceeds viewport height and the user footer disappears off screen.

**Why it happens:** The nav list uses `flex-1` but doesn't set `overflow-y-auto` on the `<nav>` element.

**How to avoid:** Add `overflow-y-auto` to the nav element: `<nav className="flex-1 overflow-y-auto py-2">` — matches POC line 25.

### Pitfall 4: `sticky top-0 h-screen` sidebar + StagingBanner height offset

**What goes wrong:** When StagingBanner is visible (non-production), the sidebar's `sticky top-0` means its top edge sits at `top: 0` (under the banner). The sidebar then appears 40px shorter than the viewport, and the footer may be clipped at the bottom.

**Why it happens:** `sticky top-0` is relative to the scroll container (the `flex flex-col min-h-screen` wrapper). Since `StagingBanner` is above the flex row containing the sidebar, the sidebar's effective sticky anchor is correct — its top tracks the top of the inner `flex flex-1` div, not `top: 0` of the viewport.

**How to avoid:** The POC structure (`flex flex-col min-h-screen` → `StagingBanner` → `flex flex-1` → aside + main) handles this correctly. Do not change the DOM order. Do not try to add a `top` offset to the aside.

**Warning signs:** If the banner and sidebar appear to overlap, the DOM structure has deviated from D-01.

### Pitfall 5: AIQueryBar renders outside the layout tree

**What goes wrong:** If `<AIQueryBar>` is placed inside the sidebar `<aside>` or `<main>`, it may render at an unexpected scroll offset. It also no longer has access to a portal target outside the sidebar box.

**Why it happens:** AIQueryBar uses a modal/dialog pattern. It must be a sibling of the top-level flex wrapper, not nested inside sidebar or main.

**How to avoid:** Keep `<AIQueryBar open={commandOpen} onOpenChange={setCommandOpen} />` as the last child of the outer `<div className="flex flex-col min-h-screen">` — outside the `<div className="flex flex-1">` wrapper. This is already the pattern in the current Layout.jsx.

---

## Code Examples

### Current Layout.jsx structure to DELETE

```jsx
// DELETE: entire <header className="fixed inset-x-0 top-0 z-30 bg-slate-900 ...">
// DELETE: <main className="pt-14 p-6"> — replace with sidebar+main flex layout
// DELETE: Avatar, DropdownMenu, Bell, Search imports (no longer used)
// KEEP: useAuth, useEffect, useState, Outlet, NavLink, cn, AIQueryBar imports
// KEEP: Lucide icon imports (add Settings for Admin/Team nav items)
```

### LoginPage.jsx targeted changes (3 lines)

```jsx
// Line 49-53: DELETE inline staging banner div, REPLACE with:
import StagingBanner from '@/components/StagingBanner'
// ... inside JSX:
<StagingBanner />

// Line 58: DELETE text placeholder span, REPLACE with:
import twgLogo from '@/assets/twg-logo.png'
// ... inside JSX:
<img src={twgLogo} alt="TWG Global" className="h-10 w-auto" />

// Line 77: PATCH button className:
// FROM: className="w-full bg-slate-900 text-white hover:bg-slate-700"
// TO:   className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
```

### StagingBanner.jsx (full file — copy exactly from POC)

```jsx
// Source: /Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/components/StagingBanner.tsx
export default function StagingBanner() {
  if (import.meta.env.VITE_APP_ENV === 'production') return null
  return (
    <div className="w-full bg-amber-400 text-gray-900 text-center text-sm font-bold py-2 px-4 sticky top-0 z-50">
      STAGING -- Not Production
    </div>
  )
}
```

### Layout.test.jsx (new — smoke coverage for NAV-01 through NAV-05)

```jsx
// Pattern: matches existing test-utils.jsx renderWithProviders pattern
import { screen } from '@testing-library/react'
import Layout from '@/components/Layout'
import { renderWithProviders } from './__tests__/test-utils'

vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { full_name: 'Test User', username: 'test', role: 'admin' }, logout: vi.fn() })
}))

vi.mock('@/components/AIQueryBar', () => ({ default: () => null }))

describe('Layout sidebar', () => {
  it('renders white sidebar with nav links and section labels', () => {
    renderWithProviders(<Layout />, { route: '/', path: '/*' })
    expect(screen.getByAltText('TWG Global')).toBeInTheDocument()       // NAV-02 logo
    expect(screen.getByText('DEALS')).toBeInTheDocument()               // NAV-04
    expect(screen.getByText('TOOLS')).toBeInTheDocument()               // NAV-04
    expect(screen.getByText('ADMIN')).toBeInTheDocument()               // NAV-04
    expect(screen.getByText('Test User')).toBeInTheDocument()           // NAV-05 username
    expect(screen.getByText('admin')).toBeInTheDocument()               // NAV-05 role
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()  // NAV-05
  })

  it('renders staging banner in non-production', () => {
    renderWithProviders(<Layout />, { route: '/', path: '/*' })
    expect(screen.getByText(/staging/i)).toBeInTheDocument()            // BANNER-01
  })
})
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat `navItems` array + horizontal top-bar | Grouped `navGroups` + vertical sidebar | This phase | Requires restructuring data shape from flat list to grouped list |
| `import.meta.env.MODE !== 'production'` | `VITE_APP_ENV === 'production'` via StagingBanner | This phase | Consistent with POC and REQUIREMENTS.md; test must be updated |
| Inline staging banner div in LoginPage | Shared `StagingBanner` component | This phase | Single source of truth for banner text and styling |

---

## Open Questions

1. **Team Settings in ADMIN nav group or omit from sidebar?**
   - What we know: `/settings/team` is a valid route in App.jsx; D-06 lists it under ADMIN. The POC does not have this route.
   - What's unclear: Whether to show it as a nav item alongside Admin, or only in the user footer as a link.
   - Recommendation: Include it as a nav item in the ADMIN group (as specified in D-06). Both routes exist and are within the same `<AuthGuard><Layout />` subtree.

2. **AdminPage route guard (role-based visibility)**
   - What we know: D-06 includes Admin in the ADMIN section; D-22 says "admin-only nav item visibility" is deferred.
   - What's unclear: Should the Admin nav link render for all roles (and rely on backend 403), or be hidden for non-admins?
   - Recommendation: Render for all authenticated users this phase (backend enforces access). Role-based hiding is explicitly deferred per CONTEXT.md.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js / npm | Frontend dev server | ✓ | (project running) | — |
| POC logo asset | LOGIN-01, NAV-02 | ✓ | — | — |
| `frontend/src/assets/` directory | Vite logo import | ✗ | — | Create directory as part of asset copy |
| `VITE_APP_ENV` env var | BANNER-01, LOGIN-02 | not set (undefined OK) | — | Undefined = banner shows (safe default per POC) |

**Missing dependencies with no fallback:**
- None that block execution.

**Missing dependencies with fallback:**
- `frontend/src/assets/` directory: must be created with `mkdir -p frontend/src/assets` before or during the logo copy step.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 2.1.8 |
| Config file | `frontend/vite.config.js` (`test` section) |
| Setup file | `frontend/src/test/setup.js` |
| Quick run command | `cd frontend && npm test` |
| Full suite command | `cd frontend && npm test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LOGIN-01 | Logo image present above form | unit | `cd frontend && npm test -- --reporter=verbose LoginPage` | ✅ update needed |
| LOGIN-02 | StagingBanner renders on login page | unit | `cd frontend && npm test -- --reporter=verbose LoginPage` | ✅ update needed |
| LOGIN-03 | Backend status indicator renders | unit | `cd frontend && npm test -- --reporter=verbose LoginPage` | ✅ already passing |
| LOGIN-04 | Sign in button uses navy primary | unit | `cd frontend && npm test -- --reporter=verbose LoginPage` | ✅ update optional |
| BANNER-01 | StagingBanner renders in Layout | unit | `cd frontend && npm test -- --reporter=verbose Layout` | ❌ Wave 0 |
| NAV-01 | Sidebar has white bg + border-r | unit | `cd frontend && npm test -- --reporter=verbose Layout` | ❌ Wave 0 |
| NAV-02 | TWG logo present in sidebar | unit | `cd frontend && npm test -- --reporter=verbose Layout` | ❌ Wave 0 |
| NAV-03 | Active item has navy border-l-4 | unit | `cd frontend && npm test -- --reporter=verbose Layout` | ❌ Wave 0 |
| NAV-04 | Section labels (DEALS/TOOLS/ADMIN) render | unit | `cd frontend && npm test -- --reporter=verbose Layout` | ❌ Wave 0 |
| NAV-05 | Footer shows user name, role, sign out | unit | `cd frontend && npm test -- --reporter=verbose Layout` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `cd frontend && npm test`
- **Per wave merge:** `cd frontend && npm test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/src/__tests__/Layout.test.jsx` — covers BANNER-01, NAV-01 through NAV-05
- [ ] `frontend/src/__tests__/LoginPage.test.jsx` — update line 59: `getByText(/environment/i)` → `getByText(/staging/i)`

---

## Sources

### Primary (HIGH confidence)
- POC `Layout.tsx` — `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/components/Layout.tsx` (read directly)
- POC `StagingBanner.tsx` — `/Users/oscarmack/PythonFramework/Intrepid-POC/frontend/src/components/StagingBanner.tsx` (read directly)
- Existing `Layout.jsx` — `/Users/oscarmack/OpenClaw/nexus-crm/frontend/src/components/Layout.jsx` (read directly)
- Existing `LoginPage.jsx` — `/Users/oscarmack/OpenClaw/nexus-crm/frontend/src/pages/LoginPage.jsx` (read directly)
- Existing `LoginPage.test.jsx` — `/Users/oscarmack/OpenClaw/nexus-crm/frontend/src/__tests__/LoginPage.test.jsx` (read directly)
- `vite.config.js` — `@` alias and test config confirmed (read directly)
- `frontend/package.json` — library versions confirmed (read directly)
- `frontend/src/styles.css` — `--primary: 217 60% 25%` navy confirmed (read directly)

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions D-01 through D-22 — user-locked implementation choices (project artifact)
- CONVENTIONS.md — frontend naming patterns (project artifact)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies already installed; verified from package.json
- Architecture: HIGH — POC source read directly; existing codebase patterns confirmed
- Pitfalls: HIGH — identified from direct code inspection (test failure, missing assets dir, sticky offset)

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable stack — React Router v6, Tailwind v3, Vitest v2 are all stable releases)
