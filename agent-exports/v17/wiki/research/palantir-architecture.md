# Palantir Architecture

**Status: STABLE**
**Created: 2026-05-20**
**Deepened: 2026-05-20**

How Palantir's Foundry and Gotham platforms work architecturally — ontology layer, object resolution, link analysis, and data integration patterns.

## Overview

Palantir Technologies builds two primary platforms: **Gotham** (defense/intelligence community) and **Foundry** (commercial/civil government). Both share a core architectural philosophy centered on an **ontology-driven data integration layer** that resolves entities across heterogeneous sources and surfaces non-obvious connections through link analysis.

Palantir's architecture is not a data warehouse. It converts raw data into an **operational ontology** — a semantic model of the real-world entities (people, places, organizations, equipment, events) that matter to the organization, connected by typed relationships, and surfaced through purpose-built operational applications.

## The Ontology Layer

The Ontology is the architectural centerpiece. Per the official Palantir documentation:

> "The Palantir Ontology is an operational layer for the organization. The Ontology sits on top of the digital assets integrated into the Palantir platform."

### Core Concepts

1. **Object Types** — Real-world entities: Person, Organization, Vehicle, Sensor, Transaction, Alert. Each object type has properties (attributes), incoming/outgoing links, and associated actions.

2. **Link Types** — Typed, directional relationships between objects. For example: `Person --[WORKS_FOR]--> Organization`, `Transaction --[INVOLVES]--> Person`.

3. **Actions** — Operations that can be performed on objects. Actions are versioned, parameterized, and can trigger workflows. Examples: "Submit for Review," "Run Vulnerability Scan," "Generate Report."

4. **Functions** — The query and computation layer. Functions traverse the ontology graph, aggregate properties, and transform data. Written in TypeScript, Functions are the primary developer surface for building operational workflows.

### Architecture Pattern: Semantic Layer

The Ontology is fundamentally a **semantic layer** — it abstracts away the physical data locations (databases, APIs, files) and presents a unified object model. When a user accesses an Object Type like "Supplier," they don't need to know that supplier data is scattered across ERP tables, Excel sheets, and third-party APIs. The Ontology resolves all sources and presents a single coherent view.

This is the inversion that distinguishes Palantir from traditional ETL pipelines. In a conventional architecture, you transform data into a canonical schema, then build applications on that schema. In Palantir, raw data is ingested as-is; the Ontology maps raw data to object semantics, and applications are built on the object model.

## Object Resolution (Entity Resolution)

Object resolution is the process of determining whether two or more data records refer to the same real-world entity. Palantir's object resolution capabilities operate at multiple levels:

### Deterministic Matching
- Exact key matching on known identifiers (SSN, VIN, email address)
- Composite key matching (name + date of birth + address)
- Rule-based matching with configurable thresholds

### Probabilistic Matching
- Fellegi-Sunter statistical model for record linkage
- Feature vectors constructed from entity properties
- Match probability scores with human-in-the-loop review for borderline cases

### Cross-Source Resolution
- Data sources may use different identifiers for the same entity
- The Ontology resolves these into a single Object Type instance
- Aliases and alternative identifiers are stored as properties on the resolved object

### Operational Resolution Pipeline
1. **Ingest**: Raw data enters Foundry via connectors (databases, APIs, file uploads)
2. **Clean & Normalize**: Data transforms standardize formats (dates, addresses, names)
3. **Resolve**: Matching engine applies deterministic and probabilistic rules
4. **Merge or Flag**: High-confidence matches auto-merge; borderline cases flagged for review
5. **Publish**: Resolved objects appear in the Ontology with provenance trails

## Link Analysis

Link analysis is the core intelligence capability — discovering non-obvious relationships by traversing the ontology graph.

### Graph Traversal
- Objects and Links form a directed property graph
- Analysts traverse the graph interactively: start from a Person, follow their WORKS_FOR link to an Organization, then INVOICES_FROM to a Supplier, then SHARES_ADDRESS_WITH to other organizations
- The system computes and displays shortest paths, common connections, and network metrics

