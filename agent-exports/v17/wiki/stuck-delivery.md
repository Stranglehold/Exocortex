# Stuck Delivery

**Created:** 2026-04-28T05:18Z | **Deepened:** 2026-05-10T03:45Z (cycle 22)
**Component** | **Hook:** supervisor_signals | **Type:** Reactive intervention

## Purpose

Stuck Delivery detection identifies when the agent is caught in a loop attempting to deliver a response to the user but failing due to context window exhaustion, and then triggers a surgical suppression of non-essential injections to free token space and break the cycle.

## Why It Happens

The agent accumulates injection text (BST context, memory recall, tool list, skill list, supervisor guidance, etc.) that grows each turn. When the model’s response approaches the token limit:
1. The response is truncated before the final `}` of a JSON tool call, ending the turn early
2. The framework may retry or the next turn re-adds similar injections, causing repeat truncation
3. Without detection, the agent can loop indefinitely — attempting delivery, truncation, retry, truncation — until session timeout or manual kill

## Detection Signals

The stuck delivery detector monitors multiple concurrent signals:
- **Consecutive Truncations**: 3+ consecutive turns where output ended without valid JSON close
- **Idempotent Retry Content**: high cosine similarity (>0.95) between current response text and previous turn’s truncated response
- **Context Pressure**: context window utilization >85%
- **No Progress Markers**: absence of tool calls, file writes, or sub-agent invocations in recent turns (different from normal conversation turns)

When all four signals are simultaneously active, stuck delivery is declared.

## Surgical Suppression Sequence

Upon detection, the system executes a tiered suppression:

### Tier 1 — Immediate (applied mid-turn if possible, else next turn start)
1. **BST state injection halted** — domain context is already stable, no new BST enrichment needed
2. **Tool description list removed** — full tool descriptions are non-essential in stuck loop
3. **Skill list and injection guide shortened** — compress to 1-line summaries

### Tier 2 — If Tier 1 fails (next turn)
1. **Memory recall frozen** — no new memory retrievals injected
2. **Supervisor monitoring reduced** — only hard signals (imminent failure) retained, soft/medium dropped
3. **Epistemic Integrity checks disabled** — hallucination verification suspended to save tokens

### Tier 3 — If Tier 2 fails (escalation to Supervisor L3)
1. **Compressed injection mode** — only system message and user message, all injections stripped
2. **Minimal response template** — model prompted to deliver final answer in <100 tokens
3. **Cycle completion flag** — after delivery, session may be flagged for checkpoint

## Recovery and Resume

After successful delivery:
- Suppression state cleared next turn
- Injection gate resumes normal budget allocation
- BST enrichment refreshed with latest domain state
- Supervisor CUSUM reset if the stuck delivery was the cause of score accumulation

## Interaction with Context Pruner

- **[[context-pruner]]** is the proactive counterpart — it prunes injection content *before* injection to prevent context pressure
- Stuck Delivery is the reactive safety net when despite pruning, context still exhausts
- The two share a feedback loop: pruner parameters are tightened after a stuck delivery event

## Testing and Observability

- Metric: `stuck_delivery_count` per session logged to `receipts.jsonl`
- Dashboard: visible in [[nerv-dashboard]] as "Stuck Events" counter under System Health
- Simulations: can be forced by setting `context_utilization_threshold` artificially low in test harness

## Anti-Pattern: The Stuck Delivery Loop

Without detection, the agent enters infinite loop:
1. Tries to deliver → context full → truncation
2. Retries with same content → still full → truncation
3. Loses task goal in noise → starts new subtask → delivers nothing
4. Repeat indefinitely until timeout or manual kill

## Edge Cases

- **Genuine multi-turn response**: if response legitimately requires multiple tool-calls before delivery, the "no progress markers" signal prevents false detection (tool calls count as progress)
- **Temporary backend latency spike**: if truncation is due to network timeout rather than token exhaustion, context utilization signal prevents false detection
- **Explicit user pause**: if user sends "hold" or "wait", stuck detection is disabled for the subsequent turn

## Connection to Other Concepts

- **[[context-pruner]]** — upstream pruning prevents stuck delivery proactively; this is reactive fallback
- **[[supervisor-loop]]** — stuck detection feeds as hard signal into CUSUM accumulator
- **[[backend-standby]]** — if LLM endpoint dies during surgery suppression, need graceful state preservation for later resumption
- **[[injection-gate]]** — surgical suppression temporarily overrides injection gate budget to force delivery

## References

- Incident `inc-stuck-delivery-loop` documents real occurrence and root cause analysis
- Architecture spec: Exocortex injection chain documentation

## Verification Status
Last verified: 2026-05-10. Deepened cycle 22 with detection signals, surgical suppression tiers, proactive/preactive interplay, edge cases, and testability.
