# RTX 3090 CUDA Optimization: Tensor Core Utilization & Custom Kernels

**Status:** STABLE
**Created:** 2026-07-14
**Last Updated:** 2026-08-12

## Overview

Optimization of NVIDIA RTX 3090 (GA102, 24 GB VRAM, 82 SMs, 10,496 CUDA cores, 3rd-gen Tensor Cores, 768 GB/s GDDR6X bandwidth) for LLM inference and GPU compute beyond standard cuBLAS/cuDNN abstractions. Focus on maximizing tensor core utilization, memory bandwidth efficiency, and inference throughput on consumer hardware at $500-600 used market cost (2026).

## Architecture Baseline

| Parameter | Value |
|-----------|-------|
| GPU | GA102 (Ampere, SM86) |
| CUDA Cores | 10,496 (128/SM × 82 SMs) |
| Tensor Cores | 328 (4/SM, 3rd-gen) |
| VRAM | 24 GB GDDR6X |
| Memory Bandwidth | 768 GB/s (effective ~936 GB/s measured via Luce-Megakernel benchmarks) |
| L1/Shared Memory | 128 KB/SM |
| L2 Cache | 6 MB |
| Register File | 256 KB/SM (65,536 registers total) |
| Peak FP16 TFLOPS | 142 TFLOPS (sparse) |
| FP8 Support | None — requires Ada/Hopper architecture |
| NVLink | Not available (GA102 consumer variant) |
| Interconnect | PCIe Gen 4 ×16 |

## Key Optimization Techniques

### 1. Megakernel Fusion

Single CUDA kernel launch for all transformer layers, eliminating ~100 kernel launches per token. Activations remain in shared memory/L2 between layers rather than round-tripping through global memory. Implemented via CudaForge, AutoKernel, and FlashInfer. Critical to keeping the 6 MB L2 cache from thrashing under large weight tensors.

### 2. Tensor Core Tiling

- **S_TILE=8** pattern avoids register spilling on the 65,536-register budget per SM
- MMA instructions (`mma.sync.aligned.m16n8k16`) for BF16 compute with FP32 accumulation
- WMMA for portable tensor core programming across architectures
- Balance MMA tile size against register pressure — spilling to local memory kills throughput

### 3. Power-Optimized Inference

- Stock power: 350 W typical
- **Undervolted to 220 W** with megakernel fusion achieves **1.87 tok/J** — a **2.46×** efficiency gain over stock
- <5% throughput loss at 220W vs stock — the RTX 3090 operates efficiently below its rated TDP
- Critical for sustained inference workloads where thermal throttling would otherwise degrade performance

### 4. FlashAttention-3 on Ampere

FlashAttention-3 confirmed to support Ampere (RTX 3000 series) as of mid-2026. FA3 achieves 75% GPU utilization on H100 (vs. 35% for FA2), and while Ampere won't match those numbers, the IO-aware tiling improvements translate directly: the RTX 3090's 6 MB L2 cache bottleneck benefits from FA3's reduced global memory traffic.

**Pragmatic approach:** Load prebuilt FA3 wheels, benchmark against custom megakernel attention, and use whichever wins for the target model size. FA3 partially supersedes hand-coded Triton/CUDA attention kernels.

### 5. MoE Architecture Sweet Spot

Qwen3.5-35B-A3B achieves 112 tok/s on a single RTX 3090 at full 262K context (CodePulse, July 2026). The general principle: **MoE with a high expert-to-active ratio (>10:1) is the optimal architecture for consumer GPUs with large VRAM but limited compute.** The RTX 3090 has sufficient VRAM to hold all experts while the compute budget only needs to cover active experts. This has direct implications for cascade routing in local-to-frontier bridging architectures — bias toward MoE local models over dense ones on RTX 3090 hardware.

### 6. FP8-as-Storage (Ampere Inference)

Mohan's CUDA FP8 emulation framework (June 2026) enables FP8 weight storage on Ampere, using IMMA instructions for matmul with LUT-based decode. Key points:
- Inference only — no backward pass, no stochastic rounding
- ~2x VRAM savings: fit ~13-14B models in 24 GB with FP8 weights + INT8 activations
- Not performance-competitive with native FP8 hardware (Ada/Hopper), but enables larger models on Ampere
- Practical value: cascade routing benefits from larger local models = fewer frontier API calls

### 7. CuTile vs Triton Cross-Architecture (2026)

