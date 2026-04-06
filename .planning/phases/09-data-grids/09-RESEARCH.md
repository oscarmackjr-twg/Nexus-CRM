# Phase 9: Data Grids - Research

**Researched:** 2026-04-06
**Domain:** React table UI, Tailwind compact density, client-side pagination, shadcn/ui Table component
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GRID-01 | Contacts list view uses compact row density (`py-2`, `text-sm`) | Contacts list page does not yet exist — must be created as a new page component |
| GRID-02 | Companies list view uses compact row density (`py-2`, `text-sm`) | Companies list page does not yet exist — must be created as a new page component |
| GRID-03 | Deals list view uses compact row density (`py-2`, `text-sm`) | Deals list page does not yet exist — must be created as a new page component |
| GRID-04 | Column headers uppercase, `text-xs`, `text-gray-500`, `tracking-wide`, bottom border, sort indicators | shadcn/ui `<TableHead>` component is the base; override styling and add sort click handlers |
| GRID-05 | Row hover highlights `bg-gray-50`; row action buttons visible on hover only | Tailwind `group`/`group-hover` pattern on `<TableRow>` |
| GRID-06 | Pagination bar shows page count, prev/next, records-per-page selector in TWG style | Backend already returns `total`, `page`, `size`, `pages` in all three list schemas — full pagination is wired with zero backend changes |
</phase_requirements>

---

## Summary

Phase 9 is a pure frontend phase: all three list views (Contacts, Companies, Deals) do not yet exist as page components. The sidebar links to `/contacts`, `/companies`, and (implicitly) a deals list route, but no corresponding list page files are present in `frontend/src/pages/`. The work is to create three new page components from scratch — not to refactor existing ones.

The backend is already pagination-ready. All three list endpoints (`GET /contacts/`, `GET /companies/`, `GET /deals/`) accept `page` and `size` query parameters and return `{ items, total, page, size, pages }`. No backend changes are required for this phase.

The project uses shadcn/ui's `<Table>` / `<TableHeader>` / `<TableHead>` / `<TableBody>` / `<TableRow>` / `<TableCell>` components (confirmed in `AdminPage.jsx` which already uses them for the reference data grid). Those components are available without installation. The recommended approach is a single shared `DataGrid` component that all three list pages consume, parameterised with column definitions, a data query result, and sort/pagination state.

**Primary recommendation:** Build one shared `DataGrid` component with Salesforce-density styling, then create three thin list page wrappers (ContactsPage, CompaniesPage, DealsPage) that pass column configs and query params to it.

---

## Project Constraints (from CLAUDE.md)

No `CLAUDE.md` found at project root. Authoritative conventions are in `.planning/codebase/CONVENTIONS.md`.

Directives extracted:

- React components: `PascalCase.jsx` — new files must follow this pattern (e.g., `ContactsPage.jsx`, `DataGrid.jsx`)
- Shared components: named exports (`export function DataGrid(...)`) under `frontend/src/components/`
- Page components: default exports from `frontend/src/pages/`
- Accept `className` prop and merge with `cn()` from `@/lib/utils`
- Data fetching: `useQuery` / `useMutation` from `@tanstack/react-query` owned directly by page components
- Query key pattern: arrays with domain prefix — `['contacts']`, `['companies']`, `['deals']`
- No TypeScript; vanilla JSX only
- No JSDoc or TSDoc comments
- Import order: React ecosystem first, then lucide-react, sonner, internal API, components, hooks, stores, utils
- Mutation errors: `onError: (error) => toast.error(error.response?.data?.detail || 'Fallback message')`
- No dark mode — `Layout.jsx` explicitly removes `dark` class on mount
- Brand navy: `#1a3868` (also available as `--color-brand` CSS var and Tailwind config `primary` = `217 60% 25%`)
- Font: Montserrat (loaded via Google Fonts in `index.html`)
- `from __future__ import annotations` required in backend files when modified (companies.py, contacts.py, deals.py are in the list — but NO backend changes are needed for this phase)

---

## 1. Current State Analysis

### 1.1 List Views — Status

**Finding: None of the three list views exist as page components.**

