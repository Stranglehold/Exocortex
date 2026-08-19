# Cross-Jurisdictional Entity Resolution

**Status: STABLE**
**Created: 2026-06-06**
**Topic Source: interests.md — Data Aggregation & Entity Resolution**
**Exploration Question: "Cross-jurisdictional data linking challenges (different naming conventions, ID formats, filing standards)"**

## Overview

Cross-jurisdictional entity resolution (ER) addresses the challenge of linking records about the same real-world entity — a company, individual, vessel, or asset — when those records originate from different legal jurisdictions. Each jurisdiction has its own naming conventions, identifier formats, filing standards, language, data quality, and access restrictions. The core tension: ER algorithms assume consistent field formats and comparable signal quality, but cross-jurisdictional data violates nearly every assumption.

This page builds on the May 29, 2026 EXPLORE field report (cross-jurisdictional-entity-resolution.md) which identified FinCEN's March 2025 CTA rollback as a structural regression in US beneficial ownership transparency and the opportunities created by open-source ER tooling (Splink, Zingg, dedupe).

---

## 1. Foundational Challenge: Field Assumptions Violated

The Fellegi-Sunter (1969) probabilistic record linkage model — the mathematical foundation of modern ER — was designed for census record linkage where:
- Fields have consistent formats (standardized names, addresses)
- m-probabilities (probability field matches given true match) are stable across the dataset
- u-probabilities (probability field matches by chance) follow known distributions
- Base rate of true matches is estimable

Cross-jurisdictional ER violates all of these:

| Assumption | Cross-Jurisdictional Violation |
|-----------|-------------------------------|
| Consistent field formats | Legal name formats vary dramatically: "ACME Corp" vs "Acme Corporation Ltd" vs "ACME CORPORATION (HOLDINGS) LIMITED" vs local-language equivalents |
| Stable m-probabilities | m-probabilities vary by jurisdiction — name matching is far more reliable in the UK (consistent naming) than in China (transliteration variation + local subsidiary naming) |
| Known u-probabilities | The probability of random name collision depends on jurisdiction-specific name distributions — "ABC Holdings" is common in the BVI but rare in Germany |
| Estimable base rate | Cross-jurisdictional matching base rates span orders of magnitude depending on industry and region |

---

## 2. The Five Core Challenge Dimensions

### 2.1 Naming Conventions

**Legal entity name variation:** The same entity may appear as:
- Local name: "中国石油天然气集团公司"
- English transliteration: "China National Petroleum Corporation"
- Abbreviated: "CNPC"
- Holding company variant: "CNPC International Ltd" (BVI subsidiary)
- Trading name: "PetroChina" (listed subsidiary, different legal entity)

**Name suffix fragmentation:** Jurisdictions use different legal-form indicators:
- UK: Ltd, PLC, LLP, CIC
- US: Inc, Corp, LLC, LP, PLLC
- Germany: GmbH, AG, GmbH & Co. KG, UG
- Netherlands: BV, NV, CV, VOF
- BVI/OFCs: IBC, Ltd, Inc, Corp (often deliberately ambiguous)

**Transliteration variance:** Arabic, Chinese, Cyrillic, and other non-Latin names have multiple valid transliterations. "محمد" → Mohammed, Mohammad, Muhammed, Mohamed, etc. Entity resolution across Latin-script registries and Arabic beneficial ownership records compounds this problem.

### 2.2 Identifier Format Fragmentation

No universal entity identifier exists across all jurisdictions. The landscape:

| Identifier | Scope | Format | Strengths | Limitations |
|-----------|-------|--------|-----------|-------------|
| **LEI** (Legal Entity Identifier) | Global (~2.5M entities, 2026) | 20-char alphanumeric (ISO 17442) | Standardized, publicly searchable via GLEIF | Limited adoption by SMEs; not required outside financial sector |
| **DUNS** | Global (~500M records) | 9-digit numeric | Extensive coverage, historical depth | Proprietary (Dun & Bradstreet); not free/open |
| **EIN/TIN** | US only | 9-digit numeric (XX-XXXXXXX) | Authoritative for US entities | Single jurisdiction; not public for individuals |
| **Companies House Number** | UK only | 8-character alphanumeric | Open, free, structured API | UK-only |
| **UEI** (Unique Entity ID) | US federal contracting | 12-character alphanumeric | Required for US federal awards | Limited to entities doing business with USG |
| **OpenCorporates ID** | Cross-jurisdictional (147 jurisdictions) | URL-based | Aggregates multiple registries; open data | Coverage varies; dependent on underlying registry quality |
| **State SoS Filing Number** | US state-level | Varies by state | Official state record | No cross-state unification; formats differ even within US |

**The identifier resolution problem:** When two records from different jurisdictions lack a shared identifier, ER must rely on probabilistic matching across name, address, and date fields — pushing the problem back into naming conventions and filing standard variance.

### 2.3 Filing Standards Variance

**Timing and frequency:**
- UK Companies House: Annual confirmation statement + annual accounts (within 9 months)
- US Secretary of State: Annual/biennial report (varies by state); Delaware annual franchise tax payment (no detailed filing required)
- BVI: Annual return (minimal disclosure); no public accounts filing
- China: Annual report to SAMR (often delayed, quality variable)

**Disclosure depth:**
- UK: Directors, persons with significant control (PSC), shareholders, annual accounts
- Delaware: Registered agent, incorporation date, status — nothing else public
- Cayman Islands: Name, registration number, registered office, status — no director/shareholder disclosure
- EU (AMLD6): Central beneficial ownership registries (implementation quality varies significantly)

**Data quality:** Registry data is self-reported with minimal verification. Companies House estimates 10-15% of PSC data is inaccurate; BVI and Cayman registries do not verify beneficial ownership claims. Cross-jurisdictional ER pipelines must incorporate data quality metadata as a first-class input, not an afterthought.

### 2.4 Language Barriers

- **Multi-script matching:** The same entity may appear in Arabic script in UAE corporate registry, Latin script in UK, and Chinese characters in Hong Kong
- **Transliteration schemes:** No single standard; Arabic has at least 6 common Romanization schemes in active use
- **Semantic equivalence:** "Société Anonyme" (French) = "Naamloze Vennootschap" (Dutch) = "Aktiengesellschaft" (German) = "Public Limited Company" (English) — all describe the same legal form but share zero lexical overlap
- **LLM-assisted cross-lingual ER:** Emerging approach using LLMs for semantic matching of entity names across languages, particularly for non-Latin scripts where string-distance metrics fail entirely

### 2.5 Access and Transparency Asymmetry

The most fundamental challenge: different jurisdictions have fundamentally different transparency regimes, creating systematic blind spots in cross-jurisdictional ER pipelines.

**FinCEN CTA Rollback (March 21, 2025):** The Interim Final Rule eliminated BOI reporting for US companies and US persons. US-linked entities can now be nested behind Delaware LLCs or Wyoming holding companies with zero public ownership trail, while their European subsidiaries face increasing transparency under EU AMLD6 and UK Economic Crime Act requirements. This creates an asymmetric intelligence environment where the US is the preferred jurisdiction for opacity.

**Transparency index (qualitative, 2026):**
| Jurisdiction | BOI Public | Machine-Readable | Structured API | Free |
|-------------|-----------|-----------------|---------------|------|
| UK (Companies House) | Yes (PSC register) | Yes | Yes (REST/streaming) | Yes |
| EU (AMLD6) | Yes (varies by member state) | Partial | Partial | Varies |
| US (Federal) | No (post-CTA rollback) | N/A | N/A | N/A |
| US (Delaware) | No | No | No | Partial |
| BVI | No | No | No | No |
| Cayman Islands | No | No | No | No |
| Singapore (ACRA) | Partial | Yes | Yes | Paid |
| Hong Kong (CR) | Yes (directors) | Yes | Yes | Paid |

