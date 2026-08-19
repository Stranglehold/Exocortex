# Knowledge Graph Construction Patterns

**Status: STABLE**
**Created: 2026-07-08 | Deepened: 2026-07-10**
**Interest: Data Aggregation & Entity Resolution / OSINT & Investigation Methodology**
**Sources: 16**
**Cross-Domain Connections: 14**

## Overview

Knowledge graphs (KGs) are structured representations of entities and their relationships, serving as the connective tissue between data aggregation, entity resolution, and investigative reasoning pipelines. This page surveys construction pattern tradeoffs — property graphs vs RDF, database selection, schema design, query languages, billion-node scalability, LLM-driven automated construction, GraphRAG integration, and integration with OSINT and financial intelligence (FININT) entity resolution workflows.

The 2026 landscape is shaped by three converging forces: GQL (ISO 39075) standardization unifying the property graph query surface, LLM-driven automated KG construction from unstructured text, and GraphRAG architectures that combine graph traversal with vector-based semantic retrieval for LLM-augmented querying. For Exocortex-scale OSINT investigations, the key architectural choice is whether to treat the KG as a persistent authoritative store (Neo4j, TigerGraph) or an ephemeral analytical workspace (NetworkX, cuGraph, igraph) built per investigation and discarded.

---

## 1. Property Graph Model vs RDF

### Property Graph (PG)
- **Model**: Nodes with labels + arbitrary key-value properties; edges with types + properties
- **Strengths**: Intuitive for entity-relationship modeling; native to Neo4j, TigerGraph, Amazon Neptune, JanusGraph; performant traversals (constant-time adjacency)
- **Weaknesses**: No built-in semantics/ontology layer; schema is emergent, not declared; cross-graph interoperability requires custom mapping
- **Query languages**: Cypher (Neo4j), Gremlin (Apache TinkerPop), GQL (ISO 39075, ratified 2024)

### RDF (Resource Description Framework)
- **Model**: Subject-predicate-object triples; URIs for global identifiers; OWL/RDFS ontologies for formal semantics
- **Strengths**: Global identification (URIs) enables cross-dataset linking without schema negotiation; inference engines (reasoning over ontologies); W3C standard (SPARQL)
- **Weaknesses**: Triple explosion for properties that PGs model inline; REIFICATION required for statement-level metadata (e.g., provenance, confidence) adds 3-4× triple count; slower graph traversals than PG-native engines

### Reconciliation Approaches
- **RDF*** (Hartig 2014, arXiv:1409.3288): Extends RDF with statement-level annotation — bridges RDF and PG models at the data level
- **G2GML** (Chiba et al. 2022, arXiv:2203.06393): Graph-to-Graph Mapping Language for automated RDF↔PG translation
- **Unified frameworks**: Expressive Reasoning Graph Store (Neelam et al. 2022, arXiv:2209.05828) — single engine managing both RDF and PG datasets

### Decision Heuristic
| Factor | Property Graph | RDF |
|--------|---------------|-----|
| Ad-hoc investigative queries | ✓✓ | ✓ |
| Cross-organization data linking | ✗ | ✓✓ |
| Ontology-driven inference | ✗ | ✓✓ |
| High-throughput graph traversals | ✓✓ | ✗ |
| Schema evolution during investigation | ✓✓ | ✗ |
| Provenance/confidence at edge level | ✓ (built-in props) | ✗ (requires reification) |

---

## 2. GQL Standardization (ISO 39075)

GQL (Graph Query Language) was ratified as ISO 39075 in 2024, marking the first international standard for property graph querying. Key characteristics:

- **Unified surface**: One query language for Neo4j, TigerGraph, JanusGraph, Amazon Neptune — eliminating Cypher/Gremlin lock-in
- **Composability**: GQL is designed to compose with SQL (ISO 9075) — SQL/PGQ property graph queries can operate over relational tables as graphs, and GQL can reference SQL views
- **Graph pattern matching**: Declarative path patterns with variable-length traversal, quantified path patterns (similar to regular expressions on graph topology)
- **Graph construction**: CREATE GRAPH TYPE, CREATE GRAPH statements formalize schema-first graph construction — a departure from the schema-last Cypher tradition
- **Adoption timeline**: Early production implementations shipping in 2025-2026; full ecosystem maturity expected 2027-2028

