# Financial Intelligence (FININT) for Entity Resolution

**Status: STABLE**
**Created: 2026-06-08 | Last Updated: 2026-06-08**
**Domain: Data Aggregation & Entity Resolution | OSINT Investigation**
**Line Count: ~185 lines**

## Overview

Financial intelligence (FININT) refers to the collection, analysis, and dissemination of financial transaction data to identify illicit activity, track fund flows, and reconstruct entity networks. As an entity resolution (ER) data source, FININT provides uniquely deterministic linkage signals — bank account numbers, SWIFT/BIC codes, tax identifiers, and beneficial ownership records — that complement the probabilistic signals from corporate registries, campaign finance, and social media analysis.

## Data Sources Taxonomy

### Primary Regulatory Data

| Source | Jurisdiction | Volume | Key ER Fields |
|--------|-------------|--------|---------------|
| **FinCEN SARs** (Suspicious Activity Reports) | US | 4M+/year | Names, addresses, phones, account numbers, IDs, narrative text |
| **FinCEN CTRs** (Currency Transaction Reports) | US | 21M+/year | Names, addresses, SSN/EIN, account numbers, transaction amounts |
| **FinCEN CMIRs** (CMIR/Form 105) | US | Lower volume | Cross-border instrument data, courier identification |
| **FinCEN FBARs** (Foreign Bank Account Reports) | US | ~1.5M/year | Foreign account numbers, foreign institution names |
| **BSA E-Filing System** | US | Multi-million | Consolidated BSA data accessible via FinCEN Query (FCQ) |
| **BOI Registry** (Beneficial Ownership Information) | US | ~35M filings anticipated | Beneficial owners, company applicants, entity identifiers |

Bulk BSA data is accessible to authorized agencies via the FinCEN Query system (FCQ). IRS Criminal Investigation conducted nearly 2 million FCQ queries in FY23; over 87% of all IRS-CI investigations involve a BSA filing related to the primary subject (Quantexa 2025).

### International Payment Networks

| Network | Type | Data Content | ER Relevance |
|---------|------|-------------|-------------|
| **SWIFT** | Messaging | MT103/MT202 messages, sender/receiver BIC, intermediary banks, purpose codes | Corporate counterparty resolution, sanctions screening |
| **CHIPS** | Clearing | USD high-value clearing, US correspondent bank identification | US nexus determination for foreign entities |
| **Fedwire** | Settlement | USD real-time gross settlement, ABA routing numbers | US bank relationship mapping |
| **CIPS** | Clearing | China cross-border RMB payments (alternative to SWIFT) | Entity obfuscation detection, parallel system analysis |
| **SPFS** | Messaging | Russian financial messaging system | Sanctions evasion detection |

### Investigative Datasets

- **ICIJ FinCEN Files** (2020): 2,657 leaked SARs covering $2 trillion in transactions (1999-2017), exposing global correspondent banking flows and enabling public interest entity resolution at scale
- **Panama Papers / Pandora Papers / Paradise Papers**: Offshore entity registries with director/shareholder data, bank account linkages
- **OCCRP Aleph**: Integrated investigative data platform with cross-referenced financial, corporate, and sanctions data

## Entity Resolution Methodology

### FinCEN-Specific ER Challenges

Entity resolution across BSA filings faces distinctive challenges beyond standard ER (Quantexa 2025; Westphal 2025):

1. **Name Variation**: Same subject appears as "John Smith" (SAR), "Jonathan Smith" (CTR), "Jon Smith" (CMIR) — requires Soundex, Double Metaphone, alias matching
2. **Deliberate Obfuscation**: Adversarial actors provide false names, addresses, IDs to evade detection — requires cross-form consistency scoring
3. **Data Quality Variance**: 4M+ SARs filed by thousands of institutions with inconsistent formatting, spelling, and completeness
4. **Temporal Resolution**: Entity identity changes over time (name changes, corporate restructuring) — requires temporal-aware matching
5. **Volume Scaling**: 25M+ BSA filings/year with multi-million record cross-matching — requires efficient blocking strategies

### Matching Techniques

