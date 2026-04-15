# NES.css — UI reference notes

**URL:** https://github.com/nostalgic-css/NES.css · https://nostalgic-css.github.io/NES.css/
**Tagline:** "NES-style CSS Framework."
**Domain:** Nintendo Entertainment System (1985) 8-bit UI recreation.
**Tech:** Single CSS file, ~308KB (mostly hand-drawn sprite characters as box-shadow positions).
**Captured:** 2026-04-14
**Why this matters:** The depth-via-pseudo-element pattern is a genuinely useful technique for buttons that shouldn't translate on interaction. The categorical palette validates a lesson about fixed semantic colors. Phase 3 reference — informational, but the pseudo-element trick is worth archiving.

## What's distinctly NES.css

### 1. The file is huge because it contains sprites

NES.css is ~308KB. The vast majority is NOT UI CSS — it's hand-drawn 8-bit sprite characters (Mario, Kirby, Ash, Boo, an octocat, a wave) implemented as single `div` elements with box-shadow declarations containing **dozens of pixel positions each**. Example:

```css
.nes-mario {
  box-shadow:
    24px 12px,30px 12px,36px 12px,42px 12px,48px 12px,
    24px 18px,30px 18px,36px 18px,42px 18px,48px 18px,54px 18px,
    18px 24px,24px 24px,30px 24px,36px 24px,42px 24px,
    ... /* hundreds more */;
}
```

Each `<x>px <y>px` is a "pixel" drawn at that offset. Chain dozens together and you've drawn a sprite. It's beautiful and completely impractical for UI — these sprites are 3-5KB of CSS each and only exist so NES.css can ship an 8-bit Mario you can paste into your page.

Strip the sprites out and the actual UI vocabulary of NES.css is maybe 15KB. The rest is pixel art stored as CSS.

**For Exocortex:** not portable. The technique is fun but the file-size cost is extreme. Filed as "things you can do with box-shadow if you want to prove a point."

### 2. The pseudo-element depth shadow pattern

This is the genuinely interesting UI technique. NES.css buttons do NOT modify their own box-shadow on hover or active. Instead, every button has a `::after` pseudo-element:

```css
.nes-btn::after {
  position: absolute;
  top: -4px;
  right: -4px;
  bottom: -4px;
  left: -4px;
  content: "";
  box-shadow: inset -4px -4px #006bb3;  /* depth color */
}

.nes-btn:hover::after {
  box-shadow: inset -6px -6px #006bb3;  /* deeper */
}

.nes-btn:active:not(.is-disabled)::after {
  box-shadow: inset 4px 4px #006bb3;    /* inverted — pushed in */
}
```

The pseudo-element extends 4px beyond the button on all sides. Its inset box-shadow draws the "depth" color on only the bottom-right side. On hover, the inset deepens (-6px). On active, it inverts (+4px on top-left = "pushed in").

**The button element itself never moves.** No transform. No translate. No resize. The state animation happens entirely in the pseudo-element. Layout is stable regardless of interaction.

This is categorically different from the neumorphism-style "press-in via transform" or the Material-style "elevation change via shadow." The pseudo-element carries all the state visualization. The main element just sits there.

**For Exocortex:** directly portable as a technique. Any button where we DON'T want the element to translate on press can use this pattern. Useful for data-table cells that should show hover/active feedback without causing row reflow. Reserved as a pattern.

### 3. The categorical depth-color pairing

Each button variant has a base color and a darker "depth" color:

| State    | Base     | Depth    | Hue shift |
|----------|----------|----------|-----------|
| Primary  | #209cee  | #006bb3  | blue, -35% L |
| Success  | #92cc41  | #4aa52e  | green, -30% L |
| Warning  | #f7d51d  | #e59400  | yellow → orange (hue shifts toward saturation) |
| Error    | #e76e55  | #8c2022  | red, -45% L |
| Disabled | #d3d3d3  | #adafbc  | grey, slight desaturation |

The depth colors aren't computed algorithmically — they're hand-picked from NES sprite palettes. Each pair comes from actual NES game graphics. The warning pair is the most interesting: the base is yellow and the depth is orange. Not "darker yellow" — a hue shift. This is how NES games handled depth on yellow objects, because pure darker-yellow looks muddy.

**For Exocortex:** the lesson isn't the specific hex values — it's the principle that **depth colors should be hand-picked, not computed**. CSS `color-mix()` and `darken()` produce colors that are "correct" but often look muddy. Artists handling depth in painting and pixel art shift hue slightly toward warm or cool as they darken. We should remember this when adding any "elevated" state to components: the darker variant may want a small hue shift, not just a luminance drop.

### 4. Zero transitions — the third Phase 3 reference to commit to this

