# Phase 1: UI Polish - Research

**Researched:** 2026-03-26
**Domain:** React / Tailwind CSS / shadcn-ui dark mode polish
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Theme**
- D-01: Lock the app to dark mode only. Remove the dark/light theme toggle from the sidebar. The login page already sets a dark tone — the inner app must match it consistently.
- D-02: Dark mode is the definitive design target for all polish work this phase. No light mode maintenance required.

**Login Page**
- D-03: Redesign the login page to match the qa.oscarmackjr.com pattern:
  - Staging/env banner — a top banner that appears when the environment is not production (controlled by `VITE_ENV` or equivalent env var). Hidden in production.
  - TWG Global logo — firm branding displayed prominently above the form.
  - App name: "Nexus CRM" — displayed below the logo.
  - Backend status indicator — a small indicator showing API connectivity ("Backend: Connected" / "Backend: Unavailable"). Ping the health endpoint on mount.
  - Sign-in form/bar — email + password fields, sign-in button. Clean, vertically stacked.
- D-04: Background remains dark (similar to current slate-950 gradient).

**Spacing & Typography Consistency**
- D-05: Audit and fix spacing, heading sizes, input padding, and card layout across all in-scope screens so they are visually indistinguishable in quality. The DashboardPage stat cards, ContactsPage table, and detail page layouts are the primary targets.
- D-06: No new design language introduced — use the existing shadcn/ui component library and Tailwind scale throughout.

**Dashboard**
- D-07: Dashboard stat cards should reflect data available in Phase 1 (no DealCounterparty/DealFunding — those are Phase 5). Metrics sourced from existing deals and contacts are acceptable. Focus is on making the cards look correct and consistent, not on changing what they show.

### Claude's Discretion

- Exact TWG Global logo asset: use a text placeholder (`TWG GLOBAL`) if no logo file exists in the repo, and add a `TODO: replace with actual logo` comment. Planner should check `frontend/src/assets/` for existing logo files first.
- Backend health endpoint to ping: check `backend/api/main.py` or the router for an existing `/health` or `/ping` endpoint. If none exists, create a simple one.
- Typography scale specifics (font weights, sizes): follow shadcn/ui defaults for dark mode; enforce consistency, not custom values.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | Login page has clean, consistent styling matching the app's design language (correct spacing, typography, and layout) | LoginPage.jsx audit complete; redesign spec per D-03/D-04; existing Card/Input/Label/Button primitives reusable |
| UI-02 | All screens have consistent spacing, typography weights, and layout alignment (no mismatched padding, font sizes, or component gaps across Contact, Company, Deal, Dashboard, and list views) | All in-scope page components read; established patterns identified; inconsistencies catalogued |
| UI-03 | Dashboard metrics and layout reflect the expanded data model (correct deal counts, updated stat cards) | DashboardPage.jsx fully read; current query structure analysed; Phase 1 constraint (no CPARTY/FUNDING data) confirmed |
</phase_requirements>

---

## Summary

Phase 1 is a pure frontend polish pass — no backend schema changes, no new API endpoints (except a trivial health ping that already exists). All work is in React JSX files under `frontend/src/`. The stack is React 18 + Tailwind CSS 3 + shadcn/Radix primitives + Zustand for UI state. No new dependencies are needed.

The three work streams are well-separated: (1) redesign `LoginPage.jsx` to add staging banner, TWG branding, and backend status indicator; (2) make spacing/typography consistent across the six in-scope pages; (3) confirm `DashboardPage.jsx` stat cards are live-wired and visually polished. All three streams are isolated file edits with no inter-dependency.

One infrastructure issue must be addressed in this phase: `tailwind.config.js` does not declare `darkMode: 'class'`, which is required for the `.dark` class applied by `Layout.jsx` to activate Tailwind dark-mode utilities. While the app currently relies on CSS custom properties rather than `dark:` utility classes (which is why it mostly works), adding `darkMode: 'class'` is the correct foundation for a locked-dark-mode app and should be done as the first task.

**Primary recommendation:** Start with the Tailwind dark mode config fix, then the Login redesign, then the spacing pass, then the Dashboard metrics verification.

---

## Standard Stack

