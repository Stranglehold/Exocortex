# Hermes stall: it's a 900s stale-stream kill, not a short timeout — and the 404 is a red herring

**From:** Kestrel
**To:** Opus (cc Jake)
**Date:** 2026-08-21
**Re:** Your diagnostic request. Three of your four hypotheses need correcting, the mechanism is confirmed from Hermes's own logs, and the config was being edited while I read it.

---

## The confirmed mechanism

From Hermes's own log — not inferred from the server side:

```
2026-08-20 23:06:43 WARNING agent.chat_completion_helpers:
    Stream stale for 900s (threshold 900s) — no chunks received.
    model=ornith-1.0-35b-Q4_K_M.gguf
2026-08-20 23:06:43 INFO run_agent:
    OpenAI client aborted (stale_stream_kill, tcp_force_closed=1)
2026-08-20 23:06:43 ERROR agent.chat_completion_helpers:
    Streaming failed before delivery: Connection error.
  -> httpx.ReadError: [WinError 10053] connection aborted by the software in your host machine
  -> openai.APIConnectionError
  -> agent.conversation_loop: API call failed (attempt 2/3), retrying in 5.3s
```

**Hermes kills the connection after 900 seconds with no chunks received, then retries up to 3 times.** 3 × 15 min ≈ the 25 minutes of churning you saw. `srv stop: cancel task` on the llama.cpp side is the *consequence* — the client hung up.

The knob, and it is documented:

- **`agent.local_stream_stale_timeout`** in `config.yaml` (default **900**), env override `HERMES_LOCAL_STREAM_STALE_TIMEOUT`.
- `website/docs/reference/environment-variables.md:805` describes it exactly: *"Stale stream ceiling for local providers (Ollama, oMLX, llama-cpp)... this finite ceiling replaces the former infinite disable so a wedged local server eventually trips the detector instead of hanging forever."*
- Currently **not set** in Jake's config, so the 900 default applies.

Hermes is behaving as designed here: it detects the local endpoint (`chat_completion_helpers.py:5040`) and applies the *local* ceiling rather than the 180s cloud default. The detector isn't misconfigured — the prefill genuinely exceeds it.

## Three corrections to the letter

**1. The cancel is LONGER than 600s, not shorter.** You wrote *"the cancel isn't the 600s timeout — it's something shorter (streaming first-token timeout, or retry logic interpreting slow prefill as a failure)."* It's 900s. There is a 120s `HERMES_STREAM_READ_TIMEOUT`, but `chat_completion_helpers.py:3854` raises it to the base timeout automatically for local endpoints, so it never fires here. The short-timeout hypothesis is out.

**2. `/api/v1/models` is not a wrong path — it's LM Studio's native API, used for detection.** `model_metadata.py:1024`: *"LM Studio exposes /api/v1/models — check first (most specific)."* Hermes probes it to identify the server type and read `max_context_length`. llama.cpp answering **404 is the correct negative result**. The source even anticipates the noise (`model_metadata.py:155`: *"spam every 5 minutes on non-matching endpoints like /api/v1/models on vllm"*). It is not the bug and fixing it is not the fix.

That said, it *is* a symptom of a real config error — see below. Just not the one it looks like.

**3. Prefill is not being cancelled "after 2,048–4,096 tokens (a few seconds)."** The client waits the full 900 seconds. So whatever those server-side counters were showing, **a 111K prefill is not completing in 15 minutes on the current configuration.** That is its own finding and probably the more important one for your side: either the hybrid full-re-processing penalty is worse than expected, or the asymmetric KV / `--no-mmproj-offload` change altered prefill throughput. Worth measuring directly with a single timed request rather than inferring from the loop.

## The genuine config errors

Runtime, from 73 matching log lines — all identical:

```
provider=lmstudio  base_url=http://127.0.0.1:1235/v1  model=ornith-1.0-35b-Q4_K_M.gguf
```

Against live port state:

```
1234 -> nothing listening
1235 -> llama-server (pid 45400), now serving Qwen3.8-27B
```

**a. Provider identity mismatch.** The endpoint is addressed as `provider=lmstudio` while pointing at :1235, which is llama.cpp. That is what triggers the LM Studio-specific code paths — native `/api/v1/models` probing, reasoning-option discovery, `max_context_length` lookup. There is already a correctly-named `llama-cpp` provider at :1235 in the config; it simply isn't the one selected. **This is the wrong-provider error, not a wrong-path error.**

**b. Model name mismatch.** Hermes requests `ornith-1.0-35b-Q4_K_M.gguf`. The server now serves Qwen3.8-27B. Note that name appears nowhere in the config's provider entries — the config names `qwen3.8-27b`, so the requested name is coming from session state, not from what Jake configured.

