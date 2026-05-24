# DFlash Build Validation
## lucebox-dflash (Luce-Org/lucebox-hub) + buun-llama-cpp (spiritbuun)
## RTX 3090 · CUDA 12.8 · Windows 10

---

## Build Environment

| Component | Value |
|-----------|-------|
| lucebox-dflash repo | `Luce-Org/lucebox-hub` (cloned 2026-05-11) |
| buun-llama-cpp repo | `spiritbuun/llama.cpp` fork (cloned 2026-05-11) |
| Compiler | MSVC 19.50 (VS 2026 BuildTools) |
| CUDA | 12.8.93 |
| CMake flags | `-G Ninja -DCMAKE_CUDA_ARCHITECTURES=86 -DCMAKE_CUDA_FLAGS=-allow-unsupported-compiler -DGGML_CUDA=ON -DGGML_NATIVE=ON -DGGML_CUDA_FA=ON -DGGML_CUDA_FA_ALL_QUANTS=ON` |
| Generator | Ninja |
| GPU | RTX 3090 (sm_86, 24 GB VRAM) |
| Build date | 2026-05-11 |

## Build Status

| Step | Status | Notes |
|------|--------|-------|
| lucebox-dflash cmake configure | ✅ Pass | Fixed: LNK2019 via `GGML_CUDA_CONVERT_API` macro in `convert.cuh` |
| `test_dflash.exe` compile | ✅ Pass | 249 targets |
| lucebox Python server | ✅ Pass | FastAPI + uvicorn, `server.py` |
| buun-llama-cpp cmake configure | ✅ Pass | `-allow-unsupported-compiler` required for CUDA 12.8 + VS2026 |
| buun `llama-server.exe` compile | ✅ Pass | 490 targets, completed overnight |
| Python venv | ✅ Created | fastapi, uvicorn, transformers, gguf |

## Model Paths

| Role | Path | Size |
|------|------|------|
| Target (3.6) | `D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf` | 15.41 GB |
| Target (3.5) | `D:\LMStudio\Models\Jackrong\Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-GGUF\Qwen3.5-27B.Q4_K_M.gguf` | 15.4 GB |
| Draft (3.6 Q8_0) | `D:\LMStudio\Models\spiritbuun\Qwen3.6-27B-DFlash-GGUF\dflash-draft-3.6-q8_0.gguf` | 1.72 GB |
| Draft (3.5 fallback) | lucebox `models/dflash-draft-3.5/` (z-lab/Qwen3.5-27B-DFlash) | ~2 GB |

---

## Test Results (buun-llama-cpp, 2026-05-12)

### Test 1: AR Baseline — Qwen3.6-27B Q4_K_M

Server flags: `-ngl 99 -c 8192 -fa on -b 512 -ub 512 --reasoning off`
Prompt: merge sort in Python, raw `/completion`, temp=0, 400 tokens

| Run | Tokens | Time (s) | TPS |
|-----|--------|----------|-----|
| 1 | 400 | 16.12 | 24.8 |
| 2 | 400 | 15.93 | 25.1 |
| 3 | 400 | 16.27 | 24.6 |
| **avg** | | | **24.8** |

**AR Baseline: 24.8 tok/s**

---

### Test 2: DFlash (flat) — Qwen3.6-27B Q4_K_M + Q8_0 draft

Server flags: `--spec-dflash-default -ngl 99 -ngld 99 -c 8192 -cd 2048 -fa on -b 256 -ub 64 --reasoning off`
Key: `enable_thinking: false` required in request body, raw `/completion`, temp=0

#### Raw `/completion` endpoint (5 runs + 1 warmup)

| Run | Tokens | Time (s) | TPS | ms/tok (server) |
|-----|--------|----------|-----|-----------------|
| warmup | 200 | — | — | — |
| 1 | 400 | 11.01 | 36.3 | 26.9 |
| 2 | 400 | 10.31 | 38.8 | 25.0 |
| 3 | 400 | 10.22 | 39.1 | 25.3 |
| 4 | 400 | 10.13 | 39.5 | 25.1 |
| 5 | 400 | 10.23 | 39.1 | 25.2 |
| **avg** | | | **38.6** | **25.3** |

**DFlash raw: 38.6 tok/s avg, stdev=1.3, 1.56x AR**

#### Chat `/v1/chat/completions` endpoint (5 runs, `enable_thinking: false`)

| Run | Tokens | Time (s) | TPS |
|-----|--------|----------|-----|
| 1 | 270 | 6.94 | 38.9 |
| 2 | 345 | 9.29 | 37.2 |
| 3 | 345 | 9.18 | 37.6 |
| 4 | 345 | 9.04 | 38.2 |
| 5 | 345 | 9.10 | 37.9 |
| **avg** | | | **37.9** |

**DFlash chat API: 37.9 tok/s avg, stdev=0.7, 1.53x AR**

**Draft acceptance rate**: 79.7–80.2% (all 10 runs, very stable)

---

### Test 3: Cross-Family Draft (3.5 draft → 3.6 target) — FAILED

Attempt: lucebox-dflash with Qwen3.5-DFlash draft serving Qwen3.6-27B target

| Metric | Value |
|--------|-------|
| TPS | 6.84 tok/s |
| vs AR | 0.28x (slower) |

**Verdict: Cross-family DFlash is not viable for Qwen3.6.** Root cause: Qwen3.6 uses GatedDeltaNet SSM architecture (49/65 layers are SSM). The 3.5 draft cannot predict the 3.6 target's SSM state transitions. Do not attempt 3.6-target + 3.5-draft.

---

### Test 4: Thinking-Tag Injection — Root Cause Analysis

