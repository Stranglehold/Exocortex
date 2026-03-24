# The Orientation Stack — Design Note
## Positional Awareness Architecture for Long-Horizon Agent Tasks

**Status:** Pre-spec exploration with field evidence. Motivated by ST-005 (stock Agent Zero GEPA session, March 22 2026), Kestrel's independent observations, post-session memory_save testing, and research synthesis. Ready for Kestrel review and implementation planning.

**Related documents:**
- ST-005 Stress Test Report (stock Agent Zero GEPA, 146+ min autonomous)
- Kestrel Observations ST-005 (independent analysis)
- ST-005 Design Implications (Kestrel synthesis + ST-006 planning)
- Loop Feedback Cascade Design Note (Session 049) — Tiers 1-3: warn, summarize, reset
- Loop Feedback Cascade Addendum (Session 055) — Tier 4: anti-pattern learning
- Reasoning Persistence & PACE Design Note (Session 057) — reasoning state, strategy planning
- Staging Tier Spec L3 (Session 060) — intermediate memory, canary CUSUM, session init
- CORAL: Cognitive Resource Self-Allocation (ICLR 2026 submission) — checkpoint-based working memory management
- Boyd's OODA Loop (1986) — Observe-Orient-Decide-Act decision cycle

---

## The Problem

### What ST-005 Demonstrated

A stock Agent Zero instance (keller) running a local 27B model with no Exocortex scaffolding and no persistent memory built a multi-file GEPA system across 146+ minutes of autonomous work. It created 8 skills from operational experience, patched a core Agent Zero bug, and modified its own system prompt — all without being told to.

It also looped for 7 consecutive turns at one phase boundary, recycled dead ends after every context compression event, hallucinated parameters for its own generated code, wrote 15 tests that all confirmed the happy path with zero adversarial probes, and failed to save a single memory across 2.5 hours of work.

Every failure mode traces to a single root cause: **the agent doesn't know where it is.**

### The Positional Awareness Gap

At Phase 1→2 transition, the agent completed Phase 1 analysis but didn't know it had completed it. It repeated "Phase 1 appears complete" seven times before the operator manually said "let's get started on the remaining phase 3 steps in order." The agent began Phase 2 immediately. The capability was present. The positional awareness was absent.

After context compression, the utility model summarized the conversation history. The summary preserved the goal (build GEPA) and lost the dead-end map (which approaches failed and why). The agent immediately retried approaches that had already failed — not because it chose to retry them, but because it no longer knew they had been tried. The information was gone. The decisions that followed were wrong because they were made from incomplete information.

During code construction, the agent wrote `evolve_tool_description()` with specific parameters, then called it two turns later with hallucinated parameters (`confidence` instead of `confidence_score`, `usage_traces` instead of actual parameter names). The working signature was no longer in context. The agent pattern-matched to what the API *should* look like based on general Python conventions, not what it *actually* was.

In post-session testing, the agent attempted `from agent import AgentZero; agent.memory_save()` — treating a JSON tool call as a Python import. The boundary between "thing I call as a Python method" and "thing I invoke as an Agent Zero tool" doesn't exist in the model's working memory.

### The Missing Phase: Orient

Boyd's OODA loop (Observe-Orient-Decide-Act) describes a decision cycle where each phase feeds the next. The agent currently performs three of the four phases:

- **Observe:** Reads context (conversation history, tool output, system messages)
- ~~**Orient:** Assess position, integrate new information with existing knowledge, update situational model~~
- **Decide:** Choose an action based on available context
- **Act:** Execute the chosen action via tool call

The Orient phase is missing. The agent jumps from observation to decision without assessing its position in the task, reviewing what it's already tried, or checking its plan. When the observation is clean (turn 1, fresh context), this works. When the observation is degraded (post-compression, mid-loop, long action history), the missing Orient phase means decisions are made from degraded information without the agent knowing the information is degraded.

Jake's manual interventions in ST-005 were mechanically inserting the Orient phase: "stop, find where you are, check what you've completed, look at your build plan." Each intervention produced immediate forward progress — not because the operator provided new information, but because the operator triggered the orientation the agent couldn't perform for itself.

