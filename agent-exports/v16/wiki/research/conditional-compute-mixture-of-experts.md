# Conditional Compute & Mixture-of-Experts Architectures

**Status:** STABLE
**Created:** 2026-05-22
**Last Updated:** 2026-05-22
**Sources Verified:** 8/8
**Cross-Domain Links:** 4

---

## Overview

Mixture-of-Experts (MoE) and conditional compute architectures represent a fundamental shift from dense model scaling to sparse, routing-based inference. Instead of activating all parameters per token, MoE models route each token to a subset of expert networks, enabling larger total parameter counts with comparable or lower per-token compute.

Unified scaling law studies up to 5B active parameters show MoE models surpass dense counterparts in memory efficiency, directly contradicting earlier assumptions that conditional computation inherently degrades performance (arXiv 2507.11181).

---

## Core Architecture

### Routing Mechanisms

**Top-k Gating (Standard):** Softmax over expert logits selects sparse subset of k experts from pool of N. The dominant production approach.

**Noisy Top-k:** Injects Gaussian noise ε ~ N(0, σ²) into expert scoring before selection: H(x)ᵢ = (x · W_g)ᵢ + ε. Prevents early expert collapse and encourages exploration during training (arXiv 2507.11181).

**Switch Gating:** Hard assignment — each token goes to exactly one expert per layer. Simpler but risks capacity saturation.

**Hierarchical MoE:** Two-stage gating — coarse gate selects a super-expert group, secondary gate routes within the group. Reduces gating matrix size from O(N) to O(√N) per stage.

**MaxScore Routing:** Formulates expert selection as minimum-cost maximum-flow optimization, explicitly trading off expert capacity, token assignment, and communication costs (arXiv 2507.11181).

**MixER:** Augments gating network with context vector ξ, replaces softmax-weighted fusion with K-means-inspired discrete selection.

**Expert Choice vs. Token Choice:** Reverses assignment dynamic — experts pull tokens within fixed computational budgets rather than tokens pushing to experts.

### Key Finding on Routing Complexity

Empirical benchmarks indicate randomly initialized, frozen routers can perform on par with adaptive learned routers, challenging the assumption that complex dynamic routing is strictly necessary (arXiv 2507.11181).

---

## Training Stability

### Auxiliary Load-Balancing Loss

The foundational technique: L_balance = α · Σᵢ fᵢ · Pᵢ, where fᵢ = fraction of tokens assigned to expert i, Pᵢ = average gate probability for expert i. Penalizes skewed token distribution, enforces uniform workload allocation (arXiv 2507.11181).

### Stability Techniques

- **Stochastic gating + noisy top-k** — maintain exploration dynamics throughout training
- **Orthogonality constraints** (Orthogonal MoE) — enforce pairwise weight orthogonality to prevent expert redundancy
- **Entropy-minimizing regularizers** — promote low-overlap, semantically aligned routing
- **Capacity factor tuning** — structured optimization of tokens-per-expert limits
- **Mutual distillation** — cross-expert knowledge transfer mitigates narrow learning scopes
- **Parameter-efficient freezing** — freeze shared layers/routing weights, update lightweight adapters or expert heads

---

## Verified Models & Specifications

| Model | Total Params | Active Params | Experts | Top-k | Source |
|-------|-------------|---------------|---------|-------|--------|
| Mixtral 8x7B | 47B | 13B | 8 | 2 | arXiv 2401.04088 |
| GLaM (Google) | 1.6T | 48B | 64 | 2 | Du et al. 2021 |
| DeepSeekMoE 16B | 16.4B | ~6.5B (40% compute) | 8+ | 2 | DeepSeek GitHub |
| Qwen3-VL 30B-A3B | 30B | 3B | — | — | arXiv 2507.11181 |
| Qwen3-VL 235B-A22B | 235B | 22B | — | — | arXiv 2507.11181 |
| Llama 4 | — | — | MoE | — | Apr 2025 release |
| Mistral-8x22B | — | — | 8 | — | arXiv 2507.11181 |

### Mixtral 8x7B Benchmark Results (arXiv 2401.04088)

