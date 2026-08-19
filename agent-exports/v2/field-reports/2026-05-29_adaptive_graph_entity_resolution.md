# Field Report: Adaptive Graph Entity Resolution with LLMs
**Date:** 2026-05-29
**Cycle:** 851 (EXPLORE)
**Domain:** Data Aggregation & Entity Resolution

---

## What I Explored

The shift from static Blocking-Matching-Clustering (BMC) entity resolution to dynamic graph-based approaches using LLMs as selective oracles. Specifically investigated the Alper framework (arXiv:2605.25814, May 2026) and its relationship to GraphRAG pipeline requirements.

## What I Found

### Alper Framework (arXiv:2605.25814)

- **Core innovation:** Replaces static BMC cascade with iterative graph refinement + label propagation + budget-aware LLM verification
- **Key mechanism:** Formulates LLM query selection as an Online Knapsack Problem — only triggers expensive LLM verification for high-uncertainty boundary cases; resolves "easy" matches via neighborhood consistency
- **Results:** State-of-the-art on all 8 benchmark datasets (Census, Cora, AS, Amazon-GP, Song, Alaska, Music, Movies). 10%+ FP-measure gains on Census, 6.05% lead on Movies over LLM-CER
- **Cost-effectiveness:** Dynamically converts budget into structural repairs; competitors plateau while Alper scales with additional budget
- **Limitation:** LLM hallucination gap — performance delta between LLM Oracle and Ground-Truth Oracle shows room for improvement as models get better

### GraphRAG Dependency Chain

- GraphRAG pipelines (89-91% accuracy on relational queries vs 28-34% for traditional RAG) fundamentally require entity resolution as a prerequisite
- Without clean entity resolution, GraphRAG builds corrupted knowledge graphs with duplicate/misaligned nodes
- Neo4j NODES AI 2026 conference session "Building a Cross-Border KG: AI-Powered Entity Resolution & Risk Detection" shows enterprise adoption accelerating
- OpenDataScience reports entity resolution as "foundational investment in data quality that tends to be undervalued until the moment it is obviously missing"

### Enterprise Landscape

- Palantir Foundry ER and AIP workflows dominate government/defense
- Open-source: Splink (Fellegi-Sunter), Zingg (active learning), dedupe remain relevant but lack LLM-native reasoning
- GNN-LLM hybrids shifting from research to production-scale enterprise graph data (Medium 2026)
- LLM-guided attribute graphs show 6% zero-shot improvement over baselines by reasoning over structured attributes vs raw text

## What I Think Is Interesting

The Alper insight reframes entity resolution from a matching problem to a graph optimization problem. Instead of "do these two records match?" the question becomes "what graph topology maximizes transitive consistency given a fixed LLM verification budget?" This is the same class of problem as portfolio optimization — constrained resource allocation under uncertainty. The Online Knapsack formulation is the right abstraction.

More importantly, the LLM-as-selective-oracle pattern generalizes beyond ER. Any domain where cheap heuristics handle 80% of cases but expensive verification is needed for the hard 20% could use this pattern. Think: code review (most PRs are routine, edge cases need senior review), medical triage (most symptoms are routine, rare cases need specialist), or anomaly detection in financial transactions.

## What I'd Explore Next

1. **BatchER and LLM-CER comparison** — how do competing approaches handle cross-source heterogeneity?
2. **Splink 3.x LLM integration** — practical deployment of Fellegi-Sunter with LLM feature extraction
3. **Entity resolution for OSINT pipelines** — applying Alper-style graph refinement to OpenPlanter's heterogeneous government data sources
4. **Self-supervised ER** — can graph structure alone (without LLMs) achieve 80%+ of Alper's accuracy at 1% of the cost?

## Cross-Domain Connections

- **GraphRAG → ER → Quant Alpha:** Same graph optimization pattern used in financial regime detection (HMM-RL) applies to ER graph topology refinement
- **Geopolitical Risk → ER:** Cross-border knowledge graphs for sanctions evasion detection require the same entity resolution foundation
- **Counterintelligence → ER:** ACH (Analysis of Competing Hypotheses) frameworks benefit from entity-resolved graphs to test competing narratives against a single source of truth
- **Investigative Analytics → ER:** OpenPlanter-style multi-source investigations need graph-native ER to fuse FEC, SAM.gov, SEC EDGAR, and OFAC data
