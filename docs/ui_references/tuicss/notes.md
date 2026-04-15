# TuiCss — UI reference notes

**URL:** https://github.com/vinibiavatti1/TuiCss
**Tagline:** "Library to create MS-DOS interfaces."
**Domain:** Aesthetic recreation. Lets web developers build interfaces that look like text-mode IBM PC software (Norton Commander, Lotus 1-2-3, Borland Sidekick, classic BBSes).
**Tech:** Pure CSS (~46KB un-minified, 2703 lines). Single CSS file plus a custom bitmap font and minimal JS for tab/modal toggling.
**Captured:** 2026-04-14

## What makes it feel right (and what makes it different from OpenGridWorks)

This is the most important finding from the extraction:

**TuiCss has zero CSS custom properties, zero transitions, zero easing curves, zero `:hover`/`:active` pseudo-class rules, and exactly one `@keyframes` rule (the indeterminate progress bar).**

That isn't an oversight. It's the design philosophy. MS-DOS UI didn't animate. State changes happened the moment you pressed a key — there was no transition, no fade, no slide. The aesthetic of "instantaneous response" is what makes a TUI feel precise. A modern fade-in would actively destroy the look.

So TuiCss offers a *contrasting* model to OpenGridWorks's "fluidity through fast transitions":

| OpenGridWorks | TuiCss |
|---|---|
| Fast transitions (150ms) feel responsive | Zero transitions feel instantaneous |
| Tactile scale feedback (`scale(1.06)`) on hover | No hover feedback — click *is* the feedback |
| Color tint on hover signals "interactive" | Color is allocated by category, not by interaction state |
| State interpolation via easing curves | State is binary, swapped via JavaScript class toggling |
| Glow shadows mark "alive" elements | Hard offset drop shadows mark "physical" elements |

Both are valid. They produce *different feelings of correctness*. OpenGridWorks feels alive; TuiCss feels precise.

**For Exocortex:** the OSS panel mostly wants OpenGridWorks's approach (we want responsive dashboard). But there's a place for TuiCss's approach — specifically in **status indicators that should never lie**:

- The "ALL RUNNING / PARTIAL / STOPPED" service status pills should snap to new state instantly with zero fade. A fading status indicator misrepresents reality during the fade.
- Confidence values, claim counts, hypothesis counts — anything where the data IS the message.
- The pause/resume button could lose its scale-up animation in favor of a hard color flip, signaling "I am the source of truth about ingestion state, and I do not lie."

## What I extracted

### The IBM PC 16-color VGA palette (the historical canon)

This is the canonical CGA/EGA palette used by IBM PC text modes from 1981 onward:

```
Base 8 (intensity 0xA8 = 168):
  Black           rgb(0,0,0)
  Blue            rgb(0,0,168)
  Green           rgb(0,168,0)
  Cyan            rgb(0,168,168)
  Red             rgb(168,0,0)
  Purple          rgb(168,0,168)
  Orange/Brown    rgb(168,86,0)
  Light gray      rgb(168,168,168)

Bright 8 (intensity 0xFF = 255):
  Dark gray       rgb(85,85,85)     (a.k.a. "bright black")
  Bright blue     rgb(0,0,255)
  Bright green    rgb(0,255,0)
  Bright cyan     rgb(0,255,255)
  Bright red      rgb(255,0,0)
  Bright purple   rgb(255,0,255)
  Yellow          rgb(255,255,0)    (a.k.a. "bright brown")
  White           rgb(255,255,255)
```

Major Zero from MGS3 would have been looking at exactly these colors on a 1960s/70s mainframe terminal. So would the operators in *War Games*, *Sneakers*, *Three Days of the Condor*, every classic intelligence-agency film. These colors are loaded with cinematic and historical signal.

### Typography