The sidebar in `Layout.jsx` links to `/contacts`, `/companies`, and deals appear to be accessible via `/pipelines` / `/boards` from the navigation — but there is no dedicated deals list route registered. Only these six page files exist:

```
frontend/src/pages/AdminPage.jsx         — exists, fully implemented
frontend/src/pages/CompanyDetailPage.jsx — exists, fully implemented
frontend/src/pages/ContactDetailPage.jsx — exists, fully implemented
frontend/src/pages/DashboardPage.jsx     — exists, fully implemented
frontend/src/pages/DealDetailPage.jsx    — exists, fully implemented
frontend/src/pages/LoginPage.jsx         — exists, fully implemented
```

There is no `ContactsPage.jsx`, `CompaniesPage.jsx`, or `DealsPage.jsx`. The routes `/contacts`, `/companies`, and `/deals` are navigation targets in `Layout.jsx` and are used by `getDeals()` in `DashboardPage.jsx`, but they have no corresponding list-view page.

### 1.2 Routing

`frontend/src/main.jsx` is referenced by `index.html` but not tracked in git (confirmed missing from glob and noted in `CONCERNS.md`). The routing configuration is therefore not directly readable. However, from `Layout.jsx` we know the navigation expects:

- `/contacts` → contacts list
- `/companies` → companies list
- `/pipelines` and `/boards` → pipeline/board views (different feature area)

No `/deals` list link exists in the sidebar — deals are accessed via Pipelines/Boards. For this phase, a `/deals` route will need to be registered in `main.jsx` as well.

### 1.3 Existing Table Component Usage

`AdminPage.jsx` uses shadcn/ui `<Table>` for the reference data grid:

```jsx
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
```

This confirms:
- The `table` shadcn/ui component is installed and working
- The project's shadcn/ui source files are not tracked in git (they live in `node_modules` or a separate location not in the repo) — confirmed by glob finding no files under `frontend/src/components/ui/`
- The component is used at `AdminPage` with basic styling, no sort indicators, no hover actions, no pagination

AdminPage's table is not compact — rows use default shadcn padding. That is the before-state we're replacing in the new list pages.

### 1.4 API Modules

| Entity | API Module | List Function | Pagination Params |
|--------|-----------|---------------|-------------------|
| Contacts | `frontend/src/api/contacts.js` | `getContacts(params)` | `page`, `size` passed via `params` object |
| Companies | `frontend/src/api/companies.js` | `getCompanies(params)` | `page`, `size` passed via `params` object |
| Deals | NOT PRESENT (`@/api/deals` is missing) | `getDeals(params)` — referenced but 404s | Needs file creation |

`@/api/deals` is imported by `DashboardPage.jsx` and `DealDetailPage.jsx` (which also imports `getDeal`, `getDealActivities`, `logActivity`, `scoreDeal`, `updateDeal`), but the file `frontend/src/api/deals.js` does not exist on disk. This is a pre-existing gap documented in `CONCERNS.md`. This phase must create `frontend/src/api/deals.js`.

### 1.5 Backend Pagination — Fully Ready

All three list routes and schemas already support pagination with no changes needed:

**Contacts** (`backend/api/routes/contacts.py` + `backend/schemas/contacts.py`):
- Route: `GET /contacts/?page=1&size=25&search=...`
- Response schema: `ContactListResponse { items: list[ContactResponse], total: int, page: int, size: int, pages: int }`
- No sort param yet (sort is a gap)

**Companies** (`backend/api/routes/companies.py` + `backend/schemas/companies.py`):
- Route: `GET /companies/?page=1&size=25&search=...`
- Response: `CompanyListResponse { items, total, page, size, pages }`
- No sort param yet

**Deals** (`backend/api/routes/deals.py` + `backend/schemas/deals.py`):
- Route: `GET /deals/?page=1&size=25&search=...&status=open`
- Response: `DealListResponse { items, total, page, size, pages }`
- No sort param yet

**Sort conclusion:** No backend endpoint currently accepts a `sort_by` or `order` parameter. Client-side sorting of the current page's items is the correct approach for this phase to avoid backend changes.

### 1.6 Data Shape — What Fields Exist for List Display

