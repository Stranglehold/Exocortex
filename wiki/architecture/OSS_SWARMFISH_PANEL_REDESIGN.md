# OSS + SWARMFISH Panel Redesign
## Architecture Analysis · UX Review · Proposed Changes

**Date:** 2026-05-05  
**Author:** Kestrel  
**Context:** Full wiring audit of the existing OSS/SWARMFISH interfaces, analyst output quality review from the April 2026 run, and a redesign proposal using the v1.13 right-canvas panel system documented in `V113_UI_PANEL_SYSTEM_WIRING.md` and `V113_BROWSER_MONITOR_WIRING.md`.

---

## Part 1 — Analyst Output Quality Review

*Last ingestion: 2026-04-15. Today: 2026-05-05. Three weeks of missed coverage assessed below.*

### Current Ledger State

| Metric | Value |
|--------|-------|
| Total claims | 12,228 |
| Promoted | 3,721 (30%) |
| Staged (unreviewed) | 8,428 (69%) |
| Irrelevant | ~79 |
| Sources | 23 (0 active, 19 stale, 4 dormant) |
| Ingestion | PAUSED since 2026-04-15 |
| Hypotheses | 12 (all ACTIVE, 0 falsified, 0 outcomes recorded) |

### Signal Quality: What the Pipeline Was Capturing

The April 14-15 claims from the feed are substantive and on-target. Sample promoted claims from that final ingestion run:

**From `NYT` — "Iran War Live Updates" (2026-04-14T01:16Z):**
- *"A new pattern of deceptive activity by some vessels around the critical waterway suggests the new American blockade is changing how some ships linked to Iran are behaving."* → technique: `fracture`, tag: `iran-hormuz`
- *"Diplomatic meetings between Israel and Lebanon in Washington are taking place to advance peace talks"* → technique: `presuasion`, tag: `iran`
- *"Israel continued to refuse to halt its military campaign against Iran-backed Hezbollah in Lebanon."* → technique: `fracture`, tag: `iran`
- *"The conflict in southern Lebanon is a direct result of Iran's support for Hezbollah"* → technique: `fracture`, tag: `iran`

**From `NYT` — "Ship Spoofing in Strait of Hormuz May Compound Confusion" (2026-04-14):**
- *"A new pattern of deceptive activity by some vessels around the critical waterway suggests the new American blockade is changing how some ships linked to Iran are behaving."*

**From `NYT` — "Rubio Hosts Israel and Lebanon for Rare Meeting Shadowed by U.S.-Iran War":**
- Multiple claims establishing the geopolitical frame: active US-Iran war, Israel-Lebanon diplomacy under fire.

**Assessment:** The pipeline was finding exactly the right signal. The topic descriptions prove it — the iran-hormuz topic description included "Lloyd's Joint War Committee Listed Areas changes affecting Persian Gulf shipping" and "shipping insurance war-risk premium changes for Gulf transit" — those are precise, high-value intelligence dimensions. The claims captured directly address: the American naval blockade, ship AIS spoofing in response, Israel-Lebanon diplomacy in the shadow of the larger conflict, and IRGC/Hezbollah operations.

**Technique classification** is working. `fracture` correctly flags claims about Israel's military operation and Iran-Hezbollah attribution — these are contested frames in the media ecosystem. `presuasion` correctly flags the peace-talks framing. The classifier is not producing noise.

### What 3 Weeks of Missed Coverage Means

The topic descriptions themselves tell the story. Iran's Supreme Leader Ali Khamenei died in February 2026. Mojtaba Khamenei was in succession. The April 14-15 claims show a US-Iran war was active, with a naval blockade at Hormuz. The source list includes "Department of War" (a renamed DoD) — that URL was added specifically for official US government statements during an active conflict.

Three weeks of missed coverage on an active war is significant. The staging queue is 8,428 unreviewed claims. If OSS was running during this period: the ship spoofing trajectory, the progression of the blockade, the Lebanon ceasefire negotiations — all of that would be in the ledger. Instead, the last snapshot is April 15 and the situation has evolved substantially. This is an argument for resuming ingestion, not just reviewing the backlog.

### SWARMFISH Hypothesis Quality: Bug Diagnosis

