# Roadmap: Nexus CRM — PE Data Model Expansion

## Overview

This milestone expands Nexus CRM from a generic deal CRM into a purpose-built PE advisory platform for TWG Asia. Six phases deliver the work in dependency order: UI polish runs first (independent, fast), then the reference data system that all other entities depend on, then Contact and Company model expansions, then the Deal model expansion with the Fund entity, then the two new sub-entities (DealCounterparty and DealFunding) that depend on all the above, and finally the Admin UI that exposes reference data management to org admins and wires up all dropdowns.

## Phases

- [ ] **Phase 1: UI Polish** - Clean up login screen styling and standardize spacing, typography, and layout across all existing screens
- [ ] **Phase 2: Reference Data System** - Build the ref_data table, seed all TWG lookup values via migration, and expose CRUD API endpoints
- [ ] **Phase 3: Contact & Company Model Expansion** - Add all PE Blueprint fields to Contact and Company with migrations, API, and updated detail screens
- [ ] **Phase 4: Deal Model Expansion & Fund Entity** - Add PE deal fields and milestones to Deal, create the Fund entity, and update the deal detail screen
- [ ] **Phase 5: DealCounterparty & DealFunding** - Build the two new sub-entities with full CRUD APIs and embed their management UIs inside deal detail
- [ ] **Phase 6: Admin Reference Data UI** - Build the Admin page for managing reference items and wire all form dropdowns to use ref_data

---

## Phase Details

### Phase 1: UI Polish
**Goal**: All screens have consistent, professional visual presentation that matches the app's design language
**Depends on**: Nothing (first phase — no database or API changes required)
**Requirements**: UI-01, UI-02, UI-03
**Success Criteria** (what must be TRUE):
  1. Login page renders with correct spacing, typography, and visual hierarchy — no layout shifts or unstyled elements
  2. Contact, Company, Deal, and Dashboard screens share consistent heading sizes, input spacing, and card padding — no visible mismatches between screens
  3. Dashboard stat cards display correct deal and pipeline metrics (no stale or hardcoded values)
**Plans**: 3 plans
**UI hint**: yes

Plans:
- [ ] 01-01-PLAN.md — Dark mode lock + login page redesign (TWG branding, staging banner, backend status indicator)
- [ ] 01-02-PLAN.md — Spacing and typography consistency pass across ContactDetail, CompanyDetail, Contacts, and DealDetail pages
- [x] 01-03-PLAN.md — Dashboard stat card polish, PE heading, empty state hardening, and visual verification checkpoint

---

### Phase 2: Reference Data System
**Goal**: A single org-scoped reference data table exists, seeded with all TWG lookup values, and is queryable via API so all downstream entity fields can use it as their source of truth
**Depends on**: Nothing (schema-level change with no upstream dependencies)
**Requirements**: REFDATA-01, REFDATA-02, REFDATA-03, REFDATA-04, REFDATA-05, REFDATA-06, REFDATA-07, REFDATA-08, REFDATA-09, REFDATA-10, REFDATA-11, REFDATA-12, REFDATA-13, REFDATA-14, REFDATA-15
**Success Criteria** (what must be TRUE):
  1. Running `alembic upgrade head` on a fresh database creates the ref_data table and populates all 10 categories with TWG values — no separate seed step required
  2. `GET /admin/ref-data?category=sector` returns the 10 sector values ordered by position, scoped to the requesting org
  3. An org admin can POST a new reference item, PATCH an existing item's label or position, and PATCH is_active=false to soft-delete it — all without restarting the server
  4. A deactivated reference item no longer appears in `GET /admin/ref-data` results, but existing records that reference its ID are not affected
**Plans**: TBD

Plans:
- [ ] 02-01: ref_data migration — write `0002_pe_ref_data.py` Alembic migration: CREATE TABLE ref_data with (org_id, category, value) unique constraint and (org_id, category) index; seed all 10 TWG categories via op.bulk_insert; write explicit downgrade
- [ ] 02-02: ref_data service and API — implement RefDataService with list_by_category, create, update methods; add GET/POST/PATCH routes at `/admin/ref-data`; add require_role(org_admin) guard; write Pydantic Create/Update/Response schemas
- [ ] 02-03: Frontend ref data hooks — implement `useRefData(category)` TanStack Query hook with `queryKey: ['ref', category]` and 5-minute staleTime; create `<RefSelect>` component that accepts a category prop and renders a populated dropdown; invalidate `['ref']` prefix on admin mutations

