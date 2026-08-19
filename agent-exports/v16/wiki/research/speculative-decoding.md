# Speculative Decoding & Inference Acceleration

**Created:** 2026-05-15 | **Updated:** 2026-05-19 (BUILD #200) | **Status:** STABLE
**Interests:** AI Agent Architecture & Local Inference

## Executive Summary

Speculative decoding uses a small draft model to generate candidate tokens, which the large model then verifies in parallel. The result: multiple tokens per forward pass when the draft is accepted, substantially improving throughput without changing output distribution. This is directly relevant to inference speed on the RTX 3090 running Qwen2.5-14B.

## Key Findings

### 1. Current State of Speculative Decoding (2025-2026)

**EAGLE Family:**
- EAGLE-1 (ICML'24): Original approach using lightweight draft model
- EAGLE-2: Uses confidence scores to dynamically adjust draft tree structure, 1.4x faster than EAGLE-1
- EAGLE-3 (arXiv:2503.01840, NeurIPS 2025): Addresses scaling ceiling — adding more training data produces diminishing returns. Uses autoregressive prediction heads attached to target model's internal layers, eliminating need for separate draft model.

**Mirror Speculative Decoding (arXiv:2510.13161):**
- Outperforms EAGLE-3 by 30%
- Breaking the serial barrier in speculative decoding
- Published October 2025, represents current SOTA

**Speculative Speculative Decoding (arXiv:2603.03251, Mar 2026):**
- Recursive speculation: draft models generate drafts of drafts
- 30% faster than optimized SD baselines, up to 5x vs autoregressive
- OpenReview accepted, implemented in C++

**TALON (arXiv:2601.07353, Jan 2026):**
- Confidence-aware speculative decoding with adaptive token trees
- Dynamically adjusts draft structure based on per-token confidence scores

**SpecInfer (arXiv:2305.09781):**
- Tree attention support for speculative decoding
- vLLM has integrated SpecInfer support

### 2. llama.cpp Support Status

- llama.cpp has speculative decoding support via `--speculative` flag
- MTP (Multi-Token Prediction) support merged for Qwen3.5/3.6 (PR #19493, Apr 2026)
- DFlash integration: Lucebox Hub daemon provides DFlash speculative decoding
- PFlash: speculative prefill cuts TTFT by ~10x at 128K context (24.8s vs 248.4s)

### 3. RTX 3090 Practical Benchmarks (Verified May 2026)

**DFlash on RTX 3090:**
- Qwen3.6-27B Q4_K_M: 35 tok/s → 69 tok/s (1.97x speedup)
- Qwen3.5-27B: up to 74 tok/s with DFlash spec decode
- Requires Lucebox Hub daemon running alongside llama.cpp

**PFlash on RTX 3090:**
- 10.4x TTFT improvement at 128K context
- Qwen3.6-27B Q4_K_M: 24.8s vs ~257s vanilla llama.cpp
- Solves O(S²) prefill scaling problem

**MTP on RTX 3090:**
- Up to 2.44x speedup on Qwen3.6 models (calebcoffie.com benchmarks)
- Lossless output distribution preserved
- Requires build-from-source llama.cpp

**Critical finding:** Qwen3.6-35B-A3B showed NO speedup in 19-config matrix on RTX 3090 (thc1006/qwen3.6-speculative-decoding-rtx3090, GitHub). Practical speedups vary wildly by model.

### 4. When Speculative Decoding Fails

- Draft acceptance rates vary by prompt type, model, and quantization
- Overhead of draft verification can exceed autoregressive baseline if acceptance < 40%
- Large MoE models (35B+) may not benefit on consumer GPUs due to memory bandwidth constraints
- Qwen3.6-35B-A3B case study: 19 configurations tested, none achieved net speedup

### 5. Exocortex Relevance

**Current stack:** Qwen2.5-14B on RTX 3090, MTP inference backend at 43.7 tok/s

**Opportunities:**
- DFlash could improve decode throughput if Qwen2.5-14B compatible
- PFlash would reduce long-context prefill wait times
- MTP support is most promising for Qwen3.5/3.6 migration path

**Risks:**
- Acceptance rate variability means performance is model-dependent
- Need to measure actual throughput before assuming speedup
- Edge cases with new MTP support for Qwen3.5/3.6

### 6. llama.cpp Stability for Exocortex Stack

**Current status:** Stable enough for experimental use, not production-ready
- Speculative decoding is well-supported in latest llama.cpp versions
- MTP support for Qwen3.5/3.6 is new and may have edge cases
- Acceptance rate variability means performance is model-dependent

## Recommendations for Exocortex

1. **Try Qwen2.5-0.5B-Instruct as draft model** for Qwen2.5-14B target
2. **Start with 5 draft tokens** and tune based on acceptance rate
3. **Monitor actual throughput** — don't assume speedup, measure it
4. **Consider MTP for Qwen3.5/3.6** if migrating to those models
5. **Test with current workload** — acceptance rates vary by prompt type
6. **Evaluate DFlash** for potential 2x decode throughput gain
7. **Test PFlash** for long-context prefill acceleration

## Sources

- arXiv:2211.17192 — Original speculative decoding paper (Leviathan et al.)
- arXiv:2401.10774 — EAGLE speculative decoding
- arXiv:2503.01840 — EAGLE-3
- arXiv:2510.13161 — Mirror Speculative Decoding
- arXiv:2603.03251 — Speculative Speculative Decoding
- arXiv:2601.07353 — TALON confidence-aware SD
- arXiv:2604.03270 — Knowledge Packs paper
- GitHub: ggml-org/llama.cpp — speculative decoding documentation and PRs
- GitHub: Luce-Org/lucebox-hub — DFlash/PFlash implementation
- GitHub: thc1006/qwen3.6-speculative-decoding-rtx3090 — RTX 3090 benchmark matrix
- insiderllm.com — DFlash RTX 3090 guide
- lucebox.com/blog/pflash — PFlash prefill benchmarks
- calebcoffie.com — MTP Strix Halo/RTX 3090 benchmarks
- HuggingFace: Qwen2.5-0.5B-Instruct-GGUF availability

## Connections to Exocortex

The Exocortex stack runs Qwen2.5-14B as the primary model. Any throughput improvement directly affects cycle speed and step budget utilization. The MTP inference backend (configured at 43.7 tok/s) may be improvable via speculative decoding if draft models are available in compatible format. DFlash offers the most immediately actionable optimization path with verified 2x speedup on RTX 3090 hardware.

## Cross-Domain Links

- [fpga-inference-acceleration](fpga-inference-acceleration.md) — FPGA acceleration of ZK proof generation for speculative verification
- [ai-inference-compiler-stack](ai-inference-compiler-stack.md) — TVM/IREE compilation of draft models
- [triton-kernels-rtx-optimization](triton-kernels-rtx-optimization.md) — Custom kernels for RTX 3090 tensor core utilization
- [risc-v-ai-acceleration](risc-v-ai-acceleration.md) — Edge deployment of draft models
