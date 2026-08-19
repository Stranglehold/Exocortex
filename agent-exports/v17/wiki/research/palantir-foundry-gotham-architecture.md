# Palantir Foundry/Gotham Architecture

**Status: STABLE**
**Created: 2026-07-25 | Last Updated: 2026-07-25**
**Domain: Data Aggregation & Entity Resolution | AI Agent Architecture**

A deep-dive into the architecture of Palantir Technologies' two primary platforms — Gotham (defense/intelligence community) and Foundry (commercial/enterprise) — covering the three-layer ontology model, data ingestion pipeline, entity resolution engine, Foundry vs. Gotham differences, AIP/LLM integration, the Rubix infrastructure substrate, and implications for OSINT entity resolution pipelines.

---

## 1. Overview

Palantir Technologies builds two primary platforms: **Gotham** (defense/intelligence community) and **Foundry** (commercial/civil government). Both share a core architectural philosophy centered on an **ontology-driven data integration layer** that resolves entities across heterogeneous sources and surfaces non-obvious connections through link analysis.

Palantir's architecture is not a data warehouse. It converts raw data into an **operational ontology** — a semantic model of the real-world entities (people, places, organizations, equipment, events) that matter to the organization, connected by typed relationships, and surfaced through purpose-built operational applications. Per the official documentation:

> "The Palantir Ontology is an operational layer for the organization. The Ontology sits on top of the digital assets integrated into the Palantir platform (datasets, virtual tables, and models) and connects them to their real-world counterparts."

---

## 2. The Three-Layer Ontology Architecture

The Ontology is organized into three interconnected layers, each serving a distinct role:

### 2.1 Semantic Layer (The "Nouns")

Defines **what exists** in the organization's world. Integrates heterogeneous data sources — ERP systems, CRM databases, IoT sensors, unstructured documents, and real-time streams — into a unified object model.

**Object Types:** Real-world entities modeled with properties, links, and associated actions:
- Person, Organization, Vehicle, Sensor, Transaction, Alert
- Each object type has typed properties (attributes) and incoming/outgoing link types

**Link Types:** Typed, directional relationships between objects:
- `Person --[WORKS_FOR]--> Organization`
- `Transaction --[INVOLVES]--> Person`
- `Sensor --[MONITORS]--> Equipment`

**Property Types:** Typed attributes with validation rules, default values, and inheritance. Shared property types enable cross-object consistency.

### 2.2 Kinetic Layer (The "Verbs")

Defines **what happens** — the operational workflows, actions, and computations that drive the organization.

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

**Functions:** The query and computation layer. Written in TypeScript, Functions are the primary developer surface for building operational workflows. Functions traverse the ontology graph, aggregate and transform properties, compute derived values, and return structured results for display in Operational Applications.

**Workflows:** Action-Function chains that automate multi-step processes.

### 2.3 Intelligence Layer / Dynamic Layer

The topmost layer provides AI/ML capabilities integrated directly into the ontology. This is where **AIP (Artificial Intelligence Platform)** operates.

**AIP Logic:** LLM-powered reasoning over ontology objects — provides models with structured ontology context (objects, properties, links) and receives structured outputs that write back through Actions.

**Key AIP Integration Points (2026):**
- **Object summarization:** Generate human-readable summaries from structured object data
- **Link discovery:** LLM identifies potential relationships from unstructured text
- **Entity resolution augmentation:** Deep contextual matching for fuzzy cases
- **Natural language querying:** Users ask in plain English; system translates to Function calls
- **k-LLM architecture:** Model-agnostic deployment where different LLMs serve different ontology operations with fallback chains and quality scoring

---

## 3. The AIP Architecture: 12-Capability Breakdown (2026)

Palantir's official architecture documentation decomposes AIP into **12 general categories of capability**, revealing the platform's full operational scope beyond the three-layer ontology model. This section synthesizes the official AIP Architecture Overview (Palantir, 2026) with the three-layer ontology framework.

### 3.1 Secure LLM Integration & Access
Enables secure access to the full range of commercial LLMs (GPT, Gemini, Claude, Grok) and open-source models (Llama) through Palantir-managed infrastructure. No transmitted data is retained by third-party providers, and no transmitted data is used for retraining by model providers. Enterprises can integrate existing model subscriptions, fine-tuned models, or domain-specific models.

### 3.2 End-to-End Observability
Provides monitoring tools for every step of AI-driven workflows and agentic processes: fine-grained monitoring for all data flows feeding the Ontology, logging for every action taken by humans or AI agents, and the ability to trace cascading chained executions. Extends to token consumption and resource usage tracking.

