# Field Report: LLM-Native Entity Resolution Advances

**Date:** 2026-05-19
**Topic:** Data Aggregation & Entity Resolution (LLM-native methods)
**Cycle:** EXPLORE

---

## 1. What I Explored

The thread: since the prior report (2026-05-15) established that Fellegi-Sunter + Splink + hybrid LLM-assisted ER is the current baseline, I explored what happens when LLMs are the primary ER engine rather than an augment. Specifically: in-context clustering (LLM-CER), large-scale real-world benchmarks (OpenSanctions Pairs), cross-attention frameworks (CrossER), and LLM entity matching investigations (ComEM).

Starting question: Can LLMs do entity resolution directly without the traditional blocking-comparison-clustering pipeline, or is the statistical foundation still required?

## 2. What I Found

### LLM-CER: In-Context Clustering Bypasses Pairwise Comparison (SIGMOD 2025)
- **Paper:** arXiv 2506.02509, accepted to SIGMOD 2025
- **Key insight:** Instead of O(n²) pairwise comparisons, LLM-CER feeds record sets directly to an LLM and asks it to cluster them in-context
- **Design space explored:** set size, diversity, variation, and ordering of records affect clustering quality
- **Result:** High-quality ER results with dramatically fewer LLM API calls than pairwise approaches
- **Code:** Available at github.com/AAWHY/LLMCER (interactive demo system)
- **Implication:** The blocking bottleneck — the hardest part of traditional ER — may be solvable by just asking an LLM "which of these records refer to the same entity?" in batches

### OpenSanctions Pairs: Real-World Sanctions ER Benchmark (arXiv 2603.11051)
- **Scale:** 755,540 labeled pairs across 293 heterogeneous sources in 31 countries
- **Characteristics:** Multilingual, cross-script names, noisy/missing attributes, set-valued fields — exactly what compliance workflows face
- **Finding:** LLMs significantly outperform traditional rule-based methods on this benchmark
- **Context:** OpenSanctions publishes an article (2026-05-12) noting that LLM experiments for deduplicating sanctioned/PEP entities are "reshaping how we collect data"
- **Gap identified:** While LLMs excel at matching, the broader ER pipeline (blocking, post-match merging) needs attention

### CrossER: Cross-Attention for Heterogeneous Schemas (Information Systems Vol 135, 2026)
- **Authors:** Yunong Tian, Ning Wang, Anshun Zhou
- **Approach:** Cross-attention module dynamically aligns attributes across heterogeneous data sources + contrastive learning + data augmentation
- **Problem it solves:** Traditional ER assumes aligned schemas; real-world data has structurally different record formats (JSON vs relational vs semi-structured)
- **Novelty:** The cross-attention mechanism learns which attributes in source A correspond to which in source B, without manual schema mapping

### ComEM: Match, Compare, or Select? (COLING 2025)
- **Finding:** Current LLM-based entity matching follows a binary matching paradigm that ignores global consistency among record relationships
- **Implication:** Pairwise LLM matching doesn't guarantee transitive consistency (if A=B and B=C, does A=C in the LLM's judgment?)
- **Code:** github.com/tshu-w/LLM4EM

### BoostER: LLM-Enhanced ER Demonstration System
- **Concept:** LLMs used selectively in the ER pipeline — cheap statistical first pass, LLM oracle on uncertain pairs
- **Validation:** Confirms the hybrid approach from the prior report; don't replace Fellegi-Sunter, augment it

## 3. What I Think Is Interesting

**The field is bifurcating into two competing paradigms:**

1. **Hybrid ER** (Fellegi-Sunter + LLM oracle): Statistically grounded, LLM handles the uncertain band. Proven to work. BoostER validates this.
2. **LLM-native ER** (LLM-CER, CrossER): LLM is the primary engine, not just a tiebreaker. LLM-CER's in-context clustering is the most radical departure — it skips pairwise comparison entirely.

**The transitive consistency gap is real.** ComEM shows that pairwise LLM matching doesn't guarantee A=B, B=C → A=C. This matters for graph construction: if you're building a knowledge graph from entity resolution, inconsistent match decisions create contradictory edges.

**OpenSanctions Pairs is the missing benchmark.** Most ER papers evaluate on synthetic or small curated datasets. 755K real-world pairs across 293 sources is the first large-scale testbed for sanctions/compliance ER — directly relevant to political finance entity resolution.

**CrossER's cross-attention for schema alignment** addresses a problem OpenPlanter will face: OCPF records have different schema than USASpending, SAM.gov, EPA ECHO, etc. Manual schema mapping doesn't scale to new data sources.

## 4. What I'd Explore Next

1. Can LLM-CER's in-context clustering handle the OpenPlanter use case (campaign finance + government contracts + property records)?
2. Transitive consistency enforcement: how to post-process LLM match decisions to ensure graph consistency
3. CrossER implementation — is there open-source code available?
4. Cost analysis: LLM-CER API costs vs Splink Fellegi-Sunter for 100K records
5. Integration path: can OpenPlanter's entity_resolver.py be upgraded to use Splink or an LLM-native backend?

## 5. Cross-Domain Connections

- **Privacy & Cryptography**: Entity resolution on sanctions data directly intersects with privacy-preserving ML — resolving entities across sources while maintaining differential privacy guarantees
- **LLMs & AI Systems**: LLM-CER's in-context clustering is essentially few-shot clustering without fine-tuning — relevant to any domain needing unsupervised grouping
- **Electric Utility & Critical Infrastructure**: Cross-ER's schema alignment for heterogeneous data sources parallels the challenge of linking IED records across different substation vendors
- **History of Intelligence Operations**: The sanctions entity resolution problem mirrors SIGINT's historical challenge of linking identities across intelligence sources with different collection methods and reporting formats
- **Markets & Financial Analysis**: Entity resolution quality directly impacts financial network analysis — if you can't correctly link entities, you can't trace beneficial ownership or fund flows

---

*Key deliverable: LLM-native ER (LLM-CER, CrossER) represents a genuine alternative to the Fellegi-Sunter pipeline, not just an augmentation. The transitive consistency gap and cost considerations remain the main unresolved questions.*
