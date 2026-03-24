# AESTHETICS_DESIGN_BRIEF.md
# UI Aesthetics Brief and Design System Foundation: Exocortex Interface

*Synthesized from deep research into game UI design, motion design, typography, color theory, materiality, and the craft vocabulary of exceptional interfaces. Companion to WEBUI_DESIGN_BRIEF.md (functional/safety principles). This document governs feel, not just function.*

*Reference works: Persona 5, Persona 3 Reload, NieR: Automata, Metal Gear Solid V: The Phantom Pain, Metal Gear Solid 3 Snake Eater / Delta, Bravely Default.*

---

## 1. The Aesthetic Stakes

Aesthetics are not decoration. Don Norman's three-level model of emotional design establishes this empirically: the **visceral** level (pre-conscious response to appearance) is processed before behavioral interaction begins and shapes how capable users believe the system is before they have used it. Beautiful interfaces are rated as more usable, more trustworthy, and more capable than functionally identical ugly ones — even when users are told that only function matters. This is not irrationality. It is the brain making probabilistic inferences: systems built with care in one dimension are more likely to have been built with care in all dimensions.

The implication for Exocortex: aesthetic quality is not a reward for completing the functional work. It is part of the functional work. An interface that looks powerful but feels uncertain to use fails in both directions.

The three levels, applied:

| Level | What it processes | Interface implication |
|-------|------------------|----------------------|
| **Visceral** | Shape, color, proportion, first impression | The look of the interface before interaction — typography, palette, motion on load |
| **Behavioral** | Usability, feedback, responsiveness | The feel of using it — does it respond correctly, does it feel like a professional tool |
| **Reflective** | Meaning, narrative, self-image | Does using this interface make the analyst feel like a professional doing important work |

All three levels must be designed. Visceral and reflective are typically abandoned after behavioral is addressed. This is the design failure that separates adequate interfaces from exceptional ones.

---

## 2. The Diegetic Principle

The most important distinction in game UI that applies to software is **diegesis** — whether interface elements exist within the conceptual world of the software or are overlays on top of it.

**Non-diegetic** elements are honest overlays: they belong to the software convention, not to a narrative. Most software UI is entirely non-diegetic — windows, tabs, buttons, status bars. These are fine. The problem is that they accumulate with no unifying logic, and the result looks like a toolbox rather than an instrument.