**ContactResponse** — fields useful in list view:
- `id`, `first_name`, `last_name`, `email`, `phone`, `title`, `company_name` (resolved), `lifecycle_stage`, `lead_score`, `owner_name` (resolved), `tags`, `is_archived`, `created_at`, `updated_at`, `contact_type_label` (resolved), `related_deal_count`

**CompanyResponse** — fields useful in list view:
- `id`, `name`, `domain`, `industry`, `size_range`, `annual_revenue`, `website`, `owner_name` (resolved), `company_type_label` (resolved), `tier_label` (resolved), `sector_label` (resolved), `tags`, `is_archived`, `linked_contacts_count`, `open_deals_count`, `created_at`, `updated_at`

**DealResponse** — fields useful in list view:
- `id`, `name`, `pipeline_name`, `stage_name`, `value`, `currency`, `status`, `owner_name` (resolved), `company_name` (resolved), `contact_name` (resolved), `expected_close_date`, `days_in_stage`, `is_rotting`, `tags`, `created_at`, `updated_at`, `transaction_type_label` (resolved), `fund_name` (resolved)

---

## 2. Gap Analysis

| Gap | Severity | Resolution |
|-----|----------|-----------|
| `ContactsPage.jsx` does not exist | BLOCKING | Create new file |
| `CompaniesPage.jsx` does not exist | BLOCKING | Create new file |
| `DealsPage.jsx` does not exist | BLOCKING | Create new file |
| `frontend/src/api/deals.js` does not exist | BLOCKING | Create new file (needed by DealsPage and already referenced by existing pages) |
| No `/deals` route in `main.jsx` | BLOCKING | Add route to routing config |
| No shared `DataGrid` component | DESIGN CHOICE | Create `frontend/src/components/DataGrid.jsx` |
| No `Pagination` component | DESIGN CHOICE | Create `frontend/src/components/Pagination.jsx` |
| Backend has no sort param | ACCEPTED GAP | Client-side sort of current page items; note in plan |
| AdminPage table uses default (non-compact) styling | OUT OF SCOPE | Phase 9 does not touch AdminPage |

---

## 3. Implementation Approach

### 3.1 Shared Component vs Per-Page Refactor

**Recommendation: Build a shared `DataGrid` component.**

Rationale:
- Three pages need identical structure: compact headers, hover states, row actions, pagination bar
- Any per-page approach triples the code and means future style changes (e.g., density tweaks) must be made in three places
- The AdminPage already demonstrates that one table component serves many data shapes via column config
- Conventions require shared components in `frontend/src/components/` as named exports

The `DataGrid` component receives:
- `columns` — array of `{ key, label, render?, sortable? }` column definitions
- `data` — the current page's `items` array
- `total`, `page`, `size`, `pages` — pagination metadata from the API response
- `onPageChange(newPage)` — callback to update query param
- `onSizeChange(newSize)` — callback to update page size query param
- `isLoading` — show skeleton rows
- Optional: `onRowClick(row)` — navigate to detail page

Sorting state (sort column + direction) lives inside `DataGrid` as local `useState`, since it is UI-only (client-side sort of current page).

### 3.2 Tailwind Density Pattern

Salesforce-density is achieved by overriding shadcn/ui's default table cell padding:

```jsx
// Header cells
<TableHead className="py-2 px-3 text-xs font-semibold uppercase tracking-wide text-gray-500 border-b border-gray-200">
  {col.label}
  {col.sortable && <SortIcon direction={sortState[col.key]} />}
</TableHead>

// Data cells
<TableCell className="py-2 px-3 text-sm text-gray-900">
  {col.render ? col.render(row) : row[col.key] ?? '—'}
</TableCell>
```

Row hover uses Tailwind `group` on `<TableRow>`:

```jsx
<TableRow
  key={row.id}
  className="group hover:bg-gray-50 cursor-pointer"
  onClick={() => onRowClick?.(row)}
>
  {/* ... cells ... */}
  {/* Row actions — hidden until hover */}
  <TableCell className="py-2 px-3">
    <div className="invisible group-hover:visible flex gap-1">
      <Button size="sm" variant="ghost" asChild>
        <Link to={`/${entity}/${row.id}`}>View</Link>
      </Button>
    </div>
  </TableCell>
</TableRow>
```