The Exocortex should provide this orientation structurally.

---

## Research Lineage

### CORAL: Cognitive Resource Self-Allocation (ICLR 2026 submission)

CORAL gives agents a callable working memory management toolset. The agent maintains checkpoints of its progress and can initiate a new problem-solving episode by purging cluttered context and resuming from the most recent checkpoint. Attention analysis shows agents using CORAL maintain focused allocation on checkpoints rather than getting diluted by accumulated noise. Significant improvements on long-horizon task benchmarks.

**Design implication:** Checkpointing is the right primitive. The agent should be able to save and restore its positional state. The orientation stack provides this through the task completion tracker and reasoning state — both persist outside the context window and are injected when needed.

### Boyd's OODA Loop (1986)

The Orient phase is the most important phase in Boyd's framework — more important than Decide or Act. Orientation integrates new observations with prior experience, cultural traditions, genetic heritage, and previous destruction/creation processes to form a mental model. In Boyd's formulation, the quality of orientation determines the quality of all subsequent decisions. Agents that orient faster and more accurately outperform agents that act faster.

**Design implication:** Speed of action is irrelevant if orientation is wrong. The agent that retries dead ends after compression is acting fast but orienting from incomplete information. The orientation stack prioritizes correct orientation over fast action.

### Reasoning Persistence & PACE (Session 057, internal)

Already specified but not yet built. Two mechanisms: (1) a compressed reasoning state injected at top of context every turn — theory, what's been tried, current approach, open questions; (2) PACE pre-generated strategies with mechanical switching — Primary, Alternate, Contingency, Emergency. Both address the loop problem from the model's perspective rather than from the environment's perspective.

**Design implication:** The reasoning state is Component 2 of the orientation stack. PACE strategies become the "OPTIONS" field in the tool-failure orientation prompt. These designs integrate directly — they were waiting for the integration layer that the orientation protocol provides.

### Loop Feedback Cascade (Session 049, internal)

Operates on the conversation history after loop detection. Tier 1: warn. Tier 2: context surgery (remove loop turns, inject summary). Tier 3: force response. Tier 4: anti-pattern capture for procedural memory.

**Design implication:** The cascade is reactive — it fires after the loop starts. The orientation stack is proactive — it fires at the moments where loops are most likely to begin (phase boundaries, tool failures, compression events). The two are complementary: orientation reduces loop probability, the cascade catches loops that orientation doesn't prevent. Defense in depth.

### Staging Tier (Session 060, deployed)

The staging tier provides the persistence layer that the orientation stack reads from. Canary entries survive compression. Observations tagged with dead-end information persist in `staging.jsonl` when the context window loses them. Session init injects active staging entries on the first turn of each session.

**Design implication:** The staging tier is the dead-end persistence mechanism. The orientation protocol reads from it. The agent writes to it via `staging_note`. The question is whether the agent self-initiates staging writes — if not, the orientation protocol should prompt staging writes after tool failures.

### Convergent Architecture (ST-005 finding)

Keller, with no scaffolding and no knowledge of Exocortex, independently built:
- `loop-detection-recovery` skill triggered by the supervisor's exact warning string
- A steering mechanism injected into its own system prompt
- Completion state tracking via a buildplan markdown file

These are structurally identical to the Exocortex supervisor, BST enrichment, and the task completion tracker proposed here. The problem domain forces similar solutions regardless of the builder.

**Design implication:** The orientation stack is not arbitrary. It addresses problems the agent will attempt to solve for itself if we don't provide the infrastructure. Providing it structurally means the agent doesn't spend 30+ turns building workarounds under pressure — it has them from the start.

---

## Design Principles

1. **Orient before acting.** The agent must assess its position before every consequential decision. The orientation is injected, not generated — the agent reads its state rather than reconstructing it from degraded context.

2. **Trigger-based, not continuous.** Orientation fires at specific moments: phase boundaries, tool failures, compression events, session start. It does not fire on every turn — that would be the per-turn injection overhead we diagnosed in Session 060 as net-negative. The triggers are the moments where positional awareness degrades most.

