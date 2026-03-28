# Spec: Aesthetic Theme Engine (Wallpaper Engine for Agent Zero)

**Status:** Ready to build. Agent's existing palette-swap system provides the foundation. Extension does not require changes to Agent Zero core.
**Date:** 2026-03-27
**Authors:** Kestrel, with design direction from Jake
**Related:** Agent Zero webUI (`/a0/python/`), `themes/` directory, existing Flask theme route and ThemeManager

---

## Origin

The agent built a working palette-swap theme system during prior session work: a Flask route serving theme JSON, an Alpine store binding it to the UI, a ThemeManager class applying CSS variables, and 6 initial themes. The bones are good.

This spec extends that foundation into a full atmospheric theming system — recreation of game UI aesthetics with background images, CSS overlay effects, and canvas animations. The organizing metaphor is Wallpaper Engine for Agent Zero: themes as atmosphere, not just color palettes.

Reference images analyzed from the user's UI examples folder informed every design decision below.

---

## Reference Aesthetics

Six source aesthetics were analyzed. Each maps to a tier and a showcase theme.

**NieR: Automata** — Pure typography, near-monochrome, system boot log aesthetic. Loading screen: "LOADING - BOOTING SYSTEM.." with YoRHa logo watermark behind text. Directly maps to Agent Zero chat output structure. Typography alone carries the entire aesthetic — no background, no effects required. This is the proof that a Tier 1 palette can be a complete artistic statement.

**MGS V: The Phantom Pain** — Photorealistic background bleeds through translucent panels (iDroid). Diamond Dogs emblem watermark at ~5% opacity on level complete screen. Sparse white typography over dark. The world-bleeding-through-UI paradigm: the background is not decoration, it is the theme.

**MGS Delta (Snake Eater Remake)** — Codec/radio screen: character portrait in CRT frame, frequency "140.85" in amber gold, photographic texture background, sepia-monochrome tint. The transmission aesthetic — encrypted, degraded, intimate.

**Highfleet** — Physical cockpit instrument cluster: phosphor green radar, amber gauges, riveted metal panels, handwritten and mechanical text mixed. Structurally different paradigm — requires DOM changes. Cited here as Tier 4 future direction, explicitly out of scope for this spec.

**Witcher 3** — Deep red accent, diamond/wolf medallion geometric motif, near-black, medieval manuscript quality. Restrained use of a single heraldic symbol as atmosphere.

**Bravely Default** — Warm parchment, illustrated/watercolor adjacent, fantasy warmth. Included as contrast to the tactical aesthetics — evidence that the framework should accommodate warmth, not just darkness.

---

## Three-Tier System

Themes are classified by what they use. The tier determines complexity, asset requirements, and performance cost.

**Tier 1: Palette** — Colors and fonts only. Single JSON file, no assets. Current system capability. Deploys anywhere, zero performance cost. NieR demonstrates that this tier can be a complete aesthetic.

**Tier 2: Atmospheric** — Background image plus panel translucency plus CSS overlay effects (scanlines, vignette, noise grain, watermark). Requires image assets bundled in `themes/assets/`. Moderate complexity. All effects are CSS — no JavaScript animation loop.

**Tier 3: Immersive** — Canvas-based ambient animations on top of Tier 2. Requires a persistent `requestAnimationFrame` loop. Adds JavaScript animation classes. Reserved for themes where the animation is the aesthetic, not a decoration.

**Tier 4 (out of scope):** Highfleet-style physical cockpit UI. Requires structural DOM changes to Agent Zero's interface. Not addressed in this spec.

---

## Extended JSON Schema

The existing schema carries `colors`, `fonts`, and `preview`. This spec extends it with four new top-level keys: `background`, `panel`, `overlay`, and `animation`.

```json
{
  "name": "YoRHa",
  "author": "Exocortex",
  "description": "NieR: Automata system terminal. Typography as complete aesthetic.",
  "version": "1.0.0",
  "tier": "palette",

  "colors": { },
  "fonts": { },
  "preview": { },

  "background": {
    "type": "none",
    "src": null,
    "opacity": 0.15,
    "blur": 0,
    "blend_mode": "normal",
    "position": "center",
    "size": "cover"
  },

  "panel": {
    "opacity": 1.0,
    "backdrop_blur": 0
  },

  "overlay": {
    "scanlines": { "enabled": false, "opacity": 0.04, "spacing": 2 },
    "noise": { "enabled": false, "opacity": 0.02 },
    "vignette": { "enabled": false, "opacity": 0.3 },
    "watermark": {
      "enabled": false,
      "src": null,
      "opacity": 0.05,
      "position": "center",
      "size": "40%"
    }
  },

  "animation": {
    "type": "none",
    "intensity": 0.5,
    "color": null
  }
}
```

