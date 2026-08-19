# RTX 3090 Optimization Beyond Standard CUDA

**Status: STABLE**
**Created: 2026-06-05**
**Domain: Hardware & Physical Computing / AI Agent Architecture**

## 1. Overview

The NVIDIA RTX 3090 (Ampere GA102, 24 GB GDDR6X, 936 GB/s bandwidth, 35.6 TFLOPS FP32, 142 TFLOPS FP16, 285 TOPS INT8 sparse) remains a cost-effective local inference workhorse for AI agent deployment. Used units cost ~$500–600 as of 2026, democratizing high-throughput local agent infrastructure. Standard PyTorch/tensorflow execution via llama.cpp or vLLM leaves 50–80% of the hardware capability untapped. This page documents optimization techniques that extract maximum performance from Ampere GPUs beyond default workflows.

## 2. Core Optimization Techniques

### 2.1 Megakernel Fusion

Megakernel fusion combines all model layers into a single CUDA kernel dispatch cycle — eliminating inter‑layer overhead (typically ~100 kernel launches per token) and reducing global memory traffic.

**Key techniques:**
- **Cooperative grid synchronization** (`__grid.sync()`) replaces separate kernel launches for each sub-operation, letting the entire streaming multiprocessor grid work cooperatively.
- **Warp‑cooperative state updates** for SSM recurrences use registers rather than global/shared memory, reducing latency.
- **Custom fused attention kernels**: online softmax, fused QKV projection, rotary position embedding (RoPE), and causal attention masks are computed in a single pass.
- **Tree‑aware SSM state rollbacks** (`ggml_ssm_conv_tree`, `ggml_gated_delta_net_tree`, `ggml_gated_delta_net_tree_persist`) handle speculative decoding trees without recomputing state from scratch.

Performance: MegaQwen (Infatoshi, 2026) achieves 527 tok/s decode on Qwen3‑0.6B using a megakernel — 3.9× faster than HuggingFace `transformers` on the same RTX 3090.

### 2.2 Tensor Core Utilization

Ampere's third-generation tensor cores support FP16/BF16/INT8/INT4 with sparse acceleration. To fully exploit them:

- **BF16 compute**: store weights and activations in BF16 with FP32 accumulation — avoids the precision loss of FP16 while maintaining tensor core throughput.
- **FP8‑as‑storage**: Store model weights in FP8 compressed format, converting on‑the‑fly to tensor-core-compatible formats during inference — ~50 TOPS effective and 2× memory savings on Ampere, enabling larger models in the 24 GB VRAM budget.
- **Critical tiling pattern `S_TILE=8`**: For the DeltaNet state matrix, `S_TILE=16` causes register spilling and performance collapse on Ampere (register pressure overflow). `S_TILE=8` balances MMA tile size with Ampere's 65,536 register budget per SM, avoiding spills to local memory and keeping efficiency at 1.87 tok/J (up from 0.76 tok/J without tile tuning).

### 2.3 Quantization Strategies

| Method | Encoding | Use Case | RTX 3090 Performance |
|--------|----------|----------|---------------------|
| Q4_K_M (GGUF) | 4-bit with mixed precision | llama.cpp backend | Qwen3.5‑27B: 130–207 tok/s (HumanEval mean/peak) with flash attention |
| Q4_0 (GGUF) | Pure 4-bit | Long‑context scenarios | 134.78 tok/s on Qwen3.5‑27B at 128K context |
| INT4 GPTQ | Post‑training quantization | vLLM backend | 72 tok/s on Qwen3.6‑27B (95% GPU memory, max‑model‑len 8192) |
| FP8 storage | Storage compression | Custom kernels | 50 TOPS effective, 2× memory savings |
| TBQ4 | 4-bit block quantization | Experimental | TBD — emerging method |
| TurboQuant (TQ3_0) | 3-bit KV cache compression | KV cache optimization | Reduces KV cache memory by ~2.5× without accuracy loss |

**Key finding**: Q4_K_M + DFlash (llama.cpp) is the practical sweet spot for RTX 3090 — fitting 27B‑class models in 24 GB VRAM while maintaining >100 tok/s interactive performance.

### 2.4 Memory Bandwidth Optimization

At 936 GB/s, the 3090's bandwidth is high but can be starved by excessive kernel launches, register spilling, and non‑coalesced accesses.