**Implication for Exocortex**: GQL-native tooling will simplify multi-database OSINT pipelines. An investigation spanning Neo4j (entity graph) + PostgreSQL (transaction records) can use SQL/PGQ for unified queries without ETL.

Sources: ISO 39075:2024; "Database Technology Evolution III: Knowledge Graphs and Linked Data" (arXiv:2407.05096).

---

## 3. Graph Database Landscape & Benchmarking

### Production Graph Databases
| Database | Model | Query Language | Scale | Best For |
|----------|-------|---------------|-------|----------|
| **Neo4j** | Property Graph | Cypher, GQL (5.x+) | Billions of nodes/edges | General-purpose, mature ecosystem |
| **TigerGraph** | Property Graph | GSQL, GQL | Billions; massively parallel | Deep-link analytics, sub-second traversals on 10-hop paths |
| **Amazon Neptune** | PG + RDF | Gremlin, SPARQL, openCypher | AWS-managed | Multi-model, auto-scaling |
| **JanusGraph** | Property Graph | Gremlin | Distributed (Cassandra/HBase backend) | Open-source, horizontally scalable |
| **Memgraph** | Property Graph | Cypher | In-memory, real-time | Low-latency streaming graph analytics |
| **PuppyGraph** | Property Graph | Cypher, Gremlin | Query over data lakes/lakehouses without ETL | Zero-ETL graph queries over Parquet/Iceberg |
| **Apache Jena** | RDF | SPARQL | Millions to billions of triples | Semantic web, ontology reasoning |

### Benchmarking
- **LDBC SNB** (Linked Data Benchmark Council Social Network Benchmark): Industry-standard benchmark; tests traversal depth, throughput, and query complexity across SF1-SF10000 scale factors
- **JanusGraph vs Nebula vs Neo4j vs TigerGraph** (MDPI Applied Sciences 13(9):5770, 2023): LDBC SNB benchmark — Neo4j and TigerGraph lead on traversal performance; JanusGraph competitive at scale with Cassandra backend
- **PuppyGraph**: Unique architecture — runs Cypher/Gremlin queries directly on data lake files (Parquet, Iceberg, Delta Lake) without ingestion, enabling ephemeral investigation graphs over existing OSINT data stores

---

## 4. Graph-Native Entity Resolution

The convergence of graph databases and LLM-augmented entity resolution (ER) creates a new category: **graph-native ER**. Rather than running ER upstream then loading results into a graph, these systems perform resolution directly within the graph engine, leveraging topology for disambiguation.

Key advances:
- **On-demand resolution (FastER)**: Resolve entities only when queried, not upfront; changes the economics from O(n²) to O(k) where k = query set size
- **Topology-aware matching**: Two "John Smith" nodes that share the same employer, address, and transaction counterparties are likely the same entity — classical pairwise ER misses this; graph-native algorithms exploit it
- **LLM as semantic resolver**: GraphRAG pipelines use LLMs to assess entity merge candidates based on combined property similarity + graph neighborhood context

See [[graph-neural-networks-entity-resolution]] for GNN-based ER methods; [[entity-resolution-agent-safety]] for entity binding failure modes.

---

## 5. GraphRAG: Retrieval-Augmented Generation with Graphs

GraphRAG combines graph traversal with vector-based semantic retrieval to ground LLM responses in structured knowledge. Rather than retrieving text chunks (standard RAG) or graph subgraphs alone, GraphRAG traverses the KG to find relevant entities and relationships, then uses those as context for LLM generation.

### Architecture Variants
1. **Graph-then-RAG**: Traverse KG for relevant subgraph → convert to text → feed to LLM
2. **RAG-then-Graph**: Retrieve relevant documents via vector search → extract entities → resolve against KG for enrichment
3. **Iterative GraphRAG**: Interleave graph expansion with LLM assessment of relevance (GRAIL architecture, Feng et al. 2025, arXiv:2508.05498)

