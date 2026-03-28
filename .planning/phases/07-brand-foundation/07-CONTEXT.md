# Phase 7: Brand Foundation - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish the TWG brand baseline globally: `#1a3868` navy replaces indigo/purple as the primary color, Montserrat (Google Fonts) is loaded as the body font, and CSS variables are consolidated per the POC pattern. This phase is a prerequisite for all other v1.1 UI phases — no component-level UI work, just the global styling foundation.

</domain>

<decisions>
## Implementation Decisions

### Font
- **D-01:** Use Montserrat from Google Fonts as the Gotham stand-in. Load via `@import` in `styles.css` or `<link>` in `index.html`. Set `font-family: 'Montserrat', ui-sans-serif, system-ui, sans-serif` on `body`. Licensed Gotham files are not available; Montserrat is the approved substitute.

### CSS Variables
- **D-02:** Add the new POC-pattern vars (`--color-brand`, `--color-brand-hover`, `--color-page-bg`, `--color-content-bg`, `--color-text`) AND simultaneously remap `--primary` and `--ring` to the navy value. Both systems aligned in one pass — downstream phases can use `text-primary` or `--color-brand` interchangeably.
- **D-03:** Navy value is `#1a3868`. HSL equivalent ≈ `214 62% 25%` — use this in HSL CSS variable declarations.
- **D-04:** `--color-brand-hover` should be a slightly lighter/brighter navy — approximately `#1e4080` or `hsl(214, 58%, 30%)`.
- **D-05:** `--color-page-bg` = white (`#ffffff`), `--color-content-bg` = white (`#ffffff`), `--color-text` = dark near-black (`hsl(222, 47%, 11%)` matching existing `--foreground`).

### Dark Mode Variables
- **D-06:** Keep the `.dark` CSS variable block and update it with matching navy values. Future-proof for when dark mode support returns. Dark mode `--primary` and `--color-brand` should also be navy (same hex, may adjust lightness for dark backgrounds if needed by researcher).

### Indigo/Purple Sweep
- **D-07:** Phase 7 performs a **full grep-and-replace** of all hardcoded `indigo-*`, `purple-*`, and `violet-*` Tailwind class names across all JSX files. Replace with `primary` equivalents (e.g., `bg-indigo-600` → `bg-primary`, `text-indigo-600` → `text-primary`, `border-indigo-600` → `border-primary`). Goal: clean baseline so phases 8-12 don't encounter stale indigo classes.
- **D-08:** The `surface-grid` utility in `styles.css` uses `rgba(99, 102, 241, ...)` (indigo raw hex) — update those rgba values to the navy equivalent during sweep.

### Claude's Discretion
- Exact HSL rounding for navy variants — planner can compute precisely.
- Whether to use `@import url(...)` vs `<link>` tag for Montserrat — either is fine; `<link>` in `index.html` preferred for performance.
- Order of Tailwind color class replacements — follow grep output, no preference on order.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope
- `.planning/ROADMAP.md` — Phase 7 goal, success criteria (BRAND-01, BRAND-02, BRAND-03)
- `.planning/REQUIREMENTS.md` — BRAND-01, BRAND-02, BRAND-03 requirement definitions

### Existing styling files
- `frontend/src/styles.css` — current CSS variable declarations (HSL format, shadcn/ui pattern); font-family on body
- `frontend/tailwind.config.js` — color mappings via `hsl(var(--...))`, darkMode: 'class'
- `frontend/index.html` — where to add Google Fonts `<link>` tag

### Codebase conventions
- `.planning/codebase/CONVENTIONS.md` — naming conventions and patterns
- `.planning/codebase/STRUCTURE.md` — frontend directory layout

No external ADRs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/styles.css` — 67-line file, clean structure: @tailwind directives, `@layer base` with `:root` + `.dark` blocks, `@layer utilities`. Easy to extend.
- `frontend/tailwind.config.js` — all colors already mapped to CSS variables via `hsl(var(--...))`. Updating CSS vars alone cascades to all Tailwind utility classes automatically.

### Established Patterns
- CSS variables use HSL triplet format (no `hsl()` wrapper in the var value, wrapper is in tailwind config): `--primary: 239 84% 67%`
- Font is declared on `body` in `@layer base` — Montserrat declaration goes in the same place, replacing `"IBM Plex Sans"`
- Both `:root` (light) and `.dark` class blocks exist — update both

### Integration Points
- All shadcn/ui components use `text-primary`, `bg-primary`, `ring-primary` — they will automatically pick up the navy once `--primary` is updated in CSS vars
- `tailwind.config.js` has no hardcoded `indigo`/`purple` color entries — all component-level classes are in JSX files
- `surface-grid` utility uses inline rgba values referencing old indigo hex — needs manual update

</code_context>

<specifics>
## Specific Ideas

- Montserrat as Gotham stand-in is a deliberate decision, not a compromise — no TODO comment needed.
- Google Fonts `<link>` preferred over `@import` for performance (preconnect + stylesheet link in `index.html`).
- The full indigo/purple sweep is part of this phase's definition of done — it is not optional cleanup.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 07-brand-foundation*
*Context gathered: 2026-03-28*
