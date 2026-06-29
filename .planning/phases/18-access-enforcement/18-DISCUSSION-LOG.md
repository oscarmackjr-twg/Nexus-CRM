# Phase 18: Access Enforcement - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-29
**Phase:** 18-access-enforcement
**Areas discussed:** 403/404 leakage matrix, Role write/delete matrix, Enforcement architecture, Phase entity scope

---

## 403/404 Leakage Matrix

| Option | Description | Selected |
|--------|-------------|----------|
| 403 Forbidden | Out-of-scope existing record on detail GET → 403 (matches criterion #6) | ✓ |
| 404 Not Found | Hide existence — contradicts roadmap | |

| Option | Description | Selected |
|--------|-------------|----------|
| 404 Not Found | Nonexistent ID → 404; out-of-scope=403, missing=404 | ✓ |
| 403 (everything) | 403 for both out-of-scope and nonexistent | |

| Option | Description | Selected |
|--------|-------------|----------|
| Silently filtered out | List returns only in-scope records, no error | ✓ |
| Filtered + show total | Expose hidden/total count | |

| Option | Description | Selected |
|--------|-------------|----------|
| 403 Forbidden | Out-of-scope write/delete → 403 (criterion #2) | ✓ |
| 404 Not Found | Hide existence on writes | |

| Option | Description | Selected |
|--------|-------------|----------|
| 403, same as out-of-scope | Supervisor-can't-delete returns uniform 403 | ✓ |
| Different error bodies | Distinct detail messages per cause | |

**User's choice:** Out-of-scope (read & write) → 403; nonexistent → 404; lists silently filtered; allowed-but-action-denied → uniform 403.
**Notes:** Locks ACCESS-07 and success criteria #2, #3, #6. Distinct 403 detail messages left optional.

---

## Role Write/Delete Matrix

| Option | Description | Selected |
|--------|-------------|----------|
| Read-all + CRUD own only | Principal reads cross-group, writes only own records | ✓ |
| Read-all, zero writes | Pure reporting role, no writes at all | |
| Read-all + edit-all | Edit across all groups (scope expansion) | |

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — owner can always delete own | Delete = owns-it OR admin; Supervisor deletes own | ✓ |
| No — Supervisors never delete | Role blocks all deletes incl. own | |

| Option | Description | Selected |
|--------|-------------|----------|
| Private from peers only; oversight roles still see | is_private hides from same-group peers; Supervisor/Principal/Admin still see | ✓ |
| Private means owner-only (current) | Only owner sees, even admins filtered | |
| Drop is_private interaction this phase | Leave as-is, don't reconcile | |

| Option | Description | Selected |
|--------|-------------|----------|
| Forced to creator's own group | team_id set server-side; payload ignored | ✓ |
| Payload team_id, validated | Honor payload if writable | |

| Option | Description | Selected |
|--------|-------------|----------|
| Only Admin can reassign group/owner | Non-admins cannot change team_id/owner_id | ✓ |
| Owner can reassign within writable scope | Change allowed if both ends writable | |
| You decide | Defer to planner | |

**User's choice:** Principal = read-all + CRUD-own; owner always deletes own (incl. Supervisors); is_private hides from peers only; create forces creator's group; only Admin reassigns team/owner.
**Notes:** Reconciles the existing owner-only private_deal_predicate toward an oversight model.

---

## Enforcement Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| One reusable authz module | Single source of truth; Phase 19 reuses | ✓ |
| Inline per service | Each service implements its own checks | |

| Option | Description | Selected |
|--------|-------------|----------|
| Query predicate + action guard | SQL predicate for lists + guard for single-record 403/404 | ✓ |
| Guard-only (load then check) | Always load then filter in Python | |

| Option | Description | Selected |
|--------|-------------|----------|
| Rewrite to four-role model fully | Replace accessible_team_ids/private_deal_predicate, update callers | ✓ |
| New module, leave old helpers | Two scoping systems coexist | |

**User's choice:** Centralized authz module; query-predicate + action-guard pattern; full rewrite of broken helpers.
**Notes:** accessible_team_ids currently returns own-team for everyone — wrong for Admin/Principal.

---

## Phase Entity Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Deals + global Contacts/Companies, build reusable layer | Enforce Deals; Contacts/Companies global-read; layer ready for Phase 19 | ✓ |
| Also stub Calls/Notes enforcement now | Pre-write hooks for nonexistent entities | |

| Option | Description | Selected |
|--------|-------------|----------|
| Any authenticated user can write | No role/group gating on Contact/Company writes | ✓ |
| Owner-or-admin to edit/delete | Apply guard for consistency (scope expansion) | |
| You decide | Defer to planner | |

| Option | Description | Selected |
|--------|-------------|----------|
| Children inherit deal scope; Funds global | DealActivity/Counterparty/Funding inherit parent; Funds global | ✓ |
| Only top-level Deals this phase | Leave child endpoints unguarded | |
| You decide | Defer to research | |

**User's choice:** Enforce Deals + confirm global-read Contacts/Companies (writes open); deal children inherit deal scope; Funds global; Calls/Notes deferred to Phase 19.
**Notes:** Authz module built generically so Phase 19 wires Calls/Notes in with one line each.

---

## Claude's Discretion

- Exact authz module name/location (`backend/auth/access.py` vs. expanding `_crm.py`)
- Whether 403 responses carry distinct detail messages per cause
- Admin-override path for create/reassign
- SQL-predicate vs. load-then-filter for low-volume list endpoints
- Test fixtures/strategy for the role × action matrix

## Deferred Ideas

- Call & Note entity enforcement — Phase 19
- Distinct 403 detail messages — optional UX nicety
- Tasks/Boards group scoping — outside v1.3 access-control entity list
- PostgreSQL RLS — explicitly out of scope for v1.3
