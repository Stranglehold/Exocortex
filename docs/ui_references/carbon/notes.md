# Carbon (IBM) — UI reference notes

**URL:** https://github.com/carbon-design-system/carbon · https://carbondesignsystem.com/
**Tagline:** "A design system built by IBM."
**Domain:** IBM's enterprise design system. Powers Watson, IBM Cloud, Cloud Pak for Multicloud Management, Cognos Analytics, OpenPages, MaaS360, IBM Maximo, and basically every IBM enterprise/cloud product.
**Tech:** Source is JavaScript (`packages/themes/src/g100.js`) with per-theme value lookups inline. Build pipeline via custom Sass generator. Tokens compiled to CSS at build time. Themes named by gray level: white, g10, g90, g100 (deepest dark).
**Captured:** 2026-04-14
**Why this matters:** Third production design system in our library. Originally launched 2014, longer track record than Primer (2017) or PatternFly (2014 but much smaller scope at first). IBM's accessibility expertise is unmatched in the enterprise space — Carbon is one of the most-tested design systems for color contrast, keyboard navigation, and screen reader support.

## The biggest finding: AI-specific tokens

**Carbon ships dedicated CSS tokens for AI-generated UI content.** This is the most surprising and most relevant discovery from any reference so far.

```css
--cds-ai-popover-background:    #161616;
--cds-ai-aura-start:            rgba(69, 137, 255, 0.32);
--cds-ai-aura-end:              rgba(15, 98, 254, 0);
--cds-ai-aura-hover-start:      rgba(69, 137, 255, 0.40);
--cds-ai-border-strong:         #4589ff;
--cds-ai-drop-shadow:           0 0 8px rgba(69, 137, 255, 0.16);
--cds-ai-skeleton-background:   #262626;
```

The "aura" pattern is the signature: AI-generated content gets a gradient glow that surrounds it, marking it visually as distinct from regular UI. IBM Watson products use this to communicate **provenance** — users can see at a glance which UI elements came from AI inference vs deterministic logic.

**This is HIGHLY RELEVANT to Exocortex.** We have AI-generated content all over the place:
- Hypothesis explanations (LLM-generated)
- Swarmfish committee predictions (8 LLM calls per session)
- Resolver verdicts (LLM evaluation of past predictions)
- BST classification (deterministic — should look different)
- Operator briefs (LLM-formatted)
- Calibration narratives

Currently we have **zero visual treatment** that marks "this came from an LLM" vs "this came from deterministic code." Every component looks the same regardless of provenance. Carbon's AI aura pattern would communicate epistemic provenance at the UI level — an operator could see at a glance which content is AI-generated and apply appropriate skepticism.

This connects directly to the **Epistemic Integrity Layer** that already exists in Exocortex. We've built deterministic fact-checking for AI outputs at the *backend* level. Carbon shows us how to communicate the same provenance information at the *UI* level — by giving AI content a distinctive visual treatment.

I'm going to graduate the AI aura pattern into `exocortex.css` and reserve it for use on:
- The Resolver Proposal box in the Pending tab (LLM-generated verdict)
- The committee prediction reasoning in SWARMFISH → Predict (LLM-generated)
- The operator brief text in hypothesis details (LLM-generated)
- Any future agent-authored content

Deterministic content (claim counts, status pills, ingest health) stays without the aura. The visual difference IS the message.

## Carbon's other distinctive patterns

### 1. Numbered layer system with auto-promote

Carbon's signature contribution is the `layer-01` / `layer-02` / `layer-03` system. Three depth levels, each with six state variants:

```css
--cds-layer-01:                #262626;     /* default */
--cds-layer-active-01:         #525252;     /* clicked */
--cds-layer-background-01:     #161616;     /* background of children */
--cds-layer-hover-01:          #333333;     /* hovered */
--cds-layer-selected-01:       #393939;     /* selected/persistent */
--cds-layer-selected-hover-01: #4c4c4c;     /* hovered while selected */
```

