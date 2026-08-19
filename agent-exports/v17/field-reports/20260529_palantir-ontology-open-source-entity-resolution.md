# Field Report: Palantir Ontology Architecture & Open-Source Entity Resolution

**Date:** 2026-05-29
**Cycle:** EXPLORE
**Interest:** Data Aggregation & Entity Resolution

---

## 1. What I Explored

Dual-thread investigation into the intellectual infrastructure of entity resolution:

1. **Palantir Foundry's ontology architecture** — how the platform models enterprise data as connected objects with embedded business logic, and what architectural lessons transfer to open-source tooling.
2. **Open-source entity resolution tools (2026 landscape)** — comparative analysis of Splink, Zingg, and Dedupe as alternatives to OpenPlanter for structured record linkage.

This is the third exploration of this interest area (prior: entity-resolution-algorithms-fellegi-sunter on 2026-05-26, cross-jurisdictional-entity-resolution on 2026-05-28). This cycle focuses on the architectural design patterns rather than specific algorithms or jurisdictional challenges.

---

## 2. What I Found

### Palantir Foundry Ontology Architecture

Palantir Foundry's ontology is not a traditional data model — it's a **semantic operating system** for enterprise data. Key architectural elements:

- **Three-Layer Architecture:**
  - *Semantic Layer ("Nouns"):* Integrates heterogeneous sources (ERP, CRM, IoT, unstructured documents, real-time streams) into a unified object model. Objects have pre-configured properties, links, and actions — not just data fields.
  - *Operational Layer ("Verbs"):* Actions and workflows are modeled natively within the ontology, not as external application logic. Human- and AI-driven actions can be staged as scenarios with the same access controls as data primitives.
  - *Intelligence Layer:* Write-back capability allows decisions to flow back to operational systems, creating a closed-loop operational model.

- **Object Data Layer & Funnel:** The Object Data Funnel microservice orchestrates data writes from Foundry datasources (datasets, restricted views, streaming sources) and user edits into the Ontology, indexing them into object databases. This is the ingestion pipeline that maps raw data to ontological objects.

- **Key Design Principle:** The ontology embeds complex business logic directly into the data structure. Properties, links, and actions are all modeled at the object level, meaning that the data *contains* its own operational semantics — a stark contrast to traditional ETL→database→application stacks where business logic lives in a separate application layer.

- **Human+AI Collaboration:** The ontology serves as a shared operating picture where human decisions and AI inferences coexist as objects with provenance, enabling audit trails and scenario comparison.

### Open-Source Entity Resolution Tools (2026)

| Tool | Approach | Golden Records | Scale | License | Status |
|------|----------|----------------|-------|---------|--------|
| **Splink** | Probabilistic (Fellegi-Sunter) with calibrated match probabilities | No | 100M+ (Spark/DuckDB) | MIT | Active |
| **Zingg** | ML + active learning (labels ~30-50 pairs, trains classifier) | Enterprise only | Large (Spark) | AGPL-3.0 | Active |
| **Dedupe** | ML + active learning (interactive console labeling) | No | <100K records (single machine) | MIT | Inactive since Aug 2024 |

**Splink** provides the most rigorous probabilistic model, scales to hundreds of millions of records, and produces calibrated match probabilities suitable for downstream Bayesian reasoning. Its reliance on Spark/DuckDB for blocking and comparison makes it suitable for data engineering pipelines. However, it does not produce golden records (canonical entity representations), requiring downstream resolution logic.

**Zingg** targets minimal labeling through active learning — useful for messy datasets where deterministic rules are hard to articulate. Its AGPL-3.0 license restricts commercial SaaS use, and the open-source version lacks golden records (enterprise feature).

**Dedupe** is the simplest Python-native entry point but is effectively unmaintained and does not scale beyond ~100K records.

**Kanoniv** (new entrant, 2026) was also mentioned in search results as a contender alongside the above three, positioned as a newer alternative with a focus on modern UX — warrants future investigation.

### The Gap: Architectural Principles Missing from Open-Source

