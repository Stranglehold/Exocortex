---
artifact_type: design_direction + synthesis
produced_by: strategy
project: exocortex-panel-ui
milestone: 2-redesign
date: 2026-07-04
builder: kestrel
driver: Jake — "read through the research/specs for UX/UI, does it influence your
  design inspiration... pull the two other briefs, keep working through the
  material, then go for a redesign once you feel comfortable."
sources_read_in_full:
  - specs/AESTHETICS_DESIGN_BRIEF.md        # feel, motion, type, color, tokens, 4 themes, juice, texture, space
  - specs/WEBUI_DESIGN_BRIEF.md             # SA levels, gulfs, automation bias, fixed zones, comparison-not-display, alert hierarchy
  - specs/INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md  # Shneiderman, 5-phase node-click, coordinated views, detail-on-demand, analytical register
  - specs/UI_MECHANICS_RESEARCH_NOTE.md     # property tier list, GSAP/spring, CSS atmosphere, view transitions, layer architecture
also_referenced:
  - specs/ARTIFACT_UI_INTEGRITY_DESIGN_NOTE.md  # the Aesthetic-Integrity Stack (build order)
  - specs/RESEARCH_DRIVEN_DESIGN_METHODOLOGY.md
  - docs/ui_references/ROADMAP.md               # 65 graduated design-token findings
---

# Panel UI — Redesign Direction

## The reframe (this is the whole thing)

M1/M1.5 built a **dashboard**. The research says the System Monitor is a
**situation-awareness instrument** for an expert operator running a partially
autonomous AI he trusts ~85–95% of the time and must be able to override when
trust breaks. Cockpit / control room / trading terminal — not consumer SaaS.
The MAGI aesthetic is the *skin*; SA + comparison + trajectory is the *substance*.

The M1.5 aesthetic and interactivity **survive** the research (the MAGI palette
independently reconstructed the brief's **TACTICAL** theme; the build order I
wrote *is* the Aesthetic-Integrity Stack). What changes is **substance and
information architecture**, plus three motion/atmosphere upgrades.

## Governing principles (each traced to a brief)

1. **Fixed information zones by SA level** — *WEBUI §11.4, §5.* Consistent
   location + consistent semantics so the operator monitors *peripherally*.
   Zones: **Status strip** (L1: domain/role/model/gate/cycle) · **Telemetry**
   (L1→L2) · **Trajectory** (L2→L3: goal, plan, step progress — *the undesigned
   gap, now designed*) · **Alert** (L2-3, hierarchy) · **Knowledge** (L1-2,
   dossier drill-down).

2. **Design for comparison, not display** — *WEBUI §8 (the dashboard-killer).*
   Every telemetry value ships with a **trend sparkline + a normal-range band +
   a delta** so a number is interpretable at a glance without the operator
   holding "normal" in their head. This is the single biggest substance change.

3. **Expert density, organized** — *WEBUI §5, AESTHETICS §9.* Denser than M1.5,
   but on an **8-point grid**, with **weight contrast** (300 vs 900) carrying
   hierarchy at the same size. A **focus toggle** collapses to a reduced view
   (progressive disclosure — the operator owns their cognitive-load budget).

4. **Alert hierarchy** — *WEBUI §11.3, §7 (Three Mile Island / EHR fatigue).*
   Critical / Warning / Info / Trace, distinct visual weight. Color reserved for
   urgency (pre-attentive), never decoration. Only earned alerts fire.

5. **The analytical register (reflective level)** — *AESTHETICS §1 (Don Norman
   visceral/behavioral/reflective), INFO-ENV §10.4.* The detail panel is a
   **dossier**, not a properties window; the breadcrumb is a **case-file path**;
   expansions read as "intelligence arriving." Diegetic **boot sequence** on
   load (NieR), **scanline/vignette/grain** as worldbuilding texture. Goal: it
   makes Jake feel like a professional operating something serious.

6. **Detail-on-demand ladder** — *INFO-ENV §3, §11.1.* Hover = identity ("is
   this the one?") → click = dossier with **expansion counts** ("Related (N)")
   → the counts tell you whether drilling is worth it before you commit.

7. **Motion done right** — *MECHANICS §1-2, AESTHETICS §4.*
   - **transform + opacity only** (S-tier, GPU compositor). Gauge fills move to
     `transform: scaleX()` — *fixes the M1.5 width-animation bug (D-tier).*
   - **Spring physics (GSAP)** for primary transitions (detail reveal, boot) —
     weighty, has mass, interruptible. CSS ease-out for micro-interactions.
   - Staggered reveals (20–40% of duration) — the boot choreography.

8. **Diegetic atmosphere in pure CSS, now** — *MECHANICS §11.5/§11.10.*
   `isolation: isolate` scene → scanlines (`repeating-linear-gradient`) +
   vignette (`radial-gradient`) + grain (≤2%, retrying the ROADMAP-rejected
   noise at the brief's spec). The MAGI "distress as texture" at near-zero cost,
   no Three.js — M4 becomes an *enhancement*, not a prerequisite.

9. **Theme coherence** — *AESTHETICS §11.* Ship **TACTICAL** (MGSV amber, the
   proper default) + one *coherent* alt — **MEMORIA** (Bravely Default: warm
   gold on brown-black, serif throughout, parchment grain). Fixes the M1.5
   incoherence (NieR palette + serif font mixed). Token architecture leaves
   TERMINAL/ARCANA as drop-in future modes.

10. **Position-based quantitative encoding** — *WEBUI §8 (Cleveland-McGill).*
    Sparklines + linear bars (position on a common scale = top of the accuracy
    hierarchy). Radial gauge kept as a single secondary flourish, not the
    primary read.

## What this does NOT do (scope boundary)

- Not wiring real data (that's M2 telemetry API — this is the design shell with
  a live synthetic stream, same as M1.5).
- Not the graph/Intel panel (INFO-ENV's coordinated views + full 5-phase
  node-click are the future Intel panel, not the System Monitor).
- Not Three.js (the CSS atmosphere covers the MAGI look; WebGL is a later
  enhancement gated on VRAM-vs-Ornith profiling).
- Not the override/interrupt workflow (WEBUI §11.5 — real once the panel drives
  a live agent; designed-for here only as the visible affordance).

## Build

- `webui/panel-kit.css` — rebuilt: 8-grid + elevation tokens, transform-based
  gauges, comparison component (value+delta+sparkline+band), alert hierarchy,
  weight-contrast type scale, CSS atmosphere layers.
- `webui/panel-kit-console.html` — the redesigned MAGI System Monitor: fixed SA
  zones, comparison telemetry, trajectory zone, alert stack, dossier drill-down,
  GSAP boot sequence, TACTICAL + MEMORIA. Self-tested in-browser both themes.