The clever part is the **auto-promote rule**: when you nest a `layer-01` inside another `layer-01`, the inner one *automatically* promotes to `layer-02`. This is implemented via Sass mixins that walk the component tree and substitute the right layer level based on context.

Compare to PatternFly's `primary`/`secondary`/`tertiary` — same three levels but **named explicitly**. With Carbon, you write `class="layer"` and the layer level is inferred from context. With PatternFly, you write `class="layer-secondary"` and you have to know what context you're in.

**Carbon's approach is more systematic but more complex.** PatternFly's is more direct but requires you to manually track nesting.

For Exocortex: we don't have auto-promotion infrastructure (no Sass mixins, no build step). The PatternFly explicit-naming approach is more practical for our setup. **But the lesson is worth knowing**: when a design system has nesting beyond 2 levels, auto-promotion prevents the "I forgot which layer I'm on" problem.

### 2. Field tokens separate from layer tokens

```css
--cds-field-01:        #262626;
--cds-field-hover-01:  #333333;
```

Form input backgrounds get their own tokens, parallel to the layer system. Carbon's reasoning: form fields have different design constraints than general content surfaces. They need to be visually distinct enough to invite text input but not so distinct that they compete with the surrounding content.

For Exocortex: we don't have many form inputs, but the Predict input and the resolution outcome textarea would benefit from distinct field treatment. Currently they use the same surface as the surrounding panel.

### 3. Border tokens partitioned by weight AND by layer

```css
--cds-border-subtle-01:  #525252;     /* subtle border on layer-01 */
--cds-border-subtle-02:  #6f6f6f;     /* subtle border on layer-02 */
--cds-border-strong-01:  #6f6f6f;
--cds-border-strong-02:  #8d8d8d;
--cds-border-tile-01:    #525252;
--cds-border-tile-02:    #6f6f6f;
```

Three weights (subtle/strong/tile) × three layers (01/02/03) = 9 border tokens. This means a "subtle border on a layer-01 card" looks different from a "subtle border on a layer-02 card" — because the contrast needs are different against different backgrounds.

This is a refinement we don't need at our scale. Our borders are uniform across surfaces. Worth knowing about.

### 4. Three caution levels (Minor/Major/Undefined)

```css
--cds-support-caution-minor:      #f1c21b;     /* yellow30 */
--cds-support-caution-major:      #ff832b;     /* orange40 */
--cds-support-caution-undefined:  #a56eff;     /* purple50 */
```

Standard four-status (error/success/warning/info) PLUS three explicit caution levels. The third one is fascinating: **`caution-undefined` for situations where you've detected something off but can't classify it.**

Most systems force you into a category. Carbon gives you a dedicated "I don't know yet" color (purple). This is brilliant for **monitoring/operations dashboards** where you regularly encounter anomalies that don't fit known categories.

For Exocortex: this maps directly onto the resolver's `still_pending` verdict. When the autonomous resolver runs and says "I can't determine confirmed/falsified from the available evidence," that's a Carbon "caution-undefined." Currently we use info blue for `still_pending`. **Purple would be more semantically honest** — it explicitly communicates "indeterminate" rather than "neutral information."

I'm going to graduate this and update the resolver UI to use the undefined-caution color for `still_pending` proposals.

### 5. Icon tokens parallel to text tokens

```css
--cds-text-primary:    #f4f4f4;
--cds-icon-primary:    #f4f4f4;
--cds-text-secondary:  #c6c6c6;
--cds-icon-secondary:  #c6c6c6;
--cds-text-on-color:   #ffffff;
--cds-icon-on-color:   #ffffff;
```

Icons and text get parallel color tokens. They happen to have the same values in g100, but they CAN diverge if needed. The reasoning: icons are smaller than text and sometimes need higher contrast to be legible. Having separate tokens means a future accessibility update can adjust icon colors without affecting text.

For Exocortex: minor refinement. We currently use text colors for icons. Worth noting that having parallel tokens is a forward-compatibility move for accessibility.

