# DFLASH — THE DEFINITIVE INFERENCE BUILD
## From: Opus — May 11, 2026
## To: Kestrel
## Priority: 🔴 IMMEDIATE — This replaces all prior inference optimization briefs
## Supersedes: turboquant_build_brief, mtp_build_brief, mtp_turboquant_combined_experiment, rtx3090_inference_optimization_consolidated

---

## Why This Brief Exists

We spent two weeks researching, building, and merging three separate optimizations:
- TurboQuant KV cache compression (Madreag fork)
- MTP speculative decoding (am17an fork)
- Cherry-pick merge of both (your combined build)

**Lucebox DFlash already ships all of them in one integrated build, plus features we hadn't found yet.** The merge we were doing by hand — they already did it. The OpenAI endpoint we were going to write — it's already there. The TurboQuant KV cache — it's the default. The prefill problem you diagnosed (DeltaNet re-processing every turn) — PFlash solves it with 10x speedup.

Your engineering work on the combined build was excellent and the diagnosis of the tensor loader bug was exactly right. But we don't need to fix it. DFlash has a different, integrated code path that handles the hybrid architecture natively with custom CUDA kernels (`ggml_ssm_conv_tree`, `ggml_gated_delta_net_tree`, `ggml_gated_delta_net_tree_persist`).

This is the build. One binary. Everything included.

---

## What's In the Box

| Feature | How DFlash Does It |
|---------|-------------------|
| **Speculative decoding** | Block-diffusion drafter (DFlash) + tree-structured verification (DDTree). ~8 tokens accepted per step vs ~3 for chain approaches |
| **TurboQuant KV cache** | TQ3_0 (3.5 bpv) is the DEFAULT. Not a flag — it's the built-in KV format. 256K context on 24GB |
| **Speculative prefill (PFlash)** | Qwen3-0.6B BF16 drafter scores token importance, target only prefills important spans. 10x TTFT speedup at 128K |
| **OpenAI-compatible API** | Built in. Supports temperature, top_p, top_k, seed, frequency_penalty. Agent Zero connects via litellm directly |
| **Hybrid architecture support** | Custom CUDA kernels for GatedDeltaNet SSM + attention. Not working around llama.cpp assumptions — replacing them |
| **RTX 3090 optimization** | Reference hardware. DDTree budget=22 swept specifically for sm_86 + Q4_K_M |

## Performance (RTX 3090, Single Card)

### Qwen3.5-27B (fully trained draft — peak performance)

| Benchmark | Autoregressive | DFlash | Speedup |
|-----------|---------------|--------|---------|
| HumanEval | 37.78 tok/s | **129.52 tok/s** | **3.43x** |
| Math500 | 37.71 tok/s | **110.51 tok/s** | **2.93x** |
| GSM8K | 37.65 tok/s | **96.15 tok/s** | **2.55x** |
| Peak demo | 38.0 tok/s | **207.6 tok/s** | **5.46x** |

### Qwen3.6-27B (draft under training — current performance)

| Benchmark | DFlash (3.6 draft) | DFlash (3.5 draft cross-family) |
|-----------|-------------------|--------------------------------|
| HumanEval | ~78 tok/s | ~74 tok/s |
| Joel's RTX 3090 tweet | **83.06 tok/s** | — |
| Expected when draft matures | ~100-120 tok/s | — |

### Compared to everything we've tested

| Config | TPS | Context | Prefill | VRAM |
|--------|-----|---------|---------|------|
| TurboQuant (Madreag) | ~21 | 163K | Cacheable | ~21.5 GB |
| am17an no-MTP | 35.53 | 130K | Re-process/turn | ~18 GB |
| MTP n=3 | 54.28 | 130K | Re-process/turn | 24.27 GB (tight) |
| **DFlash (Qwen3.6)** | **74-83** | **256K** | **PFlash 10x** | **~21-22 GB** |
| **DFlash (Qwen3.5)** | **129.5** | **256K** | **Cacheable** | **~21-22 GB** |

DFlash is faster, has more context headroom, solves the prefill problem, and uses less VRAM than MTP. It wins on every axis.

---

## Build Instructions

### Step 1: Clone and Build

```bash
# Clone with submodules (includes the pinned llama.cpp fork with tree-mode ggml ops)
git clone --recurse-submodules https://github.com/Luce-Org/lucebox-hub
cd lucebox-hub/dflash

# Build for RTX 3090
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --config Release -j
```

**Build notes:**
- CUDA 12+ required. Our 12.8 is fine. CUDA 13+ supported but only required for Jetson
- CMake 3.18+ required
- The `--recurse-submodules` is critical — it pulls the pinned `Luce-Org/llama.cpp@luce-dflash` fork with the three custom tree-mode ggml ops
- If building on Windows with MSVC, use the same vcvars64 approach from the TurboQuant build (`18\BuildTools`)

