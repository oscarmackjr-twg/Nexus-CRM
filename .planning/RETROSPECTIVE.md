# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

---

## Milestone: v1.0 — PE CRM Foundation

**Shipped:** 2026-03-28
**Phases:** 6 | **Plans:** 23 | **Duration:** 3 days (Mar 26–28, 2026)

### What Was Built

- Professional PE CRM UI: TWG GLOBAL branding, light theme, consistent layout across all screens
- Reference data system: 12 categories, 96+ seed values, RefSelect component as canonical dropdown pattern
- Contact & Company PE Blueprint expansion: 20+ / 33 new fields respectively, coverage persons M2M, section-card detail UIs with per-card editing
- Deal model expansion + Fund entity: 30+ PE transaction fields, deal team M2M, 8 date milestones, Fund CRUD
- DealCounterparty sub-entity: investor stage tracking (NDA→VDR→feedback), horizontally scrollable grid, inline date editing
- DealFunding sub-entity: capital commitment tracking (projected + actual), provider company FK, status ref_data
- Admin Reference Data UI: 12-category management page, add/edit/deactivate/reactivate, prefix query invalidation

### What Worked

- **Wave-based parallelization**: Plans 06-01 and 06-02 ran in parallel and both completed correctly — the audit (06-02) finished faster and its result (no changes needed) saved the 06-01 executor from redundant work
- **RefSelect + useRefData pattern**: Established in Phase 2 and consistently reused through Phase 6 with zero drift — ADMIN-07 audit confirmed zero hardcoded dropdown lists across the entire app
- **Aliased join pattern**: `aliased(RefData)` for label resolution established in Phase 2 and reused in every subsequent entity service — no N+1 issues
- **Verifier catching gaps**: Phase 6 verifier found `deal_funding_status` and `fund_status` missing from REF_CATEGORIES — caught before tag, fixed in one commit
- **CONTEXT.md quality**: Detailed discuss-phase decisions (D-01 through D-07) meant the planner could write concrete task actions without guessing

### What Was Inefficient

- **Worktree merge conflicts**: Parallel worktree agents both updated `.planning/STATE.md`, `.planning/ROADMAP.md`, and `.planning/REQUIREMENTS.md` — required manual conflict resolution when cherry-picking. The 06-01 worktree had stale phase 3/4/5 state from reading outdated STATE.md at execution start.
- **REQUIREMENTS.md checkbox skipping**: Phase 5 executor built CPARTY and FUNDING implementations but did not mark the requirements as `[x]` — left 15 requirements unchecked that were actually complete. Required manual reconciliation at milestone completion.
- **Phases 3/4 partial execution**: Plans 03-02, 03-04, 03-05, 03-06, 04-04 were in the roadmap but never executed — carried as tech debt into v1.1. The roadmap showed them as "In Progress" which caused confusion when counting completions.

### Patterns Established

- `aliased(RefData)` join pattern for label resolution in all services (Phase 2 → reused in 3, 4, 5)
- `queryClient.invalidateQueries({ queryKey: ['ref'] })` prefix invalidation after every admin mutation (Phase 6)
- `include_inactive` query param on admin endpoints — separate from the read path used by dropdowns
- `REF_CATEGORIES` array as canonical source for all category-aware UI components
- Two-tab Admin page structure: Users tab (existing) + Reference Data tab (new) via shadcn Tabs

### Key Lessons

1. **Parallel agents write to the same planning docs** — either serialize planning doc updates or use a post-merge step. Consider having executors only update their own phase SUMMARY.md and leaving STATE/ROADMAP updates to the orchestrator.
2. **Mark requirements during execution, not after** — executor agents should mark `[x]` in REQUIREMENTS.md as part of their SUMMARY commit, otherwise it falls through.
3. **Verifier is worth running** — the Phase 6 verifier found a real gap (2 missing REF_CATEGORIES) that human approval didn't catch. Always run verify before tagging.
4. **CONTEXT.md with explicit D-XX decisions produces concrete plans** — planner agents back-referenced every decision. Vague CONTEXT.md leads to vague task actions.

### Cost Observations

- Model mix: Opus (planning), Sonnet (execution + verification)
- Plans 06-01 and 06-02 ran in parallel — total wall time ≈ 15 min instead of 20 min sequential
- Phase 6 was the fastest phase (3 plans, 25 min total) because CONTEXT.md was the most detailed

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Duration | Phases | Plans | Key Pattern |
|-----------|----------|--------|-------|-------------|
| v1.0 | 3 days | 6 | 23 | Wave-parallel execution; aliased join pattern; RefSelect canonical |

### Top Lessons (Verified Across Milestones)

1. Concrete CONTEXT.md decisions (D-XX format) → concrete plan task actions → less executor drift
2. Run verifier before tagging — catches gaps human approval misses
