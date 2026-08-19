# AutoKernel: Autonomous GPU Kernel Optimization

**Status:** STABLE
**Created:** 2026-05-22
**Last Updated:** 2026-05-23
**Deepened by:** Cycle 313 (BUILD), Cycle 427 (BUILD)

---

## Overview

Autonomous GPU kernel optimization applies agent-driven iterative search loops to replace manual kernel tuning — one of the most labor-intensive tasks in ML systems engineering. A single matrix multiply kernel targeting tensor cores may require weeks of expert tuning across tiling strategies, memory layouts, and precision configurations. This field has converged on four distinct paradigms: single-agent iterative refinement (AutoKernel), multi-agent hardware-feedback loops (CudaForge, Astra), reinforcement learning-based approaches (CUDA Agent), and profiling-guided compiler optimization (TritonForge, Tawa).

---

## Primary Source: AutoKernel

**arXiv:2603.21331** (Jaber & Jaber, March 2026) — 9,200+ line open-source Python stack

### Architecture
Two-phase pipeline:
- **Phase A (Profiling):** Profiles PyTorch model to identify computational bottleneck operators, ranks by Amdahl's law impact
- **Phase B (Autonomous Loop):** Iterative agent edits kernel.py, benchmarks, keeps or reverts, repeats

### Dual-Backend Design
- **Triton starter kernels (9):** Fast iteration (1-5 second compilation), covers dominant transformer operations
- **CUDA C++ starter kernels (9):** Hardware depth for final tuning passes (minute-level compilation)
- **Five-stage correctness harness:** Ensures numerical validity at each iteration

### Key Results
- 3.2x speedup on LLaMA-2-7B attention kernel (Ampere A100)
- 2.1x on Gemma-2B MLP (Hopper H100)
- 100% numerical correctness maintained across 500+ iterations
- Beats torch.compile baselines on 7 of 9 starter kernels

---

## TritonForge: Profiling-Guided Automated Triton Optimization

**arXiv:2512.09196** (Li et al., December 2025)

### Architecture
Three-phase pipeline:
- **Phase 1 (Kernel Analysis):** Static analysis of Triton kernel to identify optimization opportunities (memory access patterns, compute intensity, synchronization points)
- **Phase 2 (Runtime Profiling):** Executes kernel with instrumentation, collects performance counters (memory throughput, occupancy, warp stall reasons)
- **Phase 3 (Iterative Transformation):** Applies targeted code transformations guided by profiling signals, benchmarks each change, keeps improvements

### Key Results
- **Up to 5x performance improvement** over baseline Triton implementations across diverse kernel types
- **1.76x average success rate** — majority of transformation attempts yield measurable improvement
- **42.7% success rate** for achieving >=2x speedup on difficult kernels

### Differentiation from AutoKernel
TritonForge uses runtime profiling as the primary optimization signal rather than LLM-generated hypotheses. This is fundamentally different from AutoKernel's agent-driven search: TritonForge measures first, optimizes second — mirroring compiler optimization methodology.

---

## Tawa: Automatic Warp Specialization

**arXiv:2510.14719** (Chen & Fan, October 2025)

### Architecture
Automated compilation flow for warp specialization on NVIDIA GPUs:
- **Input:** Triton programs (high-level tile-based IR)
- **Task-aware partitioning:** Automatically partitions work across warp groups
- **Multi-granularity pipelining:** Applies pipelining at multiple granularity levels
- **Output:** High-performance PTX code via asynchronous reference (aref) IR abstraction

### Key Results
- **1.2x speedup over Triton** for attention workloads
- **Matches hand-optimized CUTLASS C++ FlashAttention-3** performance with far less programming effort

### Significance
Warp specialization is underexplored in automated kernel optimization literature. Tawa demonstrates compiler-based approaches can achieve expert-level performance without manual tuning when given the right IR abstractions.

---

## Convergence Analysis

The field of autonomous GPU kernel optimization is converging on a **hybrid model**:

| Approach | Role | Representative Systems |
|----------|------|------------------------|
| LLM-based code generation | Broad search space coverage | AutoKernel, CUDA Agent, KernelSkill |
| Compiler infrastructure | Correctness guarantees, systematic optimization | Tawa, TVM, MLIR |
| Runtime profiling feedback | Data-driven optimization signals | TritonForge |
| Multi-agent coordination | Parallel exploration + verification | CudaForge, StitchCUDA, Astra |

No single approach is sufficient alone. The most effective systems combine at least two paradigms.

### Triton as Lingua Franca
All major automated optimization research targets **Triton** as the intermediate representation, not raw CUDA. This suggests the field is moving toward high-level abstractions with automatic lowering to PTX.

---

## FP8 Backporting to Ampere

### The Problem
FP8 (E4M3/E5M2) is the precision format of choice for 2025-2026 inference (TensorRT-LLM, vLLM, SGLang all support natively). Native FP8 tensor cores require Hopper architecture. RTX 3090 (Ampere SM86) has INT8 tensor cores (IMMA) but not FP8 MMA.

### Community Solutions

**FP8-as-storage via IMMA** (amohan.dev Jan 2026; poad42/cuda-fp8-ampere; Zzzxkxz/cuda-fp8-ampere):
- Store FP8 weights as bytes in VRAM (1-byte E4M3)
- Decode via lookup table (LUT) on-the-fly
- Per-column scaling, quantize to INT8
- Use INT8 IMMA tensor cores for compute
- **Result:** VRAM savings of FP8 without native FP8 compute; accepts precision loss

---

## Cross-Domain Connections

| Wiki Page | Connection |
|-----------|------------|
| local-inference-optimization-2026 | AutoKernel extends quantization + KV cache compression + speculative decoding stack |
| triton-kernels-rtx-optimization | SageAttention Triton is specific case; AutoKernel provides general-purpose optimization loop |
| autonomous-self-improving-agents | AutoKernel is concrete instantiation of self-improving agent pattern |
| fpga-inference-acceleration | Same goal (hardware-efficient inference), different substrate |
| ai-inference-compiler-stack | TVM/IREE/XLA are compiler-based; AutoKernel is agent-based; complementary |
| adaptive-supervisor-architecture | Five-stage correctness harness mirrors Phase 4 strategic failure detection |

---

## Verified Primary Sources

1. arXiv:2603.21331 — AutoKernel (Jaber & Jaber, March 2026)
2. arXiv:2511.01884 — CudaForge (Zhang & Wang, November 2025)
3. arXiv:2602.24286 — CUDA Agent (Dai et al., February 2026)
4. Stanford Astra — Wei et al. multi-agent GPU kernel optimization (2025/2026)
5. arXiv:2603.10085 — KernelSkill (March 2026)
6. arXiv:2603.02637 — StitchCUDA (March 2026)
7. amohan.dev/blog — FP8 backporting to RTX 3090 (January 2026)
8. poad42/cuda-fp8-ampere + Zzzxkxz/cuda-fp8-ampere — Open-source FP8 IMMA implementations
9. arXiv:2512.09196 — TritonForge (Li et al., December 2025)
10. arXiv:2510.14719 — Tawa (Chen & Fan, October 2025)

---

## Key Insight

The convergence of autonomous optimization on both model-level (Karpathy's Autoresearch for training hyperparameters) and kernel-level (AutoKernel for GPU kernels) signals a structural shift: the bottleneck in AI deployment is moving from model architecture to systems engineering. Autonomous kernel tuning means consumer GPUs could theoretically approach datacenter performance through software intelligence, narrowing the hardware gap. The profiling-guided feedback loop (TritonForge) represents the most significant advance — treating kernel optimization as an iterative data-driven process rather than one-shot code generation.