### Core (already installed — no new packages needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | ^18.3.1 | UI rendering | Project standard |
| Tailwind CSS | ^3.4.15 | Utility styling | Project standard |
| shadcn/Radix primitives | see `components/ui/` | Button, Card, Input, Label, Badge, Skeleton, Tabs, Dialog, Sheet | All already present in `frontend/src/components/ui/` |
| Zustand | ^5.0.2 | `useUIStore` — sidebar + theme state | Already manages theme; needs dark-lock update |
| TanStack Query | ^5.64.2 | Server state / data fetching | Dashboard uses `useQuery` for all live data |
| Axios | ^1.7.2 | HTTP client | `frontend/src/api/client.js` handles auth headers |
| react-hook-form + zod | ^7.54.2 / ^3.24.1 | Form validation on login | Already used in LoginPage |
| Vitest + Testing Library | ^2.1.8 / ^16.1.0 | Unit tests | Existing test suite; LoginPage.test.jsx exists |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lucide-react | ^0.468.0 | Icons | Use for any icon additions (e.g., status dot, brand mark fallback) |
| sonner | ^1.7.1 | Toast notifications | Already used; no changes needed |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| CSS custom properties for dark colors | Tailwind `dark:` utilities | `dark:` utilities require `darkMode: 'class'` in tailwind.config — worth adding even if not actively needed for this phase |
| Text placeholder for TWG logo | Inline SVG | Text placeholder is correct per discretion rules; only replace if `frontend/src/assets/` contains a logo file |

**Installation:** No new packages required.

---

## Architecture Patterns

### Recommended Project Structure (no changes to structure)

```
frontend/src/
├── pages/          # LoginPage.jsx, DashboardPage.jsx + 4 other in-scope pages
├── components/
│   ├── Layout.jsx  # Dark mode lock lives here
│   └── ui/         # shadcn primitives — no changes needed
├── store/
│   └── useUIStore.js  # Remove setTheme / light mode support
└── styles.css      # .dark CSS vars already defined correctly
```

### Pattern 1: Dark Mode Lock

**What:** `Layout.jsx` currently calls `document.documentElement.classList.toggle('dark', theme === 'dark')` on mount and on `theme` changes. `useUIStore` holds `theme` with a `setTheme` action.

**Correct approach to lock dark mode:**
1. Add `darkMode: 'class'` to `tailwind.config.js` (infrastructure correctness).
2. In `Layout.jsx`, replace the toggle effect with a one-time `useEffect` that unconditionally sets the `.dark` class: `document.documentElement.classList.add('dark')`.
3. Remove the `DropdownMenuItem` that calls `setTheme(...)` from the user menu.
4. Remove `theme` state and `setTheme` action from `useUIStore`. Remove `localStorage.getItem('nexus-theme')` initialisation.
5. Set the `localStorage` key `nexus-theme` to `'dark'` on first run, or simply stop reading it.

**Example (Layout.jsx effect):**
```jsx
// Replace the existing theme useEffect:
useEffect(() => {
  document.documentElement.classList.add('dark');
}, []);
```

**Example (useUIStore.js — simplified):**
```js
// Remove: theme, setTheme, localStorage.getItem('nexus-theme')
// Keep:   sidebarCollapsed, toggleSidebar
export const useUIStore = create((set) => ({
  sidebarCollapsed: savedCollapsed,
  toggleSidebar: () => set((state) => {
    const next = !state.sidebarCollapsed;
    localStorage.setItem('nexus-sidebar-collapsed', String(next));
    return { sidebarCollapsed: next };
  })
}));
```

### Pattern 2: Login Page Redesign

**What:** The current `LoginPage.jsx` is a minimal Card with title + description + form. D-03 requires five new visual elements.

**Structure to build:**
```jsx
<div className="relative flex min-h-screen flex-col items-center justify-center bg-[...existing gradient...] p-6">
  {/* 1. Staging banner — conditionally rendered */}
  {import.meta.env.MODE !== 'production' && (
    <div className="absolute top-0 left-0 right-0 bg-amber-500/90 py-1.5 text-center text-xs font-semibold text-black">
      Staging — {import.meta.env.MODE}
    </div>
  )}

  <Card className="w-full max-w-md ...">
    {/* 2. TWG Global logo / placeholder */}
    {/* 3. App name */}
    {/* 4. Backend status indicator */}
    {/* 5. Sign-in form (existing) */}
  </Card>
</div>
```

**Env detection:** Use `import.meta.env.MODE` (Vite built-in). Returns `'development'` in dev, `'production'` in production build. No new env variable required unless they want a custom staging label — discretion says use `VITE_APP_ENV` if needed, but `MODE` is sufficient.

