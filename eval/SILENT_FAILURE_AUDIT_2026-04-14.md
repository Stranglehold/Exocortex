# Silent Failure Audit — OSS + SWARMFISH + Exocortex Stack

**Audit ID:** SFA-001
**Date:** 2026-04-14 (immediately after Phase 2 deployment of the OSS+SWARMFISH overhaul)
**Auditor:** Kestrel
**Scope:** Investigate the codebase and live state for "silent failure" patterns — components that appear to function but actually produce no result, where no caller notices because "no result" is indistinguishable from "no relevant data."

**Trigger:** During Phase 2 validation of the OSS+SWARMFISH overhaul, discovered that `services/swarmfish/src/oss_bridge.py` had been silently broken since deployment, filtering on a `trust_level` field that the upstream endpoint does not return. The bridge returned None for every call, profiles ran with no context, and no upstream code noticed. This audit asks: where else does that pattern exist?

**Method:** Read-only investigation. For each candidate subsystem, run a query or read code that asks "did this actually do work in the last N days?" Compare results to expectations. Document findings verbatim.

**Verdict scale:**
- ✅ **Working** — produces output that matches expected behavior
- ⚠️ **Partial** — produces some output but with significant gaps
- ❌ **Broken** — produces no output, or output that doesn't match purpose
- ❓ **Cannot determine** — would require behavioral testing not available read-only

---

## Findings index

| # | Subsystem | Verdict | Severity |
|---|-----------|---------|----------|
| 1 | OSS `/api/record` trust_level mechanism | ❌ Broken (mismatch) | Critical |
| 2 | Topic-tagging historical pollution | ⚠️ Partial (rot in old data) | High |
| 3 | Autonomous resolver | ✅ Working — but unread | **Critical (silent success)** |
| 4 | Contradiction detection | ❌ Broken | High |
| 5 | Sleep consolidation (Agent Zero) | ✅ Working | Healthy |
| 6 | Ontology entity resolution | ❌ Dormant (never ran) | Medium |
| 7 | SWARMFISH→OSS hypothesis ingest | ✅ Working | Healthy |
| 8 | Test-topic pollution in production | ⚠️ Partial | Medium |
| 9 | Per-source health & wire bypass | ⚠️ Partial | High |
| 10 | Staging backlog (7242 stuck claims) | ⚠️ Partial | High |

---

## Finding 1 — OSS `/api/record` trust_level mismatch (the Phase 2.4 bug, in detail)

**Subsystem:** `services/oss/src/app.py` line 499 (`/api/record` endpoint) and `services/swarmfish/src/oss_bridge.py` (callers)

**Question asked:** does the trust_level system actually flow from DB → API → bridge?

**Evidence:**

The `claims.trust_level` column **exists in the DB schema** (`character varying(20)`, default `'STAGED'`, CHECK constraint enforces 5 valid states), is **populated correctly** (2484 PROMOTED, 7242 STAGED, 79 IRRELEVANT), and is **indexed** (`idx_claims_trust`).

But the `/api/record` endpoint's SQL query at lines 524-538 **does not SELECT trust_level**:
```sql
SELECT c.id, c.claim_text, c.article_url, c.article_title,
       c.technique_class, c.extracted_at, c.published_at,
       c.topic_tags,
       s.name AS source_name, s.cluster, s.confidence_score
FROM claims c
JOIN sources s ON s.id = c.source_id
WHERE %s = ANY(c.topic_tags)
```

And it does not WHERE-filter on trust_level either. The endpoint returns **all claims for a topic regardless of state, including STAGED and IRRELEVANT**, with no field telling the caller which is which.

`oss_bridge.get_oss_context()` was filtering the response with `if c.get("trust_level") == "PROMOTED"`. Since the field is never returned, the filter always evaluated False, `all_claims` stayed empty, the bridge returned None, and `/acp/predict` profiles ran with no context for the entire history of the manual prediction endpoint.

**Verdict:** ❌ **Broken.** Critical severity because it silently nullified the entire SWARMFISH manual-prediction path — every `/acp/predict` call ran with no input, every profile reasoned from training-time priors only, and every grade we did against ST-007 prior to tonight's Phase 2.4 fix was meaningless.

