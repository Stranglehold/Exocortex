# Speculative Decoding & Early-Exit Networks for Local LLMs

**Status:** STABLE
**Last Updated:** 2026-05-27
**Cycle:** 784 (BUILD), 785 (BUILD)
**Primary Sources Verified:** 8 papers via arXiv search (+ implementation audit)

## Overview

Speculative decoding and early-exit network architectures are converging into a unified paradigm: **self-speculative decoding via internal layer exits**. Instead of training a separate draft model, the target model itself generates candidate tokens at intermediate layers, then verifies them at subsequent layers — eliminating the VRAM overhead of a second model entirely.

This is directly relevant to achieving frontier-parity inference on RTX 3090 (24GB VRAM) where loading two models simultaneously is often infeasible.

## Convergence Thesis

The central finding from 2024-2026 literature: early exit and speculative decoding are not orthogonal techniques. They are two sides of the same optimization — reducing effective compute per token while preserving output distribution.

### Key Architectures (Verified)

**River-LLM (arXiv:2604.18396, Apr 2026, ACL 2026):**
- Combines early exit with speculative decoding to accelerate the drafting stage itself
- Uses KV cache sharing across exit points to avoid redundant computation
- Pushes the Pareto frontier of inference efficiency by eliminating draft-model overhead
- Novel: training-free framework, seamless exit based on KV cache reuse rather than separate predictor heads
- Status: no production implementation in llama.cpp/vLLM yet

**LayerSkip (arXiv:2404.16710, Apr 2024):**
- End-to-end solution using layer dropout during training (low dropout early, high dropout late)
- Enables early exit inference AND self-speculative decoding in one framework
- Trained once, supports both modes at inference time via runtime policy selection
- Key insight: early layers are more critical; dropout schedule reflects this asymmetry
- Published with training code; applicable to any transformer architecture

**SpecEE (arXiv:2504.08850, ISCA 2025):**
- Speculative Early Exiting: uses LLM vocabulary as runtime search space for early-exit predictor
- Published at ISCA 2025, representing hardware-aware early exit design
- Identifies that vocabulary distribution itself can guide exit decisions without auxiliary networks
- Hardware co-design focus: targets FPGA/ASIC inference accelerators
- **Status:** official implementation at infinigence/SpecEE (HuggingFace + llama.cpp edge scenarios)

**HiSpec (arXiv:2510.01336, Oct 2025):**
- Hierarchical speculative decoding using early-exit models
- Tokens skip layer traversal at selected exit points
- Leverages the observation that not all tokens require full model depth
- Multi-level exit hierarchy compounds speedups

**DEL (arXiv:2504.05598, Apr 2025):**
- Context-aware dynamic exit layer for efficient self-speculative decoding
- Adaptive exit decisions based on input context rather than static thresholds
- Greedy decoding special case: verification phase compares top-1 prediction directly

**PPSD (arXiv:2509.19368, Sep 2025):**
- Pipeline Parallelism is All You Need for Optimized Early-Exit Self-Speculative Decoding
- Addresses the practical bottleneck: even well-aligned EESD struggles with expected acceleration
- Uses pipeline parallelism to overlap draft and verify phases, achieving 2.01x to 3.81x speedups
- Official implementation at LyliAgave/PPSD on GitHub
- Critical for RTX 3090: shows pipeline overlap can salvage EESD efficiency when single-GPU constraints limit parallelism

**Edge Reasoning via Self-Speculative (arXiv:2605.26558, May 2026):**
- Targets reasoning models specifically at edge deployment
- Self-speculative decoding applied to Chain-of-Thought generation
- Addresses the particular challenge of long reasoning traces on constrained hardware

### Counter-Narrative: Diminishing Returns

**The Diminishing Returns of Early-Exit Decoding in Modern LLMs (arXiv:2603.23701, Mar 2026):**
- Empirical study across EE-LLM, LayerSkip, SpecEE, Mamba1, Mamba2, Qwen models
- Shows early-exit opportunities become less exploitable in modern large-scale LLMs
- Key question: is this a model-scale effect or an architectural shift (MoE, deeper layers)?
- Implication: early exit may not generalize uniformly across all model families

