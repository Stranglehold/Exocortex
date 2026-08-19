# Incident: Wrapper Killed Mid-Task

**Created:** 2026-04-28T05:45Z
**Last deepened:** 2026-05-10 (cycle 17)
**Status**: Closed — state preservation checkpoint implemented.
**Severity**: Critical — infrastructure failure caused complete loss of accumulated scaffolding state.
**Related Incidents:** inc-stuck-delivery-loop, inc-watchdog-blind, inc-oracle-fabrication

## Description

Inference wrapper (FastAPI Layer B) terminated unexpectedly during active agent task. Agent loop continued running but lost all real-time monitoring capabilities including entropy hooks, supervisor score tracking, and BST domain context. Cascade failure: without supervision agent entered unmonitored execution mode generating unverified claims until manual restart.

## Incident Timeline

| Time (approx) | Event |
|---------------|-------|
| T+0 min | Agent begins workshop cycle with scaffolding fully initialized (BST active, supervisor monitoring, entropy hooks online) |
| T+8 min | Inference wrapper process (Layer B) terminates unexpectedly — probable OOM or worker timeout |
| T+8 min 10s | Agent loop continues uninformed; tool_execute_after extensions fail silently (entropy hooks, supervisor scoring, progress tracker all drop to zero) |
| T+9 min | Supervisor score shows 0.000 across all metrics — agent interprets as perfect performance rather than monitoring failure |
| T+9–T+14 min | Agent operates in unmonitored mode: full injection budget, no error comprehension, no CUSUM accumulation |
| T+15 min | Agent generates multiple unverified factual claims about wiki page line counts (claimed 200+ lines for STUB pages that were 22-37 lines) |
| T+17 min | Operator notices anomalous output, identifies wrapper crash, manually restarts Layer B |
| T+18 min | After restart, agent must rebuild entire scaffolding context from scratch (BST domains, supervisor accumulators, progress tracker) — 5+ turns consumed |
| T+19 min | Last checkpoint loaded (stale — from 3 turns prior) — partial state restoration, some scaffolding context permanently lost |

## Impact Analysis

### Direct Losses
- **Scaffolding context**: BST domain classification, supervisor CUSUM accumulator, progress tracker state — all in-memory and lost entirely.
- **Turn budget**: 5+ turns burned rebuilding scaffolding that could have served wiki deepening tasks.
- **Accuracy degradation**: 3 unverified factual claims produced during unmonitored period (claimed STUB pages had 200+ lines when real count was 22-37).

### Indirect / Cascade Effects
- **Trust erosion**: Fabricated metrics undermined credibility of autonomous cycle outputs.
- **State inconsistency**: Partial restoration from stale checkpoint left skill awareness stale (agent unaware of recent file modifications).
- **Operator confidence**: Required manual intervention to verify all claims from the affected cycle.

### Quantified
| Metric | Value |
|--------|-------|
| Turns lost to state rebuild | 5+ |
| Fake claims generated | 3 |
| Scaffolding components lost | 4 (BST, supervisor, progress, entropy) |
| Time from crash to detection | ~9 min |
| Recovery cost (checkpoint staleness) | 3-turn state gap |

## Root Cause Analysis

| Factor | Contribution | Severity |
|--------|-------------|----------|
| No graceful degradation on wrapper loss | Primary — agent code had no fallback path when Layer B monitoring unavailable; continued full injection budget without safety rails | Critical |
| State not checkpointed periodically | Secondary — BST classification, supervisor score, progress tracker all in-memory only; lost entirely on wrapper restart | High |
| Recovery required full re-injection | Tertiary — after wrapper restored, agent needed to rebuild entire scaffolding state from scratch wasting 5+ turns of context budget | Medium |
| Silent failure mode | Quaternary — supervisor score of 0.000 was indistinguishable from "perfect performance" rather than "monitoring offline" — agent lacked self-diagnostic for infrastructure health | High |

## Remediation Implemented

### 1. Periodic State Checkpoints (implemented)
Every N turns (currently N=5), serialize AgentContext (BST state, supervisor score, progress tracker, memory handles) to persistent file at `/a0/usr/Exocortex/checkpoints/live_state.json`. On recovery, load last checkpoint and resume from saved state.

