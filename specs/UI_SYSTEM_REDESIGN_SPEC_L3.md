# UI_SYSTEM_REDESIGN_SPEC_L3.md
# Exocortex Interface Redesign: Full-System Specification

*Written March 2026 by Kestrel following a research session covering UI/UX safety principles, aesthetic design systems, information environment design, and artifact data channels. Intended as a handoff document to Opus for architectural review and implementation direction.*

*This spec synthesizes four companion documents into a single actionable design plan:*
- *`WEBUI_DESIGN_BRIEF.md` — functional safety, situation awareness, automation bias*
- *`AESTHETICS_DESIGN_BRIEF.md` — visual language, token system, four reference themes*
- *`INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md` — graph interaction, analyst workflow, node-click spec*
- *`ARTIFACT_DATA_CHANNEL_SPEC.md` — live data channel protocol, test methodology*

---

## 1. Why This Work Exists

The Exocortex stack is architecturally sophisticated — 12 layers of deterministic scaffolding, an OSS intelligence ledger, entity graph, SWARMFISH consensus engine, episodic memory, sleep consolidation. The interface through which an analyst interacts with all of this was built incrementally, feature by feature, with no overarching visual language or design system.

The result: five front-end surfaces (three artifacts, two service frontends) that do not look or behave like they belong to the same system. No shared token system. No consistent interaction patterns. A broken data channel. A graph visualization that shows nodes but doesn't let you investigate them.

Three sessions of deep cross-industry research established what a system of this type should look and feel like. We now have the theory. This spec translates it into an implementation plan.

**The research finding that matters most:** the Exocortex interface serves an expert analyst working with a partially autonomous AI agent on intelligence analysis tasks. The closest analogues are aircraft cockpits, nuclear control rooms, Palantir Gotham, and i2 Analyst's Notebook — not consumer chat apps. Every design decision should be evaluated against that frame.

---

## 2. Research Foundation (Summary)

### 2.1 From WEBUI_DESIGN_BRIEF.md — Functional Principles

**The two failure modes every interface either solves or suffers:**
- *Gulf of Execution* — user cannot map intent to available actions
- *Gulf of Evaluation* — user cannot perceive current system state

For AI agent interfaces, **the Gulf of Evaluation dominates**. The agent takes actions the user didn't explicitly request, using tools the user didn't know existed, for reasons the user cannot see. Every design decision should be evaluated: *does this help the analyst understand what the agent is doing and why?*

**Automation bias** (Parasuraman & Manzey, 2010): at 85–95% reliability, humans working alongside AI recommendations perform *worse* than the AI alone because they reduce independent analysis. This is not a failure of intelligence — it is a feature of human cognition. The mitigation is deliberate: show uncertainty explicitly, reveal reasoning before conclusions, make overriding the agent easy, design for the 15% failure case not just the 85% success case.

**Situation Awareness** (Endsley, 1995): three levels — Level 1 (perception: what tool fired, what the agent said), Level 2 (comprehension: what is the agent currently doing and why), Level 3 (projection: where is this heading, when should I intervene). Current Exocortex UI supports Level 1 inadequately and Level 2/3 not at all. The Stack Status tool is the seed of Level 1. Level 2 and 3 are the design gap.

**Alert calibration:** the supervisor loop, epistemic integrity layer, and action boundary all fire signals. If they all fire at the same visual weight, the analyst will habituate and miss the critical one. A severity hierarchy with distinct visual treatment is required: Critical (requires action) → Warning (calls attention) → Informational (available) → Trace (in log, not primary feed).

### 2.2 From AESTHETICS_DESIGN_BRIEF.md — Visual Language

**Norman's three levels:** Visceral (first impression before interaction), Behavioral (usability and feedback), Reflective (does using this interface make the analyst feel like a professional doing important work). All three must be designed. Most systems stop at Behavioral.

**The reference game analysis established four aesthetic philosophies, each a coherent design commitment:**

| Theme | Game | Register | Core palette | Typography |
|-------|------|---------|-------------|-----------|
| **TACTICAL** | MGS5 | Military operational display | Amber on near-black | Condensed display + Inter |
| **TERMINAL** | Nier: Automata | Diegetic android OS | Warm beige monochrome | All-monospace |
| **ARCANA** | Persona 5 | Graphic design manifesto | Black / white / red only | Heavy condensed, aggressive |
| **MEMORIA** | Bravely Default | Material warmth | Gold on deep brown | Serif, layered depth |

