# Phase 9: Data Grids - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Upgrade the three existing list pages (Contacts, Companies, Deals) to compact Salesforce-style data grids. This means: tighter row padding, polished uppercase headers with sort indicator icons, `bg-gray-50` row hover, hover-only action buttons, and a full pagination bar with per-page selector. No new routes, no create/edit flows, no filtering beyond the Deals status filter.

</domain>

<decisions>
## Implementation Decisions

### Sort Indicators
- **D-01:** Sort indicator arrows on column headers are **visual only** — static up/down chevron icons displayed on all headers. No click behavior, no API sort params, no client-side sort logic. Pure cosmetic density matching Salesforce style. Keeps scope tight.

### Row Action Buttons
- **D-02:** A single **"View" button** appears on row hover only (`group-hover:visible` pattern). The name cell already links to detail — "View" is a consistent secondary affordance. No "Edit" button in this phase (edit forms may not exist for all entities yet).

### Columns Per Grid
- **D-03:** Columns confirmed as specified in existing plans:
  - **Contacts:** NAME, COMPANY, TITLE, STAGE, EMAIL, SCORE, OWNER, UPDATED
  - **Companies:** NAME, TYPE, TIER, SECTOR, INDUSTRY, CONTACTS, DEALS, OWNER
  - **Deals:** DEAL, COMPANY, STAGE, VALUE, STATUS, CLOSE DATE, OWNER, DAYS

### Deals Status Filter
- **D-04:** Include a status filter bar on the Deals page (All / Open / Won / Lost). Filter passes `?status=` param to the API. Sits above the DataGrid, below the page header. Immediately useful for deal teams scanning open deals.

### Row Density & Styling
- **D-05:** Row padding changes from current `py-3` to `py-2` across all three grids (GRID-01, GRID-02, GRID-03).
- **D-06:** Column headers: `uppercase text-xs text-gray-500 tracking-wide` with `border-b` separator. Replace current `font-medium py-3 bg-muted/50` headers.
- **D-07:** Row hover changes from current `hover:bg-muted/30` to `hover:bg-gray-50` (consistent with sidebar nav hover established in Phase 8).

### Pagination Bar
- **D-08:** Pagination bar is **always visible** (even when pages === 1) — shows current page, total pages, prev/next buttons, and a records-per-page selector. Per-page options: 10 / 25 / 50 / 100, default 25.
- **D-09:** Current implementation hides pagination when `pages <= 1` — this should be replaced with the always-visible Pagination component.

### Shared Component Architecture
- **D-10:** A shared `DataGrid` component (`frontend/src/components/DataGrid.jsx`) takes `columns` and `data` props, renders the styled table. A shared `Pagination` component (`frontend/src/components/Pagination.jsx`) is rendered inside/below DataGrid. All three list pages consume these shared components.

### Claude's Discretion
- Exact Tailwind classes for the sort indicator icon (ChevronUpDown, ArrowUpDown, or similar Lucide icon)
- Whether per-page selector resets to page 1 on change (yes, it should — planner can handle)
- Exact layout/spacing of the Deals status filter tabs

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` — Phase 9 goal, success criteria (GRID-01 through GRID-06)
- `.planning/REQUIREMENTS.md` — GRID-01, GRID-02, GRID-03, GRID-04, GRID-05, GRID-06 definitions

### Existing implementations to update
- `frontend/src/pages/ContactsPage.jsx` — current basic table, needs DataGrid migration
- `frontend/src/pages/CompaniesPage.jsx` — current basic table, needs DataGrid migration
- `frontend/src/pages/DealsPage.jsx` — current basic table, needs DataGrid migration + status filter

### Existing patterns from prior phases
- `.planning/phases/08-login-banner-sidebar/08-CONTEXT.md` — D-08/D-09 establish `hover:bg-gray-50` and `border-[#1a3868]` hover/active patterns
- `frontend/src/components/Layout.jsx` — sidebar nav with `hover:bg-gray-50` pattern to stay consistent with

No external ADRs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/pages/ContactsPage.jsx` — exists with basic table (py-3, font-medium headers, hover:bg-muted/30). Migration target.
- `frontend/src/pages/CompaniesPage.jsx` — same pattern as Contacts. Migration target.
- `frontend/src/pages/DealsPage.jsx` — same pattern + STATUS_COLORS badge map. Migration target.
- `frontend/src/components/ui/` — shadcn/ui Table primitives likely available for DataGrid to wrap
- `@/lib/utils` — `formatDate`, `formatCurrency` already imported in list pages

### Established Patterns
- Hover uses `hover:bg-gray-50` per Phase 8 sidebar (not `hover:bg-muted/30` which the old list pages use)
- Navy `#1a3868` is the brand color via `--color-brand` / `text-primary` CSS variables
- `group` + `group-hover:visible` is the established hover-reveal pattern (used in plan 01 spec)

### Integration Points
- `frontend/src/main.jsx` — routes for `/contacts`, `/companies`, `/deals` need to be confirmed/added
- `frontend/src/components/Layout.jsx` — Deals nav link needs to be added under DEALS group
- `frontend/src/api/deals.js` — missing module (currently breaking DashboardPage/DealDetailPage imports); plan 01 creates it

</code_context>

<specifics>
## Specific Ideas

- The "DAYS" column on Deals grid shows days since deal was created or days to close — planner to determine from data available on the deal object.
- Deals STATUS_COLORS badge map already exists in current DealsPage.jsx (`open: blue, won: green, lost: red`) — reuse this in the DataGrid implementation.
- Records-per-page selector changes current `size: 25` hardcode to a user-controllable state variable.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-data-grids*
*Context gathered: 2026-04-06*
