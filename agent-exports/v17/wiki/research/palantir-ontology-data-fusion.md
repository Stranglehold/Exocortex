# Palantir Ontology Architecture & Data Fusion

**Status:** STABLE

**Last updated:** 2026-05-24

## Overview

Palantir Technologies (NYSE: PLTR) builds data fusion platforms — Foundry (commercial/government) and Gotham (defense/intelligence) — that center on an ontology layer for entity resolution and link analysis across heterogeneous data sources. The ontology is not merely a data catalog but an operational layer that serves as a digital twin of the organization, combining semantic elements (objects, properties, links) with kinetic elements (actions, functions, dynamic security) to power decision-making at scale.

## The Three-Layer Architecture

Palantir Foundry organizes enterprise intelligence into three interconnected layers:

1. **Semantic Layer ("Nouns")** — Object types represent real-world entities (assets, products, transactions, customers). Link types model relationships between objects. Properties capture attributes. The ontology maps raw data sources into these semantic elements, formalizing the concepts that describe the organization's operations.

2. **Kinetic Layer ("Verbs")** — Action types define how operators interact with the ontology, capturing decisions, approvals, and workflows. Functions encode arbitrary business logic for computation and transformation. Together they enable the organization to act on its data while maintaining governance and security.

3. **Intelligence Layer** — The ontology integrates with Palantir's analytical tools: Object Explorer for search and discovery, Quiver for complex analysis, and Workshop for building operational applications. The combination enables real-time decision-making across the enterprise.

## Core Components

### Object Types and Link Types

The semantic foundation. Object types are created by mapping existing datasets into the ontology. Each object type can have multiple properties (fields with rich metadata) and can be linked to other object types via named link types. Far beyond a data catalog, the ontology allows granular security and governance for all changes, supporting robust end-user workflows.

### Interfaces

Interfaces provide object type polymorphism — they describe the shape of an object type and its capabilities. This allows consistent modeling and interaction with object types that share a common shape, enabling reuse and abstraction across the ontology.

### Actions and Functions

Actions are the kinetic dimension: they allow operators to capture data from users, trigger decision-making processes, and integrate with external systems. Functions provide a way to author and evolve business logic with arbitrary complexity, typed in TypeScript or Python, and deployed as serverless functions within the ontology.

### The Ontology as Digital Twin

The ontology sits on top of integrated digital assets (datasets, virtual tables, models) and connects them to their real-world counterparts. It serves as a digital twin of the organization, containing both the current semantic state and the kinetic processes that change that state. This dual nature — static data modeling plus dynamic operational logic — distinguishes Palantir's ontology from traditional enterprise data catalogs.

## Foundry vs Gotham Architecture

While Foundry targets commercial and government data integration, Gotham focuses on intelligence and defense workflows. Both share the same ontology core but differ in emphasis:

- **Foundry** emphasizes operational workflows, supply chain modeling, and enterprise data fusion. The ontology serves business analysts, operational users, and decision-makers through low-code/no-code applications.
- **Gotham** emphasizes entity extraction, link analysis, temporal pattern detection, and geospatial intelligence. The ontology is optimized for intelligence analysts working with classified and sensitive data, with lineage tracking and dissemination controls.

The introduction of AI Platform (AIP) in 2023 added a layer enabling LLM-powered reasoning over the ontology, allowing natural language queries and automated data fusion powered by large language models while respecting the security and governance framework.

## Entity Resolution & Identity Graph Capabilities

Palantir's platforms incorporate entity resolution at multiple levels:

1. **Deterministic Matching** — Rule-based matching on identifiers (SSN, email, phone) with configurable match keys.
2. **Probabilistic Matching** — Fellegi-Sunter model implementations that assign match probabilities based on attribute agreement/disagreement patterns.
3. **Graph-Based Resolution** — Leveraging the ontology's link structure to propagate identity information across the graph (transitive resolution).
4. **LLM-Assisted Resolution (2024+)** — AIP's language models can resolve ambiguous entity references in unstructured text and link them to ontology objects using contextual understanding.

These capabilities allow Palantir to build identity graphs that span multiple data silos, incorporating corporate registries, financial transactions, communications metadata, and OSINT sources — while maintaining access controls and audit trails.

## Open-Source & Competitive Landscape

### Commercial Alternatives

- **Maltego CE/XL** — Graph-based investigation tool with transforms for OSINT data collection; not enterprise-scale but powerful for individual analysis.
- **Linkurious** — Graph visualization and analysis on top of Neo4j; used by financial crime investigators (ICIJ, Panama Papers).
- **Neo4j Bloom** — Graph exploration and visualization for Neo4j databases; supports natural language search over graph data.
- **Apache Atlas** — Metadata management and governance platform; provides data lineage, classification, and glossary but lacks kinetic layer.
- **Amundsen/DataHub** — Data discovery and catalog platforms with entity lineage; focus on data governance rather than operational decision-making.

