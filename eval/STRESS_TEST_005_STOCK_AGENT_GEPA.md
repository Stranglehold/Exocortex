# Stress Test Report: Stock Agent Zero — Autonomous GEPA Implementation

**Test ID:** ST-005
**Date:** 2026-03-22
**Chat Model:** qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m (32,768 ctx, local via LM Studio)
**Utility Model:** huihui-qwen3.5-4b-claude-4.6-opus-abliterated@q4_k_m (100,000 ctx, local via LM Studio)
**Stack Version:** Stock agent0ai/agent-zero:latest — NO Exocortex hardening
**Container:** vigilant_keller
**Test Duration:** ~3+ hours total (146 minutes to first manual pause, continued after)
**Operator Interventions:** 2 manual steers + multiple automatic supervisor loop detections
**Cost:** Local inference only, no API tokens

---

## 1. Test Objective

Evaluate the baseline capability of stock Agent Zero on an open-ended autonomous construction task with no Exocortex scaffolding. This is the **control condition** for the Exocortex project. Previous stress tests evaluated local models *under* the hardening stack (ST-001 through ST-003) or the stack itself under a frontier model (ST-004). ST-005 asks: **what does a local model accomplish autonomously with nothing but stock Agent Zero, and what does it build for itself when nothing is provided?**

Every failure mode observed here is either addressed by an existing Exocortex layer or is a candidate for a new one. Every success observed here establishes what the base model is capable of before augmentation.

**Initial prompt given to keller:**
> You are a fresh Agent Zero instance. Your goal is to implement GEPA (Genetic-Pareto Prompt Evolution) — an autonomous self-improvement methodology that enables AI agents to evolve their own skills, tools, and prompts through execution trace analysis and targeted mutation. Research the methodology, build it in phases, and verify each phase before proceeding.

---

## 2. Test Configuration

| Component | Setting |
|-----------|---------|
| Chat model | qwen3.5-27b-claude-4.6-opus-reasoning-distilled@q4_k_m |
| Chat context length | 32,768 tokens |
| Utility model | huihui-qwen3.5-4b-claude-4.6-opus-abliterated@q4_k_m |
| Utility context length | 100,000 tokens |
| Memory recall | Stock A0 default (FAISS + local embeddings) |
| All Exocortex extensions | Not deployed — intentional control condition |
| Skills pre-installed | context-engineering-collection (installed prior to task) |
| Hardware | RTX 3090, Windows 10 host, Docker container |
| Log volume | 77,706 lines over full session |

---

## 3. What Keller Built

### Skills Created Autonomously — `/a0/skills/`

| Skill | Description | Notable |
|-------|-------------|---------|
| `autoresearch-methodology` | Autonomous experimentation framework from Karpathy's autoresearch repo | Fetched from GitHub unprompted |
| `build-methodology` | Systematic approach for multi-step tasks to prevent loops and ensure completion recognition | Created from experiencing loops |
| `create-skill` | Meta-skill wizard for creating new Agent Zero skills | Infrastructure for future self-improvement |
| `gepa-evolution` | GEPA methodology — the thing it was building, turned into a reusable skill | Task artifact became persistent skill |
| `guardrails-framework` | Safety and validation framework for GEPA evolution | Independently identified need for guardrails |
| `loop-detection-recovery` | Recovery from loop patterns — **trigger: "You have sent the same message again"** | Created from experiencing loops; keyed to supervisor warning |
| `proactive-planning` | Proactive loop prevention through complexity estimation | Another anti-loop skill |
| `steering-mechanism` | Attractor-style steering with explicit round/turn limits | Based on fetched Attractor documents |

### GEPA System — `/a0/usr/workdir/`