The Exocortex interface ships **TACTICAL as default**. The token architecture makes the others swappable without code changes.

**The design token architecture:** three layers — Primitive (raw values), Semantic (meaning-assigned), Component (component-specific). Theme swapping replaces only Primitive token values. Everything above adapts automatically.

**Motion:** spring physics for primary transitions (not cubic-bezier — spring physics have mass and settle naturally). Duration budget: 100ms micro, 200ms small, 300ms medium, 450ms large. Easing: ease-out for elements entering, ease-in for elements leaving, standard for elements staying on screen.

**Typography:** weight contrast is the primary hierarchy tool. Inter for body/labels, JetBrains Mono for all numeric and code content, condensed display face (Bebas Neue or Barlow Condensed) for TACTICAL headings. The monospace rule for data values is non-negotiable — it aligns columns and visually separates "data" from "label."

**Expert density:** the Exocortex analyst is a trained expert. The interface should optimize for expert throughput, not first-time learnability. High information density with organized zones is correct. Reducing density to "simplify" forces experts to navigate for information they could have seen at a glance.

### 2.3 From INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md — Graph Interaction

The fundamental problem: narrow visual window, vast non-linear information space. Every design decision is an answer to that tension.

**Shneiderman's extended mantra for discovery tasks:** Overview → Zoom/Filter → Relate/Compare → Details on Demand.

**The five-phase node-click specification** (full detail in INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md §3):
1. **< 100ms:** Selection state. Connected edges highlight. Unconnected nodes dim to 20% opacity.
2. **< 300ms:** Hover card. Minimal identity fields only — "is this the entity I want?"
3. **< 500ms (deliberate click):** Detail panel slides in alongside canvas (non-modal). Full properties + available expansion counts ("Associates (14)", "Documents (3)").
4. **On expand click:** New nodes animate in from source. Local layout adjustment (not full relayout). New nodes in distinct "just-arrived" state.
5. **Breadcrumb trail:** navigation path showing Entity A → Associates → Entity B. Jumpable.

**Non-destructive filtering:** filtered elements go to 20% opacity, not hidden. The analyst retains awareness of the complete information space.

**Coordinated views:** the OSS ledger and ontology graph should eventually support synchronized graph + timeline + table views. Selection in one propagates to all.

**The ten design principles** from Palantir/Maltego/ATAK analysis (full list in INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md §13) — the most directly applicable:
- Domain-native entity types (person, organization, claim, event — not generic "node")
- Progressive disclosure at every level
- Node interaction crafted at every phase
- Filtering non-destructive and visually honest
- Layout algorithm matches data structure
- Annotations and provenance first-class

### 2.4 From ARTIFACT_DATA_CHANNEL_SPEC.md — Live Data

Artifacts render in `srcdoc` iframes (origin: `about:srcdoc`). Direct `fetch` to Agent Zero API endpoints fails due to same-origin policy. The solution is a **postMessage data channel** between artifact and `artifact-panel.js`.

**Two-tier polling:**
- Tier 1 (heartbeat, 10s): lightweight health/counts endpoint, < 2KB response. Detects change.
- Tier 2 (data fetch, on change or 60s max): full data. Runs only when heartbeat signals new data.

At steady state (no new ingestion): 6 × 2KB heartbeat polls per minute. Negligible load. The expensive query fires only when data actually changed.

**The `ArtifactDataChannel` class** (specified in §3 and §4 of the channel spec) handles subscription management, polling intervals, and retry with exponential backoff in `artifact-panel.js`. Each artifact uses a lightweight `ArtifactDataClient` class to subscribe and receive data.

**The artifact manifest** (`manifest.json` alongside each artifact HTML) declares: endpoints required, polling intervals, DOM selectors for test assertions, data binding assertions.

---

## 3. Current State Audit

### 3.1 Inventory

