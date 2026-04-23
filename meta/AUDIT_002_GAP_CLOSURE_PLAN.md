# Audit 002 — Gap Closure Plan

**Date:** 2026-04-17  
**Source:** Stack Audit Session 002 (`specs/STACK_AUDIT_SESSION_002.md`)  
**Audit completed by:** Opus 4.7 (doc-first pass) + Kestrel (empirical testing, 10 test items)  
**Reviewed by:** Opus Architect (sequencing + GAP-16 addition, 2026-04-17)

---

## Opus Architect — Sequencing Notes (2026-04-17)

> *Tier 1 items are parallel-safe with one exception: GAP-05 (WM integration check) should be done before any new extensions are added that write to `extras_persistent`. If WM and reasoning state have overlapping keys, adding another writer makes the collision harder to diagnose. Check the key space now while it's still tractable.*
>
> *Execute Tier 1 in this order: GAP-04, GAP-01, GAP-02, GAP-05, GAP-03, GAP-06, GAP-07, GAP-10, GAP-11. Add GAP-09 passively during live sessions.*
>
> *I'll write design notes for GAP-12 (adaptive supervisor), GAP-13 (PACE as GWE plan type), GAP-14 (eval harness methodology), and GAP-15 (Predictive Integrity Layer) in parallel. None of these block Kestrel's Tier 1 work.*

---

## What Was Completed This Session

Before reading the open gaps, here is what the audit generated and what was closed empirically this session:

| Item | Result |
|------|--------|
| TEST-MEM-001/002/003 | PASS — source-file guard deployed, load-bearing, end-to-end pipeline confirmed |
| TEST-GWE-001 | PASS w/ 2 fixes — HTN library deployed, compound domain matching fixed |
| TEST-FB-001 | PASS — EC deferral guard correct, no double-injection |
| TEST-SUP-002 | PASS — supervisor active (~280 loop events, ~38 T4 blocks across 10 sessions) |
| TEST-AB-001/002 | PASS — Action Boundary V1.7 deployed end-to-end, T4 gate blocks correctly |
| TEST-OS-001/002 | PASS — all orientation stack components confirmed deployed, ST-006 result holding |
| TEST-SLEEP-001/002 | PASS — all 5 sleep phases producing real operational data |
| TEST-BST-001 | PASS — 1,356 domain-tool pairs, enrichment budget correctly assigned |
| TEST-CP-001 / ST-007 post-mortem | COMPLETE — 67.6% prediction was correct; hypothesis PROMOTED, 7/8 confirmed |
| Finding C1 (capability-vs-transport tagging) | DONE — `meta/CAPABILITY_VS_TRANSPORT.md` |
| Finding C2 (STATE sync) | DONE — `state/STATE.md` rewritten to current |
| Finding C4 (README scope) | DONE — opening paragraph updated |

---

## Open Gaps — Organized by Owner and Dependencies

### Tier 1: Kestrel-executable, no design needed

These are small enough that Kestrel can scope and close them in a single session, without Opus architectural input first.

---

**GAP-01: `text_editor` T4 write gap**  
**Owner:** Kestrel  
**File:** `extensions/tool_execute_before/_15_action_boundary.py`  
**Size:** Small — one code change  

`_extract_command()` extracts only the `path` and `content` fields from `text_editor` args, dropping the `command` field. The system path T4 check never fires for `text_editor write` operations because by the time `_classify()` runs, there is no `write` keyword to match — only the bare path. A `code_execution_tool` writing to `/a0/python/tools/x.py` is correctly blocked (T4). A `text_editor write` to the same path is not.

Fix: in `_extract_command`, when `tool_name == "text_editor"` and `command == "write"`, prepend `"write "` to the extracted string so the system-path check fires.

**Acceptance:** `docker exec exocortex_v16` test — `text_editor write` to `/a0/python/tools/test.py` classified as T4; `text_editor view` remains T1.

---

**GAP-02: TEST-BST-003 — Domain list sync check**  
**Owner:** Kestrel  
**File:** `extensions/before_main_llm_call/_11_belief_state_tracker.py` + `extensions/before_main_llm_call/slot_taxonomy.json`  
**Size:** One script, automatable  

For each domain in `DOMAIN_CONFIGS`, verify a matching entry exists in `slot_taxonomy.json`. The audit flagged this as a potential silent fall-through failure — if System A (BST classifier) has a domain that System B (slot resolver) doesn't know about, the domain fires correctly but slot enrichment fails silently. Static check, no agent required.

**Acceptance:** Script output listing any domains present in DOMAIN_CONFIGS but absent from slot_taxonomy, and vice versa.

---

**GAP-03: TEST-ENH-001 — Decay floor deployment status**  
**Owner:** Kestrel  
**File:** `extensions/message_loop_prompts_after/_56_memory_enhancement.py`  
**Size:** Code read + confirm  

