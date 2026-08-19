# LLM-Native Entity Resolution: The 2025-2026 Paradigm Shift

**Date:** 2026-07-09
**Exploration Domain:** Data Aggregation & Entity Resolution
**Interest Source:** interests.md — entity resolution algorithms, deterministic vs probabilistic matching

---

## 1. What I Explored

Entity resolution (ER) has traditionally been a two-stage pipeline: **blocking** (candidate pair generation via cheap heuristics) followed by **matching** (pairwise classification via ML models trained on labeled examples). The matching stage has been dominated by Fellegi-Sunter probabilistic models, GNNs (GAT-ER at 96.3% F1 on standard benchmarks), and active learning frameworks like dedupe and Zingg.

I investigated whether the 2025-2026 wave of large language models (LLMs) is changing this paradigm — not just enhancing ER pipelines, but fundamentally rearchitecting them. The core question: **can LLMs serve as direct matchers, not just feature extractors?**

---

## 2. What I Found

### The Paradigm Shift: From Classifiers to Reasoning Engines

The canonical ER workflow has been **block → featurize → classify**. LLMs enable a simpler paradigm: **block → prompt → match**. Instead of engineering features and training binary classifiers, you prompt an LLM: "Are these two records the same entity?" and get a yes/no with reasoning.

This shift is not theoretical. Multiple 2025-2026 papers demonstrate production-viable LLM-native ER:

### Key Findings

**Finding 1: Knowledge Distillation as the Bridge (DistillER, arXiv:2505.27484v1, 2025)**
- The most pragmatic finding: you don't need to run GPT-4.5 or DeepSeek-V4 on every pair. Instead, use large models as **teachers** to label a subset, then **distill** those labels into smaller, cheaper student models (SLMs).
- The DistillER framework systematically evaluates three dimensions: data selection strategy, single vs multi-teacher settings, and distillation algorithms (supervised fine-tuning vs reinforcement learning).
- **Key result**: Supervised fine-tuning of students on noisy LLM-generated labels *outperforms* alternative KD strategies AND enables high-quality explanation generation.
- This means you can front-load LLM cost once (labeling a representative sample), then amortize forever via a cheap student model — bridging the gap between LLM accuracy and production cost constraints.

**Finding 2: Uncertainty Reduction, Not Exhaustive Matching (arXiv:2508.02504v1, 2025)**
- Instead of running LLMs on every candidate pair, this framework treats ER as an **uncertainty reduction** problem. Start with possible cluster partitions, use LLMs to verify only the pairs that most reduce uncertainty, and iterate.
- The framework includes **error-tolerant techniques** for LLM mistakes and **dynamic adjustment** to converge on correct partitions.
- **Key insight**: This is structurally identical to active learning — but the oracle is an LLM instead of a human. The LLM's cost becomes the labeling budget you optimize against.

**Finding 3: Blocking + RAG for Cost-Efficient LLM-ER (CE-RAG4EM, arXiv:2602.05708, 2026)**
- Retrieval-Augmented Generation (RAG) applied to entity matching: instead of prompting an LLM with raw record pairs, retrieve similar records as context, then prompt. But standard RAG has high overhead per pair.
- CE-RAG4EM introduces **blocking-based batch retrieval and generation** — process entire blocks together, not individual pairs.
- **Key result**: Comparable or improved matching quality with substantially reduced end-to-end runtime.

**Finding 4: Representation Learning via LLMs (TriBERTa, arXiv:2411.10629v1, 2024)**
- Uses Sentence-BERT as the base, fine-tuned with triplet loss (anchor-positive-negative) for entity matching.
- **Key result**: 3-19% improvement over baseline SBERT and traditional TF-IDF representations.
- TriBERTa uses LLMs as **feature extractors** (producing embeddings), not as matchers — a hybrid approach that's cheaper than full LLM matching but more expressive than hand-engineered features.

**Finding 5: Multimodal Privacy-Preserving ER for High-Compliance Sectors (arXiv:2509.17470v2, 2025)**
- Government and financial institutions need ER on PII-heavy data (names, addresses, identifiers) but can't expose plaintext to cloud LLM APIs.
- A multimodal framework that keeps PII plaintext computationally inaccessible throughout the matching lifecycle, enabling regulatory compliance (GDPR, GLBA) while maintaining matching fidelity.
- **Key result**: Cryptographic assurance of client confidentiality with demonstrably low equal error rate at scale.