| Surface | Location | Type | Current state |
|---------|---------|------|--------------|
| Artifact gallery | `patches/artifacts/index.html` | Navigation | Working but wrong register |
| Network graph | `patches/artifacts/network_graph.html` | D3 visualization | Static, incomplete interaction |
| OSS control panel | `patches/artifacts/oss_control_panel.html` | Dashboard | **Data channel broken** |
| OSS service UI | `services/oss/src/templates/index.html` | Standalone web app | Functional, inconsistent style |
| SWARMFISH UI | `services/swarmfish/src/templates/index.html` | Standalone web app | Functional, inconsistent style |
| Artifact panel | `patches/webui/artifact-panel.css` + `.js` | Panel system | Well-built, tokenized |
| Sidebar artifacts | `patches/webui/components/sidebar/artifacts/` | Sidebar integration | Functional |

### 3.2 Critical Bug: OSS Control Panel Data Channel

`oss_control_panel.html` makes direct `fetch('http://localhost:7731/...')` calls from inside a `srcdoc` iframe. The iframe's origin is `about:srcdoc`. The OSS Flask service does not emit CORS headers for that origin. Every API call fails silently. The panel renders but shows `—` for all values.

This is the only broken-functionality issue in the audit. Everything else is design debt, not a bug.

**Fix:** Route OSS control panel API calls through the postMessage data channel (implemented in Step 2 below). The panel sends `data-subscribe` messages; `artifact-panel.js` makes the actual fetch to Agent Zero's OSS proxy endpoints; responses come back via `data-response`.

*Alternative fix if preferred:* Add CORS headers to the OSS Flask service allowing `about:srcdoc` and `null` origins. Simpler but less architecturally clean — every artifact would still need direct access to the OSS service rather than going through Agent Zero's authenticated API layer.

### 3.3 Design Audit Findings

**No design token system.**
Five surfaces, five independent color systems:

```
index.html:          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)
network_graph.html:  background: #1a1a2e; graph container: #16213e
oss_control_panel:   body: #111827; cards: #1f2937
OSS service:         own grey scale, green accent (#22c55e)
SWARMFISH:           own palette, different greens and greys
artifact-panel.css:  var(--color-panel) — correctly tokenized, isolated
```

None form a visual family. The token system from AESTHETICS_DESIGN_BRIEF.md resolves this entirely: one `design-tokens.css` file, all surfaces reference the same semantic tokens.

**Wrong register on `index.html`.**
The blue-purple gradient and glassmorphism cards read as a weekend project page. The `📦` emoji in the H1, the blue gradient text on "Agent Zero Artifacts" — this is consumer aesthetic, not operational analyst tool. Per the AESTHETICS_DESIGN_BRIEF.md, the Exocortex register is **TACTICAL**: amber on near-black, condensed display typography, purposeful density, no decorative gradients.

**Network graph interaction is incomplete.**
The D3 graph implements Phase 2 of the five-phase node-click spec (hover tooltip for identity). Missing:
- Phase 1: neighbor edge highlight + non-neighbor dimming on click
- Phase 3: detail panel (non-modal, slides in alongside canvas)
- Phase 4: typed expansions with counts
- Phase 5: breadcrumb trail

The graph's data model (nodes with category, id; edges with source/target) supports the full interaction spec. The structure is there. The interaction layer is not.

**Typography: no hierarchy, no monospace for data.**
All surfaces use `system-ui` or `-apple-system` at a single weight with size-only hierarchy. Data values (claim counts, source names, timestamps) are styled identically to labels. This violates both the weight-contrast principle and the monospace-for-data rule from AESTHETICS_DESIGN_BRIEF.md §5.

**OSS and SWARMFISH services: functionally solid, visually isolated.**
These are genuinely well-built front-ends. Alpine.js architecture is clean. Information density is appropriate. The OSS multi-tab layout (Feed, Staging, Hypotheses, Sources, Admin) is correct for the domain. SWARMFISH's streaming prediction cards are the right interaction pattern for that use case.

The problem is visual isolation: different color scales, different component styles, different typography decisions. They need palette and typography alignment, not architectural changes.

**`artifact-panel.css` / `artifact-panel.js` are the best-built surfaces.**
These use CSS custom properties correctly (`var(--color-panel)`, `var(--color-border)`, `var(--color-primary)`). The panel architecture — multi-tab, resize sash, skeleton loader, zoom injection — is production-quality. This is the pattern everything else should follow.

### 3.4 What Is Good and Should Be Preserved

