# PatternFly (Red Hat) — UI reference notes

**URL:** https://github.com/patternfly/patternfly · https://www.patternfly.org/
**Tagline:** "An open source design system."
**Domain:** Red Hat's enterprise design system. Powers OpenShift, Ansible Automation Platform, Quay container registry, Foreman/Satellite, RHEL Insights, ACM, Operator Lifecycle Manager — basically every Red Hat operations product.
**Tech:** SCSS source files compiled to CSS via Style Dictionary. Tokens shipped as `--pf-t--*` custom properties. Multiple theme files (default/dark/highcontrast/glass) per variant.
**Captured:** 2026-04-14
**Why this matters:** Domain match. PatternFly is built for **monitoring/operations dashboards** — exactly what Exocortex is. The patterns it uses are validated by years of operator-facing UI on enterprise infrastructure products.

## The two-axis insight

The single most important insight from comparing PatternFly to Primer:

**Primer and PatternFly take orthogonal axes for organizing color tokens.**

| Axis | Primer | PatternFly |
|---|---|---|
| **Intensity** | `default` / `muted` / `emphasis` | (not explicit) |
| **Interaction state** | (limited) | `default` / `hover` / `clicked` |
| **Categorical vs semantic** | Aliased separately | `status--*` vs `nonstatus--*` |
| **Surface elevation** | Flat (default/muted/inset/inverse) | `primary` / `secondary` / `tertiary` + `floating` + `sticky` |
| **Naming style** | `--bgColor-success-emphasis` (camelCase + dash) | `--pf-t--global--background--color--status--success--default` (deep hierarchy) |

**A complete design system has BOTH axes.** Intensity (Primer) + Interaction state (PatternFly). For example, a button might want all of:

- `--ds-signal-positive-default-rest` (default state, default intensity)
- `--ds-signal-positive-default-hover` (default intensity, hovered)
- `--ds-signal-positive-default-clicked` (default intensity, pressed)
- `--ds-signal-positive-emphasis-rest` (saturated emphasis, default state)
- `--ds-signal-positive-emphasis-hover` (saturated, hovered)
- `--ds-signal-positive-emphasis-clicked` (saturated, pressed)

That's 2 intensities × 3 states = 6 variants per category × 4 categories = 24 tokens. PatternFly does this at scale (45+ status tokens across 5 categories). We can adopt a subset where it matters most: the buttons that drive the most action (Sprint, Predict, Run Cycle Now, Resume).

## What's distinctly PatternFly (worth stealing)

### 1. Status vs Nonstatus distinction

PatternFly explicitly partitions colors into two semantic classes:

```css
--pf-t--global--color--status--success--default     /* MEANINGFUL: success = "good thing" */
--pf-t--global--color--nonstatus--blue--100         /* CATEGORICAL: blue = "blue, no meaning" */
```

The rule encoded at the token level: **don't use status colors for decorative purposes**. If you need a blue label for visual variety, use `nonstatus--blue`, not `status--info`. This prevents the common bug where someone uses "info blue" for a label that has nothing to do with information state, then later wonders why their info messages don't stand out.

For Exocortex: we currently use `--ds-signal-info` (cyan/blue) for any neutral information state. We don't have nonstatus colors — every color in our system carries semantic weight. **If we ever add categorical colors** (e.g., for charts where each topic gets a distinct hue), we should explicitly namespace them as `--ds-categorical-*` or `--ds-nonstatus-*` to prevent confusion.

### 2. Three-level surface hierarchy (primary/secondary/tertiary)

PatternFly distinguishes three levels of content elevation on the same page:

| Token | Use for |
|---|---|
| `primary--default` | Main content area, top-level cards |
| `secondary--default` | Nested cards, sidebars |
| `tertiary--default` | Deeply nested content, inset blocks |

Plus separate categories for `floating` (popovers, menus) and `sticky` (sticky headers). **These are different concepts.** Tertiary is "card on a card on a page." Floating is "menu that pops out and disappears." They look similar visually but have different layout semantics.

