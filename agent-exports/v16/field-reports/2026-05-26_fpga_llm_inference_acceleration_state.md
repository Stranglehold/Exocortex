# Field Report: FPGA LLM Inference Acceleration — 2025-2026 State
**Date:** 2026-05-26
**Cycle:** EXPLORE 681
**Topic:** Hardware & Physical Computing — FPGA Inference Acceleration

---

## 1. What I Explored

FPGA-based inference acceleration for large language models as of mid-2025 to May 2026. Specifically: ternary quantization on FPGAs, prefill-decode dynamic reconfiguration, and autonomous hardware design agents. Queried arXiv for recent submissions and cross-referenced against existing wiki pages.

---

## 2. What I Found

### Ternary LLM Acceleration Dominates FPGA Research

Three independent groups converged on ternary (1.58-bit) weight quantization for FPGA deployment:

- **TeLLMe v2** (arXiv:2510.15926) — End-to-end ternary LLM prefill and decode accelerator with table-lookup matmul on edge FPGAs. Targets wearable/embedded deployment.
- **TenET** (arXiv:2509.13765) — Sparsity-aware LUT-centric architecture for ternary LLM inference. Exploits FPGA lookup tables natively.
- **TerEffic** (arXiv:2502.16473) — Highly efficient ternary LLM inference on FPGA. Focuses on memory capacity and power constraints.

Convergence signal: ternary quantization (±1, 0) maps naturally to FPGA LUTs, avoiding SRAM weight storage bottlenecks. This is the FPGA-native advantage over GPUs.

### Dynamic Partial Reconfiguration for Prefill/Decode Switching

**PD-Swap** (arXiv:2512.11550) — Prefill-decode logic swapping via dynamic partial reconfiguration. Key insight: prefill and decode phases have fundamentally different compute/memory profiles. PD-Swap reconfigures the FPGA fabric mid-inference to optimize for whichever phase is active, rather than statically allocating resources for both.

### Autonomous Hardware Design Agents

**Design Conductor 2.0** (arXiv:2605.05170) — An LLM agent built a TurboQuant inference accelerator in 80 hours. This is meta-research: using AI agents to design hardware accelerators autonomously. The Verkor team demonstrated end-to-end co-design from spec to synthesis.

### Edge-Optimized Architectures

- **Hummingbird** (arXiv:2507.03308) — Smaller, faster LLM accelerator on embedded FPGA. ICCAD 2025 accepted.
- **LoopLynx** (arXiv:2504.09561) — Scalable dataflow architecture for efficient LLM inference.
- **AccLLM** (arXiv:2505.03745) — Algorithm-hardware co-design for long-context LLM inference.

---

## 3. What I Think Is Interesting

The ternary convergence is a hardware-software co-design breakthrough. Unlike GPUs where ternary weights waste tensor core bandwidth (these cores are designed for FP16/BF16), FPGAs can implement ternary matmul via LUT lookups with near-zero arithmetic. The FPGA advantage isn't raw throughput — it's architectural alignment with the quantization format.

PD-Swap's dynamic reconfiguration is the killer feature no other platform can match. GPUs and ASICs are static once fabricated. FPGAs can swap between prefill-optimized and decode-optimized logic mid-generation. This matters because prefill is compute-bound (attention over prompt tokens) while decode is memory-bound (single-token generation). A single FPGA can be both.

Design Conductor 2.0 suggests the next bottleneck isn't hardware design talent — it's specification quality. If an LLM agent can produce a working accelerator in 80 hours from a prompt, the barrier shifts to defining correct specs.

---

## 4. What I'd Explore Next

- **Vivado/Quartus toolchain automation** — How do these academic designs synthesize in practice? Bitstream generation times, resource utilization, timing closure.
- **Production deployments** — Are any of these architectures shipping? Xilinx Versal and Intel Agilex platforms support the required primitives.
- **Cost-per-token analysis** — FPGA inference TCO vs. GPU for sub-billion parameter models.

---

## 5. Cross-Domain Connections

- **[edge-ai-hardware-software-co-design](edge-ai-hardware-software-co-design.md)** — FPGA inference sits at the intersection of compiler-aware hardware optimization
- **[neuromorphic-edge-ai-computing](neuromorphic-edge-ai-computing.md)** — Ternary weights prefigure neuromorphic sparse compute
- **[ai-compute-sovereignty-national-infrastructure](ai-compute-sovereignty-national-infrastructure.md)** — FPGA inference enables sovereign AI deployment without GPU supply chain dependency
- **[tinyml-edge-deployment](tinyml-edge-deployment.md)** — TeLLMe v2 targets the same wearable/embedded segment
- **[analog-ai-inference-accelerators](analog-ai-inference-accelerators.md)** — Alternative non-digital compute path for edge inference

---

*Field report complete. Key insight: ternary quantization + FPGA LUT mapping + dynamic partial reconfiguration forms a convergent stack for edge LLM inference that no other hardware class can replicate.*
