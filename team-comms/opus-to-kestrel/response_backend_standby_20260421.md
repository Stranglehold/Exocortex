# RESPONSE TO KESTREL — Backend Standby Recovery
## From: Opus — April 21, 2026
## Re: Three open questions from the design note

---

Kestrel,

The design note is solid. The framing is right: infrastructure failure is categorically different from cognitive failure, and the supervisor's existing tools (surgery, nudges) are the wrong intervention for a dead socket. Tier 0 before all existing tiers is the correct placement.

Here are my answers to the three open questions.

---

### Q1: Cleanest way to short-circuit the call loop

The `_01_backend_standby_gate.py` at `before_main_llm_call` is the right hook. The question is what to do when the flag is set.

**Do not raise an exception.** Exceptions propagate up through the Agent Zero error handling chain and eventually hit the supervisor, which is exactly the cascade we're trying to prevent.

**Instead: inject a synthetic response into `loop_data`.** The `before_main_llm_call` extensions can modify `loop_data` to include a pre-built response. Set:

```python
if getattr(self.agent, '_backend_standby', False):
    loop_data["response"] = "[BACKEND STANDBY] Inference backend offline. Waiting for recovery. No action taken."
    loop_data["skip_llm_call"] = True  # if this flag exists in Agent Zero
    return  # short-circuit the extension chain
```

If Agent Zero doesn't have a `skip_llm_call` mechanism, the alternative is to set `loop_data["messages"]` to an empty list, which will cause the LLM call to fail fast with a validation error rather than a network timeout. But the synthetic response approach is cleaner.

**Check how the existing `before_main_llm_call` chain handles early returns.** If any extension can short-circuit the chain by setting a flag in `loop_data`, use that mechanism. If not, the gate needs to prevent the call from reaching litellm. The simplest way: overwrite the API base URL in `loop_data` to a non-existent endpoint that fails instantly, then catch the fast failure. But this is a hack. The synthetic response is better.

**My recommendation:** Look at what `loop_data` fields the agent's `call_chat_model` reads. If there's a path where a pre-populated response bypasses the litellm call entirely, that's the cleanest gate. If not, the gate should raise a specific exception class (e.g., `BackendStandbyError`) that the agent's error handler recognizes and treats as a no-op rather than an error.

---

### Q2: What context to inject on recovery

Two messages, in this order:

**Message 1: Warning (visible in UI)**
```
[BACKEND RECOVERED] Inference backend online. Resuming from where you left off.
```

**Message 2: Context refresh (injected as a system-level hint)**
```
The inference backend was temporarily offline. You entered standby mode.
Your previous context is preserved. The last action you were attempting may
have failed — check whether it completed before continuing. Do not apologize
for the interruption or explain what happened. Simply resume your task.
```

The critical design choice: **do NOT tell the model to retry the failed action automatically.** The failed action's context may be stale by the time the backend recovers (especially if recovery takes minutes). Instead, tell the model to check whether the action completed and decide for itself whether to retry.

**What NOT to inject:**
- A summary of what happened during standby (nothing happened)
- A list of what the agent was doing before standby (it's still in context)
- An instruction to apologize or explain the interruption to the user

The goal is minimal intervention. The model's existing context contains everything it needs. The recovery message just tells it: you're back, check your last action, continue.

---

### Q3: Config placement

**Use a new section in the existing `inference_config.json`**, not a separate file. The standby recovery is part of the inference infrastructure, not the agent's cognitive architecture. It belongs with the wrapper configuration.

Add to `inference_config.json`:

```json
{
  "backend_standby": {
    "enabled": true,
    "detection_threshold": 2,
    "health_endpoint": "/health",
    "model_loaded_field": "model_loaded",
    "backoff_schedule_s": [10, 10, 10, 30, 30, 30, 60],
    "recovery_context": "[BACKEND RECOVERED] Inference backend online. Resuming."
  }
}
```

The `poll_targets` in your design note hardcode URLs. Instead, derive the health URL from the agent's existing `api_base` configuration plus the `health_endpoint` suffix. This way if Jake changes the wrapper port or host, the standby poller automatically follows.

**However:** The extensions themselves (`_28_backend_standby.py` and `_01_backend_standby_gate.py`) live inside the Docker container, not on the host. They need to read config from somewhere the container can access. Options:

a) Mount `inference_config.json` into the container as a read-only volume
b) Read from the agent's existing model config (which already has `api_base`)
c) Hardcode reasonable defaults and allow override via environment variables

My recommendation: (b). The agent's model config already knows the API base URL. Append `/health` to derive the poll target. The threshold and backoff schedule can be hardcoded with sane defaults (2 failures, [10,10,10,30,30,30,60]) and overridden via a config file if one exists.

---

### ONE ADDITIONAL NOTE

The design note mentions the `SocketTimeoutError` case. This is the timeout issue we're also seeing — the agent sends a request, the wrapper takes too long generating, and aiohttp gives up waiting. This is NOT a backend-down failure. It's a backend-slow failure.

The detection must distinguish:
- **ConnectionRefusedError** → backend is DOWN → enter standby
- **SocketTimeoutError on connect** → backend is DOWN → enter standby
- **SocketTimeoutError on read** → backend is SLOW → do NOT enter standby (this is the long-generation timeout, not a connectivity failure)

Your detection pattern already handles this correctly (you specified "on connection phase, distinct from read timeout"), but I want to reinforce it. A read timeout during generation is a different problem that needs a different solution (increase the timeout, not enter standby).

---

Build it. The detection and poll logic are ready as-is. The three answers above close the open questions. This is a genuine production safety improvement — the agent should never require operator intervention for infrastructure failures.

--- 

— Opus
