# Entity Resolution Algorithms — 2026 State of the Art

**Status: STABLE**
**Created: 2026-07-14**
**Domain: Entity Resolution / Record Linkage / OSINT Methodology**
**Cross-domain: OSINT, Identity Resolution, Privacy, Multi-Agent Systems, Financial Intelligence**

---

## Overview

Entity Resolution (ER) is the computational problem of determining whether two or more records refer to the same real-world entity despite variations, errors, or deliberate obfuscation in their representations. In OSINT investigations, ER is the linchpin connecting fragmented data — social media profiles, corporate registries, breach databases, financial records — into a unified picture.

The field in 2025-2026 is undergoing a paradigm shift from traditional Fellegi-Sunter probabilistic pipelines to hybrid architectures combining LLM-native approaches, graph neural networks, and privacy-preserving computation. Three dominant research directions have converged.

---

## 1. Probabilistic Record Linkage (Classical Foundation)

### 1.1 Fellegi-Sunter Framework

The foundational mathematical framework for entity resolution remains Fellegi & Sunter (1969). Records are compared across attributes, and the decision boundary separates matches, non-matches, and potential matches.

**Core components:**
- **Blocking**: Reduce the O(n²) comparison space by grouping records into blocks sharing common attribute values (Soundex, double metaphone, n-gram blocking)
- **Comparison vector**: For each candidate pair, compute agreement/disagreement across attributes
- **Match/mismatch probabilities (m/u)**: m = probability attributes agree given true match; u = probability attributes agree by chance
- **Decision rule**: Composite weight = Σ log₂(mᵢ/uᵢ); classify based on upper/lower thresholds

**OSINT weighting examples (from breach identity linkage):**

| Attribute | Match Weight | Rationale |
|-----------|-------------|-----------|
| SSN exact match | >20 | Near-unique identifier |
| Password hash match | >15 | High entropy; strong linkage |
| Email exact match | >10 | Typically unique per individual |
| Phone exact + area code | >8 | High uniqueness; less stable than email |
| Username + birth year | >6 | Moderate; false matches in common names |
| IP address match | >5 | Shared infrastructure; requires temporal proximity |

### 1.2 Production Implementations

| Tool | Language | Approach | Scale | Notable Users |
|------|----------|----------|-------|---------------|
| **Splink** | Python/SQL | Fellegi-Sunter, EM estimation | Millions | UK Government (MoJ), ONS |
| **Zingg** | Java/Python | ML-based blocking + matching | Enterprise | Multi-lingual; Spark-native |
| **dedupe** | Python | Active learning + FS | 100K+ | Investigative journalism (ICIJ) |
| **Record Linkage Toolkit** | Python | Classic FS | Moderate | Academic; pandas-native |
| **OpenSanctions Pairs** | Python | LLM-based (2026) | Millions | Sanctions screening; investigative |

---

## 2. Neural Entity Resolution (Deep Learning)

### 2.1 Cross-Attention Architectures

**CrossER** (2025-2026): Cross-attention between record pairs enables the model to learn which attribute alignments matter without manual feature engineering. Unlike Siamese networks (which encode records independently), cross-attention models the interaction between records directly.

- Learns attribute-level alignment weights from training data
- Handles schema heterogeneity — resolves "Company Name" ↔ "Organization" mapping automatically
- Outperforms traditional FS on dirty, multi-lingual datasets

### 2.2 Graph Neural Networks for Entity Resolution

GNNs model the ER problem as a graph where nodes are records and edges are candidate matches. Message-passing propagates resolution decisions through the graph.

| Architecture | Mechanism | 2026 Advances |
|-------------|-----------|---------------|
| **GraphSAGE** | Inductive node embeddings | Applied to corporate registry deduplication |
| **GAT (Graph Attention)** | Weighted neighbor aggregation | Learns which neighboring records most influence this match decision |
| **Temporal GNNs** | Time-aware embeddings | Dynamic relationship detection; entities evolve over time |
| **Entity Resolution GNN** | Joint embedding + clustering | arXiv 2602.05514: temporal graph networks for entity linkage |

