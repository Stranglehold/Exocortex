# Campaign Finance Entity Resolution
**Status: STABLE**
**Created: 2026-06-05 | Last Updated: 2026-06-05**
**Domain: Data Aggregation & Entity Resolution | OSINT Investigation**

## Overview

Federal campaign finance data — covering billions in political contributions, expenditures, and independent spending — represents one of the richest structured datasets for entity resolution. The Federal Election Commission (FEC) maintains comprehensive records of political committees, individual donors, candidate disbursements, and independent expenditures. When cross-referenced with corporate registries, lobbying disclosures, government contracts, and property records, campaign finance data becomes a powerful lens for identifying influence networks, beneficial ownership, and non-obvious organizational connections.

## Key Data Sources

### Federal Election Commission (FEC.gov)

| Data Type | Description | Access Method |
|-----------|-------------|---------------|
| **Committees** | Political committees (PACs, Super PACs, candidate committees, party committees) with IDs, treasurers, and filing history | [FEC API](https://api.open.fec.gov/) — RESTful with filtering, pagination |
| **Filings** | Raw FEC filings (F3, F3X, F24, F99 forms) with itemized transactions | FEC API or bulk downloads via [FEC Bulk Data](https://www.fec.gov/data/browse-data/) |
| **Individual Contributions (Schedule A)** | Itemized receipts — contributor name, address, employer, occupation, date, amount | FEC API: `/schedules/schedule_a/` |
| **Operating Expenditures (Schedule B)** | Disbursements to vendors, consultants, payroll | FEC API: `/schedules/schedule_b/` |
| **Independent Expenditures (Schedule E)** | Outside spending by Super PACs and other non-candidate committees | FEC API: `/schedules/schedule_e/` |
| **Communication Costs (Schedule F)** | Electioneering communications, coordinated spending | FEC API: `/communication_costs/` |
| **Electioneering Communications (Schedule I)** | Broadcast/cable/satellite communications mentioning candidates | FEC API: `/electioneering/` |
| **Candidate Master** | Candidate profiles, office sought, party affiliation, district | FEC API: `/candidates/` |
| **Committee Master** | Committee profiles, type (P, Q, O, U, N, I, Z, J, D), connected org, sponsor | FEC API: `/committees/` |
| **Disbursements (Schedule C)** | Loans and loan repayments | FEC API |

### Third-Party Aggregators and Enriched Data

| Source | Description | Access |
|--------|-------------|--------|
| **OpenSecrets (CRP)** | Enriched FEC data with industry codes, org IDs, revolving door tracking | [OpenSecrets API](https://www.opensecrets.org/open-data/api) — paid tiers |
| **FollowTheMoney (NIMSP)** | State-level campaign finance across 50 states | [FollowTheMoney.org](https://www.followthemoney.org/) |
| **ProPublica FEC Itemizer** | Searchable individual contributions database | [ProPublica API](https://projects.propublica.org/api-docs/campaign-finance/) |
| **FEC Itemizer** | FEC-hosted individual contribution search | [FEC Itemizer](https://www.fec.gov/data/receipts/individual-contributions/) |

## Entity Resolution Challenges in Campaign Finance Data

### 1. Committee Name Variation
- Committees use both full names and acronyms (e.g., "National Rifle Association Political Victory Fund" vs "NRA PVF")
- Joint fundraising committees (JFCs) create intermediary entities that disburse to sub-committees
- Affiliated committees share naming patterns but separate FEC IDs (e.g., leadership PACs, campaign committees)
- **Resolution approach**: Committee ID (CXXXXXXXX) is the primary key; name normalization via alias tables and fuzzy matching for cross-committee linkage

### 2. Individual Contributor Name Variation
- Same donor appears as "Robert Smith", "Bob Smith", "Robert J. Smith" across filings
- Employer/occupation variations: "Google Inc" vs "Google LLC" vs "Alphabet Inc"
- Address changes over time (moves, ZIP+4 variations)
- **Resolution approach**: Multi-field blocking (ZIP5 + last name), Fellegi-Sunter probabilistic matching on name, employer, occupation, and address fields

### 3. Organization Disambiguation
- Connected organizations: Corporation X and its PAC may share a primary address but different FEC IDs
- Vendor names: Consulting firms billing through multiple LLCs
- **Resolution approach**: Committee-to-organization linkage tables (OpenSecrets CRPFiler IDs), employer name normalization to canonical organization identifiers

### 4. Cross-Cycle Entity Persistence
- Committees dissolve and re-form with new IDs across election cycles
- Super PACs rebrand (e.g., "Priorities USA Action" → "Priorities USA" → "Priorities USA 2024")
- **Resolution approach**: Temporal entity resolution with committee succession tracking

## Entity Resolution Methods

### 1. Deterministic Matching via FEC Committee ID
- FEC-assigned Committee ID (CXXXXXXXX) provides a unique, stable identifier
- Committee Master data includes sponsor candidate ID, connected organization, and committee type taxonomy
- Committee type codes: P (Presidential), S (Senate), H (House), Q (PAC with non-contribution account), O (Super PAC / Independent Expenditure-Only), U (Single candidate), N (Non-party non-qualified), I (Inaugural), Z (National party non-federal), J (Joint fundraising), D (Leadership PAC)

### 2. Probabilistic Matching — Fellegi-Sunter Model
- Core framework: compare fields (name, employer, occupation, ZIP5) with agreement/mismatch probabilities
- M-probability: probability that matching records agree on field X (representing true positive match rate — high for exact employer strings from same company HR system)
- U-probability: probability that non-matching records agree on field X by random chance (function of field cardinality — low for full address, moderate for common employer names)
- **EM algorithm** for parameter estimation when training data unavailable
- Splink: Fast, scalable Python implementation with Fellegi-Sunter, expectation-maximization, Bayesian comparison levels, term frequency adjustments for common names, and interactive model diagnostics

### 3. Blocking Strategies
- Blocking key design is critical for scaling: FEC individual contributions exceed 100M+ records per cycle
- **Blocking schemes**:
  - ZIP5 + last name (high precision, moderate recall — 85-90% pair completeness on residential donors)
  - Employer + occupation (for organization-linked donors — captures donors who moved but kept same job)
  - State + first initial + last name (higher recall, lower precision — 95%+ pair completeness at cost of 3x comparisons)
  - ZIP3 + Soundex last name (phonetic variation handling for name misspellings and OCR errors)
- **Adjudication pattern**: Run multiple blocking passes with different keys, union the candidate pairs, deduplicate before scoring

### 4. Splink-Specific Implementation
Splink is the recommended Python package for campaign finance entity resolution workflows. Key capabilities:
- SplinkDataFrame abstraction for both in-memory (DuckDB) and out-of-core (Spark) backends
- Deterministic rules as hard constraints ("if SSN matches, it's a match")
- Clustering algorithms: connected components with edge thresholds
- Interactive model diagnostics: m/u probability charts, match weight histograms, prediction viewer
- Term frequency adjustments down-weight common values (e.g., "John Smith" employer "United States Government")
- **Pipeline**: preprocess → blocking → comparison (levenshtein/jaro-winkler/exact) → EM training → scoring → clustering

### 5. LLM-Assisted Entity Resolution
- Zero-shot matching: Prompt LLM with "Are these two records the same person?"
- Few-shot: Provide 3-5 labeled examples per comparison
- Batch inference: Process multiple pairs in single prompt for throughput
- **State of practice**: Effective for difficult edge cases (nicknames, international names, typos) but expensive at scale
- **Hybrid approach**: Deterministic blocking + Probabilistic scoring for bulk; LLM adjudication for borderline cases (match weight 0.3-0.7)

## Integration with Other Entity Resolution Datasets

### 1. Campaign Finance ↔ Lobbying Disclosure (LDA)
- OpenSecrets maintains FEC Committee ID ↔ Lobbying Registrant ID crosswalk
- Shared patterns: corporate PAC officers often appear as lobbyists; same law firms appear as both PAC treasurers and lobbying firms
- Revolving door tracking: OpenSecrets matches former congressional staffers (from LegiStorm/House disbursement data) to lobbying registrations and campaign contributions
- **Fellegi-Sunter pipeline**: Block on ZIP5 + organization name, score on name + title, cluster connected components

### 2. Campaign Finance ↔ Government Contracts (USASpending.gov)
- UEI (Unique Entity Identifier) to FEC Committee ID linkage via corporate parent name normalization
- Pattern: Defense contractors with PACs → contract award patterns show correlation with contribution timing
- OpenSecrets "Money in Politics" data integrates contract award data with campaign contributions
- **Pipeline**: Normalize company names → TF-IDF cosine matching → manual review for borderline cases

### 3. Campaign Finance ↔ Corporate Registries
- PAC registration requires treasurer and custodian of records — these individuals appear in state business filings
- Connected organization field in FEC committee master links to corporate entity
- **Pattern**: Secretary of State business name → FEC employer normalization → contribution pattern analysis

### 4. Campaign Finance ↔ Property Records
- Individual contributor address → county assessor ownership verification
- **Pattern**: LLC contributions traced through property ownership to beneficial owners
- Address as blocking key: ZIP5 + street number for high-precision blocking

## Key Investigation Patterns

### Pattern 1: Straw Donor Detection
- Multiple contributions from same address with different names
- Same employer + same contribution amount + same date = red flag
- FEC enforcement priority: conduit contributions (straw donors) are illegal under 52 U.S.C. § 30122

### Pattern 2: Dark Money → Super PAC Flow
- 501(c)(4) "social welfare" organizations → Super PAC independent expenditures
- Names don't match, but vendor relationships and address clusters reveal connections
- **Method**: Schedule B (disbursements) entity resolution across committees — shared vendors signal coordination

### Pattern 3: Corporate Influence Network Reconstruction
- Committee Master connected organization → parent company
- Employer field normalization across individual contributions → employee contribution concentration
- Cross-reference with lobbying disclosure → unified influence profile per organization

### Pattern 4: Geographic Contribution Pattern Analysis
- ZIP code aggregation of contributions → "donor communities"
- Cross-reference with property records → wealth concentration mapping
- **Cross-domain**: ZIP-level contribution data + Census ACS data → demographic contribution patterns

## Open-Source Tools for Campaign Finance Entity Resolution

| Tool | Capability | Notes |
|------|-----------|--------|
| **Splink** | Probabilistic record linkage (Fellegi-Sunter) | DuckDB backend for 100M+ records; EM training; Bayesian comparison levels |
| **dedupe** | Active learning-based deduplication | Training interface for manual labeling; good for custom matching rules |
| **Python Record Linkage Toolkit** | Comprehensive record linkage library | Blocking, comparing, classification; pandas-native |
| **Zingg** | ML-based entity resolution | Training data generation; handles multiple languages |
| **OpenFEC Python SDK** | FEC API client library | Streamlined FEC data access: `pip install openfec` |
| **fecfile** | FEC electronic filing parsing | Python library for parsing .fec files |

## Cross-Domain Connections

1. **Entity Resolution Stack Integration**: Campaign finance is the fifth pillar of the OSINT entity resolution pentagon: corporate registries → lobbying disclosure → government contracts → property records → campaign finance. Each dataset has unique blocking keys and comparison vectors, but the Fellegi-Sunter probabilistic framework generalizes across all five.

2. **Intelligence Failure Analysis**: Straw donor detection patterns structurally mirror intelligence source reliability assessment (Admiralty Code). Just as HUMINT sources must be cross-validated, campaign contribution patterns must be verified against employer, address, and historical giving patterns to avoid false-positive "conduit" flags.

3. **Counterintelligence Analysis Frameworks**: CI-ACH (Analysis of Competing Hypotheses) is directly applicable to campaign finance entity resolution — when multiple donor aliases map to a single beneficial owner, competing identity hypotheses must be evaluated against evidence (address matches, employer consistency, contribution timing patterns).

4. **Knowledge Graph Construction**: Campaign finance data naturally forms a bipartite graph: donors ↔ committees. Committee-to-organization and organization-to-lobbying edges create a multi-modal knowledge graph amenable to centrality analysis, community detection, and influence flow tracing.

5. **Network Analysis Techniques for OSINT**: Committee-to-donor networks exhibit power-law degree distributions (few mega-donors, many small contributors). Betweenness centrality identifies donor "brokers" who connect otherwise separate political networks. Temporal network analysis reveals contribution coordination patterns (bundling).

6. **Structured Analytic Techniques (SAT)**: Key Assumptions Check applicable to entity resolution: "Assuming that 'Robert J. Smith' at 123 Main St. and 'Bob Smith' at 123 Main St. are the same person" — explicit assumption documentation prevents false merges in probabilistic matching.

7. **Bridging Local-to-Frontier Model Performance**: LLM-assisted entity resolution for campaign finance is a prime candidate for local model deployment: FEC data is public, non-PII, and amenable to batch processing. A fine-tuned local model (Qwen3.6-27B) on labeled FEC match pairs could achieve near-frontier performance at negligible cost for high-volume schedule A matching.

8. **Economic Espionage / Counterintelligence**: Campaign finance data can reveal foreign influence operations through: pattern-of-life contribution analysis (timing aligned with foreign policy debates), employer tracing to state-owned enterprises, and joint fundraising committee participation networks.

9. **Embedding-Based Probabilistic Record Linkage**: The Political Analysis paper (Ornstein et al., 2022) demonstrates that pretrained transformer embeddings (GPT-3, GPT-4) outperform traditional string metrics (Jaro-Winkler, Levenshtein) for name matching in political science applications — directly applicable to FEC donor name resolution where traditional fuzzy matching fails on nicknames, international names, and OCR artifacts.

## References

1. FEC.gov — Federal Election Commission data and API documentation. https://www.fec.gov/data/
2. Fellegi, I.P. & Sunter, A.B. (1969). "A Theory for Record Linkage." *Journal of the American Statistical Association*, 64(328), 1183-1210.
3. Splink — Fast, accurate and scalable probabilistic data linkage. https://github.com/moj-analytical-services/splink
4. OpenSecrets (Center for Responsive Politics). Campaign finance and lobbying data integration. https://www.opensecrets.org/open-data
5. AI Analytics. "Tracking PAC money through FEC data: entity resolution across 50 filing jurisdictions." https://www.ai-analytics.org/writing/election-finance-entity-resolution/
6. Christen, P. (2012). *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection*. Springer.
7. Binette, O. & Steorts, R.C. (2022). "(Almost) all of entity resolution." *Science Advances*, 8(50). https://pmc.ncbi.nlm.nih.gov/articles/PMC11636688/
8. ProPublica Campaign Finance API. https://projects.propublica.org/api-docs/campaign-finance/
9. FollowTheMoney.org — National Institute on Money in State Politics. State-level campaign finance data. https://www.followthemoney.org/
10. dedupe — Python library for accurate and scalable fuzzy matching, record deduplication, and entity resolution. https://github.com/dedupeio/dedupe
11. OpenFEC Python SDK. https://github.com/18F/openFEC
12. Winkler, W.E. (2006). "Overview of Record Linkage and Current Research Directions." U.S. Census Bureau Statistical Research Division.

13. Ornstein, J.T. et al. (2022). "Probabilistic Record Linkage Using Pretrained Text Embeddings." *Political Analysis*, Cambridge University Press. https://www.cambridge.org/core/journals/political-analysis/article/0414DDE200A0305EEDD7B31EA8849EB9
14. Binette, O. & Steorts, R.C. "(Almost) All of Entity Resolution." arXiv:2008.04443v3 [stat.ME]. https://arxiv.org/abs/2008.04443
15. Wu, Y. et al. (2026). "EnsembleLink: Accurate Record Linkage Without Training Data." arXiv:2601.21138. https://arxiv.org/abs/2601.21138
16. UK Ministry of Justice. "Splink: Algorithmic Transparency Record." https://www.gov.uk/algorithmic-transparency-records/moj-splink-master-record
17. Data in Government Blog (2022). "Splink: Fast, accurate and scalable record linkage." https://dataingovernment.blog.gov.uk/2022/09/23/splink-fast-accurate-and-scalable-record-linkage/
