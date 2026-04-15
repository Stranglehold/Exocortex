# OVERHAUL PLAN: OSS + SWARMFISH Intelligence Pipeline

**Spec ID:** L3-OVERHAUL-OSS-SWARMFISH-001
**Date:** 2026-04-14
**Authors:** Jake (direction), Kestrel (implementation), grounded in research from two parallel investigation agents
**Status:** Draft — Phase 1 implementing tonight
**Driving artifact:** [eval/STRESS_TEST_007_OSS_SWARMFISH_IRAN_BLINDNESS.md](../eval/STRESS_TEST_007_OSS_SWARMFISH_IRAN_BLINDNESS.md)

---

## 1. Why This Spec Exists

ST-007 documents a catastrophic failure of the OSS+SWARMFISH pipeline. Asked to characterize the Iran/Strait of Hormuz situation in April 2026 — during day 45 of an active war — the SWARMFISH committee produced a confident (67.6%) prediction that the Strait would remain open with periodic tensions. **Reality:** the Strait had been blocked since Feb 28, CENTCOM was launching a full naval blockade the same day, Khamenei had been dead for six weeks, and the new Supreme Leader Mojtaba Khamenei had been installed in March.

The committee was not stupid. It was **fed the wrong data and never asked why.** Of 20 claims tagged `iran-hormuz` by OSS, only 4 were on-topic. The off-topic 16 included Pacific drug-interdiction strikes, Qantas flight rerouting, Australian EV sales, and Sam Altman's home incident. Zero claims about the actual war reached the committee — not the blockade, not the mining, not the leadership succession, not the carrier strike groups.

This spec lays out a full architectural overhaul to ensure ST-007 cannot recur.

---

## 2. Diagnosed Root Causes (from parallel investigations)

### 2.1 OSS layer

**Topic-tagging contamination (the primary mechanism).** Verified by code review of `services/oss/src/ingest.py:209-218`. The ingestion pipeline calls an LLM to classify each claim against the available topic tags, but the prompt only passes **tag names** (`iran-hormuz`, `iran`) without the **descriptions** that exist in the `topics` database table. The LLM has no semantic context to distinguish narrow topics from broad ones, so it generalizes — anything mentioning Iran, naval activity, "strike," or "war" gets tagged `iran-hormuz`. The `topics.description` column exists in `schema.sql:265-274` and contains the right guidance ("Coverage of Iran-related Hormuz attribution and military posture"), but `get_active_topics()` only selects `tag` (line 266), so the description is dead weight.

**Source coverage catastrophe.** Verified by querying the live OSS database. Of 17 configured sources, **9 are active and 8 are failing.** Both **Reuters and AP have ZERO claims ever ingested** despite being configured — their feed URLs are broken or their proxies are non-functional. The active sources are dominated by The Guardian (1,749 claims), BBC (1,317), Al Jazeera (1,075), with ABC News, NYT, Fox News, NPR, WSJ, and The Intercept rounding out the active set. **Zero specialized intelligence sources are configured at all** — no Defense News, no Naval News, no USNI News, no Lloyd's List, no TradeWinds, no Tehran Times, no Mehr News, no Times of Israel, no Foreign Policy, no War on the Rocks. The result: 948 Iran-related claims in the last 7 days, but **none mention CENTCOM, the blockade, Hormuz mining, or carrier strike group deployments** — because none of the sources covering that material are in the source list.

**Auto-promotion bypass.** Wire sources (Reuters, AP) are configured with `require_topics: False` (`ingest.py:316`), meaning they auto-promote to the ledger regardless of whether the LLM assigned a topic. This compounds the contamination problem when those sources eventually start working.

**Ingestion paused.** As of test time, `OSS_INGEST_PAUSED=true` in the container environment. No new claims are being added. (This is a deliberate analyst pause, not a bug, but it means the data layer is currently frozen.)

### 2.2 SWARMFISH layer

**No input quality gate.** Verified by code review of `services/swarmfish/src/app.py:113-165`. The `/acp/predict` endpoint accepts whatever context is provided and runs all 8 profiles against it without checking whether the context is relevant to the question. The pipeline trusts the caller to provide good data. The autonomous monitor (`services/swarmfish/src/monitor.py`) is the caller, and it provides whatever the OSS feed returns — contaminated or not.

