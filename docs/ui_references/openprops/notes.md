# Open Props — UI reference notes

**URL:** https://open-props.style · https://unpkg.com/open-props/open-props.min.css
**Tagline:** "CSS variables to help accelerate adaptive and consistent design."
**Domain:** Pure design-token library. Not a framework, not a component system, not a design system. Just a giant collection of named CSS custom properties you can reference.
**Author:** Adam Argyle (Google Chrome team).
**Tech:** 29KB minified CSS file, no JavaScript, no build step. Drop in via `<link>` and use the variables.
**Captured:** 2026-04-14

## What this is (and what it isn't)

Open Props is **raw materials**, not a finished design system. It does not tell you what colors to use for primary actions vs. secondary actions, or what shadow to apply to a card vs. a modal. It gives you 603 named values across 32 prefix groups, and expects you to build your own semantic layer on top.

This is exactly what we're doing with [`exocortex.css`](../exocortex.css) — building our own semantic layer (`--ds-accent-cyan`, `--ds-signal-positive`, etc.) on top of raw values. Open Props is a faster way to populate that semantic layer than extracting tokens one site at a time.

**The mental model:** Open Props is the lumber yard. OpenGridWorks's `--ds-*` system is "here's a house pre-built from this lumber yard." `exocortex.css` is "here's our house, built from the lumber yard with notes on which boards came from where."

## Inventory (32 prefix groups, 603 unique custom properties)

| Group | Count | What it provides |
|---|---|---|
| `--ease-*`     | 81 | Every named easing curve in CSS literature: numbered (1-5), named (sine, quad, quart, quint, cubic, expo, circ), elastic, spring, bounce, step. |
| `--size-*`     | 74 | Comprehensive sizing scale with rem, px, fluid (clamp), content (ch), header (ch), and relative (ch) variants of each size step. |
| `--font-*`     | 56 | 15 named font *stacks* by historical category (industrial, neo-grotesque, didone, humanist, antique, slab, handwritten, etc.) plus weights (1-9), line-heights (00-5), letter-spacings (0-7), sizes (00-8 plus fluid 0-3). |
| `--gradient-*` | 31 | Named gradient presets (mostly aesthetic — sunset, conic, radial). |
| `--radius-*`   | 24 | Numeric scale (1-6), pill, round, conditional, plus blob shapes and "drawn" hand-irregular shapes. |
| `--animation-*`| 23 | Pre-built `animation:` shorthand strings for fade, slide, scale, shake, spin, ping, blink, float, bounce, pulse. Each pairs with a `@keyframes` rule shipped in the same file. |
| **17 color names** | 13 each | `--blue-*`, `--cyan-*`, `--gray-*`, `--green-*`, `--indigo-*`, `--lime-*`, `--orange-*`, `--pink-*`, `--purple-*`, `--red-*`, `--teal-*`, `--violet-*`, `--yellow-*`, plus less common: `--brown-*`, `--camo-*`, `--choco-*`, `--jungle-*`, `--sand-*`, `--stone-*`. Each color has 13 shades from 0 (lightest) to 12 (darkest). |
| `--color-*`    | 16 | OKLCH-based palette generator. Configure `--palette-hue` and `--palette-chroma`, get a coherent 16-step palette out. Programmatic theming. |
| `--shadow-*`   | 15 | Outer shadow scale (1-6) + inner shadow library (`--inner-shadow-*`) + auto-adapting `--shadow-color` and `--shadow-strength` for light/dark modes. |
| `--noise-*`    | 10 | SVG-encoded fractal noise filters (5 frequencies) + 5 noise-filter brightness/contrast adjustments. Apply as background-image for subtle texture. |
| `--ratio-*`    | 6  | Aspect ratios: square, landscape, portrait, widescreen, ultrawide, golden. |
| `--layer-*`    | 6  | Z-index scale: 1-5 plus `--layer-important: 2147483647`. |
| `--border-*`   | 5  | Border-size scale (1px to 25px). |
| `--palette-*`  | 3  | Palette generator config (hue rotate, base hue, base chroma). |

## What ports to Exocortex

I selected the most useful groups and vendored them into [`tokens.css`](tokens.css) under an `--op-*` prefix. The rest is documented but not extracted — the source is 29KB minified and most of it is decorative material we don't need.

