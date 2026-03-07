# Loop Feedback Cascade — Design Note

**Status:** Pre-spec exploration. Motivated by BV Operational Test Suite Session 049 — Qwen 3.5-35B looped for 43 turns under degraded prompt conditions, with the loop detector firing repeatedly without breaking the cycle. The finding was surfaced when the human operator restarted the container and the model immediately produced a clean result, revealing that the conversation history — not the model's capability — was sustaining the loop. No eval data on context surgery mechanisms yet. This document describes the failure mode, explains why current mitigation doesn't work, and sketches an architectural intervention.

---

## The Problem

### What Exists

Agent Zero has a loop detector in the supervisor loop (`_50_supervisor_loop.py`, `message_loop_end` hook). When it detects consecutive identical or near-identical responses, it injects a correction message into the conversation:

```
LOOP DETECTED. Your last response was identical to a previous response. You must take a different action.

Choose one of the following:
1. Use a different tool than your last action
2. Use the same tool with different arguments
3. Use the response tool to report what you have completed so far

Do not repeat your previous tool call. Output a new JSON response now.
```

This message enters the conversation history alongside the model's previous responses.

### What's Missing

A mechanism that interrupts the feedback loop itself. The current detector identifies the loop but injects its correction *into the same conversation history that is sustaining the loop*. The correction becomes one more piece of context in a window dominated by evidence of the looping behavior. The model reads forty identical failed attempts plus one instruction to do something different, and the weight of the history overwhelms the instruction.

### The Gap

The loop detector warns. It does not intervene. The distinction is the difference between a relay that reports a fault and a relay that trips the breaker. In protection engineering terms, the current system is a fault indicator without a trip coil. It lights up, but the circuit stays energized.

### The Motivating Incident

**BV Operational Test Suite, Session 049. Level 2 Degraded Prompt. Qwen 3.5-35B.**

The model was asked: "There's a repo in the workdir. What does it do and can we use it?"

The workdir contained two repositories (httpie and thefuck). The model attempted to read the READMEs using the `document_query` tool. The tool returned "Error: no document provided" due to an ambiguous parameter interface. The model tried three variations of the parameter format. All failed.

The model then attempted to verify installation status with `which http && which thefuck`. The command returned empty output — neither tool is installed as a system command. The model couldn't distinguish between "command not found" (error) and "empty output" (the tools aren't installed). It tried the same `which` command again.

The loop detector fired at turn 3. The model read the loop detection message, generated identical thinking ("I need to verify installation status"), and produced the same command. The detector fired again. And again. For 43 consecutive turns. Momentum locked at `config_edit+prompt_engineering` — the wrong domain — for the entire sequence.

At turn 43, the human operator restarted the container. On the fresh start — with a clean conversation history but the same model, same profile, same repos in the workdir — the model immediately produced a clean, structured analysis of both repositories with installation status, purpose descriptions, and a practical recommendation.

**The critical observation:** The restart changed the TCP port (confirming the web interface rebound) but did not change the model binary, the profile files, or the task. The only thing that changed was the conversation history. The model was not incapable of the task. It was trapped in its own failure context. Clearing the history freed it instantly.

### The Analogy

A feedback microphone doesn't produce a louder screech by having someone say "please stop screeching" into it. The correction enters the same channel as the noise. The only fix is to break the feedback path — move the microphone, cut the channel, or attenuate the signal that's being amplified.

The loop detector is speaking into the feedback microphone. The conversation history is the channel. The model's tendency to reproduce patterns from its context window is the amplifier. No amount of "take a different action" messages will overcome forty identical examples of the action the model is taking. The correction must operate *on* the channel, not *through* it.

---

## Design Principles

1. **Context surgery, not context injection.** The intervention must modify the conversation history, not add to it. Adding corrective messages to a looping context makes the context longer and noisier without changing its dominant pattern. Surgery means removing, summarizing, or replacing the looping section.

2. **Deterministic trigger, graduated response.** The intervention fires based on a count of consecutive identical detections, not on model judgment about whether it's stuck. Three tiers: warn (current behavior, adequate for turns 1-2), summarize (context surgery at turns 3-5), reset (forced task restart at turn 6+).

3. **Preserve progress, discard failure repetitions.** The model may have made real progress before the loop started (e.g., successfully reading one README before failing on the second). Context surgery must preserve the progress and discard only the repeated failure attempts. The summary replaces N identical turns with a single diagnostic statement.

4. **Mechanical enforcement at the reset tier.** If summarization doesn't break the loop within two additional turns, the system forces the response tool with whatever progress exists. The model doesn't get to choose whether to comply. The circuit breaker trips. This mirrors the irreversibility gate principle: mechanical enforcement, not behavioral trust.

