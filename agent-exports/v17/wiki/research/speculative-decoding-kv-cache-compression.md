# Speculative Decoding & KV Cache Compression for Local LLM Inference

**Status:** STABLE
**Created:** 2026-07-18
**Last deepened:** 2026-07-18
**Domain:** AI Agent Architecture & Local Inference
**Tags:** [local-inference, speculative-decoding, kv-cache, memory-optimization, LLM-efficiency, edge-AI]

## Overview

Speculative decoding and KV cache compression are the two primary lossless techniques for accelerating local LLM inference on consumer hardware (RTX 3090/4090, 24GB VRAM). Speculative decoding uses a small draft model to generate candidate tokens that the larger target model verifies in parallel, achieving 2–3× throughput improvement without quality loss. KV cache compression reduces the memory footprint of stored key-value states during autoregressive generation, enabling longer contexts and higher concurrency on memory-constrained hardware.

Together, these techniques enable Exocortex-class agent systems to run locally on consumer GPUs, narrowing the frontier gap through engineering rather than scale.

---

## 1. Speculative Decoding

### 1.1 Core Mechanism

Speculative decoding decouples token generation into two phases:
1. **Draft phase:** A small, fast draft model generates *k* candidate tokens autoregressively.
2. **Verify phase:** The target model evaluates all *k* candidates in a single forward pass, accepting tokens until the first mismatch, then generating one additional token.

The result is identical to target-model autoregressive generation — the technique is **lossless**.

### 1.2 Draft Model Strategies

| Strategy | Description | Speedup | Training Required |
|---|---|---|---|
| **Independent draft** | Separate small model (e.g., 0.5B draft for 7B target) | 2-3× | No (use off-the-shelf) |
| **Self-speculative (layer skip)** | Skip intermediate layers of target model | 1.5-2× | No |
| **Self-speculative (quantized)** | Quantized weights + compressed KV cache draft | 2-2.5× | No (QuantSpec) |
| **Eagle-style (feature prediction)** | Train draft head on target model features | 3-4× | Yes (lightweight) |
| **KV-aware (KVShot)** | Draft model reuses target KV cache for long-range context | Marginal† | Yes (TTT, future: block-wise) |

† KVShot (arXiv:2604.26412) shows improved long-range acceptance rates with KV-reuse, but end-to-end speedups remain marginal under current training pipelines due to shallow drafter structural bottlenecks.

### 1.3 2026 State of the Art

**Cassandra (arXiv:2605.26558):** Algorithm-hardware co-designed self-speculative decoding for consumer GPUs. Constructs draft model via fine-grained data selection + pruning + mantissa truncation, enabling rapid candidate generation before full-precision verification. Achieves **2.41× speedup over BF16 baseline** on Llama 3 8B / RTX 4090, and **1.81× more tokens under same memory budget vs Eagle-3**.

**QuantSpec (arXiv:2502.10424):** Self-speculative decoding with hierarchical 4-bit quantized KV cache + 4-bit weights for draft. Maintains >90% acceptance rate and delivers **~2.5× end-to-end speedup** for long-context inference, outperforming sparse-KV self-speculative methods.

**VeriCache (arXiv:2605.17613):** Converts lossy KV cache compression methods into lossless inference by using compressed cache for drafting and full cache for verification — composing speculative decoding with token-dropping/quantization methods.

**SpecEE:** Compound gain pattern — speculative decoding (2-3×) × early-exit networks (1.5-2× on easy tokens) = multiplicative throughput improvement for local inference.

---

## 2. KV Cache Compression

### 2.1 The KV Cache Bottleneck

At 32K tokens, a Qwen3-8B model holds ~4.5 GiB of fp16 KV cache against ~5 GiB of int4 weights. The cache grows **linearly with context length** — it is the dominant memory consumer in long-context inference.

### 2.2 Compression Taxonomy

