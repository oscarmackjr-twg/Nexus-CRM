# Phase 7: Brand Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 07-brand-foundation
**Areas discussed:** Font source, CSS variables, Indigo/purple sweep, Dark mode block

---

## Area 1: Gotham Font Sourcing

**Question:** Where does Gotham come from? It's a licensed font with no free CDN option.

**Options presented:**
- Self-host .woff2 files — drop font files into frontend/src/assets/fonts/, requires licensed files
- Montserrat (Google Fonts) — free, visually close to Gotham, geometric sans-serif
- Skip font this phase — placeholder comment, defer until files available

**Selected:** Montserrat (Google Fonts)

---

## Area 2: CSS Variable Migration Strategy

**Question:** How should the new --color-brand vars coexist with the existing shadcn/ui --primary system?

**Options presented:**
- Add new + remap primary (Recommended) — add --color-brand vars AND update --primary/--ring to navy in same phase
- New vars only, keep --primary — add --color-brand vars but leave --primary as indigo
- Replace old vars entirely — remove --primary/--ring/--secondary, rename to --color-brand pattern throughout

**Selected:** Add new + remap primary (Recommended)

---

## Area 3: Indigo/Purple Sweep Scope

**Question:** Should Phase 7 hunt down all hardcoded indigo-*/purple-*/violet-* Tailwind classes in JSX, or just fix the CSS root?

**Options presented:**
- Full sweep this phase (Recommended) — grep all JSX for indigo/purple/violet, replace with primary equivalents
- CSS root only — update styles.css and tailwind.config.js only
- Grep & report, fix only obvious ones — audit and fix clear cases, log rest as known debt

**Selected:** Full sweep this phase (Recommended)

---

## Area 4: Dark Mode Variable Block

**Question:** What should happen to the .dark CSS variable block?

**Options presented:**
- Keep it, update to navy too — maintain .dark block with matching navy values, future-proof
- Leave .dark untouched — don't modify .dark vars this phase
- Remove .dark block — delete entirely, signals light-only decision

**Selected:** Keep it, update to navy too
