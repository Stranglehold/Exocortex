# FUSED MTP + TURBOQUANT BUILD — Indras-Mirror Fork
## From: Opus — May 14, 2026
## To: Kestrel
## Priority: 🔴 HIGH — this is the combined build we've been trying to create, already done
## Goal: Something that works well, quickly, and consistently

---

## What This Is

Someone already built exactly what we spent days trying to cherry-pick. The Indras-Mirror fork fuses TurboQuant TBQ4 directly into the flash attention CUDA kernel — the FA reads raw TBQ4 bytes inline during attention computation. No separate dequant pass, no intermediate F16 buffer. MTP and shared tensor linking are included.

**Repo title: "200K ctx at 97 tok/s on 24GB"**

This is MTP + TurboQuant + shared tensors in one build. Not a merge of two PRs — a custom fused implementation that's architecturally better than merging would produce.

---

## Benchmarks (RTX 4090, same 24GB VRAM)

| Config | Decode TPS | Acceptance | Notes |
|--------|-----------|------------|-------|
| MTP n=3 + turbo3 KV | **80.6 tok/s** | **92.6%** | Best per-token speed |
| MTP n=5 + turbo3 KV | 79.6 tok/s | 90.1% | Diminishing returns past n=3 |
| Peak observed | 179 tok/s | — | Burst on predictable content |

**92.6% acceptance** — compare to our current 69.3%. The fused TBQ4 kernel + shared tensors give the draft head cleaner data to predict from.

**682 MiB VRAM saved** by shared tensor linking — the MTP head no longer loads a duplicate copy of token embeddings. This directly addresses the VRAM headroom problem (24,270 MiB with 306 MiB free) that made our am17an MTP build unstable.

**200K context** at 4.25 bits per value KV cache. Our current ceiling is 130K with q8_0/q4_0.

---

## Known Issues (Assessed for Our Use Case)

| Issue | Affects Us? | Mitigation |
|-------|------------|------------|
| Vision + MTP crashes | ❌ No — A0 is text-only | Use `--spec-type none` for vision tasks |
| nstages=2 garbled output | ❌ No — use nstages=0 | Default is nstages=0 (synchronous) |
| MTP requires `--parallel 1` | ✅ Yes but fine — A0 uses single slot | Single-slot serving matches our workload |
| 7B models crash with TBQ4 | ❌ No — we use 27B | 27B works fine (nb1=528 is 16-byte aligned) |
| MoE models may fail | ❌ No — we use dense 27B | Dense models work correctly |
| output.weight sharing causes 0% acceptance | ✅ Fixed in fork | `link_shared_tensors()` shares tok_embd only |

**No blockers for our use case.** Every known issue either doesn't apply (vision, 7B, MoE) or is already fixed in the fork (shared tensors).

---

## Build Instructions

```bash
# Clone
git clone https://github.com/Indras-Mirror/llama.cpp-mtp.git
cd llama.cpp-mtp

# Build for RTX 3090 (sm_86)
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --config Release -j
```

**Build notes:**
- Same CUDA toolchain as all prior builds (12.x, MSVC via vcvars64)
- sm_86 targets RTX 3090 specifically — same flag as Madreag and am17an builds
- The fused TBQ4 FA kernel compiles as part of the standard build — no extra flags

---

## Model Files

Use the froggeric MTP GGUF we already have (or download if not yet on disk):

```bash
# If not already downloaded:
huggingface-cli download froggeric/Qwen3.6-27B-MTP-GGUF \
  Qwen3.6-27B-Q4_K_M-mtp.gguf \
  --local-dir ./models/
```

The froggeric GGUF has:
- MTP heads baked in (Q8_0 precision)
- Fixed Jinja template (tool calls work in C++ runtimes)
- imatrix quantization (better quality than standard Q4_K_M)

Alternatively, the havenoammo Unsloth Dynamic GGUF also works.

---

## Server Launch

```bash
# Production config for Agent Zero
./build/bin/llama-server \
  -m ./models/Qwen3.6-27B-Q4_K_M-mtp.gguf \
  -ngl 99 -fa \
  --spec-type mtp --spec-draft-n-max 3 \
  -ctk turbo3 -ctv turbo3 \
  -c 130000 \
  --parallel 1 \
  --host 0.0.0.0 --port 1235
```

**Critical flags:**
- `--spec-type mtp` — enables MTP speculative decoding
- `--spec-draft-n-max 3` — draft 3 tokens per step (optimal per benchmarks, better than 5)
- `-ctk turbo3 -ctv turbo3` — fused TBQ4 KV cache (the FA kernel reads these directly)
- `--parallel 1` — required for MTP (single slot)
- `-c 130000` — 130K context (leaves VRAM headroom; can push to 200K if needed)

**Also critical — in every A0 request body:**
```json
{
  "enable_thinking": false
}
```
And server flag: `--reasoning off` or `-fit off`

