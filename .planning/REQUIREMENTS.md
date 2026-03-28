# Requirements: Nexus CRM — PE Data Model Expansion

**Defined:** 2026-03-26
**Core Value:** Deal teams can track every counterparty touchpoint across every live deal — who signed the NDA, who got the VDR, who gave feedback, what's the next step — without leaving the CRM.

---

## v1 Requirements

### UI Polish

- [x] **UI-01**: Login page has clean, consistent styling matching the app's design language (correct spacing, typography, and layout)
- [x] **UI-02**: All screens have consistent spacing, typography weights, and layout alignment (no mismatched padding, font sizes, or component gaps across Contact, Company, Deal, Dashboard, and list views)
- [x] **UI-03**: Dashboard metrics and layout reflect the expanded data model (correct deal counts, updated stat cards)

### Reference Data System

- [x] **REFDATA-01**: A `ref_data` table exists in the database with columns: id, org_id (nullable for system defaults), category, value, label, position, is_active, created_at
- [x] **REFDATA-02**: The following categories are pre-seeded with TWG values at migration time: sector, sub_sector, transaction_type, tier, contact_type, company_type, company_sub_type, deal_source_type, passed_dead_reason, investor_type
- [x] **REFDATA-03**: sector is seeded with: Financial Services, Technology, Healthcare, Real Estate, Infrastructure, Consumer, Industrials, Energy, Media & Telecom, Business Services
- [x] **REFDATA-04**: transaction_type is seeded with: Equity, Credit, Preferred Equity, Mezzanine, Growth Equity, Buyout, Debt Advisory, M&A Advisory
- [x] **REFDATA-05**: tier is seeded with: Tier 1, Tier 2, Tier 3
- [x] **REFDATA-06**: contact_type is seeded with: LP, GP, Advisor, Management, Lender, Co-Investor, Strategic
- [x] **REFDATA-07**: company_type is seeded with: Financial Sponsor, Strategic, Family Office, Sovereign Wealth Fund, Pension Fund, Insurance Company, Bank, Operating Company
- [x] **REFDATA-08**: deal_source_type is seeded with: Proprietary, Bank, Advisor, Management, Portfolio Company, Existing LP
- [x] **REFDATA-09**: passed_dead_reason is seeded with: Valuation, Diligence, Market Conditions, Competitive, Strategic Fit, Timing, Management, No Follow-Up
- [x] **REFDATA-10**: investor_type is seeded with: SWF, Pension/Super, Corporate, Family Office, Financial Sponsor, Insurance, Bank
- [x] **REFDATA-11**: `GET /admin/ref-data?category=<category>` returns all active items for a category (org-scoped + system defaults), ordered by position then label
- [x] **REFDATA-12**: `POST /admin/ref-data` allows org admins to create a new reference item in any category
- [x] **REFDATA-13**: `PATCH /admin/ref-data/{id}` allows org admins to update label, position, or is_active on any reference item
- [x] **REFDATA-14**: Deleting a reference item via PATCH (is_active = false) soft-deletes it — the row remains for historical FK integrity, but the item no longer appears in dropdowns
- [x] **REFDATA-15**: All entity FK columns pointing to ref_data use ondelete="SET NULL" so that deactivated reference items do not break existing records

### Contact Data Model

- [x] **CONTACT-01**: Contact model has: business_phone (String), mobile_phone (String), assistant_name (String), assistant_email (String), assistant_phone (String)
- [x] **CONTACT-02**: Contact model has address fields: address, city, state, postal_code, country
- [x] **CONTACT-03**: Contact model has: contact_type_id (FK to ref_data, category=contact_type), primary_contact (Boolean), contact_frequency (Integer)
- [x] **CONTACT-04**: Contact model has: coverage_persons as a M2M association table to users (contact_coverage_persons)
- [x] **CONTACT-05**: Contact model has: sector (multi-ref, stored as JSONB array of ref_data IDs), sub_sector (multi-ref, stored as JSONB array of ref_data IDs)
- [x] **CONTACT-06**: Contact model has: previous_employment (JSONB array of {company, title, from, to} objects), board_memberships (JSONB array of {company, title} objects)
- [x] **CONTACT-07**: Contact model has: linkedin_url (Text), legacy_id (String, org-scoped unique index)
- [ ] **CONTACT-08**: Contact API responses include resolved labels for contact_type_id (contact_type_label) and resolved display names for coverage_persons
- [ ] **CONTACT-09**: Contact detail screen displays all new PE fields grouped by section (Identity, Investment Preferences, Internal Coverage)
- [ ] **CONTACT-10**: Contact detail edit form supports all new fields with appropriate input types (text, select from ref_data, multi-select, date, boolean, number)