### 2025-2026 Research
- **GraphRAG** (Han et al. 2025, arXiv:2501.00309): Foundational architecture — community-based graph summarization, global + local search modes
- **GraphRAG-Bench** (Zhu et al. 2025, arXiv:2505.21508): Critical evaluation — tests whether GraphRAG actually outperforms standard RAG. Mixed results: GraphRAG excels on multi-hop relational questions, underperforms on factoid single-hop queries
- **GRAIL** (Feng et al. 2025, arXiv:2508.05498): Iterative graph retrieval with LLM relevance scoring — 15-22% improvement on multi-hop QA benchmarks
- **Domain-specific GraphRAG**: Construction claims (MDPI Buildings 2026), bridge inspection (SSRN 6083106), agronomic knowledge (Research Square 2026) — pattern of domain ontology → KG construction → GraphRAG QA pervasive across industries

### Exocortex Integration
GraphRAG fits the Exocortex investigation pattern: resolved entities from OSINT sources populate a Neo4j graph, then GraphRAG enables investigators to ask "Who controls this shell company?" or "What other entities share this address?" with the LLM grounding responses in traversed subgraphs.

---

## 6. LLM-Driven KG Construction (2025-2026)

LLMs are reshaping KG construction from manual schema design to automated extraction:

- **Peshevski et al. (2025, arXiv:2511.11017)**: Three-stage agent-driven framework — ontology creation, refinement, and KG population — achieves 97% property coverage from unstructured product descriptions without predefined schemas.
- **Trajanoska et al. (2025, arXiv:2511.06455)**: Multi-agent system for semantic mapping of relational databases to KGs, achieving >90% mapping accuracy using Schema.org vocabulary alignment.
- **LoRA-finetuned extraction**: Domain-specific fine-tuning (e.g., Llama-LoRA for agronomic triple extraction) outperforms general-purpose LLMs for structured KG construction from specialized corpora (Research Square 2026).

For Exocortex: These techniques automate the "data ingestion → entity extraction → relationship extraction → graph construction" pipeline, particularly for PDF documents, HTML pages, and structured database exports. See [[pdf-ingestion-knowledge-base-enrichment]].

---

## 7. Scalability & Indexing

### Scaling Challenges
1. **Structural sparsity of adjacency matrices** → inefficient I/O patterns; compressed sparse formats (CSR/CSC) critical
2. **Super-node problem**: Entities with millions of edges (e.g., "United States" in a sanctions graph, "HSBC" in a transaction graph) create traversal bottlenecks — edge partitioning and weighted sampling required
3. **Temporal graphs**: Investigations frequently require time-windowed queries ("show all transactions between these entities in Q3 2024"). Time-versioned property graphs or temporal RDF approaches add storage and query complexity
4. **Sharding**: Native graph partitioning (edge-cut, vertex-cut) vs. database-level sharding — TigerGraph uses hash-based partitioning; Neo4j Fabric for federated queries across shards

### Indexing Strategies
- **Full-text indexes**: Lucene-backed in Neo4j for entity name/description search
- **Vector indexes**: Neo4j 5.x+ supports ANN vector indexes for embedding-based entity similarity search — enables hybrid graph+vector queries
- **Composite indexes**: Property combinations for equality and range lookups
- **Spatial indexes**: Geospatial queries for OSINT investigations ("find all entities registered within 50km of this port")

---

## 8. Application Patterns

### OSINT Investigative Workflows
1. **Entity graphs**: Persons → phones → emails → addresses → organizations (see [[phone-number-investigation-osint]], [[email-header-analysis]], [[dns-whois-investigation-osint]])
2. **Pivot chain traversal**: Phone → common address → co-registrant → new company → new phone — graph databases excel at arbitrary-depth traversals
3. **Community detection**: Finding clusters of related shell companies, coordinated inauthentic accounts, or sanctions evasion networks (see [[community-detection-osint]], [[link-prediction-osint-entity-resolution]])
4. **Temporal analysis**: Entity creation dates, registration changes, and transaction timestamps as temporal graph edges (see [[timeline-reconstruction-osint]])

