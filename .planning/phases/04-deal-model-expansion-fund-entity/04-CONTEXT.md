# Phase 4: Deal Model Expansion & Fund Entity — Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Add all PE transaction fields to the Deal entity (financials, date milestones, deal team, fund association, source tracking, passed/dead detail), create the Fund entity with basic CRUD, and update DealDetailPage with a tabbed layout and full Profile tab UI. The Fund entity exists only to be referenced from deals — no standalone Fund management page this phase.

No DealCounterparty or DealFunding sub-entities this phase (Phase 5). No Admin UI (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### Deal Detail Screen Layout
- **D-01:** DealDetailPage gets a **tabbed layout** with four tabs: **Profile**, **Activity**, **AI Insights**, **Tasks** (in that order). Profile tab is first and holds all PE fields. The existing 3-column grid is replaced — existing content (activity log, AI score card, tasks) moves into their respective tabs.
- **D-02:** Profile tab uses five section cards in order: **Deal Identity**, **Financials**, **Process Milestones**, **Source & Team**, **Passed / Dead**. All five cards are always visible regardless of deal status.
- **D-03:** Editing uses **per-card Edit/Save buttons** — same pattern as Phase 3 Contact/Company Profile cards. Only one card in edit mode at a time.

### Deal Identity Card
- **D-04:** Deal Identity card fields: transaction_type_id (RefSelect), fund_id (dropdown + `+ New fund` inline create), platform_or_addon (select: Platform / Add-on / Neither), platform_company_id (company link, shown only when add-on selected), description (textarea), legacy_id (text input).

### Financials Card
- **D-05:** Financials card fields grouped in two sub-sections:
  - **Deal Metrics:** revenue (amount + currency), EBITDA (amount + currency), enterprise_value (amount + currency), equity_investment (amount + currency)
  - **Bid Amounts:** ioi_bid (amount + currency), loi_bid (amount + currency)
  - Amount and currency pairs rendered side-by-side (3-char currency input) — same pattern as Phase 3 D-07.

### Process Milestones Card
- **D-06:** Milestones displayed as a **2-column date grid**: label on left, date value on right, two columns side by side. `new_deal_date` appears first as the timeline anchor ("New Deal Date"). Remaining 8 milestones follow in process order: CIM Received, IOI Due, IOI Submitted, Management Presentation, LOI Due, LOI Submitted, Live Diligence, Portfolio Company. Null dates display as `—`. In edit mode, date picker inputs.

### Source & Team Card
- **D-07:** Source & Team card fields: deal_team (M2M users — chip pattern same as Phase 3 coverage_persons D-05: display name chips with ×, user selector to append), originator_id (user select), source_type_id (RefSelect, category=deal_source_type), source_company_id (company link/select), source_individual_id (contact link/select).

### Passed / Dead Card
- **D-08:** Passed / Dead card is **always visible** in the Profile tab regardless of deal status. Fields: passed_dead_date (date picker), passed_dead_reasons (multi-select chips using RefSelect, category=passed_dead_reason), passed_dead_commentary (textarea). Empty by default; users fill it in when a deal dies.

### Fund Entity
- **D-09:** Fund entity is created via an **inline quick-create modal** triggered by `+ New fund` in the Deal Identity card (edit mode). Modal fields: fund_name (text, required), fundraise_status_id (RefSelect, category=fund_status), target_fund_size_amount + target_fund_size_currency (amount + currency pair), vintage_year (number). On create, fund is selected automatically in the dropdown.
- **D-10:** The fund_status ref_data category needs to be added: seed values = `Fundraising`, `Closed`, `Deployed`, `Returning Capital`. This is a new category not in the Phase 2 seed list.
- **D-11:** Fund CRUD routes: `GET /funds` (list for org), `POST /funds` (create), `PATCH /funds/{id}` (update). No delete — funds referenced by deals cannot be removed safely.

### Patterns Carried Forward from Phase 3
- **D-12:** All ref_data FK columns use `ForeignKey('ref_data.id', ondelete='SET NULL')` — Phase 3 D-11.
- **D-13:** All new migration columns are nullable — Phase 3 D-14.
- **D-14:** JSONB columns (passed_dead_reasons) use the existing `JSONVariant` type alias — Phase 3 D-13.
- **D-15:** `<RefSelect category="...">` with queryKey `['ref', category]` and staleTime 5min for all dropdown fields — Phase 3 D-12.
- **D-16:** All ref_data FK fields in API responses return resolved labels alongside UUIDs (e.g., `transaction_type_label` alongside `transaction_type_id`) — Phase 3 label resolution pattern.
- **D-17:** Deal team field returns display names for all assigned users (same pattern as coverage_persons in Phase 3).

### Claude's Discretion
- Exact tab label abbreviations if needed for narrow viewports.
- Whether platform_company_id shows as a read-only link or a live search select in edit mode.
- Column ordering within the 2-column milestones grid (whether pairs are grouped logically or just in chronological order).
- Fund dropdown query key: `['funds']` or similar — Claude picks a consistent key.

### Folded Todos
None folded from backlog (no matching todos found).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` §Deal Data Model (DEAL-01 through DEAL-12) — all PE deal fields and acceptance criteria
- `.planning/REQUIREMENTS.md` §Fund Entity (FUND-01 through FUND-05) — fund schema and API spec

### Phase Roadmap
- `.planning/ROADMAP.md` §Phase 4 — goal, success criteria, and plan stubs (04-01 through 04-04)

### Phase 3 Patterns (must follow)
- `.planning/phases/03-contact-company-model-expansion/03-CONTEXT.md` — D-04 (chips+RefSelect), D-05 (coverage_persons chip pattern), D-07 (amount+currency pairs), D-11/D-12/D-13/D-14 (migration/JSONB patterns)

### Phase 2 Patterns (must follow)
- `.planning/phases/02-reference-data-system/02-03-SUMMARY.md` — RefSelect component API, useRefData hook, queryKey convention
- `.planning/phases/02-reference-data-system/02-02-SUMMARY.md` — ref_data service patterns, REFDATA-15 FK pattern

### Codebase Conventions
- `.planning/codebase/CONVENTIONS.md` — SQLAlchemy 2.0 patterns, Pydantic schema conventions, async service pattern, JSONVariant usage
- `.planning/codebase/STRUCTURE.md` — module boundaries, where to add new code

### Existing Models (read before migration)
- `backend/models.py` — existing Deal ORM model (understand what already exists before adding columns)

### Existing Frontend Pages (read before UI work)
- `frontend/src/pages/DealDetailPage.jsx` — current 3-column grid layout being replaced with tabs
- `frontend/src/pages/ContactDetailPage.jsx` — reference for Profile tab + per-card edit pattern established in Phase 3

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/ui/` — Card, Badge, Button, Input, Textarea, Skeleton all available
- `<RefSelect>` component (Phase 2) — available for all ref_data dropdown fields
- Chips + RefSelect pattern (Phase 3) — available for deal_team and passed_dead_reasons
- `backend/schemas/deals.py` — existing `DealCreate`, `DealUpdate`, `DealResponse` schemas to extend
- `backend/services/deals.py` — existing `DealService` to expand with new field handling
- `backend/api/routes/deals.py` — existing routes; PATCH `/deals/{id}` to accept new fields

### Established Patterns
- Per-card edit/save with `useState(editMode)` per card — established in Phase 3 Contact/Company Profile tabs
- Amount + currency side-by-side inputs — established in Phase 3 D-07
- TanStack Query mutation + `invalidateQueries` on success — used throughout
- Label resolution via aliased SQLAlchemy joins — established in Phase 3 service layer

### Integration Points
- New `funds` table + `/funds` routes needed (new module, not extending existing)
- `fund_status` ref_data category needs to be added to the Phase 2 migration (or a new migration) — currently not seeded
- `deal_team_members` association table: new M2M between deals and users (similar to `contact_coverage_persons`)
- Alembic: migration `0007_deal_pe_fields.py` + `0008_deal_team_members.py` + `0006_fund.py` (Fund entity)

</code_context>

<specifics>
## Specific Ideas

- The `+ New fund` inline create should auto-select the newly created fund in the dropdown after creation — no extra click required.
- `new_deal_date` is labeled "New Deal Date" in the UI (not "Deal Created" or "First Identified") to match PE Blueprint naming.
- `platform_or_addon` field uses the values "platform", "addon", null — in the UI these map to "Platform Company", "Add-on", "N/A" or similar readable labels.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-deal-model-expansion-fund-entity*
*Context gathered: 2026-03-27*