### Open-Source Ontology Projects

- **foundry-ontology-open (GitHub)** — A lightweight Python library that mirrors Foundry's Object Types, Link Types, Action Types, and Functions, with OWL/RDF and SHACL export, plus an MCP server for AI agent integration. Enables vendor-independent ontology development while maintaining Foundry compatibility.
- **Knowledge Graphs** — Property graph (Neo4j, JanusGraph) and RDF triplestore (Apache Jena, RDF4J) approaches can approximate ontology functionality but lack tight integration with data pipelines, security policies, and operational workflows that Foundry provides.

### Architecture Tradeoffs

| Capability | Palantir Ontology | Open-Source Approx |
|-----------|-------------------|--------------------| 
| **Schema Flexibility** | Schema-on-read with semantic mapping | Database schema-first |
| **Kinetic Layer** | Built-in actions, functions, security | Separate workflow engine needed |
| **Entity Resolution** | Multi-method (rule, ML, LLM) | Custom implementation required |
| **Governance** | Granular at field/object/link level | Varies (Ranger, Sentry, custom) |
| **Scale** | Petabyte+ (AIP deployment) | Depends on underlying store |
| **AI Integration** | Native AIP LLM layer | External LLM integration |

## Implications for OSINT Entity Resolution Pipelines

Palantir's architecture offers lessons for building lightweight OSINT investigation pipelines:

1. **Semantic Modeling** — Formalize your domain (persons, organizations, locations, events, documents) before connecting data sources. The ontology should reflect the investigation's real-world semantics, not the structure of source datasets.
2. **Kinetic Layer** — Even in OSINT, workflows matter: evidence capture, source rating (Admiralty Code), link validation, and report generation are kinetic actions that should be modeled alongside data.
3. **Multi-Method Resolution** — Combine deterministic rules (exact identifiers), probabilistic scoring (name/address similarity), and graph propagation to build identity graphs — then use LLMs for deep contextual matching on unstructured text.
4. **Security & Lineage** — Every piece of OSINT evidence should carry provenance metadata (source, date, reliability) analogous to Palantir's granular security and governance.
5. **Tool Integration** — The ontology should surface in investigation tools: search, graph visualization, timeline analysis — analogous to Object Explorer and Quiver.

## Cross-Domain Connections

- **Data Aggregation & Entity Resolution** — Palantir's ontology is the commercial implementation of the entity resolution challenges explored in our data-aggregation-entity-resolution page; the Foundry architecture provides a real-world reference for how Fellegi-Sunter, graph propagation, and LLM matching combine.
- **Human Investigation & OSINT** — The ontology's role in linking disparate data sources directly supports the cross-platform identity correlation described in our human-investigation-osint pipeline.
- **Network Analysis & Graph Theory** — The ontology's link types and graph-based resolution align with our network-analysis-graph-theory page's coverage of community detection, centrality measures, and scalable graph analysis.
- **AI Agent Architecture** — The integration of AIP's LLM layer over the ontology is a case study in deterministic scaffolding around probabilistic models — a pattern central to Exocortex's own architecture.
- **History of Intelligence Operations** — The shift from siloed intelligence databases to unified data fusion platforms mirrors the historical evolution of SIGINT and all-source analysis, connecting to our history-of-intelligence-operations coverage.

## References

1. Palantir. "Ontology Overview." Palantir Documentation, accessed May 2026. https://www.palantir.com/docs/foundry/ontology/overview
2. Sharma, A. "Practical Ontologies & How to Build Them." FourthAge Newsletter, 2024. https://fourthage.substack.com/p/practical-ontologies-and-how-to-build-d7e
3. Bogdanov, D. "Understanding Palantir's Ontology: The Semantic, Kinetic, and Intelligence Layers." LinkedIn Articles, 2025.
4. cloudbadal007. "foundry-ontology-open: Open-source Palantir ontology mirror with OWL/RDF export." GitHub, 2025. https://github.com/cloudbadal007/foundry-ontology-open
5. Odiodeji, R. "Learning Palantir Foundry as an Engineer." Medium, 2024.
6. Oboe. "Architecting Palantir Foundry Ontologies." Oboe Learning, 2025. https://oboe.com/learn/architecting-palantir-foundry-ontologies
7. PuppyGraph. "Palantir Ontology: Architecture & Benefits." 2025. https://www.puppygraph.com/blog/palantir-ontology
8. Rebooting With AI. "The Ontology Layer — Palantir Foundry." https://rebootingwithai.com/src/pages/Foundry/Ontology_Layer.html