**Status:** Fixed tonight in Phase 2.4 by switching the bridge to `/api/feed` (which DOES filter to non-IRRELEVANT claims server-side and is the correct endpoint for this purpose). But the underlying mismatch in `/api/record` still exists — any other caller of that endpoint expecting trust_level filtering will hit the same bug.

**Recommended follow-up:** Either add `c.trust_level` to the SELECT in `/api/record`, OR document that this endpoint returns ALL claims regardless of state and callers must filter externally, OR delete the endpoint if `/api/feed` covers all use cases.

---

## Finding 2 — Topic-tagging historical pollution

**Subsystem:** `services/oss/src/ingest.py:process_article` (pre-Phase-1 version) and `claims.topic_tags` column

**Question asked:** how many existing claims have wrong tags from the era before tonight's topic-description-injection fix?

**Evidence:**

Distribution of claims by tag count (only counting claims with at least one tag):

| num tags | count | comment |
|---|---|---|
| 1 | 2100 | Mostly clean |
| 2 | 195 | Mostly correct overlap (e.g. iran + iran-hormuz) |
| 3 | 3 | Suspicious |
| 4 | 2 | Almost certainly wrong |
| 5 | 6 | Definitely wrong |

Sample 4-5 tag claims (all PROMOTED to active feed):

```
4 tags  PROMOTED  "The UK government acknowledged that it had run out of time to pass legislation to hand over the Chag[os Islands]..."
5 tags  PROMOTED  "The Philippines claims that cyanide was used to kill fish in the South China Sea."
5 tags  PROMOTED  "Beijing rejects the allegation of cyanide dumping in the South China Sea as a 'farce'."
```

These claims are tagged with `iran`, `iran-hormuz`, `private-credit`, `test-topic`, `test-verify` simultaneously. The pre-Phase-1 LLM was treating topic tags as loose keyword associations rather than topic membership.

Cross-tag combinations specific to iran-hormuz also expose the rot: 9 claims tagged `iran-hormuz + test-verify`, 6 tagged `iran-hormuz + private-credit`, etc. None of those combinations are semantically valid.

**Verdict:** ⚠️ **Partial.** Phase 1's topic-description-injection fix prevents new claims from being mis-tagged, but **historical claims are still wrong and still serving the iran-hormuz feed.** The Chagos Islands claim is still in the active corpus, tagged as iran-hormuz, available to any future SWARMFISH prediction that asks for that topic.

**Recommended follow-up:** Run a one-time re-tag migration. For each PROMOTED claim with multiple topic tags, re-classify with the new prompt + topic descriptions. Discard tags that don't match. This is bounded — probably ~200 claims worth re-classifying — and could be done in a single sleep-window batch.

---

## Finding 3 — Autonomous resolver: working, ignored, **the most important finding of the audit**

**Subsystem:** `services/swarmfish/src/acp/resolver.py`, `services/swarmfish/src/monitor.py:run_resolution_review_cycle`, `acp_proposed_resolutions` table, `/acp/pending` endpoint

**Question asked:** has the autonomous resolver actually been finding sessions to resolve and producing verdicts? If yes, are those verdicts being acted on?

**Evidence:**

The `acp_proposed_resolutions` table contains **19 historical resolver verdicts**:
- 11 still_pending
- 7 falsified
- 1 confirmed

The 7 falsifications include verdicts about Iran/Hormuz that **explicitly identified the committee was wrong, citing specific claim IDs as evidence**. The most recent one (April 13, 11:29 UTC, ~17 hours before this audit):

> **Verdict:** falsified
> **Confidence:** 0.85
> **Cited claims:** #7606 (Al Jazeera) "The United States has imposed a blockade on the Strait of Hormuz", #7607 "The US-Iran conflict has reached day 45 of ongoing hostilities", #7589 "energy shock... more severe than previously recognized", #7587 "gap between physical and on-paper oil prices indicates a more serious energy shock"
> **Reasoning:** "The prediction was for intermittent Iranian-caused disruptions without full closure. However, the evidence shows the US has imposed an actual blockade of the Strait of Hormuz (#7606), which constitutes a sustained physical blocking of the main shipping channel exceeding 48 hours - directly meeting falsification condition #2 and #6. This is not merely 'intermittent disruption' as predicted but an active blockade situation."

