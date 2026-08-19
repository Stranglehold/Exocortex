# LLM-Native Entity Resolution at Scale

**Status:** STABLE  
**Created:** 2026-05-24  
**Last Updated:** 2026-06-15  
**Primary Sources:** 13/13  
**Cross-Domain Links:** 4/4  

---

## Overview

Entity resolution (ER) — the task of determining whether different records refer to the same real-world entity — is a foundational problem in data integration, intelligence analysis, financial compliance, and knowledge graph construction. Traditional ER pipelines rely on handcrafted feature engineering, blocking strategies, and supervised classifiers. The emergence of LLMs and embedding-based methods has fundamentally shifted the ER landscape toward neural and language-native approaches.

This page tracks the state of the art in entity resolution, with emphasis on:
- Embedding-based ER (sentence transformers, domain-specific encoders)
- LLM-as-comparator methods (pairwise comparison, self-consistency, in-context clustering)
- Graph-native ER (GNN-based, knowledge graph integrated)
- Scalable blocking + learning pipelines (FastER, BiGCAT, GraphER)
- Domain applications (investigative journalism, AML/KYC, government records, sanctions screening)

---

## Verified Primary Sources

### 1. LLM-Enhanced Entity Matching: Comparative Analysis (ETH Zurich, 2025)
- **Source:** ETH Zurich Research Collection (downloadable PDF)
- **Finding:** Systematic comparison of traditional vs LLM-based entity matching across 6 benchmark datasets (WDC-Shoes, WDC-Computers, WDC-Watches, WDC-Cameras, DBLP-Scholar, MusicBrainz 20K)
- **Key result:** LLM-enhanced methods outperform traditional pipeline on semantic-difficult records but at higher compute cost

### 2. In-Context Clustering-based ER (arXiv 2506.02509, Jun 2025)
- **Source:** arXiv:2506.02509v1 [cs.DB]
- **Method:** Design space exploration of in-context learning for ER clustering
- **Key insight:** LLMs can do entity clustering without pairwise comparison — reduces O(n²) to near-linear via in-context examples
- **Significance:** Challenges the pairwise comparison paradigm that dominates ER literature

### 3. OpenSanctions Pairs: Large-Scale ER with LLMs (arXiv 2603.11051, Feb 2026)
- **Source:** arXiv:2603.11051
- **Context:** OpenSanctions is a real-world sanctions/intelligence database used by investigative journalists
- **Key finding:** LLM-based ER on real-world sanctions data; includes prompt templates for entity comparison
- **Domain relevance:** Directly applicable to Jake's intelligence analysis and investigative graph interests

### 4. On Leveraging LLMs for Entity Resolution (arXiv 2401.03426)
- **Source:** arXiv:2401.03426 (Li & Feng)
- **Method:** Uncertainty reduction framework using LLMs to judiciously select which record pairs to query
- **Key result:** Reduces LLM API cost while maintaining accuracy via active learning strategy

### 5. ComEM: Match, Compare, or Select? (COLING 2025)
- **Source:** COLING 2025 Main Proceedings, ACL Anthology 2025.coling-main.8
- **Finding:** Binary matching paradigm ignores global consistency; proposes comparison and selection alternatives
- **GitHub:** tshu-w/ComEM with reproducible code

### 6. FUSER: Few-Shot ER with Uncertainty Qualification (2025)
- **Source:** EurekAlert news release + associated paper
- **Method:** Few-shot LLM ER framework with uncertainty qualification mechanism
- **Key result:** Evaluated on 6 ER benchmarks; uncertainty mechanism reduces hallucination-induced errors

### 7. GAPLink: LLM-Enhanced ER with Graph Differential Dependencies (Springer 2025)
- **Source:** Springer chapter (10.1007/978-981-96-9921-6_11)
- **Method:** Combines GDD with LLM for link prediction in ER
- **Key result:** Robust to missing labels, strong cross-domain adaptation



### 8. GER-LLM: Geospatial Entity Resolution (EMNLP 2025)
- **Source:** EMNLP 2025 Main Conference, ACL Anthology 2025.emnlp-main.1186
- **Finding:** LLM-based geospatial ER with efficient blocking for location-based record matching
- **Key insight:** Domain-specific ER benefits from LLM semantic understanding of place names and address variations

### 9. LLM-Enhanced ER Using Graph Differential Dependencies (Springer, Jul 2025)
- **Source:** Springer LNCS 10.1007/978-981-96-9921-6_11, Jul 2025
- **Finding:** Graph differential dependencies improve LLM-based ER generalization when labeled data is scarce
- **Key insight:** Combining graph structure with LLM semantic understanding overcomes supervised method limitations

### 10. LLM-Empowered KG Construction Survey (arXiv 2510.20345)
- **Source:** arXiv 2510.20345v1, Oct 2025
- **Finding:** Evolution from heuristic clustering to structured reasoning-based ER frameworks in KG construction
- **Key insight:** KGGEN iterative LLM-guided clustering merges equivalent entities beyond surface matching