---

## 3. Technical Approaches

### 3.1 Fellegi-Sunter Model Adaptations

Modern implementations extend the classic model for cross-jurisdictional challenges:

- **Splink (UK Ministry of Justice):** Bayesian blocking with jurisdiction-specific comparison levels. Handles the m/u probability variance across jurisdictions by allowing jurisdiction as a blocking key, computing per-block m/u estimates. DuckDB backend enables laptop-scale ER on datasets up to ~50M records.
- **Zingg:** Trainable matching with active learning — a human labels a small set of pairwise comparisons per jurisdiction pair, and the model learns jurisdiction-specific matching rules.
- **dedupe:** Active learning with UI for labeling uncertain pairs; can incorporate jurisdiction as a feature to adjust comparison thresholds.

### 3.2 LLM-Assisted Entity Resolution

For the fuzzy matching step where traditional string distance metrics fail:

- **Zero-shot name matching:** LLMs can assess whether "中国石油天然气集团公司" and "China National Petroleum Corporation" refer to the same entity, using semantic understanding rather than string comparison
- **Cross-language address normalization:** LLMs can parse and normalize addresses across jurisdictions: "123 Main St, Suite 400, New York, NY 10001" ↔ "Level 4, 123 Main Street, Manhattan, New York City"
- **Legal form translation:** LLMs can recognize that "Société à Responsabilité Limitée" = "Limited Liability Company" = "GmbH"
- **Production considerations:** LLM-based matching is 10-100x more expensive per comparison than Splink; use blocking to reduce candidate pairs, reserving LLM matching for borderline cases where Splink confidence is below threshold

### 3.3 ICIJ Graph Construction Methodology

The International Consortium of Investigative Journalists (ICIJ) pioneered cross-jurisdictional entity resolution at scale for the Panama Papers, Paradise Papers, and Pandora Papers investigations. Key patterns:

- **Multi-signal fusion:** Name, address, intermediary (law firm/agent), date of incorporation, shareholders, directors — no single signal is authoritative; matches emerge from signal convergence
- **Address co-occurrence:** Entities sharing the same registered address (particularly in BVI/Cayman/Panama where thousands of companies use the same law firm address) are probabilistically linked via intermediary clustering
- **Intermediary clustering:** The law firm or corporate service provider is often the strongest signal — shell companies using the same Mossack Fonseca intermediary are more likely linked than companies sharing similar names
- **Neo4j graph patterns:** Entity resolution produces candidate nodes; graph queries (shared address, shared director, shared intermediary, temporal proximity of incorporation) surface hidden beneficial ownership connections

---

## 4. Open-Source Production Tooling

Three mature open-source tools are production-ready for cross-jurisdictional ER (2026):

| Tool | Language | Backend | Key Strength | Limitation |
|------|----------|---------|-------------|-----------|
| **Splink** | Python | DuckDB/Spark | Bayesian probabilistic matching; handles 50M+ records on laptop | Requires statistical literacy; complex blocking rules |
| **Zingg** | Java/Python | Spark | Active learning for matching rules; handles non-Latin scripts well | Spark dependency; heavier operational footprint |
| **dedupe** | Python | SQLite/PostgreSQL | Active learning with labeling UI; good for small/medium datasets | Does not scale beyond ~1M records well; single-machine |

Splink's DuckDB backend is particularly notable: cross-jurisdictional ER on datasets up to ~50M records now runs on a consumer laptop. The bottleneck is data access, not computation.

---

## 5. The Sanctions Evasion Connection

Cross-jurisdictional entity resolution directly addresses sanctions evasion detection:

- **Shadow fleet pattern:** Iranian oil shipment vessels (~430 vessels) use multi-jurisdictional shell companies — Panama-flagged, UAE-owned, Chinese-insured — to evade detection. Entity resolution across Panamanian, Emirati, and Chinese registries can surface hidden beneficial ownership chains.
- **US Treasury network-based sanctions:** OFAC's network-based designation approach is essentially entity resolution at industrial scale, using graph analytics to surface hidden ownership connections across opaque jurisdictions.
- **Open-source parity:** Splink-level tooling makes ICIJ-level investigative capability accessible to individual researchers; the bottleneck is registry access, not computational capacity.

---

## 6. Cross-Domain Connections

1. **Sanctions Evasion (Iranian shadow fleet):** Multi-jurisdictional shell company networks are the investigative target; cross-jurisdictional ER is the countermeasure (see maritime-logistics-gray-zone, iranian-sanctions-evasion-escalation)
2. **OSINT Investigation Methodology:** Cross-jurisdictional ER is the technical substrate for ICIJ-style document-based investigation and Bellingcat-style visual investigation
3. **Knowledge Graph Construction:** ER produces the nodes; knowledge graph construction determines how they connect — a two-step pipeline where ER errors cascade through graph analysis (see knowledge-graph-construction)
4. **LLM-Assisted Entity Resolution:** LLMs handle the fuzzy matching step where string metrics fail — cross-language name matching is the killer application (see llm-assisted-entity-resolution)
5. **Privacy & Cryptography:** Zero-knowledge proofs could enable ER without exposing underlying PII — useful for cross-jurisdictional data sharing where privacy laws constrain data pooling (see homomorphic-encryption-state-of-art)
6. **AI Agent Architecture:** An agent equipped with Splink + corporate registry APIs could autonomously surface hidden beneficial ownership connections — a concrete use case for agentic OSINT (see multi-agent-orchestration-patterns)
7. **Government Contracts ER:** Federal contracting data often involves foreign subsidiaries; cross-jurisdictional ER connects USASpending.gov to foreign corporate registries (see government-contracts-entity-resolution)
8. **Campaign Finance ER:** Foreign-linked dark money flows through US-registered entities; cross-jurisdictional ER traces the connection to foreign principals (see campaign-finance-entity-resolution)
9. **Bridging Local-to-Frontier Models:** DeepSeek-R1-Distill-Qwen-14B achieving 98.23% F1 on OpenSanctions Pairs is a concrete validation of local models approaching frontier performance for entity resolution — a working case study for the bridging-local-to-frontier-model-performance thesis (see bridging-local-to-frontier-model-performance)
10. **LLM-Assisted Entity Resolution:** The OpenSanctions benchmark provides empirical validation for LLM-based ER approaches previously discussed theoretically in the May 2026 field report (see llm-assisted-entity-resolution)

---


## 7. LLM-Based Entity Matching for Cross-Jurisdictional ER

LLMs have emerged as a breakthrough for the cross-lingual, cross-script matching problem that traditional string-metric approaches fail on. The benchmark landscape in 2026 shows pairwise matching approaching a practical ceiling.

### OpenSanctions Pairs Benchmark (Smith et al., 2026)

The OpenSanctions Pairs dataset (arXiv:2603.11051, February 2026) is the largest cross-jurisdictional entity matching benchmark available: **755,540 labeled pairs** from 293 heterogeneous sources across 31 countries, with multilingual/cross-script names, noisy attributes, and set-valued fields typical of sanctions compliance workflows.

| System | F1 Score | Notes |
|--------|----------|-------|
| nomenklatura RegressionV1 (rule-based) | 91.33% | Production baseline used by OpenSanctions |
| DeepSeek-R1-Distill-Qwen-14B (local) | 98.23% | Open model, locally deployable |
| GPT-4o (cloud, zero-shot) | 98.95% | Current SOTA on this benchmark |

