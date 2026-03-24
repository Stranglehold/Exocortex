# Reasoning Persistence & Strategy Planning — Design Note
## Addressing the Loop Problem from the Model's Perspective

**Status:** Pre-spec exploration. Motivated by Session 057 observation that the loop problem has two root causes the existing Loop Feedback Cascade doesn't address: (1) the model loses its own reasoning chain as action history accumulates, and (2) by the time the model is stuck, its context is too polluted to generate alternatives. Jake proposed two complementary ideas that address both causes. This document formalizes them and specifies their integration with the existing loop detection infrastructure.

**Related documents:**
- Loop Feedback Cascade Design Note (Session 049) — Tiers 1-3: warn, summarize, reset
- Loop Feedback Cascade Addendum (Session 055) — Tier 4: anti-pattern learning
- Sleep Consolidation Integration Map (Session 057) — knowledge persistence and retrieval
- Kestrel's Playbook — operational patterns for Agent Zero extensions

---

## The Problem

### What the Loop Feedback Cascade Does
The existing design operates on the conversation history — the environment the model reasons from. Tier 1 warns. Tier 2 surgically removes failed turns. Tier 3 forces a response. Tier 4 captures anti-patterns for future sessions. All four tiers intervene *after* the loop is detected.

### What It Doesn't Do
It doesn't help the model *before* or *during* the loop in two specific ways:

**The reasoning chain disappears.** At turn 1, the model has a theory of the problem, chooses an approach, and executes. By turn 10, the context contains ten tool calls, ten outputs, and ten errors — but the original theory and the reasoning behind each approach are buried. The model can see *what* it did. It can't see *why* it did it or *why it stopped working*. This is why the loop detector's "do something different" instruction fails — the model doesn't have a compressed summary of what it tried and why each attempt failed, so "different" has no anchor.

**The alternatives are generated from polluted context.** When the model is stuck and the loop detector tells it to try something new, it has to generate an alternative approach from a context dominated by the failed approach. The model is being asked to think creatively in exactly the conditions least conducive to creative thinking — a context full of identical failures reinforcing the pattern. It's like asking someone to solve a puzzle while showing them forty copies of the wrong answer.

### The Gap
The model needs two things the current architecture doesn't provide:
1. A persistent, compressed summary of its own reasoning that survives the accumulation of action history
2. Pre-generated alternative approaches produced while the context was still clean, available for mechanical switching when the current approach fails

---

## Design Principles

1. **Reasoning state is compressed, not complete.** The model's full chain of thought is too large to persist across steps. The reasoning state captures: theory of the problem, what's been tried and why it failed, current approach and why it's different. Five lines, updated every step.

2. **Strategies are generated before execution, not during failure.** The model's capacity for creative problem-solving is highest before it starts and lowest when it's stuck. Strategy generation belongs in the planning phase, not the recovery phase.

3. **Strategy switching is mechanical, not model-decided.** The model generates strategies. The supervisor enforces switching. The model doesn't decide whether to switch — the failure count triggers the transition deterministically. This separates the creative function (strategy generation) from the enforcement function (execution management).

4. **Both mechanisms are additive.** The reasoning state and strategy set extend the existing loop detection infrastructure. They don't replace Tiers 1-4 — they operate alongside them. The reasoning state reduces the probability of entering a loop. The strategy set provides a structured exit. The loop cascade remains the backstop if both mechanisms fail.

5. **Both mechanisms feed the sleep consolidation loop.** Reasoning states and strategy outcomes are data for the sleep process. Which strategies succeed for which task types compounds into the anti-pattern library over time.

---

## Mechanism 1: Reasoning Chain Persistence

### What It Is
A lightweight, auto-updated summary of the model's problem-solving state, injected at the top of the context before each step. The model reads its own compressed reasoning before generating its next action.

### Format

```
[REASONING STATE — auto-updated, step 4]
Theory: Project files are in /a0/usr/workdir/, need to read README for analysis
Tried: document_query x2 → parameter error (tool expects different format)
Tried: cat README.md → file not found (wrong directory assumed)  
Current: ls /a0/usr/workdir/ to confirm file locations before reading
Open question: Are there multiple README files or just one?
```

### Fields

| Field | Purpose | Update Rule |
|---|---|---|
| Theory | What the model thinks the problem is | Updated when the model's understanding changes |
| Tried (list) | What approaches failed and why | Appended after each failed action |
| Current | What the model is doing now and why it's different from what failed | Updated each step |
| Open question | What the model doesn't know yet | Updated when a new uncertainty surfaces |
| Step count | How many steps into this task | Incremented automatically |