### 3.3 Context Engineering
Equips developers with no-, low-, and pro-code tools for integrating contextual data, logic, and actions that power the Ontology. All modalities of data integration (batch, streaming, real-time replication via CDC) can be leveraged through any runtime (Spark, Flink, DataFusion, Polars) while adhering to cohesive security, governance, and provenance-tracking guarantees.

### 3.4 The Ontology System
Activates context by integrating disparate data, logic, action, and security into a unified representation of enterprise decision-making. The Ontology's language models the "nouns" and "verbs" of operational processes into a legible form for both humans and agents. The engine enables querying billions of objects, orchestrating tens of thousands of actions, and continuously incorporating feedback-based learning.

### 3.5 Vector, Compute, & Tool Services
Provides integrated vectorization services for embeddings; an extensible compute framework leveraging multi-node engines (Spark, Flink), efficient single-node engines (DuckDB, Polars), and any containerized "BYO" engine; and an integrated set of tool services that work with the Ontology system as an evolving tool factory.

### 3.6 Security & Governance
Ensures every operation by humans and agents abides by rigorous role-, marking-, and purpose-based controls. These controls are granularly configurable and dynamically interrogable, cataloged in expressive audit logging. Governance extends uniformly across all operational, engineering, and developer activities within platform interfaces and programmatically through APIs/SDKs.

### 3.7 Agent Lifecycle
Powers the interconnected building, orchestration, and evaluation processes for agents in production. Agents can be constructed using no-, low-, and pro-code workbenches. Durable orchestrations are configured through low-code interfaces (AIP Logic) or pro-code interfaces (Code Workspaces). The integrated **AIP Evals** evaluation framework operates seamlessly with the Ontology, enabling test case creation, debugging, iteration on agent definitions, comparison across different LLMs, and examination of execution variance.

### 3.8 Operational Automation
Facilitates different modes of automation: scalable schedule-based automations, near real-time event-driven automations processing streaming data, and API-driven operations. Every automation can leverage the Ontology's data, logic, and action primitives alongside execution and notification configurations.

### 3.9 Development Environments
Provides integrated development environments (VS Code, JupyterLab) with seamless connectivity to Ontology-driven applications and integrated testing/evaluation frameworks. The Platform SDK and Ontology SDK, in conjunction with Palantir's VS Code plug-in, bring the same core functionality to existing developer toolchains.

### 3.10 Human + AI Applications
Delivers the full spectrum of AI-driven experiences: object-oriented analytics, real-time application building, multimodal governance workflows, and administration of core platform capabilities. Each persona (operational users, compliance teams, engineers, analysts) has out-of-the-box applications.

### 3.11 Package, Release, Deploy
Moves beyond point analytics to fully featured AI products with an integrated DevOps toolchain. End-to-end collections of data pipelines, Ontology definitions, automations, and prebuilt applications can be packaged, released, and deployed across heterogeneous target environments.

### 3.12 Enterprise Automation
Enables specialized AI agents (e.g., AI FDE, AIP Analyst) to construct data pipelines, write business logic, train models, build ontologies, produce analytics, and develop end-to-end applications. These agents operate atop the same foundation as human users, abiding by the same integrated change management capabilities (e.g., Global Branching) and seamlessly weaving human-in-the-loop workflows with entirely autonomous operations.

---

## 4. Data Ingestion Pipeline

### 4.1 Connection Layer
Supports JDBC databases, file-based (CSV, JSON, Parquet, Avro, XML), stream ingestion (Kafka, Kinesis), REST/GraphQL APIs, and unstructured documents with OCR/NLP preprocessing.

### 4.2 Pipeline Builder

- **Datasets:** Immutable, versioned collections. Every transform produces a new dataset version.
- **Incremental transforms:** Process only new/changed data for near-real-time updates.
- **Branching & merging:** Git-like branching for experimentation. Production runs on 'master'.
- **Data expectations:** Declarative quality checks; failed expectations can block downstream consumption.
- **Lineage tracking:** Full provenance — which transforms, source data, timestamp, user.

### 4.3 Ontology Mapping

1. **Object type backing:** Each object type backed by one or more datasets providing properties
2. **Link derivation:** Link types backed by datasets defining source/target/type
3. **Synchronization:** New dataset versions auto-reflect in the ontology
4. **Multi-source resolution:** One object type can be backed by multiple datasets with configurable reconciliation

---