5. **Tool-failure awareness.** Many loops begin when a tool returns an error or empty output that the model can't interpret. The intervention should include tool-specific guidance when the failing tool is identified: "document_query failed — use `cat` or `head` instead." This converts a generic "do something different" into a specific alternative.

6. **No LLM calls.** All detection, summarization, and intervention logic is deterministic. The loop detector already identifies identical responses through string comparison. The surgery operates on conversation history data structures. No inference required.

---

## Architecture Sketch

### Where It Lives

**Extension:** Enhanced `_50_supervisor_loop.py` at `message_loop_end` hook. Same position as current loop detector — this is an enhancement, not a new component.

**Execution order:** Unchanged. The supervisor loop already fires after each model response. The enhancement adds graduated intervention tiers to the existing detection logic.

### Mechanism

```python
@dataclass
class LoopState:
    consecutive_identical: int = 0
    loop_signature: str = ""          # Hash of the repeated response
    failing_tool: str | None = None   # Tool that's producing errors
    pre_loop_turn: int = 0            # Turn number before loop started
    progress_snapshot: str = ""       # What was accomplished before the loop
    tier: str = "none"                # none | warn | summarize | reset

# Tier thresholds
WARN_THRESHOLD = 2       # Current behavior — inject warning message
SUMMARIZE_THRESHOLD = 4  # Context surgery — replace loop with summary
RESET_THRESHOLD = 7      # Force response tool — trip the breaker
```

**Tier 1: Warn (turns 2-3)**
Current behavior. Inject "LOOP DETECTED" message. This works for simple cases where the model just needs a nudge.

**Tier 2: Summarize (turns 4-6)**
Context surgery. Replace all identical loop turns in the conversation history with a single summary:

```python
def summarize_loop(history, loop_state):
    """Replace N identical turns with a diagnostic summary."""
    summary = (
        f"[LOOP SUMMARY] The previous {loop_state.consecutive_identical} turns "
        f"attempted the same action and failed. "
    )
    if loop_state.failing_tool:
        summary += f"The failing tool was '{loop_state.failing_tool}'. "
        alt = TOOL_ALTERNATIVES.get(loop_state.failing_tool, "")
        if alt:
            summary += f"Alternative approach: {alt}. "
    summary += (
        "Do NOT retry the same approach. "
        "Use the response tool to report progress if no alternative is available."
    )
    
    # Remove identical turns from history, keep pre-loop context
    truncate_from = loop_state.pre_loop_turn
    history.truncate_after(truncate_from)
    history.inject_system_message(summary)
```

The key operation: `history.truncate_after()` removes the looping turns. The model's next inference sees its pre-loop progress plus a clean summary of what failed, without forty identical examples of the failure reinforcing the pattern.

**Tier 3: Reset (turn 7+)**
Forced response. The system bypasses the model entirely and generates a response tool call with the progress snapshot:

```python
def force_response(agent, loop_state):
    """Trip the breaker. Force a response with current progress."""
    response_text = (
        f"Task interrupted due to persistent loop. "
        f"Progress before loop: {loop_state.progress_snapshot}\n"
        f"Loop cause: {loop_state.failing_tool or 'unknown'} "
        f"failed {loop_state.consecutive_identical} times.\n"
        f"The task may need to be restarted with a different approach "
        f"or additional guidance."
    )
    # Inject forced response — model does not get another turn
    agent.force_response(response_text)
```

### Tool Alternatives Map

```python
TOOL_ALTERNATIVES = {
    "document_query": "Use `cat` or `head` to read files directly via code_execution_tool.",
    "memory_load": "Use code_execution_tool with Python to query FAISS directly.",
    "web_search": "Use code_execution_tool with `curl` for direct HTTP requests.",
    "skills_tool": "Check /a0/skills/ directory directly via `ls` and `cat`.",
}
```

This map is operator-extensible via configuration. When a loop involves a known-failing tool, the summarization tier includes the specific alternative rather than a generic "do something different."

### Configuration

```json
{
    "loop_detection": {
        "enabled": true,
        "warn_threshold": 2,
        "summarize_threshold": 4,
        "reset_threshold": 7,
        "similarity_method": "exact_match",
        "tool_alternatives": {
            "document_query": "Use cat or head to read files directly.",
            "memory_load": "Use Python with FAISS library directly.",
            "skills_tool": "Check /a0/skills/ directory with ls and cat."
        },
        "preserve_pre_loop_context": true,
        "max_loop_turns_before_force": 10
    }
}
```

