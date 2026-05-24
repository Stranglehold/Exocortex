# MTP Build Validation
## am17an/llama.cpp mtp-clean branch | RTX 3090 | Qwen3.6-27B-MTP-UD-Q4_K_XL

**Date:** 2026-05-10
**Build commit:** _fill in — run `git -C inference/llama-cpp-mtp rev-parse HEAD`_
**Model:** Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf (`havenoammo/Qwen3.6-27B-MTP-UD-GGUF`)
**Baseline comparison:** TurboQuant build (Madreag/turbo3-cuda) at turbo4-K/turbo3-V, CTX=163840

---

## Test Environment

| Item | Value |
|------|-------|
| GPU | RTX 3090 24GB |
| CUDA version | 12.8 |
| Host RAM | 64GB |
| CTX size (MTP tests) | 130000 |
| KV cache type | q8_0 K+V (standard llama.cpp — turbo3/4 only in Madreag fork) |
| Flash attention | on |
| Parallel slots | 1 |
| CPU threads | 8 |

### Architecture Notes (Qwen3.6-27B-MTP-UD)

**Critical finding:** Qwen3.6-27B uses DeltaNet SSM layers (49/65 layers) with only 16/65 full attention layers (`full_attention_interval=4`). The SSM recurrent state cannot be checkpointed, which means **prompt cache is invalidated every turn** — llama.cpp forces full context re-processing on each new request regardless of overlap. This produces a per-turn prefill cost that scales linearly with accumulated context length.

**Impact on decode speed:** None — SSM only affects prefill, not generation.
**Impact on agentic use:** Significant at long context (>5K tokens accumulated). At ~140 tok/s prefill, a 10K-token context costs ~70 seconds of prefill per turn.

**KV cache size (corrected):** `n_embd_head_k=256`, 16 attention layers → 4,318 MiB at 130K context (4× larger than initially projected from Qwen3.5 assumptions).

---

## Results Table

| Metric | Config C: No MTP | Config B: MTP n=2 | Config A: MTP n=3 |
|--------|-----------------|-------------------|-------------------|
| Decode TPS | **35.53** | Not tested | **54.28** |
| Time to first token (s) | 0.20s | — | ~0.22s |
| Wall time — merge sort (s) | 14.28s | — | 9.21s |
| Acceptance rate | N/A | — | 69.3% (337/486 drafts) |
| Peak VRAM idle (MiB) | — | — | **24,270** (306 MiB headroom) |
| Output correct | Baseline | — | Not yet verified |
| A0 integration | Not tested | — | Not tested |

---

## Test 1: Raw TPS

**Prompt:** "Write a Python implementation of merge sort with type hints, docstrings, and comprehensive tests."
**Max tokens:** 500

Run command for each config (PowerShell):
```powershell
$body = '{"model":"qwen3.6-27b","messages":[{"role":"user","content":"Write a Python implementation of merge sort with type hints, docstrings, and comprehensive tests."}],"max_tokens":500,"stream":false}'
Invoke-RestMethod -Uri "http://localhost:1235/v1/chat/completions" -Method POST -ContentType "application/json" -Body $body
```

Check server console for `eval time` and `prompt eval time` lines.

**Config C (no MTP) results — 2026-05-10:**
- Decode TPS: **35.53 tok/s** (run 1), **35.01 tok/s** (run 2)
- Prefill TPS: 139.37 tok/s (run 1, cold GPU), 280.12 tok/s (run 2, warm)
- TTFT: 200.90 ms (28-token prompt, run 1)
- Wall time (500 tokens): 14.28s
- Prompt tokens: 28 (benchmark only — does not include system prompt)
- DeltaNet forced re-process confirmed on run 2: `forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory)`

