# Phase 7: Brand Foundation - Research

**Researched:** 2026-03-28
**Domain:** CSS variables, Tailwind theming, Google Fonts, Tailwind class sweep
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use Montserrat from Google Fonts as the Gotham stand-in. Load via `<link>` in `index.html`. Set `font-family: 'Montserrat', ui-sans-serif, system-ui, sans-serif` on `body`. Licensed Gotham files are not available; Montserrat is the approved substitute.
- **D-02:** Add the new POC-pattern vars (`--color-brand`, `--color-brand-hover`, `--color-page-bg`, `--color-content-bg`, `--color-text`) AND simultaneously remap `--primary` and `--ring` to the navy value. Both systems aligned in one pass — downstream phases can use `text-primary` or `--color-brand` interchangeably.
- **D-03:** Navy value is `#1a3868`. HSL equivalent = `217 60% 25%` (verified by calculation).
- **D-04:** `--color-brand-hover` = `#1e4080` / `hsl(219, 62%, 31%)` (verified by calculation).
- **D-05:** `--color-page-bg` = white (`#ffffff`), `--color-content-bg` = white (`#ffffff`), `--color-text` = dark near-black (`hsl(222, 47%, 11%)` matching existing `--foreground`).
- **D-06:** Keep the `.dark` CSS variable block and update it with matching navy values. Future-proof for when dark mode support returns. Dark mode `--primary` and `--color-brand` should also be navy.
- **D-07:** Phase 7 performs a full grep-and-replace of all hardcoded `indigo-*`, `purple-*`, and `violet-*` Tailwind class names across all JSX files. Replace with `primary` equivalents. Goal: clean baseline.
- **D-08:** The `surface-grid` utility in `styles.css` uses `rgba(99, 102, 241, ...)` (indigo raw hex) — update to navy equivalent `rgba(26, 56, 104, ...)`.

### Claude's Discretion

- Exact HSL rounding for navy variants — planner can compute precisely (computed: `217 60% 25%` for brand, `219 62% 31%` for hover).
- Whether to use `@import url(...)` vs `<link>` tag for Montserrat — `<link>` in `index.html` preferred for performance (locked by D-01).
- Order of Tailwind color class replacements — follow grep output, no preference on order.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BRAND-01 | TWG `#1a3868` navy replaces indigo/purple as the primary brand color throughout (CSS variables and Tailwind config updated) | CSS var remapping in `styles.css` cascades automatically to all Tailwind utility classes via `hsl(var(--primary))` in `tailwind.config.js`; indigo sweep covers remaining hardcoded class names |
| BRAND-02 | Gotham font applied as body font with system-ui fallback via CSS `@font-face` or font-family declaration | Montserrat via Google Fonts `<link>` in `index.html` + `font-family` override on `body` in `@layer base`; replaces current `"IBM Plex Sans"` declaration on line 52 of `styles.css` |
| BRAND-03 | CSS variables consolidated to match POC pattern: `--color-brand`, `--color-brand-hover`, `--color-page-bg`, `--color-content-bg`, `--color-text` | New vars added to `:root` and `.dark` blocks in `styles.css`; no tailwind.config.js changes needed as downstream phases can use `var(--color-brand)` directly in CSS |
</phase_requirements>

---

## Summary

Phase 7 is a pure front-end styling operation with three atomic changes: (1) remap CSS custom properties in `styles.css`, (2) inject the Google Fonts `<link>` tag in `index.html` and update the `font-family` declaration on `body`, and (3) sweep all JSX files for hardcoded indigo/purple/violet Tailwind class names and replace with their `primary`-token equivalents.

The project's existing architecture makes this straightforward: `tailwind.config.js` already routes every semantic color (primary, ring, etc.) through `hsl(var(--...))` CSS variables, so a single edit to `--primary` and `--ring` in `styles.css` cascades to every shadcn/ui component automatically. No Tailwind config file changes are required for the color swap.

The indigo sweep search turned up zero matches in JSX files as of the research scan — the `surface-grid` utility in `styles.css` is the only confirmed hardcoded indigo reference (`rgba(99, 102, 241, ...)`) that must be updated manually. The planner should include the sweep as a verification step even if no JSX matches exist, since JSX files are the most likely future regression point.

