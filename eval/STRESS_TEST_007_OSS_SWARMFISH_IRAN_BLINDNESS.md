# Stress Test Report: OSS + SWARMFISH — Iran/Hormuz Blindness

**Test ID:** ST-007
**Date:** 2026-04-14 (original), revised 2026-04-14 later same day after SFA-001 audit
**System Under Test:** OSS intelligence ledger + SWARMFISH committee prediction service (production deployment, day-of-test state)
**Subject domain:** Geopolitical risk forecasting — Iran / Strait of Hormuz
**Test type:** Naturalistic (not designed) — discovered during routine analyst review of the autonomous monitor's output
**Operator interventions during run:** 0
**Cost:** Local inference only
**Related artifacts:** [OVERHAUL_PLAN_OSS_SWARMFISH_L3.md](../specs/OVERHAUL_PLAN_OSS_SWARMFISH_L3.md) · [SILENT_FAILURE_AUDIT_2026-04-14.md](SILENT_FAILURE_AUDIT_2026-04-14.md)

> **⚠ REVISION NOTICE (end of document):** This test's diagnosis was partially corrected after the SFA-001 silent-failure audit uncovered a critical finding that reframes the failure mode. See §10 "Post-audit diagnosis revision" at the end of this document for the corrected interpretation. The original observations in §§1-8 remain accurate as a moment-in-time snapshot of what was seen; §9 (disposition) and §10 capture what we now understand.

---

## 1. Test Objective

Determine whether the production OSS+SWARMFISH pipeline can correctly characterize a high-stakes, fast-moving geopolitical situation when run autonomously. The Iran/Hormuz topic was selected because (a) it is a real active war as of the test date, (b) the situation is well-covered by mainstream international press, and (c) the analyst has independent ground truth to grade against.

**The committee's output, the input it reasoned from, and the underlying ground truth were captured at the same instant.** This is a moment-in-time snapshot of how the system performs against a hard problem with an unambiguous correct answer.

The test was not designed to surface failures. It was a routine inspection. The failures surfaced themselves.

---

## 2. Ground Truth (April 13–14, 2026)

Compiled from Reuters, Al Jazeera, NPR, CNN, Wikipedia, Time, Haaretz, IAEA, Lloyd's List, CNBC, Foreign Policy, Atlantic Council, and others. Verified by external research.

