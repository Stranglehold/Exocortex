# 7.css — UI reference notes

**URL:** https://khang-nd.github.io/7.css/ · https://github.com/khang-nd/7.css
**Tagline:** "CSS library for building interfaces that look like Windows 7."
**Domain:** Aesthetic recreation. Lets web developers build interfaces that look like Windows 7 (the Aero era — translucent glass, gradient buttons, Segoe UI typography).
**Tech:** SCSS source compiled to CSS. ~24 component partials in `gui/`. Single compiled output.
**Captured:** 2026-04-14

## The single most important finding

**7.css implements "glass" entirely with stacked CSS gradients and box-shadows. It does NOT use `backdrop-filter`.**

This matters because we now have **two valid approaches to glass UI** in our reference library:

| OpenGridWorks glass | 7.css glass |
|---|---|
| `backdrop-filter: blur(20px) saturate(140%)` | Layered gradients with inset white highlights |
| Real-time GPU blur of whatever's behind | Pre-baked highlight bands, identical regardless of context |
| Modern, expensive (GPU shader pass per frame) | Period-authentic, cheap (no shader) |
| Requires content behind the panel to look right | Works on any background |
| Browser support varies (Safari needs `-webkit-`, some configurations disable it) | Works everywhere |

**For Exocortex, this means we have a fallback.** If `backdrop-filter` proves expensive on Jake's hardware, or if we ever want a panel that looks "lit" without depending on what's behind it, we can fall back to the 7.css approach: `linear-gradient(rgba(255,255,255,0.4), rgba(0,0,0,0.1), rgba(255,255,255,0.2))` over a base color, with `box-shadow: inset 0 0 0 1px rgba(255,255,255,0.8)` for the edge highlight.

## What 7.css reveals about Aero's tricks

### 1. The hard-stop gradient is the signature

Every 7.css element uses gradients with a HARD STOP at 45%:

```css
--w7-el-grad: linear-gradient(#f2f2f2 45%, #ebebeb 45%, #cfcfcf);
```

The `45%` value appears twice — once for where the light region ends, once for where the darker region begins. This creates a sharp transition at the midline, implying a curved surface caught in raking light. It's mathematically flat, but the eye reads it as 3D.

This is the SINGLE most identifiable visual trait of Aero. If you see hard-stop two-tone gradients on a button, you're looking at a Windows 7-era UI.

### 2. Asymmetric hover transitions

7.css buttons fade hover state in **fast** (0.3s ease) and out **slow** (1s linear):

```scss
&:hover { transition: 0.3s; }       // fast in
&:not(:hover) { transition: 1s linear; }   // slow out
```

This creates the feeling that the button "noticed you" and is lingering after your cursor moved on. It's a 0.7-second-long subliminal acknowledgment of the interaction.

OpenGridWorks uses symmetric 150ms transitions — fast in both directions. **Both are correct in their context.** Symmetric feels precise; asymmetric feels warm. Use asymmetric for elements that benefit from feeling "humanized" (welcome panels, primary CTAs); use symmetric for elements that should feel mechanical (controls, status indicators).

### 3. State changes via stacked pseudo-elements

Instead of changing a button's `background-color` directly, 7.css layers pre-built backgrounds via `::before` (hover) and `::after` (active) and fades their opacity:

```scss
button {
  background: var(--w7-el-grad);          // default state
  &::before { background: var(--w7-el-grad-h); opacity: 0; }  // hover layer
  &::after  { background: var(--w7-el-grad-a); opacity: 0; }  // active layer
  &:hover::before { opacity: 1; }
  &:active::after { opacity: 1; }
}
```

This lets you cross-fade between completely different appearances (different gradient colors, different shadows, different border radii) instead of trying to interpolate between two background-color values. The result is smoother because gradients can't be CSS-interpolated cleanly, but opacity can.

**Worth porting** if we want richer state transitions on Exocortex buttons. Currently our buttons swap colors directly; the pseudo-element approach would let us do gradient transitions properly.

### 4. The pulse-on-default-button affordance

Aero's "this is the default action, press Enter" indicator is a slowly-pulsing cyan inner glow:

```scss
@keyframes pulse-anim {
  from { box-shadow: inset 0 0 3px 1px #34deffdd; }
  to   { box-shadow: inset 0 0 1px 1px #34deffdd; }
}
.default-button { animation: 1s ease infinite alternate pulse-anim; }
```

The blur radius alternates between 3px and 1px every second, creating a subtle breathing effect. It's not flashy enough to be distracting, but it draws the eye to the button you should press.

**This is genuinely useful** for Exocortex's Predict button or any "primary action" CTA.

### 5. Border colors signal interaction state

Four border colors map to four states:

| State | Variable | Color | Meaning |
|---|---|---|---|
| Default | `--w7-el-bd` | `#8e8f8f` neutral gray | "you can interact with me" |
| Hover | `--w7-el-bd-h` | `#3c7fb1` Aero blue | "you're touching me" |
| Active | `--w7-el-bd-a` | `#6d91ab` muted blue | "you're pressing me" |
| Disabled | `--w7-el-bd-d` | `#adb2b5` light gray | "I'm not available" |