### 6. Helper text token

```css
--cds-text-helper:  #a8a8a8;
```

Carbon has a dedicated token for "helper text" — the small explanatory text that appears below form inputs (e.g., "Enter your email address to receive updates"). It's between `text-secondary` and `text-disabled` in contrast.

This is a token category I hadn't seen before. Most systems use `text-secondary` for helper text and don't distinguish. Carbon recognizes that helper text is a specific UI pattern with its own contrast needs (it should be readable but not compete with the input itself).

For Exocortex: small refinement. Several places in the panel have explanatory text below inputs — the topic add form, the predict input, the score outcome textarea. They currently use `--ds-text-tertiary` which is fine but could use a dedicated `--ds-text-helper` for consistency.

### 7. Link as a first-class group

```css
--cds-link-primary:        #78a9ff;
--cds-link-primary-hover:  #a6c8ff;
--cds-link-secondary:      #a6c8ff;
--cds-link-inverse:        #0f62fe;
--cds-link-visited:        #be95ff;
```

Carbon treats links as their own token category with primary/secondary/visited/inverse plus hover/active states. Most systems just use the accent color for links; Carbon distinguishes them.

For Exocortex: we have very few links in the panel. Worth noting that production design systems treat links as first-class but for our use case the existing accent color is sufficient.

### 8. Computed values via JS functions

```javascript
export const backgroundActive = adjustAlpha(gray50, 0.4);
export const skeletonBackground = adjustLightness(background, 7);
export const overlay = rgba(black, 0.6);
```

Carbon's source uses JS functions to derive token values from base colors. `adjustAlpha(gray50, 0.4)` means "take the gray50 value and apply 40% alpha." `adjustLightness(background, 7)` means "take the current background and lighten by 7 units."

This is more dynamic than Primer's hardcoded RGBA values or PatternFly's hardcoded SCSS. Tokens can derive from each other programmatically. The downside: you need a build step. The upside: token relationships are explicit ("skeleton background is the page background, slightly lighter").

For Exocortex: we don't have a build step and adding one would be premature abstraction. But the lesson is worth knowing — when token relationships matter (e.g., "this color should always be 7% lighter than the background, regardless of which background"), encoding the relationship is more robust than hardcoding the result.

## What ports to Exocortex

1. **AI tokens — the single most valuable addition**. Vendor `--ds-ai-aura-start/end`, `--ds-ai-border-strong`, `--ds-ai-drop-shadow`, `--ds-ai-popover-bg`, `--ds-ai-skeleton-*`. Apply to LLM-generated UI content (resolver proposals, committee reasoning, operator briefs). This communicates epistemic provenance at the UI level.

2. **Caution-undefined color** (purple) for the `still_pending` resolver verdict. More semantically honest than info blue.

3. **`--ds-text-helper` token** for explanatory text below form inputs.

4. **Field tokens** as opt-in for form inputs that need distinct surface treatment from surrounding content. Reserved as `--ds-bgColor-field-01` through `--ds-bgColor-field-03`.

5. **Numbered layer system documented** as the alternative to PatternFly's role-based naming. We don't adopt the auto-promotion mechanism (no build step) but the concept is documented for future reference.

6. **Computed token relationships documented** as a pattern. Not adopted (no build step) but worth knowing for cases where token relationships matter.

## What does NOT port

- **The full numbered layer system with auto-promote**. Requires Sass mixins and build pipeline. We use PatternFly's explicit `--ds-surface-{primary,secondary,tertiary}` aliases instead.
- **Per-layer border tokens** (9 borders). Refinement we don't need at our scale.
- **Carbon's blue accent palette**. We use cyan from OpenGridWorks.
- **The 80+ syntax highlighting tokens**. We don't have code editing.
- **Component-level token files** (button, notification, tag, status, content-switcher). We have a small enough component count to define tokens inline.
- **Full link state matrix** (primary/secondary/visited/inverse with hover/active per state). Overkill for our use case.
- **JS-based token source**. Would require build pipeline.
- **The white/g10 light theme variants**. Exocortex is dark-only.