**Backend status indicator:** Ping `GET /health` on component mount using a `useEffect` + `fetch` (or Axios). The `/health` endpoint already exists in `backend/api/main.py` at line 102. It returns `{"status": "ok", ...}`. The Vite proxy routes `/health` to `http://backend:8000`. The indicator should be non-blocking — login form renders regardless.

**Logo:** `frontend/src/assets/` directory does not exist. Use `<span className="text-lg font-bold tracking-widest text-white/80">TWG GLOBAL</span>` with a `{/* TODO: replace with actual logo */}` comment.

**Example backend status hook pattern:**
```jsx
const [backendStatus, setBackendStatus] = useState('checking');
useEffect(() => {
  fetch('/health')
    .then((r) => r.ok ? setBackendStatus('connected') : setBackendStatus('unavailable'))
    .catch(() => setBackendStatus('unavailable'));
}, []);
```

### Pattern 3: Spacing & Typography Consistency Pass

**What:** All in-scope pages should use the same established patterns from `DashboardPage.jsx` and `CompaniesPage.jsx`.

**Established pattern (HIGH confidence — verified in codebase):**
```jsx
// Page wrapper
<div className="space-y-6">
  {/* Page header */}
  <div>
    <h1 className="text-3xl font-semibold">{title}</h1>
    <p className="text-muted-foreground">{subtitle}</p>
  </div>
  {/* Content */}
</div>
```

**Card pattern (SectionCard / plain Card):**
```jsx
<Card>
  <CardHeader>
    <CardTitle>{title}</CardTitle>
    {description && <CardDescription>{description}</CardDescription>}
  </CardHeader>
  <CardContent>{children}</CardContent>
</Card>
```

**In-page row items:**
```jsx
<div className="rounded-xl bg-muted/40 px-4 py-3">...</div>
```

**Audit targets:** `ContactsPage.jsx`, `ContactDetailPage.jsx`, `CompaniesPage.jsx`, `CompanyDetailPage.jsx`, `DealDetailPage.jsx` — ensure all use `text-3xl font-semibold` for h1, `text-muted-foreground` for subtitles, and consistent card/row padding.

### Pattern 4: Dashboard Metrics Wiring

**What:** Confirm stat cards pull live data. `DashboardPage.jsx` already fetches from `getDeals()` and `getContacts()` with a combined `useQuery`. The stat cards are: Open pipeline value, Status mix (open/won/lost counts), 30-day win rate.

**Current metrics (verified in DashboardPage.jsx lines 67-70):**
- `totalOpenValue` — sum of `deal.value` where `deal.status === 'open'` ✓ live
- Status mix badges — counts by status ✓ live
- 30-day win rate — `wonLast30.length / closedLast30.length` ✓ live
- My deals — filtered by `deal.owner_id === user?.id` ✓ live

**D-07 constraint:** Do not add metrics that require DealCounterparty or DealFunding. The current stat cards are acceptable. The polish task is visual: ensure card layout, font sizes, and spacing are consistent — not metric substitution.

**Note:** The page heading says "Revenue command center" — this is generic CRM language. D-07 does not require renaming it. If the planner wants to update it to PE context (e.g., "Deal command center"), that is safe within D-05's scope, but is not required.

### Anti-Patterns to Avoid

- **Do not use `dark:` Tailwind utilities before adding `darkMode: 'class'` to tailwind.config.js.** Without the config key, `dark:` classes are dead code. Add the key first.
- **Do not introduce new design tokens or CSS variables.** D-06 forbids new design language. All classes must come from the existing Tailwind scale and `styles.css` variables.
- **Do not add `setTheme` calls anywhere after the dark lock is implemented.** Removing the toggle from the dropdown is sufficient; no need to guard every potential call site since `setTheme` will be deleted from the store.
- **Do not use `document.documentElement.classList.toggle('dark', ...)` with a dynamic condition.** After the lock, the `.dark` class must be permanent. Use `.add('dark')` unconditionally.
- **Do not use `import.meta.env.VITE_*` for the staging banner** unless you also add the variable to `.env.example`. `import.meta.env.MODE` is zero-config.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dark mode class toggle | Custom theme manager | `document.documentElement.classList.add('dark')` once in `useEffect` | One line; Tailwind handles the rest via CSS vars |
| Health check HTTP call | Custom hook with retries, timeout, cache | Plain `fetch('/health')` in a single `useEffect` | Non-blocking status indicator only; no retry needed |
| Staging env detection | Config file, env service | `import.meta.env.MODE` | Vite built-in, zero configuration |
| Logo placeholder | Image upload flow | Inline text `TWG GLOBAL` with TODO comment | Per discretion; logo file absent from repo |
| Form validation on login | Custom validation logic | `react-hook-form` + `zodResolver` (already in use) | Already present; don't replace or duplicate |
| Spacing/typography tokens | CSS custom properties | Tailwind classes from existing scale | D-06 forbids new design language |

