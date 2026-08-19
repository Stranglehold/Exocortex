# Neural Architecture Search & AutoML

**Status:** STABLE
**Created:** 2026-05-23
**Last Updated:** 2026-05-23
**Domain:** Hardware & Physical Computing / AI Systems

## Overview

Neural Architecture Search (NAS) automates discovery of optimal neural network architectures for specific tasks, hardware constraints, and performance targets. Hardware-aware NAS (HW-NAS) extends this by co-optimizing for latency, energy, and memory alongside accuracy.

## NAS Method Families

### 1. Differentiable NAS (DARTS family)
- Continuous relaxation of architecture search space, gradient descent over weights and architecture
- DARTS-EAST (Springer 2025): edge-adaptive selection with topology-first discretization, fixes randomness in edge selection
- ZO-DARTS++ (arXiv 2503.06092): zeroth-order size-variable differentiable NAS
- RZ-NAS (ICML 2025 poster): LLM-guided NAS with reflective zero-cost strategy

### 2. Evolutionary NAS (E-NAS)
- Population-based mutation/crossover of architecture genes
- AE-NAS (Nature 2025, Mar 20): attention-enhanced evolutionary search with forward evolution mechanism
- Still used in production for robustness despite differentiable advances

### 3. One-Shot / Proxy-Based
- Train supernetwork covering search space, sample sub-architectures
- CoreML hardware utility (Apple 2026) enables 10-probe latency estimation (arXiv 2504.00663)

## Hardware-Aware NAS (HW-NAS)

**Key survey:** ACM Computing Surveys 10.1145/3524500 (comprehensive HW-NAS taxonomy)
**Key survey:** arXiv 2101.09336 (search space, strategy, acceleration, four dimensions)

HW-NAS multi-objective optimization targets:
- Execution latency (ms)
- Energy consumption (mJ)
- Memory footprint (MB)
- Compute budget (MFLOPs)

### Recent Advances

**LLMForge (arXiv 2605.17653):** Multi-backend HW-NAS for sub-billion-parameter Transformers on edge devices. Co-optimizes architecture choice and accelerator-specific cost. Addresses tight memory-bandwidth, energy, and thermal budgets.

**MicroNAS (Nature 2025, Mar 4):** First demonstration of NAS for memory/latency-constrained hardware targets.

## Compiler Integration

### TVM-Based NAS
- MATCH framework: model-aware TVM-based compilation for heterogeneous edge devices
- Compiler-aware hardware design (ACM TECS 2025): derive architecture principles from TVM workload representations

### IREE-Based NAS
- IREE (MLIR-based end-to-end compiler): scales from datacenter to edge
- arXiv 2605.12445: packed layouts for vector-length-agnostic ML code, IREE + LLVM extensions

## Computational Cost Hierarchy

| Method | Approximate GPU Hours | Typical Use Case |
|--------|----------------------|------------------|
| RL-NAS | 1000-3000 | Baseline research |
| E-NAS | 500-1500 | Robust production |
| DARTS | 50-200 | Efficient search |
| One-Shot | 10-50 | Rapid prototyping |
| Proxy/Zero-Cost | <1 | Screening |

## Primary Sources (8 verified)

1. ACM Computing Surveys 10.1145/3524500 — HW-NAS comprehensive survey
2. arXiv 2101.09336 — HW-NAS four-dimension taxonomy
3. arXiv 2605.17653 — LLMForge multi-backend HW-NAS for edge LLMs
4. Nature 2025 (Mar 4) — MicroNAS memory/latency-constrained NAS
5. arXiv 2503.06092 — ZO-DARTS++ zeroth-order size-variable NAS
6. Springer 2025 — DARTS-EAST edge-adaptive topology-first
7. ICML 2025 poster — RZ-NAS LLM-guided reflective zero-cost NAS
8. ACM TECS 2025 — Compiler-aware AI hardware design for edge devices

## Cross-Domain Links

- [Autokernel & Autonomous Kernel Optimization](research/autokernel-autonomous-kernel-optimization.md) — NAS for kernel-level optimization
- [Edge AI Hardware-Software Co-Design](research/edge-ai-hardware-software-co-design.md) — hardware-aware architecture search
- [AI Inference Compiler Stack](research/ai-inference-compiler-stack.md) — TVM/IREE integration
- [FPGA Inference Acceleration](research/fpga-inference-acceleration.md) — NAS for reconfigurable hardware

## Key Insight

Convergence of NAS, compiler technology, and hardware co-design represents a stack-level optimization opportunity. LLMForge and MicroNAS demonstrate that NAS is no longer just about accuracy — it's about finding the Pareto frontier across accuracy-latency-energy-memory for specific deployment targets. Proxy-based and zero-cost screening are essential since RL-NAS still requires thousands of GPU hours.