The hover blue is desaturated when active — a subtle "you've engaged this" cue that doesn't add another color. We could borrow this for our cyan signal: `var(--ds-accent-cyan)` on hover, slightly desaturated cyan on active.

## What ports to Exocortex

1. **Layered-gradient glass technique** — vendored as `.ds-aero-glass` utility. Useful if `backdrop-filter` proves too expensive or if we want a glass panel that doesn't depend on what's behind it.

2. **Asymmetric hover transitions** — vendored as `--ds-duration-hover-out: 1s` + `--ds-duration-hover-in: 0.3s`. NOT applied as a default — this would override OpenGridWorks's symmetric 150ms transitions everywhere. Available as opt-in for elements that want the warmth.

3. **Pulse animation for default buttons** — vendored as `--ds-anim-default-pulse` + `@keyframes ds-default-pulse`. Apply to the primary action button on any form that responds to Enter.

4. **Hard-stop gradient pattern** — vendored as `.ds-hard-stop-gradient` utility class. The signature 45% hard-stop technique is the single most visually distinctive element of Aero. Useful for any element that should read as a "raised surface" rather than a flat color block.

5. **Border-state color scheme** — informs how we currently use border-color on hover. Worth noting that desaturating the active border is a real Aero technique we could borrow.

6. **Stacked-pseudo-element state layering** — NOT vendored as a token, but documented as a technique. If we want to do gradient transitions cleanly, this is how. May graduate later if we adopt richer button styling.

## What does NOT port

- **The full Aero color palette** (light theme, gray + blue). Our panel is dark-only. Aero is fundamentally a light-theme aesthetic — the gradient highlights only work on light surfaces because they imply light hitting the surface from above. Trying to do "dark Aero" produces a contradiction (dark surface with white highlights = looks broken, like the surface is lit from below).
- **The `--w7-w-glass` stripe pattern.** It's a 50-line gradient with stripe positions that recreate Aero's wallpaper-sheen effect. Beautiful but extremely period-specific. Doesn't suit our intelligence-console aesthetic.
- **Segoe UI as the default font.** It's Microsoft proprietary. We'd use Inter or system-ui as fallback.
- **The window control gradients** (`--w7-wct-*`). These are min/max/close button styling that we don't have an equivalent for in our flat panel.
- **Gentle 3px border-radius across everything.** Aero's "softness" comes partly from this rounding. Our panel uses `--ds-radius-sm: 6px` which is similar but slightly more pronounced. Aero's 3px would feel dated in a modern UI.

## Cross-pollination notes

**With OpenGridWorks:** OpenGridWorks's glass uses real backdrop-filter. 7.css's glass fakes it with gradients. Both are valid. Having both in our reference library means we have a fallback for hardware/browser issues.

**With TuiCss:** TuiCss has zero animations; 7.css has the pulse animation, the asymmetric hover fade, AND a transition on every interactive element. They're at opposite ends of the "how much should the UI move" spectrum. OpenGridWorks sits in the middle.

**With Open Props:** Open Props has 81 named easing curves; 7.css uses just two (`ease` and `linear`). 7.css's restraint is informative — the asymmetric timing (`0.3s ease` vs `1s linear`) does more work than any fancy easing curve would. Sometimes the curve doesn't matter as much as the duration mismatch.

## Caveats

- 7.css is SCSS source, not pre-compiled CSS. To extract from the compiled output, you'd need to run the build (npm + sass). I extracted from the SCSS partials directly by reading them, which gave cleaner results than parsing minified output.
- The library is light-theme only. There's no dark-mode variant in upstream. If we want "dark Aero" we'd have to invent it, and based on first principles, dark Aero doesn't really exist as a coherent aesthetic — Aero is fundamentally about light hitting glass.
- The `--w7-w-glass` stripe pattern is a 50-line gradient with carefully positioned stripes. I included a simplified version in `tokens.css` (the three-stop horizontal gradient + base color) but skipped the full stripe pattern. If we ever want it, the source is in `_window.scss`.
- The font is `9pt "Segoe UI"`. Note the `pt` units — 7.css uses points, not pixels. We use pixels consistently, so any port would convert (`9pt ≈ 12px`).

## Extraction methodology used

7.css is structured as SCSS partials, one per component. I went straight to:

1. **`_variables.scss`** (the global token file) — got the naming convention and all base tokens
2. **`_window.scss`** (the window/glass component) — saw how the Aero glass is constructed
3. **`_button.scss`** (the button component) — saw the stacked-pseudo-element pattern and asymmetric transitions
4. **`_typography.scss`** (just to round out the typography colors)

Skipped the 9 greps because the source is already organized by category. **For a well-structured framework**, reading the per-component partials is faster than grepping the compiled output.

**Total extraction time:** ~15 minutes. Comparable to TuiCss because both are well-organized small libraries. The lesson: **methodology should adapt to source structure**. Application sites need 9-grep against compiled CSS. Token libraries need the prefix counter. Component-based frameworks like 7.css need per-file reads.