3. **Domain-tailored.** The BST classifies the current domain. The orientation prompt adapts: coding tasks get file structure and API signatures; research tasks get sources consulted and findings; operational tasks get system state and commands run. The orientation is relevant because it's shaped by the domain.

4. **Reads from existing infrastructure.** The orientation protocol doesn't create new data — it reads from components that already exist or are specified: task completion tracker, reasoning state, staging tier canaries, working memory entities, tool registry. It is the integration layer, not a new data source.

5. **Deterministic.** All trigger detection, state reading, and prompt assembly is deterministic. No LLM calls for orientation. The orientation block is constructed from structured data and injected as formatted text.

6. **Graceful degradation.** If the task tracker has no buildplan, orientation skips the plan section. If staging has no canaries, the dead-end section is empty. If reasoning state doesn't exist yet, orientation uses whatever is available. Every component is optional — the protocol assembles whatever state exists.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ AGENT TURN                                                      │
│                                                                 │
│  ┌─────────┐   ┌──────────┐   ┌───────────────────┐            │
│  │ BST     │──→│ Orient   │──→│ Main LLM Call     │            │
│  │ (_11)   │   │ (_12)    │   │                   │            │
│  │ domain  │   │ trigger  │   │ [ORIENT] block    │            │
│  │ classify│   │ check +  │   │ in context if     │            │
│  └─────────┘   │ inject   │   │ trigger fired     │            │
│                └────┬─────┘   └───────────────────┘            │
│                     │ reads from:                               │
│          ┌──────────┼──────────────────────┐                   │
│          ↓          ↓          ↓           ↓                   │
│  ┌────────────┐ ┌────────┐ ┌────────┐ ┌──────────┐           │
│  │ Task       │ │Reason- │ │Staging │ │ Tool     │           │
│  │ Completion │ │ing     │ │Tier    │ │ Registry │           │
│  │ Tracker    │ │State   │ │canaries│ │          │           │
│  └────────────┘ └────────┘ └────────┘ └──────────┘           │
│       ↑              ↑          ↑                              │
│  buildplan      compressed   dead ends                         │
│  + subtask      reasoning    + observations                    │
│  states         chain        that survived                     │
│                              compression                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Components

### Component 1: Task Completion Tracker

**What it is:** A structured checklist that tracks the agent's position in a multi-phase task. Persists outside the context window via staging tier.

**When it activates:** When BST classifies a task as COMPLEX (multi-step, multi-file, planning required) and the agent creates a buildplan, OR when the orientation protocol detects a structured plan in the agent's output.

**What it stores:**

```json
{
  "plan_id": "gepa_build_20260322",
  "phases": [
    {
      "name": "Phase 1: Research & Design",
      "status": "completed",
      "subtasks": [
        {"task": "Fetch GEPA methodology", "status": "completed", "turn": 4},
        {"task": "Analyze autoresearch repo", "status": "completed", "turn": 8},
        {"task": "Create design document", "status": "completed", "turn": 12}
      ]
    },
    {
      "name": "Phase 2: Core Implementation",
      "status": "in-progress",
      "subtasks": [
        {"task": "Build evolve_skill.py", "status": "completed", "turn": 18},
        {"task": "Build tool_evolution.py", "status": "in-progress", "turn": null},
        {"task": "Write tests", "status": "pending", "turn": null}
      ]
    }
  ],
  "current_phase": 1,
  "current_subtask": 1,
  "total_phases": 4,
  "completed_phases": 1
}
```

**Persistence:** Written to `staging.jsonl` as an `intention` entry (survives compression, injected at session start). Updated after each subtask completion detected by the orientation protocol.

**Detection mechanism:** The orientation protocol monitors for subtask completion signals: file creation confirmed, test suite passed, agent explicitly marks a step done. Detection is heuristic — keyword matching on agent output for completion indicators (`"Phase N complete"`, `"Tests pass"`, `"Created file X"`, tool success on write operations). False positives are acceptable because the tracker is advisory, not authoritative.

