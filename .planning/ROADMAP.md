# Roadmap: Nexus CRM — PE Deal Management Platform

## Milestones

- ✅ **v1.0 PE CRM Foundation** — Phases 1-6 (shipped 2026-03-28) — [archive](.planning/milestones/v1.0-ROADMAP.md)
- 📋 **v1.1 UI Professionalism** — Phases 7-12 (in progress)

---

## Phases

<details>
<summary>✅ v1.0 PE CRM Foundation (Phases 1-6) — SHIPPED 2026-03-28</summary>

- [x] Phase 1: UI Polish (3/3 plans) — completed 2026-03-27
- [x] Phase 2: Reference Data System (3/3 plans) — completed 2026-03-27
- [x] Phase 3: Contact & Company Model Expansion (6/6 plans) — completed 2026-03-28
- [x] Phase 4: Deal Model Expansion & Fund Entity (4/4 plans) — completed 2026-03-28
- [x] Phase 5: DealCounterparty & DealFunding (4/4 plans) — completed 2026-03-28
- [x] Phase 6: Admin Reference Data UI (3/3 plans) — completed 2026-03-28

</details>

### v1.1 UI Professionalism

- [ ] **Phase 7: Brand Foundation** — TWG color palette, Gotham font, CSS variable consolidation
- [ ] **Phase 8: Login, Banner & Sidebar** — branded login page, staging banner, white sidebar redesign
- [ ] **Phase 9: Data Grids** — compact Salesforce-style list views for Contacts, Companies, Deals
- [ ] **Phase 10: Detail Page Polish** — section card headers, field layout, empty values, tab bar
- [ ] **Phase 11: Contact & Company Data Completeness** — API label resolution + detail/list UI for Contact and Company PE fields
- [ ] **Phase 12: Deal & Fund Data Completeness** — Deal detail/edit UI for all PE expansion fields, Fund selector on Deal form

---

## Phase Details

### Phase 7: Brand Foundation
**Goal**: The TWG color palette and Montserrat font are live globally — all subsequent UI work builds on this baseline
**Depends on**: Nothing (first phase of v1.1)
**Requirements**: BRAND-01, BRAND-02, BRAND-03
**Success Criteria** (what must be TRUE):
  1. Every button, active indicator, and focus ring in the app shows `#1a3868` navy instead of indigo or purple
  2. Body text renders in Montserrat with system-ui fallback on all pages
  3. CSS variables `--color-brand`, `--color-brand-hover`, `--color-page-bg`, `--color-content-bg`, `--color-text` are defined and consumed throughout — no inline hex or one-off Tailwind color overrides
**Plans:** 1 plan
Plans:
- [ ] 07-01-PLAN.md — Navy CSS variables + Montserrat font + POC tokens + indigo sweep
**UI hint**: yes

### Phase 8: Login, Banner & Sidebar
**Goal**: Users see a professional TWG-branded login screen and a white sidebar with navy indicators on every authenticated page
**Depends on**: Phase 7
**Requirements**: LOGIN-01, LOGIN-02, LOGIN-03, LOGIN-04, BANNER-01, NAV-01, NAV-02, NAV-03, NAV-04, NAV-05
**Success Criteria** (what must be TRUE):
  1. Login page shows TWG logo centered above the form, navy primary button, and the staging banner when not in production
  2. A backend health status indicator is visible on the login page ("Backend connected" or "Backend unreachable")
  3. The sidebar background is white with a right-border separator; the active nav item shows a navy `border-l-4` left bar, navy text, and `bg-gray-50` highlight
  4. Section group labels (DEALS, ADMIN) appear in uppercase muted tracking-widest text in the sidebar
  5. The sidebar footer shows the current user's name, role, and a Sign Out button in muted style
  6. The amber-400 staging banner appears at the top of every authenticated page (not just login) when not in production
**Plans**: TBD
**UI hint**: yes

