# Primer (GitHub) — UI reference notes

**URL:** https://github.com/primer/primitives · https://primer.style/
**Tagline:** Color, typography, and spacing primitives in JSON5 (compiled to CSS via Style Dictionary).
**Domain:** GitHub's official design system. Powers github.com itself. Used by every developer-facing GitHub product.
**Tech:** JSON5 source files in `src/tokens/`, compiled by `style-dictionary` into per-platform outputs (CSS, Sass, JS, iOS, Android). Versioned as `@primer/primitives` on npm.
**Captured:** 2026-04-14

## Why Primer matters

This is the **largest and most rigorously organized** design system we've referenced. The dark theme alone has **900 unique custom properties across 41 prefix groups** — and that's only the dark theme. Across all 8 dark + 5 light theme variants, the total surface is several thousand tokens.

GitHub takes accessibility seriously. There are dark variants for:
- regular dark mode
- dimmed (softer black, less harsh on eyes)
- high contrast
- colorblind (deuteranopia/protanopia)
- colorblind + high contrast
- tritanopia
- tritanopia + high contrast

Each variant is a complete CSS file with the same token names but different values. **The architecture lesson is this: variables are the abstraction layer between visual values and component code. Swapping themes = swapping one CSS file for another with the same names.** Components never change. This is how you build theming.

## The architectural patterns worth stealing

### 1. The triplet pattern: `default` / `muted` / `emphasis`

Every semantic color category gets three intensity levels:

| State | Use for | Example |
|---|---|---|
| **default** | base elements | text color, surface color |
| **muted** | translucent backgrounds, subtle borders (~10-15% alpha) | hover fills, info backgrounds, soft separators |
| **emphasis** | strong, saturated, attention-grabbing | active states, pills, alerts |

Our current system has only two intensity levels per category (`--ds-signal-positive` and `--ds-signal-positive-muted`). Primer suggests adding a third: `--ds-signal-positive-emphasis`. **The asymmetry I had — bright text colors but muted backgrounds — was incomplete.** A full triplet means we can do bright pills, subtle backgrounds, and prominent buttons all from the same category without inventing new colors.

### 2. Semantic aliases for state, not just visual

Primer has both `--bgColor-success-emphasis` AND `--bgColor-open-emphasis` (which aliases to it). Components reference the SEMANTIC alias (`open`, `closed`, `draft`, `upsell`) — not the visual one (`success`, `danger`, `neutral`, `done`).

```css
--bgColor-closed-emphasis: var(--bgColor-danger-emphasis);
--bgColor-open-emphasis:   var(--bgColor-success-emphasis);
--bgColor-draft-emphasis:  var(--bgColor-neutral-emphasis);
```

**The crucial insight:** the visual mapping (closed=red, open=green) is an *implementation detail*. Components reference `bgColor-closed-emphasis`, which TODAY happens to be red but COULD be redefined. If GitHub ever decided closed PRs should be a different color, they could change one alias without touching component code.

For Exocortex this maps directly onto our hypothesis lifecycle:
```css
--ds-state-confirmed:  var(--ds-signal-positive);
--ds-state-falsified:  var(--ds-signal-negative);
--ds-state-pending:    var(--ds-signal-warning);
--ds-state-still-pending: var(--ds-signal-info);
```

The Pending tab UI references `--ds-state-confirmed` instead of `--ds-signal-positive`. The semantic intent is encoded in the variable name.

### 3. The `onEmphasis` / `onInverse` text colors

Solving the contrast pairing problem at the token level:

```css
--fgColor-onEmphasis: #ffffff;   /* text for use ON emphasis backgrounds */
--fgColor-onInverse:  #010409;   /* text for use ON inverse backgrounds */
```

When you put text on a colored button or pill, you need a different text color than your default. Most systems leave this to per-component `color: white` declarations. Primer encodes the contrast rule once. **Every component that needs "text on a colored background" uses the same token, and if the contrast rule ever changes, it changes once.**

For Exocortex: replace ad-hoc `color:#fff` on buttons with `--ds-text-onAccent`. Add the equivalent for our other accent colors.

### 4. Shadows by ROLE, not by SIZE

Most design systems name shadows `--shadow-1`, `--shadow-2`, `--shadow-3` by dimension. Primer names them by what the element IS doing:

| Role | Use for | Sizes |
|---|---|---|
| **resting** | element at rest, sitting on surface | xsmall, small, medium |
| **floating** | element floating above content | small, medium, large, xlarge |
| **inset** | element recessed below surface | (single value) |

```css
--shadow-resting-medium:  0 1px 1px 0 #01040966, 0 3px 6px 0 #010409cc;
--shadow-floating-medium: 0 0 0 1px #3d444d, 0 8px 16px -4px #01040966, 0 4px 32px -4px #01040966, 0 24px 48px -12px #01040966;
```

You choose the role first ("is this thing resting or floating?"), then the size. **This communicates intent better than a numeric scale.** Looking at a component definition that says `box-shadow: var(--shadow-floating-medium)`, you instantly know it's a floating element. Looking at `box-shadow: var(--shadow-3)` tells you nothing about its role.

For Exocortex: rename our existing shadows from `--ds-shadow-{sm,md,lg,xl}` to `--ds-shadow-resting-{sm,md}` and `--ds-shadow-floating-{sm,md,lg}`.

### 5. Hairline border baked into floating shadows

Look closely at the floating shadow:

```css
--shadow-floating-medium: 0 0 0 1px #3d444d, 0 8px 16px -4px #01040966, ...
                          ^^^^^^^^^^^^^^^^^
                          this is a 1px hairline border drawn via box-shadow
```

The first stop is `0 0 0 1px #3d444d` — a zero-blur 1px shadow at the same color as `borderColor-default`. That's a hairline border. **Floating elements get a clean edge for free without needing an actual `border` declaration.**

This matters because:
- Floating elements (modals, dropdowns) need a visible edge to separate them from content
- Adding `border: 1px solid` requires accounting for the extra 2px in layout
- A box-shadow border doesn't affect layout — it's purely visual
- Including it in the floating shadow token means components that use the shadow get the edge automatically

For Exocortex: bake a hairline border into our `--ds-shadow-floating-*` tokens.

### 6. Typed exception: the translucent border

```css
--borderColor-translucent: #ffffff26;
/** Semi-transparent border for overlays and layered elements.
    Border-specific token — no equivalent bg/fg variant. */
```

The comment explicitly notes this is **border-specific**: there's no equivalent `--bgColor-translucent` or `--fgColor-translucent`. This kind of explicit exception is valuable — it tells future maintainers "we considered the parallel but it doesn't exist on purpose." Reduces surprise and prevents people from inventing parallel tokens later.

For Exocortex: when we deliberately omit a token from a parallel structure, document the omission inline.

### 7. Documentation per token

Every token in Primer has a `/** description */` comment explaining its intended use. Every single one:

```css
--bgColor-default: #0d1117;     /** Default background color for pages and main content areas */
--bgColor-muted:   #151b23;     /** Muted background for secondary content areas and subtle grouping */
```

This is the level of documentation we should aspire to in `exocortex.css`. Currently we group tokens under section headers; Primer documents each token individually. The cost is high (every token needs a comment) but the value is enormous (any developer can find a token by searching for the use case in plain English).

## What ports to Exocortex

I'm going to graduate the **architectural patterns**, not just specific values. The values from Primer aren't directly applicable (their accent is GitHub-blue, ours is cyan; their dark is `#0d1117`, ours is `#060810`). What ports is the **structure**:

1. **The triplet pattern** — add `--ds-signal-{positive,negative,warning,info}-emphasis` variants alongside the existing `-muted` variants. We already have the base color and muted; emphasis is the third intensity level.

2. **Semantic state aliases for the hypothesis lifecycle** — add `--ds-state-{confirmed,falsified,pending,still-pending}` that alias to the underlying signal colors. The Pending tab and Hypotheses tab can reference these instead of the visual signal names.

3. **The `--ds-text-onAccent` / `--ds-text-onSignal-*` pattern** — add explicit "text for use on colored backgrounds" tokens. Replace the ad-hoc `color: white` declarations on buttons.

4. **Shadows renamed to roles** — restructure `--ds-shadow-{sm,md,lg}` into `--ds-shadow-resting-{sm,md}` and `--ds-shadow-floating-{sm,md,lg}`. Bake a 1px hairline border into the floating variants. The existing names will become aliases for backwards compat.