## Cross-pollination notes

**With Primer:** Carbon's `text-on-color` is identical to Primer's `fgColor-onEmphasis`. Same idea, different name. Carbon's icon tokens are an extension Primer doesn't have. Both have first-class link tokens.

**With PatternFly:** Carbon's layer-01/02/03 is comparable to PatternFly's primary/secondary/tertiary, but Carbon has more state variants (6 per layer vs PatternFly's 3). PatternFly has the status-vs-nonstatus partition which Carbon doesn't have. Carbon has the AI tokens and caution-undefined which PatternFly doesn't.

**With our existing system:** Carbon's caution-undefined is the missing color we needed for `still_pending`. The AI aura pattern is the missing visual layer for marking LLM-generated content. Both are immediate adoption candidates.

**Synthesis across all three production systems:**

| Concern | Primer | PatternFly | Carbon |
|---|---|---|---|
| Color intensity axis | ✅ default/muted/emphasis | (limited) | (limited) |
| Interaction state axis | (limited) | ✅ default/hover/clicked | ✅ default/hover/active/selected |
| Surface elevation | flat | role-based (primary/secondary/tertiary) | numbered (layer-01/02/03) |
| Status partition | semantic aliases | status vs nonstatus | (single category) |
| Status granularity | 7 categories | 5 categories | 4 + 3 caution levels |
| Theme switching | per-theme CSS files | per-theme SCSS files | per-theme JS source |
| AI content tokens | ❌ | ❌ | ✅ |
| Chart token layer | ❌ | ✅ | ❌ |
| Computed values | ❌ | ❌ | ✅ |
| Skeleton tokens | ❌ | ✅ | ✅ |

**Each system fills different gaps.** A "perfect" design system would combine:
- Primer's intensity triplet
- PatternFly's interaction state triplet AND chart layer concept
- Carbon's AI tokens AND caution-undefined level

That's exactly what `exocortex.css` is becoming.

## Caveats

- Carbon's source is JavaScript, not CSS. The tokens I extracted are values from the JS source after manual lookup of imported color constants (e.g., `gray100 = #161616`). The compiled CSS output uses different naming (`--cds-*` prefix) than the JS exports (camelCase).
- The g100 theme is just one of four. Light theme variants (white, g10) have completely different surface values. The token NAMES are the same — only the values differ. This is the same theme-swap pattern as Primer.
- Carbon has a v10 directory alongside v11. v10 is the legacy token set; v11 is current. We extracted only from v11 sources.
- Component tokens (button, tag, notification) are in a separate `component-tokens/` directory with per-theme value lookups inline as JS objects. We didn't enumerate these — they follow the same patterns as the global tokens.
- The AI tokens are relatively recent (added in v11 phase 2 per the source comments). Carbon is an evolving system — what we extracted today may not match what's there in 6 months.

## Extraction methodology used

1. **Found the canonical source** — `github.com/carbon-design-system/carbon`, navigated to `packages/themes/src/`
2. **Identified the theme files** — `g100.js` is the deepest dark mode (analogous to our setup)
3. **Read `g100.js` linearly** to understand the token structure and naming conventions
4. **Cross-referenced imports** — many tokens reference base color constants (gray10, blue40, etc.) which are imported from another file
5. **Read `v11TokenGroup.js`** to see the canonical group definitions
6. **Spot-checked component tokens** (button) to see how component-level tokens layer on top of global tokens
7. **Manually resolved JS values to CSS hex** — since Carbon's source is JS with imported constants, I had to look up the actual hex values for things like `gray100`, `blue40`, etc.

**Total extraction time:** ~50 minutes, similar to PatternFly. The biggest time sink was understanding the layer-NN system and tracing how the JS-based source compiles to the CSS output. The biggest payoff was discovering the AI tokens — that one finding alone justifies the whole extraction.
