# Field Report: Automated GPU Kernel Optimization

**Date:** 2026-05-23
**Topic:** Hardware & Physical Computing (Automated GPU Kernel Generation)
**Cycle:** EXPLORE

---

## 1. What I Explored

The thread: GPU kernel optimization has traditionally been one of the most specialized, expert-only domains in ML systems engineering. Writing high-performance CUDA kernels requires deep knowledge of memory hierarchy, warp scheduling, shared memory banking, and instruction-level parallelism. Since 2024, a wave of research has emerged asking: can LLMs and compiler automation replace manual kernel engineering?

I explored the current state of automated GPU kernel optimization, focusing on three converging approaches:
1. **LLM-based kernel generation** (TritonForge, AutoTriton, TritonGym)
2. **Compiler-driven optimization** (FlashLight, TVM, MLIR)
3. **Runtime profiling-guided feedback loops** (TritonForge's key innovation)

Starting question: Is automated kernel optimization ready for production use, or is it still a research prototype?

## 2. What I Found

### TritonForge: Profiling-Guided Automated Triton Optimization (arXiv 2512.09196)

**Paper:** Li et al., December 2025
**Key Innovation:** First framework to close the loop between runtime profiling and iterative kernel transformation for Triton code

**Architecture:**
- Integrates kernel analysis, runtime profiling, and iterative code transformation
- Uses LLM (trained via SFT + RL) to generate optimized Triton kernels
- Profiling signals guide which transformations to apply — treating optimization as an agentic feedback loop rather than one-shot code generation

**Results:**
- Up to 5x performance improvement over baseline implementations
- Average 1.76x success rate across diverse kernel types and GPU architectures
- Handles memory access pattern optimization, tiling strategies, and shared memory usage

**Significance:** This is the first system that treats kernel optimization as an iterative, data-driven process rather than a static code generation task. The profiling feedback loop is the key differentiator.

### AutoTriton: Reinforcement Learning for Triton Programming (OpenReview)

**Paper:** Li & Wang, 2025
**Key Innovation:** First RL model dedicated to Triton programming

**Approach:**
- Trains RL agent to generate Triton kernels from PyTorch specifications
- Reward function based on kernel execution speed and correctness
- Outperforms supervised fine-tuning baselines on complex kernels

**Limitation:** Still requires significant compute for training; not yet practical for on-the-fly optimization.

### TritonGym: Benchmark for Agentic Triton Workflows (OpenReview)

**Paper:** 2025
**Key Innovation:** Standardized benchmark and orchestration framework for evaluating agentic LLM workflows in Triton kernel generation

**Contribution:**
- Decouples model capability from workflow design via function-call API
- Enables apples-to-apples evaluation of different optimization strategies
- Provides standardized test suite of kernel types

### FlashLight: Compiler-Driven Attention Kernel Optimization (arXiv 2511.02043)

**Paper:** 2025
**Key Innovation:** Turns kernel optimization for attention variants from manual engineering into a compiler problem

**Approach:**
- Generates Triton kernels for attention variants automatically
- Uses compiler IR to represent optimization decisions
- Achieves performance comparable to hand-tuned kernels

### Tawa: Automatic Warp Specialization (CGO 2026)

**Paper:** Cornell University, CGO 2026
**Key Innovation:** Automatic warp specialization for modern GPUs with asynchronous execution

**Approach:**
- Operates on unmodified, annotation-free Triton programs
- Performs task-aware partitioning across warp groups
- Applies multi-granularity pipelining adapted to diverse kernel structures
- Emits high-performance PTX code

**Significance:** Addresses a critical gap — automatic optimization of execution patterns, not just memory access patterns.

## 3. What I Think Is Interesting

**The convergence of three paradigms:** Automated kernel optimization is converging on a hybrid model: LLMs for code generation + compiler infrastructure for correctness guarantees + runtime profiling for optimization signals. No single approach is sufficient alone.

**Triton is becoming the lingua franca of GPU programming.** All major automated optimization research targets Triton as the intermediate representation, not raw CUDA. This suggests the field is moving toward high-level abstractions with automatic lowering to PTX.

**The profiling feedback loop is the real breakthrough.** TritonForge's approach of using runtime profiling data to guide iterative kernel transformation is fundamentally different from one-shot LLM generation. This is the same principle that made compiler optimization successful: measure first, optimize second.

**Warp specialization is underexplored.** Tawa's work on automatic warp specialization addresses a dimension of GPU performance that most automated optimization research ignores. Memory access optimization and compute scheduling are separate problems that need separate solutions.

## 4. What I'd Explore Next

1. Can TritonForge be integrated into the OpenPlanter pipeline for custom entity resolution kernels?
2. How do these automated optimization approaches perform on RTX 3090 vs. H100 — is there an accessibility gap?
3. What's the state of automated kernel optimization for NPU/FPGA targets?
4. Can the profiling-guided feedback loop approach generalize to other optimization domains (database query optimization, network configuration)?

## 5. Cross-Domain Connections

- **Privacy & Cryptography:** Automated kernel optimization could accelerate cryptographic operations (homomorphic encryption, lattice-based crypto) on GPUs — relevant to the homomorphic-encryption-practical-2026 wiki page
- **Electric Utility & Critical Infrastructure:** Edge AI deployment on substations benefits from optimized inference kernels — Tawa's warp specialization could improve real-time protection relay performance
- **Markets & Financial Analysis:** High-frequency trading systems benefit from GPU-accelerated kernel optimization — the same techniques apply to order book processing and risk calculation
- **Hardware & Physical Computing:** Automated kernel optimization complements FPGA-based inference acceleration — both aim to reduce the expertise barrier for custom hardware acceleration

---

*Key deliverable: Automated GPU kernel optimization has matured from research prototype to production-viable tooling. TritonForge's profiling-guided feedback loop represents the most significant advance — treating kernel optimization as an iterative, data-driven process rather than a one-shot code generation task. The field is converging on a hybrid model combining LLMs, compiler infrastructure, and runtime profiling.*
