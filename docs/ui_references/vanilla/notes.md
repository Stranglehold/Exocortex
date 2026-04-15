# Vanilla Framework (Canonical) — UI reference notes

**URL:** https://github.com/canonical/vanilla-framework · https://vanillaframework.io/
**Tagline:** "From community websites to web applications, this CSS framework will help you achieve a consistent look and feel."
**Domain:** Canonical's official design system. Powers ubuntu.com, snapcraft.io, charmhub.io, MAAS web UI, Juju Dashboard, Landscape, Cube, OpenStack Horizon (via Cube), and most Canonical-built operations dashboards.
**Tech:** SCSS source plus W3C Design Tokens Format Module JSON files (`tokens/color/dark/*.json`). Tokens compiled to CSS via Style Dictionary. The W3C standard format is the distinctive choice — most other systems use vendor-specific source formats.
**Captured:** 2026-04-14
**Why this matters:** Smallest of the four production design systems we've extracted, but with its own opinionated philosophy. Notable for being the only one that uses the W3C Design Tokens standard, which makes it the most portable across tools.

## What's distinctively Vanilla

After three other production design systems, I expected Vanilla to mostly confirm what we already knew. It surprised me with several genuinely new patterns.

### 1. W3C Design Tokens Format Module compliance

Vanilla is the only reference in our library that uses the **official W3C standard** for design token files:

```json
{
  "$type": "color",
  "color": {
    "background": {
      "default": {
        "themeable": true,
        "$value": "#262626"
      }
    }
  }
}
```

The `$type` and `$value` syntax is W3C standard. Reference syntax uses dot-paths: `{color.text.link.default}`. This format is consumed by Figma plugins, Tokens Studio, design-token build tools, and any other system that supports the standard.

**The lesson is portability.** Carbon's tokens are JS, PatternFly's are SCSS, Primer's are JSON5 (a superset of JSON), and Vanilla's are W3C JSON. Vanilla's choice means designers using Tokens Studio or Figma can import Vanilla tokens directly without anyone writing a custom parser. The other systems require platform-specific tooling.

For Exocortex: we don't have a token build pipeline at all (we hand-write CSS). But if we ever want to share tokens between code and design tools, **the W3C format is the right choice** — it's the only format with cross-tool support.

### 2. The `themeable` metadata field

Every Vanilla token has an explicit `themeable: true|false` annotation:

```json
{
  "background.default": {
    "themeable": true,
    "$value": "#262626"
  }
}
```

This declares whether the token can be customized per-theme. Most Vanilla tokens are themeable, which makes sense given that Canonical builds custom themes for each Ubuntu sub-product (snapcraft.io has a different palette than charmhub.io, both built on Vanilla).

