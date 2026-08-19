# Knowledge Graph Construction Patterns

**Status: STABLE**
**Line Count: 185**
**Primary Sources: 7 arXiv papers, 2 OpenPlanter codebases, 1 field report**
**Topic Slug: knowledge-graph-construction**
**Created: 2026-05-19 | Last Deepened: 2026-05-19**
**Interest Origin: Data Aggregation & Entity Resolution (Palantir thesis ~2021)**

---

## Abstract

Knowledge graphs sit downstream of entity resolution: once entities are resolved across heterogeneous datasets, the graph structure determines what relationships you can query, how traversals perform at scale, and what insights surface. Two dominant paradigms exist — property graphs (Neo4j, JanusGraph, Amazon Neptune) and RDF triplestores (Apache Jena, GraphDB, Stardog) — each with fundamentally different data models, query languages, and scaling characteristics. This page covers both paradigms, their formal reconciliation, entity resolution algorithms that feed them, GraphRAG integration for LLM-augmented querying, and practical ingestion patterns validated against OpenPlanter's 15-source heterogeneous pipeline.

---

## Core Question

How do you choose between property graphs and RDF for an intelligence/OSINT knowledge graph that must ingest heterogeneous datasets, support rich relationship queries, and scale to millions of nodes?

Sub-questions:
1. When does the flexible schema of property graphs become technical debt vs. the rigid schema of RDF becoming a constraint?
2. What query patterns (Cypher path traversals vs. SPARQL graph pattern matching) matter for investigative link analysis?
3. How do NetworkX/Python-based in-memory graphs compare to persistent graph databases for the 100K-node range?
4. What ingestion patterns handle streaming updates from 15+ heterogeneous sources without full rebuilds?
5. Can GraphRAG augment knowledge graph querying for LLM-native Exocortex memory?

---

## Property Graphs vs. RDF

### Data Models

**Property Graphs (Labeled Property Graph / LPG):**
- Nodes have labels (type markers) and key-value properties
- Edges have a type, direction, and key-value properties
- Schema is implicit — defined by application code, not enforced at the database level
- Query language: Cypher (Neo4j), Gremlin (Apache TinkerPop), GSQL (TigerGraph)
- Strengths: fast traversal, developer ergonomics, flexible schema evolution
- Weaknesses: no built-in semantic reasoning, schema drift across teams, non-standardized

**RDF Triplestores:**
- Everything is a triple: (subject, predicate, object)
- URIs provide global identifiers; literals provide typed values
- Schema enforced via OWL/RDFS ontologies
- Query language: SPARQL (W3C standard)
- Strengths: semantic reasoning, data interoperability, W3C standardization, reification for provenance
- Weaknesses: verbose, slower traversal, ontology design is front-loaded complexity

### Formal Reconciliation (Primary Sources)

**Hartig (2014, arXiv:1409.3288)** provides the foundational formal reconciliation between RDF and property graphs. The paper:
- Proposes a formal definition of the PG model (since no standard existed)
- Defines bidirectional transformations: RDF to PG and PG to RDF
- Enables PG systems to load RDF data via Cypher/Gremlin
- Enables RDF systems to query PG content via SPARQL
- Key insight: the models are formally interconvertible — the choice is about query patterns and operational fit, not expressive power

**G2GML (Chiba et al., 2022, arXiv:2203.06393)** extends this with a practical mapping language for converting accumulated RDF data to property graphs. Their framework:
- Defines a Graph to Graph Mapping Language for RDF to PG conversion
- Redefines the PG model with exchangeable serialization formats (CSV, JSON)
- Demonstrates use cases with publicly available RDF datasets (DBpedia, Wikidata)
- Enables graph analysis engines (Neo4j, TigerGraph) to consume RDF data

**IBM Expressive Reasoning Graph Store (Neelam et al., 2022, arXiv:2209.05828)** proposes a unified framework that manages both RDF and property graph databases under a single system:
- Dual ingestion: same data queryable via SPARQL and Cypher
- RDF for semantic reasoning, PG for path analytics
- Addresses the false dichotomy — production systems can use both

### Practical Decision Matrix