The 12 hypotheses in the ledger reveal a critical bug. The most recent auto-generated ones are labeled:
- "Private Credit — Apr 2026" (ACTIVE, id=12, created 2026-04-13)
- "Test Verify — Apr 2026" (SUSPENDED, id=11, created 2026-04-13)
- "Test Topic — Apr 2026" (ACTIVE, id=10, created 2026-04-13)

These are NOT Iran/Hormuz topics. The SWARMFISH autonomous monitor (`monitor.py`) was generating questions from topics that don't exist in OSS. The prediction briefs show SWARMFISH correctly identifying the problem: every profile said "no relevant data" because the intelligence feed (Iran claims) doesn't match the question topic (Private Credit).

**Root cause hypothesis:** The SWARMFISH monitor's `oss_bridge.py` is fetching claims using `limit=50` but using a topic name generated from somewhere other than the OSS topics endpoint. The monitor probably has a hardcoded test topic list or is deriving topic names from SWARMFISH profile domain labels ("geopolitical_risk", "commodities", "market_structure") instead of OSS topic tags ("iran", "iran-hormuz").

**Consequence:** No meaningful SWARMFISH predictions have been generated for the actual monitored topics. All `predictions_confirmed: 0`, all calibration "insufficient history." The feedback loop (which is the entire point of the calibration architecture) has never exercised a real prediction.

**Verdict:** The OSS pipeline is working well and finding real signal. SWARMFISH has never run correctly on OSS topics. This is a configuration bug, not a fundamental architecture problem.

---

## Part 2 — Wiring Check: Current Interface Architecture

### Three-Surface Problem

The current state has three separate UIs with no coordination:

```
┌─────────────────────────────────────────┐
│  localhost:7731 — OSS Dashboard         │  ← Standalone Flask/Alpine
│  1,248 lines HTML/CSS/JS                │    Full-featured, proper tabs
│  Claims, Staging, Topics, Sources,      │    Not integrated with A0
│  Contradictions, Silences, Activations, │    Separate browser window
│  Hypotheses                             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  localhost:7732 — SWARMFISH Dashboard   │  ← Standalone Flask/Alpine
│  542 lines HTML/CSS/JS                  │    Predict, Sessions, Profiles
│  SSE streaming for prediction progress  │    Not integrated with A0
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Agent Zero WebUI — Intel Panel         │  ← initFw_start sidebar
│  732 lines JS (custom CSS + HTML)       │    Read-only review
│  Claims (staged only), Hypotheses,      │    No SWARMFISH prediction
│  Sources, Topics, SWARMFISH profiles    │    No drift/silence analysis
│  Ingest pause/resume                    │    No bulk actions
│  Width: 28px strip → 520px expanded    │    Manual refresh only
└─────────────────────────────────────────┘
```

### Intel Panel: What It Does and Doesn't Do

**What it does:**
- Injects a sidebar panel via `initFw_start` hook
- 5 tabs: Claims (staged queue), Hypotheses, Sources, Topics, SWARMFISH
- One-at-a-time promote/dismiss for staged claims
- Ingest pause/resume
- Manual refresh per tab

**What it doesn't do:**
- No SWARMFISH prediction execution (tab only shows profile calibration status)
- No narrative drift / silence / activation analysis
- No contradiction view
- No hypothesis management (promote/falsify — view only)
- No ingestion sprint control
- No bulk claim operations
- No real-time updates (everything is manual refresh)
- No source credibility editing
- No topic management

**Architecture problems with the current approach:**

1. **Space competition**: The Intel Panel inserts before `#artifact-panel`, creating a three-column layout: Intel Panel | Chat | Artifact Panel. This compresses the chat column. The browser panel (v1.13) now occupies right-canvas and also competes for this space.

2. **Outside the v1.13 surface system**: The Intel Panel uses its own `initFw_start` injection pattern, not the right-canvas surface registration system. It doesn't participate in `rightCanvasStore` — it can't be toggled from surface buttons in the toolbar.

3. **Read-only for the most important actions**: Hypothesis management (the core Chamberlin workflow) is view-only. You can see hypotheses but can't falsify, promote, or link predictions.

