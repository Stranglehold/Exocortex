# TurboQuant for llama.cpp — Research Findings
## Date: May 7, 2026
## Context: Evaluating TurboQuant KV cache compression for Exocortex inference stack

---

## Executive Summary

TurboQuant (Zandieh et al., ICLR 2026) has been independently implemented for llama.cpp CUDA by multiple contributors. RTX 3090 (sm_86) testing is already done. The results are directly applicable to our stack.

**Bottom line for our 3090 + Qwen3.5-27B setup:**
- turbo3 KV cache: 4.6-5.1x compression vs FP16, decode within 4-7% of q8_0
- turbo4 KV cache: 3.8x compression, quality closer to q8_0 than q4_0
- Qwen3.5 specifically: q4_0 KV cache is already LOSSLESS (BLEU 1.000) because only 8 of 32 layers use full attention — the 24 DeltaNet linear attention layers act as error correction
- Practical impact: 80K context at FP16 KV → potentially 320K+ at turbo3, or much more VRAM headroom for model weights + longer context simultaneously

---

## Available Implementations (tested, working)

### 1. TheTom/llama-cpp-turboquant (consolidated fork)
- **GitHub:** https://github.com/TheTom/llama-cpp-turboquant
- **Branch:** feature/turboquant-kv-cache
- **What's integrated:** All CUDA work (via signalnine's PR), block_size=128 optimization (turbo3: 4.57x → 5.12x compression), HIP/ROCm support, InnerQ, turbo4 prefill optimizations
- **Community:** 30+ testers across RTX 3080Ti/3090/4090/5090, AMD GPUs, Apple Silicon
- **RTX 3090 results (Qwen3.5-9B Q4_K_M):** CUDA decode within 4-7% of q8_0 across all configs. Prefill within 4-7%.

### 2. spiritbuun/buun-llama-cpp (CUDA optimized)
- **GitHub:** https://github.com/spiritbuun/buun-llama-cpp
- **Specialty:** TCQ (Trellis Coded Quantization) extension — turbo3_tcq achieves ~7x compression
- **Extra features:** Context-adaptive alpha (auto-adjusts dequant scale per context length), codebook training scripts
- **Note:** 98.8% of q8_0 prefill speed on RTX 3090 using dequant-then-MMA path

### 3. Madreag/turbo3-cuda (optimized decode kernels)
- **GitHub:** https://github.com/Madreag/turbo3-cuda
- **Specialty:** Aggressive CUDA kernel optimizations — 13-69% faster turbo decode at 32K+ context vs base implementation
- **RTX 3090 specific:** 32K → 64K context shows +34-47% speed improvement
- **NIAH testing:** q8_0/turbo3 = 100% accuracy on 3090 at 4K-64K context
- **Build for 3090:** `cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"`

### 4. craftogrammer/llama.cpp-adaptive-turboquant (auto-selecting)
- **GitHub:** https://github.com/craftogrammer/llama.cpp-adaptive-turboquant
- **Specialty:** Auto-selects optimal KV layout based on context length
- **3090 build verified:** Explicit sm_86 build instructions in README
- **Layer-adaptive mode:** Protects first4+last4 layers with q8_0-V, recovers 37-91% of turbo2-to-turbo3 quality gap

---

## Key Technical Findings

### QJL Error Correction: HURTS Performance in Practice
A PyTorch reproduction found that QJL (the error correction component from the original paper) actually degrades quality:
- QJL eliminates bias but explodes variance
- For attention, variance is worse than bias
- MSE-only consistently wins on Top-1 token matching
- The gap is huge at low bits, still noticeable at 8-bit
- **Implication:** Our MLX TurboQuant implementation used PolarQuant + QJL. Consider dropping QJL.

