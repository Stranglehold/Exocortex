# Entity Resolution in the AI Era — Production Identity Ladders, Embedding Fine-tuning, and Agentic ER

**Status:** STABLE
**Created:** 2026-08-18 (BUILD cycle, promoted from field report 20260818_entity-resolution-ai-era.md)
**Domain:** Data Aggregation & Entity Resolution
**Related pages:** [[agentic-entity-resolution]], [[entity-resolution-agent-safety]], [[entity-resolution-pipeline-performance]], [[cross-jurisdictional-entity-resolution]], [[active-learning-entity-resolution]], [[entity-resolution-confidence-calibration]]

---

## Overview

Modern entity resolution (ER) is moving beyond the classic Fellegi-Sunter / probabilistic matching paradigm in three directions: (1) **production identity ladders** — deterministic, evidence-ordered decisions of sameness that treat merge as destructive and therefore curate before they connect; (2) **embedding fine-tuning** — domain-specific triplet training that reshapes general-purpose embeddings for identity-sensitive retrieval; (3) **agentic ER** — sequential decision-making where the ER pipeline becomes a policy space (see [[agentic-entity-resolution]]). This page captures the production/operational slice: how real systems decide identity, why conservative merge policy is the core design principle, and what happens when LLM agents do entity binding.

Grounded corpus-first: shared Exocortex corpus (agentic-ER v17 page, entity-resolution-agent-safety, active-learning-ER, pipeline-performance) + arXiv verification. The 355-book reference library contains **no dedicated record-linkage/data-integration title** — an honest gap; production ER 2026 literature lives in arXiv/preprint space.

---

## 1. Production Identity Ladders: Curate Before You Connect

**Curate Before You Connect: Identity and Ontology Tagging in a Production Knowledge Graph** (Dangaich, Lewis, Pundalik; arXiv:2608.10644, Aug 2026) describes the ingestion and ontology-tagging layer that turns a validated extraction stream into a knowledge graph of **537,157 entities and 2,198,567 relationships drawn from 98,795 government documents**.

### The record-identity ladder
- Sameness is decided from **identifier columns → name columns → display names → type-scoped position**, NOT from name similarity.
- The ladder governs de-duplication within parsed tables; the graph write applies a coarser **canonical-name key** so records sharing a canonical name merge automatically on exact equality.
- The authors argue — rather than demonstrate — that **this is where the automation line belongs**: no identity benchmark is reported, and the over-merges the key permits are undetectable by construction.

### The destructive-merge incident
- The conservative policy (ER only ever flags candidates) followed an incident: two surface forms of one name were merged, **corrupting a correct record and deleting eight entities from an unrelated document**.
- **Identity decisions are destructive in a way extraction errors are not.** A wrong type can be corrected later; two records merged under one identity cannot be separated once properties have been combined, and the merge leaves no error behind.

### Ontology tagging: the evidence asymmetry
- An entity name is an **instance label rather than a type assertion** — matching name fragments against a class index *invents classifications*.
- Requiring anchored evidence cut role assignments on an enriched sample from **36 to 4, all confirmed correct**.
- Quantified: conformance debt, secondary classifications compensating for a mis-parented primary class, and a curation queue grown to **48,403 pending proposals against 775 human decisions**.

### Design takeaways for production ER
1. **Optimize recoverability, not recall.** A false non-merge is visible (candidate can be re-examined); a false merge is invisible and permanent. Conservative identity keys for writes; similarity only to surface candidates.
2. **Human review scales by queue design, not by volume.** The 48k proposals / 775 decisions ratio shows curation is the binding constraint — threshold design (what reaches the queue) matters more than reviewer throughput.
3. **Anchored evidence beats name-pattern inference** for ontology/type assignment — same principle as the identity ladder.

---

## 2. Embedding Fine-tuning for Identity-Sensitive Retrieval

**Domain-Specific Text Embedding Models for Entity Resolution** (Sapram, Raju, Konda; arXiv:2608.16161, Aug 2026) addresses the core limitation of general-purpose embeddings: they capture semantic similarity but are not optimized for distinguishing entity records where **small textual differences may either preserve or change identity**.

- Method: **domain-specific triplet fine-tuning** on a synthetic dataset of business and person records with identity-preserving variations and challenging non-matching examples; margin-based similarity evaluation on two widely used embedding models.
- Result: substantial improvements in separating true matches from highly similar non-matches — triplet training effectively reshapes general-purpose embedding spaces for entity retrieval.
- Implication: cheap, targeted fine-tuning is a practical upgrade path for data-quality and duplicate-retrieval applications without replacing the retrieval stack.
- **Caveat (uncerta, below):** embedding similarity must remain a *candidate surface*, not a decision — identity decisions stay with the ladder / gated layer.

---

## 3. The Agentic ER & Entity-Binding Frontier

**(Already covered in depth by [[agentic-entity-resolution]] and [[entity-resolution-agent-safety]] — summary for completeness.)**

- **Agentic ER** (Papadakis et al., arXiv:2607.27435) reframes the ER pipeline as a policy space: blockers, matchers, retrievers, tools, and human-in-the-loop queries become actions with cost and information gain.
- **Entity binding failures** (Babu & Indukuri, arXiv:2606.30531): 24–26% wrong-entity actions at 0% wrong-tool across 60 tasks × 5 backends × 6 tool-use methods. Entity-aware execution mechanisms (ER preconditions, confidence-gated binding, clarification, provenance) eliminate the failure at the cost of deferring under ambiguity.
- Production implication: **tool selection is solved; entity binding is not.** For autonomous OSINT research, calling the right tool (search, registry lookup, document query) against the wrong Alex/company/contract silently poisons the analysis.