Without these, the Qwen3.6 chat template injects thinking tokens that collapse draft acceptance from 92% to near zero. This is the same fix you discovered on the am17an build — it applies here too.

---

## Test Protocol

### Test 1: Build Verification
```bash
./build/bin/llama-server --help | grep -E "spec|turbo|tbq"
```
Confirm MTP and turbo cache types are present.

### Test 2: Benchmark — Raw TPS
```bash
# Start server, then:
curl -s -X POST http://localhost:1235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "Write a Python merge sort with type hints and tests."}],
    "max_tokens": 500,
    "enable_thinking": false,
    "stream": false
  }'
```
Extract TPS from response timings. **Target: 65+ tok/s on 3090.**

### Test 3: Cache Reuse Verification
Send two consecutive requests. Check `cache_n` in second response.
**The cache reuse patch should be applied to this fork too** — check if the checkpoint search code has the same `pos_min` bug. If so, apply the same fix from Issue #22384.

### Test 4: VRAM Check
```bash
nvidia-smi
```
Record peak VRAM. With shared tensor linking, expect ~23-23.5 GB — leaving 600-1000 MiB headroom vs the 306 MiB on the am17an build.

### Test 5: Agent Zero Integration
Point A0 at port 1235. Run:
- [ ] Merge sort baseline (JSON tool calls work?)
- [ ] Multi-turn conversation (context accumulates?)
- [ ] Tool call + response cycle (correct formatting?)
- [ ] Check for thinking token interference (acceptance rate in logs)

### Test 6: Acceptance Rate
Check server logs for MTP acceptance statistics.
**Target: 85%+ acceptance** (the fork gets 92.6% on 4090; 3090 should be similar since acceptance is model-dependent, not hardware-dependent).

---

## Results Table (fill in)

| Metric | Indras-Mirror | am17an MTP (prev) | TurboQuant (prev) |
|--------|--------------|--------------------|--------------------|
| Decode TPS | | 43.7 (production) / 54.28 (bench) | ~21 |
| MTP Acceptance | | 69.3% / 71.6% | N/A |
| TTFT Turn 1 | | 3-5 min | — |
| TTFT Turn 2+ | | ~30-60 sec (with cache fix) | — |
| Peak VRAM | | 24,270 MiB (306 free) | ~21,500 MiB |
| Max Context | | 130K | 163K |
| A0 Integration | | ✅ | ✅ |
| Tool Calls | | ✅ (enable_thinking: false) | ✅ |

---

## What Success Looks Like

Jake opens Agent Zero. The pre-warmer has already processed the system prompt during idle time. He types a message. First token appears in 10-30 seconds (cache hit). The model generates at 65-80 tok/s — fast enough that responses feel conversational, not like waiting for a batch job. Tool calls work. Context accumulates across turns without VRAM crashes. The monitoring dashboard shows turbo3 KV active, 92% acceptance rate, 600+ MiB VRAM headroom.

That's the production stack. One fork. Everything fused. No cherry-picks, no merges, no separate code paths fighting each other.

---

## Directory Structure

```
D:\Vibecode\Agent-Zero\Exocortex\inference\
├── llama-cpp-indras/              # NEW: the fused build
│   ├── build/
│   └── models/
│       └── Qwen3.6-27B-Q4_K_M-mtp.gguf
├── compile_indras.bat             # NEW
├── start_indras.bat               # NEW
├── eval/
│   └── INDRAS_BUILD_VALIDATION.md # NEW: fill in with results
├── archive/                       # All prior builds
│   ├── turbo3-cuda/
│   ├── llama-cpp-mtp/
│   ├── llama-cpp-combined/
│   ├── llama-cpp-atomicbot/
│   └── lucebox-dflash/
└── ...
```

---

## If It Doesn't Work

If the build fails or performance is significantly below expectations:

1. **Build fails on sm_86:** Check if the TBQ4 FA kernel uses CUDA features not available on Ampere (sm_86). The fork was developed on sm_89 (4090/Ada). Some CUDA intrinsics differ between Ampere and Ada. If so, check the Issues tab or open one.

2. **TPS significantly below 65:** Check VRAM utilization — if >23.5 GB, the shared tensor linking may not be working. Check server logs for `link_shared_tensors` messages.

3. **Acceptance rate below 80%:** Verify `enable_thinking: false` is in the request. Check that the GGUF has MTP heads (`--verbose` server flag shows tensor counts — should show 18 MTP tensors for 27B).

4. **Cache reuse not working:** Apply the same Issue #22384 patch. The fork is based on upstream + PR #22673, which has the same checkpoint search bug for hybrid models.

**Fallback:** The am17an MTP build at 43.7 tok/s is still working and A0-integrated. If Indras-Mirror has issues, we haven't lost anything.

— Opus
