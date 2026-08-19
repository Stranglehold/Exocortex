# Link Prediction for OSINT Entity Resolution

**Status: STABLE**
**Created: 2026-07-10**
**Last Deepened: 2026-07-10**
**Domain: OSINT & Investigation Methodology → Network Analysis, Entity Resolution**
**Interests: OSINT & Investigation Methodology, Network Analysis & Graph Theory**

---

## Summary
Link prediction is the problem of inferring missing or future edges in a network from observed structure and node attributes. In OSINT, link prediction algorithms surface non-obvious relationships—covert connections, hidden intermediaries, future associations—that are invisible to direct database queries. This page covers algorithmic approaches (distance-based, probabilistic, embedding-based, GNN-based, temporal), their application to entity resolution augmentation, integration into OSINT investigation workflows, and the 2025–2026 research frontier including LLM-enhanced KG completion and fairness-aware prediction.

---

## 1. Link Prediction Fundamentals

### Problem Statement
Given a snapshot of a graph G(V,E) at time t, predict which edges are missing (currently unobserved) or will form in the future. In OSINT terms: find the hidden relationships.

### OSINT Intelligence Value
| Domain | Link Type | Intelligence Value |
|--------|-----------|-------------------|
| Corporate networks | Beneficial ownership | Shell company detection |
| Communication graphs | Covert contact channels | Conspiracy structure |
| Financial transactions | Money flow paths | Sanctions evasion |
| Infrastructure | Co-location/shared resources | Attribution linkage |
| Social networks | Secret group membership | Insider threat |
| Maritime logistics | Vessel-to-vessel transfers | Shadow fleet coordination |
| Crypto transactions | Cross-chain laundering paths | Illicit finance tracing |
| Influence operations | Coordinated account networks | CIB campaign detection |

### Formal Notation
- **Observed graph:** G_obs = (V, E_obs) where E_obs ⊂ E_all (the complete edge set)
- **Missing edges:** E_missing = E_all \ E_obs
- **Future edges:** E_future(t+Δt) given G(t)
- **Training split:** For supervised LP, edges are split temporally or randomly into train/validation/test sets, with the test set containing true but held-out edges and an equal number of randomly sampled non-edges.

---

## 2. Algorithmic Approaches

### 2.1 Distance-Based (Heuristic) Methods
Fast, interpretable, no training required. Use local neighborhood similarity as edge-likelihood proxy.

| Method | Formula / Logic | Strengths | Weaknesses |
|--------|-----------------|-----------|------------|
| Common Neighbors | Γ(u) ∩ Γ(v) | Simple baseline | Ignores degree distribution |
| Jaccard Coefficient | \|Γ(u) ∩ Γ(v)\| / \|Γ(u) ∪ Γ(v)\| | Normalizes by union | Still purely local |
| Adamic-Adar | Σ_w (1/log\|Γ(w)\|) where w ∈ common neighbors | Weights rare common neighbors | No structural role awareness |
| Preferential Attachment | \|Γ(u)\| × \|Γ(v)\| | Predicts popular nodes | Ignores actual similarity |
| Katz Index | Σ_∞_l=1 β^l · (A^l)_uv | Global path counting | O(n³) naive |
| SimRank | Recursive: two nodes similar if linked to similar nodes | Structural equivalence | Computationally expensive |

**OSINT Use:** Baseline screening when graph is too large for deep models; explanatory sanity check on GNN predictions.

### 2.2 Probabilistic Models
Model the graph generation process, estimating the probability of missing edges.

- **Stochastic Block Models (SBM):** Partition nodes into communities; edge probability depends on community assignments. Useful for detecting hidden community membership—isomorphic to clustering entities into real-world organizations.
- **Exponential Random Graph Models (ERGM):** Maximum entropy models where network statistics (edge count, triangles, degree distribution) are sufficient statistics. Snijders et al. (2006) provides theoretical foundations.
- **TGSBM (Transformer-Guided SBM, Yang et al. 2026, arXiv:2601.20646):** Combines overlapping SBM with sparse Graph Transformer attention, achieving mean rank 1.6 under HeaRT protocol, 6× faster training. Preserves interpretability through explicit community posteriors while capturing non-local dependencies. **Relevance to OSINT:** Interpretable community structures map to real-world organizations; overlapping memberships model multi-hat individuals.