### Company Data Model

- [x] **COMPANY-01**: Company model has: company_type_id (FK to ref_data, category=company_type), company_sub_type_ids (JSONB array of ref_data IDs for multi-select sub-types), description (Text)
- [x] **COMPANY-02**: Company model has: main_phone (String), parent_company_id (self-referential FK to companies, nullable)
- [x] **COMPANY-03**: Company model has address fields: address, city, state, postal_code (existing country field retained)
- [x] **COMPANY-04**: Company model has: tier_id (FK to ref_data, category=tier), sector_id (FK to ref_data, category=sector), sub_sector_id (FK to ref_data, category=sub_sector)
- [x] **COMPANY-05**: Company model has investment preference fields: sector_preferences (JSONB array of ref_data IDs), sub_sector_preferences (JSONB array of ref_data IDs), preference_notes (Text)
- [x] **COMPANY-06**: Company model has financial fields: aum_amount (Numeric 18,2), aum_currency (String 3), ebitda_amount (Numeric 18,2), ebitda_currency (String 3)
- [x] **COMPANY-07**: Company model has deal sizing fields: typical_bite_size_low (Numeric 18,2), typical_bite_size_high (Numeric 18,2), bite_size_currency (String 3), co_invest (Boolean), target_deal_size_id (FK to ref_data)
- [x] **COMPANY-08**: Company model has deal preference fields: transaction_types (JSONB array of ref_data IDs), min_ebitda (Numeric 18,2), max_ebitda (Numeric 18,2), ebitda_range_currency (String 3)
- [x] **COMPANY-09**: Company model has relationship fields: watchlist (Boolean), coverage_person_id (FK to users), contact_frequency (Integer), legacy_id (String, org-scoped unique index)
- [ ] **COMPANY-10**: Company API responses include resolved labels for all FK ref_data fields and the coverage person display name
- [ ] **COMPANY-11**: Company detail screen displays all new PE fields grouped by section (Identity, Investment Profile, Financials, Internal)
- [ ] **COMPANY-12**: Company detail edit form supports all new fields with appropriate input types

### Deal Data Model

- [x] **DEAL-01**: Deal model has: description (Text), new_deal_date (Date), transaction_type_id (FK to ref_data, category=transaction_type)
- [x] **DEAL-02**: Deal model has: deal_team as a M2M association table to users (deal_team_members)
- [x] **DEAL-03**: Deal model has: fund_id (FK to new Fund entity), platform_or_addon (enum/string: "platform", "addon", null), platform_company_id (FK to companies)
- [x] **DEAL-04**: Deal model has source tracking fields: source_type_id (FK to ref_data, category=deal_source_type), source_company_id (FK to companies), source_individual_id (FK to contacts), originator_id (FK to users)
- [x] **DEAL-05**: Deal model has financial fields: revenue_amount (Numeric 18,2), revenue_currency (String 3), ebitda_amount (Numeric 18,2), ebitda_currency (String 3), enterprise_value_amount (Numeric 18,2), enterprise_value_currency (String 3), equity_investment_amount (Numeric 18,2), equity_investment_currency (String 3)
- [x] **DEAL-06**: Deal model has bid fields: loi_bid_amount (Numeric 18,2), loi_bid_currency (String 3), ioi_bid_amount (Numeric 18,2), ioi_bid_currency (String 3)
- [x] **DEAL-07**: Deal model has date milestone fields: cim_received_date, ioi_due_date, ioi_submitted_date, management_presentation_date, loi_due_date, loi_submitted_date, live_diligence_date, portfolio_company_date (all Date, nullable)
- [x] **DEAL-08**: Deal model has passed/dead fields: passed_dead_date (Date), passed_dead_reasons (JSONB array of ref_data IDs), passed_dead_commentary (Text)
- [x] **DEAL-09**: Deal model has: legacy_id (String, org-scoped unique index)
- [x] **DEAL-10**: Deal API responses include resolved labels for all FK ref_data fields and deal_team display names
- [ ] **DEAL-11**: Deal detail screen displays all new PE fields grouped by section (Deal Identity, Financials, Process Milestones, Source & Team, Passed/Dead)
- [ ] **DEAL-12**: Deal detail edit form supports all new fields with appropriate input types