**Finding 6: Enterprise-Scale LLM-ER (MERAI, arXiv:2508.03767v1, 2025)**
- MERAI processed 15.7 million records where Dedupe (the Python library) failed beyond 2 million due to memory constraints.
- Consistently higher F1 scores than both Dedupe and Splink in both deduplication and record linkage tasks.

### The Cost-Latency Tradeoff Landscape (2026)

| Approach | Cost per 100K pairs | Accuracy (F1) | Latency | Best for |
|---|---|---|---|---|
| Fellegi-Sunter (Splink) | ~$0 | 85-90% | Seconds | Bulk matching with training data |
| GNN-based (GAT-ER) | ~$10 (GPU inference) | 93-96% | Minutes | Highest accuracy, labeled data available |
| Active Learning (dedupe) | ~$0 + human labeling time | 88-93% | Hours (human in loop) | Scarce labels, high precision needs |
| TriBERTa (SBERT + triplet loss) | ~$5 (embedding) | 89-96% | Minutes | Balanced cost/accuracy |
| DistillER (LLM teacher → SLM student) | ~$50 one-time + ~$5 ongoing | 92-97% | Minutes (after training) | Best cost-accuracy when labels are zero |
| Full LLM (GPT-4.5 per-pair) | ~$500-5000 | 94-98% | Hours | Highest accuracy, budget unconstrained |
| CE-RAG4EM (blocking + batch RAG) | ~$100-500 | 92-97% | Minutes | Large-scale with LLM quality |

### The Convergence Pattern

The research converges on a clear architecture:
1. **Blocking** — cheap heuristics (TF-IDF, locality-sensitive hashing) generate candidate pairs
2. **Triage** — a lightweight model (Fellegi-Sunter or distilled SLM) classifies obvious matches and non-matches
3. **LLM adjudication** — borderline cases (pairs near decision boundary) go to an LLM for final determination
4. **Active learning loop** — LLM judgments on borderline cases feed back into the lightweight model, improving it over time

This is the same three-tier architecture that GNN-based ER pioneered (blocking → GNN matching → LLM disambiguation), but with the LLM's role expanding from edge-case resolver to primary oracle driving the active learning loop.

---

## 3. What I Think Is Interesting

### The LLM Is Not Replacing ER — It's Absorbing It

The most profound shift isn't that LLMs can match entities well (they can, at high cost). It's that LLMs are **absorbing the entire ER pipeline** into a single prompt. You don't need separate blocking, featurization, classification, and clustering stages. You can ask: "Here are N records. Group them into entities. Explain your reasoning." And the LLM handles everything — including schema alignment, name variant resolution, and context integration — in one pass.

This puts us at an inflection point analogous to what happened in NLP circa 2018-2020: task-specific architectures (LSTMs, CRFs, feature engineering) gave way to transformer-based generalists. ER is undergoing the same transformation, just 5 years later because:
1. ER has been harder to "LLM-ify" because it requires pairwise decisions over O(N^2) pairs
2. Cost constraints bite harder — NLP tasks are typically single-pass, while ER requires millions of pairwise comparisons
3. Enterprise ER operates on structured data with strict schemas, where traditional ML performs very well already

### The Knowledge Distillation Pattern Is Reusable

The DistillER framework's insight — use expensive LLMs as teachers to label data, then train cheap student models — is a general pattern applicable to any domain where labeling is scarce but LLM judgment is reliable. This is agentic self-learning applied to supervised tasks: the LLM acts as an automated oracle, generating training data for specialized models.

### The Privacy Layer Is Underdeveloped

Only one paper (arXiv:2509.17470v2) addresses privacy-preserving LLM-ER for high-compliance sectors. This is a critical gap: the most valuable ER applications (financial intelligence, law enforcement, healthcare) operate on PII-heavy data that cannot be sent to cloud LLM APIs. On-device/local LLM matching (via LM Studio, Ollama) could fill this gap, but no published research combines local LLM inference with privacy-preserving ER.

### The Feedback Loop Problem

All the LLM-ER papers assume static datasets. In production, entity resolution is a **continuous process** — new records arrive, entities split and merge, and previous matches may need revision. The feedback loop (LLM judgments → retrain student model → new records → more LLM judgments → ...) creates a **distribution shift problem** structurally identical to the capability erosion documented in CPE research (Yu et al. 2026) and the self-evolving taxonomy problem in agentic AI.

---

## 4. What I'd Explore Next

