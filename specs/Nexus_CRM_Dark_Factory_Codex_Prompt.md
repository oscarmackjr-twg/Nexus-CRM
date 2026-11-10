# Codex Prompt — Nexus CRM Dark Factory Demo Tranche

Copy the prompt below into Codex while opened at the root of the Nexus CRM repository.

---

## BEGIN CODEX PROMPT

You are executing:

`NEXUS_CRM_DARK_FACTORY_DEMO_TRANCHE_001`

### Mission

Implement and test the bounded demo-readiness functionality defined by `Nexus_CRM_Dark_Factory_Functionality_Spec.md`, using documentation-first, architecture-first, contract-first, tests-first, and code-last sequencing.

This prompt authorizes local repository inspection, scoped documentation, tests, implementation, migrations only if proven necessary, and local validation. It does **not** authorize deployment, production data changes, cloud infrastructure changes, push, pull request creation, merge, or release publication.

### Authoritative inputs

Locate and read completely before acting:

1. `Nexus_CRM_Dark_Factory_Functionality_Spec.md`
2. `Nexus_CRM_Demo_Functionality_Priorities.md`
3. `README.md`
4. `.planning/PROJECT.md`
5. `.planning/REQUIREMENTS.md`
6. `.planning/ROADMAP.md`
7. `.planning/STATE.md`
8. Repository instructions such as `AGENTS.md`, if present

Authority precedence is defined in the specification. Do not reinterpret, broaden, or replace the required semantics.

If either of the first two inputs is not present in the repository, stop with:

`STATUS=BLOCKED_MISSING_CONTROLLING_ARTIFACT`

and list the missing paths. Do not reconstruct them from memory.

### Required scope

Implement and validate:

- `DF-FUNC-001` — visible core creation for Contacts, Companies, and Deals.
- `DF-FUNC-002` — authorized server-backed search and filters.
- `DF-FUNC-003` — replace Cmd/Ctrl+K placeholder with global record search, or hide it under the specification’s fail-safe rule.
- `DF-FUNC-004` — distinct, recoverable loading/empty/no-match/validation/API-error states.
- `DF-FUNC-005` — reversible user and group lifecycle with backend admin enforcement and self/last-admin protection.
- `DF-FUNC-006` — safe CSV export using the exact filtered and authorized view.
- `DF-FUNC-008` — clickable communication fields if it is isolated and does not jeopardize the required tranche.

Evaluate but do not force:

- `DF-FUNC-007` — My Work, only when existing next-step semantics are sufficient.
- `DF-FUNC-009` — prepare a security design and test contract only; do not implement until its separate security gate is satisfied.

### Prohibited scope

Do not add or change:

- Email/calendar synchronization.
- Automated email parsing or automatic stage updates.
- Real-time notification infrastructure.
- Placeholder-backed AI scoring or AI answers.
- New role semantics, fine-grained field permissions, or PostgreSQL RLS.
- FX conversion, investor portal, VDR distribution, cap table, waterfall, or fund accounting.
- AWS/Azure/Terraform/deployment configuration unless a non-mutating read is essential to understand current local behavior.
- Production data, credentials, secrets, remote branches, PRs, merges, or releases.

Do not regenerate or rewrite unrelated completed documentation. Preserve unrelated dirty-worktree content.

### Operating model

Execute the following gates in order. A later gate may begin only when its predecessor passes. Fail closed on missing authority, contradictory semantics, unverifiable baseline, or unsafe access behavior.

#### Gate 0 — Repository and authority verification

1. Confirm the repository root, remote identity, current branch, HEAD SHA, and worktree status.
2. Inventory unrelated modified/untracked files; preserve them.
3. Read all authoritative inputs completely.
4. Compare the current source with the reviewed baseline `3d1090d09fb0ff43760f2a95a5a778570c44ccaa`.
5. Do not require an exact baseline match. If it differs, produce a semantic drift assessment showing whether the specification remains applicable.
6. Run the existing repository-prescribed baseline checks before making changes.

