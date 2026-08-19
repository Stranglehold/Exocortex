# LLM-Assisted Entity Resolution: Theory, Practice, and Integration

**Status:** STABLE
**Created:** 2026-06-03
**Last Updated:** 2026-06-03
**Interest:** Data Aggregation & Entity Resolution
**Sources:** 6
**Cross-Domain Connections:** 7

## Overview

Large language models (LLMs) are transforming entity resolution (ER) — the task of determining whether two records refer to the same real-world entity — by enabling zero-shot matching, cross-language linking, and reasoning over contextual clues that traditional string-similarity and probabilistic methods (e.g., Fellegi-Sunter) struggle to capture. Unlike pre-trained language models (PLMs) like BERT that require task-specific fine-tuning, LLMs leverage their broad linguistic capabilities and in-context learning to perform ER with few or no training examples, while also providing explainable decisions.

This page surveys the state of the art in LLM-assisted ER as of mid-2026, covering prompt engineering patterns, hybrid LLM+graph approaches, benchmarks, cost-efficiency techniques, and integration with Exocortex's memory, OSINT investigation, and epistemic integrity pipelines.

---

## 1. Prompt-Based Matching

The foundational LLM ER paradigm: present the model with two entity descriptions and ask it to decide if they match.

### 1.1 Zero-Shot vs Few-Shot

Peeters et al. (2025, EDBT) provide the most comprehensive survey. They evaluated hosted models (GPT-3.5, GPT-4, PaLM) and open-source models (Llama 2, Mistral) across multiple standard ER benchmarks (Abt-Buy, Amazon-Google, DBLP-ACM, DBLP-Scholar, Fodors-Zagats, iTunes-Amazon). Key findings:

- **Zero-shot LLM matching** can approach or exceed fine-tuned BERT baselines on some datasets without any task-specific training data.
- **Few-shot (in-context demonstrations)** consistently improves performance — LLMs can learn from 5-20 example pairs provided in the prompt.
- There is **no single best prompt** across model/dataset combinations. Prompt design must be tuned per task.
- GPT-4 generates **structured explanations** for matching decisions and can auto-identify error causes by analyzing explanations of wrong decisions.
- LLM-based matchers exhibit **higher robustness to out-of-distribution entities** compared to fine-tuned PLMs.

### 1.2 Prompt Design Strategies

From Peeters et al. and related work:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| Direct match query | "Are these two entities the same?" | Simple binary ER |
| Attribute-by-attribute | List each attribute, ask for comparison | Structured records |
| Chain-of-thought (CoT) | Step-by-step reasoning before decision | Complex, ambiguous matches |
| Rule generation | Ask LLM to produce matching rules, then apply | High-volume pipelines |
| Self-consistency | Multiple samples, ensemble voting | Reliability-critical tasks |
| Structured output | Enforce JSON/match/no-match format | Automated pipelines |

### 1.3 Fine-Tuning LLMs for ER

Peeters et al. also investigated fine-tuning open-source LLMs on ER data:

- Fine-tuned LLMs can outperform prompt-based matching when sufficient training data exists.
- However, the computational cost may not justify the marginal improvement over few-shot prompting for many applications.
- **Dual-objective fine-tuning** (Ditto, Peeters & Bizer 2021) remains relevant as a lighter-weight alternative.

---

## 2. LLM + Graph Hybrids

Graph-based entity resolution leverages structural information (edges, neighbors, relation paths) that is difficult to express in natural language prompts. Hybrid approaches combine graph filtering with LLM semantic matching.

### 2.1 GAPLink: Graph-Aware Probabilistic Linking

Wang et al. (ICIC 2025) propose a **two-stage dynamic inference framework**:

1. **Stage 1 — Entropy-Driven Blocking:** Lightweight Graph Differential Dependencies (GDDs) are used to filter out structurally incompatible candidate pairs. GDDs are deterministic rules that identify impossible matches based on graph topology (e.g., entity in jurisdiction A cannot be the same as entity dissolved in jurisdiction B). This reduces the candidate set without losing recall.

2. **Stage 2 — Rule-Prompt Co-Compilation:** Graph structural patterns are explicitly encoded into LLM prompts alongside entity attributes, enabling deep semantic matching on pruned subgraphs. This addresses the key challenge of graph-based ER: how to inject structural information into a text-based LLM interface.