**File:** `extensions/message_loop_end/_48_task_tracker.py` (fires before supervisor at _50, writes state that orientation reads)

---

### Component 2: Reasoning State Persistence

**What it is:** A compressed, auto-updated summary of the agent's problem-solving state, injected at the top of context before each step.

**Format (from Session 057 design note):**

```
[REASONING STATE — step {n}]
Theory: {one-line theory of the current problem}
Tried: {approach 1} → {outcome}
Tried: {approach 2} → {outcome}
Current: {what the agent is doing now and why it's different from what failed}
Open question: {the thing the agent isn't sure about}
```

**Update mechanism:** After each agent turn, a deterministic extractor parses the tool call and its result:
- Tool name and key parameters → updates "Current"
- Error output → adds to "Tried" with failure reason
- Success output → clears "Tried" for that approach, advances "Current"

The "Theory" and "Open question" fields are updated by the agent itself — the reasoning state prompt includes `"Update your theory if your understanding has changed"` as a lightweight metacognitive instruction. If the agent doesn't update, the previous values persist.

**Files:**
- `extensions/before_main_llm_call/_12_reasoning_state.py` — Injects reasoning state at top of context
- `extensions/message_loop_end/_49_reasoning_state_update.py` — Deterministic update after each step

**Interaction with staging tier:** On compression events, the current reasoning state is written to `staging.jsonl` as an `observation` entry so it survives. On the next turn, the orientation protocol reads it back.

---

### Component 3: Situational Orientation Protocol

**What it is:** A trigger-based injection system that provides domain-tailored orientation prompts at critical moments. The integration layer that reads from all other components.

**File:** `extensions/before_main_llm_call/_12_situational_orientation.py` (fires after BST at _11, before or combined with reasoning state injection)

**Triggers and templates:**

#### Trigger A: Phase Boundary

**Detection:** Task tracker reports a phase status change (any subtask within a phase transitions to `completed` and the next subtask is `pending`), OR BST detects a domain shift that indicates task mode change (e.g., research → implementation).

**Injection:**

```
[ORIENT — Phase transition]
COMPLETED: Phase 1 (Research & Design) — all 3 subtasks done
ENTERING: Phase 2 (Core Implementation)
FIRST STEP: Build evolve_skill.py (fitness function, mutation engine, selection)
{dead ends from staging canaries, if any}
Do not re-analyze Phase 1. Begin executing the first step of Phase 2.
```

**What this addresses:** The 7-repetition comprehension loop at Phase 1→2 in ST-005. The agent sees what's done, what's next, and receives an explicit instruction to execute rather than reflect.

#### Trigger B: Tool Failure / Momentum Break

**Detection:** Tool call returns an error, OR supervisor detects momentum stall (same tool called 2+ times with same parameters), OR BST detects domain hasn't changed across 3+ turns with no forward progress.

**Injection:**

```
[ORIENT — Tool failure: {tool_name}]
ERROR: {structured error summary from error comprehension if available}
TRIED SO FAR: {from reasoning state "Tried" entries}
BUILDPLAN SAYS: {current subtask and its success criterion from tracker}
OPTIONS:
  A) {tool alternative from TOOL_ALTERNATIVES map, if applicable}
  B) Use staging_note to record this dead end, then try a fundamentally different approach
  C) If stuck after 2 alternatives, use response tool to report progress and ask for guidance
Do NOT retry the same approach with the same parameters.
```

**What this addresses:** Dead-end recycling, string-replace repetition (4x same call in ST-005), and the "do something different" instruction that fails because "different" has no anchor. The orientation provides specific alternatives and a structured escalation path.

#### Trigger C: Post-Compression Recovery

**Detection:** Context compression event detected (utility model summarization fired — detectable via conversation history length dropping significantly between turns, or via explicit signal from the A0 compression handler).

**Injection:**