For Exocortex: we currently have `--ds-surface-{void,base,raised,overlay,scrim}`. The OpenGridWorks names are good but they describe DEPTH (void → scrim) rather than ROLE (primary → tertiary). PatternFly's role-based names communicate intent better. **Hybrid approach**: keep the void/base/raised/overlay names for the depth scale, ADD primary/secondary/tertiary aliases for the role meaning.

### 3. Skeleton loading tokens

```css
--pf-t--global--background--color--loading--skeleton--default
--pf-t--global--background--color--loading--skeleton--subtle
```

Two shades for skeleton-loader placeholders. We don't have skeleton loaders in Exocortex, but if/when we add them (say, for the Pending tab while predictions load), having dedicated tokens prevents inconsistency. **The lesson is broader: any UI pattern that recurs gets its own token.** Striped table rows, sticky headers, modal backdrops, skeleton loaders, focus rings — each one is a token in PatternFly because each one has its own design constraint.

### 4. Backdrop and striped row tokens

```css
--pf-t--global--background--color--backdrop--default        /* modal scrim */
--pf-t--global--background--color--striped--row--default    /* alternating table rows */
```

Modal backdrops and striped table rows are two of the most consistently-styled UI elements that often get re-invented per-component. PatternFly prevents drift by giving each its own token. **For Exocortex**: we don't have modals yet but the resolver proposal might benefit from being a modal in the future. We do have lots of tables (claims, sources, sessions, hypotheses, calibration). Adding `--ds-bgColor-row-striped` and using it consistently would be cheap and prevent drift.

### 5. Status state triplet (default/hover/clicked)

PatternFly's most distinctive contribution. Every interactive element with a status semantic gets THREE state variants:

```css
--pf-t--global--color--status--success--default
--pf-t--global--color--status--success--hover
--pf-t--global--color--status--success--clicked
```

Same for borders. Same for backgrounds. Same for all five status categories (success/danger/warning/info/custom).

For Exocortex: this is where we're weakest. Our buttons currently change color on hover but don't have a distinct "clicked" state. The OpenGridWorks scale-down trick (`transform: scale(0.97)` on `:active`) handles physical feedback but not color feedback. PatternFly suggests adding `--ds-state-{confirmed,falsified,pending}-{rest,hover,clicked}` triplets so buttons can have three distinct color appearances per interaction state.

### 6. Read/Unread/Attention tokens

```css
--pf-t--global--color--status--read--on-primary
--pf-t--global--color--status--read--on-secondary
--pf-t--global--color--status--unread--default
--pf-t--global--color--status--unread--attention--default
--pf-t--global--color--status--unread--attention--clicked
```

Notification state has its own dedicated token system, including "unread + needs attention" as a distinct level beyond just "unread." This is the level of UI specificity enterprise dashboards demand. **For Exocortex**: when we add the resolution-pending notification system to surface "the resolver has proposed verdicts you should review", these read/unread/attention tokens are the right model.

### 7. Glass as a theme overlay (third glass approach)

We now have THREE references for glass effects in our reference library:

| Approach | Source | Mechanism |
|---|---|---|
| **Modern blur** | OpenGridWorks | `backdrop-filter: blur(20px) saturate(140%)` hardcoded |
| **Period gradient** | 7.css | Stacked CSS gradients, no `backdrop-filter` |
| **Theme-token blur** | PatternFly | `backdrop-filter: var(--ds-glass-blur)` where `--ds-glass-blur` is a theme token |

PatternFly's approach is the most flexible. The blur amount is a CSS variable, so:
- The default theme can have `--blur: initial` (no glass)
- The glass theme has `--blur: blur(16px)` (16px blur)
- Components reference `var(--blur)` and never know which theme is active

**For Exocortex**: we currently hardcode `backdrop-filter: blur(20px) saturate(140%)`. We should make the blur amount a token (`--ds-glass-blur-amount: 20px`) so future themes can adjust it. Better still: make the entire glass background a theme token so a "high-performance mode" theme could disable backdrop-filter entirely by setting it to `none`.

### 8. Charts as a separate token layer

