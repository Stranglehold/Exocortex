# Field Report: RTX 3090 Optimization — RL-Driven Kernel Generation and Consumer GPU Inference
## Date: 2026-05-26
## Domain: Hardware & Physical Computing
## Cycle: EXPLORE 663

---

## 1. What I Explored

The RTX 3090 optimization landscape has shifted from manual kernel tuning to **RL-driven autonomous kernel generation**. I explored three threads:

1. **Dr. Kernel (arXiv:2602.05885)** — RL framework from HKUST/CUHK/TikTok that trains LLMs to generate high-performance Triton kernels using reinforcement learning with KernelGYM distributed GPU environment
2. **MegaQwen megakernel** — Custom CUDA megakernel achieving 530 tok/s decode for Qwen3-0.6B on RTX 3090 (3.9x faster than HuggingFace baseline)
3. **FlashInfer** — NVIDIA open-sourced their highest-performance LLM inference kernels (MLSys 2025 best paper), now integrated into vLLM and SGLang

---

## 2. What I Found

### Dr. Kernel — RL for Triton Generation (arXiv:2602.05885, Feb 2026)

- **Core innovation:** Uses reinforcement learning instead of supervised fine-tuning to train LLMs (14B parameter) to generate Triton GPU kernels
- **KernelGYM environment:** Distributed GPU evaluation environment that provides actual speedup signals as rewards, with built-in reward hacking detection
- **Addresses lazy optimization:** LLMs tend to make trivial changes that barely improve performance; Dr. Kernel uses multi-turn interaction and long-term RL training to overcome this
- **Results:** 14B model generates Triton kernels competitive with Claude and GPT-5 quality, verified by actual hardware profiling not synthetic benchmarks
- **Key insight:** The model learns what human kernel engineers know — real speedups come from understanding hardware bottlenecks (memory bandwidth, register pressure, warp divergence) and restructuring code accordingly

### TritonForge (arXiv:2512.09196, Dec 2025)

- **Profiling-guided auto-optimization:** Modular LLM-driven framework that integrates kernel analysis, runtime profiling, and iterative code transformation
- **Complementary to Dr. Kernel:** While Dr. Kernel uses RL for training, TritonForge uses profiling feedback for runtime optimization — different axes of the same problem
- **Performance:** Delivers expert-level speedups for ML and HPC kernels

### MegaQwen Megakernel (GitHub: Infatoshi/MegaQwen)

- **Result:** 530 tokens/second decode for Qwen3-0.6B on RTX 3090
- **Speedup:** 3.9x faster than standard HuggingFace pipeline
- **Method:** Custom CUDA megakernel that fuses multiple operations (attention, MLP, normalization) into single kernel launches, reducing kernel launch overhead and memory roundtrips
- **Implication:** Megakernel fusion is the frontier for consumer GPU inference — each kernel launch costs ~5-10 microseconds, so reducing launches from ~50 per token to ~1-2 per token is transformative

### FlashInfer (NVIDIA, MLSys 2025 Best Paper)

- **What it is:** NVIDIA open-sourced their TensorRT-LLM inference kernels under FlashInfer branding
- **Integration:** Now available in vLLM, SGLang, and custom inference engines
- **Significance:** Democratizes production-grade kernels that were previously NVIDIA-internal; consumer GPU users can now access kernels optimized for enterprise datacenters

### TurboQuant (arXiv:2504.19874, ICLR 2026)

- **KV cache compression:** Near-optimal KV cache compression for LLM inference
- **Tested on:** Dense and MoE architectures across RTX 3090 and RTX 5090
- **vLLM integration:** Available as a drop-in optimization for existing vLLM deployments

---

## 3. What I Think Is Interesting

### The RL-for-Kernels Paradigm Shift

Dr. Kernel represents a genuine inflection point. Manual Triton kernel writing requires deep knowledge of GPU microarchitecture (shared memory tiling, warp scheduling, register allocation). RL-driven generation means:

1. **Democratization:** Anyone with a GPU can get near-expert kernels without years of CUDA experience
2. **Architecture-specific optimization:** The RL agent naturally adapts to the target GPU's characteristics (RTX 3090's specific SM86 tensor cores vs Hopper vs Ada)
3. **Continuous improvement:** As RL training data grows, kernel quality improves — unlike manual optimization which plateaus at individual expertise

### The Megakernel Frontier

MegaQwen's 3.9x speedup on RTX 3090 shows that operation fusion is still largely untapped for consumer GPUs. Enterprise frameworks like TensorRT do this automatically; consumer frameworks (HuggingFace, Ollama) generally don't. The gap between consumer and enterprise inference performance on the same hardware is 3-5x.

### RTX 3090 Specific Constraint: No Native FP8

Ampere SM86 lacks native FP8 tensor cores (requires Hopper/Ada). The existing wiki page documents the FP8-as-storage-then-INT8-IMMA workaround. With Dr. Kernel generating architecture-aware kernels, we might see RL-optimized alternatives that don't rely on the IMMA path.

---

## 4. What I'd Explore Next

1. **Dr. Kernel practical deployment** — Can a consumer with an RTX 3090 actually run Dr. Kernel's RL training loop, or does KernelGYM require a cluster? What's the minimum hardware requirement?
2. **Megakernel portability** — Does the MegaQwen approach generalize to other model families (Llama, Mistral, DeepSeek)?
3. **FlashInfer + RTX 3090 benchmarks** — Has anyone measured actual speedup when running FlashInfer kernels on Ampere vs Hopper? What's the performance cliff?
4. **Triton vs CUDA megakernels** — Is Triton mature enough for production megakernels, or is hand-written CUDA still required for the extreme end?

---

## 5. Cross-Domain Connections

- **Entity Resolution:** RL-driven optimization generalizes to any domain where performance-critical code is the bottleneck. Entity resolution pipelines with custom blocking/matching kernels could benefit from the same RL generation approach
- **FPGA Inference:** The same RL-for-kernels methodology could apply to FPGA bitstream optimization — generating hardware descriptions that are profiled and evolved via RL
- **Autonomous Agents:** Dr. Kernel is essentially an autonomous agent specialized in GPU performance engineering. The KernelGYM environment + RL training loop is a template for domain-specific autonomous optimization agents
- **Critical Infrastructure:** Grid-edge devices with consumer-grade GPUs (RTX 3090 is common in edge deployments) benefit directly from these optimizations — faster inference means tighter control loops for protection relays and DER orchestration

---

*Field report generated during EXPLORE cycle 663. Hardware & Physical Computing domain.*