```
[ORIENT — Context compressed. Your memory of failed approaches may be incomplete.]
BUILDPLAN STATUS:
  Phase 1: ✓ Complete
  Phase 2: In progress — subtask 2 of 3 (tool_evolution.py)
DEAD ENDS (from staging — these survived compression):
  • document_query fails with parameter error — use cat/head instead
  • string-replace on evolve_skill.py line 42 failed 3x — read file section first
REASONING STATE: {last saved reasoning state from staging}
Check staging notes before retrying any approach you're uncertain about.
```

**What this addresses:** Finding 4 from ST-005 — compression preserves goals and loses dead ends. The post-compression agent gets its dead-end map back from the staging tier, its positional state from the tracker, and its reasoning chain from the persisted reasoning state.

#### Trigger D: Session Start (enhancement to existing _10_session_init)

**Detection:** First turn of a new session (existing mechanism in `_10_session_init.py`).

**Enhancement:** In addition to the current staging injection, include the task tracker state and the last reasoning state snapshot. The agent starts the session knowing exactly where the previous session left off.

---

### Component 4: Tool Registry

**What it is:** Dynamic injection of custom tool availability at turn start.

**Already specified by Kestrel.** See plan file `eventual-swinging-pixel.md`. Injects `[CUSTOM TOOLS — call by tool_name]` block. Auto-discovers Tool subclasses via AST parse (no import). Reads `tool_manifest.json` for installed programs.

**What this addresses:** The micro-confabulation boundary between Python methods and Agent Zero tool calls. Confirmed in three tests (stack_status, oss_health, swarmfish_predict) and in post-session memory_save testing.

**Integration with orientation protocol:** When Trigger B fires (tool failure), the orientation prompt includes the relevant tool registry entry showing correct calling convention.

---

### Component 5: Working Memory API Extraction (Enhancement)

**What it is:** Extension to existing `_11_working_memory.py` entity extraction. When the agent writes code that defines a function signature, class definition, or attribute assignment, extract and store the signature as a working memory entity.

**Detection patterns (regex or AST-lite):**

```python
# Function definitions
r'def\s+(\w+)\s*\(([^)]*)\)'  # → "Function evolve_tool_description(tool_name: str, ...)"

# Class definitions  
r'class\s+(\w+)'  # → "Class ToolEvolutionEngine"

# Key attribute assignments (in __init__ or class body)
r'self\.(\w+)\s*='  # → "Attribute: self.confidence_score"
```

**What this addresses:** The `confidence` vs `confidence_score` confabulation. The `usage_traces` hallucination. The model pattern-matching to what the API should look like instead of what it actually is. By storing the actual signatures in working memory and re-injecting them like file paths and variable names already are, the model sees the correct API surface before calling it.

---

### Component 6: Memory Catalog Async Fix

**What it is:** Bug fix. Lines 66 and 70 of `_18_memory_catalog.py` call async functions without `await`. Memory catalog silently produces no output.

**Fix:** Add `await` to `_build_episodic_catalog()` and `_build_procedural_catalog()` calls. Verify both are declared `async def`.

---

## Integration Map

| Component | File(s) | Hook | Reads From | Writes To |
|-----------|---------|------|------------|-----------|
| Task Tracker | `_48_task_tracker.py` | message_loop_end | Agent output, tool results | staging.jsonl (intention), `_layer_signals` |
| Reasoning State Inject | `_12_reasoning_state.py` | before_main_llm_call | `agent.data["reasoning_state"]` | User message context |
| Reasoning State Update | `_49_reasoning_state_update.py` | message_loop_end | Agent output, tool results | `agent.data["reasoning_state"]`, staging.jsonl on compression |
| Orientation Protocol | `_12_situational_orientation.py` | before_main_llm_call | Tracker, reasoning state, staging, tool registry, working memory | User message context |
| Tool Registry | `_16_tool_registry.py` | before_main_llm_call | Tool directory AST scan, tool_manifest.json | User message context |
| WM API Extraction | `_11_working_memory.py` (modify) | hist_add_before | Agent code output | Working memory entity store |
| Memory Catalog Fix | `_18_memory_catalog.py` (modify) | before_main_llm_call | Memory stores | User message context |