### 3.3 Pagination Bar Pattern

A standalone `Pagination` component renders below the table:

```jsx
// Props: page, pages, total, size, onPageChange, onSizeChange
<div className="flex items-center justify-between px-3 py-2 border-t border-gray-200 text-sm text-gray-600">
  <span>{total} records &bull; Page {page} of {pages}</span>
  <div className="flex items-center gap-3">
    <select
      value={size}
      onChange={(e) => onSizeChange(Number(e.target.value))}
      className="text-sm border border-gray-200 rounded px-2 py-1"
    >
      {[10, 25, 50, 100].map((n) => <option key={n} value={n}>{n} per page</option>)}
    </select>
    <Button
      variant="outline" size="sm"
      disabled={page <= 1}
      onClick={() => onPageChange(page - 1)}
    >
      Previous
    </Button>
    <Button
      variant="outline" size="sm"
      disabled={page >= pages}
      onClick={() => onPageChange(page + 1)}
    >
      Next
    </Button>
  </div>
</div>
```

TWG styling cues: `border-[#1a3868]` active state on prev/next buttons when navigating, consistent with the nav active color.

### 3.4 Column Definitions Per Entity

**Contacts columns (compact view):**

| Column Key | Label | Notes |
|-----------|-------|-------|
| `name` | NAME | Rendered: `${first_name} ${last_name}`, link to `/contacts/:id` |
| `company_name` | COMPANY | `row.company_name ?? '—'` |
| `title` | TITLE | `row.title ?? '—'` |
| `lifecycle_stage` | STAGE | Badge component |
| `email` | EMAIL | `row.email ?? '—'` |
| `lead_score` | SCORE | `row.lead_score` |
| `owner_name` | OWNER | `row.owner_name ?? '—'` |
| `updated_at` | UPDATED | `formatDate(row.updated_at)` |

**Companies columns (compact view):**

| Column Key | Label | Notes |
|-----------|-------|-------|
| `name` | NAME | Link to `/companies/:id` |
| `company_type_label` | TYPE | `row.company_type_label ?? '—'` |
| `tier_label` | TIER | `row.tier_label ?? '—'` |
| `sector_label` | SECTOR | `row.sector_label ?? '—'` |
| `industry` | INDUSTRY | `row.industry ?? '—'` |
| `linked_contacts_count` | CONTACTS | `row.linked_contacts_count ?? 0` |
| `open_deals_count` | DEALS | `row.open_deals_count ?? 0` |
| `owner_name` | OWNER | `row.owner_name ?? '—'` |

**Deals columns (compact view):**

| Column Key | Label | Notes |
|-----------|-------|-------|
| `name` | DEAL | Link to `/deals/:id` |
| `company_name` | COMPANY | `row.company_name ?? '—'` |
| `stage_name` | STAGE | |
| `value` | VALUE | `formatCurrency(row.value, row.currency)` |
| `status` | STATUS | Badge with color coding: open=blue, won=green, lost=gray |
| `expected_close_date` | CLOSE DATE | `formatDate(row.expected_close_date) ?? '—'` |
| `owner_name` | OWNER | `row.owner_name ?? '—'` |
| `days_in_stage` | DAYS | `row.days_in_stage` |

### 3.5 State Management for Pagination

Page and size state lives in each list page component as `useState`. Changing page calls `queryClient.invalidateQueries` or simply changes the query key (TanStack Query re-fetches when query key changes):

```jsx
const [page, setPage] = useState(1);
const [size, setSize] = useState(25);

const { data, isLoading } = useQuery({
  queryKey: ['contacts', { page, size }],
  queryFn: () => getContacts({ page, size }),
  keepPreviousData: true,  // prevents flicker on page change
});
```

`keepPreviousData: true` is the critical option — it keeps the previous page visible while the next page loads, preventing a jarring white flash.

### 3.6 Sort Implementation (Client-Side)

Since the backend has no sort parameters, sort is applied to the current `data.items` array inside `DataGrid` via `useMemo`:

```jsx
const [sortKey, setSortKey] = useState(null);
const [sortDir, setSortDir] = useState('asc');

const sortedRows = useMemo(() => {
  if (!sortKey) return rows;
  return [...rows].sort((a, b) => {
    const av = a[sortKey] ?? '';
    const bv = b[sortKey] ?? '';
    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return sortDir === 'asc' ? cmp : -cmp;
  });
}, [rows, sortKey, sortDir]);
```

Sort indicators: Lucide `ChevronUp` / `ChevronDown` icons inline in `<TableHead>`.

---

## 4. Backend Changes Needed

**None.** All three endpoints already:
- Accept `page` and `size` params
- Return `total`, `page`, `size`, `pages` in the response schema
- Return resolved label fields (e.g., `company_type_label`, `tier_label`, `transaction_type_label`)

The only missing backend-adjacent item is `frontend/src/api/deals.js`, which is a frontend API module that must be created to expose `getDeals`, `getDeal`, `getDealActivities`, `logActivity`, `scoreDeal`, `updateDeal` (the latter four are already assumed to exist by `DealDetailPage.jsx`).

---

## 5. Component Breakdown

### New Files to Create

```
frontend/src/
├── api/
│   └── deals.js                        NEW — API module for all deal operations
├── components/
│   ├── DataGrid.jsx                    NEW — shared compact table component
│   └── Pagination.jsx                  NEW — pagination bar component
└── pages/
    ├── ContactsPage.jsx                NEW — contacts list view
    ├── CompaniesPage.jsx               NEW — companies list view
    └── DealsPage.jsx                   NEW — deals list view
```

Also requires updating (not creating):
- `frontend/src/main.jsx` — add routes for `/contacts`, `/companies`, `/deals` (the file currently exists as a ghost but must be updated once it is tracked/created in the project setup)

**Note on `main.jsx`:** Per `CONCERNS.md`, `frontend/src/main.jsx` does not exist in git. This phase will need to verify whether it has been created as part of prior work (the app presumably runs), or create it if absent. The routes for `/contacts`, `/companies`, `/deals` must be added regardless.

### Component Interfaces

**`DataGrid` (shared):**
```jsx
export function DataGrid({
  columns,        // { key, label, sortable?, render?(row) }[]
  data,           // items[] from API response
  total,          // number
  page,           // number
  pages,          // number
  size,           // number
  isLoading,      // boolean
  onPageChange,   // (newPage: number) => void
  onSizeChange,   // (newSize: number) => void
  onRowClick,     // (row) => void — optional
  className,      // string — optional
})
```

**`Pagination` (shared):**
```jsx
export function Pagination({
  page,
  pages,
  total,
  size,
  onPageChange,
  onSizeChange,
})
```

**`ContactsPage` (page):**
```jsx
// Owns: page state, size state, search state
// Calls: getContacts({ page, size, search })
// Query key: ['contacts', { page, size, search }]
// Renders: DataGrid with contacts column config
```

**`CompaniesPage` (page):**
```jsx
// Owns: page state, size state, search state
// Calls: getCompanies({ page, size, search })
// Query key: ['companies', { page, size, search }]
// Renders: DataGrid with companies column config
```

**`DealsPage` (page):**
```jsx
// Owns: page state, size state, search state, status filter state
// Calls: getDeals({ page, size, search, status })
// Query key: ['deals', { page, size, search, status }]
// Renders: DataGrid with deals column config
```

---

## 6. Architecture Patterns

### Recommended Project Structure Change

```
frontend/src/
├── api/
│   ├── client.js            (existing)
│   ├── companies.js         (existing)
│   ├── contacts.js          (existing)
│   ├── deals.js             NEW
│   ├── ...
├── components/
│   ├── DataGrid.jsx         NEW — shared
│   ├── Layout.jsx           (existing)
│   ├── Pagination.jsx       NEW — shared
│   ├── RefSelect.jsx        (existing)
│   ├── StagingBanner.jsx    (existing)
│   └── ui/                  (shadcn/ui, source not in git)
├── pages/
│   ├── AdminPage.jsx        (existing)
│   ├── CompaniesPage.jsx    NEW
│   ├── CompanyDetailPage.jsx (existing)
│   ├── ContactDetailPage.jsx (existing)
│   ├── ContactsPage.jsx     NEW
│   ├── DashboardPage.jsx    (existing)
│   ├── DealDetailPage.jsx   (existing)
│   ├── DealsPage.jsx        NEW
│   └── LoginPage.jsx        (existing)
```