| Technique | Application | Example |
|-----------|------------|---------|
| **Soundex / Double Metaphone** | Phonetic name matching across spelling variations | "Smith" ↔ "Smyth" ↔ "Smythe" |
| **Alias Resolution** | Known aliases, name variants, transliterations | "Vladimir" ↔ "Volodymyr" ↔ "Wladimir" |
| **Date of Birth Fuzzy Matching** | Year match, transposed month/day, ±range | 1985-06-15 ↔ 1985-15-06 ↔ 1985 |
| **Address Standardization** | USPS CASS, international format normalization | "123 Main St" ↔ "123 Main Street" ↔ "123 MAIN ST" |
| **Tax ID / SSN / EIN Matching** | Exact + check-digit validation | SSN xxx-xx-xxxx format verification |
| **Account Number Matching** | IBAN/SWIFT/BIC normalization + routing validation | GB29NWBK60161331926819 → bank code + sort code + account |
| **Phone Number Normalization** | E.164 formatting, country code parsing | (212) 555-1234 ↔ +1-212-555-1234 |
| **Custom Heuristics** | Domain-specific weighting and threshold tuning | Assign BOI data higher weight than SAR narrative alone |

### Fellegi-Sunter Integration

FININT entity resolution maps naturally to Fellegi-Sunter probabilistic record linkage:

- **Agreement weights** for exact matches: tax ID (high), bank account number (high), DOB+name (medium), phone number (medium), address (medium-low)
- **Disagreement weights** for mismatches: SSN mismatch (strong evidence against match), name mismatch with matching DOB (weak evidence), address mismatch with matching bank account (weak evidence)
- **Blocking keys**: ZIP5+last name, IBAN prefix+account type, SWIFT BIC+country code, year of birth+name Soundex
- **Splink implementation**: FININT ER benefits from Splink's Fellegi-Sunter with term frequency adjustments, which accounts for common surname/address frequency in financial data

## Blocking Key Design for Financial Data

Efficient blocking is critical given 25M+ annual BSA filings. Recommended schemes:

1. **Account-grounded blocking**: IBAN country+check digits, SWIFT BIC8, ABA routing number — produces high-precision blocks with low cardinality
2. **Identity-grounded blocking**: SSN last-4 + ZIP5, EIN + state, DOB year + Soundex last name — balances recall and precision
3. **Entity-grounded blocking**: Legal entity identifier (LEI), tax ID + jurisdiction, registration number + jurisdiction — links FININT to corporate registries
4. **Cross-dataset blocking**: FININT account → corporate registry bank account filings, FININT EIN → government contracts UEI/DUNS, FININT name+address → campaign finance contributor records

## Cross-Domain Integration Patterns

### FININT → Campaign Finance ([[campaign-finance-entity-resolution]])
- SAR subjects who are also FEC contributors: cross-reference SAR narrative names against FEC individual contribution records
- CTR cash transaction patterns → straw donor detection: cash structuring (multiple sub-$10K deposits) before political contributions
- FinCEN BOI data → dark money entity resolution: trace anonymous LLC donors through beneficial ownership to known political operatives

### FININT → Government Contracts ([[government-contracts-entity-resolution]])
- SAR subjects with federal contracts: cross-reference against USASpending.gov UEI numbers and SAM.gov registrations
- Suspicious wire patterns → procurement fraud indicators: round-dollar payments, shell company payment chains, offshore intermediary routing
- FBAR foreign accounts → contractor foreign subsidiary mapping

### FININT → Lobbying Disclosure ([[lobbying-disclosure-entity-resolution]])
- SAR narrative entities → LD-2 registrant/client matching: same name resolution techniques applied
- Financial institution SARs → lobbying firm payment analysis: track flows between regulated entities and their lobbying representatives

### FININT → Corporate Registries ([[corporate-registry-analysis-entity-resolution]])
- BOI beneficial ownership → Secretary of State entity resolution: cross-validate ownership claims against financial signatures
- SAR shell company indicators → OpenCorporates network analysis: identify repeated addresses, nominee directors, circular ownership
- Account signatory names → corporate officer matching: who controls the bank account vs. who is listed as director

### FININT → Sanctions ([[secondary-sanctions-extraterritorial-enforcement]])
- SAR+CTR pattern analysis → sanctions evasion typology detection: ship-to-ship transfer financing, trade-based money laundering, nested correspondent banking
- SWIFT MT202 COV → intermediary bank sanctions exposure: identify non-sanctioned banks routing payments through sanctioned intermediaries
- OFAC 50 Percent Rule automation: aggregate FININT entity resolution results to calculate aggregate SDN ownership percentages

## Academic Research & Benchmarks

### Synthetic Data Generators

Financial transaction data for entity resolution research is scarce due to privacy constraints. Two key 2026 open-source generators address this:

- **IBM AMLSim** (Altman et al., arXiv:2306.16424v3, 2023): Agent-based synthetic financial transaction generator calibrated to real transaction patterns. Produces complete ground-truth labels — a key advantage over real data where many laundering transactions are never detected. Public datasets released.
- **Tide** (van den Beukel et al., arXiv:2603.01863v1, 2026): Graph-based financial network generator incorporating structural AND temporal laundering patterns. Reference datasets with varying illicit ratios (LI: 0.10%, HI: 0.19%). Benchmark results: LightGBM PR-AUC 78.05 (low illicit), XGBoost PR-AUC 85.12 (high illicit).

### Detection Models

- **Unsupervised cross-border AML** (Abdalwahid Sidiq & Wondaferew, arXiv: 2412.07027v1, 2024): CNN → CRNIM hybrid architecture for cross-border transaction anomaly detection. Model complexity correlates with detection accuracy.
- **Quantexa Decision Intelligence Platform** (Westphal 2025): Production entity resolution across BSA forms with Soundex, alias, address, phone, ID-number standardization and custom heuristic weighting.
- **DataWalk ER** (2024): AI-powered ER for financial crime with false positive reduction through knowledge graph contextualization.

## Architecture Notes

### Integration with Splink/Fellegi-Sunter

FININT ER is a natural Splink application domain: the blocking key → pairwise comparison → EM-trained match probability pipeline maps directly to BSA cross-form matching. Key considerations:

1. **Training data**: Use SAR-CTR pairs where SSN/EIN exact match provides ground truth for training Fellegi-Sunter m-probabilities
2. **Term frequency adjustments**: Common surnames in SAR data (Smith, Garcia, Patel) should have lower agreement weight than rare surnames
3. **Temporal decay**: Match probability should decay as transaction dates diverge — a 2010 SAR subject is less likely to be a 2025 CTR subject

### Agentic OSINT Integration ([[agentic-osint-autonomous-investigation]])

FININT ER as a tool module within agentic OSINT pipelines:
- SAR narrative extraction → LLM-based entity extraction → Splink matching → knowledge graph integration
- Multi-INT fusion: FININT (transaction data) + SIGINT (communications) + GEOINT (location) + OSINT (social media) for comprehensive entity profiles

## Verification Status

**Last verified: 2026-06-08**
- FinCEN SAR/CTR volumes confirmed per FinCEN.gov FY2024 release and EPCOR 2024 SAR Data Deep Dive
- BOI filing estimates confirmed per FinCEN 2025 implementation timeline
- IRS-CI query statistics confirmed per Quantexa blog (Westphal, March 2025)
- arXiv references verified against abstracts: 2306.16424v3, 2603.01863v1, 2412.07027v1
- Splink Fellegi-Sunter integration validated against existing [[campaign-finance-entity-resolution]] methodology

## Cross-Domain Connections

1. **Campaign Finance ER** — FININT SAR subjects as FEC contributors, straw donor detection via cash structuring patterns
2. **Government Contracts ER** — SAR subjects with federal contracts, procurement fraud indicators
3. **Lobbying Disclosure ER** — SAR narrative entities matched to LD-2 registrants/clients
4. **Corporate Registry Analysis** — BOI-SoS cross-validation, shell company network analysis
5. **Secondary Sanctions** — SAR pattern analysis for sanctions evasion typology detection
6. **Agentic OSINT** — FININT as tool module in autonomous investigation pipelines
7. **Knowledge Graph Construction** — FININT ER feeds into property graph enrichment ([[knowledge-graph-construction]])
8. **Open-Source ER Frameworks** — Splink implementation methodology ([[open-source-entity-resolution-frameworks]])

## References

1. Westphal, C. (2025). "Entity Resolution: The Key to Unlocking FinCEN Data." Quantexa Blog, March 17, 2025.
2. Altman, E. et al. (2023). "Realistic Synthetic Financial Transactions for Anti-Money Laundering Models." arXiv:2306.16424v3.
3. van den Beukel, M., Rožanec, J.M., Varbanescu, A.L. (2026). "Tide: A Customisable Dataset Generator for Anti-Money Laundering Research." arXiv:2603.01863v1.
4. Abdalwahid Sidiq, M., Wondaferew, Y.K. (2024). "Anti-Money Laundering Systems Using Deep Learning." arXiv:2412.07027v1.
5. DataWalk (2024). "Entity Resolution in Financial Crime: A Practical Guide to Uncover Hidden Risks."
6. ICIJ (2020). "FinCEN Files: Download Transaction Data." https://www.icij.org/investigations/fincen-files/
7. FinCEN (2025). "Frequently Asked Questions Regarding Suspicious Activity Reporting." Joint agency guidance, October 9, 2025.
8. EPCOR (2025). "2024 Deep Dive: SAR Data Across the Payments Networks."
