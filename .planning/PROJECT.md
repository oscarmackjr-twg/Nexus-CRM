# Nexus CRM — PE Deal Management Platform

## What This Is

A Private Equity-focused CRM built for deal teams at firms like TWG Asia. It tracks companies, contacts, deals, and counterparty pipelines through the full investment lifecycle — from initial outreach through diligence, NDA, LOI, and close. Built on FastAPI + React + PostgreSQL, deployed via Docker Compose.

## Core Value

Deal teams can track every counterparty touchpoint across every live deal — who signed the NDA, who got the VDR, who gave feedback, what's the next step — without leaving the CRM.

## Requirements

### Validated

<!-- Inferred from existing codebase — these are working and relied upon -->

- ✓ Multi-tenant org-scoped backend (FastAPI + PostgreSQL + Redis + Celery) — existing
- ✓ JWT authentication with access/refresh tokens — existing
- ✓ Role-based access control (super_admin, org_admin, team_manager, member) — existing
- ✓ Contact management with lifecycle stages, lead scoring, owner assignment — existing
- ✓ Company management with industry, size, website, country — existing
- ✓ Deal pipeline with stages, kanban view, win/loss tracking — existing
- ✓ Task boards (Kanban) with columns and due dates — existing
- ✓ Team management — existing
- ✓ LinkedIn contact import — existing
- ✓ AI deal scoring and proactive suggestions — existing
- ✓ Alembic database migrations — existing
- ✓ React frontend with TanStack Query + Zustand state management — existing

### Active

<!-- Current milestone scope -->

- [x] UI polish — login screen cleaned up, consistent spacing/typography/layout across all screens (Validated in Phase 1: UI Polish — 2026-03-27)
- [x] Contact data model expanded to PE Blueprint fields (phones, assistant, coverage persons, contact type, sector preferences, previous employment, board memberships, LinkedIn URL, legacy ID) (Validated in Phase 3: Contact/Company Model Expansion — 2026-03-27)
- [x] Company data model expanded to PE Blueprint fields (type/sub-type, AUM, EBITDA, bite sizes, investment preferences, tier, sector/sub-sector, co-invest, watchlist, coverage person, legacy ID) (Validated in Phase 3: Contact/Company Model Expansion — 2026-03-27)
- [ ] Deal data model expanded to PE deal fields (transaction type, deal team, fund, platform/add-on, source tracking, financial metrics: revenue/EBITDA/EV/equity investment, date milestones: CIM/IOI/LOI/management presentation/live diligence/portfolio company, passed/dead reasons, legacy ID)
- [ ] DealCounterparty entity — per-deal investor/counterparty pipeline with stage tracking (NDA signed, NRL signed, intro materials sent, VDR access, feedback, next steps, contact info, tier, check size, AUM, investor type)
- [ ] DealFunding entity — capital provider commitment tracking per deal (capital provider, projected commitment, actual commitment, terms, comments/next steps)
- [ ] Admin-configurable reference data with pre-populated TWG values: Sectors, Sub-Sectors, Transaction Types, Tiers, Contact Types, Company Types, Company Sub-Types, Currencies, Deal Source Types, Passed/Dead Reasons
- [ ] All expanded fields surfaced in the relevant UI screens (contact detail, company detail, deal detail)
- [ ] Dashboard and list views updated to reflect new data model

### Out of Scope

- Data import/migration from PE Blueprint template — deferred to a later phase once the data model is stable
- Mobile app improvements — not part of this milestone
- Analytics stub endpoints (pipeline-velocity, forecast, leaderboard) — remain stubs for this milestone
- Screen redesign / information architecture restructuring — UI work is polish only, not redesign
- Multi-currency conversion — amounts stored with currency code, no FX conversion

## Context

**Codebase state:** Full-stack CRM with backend (FastAPI, SQLAlchemy 2.0, PostgreSQL), React frontend (Vite, TanStack Query, Recharts), Celery workers. Phase 3 complete — Contact and Company models fully expanded with PE Blueprint fields: 19 new Contact columns + contact_coverage_persons M2M, 33 new Company columns, Pydantic schemas with resolved ref_data labels, service layer with aliased RefData joins, and Profile tab UIs with per-card editing, chips+RefSelect, and row UI for employment/board memberships.

**Domain:** Private Equity deal advisory / capital markets. TWG Asia is a deal team that manages capital raises (equity, credit, preferred equity). Their workflow centers on tracking counterparties (investors) through a diligence pipeline for each deal — who got the NDA, who signed, who's in the VDR, what's the feedback.

**Source data structures:**
- PE Blueprint Import Template — defines Company, Contact, Deal, DealFunding, Interaction schemas for the firm's existing CRM (Intapp DealCloud)
- TWG Asia Deal Tracker — per-deal counterparty tracking spreadsheet with deal name, format, TWG owner, and per-counterparty rows (NDA/NRL/materials/VDR/feedback/next steps)

**Reference data:** Admin-configurable with pre-populated values. Sectors include PE-relevant categories (Financial Services, Technology, Healthcare, Real Estate, Infrastructure, Consumer, Industrials, Energy). Transaction Types include Equity, Credit, Preferred Equity, Mezzanine, Growth Equity. Contact Types include LP, GP, Advisor, Management, Lender.

## Constraints

- **Tech stack**: Python/FastAPI backend, React/Vite frontend — no framework changes this milestone
- **Database**: PostgreSQL via SQLAlchemy 2.0 async — all new entities use Alembic migrations
- **Compatibility**: Existing API consumers (frontend) must not break — new fields are additive
- **Docker**: Everything runs in Docker Compose via `make dev` — no native dependencies

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| DealCounterparty as first-class entity | Deal tracker shows a per-deal investor pipeline that's central to PE workflow — not just notes | — Pending |
| DealFunding as separate entity | Capital providers and commitments are structured data used for fund reporting, not freeform | — Pending |
| Admin-configurable reference data | Firm-specific sectors, types, tiers change over time — hardcoding creates maintenance burden | — Pending |
| UI: polish only, not redesign | User confirmed fix styling/layout, not restructure screens | — Pending |
| Import deferred | Data model must be stable before migration — get the schema right first | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-26 after initialization*