4. **No streaming**: The v1.13 browser panel proves that real-time streaming over Socket.io is possible. The Intel Panel polls on demand only.

### Wiring Check: Key Findings

| Finding | Severity | Details |
|---------|----------|---------|
| SWARMFISH topic routing bug | High | Monitor generates predictions for non-OSS topics ("Private Credit", "Test Topic"). Zero meaningful predictions generated. |
| Staging flood | High | 8,428 unreviewed claims. No bulk review tooling. One-at-a-time dismiss is insufficient for backlog management. |
| Zero outcome recording | High | All SWARMFISH predictions have 0 confirmed outcomes. Calibration loop has never fired. Brier scores uncalibrated. |
| Intel Panel space competition | Medium | Three-column layout compresses chat. Intel Panel is outside v1.13 surface system. |
| No drift/silence/activation in panel | Medium | The three most analytically interesting OSS endpoints aren't exposed in the panel. |
| 19 stale sources | Medium | All stale since April 15. Ingestion paused. 3 weeks of active conflict missed. |
| Hypothesis management read-only | Medium | Panel shows hypotheses but can't falsify, promote, or manage them. |
| No SWARMFISH predict from panel | Medium | Have to open a separate browser window to run a prediction. |
| Source credibility scores are static | Low | `confidence_score` is manually set, not computed from accuracy history. |
| Department of War URL may be broken | Low | URL format `war.gov/...` — worth verifying this feeds correctly. |

---

## Part 3 — UX/UI Research Applied

### From the Reference Library

The current UI references in `docs/ui_references/` provide specific applicable patterns:

**OpenGridWorks `--ds-*` tokens** (in `exocortex.css`):
- Glass effects: `backdrop-filter: blur(20px)` (adapted from 32px)
- Transition: `cubic-bezier(0.22, 1, 0.36, 1)` — same spring easing used in Intel Panel
- The 73 `--ds-*` tokens give us a complete design vocabulary

**Contentsquare behavioral principles applied:**
- *Above-fold concentration*: The most critical controls (operator state alert, claim count, ingestion toggle, sprint button) belong at the top of the panel, not in a tab. Currently the ingest bar is at the bottom and only shows on Claims/Topics tabs.
- *Rage-click equivalent*: Analysts trying to triage 8,428 staged claims one-at-a-time by clicking Promote/Dismiss is the exact pattern that creates frustrated repeat-clicking. Bulk triage operations are needed.
- *Feature discovery*: Drift analysis, silence detection, activation patterns — these are key OSS capabilities that no analyst would discover from the current panel. They need a dedicated analysis tab with clear affordances.
- *Immediate clarity*: The panel header says "Intelligence" — it should say what's happening right now: "41 staged · NOMINAL · Ingest PAUSED".

**RealtimeLogic embedded principles applied:**
- *Auto-submit on change*: Source credibility sliders should save on release, not require a separate Save button.
- *State persistence*: After promote/dismiss, the claim should disappear in-place (already implemented correctly in Intel Panel).
- *Targeted updates*: Health status bar should poll `/api/health` every 30s independently from tab content — not require a tab refresh to update the status dot.

**Major Zero mission control aesthetic** (the stated design direction):
- Dark monospace, green/amber/red semantics
- Radar-style operator state indicator
- Compact information density (Bloomberg model, not consumer app)
- The OSS standalone CSS is already close to this. The Intel Panel CSS is functional but not thematic.

---

## Part 4 — Proposed Redesign

### Core Decision: v1.13 Right-Canvas Surface

**Replace the Intel Panel sidebar with a proper v1.13 right-canvas surface.**

Rationale:
1. The right-canvas is the correct location for persistent analyst tooling in v1.13. It doesn't compete with the chat column.
2. The surface system provides proper lifecycle management (subscribe/unsubscribe, surface tokens, `rightCanvasStore` coordination).
3. The browser panel wiring shows the exact pattern to follow — we have the full reference document.
4. The sidebar approach was built before v1.13. The surface approach is the architectural successor.

The standalone OSS and SWARMFISH web UIs (`localhost:7731`, `localhost:7732`) are retained as administrative interfaces. The right-canvas surface is the analyst's primary working view.