- `artifact-panel.js` multi-tab architecture and localStorage persistence
- `artifact-panel.css` CSS variable architecture
- OSS service Alpine.js multi-tab layout and information hierarchy
- OSS service staging queue workflow (claim review + promote/reject)
- SWARMFISH streaming prediction card pattern
- Network graph D3 force-directed layout with category color encoding and zoom/pan
- OSS control panel information architecture (stats → pipeline → SWARMFISH → claims feed)

---

## 4. The Design System

### 4.1 TACTICAL Theme Token Reference

The complete token system is specified in AESTHETICS_DESIGN_BRIEF.md §6 and §10. This is the implementation-ready reference.

**Primitives (the values that change per theme):**
```css
/* Amber scale */
--amber-400: #FBBF24;
--amber-500: #F59E0B;
--amber-600: #D97706;

/* Neutral scale */
--neutral-50:  #E8E0D0;   /* warm near-white — not cold */
--neutral-400: #A3A3A3;
--neutral-600: #525252;
--neutral-700: #404040;
--neutral-800: #262626;
--neutral-850: #1A1A1A;
--neutral-900: #111111;
--neutral-950: #0A0A0A;

/* Semantic accent */
--red-500: #E53E3E;        /* critical only — nowhere else */
```

**Semantic tokens (the names that stay constant across themes):**
```css
--color-surface-ground:   var(--neutral-950); /* true background */
--color-surface-base:     var(--neutral-900); /* primary surface */
--color-surface-raised:   var(--neutral-850); /* cards, panels */
--color-surface-float:    var(--neutral-800); /* dropdowns, tooltips */

--color-accent:           var(--amber-500);
--color-accent-hover:     var(--amber-400);
--color-accent-critical:  var(--red-500);     /* alerts, errors only */

--color-text-primary:     var(--neutral-50);
--color-text-secondary:   var(--neutral-400);
--color-text-muted:       var(--neutral-600);

--color-border:           var(--neutral-800);
--color-border-subtle:    var(--neutral-850);

/* Elevation via lighter surface on dark ground */
--color-surface-elevation-1: var(--color-surface-base);
--color-surface-elevation-2: var(--color-surface-raised);
--color-surface-elevation-3: var(--color-surface-float);
```

**Typography tokens:**
```css
--font-display: 'Bebas Neue', 'Barlow Condensed', sans-serif;
--font-body:    'Inter', system-ui, sans-serif;
--font-mono:    'JetBrains Mono', 'Fira Code', monospace;

--text-xs:   11px;
--text-sm:   13px;
--text-base: 15px;
--text-lg:   20px;
--text-xl:   24px;
--text-2xl:  32px;

--weight-light:   300;
--weight-regular: 400;
--weight-medium:  500;
--weight-bold:    700;
--weight-black:   900;
```

**Motion tokens:**
```css
--duration-micro:  100ms;
--duration-fast:   200ms;
--duration-medium: 300ms;
--duration-slow:   450ms;

--ease-enter:    cubic-bezier(0, 0, 0, 1.0);
--ease-exit:     cubic-bezier(0.3, 0, 1.0, 1.0);
--ease-standard: cubic-bezier(0.2, 0, 0, 1.0);
--ease-emphasis: cubic-bezier(0.2, 0, 0, 1.2);  /* slight overshoot */
```

**Spacing tokens (8-point grid):**
```css
--space-2:  2px;   --space-4:  4px;  --space-8:  8px;
--space-12: 12px;  --space-16: 16px; --space-24: 24px;
--space-32: 32px;  --space-48: 48px; --space-64: 64px;
```

### 4.2 Entity Type Colors (for graph visualization)

Each entity type gets a distinct hue at consistent saturation. Maximum 8 types before the preattentive advantage is lost (Ware, 2004).

```css
--entity-person:        #60A5FA;   /* blue */
--entity-organization:  #34D399;   /* green */
--entity-location:      #F87171;   /* red */
--entity-event:         #FBBF24;   /* amber — matches accent */
--entity-document:      #A78BFA;   /* purple */
--entity-claim:         #94A3B8;   /* slate — for OSS claim nodes */
--entity-hypothesis:    #FB923C;   /* orange */
--entity-unknown:       #6B7280;   /* grey */
```

### 4.3 Alert Severity System

From WEBUI_DESIGN_BRIEF.md §11.3:

```css
/* Critical — requires user action */
--alert-critical-bg:   rgba(220, 38, 38, 0.15);
--alert-critical-border: var(--red-500);
--alert-critical-text: #FCA5A5;

/* Warning — calls attention */
--alert-warning-bg:    rgba(245, 158, 11, 0.12);
--alert-warning-border: var(--amber-500);
--alert-warning-text:  #FDE68A;

/* Informational — available, not demanding */
--alert-info-bg:       rgba(99, 102, 241, 0.10);
--alert-info-border:   #6366F1;
--alert-info-text:     #C7D2FE;

/* Trace — in log only, never in primary feed */
--alert-trace-text:    var(--color-text-muted);
```

---

## 5. Implementation Plan

### Step 1: Design Token Foundation
**What:** Create `patches/webui/design-tokens.css` — the single source of truth for all visual values. Deploy to `/a0/webui/design-tokens.css`.

**Why first:** Every subsequent step references these tokens. Without the foundation, each surface must be updated independently with hardcoded values, and the system never becomes coherent.

**Deliverable:** `patches/webui/design-tokens.css` containing all primitive, semantic, and component tokens for the TACTICAL theme. Deployed and imported by `patches/webui/index.html` (the Agent Zero webui root) so the variables cascade to all patched surfaces.

**Verification:** Token file compiles (valid CSS). Opening the webui shows no visual regressions on the existing Agent Zero interface. Token variables are resolvable in browser devtools.

**Does not include:** Font loading (fonts are pulled from Google Fonts or bundled separately). Theme switching mechanism (Step 1 is TACTICAL only; switcher comes later).

---

### Step 2: Fix OSS Control Panel Data Channel
**What:** Rewrite `oss_control_panel.html` to use the postMessage data channel from ARTIFACT_DATA_CHANNEL_SPEC.md. Remove direct `fetch('http://localhost:7731/...')` calls. Add `ArtifactDataClient` inline. Add `manifest.json` alongside the artifact.

**Why second:** This is the only broken-functionality issue. A data screen that shows `—` everywhere is worse than no data screen. The fix is well-specified in ARTIFACT_DATA_CHANNEL_SPEC.md §3–§5.

**Dependencies:**
- `artifact-panel.js` must have the `ArtifactDataChannel` subscription manager added (ARTIFACT_DATA_CHANNEL_SPEC.md §4)
- Agent Zero must expose OSS proxy endpoints (or the OSS service must add CORS headers for `null` origin — verify which is correct)

**The data channel flow:**
```
oss_control_panel (srcdoc)
  → postMessage data-subscribe {endpoint: '/oss_health', interval: 10000}
  → artifact-panel.js ArtifactDataChannel
  → fetch('/oss_health')   [Agent Zero proxies to OSS service]
  → postMessage data-response {data: {...}}
  → oss_control_panel updates DOM
```

**Deliverables:**
- `patches/webui/artifact-panel.js` — add `ArtifactDataChannel` class
- `patches/artifacts/oss_control_panel.html` — rewritten with data client
- `patches/artifacts/oss_control_panel/manifest.json` — artifact manifest

**Verification:** Open OSS control panel in webui. Claim count, source count, hypothesis count all show real numbers. Ingestion status shows correct running/paused state. After `oss_submit` adds a claim, the count updates within 15 seconds (10s heartbeat + 5s render budget).

---

### Step 3: Apply Tokens to All Artifacts
**What:** Update `index.html`, `network_graph.html`, and `oss_control_panel.html` to reference token variables instead of hardcoded colors. Establish TACTICAL visual register across all three.

**Specific changes per artifact:**

`index.html`:
- Remove `linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)` → `var(--color-surface-ground)`
- Remove emoji from H1 (`📦 Agent Zero Artifacts` → `Agent Zero Artifacts`)
- H1 font: `var(--font-display)` at `var(--weight-black)`, `var(--color-text-primary)` — no gradient text
- Card background: `var(--color-surface-raised)` border: `var(--color-border)`
- Card hover: `var(--color-surface-float)` border: `var(--color-accent)` with 40% opacity
- Badge: `var(--color-accent)` background at 15% opacity, text `var(--color-accent)`
- Subtitle: `var(--font-mono)` `var(--text-sm)` `var(--color-text-muted)`