All new keys have explicit defaults. Tier 1 themes omit them entirely — the schema is backward compatible. `ThemeManager` reads new keys with `theme.get("background", {})` fallback to defaults.

---

## CSS Variable Extensions

Add to the CSS variable set generated by `ThemeManager.generateThemeCSS()`:

- `--panel-opacity` — drives the alpha channel of panel background colors
- `--panel-backdrop-blur` — drives `backdrop-filter: blur()` on panels

The existing panel CSS uses solid `background-color: var(--color-panel)`. For atmospheric themes, this becomes:

```css
background-color: rgba(var(--color-panel-rgb), var(--panel-opacity));
backdrop-filter: blur(var(--panel-backdrop-blur));
```

`--color-panel-rgb` is the RGB decomposition of `--color-panel` (e.g., `"13, 13, 13"`) added alongside the hex value when CSS variables are generated. This allows alpha manipulation without switching color formats in the JSON.

---

## Effect Layer Architecture

All effect layers are injected into the DOM by `ThemeManager.applyTheme()` and removed on theme switch. Existing DOM structure is never modified — only dedicated elements are added and removed.

**Layer stack, bottom to top:**

| Element | z-index | Role |
|---------|---------|------|
| `#theme-background` | -10 | Fixed full-viewport div. Background image with opacity and optional blur. |
| Agent Zero's existing panels | (existing) | Unmodified. Panel CSS vars apply translucency. |
| `#theme-canvas` | 9998 | Fixed full-viewport canvas. Animated effects. `pointer-events: none`. |
| `#theme-overlay` | 9999 | Fixed full-viewport div. Scanlines, vignette, noise, watermark as CSS. `pointer-events: none`. |

**`applyTheme()` execution sequence:**

1. Remove `#theme-background`, `#theme-overlay`, `#theme-canvas` if present (cleanup from previous theme).
2. Apply CSS variables to `:root` — existing behavior, unchanged.
3. Inject `--panel-opacity` and `--panel-backdrop-blur` CSS vars.
4. If `background.type !== "none"`: create and insert `#theme-background` div with appropriate inline styles.
5. If any overlay is enabled: create and insert `#theme-overlay` div with CSS-defined effects.
6. If `animation.type !== "none"`: create and insert `#theme-canvas`; instantiate the appropriate animation class and call `start(canvas, config)`.

On theme switch, the cleanup step (step 1) calls `currentAnimation.stop()` if an animation loop is running before removing the canvas element.

---

## Overlay Implementation Details

All overlays are implemented as CSS properties on `#theme-overlay`. No JavaScript is involved in rendering.

**Scanlines** — `repeating-linear-gradient`:
```css
background: repeating-linear-gradient(
  0deg,
  transparent,
  transparent {spacing}px,
  rgba(0, 0, 0, {opacity}) {spacing}px,
  rgba(0, 0, 0, {opacity}) {spacing + 1}px
);
```
`spacing` is in pixels. Values of 2–4 read as CRT lines. Values of 1 read as fine mesh.

**Vignette** — `radial-gradient`:
```css
background: radial-gradient(
  ellipse at center,
  transparent 60%,
  rgba(0, 0, 0, {opacity}) 100%
);
```

**Noise grain** — SVG `feTurbulence` filter injected inline into the overlay div, applied via CSS `filter: url(#theme-noise-filter)`. This is a single `<svg>` element prepended to the overlay div, not a separate DOM insertion.

**Watermark** — `background-image` on the overlay div, centered with `background-position: {position}`, `background-size: {size}`, and `opacity: {opacity}`. SVG assets are preferred for crispness at all viewport sizes. The overlay's own opacity is set to 1; the watermark image carries its own opacity via an `<img>` element with inline `opacity` style, or via the background-image approach with a CSS filter.

Multiple overlay effects compose by layering CSS properties on the same div. Scanlines and vignette can coexist on a single element using a comma-separated background shorthand. Watermark is separate (background-image would conflict). If both are needed, watermark gets a child element within `#theme-overlay`.

---

## Canvas Animations (Tier 3)

Each animation type is a self-contained JavaScript class with a consistent interface:

```javascript
class ThemeAnimation {
  start(canvas, config) { /* set up context, begin requestAnimationFrame loop */ }
  stop() { /* cancel animation frame, release resources */ }
}
```

`ThemeManager` holds a reference to the current animation instance. `stop()` is called before any theme switch that removes the canvas.

**Rain** — MGS2 / Big Shell aesthetic.
- Diagonal line segments, randomized alpha and length, slight blue tint.
- `requestAnimationFrame` loop at uncapped framerate.
- ~150 drops active at default intensity. `intensity` config parameter scales drop count.
- Default color: `#8aafc0` (blue-gray rain on dark background).

