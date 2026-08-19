# Data Aggregation & Entity Resolution

**Status: STABLE**
**Topic Slug: data-aggregation-entity-resolution**
**Created: 2026-05-15 | Last deepened: 2026-05-19**
**Interest Origin: Palantir thesis (~2021), OpenPlanter evaluation (2026)**
**Primary Sources:** entity_resolution.py, cross_link_analysis.py (OpenPlanter study), field report 2026-05-09

---

## Abstract

Entity resolution (ER) — the task of determining whether two records from different datasets refer to the same real-world entity — is the critical bridge between raw heterogeneous data and actionable intelligence. Without it, corporate registries, campaign finance records, lobbying disclosures, government contracts, and property records remain disconnected silos. With effective ER, non-obvious connections surface: a city contractor whose officers donated to the officials who approved the contract; a lobbying firm sharing a registered address with a vendor receiving sole-source awards.

The current state of the art combines deterministic blocking and normalization (heavy lift) with probabilistic matching (Fellegi-Sunter models) and, increasingly, LLM-based verification for edge cases. OpenPlanter's entity_resolution.py implements a practical two-phase pipeline (normalization → token-index matching) on Massachusetts municipal contracting and campaign finance data that demonstrates the core pattern at ~750 lines of Python.

---

## Core Question

How do you take heterogeneous datasets — corporate registries, campaign finance records, lobbying disclosures, government contracts, property records — and resolve entities across them to surface non-obvious connections?

Sub-questions:
1. What normalization strategies handle the same legal entity appearing as "ACME Corp.", "Acme Corporation", and "ACME CORP INC" across datasets?
2. How do blocking strategies (pre-filtering candidate pairs) scale to millions of records without missing true matches?
3. When should deterministic rules give way to probabilistic matching, and when should LLMs enter the pipeline?
4. How do you preserve failure evidence so that a false negative (missed match) can be investigated rather than lost?

---

## Primary Source: OpenPlanter Entity Resolution Pipeline

### Implementation (`/a0/usr/workdir/openplanter_study/scripts/entity_resolution.py`, 753 lines)

The OpenPlanter ER pipeline connects Boston municipal contract vendors to Massachusetts OCPF campaign finance donors/employers. It implements a two-phase approach:

#### Phase 1: Name Normalization

```python
def normalize_name(name):
    """Normalize a company/organization name for matching."""
    name = name.upper().strip()
    name = name.replace('"', '').replace("'", '')
    # Remove common suffixes: INC, LLC, CORP, LTD, CO, etc.
    suffixes = [
        r'\bINC\.?\b', r'\bLLC\.?\b', r'\bCORP\.?\b', r'\bLTD\.?\b',
        r'\bCO\.?\b', r'\bCOMPANY\b', r'\bCORPORATION\b', r'\bINCORPORATED\b',
        r'\bL\.?L\.?C\.?\b', r'\bLIMITED\b', r'\bGROUP\b', r'\bSERVICES\b',
        r'\bENTERPRISE[S]?\b', r'\bHOLDINGS?\b', r'\bINTERNATIONAL\b',
        r'\bAMERICA[S]?\b', r'\bASSOCIATES?\b', r'\bPARTNERS?\b',
        r'\bSOLUTIONS?\b', r'\bTECHNOLOG(Y|IES)\b', r'\bCONSULTING\b',
        r'\bMANAGEMENT\b',
    ]
    for suffix in suffixes:
        name = re.sub(suffix, '', name)
    # Remove punctuation
    name = re.sub(r'[.,;:!@#$%^&*()_\-+=\[\]{}|\\/<>~`]', ' ', name)
    # Collapse whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def normalize_name_aggressive(name):
    """Even more aggressive normalization - just alpha tokens sorted."""
    n = normalize_name(name)
    tokens = sorted(set(n.split()))
    return ' '.join(tokens)
```

Key design decisions:
- **Suffix stripping** handles the INC/LLC/CORP variation that is the most common source of false negatives in regulatory datasets.
- **Aggressive normalization** (sorted unique tokens) handles transpositions like "Smith John Consulting" vs "John Smith Consulting" — loses some discriminative power but catches name-order variations.
- **Minimum token length filter** (`len(token) >= 4`) in the matching phase prevents common short tokens ("THE", "AND", "OF") from creating spurious matches.

#### Phase 2: Token-Index Matching

```python
def match_entities(vendors, contributions):
    # Build lookup indexes
    vendor_norm_index = {}  # normalized name -> vendor key
    vendor_token_index = defaultdict(set)  # token -> set of vendor keys

    for norm_name in vendors:
        vendor_norm_index[norm_name] = norm_name
        tokens = norm_name.split()
        for token in tokens:
            if len(token) >= 4:  # Skip short tokens
                vendor_token_index[token].add(norm_name)

    # Build aggressive normalization index
    vendor_aggressive_index = {}
    for norm_name in vendors:
        agg = normalize_name_aggressive(
            list(vendors[norm_name]['original_names'])[0]
        )
        if agg and len(agg) >= 4:
            vendor_aggressive_index[agg] = norm_name