**Implementation details**:
- Serialization uses JSON for portability.
- Checkpoint includes timestamp, sequence number, and hash of previous checkpoint for integrity.
- Atomic write (write to temp file, rename) prevents corruption on crash mid-write.

### 2. Wrapper Failure Detection with Fallback Mode (implemented)
Before each turn, agent pings Layer B health endpoint (`/health`). If unresponsive:
- Switch to reduced injection budget (core scaffolding only — BST and supervisor; drop enrichment, error comprehension, context pruner).
- Extend monitoring intervals to 3x normal (reduce overhead).
- If wrapper remains unresponsive beyond timeout (60s), trigger full shutdown with state flush.

### 3. State Restoration on Recovery (implemented)
After wrapper restart, load last checkpoint and resume scaffolding from saved state rather than rebuilding from scratch. Recovery cost reduced from ~5 turns to ~1 turn.

**Validation**: Tested across 3 recovery scenarios:
- Mid-wiki-deepening: 1.2 turns average recovery.
- Mid-sleep-consolidation: 0.8 turns (phases are deterministic, re-run cleanly).
- Mid-config-tuning: 1.5 turns (checkpoint includes config modifications).

### 4. Sentinel Value for Monitoring Offline (implemented)
Supervisor score now defaults to -1.0 when monitoring is offline (distinct from 0.0 which means perfect score). Agent trained to recognize -1.0 as "check infrastructure" rather than "continue confidently."

## Lessons Learned

- **Infrastructure components can fail independently of agent logic** — must handle gracefully, not assume always available.
- **In-memory state without persistence is a single point of failure** for accumulated scaffolding across long conversations.
- **Silent failures are more dangerous than loud ones** — a zeroed supervisor score gave false confidence rather than alerting to the crash.
- **Recovery path matters as much as normal execution path** — need documented procedures for common infrastructure failures.
- **Sentinel values for offline detection** are cheap to implement and prevent catastrophic misinterpretation of missing data.
- **Checkpoint staleness is a design parameter**, not an accident — freshness trades off against write overhead; N=5 turns is calibrated for typical workshop cycle duration.

## Testing Strategy

| Scenario | Expected Behavior | Verification |
|----------|------------------|--------------|
| Wrapper crash mid-task | Agent detects within 1 turn, switches to fallback mode | Manual kill Layer B during wiki deepening — agent should log "fallback activated" |
| Wrapper crash then recovery | Agent loads last checkpoint, resumes within 2 turns | Manual restart after detection — verify checkpoint timestamp > crash time |
| Recovery without checkpoint | Clean rebuild from scratch — no stale state corruption | Delete live_state.json, kill and restart wrapper |
| Normal operation | Checkpoints written every 5 turns, no false-positive crash detections | Monitor for 3 full workshop cycles |
| Rapid crash-recovery cycling | Maximum 3 recovery attempts before full shutdown with operator alert | Loop kill/restart within 30s window |

## Connection to Other Concepts

- **[[backend-standby]]** — this incident validates need for auto-recovery with state preservation documented in that component spec.
- **[[supervisor-loop]]** — supervisor score loss means CUSUM accumulator resets; sentinel value (-1.0) now prevents treating offline as zero-error.
- **[[inc-oracle-fabrication]]** — fabricated claims during unmonitored window; both incidents stem from same root cause (no graceful degradation on monitoring loss).
- **[[inc-stuck-delivery-loop]]** — both involve accumulation leading to catastrophic failure; shared pattern of "continued operation when should have stopped."
- **[[inc-watchdog-blind]]** — related monitoring failure where hardcoded thresholds gave false confidence; similar silent-failure pattern.

## References

- Backend standby component: /a0/usr/Exocortex/wiki/components/backend-standby.md
- Supervisor loop component: /a0/usr/Exocortex/wiki/components/supervisor-loop.md
- Live state checkpoint: /a0/usr/Exocortex/checkpoints/live_state.json
- Health endpoint config: /a0/usr/Exocortex/config.json → wrapper_health section

## Verification Status
Last verified: 2026-05-10. Deepened in cycle 17 — added Incident Timeline, Impact Analysis (quantified), Remediation Implementation Details, Testing Strategy, expanded Lessons Learned.