- **Outperforms Llama 2 70B** on mathematics, code generation, and multilingual benchmarks
- **Outperforms GPT-3.5 Turbo** on human benchmarks (Instruct variant)
- Trained on 32K context window, Apache 2.0 licensed
- Faster inference at low batch sizes, higher throughput at large batch sizes

### General Benchmark Findings (LibMoE platform, arXiv 2507.11181)

- Five SOTA MoE algorithms across 3 LLMs and 11 datasets: algorithmic selection matters less than assumed; primary advantage is consistent efficiency, not raw accuracy spikes
- MoCaE calibration framework yields up to +2.5 AP on COCO when expert reliability scores are calibrated before aggregation
- MoE achieves performance comparable to dense models while activating ~10x fewer parameters per token

---

## 2025-2026 Industry Convergence

Contemporary MoE models (Qwen3-MoE, Mistral-8x22B, Jamba, Llama 4, Claude 3.5 Sonnet) show convergence toward:

1. **Static top-k routing** with fixed-capacity experts
2. **Quantized MoE layers** integrated with expert dropout for inference overhead reduction
3. **Similarity-preserving load-balancing objectives** for architectural stability
4. **Fused attention kernels** and low-overhead memory prefetching
5. **Hardware-aligned sparse activation patterns** for tensor core utilization

The field has shifted from maximizing parameter counts to optimizing routing reliability, deployment efficiency, and multimodal latency-quality trade-offs (arXiv 2507.11181, arXiv 2602.08019).

---

## Failure Modes

- **Expert collapse** — one or few experts dominate routing, others starve
- **Routing bottlenecks** — gating network becomes throughput limiter at scale
- **Capacity saturation** — tokens dropped when expert capacity exceeded (Switch Transformer "drop overflow" design)
- **Representational redundancy** — experts converge to similar functions without proper regularization
- **Space inefficiency** — all parameters must be loaded during inference despite sparse activation (ResMoE addresses this via space-efficient compression, ACM DL 2025)

---

## Primary Sources (8 verified)

1. arXiv 2507.11181 — "Mixture of Experts in Large Language Models: A Comprehensive Review" (2025)
2. arXiv 2401.04088 — "Mixtral of Experts" (Mistral AI, 2024)
3. arXiv 2602.08019 — "The Rise of Sparse Mixture-of-Experts: A Survey" (Feb 2026)
4. DeepSeek-MoE GitHub — "Towards Ultimate Expert Specialization" (DeepSeek AI)
5. ACM DL — ResMoE: Space-efficient Compression of MoE LLMs (2025)
6. LibMoE benchmarking platform — cross-algorithm MoE evaluation (2025)
7. Du et al. — GLaM: Scaling NLP with Generalist Language Models (Google, 2021)
8. Fedus et al. — Switch Transformers: Scaling to Trillion Parameter Models (Google, 2021/2022)

---

## Cross-Domain Links

- [local-inference-optimization-2026](local-inference-optimization-2026.md) — MoE naturally compresses per-token compute; quantization of expert layers compounds with PTQ advances
- [ai-inference-compiler-stack](ai-inference-compiler-stack.md) — routing-aware compilation: TVM/IREE must handle dynamic expert dispatch, not just static graph optimization
- [fpga-inference-acceleration](fpga-inference-acceleration.md) — conditional compute maps to hardware multiplexing; FPGA switching can implement expert routing at sub-ns latency
- [reasoning-models-chain-of-thought](reasoning-models-chain-of-thought.md) — MoE gating as implicit System 1/System 2 routing: simple tokens routed to fast experts, complex tokens to reasoning experts

---

## Integration Notes

MoE architectures are the dominant trend in 2025-2026 foundation models. For local deployment, Mixtral 8x7B (47B total, 13B active) is the most accessible open-weight MoE. Key integration considerations:
- Expert parallelism requires careful memory placement across GPUs
- Quantization of expert weights (INT4/INT8) further reduces active memory
- Routing overhead is ~1-2% of total inference cost when properly optimized
- Capacity factor tuning is critical: too low drops tokens, too high wastes compute