**The metadata is the lesson.** Other token systems implicitly allow theme overrides on every token. Vanilla makes it explicit. **A non-themeable token is one the design system OWNS** — you should not override it because it's part of the framework's identity. Examples might be `--color-brand-canonical-logo` or `--color-base-positive` (the desaturated green that is part of Vanilla's visual signature).

For Exocortex: we don't have multiple themes today, but if we ever add one (deep retro mode, high contrast mode, performance mode), having explicit `themeable` metadata would prevent accidental overrides of identity-bearing tokens. **Reserved as a documentation pattern**, not vendored as actual code.

### 3. Status vocabulary: positive/negative/caution/information

The other production systems use **success / danger / warning / info**. Vanilla uses **positive / negative / caution / information**:

| Standard | Vanilla |
|---|---|
| success | positive |
| danger  | negative |
| warning | caution |
| info    | information |

The naming choice emphasizes **valence** rather than **action**. "Negative" doesn't necessarily mean something bad happened that the user did — it could just mean a value went down or a result was unfavorable. "Caution" is softer than "warning" — it implies "be aware" rather than "stop and pay attention."

**This is more flexible vocabulary for monitoring contexts.** Imagine a swarmfish prediction with consensus_confidence dropping over time. It's not "danger" (no error occurred) and it's not exactly "warning" (nothing wrong) — it's "negative" (the value moved in an unfavorable direction). Vanilla's vocabulary lets you express that distinction.

For Exocortex: our existing vocabulary (positive/negative/warning/info via OpenGridWorks signal colors) is already close to Vanilla's. The mapping is essentially a rename — "warning" → "caution" might be slightly more honest. Documented but not vendored as a rename (would be churn for marginal gain).

### 4. Tinted borders — softer status border variants

Vanilla has a separate `border.tinted.*` namespace for desaturated status borders:

```css
--color-border-positive:        #62A36C;     /* full saturation */
--color-border-tinted-positive: #62a36c;     /* desaturated, softer */
```

Wait — the values are nearly identical here because Vanilla's base colors are ALREADY desaturated. The tinted variants are slightly different shades for borders specifically.

The pattern matters more than the values: **two intensity levels for borders**. Use the full saturation when the border needs to grab attention (alert boxes, error states). Use the tinted variant when the border needs to communicate status without dominating (inline status indicators, subtle dividers between sections).

This is similar to Primer's intensity triplet but applied specifically to borders. Vanilla doesn't extend it to backgrounds or text — only borders get the tinted treatment.

For Exocortex: minor refinement. Reserved as `--ds-border-tinted-{positive,negative,warning,info}` if we ever need softer status borders.

### 5. Status backgrounds with explicit alpha progression

```css
--color-background-positive-default: rgba(10, 189, 37, 0.20);   /* 20% alpha */
--color-background-positive-hover:   rgba(0, 199, 30, 0.30);    /* 30% alpha */
--color-background-positive-active:  rgba(0, 199, 30, 0.36);    /* 36% alpha */
```

Three states (default/hover/active) with explicit alpha values: 20% → 30% → 36%. Each interactive state gets a slightly more opaque background. The 16-percentage-point progression is visible but not jarring.

Compare to PatternFly which uses three discrete RGBA values (also alpha-based but inconsistent step sizes). Vanilla's progression is more disciplined: each step is exactly 10pp from the previous (default→hover) and exactly 6pp (hover→active).

For Exocortex: our hover backgrounds use mostly 15% alpha. Vanilla suggests we should have **explicit progressions** (default → hover → active) using consistent alpha steps. Small refinement worth knowing.

### 6. text.muted vs text.inactive — two different "less prominent" states

```css
--color-text-default:   #ffffff;
--color-text-muted:     rgba(255, 255, 255, 0.6);    /* secondary content */
--color-text-inactive:  rgba(255, 255, 255, 0.75);   /* dormant element */
```

Vanilla distinguishes **three** less-prominent text states (most systems have two: default and secondary).

The muted/inactive distinction is subtle but principled:
- **Muted** content is **intentionally de-emphasized** — helper text, captions, metadata, the kind of content you write small on purpose
- **Inactive** content is **currently dormant but should remain readable** — an unselected tab, a closed accordion header, a button that's still informative even when not the active focus

The visual difference: inactive (75%) is brighter than muted (60%). A user can read inactive text comfortably; muted text requires more effort.

For Exocortex: we currently use `--ds-text-tertiary` for both purposes. Vanilla suggests we should distinguish them. **Reserved as `--ds-text-inactive: rgba(255,255,255,0.75)`** for elements that are dormant but should remain readable (unselected tabs, closed expansions). Currently unused but available.

### 7. Special-purpose backgrounds — input, code, tooltip

```css
--color-background-input:    rgba(255, 255, 255, 0.04);   /* form inputs */
--color-background-code:     rgba(255, 255, 255, 0.03);   /* inline code */
--color-background-tooltip:  #111111;                     /* tooltips */
```

Each is a recurring UI pattern with distinct contrast needs:
- **Input backgrounds** need to look subtly recessed compared to the surrounding surface (form fields invite text input)
- **Code backgrounds** need to be very subtle — code is often inline and shouldn't dominate
- **Tooltip backgrounds** need to be very dark (much darker than the page background) so they look like floating overlays distinct from main content

PatternFly has the form field tokens; Carbon has the field tokens. Vanilla adds **tooltip and code** as their own categories. We don't have either yet (no tooltips, no code blocks) but the lesson is the same: **any UI pattern that has its own design constraint deserves its own token**.

### 8. Brand tokens built into the design system

```css
--color-brand-ubuntu:           #e95420;     /* Ubuntu orange */
--color-background-canonical-logo: #E95420;  /* same color, different role */
--color-brand-accent:           #70bbc2;     /* Vanilla's secondary brand */
```

Vanilla treats brand identity as **first-class tokens within the design system**. The Ubuntu orange isn't hardcoded in component files — it's in the token library, available for any component to reference.

This matters because brand colors evolve. Ubuntu has redesigned its orange several times in the last decade. By centralizing brand colors in tokens, components that use Ubuntu orange automatically pick up the new shade when the brand updates.

For Exocortex: we don't currently have a brand identity (no logo, no signature color beyond the cyan accent). **If we ever add an Exocortex visual mark or wordmark, it should live in the token system** as `--ds-brand-exocortex` or similar — not hardcoded in the panel HTML.

### 9. Range-specific disabled opacity

```css
--opacity-disabled-default: 0.33;     /* 33% — most disabled elements */
--opacity-disabled-range:   0.5;      /* 50% — slider/range inputs */
```

Vanilla has TWO disabled-state opacity values. Most disabled elements use 33%. Range inputs (sliders) use 50% because the track and thumb need to remain visible enough to communicate value position even when disabled.

This is a tiny detail but **principled**. Most systems use a single disabled opacity for everything. Vanilla acknowledges that range inputs are a special case.

For Exocortex: we don't have sliders. But the lesson is broader: **when an element class has different visibility needs in the disabled state, it deserves its own opacity token**. Future application: if we add a confidence slider for hypothesis filtering, it should use a higher disabled opacity than buttons.

### 10. Lighter base dark theme — Canonical's contrast philosophy

Vanilla's "dark" theme has `#262626` as its base background. Compare:
- **Vanilla dark**: `#262626` (15% lightness)
- **Carbon g100**: `#161616` (8% lightness)
- **Primer dark**: `#0d1117` (~6% lightness)
- **Exocortex (us)**: `#060810` (~4% lightness)

**Vanilla is by far the lightest dark theme.** Canonical's preference is for less-extreme contrast — closer to what other systems call "dimmed dark mode."

The reason: Vanilla powers Canonical's web properties, which are documentation-heavy. Long-form reading is fatiguing on pure-black backgrounds. The slightly-lighter `#262626` is more comfortable for extended reading.

For Exocortex: our `#060810` is the deepest dark of any reference we've extracted. That's the right call for a dashboard (data should pop against the background) but worth knowing that documentation-heavy interfaces lean lighter. **If we ever add a long-form reading view (e.g., for hypothesis lineage or analyst notes), it might benefit from a lighter background.**

## What ports to Exocortex

1. **`themeable` metadata pattern documented** — not vendored as code, but added to the `exocortex.css` notes. When we eventually add multi-theme support, marking certain tokens as non-themeable (the brand identity) prevents accidental overrides.

2. **`--ds-text-inactive`** — for dormant-but-readable elements (unselected tabs, closed expansions). 75% opacity, brighter than `--ds-text-tertiary`. Available for application when we have a use case.

3. **Tinted border namespace reserved** — `--ds-border-tinted-{positive,negative,warning,info}` documented in the curated stylesheet but not vendored. Available for future application when we need softer status borders.

4. **Explicit alpha progression for status backgrounds documented** — current ad-hoc 15% alpha values should ideally become a disciplined 20%/30%/36% progression for default/hover/active. Documented in `exocortex.css` notes; not yet applied because it would be churn.

5. **Brand token reservation** — `--ds-brand-exocortex` reserved namespace for any future Exocortex visual identity.

6. **Range-specific disabled opacity reserved** — documented as a pattern. Not applicable today (no sliders) but good to know.

## What does NOT port

- **The full W3C Design Tokens Format JSON source**. We hand-write CSS; no build pipeline. Adopting W3C JSON would require a build step.
- **Vanilla's positive/negative/caution/information vocabulary**. Slightly more flexible than success/danger/warning/info but the rename would be churn for marginal gain. We keep our current vocabulary.
- **The lighter `#262626` base background**. Our intelligence-console aesthetic benefits from the deeper `#060810`. Vanilla's preference for less-extreme contrast doesn't suit our domain.
- **The Ubuntu orange and Canonical brand identity**. We have our own visual direction.
- **Vanilla's full Style Dictionary build pipeline**. Same reasoning as Primer/PatternFly/Carbon — premature abstraction at our scale.
- **The `text.button.{brand,default,base,positive,negative}` nested component tokens**. We already have `--ds-text-on-{accent,positive,negative,warning,info}` from Primer, which serves the same purpose with simpler naming.

## Cross-pollination notes

**With other production systems:** Vanilla is the smallest of the four production systems we've extracted, but it's the only one with W3C standard compliance. The trade-off is structure flexibility vs portability — the others have richer hierarchies but require custom tooling.

**With our existing system:** Vanilla's text.muted vs text.inactive distinction is a small but principled refinement we should adopt. The brand token reservation is a forward-compatibility move worth documenting. Everything else is reinforcement of patterns we already have.

**Phase 2 synthesis:** After four production design systems, the patterns have converged. Each contributed something distinctive:

| Reference | Distinctive contribution |
|---|---|
| Primer | Intensity triplet (default/muted/emphasis), text-on-emphasis, role-based shadows |
| PatternFly | Interaction state triplet (default/hover/clicked), status vs nonstatus, chart layer concept |
| Carbon | AI tokens, caution-undefined for "I don't know yet", helper text token |
| Vanilla | W3C standard format, themeable metadata, text.muted vs text.inactive, range-specific opacity |

**No further production design systems would offer dramatically new patterns.** The major architectural axes have all been mapped:
- Intensity (default/muted/emphasis) ✓
- Interaction state (default/hover/clicked) ✓
- Surface elevation (primary/secondary/tertiary or layer-NN) ✓
- Status vs categorical partition ✓
- Theme switching mechanisms (per-file vs build-overlay) ✓
- Component-specific vs global tokens ✓
- AI content provenance ✓
- Token portability (W3C standard) ✓
- Per-element opacity exceptions ✓

**Phase 2 is complete.** The reference library now has a comprehensive design vocabulary spanning four production-validated systems plus four aesthetic-distinctive systems. We can articulate any UI design decision in concrete terms.

## Caveats

- Vanilla's source is W3C Design Tokens JSON. The values I extracted are from the source files (not compiled CSS). The build pipeline generates kebab-case CSS variables (`--color-background-default`) from the dot-path JSON keys (`color.background.default`).
- Vanilla has a `tokens/color/light/` directory with the light theme variants. I didn't extract those — Exocortex is dark-only.
- Vanilla also has SCSS source files (`scss/`) that compile to CSS via the build pipeline. Those define component styles that consume the tokens. I didn't extract component code — only the token layer.
- The `themeable` field is metadata for build tools. It doesn't affect the compiled CSS output — both themeable and non-themeable tokens become regular CSS variables. The distinction matters for design tool integrations and theme generators.
- Canonical's brand orange (#e95420) is the famous Ubuntu Aubergine-and-orange palette. The orange is uniquely Canonical's — even other Linux distributions don't use it.

## Extraction methodology used

Vanilla took ~30 minutes — the smallest extraction of any production design system. This was because:

1. **The W3C JSON format is easier to parse** — each file has a clean nested structure that maps directly to design token paths
2. **Vanilla is smaller in scope** — fewer total tokens than Primer, PatternFly, or Carbon
3. **The file organization is purpose-specific** — `tokens/color/dark/{background,base,border,brand,code,icon,link,text}.json` is self-explanatory; I didn't have to read group-definition files to understand the taxonomy

Methodology:
1. Found the canonical source at `github.com/canonical/vanilla-framework`
2. Identified the token files in `tokens/color/dark/`
3. Fetched all 8 files via curl
4. Read each file in order: base → background → border → text → icon → brand → code → link
5. Compared each category to the equivalent in the other three production systems
6. Identified four genuinely new patterns (W3C format, themeable metadata, text.inactive distinction, range-specific opacity)
7. Reserved patterns documented for future use; nothing graduated as code (Vanilla's value-set is too different from ours to vendor directly)

**The pattern: Phase 2 reference extraction times have averaged ~45 minutes** with Vanilla as the smallest at ~30. Production design systems take roughly the same time regardless of size because most of the time is spent understanding architectural intent, not enumerating values.