**Interpretation:** 35.5 tok/s decode is ~1.7× the TurboQuant baseline (~21 tok/s on Qwen3.5-27B). This is Config C — no MTP. The improvement comes from a combination of the am17an build's CUDA kernels and Qwen3.6's smaller effective KV footprint (16 attention layers vs Qwen3.5's full attention). MTP has not been applied yet.

**Config B (MTP n=2) results:**
- Not tested — Config A result (run 2, without Docker) was strong enough to proceed.

**Config A (MTP n=3) results:**

Run 1 — 2026-05-10, Docker containers running simultaneously:
- Decode TPS: **4.01 tok/s** — VRAM overflow to CPU confirmed as cause (see VRAM notes)
- Draft tokens: 516 attempted, 327 accepted → 63.4% acceptance
- Wall time (500 tokens): 124.5s

Run 2 — 2026-05-10, Docker Desktop stopped, MTP server only:
- Decode TPS: **54.28 tok/s**
- Prefill: 128.13 tok/s
- Wall time (500 tokens): **9.21s**
- Draft tokens: 486 attempted, 337 accepted → **69.3% acceptance**
- Gain vs Config C: **+52.8%** throughput (54.28 vs 35.53)
- Gain vs TurboQuant baseline: **+2.58×** (54.28 vs ~21 tok/s)

---

## Test 2: VRAM Usage

Monitor with `nvidia-smi` during generation for each config.

| Config | Idle VRAM | Peak during generation |
|--------|-----------|----------------------|
| No MTP | | |
| MTP n=2 | | |
| MTP n=3 | | |

---

## Test 3: Output Quality

Merge sort task output from each config (truncated if long):

**Config C output:** _paste or describe_

**Config B output:** _identical to C? note any differences_

**Config A output:** _identical to C? note any differences_

MTP is mathematically lossless — differences indicate a bug in the build or model.

---

## Test 4: Agent Zero Integration

Point A0 at port 1235 (MTP server) in settings, run the merge sort baseline task.

- [ ] JSON tool calls formatted correctly
- [ ] Response tool fires correctly
- [ ] No format errors from MTP interaction
- [ ] Acceptance rate from A0 workload (check server log):

Notes:

---

## Test 5: Long Context Stability

Paste a large document or code file as context, verify MTP acceptance rate at longer lengths.

**Note:** DeltaNet forces full re-processing per turn. Prefill cost scales linearly with context.
Estimated prefill time per turn at 140 tok/s:
- 2K tokens → ~14s/turn
- 5K tokens → ~36s/turn
- 10K tokens → ~71s/turn
- 40K tokens → ~286s/turn (impractical for interactive use)

| Context length | Prefill time/turn (estimated) | Acceptance rate | Notes |
|---------------|------------------------------|----------------|-------|
| ~2K tokens | ~14s | | |
| ~10K tokens | ~71s | | |
| ~40K tokens | ~286s (impractical) | | |

---

## MTP vs TurboQuant Comparison

| Metric | TurboQuant (current) | MTP Config C (no MTP) | MTP best config |
|--------|---------------------|----------------------|-----------------|
| Decode TPS | ~21 (Club-3090 baseline) | **35.53** | TBD |
| Model | Qwen3.5-27B | Qwen3.6-27B | Qwen3.6-27B |
| KV type | turbo4-K/turbo3-V | q8_0 K+V | q8_0 K+V |
| CTX | 163840 | 130000 | 130000 |
| Per-turn prefill cost | Cacheable (negligible) | Full re-process (DeltaNet) | Full re-process (DeltaNet) |
| VRAM at max CTX | ~21.5 GB | ~21.9 GB (estimated) | TBD |
| Acceptance rate | N/A | N/A | TBD |
| A0 integration | Verified | Not yet tested | TBD |

---

## Decision

Based on Opus's decision matrix:

| MTP Result | TurboQuant Result | Recommended Action |
|-----------|-------------------|--------------------|
| >2x gain | Moderate gain | Prioritize merged build |
| ~1.5-2x gain | Moderate gain | Merge both — worth effort |
| >2x gain | Marginal | MTP-only build as primary |
| Marginal | Wins | Stay on Madreag TurboQuant |

**Config C result:** 35.5 tok/s decode without MTP = **~1.7× TurboQuant baseline**.

**Config A result:** 4.01 tok/s with MTP n=3 = **−88.7% vs Config C**. MTP is non-functional.

**Root cause (primary hypothesis):** DeltaNet SSM layers cannot parallelize verification. Standard speculative decoding accelerates because the verifier processes all k+1 draft tokens in a single parallel forward pass. DeltaNet's recurrent state is sequential — each token's SSM state depends on the previous one. The likely result is ~3 sequential forward passes per verification step instead of one parallel pass, inverting the expected speedup. The PR author's benchmarks were likely on attention-dominant or attention-only architectures; Qwen3.6-27B's 49/65 SSM ratio is unusually high.

**Alternative hypothesis (Jake):** MTP heads require additional VRAM. If total VRAM exceeds 24GB at MTP n=3 context, inference offloads to CPU — dropping from ~35 tok/s to ~4 tok/s. Verify with `nvidia-smi` during MTP generation. If VRAM is <23GB, the SSM hypothesis is primary. If VRAM is at/near 24GB and CPU usage spikes, this is the cause.

**Actual result:** MTP on Qwen3.6-27B-UD is non-viable on the RTX 3090 with the am17an build. Config C (no MTP) is the practical outcome of this eval.

**Recommendation:** Per Opus's decision matrix — falls into "Marginal / TurboQuant wins" row. Two paths forward:
1. **Switch primary build to am17an without MTP** — 1.7× decode gain, but loses TurboQuant KV compression (limited to ~130K context at q8_0 vs 163K with turbo4/3)
2. **Merge investigation** — combine am17an CUDA kernels with Madreag TurboQuant KV types. Gets both the decode speedup and extended context. Higher engineering cost.
3. **Stay on TurboQuant** — known-good, 163K context, ~21 tok/s. Safe default if merge is not worth the effort.

---

## Build Notes / Issues Encountered

- **Visual Studio path:** `BuildTools\VC\Auxiliary\Build\vcvars64.bat` uses `\18\` (VS 2022 BuildTools). Standard `\2022\` paths may differ — check actual install.
- **MTP flags:** `--spec-type mtp --spec-draft-n-max N` (not `--draft-*` — these are the am17an branch flag names)
- **KV cache size miscalculation:** Initially projected 8 attention layers at head_dim=128. Actual: 16 attention layers (`full_attention_interval=4`, 65 total), head_dim=256. KV cache is 4× larger than projected → 4,318 MiB at 130K context. CTX was revised from 80K to 130K after confirming VRAM budget.
- **turbo3/turbo4 KV types unavailable:** These only exist in Madreag fork. am17an build uses standard q8_0/q4_0. To get both MTP and TurboQuant, the forks must be merged.
- **DeltaNet SSM architecture:** Qwen3.6-27B cannot cache recurrent state between turns. Every API call triggers full context re-processing. This is a fundamental model architecture constraint, not a build issue.
- **Port:** 1235 (separate from TurboQuant's 1234 — both can run simultaneously for comparison)

---

## Next Steps

- [x] Config C baseline complete — 35.53 tok/s
- [ ] Run Config A (MTP n=3): edit `start_mtp.bat` → `MTP_DRAFT_N=3`, restart, repeat benchmark
- [ ] Run Config B (MTP n=2): edit `start_mtp.bat` → `MTP_DRAFT_N=2`, restart, repeat benchmark
- [ ] Fill VRAM table with nvidia-smi readings during each config
- [ ] Test A0 integration on short-context task (tool calls + response)
- [ ] Report results to `team-comms/kestrel-to-opus/mtp_results_20260510.md`
- [ ] If MTP wins: investigate merging am17an branch with Madreag TurboQuant fork
- [ ] If Qwen3.6 shows quality improvement over Qwen3.5 on A0 workloads: flag for model upgrade decision
