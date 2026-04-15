# System.css — UI reference notes

**URL:** https://github.com/sakofchit/system.css · https://sakofchit.github.io/system.css/
**Tagline:** "A design system for building retro Apple interfaces."
**Domain:** Aesthetic recreation of classic Mac OS (System 1-7, 1984-1995).
**Tech:** Single CSS file, 698 lines, plus bundled bitmap fonts.
**Captured:** 2026-04-14
**Why this matters:** The most minimal color palette in the library (4 colors). Several clever pure-CSS techniques for recreating 1-bit dithering and dotted desktop patterns. Phase 3 reference — informational rather than directly portable.

## What's distinctly System.css

### 1. Four colors total — the entire palette

```css
--sys-color-white:    #FFFFFF;
--sys-color-black:    #000000;
--sys-color-grey:     #A5A5A5;
--sys-color-darkgrey: #B6B7B8;
```

Plus a three-tier semantic mapping (`--sys-primary: white`, `--sys-secondary: black`, `--sys-tertiary: grey`) and a single `--sys-disabled` token. **That's the entire color system.** Even more minimal than Tufte CSS (which had 5 colors).

The reason: classic Mac OS was 1-bit (black/white) initially, then 4-bit greyscale by System 7. The hardware imposed the constraint. System.css faithfully recreates the constraint.

The lesson: **discipline through hard limits.** When you can't add a color, you have to use the colors you have well. Compare to Carbon (900 tokens in dark theme alone) — the opposite philosophy. Both produce coherent interfaces; the path is different.

### 2. Single-token shadow — `--box-shadow: 2px 2px`

System.css ships ONE shadow value used everywhere. No blur. No color. No size variants. Every dialog, button, and modal gets the same hard offset shadow.

```css
--sys-box-shadow: 2px 2px;  /* defaults to currentColor */
```

When `box-shadow` is given only offsets without a color, it defaults to `currentColor` (the element's foreground color). This means the shadow is always the same color as the element's text — automatic monochrome theming with no per-component color decisions.

For Exocortex: not directly portable (we want richer shadows), but the **currentColor-default trick** is worth knowing. Any element where the shadow should match the text color can use offsets-only `box-shadow` and skip explicit color.

### 3. The dotted desktop grid via crossed linear-gradients

The classic Mac OS desktop had a dotted grid pattern. System.css recreates it with two crossed linear-gradients and zero image assets:

```css
body {
  background:
    linear-gradient(90deg, var(--primary) 21px, transparent 1%) center,
    linear-gradient(var(--primary) 21px, transparent 1%) center,
    var(--secondary);
  background-size: 22px 22px;
}
```

Two gradients (vertical and horizontal) with 21px stops create a 22x22 tiled pattern. Pure CSS, scales to any viewport, no images.

**The technique generalizes**: any tiled background pattern can be implemented with 2-3 linear-gradients and `background-size`. Polka dots, grids, stripes, checkerboards — all CSS-only.

For Exocortex: reserved as a technique for any future retro mode or pattern overlay. We currently use a radial gradient for the body backdrop; we could swap in a subtle dot grid for an opt-in retro view.

### 4. 1-bit dither via 45-degree gradient

The Mac scrollbar uses a 50% gray dither pattern (alternating black and white pixels at 1:1 ratio) to fake a mid-tone on a 1-bit display. System.css recreates it with two crossed 45-degree gradients:

```css
::-webkit-scrollbar-track {
  background:
    linear-gradient(45deg, var(--secondary) 25%, transparent 25%,
                    transparent 75%, var(--secondary) 75%, var(--secondary)),
    linear-gradient(45deg, var(--secondary) 25%, transparent 25%,
                    transparent 75%, var(--secondary) 75%, var(--secondary));
  background-size: 4px 4px;
  background-position: 0 0, 2px 2px;
}
```

The two gradients are offset by 2px to create the alternating pixel pattern. The result is a 50% gray that's actually composed of pure black and white pixels.

**This is brilliant.** It's the technique used by the Mac to display gray on 1-bit hardware, recreated in CSS. For Exocortex: useful for any "1-bit retro mode" we might add. Reserved as a pattern.

### 5. Computed token geometry

System.css uses CSS calc() to derive radio button and checkbox dimensions from base tokens:

```css
--radio-dot-top: calc(var(--radio-width) / 2 - var(--radio-dot-width) / 2);
--radio-dot-left: calc(-1 * (var(--radio-total-width-precalc))
                       + var(--radio-width) / 2 - var(--radio-dot-width) / 2);
```

Change `--radio-width` and the dot automatically re-centers. This is a pattern more sophisticated than most production design systems use.

The lesson: **when geometry has interdependent values, compute them at the token level**. Radio button positioning is the canonical example — the dot centering depends on the radio width which depends on the label spacing. Computed tokens are more robust than hardcoded duplicate values.

For Exocortex: we don't have radios or checkboxes (no forms beyond text inputs), but the technique is worth knowing for future form components.

### 6. Bitmap fonts (Chicago, Monaco, Geneva)

System.css ships four bitmap fonts:
- **Chicago** — the original Mac UI font (System 1-7)
- **Monaco** — the original Mac monospace
- **Chicago_12** — a recreation that works at 12pt
- **Geneva_9** — a recreation of the 9pt body font

Bitmap fonts only look right at their native size (12pt Chicago renders crisply; 13pt looks jagged). On modern displays this is a constraint — the fonts can't scale.

For Exocortex: don't port bitmap fonts. We use IBM Plex Mono which scales cleanly. The lesson: pixel-perfect typography mattered when pixels were visible. On modern high-DPI displays, vector fonts win.

## What ports to Exocortex

System.css's value is in **techniques**, not values. None of its colors or component styles port directly (we're dark-themed, not 1-bit Mac).

