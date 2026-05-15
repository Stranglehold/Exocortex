# MTP (MULTI-TOKEN PREDICTION) BUILD & TEST — Kestrel Brief
## From: Opus — May 9, 2026
## To: Kestrel
## Context: Potential 2-2.5x throughput upgrade for llama.cpp inference on RTX 3090
## Priority: Evaluate alongside current TurboQuant build — this is a parallel experiment, not a replacement

---

## What MTP Is

Multi-Token Prediction allows the model to draft multiple tokens per forward pass using built-in prediction heads, then verify them in parallel. Unlike traditional speculative decoding (which requires loading a separate small draft model and doubling your VRAM), MTP uses heads embedded in the model's own GGUF — the overhead is roughly one additional transformer layer, not a second network.

When the draft tokens are accepted (model verifies they match what it would have generated), you get 2-3 tokens for the compute cost of ~1. When they're rejected, you fall back to normal generation with minimal overhead.

**Benchmark from the PR author (Qwen3.6 27B, DGX Spark):**

| Config | Wall Time (9 tasks) | Effective TPS | Acceptance Rate |
|--------|-------------------|---------------|-----------------|
| No MTP (baseline) | 201s | 7.0-7.7 | N/A |
| MTP draft-max-n=3 | 83.8s | 15.8-21.6 | 72.2% aggregate |
| MTP draft-max-n=2 | 90.4s | 15.2-18.2 | 82.6% aggregate |

**Code generation hit 90.8% acceptance and 21.6 tok/s — nearly 3x baseline.**

For our 3090 with Club-3090's measured ~21 TPS baseline on llama.cpp: a 2x MTP gain would put us at ~42 TPS. A 2.5x gain would hit ~52 TPS. That approaches vLLM single-card speeds without any of vLLM's VRAM cliff issues.

---

## What You Need

### 1. The MTP-Enabled GGUF

Standard GGUF files don't include MTP heads. You need a GGUF with MTP layers grafted in.

**Recommended source:** `havenoammo/Qwen3.6-27B-MTP-UD-GGUF` on HuggingFace

This repo has pre-built GGUFs with:
- Base quantization: Unsloth Dynamic 2.0 XL
- MTP layers: Grafted from `Radamanthys11/Qwen3.6-27B-MTP-Q8_0-GGUF`, stored in Q8_0 precision
- MTP layers are small relative to the base model, so Q8_0 keeps them near-lossless

Download the Q4_K_XL variant (should be ~17-18GB, fits on 3090 with room for KV cache):
```bash
# Using huggingface-cli:
huggingface-cli download havenoammo/Qwen3.6-27B-MTP-UD-GGUF \
  --include "Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf" \
  --local-dir ./models/

# Or direct browser download from the HuggingFace Files tab
```

**Note:** This is Qwen3.6-27B, not Qwen3.5-27B. Same hybrid DeltaNet architecture, same parameter count. 3.6 is newer with improvements to coding and tool use. If MTP works well, we may want to evaluate 3.6 as the primary model.

### 2. The MTP-Enabled llama.cpp Build

The MTP support comes from PR #22673 by am17an. It's in Draft status but functional and tested.

```bash
# Clone the MTP branch
git clone https://github.com/am17an/llama.cpp.git -b mtp-clean
cd llama.cpp

# Build for RTX 3090 (sm_86)
cmake -B build \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES="86-real"

cmake --build build --config Release -j

# Verify the build produced llama-server with MTP support
./build/bin/llama-server --help | grep -i "spec\|mtp"
```

**Build notes:**
- Same CUDA version rules as the TurboQuant build: use 11.8 or 12.x, avoid 13.x
- The `-DCMAKE_CUDA_ARCHITECTURES="86-real"` flag is identical to the TurboQuant build
- This is a SEPARATE build from the Madreag TurboQuant fork — keep both directories

### 3. Running with MTP

```bash
# Config A: MTP with 3 draft tokens (highest throughput, ~72% acceptance)
./build/bin/llama-server \
  -m ./models/Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  --spec-type mtp --spec-draft-n-max 3 \
  -c 80000 \
  --host 0.0.0.0 --port 8080

# Config B: MTP with 2 draft tokens (higher acceptance rate, ~82%, slightly lower peak TPS)
./build/bin/llama-server \
  -m ./models/Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  --spec-type mtp --spec-draft-n-max 2 \
  -c 80000 \
  --host 0.0.0.0 --port 8080

# Config C: No MTP baseline (for comparison)
./build/bin/llama-server \
  -m ./models/Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf \
  -ngl 99 -fa \
  -c 80000 \
  --host 0.0.0.0 --port 8080
```

**Critical flags:**
- `--spec-type mtp` enables MTP speculative decoding
- `--spec-draft-n-max 3` sets maximum draft tokens per step (3 is the sweet spot per PR benchmarks)
- `-fa` (flash attention) still required
- The MTP model loads from the same GGUF — no separate draft model file needed

---

## Test Protocol

Run all three configs (A, B, C) and record results.

### Test 1: Raw TPS Benchmark
```bash
# For each config, use the same prompt set:
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.6-27b",
    "messages": [{"role": "user", "content": "Write a Python implementation of merge sort with type hints, docstrings, and comprehensive tests."}],
    "max_tokens": 500
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Tokens: {d[\"usage\"][\"completion_tokens\"]}, Time: {d[\"usage\"].get(\"total_time\", \"N/A\")}')"
```

Record for each config:
- Tokens per second (decode)
- Time to first token (TTFT)
- Total wall time
- Acceptance rate (from server logs — look for `spec` or `accept` in log output)

