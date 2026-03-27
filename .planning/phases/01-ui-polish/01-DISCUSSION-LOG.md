# Phase 1: UI Polish - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 01 — UI Polish
**Areas discussed:** Theme target, Design reference

---

## Theme target

| Option | Description | Selected |
|--------|-------------|----------|
| Dark mode only | Polish everything in dark mode. PE/finance aesthetic fits dark UI — login page already sets that tone. | ✓ |
| Both modes | Ensure all screens look good in dark and light. More work, but the toggle is already built in. | |
| Light mode only | Switch to a light-first design — more traditional enterprise/finance look. | |

**User's choice:** Dark mode only

---

| Option | Description | Selected |
|--------|-------------|----------|
| Lock to dark, remove toggle | Cleaner — one target state, no maintenance of two themes. | ✓ |
| Keep the toggle, polish dark only | Toggle stays for future light mode work, but this phase only polishes dark. | |
| You decide | Claude picks the appropriate approach. | |

**User's choice:** Lock to dark, remove toggle

---

## Design reference

**Reference site:** qa.oscarmackjr.com

| Option | Description | Selected |
|--------|-------------|----------|
| Dark background, similar to current login | Same dark/slate tone as the reference | ✓ |
| Lighter / neutral background | Reference uses a lighter palette | |

**User's choice:** Dark background

---

| Option | Description | Selected |
|--------|-------------|----------|
| TWG Global logo + Nexus CRM | Firm brand prominently, app name below | ✓ |
| Nexus CRM only | App-first, no firm logo | |
| TWG logo only | Minimal — logo does the talking | |

**User's choice:** TWG Global logo + Nexus CRM
**Notes:** User specified "TWG Global" (not TWG Asia) as the branding.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — show backend status | Small indicator showing API connectivity | ✓ |
| No — skip it | Keep login clean, no status indicator | |

**User's choice:** Yes — show backend status ("Backend: Connected")

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — show env banner when not production | Top banner in staging/QA, hidden in production | ✓ |
| No — no banner needed | Same page in all environments | |

**User's choice:** Yes — show env banner when not production

---

## Claude's Discretion

- Exact logo asset handling (use text placeholder if no file found)
- Backend health endpoint selection (check for existing, create if missing)
- Typography scale specifics (follow shadcn/ui dark mode defaults)

## Deferred Ideas

None.