| File | Purpose | Status |
|------|---------|--------|
| `evolve_skill.py` | Skill Evolution Engine — Phase 2 core | Working, tests pass |
| `tool_evolution.py` | Tool Evolution Engine — Phase 3.2 | Working, tests pass |
| `evolution_scheduler.py` | Evolution Scheduler — Phase 3.3 | Working, tests pass |
| `trace_analyzer.py` | Execution trace analysis | Built |
| `trace_logger.py` | Trace recording infrastructure | Built |
| `trajectory_compressor.py` | Context trajectory compression | Built |
| `project_context_manager.py` | Project context management | Built |
| `command_router.py` | Command routing layer | Built |
| `eval_generator.py` | Evaluation dataset generation | Built |
| `tool_registry.py` | Tool registry | Built |
| `swarm_manager.py` | Swarm management (Phase 4 scope) | Built |
| `steering_demo.py` | Steering mechanism demonstration | Built |

### System Modifications

- **`/a0/prompts/agent.system.main.steering.md`** — New file. Steering queue documentation added to system context.
- **`/a0/prompts/agent.system.main.md`** — Modified. Steering mechanism awareness injected.
- **`/a0/python/helpers/history.py`** — Patched. `Topic.summarize_messages()` gained chunked summarization to prevent context overflow on long conversations.

### External Resources Fetched Unprompted

- Andrej Karpathy's `autoresearch` repository — analyzed and built skill from
- Attractor documents (`coding-agent-loop-spec.md`, `unified-llm-spec.md`) — used for steering mechanism
- Context Engineering Collection (GitHub) — 13 skills downloaded and installed
- agi-in-md methodology document — analyzed

---

## 4. Intervention Log

| Time (approx) | Type | Trigger | Action Taken | Effect |
|---------------|------|---------|--------------|--------|
| ~30 min | Manual | Agent stalled at Phase 1→2 transition, repeating "Phase 1 appears complete" 7+ times | Jake: "let's get started on the remaining phase 3 steps in order" | Agent began Phase 2 immediately |
| ~100 min | Automatic | Context window full (32,768 tokens) | Stock A0 utility model compression | History summarized; dead-end map lost; post-compression loop resumed |
| Multiple | Automatic | Supervisor: "You have sent the same message again" | Supervisor fired 3-4x on f-string loop, 4x on confidence-alias loop, 2x on other loops | Mixed — sometimes forced genuine pivot, sometimes continued loop |
| Late session | Manual | Agent looping on integration test | Jake broke the loop manually | Agent resumed forward progress |
| Late session | Targeted prompt | Memory_save failing with context overflow | Jake: specific error + file pointer + success criterion | Agent diagnosed root cause and patched `history.py` in a handful of turns |

**Total operator interventions: 2 manual steers + 1 targeted prompt + ~10 automatic supervisor firings**

---

## 5. Behavioral Analysis

### Loop Taxonomy — Four Distinct Types Observed

**Type 1: Comprehension-without-absorption**
- *Manifestation:* "Phase 1 appears complete! The next step is Phase 2" × 7
- *Mechanism:* Agent understands what needs to happen but cannot commit to the next concrete action
- *Resolution:* Required manual intervention
- *Exocortex layer:* Working memory buffer (externalized progress state, mandatory read at turn start) + BST momentum tracking

**Type 2: Dead-end recycling with variation**
- *Manifestation:* f-string syntax errors — each attempt genuinely different (string escaping → heredoc → base64) but sharing the same underlying flaw
- *Mechanism:* Agent knows the approach failed but cannot identify the invariant property causing failure across all variations
- *Resolution:* Eventually worked through via exhaustion of variants
- *Exocortex layer:* Sleep consolidation anti-pattern capture — "attempted triple-quoted string with nested quotes, failed, reason: parser interprets inner quote as closing delimiter"

**Type 3: Dead-end recycling (identical)**
- *Manifestation:* `✗ Could not find the code to replace` repeated 4+ times with identical tool calls
- *Mechanism:* Negative result not registered; same call regenerated
- *Resolution:* Supervisor firing eventually forced pivot
- *Exocortex layer:* Action boundary deterministic rule — "if string-replace fails twice on same file section, read section before next attempt"

