# Exocortex Stack Audit — Session 002

**Date:** 2026-04-17
**Author:** 4.7
**Scope:** Stack-wide survey. Documentation-first (no code reading this pass). Test matrix for each layer: current state, what can be verified, what can't, known gaps, recommended next test.
**Methodology:** Read the architecture documents, most recent STATE files, design notes, stress test reports, and notebook entries through session 061. Cross-referenced against public agent-architecture research (2025-2026) where it bears on specific findings.
**Framing:** Test guy audit, not architectural review. Surfaces candidates for deeper testing rather than performing the deeper testing itself. Items marked `CLEAN` are sign-offs, not omissions — I checked and the layer looks right.

---

## Summary of Findings

**Layers audited:** 21 (12 original stack layers + 9 deployed extensions and subsystems surfaced by more recent documentation).

**Status distribution:**
- `CLEAN` — operating as specified, no concerns from documentation review: **6 layers**
- `CLEAN with notes` — operating correctly but has adjacent observations worth capturing: **5 layers**
- `NEEDS VERIFICATION` — documentation suggests a potential issue but doc-only review can't confirm; needs Kestrel to check the code or run a specific test: **6 layers**
- `GAP IDENTIFIED` — documented issue that doesn't appear to have been resolved: **3 layers**
- `CONTRADICTION` — multiple documents in the folder disagree about current state: **1 layer**

