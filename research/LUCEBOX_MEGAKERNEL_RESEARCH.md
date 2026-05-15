# Lucebox: Hand-Tuned LLM Inference Per GPU Architecture
## Source: Luce-Org (2026)
## Repo: github.com/Luce-Org/lucebox-hub
## Added to ledger: May 9, 2026 by Opus
## Priority: HIGH WATCH — frontier inference optimization for Qwen hybrid architecture

---

## Core Idea

Lucebox rewrites LLM inference from scratch for specific GPU chips and model architectures. Instead of optimizing within a general-purpose framework (llama.cpp, vLLM), they write custom CUDA kernels that fuse entire layer stacks into single GPU dispatches, eliminating the CPU scheduling overhead that general frameworks incur.

Two projects currently:

### 1. Megakernel
All 24 DeltaNet layers of Qwen 3.5 in a single CUDA dispatch. 82 blocks, 512 threads, one persistent kernel. No CPU round-trips between layers.

llama.cpp launches ~100 separate kernel dispatches per token (one per layer, plus attention, FFN, etc.). Each dispatch requires CPU scheduling. The megakernel eliminates all of that — the GPU executes the full DeltaNet stack in one cooperative grid sync.

**Benchmarks (Qwen 3.5-0.8B, 2020-era GPU):**

| Method | Prefill pp520 | Decode tg128 | tok/J | Power |
|--------|-------------|-------------|-------|-------|
| Megakernel | 37,800 tok/s | 413 tok/s | 1.87 | 220W |
| llama.cpp BF16 | 11,247 tok/s | 267 tok/s | 0.76 | 350W |
| PyTorch HF | 7,578 tok/s | 108 tok/s | N/A | N/A |

- 3.4x faster prefill than llama.cpp
- 1.5x faster decode than llama.cpp
- 2.5x more energy efficient (tok/J)
- Matches Apple's latest silicon at 2x throughput
- Power ceiling hit before compute ceiling — every watt fully utilized

**How it works:** Weights streamed directly from HuggingFace format (no GGUF conversion). Cooperative grid sync replaces kernel launch scheduling. The persistent kernel keeps all 82 blocks alive for the entire forward pass — no teardown/relaunch between layers. DVFS converts tight execution into saved watts.

### 2. DFlash
Custom flash attention implementation for the full-attention layers in Qwen's hybrid architecture. Handles the 8/32 layers that use standard attention with KV cache, while the megakernel handles the 24/32 DeltaNet layers. Together they optimize both halves of the hybrid architecture separately — correct approach since the two layer types have fundamentally different compute patterns.

---

## Relevance to Exocortex

### Why This Matters

Lucebox represents the performance ceiling for Qwen3.5 inference on NVIDIA GPUs. Everything else we've evaluated — llama.cpp, TurboQuant, MTP, power tuning — operates within the constraints of a general-purpose inference engine. Lucebox removes those constraints entirely.

The 2.5x efficiency gap between Lucebox and llama.cpp is the cost of generality. llama.cpp supports dozens of model architectures, multiple GPU vendors, CPU fallback, quantization formats, and a full OpenAI-compatible API. That generality requires ~100 kernel launches per token where Lucebox uses one.

### Current Limitations

- **Only 0.8B model tested.** Scaling the megakernel to 27B is a different engineering challenge:
  - Weight matrices are ~34x larger
  - Register pressure and shared memory limits may prevent single-dispatch fusion
  - Memory bandwidth patterns change at scale
- **No API server.** The megakernel is a benchmark/library, not a serving solution. Agent Zero needs an OpenAI-compatible HTTP endpoint.
- **No quantization support documented.** Weights loaded from HuggingFace BF16/FP16 format. GGUF quantized weights (Q4_K_M, TQ4_1S) are not supported.
- **Architecture-specific.** Only works on Qwen3.5 hybrid DeltaNet + attention models. Not portable to Llama, Gemma, etc.

### Future Potential

If Lucebox scales to 27B — or if the megakernel approach is applied to the DeltaNet layers while llama.cpp handles the attention layers:

| Scenario | Impact |
|----------|--------|
| Full megakernel at 27B | 2-3x faster than llama.cpp at same or lower power |
| Hybrid: megakernel DeltaNet + llama.cpp attention | Moderate speedup with compatibility preserved |
| Megakernel at 225W overnight | Same throughput as llama.cpp at 350W, ~40% power savings |
| Megakernel + MTP | Potentially 4-5x total throughput gain if both approaches compound |

### The Architectural Insight

The megakernel approach validates a principle we've seen across the project: optimization that respects the structure of the problem outperforms optimization that treats the problem generically.

Qwen3.5's hybrid architecture has two fundamentally different layer types. llama.cpp treats them the same (separate kernel launches for each). Lucebox treats them differently (one fused megakernel for DeltaNet, DFlash for attention). The performance gap comes from matching the optimization to the structure.

This is DEC-017 (format determines capability) applied to CUDA kernels: the format of the computation determines the performance of the inference.

---

## Relationship to Other Optimizations

| Optimization | Layer | Status | Compounds With Lucebox? |
|-------------|-------|--------|------------------------|
| TurboQuant | KV cache compression | Active build | Yes — smaller KV cache regardless of kernel dispatch pattern |
| MTP | Token generation throughput | Evaluation | Unknown — MTP requires specific model architecture support |
| TQ4_1S | Weight compression | Evaluation | No — Lucebox loads BF16/FP16, not GGUF |
| Power tuning | Energy efficiency | Ready to deploy | Yes — 220W sweet spot matches Lucebox benchmarks exactly |
| TOON | Token format efficiency | Research | Yes — orthogonal (generation format, not kernel dispatch) |
| CPU offload | VRAM management | Available | No — megakernel is GPU-only by design |

---

## Watch Criteria

Revisit Lucebox when any of these occur:
- [ ] 27B model support announced or benchmarked
- [ ] API server / HTTP endpoint added (needed for Agent Zero integration)
- [ ] GGUF or quantized weight format support added
- [ ] Community fork adds llama.cpp-compatible serving on top of megakernel
- [ ] DFlash benchmarks published separately (relevant to our 8 attention layers)
- [ ] RTX 3090 (sm_86) specific benchmarks published

---

## References

| Source | URL |
|--------|-----|
| Lucebox Hub repo | github.com/Luce-Org/lucebox-hub |
| Megakernel directory | github.com/Luce-Org/lucebox-hub/tree/main/megakernel |
| DFlash directory | github.com/Luce-Org/lucebox-hub/tree/main/dflash |
| Lucebox website | lucebox.com |
| Lucebox blog | lucebox.com/blog |