5. **Per-token documentation comments** — go through `exocortex.css` and add inline `/** */` comments explaining the intended use of each token, like Primer does.

6. **Theme-swap pattern documented** — note in `exocortex.css` that future themes (deep retro, high contrast) should ship as separate files with the same variable names, swapped at runtime.

## What does NOT port

- **The 41-group taxonomy.** GitHub's specific groups (`--label-*`, `--display-*`, `--diffBlob-*`, `--codeMirror-*`, `--contribution-*`, `--reactionButton-*`, `--buttonKeybindingHint-*`) are extremely product-specific. We don't have GitHub Sponsors, contribution graphs, or diff blob views. Adopting their full taxonomy would be cargo-culting.
- **The `--display-*` 285 tokens** — these are markdown rendering colors specific to GitHub's content. Not applicable.
- **The `--label-*` 133 tokens** — issue/PR label colors. Not applicable.
- **The 8 dark theme variants** — overkill. We need one dark theme. The variants exist for accessibility (colorblindness, high contrast) which we can address with a single high-contrast variant if/when needed.
- **Style Dictionary as a build tool** — we don't have a build pipeline for CSS. Our tokens live directly in `exocortex.css` and the embedded panel CSS. Adding Style Dictionary would be premature abstraction for a one-builder system.
- **The accent color palette (GitHub blue `#1f6feb`)** — we use cyan `#00e5ff` from OpenGridWorks. The Primer blue is too cool for our intelligence-console aesthetic.

## The methodology lesson

Primer is a **fourth category of reference**, distinct from the three I knew before:

| Category | Examples | Optimal extraction strategy |
|---|---|---|
| Application sites | OpenGridWorks | 9-grep against compiled CSS |
| Token libraries | Open Props | prefix counter, skip the 9 greps |
| Component frameworks | TuiCss, 7.css | per-component partial reads |
| **Production design systems** | **Primer** | **Read the design tokens guide first, then extract the universal semantic layer (bgColor/fgColor/borderColor/shadow/focus), skip the product-specific groups** |

For Primer, I read the dist file directly (97KB, 1811 lines), counted prefix groups (41 total), filtered to the universal categories (5 of 41), and extracted with regex. Total time: ~30 minutes. Most of that was reading the inline comments to understand the intent behind each token group.

The critical step for production design systems is **filtering out the product-specific noise**. Primer has 285 `--display-*` tokens for markdown rendering and 133 `--label-*` tokens for issue labels — those are GitHub-internal and would be cargo-culting if we adopted them. The universal layer (bgColor, fgColor, borderColor, shadow, focus) is the part worth studying.

## Caveats

- Primer's source is JSON5, not CSS. The compiled output is what I extracted. If we ever wanted to track upstream changes, we'd want to monitor either the npm package versions or the JSON5 source files.
- The `[data-color-mode="dark"][data-dark-theme="dark"]` selector is GitHub's theme-switching mechanism. When we extract the tokens, we wrap them in `[data-color-mode="dark"]` to preserve the spec, but in practice we'd put them on `:root` since Exocortex is dark-only.
- Some tokens reference each other via `var()` (the aliasing pattern). When extracting values, you have to dereference these manually if you want the literal hex.
- GitHub uses a custom build pipeline (`primerStyleDictionary.ts`) that does extra processing beyond standard Style Dictionary. The compiled output includes some quirks (duplicate declarations, ordering changes) that aren't in the source JSON5.

## Extraction methodology used

1. Found the Primer Primitives repo: `github.com/primer/primitives`
2. Identified the source structure: JSON5 in `src/tokens/`, compiled to CSS
3. Skipped the source files (would need build tooling) and went directly to the npm-published compiled CSS
4. Found `dist/css/functional/themes/dark.css` via unpkg
5. Ran prefix counter (1811 lines, 900 unique tokens, 41 groups)
6. Filtered to universal categories: bgColor, fgColor, borderColor, shadow, focus
7. Extracted with regex including the inline `/** comment */` documentation
8. Compared `dark.css` to `dark-dimmed.css` to understand the theme-swap mechanism

**Total extraction time:** ~45 minutes. Slower than Phase 1 because the surface area is much larger and the architectural patterns required careful reading to understand fully. Worth every minute — the lessons here are more valuable than the lessons from any single Phase 1 reference because they apply to **every** future design system we extract.