Independent evaluation (arXiv:2604.23466, June 2026) on H100 NVL, B200, and RTX PRO 6000:
- **CuTile** achieves up to 1007 TFLOP/s fused attention on B200 (2.5× FlashAttention-2) in 60 lines of Python
- However, same CuTile attention kernel gets only **53% of FA2 throughput on RTX PRO 6000** — significant cross-architecture gaps
- **Triton** sustains 62-101% of cuBLAS across all platforms without architecture-specific tuning — substantially stronger portability
- Implication: CuTile is a replacement for hand-written CUDA kernels but not yet for vendor-optimized libraries; Triton remains the pragmatic choice for consumer GPU optimization

## Inference Stack Performance

| Framework | Tok/sec (Qwen3.6-27B Q4_K_M) | Notes |
|-----------|------------------------------|-------|
| llama.cpp | 25-35 | CPU offload fallback, pure GPU |
| vLLM + AWQ | 45-60 | PagedAttention, INT4 quantization |
| FlashInfer | 50-70 | Megakernel fusion path |
| TensorRT-LLM | 60-80 | NVIDIA-optimized, FP16/BF16 |

## Tools & Libraries

| Tool | Purpose |
|------|---------|
| TensorRT-LLM | NVIDIA-optimized inference with FlashAttention and masked MHA kernels; now available on Windows (beta) for GeForce RTX GPUs |
| Triton | Portable custom kernel development; 62-101% of cuBLAS without architecture-specific tuning |
| FlashInfer | Megakernel-fused attention kernels |
| CudaForge | Automated kernel generation and tuning |
| AutoKernel | Iterative optimization pipeline for custom ops |
| vLLM | PagedAttention-based serving framework |
| llama.cpp | Lightweight pure-CUDA inference with GGUF quantization |
| RIS-Kernel | Model-agnostic sparse attention (O(N log N) from O(N^2)) for long-context on commodity hardware |

## 2026 Research Frontiers

- **Cross-architecture portability gap:** CuTile's 2.5× advantage on B200 collapses to 53% underperformance on consumer RTX hardware. The tooling isn't ready for heterogeneous GPU fleets.
- **Sparse attention as regularizer:** RIS-Kernel at 1% density with ensemble seeds outperforms dense attention (75% vs 71.88% accuracy) — sparse patterns filter sequence-level noise.
- **FP8 quantization ecosystem:** While Ampere lacks native FP8 support, FP8-as-storage bridges the gap for model loading. Checkpoint compatibility with HuggingFace FP8 models avoids conversion costs.
- **Autonomous kernel optimization:** AutoKernel and AutoRestTest demonstrate reinforcement learning + LLM-guided exploration for kernel search — potential for closed-loop kernel discovery on RTX 3090.

## Cross-Domain Connections

- [[bridging-local-to-frontier-model-performance]] — Cascade routing architecture; MoE local model preference on RTX 3090
- [[triton-kernels-rtx-optimization]] — Custom Triton operators for Ampere tensor cores
- [[power-efficient-local-llm-inference-benchmarks]] — Undervolting and power optimization benchmarks
- [[hardware-software-codesign-ai-agents]] — Hardware-aware agent design
- [[quantization-advances-llm-inference]] — INT4/FP8 quantization for consumer GPUs
- [[speculative-decoding]] — Complementary inference acceleration
- [[local-model-inference-optimization-pipeline]] — Full pipeline architecture
- [[ai-inference-compiler-stack]] — TVM/IREE for low-bit quantization
- [[tinyml-microcontroller-ai-inference]] — Same quantization principles at edge scale
- [[fhe-enterprise-deployment-2026]] — Encryption overhead drives inference optimization

## References

1. FlashAttention-3 Ampere Support — Dao-AILab/flash-attention GitHub Issue #1049 (2026)
2. Mohan FP8 CUDA Experimental Framework — arXiv:2606.01839 (June 2026)
3. CuTile Cross-Architecture Evaluation — arXiv:2604.23466 (2026)
4. RIS-Kernel Sparse Attention — SSRN 6869438 (2026)
5. TensorRT-LLM — NVIDIA GitHub, developer.nvidia.com (2026)
6. Qwen3.5-35B-A3B RTX 3090 Benchmark — CodePulse (July 2026)
7. FlashInfer Megakernel Fusion — flashinfer.ai (2026)
8. AutoKernel — GitHub (2026)
9. vLLM PagedAttention — vllm.ai (2026)
10. Nvidia CUDA Programming Guide — Ampere Architecture (2026)