`network_graph.html`:
- Graph container background: `var(--color-surface-base)` (not `#16213e`)
- Body background: `var(--color-surface-ground)`
- Tooltip background: `var(--color-surface-float)` border: `var(--color-border)`
- Node colors: use entity type tokens from §4.2 rather than ad-hoc hex values
- Labels: `var(--font-mono)` at `var(--text-xs)` `var(--color-text-secondary)`
- Remove emoji from H1 (`🌱 OpenPlanter` → `OpenPlanter`)
- Hint text: `var(--font-mono)` `var(--text-xs)` `var(--color-text-muted)`

`oss_control_panel.html` (after Step 2):
- Apply full token system to all colors
- Card values (numbers): `var(--font-mono)` `var(--weight-black)` `var(--text-2xl)`
- Card titles (labels): `var(--font-body)` `var(--weight-medium)` `var(--text-xs)` uppercase `var(--color-text-muted)`
- Status dots: use alert severity system from §4.3
- Buttons: token-referenced background colors

**Verification:** Visual review — all three artifacts look like they belong to the same system. No hardcoded hex values remain in artifact CSS (grep check). Typography hierarchy is consistent across all three (number values are monospace, labels are regular weight).

---

### Step 4: Network Graph Interaction Layer
**What:** Implement the five-phase node-click specification on `network_graph.html`.

This is the most significant single change. The D3 graph currently has nodes and edges with category-encoded colors and a hover tooltip. The interaction layer adds:

**Phase 1 — Selection state (< 100ms):**
```javascript
node.on('click', function(event, d) {
  event.stopPropagation();
  // 1. Update selection state
  svg.selectAll('.node circle')
    .attr('opacity', n => isConnectedTo(d, n) ? 1.0 : 0.2)
    .attr('stroke', n => n === d ? 'var(--color-accent)' : n.color)
    .attr('stroke-width', n => n === d ? 3 : 1.5);
  svg.selectAll('.link')
    .attr('stroke-opacity', l =>
      l.source === d || l.target === d ? 0.9 : 0.08);
  // 2. Show detail panel (Phase 3)
  showDetailPanel(d);
});

// Click canvas to deselect
svg.on('click', () => clearSelection());
```

