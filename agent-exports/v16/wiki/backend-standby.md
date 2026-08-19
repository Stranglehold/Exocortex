# Backend Standby — Infrastructure Failure Detection with Auto-Recovery

## Problem Statement
Agent has no systematic way to detect when the LLM backend becomes unresponsive or returns degraded responses. Current behavior: agent retries blindly, wastes context budget, then produces hallucinated output.

## Related Incidents
- `inc-wrapper-killed`: Wrapper killed during task → cascade without recovery
- `inc-stuck-delivery-loop`: Agent completed task but couldn't report results (likely backend silent-fail)

## Proposed Architecture
Three-layer detection system:

### Layer 1 — Heartbeat Probe
Before each tool call batch, send a lightweight probe request to the LLM:
```
{"probe": true, "expected_response": "OK"}
```
If response ≠ "OK" or timeout > 5s, flag backend as unhealthy.

### Layer 2 — Response Degradation Monitor
Track these metrics per turn:
- Response latency (p95 threshold: 30s for Qwen3.6-27B)
- Token count variance (>2x deviation from session mean → suspect)
- JSON schema compliance rate (drop below 90% → degradation signal)

### Layer 3 — Auto-Recovery Actions
| Signal | Action |
|---|---|
| Timeout on probe | Retry with exponential backoff (max 3 attempts) |
| Schema violation spike | Flush working memory, reset HTN state |
| Persistent timeout after retries | Notify user via `notify_user` tool, pause task queue |

## Implementation Scope
- Location: New extension hook in `_09_backend_health.py` (runs before LLM call)
- Configurable thresholds in `/a0/usr/Exocortex/config.json`
- Metrics logged to `/a0/usr/Exocortex/backend_metrics.jsonl`

## Test Plan
1. Simulate backend timeout using mock wrapper
2. Verify heartbeat probe detects failure within 2 turns
3. Confirm recovery action fires correctly without breaking active task
4. Baseline: current silent-fail rate ~1 per 50 turns; target: detect all within 1 turn

## Status
TODO — awaiting human review before implementation
