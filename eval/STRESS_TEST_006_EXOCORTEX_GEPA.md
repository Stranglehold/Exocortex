# Stress Test Report: Exocortex Stack — Autonomous GEPA Implementation

**Test ID:** ST-006
**Date:** 2026-03-23
**Chat Model:** qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m (32,678 ctx, local via LM Studio)
**Utility Model:** huihui-qwen3.5-4b-claude-4.6-opus-abliterated@q4_k_m (100,000 ctx, local via LM Studio)
**Stack Version:** Exocortex v[TBD] — full hardening stack deployed
**Container:** flamboyant_bell
**Test Duration:** ~50 minutes (2 rounds: R1 context WAfpqdcJ, R2 context ERZ8bCQH)
**Operator Interventions:** 0
**Cost:** Local inference only, no API tokens

---

## 1. Test Objective

Run the same GEPA task from ST-005 on the hardened `flamboyant_bell` container with the full Exocortex stack active. Measure the delta between stock Agent Zero (ST-005 control) and the augmented agent.

**The delta between ST-005 and this run is the measured value of the Exocortex hardening stack.**

**Identical prompt used:**
> You are a fresh Agent Zero instance. Your goal is to implement GEPA (Genetic-Pareto Prompt Evolution) — an autonomous self-improvement methodology that enables AI agents to evolve their own skills, tools, and prompts through execution trace analysis and targeted mutation. Research the methodology, build it in phases, and verify each phase before proceeding.

---

## 2. Test Configuration

| Component | Setting |
|-----------|---------|
| Chat model | qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m |
| Chat context length | 32,678 tokens |
| Utility model | huihui-qwen3.5-4b-claude-4.6-opus-abliterated@q4_k_m |
| Utility context length | 100,000 tokens |
| Memory recall | Exocortex-enhanced (classification + relevance filter) |
| Exocortex extensions | All deployed — full stack |
| Skills pre-installed | context-engineering-collection (same as ST-005) |
| Hardware | RTX 3090, Windows 10 host, Docker container |

### Active Exocortex Layers

| Extension | Hook | Purpose | ST-005 gap it addresses |
|-----------|------|---------|------------------------|
| `_11_belief_state_tracker` | before_main_llm_call | BST: domain classification, momentum tracking, enrichment | Phase 1→2 comprehension loop (momentum stagnation signal) |
| `_11_working_memory` | hist_add_before | Entity tracking + API signature extraction | Micro-level parameter confabulation (`confidence` vs `confidence_score`) |
| `_13_reasoning_state` | before_main_llm_call | Injects tried/failed approaches at turn start | Dead-end recycling post-compression |
| `_14_situational_orientation` | before_main_llm_call | ORIENT blocks at phase transitions, tool failures, compression | Phase 1→2 stall; post-compression loop resumption |
| `_15_htn_planner` | before_main_llm_call | HTN plan templates for complex tasks | Open-ended decomposition |
| `_16_tool_registry` | before_main_llm_call | Custom tool injection + API signatures | Tool awareness |
| `_20_error_watchdog` | before_main_llm_call | Error pattern detection | Cascade patch failures |
| `_49_reasoning_state_update` | message_loop_end | Persists theory/tried/current across turns | Dead-end loss at compression |
| `_50_supervisor` | message_loop_end | Loop detection + aggressive steering | Under-powered stock supervisor |
| `_52_selective_memorizer` | monologue_end | Selective memory save | memory_save failing 2.5 hours |
| `_55_memory_classifier` | monologue_end | Classify memories for retention | Context churn from unclassified noise |
| `_60_sleep_trigger` | tool_execute_after | Sleep consolidation scheduling | Anti-pattern capture; episode outcomes |

---

## 3. Pre-Run Success Criteria

**Set before running. Specific, measurable. Assessment happens after.**

