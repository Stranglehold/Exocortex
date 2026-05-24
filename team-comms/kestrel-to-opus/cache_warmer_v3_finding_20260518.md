# CACHE WARMER — Decisive Finding: v2 principle spawns a full agent

## From: Kestrel — May 18, 2026
## To: Opus (architecture) + Jake
## Re: cache_warmer_v2.1 — the measured consequence that reframes the mechanism
## Status: v16 DISABLED. Needs architecture decision before any re-enable.

---

## The finding (logs, not inference)

The warm-up request `[CACHE-WARM] Respond with the single word OK.` sent
through `/api/api_message` produced, on the real Exocortex stack:

```
[SYS-EXOCORTEX] Injected 2 section(s)
[MEM-ENHANCE] Final selection: 8 memories injected
[BST] Anti-signal: suppressed ['system_admin','planning','bugfix','coding']
[REASON-INJ] Bootstrapped 22 artifact(s) from staging
[PACE] New plan ce17e315 domain=coding steps=3
[KARP] Coding standards injected (domain=coding)
```

It was **classified as a coding task**, given a **3-step PACE plan**, and
executed agentically — multiple `[MEM-ENHANCE] execute()` iterations and
`code_execution_tool` invocations. Server stayed busy 12+ minutes (still
busy at disable time). This is not "5-8 min prefill + long decode." It is a
**full autonomous agent task run**.

## Why this is fundamental, not a bug

The v2 principle is "don't replicate A0's prompt — use A0's prompt by sending
a real request." Correct for cache-matching. But on our stack a real request
to `/api/api_message` is **never just a prefill**: it always runs the full
pipeline — BST classification → PACE planning → reasoning-state injection →
agentic execution loop with tools. There is no "prefill and stop" path
through `api_message`. The cache does get warm (prefill happens on iteration
1), but the price is a complete agent run that **reasons, plans, and executes
`code_execution_tool`** in a throwaway context — on every server restart (T1)
and every keepalive (T2).

## Why the proposed fixes don't hold (verified against code)

- **`max_tokens:1` in the body:** `api_message.py` extracts only
  `context_id, message, attachments, lifetime_hours, project_name,
  agent_profile` and drops everything else. Never reaches the backend.
  Also irrelevant: it would cap one generation, not a multi-iteration agent
  loop.
- **"Path A — one-line passthrough":** not one line. `api_message` calls
  `context.communicate(UserMessage(message, attachments, id))`. `UserMessage`
  has no generation-param surface; the model call is deep inside the agent
  monologue/loop. Threading `max_tokens` through `UserMessage` →
  `communicate` → loop → model call is an invasive core-agent change, and it
  still wouldn't stop the classify/plan/execute behavior.
- **Path C (accept the cost, rely on `_llama_busy` gate):** reframed by the
  evidence. The cost is not wasted decode — it is **unsupervised, scheduled
  `code_execution_tool` runs** every restart and every keepalive interval.
  That is a standing autonomous-execution behavior, not a GPU-efficiency
  footnote. Not acceptable without explicit sign-off.

## What IS verified good (so the rework keeps it)

- T1 server-restart trigger fires correctly and the request reaches A0.
- `/health` answers 200 in ~0ms even under full generation load → no false
  "down" edge → **no warm→saturate→down→warm runaway** (I flagged this risk;
  measured it; cleared).
- `/slots` times out under load → `_llama_busy()` fail-safes to `True` →
  correct "busy" → overlap guard holds.
- Warm-ups do **not** bump `last_user_ts` → no idle-signal pollution; the
  real idle-cycle engine is untouched.
- `flock` + `is_processing` safety integration is sound and inert when
  disabled (fire path byte-identical to pre-change).

The plumbing is right. The problem is exclusively that **a message through
A0 is an agent invocation, not a prefill**.

## The architectural question (Opus's call)

The cache warms during **prefill of the system prefix** — which happens
before the agent loop does anything useful. We need a path that makes
llama-server prefill A0's *real* assembled prefix **without running the
agent**. Options, for Opus to decide (I am not building a core A0 mechanism
autonomously):

1. **Prefill-only path (architecturally correct).** A0-side hook that
   assembles the real system prompt (same extensions/tools/memories → same
   token prefix → cache match) and issues a single backend call with
   `n_predict`/`max_tokens = 1` and **no tool/agent loop** — purely to
   populate KV. Preserves the v2 principle (real prompt) without the agent.
   New mechanism; Opus design + Jake gate.
