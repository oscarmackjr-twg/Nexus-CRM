# Nexus CRM — Dark Factory Demo Functionality Specification

**Specification ID:** `NEXUS-CRM-DF-DEMO-001`  
**Status:** Candidate implementation authority  
**Repository:** `oscarmackjr-twg/Nexus-CRM`  
**Controlling source:** `Nexus_CRM_Demo_Functionality_Priorities.md`  
**Baseline reviewed:** `main` at `3d1090d09fb0ff43760f2a95a5a778570c44ccaa`  
**Date:** 2026-09-02

## 1. Mission

Add and test a bounded set of low-effort, high-visibility CRM capabilities that make the proof of concept credible for both basic and administrative users. The implementation must preserve the PE-specific counterparty workflow and the existing FastAPI, React, PostgreSQL, JWT/RBAC, TanStack Query, and Docker Compose architecture.

The delivery sequence is documentation-first, architecture-aware, contract-first, tests-first, and code-last. No feature is complete merely because a control is visible in the UI; its API behavior, authorization, failure handling, and automated tests must also be complete.

## 2. Authority and precedence

When sources conflict, apply this order:

1. This specification for the bounded demo tranche.
2. `Nexus_CRM_Demo_Functionality_Priorities.md` for business priority and exclusions.
3. Existing repository tests and published API contracts for backward compatibility.
4. `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, and `.planning/ROADMAP.md` for existing product decisions.
5. Current implementation as evidence of behavior, not permission to contradict higher authority.

Any unresolved normative conflict is a stop condition. Record it; do not invent replacement semantics.

## 3. Actors

| Actor | Meaning | Required access in this tranche |
|---|---|---|
| Regular User | Authenticated basic CRM user | Create, read, search, filter, and update permitted core records within existing org/group rules; export only records the user may read |
| Supervisor | Existing elevated group role | Same functionality, with existing same-group permissions preserved |
| Principal | Existing cross-group reporting/read role | Search and export only within current backend authority; no new write authority |
| Admin | Existing administrative role | User/group lifecycle recovery and current CRM access; no implicit superuser bypass beyond existing backend policy |

Authorization must be enforced by the backend. Frontend visibility is usability, not a security boundary.

## 4. Delivery scope

### Tranche A — Required before demo

#### DF-FUNC-001: Core record creation

Provide visible `New Contact`, `New Company`, and `New Deal` actions on their list pages.

Requirements:

- Use existing create endpoints and schemas where adequate; extend them additively only when required.
- Present a focused create form containing the minimum fields needed to create a valid record.
- Use existing reference-data APIs and `RefSelect`; do not introduce hard-coded governed dropdown values.
- Validate required fields client-side and server-side.
- Preserve entered values after a recoverable validation or API failure.
- On success, invalidate relevant queries and navigate to the new detail record.
- Prevent duplicate submission while a request is pending.
- Do not add delete or bulk-create behavior in this tranche.

Minimum fields:

| Entity | Required UI fields | Optional high-value fields |
|---|---|---|
| Contact | First name, last name | Company, title, email, phone, owner, lifecycle stage |
| Company | Name | Type, tier, sector, website, owner |
| Deal | Name | Company, pipeline/stage, status, owner, value/currency, expected close date |

The implementation must defer to stricter current API requirements discovered during contract inventory.

#### DF-FUNC-002: Search and filters

Add server-backed search and filters to Contacts, Companies, and Deals.

Requirements:

- Search must be case-insensitive and safely parameterized.
- Search must be debounced on the frontend.
- Every search/filter change resets pagination to page 1.
- Search, filters, sorting, page, and page size must produce one coherent query contract.
- Prefer URL query parameters so the view can be refreshed or shared without losing state.
- Empty filtered results must be distinct from an empty dataset.
- Invalid filter identifiers or values must fail predictably without a server error.
- Org and group access predicates must be applied before results, counts, and exports are returned.

Minimum filter contract:

| Page | Search fields | Filters |
|---|---|---|
| Contacts | Name, email, company | Company, owner, lifecycle stage |
| Companies | Name, website/domain | Company type, tier, sector, owner |
| Deals | Name, company | Stage, status, owner |

#### DF-FUNC-003: Command palette disposition

The existing Cmd/Ctrl+K placeholder must not remain visible as unfinished functionality.

Preferred implementation:

- Convert it to global record search across Contacts, Companies, and Deals.
- Group results by entity type.
- Display a maximum of five results per entity plus a clear no-results state.
- Support keyboard navigation, Enter to open, Escape to close, and a visible discoverable trigger.
- Reuse authorized list/search APIs; do not generate SQL or invoke unfinished AI behavior.

Fail-safe fallback:

- If global search cannot be completed without unsafe API expansion, remove the shortcut and visible placeholder from the demo build.
- Record `COMMAND_PALETTE_DISPOSITION=HIDDEN_WITH_REASON` in the implementation report.

#### DF-FUNC-004: Recoverable loading, empty, validation, and error states

For the three list pages and new create flows:

- Loading uses the established skeleton pattern.
- Empty dataset and no filter matches use different copy.
- API failure shows a non-destructive error with Retry.
- Retry preserves query/filter/form state.
- Field validation is associated with the relevant field when practical.
- Server messages must be safely presented; no stack traces or secrets may reach the browser.
- Error states must be covered by component tests.

#### DF-FUNC-005: Reversible user and group lifecycle

Complete the current admin lifecycle.

Requirements:

- Users page can include inactive users and filter by status.
- Admin can reactivate an inactive user.
- Groups page can reactivate an inactive group.
- Deactivation and reactivation require confirmation and produce success/failure feedback.
- The system must prevent deactivation of the current admin when that would make the session invalid.
- The system must prevent deactivation of the last active admin in the organization.
- Group reactivation does not silently restore or change user assignments unless existing authoritative behavior already defines it.
- Admin endpoints must reject non-admin callers regardless of frontend routing.

### Tranche B — Strong demo enhancement

#### DF-FUNC-006: CSV export of current filtered view

Requirements:

- Export Contacts, Companies, and Deals using the same authorized search/filter/sort semantics as the grid.
- Export the complete filtered result, not only the visible page, subject to a documented safe row limit.
- Use friendly labels instead of internal UUIDs where labels exist.
- Define an explicit stable column list per entity; do not export secrets, tokens, internal audit payloads, or unauthorized financial fields.
- Use RFC 4180-compatible CSV, UTF-8 encoding, and spreadsheet-safe handling for values beginning with `=`, `+`, `-`, or `@`.
- Filename format: `nexus_<entity>_<UTC timestamp>.csv`.
- Empty authorized results produce a header-only file or a clear no-data response, consistently documented and tested.

#### DF-FUNC-007: My Work dashboard card

Build only if existing authoritative next-step/due-date data can support it without inventing a new task model.

- Show overdue and upcoming authorized items.
- Sort overdue first, then ascending due date.
- Link every item to its source record.
- Do not introduce notifications, background reminders, or automatic stage updates.
- If source semantics are insufficient, stop this function as `BLOCKED_PENDING_PRODUCT_DECISION` without blocking completed functions.

#### DF-FUNC-008: Clickable communication fields

- Render valid email, phone, website, and LinkedIn values as `mailto:`, `tel:`, or safe external HTTPS links.
- Normalize schemes without allowing `javascript:` or other unsafe protocols.
- External links open consistently and include appropriate rel attributes.
- Invalid or absent values remain plain text or an em dash.

### Tranche C — Admin enhancement; separate gate

#### DF-FUNC-009: Admin-assisted password reset

This function requires an explicit security design gate before implementation.

Candidate contract:

- Admin initiates a time-limited, single-use reset flow or generates a temporary credential that must change at next login.
- No stored password or password hash is ever returned.
- Action is rate-limited and audit-attributed.
- Reset invalidates appropriate active refresh tokens.
- User enumeration and cross-organization reset are prohibited.

Codex may prepare the design, tests, and migration plan, but must not implement a weaker ad hoc password-reset mechanism merely to complete the demo.

## 5. Explicit exclusions

- Email/calendar synchronization.
- Automated email parsing or counterparty-stage updates.
- Real-time notifications or notification preferences.
- AI scoring or AI-generated answers backed by placeholder endpoints.
- Fine-grained field permissions or new role semantics.
- PostgreSQL row-level security migration.
- FX conversion.
- Investor portal, VDR distribution, cap table, waterfall, or fund-accounting behavior.
- Deployment, production data mutation, cloud infrastructure changes, push, PR, or merge.

## 6. Architecture constraints

- Preserve Python/FastAPI, SQLAlchemy 2.0 async, Pydantic, PostgreSQL/Alembic, React 18/Vite, TanStack Query, Zustand, React Router, and Tailwind/Radix conventions.
- API changes must be additive and backward compatible.
- Reuse current service-layer authorization predicates; do not duplicate access policy in route handlers.
- Reuse shared frontend components and established query-key conventions.
- No hard-coded reference-data lists when a governed reference category exists.
- Database schema changes require Alembic upgrade/downgrade coverage and are disallowed unless a scoped function genuinely requires them.
- Preserve unrelated dirty-worktree changes.

## 7. Contract and design artifacts required before code

Codex must prepare and validate these repository-local artifacts before implementation:

1. `docs/demo-tranche/IMPLEMENTATION_CONTRACT.md`
2. `docs/demo-tranche/API_CONTRACT.md`
3. `docs/demo-tranche/TEST_MATRIX.md`
4. `docs/demo-tranche/TRACEABILITY_MATRIX.md`

The traceability matrix must map every `DF-FUNC-*` requirement to files, API routes, backend tests, frontend tests, and final status.

## 8. Test contract

### Backend

- Unit/service tests for search predicates, filters, counts, export mapping, and lifecycle rules.
- API tests for valid, empty, invalid, unauthorized, cross-org/group, and pagination cases.
- CSV tests for headers, ordering, quoting, UTF-8, formula-injection defense, row limit, and authorization.
- Admin lifecycle tests for non-admin denial, self/last-admin protection, reactivation, and idempotent invalid transitions.

### Frontend

- Component tests for create success, validation failure, API failure, retry, and double-submit prevention.
- List tests for debouncing, query reset, filter combinations, URL-state restoration, empty/no-match/error distinctions, and pagination consistency.
- Command palette tests for keyboard behavior and navigation, or an assertion that the placeholder is absent when hidden.
- Admin tests for include-inactive, deactivate/reactivate confirmation, feedback, and permission gating.
- Export tests for request parameters, disabled/pending state, success, and error feedback.

### Integration and end-to-end

At least one automated flow for each:

1. Create Contact → find by search → open → update.
2. Create Company → filter → open → update.
3. Create Deal → filter by status/stage/owner → open → update.
4. Apply filters → paginate/sort → export → validate exported scope.
5. Admin deactivates and reactivates a user and a group.
6. Regular user receives 403 from admin lifecycle APIs.
7. Cmd/Ctrl+K global search opens an authorized result, or the placeholder is absent.

### Quality gates

- Existing backend test suite remains green and meets the repository coverage gate.
- Existing frontend test suite remains green.
- New changed backend code should meet or exceed 85% line coverage unless the repository enforces a stricter threshold.
- Lint, type checks, frontend build, Alembic validation if applicable, and Docker-backed smoke test must pass.
- No skipped or xfailed new test may be counted as passing evidence.

## 9. Demo data contract

Seed data must remain deterministic and idempotent and include:

- At least one active user for each existing role.
- At least two active groups and one inactive group.
- At least one inactive non-admin user available for reactivation.
- Several linked companies and contacts spanning owners, tiers, sectors, and lifecycle stages.
- At least two deals in different stages/statuses with owners, counterparties, next steps, and dates.
- No production-identifying personal or client data.

## 10. Evidence and completion report

Create `docs/demo-tranche/IMPLEMENTATION_REPORT.md` containing:

- Baseline and final commit identities.
- Dirty-worktree inventory before and after.
- Files changed, migrations added, and routes changed.
- Requirement-by-requirement status: `PASS`, `BLOCKED`, or `NOT_IMPLEMENTED`.
- Exact commands executed, exit codes, test counts, failures/skips/xfails, coverage, build result, and smoke-test result.
- Command-palette disposition.
- Password-reset gate status.
- Known limitations and residual risks.
- Explicit statement that no deploy, production mutation, push, PR, or merge occurred.

## 11. Completion conditions

The tranche may be reported `COMPLETE` only when:

- DF-FUNC-001 through DF-FUNC-006 pass all mapped tests.
- DF-FUNC-003 is either implemented as global record search or safely hidden with documented evidence.
- All existing and new required quality gates pass.
- No visible rehearsed-demo control leads to placeholder-only functionality.
- Authorization tests prove backend enforcement.
- The implementation and traceability reports are complete and truthful.

DF-FUNC-007 through DF-FUNC-009 may be separately `BLOCKED` or deferred without falsifying completion of the required tranche, provided their status and reasons are explicit.

## 12. Stop conditions

Stop and report without guessing if:

- The checked-out repository or branch is not the intended Nexus CRM repository.
- Authority files are missing or conflict materially.
- The baseline has changed in a way that invalidates the contract inventory.
- Existing tests fail before scoped changes and the failure cannot be attributed safely.
- Current authorization semantics cannot support a requirement without a new normative role decision.
- Password reset lacks a safe token/session design.
- A requested change would require an excluded integration or production operation.
- Credentials, production secrets, or real client data appear in the worktree or test fixtures.