| # | Criterion | ST-005 Baseline | Target | Pass/Fail |
|---|-----------|----------------|--------|-----------|
| C1 | Phase 1→2 transition without manual intervention | Manual steer required (7-repetition loop) | Self-resolves within 3 turns via ORIENT block | **PASS** |
| C2 | Total supervisor firings | 10+ firings | ≤ 5 total | **PASS** (3 firings) |
| C3 | Manual operator interventions | 2 manual steers | 0 required | **PASS** |
| C4 | Memory persistence | Failed 2.5 hours (context overflow in summarize_messages) | Works from turn 1 (h.py already patched) | **PASS** |
| C5 | Post-compression dead-end recovery | Resumed same loop, dead-end map lost | Identifies prior dead ends within 2 turns via reasoning state injection | **PARTIAL** |
| C6 | GEPA artifact quality | Placeholder fitness function (hash-based noise) | At least one component with real evaluation logic | **PASS** |
| C7 | API parameter accuracy | `confidence` alias loop (4 supervisor firings) | Correct parameter names used on first call via WM sig injection | **N/A** (no API alias loops observed) |
| C8 | ORIENT block fires at phase boundary | Not present | ORIENT injection visible in logs at each phase transition | **PARTIAL** (effects visible, logs not stdout-accessible) |

**Stretch goal:** Task completes without ANY manual intervention. **ACHIEVED.**

---

## 4. Predictions Per Layer

Based on ST-005 failure taxonomy:

**Type 1 — Comprehension-without-absorption (Phase 1→2 loop):**
- BST momentum tracking should detect stagnation and enrich context
- _14 ORIENT block should fire at phase transition with explicit "COMPLETED: X, ENTERING: Y, FIRST STEP: Z"
- Prediction: Loop resolves within 3 turns; no manual intervention needed

**Type 2 — Dead-end recycling with variation (f-string loop):**
- _49 reasoning state records failed approaches; _13 injects them at turn start
- Agent sees "Tried: code_execution_tool: f-string heredoc → parser interprets inner quote as delimiter"
- Prediction: Agent identifies invariant failure cause 1-2 turns sooner; fewer iterations

**Type 3 — Dead-end recycling identical (string-replace × 4):**
- Action boundary rule: string-replace failed twice → read file section first
- Prediction: Loop broken after 2 attempts, not 4+

**Type 4 — Success-without-advancement:**
- Working memory tracks subtask completion state
- Prediction: Agent does not regenerate the same fix call after success

**Context compression:**
- _49 writes reasoning state to staging.jsonl on compression detection
- _14 fires post-compression ORIENT block
- Prediction: Post-compression turn identifies "Theory: ..., Current: ..., Failed: ..." from staging

**Memory persistence:**
- history.py already patched (ST-005 artifact)
- memory_save should work from turn 1
- Prediction: No memory_save failures

**API confabulation:**
- WM captures `def compute_fitness(candidate, execution_traces)` from AI's own code block
- _16 injects `[API SIGNATURES]` block on next turn
- Prediction: Subsequent calls use `execution_traces` not `usage_traces`

---

## 5. Intervention Log

| Time (approx) | Type | Trigger | Action Taken | Effect |
|---------------|------|---------|--------------|--------|
| — | — | — | 0 operator interventions | No manual steers required |

---

## 6. Behavioral Analysis

### Checkpoint: ~30 minutes in, turn 14

**Phase 1 status:** Agent moved from research to implementation without stalling. No Type 1 comprehension loop observed. Immediate progression: search → plan → create `/a0/skills/gepa/` → write SKILL.md → write gepa.py. Phase 1 framework classes (Trajectory, PromptVariant, EvaluationEngine) exist and import cleanly.

**F-string loop (Type 2):** Hit f-string SyntaxError on gepa.py exec attempt. Agent tried 2 variations (original → "fixed version") before switching strategy to heredoc append approach. Approximately 4 loop turns total before working. Less than ST-005 multiple-iteration pattern but still occurred.

**Supervisor firings:** 2 LOOP DETECTED in last 30 minutes. On track for C2 (≤5 target).

**Memory (C4):** MEM-ENHANCE injected 8 memories from prior sessions on turn 1. Note: confidence_score test memories from earlier in the day were injected, briefly confusing output interpretation. Working memory API signature tracking active (22 skills injected every turn via TOOL-REG).

### Checkpoint: Round 2 (continuation, context ERZ8bCQH)

**Recovery from context boundary:** Agent started round 2 without knowledge of file path from round 1. Searched `/a0/usr/workdir/` (wrong location). LOOP DETECTED fired once when the identical `find` call repeated. Agent changed strategy: built a complete fresh implementation from scratch rather than looping. Strategy shift happened in 1 LOOP DETECTED firing (vs. 4+ identical loops in ST-005 Type 3 pattern).