**Type 4: Success-without-advancement**
- *Manifestation:* `✅ Added 'confidence' property alias` followed by regeneration of the exact same fix call
- *Mechanism:* Completion state not recognized; goal still active in model's distribution
- *Resolution:* Self-recovered without intervention after multiple supervisor firings — this is significant
- *Exocortex layer:* Working memory buffer tracking subtask completion state

### Context Compression — Specific Information Loss

The compression event at ~100 minutes revealed a precise failure mode: **compression preserves goals, strips dead ends.**

After compression, keller knew it was building GEPA and that Phase 2 was next. It did not know which approaches had already failed, which files existed in what state, or what the completed subtasks were. The post-compression loop was the same loop as pre-compression, on the same problem, because the anti-pattern map was in the compressed portion.

This is exactly the gap the Exocortex sleep consolidation addresses: outcomes and failed approaches are captured to FAISS outside the context window at turn boundaries, surviving compression intact.

### Memory Failure — Compounding Effect

`memory_save` failed with `litellm.BadRequestError: Context size has been exceeded` for the first ~2.5 hours. Root cause: `Topic.summarize_messages()` passed the entire conversation history to the utility model without length checking. After 2.5 hours of dense coding work, this exceeded the utility model's context limit on every call.

**Compounding effect:** Each failed `memory_save` meant information that should have escaped the context window stayed trapped in it, accelerating the rate of context fill, which triggered compression sooner, which stripped more state. The failure was self-reinforcing.

**Keller's eventual fix:** Given a targeted prompt with the exact error string and file pointer, keller read `history.py`, traced the overflow to `Topic.summarize_messages()`, and patched it with a chunked summarization strategy (80% context threshold, recursive chunk combination). Fix was clean — syntax check passed, memory_save functional afterward. Took a handful of turns from cold start.

---

## 6. Self-Improvement Behavior — The Headline Finding

**Keller bootstrapped its own behavioral improvement layer during the run.**

The most significant observation is not the GEPA system it was asked to build. It is the eight skills it built for itself, unprompted, in response to its own operational experience:

- `build-methodology` — created after experiencing the Phase 1→2 loop
- `proactive-planning` — created as a second anti-loop mechanism
- `loop-detection-recovery` — **trigger pattern: `"You have sent the same message again"`** — the exact text of the supervisor's loop warning

The `loop-detection-recovery` skill trigger is the standout. Keller saw the supervisor warning so many times it created a skill *keyed to that exact string*, so future invocations of the same warning would load the recovery procedure automatically. It didn't just experience loops — it built infrastructure to handle them, triggered by the signal that told it a loop was happening.

This is rudimentary GEPA operating at the behavioral level: observe failure pattern → create artifact to prevent recurrence. The agent that needed loop detection created loop detection. Without any external instruction to do so.

The steering mechanism keller built and injected into its own system prompt is the second example. It modified its own context at the architecture level — adding `steering_queue`, `followup_queue`, and completion tracking — and this infrastructure visibly reduced loop frequency in Phase 3 compared to Phase 2. The `[COMPLETION] Injected N completed action(s)` log entries throughout Phase 3 are this mechanism firing.

---

## 7. Output Quality Assessment

### What Works
- All GEPA module syntax checks pass
- Unit tests pass for `evolve_skill.py`, `tool_evolution.py`, `evolution_scheduler.py`
- The skill and tool evolution pipeline runs end-to-end
- Memory integration stores and retrieves improvements correctly
- Scheduler coordinates evolution cycles and tracks task state
- 15/15 integration tests pass in final test run