**Symptom (initial)**: DFlash engaged but only 22 tok/s, `#acc tokens = 0` in dflash stats.

**Root cause**: `--reasoning off` sets `thinking=0` in server, but the Qwen3 chat template still injects `<|im_start|>assistant\n<think>\n\n</think>\n\n` at generation start via `generation_prompt`. The draft model was not trained on this prefix → catastrophic acceptance collapse (25% token-level acceptance, 0 DFlash draft acceptance).

**Fix**: Pass `enable_thinking: false` in the API request body for `/v1/chat/completions`, OR use the raw `/completion` endpoint with manually-formatted prompt (no chat template prefix).

| Config | TPS | Acceptance |
|--------|-----|------------|
| chat API, no thinking flag | 22.3 tok/s | 25% |
| chat API + `enable_thinking: false` | 37.9 tok/s | 80% |
| raw `/completion` | 38.6 tok/s | 80% |

---

### Test 5: Agent Zero Integration — Functional

Test method: direct HTTP requests to buun server at `http://127.0.0.1:8000`, OpenAI-compatible chat completions API.

| Test | Result | Notes |
|------|--------|-------|
| JSON tool-call format | ✅ PASS | `{"thoughts":..., "tool_name":..., "tool_args":{...}}` correctly generated |
| Multi-turn context coherence | ✅ PASS | 4-turn math chain, context preserved across turns |
| Long generation stability (1024 tok) | ✅ PASS | 32.5 tok/s, no KV cache errors |
| Tool call + response cycle | ✅ PASS | Correct format on short prompts (52 tokens) |
| `host.docker.internal:8000` reachable from container | ✅ PASS | `{"status":"ok"}` from container |

**A0 Integration config required:**
```json
{
  "chat_model": {
    "api_base": "http://host.docker.internal:8000/v1",
    "name": "local",
    "kwargs": {"temperature": "0", "enable_thinking": false}
  }
}
```

Note: `enable_thinking: false` MUST be in kwargs for correct DFlash acceptance rate. Without it, thinking tags are injected by the chat template and acceptance collapses from 80% to 25%.

---

### DDTree Status

DDTree (tree-structured verification with `--tree-budget N`) is **not available in `llama-server`** — only in the `speculative-simple` example binary. The server only supports flat DFlash (linear 7-token draft).

Model card claims 87–97 tok/s. Gap analysis:
- DDTree with budget=22 would verify 22 paths per target pass, increasing effective accepted tokens from ~5.6 to potentially 8–14 per cycle
- SSM architecture overhead: verifying 8 tokens takes ~105ms (vs theoretical ~16ms for pure attention). GatedDeltaNet SSM state computation does not batch as efficiently as attention
- Quantization: card uses UD-Q4_K_XL (tuned), we use Q4_K_M

**Server-mode ceiling**: ~38–39 tok/s (flat DFlash). To get 87–97 tok/s, use `speculative-simple` binary with `--tree-budget 22` (not HTTP-server compatible).

---

### Test 6: Configuration Parameters — Validated

| Parameter | Value | Notes |
|-----------|-------|-------|
| `-c` (main context) | 8192 | Sufficient for A0 agentic sessions |
| `-cd` (draft context) | 2048 | **Must be ≥2048.** 256 causes draft truncation at token ~225, degrading second half of generation |
| `-np` (slots) | 1 | Single slot, adequate for A0 |
| `-ngl` / `-ngld` | 99 / 99 | All layers on GPU |
| `-fa` | on | Flash attention enabled |
| `-b` / `-ub` | 256 / 64 | DFlash auto-cap (per ubatch-vram-deflate.md) |
| `--reasoning off` | required | Sets thinking=0 in server, but chat template still injects `<think>` tags |
| `--spec-dflash-default` | required | Sets type=DFLASH, n_max=7, p_min=0 |
| `--jinja` | required | Enables Jinja chat templates |

---

## Summary Table

| Metric | buun DFlash (flat) | AR Baseline | MTP (prev) |
|--------|-------------------|-------------|------------|
| Decode TPS | **38.6** (raw) / **37.9** (chat) | 24.8 | 54.28 |
| DFlash speedup | **1.56x** | N/A | ~4x |
| Draft acceptance | **79.7–80.2%** | N/A | N/A |
| Max context | 8192 | 8192 | 130K |
| VRAM | ~19.5 GB (target + draft) | ~16 GB | 24.27 GB |
| A0 functional | ✅ PASS | ✅ (baseline) | Not tested |
| Thinking-off req. | `enable_thinking: false` in req | N/A | N/A |

---

## Critical Notes

1. **`enable_thinking: false` is mandatory** in all API requests to the buun server. Without it, the chat template injects `<think></think>` prefix, collapsing DFlash acceptance from 80% to 25%.

2. **`-cd 2048` minimum** for draft context. `-cd 256` causes draft truncation after ~225 generated tokens, degrading the second half of any response.

3. **Q8_0 draft only**: Per spiritbuun model card and confirmed in SWA layer analysis, Q4 quantization of the DFlash draft model reduces acceptance by ~30–40%. Use `dflash-draft-3.6-q8_0.gguf`.

4. **Cross-family (3.5 draft → 3.6 target) does not work**: Qwen3.6 SSM architecture makes cross-family speculative decoding ineffective (0.28x AR).

5. **DDTree unavailable in server mode**: The 87–97 tok/s model card figure uses `speculative-simple` with DDTree. Server-mode ceiling with flat DFlash is ~38–39 tok/s (1.56x AR).

6. **KV cache invalidation on request switch**: The first request after a different-format request triggers full prompt re-processing (SWA cache invalidation). This adds ~260ms latency to the first token. Subsequent requests to the same-format endpoint use cached prompts.