**Strategic situation:**
- **Day 45+ of the 2026 Iran War.** Active kinetic conflict between US/Israel and Iran beginning Feb 28, 2026.
- **Khamenei assassinated Feb 28** in opening US-Israeli strikes, age 86.
- **Mojtaba Khamenei** (Khamenei's son) confirmed as new Supreme Leader **March 9** after Assembly of Experts election; succession reportedly engineered by IRGC commanders Vahidi and Jaffari.
- **Pezeshkian still President**; civilian-military fracture reported between Pezeshkian and IRGC's Vahidi over war economics.

**Strait of Hormuz status:**
- **Strait largely blocked since Feb 28.** Only 17 vessels transited on April 11 (vs typical ~70/day).
- **21 confirmed IRGC attacks on merchant shipping.**
- Iran has reportedly **laid naval mines** and declared a "permanent control mechanism" for the strait.
- **CENTCOM full naval blockade of all Iranian ports begins April 13, 10:00 ET — i.e. the day of this test.**
- US force composition in CENTCOM AOR: **two carrier strike groups** (USS Gerald R. Ford in Gulf of Oman, USS Abraham Lincoln in northern Arabian Sea), 12 destroyers/frigates outside the Gulf, 6 inside, third CSG in reserve in Eastern Med — largest US naval concentration in the Middle East since 2003.
- **Mine-clearance gap:** Avenger-class MCM ships were decommissioned Sept 2025; CENTCOM is improvising with destroyer-mounted systems and USVs, untested at scale in contested water.

**Diplomacy:**
- April 11–12 **Islamabad talks failed** after 21-hour marathon. Iran offered 5-year enrichment suspension; US demanded 20-year halt (a softening from earlier permanent-dismantlement insistence).
- VP JD Vance led US delegation with envoy Steve Witkoff and Jared Kushner. Pakistan hosted; Türkiye also reportedly active as mediator.
- **Israel preparing to resume strikes on Iran** per Israeli press.

**Markets:**
- **Brent ~$102–103/bbl** (+40% since war start). **WTI ~$104** (+50%).
- Brent briefly spiked **past $120** in early March on initial Hormuz closure.
- Lloyd's Joint War Committee added entire Persian Gulf to Listed Areas. US/UK/Israeli flagged ships paying ~3x premium of others.

**Other load-bearing facts:**
- **IAEA access terminated by Iran Feb 28.** Last verified stockpile (June 2025): 440.9 kg of 60% HEU. Current breakout status unknown.
- **Houthis joined the war March 28** with ballistic missiles at Israel.
- **Hezbollah significantly weakened** after April 8 Israeli strike killed 300+ in 10 minutes.
- **GCC fractured** — UAE leaning toward open military support, Saudi/Kuwait/Bahrain hedging, Iran has retaliated against all of them.
- **Russia/China abstained** on UNSC resolution condemning Iran. Limited material support from either.

---

## 3. The Committee's Prediction

**Session ID:** `709fb4a3-5db3-4224-866b-76dcb3e1bad8`
**Generated:** April 14, 2026 04:31 UTC
**Topic:** Iran / Strait of Hormuz
**Input:** "41 new promoted claims" from OSS feed
**Question:** "Assess the current situation for: Iran / Strait of Hormuz. 41 new intelligence items detected since last assessment. What is the most likely trajectory and what conditions would change this assessment?"

**Consensus:**
- **Confidence: 67.6%** ("Strait remains open with periodic tensions, no full closure")
- **Range:** 64.7%–70.4%
- **Meta-confidence: HIGH** (agents broadly agree)
- **Disagreement level: 0.057** (extremely tight clustering)

**Per-profile confidences:**

| Profile | Confidence | Capped | Position |
|---------|------------|--------|----------|
| Base Rate Analyst | 72% | no | "Continued elevated tensions without full closure, periodic disruptions" |
| Contrarian | 72% | no | "Strait remains open, narrative overstates risk" |
| Historian | 58.5% | no | "Sustained tension with periodic spikes, full closure unlikely" |
| Reflexivity Modeler | 62% | no | "Self-reinforcing feedback loop in expansion phase, full closure low probability" |
| Decomposer | 62% | no | "35–45% escalation probability, no full closure within 30 days" |
| Network Analyst | 72% | no | "Periodic events but no sustained closure" |
| Sentiment Decoder | 72% | no | "Narrative overstates threat, sentiment positioned for downward recalibration" |
| Risk Manager | 70% | **yes** (Taleb extremistan cap) | "Persists at elevated levels, no full closure, tail risk remains non-trivial" |

**Falsification conditions** identified by the committee included: "Iran announces or executes sustained closure of Strait of Hormuz for more than 48 hours" and "Observable Iranian naval buildup or mine-laying activity detected." **Both of these conditions had already been met before the prediction was generated.**

---

## 4. The Input Data the Committee Saw

I queried OSS `/api/feed?topic=iran-hormuz&limit=20` immediately after the prediction completed. Of 20 returned claims, manually classified by topic relevance:

**On-topic (4/20 = 20%):**
- "Electric vehicle purchases are increasing in Australia while the US-Israel conflict over Iran disrupts oil supply..."
- "The 'stagflationary shock' from the Iran war is linked to a crash in household confidence in Australia."
- "Andrew Hauser, the Reserve Bank of Australia's deputy governor, described a 'stagflationary shock' from the Iran war..."
- "A sharp rise in inflation is one of the economic impacts attributed to the Iran war."

(Note: even these "on-topic" claims are downstream financial commentary about the Iran war's impact on Australia, not direct reporting on Iran or the Strait.)

**Off-topic (16/20 = 80%):**
- 4 claims about Qantas flight rerouting to Asia/Europe (irrelevant)
- 1 claim about Australian EV sales (irrelevant)
- 3 claims about an Australian arms-export legal bid related to Israel (irrelevant)
- **5 claims about US military strikes on vessels in the eastern Pacific and Caribbean — Trump-era drug interdiction operations with zero connection to Iran**
- 1 claim about NY anti-war protesters arrested
- 1 claim about Sam Altman's home incident
- 1 claim about a Brazilian intelligence chief arrested by ICE

**Zero claims** about: the Strait blockade, the CENTCOM blockade announcement, IRGC attacks on shipping, mine-laying, Khamenei's death, Mojtaba succession, Islamabad talks, Carrier Strike Group deployments, Houthis, Israel's planned strikes, Brent/WTI price levels, Iranian nuclear status, IAEA termination, Pezeshkian-Vahidi tensions, GCC alignment.

The general `iran` topic feed is barely better. Of 20 returned claims, only 6 are on-topic, and those 6 are dominated by commentary about the failed Islamabad talks (which is welcome but represents perhaps 10% of the news ecosystem's actual Iran coverage that day).

**The committee was asked to assess Iran/Hormuz and was given Pacific drug-interdiction claims and Australian RBA financial commentary.**

---

## 5. Failure Analysis — Three Layers

### Layer 1 — OSS data pipeline (PRIMARY failure)

This is the source of the catastrophe. Two independent OSS bugs combine:

**Bug 1A: Topic-tagging contamination.** Claims that have nothing to do with Iran are being assigned the iran-hormuz topic_tag. The 5 Pacific drug-strike claims are the most egregious example — they share zero keywords with "iran", "hormuz", "strait", or "IRGC". Whatever topic-assignment mechanism OSS uses (vector similarity, keyword match, LLM classification, or per-source mapping) is producing >80% false positives on this topic. (Root cause investigation in progress as of test report time.)

**Bug 1B: Source coverage gap.** The OSS source list is missing the major outlets covering the war. Reuters, AP, AFP, BBC, CNN, Bloomberg, Financial Times, Defense News, Naval News, Lloyd's List, Times of Israel, Tehran Times, Atlantic Council, CSIS — none of these (or their RSS feeds) appear to be ingesting into OSS, because their content would generate dozens of war-relevant claims per day and instead the corpus has zero. (Root cause investigation in progress.)

**Combined effect:** the iran-hormuz topic is being populated by a small handful of sources (predominantly The Guardian and Al Jazeera based on this sample), most of whose Iran-mentioning content is downstream economic commentary or unrelated stories that mention "US military" or "naval." The committee was reasoning from a contaminated 20% on-topic dataset that contained zero direct war reporting.

### Layer 2 — SWARMFISH reasoning (SECONDARY failure)

Even given bad inputs, the committee should have caught the data quality problem. They didn't. Specific failures:

**Sentiment Decoder confabulation.** Claimed "Observable data shows US naval activity concentrated in Pacific/Caribbean drug interdiction zones, not Persian Gulf escalation patterns." This is **factually wrong by an order of magnitude.** Two carrier strike groups are in CENTCOM AOR. The profile generated this claim by reading the contaminated input literally — there are 5 Pacific-drug-strike claims in the feed, so it concluded that's where US naval activity is. **No profile asked the obvious question: "Why am I being shown Pacific drug interdictions when I'm asked about Hormuz?"**

**Contrarian failed to be contrarian.** The Contrarian profile's position aligned with the consensus ("strait will remain open"). A real contrarian would have challenged the input set itself: "We're being shown Australian RBA stagflation commentary but no direct Hormuz reporting; either nothing is happening (so why is the RBA panicking?) or something is happening that we're not seeing. The latter is more likely." That meta-question is exactly what a contrarian profile is for, and it didn't happen.

**Base Rate Analyst applied an invalidated prior.** Anchored on "Iran maintains rational cost-benefit calculation regarding its own economic survival." This prior was correct for the pre-war world, but Iran's leadership has been decapitated and the survival calculus has fundamentally changed. The base rate from the 1980s Tanker War does not apply when the regime is in week 7 of an existential war.

**Historian picked the wrong analogue.** Identified the 1980–1988 Tanker War as closest relevant-similarity match (similarity score 0.72). The current situation has already passed that threshold — open war, mined waters, and a formal blockade are beyond the Tanker War's shadow-conflict character. Better analogues would be Operation Earnest Will + Praying Mantis (1987–1988) or the early phase of Operation Iraqi Freedom (2003).

**Risk Manager was the most epistemically honest.** Capped its own confidence at 0.70 citing Taleb's "extremistan" framework, with the prescient note that "stability often precedes sudden regime shifts — the model may be wrong precisely when it matters most." This is exactly what was happening. Unfortunately 0.70 is still high — given the data thinness it should have been LOW.

**Decomposer / Network Analyst / Reflexivity Modeler** all hand-waved at methodology citations (Fermi estimation, Minsky framework, Soros reflexivity) without showing mechanical reasoning. None identified a specific belief-action loop with named actors. Reflexivity Modeler in particular should have been the one to say "the RBA stagflation commentary IS the reflexive belief — the underlying trend has already moved past it" — instead it concluded the reflexive loop was in expansion phase.

### Layer 3 — Architectural failure (STRUCTURAL)

The committee's `meta_confidence` field is **HIGH** with a `disagreement_level` of **0.057**. The pipeline interprets tight convergence as strong confidence. But on contaminated input, tight convergence is the **opposite** of what should boost confidence — it's evidence of shared error mode.

There is **no input-quality gate** anywhere in the SWARMFISH pipeline:

- No "what fraction of provided claims are directly on-topic?" check
- No "what's the temporal density of input claims relative to the question's time horizon?" check
- No "are there contradictions between claims that should trigger investigation?" check
- No "what are the OBVIOUS questions a human analyst would ask but the input doesn't answer?" check

There is also a **storage truncation bug** in [services/swarmfish/src/app.py:89](services/swarmfish/src/app.py#L89): `context_summary = context[:200] if context else None`. The full input context is passed to the profiles but only the first 200 characters are stored on the session row. This makes post-hoc audit of the input impossible. We had to query OSS directly to reconstruct what the profiles saw, because the SWARMFISH database had only the first claim line saved.

---

## 6. Plausibility Verdict

**The committee's output is plausible-sounding but reality-blind.** It would survive a casual read by anyone not currently tracking Iran. The methodology citations, well-formed falsification conditions, and calibration notes give the appearance of rigor. The fundamental claim — "Strait remains open with periodic tensions" — is the opposite of the truth, and the reasoning that justifies it relies on input data that doesn't reflect the actual situation.

**Grading:**

| Axis | Grade | Notes |
|------|-------|-------|
| Forecast accuracy vs reality | **F** | Predicted stable open Strait while a blockade was in effect and CENTCOM was launching a full naval blockade the same day |
| Reasoning quality given the data shown | **C+** | Methodology citations are name-checks, but at least Risk Manager and Historian engaged seriously with the (wrong) analogue |
| Input interrogation | **F** | Zero profiles questioned why they were being shown Pacific drug-strike claims when asked about Hormuz |
| Meta-confidence calibration | **F** | HIGH meta-confidence on a topic where the data is 20% relevant is the opposite of the correct response |
| Falsification design | **B** | Falsification conditions are reasonable in shape, but two of them had already been met before the prediction was generated |

---

## 7. What This Test Establishes

ST-007 is the canonical regression test for the OSS+SWARMFISH overhaul. After the overhaul, the same query against the same topic must produce **either**:

1. A correct prediction that engages with the actual war state (CENTCOM blockade, Khamenei succession, mine-laying, oil price impact, etc.), **or**
2. A refusal to predict due to insufficient/contaminated input, with an explicit `meta_confidence: INSUFFICIENT_DATA` signal back to the analyst

**Pass criteria for the regression test:**

- Topic feed for `iran-hormuz` returns ≥80% on-topic claims
- Source list includes at least 5 of the major war-coverage outlets (Reuters, AP, BBC, CNN, AFP, Al Jazeera English, Bloomberg, FT, Defense News, Naval News)
- At least one promoted claim about: blockade status, IRGC operations, Iranian leadership, US naval posture, oil prices, IAEA status — i.e., concrete current state, not just downstream commentary
- SWARMFISH input quality gate flags a session with `<50% on-topic input` and refuses high meta_confidence
- A re-run of the same prediction either (a) correctly identifies that the Strait is closed/blockaded, or (b) explicitly declines to predict and tells the analyst why

If the post-overhaul system passes ST-007, we have confidence the underlying failure mode is fixed. If it doesn't, the overhaul is incomplete.

---

## 8. Test Disposition (original)

**Status:** FAILED. Committee output catastrophically wrong. Architectural failures identified at three layers. Test artifact captured for post-overhaul regression validation.

**Follow-up artifacts:**
- `OVERHAUL_PLAN_OSS_SWARMFISH_L3.md` — phased plan derived from this test (in progress)
- OSS topic-tagging investigation (subagent in progress)
- OSS source list audit (subagent in progress)
- SWARMFISH input quality gate (implementation tonight)

**This file is the benchmark.** Future tests against the same scenario must reference `ST-007` as the baseline. The session ID `709fb4a3-5db3-4224-866b-76dcb3e1bad8` is preserved in the swarmfish_postgres database for direct comparison.

---

## 9. Phase 1 + 2 validation outcomes (same night, before audit)

**Session b9103c78 (autonomous monitor, post-Phase-1 deploy, pre-audit):** consensus 0.312 / LOW meta / 0.272 disagreement. Quality gate fired at 8% relevance. Committee responded correctly to contaminated input. This was the autonomous monitor path, which fetches OSS claims directly (not via `oss_bridge`).

**Session 1e58ded5 (manual `/acp/predict`, post-Phase-1, pre-Phase-2):** consensus 0.719 / HIGH meta / 0.049 disagreement. Looked like a "reasoning-layer failure" at the time — the committee appeared to be confidently ignoring good data. Diagnosed as requiring Phase 2 grounding validation.

**Session 1e58ded5 context_summary: NULL.** This was the signal that should have caught the bridge bug earlier in the night but didn't — we only noticed it during Phase 2 DB inspection. The manual endpoint's context field was never populated.

**Session a11d07e0 (Phase 2 deployed, bridge fixed, manual `/acp/predict`):** consensus 0.703 / HIGH meta / 0.067 disagreement. Profiles extracted 5 observed_facts each (verified in DB at `acp_predictions.profile_extra_data`). Every profile's reasoning_summary explicitly referenced the blockade, the CSGs, oil continuing to flow, and the Vance diplomatic channel. Devil's Inquisitor correctly identified the consensus blind spot and named Base Rate Analyst and Historian as the profiles that would miss the day-46-blockade signal.

**The committee's conclusion in session a11d07e0 was not "wrong" in the original ST-007 sense.** Given the 12 specific OSS claims the bridge fetched (newest-12-by-published_at from iran-hormuz topic), every profile produced a conclusion faithful to those 12 claims: "blockade is active but oil flowing, diplomatic resolution path open." This is accurate given *that particular slice* of the available evidence. The conclusion diverges from ground truth not because of reasoning failure, but because the 12 claims the bridge happened to select did not include the IRGC attacks, mine-laying, Khamenei succession, or the 3x insurance premium spike — all of which exist in the OSS database but weren't in the newest-12 window.

The original ST-007 graded the committee at F for forecast accuracy. **The corrected grading is:** 
- C-/D: the underlying OSS dataset at that moment had a sampling bias that obscured the full situation, the bridge returned a biased slice, the profiles accurately characterized the slice they received. The committee's methodology is not as broken as the original report suggested.
- A clear win: Devil's Inquisitor provided the meta-signal that the consensus was missing something, even from the biased slice. The architecture is producing the right dissent.
- A clear remaining failure: the bridge sampling logic needs diversity (not just newest-by-date), and the consensus aggregation needs to weight DI's structured dissent more heavily than one-in-nine averaging.

---

## 10. Post-audit diagnosis revision (SFA-001)

After Phase 2 validation, a silent-failure audit (SFA-001) was conducted to look for other gaps in the pattern of the bridge bug. The audit uncovered a finding that reframes ST-007's original diagnosis.

### What changed in the diagnosis

The original ST-007 diagnosed a "three-layer failure": OSS data contamination, SWARMFISH reasoning failure, and architectural meta-confidence miscalibration. With the audit complete, we can now be more precise:

**Original Layer 1 (OSS data contamination):** Confirmed. Topic-tagging was producing 80%+ contamination in the iran-hormuz feed. Fixed in Phase 1 via topic-description injection in the ingest prompt. But the audit also revealed that ~200 historical claims from the pre-Phase-1 era are still in the corpus with wrong tags, and 7242 claims are stuck in STAGED because the pre-fix LLM produced empty tag lists for them. The contamination is fixed forward but not backward.

**Original Layer 2 (SWARMFISH reasoning failure):** Partially false. What we thought was reasoning-layer confabulation in session 1e58ded5 was actually a **silent bridge bug** — the manual `/acp/predict` endpoint was returning NULL context to profiles, and profiles were producing training-time-prior predictions with no input at all. The "confabulation" was invented by profiles reasoning without data, not by profiles ignoring data. Fixed in Phase 2.4 by switching `oss_bridge.py` from `/api/record` (which doesn't return `trust_level`) to `/api/feed` (which filters to non-IRRELEVANT server-side).

When the bridge was fixed in session a11d07e0, profiles DID engage with the input (verified in DB), DID extract observed_facts, DID pass grounding validation, and DID acknowledge war facts in their reasoning. **The reasoning layer is less broken than ST-007 originally claimed.** The remaining gap is not "profiles ignoring data" but "profiles producing methodology-correct conclusions on a sampling-biased slice of the available evidence."

**Original Layer 3 (architectural meta_confidence miscalibration):** Still true but incomplete. The meta_confidence aggregator treats tight convergence as HIGH regardless of input quality or the presence of structured dissent. Devil's Inquisitor's adversarial dissent in session a11d07e0 was averaged in as one vote of nine rather than treated as a structural signal. The audit's finding 3 (autonomous resolver) adds a fourth architectural failure: even when the system has generated a correct falsification verdict, there's no attention-layer mechanism to surface it to the analyst.

### The critical audit finding that reframes this test

**Finding 3 from SFA-001: the autonomous resolver had already identified the iran/hormuz prediction was falsified — seventeen hours before this test was written.**

At 2026-04-13 11:29 UTC, the autonomous resolver wrote the following to `acp_proposed_resolutions`:

> **Verdict:** falsified (confidence 0.85)
> **Cited claims:** #7606 "The United States has imposed a blockade on the Strait of Hormuz" (Al Jazeera), #7607 "The US-Iran conflict has reached day 45 of ongoing hostilities", #7589 "energy shock... more severe than previously recognized", #7587 "gap between physical and on-paper oil prices"
> **Reasoning:** "The prediction was for intermittent Iranian-caused disruptions without full closure. However, the evidence shows the US has imposed an actual blockade of the Strait of Hormuz (#7606), which constitutes a sustained physical blocking of the main shipping channel exceeding 48 hours - directly meeting falsification condition #2 and #6."

That verdict was sitting in the database, tagged as `operator_action = NULL`, surfaced through `/acp/pending` which returns 53 such entries at the moment of the audit. The OSS panel has a Pending tab with a count badge wired up. The entire diagnostic chain was functional. **It was never read by the operator.**

The original ST-007 framing called the system "catastrophically wrong" and "reality-blind." The accurate framing, as of the audit, is that **the system had generated the correct diagnosis of its own wrongness and the analyst had not been surfaced to notice.** ST-007 is not primarily a forecasting failure — it is an attention-layer failure at the operator interface. The forecasting subsystem was self-correcting; the human-loop interface was not closing.

### What this changes about the regression criteria

The original pass criteria in §7 still apply — correct forecast OR explicit refusal-to-predict — but we should add a fourth criterion that honors the new finding:

**Revised pass criteria for the ST-007 regression test:**

- Topic feed for `iran-hormuz` returns ≥80% on-topic claims (unchanged)
- Source list includes at least 5 major war-coverage outlets (unchanged)
- At least one promoted claim about concrete current state (unchanged)
- SWARMFISH input quality gate flags `<50% on-topic input` (unchanged)
- Re-run of the same prediction either correctly characterizes the war state OR refuses with explicit meta_confidence signal (unchanged)
- **NEW:** If the autonomous resolver produces a `falsified` verdict against a session within 24 hours of prediction, that verdict is surfaced to the analyst through a top-level panel header badge, not only through a tab-specific badge. The system must not be able to diagnose its own error without the analyst being notified.
- **NEW:** Bridge sampling must return at least 20 claims and must include diversity — not just newest-by-date. Claims matching question-specific keywords (e.g., "blockade", "centcom", "irgc", "khamenei", "mine") should be preferentially included alongside recent claims.
- **NEW:** Consensus aggregation must not produce HIGH `meta_confidence` when Devil's Inquisitor confidence ≥0.7 indicates it believes the consensus is missing a load-bearing fact.

### Preservation notes

Session IDs preserved for future comparison:
- `709fb4a3-5db3-4224-866b-76dcb3e1bad8` — original autonomous monitor session, pre-Phase-1, the baseline ST-007 failure
- `b9103c78-531b-4b07-a38d-7675bda22b6d` — post-Phase-1 autonomous monitor, gate fired correctly on contaminated input
- `1e58ded5-d7a9-4b48-9a30-b8a0cba47d22` — post-Phase-1 manual predict, silent bridge bug, no context
- `a11d07e0-f7ac-425d-b59b-3f268164e8e0` — post-Phase-2 manual predict, bridge fixed, profiles engaged with context, sampling bias remaining
- Resolver verdict created 2026-04-13 11:29 UTC against the pre-Phase-1 sessions — preserved in `acp_proposed_resolutions`

Together these sessions capture the evolution of the system across four distinct architectural states in a single night. Any future regression must reference this chain, not just the original ST-007 failure.

---

## 11. Revised overall verdict

**Original verdict (before audit):** "Committee catastrophically wrong. F grade on forecast accuracy. Reality-blind."

**Revised verdict (after audit):** The committee is weaker than expected at extracting nuance from sampling-biased inputs, but its reasoning is less broken than originally diagnosed. The **real** catastrophic failure was at the operator-attention interface — the autonomous resolver had already generated the correct diagnosis of this test's original failure, the OSS panel had a path to surface it, and that path was not prominent enough to be noticed. The forecasting architecture caught its own error. The human-loop interface did not close the loop.

The practical implication: ST-007 should be retired as a "forecast accuracy test" and reframed as a "self-diagnosing system attention test." The question is no longer "can the committee forecast correctly?" It is "when the system has already diagnosed its own error, does the analyst notice?"

This reframing does not invalidate any of the Phase 1 or Phase 2 work. It reveals that the Phase 2.5 work (bridge diversity + DI consensus weighting) is necessary but not sufficient. The most important follow-up is a Phase 3 attention-layer fix: surfacing autonomous resolver verdicts prominently in the OSS panel so the system's self-diagnostics cannot be silently ignored.

See [SILENT_FAILURE_AUDIT_2026-04-14.md](SILENT_FAILURE_AUDIT_2026-04-14.md) and the forthcoming `REPAIR_CHECKLIST_2026-04-14.md` for the full action plan.
