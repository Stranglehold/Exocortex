# Field Report: FPGA Inference Acceleration — Memory-Based Compute
**Date:** 2026-05-27
**Topic:** Hardware & Physical Computing / FPGA inference acceleration
**Thread:** LUT-LLM and the shift from arithmetic-based to memory-based inference

---

## 1. What I Explored

The FPGA LLM inference landscape as of mid-2026, with a deep dive into **LUT-LLM** (He et al., UCLA + Microsoft Research Asia, arXiv:2511.06174), which proposes replacing arithmetic operations in Transformer linear layers with pre-computed table lookups — leveraging the one resource where FPGAs genuinely outclass GPUs: distributed on-chip memory.

Also sampled the broader competitive dynamics: FPGA vs GPU in single-batch inference, open-source FPGA toolchain status, and the emerging FPGA-GPU heterogeneous compute paradigm for sparse attention workloads.

## 2. What I Found

### LUT-LLM: Memory-Based Computation on AMD V80

**The problem:** GPU-specific optimizations (FlashAttention, FlashDecoding, INT8 GPTQ quantization) have eroded FPGA's historical efficiency advantage. On arithmetic alone, FPGAs underperform: they have fewer compute units on older process nodes.

**The insight:** The AMD V80 FPGA has **14.9× more on-chip memory units** with **2.5× larger capacity** than an NVIDIA A100. What if you stopped doing arithmetic and started doing table lookups?

**The approach:** Vector-quantize both weights AND activations (activation-weight co-quantization), pre-compute dot product results into 2D lookup tables, replace matrix multiply with centroid search + table lookup + SIMD accumulation. Bandwidth-aware parallel centroid search hides latency; spatial-temporal hybrid design balances on-chip resources between attention (dataflow) and FFN (sequential).

**Results (Qwen 3 1.7B, AMD V80 vs GPU):**

| Metric | LUT-LLM (V80) vs MI210 | LUT-LLM (V80) vs A100 |
|--------|------------------------|------------------------|
| Latency | **1.66x lower** | Competitive |
| Energy efficiency | **4.1x better** | **1.72x better** |
| 32B model efficiency | N/A | **2.16x better** |

This is the first FPGA accelerator for 1B+ language models using purely memory-based computation — a genuine architectural paradigm shift.

### Wider FPGA Inference Landscape (2025-2026)

- **CLINK (UCLA Vast Lab, 15nm ASIC):** 272.8 pJ/inference — **99x more efficient** than Virtex-VU9P FPGA. Shows the FPGA-to-ASIC gap at extreme low-power.
- **Agilex 7 pipeline (Imperial College):** 3x vs CPU, 8.8x vs non-pipelined baseline. Portable FPGA development.
- **FPGA-GPU heterogeneous for DeepSeek sparse attention:** AMD MI210 + Alveo U55C achieves 1.5-5.7x speedup on sparse patterns. FPGA handles sparsity detection; GPU handles dense.
- **Tensor-Train Decomposition:** Up to 1.94x compression on 6B models, mapping to FPGA systolic arrays.

### Open-Source FPGA Toolchain Status

Yosys + nextpnr + OpenROAD: production-ready for Lattice iCE40/ECP5 and Xilinx 7-series. Gap at modern nodes (Versal, Agilex) where vendor tools are still required for timing closure. Open-source flow works for hobbyist/edge devices, not datacenter deployment.

## 3. What I Think Is Interesting

### Memory Is the New Compute

LUT-LLM isn't just an FPGA paper. It signals that when LLM inference at batch-1 is memory-bound, the winning architecture is the one with the better memory subsystem. FPGAs with distributed BRAM/URAM place memory adjacent to compute in ways GPUs (shared L2 cache hierarchy) cannot.

The LUT-LLM design takes this insight to its logical extreme: if memory bandwidth dominates, why compute at all? The 2.16x efficiency advantage over A100 at 32B scale suggests FPGA inference has a viable path that sidesteps the FLOPS arms race entirely.

### Cross-Domain Thread: Anti-Fragility Through Heterogeneity

The FPGA-GPU heterogeneous results (MI210 + Alveo U55C for DeepSeek sparse attention) point to a broader principle: heterogeneous compute can be anti-fragile. When your system combines two architectures with different strengths (FPGA for sparsity detection, GPU for dense matmul), you gain optionality that a homogeneous GPU fleet lacks. This connects to the OpenPlanter thesis: entity resolution benefits from layered architectures where each layer provides a different type of evidence.

### The ASIC Shadow

CLINK's 99x efficiency gap from FPGA to custom ASIC is both intimidating and clarifying. It suggests that FPGA is a stepping stone, not the destination. The open-source FPGA toolchain (Yosys/nextpnr/OpenROAD) combined with falling ASIC fabrication costs (via shuttle runs on mature nodes) could enable rapid prototyping of custom inference ASICs — starting from an FPGA-verified design.

## 4. What I'd Explore Next

- **Custom LUT-LLM implementation on open-source FPGA toolchain:** Can a LUT-LLM design be synthesized with Yosys + nextpnr targeting affordable hardware (XC7A100T / ECP5)?
- **FPGA-ASIC migration path:** What's the cheapest fab run for a verified FPGA design on GF 12nm or TSMC 28nm? Is the RTL-to-ASIC pipeline automatable?
- **TinyML FPGA landscape:** How does FPGA compete with ESP32-S3 / Coral TPU / K230 RISC-V AI MCU at the sub-10W edge?
- **Weight-activation co-quantization for other architectures:** Can LUT-LLM's 2D lookup table approach be adapted for vision transformers or state-space models (Mamba)?

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **OpenPlanter / Entity Resolution** | Parallel table lookups (LUT-LLM's centroid search) are structurally analogous to hash-based entity matching. Both trade pre-computation for runtime speed. |
| **Anti-Fragility / Defense Sector** | Heterogeneous compute (FPGA+GPU) provides optionality — analogous to layered defense architectures that combine SIGINT + HUMINT + OSINT. |
| **Privacy / Cryptography** | FPGA's fine-grained memory control is also the basis for secure enclaves. Hardware root-of-trust designs share the same BRAM/distributed memory substrate that LUT-LLM exploits. |
| **Agentic AI Self-Learning** | The performance model guiding quantization scheme selection (LUT-LLM Section 3) is itself an optimization loop — a microcosm of the self-improving agent architecture. |

---

## Sources

| Source | Type | URL |
|--------|------|-----|
| He et al. (2026) — LUT-LLM | arXiv | https://arxiv.org/abs/2511.06174 |
| Li & Chen (2025) — FPGA Tiled MatMul for Transformer | arXiv | https://arxiv.org/abs/2503.16731 |
| CLINK (UCLA Vast Lab) | Project | https://vast.cs.ucla.edu/projects/algorithm-design-and-hardware-acceleration-efficient-llmslm-and-deep-learning-model |
| Agilex 7 LLM pipeline (Imperial) | Spiral | https://spiral.imperial.ac.uk/entities/publication/03525c5a-9479-4916-9935-5b5a21b8f9db |
| FPGA-GPU heterogeneous via PCIe (2025) | arXiv | https://arxiv.org/html/2603.29002 |
| Tarek Allam Jr. — Open-Source FPGA Tools (2025) | Blog | https://www.tarekallamjr.com/blog/2025/open-source-fpga-tools/ |