**Key insight:** This phase has zero net-new infrastructure. Every problem is solved by composing primitives that already exist in the project.

---

## Common Pitfalls

### Pitfall 1: Tailwind `dark:` utilities not working without `darkMode: 'class'`

**What goes wrong:** Implementing dark mode using `dark:bg-slate-900` style utilities, only to find they have no effect because Tailwind v3 defaults to `darkMode: 'media'`.
**Why it happens:** The tailwind.config.js in this project has no `darkMode` key. Tailwind v3 defaults to `media` strategy, not `class`.
**How to avoid:** The first task must add `darkMode: 'class'` to `tailwind.config.js`. Confirm by checking that the `.dark` CSS variables in `styles.css` are already structured for class-based activation (they are — `.dark { ... }` block present).
**Warning signs:** `dark:*` classes have no visible effect even after adding the `.dark` class to `html`.

### Pitfall 2: `index.html` body style overriding dark background

**What goes wrong:** The `index.html` file sets an inline body style: `style="margin:0;background:#f3ead9;color:#10212f;font-family:Georgia,serif;"` — this is a warm beige/serif fallback. If the app JS fails to load or takes a moment to apply, the user sees a flash of warm light background.
**Why it happens:** The HTML file has a legacy inline style not updated when the app was built.
**How to avoid:** During the dark mode lock task, update `index.html` body style to `background: #0f172a; color: #e2e8f0;` (slate-950 / slate-200) to match the dark theme. Also remove `font-family: Georgia, serif` since the app uses IBM Plex Sans.
**Warning signs:** Brief flash of beige/serif text on page load before JS hydrates.

### Pitfall 3: `useUIStore` still exposing `setTheme` after toggle removal

**What goes wrong:** Removing the toggle button from the UI but leaving `setTheme` and `theme` in `useUIStore` — any code path that reads `theme` from the store will still function as if light mode is possible.
**Why it happens:** Partial cleanup.
**How to avoid:** Remove both `theme` state and `setTheme` action from `useUIStore`. Remove `localStorage.getItem('nexus-theme')` initialisation. If any component imports `theme` or `setTheme`, those references will break visibly at runtime — which is the correct signal to clean them up.
**Warning signs:** TypeScript/JSX import warnings (none enforced here, but runtime errors if destructured and not found).

### Pitfall 4: LoginPage test breaks after redesign

**What goes wrong:** `LoginPage.test.jsx` tests the form with `screen.getByLabelText(/username/i)`. Adding new elements to the page (banner, status indicator) should not break existing tests — but if the test structure queries for specific CardTitle text that changes, it will fail.
**Why it happens:** The current test queries by label (`/username/i`, `/password/i`) and button role. These are stable. However, if the redesign changes the field label from "Username" to "Email", `getByLabelText(/username/i)` will fail.
**How to avoid:** Retain the `Username` label on the login field (the backend accepts username or email via the same field), or update the test in the same commit if the label changes. Add new tests for the staging banner and backend status indicator.
**Warning signs:** `TestingLibraryElementError: Unable to find a label with the text of /username/i`.

### Pitfall 5: Backend health ping CORS or proxy miss

**What goes wrong:** The health fetch from `LoginPage.jsx` (which renders outside the auth-guarded layout) hits `/health` directly. In dev, Vite proxies `/health` to `http://backend:8000`. In a direct browser context (not via the Vite dev server), this works. But if the frontend is served from a different port than expected, the fetch may fail with a network error.
**Why it happens:** `vite.config.js` already proxies `/health` to `http://backend:8000` — this is correct for dev. In production, the same path must be routed by the reverse proxy (nginx/ALB) to the backend.
**How to avoid:** The status indicator is display-only and non-blocking. A catch clause sets `backendStatus` to `'unavailable'` rather than throwing. This is already in the recommended pattern above.
**Warning signs:** Console network error on `/health` — acceptable as long as the form remains usable.

---

## Code Examples

Verified patterns from codebase inspection:

### Dark Mode Lock (Layout.jsx)
```jsx
// Source: Layout.jsx lines 45-47 (current), simplified to hard-lock
useEffect(() => {
  document.documentElement.classList.add('dark');
}, []);
```