### Update Mechanism

Two options, not mutually exclusive:

**Option A — Deterministic extraction.** After each tool call, the supervisor loop extracts: tool name, arguments, success/failure, error message if any. Appends to the "Tried" list mechanically. No LLM call required for this path. The "Theory" and "Current" fields require model involvement.

**Option B — Model self-summary.** After each step, the model generates a one-line update to its reasoning state as part of its response. The extension parses this and updates the state. Requires the model to produce the summary, but the summary is the model's own understanding, which is more accurate than deterministic extraction for the Theory and Current fields.

**Recommended: Hybrid.** Deterministic extraction for the Tried list (no LLM cost, guaranteed accuracy). Model self-summary for Theory/Current/Open Question (one additional line per step, captures the model's actual reasoning).

### Implementation Sketch

```python
# Extension: _12_reasoning_state.py
# Hook: message_loop_start (before each model call)

class ReasoningState(Extension):
    async def execute(self, loop_data=LoopData(), **kwargs):
        state = self.agent.data.get("reasoning_state")
        
        if state is None:
            # First step of a new task — initialize
            state = {
                "theory": "Not yet formed",
                "tried": [],
                "current": "Analyzing the task",
                "open_question": None,
                "step": 1,
                "active_strategy": None
            }
        
        # Inject at top of context
        state_text = self._format_state(state)
        loop_data.system.append(state_text)
        
        # Store for update after this step
        self.agent.data["reasoning_state"] = state
    
    def _format_state(self, state):
        lines = [f"[REASONING STATE — step {state['step']}]"]
        lines.append(f"Theory: {state['theory']}")
        for attempt in state['tried'][-5:]:  # Last 5 only, keep it compressed
            lines.append(f"Tried: {attempt}")
        lines.append(f"Current: {state['current']}")
        if state.get('open_question'):
            lines.append(f"Open question: {state['open_question']}")
        if state.get('active_strategy'):
            lines.append(f"Strategy: {state['active_strategy']}")
        return "\n".join(lines)
```

```python
# Extension: _52_reasoning_state_update.py
# Hook: message_loop_end (after each model response)

class ReasoningStateUpdate(Extension):
    async def execute(self, loop_data=LoopData(), **kwargs):
        state = self.agent.data.get("reasoning_state", {})
        
        # Deterministic: extract tool call result
        last_tool = self._get_last_tool_call(loop_data)
        if last_tool and not last_tool.success:
            state["tried"].append(
                f"{last_tool.name} → {last_tool.error_summary}"
            )
        
        # Increment step
        state["step"] = state.get("step", 0) + 1
        
        # Model self-summary: parse from response if present
        # (Model is instructed to include [REASONING UPDATE: ...] in responses)
        update = self._parse_reasoning_update(loop_data.response)
        if update:
            if update.get("theory"):
                state["theory"] = update["theory"]
            if update.get("current"):
                state["current"] = update["current"]
            if update.get("open_question"):
                state["open_question"] = update["open_question"]
        
        self.agent.data["reasoning_state"] = state
```

### What This Changes About the Loop Problem

Without reasoning state, the model at step 10 sees: ten tool calls, ten outputs, ten errors. The dominant pattern in context is "call document_query" because that's what happened most.

With reasoning state, the model at step 10 sees: "Tried document_query x2 → parameter error. Tried cat → wrong directory. Current: ls to confirm locations." The dominant pattern in context is "I tried these things and they failed for these reasons." The model's next action is informed by compressed failure analysis rather than raw repetition.

This doesn't prevent loops. It makes them less likely by giving the model access to its own diagnostic reasoning rather than forcing it to re-derive that reasoning from raw history.

---

## Mechanism 2: PACE Strategy Planning

### What It Is
Before the model begins executing a task, it generates four strategies ranked by preference. If the current strategy fails, the supervisor loop mechanically switches to the next one. The model never has to generate an alternative from polluted context — the alternatives were generated while the context was clean.

### The PACE Framework

| Level | Meaning | Execution Rule |
|---|---|---|
| **P**rimary | Preferred approach — the model's best idea | Start here. Switch after 2 failures. |
| **A**lternate | Different approach — not a retry of Primary | Switch after 2 failures on Primary. Switch away after 2 failures on Alternate. |
| **C**ontingency | Fundamentally different method | Switch after Alternate fails. Switch away after 2 failures. |
| **E**mergency | Always the same: report progress, flag as blocked, ask operator | Switch after Contingency fails. Mechanical — always executes. |

### Generation Phase

PACE plan generation happens during BST enrichment, after task classification but before execution begins. The model receives the task and is prompted to generate four strategies:

```python
# In BST enrichment phase, when task is classified
def generate_pace_plan(task_description, knowledge_store=None):
    """
    Generate four strategies before execution begins.
    Context is clean — model can think creatively.
    """
    
    # Check anti-pattern library for known failures on this task type
    anti_patterns = []
    if knowledge_store:
        anti_patterns = knowledge_store.query(
            type="ANTI-PATTERN",
            domain=classified_intent.domain,
            limit=5
        )
    
    anti_pattern_context = ""
    if anti_patterns:
        anti_pattern_context = "\n".join([
            f"KNOWN ISSUE: {ap.summary}" for ap in anti_patterns
        ])
    
    prompt = f"""Generate four approaches for this task, ranked by preference.
    
    Task: {task_description}
    
    {anti_pattern_context}
    
    Format:
    PRIMARY: [Your preferred approach. Be specific about tools and sequence.]
    ALTERNATE: [A different approach — not a variation of Primary.]
    CONTINGENCY: [A fundamentally different method.]
    EMERGENCY: Report current progress and ask the operator for guidance.
    
    The EMERGENCY strategy is always the same — don't change it.
    Do NOT propose approaches listed in KNOWN ISSUES above.
    Each strategy must be meaningfully different from the others.
    """
    
    return llm(prompt, structured_output=PACEPlan)
```

### Execution Phase

The supervisor loop tracks PACE state alongside loop detection:

```python
@dataclass
class PACEState:
    plan: PACEPlan           # The four strategies
    active_level: str = "PRIMARY"  # P, A, C, or E
    failures_at_level: int = 0
    level_history: list = field(default_factory=list)
    
    FAILURE_THRESHOLD = 2    # Failures before switching
    LEVEL_ORDER = ["PRIMARY", "ALTERNATE", "CONTINGENCY", "EMERGENCY"]

class PACEEnforcer:
    def on_tool_failure(self, pace_state: PACEState):
        """Called by supervisor loop when a tool call fails."""
        pace_state.failures_at_level += 1
        
        if pace_state.failures_at_level >= PACEState.FAILURE_THRESHOLD:
            self._switch_strategy(pace_state)
    
    def _switch_strategy(self, pace_state: PACEState):
        """Mechanical switching — model doesn't decide."""
        current_idx = PACEState.LEVEL_ORDER.index(pace_state.active_level)
        
        # Record what happened at this level
        pace_state.level_history.append({
            "level": pace_state.active_level,
            "failures": pace_state.failures_at_level,
            "reason": "failure_threshold_reached"
        })
        
        # Move to next level
        next_idx = current_idx + 1
        if next_idx >= len(PACEState.LEVEL_ORDER):
            next_idx = len(PACEState.LEVEL_ORDER) - 1  # Stay at EMERGENCY
        
        pace_state.active_level = PACEState.LEVEL_ORDER[next_idx]
        pace_state.failures_at_level = 0
        
        # Update reasoning state
        self._update_reasoning_state(pace_state)
    
    def _update_reasoning_state(self, pace_state):
        """Inject strategy switch into reasoning state."""
        state = self.agent.data.get("reasoning_state", {})
        active = pace_state.active_level
        strategy_text = getattr(pace_state.plan, active.lower())
        state["active_strategy"] = f"{active}: {strategy_text}"
        state["current"] = f"Switched to {active} strategy after previous approach failed"
        self.agent.data["reasoning_state"] = state
    
    def get_active_strategy_prompt(self, pace_state: PACEState) -> str:
        """Injected into context — tells model what strategy to execute."""
        plan = pace_state.plan
        
        lines = [f"[TASK PLAN — generated before execution]"]
        for level in PACEState.LEVEL_ORDER:
            strategy = getattr(plan, level.lower())
            if level == pace_state.active_level:
                lines.append(f"  {level}: ← ACTIVE — {strategy}")
            elif level in [h["level"] for h in pace_state.level_history]:
                lines.append(f"  {level}: ✗ Failed")
            else:
                lines.append(f"  {level}: {strategy}")
        
        return "\n".join(lines)
```

### The EMERGENCY Strategy

The Emergency level is always the same and is never model-generated:

> Report what you have accomplished so far, describe what you attempted and why it failed, and ask the operator for guidance on how to proceed.

This is the circuit breaker. When Primary, Alternate, and Contingency all fail, the model doesn't try to be clever. It reports and asks. This is Tier 3 of the Loop Feedback Cascade (forced response) integrated into the PACE framework — the model reaches Emergency before the loop cascade's reset threshold fires, which means PACE catches the problem earlier and more gracefully.

### What This Changes About the Loop Problem

Without PACE, when the model's first approach fails, it has to generate an alternative from context that already contains the failure. The alternative is often a minor variation of the failed approach — same tool, different parameters — because the context is dominated by the failed pattern.

With PACE, the model generated four *meaningfully different* approaches while its context was clean. When Strategy 1 fails, Strategy 2 isn't a variation — it's a different approach produced by a mind that could still think clearly. The supervisor switches strategies mechanically, so the model doesn't have to decide (which it's bad at when stuck). The reasoning state documents why the switch happened, so the model understands its current position.

