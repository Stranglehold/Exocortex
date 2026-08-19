# Inference Wrapper (Layer B)

**Created:** 2026-04-28T05:18Z
**Status**: Component specification — FastAPI Layer B with entropy monitoring hooks.

## Overview

The Inference Wrapper sits between the agent loop and the LLM endpoint as a thin FastAPI service. It intercepts every request/response to enable real-time internal state monitoring that neither the agent code nor the external provider can see directly.

## Architecture

```
Agent Loop → [Inference Wrapper Layer B] → External LLM (lm_studio / OpenAI)
                     │
                     ├─ Entropy Monitoring Hooks
                     ├─ Token-Level Latency Tracking  
                     └─ Generation Health Metrics
```

## Monitoring Capabilities

### Entropy Hooks

Per-token output entropy logged to streaming buffer. Enables:
- Real-time detection of exploratory vs deterministic decoding regime shifts
- Correlation with BST domain classification for cross-validation
- Trigger supervisor L2 when entropy spikes during otherwise stable turns

### Latency Tracking

Time-to-first-token (TTFT) and time-per-token recorded per turn. Anomalies detected:
- TTFT > 10s on cached prefix → KV cache miss or backend degradation
- Per-token latency increasing over consecutive tokens → context window pressure building

### Generation Health

```
health_score = (
    entropy_stability_weight * (1 - entropy_variance) +
    latency_consistency_weight * (1 - latency_stddev) +
    confidence_calibration_weight * calibration_accuracy
)
if health_score < threshold → flag degraded mode
```

## Failure Mode: Wrapper Killed During Agent Task

Incident log `inc-wrapper-killed` documents case where wrapper terminated mid-task causing cascade failure. Recovery requires:
1. State preservation checkpoint before wrapper restart
2. BST domain re-classification from cached history (not full re-injection)
3. Supervisor score reset to avoid double-penalizing agent for infrastructure failure

## Connection to Other Concepts

- **[[entropy-as-signal]]** — entropy hooks provide real-time trace-level monitoring described in arXiv:2604.03589
- **[[supervisor-loop]]** — health metrics feed CUSUM accumulator as continuous signal stream not discrete events
- **[[backend-standby]]** — wrapper failure triggers structured recovery with state preservation
- **[[nerv-dashboard]]** — wrapper metrics displayed in real-time GPU/generation monitoring panel

## References

- FastAPI service architecture documented in Exocortex spec directory
\n## Verification Status\nLast verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.