### New Surface Architecture

```
Plugin ID: exocortex-intel (or oss-intel)
Surface ID: intel
Surface type: right-canvas

File layout:
/a0/usr/plugins/exocortex/
├── webui/
│   ├── intel-surface.html          ← Surface HTML + Alpine component
│   └── intel-surface.css           ← Scoped styles (pulls exocortex.css tokens)
└── __init__.py                     ← Registers surface via initFw_start (replaces intel-panel-init.js)
```

**Initialization pattern** (from V113_UI_PANEL_SYSTEM_WIRING.md):
```javascript
// In initFw_start hook — replaces current intel-panel-init.js approach
document.addEventListener("alpine:init", () => {
    Alpine.data("intelStore", intelStoreFactory);
});

// Register the surface button in the toolbar
rightCanvasStore.registerSurface({
    id: "intel",
    icon: "radar",
    label: "INTEL",
    badgeSource: () => intelStore.stagedCount,  // live badge
    onOpen: () => { /* init WebSocket or start polling */ },
});
```

### Tab Structure: Redesigned

Current 5 tabs → New 6 tabs with clearer scope:

| Tab | Current Panel | Redesigned |
|-----|--------------|-----------|
| **Status** | ❌ Missing | NEW: Operator state · Claim velocity · Source health · Ingestion controls · Sprint |
| **Triage** | Claims (staged only) | Redesigned: Staged queue with bulk operations |
| **Ledger** | ❌ Missing | NEW: Promoted claims feed · Topic filter · Technique filter |
| **Analysis** | ❌ Missing | NEW: Drift · Silence · Activation · Contradictions |
| **Hypotheses** | View only | Full management: falsify · promote · link predictions |
| **Predict** | SWARMFISH profiles (static) | Full predict execution with SSE stream |

### Status Tab (NEW — Always First)

This is the most important addition. Current state: analysts have to click into Claims tab and check the bottom bar to see ingest status. Proposed: the Status tab is the landing view, contains everything above-fold.

```
┌──────────────────────────────────────────┐
│ ● NOMINAL                        [Sprint]│  ← Operator state pill + sprint button
│ Ingest: PAUSED  [Resume]    Apr 15 last  │  ← Ingest status with action + timestamp
├──────────────────────────────────────────┤
│ Claims   12,228   Staged   8,428         │  ← Key numbers grid
│ Promoted  3,721   Sources    23          │
├──────────────────────────────────────────┤
│ SOURCES                    19 stale      │  ← Source health summary
│ NYT           99%    1,107 claims  stale │
│ The Guardian  99%    1,884 claims  stale │
│ Al Jazeera    99%    1,242 claims  stale │
│ [+ 20 more]                              │
├──────────────────────────────────────────┤
│ TOPICS                                   │
│ ● iran           1,576 claims            │
│ ● iran-hormuz    1,285 claims            │
└──────────────────────────────────────────┘
```

Key behaviors:
- Operator state pill uses `--ds-status-red/yellow/green` tokens
- Sprint button calls `oss_ingest_sprint` — labeled with estimated duration
- Status bar polls `/api/health` every 30s (independent of tab content)
- "19 stale" badge on source count is immediately visible without tab switching

### Triage Tab (Bulk Operations)

The staged queue has 8,428 claims. One-at-a-time review isn't viable for backlog management.

**Proposed additions:**

1. **Bulk threshold promote**: All staged claims with `staging_confidence >= X%` → promote. Slider sets threshold. Shows count ("Promote 2,341 above 75% confidence?"). Confirms before executing.

2. **Bulk technique dismiss**: All staged claims with `technique_class = 'none'` and `staging_confidence < 40%` → mark irrelevant. Low-confidence, unclassified claims are likely noise extractions.

3. **Topic batch view**: Claims grouped by topic tag. Collapse/expand per topic. Topic-level promote-all button.

4. **Technique filter**: Radio buttons — All / fracture / presuasion / emergent / direct / none. Quickly review by technique class.

The existing per-claim card UI (promote/dismiss buttons) is kept — it's correct for careful review of individual high-value claims.

### Analysis Tab (NEW)

Surfaces the three OSS capabilities that currently require hitting `localhost:7731` directly:

**Drift panel:**
```
Narrative Drift — iran-hormuz
Status: [Check] [Stable]
Window: [24h ▾]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
blockade_framing: delta=+0.23 ↑
ceasefire_framing: delta=-0.11 ↓
```

**Silence panel:** List of flagged narratives with cluster presence/absence. Which clusters are covering what the others aren't.

**Activation panel:** Claim patterns across clusters. Useful for detecting coordinated messaging.

**Contradictions panel:** Side-by-side claim pairs with confidence score. Currently only viewable in the standalone dashboard.

All panels lazy-load on tab select. Topic filter applies across all analysis views.

### Hypotheses Tab (Full Management)

Current Intel Panel: display only. Proposed: full Chamberlin workflow.

```
┌──────────────────────────────────────────┐
│ ◉ ACTIVE  conf=67%                       │
│   US blockade will cause Iran to resume  │
│   secret enrichment outside IAEA view    │
│                                          │
│   Predictions: 3✓ / 0✗ / 5 total        │
│                                          │
│   [Falsify ▾]  [Promote]  [Run SWARMFISH]│
└──────────────────────────────────────────┘
```

**"Run SWARMFISH" button**: Deep-links directly to the Predict tab with the hypothesis text pre-filled as the question. This closes the gap between hypothesis tracking and SWARMFISH analysis — currently they're in separate browser windows with no connection.

**Falsify workflow**: Click "Falsify ▾" → dropdown shows "Enter falsification evidence" → text input → calls `oss_hypotheses` falsify → updates SWARMFISH via outcome endpoint.

### Predict Tab (Full SWARMFISH Execution)

Replace the current static calibration view with the full prediction workflow.

```
┌──────────────────────────────────────────┐
│ Question ──────────────────────────────  │
│ Will Iran resume enrichment outside      │
│ IAEA visibility within 60 days?          │
│                                          │
│ Domain: [Geopolitical Risk ▾]            │
│                                          │
│ [Run Profiles]                           │
├──────────────────────────────────────────┤
│ Streaming (SSE) — profile cards appear   │
│ as each profile completes:               │
│                                          │
│ ✓ Base Rate Analyst    42%               │
│ ◉ Historian            (running…)        │
│ ○ Contrarian           (waiting)         │
│   ...                                    │
├──────────────────────────────────────────┤
│ CONSENSUS: 38%  Meta: MEDIUM  Range: 22-54│
│ [Operator Brief ▾]                       │
│ [Post as Hypothesis]  [Record Outcome]   │
└──────────────────────────────────────────┘
```

**Key**: The SSE streaming (`/acp/predict/stream`) means profile cards appear in real-time as each profile completes. This is the same principle as the browser screencast — don't wait for all results, stream them as they arrive.

**"Post as Hypothesis"**: Takes the consensus brief and posts it to OSS as a new hypothesis via `oss_hypotheses register`. Closes the SWARMFISH → OSS loop.

**"Record Outcome"**: After a prediction session, links an outcome. Triggers calibration update.

The **Profiles sub-tab** (currently the whole SWARMFISH view) moves here as a secondary tab within Predict.

### Styling Direction

Apply the exocortex.css token set with the Major Zero thematic:

```css
/* Intel surface — tokens from exocortex.css / OpenGridWorks base */
.intel-surface {
    --intel-bg: var(--ds-background-neutral-subtle);
    --intel-border: var(--ds-border-neutral);
    --intel-text: var(--ds-text-default);
    --intel-accent: #4a9eff;         /* SWARMFISH blue */
    --intel-nominal: #4caf93;        /* NOMINAL green */
    --intel-degraded: #f0b429;       /* DEGRADED amber */
    --intel-compromised: #e05c5c;    /* COMPROMISED red */
    --intel-muted: var(--ds-text-subtle);
    
    font-family: 'IBM Plex Mono', 'JetBrains Mono', monospace;  /* Major Zero */
    font-size: 11px;
}

/* Operator state — the single most important status indicator */
.intel-operator-state {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    border-bottom: 1px solid var(--intel-border);
    background: rgba(0,0,0,0.2);
}
.intel-state-nominal  { color: var(--intel-nominal); }
.intel-state-degraded { color: var(--intel-degraded); }
.intel-state-compromised { color: var(--intel-compromised); }
```