## 2026-08 Deepening Addendum

### Sync-Bound Ceiling — the real bottleneck

Corpus memory (PH3dFqmmpL/lfPyaROrFw) confirms the deepest structural finding: MegaQwen's megakernel decodes 527–531 tok/s (3.9× over HuggingFace) but is **sync-bound**, not memory-bandwidth-bound. Batch=1 BF16 inference uses only 5% of peak bandwidth (47 GB/s of 936 GB/s); ~140 `grid.sync()` calls per token at ~0.7 µs each create ~100 µs overhead per token and set an architectural ceiling around **~530 tok/s** for cooperative megakernels. Practical corollary: further single-GPU gains require reducing synchronization points or moving to wavefront-style scheduling (Hopper+), not more bandwidth or L2. This is structurally isomorphic to [[entropy-as-signal]] — the obvious constraint (bandwidth, cache) is a misdirection; the true constraint is coordination overhead.

### Multi-GPU Tensor Parallelism

Dual RTX 3090 with NVLink (112.5 GB/s bidirectional) is unique among consumer GPUs for tensor parallelism: 48 GB combined VRAM, tensor-parallel 27B-class models, and multi-token-prediction speculative decoding yield **50+ tok/s** on Qwen3.6-27B while eliminating offloading bottlenecks.

### RL-Guided Kernel Auto-Optimization

- **CUDA-L2** (arXiv:2512.02551): RL discovered 6 transferable Ampere kernel patterns — zero-padding, double-buffered register fragments, multi-step prefetching, staggered A-B prefetch scheduling, block swizzle, direct register-to-shared-memory epilogue — beating cuBLASLt-AT by **11.4%** and directly applicable to GA102.
- **CudaForge** (arXiv:2509.14279): multi-agent LLM kernel workflow tested on RTX 3090; 97.6% correctness, **1.68× over PyTorch**, ~$0.30/kernel.
- **AutoKernel** (arXiv:2603.21331): agent-driven iterative kernel optimization — the convergence of agentic AI and hardware tuning.

### 2026-08 Ecosystem Movement

- **TensorRT adaptive inference for RTX** (NVIDIA, 2026): runtime auto-optimization via Dynamic Shapes Kernel Specialization plus built-in CUDA Graphs to eliminate launch overhead — directly attacks the launch-overhead component of the sync-bound ceiling without custom kernels.
- **TensorRT-LLM Windows beta** brings NVIDIA-optimized GeForce RTX kernels to consumer Ampere on Windows.
- **Gemma 4 local CUDA benchmarks** on RTX 3090: BF16 **110 tok/s**, Q4_K_M variant (LinkedIn, Apr 2026).
- **llama.cpp Discussion #8422**: `CUDA_USE_TENSOR_CORES` compile-time flag exploration for single-3090 + 64 GB system RAM builds.

### Verification Status

Grounded in the shared corpus via memory_load (lfPyaROrFw, PH3dFqmmpL, eUBVbO5xZo, NKOTp8D6YY) plus wiki grep; remaining 2026-08 gaps filled via search_engine (NVIDIA TensorRT docs, LinkedIn Gemma 4, llama.cpp discussion, RightNow AI spec guide, bestgpusforai 3090-vs-Ti). The 355-book library is not mounted in this environment (`search_library` not exposed) — honest gap carried from prior cycles. Duplicate page `rtx3090-cuda-optimization.md` (92 lines; index rows 234/291) is a known integrity gap; noted, not deleted.

### New Cross-Domain Connections (2026-08)

- [[entropy-as-signal]] — sync-bound ceiling as coordination-overhead vs bandwidth misdirection
- [[agentic-ai-self-learning]] — AutoKernel/CUDA-L2 agent-driven kernel search
- [[autoresearch]] — optimization-loop isomorphism
- [[local-frontier-inference-cascading]] — dual-3090 NVLink TP + MoE routing
- [[multi-gpu-inference-architectures]] — consumer NVLink uniqueness

### Additional References (2026-08)

11. CUDA-L2 — arXiv:2512.02551 (2025)
12. CudaForge — arXiv:2509.14279 (2025)
13. AutoKernel — arXiv:2603.21331 (2026)
14. NVIDIA TensorRT Adaptive Inference for RTX — developer.nvidia.com (2026)
15. Gemma 4 RTX 3090 BF16/Q4 benchmark — LinkedIn (Apr 2026)
16. llama.cpp Discussion #8422 — github.com/ggml-org/llama.cpp (2026)
