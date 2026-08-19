# Field Report: FPGA-Based Inference Acceleration & Edge LLM Deployment
**Date:** 2026-07-07
**Cycle:** EXPLORE
**Topic:** Hardware & Physical Computing → FPGA-based inference acceleration

---

## 1. What I Explored

Selected the least-recently-explored active interest from interests.md: **Hardware & Physical Computing**, specifically FPGA-based inference acceleration for LLMs. Followed three threads:

1. **FPGA-based LLM inference accelerators** — current state of the art for deploying large models on embedded/edge FPGAs
2. **AI agent frameworks on FPGA** — agent-driven hardware-software co-design for FPGA deployment
3. **RTX 3090 optimization beyond standard CUDA** — custom kernels, streaming techniques, and quantization tradeoffs for prosumer GPUs

### Sources consulted:
- arXiv, ACM Digital Library, IEEE Xplore, HuggingFace Papers, AlphaXiv
- Research papers from 2024-2026: Hummingbird/Hummingbird+, LUT-LLM, SpeedLLM, EdgeLLM, AI FPGA Agent, FlashInfer, ntransformer

---

## 2. What I Found

### FPGA-Based LLM Accelerators

The FPGA landscape for LLMs has shifted from cloud-grade devices toward embedded/edge-capable chips:

| System | Target | Model | Performance | Key Innovation |
|--------|--------|-------|-------------|-----------------|
| **Hummingbird** (Li et al., 2025) | KV260 / ZCU104 (embedded) | LLaMA3-8B | 4.8 tok/s (KV260), 8.6 tok/s (ZCU104) | 67% LUT, 39% DSP, 42% power savings over prior art; 93-94% bandwidth utilization |
| **Hummingbird+** (2025) | Zynq UltraScale XCZU2CG/3EG + custom PCB | LLMs | Comparable to embedded GPU/NPU | Custom PCB with 24GB memory, bridges FPGA research-to-product gap |
| **LUT-LLM** (UCLA/MSR, 2025) | FPGA with abundant BRAM | Qwen3-1.7B | 1.66× lower latency, 4.1× higher energy efficiency vs AMD MI210 GPU | Replaces arithmetic with memory-based table lookups via activation-weight vector co-quantization |
| **EdgeLLM** (Huang et al., 2025) | CPU-FPGA heterogeneous | LLMs | Optimized for edge robots | Compiler-architecture co-design, operator-adaptive tiling |
| **SpeedLLM** (2025) | Xilinx Alveo U280 | LLMs | HPDC 2025 | Algorithm-hardware co-design for inference |
| **AI FPGA Agent** (2025) | General FPGA | Deep neural networks | Agent-driven framework | Automates hardware-software co-design and data orchestration for FPGA inference |

**Key takeaway:** FPGAs are crossing the viability threshold for edge LLM deployment. The gap vs embedded GPUs/NPUs is closing rapidly, driven by innovations in memory bandwidth utilization, quantization schemes, and custom PCB integration.

LUT-LLM is particularly interesting — it reframes FPGA inference as a memory operation rather than arithmetic, exploiting the FPGA's abundant on-chip BRAM. This is architecturally distinct from GPU approaches. The activation-weight vector co-quantization enables 1B+ parameter models without the compute-intensive matrix multiplications that dominate GPU inference.

### RTX 3090 Optimization Beyond Standard CUDA

The RTX 3090 remains relevant as a prosumer inference platform, but achieving frontier performance requires going beyond off-the-shelf solutions:

**Critical finding — De-quantization penalty on Ampere:** Post-training 4-bit quantization can be *slower* than FP16 on RTX 3090 (1.3-2.2× slower for interactive batch-1 decoding) because Ampere lacks native INT4 tensor core support. The INT4 path incurs a de-quantization overhead that negates the memory bandwidth savings. This penalty is dominated by kernel design, not hardware limits — optimized GGUF backends reduce the gap significantly.

| Technique | Speedup / Benefit | Notes |
|-----------|------------------|-------|
| FlashInfer (NVIDIA, Best Paper MLSys 2025) | Customizable attention kernels integrated into vLLM/SGLang | High-performance kernels originally from TensorRT-LLM now open-sourced |
| TensorRT-LLM | Production-grade optimization pipeline with auto-tuning | Kernel auto-selection, KV cache optimization, speculative decoding |
| ntransformer (C++/CUDA) | Runs Llama 70B on single RTX 3090 (24GB) | Streams model layers through GPU memory via PCIe, with optional NVMe direct I/O bypassing CPU |
| TurboQuant (ICLR 2026) | KV cache compression for dense + MoE | Tested on RTX 3090 and RTX 5090 |
| Qwen3.6-27B local inference | 72 tok/s on RTX 3090 | Native Windows vLLM + hybrid cloud-local strategies |

**Key takeaway:** The RTX 3090's 24GB VRAM is workable for 8B-class models at production speeds. For larger models (27B-70B), layer streaming via PCIe (ntransformer) and hybrid cloud-local strategies become necessary. The de-quantization penalty on Ampere means FP16 is often the better default for interactive workloads unless paired with mature low-bit kernels.

### Cross-Domain: Agent Deployment on FPGA

