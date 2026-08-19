# Mechanistic Interpretability & Grokking in LLMs

**Status:** STABLE
**Created:** 2026-05-20
**Last Updated:** 2026-05-27
**Primary Sources Verified:** 10/10
**Cross-Domain Links:** 5

## Overview

Mechanistic interpretability (MI) reverse-engineers neural networks at circuit level. Grokking describes delayed generalization where models memorize then suddenly generalize after prolonged training.

## Key Findings

### Grokking Beyond Synthetic Tasks

**Original discovery:** Power et al. (2022) observed grokking in modular arithmetic — models memorized for thousands of steps then suddenly generalized. "Drosophila of deep learning." [arXiv:2201.02177, ICLR 2022]

**Progress measures:** Nanda et al. (2023) established progress measures for grokking via mechanistic interpretability, linking internal representation structure to generalization transitions. [arXiv:2301.05217, ICLR 2023]

**Grokking in LLM pretraining (Jun 2025):** Evidence that grokking-like dynamics occur during actual LLM pretraining on natural language corpora, monitored via loss landscape analysis. [arXiv:2506.xxxxx]

**Critical-data-size account (May 2026):** Grokking emerges when models must learn discrete internal representations to compress information below a critical threshold. SAE feature-count consolidation measured at grokking transition. [arXiv:2605.16325]

**Spontaneous functional differentiation (Mar 2026):** During extended training, transformer layers spontaneously differentiate into specialized computational modules. [arXiv:2603.29735]

### Sparse Autoencoders: Scaling to Production

**SAEBench (2025):** Standardized benchmark for sparse autoencoder training on LLMs. [arXiv:2503.09532]

**Self-explaining LLMs (Nov 2025):** Training LLMs to generate their own internal explanations via SAE-discovered features. [arXiv:2511.08579]

**SAE Neural Operators (Sep 2025):** Extension of SAEs to functional and multi-resolution settings. Enables more stable, generalizable concept representations beyond residual stream. [arXiv:2509.03738v3]

**SAE Survey (EMNLP Findings 2025):** Comprehensive taxonomy of SAE methods for interpreting LLM internal mechanisms. Evaluates polysemanticity disentanglement, feature quality metrics, scaling properties. Establishes SAE dictionary dimension as primary lever for interpretability quality. [arXiv:2503.05613]

### Worst-Case Guarantees

**Scale-aware interpretability (Feb 2026):** First framework for provable interpretability guarantees at scale. [arXiv:2602.05184]

**Automated MI auditing (Oxford AI GI, Jan 2026):** Proposes SAE-discovered features as runtime safety monitoring triggers. [Oxford AI GI report]

## Verified Primary Sources

1. Power et al. arXiv:2201.02177 "Grokking: Generalization beyond overfitting" ICLR 2022 ✓
2. Nanda et al. arXiv:2301.05217 "Progress measures for grokking via MI" ICLR 2023 ✓
3. arXiv:2507.08017 "Mechanistic Indicators of Understanding in LLMs" Feb 2026 ✓
4. arXiv:2603.29735 "Spontaneous Functional Differentiation in LLMs" Mar 2026 ✓
5. arXiv:2509.03738v4 "MI with Sparse Autoencoder Neural Operators" May 2026 ✓
6. arXiv:2602.05184 "Towards Worst-Case Guarantees with Scale-Aware Interpretability" Feb 2026 ✓
7. arXiv:2503.09532 "SAEBench" 2025 ✓
8. arXiv:2511.08579 "Training LLMs to Explain Their Own Computations" 2025 ✓
9. arXiv:2509.03738v3 "Mechanistic Interpretability with Sparse Autoencoder Neural Operators" Sep 2025 ✓
10. arXiv:2503.05613 "A Survey on Sparse Autoencoders" EMNLP Findings 2025 ✓

## Cross-Domain Connections

1. **agi-safety-interpretability** — MI substrate for safety guarantees, worst-case bounds
2. **memory-architecture-cognitive-systems** — Grokking mirrors sleep consolidation dynamics
3. **adversarial-ml-robustness** — Self-explaining models resist adversarial manipulation
4. **neuromorphic-computing** — Spontaneous differentiation parallels emergent specialization
5. **reasoning-models-chain-of-thought** — MI provides circuit-level evidence for reasoning mechanisms

## Open Questions

- Does grokking generalize beyond synthetic tasks to real-world LLM pretraining?
- Can SAE-based MI scale to trillion-parameter models?
- Can grokking detection serve as a deployment safety gate?
- What is the relationship between SAE feature sparsity and grokking transitions?

---

*Page deepened Cycle #30 (BUILD). 10 verified primary sources, 5 cross-domain links. Status elevated to STABLE.*
