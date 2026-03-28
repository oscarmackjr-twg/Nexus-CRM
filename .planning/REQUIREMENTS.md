# Requirements: Nexus CRM v1.1 — UI Professionalism

**Milestone:** v1.1 UI Professionalism
**Defined:** 2026-03-28
**Status:** Active

---

## Branding & Theme

- [ ] **BRAND-01**: TWG `#1a3868` navy replaces indigo/purple as the primary brand color throughout (CSS variables and Tailwind config updated)
- [ ] **BRAND-02**: Gotham font applied as body font with system-ui fallback via CSS `@font-face` or font-family declaration
- [ ] **BRAND-03**: CSS variables consolidated to match POC pattern: `--color-brand`, `--color-brand-hover`, `--color-page-bg`, `--color-content-bg`, `--color-text`

## Login Page

- [ ] **LOGIN-01**: TWG logo (`twg-logo.png`) displayed centered above the login form
- [ ] **LOGIN-02**: Staging banner displayed on login page when `VITE_APP_ENV !== 'production'` (amber-400, sticky top)
- [ ] **LOGIN-03**: Backend health status indicator shown on login page ("Backend connected" / "Backend unreachable")
- [ ] **LOGIN-04**: Login page button and focus rings use `#1a3868` navy primary color

## Staging Banner

- [ ] **BANNER-01**: `StagingBanner` component created and displayed on all authenticated pages (amber-400, sticky top, z-50, env-gated)

## Navigation / Sidebar

- [ ] **NAV-01**: Sidebar redesigned with white background + `border-r` separator (replacing dark slate-900)
- [ ] **NAV-02**: TWG logo + "Nexus CRM" subtext displayed in sidebar header (matching POC Layout.tsx pattern)
- [ ] **NAV-03**: Active nav items display navy `border-l-4` left indicator + `#1a3868` text + `bg-gray-50` background
- [ ] **NAV-04**: Nav section group labels styled with uppercase tracking-widest muted text (e.g., DEALS, ADMIN)
- [ ] **NAV-05**: Sidebar footer displays current username, role, and Sign out button in muted POC style

## Data Grids

- [ ] **GRID-01**: Contacts list view uses compact row density — tight padding (`py-2`), `text-sm` throughout
- [ ] **GRID-02**: Companies list view uses compact row density
- [ ] **GRID-03**: Deals list view uses compact row density
- [ ] **GRID-04**: All list view column headers styled: uppercase, `tracking-wide`, `text-xs`, `text-gray-500`, `border-b`, sort indicator arrows
- [ ] **GRID-05**: Table rows have subtle hover state (`hover:bg-gray-50`); row action buttons (View/Edit) revealed on hover
- [ ] **GRID-06**: Pagination bar polished — page count display, prev/next buttons, records-per-page selector, consistent with TWG style

## Detail Page Polish

- [ ] **DETAIL-01**: Section card headers consistent across all detail pages — title in `font-semibold`, optional Edit button right-aligned, `border-b` separator below header
- [ ] **DETAIL-02**: Field label/value layout uses two-column grid — muted `text-xs uppercase` label left, normal value right, consistent vertical spacing
- [ ] **DETAIL-03**: Empty/null field values display `—` (em dash) placeholder instead of blank space
- [ ] **DETAIL-04**: Tab bar on detail pages uses navy underline active indicator, clean border, consistent with brand color

## Carried-Forward: v1.0 Data Completeness Gaps

*These requirements were defined in v1.0 but not fully executed.*

- [ ] **CONTACT-08**: Contact detail page profile tab displays all 20+ PE Blueprint fields (identity, employment, board memberships, investment preferences, internal coverage)
- [ ] **CONTACT-09**: Contact list view displays resolved label fields (contact_type label, not raw UUID)
- [ ] **CONTACT-10**: Contact API returns resolved label fields in list and detail responses
- [ ] **COMPANY-10**: Company detail page displays all 33 PE Blueprint fields with per-card editing
- [ ] **COMPANY-11**: Company list view displays resolved label fields (company_type, tier, sector labels)
- [ ] **COMPANY-12**: Company API returns resolved label fields in list and detail responses
- [ ] **DEAL-11**: Deal detail screen Profile tab displays all 30+ PE expansion fields with edit capability
- [ ] **DEAL-12**: Deal edit form includes all PE expansion fields (financial metrics, date milestones, deal team)
- [ ] **FUND-05**: Fund dropdown selector available on Deal edit form

---

## Future Requirements (Deferred)

*Reviewed but deferred to a later milestone.*

- **IMPORT-01/02/03**: Bulk import from PE Blueprint CSV — deferred until data model stable
- **ANALYTICS-01/02/03**: Pipeline velocity, counterparty funnel, investor history — analytics stubs remain
- **INTLOG-01/02**: Per-counterparty interaction log — future milestone

---

## Out of Scope (v1.1)

- Dark mode support — light theme is the standard; dark mode toggle remains future work
- Multi-currency FX conversion — amounts stored with currency code, no conversion
- Mobile app improvements — not in scope
- Screen information architecture restructuring — polish only, not redesign
- Analytics stub endpoint implementation — stubs remain stubs

---

## Traceability

*Filled by roadmapper agent.*

| REQ-ID | Phase | Plan |
|--------|-------|------|
| | | |