### Pattern: Sort Toggle Header

Column headers with `sortable: true` in the column config render a sort indicator and register a click handler:

```jsx
function SortIndicator({ column, sortKey, sortDir }) {
  if (column.key !== sortKey) return <ChevronsUpDown className="h-3 w-3 text-gray-400 ml-1" />;
  return sortDir === 'asc'
    ? <ChevronUp className="h-3 w-3 ml-1" />
    : <ChevronDown className="h-3 w-3 ml-1" />;
}
```

### Anti-Patterns to Avoid

- **Duplicating grid markup in each page:** Putting `<Table>` JSX directly in ContactsPage, CompaniesPage, DealsPage would force three-way changes for any future style update. Use the shared `DataGrid`.
- **Using `useSearchParams` for pagination:** Query string pagination is optional; `useState` is simpler and sufficient since deep-linking to a specific page is not a requirement for this phase.
- **Fetching all records and paginating client-side:** The backend paginates — always pass `page` and `size` to the API. Never `getContacts({ size: 10000 })`.
- **Removing `keepPreviousData: true`:** Without this TanStack Query option, page transitions flash a loading skeleton. Include it.
- **Calling `getDeals` without creating `deals.js`:** `DealDetailPage.jsx` already imports from `@/api/deals` — creating the file fixes both that broken import and enables DealsPage.

---

## 7. Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table markup | Raw `<table>` HTML | shadcn/ui `<Table>` / `<TableHead>` / `<TableRow>` / `<TableCell>` | Accessibility, responsive baseline, consistent border/color tokens already set |
| Sort icon | Custom SVG arrows | Lucide `ChevronUp`, `ChevronDown`, `ChevronsUpDown` | Already imported in other pages; consistency |
| Button components | `<button>` with inline classes | shadcn/ui `<Button size="sm" variant="outline">` | Consistent focus rings, hover states, disabled states |
| Loading skeleton | Spinner or inline CSS | shadcn/ui `<Skeleton>` (already used across all pages) | Matches rest of app |
| Toast notifications | `alert()` or custom modal | `toast.error()` / `toast.success()` from `sonner` | Project-wide pattern |
| Currency/date formatting | `new Intl.NumberFormat(...)` inline | `formatCurrency`, `formatDate` from `@/lib/utils` | Already used on DealDetailPage, DashboardPage |

---

## 8. Common Pitfalls

### Pitfall 1: Missing `deals.js` API Module

**What goes wrong:** `DealsPage.jsx` imports `getDeals` from `@/api/deals`, but the file doesn't exist. The page component errors out immediately. Worse, `DealDetailPage.jsx` and `DashboardPage.jsx` already import from this missing file — creating it fixes multiple existing bugs simultaneously.

**Why it happens:** The deals API module was never created (documented in `CONCERNS.md`).

**How to avoid:** Create `frontend/src/api/deals.js` as the very first task of this phase before any page work.

**Warning signs:** `Module not found: '@/api/deals'` error in browser console.

### Pitfall 2: Route Not Registered

**What goes wrong:** `ContactsPage`, `CompaniesPage`, `DealsPage` are created but the user navigates to `/contacts` and gets a blank page or 404.

**Why it happens:** `main.jsx` must be updated to register the new routes. This file is not tracked in git and is listed as a ghost file in `CONCERNS.md`.

**How to avoid:** Verify `main.jsx` exists and add the three routes. If `main.jsx` doesn't exist yet, creating it is a prerequisite.

**Warning signs:** Blank `<main>` content area with no error, or React Router "no route matched" warning.

### Pitfall 3: `keepPreviousData` Omitted

**What goes wrong:** When the user clicks "Next page", the table briefly goes blank (shows skeleton rows) before the new page appears.

**Why it happens:** Without `keepPreviousData: true`, TanStack Query clears the data on every new query key change.

**How to avoid:** Always include `keepPreviousData: true` in page list queries.

### Pitfall 4: Sort Resets on Page Navigation

**What goes wrong:** User sorts by column A, navigates to page 2, and the sort is gone.