### Temporal Analysis
- Links can be time-bounded (e.g., `Person --[WORKED_AT: 2018-2022]--> Organization`)
- Temporal queries reveal patterns: "Show all transactions where Entity A and Entity B were connected within 30 days of the event"
- Time-series visualization overlays on graph views

### Relationship Inference
- Indirect relationships surfaced through path analysis
- Example: Company A and Company B have no direct link, but both received contracts from the same procurement officer within a 6-month window → flagged for review
- Weighted relationship scoring based on connection type, recency, and path multiplicity

## Foundry Technical Architecture

### Microservices Backend
Foundry uses a microservices architecture where multiple services together comprise the Ontology backend. Key services include:

- **Object Backend**: Stores and indexes object type instances, handles CRUD operations, manages property schemas
- **Link Backend**: Manages typed relationships, handles link cardinality, supports graph traversal queries
- **Action Service**: Orchestrates action execution, manages versioning and rollback
- **Function Runtime**: Executes TypeScript Functions for data transformation and workflow logic
- **Search Service**: Full-text and structured search across object properties and linked data
- **Authorization Service**: Granular, object-level access control that propagates through the graph

### Data Integration Layer
- **Connectors**: Pre-built integrations for databases (PostgreSQL, Oracle, MSSQL), cloud services (AWS S3, GCP BigQuery), APIs (REST, GraphQL), and file formats (CSV, Parquet, JSON)
- **Pipeline Builder**: Visual or code-based ETL pipeline construction
- **Data Lineage**: All transformations tracked end-to-end; every Ontology object traces back to its source records

### Application Layer
- **Workshop**: Drag-and-drop application builder for building operational UIs on top of the Ontology
- **Quiver**: Geospatial and temporal analysis application
- **Contour**: Interactive data exploration and ad-hoc analysis
- **Slate**: Custom dashboard and reporting builder
- **AIP (Artificial Intelligence Platform)**: LLM-powered interface that can query the Ontology using natural language

## Gotham vs Foundry

| Aspect | Gotham | Foundry |
|--------|--------|---------|
| Primary users | Intelligence analysts, military | Commercial enterprises, government agencies |
| Data model | Event/entity-centric, temporal | Object-centric, operational |
| Deployment | Air-gapped, on-premises | Cloud (SaaS) or on-premises |
| Key workflows | Pattern-of-life analysis, link charts, geospatial timelines | Supply chain optimization, fraud detection, patient outcomes |
| Ontology focus | Intelligence entities (persons of interest, locations, signals) | Business entities (customers, products, transactions, assets) |

## Open-Source Alternatives & Ecosystem

### OSINT / Investigation Tools
- **Maltego CE**: Graph-based link analysis with transforms for OSINT data sources. Free Community Edition limited to 10,000 entities per graph.
- **SpiderFoot HX**: Automated OSINT reconnaissance — queries 200+ data sources and maps relationships. Open-source core, commercial HX version adds collaboration and scheduling.
- **Recon-ng**: Modular reconnaissance framework (Python) with marketplace of modules for domain, contact, and credential harvesting. Terminal-based, scriptable.
- **theHarvester**: Email, subdomain, and name enumeration tool — queries search engines, PGP key servers, and SHODAN. Lightweight, fast, ideal for initial reconnaissance.

### Entity Resolution Libraries
- **Dedupe.io / dedupe (Python)**: Active learning-based entity resolution. Trains on human-labeled pairs, learns matching rules automatically.
- **Splink (Python/PySpark)**: Fellegi-Sunter probabilistic record linkage at scale. Developed by UK Ministry of Justice.
- **Zingg (Java/Python)**: ML-based entity resolution with training data generation. Handles common variations (typos, abbreviations, missing values).