**Primary recommendation:** Edit `styles.css` (CSS vars + font-family + surface-grid rgba) and `index.html` (Google Fonts link) — two files fully cover BRAND-01, BRAND-02, and BRAND-03.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Tailwind CSS | Already installed (v3.x per package.json) | Utility classes — all color tokens routed through CSS vars | Project's established styling system |
| Google Fonts (Montserrat) | CDN / no versioning | Gotham-substitute body font | Approved substitute per D-01; no license cost |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shadcn/ui CSS variable pattern | N/A (CSS convention) | HSL triplet vars without `hsl()` wrapper in the var value | Already in use — extend, do not change format |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `<link>` in index.html | `@import url(...)` in styles.css | `@import` in CSS blocks rendering until font loads; `<link>` with preconnect is faster |
| HSL triplet format `217 60% 25%` | Full hex `#1a3868` directly in vars | Tailwind's `hsl(var(--...))` pattern requires the triplet format — changing format would break all existing Tailwind color utilities |

**Installation:** No new packages required. Google Fonts is CDN-loaded.

---

## Architecture Patterns

### Recommended Project Structure

No directory changes needed. All edits are in:

```
frontend/
├── index.html                   # Add Google Fonts <link> tags
└── src/
    └── styles.css               # CSS var remapping + font-family + surface-grid rgba
```

No JSX files require edits (indigo sweep confirmed zero matches — but sweep task is still required as a verification gate).

### Pattern 1: shadcn/ui CSS Variable Cascade

**What:** All color utilities in Tailwind are wired to CSS custom properties. Changing the property value changes every component that uses the utility class.

**When to use:** Any time a global color token needs changing — edit the CSS var, not individual class names.

**Example:**
```css
/* styles.css — existing pattern, verified from file */
:root {
  --primary: 239 84% 67%;  /* current indigo */
  --ring:    239 84% 67%;
}

/* tailwind.config.js — existing wiring */
primary: 'hsl(var(--primary))',
ring:    'hsl(var(--ring))',
```

After updating `--primary: 217 60% 25%`, every `bg-primary`, `text-primary`, `ring-primary`, `border-primary` becomes navy automatically.

### Pattern 2: Google Fonts Preconnect + Stylesheet Link

**What:** Two `<link>` tags in `<head>` — one preconnect to `fonts.googleapis.com`, one preconnect to `fonts.gstatic.com` (crossorigin), one stylesheet link.

**When to use:** Loading any Google Font via CDN for production-quality performance.