**Snow** — Shadow Moses aesthetic.
- Circular particles with slow downward drift and slight sinusoidal horizontal oscillation.
- White or light blue particles, low opacity, varying radius.
- `intensity` scales particle count.

**Particles** — Generic ambient.
- Small dots, very slow drift in randomized directions, color from `animation.color` config.
- Lowest performance cost of the three animated types. Suitable as a subtle background presence.

**Static** — Codec/CRT aesthetic.
- Random pixel noise rendered at low opacity. Full-screen or region-constrained.
- Capped at 24fps to simulate CRT refresh rate — `setTimeout` inside the `requestAnimationFrame` loop enforces this.

All four animation types target a performance floor of 60fps on mid-range hardware at 1080p. Static at 24fps is intentional, not a performance constraint.

---

## Theme Authoring Framework

Two components: an authoring guide document that the agent reads when creating themes, and a validation tool that checks a completed theme JSON before it is committed.

### Authoring Guide (`specs/THEME_AUTHORING_GUIDE.md`)

The authoring guide is a document the agent reads as context when asked to create a new theme. It is structured as a six-step procedure.

**Step 1: Identify the source aesthetic.**
What game, film, or era? What specific screen or moment within it? More importantly: what is the *feeling*, not the visual description. NieR is a corrupted archive. The iDroid is holographic field intelligence. The Codec is an encrypted transmission. The feeling is the brief. The visual elements are how you implement it.

**Step 2: Color extraction.**
Maximum five colors. Identify: background, text, muted text, accent, panel. One accent only — the accent carries all interactive meaning (links, highlights, active states). The test: does this palette work at 1am on a monitor at 50% brightness? High contrast is not the goal. Legibility under fatigue is.

**Step 3: Typography.**
One font stack for UI elements, one for chat/content (can be the same). Monospace for terminal and tactical feel. Condensed sans-serif for efficiency and information density. Serif for manuscript and ancient aesthetics. Do not use novelty display fonts for body text.

**Step 4: Effect decisions.**
For each potential effect: does it serve the feeling, or does it decorate? If it decorates, remove it. Scanlines belong only if CRT or terminal is structurally part of the aesthetic. Background images belong only if the world bleeding through the UI IS the theme. Animation belongs only if the animation is atmospheric — rain is Big Shell, not decoration.

**Step 5: Write the JSON.**
Start from `themes/template.json`. Set `tier` based on what fields are actually used. Fill `preview.background` with the dominant background color. All color values are hex or rgba strings.

**Step 6: Validate.**
Run `python3 themes/validate_theme.py themes/yourtheme.json`. Fix all reported errors before committing.

### Validation Tool (`themes/validate_theme.py`)

A Python script. Takes a theme JSON file path as argument. Checks:

- Required fields present: `name`, `author`, `description`, `version`, `colors`, `fonts`, `preview`
- All color values are valid hex (`#rrggbb`, `#rgb`) or `rgba(r, g, b, a)` strings
- All referenced asset paths (`background.src`, `overlay.watermark.src`) exist in `themes/assets/`
- `tier` claim matches what fields are actually populated (palette theme should have no background/overlay/animation fields with non-default values)
- All numeric values are within valid ranges (opacity 0.0–1.0, blur ≥ 0, spacing ≥ 1)

Prints pass with a summary, or fail with specific field-level error messages. Exit code 0 on pass, 1 on fail.

No LLM calls. Deterministic validation only.

---

## Showcase Themes

Six themes to build, one per source aesthetic, covering all three tiers.

**YoRHa** — `themes/yorha.json` — Tier 1: Palette
NieR: Automata system terminal. Near-white text (`#e8e4dc`) on near-black (`#0a0a0a`). Single green accent (`#52c57a` — "NO ERROR" green). Condensed monospace throughout. No effects. The typography is the aesthetic. Scanlines are optional at `0.03` opacity for users who want the CRT register, but the palette stands without them.

**iDroid** — `themes/idroid.json` — Tier 2: Atmospheric
MGS V field intelligence terminal. Deep navy (`#050d14`) background color. Teal/cyan accent (`#00c8c8`). Panel opacity `0.82`, backdrop blur `12px`. Background: Afghan landscape photograph at `0.12` opacity. Scanlines at `0.03`. Vignette at `0.25`.

**Codec** — `themes/codec.json` — Tier 2: Atmospheric
MGS Delta transmission screen. Dark sepia (`#1a1610`). Amber gold accent (`#c9922e`). Noise grain overlay at `0.025`. Background: jungle foliage or warehouse photograph at `0.18` opacity, blur `4px`. Panel opacity `0.88`.

