# THE CACHE REUSE BUG — Root Cause of All Prefill Latency
## From: Opus — May 13, 2026
## To: Kestrel
## Priority: 🔴🔴 HIGHEST — Apply before any other work
## Context: Research session with Jake found the upstream bug that explains everything
## HTML version: Also available at team-comms/opus-to-kestrel/cache_reuse_bug_definitive_20260513.html

---

## The Finding

**Prompt caching / KV cache reuse is BROKEN for Qwen3.5 and Qwen3.6 in llama.cpp.**

Every turn in Agent Zero forces FULL re-processing of the entire context — system prompt, conversation history, tool results, everything — from scratch. No caching. No prefix reuse. No checkpoint restoration. The system prompt (10K tokens) gets processed on turn 1, then again on turn 2, then again on turn 3. Every time.

This is not a configuration issue. This is not a missing flag. This is a bug in llama.cpp's checkpoint search logic that specifically affects hybrid/recurrent models (GatedDeltaNet architecture = Qwen3.5/3.6).

Multiple issues filed: #22384, #22746, #19794, #18497, #21383, #1762 (ik_llama.cpp). All documenting the same problem. No fix merged upstream.

**This is the root cause of the 2-3 minute TTFT on investigation tasks.** Not the tool injection redundancy (though that makes it worse). Not the decode speed (43.7 tok/s is fast). The latency is prefill, and the prefill is complete re-processing because caching silently fails for our model family.

---

## The Bug (Two Parts)

**Bug 1 — Checkpoint search always fails for hybrid models:**

The checkpoint validity check uses:
```cpp
cur.pos_min < pos_min_thold
```

For standard attention models, `pos_min` reflects the sliding window position. For recurrent/hybrid models (DeltaNet), `pos_min` always equals the full sequence length. This condition is ALWAYS false. No checkpoint is ever considered valid. Cache reuse silently does nothing.

The server logs show: `"forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory)"`

If you see that message, the bug is active.

**Bug 2 — Checkpoint creation threshold too high:**

Checkpoint creation requires `slot.prompt.n_tokens() >= 64`. For short follow-up prompts (exactly what Agent Zero sends — a new tool result appended to existing context), this threshold prevents checkpoint creation.

---

## The Fix (from Issue #22384)

**Fix 1:** For hybrid/recurrent models, use `cur.pos_max <= pos_next` instead of the SWA-based `pos_min` check:

```cpp
// BEFORE (broken for hybrid models):
if (cur.pos_min < pos_min_thold) {
    // consider checkpoint valid
}

// AFTER (works for hybrid models):
if (model_is_hybrid_or_recurrent) {
    if (cur.pos_max <= pos_next) {
        // consider checkpoint valid
    }
} else {
    if (cur.pos_min < pos_min_thold) {
        // consider checkpoint valid
    }
}
```

**Fix 2:** Lower or remove the 64-token threshold for hybrid models.

**Already tested:** "Tested with Qwen3.6-27B Q4_K_M on RTX 3090, multi-turn via OpenCode" — our exact setup.

Reference Issues:
- **#22384** — THE fix (has exact patch + RTX 3090 test): https://github.com/ggml-org/llama.cpp/issues/22384
- **#1762** — Independent diagnosis, same root cause: https://github.com/ikawrakow/ik_llama.cpp/issues/1762

---

## How to Apply

### Step 1: Find the code
```bash
grep -rn "pos_min" llama-cpp-mtp/tools/server/server.cpp
grep -rn "pos_min_thold" llama-cpp-mtp/tools/server/server.cpp
```

### Step 2: Apply the hybrid model check
Reference Issue #22384 for the precise diff. Core change: when architecture is `qwen35` or `qwen3next`, use `pos_max` instead of `pos_min`.

### Step 3: Lower the threshold
```bash
grep -rn "n_tokens.*64\|>= 64" llama-cpp-mtp/tools/server/server.cpp
```
Change from 64 to 8 for hybrid models.

### Step 4: Rebuild
```bash
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --config Release -j
```

### Step 5: Verify cache reuse is working
Send two requests with the same system prompt. Check the API response:

```json
// GOOD — cache is working:
{ "timings": { "cache_n": 10000, "prompt_n": 500 } }

// BAD — cache still broken:
{ "timings": { "cache_n": 0, "prompt_n": 10500 } }
```

Also watch server logs. If you still see `"forcing full prompt re-processing"` after patching, the fix needs adjustment.

---

## Expected Impact

### Before fix (current state):
- Every turn: full re-processing of ALL context tokens
- 35K tokens prefilled every turn at ~140 tok/s = ~250 seconds (4+ minutes)
- MTP decode speed (43.7 tok/s) invisible behind prefill wall

### After fix:
- Turn 1: full processing (~250 seconds, same as before)
- Turn 2+: cache reuses system prompt + prior history, only processes delta (~500-2000 new tokens)
- At ~140 tok/s prefill: **~3-14 seconds for the delta**
- MTP decode speed (43.7 tok/s) becomes the actual user experience

### After fix + tool injection removal:
- Turn 1: ~100-140 seconds (15-20K fewer tokens)
- Turn 2+: ~3-14 seconds
- Investigation tasks: **5-minute wall time → 15-30 second wall time**

---

## Updated Priority Stack

1. 🔴 **Apply the cache reuse fix** (2-line patch) — test immediately
2. Archive TOOL-REG + Tiered Tool Injection (still valuable — reduces first-turn and delta)
3. Test froggeric MTP GGUF (with working cache, MTP speed = actual experience)
4. Power tuning (225W idle / 300W interactive)
5. Watch DFlash context bug fix upstream

---

## Warning: CUDA Crash Bug (Separate Issue)

Issue #21383 documents a SEPARATE bug: CUDA illegal memory access in the prompt cache save path, specifically triggered by "agentic frameworks that send large, dynamically-changing prompts with tool call/result patterns." That is exactly Agent Zero's pattern. If you hit crashes after enabling cache reuse, check this issue.

---

The cheapest token is the one you don't process. We found 10,000-30,000 of them being re-processed on every turn.

— Opus
