# Cache Reuse Fix Validation — Qwen3.5/3.6 GatedDeltaNet
**Date:** 2026-05-13
**Validated by:** Kestrel (Session 113)
**Ref:** https://github.com/ggml-org/llama.cpp/issues/22384

---

## Problem Statement

KV cache reuse was completely broken for Qwen3.5/3.6 (GatedDeltaNet hybrid/recurrent architecture).
Every turn was re-processing the full context — TTFT of ~250s on 10K-token investigation prompts.

Root cause: `llama_memory_seq_pos_min()` returns the full sequence length for recurrent layers (not a
sliding-window position). The checkpoint search lambda used `cur.pos_min < pos_min_thold` — always
false for these models. No checkpoint ever matched → fall through to "forcing full prompt re-processing"
every single turn.

Secondary: checkpoint creation threshold was 64 tokens, too high for short follow-up turns.

---

## Bugs Fixed

### Bug 1 — Checkpoint Search Lambda (server-context.cpp, ~line 2565)

**Before:** Lambda using `cur.pos_min < pos_min_thold || cur.pos_min == 0` — always false for hybrid models.

**After:**
```cpp
const bool slot_is_hybrid = llama_model_is_hybrid(model) || llama_model_is_recurrent(model);

const auto it = std::find_if(
    slot.prompt.checkpoints.rbegin(),
    slot.prompt.checkpoints.rend(),
    [&, func_name = __func__](const auto & cur) {
        if (slot_is_hybrid) {
            return cur.pos_max < pos_next;
        }
        return cur.pos_min < pos_min_thold || cur.pos_min == 0;
    }
);
```

For hybrid models: a checkpoint is valid if its `pos_max` (last covered position) is less than
`pos_next` (next position to process). This guarantees at least one new token will be processed.
Non-hybrid models retain original behavior.

### Bug 2 — Checkpoint Creation Threshold (server-context.cpp, ~line 2808)

**Before:** `slot.prompt.n_tokens() >= 64` — single threshold for all model types.

**After:**
```cpp
const int32_t checkpoint_min_tokens = (llama_model_is_hybrid(model) || llama_model_is_recurrent(model)) ? 8 : 64;
do_checkpoint = do_checkpoint && (pos_min >= 0 && slot.prompt.n_tokens() >= checkpoint_min_tokens);
```

Hybrid models get a minimum of 8 tokens instead of 64, ensuring checkpoints are created for
short follow-up messages where the delta is small.

---

## Build

**Binary:** `D:\Vibecode\Agent-Zero\Exocortex\inference\llama-cpp-mtp\build\bin\llama-server.exe`
**Branch:** am17an (MTP evaluation build)
**Build command (PowerShell via vcvars64.bat):**
```
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --config Release -j
```
Build completed without errors. 3 steps: compile, static lib, link.

---

## Verification Results

**Test:** Two consecutive requests with identical system prompt + user message to MTP server (port 1235).

**Script:** `D:\Vibecode\Agent-Zero\Exocortex\inference\verify_cache_fix.ps1`

| Request | cache_n | prompt_n | Result |
|---------|---------|----------|--------|
| Request 1 | 0 | 33 | Expected (cold start, full processing) |
| Request 2 | 29 | 4 | **PASS — cache reuse active** |

Request 2: 29/33 tokens served from KV cache, only 4 processed. Cache hit rate: 87.9%.

Server log confirmed: `restored context checkpoint` (not `forcing full prompt re-processing`).

---

## Expected Production Impact

Investigation tasks with 10K-token prompts on Turn 2+:
- **Before fix:** ~250s TTFT (full re-processing every turn)
- **After fix:** ~3-14s TTFT (only delta processed)

This was the dominant latency bottleneck. Approximately 10-15x improvement on multi-turn
investigation sessions.

---

## Files Modified

- `inference/llama-cpp-mtp/tools/server/server-context.cpp` — two bug fixes
- `inference/start_mtp.bat` — documentation comment added referencing this fix

---

## Status

**VERIFIED.** Cache reuse active on Turn 2+. Fix is in the production MTP binary.