### Financial Intelligence
1. **Transaction network analysis**: Bank accounts → transactions → shell companies → beneficial owners (see [[financial-intelligence-entity-resolution]])
2. **Trade-based money laundering (TBML)**: Importers → suppliers → vessels → port calls → pricing anomalies (see [[alternative-data-sources-financial-intelligence]])
3. **Sanctions evasion**: Entity networks with temporal churn (shell company rotation, shadow fleet IMO changes) — see [[sanctions-evasion-detection]], [[temporal-entity-resolution]]
4. **Government contracts**: Awardee → parent company → subcontractors → beneficial owners (see [[government-contracts-procurement-osint]])
5. **Campaign finance**: Donors → committees → candidates → policy outcomes — bipartite graph analysis (see [[campaign-finance-entity-resolution]])

### Alternative Data Integration
Alternative datasets (web traffic, job postings, satellite imagery, credit card panels) map naturally to property graphs: companies as nodes, supplier/customer relationships as edges, enriched with foot traffic, sentiment, and hiring attributes. See [[web-traffic-analytics-alternative-data]], [[alternative-data-sources-financial-intelligence]].

---

## 9. Exocortex Architectural Recommendations

### Persistent Store (Authoritative)
- **Neo4j AuraDB or self-hosted**: For long-lived investigation graphs, shared entity registries, and cross-case knowledge retention
- **Schema**: Property graph with typed nodes (Person, Organization, Location, Event, Document) and relationships (OWNS, EMPLOYED_BY, REGISTERED_AT, TRANSACTED_WITH)
- **Provenance**: Every relationship carries `source`, `confidence`, `timestamp` properties — enables source-weighted traversal and temporal queries

### Ephemeral Analytical Workspace
- **NetworkX + cuGraph**: For ad-hoc analysis of small-to-medium graphs loaded from structured OSINT data; Python-native, rapid prototyping
- **PuppyGraph**: Query OSINT data lake files (Parquet/Iceberg) as graphs without ingestion — ideal for one-off investigations where persistent storage overhead isn't justified
- **GraphRAG pipeline**: Neo4j (persistent) + vector index + LLM for investigative Q&A over resolved entity graphs

### Memory Integration
Knowledge graphs complement the Exocortex memory system:
- **Shared corpus** (exocortex_memory.search_memory): Semantic retrieval over all wiki pages, specs, and reports
- **Library** (exocortex_memory.search_library): Technical reference retrieval from 355+ books
- **KG**: Structured entity-relationship storage for resolved entities, enabling graph traversal and multi-hop queries that vector search alone cannot perform

The three systems form a **retrieval pyramid**: vector search for broad relevance → KG traversal for precise relationship queries → LLM for synthesis and natural-language Q&A.

---

## 10. SPARQL-Cypher Interoperability

As OSINT investigations pull from both RDF-based open data (Wikidata, DBpedia) and PG-based internal stores, query translation becomes critical:

- **Spider4SSC & S2CLite** (arXiv:2511.09354, 2025): Text-to-multi-query-language system — generates both SPARQL and Cypher from natural language. S2CLite rule-based SPARQL→Cypher parser achieves 96.6% execution accuracy.
- **Gremlinator** (arXiv:1801.02911, 2018): SPARQL-to-Gremlin translator for TinkerPop-compatible graph databases.
- **GQL convergence**: As both SPARQL and Cypher implementations adopt GQL, cross-model queries become native rather than translated.

---

## Cross-Domain Connections