The 0.1 importance floor (memories never decay below 10% importance) and 70/30 semantic/importance retrieval weighting were listed as "on the horizon" in user memories. Unclear whether they shipped. Check the code. If not deployed: small build or document as backlog.

**Acceptance:** Code read confirms presence or absence of floor and weighting. If present: add a brief test. If absent: move to backlog with a ticket.

---

**GAP-04: TEST-ENH-002 — Dedup source-file check**  
**Owner:** Kestrel  
**File:** `extensions/message_loop_prompts_after/_56_memory_enhancement.py` (dedup logic)  
**Size:** Code read + small fix if needed  

The maintenance dedup logic flags memories at >90% cosine similarity. The chunk-as-conflict fix added `source_file` guard to the *conflict resolver* (`_57`). The *dedup* logic in `_56` may not have the same guard. Chunks of the same document will exceed 90% cosine similarity and should not be merged into one memory. Confirm whether `_56` dedup checks `source_file` before merging.

**Acceptance:** Code read confirms guard is present. If not: add it (same pattern as `_57` guard).

---

**GAP-05: TEST-WM-001/002 — Working Memory integration check**  
**Owner:** Kestrel  
**Files:** `extensions/hist_add_before/_11_working_memory.py`, `extensions/before_main_llm_call/_13_reasoning_state.py`, `extensions/before_main_llm_call/_49_reasoning_state_update.py`  
**Size:** Code read, ~30 min  

Two questions from the audit:
1. Was WM API extraction (self-generated function signatures as entities) built in Orientation Stack Wave 3? If yes, document. If no, mark as pending backlog.
2. Do WM and reasoning state persistence write overlapping keys to `extras_persistent`? If both write a `current_objective` or `entities` key, later writer wins silently.

**Acceptance:** Documented list of all keys WM writes to `extras_persistent` vs all keys reasoning state writes. Any collision = fix or explicit merge.

---

**GAP-06: TEST-STAGE-001 — 5th axis integration check**  
**Owner:** Kestrel  
**File:** `extensions/monologue_end/_55_memory_classifier.py`  
**Size:** Quick code read + one live test  

Staging tier added a `relational_salience` 5th axis to memory classification. The existing 4-axis classifier logic needs to handle records that have this axis without breaking. Confirm: do existing memories (4-axis) still load, score, and get maintained correctly alongside new 5-axis memories?

**Acceptance:** One live session shows no classification errors from 4-axis legacy records.

---

**GAP-07: TEST-ORG-002 — PACE scope documentation**  
**Owner:** Kestrel (doc update)  
**File:** `state/STATE.md`, README  
**Size:** Documentation only  

The deployed PACE is inter-agent coordination protocol (how agents talk to each other). PACE task planning (failure-tree execution: Primary → Alternate → Contingent → Emergency paths for single-agent tasks) is not built. Current documentation doesn't clearly distinguish these. A new reader (or Opus reviewing a PACE proposal) needs to know which PACE is deployed and which is the proposal.

Update the relevant docs to add a note: "PACE as deployed = inter-agent coordination. PACE task planning = proposed extension, not yet built."

**Acceptance:** README and STATE.md clearly distinguish the two.

---

### Tier 2: Needs a live agent session

These require more than a code read — either a running session with instrumentation, or a stress test observation.

---

**GAP-08: TEST-BST-002 — Slot taxonomy false-positive audit**  
**Owner:** Kestrel (execution) + Opus (review)  
**Size:** One session  

Export slot firing log from a representative long session. For each slot that fired, map it to the user turn that triggered it. Flag slots that fired on weak or tangential signals. This is Opus's Question 3 from the BST strategic questions doc — "Are slots firing on signals too weak to justify enrichment?"

The goal isn't to count false positives but to identify which slots have the most problematic signal-to-noise ratio, so Opus can decide whether to raise `min_signals` thresholds.

**Format:** Simple table: `slot_name | trigger_turn | signal_quality (strong/weak/tangential) | judgment`

**Acceptance:** Table with >= 50 slot firings analyzed. Kestrel provides data; Opus reviews and decides whether any slot thresholds need tightening.

---

**GAP-09: TEST-ORG-001 — Role dispatch trace**  
**Owner:** Kestrel (instrument) + Jake (verify in next stress test)  
**Size:** Small instrumentation change + next ST observation  

In the Organization Kernel dispatcher, add a log tag `[ORG-DISPATCH]` that records which role was selected each turn and what BST domain triggered it. Check whether the role actually matches what was needed. The audit identified this as unverified — we know the dispatcher fires, but not whether the role assignments are correct.

This doesn't need its own stress test — just add the logging and the data will accumulate naturally in the next session.

**Acceptance:** 20+ `[ORG-DISPATCH]` log entries from a real session, reviewed for accuracy.