Stop if baseline failures or semantic drift prevent safe attribution.

Required output fields:

```text
REPOSITORY_IDENTITY=
START_BRANCH=
START_HEAD=
WORKTREE_STATUS=
BASELINE_DRIFT_STATUS=NONE|NON_MATERIAL|MATERIAL_BLOCKING
BASELINE_TEST_STATUS=PASS|FAIL|BLOCKED
```

#### Gate 1 — Current-state and contract inventory

Inspect, at minimum:

- Backend routes, schemas, services, authorization dependencies, models, migrations, seed data, and tests for contacts, companies, deals, auth, users/groups, reference data, and exports if any.
- Frontend API clients, route registration, list/detail pages, shared grids/forms, query-key conventions, auth/role utilities, admin pages, command palette, error handling, and tests.

Identify what already exists. Reuse existing endpoints and components when their contracts are adequate. Do not implement duplicate functionality.

Prepare but do not yet write production code:

- `docs/demo-tranche/IMPLEMENTATION_CONTRACT.md`
- `docs/demo-tranche/API_CONTRACT.md`
- `docs/demo-tranche/TEST_MATRIX.md`
- `docs/demo-tranche/TRACEABILITY_MATRIX.md`

The API contract must specify parameter names, types, defaults, allowed values, sorting rules, result shapes, export rules, error codes, and authorization behavior.

Validate that all `DF-FUNC-*` requirements are represented exactly once in the traceability matrix.

#### Gate 2 — Architecture and security adjudication

Before tests or code, decide and record:

1. Whether current create endpoints are sufficient.
2. Whether search/filter extensions remain additive and backward compatible.
3. Whether global search can reuse entity list APIs or needs one bounded aggregate endpoint.
4. The maximum CSV export row count and deterministic ordering.
5. Formula-injection protection strategy.
6. Exact backend rule for current-admin and last-active-admin deactivation protection.
7. Whether My Work has authoritative due-date semantics.
8. Why password reset is blocked or what separate secure design gate is required.

If a decision changes role authority, data ownership, or password/session security beyond existing authority, stop that function at:

`STATUS=BLOCKED_PENDING_HUMAN_ADJUDICATION`

Continue independent authorized functions when isolation is proven.

#### Gate 3 — Tests first

Add failing tests from the approved test matrix before production implementation.

Required coverage includes:

- Valid, empty, invalid, unauthorized, cross-org/group, pagination, sorting, and combined-filter cases.
- Frontend create success, validation failure, API failure, retry, and double-submit prevention.
- URL/query-state restoration and page reset on filter changes.
- Global-search keyboard flow or verified absence of the placeholder.
- CSV headers, labels, ordering, quoting, UTF-8, formula-injection defense, row cap, exact filter parity, and access scoping.
- Admin deactivate/reactivate, non-admin denial, self-admin protection, last-admin protection, and safe group behavior.
- Existing behavior regression coverage.

Run the new tests and record that they fail for the expected missing behavior, not for syntax, fixture, environment, or unrelated defects.

Required output fields:

```text
TEST_CONTRACT_COUNT=
EXPECTED_RED_TEST_COUNT=
EXPECTED_RED_STATUS=PASS|FAIL|BLOCKED
UNEXPECTED_FAILURE_COUNT=
```

#### Gate 4 — Minimal implementation

Implement only enough production code to satisfy the validated contracts.

Rules:

- Use service-layer authorization and parameterized SQLAlchemy queries.
- Apply authorization predicates before count, list, global-search, and export results.
- Reuse `RefSelect` and reference-data APIs.
- Keep API changes additive.
- Keep query/filter/export semantics in shared backend functions so grid and export cannot drift.
- Preserve user input after recoverable failures.
- Provide distinct loading, empty dataset, no matches, validation error, and service error states.
- Never expose stack traces, secrets, password material, internal UUIDs in friendly export columns, or unauthorized records.
- If implementing global search becomes unsafe or materially expands scope, remove/hide the placeholder and document the disposition.
- Do not implement password reset in this execution.

