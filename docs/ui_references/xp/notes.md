# XP.css — UI reference notes

**URL:** https://github.com/botoxparty/XP.css · https://botoxparty.github.io/XP.css/
**Tagline:** "A design system for building faithful recreations of old UIs."
**Domain:** Windows XP Luna theme (2001-2006).
**Tech:** Single CSS file, ~256KB, extends 98.css's vocabulary with multi-stop gradients.
**Captured:** 2026-04-14
**Why this matters:** The Luna title-bar gradient pattern (8-stop vertical gradient with intentional reflection bands) is the technique for "glossy 3D surface" that replaced flat colors. One transition in the entire library validates a minimal-motion philosophy. Phase 3 reference — informational, with one technique worth archiving.

## What's distinctly XP.css

### 1. It's 98.css plus gradients

XP.css is explicitly a superset of 98.css. The bevel patterns, the color naming conventions, the scrollbar styling, the beige `#ece9d8` dialog background — all inherited directly from 98.css. You can see the same four-layer `inset -1px -1px #0a0a0a, inset 1px 1px #fff, ...` bevel structure repeated throughout.

What XP.css adds is **multi-stop vertical gradients** replacing flat color fills. Every surface that was a flat color in 98 gets a 4-8 stop gradient in XP. The bevels remain (they're what makes edges "chiseled"), but the faces go from silver-flat to gradient-plastic.

**The lesson:** design systems evolve by layering. XP didn't rip out 98's bevel vocabulary — it extended it. The bevel handles the edge-definition job; the gradient handles the surface-material job. Two orthogonal techniques composing into one visual language.

**For Exocortex:** the pattern of "extend rather than replace" is the right model for our own reference library. When we adopt a Phase 3 technique (chunky bevel, gradient surface, striped progress bar) it should layer on top of our existing token system, not replace anything.

### 2. The Luna title bar — 8-stop vertical gradient with reflection bands

The signature XP title bar:

```css
background: linear-gradient(
  180deg,
  #0997ff,           /* top highlight */
  #0053ee 8%,
  #0050ee 40%,
  #06f    88%,
  #06f    93%,       /* thin flat band */
  #005bff 95%,
  #003dd7 96%,       /* thin dark band = "reflection line" */
  #003dd7            /* shadow fill to bottom */
);
```

Notice the stops aren't evenly spaced. Most of the gradient falloff happens between 0% and 40% (the top highlight fading down). The middle 40-88% is nearly flat primary blue. The bottom 88-96% is a compressed shadow band with a tiny "flat pixel" at 88-93% — that's the deliberate highlight line that gives XP chrome its glossy "reflection" appearance.

This is not a natural falloff. It's hand-tuned to look like a curved plastic surface catching a light source from above. Real plastic doesn't interpolate linearly from bright to dark — it has a bright highlight band, a mid-tone middle, a dark shadow band, and usually a subtle "reflection" near the bottom. The 8 stops let you fake all of those with linear-gradient.

**Compare to 98.css's title bar:** `linear-gradient(90deg, navy, #1084d0)`. Two stops. Horizontal. Flat interpolation. 98's title bar looks like "blue fading to darker blue." XP's title bar looks like a shiny blue plastic strip. Same CSS feature (linear-gradient), completely different visual outcome, all down to stop count and hand-tuning.

**For Exocortex:** directly useful as a technique. The pattern "multi-stop vertical gradient with hand-tuned reflection bands" can produce any material look (plastic, glass, metal, leather) depending on color choice. Reserved as a technique for any future "glossy mode" or skeuomorphic accent panel. Not for the primary dashboard — we want flat/minimal — but worth archiving.

### 3. The four-stop Luna surface gradient

For buttons and panels, XP.css uses a simpler 4-stop gradient:

```css
background: linear-gradient(
  180deg,
  #cdcac3,
  #e3e3db 8%,
  #e5e5de 94%,
  #f2f2f1
);
```

The variation is subtle (#cdcac3 is only slightly darker than #f2f2f1). The two middle stops at 8% and 94% create the "squeeze" effect where most of the color change happens at the extreme top and bottom of the element. The middle 86% is nearly flat.

This is the template for "very subtle 3D surface" — the element looks almost flat but has just enough gradient to suggest it's curved. If you want to add depth to a dark-theme panel without going full skeuomorphic, this pattern with tight color variation near the edges is the way.

**For Exocortex:** potentially useful for accent panels that should feel slightly raised. `linear-gradient(180deg, var(--ds-bg-panel) 0%, var(--ds-bg-panel-lighter) 8%, var(--ds-bg-panel-lighter) 94%, var(--ds-bg-panel) 100%)` — two tones of the same base, 8%/94% stops, produces subtle "plastic" without obvious gradient. Reserved as a pattern.

### 4. One transition in 256KB — the minimum viable motion

XP.css contains exactly one `transition:` declaration in the entire file:

```css
button {
  transition: background .1s;
}
```

That's it. 100ms, background only, on buttons. No hover translate, no focus ring fade-in, no active state animation. Just the one thing users most want feedback on (the background color changing under the cursor) at the minimum perceptible duration (100ms).

**This is the fourth Phase 3 reference and the only one with any transitions at all.** System.css: zero. 98.css: zero. NES.css: zero. TuiCss: zero. XP.css: exactly one.

The lesson is about priority. If you had to pick ONE thing to animate in a UI, it would be background color change on hover — it's the most direct feedback that "your cursor is here and this thing is interactive." Everything else (layout shifts, focus rings, scale effects, fade-ins) is optional. XP.css picked the one critical animation and ignored the rest.

**For Exocortex:** this is a useful constraint to measure our own system against. We currently use transitions more broadly (transform, box-shadow, opacity, background). Some of those are legitimate — feedback during drag, panel expand/collapse, modal fade-in. But each should be justifiable as "this is the thing users need to see move for this interaction to feel right." The XP philosophy is a valid calibration point: if you can only have one, the answer is background at 100ms.

### 5. The XP progress bar marquee

The classic XP "loading..." blue bar with sliding white stripes is implemented as:

1. Base layer: solid blue background
2. Overlay layer: `linear-gradient(90deg, #fff 0, #fff 2px, transparent 0, transparent 10px)` — a repeating stripe pattern
3. Animation: `@keyframes sliding { 0% { transform: translateX(-30px); } 100% { transform: translateX(100%); } }`
4. Apply animation to the overlay: `animation: sliding 1s linear infinite`

The stripes aren't really a `repeating-linear-gradient` — they're a single linear-gradient that, combined with the translate animation, creates the illusion of scrolling stripes. The element moves; the "stripes" are just the gradient moving with it.

**For Exocortex:** directly portable as a pattern for any "activity in progress" indicator. We could use this on the Sprint button or the ingestion status to show "currently running" without a spinner. Simpler than the current pulse animations and more immediately readable as "thing is working."

Reserved as a pattern for potential use in the health strip or sprint button.

### 6. The `#ece9d8` dialog beige

XP's dialog background is #ece9d8 — a warm beige that replaced 98's cool silver. This single color change shifted the entire feel of Windows from "gray industrial" to "warm consumer." Small choice, huge impact.

**For Exocortex:** not portable (we're dark theme), but the lesson is worth internalizing: a single surface color choice can redefine an entire aesthetic. The current dark navy we use is doing the same work that #ece9d8 did for XP — setting the temperature of every interaction that touches that background.

## What ports to Exocortex

1. **Multi-stop vertical gradient with reflection bands** as a technique for producing glossy/material surfaces. Reserved for any future skeuomorphic mode or for accent panels that should feel slightly raised. The 8-stop template with hand-tuned highlight/shadow bands is the generalizable pattern.

2. **Tight-stop subtle surface gradient** (4 stops, 8%/94% middle anchors) as a technique for very subtle depth that feels almost flat. Useful for cards or panels that should have just enough dimensionality to suggest interactability.

3. **Sliding stripe marquee** (linear-gradient stripe + translateX keyframe) as a progress/activity pattern. Directly usable for any "in progress" indicator we want to show without a spinner.

4. **"One transition if you can only have one"** as a minimum-viable-motion design principle. Background color at 100ms is the answer. Validates that our current animation set should be measured against "is each of these the background-at-100ms of its use case?"

## What does NOT port

- The Luna blue palette (we use cyan/violet, not royal blue)
- The `#ece9d8` beige dialog background
- The Luna green Start button gradient (wrong color for our UI)
- Pixelated MS Sans Serif and Perfect DOS VGA 437 Win fonts
- The 6-layer chunky bevel (our panels use subtle 1px borders)
- The entire "wet plastic" material aesthetic
- The SVG-based scrollbar arrow buttons

## Cross-pollination notes

**With 98.css:** XP.css IS 98.css plus gradients. The bevel inheritance is visible throughout. Same `#fff / grey / #dfdfdf / #0a0a0a` four-color bevel palette. The extension pattern (add gradients on top of existing bevels) is the model for how design systems evolve without breaking backwards compatibility.

**With System.css:** Both are Mac/Windows retro recreations with minimal vocabularies. System.css is purer (1-bit, no gradients at all). XP.css is lusher (8-stop gradients, reflections, gloss). Both commit fully to their era's visual grammar.

**With NES.css:** Both use multi-layer box-shadows for button depth. NES.css uses a pseudo-element; XP.css layers shadows directly. NES.css has zero transitions; XP.css has one. XP.css is closer to modern UI in motion philosophy, NES.css is more committed to authentic retro.

**With TuiCss:** TuiCss is phosphor terminal (instant everything). XP.css is glossy plastic (almost instant, one 100ms transition). Both agree that transitions should be minimal but pick different minimums.

**With Carbon:** Carbon uses 900+ tokens and assumes motion is compositional. XP.css uses zero tokens and commits to one transition. Different universes, same problem space. The lesson is that token count doesn't predict motion complexity — XP.css has tons of visual variation and almost no motion.

## Caveats

- The Luna title-bar gradient has visible banding on low-color displays. On modern 24-bit displays it's smooth, but on older equipment or certain screenshot tools it may stripe. Add more stops if banding appears.
- XP.css depends on both MS Sans Serif AND "Perfect DOS VGA 437 Win" for the `<pre>` tag. Missing those fonts makes code blocks fall back to browser default monospace, which looks wrong in the XP context.
- The 256KB file size is inflated by SVG scrollbar arrow button data URIs. Strip those (or use the `.no-scrollbar` variant if one exists) to get ~60KB of actual UI CSS.
- The `transform: translateX()` in the sliding animation has sub-pixel rounding issues on some browsers, causing the stripes to "judder." Using `will-change: transform` on the animated element fixes it but may cause GPU memory concerns on low-end hardware.

## Extraction methodology used

XP.css is large (~256KB) but most of that is scrollbar SVG data URIs and sprite-style decorations. The actual UI vocabulary is a set of ~10 linear-gradient declarations, a handful of multi-layer box-shadows (mostly inherited from 98.css), one transition, and one keyframe.

Key greps that produced the full picture:
1. `linear-gradient\([^)]*\)` — 10 unique gradients, this is the entire Luna vocabulary
2. `box-shadow:` — 22 unique, mostly 98.css-inherited bevels plus a 6-layer chunky variant
3. `transition:` — exactly one declaration
4. `@keyframes` — exactly one (`sliding`)
5. `\.title-bar`, `\.progress-indicator`, `button` — the core component rules

Five greps. The interesting findings concentrate in 10 gradient declarations that define XP's entire surface-material vocabulary.

**Total extraction time: ~17 minutes.** Similar to NES.css. The gradient analysis (understanding why the stops are placed where they are) took longer than the raw pattern extraction.