**The system was telling itself it was wrong about Iran/Hormuz yesterday morning — clearly, evidentially, with named cited claims. We did not see that signal.**

`/acp/pending` returned **53 pending resolutions** at the moment of this audit. The OSS panel UI exists for this (line 3101: "No pending resolutions. Committee is fully scored.", line 3382: "Fetch the pending-resolution count so the Pending tab badge is accurate", line 3813: `await api(SF, '/acp/pending')`). The Pending tab badge is wired up. The data is there. Nobody is reading it.

Every single proposed resolution has `operator_action = NULL` — none have ever been accepted, overridden, or deferred by an analyst.

**Verdict:** ✅ Working at the resolver layer; ❌ Catastrophically broken at the analyst-attention layer. **The autonomous resolver is a working bug-detection mechanism that nobody is reading.** This is worse than a broken component — a broken component fails loudly. Working components whose outputs are never read fail silently, accumulating wisdom that the system doesn't know it has.

**Recommended follow-up (highest priority of the audit):**
1. Surface the pending-resolution count prominently in the OSS panel header, not just the tab badge — make it impossible to miss "53 falsifications waiting for review"
2. Audit the existing 53 pending resolutions tonight or in the next session — at least the 7 falsified ones — and accept/override each
3. Add a notification mechanism (header-bar warning, status badge) when new falsified verdicts appear
4. Consider whether falsified verdicts above some confidence threshold should automatically downweight the source committee's confidence, not just sit in a queue

---

## Finding 4 — Contradiction detection: the same bug pattern as the bridge

**Subsystem:** `services/oss/src/contradict.py:classify_contradiction`

**Question asked:** has the contradiction detector ever stored a contradiction?

**Evidence:**

The `contradictions` table contains **0 rows**. Zero contradictions have ever been stored. The OSS service has been running for weeks against thousands of claims from sources that frequently contradict each other.

The OSS logs show repeated:
```
[APP] Contradiction classification failed: Expecting value: line 1 column 1 (char 0)
```

That's `json.loads('')` — the LLM is returning empty content.

Reading `contradict.py:67-97`:
```python
resp = get_llm().chat.completions.create(
    model=LLM_MODEL,                # The 27B reasoning-distilled model
    ...
    max_tokens=200,
)
raw = resp.choices[0].message.content.strip()
if raw.startswith("```"):
    raw = raw.split("```")[1]
    if raw.startswith("json"):
        raw = raw[4:]
