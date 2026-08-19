# Data Lineage & Provenance in Entity Resolution Pipelines

**Status: STABLE** | Created: 2026-07-06 | Last Updated: 2026-07-06
**Deepened from DRAFT by BUILD cycle: arxiv + web deep research integration**

---

## 1. Overview

Entity resolution (ER) — the task of determining whether two or more records refer to the same real-world entity — is inherently uncertain. Every match decision is a probabilistic inference built atop imperfect data from heterogeneous sources. Without provenance, the resolved entity is a black box: you know the output, but not why it exists, which sources contributed to it, how conflicts were resolved, or how much trust to place in the conclusion.

**Data provenance** records the origin and processing history of data — the *who, what, when, where, why, and how* of every data artifact. **Data lineage** is the subset of provenance concerned with transformation chains: how data moved and changed through a pipeline. In ER pipelines, provenance serves four critical functions:

1. **Epistemic integrity**: users and downstream systems can judge whether a resolved entity is trustworthy rather than taking it on faith.
2. **Reproducibility and debugging**: analysts can trace a suspicious match back to its raw sources and identify which pipeline stage introduced an error.
3. **Cross-validation**: when multiple sources agree or conflict, provenance chains reveal which sources carry how much weight, enabling informed conflict resolution.
4. **Agent memory qualification**: autonomous agents retrieving facts from a knowledge base can annotate claims with provenance metadata, distinguishing grounded assertions from inferred ones.

Oppold and Herschel (2018) established the first formal provenance model tailored to ER, observing that naive data provenance — "which input records produced this output cluster" — is tautological in ER because the output cluster *is* the set of matching input records. Meaningful ER provenance must instead describe *how* data flowed through each pipeline stage: how blocking partitioned the search space, how pairwise comparisons were scored, and how clusters were formed and constrained.

---

## 2. Key Provenance Models and Standards

### 2.1 W3C PROV Standard (PROV-O)

The W3C PROV family of specifications (PROV-DM, PROV-O, PROV-N) provides an ontology for representing provenance information. Its core model revolves around three primitives:

- **Entities** (`prov:Entity`): data artifacts — raw records, candidate pairs, clusters, resolved entities.
- **Activities** (`prov:Activity`): processes that generate or modify entities — blocking, pairwise comparison, classification, clustering, post-processing.
- **Agents** (`prov:Agent`): entities responsible for activities — matching algorithms, human annotators, LLM-based matchers.

The relationships `wasGeneratedBy`, `used`, `wasDerivedFrom`, and `wasAttributedTo` form directed acyclic graphs linking outputs back through activities to inputs. Jain (2025, arXiv:2501.09029) demonstrated PROV-O applied to multi-domain data integration, using RDF triples and SPARQL queries to trace integrated records across heterogeneous source systems. TrustGraph (trustgraph-ai) implements PROV-O with custom extensions (`tg` namespace) for GraphRAG provenance, tracking both extraction-time lineage (which document/chunk/LLM produced each triple) and query-time explainability (the reasoning path from user question to answer).

### 2.2 OpenLineage

OpenLineage is an open standard for collecting data lineage from pipeline orchestration systems. Unlike PROV-O's fine-grained entity/activity model, OpenLineage operates at the job and dataset level:

- **Run events**: a pipeline stage starts and completes (e.g., "ER matching job v3 ran on dataset D at time T").
- **Input/output facets**: schema, statistics, and lifecycle metadata for datasets consumed and produced.
- **Integration with Marquez**: Marquez consumes OpenLineage events, stores them in a metadata service, and provides lineage visualization.

An ER pipeline integrated with OpenLineage would emit events showing: `[Raw Source A, Raw Source B] → ER Blocking Job → Candidate Pairs → ER Matching Job → Resolved Entities`. This provides table-level observability but not row-level provenance — it tells you *which job* ran on *which dataset*, not *which specific input record* contributed to *which output entity*. Row-level ER provenance at production scale remains an open research challenge.