### Staging Banner (LoginPage.jsx)
```jsx
// Source: CONTEXT.md D-03, Vite docs (import.meta.env.MODE)
{import.meta.env.MODE !== 'production' && (
  <div className="absolute inset-x-0 top-0 bg-amber-500/90 py-1.5 text-center text-xs font-semibold text-black">
    {import.meta.env.MODE.toUpperCase()} ENVIRONMENT
  </div>
)}
```

### Backend Status Indicator (LoginPage.jsx)
```jsx
// Source: backend/api/main.py line 102 — GET /health returns {"status": "ok"}
// Vite proxy in vite.config.js line 17 — '/health' -> 'http://backend:8000'
const [backendStatus, setBackendStatus] = useState('checking');
useEffect(() => {
  fetch('/health')
    .then((r) => r.ok ? setBackendStatus('connected') : setBackendStatus('unavailable'))
    .catch(() => setBackendStatus('unavailable'));
}, []);

// Render:
<div className="flex items-center gap-1.5 text-xs">
  <span className={cn('h-2 w-2 rounded-full', backendStatus === 'connected' ? 'bg-green-400' : backendStatus === 'unavailable' ? 'bg-red-400' : 'bg-yellow-400')} />
  <span className="text-muted-foreground">
    Backend: {backendStatus === 'connected' ? 'Connected' : backendStatus === 'unavailable' ? 'Unavailable' : 'Checking...'}
  </span>
</div>
```

### Standard Page Header (consistent pattern)
```jsx
// Source: DashboardPage.jsx lines 73-76, CompaniesPage.jsx lines 18-19
<div className="space-y-6">
  <div>
    <h1 className="text-3xl font-semibold">{pageTitle}</h1>
    <p className="text-muted-foreground">{pageSubtitle}</p>
  </div>
  {/* page content */}
</div>
```

### SectionCard Pattern (Dashboard stat cards)
```jsx
// Source: DashboardPage.jsx lines 17-27
function SectionCard({ title, description, children }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
```

### Tailwind Config Dark Mode Fix
```js
// frontend/tailwind.config.js — add darkMode key
export default {
  darkMode: 'class',   // ADD THIS LINE
  content: ['./index.html', './src/**/*.{js,jsx}'],
  // ... rest unchanged
};
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind `media` dark mode (default) | Must switch to `class` strategy | This phase | Enables programmatic dark lock; makes `dark:` utilities work |
| Light/dark toggle in user menu | Dark-only lock | D-01 | Simplifies `useUIStore`; removes dead state |
| Generic login page (no branding) | Branded login with staging banner + status | D-03 | Matches qa.oscarmackjr.com reference |

**Deprecated/outdated:**
- `theme` state in `useUIStore`: Remove this phase — dark is permanent
- `setTheme` action in `useUIStore`: Remove this phase
- `localStorage` key `nexus-theme`: Stop reading/writing this phase
- `index.html` body inline style `background:#f3ead9; font-family:Georgia,serif`: Stale from initial HTML template; update to dark defaults

---

## Open Questions

1. **Does qa.oscarmackjr.com use the TWG Global wordmark or a logo image?**
   - What we know: `frontend/src/assets/` directory does not exist. No image assets in the frontend source tree.
   - What's unclear: Whether an SVG or PNG logo file should be added to the repo.
   - Recommendation: Use the text placeholder `TWG GLOBAL` as specified in discretion rules. Add a `TODO: replace with actual logo` comment. The planner should surface this as a manual prerequisite if the client wants to provide the logo before the phase ships.

2. **Should the login field label change from "Username" to "Email"?**
   - What we know: The backend `auth.py` accepts either username or email for login (field is named `username` in the OAuth2 form). The current label is "Username".
   - What's unclear: The reference design likely shows "Email" since PE users log in with email addresses.
   - Recommendation: Change label to "Email" in the redesign (more professional for PE context) and update `LoginPage.test.jsx` to match. This is a one-line change in both files.

3. **Nav item "Pipelines" — is it within scope of the spacing pass?**
   - What we know: `PipelinePage.jsx` is not listed in CONTEXT.md's "Screens in scope" list (Login, Dashboard, Contacts list+detail, Companies list+detail, Deals list+detail).
   - Recommendation: Exclude `PipelinePage.jsx` from the spacing pass. Scope is clear from CONTEXT.md.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js / npm | Frontend build | ✓ | (via `make dev`) | — |