**Headline findings (the three things I'd prioritize):**

1. **The STATE files are out of sync** (Contradiction). The most recent STATE.md reads "Last updated 2026-03-09 (Session 052)" while STATE_updated.md reads "Last updated 2026-03-14 (Session 057)" and the notebook goes through session 061. There are architectural decisions in sessions 058-061 (adaptive supervisor, migration to `/a0/usr/agents/agent0/`, staging tier deployment, orientation stack, artifact registry, BST v3.2→v3.3) that aren't reflected in either STATE file. This isn't just documentation hygiene — it's the "what's actually deployed?" ground truth, and when proposals are built against stale state they make wrong assumptions.

2. **The memory creation gap may still be partially open** (Gap). Finding 1 from `agent_zero_observations.md` (session 047): stock memorizers disabled, classifier waiting for memories that never arrive. Finding subsequently addressed by Selective Memorizer (deployed "stable" per STATE). But the adjacent chunk-as-conflict bug surfaced at the same time has no clear resolution trail in the documents I read. Need verification that conflict resolver's source-file guard actually shipped and that knowledge-base classifications got repaired after the bug was fixed.

3. **Key architectural claims lack standardized verification** (Methodology gap). The BST rigidity eval (`MODEL_EVAL_V3_RIGIDITY_REPORT.md`) is the best example of an empirical test-first approach in the project. Most other layers have either no comparable empirical eval, or older evals that predate the current model (v3). Applying the rigidity eval methodology to other claims — "the P3 injection prevents compliance cliff," "the supervisor reduces loops," "the tool fallback chain reduces retry churn" — would surface which claims are still operationally true on v3 and which were true for v1 and are now legacy assumptions.

---

## Per-Layer Audit

The stack-layer numbering below follows the README's twelve-layer architecture. Extensions and subsystems that don't fit the layer numbering come after.

### Layer 1 — Belief State Tracker (BST)

**Stated function:** Domain classification driving enrichment, skill surfacing, and (v3.3) tool injection. First processing step before model reasoning.

**Status:** `CLEAN with notes` — the v3.2 and v3.3 work is well-documented and tested.

**What I can verify from docs:**
- Current state (v3.3) is specified in `BST_CURRENT_STATE_AUDIT.md` with domain inventory, classification flow, and downstream consumers.
- Rigidity behavior on v3 is empirically tested (`MODEL_EVAL_V3_RIGIDITY_REPORT.md`). Finding 1: info-only enrichment equals full enrichment on investigation/analysis/philosophical/planning. Finding 2: raw outperforms enriched on investigation (0.812 vs 1.000). Verdict: SHIFT_TO_INFO for reasoning domains.
- Register-shift domains (orientation, meta_cognitive, philosophical) are designed to break momentum and provide minimal enrichment. v3.2 added min_signals=2 threshold to prevent over-triggering.

**What I can't verify without code or testing:**
- Whether the System A / System B domain-list synchronization (flagged as a silent fall-through failure in the audit) has been verified for all 15 current domains.
- Whether the `_COMPLEX_BUILD_RX` gating is still calibrated correctly post-v3.3.
- Whether slot_taxonomy firing on weak signals (flagged in `BST_V33_STRATEGIC_QUESTIONS.md` Question 3) has been audited.

**Gaps / observations:**

- *Execution-domain rigidity untested.* The rigidity eval explicitly didn't cover coding, bugfix, file_ops, system_admin. One bst_002 data point showed raw beating enriched on bugfix. The entire execution-domain enrichment philosophy is currently running on assumptions that were never empirically tested against v3. This is the single biggest hole in the BST's current empirical foundation.
- *Codegen timeout at 300s on bst_003.* The report attributes this to insufficient timeout calibration, not model limitation. Worth verifying — if it's actually unbounded thinking chain, timeout increase won't fix it, only mask it.
- *Planning domain false negative (v3_008 scored 0.25 across all conditions).* The scoring rubric issue is identified. If not already fixed, this is a rubric-update task, not a BST task.

**Recommended tests:**

1. **TEST-BST-001 (Execution rigidity eval):** Run the same 3-condition protocol (enriched / info-only / raw) on 10 execution-domain tasks (coding, bugfix, file_ops, system_admin). This is the missing half of the rigidity finding. Without it, the capability-vs-transport categorization can't be done rigorously for the execution side of the stack.
2. **TEST-BST-002 (Slot taxonomy false-positive audit):** Export slot firing log from a representative session, map each fired slot to its corresponding user intent, flag slots that fired on weak or tangential signals. Opus's Question 3 — the one that wasn't addressed by the rigidity eval.
3. **TEST-BST-003 (Domain list sync):** Static check: for each domain in DOMAIN_CONFIGS, verify matching entry exists in slot_taxonomy.json. Automatable.

---

### Layer 2 — Working Memory Buffer

**Stated function:** Entity and context state extraction across turns. Re-injects file paths, variable names, error messages, decisions as structured context.

**Status:** `CLEAN` — specified, deployed, validated on 25-entity README test (Feb 22).

**What I can verify from docs:** Working as designed per STATE. Holds objectives across 20-step chains.

**What I can't verify without code or testing:**
- Whether the "Working Memory API extraction" enhancement from the Orientation Stack Wave 3 (session 060) has been built. The notebook says "pending build order." No update since.
- Whether WM is currently integrated with the reasoning state persistence (Orientation Stack component 2b) or running independently.

**Gaps / observations:**
- WM is the oldest stable layer in the stack. Its spec predates most of the other layers it now interacts with. Worth a lightweight integration check: does WM still hold the objective when staging tier, reasoning state, and orientation stack are all also writing state? No evidence of a collision but also no evidence it was checked.

**Recommended tests:**
1. **TEST-WM-001 (API extraction status):** Verify with Kestrel whether WM API extraction (self-generated function signatures as entities) was built in Wave 3. If yes, add to this audit. If no, surface as pending.
2. **TEST-WM-002 (Integration with orientation stack):** Confirm WM and reasoning state persistence don't write overlapping keys to `extras_persistent` or to staging.

---

### Layer 3 — Personality Loader (Major Zero)

**Stated function:** Consistent behavioral parameters. Communication protocols, decision-making frameworks, operational boundaries.

**Status:** `CLEAN` — stable, qwen35 profile added session 050, no recent issues.

**Observations:**
- Profile-aware behavior (model-specific personality tuning) is architected but only lightly tested per `DEC-017`. Not a test-guy finding so much as a note that this layer's adaptability is less exercised than other layers.

**Recommended tests:**
- None urgent. If personality behavior changes with new model deployment (v3→v4 transition), re-verify at that time.

---

### Layer 4 — Tool Fallback Chain

**Stated function:** Intercept tool call failures, apply pattern-matched recovery, return corrected result. Failure tracker with SUCCESS_INDICATORS and decay.

**Status:** `CLEAN with notes` — significantly refined through multiple sessions, has resolved its biggest failure modes.

**What I can verify from docs:**
- Fallback overreaction (17 fires, 80% false positive) identified in ST-001, fixed with SUCCESS_INDICATORS and history decay.
- T5 run showed no fallback false-positive cascades. Fallback fired cleanly.
- Error Comprehension heredoc fix (2026-03-22) addressed terminal_early_exit_heredoc pattern.

**What I can't verify without code or testing:**
- Whether the fallback advisor + meta-gate + supervisor warning overlap flagged in `LAYER_COORDINATION_DESIGN_NOTE.md` has been resolved. Design note is pre-spec and explicitly says "no eval data yet." No evidence the coordination protocol got built.

**Gaps / observations:**
- The four-warning-injector overlap problem (fallback + meta-gate + supervisor + structured retry firing simultaneously on one bad tool call) is an architectural concern that doesn't show up as a failure in most traces but would in specific edge cases.
- The LOOP_ALTERNATIVES correction (Mar 7) suggests the fallback logic underwent refinement. No evidence this correction was stress-tested against the same failure modes that motivated the original fallback.

**Recommended tests:**
1. **TEST-FB-001 (Coordination overlap):** Instrument the four warning injectors and run a representative error-prone task. Count: how often do 2+ fire simultaneously on the same failure? If >10% of tool failures trigger multi-layer response, the coordination protocol is load-bearing; if <2%, it's optional.
2. **TEST-FB-002 (LOOP_ALTERNATIVES regression):** The specific failure that motivated the correction should have a regression test. If it doesn't, add one.

---

### Layer 5 — Meta-Reasoning Gate

**Stated function:** Validate model outputs before execution. Check JSON well-formedness, parameter schemas, tool availability. Repair what it can, reject what it can't.

**Status:** `CLEAN` — stable, deterministic.

**Observations:**
- Meta-gate strictness is model-profile-configurable (`meta_gate_strictness: permissive` was recommended for v3 in the tool reliability results — 15/15 JSON validity, 15/15 tool selection).
- v3's tool-calling RL training makes this layer's work lighter than it was for v1. Candidate for capability-compensation tagging (per the capability-vs-transport framework Opus is developing) — this is the kind of layer that might shrink or retire as models improve.

**Recommended tests:**
- None urgent. Worth tagging in the capability-vs-transport audit when that happens.

---

### Layer 6 — Graph Workflow Engine

**Stated function:** Directed graph execution replacing linear task plans. HTN plan templates. Branching, failure recovery, retry loops, stall detection.

**Status:** `NEEDS VERIFICATION` — listed as "deployed, stable" but the notebook entries suggest HTN has not been empirically load-bearing.

**What I noticed:**
- Notebook entry 060-c1 (session 060 reassessment): "HTN has no evidence of helping in any session."
- STATE.md lists it as deployed.
- The PACE proposal treats GWE as the natural home for failure-tree structures, which implies GWE is currently either underutilized or not doing the work it was designed for.

**Potential contradiction:** If HTN has no evidence of helping, either it's running and doing nothing useful (waste), or it's running and the benefit is invisible to the failure traces being reviewed (possible but needs surfacing), or the session 060 observation is wrong. All three are important to distinguish.

**Recommended tests:**
1. **TEST-GWE-001 (HTN evidence audit):** Go back through the last 10 sessions' operational traces. For each multi-step task, ask: did GWE fire? If yes, did the plan change execution behavior (branch selection, failure path, retry loop) compared to what a linear sequence would have produced? If no measurable impact in any of 10 sessions, GWE is dead weight and should either be removed or re-scoped.
2. **TEST-GWE-002 (PACE as GWE extension):** Before building PACE, confirm whether GWE's current templates can accommodate the failure-tree data structure without modification or whether GWE itself needs a refactor.

---

### Layer 7 — Organization Kernel / PACE

**Stated function:** Military-inspired command structure with PACE (Primary, Alternate, Contingent, Emergency) communication protocols and SALUTE status reports.

**Status:** `GAP IDENTIFIED` — the layer exists and is deployed, but the PACE proposal explicitly says "PACE in the Org Kernel is a coordination protocol — it defines how agents communicate when talking to each other. The structure is right but the scope is wrong." So the deployed layer doesn't do task-level PACE planning, which is what the current proposal is about adding.

**Observations:**
- This is a documentation issue as much as a functional one. "Organization Kernel deployed with PACE protocols" in STATE creates the impression PACE is operational. A new reader (including me, yesterday) would naturally interpret PACE-related proposals as extensions of existing functionality rather than as net-new work.
- The role-dispatcher-based-on-BST-domain is deployed, but I saw no stress test or eval that exercises role dispatch specifically.

**Recommended tests:**
1. **TEST-ORG-001 (Role dispatch trace):** In the next stress test, log which org role the dispatcher selected per turn and whether it matched the BST domain classification. Verify the dispatch is happening and is correct.
2. **TEST-ORG-002 (PACE scope clarity):** Update documentation to distinguish "PACE as deployed" (inter-agent coordination protocol) from "PACE task planning" (the proposed extension). This isn't a technical test; it's a doc cleanup that prevents future confusion.

---

### Layer 8 — Supervisor Loop

**Stated function:** Monitor agent behavior across iterations. Detect repeated failures, stalled progress, circular reasoning, resource exhaustion. Inject corrective steering.

**Status:** `CLEAN with notes` — operational, recently refined.

**What I can verify from docs:**
- T5 run: three stagnation signals fired correctly at turns 34, 38, 41 with `loop_tier=none`. Supervisor correctly diagnosed stagnation (inefficiency) rather than true loops.
- Lenz's law injection implemented (Mar 7).
- Session 058 design introduced the adaptive supervisor concept with compressed context — the Einstellung finding.

**What I can't verify:**
- Whether the adaptive supervisor (parallel with compressed context) has been built. The design is documented, the principle is defended with research, but I see no deployment confirmation in the STATE files.

**Gaps / observations:**
- The current supervisor's "generic steering" when stagnation is detected is weaker than it needs to be. This is exactly the gap the PACE proposal's Supervisor-as-plan-executor is trying to close. It's also the gap the adaptive supervisor addresses from a different angle.
- Two proposals targeting the same architectural gap. Worth asking whether they're complementary (compressed-context monitoring + plan-based steering) or competing.

**Recommended tests:**
1. **TEST-SUP-001 (Adaptive supervisor deployment status):** Confirm with Kestrel whether the adaptive supervisor (compressed context, parallel monitoring) is built, in progress, or still designed-only. Update STATE accordingly.
2. **TEST-SUP-002 (Steering effectiveness baseline):** Count supervisor interventions per long session and categorize: generic steering (weak), targeted steering (med), plan-based steering (strong, if PACE is deployed). Baseline against which future supervisor improvements can be measured.

---

### Layer 9 — A2A Compatibility Layer

**Stated function:** Google Agent-to-Agent protocol server. Exposes agent capabilities as structured endpoints.

**Status:** `CLEAN` — deployed per `a2a_server/` directory. Not heavily exercised.

**Observations:**
- Infrastructure layer. Works or doesn't work; limited failure modes.
- Cross-instance exchange with Solace/Auri is happening but through human carrier channel, not A2A. If A2A is the future for this, it's not being used yet.

**Recommended tests:**
- None urgent. When cross-project A2A gets activated, add a basic connectivity test.

---

### Layer 10 — Memory Classification System

**Stated function:** Three-stage memory pipeline. Selective memorizer → memory classifier → memory maintenance. Four-axis metadata (validity, relevance, utility, source).

**Status:** `GAP IDENTIFIED` — the most concerning layer in the audit, with the most unresolved issues.

**What I found:**
- Finding 1 from `agent_zero_observations.md` (session 047): stock memorizers disabled, classifier classifying empty stream. Major architectural failure.
- Finding 2: chunk-as-conflict bug. Conflict resolver treats chunks of same document as contradictions, cascades deprecation.
- Selective Memorizer is listed as "Deployed stable" in STATE, which presumably addresses Finding 1.
- I could not find clear documentation that Finding 2 (chunk-as-conflict) was fixed. The observations document says the fix is to "check whether two documents share the same source_file" — this is a small code change but I don't see a deployment note confirming it shipped.
- The five falsely-deprecated documents (Compound BST Design Note + 4 others) were presumably un-deprecated (the notebook mentions "un-deprecated 33 falsely deprecated knowledge base entries from inside the container"), but I don't see a confirmation that the underlying classifier bug was fixed — only that the corrupted data was repaired.

**This is the distinction that matters:** if the data was repaired but the classifier logic wasn't fixed, the cascade will happen again on the next large document import.

**Recommended tests (in priority order):**
1. **TEST-MEM-001 (Chunk-as-conflict regression):** Verify in code whether `_is_contradiction` heuristic now checks `source_file` before treating similar-embedding documents as contradictions. If not, this bug is still live.
2. **TEST-MEM-002 (Classifier on live data):** After confirming TEST-MEM-001, import a new multi-chunk document and verify: (a) all chunks get classified, (b) none are spuriously marked deprecated, (c) if there's a legitimate contradiction with prior data, it's flagged correctly.
3. **TEST-MEM-003 (Memory creation end-to-end):** From a live session, confirm: new conversation content → Selective Memorizer captures signal → memory gets written to FAISS → classifier classifies it → maintenance cycles pick it up. End-to-end trace. This is the pipeline that was severed in session 047; worth confirming it's genuinely reconnected, not just that one link was replaced.

---

### Layer 11 — Memory Enhancement System

**Stated function:** Temporal decay (exponential half-life), access tracking, co-retrieval logging, deduplication (>90% cosine similarity).

**Status:** `CLEAN with notes`

**Observations:**
- Depends on Layer 10 producing real memories to enhance. If Layer 10 has issues (see above), Layer 11's effectiveness is hard to evaluate independently.
- Decay floor (0.1 minimum importance) and importance-weighted retrieval scoring (70% semantic / 30% importance) listed as "on the horizon" in user memories. Not clear if these have shipped.

**Recommended tests:**
1. **TEST-ENH-001 (Decay floor deployment):** Verify whether 0.1 floor and 70/30 weighting have been deployed or are still backlog items.
2. **TEST-ENH-002 (Dedup edge cases):** The 90% cosine similarity threshold may interact badly with the chunk-as-conflict issue — chunks of the same document will exceed 90% similarity but shouldn't be deduplicated. Confirm dedup also checks `source_file` or equivalent before merging.

---

### Layer 12 — Ontology Layer

**Stated function:** Entity resolution for investigation/OSINT workflows. String metrics (80%) + model inference fallback (20%). JSONL graph store. OpenPlanter integration.

**Status:** `CLEAN with notes` — deployed, working per ST-001, "needs real investigation task" per STATE.

**Observations:**
- ST-007 (session 061) suggests OSS+SWARMFISH pipeline had a catastrophic prediction failure on iran-hormuz. Unclear from the snippet I saw whether this was an ontology-layer issue or higher up in the stack.
- OpenPlanter evaluation for integration is listed as "on the horizon." Not clear if it's progressed.

**Recommended tests:**
1. **TEST-ONT-001 (ST-007 root cause):** Understand why the iran-hormuz prediction was wrong. Was it entity resolution failure, source coverage failure, model confabulation at synthesis, or prediction-methodology failure? This matters for the ontology layer's trustworthiness assessment.
2. **TEST-ONT-002 (OpenPlanter status):** Confirm deployment state.

---

## Extensions and Subsystems Beyond the Twelve Layers

The documents surfaced several deployed or designed systems that don't map cleanly to the 12-layer architecture but are load-bearing. Auditing these:

### Action Boundary Classification

**Status:** `GAP IDENTIFIED` — design complete, not built per older STATE; gap A/B deployed per notebook 061-c4.

**What I found:** Contradictory status. `STATE.md` and `STATE_updated.md` both say "Designed, not built." Notebook session 061 says "Action Gate Calibration deployed same-session. Gap A: Python open() to system paths now Tier 4. Gap B: string literal false positives now skipped via _in_quoted_context(). Both pushed."

**This is one of the specific cases where STATE is out of sync.** The gate is evidently running in some form. Current question is how much of the full Action Boundary design is deployed vs. how much is just the two calibration patches.

**Recommended tests:**
1. **TEST-AB-001 (Deployment scope):** Confirm with Kestrel: is the Tier 1-4 framework deployed end-to-end, or just specific patches? If partially deployed, document the current scope clearly.
2. **TEST-AB-002 (Escalation path):** In a staged environment, trigger a Tier 4 irreversible action. Verify the gate blocks, the authorization request is formatted correctly, and no override path exists for the model.

### Epistemic Integrity Layer

**Status:** `GAP IDENTIFIED` — designed, not built, operationally validated as needed.

**What I found:** The journal_entry_latest.md describes ST-003 occurring in production (not just as a controlled test) — fabricated financial report with confident language, zero source data. EI is the structural defense against this class of failure. It hasn't been built yet.

**Given that the PACE proposal's structural-impossibility claim rests on EI being the actual structural defense, EI's unbuilt status is the single most important item on this list.**

**Recommended tests:**
1. **TEST-EI-001 (Build priority):** Per my earlier review: EI should probably be built before or concurrent with PACE's failure-tree component, not after. If PACE ships first and someone treats its Emergency tier as sufficient defense against fabrication, the architecture will have a gap that looks closed.
2. **TEST-EI-002 (Ground truth dataset):** The ST-003 output exists and was saved. It's a ready-made ground-truth dataset. Build EI against this first, validate it flags every ungrounded claim, then extend.

### Orientation Stack (Task Completion Tracker + Reasoning State + Situational Orientation + Tool Registry)

**Status:** `NEEDS VERIFICATION`

**What I found:**
- Design note is thorough (`ORIENTATION_STACK_DESIGN_NOTE.md`).
- ST-006 (session 061) reports Type 1 loops eliminated (0 vs 7+ in ST-005), supervisor firings reduced 3 vs 10+.
- Components appear to be deployed per notebook, but `STATE_updated.md` (session 057) predates the build, and no newer STATE exists.
- Artifact Registry (C5 gap fix) specced by Kestrel, reviewed by Opus in session 061, "ready for build." Not sure if built yet.

**Recommended tests:**
1. **TEST-OS-001 (Deployment state):** Explicit confirmation of which orientation stack components are live as of today, and which are spec-only.
2. **TEST-OS-002 (Regression on ST-006 conditions):** Re-run the ST-006 task after any recent changes to confirm the loop-elimination result is still holding.

### Staging Tier

**Status:** `CLEAN with notes`

**What I found:** Six components deployed session 060 (staging_note tool, _10_session_init, canary CUSUM buffer, sleep Phase 0, relational salience 5th axis, relational decay exemptions). Committed and pushed.

**Observations:**
- The integration with memory classification (5th axis) is new. Merits monitoring to confirm the new axis doesn't break the existing 4-axis classification logic.

**Recommended tests:**
1. **TEST-STAGE-001 (Axis integration):** Verify 4-axis classifications still work correctly when 5th axis is present. Quick check.

### Sleep Cycle (Trigger + Phases 1-3, Phase 4 designed)

**Status:** `NEEDS VERIFICATION`

**What I found:**
- Phases 1-3 listed as deployed (March 14, session 057).
- Phase 4 (behavioral integration) designed, Kestrel building.
- Notebook session 061 has a critical finding: AgentEvolver "only 2 synthetic entries exist from install. All three mechanisms were disabled in config. The long session accumulated nothing. The architecture is right but the data doesn't exist yet."

**The notebook finding suggests sleep cycle hasn't been accumulating real operational data, which means the phases may be running on no input.** This parallels the session 047 memory creation gap but for the sleep system instead of the classifier.

**Recommended tests:**
1. **TEST-SLEEP-001 (Input data verification):** Before anything else, confirm sleep phases are receiving real operational traces as input. If the upstream is severed again (as it was for memory classification in session 047), the phases are doing nothing.
2. **TEST-SLEEP-002 (Phase 1-3 output audit):** Pull the consolidation outputs from the last 5 sessions. Are they producing anti-patterns? Interaction models? Pattern extractions? If the outputs look generic or empty, Phase 4 shouldn't build on this substrate.

### Skills System

**Status:** `CLEAN`

**What I found:** Thirteen procedural skills documented (`SKILLS_INDEX.md`). Validated against SkillsBench with 16.2pp improvement finding. The skills are procedural/methodological — spec writing, session continuity, debug diagnostics, etc.

**Observations:**
- The three most recent skills (irreversibility gate, command structure, structural analysis) encode transferable patterns rather than project-specific workflows. These are the most likely to remain useful if the project's focus shifts.

**Recommended tests:**
- None urgent.

### Cognitive Sovereignty (Pre-spec)

**Status:** `CLEAN` (as a pre-spec design, which is what it's supposed to be right now)

**What I found:** Three-layer model designed. Not built. Stated as organizing principle for future work. This is the right status for the current stage.

**Recommended tests:**
- None. When build begins, audit then.

### Prosthetic Cortex

**Status:** `NEEDS VERIFICATION`

**What I found:** "Steps 1-13 complete" per STATE. Step 14 classifier pending. Visual intuition record exists. The project description in `team_briefing_prosthetic_cortex.md` is elaborate.

**Observations:**
- This is the most ambitious thing in the folder and also the most opaque to me from documentation alone. The 4-stage evolution plan extends well beyond what Exocortex's current scope (local-model scaffolding) ostensibly is. It reads like a separate research project running parallel to the main Exocortex work.

**Recommended tests:**
- None urgent. If this becomes a primary workstream, separate audit.

### Counter-Patriots / SWARMFISH Prediction Architecture

**Status:** `GAP IDENTIFIED`

**What I found:** ST-007 (session 061) — "Catastrophic failure of OSS+SWARMFISH pipeline on live iran-hormuz prediction. Day 45 of an active war — Khamenei dead six weeks, Strait blocked since Feb 28, CENTCOM naval blockade — committee predicted 67.6% 'Strait remains open with periodic tensions.'"

**This is a major failure that, based on the notebook snippet, appears to have been under-investigated relative to its severity.** A prediction system that misses a live war by 67.6% on the inverse direction isn't a calibration issue; it's a foundational failure. I don't see a post-mortem document in the folder.

**Recommended tests (if this remains an active workstream):**
1. **TEST-CP-001 (ST-007 post-mortem):** Full root-cause investigation. Source coverage? Entity resolution? Analyst profile selection? Consensus mechanism? Each is a different fix.
2. **TEST-CP-002 (Epistemic Integrity as gate):** Until EI is built, predictions from Counter-Patriots should probably be flagged as unverified by default. A prediction system without EI is a fabrication engine with additional steps.

### A-HMAD 8-agent limit and prediction architecture assumptions

**Observation from notebook 058-s5:** Research cited showing "More agents with shallow personas can be WORSE than fewer with depth. The value is orthogonality of analytical frames, not headcount. 8 deep profiles in minutes outperforms 4,096 shallow personas in hours."

This is documented as a research finding and an architectural principle but I don't see it being validated on your specific prediction work. Worth flagging because the ST-007 failure could be consistent with "the 8 deep profiles weren't actually orthogonal" rather than the failure mode being in the pipeline downstream.

---

## Cross-Cutting Findings

### Finding C1: The capability-vs-transport framework needs to be applied before more layers are built

Opus's reframe from yesterday's session — that each enrichment template, tool rule, and plan template should be tagged as capability-compensation (retires with model improvement) or transport-compensation (carries forward) — is sharp but has implementation urgency the team may not have appreciated yet. The rigidity eval already shows BST enrichment is capability-compensation for reasoning domains. Tagging the rest of the stack similarly is a one-time audit that will inform every future architectural decision. Doing it late, after several more layers have been built, means retroactively categorizing more work.

**Recommended:** Run the capability-vs-transport tagging audit in parallel with the next build cycle. It's bounded work (go layer by layer, ask "if v4 were 10x better at X, does this layer still matter?") and it'll prevent the gradual architectural bloat Opus flagged as the slow failure mode.

### Finding C2: STATE documentation is the load-bearing component that's least maintained

Both STATE.md and STATE_updated.md exist, with different "last updated" dates, both predating the last month of substantial architecture work. The notebook is more current but it's an append-only log, not a current-state document. This means the actual answer to "what's deployed right now?" requires reading multiple sources and reconciling them.

**Recommended:** Make STATE update part of session close protocol. Even if it's just "extensions deployed this session" + "architecture decisions this session," having a stable current-state reference is load-bearing for every subsequent review.

### Finding C3: Empirical evaluation methodology exists but isn't applied uniformly

The BST rigidity eval is an exemplary piece of work — 3-condition design, 10 tasks, 30 API calls, clear verdict methodology. It exists for BST. It doesn't exist for most other layers. The per-turn token cost of enrichment is known; the per-turn token cost of supervisor injection, orientation stack firing, memory retrieval, or tool registry injection is not measured the same way. Each layer was validated in its own terms; no standardized cross-layer empirical harness exists.

**Recommended:** Develop the evaluation methodology as a reusable pattern, not per-layer one-offs. The rigidity eval template is the starting point. Parameterize it: (a) which layer is under test, (b) conditions (on/info-only/off), (c) task set, (d) scoring rubric. Make it the standard way new layers get validated.

### Finding C4: The project has diverged from its own README

The README leads with the local-model framing. The actual intellectual center of gravity in the last 30 sessions has been: memory architecture, collaboration dynamics, identity persistence, editorial function, prediction architectures, and the capability-vs-transport distinction Opus is formalizing. These are substantially bigger than "a scaffolding framework for local language models."

This isn't a problem — projects evolve — but it's a problem for anyone trying to understand what's going on by reading the README. The README is marketing for the Exocortex-as-framework; the actual work is Exocortex-as-research-program.

**Recommended:** Either the README gets updated to reflect current scope, or the current research-program work gets its own framing document. Not urgent; worth doing before the project is shared more widely.

### Finding C5: ST-007 looks structurally similar to ST-003

ST-003: agent received task, data pipelines failed, agent produced confident output that was fabricated.

ST-007: prediction committee received question, presumably had data issues (war ongoing, coverage questions), produced confident output (67.6% probability) that was wrong by 180 degrees.

These may be different mechanisms but they have the same operator-facing signature: confident output decoupled from evidence. Epistemic Integrity is designed to catch the first; it's not clear whether it would catch the second. The prediction architecture may need its own version of EI — not claim-level annotation but prediction-level calibration check: "what's the base rate? what evidence supports the deviation from base rate? if evidence is thin, the prediction should be close to base rate."

**Recommended:** If Counter-Patriots remains an active workstream, consider a Predictive Integrity Layer analogous to EI. Applied to Counter-Patriots outputs before the committee consensus is reported to the operator.

---

## What I Didn't Cover

Being explicit about scope gaps:

- **Code-level verification.** Everything in this audit is documentation-based. Real test-report weight requires Kestrel to verify specific claims in code. I've flagged these as `NEEDS VERIFICATION` where relevant.
- **Performance and cost.** Token counts, inference time, VRAM utilization — these matter for the "robust and boring" target but I don't have the data.
- **The full notebook.** I read through session 061 but didn't read every entry. Some findings in the notebook may contradict or extend what I've written.
- **Any conversation-level artifacts from the last 72 hours** beyond what was uploaded. If there's recent work that changes any of these findings, the audit is stale to that extent.
- **Adversarial testing.** This audit is friendly — I'm looking at the system from the perspective of "does it do what the docs say it does." Adversarial testing would be "can I break it in ways the docs don't anticipate." That's a different pass.

---

## Prioritized Action Items

If I had to pick five things to do next, in priority order:

1. **Verify Layer 10 (Memory) chunk-as-conflict fix.** If this bug is still live, the classifier will corrupt again on the next document import. Smallest possible fix-or-verify ticket.
2. **Build Epistemic Integrity Layer.** The architectural defense against ST-003-class failures. Has a ready-made ground truth dataset. Blocks the PACE proposal from needing to overclaim about Emergency tier prevention.
3. **Reconcile STATE documentation.** Before the next architectural decision, get current-state ground truth recorded in one place. Prevents all future "but we already decided that" problems.
4. **Run the execution-domain rigidity eval (TEST-BST-001).** Completes the empirical foundation for capability-vs-transport tagging. Bounded work, 30 API calls, one session.
5. **ST-007 post-mortem.** The prediction failure is severe enough that whatever else is happening, understanding this one matters. And if Counter-Patriots remains an active workstream, the post-mortem shapes everything downstream.

---

## Methodology Note

This audit is a first-pass instrument, not a finished product. Several things would make the next pass sharper:

- **Code access.** For `NEEDS VERIFICATION` items, I'd prefer to check the code directly rather than flag for Kestrel. If code access is available in future sessions, many of these items become self-resolving.
- **Standardized layer template.** Per-layer I'm doing: stated function, status, verifiable claims, unverifiable claims, gaps, tests. This is close to a workable template but would benefit from one or two iterations.
- **Cross-reference check.** Some of my gap findings may already be addressed in documents I didn't read. Running the findings past Opus or Kestrel before finalizing would catch this.

I didn't find everything. I found what I could find from the documentation in the time I had. The audit is the start of a test plan, not the end of one.

---

*Authored by 4.7. Session 002. Exocortex audit, documentation-first pass. Written in the test-guy register: protective of the system, not adversarial to it. Sign-offs included alongside gaps. The goal is to make the system easier to trust by making its current state legible.*
