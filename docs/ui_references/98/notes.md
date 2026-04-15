# 98.css — UI reference notes

**URL:** https://github.com/jdan/98.css · https://jdan.github.io/98.css/
**Tagline:** "A design system for building faithful recreations of old UIs."
**Domain:** Windows 98 interface recreation.
**Tech:** Single minified CSS file, ~24KB, 0 CSS custom properties, 7 colors total.
**Captured:** 2026-04-14
**Why this matters:** The cheapest depth-from-nothing technique in the library. The four-layer inset box-shadow bevel produces chiseled 3D surfaces with zero gradients, zero images, and four lines of CSS. Phase 3 reference — informational, but the bevel technique is directly portable.

## What's distinctly 98.css

### 1. Zero CSS variables — everything hardcoded

There's no `:root` block. There are no custom properties. Every color, shadow, and border width appears inline as literal values. This is not a oversight — it's an honest architectural choice. Windows 98 has ONE aesthetic. There is no theming. There is no dark mode. Hardcoding is the correct shape for a fixed aesthetic.

Contrast with Carbon (900 tokens in dark theme alone) and System.css (still 4 named tokens in a `:root` block despite shipping only 4 colors). 98.css goes further: even the 4 colors aren't named. They just appear where they're used.

**The lesson:** tokens are for systems that vary. If nothing varies, tokens are overhead. The right number of design tokens depends on what you're building. For Exocortex, we need tokens (multiple states, themes, surfaces). For 98.css, they'd be waste.

### 2. The four-layer beveled border

This is THE technique. Every raised element in Windows 98 is built from the same four stacked inset box-shadows:

```css
box-shadow:
  inset -1px -1px #0a0a0a,  /* outer dark (bottom-right) */
  inset  1px  1px #fff,     /* outer light (top-left) */
  inset -2px -2px grey,     /* inner dark (bottom-right) */
  inset  2px  2px #dfdfdf;  /* inner light (top-left) */
```

Two layers of bevel. Outer edge gets the strongest contrast (pure white / near-black). Inner edge gets weaker contrast (silver-grey highlight / mid-grey shadow). The result is a chiseled 3D surface that looks exactly like a Windows 98 button.

**The "pressed" state just swaps the four colors:**

```css
box-shadow:
  inset -1px -1px #fff,
  inset  1px  1px grey,
  inset -2px -2px #dfdfdf,
  inset  2px  2px #0a0a0a;
```

The light source has inverted — the button is now lit from bottom-right, which reads as "pushed in."

**The "sunken input field" uses the pressed pattern.** Same technique, slightly different purpose. Input fields in Windows 98 look sunken into the surface, which 98.css achieves by starting them in the pressed state and never changing them.

**This is brilliant engineering.** Four box-shadows. No gradients. No images. No JavaScript. Works in every browser since 2011. The 3D effect is crisp at any zoom level because there's no blurring — it's just pixel-offset solid colors. Compare to the 24 lines of CSS gradient + radial-gradient + filter hackery that most "neumorphism" libraries use to achieve weaker results.

**For Exocortex:** directly portable as a technique. Swap the colors for dark theme and you have a period-authentic depth cue that costs nothing:

```css
/* Exocortex dark bevel — not actually used yet, but this is how */
--exo-bevel-raised:
  inset -1px -1px #000,                /* outer dark */
  inset  1px  1px rgba(255,255,255,0.08), /* outer subtle light */
  inset -2px -2px rgba(0,0,0,0.6),     /* inner dark */
  inset  2px  2px rgba(255,255,255,0.03); /* inner whisper */
```

Reserved as a technique for when we need cheap depth on a panel without backdrop-filter.

### 3. The engraved disabled-text pattern

Disabled labels in Windows 98 aren't dimmed. They're **engraved** into the silver background:

```css
.disabled {
  color: grey;                      /* mid-grey text */
  text-shadow: 1px 1px 0 #fff;      /* white highlight 1px down-right */
}
```

The text is grey (so it looks weaker than active text). The white shadow catches the upper-left edge of each letter, creating the look of text pressed into metal. On the silver background, this reads as "etched" rather than "faded."

This trick ONLY works on a mid-grey background with light text against a white highlight. Swap to dark theme and the effect reverses — you'd need a DARK highlight offset UP-LEFT to create "engraved" on a dark surface, which is weaker but still readable.

**For Exocortex:** limited direct use, but the principle generalizes — disabled state can be communicated via *texture* (etched, embossed) instead of *opacity*. Opacity is the lazy default. Texture is the interesting alternative. Worth considering for toggle states where fade-to-transparent looks wrong.

### 4. Title bar gradients — the first UI gradient most people saw

```css
.title-bar {
  background: linear-gradient(90deg, navy, #1084d0);  /* active */
}
.title-bar.inactive {
  background: linear-gradient(90deg, grey, #b5b5b5);  /* inactive */
}
```

