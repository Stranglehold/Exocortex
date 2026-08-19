# Cross-Jurisdictional Data Linking

**Status: STABLE**
**Created: 2026-05-20**
**Last deepened: 2026-05-20**

## Summary

Cross-jurisdictional data linking addresses the challenge of resolving entities across
legal and administrative boundaries where naming conventions, identifier formats, filing
standards, and data availability differ fundamentally. This is the hardest sub-problem in
entity resolution — same-country matching can achieve 95%+ F1, but cross-border resolution
typically drops to 60-80% without specialized techniques.

---

## Core Challenges

### 1. Naming Convention Divergence
- Romanization/transliteration inconsistencies (e.g., Cyrillic → Latin: multiple standards)
- Legal entity suffix variations (Ltd, GmbH, Pty Ltd, S.A., S.p.A., KK, OOO)
- Name order differences (Western given-name-first vs Eastern family-name-first)
- Diacritic handling and Unicode normalization (NFKD/NFKC required)

### 2. Identifier Format Heterogeneity
- No universal company identifier — each jurisdiction uses its own (EIN, LEI, DUNS, VAT, CRN, etc.)
- Identifier collision risk across registries (same number, different entities)
- Some jurisdictions use numeric IDs, others alphanumeric, varying lengths
- Cross-reference tables (LEI↔DUNS↔CRN) exist but are incomplete and proprietary

### 3. Filing Standards and Data Quality
- Disclosure thresholds vary by jurisdiction (US: $200+ per individual donor annualized; EU: GDPR-constrained)
- Reporting periodicity differs (quarterly, annual, ad hoc)
- Data format heterogeneity (PDF scans vs structured XML/JSON/CSV APIs)
- Missing data is jurisdiction-coded, not random — e.g., jurisdictions with weak disclosure laws

### 4. Access and Availability
- Some registries are publicly searchable, others require paid access or registration
- Rate limiting and API access patterns differ
- Language barriers in non-English registries

---

## Technical Approaches

### Deterministic Matching
- **Name normalization**: Remove legal suffixes, punctuation, Unicode normalization (NFKC)
- **Token-index matching**: Build inverted indexes of normalized name tokens for O(1) candidate lookup
- **Multi-field exact matching**: Tax ID + jurisdiction code, registration number + country

### Probabilistic Matching
- **Fellegi-Sunter model**: Bayesian framework computing match weights from agreement/disagreement
  patterns across multiple fields. Produces a composite score with threshold classification
  (match/non-match/possible).
- **String similarity**: Levenshtein, Jaro-Winkler, TF-IDF cosine similarity across multi-lingual fields
- **Graph-based resolution**: Entity co-occurrence networks across corporate registries; community
  detection algorithms (Louvain, Leiden) for cluster-based resolution

### Hybrid Approaches
- **Staged resolution pipeline**: Within-jurisdiction deterministic → cross-jurisdiction probabilistic
- **Active learning for edge cases**: Human-in-the-loop for ambiguous matches (dedupe, Zingg libraries)
- **Consensus-based resolution**: Multiple matchers vote, discordant results flagged for review

---

## Implementation Reference: OpenPlanter Entity Resolution Pipeline

**Primary source**: `/a0/usr/workdir/openplanter_study/scripts/entity_resolution.py` (753 lines)
**Companion source**: `/a0/usr/workdir/openplanter_study/scripts/cross_link_analysis.py` (585 lines)

The OpenPlanter pipeline connects Boston municipal contract vendors to Massachusetts OCPF
campaign finance donors/employers across heterogeneous datasets, implementing a two-phase
approach directly applicable to cross-jurisdictional linking.

### Phase 1: Name Normalization (`normalize_name()`)
Removes legal entity suffixes (INC, LLC, CORP, LTD, CO, LIMITED, GROUP, HOLDINGS, etc.) via regex,
strips punctuation and diacritics, and collapses whitespace. An aggressive variant additionally
removes common business words (SERVICES, SOLUTIONS, TECHNOLOGIES, CONSULTING, MANAGEMENT).