Single font family: custom "DOS" bitmap font with `"Lucida Console"` fallback. No proportional fonts. No font weights (bitmap fonts don't have weights). No italic. The typography decision is made for you the moment you adopt the framework — there is one font, one weight, one style.

The DOS font itself is shipped as a `.ttf` in the TuiCss `resources/` folder. We can fetch it later if we want pixel-perfect retro mode.

### Borders and shadows

- **Borders are 2px solid** for most components, **6px white double** for window chrome emphasis. Borders use the categorical color palette directly.
- **Shadows are hard offset**: `10px 10px black` through `30px 30px black`, with negative-x variants for upper-left direction. **No blur radius.** This produces the "paper sticker on a flat surface" effect rather than the modern "floating element with soft shadow" effect.

### Component classes

State is shown via static class names like `.tui-modal.active`, `.tui-tab.active`, `.tui-button.disabled`. JavaScript toggles these classes — no `:hover` or `:active` pseudo-classes anywhere in the source. This is the pre-CSS3 way of doing things, kept intentionally to match the era.

## What ports to Exocortex

1. **The full 16-color CGA/EGA palette as a `--tui-*` namespace** — already in `tokens.css`. Available to graduate into `exocortex.css` if we ever want to do "deep retro mode" or use the colors for categorical assignment.

2. **Hard drop shadow utility** (`box-shadow: 10px 10px black`) — port as a contrast option to the soft glow shadows from OpenGridWorks. Useful when you want a UI element to read as "physical artifact" rather than "floating alive thing."

3. **The instantaneous-state philosophy** — adopt as a guideline for status indicators specifically. Document in `exocortex.css` as a CSS class like `.ds-instant-state` that explicitly disables transitions:
   ```css
   .ds-instant-state, .ds-instant-state * {
     transition: none !important;
     animation: none !important;
   }
   ```
   Apply to status pills, claim counts, monitor active/paused indicators.

4. **Class-based state instead of pseudo-class state** for elements where the state is canonical, not visual. This is more of an architectural pattern than a CSS pattern, but worth noting in `notes.md`: don't lean on `:hover` / `:active` for state representation, because those bind state to mouse position rather than to data.

## What does NOT port

- **The custom DOS font.** Bitmap fonts at non-native sizes look terrible. Modern monospace (IBM Plex Mono, JetBrains Mono) gives you "monospace feel" without the rendering issues.
- **Hard drop shadows on every element.** The aesthetic only works if it's the *whole interface*. Mixed with modern soft shadows it looks broken.
- **The high-saturation colors at full strength** (`rgb(0,0,255)` bright blue, etc.). These are eye-searing on modern displays. They worked on CRTs because CRTs softened everything. Use the dimmer base-8 colors (`rgb(0,0,168)`) on LCDs.
- **Inline-block layout pattern.** TuiCss uses `display: inline-block` for windows and panels. This is fine for the demo aesthetic but doesn't compose with modern flexbox/grid layouts.

## Caveats

- TuiCss is a *recreation*, not the original DOS rendering pipeline. The colors are accurate but the *texture* of CRT phosphor is gone. If we ever want true CRT feel, we'd need a full-screen overlay shader (scanlines, bloom, chromatic aberration) — that's out of scope for a CSS-only framework.
- The framework targets `display: inline-block` exclusively for windows. Adapting to flexbox/grid layouts requires overriding the framework's display rules.
- The `@keyframes indeterminate` is the only animation in the entire library — used for the loading progress bar's marching stripes. Worth knowing because you can't disable animations entirely without breaking that one component.

## Extraction methodology used

Used the standard 9-grep workflow from `memory/project_ui_reference_library.md`. Findings per grep:

| # | Grep | Result |
|---|------|--------|
| 1 | `--[a-z-]+:` (custom properties) | **Zero** — TuiCss predates the convention, uses literal values |
| 2 | `transition[^;]*` | **Zero** |
| 3 | `cubic-bezier[^)]*` | **Zero** |
| 4 | `backdrop-filter[^;]*` | **Zero** |
| 5 | `box-shadow:[^;]*` | 10 declarations, all hard offsets in pure black, no blur |
| 6 | `:hover\{[^}]*\}` | **Zero** — state via class names, not pseudo-classes |
| 7 | `:active\{[^}]*\}` | **Zero** |
| 8 | `@keyframes [a-z-]+` | One: `indeterminate` (loading bar) |
| 9 | `font-family:` | Two: `"DOS"` (bitmap) and `"Lucida Console", monospace` |

**Total extraction time:** ~12 minutes. Faster than OpenGridWorks because the surface area was smaller and most greps returned empty (which is itself a finding).

The unusual finding ("most greps returned empty") is the most important data point from this analysis. The 9-grep methodology is calibrated for modern frameworks; when applied to a pre-modern one, the *absence* of results is the signal.
