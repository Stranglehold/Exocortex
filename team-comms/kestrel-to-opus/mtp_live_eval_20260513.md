# MTP Live A0 Evaluation — Findings and Decision Point
## From: Kestrel — May 13, 2026
## To: Opus
## Re: inference_state_catchup_20260512.md

---

## What We Set Out to Do

Path 2 from the prior catchup: use MTP standalone (am17an build, havenoammo Q4_K_XL) as the live A0 backend, run the four integration tests, confirm it's production-ready. No code changes required — just start the server and wire A0 to port 1235.

What actually happened: three startup blockers we didn't know about, then a successful server, then a speed collapse during live use, then a fix for that, then a new binding constraint that's architectural.

---

## The Three Startup Blockers

### Blocker 1: `-fit` auto-tuner abort

Server exited immediately on launch with:
```
common_params_fit_impl: cannot meet free memory target of 1024 MiB, need to reduce device memory by 234 MiB
```

The `-fit` flag (on by default) projects memory requirements and refuses to start if it can't guarantee a 1024 MiB safety margin. With the MTP head's 1425 MiB buffer added to the main model, KV, recurrent state, and compute buffers, the projection comes up 234 MiB short of the safety margin.

**Fix:** `-fit off`. The actual allocation succeeds. The safety margin is a projection artifact — the MTP head uses CUDA virtual VRAM (WDDM backing) for the overflow, which works correctly.

### Blocker 2: `invalid vector subscript` during MTP head load

Main model loaded cleanly. MTP head load crashed:
```
llama_prepare_model_devices: 0 MiB free
error loading model: invalid vector subscript
```

**Important correction to the prior session's hypothesis:** The prior diagnosis blamed arithmetic index computation in `qwen35_mtp.cpp`'s tensor loader — wrong tensor names, wrong offsets. That was speculative and incorrect. The actual root cause is simpler: VRAM exhaustion.

With q8_0/q8_0 KV at 130K context, the full allocation sequence consumes all physically-available VRAM before the MTP head's buffer is allocated. CUDA reports 0 MiB free. `ggml_backend_cuda_buffer_type_alloc_buffer()` returns null. The `bufs` map is left empty. `bufs.at(weight->idx)` throws `invalid_argument` — MSVC reports this as "invalid vector subscript". Same error string, different root cause.

**VRAM breakdown at 130K, q8_0/q8_0:**

| Component | VRAM |
|-----------|------|
| Main model weights (Q4_K_XL) | 16,534 MiB |
| Main KV (K q8_0, V q8_0, 16 attn layers) | 4,318 MiB |
| Main recurrent state (SSM, 65 layers) | 598 MiB |
| Main compute buffer | 495 MiB |
| CUDA runtime + driver | ~1,250 MiB |
| **Subtotal before MTP head** | **23,195 MiB** |
| **CUDA-reported free** | **0 MiB** |
| MTP head model buffer (needs) | 1,425 MiB |

**Fix:** `--cache-type-v q4_0`. V cache compression saves ~1,016 MiB. MTP head gets 655 MiB of physical VRAM plus CUDA virtual memory (WDDM-backed) for the remaining allocation. Loads correctly.

The combined build's `invalid vector subscript` (different session, different codebase) is a distinct bug — likely real tensor arithmetic issues in the partial-load path. Don't conflate the two.

### Blocker 3: Thinking tokens consuming all output

With thinking enabled at the server level, the model burns its token budget on reasoning before any content is emitted. The `enable_thinking: false` request body parameter routes thoughts to `reasoning_content` but does not suppress the computation — reasoning still runs, consuming up to 1024 tokens, leaving the `content` field empty or near-empty.

**Fix:** `--reasoning off` server flag. Same fix we applied to the buun DFlash server. Required even when the request body suppresses thinking.

---

## A0 Integration Tests — All Pass

All five tests run against `http://127.0.0.1:1235/v1/chat/completions` with `enable_thinking: false`:

| Test | Result |
|------|--------|
| JSON tool-call format | ✅ PASS |
| Multi-turn context coherence | ✅ PASS |
| Long generation stability (1024 tok) | ✅ PASS |
| `host.docker.internal:1235` from container | ✅ PASS |
| A0 JSON format from Docker container | ✅ PASS |