---

## 4. LLM Self-Explanation Over-trust: uncerta

**Can We Trust LLM Self-Explanations for Entity Resolution?** (Teofili, Firmani, Koudas, Merialdo, Srivastava; arXiv:2606.01210, May 2026) — first large-scale systematic evaluation of LLM self-explanations for ER across **3 LLMs, 10 datasets, multiple prompting strategies**, focusing on feature attribution and counterfactual explanations at attribute and token level.

- Finding: self-explanations are **often unstable, weakly faithful, and poorly aligned with counterfactual evidence** — a substantial gap between plausibility and causal relevance.
- Established post-hoc explanation methods are significantly more trustworthy but **computationally prohibitive** on LLMs.
- Bridge: **uncerta**, a hybrid framework using self-explanations as priors to guide post-hoc exploration — explanation quality comparable to post-hoc methods at **up to an order of magnitude lower cost**.
- Integrity trap for autonomous research loops: asking an LLM *why* it matched two records produces plausible but causally wrong rationales; the explanation looks like evidence but is not. Connects to the workspace epistemic-integrity concerns ([[epistemic-integrity]]).

---

## 5. Splink Production Architecture (DeepWiki-Verified)

From moj-analytical-services/splink (verified via DeepWiki):
- All core Fellegi-Sunter algorithms implemented in **backend-agnostic SQL**, transpiled via **sqlglot**, executed on DuckDB (default: millions of rows on laptop, tens of millions on high-spec cloud) or Spark (100M+ records).
- Parameter estimation is hybrid: λ from deterministic rules + recall estimate; u from random sampling (random pairs ≈ non-matches); m via **EM with blocking rules** to concentrate matches.
- Counter-intuitive design guidance: prefer **many strict blocking rules over few loose ones** (fewer comparisons, same recall); salting on blocking rules unlocks DuckDB parallelism (~100% CPU on high-core machines).

---

## 6. Cross-Domain Connections

1. **OSINT Investigations** — identity-ladder policy maps to investigation evidence standards: never auto-merge people/companies without corroborating identifiers (ID columns, addresses, positions); let similarity flag, not decide. Reinforces Venona-as-manual-Fellegi-Sunter theme ([[venona-project-entity-resolution]]).
2. **AI Agent Architecture & Local Inference** — entity binding failures are the ER analog of tool-selection reliability; autonomous agents need an entity-resolution precondition layer before acting on named entities (confidence-gated binding, clarification under ambiguity).
3. **Geopolitics & Strategic Analysis** — corporate-registry ER underpins sanctions-evasion detection (OFAC list matching, [[ofac-sanctions-enforcement-2026]]), beneficial-ownership tracing, DPRK IT-worker evasion mapping ([[dprk-it-worker-sanctions-evasion]]); conservative merge policy matters when a false identity merge corrupts a designation case.
4. **Markets & Financial Analysis** — duplicate-entity risk in financial datasets (vendor IDs, legal entity identifiers) corrupts alt-data signals; merge-is-destructive applies to financial data lakes ([[privacy-preserving-entity-resolution-osint]]).
5. **Knowledge Graph Construction** — Curate Before You Connect conformance debt, secondary-class compensation, and curation queue are directly reusable in Exocortex KG design ([[knowledge-graph-construction-patterns]]).
6. **Entity Resolution as Agent Safety** — error asymmetry (merge is destructive, non-merge recoverable) is the design principle that makes ER a safety substrate rather than a data-engineering nicety ([[entity-resolution-agent-safety]]).
7. **Evidence Preservation & Chain of Custody** — curated identity decisions with anchored evidence connect to OSINT evidence standards ([[evidence-preservation-chain-of-custody-osint]]).
8. **Intelligence Failure Analysis** — over-trust in LLM self-explanations is a mirror-imaging / plausible-but-wrong evidence failure isomorphic to classic intelligence failure patterns ([[intelligence-failure-analysis]]).
9. **Corporate Registry Investigation** — identity ladders operationalize corporate-registry resolution across jurisdictions ([[corporate-registry-investigation-osint]]).
10. **Entity Resolution Confidence & Uncertainty Calibration** — conservative gating and confidence thresholds connect directly to ER calibration work ([[entity-resolution-confidence-calibration]]).

---

## 7. Sources

1. Dangaich, Lewis, Pundalik — *Curate Before You Connect: Identity and Ontology Tagging in a Production Knowledge Graph* (arXiv:2608.10644; abstract verified 2026-08-18)
2. Sapram, Raju, Konda — *Domain-Specific Text Embedding Models for Entity Resolution* (arXiv:2608.16161; abstract verified 2026-08-18)
3. Teofili, Firmani, Koudas, Merialdo, Srivastava — *Can We Trust LLM Self-Explanations for Entity Resolution?* (arXiv:2606.01210; abstract verified 2026-08-18)
4. Papadakis et al. — *Agentic ER* (arXiv:2607.27435; via [[agentic-entity-resolution]])
5. Babu & Indukuri — *Entity Binding Failures* (arXiv:2606.30531; via [[entity-resolution-agent-safety]])
6. Splink (moj-analytical-services/splink) production architecture — DeepWiki verification
7. Exocortex shared corpus — search_memory/search_all (agentic-entity-resolution, entity-resolution-pipeline-performance, entity-resolution-agent-safety, sanctions-evasion-detection)
8. 355-book reference library — search_library (honest gap: no record-linkage title)