**Diegetic coherence** — the principle that applies to software without requiring fiction — means that every element should feel like it belongs to the same world, obeys the same physical rules, and was made by the same hand. In NieR: Automata, the interface is diegetically justified (it is YoRHa's android OS), but the diegetic principle works for software too: the Exocortex interface should look and feel like it was built by an intelligence organization for professional analysts. Not like a web app assembled from components.

This is the **unified aesthetic world** principle. Every element should fit a consistent register. The register is a choice — but once chosen, every element is evaluated against it.

---

## 3. The Reference Games: What They Teach

These are not aesthetics to copy. They are studied examples of specific design decisions executed without compromise. Each teaches something different.

### 3.1 Persona 5 — UI as Identity

Art director Masayoshi Sutou's design philosophy: the interface is the game's first and most economical marketing tool. Before a player understands what Persona 5 is, the UI has already told them: this is aggressive, this is confident, this is different.

**What makes it work:**

- **Palette restraint with maximal contrast.** Primary: white, black, red. No sub-colors compete with red. The restriction is the power. Every use of red is immediately important because nothing else is red. When you add a fourth color, you dilute the third.
- **Typography as attitude.** The typeface choices read as ransom-note cut-outs, activist posters, POST NO BILLS signage. The type is not neutral — it has a graphic register. Heavy weights, compressed forms, sharp diagonals. The type and the palette agree on the same personality.
- **Motion as punctuation.** Transitions are not smooth fades — they are cuts, slashes, impacts. The animation vocabulary uses the same energy as the palette. A slow dissolve would be tonally wrong.
- **No wasted space, but no fear of space.** The composition is asymmetric, aggressively structured. Elements are not centered unless centering makes a statement. Diagonals break the grid deliberately.
- **The UI is always present.** Sutou made the decision to animate the menu rather than make it invisible. The menu is part of the game's identity, not an interruption of it.

**The lesson:** Pick a register. Commit to it in every dimension simultaneously — palette, type, motion, composition. Partial commitment produces visual confusion.

### 3.2 NieR: Automata — The Interface That Believes It Exists

Designer Hisayoshi Kijima's concept: "systematic and sterile but beautiful." The interface is YoRHa's android operating system. It believes it exists within the game's world. Players are using 2B's HUD, not a game's HUD.

**What makes it work:**

- **Monochrome with tactical color.** The palette is warm beige (Yoko Taro's specific direction — not cold grey), with selective use of white for active elements and near-black for backgrounds. Color exists only to carry meaning: HP is a specific shade. Enemy indicators are another. Nothing is colored for decoration.
- **The loading screen is diegetic.** When the game loads, it shows a YoRHa boot sequence. The player is not waiting for a game to load — they are watching 2B's systems initialize. This is not expensive to implement; it costs almost nothing. The payoff is that the threshold between interface and game world blurs.
- **Distress as intentional texture.** The interface has deliberate imperfections — slight misalignments, scan line effects, CRT-era artifacts. These are not errors; they are worldbuilding. They signal that this technology has history, has wear. Clean and perfect interfaces have no weight. Slightly distressed interfaces feel real.
- **Plugin chips as UI-as-gameplay.** The ability system uses chips that physically rearrange the HUD. The inventory is the interface. The player's relationship with the UI is a relationship with 2B's system. This is the deepest form of diegetic design — the UI is a game mechanic.
- **Restraint in information density.** The HUD shows very little. HP, map suggestion, targeting. Everything else is hidden until needed. The restraint makes each UI element feel considered.

**The lesson:** Know your fiction, even in software. The Exocortex is an intelligence analysis tool. The interface should feel like it was built for that purpose by people who take that purpose seriously. The register is tactical, not consumer.

### 3.3 Metal Gear Solid V / MGS3 — Tactical Authenticity

Hideo Kojima's design mandate for MGS3's interface: it should look like it was made in 1964. The CIA/KGB cold war spy aesthetic — era-accurate equipment, period typography, operational display language — was not decoration. It was the world the player was inhabiting.

MGS5's iDroid was inspired by the "Dark Star" instrument cluster — operational, amber-tinted, information-dense but parseable. The HUD establishes military credibility: information that a field operative would need, displayed the way operational tech would display it.

**What makes it work:**

- **The amber/green operational palette.** Terminal screens, radar displays, night-vision overlays — the green phosphor / amber LCD palette reads immediately as "serious operational technology." This is a learned cultural association: these colors mean surveillance, intelligence, precision instruments.
- **Typography as period signal.** Stencil lettering, condensed sans-serifs, military label fonts. The type looks like it was stamped onto equipment. It communicates: this was built for function, by people who know what they are doing.
- **Mission briefings as TV broadcasts.** MGS5 presents information as intercepted broadcasts and tape recordings. The framing device changes the relationship to information — you are not reading a UI, you are receiving intelligence. The format is the message.
- **Information density calibrated to professional use.** The interface is not minimal. It shows everything an operator needs. But it is organized: information has consistent zones, consistent formats, consistent visual language.

**The lesson:** The Exocortex has a clear operational world. The analyst is running intelligence analysis on an AI agent. The interface should look like it was built by people who understood that operational context — not borrowed from a consumer chat app.

### 3.4 Bravely Default — Material Depth and Warmth

Where NieR is cool and systematic, Bravely Default is warm and layered. The menu system uses physical depth — cards stacked behind cards, parchment textures, ornamental borders — to communicate information hierarchy through material metaphor.

**What makes it work:**

- **Layering as hierarchy.** The most important information is closest to the viewer in the z-axis. Supporting information recedes. This is skeuomorphism done correctly: the physical metaphor carries functional meaning.
- **Warm palette with cool accents.** Parchment, warm ivory, amber gold — the primary tones feel tactile. Cool blue-white is reserved for highlights, creating contrast that reads as focused attention.
- **Ornamentation as identity.** Borders, filigree, decorative elements — these are not wasted space. They establish that this is a crafted object, not a generated one. The ornamentation says: someone made this.
- **Transitions as page turns.** Menu transitions reference book-turning, card-drawing, physical revealing. The motion vocabulary is consistent with the material vocabulary.

**The lesson:** Warmth and material depth are their own register. If the interface is meant to feel like a workshop — a place where a craftsman works — texture and layer are appropriate. Cool, clinical interfaces communicate precision; warm, material interfaces communicate care.

---

## 4. Motion: The Physics of Feel

Motion is the dimension that most separates perceived quality. A mediocre static design becomes premium with excellent motion. An excellent static design becomes cheap with mediocre motion.

### 4.1 The Foundational Principles (Disney, adapted for UI)

Disney's 12 Principles were developed for character animation but encode physical truth that applies to any motion:

**Squash and Stretch:** Objects deform under force. A button pressed should compress slightly, releasing with a micro-expansion. This is almost imperceptible but creates the sense that the element has mass.

**Anticipation:** Significant motion is telegraphed. A panel that will slide in shows a slight hint before committing. A menu that will open briefly scales down before expanding. This removes the shock of sudden state change.

**Staging:** One thing at a time. When multiple elements animate, the most important animates first (or most prominently). Simultaneous unrelated motion competes for attention.

**Ease-in / Ease-out:** Objects accelerate out of rest and decelerate into it. Linear motion is mechanical and unconvincing. Natural motion follows curves. This is not an aesthetic preference — it describes how mass actually behaves.

**Secondary action:** Supporting elements add dimension to primary motion. When a card expands, its shadow deepens and spreads slightly. The secondary action enriches the primary without competing with it.

**Timing:** Duration encodes weight. Heavy things move slowly; light things move quickly. A large panel transitioning in at the same speed as a small tooltip violates this and both feel wrong.

**Follow-through / Overlapping action:** Not all parts of a compound element stop at the same time. The leading edge of a sidebar arrives; the content inside settles slightly afterward. Simultaneous stops read as mechanical.

### 4.2 Spring Physics vs. Cubic Bezier

The fundamental distinction in animation quality for UI:

**Cubic bezier curves** define motion using start state, end state, and two control points. Duration is fixed. The animation always takes exactly as long as specified. This is mathematically clean but physically wrong — real objects don't stop at a predetermined time, they stop when their energy dissipates.

**Spring physics** define motion using mass, stiffness, and damping. Duration emerges from physics. The animation behaves like a mass on a spring: it overshoots its target slightly, bounces back, settles. This matches how physical objects actually behave when placed or released.

The reason iOS feels physical and most web interfaces feel mechanical is that iOS uses spring physics for primary transitions (UIKit spring animations) while web interfaces typically use cubic bezier curves. The difference is not large when the animation completes — it is in the last 10-15% of motion where the spring settles vs. the cubic bezier terminates.

**For the Exocortex interface:**
- **Primary panel transitions:** spring physics (stiffness 300, damping 30 — responsive without excessive bounce)
- **Micro-interactions (buttons, toggles):** cubic bezier with ease-out (fast response, no bounce)
- **Loading states / progress indicators:** linear or slight ease-in (conveys ongoing work, not settling)
- **Alerts / notifications entering:** ease-out-back (slight overshoot signals importance)

### 4.3 Duration Guidelines

| Interaction type | Duration range | Feel at minimum | Feel at maximum |
|-----------------|---------------|-----------------|-----------------|
| Micro (button press, toggle) | 80–150ms | Instant, responsive | Perceptible |
| Small transition (tooltip, dropdown) | 150–250ms | Crisp | Comfortable |
| Medium transition (panel open, modal) | 250–400ms | Quick | Deliberate |
| Large transition (page, full-screen) | 300–500ms | Efficient | Considered |
| Beyond 500ms | Avoid | — | Feels slow |

### 4.4 Choreography and Stagger

When multiple elements animate together, **stagger** — offsetting the start times of sequential elements — creates the perception of coordinated motion rather than simultaneous chaos.

Rule of thumb: stagger offset = 20–40% of individual animation duration. A list of items entering at 200ms each should stagger by 40–80ms between items.

**Choreography** is the larger principle: think about what the screen is doing as a whole, not what each element is doing individually. The screen tells a story of state change. The motion should tell that story coherently.

### 4.5 Easing Curve Reference

```
ease-in:        starts slow, ends fast — use for elements leaving the screen
ease-out:       starts fast, ends slow — use for elements entering the screen
ease-in-out:    slow-fast-slow — use for elements moving across the screen
linear:         constant speed — use for continuous processes (spinners, progress)
ease-out-back:  enters, overshoots slightly, settles — use for notifications, emphasis
```

The specific values from Material Design (reliable starting points, adjust by feel):
```css
--motion-standard:   cubic-bezier(0.2, 0, 0, 1.0)   /* elements that stay on screen */
--motion-decelerate: cubic-bezier(0, 0, 0, 1.0)      /* elements entering */
--motion-accelerate: cubic-bezier(0.3, 0, 1.0, 1.0)  /* elements leaving */
--motion-spring:     spring(stiffness: 300, damping: 30)
```

---

## 5. Typography System

Typography is the dimension with the largest gap between functional adequacy and premium feel.

### 5.1 The Functional / Expressive Spectrum

| Type | Role | Examples | When to use |
|------|------|---------|-------------|
| **Functional** | Read, not noticed | Inter, SF Pro, Roboto | Body text, labels, data |
| **Expressive** | Noticed and read | Display fonts, editorial faces | Headers, titles, identity moments |
| **Character** | Personality carrier | Stencil, terminal fonts, condensed gothics | Theme identity, decorative contexts |

For an expert interface like Exocortex:
- **Body / data:** Functional type. Inter or JetBrains Mono for data-dense content.
- **Headers / labels:** Expressive with restraint — weight variation carries hierarchy without requiring a second typeface.
- **Identity moments:** Character type, used sparingly.

### 5.2 The Weight Contrast Principle

Weight contrast (thin vs. heavy weights within a single typeface family) is the most underused hierarchy tool. Most interfaces use size to create hierarchy, which requires significant size differences to read. Weight contrast creates hierarchy at the same size — a 900-weight label next to a 300-weight label reads as a clear primary/secondary relationship without needing one to be larger.

This is how premium interfaces achieve dense layouts that still read clearly: size differences are minimal (compressed vertical space) while weight differences create all the hierarchy.

**Recommended weight system:**
```
Display:     900 (Black) — used for primary state labels, identity moments
Heading:     700 (Bold) — section headers, primary data values
Label:       500 (Medium) — UI labels, field names, secondary headers
Body:        400 (Regular) — body text, descriptions
Supporting:  300 (Light) — metadata, timestamps, tertiary information
```

### 5.3 Monospace for Data

Data values — numbers, codes, hashes, timestamps — should use a monospace typeface. This is not just stylistic. Monospace aligns columns, makes numeric comparisons legible, and visually separates "data value" from "label." The convention is universal in terminal and operational interfaces because it works.

**Recommended:** JetBrains Mono (has programming ligatures, excellent screen rendering, multiple weights) or IBM Plex Mono (authoritative, slightly warmer).

### 5.4 Tracking and Leading

**Tracking (letter-spacing):**
- Large text (display, 24px+): slight negative tracking (-0.02em to -0.04em) — reduces the optical looseness that large type has at default spacing
- Small text (12px and below): slight positive tracking (+0.02em to +0.05em) — compensates for reduced legibility at small sizes
- ALL CAPS text: always +0.05em to +0.1em — all-caps at default tracking looks compressed

**Leading (line-height):**
- Body text: 1.5–1.6 — comfortable reading rhythm
- Data/code: 1.4–1.5 — dense but not compressed
- Display/headline: 1.1–1.2 — tight is intentional at large sizes

---

## 6. Color System

### 6.1 Why Classical Color Theory Fails for UI

Classical color theory (complementary, triadic, analogous) was developed for print on white ground. In UI, color exists at varying opacities, on both light and dark grounds, at sizes ranging from 2px borders to full-screen backgrounds. A complementary pair that works in a painting can vibrate destructively when adjacent in UI (red and cyan at full saturation next to each other cause chromatic aberration at the edges).

The working method for UI color is **tonal variation from a base hue**, not multi-hue selection from a color wheel.

### 6.2 The Token Architecture

Design tokens are the atomic units of a design system — named variables that store design decisions. By separating the decision (what the color means) from the value (what the color is), tokens enable theming: swap the values for a different theme while all the meaning-labels remain the same.

**Three layers:**

**Primitive tokens** — raw values without semantic meaning:
```
--color-red-500:    #E53E3E
--color-amber-400:  #F6AD55
--color-neutral-900: #0A0A0A
```

**Semantic tokens** — meaning assigned to primitives:
```
--color-surface-base:     var(--color-neutral-900)
--color-surface-elevated: var(--color-neutral-800)
--color-accent-primary:   var(--color-amber-400)
--color-accent-critical:  var(--color-red-500)
--color-text-primary:     var(--color-neutral-50)
--color-text-secondary:   var(--color-neutral-400)
```

**Component tokens** — component-specific references to semantic tokens:
```
--alert-critical-background:  var(--color-accent-critical)
--button-primary-background:  var(--color-accent-primary)
--sidebar-background:         var(--color-surface-base)
```

**The theme swap works by replacing primitive token values.** Component and semantic tokens do not change — only the primitives they reference. This is how a single component library supports multiple themes.

### 6.3 The Palette from Tonal Variation

Build each functional color as a scale of 9–10 tones from near-white to near-black, derived from a single hue at consistent saturation intervals. Name them numerically (100–900 or 50–950).

For Exocortex's default theme (tactical dark):
```
Amber scale (primary accent):
  --amber-100: #FFFBEB
  --amber-200: #FEF3C7
  --amber-300: #FDE68A
  --amber-400: #FCD34D
  --amber-500: #F59E0B   ← primary accent
  --amber-600: #D97706
  --amber-700: #B45309
  --amber-800: #92400E
  --amber-900: #78350F

Neutral scale (surfaces and text):
  --neutral-50:  #FAFAFA
  --neutral-100: #F5F5F5
  --neutral-200: #E5E5E5
  --neutral-300: #D4D4D4
  --neutral-400: #A3A3A3
  --neutral-500: #737373
  --neutral-600: #525252
  --neutral-700: #404040
  --neutral-800: #262626
  --neutral-850: #1A1A1A   ← elevated surface
  --neutral-900: #111111   ← base surface
  --neutral-950: #0A0A0A   ← deep surface
```

### 6.4 Palette Restraint

The Persona 5 principle: **the fewer colors you use, the more impact each carries.** A three-color palette where one color is reserved for critical emphasis is more powerful than a six-color palette where every color has some use.

**Rule of thumb for interface palettes:**
- 1 base surface color (background/ground)
- 1–2 elevated surface colors (panels, cards)
- 1 primary accent (interactive elements, primary actions)
- 1 semantic accent (critical alerts, errors — different from primary)
- Text hierarchy handled through tonal variation of a single neutral (not multiple hues)
- Total hues in active use: 3 maximum (neutral, primary accent, critical accent)

### 6.5 Dark Theme Technical Constraints

Dark themes have five specific technical challenges:

1. **Halation.** Pure white (#FFFFFF) on pure black (#000000) creates chromatic fringing at letter edges due to the extreme contrast. Solution: use near-white (#E0E0E0 or similar) for body text, reserving pure white for display elements.

2. **Color vibration.** Fully saturated complementary colors (red/cyan, orange/blue) vibrate at the edges when adjacent. Solution: desaturate one or both, or add a neutral separator.

3. **Saturation inflation.** Colors that look correct at design-time appear over-saturated on high-gamut displays. Design at P3-wide gamut or reduce saturation 10-15% from what looks right on a standard display.

4. **Elevation through lightness.** In dark themes, higher surfaces should be lighter, not darker. An elevated card on a dark background uses a slightly lighter background color than the base surface — this matches physical intuition (light sources above illuminate elevated surfaces more than recessed ones). Google's Material 3 dark theme spec establishes this explicitly.

5. **Colored surface overlays.** Instead of literal shadows (which are invisible on dark surfaces), elevation in dark themes is communicated through colored overlays. A surface at elevation-1 has the base color; at elevation-2, a semi-transparent overlay of the accent color at 5-8% opacity is applied. This is subtle but creates clear depth hierarchy.

---

## 7. The "Juice" Principle

"Juice" is the term from game design for the aggregate of visual and audio feedback that makes interactions feel satisfying beyond their functional purpose. The definition from Jonasson and Purho (GDC 2012): "maximum output for minimum input."

The components:

**Feedback completeness.** Every action produces a response. Not just functional feedback (the button was pressed) but perceptual feedback (the button visibly responds). Missing feedback makes an interface feel unresponsive even when it is technically responsive. Latency below 16ms is imperceptible; feedback absence is always perceptible.

**State transitions as events.** When something changes state (agent starts a task, tool call completes, alert fires), this is an event worth marking. Not with screen shake (too much for software) but with a micro-animation — a brief highlight, a small pulse, a transition that registers the change.

**Hover states with weight.** Interactive elements should respond to hover with enough change to confirm they are interactive. The hover state is the element anticipating interaction — it should feel ready, not just highlighted.

**The principle of minimum juice.** Game juice can be overused (Vlambeer's screen shake is constantly referenced as the canonical example). Software juice must be calibrated: enough feedback to feel responsive and alive, not so much that it becomes distracting during focused work. The target is: the interface feels slightly dead if the juice is removed, but the user never notices the juice while working.

**Restraint is the discipline.** Every juicy element should be evaluated: if I removed this, would the interface feel worse? If yes, keep it. If no, remove it.

---

## 8. Texture, Noise, and Materiality

The history of UI design trends is a history of overcorrection. Skeuomorphism was abandoned for flat design, which was abandoned for material design, which spawned neumorphism, then glassmorphism. Each trend emerged from the failures of the previous and overcorrected into its own failure.

The current best practice is not a trend — it is a principle:

**Texture should earn its presence.** A noise/grain texture on a surface adds perceptible depth and prevents the flat, featureless quality of solid fills — but only if it is subtle (2–4% opacity at standard screen resolution). Too much noise becomes the loudest element on the screen. The right amount is noticed only when removed.

**Material metaphors should carry functional meaning.** Bravely Default's card layering communicates depth hierarchy (closer = more important). NieR's CRT scan lines communicate era and technology. MGS's amber tint communicates operational display language. Texture that carries no functional meaning should be removed.

**The grain/noise resurgence (2022–present)** is the correct resolution of the flat-vs-skeuomorphic debate. A flat design with 2–3% film grain looks crafted, tactile, and warm without making false claims about physical objects. The grain removes the synthetic quality of pure flat design without the pedagogical weight of skeuomorphism.

For Exocortex's tactical register: a subtle grain texture on surface elements (2–3% opacity, monochromatic) is appropriate and consistent with operational display aesthetics. It should be nearly invisible in use but present when absent.

---

## 9. Negative Space as Signal

Luxury is largely communicated through what is not there. The amount of space given to an element signals the importance of that element. Dense, tightly packed interfaces communicate utility and economy. Spacious interfaces communicate premium positioning and focused attention.

**For expert interfaces:** the balance shifts — experts benefit from density, and excessive whitespace forces navigation for information they could have seen at a glance. But whitespace is not binary. The principle applies to *quality* of space, not *amount*.

**Micro-whitespace** (spacing between elements within a component: label-to-field, icon-to-text) has more impact on perceived quality than macro-whitespace. The feeling of a premium interface often comes from correct micro-spacing rather than large empty areas.

**The 8-point grid.** Align all spacing to multiples of 8px (8, 16, 24, 32, 48, 64). This creates implicit rhythm — elements spaced at consistent intervals create visual order without requiring the eye to consciously register it. Deviations from the grid feel subtly wrong in ways that are hard to articulate.

**Hierarchy through space.** Within a group, elements are closely spaced. Between groups, significantly more space. The ratio matters: if within-group spacing is 8px, between-group spacing should be at minimum 24px (3x). Less than 2x ratio makes groups indistinguishable.

---

## 10. The Design System Architecture

### 10.1 What a Design System Is

A design system is a collection of reusable components, tokens, and guidelines that together define a consistent visual and behavioral language for an interface. The key property is **single source of truth**: when a color, a spacing value, or an animation curve changes, it changes everywhere through the token system.

A design system for Exocortex must be:
- **Themeable:** multiple visual personalities expressed through token swaps, not code changes
- **Composable:** components combine into layouts without requiring bespoke arrangements
- **Expert-density-capable:** components must support high information density, not just comfortable spacing
- **Motion-aware:** transitions and states are part of the component specification, not afterthoughts

### 10.2 Token Layers

```
┌─────────────────────────────────────────────┐
│  COMPONENT TOKENS                           │
│  --button-primary-bg, --alert-critical-text │
│  Component-specific names. Reference        │
│  semantic tokens only.                      │
├─────────────────────────────────────────────┤
│  SEMANTIC TOKENS                            │
│  --color-surface-base, --color-accent       │
│  --motion-transition-medium                 │
│  Meaning names. Reference primitives.       │
├─────────────────────────────────────────────┤
│  PRIMITIVE TOKENS                           │
│  --amber-500: #F59E0B                       │
│  --space-8: 8px                             │
│  --duration-250: 250ms                      │
│  Raw values. Theme swap happens here.       │
└─────────────────────────────────────────────┘
```

### 10.3 Spacing System

All spacing values are multiples of 8px. Named by their value:

```css
--space-2:   2px   /* micro-gaps, borders */
--space-4:   4px   /* tight component internal spacing */
--space-8:   8px   /* standard component internal spacing */
--space-12:  12px  /* comfortable component internal spacing */
--space-16:  16px  /* between related elements */
--space-24:  24px  /* between component groups */
--space-32:  32px  /* section separation */
--space-48:  48px  /* major section separation */
--space-64:  64px  /* zone separation */
```

### 10.4 Motion Token System

```css
/* Durations */
--duration-micro:    100ms  /* button press, toggle */
--duration-fast:     200ms  /* small transitions */
--duration-medium:   300ms  /* panel transitions */
--duration-slow:     450ms  /* page transitions */

/* Easing */
--ease-standard:     cubic-bezier(0.2, 0, 0, 1.0)    /* staying on screen */
--ease-enter:        cubic-bezier(0, 0, 0, 1.0)       /* entering */
--ease-exit:         cubic-bezier(0.3, 0, 1.0, 1.0)   /* leaving */
--ease-emphasis:     cubic-bezier(0.2, 0, 0, 1.2)     /* overshoot, emphasis */
--ease-linear:       linear                             /* loaders, progress */
```

### 10.5 Typography Scale

```css
/* Size scale */
--text-xs:   11px   /* metadata, timestamps */
--text-sm:   13px   /* labels, secondary text */
--text-base: 15px   /* body text */
--text-md:   17px   /* prominent body */
--text-lg:   20px   /* small headings */
--text-xl:   24px   /* headings */
--text-2xl:  32px   /* display */
--text-3xl:  48px   /* identity moments */

/* Weight scale */
--weight-light:    300
--weight-regular:  400
--weight-medium:   500
--weight-bold:     700
--weight-black:    900

/* Line height */
--leading-tight:   1.15  /* display text */
--leading-normal:  1.5   /* body text */
--leading-relaxed: 1.7   /* comfortable reading */
--leading-code:    1.4   /* code/monospace */
```

### 10.6 Elevation System (Dark Surfaces)

Elevation in dark themes is communicated through surface lightness and optional colored overlay, not shadows.

```css
--surface-ground:   #0A0A0A   /* z-0: true background */
--surface-base:     #111111   /* z-1: primary surface */
--surface-raised:   #1A1A1A   /* z-2: cards, panels */
--surface-float:    #222222   /* z-3: dropdowns, tooltips */
--surface-overlay:  #2A2A2A   /* z-4: modals */

/* Optional: accent-tinted surface overlays */
--surface-accent-subtle: color-mix(in srgb, var(--color-accent) 6%, var(--surface-raised))
```

---

## 11. The Theme Architecture

The token system enables multiple visual personalities without rebuilding components. Each theme overrides primitive tokens. Semantic and component tokens remain the same.

Exocortex ships with four reference themes, each drawn from one of the reference games. These are not novelties — each represents a coherent aesthetic philosophy that may suit different analysts or use contexts.

### Theme 1: TACTICAL (Default)
*Inspired by: Metal Gear Solid V: The Phantom Pain*

The operational display language of military intelligence technology. Amber on near-black. Stencil-adjacent typography. The look of a system built for field use by people who mean business.

```css
/* TACTICAL theme primitives */
--amber-500:     #F59E0B;
--amber-400:     #FBBF24;
--neutral-950:   #080808;
--neutral-900:   #101010;
--neutral-850:   #181818;
--neutral-50:    #E8E0D0;   /* warm near-white, not cold */

--color-accent:        var(--amber-500);
--color-accent-hover:  var(--amber-400);
--color-surface-base:  var(--neutral-900);
--color-text-primary:  var(--neutral-50);

--font-display:  'Bebas Neue', 'Barlow Condensed', sans-serif;
--font-body:     'Inter', system-ui, sans-serif;
--font-mono:     'JetBrains Mono', monospace;
```

Aesthetic signature: dense, amber-accented, warm-neutral text. Typography uses condensed display faces for headings. Scan-line grain texture on surfaces at 2% opacity. Transitions are crisp and fast.

### Theme 2: TERMINAL
*Inspired by: NieR: Automata*

The YoRHa android OS aesthetic. Monochromatic with warm beige bias. Diegetic distress textures. Sparse, systematic, precise.

```css
/* TERMINAL theme primitives */
--terminal-light:   #D4C9AA;   /* Yoko Taro's warm beige */
--terminal-mid:     #6B6458;
--terminal-dark:    #0C0B09;
--terminal-accent:  #C8B88A;   /* near-gold, not white */

--color-accent:        var(--terminal-accent);
--color-surface-base:  var(--terminal-dark);
--color-text-primary:  var(--terminal-light);

--font-display:  'Share Tech Mono', 'Courier Prime', monospace;
--font-body:     'Share Tech Mono', monospace;   /* all monospace */
--font-mono:     'Share Tech Mono', monospace;
```

Aesthetic signature: near-monochrome, warm beige tone, all-monospace typography. CRT scan line effect on primary surface. Selective use of accent only for active/critical states. Transitions are slightly slower and use linear easing — the "mechanical boot" feel.

### Theme 3: ARCANA
*Inspired by: Persona 5*

The graphic design manifesto. Maximum contrast, aggressive palette restraint, type as attitude. Reserved for analysts who want the interface to make a statement.

```css
/* ARCANA theme primitives */
--arcana-red:     #CC1C1C;
--arcana-white:   #F5F5F5;
--arcana-black:   #0D0D0D;
--arcana-accent:  var(--arcana-red);   /* NOTHING ELSE IS RED */

--color-accent:        var(--arcana-red);
--color-surface-base:  var(--arcana-black);
--color-text-primary:  var(--arcana-white);

--font-display:  'Bebas Neue', 'Anton', sans-serif;
--font-body:     'Inter', system-ui, sans-serif;
--font-mono:     'JetBrains Mono', monospace;
```

Aesthetic signature: black/white/red, no other colors. Typography is heavy, condensed, angular. Transitions use ease-out-back — they arrive with intent. The slash/diagonal motif in component borders and dividers. Red appears only for critical/primary action — never for decoration.

### Theme 4: MEMORIA
*Inspired by: Bravely Default*

Warm, layered, material. The workshop aesthetic — a place where a craftsman works. Parchment textures, warm gold accents, depth through layering.

```css
/* MEMORIA theme primitives */
--memoria-parchment: #F4EDD8;
--memoria-gold:      #B8860B;
--memoria-warm:      #1A1510;
--memoria-text:      #2C241A;

--color-accent:        var(--memoria-gold);
--color-surface-base:  var(--memoria-warm);
--color-text-primary:  var(--memoria-parchment);

--font-display:  'Cinzel', 'Cormorant Garamond', serif;
--font-body:     'EB Garamond', 'Libre Baskerville', serif;
--font-mono:     'JetBrains Mono', monospace;
```

Aesthetic signature: warm gold on deep brown-black, serif typography, z-axis depth through card layering. Transitions are slightly slower and use standard easing — they feel deliberate, weighted. Texture is parchment-grain at 3% opacity.

---

## 12. Component Philosophy

Components are the reusable units built from the token system. Each component must:

1. **Express theme correctly.** A button in TACTICAL looks different from the same button in ARCANA — same dimensions, same function, different aesthetic register.
2. **Define all states.** Default, hover, active, focus, disabled, loading. States are not afterthoughts.
3. **Specify motion.** Entry, exit, state transition animations are part of the component specification.
4. **Be density-capable.** Components have compact and comfortable size variants. Expert users use compact.

**Component types (initial set):**

| Category | Components |
|----------|-----------|
| **Foundation** | Button (primary/secondary/ghost/destructive), Input, Select, Toggle, Checkbox |
| **Display** | Badge, Tag, Status indicator, Progress bar, Spinner |
| **Layout** | Panel, Card, Divider, Spacer |
| **Navigation** | Sidebar, Tab bar, Breadcrumb |
| **Feedback** | Alert (critical/warning/info), Toast notification, Tooltip |
| **Data** | Table, Log stream, Key-value pair, Code block |
| **Agent-specific** | Stack status bar, Tool execution indicator, BST domain badge, SA level indicator |

---

## 13. The Feel Specification

Beyond visual tokens, a design system for a premium interface must specify *feel* — the aggregate quality of using it.

**Target feel for Exocortex (TACTICAL default):**

- *Immediate and responsive.* The interface reacts before the user has consciously noticed they acted. Sub-100ms for all micro-interactions.
- *Weighty and precise.* Transitions feel like they have mass. Not slow — deliberate. The distinction is that deliberate motion communicates confidence; slow motion communicates hesitation.
- *Controlled and calm.* Even when the agent is running complex tasks, the interface communicates competence rather than urgency. Alerts are clear but not frantic. The interface of a system that has seen this before.
- *Expert without being cryptic.* Dense, but organized. The expert user finds everything exactly where they expect it. The novice user can find the primary path through visual hierarchy.

The test: if the interface were a person, they would be the calm, experienced operative who has run this operation before, knows exactly where everything is, and handles unexpected developments without visible stress.

---

## 14. What This Design Brief Is Not

- This brief does not specify the implementation framework (React, Vue, Alpine, vanilla CSS). The token system and component philosophy are framework-agnostic.
- This brief does not define the visual layout of specific screens. It establishes the vocabulary for building them.
- This brief is not final. As implementation reveals gaps or as the interface evolves, the brief should evolve with it. The tokens are the mechanism for managed evolution — changing a token changes everything that references it, controlled and traceable.
- This brief does not replace testing. Aesthetic quality judgments must ultimately be validated by the people who use the interface. The principles reduce the error rate; they do not eliminate subjectivity.

---

## 15. Relationship to WEBUI_DESIGN_BRIEF.md

The functional safety brief (WEBUI_DESIGN_BRIEF.md) and this aesthetics brief govern complementary dimensions:

| WEBUI_DESIGN_BRIEF.md | AESTHETICS_DESIGN_BRIEF.md |
|----------------------|---------------------------|
| What the interface does | How the interface feels |
| Safety, situation awareness, automation bias | Visceral, behavioral, reflective design |
| Alert calibration, Gulf of Evaluation | Color, motion, typography, texture |
| Override path, SA levels | Theme architecture, token system |
| When to interrupt the analyst | How to interrupt the analyst without breaking flow |

Both must be satisfied simultaneously. The alert severity hierarchy from WEBUI_DESIGN_BRIEF.md is implemented through the token and component system from this brief. The two documents should be read together for any design decision that is both functional and aesthetic — which is most of them.

---

## 16. Research Sources

**Game UI and design:**
- Sutou, M. (2016). Persona 5 UI/UX Art Director interview, various Atlus developer commentary.
- Kijima, H. (2018). NieR: Automata UI concept and execution. PlatinumGames developer notes.
- gameuidatabase.com — 55,000+ screenshots, searchable by game, element, color.
- hudsandguis.com — Fictional HUD reference library.

**Motion design:**
- Johnston, O. & Thomas, F. (1981). *The Illusion of Life: Disney Animation.* 12 Principles.
- Material Design 3 Motion Specification. m3.material.io/styles/motion
- Comeau, J. "A Friendly Introduction to Spring Physics." joshwcomeau.com.
- easings.net — Easing function visual reference.

**Typography:**
- Czaplewski, R. Inter font design documentation.
- typewolf.com — In-use typography examples.
- v-fonts.com — Variable font explorer.

**Color:**
- Kennedy, E.D. (2020). "Refactoring UI" — tonal variation palette methodology.
- Material Design 3 Dark Theme specification.
- Bostock, M. Observable color theory notebooks.

**Visual hierarchy and composition:**
- Wertheimer, M. (1923). Gestalt laws of perceptual organization. *Psychologische Forschung 4.*
- Norman, D.A. (2004). *Emotional Design: Why We Love (or Hate) Everyday Things.* Three levels.

**Juice and game feel:**
- Jonasson, M. & Purho, P. (2012). "Juice It or Lose It." GDC talk.
- Byttebier, J. "Game Feel: The Secret Ingredient." Medium/GDC references.
- Swink, S. (2008). *Game Feel: A Game Designer's Guide to Virtual Sensation.*

**Design systems:**
- Design Tokens W3C Community Group Specification (draft).
- Salesforce Lightning Design System token documentation.
- Material Design token architecture documentation.

---

*Research conducted March 2026. Raw research synthesis: D:\tmp\aesthetics_research.md (85KB).*
*See also: WEBUI_DESIGN_BRIEF.md for functional/safety principles.*
