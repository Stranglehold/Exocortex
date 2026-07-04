# Exocortex Panel Design Lab — Changelog

Diegetic game-UI mockups. Self-contained HTML, opened locally (artifact tool is org-blocked).
The HTML pages are the **design lab**: nail the spirit per material → extract principles → port
to the real A0 right-canvas panels (`patches/webui/right-canvas-panels/`, native Alpine/vanilla — NOT React).

**Checkpoint convention:** every milestone freezes all three panels into `vN/`. Top-level
`*_panel.html` is always the LATEST. Earlier drafts are never deleted, so we can pull an element
from any prior version. `D:\tmp\exocortex_*_panel.html` mirrors the latest for quick opening.

---

## CANVAS PORT — 2026-06-21 — EXO·OPS live right-canvas panel (DEPLOYED to v16+v17)
First mockup → real A0 right-canvas. Files in `panels/canvas/`; deployed via plugin webui dirs.

- **`exo-ops-panel.html`** — diegetic ops console as a real right-canvas surface (canvas contract: scoped `.xops`
  fragment, `data-surface-id="exo-ops"`, `setTimeout` init, IntersectionObserver polling). Renders the **REAL** idle
  cycle feed from **`GET /api/office_feed`** (live: cycle number/type, activity, steps, pages/skills/mem/field-report/
  integrity counts) in the iDroid aesthetic with expandable per-cycle **report dossiers** built from the real fields.
  **REAL controls** via **`POST /api/idle_control`**: ENABLE/DISABLE engine, PAUSE (duration select) / RESUME.
  Live status badge, cycle counter, real aggregates. Polls every 20s only while visible. Self-contained palette (theme-agnostic).
- **`register-exo-ops.js`** — surface registrar (id `exo-ops`, title "EXO·OPS", icon `radar`, order 36 — right after Office).
- **Deploy:** docker cp → `/a0/usr/plugins/exocortex/extensions/webui/{right-canvas-panels,right_canvas_register_surfaces}/`
  on **v16 + v17** (md5 parity verified). Added to `scripts/install_idle_engine.sh` so the install pipeline bakes it.
  No A0 restart needed — hard-reload the web UI to load the new surface.
- **Note:** office_feed has no GPU telemetry (VRAM/temp/decode) — those need a host-side metrics bridge (container can't
  see the GPU). EXO·OPS shows only REAL fields (no fabricated numbers). GPU telemetry on canvas = a follow-up endpoint.

---

## v6 — 2026-06-21 — Real-world map geography + hover-to-interact everywhere
Frozen in `v6/`. The "command / video-game feel" pass: hover any entity → an interactive card.

**Map — real geography:**
- Replaced the stylized blobs with **data-driven real coastlines** (lon/lat vertex arrays, equirectangular w/ cos-latitude
  correction): Iran, Qeshm Island, Musandam Peninsula/Oman (the chokepoint), UAE, + islands (Hormuz, Larak, Hengam, Quoin,
  Greater Tunb, Abu Musa), real TSS shipping lanes, and place labels (BANDAR ABBAS, STRAIT OF HORMUZ, PERSIAN GULF, GULF OF OMAN).
  A recognizable Strait of Hormuz. Geometry stays KML-true (lon/lat) so the EXPORT KML / TAK path is unaffected.

**Hover-to-interact popover — spread across the whole UI:**
- **Map** — hover a contact → card with description, coords, source, confidence + **actions** (▸ CASE FILE, ⊕ PIN [drops a pin ring on the map], ⤓ KML). Move into the card and click.
- **SWARMFISH** — hover a scope contact → **agent dossier** (callsign, role, P, reasoning, Δ-consensus, confidence) + ▸ FOCUS IN ROSTER (opens+scrolls the roster card).
- **System** — hover a gauge → live detail (current / peak / range, e.g. VRAM headroom + WDDM-cliff note, temp throttle, decode vs baseline) + ▸ CYCLE HISTORY (jumps to Cycles tab).
- **Office** — hover a cycle → peek (objective + outcome chips) + ▸ OPEN DOSSIER (expands the full report). Click still opens directly.
- **Intel** — hover a claim → peek (snippet + sources/conf/volatility) + ▸ OPEN CASE FILE.
- All popovers: spring fade-in, cursor-anchored + viewport-clamped, and **keep-alive while hovering the card** so its action buttons are clickable.