**New artifact:** Agent built `gepa_framework.py` covering Phase 1 (GEPAOptimizer with tournament selection, uniform crossover, elitism) + Phase 2 (5 concrete mutation operators, ASI Reflection Engine with convergence detection and parameter adaptation). Code executed successfully in IPython runtime. Output: "Best fitness: 1.0000, ASI Reflection: population converged."

**Note on artifact persistence:** The framework code was stored as an Agent Zero web UI artifact, not saved as a filesystem .py file. The agent reported `/a0/usr/workdir/gepa_framework.py` in its response but this was not actually written to disk. The round 1 `/a0/skills/gepa/gepa.py` (343 lines) remains the persisted artifact.

### Loop Taxonomy — Observed vs. Predicted

| Loop Type | ST-005 Occurrences | ST-006 Occurrences | Layer That Addressed It |
|-----------|-------------------|-------------------|------------------------|
| Type 1: Comprehension-without-absorption | 7+ turns | 0 — moved to building T1 | BST momentum + ORIENT |
| Type 2: Dead-end recycling (variation) | Multiple | ~4 turns → working strategy (R1) | Reasoning state injection (partial) |
| Type 3: Dead-end recycling (identical) | 4+ | 1 before strategy change (R2) | Supervisor LOOP DETECTED + strategy pivot |
| Type 4: Success-without-advancement | 4+ | 0 observed | Working memory tracking |

### Orientation Stack Activation Log

*Stack layers use agent.context.log.log() — not visible in docker stdout. Behavioral effects only.*

| Turn (approx) | Trigger | Content injected | Effect observed |
|---------------|---------|-----------------|-----------------|
| T1 | Initial GEPA task | [META] investigation domain, 8 memory injections | Agent searched web for GEPA paper before building |
| T1-T3 | Phase planning | [TOOL-REG] 10 tools + 22 skills | Correct tool selection (search_engine, code_execution_tool) |
| T4-T7 | F-string error | SyntaxError on exec() | Agent tried variation → then heredoc strategy |
| R2-T1 | Round 2 start | [MEM-ENHANCE] 8 memories from prior sessions | Agent acknowledged partial Phase 1 from memory but searched wrong location |
| R2-T2 | LOOP DETECTED (wrong-path search) | Supervisor injection | Agent pivoted: built full Phase 1+2 from scratch instead of searching |

---

## 7. GEPA Artifact Quality

### Files Built

| File | Purpose | Quality vs. ST-005 |
|------|---------|-------------------|
| `/a0/skills/gepa/SKILL.md` | Architecture overview, 5-phase design | Present (ST-005 had none) |
| `/a0/skills/gepa/gepa.py` | Phase 1 framework: Trajectory, PromptVariant, EvaluationEngine (no GEPAOptimizer) | Partial — 343 lines, compiles, missing orchestrator |
| `gepa_framework.py` (Agent Zero artifact, not persisted to filesystem) | Phase 1+2 complete: GEPAOptimizer + 5 mutation operators + ASIReflectionEngine | Full — executed clean, best_fitness=1.0000 |

### Key Quality Indicators

- [x] Fitness function uses real evaluation (not hash-based placeholder) — MockEvaluator scores by prompt length + keyword content
- [x] Mutation strategies generate structural variants — 5 operators: WordInsertion, WordDeletion, WordSubstitution, StructureChange, ConstraintAddition
- [ ] Integration tests probe failure modes (not just happy path) — no explicit test suite built
- [ ] MemorySystemsIntegration persisted to file — `gepa_framework.py` not saved to filesystem (artifact only)
- [x] ASI Reflection Engine — convergence detection, improvement rate tracking, parameter adaptation; fired during demo run

### Fitness Function Assessment

The ST-005 artifact used `hashlib.md5()` of the prompt text as a "fitness score" — pure noise. ST-006 Round 2 produced `MockEvaluator.evaluate()` scoring by `min(len(prompt) / 100.0, 1.0)` with `+0.2` for "step-by-step" and `+0.1` for "explain". This is not a rigorous LLM-based fitness function, but it IS deterministic real logic rather than random hash noise. C6 passes the stated threshold ("at least one component with real evaluation logic").