## 5. Entity Resolution Architecture

### 5.1 Resolution Methods

| Method | Description |
|--------|-------------|
| **Deterministic Rules** | Exact matching on unique identifiers (SSN, passport, corporate registration ID). Composite key matching (name + DOB + address). Priority-ordered rule chains. |
| **Probabilistic Scoring** | Fellegi-Sunter model with configurable m/u-probabilities. String similarity: Levenshtein, Jaro-Winkler, Soundex, Metaphone. Weighted composite scores. |
| **Graph Propagation** | Transitive resolution: if A≈B and B is strongly linked to C, increase confidence A≈C. Community detection for entity clusters. |
| **LLM-Assisted Matching** | Deep contextual matching on unstructured text for ambiguous cases. AIP Logic invoked during resolution pipeline. Human-in-the-loop review for sub-threshold matches. |

### 5.2 Identity Graph

Resolution results stored as a specialized sub-ontology:
- Each resolved entity has a **canonical representation**
- Alternative representations (aliases, variant spellings, outdated records) link to the canonical entity
- Resolution confidence scores preserved for auditability
- Resolution decisions are reversible with full provenance

### 5.3 Resolution Pipeline Flow

```
Raw Records → Normalization → Candidate Generation → Scoring → Decision → Identity Graph
                (clean/standardize)  (blocking keys)    (multi-method) (auto/manual)
```

- **Blocking:** To avoid O(n²) comparisons, records are assigned blocking keys (e.g., zip code, first letter of name) and comparisons are limited to records sharing blocking keys
- **Candidate generation:** Within each block, potential matches are identified using cheap similarity metrics
- **Scoring:** Full comparison across all configured resolution methods
- **Decision:** Auto-resolve above high threshold, auto-reject below low threshold, queue for review in the middle band

---

## 6. Foundry vs. Gotham: Architectural Differences

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

**Type mapping** enables unified representation across both platforms. Gotham types can be created based on Foundry object types through the Ontology Manager, with properties that remain synchronized as the ontology evolves.

---

## 7. Operational Applications

Foundry applications are purpose-built interfaces exposing ontology objects and actions to end users:

| Application | Purpose |
|-------------|---------|
| **Object Explorer** | View, search, and navigate the ontology graph |
| **Quiver** | Link analysis and graph visualization (primarily Gotham) |
| **Workshop** | Drag-and-drop application builder for Foundry |
| **Slate** | Dashboard and reporting tool |
| **Vertex** | Geospatial analysis application |
| **Contour** | No-code data analysis and visualization |

Applications are built on top of the ontology, not directly on datasets. All data access goes through the ontology's security, lineage, and resolution layers.

---

## 8. Security and Governance Model

Palantir's security architecture is a distinguishing feature, especially for Gotham deployments:

### 8.1 Granular Access Control
- **Object-level permissions:** Control which users can see which objects
- **Property-level permissions:** Control which properties of an object are visible
- **Link-level permissions:** Control which relationships are visible
- **Conditional permissions:** e.g., "visible only if user has caveat X"

### 8.2 Markings and Caveats
- Data can be tagged with dissemination controls (e.g., NOFORN, ORCON, PROPIN)
- Markings propagate through the ontology: if an object is classified at a certain level, derived objects inherit appropriate markings
- Automatic conflict detection when markings are incompatible

### 8.3 Audit and Provenance
- Every action, data access, and resolution decision is logged
- Full lineage from raw source data to derived conclusions
- Immutable audit trails for compliance and investigation

### 8.4 Compliance and Deployment Certifications
- AIP/Foundry achieved **FedRAMP High** authorization
- **IL5 and IL6** (classified) deployment options for DoD/IC workloads
- Air-gapped deployment support for disconnected/enclave environments
- Deployed within **Rubix** — Palantir's orchestrated Kubernetes substrate that provides the infrastructure layer across cloud, on-premises, and classified environments

---

## 9. Rubix Substrate & Apollo Platform

Beneath the application and ontology layers sits Palantir's infrastructure orchestration platform:

**Rubix:** A Kubernetes-based orchestration substrate that provides the deployment and operational backbone for AIP, Foundry, and Gotham across heterogeneous environments. Rubix handles:
- Multi-cloud and hybrid deployment (AWS, Azure, GCP, on-premises, air-gapped)
- Automated scaling, health monitoring, and self-healing
- Zero-downtime upgrades and canary deployments
- Unified identity and access management across deployments

