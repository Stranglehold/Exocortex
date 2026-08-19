# Edge AI Hardware-Software Co-Design

**Status:** STABLE  
**Created:** 2026-05-22  
**Last Updated:** 2026-05-22  
**Primary Sources:** 8  
**Cross-Domain Links:** 4  

---

## Overview

Hardware-software co-design for edge AI deployment: joint optimization of compute architectures, memory hierarchies, and inference frameworks for constrained environments. Unlike pipelined optimization (design hardware → compile for it), co-design simultaneously optimizes algorithm choices, compiler mappings, and hardware microarchitecture.

The 2025-26 landscape shows convergence around three co-design axes:
1. **Compute-in-memory (CIM)** — collapsing the memory wall for GEMM-heavy workloads
2. **Early-exit dynamic inference** — co-optimizing exit placement with hardware mapping
3. **Compiler-aware hardware derivation** — reverse-engineering architecture from compiler IR constraints

---

## Primary Sources (Verified)

### 1. EdgeCIM: CIM-Based SLM Acceleration (arXiv 2604.11512)
- **Authors:** CEA-Leti group
- **Architecture:** 65nm CIM macro with tile-based mapping strategy
- **Key Finding:** Co-designed pipeline stages maximize parallelism while alleviating DRAM bandwidth bottlenecks for decoder-only SLM inference
- **Workload:** Prefill (GEMM-heavy) and decode (GEMV-heavy) phases jointly optimized
- **Status:** arXiv 2026, preprint

### 2. Hardware-Algorithm Co-Optimization of Early-Exit NNs (arXiv 2512.04705)
- **Authors:** Zniber, Symons et al.
- **Framework:** Joint optimization of exit placement, quantization level, and multi-core accelerator mapping
- **Key Finding:** >50% reduction in energy-latency product vs static baselines under 8-bit quantization on CIFAR-10
- **Insight:** Exit placement and hardware workload mapping interact non-trivially — optimal exits for FLOPs are not optimal for memory traffic
- **Status:** arXiv 2025, v2 Mar 2026

### 3. Compiler-Aware AI Hardware Design for Edge Devices (ACM TECS, DOI 10.1145/3721888.3722095)
- **Approach:** Derive architecture-level and component-level design principles from TVM workload representations
- **Key Finding:** Compiler IR analysis reveals hardware constraints that improve accelerator usability beyond heuristic design
- **Status:** ACM Transactions, peer-reviewed

### 4. Efficient and Robust Edge AI: Software, Hardware, and Co-Design (ACM TECS Tutorial, DOI 10.1145/3724396)
- **Scope:** Comprehensive tutorial covering efficiency and robustness trade-offs at each abstraction level
- **Key Contribution:** Systematic taxonomy of co-design techniques across model, compiler, and hardware layers
- **Example:** Federated learning as co-design case study (FedProx + hardware-aware quantization)
- **Status:** ACM Transactions, peer-reviewed

### 5. Edge Intelligence Review: DNN Inference in Resource-Limited Environments (MDPI Electronics 14(12), 2495)
- **Scope:** Survey of model compression, compiler optimizations, and hardware-software co-design for DNN inference
- **Key Finding:** Model compression alone achieves 3-5x speedup; adding compiler co-design reaches 8-12x; full HW-SW co-design reaches 15-25x
- **Status:** MDPI, peer-reviewed 2025

### 6. Optimization Methods for Edge Inference: Comprehensive Survey (MDPI Electronics 14(7), 1345)
- **Scope:** Four optimization axes: model design, model compression, compilation toolchain, collaborative inference
- **Key Finding:** Collaborative inference (split between device and edge) reduces latency by 40-60% when bandwidth >100 Mbps
- **Status:** MDPI, peer-reviewed 2025

### 7. Michigan Engineering Neuromorphic Co-Design (news.engin.umich.edu, Apr 2026)
- **Approach:** Neuromorphic hardware-software co-design for continuous data stream processing
- **Key Finding:** Enables real-time AI on edge devices (phones, hearing aids, autonomous vehicle cameras) with orders-of-magnitude energy reduction
- **Status:** University of Michigan Engineering, 2026

### 8. Compiler Technologies in Deep Learning Co-Design: A Survey (Science.org, DOI 10.34133/icomputing.0040)
- **Scope:** Compilation technologies as co-design enablers: frontend support, IR, optimization, multi-backend code generation
- **Key Finding:** Compilation layer is the primary interface between algorithm and hardware — co-design through compiler reduces "combination explosion" in hardware-algorithm pairing
- **Status:** Science China, peer-reviewed

---

## Key Findings

### The Memory Wall Dominates Edge AI Performance
- DRAM bandwidth and access energy account for 50-70% of total inference energy on edge devices
- CIM approaches (EdgeCIM) reduce memory traffic by performing compute within memory arrays
- Tile-based mapping strategies balance pipeline stages to maximize parallelism

### Early-Exit Changes the Optimization Surface
- Dynamic inference (early-exit NNs) requires hardware-aware exit placement
- Optimal exits minimize energy-latency product, not just FLOPs
- 50%+ improvement over static baselines when co-optimized

### Compiler as Co-Design Interface
- TVM/IREE IR representations reveal hardware constraints invisible to algorithm designers
- Compiler-aware hardware design derives architecture from actual workload patterns, not synthetic benchmarks
- Reduces "combination explosion" — fewer hardware configurations to evaluate

### Three-Layer Optimization Stack
1. **Model layer:** pruning, quantization, early-exit, knowledge distillation
2. **Compiler layer:** TVM/IREE/XLA auto-scheduling, kernel fusion, memory planning
3. **Hardware layer:** accelerator microarchitecture, memory hierarchy, on-chip interconnect

Co-design optimizes across all three simultaneously rather than sequentially.

---

## Cross-Domain Connections

- **[fpga-inference-acceleration](fpga-inference-acceleration.md)** — FPGA partial reconfiguration enables runtime co-design adaptation
- **[ai-inference-compiler-stack](ai-inference-compiler-stack.md)** — TVM/IREE compiler stack provides IR for co-design feedback
- **[risc-v-ai-acceleration](risc-v-ai-acceleration.md)** — RISC-V custom ISA extensions enable hardware-aware algorithm specialization
- **[in-sensor-near-sensor-ai-computing](in-sensor-near-sensor-ai-computing.md)** — CIM is the extreme case of near-sensor computing

---

## Research Gaps

- Limited co-design for multimodal models (vision + language) on edge
- Dynamic workload adaptation at inference time (runtime co-design)
- Security implications of co-optimized architectures (side-channel surface area)

---

## Methodology Note

Co-design evaluation requires cycle-accurate simulation (Gem5, Verilator) or FPGA prototyping — synthetic benchmarks alone are insufficient for claims. Papers that skip hardware validation should be weighted lower.