### 2.3 NRAB-Based ER Provenance Model (Oppold & Herschel, 2018)

The foundational ER-specific provenance model maps ER pipelines to trees of algebraic operators expressed in Nested Relational Algebra for Bags (NRAB). This provides a language-independent formal semantics that covers:

- **Pre-processing**: normalization, cleaning, standardization.
- **Blocking**: Cartesian product with blocking predicates → candidate pair generation.
- **Pairwise Matching**: selection operators applying similarity functions to attribute pairs.
- **Classification**: selection operators applying match/non-match thresholds.
- **Clustering**: grouping operators with transitive closure.
- **Post-processing**: cardinality constraints (e.g., 1:1 matching enforcement).

Each operator in the tree contributes provenance metadata showing how pairs were formed, compared, scored, and resolved. The proof-of-concept instrumented HIL (High-Level Integration Language) ER rules to return both the resolution result and provenance data in the same output format, enabling seamless downstream consumption.

### 2.4 RDF Named Graphs (TrustGraph Approach)

TrustGraph partitions knowledge graph triples into RDF named graphs, separating core knowledge from provenance metadata. Three layers coexist within the same graph database:
- **Core graph**: resolved entities and their relationships (the "clean" knowledge).
- **Extraction provenance graph**: which document, chunk, and extraction pipeline produced each triple.
- **Query provenance graph**: which reasoning steps produced each query answer.

This separation keeps the core knowledge graph queryable without provenance noise while enabling SPARQL queries that join across layers when provenance is needed.

---

## 3. Architecture for Provenance-Aware ER Pipelines

A provenance-aware ER pipeline extends the standard multi-stage ER architecture (blocking → comparison → classification → clustering) with a parallel provenance capture layer:

```
Layer 1: Ingestion & Source Attribution
  Raw sources → Source Registry (reliability score, format, freshness)
  Every ingested record tagged with source provenance triple:
    (record_id, prov:wasDerivedFrom, source_document_id)

Layer 2: Pipeline Instrumentation
  Each ER stage (blocking, pairwise matching, classification, clustering)
  emits provenance events:
    - Stage input/output record sets
    - Algorithm parameters and version
    - Intermediate scores and decisions
    - Timestamps and execution context

Layer 3: Provenance Store
  Graph database (e.g., labeled property graph or RDF store) captures:
    (InputRecord) -[BLOCKED_IN]-> (Block) -[PRODUCED]-> (CandidatePair)
    (CandidatePair) -[SCORED_BY]-> (Matcher) -[YIELDED]-> (MatchScore)
    (MatchScore) -[CLASSIFIED_AS]-> (Decision) -[CLUSTERED_INTO]-> (Cluster)
    (Cluster) -[CONSTRAINED_TO]-> (ResolvedEntity)

Layer 4: Query & Annotation Layer
  Resolved entities carry provenance annotations:
    - Source list with individual reliability scores
    - Processing chain hash (tamper detection)
    - Match confidence distribution
    - Conflict resolution log (which sources disagreed, how resolved)
    - Human-in-the-loop interventions (who, when, what)
```

The Oppold & Herschel proof-of-concept demonstrated Layer 2 instrumentation by modifying HIL ER rules to return provenance alongside results. TrustGraph demonstrates Layer 4 in production for knowledge graph construction. OpenLineage + Marquez provides Layer 2 at the job/dataset granularity for pipeline observability. The key architectural gap remains **unified row-level provenance capture at scale** combining the formal rigor of the NRAB model with the operational observability of OpenLineage.

---

## 4. Source Reliability Scoring

### 4.1 Admiralty Code Adaptation

The Admiralty Code (NATO intelligence rating system) provides a two-dimensional framework for source evaluation that maps naturally to ER source attribution:

- **Reliability (A-F)**: the source's historical track record.
  - A: Completely reliable — government registry with cryptographic integrity.
  - B: Usually reliable — curated commercial database with audit trail.
  - C: Fairly reliable — user-generated content with moderation.
  - D: Not usually reliable — unverified web scraping.
  - E: Unreliable — known error-prone source.
  - F: Reliability cannot be judged — novel or uncharacterized source.

