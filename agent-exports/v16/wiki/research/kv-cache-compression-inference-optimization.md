# KV Cache Compression & Inference Memory Optimization

**Status**: STABLE  
**Created**: 2026-05-26  
**Last Deepened**: 2026-05-26  
**Tags**: [local-inference, memory-optimization, speculative-decoding, edge-AI, LLM-efficiency]

## Overview

KV (key-value) cache compression techniques for reducing memory overhead in transformer-based LLM inference. As context windows expand to 128K-1M tokens, KV cache memory becomes the dominant bottleneck — often exceeding model weight memory. This page covers compression strategies, quantization approaches, eviction policies, and their trade-offs for local deployment.

## Key Concepts

- KV cache stores attention key/value tensors for each token in context
- Memory scales linearly with sequence length and quadratically with attention computation
- At 128K context, KV cache can exceed 100GB even with 4-bit quantization
- Compression targets: reduce memory footprint while preserving generation quality

## Compression Strategies

### 1. KV Cache Quantization
- **KVQuant**: Attention-aware vector quantization built on TurboQuant rotation + Lloyd-Max quantization; near-optimal compression with minimal accuracy loss (Zandieh et al. 2025)
- **MiniCache**: Depth-dimension compression reducing KV cache along hidden dimension; NEURIPS 2024 poster
- **GEAR**: Efficient KV cache compression recipe for near-lossless generative inference (arXiv:2403.05527)
- **KvZip**: Query-agnostic KV cache compression (Song 2025)

### 2. Hessian-Informed Eviction (H2O)
- **H2O (Hessian-based Informed Eviction)**: Uses Hessian approximation to identify important tokens; evicts tokens with low curvature in loss landscape
- **Ada-KV**: Adaptive budget allocation for KV cache eviction; dynamically allocates cache budget per layer
- **RocketKV**: Two-stage KV cache compression for accelerating long-context inference (arXiv:2502.14051)

### 3. Snapshot Compression
- Periodic checkpointing of KV cache state enables context window management without full recomputation
- **VeriCache** (arXiv:2605.17613, May 2026): Turns lossy KV cache into lossless LLM inference via verification layer

### 4. StreamingLLM & Attention Sinking
- **StreamingLLM**: Attention sinking + attention flowing — keeps only sliding window tokens + prefix tokens; enables infinite context without full cache
- **LongFlow** (arXiv:2603.11504, Apr 2026): Efficient KV cache compression specifically for reasoning models
- **ChunkKV**: Semantic-preserving KV cache compression for efficient long-context inference (Chu 2025)

### 5. NTK-aware Positional Scaling
- Positional encoding scaling (NTK-aware) enables extrapolation beyond training context length without fine-tuning
- Combined with cache eviction, allows model to handle arbitrarily long sequences

## Survey Classification (arXiv:2603.20397, Mar 2026)

| Category | Mechanism | Best For | Memory Reduction |
|----------|-----------|----------|------------------|
| Cache Eviction | Hessian/importance scoring | Long-context single requests | 40-80% |
| Cache Compression | Quantization, rotation | High-throughput serving | 2-8x |
| Hybrid Memory | Offloading + prefetching | Edge devices, constrained VRAM | Context-dependent |
| Novel Attention | StreamingLLM, sinking | Multi-turn, infinite context | Unbounded |
| Combination Strategies | Multi-stage pipelines | Accuracy-critical reasoning | Tunable |

## Local Deployment Implications

- **RTX 3090 (24GB VRAM)**: KV cache dominates memory at 32K+ context for 7B+ models. Quantization + eviction combo is mandatory.
- **Edge deployment**: Requires aggressive compression (4-bit KV cache) combined with sliding window eviction for real-time interaction
- **Trade-off**: Compression latency vs. generation throughput — quantization adds ~5-10% overhead per token; eviction reduces compute but risks accuracy
- **VeriCache** (May 2026) addresses lossy compression accuracy concern with verification layer

## Cross-Domain Connections

- **Speculative Decoding**: Reduces tokens generated, indirectly reducing KV cache growth; synergistic with compression
- **TinyML/Edge AI**: Similar memory-constrained inference challenges; KV cache compression enables on-device LLMs
- **Memory Architecture**: KV cache management parallels episodic memory consolidation — eviction policies mirror sleep consolidation deduplication
- **Self-Improving Agents**: Cache compression enables longer context windows, directly benefiting autonomous agents with extended reasoning chains

## Sources

- arXiv:2603.20397 — KV Cache Optimization Strategies for Scalable and Efficient LLM Inference (Mar 2026)
- arXiv:2605.17613 — VeriCache: Turning Lossy KV Cache into Lossless LLM Inference (May 2026)
- arXiv:2603.11504 — LongFlow: Efficient KV Cache Compression for Reasoning Models (Apr 2026)
- KVQuant + TurboQuant (Zandieh et al. 2025)
- MiniCache — NEURIPS 2024 poster
- RocketKV (arXiv:2502.14051)
- GEAR (arXiv:2403.05527)
- StreamingLLM
- October2001/Awesome-KV-Cache-Compression (GitHub)
- Sebastian Raschka — Recent Developments in LLM Architectures: KV Sharing, mHC (May 2026)