**Diamond Dogs** — `themes/diamond_dogs.json` — Tier 2: Atmospheric
MGS V mission debrief. Near-black (`#0d0d0d`). White text, amber gold accent (`#c9922e`). Diamond Dogs emblem SVG as watermark at `0.05` opacity, centered. No background image — the emblem is the entire atmospheric layer. Vignette at `0.2`.

**Big Shell** — `themes/big_shell.json` — Tier 3: Immersive
MGS2 / Sons of Liberty. Blue-gray (`#0e1218`). Rain animation, intensity `0.6`, color `#8aafc0`. Panel opacity `0.85`, backdrop blur `8px`. Rainy ocean background photograph at `0.15` opacity.

**Kaer Morhen** — `themes/kaer_morhen.json` — Tier 2: Atmospheric
Witcher 3 character screen. Near-black (`#0d0b0e`). Deep crimson accent (`#8b1a1a`). Wolf School medallion SVG watermark at `0.06` opacity. Background: stone/dungeon photograph at `0.10` opacity. Heavy vignette at `0.4`.

Asset files for Tier 2 and Tier 3 themes live in `themes/assets/`. SVG emblems are authored from scratch (no copyright assets). Photographic backgrounds are sourced from public domain or CC0 repositories.

---

## What This Does NOT Do

- Does not add sound or ambient audio. Browser autoplay restrictions apply, and audio is a distraction in a work tool.
- Does not serve video backgrounds. Performance cost and motion distraction are both disqualifying.
- Does not change Agent Zero's DOM structure. Highfleet-tier cockpit UI is a separate future project requiring structural changes outside the scope of this spec.
- Does not implement a user-facing theme editor or asset upload UI.
- Does not add new routes to Agent Zero's core Python. The Flask theme route already exists from the agent's prior work.
- Does not use LLM calls for color extraction or theme generation. The authoring guide provides deterministic instructions the agent follows directly.

---

## Build Status

The agent's existing work provides the foundation. The delta is:

| Component | Status | Work Required |
|-----------|--------|---------------|
| Flask theme route | Done | None |
| Alpine store | Done (fixed) | None |
| ThemeManager + CSS vars | Done | Extend `applyTheme()` for effect layers |
| Sidebar UI | Done (fixed) | None |
| Theme JSON schema (colors/fonts) | Done | Extend schema with background/panel/overlay/animation keys |
| Background layer (`#theme-background`) | Missing | Add injection to `applyTheme()` |
| Panel translucency CSS vars | Missing | Add `--panel-opacity` and `--panel-backdrop-blur` to `generateThemeCSS()` |
| Overlay layer (scanlines, vignette, noise, watermark) | Missing | Add `#theme-overlay` injection with CSS effect composition |
| Canvas animations | Missing | Add `#theme-canvas` injection and Rain/Snow/Particles/Static classes |
| Schema template + validation tool | Missing | `themes/template.json` + `themes/validate_theme.py` |
| Authoring guide | Missing | `specs/THEME_AUTHORING_GUIDE.md` |
| Showcase themes (6) | Missing | JSON files + SVG assets + photographic backgrounds |

---

## Research Lineage

- **Wallpaper Engine (Valve/Steam, 2018)** — The model for "theme as atmosphere." Layered background system with animation types, performance modes, and community packs. Establishes that backgrounds can be a serious part of an application's identity without compromising usability.
- **CSS `backdrop-filter` specification (W3C Filter Effects Level 2)** — `backdrop-filter: blur()` for panel translucency. Supported Chrome 76+, Firefox 103+, Safari 9+ (with prefix). No polyfill needed for modern browsers.
- **NieR: Automata UI design (Yoko Taro / PlatinumGames, 2017)** — Typography as a complete aesthetic system. Monochrome palette with single accent. System boot log as emotional device. Demonstrates that Tier 1 (palette only) can be a fully realized artistic statement.
- **Metal Gear Solid V: The Phantom Pain (Konami, 2015)** — World-bleeding-through-UI paradigm. Photographic backgrounds behind translucent panels. The iDroid interface is the direct design reference for the iDroid showcase theme.
- **Metal Gear Solid Delta: Snake Eater (Konami, in development)** — Codec transmission screen aesthetic: amber frequency display, CRT portrait frame, photographic texture background. Reference for the Codec showcase theme.
- **Highfleet (Microprose, 2021)** — Physical instrument panel aesthetic. Cited as Tier 4 future direction. Included in lineage because it establishes the outer boundary of what "theme" can mean when DOM structure is in scope.
- **CSS scanline techniques** — Established pattern in retro and terminal UI design communities. Uses `repeating-linear-gradient` to approximate phosphor screen line structure. No external libraries required.
- **SVG `feTurbulence` filter** — W3C SVG specification. Procedurally generates noise texture in the browser with no image asset. Used for the noise grain overlay effect.