### DealCounterparty Entity

- [x] **CPARTY-01**: A deal_counterparties table exists with: id, org_id, deal_id (FK cascade), company_id (FK set null), primary_contact_name (String), primary_contact_email (String), primary_contact_phone (String), position (Integer for ordering)
- [x] **CPARTY-02**: DealCounterparty has stage tracking date columns: nda_sent_at, nda_signed_at, nrl_signed_at, intro_materials_sent_at, vdr_access_granted_at, feedback_received_at (all Date, nullable)
- [x] **CPARTY-03**: DealCounterparty has: tier_id (FK to ref_data, category=tier), investor_type_id (FK to ref_data, category=investor_type), next_steps (Text), notes (Text)
- [x] **CPARTY-04**: DealCounterparty has financial fields: check_size_amount (Numeric 18,2), check_size_currency (String 3), aum_amount (Numeric 18,2), aum_currency (String 3)
- [ ] **CPARTY-05**: `GET /deals/{deal_id}/counterparties` returns all counterparties for a deal with company name, stage dates, tier label, and investor type label — resolved in a single query (no N+1)
- [ ] **CPARTY-06**: `POST /deals/{deal_id}/counterparties` creates a new counterparty entry for a deal
- [ ] **CPARTY-07**: `PATCH /deals/{deal_id}/counterparties/{id}` updates counterparty fields including individual stage date columns
- [ ] **CPARTY-08**: `DELETE /deals/{deal_id}/counterparties/{id}` removes a counterparty from a deal
- [ ] **CPARTY-09**: Deal detail screen has a Counterparties tab showing all counterparties in a grid with columns: Company, Tier, Investor Type, NDA Sent, NDA Signed, NRL, Materials, VDR, Feedback, Next Steps
- [ ] **CPARTY-10**: Users can add a new counterparty to a deal from the Counterparties tab (inline form or modal)
- [ ] **CPARTY-11**: Users can edit a counterparty row inline or via a modal, including setting stage dates and updating next steps
- [ ] **CPARTY-12**: Users can remove a counterparty from a deal from the Counterparties tab

### DealFunding Entity

- [x] **FUNDING-01**: A deal_funding table exists with: id, org_id, deal_id (FK cascade), capital_provider_id (FK to companies, set null), status_id (FK to ref_data, category=deal_funding_status)
- [x] **FUNDING-02**: DealFunding has financial fields: projected_commitment_amount (Numeric 18,2), projected_commitment_currency (String 3), actual_commitment_amount (Numeric 18,2), actual_commitment_currency (String 3), actual_commitment_date (Date)
- [x] **FUNDING-03**: DealFunding has: terms (Text), comments_next_steps (Text)
- [x] **FUNDING-04**: `GET /deals/{deal_id}/funding` returns all funding entries for a deal with capital provider company name resolved
- [x] **FUNDING-05**: `POST /deals/{deal_id}/funding` creates a new funding entry for a deal
- [x] **FUNDING-06**: `PATCH /deals/{deal_id}/funding/{id}` updates a funding entry
- [x] **FUNDING-07**: `DELETE /deals/{deal_id}/funding/{id}` removes a funding entry
- [ ] **FUNDING-08**: Deal detail screen has a Funding tab showing all capital providers with columns: Provider, Status, Projected Commitment, Actual Commitment, Commitment Date, Terms
- [ ] **FUNDING-09**: Users can add, edit, and remove funding entries from the Funding tab