| Requirement | Prefer Property Graph | Prefer RDF |
|------------|----------------------|------------|
| Schema flexibility during exploration | Yes | |
| Semantic inference / ontology reasoning | | Yes |
| Fast multi-hop traversals | Yes | |
| Data federation across organizations | | Yes |
| Provenance tracking (per-edge metadata) | Yes | Yes (via reification) |
| W3C standards compliance | | Yes |
| Developer velocity | Yes | |
| Regulatory data sharing | | Yes |

---

## Entity Resolution Algorithms

Entity resolution (ER) determines when two records refer to the same real-world entity — the critical upstream step before graph construction.

### Algorithmic Approaches

1. **Deterministic matching:** Exact or rule-based matching on key fields (SSN, email, tax ID). Fast but brittle — fails on typos, abbreviations, inconsistent formatting.

2. **Probabilistic matching (Fellegi-Sunter model):** The canonical statistical framework. Computes match probability from agreement/disagreement vectors across fields, weighting each field by its discriminatory power. Requires training data for m-probability (field agreement rate among true matches) and u-probability (field agreement rate by chance).

3. **Active learning:** Human-in-the-loop labeling of uncertain pairs. Higher precision than fully automated but scales poorly beyond 10K-record datasets without sampling strategies.

4. **Embedding-based (neural ER):** Map entity records to dense vectors; cosine similarity above threshold implies match. Effective for unstructured text (organization names, addresses) but requires GPU compute for datasets above 100K entities.

### Entity Resolution in Personal Knowledge Graphs (Abdelqader et al., 2023, arXiv:2307.12173)

This paper addresses a specific sub-problem relevant to OSINT: resolving entities that appear across *personal* knowledge graphs — the fragmented, inconsistent graphs individuals build from their own data. Key findings:
- ER in personal KGs faces unique challenges: no shared schema, no global identifiers, inconsistent entity representations
- Graph structure (edges/relationships) provides strong matching signals beyond attribute comparison
- Transitive closure matters: if A matches B, and B matches C, then A matches C — but this can propagate errors. Gating with confidence thresholds is essential.

### OpenPlanter Implementation

OpenPlanter's `entity_resolution.py` (15-source pipeline) demonstrates practical ER at ~100K entity scale:
- **Source-specific extraction:** Each of 15 data sources (FEC, SAM.gov, SEC EDGAR, OFAC SDN, etc.) has its own parser that extracts entities into a common schema
- **Crosswalk table pattern:** A centralized mapping table (`entity_id -> source_dataset -> source_id`) maintains provenance while allowing deduplication
- **Matching strategy:** Rule-based on normalized names + geographic disambiguation (Boston vs. Boston, MA vs. Boston, GA) — not probabilistic matching
- **Limitation:** No learned matching model; relies on domain-specific normalization rules that do not generalize

---

## NetworkX vs. Neo4j: Scaling Characteristics

### NetworkX (In-Memory Python)

OpenPlanter's `wiki_graph.py` uses NetworkX for in-process graph analysis:
- **Parsing:** Extracts cross-reference relationships from wiki markdown files using regex patterns
- **Graph model:** Directed graph with category-colored nodes (campaign-finance, contracts, nonprofits, etc.)
- **Visualization:** Character-cell rendering via Textual TUI — ~100-node graphs are legible; >500 nodes become noise
- **Scaling ceiling:** NetworkX stores the full graph in Python process memory. At 100K nodes with ~5 edges/node, this is ~50MB of edge metadata + ~20MB of node properties — manageable. At 1M nodes: ~500MB, approaching practical limits without careful optimization.

### Neo4j (Persistent Graph Database)

- **Disk-backed:** Handles billion-node graphs on commodity hardware
- **Index-free adjacency:** Each node stores pointers to its neighbors — constant-time traversal regardless of graph size
- **Cypher path queries:** `MATCH path = (a:Person)-[*1..5]-(b:Organization)` — variable-length path matching that would require custom BFS/DFS in NetworkX
- **Graph Data Science library:** Built-in PageRank, community detection (Louvain, Leiden), similarity algorithms — no Python implementation needed

### Benchmark Decision Rule