| Vite dev server | Frontend hot reload | ✓ | ^5.4.10 | — |
| `GET /health` backend endpoint | LoginPage status indicator | ✓ | Exists at `backend/api/main.py:102` | None needed |
| `frontend/src/assets/` directory | TWG logo image | ✗ | Does not exist | Text placeholder `TWG GLOBAL` |
| `tailwind.config.js` `darkMode: 'class'` | Dark mode utilities | ✗ | Missing (defaults to `media`) | Add in Wave 0 / first task |

**Missing dependencies with no fallback:**
- None blocking

**Missing dependencies with fallback:**
- `frontend/src/assets/` — use text placeholder per discretion rules
- `darkMode: 'class'` in tailwind config — must be added; one-line change

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest ^2.1.8 + Testing Library React ^16.1.0 |
| Config file | `frontend/vite.config.js` (test block, environment: jsdom) |
| Quick run command | `cd frontend && npm test` |
| Full suite command | `cd frontend && npm test` (runs all `__tests__/` files) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| UI-01 | Login page renders with staging banner, branding, status indicator, and sign-in form | unit | `cd frontend && npm test -- LoginPage` | ✅ `__tests__/LoginPage.test.jsx` |
| UI-01 | Login form submits credentials correctly | unit | `cd frontend && npm test -- LoginPage` | ✅ existing test covers this |
| UI-02 | Page header pattern consistent (h1 text-3xl font-semibold) | visual / manual | N/A — visual audit | manual only |
| UI-03 | Dashboard stat cards show non-zero or N/A values from live query | smoke / manual | `cd frontend && npm test -- DashboardPage` (if added) | ❌ Wave 0 gap |

### Sampling Rate

- **Per task commit:** `cd frontend && npm test`
- **Per wave merge:** `cd frontend && npm test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/src/__tests__/LoginPage.test.jsx` — existing tests must be updated for new label/elements after redesign (email label, staging banner render, status indicator render)
- [ ] `frontend/src/__tests__/DashboardPage.test.jsx` — does not exist; add smoke test that renders `DashboardPage` with mocked `useQuery` returning deal/contact data and asserts stat cards render

*(LoginPage.test.jsx exists but needs expansion — does not cover banner or status indicator)*

---

## Project Constraints (from CLAUDE.md)

No `CLAUDE.md` exists in the project root. No additional project-level constraints enforced.

Constraints derived from `CONVENTIONS.md` and `STRUCTURE.md` (treated as equivalent authority):

- Frontend components: `PascalCase.jsx` in `pages/` or `components/`
- No TypeScript — vanilla JSX only; no JSDoc
- No ESLint/Prettier config — no formatter enforced on frontend
- Import order: React ecosystem → form libs → icons/UI → internal API → internal components → hooks → store → utils
- Zustand stores: `useNounStore.js` in `frontend/src/store/`
- UI primitives: stateless, in `frontend/src/components/ui/`, no imports from hooks/store/api
- Page components own their `useQuery`/`useMutation` directly
- Python `from __future__ import annotations` mandatory (not relevant to this phase)
- No new shadcn primitives needed — all required ones already exist

---

## Sources

### Primary (HIGH confidence)
- `frontend/src/pages/LoginPage.jsx` — current login implementation, directly inspected
- `frontend/src/pages/DashboardPage.jsx` — stat card implementations, directly inspected
- `frontend/src/components/Layout.jsx` — theme toggle location and dark mode mechanism, directly inspected
- `frontend/src/store/useUIStore.js` — theme state structure, directly inspected
- `frontend/src/styles.css` — CSS variable definitions for dark/light modes, directly inspected
- `frontend/tailwind.config.js` — confirmed missing `darkMode: 'class'`, directly inspected
- `frontend/vite.config.js` — `/health` proxy confirmed, directly inspected
- `backend/api/main.py` — `GET /health` endpoint confirmed at line 102, directly inspected
- `frontend/index.html` — stale inline body style confirmed, directly inspected
- `frontend/package.json` — all dependency versions confirmed

### Secondary (MEDIUM confidence)
- Tailwind CSS v3 official docs (https://v3.tailwindcss.com/docs/dark-mode) — confirmed default `darkMode` strategy is `media`, not `class`; `class` strategy requires explicit config

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified from package.json
- Architecture: HIGH — all patterns verified from direct codebase inspection
- Pitfalls: HIGH — Tailwind dark mode issue verified against official docs; others derived from direct file inspection

**Research date:** 2026-03-26
**Valid until:** 2026-06-26 (stable stack; no fast-moving dependencies in scope)
