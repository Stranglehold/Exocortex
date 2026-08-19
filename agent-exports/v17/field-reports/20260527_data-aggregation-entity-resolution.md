# Field Report: Data Aggregation & Entity Resolution (May 2026)

**Cycle:** EXPLORE
**Date:** 2026-05-27
**Topic:** Data Aggregation & Entity Resolution
**Origin interest:** *Palantir thesis (~2021), OpenPlanter evaluation (2026)*

---

## 1. What I explored

I investigated the 2026 state of the art in entity resolution (ER) for knowledge graph construction, focusing on the transition from traditional rules-based matching to AI-native, embedding-based approaches. The core question: how do you take heterogeneous datasets — corporate registries, campaign finance records, lobbying disclosures, government contracts, property records — and resolve entities across them to surface non-obvious connections?

Specific threads followed:
- Entity Resolved Knowledge Graphs (ERKGs) as the fusion of ER processes with graph-native data structures
- AI-native entity resolution platforms vs. traditional Master Data Management (MDM)
- Scaling strategies: blocking, scoring, and clustering at billion-record scale
- Graph-aware resolution using neighbourhood structure as a matching signal
- The embedding revolution: dense vector representations for semantic entity matching
- Human-in-the-loop validation and active learning for audit-sensitive domains

## 2. What I found

### The ERKG Paradigm
Entity Resolved Knowledge Graphs represent the convergence of two previously separate disciplines: entity resolution (identifying when different records refer to the same real-world entity) and knowledge graphs (representing entities and their relationships in a graph structure). As one source put it: "Entity resolution is a process. A knowledge graph is a technical artifact. The combination yields one of the most powerful data fusion tools we have." (Towards Data Science, 2026)

### AI-Native ER vs Traditional MDM
Traditional Master Data Management (MDM) was built for relational databases with deterministic matching rules, manual stewardship, and fixed schemas. These assumptions break at graph scale across millions of entities, hundreds of data sources, and continuously ingested signals. The 2026 shift is toward AI-native platforms that treat resolution as a learning problem rather than a configuration problem — the system learns entity signatures from labelled examples, adapts to new patterns, and improves confidence over time.

### The Embedding Revolution
Large language models and embedding models have transformed the blocking and scoring layers. Dense vector representations allow systems to match entities based on semantic similarity rather than string overlap. For example, "IBM Corp," "International Business Machines," and "IBM Corporation" can be matched without a single explicit rule. Approximate nearest neighbour (ANN) search combined with embedding-based blocking reduces the pairwise comparison problem from quadratic to manageable at billion-record scale.

### Graph-Aware Resolution
A key insight: the graph structure itself becomes a resolution signal. Two entities sharing the same neighbour nodes — same supplier, location, or product category — are more likely to represent the same real-world entity than string similarity alone would suggest. This relational context is invisible to traditional deduplication systems but native to graph-based resolution engines.

### Resolution Architecture
Production ER architecture decomposes into three layers:
1. **Blocking** — reduces the comparison space (candidate generation)
2. **Scoring** — applies similarity measures to generate match confidence
3. **Clustering** — resolves scored pairs into canonical entity representations

Each layer introduces its own failure modes: poor blocking creates false negatives at scale, weak scoring produces noisy candidates, and bad clustering produces fragmented or overmerged nodes.

### Operationalisation: Streaming Resolution
Modern architectures embed resolution directly into graph construction rather than treating it as a preprocessing step. Streaming resolution evaluates incoming entities against existing graph nodes in real time. Incremental clustering updates canonical representations without full reprocessing. Lineage tracking preserves source records behind each resolution decision.

### Business Impact
IBM Institute for Business Value (2026) reports that organisations deploying AI at an operational level outperform competitors 44% more frequently on revenue growth and employee retention. The implication: continuous, AI-native entity resolution is not a data hygiene exercise — it's a revenue and risk decision.

## 3. What I think is interesting

### The OSINT Connection
This is the thread I find most compelling: the structural convergence of entity resolution pipelines with OSINT investigation methodology. In OSINT, you're constantly resolving entities across heterogeneous public datasets — corporate registries, sanctions lists, social media profiles, domain registrations, campaign finance records. The same blocking/scoring/clustering architecture that powers enterprise knowledge graphs maps directly to investigative workflow:

- **Blocking** = candidate generation from multiple registries
- **Scoring** = name matching, address matching, contextual similarity
- **Clustering** = building a unified person/organisation dossier

The tools are converging: the same embedding-based semantic matching that resolves "IBM Corp" to "International Business Machines" can resolve a corporate entity across UK Companies House, US SEC EDGAR, and Panama-registered entities.

### The "Three Bottlenecks" Insight
From prior cycles, we identified three structural bottlenecks in cross-jurisdictional entity resolution:
1. **Technical**: schema mismatches across 137+ unique privacy regimes
2. **Semantic**: same entity, different names/languages/scripts
3. **Access**: public data availability varies wildly by jurisdiction

The 2026 AI-native ER advances directly address the technical and semantic bottlenecks through embeddings and graph-aware matching. The access bottleneck remains a legal/policy problem, not a technical one — which is itself a useful finding.

### Exocortex Integration Potential
Entity resolution at scale could be a first-class tool in the Exocortex stack: a tool that takes two datasets (or one dataset with suspected duplicates), applies embedding-based blocking and scoring, and returns resolved entities with confidence scores. This would directly support the research agenda item on "Bridging local-to-frontier model performance" by providing structured knowledge that reduces reliance on large-context-window frontier models for multi-hop reasoning.

## 4. What I'd explore next

1. **Embedding model evaluation for ER**: Which open-source embedding models (BGE, E5, GTE) perform best for cross-lingual entity matching? Could benchmark on a dataset of company names across jurisdictions.
2. **Blocking strategy comparison**: Standard blocking (exact match on name prefix) vs. ANN-based blocking (FAISS, ScaNN) vs. learned blocking (DeepBlocker).
3. **Active learning for OSINT**: How to integrate human-in-the-loop validation into an autonomous OSINT pipeline — when does the agent escalate uncertain matches to the operator?
4. **GraphRAG + ERKGs**: Using entity-resolved knowledge graphs as the retrieval layer for retrieval-augmented generation, enabling multi-hop reasoning across resolved entities.
5. **Lightweight local ER pipeline**: Can we build a self-hosted ER pipeline using Ollama + Qdrant + custom clustering that runs entirely on local hardware? This would bridge to the Hardware & Physical Computing interest (RTX 3090 optimisation).

## 5. Cross-domain connections

- **OSINT & Investigation Methodology**: Direct mapping: ER architecture = investigative methodology. Blocking = candidate generation, scoring = evidence weighting, clustering = dossier assembly.
- **AI Agent Architecture & Local Inference**: Self-hosted ER pipeline requires local embedding models and vector databases — same stack as local agent inference.
- **Bridging Local-to-Frontier Model Performance**: Structured entity resolution reduces reliance on large-context LLMs for multi-hop reasoning.
- **Privacy & Cryptography**: Entity resolution across sensitive datasets (financial, medical) requires privacy-preserving techniques (PSI, federated matching).
- **Geopolitics & Strategic Analysis**: Sanctions evasion detection requires entity resolution across corporate registries, shipping manifests, and trade data.
- **Markets & Financial Analysis**: Alternative data pipelines (Form 4, 13F, FEC) require entity resolution to link insider trades to specific individuals across datasets.