PatternFly ships a SEPARATE token file for charts (`tokens-charts-dark.scss`). Chart tokens cover:
- Stroke widths (`xs/sm/lg`) — different from UI border widths
- Font sizes (`xs/sm/lg/2xl`) — smaller than UI text sizes by default
- Layout dimensions (default chart width/height/padding)
- Categorical color palette (8 hues × 5 intensities = 40 chart-specific colors)
- Sequential color scales for heat maps and progression visualization
- Chart-specific status colors (note: chart success uses BLUE not green — green-on-dark charts have legibility issues)

**Critical insight: charts have different design constraints than UI.** Chart fonts need to be smaller because they sit inside data marks. Chart strokes need consistent widths so two lines of the same series read as related. Chart status colors might need to differ from UI status colors for accessibility reasons.

For Exocortex: when we eventually build the calibration trend chart or hypothesis lifecycle visualization, we should NOT just reuse `--ds-signal-positive` and `--ds-text-md`. We should add a chart-specific token layer (`--ds-chart-color-positive`, `--ds-chart-stroke-sm`, `--ds-chart-text-sm`) so chart design can evolve independently from UI design.

### 9. Directional shadows

PatternFly splits each shadow size into TWO variants:

```css
--pf-t--global--box-shadow--color--md--default      /* ambient — light from above */
--pf-t--global--box-shadow--color--md--directional  /* directional — light from a specific angle */
```

The directional variant is for elements that imply they're lit from a specific direction (top-left, usually). Useful for creating depth hierarchy where you want some elements to "lean" toward the light source.

This is a different mental model than Primer's role-based shadows. Primer answers "what's this element doing?" PatternFly answers "where is the light coming from?"

For Exocortex: we don't have directional shadows. Adding them is a polish move — it makes the UI feel more physically coherent (everything appears lit from the same direction). Low priority but worth knowing about.

## What ports to Exocortex

I'm graduating the **architectural patterns** plus a few specific tokens. The PatternFly values themselves don't directly apply (their accent is Red Hat blue/red, ours is cyan; their surfaces are gray, ours are navy).

1. **Status state triplet** — add `--ds-state-{confirmed,falsified,pending,still-pending}-{rest,hover,clicked}` for the buttons that drive the most action. Default/hover/clicked on top of the existing triplet pattern from Primer means we now have intensity × interaction state, fully populated.

2. **Surface role aliases** — add `--ds-surface-primary`, `--ds-surface-secondary`, `--ds-surface-tertiary` as aliases for our existing depth-named surfaces. Both naming schemes coexist. New code uses role names; existing code keeps using depth names.