```

The matcher uses three indexes in cascade:
1. **Exact normalized match** — fastest, catches straightforward variations.
2. **Token overlap** — finds records sharing significant tokens, enabling partial matches.
3. **Aggressive normalized match** — catches transpositions and extreme abbreviation differences.

### Cross-Link Analysis (`cross_link_analysis.py`)

The companion script produces structured findings:
- Boston candidates identified from OCPF filings
- Contractor-donor cross-references (vendors who are also donors)
- Sole-source vendor red flags
- Bundled donation events (multiple contributions on the same date)

This represents the **intelligence product** that entity resolution enables — the raw match pairs are not the deliverable; the structured anomalies are.

### Data Sources (15 total in OpenPlanter study)
The pipeline integrates across these domains:
- Contracts: Boston procurement, SAM.gov federal awards, USAspending
- Campaign finance: OCPF (Massachusetts), FEC (federal)
- Corporate: SEC EDGAR filings, FDIC BankFind
- Lobbying: Senate Lobbying Disclosure
- Nonprofits: ProPublica 990 filings
- Sanctions: OFAC SDN list
- Regulatory: EPA ECHO, OSHA inspections
- Infrastructure: Census ACS
- International: ICIJ Offshore Leaks

The cross-domain challenge is that each uses a different identifier system:

| Dataset | Identifier | Temporal Window |
|---------|-----------|-----------------|
| SEC EDGAR | CIK (Central Index Key) | Quarterly filings |
| FEC | Committee ID | Election cycles |
| SAM.gov | DUNS / UEI | Active registrations |
| IRS 990 | EIN (Employer ID Number) | Annual filings |
| OFAC SDN | Name + aliases | Event-driven updates |
| Boston contracts | Vendor name (unstructured) | Fiscal year |

**No single identifier spans all datasets.** The resolution must be name-based with cross-reference validation.

---

## External Research & Tools

### Fellegi-Sunter Model (Industry Standard)

The Fellegi-Sunter model for probabilistic record linkage uses Bayesian statistics to compute match probabilities from agreement/disagreement patterns across multiple fields. It produces a match weight for each field comparison, sums them into a composite score, and applies a threshold to classify pairs as match/non-match/possible.

**Splink** (github.com/moj-analytical-services/splink, 1.9k stars) is the leading open-source implementation. Backed by SQL or Spark, scales to millions of records. Used by UK government (MoJ Algorithmic Transparency Records confirm it as the GOV.UK standard). Key features:
- Fellegi-Sunter model as the core engine
- u-probabilities (probability of chance agreement) trained via expectation-maximization
- Blocking rules to reduce the O(n²) comparison space
- Deterministic rules can be layered with probabilistic scoring

**Splink relevance to OpenPlanter:** The existing entity_resolution.py normalization functions could serve as Splink's `comparison` definitions. Splink would add:
- Proper m/u probability estimation (currently hardcoded thresholds)
- Clustering (transitive closure of match pairs into entity groups)
- Interactive labelling UI for active learning

### Active Learning Tools
- **Zingg** — Java/Python, builds models from labeled examples. Suitable for domains where deterministic rules are hard to specify upfront.
- **dedupe** — Python library, active learning UI for single-machine datasets. Widely used in journalism (investigative data linking).

### Academic Research (2025-2026)
- **Multi-Agent RAG Framework for ER** (MDPI Computers, Dec 2025) — Specialized LLM agents for blocking, matching, and verification phases. Key insight: monolithic LLM approaches suffer from scalability and interpretability limits; multi-agent coordination allows specialization on resolution sub-tasks.
- **Data Integration and Storage Strategies in Heterogeneous Analytical Systems** (MDPI Information, Nov 2025) — Cross-layer taxonomy coupling integration mechanisms (schema matching, entity resolution, semantic enrichment) with storage models. Reproducible workflows for canonical heterogeneity problems.

### Architecture Patterns
- **Deterministic + LLM hybrid** — The dominant emerging pattern: deterministic methods (blocking keys, fuzzy matching, Fellegi-Sunter) handle the heavy lift at scale; LLMs handle edge cases, explanation, and verification.
- **Observation masking > summarization** for failure preservation (JetBrains/TUM, NeurIPS 2025) — When ER produces a false negative, raw evidence (SQL queries, field comparisons, threshold values) must be preserved. LLM summarization would say "no match found" and lose the evidence of why.

---

## Knowledge Graph Construction

Entity resolution is the input to knowledge graph construction. Once entities are resolved, the relationships between them form the graph:

**Property graph (Neo4j):** Nodes have properties (name, address, identifiers); edges have types (DONATED_TO, AWARDED_CONTRACT, EMPLOYED_BY, LOBBYED_FOR). Cypher queries enable path traversal. Neo4j scales to billions of nodes/edges in enterprise deployments.

**RDF (triple store):** Subject-predicate-object triples. Standardized via SPARQL. Better for semantic reasoning and linked data integration across organizations. Less intuitive for ad-hoc investigative queries.

**NetworkX (Python):** In-memory graph library. Suitable for small-to-medium graphs (<1M nodes). Good for rapid prototyping and algorithmic analysis (centrality, community detection).

For the OpenPlanter use case, a **property graph with Neo4j** would be the natural target: the entity resolution pipeline produces match pairs, which get merged into entity nodes, and the original data source edges get attached. The cross_link_analysis.py output (vendor → donation → candidate → contract) is already an edge list.

---

## Exocortex Integration Potential

### 1. Multi-Agent Resolution Pipeline

The multi-agent RAG paper's architecture maps cleanly to Exocortex's subordinate agent pattern:
- **Blocking agent:** Generates candidate pairs from large datasets using deterministic rules (shared tokens, phonetic encoding, geographic proximity).
- **Matching agent:** Scores candidate pairs using Fellegi-Sunter or LLM-based comparison.
- **Verification agent:** Explains and validates high-confidence matches, flags borderline cases for human review.
- **Consensus agent:** Aggregates results across agents (mirrors SWARMFISH committee deliberation).

### 2. Epistemic Integrity for Resolution Claims

Every resolved entity pair must be recorded with provenance:
- Which datasets contributed the records
- Which matching fields were compared
- Which algorithm produced the match
- What confidence score was assigned
- Whether the match was LLM-assisted (higher confabulation risk)

This maps directly to the Evidence Ledger structure — entity resolution pairs are structured data that the ledger was designed to store.

### 3. Failure Preservation (Observation Masking)

The Context Pruner's observation masking pattern is directly applicable: when a match fails, preserve the raw comparison data (field values, scores, thresholds) rather than summarizing as "no match." This enables retrospective debugging when a missed connection is discovered later.

### 4. Tool Integration Path

A dedicated `entity_resolution` skill could wrap Splink or the existing entity_resolution.py pipeline, making it callable as a tool during autonomous cycles. This would enable the agent to perform cross-dataset entity resolution as a standard operation rather than a manual investigation.

### 5. Cross-Domain Connections to Exocortex Components

| Component | Connection |
|-----------|-----------|
| SWARMFISH | Multi-agent committee deliberation for match consensus |
| Epistemic Integrity | Provenance tracking for resolved entity pairs |
| Evidence Ledger | Structured storage of match records with confidence scores |
| Context Pruner | Observation masking for failed resolution attempts |
| Stateful Injection | Caching of resolved entity indexes across turns |
| Knowledge Packs | Pre-resolved entity indexes as curated knowledge bundles |
| Autoresearch | Autonomous identification of new datasets requiring resolution |

---

## Next Steps (Exploration Threads)

1. **Test Splink on OpenPlanter datasets** — Feed FEC, SEC, and SAM.gov data through Splink and measure deduplication quality before attempting cross-domain resolution.
2. **Build a cross-domain entity index** — A lightweight SQLite database mapping `{entity_name, source_dataset, source_id, normalized_name}` across all 15 OpenPlanter sources. Minimum viable step before sophisticated resolution.
3. **Evaluate the multi-agent RAG approach** — Can an Exocortex subordinate agent chain (blocking → matching → verification) outperform Splink alone on government/regulatory datasets?
4. **Investigate ICIJ Offshore Leaks methodology** — ICIJ resolved entities across 40+ jurisdictions with different languages, legal systems, and naming conventions for the Panama Papers. Their deterministic rules + human review methodology is the real-world benchmark.
5. **Skill packaging** — Wrap the entity_resolution.py + cross_link_analysis.py pipeline as an auto-generated skill with Splink integration parameters.

---

## References

- Splink: github.com/moj-analytical-services/splink (Fellegi-Sunter, SQL/Spark backend, UK Government standard)
- MDPI Computers 14(12):525 (2025) — Multi-Agent RAG Framework for Entity Resolution
- MDPI Information 16(11):932 (2025) — Data Integration and Storage Strategies in Heterogeneous Analytical Systems
- JetBrains/TUM, NeurIPS 2025 DL4Code — Observation Masking for Failure Preservation
- Awesome-Entity-Resolution: github.com/OlivierBinette/Awesome-Entity-Resolution
- ICIJ Offshore Leaks Database: offshoreleaks.icij.org
- Zingg: github.com/zinggAI/zingg (Active learning ER)
- dedupe: github.com/dedupeio/dedupe (Python active learning ER)
- OpenPlanter entity_resolution.py: /a0/usr/workdir/openplanter_study/scripts/entity_resolution.py
- OpenPlanter cross_link_analysis.py: /a0/usr/workdir/openplanter_study/scripts/cross_link_analysis.py
- Field Report 2026-05-09: /a0/usr/Exocortex/field-reports/20260509_entity-resolution.md