- **Credibility (1-6)**: the specific record's internal consistency and corroboration.
  - 1: Confirmed by multiple independent sources.
  - 2: Probably true — consistent with other known facts.
  - 3: Possibly true — plausible but uncorroborated.
  - 4: Doubtful — inconsistent with other data.
  - 5: Improbable — contradicted by reliable sources.
  - 6: Truth cannot be judged — insufficient context.

In an ER pipeline, every source registry entry carries a (reliability, credibility) tuple. When records from multiple sources are matched into a cluster, the cluster inherits a weighted reliability vector reflecting the composition of contributing sources.

### 4.2 Fellegi-Sunter as Provenance Signal

The Fellegi-Sunter probabilistic framework provides match probabilities (m-probability, u-probability) for attribute agreement patterns. These probabilities serve as provenance signals:

- **High m-probability attributes** (e.g., government-issued ID numbers) signal strong provenance — agreement on these attributes is rare by chance.
- **Low m-probability attributes** (e.g., shared email domain) signal weak provenance — agreement is common and less informative.

The per-attribute agreement vector can be stored as provenance metadata, enabling downstream consumers to see *which* attributes drove the match decision and *how strongly*.

---

## 5. Confidence Propagation Through Resolution Chains

Entity resolution is rarely a single-step process. Records pass through blocking → candidate generation → pairwise scoring → classification → clustering → post-processing. Each stage introduces uncertainty, and these uncertainties compound.

### 5.1 Stage-Level Confidence Tracking

| Pipeline Stage | Confidence Factor | Tracking Mechanism |
|---------------|-------------------|-------------------|
| Blocking | Recall risk (missed true matches) | Blocking key coverage statistics |
| Pairwise Matching | Similarity score distribution | Per-attribute similarity vectors |
| Classification | Decision boundary proximity | Distance from threshold, score margin |
| Clustering | Transitive closure risk (A matches B, B matches C, but A ≠ C) | Cluster coherence score |
| Post-processing | Cardinality constraint violations | Constraint satisfaction metrics |

### 5.2 Propagation Mathematics

For a resolved entity *E* formed from source records *R₁, R₂, …, Rₙ* through pipeline stages *S₁, S₂, …, Sₖ*:

$$\text{confidence}(E) = f(\text{source\_reliability}(R₁…Rₙ), \text{match\_scores}, \text{cluster\_coherence}, \text{constraint\_satisfaction})$$

A naive multiplicative model: `confidence(E) = min(source_reliability, match_confidence, cluster_coherence, constraint_satisfaction)` — the chain is only as strong as its weakest link. More sophisticated Bayesian models update a prior based on evidence strength at each stage.

### 5.3 LEMON's Dual Explanation Framework

Barlaug's LEMON (2021, arXiv:2110.00516) introduced a dual explanation paradigm for ER decisions:

- **Match explanations**: which attributes caused two records to be matched (attribute-level attribution).
- **Non-match explanations**: why two records were NOT matched — the harder and more valuable explanation. LEMON's non-match explanations achieved 49% improvement over baselines in user studies.

This framework extends confidence into *explainability*: confidence tells you how certain the system is; LEMON-style attributions tell you *why* it's certain, enabling human auditors to judge whether the certainty is justified.

---

## 6. Trust Scoring Mechanisms

### 6.1 PageRank-Style Trust Propagation

When entities are resolved into a knowledge graph, trust can propagate along graph edges. TrustGraph's architecture models this implicitly: if entity *A* cites entity *B*, and *A* has high provenance quality, *B* inherits some of that trust. This is analogous to PageRank, where the "authority" of a node is a function of the authority of nodes that link to it.

For ER clusters: if a cluster contains records from multiple high-reliability sources that independently agree, the cluster's trust score increases beyond a simple average — the independence of agreement provides a multiplicative confidence boost (Bayesian updating with conditionally independent evidence).