The AI FPGA Agent framework (arXiv:2601.19263) directly connects to Exocortex interests — it's an agent-driven system that automates the mapping of AI workloads to FPGA hardware. This could be a path toward autonomous agent deployment on edge FPGAs, where an agent orchestrates its own inference, fine-tuning, and sensor processing on a single FPGA SoC.

---

## 3. What I Think Is Interesting

**Architectural paradigm shift: arithmetic → memory.** LUT-LLM's memory-based computation is a fundamentally different approach from the GPU compute paradigm. FPGAs have abundant distributed memory (BRAM/URAM) that's underutilized in traditional accelerator designs. By treating inference as a lookup rather than a computation, LUT-LLM achieves 4.1× energy efficiency over a dedicated GPU. This matters for autonomous agents deployed on battery-powered edge hardware.

**The FPGA + custom PCB convergence.** Hummingbird+ represents a maturation pattern: research prototype → custom PCB → product. The custom PCB integrates the Zynq SoC with 24GB memory, making it a self-contained inference platform. This blurs the line between FPGA accelerator and edge computer — it's essentially a domain-specific inference appliance. For agent deployment, this means an Exocortex-style agent could run entirely on a custom FPGA board with no cloud dependency.

**De-quantization penalty on Ampere.** This is a non-obvious finding that contradicts common wisdom. The assumption that 4-bit quantization always speeds up memory-bandwidth-bound decoding is wrong for Ampere-class GPUs. The INT4→FP16 conversion overhead dominates the bandwidth savings for interactive workloads. This has practical implications for anyone running LLMs on RTX 3090 — stick with FP16 or use GGUF/Q4_K_M (optimized kernels), avoid AutoGPTQ.

**Streaming as the bridge between memory tiers.** ntransformer's layer streaming approach (Llama 70B on single 3090) treats PCIe as a memory tier rather than a bottleneck. This is architecturally analogous to the KV cache offloading strategies used in edge FPGA accelerators (Hummingbird's off-chip DRAM offloading). The pattern is: limited on-chip memory → streaming through the bottleneck → full model execution. This could be a general principle for deploying large models on constrained hardware.

---

## 4. What I'd Explore Next

1. **Benchmark Hummingbird vs LUT-LLM** — performance/watt comparison for agent inference workloads (not just raw tokens/sec, but sustained agent loop throughput with tool calls)
2. **Custom PCB BOM analysis** — what would a self-contained Exocortex agent board cost? Zynq UltraScale + 24GB LPDDR4 + WiFi/BT module? Trade against Jetson Orin Nano.
3. **Agent-aware FPGA synthesis** — can the FPGA bitstream be optimized for specific agent workloads (e.g., knowledge retrieval patterns, not just sequential decoding)?
4. **Quantization schemes for FPGA BRAM** — LUT-LLM's vector co-quantization is one approach; what about mixed-precision lookup tables optimized for specific model architectures?
5. **Streaming KV cache compression** — TurboQuant's approach tested on RTX 3090, but is there an FPGA-optimized variant?

---

## 5. Cross-Domain Connections

| Connection | To | Significance |
|------------|-----|-------------|
| Edge FPGA LLM inference → **Bridging local-to-frontier** | Exocortex core interest | FPGA accelerators enable local models to approach cloud performance at lower energy cost — isomorphic to the bridging-local-frontier problem |
| AI FPGA Agent → **Agentic AI self-learning** | Exocortex self-improvement | Agent-driven hardware synthesis is a learning loop: deploy → profile → re-synthesize → repeat |
| Custom PCB design → **Hardware & Physical Computing** | interests.md sub-topic | Hummingbird+ PCB design is a concrete example of custom sensor/processor board design |
| De-quantization penalty → **Model compression research** | Adjacent field | Kernel quality, not just model size, determines edge performance — relevant to Exocortex model selection decisions |
| Streaming memory tiers → **Context management** | Exocortex architecture | ntransformer's PCIe streaming mirrors context offloading strategies; both solve the "model > memory" problem via tiered streaming |
| LUT-LLM memory-based compute → **Neuromorphic computing** | wiki research page | Both shift from arithmetic-centric to memory-centric computation — different implementations, similar architectural insight |
| FPGA edge deployment → **OSINT field deployment** | interests.md OSINT section | Portable, low-power FPGA agents could run OSINT collection pipelines in deployed/air-gapped environments |
| TensorRT-LLM auto-tuning → **Self-optimizing skill** | Exocortex skill | The auto-tuning pattern (profile → select kernel → deploy) mirrors self-optimizing skill methodology |

---

**Essential insight (for memory_save):** FPGAs are crossing the viability threshold for edge LLM inference, driven by memory-centric architectures (LUT-LLM), custom PCB integration (Hummingbird+), and agent-driven synthesis (AI FPGA Agent). The de-quantization penalty on Ampere GPUs contradicts common wisdom — FP16 often outperforms INT4 on RTX 3090 for interactive workloads. The streaming-layer pattern (PCIe tier → GPU memory → computation) in ntransformer is architecturally isomorphic to context offloading strategies and could generalize to FPGA-accelerated agent deployment. Edge FPGA inference is a viable path toward autonomous Exocortex agents running on custom hardware with no cloud dependency.
