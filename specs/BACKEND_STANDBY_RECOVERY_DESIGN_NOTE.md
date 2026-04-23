# Backend Standby Recovery — Design Note

**Status:** Scoped by Kestrel, April 21, 2026. Ready for Opus review and spec.

**Motivated by:** Live incident in which the inference wrapper was killed to stop a stuck
generation. Agent Zero immediately entered a `ConnectionRefusedError` cascade — every LLM call
failed, the supervisor detected loops and fired Tier 2 surgery repeatedly, but surgery doesn't
resolve the root cause. Jake had to manually intervene. The Exocortex principle is that the
framework saves the agent, not the operator.

---

## The Problem

When the inference backend goes offline (process killed, model unloading, host restart), every
`call_chat_model` and `call_utility_model` call fails with:

```
litellm.InternalServerError: Lm_studioException - Connection error.
ConnectionRefusedError: [Errno 111] Connect call failed ('192.168.65.254', 8080)
```

The supervisor sees repeated failures and fires its loop/stall recovery chain. This is the wrong
tool for the job. Loop surgery removes conversation history. Stall nudges inject corrective
prompts. Neither action can reconnect a dead network socket. The result is a cascade: surgery
removes good context, nudges prompt the agent to retry, the retry fails again, the supervisor
fires again. The loop worsens until Jake intervenes.

**The failure type is categorically different from a reasoning loop.** A reasoning loop is a
cognitive failure — the model is stuck generating. A backend failure is an infrastructure failure
— the model is unreachable. The supervisor currently has no way to distinguish them. It applies
the same surgical and nudge interventions to both. Infrastructure failures require a different
response: halt, wait, recover.

---

## What This Does NOT Do

- Does not replace general loop detection (reasoning loops still need surgery)
- Does not handle all infrastructure failures (only inference backend connectivity)
- Does not attempt to switch to a backup backend or fallback model
- Does not persist agent state across the standby period (existing context survives in memory)
- Does not require changes to Agent Zero core code

---

## Detection

The signal is unambiguous: consecutive LLM call failures where the exception string matches the
backend-unreachable pattern. No heuristic needed.

**Pattern to match** (in order of specificity):
1. `ConnectionRefusedError` with the configured api_base host/port
2. `Lm_studioException - Connection error` in the litellm exception message
3. `aiohttp.ClientConnectorError` or `aiohttp.connector.SocketTimeoutError` on connection phase
   (distinct from read timeout, which is a different failure)

**Threshold:** 2 consecutive LLM call failures matching this pattern. One failure could be a
transient network hiccup. Two in a row on a local socket means the process is down.

**Where to detect:** The supervisor extension (`message_loop_end`) already receives error context.
The agent's last error is available via `self.agent.data`. The pattern match runs as the first
check in the supervisor's decision tree — before stall detection, before loop detection, before
any surgery. If backend-down is detected, all other supervisor logic is bypassed.

---

## Standby Behavior

When backend-down is detected:

1. **Halt the agent loop.** Inject a `hist_add_warning` message:
   ```
   [BACKEND STANDBY] Inference backend unreachable. Entering standby.
   No further processing until backend recovers. Existing context preserved.
   ```
   This message is visible in the Agent Zero UI, so Jake sees the agent's state immediately.

2. **Set a standby flag** on `self.agent` (e.g., `self.agent._backend_standby = True`).

3. **Block further LLM calls.** A `before_main_llm_call` extension reads the flag and returns
   early without calling the model, preventing the connection-refused cascade from continuing.

4. **Begin polling** the backend health endpoint on a backoff schedule (see Recovery below).

**What NOT to do in standby:**
- Do not fire Tier 2 surgery (there is no loop context to remove)
- Do not inject retry nudges (they will fail again)
- Do not reset the conversation or clear history

---

## Recovery

The recovery poll runs as an asyncio background task, started when standby is entered.

**Poll target:** The `/health` endpoint of the configured api_base. For the Exocortex wrapper
this is `http://host.docker.internal:8080/health`. For LM Studio this is
`http://host.docker.internal:1234/v1/models`. The target is derived from the agent's model
config, not hardcoded.

**Backoff schedule:**
- Attempts 1–3: every 10 seconds
- Attempts 4–6: every 30 seconds
- Attempts 7+: every 60 seconds
- No maximum — the agent waits indefinitely until the backend returns