---

### Phase 3: Contact & Company Model Expansion
**Goal**: Contact and Company records hold all PE Blueprint fields with full API support and updated detail screens, so deal teams can record coverage persons, sector preferences, investment profile, and relationship metadata
**Depends on**: Phase 2 (ref_data IDs used as FKs for contact_type, sector, tier, company_type, etc.)
**Requirements**: CONTACT-01, CONTACT-02, CONTACT-03, CONTACT-04, CONTACT-05, CONTACT-06, CONTACT-07, CONTACT-08, CONTACT-09, CONTACT-10, COMPANY-01, COMPANY-02, COMPANY-03, COMPANY-04, COMPANY-05, COMPANY-06, COMPANY-07, COMPANY-08, COMPANY-09, COMPANY-10, COMPANY-11, COMPANY-12
**Success Criteria** (what must be TRUE):
  1. A contact record can be saved with business phone, mobile phone, assistant details, address, contact type, coverage persons (multiple), sector preferences, previous employment history, board memberships, LinkedIn URL, and legacy ID — all persisted and returned by the API
  2. A company record can be saved with company type, sub-types, AUM, EBITDA, bite size range, co-invest flag, sector preferences, tier, coverage person, watchlist flag, parent company, and legacy ID — all persisted and returned by the API
  3. Contact detail screen shows new fields organized into sections; edit form exposes all new fields with correct input types (dropdowns pull from ref_data, multi-selects work, numeric fields accept decimals)
  4. Company detail screen shows new fields organized into sections; edit form exposes all new fields with correct input types
  5. All ref_data FK fields return both the UUID and the resolved label in API responses (e.g., contact_type_label alongside contact_type_id)
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 03-01: Contact migration — write `0003_contact_pe_fields.py`: add all PE contact columns (phones, assistant, address, contact_type_id FK, primary_contact bool, contact_frequency int, linkedin_url, legacy_id); write `0004_contact_coverage_persons.py`: CREATE TABLE contact_coverage_persons (contact_id, user_id); write explicit downgrades; all new columns nullable
- [ ] 03-02: Contact service and API — update ContactService and ContactResponse schema to include all new fields with resolved labels; update PATCH /contacts/{id} to accept all new fields; add coverage_persons as a separate sub-resource or embedded list; Pydantic validators for currency codes on any amount fields
- [ ] 03-03: Company migration — write `0005_company_pe_fields.py`: add all PE company columns (company_type_id FK, company_sub_type_ids JSONB, description, main_phone, parent_company_id self-ref FK, address fields, tier_id FK, sector_id FK, sub_sector_id FK, preference fields, AUM/EBITDA/bite-size Numerics with paired _currency columns, co_invest bool, watchlist bool, coverage_person_id FK, contact_frequency, legacy_id); write explicit downgrade
- [ ] 03-04: Company service and API — update CompanyService and CompanyResponse schema to include all new fields with resolved labels; update PATCH /companies/{id} to accept all new fields
- [ ] 03-05: Contact and Company UI — update ContactDetailPage and CompanyDetailPage: group fields into tabbed or sectioned edit/view layouts; replace flat field list with section-grouped field configs; wire all dropdown fields to `<RefSelect>` components; ensure multi-select fields (sector_preferences, sub_sector_preferences, coverage_persons) render correctly

---