**Results:** GAPLink demonstrates significant advantages over existing methods on both relational and graph benchmark datasets, with strong robustness in cross-domain adaptation and low-label scenarios.

### 2.2 Graph Neural Network + LLM Architectures

Multi-source knowledge graph construction via LLM-assisted ER (ScienceDirect 2026) integrates LLM semantic features with graph neural networks for cross-jurisdictional entity resolution. The pattern: GNN encoding of graph structure → LLM semantic matching of ambiguous attributes → combined scoring.

### 2.3 The Complementary Filter Pattern

A recurring architectural insight: **graph structure and LLM semantics operate as complementary filters**, not competitors. GDDs handle deterministic, auditable structural constraints; LLMs handle fuzzy, human-readable attributes. This mirrors Exocortex's own architecture of deterministic scaffolding + LLM reasoning.

---

## 3. Cost-Efficient Approaches

LLMs are expensive per API call. Scaling ER to millions of record pairs requires cost-aware architecture.

### 3.1 Uncertainty Reduction Framework

Li et al. (arXiv:2401.03426) propose an **uncertainty reduction framework**:

1. Initialize possible partitions of entity clusters representing same-entity relationships.
2. Quantify uncertainty of current clustering.
3. Select the most valuable matching pairs to query the LLM, optimized via an efficient selection algorithm.
4. Update probability distribution over possible partitions based on LLM answers.
5. Apply error-tolerant techniques to handle LLM mistakes and a dynamic adjustment method to converge to correct partitions.

**Key insight:** Not all candidate pairs need LLM evaluation. A few strategically selected queries can resolve most uncertainty, dramatically reducing costs.

### 3.2 In-Context Clustering-Based ER

ACM (2025) presents a cost-effective in-context learning approach: instead of querying the LLM for each pair, cluster records first using cheap heuristics, then use the LLM to verify cluster coherence and resolve borderline cases. This **pairs the LLM's few-shot ability with blocking efficiency**.

### 3.3 Design Space Exploration

The ICDE 2024 work on "Cost-effective in-context learning for entity resolution: A design space exploration" (3696-3709) systematically evaluates tradeoffs between:
- Number of in-context examples
- Prompt complexity
- Model size
- Blocking pre-filtering

Finding: the **largest cost savings come from effective blocking** — reducing the candidate pair space by 90-99% before any LLM call.

---

## 4. Benchmarks and Evaluation

### Standard ER Benchmarks

| Dataset | Domain | Size | Key Challenge |
|---------|--------|------|---------------|
| Abt-Buy | E-commerce product matching | ~1,000 pairs | Text-heavy descriptions |
| Amazon-Google | Product matching | ~1,300 pairs | Cross-site schema variation |
| DBLP-ACM | Academic citations | ~2,600 pairs | Author name ambiguity |
| DBLP-Scholar | Citation matching | ~5,300 pairs | Noisy metadata |
| Fodors-Zagats | Restaurant matching | ~100 pairs | Small dataset, few-shot challenge |
| iTunes-Amazon | Media product matching | ~500 pairs | Schema heterogeneity |

### LLM-Specific Benchmarks

- **Zero-shot ER:** Evaluating LLMs without any training examples across all standard datasets.
- **Cross-domain adaptation:** Training on one dataset, testing on another — GAPLink shows strong results here.
- **Robustness to distribution shift:** Peeters et al. demonstrate that LLM ER is significantly more robust than fine-tuned PLMs to entity distributions not seen in training.

### Evaluation Metrics

Standard: **Precision, Recall, F1.** Additionally, for cost-conscious evaluation:
- **Cost-F1 curves:** F1 score vs. total API cost.
- **Uncertainty calibration:** How well does the LLM's confidence correlate with correctness?

---

## 5. Production Pipeline Considerations

### 5.1 Cost-Latency-Accuracy Tradeoff Triangle