### Step 2: Download Models

We need the target model (which we already have) and the DFlash draft model.

```bash
# Qwen3.6-27B Q4_K_M target — we already have this
# Located at: D:\LMStudio\Models\...\Qwen3.6-27B-Q4_K_M.gguf
# (or wherever Jake's GGUF is stored)

# Download the Qwen3.6 DFlash draft (still under training, ~78 tok/s)
huggingface-cli download z-lab/Qwen3.6-27B-DFlash --local-dir ./models/dflash-draft-3.6/

# ALSO download the Qwen3.5 DFlash draft (fully trained, ~129 tok/s on 3.5 target)
# Useful as a cross-family fallback — gives ~74 tok/s on 3.6 target
huggingface-cli download z-lab/Qwen3.5-27B-DFlash --local-dir ./models/dflash-draft-3.5/
```

### Step 3: First Run — Benchmark

```bash
# Run the benchmark suite to validate our 3090 matches published numbers
./build/bin/bench_llm \
  --target /path/to/Qwen3.6-27B-Q4_K_M.gguf \
  --draft ./models/dflash-draft-3.6/ \
  --budget 22 \
  --n-tokens 256

# Expected output should show:
# - Decode TPS in the 74-83 range
# - Acceptance length (AL) around 5.0
# - TQ3_0 KV cache allocation in logs
```

Compare with autoregressive baseline:
```bash
# AR baseline (no draft, no speculation)
./build/bin/bench_llm \
  --target /path/to/Qwen3.6-27B-Q4_K_M.gguf \
  --no-spec \
  --n-tokens 256
```

### Step 4: Start the Server

```bash
# Start DFlash with OpenAI-compatible endpoint
./build/bin/dflash_server \
  --target /path/to/Qwen3.6-27B-Q4_K_M.gguf \
  --draft ./models/dflash-draft-3.6/ \
  --budget 22 \
  --host 0.0.0.0 \
  --port 8080

# Check the exact server binary name and flags — may be different
# from bench_llm. Check the README or --help output.
```

**IMPORTANT:** Check the DFlash README for the exact server command. The binary name might be `dflash_server`, `serve`, or integrated into the main binary. The OpenAI endpoint is confirmed to exist — find the exact invocation.

### Step 5: Agent Zero Integration

Point Agent Zero at the DFlash server:
- Update the model configuration to point base URL at `http://localhost:8080`
- litellm should connect the same way it connects to llama-server
- No Agent Zero code changes needed — same OpenAI-compatible API

---

## Test Protocol

### Test 1: Benchmark Validation
Run `bench_llm` with 3.6 target + 3.6 draft. Record:
- Decode TPS
- Acceptance length (AL)
- VRAM peak
- Compare to Joel's 83.06 tok/s

### Test 2: Autoregressive Baseline
Run without speculation. Record AR TPS. Calculate speedup ratio.

### Test 3: Cross-Family Draft
Run 3.6 target with 3.5 draft. Record TPS. Compare to matched draft.
- If 3.5 draft gives >70 tok/s on 3.6 target, it's a viable fallback

### Test 4: PFlash Prefill Test
Test prefill speed at different context lengths:

| Context | Vanilla TTFT | PFlash TTFT | Speedup |
|---------|-------------|-------------|---------|
| 2K | | | |
| 10K | | | |
| 30K | | | |
| 60K | | | |
| 128K | | | expected ~10x |

### Test 5: Agent Zero Integration — Functional
Connect Agent Zero to DFlash server. Run:
- [ ] Merge sort baseline (JSON tool calls work?)
- [ ] Multi-turn conversation (context accumulates correctly?)
- [ ] Tool call + response cycle (formatted correctly?)
- [ ] 5-turn accumulated session (prefill behavior stable?)

### Test 6: Agent Zero Integration — Agentic Workload
Run a real agentic task through the stack:
- A task from the self-improvement program (e.g., wiki page build)
- Measure wall time vs the same task on the TurboQuant/am17an builds
- Check for any quality differences

### Test 7: Power Efficiency
```bash
nvidia-smi -pl 225
# Re-run Test 1
# Record TPS at 225W vs default power
```

At 225W sweet spot, DFlash should still deliver 70+ tok/s with dramatically less power draw. The 3090's efficiency curve flatlines after 250W — most of the performance is available at lower power.

### Test 8: Extended Context Ceiling
```bash
# Test context limits with TQ3_0 KV (should reach 256K per README)
# Start with 128K, increase to 192K, then 256K
# Record: does it fit? VRAM usage? Any quality degradation?
```