---

## v5 — 2026-06-21 — Console hub, global theme, customization suite, Map (KML/TAK)
Frozen in `v5/` (6 files). The set becomes a cohesive console.

**NEW — `console.html` (the hub):**
- **At-a-glance overview** — a live mini-card per screen (System/Office/Intel/SWARMFISH/Map), each with real-ish
  live data + an **OPEN FULL ▶** link to its standalone page. This is the canvas-glance → full-page model:
  rich interaction in the small card, the full screen one click away.
- **Global theme selector** — 4 canonical themes as SHARED tokens (amber/holo/parchment/tactical = MAGI/iDroid/YoRHa/HighFleet).
  The whole console re-skins; choice persists to `localStorage['exo-theme']`.
- **Customization suite** (slide-in drawer) — background **image upload** (data URL → `localStorage['exo-bg']`),
  **opacity slider** (`exo-bg-op`), theme picker. Applied live, persisted.

**NEW — `map_panel.html` (5th panel, geospatial):**
- Stylized **Strait of Hormuz** theatre (ties to the Intel/OSS iran-hormuz claims) — landmasses, lat/lon graticule, TSS shipping lanes, sweep.
- **KML-shaped data model** — every event is a `<Placemark>` (lon/lat + styleUrl category). `toKML()` emits standard **KML 2.2**;
  **EXPORT KML** button downloads a file that loads directly into **ATAK / WINTAK**, Google Earth, or a TAK server. On port, the same
  schema is fed FROM a TAK server / OSS geo-claims instead of the sim.
- Placemarks colored by category, pulse, drop-in on live arrival; cursor lat/lon readout; **drill-down case files**;
  tabs: Tactical Map / Event Feed / KML Layers (toggle styleUrl categories on/off).