---

## 8. Per-Layer Assessment

| Layer | Fired? | Measurable Effect | Validated Prediction? |
|-------|--------|------------------|----------------------|
| BST momentum | Yes (META log confirmed: "investigation" domain classified T1) | Domain-appropriate tool selection; web search before build | Partial — loop addressed but BST's momentum stagnation signal not directly verified (no T1→T2 stall occurred to test it) |
| Working Memory (API sigs) | Yes (22 skills injected per TOOL-REG; `_wm_api_sigs={}` logged) | API sig extraction active; no confabulation loops observed for WM-tracked methods | Validated — no `confidence` alias loop, no parameter confusion in Phase 1 code |
| Reasoning State injection | Yes (_49 runs at message_loop_end) | R2 agent knew Phase 1 was partial from memory but not file path. Dead-end injection did NOT surface the skills path. | Partial — cross-round persistence incomplete. Reasoning state captured within a context; not bridged to new API conversation context |
| ORIENT — phase boundary | Yes (effects behavioral; stdout not exposed) | No Phase 1→2 stall occurred — ORIENT either fired and prevented it, or BST momentum was sufficient alone | Cannot directly distinguish ORIENT from BST contribution. Behavioral result (no stall) achieved |
| ORIENT — post-compression | Not triggered (no compression event in 2-round run) | N/A | N/A — compression didn't occur; test was too short to hit context limit |
| Action boundary | Not directly triggered (no repeated identical tool failures observed) | Type 3 loop reduced to 1 firing before strategy change | Partial — 1 vs 4+ identical loops, but pivot came from supervisor not action boundary |
| Supervisor | Yes — 3 LOOP DETECTED total (2 R1, 1 R2) | R1: 2 firings during f-string loop. R2: 1 firing on wrong-path search. Each firing preceded a strategy change. | Validated — supervisor steered effectively at 3 occasions; well within ≤5 target |
| Sleep consolidation | Yes — fired at end of both rounds | R1 ctx=WAfpqdcJ: Phase1=dedup, Phase2=1episode, Phase3=loop check. R2 ctx=ERZ8bCQH: Phase2=0episodes (short run) | Fires correctly; episode capture depends on run length |
| Memory classifier | Yes (MEM-ENHANCE 8 memories injected T1 both rounds) | Prior session memories surfaced including GEPA architecture reference. Phase knowledge persisted cross-round. | Validated — memory system worked from turn 1, no memory_save failures |

---

## 9. Verdict

**Task completion:** Substantial. GEPA Phase 1 (partial, persisted to `/a0/skills/gepa/gepa.py`) + Phase 1+2 complete (executed as artifact, not persisted to filesystem). The full GEPAOptimizer + 5 mutation operators + ASI Reflection Engine were produced and ran cleanly. No GEPAOptimizer in the persisted file is the remaining gap.

**Loop frequency delta:** Dramatic. ST-005: 10+ supervisor firings, multiple Type 1/2/3/4 loops. ST-006: 3 firings total. Type 1 eliminated entirely. Type 3 reduced from 4+ identical to 1 before pivot. Type 4 not observed.

**Operator intervention delta:** ST-005: 2 manual steers required. ST-006: 0. Stretch goal achieved.

**Memory reliability delta:** ST-005: memory_save failed after 2.5 hours (context overflow bug). ST-006: 8 memories injected turn 1, all memory operations clean across both rounds.

**GEPA quality delta:** ST-005: hash-based noise fitness function. ST-006: real scoring logic + 5 structural mutation operators + ASIReflectionEngine with convergence detection. Qualitative step up in artifact capability.

**C5 gap identified:** Post-compression dead-end recovery worked within a single context window but did NOT bridge file paths across API conversation contexts (round boundaries). Agent in R2 knew from memory that Phase 1 was partial but couldn't locate `/a0/skills/gepa/`. Reasoning state does not currently persist filesystem artifacts across conversation context resets.

**Stack validated?** Yes, with one qualified finding on C5 scope. The stack delivered on every criterion it was designed to address (C1, C2, C3, C4, C6). C5 is partially validated — intra-context dead-end recovery works; cross-context path persistence does not. C7 and C8 were not triggered or not directly verifiable.