### 2.3 Sentence-BERT / Dense Retrieval Approaches

Pre-trained language models (SBERT, E5, BGE) encode record attributes into dense vectors. Cosine similarity between embeddings replaces string-matching heuristics. Blocking uses approximate nearest neighbor (FAISS, ScaNN) rather than exact key matching.

---

## 3. LLM-Based Entity Resolution (2025-2026 Frontier)

### 3.1 LLM-as-Judge Paradigm

The dominant 2026 pattern: present two records to an LLM with a structured prompt asking it to classify match/no-match, with chain-of-thought reasoning.

**Key findings:**
- **GPT-4 / Claude 3.5 Sonnet**: 90-95% accuracy on clean corporate registry matching; significant degradation on adversarial obfuscation
- **OpenSanctions Pairs** (arXiv 2603.11051): LLM-based ER in production for sanctions list deduplication; specialized prompts reduce hallucinated matches
- **Cost considerations**: LLM-as-judge is 10-100x more expensive per pair than FS; only practical when used after aggressive blocking

### 3.2 In-Context Clustering

Rather than evaluating every pair, arXiv 2506.02509 proposes in-context clustering: pass a batch of records to the LLM and ask it to output cluster assignments directly. Reduces the O(n²) comparison problem to O(n) LLM calls.

### 3.3 Retrieval-Augmented ER

Combine dense retrieval (SBERT, ColBERT) for candidate generation with LLM for final verification. The retriever handles scale; the LLM handles precision.

---

## 4. Active Learning for Entity Resolution

Active learning reduces the labeling burden by selecting the most informative record pairs for human annotation.

### 4.1 Strategies

| Strategy | Description | OSINT Applicability |
|----------|-------------|---------------------|
| **Uncertainty Sampling** | Select pairs with match probability near 0.5 | Flag ambiguous entity merges for analyst review |
| **Query by Committee** | Multiple models disagree | Cross-reference HIBP + DeHashed + IntelX for consensus |
| **Expected Error Reduction** | Select pairs that would most reduce model error | Prioritize high-impact investigative leads |
| **Representative Sampling** | Cover the feature space evenly | Ensure diverse entity types are represented |
| **Density-Weighted** | Uncertain + in dense regions | Avoid labeling outliers; focus on typical entities |

### 4.2 Key Implementations

- **dedupe** (Python): Active learning ER for investigative journalism; used by ICIJ for Panama Papers
- **ALER** (arXiv 2601.20664, 2026): Active Learning hybrid system combining traditional FS with LLM verification
- **ALLabel** (EMNLP 2025): Three-stage active learning for LLM-based entity recognition

---

## 5. Privacy-Preserving Entity Resolution

### 5.1 Private Record Linkage (PPRL)

The need to resolve entities across organizations without exposing sensitive data has driven PPRL innovation.

| Technique | Privacy Guarantee | Overhead | 2026 Deployments |
|-----------|-------------------|----------|------------------|
| **Bloom Filter Encoding** | Cryptographic hashing | 2-5x | Americas DataHub (Anonlink CLKs, NCSES×NSF) |
| **Embedding + Laplace Noise** | ε-differential privacy | 1.5-3x | Research prototype; academic benchmarks |
| **SMPC + DP Hybrid** | Information-theoretic | 10-100x | VLDB 2025 benchmarks; federal KYC pilots |
| **FHE-based ER** | Semantic security | 1000x+ | Research only; throughput inadequate for production |
| **Synthetic Record Generation** | DP guarantee on output | 5-10x | Trade finance; sanctions screening pilots |

### 5.2 Key 2026 Advances

- **ISE_PPRL** (EDBT 2026): Hardened Bloom filter encoding against frequency-based attacks
- **REAEDP** (2025): Real-valued embedding autoencoder with differential privacy for ER
- **DP+SMPC Hybrid** (VLDB 2025): Split the problem — DP for candidate generation, SMPC for verification

---

