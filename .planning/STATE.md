---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Executing Phase 04
stopped_at: Completed 04-02-PLAN.md
last_updated: "2026-03-27T23:21:10.482Z"
progress:
  total_phases: 6
  completed_phases: 3
  total_plans: 16
  completed_plans: 14
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-03-26)

**Core value:** Deal teams can track every counterparty touchpoint across every live deal — who signed the NDA, who got the VDR, who gave feedback, what's next — without leaving the CRM.
**Current focus:** Phase 04 — deal-model-expansion-fund-entity

## Current Status

**Milestone:** M1 — PE CRM Foundation
**Active phase:** 04 — Deal Model Expansion & Fund Entity (in progress — plan 02 complete)
**Last action:** Completed 04-02 — Deal PE fields: migrations 0008 (32 PE columns on deals table) and 0009 (deal_team_members M2M), DealTeamMember ORM class, Deal class expanded with all PE Blueprint fields (identity, source tracking, 6 financial pairs, 8 date milestones, passed/dead, legacy_id). Fixed AmbiguousForeignKeysError. 17 tests pass.

## Phase Completion

| Phase | Name | Status |
|-------|------|--------|
| 1 | UI Polish | Done (3/3 plans complete) |
| 2 | Reference Data System | Done (3/3 plans complete) |
| 3 | Contact & Company Expansion | Done (6/6 plans complete) |
| 4 | Deal Expansion & Fund Entity | In progress (2/4 plans complete) |
| 5 | DealCounterparty & DealFunding | Not started |
| 6 | Admin Reference Data UI | Not started |

## Key Files

- `.planning/PROJECT.md` — project goals and requirements
- `.planning/REQUIREMENTS.md` — 86 v1 requirements across 6 phases
- `.planning/ROADMAP.md` — phase breakdown with success criteria
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

## Notes

- Seed data enabled (`.env`: `RUN_SEED_DATA=true`) — demo login: `admin@demo.local` / `password123`
- Backend `db.bind` SQLAlchemy 2.0 bug fixed in `deals.py` and `ai_service.py`
- Run `make dev` to start the app
- Phase 1 fully complete. Light theme active: white content, dark blue sidebar, centered login page.
- Phase 2 (Reference Data System) ready to begin.

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

## Session Continuity

Last session: 2026-03-27T23:21:10.478Z
Stopped at: Completed 04-02-PLAN.md

---
*Last updated: 2026-03-27 after plan 02-03 completion (Phase 2 complete — all 3 plans done)*