**Execution order in `before_main_llm_call`:**
1. `_10_session_init.py` — staging injection (first turn only)
2. `_11_belief_state_tracker.py` — domain classification
3. `_12_situational_orientation.py` — trigger check + orientation injection (includes reasoning state)
4. `_16_tool_registry.py` — tool availability injection
5. `_18_memory_catalog.py` — memory catalog (after async fix)

**Execution order in `message_loop_end`:**
1. `_48_task_tracker.py` — update buildplan state from agent output
2. `_49_reasoning_state_update.py` — update compressed reasoning chain
3. `_50_supervisor_loop.py` — anomaly detection, canary CUSUM (existing)

---

## What This Does NOT Do

- **Does not replace the Loop Feedback Cascade.** The cascade is the backstop. Orientation reduces loop probability; the cascade catches loops that orientation doesn't prevent. Defense in depth.

- **Does not fire on every turn.** Trigger-based, not continuous. Simple conversational turns get no orientation injection. Only phase boundaries, tool failures, compression events, and session starts trigger the protocol. This avoids the per-turn overhead diagnosed in Session 060 as net-negative.

- **Does not make decisions for the agent.** The orientation block provides information and options. The agent still decides what to do. The options are structured (PACE-style A/B/C alternatives), but the choice is the agent's.

- **Does not require LLM calls.** All trigger detection, state reading, and prompt assembly is deterministic. The only LLM-assisted component is the "Theory" and "Open question" fields in reasoning state, which are updated by the agent as part of its normal output processing.

- **Does not depend on all components being present.** Each component degrades gracefully. No tracker → orientation skips plan section. No reasoning state → orientation skips "tried" section. No staging canaries → orientation skips dead-end section. The protocol assembles whatever state exists.

---

## Build Order

### Wave 1: Immediate Fixes (can deploy now)

| # | Component | Effort | Impact |
|---|-----------|--------|--------|
| 1a | Tool Registry (`_16_tool_registry.py`) | Already specced | Fixes micro-confabulation boundary |
| 1b | Memory Catalog async fix (`_18_memory_catalog.py`) | 2 lines | Unblocks catalog |
| 1c | Error Comprehension heredoc pattern | **DONE** — deployed 2026-03-22 | Fixes terminal loop |

### Wave 2: Orientation Stack Core (one integrated build)

| # | Component | Effort | Depends On |
|---|-----------|--------|------------|
| 2a | Task Completion Tracker (`_48_task_tracker.py`) | ~120 lines | Staging tier (deployed) |
| 2b | Reasoning State Persistence (`_12` + `_49`) | ~150 lines total | None |
| 2c | Situational Orientation Protocol (`_12_situational_orientation.py`) | ~200 lines | 2a, 2b, staging tier, BST |

Build order within Wave 2: Tracker first (2a) — it's the simplest and provides the positional backbone. Reasoning state second (2b) — it's the compressed chain. Orientation protocol last (2c) — it's the integration layer that reads from both.

### Wave 3: Enhancement

| # | Component | Effort | Depends On |
|---|-----------|--------|------------|
| 3a | Working Memory API extraction | ~40 lines added to `_11` | None |
| 3b | BST adversarial testing prompt | ~10 lines conditional in BST enrichment | BST (existing) |

### Wave 4: Validation

| # | Test | Purpose |
|---|------|---------|
| 4a | Unit verification | Each component fires correctly in isolation |
| 4b | Integration test | Orientation fires on tool failure, injects correct state |
| 4c | ST-006 | Full GEPA comparison: stock keller (ST-005) vs orientation-stack flamboyant_bell |

---

## ST-006 Test Design

**Hypothesis:** The same GEPA task run on flamboyant_bell with the orientation stack will produce qualitatively different behavior — not just fewer loops, but different decisions at transition points.

**Task:** Identical GEPA prompt from ST-005.

**Comparison metrics:**