### Phase 4: Deal Model Expansion & Fund Entity
**Goal**: Deal records hold all PE transaction fields — financials, date milestones, deal team, fund association, source tracking, and passed/dead detail — and the Fund entity exists so deals can be associated with a specific fund
**Depends on**: Phase 2 (ref_data FKs for transaction_type, source_type, passed_dead_reasons), Phase 3 (source_company_id and source_individual_id reference expanded Company/Contact models)
**Requirements**: DEAL-01, DEAL-02, DEAL-03, DEAL-04, DEAL-05, DEAL-06, DEAL-07, DEAL-08, DEAL-09, DEAL-10, DEAL-11, DEAL-12, FUND-01, FUND-02, FUND-03, FUND-04, FUND-05
**Success Criteria** (what must be TRUE):
  1. A deal record can be saved with transaction type, deal team members (multiple users), fund association, platform/add-on flag, source type, source company, originator, all six financial metric fields with paired currency codes, all eight date milestones, and passed/dead reasons — all persisted and returned by the API
  2. A Fund record can be created, listed, and updated via the API; the Deal edit form includes a fund selector dropdown
  3. Deal detail screen shows all new PE fields organized into sections (Deal Identity, Financials, Process Milestones, Source & Team, Passed/Dead); edit form exposes all fields with correct input types
  4. All ref_data FK fields in deal responses return resolved labels alongside their UUIDs
  5. Deal team field returns display names for all assigned users
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 04-01: Fund entity migration and API — write `0006_fund.py`: CREATE TABLE funds (id, org_id, fund_name, fundraise_status_id FK ref_data, target_fund_size_amount Numeric 18,2, target_fund_size_currency, vintage_year); implement FundService with list, create, update; add GET/POST/PATCH routes at `/funds`; write Pydantic schemas
- [ ] 04-02: Deal migration — write `0007_deal_pe_fields.py`: add all PE deal columns (description, new_deal_date, transaction_type_id FK, fund_id FK, platform_or_addon String, platform_company_id FK, source_type_id FK, source_company_id FK, source_individual_id FK, originator_id FK, all financial Numeric+currency columns, all date milestone Date columns, passed_dead_date, passed_dead_reasons JSONB, passed_dead_commentary, legacy_id); write `0008_deal_team_members.py`: CREATE TABLE deal_team_members (deal_id, user_id, role); write explicit downgrades; all new columns nullable
- [ ] 04-03: Deal service and API — update DealService and DealResponse schema to include all new fields with resolved labels and deal_team display names; update PATCH /deals/{id} to accept all new fields; Pydantic validators for currency codes and amount+currency pairing
- [ ] 04-04: Deal UI — update DealDetailPage: group new fields into section tabs (Deal Identity, Financials, Process Milestones, Source & Team, Passed/Dead); wire all dropdown fields to `<RefSelect>`; add deal team multi-user selector; add fund selector dropdown; render date milestone fields with date pickers

---

### Phase 5: DealCounterparty & DealFunding
**Goal**: Deal detail has two new sub-entity tabs — Counterparties for tracking investor stage progression (NDA, NRL, materials, VDR, feedback) and Funding for tracking capital commitments — both with full inline management from the deal detail screen
**Depends on**: Phase 2 (ref_data FKs for tier, investor_type), Phase 3 (company_id FK on counterparty), Phase 4 (deal_id FK on both sub-entities)
**Requirements**: CPARTY-01, CPARTY-02, CPARTY-03, CPARTY-04, CPARTY-05, CPARTY-06, CPARTY-07, CPARTY-08, CPARTY-09, CPARTY-10, CPARTY-11, CPARTY-12, FUNDING-01, FUNDING-02, FUNDING-03, FUNDING-04, FUNDING-05, FUNDING-06, FUNDING-07, FUNDING-08, FUNDING-09
**Success Criteria** (what must be TRUE):
  1. A deal with 30 counterparties loads the Counterparties tab in a single query — no N+1 — with company name, tier, investor type, all six stage dates, check size, and next steps visible in a grid
  2. A deal team member can add a counterparty, set stage dates (NDA sent, NDA signed, NRL, materials, VDR, feedback), update next steps, and remove the counterparty — all without leaving the deal detail screen
  3. A deal team member can add a capital provider to the Funding tab with projected and actual commitment amounts and currency, status, and terms — all without leaving the deal detail screen
  4. Counterparty and funding list endpoints enforce a 50-row default page size so full-table fetches cannot occur accidentally
  5. Deactivating a ref_data item used by a counterparty (e.g., tier) does not break the counterparty list — the label renders as "—" gracefully
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 05-01: DealCounterparty migration — write `0009_deal_counterparties.py`: CREATE TABLE deal_counterparties with all fields (id, org_id, deal_id FK cascade, company_id FK set null, primary_contact_name/email/phone, nda_sent_at, nda_signed_at, nrl_signed_at, intro_materials_sent_at, vdr_access_granted_at, feedback_received_at as Date columns, tier_id FK, investor_type_id FK, check_size_amount/currency, aum_amount/currency, next_steps, notes, position); add UniqueConstraint(deal_id, company_id); add indexes on deal_id and company_id; write explicit downgrade
- [ ] 05-02: DealCounterparty service and API — implement DealCounterpartyService with list_for_deal (single JOIN query resolving company name, tier label, investor_type label; default page size 50), create, update, delete; add nested routes at `/deals/{deal_id}/counterparties`; write Pydantic Create/Update/Response schemas; declare relationship with `lazy="raise"` on ORM model
- [ ] 05-03: DealFunding migration and API — write `0010_deal_funding.py`: CREATE TABLE deal_funding (id, org_id, deal_id FK cascade, capital_provider_id FK set null, status_id FK ref_data, projected_commitment_amount/currency, actual_commitment_amount/currency, actual_commitment_date, terms, comments_next_steps); implement DealFundingService with list_for_deal, create, update, delete; add nested routes at `/deals/{deal_id}/funding`; write Pydantic schemas; write explicit downgrade
- [ ] 05-04: Counterparties and Funding UI — add Counterparties tab to DealDetailPage: grid with stage date columns (boolean visual with date tooltip), inline row editing for next_steps and stage dates, add/remove counterparty via modal; add Funding tab: table with provider name (company link), status dropdown, commitment amounts, add/edit/remove via modal; both tabs use TanStack Query with deal_id in query key; handle null ref_data labels gracefully with "—"