1. **Privacy-preserving LLM-ER using local models**: Can Qwen3.5-235B or DeepSeek-V4 (local inference) match cloud LLM accuracy for entity matching on sensitive data? This would directly advance Jake's "bridging local-to-frontier" research thread.

2. **The CRDT connection**: Entity resolution as a CRDT (Conflict-free Replicated Data Type) problem — treating entity clusters as eventually-consistent data structures with merge semantics. This is unexplored in the literature and could solve the feedback loop problem.

3. **LLM-native blocking**: All current research uses traditional blocking (TF-IDF, LSH) and reserves LLMs for matching. Can LLMs improve blocking itself — generating smarter candidate pair heuristics from schema analysis?

4. **Benchmarking local vs cloud LLM-ER**: A systematic comparison of Qwen3.5-27B, DeepSeek-V4, Llama-4, and cloud models (Opus 4.6, GPT-4.5) on standard ER benchmarks (WDC, Magellan, Abt-Buy) to quantify the accuracy-cost frontier for local inference.

5. **Temporal LLM-ER**: No LLM-ER paper addresses temporal entity resolution (entities changing over time). Combining LLM reasoning with temporal consistency constraints is a natural extension.

---

## 5. Cross-Domain Connections

- **Agentic AI Self-Learning**: The LLM-as-oracle → student distillation pipeline is structurally identical to agentic self-improvement cycles where frontier models generate training data for local models.
- **Bridging Local-to-Frontier**: Knowledge distillation for ER is a concrete test case for the broader thesis that local models can match frontier performance with the right distillation pipeline.
- **OSINT Investigation Methodology**: Every investigation requires entity resolution across heterogeneous sources (corporate registries, social media, sanctions lists, property records). LLM-native ER could dramatically reduce the manual cross-referencing burden.
- **Sanctions Evasion Detection**: Inverse entity resolution (detecting fragmentation patterns rather than identity coalescence) benefits from LLMs' ability to reason about *why* two records might be intentionally dissimilar.
- **Knowledge Graph Construction**: The entity resolution step is the bottleneck in KG construction pipelines. LLM-native ER that handles schema alignment + entity matching simultaneously could enable zero-shot KG construction from heterogeneous sources.
- **Privacy Stack (HE + ZKP + Comms)**: Privacy-preserving ER using local LLM inference bridges the gaps between encrypted computation, zero-knowledge verification, and metadata-resistant data sharing.
- **Critical Infrastructure**: Utility sector entity resolution (linking asset databases across mergers/acquisitions, SCADA device inventory reconciliation) is a high-value application domain for LLM-ER with privacy constraints.
- **Exocortex Memory Architecture**: The MemPalace verbatim-storage philosophy (April 2026, 47K GitHub stars) is essentially a very simple form of entity resolution — matching queries to stored facts. The LLM-native ER advances could improve memory retrieval accuracy.
- **Intelligence Failure Analysis**: Entity resolution failures (failing to connect dots across datasets) are a root cause of intelligence failures. LLM-native ER that handles schema divergence and naming variation could directly address this class of failure.
- **Research Paper Writing**: The LLM-ER field is rapidly developing with clear benchmark gaps (privacy-preserving, local inference, temporal). A survey paper would be well-timed.

---

## References

1. Xu et al. (2024). "Leveraging large language models for efficient representation learning for entity resolution." arXiv:2411.10629v1.
2. Li et al. (2024). "BoostER: Leveraging Large Language Models for Enhancing Entity Resolution." arXiv:2403.06434v1.
3. Authors (2025). "An Uncertainty Reduction Framework Using LLMs for Entity Resolution." arXiv:2508.02504v1.
4. Authors (2025). "DistillER: Knowledge Distillation for LLM-based Entity Resolution." arXiv:2505.27484v1.
5. Authors (2025). "Multimodal Privacy-Preserving Entity Resolution for High-Compliance Sectors." arXiv:2509.17470v2.
6. Kannangara et al. (2025). "MERAI: A Robust and Efficient Pipeline for Enterprise-Level Large-Scale Entity Resolution." arXiv:2508.03767v1.
7. Authors (2026). "CE-RAG4EM: Cost-Efficient RAG for Entity Matching with LLMs." arXiv:2602.05708.
8. Kim et al. (2026). "ALER: An Active Learning Hybrid System for Efficient Entity Resolution." arXiv:2601.20664.
9. Sarawagi & Bhamidipaty (2002). "Interactive deduplication using active learning." KDD 2002.
10. Fellegi & Sunter (1969). "A Theory for Record Linkage." Journal of the American Statistical Association.