**Phase 3 — Detail panel (non-modal, alongside canvas):**
The panel slides in from the right edge of the graph container — not a modal, not a tooltip. The canvas reflows to accommodate it (or the panel overlaps the right 30% of the canvas, which is acceptable at the artifact panel's width).

Panel content for a data source node:
```
[Node Name] (large, display font)
Category: Campaign Finance
Connections: 4

AVAILABLE EXPANSIONS
─────────────────────────────────
↗ Related Sources     (3)
↗ Shared Entities     (7)
↗ Common Datasets     (2)
```

**Phase 4 — Expansion animation:**
On expansion click, new nodes enter from the selected node's position:
```javascript
newNodes.attr('transform', d => `translate(${sourceNode.x},${sourceNode.y})`)
  .transition().duration(300).ease(d3.easeBackOut.overshoot(1.2))
  .attr('transform', d => `translate(${d.x},${d.y})`);
```

**Phase 5 — Breadcrumb trail:**
A small bar at the top of the graph: `All nodes → Campaign Finance → FEC → Related Sources`
Each breadcrumb is a clickable jump point back to that state.

**Non-destructive filter:** Add a category filter panel (checkboxes for each entity type). Filtered categories set nodes to 15% opacity — not removed. `filteredNodes.attr('opacity', 0.15)`.

**Deliverables:**
- `patches/artifacts/network_graph.html` — full interaction layer added
- Interaction is D3-native (no framework dependencies added)

**Verification:**
- Click a node → connected edges highlight, unconnected nodes dim, detail panel appears
- Click expansion → new nodes animate in from source
- Click canvas → selection clears, full opacity restored
- Filter checkbox → nodes dim without disappearing
- Breadcrumb trail shows current exploration path

---

### Step 5: OSS and SWARMFISH Service Visual Alignment
**What:** Apply TACTICAL palette and typography to `services/oss/src/static/style.css` and `services/swarmfish/src/static/style.css`. Do not change Alpine.js architecture, component structure, or information layout — these are correct and should be preserved.

**Scope:** Color values, font references, spacing values. Not layout, not component structure, not JavaScript logic.

**What changes:**
- Background colors → token values (import design-tokens.css, or duplicate primitive values since these are standalone services not served through Agent Zero's webui)
- Font families → Inter for body, JetBrains Mono for data values
- Button colors → token-referenced or matched to TACTICAL palette
- Data values in stat cards → monospace, bold weight
- Status indicators → use alert severity system colors

**What does NOT change:**
- Alpine.js `x-data`, `x-model`, `x-for` directives
- Tab structure, navigation, view switching logic
- API endpoints and data fetching logic
- Information hierarchy (section order, content grouping)

**Note on font loading:** The OSS and SWARMFISH services are served standalone (not through Agent Zero). They need their own font imports in the HTML head. Inter and JetBrains Mono are available on Google Fonts:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

**Verification:** Visual review of OSS service and SWARMFISH UI. Both look like they belong to the same family as the artifacts. Data values (counts, timestamps, percentages) are in JetBrains Mono. No functional regressions.

---

## 6. What This Does NOT Cover

- **Theme switching UI** — the token architecture supports themes, but the switcher control (a dropdown or toggle in the Agent Zero sidebar) is not in this spec. TACTICAL ships as the only theme in Phase 1. Theme selection is a future enhancement.
- **Situation Awareness Levels 2 and 3** — the current stack makes Level 1 visible (Stack Status tool) but doesn't surface Level 2 (current task state, plan progress) or Level 3 (trajectory projection) in the webui. This is the next major design work after the visual system is coherent.
- **Live network graph from OSS/ontology data** — the current `network_graph.html` shows static OpenPlanter data. The live version — pulling entities and relationships from the ontology layer via the data channel — is a separate spec (it requires both the data channel implementation and the ontology layer's graph query API).
- **Coordinated views (graph + timeline + table)** — specified in INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md but not implemented in this phase. This is the next evolution of the information environment after the single-graph interaction layer is working.
- **Test suite** — the Playwright-based test suite from ARTIFACT_DATA_CHANNEL_SPEC.md §7 is specified but not built in this phase. Build it once the data channel is working.

---

## 7. Implementation Notes for Kestrel

When implementing, follow the standard deployment protocol:
1. Edit file in repo
2. `docker cp` to container
3. Clear `__pycache__` if Python files changed; CSS/JS changes take effect on reload
4. Verify in browser before committing

For the design token CSS, it must be imported in `patches/webui/index.html` (the webui root) before Agent Zero's own stylesheets, so the custom properties are defined before they're used.

For `artifact-panel.js`, the `ArtifactDataChannel` class is an addition, not a replacement. The existing panel logic (multi-tab, resize, zoom injection) remains unchanged. The data channel is a new capability bolted alongside the existing system.

For the D3 graph, the existing force simulation, node rendering, and zoom/pan are preserved. The interaction layer (click handlers, detail panel, breadcrumbs) is additive. Do not rewrite the graph from scratch — the existing implementation is solid.

The ARTIFACT_DATA_CHANNEL_SPEC.md has implementation-ready JavaScript for both the panel-side `ArtifactDataChannel` class and the artifact-side `ArtifactDataClient` class. Use these verbatim as starting points.

---

## 8. Success Criteria

The redesign is complete when:

1. All five surfaces use the same color token system — no hardcoded hex values in artifact CSS except in `design-tokens.css`
2. OSS control panel shows live data from the OSS service without errors
3. Network graph node click highlights neighbors, dims non-neighbors, shows detail panel
4. All data values (numbers, timestamps, codes) are in JetBrains Mono
5. No emoji in any heading or UI label
6. OSS and SWARMFISH service UIs are visually recognizable as part of the same system as the artifacts
7. Visual review: all surfaces read as "serious operational tool" not "weekend project"

---

*Companion documents: `WEBUI_DESIGN_BRIEF.md`, `AESTHETICS_DESIGN_BRIEF.md`, `INFORMATION_ENVIRONMENTS_DESIGN_BRIEF.md`, `ARTIFACT_DATA_CHANNEL_SPEC.md`.*
*Raw research archives: `D:\tmp\ux_research.md` (63KB), `D:\tmp\aesthetics_research.md` (85KB), `D:\tmp\information_viz_research.md` (111KB).*
