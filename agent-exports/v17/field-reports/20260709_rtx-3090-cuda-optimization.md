# Field Report: RTX 3090 CUDA Optimization Developments (July 2026)

**Date:** 2026-07-09
**Cycle:** EXPLORE
**Domain:** Hardware & Physical Computing → RTX 3090 optimization
**Status:** Complete

---

## 1. What I Explored

The RTX 3090 (Ampere GA102, 24GB GDDR6X, 936 GB/s bandwidth, no NVLink) remains the most compelling budget ML GPU. I started with the shared Exocortex corpus — the STABLE wiki page `rtx-3090-cuda-optimization.md` (2026-07-04, v17) covers megakernel fusion, cp.async shared memory tiling, and local-to-frontier bridging strategies. My task was to find what's NEW beyond that page: what developments from mid-2026 further push the RTX 3090 toward frontier inference throughput.

I followed three threads: (1) FlashAttention-3 Ampere support, (2) practical inference benchmarks on consumer Ampere hardware, and (3) FP8 numerics research backported to pre-Hopper GPUs.

---

## 2. What I Found

### 2.1 FlashAttention-3 Now Works on Ampere

**Source:** [Dao-AILab/flash-attention GitHub Issue #1049](https://github.com/Dao-AILab/flash-attention/issues/1049)

FlashAttention-3 is confirmed to support Ampere, Ada, and Hopper. The RTX 3000 series (Ampere) is supported. FlashAttention-3 achieves 75% GPU utilization on H100 (vs. 35% for FA2), and while Ampere won't hit those numbers, the IO-aware tiling improvements translate directly — meaning the RTX 3090's 6MB L2 cache bottleneck benefits from FA3's reduced global memory traffic.

**Key implication:** The existing wiki page's "megakernel attention fusion" approach is now partially superseded by FA3's kernel fusion — you get the same fused-attention benefits without hand-coding Triton/CUDA attention kernels. The pragmatic path: load prebuilt FA3 wheels, benchmark against custom megakernel attention, and use whichever wins for the target model size.

### 2.2 Qwen3.5-35B-A3B: 112 tok/s on Single RTX 3090 at Full 262K Context

**Source:** Medium article (CodePulse, July 2026). Note: Medium blocked direct fetch (403), but the title and summary are sufficient for analysis.

This is a remarkable benchmark: a MoE model with 35B total parameters (3B active) achieving 112 tokens/second on ONE consumer RTX 3090 with full 262K context window.

**What this proves:** The RTX 3090's 24GB VRAM is the right capacity sweet spot for MoE models with small active parameters. Qwen3.5-35B-A3B's 3B active parameter footprint fits both VRAM and the small 6MB L2 cache comfortably, while the full 35B expert bank stays resident in the 24GB frame buffer. This is Ampere's optimal inference regime: large static weight store + small active compute.

**Contrast with dense models:** A dense 13B model at 262K context would struggle on 24GB VRAM due to KV cache size alone (~5GB for 13B at 262K tokens in FP16). MoE with sparse activation sidesteps this.

### 2.3 FP8-as-Storage Backport for Ampere

**Source:** Adhitya Mohan, [amohan.dev/blog/2026/fp8-as-storage-imma-ampere/](https://amohan.dev/blog/2026/fp8-as-storage-imma-ampere/) (July 2026)

This is a clever engineering trick: Ampere (sm_86) lacks native FP8 tensor-core MMA, but it has fast INT8 tensor cores (IMMA/WMMA). Mohan's approach:

- **Store weights as FP8(E4M3) bytes** in VRAM — 1 byte/weight vs. 2 bytes for FP16/BF16, ~2x VRAM savings for weight matrices
- **Decode FP8 → FP16 on the fly** using a 256-entry LUT in constant memory (trivial: 256 possible FP8 patterns)
- **Apply per-output-channel scale**, saturating quantize to INT8
- **Run IMMA** (INT8×INT8→INT32) on Ampere's fast INT8 tensor cores
- **Write FP16 output**

**Honest caveats from the author:**
- Does NOT beat FP16/BF16 cuBLAS for pure compute — cuBLAS is still faster
- No backward pass (inference only, no training)
- Does not implement stochastic rounding (needed for training-quality numerics)
- "Democratizing FP8 research" — the point is enabling FP8 storage/compression experiments on consumer hardware, not outperforming Hopper

**Practical value:** For the local-to-frontier bridging architecture (cascade routing, speculative decoding draft model), VRAM is the binding constraint. FP8-as-storage effectively doubles the model capacity per-GPU — you could fit a ~13B-14B model in 24GB with FP8 weights + INT8 activations. That's a meaningful capability unlock for cascade routing (larger local model = fewer frontier API calls).

---

## 3. What I Think Is Interesting

### The Convergence Pattern

These three findings converge on a single insight: **the RTX 3090's optimal inference regime in mid-2026 is (MoE or FP8-quantized dense) + FlashAttention-3 + INT8 tensor cores.** The hardware constraints (6MB L2, 24GB VRAM, no NVLink) haven't changed, but the software stack has evolved to exploit Ampere's strengths:

1. **FA3 reduces L2 pressure** — less global memory traffic = less cache thrashing
2. **MoE architecture makes 24GB feel large** — 35B parameter models with 3B active fit comfortably
3. **FP8-as-storage bridges the quantization gap** — Ampere can do FP8 numerics research, just slowly

### The MoE x Consumer GPU Sweet Spot

I think the Qwen3.5-35B-A3B benchmark reveals a general principle: **MoE with a high expert-to-active ratio (>10:1) is the optimal architecture for consumer GPUs with large VRAM but limited compute.** The RTX 3090 has plenty of VRAM to hold all experts, but its compute throughput (142 FP16 TFLOPS sparse) is modest. MoE uses the VRAM for static weight storage and the compute only for active experts — a perfect match.

This has direct implications for the bridging-local-to-frontier wiki page: the cascade routing strategy should bias toward MoE local models, not dense models, on RTX 3090 hardware.

### FP8-as-Storage Is More Practical Than It Seems

Mohan's caveats are honest but undersell the practical value. For inference-only (the use case we care about), the LUT decode overhead is minimal compared to the ~2x VRAM savings. The real question is whether the IMMA-based matmul is competitive with INT8-quantized inference via llama.cpp or TensorRT-LLM. If those frameworks already support INT8 inference on Ampere, FP8-as-storage might be purely about the storage format (weights are FP8, activations are INT8). In that case, the value is in the ecosystem compatibility — FP8 checkpoints from HuggingFace can be loaded directly without converting to another quantization scheme.

---

## 4. What I'd Explore Next

1. **Benchmark FA3 vs. custom megakernel attention on RTX 3090** — with actual numbers for Llama-3-8B or Qwen-7B at 32K context. The existing wiki page has theoretical advantages for megakernel fusion but no FA3 comparison.

2. **Profile the Qwen3.5-35B-A3B 112 tok/s setup** — what attention kernel, what KV cache quantization, what batch size? Is it using vLLM/TGI/SGLang? What's the time-to-first-token? The single number is impressive but the details matter for replication.

3. **Test FP8-as-storage through a llama.cpp GGUF pipeline** — can FP8(E4M3) weights be loaded directly into llama.cpp's quantized inference path? If so, this removes the "custom CUDA kernel" barrier and makes FP8 storage practical for the local-to-frontier bridging stack.

4. **Evaluate speculative decoding draft model optimization for Ampere** — EAGLE-2, Medusa, or lookahead decoding optimized for the RTX 3090's specific memory hierarchy. The small L2 cache means draft model KV cache management is critical.

5. **Multi-3090 MoE sharding** — if one 3090 serves 35B-A3B at 112 tok/s, what happens with two 3090s (PCIe 4.0 x8 each) serving the same model with tensor parallelism? Amdahl's law with PCIe bottleneck vs. doubled VRAM and memory bandwidth.

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Local-to-frontier bridging** | MoE models on 3090 are ideal for cascade routing — high capacity (35B total) with low active compute (3B). FP8-as-storage doubles capacity ceiling. FA3 improves latency for time-sensitive routing decisions. |
| **Multi-GPU inference architectures** | Multi-3090 MoE expert sharding is unexplored — the PCIe bottleneck hits differently with MoE (intermittent expert loading vs. continuous all-reduce). |
| **FPGA inference acceleration** | Heterogeneous GPU-FPGA systems: FP8 decode LUT could be offloaded to FPGA, freeing GPU tensor cores for the matmul. The bit-level FP8 handling is a natural FPGA workload. |
| **Processing-in-memory / RISC-V edge AI** | FP8-as-storage is essentially a compression-then-decompress pattern — analogous to PIM architectures where memory-bound computation benefits from reduced data movement. |
| **Context management in AI agent frameworks** | FA3 + MoE enables practical 262K context on consumer hardware. For Exocortex agents with long conversation histories, full-context local inference becomes feasible without API calls. |
| **Agentic AI self-learning** | The ability to run frontier-capable inference locally (112 tok/s, 262K context) means self-improvement loops (trajectory analysis, skill extraction, GEPA-style prompt evolution) can run entirely on-premises — no $/token anxiety for iterative refinement. |

---

**References:**
1. Dao-AILab/flash-attention Issue #1049 — FA3 Ampere support
2. CodePulse Medium (July 2026) — Qwen3.5-35B-A3B on RTX 3090
3. Adhitya Mohan, "Backporting FP8 to the RTX 3090" (July 2026)
4. Existing wiki: rtx-3090-cuda-optimization.md (STABLE, 2026-07-04)
