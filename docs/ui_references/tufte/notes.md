# Tufte CSS — UI reference notes

**URL:** https://github.com/edwardtufte/tufte-css · https://edwardtufte.github.io/tufte-css/
**Tagline:** "Style your webpage like Edward Tufte's handouts."
**Domain:** Print-aesthetic translated to web. Implements the typographic and layout principles from Edward Tufte's books (*The Visual Display of Quantitative Information*, *Envisioning Information*, *Beautiful Evidence*).
**Tech:** Single CSS file, 9.4KB, 451 lines. No JavaScript. No build step. Drop-in `<link>`.
**Captured:** 2026-04-14
**Why this matters:** Tufte CSS is the **philosophical opposite** of every other reference in our library. It teaches us about calm long-form reading interfaces, sidenote/marginal annotation patterns, and the discipline of minimal color + maximum information density. The least directly portable reference but the most architecturally distinctive.

## The Tufte philosophy

After eight references that mostly converge on "dark theme + cyan accent + glass panels + status pills," Tufte CSS is a complete reset. Its design philosophy is print typography on the web:

- **No animations.** No transitions. No glows. The page doesn't move.
- **No backdrop-filter.** No glass effects. The page is a page.
- **No gradients.** Pure flat color.
- **Five colors total** in the entire library.
- **Generous typography** — body text at 21px with 30px line-height (1.43 ratio), serif font, optical kerning.
- **Bounded reading width** (55%) — long lines of text are hard to read; cap the column.
- **Sidenotes in the right margin** instead of footnotes at the bottom.
- **Old-style numerals** in body text so numbers blend with words.
- **Cream-white background** (#fffff8) instead of pure white — reduced glare.

This is **everything OpenGridWorks isn't**. And it's the right design for a fundamentally different category of content: long-form analytical writing where the words are the point and the chrome should disappear.

## The most important pattern: sidenotes

The Tufte signature is sidenotes that float in the right margin next to the text that references them. They're created entirely with CSS — no JavaScript, no special markup beyond a few class names.

```html
<p>The resolver evaluated this prediction
  <span class="tufte-sidenote-number"></span>
  and could not determine confirmed/falsified from the available evidence.
  <span class="tufte-sidenote">
    The resolver scanned 30 OSS claims, none of which contained
    direct evidence about Brent crude prices.
  </span>
</p>
```

```css
body { counter-reset: sidenote-counter; }
.tufte-sidenote-number { counter-increment: sidenote-counter; }
.tufte-sidenote-number::after {
  content: counter(sidenote-counter);
  vertical-align: super;
  font-size: 0.75em;
}
.tufte-sidenote {
  float: right;
  clear: right;
  margin-right: -60%;
  width: 50%;
}
.tufte-sidenote::before {
  content: counter(sidenote-counter) " ";
  vertical-align: super;
}
```

The CSS counter ties the inline marker to the marginal note automatically. No manual numbering. **This is one of the most clever uses of CSS counters in the wild.**

For Exocortex this is HIGHLY relevant to several future features:

1. **Resolver verdicts with cited claims.** Currently we render cited claims as bullet points below the verdict. Sidenotes would let us inline citation numbers in the verdict text and put the actual claims in the margin — much closer to how analysts actually read evidence.

2. **Hypothesis explanations with provenance.** When the operator brief says "the committee saw 50 new Iran claims," we could inline a sidenote with which specific claim IDs were considered.

3. **Calibration narratives.** When we eventually build a "why did this profile's Brier score change" view, the inline numbers (4 predictions, 2 confirmed, Brier 0.18) could have margin notes explaining each one.

4. **Decision logs.** When we record analyst decisions about predictions, the reasoning can have inline citation markers pointing to the evidence that informed the decision.

**The Tufte sidenote pattern is the right model for any feature where you have a primary claim and supporting evidence, and you want both visible at the same time without the user clicking to expand.**

## Other Tufte patterns worth knowing

### 1. Old-style vs lining numerals

Most fonts ship with **lining numerals** (uniform height, like capital letters: `1234567890`) by default. Tufte uses **old-style numerals** in body text — these have descenders, so the 3, 4, 5, 7, 9 hang below the baseline like lowercase letters do. The result: numbers in prose look like they belong to the words around them, instead of standing out as typographic intrusions.

CSS:
```css
.in-prose  { font-variant-numeric: oldstyle-nums; }   /* numbers in body text */
.in-tables { font-variant-numeric: tabular-nums;  }   /* numbers in data displays */
```

We already use `tabular-nums` for stat displays (from OpenGridWorks). Adding `oldstyle-nums` for any inline numbers in long-form content (e.g., "the resolver scanned 30 claims" should have the 30 in old-style figures) would be a typographic refinement that almost no web framework implements.

**Most important detail:** the choice depends on the font. IBM Plex Mono (our current font) supports `oldstyle-nums` via OpenType features. Most monospace fonts don't bother. Worth a one-line CSS test if we ever want to apply this.

### 2. The newthought pattern

```css
.tufte-newthought {
  font-variant: small-caps;
  font-size: 1.2em;
  letter-spacing: 0.05em;
}
```

A paragraph that begins a new section starts with a few words in small caps. Tufte uses this everywhere. It's lighter than a heading but more meaningful than a paragraph break.

For Exocortex: we could use this in the resolver proposal box. Currently the verdict appears as a pill ("CONFIRMED") above the reasoning text. We could ALSO start the reasoning with `<span class="tufte-newthought">THE COMMITTEE FOUND</span> that...` — gives visual rhythm to LLM-generated content without adding more chrome.

### 3. Reading width constraint

```css
section > p, section > footer, section > table {
  width: 55%;
}
```

Body text is constrained to 55% of the available width. The remaining 45% is reserved for sidenotes. Even on a 4K monitor, body text doesn't span 1500px because long lines are hard to read.

**For Exocortex**: not directly applicable to dashboard UI (we want full-width data displays). But essential for any long-form text view we add. If we build a "full hypothesis lineage essay" or "post-mortem narrative" view, body text should respect this constraint.

### 4. Cream background, not pure white

```css
body { background-color: #fffff8; color: #111; }
```

Tufte uses `#fffff8` (slightly cream) instead of pure white `#ffffff`. The cream tint reduces glare for long reading sessions. Pure white is fatiguing.

**For Exocortex**: we're dark-themed, so this doesn't directly apply. But the principle translates: instead of pure black `#000000`, we use `#060810` (slightly navy) — and this is exactly what every other dark theme reference does too. Tufte's reasoning is the same as ours, just inverted: pure extremes are hard on the eye; nudge slightly off pure to reduce strain.

### 5. The danger color is `red`

```css
.danger { color: red; }
```

That's it. No `#dc3545`, no `var(--ds-signal-negative)`. Just the CSS keyword `red`. Tufte ships almost no color-coded UI — the only accent is for emphasized warnings, and even that uses the most basic possible color value.

**The lesson**: when 99% of your UI is grayscale, even a tiny touch of color screams. You don't need a sophisticated palette when the contrast itself is the signal.

For Exocortex: the opposite is true (we have many status colors because we have many concurrent states to communicate). But the principle is worth knowing — color discipline matters more than color quantity.

### 6. Italicized headings

```css
h2 { font-style: italic; }
h3 { font-style: italic; }
.subtitle { font-style: italic; }
```

Tufte uses italics for h2, h3, and subtitles. The h1 is upright. This creates visual rhythm between section levels — the eye distinguishes "main heading" (upright) from "subheading" (italic) without needing different sizes alone.

**For Exocortex**: not directly portable (we don't have prose headings). But the principle is worth knowing: typography weight and style can carry hierarchy as effectively as size, sometimes more cleanly.

### 7. Generous leading

Body text is `font-size: 1.4rem` (~21px) with `line-height: 2rem` (~30px). That's a 1.43 line-height ratio — generous for comfortable reading. Most modern sites use 1.5 or 1.6; Tufte goes slightly tighter but with bigger absolute size.

The lesson: leading is not a single ratio that fits all use cases. Long-form reading wants generous leading. Dense data displays want tighter leading. Adjust per context.

### 8. CSS counters for auto-numbering

The sidenote counter pattern is brilliant because it's **invisible until you need it**. The CSS counter increments automatically as the user reads, producing perfect numbering without any manual coordination.

This pattern generalizes beyond sidenotes. Any time you have a sequence of inline references that should be numbered, CSS counters can do the work:

```css
.cited-claim { counter-increment: claim-counter; }
.cited-claim::before { content: "[" counter(claim-counter) "] "; }
```

For Exocortex: when we render cited claims in resolver verdicts, the [1] [2] [3] markers could be CSS counters instead of hand-numbered. The data has the claim IDs; the visual markers are derived.

## What ports to Exocortex

Tufte CSS is the LEAST directly portable reference in our library. None of its visual values translate to our dashboard aesthetic. But several of its **principles and patterns** are valuable for future work:

1. **The sidenote pattern** — vendored as `.tufte-sidenote-host`, `.tufte-sidenote-number`, `.tufte-sidenote` in `exocortex.css` for any future feature that displays primary content + supporting evidence simultaneously.

2. **Old-style vs lining numerals** — documented as a typographic refinement. `font-variant-numeric: oldstyle-nums` for inline numbers in body text; `tabular-nums` (already in use) for tables.

3. **The `.tufte-newthought` small-caps pattern** — vendored for use in long-form LLM-generated content where natural section breaks need to be marked without explicit headings.

4. **The reading-column constraint** — `--ds-reading-width: 65ch` reserved as a token. For any future long-form text view, body text should be capped at ~60-70 characters per line.

5. **The CSS counter pattern for citations** — documented as the right model when we render inline references with auto-numbered markers.

6. **The "calm mode" philosophy** — documented as a guideline. For any future view where long-form reading is the goal (analyst notes, post-mortem narratives), disable transitions and animations on the content area. Tufte's `.ds-tufte-calm` mental model: the content is the visual signal; the chrome should disappear.

## What does NOT port

- **The cream-white background.** We're dark-themed.
- **The serif body font.** We use IBM Plex Mono. Serif fonts feel out of place in a technical dashboard.
- **The italicized headings.** We don't have prose headings.
- **The figure/figcaption pattern.** We don't have figures.
- **The mobile checkbox-toggle for sidenotes.** We don't target mobile.
- **The 55% global reading width constraint.** Dashboards want full-width data displays.
- **ET Book font.** Not free for all uses; renders poorly at small sizes on dark backgrounds.
- **The minimal 5-color palette applied to everything.** We need more colors to distinguish states.
- **Italic blockquotes with right-aligned citations** (the epigraph pattern). We don't have epigraphs in dashboard UI.

## Cross-pollination notes

**With OpenGridWorks**: Tufte is the philosophical opposite. OpenGridWorks is dense radar-screen UI with motion and glow; Tufte is calm long-form reading. Both are valid for their contexts. The lesson from having both in the library: **information density and calm reading are not opposites — they're different modes for different content types**. A dashboard panel can have both: dense radar-screen state at the top (OpenGridWorks aesthetic), long-form analyst notes at the bottom (Tufte aesthetic).

**With TuiCss**: Both Tufte and TuiCss have zero animations. But the philosophies are completely different:
- TuiCss's no-animation principle is "state is binary, snap to it instantly"
- Tufte's no-animation principle is "the content is the signal, don't compete with it"

Both arrive at the same CSS (`transition: none`) for opposite reasons. Worth knowing because it shows that the same technique can serve different design philosophies.

**With Carbon's AI tokens**: Tufte's sidenote pattern would be the perfect way to render AI-generated reasoning with inline citations. Imagine a resolver proposal that says "the committee found significant evidence [1] [2] [3]" with the actual cited claims appearing in the margin. The AI-content treatment would mark the resolver's text as LLM-generated; the sidenote pattern would put its evidence right next to its claims. **The two patterns are complementary and would compose beautifully.**

## Caveats

- Tufte CSS targets desktop reading. The mobile responsive code (`@media (max-width: 760px)`) is a fallback that hides sidenotes and adds a tap-to-toggle pattern. We don't target mobile, so we can ignore this.
- The ET Book font is a custom embed. It's not on Google Fonts. It's licensed for free non-commercial use only. We use Palatino as the fallback, which is on most systems.
- The CSS uses `rem` units throughout. The root `font-size: 15px` means `1rem = 15px`. Conversions in our notes: `1.4rem ≈ 21px`, `2rem ≈ 30px`, `3.2rem ≈ 48px`.
- Tufte's `.danger` class uses just `red`. This is a single-color override, not a system. Don't read it as "Tufte recommends `red` as a danger color name" — it's just an example of how to add minimal accent colors when needed.
- The figcaption float-right pattern requires the parent figure to have a constrained width (`max-width: 55%`). If the figure spans full width, the caption can't float into the margin because there is no margin. Tufte handles this with `.fullwidth` classes that disable the constraint.

## Extraction methodology used

Tufte CSS is the smallest extraction so far — 451 lines, single file. Methodology:

1. Found the canonical source at `github.com/edwardtufte/tufte-css`
2. Fetched `tufte.css` from the gh-pages branch (the published version)
3. Read the entire file linearly — short enough to do in one pass
4. Identified the distinctive patterns (sidenote counter, old-style numerals, reading width, newthought, minimal palette)
5. Cross-referenced against Tufte's books to understand the philosophical principles behind the CSS choices
6. Compared to the other 8 references in our library to identify what's UNIQUELY Tufte

**Total extraction time:** ~25 minutes. Faster than any production design system because the file is small and the patterns are concentrated. The bulk of the time was thinking about how each pattern would translate to a dark-theme dashboard context (most don't) and which ones to graduate (a small but high-value subset).

The unusual finding: **the value of Tufte CSS is not in CSS values at all.** It's in the philosophy and the few signature patterns (sidenote counter, newthought, old-style numerals). Most production design systems offer rich token libraries; Tufte offers a worldview. Different kinds of value, both worth having in a reference library.
