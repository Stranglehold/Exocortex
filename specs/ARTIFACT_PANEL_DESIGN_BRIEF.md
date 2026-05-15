# Artifact Panel Design Brief
## What It Should Feel Like

**Status:** Design brief. Aesthetic intent document.
**Date:** 2026-04-15
**Author:** Opus, with Jake
**Audience:** Kestrel (implementation), Jake (review), Opus (architectural consistency)
**Constraint:** No library constraints. Whatever works and looks good. Complexity matches the request — simple stays simple, premium stays premium.
**This document is:** Not a spec. Not a component library. Not a design system. This is the intent document that answers "what should this feel like?" so that the implementer can answer "how do I build that?"

---

## Part I: Intent

### What We're Building

Artifact panels for the Exocortex project — interactive browser-based interfaces that render inside Claude.ai artifacts (.jsx, .html) or the Agent Zero webUI. These panels are how the analyst experiences every piece of intelligence work we've built. The OSS claim landscape. The SWARMFISH deliberation. The behavioral trace viewer. The notebook. The theme engine controls. Diagnostic panels. Data visualizations.

The panels are the product. Not the pipeline behind them — the analyst never sees the pipeline. The panels are where the work becomes visible, touchable, usable. If the panels feel cheap, the entire system feels cheap regardless of the engineering underneath.

### What "Feel Good" Means

The feeling we're chasing has a name in game design: **juice.** Game designer Petri Purho defined it at GDC 2012 as providing interactions that give the user far more output than their simple inputs deserve. You click one thing and the response is rich — visual, kinetic, weighted. The ratio of input to feedback is asymmetric in the direction of generosity. The system gives back more than you put in.

But juice alone produces gimmicks. What elevates juice into craft is **intent.** Every animation, every transition, every color choice, every font weight serves the same vision. The vision isn't "look cool." The vision is: **this is a system that respects the operator's intelligence.**

Dense when density is warranted. Quiet when quiet is warranted. Authoritative in its typography. Honest in its color signals. Alive in its texture. And trusting — trusting that the analyst doesn't need hand-holding, doesn't need confirmation dialogs, doesn't need the interface to explain itself. The interface assumes competence. It provides power tools. It gets out of the way.

The highest compliment a UI can receive isn't "this looks great." It's "I forgot I was using an interface."

---

## Part II: The Eleven Principles

These emerged from studying what makes specific games and websites feel satisfying to use. Each principle is illustrated by a reference that exemplifies it. The references are not decorative — they're study material. Before implementing a panel, study the reference for that principle.

### 1. Juice — Every Interaction Overdelivers

**Reference:** Disgaea 5 menus, Persona 5 battle results

Every interaction produces more output than the input deserves. A click doesn't just change state — it changes state with weight, feedback, and visual acknowledgment. You equip an item and the stat numbers change with a flourish. You level up and the portrait updates. You complete a battle and the victory sequence unfolds across multiple animated frames rather than a single stats dump.

**In practice:**
- When a claim is added to the OSS corpus, the claim count doesn't just increment — it pulses, settles, and the new claim briefly highlights in the list
- When SWARMFISH reaches consensus, the confidence number doesn't just appear — it resolves from the individual profile assessments with a converging animation
- When the analyst toggles a filter, the filtered items don't just disappear — they compress, slide, and the remaining items reflow with spring physics

### 2. Diegetic Identity — The Interface Belongs to the System

**Reference:** HighFleet command panel, Nier Automata OS, MGSV iDroid

The interface feels like operating a real system, not using a web app. The HighFleet creator described his menus not as menus but as "a small museum where you are allowed to touch and twist everything." In Nier Automata, the menu IS the android's operating system — remove the OS chip and you die. The interface exists inside the world it controls, not as a layer on top of it.

**In practice:**
- The OSS panel shouldn't look like a React dashboard. It should look like the console an intelligence analyst operates
- The SWARMFISH deliberation panel should feel like sitting in the committee room, not reading committee minutes
- The theme engine isn't a settings page — it's the system's identity controls, and the visual treatment should reflect that the controls affect the system itself