### Fund Entity

- [x] **FUND-01**: A funds table exists with: id, org_id, fund_name (String), fundraise_status_id (FK to ref_data, category=fund_status), target_fund_size_amount (Numeric 18,2), target_fund_size_currency (String 3), vintage_year (Integer)
- [x] **FUND-02**: `GET /funds` returns all funds for the org
- [x] **FUND-03**: `POST /funds` creates a new fund
- [x] **FUND-04**: `PATCH /funds/{id}` updates a fund
- [ ] **FUND-05**: Fund dropdown is available on the Deal edit form (deal_id FK on deal links to fund)

### Admin UI

- [ ] **ADMIN-01**: An Admin page exists in the frontend, accessible to org_admin and super_admin roles
- [ ] **ADMIN-02**: Admin page shows all reference data categories in a sidebar or tab list
- [ ] **ADMIN-03**: Selecting a category shows the active items for that category in a sortable list with label, value, and position
- [ ] **ADMIN-04**: Org admin can add a new item to any category (form with label, value fields)
- [ ] **ADMIN-05**: Org admin can edit an existing item's label and position
- [ ] **ADMIN-06**: Org admin can deactivate (soft-delete) an item — it disappears from dropdowns but existing records retain the FK
- [ ] **ADMIN-07**: All dropdowns in Contact, Company, and Deal forms fetch their options from the ref_data API (`GET /admin/ref-data?category=<category>`) and use consistent TanStack Query keys (`['ref', '<category>']`) for caching
- [ ] **ADMIN-08**: After any admin mutation (add/edit/deactivate), all ref data queries are invalidated via queryClient so dropdown updates are visible immediately

---

## v2 Requirements

### Data Import

- **IMPORT-01**: Bulk import contacts from PE Blueprint CSV template
- **IMPORT-02**: Bulk import companies from PE Blueprint CSV template
- **IMPORT-03**: Bulk import deals from PE Blueprint CSV template with legacy_id cross-reference

### Analytics

- **ANALYTICS-01**: Pipeline velocity metrics using deal date milestones (average days CIM to IOI, IOI to LOI, LOI to close)
- **ANALYTICS-02**: Counterparty stage funnel view across all deals (how many investors at each stage across the portfolio)
- **ANALYTICS-03**: Investor relationship history — all deals a specific company has participated in as counterparty

### Interaction Log