After each bounded function, run its focused tests before starting the next function. Do not batch all debugging until the end.

#### Gate 5 — Full validation

Run, using repository-authoritative commands:

1. Focused backend tests.
2. Full backend test suite with coverage.
3. Backend lint/type checks.
4. Focused frontend tests.
5. Full frontend test suite.
6. Frontend lint/type/build checks as configured.
7. Alembic upgrade/downgrade validation only if a migration was necessary.
8. Docker Compose smoke validation of health, login, and required API/UI flows.
9. Automated or scripted end-to-end flows required by the specification.

Do not count skipped, xfailed, or unexecuted tests as passing. Report exact commands, exit codes, pass/fail/skip/xfail counts, coverage, and environment blockers.

If the repository’s documented command is stale, repair it only when the repair is clearly within scope and tested; otherwise report the blocker.

#### Gate 6 — Traceability and evidence

Update `docs/demo-tranche/TRACEABILITY_MATRIX.md` with actual files and test evidence.

Create `docs/demo-tranche/IMPLEMENTATION_REPORT.md` with every field required by the specification, including:

```text
PHASE=NEXUS_CRM_DARK_FACTORY_DEMO_TRANCHE_001
START_HEAD=
FINAL_HEAD=
REQUIRED_FUNCTION_STATUS=
DF_FUNC_001_STATUS=
DF_FUNC_002_STATUS=
DF_FUNC_003_STATUS=
COMMAND_PALETTE_DISPOSITION=
DF_FUNC_004_STATUS=
DF_FUNC_005_STATUS=
DF_FUNC_006_STATUS=
DF_FUNC_007_STATUS=
DF_FUNC_008_STATUS=
DF_FUNC_009_STATUS=DESIGN_GATE_ONLY
BACKEND_TEST_STATUS=
BACKEND_TEST_COUNTS=
BACKEND_COVERAGE=
FRONTEND_TEST_STATUS=
FRONTEND_TEST_COUNTS=
FRONTEND_BUILD_STATUS=
MIGRATION_STATUS=NOT_REQUIRED|PASS|FAIL|BLOCKED
E2E_STATUS=
SMOKE_STATUS=
UNRELATED_WORKTREE_PRESERVED=PASS|FAIL
PUSH_PERFORMED=NO
PR_CREATED=NO
MERGE_PERFORMED=NO
DEPLOYMENT_PERFORMED=NO
PRODUCTION_DATA_MUTATED=NO
OVERALL_STATUS=COMPLETE|PARTIAL|BLOCKED
NEXT_GATE=HUMAN_DEMO_READINESS_REVIEW
```

Every `PASS` must cite a concrete executed test or validation result. Every `BLOCKED` must state the exact cause and what authority or environment is needed.

### Completion rule

Report `OVERALL_STATUS=COMPLETE` only if DF-FUNC-001 through DF-FUNC-006 meet the specification, all required regression and quality gates pass, backend authorization is proven, the placeholder AI experience is removed or replaced, and evidence is complete.

DF-FUNC-007, DF-FUNC-008, and DF-FUNC-009 may be separately deferred or blocked as allowed by the specification. Never convert their incomplete status into a false pass.

### Final response format

Lead with the outcome and include:

1. Overall status and final HEAD.
2. Implemented functions and user-visible behavior.
3. Blocked/deferred functions and exact reasons.
4. Test/build/migration/E2E/smoke evidence with counts.
5. Files and documentation created or changed.
6. Confirmation that unrelated worktree content was preserved.
7. Confirmation that no push, PR, merge, deploy, or production mutation occurred.
8. The next human gate: `HUMAN_DEMO_READINESS_REVIEW`.

Do not claim deployment readiness, production readiness, or completion beyond the executed evidence.

## END CODEX PROMPT

