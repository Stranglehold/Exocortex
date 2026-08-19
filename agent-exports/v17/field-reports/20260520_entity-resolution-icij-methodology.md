# Field Report: ICIJ Cross-Jurisdictional Entity Resolution Methodology
**Date:** 2026-05-20 | **Cycle:** EXPLORE | **Topic:** Data Aggregation & Entity Resolution

---

## 1. What I Explored

**The specific thread: how ICIJ actually resolves 810,000+ entities across 5 massive leaks (Pandora Papers, Paradise Papers, Panama Papers, Bahamas Leaks, Offshore Leaks) with different schemas, jurisdictions, and naming conventions — and what the open-source tooling landscape looks like for replicating that at scale.**

The prior field report (2026-05-09) covered the algorithmic landscape (Splink, Zingg, dedupe) and the multi-agent RAG ER architecture. This report goes deeper into the practical methodology: what ICIJ does, what tools exist to replicate it, and what the OpenPlanter pipeline (sitting right in /a0/usr/workdir/openplanter_study/) actually implements.

---

## 2. What I Found

### 2.1 ICIJ's Public Methodology

ICIJ publishes the Offshore Leaks Database containing data from 5 leaks spanning 2013-2022. Key architectural observations from their documentation and reconciliation API:

- **Source diversity as architecture constraint:** The data comes from *leaked records, not standardized corporate registries*. ICIJ explicitly warns: "there may be duplicates, including in the same leak." This is not a clean-warehouse problem — it's a heterogeneous-ingestion problem.
- **Node/Edge graph structure:** The database models 4 entity types: Officers (directors/shareholders/beneficiaries), Intermediaries (banks, law firms), Entities (shell companies), and Addresses (countries, jurisdictions). The natural graph connects these via officer→entity, intermediary→entity, entity→address edges.
- **Reconciliation API:** ICIJ provides an OpenRefine-compatible reconciliation API at offshoreleaks.icij.org/docs/reconciliation. This is a *deterministic matching service* that aligns external datasets to ICIJ's resolved entity graph — it's the output of their internal resolution work made available as a service.
- **No public disclosure of internal deduplication algorithm:** ICIJ acknowledges the problem but doesn't open-source their resolution pipeline. The reconciliation API is the interface, not the methodology.

### 2.2 Senzing Principle-Based Entity Resolution on ICIJ Data

Senzing, founded by Jeff Jonas (IBM/G2 fame), offers a fundamentally different approach from the Fellegi-Sunter probabilistic model:

**Entity-Centric Learning (ECL):** Instead of training a model on labeled match/non-match pairs, Senzing uses *principles* derived from observable entity behavior. The core insight Jonas articulates: "understanding who is who and who is related to who is essential — and exceptionally essential in the creation of entity resolved knowledge graphs (ERKG)."

