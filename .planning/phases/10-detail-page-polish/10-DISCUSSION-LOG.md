# Phase 10: Detail Page Polish - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-06
**Phase:** 10-detail-page-polish
**Areas discussed:** FieldRow component, Tab bar navy underline, Empty value definition, Card header border

---

## FieldRow Component

| Option | Description | Selected |
|--------|-------------|----------|
| Shared `<FieldRow />` component | Create FieldRow.jsx with label+value props, handles em-dash, used across all 3 pages. Consistent with DataGrid/Pagination pattern from Phase 9. | ✓ |
| Inline Tailwind on each page | Apply grid classes directly in each page. No new component but many more lines changed. | |
| You decide | Claude picks approach. | |

**User's choice:** Shared `<FieldRow />` component

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed 140px label + 1fr value | `grid-cols-[140px_1fr]` — wide enough for long PE field labels. | ✓ |
| Proportional 1fr 2fr | `grid-cols-[1fr_2fr]` — responsive but labels can feel cramped. | |
| You decide | Claude picks based on longest labels. | |

**User's choice:** Fixed 140px label + 1fr value

---

## Tab Bar Navy Underline

| Option | Description | Selected |
|--------|-------------|----------|
| Bottom-border underline on active tab | Remove TabsList background. Active tab: `border-b-2 border-[#1a3868] text-[#1a3868]`. Matches Phase 8 sidebar active pattern. | ✓ |
| Keep shadcn pill style, swap to navy | Keep gray container, change active pill to navy bg. Diverges from border-indicator pattern. | |
| You decide | Claude chooses. | |

**User's choice:** Bottom-border underline on active tab

| Option | Description | Selected |
|--------|-------------|----------|
| CSS override in styles.css | `.detail-tabs` class on TabsList. One change covers all 3 pages. | ✓ |
| className prop on each TabsList/TabsTrigger | Explicit per-page but 15+ lines across 3 files. | |
| Patch shadcn/ui tabs component directly | Would affect ALL tabs app-wide. | |

**User's choice:** CSS override in styles.css

---

## Empty Value Definition

| Option | Description | Selected |
|--------|-------------|----------|
| null, undefined, and empty string only | `value ?? '—'` + trim check. Zero shows as '0'. Empty arrays show as '—'. | ✓ |
| Falsy values (null, undefined, '', 0, false) | Risk: EBITDA of 0 shows as em dash — misleading for financial data. | |
| You decide | Claude defines per field type. | |

**User's choice:** null, undefined, and empty string only

---

## Card Header Border

| Option | Description | Selected |
|--------|-------------|----------|
| Add `border-b` to CardHeader className on each card | Append `border-b border-gray-200 pb-3` to each CardHeader. ~15 occurrences. Explicit and verifiable. | ✓ |
| Global CSS override for all CardHeaders | Affects ALL cards app-wide including admin pages. | |
| Wrapper utility class `.card-header-ruled` | Middle ground — still requires touching each CardHeader. | |

**User's choice:** Add `border-b` to CardHeader className on each card

---

## Claude's Discretion

- Exact CSS selector syntax for `.detail-tabs` shadcn data-attribute overrides
- Whether FieldRow renders value as `<span>` or `<p>`
- Exact Tailwind class for label color (`text-muted-foreground` vs `text-gray-500`)

## Deferred Ideas

None — discussion stayed within phase scope.