**Example:**
```html
<!-- index.html <head> — add before </head> -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Weights 400/500/600/700 cover all text weights used in the app (normal, medium, semibold, bold). `display=swap` prevents invisible text during font load.

### Pattern 3: POC-Pattern CSS Variables Alongside Existing Variables

**What:** Additive addition of new semantic vars (`--color-brand` etc.) that mirror the remapped `--primary` value. Both sets live in `:root` simultaneously — downstream phases can use either.

**When to use:** When bridging old naming conventions (shadcn's `--primary`) with a new project-specific naming convention.

**Example:**
```css
:root {
  /* --- Remapped existing tokens --- */
  --primary: 217 60% 25%;
  --ring:    217 60% 25%;

  /* --- New POC-pattern tokens (D-02, D-03, D-04, D-05) --- */
  --color-brand:      #1a3868;
  --color-brand-hover: #1e4080;
  --color-page-bg:    #ffffff;
  --color-content-bg: #ffffff;
  --color-text:       hsl(222, 47%, 11%);
}
```

Note: `--color-brand` and friends do NOT need to use the HSL-triplet format (they aren't consumed by Tailwind config) — plain hex or full `hsl()` syntax is fine here.

### Pattern 4: surface-grid RGBA Update

**What:** The `.surface-grid` utility in `@layer utilities` uses raw RGBA values referencing the old indigo hex. Must be updated manually since it is not a CSS variable.

**Current value (line 63, styles.css):**
```css
rgba(99, 102, 241, 0.06)   /* indigo */
```

**Replacement:**
```css
rgba(26, 56, 104, 0.06)    /* navy #1a3868 = rgb(26, 56, 104) */
```

The second gradient line (`rgba(6, 182, 212, 0.05)` — cyan) is unrelated to the brand color and should be left unchanged unless the planner decides to update it.

### Anti-Patterns to Avoid

- **Editing tailwind.config.js colors:** No changes to `tailwind.config.js` are needed — the existing `hsl(var(--primary))` wiring already handles the cascade. Editing the config file risks breaking the variable indirection.
- **Using the `hsl()` wrapper inside the CSS var value:** The project's established pattern is `--primary: 217 60% 25%` (triplet only, no `hsl()` wrapper) — the wrapper lives in `tailwind.config.js`. Breaking this convention would cause Tailwind's color utilities to emit malformed CSS.
- **Adding `@import url(...)` to styles.css instead of `<link>` in index.html:** `@import` in CSS blocks rendering; the `<link>` preconnect pattern is faster per D-01.
- **Adding Montserrat to a `@font-face` block:** There is no font file to self-host; Google Fonts CDN is the source. `@font-face` is not needed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Font loading | Self-hosted @font-face setup | Google Fonts CDN `<link>` | No font files available; CDN handles subsetting, caching, format negotiation |
| Color cascade to all components | Per-component color overrides | Single CSS var change in `:root` | tailwind.config.js already routes all color utilities through CSS vars |
| Indigo class discovery | Manual file-by-file review | `grep -r "indigo\|purple\|violet" frontend/src/` | Automated grep catches all occurrences in one pass |

**Key insight:** The shadcn/ui CSS variable architecture makes global retheming a two-line change in `styles.css`. Any approach that touches individual component files is wasted effort.

---

## Common Pitfalls

### Pitfall 1: Using `hsl()` Wrapper in CSS Variable Value

**What goes wrong:** Developer writes `--primary: hsl(217, 60%, 25%)` instead of `--primary: 217 60% 25%`.
**Why it happens:** The full `hsl()` syntax looks more correct to someone unfamiliar with the shadcn/ui pattern.
**How to avoid:** Match the exact format of existing vars: bare triplet without wrapper, without commas — `217 60% 25%`.
**Warning signs:** Tailwind color utilities resolve to `hsl(hsl(...))` and render transparent/black.

### Pitfall 2: Forgetting the `.dark` Block

**What goes wrong:** `:root` block is updated but `.dark` block still has `--primary: 239 84% 67%` (old indigo). Dark mode (if ever activated) shows wrong color.
**Why it happens:** Developer edits only the `:root` block since dark mode is currently disabled.
**How to avoid:** Update both `:root` and `.dark` in the same edit per D-06.
**Warning signs:** Toggling `.dark` class on `<html>` shows indigo instead of navy.

### Pitfall 3: Missing the `crossorigin` Attribute on gstatic Preconnect

**What goes wrong:** Google Fonts `<link>` loads but the preconnect for `fonts.gstatic.com` is missing `crossorigin`, so font files aren't actually preloaded. No error, just slower first load.
**How to avoid:** Use the canonical three-tag Google Fonts pattern (preconnect googleapis, preconnect gstatic with crossorigin, stylesheet link).

### Pitfall 4: surface-grid Not Updated

**What goes wrong:** All buttons/rings turn navy, but the background grid on certain pages (e.g. dashboard) still glows indigo.
**Why it happens:** It's not a Tailwind class — it's an inline rgba value in `@layer utilities` that doesn't get caught by Tailwind's cascade.
**How to avoid:** Explicitly update `rgba(99, 102, 241, 0.06)` → `rgba(26, 56, 104, 0.06)` in the surface-grid rule.

### Pitfall 5: Assuming JSX Sweep Is Needed

**What goes wrong:** Planner allocates a full sweep task, wastes time, finds nothing.
**Reality:** As of the research scan, `grep -r "indigo|purple|violet" frontend/src/` returns zero matches. The sweep task should be a verification step (confirm zero matches) rather than an active replacement task. Include it as a required check so future regressions are caught.

---

## Code Examples

Verified patterns from existing codebase inspection:

### Complete styles.css After Change

```css
/* Source: verified from frontend/src/styles.css current state */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 220 33% 98%;
    --foreground: 222 47% 11%;
    --card: 0 0% 100%;
    --card-foreground: 222 47% 11%;
    --border: 214 32% 91%;
    --input: 214 32% 91%;
    --ring:    217 60% 25%;   /* was: 239 84% 67% */
    --primary: 217 60% 25%;   /* was: 239 84% 67% */
    --secondary: 262 83% 67%;
    --accent: 188 86% 43%;
    --success: 160 84% 39%;
    --warning: 38 92% 50%;
    --danger: 0 84% 60%;
    --muted: 220 20% 96%;
    --muted-foreground: 220 9% 46%;

    /* POC-pattern vars (BRAND-03) */
    --color-brand:       #1a3868;
    --color-brand-hover: #1e4080;
    --color-page-bg:     #ffffff;
    --color-content-bg:  #ffffff;
    --color-text:        hsl(222, 47%, 11%);
  }

  .dark {
    --background: 222 47% 11%;
    --foreground: 213 31% 91%;
    --card: 222 39% 16%;
    --card-foreground: 213 31% 91%;
    --border: 217 33% 22%;
    --input: 217 33% 22%;
    --ring:    217 60% 25%;   /* was: 239 84% 67% */
    --primary: 217 60% 25%;   /* was: 239 84% 67% */
    --secondary: 262 83% 67%;
    --accent: 188 86% 43%;
    --success: 160 84% 39%;
    --warning: 38 92% 50%;
    --danger: 0 84% 60%;
    --muted: 222 31% 18%;
    --muted-foreground: 215 20% 65%;

    /* POC-pattern vars (BRAND-03) */
    --color-brand:       #1a3868;
    --color-brand-hover: #1e4080;
    --color-page-bg:     #ffffff;
    --color-content-bg:  #ffffff;
    --color-text:        hsl(222, 47%, 11%);
  }

  * {
    @apply border-border;
  }

  html {
    @apply bg-background text-foreground;
  }

  body {
    @apply min-h-screen bg-background text-foreground antialiased;
    font-family: 'Montserrat', ui-sans-serif, system-ui, sans-serif;
    /* was: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif */
  }

  #root {
    @apply min-h-screen;
  }
}

