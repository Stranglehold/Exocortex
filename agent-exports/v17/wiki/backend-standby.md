# Backend Standby Mode

**Component** | **Hook:** before_main_llm_call (_01) | **Type:** Infrastructure resilience

---

## Purpose

Backend Standby Mode handles the agent's transition into a degraded operational state when the primary LLM provider becomes unreachable. Instead of letting the agent loop on retries until context exhaustion, it detects backend failure early and gates the LLM call, preserving context integrity.

Motivated by: Wrapper killed during agent task — the agent sent a request, the backend was down, and the supervisor loop's nudges and surgery were the wrong intervention for a dead socket.

## Mechanism

### Detection
The backend standby extension (`_28_backend_standby.py` in `tool_execute_after`) detects infrastructure failures by inspecting error patterns:
- **`connection_refused`** — provider unreachable at TCP level
- **`http_error`** — non-200 responses from provider API
- **`SocketTimeoutError` on connect** — unable to establish connection (backend DOWN)

**Critical distinction:** SocketTimeoutError on *connect* is a DOWN failure. SocketTimeoutError on *read* (long generation time) is NOT a standby trigger — that's a slow backend, not a dead one.

### Gating
The `before_main_llm_call` extension (`_01_backend_standby_gate.py`) reads a flag set by the detector. When active, it short-circuits the LLM call entirely. Instead of letting the request hang or timeout, it returns a synthetic response informing the model that the backend is unavailable. This prevents:
- Context window consumption on retries
- The supervisor loop escalating inappropriately (surgery on a dead socket)
- The model executing stale recovery actions on backend return

### Recovery
When the backend becomes available again, the gate injects: "Backend was offline. Resume from where you left off. Review the last action before proceeding." This gives the model fresh context while making it re-evaluate rather than blindly retrying a stale command.

## Supervisor Loop Interaction

| Tier | Threshold | Action |
|------|-----------|--------|
| Tier 1 (Warn) | 3 consecutive hard signals | Agent notified, continues |
| Tier 2 (Surgery) | 6 consecutive hard signals | Context compression initiated |
| Tier 3 (Breaker) | 9 consecutive hard signals | Forced response — task termination |

Domain-aware thresholds exist for structural domains (codegen, debugging, system_admin) where repeated failures are expected mechanism rather than evidence of being stuck. These use elevated tiers: tier1=6, tier2=12, tier3=18.

## Integration Points

- **Hook chain:** `_28_backend_standby.py` (detection, tool_execute_after) → `_01_backend_standby_gate.py` (gating, before_main_llm_call)
- **Supervisor Loop (L4)** — Standby detection feeds hard signals into the supervisor's escalation tiers
- **Error Comprehension (L2)** — Error classification provides the structured diagnosis the standby detector reads
- **Context Pruner (L6)** — If standby extends, the pruner compresses context to buy time

## Key Design Decision

**Do not tell the model to retry the failed action automatically.** The failed action's context may be stale by the time the backend recovers. Instead, tell the model to check whether the action completed and decide for itself whether to retry. This is the difference between recovery and blind replay.

## Related Incidents
- [[inc-wrapper-killed]] — Backend process killed during agent task, validator fired with stale state

## Source
- Concept: `wiki/concepts/backend-standby.md`
- Detection: `extensions/tool_execute_after/_28_output_compressor.py` (standby detection may be integrated)
- Scope/design: `team-comms/kestrel-to-opus/backend_standby_scope_20260421.md`
- Response/review: `team-comms/opus-to-kestrel/response_backend_standby_20260421.md`