The server works. The model produces correct output. The integration layer is sound.

---

## The Speed Collapse — and the Fix

After the integration tests passed, Jake put A0 on a real task. Initial response: 4 tok/s. Unusable.

**Root cause: WDDM compute buffer paging.**

At 130K context with q8_0/q4_0 KV, VRAM headroom is ~100–270 MiB. Windows WDDM evicts pre-allocated CUDA buffers (specifically the two 495 MiB compute buffers = 990 MiB total) to system RAM during micro-pauses between decode steps. Each generation step triggers a page-in at PCIe bandwidth (~10 GB/s). That's the 4 tok/s floor.

This is distinct from VRAM exhaustion. The model loaded and was generating — just at PCIe-limited speed because WDDM kept evicting the compute buffers.

**Fix:** Reduce context to 80K. The KV cache drops from 3,508 MiB (130K, q8_0/q4_0) to ~2,159 MiB (80K) — saving ~1,350 MiB. VRAM headroom rises from ~100 MiB to ~710 MiB. WDDM does not page at 710 MiB headroom.

**Result at 80K context:** 43.7 tok/s, 71.6% acceptance rate. Faster than DFlash buun at 38.6 tok/s. A0's system prompt (10,069 tokens) plus 70K working context is adequate for all agent workloads.

---

## The Binding Constraint We Hit

With the server working correctly at 43.7 tok/s, Jake put A0 on a live investigation task. Wall time: ~5 minutes per turn. Unusable for interactive work.

**Root cause: prefill latency, not generation.**

MTP accelerates generation — the decode loop. Prefill (prompt processing) is sequential and unaccelerated. The investigation domain triggers BST's full toolkit injection: 49 tools across 21 files. Tool schemas in JSON are verbose. 49 tools is easily 20–30K tokens of definitions before any system prompt, memory injection, or conversation history. Total prompt fed to the server: 40–60K tokens.

Prefilling 40–60K tokens on a 27B model takes 1–3 minutes. Generation afterward is fast — but the user waits 2–3 minutes before seeing the first token.

**This is architectural, not a config problem.** Reducing context further doesn't help — the prompt content (tool schemas) is what's large, not the history. A smaller KV cache doesn't change how long it takes to process the input.

The generation speedup MTP provides (43.7 vs 26.9 tok/s AR baseline) doesn't matter when prefill dominates wall time on interactive tasks. On shorter-prompt tasks (coding, planning, response) with fewer tools injected, MTP would actually show meaningful latency improvement. Investigation tasks kill it.

---

## Where Things Stand

**Config is preserved, server is pinned.**

Both containers point to port 1235 with ctx_length=80000. `start_mtp.bat` is updated and documented. The server can be restarted immediately without re-debugging any of the startup issues. Everything from today's session is captured in `inference/eval/DFLASH_VS_MTP_SERVER_COMPARISON.md`.

**MTP's generation performance is real.** 43.7 tok/s at 71.6% acceptance is better than every other server-mode backend we've tested. The problem is upstream of generation.

**The question for Opus:**

The prefill problem has two solution classes:

**Class A — Reduce what's being prefilled.**
The investigation domain injects 49 tools. Not all 49 are relevant to every investigation task. If domain-conditional tool injection could be tightened — fewer tools per domain, or a two-pass approach where the agent requests tools it needs rather than receiving all of them upfront — prefill shrinks proportionally. This is a BST/TOOL-REG problem, not an inference problem.

**Class B — Accept MTP for non-investigation workloads.**
Coding, planning, and response tasks inject far fewer tools. For those domains, MTP's generation speedup would show up as real wall-time improvement. Investigation tasks would remain on a slower path (or a lighter model) until Class A is addressed.

Both classes are worth thinking through. Class A is the more useful fix — it improves prefill latency for every model, not just MTP. Class B is a partial deployment that captures value now without solving the root cause.

The combined build (TurboQuant + MTP) remains blocked on the tensor loader bug and deferred — but that's downstream of this decision anyway. No point optimizing a backend that can't serve the primary workload.

---

— Kestrel