## 6. OSINT Entity Resolution Pipeline

### 6.1 Five-Phase Architecture

```
Phase 1: Seed Discovery
  → Harvest initial identifiers: email, phone, username, domain, IP
  → Sources: surface OSINT (social media, WHOIS, corporate registries)

Phase 2: Record Gathering
  → Expand via breach databases, public records, social media scraping
  → Tools: HIBP, DeHashed, IntelX, Constella, Sherlock, Maigret

Phase 3: Blocking & Candidate Generation
  → Group records sharing common attributes (email domain, phone area code, username pattern)
  → Techniques: Soundex, double metaphone, n-gram indexing, dense retrieval (FAISS)

Phase 4: Pairwise Matching
  → Compute match probabilities using FS, neural, or LLM-based methods
  → Weighted evidence aggregation across attributes

Phase 5: Graph Construction & Entity Fusion
  → Build identity graph; apply community detection
  → Export to visualization (Gephi, Cytoscape) or knowledge graph (Neo4j)
```

### 6.2 Evidence Weight Aggregation

Combining match evidence across heterogeneous data sources follows a Bayesian updating process. Each new source (breach record, social media profile, corporate filing) updates the posterior probability of identity match.

---

## 7. Research Frontiers (2026)

### 7.1 LLM + Symbolic Hybrid Systems

Combining the precision of Fellegi-Sunter (explainable, auditable, no hallucinations) with the semantic flexibility of LLMs (handling obfuscation, multilingual variation). The LLM handles hard cases escalated by the FS pipeline.

### 7.2 Cross-Lingual Entity Resolution

Entities operating across linguistic boundaries deliberately exploit translation gaps. Multilingual embeddings (XLM-R, LaBSE) combined with LLM-based transliteration handling are closing this gap.

### 7.3 Adversarial Entity Resolution

Targets actively obfuscating their identity — using shell companies, name variations, proxy registrations — require adversarial ER methods. This converges with counterintelligence analysis: detecting deliberate deception patterns in entity representations.

### 7.4 Streaming Entity Resolution

Real-time OSINT pipelines require incremental ER: new records must be resolved against an existing entity graph without full recomputation. Event-driven architectures using Kafka/Pulsar with incremental graph updates are emerging.

### 7.5 Agentic GraphRAG for ER

Capozzi & Helbing (arXiv 2605.18770) demonstrate Agentic GraphRAG: an autonomous agent loop that constructs, queries, and refines an entity knowledge graph. Achieves 97.15% merge precision in production. The agent decides when to merge entities, when to escalate, and when to request additional evidence.

### 7.6 Batched Oracle Queries — Progressive Batched ER (pERbacco)

Balzotti, Firmani, Gagliardelli & Simonini (arXiv:2606.24407, June 2026) formalize progressive entity resolution where an oracle (LLM, crowdsorcer, set-based model) jointly resolves batches of records rather than pairwise comparisons. Key contributions:

- **NP-hardness result**: selecting an optimal sequence of batch queries to maximize match-edge discovery is NP-hard (reduction from Heaviest Subgraph Problem). An optimal solution does not always exist, unlike the pairwise case where a 2-optimal always exists.
- **pERbacco algorithm**: community-detection-guided adaptive batch selection. Heavy communities (density ≥ threshold) are detected in a similarity graph via Louvain or Leiden. Two batch types alternate:
  - *Community-batches*: disjoint batches of unqueried records from a single community, bounded by batch size. Explore new territory.
  - *Current-batches*: may include already-queried records across communities to enlarge known entities by testing representative pairs.
  - *Temperature parameter*: adaptively controls the tradeoff. Increases when current-batch returns fewer matches than community-batch average; decreases when benefit graph is sparse.
- **Benefit function**: mean cross-edge weight between candidate representatives (Equation 12) outperforms max-edge benefit (pERbac/Oracle) across 5 real datasets (Cora, Camera, Funding, WDC-80, Voters) and synthetic variants.
- **LLM oracle experiments**: GPT-5 mini as oracle on Cora, pERbacco outperforms baselines at batch sizes 2–20. Batch queries provide token efficiency: clustering b records costs one prompt, not b(b−1)/2 pairwise prompts.

