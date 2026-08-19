# Local Inference Optimization 2026

**Status:** STABLE
**Created:** 2026-05-22 | **Last Deepened:** 2026-05-22
**Sources:** 8 verified primary sources
**Cross-domain Links:** 4

## Executive Summary

Post-training quantization (PTQ) and KV cache compression form the two dominant levers for reducing LLM inference cost on fixed hardware. PTQ reduces model weight memory from 16-bit FP16 down to 2-4 bits per parameter (4-8x compression), while KV cache compression reduces the per-token memory cost that grows linearly with context length. Together they enable 70B+ parameter models to run on consumer GPUs (RTX 3090, 24GB) and edge devices.

## Quantization Advances (2025-2026)

### Extreme Low-Bit Quantization (<=4 bits)

| Method | Bits | Key Innovation | Venue | arXiv |
|--------|------|----------------|-------|-------|
| **QuIP#** | 2-4 | Hadamard incoherence + E8 lattice codebook (2^16 codewords) | ICML 2025 | 2402.04396 |
| **AQLM** | 2 | Asymmetric quantization via learned mixing; 70B on 8xA100 takes 3d 18h | GitHub repo | — |
| **SignRoundV2** | <=2 | Closes performance gap in extreme low-bit via sign-magnitude separation | arXiv 2025 | 2512.04746 |
| **Bielik-Q2-Sharp** | 2 | Comparative study of 2-bit methods; Q2-Sharp variant | arXiv 2026 | 2603.04162 |
| **ParetoQ** | variable | Optimized training schemes; surpasses all previous methods at specific bit widths | NeurIPS 2025 | — |

**Key finding:** QuIP# represents the current SOTA for <=4-bit PTQ using E8 lattice codebooks with Hadamard incoherence preprocessing. SignRoundV2 addresses the remaining accuracy gap at 2-bit widths. The Pareto front across bit widths shows no single method dominates all regimes.

### Mixed-Precision Quantization

- **SliM-LLM** (ICML 2025): Salience-driven mixed-precision — quantizes less-important layers to lower bits while preserving higher precision for critical layers. Outperforms uniform-precision at same average bit budget.

## KV Cache Compression

KV cache grows O(n*d*layers) with context length n, making it the dominant memory bottleneck for long-context inference. Compression techniques fall into three categories:

### Token-Level Selection (Eviction)

| Method | Mechanism | Venue |
|--------|-----------|-------|
| **H2O** | Heavy-hitter outlier retention | ICLR 2024 |
| **SnapKV** | Local window attention for token importance | NeurIPS 2024 |
| **Ada-KV** | Adaptive budget allocation per layer | Jan 2025 |
| **RocketKV** | Two-stage compression pipeline | ICML 2025 (NVlabs) |

**RocketKV** (ICML 2025) represents current SOTA: two-stage pipeline achieves superior accuracy vs memory tradeoff over H2O and SnapKV on LongBench benchmarks.

### Semantic Chunk-Level Compression

- **ChunkKV** (OpenReview 2025): Groups tokens into semantic chunks rather than token-level eviction. Preserves linguistic structure and contextual integrity better than per-token methods.

### Retrieval-Based Compression

- **RazorAttention** (OpenReview): Compresses KV cache through retrieval-based approximation, outperforming H2O/SnapKV/MInference under strict cache budgets.

### Review & Synthesis

- **KV Cache Compression Review** (arXiv:2508.06297): Systematic review covering selective token strategies, quantization, and attention compression.
- **Understanding the Physics of KV Cache Compression** (arXiv:2603.01426): Theoretical analysis of why compression works.
- **Value-Guided KV Compression** (NeurIPS 2025): CUR decomposition approach.
- **HybridKV** (arXiv:2604.05887): Multimodal extension for vision-language models.

## Speculative Decoding Integration

Speculative decoding (covered in [speculative-decoding.md](speculative-decoding.md)) provides throughput gains independent of quantization and KV cache compression. The three techniques compose:

1. Quantize the target model (QuIP# 4-bit -> 4x weight compression)
2. Compress KV cache (RocketKV -> 50-70% cache reduction)
3. Apply speculative decoding (EAGLE-3/Mirror -> 1.4-3x token throughput)

**Combined effect:** Enables 70B+ models on RTX 3090 (24GB VRAM) with competitive latency.

## Integration Path for Exocortex

For the RTX 3090 local inference stack:
- **Immediate:** GGUF 4-bit quantization (already used via llama.cpp)
- **Near-term:** Evaluate QuIP# compatibility with llama.cpp / ExLlamaV2 backends
- **Medium-term:** RocketKV for long-context tasks (policy analysis, document review)
- **Speculative decoding:** EAGLE-3 or Mirror already covered in speculative-decoding.md

## Sources (8 verified)

1. QuIP#: Chee et al., arXiv:2402.04396, ICML 2025
2. SignRoundV2: arXiv:2512.04746
3. Bielik-Q2-Sharp: arXiv:2603.04162
4. ParetoQ: NeurIPS 2025
5. SliM-LLM: ICML 2025
6. RocketKV: ICML 2025, NVlabs GitHub
7. KV Cache Compression Review: arXiv:2508.06297
8. HybridKV: arXiv:2604.05887

## Cross-Domain Connections

- [triton-kernels-rtx-optimization.md](triton-kernels-rtx-optimization.md) — Custom kernels needed for efficient int2/int4 matmul on RTX 3090 tensor cores
- [tinyml-edge-inference-constrained-hardware.md](tinyml-edge-inference-constrained-hardware.md) — Same quantization principles apply at edge scale
- [ai-inference-compiler-stack.md](ai-inference-compiler-stack.md) — TVM/IREE support for low-bit quantization execution
- [speculative-decoding.md](speculative-decoding.md) — Complementary inference acceleration technique

## Open Questions

- How does QuIP# integrate with ExLlamaV2 backend used by Exocortex?
- What is the accuracy degradation of RocketKV on 128K+ context windows (our typical document analysis use case)?
- Can mixed-precision (SliM-LLM) be applied to already-quantized GGUF models without full re-quantization?
