# Phase 2: Reference Data System - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the `ref_data` table with all TWG lookup values seeded via Alembic migration, expose CRUD API endpoints at `/admin/ref-data`, and create the reusable frontend query infrastructure (`useRefData` hook and `<RefSelect>` component) that downstream phases (3–6) will consume for all dropdown fields.

No UI management screen this phase — that is Phase 6. No entity FK columns this phase — those land in Phases 3–5.

</domain>

<decisions>
## Implementation Decisions

### Sub-Sector Seed Data
- **D-01:** `sub_sector` is pre-seeded at migration time — not left empty. Claude selects a sensible PE-relevant sub-sector list covering the 10 seeded parent sectors (Financial Services, Technology, Healthcare, Real Estate, Infrastructure, Consumer, Industrials, Energy, Media & Telecom, Business Services). Values can be edited via the Admin UI in Phase 6.
- **D-02:** All other categories (sector, transaction_type, tier, contact_type, company_type, company_sub_type, deal_source_type, passed_dead_reason, investor_type) use the values already specified in REQUIREMENTS.md (REFDATA-03 through REFDATA-10). No additional values beyond what's listed.

### GET Endpoint Access Level
- **D-03:** `GET /admin/ref-data?category=<category>` is accessible to **all authenticated users** — no `require_role` guard on the read endpoint. Only POST and PATCH require `org_admin` role. This is required because Contact, Company, and Deal forms (Phases 3–5) are used by all roles (rep, team_manager, org_admin) and all need to populate dropdowns.

### Org Default Duplicate Handling
- **D-04:** The GET endpoint returns a **union of system defaults (org_id=NULL) + org-specific items** — no deduplication. If an org admin creates an item whose label/value matches a system default, both appear. Org admins can deactivate the system default via PATCH (is_active=false) if they want to replace it. This keeps the query simple (no deduplicate logic).

### RefSelect Component
- **D-05:** `<RefSelect>` uses shadcn/ui `Select` component (simple dropdown, no search input). Categories have 5–10 items initially. Component accepts a `category` prop, internally calls `useRefData(category)`, and renders a populated Select. No Combobox/type-to-filter for this phase.
- **D-06:** Component interface: `<RefSelect category="sector" value={value} onChange={onChange} placeholder="Select sector" />`. Caller controls value/onChange — uncontrolled form integration is out of scope this phase.

### Claude's Discretion
- Exact sub-sector seed values: Claude selects a PE-appropriate list (planner/executor decides specific values). Should cover ~3–5 sub-sectors per parent sector. Example: Technology → Software & SaaS, Fintech, Healthtech, Hardware & Semiconductors.
- Migration file structure: Add `RefData` model to `backend/models.py` (for ORM use in the service layer) + write explicit `op.create_table` DDL in `0002_pe_ref_data.py` migration (consistent with plan stub, not the `metadata.create_all` shortcut from 0001). Seed via `op.bulk_insert`.
- `position` default: Start all system seed values at position=0 (sorted by label as tiebreaker). Org-added items get position=0 by default.
- `value` field: Use lowercase snake_case slugs (e.g., `financial_services`, `technology`). `label` is the display string.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria, plan stubs (02-01, 02-02, 02-03)
- `.planning/REQUIREMENTS.md` — REFDATA-01 through REFDATA-15 (full schema + seed values + API spec)

### Codebase patterns
- `backend/models.py` — all SQLAlchemy models live here; `RefData` model goes here too
- `backend/api/dependencies.py` — `get_current_user`, `require_role`, `get_db` Depends factories
- `alembic/versions/0001_initial.py` — existing migration pattern (reference for structure, but 0002 uses explicit DDL not metadata.create_all)
- `backend/services/contacts.py` — canonical service pattern: `(db, current_user)` constructor, `async def` methods, org-scoped queries
- `backend/schemas/contacts.py` — canonical schema pattern: `ConfigDict(from_attributes=True)`, `Create`/`Update`/`Response` naming
- `frontend/src/hooks/useContacts.js` — canonical hook pattern: thin `useQuery` wrapper
- `frontend/src/api/contacts.js` — canonical API module pattern: functions calling the Axios client
- `.planning/codebase/CONVENTIONS.md` — naming conventions (snake_case Python, camelCase JS, `Mapped[T]` SQLAlchemy, etc.)
- `.planning/codebase/ARCHITECTURE.md` — request lifecycle, service layer pattern, TanStack Query patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/ui/` — shadcn/ui primitives including `select.jsx` for the `<RefSelect>` implementation
- `backend/api/dependencies.py` — `require_role` factory for POST/PATCH auth guards
- `backend/services/_crm.py` — shared helpers (`is_admin`, org scoping patterns) that RefDataService can reuse

### Established Patterns
- All models in `backend/models.py` — `RefData` joins here, not a separate file
- Service classes: `RefDataService(db, current_user)` following the existing pattern
- Route guards: `Depends(require_role("org_admin", "super_admin"))` on POST/PATCH; `Depends(get_current_user)` on GET
- TanStack Query key: `['ref', category]` (already specified in REQUIREMENTS.md ADMIN-07)
- Invalidation prefix: `queryClient.invalidateQueries({ queryKey: ['ref'] })` after admin mutations

### Integration Points
- `backend/api/main.py` — new `admin_router` needs to be registered here (or route module added to existing router include list)
- Phase 3–5 will import `useRefData` and `<RefSelect>` directly — the hook + component API must be stable after this phase
- `frontend/src/api/` — new `refData.js` API module for the admin endpoints

</code_context>

<specifics>
## Specific Ideas

- Sub-sector seed values: Claude picks a PE-relevant list. Example starter: Technology → Software & SaaS, Fintech, Healthtech; Healthcare → Healthcare IT, Pharma & Biotech, Medical Devices; Real Estate → Residential, Commercial, Industrial; Financial Services → Asset Management, Banking, Insurance; Infrastructure → Energy & Renewables, Transportation, Utilities; Consumer → Retail, Food & Beverage, Luxury; Industrials → Manufacturing, Logistics, Chemicals; Energy → Oil & Gas, Renewables, Power Generation; Media & Telecom → Media, Telecom; Business Services → Consulting, Outsourcing, HR & Staffing.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-reference-data-system*
*Context gathered: 2026-03-26*