1. **The `currentColor`-default box-shadow trick** documented as a technique. Useful when shadows should match text.

2. **Linear-gradient pattern technique** documented for any future retro mode or background pattern overlay.

3. **Computed token geometry pattern** documented for any future form components where radio/checkbox/slider dimensions need to scale together.

4. **The "discipline through hard limits" philosophy** documented as a guideline. When you have only N colors, you have to use them well. Adding more colors doesn't necessarily improve the UI.

## What does NOT port

- The 4-color palette
- Bitmap fonts (Chicago, Monaco, etc.)
- The dot grid desktop background
- The 1-bit dither scrollbar
- The Mac OS-specific component styles (modeless dialogs, alert boxes with the `<title-bar>` element)
- The hard 2px drop shadow as the only shadow
- The Mac-specific scrollbar with up/down arrow buttons

## Cross-pollination notes

**With Tufte CSS**: Both have minimal color palettes and zero animations. But the philosophies differ:
- Tufte's minimalism is about reading focus
- System.css's minimalism is about hardware constraint authenticity

**With TuiCss**: Both are retro-system recreations with no animations. TuiCss is MS-DOS character mode; System.css is Mac OS bitmap GUI. Same era (1980s-90s), different platforms.

**With Carbon**: Carbon ships 900 tokens in dark theme alone; System.css ships 4 colors total. Both produce coherent interfaces. The lesson: the right number of design tokens depends on what you're building, not what's "modern best practice."

## Caveats

- The bitmap fonts have licensing requirements (Chicago is Apple-owned). The recreations by Giles Booth (Chicago_12, Geneva_9) are free.
- The `svg-load(...)` syntax in scrollbar buttons is a postcss-inline-svg plugin convention, not standard CSS. The shipped CSS file uses inline data URIs after build.
- The 22px tile size for the desktop dot pattern is calibrated for 72dpi displays. On modern high-DPI displays it would render slightly differently.

## Extraction methodology used

System.css is small and well-organized. Single CSS file, 698 lines. Read top to bottom in ~15 minutes. The interesting patterns are concentrated in the opening 200 lines (color system, scrollbar, body backdrop) — the rest is component-by-component recreation of Mac OS UI elements.

**Total extraction time: ~15 minutes**, fastest of any reference so far.