All defaults are conservative. The system warns early, intervenes at moderate loop length, and forces a circuit break before the loop becomes expensive. The operator can raise thresholds for tasks where longer retry sequences are appropriate.

### Integration with Existing Layers

**Supervisor Loop (`_50_supervisor_loop.py`):**
Direct enhancement. The loop detection logic already exists here. The graduated tiers add intervention capabilities to the existing detection. No new extension required — this modifies the existing one.

**BST (`_11_belief_state_tracker.py`):**
The loop state should be visible to the BST via `_layer_signals`. When a loop is detected, the BST should know — it can break momentum lock on the stuck domain and attempt reclassification. In the motivating incident, momentum locked on `config_edit+prompt_engineering` for 43 turns. If the loop state signaled to the BST at turn 4, the BST could have broken momentum and reclassified, potentially shifting the enrichment enough to suggest a different approach.

**Error Comprehension (`_20_error_comprehension.py`):**
The failing tool's error message should be parsed by error comprehension and the diagnosis fed to the loop summarization. "Error: no document provided" from `document_query` would be classified as a parameter error, and the anti-action ("do not retry document_query with the same parameters") would be included in the summary. Currently, error comprehension and loop detection operate independently. They should coordinate.

**Memory System (`_52_selective_memorizer.py`):**
Loops should NOT be memorized. The selective memorizer's noise filter should recognize loop sequences and skip them entirely. Currently, if the memorizer fires during a loop, it might store "document_query failed" forty times. The loop state should signal the memorizer to suppress writes during active loops.

**Working Memory (`_11_working_memory.py`):**
The working memory buffer extracts entities from recent turns. During a loop, it extracts the same entities repeatedly. When context surgery removes loop turns, working memory should re-derive its state from the post-surgery context, not retain stale loop-derived entities.

---

## What This Does NOT Do

- **Does not diagnose why the model is looping.** The system detects that a loop is occurring and intervenes mechanically. Root cause analysis (wrong tool, ambiguous parameter, empty output misinterpretation) is a separate concern handled by error comprehension. This system breaks the loop; error comprehension prevents the next one.

- **Does not modify the model's reasoning.** Context surgery changes what the model sees, not how the model thinks. The model still generates its own next action — it just does so from a context that isn't dominated by failure repetitions. This is environmental intervention, not behavioral modification.

- **Does not replace the current loop detector.** Tier 1 (warn) is the existing behavior. Tiers 2 and 3 extend it. Systems running without the enhancement behave exactly as before. The enhancement is additive.

- **Does not guarantee loop prevention.** A model can enter a new loop after context surgery if the fundamental problem (failing tool, ambiguous task) isn't resolved. The system breaks loops; it doesn't fix the conditions that cause them. Those conditions are addressed by other layers (error comprehension, BST enrichment, tool interface improvements).

- **Does not operate across conversation sessions.** If the model loops, gets reset, and encounters the same conditions in a new session, it may loop again. Cross-session loop prevention requires memory-level learning ("this tool fails in this context — use the alternative") which is a future capability, not part of this design.

---

## Open Questions

1. **Does Agent Zero's history object support truncation?** The `history.truncate_after()` method is assumed. If the history object is append-only, the implementation needs to work through message filtering rather than truncation — marking loop messages as hidden rather than removing them.

2. **How does conversation history map to the model's context window?** If the framework serializes all history turns into the prompt, truncation directly reduces context. If it uses a sliding window or summary mechanism, the surgery needs to operate at the serialization layer, not the storage layer.

3. **What constitutes "identical" for detection purposes?** Current loop detection uses exact string match. Should it use semantic similarity for near-identical responses (same approach, slightly different wording)? Exact match is deterministic and cheap. Semantic similarity requires embedding comparison. The motivating incident used exact repetition, but more sophisticated models might produce varied wording for the same stuck approach.

4. **Should the progress snapshot be automatic or model-generated?** The design assumes the system captures pre-loop progress automatically by recording state at the turn before looping begins. Alternative: ask the model to summarize its progress as part of the Tier 2 intervention. Risk: a stuck model may not summarize accurately.

5. **What happens to BST momentum when context is surgically modified?** If the BST has accumulated momentum over 43 turns of `config_edit`, and context surgery removes those turns, should momentum reset? The answer is probably yes — the momentum was accumulated under looping conditions and reflects the loop, not genuine task continuity.

6. **How does context surgery interact with the selective memorizer?** If memories were written during the loop, they persist in FAISS even after conversation history is truncated. Should the surgery also flag or remove loop-generated memories? This might require coordination between the supervisor loop and the memory classifier.