Key findings:
- **Pairwise matching approaching ceiling:** 98.95% F1 leaves minimal room for improvement on direct comparison
- **Complementary failure modes:** rule-based systems over-match (high false positives); LLMs primarily fail on cross-script transliteration and minor identifier/date inconsistencies
- **In-context examples provide marginal benefit:** DSPy MIPROv2 prompt optimization yields consistent but modest gains; adding examples can degrade performance
- **Shift to pipeline components:** Authors recommend reallocating effort toward blocking, clustering, and uncertainty-aware review rather than further pairwise optimization

### Structure-Guided and In-Context Clustering Approaches

Recent ACL 2026 and SIGMOD 2026 papers address the pipeline-level challenge:

- **Structure-Guided ER (ACL 2026 Industry Track):** Fine-tuning LLMs for robust name matching using structural context (entity attributes, relationships) rather than isolated pairwise comparison, improving performance in complex linguistic contexts with non-Latin scripts
- **In-Context Clustering-Based ER (SIGMOD/PACMMOD 2026):** A design space exploration showing that LLM-based clustering — grouping records into entity clusters in a single pass — outperforms iterative pairwise matching for heterogeneous datasets, reducing the blocking dependency
- **OpenSanctions Pairs open-source codebase:** Released at github.com/chansmi/OSINT_entity_resolution, providing a reproducible benchmark for cross-jurisdictional ER research

### Implications for OSINT and Compliance

The practical ceiling on pairwise matching (~99% F1) means the OSINT investigator's bottleneck is no longer computational — it's **data access**. An investigator with Splink + a locally-deployed DeepSeek-R1-Distill-Qwen-14B can achieve ICIJ-level entity resolution quality on a consumer laptop, provided they can obtain the underlying registry data.


## 8. 2025-2026 Regulatory and Data Access Landscape

### FinCEN CTA Rollback (March 2025)

The US Corporate Transparency Act (CTA), which mandated beneficial ownership reporting to FinCEN for US-registered entities, was effectively rolled back via FinCEN's March 21, 2025 Interim Final Rule. This reverses the most significant US beneficial ownership transparency gain in decades and creates a structural data access asymmetry: investigators can access UK PSC registers and EU AMLD6-mandated registries but cannot obtain equivalent US data.

### UK Economic Crime and Corporate Transparency Act (ECCTA 2023, fully in force 2025-2026)

ECCTA 2023 strengthens the UK Persons with Significant Control (PSC) framework:
- Mandatory identity verification for company directors and PSCs
- Companies House empowered to query, reject, and remove suspicious filings
- Expanded PSC disclosure requirements closing nominee shareholder loopholes

This creates an investigative asymmetry: UK entity ownership data is now among the most transparent globally, enabling cross-jurisdictional matching from opaque jurisdictions (Delaware, BVI, Panama) to UK-registered entities.

### EU AMLD6 (2024, implementation 2025-2027)

The Sixth Anti-Money Laundering Directive expands beneficial ownership registers to all EU member states with centralized, publicly accessible platforms. Combined with GLEIF's LEI system (2.3M+ active LEIs as of Q2 2026), the EU regulatory landscape enables systematic cross-jurisdictional matching between EU-registered entities and global corporate registries.

### Registry Access as the Binding Constraint

The computational capacity for cross-jurisdictional ER at ICIJ scale now runs on a laptop. The binding constraint is **registry access**:
- **Open registries:** UK PSC, EU AMLD6, GLEIF LEI (free, structured, API-accessible)
- **Semi-open:** US state-level registries (paywalled, inconsistent formats, no API for most)
- **Opaque:** BVI, Panama, UAE, and other secrecy jurisdictions (no public beneficial ownership data)

The gap between what is computationally possible and what is legally accessible defines the frontier of OSINT entity resolution.

## 9. Open Questions

