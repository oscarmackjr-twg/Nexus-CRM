# Nexus CRM — PE Deal Management Platform

## Current Milestone: v1.2 Cloud Deployment

**Goal:** Deploy Nexus CRM to AWS (primary) with a warm Azure failover using Terraform IaC and GitHub Actions CI/CD.

**Target features:**
- Terraform: AWS VPC, ECS Fargate, RDS PostgreSQL, ElastiCache Redis, ALB, ACM, Route 53, ECR, Secrets Manager
- Terraform: Azure warm failover — PostgreSQL read replica + idle ACI containers, pre-deployed, no traffic until manual cutover
- GitHub Actions pipeline — build images → push to ECR → deploy to ECS on merge to main
- AWS Secrets Manager — all secrets injected into ECS task definitions at runtime
- HTTPS with ACM certificate + ALB HTTPS listener + DNS records
- Alembic migration step baked into deploy pipeline (runs before app containers start)
- Multi-environment support (staging + prod)

## Previous Milestone: v1.1 UI Professionalism (in progress — Phases 7-12)

**Goal:** Apply the TWG Global brand identity across all screens for a professional enterprise CRM appearance.

**Target features:**
- TWG-branded login page — logo, `#1a3868` navy, staging banner, backend status indicator
- White sidebar with navy left-border active indicators (matching Intrepid-POC pattern)
- Staging banner on every authenticated page (amber-400, sticky top, env-gated)
- TWG color palette globally — replace current indigo/purple primary with `#1a3868` navy
- Gotham font + typography polish across headings, labels, and hierarchy
- Compact Salesforce-style data grids for Contacts, Companies, Deals list views
- Detail page cards polish — field layout, section headers, consistent spacing

## What This Is

A Private Equity-focused CRM built for deal teams at firms like TWG Asia. It tracks companies, contacts, deals, counterparty investor pipelines, and capital funding commitments through the full investment lifecycle — from initial outreach through diligence, NDA, LOI, and close. Built on FastAPI + React + PostgreSQL, deployed via Docker Compose.

## Core Value

Deal teams can track every counterparty touchpoint across every live deal — who signed the NDA, who got the VDR, who gave feedback, what's the next step — without leaving the CRM.

## Requirements

### Validated

<!-- Shipped and verified in production -->

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
- ✓ UI polish — professional presentation across all screens, TWG GLOBAL branding, light theme — v1.0
- ✓ TWG brand foundation — navy CSS variables, Gotham font, brand tokens globally applied — v1.1 Phase 7
- ✓ Login page — real TWG logo, StagingBanner, navy primary button, backend health indicator — v1.1 Phase 8
- ✓ White left sidebar layout — TWG logo header, grouped nav (DEALS/TOOLS/ADMIN), navy active highlight, user footer, staging banner on every authenticated page — v1.1 Phase 8
- ✓ Compact Salesforce-density data grids — shared DataGrid+Pagination components, 8-column layouts, sort indicators, hover View button, status filter bar on Deals, Deals nav link — v1.1 Phase 9
- ✓ Detail page polish — shared FieldRow component, `.detail-tabs` navy underline tabs, CardHeader border separators across Contact, Company, and Deal detail pages — v1.1 Phase 10
- ✓ Admin-configurable reference data — 12 categories, 96+ seed values, soft-delete, org-scoped — v1.0
- ✓ RefSelect component + useRefData hook — canonical dropdown infrastructure for all entities — v1.0
- ✓ Admin Reference Data UI — 12-category management page, full CRUD, query prefix invalidation — v1.0
- ✓ Contact PE Blueprint expansion — 20+ new fields, coverage persons M2M, section-card detail UI — v1.0
- ✓ Company PE Blueprint expansion — 33 new fields, financials, investment preferences, self-ref parent — v1.0
- ✓ Deal PE field expansion — 30+ fields, deal team M2M, 6 financial metrics with currencies, 8 date milestones — v1.0
- ✓ Fund entity — Fund CRUD API, fund_status ref_data, Fund inline-create on deal detail — v1.0
- ✓ DealCounterparty sub-entity — per-deal investor stage tracking (NDA→feedback), horizontal grid UI — v1.0
- ✓ DealFunding sub-entity — capital commitment tracking, provider company FK, status ref_data — v1.0

### Active

<!-- v1.1 UI Professionalism (in progress) -->