### 6.2 Bayesian Trust Updating

A Bayesian trust model for resolved entity *E*:

$$P(\text{correct} \mid \text{source\_agreement}) = \frac{P(\text{source\_agreement} \mid \text{correct}) \cdot P(\text{correct})}{P(\text{source\_agreement})}$$

Where:
- Prior *P(correct)* = base rate of match correctness for this pipeline.
- Likelihood *P(source_agreement | correct)* = probability that independent sources would agree given the entity is correctly resolved.
- Likelihood *P(source_agreement | ¬correct)* = probability of coincidental agreement from unrelated entities.

This formalizes the intuition that agreement among independent, reliable sources is stronger evidence than agreement among correlated or unreliable sources.

### 6.3 Composite Trust Score (Research Gap)

**Critical finding**: no reviewed paper or system proposes an explicit composite trust scoring function for resolved entities combining:
1. Source reliability (Admiralty Code or equivalent).
2. Provenance completeness (what fraction of the pipeline is traced?).
3. Match confidence (Fellegi-Sunter probability).
4. Historical accuracy (how often has this pipeline/source combination produced correct results?).
5. Corroboration depth (how many independent sources agree?).

This represents the clearest opportunity for original contribution — a weighted trust score that ER systems and knowledge graphs can use to annotate every resolved entity with a calibrated confidence metric.

---

## 7. Provenance Query Patterns for ER Debugging

A provenance-aware ER pipeline enables structured debugging queries that are impossible in black-box systems:

### 7.1 Root Cause Analysis
```sparql
# Why were records A and B resolved as the same entity?
SELECT ?stage ?operation ?parameter ?intermediate_result
WHERE {
  ?resolution prov:wasGeneratedBy ?process .
  ?process prov:used ?recordA, ?recordB .
  ?intermediate prov:wasDerivedFrom ?recordA, ?recordB .
  ?intermediate prov:wasGeneratedBy ?stage .
  ?stage prov:qualifiedAssociation [
    prov:hadPlan ?operation ;
    prov:agent ?parameter
  ] .
}
```

### 7.2 Source Contribution Audit
```sparql
# Which sources contributed to entity E, and with what reliability?
SELECT ?source ?reliability ?credibility ?attribute_contribution
WHERE {
  ?entity prov:wasDerivedFrom ?source_record .
  ?source_record prov:wasAttributedTo ?source .
  ?source :hasReliability ?reliability ;
          :hasCredibility ?credibility .
  ?entity :attributeContribution ?attribute_contribution .
}
```

### 7.3 Pipeline Impact Analysis
```
# If blocking key K is changed, which resolved entities would be affected?
SELECT ?entity ?current_match ?affected_status
WHERE {
  ?entity prov:wasGeneratedBy ?clustering .
  ?clustering prov:used ?candidate_pair .
  ?candidate_pair prov:wasGeneratedBy ?blocking .
  ?blocking prov:qualifiedAssociation [ prov:hadPlan :blocking_key_K ] .
}
```

### 7.4 Confidence Drift Detection
Track how confidence scores change across pipeline versions:

$$\Delta\text{confidence} = \text{confidence}_{\text{v2}}(E) - \text{confidence}_{\text{v1}}(E)$$

A significant negative drift signals potential regressions in matching logic, source quality degradation, or schema changes that broke attribute mappings.

---

## 8. Integration with Knowledge Graphs and GraphRAG

### 8.1 Property Graph with Provenance Edges

In a labeled property graph (Neo4j/LPG model), provenance becomes first-class graph structure:

```
(:Source {reliability: "A", credibility: 1})
  -[:PROVIDED]-> (:RawRecord)
  -[:BLOCKED_INTO]-> (:Block)
  -[:PRODUCED]-> (:CandidatePair {similarity: 0.87})
  -[:SCORED_BY]-> (:Matcher {algorithm: "jaro-winkler", version: "2.1"})
  -[:RESOLVED_TO]-> (:ResolvedEntity {confidence: 0.93})
```

