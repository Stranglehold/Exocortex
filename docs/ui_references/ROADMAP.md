# UI Reference Library — Analysis Roadmap

*Living document. Updated when references are added, analyzed, graduated, or deferred.*
*Last revised: 2026-04-14*

---

## Research question

**What combinations of design tokens and interaction patterns produce interfaces that feel good to use?**

"Feel good" is the load-bearing criterion. We're not collecting design systems as abstract knowledge — we're assembling a vocabulary of patterns that demonstrably produce fluidity, information density, and aesthetic coherence in real use. Every entry in this library should trace back to either:

1. A site or framework whose aesthetic actively resonated with Jake, or
2. A production design system whose token organization teaches us something about structure

Patterns graduate into [`exocortex.css`](exocortex.css) only when we can articulate *why* they feel good, not just that they look nice.

## Aesthetic direction (the filter)

The Exocortex intelligence console we're building toward has a specific target vibe:

- **Dark / midnight palette** — deep navy to near-black, not neutral grey
- **Cyan + violet accent palette** — radar/sonar/terminal lineage, not corporate brand colors
- **Glowing signal indicators** — active elements emit light; inactive elements recede
- **Data-dense but organized** — high information per square pixel without crowding
- **Fast aggressive motion** — 80-150ms transitions, ease-out curves, tactile scale feedback
- **Fluid state transitions** — interactions feel instant; state changes feel intentional
- **MGS3 Major Zero / OpenPlanter / mission control lineage** — analytical, operational, slightly cinematic

References get rated against this target. Patterns that match score higher; patterns that don't still get archived but are marked as "informational only."

## What counts as a reference worth analyzing

A candidate makes the list if it satisfies at least two of:

1. **Distinct aesthetic** — doesn't look like a Bootstrap variant
2. **Documented design system** — exposes tokens as CSS custom properties we can grep
3. **Actively maintained** — recent commits, working demo
4. **Domain adjacency** — data-dense dashboards, terminal UIs, monitoring/ops surfaces, geospatial viz
5. **Interaction quality** — notable transition/hover/focus states we can steal

A candidate gets **rejected** (not deferred) if:

- It's a Bootstrap/Tailwind theme pack (we have those patterns already)
- It has no documented design tokens (pure utility classes don't port)
- It depends on paid fonts/assets we can't redistribute
- It's marked "stalled development" in the source and hasn't been touched in 2+ years

## Extraction methodology

Documented in [memory/project_ui_reference_library.md](../../../memory/project_ui_reference_library.md).

Summary: save page → 9-grep extraction → tokens.css + notes.md in `docs/ui_references/<sitename>/` → optionally graduate patterns into `exocortex.css` with source comment.

The 9 greps in order of priority:

1. `--[a-z-]+:` — CSS custom properties (highest signal)
2. `transition[^;]*`
3. `cubic-bezier[^)]*`
4. `backdrop-filter[^;]*`
5. `box-shadow:[^;]*`
6. `:hover\{[^}]*\}`
7. `:active\{[^}]*\}`
8. `@keyframes [a-z-]+`
9. `font-family:`

Target: ~15-30 minutes per reference depending on CSS size.

---

## Phase 1 — Highest-value fastest-extract

**Goal:** Build the initial token library with references most directly aligned to our aesthetic target. Each is small enough to extract in one sitting.

| # | Name | Why | Priority | Status |
|---|------|-----|----------|--------|
| 1 | [OpenGridWorks](https://opengridworks.com/power-plants) | Modern cyberpunk dashboard. 73 tokens, glass panels, cyan signal. Jake's original visual reference. | Done | ✅ Analyzed 2026-04-13 · [tokens.css](opengridworks/tokens.css) · [notes.md](opengridworks/notes.md) · many patterns graduated into `exocortex.css` |
| 2 | [TuiCss](https://github.com/vinibiavatti1/TuiCss) | MS-DOS interfaces. Direct MGS3 Major Zero match. Phosphor/monospace/panel borders. | Done | ✅ Analyzed 2026-04-14 · [tokens.css](tuicss/tokens.css) · [notes.md](tuicss/notes.md) · 16-color CGA palette + instantaneous-state utility graduated into `exocortex.css` |
| 3 | [Open Props](https://open-props.style) | Pre-built CSS custom property library. Not for aesthetic — for token structure. We should vendor selected groups directly. | Done | ✅ Analyzed 2026-04-14 · [tokens.css](openprops/tokens.css) · [notes.md](openprops/notes.md) · animation presets, layer scale, easing curves, and noise texture graduated into `exocortex.css` |
| 4 | [7.css](https://khang-nd.github.io/7.css/) | Aero Glass in pure CSS. Second reference for glass pattern. Border treatments + translucency formulas. | Done | ✅ Analyzed 2026-04-14 · [tokens.css](7css/tokens.css) · [notes.md](7css/notes.md) · `.ds-aero-glass`, `.ds-warm-hover`, `.ds-default-pulse`, `.ds-hard-stop-gradient` graduated into `exocortex.css` |

**Phase 1 exit criterion:** ✅ Met. `exocortex.css` now contains tokens and patterns sourced from 4 references with full lineage comments. Ready to move into Phase 2 (production design systems).

## Phase 2 — Production design systems

**Goal:** Learn from how mature design systems organize tokens. Focus is on *structure* and *token grouping conventions*, not aesthetics.

| # | Name | Why | Priority | Status |
|---|------|-----|----------|--------|
| 5 | [Primer](https://primer.style/) | GitHub's design system. Battle-tested dark mode, accessible, well-organized token scale. | Done | ✅ Analyzed 2026-04-14 · [tokens.css](primer/tokens.css) · [notes.md](primer/notes.md) · triplet pattern, state aliases, on-emphasis text colors, role-based shadows graduated into `exocortex.css` |
| 6 | [PatternFly](https://www.patternfly.org/) | Red Hat's enterprise dashboard framework. Domain match (monitoring/ops). Study layout primitives, not components. | Done | ✅ Analyzed 2026-04-14 · [tokens.css](patternfly/tokens.css) · [notes.md](patternfly/notes.md) · interaction state triplet, surface role aliases, special-purpose backgrounds, glass-as-theme-token, chart layer reservation graduated into `exocortex.css` |
| 7 | [Carbon](https://www.carbondesignsystem.com/) | IBM's enterprise design system. Similar territory to Primer, different conventions — useful for comparison. | Done | ✅ Analyzed 2026-04-14 · [tokens.css](carbon/tokens.css) · [notes.md](carbon/notes.md) · **AI tokens (the most important finding from Phase 2)**, caution-undefined for still_pending, helper text token, layered surface system documented |
| 8 | [Vanilla Framework](https://vanillaframework.io/) | Canonical (Ubuntu). Minimalist, dark theme compatible. | Done | ✅ Analyzed 2026-04-14 · [tokens.css](vanilla/tokens.css) · [notes.md](vanilla/notes.md) · W3C Design Tokens Format compliance, themeable metadata pattern, text-inactive distinction graduated, brand reservation added |

**Phase 2 exit criterion:** ✅ **MET (2026-04-14).** All 4 production design systems analyzed. Token grouping in `exocortex.css` reviewed against all four; gaps either filled or documented as intentionally omitted. The reference library now spans 8 sources (4 from Phase 1 + 4 from Phase 2) with a comprehensive design vocabulary across every major architectural axis.

## Phase 3 — Adjacent aesthetics (informational)

**Goal:** Archive alternative aesthetic traditions for cross-pollination and context. These don't directly port but inform variation decisions.

| # | Name | Why | Priority | Status |
|---|------|-----|----------|--------|
| 9 | [System.css](https://sakofchit.github.io/system.css/) | Retro Apple / classic Mac. Informs how to do "authentic system aesthetic." | Low | ✅ Analyzed 2026-04-14 · [tokens.css](system/tokens.css) · [notes.md](system/notes.md) · techniques archived, no direct graduation (4-color 1-bit Mac palette doesn't port to dark dashboard) |
| 10 | [98.css](https://jdan.github.io/98.css/) | Windows 98 UI. 3D chrome, beveled borders. | Low | ✅ Analyzed 2026-04-14 · [tokens.css](98/tokens.css) · [notes.md](98/notes.md) · four-layer inset-shadow bevel reserved as dark-theme depth technique; zero-variables philosophy documented |
| 11 | [NES.css](https://nostalgic-css.github.io/NES.css/) | NES 8-bit. Pixel-perfect discrete color palette. Lesson in categorical color. | Low | ✅ Analyzed 2026-04-14 · [tokens.css](nes/tokens.css) · [notes.md](nes/notes.md) · `::after` depth-shadow pattern reserved; hand-picked-depth-over-computed principle documented; third validation of calm-mode philosophy |
| 12 | [XP.css](https://botoxparty.github.io/XP.css/) | Windows XP. Luna theme recreation. | Low | ✅ Analyzed 2026-04-14 · [tokens.css](xp/tokens.css) · [notes.md](xp/notes.md) · 8-stop reflection-band gradient technique reserved; one-transition-is-enough philosophy archived; sliding-stripe progress pattern reserved |
| 13 | [Tufte CSS](https://edwardtufte.github.io/tufte-css/) | Edward Tufte's information design. Data-dense typography. Different direction but informs density judgments. | Done | ✅ Analyzed 2026-04-14 · [tokens.css](tufte/tokens.css) · [notes.md](tufte/notes.md) · sidenote pattern, newthought small-caps, reading-column constraint, calm-mode utility, old-style numerals graduated into `exocortex.css` |

**Phase 3 exit criterion:** ✅ **MET (2026-04-14).** All 5 adjacent-aesthetic references analyzed. Phase 3 was never meant to graduate heavy patterns — it was meant to archive alternative traditions and surface cross-cutting philosophies. The cross-cutting findings (below) are the real output of the phase.

### Phase 3 synthesis — what the five retro references agreed on

The five Phase 3 references (Tufte, System.css, 98.css, NES.css, XP.css) came from wildly different eras and aesthetics — Edwardian book typography, 1984 classic Mac, 1998 Windows, 1985 Nintendo, 2001 Windows XP. But after extracting all five, three philosophical principles recur across every one of them, and none of them is something modern design systems (Carbon, Primer, Vanilla, PatternFly) emphasize. This is the value of Phase 3: alternative traditions surfacing assumptions that current production design systems have forgotten.

**1. Motion is optional, and usually wrong.** Four of five Phase 3 references ship zero transitions. The fifth (XP.css) ships exactly one — a 100ms background transition on buttons. Five retro references, five commitments to minimal motion. Compare to modern design systems which treat motion as compositional (Carbon has a full motion token layer; Material has elevation animations baked into every component; PatternFly documents hover/focus/clicked as three distinct states). The retro tradition is different: **if you have to pick one thing to animate, animate the background color under the cursor at 100ms and ignore everything else.** Our `.ds-calm-mode` utility is validated three times over by this convergence. Worth promoting from "one possible mode" to "recognized alternative tradition worth offering users."

**2. The right number of design tokens is determined by what varies.** System.css: 4 colors + semantic mapping, total ~12 tokens. 98.css: 0 CSS custom properties, everything hardcoded. NES.css: 0 CSS custom properties, everything hardcoded. XP.css: 0 CSS custom properties (extends 98.css). Tufte CSS: 5 colors, 1 font stack, ~6 tokens. Compare to Carbon's 900 tokens in the dark theme alone. The lesson is not "retro is simpler" — it's that **token count should match the variability of the visual language you're building**. Carbon needs 900 tokens because IBM themes across hundreds of products. 98.css needs 0 because Windows 98 has exactly one aesthetic. Token bloat is a real cost when the system isn't themed. Exocortex is somewhere in the middle and the right count is probably 60-100 — enough to support states and semantic colors without over-parameterizing fixed choices.

**3. Commitment to a single era produces coherence that hybrid aesthetics cannot.** All five Phase 3 references commit fully to their source material. System.css is 1-bit classic Mac; no compromises for modern accessibility or dark themes. 98.css is pure Windows 98; no Aero or Modern UI mixing. NES.css is NES 1985; every sprite is a hand-drawn pixel art. XP.css is Luna; no Fluent Design touches. Tufte CSS is Edward Tufte's book design; no dashboard adaptations. **The commitment is the aesthetic.** Our dashboard is trying to commit to one specific vibe (MGS3 Major Zero / cyberpunk mission control / glass + signal + precision). The Phase 3 lesson is to commit harder — resist the urge to mix in Material "feel" or Bootstrap familiarity. Either be the specific thing or don't, but don't half-commit.

### Phase 3 techniques archived (not yet graduated)

None of the Phase 3 references produced patterns urgent enough to graduate into `exocortex.css` immediately. The following techniques are documented in their respective `notes.md` files and are **available for future use** when the right need arises:

| Technique | Source | Use case |
|-----------|--------|----------|
| Four-layer inset-shadow bevel | 98.css | Cheap depth on dark panels without backdrop-filter. Reserved for potential retro mode or chunky accent panels. |
| `::after` depth-shadow pattern | NES.css | Hover/active states on dense grids where layout must stay stable (no transforms). Useful for data table cells. |
| Multi-stop reflection-band gradient | XP.css | Glossy skeuomorphic surfaces. Reserved for potential "material mode" or accent headers that should feel physical. |
| Sliding-stripe progress marquee | XP.css | Activity indicator without a spinner. Candidate for sprint button or ingestion status. |
| `currentColor`-default box-shadow | System.css | Shadows that should match their element's text color — skip explicit color declaration. |
| Linear-gradient tiled background patterns | System.css | Dot grids, stripes, checkerboards via two crossed linear-gradients, zero image assets. Reserved for potential retro overlay. |
| Computed token geometry via calc() | System.css | When radio/checkbox/slider dimensions need to scale together. Reserved for form components we don't yet have. |
| Hand-picked depth colors over computed | NES.css | When adding elevated/recessed states to accent colors, shift hue slightly rather than just darken luminance. |
| The "one transition" philosophy | XP.css | Minimum-viable-motion calibration point. Use to audit our current animation set — is each transition the background-at-100ms of its context? |

These are reference techniques, not active patterns. They live in the respective `tokens.css` and `notes.md` files until a specific need arises.

## Phase 4 — Application sites (ongoing)

**Goal:** Analyze real products that feel good to use, not just frameworks. Jake curates the inputs as he finds them in the wild.

| # | Name | Why | Status |
|---|------|-----|--------|
| — | [OpenGridWorks](https://opengridworks.com/power-plants) | See Phase 1 | ✅ |

**This phase grows over time.** When Jake finds a site whose aesthetic resonates, add it here. No priority tiers — each gets analyzed when it arrives.

## Open backlog

*URLs to pick up in future sessions. Jake drops, Kestrel picks up.*

- (empty)

## Rejected (explicit exclusions, with reason)

*References we've decided NOT to analyze, and why. Saves us from reconsidering them later.*

- **Bootstrap** — ubiquitous, patterns already well-known, we'd learn nothing new
- **Foundation** — Bootstrap-adjacent; same reasoning
- **Bulma / UIkit / Fomantic-UI / Cirrus / HiQ** — general-purpose frameworks, none with distinct aesthetic tradition
- **Materialize / Beer CSS** — Material Design recreations, patterns already documented by Google
- **modern-normalize / ress / sanitize.css / CSS Remedy** — resets, no design tokens
- **Pure / Picnic / Chota / Simple.css / Sakura / Pico.css / MVP.css / Tacit** — classless/lightweight frameworks with minimal customization surface
- **Tailwind CSS** — utility-first, not a design system we can extract tokens from (it IS tokens but the philosophy is different — closer to Open Props)
- **Semantic UI / Material Components Web / Tachyons / Bourbon / Water.css / Blaze UI / Concise CSS / Responsive Boilerplate** — all marked "stalled development" in the source

## Findings notebook

*Accumulated observations across analyses. Grows with each new reference.*

### 2026-04-13 — from OpenGridWorks extraction

1. **Fluidity is a numbers problem, not a taste problem.** 150ms default / 80ms micro-feedback + `cubic-bezier(0.16, 1, 0.3, 1)` produces the "feels responsive" effect. Slower timings feel sluggish; faster feel abrupt.

2. **Glass panels require a background to blur.** `backdrop-filter: blur(20px) saturate(140%)` only works when there's content behind the panel. On a flat solid background it degrades to a translucent color — no benefit. Solution: add a subtle radial gradient or noise pattern to the body so glass has something to interact with.

3. **Scale feedback on buttons is more valuable than color change.** `transform: scale(1.03)` on hover + `scale(0.97)` on active, combined with a 80ms transform duration, gives tactile "this is clickable" feedback that color-only changes don't.

4. **Full color palettes for state, not opacity shifts.** Each state (hover/active/success/error/info) gets a distinct hue instead of "normal with less opacity." Parses faster for the eye because it's categorically different.

5. **Data-label tooltips are CSS-only, no JS.** `::after { content: attr(data-label) }` with opacity transitions handles hover tooltips without any framework overhead. This scales to every button in a UI with zero per-component effort.

6. **CSS custom properties are the killer grep target.** OpenGridWorks exposed 73 `--ds-*` variables. Extracting them wholesale saved hours vs. reading component rules. **Always grep for `--[a-z-]+:` first.**

7. **Count-first row format.** `Solar · 91 · 482 MW` puts the numbers first and the label second. High data density without crowding because the eye can scan numerically.

### 2026-04-14 — from TuiCss extraction

8. **Absence is a finding.** The 9-grep methodology returned **zero results for 5 of 9 patterns** on TuiCss (no custom properties, no transitions, no easings, no backdrop filters, no hover/active rules). That isn't a failed analysis — it's the most important thing about TuiCss. The methodology's "what's missing" output is signal, not noise.

9. **Two design philosophies for "responsive UI":**
   - **OpenGridWorks model:** Fluidity comes from *fast transitions* (150ms) and *tactile feedback* (scale + glow). Interactive elements feel "alive."
   - **TuiCss model:** Fluidity comes from *zero transitions* — state changes are instantaneous and binary. Elements feel "precise."
   - These are not better/worse. They produce different feelings of correctness. **Use OpenGridWorks for elements where the user wants to feel they're interacting with something alive (buttons, menus, navigation). Use TuiCss for elements where the user needs to trust that the visual matches the data exactly (status indicators, counts, monitor states).**

10. **The CGA/EGA 16-color palette is loaded with cinematic signal.** Major Zero, *War Games*, *Sneakers*, *Three Days of the Condor* all used these exact colors because that's what 1960s-1980s mainframe terminals displayed. The palette itself does narrative work — invoking it places a UI in the intelligence-agency lineage instantly. Reserved as `--tui-*` namespace in `exocortex.css` for opt-in deep-retro mode.

11. **Hard offset shadows vs. soft glow shadows are categorically different.** Hard shadows (`box-shadow: 10px 10px black`, no blur) read as "physical sticker on a flat surface." Soft glow shadows (`box-shadow: 0 0 20px rgba(0,229,255,0.06)`) read as "floating lit element." Both are valid; mixing them on the same surface looks broken. Choose one register per visual context.

12. **State via class names, not pseudo-classes.** TuiCss uses `.tui-modal.active`, `.tui-tab.active` — JavaScript adds/removes the class. This binds visual state to *data state*, not to *mouse position*. Better for status indicators where the data is the source of truth. We already do this in the OSS panel (Alpine.js drives it) — TuiCss confirms it as a deliberate design pattern, not just a framework constraint.

### 2026-04-14 — from Open Props extraction

13. **Token libraries are different from design systems.** Open Props ships 603 raw values across 32 prefix groups. It deliberately gives you no semantic guidance ("what's primary, what's secondary"). It expects you to build your own semantic layer on top. This is exactly what `exocortex.css` does — Open Props is the lumber yard, OpenGridWorks's `--ds-*` is "a house pre-built from this lumber," and `exocortex.css` is "our house, with notes on which boards came from where."

14. **The 9-grep methodology has an alternate fast path for token libraries.** When a reference is structured as `--prefix-name: value` everywhere (no components, no rules), skip the 9 greps and go straight to:
    ```python
    re.findall(r'--[a-z][a-z0-9-]*(?=:)', css)  # all custom property names
    Counter(p.split('-')[1] for p in unique)    # group by prefix
    ```
    Open Props extraction took 10 minutes vs. ~30 for OpenGridWorks because it's *designed* to be parsed.

15. **Animation presets are a high-leverage category.** Open Props ships 23 named animation strings (`--animation-fade-in`, `--animation-shake-x`, `--animation-pulse`) paired with their @keyframes. These let you write `animation: var(--ds-anim-shake-x)` on any element to get the effect — no per-component keyframe boilerplate. We graduated 8 of them into `exocortex.css` for use in the Pending tab (shake on failed prediction), the monitor status (pulse on running cycle), and the panel reveals (fade-in/slide-in).

16. **Three philosophies of motion now coexist in `exocortex.css`:**
    - **OpenGridWorks fast transitions** (150ms cubic-bezier) — for hover/active feedback on interactive elements
    - **Open Props animation presets** (longer durations, named keyframes) — for content reveals and attention markers
    - **TuiCss `.ds-instant-state`** (zero transition) — for truth-bearing indicators that should never lie during a transition
    
    Each has its place. The Exocortex visual vocabulary is now richer because we have all three, with explicit rules for when to use each.

17. **CSS noise textures are subtle but valuable.** Open Props ships SVG-encoded fractal noise filters that can be applied as background-images. At low opacity (0.03-0.05) over a dark background, they prevent banding on cheap displays and add subtle texture without being visible. The `--ds-noise` token is now available in `exocortex.css`.

18. **Z-index discipline matters more than I thought.** Currently the OSS panel has ad-hoc z-indices (`1000` for tooltips, `42` for FABs in OpenGridWorks). A canonical layer scale (`--ds-layer-overlay: 100`, `--ds-layer-modal: 500`, `--ds-layer-toast: 900`, `--ds-layer-important: 2147483647`) replaces guesswork with named intent. Vendored from Open Props.

### 2026-04-14 — from 7.css extraction

19. **There are TWO valid approaches to "glass" in CSS, and we now have both.** OpenGridWorks uses `backdrop-filter: blur(20px)` — modern, expensive, dynamic, blurs whatever's behind. 7.css uses stacked CSS gradients with inset highlights — period-authentic, cheap, static, identical regardless of background. **Both are now in `exocortex.css`** as `.ds-glass` (backdrop-filter) and `.ds-aero-glass` (gradient). This is a real fallback if backdrop-filter ever becomes a performance problem or we need a glass panel that doesn't depend on what's behind it.

20. **Asymmetric hover transitions are warmth.** 7.css fades hover-in fast (0.3s) and hover-out slow (1s). The slow fade-out makes buttons feel like they "noticed you" and are lingering. OpenGridWorks's symmetric 150ms feels precise and mechanical. **Both are correct in their context.** Symmetric for controls and status pills (mechanical accuracy); asymmetric for primary CTAs and welcome panels (humanized warmth). Available as `.ds-warm-hover` opt-in class — not the default.

21. **The hard-stop gradient is the single most identifiable Aero technique.** A linear gradient with a sharp transition at 45% (instead of a smooth blend) creates the appearance of a curved surface caught in raking light, even though the gradient is mathematically flat. The eye reads the discontinuity as 3D. Vendored as `.ds-hard-stop-gradient` for use on cards/panels that should read as "physical surface" rather than "data display."

22. **Stacked-pseudo-element state layers are how you cross-fade between completely different appearances.** 7.css buttons use `::before` for hover state and `::after` for active state, fading their opacity rather than interpolating background-colors directly. Lets you transition between gradients (which can't be CSS-interpolated). Documented as a technique in 7.css notes; not vendored as a token because it requires per-component HTML structure.

23. **The pulse-default-button affordance is genuinely useful.** Aero's "this is the default action, press Enter" indicator is a slowly-pulsing cyan inner glow (alternating blur radius from 3px to 1px every second). Subtle but unmistakable. Vendored as `.ds-default-pulse` + `@keyframes ds-default-pulse`. Apply to the primary CTA on any form where Enter does something meaningful.

24. **Dark Aero doesn't really exist as a coherent aesthetic.** Aero's softness comes from light hitting glass from above. Dark surfaces with white highlights look broken — like the surface is lit from below. We adapted the hard-stop gradient to dark theme (surface-raised → surface-base) but the effect is much subtler than the original. Lesson: **some aesthetic traditions are fundamentally light-mode or fundamentally dark-mode, not interchangeable.**

25. **Methodology should adapt to source structure.** Three different reference types now have three different optimal approaches:
    - **Application sites** (OpenGridWorks): 9-grep against compiled CSS
    - **Token libraries** (Open Props): prefix counter, skip the 9 greps
    - **Component-based frameworks** (7.css, TuiCss): per-component partial reads
    
    7.css took 15 minutes; reading the SCSS partials directly was faster than running greps against compiled output.

### 2026-04-14 — from Primer extraction

26. **Production design systems are a fourth methodology category.** Primer ships **900 unique custom properties across 41 prefix groups in just the dark theme** — and that's only one of 13 theme variants. The 9-grep methodology would drown in noise. The right approach is: read the design tokens guide first, run the prefix counter to identify groups, **filter to the universal semantic layer** (bgColor, fgColor, borderColor, shadow, focus), and explicitly skip product-specific groups (in Primer's case: `--label-*`, `--display-*`, `--diffBlob-*`, `--codeMirror-*`, `--contribution-*` — all GitHub-internal). Total time ~45 min, longer than other categories but worth it because the architectural lessons compound.

27. **The `default` / `muted` / `emphasis` triplet is the right shape.** I had two intensity levels per signal color (`positive` and `positive-muted`); Primer has three. The third (`emphasis`) is the saturated variant for prominent backgrounds. Without it, you can't have "subtle hover tint" AND "active button background" AND "text color" all from the same category. Adopted into `exocortex.css` as `--ds-signal-{positive,negative,warning,info}-emphasis`.

28. **Semantic state aliases decouple intent from visual implementation.** Primer has `--bgColor-success-emphasis` (visual) AND `--bgColor-open-emphasis` (semantic — aliases to success). Components reference the SEMANTIC name. If GitHub ever changes the visual mapping, only the alias changes — components stay the same. Adopted as `--ds-state-{confirmed,falsified,pending,still-pending,running,paused,stopped}` for our hypothesis lifecycle and service control. Pending tab and Hypotheses tab can now reference `--ds-state-confirmed` instead of `--ds-signal-positive`, encoding intent in the variable name.

29. **Text-on-background contrast pairing belongs in the token system.** Every component that puts text on a colored background needs a different text color than the default. Most systems leave this to ad-hoc `color: white` declarations. Primer encodes the rule once via `--fgColor-onEmphasis: #ffffff`. Adopted as `--ds-text-on-{emphasis,accent,positive,negative,warning,info}`. **The cyan one is dark** — `--ds-text-on-accent: #060810` — because cyan is too light for white text to pass contrast. This solves a class of bugs ("I tried to make a cyan button but the text was unreadable") at the token level.

30. **Shadows by ROLE, not by SIZE.** This is the most architecturally valuable lesson from Primer. Most design systems name shadows `--shadow-1`, `--shadow-2`, `--shadow-3` by dimension. Primer names them by what the element IS doing: `resting` (sitting on a surface), `floating` (above other content), `inset` (recessed below the surface). Each role has size variants. **Looking at `box-shadow: var(--ds-shadow-floating-md)` instantly tells you the element is floating**, which `box-shadow: var(--ds-shadow-3)` doesn't. Restructured `exocortex.css` shadow scale; legacy `--ds-shadow-{sm,md,lg}` aliases preserved for backwards compat.

31. **Hairline borders baked into floating shadows.** Primer's `--shadow-floating-medium` starts with `0 0 0 1px #3d444d` — a zero-blur 1px shadow that draws a hairline border around the element WITHOUT affecting layout (because box-shadow doesn't add to size like `border` does). Floating elements (modals, dropdowns, popovers) need a visible edge to separate from content; this gives them one for free. Applied to `.sess-detail` and `.pdetail` in OSS panel — the row-expansion containers used to have separate `border` declarations, now they get the edge from the shadow alone.

32. **Theme switching: variables ARE the abstraction layer.** GitHub ships 13 theme variants (dark, dark-dimmed, dark-high-contrast, 3 colorblindness modes, plus 5 light variants), each as a separate CSS file with the **same variable names** but different values. Application code never changes — it always references `var(--bgColor-default)`. Swapping themes = loading a different CSS file. **This is how to build theming.** When we eventually add a "deep retro mode" or "high contrast mode" to Exocortex, ship it as a separate file with the same `--ds-*` names, swapped at runtime via a class on the body or a `data-theme` attribute. Documented in `exocortex.css` for future use.

33. **Per-token documentation comments are aspirational but valuable.** Every token in Primer has a `/** description */` comment. We don't have that level of documentation in `exocortex.css` yet — we group tokens under section headers but don't comment each one individually. The cost is high (every token needs a comment) but the value compounds: any developer can find a token by searching for its use case in plain English. Future improvement to `exocortex.css`: pass through and add inline documentation, prioritizing the semantic layer over the raw values.

### 2026-04-14 — from PatternFly extraction

34. **Color tokens have TWO orthogonal axes.** Primer focuses on intensity (default/muted/emphasis); PatternFly focuses on interaction state (default/hover/clicked). **These are NOT alternatives — they're orthogonal axes.** A complete design system has both: a button can be `intensity-default × state-rest`, or `intensity-emphasis × state-clicked`, etc. That's 6 variants per category (2 intensities × 3 states). Most categories will use only the default-intensity row; emphasis interactivity is reserved for primary CTAs where every state needs explicit colors. Vendored as `--ds-state-{confirmed,falsified,pending}-{rest,hover,clicked}` for our most active categories.

35. **Status vs Nonstatus is a partition rule, not just naming.** PatternFly explicitly partitions colors into `status--*` (carries semantic meaning: success means "good thing") and `nonstatus--*` (categorical/decorative: blue is just blue). The token system encodes the rule "don't use status colors for decoration" — if you need a blue label for visual variety, you reach for `nonstatus--blue`, not `status--info`. **Reserved as `--ds-categorical-*` namespace in our system.** Not yet populated, but documented for when we add tag/topic colors that need visual variety without semantic weight.

36. **Surface hierarchy is multi-level (primary/secondary/tertiary) and orthogonal to elevation (raised/floating).** PatternFly distinguishes:
    - `primary` / `secondary` / `tertiary` — depth ROLE (which level of nesting)
    - `floating` — separately, ABOVE everything (menus, popovers)
    - `sticky` — separately, sticky-positioned (sticky headers)
    
    Three levels of stacked content, plus two special positions. **Different concepts.** Tertiary is "card on a card on a page." Floating is "menu that pops out and disappears." They look similar visually but have different layout semantics. Vendored as role aliases on top of our existing depth-based names.

37. **Skeleton loading, striped rows, and modal scrims deserve dedicated tokens.** Each is a recurring UI pattern with consistent design constraints. PatternFly has dedicated tokens for all three. **The lesson is broader: any UI pattern that recurs gets its own token.** Reserved as `--ds-bgColor-{backdrop,row-striped,skeleton,skeleton-subtle}` for when we add modals, striped tables, and skeleton loaders.

38. **Read/Unread/Attention is a three-state pattern, not two.** PatternFly has dedicated tokens for `read`, `unread`, AND `unread--attention` (unread + needs operator review). The third level is the key insight: there's a difference between "you haven't seen this yet" and "you haven't seen this yet AND it requires action." **For Exocortex**: when we add the resolution-pending notification system that surfaces "the resolver has proposed verdicts you should review," these read/unread/attention tokens are the right model.

39. **Glass blur should be a theme token, not a hardcoded value.** OpenGridWorks hardcodes `backdrop-filter: blur(20px) saturate(140%)`. PatternFly makes it `--background--filter--glass--blur--primary: blur(16px)` so themes can override it. **Adopted into `exocortex.css`** as `--ds-glass-blur-amount`. The `#hdr` and `#tabbar` declarations now reference the token instead of hardcoding the value. A future "performance mode" theme can set `--ds-glass-blur-amount: none` to disable backdrop-filter entirely.

40. **Charts have different design constraints than UI — they need their own token layer.** PatternFly ships a SEPARATE 173-line token file (`tokens-charts-dark.scss`) for chart-specific tokens: stroke widths, font sizes, layout dimensions, categorical color palette, sequential color scales for heat maps, and chart-specific status colors (note: chart success uses BLUE not green because green-on-dark has legibility issues!). Reserved as `--ds-chart-*` namespace in `exocortex.css`. **When we build calibration trends, hypothesis lifecycle visualizations, or any data viz, we should NOT just reuse UI tokens — we should add chart-specific tokens** that account for the different design constraints.

41. **Methodology refinement for production design systems with multiple token layers:** PatternFly ships base + dark + glass + highcontrast + charts as separate files (each is a "theme overlay" on the base). The right extraction approach is:
    1. Read the base tokens file first to understand the semantic structure
    2. Read each overlay file to see what each theme overrides (often surprisingly small — just the values that differ)
    3. The CHART layer is its own thing — read it separately, don't try to merge with UI tokens
    4. Compare against the previous reference (Primer) to identify what's NEW vs what's CONFIRMED
    
    PatternFly took ~50 minutes, comparable to Primer. The ratio of "new architectural insights" to "confirmed insights from previous references" was about 60/40 — meaningful new value, but diminishing as we accumulate more references.

42. **The third glass approach completes the trio.** We now have THREE references for glass effects:
    - **OpenGridWorks**: `backdrop-filter: blur(20px) saturate(140%)` — modern, hardcoded
    - **7.css**: stacked CSS gradients with no blur — period-authentic, cheap, static
    - **PatternFly**: `backdrop-filter: var(--theme-token)` — modern, theme-overridable
    
    Each has its place. PatternFly's approach is the most flexible because it allows runtime theme switching to disable or modify glass. **Adopted PatternFly's pattern** — glass blur is now a theme token in `exocortex.css`.

### 2026-04-14 — from Carbon extraction

43. **AI-generated content deserves its own visual treatment.** Carbon ships a dedicated `--cds-ai-*` token namespace for AI content used in IBM Watson products. The "aura" pattern — a gradient glow surrounding AI-generated UI — communicates **epistemic provenance at the UI level**. Users see at a glance which content came from AI inference vs deterministic logic. **For Exocortex this is HIGHLY RELEVANT** because we have AI-generated content all over: hypothesis explanations, swarmfish committee predictions, resolver verdicts, operator briefs, calibration narratives. We have ZERO visual treatment that marks LLM-generated vs deterministic content — until tonight. **Vendored as `--ds-ai-*` namespace** with `.ds-ai-content` and `.ds-ai-label` utility classes. Applied to the Resolver Proposal box and the operator brief in the Pending tab. The visual difference IS the message — operators can now see which content needs epistemic skepticism applied. **This connects directly to the existing Epistemic Integrity Layer in the backend.** We had deterministic fact-checking for AI outputs; now we also have visual provenance signaling.

44. **Three caution levels, including "undefined" (purple).** Carbon's status system has the standard four (success/warning/error/info) PLUS three caution levels: Minor (yellow), Major (orange), and **Undefined (purple)**. The undefined level is for situations where you've detected something off but can't classify it. **For Exocortex this maps directly onto the resolver's `still_pending` verdict.** When the autonomous resolver says "I cannot determine confirmed/falsified from available evidence," that's not "info" (which implies a known neutral state) — it's "indeterminate." **Vendored as `--ds-state-undefined: #a78bfa`** (purple). Available for application to the resolver still_pending verdict UI.

45. **Numbered layer system as an alternative to role-based naming.** Carbon's `layer-01` / `layer-02` / `layer-03` is comparable to PatternFly's `primary` / `secondary` / `tertiary` — same three depth levels but named differently. Carbon's distinctive addition: each layer has SIX state variants (default/active/background/hover/selected/selected-hover) instead of PatternFly's THREE (default/hover/clicked). Carbon also has the **auto-promote rule** — a `layer-01` nested inside another `layer-01` automatically becomes a `layer-02` via Sass mixins. **NOT vendored** because we don't have a Sass build pipeline. But the lesson is documented: when nesting goes beyond 2 levels, auto-promotion prevents the "I forgot which layer I'm on" problem.

46. **Helper text token** (`text-helper`) for explanatory text below form inputs. Sits between `text-secondary` and `text-disabled` in contrast — readable but doesn't compete with the input itself. Carbon recognized this as its own UI pattern; Primer and PatternFly don't have it. **Vendored as `--ds-text-helper: #8a96a8`**.

47. **Icon tokens are parallel to text tokens, not a subset.** Carbon ships `icon-primary`, `icon-secondary`, `icon-on-color`, `icon-disabled`, etc. as separate tokens from `text-*`, even when the values happen to match. The reasoning: icons need different contrast than text because they're smaller. Having parallel tokens means a future accessibility update can adjust icon colors without affecting text. **NOT vendored** (overhead vs benefit at our scale) but documented as a forward-compatibility move.

48. **Computed token values via build-time functions.** Carbon's source uses `adjustAlpha(gray50, 0.4)` and `adjustLightness(background, 7)` to derive token values from base colors. This makes token relationships explicit ("skeleton background is 7% lighter than the page background") instead of hardcoded. Requires a build step. **NOT vendored** — would require adding a Sass/JS build pipeline. Documented as a pattern for when token relationships matter more than literal values.

49. **Carbon ships AI tokens, PatternFly ships chart tokens, Primer ships neither.** Each production design system has ONE distinctive concept the others lack:
    - **Primer**: intensity triplet (default/muted/emphasis)
    - **PatternFly**: chart token layer + status/nonstatus partition
    - **Carbon**: AI tokens + caution-undefined + layer-NN system
    
    A complete design system would combine all three. **`exocortex.css` now contains the synthesis** — Primer's intensity, PatternFly's interaction state + chart reservation, Carbon's AI tokens + caution-undefined. We're past the point where any individual reference can offer dramatically new patterns; the marginal value per reference is approaching saturation.

50. **Methodology note for JS-source design systems**: Carbon's source is JavaScript (`g100.js`) with imported color constants and per-theme value lookups. Extraction required:
    1. Find the canonical theme file (`g100.js` for deepest dark)
    2. Read it linearly to understand the structure
    3. Cross-reference imports to resolve color constant names to hex values
    4. Read the v11 token group definition file (`v11TokenGroup.js`) for the canonical group taxonomy
    5. Spot-check component-level token files for the layering pattern
    
    Total time: ~50 min, comparable to Primer and PatternFly. **The pattern: production design systems take 45-60 min each regardless of source format**, because most of the time is spent understanding architectural intent, not enumerating values.

### 2026-04-14 — from Vanilla Framework extraction

51. **W3C Design Tokens Format Module exists and Vanilla is the only reference using it.** The other production systems use vendor-specific source formats: Primer (JSON5), PatternFly (SCSS), Carbon (JS). Vanilla uses the W3C standard JSON format with `$type`, `$value`, and dot-path references. The trade-off: vendor-specific formats can be richer but require custom tooling; W3C format is portable across Figma plugins, Tokens Studio, and other design-token tools. **For Exocortex**: we don't have a build pipeline at all (we hand-write CSS). But if we ever want to share tokens between code and design tools, the W3C format is the only choice with cross-tool support. Documented as a future-portability move.

52. **Explicit `themeable` metadata field is a documentation pattern.** Every Vanilla token has `themeable: true|false`. Most are themeable; some (brand identity, base colors) are not. The metadata declares **which tokens the design system OWNS** (and shouldn't be overridden) vs which are intentionally customizable. **For Exocortex**: when we eventually add multi-theme support, we should mark `--ds-accent-cyan`, `--ds-ai-*`, and `--ds-state-undefined` as non-themeable because they ARE our identity. Documented in `exocortex.css` as a guideline (no enforcement mechanism — just discipline).

53. **`text.muted` vs `text.inactive` is a principled distinction.** Vanilla has THREE less-prominent text states where most systems have two: default (100%), muted (60%), inactive (75%). The brighter "inactive" is for elements that exist and matter but are currently dormant — unselected tabs, closed expansion headers, button labels in the rest state of a panel. The dimmer "muted" is for content that's intentionally subtle — helper text, captions, metadata. **Vendored as `--ds-text-inactive` and applied to the panel's tab navigation.** Unselected tabs now use `inactive` (brighter, still readable), selected tabs use `accent-cyan`. Subtle but principled.

54. **Vanilla is the smallest production design system but not the least valuable.** The library now has four production design systems with distinctive contributions:
    - **Primer**: intensity triplet
    - **PatternFly**: interaction state triplet
    - **Carbon**: AI tokens + caution-undefined
    - **Vanilla**: W3C standard format + themeable metadata + text-inactive distinction
    
    Each filled a gap the others left. **Vanilla's contributions are smaller in scope but each one is principled** — a small refinement that improves the overall system without major restructuring. The smallest extraction had the highest signal-to-noise ratio.

55. **Lighter base dark themes for documentation-heavy interfaces.** Vanilla's base is `#262626` (15% lightness), much lighter than Carbon `#161616`, Primer `#0d1117`, or our own `#060810`. Canonical's preference for less-extreme contrast is calibrated for **long-form reading**. Their products (ubuntu.com, snapcraft.io) are documentation-heavy; pure black is fatiguing. **For Exocortex**: our `#060810` is the right call for a dashboard (data should pop). But if we ever add a long-form reading view (analyst notes, hypothesis lineage essays), it might benefit from a lighter background variant. Not vendored; documented as a future consideration.

56. **Phase 2 is COMPLETE.** Four production design systems analyzed (Primer, PatternFly, Carbon, Vanilla). The reference library contains comprehensive design vocabulary across every major architectural axis identified in the literature. Further production design systems would mostly confirm patterns rather than introduce new ones — the marginal value per reference has plateaued. **The next valuable work is APPLICATION** — going through the OSS panel and migrating components to use the patterns we've graduated, especially the AI content treatment for LLM-generated content and the state-undefined purple for resolver still_pending verdicts.

57. **Methodology lesson: Phase 2 references averaged ~45 minutes each** (Primer 45min, PatternFly 50min, Carbon 50min, Vanilla 30min). The variation is driven less by reference SIZE than by source FORMAT and the depth of architectural insights to discover. Vanilla was fastest because the W3C JSON format is the most parseable and Vanilla's smaller scope meant fewer unique patterns to understand. Carbon was the most valuable per-minute because of the AI tokens discovery.

### 2026-04-14 — from Tufte CSS extraction

58. **Tufte CSS is the philosophical opposite of every other reference.** Where every production design system + OpenGridWorks gives us dense radar-screen UI with motion and glow, Tufte CSS gives us calm long-form reading with marginal annotations. NO animations, NO transitions, NO shadows, NO gradients, NO backdrop-filter, NO custom properties. Five colors total in the entire 451-line library. The whole thing is print-aesthetic translated to web. **It teaches us about CALM as a design value** — when the content is the visual signal, the chrome should disappear. For dashboards (the OSS panel) this is the wrong call. For long-form content views (analyst notes, post-mortem narratives, hypothesis lineage essays) it's exactly right. The library now contains references for both ends of the design spectrum.

59. **The sidenote pattern is one of the most clever uses of CSS counters in the wild.** Tufte's signature: footnotes that float in the right margin next to the text that references them, auto-numbered via CSS counters with zero JavaScript. The CSS counter increments automatically as inline `.sidenote-number` elements appear, and the same counter renders as a prefix in the marginal `.sidenote` element. **HIGHLY relevant to Exocortex** for future features like resolver verdicts with cited claims, hypothesis explanations with provenance, calibration narratives with Brier-score citations. **Vendored as `.ds-sidenote-host`, `.ds-sidenote-number`, `.ds-sidenote` in `exocortex.css`** with responsive fallback for narrow viewports. Reserved for application when we add inline-citation features.

60. **Old-style vs lining numerals is a typographic detail almost no web framework implements.** "Lining numerals" are uniform-height (capital height: `1234567890`). "Old-style numerals" have descenders so 3, 4, 5, 7, 9 hang below the baseline like lowercase letters. **Tufte uses old-style for prose** so numbers blend with words, **lining (tabular) for tables** so columns align. We already use `tabular-nums` for stat displays. Adding `oldstyle-nums` for inline numbers in prose contexts is a refinement worth knowing — but only effective when the font supports OpenType `oldstyle-nums`. IBM Plex Mono does; most monospace fonts don't. Documented as `.ds-numeral-prose` utility.

61. **The newthought small-caps pattern is lighter than a heading, more meaningful than a paragraph break.** Tufte's signature: a paragraph that begins a new section starts with a few words in small caps. Useful when content is organized by theme but doesn't need explicit headings. **Vendored as `.ds-newthought`** for use inside long-form LLM-generated content (resolver verdicts, hypothesis explanations) where natural section breaks need marking without explicit headers.

62. **"Calm mode" as a design value distinct from "instantaneous state."** TuiCss's no-animation philosophy is "state is binary, snap to it instantly" — appropriate for status indicators that should never lie. Tufte's no-animation philosophy is "the content is the signal, don't compete with it" — appropriate for long-form reading. **Both arrive at the same CSS (`transition: none`) for opposite reasons.** The same technique can serve different design philosophies. Vendored as `.ds-calm-mode` (parallel to TuiCss's `.ds-instant-state`) for any future long-form reading view.

63. **The reading-column constraint** (~65ch / 55% width) **is essential for any long-form text view we add.** Long lines of text are hard to read; cap at 60-70 characters per line. Vendored as `.ds-reading-column` with `max-width: 65ch`. Currently unused — reserved for future analyst notes view, hypothesis lineage essays, post-mortem narratives.

64. **The Tufte sidenote pattern + Carbon AI content treatment compose beautifully.** Imagine a resolver proposal that uses `.ds-ai-content` for the cyan aura (marking it as LLM-generated) AND uses `.ds-sidenote` for the cited claims (marking each citation in the margin next to its inline reference). The two patterns from completely different references (Carbon for AI provenance, Tufte for marginal annotation) compose without conflict because they target different concerns: one marks WHERE content came from, the other marks WHAT supports it. **This is the kind of synthesis that emerges from a diverse reference library** — patterns from different traditions stack instead of competing.

65. **Methodology note: Phase 3 references take ~25 minutes each.** Tufte was the smallest extraction yet (451 lines, single file). The bulk of the time was thinking about how each pattern would translate to a dark-theme dashboard context (most don't) and which ones to graduate (a small but high-value subset). **The pattern: aesthetic-distinctive references take less time than production design systems** because they have fewer tokens but more concentrated philosophical content.

### Decisions log

Patterns that have graduated into [`exocortex.css`](exocortex.css) with source lineage:

| Pattern | Source | Notes |
|---------|--------|-------|
| Full `--ds-*` token set (timings, easings, radii, surfaces, text, borders, accents, signals, shadows) | opengridworks | Adapted: blur reduced 32px→20px (GPU budget), light-mode tokens omitted (Exocortex is dark-only), Avenir Next removed (paid font) |
| `.ds-cyan-signal` hover/active interaction pattern | opengridworks | Applied to every `.btn` in the OSS panel and daemon bootstrap |
| Glass panel via `backdrop-filter` | opengridworks | Applied to `#hdr` and `#tabbar` in OSS panel |
| Radial-gradient body backdrop (so glass has something to blur) | our invention (informed by opengridworks's map-backdrop pattern) | Body uses `radial-gradient(ellipse at 20% 0%, rgba(0,229,255,0.03)...)` to give panels a gradient substrate |
| Tabular numerals + small-caps section headers | opengridworks | Applied to `.sec` and `.stat-n` in OSS panel |
| `.ds-instant-state` utility (disable transitions on truth-bearing elements) | tuicss | Available in `exocortex.css`, not yet applied to OSS panel — needs decision on which elements qualify as "truth-bearing" |
| `.ds-hard-shadow` / `.ds-hard-shadow-lg` utilities | tuicss | Available, not yet applied — reserved for retro-mode contexts |
| Full `--tui-*` 16-color CGA/EGA palette namespace | tuicss | Reserved for opt-in deep retro mode. Not used in default UI but available for categorical color or aesthetic switching |
| Z-index layer scale (`--ds-layer-1..5`, `--ds-layer-overlay`, `--ds-layer-modal`, `--ds-layer-toast`, `--ds-layer-important`) | openprops | Replaces ad-hoc z-indices with named intent |
| Supplemental easing curves (`--ds-ease-circ-out`, `--ds-ease-expo-out`, `--ds-ease-quart-out`, `--ds-ease-bounce`) | openprops | Adds personality variants to the OpenGridWorks easing set |
| Animation preset library (`--ds-anim-fade-in`, `--ds-anim-slide-in-up`, `--ds-anim-shake-x`, `--ds-anim-pulse`, `--ds-anim-blink`, etc.) + their @keyframes | openprops | 8 prebuilt animation shorthand strings for common effects (content reveal, attention marker, error feedback) |
| `--ds-noise` SVG fractal noise texture | openprops | **REJECTED 2026-04-14**: Tested at .04 opacity on dark theme, produced visible "oatmeal" pattern that read as display corruption. Token preserved in `exocortex.css` for documentation but NOT applied to any surface. If reattempted, use opacity ≤.015 and higher baseFrequency (.65+) for finer grain — and visually verify before shipping. |
| `.ds-aero-glass` (gradient-based glass alternative to `backdrop-filter`) | 7css | Fallback for hardware where backdrop-filter is expensive, or for elements without content behind them to blur |
| `.ds-warm-hover` (asymmetric 0.3s in / 1s out) + `--ds-duration-warm-in/out` | 7css | Opt-in for primary CTAs and welcome panels — NOT applied as a default |
| `.ds-default-pulse` + `@keyframes ds-default-pulse` (cyan inner glow breathing) | 7css | Aero's "press Enter to do this" affordance, adapted to use our --ds-accent-cyan-glow |
| `.ds-hard-stop-gradient` (Aero signature two-tone surface) | 7css | Adapted to dark theme. Reserved for cards/panels that should read as physical surfaces |
| Triplet pattern: `--ds-signal-{positive,negative,warning,info}-emphasis` | primer | Third intensity level alongside default and muted. Enables "subtle hover tint" + "active button background" + "text color" all from same category |
| Semantic state aliases: `--ds-state-{confirmed,falsified,pending,still-pending,running,paused,stopped}` | primer | Decouple semantic intent from visual implementation. Pending tab and Hypotheses tab can now reference `--ds-state-confirmed` instead of `--ds-signal-positive` |
| Text-on-background pairing: `--ds-text-on-{emphasis,accent,positive,negative,warning,info}` | primer | Solves the contrast pairing problem at the token level. Cyan one is dark (`#060810`) because cyan is too light for white text |
| Role-based shadow scale: `--ds-shadow-{resting,floating,inset}-*` | primer | Replaces numeric scale with intent-bearing names. Floating shadows include a 1px hairline border baked in via `0 0 0 1px` first stop. Legacy `--ds-shadow-{sm,md,lg}` aliases preserved |
| Theme-swap pattern documented (variables ARE the abstraction layer) | primer | Future themes (deep retro, high contrast) ship as separate files with same `--ds-*` names, swapped via `data-theme` attribute |
| Interaction state triplet: `--ds-state-{confirmed,falsified,pending}-{rest,hover,clicked}` | patternfly | Orthogonal to Primer's intensity triplet. Default/hover/clicked variants for the most active categories. Most categories use only the rest+hover+clicked combination on default intensity |
| Surface role aliases: `--ds-surface-{primary,secondary,tertiary,floating,sticky}` | patternfly | Role-based names alongside our existing depth-based names. New code can use either |
| Special-purpose backgrounds: `--ds-bgColor-{backdrop,row-striped,skeleton,skeleton-subtle}` | patternfly | Reserved tokens for modal scrims, alternating tables, skeleton loaders. Available for future UI features |
| Glass blur as theme token: `--ds-glass-blur-amount` | patternfly | Replaces hardcoded `blur(20px) saturate(140%)` in `#hdr` and `#tabbar`. Future "performance mode" theme can override to `none` |
| `--ds-categorical-*` namespace reservation | patternfly (status vs nonstatus distinction) | Documented but not populated. For future tag/topic colors that need visual variety without semantic weight |
| `--ds-chart-*` namespace reservation | patternfly (charts as separate token layer) | Documented but not populated. For future calibration trends and data viz where chart constraints differ from UI |
| `--ds-ai-*` namespace + `.ds-ai-content` + `.ds-ai-label` (the AI aura pattern) | carbon | **Most important Phase 2 finding.** Visual marker for LLM-generated content. Applied to Resolver Proposal box and operator brief in Pending tab. Communicates epistemic provenance at the UI level — operators can see which content needs skepticism applied. Connects to the existing Epistemic Integrity Layer in the backend |
| `--ds-state-undefined: #a78bfa` (purple — caution-undefined) | carbon | Maps directly onto resolver `still_pending` verdict. More semantically honest than info blue: "I don't know yet" vs "neutral information" |
| `--ds-text-helper: #8a96a8` | carbon | For explanatory text below form inputs. Sits between text-secondary and text-tertiary in contrast |
| `--ds-text-inactive: rgba(176,184,200,.75)` | vanilla | Distinct from text-tertiary/muted. For dormant-but-readable elements. Applied to unselected tab navigation in OSS panel |
| W3C Design Tokens Format documentation | vanilla | Documented as a future-portability move. We don't have a build pipeline today, but if we ever want to share tokens with design tools, the W3C format is the only portable choice |
| `themeable` metadata pattern documentation | vanilla | Documented in `exocortex.css` as a guideline. Marks which tokens are part of Exocortex's identity (--ds-accent-cyan, --ds-ai-*, --ds-state-undefined) and shouldn't be overridden by future themes |
| Tinted border namespace reservation | vanilla | `--ds-border-tinted-{positive,negative,warning,info}` reserved for softer status borders if needed |
| Brand identity namespace reservation | vanilla | `--ds-brand-exocortex` reserved for any future Exocortex visual mark/wordmark |
| `.ds-newthought` (small-caps section break) | tufte | For long-form LLM content where natural section breaks need marking without explicit headings |
| `.ds-reading-column` (`max-width: 65ch`) | tufte | For any future long-form text view (analyst notes, post-mortem narratives, hypothesis lineage essays) |
| `.ds-calm-mode` (disable transitions/animations on content) | tufte | Distinct from `.ds-instant-state` (TuiCss). Calm mode is for content the user reads carefully; instant-state is for truth-bearing indicators |
| `.ds-numeral-prose` (`oldstyle-nums`) | tufte | For inline numbers in body text. Only effective when font supports OpenType old-style figures (IBM Plex Mono does) |
| `.ds-sidenote-host` + `.ds-sidenote-number` + `.ds-sidenote` (CSS-counter marginal annotations) | tufte | Reserved for future features with inline citations: resolver verdicts with cited claims, hypothesis explanations with provenance, calibration narratives with Brier-score citations. Uses CSS counters for auto-numbering, no JavaScript required |

Patterns rejected or deferred:

| Pattern | Source | Why not |
|---------|--------|---------|
| 32px backdrop blur | opengridworks | Too expensive on weaker GPUs; reduced to 20px |
| Avenir Next display font | opengridworks | Paid font, Inter fallback works fine |
| Categorical fuel-type color palette | opengridworks | Domain mismatch — our semantics are "stages of a process" (staged/promoted/falsified), not "types of a thing" |
| Hexagonal minimap | opengridworks | Nothing to put in a second view |
| Custom DOS bitmap font | tuicss | Renders poorly at non-native sizes on modern displays. IBM Plex Mono fallback gives "monospace feel" without the rendering issues |
| Full-saturation bright-8 colors at default | tuicss | Eye-searing on LCDs. Worked on CRTs because phosphor softened them. Use the dimmer base-8 colors (intensity 168) for normal use; bright-8 only as emphasis accents |
| Inline-block component layout | tuicss | Doesn't compose with modern flexbox/grid. Architectural mismatch with our existing layout |
| Hard drop shadows on every element | tuicss | The aesthetic only works if it's the whole interface. Mixed with modern soft shadows it looks broken. Available as `.ds-hard-shadow` for opt-in usage only |
| Open Props 17×13 color palettes (221 color tokens) | openprops | Overlap with our existing signal/accent palette from OpenGridWorks. Adding 221 more would clutter the namespace without value |
| Open Props OKLCH `--color-*` palette generator | openprops | Powerful but overkill — we know exactly which colors we want, no need for runtime palette computation |
| Open Props 31 named gradient presets | openprops | Aesthetic-specific (sunsets, conic rainbows). None match our cyan/violet palette |
| Open Props inner shadow library | openprops | Inner shadows are for inset/pressed/sunken effects — not part of our visual vocabulary |
| Open Props 56 font tokens (15 named font stacks + 9 weights + line-heights + letter-spacings + sizes) | openprops | We use IBM Plex Mono with system fallback. Switching now would be churn for no benefit |
| Open Props blob/drawn radius variants | openprops | Gimmicky. Standard radius scale is sufficient |
| 7.css full Aero color palette (light theme, gray + blue) | 7css | Our panel is dark-only. Aero is fundamentally light-theme — gradient highlights only work when light hits surfaces from above |
| 7.css `--w7-w-glass` 50-line stripe pattern | 7css | Period-specific wallpaper sheen. Doesn't suit intelligence-console aesthetic |
| 7.css 3px universal border-radius | 7css | Aero's signature softness from this rounding. Our `--ds-radius-sm: 6px` is more modern |
| 7.css window control button styling (`--w7-wct-*`) | 7css | We have no equivalent of OS window chrome buttons in our flat panel |
| Stacked-pseudo-element state layering technique | 7css | Documented as a *technique* in 7.css notes but not vendored — requires per-component HTML structure rather than being a pure CSS token. May graduate later if we adopt richer button styling |
| Primer's 41-group prefix taxonomy | primer | Most are GitHub-internal: `--label-*` (133), `--display-*` (285, markdown rendering), `--diffBlob-*`, `--codeMirror-*`, `--contribution-*` (the green squares), `--reactionButton-*`, `--buttonKeybindingHint-*`. Adopting their full taxonomy would be cargo-culting GitHub product specifics |
| Primer's 8 dark theme variants (regular, dimmed, high-contrast, 3 colorblindness modes, plus tritanopia) | primer | Overkill for a one-builder system. We need one dark theme. Variants exist for accessibility and can be added single-purpose if/when needed |
| Style Dictionary build pipeline | primer | We don't have a build pipeline for CSS. Tokens live directly in `exocortex.css` and the embedded panel CSS. Adding Style Dictionary would be premature abstraction |
| Primer's GitHub-blue accent palette (`#1f6feb`) | primer | We use OpenGridWorks cyan (`#00e5ff`) which suits the intelligence-console aesthetic better. The Primer blue is too cool |
| PatternFly deep hierarchical naming (`--pf-t--global--background--color--status--success--default`) | patternfly | Extremely explicit but very verbose (avg 7 segments). Our convention (`--ds-bgColor-success-emphasis`) compromises by using camelCase to compress while preserving hierarchy |
| PatternFly's 136 nonstatus tokens (8 hues × multiple intensities × multiple properties) | patternfly | We don't have a use case for that many categorical colors yet. Pattern reserved as `--ds-categorical-*` namespace; tokens not vendored |
| Full PatternFly status matrix (5 categories × 3 properties × 3 states × 2 intensities = 90 status tokens) | patternfly | We graduated a subset (3 categories × 3 states = 9 new tokens). Adding the full matrix would be premature without proven usage |
| PatternFly chart token file (173 lines) | patternfly | Reserved as `--ds-chart-*` namespace. Will graduate when we actually build charts |
| PatternFly directional shadows (`shadow--md--directional` for shadows implying directional light) | patternfly | Polish move with limited value at our scale. We use Primer's role-based shadows instead |
| PatternFly Red Hat brand palette (red/blue/yellow) | patternfly | Cyan accent fits intelligence-console aesthetic better |
| PatternFly high contrast theme variants | patternfly | Single dark theme is sufficient. Accessibility variants can be added single-purpose if/when needed |
| Carbon's full numbered layer system (layer-01/02/03 with auto-promote via Sass mixins) | carbon | Requires Sass build pipeline. We use PatternFly's explicit role aliases instead |
| Carbon's per-layer border tokens (9 borders: 3 weights × 3 layers) | carbon | Refinement we don't need at our scale. Our borders are uniform across surfaces |
| Carbon's blue accent palette | carbon | Cyan from OpenGridWorks fits intelligence-console aesthetic better |
| Carbon's 80+ syntax highlighting tokens | carbon | We don't have code editing in Exocortex |
| Carbon's component-level token files (button, notification, tag, status, content-switcher) | carbon | Component count is small enough to define tokens inline |
| Carbon's full link state matrix | carbon | We have very few links in the panel. Existing accent color is sufficient |
| Carbon's JS-based token source format | carbon | Would require build pipeline |
| Carbon's white/g10 light theme variants | carbon | Exocortex is dark-only |
| Carbon's adjustAlpha() / adjustLightness() computed token values | carbon | Requires build pipeline. Worth knowing for cases where token relationships matter, but not adopted |
| Carbon's icon-NN tokens parallel to text-NN tokens | carbon | Forward-compatibility move for accessibility. Marginal benefit at our scale |
| Vanilla's W3C JSON source format | vanilla | We hand-write CSS; no build pipeline. Adopting W3C JSON would require a build step. Documented as a future option |
| Vanilla's positive/negative/caution/information vocabulary | vanilla | Slightly more flexible than success/danger/warning/info but renaming would be churn for marginal gain. We keep our current vocabulary |
| Vanilla's lighter `#262626` base background | vanilla | Our intelligence-console aesthetic benefits from the deeper `#060810`. Vanilla's preference for less-extreme contrast doesn't suit our domain |
| Vanilla's Ubuntu orange / Canonical brand identity | vanilla | We have our own visual direction (cyan accent) |
| Vanilla's nested component tokens (text.button.{brand,default,base,positive,negative}) | vanilla | We already have `--ds-text-on-{accent,positive,negative,warning,info}` from Primer with simpler naming |
| Vanilla's range-specific disabled opacity | vanilla | We don't have sliders. Reserved as a pattern for future use |
| Vanilla's full Style Dictionary build pipeline | vanilla | Same reasoning as the other production systems — premature abstraction |
| Tufte's cream-white background (`#fffff8`) | tufte | We're dark-themed |
| Tufte's serif body font (ET Book + Palatino fallback) | tufte | We use IBM Plex Mono. Serif fonts feel out of place in a technical dashboard |
| Tufte's italicized headings (h2, h3 italic) | tufte | We don't have prose headings in the panel |
| Tufte's figure/figcaption float-right pattern | tufte | We don't have figures in the panel |
| Tufte's mobile checkbox-toggle for sidenotes | tufte | We don't target mobile |
| Tufte's 55% global reading width constraint applied to entire page | tufte | Dashboards want full-width data displays. We use the constraint only on opt-in `.ds-reading-column` containers |
| ET Book font files | tufte | Not free for all uses; renders poorly at small sizes on dark backgrounds. Palatino fallback is sufficient when needed |
| Tufte's italic blockquote/epigraph pattern | tufte | We don't have chapter structure or epigraphs in dashboard UI |
| Tufte's minimal 5-color palette applied to everything | tufte | We need more colors to distinguish concurrent states. Tufte's discipline applies to single-content reading; dashboards need vocabulary |

---

## How to use this document

**When adding a new reference:**
1. Drop it into the appropriate phase table with a short "why" and priority
2. Status starts as ⏳ Pending
3. When analyzed, change to ✅ with a date and links to the extracted files

**When graduating a pattern into `exocortex.css`:**
1. Add an entry to the Decisions log with the pattern name, source, and any adaptations
2. In `exocortex.css`, include a comment above the pattern noting which reference it came from

**When rejecting a pattern:**
1. Add it to the Decisions log rejected section with the reason
2. Don't just delete it — a documented rejection saves future-you from reconsidering

**When you find a new reference in the wild:**
1. Drop the URL into the Open backlog section with a one-sentence "why this caught my eye"
2. Next session, Kestrel picks it up, decides which phase it belongs in, and either queues or analyzes
