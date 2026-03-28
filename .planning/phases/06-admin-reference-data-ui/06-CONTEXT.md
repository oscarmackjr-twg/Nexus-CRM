---
phase: "06"
phase_name: admin-reference-data-ui
status: ready
created: "2026-03-28"
---

<decisions>
## Implementation Decisions

### Admin Page Structure
- **D-01:** AdminPage gets **two tabs** using the existing `Tabs` shadcn component: `Users` (existing org snapshot + user list content) and `Reference Data` (new). Reference Data tab is the focus of this phase. The Users tab content is unchanged — just wrapped in a tab panel.

### Category Navigation
- **D-02:** Reference Data tab uses a **sidebar list** layout — vertical list of all categories on the left (fixed width ~200px), selected category's items fill the right panel. All categories always visible without clicks. First category (Sector) is selected by default. Category labels should be human-readable (e.g., "Sector", "Transaction Type", "Tier") not snake_case slugs.

### Item CRUD Interaction
- **D-03:** Add and Edit use **modal dialogs** — consistent with Phase 5 (Counterparties/Funding tabs). `[+ Add Item]` button above the table opens an empty modal. Edit icon/button on each row opens a pre-filled modal. Modal fields: Label (text input, required) and Position (number input, optional — defaults to end of list). No need for a Value field in the UI (value is derived from label on the backend or set to label at creation).
- **D-04:** Deactivate is a **separate action** from Edit — a `[✕]` icon button on each row triggers deactivation directly (no confirmation modal needed for deactivation — it's reversible).

### Deactivate UX
- **D-05:** Deactivation is **reversible** — PATCH `is_active=false` to deactivate, PATCH `is_active=true` to reactivate. Inactive items are **shown in the admin table greyed-out** (opacity-50 or muted text color) with a `[↺]` reactivate button instead of the deactivate `[✕]`. Inactive items immediately disappear from all form dropdowns (ref data query invalidated after mutation) but are still visible to admins so they can restore them. No separate "Show inactive" toggle needed — always show all.

### Dropdown Wiring (ADMIN-07)
- **D-06:** RefSelect, useRefData, and refData.js API module are already built and in use across ContactDetailPage, CompanyDetailPage, and DealDetailPage (Phases 2–5). The executor should audit all form dropdowns in these pages plus DealDetailPage's Counterparties and Funding tab modals to confirm no hardcoded `<option>` lists remain. Any hardcoded selects found must be replaced with `<RefSelect category="..." />`.

### Query Invalidation (ADMIN-08)
- **D-07:** After any admin mutation (add, edit, deactivate, reactivate), invalidate ALL ref data queries using `queryClient.invalidateQueries({ queryKey: ['ref'] })` — the prefix invalidation pattern so all `['ref', category]` keys are cleared simultaneously.

### Claude's Discretion
- Category display names: map snake_case category values to human-readable labels (e.g., `transaction_type` → "Transaction Type", `contact_type` → "Contact Type", `company_sub_type` → "Company Sub-Type", `deal_source_type` → "Deal Source Type", `passed_dead_reason` → "Passed/Dead Reason", `investor_type` → "Investor Type"). Executor decides the full mapping.
- Table columns for the items panel: Label, Position, Status (Active/Inactive badge), Actions (Edit icon + Deactivate/Reactivate icon).
- Empty state for items panel: "No items in this category. Add the first one."
- Role guard: Reference Data tab should only be interactive for org_admin and super_admin. Members can see the page (it's at /admin which already checks role) but the Add/Edit/Deactivate actions should be hidden or disabled for non-admins if needed — executor decides based on existing role guard pattern.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria, requirements (ADMIN-01 through ADMIN-08)
- `.planning/REQUIREMENTS.md` — ADMIN-01 through ADMIN-08 full spec

### Existing ref data infrastructure (built in Phase 2)
- `frontend/src/components/RefSelect.jsx` — existing RefSelect component (uses useRefData internally)
- `frontend/src/hooks/useRefData.js` — useRefData hook (queryKey ['ref', category], staleTime 5min)
- `frontend/src/api/refData.js` — getRefData, createRefData, updateRefData API functions (no deleteRefData — deactivation uses updateRefData with is_active=false)
- `.planning/phases/02-reference-data-system/02-CONTEXT.md` — Phase 2 decisions (D-03: GET open to all, D-04: system defaults + org items union, D-05: RefSelect uses shadcn Select)

### Existing admin page
- `frontend/src/pages/AdminPage.jsx` — current AdminPage (user management only — will gain Ref Data tab)
- `frontend/src/App.jsx` — routing (AdminPage at /admin, AuthGuard wraps it)

### Codebase patterns
- `frontend/src/pages/DealDetailPage.jsx` — canonical tab layout + modal CRUD pattern (Phase 5)
- `frontend/src/components/ui/tabs.jsx` — shadcn Tabs component
- `frontend/src/components/ui/dialog.jsx` — shadcn Dialog (modal)
- `frontend/src/components/ui/table.jsx` — shadcn Table
- `backend/api/dependencies.py` — require_role pattern for org_admin guard
- `.planning/codebase/CONVENTIONS.md` — naming conventions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` from `@/components/ui/tabs` — already used in DealDetailPage, can use same pattern here
- `Dialog`, `DialogContent`, `DialogHeader`, `DialogTitle` from `@/components/ui/dialog` — used in DealDetailPage modals
- `Table`, `TableBody`, `TableCell`, `TableHead`, `TableHeader`, `TableRow` from `@/components/ui/table` — used in PipelinePage list view
- `Badge` from `@/components/ui/badge` — for Active/Inactive status display
- `useRefData` + `RefSelect` + `refData.js` — full ref data read/write infrastructure already in place
- `queryClient.invalidateQueries` — pattern established in Phase 5 CRUD modals

### Integration Points
- `frontend/src/pages/AdminPage.jsx` — wrap existing content in Users tab, add Reference Data tab
- `frontend/src/api/refData.js` — may need to add `updateRefData` for is_active toggle if not already covering it (it does: `PATCH /admin/ref-data/:id`)
- All form pages using RefSelect already pull from the correct query keys — just verify no hardcoded lists remain

### What Doesn't Exist Yet
- No admin ref data management UI (category sidebar + items table + modals)
- No reactivate endpoint usage (updateRefData covers it via is_active: true)
- No category-to-display-name mapping utility
</code_context>

<deferred>
## Deferred Ideas

None raised during discussion.
</deferred>