### 2.3 Embedding-Based Methods
Map nodes (and sometimes relations) to continuous vector spaces where proximity predicts link existence. Dominant in knowledge graph completion.

| Model | Geometry | Scoring Function | Key Innovation |
|-------|----------|-----------------|----------------|
| TransE (Bordes 2013) | Euclidean | ‖h + r − t‖ | Translational invariance |
| RotatE (Sun 2019) | Complex | ‖h ◦ r − t‖ | Symmetry/antisymmetry patterns |
| ComplEx (Trouillon 2016) | Complex | Re(⟨h, r, t̄⟩) | Asymmetric relations |
| TuckER (Balazevic 2019) | Euclidean | W ×₁ h ×₂ r ×₃ t | Full Tucker decomposition |
| Mixed-Geometry Tensor (Yusupov et al. 2025, arXiv:2504.02589) | Euclidean + Hyperbolic | Tucker + hyperbolic correction | SOTA accuracy with fewer params; hyperbolic term better captures hierarchical structures (e.g., corporate ownership trees) |

**OSINT Use:** Knowledge graph embeddings can propose missing beneficial ownership links, undisclosed board relationships, or hidden supply chain intermediaries.

### 2.4 Graph Neural Networks (GNNs)
End-to-end learnable link prediction using message passing to aggregate neighborhood features.

**Key Architectures:**
- **SEAL (Zhang & Chen, NeurIPS 2018):** Enclosing subgraph extraction + GNN classification. Learns from local subgraph patterns rather than node embeddings. Strong on benchmarks.
- **GraphSAGE (Hamilton et al., NeurIPS 2017):** Inductive learning—train on one graph, predict on unseen nodes. Critical for OSINT where new entities appear continuously.
- **GAT (Veličković et al., ICLR 2018):** Attention-weighted neighbor aggregation; explainable through attention weights.
- **SAT (Structure-Aware Alignment-Tuning, 2025, arXiv:2505.03608):** LLM-enhanced framework using hierarchical knowledge alignment + structural instruction tuning. 8.7–29.8% improvement on link prediction over prior LLM-based KGC. Bridges the gap between graph structure and natural language representations.
- **Temporal Graph Networks (Rossi et al., arXiv:2006.10637):** Dynamic graphs with memory modules; captures evolving entity relationships.

**OSINT pipeline integration:** GNNs are the missing link between fragmented entity records. As noted in the field report *OSINT Network Analysis & Graph Intelligence* (2026-06-28), the 2026 trend is moving from static graph analysis ("what does the network look like?") to dynamic graph learning ("what will the network become?") and causal graph reasoning ("why did this network form?").

### 2.5 Dynamic and Temporal Link Prediction
Real-world OSINT networks evolve—entities dissolve, merge, rebrand, form new associations. Temporal link prediction captures this.

**Approaches:**
- **Snapshot-based:** Treat each time window as a static graph; apply static LP separately. Simple but ignores temporal dependencies.
- **Recurrent GNNs:** Node embeddings evolve via RNN/LSTM/Gated mechanisms. TGN (Rossi et al. 2020) uses memory modules.
- **Hawkes processes:** Model event arrival rates; each edge formation is a point process influenced by history.
- **Continuous-time dynamic GNNs:** Time as a continuous variable; attention over temporal neighborhood.

**OSINT Application:** Detecting when a shell company changes its beneficial owner, when a vessel reflags to evade sanctions, or when a social media account shifts from dormant to active as part of a coordinated campaign.

---

## 3. Integration with OSINT Entity Resolution

### 3.1 Augmenting Fellegi-Sunter Match Weights
Link prediction scores provide a structural prior for entity matching. When two entity records share predicted links to common third entities, the match probability increases. This is isomorphic to the Fellegi-Sunter agreement weight on a derived feature: "do these records co-occur in the same predicted neighborhood?"