| Graph Size | Recommendation |
|-----------|----------------|
| <10K nodes | NetworkX — zero setup, fast iteration |
| 10K-100K nodes | NetworkX acceptable with memory planning; Neo4j if traversals are complex |
| >100K nodes | Neo4j — NetworkX hits memory constraints |
| >1M nodes | Neo4j with index tuning; consider JanusGraph (Cassandra-backed) for >100M |

---

## GraphRAG: Knowledge Graph-Augmented LLM Retrieval

GraphRAG is an emerging paradigm that uses knowledge graphs to structure retrieval for LLMs, addressing a key limitation of vanilla RAG: unstructured chunk retrieval loses entity-relationship context.

### Foundational Survey (Han et al., 2025, arXiv:2501.00309)

Comprehensive survey of GraphRAG approaches:
- **Graph-based indexing:** Documents are parsed into entity-relation triples, which form a KG. Retrieval traverses the graph rather than searching flat chunks.
- **Query-time graph traversal:** User query is decomposed, relevant subgraphs are extracted, and the subgraph (as structured context) is injected into the LLM prompt.
- **Key advantage over vanilla RAG:** Preserves multi-hop relationships — "Who funded the organization that employed the person who donated to candidate X?" is a graph traversal, not a keyword search.

### GraphRAG Effectiveness (Zhu et al., 2025, arXiv:2505.21508)

GraphRAG-Bench provides the first systematic evaluation benchmark:
- **Finding:** GraphRAG frequently *underperforms* vanilla RAG on simple fact retrieval (where keyword matching suffices)
- **Finding:** GraphRAG excels on hierarchical reasoning and multi-hop questions where relationship structure matters
- **Implication for Exocortex:** GraphRAG is not a drop-in replacement — it should be a retrieval *mode*, gated by query complexity classification. Simple fact lookups use vanilla RAG. Multi-hop investigative queries use GraphRAG.

### GRAIL (Feng et al., 2025, arXiv:2508.05498)

Interactive graph retrieval with precision-conciseness balance:
- **Approach:** LLM-guided random exploration + path filtering yields training data synthesis and policy learning for optimal action selection
- **Result:** 21% accuracy improvement and 22.43% F1 improvement on KGQA datasets
- **Relevance to Exocortex:** The interactive retrieval paradigm (agent autonomously explores graph paths) mirrors the Exocortex tool-use pattern — the agent could traverse a local knowledge graph via tool calls rather than receiving a pre-extracted subgraph.

---

## Ingestion Patterns for Heterogeneous Sources

### OpenPlanter 15-Source Pipeline

OpenPlanter demonstrates a practical ingestion architecture for heterogeneous data:

1. **Source-specific fetchers** (`scripts/fetch_*.py`): Each fetcher handles one data source (FEC, SAM.gov, SEC EDGAR, OFAC SDN, EPA ECHO, OSHA, FDIC, Census ACS, Senate Lobbying, ProPublica 990, ICIJ Leaks, USAspending). Standardizes to TSV/CSV output.

2. **Entity extraction** (`entity_resolution.py`): Normalizes names, geographic disambiguation (city/district matching), candidate-filtered resolution.

3. **Cross-link analysis** (`cross_link_analysis.py`): Joins resolved entities across sources — finds intersections (e.g., campaign donors who are also contract recipients).

4. **Wiki graph** (`wiki_graph.py`): Renders the cross-linked entity graph as a NetworkX structure with category-colored nodes, exposed through a Textual TUI.

### Key Ingestion Design Patterns

| Pattern | Description | When to Use |
|---------|-------------|------------|
| **Crosswalk table** | Central mapping table: (entity_id, source, source_id, confidence) | Provenance-required ingestion |
| **Batch rebuild** | Full graph reconstruction from source data on schedule | Stable schemas, batch data |
| **Streaming upsert** | Incremental entity resolution and edge insertion on data arrival | Real-time ingestion, streaming sources |
| **Schema-on-read** | Raw data stored as-is; graph structure applied at query time | Exploratory analysis, unknown schemas |
| **ETL-first** | Transform and normalize before graph insertion | Production pipelines, known schemas |

### Provenance Tracking

RDF reification model (statement about a statement) provides native provenance: each triple can itself be described with attribution, confidence, and timestamp. Property graphs handle this through edge properties (e.g., `edge.source = "FEC_2024"`, `edge.confidence = 0.92`). The practical difference: RDF reification is queryable via SPARQL without schema changes; LPG edge properties are queryable via Cypher but require consistent property naming across the graph.

