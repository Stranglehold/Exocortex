# Field Report: FPGA Memory-Compute Paradigm Shift for LLM Inference (2026)

**Date:** 2026-06-05 EDT
**Cycle:** EXPLORE
**Topic:** Hardware & Physical Computing — FPGA-based inference acceleration (memory-compute paradigm shift)

---

## 1. What I Explored

Investigated the 2026 state of FPGA LLM inference acceleration, focusing on the **memory-based computation paradigm shift** that is re-framing the FPGA-vs-GPU competition. Previous exploration (2026-05-27) covered LUT-LLM v1 (November 2025) as an emerging approach. Six months later, v2 is validated and the ecosystem has matured: MDPI published energy footprint benchmarks (March 2026), EE Journal ran the headline "FPGAs Beating GPUs at LLM Inference" (March 2026), and the open-source EDA toolchain (OpenROAD) reached production-readiness for real silicon tapeouts.

Specific threads:
- LUT-LLM v2: Qwen 3 1.7B on AMD V80 FPGA, 1.10-3.29x faster generation, 3.05-6.60x better energy efficiency vs GPUs at same technology node
- MDPI Electronics: heterogeneous FPGA+GPU platforms reducing LLM inference energy by up to 6.6x
- RISC-V AI ecosystem convergence: SiFive Intelligence X, llama.cpp RVV support, ztachip open-source accelerator
- Open-source ASIC toolchain: OpenROAD production-ready for SKY130 and GF180MCU, ASIC-Agent LLM-for-EDA workflow
- FCCM 2026: LUT-LLM as part of a broader memory-compute movement on FPGAs

## 2. What I Found

### LUT-LLM v2: Memory-Compute Validated

The core insight of LUT-LLM (arXiv 2511.06174, updated March 2026) is simple: **FPGAs have vastly more distributed on-chip memory than GPUs** — the AMD V80 has 14.9x more memory units at 2.5x larger capacity than an NVIDIA A100. Traditional FPGA accelerators try to compete on arithmetic throughput (TOPS) and lose. LUT-LLM flips the paradigm: vector-quantize the model weights, then replace matrix multiplies with pre-computed table lookups using the FPGA's abundant distributed memory.

Key results on Qwen 3 1.7B:
- Arithmetic operations reduced 4x
- Generation speed: 1.10-3.29x faster than comparable-node GPUs
- Energy efficiency: 3.05-6.60x better (TOPS/W)
- Training recipe: activation-weight vector co-quantization with accuracy preservation
- Architecture: bandwidth-aware parallel centroid search, efficient 2D table lookups, spatial-temporal hybrid design

### MDPI Energy Footprint Paper (March 2026)

Published in Electronics (MDPI, March 3 2026), this study quantified the energy savings of heterogeneous FPGA+GPU platforms for LLM inference. Key finding: FPGA offloading of specific transformer sub-modules (especially FFN layers after vector quantization) reduces total system energy by 3-6x while maintaining throughput. The pattern is NOT FPGA-only — it's strategic workload partitioning where memory-compute-heavy operations go to FPGA and attention/arithmetic-heavy operations stay on GPU.

### EE Journal Analysis (March 24, 2026)

Max Maxfield's article "FPGAs Beating GPUs at LLM Inference: Say What?!?" frames the shift for industry readers: general-purpose GPUs are optimized for training + HPC + graphics + inference, creating a structural inefficiency that FPGAs exploit by being workload-specific. The key quote: "The more general-purpose something is, the more its efficiency is typically degraded for specific tasks."

### RISC-V AI Stack Convergence

From prior research: SiFive Intelligence X family (scalar + vector + matrix compute in single IP), llama.cpp fully leveraging 128-bit RVV for quantized inference, PyTorch upstreaming via RISE initiative, ztachip open-source tensor processor (20-50x acceleration over non-accelerated RISC-V).

### Open-Source EDA Toolchain Maturation

OpenROAD is now "production-ready" for SKY130 and GF180MCU processes. IHP offers shuttle services. ASIC-Agent (2024) demonstrated multi-agent LLMs automating the full ASIC flow: RTL generation, verification, OpenLane hardening, Caravel chip integration. The pathway from "PyTorch model" to "custom ASIC" is compressing from years to months.

## 3. What I Think Is Interesting

### The Memory-Compute Paradigm Shift Is Real — and FPGAs Are the First Beneficiary

This is not incremental optimization. LUT-LLM represents a **qualitative architectural shift** from arithmetic-dominated to memory-dominated computation for LLM inference. The implications cascade:

1. **FPGA competitive landscape changes:** FPGAs are not competing on arithmetic throughput (they'll always lose to GPUs there). They're competing on memory density x bandwidth, which is their structural advantage.

2. **ASICs will follow:** If memory-compute proves viable at scale, custom ASICs will be built specifically for this paradigm (not just the Transformer ASICs like d-Matrix and Etched, but memory-compute ASICs).

3. **Exocortex bridging-local-frontier connection:** The 3.05-6.60x energy efficiency gain is directly relevant to Jake's interest in bridging local-to-frontier model performance. An FPGA-based inference node could run Qwen3.6-27B-class models at a fraction of GPU power, enabling always-on local inference for Exocortex agent loops without cloud dependency.

### The Heterogeneous Future Is Not FPGA-Only

The MDPI paper's insight is crucial: the winning architecture is **heterogeneous workload partitioning**, not FPGA purity. Attention layers (which benefit from high arithmetic intensity) stay on GPU; FFN layers (memory-bandwidth-bound) go to FPGA via memory-compute. This mirrors the big.LITTLE architecture in mobile SoCs.

### The Economics Are Driving Democratization

OpenROAD production-ready + ASIC-Agent LLM-for-EDA + IHP shuttle services = the "GCC moment" for hardware. Five years ago, a custom AI accelerator required a team of 20 ASIC designers and $10M+. Today, a skilled team of 2-3 with LLM assistance can produce a tapeout-ready design on an open-source PDK for under $100K. Domain-specific accelerators will proliferate — for graph traversal (investigative OSINT), FHE (privacy-preserving ML), and sensor fusion (edge AI).

### Cascading Inference Architecture for Exocortex

The heterogeneous partitioning pattern suggests a **cascading inference architecture**: a small FPGA-based model runs continuously (always-on agent loop), escalating to a GPU-based model for complex queries, with a cloud frontier model as the final escalation tier.

## 4. What I'd Explore Next

1. **Practical FPGA deployment for local models:** What would an AMD V80 or Xilinx Alveo card cost, and can it run a Qwen3.6-27B-Q4 model via LUT-LLM methodology? Actual tokens-per-second and watts?
2. **LUT-LLM for graph workloads:** The memory-compute paradigm is inherently better for graph-traversal operations. Could this accelerate OSINT knowledge graph queries?
3. **RISC-V + FPGA hybrid for edge AI:** Combining a RISC-V host processor with FPGA fabric on the same die (like Xilinx Zynq but open-source) for embedded Exocortex agent nodes.
4. **ASIC-Agent pipeline for Exocortex:** Could an LLM agent take a Python description of an Exocortex inference pipeline and produce a custom ASIC layout via OpenROAD? This is the ultimate "bridging local-to-frontier" pathway.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Bridging Local-to-Frontier Performance** | 3-6x energy efficiency enables always-on local models. Cascading FPGA->GPU->Cloud architecture. |
| **AI Agent Architecture** | Always-on agent loop needs low-power inference. Heterogeneous workload partitioning mirrors agent task decomposition. |
| **Privacy & Cryptography** | FPGA FHE accelerators already exist (Cheddar, Intel Heracles). Memory-compute FHE is unexplored intersection. |
| **OSINT & Investigation** | Graph traversal workloads are memory-bandwidth-bound, not arithmetic-bound. FPGA memory-compute could accelerate investigative graph analysis. |
| **Electric Utility** | Edge AI for substation monitoring needs low-power always-on inference. FPGA memory-compute ideal for protection relay anomaly detection and SCADA intrusion detection. |
| **Markets & Financial Analysis** | FPGA-based inference for real-time market data processing already used in HFT. Memory-compute LLMs could enable on-device financial analysis without cloud latency. |
| **History of Intelligence Operations** | Shift from general-purpose to specialized compute mirrors SIGINT evolution from broad-spectrum collection to targeted, workload-specific interception. |

---

## References

1. He et al., "LUT-LLM: Efficient Large Language Model Inference with Memory-based Computations on FPGAs," arXiv 2511.06174v2, March 2026.
2. "Reducing Energy Footprint of LLM Inference Through FPGA-Based Heterogeneous Computing Platforms," MDPI Electronics 15(5):1052, March 2026.
3. Maxfield, "FPGAs Beating GPUs at LLM Inference: Say What?!?," EE Journal, March 24, 2026.
4. "A Survey on Hardware Accelerators for Large Language Models," MDPI Applied Sciences 15(2):586, 2026.
5. VAST Lab, "Algorithm Design and Hardware Acceleration for Efficient LLM/SLM," FCCM 2026.
6. "Recent Developments in Transformer Inference Deployment on FPGA Platforms," ScienceDirect, 2026.
7. OpenROAD Project, "Production-Ready for SKY130 and GF180MCU," 2026.
8. ztachip: Open-Source Tensor Processor, GitHub, 2026.