### Graph Platforms
- **Neo4j**: Native property graph database with Cypher query language. Strong for link analysis but requires custom ETL for heterogeneous source integration.
- **NetworkX (Python)**: In-memory graph library for analysis and algorithms. Good for prototyping, not for production data scale.
- **Apache TinkerPop/Gremlin**: Graph traversal language and framework. Vendor-neutral, supports multiple backends (JanusGraph, Neptune, Cosmos DB).

### Relationship to Palantir
None of these tools individually replicate Palantir's architecture. Palantir's differentiation is in the **integration** — the ontology layer that unifies data integration, entity resolution, link analysis, and application building into a single operational platform. The open-source tools are components; Palantir is the fully integrated stack. An organization building Palantir-equivalent capability from open source would need to stitch together: data connectors → ETL pipeline → entity resolution engine → graph database → link analysis → application builder → access control → lineage tracking.

## Exocortex Cross-Domain Connections

1. **Data Aggregation & Entity Resolution**: Palantir's architecture is the commercial gold standard for the entity resolution problem Jake studies. The ontology layer pattern — abstracting heterogeneous data behind a unified object model — is directly applicable to Exocortex's knowledge graph construction.

2. **Knowledge Graph Construction**: The Ontology is a property graph with strong typing (Object Types, Link Types). This maps to the RDF-vs-PG debate in the KG wiki page — Palantir chose property graphs with object-level typing rather than RDF triples.

3. **OSINT Investigation**: Gotham's link analysis workflow (start from entity, traverse typed links, find non-obvious connections) is the essential OSINT pivot chain methodology. Palantir productized it; OSINT practitioners replicate it manually with Maltego and SpiderFoot.

4. **AI Agent Architecture**: Palantir AIP's integration of LLMs with the Ontology — natural language queries that traverse typed object graphs — is a production implementation of the "agentic tool use" concept. The Ontology provides the structured ground truth that constrains LLM outputs.

5. **History of Intelligence Operations**: Gotham descends directly from intelligence community requirements developed during the GWOT era. Its architecture (entity-centric, temporal, geospatial-first) mirrors the analyst workflow taught in intelligence tradecraft.

6. **Network Analysis & Graph Theory**: Link analysis = applied graph theory. Palantir's backend implements shortest-path, community detection, and centrality algorithms optimized for investigative workflows rather than academic research.

7. **Privacy & Cryptography**: Palantir's authorization model — object-level access control propagating through the graph — implements the principle of least privilege at graph granularity. This is a practical implementation of the access control patterns discussed in the privacy research.

## Primary Sources

1. Palantir Technologies. "Ontology — Overview." Official documentation. https://palantir.com/docs/foundry/ontology/overview/
2. Palantir Technologies. "Object Backend — Overview." Official documentation. https://palantir.com/docs/foundry/object-backend/overview/
3. Levinshtein, Gal. "Technical Majesty of Palantir Foundry OS: A Deep-Dive." LinkedIn, December 2024. https://www.linkedin.com/pulse/technical-majesty-palantir-foundry-os-deep-dive-gal-levinshtein-a9bee
4. PuppyGraph. "Palantir Ontology: Architecture & Benefits." May 2026. https://www.puppygraph.com/blog/palantir-ontology
5. Towards AI. "Palantir Foundry Ontology: How It Works, What Problems It Solves, and Where It Falls Short." March 2026. https://pub.towardsai.net/palantir-foundry-ontology-how-it-works-what-problems-it-solves-and-where-it-falls-short-d8b4a1ae4900

## Deep Architecture: Language, Engine, Toolchain

Per the PuppyGraph analysis (2026), Palantir groups the Ontology system into three tiers:

### Language Tier
- **Object Types, Link Types, Action Types**: The schema vocabulary
- **Interfaces**: Shared object shapes across types
- **Functions**: TypeScript business logic
- **AIP Logic**: LLM-powered function authoring using natural language

