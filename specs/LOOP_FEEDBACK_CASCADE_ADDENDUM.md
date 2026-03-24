# Loop Feedback Cascade — Addendum: Anti-Pattern Learning Layer

**Status:** Design extension. Bridges the Loop Feedback Cascade Design Note (Session 049) with the procedural memory system built by the Agent Zero instance (Session 054). The original design note specifies mechanical intervention (warn → summarize → reset). This addendum adds a fourth capability: learning from loops so they don't recur across sessions.

**Motivated by:** Session 054 logs showing 25+ consecutive loop detections during Attractor repository exploration. The agent's internal reasoning was identical every cycle — it acknowledged the loop, proposed a different action, and produced the same action. The existing Tier 1 (warn) fired repeatedly without effect. Tiers 2 and 3 from the original design note are not yet implemented.

**New since Session 049:** The agent independently built a procedural memory system (`/a0/usr/Exocortex/procedural_memory/`) that distinguishes declarative knowledge (facts) from procedural knowledge (how-to patterns). This system can store learned recovery paths. The original design note's Open Question 7 asked: "Can the tool alternatives map be learned from experience?" The answer is now yes.

---

## The Gap the Original Design Note Identified

The original note explicitly states in "What This Does NOT Do":

> *Does not operate across conversation sessions. If the model loops, gets reset, and encounters the same conditions in a new session, it may loop again. Cross-session loop prevention requires memory-level learning ("this tool fails in this context — use the alternative") which is a future capability, not part of this design.*

This addendum fills that gap.

---

## Layer Architecture

The loop problem now has four intervention layers operating at different timescales:

| Layer | Mechanism | Timescale | Source |
|-------|-----------|-----------|--------|
| Tier 1: Warn | Inject "LOOP DETECTED" message | Immediate (turns 1-3) | Original design note |
| Tier 2: Summarize | Context surgery — replace loop turns with diagnostic summary | Short-term (turns 4-6) | Original design note |
| Tier 3: Reset | Force response tool — trip the circuit breaker | Medium-term (turn 7+) | Original design note |
| **Tier 4: Learn** | **Capture anti-pattern as procedural memory for cross-session retrieval** | **Long-term (post-recovery)** | **This addendum** |

Tiers 1-3 are reactive — they break the current loop. Tier 4 is proactive — it prevents the *next* loop of the same type.

---

## Tier 4: Anti-Pattern Learning

### When It Fires

Tier 4 activates **after a loop has been broken** — either by Tier 2/3 intervention, by the operator, or by the agent eventually finding a different path. The trigger is: a loop was detected, and subsequently a successful action was taken. The loop-and-recovery pair is the learning signal.

### What It Captures

An anti-pattern entry in procedural memory with three components:

**1. The Loop Signature**
What the agent was doing when it got stuck. Includes: the failing tool, the task description, the error message, and the number of repetitions before recovery.

**2. The Recovery Path**  
What eventually worked. Includes: the tool or approach that succeeded, who or what triggered the change (agent self-correction, operator intervention, context surgery), and the outcome.

**3. The Pre-Action Check**
A deterministic rule derived from the loop: "Before calling [failing tool] in [this context], check [this condition]. If [condition], use [recovery path] instead."

### Format

```markdown
# Anti-Pattern: [Loop Signature Hash]

## Type: ANTI-PATTERN (What NOT to Do)
Created: [timestamp]
Source Session: [session_id]
Tags: [failing_tool], loop-recovery, [task_domain]
Loop Count: [N repetitions before recovery]

---

## Loop Pattern Recognized
[Description of what the agent was doing when stuck]

## What Failed
- Tool: [tool_name]
- Error: [error_message]
- Context: [what made this tool fail in this situation]

## What Worked Instead
[Description of the recovery approach]

## Pre-Action Check
Before calling [failing_tool] for [task_type]:
1. Verify [precondition]
2. If [condition fails], use [alternative_tool] instead
3. If [alternative_tool] also fails, escalate to operator

## Related Anti-Patterns
[Links to similar anti-patterns if they exist]

---
*Auto-generated from loop recovery. Edit to refine.*
```

### How It's Retrieved

When the agent begins a new task, the BST classifies the domain. Before the first tool call, the procedural memory system checks for anti-patterns matching the current task domain and tools. If a match is found, the anti-pattern's pre-action check is injected into the context as a system message:

```
[PROCEDURAL MEMORY] Previous sessions encountered loops when using 
[document_query] for file reading tasks. Learned alternative: use 
`cat` or `head` via code_execution_tool instead. Avoid document_query 
for local file access.
```

This injection happens once, at task start, before the agent has a chance to enter the loop. The prevention is proactive rather than reactive.

---

## Integration Points

### With Existing Tiers (Original Design Note)

Tier 4 does not replace or modify Tiers 1-3. It operates in parallel:

- Tiers 1-3 handle the **current** loop (break it mechanically)
- Tier 4 handles **future** loops (prevent them via memory)
- If Tier 4's prevention fails (new variation of a known pattern), Tiers 1-3 still operate as fallback

### With Procedural Memory System