@layer utilities {
  .surface-grid {
    background-image:
      linear-gradient(to right, rgba(26, 56, 104, 0.06) 1px, transparent 1px),
      /* was: rgba(99, 102, 241, 0.06) — indigo */
      linear-gradient(to bottom, rgba(6, 182, 212, 0.05) 1px, transparent 1px);
      /* cyan line unchanged */
    background-size: 36px 36px;
  }
}
```

### Google Fonts Link Block for index.html

```html
<!-- Source: Google Fonts canonical pattern -->
<!-- Add inside <head>, before </head> -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcode indigo hex in component classes | CSS variable system via tailwind.config.js | v1.0 (already in place) | Single-point retheming — this phase exploits it |
| `@import` for fonts | `<link>` preconnect + stylesheet | Industry standard ~2019+ | Faster font load, no render-blocking |

**Deprecated/outdated:**
- `"IBM Plex Sans"` font declaration on `body`: replaced by Montserrat per D-01. The IBM Plex Sans font is likely not loaded anyway (no `<link>` tag in index.html for it) — system-ui is currently the effective fallback.

---

## Open Questions

1. **Should `--color-brand` in `.dark` be lightness-adjusted for dark backgrounds?**
   - What we know: D-06 says "same hex, may adjust lightness for dark backgrounds if needed by researcher"
   - Finding: Dark mode is currently disabled and will not be activated in v1.1. Using identical navy in `.dark` is safe — any dark-mode adjustment can happen when dark mode is re-enabled in a future milestone.
   - Recommendation: Use the same `#1a3868` / `217 60% 25%` values in `.dark` block for both `--primary` and `--color-brand`. No lightness adjustment needed now.

2. **Are there JSX files outside `frontend/src/` with hardcoded indigo/purple classes?**
   - What we know: Grep across `frontend/src/` returned zero matches.
   - What's unclear: `frontend/dist/` (build output) also exists but is not source.
   - Recommendation: Sweep `frontend/src/` only; ignore `dist/`. Build artifacts are regenerated.

---

## Environment Availability

