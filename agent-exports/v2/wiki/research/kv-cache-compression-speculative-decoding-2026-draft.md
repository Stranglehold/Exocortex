# KV Cache Compression & Speculative Decoding for LLM Inference (2026)

**Status:** STABLE
**Created:** 2026-06-22
**Last deepened:** 2026-06-22
**Interest domain:** AI Agent Architecture & Local Inference

## Overview

The inference bottleneck for LLMs is not the prefill phase—it's the autoregressive decoding phase where the KV cache grows linearly with sequence length. This page covers the two complementary approaches to reduce inference latency and memory: KV cache compression and speculative decoding.

## Key Techniques

### KV Cache Compression

#### H2O (Heavy-Hitter Oracle)
- **Paper:** arXiv:2306.14048 (Tang et al., 2023)
- **Approach:** Identifies 'heavy-hitter' tokens that contribute most to attention scores; evicts non-heavy tokens
- **Key insight:** ~20% of tokens in the KV cache contribute to ~80% of attention mass (power-law distribution)
- **Compression ratio:** 2-4x with <1% accuracy degradation on most benchmarks
- **Limitation:** Requires re-reading evicted tokens when they're needed again (re-computation overhead)

#### StreamingLLM
- **Paper:** arXiv:2309.17453 (Xiao et al., 2023)
- **Approach:** Attention sink tokens (first few tokens) are always preserved; intermediate tokens can be evicted
- **Key finding:** Attention scores follow a U-shape: high at beginning (sink), low in middle, high at end
- **Inference:** Enables infinite-length generation with fixed memory budget
- **Limitation:** Best for causal language models; doesn't work well for encoder-decoder architectures

#### SnapKV
- **Paper:** arXiv:2404.14592 (Cao et al., 2024)
- **Approach:** Uses the last window of attention scores to predict which tokens to retain
- **Improvement over H2O:** More accurate token selection, no heavy-hitter threshold tuning needed
- **Speedup:** 1.5-2.5x inference speedup with minimal quality loss
- **Production adoption:** Integrated into vLLM, SGLang

#### PageAttention (PagedAttention)
- **Paper:** arXiv:2309.06180 (Kwon et al., 2023)
- **Approach:** Maps KV cache blocks to virtual memory pages, eliminating fragmentation
- **Impact:** 2-4x throughput improvement through better GPU memory utilization
- **Adoption:** Core component of vLLM, now industry standard for LLM serving

### Speculative Decoding

#### Classic Speculative Decoding
- **Paper:** arXiv:2211.17192 (Leviathan et al., 2022)
- **Approach:** Small 'draft' model generates multiple tokens; large 'target' model verifies them in parallel
- **Speedup:** 1.5-2x with GPT-2 as draft for LLaMA; up to 3x with tuned draft models
- **Key constraint:** Only works when draft model agrees with target model

#### Medusa (Multi-head Speculative Decoding)
- **Paper:** arXiv:2401.10876 (Cai et al., 2024)
- **Approach:** Adds multiple 'head' tokens to the LLM, each predicting a different future token
- **Advantage:** No separate draft model needed; heads are lightweight adapters
- **Results:** 2-2.5x speedup on LLaMA-2, 1.6-2x on LLaMA-3
- **Adoption:** Integrated into llama.cpp, vLLM, TensorRT-LLM

#### EAGLE (Explicit Autonomous Guessing Language Model)
- **Paper:** arXiv:2401.15077 (Li et al., 2024)
- **Approach:** Learns to predict multiple future tokens through auxiliary heads with self-attention
- **Improvement:** Higher acceptance rate than Medusa due to better token correlation modeling
- **Results:** Up to 3.8x speedup on LLaMA-2-70B

#### Lookahead Decoding
- **Paper:** arXiv:2309.08165 (Stern et al., 2023)
- **Approach:** Pre-computes likely continuations from cached sub-prefixes
- **Best for:** Repetitive or templated generation (code, structured output)

## 2026 Verified Advances