1. ~~Can LLM-based matching achieve production-adequate precision/recall for cross-language entity matching?~~ **ANSWERED (2026):** Yes. OpenSanctions Pairs benchmark shows 98.95% F1 with GPT-4o, 98.23% with locally-deployed DeepSeek-R1-Distill-Qwen-14B. Pairwise matching at production ceiling; remaining challenges are in blocking/clustering pipeline.
2. What is the minimum viable signal set for reliable cross-jurisdictional matching when one jurisdiction is opaque (e.g., Delaware LLC matched against UK PSC register)?
3. How can zero-knowledge proofs enable privacy-preserving cross-jurisdictional entity resolution?
4. What would a jurisdiction-specific u-probability reference table look like for the top 20 financial secrecy jurisdictions?
5. How can LLM-based clustering (rather than pairwise matching) improve recall for cross-script entity resolution where transliteration introduces noise?

---

## 8. References

1. Fellegi, I.P. and Sunter, A.B. (1969). "A Theory for Record Linkage." *Journal of the American Statistical Association*, 64(328), 1183-1210.
2. FinCEN. "Interim Final Rule: Beneficial Ownership Information Reporting Requirements." March 21, 2025. Federal Register.
3. UK Ministry of Justice. "Splink: Probabilistic Record Linkage at Scale." GitHub, 2026. https://github.com/moj-analytical-services/splink
4. GLEIF. "Global LEI System: LEI Data." https://www.gleif.org/en/lei-data
5. OpenCorporates. "Entity Resolution Pipeline for Data Aggregators." June 2025.
6. ICIJ. "Pandora Papers: Investigation Methodology." 2021. https://www.icij.org/investigations/pandora-papers/
7. OFAC. "Sanctions Compliance Guidance: Network-Based Designations." US Treasury, 2024-2026.
8. European Commission. "AMLD6: Sixth Anti-Money Laundering Directive." 2024.
9. Companies House. "Persons with Significant Control (PSC) Register." 2016-2026. https://www.gov.uk/government/collections/people-with-significant-control
10. Zingg. "Entity Resolution for All." https://github.com/zinggAI/zingg
11. dedupe. "Data Matching and Entity Resolution." https://github.com/dedupeio/dedupe

12. Smith, C., Sesodia, M., Lindenberg, F., and Schroeder de Witt, C. (2026). "OpenSanctions Pairs: Large-Scale Entity Matching with LLMs." arXiv:2603.11051. https://arxiv.org/abs/2603.11051
13. ACL 2026 Industry Track. "Structure-Guided Entity Resolution: Fine-Tuning LLMs for Robust Name Matching in Complex Linguistic Contexts." https://aclanthology.org/2026.acl-industry.101/
14. ACM SIGMOD/PACMMOD 2026. "In-context Clustering-based Entity Resolution with Large Language Models: A Design Space Exploration." https://dl.acm.org/doi/10.1145/3749170
15. Shu et al. (2024). "LawLLM: Law in Large Language Models." LoRA-based instruction tuning on Gemma-7B for cross-jurisdictional reasoning.
16. UK Companies House. "Economic Crime and Corporate Transparency Act 2023: Implementation." https://www.gov.uk/government/collections/economic-crime-and-corporate-transparency-act-2023
17. FinCEN. "Beneficial Ownership Information Reporting Requirements: Interim Final Rule." March 21, 2025. 90 FR 13486.
18. European Commission. "AMLD6 Implementation: Centralized Beneficial Ownership Registers." 2025-2027.
19. SMBench (Astappiev et al., 2026). "No-code benchmarking of learning-based entity matching." Information Systems, 139:102711.

---

*Page deepened 2026-07-05: Added LLM-Based Entity Matching section (OpenSanctions Pairs benchmark, GPT-4o 98.95% F1, DeepSeek-R1-Distill-Qwen-14B 98.23% F1), 2025-2026 Regulatory Landscape (FinCEN CTA rollback, UK ECCTA, EU AMLD6), updated cross-domain connections to bridging-local-to-frontier and LLM-assisted-ER. Answered Open Question #1 on LLM adequacy for cross-lingual matching. Promoted to STABLE.*