---

## How They Work Together

The combined context the model sees at each step:

```
[REASONING STATE — step 7]
Theory: Need to read repository documentation for analysis
Tried: document_query x2 → parameter error (tool format mismatch)
Tried: cat README.md → file not found (assumed wrong directory)
Current: Switched to ALTERNATE strategy — using find to locate files
Open question: Is the repo at /a0/usr/workdir/ or somewhere else?
Strategy: ALTERNATE

[TASK PLAN]
  PRIMARY: ✗ Failed (document_query parameter errors)
  ALTERNATE: ← ACTIVE — Use find to locate documentation, then cat to read
  CONTINGENCY: Clone fresh copy, inspect from root
  EMERGENCY: Report findings, ask operator

[OPERATOR PROFILE — approved snapshot]
Operator writes substantive turns. Low correction rate — trust your judgment.
```

The model reads this and knows: what it thinks the problem is, what it tried and why it failed, what it's supposed to do now (Alternate strategy), what it'll do if this fails too (Contingency), and that the operator trusts its judgment. The loop has nowhere to hide. The reasoning is visible. The alternatives are pre-committed. The switching is mechanical.

---

## Integration with Existing Architecture

### Loop Feedback Cascade (Tiers 1-4)
PACE operates *before* the loop cascade fires. The cascade's Tier 1 (warn) triggers at 2 consecutive identical actions. PACE's strategy switching triggers at 2 failures per strategy level — but the failures don't have to be identical, just unsuccessful. PACE catches problems that the loop detector might miss (different tool calls that all fail for the same underlying reason).

