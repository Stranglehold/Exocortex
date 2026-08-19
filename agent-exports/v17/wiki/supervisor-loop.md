# Supervisor Loop

## Layer
L4: Stall & Loop Detection

## Hook
`message_loop_end` — `_50_supervisor_loop.py` — runs in the `finally` block of every message loop iteration

## What It Does
The Supervisor Loop is the operational safety layer. It monitors every agent loop iteration for anomalies — stalls, loops, context exhaustion, and cascading failures — then injects corrective steering messages into the conversation history before the next model call.

Without it, local models loop endlessly: re-running completed commands, re-deriving already-answered questions, cycling through the same tool calls until context overflows.

## Anomaly Types

### 1. Stall Detection
Agent stops making progress — no new tool calls, repeated responses, or waiting on non-existent output.
- **Detection:** Message similarity across N consecutive turns exceeds threshold
- **Response:** Inject stall warning ← "You appear to be stalled. Check if the previous action completed successfully."

### 2. Loop Detection (3-Tier Escalation)
Agent repeats the same tool call or reasoning pattern:
- **Tier 1 (Warn):** Same tool called 3+ times with same args → inject warning
- **Tier 2 (Summarize):** Warnings don't help → inject summarization of what succeeded/failed, plus anti-actions
- **Tier 3 (Reset):** Agent still looping → force context reset with stark intervention message

### 3. Context Exhaustion
Model context approaching token limit:
- **Detection:** Step budget tracker + context watchdog signals
- **Response:** Inject compaction instruction, halt non-essential enrichments

### 4. Cascade Detection
Multiple different tools failing in rapid succession — not a loop, but systemic failure:
- **Detection:** N different failing tools in last M history entries
- **Response:** Diagnose pattern (permissions? network? model unloaded?) and inject corrective

### 5. Completion Boundary Loops
Model generates a complete, correct response but then re-executes the same tool call:
- **Detection:** Tool success + same tool called again within 2 turns
- **Response:** Inject anti-action ← "Do NOT call this tool again — it already succeeded"

## Key Configuration

```python
# Tier thresholds
STALL_SIMILARITY = 0.85
LOOP_TOOL_THRESHOLD = 3
CASCADE_TOOL_COUNT = 3
CASCADE_WINDOW = 5

# Tier 2 suppression: if agent hits 3+ distinct error types, it's iterating not looping
DIVERSITY_SUPPRESS_THRESHOLD = 3
```

## Loop Surgery (Tier 2-3)
When Tier 2 fires, the supervisor performs loop surgery:
1. Sets `_loop_active` flag → marks subsequent memory writes as loop-period
2. Records loop entry/exit in evidence ledger
3. On Tier 3: clears agent's working memory cache, forces fresh context
4. False recovery detector: if same tool failed post-prior-surgery → immediate Tier 3 escalation

## Integration Points
- **BST (L6)** — Domain classification used to adjust loop thresholds (code vs. investigation have different timing)
- **Injection Gate (L3)** — Supervisor can override injection budget during anomalies
- **Evidence Ledger (L8)** — Loop episodes recorded for post-hoc analysis
- **Context Watchdog (L5)** — Context exhaustion signals feed supervisor

## File
`/a0/usr/Exocortex/extensions/message_loop_end/_50_supervisor_loop.py`

## Related
- [[bst-classifier]]
- [[injection-gate]]
- [[error-comprehension]]
- [[stuck-delivery]]

## Known Limitations

1. **Cannot distinguish strategic repetition from stuck loop**: If the agent intentionally calls the same tool 3 times with identical args for batching, supervisor will intervene.
2. **Blind to model-internal reasoning**: Only action-level checks; cannot detect bad reasoning chains.
3. **Limited to tool-call JSON**: Does not parse plain-text responses for errors.

## Cross-References
- [[stuck-delivery]] — specific incident page for stuck-loop pattern
- [[injection-gate]] — how supervisor directives are delivered
- [[epistemic-integrity]] — downstream audit triggered by supervisor flags
- [[error-comprehension]] — error classification pipeline