result = json.loads(raw)            # Always fails when raw is empty
```

The classifier uses the 27B reasoning model with max_tokens=200. The model emits `<think>...</think>` blocks before any JSON. Those thinking blocks exceed 200 tokens, the response gets truncated mid-thinking, no JSON ever appears in the output, `raw` is empty, `json.loads('')` blows up, the exception is caught and logged but not propagated, and the function returns a fallback `{'relationship': 'unrelated', 'confidence': 0.0}` for every call.

**This is the exact same bug pattern as the bridge.** Function appears to work, returns a value, no caller notices the value is fallback garbage. Every contradiction call has been silently failing since the reasoning-distilled model was deployed.

The SWARMFISH `extract_json` function in `predictor.py:266-294` handles this correctly — it strips XML-style reasoning blocks via regex before parsing. `contradict.py` was written before that pattern existed and was never updated.

**Verdict:** ❌ **Broken.** Producing zero output for the entire deployment of the 27B reasoning model.

**Recommended follow-up:**
1. Port the `extract_json` thinking-token-stripping pattern from `predictor.py` into `contradict.py`
2. Increase max_tokens from 200 to at least 1024 to give thinking-token-emitting models room
3. After fix, run a backfill pass on existing claims to populate the contradictions table — the source data is there, only the classification was broken

---

## Finding 5 — Sleep consolidation: working

**Subsystem:** `/a0/usr/Exocortex/sleep_consolidation.py` and friends, runs in `exocortex_v16` container

**Question asked:** is sleep consolidation actually running and producing meaningful work, or is it idle infrastructure?

**Evidence:**

`/a0/usr/Exocortex/sleep_reports/` contains **289 report JSON files** spanning 2026-03-13 through 2026-04-13. Surveying the most recent 50 reports: **42 of 50 contain non-zero action counts.**

Phase distribution:
- Phase 4 (Loop-Period Memory Adjudication): 45/50 — most active
- Phase 0 (Staging Lifecycle): 2/50
- Phase 1 (Self-Consolidation): 2/50
- Phase 2 (Episode Chunking + Anti-Pattern Capture): 1/50

Sample non-zero entries:
- `2026-04-12T18:52:41 [Phase 4]: loop_period_found, promoted_to_inferred`
- `2026-04-12T18:31:01 [Phase 1]: groups_processed, total_entries_before, total_entries_after`
- `2026-04-09T03:55:27 [Phase 2]: loop_patterns_found, already_covered`

The last meaningful run was 2026-04-13 01:13 — about 30 hours before this audit. After that, sleep reports stopped (likely because Agent Zero hasn't been running active sessions to trigger consolidation).

**Verdict:** ✅ **Working.** Sleep consolidation is doing real work and writing structured reports. The recent inactivity is downstream — no sessions to consolidate, not a broken consolidator.

---

## Finding 6 — Ontology entity resolution: dormant infrastructure

**Subsystem:** `/a0/usr/ontology/` (Layer 11)

**Question asked:** has the ontology system actually resolved any entities or stored any relationships?

**Evidence:**

```
//a0/usr/ontology/relationships.jsonl    — 0 lines
//a0/usr/ontology/ingestion_queue.jsonl  — 0 lines
//a0/usr/ontology/resolution_audit.jsonl — 0 lines
//a0/usr/ontology/review_queue.jsonl     — 0 lines
```

Every ontology data file is empty. The Layer 11 ontology system has been deployed but has stored zero entities, zero relationships, zero resolution events.

The directory contains 10 backup files of every ontology .py file (total 50+ .bak files) — evidence that the system has been versioned and re-deployed many times, but never actually used.

This was previously diagnosed as "working as designed" because it requires explicit `source_ingest` tool calls from an agent to populate it — and no agent has ever called that tool. Technically not a bug, but architecturally the ontology system is **infrastructure that has never run** since deployment.

**Verdict:** ❌ **Dormant.** Not broken — never invoked. Whether this matters depends on whether Layer 11 is supposed to be auto-populated from OSS ingestion or only from manual analyst calls. If the latter, then the system is "working" but has zero realized value.

**Recommended follow-up:** Decide whether to (a) wire ontology population into the OSS ingestion path so entities are extracted automatically, or (b) document that the ontology is analyst-only and provide tooling to populate it from the existing corpus, or (c) deprecate it if the value isn't there.

---

## Finding 7 — SWARMFISH→OSS hypothesis ingest: working

**Subsystem:** `services/swarmfish/src/monitor.py:_post_hypothesis_to_oss`, `services/oss/src/app.py` (`/api/hypothesis/from_swarmfish`), `hypothesis_registry` table

**Question asked:** when the autonomous monitor posts a hypothesis back to OSS, does it actually create a row?

**Evidence:**

`hypothesis_registry` contains **12 hypotheses**, all with valid `swarmfish_session_id` linkages, recent activity through April 13. Sample:

| id | swarmfish_session_id | observation_label | status | confidence |
|---|---|---|---|---|
| 12 | 0cde95e9... | Private Credit — Apr 2026 | ACTIVE | 0.411 |
| 11 | de19d639... | Test Verify — Apr 2026 | ACTIVE | 0.709 |
| 10 | 67c66126... | Test Topic — Apr 2026 | ACTIVE | 0.487 |
| 9 | b502b3b2... | Iran / Strait of Hormuz — Apr 2026 | ACTIVE | 0.685 |
| 8 | 06ec0935... | Iran (general) — Apr 2026 | ACTIVE | 0.656 |

The round trip is functional. Hypotheses are reaching OSS with the session ID, observation label, current confidence, and source profile attribution.

**Verdict:** ✅ **Working.** But note: hypotheses are being created for `Test Verify` and `Test Topic` — the test seed topics that should never have made it to production. See finding 8.

---

## Finding 8 — Test-topic pollution in production

**Subsystem:** `topics` table

**Question asked:** when were the test topics created and why are they still active?

**Evidence:**

```
tag             display_name              created_at
----------------------------------------------------------
iran-hormuz     Iran / Strait of Hormuz   2026-03-13 03:45:59
iran            Iran (general)            2026-03-13 03:45:59
test-topic      Test Topic                2026-03-15 14:34:54
test-verify     Test Verify               2026-03-21 01:39:44
private-credit  Private Credit            2026-04-13 02:55:32
```

`test-topic` (March 15) and `test-verify` (March 21) are seed topics from prior development sessions, never archived. They're `active = TRUE`, getting passed to the LLM in every ingest classification call, getting tagged on hundreds of unrelated claims (the 5-tag Philippines/cyanide claim being the worst case), and producing fake hypotheses in the registry like "Test Verify — Apr 2026" with 0.709 confidence.

The autonomous monitor is wasting LLM cycles producing committee predictions for these meaningless topics. Each test-topic SWARMFISH session is ~10 minutes of LLM time that could be spent on real topics.

**Verdict:** ⚠️ **Partial — pollution propagating across the entire pipeline.**

**Recommended follow-up:** `UPDATE topics SET active = FALSE WHERE tag IN ('test-topic', 'test-verify')` — one-line cleanup, deletes nothing (preserves the rows for audit), but stops the pollution immediately.

---

## Finding 9 — Per-source health and the wire-bypass loophole

**Subsystem:** `services/oss/src/ingest.py:316` (auto-promotion logic) and `sources` table

**Question asked:** are sources contributing claims at expected rates? And: is the "wire sources auto-promote without topic check" exception introducing rubbish?

**Evidence:**

| Source | Total | Promoted | Staged | Promote rate |
|---|---|---|---|---|
| The Guardian | 1815 | 425 | 1377 | 23% |
| BBC | 1329 | 286 | 983 | 22% |
| Al Jazeera | 1107 | 202 | 905 | 18% |
| ABC News | 1024 | 175 | 849 | 17% |
| NYT | 1009 | 173 | 836 | 17% |
| Fox News | 913 | 253 | 655 | 28% |
| **Reuters** | **139** | **139** | **0** | **100%** |
| **AP** | **131** | **131** | **0** | **100%** |
| Tehran Times | 79 | 37 | 42 | 47% |
| Defense News | 75 | 33 | 42 | 44% |
| State Dept | 0 | 0 | 0 | n/a |
| Moon of Alabama | 0 | 0 | 0 | n/a |
| X/Twitter etc. | 0 | 0 | 0 | n/a |

Outlet sources promote at 17-28% — the LLM is filtering most claims as off-topic for the active topics. This is reasonable.

**Reuters and AP promote at 100%.** This is the wire-source `require_topics: False` exception in action. Every claim from a wire source is promoted regardless of whether the LLM assigned a topic. That means Reuters claims about North Korean missile tests, weather, sports, etc. all get promoted to the active corpus and become potential SWARMFISH input.

This isn't catastrophic — wire sources are generally high-quality — but it's a back door for noise.

State Dept (URL just fixed tonight, hasn't fetched yet), Moon of Alabama (URL probably broken), and the X/Twitter sources (no RSS) are silent zeros.

**Verdict:** ⚠️ **Partial.** Outlet sources working as designed. Wire sources have a quiet back door that lets ~10% of their content into the corpus untagged. Some sources are silently failing to fetch.

**Recommended follow-up:**
1. Remove the `require_topics: False` exception for wire sources — make them go through the same topic-tagging filter as outlets
2. Test/repair Moon of Alabama URL
3. Decide whether the Twitter/X sources should be removed (X has no public RSS) or replaced with a different mechanism

---

## Finding 10 — Staging backlog: 7242 stuck claims

**Subsystem:** `claims` table, the staging→promotion pipeline

**Question asked:** how many claims are stuck in STAGED forever, and how old are they?

**Evidence:**

7242 claims with `trust_level = 'STAGED'`. Daily distribution of the most recent staged claims:

```
2026-04-14:  488   (today)
2026-04-13:  461
2026-04-06:  315
2026-04-04: 2117   (huge spike)
2026-04-01:  171
2026-03-21:  411
2026-03-20:  685
2026-03-16: 2203   (massive spike — month old)
2026-03-15:    3
2026-03-13:  388
```

There's a claim from a month ago that's still STAGED. There's a March 16 spike of 2203 claims that have been waiting for promotion for nearly a month.

The promotion logic for outlet sources requires `topic_tags` to be non-empty. The pre-Phase-1 LLM prompt (without topic descriptions) frequently produced empty topic lists for ambiguous claims. Those claims went into STAGED and have no path to promotion — there's no re-classification trigger, no retry, no manual review queue.

These claims are not lost — they exist in the database and could in principle be re-tagged. But they're also not visible to any consumer, including SWARMFISH predictions.

**Verdict:** ⚠️ **Partial.** Working as designed, but the design has no mechanism to recover from historical false-negatives in topic tagging.

**Recommended follow-up:** Same as Finding 2 — a one-time re-tag migration with the new topic-description-injection prompt would unstick a meaningful fraction of these.

---

## Synthesis — patterns across findings

The audit confirms that the bridge bug was not unique. **Three findings (1, 4, 6) share the same shape:** a component appears to function (no errors thrown to callers), but produces no actual output, and no upstream code can tell the difference between "no result because nothing matched" and "no result because the function is silently broken."

Each silent-failure component had a specific upstream defense that should have caught it:

| Finding | What should have caught it |
|---|---|
| 1 — bridge filter on missing field | An assertion at the bridge boundary: "if I requested PROMOTED claims and got zero back, log a warning" |
| 4 — contradiction classifier returning empty | The existing fallback returns `{'relationship': 'unrelated', 'confidence': 0.0}` — but `confidence: 0.0` should have triggered a "did this fail?" check upstream |
| 6 — ontology never invoked | A startup self-test: "is anything ever calling source_ingest?" If no, log a notice |

**The general pattern:** layered systems hide failures from layers above unless each layer asserts what it expects from the layer below. **Phase 2.5+ should add explicit assertions at each joint.**

**The most important finding is #3 — the autonomous resolver.** It's working perfectly. It has been telling us we're wrong. We just haven't been reading its output. Of all the findings in this audit, that one is the most actionable and the most consequential. 53 unread resolutions, 7+ confident falsifications including the iran/hormuz one we've been working on tonight.

---

## Priority queue for next session

1. **(P0) Surface the pending-resolution count in the OSS panel header.** Make finding #3 unmissable. ~10 line change to `services/oss/src/app.py` template.
2. **(P0) Audit the existing 53 pending resolutions.** At minimum the 7 falsified ones. Accept or override each.
3. **(P1) Fix `contradict.py` thinking-token stripping.** Port the regex from `predictor.py:extract_json`. ~10 line change.
4. **(P1) `UPDATE topics SET active = FALSE WHERE tag IN ('test-topic', 'test-verify')`.** Stops pollution immediately.
5. **(P2) Re-tag migration for staged claims.** Run the new topic-classification prompt on the 7242 stuck STAGED claims. Expect to unblock several thousand.
6. **(P2) Remove wire-source `require_topics: False` exception.** Force Reuters/AP through the same topic gate as outlets.
7. **(P3) Decide ontology fate.** Wire it into auto-ingest, build manual tooling, or deprecate.
8. **(P3) Add boundary assertions at silent-failure-prone joints.** Specifically: bridge "got non-empty result" check, classifier "fallback wasn't returned" check, periodic "is this subsystem actually doing work" health probe.

---

*End of audit. No code changes made. All findings are read-only observations.*
