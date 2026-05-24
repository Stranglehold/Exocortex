# Intelligence Reality-Feedback Loop — Build Plan (L3)

## Author: Kestrel — 2026-05-24
## Status: APPROVED (Jake + Opus, 2026-05-24). Decisions RESOLVED:
##   D1 = (b) web-verify reality at deadline + escalate ambiguous to operator.
##   D2 = BOTH auto-propose (from drift/surprise) + analyst-seeded (oss_question);
##        crisp dated falsifiable questions ("Will [event] occur by [date]?").
##   Execute Phase 0 + 1a now; Phase 2 on D1; Phase 3 on D2; acceptance = replay
##   Iran-Hormuz against known reality and confirm the loop FALSIFIES the missed baseline.
## Scope: Make OSS/SWARMFISH a closed-loop forecasting system that grades itself
## against reality, calibrates, and runs as autonomous A0 cycles.

---

## Evidence base (what the investigation found — all measured, not assumed)

1. **Forecasts evaporate.** `services/oss/src/ingest.py::_trigger_swarmfish_v2_predictions`
   fires a SWARMFISH V2 prediction per topic, logs `consensus_confidence`, and
   **never registers the hypothesis** — it does not call `/api/hypothesis/from_swarmfish`.
   The V2 predict response *does* return `falsification_checklist`
   (`services/swarmfish_plugin/api/api_swarmfish_predict.py:123`) — it's discarded.

2. **The questions are non-falsifiable.** The auto-prediction question is literally
   *"Assess the current situation for: {label}… evaluate trajectory confidence."*
   That asks for a vibe number, not a dated event forecast. Nothing crisp to resolve.