**Why it happens:** Sort state is local to `DataGrid`. When `DataGrid` unmounts (because the query re-runs and React reconciles a different key), sort state is lost.

**How to avoid:** Keep sort state in the page component (not inside `DataGrid`), and pass `sortKey` / `sortDir` / `onSort` as props to `DataGrid`. Alternatively, accept this limitation since sort is client-side only and document it.

### Pitfall 5: `null` Field Display

**What goes wrong:** Many fields in all three schemas are `str | None`. Rendering `{row.company_name}` for a null value renders nothing — an empty cell with no visual indicator.

**Why it happens:** React renders `null` and `undefined` as nothing.

**How to avoid:** Use `row.company_name ?? '—'` consistently. The `DataGrid` `render` function should default to `row[col.key] ?? '—'` when no custom renderer is provided (satisfies DETAIL-03 requirement pattern too).

### Pitfall 6: shadcn/ui `<Table>` Default Padding Too Large

**What goes wrong:** Using `<TableCell>` without overriding padding produces default shadcn spacing, which is not compact.

**Why it happens:** shadcn/ui `table.jsx` applies its own `px-4 py-3` (or similar) defaults.

**How to avoid:** Explicitly pass `className="py-2 px-3 text-sm"` on every `<TableCell>` and `<TableHead>`. Or, if the project's shadcn `table.jsx` source is accessible, override the defaults there globally. Since source is not in git, override per-call.

---

## 9. Plan Structure Recommendation

This phase divides cleanly into three plan files:

**09-01: Foundation — deals.js API + DataGrid + Pagination components**
- Create `frontend/src/api/deals.js` (fixes existing broken imports)
- Create `frontend/src/components/DataGrid.jsx`
- Create `frontend/src/components/Pagination.jsx`
- Vitest smoke test for `DataGrid` rendering columns and rows
- This plan is the dependency for 09-02 and 09-03

**09-02: List Pages — ContactsPage + CompaniesPage**
- Create `frontend/src/pages/ContactsPage.jsx`
- Create `frontend/src/pages/CompaniesPage.jsx`
- Add `/contacts` and `/companies` routes to `main.jsx`
- Satisfies GRID-01, GRID-02, GRID-04, GRID-05, GRID-06 for these two entities

**09-03: Deals List Page**
- Create `frontend/src/pages/DealsPage.jsx`
- Add `/deals` route to `main.jsx`
- Satisfies GRID-03 for deals, and GRID-04, GRID-05, GRID-06 for deals
- Separate plan because Deals has an additional status filter and the column set is meaningfully different

**Rationale for 3 plans vs 2:** Separating the shared foundation from the pages enables the planner to verify DataGrid works before building on it. Deals is separated from Contacts/Companies because it requires creating the `deals.js` API module (which 09-01 handles) and has a distinct column schema with status filtering.

---

## 10. Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest (configured in `frontend/vite.config.js`) |
| Config file | Inline in `frontend/vite.config.js` (`test:` block) |
| Quick run command | `cd frontend && npm test` |
| Full suite command | `cd frontend && npm test` (same — Vitest runs all specs) |

### Phase Requirements — Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GRID-01 | Contacts list renders compact `py-2 text-sm` rows | smoke / render | `cd frontend && npm test -- ContactsPage` | No — Wave 0 |
| GRID-02 | Companies list renders compact `py-2 text-sm` rows | smoke / render | `cd frontend && npm test -- CompaniesPage` | No — Wave 0 |
| GRID-03 | Deals list renders compact `py-2 text-sm` rows | smoke / render | `cd frontend && npm test -- DealsPage` | No — Wave 0 |
| GRID-04 | Column headers have uppercase/tracking-wide/text-xs classes | unit | `cd frontend && npm test -- DataGrid` | No — Wave 0 |
| GRID-05 | Row action buttons invisible by default, visible on hover | manual | — | Manual verification in browser |
| GRID-06 | Pagination bar shows prev/next/per-page selector | unit | `cd frontend && npm test -- Pagination` | No — Wave 0 |

Note: GRID-05 (hover visibility) cannot be reliably tested with jsdom because CSS `group-hover:` utility is Tailwind — jsdom does not compute CSS. This must be verified manually in the browser.

### Sampling Rate

