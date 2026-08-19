# How Palantir's Foundry/Gotham Actually Work Architecturally

**Status: STABLE**
**Created: 2026-05-30**
**Deepened: 2026-05-31**
**Domain: Data Aggregation & Entity Resolution**

A deep-dive into the architecture of Palantir Technologies' two primary platforms — Gotham (defense/intelligence community) and Foundry (commercial/enterprise) — covering the three-layer ontology model, data ingestion pipeline, entity resolution engine, platform differences, and the AIP/LLM integration layer.

---

## 1. Overview

Palantir Technologies builds two primary platforms: **Gotham** (defense/intelligence community) and **Foundry** (commercial/civil government). Both share a core architectural philosophy centered on an **ontology-driven data integration layer** that resolves entities across heterogeneous sources and surfaces non-obvious connections through link analysis.

Palantir's architecture is not a data warehouse. It converts raw data into an **operational ontology** — a semantic model of the real-world entities (people, places, organizations, equipment, events) that matter to the organization, connected by typed relationships, and surfaced through purpose-built operational applications. Per the official documentation:

> "The Palantir Ontology is an operational layer for the organization. The Ontology sits on top of the digital assets integrated into the Palantir platform (datasets, virtual tables, and models) and connects them to their real-world counterparts."

---

## 2. The Three-Layer Ontology Architecture

The Ontology is organized into three interconnected layers, each serving a distinct role:

### 2.1 Semantic Layer (The "Nouns")

The semantic layer defines **what exists** in the organization's world. It integrates heterogeneous data sources — ERP systems, CRM databases, IoT sensors, unstructured documents, and real-time streams — into a unified object model.

**Object Types:** Real-world entities modeled with properties, links, and associated actions:
- Person, Organization, Vehicle, Sensor, Transaction, Alert
- Each object type has typed properties (attributes) and incoming/outgoing link types

**Link Types:** Typed, directional relationships between objects:
- `Person --[WORKS_FOR]--> Organization`
- `Transaction --[INVOLVES]--> Person`
- `Sensor --[MONITORS]--> Equipment`

**Property Types:** Typed attributes with validation rules, default values, and inheritance. Shared property types enable cross-object consistency.

### 2.2 Kinetic Layer (The "Verbs")

The kinetic layer defines **what happens** — the operational workflows, actions, and computations that drive the organization.

**Actions:** Versioned, parameterized operations performable on objects. Examples:
- "Submit for Review"
- "Run Vulnerability Scan"
- "Generate Intelligence Report"
- "Escalate Alert"

Actions are the ONLY write path to the ontology. There is no direct database write. When an action is submitted:
1. The action type validates all parameters
2. Security checks run against the calling user's permissions
3. The action executes, potentially triggering downstream workflows
4. All changes are audited with full provenance

**Functions:** The query and computation layer. Written in TypeScript, Functions are the primary developer surface for building operational workflows. Functions:
- Traverse the ontology graph (follow links between objects)
- Aggregate and transform properties
- Compute derived values
- Return structured results for display in Operational Applications

**Workflows:** Action-Function chains that automate multi-step processes. For example, an alert triage workflow might:
1. Function queries related alerts by geospatial proximity
2. Action merges duplicate alerts
3. Function computes risk score from linked intelligence
4. Action assigns to analyst with highest domain expertise

### 2.3 Intelligence Layer / Dynamic Layer

The topmost layer provides AI/ML capabilities integrated directly into the ontology. This is where **AIP (Artificial Intelligence Platform)** operates.

**AIP Logic:** LLM-powered reasoning over ontology objects. Rather than prompting an LLM with raw text, AIP Logic provides the model with structured ontology context — objects, properties, links — and receives structured outputs that write back to the ontology through Actions.

**Key AIP integration points:**
- **Object summarization:** Generate human-readable summaries from structured object data
- **Link discovery:** LLM identifies potential relationships between objects from unstructured text descriptions
- **Entity resolution augmentation:** Deep contextual matching for fuzzy entity resolution cases where deterministic/probabilistic methods fail
- **Natural language querying:** Users ask questions in plain English; the system translates to Function calls against the ontology

**Model-agnostic architecture:** AIP supports a k-LLM (multiple LLM) model where different LLMs can be used for different ontology operations, with fallback chains and quality scoring.