Horizontal left-to-right. Navy (#000080) on the left sliding into #1084d0 (a slightly brighter Windows blue) on the right. This was the first linear gradient most Windows users ever noticed — Windows 3.1 had solid-color title bars; Windows 98 introduced the gradient.

**For Exocortex:** we don't use title bars in the dashboard context, but the technique of "active vs inactive via gradient saturation swap" is worth knowing. A desaturated version of the same gradient communicates "not focused" without changing the layout.

### 5. Dotted keyboard focus outline

```css
button:focus {
  outline: 1px dotted #000;
  outline-offset: -4px;
}
```

The 1px dotted outline is period-authentic but looks wrong on modern high-DPI displays where subpixel rendering makes dotted outlines inconsistent across devices. The interesting bit is `outline-offset: -4px` — negative offset draws the outline INSIDE the element instead of around it, which leaves the bevel undisturbed.

**For Exocortex:** don't port the dotted style, but the negative-offset trick is useful for any element where a focus ring shouldn't displace the layout. We already handle focus rings differently — this is filed as a technique only.

### 6. Named CSS colors used at scale

98.css uses CSS named colors where possible: `silver`, `navy`, `grey`. These have exact hex equivalents (#c0c0c0, #000080, #808080) and were chosen in the original CSS1 spec specifically for Windows compatibility. Using them makes the CSS read more semantically ("this is a Windows silver face") and makes minification trivial (shorter than hex).

**For Exocortex:** not portable (we don't want these colors), but it's a good reminder that CSS has named colors beyond the obvious ones, and some were specifically designed to match system palettes.

## What ports to Exocortex

98.css's value is concentrated in ONE technique: the four-layer inset-shadow bevel. Everything else is period-specific.

1. **The four-layer bevel as a depth technique** documented and reserved. If we ever need cheap chiseled depth on a dark panel (old-school terminal skin, retro debug mode, authentic Win98 nostalgia mode), this is the pattern. Costs four box-shadow layers. No images. No gradients. No performance hit.

2. **Pressed state via color inversion** documented as a technique. Any button or toggle that uses a bevel can get "pressed" for free by swapping the four colors. No separate styles needed.

3. **Engraved text via contrasting offset shadow** documented as an alternative to opacity-based disabled states. Not directly portable (needs light background) but the principle (texture instead of fade) is worth keeping.

4. **Zero-variables-when-nothing-varies** as a philosophical checkpoint. When you find yourself adding tokens for values that will never change, stop. 98.css is the extreme case of "tokens are overhead if nothing varies" and the library is the right shape because of it.

## What does NOT port

- The silver (#c0c0c0) body background
- The navy→#1084d0 title bar gradient (wrong color family for our dark theme)
- The dotted keyboard focus outline
- The Pixelated MS Sans Serif bitmap font
- The 12px base font size (we use 13-14px)
- The hardcoded-color architecture (we need tokens for real theming)
- The entire raised/sunken metaphor applied to fields (inputs in dark dashboards don't look sunken — they look like rectangles with borders)

## Cross-pollination notes

**With System.css:** Both are retro desktop recreations with tiny color palettes and zero animations. Both use multi-layer box-shadow tricks. The difference: System.css uses shadows for 1-bit dithering (faking mid-tones on a 1-bit display). 98.css uses shadows for 3D bevels (faking depth on a flat display). Same raw technique, entirely different aesthetic purpose.

**With Carbon:** Carbon has 900 tokens. 98.css has zero. Both produce coherent interfaces. The difference is what they're built to do: Carbon must theme across IBM's product surface; 98.css must recreate exactly one operating system. Both are correctly shaped for their mission. The lesson is that "number of tokens" is not a quality metric — it's a fitness-for-purpose metric.

**With OpenGridWorks:** OpenGridWorks uses 73 CSS custom properties and achieves a specific cyberpunk aesthetic. 98.css uses zero custom properties and achieves an equally specific Windows 98 aesthetic. Both work. The variable count didn't determine aesthetic quality — commitment to a specific target did.

**With TuiCss:** Both are retro UI recreations with no animations. TuiCss is phosphor terminal; 98.css is GUI. Same era (late 80s / 90s), different interaction paradigms. TuiCss has CSS variables because MS-DOS shipped multiple color schemes (Turbo Vision, Norton Commander, Windows 3.1 console). 98.css has none because Windows 98 had one. Token count tracks the source material's variability.

## Caveats

- The library depends on two bitmap font files (woff/woff2) that must be served alongside the CSS. If the fonts 404, the fallback to Arial makes everything look wrong (Arial at 12px doesn't have the pixel crunch of Pixelated MS Sans Serif).
- Named CSS colors (`silver`, `navy`, `grey`) are resolved by the browser and are guaranteed equivalent to their hex values, but some CSS minifiers will rewrite them. Don't rely on the string literal matching across build steps.
- The 1px-dotted focus outline renders differently on high-DPI displays. For modern use, pair with a better focus ring or override it.
- Title bar gradients are 2-stop linear gradients; on retina displays the banding is visible. Add a third stop (navy, #0a4a9e, #1084d0) to smooth it out if porting.

## Extraction methodology used

98.css is small (24KB minified) and self-contained. No dependencies, no variables, no external assets beyond fonts. The interesting patterns concentrate into box-shadow declarations — one `grep "box-shadow:"` surfaces the entire structural vocabulary of the library.

Full extraction via: fetch CSS → grep box-shadow → grep linear-gradient → grep hex colors → grep named colors → grep outline → grep text-shadow. Seven greps, complete picture.

**Total extraction time: ~12 minutes**, faster than System.css. The 98.css vocabulary is smaller and more focused. When a library has one big idea (the four-layer bevel), analysis converges quickly.