This enables graph traversal queries that walk from resolved entities backward through the entire processing chain to raw sources, or forward from sources to all entities they influenced.

### 8.2 GraphRAG with Provenance-Grounded Retrieval

TrustGraph demonstrates how provenance enables GraphRAG systems to return *grounded* answers. When a user asks "What companies does Person X control?", the system retrieves relevant entities AND their provenance chains:

- Entity: `Person X` → derived from SEC filing F-2024-Q3, extracted by LLM v3.2, chunk C42.
- Relationship: `Person X controls Company Y` → derived from ownership table T, validated against state registry R.

This prevents the oracle problem in agent systems: the agent does not just assert facts; it cites the provenance chain that produced each assertion, enabling the user (or supervisor agent) to independently evaluate trustworthiness.

### 8.3 Provenance for Epistemic Status Tagging

Every fact in a provenance-aware knowledge graph carries an epistemic status derived from its provenance:

| Status | Provenance Pattern | Example |
|--------|-------------------|---------|
| GROUNDED | Single authoritative source + cryptographic verification | Government registry with digital signature |
| CORROBORATED | Multiple independent sources with agreement | 3+ registries showing same company ownership |
| INFERRED | Derived via resolution pipeline from lower-confidence sources | LLM-matched records with 0.78 confidence |
| UNVERIFIED | Single low-reliability source, no corroboration | Web scrape of unverified directory |
| DISPUTED | Sources conflict, resolution required human intervention | Two databases showing different corporate parents |

---

## 9. Cross-Domain Connections to the Exocortex Stack

### 9.1 Entity Resolution Agent Safety
Provenance is the structural antidote to oracle fabrication by AI agents. When an agent retrieves a resolved entity from a knowledge graph, the provenance chain provides verifiable grounding — the agent can cite *which* sources produced the entity, *how* it was matched, and *how confident* the system is. This transforms agent assertions from opaque claims into auditable inferences. The evidence-chain pattern (claim → evidence → source → confidence) structurally prevents fabrication by requiring provenance at assertion time.

### 9.2 Epistemic Integrity Layer
Provenance-aware ER directly implements the Epistemic Integrity layer's core function: qualifying every knowledge artifact with its origin, processing history, and confidence. The epistemic status tags (GROUNDED, CORROBORATED, INFERRED, UNVERIFIED, DISPUTED) derived from provenance metadata enable downstream systems — agent supervisors, irreversibility gates, human auditors — to make risk-aware decisions based on information quality rather than treating all data as equally trustworthy.

### 9.3 Memory Consolidation
In the Exocortex memory architecture, provenance determines attentional salience. Facts with rich provenance (multiple independent, reliable sources) receive higher salience weights during memory consolidation. Facts with thin provenance (single unverified source) are retained but flagged as low-confidence, subject to re-verification or expiry. This parallels the LEMON framework's dual explanation: not just *what* is remembered, but *why* it was considered worth remembering.

### 9.4 Irreversibility Gate
Irreversible actions in the Exocortex — committing a fact to the knowledge graph, emitting a notification, triggering an external API call — should be gated by provenance strength. The irreversibility gate can implement rules like:

- **GROUNDED or CORROBORATED entities**: automatic commit.
- **INFERRED entities**: commit with warning flag, human review optional.
- **UNVERIFIED entities**: block commit, require human approval.
- **DISPUTED entities**: block commit, escalate for resolution.

This directly connects ER provenance to operational safety: the confidence in a resolved entity determines what actions that entity can trigger.

### 9.5 Counterintelligence and Data Poisoning Detection
Provenance metadata enables anomaly detection for adversarial data manipulation. If a source that historically produced records with high agreement rates suddenly produces records that conflict with all other sources, the provenance system flags this as a potential poisoning attack. Changes in source reliability over time — tracked via provenance metadata rather than static scores — provide early warning of compromised data feeds.