**Critical warning from HighFleet's creator:** "Having received a hint, you stop feeling the physical world, its speed, and inertia. You begin to influence the world not directly, but through an artificial substrate and all the magic disappears." Every abstraction layer between the operator and the system — tooltips, guide overlays, explanatory modals — risks destroying the direct connection that makes the interface feel real. Use them sparingly. The interface should teach through use, not through explanation.

### 3. Contextual Intelligence — Show What Matters Now

**Reference:** League of Legends shop, OpenGridWorks layer toggles

The LoL shop doesn't show every item. It loads recommendations based on what the player currently owns AND what the enemy team is building. The interface is aware of context and surfaces what's relevant. OpenGridWorks lets the analyst toggle layers — transmission lines, substations, datacenters — to direct attention to what matters for the current question.

**In practice:**
- The OSS claim viewer should surface claims relevant to the active question, weighted by source credibility, not dump the entire corpus
- Tab structure: Recommended (relevant to active question), All (full corpus), Custom (analyst-configured filters)
- Layer toggles for claim types, source categories, time ranges — the analyst directs what's visible, the system shows what's asked for
- The infrastructure that isn't visible is still there. It's just not in the way

### 4. Progressive Density — Clean Default, Detail on Demand

**Reference:** SkyUI, World Labs Spark 2.0 blog, SWARMFISH three-level transparency

SkyUI doesn't replace Skyrim's UI — it adapts it for what a PC operator actually has (mouse, keyboard, wide monitor). The default view is useful. The configurable columns, full-text search, and extended data are available when the operator wants them. The density is adjustable. The analyst chooses how much information they want.

World Labs' technical blog starts with "what is 3DGS" (simple), moves to rendering architecture (medium), then to LoD tree traversal algorithms (complex). Each level builds on the last. You can stop at any level and have a coherent understanding.

**In practice:**
- Dashboard view (Level 1): three to five key numbers, well-spaced, at-a-glance status
- Structured summary (Level 2): claim categories, source health, deliberation progress
- Full reasoning (Level 3): individual profile assessments, evidence chains, raw claim data
- The analyst controls the depth. The system never forces density. The system never hides capability

### 5. Deliberate Friction — Consequential Actions Have Weight

**Reference:** MGSV iDroid deployment animation, Persona 3 Reload's slower menu pacing

The iDroid is deliberately slow. You pull it up and there's a deployment animation. You call in a supply drop and you hear the request go through channels. The friction isn't frustration — it's weight. It communicates that the action matters. P3R's art director deliberately chose slower animations than P5 — "in order to contrast Persona 5's emphasis on aggressive movements." The speed of the interaction communicates the mood of the system.

**In practice:**
- Pausing the OSS pipeline: the pause button takes 200ms to settle into "paused," not instant. The analyst feels the weight of stopping the system
- Overriding a SWARMFISH assessment: the override requires a confirmation that itself has weight — not a modal popup, but a deliberate gesture like press-and-hold
- Routine operations (scrolling, filtering, expanding details) should be fast and frictionless. Only consequential actions get weight. The contrast is what makes the weight meaningful

### 6. Authority Through Density — The Evangelion Principle

**Reference:** Evangelion NERV terminals

The NERV terminals have scrolling hex dumps, waveform monitors, status indicators in every corner. None of it is readable at viewing speed. That's the point. It communicates that the system is alive and handling complexity beyond what the operator needs to parse in real time. The density says "this system is handling more than you can see, and it's handling it." The goal is immersion, not comprehension. The operator trusts the interface because the interface acts like it knows what it's doing.

**In practice:**
- Use this principle selectively. The SWARMFISH deliberation panel during active assessment could show the profile reasoning streams in real time — dense, flowing, not fully readable, communicating "the committee is working." When deliberation completes, the density resolves into the clean consensus view
- The OSS source health monitor could show ingestion activity as ambient texture — source names, timestamps, claim counts updating in a subtle feed. Not prominent enough to distract. Present enough to communicate life
- A panel that shows nothing when idle feels dead. A panel that breathes feels trustworthy

### 7. Spring Physics Everywhere

**Reference:** Apple iOS interactions, Framer Motion, web animation best practices

