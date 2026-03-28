# Phase 5: DealCounterparty & DealFunding — Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Add two new sub-entity management tabs to DealDetailPage — Counterparties (investor stage progression: NDA, NRL, materials, VDR, feedback) and Funding (capital commitments). Backend: two new tables (`deal_counterparties`, `deal_funding`) with nested CRUD APIs at `/deals/{deal_id}/counterparties` and `/deals/{deal_id}/funding`. Frontend: two new tabs embedded inside the existing DealDetailPage tab strip.

No standalone pages for counterparties or funding. No aggregate views across deals (Phase 6+). No interaction log per counterparty (deferred to v2).

</domain>

<decisions>
## Implementation Decisions

### Tab Order
- **D-01:** DealDetailPage tab strip order: **Profile | Counterparties | Funding | Activity | Tasks | AI Insights**. PE deal data (Profile, Counterparties, Funding) front-loaded; operational tabs (Activity, Tasks) in the middle; AI Insights at end as least-used in daily workflow.

### Counterparties Tab — Grid Layout
- **D-02:** Counterparties displayed as a **horizontally scrollable data table**. Company column is **sticky left** so it remains visible while scrolling through stage date columns. Stage date columns are narrow fixed-width. No column hiding or progressive disclosure — all columns always rendered.
- **D-03:** Grid columns in order: Company (sticky), Tier, Investor Type, NDA Sent, NDA Signed, NRL, Materials, VDR, Feedback, Next Steps, Actions (edit/delete).

### Counterparty Stage Date UX
- **D-04:** Each stage date cell displays the **abbreviated date** when set (e.g. "Mar 15"), blank when not set. Clicking any cell (set or unset) opens a **date picker**. No click-to-stamp behavior — always date picker for precision. This applies in the grid row directly (not requiring a modal to open first).
- **D-05:** Stage dates are editable directly from the grid (inline click → date picker). No need to open the full edit modal just to set a date.

### Counterparty Add Modal
- **D-06:** "+ Add Counterparty" modal contains: **Company** (required, select from companies), **Tier** (RefSelect, category=tier), **Investor Type** (RefSelect, category=investor_type), **Primary Contact Name** (text), **Check Size** (amount + currency pair), **Next Steps** (textarea). All other fields (AUM, primary contact email/phone, notes, stage dates) are set after creation via the row edit modal.
- **D-07:** Edit modal (opened via row Actions button) exposes the full counterparty form: all fields from the add modal plus AUM (amount + currency), Primary Contact Email, Primary Contact Phone, Notes, and all 6 stage dates as date inputs.

### Counterparty Empty State
- **D-08:** Empty state text: "No counterparties tracked yet. Add the first investor to start tracking stage progression." + "+ Add Counterparty" button.

### Funding Tab — Table Layout
- **D-09:** Funding displayed as a standard table (no horizontal scroll needed — fewer columns). Columns: Provider (company link), Status (ref_data label), Projected Commitment, Actual Commitment, Commitment Date, Terms preview (truncated), Actions (edit/delete).
- **D-10:** "+ Add Funding" opens a modal with: **Capital Provider** (company select), **Status** (RefSelect, category=deal_funding_status), **Projected Commitment** (amount + currency), **Actual Commitment** (amount + currency), **Commitment Date** (date), **Terms** (textarea), **Comments / Next Steps** (textarea).
- **D-11:** Edit funding uses the same modal as add (fields pre-populated). No inline editing on the funding table rows.

### Funding Empty State
- **D-12:** Empty state text: "No funding commitments recorded. Add a capital provider to track commitments." + "+ Add Funding" button.

### Backend Patterns
- **D-13:** Both tables follow REFDATA-15 FK pattern: `ForeignKey('ref_data.id', ondelete='SET NULL')` for tier_id, investor_type_id, status_id.
- **D-14:** `company_id` FK on deal_counterparties: `ForeignKey('companies.id', ondelete='SET NULL')` — counterparty row survives if company is deleted.
- **D-15:** `capital_provider_id` FK on deal_funding: `ForeignKey('companies.id', ondelete='SET NULL')` — same pattern.
- **D-16:** Both list endpoints (`GET /deals/{deal_id}/counterparties`, `GET /deals/{deal_id}/funding`) resolve company name and all ref_data labels in a **single JOIN query** — no N+1. Default page size 50 (per CPARTY/FUNDING success criteria).
- **D-17:** Both tables have `deal_id FK cascade delete` — removing a deal removes all its counterparties and funding entries.
- **D-18:** `deal_counterparties` has a **UniqueConstraint(deal_id, company_id)** — a company can only appear once per deal as a counterparty.

### TanStack Query Keys
- **D-19:** Counterparties query key: `['deal-counterparties', dealId]`
- **D-20:** Funding query key: `['deal-funding', dealId]`
- Both use `invalidateQueries` on mutation success scoped to the deal ID.