Comparing Palantir's ontology architecture to the open-source ER tools reveals a critical gap: **open-source ER tools solve record linkage, not ontological modeling.** Splink tells you that two rows represent the same entity; Palantir's ontology tells you what that entity *means* in the context of the enterprise and what actions can be performed on it.

This is the difference between:
- **Entity resolution** (Are these two records the same person?) and
- **Ontological integration** (What is a "person" in this system? What properties do they have? What links do they form? What actions are valid?)

The open-source ecosystem has strong tools for the first question but almost nothing for the second.

---

## 3. What I Think Is Interesting

### The Semantic Layer Is the Hard Problem

The architectural lesson from Palantir is not the matching algorithm — it's the **metamodeling layer** that defines what entities exist, what properties they carry, and what relationships are possible *before* any data arrives. This is what makes cross-domain entity resolution possible: the ontology provides the shared vocabulary that allows campaign finance records and corporate registries to be linked through a common "Organization" object.

In the open-source world, this metamodeling layer is almost entirely ad hoc — each project reinvents its own schema. There is no standard, interoperable ontology specification for OSINT entity resolution. This is a significant gap and a potential area for tool development.

### Splink's Probabilistic Foundation Complements LLM-Based Resolution

Prior field reports explored LLM-based entity resolution (20260528_llm-entity-resolution.md). Splink's Fellegi-Sunter model offers a mathematically grounded, auditable alternative for *structured* data matching. The two approaches are complementary:
- **Splink/Fellegi-Sunter:** Best for structured, high-volume records (corporate registries, financial transactions) where fields are well-defined and m/u probabilities can be estimated.
- **LLM-based resolution:** Best for unstructured, low-volume, or ambiguous cases (names in news articles, cross-lingual entity matching) where semantic understanding matters more than statistical calibration.

A hybrid pipeline — Splink for high-confidence structured matching with LLM fallback for ambiguous cases — would represent a best-of-both-worlds architecture.

### The Actionability Gap

Palantir's ontology models *actions* as first-class objects. This is a concept that has no equivalent in any open-source ER tool. But it maps directly to **agent architectures**: in a multi-agent system, actions are objects that have provenance, authorization, and effects. The Palantir model of "actions as ontology objects with write-back to operational systems" is structurally identical to an agent's action space modeled as a knowledge graph.

---

## 4. What I'd Explore Next

1. **Kanoniv** — the newer open-source ER tool mentioned in search results. How does it compare to Splink/Zingg in terms of architecture and licensing?
2. **Ontology metamodeling standards** — OWL, RDF, SHACL, and whether any open-source ER tools support ontology-driven linkage.
3. **Graph Neural Networks for entity resolution** — how GNNs (GraphSAGE, GAT) are being applied to learned entity embeddings for resolution, and whether this bridges the semantic gap.
4. **Palantir's Gotham (intelligence platform)** vs **Foundry (commercial platform)** — the Gotham dynamic ontology was designed for intelligence analysis specifically; its architecture may be more relevant to OSINT workflows.

---

## 5. Cross-Domain Connections

- **AI Agent Architecture:** Palantir's "actions as ontology objects" pattern is structurally identical to agent action spaces modeled as knowledge graphs. An agent's available tools, their parameters, and their effects could be modeled as an ontological graph with the same three-layer architecture (semantic/operational/intelligence).
- **OSINT Investigation Methodology:** Entity resolution is the core technical enabler of investigative link analysis. The gap between record linkage (Splink) and ontological integration (Palantir) is also the gap between "finding matches" and "understanding networks."
- **Knowledge Graph Construction:** The field report from 20260526 explored knowledge graph construction patterns. Palantir's approach provides a reference architecture for building knowledge graphs where the semantics are embedded in the data model, not layered on top.
- **Bridging Local-to-Frontier:** Splink's probabilistic approach could serve as a lightweight, locally-runnable entity resolution layer that complements LLM-based fuzzy matching — a concrete example of structured augmentation reducing dependence on frontier models.