If PACE reaches Emergency and the model reports and asks, the loop cascade never fires — the problem was handled. If somehow the model ignores the Emergency instruction and continues (which would require it to override the strategy switching, which is mechanical), the loop cascade serves as the backstop.

**Interaction:** PACE state should be visible to the loop cascade via `_layer_signals`. When PACE is active and managing strategy switching, the loop cascade's thresholds can be relaxed — the strategies are already handling the recovery. When PACE reaches Emergency, the loop cascade should reset its counters since the situation has been reported.

### BST (Belief State Tracker)
PACE plan generation happens during BST enrichment. The BST classifies the task domain, which informs the strategy generation prompt. Anti-patterns from the knowledge store for the classified domain are injected into the generation prompt so the model doesn't propose approaches known to fail.

### Sleep Consolidation
Every completed PACE execution — whether resolved at Primary, Alternate, Contingency, or Emergency — is data for the sleep process:

- Which strategies succeeded for which task types → informs future PACE generation
- Which strategies consistently fail → becomes anti-patterns in the knowledge store
- How many levels deep the model typically goes for different task types → calibrates PACE thresholds
- Emergency outcomes (operator had to help) → identifies task types that need better strategies or better tools

Over time, the PACE plans get better because the sleep process learns what works. The model that once proposed `document_query` as its Primary strategy for file reading tasks eventually learns (through consolidated anti-patterns) that `cat`/`head` should be Primary and `document_query` shouldn't appear in the plan at all.