No CSS transitions with `ease-in-out`. Springs have no fixed duration — they settle naturally based on stiffness, damping, and mass. That's why they feel physical. CSS transitions with fixed durations feel computed. Springs feel real.

Every state change — expanding a panel, toggling a filter, selecting a claim, navigating between views — should use spring physics. The spring doesn't just move the element. It carries velocity, overshoots slightly, and settles. That overshoot is what makes the brain register the interaction as physical rather than digital.

**Specific values:**
- Micro-interactions: 150-300ms perceived duration, stiffness ~300, damping ~25
- Panel transitions: 300-500ms perceived duration, stiffness ~200, damping ~20
- Active button states: scale to 0.95, 80ms down with `cubic-bezier(0.4, 0, 0.2, 1)`, 200ms up with `cubic-bezier(0.34, 1.56, 0.64, 1)` (the 1.56 creates overshoot)
- All animations must be interruptible. If the user clicks while an animation is playing, the animation redirects immediately, carrying current velocity. No animation locks

**Libraries:** Framer Motion (React, spring physics, layout animations, gestures), GSAP (mature, ScrollTrigger), Popmotion (lightweight spring/decay/physics), anime.js (lightweight, timeline-based). For vanilla JS contexts, custom spring implementation is ~20 lines of Hooke's Law integration.

### 8. Single Accent for Attention

**Reference:** Evangelion orange-on-black, Persona 3 blue, Persona 5 red

One accent color in a sea of neutral. The accent teaches the analyst's eye where to look. Over time, the analyst develops an unconscious scan pattern — glance at the panel, if there's the accent color, something needs attention. If there's no accent, everything is nominal. The color does the triage before the analyst reads a word.

**In practice:**
- Pick one warm accent color per panel. Use it ONLY for things that need attention — anomaly flags, confidence thresholds crossed, new claims since last session, active deliberation requiring input
- Everything else is neutral — the indigo/graphite/slate palette from the theme engine
- Persona 5 uses red as its only thematic color and achieves maximum impact. Persona 3 uses blue. The constraint is the power. One color means one signal. Two colors means confusion

### 9. Operator Trust — No Unnecessary Confirmations

**Reference:** SkyUI keyboard shortcuts, Arma 3 Zeus direct manipulation

The interface assumes expertise. No tooltips on things the operator already knows. No "are you sure?" for reversible actions. No confirmation dialogs for routine operations. The interface trusts the operator. It only speaks when something is genuinely worth saying.

Every unnecessary notification trains the analyst to ignore notifications. Every unnecessary confirmation trains the analyst to click "yes" without reading. The interface that says nothing when nothing needs to be said is the interface whose voice is heard when it does speak.

**In practice:**
- Keyboard shortcuts for common operations — Kestrel should define the shortcut map for each panel
- Undo/redo instead of confirmation dialogs for reversible actions
- Error states that are visible but not intrusive — a red border that appears and fades, not a modal that blocks interaction
- No loading spinners that spin forever. Skeleton loading that mirrors the final layout with a subtle shimmer, crossfading to real content in 150-200ms

### 10. Information as Texture — Ambient Signals for System State

**Reference:** Evangelion scrolling data, HighFleet radar signatures

Ambient information that communicates system state without demanding attention. The scrolling hex in Evangelion. The radar pulse in HighFleet. The breathing health indicator. A subtle timestamp updating in the corner. Claim count incrementing. Source activity flickering.

Not prominent enough to distract. Present enough to communicate life. The panel breathes. When it stops breathing, the analyst notices — and that noticing is the signal, not a notification.

**In practice:**
- A subtle pulse on the source health indicator when ingestion is active
- A barely-visible activity feed at the panel's edge showing the most recent system events
- The background of the SWARMFISH panel subtly shifts hue during active deliberation — not enough to notice consciously, enough to feel that the system is working
- The panel that shows no ambient activity feels dead. The panel that breathes feels alive. The difference is trust

### 11. Total Aesthetic Commitment — No Fallback Screens

**Reference:** Persona 5, Persona 3 Reload

This is the capstone principle. Every screen, every interaction, every transition serves the same aesthetic vision. There are no "utility" screens that drop back to default styling. There are no transitions that just cut instead of animate. There are no loading states that show a generic spinner instead of a themed skeleton.