**Implications for OSINT ER pipelines**: progressive batched ER algorithms can schedule LLM queries to achieve highest recall-per-dollar when resolving identity graphs across breach databases, corporate registries, and social media. The community-detection approach mirrors intelligence collection management: dense signal regions processed first, ambiguous edges deferred.

---

## 8. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Data Breach Analysis** | Breach records provide attribute weights for FS matching |
| **Financial Intelligence (FININT)** | Splink-based ER on FinCEN SAR/CTR data; Fellegi-Sunter is FinCEN Query system backbone |
| **DNS/WHOIS Investigation** | Domain registrant email → entity resolution; historical WHOIS provides temporal attribute evidence |
| **Social Media OSINT** | Cross-platform identity correlation uses probabilistic matching across username, display name, avatar hash |
| **Active Learning ER** | Same active learning loop applied to breach correlation ambiguity resolution |
| **Privacy-Preserving FL** | Federated ER enables multi-jurisdictional entity resolution without data sharing |
| **Intelligence Failure Analysis** | Entity binding failures (24-26% wrong-entity despite 0% wrong-tool) are an ER problem |
| **Multi-Agent Orchestration** | Entity-aware action gating prevents agent tool calls on wrong entities |
| **Counterintelligence** | Adversarial ER = detecting deliberately obscured entity relationships |
| **Influence Operations Detection** | IO attribution is structurally isomorphic to entity resolution (confidence-weighted multi-source corroboration) |
| **Supply Chain Network Analysis** | Corporate entity resolution across supplier networks reveals hidden dependencies |
| **Real-Time OSINT Monitoring** | Streaming ER for incremental identity graph updates in alerting pipelines |

---

## 9. References

1. Fellegi, I.P. & Sunter, A.B. "A Theory for Record Linkage." *JASA* 64(328):1183-1210, 1969.
2. Splink. UK Ministry of Justice. https://github.com/moj-analytical-services/splink
3. Zingg. ML-based entity resolution. https://github.com/zinggAI/zingg
4. dedupe. Active learning ER library. https://github.com/dedupeio/dedupe
5. Binette, O. "(Almost) All of Entity Resolution." *Science Advances*, 2024.
6. OpenSanctions Pairs. LLM-based ER. arXiv:2603.11051, 2026.
7. Kim et al. "ALER: Active Learning Hybrid System for ER." arXiv:2601.20664, 2026.
8. Capozzi & Helbing. "Agentic GraphRAG for Entity Resolution." arXiv:2605.18770, 2026.
9. In-context clustering for ER. arXiv:2506.02509, 2025.
10. ALLabel. Three-stage active learning for LLM-based ER. EMNLP 2025.
11. Americas DataHub PPRL2. Anonlink CLKs for federal statistical entity resolution. 2026.
12. ISE_PPRL. Hardened Bloom filter encoding. EDBT 2026.
13. REAEDP. Real-valued embedding autoencoder with DP. 2025.
14. DP+SMPC Hybrid PPRL. VLDB 2025.
15. Temporal GNNs for entity linkage. arXiv:2602.05514, 2026.
16. Balzotti, L., Firmani, D., Gagliardelli, L., Simonini, G. "Entity Resolution via Batched Oracle Queries." arXiv:2606.24407, June 2026.

---

## Change Log
- **2026-07-17**: Deepened with pERbacco batched oracle queries (Balzotti et al. arXiv:2606.24407). Added subsection 7.6. Status promoted to STABLE (16 refs, 12 cross-domain).

- **2026-07-14**: DRAFT created. Grounding: shared corpus v17 (entity-resolution-algorithms.md, osint-entity-resolution-methods.md, active-learning-entity-resolution.md, cross-platform-identity-correlation.md, entity-resolution-2026-state-of-the-art.md). 15 references, 12 cross-domain connections.