3. **`falsifiable_by` is hardcoded null** in the V1 bridge
   (`services/swarmfish/src/monitor.py:287`) — the 12 registry hypotheses are stale
   V1 output. SWARMFISH `predictor.py` *does* generate real
   `falsification_conditions` (prompted for "3–5 specific observable triggers,
   excluding already-occurred events"); they're dropped at the bridge.

4. **Resolution is advisory + manual.** `services/swarmfish/src/acp/resolver.py`
   writes proposals to `acp_proposed_resolutions`; an operator must confirm via
   `/acp/outcome`. No scheduler fires it. `last_prediction_check` cursor exists,
   unused.

5. **Calibration starves.** `calibration.py` needs ≥5 scored outcomes
   (`MIN_CALIBRATION_PREDICTIONS`) to update weights; outcomes never fire
   autonomously, so all 8 profiles stay weight=1.0 "uncalibrated".

6. **Collection is fragile.** Ingestion `OSS_INGEST_PAUSED` defaults true; went
   dark 2026-04-15, 3 days before the Apr 18 Hormuz re-closure. No liveness alarm.

7. **Quality-vs-reality verdict.** On 2026-04-13 the system was 66%-confident in a
   "sustained pressure" baseline, filing the actual dual-blockade/closure events as
   invalidating tail risks, self-reporting 80 confirmed / 0 falsified. Reality
   (Wikipedia/AlJazeera/WaPo): Hormuz closed Mar 27 + Apr 18, US air campaign Mar 19,
   dual blockade Apr 13, ~2,000 ships stranded. The system never noticed.

---

## DESIGN DECISIONS (need Jake before building the resolution loop)

### DECISION 1 — Ground-truth source for resolution
How does the system decide whether a prediction came true?
- **(a) Internal claims** — existing advisory resolver checks claims that arrived
  after the prediction. *Fragile: fails exactly when ingestion goes dark, which is
  what happened.*
- **(b) External web verification (RECOMMENDED)** — an A0 RESOLVE cycle uses A0's
  web/search tools to check reality directly at the prediction's deadline. True
  reality-grounding; robust to ingestion gaps; leverages A0's native strength.
- **(c) Operator-confirmed only** — human grades every outcome. Not autonomous;
  calibration only advances when Jake reviews.
- **Kestrel recommendation: (b) primary + (c) escalation.** Auto-resolve when web
  evidence is clear and the resolver is confident; route ambiguous/contested cases
  to the operator via the existing `escalation_requests` table. Matches the
  project's "deterministic + human-gate-on-ambiguity" doctrine and is the only
  option that calibrates autonomously while staying honest.

### DECISION 2 — Forecast question design
Current auto-question is vague. To be resolvable, forecasts must be crisp.
- **Kestrel recommendation:** generate structured, dated, falsifiable questions of
  the form *"Will [specific observable event] occur on/before [date]?"* derived from
  (active topic) × (recent high-surprise claims) × (analyst active questions —
  `oss_question` already exists). Each carries an explicit resolution date and a
  `falsifiable_by` condition. Confidence attaches to a crisp event, not a "trajectory".
- Open sub-question for Jake: who picks the events — fully auto (LLM proposes from
  drift/surprise signals), or analyst-seeded via `oss_question`, or both? Rec: both
  (auto-propose, analyst can pin priorities).

---

## Architecture: the intelligence cycle as A0 loops

Mirror the idle-engine pattern (`services/idle_watch.py` daemon → cycle types).
Add an **intelligence cycle** family that runs inside A0 and drives the existing
OSS/SWARMFISH A0 tools (which already exist: `oss_ingest_sprint`, `oss_drift`,
`swarmfish_predict`, `swarmfish_outcome`, `oss_hypotheses`, `oss_question`,
`oss_synthesize`). Cycle types map to the intelligence cycle:

| A0 cycle | Intelligence phase | Drives |
|---|---|---|
| **COLLECT** | collection | `oss_ingest_sprint` (bounded), liveness check |
| **ANALYZE** | processing+analysis | `oss_drift`/`oss_dynamics` → on signal, `swarmfish_predict` with a CRISP question → register hypothesis w/ `falsifiable_by` |
| **RESOLVE** | feedback/calibration | find ACTIVE hypotheses past deadline → web-verify reality (Decision 1b) → mark confirmed/falsified → `swarmfish_outcome` → calibration; escalate ambiguous |
| **DISSEMINATE** | dissemination | synthesize current picture + calibration state into a brief (feed.jsonl-style) |

---

## Phased build + testing

### BUILD STATUS (2026-05-24)
- **Phase 0 liveness alarm — BUILT + TESTED.** `_check_collection_liveness()` in
  `ingest.py`, wired into `run_scheduler`. Test: fired `[LIVENESS-ALARM]` at
  941h-old/active; self-guarded when paused. Deployed oss_app (md5 86cc1358).
- **Phase 1a forecast capture — BUILT + TESTED.** Rewrote
  `_trigger_swarmfish_v2_predictions` + new `_register_swarmfish_hypothesis`:
  forecasts now register with non-null `falsifiable_by` (from the V2
  `falsification_checklist`) + a resolution `deadline` + profile attribution,
  idempotent per (topic, month). Test: synthetic SWARMFISH result → hypothesis
  row with 3 falsifiable predictions, all carrying deadline. Discard bug fixed.
- **Phase 1b crisp dated question — BUILT.** Replaced the unresolvable "assess
  trajectory confidence" with a horizon-bounded outcome question that requests
  dated observable falsification conditions. (Drift-derived event specificity is
  Phase 3's ANALYZE cycle.)
- **OPEN BLOCKER (resume collection):** the OSS ingest LLM endpoint
  (`host.docker.internal:1234`) is unreachable — nothing serves it, so resuming
  produces failing extraction calls, not claims. Resuming needs a reachable
  ingest LLM. Options: (1) point at v16's turbo3 27B `:1235` — zero extra VRAM,
  reachable, coordination-guarded, but ingest extraction contends with idle
  cycles on the single 27B slot; (2) stand up a small 4B server — ~2.8 GB,
  tight at current ~3 GB free; (3) hosted API. Kestrel rec: (1), accepting the
  idle-cycle contention (collection runs every 30 min, bounded). NEEDS JAKE.

### PHASE 0 — Restore collection + liveness (decision-independent, build first)
- Resume ingestion; add a liveness alarm (claim age > N hours while active → flag).
- **Test:** force-resume, confirm new claims land within one interval; kill feed,
  confirm liveness alarm fires.

### PHASE 1 — Capture forecasts with real falsification criteria (core fix)
- Fix `_trigger_swarmfish_v2_predictions`: extract `falsification_checklist` from
  the V2 predict response, build `predictions=[{prediction, falsifiable_by, deadline}]`,
  POST to `/api/hypothesis/from_swarmfish`. Stop discarding.
- Replace the vague question with a crisp dated question (Decision 2).
- **Test:** trigger one prediction; assert a hypothesis row appears with non-null
  `falsifiable_by` and a resolution `deadline`; assert `predictions_generated`
  contains the real conditions, not "assess the situation".

### PHASE 2 — Resolution + calibration loop (needs Decision 1)
- RESOLVE cycle: query ACTIVE hypotheses past deadline → establish ground truth
  (web per 1b) → write confirmed/falsified + evidence → call `swarmfish_outcome`
  (Brier/calibration) → mark hypothesis PROMOTED/FALSIFIED; ambiguous → escalate.
- **Test (backtest):** replay the Iran-Hormuz hypotheses against known reality
  (closures Mar 27/Apr 18) and assert the loop FALSIFIES the "sustained pressure"
  baseline and updates at least one profile's Brier score. This is the acceptance
  test — the system must catch the failure it previously missed.

### PHASE 3 — A0 intelligence-cycle daemon
- New daemon (pattern: `idle_watch.py`) or extension that fires COLLECT/ANALYZE/
  RESOLVE/DISSEMINATE on schedule, gated by config (default off), deploy v16.
- **Test:** run one full cycle of each type end-to-end in v16; verify logs, DB
  effects, no overlap with the idle engine, GPU sane.

### PHASE 4 — Profile tuning (needs Phase 2 producing calibration data)
- Once real Brier scores accrue, tune the 8 profiles + consensus weighting against
  measured calibration. (Tetlock/superforecasting methodology research feeds here.)

---

## What this does NOT do
- Does not replace the OSS Docker service or its Postgres — A0 cycles orchestrate
  via existing tools/endpoints; the service stays the system of record.
- Does not auto-act on forecasts (no trading/operational triggers) — analysis only.
- Does not change model config. Cycles run on the existing v16 chat model.
- Phase 4 (profile tuning) is deferred until calibration data exists — tuning
  uncalibrated profiles would be guessing.

---

## Open questions for Jake
1. **Decision 1** (ground-truth source) — confirm 1b+escalation, or pick another.
2. **Decision 2** (question design) — confirm crisp-dated + auto/analyst event
   selection.
3. **Execution scope now** — build Phase 0+1 immediately (decision-light), then
   2/3 after you confirm Decision 1? Or hold all until both decisions are set?