---

### Phase 6: Admin Reference Data UI
**Goal**: Org admins can manage all reference data categories through a dedicated Admin page, and every form dropdown across the app fetches its options from the ref_data API using consistent query keys
**Depends on**: Phase 2 (ref_data API), Phase 3 (Contact/Company forms use dropdowns), Phase 4 (Deal forms use dropdowns), Phase 5 (Counterparty/Funding forms use dropdowns)
**Requirements**: ADMIN-01, ADMIN-02, ADMIN-03, ADMIN-04, ADMIN-05, ADMIN-06, ADMIN-07, ADMIN-08
**Success Criteria** (what must be TRUE):
  1. An org admin navigates to `/admin` and sees a list of all reference data categories; selecting a category shows all active items with their label, value, and position
  2. Org admin can add a new item to any category (it appears in the relevant dropdowns on Contact/Company/Deal forms within the same session after invalidation)
  3. Org admin can edit an existing item's label and position; org admin can deactivate an item (it disappears from all form dropdowns but existing records showing that value are not broken)
  4. All dropdowns across Contact, Company, Deal, DealCounterparty, and DealFunding forms fetch from `GET /admin/ref-data?category=<category>` with `queryKey: ['ref', '<category>']` — no hardcoded option lists remain in any form
  5. After any admin mutation, all `['ref', ...]` prefixed queries are invalidated so changes propagate to open forms without a page reload
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 06-01: Admin page scaffold — create `/admin` route (protected by org_admin role check); build AdminPage component with category sidebar listing all 10+ ref_data categories; route to CategoryView when a category is selected
- [ ] 06-02: Category management UI — build CategoryView component: sortable list of items with label, value, position, and is_active toggle; add item form (label + value fields); inline edit for label and position; deactivate button with confirmation; all mutations call `queryClient.invalidateQueries({ queryKey: ['ref'] })` on success
- [ ] 06-03: Dropdown wiring audit — audit all Contact, Company, Deal, DealCounterparty, and DealFunding edit forms; replace any hardcoded option arrays with `<RefSelect category="...">` component calls; verify consistent `['ref', category]` query keys; confirm staleTime=5min on all ref data queries

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. UI Polish | 1/3 | In Progress|  |
| 2. Reference Data System | 0/3 | Not started | - |
| 3. Contact & Company Model Expansion | 0/5 | Not started | - |
| 4. Deal Model Expansion & Fund Entity | 0/4 | Not started | - |
| 5. DealCounterparty & DealFunding | 0/4 | Not started | - |
| 6. Admin Reference Data UI | 0/3 | Not started | - |