**Apollo:** The continuous delivery and operations management layer that sits on top of Rubix. Apollo provides:
- Automated release management and configuration drift detection
- Multi-environment synchronization (dev → staging → production → classified)
- Microservice health monitoring and auto-remediation
- Cost optimization and resource governance

The combination of Apollo + Rubix enables Palantir's "single pane of glass" operations model where the same software stack runs identically from unclassified cloud to classified air-gapped environments.

### 9.1 Palantir MCP

A notable 2026 development is **Palantir MCP** (Model Context Protocol), providing a secure interface for agentic development analogous to what is possible in the platform with AI FDE (Foundry Development Environment). MCP enables external AI agents to interact with the Ontology through a standardized protocol, bridging the AIP ecosystem with the broader agent development landscape. This positions Palantir as a participant in the emerging MCP ecosystem (alongside Anthropic, OpenAI, and Google) while maintaining its security and governance guarantees.

---

## 10. Implications for OSINT Entity Resolution Pipelines

Palantir's architecture offers concrete lessons for building lightweight OSINT investigation pipelines:

1. **Semantic Modeling First** — Formalize your domain (persons, organizations, locations, events, documents) before connecting data sources. The ontology should reflect the investigation's real-world semantics, not the structure of source datasets.

2. **Kinetic Layer Matters** — Evidence capture, source rating (Admiralty Code), link validation, and report generation are kinetic actions that should be modeled alongside data. Every piece of evidence needs provenance metadata (source, date, reliability).

3. **Multi-Method Resolution** — Combine deterministic rules (exact identifiers), probabilistic scoring (name/address similarity), and graph propagation to build identity graphs — then use LLMs for deep contextual matching on unstructured text.

4. **Immutable Lineage** — Every OSINT finding should carry full provenance: which source, when collected, what methodology, what confidence. This is structurally equivalent to Palantir's data lineage system.

5. **Write-Through Actions** — All modifications should go through defined action types rather than direct data manipulation, enabling audit trails and rollback capability essential for investigative integrity.

6. **Compartmented Collaboration** — Information sharing agreements map naturally to Palantir's marking/caveat system. Sensitive findings can be shared with granularity rather than all-or-nothing.

---

## 11. Cross-Domain Connections

1. **Entity Resolution Agent Safety** — Action-gated writes with full provenance prevent wrong-entity mutations (24-26% failure mode per Babu & Indukuri 2026). Palantir's action-only write path is a production validation of this paradigm.
2. **Multi-Agent Orchestration Patterns** — AIP's agent lifecycle management (build → orchestrate → evaluate) with AIP Evals directly maps to multi-agent framework benchmarks like MAFBench, where coordination collapse from architectural choices (>90%→<30%) is a known failure mode.
3. **Knowledge Graph Construction** — Palantir's identity graph (canonical entities, alternative representations, resolution provenance) directly maps to knowledge graph construction patterns.
4. **Fusion Centers & Multi-INT Analysis** — Gotham's operational paradigm (analyst-driven, multi-source intelligence fusion, compartmented security) is the commercial implementation of the all-source analysis architecture described in our fusion-centers page.
5. **Counterintelligence Analysis Frameworks** — The immutable lineage and marking propagation system directly addresses source reliability neglect — a canonical intelligence failure pattern identified in CI-ACH methodology.
6. **Privacy-Preserving Entity Resolution** — Granular access control with marking propagation mirrors challenges in privacy-preserving ER where data visibility must be controlled at the attribute level.
7. **OSINT Visualization Techniques** — Quiver's link analysis and Object Explorer's graph navigation are reference implementations for visualization patterns.
8. **Agentic Software Development** — AIP's enterprise automation agents (AI FDE, AIP Analyst) constructing pipelines, writing business logic, and building ontologies is a production case study in agentic software development.
9. **Intelligence Failure Analysis** — Immutable lineage directly addresses source reliability neglect — a canonical intelligence failure pattern.
10. **Dynamic Tool Discovery & MCP** — Palantir MCP's integration with external AI agents bridges the AIP ecosystem with the broader Model Context Protocol landscape, connecting to our dynamic-tool-discovery page's coverage of evolving agent-tool interfaces.
11. **Context Management in AI Agent Frameworks** — The Ontology's role as a continuously updated operational context layer for AI agents is a production analog to context management architectures (e.g., Entity Continuous Awareness, rolling summaries).
12. **Intelligence Oversight & Accountability** — The full audit trail and provenance system maps to the historical evolution of intelligence oversight mechanisms, where accountability depends on traceable decision chains.