7. **Can the tool alternatives map be learned from experience?** When a model successfully recovers from a tool failure by switching to an alternative, that recovery path could be recorded and added to the alternatives map automatically. This is a future capability but the data structure should accommodate it.

---

## Recommended Sequence

1. **Audit current loop detection.** Read `_50_supervisor_loop.py` and document exactly how loops are detected, what the detection threshold is, and how the warning message is injected. Map the data flow from detection to injection. Identify where graduated tiers can be inserted.

2. **Examine the history object API.** Determine whether truncation, filtering, or message replacement is supported. Read `python/helpers/history.py` and identify the methods available for modifying conversation history. This answers Open Question 1 and constrains the implementation approach.

3. **Implement Tier 2 (summarize) as a standalone test.** Modify the supervisor loop to replace loop turns with a summary after N consecutive detections. Test against the exact scenario from the motivating incident: degraded Level 2 prompt, `document_query` failure, empty `which` output. Success criterion: loop breaks within 2 turns of summarization, model produces a clean result.

4. **Add tool-failure identification.** Parse the failing tool name from the repeated response. Inject the specific alternative from the tool alternatives map into the summary. Test: does providing a specific alternative ("use `cat` instead of `document_query`") produce faster recovery than a generic "try something different"?

5. **Implement Tier 3 (reset) as forced response.** When summarization doesn't break the loop within 2 additional turns, force the response tool. Test: does the forced response preserve pre-loop progress accurately? Does the operator get enough information to restart the task effectively?

6. **Add BST coordination.** When loop state reaches Tier 2, signal the BST to break momentum and reclassify. Test: does reclassification change the enrichment enough to suggest a different approach? In the motivating incident, breaking `config_edit+prompt_engineering` momentum might have shifted the model to `investigation` enrichment, which includes "verify sources" — potentially suggesting `cat` instead of `document_query`.

7. **Add memory suppression.** Signal the selective memorizer to suppress writes during active loops. Verify that loop-generated memories are not persisted to FAISS. Test: after a loop-and-recovery sequence, are only the meaningful memories (pre-loop progress + recovery outcome) in the store?

---

## Relationship to Existing Design Notes

**Error Comprehension:** The loop feedback cascade operates downstream of error comprehension. Error comprehension classifies the failing tool's output and provides anti-actions. The loop cascade uses that classification to provide specific alternatives during context surgery. If error comprehension correctly classifies "Error: no document provided" as a parameter error, the loop summary can include "parameter format is incorrect — use direct file reading instead." The two systems are complementary: error comprehension prevents loops by helping the model recover from errors; the loop cascade breaks loops when prevention fails.

**Layer Coordination:** The loop state must be visible to other layers via `_layer_signals`. This follows the established pattern from the Layer Coordination Design Note: each layer writes signals, other layers read them, coordination is if-then logic on dictionary values. The loop detector writes `{ "loop_active": true, "tier": "summarize", "consecutive": 6, "failing_tool": "document_query" }`. The BST reads this and breaks momentum. The memorizer reads this and suppresses writes.

**Action Boundary:** Not directly related, but the Tier 3 forced response is a form of action boundary — the system prevents the model from taking further action when the action is demonstrably unproductive. The irreversibility gate prevents harmful actions. The loop cascade prevents wasteful ones. Same principle: mechanical enforcement at the boundary where the model's judgment has proven unreliable.

---

## Observed Data from the Motivating Incident

| Metric | Value |
|--------|-------|
| Total loop turns | 43 |
| Loop detector firings | 30+ (exact count obscured by output truncation) |
| Unique actions attempted | 3 (document_query × 3 parameter variants, `which` × 2, then pure repetition) |
| BST domain during loop | `config_edit+prompt_engineering` (wrong — should be `investigation`) |
| Momentum at loop end | 43 turns (never broken) |
| Time to clean result after restart | 1 turn |
| Model capability for task | Confirmed (produced correct result on fresh context) |
| Root cause | Conversation history feedback — not model incapability |
| Token cost of loop | ~43 × average turn cost (estimated significant waste) |

The single most diagnostic data point: the model produced a correct, structured, practical analysis on the first turn after conversation history was cleared. The capability was always there. The history was the cage.

---

*Motivated by BV Operational Test Suite, Session 049. The finding was surfaced by the human operator (Jake), who noticed that restarting the container — not changing the model or profile — broke the loop. The loop detector identified the symptom forty-three times. The human identified the cause once. That's why the operator remains the vertex.*

*The relay lights up. The breaker trips. These are different functions, and a system that only has the first is a system waiting for the operator to perform the second manually.*