**Vendored:**
1. **A curated selection of easing curves** (12 of 81). The `--op-ease-1` through `--op-ease-5` numbered scale plus the named ones (sine, quart, expo, circ) plus the personality curves (spring, elastic, bounce, step). This complements the OpenGridWorks easing curves we already have — Open Props gives us the personality variants we don't.
2. **The full animation preset library** (23 prebuilt `animation:` strings + their keyframes). `--op-animation-shake-x` is exactly what we want for "this prediction failed, draw your eye to it." `--op-animation-pulse` for "running cycle in progress." `--op-animation-slide-in-up` for content reveals.
3. **Z-index layer scale** — replaces ad-hoc z-indices in our panel. Currently we have z-indices like `1000` for tooltips, `999` for the legend hint; the layer scale gives us `--op-layer-1..5` plus `--op-layer-important` for true emergencies.
4. **Aspect ratios** — `--op-ratio-square`, `--op-ratio-widescreen`, `--op-ratio-golden`. Useful when we add chart containers in the future.
5. **One noise texture** (`--op-noise-2`) — the SVG noise filter, applied as a background-image with low opacity, replaces the simple radial gradient body backdrop with subtle texture. This is a small but distinctive aesthetic upgrade.

**Not vendored (but available in source):**

- **Color palettes (17 × 13 shades).** These overlap with what we already get from OpenGridWorks's signal/accent palette. Adding 221 color variables for choices we don't need would just clutter the namespace.
- **Size/font/radius scales.** We already have these from OpenGridWorks via `--ds-text-*`, `--ds-radius-*`, etc. Open Props's are more comprehensive but we don't need that comprehensiveness — we need a curated subset.
- **31 gradient presets.** Aesthetic-specific. None of them match our cyan/violet palette and most are decorative (sunset gradients, conic rainbows). We invented our own subtle radial gradient backdrop and that's enough.
- **OKLCH `--color-*` palette generator.** Powerful but overkill — we know exactly which colors we want, we don't need a generator.
- **Inner shadow library.** We use outer shadows + glow. Inner shadows are for inset effects (pressed buttons, sunken inputs) which aren't part of our visual language.
- **The 56 font tokens.** We use IBM Plex Mono with a system fallback — any of Open Props's 15 named font stacks would be valid alternatives but switching now would be churn.

## What does NOT port

- **Open Props's philosophy of "pick from a comprehensive scale at the call site"** — this works when you have many people building UI in parallel and you want consistency through enforced choice. We're a single builder iterating on a focused panel; we benefit more from semantic naming (`--ds-accent-cyan`) than from "pick the right size from the 74 available."
- **The OKLCH palette generator approach.** Conceptually elegant but adds runtime computation and conceptual overhead. Direct hex values are fine for our scale.
- **The `:where()` selector specificity trick.** Open Props wraps everything in `:where(html)` to make all variables zero-specificity (overridable by anything). This matters if you're shipping a shared library; we control our own stylesheet, so we can use plain `:root`.

## Cross-pollination notes

**With OpenGridWorks:** Open Props's `--ease-*` (numbered scale) and OpenGridWorks's `--ds-ease-out` (`cubic-bezier(.16, 1, .3, 1)`) point at the same idea — aggressive ease-out for fast-feeling motion. OpenGridWorks's curve is closest to Open Props's `--ease-out-3` or `--ease-out-4`. Either is fine; we keep OpenGridWorks's because it's already in our stylesheet.

**With TuiCss:** TuiCss's "no animations" philosophy is the opposite of Open Props's "23 named animations available." Both are correct in their context. Open Props provides the *option* to animate; TuiCss provides the *option* to not. Use OpenGridWorks-style fast transitions for hover/active feedback, Open Props animations for content reveals, and TuiCss-style instantaneous state for truth-bearing indicators.

## Caveats

- Open Props gets new tokens added periodically. The 603 count is from 2026-04-14. If we re-extract later we may find new groups.
- The minified file uses `:where(html)` for zero specificity. When we vendor portions of it into our own stylesheet, we use `:root` instead. Equivalent for our purposes since we don't have multiple competing stylesheets.
- Some of the easing curves use the new `linear()` syntax (for spring/bounce). Browser support is good in 2025+ but worth knowing if we ever target older browsers.
- The SVG noise textures are inlined as data URLs. They're technically background-images, not filter primitives. To use them, you set `background-image: var(--op-noise-2)` on an element.

## Extraction methodology used

Open Props was a special case. The 9-grep methodology *would* work, but the file is fundamentally already grep-friendly (one custom property per assignment, predictable prefix structure). I went straight to:

1. Count all custom properties: `re.findall(r'--[a-z][a-z0-9-]*(?=:)', css)` — 603 unique
2. Group by prefix: `Counter` of first segment after `--` — 32 groups
3. Read the values for each group of interest manually

**Total extraction time:** ~10 minutes. Faster than TuiCss (12 min) and OpenGridWorks (~30 min) because Open Props is *designed* to be parsed.

The lesson for the methodology: when a reference is a token library rather than an application, **skip the 9 greps and go straight to the prefix counter.** A token library's value is in its structure, not its component CSS.
