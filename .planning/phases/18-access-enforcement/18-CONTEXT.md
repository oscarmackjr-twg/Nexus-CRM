# Phase 18: Access Enforcement - Context

**Gathered:** 2026-06-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn the Phase 17 schema (four-role model + group membership + `Deal.team_id`) into **enforced** access rules at the API/service layer:

- Every Deal endpoint enforces group-scoped read/write/delete based on the four-role model (Regular User / Supervisor / Principal / Admin)
- Out-of-scope record requests return **HTTP 403** (not 404); truly nonexistent IDs return 404
- Contacts and Companies are confirmed globally readable (ACCESS-01)
- A **reusable authorization module** is built so Phase 19 (Calls/Notes) can plug in with minimal new code

**Not in this phase:** Call and Note entities (Phase 19 — models/routes don't exist yet). DB-layer row-level security / PostgreSQL RLS (explicitly out of scope per REQUIREMENTS.md — enforcement stays in the application service layer). Modification history (Phase 20). Reports (Phase 21).

</domain>

<decisions>
## Implementation Decisions

### 403 / 404 Leakage Matrix
- **D-01:** Out-of-scope **existing** record on detail GET `/{id}` → **403 Forbidden** (locks ACCESS-07 + success criterion #6: "return 403, not 404").
- **D-02:** **Nonexistent** ID (never created / wrong UUID) → **404 Not Found**. Clean split: 403 = "exists, forbidden", 404 = "no such record".
- **D-03:** LIST endpoints → out-of-scope records are **silently filtered out** of results (no error). Pagination/counts reflect only visible records. No "hidden total" exposed.
- **D-04:** Out-of-scope WRITE/DELETE (e.g., Regular User edits/deletes another group's deal) → **403** (consistent with reads; locks success criterion #2).
- **D-05:** "Allowed-but-action-denied" (e.g., Supervisor tries to DELETE a group member's deal — criterion #3) → **403, same as out-of-scope** (uniform; no separate status). Distinct detail messages are optional/Claude's discretion.

### Role Write/Delete Matrix
- **D-06:** **Principal** = **read-all across all groups + CRUD on own records only**. The cross-group power is read/reporting only; for writes a Principal behaves like a Regular User on their own records. (Matches ACCESS-05's read-only wording.)
- **D-07:** **Owner can always delete their own record** (delete permission = owns-it OR is-admin). This applies to Supervisors too — the "no delete" rule (criterion #3) only blocks deleting **other** group members' deals, not the Supervisor's own.
- **D-08:** **Supervisor** = read + edit any deal of their group's members; **cannot delete** other members' deals (403); **can** delete own (per D-07).
- **D-09:** **Admin** = full CRUD on any deal across any group; never receives 403.
- **D-10:** **Regular User** = CRUD on own deals; read deals visible to their group (per visibility rules); 403 on other groups' deals.
- **D-11:** `is_private` hides a deal from **same-group peers only** — Supervisor (of that group), Principal, and Admin still see it. Oversight roles are not blinded by the checkbox. (Reconciles/replaces current owner-only `private_deal_predicate` behavior.)
- **D-12:** On CREATE, a deal's `team_id` is **forced server-side to the creator's own group**; any `team_id` in the payload is ignored. (Admins may override — planner's discretion on the admin path.)
- **D-13:** **Only Admin** can reassign a deal's `team_id` or `owner_id` via update. For non-admins these fields are immutable (ignored or 403 if changed) — prevents a user moving a record out of their own access.

### Enforcement Architecture
- **D-14:** Centralize the four-role scoping in **one reusable authz module** (single source of truth — e.g. a new `backend/auth/access.py` or consolidated `_crm.py` helpers) exposing functions like a visible-team query predicate, `can_write(user, record)`, `can_delete(user, record)`. Every service calls these; Phase 19 reuses them verbatim. No per-service reimplementation.
- **D-15:** Two complementary enforcement points: **(a)** a reusable SQL **query predicate** for list/read scoping (replaces the broken `accessible_team_ids`), and **(b)** an **action guard** invoked in get/update/delete that loads the record and raises 403/404 per D-01/D-02.
- **D-16:** **Full rewrite** to the four-role model — replace `accessible_team_ids()` (currently returns own-team for everyone, wrong for Admin/Principal) and reconcile `private_deal_predicate()` with D-11. Update `DealService` and any already-scoped callers to the corrected behavior. Do it right once rather than layering a second system.

### Entity Scope (this phase)
- **D-17:** Enforce group-scoping on **Deals** (top-level). Confirm **Contacts & Companies are global-read** (ACCESS-01).
- **D-18:** Contacts & Companies **writes remain open to any authenticated user** — requirements specify only global read and say nothing about restricting their writes. Do not add restrictions not in scope. (Keep current behavior; `ensure_owner_or_admin` exists but is not applied here.)
- **D-19:** Deal **child entities inherit the parent deal's visibility** — DealActivity, DealCounterparty, DealFunding: if a user can't see the deal, they can't see its children (403). Guards on those endpoints must check parent-deal scope (close the side-door).
- **D-20:** **Funds** are treated as **global / org-level reference data** — no group scoping.
- **D-21:** **Calls/Notes are NOT wired this phase** (don't exist until Phase 19). Build the authz module shaped so Phase 19 adds them with one line each. No stubs/dead code for nonexistent entities.

### Claude's Discretion
- Exact module name/location for the authz helpers (`backend/auth/access.py` vs. expanding `backend/services/_crm.py`).
- Whether 403 responses carry distinct detail messages for "out of scope" vs "insufficient role for delete" (D-05 allows either).
- The specific admin-override path for create/reassign (D-12, D-13).
- Whether list scoping uses a pure SQL predicate or a hybrid load-then-filter for low-volume endpoints (D-15 prefers predicate; efficiency call is the planner's).
- Test fixtures/strategy for exercising the full role × action matrix.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — ACCESS-01 to ACCESS-07 (full access-control requirement definitions); also note "Out of Scope (v1.3)": PostgreSQL RLS excluded, enforcement in application service layer
- `.planning/ROADMAP.md` §Phase 18 — Goal, 6 success criteria (the authoritative 403-not-404 + role matrix statements), dependency on Phase 17

### Prior Phase Context (schema this phase enforces)
- `.planning/phases/17-groups-roles-authorship-schema/17-CONTEXT.md` — D-01..D-03 (Team table = Group; `User.team_id` = membership; `Deal.team_id` already scopes deals), D-05..D-07 (role string values `regular_user`/`supervisor`/`principal`/`admin`; route guards updated)

### Backend auth & enforcement (the code to rewrite/extend)
- `backend/auth/security.py` — `get_current_user`, `require_org_admin` (checks `role == admin`); JWT/role plumbing
- `backend/services/_crm.py` — `accessible_team_ids` (BROKEN: returns own-team for everyone — rewrite per D-16), `private_deal_predicate` (owner-only today — reconcile per D-11), `is_admin`, `is_manager_plus`, `ensure_owner_or_admin`, `ensure_*_in_org` helpers
- `backend/services/deals.py` — `DealService` (`_visible_team_ids`, `_base_deal_stmt`, get/update/delete/create) — primary integration site
- `backend/api/routes/deals.py` — Deal routes (list/get/create/update/patch/delete/move-stage/activities) — where guards apply
- `backend/api/routes/counterparties.py`, `backend/api/routes/funding.py` — deal-child endpoints needing parent-scope guards (D-19)
- `backend/models.py` — `Deal` (`team_id` NOT NULL line ~420, `owner_id` line ~430, `is_private` line ~439), `DealActivity` (`is_private` line ~518), `User.team_id` (~85), `Contact`/`Company` (owner_id but no `team_id` → confirms global-read), `Fund` (~305, global)

### Frontend (consumes 403/404 semantics)
- `frontend/src/` — API error handling must distinguish 403 (forbidden, show "no access") from 404 (not found); planner to confirm interceptor behavior

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/services/_crm.py` helpers (`is_admin`, `is_manager_plus`, `ensure_owner_or_admin`, `count_rows`, pagination) — extend these into the centralized authz module (D-14)
- `DealService(db, current_user)` constructor pattern — `current_user` already threaded into every service; the guard functions can consume it directly
- `private_deal_predicate` / `_base_deal_stmt` — existing WHERE-clause composition pattern to build the new query predicate on (D-15)

### Established Patterns
- Service-layer enforcement: routes are thin (`return await DealService(db, current_user).x(...)`); all scoping belongs in the service/helper layer — consistent with REQUIREMENTS.md "enforced in application service layer"
- Existing 403 raising: `raise HTTPException(status_code=403, ...)` (e.g. `require_org_admin`, `ensure_owner_or_admin`); 404 via `ensure_*_in_org`
- Role check style: `user.role in (...)` tuples (`is_admin`, `is_manager_plus`) — extend to a `principal`-aware set
- `org_id` scoping is already universally applied (`Deal.org_id == current_user.org_id`); group scoping layers on top of it, not instead of it

### Integration Points
- `accessible_team_ids()` is the single chokepoint feeding `_base_deal_stmt` — rewriting it propagates correct list scoping to all deal queries
- `get_deal` / `update_deal` / `delete_deal` in `DealService` — insert the action guard (load record → 403/404 decision) here
- Deal-child route services (counterparties, funding, activities) — add parent-deal scope check before returning/mutating
- Frontend API client error interceptor — must surface 403 vs 404 distinctly

</code_context>

<specifics>
## Specific Ideas

- The 403-not-404 rule is a hard requirement repeated in ROADMAP success criterion #6 and ACCESS-07 — treat the full matrix (D-01..D-05) as a verification checklist, not a suggestion.
- Build the authz module API generically enough (operates on "a record with `team_id` and `owner_id`") that Phase 19 Calls/Notes register with one line each (D-21).

</specifics>

<deferred>
## Deferred Ideas

- **Call & Note entity enforcement** — Phase 19 (entities don't exist yet); authz module is designed to absorb them.
- **Distinct 403 detail messages** ("out of scope" vs "insufficient role for delete") — optional UX nicety; planner may include or skip (D-05).
- **Tasks/Boards group scoping** — those entities have `team_id`/`is_private` but are outside the v1.3 access-control entity list; not enforced here unless they ride on the shared helper rewrite incidentally.
- **PostgreSQL row-level security (RLS)** — explicitly out of scope for v1.3 per REQUIREMENTS.md; enforcement stays in the application layer.

</deferred>

---

*Phase: 18-access-enforcement*
*Context gathered: 2026-06-29*
