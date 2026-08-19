# AI Hardware Co-Design

**Status:** STABLE
**Created:** 2026-05-19
**Last Updated:** 2026-05-26
**Research Cycle:** BUILD-133

---

## Overview

Hardware-AI co-design: jointly optimizing neural network architectures and the underlying compute fabric (GPUs, TPUs, NPUs, FPGAs, custom ASICs) rather than treating hardware as a fixed constraint. The co-design paradigm emerged as dominant post-2020 when domain-specific architectures (DSAs) began outperforming general-purpose GPUs for targeted workloads by 5-50x in energy efficiency.

**Key insight:** The chip alone is not enough — it is the compiler stack, ecosystem maturity, and software-defined abstraction that determine real-world viability.

---

## The DSA Landscape 2025-2026

### Datacenter-Class Accelerators

| Accelerator | Architecture | Key Differentiator | Status 2026 |
|---|---|---|---|
| **Cerebras WSE-3 (CS-3)** | Wafer-scale engine, 4T+ params on-chip | No off-chip memory bandwidth bottleneck; 6x faster inference on frontier LLMs vs Groq | Active, shipping to enterprise |
| **Groq LPU** | Deterministic LPUs, no weight movement | Token-by-token sequential processing, sub-100ms first token | Absorbed by NVIDIA 2025, ecosystem uncertain |
| **AWS Trainium2/Inferentia2** | Custom ASIC + compiler stack | $/M tokens optimization, native SageMaker integration | Production, competitive pricing |
| **Google TPU v5p** | TPU-specific architecture, XLA compiler | Tightest software-hardware integration for training | Active, GCP-only |
| **SambaNova DataScale** | SN40L chips, dataflow architecture | Reconfigurable compute units, large KV cache on-chip | Active, enterprise deployment |
| **Tenstorrent Wormhole/Grasshopper** | RISC-V based, open ISA | Open-source toolchain, RISC-V microkernel support emerging | Early access, RISC-V edge potential |

**McKinsey assessment (2025):** DSAs achieve efficiency through five dimensions: special data types/operations, massive parallelism, customized memory access, amortized instruction overhead, and algorithm-architecture co-design. Foundries now enable startups to access advanced nodes without capex.

---

## Compiler Frameworks: The Software Stack

### TVM (Apache)
- **Status:** v0.25.dev0 (2026), mature production deployment
- **Strengths:** Broadest framework support (PyTorch, JAX, ONNX, TensorRT), auto-scheduler for hardware-specific optimization, largest vendor ecosystem
- **Weaknesses:** Auto-tuning can be slow (minutes to hours per model/hardware pair)
- **Use case:** Multi-hardware deployments, heterogeneous edge environments

### IREE (Intermediate Representation Execution Environment)
- **Status:** LF AI & Data Foundation sandbox (2024), production-ready 2025
- **Strengths:** MLIR-based end-to-end compiler, scales from datacenter to mobile/edge, RISC-V support improving (GenAI RISC-V microkernels added 2025)
- **Weaknesses:** Fewer supported frameworks than TVM, smaller community
- **Use case:** Edge deployments, RISC-V targets, AMD GPU workloads (SDXL in MLPerf 2025)

### XLA (Accelerated Linear Algebra)
- **Status:** Google-internal origin, now broader ecosystem
- **Strengths:** Deepest TPU integration, replaced CUDA for Google TPU fleet, tight compiler-hardware alignment
- **Weaknesses:** TPU-biased, less portable to non-Google hardware
- **Use case:** Google Cloud TPUs, JAX workloads

### PolyBlocks (arXiv 2603.06731, March 2026)
- **Status:** Research -> early production
- **Innovation:** MLIR-based modular compiler infrastructure; lightweight affine access analysis for loop-nest transformations; composable pass pipelines
- **Significance:** Bridges growing gap between higher-level AI frameworks and specialized AI chips with unique features

**Compiler-aware hardware design** (ACM 2025): Aligning hardware architecture with DL compiler capabilities improves edge deployment by 20-40% vs designing hardware first then retro-fitting compiler support.

---

## Edge vs Datacenter Co-Design Principles