### Phase 9: Data Grids
**Goal**: Contacts, Companies, and Deals list views use compact Salesforce-style density with polished headers, hover states, and pagination
**Depends on**: Phase 7
**Requirements**: GRID-01, GRID-02, GRID-03, GRID-04, GRID-05, GRID-06
**Success Criteria** (what must be TRUE):
  1. All three list views (Contacts, Companies, Deals) use tight row padding (`py-2`) and `text-sm` throughout — visibly more compact than before
  2. Column headers are uppercase, `text-xs`, `text-gray-500`, `tracking-wide`, with a bottom border and sort indicator arrows
  3. Hovering a row highlights it with `bg-gray-50`; row action buttons (View/Edit) are only visible on hover
  4. The pagination bar shows page count, previous/next buttons, and a records-per-page selector in consistent TWG style
**Plans**: TBD
**UI hint**: yes

### Phase 10: Detail Page Polish
**Goal**: All detail pages have consistent section cards, field layout, empty value display, and navy tab indicators
**Depends on**: Phase 7
**Requirements**: DETAIL-01, DETAIL-02, DETAIL-03, DETAIL-04
**Success Criteria** (what must be TRUE):
  1. Every section card header across Contact, Company, and Deal detail pages shows a `font-semibold` title, optional right-aligned Edit button, and a `border-b` separator
  2. Field label/value pairs use a two-column grid — muted `text-xs uppercase` label on the left, normal value on the right, with consistent vertical spacing
  3. Fields with null or empty values display `—` (em dash) instead of blank space
  4. The tab bar on detail pages uses a navy underline for the active tab, with a clean bottom border
**Plans**: TBD
**UI hint**: yes

### Phase 11: Contact & Company Data Completeness
**Goal**: Contact and Company detail pages display all PE Blueprint fields with resolved label values in both list and detail views
**Depends on**: Phase 10
**Requirements**: CONTACT-08, CONTACT-09, CONTACT-10, COMPANY-10, COMPANY-11, COMPANY-12
**Success Criteria** (what must be TRUE):
  1. The Contact detail Profile tab shows all 20+ PE Blueprint fields (identity, employment, board memberships, investment preferences, internal coverage) with per-card editing
  2. The Contacts list view shows resolved label text (e.g., "LP" not a UUID) for contact_type and other ref_data columns
  3. The Company detail page displays all 33 PE Blueprint fields with per-card editing — financials, investment preferences, coverage person, and parent company all visible
  4. The Companies list view shows resolved label text for company_type, tier, and sector
  5. Both Contact and Company API responses include resolved label fields in list and detail endpoints (no raw UUIDs surfacing to the UI)
**Plans**: TBD
**UI hint**: yes

### Phase 12: Deal & Fund Data Completeness
**Goal**: The Deal detail page and edit form expose all PE expansion fields, and Fund can be selected when editing a deal
**Depends on**: Phase 11
**Requirements**: DEAL-11, DEAL-12, FUND-05
**Success Criteria** (what must be TRUE):
  1. The Deal detail Profile tab displays all 30+ PE expansion fields (financial metrics, date milestones, deal team, fund, source) with per-card editing
  2. The Deal edit form includes all PE expansion fields — financial metrics with currency selectors, all 8 date milestone pickers, deal team management
  3. The Fund dropdown is available and functional on the Deal edit form — a user can assign or change the fund associated with a deal
**Plans**: TBD
**UI hint**: yes

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. UI Polish | v1.0 | 3/3 | Complete | 2026-03-27 |
| 2. Reference Data System | v1.0 | 3/3 | Complete | 2026-03-27 |
| 3. Contact & Company Model Expansion | v1.0 | 6/6 | Complete | 2026-03-28 |
| 4. Deal Model Expansion & Fund Entity | v1.0 | 4/4 | Complete | 2026-03-28 |
| 5. DealCounterparty & DealFunding | v1.0 | 4/4 | Complete | 2026-03-28 |
| 6. Admin Reference Data UI | v1.0 | 3/3 | Complete | 2026-03-28 |
| 7. Brand Foundation | v1.1 | 0/1 | Planned | - |
| 8. Login, Banner & Sidebar | v1.1 | 0/? | Not started | - |
| 9. Data Grids | v1.1 | 0/? | Not started | - |
| 10. Detail Page Polish | v1.1 | 0/? | Not started | - |
| 11. Contact & Company Data Completeness | v1.1 | 0/? | Not started | - |
| 12. Deal & Fund Data Completeness | v1.1 | 0/? | Not started | - |