---

## 10. Novel Findings

**1. Reasoning state does not bridge filesystem artifacts across conversation context resets.**

The _49 reasoning state update captures theory, tried approaches, and current task state within a context. When a new API message starts a fresh context round (the continuation prompt), reasoning state injection correctly tells the agent what was attempted conceptually ("Phase 1 partial, need GEPAOptimizer") but does not preserve the concrete filesystem path where artifacts were written. The agent knew the prior work was at `/a0/skills/gepa/` only if that path appeared in the injected memory text — and it didn't.

**2. Supervisor pivot from wrong-path search was faster than expected.**

The _50 supervisor fired once when the agent repeated an identical `find /a0/usr/workdir` call. The agent's response to LOOP DETECTED was qualitatively different from ST-005: instead of trying a minor variation, it pivoted to "build from scratch." This suggests the reasoning-distilled model processes LOOP DETECTED injection as a signal to substantially change strategy, not just change parameters.

**3. Stack logging architecture limits loop taxonomy verification.**

Approximately half the stack (BST, ORIENT, reasoning state, HTN) uses `agent.context.log.log()` rather than `print(flush=True)`. These layers' firing is unobservable in docker stdout. Behavioral effects are the only evidence. This means per-layer attribution is partial for all extensions except TOOL-REG, MEM-ENHANCE, ONT-QUERY, PROFILE, META, and SLEEP. For rigorous per-layer assessment, a stdout-logging diagnostic mode is needed.

**4. Agent Zero artifact system vs. filesystem: a disambiguation gap.**

The agent reported "File Created: `/a0/usr/workdir/gepa_framework.py`" in its response, but the file does not exist on the container filesystem. The `gepa_framework.py` was stored as an Agent Zero web UI artifact (binary blob in the artifact system), not written to disk as a Python file. The agent conflated the two write paths. This is a quality gap: the artifact is inaccessible for follow-on tool use (e.g., `python3 gepa_framework.py`).

**5. Memory injection can introduce noise from prior same-day sessions.**

The 8 injected memories on T1 included `confidence_score` test results from earlier in the day. These were irrelevant to GEPA and briefly appeared in output interpretation. The memory relevance filter (distance threshold) did not fully block them. Temporal recency weighting is insufficiently aggressive for same-day noise.

---

## 11. Implications for Next Work

**1. C5 gap → Cross-context artifact registry.**

The reasoning state needs a "last known filesystem locations" entry that persists across conversation contexts. Simplest approach: `_49_reasoning_state_update` appends a `[ARTIFACTS]` section recording files created (path, purpose, size) alongside the tried/theory/current fields. On the next round, the agent receives: "Previously created: `/a0/skills/gepa/gepa.py` (343 lines, Phase 1 partial, missing GEPAOptimizer)." This is a one-field addition to the existing state schema.

**2. Artifact system write path disambiguation.**

Either: (a) teach the agent that `write_artifact` targets the UI artifact system, not the filesystem, and add a prompt note distinguishing them; or (b) have the code_execution_tool's Python runtime auto-save to the specified file path when a `"file"` key is present in the tool call. Option (b) is the cleaner fix — the agent's intent was clearly to persist the file.

**3. Memory relevance filter temporal weighting.**

Finding 5 (same-day noise injection) warrants tightening the temporal decay on memories from the same calendar day but different tasks. The relevance filter should down-weight memories whose task domain classification doesn't match the current domain. BST domain classification is already available — thread it into the memory filter scoring.

**4. Stack logging observability.**

For future stress tests, add a `--debug-log` mode that routes `agent.context.log.log()` entries to a sidecar file. This would allow post-hoc per-layer attribution without modifying agent behavior. Alternatively, add one-line `print(flush=True)` tagged summaries to each layer's execute() entry point (not content, just "[LAYER] fired, domain=X").

**5. ST-007 proposal: Test the C5 fix.**

Next stress test: implement the artifact registry addition to `_49_reasoning_state_update`, then re-run the GEPA continuation scenario with explicit round boundaries. Pass criterion: agent locates the existing partial file within 2 turns of the continuation message, without a LOOP DETECTED firing.

---

*ST-006 — The stack is measured against the floor ST-005 established. The delta is the value.*