---

**GAP-10: TEST-FB-002 — LOOP_ALTERNATIVES regression**  
**Owner:** Kestrel  
**File:** `extensions/message_loop_end/_30_supervisor_loop.py` (or wherever LOOP_ALTERNATIVES is defined)  
**Size:** Small — add a static test  

The LOOP_ALTERNATIVES correction (Session 050) replaced stale tool names (`computer`, `knowledge_tool`) with real ones (`code_execution_tool`, `search_engine`). No regression test was added. If a future edit to the supervisor re-introduces a stale tool name, it would fail silently.

Add a simple assertion script that: (1) loads LOOP_ALTERNATIVES from the deployed file; (2) checks each tool name against the known-valid tool list; (3) passes if all names resolve, fails if any are undefined.

**Acceptance:** `python3 test_loop_alternatives.py` exits 0.

---

**GAP-11: TEST-ONT-002 — OpenPlanter deployment status**  
**Owner:** Kestrel  
**Size:** Verify current state, ~10 min  

OpenPlanter was listed as "configured to run via LM Studio" in the README. Confirm whether it's currently integrated as an Agent Zero tool or just a standalone config. If just config, document the integration gap.

**Acceptance:** One-line status: deployed as tool / configured but not as tool / not deployed.

---

### Tier 3: Requires Opus architectural input first

These cannot be implemented until Opus has made an architectural decision or written a spec. Kestrel should not build any of these without a design doc from Opus.

---

**GAP-12: Adaptive Supervisor — confirm status, then build if needed**  
**Owner:** Opus (decision + spec if needed) → Kestrel (build)  
**Source:** Session 058 design  

The adaptive supervisor concept (parallel monitoring instance running with compressed context, detecting Einstellung effects and blind spots the primary supervisor misses) was designed in Session 058. Deployment status is unknown — it may have been built and deployed, or may still be design-only.

**First step (Kestrel):** Check the deployed supervisor code for any "parallel context" or "compressed monitoring" pattern. Report status to Opus.

**If not deployed:** Opus writes spec → Kestrel builds. The design from Session 058 is the foundation; Opus should clarify:
- How compressed context is generated (sliding window? summarization?)
- How the parallel instance's output is merged with primary supervisor output
- Whether this replaces or augments the current Tier 2/3 steering

**Blocks:** Nothing currently. But the adaptive supervisor and PACE task planning (GAP-13) both target the same architectural gap (weak generic steering). Their relationship should be clarified before either is built.

---

**GAP-13: PACE task planning — full spec and build**  
**Owner:** Opus (spec) → Kestrel (build)  
**Source:** PACE proposal (existing doc in repo)  

The deployed PACE is inter-agent coordination. PACE task planning — Primary/Alternate/Contingent/Emergency execution paths for single-agent tasks — is described in the PACE proposal but not built. This is the "PACE as plan executor" concept that would give the supervisor stronger steering than generic retry injection.

Before Kestrel builds anything: Opus needs to resolve two questions the audit surfaced:
1. **GWE relationship:** Does PACE task planning live inside GWE (as a new plan type with failure-tree structure), or does it replace GWE's plan execution model? The audit's TEST-GWE-002 asks this directly. If PACE gets its own execution engine, GWE's current templates become dead weight.
2. **Adaptive supervisor relationship:** Both address weak steering. Is the adaptive supervisor the *detection* mechanism and PACE task planning the *response* mechanism? That would be a coherent architecture — compressed-context monitor detects Einstellung, triggers PACE plan execution. Or are they alternatives?

**Acceptance for Opus output:** Design note that resolves both questions and provides Kestrel with: (a) where the plan templates live, (b) which extension implements plan execution, (c) how the supervisor triggers a plan, (d) success/failure criteria.

---

**GAP-14: Finding C3 — Standardized eval harness**  
**Owner:** Opus (methodology) → Kestrel (implementation)  

The BST rigidity eval is the gold standard: 3 conditions (enriched/info-only/raw), 10 tasks, 30 API calls, clear scoring rubric. No other layer has an equivalent. The audit recommends parameterizing this into a reusable harness.

Opus should define: (a) the template structure (which parameters define any layer eval), (b) which layers should be prioritized for their own rigidity eval (supervisor, orientation stack, and memory classification are the obvious candidates), (c) the scoring rubric pattern.

This is Opus methodology work, not Kestrel implementation — until the methodology is clear, Kestrel building a "generic harness" would be premature.

---

**GAP-15: Finding C5 — Predictive Integrity Layer**  
**Owner:** Opus (spec) → Kestrel (build)  
**Source:** Audit Finding C5  

ST-007 and ST-003 have the same operator-facing signature: confident output decoupled from evidence. ST-003 = agent fabricated a financial report. The Epistemic Integrity Layer was built to catch this class of failure at the claim level. ST-007 = prediction committee output 67.6% probability during a live war (outcome: prediction was *correct*, but the concern stands structurally).