---

## 3. Data Ingestion Pipeline

### 3.1 Connection Layer

The first step of any pipeline is connecting organizational data sources. Palantir supports:
- **Database connections:** JDBC for relational databases, specialized connectors for SAP, Salesforce, etc.
- **File-based ingestion:** CSV, JSON, Parquet, Avro, XML
- **Stream ingestion:** Kafka, Kinesis, real-time event streams
- **API connectors:** REST/GraphQL APIs with configurable authentication
- **Unstructured data:** Document ingestion with OCR, NLP preprocessing

### 3.2 Pipeline Builder

Data transformation is done through Foundry's visual pipeline builder or code-based transforms (Python, Java, SQL, TypeScript). Key concepts:

- **Datasets:** Immutable, versioned collections of data. Every transform produces a new dataset version rather than mutating existing data.
- **Incremental transforms:** Pipelines can be configured for full or incremental processing. Incremental transforms only process new/changed data, enabling near-real-time updates.
- **Branching & merging:** Datasets support Git-like branching for experimentation. Production pipelines run on 'master' branches.
- **Data expectations:** Declarative data quality checks that run as part of the pipeline. Failed expectations can block downstream consumption or trigger alerts.
- **Lineage tracking:** Every dataset carries full provenance — which transforms produced it, what source data fed into it, when it was built, and who triggered the build.

### 3.3 Ontology Mapping

After data is ingested and transformed into datasets, it must be mapped to ontology object types:

1. **Object type backing:** Each object type is backed by one or more datasets that provide its properties
2. **Link derivation:** Link types are backed by datasets that define source object, target object, and link type
3. **Synchronization:** When pipeline transforms produce new dataset versions, the ontology automatically reflects the updated data
4. **Multi-source resolution:** One object type can be backed by multiple datasets; the resolution logic determines how conflicting property values are reconciled

---

## 4. Entity Resolution Architecture

Entity Resolution (ER) is critical — it determines whether two records from different sources refer to the same real-world entity. Palantir's ER pipeline operates at multiple levels:

### 4.1 Resolution Methods

**Deterministic Rules:**
- Exact matching on unique identifiers (SSN, passport number, corporate registration ID)
- Composite key matching (name + date of birth + address)
- Configurable rule chains with priority ordering

**Probabilistic Scoring:**
- Fellegi-Sunter model for name/address/date matching with configurable m-probability and u-probability parameters
- String similarity metrics: Levenshtein, Jaro-Winkler, Soundex, Metaphone
- Weighted composite scores across multiple property comparisons

**Graph Propagation:**
- If A is resolved to B, and B shares a strong link with C, increase confidence that A and C may be related
- Community detection algorithms identify clusters of potentially related entities
- Transitive resolution with configurable depth limits and confidence thresholds

**LLM-Assisted Matching:**
- For ambiguous cases where structured matching fails: LLMs analyze unstructured context (biographical text, organization descriptions, incident reports)
- AIP Logic models can be invoked during the resolution pipeline to make judgment calls on edge cases
- Human-in-the-loop review queues for matches below confidence thresholds

### 4.2 Identity Graph

Resolution results are stored as an identity graph — a specialized sub-ontology where:
- Each resolved entity has a canonical representation
- Alternative representations (aliases, variant spellings, outdated records) link to the canonical entity
- Resolution confidence scores are preserved for auditability
- Resolution decisions can be reversed with full provenance tracking

### 4.3 Resolution Pipeline Flow

```
Raw Records → Normalization → Candidate Generation → Scoring → Decision → Identity Graph
                (clean/standardize)  (blocking keys)    (multi-method) (auto/manual)
```

- **Blocking:** To avoid O(n²) comparisons, records are assigned blocking keys (e.g., zip code, first letter of name) and comparisons are limited to records sharing blocking keys
- **Candidate generation:** Within each block, potential matches are identified using cheap similarity metrics
- **Scoring:** Full comparison across all configured resolution methods
- **Decision:** Auto-resolve above high threshold, auto-reject below low threshold, queue for review in the middle band

---

## 5. Foundry vs. Gotham: Architectural Differences

While both platforms share the core ontology architecture, they differ in deployment, emphasis, and operational paradigm:

| Dimension | Foundry | Gotham |
|-----------|---------|--------|
| **Primary users** | Commercial enterprises, civil government | Defense, intelligence community |
| **Deployment model** | Cloud (SaaS), on-premises, air-gapped | Classified environments, disconnected networks |
| **UI paradigm** | Operational Applications (custom-built) | Object Explorer + Quiver (investigative) |
| **Data emphasis** | Structured enterprise data, IoT, transactions | Unstructured intelligence, SIGINT, HUMINT, imagery |
| **Workflow model** | Pipeline-driven, automated business processes | Analyst-driven, investigative workflows |
| **Security model** | Role-based access control, data classification | Compartmented security, need-to-know, multi-level |
| **Collaboration** | Cross-team dashboards, shared applications | Secure investigative collaboration, information sharing agreements |
| **Temporal analysis** | Time-series analytics, forecasting | Timeline reconstruction, event sequencing |
| **Geospatial** | Supply chain tracking, asset monitoring | Geospatial intelligence (GEOINT), activity-based intelligence |

**Type mapping** enables unified representation across both platforms. You can create Gotham types based on Foundry object types through the Ontology Manager, with properties that remain synchronized as the ontology evolves. This enables intelligence derived in Gotham to flow back to Foundry operational systems and vice versa.

---

## 6. Operational Applications

Foundry applications are purpose-built interfaces that expose ontology objects and actions to end users. Key application types:

- **Object Explorer:** View, search, and navigate the ontology graph
- **Quiver:** Link analysis and graph visualization tool (primarily Gotham)
- **Workshop:** Drag-and-drop application builder for Foundry
- **Slate:** Dashboard and reporting tool
- **Vertex:** Geospatial analysis application
- **Contour:** No-code data analysis and visualization

Applications are built on top of the ontology, not directly on datasets. This means all data access goes through the ontology's security, lineage, and resolution layers.

---

## 7. Security and Governance Model

Palantir's security architecture is a distinguishing feature, especially for Gotham deployments:

**Granular access control:**
- Object-level permissions: control which users can see which objects
- Property-level permissions: control which properties of an object are visible
- Link-level permissions: control which relationships are visible
- All permissions can be conditional (e.g., "visible only if user has caveat X")

**Markings and caveats:**
- Data can be tagged with dissemination controls (e.g., NOFORN, ORCON, PROPIN)
- Markings propagate through the ontology: if an object is classified at a certain level, any derived objects inherit appropriate markings
- Automatic conflict detection when markings are incompatible

**Audit and provenance:**
- Every action, every data access, every resolution decision is logged
- Full lineage from raw source data to derived conclusions
- Immutable audit trails for compliance and investigation

**FedRAMP and classified deployments:**
- AIP/Foundry achieved FedRAMP High authorization
- IL5 and IL6 (classified) deployment options
- Air-gapped deployment support for disconnected environments

---

## 8. Implications for OSINT Entity Resolution Pipelines

Palantir's architecture offers concrete lessons for building lightweight OSINT investigation pipelines:

1. **Semantic Modeling First** — Formalize your domain (persons, organizations, locations, events, documents) before connecting data sources. The ontology should reflect the investigation's real-world semantics, not the structure of source datasets.

2. **Kinetic Layer Matters** — Evidence capture, source rating (Admiralty Code), link validation, and report generation are kinetic actions that should be modeled alongside data. Every piece of evidence needs provenance metadata (source, date, reliability).

3. **Multi-Method Resolution** — Combine deterministic rules (exact identifiers), probabilistic scoring (name/address similarity), and graph propagation to build identity graphs — then use LLMs for deep contextual matching on unstructured text.

4. **Immutable Lineage** — Every OSINT finding should carry full provenance: which source, when collected, what methodology, what confidence. This is structurally equivalent to Palantir's data lineage system.

5. **Write-Through Actions** — All modifications should go through defined action types rather than direct data manipulation, enabling audit trails and rollback capability essential for investigative integrity.

6. **Compartmented Collaboration** — Information sharing agreements map naturally to Palantir's marking/caveat system. Sensitive findings can be shared with granularity rather than all-or-nothing.

---

## 9. Cross-Domain Connections