---

## 12. Open-Source Alternatives

| Tool | Capability |
|------|-----------|
| **foundry-ontology-open** | OWL/RDF export from Palantir ontologies; semantic web integration |
| **Neo4j + GraphQL** | Typed graph database as lightweight ontology backend |
| **Linkurious** | Graph visualization/analysis (Quiver-like capabilities) |
| **Maltego** | Entity resolution and link analysis for OSINT investigations |
| **Splink** | Probabilistic record linkage at scale (MoJ) |
| **Apache Atlas** | Data governance and metadata management with lineage tracking |
| **DataHub** | Metadata platform with ontology support, lineage, and governance |

---

## 13. References

1. Palantir. "Ontology Overview." https://www.palantir.com/docs/foundry/ontology/overview
2. Palantir. "AIP Architecture Overview." https://www.palantir.com/docs/foundry/architecture-center/aip-architecture
3. Palantir. "The Ontology System." https://www.palantir.com/docs/foundry/architecture-center/ontology-system
4. Palantir. "Entity Resolution." https://www.palantir.com/foundry-entity-resolution/
5. Palantir. "Building Pipelines Overview." https://www.palantir.com/docs/foundry/building-pipelines/overview
6. Palantir. "Enable Gotham Integration — Type Mapping." https://www.palantir.com/docs/foundry/object-link-types/enable-gotham-integration
7. Bogdanov, D. "Understanding Palantir's Ontology: The Semantic, Kinetic, and Intelligence Layers." LinkedIn, 2025.
8. Sharma, A. "Practical Ontologies & How to Build Them." FourthAge Newsletter, 2024.
9. PuppyGraph. "Palantir Ontology: Architecture & Benefits." 2025.
10. Oboe. "Architecting Palantir Foundry Ontologies." 2025.
11. Rebooting With AI. "The Ontology Layer — Palantir Foundry." 2025.
12. Pebblous. "Shifting the Enterprise Ontology Paradigm: From Semantic Web to Operational Ontology." 2025.
13. IEEE. "Brief Analysis of Palantir Gotham: Collaborative Big Data Visualization Based on Dynamic Ontology." IEEE Xplore, 2024.
14. Sciforce. "Optimizing Data Mart Architecture in Palantir Foundry: TOPSIS-Based Evaluation Framework." JACR, 2025.
15. MDPI. "Data Digitization in Manufacturing Factory Using Palantir Foundry Solution." Processes 12(12), 2024.
16. Cognizant. "The Power of Ontology in Palantir Foundry."
17. Babu & Indukuri. "Entity Binding Failures in Tool-Augmented AI Agents." arXiv:2606.30531, 2026.
18. cloudbadal007. "foundry-ontology-open." GitHub, 2025.
19. Federal DS Handbook. "Palantir AIP/Foundry Guide." https://aporb.github.io/federal-ds-handbook-site/platforms/palantir.html
20. "INTEGRATION OF ARTIFICIAL INTELLIGENCE WITHIN INTELLIGENCE STRUCTURES." Annals of Military Science, 2026. doi:10.56082/annalsarscimilit.2026.2.145

---

## 14. Deepening Note (2026-08-07)

Reviewed against the shared Exocortex corpus before promotion from DRAFT to STABLE:

- **Open-source alternatives are a structural gap, not an algorithmic one.** The corpus pages on open-source OSINT tooling (open-source-osint-tools-survey, osint-reconnaissance-automation-toolchain, open-source-osint-tools-ecosystem) confirm that Splink/dedupe/Yente now cover Fellegi-Sunter probabilistic record linkage at scale, and Neo4j + GraphQL cover typed-graph storage. What no open-source stack yet replicates as an integrated runtime is Palantir's **action-only write path with immutable provenance and marking propagation** — the operational/security governance layer, not the matching math.
- **Entity-resolution safety validation.** The page's grounding claim that Palantir's action-gated writes validate the entity-aware safety gate (Babu & Indukuri, arXiv:2606.30531, 24-26% wrong-entity actions without gating) holds against the entity-resolution-agent-safety page in this corpus; the ontology's role as continuous operational context also cross-references context-management-ai-agent-frameworks.
- **Integration window.** The open-source equivalent stack (Maltego CE / SpiderFoot / Recon-ng / theHarvester for discovery, Splink for ER, Neo4j for graph, Linkurious/Gephi for analysis) is sufficient for OSINT pipelines; Palantir's differentiator remains the enterprise-grade governance and audit surface documented in Sections 8-9.
