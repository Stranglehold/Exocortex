# Silent-Gap Audit — OSS + SWARMFISH (V2 plugins)

**Date:** 2026-05-25
**Method:** 3 parallel audit agents (UI↔API contracts, OSS backend, SWARMFISH backend + bridge), hunting the silent-failure classes already found this session (shape mismatches, dead-port defaults, defeated guards, error-swallowing, sync-vs-poll UX, concurrency-vs-server assumptions).
**Scope:** `services/oss_plugin/`, `services/swarmfish_plugin/`, shared `webui/`, `tools/oss.py`, `tools/swarmfish*.py`, the OSS↔SWARMFISH bridge. V1 `services/oss/` (standalone Flask/Postgres) audited only for contrast.

**Status legend:** ✅ FIXED · 🔴 HIGH (pending) · 🟠 MED · ⚪ LOW · ❓ agent-reported, verify before fixing.
Items without ❓ on the FIXED list were verified directly.

---

## Burn-down status (2026-05-25, overnight pass)

- **HIGH: 6 of 7 fixed.** Remaining: hypothesis confirmation = similarity-not-truth (DESIGN — how confirmation should work; ties to the intelligence-loop's own "confirmation theater" warning).
- **MED: 8 of 15 fixed.** Fixed: contradiction source labels, JIT-retry-on-timeout, `LLM_TIMEOUT`→300s, salience clamp, single-profile meta honesty, tz timestamp, exact `json_each` topic match, non-blocking ingest "run". Deferred (below).
- **LOW: 3 of 6 fixed.** Fixed: live topic counters, health UNKNOWN-on-failure, install.sh syntax-check completeness, graceful confidence coercion (counted under MED). Deferred (below).

### Deferred — need a decision or a refactor, not a mechanical fix (NOT done overnight by design)
- **Predict heavy-sync → async kickoff+poll** (MED). The real UX fix, but it changes the panel's run behavior and I can't browser-test it — wants a session where Jake QAs. *Highest-value deferral.*
- **Synthesis for/against from `technique_class`** (MED) — needs real stance detection; that's a feature/design call, not a rename.
- **`COMPROMISED` unreachable on low volume** (MED) — detection-policy tuning (how many of 4 metrics = compromised); Jake/Opus call.
- **Claims from RSS teasers only** (MED) — fetching full article bodies is a scope/feature expansion.
- **FAISS↔SQLite two-commit desync** (MED) — needs a reconciliation/atomicity strategy across two stores; architectural.
- **Embedder reloaded per call** (MED) — a shared-singleton refactor across 5 files; deferred to avoid a botched refactor overnight (it's latency/OOM, not correctness).
- **`extract_claims` silent article drop** (MED) — already logs a WARNING; a true health signal needs a failure-rate metric (+ schema, since `rejection_reason` is CHECK-constrained).
- **Bridge linkage / `register_hypothesis` swarmfish_session_id** (LOW) — same design item as HIGH-7 / the merge.
- **Non-JSON `topic_tags` defensive validation** (LOW) — minor; current writers all use `jdumps`, so low real risk.

---

## ✅ FIXED (2026-05-25)

1. **Hypotheses tab permanently empty.** `intelligence-store.js:304` read `d.hypotheses`; endpoint returns `{ok, action, result:[...]}`. → now reads `d.result`. (Verified endpoint shape.)
2. **Analysis on dead port.** `silence.py:21` + `synthesis.py:19` defaulted `OSS_LLM_URL` to dead `:1234` while ingest/llm_config use `:1236`. → aligned to `:1236`. (Verified drift via grep.)
3. **OSS→SWARMFISH bridge corruption.** `hypothesis.py _notify_swarmfish` inserted a STRING into `acp_outcomes.outcome` (REAL) and bypassed scoring. → routes numeric outcome (promoted=1.0/falsified=0.0) through `record_session_outcome`; logs instead of `except: pass`. **Remaining (design):** the bridge is dormant — `swarmfish_session_id` is never set on hypotheses in the V2 plugin (`register_hypothesis` doesn't link them). Activating it needs the hypothesis↔session linkage decision (tied to the OSS↔SWARMFISH merge).

---

## 🔴 HIGH — 5 FIXED (commit 3b69e9b, 2026-05-25), 2 pending

**FIXED:** `source_weights`→source_id (both `_do_promote` and `api_oss_submit`), `OssHealth` tool key/shape, aggregator `domain` threaded from `run_profile`, `api_oss_submit` writes `faiss_id`, activation seed-suppression keyed off matching claim-ids. All deployed to v16 + verified (health endpoint clean; `run_health_check` keys confirmed).
**Still pending:** the last two bullets (rejection override faiss, hypothesis confirmation=similarity).

- **`source_weights` keyed by source_type, not source_id.** `ingest.py:302-313 _do_promote` writes `{source_type: confidence}`; `contamination_cascade.py:393-422` searches by `source_id`. → every auto-promoted claim is invisible to the contamination cascade; a compromised source never triggers remediation on what it promoted. ❓
- **`OssHealth` tool readout always blank.** `tools/oss.py:456-491` reads `health_signal`/`metrics`/`z_score`/`low_trust_count`/`resolution_time`; `meta_detection.run_health_check` returns `overall_status` + flat keys (`false_positive_rate`/`source_trust_skew`/`resolution_time_hours`/`volume_anomaly`). → `Status: ?` + empty metrics regardless of real state. ❓
- **Aggregator domain always "general".** `aggregator.py:42` reads `domain` from each assessment; `run_profile` (`predictor.py:382-398`) never returns it. → per-domain calibration weights are never applied at aggregation; the calibration loop writes domain weights nothing reads. ❓
- **API-submitted claims invisible to synthesis.** `api_oss_submit.py:75-88` computes a FAISS id but never writes it back → `faiss_id=NULL` → synthesis FAISS retrieval can't find them. (The `oss.py` tool path writes it correctly — two submit paths, one broken.) ❓
- **Activation seed-suppression broken.** `activation.py:168-170` compares a claim id (`m["id"]`) against the source-id set → participating claims never marked processed → duplicate `activation_pattern` rows for the same spike (partly masked by 24h dedup). ❓
- **Rejection override produces a second-class claim.** `rejection.py:136-152 override_rejection` re-inserts with no `faiss_id` and never embeds → invisible to dedup (re-duplicates) and synthesis. ❓
- **Hypothesis "confirmation" is similarity, not truth.** `_check_hypothesis_predictions` (`ingest.py:319-365`) confirms a prediction on cosine ≥ 0.70 to any promoted claim, inner `except: pass`. → a hypothesis is "confirmed" by topically-similar claims regardless of whether they support or refute it. Confirmation theater. ❓

---

## 🟠 MED — pending

- **Predict heavy-sync (the original gap).** `intelligence-store.js:390 runPredict` → `api_swarmfish_predict.py:86` runs the multi-minute committee in-request; browser fetch times out, the live committee grid never populates (result only via session-history poll). Needs async kickoff + poll.
- **Ingest "run" heavy-sync.** `intelligence-store.js:204 runIngestNow` → `api_oss_ingest.py:56` (action=run) runs `run_once` (minutes) in-request; `setTimeout(_loadHealth,3000)` + toast assume fast return → danger toast while the cycle is actually still running. ❓
- **Contradictions show "undefined ·".** `intelligence-panel.html:1140` reads `p.source_name`; `api_oss_contradictions.py:124-126` returns `source_a_name`/`source_b_name`.
- **JIT-retry misses timeouts.** `predictor.py:201,222` `_JIT_ERRORS` lacks `"timed out"` → on a `--parallel 1` server (the most likely failure) timeouts never retry, immediately become error rows. ❓
- **`LLM_TIMEOUT=120s` too short for 27B reasoning.** `predictor.py:34` → slow profiles time out → dropped; survivors shown as if the committee agreed (no "6 of 8 dropped" signal). ❓
- **`extract_claims` silently drops whole articles.** `ingest.py:215-217` returns `[]` on any LLM error (timeout/malformed/dead port); `ingest.py:457 if not claims: continue` → no rejection-ledger entry, no health signal. Model outage looks identical to "no claims found." ❓
- **`emotional_salience` unclamped.** `ingest.py:469` `float()` only, no [0,1] clamp, no schema CHECK → an LLM `5.0`/`-1` skews `narrative_drift` salience. ❓
- **Claims extracted from RSS teasers.** `ingest.py:441` uses `entry.summary`/`description` only, stored `raw_text[:500]` → headline-grade extraction weakens every downstream signal. ❓
- **Naive timestamp on analyst submits.** `tools/oss.py:576` `datetime.utcnow().isoformat()` (no `+00:00`) vs tz-aware elsewhere → submitted claims compare inconsistently in time-window queries (drift/activation/dynamics). ❓
- **Synthesis for/against is meaningless.** `synthesis.py:130-142` derives stance from `technique_class` (a manipulation label), not actual stance toward the question → evidence polarity mislabeled; `technique=none` is always "neutral." ❓
- **Single-profile committee → false HIGH.** `aggregator.py:74` `stdev` needs ≥2 points; a 1-profile committee returns `disagreement=0.0` → always meta HIGH. ❓
- **Embedder reloaded per call.** `synthesis.py:46`, `contradict.py:25`, `activation.py:30`, `api_oss_submit.py:54`, `oss.py:557` each load `SentenceTransformer` fresh instead of reusing `ingest.get_embedder()` → latency; OOM here is swallowed → empty results. ❓
- **`COMPROMISED` unreachable on low volume.** `meta_detection.py:64-67` needs 3+ of 4 degraded; several metrics return OK on <2 sources/empty data → attack-detection ceiling unreachable until volume builds. ❓
- **Topic substring over-match.** `tools/oss.py:91-99` dead first query + raw `topic_tags LIKE '%topic%'` → `iran` matches `iran-hormuz`. ❓
- **FAISS/SQLite two-commit desync.** `ingest.py` adds vector then writes `faiss_id` in two separate commits, no transaction → a crash between them orphans a vector / desyncs ids. ❓

---

## ⚪ LOW — pending

- **Topic counts frozen.** `db.py:308-316` `topics.claim_count`/`last_active` never updated anywhere → `oss_list_topics` shows "0 claims" forever; `api_oss_topics` orders by static `last_active`; panel renders static `t.claim_count` (`intelligence-panel.html:939`) not the endpoint's computed `live_claim_count`. ❓
- **Health swallows failures as NOMINAL.** `meta_detection.py:84-86` `run_health_check` catches all → reports NOMINAL on genuine failure. ❓
- **install.sh syntax-check omissions.** `services/oss_plugin/install.sh:133-176` doesn't syntax-check `__init__.py` or `oss_dynamics.py` (both copied) → a syntax error deploys silently. ❓
- **`register_hypothesis` never sets `swarmfish_session_id`** (`hypothesis.py:39`) — the linkage half of the bridge (see FIXED #3). ❓
- **Confidence-as-string loses a profile.** `predictor.py:369` `float(confidence)` raises on `"high"` → whole assessment becomes an error row. ❓
- **Non-JSON `topic_tags` silently invisible.** `db.py:131-141` — if any writer stores a non-JSON string, `json_each` yields nothing → claim invisible to all topic scans. ❓

---

## Structural note (for the OSS↔SWARMFISH merge / Opus)

There are **two OSS implementations**: V1 `services/oss/` (standalone Flask + Postgres) has the *working* calibration bridge (`resolve.py` → POST `api_swarmfish_outcome` → `record_session_outcome`, and it sets `swarmfish_session_id`). V2 `services/oss_plugin/` (in-A0, the live one) has a broken parallel reimplementation. Several HIGH items (bridge linkage, the contamination cascade) are symptoms of the V2 plugin being built fast and never tested end-to-end across UI→API→src→DB→bridge. The merge decision should pick one canonical implementation rather than maintaining the divergence.