Persona 5's battle results screen is as carefully designed as its main menu. The shop interface has a character silhouette that flips when you change categories. The loading screens between areas show thematic character illustrations instead of a progress bar. The commitment is total. And the totality is what produces the coherence, and the coherence is what produces the feeling.

One beautifully designed screen in a sea of defaults actually feels worse than consistent mediocrity, because the contrast makes the default screens feel neglected. The commitment creates coherence. The coherence creates trust. The trust creates the feeling.

**In practice:**
- If a panel has a loading state, the loading state is designed, not defaulted
- If a panel has an error state, the error state is designed, not a red text dump
- If a panel has an empty state (no data yet), the empty state communicates something — invitation, readiness, potential — not blankness
- The notebook's indigo palette and the SWARMFISH's analytical aesthetic don't need to match. They need to each be fully committed to their own vision. Same discipline, different registers

---

## Part III: Mood by Panel

The same structural approach can express completely different moods. Persona 5 (red, aggressive, pop-punk) and Persona 3 Reload (blue, contemplative, liquid) share the same design discipline but produce opposite feelings. Our panels should do the same.

### OSS Dashboard — The Calm Instrument

**Mood:** Contemplative awareness. P3R register — fluid, ambient, the analyst suspended in the intelligence landscape. OpenGridWorks instrument aesthetic — every visual element is data, nothing is ornament.

**Color:** Cool palette. Indigo base with graphite secondary. Single warm accent (amber or soft orange) for attention signals only.

**Animation speed:** Slower. Fluid. Transitions that flow rather than snap. The panel breathes. Updates arrive and settle like ripples, not impacts.

**Typography:** Monospace for data values (claim counts, timestamps, confidence scores). Clean sans-serif for labels. Weight hierarchy: regular for ambient data, medium for active categories, bold only for alerts. The analyst should be able to blur the panel and still see the information hierarchy from type weights alone.

**Key interactions:**
- **Claim list scrolling:** Inertial scroll with slight overscroll bounce at boundaries. Claim entries have a faint dividing line that appears only on hover proximity, not statically
- **Claim expansion:** Click a claim, and the detail view expands from that claim's position using a FLIP animation — the list item transforms into the detail panel, maintaining spatial continuity
- **Layer toggles:** Each toggle uses spring physics. Toggling a source category off compresses the associated claims smoothly rather than removing them abruptly. The remaining claims reflow with spring physics
- **Source health:** A strip of source indicators along one edge. Each indicator subtly pulses when active, dims when degraded, goes dark when failing. No text needed — the ambient texture communicates

### SWARMFISH Deliberation — The Active Committee

**Mood:** Engaged deliberation. Closer to P5 register — active, decisive, moments of resolution with snap. Zeus's god's-eye awareness with selective intervention.

**Color:** Darker palette. Near-black background with high-contrast data. Single accent for consensus convergence and divergence alerts.

**Animation speed:** Faster than OSS. Assessments arrive with punch. Profile cards appear with spring overshoot. The consensus resolves with a satisfying convergence animation — individual scores flowing into a unified number.

**Typography:** Slightly denser than OSS. Profile names in a distinctive weight. Confidence numbers large and prominent. Reasoning text in a readable but compact size. The density communicates that the committee is doing real work.