| Method Family | Approach | Compression Ratio | Quality Cost | Reversible? |
|---|---|---|---|---|
| **Quantization** | 4-bit / 3-bit KV values (KIVI, KVQuant) | 4-8× | 0.1-0.5% PPL | Lossy |
| **Token dropping** | Evict/merge low-attention tokens (SnapKV, KVzip, KVzap) | 2-8× | Variable | Irreversible |
| **Hierarchical** | Multi-tier storage (Tamarin, PolyKV) | 12-28× | 0.1-0.4% PPL | Reversible (Tamarin) |
| **Asymmetric** | Keys int8 (softmax stability), Values 3-bit (TurboQuant) | ~3× | +0.57% PPL | Lossy (PolyKV) |

### 2.3 2026 Breakthroughs

**Tamarin (HSQ) — Research Square rs-10297225:** Three-tier reversible compression: L1 (non-summarized 4-bit focal tier), L2 (3-bit learned group-summary vectors as routing keys), L3 (CPU-RAM archive of all compressed originals at 4-bit). At decode time, per-head router scores L2 groups, fetches selected originals from L3, attends to restored tokens. Compression is an **index, not a deletion**. Achieves **12-28× GPU KV cache reduction** with 0.1-0.4% PPL overhead on Qwen3 4B-14B, 96-97% token-level agreement, and statistically equivalent binary needle retrieval. Quality cost **decreases with model size**.

**PolyKV (arXiv:2604.24971):** Shared asymmetrically-compressed KV cache pool for multi-agent inference. Single compressed cache written once, injected into N independent agent contexts. Keys: int8 (q8_0) for softmax stability. Values: TurboQuant MSE (FWHT rotation + 3-bit Lloyd-Max). On Llama-3-8B with 15 agents sharing 4K context: **KV cache memory reduced from 19.8 GB → 0.45 GB (97.7% reduction)**, +0.57% PPL degradation, BERTScore F1 0.928. PPL delta does **not** grow with agent count.

**TurboQuant 3-bit:** FWHT rotation + Lloyd-Max quantization tuned to N(0,1) — removes primary memory bottleneck for long-context local inference. With 3-bit compression, 128K+ context windows become feasible on 24GB consumer GPUs.

---

## 3. KV Cache Scheduling

**Geometric Slicing Algorithm (GSA — SSRN 6153334):** First non-clairvoyant policy with constant competitive ratio for KV-cache-constrained LLM serving. Manages uncertainty through geometric phase structure (periodic restarts to bound memory exposure) and staggered pipeline mechanism (smooths aggregate memory consumption). Competitive ratio ≤61.92 (general), ≤32 (large-memory regime). Clairvoyant counterpart GBA achieves approximation ratio 10.67 (general), 6.75 (large-memory) — significant improvement over prior >9000 bound.

**sKis Survey (ACL 2026 Findings):** System-aware KV infrastructure taxonomy across three dimensions: temporal (execution/scheduling), spatial (placement/migration), structural (representation/retention). Identifies cross-behavior co-design affinity.

---

## 4. Compound Techniques & Integration

### 4.1 Speculative Decoding + KV Cache Compression

These techniques compose multiplicatively:
- **VeriCache** directly composes speculative decoding with lossy KV cache methods, turning them lossless.
- **QuantSpec** combines 4-bit quantized KV cache + 4-bit weights for self-speculative draft — unified quantization.
- **Cassandra** uses mantissa truncation on both weights and KV cache for draft candidate generation.

### 4.2 Multi-Agent Inference

PolyKV's shared KV pool is directly relevant to multi-agent orchestration patterns — when multiple Exocortex subordinate agents share overlapping context, a single compressed KV cache eliminates redundant memory allocation.

### 4.3 Local-to-Frontier Bridging

A 27B model with optimized speculative decoding + KV cache compression can approach the effective throughput of a 70B+ unoptimized model — narrowing the frontier gap through inference engineering rather than parameter scaling. Combined with knowledge distillation (see [[knowledge-distillation-local-llm-bridging]]) and cascade routing, this forms a complete local-to-frontier bridging stack.

---

## 5. TRL Assessment