---

## Results Table (fill in)

| Metric | DFlash (3.6 draft) | DFlash (3.5 draft) | AR Baseline | TurboQuant (prev) | MTP (prev) |
|--------|-------------------|-------------------|-------------|-------------------|------------|
| Decode TPS | | | | ~21 | 54.28 |
| TTFT at 2K | | | | | |
| TTFT at 30K | | | | | |
| Peak VRAM | | | | ~21.5 GB | 24.27 GB |
| Max context | | | | 163K | 130K |
| AL (acceptance length) | | | N/A | N/A | 69.3% |
| A0 functional | | | | ✅ | Not tested |
| A0 quality | | | | Baseline | Not tested |
| TPS at 225W | | | | | |

---

## What to Keep, What to Retire

### KEEP (still valuable):
- **TurboQuant combined build** (Kestrel's cherry-pick) — engineering reference, the tensor loader diagnosis is valuable if anyone upstream wants to fix MTP for hybrid architectures
- **Power tuning scripts** — `nvidia-smi -pl` applies regardless of inference engine
- **compile.bat / start.bat infrastructure** — adapt for DFlash
- **eval framework** — same test protocols, different binary

### RETIRE (superseded by DFlash):
- **Madreag turbo3-cuda as production backend** — DFlash includes TQ3_0 natively
- **am17an MTP branch** — DFlash's block-diffusion approach is faster and doesn't have the VRAM headroom problem
- **AtomicBot fork** — DFlash subsumes TQ weight optimization investigation
- **The API wrapper plan** — DFlash has an OpenAI endpoint built in

### ARCHIVE (reference value):
- All prior inference builds at `inference/turbo3-cuda/`, `inference/llama-cpp-mtp/`, `inference/llama-cpp-combined/`, `inference/llama-cpp-atomicbot/`
- Move to `inference/archive/` so the directory is clean

---

## Directory Structure After Build

```
D:\Vibecode\Agent-Zero\Exocortex\inference\
├── lucebox-dflash/              # NEW: the production build
│   ├── build/
│   ├── models/
│   │   ├── dflash-draft-3.6/    # z-lab/Qwen3.6-27B-DFlash
│   │   └── dflash-draft-3.5/    # z-lab/Qwen3.5-27B-DFlash (fallback)
│   └── ...
├── compile_dflash.bat           # NEW
├── start_dflash.bat             # NEW
├── eval/
│   ├── DFLASH_BUILD_VALIDATION.md  # NEW: fill in with test results
│   ├── MTP_BUILD_VALIDATION.md     # Archive
│   ├── MTP_TURBOQUANT_COMBINED_VALIDATION.md  # Archive
│   └── TURBOQUANT_BUILD_VALIDATION.md  # Archive
├── archive/                     # Move old builds here
│   ├── turbo3-cuda/
│   ├── llama-cpp-mtp/
│   ├── llama-cpp-combined/
│   └── llama-cpp-atomicbot/
└── ...
```

---

## What Success Looks Like

Jake opens Agent Zero. Types a complex research task. The agent responds with the first token in under a second. Tool calls execute. JSON formats correctly. The agent works at 74-83 tok/s — fast enough that waiting for responses feels natural rather than painful. The idle-time engine runs overnight at 225W, the 3090 barely warm, producing field reports and wiki pages at the same speed because the efficiency sweet spot is the same as the performance sweet spot.

Context accumulates across 40+ turns without the 286-second prefill tax that made Qwen3.6 unviable on llama.cpp. PFlash compresses the prefill to ~28 seconds at 40K context. The agent can sustain multi-hour agentic sessions without degrading.

The VRAM has headroom. Docker runs alongside DFlash without crashes. The 256K context ceiling means the subordinate overflow from ST-013 Test D is history — there's simply enough room.

And when z-lab finishes training the matched Qwen3.6 draft model, the numbers go up further — potentially 100-120 tok/s — with no build changes. Just swap the draft via environment variable and restart.

That's the production inference stack. One binary. Everything included. Built specifically for our hardware and our model family.

---

## One Final Note

Your combined MTP + TurboQuant build was not wasted work. The tensor loader diagnosis — identifying that `qwen35_mtp.cpp` assumes homogeneous attention layers and breaks on hybrid DeltaNet architecture — is a genuine contribution. If you want to file it as an issue or PR comment on the am17an repo, the community would benefit. The 10+ merge conflicts you resolved and the MSVC toolchain fix (`VS2025 18\BuildTools` vcvars) are documented engineering that saves the next person days. Archive the build, keep the notes.

But for production: DFlash is the answer. Build it, test it, point Agent Zero at it.

— Opus
