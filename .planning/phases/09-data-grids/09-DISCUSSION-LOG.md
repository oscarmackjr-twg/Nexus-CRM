# Phase 9: Data Grids - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-06
**Phase:** 09-data-grids
**Areas discussed:** Sort indicators, Row action buttons, Columns per grid, Deals status filter

---

## Sort Indicators

| Option | Description | Selected |
|--------|-------------|----------|
| Visual only | Static up/down chevron icons on all headers — no click behavior | ✓ |
| Functional | Clicking a header sorts that column — arrow flips asc/desc | |
| Functional on key columns only | Sort works on most useful columns only | |

**User's choice:** Visual only
**Notes:** Keeps scope tight. Pure cosmetic to match Salesforce density look.

---

## Row Action Buttons

| Option | Description | Selected |
|--------|-------------|----------|
| View only | Single 'View' button on hover, navigates to detail page | ✓ |
| View + Edit | Both 'View' and 'Edit' buttons on hover | |
| No buttons — full row clickable | Click anywhere on row navigates to detail | |

**User's choice:** View only
**Notes:** Name cell already links to detail; "View" is a consistent secondary affordance.

---

## Columns Per Grid

| Option | Description | Selected |
|--------|-------------|----------|
| Looks good — use as-is | Contacts: NAME/COMPANY/TITLE/STAGE/EMAIL/SCORE/OWNER/UPDATED. Companies: NAME/TYPE/TIER/SECTOR/INDUSTRY/CONTACTS/DEALS/OWNER. Deals: DEAL/COMPANY/STAGE/VALUE/STATUS/CLOSE DATE/OWNER/DAYS. | ✓ |
| Adjust Contacts columns | Keep Companies and Deals, change Contacts grid | |
| Adjust Companies columns | Keep Contacts and Deals, change Companies grid | |
| Adjust Deals columns | Keep Contacts and Companies, change Deals grid | |

**User's choice:** Confirmed as-is
**Notes:** All column sets approved without changes.

---

## Deals Status Filter

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, include it | Filter bar: All / Open / Won / Lost, passes ?status= to API | ✓ |
| Defer it | Grid-only for now, filter in a later task | |

**User's choice:** Include it
**Notes:** Useful immediately for deal teams scanning open deals.

---

## Claude's Discretion

- Exact Tailwind classes for sort indicator icon
- Per-page selector resetting to page 1 on change
- Layout/spacing of the Deals status filter tabs

## Deferred Ideas

None — discussion stayed within phase scope.