### Datacenter Priorities
- **Throughput > latency:** Batch processing, large model training, inference at scale
- **Memory bandwidth is the bottleneck:** HBM3/HBM3e, chiplet designs, on-chip SRAM for KV cache
- **Power envelopes:** 300W-1000W per chip acceptable; cooling is infrastructure problem
- **Ecosystem lock-in:** CUDA moat, vendor-specific toolchains create switching costs

### Edge Priorities (arXiv 2501.15014, CMU SEI 2024)
- **Determinism required:** Protection systems must not introduce variable latency
- **Power budget:** <1W for RTU/IED deployments (battery/solar backup scenarios)
- **Memory constraints:** <512MB typical RTU; <2GB gateway-class
- **Latency targets:** <100ms for protection relay decisions, <1s for monitoring
- **Chip-package co-design (Jun 2025):** 2.5D/3D packaging, interposer optimization, memory proximity matter as much as compute density

### Agentic Edge AI (May 2026)
- Long-lived, tool-mediated loops with variable compute demands
- Edge PPA dominated by memory, not compute
- Token streaming + local tool execution creates bursty workload profiles

---

## Real Co-Design Case Studies

### 1. FPGA Inference at Edge (see fpga-inference-acceleration wiki)
- **Sub-ms latency, 10-50W power envelopes**
- Vitis AI DPU overlay: Versal ACAP, Alveo cards
- HLS4ML for custom model synthesis
- Use cases: RTU/IED protection systems, substation monitoring

### 2. Triton Kernel Optimization (see triton-kernels-rtx-optimization wiki)
- **Custom GPU kernels for RTX 3090 tensor cores**
- SageAttention 2-5x speedup via kernel fusion
- INT4 inference, KV cache compression
- AutoKernel iterative optimization pipeline

### 3. Grid Edge AI (see grid-edge-ai wiki)
- **AI inference at distribution edge**
- RTU/IED deployment, IEC 61850 integration
- Anomaly detection on GOOSE/SV messages
- Deterministic latency requirements for protection systems

### 4. LoRaWAN Sensor Networks (see lora-wan-critical-infrastructure wiki)
- **125M+ devices, SCADA integration**
- MCU selection: nRF52840, ESP32-C6, SiM3C8xx
- Power budget math: 1.14mAh/day typical node
- Edge inference on gateways for real-time analytics

---

## Co-Design Methodology

### The Three-Layer Stack
```
Layer 1: Algorithm (model architecture, precision, sparsity)
  -->
Layer 2: Compiler (TVM/IREE/XLA, schedule generation, kernel selection)
  -->
Layer 3: Hardware (DSA features, memory hierarchy, parallelism model)
```

**Principle:** Optimize jointly, not sequentially. Designing hardware first then software second (or vice versa) misses 20-40% of achievable efficiency.

### Closed-Loop Optimization
- **Self-improving agents** (see self-improving-agent-patterns wiki) can automate hardware-software co-optimization via iterative benchmarking
- **SWE-bench evaluation** for compiler/hardware co-design validation
- **Temperature escalation** for exploring broader design spaces

---

## Open Questions & Frontiers

1. **RISC-V AI acceleration:** Tenstorrent leads but ecosystem immature; RISC-V microkernels still missing for many GenAI workloads
2. **Post-quantum implications for hardware security:** PQC algorithms have different computational profiles than current crypto (see post-quantum-cryptography-readiness)
3. **Hardware-defined vs software-defined compute:** Modular approach (compiler-driven, software-defined) vs traditional DSA approaches
4. **Multi-vendor edge deployments:** How to manage heterogeneous hardware fleets with unified compiler abstraction
5. **Economic viability:** DSAs require volume to amortize NRE; foundry access democratizes but does not eliminate capex

---

## Cross-Domain Connections

- **FPGA inference acceleration** — sub-ms latency, 10-50W edge deployment
- **Triton kernel optimization** — custom GPU kernel design patterns
- **Grid edge AI** — deterministic inference requirements in utility infrastructure
- **Autonomous coding agents** — automated hardware-software co-optimization loops
- **Self-improving agent patterns** — closed-loop benchmark-driven optimization
- **Post-quantum cryptography** — hardware implications for PQC acceleration

---

## References