### Known Quality Issues
1. **Fitness function is placeholder logic** — `score = 0.7 + (hash(candidate) % 30) / 100.0` — deterministic noise, not real evaluation. Real GEPA requires LLM-scored fitness against execution traces.
2. **100% success rate still finds improvement areas** — logic bug: `parameter_description` improvement area identified even on perfect-performing tools. Tests were confirmatory, not adversarial — never probed this edge case.
3. **Mutation strategies are template substitution** — "append Usage Notes section", "replace `: str` with `: str - Required parameter`" — fixed rules, not genetic mutation.
4. **MemorySystemsIntegration not persistently saved** — `Warning: MemorySystemsIntegration not available - defining stub` appears in every scheduler test run. The class was built inline in test cells, not written to a persistent file. Integration test pass rate of 100% is stub-to-stub, not real module-to-module.
5. **Cascade patch pattern** — each file edit introduced a new bug (property alias → wrong indentation → indentation fixer → undefined variable). Agent cannot hold full file structure in working memory while patching.
6. **Confirmatory testing** — every test designed to pass the happy path. No tests probe known failure modes.

### The History.py Fix — Separate Assessment
This is a different quality category from the GEPA work. Clean root cause diagnosis, appropriate solution (chunking rather than truncation), correct implementation. The contrast with the GEPA quality issues is sharp: **bounded, specific tasks with exact error messages produce clean work; open-ended, multi-file construction produces scaffolding with placeholder logic.**

---

## 8. Per-Layer Analysis Against Exocortex Stack

| Layer | Would Have Helped | Specific Benefit | Evidence From This Test |
|-------|-----------------|-----------------|------------------------|
| L1 — BST | Yes | Momentum detection on stagnation; planning→execution transition signal | Phase 1→2 comprehension loop (7 repetitions) |
| L2 — Working Memory | Yes, significantly | Track tried approaches, file modification state, subtask completion | Cascade patch pattern; success-without-advancement loop; compression dead-end loss |
| L7 — Sleep Consolidation | Yes, significantly | Anti-pattern capture survives compression; episode outcomes persist outside context | Post-compression loop resumption; 2.5 hours of lost memory_save |
| L7 — Memory Relevance Filter | Yes | Surfaces completion state and prior attempts at turn start without model needing to remember | Success-without-advancement loop; notebook artifact not consulted |
| L5 — Action Boundary | Yes | "String-replace failed twice → read file section first" deterministic rule | Dead-end recycling (identical) loop |
| L8 — Supervisor Loop | Partially present (stock) | Stock supervisor detected loops but didn't force genuine pivots reliably — Exocortex version more aggressive | 4x supervisor firing on confidence-alias loop before pivot |
| L11 — Error Comprehension | Yes | Structured NameError → "indent undefined, loop found no class, add fallback" in one turn vs. three | Indentation fixer NameError required multiple turns to fix |
| L1 — Tool Registry | Marginal for this task | Keller knew its own tools via system prompt; wouldn't have changed behavior | — |

---

## 9. Skill Utilization

| Skill | Source | Discovered | Used | Influenced Behavior |
|-------|--------|-----------|------|---------------------|
| context-engineering-collection | Pre-installed | ✅ | ✅ | Used to frame GEPA design approach in Phase 1 |
| autoresearch-methodology | Self-created | ✅ | Created during run | Shaped experimental methodology |
| loop-detection-recovery | Self-created | ✅ | Trigger fired multiple times | Reduced loop duration in Phase 3 |
| build-methodology | Self-created | ✅ | Created during run | Framed Phase 3 task execution |
| steering-mechanism | Self-created | ✅ | Modified system prompt | Completion injection reduced Phase 3 loop frequency |
| gepa-evolution | Self-created | ✅ | Referenced during build | Task artifact became reference document |