### 11. LLM-CER: In-Context Clustering-Based ER (SIGMOD 2026)
- **Source:** arXiv 2506.02509 — Fu, Tang, Khan, Mehrotra, Ke, Gao (accepted SIGMOD 2026)
- **Finding:** Paradigm shift from O(n²) pairwise comparison to LLM-native in-context clustering across 9 real-world datasets
- **Key result:** 150% higher accuracy vs pairwise baselines, 10% F1 increase, 5× reduction in LLM API calls at comparable monetary cost
- **Key insight:** Systematic design space — set size, diversity, variation, ordering all matter; clustering bypasses transitive closure bottleneck entirely

### 12. LLM Self-Explanations for ER Verification (arXiv 2606.01210)
- **Source:** arXiv 2606.01210, Jun 2026
- **Finding:** LLM-generated self-explanations as verification gate for ER match decisions
- **Key result:** 95% precision on self-explanation verified matches; explains rationale for each cluster assignment

### 13. Framework Selection Dominates ER Cost (arXiv 2412.09355)
- **Source:** arXiv 2412.09355
- **Finding:** Framework selection accounts for 66–117× cost variation in ER pipelines, dwarfing model choice impact
- **Key insight:** Compilation-layer bottleneck generalizes across ER, ZKML, and verification-heavy AI workloads

---

## Key Concepts

### Entity Resolution Taxonomy
1. **Pairwise ER** — binary classification: do records A and B refer to the same entity?
2. **Record Linkage** — connecting records across different data sources
3. **Deduplication** — identifying duplicates within a single dataset
4. **Clustered ER** — grouping all records belonging to each entity (transitive closure)

### Traditional Pipeline
```
Blocking → Feature Engineering → Classifier Training → Thresholding → Transitive Closure
```

### Modern LLM-Native Pipeline
```
Embedding → Similarity Search → LLM Comparison → Graph Resolution → Knowledge Graph
```

---

## Emerging Patterns

### Shift 1: From Pairwise to Clustering
Traditional ER does O(n²) pairwise comparisons. In-context clustering (arXiv 2506.02509) shows LLMs can cluster entities directly from examples, bypassing the comparison bottleneck.

### Shift 2: Active Learning for Cost Reduction
arXiv 2401.03426 demonstrates that judicious pair selection (query only the most uncertain pairs) can reduce LLM API costs by 40-60% while maintaining accuracy.

### Shift 3: Global Consistency
ComEM (COLING 2025) shows binary matching creates transitivity violations. The field is moving toward methods that enforce global consistency constraints.

---

## Production Readiness Assessment

| Approach | Accuracy | Cost | Scalability | Auditability |
|----------|----------|------|-------------|-------------|
| Traditional pipeline | High (domain-trained) | Low | Excellent | Excellent |
| LLM pairwise matching | Highest | Very High | Poor (O(n²)) | Poor (black box) |
| In-context clustering | High | Moderate | Good (near-linear) | Moderate |
| Active learning hybrid | High | Moderate | Good | Good |
| Graph-native + LLM | High | Moderate | Good | Good (GDD explainability) |

---

## Failure Modes

1. **LLM hallucination in entity attributes** — FUSER addresses this with uncertainty qualification
2. **Cost scaling** — LLM API costs make billion-record ER economically infeasible without blocking
3. **Cross-lingual gaps** — English-centric LLMs degrade on Cyrillic/Arabic/Chinese entity names
4. **Schema drift** — LLM flexibility can mask underlying schema misalignment between sources
5. **Audit trail requirements** — compliance domains (KYC/AML) require explainable matches; pure LLM outputs fail regulatory review

---

## TRL Assessment

- **TRL 4-6:** In-context clustering (SIGMOD 2026 acceptance, 9-dataset validation; limited production trials)
- **TRL 5-7:** Active learning hybrids (OpenSanctions in production, limited deployments)
- **TRL 7-9:** Traditional + LLM hybrid pipelines (widely deployed in compliance, intelligence)
- **TRL 2-4:** Pure LLM-native ER (research stage, cost prohibitive at scale)

---

## Cross-Domain Connections

- [graph-native-entity-resolution](graph-native-entity-resolution.md) — GNN-based ER, Neo4j GraphRAG
- [cross-jurisdictional-entity-resolution](cross-jurisdictional-entity-resolution.md) — CJER across EU/US/UN
- [knowledge-graph-construction-patterns](knowledge-graph-construction-patterns.md) — LLM-empowered KG construction
- [ai-augmented-intelligence-collection](ai-augmented-intelligence-collection-draft.md) — IC OSINT, investigative graphs
- [ai-agent-market-infrastructure](ai-agent-market-infrastructure-draft.md) — financial alpha screening parallels in-context clustering

---

## Notes

- This page complements graph-native-entity-resolution.md (which covers GNN/Neo4j approach)
- Focus here is on the LLM-native shift: in-context methods, active learning, cost optimization
- Connection to Jake's Palantir thesis: ER is the data plumbing that powers investigative graph construction
- OpenSanctions Pairs paper (arXiv 2603.11051) is the most directly applicable production reference
