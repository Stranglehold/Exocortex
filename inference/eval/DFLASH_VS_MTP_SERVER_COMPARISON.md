# DFlash vs MTP — Server Mode Comparison
## RTX 3090 · CUDA 12.8 · Windows 10 · 2026-05-12

---

## Summary

| Backend | Server TPS | AR Baseline | Speedup | A0 Compatible | VRAM | Notes |
|---------|-----------|-------------|---------|---------------|------|-------|
| TurboQuant (Madreag, Qwen3.5) | ~21 | ~21 | 1.0x | ✅ | ~19 GB | Baseline |
| DFlash buun (Qwen3.6) | 38.6 | 24.8 | 1.56x | ❌ | ~19.5 GB | Context limit bug at >8192 |
| **MTP am17an (Qwen3.6)** | **43.7** | **26.9** | **~1.6x** | **✅** | **22.4 GB** | **Active backend · 80K ctx · 71.6% AR** |

---

## Backends Compared

### DFlash buun (`spiritbuun/llama.cpp`)
- Model: `Qwen3.6-27B-Q4_K_M.gguf` + `dflash-draft-3.6-q8_0.gguf`
- Port: 8000
- Results: 38.6 tok/s (raw /completion), 37.9 tok/s (chat API), 1.56x AR speedup
- Acceptance rate: 79.7–80.2%
- **A0 blocker:** Context size bug — crashes at `-c > 8192`. A0 system prompt is 10,069 tokens. Cannot serve A0 agent workloads.

### MTP am17an (`llama-cpp-mtp`, PR #22673 branch)
- Model: `havenoammo/Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf` (MTP heads grafted, 16.82 GB)
- Port: 1235
- KV cache: `-ctk q8_0 -ctv q4_0` (required — q8_0/q8_0 causes OOM due to MTP head buffer)
- Context: 130K tokens (A0 system prompt fits)

---

## MTP Server Configuration — Issues Encountered and Fixes

### Issue 1: `-fit` auto-tuner abort
**Symptom:** Server exits immediately with `failed to fit params to free device memory`.
**Root cause:** The `-fit` auto-tuner projects 21,946 MiB needed vs 22,736 MiB free, but wants 1,024 MiB safety margin — 234 MiB short.
**Fix:** Add `-fit off` to the launch command. Actual allocation succeeds within physical VRAM limits.

### Issue 2: MTP head load crash (`invalid vector subscript`)
**Symptom:** Main model loads fine; MTP head load crashes with `invalid vector subscript` at `load_tensors`.
**Root cause:** After main model + KV (q8_0/q8_0) + recurrent + compute buffers, CUDA reports 0 MiB free for the MTP head's new backend buffer allocation. Buffer allocation failure leaves `bufs` map empty; `bufs.at()` throws.
**Fix:** Change V cache from q8_0 to q4_0 (`--cache-type-v q4_0`). Saves 1,016 MiB. MTP head loads with 655 MiB free (enters CUDA virtual memory zone for the 1,425 MiB head buffer, which works with WDDM backing).

### Issue 3: Thinking tokens active by default
**Symptom:** `enable_thinking: false` in request body routes thoughts to `reasoning_content` but doesn't suppress thinking computation. 1024-token budget consumed by reasoning before any response is emitted.
**Fix:** Add `--reasoning off` to launch command (same as DFlash buun config). Suppresses thinking generation at server level. `enable_thinking: false` in request body remains required to prevent chat template from injecting `<think>` prefix.

---

## MTP A0 Integration Tests (2026-05-12)

All tests run against `http://127.0.0.1:1235/v1/chat/completions` with `enable_thinking: false` in body.

| Test | Result | Notes |
|------|--------|-------|
| JSON tool-call format | ✅ PASS | `{"thoughts":..., "tool_name":"response", "tool_args":{"text":"..."}}` correct |
| Multi-turn context coherence | ✅ PASS | 4-turn math chain, secret number preserved correctly across 6 messages |
| Long generation stability (1024 tok) | ✅ PASS | `finish_reason=length`, no KV cache errors, no thinking token bleed |
| `host.docker.internal:1235` from container | ✅ PASS | `{"status":"ok"}` from exocortex_v16 |
| A0 JSON format from Docker container | ✅ PASS | Python test confirmed correct JSON output from inside container |

---

## Speed Analysis

### Raw TPS measurements (2026-05-12)

| Config | TPS | Notes |
|--------|-----|-------|
| AR baseline (no MTP, same model, q8_0/q4_0, 130K ctx) | 26.93 tok/s | havenoammo Q4_K_XL |
| MTP n=3 (q8_0/q4_0, 130K ctx) | 22.9–32.4 tok/s | High variance — WDDM paging (only ~100–270 MiB free) |
| **MTP n=3 (q8_0/q4_0, 80K ctx) — production config** | **43.7 tok/s** | **710 MiB free, WDDM stable, no paging** |
| MTP draft acceptance rate | 68–72% | 71.6% confirmed at 80K ctx |
| Tokens per decode call | ~3.1–3.2 | Expected: 1 + 0.72×3 = 3.16 |

### WDDM paging: the critical insight
At 130K context, VRAM headroom is ~100–270 MiB. Windows WDDM evicts the two 495 MiB compute buffers (990 MiB total) to system RAM during idle micro-pauses. Each decode step triggers a page-in at PCIe bandwidth (~10 GB/s) — this is the source of 4 tok/s degradation observed during live A0 use.