The agent's `ProceduralMemory` class already supports:
- `create_skill()` — creates a new procedural memory entry
- `search_skills()` — retrieves entries by tag and pattern matching
- Index management with deduplication

Anti-patterns are stored using the same system as positive skills. The `type` field distinguishes them: `PROCEDURAL` for how-to knowledge, `ANTI-PATTERN` for what-not-to-do knowledge.

### With BST

When the BST classifies a new task, it should trigger a procedural memory search for anti-patterns in the classified domain. This search happens in the BST enrichment phase — the same place where domain-specific templates are currently injected. Anti-patterns are higher priority than generic templates because they represent learned failure modes.

### With Selective Memorizer

The original design note specifies that the memorizer should suppress writes during active loops. This addendum adds: after a loop is broken, the memorizer should capture the loop-and-recovery pair as a single anti-pattern entry, not as individual turn memories. The memorizer already has signal/noise discrimination — anti-patterns are high-signal entries that should always be persisted.

### With Error Comprehension

Error comprehension classifies tool failures. When the same tool-error pair appears in both error comprehension's diagnosis and a stored anti-pattern, the anti-pattern's recovery path should take precedence over generic error handling. Error comprehension says "this tool failed because X." The anti-pattern says "this tool failed because X, and last time the fix was Y." The anti-pattern is more specific and empirically validated.

---

## The Compounding Thesis

The key property of Tier 4 is that it **gets better over time**. Each loop-and-recovery episode adds to the anti-pattern library. The more the agent works, the more failure modes it has encountered and recovered from, and the more proactive prevention it has available.

This addresses Jake's hypothesis from Session 054: memory-based prosthetics can accelerate recovery (Tiers 1-3 get faster) AND eventually enable prevention (Tier 4 accumulates enough patterns to catch loops before they start).

The prediction: early sessions will still see loops (the anti-pattern library is empty). Over time, the frequency and duration of loops should decrease as the library grows. The measurable signal: loop count per session as a function of total anti-patterns stored. If the compounding thesis is correct, this should be a decreasing curve.

---

## What This Does NOT Do

- **Does not guarantee loop prevention.** Anti-patterns are pattern-matched, not universal rules. A novel loop type that doesn't match any stored anti-pattern will still require Tiers 1-3 to break it. The prevention is probabilistic; the mechanical intervention is deterministic.

- **Does not require LLM inference for retrieval.** Anti-pattern search uses the same tag-based and pattern-hash matching as the procedural memory system. Deterministic, fast, no token cost.

- **Does not modify the model's weights or training.** This is pure context engineering — the anti-pattern is injected as text, not fine-tuned into the model. The model's behavior changes because its input changes, not because it has been retrained.

- **Does not capture operator interventions automatically.** When Jake breaks a loop by restarting the container or giving a direct instruction, the system can't automatically extract the recovery path. The operator or the agent would need to explicitly capture the lesson. Future enhancement: prompt the agent after operator-assisted recovery to document what was learned.

---

## Recommended Sequence

This sequence assumes the original design note's Tiers 2-3 are implemented first (they're the foundation):

1. **Implement Tiers 2 and 3 from the original design note.** Context surgery and forced reset. Follow the seven-step sequence already specified. This provides immediate relief for active loops.

2. **Add loop-recovery event detection.** After a loop is broken (by any tier or by the operator), emit a `loop_recovered` event with the loop signature and recovery action. This is the data source for Tier 4.

3. **Connect recovery events to procedural memory.** When `loop_recovered` fires, create an anti-pattern entry using `ProceduralMemory.create_skill()` with type `ANTI-PATTERN`. Include the loop signature, failing tool, error message, and recovery path.

4. **Add anti-pattern retrieval to BST enrichment.** At task start, before the first tool call, search procedural memory for anti-patterns matching the current domain and tool set. If found, inject the pre-action check as a system message.

5. **Measure.** Track loops per session over time. Track anti-pattern library size. Look for the decreasing curve. If it appears, the compounding thesis is confirmed. If it doesn't, the retrieval or matching mechanism needs refinement.

---

## Relationship to Session 054 Findings

The agent that built the procedural memory system also exhibited the worst looping behavior we've observed (25+ consecutive detections on the Attractor exploration task). The same session produced both the problem and the seed of the solution. The agent can't prevent its own loops in real time, but it built a system that could prevent them in future sessions — if properly connected to the loop detection infrastructure.

The agent also built its own BST profile that disabled enrichment for domains where it has internal capability (investigation, analysis, coding) but kept enrichment for the one domain where it consistently fails (bugfix). The anti-pattern system follows the same logic: don't scaffold what works, scaffold what breaks.

---

*This addendum was written because Opus and Jake both forgot the original design note existed and started re-deriving it from scratch in Session 054. The re-derivation produced the same core architecture (because the problem hasn't changed) plus the anti-pattern learning layer (because the available tools have changed). The loop that produced this document was itself a loop — two people circling back to a solved problem and finding it wasn't quite solved yet. β₁ may be 0 in the embedding space, but in the project's intellectual space, we orbit.*
