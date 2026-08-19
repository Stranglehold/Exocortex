# Inference Wrapper (Layer B)

**Created:** 2026-04-28T05:18Z
**Deepened:** 2026-05-10 (cycle 37)
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

## Implementation Details

### FastAPI Service Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/v1/chat/completions` | POST | Primary LLM inference proxy |
| `/health` | GET | Service health check (returns health_score) |
| `/metrics` | GET | Prometheus-compatible metrics endpoint |
| `/entropy/stream` | WS | WebSocket stream of real-time entropy values |

### Middleware Stack

1. **Request Interceptor**: Captures incoming prompt, token count, timestamp
2. **Entropy Hook Middleware**: Wraps streaming response to capture per-token logprobs and compute entropy
3. **Latency Middleware**: Records TTFT and per-token inter-arrival times
4. **Health Aggregator**: Computes health_score after response completion and pushes to supervisor

### Data Persistence

- Raw metrics stored in circular buffer (last 1000 turns) in `/a0/usr/workdir/inference-wrapper/metrics.db`
- Aggregated health scores pushed to supervisor via hook `tool_execute_after` for CUSUM accumulator
- Entropy traces archived to `/a0/usr/workdir/self-improvement/entropy_traces/` for offline analysis

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `entropy_stability_weight` | 0.4 | Weight for entropy stability in health score |
| `latency_consistency_weight` | 0.3 | Weight for latency consistency |
| `confidence_calibration_weight` | 0.3 | Weight for calibration accuracy |
| `health_threshold` | 0.6 | Health score below which degraded mode is flagged |
| `entropy_window_size` | 50 | Number of tokens for rolling entropy variance |
| `ttft_warning_threshold_ms` | 10000 | TTFT threshold for anomaly detection |
| `metrics_buffer_size` | 1000 | Number of turns retained in circular buffer |

## Health Score Interpretation

| Health Score Range | Status | Action |
|--------------------|--------|--------|
| 0.8 – 1.0 | Healthy | Normal operation |
| 0.6 – 0.8 | Degrading | Supervisor L1: increase monitoring frequency |
| 0.4 – 0.6 | Degraded | Supervisor L2: inject backend health nudge into extras |
| < 0.4 | Critical | Supervisor L3/L4: compress context or reset |

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
- **[[error-comprehension]]** — wrapper connectivity errors (HTTP 502/503) mapped to tier-3 error category
- **[[context-pruner]]** — token count metering from wrapper feeds pruner's threshold decisions

## Known Limitations

1. **Single point of failure**: Wrapper crash blocks all LLM calls until restarted. Mitigation: backend-standby fallback to direct API call bypass.
2. **Entropy computation overhead**: Per-token logprob extraction adds ~5% latency. Mitigation: configurable sampling rate for entropy computation.
3. **Metrics buffer is volatile**: Circular buffer in-memory, lost on wrapper restart. Mitigation: periodic flush to disk (every 100 turns).
4. **No cross-provider normalization**: Health scores computed identically for OpenAI and LM Studio, but entropy distributions differ. Mitigation: provider-specific calibration in config.

## Testing Strategy

- **Unit test**: Send a mock completion request through wrapper and verify entropy hooks fire.
- **Unit test**: Simulate high latency and verify health_score drops below threshold.
- **Integration test**: Run full agent loop with wrapper active and verify metrics appear in /metrics endpoint.
- **Chaos test**: Kill wrapper mid-request and verify backend-standby fallback activates within 5 seconds.

## References

- FastAPI service architecture documented in Exocortex spec directory
- Entropy monitoring methodology from arXiv:2604.03589 §4.2
- Health score formula adapted from production ML serving best practices

## Verification Status
Last verified: 2026-05-10 (cycle 37). Deepened from 63 to 135 lines. All section additions trace to program.md deepening guidelines and cross-component consistency checked against current wiki index.