### Null Label Handling
- **D-21:** If a ref_data item used by a counterparty (e.g., tier) has been deactivated, the label renders as `"---"` in the grid — no broken display (per Phase 5 success criteria #5).

### Claude's Discretion
- Exact column widths for the stage date columns in the grid.
- Whether the date picker in the grid appears as a popover anchored to the cell or as a floating dialog.
- Alembic migration numbering (0009, 0010, etc.) — pick next available numbers.
- Whether `position` column on deal_counterparties is used for drag-to-reorder (probably not this phase — insert order is fine).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` §DealCounterparty Entity (CPARTY-01 through CPARTY-12) — full schema and acceptance criteria
- `.planning/REQUIREMENTS.md` §DealFunding Entity (FUNDING-01 through FUNDING-09) — full schema and acceptance criteria

### Phase Roadmap
- `.planning/ROADMAP.md` §Phase 5 — goal, success criteria, and plan stubs (05-01 through 05-04)

### Phase 4 Patterns (must follow)
- `.planning/phases/04-deal-model-expansion-fund-entity/04-CONTEXT.md` — D-12 through D-17 (migration patterns, RefSelect, label resolution, chips)
- `.planning/phases/04-deal-model-expansion-fund-entity/04-04-SUMMARY.md` — DealDetailPage tab structure (tabs.jsx component usage, per-card edit pattern)

### Phase 3 Patterns (must follow)
- `.planning/phases/03-contact-company-model-expansion/03-CONTEXT.md` — D-11 (FK ondelete patterns), D-12 (RefSelect queryKey), D-14 (nullable migrations)

### Phase 2 Patterns (must follow)
- `.planning/phases/02-reference-data-system/02-03-SUMMARY.md` — RefSelect component API, useRefData hook

### Codebase Conventions
- `.planning/codebase/CONVENTIONS.md` — SQLAlchemy 2.0 patterns, async service pattern
- `.planning/codebase/STRUCTURE.md` — module boundaries

### Existing Frontend (read before UI work)
- `frontend/src/pages/DealDetailPage.jsx` — current 4-tab layout; Phase 5 adds Counterparties and Funding tabs
- `frontend/src/pages/ContactDetailPage.jsx` — reference for modal + per-row edit patterns

### Existing Backend (read before migration)
- `backend/models.py` — existing Deal, Company ORM models (understand FKs before adding)
- `backend/api/routes/deals.py` — existing deal routes (nested routes attach here)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Tabs, TabsList, TabsTrigger, TabsContent` from `@/components/ui/tabs` — already in DealDetailPage
- `Dialog, DialogContent, DialogHeader, DialogTitle` from `@/components/ui/dialog` — used for fund modal in Phase 4; same pattern for add/edit modals
- `<RefSelect category="...">` — for tier, investor_type, deal_funding_status dropdowns
- Amount + currency pair input pattern — established in Phase 3/4; reuse for check_size, AUM, projected/actual commitment
- `toast` from `sonner` — success/error toasts on mutation

### Established Patterns
- Nested CRUD routes at `/deals/{deal_id}/...` — deal_id scoping established
- Single JOIN query for label resolution — established in Phase 3/4 service layer
- `useMutation` + `invalidateQueries` on success — used throughout
- `lazy="raise"` on ORM relationships to prevent accidental N+1 — established pattern

### Integration Points
- DealDetailPage tab strip needs 2 new TabsTrigger + TabsContent blocks
- Two new API modules needed: `frontend/src/api/counterparties.js`, `frontend/src/api/funding.js`
- Two new backend route files: `backend/api/routes/counterparties.py`, `backend/api/routes/funding.py`
- Two new service files: `backend/services/counterparties.py`, `backend/services/funding.py`
- New ref_data category needed: `deal_funding_status` — seed values: `Soft Circle`, `Hard Circle`, `Committed`, `Funded`, `Declined`

</code_context>

<specifics>
## Specific Decisions from Discussion

- Tab order: Profile | Counterparties | Funding | Activity | Tasks | AI Insights (PE workflow data first, AI last)
- Stage dates: abbreviated date in cell ("Mar 15"), click always opens date picker — no click-to-stamp
- Stage dates editable directly from the grid row, not requiring the edit modal
- Add counterparty modal is intentionally minimal: Company + Tier + Investor Type + Primary Contact Name + Check Size + Next Steps
- Full counterparty editing (AUM, email, phone, notes, stage dates) is done via the row edit modal after creation

</specifics>

<deferred>
## Deferred Ideas

- Per-counterparty interaction log (calls, meetings, emails) — explicitly v2 per REQUIREMENTS.md (INTLOG-01/02)
- Drag-to-reorder counterparties — not this phase; insert order sufficient
- Aggregate counterparty funnel view across all deals — v2 analytics (ANALYTICS-02)
- Investor relationship history (all deals a company appears in as counterparty) — v2 (ANALYTICS-03)

</deferred>

---

*Phase: 05-deal-counterparty-deal-funding*
*Context gathered: 2026-03-28*