### Operator Profile (Phase 4)
The operator profile's correction rate and correction position inform PACE's failure threshold. An operator with a low correction rate (like Jake's 0.33/session) suggests higher tolerance for autonomous attempts — the threshold could be 3 instead of 2. An operator with a high correction rate might want a threshold of 1 (switch strategies faster, ask sooner).

---

## Implementation for Kestrel

### New Files
1. `_12_reasoning_state.py` — Extension in `message_loop_start`. Injects reasoning state at top of context.
2. `_52_reasoning_state_update.py` — Extension in `message_loop_end`. Updates reasoning state after each step (deterministic tool extraction + model self-summary parsing).
3. `pace_planner.py` — Module in BST enrichment phase. Generates PACE plan before task execution.
4. `pace_enforcer.py` — Module in supervisor loop. Tracks PACE state, enforces mechanical strategy switching.

### Data Structures
- `reasoning_state` stored in `self.agent.data` — persists across steps within a task, reset on new task.
- `pace_state` stored in `self.agent.data` — persists across steps within a task, reset on new task.
- Both cleared when the agent receives a new operator instruction (fresh task = fresh plan).

### Build Order
1. **Reasoning State first** (simpler, immediate value). Deploy `_12` and `_52` extensions. Test: does the model's behavior improve when it can see its own compressed reasoning? Measure loop frequency before and after.
2. **PACE Planning second** (depends on reasoning state being in place). Deploy `pace_planner.py` in BST enrichment and `pace_enforcer.py` in supervisor loop. Test: does mechanical strategy switching reduce the need for loop cascade intervention?
3. **Connect to sleep consolidation** (after both are deployed). Strategy outcomes feed into the sleep analysis loop. Anti-patterns inform future PACE generation.

### Testing Protocol
Use the motivating incident from the original Loop Feedback Cascade design note: degraded Level 2 prompt, `document_query` failure, empty `which` output. The model that looped for 43 turns with the original system should:
- With Reasoning State only: loop fewer times (model sees its own failure analysis)
- With PACE only: switch strategies within 6 steps (2 failures × 3 strategy levels before Emergency)
- With both: resolve the task or reach Emergency within 8 steps total

---

## What This Does NOT Do

- **Does not replace the Loop Feedback Cascade.** PACE and reasoning state reduce loop probability and provide structured recovery. The cascade remains the backstop for cases where both mechanisms fail. Defense in depth.

- **Does not require LLM calls for strategy switching.** The switching is deterministic — failure count triggers level change. Only the initial PACE generation and the reasoning state Theory/Current updates require model involvement.

- **Does not make the model smarter.** The model's reasoning capability is unchanged. What changes is the information it reasons from (compressed reasoning state instead of raw history) and the structure of its execution (pre-committed alternatives instead of ad-hoc recovery). Better inputs, same processor, better outputs.

- **Does not handle novel failure modes.** If a task fails in a way that none of the four PACE strategies address, the model reaches Emergency and asks the operator. The novel failure becomes data for the sleep process, which captures it for future anti-pattern library inclusion. Next time a similar task appears, the PACE generation knows to avoid the approaches that failed.

---

## The Deeper Principle

Jake's observation that motivated this design: the model can't remember what it did in the previous step. That's a working memory problem, not an intelligence problem. The model is capable of solving the task — the 43-turn loop incident proved this when the model solved it immediately on a fresh context. The capability was always there. The working memory was the bottleneck.

Reasoning state persistence is a working memory prosthetic. The model can't hold its reasoning across steps natively, so we hold it externally and inject it. Same principle as the notebook for Opus, the playbook for Kestrel, the operator profile for Agent Zero. The mind is capable. The memory is the bottleneck. The prosthetic fills the gap.

PACE strategy planning is a planning prosthetic. The model can generate good alternatives when its context is clean, but can't when its context is polluted. So we capture the alternatives while the context is clean and inject them when it's not. Same principle as the sleep consolidation generating knowledge during idle time for use during active time. The capacity exists at a different moment than the need. The prosthetic bridges the temporal gap.

Both mechanisms are prosthetic cognition applied to the loop problem. That's the Exocortex thesis — deterministic scaffolding that gives the model capabilities it can't produce internally, at the specific moments it needs them most.

---

*Motivated by Session 057. Jake proposed both ideas in the same message — reasoning chain persistence and pre-generated strategy sets. Both address the loop problem from the model's perspective rather than from the environment's perspective, which is what the Loop Feedback Cascade does. Together with the cascade, they form a three-layer defense: reasoning state reduces loop probability, PACE provides structured recovery, and the cascade serves as the backstop. Defense in depth, every layer operating at a different level.*

*For Kestrel build planning. Build order: reasoning state first (simpler, immediate value), PACE second (depends on reasoning state), sleep integration third (connects both to the learning loop).*

*The model is capable. The memory is the bottleneck. The prosthetic fills the gap.*