**Fix:** Reduce context to 80K. Saves ~1,350 MiB on KV cache → 710 MiB free → WDDM does not page → stable 43.7 tok/s. A0 system prompt (10,069 tokens) + 70K working context is adequate for all agent workloads.

### vs. Kestrel's May 10 measurements
| Config | Kestrel | This session (130K) | This session (80K) | Delta vs Kestrel |
|--------|---------|---------------------|---------------------|-----------------|
| AR baseline | 35.53 tok/s | 26.93 tok/s | — | −8.6 |
| MTP n=3 | 54.28 tok/s | 22.9–32.4 tok/s | **43.7 tok/s** | −10.6 |
| Acceptance rate | 69.3% | 68–70% | 71.6% | ≈same |

**Root cause of remaining gap vs Kestrel (43.7 vs 54.28):**
1. **Q4_K_XL vs Q4_K_M**: XL quantization has higher precision on some layers, increasing compute per token. Froggeric Q4_K_M would reduce this.
2. **Context size effect**: 80K vs Kestrel's run context. Smaller KV = faster attention.
3. **VRAM headroom**: 710 MiB free vs Kestrel's ~300 MiB free (but Kestrel used q8_0/q8_0 with less WDDM impact in their session).

### VRAM breakdown (with MTP active, q8_0/q4_0)

| Component | 130K ctx | 80K ctx |
|-----------|----------|---------|
| Main model weights (Q4_K_XL) | 16,534 MiB | 16,534 MiB |
| Main KV cache (K q8_0, V q4_0, 16 attn layers) | 3,302 MiB | ~2,032 MiB |
| Main recurrent state (SSM, 65 layers) | 598 MiB | 598 MiB |
| Main compute buffer | 495 MiB | 495 MiB |
| MTP head model buffer (1 layer + embeddings) | 1,425 MiB | 1,425 MiB |
| MTP head KV (1 layer) | 206 MiB | ~127 MiB |
| MTP head compute buffer | 495 MiB | 495 MiB |
| CUDA runtime + driver overhead | ~1,250 MiB | ~1,250 MiB |
| **Total** | **~24,305 MiB** | **~22,956 MiB** |
| **Free (physical)** | **~100–270 MiB** | **~710 MiB** |
| **WDDM paging?** | **Yes → 4 tok/s** | **No → 43.7 tok/s** |

---

## Recommended Path Forward

**Current production config (confirmed working for generation):**
MTP at 43.7 tok/s, 71.6% acceptance, 80K context. All A0 integration tests pass. Both containers configured. Server launch:
```
start_mtp.bat   (contains: -fit off --reasoning off --spec-type mtp --spec-draft-n-max 3, ctx=80000)
```

**⚠️ Live A0 use: prefill latency is the binding constraint (2026-05-13)**

Live agentic testing revealed unacceptable wall time (~5 min/turn) on investigation tasks. Root cause: MTP generation speedup only applies after prefill. Prefill is sequential and unaccelerated.

BST's investigation domain injects 49 tools across 21 files — easily 20–30K tokens of tool schemas — before any conversation history or system prompt. On a 27B model, prefilling 40–60K tokens takes 1–3 minutes. This dominates wall time regardless of generation speed.

**This is not a server configuration problem.** The server performs correctly. The constraint is architectural: large context prefill on a single 27B model. MTP does not help here.

**Status: pinned.** Revisit when one of these conditions changes:
- Tool injection volume is reduced (smarter domain filtering, fewer tools per domain)
- A faster prefill path exists (flash attention prefill, chunked prefill, or a smaller model handling tool dispatch)
- Froggeric Q4_K_M GGUF tested — smaller model may prefill faster

**To approach Kestrel's 54 tok/s (generation-only benchmark):**
1. Froggeric Q4_K_M GGUF (~15.4 GB vs 16.82 GB for XL) — saves ~1.4 GB VRAM, allows q8_0/q8_0 KV or more context headroom
2. Close Firefox/Discord/OrcaSlicer during inference sessions — frees ~1–2 GB GPU memory

**DFlash status:**
Remains viable for non-A0 workloads (short prompts, standalone benchmarks). Cannot serve A0 due to the `> 8192` context crash.

**Combined build (TurboQuant+MTP):**
`invalid vector subscript` crash in `load_all_data` for the qwen35_mtp partial-load path. Root cause: buffer allocation failure when MTP head context gets 0 MiB free (even with VRAM reduction strategies, the combined binary has a different memory layout). Deferred pending debug build investigation.

---

## Model Config (A0, both containers)

```json
{
  "allow_chat_override": true,
  "chat_model": {
    "provider": "lm_studio",
    "name": "jackrong/qwen3.6-27b",
    "api_base": "http://host.docker.internal:1235/v1",
    "ctx_length": 80000,
    "ctx_history": 0.7,
    "kwargs": { "temperature": "0", "enable_thinking": false }
  }
}
```

Applied to: `exocortex_v16`, `exocortex_v17` — `/a0/usr/plugins/_model_config/config.json`

Utility model and all other settings are controlled via the Agent Zero web UI. `allow_chat_override: true` ensures the web interface stays authoritative for anything not listed here.