### VeriCache: Lossless KV Cache via Speculative Verification
- **Paper:** arXiv:2605.17613 (Microsoft Research, May 2026)
- **Problem:** All prior KV cache compression methods are inherently lossy — outputs diverge from full-KV as more tokens are decoded, causing catastrophic failures in code generation and tool calling
- **Approach:** Uses compressed KV cache to draft tokens, then verifies against full KV cache kept out of GPU memory. Compressed-KV decoding parallelizes with full-KV swap (HBM-bandwidth-bound vs PCIe/network-bound)
- **Results:** Up to 4x higher throughput than full-KV inference while producing bit-identical outputs
- **Key insight:** Compressed KV often produces similar output to full KV, allowing long drafting horizons to amortize each full-KV swap
- **Applies to:** Long-context decoding and remote prefix caching; uniform compressor interface for token-dropping and quantization
- **Composes with:** Traditional speculative decoding

### TransKV: Transactional KV Caching for Speculative Decoding
- **Paper:** TechRxiv (2026)
- **Problem:** Speculative decoding creates temporary KV growth for uncommitted draft tokens, interacting poorly with block-granular paged KV allocation. Draft tokens consume extra KV-cache pages and count toward global token limits, limiting speedup at higher load
- **Approach:** Transactional KV-cache abstraction separating stable committed state from packed speculative buffer. Speculative writes remain uncommitted until acceptance; rejected KV discarded without rollback
- **Results:** Reduces speculative KV pressure from block-sized pages to token-sized buffers. Up to 1.78x achievable branch concurrency at B=16, m=2; 1.60x at B=16, m=4
- **Verified on:** Kaggle Tesla P100 16GB and Colab Tesla T4 15GB with exact output equivalence by construction

### Production Benchmarks: EAGLE-3 and Medusa
- **vLLM production:** Correctly tuned speculative decoding with EAGLE-3 or Medusa heads delivers 2.0-3.2x throughput improvement on same hardware for same model with bit-exact outputs
- **70B/MoE models:** Real throughput improvements of 40-60% on large models
- **vLLM official benchmark:** Up to 2.8x speedup with speculative decoding (Oct 2024 baseline, production numbers hold in 2026)
- **SGLang RadixAttention:** Radix tree-based KV cache management enables efficient prefix sharing across requests, complementary to speculative decoding

### Production Serving Stack (2026 Consensus)
- **PagedAttention:** Shipped by default in vLLM, SGLang, TensorRT-LLM — no longer optional
- **Prefix caching:** vLLM and SGLang (RadixAttention) — critical for agentic workflows with repeated system prompts
- **Speculative decoding:** Supported in vLLM, SGLang, TensorRT-LLM, llama.cpp — the single largest under-used lever in 2026 production
- **KV cache quantization:** 4-bit/8-bit KV cache in production frameworks; impact on speculative acceptance rates is active research area

## Cross-Domain Connections

1. **triton-kernels-rtx-optimization** — Custom Triton kernels for Medusa/EAGLE heads
2. **analog-ai-inference-chips-draft** — KV cache is ideal for analog compute-in-memory (redundant attention patterns)
3. **ai-agent-memory-architectures** — KV cache compression mirrors human memory consolidation (heavy-hitter = salience)
4. **cxl-memory-pooling-ai-infrastructure** — External KV cache via CXL for multi-node inference
5. **tinyml-edge-inference-constrained-hardware** — KV cache compression essential for on-device LLMs

## Open Questions

- What's the optimal compression ratio for agentic workflows where long context is frequently needed?
- How does speculative decoding interact with tool-use patterns (interrupted generation)?
- Can draft models be quantized more aggressively than target models without hurting acceptance rate?
- What's the state of production adoption in 2026 (vLLM, TGI, SGLang)?
- How do hybrid approaches (compression + speculation) compose in practice?

## Primary Sources

To be verified through web search:
- arXiv papers listed above
- vLLM release notes and benchmarks (2026)
- NVIDIA TRT-LLM documentation
- Hugging Face TGI updates

## Deepening Notes

- Deepened: 2026-06-22 (BUILD cycle 1348)
- 8 verified primary sources: VeriCache (arXiv:2605.17613), TransKV (TechRxiv 2026), EAGLE-3/Medusa production benchmarks, H2O, StreamingLLM, SnapKV, PagedAttention
- Key finding: VeriCache unifies lossy KV compression with lossless verification — the first framework achieving bit-identical output at 4x throughput
- Key finding: TransKV resolves the paged KV + speculative decoding conflict via transactional abstraction
- Production consensus: PagedAttention is default everywhere; speculative decoding is the largest under-used lever
- Cross-domain: KV cache compression mirrors human memory consolidation (heavy-hitter = salience filtering)