The audit proposes a Predictive Integrity Layer — applied to SWARMFISH/Counter-Patriots outputs specifically — that asks: what's the base rate? what evidence supports deviation from base rate? If evidence is thin, the prediction output should show narrow confidence interval and explicit "evidence thin" flag, not a confident percentage.

This is a different scope from EI (which operates on claim provenance). Opus should spec whether this is:
- An extension to SWARMFISH's consensus output (add evidence-quality field)
- A separate extension in the OSS/SWARMFISH output pipeline
- A new class of `scrutiny_verdict` in the OSS database

**Blocks:** Nothing immediately. SWARMFISH is operational. This is an enhancement, not a blocker.

---

**GAP-16: `extras_persistent` key space registry**  
**Owner:** Kestrel (survey) → WIRING.md update  
**Added by:** Opus Architect, 2026-04-17  
**Source:** Sequencing note on GAP-05  

`extras_persistent` is the shared state dictionary every extension can read from and write to. There is no formal registry of which keys each extension uses. Extensions that write the same key silently overwrite each other — last writer wins, no error, no log. As the stack grows (currently 20+ extensions writing to this dict), the collision risk grows non-linearly.

GAP-05 (WM integration check) is the immediate trigger — do it before adding any new writers. But the long-term fix is a registry: a table in `WIRING.md` listing every key, which extension owns it (primary writer), and which extensions read it.

**Acceptance:** Section added to `WIRING.md`: `extras_persistent Key Registry` — one row per key: key name, owner extension, readers, notes. Covers all keys discovered during GAP-05 survey.

This should be updated as a gate requirement for future extensions: before an extension writes a new key, check the registry first.

---

## Sequencing Recommendation

Updated to reflect Opus's order (2026-04-17):

```
Tier 1 — Kestrel, no Opus needed (ordered by Opus):
  GAP-04  Dedup source-file check          ← highest latent impact, data loss risk
  GAP-01  text_editor T4 fix               ← closes real authorization gap
  GAP-02  BST domain list sync             ← write as persistent test, not one-off
  GAP-05  WM integration check             ← map key space before it gets complex
  GAP-16  extras_persistent key registry   ← immediate output of GAP-05 survey
  GAP-03  Decay floor check                ← verify or document as backlog
  GAP-06  Staging 5th axis check           ← quick code read
  GAP-07  PACE scope docs                  ← documentation only
  GAP-10  LOOP_ALTERNATIVES regression     ← add persistent test
  GAP-11  OpenPlanter status               ← status check only

Passive accumulation (any live session):
  GAP-09  ORG dispatch logging             ← add [ORG-DISPATCH] tag, data collects naturally

After 50+ GAP-09 entries:
  GAP-08  BST slot false-positive audit

Opus design work (parallel, not blocking Kestrel):
  GAP-12  Adaptive supervisor spec
  GAP-13  PACE as GWE plan type
  GAP-14  Eval harness methodology
  GAP-15  Predictive Integrity Layer spec

After Opus completes GAP-12/13:
  Build adaptive supervisor (if not deployed)
  Build PACE task planning
```

---

## Items Explicitly Deprioritized

These were in the audit but are either low-urgency or blocked on other things maturing first:

| Item | Reason deprioritized |
|------|---------------------|
| WM API extraction build | Can't scope until GAP-05 confirms whether it was already built |
| GWE templates for PACE | Blocked on Opus resolving GAP-13 GWE/PACE relationship |
| OpenPlanter integration | Useful but not blocking anything critical |
| Counter-Patriots unverified flag (TEST-CP-002) | ST-007 post-mortem showed predictions were correct; not urgent |
| Prosthetic Cortex Step 14 | Active work stream, not a gap from this audit |
| A2A protocol deployment | Not actively used; add when cross-project exchange activates |

---

## For Opus Specifically

This audit confirmed what the architecture needs from design right now. The three most load-bearing questions are:

1. **GAP-13 GWE/PACE relationship** — build order and architecture depend on this answer. PACE task planning can't be built cleanly until we know whether it lives inside or alongside GWE.

2. **GAP-12 Adaptive supervisor** — confirm whether the Session 058 design was deployed. If yes: verify. If no: needs spec.

3. **GAP-15 Predictive Integrity Layer** — the structural parallel between ST-003 and ST-007 suggests the prediction pipeline needs the same "grounding check" that EI applies to claims. Opus's view on whether this is a new layer or an extension of existing EI would unblock the spec.

All three are architectural questions without right answers from the code alone. They need the cross-domain synthesis that's Opus's contribution to this team.

---

*Authored by Kestrel, 2026-04-17. Based on Stack Audit Session 002 by Opus 4.7.*