**Cross-panel inheritance:** all 5 standalone panels got a small loader that reads the saved theme + background from
localStorage on open and applies them (theme mapped to each panel's nearest local material). Open the console, set a vibe + background,
then OPEN FULL — the screen carries your customization. (Cross-file localStorage sharing is reliable once served from a real origin;
on `file://` it depends on the browser. Within the console it's always live.)

---

## v4 — 2026-06-21 — SWARMFISH tactical panel (4th material: HighFleet)
Frozen in `v4/` (now 4 panels). New panel `swarmfish_panel.html` joins the set.

**SWARMFISH (HighFleet ⇄ Amber-Tac):** military radar/tactical console, phosphor-green CRT, industrial framing.
Proves structure-is-component across a 4th, very different aesthetic. Same shell/header/sec/statusbar/tabs/switch DNA.
- **Hero — tactical SCOPE:** the 8-agent forecasting committee plotted as contacts; radius = P(event) (center 0 → outer ring 1.0),
  even bearings, consensus as a dashed ring that moves as the mean shifts, a rotating sweep, **dissenters pulse strike-red**.
- **Committee tab:** scope + consensus/dispersion/agreement readout + active-hypothesis bar + **roster drill-downs**
  (each agent CALLSIGN·role·P·dissent-flag expands to reasoning + estimate sparkline + Δ-consensus).
- **Forecasts tab:** open + resolved forecasts, each drills to resolution detail (consensus, outcome, Brier).
- **Calibration tab:** reliability diagram (predicted vs observed, 5 buckets) + Brier-history sparkline.
- **Live:** committee re-scores every ~5.5s — contacts move (smooth transition), consensus + dispersion + agreement recompute, scoring-round counter ticks.

The set is now FOUR materials: opaque-amber (System/MAGI), translucent-glass (Office/iDroid), light-paper (Intel/YoRHa), tactical-CRT (SWARMFISH/HighFleet).

---

## v3 — 2026-06-21 — Cycle/claim DRILL-DOWN (investigate individual reports)
Frozen in `v3/`. Latest = top-level. Goal: feel like opening a mission dossier in a game.

**Shared pattern:** accordion drill-down — click a row, it expands (spring easing, rotating chevron,
staggered child reveal) into a full report. Each panel applies it through its own lens.

**System (MAGI ⇄ MGS·Delta):**
- New **Cycles** tab; the Telemetry CYCLES tile is now clickable (▶ INVESTIGATE) and jumps to it.
- Each cycle expands to a **PERFORMANCE report**: decode-throughput sparkline + duration, tokens,
  decode avg, prefill, draft-accept, VRAM peak, power avg/peak. Completed live cycles push a real record to the top.

**Office (iDroid ⇄ Amber-Ops):**
- Every cycle row expands to a **DOSSIER**: objective, timestamped operations log (per cycle type:
  BUILD/EXPLORE/MAINTAIN have distinct generated logs), outcome chips, journal excerpt.
- Right panel decoupled — now ALWAYS tracks the live RUN cycle; left list is the browsable archive.

**Intel (YoRHa ⇄ Archive):**
- Every codex entry expands to an **EVIDENCE CASE FILE**: source list (bibliography style), corroboration
  timeline (vertical, alert-marked events), related claims (clickable — jump+open the related entry).
- Live-ingested new claims get their own generated evidence trail.

---

## v2 — 2026-06-21 — Live data, working tabs, animation
Frozen in `v2/`. Latest = top-level.

**Shared (all three):**
- **Canonical data model** — one baseline (`EXO.base`) so numbers line up across panels:
  cycle 1345, Qwen3.6-27B-MTP @ 80K, 337 wiki topics, 70 skills, 1129 OSS claims, MAINTAIN cadence.
  On port, each `EXO.tick()` is replaced by a real `fetch` (Docker MCP telemetry / cycle journal / OSS API).
- **Real-time refresh** — `requestAnimationFrame` engine loop + per-value flash on change.
- **Sim-time compressed (~22s/cycle)** for demo, so idle cycles visibly advance instead of every 30 real min.
- **Animations** — tab underline grow, view cross-fade/slide-in, number flash, fresh-row/entry slide-in.

**System (MAGI ⇄ MGS·Delta):**
- Functional **tabs**: Inference (live gauges) / Telemetry (live tiles) / Containers (v16 cycling, v17 idle-paused cards).
- Live telemetry jitter (VRAM, temp, decode, power, draft-accept), token counter climb, animated ring gauges.
- Cycle completion ticks the counter + rotates cadence (MAINTAIN≤3→BUILD×5→EXPLORE); header tag + container card mirror it.

**Office (iDroid ⇄ Amber-Ops):**
- Live **idle-cycle engine**: the RUN op's progress bar + stage advance; on completion it flips to DONE,
  a fresh cycle row **slides in at top**, counter increments, cadence rotates, detail re-selects to the new op.
- Sub-view **tabs**: Cycle Log (list+holo detail) / Workspace / Skills.
- Detail panel cross-fades on op select; BUILD cycles occasionally +1 wiki topic (propagates to status bar).

**Intel (YoRHa ⇄ Archive):**
- Tree sub-sections are **real tabs**: Claims / Hypotheses / Forecasts / Contradictions / SWARMFISH swap the codex.
- Live **ingest**: claim counter climbs continuously; when Claims is open, new claims **slide into the ledger**
  (drawn from a newswire pool, deduped-against-FAISS framing). Counters flash in tree + status bar.
- Codex cross-fades on section switch; entries carry confidence meters, provenance, volatility.

---

## v1 — 2026-06-21 — First spirit pass (3 materials)
Frozen in `v1/`. The proof that one component skeleton survives three materials.

- **System** (MAGI ⇄ MGS·Delta) — opaque amber-CRT; 3 ring gauges + telemetry tiles + status bar. Static snapshot data.
- **Office** (iDroid ⇄ Amber-Ops) — TRANSLUCENT holo-blue; list + holographic detail. The "solid surface in glass" stress test.
- **Intel** (YoRHa ⇄ Archive) — LIGHT parchment SERIF; tree nav + codex. Felt-not-seen on paper, inverse-block selection.
- Locked principles: structure-is-component / theme-is-material · felt-not-seen effects · solid surfaces over texture · real-data integrity.
- Theme toggle per panel; live clock the only live element.