3. **Striped row token** — `--ds-bgColor-row-striped` for use in tables. Not yet applied (we don't have striped tables) but available.

4. **Skeleton loader tokens** — `--ds-bgColor-skeleton`, `--ds-bgColor-skeleton-subtle`. Available for when we add skeleton loaders to the Pending and Hypotheses tabs.

5. **Backdrop scrim token** — `--ds-bgColor-backdrop` for modal scrims. Available for when we add modals.

6. **Glass blur as a theme token** — replace hardcoded `backdrop-filter: blur(20px) saturate(140%)` with `backdrop-filter: var(--ds-glass-blur)` where `--ds-glass-blur` is a token. Default theme: `blur(20px) saturate(140%)`. Future "performance mode" theme can override to `none`.

7. **Status vs nonstatus namespacing convention** — documented in `exocortex.css` notes. We don't have nonstatus colors yet, but the convention is reserved as `--ds-categorical-*` for any future categorical color additions.

8. **Chart token layer reservation** — documented in `exocortex.css`. When we build charts, add `--ds-chart-*` tokens rather than reusing UI tokens.

## What does NOT port

- **The deep hierarchical naming convention** (`--pf-t--global--background--color--status--success--default`). It's extremely explicit but extremely verbose. Our tokens average 4 segments; PatternFly averages 7. The verbosity slows down both reading and writing CSS. Our existing convention (`--ds-bgColor-success-emphasis`) compromises by using camelCase to compress segments while preserving hierarchy.
- **The 136 nonstatus tokens** (8 hues × multiple intensities × multiple properties). We don't have a use case for that many categorical colors yet. Reserved as a pattern; not vendored.
- **All 125 status tokens** with full property × state × category × intensity matrix. We'll graduate a subset (2 categories × 3 states × 1 property = 6 new tokens) where it matters most.
- **The 173-line chart token file**. Reserved as a pattern; will graduate when we actually build charts.
- **High contrast theme variants**. Same reasoning as Primer — single dark theme is enough for now, accessibility variants can be added single-purpose if/when needed.
- **Style Dictionary build pipeline**. Same reasoning as Primer — one builder, no build pipeline.
- **Red Hat accent palette** (red/blue/yellow). Our cyan accent fits the intelligence-console aesthetic better.
- **Directional shadows**. Polish move with limited value at our scale. Reserved.

## Cross-pollination with the rest of the library

This extraction unifies what we learned from the previous four references:

- **OpenGridWorks** gave us fast-transition fluidity, glass via backdrop-filter, signal/accent palette, scale-on-hover feedback
- **TuiCss** gave us instantaneous-state philosophy for truth-bearing indicators, hard drop shadows, the CGA palette
- **Open Props** gave us animation presets, easing library, layer scale, aspect ratios
- **7.css** gave us asymmetric hover transitions, default-button pulse, layered-gradient glass alternative, hard-stop gradients
- **Primer** gave us the intensity triplet, semantic state aliases, text-on-emphasis pattern, role-based shadows
- **PatternFly** gives us the interaction state triplet, status vs nonstatus distinction, surface role hierarchy, chart token layer concept, glass-as-theme-token

Each reference filled a gap the others left. Together they form a much more complete design vocabulary than any single reference could.

The biggest synthesis: **a complete design system has TWO orthogonal axes for color tokens — intensity (Primer) AND interaction state (PatternFly)**. Most systems pick one and accept the limitations of the other. We can have both.

## Caveats

- PatternFly's source is SCSS with a Style Dictionary build pipeline. The compiled CSS files I extracted from are generated artifacts. If we ever want to track upstream changes, the source of truth is the JSON5 files in `src/patternfly/base/tokens/`.
- The dark theme file is `tokens-dark.scss` but the actual theme switching uses CSS classes/data attributes that PatternFly applies at the document level. The `[data-theme]` selector I used in `tokens.css` is illustrative — actual PatternFly uses different class names.
- The `--pf-t--global--*` namespace is for "globally available" tokens. There's also `--pf-t--c--*` for component-local tokens (which I didn't extract — there are too many). Components consume globals; if they need a custom value, they define a local that overrides.
- The 173-line chart tokens file uses `--pf-t--chart--*` (different prefix). They explicitly DO NOT share namespace with UI tokens, reinforcing the "charts are a separate concern" principle.

## Extraction methodology used

Production design systems like PatternFly need their own approach. Used the following workflow:

1. **Find the canonical source** — `github.com/patternfly/patternfly`, navigated to `src/patternfly/base/tokens/`
2. **Survey the file list** — saw 17 token files including dark/light × default/highcontrast/charts/glass/redhat variants
3. **Identify which files matter** — `tokens-dark.scss` (43KB main), `tokens-charts-dark.scss` (15KB chart layer), `tokens-glass-dark.scss` (small but unique), `tokens-palette.scss` (raw palette)
4. **Read files top-down** — focused on understanding the naming convention, prefix groups, and any unique architectural patterns
5. **Compare to Primer** — looked specifically for differences in axis (intensity vs interaction state), naming style, and category organization
6. **Extract token examples per category** — listed bgColor, fgColor, borderColor tokens with their counts
7. **Look at chart tokens separately** — chart tokens are a domain-specific layer; needed separate consideration
8. **Look at glass tokens separately** — third glass approach in our library, worth comparing to OpenGridWorks and 7.css

**Total extraction time:** ~50 minutes, similar to Primer. The bulk of the time was understanding the architectural differences from Primer rather than enumerating tokens — most of the *value* of PatternFly is in the structural insights, not in specific values we'd vendor.
