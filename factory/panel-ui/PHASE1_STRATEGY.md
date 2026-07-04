---
artifact_type: requirements_document + milestone_plan + risk_register
produced_by: strategy
project: exocortex-panel-ui
milestone: 0
date: 2026-07-04
builder: kestrel
client: jake
design_authority: opus
evidence:
  - type: spec_read
    docs: [PANEL_DESIGN_OPERATING_PRINCIPLE.md, SOFTWARE_FACTORY_ARCHITECTURE.md, A2A_HUB_ARCHITECTURE.md]
  - type: wiki_search
    method: repo/plugin survey (the "prior patterns" step)
    found: [15-theme system + theme-store/editor, right-canvas panel contract (exo-ops/workshop),
            exo-artifact runtime, docs/ui_references design-token extractions]
  - type: visual_reference
    viewed: [Evangelion/evangelion-magi-system-monitor (System panel target),
             mgsv-database (iDroid master-detail component pattern)]
  - type: stack_decision
    finding: "A0 web UI is Alpine.js + vanilla JS/CSS, NOT React (spec was wrong)"
    resolution: "Opus ratified Option B — native Alpine + vanilla Three.js + GSAP. Spec revised."
  - type: theme_schema
    resolved_vars: [--color-accent, --color-background, --color-text, --color-panel,
                    --color-border, --color-primary, --color-secondary, --font-family-main]
    note: "theme-store sets -dark/-light; A0 resolves --color-X = var(--color-X-<mode>)"
---

# Panel UI — Phase 1 Strategy (Requirements + Milestones + Risks)

## Project
The Exocortex command console — a diegetic game-UI (MAGI/iDroid/NieR/HighFleet) that
makes operating the agents feel like sitting at a sovereign AI ops center. First
output of the software factory. Built **native** (Alpine + vanilla JS/CSS +
vanilla Three.js + GSAP), extending the existing right-canvas panels + 15-theme
system. Build order is integrity-first (integrity → function → clarity → aesthetics →
mechanics → delight). First panel: **System Monitor (MAGI amber)**.

## Ratified decisions (Opus, 2026-07-04)
- **Stack:** Option B — native Alpine + vanilla JS + vanilla Three.js + GSAP. No React/R3F.
- **Where:** extend the existing right-canvas panels (System Monitor becomes a surface
  next to exo-ops/workshop). Full-screen mode is a later enhancement.
- **Data:** telemetry API (M2) — a plugin `api/` endpoint gathers metrics, serves JSON
  the panel polls. Browser can't reach nvidia-smi/Docker/JSONL directly.
- **Default aesthetic:** MAGI — amber monochrome on dark, angular bordered sections,
  hex grid, bilingual labels where sensible. Amber palette + angular layout = M1;
  CRT scanlines + hex grid = M4.

## Requirements (traceable)

### M1 — Component Library (theme-aware, no 3D, no live data)
- **REQ-M1-01** Seven components: DataCard, TreeNav, StatusBar, BreadcrumbNav,
  DetailPanel, CycleTypeCard, TelemetryGauge.
- **REQ-M1-02** Every component reads theme CSS custom properties (`--color-accent`,
  `--color-background`, `--color-text`, `--color-panel`, `--color-border`,
  `--font-family-main`) — zero hard-coded colors. Switching theme re-skins them with
  no code change.
- **REQ-M1-03** MAGI amber/angular default: amber accent, near-black ground, sharp
  bordered sections, monospace telemetry readouts (Share Tech Mono / theme font).
- **REQ-M1-04** Delivered as `webui/panel-kit.css` (+ `panel-kit.js` only where
  interactivity requires it: TreeNav expand/collapse, TelemetryGauge fill, DataCard trend).
- **REQ-M1-05** A `panel-kit-showcase.html` renders all 7 with sample data + a theme
  toggle (amber/MAGI + one contrasting theme) — the verification surface.
- **REQ-M1-06** Slots into the existing right-canvas panel contract (no x-data on the
  surface root; content lives in an x-component). No new global Alpine store.
- **Acceptance (GATE before M2):** all 7 render correctly; look right in ≥2 themes;
  no hard-coded colors (grep); integrity — nothing shows a value it doesn't have.

### M2 — Telemetry API
- **REQ-M2-01** Plugin endpoint (`api/…`) serving JSON: inference tok/s, VRAM
  used/free, model name, container health (up/down, cycle count), methodology trends
  (completion rate, affect distribution).
- **REQ-M2-02** Clean, documented shape (other panels reuse it). Same pattern as the
  Docker-MCP-server, exposed as a pollable HTTP endpoint.
- **Acceptance:** endpoint returns real values (cross-checked against nvidia-smi /
  docker / the methodology JSONL); documented schema.

### M3 — System Monitor panel (wire it together, every value real)
- **REQ-M3-01** Assemble M1 components into the MAGI System Monitor as a right-canvas
  surface, polling M2. **REQ-M3-02** Integrity gate: every displayed value is real,
  every control works. **Acceptance:** live panel, no placeholder/fake data.

### M4 — Three.js immersive layer (MAGI atmosphere)
- **REQ-M4-01** CRT scanlines + hex grid + amber glow as a composable, toggleable
  Tier-3 theme layer. **REQ-M4-02** "Effect you notice has failed" — 3% scanlines etc.
  **Acceptance:** 60fps budget; **profiled for VRAM contention with Ornith** (must not
  evict Ornith's KV cache — Opus's added risk).

*(Later phases: Office/Intel/SWARMFISH panels + theme-selector mode-switch.)*

## Risk Register
- **R1 — Stack mismatch (RESOLVED):** A0 is Alpine, not React → Option B ratified.
- **R2 — Data reachability:** browser can't call nvidia-smi/Docker/JSONL → mitigated by
  M2 being an explicit milestone (telemetry API).
- **R3 — GPU contention (Opus):** M4's WebGL shares the 3090 with Ornith. Keep the
  shader pipeline tiny; profile VRAM; if it evicts Ornith's KV cache, the atmosphere
  isn't worth it. Degrade/disable gracefully.
- **R4 — Scope:** the full console is a 5-phase estimate. Land M1–M3 (a real, useful
  System panel) before 3D + other panels.
- **R5 — v1.20 canvas contract fragility:** surface root must not carry x-data/inline
  content (collapses to 0×0). Mitigated by following the exo-ops/workshop pattern exactly.

## Factory process
Receipts at every handoff; **quality gate on M1 before M2 starts** (fresh-context
review: render? theme-switch? no hard-coded colors?); Jake is the client for aesthetic
decisions; Opus is design authority for architecture revisions.