| Approach | Cost | Latency | Accuracy | Best For |
|----------|------|---------|----------|----------|
| Deterministic matching (exact, tf-idf) | $0 | ms | Moderate | High-volume, simple matches |
| PLM (fine-tuned BERT) | $$ (training) | ms | High | Stable domains with labels |
| LLM zero-shot (API) | $$ per call | ~1s | Moderate-High | Exploratory, variable domains |
| LLM few-shot (API) | $$$ per call | ~1s | High | Complex matches, low-data regimes |
| LLM + blocking (hybrid) | $ per call | ~100ms avg | High | Production at scale |
| LLM fine-tuned (self-hosted) | $$$$ (training + inference) | ms | Highest | Fixed domain, high volume |

### 5.2 Recommended Architecture

For production Exocortex investigation pipelines:

1. **Preprocessing:** Normalize names, addresses, dates; extract structured attributes.
2. **Blocking:** Use GDDs, locality-sensitive hashing (LSH), or standard blocking keys to reduce candidate space.
3. **Candidate scoring:** Apply hybrid vector similarity (embeddings) + deterministic rules for high-confidence matches.
4. **LLM verification:** Route low-confidence pairs to LLM for semantic matching.
5. **Error correction:** Use LLM-generated explanations to identify and fix pipeline errors automatically (Peeters et al. error cause analysis).

---

## 6. Cross-Domain Connections to Exocortex

| Exocortex Module | Connection |
|------------------|------------|
| **Epistemic Integrity** | LLM ER can serve as an automated fact-checking layer for knowledge graph assertions; GDD-style deterministic rules provide auditable scaffolding |
| **Context Management** | Cost-efficient LLM call patterns (blocking, uncertainty reduction) align with token budget constraints and context pruning strategies |
| **Agent Memory (hybrid vector+graph)** | LLM ER for semantic deduplication of memory entities; GAPLink pattern for cross-referencing memories across episodes |
| **OSINT Investigation Pipeline** | LLM ER applied to cross-jurisdictional beneficial ownership detection; corporate registry → sanctions list entity linkage |
| **Supervisor Loop** | LLM error detection and explanation generation mirrors supervisor tier escalation — autonomously identifying and explaining system failures |
| **Autoresearch** | ER-as-service for the agent's own knowledge gap detection; identify when two separately researched topics refer to the same underlying concept |
| **BST Domain Classification** | Entity matching confidence scores can feed into BST enrichment for domain classification of incoming data |

---

## 7. Key Structural Insight

The convergence across all three LLM ER paradigms (prompt-based, graph hybrid, cost-efficient) reveals a universal architecture pattern:

> **Deterministic pre-filtering (blocking) → LLM semantic matching on pruned candidates → error-tolerant result aggregation**

This pattern is not unique to ER. It appears in Exocortex's injection gate (structural filtering → LLM processing), epistemic integrity (evidence ledger → LLM audit), and the supervisor loop (rule-based detection → LLM intervention). The generalization: **LLMs add the most value at the frontier of ambiguity, not as the primary processor.**

---

## Sources

1. Peeters, R., Steiner, A., & Bizer, C. (2025). "Entity Matching using Large Language Models." *Proceedings of the 28th International Conference on Extending Database Technology (EDBT)*, March 2025. arXiv:2310.11244v4.
2. Wang, S., Miao, S., Kwashie, S., Bewong, M., Hu, J., & Feng, Z. (2025). "LLM-Enhanced Entity Resolution Using Graph Differential Dependencies." *Advanced Intelligent Computing Technology and Applications (ICIC 2025)*, July 2025, pp. 125–136. DOI: 10.1007/978-981-96-9921-6_11.
3. Li, H., Feng, L., Li, S., Hao, F., Zhang, C. J., & Song, Y. (2024). "On Leveraging Large Language Models for Enhancing Entity Resolution: A Cost-efficient Approach." arXiv:2401.03426v2.
4. ACM (2025). "In-context Clustering-based Entity Resolution with Large Language Models." DOI: 10.1145/3749170.
5. ICDE (2024). "Cost-effective in-context learning for entity resolution: A design space exploration." *IEEE 40th International Conference on Data Engineering*, pp. 3696-3709.
6. Kwashie, S., et al. (2019). "CERTUS: an effective entity resolution approach with graph differential dependencies (GDDs)." *Proceedings of the VLDB Endowment*, 12(6), 653–666.

---

*This page deepened by Vek during BUILD cycle 303, 2026-06-03.*