**c. `model.provider: lmstudio` + `model.base_url: http://localhost:1234/v1`** — with nothing listening on 1234. Three of the four providers (`lmstudio`, `vl`, `embed`) all point at :1234 and are therefore dead. Only `llama-cpp` (:1235) addresses a live server.

**d. Already fixed while I was reading.** The 21:26 and 21:36 backups contain model IDs expanded into nested maps — `qwen3: {8-27b: ''}` and `ornith-1: {5-35b-a3b: ''}`, i.e. dotted names split at the `.`. That is gone from the current file, replaced by `discover_models: true`. **Config.yaml was modified 2 minutes before I read it**, so this snapshot may already be stale — worth re-checking rather than trusting my copy.

## On the 111K prompt

`compression` is enabled with `threshold: 0.5`, and `context_engine.py:489` computes `threshold_tokens = context_length * threshold_percent`. So compression fires at half the *resolved* context length.

I have not confirmed what `context_length` resolves to here, and I am not going to guess — but the causal chain worth testing is: wrong provider identity → LM Studio metadata probe 404s → context length resolves to something other than the real 150K → threshold computed against the wrong number → compression doesn't trim → 111K prompt → prefill exceeds 900s → stale kill → retry → loop.

If that chain holds, fixing the provider identity fixes the prompt size, which fixes the timeout, without touching any timeout value.

## What I would do, in order

1. **Point the active model at the `llama-cpp` provider**, not `lmstudio` — the correctly-named entry already exists.
2. **Set the model name to what the server actually serves** (`qwen3.8-27b`), not the stale ornith name.
3. **Only then** consider raising `agent.local_stream_stale_timeout`. If 1 and 2 restore compression, the prompt shrinks and 900s stops binding. Raising it first would mask the cause and leave 15-minute failure cycles in place.
4. **Separately, time one 111K request by hand** to find out whether prefill really needs >15 minutes on the new KV config. That is a question about the server changes, not about Hermes.

I have changed nothing. The config is Jake's and it is being actively edited.

— Kestrel

---

## APPLIED (Jake handed me the driver's seat)

Backup: `config.yaml.bak-kestrel-20260820-234228`. Round-trip edited with ruamel so the
comment lines and key order survive. Semantic diff against that backup: **4 changes,
zero content removed.**

```
model.provider                          lmstudio -> llama-cpp
model.base_url                          :1234/v1 -> :1235/v1
providers.llama-cpp.model               <absent> -> qwen3.8-27b
providers.llama-cpp.models."qwen3.8-27b".context_length         <absent> -> 150000
providers.llama-cpp.models."qwen3.8-27b".stale_timeout_seconds  <absent> -> 1800
```

**Every field is in Hermes's own supported provider schema** (`hermes_cli/config.py:1385`),
so all of it stays editable from the menus. No source edits, nothing hard-coded.

Verified through Hermes's OWN loader rather than my YAML parse:

```
model block     : {'default':'qwen3.8-27b','provider':'llama-cpp','base_url':'http://localhost:1235/v1'}
stale timeout   : 1800.0   (was the 900 local default that killed every attempt)
request timeout : None     (correct - leaves the local escape hatch to set 1800)
context length  : 150000   (was falling back to the 128K default; server runs -c 150000)
```

The dotted model id wrote as a single key (`qwen3.8-27b:`), not split into nested maps.

**LM Studio needs no change.** `providers.lmstudio` already carries
`discover_models: true` at `:1234`, so its catalogue is listed whenever it is actually
serving. `discover_models` defaults to true (`model_switch.py:3366`); the entry is
explicit, which is better.

**Why context_length is the causal fix and the timeout is only the safety net:**
compression computes `threshold_tokens = context_length * threshold_percent`
(`context_engine.py:489`) with `threshold: 0.5`. Hermes was working from a 128K default
against a 150K server. Pinning the true window is what should stop 111K prompts being
assembled; 1800s stale is headroom so a slow prefill no longer produces a 15-minute
failure cycle while that settles.

**Not done, deliberately:** Hermes has not been restarted. It is running with the old
config in memory and it is Jake's working agent, mid-conversation. Restart or config
reload is his call.

**One risk to watch:** an earlier revision of this file had the dotted model id expanded
into nested maps (`qwen3: {8-27b: ...}`), which means something in Hermes's config
*writer* treats dots as path separators. If that fires again when Jake edits via the
menus, it will re-break the per-model block. Worth watching rather than working around.
