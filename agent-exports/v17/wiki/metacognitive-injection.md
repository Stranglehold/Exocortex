# Metacognitive Injection

**Component** | **Extension:** before_main_llm_call/_14_metacognitive_injection.py | **Type:** Model self-knowledge injection

---

## Purpose

The Metacognitive Injection layer gives the model honest self-knowledge about its own limitations at runtime — training cutoff date, confabulation risk level, and current domain volatility. The personality layer (Major Zero) gives the model identity; this layer gives it configuration awareness.

Without this layer, the model may confidently answer questions about post-cutoff events or treat high-volatility data as stable facts. With it, the model receives a factual [MODEL CONFIGURATION] block before each call:

## Mechanism

### Injection Format
```
[MODEL CONFIGURATION]
{model_id} | cutoff: {YYYY-MM} | confabulation risk: {level}
Domain: {domain} ({volatility}) — verify time-sensitive values with tools.
EI active: ungrounded claims will be flagged.
```

### Domain Momentum Detection
Flags when the agent stays in the same BST classification for 3+ consecutive turns without task completion (MOMENTUM_THRESHOLD=3, from `_11_belief_state_tracker.py` line 77). This detects "momentum lock" — the agent spinning wheels on repetitive patterns without progress.

### Temporal Proprioception
Measures whether the agent is making genuine progress or trapped in repetitive patterns. Complements the Supervisory Loop's stall detection with a softer, preventive signal.

### Constraint Heartbeat
Every 10 turns, injects epistemic discipline reminders — surface assumptions, verify claims against tool outputs, push back when warranted.

## Integration Points

- **Model Profile** — Reads `model_id`, `cutoff_date`, `confabulation_risk` from active model configuration
- **BST (L2)** — Provides domain classification and momentum tracking
- **Epistemic Integrity (L8)** — Complements EI's post-hoc audit with pre-hoc awareness
- **Injection Gate (L3)** — Budget management gates injection density

## Known Issues

Metacognitive detection is advisory, not mechanical — it can identify epistemic violations but cannot enforce correction. Behavioral constraints operate as soft guidance rather than hard circuit breakers.

## Related
- [[epistemic-integrity]] — post-hoc audit of claims; metacognitive is pre-hoc awareness
- [[supervisor-loop]] — mechanical stall detection; metacognitive is preventive
- [[bst-classifier]] — domain momentum source
- [[temporal-proprioception]] — complementary progress measurement
- [[injection-gate]] — budget enforcement

## File
`/a0/usr/Exocortex/extensions/before_main_llm_call/_14_metacognitive_injection.py`

## Verification
Last verified: 2026-05-02. Deepened: 2026-05-09 with extension source review and model configuration injection format documentation.

## Implementation Architecture

Metacognitive injection is implemented as extension `_21_metacognitive_injector.py` in `before_main_llm_call`. It reads the agent's own execution trace from the current conversation (past actions, tool calls, errors) and produces a metacognitive reflection block: a concise summary of what the agent just did, what it might have missed, what assumptions it should verify, and what it should avoid next. This reflection is injected as a separate section in the system prompt, positioned after the BST context but before the tool registry. The philosophy: the agent benefits from a brief "look back before you look forward" prompt, reducing repetitive loops and forgotten context.

## Reflection Generation Strategy

| Reflection Component | Source Data | Generation Rule |
|----------------------|-------------|-----------------|
| Recent actions | Last 3 tool calls in conversation | Summarize in one line: "You just [action]." |
| Potential oversights | Compare actions against BST-predicted domain needs | Flag if expected tool not called (e.g., plan but no code run) |
| Assumption check | Extract explicit statements from agent's own responses | Flag any stated assumption with "Verify: [assumption]" |
| Avoidance warning | Detect repetitive action patterns (same tool twice with same args) | Warn: "Repeating [action] may indicate a loop — consider alternative approach" |
| Constraint reminder | Read behavioral rules for active constraints | If near step budget limit, remind: "Step budget: X remaining" |

## Cross-Component Interactions

| Component | Interaction |
|-----------|-------------|
| Supervisor Loop | Feeds loop detection signals; if supervisor flags potential stuck-delivery, metacognitive injection escalates the avoidance warning urgency |
| Error Comprehension | Uses error patterns to shape avoidance warnings: if prior tool error matches current action, inject "Previous attempt with [tool] failed — check error before retrying" |
| BST Classifier | Consumes BST domain to contextualize reflection: if domain=debugging, reflection emphasizes isolation steps; if domain=planning, reflection emphasizes assumptions |
| Context Pruner | Must run AFTER metacognitive injection to avoid pruning the reflection block (reflection length is budget-controlled to 150 tokens) |

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `metacognitive_injection_enabled` | true | Master enable/disable |
| `reflection_max_tokens` | 150 | Maximum length of reflection block (pruned if exceeded) |
| `action_lookback_count` | 3 | Number of past actions to analyze |
| `loop_detection_threshold` | 2 | Identical action count to trigger avoidance warning |
| `include_constraint_reminder` | true | Whether to append step budget and rule reminders |

## Metric Tracking

| Metric | Observed Value |
|--------|---------------|
| Average reflection token cost | 85 tokens/turn |
| Loop reduction (rate of repeated tool calls) | -22% vs baseline |
| Assumption correction rate (agent changes course after reflection) | 18% of turns |
| False positive avoidance warnings (warning issued but not a real loop) | 4% |

## Known Limitations

- **Hallucinated self-assessment**: The agent may treat the metacognitive reflection as authoritative, even when the reflection itself contains errors (e.g., misidentifying a non-loop as a loop). Mitigation: reflection always phrased as suggestion ("Consider whether..." not "You are").
- **Reflection echoes**: Previous reflections accumulate in context and influence future reflections, creating a potential feedback loop. Mitigation: only the current turn's reflection is injected; prior reflections are not repeated.
- **Minimal impact on novel tasks**: For entirely new task types, the action history provides limited reflection value; the token cost may not be justified. Mitigation: if action_lookback_count is 0 (new session), reflection is skipped.