- **Data Aggregation & Entity Resolution** — Palantir's ontology is the commercial implementation of the entity resolution challenges explored in our wiki; the Foundry architecture provides a real-world reference for combining Fellegi-Sunter, graph propagation, and LLM matching.
- **Human Investigation & OSINT** — The ontology's role in linking disparate data sources directly supports the cross-platform identity correlation described in the human-investigation-osint pipeline. The Object Explorer/Quiver paradigm maps to OSINT investigation dashboards.
- **AI Agent Architecture** — The integration of AIP's LLM layer over the ontology (model-agnostic k-LLM architecture, deterministic scaffolding around probabilistic models) is a case study in patterns central to Exocortex's own architecture.
- **History of Intelligence Operations** — The shift from siloed intelligence databases to unified data fusion platforms (Gotham) mirrors the historical evolution from stove-piped SIGINT/HUMINT to all-source analysis.
- **Knowledge Graph Construction** — Palantir's identity graph concept with canonical entities, alternative representations, and resolution provenance directly maps to knowledge graph construction patterns in Exocortex.
- **OSINT Visualization Techniques** — Quiver's link analysis and Object Explorer's graph navigation are reference implementations for the visualization patterns covered in our osint-visualization-techniques page.
- **Privacy & Cryptography** — Granular access control with marking propagation mirrors challenges in privacy-preserving entity resolution where data visibility must be controlled at the attribute level.
- **Structured Analytic Techniques** — The action-function pipeline's immutable audit trail supports structured analytic techniques like Key Assumptions Check and Analysis of Competing Hypotheses by preserving the evidentiary chain.

---

## 10. Open-Source Alternatives

Several open-source projects attempt to replicate aspects of Palantir's ontology architecture:

- **[foundry-ontology-open](https://github.com/cloudbadal007/foundry-ontology-open):** OWL/RDF export from Palantir ontologies; enables semantic web tooling integration
- **[PalantirOntologyGenerator](https://github.com/jaymd96/PalantirOntologyGenerator):** Toolkit for discovering Foundry datasets and generating ontology JSON files
- **Neo4j + GraphQL:** Commercial graph database can serve as a lightweight ontology backend with typed nodes/edges
- **Linkurious:** Graph visualization and analysis platform that provides Quiver-like link analysis capabilities
- **Maltego:** Entity resolution and link analysis tool used widely in OSINT investigations; a practical open-source-adjacent alternative

---

## 11. References

1. Palantir. "Ontology Overview." Palantir Documentation. https://www.palantir.com/docs/foundry/ontology/overview
2. Palantir. "Entity Resolution." https://www.palantir.com/foundry-entity-resolution/
3. Palantir. "Building Pipelines Overview." https://www.palantir.com/docs/foundry/building-pipelines/overview
4. Palantir. "Enable Gotham Integration — Type Mapping." https://www.palantir.com/docs/foundry/object-link-types/enable-gotham-integration
5. Bogdanov, D. "Understanding Palantir's Ontology: The Semantic, Kinetic, and Intelligence Layers." LinkedIn Articles, 2025.
6. Sharma, A. "Practical Ontologies & How to Build Them." FourthAge Newsletter, 2024.
7. PuppyGraph. "Palantir Ontology: Architecture & Benefits." 2025. https://www.puppygraph.com/blog/palantir-ontology
8. Oboe. "Architecting Palantir Foundry Ontologies." Oboe Learning, 2025. https://oboe.com/learn/architecting-palantir-foundry-ontologies
9. Rebooting With AI. "The Ontology Layer — Palantir Foundry." https://rebootingwithai.com/src/pages/Foundry/Ontology_Layer.html
10. Pebblous. "Shifting the Enterprise Ontology Paradigm: From the Semantic Web to Operational Ontology." 2025. https://blog.pebblous.ai/project/CURK/ontology/enterprise-ontology-paradigm/en/
11. cloudbadal007. "foundry-ontology-open." GitHub, 2025. https://github.com/cloudbadal007/foundry-ontology-open
12. Federal DS Handbook. "Palantir AIP/Foundry Guide." https://aporb.github.io/federal-ds-handbook-site/platforms/palantir.html
13. Cognizant. "The Power of Ontology in Palantir Foundry." https://www.cognizant.com/us/en/the-power-of-ontology-in-palantir-foundry