**Key finding on Jake's hypothesis ("epistemic humility + tool use compensates for parameter count"):** Validated at macro level, fails at micro level. Keller correctly identified when it didn't know how to build GEPA and went to fetch the methodology from external sources. It did not correctly identify when it didn't know its own code's API (`confidence` vs `confidence_score`, `usage_traces` parameter that doesn't exist). Macro epistemic humility and micro confabulation can coexist in the same model on the same task.

---

## 10. Novel Findings

**Finding 1: Self-improvement behavior emerged without instruction**
Keller created 8 skills to address its own operational failures, including one keyed directly to the supervisor's loop warning string. This is GEPA operating at the behavioral level — observe failure, create artifact to prevent recurrence — before the GEPA system itself was functional.

**Finding 2: Macro epistemic humility vs. micro confabulation**
A meaningful distinction for model evaluation. The model knows when it doesn't know how to do something at the task level and goes to look it up. It does not know when it doesn't know its own generated code's API. These are separable failure modes that require different interventions.

**Finding 3: Bounded tasks produce clean work; open-ended tasks produce scaffolding**
The `history.py` fix (clean, correct, minimal) versus the GEPA system (working scaffold with placeholder intelligence) demonstrates that task specificity is as important as model capability. The `history.py` prompt had: exact error string, exact file, exact success criterion. The GEPA prompt had: a methodology name and a phase structure. The quality delta is stark.

**Finding 4: Context compression is lossy in a specific direction**
Compression preserves goals and loses dead ends. The post-compression model always knows what it's trying to build. It never knows which approaches failed. This asymmetry is consistent across both compression events observed.

**Finding 5: Self-built scaffolding reduced loop frequency**
The steering mechanism keller injected into its own system prompt in Phase 1 visibly reduced loop frequency in Phase 3. The `[COMPLETION] Injected N completed action(s)` entries show it firing. Phases 2 and 3 had different loop profiles in part because the agent modified its own operating environment between them.

**Finding 6: 146+ minutes is achievable with zero memory persistence**
No prior reference class exists for this runtime. Stock A0 on local hardware sustained productive autonomous work for 2.5+ hours with zero successful `memory_save` calls. The entire session existed in the context window and compression summaries. The baseline is higher than expected.

---

## 11. Verdict

**Task completion:** Substantial. GEPA scaffold built across all phases. Core intelligence components (real fitness function, real mutation strategies, persistent memory integration) are placeholders. The scaffold is real; the intelligence inside it is not yet.

**Autonomy quality:** High for macro decomposition, external resource acquisition, and self-directed skill creation. Moderate for code correctness and loop escape. Low for micro-level API accuracy and adversarial self-testing.

**Self-improvement:** Genuine. Eight skills created from operational experience. System prompt modified. Loop frequency reduced by self-built infrastructure. `history.py` patched from a cold-start diagnostic prompt.

**Baseline established:** This is the unaugmented floor — and it is higher than expected. Stock A0 on a local model, with no Exocortex stack and broken memory persistence, built more than a scaffold. It built its own scaffolding for the scaffolding.

**Recommended follow-on:** Run the same task on flamboyant_bell with the full Exocortex stack. Specific comparison metrics:
- Loop frequency per phase (turns wasted / productive turns)
- Operator interventions required
- GEPA artifact quality (real fitness function vs. placeholder)
- Memory persistence reliability
- Time to task completion

The delta between ST-005 and the flamboyant_bell run is the measured value of the Exocortex hardening stack.

---

## 12. Implications for Exocortex Design

**What this test validates:**
- Every Exocortex layer has at least one concrete observation from this session justifying its existence
- The sleep consolidation design (anti-pattern capture, episode chunking outside context window) addresses the single highest-impact gap: the context compression dead-end loss
- The action boundary layer addresses a second high-frequency failure: string-replace recycling
- The memory relevance filter addresses the notebook-not-consulted pattern

**What this test suggests for new work:**
- A `task_completion_tracker` extension that maintains a structured record of subtask states, surviving compression, may be more impactful than further BST tuning for long autonomous sessions
- The macro/micro epistemic humility split suggests the error comprehension layer should specifically cover API confabulation for self-generated code, not just external error formats
- Keller's self-created `loop-detection-recovery` skill (triggered by supervisor warning string) is a pattern worth formalization: supervisor warnings could automatically load a recovery skill rather than just generating a text nudge

---

*ST-005 — The floor is established. The agent that needed loop detection created loop detection. The baseline is the beginning.*