NES.css contains exactly **zero** `transition:` declarations. The only two `@keyframes` rules are `blink` and `wave` — both used for animating sprite characters (a blinking cursor eye, a wave's phase), not for UI state.

This is the same choice as TuiCss and System.css. Three Phase 3 references in a row converging on "instant state changes" as a deliberate philosophy. The NES had instant state changes because the hardware couldn't animate between them. System 1 Mac had instant state changes because 1-bit displays couldn't tween. MS-DOS text mode had instant state changes because character mode couldn't interpolate.

Authentic retro UI = no transitions. Period.

**For Exocortex:** this is the third validation of the `.ds-calm-mode` / `.ds-instant` utility class. We don't want instant transitions as the default — our target is 80-150ms ease-out. But the fact that every retro reference makes this choice reinforces that "instant mode" is a coherent aesthetic position. Users who find motion distracting should be able to turn all animations off and get something that looks like Windows 98 / NES / classic Mac — and that's a recognized design tradition, not a bug.

### 5. The `Press Start 2P` font commitment

NES.css sets `font-family: "Press Start 2P"` on the body and inherits it everywhere. Press Start 2P is Google's bitmap recreation of the NES in-game text font. It's monospaced, uppercase-dominant, and looks crisp only at 16px and multiples of 16px.

At 16px, "Press Start 2P" takes about 4x the horizontal space of a normal monospace font of the same point size. Dashboard content that fits in 80 characters of IBM Plex Mono would fit in 20 characters of Press Start 2P. This is a deliberate accessibility tradeoff — NES games didn't need to show dense data, so NES text is optimized for readability at distance, not density.

**For Exocortex:** not portable. Our panel is dense and Press Start 2P would be painful. But the principle — "font choice is an information density commitment" — is worth noting. We picked IBM Plex Mono for a reason: it hits a specific density/readability balance. Any font change would cascade through the entire layout.

### 6. The SVG border-image for chunky pixel borders

NES.css containers use a `border-image-source` pointing to an inline SVG 5x5 grid. The SVG has filled corner pixels and empty interior pixels, so when used as a 9-slice border at 4px width, it produces a pixelated border that looks drawn with fat pixels:

```css
.nes-container {
  border-style: solid;
  border-width: 4px;
  border-image-source: url('data:image/svg+xml;utf8,...');
  border-image-slice: 2;
  border-image-repeat: stretch;
}
```

The SVG approach is more flexible than 98.css's inset-shadow bevel but requires the SVG asset. It also scales cleanly — a 4px border looks like 4 pixels at any zoom level.

**For Exocortex:** reserved as a technique for any future retro mode. Not directly useful for our main dark dashboard aesthetic (we use thin 1px borders with subtle glows), but if we ever want a "pixel art debug overlay" mode, this is how.

## What ports to Exocortex

1. **The `::after` depth-shadow pattern** as a technique for hover/active states that shouldn't cause layout shift. Most valuable in tables, lists, and dense grids where translating the element would cause rows around it to reflow or feel unstable. Reserved for component-by-component adoption.

2. **Hand-picked depth colors over computed** as a principle. Stored in the reference library notes for future reference when adding elevation states to accent colors.

3. **The convergent retro philosophy: zero transitions is a valid aesthetic**. Third validation of our `.ds-calm-mode` utility. Promote the note from "one possible mode" to "recognized retro tradition" in the ROADMAP.

## What does NOT port

- The Press Start 2P font
- The 8-bit sprite characters drawn in box-shadow
- The chunky SVG border-image
- The specific #209cee/#92cc41/#f7d51d/#e76e55 categorical palette (we have our own state colors)
- The white background
- The 16px-base-size commitment
- The 4px-everything pixel grid
- The zero-transitions default

## Cross-pollination notes

**With 98.css:** Both use "depth shadow" for button state, but via different mechanisms. 98.css uses inset box-shadows ON the button (four layers, colors swap on press). NES.css uses inset box-shadow on a `::after` pseudo-element (one layer, offset shifts on press). 98.css is more authentic to the Windows look; NES.css's pseudo-element approach is more portable because the main element stays stable.

**With System.css:** Both have minimal color vocabulary, zero transitions, and retro authenticity. System.css ships 4 colors total; NES.css ships ~20 (because NES games had a 54-color master palette and individual sprites used subsets). Both commit fully to a single era's constraints.

**With Carbon:** Total opposite. Carbon ships 900+ tokens and treats every state as composable. NES.css ships 0 tokens and hardcodes everything. Both produce coherent interfaces — the difference is flexibility, not quality. Carbon works for IBM's cross-product design system. NES.css works for "I want my page to look like a 1985 NES game."

**With OpenGridWorks:** OpenGridWorks also commits fully to a specific aesthetic (cyberpunk cyan dashboard), but via custom properties and gradients rather than hardcoding. The aesthetic commitment is similar; the implementation is opposite. Both produce their target look.

## Caveats

- The `::after` depth pattern requires `position: relative` on the parent and `position: absolute` on the pseudo-element. Don't use on elements whose positioning context can't be set (inline buttons inside flex containers work fine; absolutely-positioned elements inside transformed containers can get weird).
- The border-image SVG breaks if the CSS is served from a different origin than the page (inline data URIs bypass this, but some CSP configurations block data: URIs in stylesheets).
- Press Start 2P's Google Fonts dependency means NES.css doesn't work offline unless you self-host the font.
- The sprite characters rely on `display: inline-block` and specific `width`/`height` values. If the element's dimensions change, the sprite breaks.

## Extraction methodology used

NES.css is large (308KB) but ~70% is sprite art. The UI vocabulary extracts quickly once you grep past the box-shadow decorative-art positions. Key greps:

1. `.nes-btn::after` — reveals the depth-pseudo-element pattern
2. `.nes-btn.is-primary` / `is-success` / etc. — reveals the categorical palette
3. `border-image-source` — reveals the chunky border SVG approach
4. `@keyframes` — confirms only blink and wave exist
5. `transition:` — confirms zero transitions exist
6. `font-family:` — confirms Press Start 2P commitment

Six greps, full picture of the UI vocabulary. The sprite art is its own category and I deliberately didn't dive into it — it's not portable and there's no pattern to extract beyond "you can draw pictures with box-shadow if you're patient."

**Total extraction time: ~18 minutes.** Slightly longer than 98.css because the sprite noise had to be filtered out.
