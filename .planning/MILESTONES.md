# Milestones

## v1.0 PE CRM Foundation (Shipped: 2026-03-28)

**Phases completed:** 6 phases, 23 plans, 30 tasks

**Key accomplishments:**

- Tailwind dark-mode-class strategy locked, useUIStore stripped of theme state, LoginPage redesigned with TWG GLOBAL branding, staging environment banner, and /health backend status indicator
- Page-level h1 headings and consistent text-3xl font-semibold added to ContactDetailPage and CompanyDetailPage; activity timeline row padding normalized to px-4 py-3 across all in-scope pages
- Dashboard polish + light theme reversal: white content area, dark blue sidebar, centered login page with slate card
- ref_data table seeded with all 10 TWG PE categories (96 rows) via atomic Alembic migration 0002_pe_ref_data.py; RefData ORM model added; test scaffold with 7 pytest functions (3 pass, 4 xfail)
- FastAPI ref-data CRUD endpoints (GET/POST/PATCH /api/v1/admin/ref-data) with RefDataService union query, RBAC split, and soft-delete; all 7 test_ref_data.py tests green
- TanStack Query hook (useRefData), API module (refData.js), and RefSelect dropdown component with 6 passing tests — canonical ref_data frontend infrastructure for Phases 3-6
- One-liner:
- Contact API fully expanded with 20 PE Blueprint fields, contact_type_label resolved server-side, coverage_persons M2M, contact-level activity logging, and deal_id nullable migration
- Alembic migration 0005 + Company ORM model expanded with 33 PE Blueprint columns — type/tier/sector FKs, financials (AUM/EBITDA/bite-size), investment preferences, watchlist, coverage_person, self-referential parent_company
- One-liner:
- ContactDetailPage rebuilt with 5-card Profile tab (Identity, Employment History, Board Memberships, Investment Preferences, Internal Coverage) using per-card editing, chips+RefSelect for multi-select JSONB fields, and contact-level activity logging without a required deal
- One-liner:
- Fund CRUD API at /api/v1/funds with Alembic migration, Fund ORM model, FundService label-join pattern, and fund_status ref_data seeded with 4 TWG values
- 32 PE Blueprint columns added to Deal model via migrations 0008/0009, DealTeamMember M2M class, named FK constraints for all ref_data/company/contact/user FK columns
- DealResponse expanded with 7 resolved label fields + deal_team list, all PE scalar fields flow through PATCH, and aliased RefData joins eliminate N+1 label lookups
- DealDetailPage fully rewritten with 4-tab layout; Profile tab renders 5 section cards with per-card edit/save, fund inline create modal, and deal team chip management — all PE transaction fields now visible and editable
- deal_counterparties table via Alembic 0010 with 6 stage date columns, 2 ref_data FKs, financial fields, and DealCounterparty ORM model with Deal.counterparties cascade relationship
- DealCounterpartyService with aliased single-query joins (company_name, tier_label, investor_type_label) and nested CRUD routes at /api/v1/deals/{deal_id}/counterparties
- deal_funding table (Alembic 0011), 5 deal_funding_status ref_data seeds, DealFunding ORM, schemas, aliased-join service, and 4 CRUD endpoints at /api/v1/deals/{deal_id}/funding
- One-liner:
- One-liner:
- ADMIN-07 audit confirmed: all 10 ref_data category dropdowns across Contact, Company, Deal, and DealCounterparty/DealFunding pages use RefSelect — zero hardcoded option lists for ref_data categories
- One-liner:

---