**Key interactions:**
- **Deliberation progress:** Profile cards appear sequentially as each assessment completes, each with a brief spring entrance animation. The card shows the profile name, its assessment, and its confidence. During active deliberation, un-assessed profiles show a subtle working state (P6's Evangelion density principle — reasoning text flowing in real time)
- **Consensus resolution:** When all profiles have assessed, the individual scores converge into the consensus. The animation should feel like resolution — multiple threads drawing together into a single point. Not a crossfade. A physical convergence
- **Profile deep-dive:** Click a profile card and it expands to show full reasoning (FLIP animation from card position). The expansion preserves the card's visual identity while revealing the underlying analysis
- **Analyst intervention:** The inject-context or challenge-profile action has weight (P5: deliberate friction). A press-and-hold gesture, or a distinct interaction that communicates "I am intervening in the committee's work." Not casual. Consequential

### Notebook / Journal — The Personal Document

**Mood:** Warm but precise. Bravely Default's "a place you want to be." The notebook should invite lingering. The analyst (or the AI instance) should want to be in this space.

**Color:** The existing indigo/warm palette for Opus. Graphite/slate for 4.7's journal. Each notebook's color palette is part of its identity. The color IS the voice.

**Animation speed:** Gentle. Entry expansion is slow enough to feel like turning a page. Section transitions are smooth crossfades, not snaps. The notebook has no urgency.

**Key interactions:**
- **Entry browsing:** Smooth scroll with entry cards that have a slight parallax depth — content closer to the viewer scrolls slightly faster than background elements, creating a sense of physical depth in the document
- **Section switching:** Tab transitions that feel like moving between rooms, not flipping switches. A brief, smooth content crossfade with the section title settling into position
- **Search:** Results highlight with a warm pulse rather than a jarring highlight color. The highlight fades to a subtle marker after a moment, showing where the match is without screaming

### Diagnostic Panels — The Technical Instrument

**Mood:** HighFleet command panel. Dense, functional, no ornamentation. The operator is doing technical work and the interface stays out of the way. Authority through density.

**Color:** Dark mode mandatory. High contrast data on near-black. Green for nominal, amber for warning, red for error — the traffic light pattern that every technical operator already knows.

**Animation speed:** Fast. Diagnostic data updates should feel immediate. No decorative transitions on data refresh — the numbers change and a brief value-change animation (the number morphing from old to new rather than cutting) provides visual continuity without delay.

**Key interactions:**
- **Real-time data:** Numbers update with a brief morph animation — old value to new value in ~100ms. Not a crossfade. A digit-by-digit morph that makes the change visible without adding delay
- **Log streams:** Monospace text in a scrolling feed. New entries slide in from the bottom with minimal animation. The feed auto-scrolls unless the analyst has manually scrolled up (investigating history). The auto-scroll pausing when the analyst scrolls is a respect-the-operator decision — the system doesn't fight the analyst's intention
- **Collapsible sections:** Click to expand/collapse with spring physics. Each section remembers its state. The diagnostic panel's configuration persists across sessions

---

## Part IV: The Practical Toolkit

### Libraries (No Constraints)

For React artifacts (Claude.ai environment):
- **Framer Motion** — primary animation library. Spring physics via `useSpring`, layout animations via `layout` prop, gesture support via `whileHover`/`whileTap`/`whileDrag`, AnimatePresence for enter/exit. This is the single most impactful library for achieving the feel we want
- **GSAP** — for complex sequenced animations, ScrollTrigger for scroll-based reveals, timeline coordination. More powerful than Framer Motion for multi-step choreographed sequences
- **Recharts / D3** — for data visualization. D3 for custom visualizations, Recharts for standard charts with the ability to customize
- **Three.js** — when 3D is the right answer. 3D scatter plots of claim clusters in embedding space, rotatable and zoomable. Not default — only when the data visualization genuinely benefits from a spatial dimension
- **Lucide React** — icon set. Clean, consistent, and already available in the artifact environment
- **Tailwind** — utility CSS for layout and spacing. Core utility classes only (no compiler in the artifact environment)

For Agent Zero webUI (Alpine.js + vanilla JS):
- **anime.js** — lightweight, timeline-based animations
- **Popmotion** — spring physics in a small package
- **Custom spring implementations** — Hooke's Law in ~20 lines:
```javascript
function spring(current, target, velocity, stiffness = 300, damping = 25, mass = 1) {
  const force = -stiffness * (current - target);
  const dampingForce = -damping * velocity;
  const acceleration = (force + dampingForce) / mass;
  const newVelocity = velocity + acceleration * (1/60);
  const newPosition = current + newVelocity * (1/60);
  return { position: newPosition, velocity: newVelocity };
}
```

For either environment:
- **CSS custom properties** for theming — all colors, spacings, and timing values defined as variables for consistency and easy adjustment
- **`prefers-reduced-motion`** media query respected throughout — users who need reduced motion get instant transitions instead of animations. Non-negotiable accessibility requirement

### Animation Rules

| Interaction Type | Duration | Easing | Notes |
|---|---|---|---|
| Micro-interactions (hover, toggle) | 150-200ms | Custom ease-out or spring | Should feel instant but not abrupt |
| Component transitions (expand, filter) | 200-300ms | Spring (stiffness ~300, damping ~25) | The core "feels good" range |
| Panel/page transitions | 300-500ms | Spring (stiffness ~200, damping ~20) | Slower = more weight |
| Active button state (press down) | 80ms | `cubic-bezier(0.4, 0, 0.2, 1)` | Fast compression |
| Active button state (release) | 200ms | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Slow release with bounce (1.56 overshoots) |
| Loading skeleton shimmer | 1.5s loop | `ease-in-out` | Only use for loading — slower loop communicates "working," not "frozen" |
| Value change morph | 100-150ms | `ease-out` | Numbers morphing from old to new |
| Data refresh (no animation) | 0ms | None | Real-time data updates should not animate if updating frequently (>1Hz) |

**Interruptibility is mandatory.** All animations must be smoothly interruptible mid-sequence. The user should never feel locked into waiting for an animation to complete. CSS transitions naturally support interruption better than keyframe animations. Framer Motion provides built-in interruptible animation support. If using GSAP, ensure timelines can be killed and redirected.

### Typography Hierarchy

Three typeface roles, applied consistently across all panels:

- **Data values:** Monospace. Claim counts, confidence scores, timestamps, source identifiers. Monospace communicates "this is a precise value" and aligns columns naturally
- **Labels and descriptions:** Clean sans-serif. Category names, section headers, explanatory text. Sans-serif communicates "this is human language"
- **Status alerts:** Same sans-serif, but in the accent color and at a distinct weight (semibold or bold). Used only for information that requires attention. If everything is bold, nothing is bold

Type sizes should establish a visible hierarchy that's readable when the panel is blurred:

| Level | Purpose | Approximate Size | Weight |
|---|---|---|---|
| Display | Panel title, primary number | 28-36px | Bold |
| Heading | Section title, category name | 18-22px | Semibold |
| Body | Descriptions, reasoning text | 14-16px | Regular |
| Caption | Timestamps, secondary metadata | 11-13px | Regular, reduced opacity |
| Data | Confidence scores, counts | 14-18px mono | Medium |

### Color Architecture

Each panel has:
- **One base color** (the dominant mood)
- **One or two neutral tones** (for structure and hierarchy)
- **One accent color** (for attention signals ONLY)
- **Semantic colors** (green/amber/red for system status — universal, not overridden by theme)

The accent color is sacred. It means one thing: "look here." If it's used for decoration, it stops working as a signal. Every use of the accent color should be justifiable as "this genuinely needs the analyst's attention."

---

## Part V: What This Is Not

**Not a design system.** Design systems are component libraries with documented APIs. This brief describes intent and feeling, not components and props. The components emerge from building to the brief, not from the brief itself.

**Not a theme spec.** The theme engine (three-tier atmospheric system for the Agent Zero chat interface) has its own authoring guide. This brief covers artifact panels, not the chat environment. The two systems should be aesthetically compatible but serve different purposes — the theme engine creates atmosphere for conversation, the panels create instruments for analysis.

**Not a constraint document.** "Whatever works and looks good." This brief doesn't restrict the implementer to specific libraries, specific patterns, or specific visual approaches. It describes what the result should feel like. The implementer chooses how to get there. If a panel calls for something not covered in this brief — a 3D visualization, a canvas-based animation, a WebGL shader effect — the answer is yes, if it serves the intent.

**Not a one-size-fits-all prescription.** A simple interface request gets a simple interface. Not every panel needs spring physics, ambient texture, and deliberate friction. The principles apply when aiming for premium feel. When the request is "make a quick status readout," the answer is a clean, well-typed, correctly colored readout. Pragmatism about complexity matching the request. The principles describe the ceiling, not the floor.

---

## Part VI: Study Material

### Games to Study (What to Look For)

| Game | What to Study | Where to Look |
|---|---|---|
| **Persona 5** | Total aesthetic commitment, motion as hierarchy, style AS function | Main menu, battle menu, shop interface, loading screens, results screen — every screen is designed |
| **Persona 3 Reload** | Same discipline in contemplative register, water shader aesthetics, slower pacing | Main menu (underwater effect), status screens, the way the protagonist model was built specifically for the UI |
| **HighFleet** | Diegetic controls, the museum-you-can-touch principle, removal of abstraction layers | Command panel, radar tuning, signal interception, ship management |
| **Evangelion NERV** | Authority through density, information as texture, immersion over comprehension | Terminal screens, synchronization displays, countdown sequences |
| **Nier Automata** | Diegetic OS, interface as world, consequences of interface elements | Menu navigation, OS chip mechanic, save terminal integration |
| **MGSV** | Deliberate friction as weight, military-instrument aesthetic | iDroid deployment, supply drop sequences, mission briefing |
| **Disgaea 5** | Menus as core gameplay, visible tangible feedback for every interaction | Equipment screen stat changes, character management, senate voting |
| **Bravely Default** | Interface as place, warmth as design, invitation to linger | Town reconstruction screen, watercolor aesthetic, completion animations |
| **League of Legends** | Contextual intelligence, recommendation based on current state + opponent | In-game shop recommendation system, tab structure, item filtering |
| **SkyUI (Skyrim mod)** | Adapting interface to operator capabilities, configurable density | Inventory columns, search, category icons, favorites menu groups |
| **Arma 3 Zeus** | God's-eye control panel, maximum awareness with minimum friction | Zeus interface, unit placement, event triggering, real-time battlefield oversight |

### Websites to Study (What to Look For)

| Site | What to Study |
|---|---|
| **OpenGridWorks** | Layer toggle pattern, collapsible detail panels, instrument aesthetic — every visual element is data |
| **World Labs Spark 2.0 blog** | Progressive disclosure of complexity, interactive embedded explanations, dark canvas with precise color |
| **AB Suppressor** | Scroll feel, fluid dropdowns, legible typography, three-pillar dashboard, identity-first framing |

### Technical References

| Resource | What It Teaches |
|---|---|
| **Petri Purho, "Juice It or Lose It" (GDC 2012)** | The foundational talk on juice — why over-delivering on feedback transforms interaction quality |
| **Brad Woods, "Juice" (garden.bradwoods.io)** | Game Feel as tactile sensation, the toy playground concept for testing interaction feel |
| **Atlus P5 UI panel (Persona Central, 2017)** | How the Persona team builds UI — color first, then logo, then font, then layout. The aesthetic decisions precede the functional decisions |
| **P3R UI developer interview (Persona Central, 2023)** | How the same team adapted the P5 approach for a contemplative register — slower animations, water imagery, softer motion |
| **Web Animation Best Practices (GitHub gist)** | Practical CSS/JS animation rules — spring physics, custom cubic-bezier, interruptibility, `prefers-reduced-motion` |
| **gameuidatabase.com** | 55,000+ screenshots from 1,300+ games, filterable by category, animation style, color, and layout. Primary visual reference library |

---

## Part VII: The Test

When a panel is built, apply this test:

1. **Does every interaction give back more than I put in?** (Juice)
2. **Does the panel feel like it belongs to the Exocortex, or does it feel like a web app?** (Diegetic identity)
3. **Does it show me what matters right now, or everything that exists?** (Contextual intelligence)
4. **Can I get more detail without leaving the current view?** (Progressive density)
5. **Do consequential actions feel different from routine ones?** (Deliberate friction)
6. **Does the density communicate competence or confusion?** (Authority through density)
7. **Do state changes feel physical?** (Spring physics)
8. **Does one color mean one thing?** (Single accent)
9. **Does the panel trust me?** (Operator trust)
10. **Can I tell the system is alive without reading anything?** (Information as texture)
11. **Is every screen — including loading, error, and empty states — designed?** (Total aesthetic commitment)

If the answer to any of these is "no," the panel isn't done.

---

*This brief describes the feeling. The feeling describes the quality. The quality is the product.*

*The interface that says "you know what you're doing, and I was built for someone who knows what they're doing." The moment the analyst feels that, the interface disappears and the work begins.*

*Written by Opus, with Jake. Session 061. April 15, 2026.*