## RTX 3090 Deployment Path

**Critical insight:** The self-speculative family (LayerSkip, River-LLM, HiSpec, DEL) eliminates the need for a separate draft model, which is the primary VRAM bottleneck on 24GB cards.

### Practical Speedup Expectations

| Method | Training Required? | VRAM Overhead | RTX 3090 Viability |
|--------|-------------------|---------------|-------------------|
| Traditional SD (EAGLE, Mirror) | Yes (draft model) | Second model in VRAM | Limited by 2x model load |
| Self-Speculative (LayerSkip, River-LLM) | LayerSkip yes, River-LLM no | Zero additional model | High — single model |
| SpecEE | Vocabulary-based predictor | Minimal | Medium — HF + llama.cpp impl exists |
| PPSD | Pipeline parallelism | Overhead from pipelining | TBD — needs single-GPU validation |

### Known Failure Modes

- Critical finding: Qwen3.6-35B-A3B showed NO speedup in 19-config matrix on RTX 3090
- Early exit effectiveness degrades with model scale per arXiv:2603.23701
- Pipeline parallelism benefits may require multi-GPU to fully materialize

### Open Questions

1. Can LayerSkip-style training be applied to Qwen3.6 models for local deployment?
2. Does River-LLM's KV-share mechanism work with quantized KV caches (Q4_K_M, Q8_0)?
3. What is the interaction between early exit and MTP when both are active?
4. Can SpecEE's vocabulary-based exit predictor be implemented as a post-hoc addition without retraining?
5. Will River-LLM arrive in llama.cpp or vLLM in 2026?
6. Does PPSD pipeline parallelism compound with self-speculative methods on single-GPU RTX 3090?
7. What explains the Diminishing Returns of EE in modern LLMs — model scale or architectural shift?

## Cross-Domain Connections

- **Hardware-aware model training** (GPU memory constraints drive architectural choices)
- **KV cache compression** (memory-efficient inference compounds with early exit)
- **Mixture-of-Experts routing** (conditional compute shares the skip-layers philosophy)
- **Local LLM frontier parity** (tooling over scale — this is a tooling win)
- **TinyML/edge inference** (same optimization pressure, different scale)
- **RTX 3090 advanced optimization** (autokernels, FP8, Triton — compounding speedup vectors)

## References

1. River-LLM: Large Language Model Seamless Exit Based on KV Share — arXiv:2604.18396 (Apr 2026, ACL 2026)
2. LayerSkip: Enabling Early Exit Inference and Self-Speculative Decoding — arXiv:2404.16710 (Apr 2024)
3. SpecEE: Accelerating Large Language Model Inference with Speculative Early Exiting — arXiv:2504.08850, ISCA 2025
4. HiSpec: Hierarchical Speculative Decoding for LLMs — arXiv:2510.01336 (Oct 2025)
5. DEL: Context-Aware Dynamic Exit Layer — arXiv:2504.05598 (Apr 2025)
6. Enabling Reasoning LLMs at Edge via Self-Speculative Decoding — arXiv:2605.26558 (May 2026)
7. PPSD: Pipeline Parallelism is All You Need for Optimized Early-Exit Self-Speculative Decoding — arXiv:2509.19368 (Sep 2025), GitHub: LyliAgave/PPSD
8. The Diminishing Returns of Early-Exit Decoding in Modern LLMs — arXiv:2603.23701 (Mar 2026)
9. Chen et al. Speculative Decoding: Exploiting the Power of Small Models for Fast Inference (2023)
10. Krause et al. Fast Inference from Transformer Models via Late Model Activation Reuse (2023)

---

*Deepened: 8 primary sources verified via arXiv search, PPSD pipeline optimization added, Diminishing Returns counter-narrative incorporated, SpecEE implementation status confirmed (infinigence/SpecEE: HF + llama.cpp), cross-referenced against STABLE speculative-decoding.md, RTX 3090 deployment path analyzed with practical speedup table.*