- [ ] Contact API label resolution and detail screen (CONTACT-08, CONTACT-09, CONTACT-10) — v1.1 Phase 11
- [ ] Company API label resolution and detail screen updates (COMPANY-10, COMPANY-11, COMPANY-12) — v1.1 Phase 11
- [ ] Deal detail screen and edit form for all new PE fields (DEAL-11, DEAL-12) — v1.1 Phase 12
- [ ] Fund selector available on Deal edit form (FUND-05) — v1.1 Phase 12

<!-- v1.2 Cloud Deployment -->

- ✓ AWS infrastructure provisioned via Terraform — Bootstrap (S3 state), Networking, RDS PG17, ElastiCache replication group, Secrets Manager, IAM, RDS Proxy, ECR (INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-07, INFRA-09, INFRA-10) — Validated in Phase 13
- [ ] Azure warm failover provisioned via Terraform (INFRA-06, INFRA-07)
- [ ] GitHub Actions CI/CD pipeline for ECS deployments (DEPLOY-01, DEPLOY-02, DEPLOY-03)
- [ ] Secrets management via AWS Secrets Manager (DEPLOY-04)
- [ ] HTTPS with ACM + ALB + DNS (INFRA-08)
- [ ] Multi-environment (staging + prod) support (DEPLOY-05)

### Out of Scope

- Data import/migration from PE Blueprint template — deferred until data model is stable
- Mobile app improvements — not part of current scope
- Analytics stub endpoints (pipeline-velocity, forecast, leaderboard) — remain stubs
- Screen redesign / information architecture restructuring — UI is polish only
- Multi-currency conversion — amounts stored with currency code, no FX conversion

## Context

**Shipped v1.0:** FastAPI + SQLAlchemy 2.0 async backend, React 18 + Vite + TanStack Query frontend. 139 files, ~28k lines added. Alembic migrations 0001–0011. 12 ref_data categories with 96+ seed rows. Full PE Blueprint data model for Contacts, Companies, Deals, DealCounterparties, DealFunding, and Funds.

**Tech stack:** Python/FastAPI (backend), React/Vite (frontend), PostgreSQL, Redis, Celery, Docker Compose via `make dev`.

**Demo credentials:** `admin@demo.local` / `password123` (seed data via `RUN_SEED_DATA=true` in `.env`)

**Domain:** Private Equity deal advisory / capital markets. TWG Asia manages capital raises (equity, credit, preferred equity). Core workflow: tracking counterparties (investors) through a diligence pipeline per deal — who got the NDA, who signed, who's in the VDR, feedback, next steps.

**Known tech debt (v1.0 gaps):**
- Contact/Company detail UIs are incomplete — API expanded but profile tab UIs for some fields missing
- Deal detail screen doesn't yet display all PE fields — DealDetailPage 4-tab layout built but some field cards missing
- CPARTY and FUNDING requirements in REQUIREMENTS.md were not marked complete (implementation built, checkbox skipped)

## Constraints

- **Tech stack**: Python/FastAPI backend, React/Vite frontend — no framework changes
- **Database**: PostgreSQL via SQLAlchemy 2.0 async — all new entities use Alembic migrations
- **Compatibility**: Existing API consumers must not break — new fields are additive
- **Docker**: Everything runs in Docker Compose via `make dev` — no native dependencies

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| DealCounterparty as first-class entity | Deal tracker shows per-deal investor pipeline central to PE workflow | ✓ Good — inline tab UI works well |
| DealFunding as separate entity | Capital providers and commitments are structured data for fund reporting | ✓ Good — clean separation |
| Admin-configurable reference data | Firm-specific sectors, types, tiers change over time | ✓ Good — 12 categories seeded, admin UI built |
| UI: polish only, not redesign | User confirmed fix styling/layout, not restructure screens | ✓ Good — fast, non-disruptive |
| Import deferred | Data model must be stable before migration | — Still pending |
| Light theme (reversed from dark) | User feedback during Phase 1 | ✓ Good — white content, dark blue sidebar |
| RefSelect + useRefData as canonical pattern | All dropdowns use same queryKey convention (['ref', category]) | ✓ Good — ADMIN-07 audit confirmed zero hardcoded lists |
| include_inactive param on GET /admin/ref-data | Admin UI needs to see/manage deactivated items | ✓ Good — backward compatible, no callers broken |
| Aliased RefData joins in all services | N+1 prevention for label resolution | ✓ Good — established in Phase 2, reused in 3-5 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-06 — Phase 9 complete: Compact data grids on Contacts, Companies, Deals list views — DataGrid+Pagination components, status filter bar, Deals sidebar nav link*
