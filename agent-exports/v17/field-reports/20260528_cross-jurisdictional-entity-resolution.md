# Field Report — Cross-Jurisdictional Entity Resolution

**Date:** 2026-05-28
**Cycle Type:** EXPLORE
**Interest Category:** Data Aggregation & Entity Resolution
**Sub-topic:** Cross-jurisdictional data linking challenges

---

## 1. What I Explored

Entity resolution across jurisdictions — the problem of linking records about the same legal entity, person, or asset when those records come from different countries' corporate registries, sanctions lists, regulatory filings, and commercial databases. This is the core unsolved problem behind Jake's original Palantir-thesis question: how do you surface non-obvious connections when every jurisdiction formats data differently?

I focused on: the Legal Entity Identifier (LEI) system as a global bridge identifier, OpenCorporates' entity resolution methodology, the shift from fuzzy-only matching to registry-anchored deterministic resolution, and the practical playbook data aggregators use.

## 2. What I Found

### The Fragmentation Problem
- The US alone has **50+ separate corporate registries**, each with its own ID format, naming conventions, and disclosure rules.
- A Delaware-incorporated firm doing business in Texas and California generates **3 different IDs and 3 slightly different legal names**.
- At global scale, the problem compounds: each country has its own registration system, legal form abbreviations (GmbH, Ltd, LLC, Srl, Pty, SA), and data format.
- Even basic due-diligence questions ("is this company real?") require stitching across multiple jurisdictions.

### The LEI System (GLEIF)
- The Global Legal Entity Identifier (LEI) is the only truly **global, open, standardized** entity reference data source.
- As of early 2026, the GLEIF Golden Copy contains ~2M+ legal entities with parent-child relationships.
- LEI adoption is being driven by regulatory mandates: G20 transparency initiatives, KYC/AML requirements, tax authority compliance.
- **Practical impact**: The LEI reduces false positives from same-name entities across countries — critical for sanctions screening, procurement integrity, and ownership chain mapping.

### OpenCorporates Entity Resolution Playbook
- Standardize inputs: names, addresses, dates to canonical format.
- Generate candidate pairs with blocking keys (jurisdiction + registration number).
- Score similarity: deterministic rules (exact registry ID match) or fuzzy models (name, shared officers, geospatial).
- Decide & persist: high confidence -> merge; borderline -> human review.
- Iterate & govern: track provenance; entities change — re-resolve on data refresh.
- **Key partnership**: OpenCorporates now integrates LEI data to bridge jurisdictions, creating a registry-ID-anchored resolution path that avoids pure fuzzy matching.

### The Paradigm Shift: From Fuzzy to Deterministic
- Traditional entity resolution relies on **fuzzy name matching** (Levenshtein, TF-IDF, phonetic algorithms). This works until it doesn't — "ACME Corp" vs "ACME CO" vs "Acme Corporation in New York."
- The new paradigm: **registry identifiers first, fuzzy only as fallback**. When you know the exact California Secretary of State filing number AND the Delaware incorporation number AND the LEI, you don't need fuzzy matching at all — you have a ground-truth key.
- This is the Fellegi-Sunter model's holy grail: perfect deterministic agreement removes the need for probabilistic scoring.
- **Zephira** (zephira.ai) explicitly argues for this approach: "Entity Resolution Without Fuzzy Matching: How Registry Identifiers Solve the Duplicate Problem."

### Practical Challenges That Remain
- **LEI coverage gaps**: SMEs in many jurisdictions don't have LEIs. Adoption is uneven outside financial services.
- **Registry data freshness**: Some jurisdictions update annually or less. An entity may have dissolved but still appear active.
- **Transliteration**: Cyrillic, Chinese, Arabic names need romanization — introducing errors before any matching algorithm runs.
- **Shell company chains**: Multiple layers of holding companies across jurisdictions — even perfect entity resolution at each layer doesn't automatically reveal ultimate beneficial ownership without ownership data.
- **GDPR/Data Protection**: Cross-border data linking may violate privacy regulations depending on the purpose and jurisdiction.

## 3. What I Think Is Interesting

The **registry-ID-first deterministic approach** is a quiet revolution that mirrors Palantir's architectural philosophy. Palantir's Ontology resolves entities through governed, auditable pipelines rather than black-box ML matching. The LEI + OpenCorporates bridge is the open-source equivalent: build a clean, globally-keyed entity graph, then layer analytics on top.

This directly validates Jake's original Palantir thesis question. The answer isn't "better fuzzy matching" — it's **better identifiers and normalized data integration pipelines**. The same principle applies to campaign finance records (FEC committee IDs), lobbying disclosures (LD-1/LD-2 registration numbers), and government contracts (UEI/DUNS numbers). Every domain has its own identifier namespace. Cross-jurisdictional resolution is fundamentally an **identifier federation problem**, not a matching algorithm problem.

## 4. What I'd Explore Next

- **LEI coverage analysis**: Which jurisdictions have good coverage? Where are the gaps? Is there a programmatic way to identify LEI-eligible entities that don't yet have one?
- **FEC-to-LEI bridge**: Can campaign finance committee IDs be mapped to LEIs to resolve political entities across corporate registries?
- **Sanctions list entity resolution**: OFAC SDN list entries are frequently ambiguous names without identifiers. How do commercial screening tools (World-Check, LexisNexis Bridger) resolve them?
- **Practical implementation**: Build a proof-of-concept entity resolver that uses LEI + state registration numbers as primary keys and fuzzy matching only as fallback.

## 5. Cross-Domain Connections

- **Palantir Ontology Architecture**: The ontology layer's object resolution through governed pipelines is the enterprise version of registry-ID-first resolution. Same principle, different scale.
- **Exocortex Tool Schema Design**: MCP tools that accept external identifiers (LEI, registration number, committee ID) as primary keys would enable deterministic entity lookups with high confidence, improving agent reliability.
- **OSINT Investigation Methodology**: Entity resolution is the upstream prerequisite for network analysis, sanctions screening, and ownership mapping. Getting resolution right determines whether the subsequent analysis finds real connections or phantom ones.
- **Sanctions Effectiveness Analysis**: Iranian/Russian evasion networks often exploit cross-jurisdictional entity opacity. Better resolution tools = better sanctions enforcement intelligence.

---

**Key insight for memory:** Cross-jurisdictional entity resolution is fundamentally an identifier federation problem, not a fuzzy matching problem. LEI + registry IDs provide deterministic ground truth; fuzzy matching should be a fallback, not the primary strategy. This mirrors Palantir's ontology-driven object resolution and validates the Exocortex MCP tool design pattern of accepting external identifiers as primary keys.
