# Phase 1: UI Polish - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Visual consistency pass across all screens — fix spacing, typography, and layout. No redesign, no new features. Lock the app to dark mode. Polish the login page to match the qa.oscarmackjr.com reference design.

Screens in scope: Login, Dashboard, Contacts (list + detail), Companies (list + detail), Deals (list + detail).

</domain>

<decisions>
## Implementation Decisions

### Theme
- **D-01:** Lock the app to dark mode only. Remove the dark/light theme toggle from the sidebar. The login page already sets a dark tone — the inner app must match it consistently.
- **D-02:** Dark mode is the definitive design target for all polish work this phase. No light mode maintenance required.

### Login Page
- **D-03:** Redesign the login page to match the qa.oscarmackjr.com pattern:
  - **Staging/env banner** — a top banner that appears when the environment is not production (controlled by `VITE_ENV` or equivalent env var). Hidden in production.
  - **TWG Global logo** — firm branding displayed prominently above the form.
  - **App name: "Nexus CRM"** — displayed below the logo.
  - **Backend status indicator** — a small indicator showing API connectivity ("Backend: Connected" / "Backend: Unavailable"). Ping the health endpoint on mount.
  - **Sign-in form/bar** — email + password fields, sign-in button. Clean, vertically stacked.
- **D-04:** Background remains dark (similar to current slate-950 gradient).

### Spacing & Typography Consistency
- **D-05:** Audit and fix spacing, heading sizes, input padding, and card layout across all in-scope screens so they are visually indistinguishable in quality. The `DashboardPage` stat cards, `ContactsPage` table, and detail page layouts are the primary targets.
- **D-06:** No new design language introduced — use the existing shadcn/ui component library and Tailwind scale throughout.

### Dashboard
- **D-07:** Dashboard stat cards should reflect data available in Phase 1 (no DealCounterparty/DealFunding — those are Phase 5). Metrics sourced from existing deals and contacts are acceptable. Focus is on making the cards look correct and consistent, not on changing what they show.

### Claude's Discretion
- Exact TWG Global logo asset: use a text placeholder (`TWG GLOBAL`) if no logo file exists in the repo, and add a `TODO: replace with actual logo` comment. Planner should check `frontend/src/assets/` for existing logo files first.
- Backend health endpoint to ping: check `backend/api/main.py` or the router for an existing `/health` or `/ping` endpoint. If none exists, create a simple one.
- Typography scale specifics (font weights, sizes): follow shadcn/ui defaults for dark mode; enforce consistency, not custom values.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, plan stubs (01-01, 01-02, 01-03)
- `.planning/REQUIREMENTS.md` — UI-01, UI-02, UI-03 requirements

### Codebase
- `frontend/src/pages/LoginPage.jsx` — current login page (to be redesigned)
- `frontend/src/pages/DashboardPage.jsx` — stat cards and layout (to be polished)
- `frontend/src/components/Layout.jsx` — sidebar, theme toggle (toggle to be removed)
- `frontend/src/components/ui/` — shadcn/ui primitives in use
- `.planning/codebase/CONVENTIONS.md` — naming conventions and patterns to follow
- `.planning/codebase/STRUCTURE.md` — frontend directory layout

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `components/ui/card.jsx` — `Card`, `CardHeader`, `CardTitle`, `CardContent`, `CardDescription` — already used on login and dashboard
- `components/ui/badge.jsx` — used in dashboard stat cards
- `components/ui/skeleton.jsx` — loading state pattern already in use on dashboard
- `components/ui/input.jsx`, `label.jsx`, `button.jsx` — form primitives already used on login

### Established Patterns
- Page layout: `<div className="space-y-6">` with `<h1 className="text-3xl font-semibold">` headings
- Stat cards: `SectionCard` wrapper in `DashboardPage.jsx` — `Card` + `CardHeader` + `CardContent`
- Dark form inputs: `className="border-white/10 bg-white/5 text-white"` (from current login)
- Muted secondary text: `text-muted-foreground`
- Grid layouts: `grid gap-4 md:grid-cols-3`

### Integration Points
- Dark mode lock: `Layout.jsx` applies `document.documentElement.classList.toggle('dark', ...)` — set permanently to `dark` and remove toggle UI
- `useUIStore` in `frontend/src/store/useUIStore.js` — holds `theme` state; needs to be updated alongside the Layout change

</code_context>

<specifics>
## Specific Ideas

- **Login page reference:** qa.oscarmackjr.com — staging banner + logo + app name + backend status + sign-in bar, on a dark background.
- **Staging banner:** Should only render when `import.meta.env.MODE !== 'production'` (or a custom `VITE_APP_ENV` variable). Top-of-page, clearly labeled "Staging" or "Development".
- **Backend status:** Ping a `/health` or `/api/health` endpoint on mount. Show a colored dot + label ("Connected" green / "Unavailable" red). Non-blocking — login form is usable regardless.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-ui-polish*
*Context gathered: 2026-03-26*