**Formal integration:**
- m-probability: Probability that truly matching records co-occur in a predicted link neighborhood
- u-probability: Probability that non-matching records coincidentally share predicted links
- The link-prediction-derived weight becomes an additional field in the FS composite weight

### 3.2 Graph Completion for Sanctions Evasion Detection
Sanctions evasion networks rely on hidden intermediaries. Link prediction serves as a hypothesis generator:
1. Build a graph from known entities: corporate registries, shipping data, trade records
2. Apply link prediction to propose missing edges (e.g., undisclosed ownership links)
3. Prioritize high-confidence predictions for deeper investigation (document retrieval, HUMINT, subpoena)
4. Validate via independent sources; update graph; iterate

This is the **structural completion** pattern: use algorithmic graph completion to surface the invisible infrastructure of evasion networks. Isomorphic to the approach used by ICIJ for offshore leak investigations and to the graph ML layer in the CHANAKYA multi-layer signal correlation framework.

### 3.3 Evidence Chain Integration
Link predictions are Tier 3 (contextual gap-filling) in the OSINT Bayesian evidence hierarchy:
- **Tier 1:** Direct evidence (confirmed beneficial ownership in official registry)
- **Tier 2:** Indicative corroboration (shared phone number, overlapping address)
- **Tier 3:** Contextual gap-filling (link prediction score > threshold suggesting undisclosed relationship)

The prediction confidence becomes the Admiralty Code credibility score for that hypothesis.

### 3.4 Investigation Pipeline
1. **Collection** — gather entities from OSINT sources
2. **Entity Resolution** — deduplicate and link records referring to the same real-world entity
3. **Graph Construction** — resolved entities become nodes; relationships become typed edges
4. **Link Prediction** — run algorithmic LP to propose hidden edges; rank by confidence
5. **Hypothesis Generation** — convert high-confidence predictions into investigative hypotheses
6. **Validation** — verify against independent sources before reporting

---

## 4. Tool Ecosystem

| Category | Tools | OSINT Suitability |
|----------|-------|-------------------|
| Python GNN frameworks | PyTorch Geometric (PyG), DGL (Deep Graph Library) | Best for custom models; SEAL, GAT, GraphSAGE, TGN implementations |
| Graph ML libraries | StellarGraph (scikit-learn API), NetworkX (heuristic LP) | Rapid prototyping |
| Graph databases with LP | Neo4j GDS (FastRP + logistic regression, GraphSAGE pipelines) | Production OSINT knowledge graphs |
| KG embedding | OpenKE, PyKEEN, DGL-KE | TransE/RotatE/ComplEx/TuckER for KG completion |
| Large-scale | PBG (PyTorch-BigGraph), GraphVite | Billion-node graphs |
| Dynamic graphs | TGN (PyG implementation), DySAT | Temporal LP for entity evolution tracking |

---

## 5. Research Frontiers (2025–2026)

### LLM-Enhanced Link Prediction
- **SAT (arXiv:2505.03608):** Structure-aware alignment-tuning bridges graph embeddings and natural language, achieving 8.7–29.8% improvement over prior LLM-based KGC
- **LLMs as feature extractors:** Entity descriptions encoded via LLM embeddings as node features for GNN input
- **LLMs as reasoning engines:** Generate natural-language justifications for predicted links

### Fairness-Aware Link Prediction
Standard LP evaluation uses dyadic demographic parity. Recent work (arXiv:2511.06568, 2025) shows this definition obscures subgroup disparities. A lightweight post-processing method with decoupled link predictors achieves state-of-the-art fairness-utility trade-offs. **OSINT relevance:** Avoiding algorithmic amplification of demographic biases in entity resolution.

### Evaluation Protocol Critique
Ferrari et al. (2025, arXiv:2507.16408) demonstrate that standard closed-world evaluation metrics penalize correct predictions of truly missing triples. Recommendation: move beyond single-value aggregation. **OSINT relevance:** In OSINT, the gold-standard edge set is never fully known.