| Metric | ST-005 Baseline | ST-006 Target |
|--------|-----------------|---------------|
| Phase boundary stalls | 7-turn comprehension loop | 0-1 turns (orientation fires) |
| Post-compression dead-end retries | Multiple (every compression) | 0 (staging canaries persist) |
| Tool parameter confabulation | 3+ instances | Reduced (WM API extraction) |
| Tool-vs-import confusion | 1 instance (memory_save) | 0 (tool registry injection) |
| Confirmatory-only tests | 15/15 confirmatory | At least 1 adversarial (BST prompt) |
| Operator interventions | 2 manual + 1 targeted | Target: 0-1 |
| Fitness function quality | Hash noise placeholder | Non-trivial evaluation logic |
| Total loops | ~10+ supervisor firings | <5 |

**The qualitative question:** When friction is removed, does the agent become a different kind of agent (makes different decisions because it has different information) or a faster version of the same agent (same decisions, fewer retries)?

**Evidence for "different kind":** The agent avoids dead ends post-compression (different decision because dead-end map is present). The agent transitions phases without stalling (different behavior because positional state is visible). The agent generates adversarial tests (different testing posture because BST prompt shifted the frame).

**Evidence for "faster version":** Loop count decreases but decision patterns are identical. The agent still builds the same GEPA scaffold with the same placeholder fitness function, just with fewer detours.

**Prediction:** Different kind. Finding 4 from ST-005 shows the post-compression agent isn't just slow — it's wrong. Changing the information changes the decisions.

---

## Answers to Kestrel's Open Questions

### Q1: The evaluation layer gap in GEPA

This is a task-design problem, not a scaffolding problem. Adversarial testing requires modeling your own failure modes — a metacognitive operation the model can't self-initiate. But there's a scaffolding intervention: when BST detects the agent is writing tests (domain: testing/validation), inject: `"Include at least one test that probes a known edge case or expected failure mode. If all tests pass on the first run, your test suite may be confirmatory rather than adversarial."` One line of conditional BST enrichment. The model may or may not follow it, but the instruction costs almost nothing and the upside is significant. This is Wave 3b in the build order.

### Q2: Friction removal — different kind or faster version?

Prediction: different kind. The argument is Finding 4. The post-compression agent with dead-end persistence makes different decisions from the post-compression agent without it, because the information set is different. An agent that orients correctly at phase boundaries doesn't stall — it proceeds. That's not speed. That's a qualitatively different behavioral pattern. ST-006 is designed to test this prediction.

### Q3: Micro confabulation beyond the tool boundary

Three-layer address: (1) Tool registry fixes the tool-vs-Python boundary specifically. (2) Working memory API extraction stores self-generated function signatures as entities, preventing parameter hallucination for the agent's own code. (3) Reasoning state persistence includes "Tried: `function_name(actual_params)` → outcome" — the correct signature is visible in the compressed reasoning chain. None of these are guaranteed fixes. Together they make the correct API surface available at three different injection points. The model still has to read them, but the information is present.

---

## The Deeper Principle

Kestrel said it best: the stack is friction removal at scale.

The orientation stack doesn't add capability. The agent already has the capability — ST-005 proved that. What it adds is the positional infrastructure that lets the capability deploy reliably across phase boundaries, compression events, tool failures, and session boundaries.

Jake's observation that motivated the Reasoning Persistence design note in Session 057 remains the foundational insight: *the model can't remember what it did in the previous step. That's a working memory problem, not an intelligence problem.* The orientation stack is a working memory prosthetic applied to the specific moments where working memory fails most consequentially.

The agent is capable. The memory is the bottleneck. The prosthetic fills the gap.

---

*Motivated by ST-005 field evidence, Kestrel's independent observations, post-session memory_save testing, and CORAL/OODA research synthesis. Integrates and supersedes the Reasoning Persistence & PACE design note (Session 057) by providing the integration layer that connects reasoning state, strategy planning, task tracking, and the staging tier into a unified orientation system.*

*The agent that always knows where it is can tackle problems the agent that doesn't know where it is cannot even attempt — regardless of how capable the model is.*

*For Kestrel review. Build order: Wave 1 (immediate fixes) → Wave 2 (orientation stack core) → Wave 3 (enhancements) → Wave 4 (ST-006 validation).*