This directly addresses naming convention divergence: the same company registered as
"Acme Technologies International Ltd" in one jurisdiction and "ACME TECH INTL" in another
normalizes to the same token string.

### Phase 2: Token-Index Matching
Builds an inverted index mapping normalized name tokens to candidate IDs for O(1) lookup.
Compares candidate entities across datasets (Boston procurement vs OCPF campaign finance)
using token overlap scoring. The pipeline demonstrates cross-jurisdictional patterns:
different identifier schemes (contract IDs vs CPF IDs), different filing formats, and
different data dictionaries across administrative domains.

### Multi-Source Integration (15 data sources)
The OpenPlanter test suite integrates: Boston procurement, SAM.gov, USAspending, OCPF
(Massachusetts), FEC (federal), SEC EDGAR, FDIC, ICIJ Offshore Leaks, OFAC SDN, EPA ECHO,
OSHA, ProPublica 990, Census ACS, Senate lobbying disclosures, and international sanctions
lists — spanning 4+ jurisdictions demonstrating the full heterogeneity problem.

---

## Exocortex Integration Research

### Fellegi-Sunter Model (Bayesian Record Linkage)
The industry standard for probabilistic multi-field record linkage. Computes match weights
from agreement/disagreement patterns. A field that agrees on a rare value contributes more
match weight than one that agrees on a common value. The composite score is compared against
thresholds calibrated for the specific domain.

### Active Learning Tools
- **Zingg**: Java/Python library, builds resolution models from labeled examples. Suitable
  for domains where deterministic rules are hard to specify upfront.
- **dedupe**: Python library with active learning UI for single-machine datasets. Widely used
  in investigative journalism for cross-dataset entity linking.

### Multi-Agent RAG for Entity Resolution (MDPI Computers, Dec 2025)
Specialized LLM agents for blocking, matching, and verification phases. The multi-agent
pattern scales to cross-jurisdictional complexity where specialized agents handle
jurisdiction-specific normalization.

### Observation Masking for Resolution Evidence
When cross-jurisdictional resolution produces a false negative, raw evidence (SQL queries,
field comparisons, threshold values) must be preserved. LLM summarization would say
"no match found" and lose the evidence of why. Observation masking preserves this for
future re-evaluation when new data becomes available.

---

## Exocortex Cross-Domain Connections

| Component | Connection |
|-----------|-----------|
| Epistemic Integrity | Provenance tracking for cross-jurisdictional match decisions — which fields agreed/disagreed, which normalization was applied |
| Deterministic Scaffolding | Two-phase resolution pipeline (normalize → match) installs structured workflow into LLM's non-deterministic reasoning |
| Build the Environment | Cross-jurisdictional data dictionaries, suffix registries, and normalization rules define a reproducible matching environment |
| Context Pruner | Observation masking preserves raw evidence from failed cross-border matches rather than summarizing to "no match" |
| Proactive Interference | Cached within-jurisdiction resolution results may interfere when a cross-jurisdictional link is later discovered — requires cache invalidation |
| Knowledge Graph Construction | Property graph representation captures jurisdiction-specific entity nodes linked by resolution edges with confidence weights |
| Human Investigation / OSINT | Cross-jurisdictional corporate records, campaign finance, and sanctions data are primary OSINT sources for entity identification |
| Privacy / Cryptography | GDPR compliance constrains cross-EU data linking; PSI and homomorphic encryption enable privacy-preserving resolution |
| History of Intelligence Operations | Intel community entity resolution evolved from manual index cards (WWII OSS) to automated cross-database matching (CIA HYDRA/TIDE) — same core challenge, different scale |
| Palantir Architecture | Foundry/Gotham ontology layer performs cross-jurisdictional object resolution as a core capability, mapping heterogeneous source identifiers to unified entity objects |

---

## See Also

- [[data-aggregation-entity-resolution]]
- [[human-investigation-osint]]
- [[knowledge-graph-construction]]
- [[palantir-architecture]]
- [[geopolitics-strategic-analysis]]
- [[privacy-cryptography]]
- [[email-forensics-header-analysis]]
- [[domain-whois-dns-investigation]]
