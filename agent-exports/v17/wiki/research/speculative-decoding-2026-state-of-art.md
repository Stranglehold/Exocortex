# Speculative Decoding — State of the Art 2025-2026

**Status:** STABLE
**Created:** 2026-07-10
**Last Updated:** 2026-07-10
**Lines:** 87
**From Field Report:** 20260710_speculative-decoding-2025-2026.md

## Overview

Speculative decoding is an inference optimization technique that breaks the autoregressive bottleneck by using a small, fast "draft" model to propose multiple candidate tokens, then having the full "target" model verify them in a single parallel forward pass. Output quality is mathematically identical to standard autoregressive generation — only the efficiency changes.

This page extends [[speculative-decoding-kv-cache-compression]] with the 2025-2026 state of the art: production deployment benchmarks, frontier research, and cross-domain connections.

## Production Status (2025-2026)

- **NVIDIA H200 benchmarks:** 3.6× throughput improvement combining speculative decoding with FP8 quantization on Llama 3.1-405B.
- **vLLM native support:** Eagle 3 integration delivers up to 2.5× speedup. Supports draft model, ngram matching, and EAGLE methods.
- **TensorRT-LLM:** Custom kernels for draft generation + verification phases.
- **Typical numbers:** Llama 3.1-70B with 1B draft = 2.31× speedup; Llama 3.1-8B on A100 = ~2× speedup.
- **Open-source frameworks:** llama.cpp speculative support (PR #6530 merged), vLLM Eagle, TensorRT-LLM.

## Frontier Research

1. **PARD-2: Target-Aligned Parallel Drafting** (arXiv:2605.08632, May 2026) — moves beyond sequential draft-then-verify: the draft model is trained to align its distribution with the target's verification preferences, enabling parallel draft generation with higher acceptance rates.

2. **Speculative Speculative Decoding** (arXiv:2603.03251, Mar 2026) — applies speculative decoding recursively: the draft model itself is speculatively decoded, creating a multi-tier cascade.

3. **Adaptive Hybrid Speculative Decoding** (ScienceDirect S0925231226011574, 2026) — dynamically switches between draft model, ngram matching, and autoregressive modes based on real-time acceptance rate monitoring.

4. **NAACL 2025 — "Decoding Speculative Decoding"** — efficiency analysis reframing verification cost as a primary metric rather than speedup alone; shows that speedup saturates with draft length due to verification overhead.

## Verification-Efficiency Reframe

NAACL 2025 key insight: speedup = (acceptance rate × draft length) / (1 + verification cost ratio). As draft length increases, verification cost grows linearly in target model forward pass, diminishing returns. Optimal draft length is typically 4-6 tokens for current hardware.


## Corpus Grounding — Existing Exocortex Knowledge

This page builds on substantial prior work in the Exocortex wiki:

- **[[speculative-decoding-kv-cache-compression]]** — the foundational page covering draft-then-verify mechanics, KV cache compression, and complementary acceleration patterns. This page extends that with 2025-2026 frontier research.
- **[[local-model-inference-optimization-pipeline]]** — documents Medusa (multiple prediction heads, ~2x), DFlash (KV-cache sharing, ~3x), and Eagle (feature-level draft, ~4x) draft model variants, plus SpecInfer tree attention for verification. 2-4x speedup with 300-800 MB VRAM overhead, zero quality degradation via rejection sampling.
- **[[bridging-local-frontier-model-performance]]** — DFlash block-diffusion speculative decoding on RTX 3090 delivers ~2x speedup (35→69 tok/s) for Qwen3.6-27B, a critical local-to-frontier bridging component.
- **[[hardware-software-codesign-ai-agents]]** — maps speculative decoding to heterogeneous hardware: draft model on low-power accelerator (NPU, small GPU, edge), verification on high-compute GPU, mirroring the prefill/decode disaggregation pattern.

## Hardware Heterogeneity & Local Inference

Speculative decoding's draft/verify pipeline maps naturally to heterogeneous silicon:

| Draft Stage | Verify Stage | Effective Platform |
|-------------|--------------|--------------------|
| Small GPU (RTX 3060) | Large GPU (RTX 4090) | Multi-GPU workstation |
| FPGA/NPU | GPU | Heterogeneous compute node |
| CPU (llama.cpp) | GPU (vLLM) | Memory-constrained edge |
| Remote fast model | Local large model | Cloud + local hybrid |

The [[fpga-inference-acceleration]] page documents LUT-LLM's 3.05-6.60× higher tokens/J vs GPUs — making FPGA an ideal draft-stage accelerator, while the GPU handles verification in a heterogeneous system.

### Local Model Impact (v17 Verified)
- **DFlash on RTX 3090:** 35→69 tok/s for Qwen3.6-27B (~2× speedup)
- **Memory overhead:** 300-800 MB VRAM for draft model co-residency
- **Compatibility:** Works with quantization (FP8, GPTQ, AWQ) and can be combined with KV cache compression

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[speculative-decoding-kv-cache-compression]] | Existing wiki page covers underlying techniques; this page extends with 2025-2026 research |
| [[bridging-local-frontier-model-performance]] | 2-3× latency reduction narrows responsiveness gap between local and cloud models |
| [[ai-agent-architecture-local-inference]] | Multi-step agent tasks benefit multiplicatively from per-call speedup |
| [[atlas-autonomous-coding-agents]] | Faster inference enables more aggressive temperature escalation retry loops |
| [[fpga-inference-acceleration]] | DSP-optimized draft model on FPGA + GPU target model = heterogeneous speculative decoding |
| [[chiplet-architectures-ai-inference]] | Draft/verify pipeline stages map naturally to heterogeneous silicon |
| [[memory-architecture-taxonomy]] | KV cache compression reduces memory pressure, freeing GPU RAM for draft model co-residency |
| [[local-model-inference-optimization-pipeline]] | Speculative decoding is third pillar alongside quantization and KV cache compression |

## References

1. NVIDIA Technical Blog (2025) — "An Introduction to Speculative Decoding" — developer.nvidia.com
2. Introl Blog (Dec 2025) — "Speculative Decoding: Achieving 2-3x LLM Inference Speedup" — introl.com
3. PARD-2 (May 2026) — arXiv:2605.08632
4. Speculative Speculative Decoding (Mar 2026) — arXiv:2603.03251
5. NAACL 2025 — "Decoding Speculative Decoding" — aclanthology.org/2025.naacl-long.328
6. Adaptive Hybrid SD (2026) — ScienceDirect S0925231226011574
7. UC Berkeley EECS-2025-224 — "Efficient LLM System with Speculative Decoding"
8. vLLM EAGLE-3 integration — docs.vllm.ai
9. BentoML LLM Inference Handbook — bentoml.com
10. Exocortex wiki: local-model-inference-optimization-pipeline.md (v17)
