# Phase 2: Reference Data System - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 02-reference-data-system
**Areas discussed:** Sub-sector seed values, GET endpoint access, Duplicate handling, RefSelect UX

---

## Sub-Sector Seed Values

| Option | Description | Selected |
|--------|-------------|----------|
| Start empty | sub_sector category exists but ships with no values; org admin populates via Admin UI | |
| Pre-seed with PE sub-sectors | Add a meaningful starter list of sub-sectors relevant to PE deal teams | ✓ |
| Mirror the sector list | Use the 10 sector values as sub-sectors | |

**User's choice:** Pre-seed with PE sub-sectors
**Follow-up:** Claude picks the specific values (no user input needed on exact sub-sector list)

---

## GET Endpoint Access Level

| Option | Description | Selected |
|--------|-------------|----------|
| All authenticated users | Any logged-in user can read ref data; required for form dropdowns across all roles | ✓ |
| org_admin only | Only org admins can read; would require a separate lower-privilege route for forms | |
| Split /ref-data vs /admin/ref-data | GET /ref-data for all users, GET/POST/PATCH /admin/ref-data for org_admin | |

**User's choice:** All authenticated users
**Notes:** GET has `Depends(get_current_user)` only; POST and PATCH have `require_role("org_admin")`

---

## Duplicate Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Return both | Union of system defaults + org items; no dedup; org admin deactivates system default to replace | ✓ |
| Org item wins | Suppress system default when org creates a matching item; deduplicate by value in query | |
| Prevent at write time | POST validates category+value uniqueness across system+org; rejects duplicates on create | |

**User's choice:** Return both
**Notes:** Simple union query; deactivation via PATCH is_active=false is the replacement mechanism

---

## RefSelect UX

| Option | Description | Selected |
|--------|-------------|----------|
| Simple Select | shadcn/ui Select; good for 5-15 items; fast to implement; consistent with existing forms | ✓ |
| Combobox | shadcn/ui Combobox with type-to-filter search; better for large growing categories | |
| Simple now, upgrade later | Ship Select for Phase 2; swap to Combobox in Phase 6 without touching callers | |

**User's choice:** Simple Select
**Notes:** Component API: `<RefSelect category="sector" value={value} onChange={onChange} />`

---

## Claude's Discretion

- Exact sub-sector seed values (Claude chooses a PE-appropriate list)
- Migration file structure (explicit `op.create_table` DDL + `op.bulk_insert`)
- `position` default for seeded values
- `value` field format (lowercase snake_case slugs)
