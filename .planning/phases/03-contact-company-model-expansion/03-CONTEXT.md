# Phase 3: Contact & Company Model Expansion — Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Add all PE Blueprint fields to Contact and Company with migrations, service/API updates, and updated detail screens. Deal teams can record coverage persons, sector preferences, investment profile, employment history, and relationship metadata on both entities — all persisted and returned by the API with resolved labels for FK fields.

**Scope extension (folded in):** Contact-level call/note logging (activity_type + occurred_at + notes, without requiring a deal). This extends the existing Activities tab so contacts can have logged interactions independent of any deal association.

</domain>

<decisions>
## Implementation Decisions

### Detail Screen Layout
- **D-01:** Add a dedicated **"Profile" tab** to both ContactDetailPage and CompanyDetailPage, placed first in tab order before Activities/Tasks/LinkedIn/AI. All new PE fields live in this tab.
- **D-02:** Contact Profile tab uses three card sections: **Identity** (contact_type, primary_contact, phones, address, linkedin_url), **Investment Preferences** (sectors, sub_sectors, contact_frequency), **Internal Coverage** (coverage_persons, legacy_id).
- **D-03:** Company Profile tab uses three card sections: **Identity** (company_type, sub_types, tier, sector, sub_sector, phone, address, parent_company), **Investment Profile** (AUM, EBITDA range, bite size, co_invest, transaction_types, sector_preferences, sub_sector_preferences, preference_notes), **Internal** (watchlist, coverage_person, contact_frequency, legacy_id).

### Multi-Value JSONB Fields
- **D-04:** All multi-select JSONB fields (sector_preferences, sub_sector_preferences, coverage_persons, transaction_types, company_sub_type_ids) use a **chips + RefSelect add** pattern: current values display as removable badge chips; a RefSelect dropdown appends additional values. No separate popover or repeated selects.
- **D-05:** Coverage persons (M2M to users) use the same chip pattern but source from the `/users` endpoint (not ref_data). Each chip shows the user's display name with an ×.

### Structured JSONB Fields (Contact)
- **D-06:** `previous_employment` and `board_memberships` use a **row UI with add/remove**: each entry is one row with input fields. previous_employment columns: Company, Title, From (year), To (year or blank for current). board_memberships columns: Company, Title. An "+ Add" button appends a new empty row; × removes a row. Both are shown in their own sub-section within the Identity card or as standalone cards in the Profile tab.

### Company Financial Fields
- **D-07:** Financial fields in CompanyDetailPage are grouped in a dedicated **"Investment Profile"** card section within the Profile tab. Amount and currency code fields are rendered side-by-side (amount input + 3-char currency input). Fields: AUM (amount + currency), EBITDA amount + currency, EBITDA range (min + max + currency), bite size (low + high + currency), co_invest boolean, min/max EBITDA for deal sizing.

### Contact Activity Logging (Scope Extension)
- **D-08:** Contact-level activity logging is **in scope for Phase 3**. Activities can be logged on a contact without requiring a deal association. The existing Activities tab on ContactDetailPage is updated to show contact-level activities alongside (or instead of) deal-tied ones.
- **D-09:** Activity fields: activity_type (call / meeting / email / note — matches existing activity_type enum), occurred_at (date), notes (text). No dealId required.
- **D-10:** Implementation approach: make `deal_id` nullable on the existing activities table (migration), update ActivityService/routes to allow deal_id=null when contact_id is provided, update the log-activity form on ContactDetailPage to remove the required deal selector.

### Patterns Carried Forward
- **D-11:** All ref_data FK columns use `ForeignKey('ref_data.id', ondelete='SET NULL')` — Phase 2 REFDATA-15 pattern.
- **D-12:** All dropdown fields use `<RefSelect category="...">` with queryKey `['ref', category]` and staleTime 5min — Phase 2 canonical pattern.
- **D-13:** JSONB columns use the existing `JSONVariant` type alias (JSON with JSONB variant for PostgreSQL).
- **D-14:** All new columns in migrations are nullable (no breaking changes to existing records).

### Claude's Discretion
- Exact section header styling (font size, divider style) — match existing Phase 1 conventions.
- Ordering of fields within each section — group logically, no specific order mandated.
- Whether Employment History and Board Memberships each get their own card or share one — Claude decides based on field count.
- Currency input width and formatting (3-char input vs select) — Claude decides; 3-char text input is fine.

### Folded Todos
None folded from backlog (no matching todos found).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` §Contact Data Model (CONTACT-01 through CONTACT-10) — all contact PE fields and acceptance criteria
- `.planning/REQUIREMENTS.md` §Company Data Model (COMPANY-01 through COMPANY-12) — all company PE fields and acceptance criteria

### Phase Roadmap
- `.planning/ROADMAP.md` §Phase 3 — goal, success criteria, and draft plan list (03-01 through 03-05)

### Phase 2 Patterns (must follow)
- `.planning/phases/02-reference-data-system/02-03-SUMMARY.md` — RefSelect component API, useRefData hook, queryKey convention
- `.planning/phases/02-reference-data-system/02-02-SUMMARY.md` — ref_data service patterns, REFDATA-15 FK pattern

### Codebase Conventions
- `.planning/codebase/CONVENTIONS.md` — SQLAlchemy 2.0 patterns, Pydantic schema conventions, async service pattern, JSONVariant usage
- `.planning/codebase/STRUCTURE.md` — module boundaries, where to add new code

### Existing Models (read before migration)
- `backend/models.py` lines 105–165 — existing Contact and Company ORM models (understand what already exists before adding columns)

### Existing Frontend Pages (read before UI work)
- `frontend/src/pages/ContactDetailPage.jsx` — existing tab structure, edit mutation pattern, activity log form
- `frontend/src/pages/CompanyDetailPage.jsx` — existing layout to understand what's already there

</canonical_refs>

<deferred>
## Deferred Ideas

None deferred — the Calls & Notes capability was folded into Phase 3 scope (D-08 through D-10).
</deferred>
