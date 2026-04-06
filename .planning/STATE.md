---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: UI Professionalism
status: Executing Phase 10
stopped_at: Completed 10-01-PLAN.md
last_updated: "2026-04-06T22:01:19.116Z"
progress:
  total_phases: 12
  completed_phases: 10
  total_plans: 37
  completed_plans: 33
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-03-29)

**Core value:** Deal teams can track every counterparty touchpoint across every live deal — who signed the NDA, who got the VDR, who gave feedback, what's next — without leaving the CRM.
**Current focus:** Phase 10 — detail-page-polish

## Current Status

**Milestone:** v1.1 — UI Professionalism (in progress — Phases 7-12)
**Active phase:** Phase 10 — detail-page-polish (Plan 1 of 2 complete)
**Last action:** 2026-04-06 — Plan 10-01 complete: FieldRow component, .detail-tabs CSS, ContactDetailPage + CompanyDetailPage CardHeader borders and tab styling

## Phase Completion

| Phase | Name | Status |
|-------|------|--------|
| 1 | UI Polish | Done (3/3 plans complete) |
| 2 | Reference Data System | Done (3/3 plans complete) |
| 3 | Contact & Company Expansion | Done (6/6 plans complete) |
| 4 | Deal Expansion & Fund Entity | Done (4/4 plans complete) |
| 5 | DealCounterparty & DealFunding | Done (4/4 plans complete) |
| 6 | Admin Reference Data UI | Done (3/3 plans complete) |
| 7 | Brand Foundation | Done (1/1 plans complete) — VERIFIED 2026-03-29 |
| 8 | Login, Banner & Sidebar | Done (2/2 plans complete) — VERIFIED 2026-03-29 |
| 9 | Data Grids | Not started |
| 10 | Detail Page Polish | In progress (1/2 plans complete) |
| 11 | Contact & Company Data Completeness | Not started |
| 12 | Deal & Fund Data Completeness | Not started |
| 13 | AWS Core Infrastructure | In progress (1/3 plans complete) |
| 14 | AWS Compute, CDN & HTTPS | Not started |
| 15 | CI/CD Pipeline | Not started |
| 16 | Azure Warm Failover | Not started |

## Key Files

- `.planning/PROJECT.md` — project goals and requirements
- `.planning/REQUIREMENTS.md` — 27 v1.1 requirements (Phases 7-12) + 20 v1.2 requirements (Phases 13-16)
- `.planning/ROADMAP.md` — phase breakdown with success criteria (Phases 7-16)
- `.planning/research/SUMMARY.md` — v1.2 stack, pitfalls, build order, confidence assessment
- `.planning/research/` — 4 domain research documents (stack, features, architecture, pitfalls)
- `.planning/codebase/` — 7 codebase map documents

## Key Decisions