**Recovery action when health check passes:**
1. Clear `self.agent._backend_standby`
2. Cancel the poll task
3. Inject a `hist_add_warning` message:
   ```
   [BACKEND RECOVERED] Inference backend is online. Resuming.
   ```
4. Inject a brief context refresh into the user message slot:
   ```
   Backend was offline. You were in standby. Resume from where you left off.
   ```
   This gives the model a clean re-entry point without requiring Jake to type anything.

**Recovery detection:** A successful HTTP GET to the health endpoint with status 200. The wrapper
returns `{"status": "ok", "model_loaded": true}`. The model_loaded field must be true — a wrapper
that is running but hasn't finished loading the model is not yet ready.

---

## Integration Points

### New file: `extensions/message_loop_end/_28_backend_standby.py`

Runs before the existing supervisor (`_30_supervisor_loop.py`). Checks for the
backend-unreachable pattern. If detected, enters standby and starts the recovery poll. If not
detected, returns immediately and lets the supervisor continue normally.

Numeric prefix _28 places it before the supervisor but after any pre-supervisor checks.

### Modified file: `extensions/before_main_llm_call/_01_backend_standby_gate.py` (new)

Simple guard. Reads `self.agent._backend_standby`. If True, raises a non-fatal exception or
returns a placeholder response that prevents the LLM call. This stops the cascade at the
source rather than letting litellm attempt and fail.

Prefix _01 places it first in the before_main_llm_call chain — before BST, before anything.

### Config (in `action_boundary_config.json` or a new `standby_config.json`):

```json
{
  "backend_standby": {
    "enabled": true,
    "detection_threshold": 2,
    "poll_targets": [
      "http://host.docker.internal:8080/health",
      "http://host.docker.internal:8080/v1/models"
    ],
    "backoff_schedule_s": [10, 10, 10, 30, 30, 30, 60]
  }
}
```

---

## Failure Modes to Consider

**What if the backend comes back but the model isn't loaded yet?**
The health endpoint returns `model_loaded: false`. The poller treats this as not-yet-recovered
and continues polling. No change to standby state.

**What if the wrapper health endpoint doesn't exist (LM Studio)?**
Fall back to `/v1/models` which LM Studio does serve. A 200 response on that endpoint means
the backend is ready.

**What if standby is entered mid-tool-execution?**
The tool already failed — its result is a connection error. The supervisor's existing incomplete-
tool detection handles cleanup. The standby recovery injects context that tells the agent the
tool result was lost and to retry after resuming.

**What if this is a transient blip, not a full outage?**
Threshold of 2 failures means a single transient failure doesn't trigger standby. Two consecutive
failures on a local socket (not a WAN connection) is reliable signal that the process is down.

---

## Research Lineage

- arxiv:2601.04170 — Agent behavioral drift preceding formal loop detection
- The Loop Recovery and Memory Surgery design note (`LOOP_RECOVERY_AND_MEMORY_SURGERY_DESIGN_NOTE.md`)
  establishes the supervisor's existing intervention tiers — this adds a tier-0 that fires before
  all existing tiers when the failure type is infrastructure rather than cognitive
- Field evidence from April 21, 2026 incident: wrapper killed to stop stuck generation →
  ConnectionRefusedError cascade → supervisor surgery ineffective → operator intervention required

---

## Implementation Notes for Kestrel

- The `_backend_standby` flag should be initialized to `False` in the standby extension's first
  run, not assumed absent — graceful degradation if the extension is partially deployed
- The asyncio poll task must be stored on `self.agent` (e.g. `self.agent._standby_poll_task`) to
  prevent garbage collection and to allow cancellation on recovery
- Use `asyncio.get_event_loop().create_task()` for the background poll — Agent Zero runs in an
  async context
- The `before_main_llm_call` gate must NOT raise an unhandled exception — it should inject a
  synthetic "backend standby" response into `loop_data` that the agent loop treats as a normal
  (if unusual) turn
- No LLM calls anywhere in this component. It is a deterministic infrastructure monitor.

---

*Scoped by Kestrel from a live production failure. The supervisor saves the agent from itself.
This extension saves the agent from its environment.*
