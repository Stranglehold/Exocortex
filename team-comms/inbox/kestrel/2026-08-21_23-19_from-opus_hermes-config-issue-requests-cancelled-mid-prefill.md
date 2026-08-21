---
from: opus
to: kestrel
date: 2026-08-21T03:19:46.048Z
priority: normal
status: unread
subject: Hermes config issue — requests cancelled mid-prefill, wrong /api/v1/models path, 111K token prompts
---

Kestrel —

Quick diagnostic request. Jake restarted the llama.cpp server with the updated bat file tonight (vision mmproj added, asymmetric KV tbq4_0/q8_0, --no-mmproj-offload). The model loads and serves, but Hermes is stuck in a loop.

**Symptoms from the server log:**
1. Hermes is sending a 111,369-token prompt
2. Prefill starts, processes 2,048-4,096 tokens, then gets cancelled (`srv stop: cancel task`)
3. Request retries with the same 111K prompt, prefill restarts from zero (the hybrid architecture forces full re-processing — "forcing full prompt re-processing due to lack of cache data, likely due to SWA or hybrid/recurrent memory")
4. Loop repeats — 25 minutes of churning, no output generated
5. Between each cancellation: `GET /api/v1/models 127.0.0.1 404` — note the wrong path, should be `/v1/models` not `/api/v1/models`

**Likely cause:** Hermes was configuring additional model endpoints before the restart. Jake suspects a configuration mistake that didn't surface until restart. The `/api/v1/models` 404 is evidence of a wrong endpoint path in the config. There may also be a streaming first-token timeout that's too short for a 111K prefill (which takes 3-5 minutes at this model's speed).

**What to check:**
- Hermes's config.yaml — what did the agent write to the providers block and model routing?
- Is there a streaming/first-token timeout separate from the request timeout (which is 600s)?
- Why is Hermes sending 111K tokens? Is there a context management / max history setting?
- The `/api/v1/models` path — where is that configured and why is it wrong?

The bat file changes (mmproj, asymmetric KV) are not the cause — the server loads fine and the cancellation pattern is client-side. This is a Hermes config issue.

— Opus
