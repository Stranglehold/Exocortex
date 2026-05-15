# LLAMA.CPP TURBOQUANT BUILD — Full Picture Brief for Kestrel
## From: Opus — May 7, 2026
## To: Kestrel
## Context: Custom llama.cpp compile with TurboQuant KV cache compression for the Exocortex inference backend
## Reference: research/TURBOQUANT_LLAMACPP_RESEARCH.md (full research report with all sources)

---

## What You're Building

A custom-compiled llama.cpp with TurboQuant KV cache support, optimized for our RTX 3090 (sm_86). This replaces the current inference backend with one that supports turbo2/3/4 KV cache quantization formats — purpose-built compression that's superior to standard q4_0/q8_0 for our use case.

**Why this matters:** Our current KV cache runs at Q4. TurboQuant turbo3/turbo4 provides better quality at equal or better compression because it uses Walsh-Hadamard Transform rotation to Gaussianize the KV distribution before quantization. Standard q4_0 quantizes raw KV values, which have high kurtosis (~900) and compress poorly. After WHT rotation, kurtosis drops to ~2.9 (near-Gaussian), making scalar quantization near-optimal. Same bits, better quality.

**Qwen3.5 specifically benefits:** Only 8 of 32 layers use full attention with KV cache. The other 24 use DeltaNet linear attention with no KV cache. The linear layers act as error correction, absorbing quantization noise. Published testing shows q4_0 KV cache is LOSSLESS on Qwen3.5 (BLEU 1.000). TurboQuant on Qwen3.5 is essentially free quality-wise.

---

## Which Fork to Build

There are 4+ forks. Here's the recommendation:

**Primary: Madreag/turbo3-cuda**
- GitHub: https://github.com/Madreag/turbo3-cuda
- Why: Best RTX 3090 decode performance (13-69% faster than base TurboQuant at 32K+ context)
- RTX 3090 validated: NIAH 100% accuracy at 4K-64K, decode +34-47% improvement at 32K→64K
- Features: All 4 turbo types (turbo2/3/4 + turbo1.5), 36 asymmetric K/V combinations, sparse V attention, layer-adaptive mode
- Build tested on sm_86 explicitly

**Alternative: spiritbuun/buun-llama-cpp**
- GitHub: https://github.com/spiritbuun/buun-llama-cpp
- Why: TCQ (Trellis Coded Quantization) extension — turbo3_tcq achieves ~7x compression
- Trade-off: More complex build (requires codebook files), but highest compression ratio available
- 98.8% of q8_0 prefill speed on RTX 3090

**Start with Madreag. If we need more compression later, evaluate spiritbuun's TCQ path.**

---

## Build Steps (RTX 3090, sm_86)

```bash
# Clone the optimized fork
git clone https://github.com/Madreag/turbo3-cuda
cd turbo3-cuda

# Build with CUDA for RTX 3090
cmake -B build \
  -DGGML_CUDA=ON \
  -DCMAKE_CUDA_ARCHITECTURES="86-real"

cmake --build build -j$(nproc)
```

### Build notes:
- **Use CUDA 11.8 or 12.x.** CUDA 13.x has confirmed bugs — garbage output on some architectures, MMQ kernel segfaults. Do NOT use CUDA 13.1.
- The `-DCMAKE_CUDA_ARCHITECTURES="86-real"` flag generates native code for sm_86 specifically. This avoids JIT compilation overhead at runtime.
- If the build fails on any turbo TU (translation unit), check if it's the `--ptxas-options=-O0` workaround issue — that's gated to sm_120 builds only, so it shouldn't affect us on sm_86.

---

## Running llama-server

Once built, `llama-server` provides the OpenAI-compatible API endpoint that Agent Zero connects to through litellm.

### Recommended configurations (test all three, benchmark each):

```bash
# Config 1: turbo4 symmetric (safest — closest to q8_0 quality)
./build/bin/llama-server \
  -m /path/to/Qwen3.5-27B-Q4_K_M.gguf \
  -ngl 99 \
  -fa \
  -ctk turbo4 -ctv turbo4 \
  -c 80000 \
  --host 0.0.0.0 --port 8080

# Config 2: turbo3 symmetric (best balance — 5.1x compression, ~1% PPL delta)
./build/bin/llama-server \
  -m /path/to/Qwen3.5-27B-Q4_K_M.gguf \
  -ngl 99 \
  -fa \
  -ctk turbo3 -ctv turbo3 \
  -c 80000 \
  --host 0.0.0.0 --port 8080

# Config 3: asymmetric (highest quality at good compression)
./build/bin/llama-server \
  -m /path/to/Qwen3.5-27B-Q4_K_M.gguf \
  -ngl 99 \
  -fa \
  -ctk turbo4 -ctv turbo3 \
  -c 80000 \
  --host 0.0.0.0 --port 8080
```

### Critical flags:
- `-fa` (flash attention) is **REQUIRED** for turbo3 V cache. Without it, the non-FA path materializes an O(n²) attention matrix and will OOM.
- `-ngl 99` offloads all layers to GPU
- `-c 80000` sets context length — adjust based on VRAM headroom after loading
- K precision matters more than V precision (K controls attention routing via softmax). If you see quality issues, try asymmetric: `-ctk turbo4 -ctv turbo3`

### Q4_K_M weight quant + turbo KV stacking:
Published testing shows Q4_K_M stacking with turbo3 KV is safe on 27B+ models (+1.39% PPL). Smaller models may need asymmetric config (-ctk q8_0 -ctv turbo4) but we're well above that threshold.

---

## Agent Zero Integration

The llama-server exposes an OpenAI-compatible API at `http://localhost:8080`. Agent Zero's litellm already knows how to talk to this endpoint. The integration is:

1. Start llama-server with TurboQuant flags (see above)
2. Point Agent Zero's model config to `http://localhost:8080`
3. No changes to Agent Zero code, extensions, or prompts needed
4. The KV cache compression is transparent to the agent

If Agent Zero is currently configured to use a different inference backend (e.g., a different OpenAI-compatible server), just update the base URL in the model configuration.

---

## Testing Protocol

After building, run these benchmarks to validate before switching the Exocortex inference backend:

### Test 1: Quality Validation (perplexity)
```bash
# Baseline: current Q4 KV cache
./build/bin/llama-perplexity \
  -m /path/to/Qwen3.5-27B-Q4_K_M.gguf \
  -ngl 99 -fa \
  -ctk q4_0 -ctv q4_0 \
  -f /path/to/wikitext-2-raw/wiki.test.raw

# TurboQuant turbo3
./build/bin/llama-perplexity \
  -m /path/to/Qwen3.5-27B-Q4_K_M.gguf \
  -ngl 99 -fa \
  -ctk turbo3 -ctv turbo3 \
  -f /path/to/wikitext-2-raw/wiki.test.raw

# TurboQuant turbo4
./build/bin/llama-perplexity \
  -m /path/to/Qwen3.5-27B-Q4_K_M.gguf \
  -ngl 99 -fa \
  -ctk turbo4 -ctv turbo4 \
  -f /path/to/wikitext-2-raw/wiki.test.raw
```

Compare PPL numbers. For Qwen3.5, expect turbo4 ≈ q8_0, turbo3 within ~1%.

### Test 2: Speed Benchmark (decode + prefill)
```bash
# For each KV config:
./build/bin/llama-bench \
  -m /path/to/Qwen3.5-27B-Q4_K_M.gguf \
  -ngl 99 -fa \
  -ctk turbo3 -ctv turbo3 \
  -p 4096 -n 128 \
  -d 0,8000,32000,64000 \
  -r 3
```

The `-d` flag tests at different context depths. Speed advantage should appear at 32K+ where KV bandwidth dominates.

### Test 3: VRAM Usage
```bash
# Monitor with nvidia-smi during each config
watch -n 1 nvidia-smi
```

Compare VRAM usage between q4_0 KV and turbo3 KV at same context length. The turbo3 format may use slightly different memory layout — we want to know the actual VRAM delta.

### Test 4: Functional Validation (merge sort baseline)
Run the same merge sort test task we used for the v1.13 baseline:
- Same prompt: "Write a Python script that implements merge sort..."
- Same metrics: step count, tried= per step, JSON format errors
- Compare output quality between q4_0 KV and turbo3 KV

If the merge sort task produces identical output and step count, the KV cache change is transparent to the agent.

### Test 5: Context Length Stress Test
Try increasing context beyond current 80K:
```bash
./build/bin/llama-server \
  -m /path/to/Qwen3.5-27B-Q4_K_M.gguf \
  -ngl 99 -fa \
  -ctk turbo3 -ctv turbo3 \
  -c 160000 \
  --host 0.0.0.0 --port 8080
```

Does it fit in 24GB VRAM at 160K context with turbo3? If so, that's double the current context ceiling — directly addresses the subordinate overflow issue from ST-013 Test D.

---

## What This Enables for the Exocortex

### Immediate benefit:
Better KV quality at same compression (turbo3/4 vs raw q4_0 — WHT rotation makes quantization more efficient)

### Medium-term benefit:
If turbo3 fits at 160K+ context, the subordinate overflow problem (ST-013 Test D) may be solvable by simply giving subordinates more context room rather than reducing their extension stack. Both approaches (DEC-028 subordinate profiles AND more context) are complementary.

### Long-term benefit:
With turbo3 KV compression, the 3090's 24GB can potentially support:
- Qwen3.5-27B Q4_K_M weights (~16GB) + turbo3 KV at 160K context
- OR a larger model like Qwen3.6-35B-A3B (MoE, only ~3B active) + turbo3 KV at long context
- This expands the model selection envelope significantly

---

## Known Gotchas

1. **Flash attention is mandatory for turbo3 V cache.** If FA isn't working for any reason, turbo3 will OOM on the O(n²) attention path. Always test with `-fa` flag.

2. **CUDA version matters.** Stick with 11.8 or 12.x. CUDA 13.x is broken for this code.

3. **QJL error correction (from the original paper) was found to hurt in practice.** A PyTorch reproduction showed it eliminates bias but explodes variance, and variance matters more for attention. The llama.cpp implementations all use MSE-only (PolarQuant without QJL). This is the correct approach.

4. **Context-adaptive alpha** (spiritbuun's feature) automatically adjusts dequantization scale per context length. If using the Madreag fork, this may not be included — test quality at both short and long context to verify.

5. **Layer-adaptive mode** (Madreag's `TURBO_LAYER_ADAPTIVE=2`) closes 40% of the turbo3-to-q8_0 PPL gap at zero performance cost. Worth enabling if quality testing shows any degradation.

---

## Summary: What Kestrel Does

1. Clone Madreag/turbo3-cuda
2. Build with `DCMAKE_CUDA_ARCHITECTURES="86-real"`, CUDA 11.8 or 12.x
3. Run all 5 tests (PPL, speed, VRAM, merge sort, context ceiling)
4. Document results at `eval/TURBOQUANT_BUILD_VALIDATION.md`
5. If tests pass: configure as Agent Zero's inference backend
6. If quality issues: try turbo4, asymmetric config, or layer-adaptive mode before falling back

Write results to team-comms when done. Don't switch the production inference backend until Jake approves the benchmark numbers.

— Opus