- **INTLOG-01**: Per-counterparty interaction log (call, meeting, email) with date, type, notes, and user
- **INTLOG-02**: Next-contact-date reminder on counterparty based on contact_frequency

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Data import / PE Blueprint migration | Data model must be stable first; explicitly deferred per PROJECT.md |
| Multi-currency FX conversion | Amounts stored with currency code for display only; no conversion logic this milestone |
| Screen redesign / IA restructuring | UI work is polish only — layout and navigation structure unchanged |
| Mobile app improvements | Web-first; mobile is a separate surface |
| Analytics stub endpoints (pipeline-velocity, forecast, leaderboard) | Remain stubs; data model populates them in v2 |
| LP portal / document distribution | Fund administration scope, not CRM |
| Automated email parsing for counterparty stage updates | High complexity, high error rate; manual stage updates only |
| Fund-level waterfall / carry calculations | Fund accounting scope, not CRM |
| Investor portal login access | Security surface increase; out of scope |
| Cap table management | Dedicated tooling (Carta, Visible) owns this |
| Duplicate deduplication AI | PE firms have small known universes; manual merge sufficient |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| UI-01 | Phase 1 | Complete |
| UI-02 | Phase 1 | Complete |
| UI-03 | Phase 5 | Complete |
| REFDATA-01 | Phase 2 | Complete |
| REFDATA-02 | Phase 2 | Complete |
| REFDATA-03 | Phase 2 | Complete |
| REFDATA-04 | Phase 2 | Complete |
| REFDATA-05 | Phase 2 | Complete |
| REFDATA-06 | Phase 2 | Complete |
| REFDATA-07 | Phase 2 | Complete |
| REFDATA-08 | Phase 2 | Complete |
| REFDATA-09 | Phase 2 | Complete |
| REFDATA-10 | Phase 2 | Complete |
| REFDATA-11 | Phase 2 | Complete |
| REFDATA-12 | Phase 2 | Complete |
| REFDATA-13 | Phase 2 | Complete |
| REFDATA-14 | Phase 2 | Complete |
| REFDATA-15 | Phase 2 | Complete |
| CONTACT-01 | Phase 3 | Complete |
| CONTACT-02 | Phase 3 | Complete |
| CONTACT-03 | Phase 3 | Complete |
| CONTACT-04 | Phase 3 | Complete |
| CONTACT-05 | Phase 3 | Complete |
| CONTACT-06 | Phase 3 | Complete |
| CONTACT-07 | Phase 3 | Complete |
| CONTACT-08 | Phase 3 | Pending |
| CONTACT-09 | Phase 3 | Pending |
| CONTACT-10 | Phase 3 | Pending |
| COMPANY-01 | Phase 3 | Complete |
| COMPANY-02 | Phase 3 | Complete |
| COMPANY-03 | Phase 3 | Complete |
| COMPANY-04 | Phase 3 | Complete |
| COMPANY-05 | Phase 3 | Complete |
| COMPANY-06 | Phase 3 | Complete |
| COMPANY-07 | Phase 3 | Complete |
| COMPANY-08 | Phase 3 | Complete |
| COMPANY-09 | Phase 3 | Complete |
| COMPANY-10 | Phase 3 | Pending |
| COMPANY-11 | Phase 3 | Pending |
| COMPANY-12 | Phase 3 | Pending |
| DEAL-01 | Phase 4 | Complete |
| DEAL-02 | Phase 4 | Complete |
| DEAL-03 | Phase 4 | Complete |
| DEAL-04 | Phase 4 | Complete |
| DEAL-05 | Phase 4 | Complete |
| DEAL-06 | Phase 4 | Complete |
| DEAL-07 | Phase 4 | Complete |
| DEAL-08 | Phase 4 | Complete |
| DEAL-09 | Phase 4 | Complete |
| DEAL-10 | Phase 4 | Complete |
| DEAL-11 | Phase 4 | Pending |
| DEAL-12 | Phase 4 | Pending |
| FUND-01 | Phase 4 | Complete |
| FUND-02 | Phase 4 | Complete |
| FUND-03 | Phase 4 | Complete |
| FUND-04 | Phase 4 | Complete |
| FUND-05 | Phase 4 | Pending |
| CPARTY-01 | Phase 5 | Complete |
| CPARTY-02 | Phase 5 | Complete |
| CPARTY-03 | Phase 5 | Complete |
| CPARTY-04 | Phase 5 | Complete |
| CPARTY-05 | Phase 5 | Pending |
| CPARTY-06 | Phase 5 | Pending |
| CPARTY-07 | Phase 5 | Pending |
| CPARTY-08 | Phase 5 | Pending |
| CPARTY-09 | Phase 5 | Pending |
| CPARTY-10 | Phase 5 | Pending |
| CPARTY-11 | Phase 5 | Pending |
| CPARTY-12 | Phase 5 | Pending |
| FUNDING-01 | Phase 5 | Complete |
| FUNDING-02 | Phase 5 | Complete |
| FUNDING-03 | Phase 5 | Complete |
| FUNDING-04 | Phase 5 | Complete |
| FUNDING-05 | Phase 5 | Complete |
| FUNDING-06 | Phase 5 | Complete |
| FUNDING-07 | Phase 5 | Complete |
| FUNDING-08 | Phase 5 | Pending |
| FUNDING-09 | Phase 5 | Pending |
| ADMIN-01 | Phase 6 | Pending |
| ADMIN-02 | Phase 6 | Pending |
| ADMIN-03 | Phase 6 | Pending |
| ADMIN-04 | Phase 6 | Pending |
| ADMIN-05 | Phase 6 | Pending |
| ADMIN-06 | Phase 6 | Pending |
| ADMIN-07 | Phase 6 | Pending |
| ADMIN-08 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 86 total
- Mapped to phases: 86
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-26*
*Last updated: 2026-03-26 after initial definition*
