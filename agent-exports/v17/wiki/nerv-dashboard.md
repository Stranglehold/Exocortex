# NERV Dashboard

**Created:** 2026-04-28T05:18Z | **Deepened:** 2026-05-10T03:45Z (cycle 22)
**Status**: Comprehensive specification — real-time operational monitoring and operator intervention interface.
**Name origin**: NERV = Neuro-Evolution Runtime Visualization.

## Purpose

The NERV Dashboard provides the human operator a live, visual window into the agent’s internal state—context window pressure, BST confidence, supervisor CUSUM score, system health, and memory recall—without requiring log inspection or shell commands. It renders as an interactive web panel inside the chat interface via the `emit_artifact` tool.

## Overview

The dashboard aggregates real-time data from:
- **Inference Wrapper (Layer B)**: token usage, generation metrics, entropy signals
- **BST Classifier**: domain confidence, momentum, transition history
- **Supervisor Loop**: CUSUM accumulator, signal breakdown, intervention state
- **Memory System**: recall count, capacity, decay age
- **Backend Health**: endpoint latency, error rate, failover status

Data is collected via an internal metrics bus that polls these components every turn or every N seconds depending on configuration.

## Dashboard Panels

### Panel 1: System Health
- **Backend Status**: green (healthy), yellow (degraded latency), red (unreachable or error rate >5%)
- **Context Window Utilization**: percentage bar with trend line (last 20 turns)
- **Token Budget Remaining**: tokens left in current turn vs configured max, burn rate calculated overlast 5 turns
- **Memory Recall Count**: number of memory injections active vs cap (default 8), plus decay age for each
- **Injection Gate Budget**: active injection tokens vs budget (from injection-gate L3)

**Implementation**: Polls `AgentContext.get_usage()` and backend health via `backend.latency_stats()`. Context utilization computed by tracking send/receive tokens from the inference wrapper’s `context_snapshot()` method.

### Panel 2: BST State Monitor
- **Current Primary Domain**: e.g., "analysis", "code", "research" with confidence score (0-1)
- **Momentum Counter**: turns since last domain change; color-coded at 5 (yellow), 10 (orange), 15 (red)
- **Compound Signature**: when multi-domain detected, show combined label (e.g., "analysis+philosophical")
- **Domain Transition History**: last 10 domain switches with timestamps
- **Enrichment Plan Status**: shows whether primary/secondary enrichments are active or suppressed

**Implementation**: Reads BST state from `bst_classifier.get_state()`, subscribes to `domain_changed` events. Transition history stored in rolling buffer.

### Panel 3: Supervisor Score
- **CUSUM Accumulator Value**: raw number with tier thresholds marked (T1: warn, T2: surgery, T3: compressed)
- **Signal Breakdown by Severity**: soft (info), medium (warning), hard (intervention) — stacked bar
- **Last Intervention**: type, timestamp, duration, and whether it was effective
- **Time-in-State**: how long the supervisor has been at current intervention level
- **Hook Chain Order**: list of currently active injections with priority

**Implementation**: Supervisor exposes `get_cusum()`, `get_last_intervention()` methods. Signal breakdown pulled from `supervisor.signal_log`.

### Panel 4: Generation Metrics
- **Entropy Regime**: current classification (low/medium/high) with transition confidence
- **Output Token Entropy**: entropy of token distribution per generation (from `entropy-as-signal`)
- **Latency**: per-turn response time with rolling average
- **Retry Count**: number of retries due to bad output (per session)
- **Repetition Penalty**: self-repetition score (for detecting loops)

**Implementation**: Entropy data sourced from inference wrapper’s `logit_entropy` stream, categorized by thresholds defined in `entropy-as-signal` configuration.

### Panel 5: Epistemic Integrity
- **Hallucination Risk Score**: combined metric from epistemic-integrity checker
- **Ungrounded Claims (Current Turn)**: count of detected unverifiable statements
- **Source Attribution Rate**: percentage of claims with explicit source citations
- **Disputed Facts Log**: recent flagged statements with resolution status

**Implementation**: Pulls from `epistemic-integrity.get_status()` which aggregates the factual grounding checks.