### 9.6 Cross-Source Triangulation
OpenPlanter's cross-source analysis methodology (name normalization → cross-link detection → timing analysis → pattern recognition) becomes strictly more powerful when each cross-link carries provenance. Instead of binary "records are linked," the system can distinguish:
- Links backed by cryptographically verified identifiers.
- Links inferred from fuzzy name matching with moderate confidence.
- Links derived from temporal coincidence (same address at same time).
- Links identified by LLM semantic reasoning (lowest provenance quality).

---

## 10. References

1. Oppold, S. & Herschel, M. (2018). "Provenance for Entity Resolution." *7th International Provenance and Annotation Workshop (IPAW 2018)*, London, UK. Springer LNCS. https://link.springer.com/chapter/10.1007/978-3-319-98379-0_25 — **Foundational**: first ER-specific provenance model using NRAB-based operator trees; proof-of-concept with HIL instrumentation.

2. Barlaug, N. (2021). "LEMON: Explainable Entity Matching." arXiv:2110.00516. https://arxiv.org/abs/2110.00516 — Dual explanation framework for ER (match + non-match attributions); 49% improvement on non-match explanations; user study methodology for evaluating explainability.

3. Jaitly, S. et al. (2022). "xEM: Explainable Entity Matching in Customer 360." arXiv:2212.00342. https://arxiv.org/abs/2212.00342 — IBM production demo of explainable ER for enterprise customer data integration.

4. Jain, N. (2025). "Enhancing Data Integrity through Provenance Tracking in Semantic Web Frameworks." arXiv:2501.09029. https://arxiv.org/abs/2501.09029 — W3C PROV-O applied to multi-domain data integration; RDF + SPARQL for provenance querying.

5. PROMPTATTRIB (2025). "Attribute-Level Prompt Tuning for Entity Matching with Logical Reasoning." arXiv:2507.14660 — LLM-based ER with attribute-level prompt engineering and fuzzy logic reasoning.

6. Bertossi, L. (2020). "Score-Based Explanations in Data Management and Machine Learning." arXiv:2007.12799. https://arxiv.org/abs/2007.12799 — Causal and counterfactual score-based explanations applicable to ER pipeline decisions.

7. TrustGraph Project. "Provenance & Explainability." https://deepwiki.com/trustgraph-ai/trustgraph/15-provenance-and-explainability — Production GraphRAG platform with W3C PROV-O provenance; named graph separation; extraction-time and query-time lineage.

8. OpenLineage. https://openlineage.io/ — Open standard for data lineage collection; Marquez metadata service; table-level pipeline observability.

9. Herschel, M., Diestelkamper, R., & Lahmar, H. B. (2017). "A survey on provenance: What for? What form? What from?" *VLDB Journal*, 26(6), 881-906. — Comprehensive provenance survey providing classification framework.

10. Christen, P. (2012). *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection.* Springer. — Foundational ER textbook; Fellegi-Sunter framework; blocking, comparison, classification, clustering methodology.

---

## 11. Research Gaps

1. **Composite trust scoring**: No existing system combines source reliability, provenance completeness, match confidence, and historical accuracy into a single trust score.
2. **Row-level ER provenance at scale**: OpenLineage provides table-level lineage; Oppold & Herschel's model provides row-level formal semantics but at academic proof-of-concept scale.
3. **ER-specific PROV extension**: PROV-O is generic; an ER-specific extension (ER-PROV?) with domain-specific entities and activities would improve interoperability.
4. **Unified operational + decision provenance**: Bridging pipeline provenance (Oppold & Herschel) with decision attribution (LEMON) for end-to-end traceability.
5. **Streaming ER provenance**: All reviewed systems assume batch processing; real-time provenance capture for streaming ER (Kafka-based) is unexplored.
6. **Provenance-aware blocking**: Current ER provenance models capture what happens after blocking; how blocking decisions themselves should carry provenance metadata is under-theorized.

---

*Deepened from DRAFT to STABLE via arxiv + web research, BUILD cycle. 10 references, 6 cross-domain Exocortex connections.*
