# OpenGridWorks — UI reference notes

**URL:** https://opengridworks.com/power-plants
**Tagline:** "Electric grid data that sparks joy."
**Domain:** Interactive geospatial data visualization. US electric grid (power plants, transmission lines, substations, data centers).
**Tech:** Next.js SPA with custom Mapbox/MapLibre base. Ships a full `--ds-*` design system in the compiled CSS.
**Captured:** 2026-04-13

## What makes it feel good

The fluidity comes from **four compounding things**, in descending order of impact:

1. **Fast timings with aggressive easing.** 150ms default, 80ms for micro-feedback, `cubic-bezier(.16, 1, .3, 1)` for ease-out (more aggressive than Material — reaches near-final value fast, then smooths to rest). Motion feels intentional but never makes you wait.

2. **Glass panels over the map.** Every control surface uses `backdrop-filter: blur(32px) saturate(150%)` with a 92% alpha dark background. Panels don't occlude the map — they float over it with blur, so the spatial context is always preserved. You never "leave" the map to interact with controls.

3. **Scale-transform feedback on interactions.** Buttons do `transform: scale(1.06)` on hover and `scale(0.95)` on active, combined with the 80ms transform duration. Tactile feedback without any sound, color flash, or ripple.

4. **Full color palettes for state, not opacity shifts.** Hover = cyan. Active = cyan + glow. Success = pale green + pulse. Error = pale red. Each state has its own distinct color instead of "normal with less opacity." Your eye parses the change faster because it's categorically different.

## Information conveyance

- **The map is the primary index.** Everything else (panels, legends, toggles) floats on top of it. Attention never leaves the map.
- **Legend entries ARE filters.** Clicking a fuel type in the sidebar toggles that layer — no separate filter UI. Controls fused with data.
- **Count-first row format.** `Solar · 91 · 482 MW` in a single tight row. Numbers first, label second. High data density without crowding because typography and spacing are disciplined.
- **Summary stat at the top.** "177 plants / 30.2 GW" under the title. One-glance headline number.
- **URL state captures everything.** `?layers=tx,datacenters,hpoints,rowTx,rowSubs&panel=closed` — every toggle, zoom, panel state is URL-encoded. Reload preserves view. Sharing a link shares an exact view.
- **Hover reveals tooltip via `data-label` + CSS.** No JavaScript tooltip library — just `::before { content: attr(data-label) }`. Every interactive element has one.

## What ports cleanly to Exocortex

- **The full `--ds-*` token set** (timings, easings, radii, shadows, surfaces, text scale, accents, signals, glass). This is the foundation.
- **The `.ds-cyan-signal` interaction pattern** for any clickable element. Transforms hover from a color swap to a tactile event.
- **The glass panel treatment** for tab content containers. Doesn't require a map underneath — works fine over any dark gradient background.
- **Small-caps section headers.** Already close in the current OSS panel; just needs the letter-spacing and color adjustment.
- **Tabular numerals on all data displays.** Free visual alignment, no layout work needed.
- **Focus rings using the accent color.** Replaces the default browser outline with something on-brand.
- **URL state persistence** for tab/filter selections. Already partially done for predict query input via localStorage; extending to `window.location.hash` would complete the pattern.
- **`data-label` tooltips** on compact icon-only controls (like the refresh `↻` button).

## What does NOT port

- **The map itself.** We don't have geospatial data. Don't simulate it.
- **The categorical fuel-color palette.** Our semantic model is "stages of a process" (staged → promoted → falsified), not "types of a thing." Signal colors (positive/negative/warning/info) fit our domain better than the plant-type palette.
- **The hexagonal minimap.** Nothing to put in a second view.
- **`backdrop-filter: blur(32px)`.** 32px is *very* aggressive and expensive on weaker GPUs. Start at 20px for Exocortex; push to 32 only if it's not enough.
- **Avenir Next.** It's a paid font and the fallback (`Inter`) works. Don't mess with font licensing.

## Extraction methodology used

1. Saved the page as "Complete" from the browser to get HTML + CSS files
2. Ran 9 targeted greps against the compiled CSS:
   - `transition[^;]*` — all transition declarations
   - `cubic-bezier[^)]*` — easing curves
   - `backdrop-filter[^;]*` — blur/saturate values
   - `--[a-z-]+:` — all CSS custom properties
   - `:hover\{[^}]*\}` — hover states
   - `:active\{[^}]*\}` — active states
   - `@keyframes [a-z-]+` — animations
   - `font-family:` — font stacks
   - `box-shadow:[^;]*` — shadows (filtered for glow patterns)
3. Discovered they expose a complete `--ds-*` prefixed design system — extracted all 73 variables wholesale
4. Translated specific component classes to portable utility classes

**Total extraction time:** ~30 minutes from first grep to complete tokens file.

## Caveats

- I extracted from the loaded HTML shell, not the runtime-rendered DOM. Some variables may only exist on specific page states (light mode, compact mode, etc.) — I included light-mode counterparts but didn't verify every rule that uses them.
- The screenshot shows Connecticut — the specific colors of dots in the legend are data-driven, not design tokens. They come from a separate plant-type → color map we didn't extract.
- `saturate(150%)` inside `backdrop-filter` is what makes the map look *lit* underneath panels. On browsers/hardware that don't support backdrop-filter with saturate, this degrades to plain blur (still good).
