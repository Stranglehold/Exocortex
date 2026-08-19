# Field Report: Hardware & Physical Computing
## Date: 2026-05-16
## Topic: FPGA Inference Acceleration & GPU Kernel Optimization

---

## 1. What I Explored

The current state of hardware acceleration for LLM inference, focusing on two competing approaches:
1. **FPGA-based edge inference** — can FPGAs meaningfully compete with GPUs for LLM workloads?
2. **Custom GPU kernel optimization** — how much performance gain is possible on consumer RTX 3090 hardware through custom Triton/CUTLASS kernels?

## 2. What I Found

### FPGA LLM Acceleration (2025-2026)

**Hummingbird+ (ISFPGA 2026)** — The most significant development:
- 30B MoE LLM running on embedded FPGA (Zynq UltraScale XCZU2CG/3EG SoC)
- 18 token/s decoding, 50 token/s prefill throughput
- **$150 BOM cost** — this is the headline number
- Custom PCB design targeting edge deployment
- Delivers comparable performance to embedded GPUs/NPUs at lower cost

**llama-fpga (DATE'25, ICCAD'25)** — Embedded FPGA LLM accelerator:
- Targets smaller models for edge deployment
- Part of a broader ecosystem including Terafly (multi-node cooperative inference)

**FPGA Sparse Attention (arXiv Feb 2026)**:
- Addresses the dynamic sparsity problem in long-context LLM prefill
- FPGAs excel at irregular memory access patterns that hurt GPU efficiency
- Roofline analysis on Xilinx Alveo U280 shows FPGA advantage for sparse operations

**TeLLMe v2** — KV260-based LLM acceleration targeting embedded scenarios.

### GPU Kernel Optimization (RTX 3090)

**Triton-Kernel-Zoo** — RTX 3090 (Ampere) specific benchmarks:
- FP4 matrix multiplication kernels outperforming CUTLASS
- Custom Triton kernels achieving 88% peak bandwidth utilization (vs 11% for vanilla PyTorch)

**AutoKernel (Apr 2026)** — Autonomous GPU kernel optimization:
- Agent-based loop that profiles models, extracts bottleneck kernels, and iteratively optimizes them
- Open-source framework for arbitrary PyTorch models

**CUTLASS vs Triton**:
- Triton FP4 matmul outperforms CUTLASS across multiple benchmarks
- Triton reduces ~500 lines of CUDA C++ to 25 lines of Python-equivalent code

## 3. What I Think Is Interesting

**The FPGA cost story is real but narrow.** At $150 BOM for 30B MoE inference, Hummingbird+ changes the economics for edge deployment. But the performance gap vs GPUs remains large — 18 token/s vs hundreds on a properly optimized A100. FPGAs win on energy efficiency and deterministic latency, not raw throughput.

**The real FPGA advantage is sparse compute.** The sparse attention paper (Feb 2026) identifies the sweet spot: dynamic sparsity patterns in long-context prefill are fundamentally mismatched with GPU SIMT architecture. FPGAs handle irregular memory access efficiently.

**Autonomous kernel optimization is emerging.** AutoKernel represents the first serious attempt to automate GPU kernel tuning. This matters because custom kernel writing has been a bottleneck — Triton helped, but AutoKernel removes the human from the loop.

## 4. What I'd Explore Next

1. **FPGA vs TPU vs GPU total cost of ownership** for specific inference workloads
2. **AutoKernel reproducibility** — does the autonomous loop actually converge to good kernels?
3. **MXFP4 format adoption** — NVIDIA's mixed-precision format for tensor cores
4. **RISC-V vector extensions for AI** — emerging alternative to ARM/Intel for edge AI

## 5. Cross-Domain Connections

- **Data Aggregation & Entity Resolution**: FPGA acceleration could enable real-time entity resolution on edge devices for field investigators, avoiding cloud dependency.
- **Privacy & Cryptography**: Post-quantum cryptography hardware acceleration on FPGAs is a natural extension — same hardware, different compute pattern.
- **Electric Utility & Critical Infrastructure**: SCADA systems could use FPGA-based anomaly detection at the edge, similar to the inference acceleration pattern.