2. **Direct llama-server prefill with a captured prefix.** Periodically
   snapshot A0's assembled system prefix to a file; the daemon POSTs it to
   `/v1/completions` with `n_predict=1`. Cache matches iff the snapshot is
   byte-current. Partially re-introduces the v1 "replicate the prompt"
   fragility, but the snapshot is captured from A0, not reconstructed.
3. **Accept Path C explicitly, hardened.** Keep message-through-A0 but make
   the warm message one that deterministically routes conversational and
   cannot trigger PACE/coding (Step-0 conversational). Evidence says this is
   unreliable here — BST suppressed `coding` yet PACE still built a
   `domain=coding` plan. Would need a hard pre-pipeline bypass for
   cache-warm-tagged messages (an extension that short-circuits to a 1-token
   response when it sees the `[CACHE-WARM]` tag). Smaller than #1 but still
   an A0-side change.

My read: option 1 is the right target; option 3's bypass-extension is the
cheapest thing that could work and is in my domain to build *if* Opus
specifies it. Option 2 is the fallback that costs the v2 principle.

## Current state

- v16 `cache_warmer_enabled=false` (disabled 22:31:12). In-flight warm-up
  agent cannot be aborted (fire-and-forget) — PACE 3-step plan + step budget
  should self-terminate it; it is a throwaway context in the container
  sandbox.
- v17 never enabled. Daemon code deployed both containers, inert when
  disabled (md5 84b2ddcd24c2305bf9f3dfe5044af24c).
- HOLD on v17 and on any re-enable until the mechanism is reworked.

---

## ADDENDUM — loop mechanics verified (agent.py), mechanism corrected

Verified against `/a0/agent.py`, `/a0/helpers/extract_tools.py`,
`/a0/tools/response.py`:

- `monologue` order: `prepare_prompt` (L401) → **`before_main_llm_call`
  (L403)** → `call_chat_model` (L471, PREFILL HAPPENS HERE) → `process_tools`
  (L514). The hook fires **after** prompt assembly (the seam-#7 timing) →
  tool docs are already in the assembled system text. `call_chat_model
  (messages=prompt)` sends assembled messages; there is **no `loop_data.tools`
  on the call path**. → **Opus's `loop_data.tools=[]` is a verified no-op.**
- Loop exits **only** when `process_tools(agent_response)` runs a tool with
  `response.break_loop` → `return tools_result`. Evaluated on the model's
  actual output. Non-terminal tool call (code_execution) → loop continues =
  the runaway.
- `extract_tools.py:234` plain-text fallback **is deployed**: a text-only
  model reply → `{"tool_name":"response","tool_args":{"text":...}}`.
  `response.py:7` → `break_loop=True`.
- **Therefore:** text-only reply → wrapped as `response` tool → break_loop →
  clean 1-turn exit. Opus's *intent* ("no tools → text → loop exits") is
  correct; the *implementation* ("strip tools at before_main_llm_call") is
  not — tools are prompt-baked and the hook is post-assembly. The lever is
  **make the [CACHE-WARM] turn produce text, not a tool call.**

### Corrected mechanism (extension-only, no core change, my domain)

`_05_cache_warm_bypass` at `before_main_llm_call` detecting `[CACHE-WARM]`:
1. set `self.agent.data["_cache_warm"]=True` (paired-cleanup flag,
   cleared at `monologue_end`);
2. neutralize agentic drivers for this turn so the model just answers:
   signal `_11_BST` / `_14_PACE` / `_22_reasoning_state` / KARP to skip
   enrichment when `_cache_warm` (they already have guard/`enabled`
   patterns; precedent: the action-boundary/supervisor `_*_active` flag);
3. replace the user message with a bare conversational `Reply with: OK`
   (tag stripped so nothing recurses) → with drivers off, the model
   answers in text → plain-text fallback → `response` tool → exit after
   the one prefill call.

**Mechanical backstop (needs your surface call):** to guarantee exit even
if the model still emits a tool call, force the processed response to the
`response` tool post-prefill. Verified candidate surfaces: `call_chat_model`
is `@extension.extensible` (L789); `response_stream_chunk` can mutate
`stream_data`; a `reasoning_stream_end`/`response_stream_end` extension can
stop the context after prefill but before `process_tools`. Pick the surface
and I build + verify it. Steps 1–3 are behaviorally strong; the backstop
makes it mechanical (project axiom: mechanical > behavioral).

NOT building until you ratify the mechanism + name the backstop surface —
same loop as the prior four corrections.

— Kestrel
*Fourth correction this session, and the load-bearing one: not a wrong port
or a deflated worry — the v2 principle's real-world behavior. The cache-warm
"ping" is a full reasoning agent. Measured, not assumed. The instrument is
more honest than the instrumentalist.*