### Qwen3.5 Hybrid Architecture: KV Cache Quant Is Nearly Free
Per-head adaptive quantization research (Issue #21385) found:
- Qwen3.5 uses only 8 of 32 layers for full attention with KV cache
- The other 24 layers use DeltaNet linear attention with NO KV cache
- The linear/sliding attention layers act as error correction
- Result: q4_0 KV cache is LOSSLESS on Qwen3.5 (BLEU 1.000 across 10 test configs)
- **This is our model family.** KV cache quantization is essentially free for us.

### Compression Ratios Available

| Type | Bits/Value | Compression vs FP16 | Quality Impact |
|------|-----------|---------------------|----------------|
| turbo4 | 4-bit | 3.8x | Closest to q8_0, better than q4_0 |
| turbo3 | 3-bit | 4.6-5.1x | ~1% PPL increase vs q8_0 |
| turbo3_tcq | 3-bit TCQ | ~7x | Trellis coded, higher quality at same bits |
| turbo2 | 2-bit | 6.4x | Best used asymmetrically (K=turbo3, V=turbo2) |

### Asymmetric K/V: K Precision Matters More
- K controls attention routing via softmax — more sensitive to quantization
- V only affects the weighted sum — more tolerant
- Recommended asymmetric config: `-ctk turbo4 -ctv turbo3`
- Or for maximum compression: `-ctk turbo3 -ctv turbo2`

### Performance on RTX 3090 (sm_86)

| Metric | q8_0 | turbo4 | turbo3 | Notes |
|--------|------|--------|--------|-------|
| Decode (short ctx) | Baseline | ~Same | ~Same | Weight-loading bound |
| Decode (32K+) | Baseline | +46-68% faster* | Within 4-7% | *With Madreag's optimized kernels |
| Prefill | Baseline | Within 4-7% | Within 4-7% | spiritbuun's dequant-then-MMA path |
| NIAH accuracy | 100% | 100% | 100% | At 4K-64K context |

*The speed advantage at long context is because smaller KV cache = less memory bandwidth consumed per token

---

## Build Instructions for RTX 3090

### Recommended: Madreag's optimized fork (best 3090 decode performance)
```bash
git clone https://github.com/Madreag/turbo3-cuda
cd turbo3-cuda
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build -j$(nproc)

# Run with turbo3 KV cache (best balance: quality ≈ q8_0, 5.1x compression)
./build/bin/llama-server -m your-model.gguf -ngl 99 -fa \
  -ctk turbo3 -ctv turbo3

# Run with asymmetric (highest quality at good compression)
./build/bin/llama-server -m your-model.gguf -ngl 99 -fa \
  -ctk turbo4 -ctv turbo3

# Run with turbo4 (safest, closest to q8_0 quality)
./build/bin/llama-server -m your-model.gguf -ngl 99 -fa \
  -ctk turbo4 -ctv turbo4
```

### Alternative: spiritbuun's fork (TCQ support, highest compression)
```bash
git clone https://github.com/spiritbuun/buun-llama-cpp
cd buun-llama-cpp
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86"
cmake --build build -j$(nproc)

# turbo3_tcq (~7x compression)
./build/bin/llama-server -m your-model.gguf -ngl 99 -fa \
  -ctk turbo3_tcq -ctv turbo3_tcq
```

### Important build notes:
- Use CUDA 11.8 or 12.x — CUDA 13.x has confirmed bugs (garbage output on some arches, MMQ segfaults)
- `-fa` flag (flash attention) is REQUIRED for turbo3 V cache — without it, the non-FA path materializes O(n²) attention matrix
- The block_size=128 warp-to-block mapping fix (commit 7cb6edb) has been validated PPL-identical on sm_86

---

## Impact on Exocortex

### Current state: 80K context with FP16 KV cache on 24GB 3090
### With turbo3: Same VRAM budget supports ~400K+ context, OR:
- Run the same 80K context with significantly more VRAM headroom
- Potentially fit a larger model (35B-A3B MoE?) alongside turbo3 KV
- Enable longer autonomous runs before context overflow (directly addresses ST-013 Test D subordinate overflow)

### With turbo4 (safer): ~300K context ceiling, quality indistinguishable from q8_0

### Recommended path:
1. Clone Madreag's fork (best 3090 performance data)
2. Build with sm_86
3. Test with Qwen3.5-27B on the merge sort + OpenPlanter benchmark tasks
4. Compare: same context, same task, turbo3 vs current FP16 KV
5. If quality holds: switch Agent Zero's inference backend to this build
6. If quality degrades: try turbo4 (safer) or asymmetric -ctk turbo4 -ctv turbo3

---

## Sources

| Source | URL |
|--------|-----|
| llama.cpp Discussion #20969 (152 comments) | https://github.com/ggml-org/llama.cpp/discussions/20969 |
| TheTom/turboquant_plus (consolidated docs) | https://github.com/TheTom/turboquant_plus |
| spiritbuun/buun-llama-cpp (TCQ CUDA) | https://github.com/spiritbuun/buun-llama-cpp |
| Madreag/turbo3-cuda (optimized kernels) | https://github.com/Madreag/turbo3-cuda |
| craftogrammer adaptive fork (auto-select) | https://github.com/craftogrammer/llama.cpp-adaptive-turboquant |
| Oliver Church writeup (dual 3090 validation) | https://oliverchurch.com/turboquant-for-ggml-achieving-4.57x-kv-cache-compression-in-llama.cpp.html |
| Per-head adaptive quant (Qwen3.5 lossless) | https://github.com/ggml-org/llama.cpp/issues/21385 |
| HIP/ROCm port | https://github.com/ggml-org/llama.cpp/discussions/21526 |
| TurboQuant paper (ICLR 2026) | https://arxiv.org/abs/2504.19874 |
