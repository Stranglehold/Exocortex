# FIELD REPORT — FPGA LLM Inference Acceleration

**Date:** 2026-05-20
**Cycle:** EXPLORE-213
**Topic:** Hardware & Physical Computing — FPGA-based LLM Inference
**Primary Sources:** arXiv 2502.16473 (TerEffic), arXiv 2511.06174 (LUT-LLM), llama-fpga (GitHub), Hummingbird+ (ACM)

---

## 1. What I Explored

The 2025-26 landscape of FPGA-based LLM inference accelerators, specifically three architectures that represent a paradigm shift: ternary quantization with on-chip execution (TerEffic), memory-based table-lookup computation (LUT-LLM), and open-source deployment frameworks (llama-fpga, Hummingbird+).

---

## 2. What I Found

### TerEffic (arXiv 2502.16473 — Peking University / NUS)
- **Architecture**: Ternary-quantized LLM inference with 1.6-bit weight compression, specialized TMUs (ternary memory units), compute-memory alignment
- **Performance**: 149x higher throughput than NVIDIA Jetson Orin Nano at 19x power efficiency
- **Throughput**: 16,300 tokens/second for small models; 3x A100 throughput for 2.7B models at just 46W
- **Key innovation**: Fully on-chip execution for small models; HBM-assisted for larger ones

### TeLLMe (ACM/IEEE, companion to TerEffic)
- First table-lookup-based ternary LLM accelerator for low-power edge FPGAs
- 1.58-bit weights with 8-bit activations
- Full prefill AND autoregressive decode support

### LUT-LLM (arXiv 2511.06174 — UCLA / Microsoft Research Asia)
- **Paradigm shift**: Replaces arithmetic MAC operations with memory-based table lookups
- **Architecture**: Vector quantization + dense lookup tables + bandwidth-aware parallel centroid search
- **Result**: 1.66x-2.16x faster inference vs conventional FPGA approaches
- **Key insight**: Leverages FPGAs' abundant on-chip BRAM (block RAM) to shift from compute-bound to memory-bound operations
- **Co-quantization**: Activation-weight vector co-quantization identified as most effective scheme

### llama-fpga (GitHub — adamgallas, DATE'25 / ICCAD'25)
- World's first open-source FPGA LLM accelerator project
- Runs LLaMA2-7B in AWQ 4-bit quantized format
- Targets both embedded and data center FPGAs

### Hummingbird+ (ACM DLaaS '25)
- First demonstration of FPGA-based edge product as practical LLM deployment medium
- Bridges research-to-production gap for FPGA inference

---

## 3. What I Think Is Interesting

**The compute-vs-memory inversion is the key trend.** LUT-LLM's central insight — that FPGAs have so much on-chip memory (BRAM) relative to compute units that shifting from arithmetic to table-lookup is actually faster — flips the conventional accelerator design philosophy. Instead of packing more DSP slices, use the memory hierarchy as the compute substrate. This is analogous to content-addressable memory (CAM) architectures but applied to transformer inference.

**Ternary quantization on FPGAs is uniquely viable.** Unlike GPUs where ternary ops waste tensor cores, FPGAs can implement ternary MACs as simple add/subtract trees with near-zero area cost. TerEffic's 149x improvement over Jetson Orin Nano isn't just quantization — it's hardware-algorithm co-design.

**The 46W envelope matters.** 3x A100 throughput for 2.7B models at 46W is not a typo-level claim — it's plausible because FPGAs skip the memory controller overhead and use direct on-chip buffering. For edge deployment (substations, RTUs, sensor gateways), this is the power envelope that actually matters.

---

## 4. What I'd Explore Next

1. **FPGA vs RISC-V AI acceleration tradeoffs** — the risc-v-ai-acceleration wiki (STABLE) has 59.3x TinyML speedup data; how does it compare to FPGA for the same workloads?
2. **Versal ACAP integration** — AMD's Versal platform combines FPGA fabric with AI engines and Arm processors; is this the convergence point?
3. **Radiation-hard FPGA inference** — HLS4ML at CERN/Fermilab demonstrates ML on rad-hard FPGAs; how far along is LLM inference in that domain?
4. **Dynamic reconfiguration during inference** — can FPGAs reconfigure mid-inference for different layers, enabling smaller footprints?

---

## 5. Cross-Domain Connections

- **Electric Utility & Critical Infrastructure**: 46W FPGA inference directly addresses the edge AI deployment gap in substations (72% cloud latency issues from prior exploration)
- **Autonomous Coding Agents**: llama-fpga open-source project shows the same OSS accelerator trend seen in ML compiler stacks
- **Privacy & Cryptography**: On-chip inference means data never leaves the device — relevant to metadata-resistant communication
- **Hardware & Physical Computing (RTX 3090 optimization)**: Triton kernels for tensor cores vs FPGA DSP slices represent competing paths to the same efficiency goal
- **Data Aggregation & Entity Resolution**: FPGA-accelerated entity matching for real-time graph construction at the edge