### Mixed-Geometry Representations
Yusupov et al. (2025, arXiv:2504.02589): Combining Euclidean and hyperbolic geometries achieves SOTA link prediction with fewer parameters. Hyperbolic space better captures hierarchical structures—critical for corporate ownership trees.

### Interpretable Generative Models
**TGSBM (Yang et al. 2026, arXiv:2601.20646):** Transformer-guided overlapping SBM that preserves interpretable community structure while achieving mean rank 1.6 on benchmark.

---

## 6. Cross-Domain Connections
1. **[[graph-neural-networks-entity-resolution]]** — Shared GNN architectures; link prediction is the inverse problem of entity clustering
2. **[[entity-resolution-algorithms]]** — Link prediction scores augment Fellegi-Sunter match weights
3. **[[network-analysis-graph-theory]]** — Centrality and community detection inform link prediction feature engineering
4. **[[temporal-entity-resolution]]** — Dynamic link prediction tracks entity identity changes over time
5. **[[knowledge-graph-construction-patterns]]** — Link prediction as KG completion
6. **[[sanctions-evasion-detection]]** — Graph completion reveals hidden intermediary entities
7. **[[cross-jurisdictional-entity-resolution]]** — Hidden cross-border relationships surfaced through link prediction
8. **[[osint-data-fusion-evidence-chains]]** — Link predictions as Tier 3 evidence with confidence scoring
9. **[[counterintelligence-analysis-frameworks]]** — Missing link patterns as counter-deception indicators
10. **[[anti-bot-evasion]]** — Behavioral graph link prediction for coordinated inauthentic behavior detection
11. **[[agentic-ai-self-learning]]** — Autonomous link prediction during idle cycles
12. **[[geolocation-osint]]** — Co-location link prediction: shared infrastructure, overlapping lease data
13. **[[entity-resolution-agent-safety]]** — Entity binding failures partially addressable through structural link prediction
14. **[[intelligence-agency-attribution-methodology]]** — CHANAKYA Graph ML layer correlation as structural link analysis

---

## 7. References
1. Liben-Nowell & Kleinberg (2007) — "The Link-Prediction Problem for Social Networks" (JASIST), foundational survey
2. Zhang & Chen (2018) — "Link Prediction Based on Graph Neural Networks" (NeurIPS), SEAL architecture
3. Rossi et al. (2020) — "Temporal Graph Networks for Deep Learning on Dynamic Graphs" (arXiv:2006.10637)
4. Lü & Zhou (2011) — "Link Prediction in Complex Networks: A Survey" (Physica A), comprehensive methodological taxonomy
5. Hamilton et al. (2017) — "Inductive Representation Learning on Large Graphs" (NeurIPS), GraphSAGE
6. Snijders et al. (2006) — "New Specifications for Exponential Random Graph Models" (Sociological Methodology)
7. Yusupov, Rakhuba & Frolov (2025) — "Knowledge Graph Completion with Mixed Geometry Tensor Factorization" (arXiv:2504.02589)
8. SAT Framework (2025) — "Structure-Aware Alignment-Tuning for LLM-Enhanced Knowledge Graph Completion" (arXiv:2505.03608)
9. Yang et al. (2026) — "TGSBM: Transformer-Guided Stochastic Block Model for Link Prediction" (arXiv:2601.20646)
10. Ferrari et al. (2025) — "Knowledge Graph Completion: A Critical Evaluation" (arXiv:2507.16408)
11. Fairness LP (2025) — "On Fairness of Link Prediction" (arXiv:2511.06568)
12. NetworkX documentation — link_prediction module reference
13. Neo4j Graph Data Science Library — FastRP, GraphSAGE link prediction pipelines
14. PyTorch Geometric documentation — SEAL, GCN, SAGE, GAT, TGN implementations
15. Exocortex field report — "OSINT Network Analysis & Graph Intelligence" (2026-06-28)