- [[entity-resolution-agent-safety]] — entity binding failures as graph integrity problem
- [[graph-neural-networks-entity-resolution]] — GNN-based ER feeding KG construction
- [[link-prediction-osint-entity-resolution]] — using KG topology to predict missing entity links
- [[community-detection-osint]] — community detection on OSINT entity graphs
- [[network-analysis-graph-theory]] — centrality, betweenness, structural hole analysis
- [[timeline-reconstruction-osint]] — temporal graph analysis for event chronology
- [[financial-intelligence-entity-resolution]] — FinCEN SAR/CTR entity graphs
- [[sanctions-evasion-detection]] — dynamic entity network churn analysis
- [[government-contracts-procurement-osint]] — procurement award graphs
- [[lobbying-disclosure-osint]] — influence network mapping
- [[supply-chain-network-analysis-osint]] — multi-tier supplier graph reconstruction
- [[multi-agent-orchestration-patterns]] — agent graphs as communication topology
- [[context-management-ai-agent-frameworks]] — KG as external agent memory substrate
- [[knowledge-graph-construction-patterns]] — self-reference for architectural patterns

---

## References

1. **GQL Standard**: ISO 39075:2024 — Database Language GQL. Also: "Database Technology Evolution III: Knowledge Graphs and Linked Data" (arXiv:2407.05096, 2024).
2. **Landscape Survey**: "Survey: On the Landscape of Graph Databases" (arXiv:2505.24758, 2025) — comprehensive survey of graph database architectures, query languages, and scalability challenges.
3. **Database Benchmark**: "Experimental Evaluation of Graph Databases: JanusGraph, Nebula Graph, Neo4j, and TigerGraph" (MDPI Applied Sciences 13(9):5770, 2023) — LDBC SNB benchmark across four graph databases.
4. **GraphRAG Foundation**: Han, H., et al. (2025). "Retrieval-Augmented Generation with Graphs (GraphRAG)." arXiv:2501.00309.
5. **GraphRAG Evaluation**: Zhu, Y., et al. (2025). "GraphRAG-Bench: Can GraphRAG Really Enhance RAG?" arXiv:2505.21508.
6. **GRAIL**: Feng, Z., et al. (2025). "GRAIL: Graph-Retrieval Augmented Interactive Learning." arXiv:2508.05498.
7. **RDF-PG Reconciliation**: Hartig, O. (2014). "Reconciliation of RDF* and Property Graphs." arXiv:1409.3288.
8. **G2GML**: Chiba, H., et al. (2022). "G2GML: Graph to Graph Mapping Language for Bridging RDF and Property Graphs." arXiv:2203.06393.
9. **Unified Graph Store**: Neelam, S., et al. (2022). "Expressive Reasoning Graph Store: A Unified Framework for Managing RDF and Property Graph Databases." arXiv:2209.05828.
10. **SPARQL-Cypher Translation**: "Spider4SSC & S2CLite: A text-to-multi-query-language dataset" (arXiv:2511.09354, 2025) — S2CLite rule-based SPARQL→Cypher parser, 96.6% execution accuracy.
11. **SPARQL-Gremlin Translation**: "A Stitch in Time Saves Nine — SPARQL querying of Property Graphs using Gremlin Traversals" (arXiv:1801.02911, 2018) — Gremlinator translator.
12. **LLM KG Construction (Agents)**: Peshevski, D., et al. (2025). "AI Agent-Driven Framework for Automated Product Knowledge Graph Construction." arXiv:2511.11017.
13. **LLM KG Construction (Multi-Agent)**: Trajanoska, M., et al. (2025). "A Multi-Agent System for Semantic Mapping of Relational Data to Knowledge Graphs." arXiv:2511.06455.
14. **Domain-Specific GraphRAG (Claims)**: "Knowledge Graph Construction and GraphRAG-Based Question-Answering System for Construction Claims" (MDPI Buildings 16(4):845, 2026).
15. **Domain-Specific GraphRAG (Bridge Inspection)**: "Knowledge Graph-Enhanced Bridge Inspection Q&A Framework with GraphRAG" (SSRN 6083106, 2026).
16. **Graph-Native ER**: Agent exports — graph-native entity resolution patterns (v16, v17). See [[graph-neural-networks-entity-resolution]].