### Engine Tier
- **Ontology Metadata Service (OMS)**: Stores all schema definitions (object types, link types, action types, property schemas). This is the single source of truth for the Ontology model.
- **Object Databases**: Materialized, indexed copies of object instances for fast retrieval. Not a single database — multiple databases, each indexing a subset of object data.
- **Object Set Service (OSS)**: Handles ALL read requests — search, filter, aggregate, load. Link traversals and relationship queries go through OSS.
- **Actions Service**: The write path. Every governed action (create, update, delete) flows through the Actions service, which validates rules, triggers side effects, and commits state.
- **Funnel (Object Data Funnel)**: Orchestrates ingestion from Foundry datasets into the Object Databases. Uses Change Data Capture to keep indexed copies synchronized with source data.

### Toolchain Tier
- **OSDK (Ontology SDK)**: Generates typed client libraries in TypeScript, Python, Java, and OpenAPI. Developers get IDE autocomplete for object types and link types.
- **Workshop**: Low-code application builder with drag-and-drop Ontology-aware components
- **MCP Endpoints**: Allows external AI agents to query and interact with the Ontology via the Model Context Protocol — a significant 2026 development that opens the Ontology to agentic workflows outside Foundry

## Write Path Architecture

Critical architectural detail: writes flow ONLY through Action Types. There is no direct database write. When an action is submitted:

1. The Actions Service validates the input against the Action Type schema
2. Business logic (Functions) executes and produces side effects
3. Edited state is committed into Foundry datasets (Object Storage V1: writeback datasets; Object Storage V2: materialized optional datasets)
4. Funnel detects changes via CDC and refreshes the Object Databases
5. Downstream pipelines and consumers see the updated data with full lineage

This means every change is governed, auditable, and traceable — a sharp contrast to most application architectures where business logic writes directly to databases.

## Limitations (from Primary Sources)

Per PuppyGraph (2026) and Towards AI (2026) analyses:

1. **Platform Lock-in**: The Ontology only exists inside Palantir Foundry. No export mechanism, no external runtime.
2. **Physical Data Integration Required**: Data must be imported through Foundry pipelines and indexed into the Ontology backend. This is not a federated query layer — it requires data residency in Foundry.
3. **No Cross-Ontology Links**: Separate Ontologies within a Foundry instance cannot link to each other. This complicates federated enterprise deployments where different business units maintain separate Ontologies.
4. **Tight Pipeline Coupling**: Changes in upstream source schemas cascade into Ontology behavior, requiring close coordination between data engineering and Ontology teams.
5. **Steep Learning Curve**: Large vocabulary (Object Types, Link Types, Action Types, Functions, Interfaces, OMS, OSS, Funnel, OSDK, Workshop, AIP Logic, etc.) typically demands dedicated training or embedded Palantir field engineers.
6. **Cost**: Palantir's pricing model (per-seat licensing + platform fees) makes it inaccessible to most organizations and all individual researchers. The open-source alternatives (Maltego, Neo4j, Splink) exist precisely because Palantir is economically out of reach.

## Significance for Exocortex

Palantir's architecture validates several design patterns relevant to Exocortex's knowledge graph construction:

1. **Materialized indexing**: Foundry doesn't query source databases at runtime — it pre-indexes into Object Databases. Exocortex's knowledge packs follow the same principle: pre-compute and index rather than query at conversation time.
2. **Governed writes through a single surface**: Actions are the only write path. Exocortex could adopt this pattern — all memory modifications flow through a single governed interface rather than arbitrary tool calls.
3. **Typed schema as shared language**: Object Types and Link Types create a shared vocabulary between technical and business users. Exocortex's compound dict enrichment gate serves a similar role — typed, structured context shared between the agent and the operator.
4. **Provenance tracking**: Every Ontology object traces back to source records. Exocortex's epistemic integrity layer pursues the same principle — every claim should trace to evidence.