- PolyBlocks: arXiv 2603.06731 (March 2026) — MLIR-based compiler infrastructure
- McKinsey: "Domain-Specific Architectures and the Future of Compute" (2025)
- ACM CACM: "Democratizing Domain-Specific Computing"
- ACM: "Compiler-aware AI Hardware Design for Edge Devices" (2025)
- CMU SEI: "Co-Design for Edge Artificial Intelligence" (2024)
- MDPI Hardware: "Hardware Acceleration for Machine Learning" (2025)
- SemiEngineering: "Designing Chips In The Context Of Rapidly Evolving AI" (May 2026)
- Fleetwood: "Domain-Specific Architectures for AI Inference" (2025)
- arXiv 2501.15014: Edge AI compression techniques
- arXiv 2604.14233: IEC 61850 GOOSE anomaly detection

## 2026 Research Additions

### Compiler-Aware Co-Design
- **arXiv 2508.14899** — RISC-V microkernel support in IREE compiler. Enables GenAI inference on RISC-V hardware with MLIR-based lowering. Out-of-order CPU models show 5.22× advantage over in-order for ML workloads.
- **arXiv 2604.13523 (ATLAAS)** — Automatic tensor-level abstraction of accelerator semantics via 8-pass MLIR semantic lifting. Bridges architecture-level model extraction to bit-level LLVM IR.
- **MLIR-ARX** — Accelerator-aware MLIR-to-RISC-V compilation integrated with EDA flow. Uses analytic + profile-guided two-stage cost model for partitioning decisions.

### Industry Signals
- **PatSnap Edge AI Compiler Patents 2026** (Apr 2026) — Cluster 4: NAS and hardware co-design emerging as dominant patent category. Joint neural + hardware architecture search tightly coupling compiler decisions.
- **ASP-DAC 2026** — MLIR-based hardware-software co-design framework for agile processor specialization. RISC-V ISA simplifies custom instruction extensions but full specialization pipeline remains challenging.
- **ASPLOS 2026 Architecture 2.0 Workshop** — Co-design of OS policies with hardware and compiler support. AI techniques applied to systems challenges across hardware stack.
- **HiPEAC 2026** — AI-assisted hardware design reshaping how systems are conceived, built, verified, deployed. Compilers, runtimes, architectures deeply intertwined.

## Failure Modes

| Failure Mode | Trigger | Impact | Mitigation |
|---|---|---|---|
| Compiler stack immaturity | DSA ships without production-grade toolchain | Model porting fails silently; suboptimal kernels | Require compiler-first DSA design; validate with StableHLO/IREE |
| Ecosystem lock-in | Vendor-specific compiler APIs | Vendor lockout; model retraining cost | Standard IR intermediates (MLIR, StableHLO); multi-backend support |
| Memory-bandwidth ceiling | On-chip SRAM insufficient for target model | Degraded perf vs claims; falls back to HBM | Co-design with model partitioning; KV cache optimization |
| NRE amortization failure | DSA volume doesn't reach breakeven | Unit economics worse than GPU baseline | Modular specialization; foundry democratization (GlobalFoundries MPW) |
| Software-defined compute gap | DSA optimized for narrow workload class | Model evolution outpaces hardware capability | Reconfigurable compute units; software-defined abstraction layer |

## TRL Assessment

| Component | TRL | Rationale |
|---|---|---|
| MLIR compiler infrastructure | 8 | Production deployment across Cerebras, TPU, IREE, TensorFlow |
| RISC-V AI acceleration | 6 | Microkernels in IREE (2508.14899); edge deployments active |
| DSA datacenter accelerators | 7-8 | Cerebras WSE-3, Trainium2 shipping; enterprise deployments |
| Agile co-design (AHA/MLIR-ARX) | 4-5 | Research prototypes; ASP-DAC 2026 tutorials |
| ATLAAS semantic lifting | 3 | arXiv publication; no production deployment |
| Edge DSA deployments | 6-7 | Coral NPU, Hailo, Myriad X in field |

## Production Deployment Gap Analysis

| Dimension | Research State | Production Reality | Gap |
|---|---|---|---|
| Compiler coverage | MLIR handles major frameworks | Long-tail ops fall back to CPU emulation | ~5-15% op coverage gap per vendor |
| Model portability | StableHLO as universal IR | Vendor-specific optimizations required | Manual tuning per DSA still needed |
| Cost model accuracy | Analytic cost models in research | Profile-guided optimization dominates | ~2-3× perf variance between analytic and measured |
| Ecosystem maturity | Open-source compiler stacks | Production support SLA required | Enterprise-grade toolchain gap |