---

## AI Agent-Driven KG Construction (Emerging Pattern)

**Peshevski et al. (2025, arXiv:2511.11017)** demonstrate fully automated KG construction from unstructured text using LLM agents:
- Three-stage pipeline: ontology creation, ontology refinement, KG population
- No predefined schemas or handcrafted extraction rules
- 97% property coverage on e-commerce product data
- The agent-driven approach generalizes: an LLM agent can inspect a dataset, propose a schema, and populate it — replacing months of manual ETL work

**Trajanoska et al. (2025, arXiv:2511.06455)** extend this to relational database mapping:
- Multi-agent system maps relational tables to Schema.org vocabulary using LLMs
- 90%+ mapping accuracy across domains
- Semantic layer above SQL tables without manual schema mapping
- Directly relevant to OpenPlanter 15-source ingestion: LLM agents could auto-map source schemas to a common ontology

---

## Exocortex Cross-Domain Connections

| Exocortex Concept | Knowledge Graph Application |
|------------------|----------------------------|
| **Deterministic Scaffolding** | Graph schema validation ensures structural integrity |
| **Epistemic Integrity** | Provenance tracking per edge (source dataset, confidence score, timestamp) via RDF reification or LPG edge properties |
| **Context Pruner** | Graph summarization / community compression for context windows — Louvain/Leiden community detection on subgraph, inject summary instead of full graph |
| **Proactive Interference** | Stale relationship removal when entities are re-resolved; edge confidence decay over time |
| **Entropy-as-Signal** | Graph topology changes as anomaly signal — sudden new connections between previously unrelated communities |
| **Stateful Injection** | Persistent graph state across conversation turns — the KG becomes a session-spanning memory substrate |
| **BST Classifier** | Query complexity gating for GraphRAG vs. vanilla RAG — simple lookups vs. multi-hop investigative queries |
| **Error Comprehension** | Entity resolution confidence thresholds — low-confidence matches flagged for human review, not silently ingested |

---

## References

### Primary Sources (arXiv)
- Hartig, O. (2014). Reconciliation of RDF* and Property Graphs. arXiv:1409.3288.
- Chiba, H., Yamanaka, R., & Matsumoto, S. (2022). G2GML: Graph to Graph Mapping Language for Bridging RDF and Property Graphs. arXiv:2203.06393.
- Neelam, S., et al. (2022). Expressive Reasoning Graph Store: A Unified Framework for Managing RDF and Property Graph Databases. arXiv:2209.05828.
- Abdelqader, A., et al. (2023). Named Entity Resolution in Personal Knowledge Graphs. arXiv:2307.12173.
- Han, H., et al. (2025). Retrieval-Augmented Generation with Graphs (GraphRAG). arXiv:2501.00309.
- Zhu, Y., et al. (2025). GraphRAG-Bench: Can GraphRAG Really Enhance RAG? arXiv:2505.21508.
- Feng, Z., et al. (2025). GRAIL: Graph-Retrieval Augmented Interactive Learning. arXiv:2508.05498.
- Peshevski, D., Stojanov, R., & Trajanov, D. (2025). AI Agent-Driven Framework for Automated Product Knowledge Graph Construction. arXiv:2511.11017.
- Trajanoska, M., Stojanov, R., & Trajanov, D. (2025). A Multi-Agent System for Semantic Mapping of Relational Data to Knowledge Graphs. arXiv:2511.06455.

### Practical Implementations
- OpenPlanter entity_resolution.py: /a0/usr/workdir/openplanter_study/scripts/entity_resolution.py
- OpenPlanter cross_link_analysis.py: /a0/usr/workdir/openplanter_study/scripts/cross_link_analysis.py
- OpenPlanter wiki_graph.py: /a0/usr/workdir/openplanter_study/agent/wiki_graph.py

### Tools & Documentation
- Neo4j Graph Data Science: neo4j.com/docs/graph-data-science
- Apache Jena: jena.apache.org
- RDF 1.1 Primer: w3.org/TR/rdf11-primer
- NetworkX documentation: networkx.org