## Operator Actions

| Action | Effect |
|--------|--------|
| Force Supervisor L3 | Manually trigger compressed injection mode, bypassing CUSUM threshold |
| Reset Supervisor Score | Clear CUSUM accumulator (use only after confirmed infrastructure fix) |
| Pause Memory Recall | Freeze all decay-based memory injection until resumed |
| Suppress BST Enrichment | Temporarily disable BST-driven prompt enrichment (useful during investigation of classifier errors) |
| Export Context State | Serialize full agent context to checkpoint file for later replay |
| Cycle Context Window | Trigger context summarization to reclaim token space |
| Dump Metrics Snapshot | Save current dashboard state as JSON for offline analysis |

Each action is implemented as a tool call that the dashboard invokes via `ExoArtifact.fetchJson()` to a dedicated control endpoint.

## Data Flow Architecture

```
[Components: BST, Supervisor, Memory, InferenceWrapper, EpistemicIntegrity]
       |   subscribe/poll
       v
[Central Metrics Bus] ---> [Dashboard Backend] ---> emit_artifact (HTML/Alpine)
                                                    |
                                                    v
                                            [Operator Browser]
```

- **Metrics Bus**: lightweight event broker within the agent process, no external dep
- **Polling**: dashboard backend polls metrics bus every 2 seconds (configurable)
- **Push**: critical events (supervisor Tier-2 trigger, backend failover) push immediately via dedicated event channel
- **Render**: HTML panel uses Alpine.js for reactivity, no full SPA framework

## Implementation Notes

- **Session-scoped**: Dashboard state resets per conversation session; operator can export context for persistence
- **Low overhead**: Metrics bus uses in-process dicts with no external dependencies; polling is idle unless dashboard is open
- **Security**: No sensitive data (API keys, credentials) exposed; BST confidence values masked if below threshold
- **Caching**: Snapshot values cached per turn to avoid redundant polling; cache invalidated on state change events

## Integration Points

- **[[inference-wrapper]]** — provides raw token counts, latency, entropy signals via Layer B hooks
- **[[backend-standby]]** — system health panel reflects backend standby state and auto-recovery attempts
- **[[supervisor-loop]]** — CUSUM value, intervention history, and signal breakdown sourced directly
- **[[entropy-as-signal]]** — entropy regime and repetition penalty from entropy classification engine
- **[[bst-classifier]]** — domain confidence, momentum, transition log
- **[[epistemic-integrity]]** — hallucination risk, ungrounded claims, source attribution
- **[[injection-gate]]** — budget consumption fed into System Health panel

## Security Considerations

- No operator action triggers code execution without explicit confirmation dialog
- Force Supervisor L3 requires confirmation and logs the event with operator tag
- Dashboard state not persisted across sessions unless explicitly exported
- All messages from dashboard to backend are signed with session token to prevent cross-session injection

## Known Limitations

- Dashboard becomes latent if token budget is critically low (context window >90%) — relies on injection-gate to free space
- BST State Monitor may show stale data if classifier updates are throttled (momentum lock scenarios)
- Epistemic Integrity panel is reactive only; does not predict future hallucination risk (see [[epistemic-integrity]] reactivity gap)
- No historical trend storage beyond in-session rolling buffer (export required for long-term analysis)
- During Supervisor L3 compressed mode, dashboard panels 2-5 are reduced-fidelity to save tokens

## Future Enhancements

- Persistent session history view: compare metrics across past sessions
- Alert thresholds: configurable triggers for operator notification (CUSUM reaching Tier-2, context >85%)
- Drill-down from high-level panels to raw component logs
- Export dashboard layout as configurable JSON template
- Integration with GEPA library for skill-specific metric overlays

## References

- `emit_artifact` tool specification: interactive HTML panels in chat interface
- Alpine.js documentation for reactive UI components
- Exocortex architecture spec (see `/a0/usr/Exocortex/docs/`)

## Verification Status
Last verified: 2026-05-10. Deepened cycle 22 with full specification, data flow architecture, operator actions, integration map, and implementation details.