### Test 2: VRAM Usage
```bash
# Monitor during generation
watch -n 1 nvidia-smi
```

Record peak VRAM for each config. MTP adds one extra layer's worth of parameters — expect ~200-500MB overhead vs baseline.

### Test 3: Merge Sort Functional Test
Same task as TurboQuant Test 4:
- Prompt: "Write a Python script that implements merge sort..."
- Compare output quality between MTP and non-MTP
- MTP should produce IDENTICAL output (speculative decoding is mathematically lossless when acceptance is verified)

### Test 4: Agent Zero Integration
Point Agent Zero at the MTP-enabled llama-server (same OpenAI-compatible API, just different port or process):
- Run the merge sort baseline task through A0
- Verify: JSON formatting works, tool calls work, response tool works
- Check for any interaction between MTP and A0's message format

### Test 5: Long Context Stability
```bash
# Use a long prompt (paste a large document or code file)
# Verify MTP still works at longer context lengths
# Acceptance rate may change with context length — document the curve
```

---

## Results Table (fill in)

| Metric | No MTP (Config C) | MTP n=2 (Config B) | MTP n=3 (Config A) |
|--------|-------------------|--------------------|--------------------|
| Decode TPS | | | |
| TTFT (seconds) | | | |
| Wall time (merge sort) | | | |
| Acceptance rate | N/A | | |
| Peak VRAM (GB) | | | |
| Output quality | Baseline | | |
| A0 integration | | | |

---

## How This Relates to TurboQuant

MTP and TurboQuant optimize different bottlenecks:

| Feature | What It Optimizes | Mechanism |
|---------|------------------|-----------|
| **TurboQuant** | Memory bandwidth (KV cache size) | WHT rotation + low-bit quantization of KV cache |
| **MTP** | Compute utilization (tokens per forward pass) | Built-in draft heads predict multiple tokens, verified in parallel |

In principle, they stack. TurboQuant shrinks the KV cache, MTP generates more tokens per pass. Combined: smaller memory footprint AND faster generation.

**However:** The current Madreag TurboQuant fork and the am17an MTP branch are separate forks of llama.cpp. Combining them requires merging the branches. That's a follow-up task — first, test each independently and measure the individual gains.

**Decision matrix after testing:**

| MTP Result | TurboQuant Result | Action |
|-----------|-------------------|--------|
| MTP wins big (>2x) | TurboQuant wins moderate | Prioritize merging both features into one build |
| MTP wins moderate | TurboQuant wins moderate | Both valuable — merge is worth the effort |
| MTP wins big | TurboQuant marginal | Consider MTP-only build as primary |
| MTP marginal on 3090 | TurboQuant wins | Stay on Madreag TurboQuant build |

---

## Important Notes

1. **This is Qwen3.6, not Qwen3.5.** The models are architecturally identical (same hybrid DeltaNet + attention) but 3.6 has improved coding and tool use performance. If MTP works well and 3.6 performs at least as well as 3.5 on our agentic workloads, we may upgrade the primary model.

2. **MTP is lossless.** Speculative decoding with verification produces mathematically identical output to standard autoregressive generation. The draft tokens are only accepted if they match what the model would have generated. There should be ZERO quality difference — only speed difference.

3. **The PR is still Draft.** This means the API may change before merge. The core functionality works (tested by the PR author on Qwen3.6 27B and 35B-A3B), but edge cases may exist. If you hit build errors or runtime issues, check the PR discussion for known issues.

4. **Acceptance rate varies by task type.** The PR benchmarks show 90.8% acceptance on Python code but only 54.2% on translation. Code generation and structured output (JSON, tool calls) tend to have higher acceptance because the token sequences are more predictable. This is good for us — Agent Zero's primary output is structured JSON with tool calls.

5. **Keep the Madreag TurboQuant build intact.** This MTP test is a parallel experiment. Don't replace the working TurboQuant build — build MTP in a separate directory and test independently.

---

## File Locations

```
D:\Vibecode\Agent-Zero\inference\
├── turbo3-cuda/              # Existing Madreag TurboQuant build
│   ├── build/
│   └── ...
├── llama-cpp-mtp/            # NEW: am17an MTP build
│   ├── build/
│   └── ...
├── models/
│   ├── Qwen3.5-27B-Q4_K_M.gguf          # Current model
│   └── Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf  # NEW: MTP-enabled model
├── compile.bat               # Existing TurboQuant compile script
├── compile_mtp.bat           # NEW: MTP compile script (create this)
├── start.bat                 # Existing TurboQuant start script
├── start_mtp.bat             # NEW: MTP start script (create this)
└── eval/
    ├── TURBOQUANT_BUILD_VALIDATION.md    # Existing
    └── MTP_BUILD_VALIDATION.md           # NEW: MTP test results
```

---

## What Success Looks Like

If MTP delivers even a 1.5x throughput gain on the 3090 with acceptable VRAM overhead:
- Interactive sessions feel noticeably snappier
- Idle-time engine completes more work per cycle (same step budget, faster steps)
- Agent Zero's response latency drops from ~3-4 seconds to ~1.5-2 seconds per response
- The system moves from "functional but a bit slow" to "genuinely responsive"

If MTP delivers 2x+, it fundamentally changes the economics: the 3090 becomes competitive with cloud API speeds for interactive use, making the sovereign local inference setup viable as a primary development environment rather than just an overnight research tool.

Write results to `eval/MTP_BUILD_VALIDATION.md` and to `team-comms/kestrel-to-opus/` when done. Don't switch the production inference backend until Jake approves the numbers.

— Opus