The monospace font is the load-bearing aesthetic choice — it reads as a terminal/mission control surface, not a dashboard widget. IBM Plex Mono or JetBrains Mono.

---

## Part 5 — Implementation Priority

Ordered by impact vs. effort:

### Priority 1: SWARMFISH Topic Routing Bug Fix (High Impact, Low Effort)

**Before any UI work**, fix the monitor so SWARMFISH runs on actual OSS topics.

In `services/swarmfish/src/monitor.py` — find where the question topic is determined and confirm it uses OSS topic tags (`iran`, `iran-hormuz`) not SWARMFISH domain labels. The `oss_bridge.py` `get_context()` method should be fetching `GET /api/topics` and using those tag names.

This is the unlock for the calibration loop. Without it, SWARMFISH is running but not doing anything useful.

### Priority 2: Status Tab + Ingest Controls (High Impact, Medium Effort)

Build the Status tab first — it's the landing view and the most immediately useful. The "Sprint" button (start a bounded ingestion run) and ingestion status are the controls analysts reach for first after a gap in coverage.

The current Intel Panel ingest controls (pause/resume) work but are buried at the bottom of the Claims tab.

### Priority 3: Bulk Triage Operations (High Impact, Medium Effort)

8,428 unreviewed claims. Without bulk triage, the staging queue is effectively a debt that grows faster than it can be paid down. The bulk threshold promote is one API call: iterate claims above threshold and call `/admin/quick_promote` per claim (or add a bulk endpoint to OSS app.py).

### Priority 4: Full v1.13 Surface Migration (Medium Impact, High Effort)

Replace `intel-panel-init.js` with a proper `initFw_start` surface registration that plugs into `rightCanvasStore`. This is primarily an architectural improvement — functionality is similar but the integration is cleaner and doesn't fight for horizontal space.

Can be done incrementally: the surface HTML can be a direct port of the current Intel Panel HTML with the new tab structure, then features are added tab by tab.

### Priority 5: Analysis Tab + SWARMFISH Predict (High Impact, High Effort)

The drift/silence/activation analysis views and full prediction execution are the highest-value additions, but also the most complex to implement cleanly in a panel context. The SSE streaming for SWARMFISH predict requires handling the stream in an Alpine.js component without blocking the panel.

### Priority 6: Hypothesis Management + SWARMFISH Outcome Loop (Medium Impact, Medium Effort)

The Chamberlin workflow (hypothesis → predictions → outcome → calibration) is architecturally complete in the backend. What's missing is the panel UI that connects all the steps. The "Run SWARMFISH" → "Post as Hypothesis" → "Record Outcome" chain can be wired once the SWARMFISH predict tab exists.

---

## Appendix: Files to Change

| File | Change |
|------|--------|
| `services/swarmfish/src/monitor.py` | Fix topic routing — use OSS topic tags, not SWARMFISH domain labels |
| `services/swarmfish/src/oss_bridge.py` | Verify `get_context()` uses `/api/topics` tag names |
| `services/oss_plugin/webui/intel-panel-init.js` | Migrate to v1.13 surface registration (Phase 4) |
| `services/oss_plugin/webui/intel-surface.html` | NEW — right-canvas surface HTML with 6-tab layout |
| `services/oss_plugin/webui/intel-surface.css` | NEW — scoped styles using exocortex.css tokens |
| `services/oss/src/app.py` | Add `/admin/bulk_promote` endpoint for threshold-based batch promotion |
| `docs/ui_references/ROADMAP.md` | Note: TuiCss reference (MS-DOS aesthetic) would directly serve the Major Zero monospace direction |

---

*Written 2026-05-05. References: `V113_UI_PANEL_SYSTEM_WIRING.md`, `V113_BROWSER_MONITOR_WIRING.md`, live OSS API queries, `intel-panel-init.js` (732 lines), OSS dashboard `index.html` (1,248 lines), SWARMFISH dashboard `index.html` (542 lines), `exocortex.css`, `docs/ui_references/ROADMAP.md`.*