- 01-ui-polish-03: Light theme adopted per user feedback — dark mode lock reversed. Sidebar bg-slate-900 (dark blue), content area white. CSS variable infrastructure kept for future toggle capability.
- 01-ui-polish-01: Email label on login (htmlFor=email) while keeping form.register('username') for API compat
- 01-ui-polish-01: vi.hoisted() pattern required in vitest for mock factories referencing top-level variables
- 01-ui-polish-03: Dashboard heading changed to "Deal command center" matching PE advisory context; metric computation logic left unchanged as already live-wired correctly
- 01-ui-polish-02: ContactDetailPage uses page-level h1 at top of space-y-6 wrapper with Log activity button alongside it; sidebar card name kept as p.text-3xl to avoid duplicate heading semantics
- 01-ui-polish-02: DealDetailPage Input-as-title inline editing pattern preserved; only activity timeline row padding normalized (p-4 → px-4 py-3)
- 02-01: Alembic 0002 uses explicit op.create_table DDL (not metadata.create_all) to decouple migration history from ORM model state
- 02-01: org_id=None rows are system-wide ref_data defaults; UniqueConstraint(org_id, category, value) allows multiple values per category since NULL != NULL in SQL
- 02-02: GET /admin/ref-data open to all authenticated roles (D-03) — dropdown data needed by all user roles in Phases 3-5
- 02-02: update() allows modifying system defaults (org_id=None) for org admins; rejects changes to other orgs' items with 403
- 02-02: REFDATA-15 pattern — downstream FK columns to ref_data.id must use ForeignKey('ref_data.id', ondelete='SET NULL')
- 02-03: Option value uses item.id (UUID) not item.value (slug) — backend FK references use ref_data.id, so form submissions must send UUIDs
- 02-03: useRefData queryKey ['ref', category] is canonical — all downstream phases (3-6) must use this exact key for cache sharing
- 02-03: enabled: Boolean(category) guard prevents spurious fetches when category prop is undefined/null
- 03-01: All 18 new Contact columns are nullable per D-14 — additive schema expansion with no defaults
- 03-01: contact_type_id FK uses ondelete=SET NULL per REFDATA-15 pattern — no orphan records
- 03-01: coverage_persons uses lazy=selectin — acceptable for detail views; service layer avoids N+1 on list queries
- 03-03: 0005 migration branches from 0002_pe_ref_data for parallel execution — merge migration needed after Phase 3 all plans complete
- 03-03: Company parent_company_id self-ref FK uses String(36) + remote_side='Company.id' string form for forward-ref compatibility
- 03-03: uq_companies_org_legacy_id UniqueConstraint placed in both migration and ORM __table_args__ for consistency
- 04-01: Fund ORM UUID comparisons use UUID type directly (not str) — SQLite stores UUIDs without hyphens; str conversion breaks IN queries via Uuid() type processor
- 04-01: fund_id FK added to Deal model in Plan 01 (not Plan 02) to keep migration chain clean
- 04-01: FundService aliased(RefData) label-join pattern established — reuse for DealCounterparty and DealFunding services in Phase 5
- 04-02: Named FK constraints via separate create_foreign_key() calls enable targeted drop_constraint() by name in downgrade()
- 04-02: Multiple FKs to same table require foreign_keys= on ALL relationship sides: Contact.deals, Company.deals, Deal.contact, Deal.company
- 04-02: fund_id already added to Deal ORM in Plan 01 — migration 0008 adds it to DB table; ORM type kept as Mapped[Optional[UUID]]
- 04-03: deal_team loaded only on get_deal (detail), not list_deals — avoids N+1 query per deal
- 04-03: PATCH /deals/{id} added alongside existing PUT — same service method, needed for PE field updates
- 04-03: source_individual_name uses func.trim + literal() concatenation matching existing contact_name_expr pattern
- 04-03: Test UUIDs use .hex format to match SQLite UUID storage (no hyphens) for FK join correctness
- 06-01: include_inactive query param added to GET /admin/ref-data — admin panel shows all items; regular dropdowns see only active
- 06-01: getAllRefData() added alongside getRefData() for backward compat — no existing hook callers broken
- 06-01: REF_CATEGORIES canonical ordering in refCategories.js — all downstream category references use this module
- 06-02: ADMIN-07 audit confirmed — all 10 ref_data categories use RefSelect; entity selectors (users/companies/contacts/funds) and app model enums (activity_type, lifecycle_stage, platform/addon) correctly remain as native selects
- 07-01: --primary/--ring use bare HSL triplet format without hsl() wrapper (e.g. "217 60% 25%") — tailwind.config.js wraps with hsl(); breaking this causes hsl(hsl(...)) double-wrap rendering transparent/black
- 07-01: Dark mode POC tokens use identical navy values as light mode — safe since dark mode is currently disabled
- 08-02: NavGroups data structure replaces flat navItems — Dashboard (unlabeled), DEALS, TOOLS, ADMIN groups
- 08-02: overflow-y-auto on nav prevents user footer clip on short viewports (Pitfall 3)
- 08-02: AIQueryBar placed outside flex-1 sidebar+main wrapper to avoid layout interference (Pitfall 5)
- v1.2-arch: INFRA split at Phase 13/14 boundary: 13 = networking+data+IAM+ECR (no public ingress), 14 = compute+CDN+HTTPS+DNS (app goes live)
- v1.2-arch: ElastiCache provisioned Redis only — Serverless is incompatible with Celery 5.3+ (documented AWS re:Post issue)
- v1.2-arch: DEPLOY-05 (remove Alembic from entrypoint.sh) is a Phase 15 prerequisite task, must be committed before first ECS deploy
- v1.2-arch: FAILOVER-01 pg_failover_slots must be enabled BEFORE replication subscription is created — order is mandatory
- 13-03: IAM OIDC provider conditional on var.create_oidc_provider; prod sets false to reuse account-scoped provider from staging
- 13-03: RDS Proxy uses SECRETS auth scheme with IAM role for Secrets Manager access (iam_auth=DISABLED on auth block)
- 13-03: secret_arn_pattern uses /nexus/environment/* to match Makefile tf-secrets-* target paths
- 13-03: ECR repos inline in environment main.tf (not a module) — only api and worker, frontend uses S3+CloudFront
- v1.2-arch: Terraform uses separate environment directories (environments/staging/, environments/prod/) not workspaces — HashiCorp guidance
- v1.2-arch: ACM certificate for CloudFront requires us-east-1 provider alias regardless of deployment region
- v1.2-arch: lifecycle { ignore_changes = [task_definition] } on all ECS services from day 1 — Terraform owns infra, CI owns image versions
- 13-01: S3 native locking (use_lockfile = true) used instead of DynamoDB — requires Terraform >= 1.10, eliminates separate table
- 13-01: Provider version ~> 6.0 with required_version >= 1.10, < 2.0; region ap-southeast-1 for TWG Asia context
- 13-01: create_oidc_provider = true in staging, false in prod — OIDC provider is account-scoped; staging creates it, prod reuses
- 13-01: Phase 14 forward-compat vars (app_domain, acm_certificate_arn) included in both env variables.tf with empty defaults
- 10-01: FieldRow uses named export matching Phase 9 DataGrid pattern; em-dash logic safe for zero values (financial fields); empty arrays also render as em-dash
- 10-01: ContactDetailPage and CompanyDetailPage FieldRow import added but not yet used — inline-edit Label+Input patterns preserved; FieldRow migration deferred to Phase 11
- 10-01: .detail-tabs CSS uses > button selector with data-state=active attribute; margin-bottom: -1px ensures active tab border overlaps container border cleanly

## Notes

- Seed data enabled (`.env`: `RUN_SEED_DATA=true`) — demo login: `admin@demo.local` / `password123`
- Backend `db.bind` SQLAlchemy 2.0 bug fixed in `deals.py` and `ai_service.py`
- Run `make dev` to start the app
- v1.0 complete: 6 phases, 23/23 plans done. Light theme active.
- v1.1 roadmap defined: Phases 7-12 covering 27 requirements.
- Phase 7 (Brand Foundation) is complete and verified — CSS vars + Montserrat font baseline established.
- Phase 8 (Login, Banner & Sidebar) is complete and verified.
- v1.2 roadmap defined: Phases 13-16 covering 20 requirements (7 INFRA → Phase 13, 3 INFRA → Phase 14, 5 DEPLOY → Phase 15, 5 FAILOVER → Phase 16).
- v1.1 Phases 9-12 are still pending — v1.2 planning does not block v1.1 completion.

## Performance Metrics

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 01-ui-polish | 01 | 2min | 2 | 6 |
| 01-ui-polish | 02 | 8min | 2 | 3 |
| 01-ui-polish | 03 | 15min | 3 | 4 |
| 02-reference-data-system | 01 | 18min | 2 | 4 |
| 02-reference-data-system | 02 | 2min | 2 | 4 |
| 02-reference-data-system | 03 | 5min | 2 | 4 |
| 03-contact-company-model-expansion | 01 | 2min | 2 | 3 |
| 03-contact-company-model-expansion | 03 | 2min | 2 | 2 |
| 04-deal-model-expansion-fund-entity | 01 | 2min | 2 | 8 |
| 04-deal-model-expansion-fund-entity | 02 | 4min | 2 | 3 |
| 04-deal-model-expansion-fund-entity | 03 | 30min | 2 | 4 |
| 05-deal-counterparty-deal-funding | 04 | 8min | 2 | 3 |
| 06-admin-reference-data-ui | 01 | 15min | 2 | 5 |
| 06-admin-reference-data-ui | 02 | 5min | 1 | 0 |
| 06-admin-reference-data-ui | 03 | 5min | 2 | 0 |
| 07-brand-foundation | 01 | 5min | 2 | 2 |
| Phase 08-login-banner-sidebar P01 | 1min | 2 tasks | 4 files |
| Phase 08-login-banner-sidebar P02 | 2min | 2 tasks | 2 files |
| 13-aws-core-infrastructure | 01 | 12min | 2 | 9 |
| Phase 13-aws-core-infrastructure P02 | 3min | 2 tasks | 11 files |
| Phase 13-aws-core-infrastructure P03 | 3min | 2 tasks | 11 files |
| Phase 09-data-grids P03 | 3min | 2 tasks | 4 files |
| Phase 10-detail-page-polish P01 | 8 | 4 tasks | 4 files |

## Session Continuity

Last session: 2026-04-06T22:01:19.111Z
Stopped at: Completed 10-01-PLAN.md

---
*Last updated: 2026-03-30 — Phase 13 Plan 01 complete: Terraform bootstrap + environment structure*