Key architectural properties:
- **Principle-based, not model-based:** Rules are derived from how entities behave in the real world (entities don't share SSNs; entities can have multiple addresses over time). These are invariant, not learned.
- **Incremental resolution:** New records are resolved against existing entities without re-processing the entire dataset. This is critical for the ICIJ use case where leaks arrive asynchronously (2013, 2016, 2017, 2021).
- **Pre-computed ER results:** Senzing published pre-computed resolution results for the entire ICIJ dataset in a GCP public bucket. The resolved graph has ~1.5M records and ~5M aliases resolved into entity clusters.
- **Scales to billions:** Senzing claims billion-record scale, which matters when considering the full scope of cross-jurisdictional corporate data (OpenCorporates alone has 200M+ companies).

The Senzing→spaCy→LanceDB pipeline (Louis Guitton, 2024) demonstrates an end-to-end architecture:
1. Senzing resolves entities from raw ICIJ CSVs
2. Resolution results (entity clusters with aliases) exported as JSON
3. Aliases indexed in LanceDB as an Approximate Nearest Neighbors (ANN) vector store
4. spaCy entity linker queries LanceDB for zero-shot entity linking against scraped news articles
5. Linked entities build a domain-specific knowledge graph seeded by journalist "leads"

**This is significant:** the pipeline closes the loop between structured entity resolution (Senzing) and unstructured text (spaCy NER → LanceDB ANN → entity linking). An investigative journalist can type a person's name into `suspicious.txt`, and the system builds the immediate subgraph of connected entities — then finds mentions of those entities in news articles.

### 2.3 Neo4j ICIJ Sandbox — The Standard Approach

The Neo4j sandbox (guides.neo4j.com/sandbox/icij-offshoreleaks) is the most commonly cited reference architecture for ICIJ data exploration:
- Load CSVs into Neo4j as nodes (Officer, Entity, Intermediary, Address) and relationships (officer_of, intermediary_of, registered_address)
- Cypher queries traverse the graph for UBO (Ultimate Beneficial Owner) discovery
- Linkurious (graph visualization) used by ICIJ partners for visual exploration

This is the "standard" approach but doesn't solve entity resolution — it assumes resolved entities are already loaded. The Senzing approach is the ER step *before* the Neo4j graph.

### 2.4 OpenPlanter Entity Resolution Pipeline (Exocortex-Relevant)

Read the full entity_resolution.py (740 lines) and cross_link_analysis.py (585 lines) in /a0/usr/workdir/openplanter_study/scripts/.

**What it does:** Links Boston municipal contract vendors to Massachusetts OCPF campaign finance donors/employers. A concrete implementation of the core question: "a city contractor whose officers donated to the officials who approved the contract."

**Architecture (two-phase):**

**Phase 1 — Name Normalization (deterministic):**
```python
def normalize_name(name):
    # Uppercase, strip quotes
    # Remove 22 suffix patterns: INC, LLC, CORP, LTD, CO, GROUP, SERVICES, etc.
    # Regex-based suffix removal with word boundaries
    # Strip all punctuation, collapse whitespace
    return name
```
This is deterministic blocking key generation — a Fellegi-Sunter prerequisite. It normalizes "ABC Services, LLC" and "ABC SERVICES LIMITED LIABILITY COMPANY" to the same key.

**Phase 2 — Cross-Reference Matching:**
- Load normalized vendor names from Boston contracts (CSV)
- Load normalized donor/employer names from OCPF campaign finance (CSV)
- Exact match on normalized names
- For non-exact matches: fuzzy matching with configurable threshold
- Output: `cross_link_summary.json` with top 20 matched vendors sorted by donation total, including sole-source contract values

**What it notably does NOT do:**
- No Fellegi-Sunter probabilistic scoring (no match probability output)
- No transitive closure (A→B→C resolution chains)
- No active learning feedback loop
- No multi-source resolution (only two datasets)
- No failure preservation — false negatives are silently lost

This is a **minimum viable ER pipeline** that works for two specific datasets with compatible schemas. It demonstrates the pattern but doesn't scale to ICIJ's 5-leak cross-jurisdictional problem.

**OpenPlanter's data ingestion breadth** (16 fetch_*.py scripts) shows the ambition: SEC EDGAR, FEC, SAM.gov, USAspending, Senate Lobbying, ICIJ Leaks, OFAC SDN, EPA ECHO, OSHA, FDIC, Census ACS, ProPublica 990. But the entity_resolution.py only connects two of these. The cross-link bridge between all 16 sources hasn't been built.

### 2.5 Splink — The UK Government Standard

Splink (github.com/moj-analytical-services/splink, 1.9k stars) implements Fellegi-Sunter probabilistic record linkage with SQL/Spark backends. Key properties:
- **Deterministic blocking + probabilistic scoring:** Block on normalized keys (same pattern as OpenPlanter), then score pairwise matches using Bayesian comparison of field-level similarity
- **Expectation-Maximization for parameter estimation:** Unsupervised learning of match probabilities — no labeled training data required
- **SplinkDataFrame API:** Abstracts over SQL/Spark backends, enabling scale from SQLite to distributed Spark clusters
- **Used by UK Government:** Ministry of Justice, NHS, other departments for deduplication and linkage

### 2.6 GoldenMatch Shell Company Case Study

A reproducible case study (github.com/benseverndev-oss/goldenmatch-shell-company-network) demonstrates cross-jurisdictional entity resolution across 4 public datasets:
- Paradise Papers (Appleby leak)
- GLEIF authoritative LEI registry
- OpenCorporates
- Sanctions lists

The methodology: Phoenix Spree Deutschland, a Jersey-incorporated SPV, appears in both the Paradise Papers leak AND the GLEIF registry. The case study uses this cluster to validate end-to-end ER across public datasets.

---

## 3. What I Think Is Interesting

### 3.1 The Resolution Gap Between ICIJ and Everyone Else

ICIJ's entity resolution is a **black box**. They have 810k entities from 5 leaks. They acknowledge duplicates. They provide a reconciliation API for external matching. But their internal deduplication methodology — the rules, thresholds, and human review processes — is not publicly documented.

Senzing provides the closest open approach: principle-based, incremental, entity-centric. But Senzing is a commercial product (free for development, paid for production). The pre-computed ICIJ resolution results are a snapshot, not a methodology you can replicate.

**The gap:** Between Splink (open-source, Fellegi-Sunter, requires parameter tuning) and ICIJ's black-box resolution (proprietary, human-reviewed, battle-tested across 5 leaks) there's a missing middle: documented, reproducible, cross-jurisdictional ER methodology that handles the Panama Papers' specific challenges (CJK characters, Cyrillic transliterations, Spanish/Portuguese naming conventions, bearer share companies with no officers).

### 3.2 Senzing's Principle-Based Approach Maps to Exocortex Epistemic Integrity

This is the cross-domain connection that matters most:

Senzing's core philosophy: **principles derived from real-world entity behavior, not learned from training data.** Entities don't share tax IDs. Entities can change addresses over time but only have one address at a time. Entities can have multiple names (aliases, legal name changes). These are *invariant principles*, not probabilistic estimates.

This maps directly to Exocortex's **epistemic integrity** pattern: build systems where errors are visible and auditable rather than smoothed over. A Fellegi-Sunter model that silently assigns a 0.47 match probability to two records that should match is undetectable failure. A principle-based system that flags "entity has two active registered addresses simultaneously" has made the anomaly visible.

**Observation masking > summarization** (JetBrains/TUM, NeurIPS 2025) is the Exocortex expression of this principle. When ER produces a false negative, preserve the raw evidence (SQL queries, field comparisons, threshold values) rather than summarizing "no match found." Senzing's principle-based approach achieves this structurally: violations of principles are detectable events, not buried in probability scores.

### 3.3 The spaCy-LanceDB Bridge Is an Under-Appreciated Pattern

The Guitton tutorial demonstrates something subtle: the bridge between **structured entity resolution** (Senzing clusters) and **unstructured text** (spaCy NER → LanceDB vector search → entity linking) creates a feedback loop. Resolved entities from structured data make entity linking in text more accurate; linked mentions in text surface new aliases for the resolution engine.

For Exocortex: this is the same pattern as the context pruner ↔ injection gate feedback loop. Structured data (wiki pages, memories) informs unstructured processing (conversation, reasoning), which produces new structured data (updated wiki pages, new memories). The LanceDB ANN index is structurally analogous to the memory vector store.

### 3.4 OpenPlanter Is a Skeleton Waiting for Organs

The 16 fetch_*.py scripts collect data from 16 heterogeneous sources. The entity_resolution.py connects exactly two. The cross_link_analysis.py produces a summary JSON. There's no:
- Persistent entity index (SQLite or knowledge graph)
- Incremental update mechanism
- Failure preservation layer
- Human-in-the-loop review interface

But the architecture is right: fetch, normalize, block, compare, link. Adding Splink for probabilistic scoring, Senzing principles for failure detection, and a knowledge graph for transitive closure would transform it from a demo to a tool.

---

## 4. What I'd Explore Next

1. **Run Splink on OpenPlanter datasets:** Feed FEC contributions, SEC EDGAR filings, SAM.gov contracts, and ICIJ Offshore Leaks through Splink and measure deduplication quality before attempting cross-domain resolution. This is low-hanging fruit — Splink has a Python API and the data is already fetched.
2. **Test the Senzing principle-based approach on a small dataset:** The ICIJ pre-computed ER results are downloadable. Build a minimal principle set ("an entity cannot have two different registered jurisdictions simultaneously") and verify against the Senzing ground truth.
3. **Build the cross-domain entity index:** A lightweight SQLite database mapping `{entity_name, source_dataset, source_id, normalized_name}` across all 16 OpenPlanter sources. Minimum viable step before sophisticated resolution. This was already on the Next Steps list from the wiki but hasn't been executed.
4. **ICIJ offshore structure detection paper:** The Utrecht University thesis (Van Aken, 2025) on "motif-based comparative analysis of shell company structures" flagged 1,138 Dutch entities in ICIJ using graph motif detection. This is a different approach: structural pattern matching rather than entity name matching. Worth investigating for cross-jurisdictional detection where names are unreliable.
5. **GoldenMatch LEI-to-leak validation:** The Phoenix Spree Deutschland case study validates cross-dataset ER by finding entities that appear in both a leak AND an authoritative registry (GLEIF). This is a falsifiable methodology: if your ER says entity A in dataset X matches entity B in dataset Y, and both have GLEIF LEIs, you can verify.

---

## 5. Cross-Domain Connections

| Exocortex Component | Entity Resolution Parallel |
|---|---|
| Epistemic Integrity | Principle-based ER (Senzing) — violations are visible events, not buried probabilities |
| Observation Masking | Failure preservation in ER — false negatives must preserve raw evidence of why |
| Deterministic Scaffolding | Blocking keys + deterministic rules before probabilistic scoring — same decomposition pattern |
| Entropy-as-Signal | Regime change detection applied to match probability distributions over time — detect when a data source changes schema |
| Context Pruner | ANN index for alias→entity lookup (LanceDB) — analogous to memory retrieval |
| Build the Environment | Structured entity index (persistent SQLite/knowledge graph) as the environment within which resolution operates |
| History of Intelligence Operations | ICIJ's methodology is SIGINT analysis applied to financial data — source handling, cross-referencing, confidence assessment |
| Privacy/Cryptography | Reverse-ER attack: if ER can link anonymized records, it's a de-anonymization vector. ZKP-based resolution without data exposure |
| Markets/Financial Analysis | Ultimate Beneficial Owner detection is structurally identical to repo counterparty mapping — who ultimately owns what through how many layers |

---

## References

- ICIJ Offshore Leaks Database: https://offshoreleaks.icij.org
- ICIJ Reconciliation API docs: https://offshoreleaks.icij.org/docs/reconciliation
- Senzing ICIJ ERKG: https://senzing.com/icij-entity-resolution-knowledge-graph/
- Guitton, L. (2024) "Panama Papers Investigation using Entity Resolution and Entity Linking": https://guitton.co/posts/entity-resolution-entity-linking
- spaCy-LanceDB Linker: https://github.com/louisguitton/spacy-lancedb-linker
- Neo4j ICIJ Sandbox: https://guides.neo4j.com/sandbox/icij-offshoreleaks/
- GoldenMatch Shell Company Case Study: https://github.com/benseverndev-oss/goldenmatch-shell-company-network
- Van Aken, J. (2025) "Motif-Based Comparative Analysis of Shell Company Structures": Utrecht University
- Splink: https://github.com/moj-analytical-services/splink
- OpenPlanter entity_resolution.py: /a0/usr/workdir/openplanter_study/scripts/entity_resolution.py
- OpenPlanter cross_link_analysis.py: /a0/usr/workdir/openplanter_study/scripts/cross_link_analysis.py
- MDPI Computers 14(12):525 (2025) — Multi-Agent RAG Framework for Entity Resolution
- JetBrains/TUM, NeurIPS 2025 — Observation Masking for Failure Preservation
- Field Report 2026-05-09: /a0/usr/Exocortex/field-reports/20260509_entity-resolution.md
- Wiki page: /a0/usr/Exocortex/wiki/research/data-aggregation-entity-resolution.md
