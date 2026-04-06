# Phase 10: Detail Page Polish - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Polish the UI of three existing detail pages — ContactDetailPage, CompanyDetailPage, and DealDetailPage — for visual consistency. This phase is CSS/layout work only: card headers get a border-b separator, fields get a two-column grid layout via a shared FieldRow component, empty values display an em dash, and tab bars get a navy underline on the active tab.

No new routes, no new data fields, no API changes, no create/edit form changes. Scope is strictly DETAIL-01, DETAIL-02, DETAIL-03, DETAIL-04.

</domain>

<decisions>
## Implementation Decisions

### FieldRow Component
- **D-01:** Create a shared `frontend/src/components/FieldRow.jsx` component (named export). Props: `label` (string) and `value` (any). Renders a two-column grid layout with muted `text-xs uppercase tracking-wide` label on the left and the value on the right.
- **D-02:** Column proportions: `grid grid-cols-[140px_1fr] gap-2 items-start` — fixed 140px label column, flexible value. Wide enough for long PE field labels like "CONTACT FREQUENCY" or "TRANSACTION TYPE" without wrapping.
- **D-03:** Em-dash fallback inside FieldRow: trigger on `null`, `undefined`, and empty string only (after trim). Zero (`0`) must show as `'0'` — this is correct for financial fields like EBITDA and revenue. Empty arrays (`[]`) render as `—` since they mean no items selected.
  - Logic: `const display = (value === null || value === undefined || String(value).trim() === '') ? '—' : value`
- **D-04:** All three detail pages (ContactDetailPage, CompanyDetailPage, DealDetailPage) migrate their field label/value pairs to use `<FieldRow />`.

### Tab Bar Navy Underline
- **D-05:** Override tab bar styling via a CSS class in `frontend/src/styles.css`. Add a `.detail-tabs` utility class that:
  - Removes the default shadcn TabsList background/border-radius pill container: `background: transparent; border-bottom: 1px solid #e2e8f0;`
  - Active TabsTrigger: `border-bottom: 2px solid #1a3868; color: #1a3868; font-weight: 600;`
  - Inactive TabsTrigger: `color: #64748b;` with `hover:color: #1a3868`
- **D-06:** Apply `className="detail-tabs"` to the `<TabsList>` in all three detail pages. No changes to shadcn component source — other tab bars in the app (admin pages) are unaffected.

### Card Header Separator
- **D-07:** Add `border-b border-gray-200 pb-3` to the `className` prop of each `<CardHeader>` across all three detail pages. Explicit, easy to verify per-card. The existing `flex flex-row items-center justify-between` stays — just append the border/padding classes.
- **D-08:** All cards in scope: every `<CardHeader>` inside ContactDetailPage, CompanyDetailPage, and DealDetailPage Profile tab. Cards without editable fields (e.g., activity timeline card) also get the border-b for visual consistency.

### Claude's Discretion
- Exact CSS selector syntax for `.detail-tabs` overriding shadcn data attributes (e.g., `[data-state='active']`) — planner can determine based on shadcn's rendered DOM.
- Whether FieldRow renders value as `<span>` or `<p>` — either is fine, keep consistent.
- Exact Tailwind class for label color — `text-muted-foreground` or `text-gray-500` (both are ~`#64748b`); planner can use whichever is cleaner given existing patterns.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` — Phase 10 goal, success criteria (DETAIL-01 through DETAIL-04)
- `.planning/REQUIREMENTS.md` — DETAIL-01, DETAIL-02, DETAIL-03, DETAIL-04 definitions

### Files being modified
- `frontend/src/pages/ContactDetailPage.jsx` — existing detail page, ~830 lines
- `frontend/src/pages/CompanyDetailPage.jsx` — existing detail page
- `frontend/src/pages/DealDetailPage.jsx` — existing detail page, ~1300+ lines
- `frontend/src/styles.css` — where `.detail-tabs` CSS override goes

### Existing patterns from prior phases
- `.planning/phases/07-brand-foundation/07-CONTEXT.md` — D-03: navy HSL `214 62% 25%`, CSS variable `--primary`
- `.planning/phases/08-login-banner-sidebar/08-CONTEXT.md` — D-08/D-09: `border-[#1a3868]` active indicator, `hover:bg-gray-50` patterns
- `.planning/phases/09-data-grids/09-CONTEXT.md` — D-10: shared component architecture pattern (DataGrid, Pagination) — FieldRow follows same pattern

### New component to create
- `frontend/src/components/FieldRow.jsx` — new shared component (does not exist yet)

No external ADRs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `shadcn/ui` Card, CardContent, CardHeader, CardTitle — already imported in all 3 detail pages; no new shadcn installs needed
- `shadcn/ui` Tabs, TabsList, TabsTrigger — already imported in all 3 detail pages
- `shadcn/ui` Label — already imported but inconsistently used; FieldRow replaces ad-hoc label patterns
- `frontend/src/components/DataGrid.jsx` + `Pagination.jsx` — Phase 9 shared component precedent

### Established Patterns
- CardHeader already uses `flex flex-row items-center justify-between` in all 3 pages — just append `border-b border-gray-200 pb-3`
- CardTitle already uses `text-base font-semibold` — DETAIL-01 title requirement already met
- Edit buttons (Edit3/Pencil icons) already present in card headers — DETAIL-01 edit button requirement already met
- CSS variable `--primary` = navy `#1a3868` (Phase 7)
- Fields currently rendered as ad-hoc `<p>`, `<Label>`, and `<span>` elements — FieldRow standardizes these

### Integration Points
- `frontend/src/styles.css` — @layer utilities section is where `.detail-tabs` class goes
- All 3 detail pages import from `@/components/ui/card` and `@/components/ui/tabs` — FieldRow will be `@/components/FieldRow`

</code_context>

<specifics>
## Specific Ideas

- FieldRow handles its own em-dash fallback so callers just pass `value={contact.title}` without null-checking
- `.detail-tabs` CSS approach is the same scoped override pattern used for other shadcn component customizations — avoids touching source

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-detail-page-polish*
*Context gathered: 2026-04-06*