| Technique | TRL | Deployment Stage |
|---|---|---|
| Speculative decoding (vLLM, TensorRT-LLM) | 7 | Production |
| KV cache quantization (KIVI, KVQuant) | 6-7 | Production integration |
| Self-speculative (layer skip) | 7 | Production (llama.cpp, vLLM) |
| PolyKV multi-agent shared KV | 4-5 | Research prototype |
| Tamarin reversible compression | 4-5 | Research prototype |
| Cassandra algorithm-hardware codesign | 4 | Research prototype |
| GSA competitive scheduling | 3-4 | Theoretical + numerical |

---

## 6. Implementation on Consumer Hardware

### RTX 3090/4090 (24GB VRAM)
- With 3-bit KV cache compression: 128K context windows feasible.
- Speculative decoding 2-3× throughput enables Qwen3-30B-class effective throughput on 24GB.
- Megakernel fusion (see [[rtx-3090-cuda-optimization]]) + KV compression + speculative decoding stack can approach 500+ tok/s on 7B-class models at batch=1.

### Key Libraries
- **vLLM:** Production speculative decoding + PagedAttention KV cache management
- **TensorRT-LLM:** NVIDIA-optimized speculative decoding + KV quantization
- **llama.cpp:** Self-speculative decoding (layer skip) + aggressive KV quantization
- **SGLang:** RadixAttention for structured KV cache reuse

---

## 7. Cross-Domain Connections

1. **Multi-agent orchestration** — PolyKV shared KV pools for subordinate agent context sharing
2. **Knowledge distillation** — Cascade routing: frontier→distilled→local, with speculative decoding as last-mile acceleration
3. **RTX 3090 CUDA optimization** — Megakernel fusion + KV compression = complementary throughput stack
4. **Context management** — KV cache compression enables longer effective context windows on constrained hardware
5. **Memory architecture** — Sleep consolidation→KV cache pruning as idle-time optimization pathway
6. **Privacy-preserving inference** — Fully local inference eliminates cloud dependency; speculative decoding makes this practical
7. **Agentic self-learning** — Faster inference → tighter learning loops during autonomous optimization cycles
8. **Entity resolution** — Long-context KV compression enables full knowledge graph in working memory during resolution
9. **Autonomous coding agents** — Speculative decoding accelerates code generation in ATLAS-style self-improving coding agents
10. **Edge AI / TinyML** — Quantization techniques from KV compression transfer to on-device microcontroller inference

---

## 8. References

1. Leviathan et al., "Fast Inference from Transformers via Speculative Decoding," ICML 2023.
2. Chen et al., "Accelerating Large Language Model Decoding with Speculative Sampling," arXiv:2302.01318.
3. Cassandra: Self-Speculative Decoding for Consumer Devices, arXiv:2605.26558 (2026).
4. QuantSpec: Self-Speculative Decoding with Hierarchical Quantized KV Cache, arXiv:2502.10424.
5. Tamarin (HSQ): Reversible Hierarchical KV-Cache Compression, Research Square rs-10297225 (2026).
6. PolyKV: Shared Asymmetrically-Compressed KV Cache Pool for Multi-Agent LLM Inference, arXiv:2604.24971 (2026).
7. VeriCache: Turning Lossy KV Cache into Lossless LLM Inference, arXiv:2605.17613 (2026).
8. KVShot: Can KV Caches Rescue Long-Range Speculative Decoding?, arXiv:2604.26412 (2026).
9. Geometric Slicing Algorithm: Competitive Non-Clairvoyant KV-Cache Scheduling, SSRN 6153334 (2026).
10. Yang et al., "Towards Efficient LLM Serving: A Survey on System-Aware KV Cache Optimization," ACL 2026 Findings.
11. Hooper et al., "KVQuant: Towards 10 Million Context Length LLM Inference with KV Cache Quantization," arXiv:2401.18079.
12. Liu et al., "KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache," ICML 2024.
13. TurboQuant: FWHT + Lloyd-Max KV cache quantization (2025).
14. Exocortex v16/v17 shared corpus: KV Cache Compression & Speculative Decoding wiki pages, field reports (2026-05-20 to 2026-07-03).
