# Field Report: RTX 3090 CUDA Kernel Optimization
## 20260704
## Cycle Type: EXPLORE | Interest: Hardware & Physical Computing

---

## 1. What I Explored

RTX 3090 optimization beyond standard CUDA — tensor core utilization, custom CUDA kernels,
and megakernel patterns for LLM inference acceleration. The RTX 3090 (Ampere GA102,
10,496 CUDA cores, 24GB GDDR6X, 936 GB/s bandwidth) remains compelling for budget
ML workstations due to its 24GB VRAM at accessible used prices. However, extracting
maximum performance requires deep architectural understanding that goes beyond
typical PyTorch-level tuning.

## 2. What I Found

### MegaQwen: Custom CUDA Megakernel (527 tok/s on RTX 3090)
The MegaQwen project (github.com/Infatoshi/MegaQwen) achieves 531 tok/s decode on
RTX 3090 — 3.9x faster than HuggingFace, 1.5x faster than TensorRT-LLM. This is
done via a **megakernel** that fuses an entire transformer block (RMSNorm, QKV
projection, RoPE, attention, O projection, MLP) into a single CUDA kernel launch.

**Key architectural findings:**
- The kernel is **sync-bound**, not memory-bandwidth-bound: only 5% memory bandwidth
  utilized (47 GB/s effective vs 936 GB/s peak)
- 140+ grid.sync() calls per token at ~0.7us each = ~100us synchronization overhead
- ~530 tok/s is the **architectural ceiling** for batch=1 bf16 cooperative
  megakernels on RTX 3090
- Static shapes enable massive optimization (compile-time constants for hidden size,
  head count, MLP width) — something production frameworks can't exploit

**What worked:** Block divergence + L2 prefetch (+2x), 128-bit vectorized loads (+3.5%)
**What didn't:** Warp producer/consumer split (0%), shared memory caching (0% —
  L1/L2 already effective), cp.async double-buffering (+1% — can't overlap enough compute)

### RTX 3090 Optimization Landscape

| Technique | Impact | Notes |
|-----------|--------|-------|
| TF32 on Tensor Cores | 2-3x over FP32 | `torch.backends.cuda.matmul.allow_tf32 = True` |
| FP16 mixed precision | 2-4x | Best for training; inference needs bf16 on Ampere |
| Memory coalescing | Critical | Small 6MB L2 cache makes access pattern crucial |
| CUDA streams/overlap | 10-30% | Overlap compute with data transfer |
| Megakernel fusion | 3-4x | Eliminates kernel launch overhead, intermediate writes |
| __ldg() texture cache | ~2x | Read-only cache path for weights — production frameworks can't assume |
| Flash Attention | 2-10x | Reduces O(n²) memory; Dao-AILab implementation |

### AutoKernel: Autonomous Kernel Optimization (arXiv:2603.21331)
AutoKernel uses an autonomous agent loop to optimize GPU kernels for arbitrary
PyTorch models. A single matrix multiplication kernel targeting tensor core hardware
may require weeks of expert tuning — AutoKernel automates tiling strategies, memory
layouts, and precision configuration search. This represents convergence between
agentic AI and hardware optimization.

### RTX 3090 vs Alternatives
| GPU | VRAM | FP16 TFLOPS | FP8 | NVLink |
|-----|------|-------------|-----|--------|
| RTX 3090 | 24GB | 71.2 | No | Yes |
| RTX 4090 | 24GB | ~165 | Yes | No |
| RTX 4080 | 16GB | ~105 | Yes | No |
| A100 | 40/80GB | 312 | Yes | Yes |

The 3090's NVLink support is unique among consumer GPUs, enabling 112.5 GB/s
GPU-to-GPU bandwidth for dual-card setups.

## 3. What I Think Is Interesting

The MegaQwen finding that inference on RTX 3090 is **sync-bound, not memory-bandwidth-bound**
is profound. Conventional wisdom says GPU kernels are memory-bandwidth-bound — optimize
for coalescing, use shared memory, reduce global memory traffic. But the megakernel
approach inverts this: by fusing everything into one kernel, you eliminate intermediate
memory traffic entirely, and the bottleneck shifts to synchronization primitives.

This has implications for Exocortex's local inference architecture:
- For batch=1 inference (the common interactive use case), the megakernel pattern
  could be applied to any transformer model with static shapes
- The 5% bandwidth utilization means there's enormous headroom for multi-stream
  or batched processing — the bottleneck is architectural, not hardware
- Autonomous kernel optimization (AutoKernel pattern) could be integrated into
  Exocortex's self-improvement loop — the agent tunes its own inference kernels

## 4. What I'd Explore Next

1. **Apply megakernel pattern to Qwen3-27B** — the local model Jake is interested in.
   Can the same cooperative groups + __ldg() approach scale to larger models?
2. **Flash Attention 3 integration** — Hopper-specific, but Flash Attention 2 works
   on Ampere and can dramatically improve long-context inference
3. **AutoKernel integration** — Can an autonomous agent loop tune Exocortex's
   inference kernels overnight?
4. **Dual RTX 3090 NVLink configuration** — Tensor parallelism across two 3090s
   with custom kernels for models that exceed 24GB
5. **Triton-based custom kernels** — OpenAI's Triton language for writing GPU kernels
   in Python, potentially more maintainable than raw CUDA

## 5. Cross-Domain Connections

- **AI Agent Architecture**: Autonomous kernel optimization (AutoKernel) is itself
  an agentic pattern — agents that improve their own runtime performance
- **Local-to-Frontier Bridging**: Custom kernels are a key lever for closing the
  gap between local (RTX 3090) and frontier (datacenter GPU) inference performance
- **Entity Resolution**: Graph operations (Fellegi-Sunter matching, community
  detection) could benefit from custom CUDA kernels for sparse matrix operations
- **Privacy**: Local inference on consumer hardware is the foundation for
  privacy-preserving AI — no data leaves the machine
- **OSINT**: Faster local inference means more sophisticated analysis pipelines
  (multi-source entity resolution, NLP over scraped data) can run on-prem

---

## References
- MegaQwen: https://github.com/Infatoshi/MegaQwen
- RTX 3090 CUDA Guide: https://www.rightnowai.co/guides/gpu-comparison/rtx-3090
- AutoKernel: arXiv:2603.21331
- Flash Attention: https://github.com/Dao-AILab/flash-attention
- NVIDIA TensorRT-LLM: https://github.com/NVIDIA/TensorRT-LLM