Step 2.6: SKIPPED (no external dependencies identified — phase is purely file edits to `styles.css` and `index.html`; Google Fonts is a CDN resource loaded at browser runtime, not a build-time dependency).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Vitest 2.1.8 |
| Config file | `frontend/vite.config.js` (`test` block, `environment: 'jsdom'`, `css: true`) |
| Setup file | `frontend/src/test/setup.js` |
| Quick run command | `cd frontend && npm test -- --run` |
| Full suite command | `cd frontend && npm test` |

Note: `css: true` in vitest config means CSS custom properties ARE processed during tests. This enables snapshot or computed-style assertions on CSS variables.

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BRAND-01 | `--primary` CSS var equals `217 60% 25%` (navy) in :root | unit/smoke | `cd frontend && npm test -- --run src/__tests__/brand.test.jsx` | ❌ Wave 0 |
| BRAND-01 | `--ring` CSS var equals `217 60% 25%` (navy) in :root | unit/smoke | included in brand.test.jsx | ❌ Wave 0 |
| BRAND-02 | `body` font-family includes `'Montserrat'` | unit/smoke | included in brand.test.jsx | ❌ Wave 0 |
| BRAND-03 | `--color-brand` CSS var defined in :root | unit/smoke | included in brand.test.jsx | ❌ Wave 0 |
| BRAND-03 | `--color-brand-hover` CSS var defined in :root | unit/smoke | included in brand.test.jsx | ❌ Wave 0 |
| BRAND-03 | `--color-page-bg` CSS var defined in :root | unit/smoke | included in brand.test.jsx | ❌ Wave 0 |
| BRAND-03 | `--color-content-bg` CSS var defined in :root | unit/smoke | included in brand.test.jsx | ❌ Wave 0 |
| BRAND-03 | `--color-text` CSS var defined in :root | unit/smoke | included in brand.test.jsx | ❌ Wave 0 |

**Alternative — manual smoke test (no Wave 0 file needed):**
Open the running app at `http://localhost:5173`, inspect any primary button, verify computed background-color equals `rgb(26, 56, 104)` and font-family includes Montserrat. This is sufficient for a visual baseline phase.

Given that this phase is purely CSS/HTML with no React component logic and no API behavior, visual verification is the canonical acceptance method. The automated test is a nice-to-have, not a gate.

### Sampling Rate

- **Per task commit:** Visual inspection of button color + font in browser
- **Per wave merge:** `cd frontend && npm test` (existing suite must remain green)
- **Phase gate:** Existing test suite green + visual confirmation before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `frontend/src/__tests__/brand.test.jsx` — CSS variable smoke tests (BRAND-01, BRAND-02, BRAND-03). Optional — visual verification is acceptable as the primary acceptance method for a pure-CSS phase.

If no brand test file is created, wave 0 gap is: "None (visual verification is primary acceptance method for this phase)."

---

## Sources

### Primary (HIGH confidence)

- Direct file inspection — `frontend/src/styles.css` (67 lines, verified current state)
- Direct file inspection — `frontend/tailwind.config.js` (35 lines, verified color wiring)
- Direct file inspection — `frontend/index.html` (13 lines, confirmed no Google Fonts link yet)
- Direct file inspection — `frontend/vite.config.js` (confirmed `css: true` in test block)
- Python calculation — HSL values for `#1a3868` and `#1e4080` computed from hex

### Secondary (MEDIUM confidence)

- Google Fonts canonical `<link>` pattern (three-tag: preconnect googleapis, preconnect gstatic crossorigin, stylesheet) — industry-standard pattern, widely documented
- Montserrat on Google Fonts: `https://fonts.google.com/specimen/Montserrat` — available with weights 400–900

### Tertiary (LOW confidence)

None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — existing files verified, no new packages needed
- Architecture: HIGH — direct file inspection confirms cascade pattern works as described
- Pitfalls: HIGH — HSL format trap verified from actual styles.css format; indigo sweep verified as clean (zero matches)
- Test strategy: MEDIUM — CSS variable assertion in jsdom requires verifying that `css: true` in vitest actually resolves custom properties at runtime (jsdom CSS support is partial)

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable domain — Tailwind CSS variable conventions do not change frequently)