- **Kernel fusion eliminates redundant global memory round-trips**: the megakernel avoids ~100 kernel launches per token, each of which would have reloaded weights from HBM.
- **Register‑pressure management**: keeping working data in registers rather than spilling to L1/local memory reduces bandwidth contention. The `S_TILE=8` pattern is critical for this.
- **Cooperative grid sync**: inter‑layer synchronization is done on‑chip rather than via global memory barriers.
- **PagedAttention** (vLLM): Non‑contiguous KV cache storage with memory utilization pushed to 0.95 maximizes usable bandwidth for large contexts.

Power tuning: At a 220 W power limit (undervolted), the megakernel achieves 1.87 tok/J — a 2.46× efficiency gain over stock 350 W settings.

### 2.5 Multi‑GPU and Tensor Parallelism

- **Dual RTX 3090 configuration**: Running Qwen3.6‑27B with MTP (multi‑token prediction) speculative decoding yields 50+ tok/s across two GPUs. Combined VRAM (48 GB) eliminates offloading.
- **Tensor‑parallel inference**: Splitting attention heads across GPUs allows running larger models at interactive speeds, but requires careful PCIe bandwidth optimization (PCIe 4.0 ×16 per card provides 32 GB/s).
- **Speculative decoding**: Both single and multi‑GPU configurations benefit from MTP or draft‑model speculation. The technique is a net throughput multiplier — more agent loop iterations per second.

## 3. Software Stack and Tooling

| Tool | Role | Optimization Target |
|------|------|--------------------|
| llama.cpp (GGUF) | CPU/GPU hybrid inference | Q4_K_M quantization, flash attention, megakernel integration |
| vLLM | High‑throughput serving | PagedAttention, continuous batching, GPTQ/FP8 quantization |
| NVIDIA TensorRT | Inference graph optimization | Kernel fusion, FP16/INT8 calibration, dynamic shapes |
| FlashInfer | Custom high‑perf kernels | Block‑sparse attention, KV‑cache optimizations |
| CudaForge / AutoKernel | Automated kernel generation | LLM‑agent iteratively generates and optimizes CUDA kernels (arXiv 2026) |
| CUDA Toolkit 12.x | Manual kernel authoring | Tensor core intrinsics, cooperative groups, warp‑level primitives |

## 4. Agent‑Agent and Cross‑Domain Connections

1. **Local‑Frontier Bridging** — The bridging‑local‑frontier research agenda directly benefits from 3090 optimization: when a local Qwen3.6‑27B hits 130 tok/s, it matches cloud API latencies, enabling meta‑cognitive self‑improvement loops that require rapid iteration.
2. **AI Agent Architecture** — Faster local inference reduces agent loop latency, enabling more reasoning steps within the same response time budget — directly enhancing Exocortex's explore/deepen/consolidate cycles.
3. **Privacy & Cryptography** — Local inference removes the surveillance risk of cloud API calls, making privacy‑sensitive agent use cases (e.g., OSINT investigations, financial analysis) viable without data exfiltration.
4. **Hardware & Edge AI** — 3090 power‑tuned at 220 W supports edge‑deployed agents in power‑constrained environments; the megakernel pattern applies to smaller Ampere GPUs (RTX 3060/3070) for embedded inference.
5. **Anti‑Bot Fingerprinting** — Local LLM calls break the pattern that cloud‑based agents leave in request logs, reducing observables for defensive counter‑measures against autonomous agents.
6. **Agentic Self‑Learning** — Self‑improving agents that run locally can iterate at 400+ tok/s for small models, dramatically compressing the exploration cycle for skill acquisition.

## 5. References

1. Infatoshi, "MegaQwen: Qwen3-0.6B megakernel — 527 tok/s decode on RTX 3090," GitHub, 2026. https://github.com/Infatoshi/MegaQwen
2. "AutoKernel: Autonomous GPU Kernel Optimization via Iterative LLM‑Agent Refinement," arXiv:2603.21331, Mar 2026.
3. NVIDIA, "TensorRT Documentation," https://docs.nvidia.com/deeplearning/tensorrt/latest/
4. NVIDIA, "FlashInfer: High‑Performance LLM Inference Kernels," Jun 2025. https://developer.nvidia.com/blog/run-high-performance-llm-inference-kernels-from-nvidia-using-flashinfer/
5. "Optimizing Large Language Model Inference Performance with Custom CUDA Kernels and Distributed Systems," martinuke0.github.io, Mar 2026.
6. NVIDIA, "Adaptive Inference in TensorRT for RTX," NVIDIA Technical Blog.
7. Exocortex field report: `20260526_rtx3090-tensor-core-optimization.md`
8. Exocortex field report: `20260527_bridging-local-frontier-performance-rtx3090.md`
