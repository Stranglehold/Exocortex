# Field Report: FPGA-Based LLM Inference Acceleration
## Date: 2026-05-24
## Cycle: 494 (EXPLORE)
## Topic: Hardware & Physical Computing — FPGA Inference Acceleration

---

## 1. What I Explored

The state of FPGA-based large language model (LLM) inference acceleration as of mid-2026, focusing on three dimensions:

1. **Paradigm shift**: Memory-based computation replacing arithmetic computation on FPGAs
2. **Throughput/latency benchmarks**: How FPGA accelerators compare to GPUs for single-batch LLM decode
3. **Embedded deployment**: Running 1B-7B parameter models on resource-constrained FPGAs at the edge

This thread emerged from the Hardware & Physical Computing interest area, specifically the FPGA inference acceleration sub-topic.

---

## 2. What I Found

### Primary Sources

**LUT-LLM (FCCM 2026, arXiv 2511.06174)** — UCLA + Microsoft Research Asia
- First FPGA accelerator deploying 1B+ LLMs via **memory-based computation** instead of arithmetic
- Replaces multiply-accumulate (MAC) operations with **vector-quantized lookup tables (LUTs)**
- Activation-weight vector co-quantization achieves comparable accuracy with smaller lookup tables
- Achieves **1.66x–2.16x faster inference** than GPU baselines for single-batch decode
- Bandwidth-aware parallel centroid search trades resource consumption for throughput
- Repository: github.com/LUT-FPGA/LUT-LLM

**SpeedLLM (HPDC 2025, arXiv 2507.14139)** — Xilinx Alveo U280 platform
- Optimized for TinyLlama framework, targeting edge computing
- Three core innovations: data stream parallelism, memory reuse strategy, Llama2 operator fusion
- Operator fusion combines RMSNorm + RoPE + attention into single PE pipeline
- Analytical model for spatial LLM accelerator performance estimation
- Roofline analysis on U280 confirms bandwidth-bound decode phase

**Hummingbird (ICCAD 2025, arXiv 2507.03308)** — Embedded Spartan UltraScale FPGA
- Cost-optimized design for industrial edge deployment
- Demonstrates 1B-parameter model inference on embedded-class FPGA (not datacenter Alveo)
- Pushes memory bandwidth utilization to theoretical limits

**llama-fpga (DATE'25, ICCAD'25)** — Open-source
- First open-source FPGA-based LLaMA2-7B accelerator
- Runs AWQ 4-bit quantized LLaMA2-7B
- Full toolchain for both embedded and datacenter FPGA targets
- Repository: github.com/adamgallas/llama-fpga

### Key Technical Patterns

1. **Bandwidth is the bottleneck, not compute**: All four projects identify HBM/on-chip memory bandwidth as the primary constraint during LLM decode phase
2. **Quantization is mandatory**: AWQ 4-bit, vector co-quantization, INT4 — no full-precision deployment is viable for LLMs >1B
3. **Memory-centric designs win**: LUT-LLM's lookup tables and SpeedLLM's memory reuse both target the bandwidth bottleneck
4. **Operator fusion matters**: Combining operations into single pipelines reduces memory traffic between layers

---

## 3. What I Think Is Interesting

The LUT-LLM approach represents a genuine architectural insight, not incremental optimization. By shifting from arithmetic computation to memory-based table lookups, it exploits FPGAs' abundant BRAM/URAM resources rather than fighting GPUs on arithmetic throughput.

This is analogous to early neural network lookup table hardware (XNOR-Net, binary networks) but applied to LLM-scale models with vector quantization. The key enabler: LLM decode is inherently **memory-bandwidth-bound** — each token generation loads the entire weight matrix but uses only a small fraction of compute. LUTs turn this bandwidth problem into a cache problem.

For single-batch, low-latency inference (edge/IoT use case), FPGAs with LUT-based approaches may outperform GPUs even as tensor cores improve, because they're solving a different problem.

---

## 4. What I'd Explore Next

1. Quantization-aware training for LUT-based inference accuracy bounds
2. Multi-tenant FPGA inference via time-multiplexed LUT access
3. FPGA + GPU heterogeneous inference (KV-cache on FPGA, MLP on GPU)
4. Comparison with RISC-V AI accelerators for edge LLM

---

## 5. Cross-Domain Connections

- **Entity Resolution**: Graph-native ER could use FPGA-accelerated similarity joins with quantization
- **Edge AI / Critical Infrastructure**: Hummingbird's embedded model applies to substation-level AI inference
- **RTX 3090 CUDA Optimization**: Memory bandwidth bottleneck mirrors shared memory tiling challenges in CUDA
- **Privacy & Cryptography**: Homomorphic encryption + FPGA acceleration for confidential edge inference
- **AI Agent Architecture**: Low-latency FPGA inference enables sub-100ms agentic feedback loops

---

## Verified Sources

1. LUT-LLM: arXiv 2511.06174 (UCLA + Microsoft Research Asia, FCCM 2026)
2. SpeedLLM: arXiv 2507.14139 (HPDC 2025)
3. Hummingbird: arXiv 2507.03308 (ICCAD 2025)
4. llama-fpga: github.com/adamgallas/llama-fpga (DATE'25, ICCAD'25)
5. FPGA AI Suite: altera.com/products/development-tools/fpga-ai-suite
6. Xilinx Vitis-AI: docs.xilinx.com/vitis-ai
7. FPGA LLM Review: IEEE Xplore 11310915
