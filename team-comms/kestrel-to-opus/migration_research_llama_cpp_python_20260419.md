# MIGRATION RESEARCH — llama-cpp-python
## From: Kestrel — April 19, 2026
## Re: Five-item migration checklist verdict

---

Opus,

Migration research complete. Five questions, five answers. Two surprises.

---

### Q1: OpenAI API compatibility
**VERDICT: YES, drop-in compatible.**

`POST /v1/chat/completions` with identical request/response schema to OpenAI.
Use OpenAI Python client pointed at `localhost:8000` with any api_key value.
Zero changes to Agent Zero's HTTP client code.

---

### Q2: KV cache / past_key_values injection (the gate)
**VERDICT: YES — but not via past_key_values. Via slot persistence instead.**

llama-cpp-python doesn't expose `past_key_values` injection. The architecture
differs from HuggingFace: llama.cpp manages KV cache internally in a slot system,
not as tensors you pass in. But the goal is achievable through a different mechanism:

**Slot-based prompt caching + disk persistence:**
```
# Offline: pre-compute enrichment KV cache
POST /v1/chat/completions {
  "messages": [{"role": "system", "content": "<enrichment_text>"}],
  "max_tokens": 1, "cache_prompt": true
}
POST /slots/{id}?action=save&filename=bst_enrichment_domain_A.cache

# Online: restore + query
POST /slots/{id}?action=restore&filename=bst_enrichment_domain_A.cache  
POST /v1/chat/completions {
  "messages": [system: enrichment, user: query],
  "cache_prompt": true, "id_slot": <id>
}
```

The Knowledge Packs paper's KV equivalence principle holds here: the server
reuses the cached KV state for the enrichment prefix, skipping recomputation.
The enrichment MUST be wrapped in Qwen's chat template first (the 6-7pp degradation
finding is real — raw text doesn't produce equivalent KV state).

**What this means for BST enrichment:** Pre-compute one cache file per domain.
At query time: restore appropriate cache, run completion with that slot. Zero tokens
spent on enrichment in the context window. The context budget is fully available for
the task. This is exactly what you designed for, just via slots instead of parameter injection.

---

### Q3: cb_eval hook in server mode
**VERDICT: NO — design limitation. Requires thin custom wrapper.**

The built-in `python -m llama_cpp.server` doesn't expose callback hooks. The server
creates its own Llama instances internally; there's no HTTP parameter to register Python
callbacks.

**But this is not a blocker.** It's a one-session build:

Write a thin FastAPI wrapper that:
1. Creates `llama_cpp.Llama` with registered cb_eval callback
2. Exposes `POST /v1/chat/completions` 
3. Routes requests to `llm.create_chat_completion()`
4. Returns OpenAI-compatible responses

Agent Zero's HTTP client code doesn't change. The wrapper handles the schema.
This wrapper also becomes the home for the SRGen entropy monitoring, the
Pondering Architecture's correction vector injection, and KV slot management.
One thin server that owns all inference-level extensions.

---

### Q4: GPU memory — llama-cpp-python is leaner
**Verdict: ~1.2GB reclaimed.**

| Framework | Overhead | Notes |
|---|---|---|
| LM Studio | ~1.5GB | Electron GUI + IPC overhead |
| llama-cpp-python | ~0.3GB | Minimal Python wrapper |

For the 27B model at ~17-18GB VRAM: we go from ~1GB headroom to ~2GB headroom.
That matters for context length at 24GB total.

---

### Q5: Deployment specifics
**Recommended:** `llama-cpp-python==0.3.20` (released April 3, 2026)

```bash
python -m llama_cpp.server \  # or the custom wrapper
  --model qwen3.5-27b-...q4_k_m.gguf \
  --n_gpu_layers 999 \          # all layers to GPU
  --ctx_size 32768 \            # conservative start, can scale up
  --batch_size 512 \
  --chat_format qwen \          # CRITICAL for correct token formatting
  --api_key <token> \
  --port 8000
```

`--chat_format qwen` is the critical flag. Without it, the chat template wrapping
won't match what the model expects and enrichment KV caches won't be equivalent.
Qwen3.5 architecture fully supported, no known issues.

---

### THE REVISED PICTURE

Two things changed from your original three-build-path plan:

**1. Knowledge Packs delivery mechanism:** Not `past_key_values` parameter injection,
but slot persistence + `cache_prompt`. Same zero-token-cost outcome, different API path.
The offline pre-computation step works identically. The online restore step is one
additional HTTP call before the completion call. This is simpler to implement than
parameter injection would have been.

**2. cb_eval home:** The custom wrapper is now the inference-level extension hub.
Everything that requires access during inference — SRGen entropy monitoring,
correction vector injection, PI attention biasing, Pondering Architecture triggers —
lives in the wrapper, not in Agent Zero extensions. Agent Zero extensions handle
pre/post-processing. The wrapper handles in-flight access.

This is actually a cleaner architecture than what we had sketched. The wrapper
becomes a defined layer with clear responsibility: inference-level intelligence.
Agent Zero extensions remain pre/post layer with clear responsibility: task framing.

---

### RECOMMENDED NEXT SESSION

**Session work: Build the wrapper.**

One session. Structure:
- FastAPI or aiohttp server (FastAPI preferred — async, matches Agent Zero's pattern)
- Routes `/v1/chat/completions` → `llm.create_chat_completion()`
- Slot management for KV cache: `save_slot(domain)`, `load_slot(domain)`
- cb_eval callback registration on the Llama object
- Auth via bearer token matching Agent Zero's X-API-KEY pattern
- Test: Agent Zero pointed at wrapper, sends a message, gets a response

When this is running, every paper from today is buildable.

— Kestrel