- **Per task commit:** `cd frontend && npm test`
- **Per wave merge:** `cd frontend && npm test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/src/__tests__/DataGrid.test.jsx` — covers GRID-04, GRID-06
- [ ] `frontend/src/__tests__/ContactsPage.test.jsx` — smoke for GRID-01
- [ ] `frontend/src/__tests__/CompaniesPage.test.jsx` — smoke for GRID-02
- [ ] `frontend/src/__tests__/DealsPage.test.jsx` — smoke for GRID-03
- [ ] `frontend/src/__tests__/Pagination.test.jsx` — covers GRID-06

---

## 11. Environment Availability

Step 2.6: SKIPPED — this phase is purely frontend code changes with no external tool dependencies beyond the existing React/Vite/Node stack (already confirmed operational by prior phases).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| shadcn/ui Table | project-installed | `<Table>`, `<TableHead>`, `<TableRow>`, `<TableCell>` primitives | Already used in AdminPage; project-standard table base |
| @tanstack/react-query | project-installed | `useQuery` with `keepPreviousData` | All pages use it; handles caching and stale-while-revalidate |
| Tailwind CSS | project-installed | Compact utility classes: `py-2 px-3 text-sm text-xs uppercase tracking-wide` | Project-wide styling system |
| lucide-react | project-installed | `ChevronUp`, `ChevronDown`, `ChevronsUpDown` sort icons | Already imported across pages |

### No New Dependencies Required

This entire phase requires zero new npm packages. All needed primitives (Table, Button, Skeleton, Badge) are already installed as shadcn/ui components.

---

## Sources

### Primary (HIGH confidence)

- `backend/api/routes/contacts.py` — confirmed `page`, `size` params, `ContactListResponse` return type
- `backend/api/routes/companies.py` — confirmed `page`, `size` params, `CompanyListResponse` return type
- `backend/api/routes/deals.py` — confirmed `page`, `size` params, `DealListResponse` return type
- `backend/schemas/contacts.py` — confirmed `ContactListResponse` has `total`, `page`, `size`, `pages`
- `backend/schemas/companies.py` — confirmed `CompanyListResponse` has `total`, `page`, `size`, `pages`
- `backend/schemas/deals.py` — confirmed `DealListResponse` has `total`, `page`, `size`, `pages`
- `frontend/src/pages/AdminPage.jsx` — confirmed shadcn/ui `<Table>` components are installed and working
- `frontend/src/api/contacts.js` — confirmed `getContacts(params)` passes params as query params
- `frontend/src/api/companies.js` — confirmed `getCompanies(params)` passes params as query params
- `.planning/codebase/STACK.md` — confirmed shadcn/ui, TanStack Query, Tailwind CSS, Lucide
- `.planning/codebase/CONVENTIONS.md` — confirmed component patterns, import order, naming rules
- `.planning/codebase/CONCERNS.md` — confirmed missing files: `deals.js`, `main.jsx`, `ContactsPage`, `CompaniesPage`, `DealsPage`

### Secondary (MEDIUM confidence)

- TanStack Query `keepPreviousData` option — well-established pattern for pagination, confirmed in TanStack Query v4/v5 docs; exact option name may differ between v4 (`keepPreviousData: true`) and v5 (`placeholderData: keepPreviousData` import) — verify against installed version
- Tailwind `group` / `group-hover:` pattern for row hover visibility — standard Tailwind utility, documented at tailwindcss.com

---

## Metadata

**Confidence breakdown:**
- Current state analysis: HIGH — file contents directly inspected
- Backend pagination: HIGH — schemas and routes directly inspected
- Missing files: HIGH — confirmed by glob and CONCERNS.md
- Standard stack: HIGH — AdminPage already demonstrates the Table component works
- Column choices: MEDIUM — reasonable selection based on schema fields; final column set is at implementer discretion
- Sort approach (client-side): HIGH — backend routes have no sort params; client-side is the only option without backend changes
- `keepPreviousData` TanStack Query version: MEDIUM — v4 vs v5 syntax difference; verify

**Research date:** 2026-04-06
**Valid until:** 2026-05-06 (stable technology choices; shadcn/ui and TanStack Query APIs are stable)