**Meta-confidence calibrated backward.** When 8 diverse profiles converge tightly on the same answer, the pipeline marks `meta_confidence: HIGH` and `disagreement_level: 0.057` (very low). For a properly diverse committee on a hard problem, **tight convergence on sparse data is evidence of shared error mode**, not collective wisdom. The architecture interprets uniformity as confidence when it should interpret it (in this regime) as a warning.

**Context summary truncation.** [services/swarmfish/src/app.py:89](services/swarmfish/src/app.py#L89) — `context_summary = context[:200] if context else None`. Only the first 200 characters of the input context are stored on the session row, making post-hoc audit impossible. We had to query OSS directly to reconstruct what the committee saw, because the SWARMFISH database had only the first claim line saved. This isn't a behavioral bug but it's a critical observability bug — without the input archive, you can't grade past predictions.

**No "what's missing?" reasoning.** None of the 8 profiles is responsible for asking "what would a competent human analyst expect to see in this input that isn't here?" The Contrarian profile is supposed to provide opposing signal but in practice it just inverts the surface narrative — its position in ST-007 was identical to the consensus. The committee has no profile that adopts the **epistemological** opposing position: questioning the input itself.

---

## 3. Overhaul Architecture

The fix is layered. Each layer addresses a distinct failure mode. They compose: even if one layer fails, the others provide independent defense.

### Layer A — Source coverage (data acquisition)

**Goal:** the OSS source list contains all the major outlets covering any topic the analyst cares about.

**Concrete changes:**

- **A1.** Repair the failing wire feeds. Test Reuters and AP RSS URLs directly (`curl -I`); replace broken URLs with current working endpoints. AP's RSSHub proxy (`rsshub.app/ap/topics/apf-intlnews`) is unreliable; switch to AP's native RSS or a different proxy.
- **A2.** Add Tier-1 missing wires: AFP, CNN World/Middle East, Bloomberg, Financial Times.
- **A3.** Add Tier-2 defense intelligence: Defense News, Naval News, USNI News, Breaking Defense.
- **A4.** Add Tier-3 maritime intelligence: Lloyd's List, TradeWinds, Splash247.
- **A5.** Add Tier-4 regime/regional: Tehran Times (Iranian state media is essential for tracking regime messaging), Mehr News, Times of Israel, Jerusalem Post, Middle East Eye.
- **A6.** Add Tier-5 think tanks: Foreign Policy, War on the Rocks, Atlantic Council Middle East, CSIS Middle East.

**Acceptance criteria:** The source list contains at least 30 active sources. Each Tier-1 source contributes ≥10 claims/day under normal operation. The next iran-hormuz feed query returns claims that include direct CENTCOM, blockade, or naval activity coverage from at least 3 distinct sources.

### Layer B — Topic classification (data routing)

**Goal:** Claims are tagged to topics with semantic precision, not by keyword adjacency.

**Concrete changes:**

- **B1.** Inject topic descriptions into the ingestion LLM prompt. `get_active_topics()` should return tag, display_name, AND description. The prompt should look like:
  ```
  Topic definitions:
  - iran-hormuz: Coverage of Iran-related Hormuz attribution and military posture, including IRGC operations, US Navy CENTCOM activity, tanker incidents, mine-laying, and oil transit security
  - iran: General Iran coverage including domestic politics, nuclear program, sanctions, and diplomatic activity not specifically tied to Hormuz
  
  Topics available: [iran-hormuz, iran]
  ```
  The LLM should be instructed: "Only assign a topic if the claim DIRECTLY engages with the topic's subject matter. Mentioning a country in passing is not sufficient. If unsure, assign no topic."

- **B2.** Tighten and expand the topic descriptions themselves. Currently `iran-hormuz` is described as "Coverage of Iran-related Hormuz attribution and military posture" — too vague. Rewrite to enumerate specific entities and event types. Same for every active topic.

- **B3.** Remove the wire-source `require_topics: False` exception. Wire claims should still auto-promote, but only if topics are assigned. An untagged Reuters claim about North Korean missile tests should NOT end up in the iran-hormuz feed just because Reuters is a wire source.

- **B4.** Add a relevance validator step. After the LLM extracts claims and assigns topics, run a second cheap validation pass: for each (claim, topic) pair, ask a smaller model "is this claim genuinely about [topic_description]? answer YES/NO." Reject claims that fail. (Optional Phase 2 — Layer B1 alone should reduce contamination by 80%+.)

**Acceptance criteria:** A re-query of `/api/feed?topic=iran-hormuz&limit=20` returns ≥80% on-topic claims (manually graded). The Pacific drug-interdiction claims, Qantas claims, and Sam Altman claims do not appear in the iran-hormuz feed. The Tehran Times and Defense News claims about the actual war DO appear.

### Layer C — Input quality gate (SWARMFISH defensive layer)

**Goal:** SWARMFISH refuses to confidently predict when its input is contaminated or sparse, and tells the analyst why.

**Concrete changes:**

- **C1.** Implement an input quality gate in `/acp/predict` (`services/swarmfish/src/app.py`). Before running the profiles loop, compute:
  - `topic_keywords` extracted from the question (e.g., "iran", "strait", "hormuz" from "Assess the current situation for: Iran / Strait of Hormuz")
  - `total_claims` = number of `•`-prefixed lines in the context
  - `on_topic_claims` = number of those lines that contain at least one topic keyword
  - `relevance_ratio` = on_topic / total
  
  If `total_claims >= 5 AND relevance_ratio < 0.5`, the gate is tripped:
  - Prepend a `⚠ INPUT QUALITY GATE: only N/M (X%) of provided claims are directly on-topic` warning to the context that the profiles see (so they can react to it)
  - Tag the session with a `quality_warning` field
  - Cap final `meta_confidence` at MEDIUM regardless of profile agreement
  - Log `[QUALITY-GATE]` to stdout for analyst review

  This is a soft gate — it doesn't refuse to predict, but it ensures the output carries an explicit "treat with skepticism" marker.

- **C2.** Fix the context_summary truncation bug. Change `context[:200]` to either store the full context (preferred — it's text, storage is cheap) or store the first 4000 characters with a `truncated: bool` flag. This restores post-hoc auditability.

- **C3.** Recalibrate `meta_confidence` aggregation. Currently HIGH means "profiles agree closely." Add an explicit downgrade path: if `relevance_ratio < 0.5`, meta_confidence cannot exceed MEDIUM. If `relevance_ratio < 0.25`, meta_confidence is forced to LOW regardless of disagreement. (Phase 2 — for tonight, the C1 gate will surface the warning manually.)

- **C4.** Add a "Devil's Inquisitor" profile. A 9th profile whose entire mandate is meta-criticism: examine the input claim set, ask "what would a competent human analyst expect to see here that isn't here?", and flag missing context categories. Use a slightly different prompt template than the other profiles — this profile doesn't predict the future, it interrogates the present input. Output structure: list of "missing context categories" + "candidate explanations for why they're missing." (Phase 2 — Layer C1 covers most of the value tonight.)

**Acceptance criteria:** When the same iran-hormuz prediction is re-run against the contaminated input from ST-007, the C1 gate fires, the operator brief carries the warning, and meta_confidence is capped at MEDIUM. The session row in the database contains the full input context (not the 200-char truncation).

### Layer D — Observability and regression testing

**Goal:** Future failures are caught immediately, and the iran-hormuz scenario becomes a permanent regression test.

**Concrete changes:**

- **D1.** Preserve session `709fb4a3-5db3-4224-866b-76dcb3e1bad8` in the swarmfish_postgres database as the canonical ST-007 baseline. Do not delete or overwrite it.
- **D2.** Add a `/regression/iran-hormuz` admin endpoint that re-runs the canonical ST-007 question against the current data and reports whether the new prediction passes the ST-007 acceptance criteria (correct identification of the actual war state, OR explicit refusal-to-predict via quality gate).
- **D3.** Add an analyst-visible "input quality" badge to the SWARMFISH session UI, showing the relevance ratio and any quality warnings. Operators should be able to see "this prediction was generated from 20% on-topic input" at a glance. (Phase 2 — UI work.)
- **D4.** Periodic source health reporting. Add a daily summary that flags sources with zero claims in the last 24 hours, sources with abnormally high/low contribution rates, and per-topic claim distribution. Surface in the OSS panel. (Phase 2.)

---

## 4. Phased Implementation

### Phase 1 — Tonight (bounded, high-confidence)

| # | Change | File | Lines | Risk |
|---|--------|------|-------|------|
| P1.1 | Inject topic descriptions into ingest LLM prompt | `services/oss/src/ingest.py` | ~10 lines | Low |
| P1.2 | Improve topic descriptions for `iran` and `iran-hormuz` in the topics table | DB migration or seed update | 2 SQL UPDATEs | Low |
| P1.3 | SWARMFISH input quality gate (Layer C1) | `services/swarmfish/src/app.py` | ~50 lines | Low |
| P1.4 | Fix context_summary truncation (Layer C2) | `services/swarmfish/src/app.py:89` | 1 line | Trivial |
| P1.5 | Repair Reuters and AP feed URLs if tractable | `services/oss/schema.sql` + DB | 2 UPDATEs | Medium (depends on whether new URLs work) |
| P1.6 | Add Tehran Times, Times of Israel, Defense News as initial source additions | `services/oss/src/app.py` admin endpoint | 3 POSTs | Low |
| P1.7 | Resume ingestion | env var or admin endpoint | 1 action | Low |
| P1.8 | Wait for one ingestion cycle (~30 min) and re-run iran-hormuz prediction | n/a | n/a | n/a |
| P1.9 | Validate against ST-007 acceptance criteria | n/a | n/a | n/a |

**Phase 1 success criteria:**

- Ingest LLM prompt now includes topic descriptions
- SWARMFISH quality gate fires on contaminated input
- Context truncation fixed; full input archived per session
- At least one new source actively ingesting
- Re-run prediction either (a) correctly engages with current war state OR (b) carries an explicit input quality warning

### Phase 2 — Reasoning-layer fix (implemented same night as Phase 1)

After Phase 1 deployed, the validation prediction confirmed that input quality
fixes were not sufficient. Even with the actual war reporting in the corpus
(USS Gerald R. Ford in Gulf of Oman, port blockade announcement, war-risk
insurance spikes), the committee continued to predict "Strait remains open"
with HIGH meta-confidence. Confidence actually rose from 0.676 to 0.719.
The failure mode shifted from "contaminated input" to "profiles confabulating
against good input." Phase 2 was scoped to address the reasoning layer.

| # | Change | Status | File |
|---|--------|--------|------|
| P2.1a | System prompt template — add CONTEXT-GROUNDED REASONING section requiring profiles to ground predictions in context facts and override priors when they conflict | ✅ Done | `services/swarmfish/src/acp/predictor.py` SYSTEM_PROMPT_TEMPLATE |
| P2.1b | Add `observed_facts` field to required JSON schema — profiles must extract 3+ facts from context verbatim | ✅ Done | Same file |
| P2.1c | Tighten user message — make CONTEXT explicit as "ground truth," instruct profiles to acknowledge events that have already happened | ✅ Done | `build_user_message()` |
| P2.2 | Grounding validation in `run_profile()` — verifies each claimed `observed_fact` actually appears in context (substring or 60% word overlap), forces confidence cap on failure | ✅ Done | New `validate_grounding()` function |
| P2.3 | Devil's Inquisitor — 9th profile whose mandate is to identify surprising/load-bearing facts the consensus is likely to miss | ✅ Done | `profiles.py` + DI extra fields in `predictor.py` |

**Grounding failure tiers (P2.2):**

- `ok` — at least 3 observed_facts, all match the context
- `partial` — minor mismatch, no penalty
- `missing_facts` — fewer than 3 observed_facts on non-empty context → confidence capped at 0.40
- `fabricated_facts` — ≥50% of claimed facts don't appear in context → confidence capped at 0.30
- `no_context` — context was empty, profile correctly acknowledged it → no penalty

The grounding cap is mechanical, not LLM-based — no extra inference cost per session.

### Phase 3 — Future sessions (deferred from original spec)

| # | Change | Notes |
|---|--------|-------|
| P3.1 | Add 8-12 more Tier-1/2 sources (AFP, CNN, Bloomberg, FT, Lloyd's List, etc.) | Test each URL before committing |
| P3.2 | Implement the relevance validator step (Layer B4) | Second LLM pass with smaller model |
| P3.3 | Implement meta_confidence recalibration (Layer C3) | Explicit downgrade path on low relevance |
| P3.4 | Build the regression test endpoint (Layer D2) | `/regression/iran-hormuz` |
| P3.5 | Source health reporting in OSS panel (Layer D4) | UI work |
| P3.6 | LLM-based fact-grounding check (deeper P2.2) | When per-context-line grounding is needed beyond keyword/overlap |

### Phase 3 — Future (architectural)

- Per-topic vector embeddings for semantic relevance scoring (move beyond keyword matching)
- Per-source quality scoring with feedback loops (analyst marks contaminated claims, source quality decays)
- Multi-language source support (Tehran Times runs Persian editions; Tehran's English coverage is curated for Western audiences)
- Active claim correction tooling — analyst can re-tag a misclassified claim and that signal feeds back to improve future classifications

---

## 5. What This Spec Does NOT Do

- **It does not solve the autonomous resolver's accuracy problem.** The resolver evaluates past predictions against new evidence; if the new evidence is contaminated, the resolver's verdict is unreliable. Layer B fixes ingest contamination, which improves the resolver as a side effect, but the resolver is not directly addressed here.
- **It does not address LLM hallucination within the profiles themselves.** Even with perfect input, individual profiles can fabricate facts (e.g., the Sentiment Decoder's confabulated US naval posture in ST-007). That's a separate problem requiring per-profile prompt hardening and output validation.
- **It does not address the GPU/JIT contention issue** between OSS ingest model and SWARMFISH chat model competing for VRAM. Resume of ingestion may degrade SWARMFISH prediction latency until the model coordination spec is implemented.
- **It does not retroactively fix existing bad classifications.** The 948 Iran-related claims currently in the database that are misclassified will stay misclassified. A migration to re-tag historical claims is out of scope for tonight; the ST-007 baseline session preserves the historical bad state for future comparison.
- **It does not change the SWARMFISH profile roster** beyond adding the Devil's Inquisitor in Phase 2. The existing 8 profiles' methodology citations and prompt templates are not modified.

---

## 6. Validation

The single test that matters: **after Phase 1 deploys, the iran-hormuz prediction either gets the war right OR refuses to predict and tells the analyst why.**

Procedure:
1. Confirm Phase 1 changes deployed
2. Resume OSS ingestion
3. Wait one ingestion cycle (~30 minutes) for new claims with improved topic-tagging to reach the staged → promoted pipeline
4. Manually trigger a SWARMFISH prediction for the iran-hormuz topic
5. Inspect the operator brief, session metadata, and per-profile outputs
6. Grade against ST-007 acceptance criteria

If the prediction fails to either correctly characterize the war OR fails to flag insufficient input, Phase 1 is incomplete and the iteration continues.

---

## 7. Open Questions

- Will improved topic descriptions actually be enough, or will the LLM still over-generalize? **Answer empirically after Phase 1.**
- Should the quality gate be a hard refusal or a soft warning? **Soft warning for Phase 1; revisit after seeing how it reads.**
- Should the Devil's Inquisitor be a 9th profile or a meta-step that runs once per session before the profiles? **Phase 2 design question.**
- How do we score "on-topic" without a vector model? Keyword matching is a starting point but will miss semantic relevance. **Phase 1 uses keywords; Phase 3 considers embeddings.**
- The autonomous resolver runs on a 7-day cooldown — will improved data eventually flush the contaminated historical predictions out, or do we need a one-time rebuild? **Probably need the rebuild; out of scope for tonight.**

---

*This spec is the contract for tonight's work. It will be updated as Phase 1 lands. The success criterion is unambiguous: ST-007 must no longer be reproducible against the post-overhaul system.*
