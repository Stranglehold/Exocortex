# Revenue Concentration Analysis for OSINT & Financial Intelligence

**Status:** STABLE
**Created:** 2026-07-25
**Cross-domain connections:** 15
**References:** 14

---

## 1. Overview

Revenue concentration analysis examines the degree to which a company's revenue depends on a small number of customers, products, or geographic markets. High customer or segment concentration represents material financial risk that is systematically disclosed in SEC filings (10-K, 10-Q) and provides a rich OSINT signal for entity resolution, sanctions evasion detection, and corporate vulnerability assessment.

**Key OSINT applications:**
- Identify single-customer dependencies that create leverage points for sanctions enforcement
- Detect undisclosed related-party transactions through anomalous customer naming patterns
- Map supply-chain concentration risk for critical infrastructure vulnerability assessment
- Cross-reference customer names across filings to resolve corporate entities

---

## 2. Regulatory Disclosure Framework

### 2.1 SEC Filing Requirements

Under ASC 275-10-50 (Risks and Uncertainties) and ASC 280-10-50 (Segment Reporting), publicly traded US companies must disclose:

1. **Major customer concentration** (ASC 280-10-50-42): If revenue from a single customer exceeds 10% of total revenue, the fact must be disclosed, though the customer need not be named by the company — customers are often identified as "Customer A" or "a US government agency."
2. **Geographic concentration** (ASC 280-10-50-41): Revenue and long-lived assets by country or region
3. **Segment reporting** (ASC 280-10-50-22): Operating segments with ≥10% of revenue, profit, or assets
4. **Risk factors** (Item 1A of 10-K): Narrative disclosure of customer concentration risk, even when below the 10% threshold

### 2.2 XBRL Structured Data Extraction

SEC EDGAR XBRL filings provide structured, machine-readable financial data using the US-GAAP taxonomy. Relevant tags:

| XBRL Tag | Description | Source |
|----------|-----------|--------|
| `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax` | Total revenue | Income Statement |
| `us-gaap:ConcentrationRiskPercentage1` | Percentage concentration for a given risk type | Risk Factors |
| `us-gaap:NumberOfMajorCustomers` | Count of major customers | Segment Reporting |
| `us-gaap:EntityWideRevenueMajorCustomerPercentage` | Revenue % from largest customer | Entity-Wide Disclosures |

**CIK as canonical identifier:** SEC CIK numbers provide unique identifiers across parent/subsidiary structures, enabling automated cross-filing entity resolution.

---

## 3. Analytical Methodology

### 3.1 Quantitative Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Customer Concentration Ratio (CCR) | Revenue from top-N customers / Total revenue | CCR₅ > 50% indicates high dependency |
| Herfindahl-Hirschman Index (HHI) | Σ(sᵢ²) over customer revenue shares | HHI > 2,500 = highly concentrated, HHI > 1,800 = moderately concentrated |
| Customer count trend | YoY change in number of disclosed major customers | Decreasing count signals intensifying concentration |
| Single-point-of-failure dependency | Max(CCR₁) for critical supply chain nodes | CCR₁ > 25% flagged as systemic risk |
| Revenue diversification index | 1 / HHI normalized to [0,1] | Near-zero = extreme dependency |

### 3.2 Narrative Analysis of Risk Factors

10-K Item 1A risk factors provide qualitative signals that complement quantitative metrics:

- **Specific vs. generic language:** "Loss of our largest customer, which accounted for 34% of revenue in FY2025..." signals higher materiality than boilerplate "We depend on a limited number of customers..."
- **Temporal trajectory:** Year-over-year changes in risk factor language — removal of a previously disclosed concentration may indicate customer loss or de-risking
- **Euphemism detection:** "Customer concentration" may be obscured as "key account risk," "revenue dependency," or "client diversification"

### 3.3 OSINT Cross-Referencing

Revenue concentration data from EDGAR can be cross-referenced with:

1. **Government contracts** (USAspending.gov, FPDS): Verify if unnamed major customers are USG agencies
2. **Lobbying disclosures** (LDA): Identify firms with high government revenue dependency
3. **Supply chain network analysis**: Map customer concentration across tiers
4. **Sanctions lists** (OFAC SDN, BIS Entity List): Detect sanctions-exposed revenue
5. **Corporate registries**: Resolve customer entity names to UBO structures

---

## 4. Application Patterns

### 4.1 Sanctions Evasion Detection

Revenue concentration analysis can identify entities with economic dependency on sanctioned jurisdictions or counterparties. Firms with >40% revenue from a single overseas customer in a high-risk jurisdiction face existential threat from sanctions designation — this creates both a detection signal and a behavioral prediction model for compliance risk.

### 4.2 Defense Industrial Base

Defense primes exhibit extreme customer concentration (60-95% USG revenue) as a feature, not a bug. Analysis should focus on:
- Subcontractor dependency (small firms with single-prime-program revenue)
- Foreign Military Sales (FMS) diversification trends
- Fixed-price program exposure as correlated concentration risk

### 4.3 Critical Infrastructure Supply Chain

The semiconductor supply chain exhibits three-level chokepoint concentration (manufacturing: TSMC >90% advanced; equipment: ASML sole EUV; design tools: Synopsys/Cadence/Siemens >80%). Revenue concentration analysis applied to each tier reveals systemic single-points-of-failure.

### 4.4 Shell Company / TBML Detection

Trade-based money laundering (TBML) and sanctions evasion often involve shell companies with concentrated customer relationships. Anomalous patterns include:
- Single-customer, single-supplier firms with no diversification
- Newly incorporated entities with immediate >90% concentration
- Customer names that resolve to known shell-company jurisdictions

---

## 5. Tool Ecosystem

| Tool | Function | Access |
|------|----------|--------|
| SEC EDGAR Full-Text Search | Raw filing retrieval (10-K, 10-Q, 8-K) | Free, rate-limited (10 req/s) |
| SEC XBRL API | Structured financial data extraction | Free, REST API |
| OpenCorporates | Entity resolution for customer names | Free tier / API paid |
| USAspending.gov | Cross-reference with federal contracts | Free, API available |
| Calcbench | Commercial XBRL analytics platform with concentration screening | Paid, API |
| BamSEC | Filing extraction and financial data normalization | Paid, API |
| Python EDGAR libraries | `python-edgar`, `edgartools`, `sec-api` | Open-source |

---

## 6. Investigation Workflow

**Phase 1 — Discovery:** Identify target companies via SEC EDGAR search or corporate registry

**Phase 2 — Extraction:** Pull 10-K, 10-Q filings; parse XBRL for concentration tags; extract Item 1A risk factors

**Phase 3 — Quantification:** Calculate CCR, HHI, and revenue diversification index; trend over 3-5 year window

**Phase 4 — Enrichment:** Cross-reference concentrated customers with sanctions lists, government contracts, lobbying disclosures

**Phase 5 — Resolution:** Resolve unnamed major customers via entity resolution (Fellegi-Sunter matching on partial names, revenue amounts, industry)

---

## 7. Legal & Ethical Boundaries

- EDGAR data is public; automated scraping within rate limits is permissible
- Customer name resolution must respect CFAA boundaries — passive, publicly available data only
- Concentration analysis may reveal material non-public information (MNPI) if combined with non-public datasets
- GDPR implications for EU company filings: customer names in risk factors may qualify as personal data
- Bellingcat framework: passive collection, public sources only, no unauthorized access

---


---

## 5. Quantitative Metrics & Calculation Methods

### 5.1 Customer Concentration Ratio (CCR)

The simplest measure: the fraction of total revenue attributable to the top <latex>n</latex> customers alone:

<latex>
CCR_n = rac{\sum_{i=1}^{n} R_i}{R_{total}}
</latex>

Where <latex>R_i</latex> is revenue from customer <latex>i</latex>. CCR₁ > 25% is flagged as a systemic single-point-of-failure risk.

### 5.2 Herfindahl-Hirschman Index for Revenue Concentration (HHI)

<latex>
HHI = \sum_{i=1}^{N} 10000 \cdot s_i^2
</latex>

Where <latex>s_i</latex> is the share of revenue from source <latex>i</latex>. An HHI of 10,000 means single-source monopoly; below 1,500 is considered unconcentrated. For OSINT applications, HHI above 2,500 suggests significant customer or geographic dependency warranting further investigation.

### 5.3 Revenue Diversification Score

<latex>
DS = 1 - CCR_1
</latex>

A simple complement of the single-customer concentration ratio. DS < 0.75 (i.e., CCR₁ > 25%) is the red-flag threshold for critical infrastructure supply chain analysis.

### 5.4 Geographic Concentration Metrics

- **GCCR (Geographic Customer Concentration Ratio)**: Revenue share from a single country > 50% suggests sanction or exchange-rate vulnerability.
- **Country HHI**: Same formula applied to geographic revenue segments as disclosed under ASC 280-10-50-41.

---

## 6. Practical SEC EDGAR Data Extraction

### 6.1 Access Patterns

Revenue concentration data is primarily sourced from SEC EDGAR filings. Extraction methods in order of complexity:

| Method | Data Structure | Effort | Best For |
|--------|---------------|--------|----------|
| SEC EDGAR Full-Text Search (HTML) | Unstructured text | Low | Ad-hoc single-company analysis |
| EdgarTools Python Library | Parsed 10-K/10-Q sections | Medium | Programmatic bulk extraction |
| XBRL/iXBRL structured data | Tagged financial facts | High | Cross-sectional quantitative studies |
| OpenEDGAR framework (arXiv:1806.04973) | Full corpus indexing | High | Research-grade bulk extraction |

### 6.2 Python Extraction with EdgarTools

```python
from edgar import *
set_identity("researcher@example.com")

# Get company filings
company = Company("AAPL")
tenk = company.get_filings(form="10-K").latest(1)

# Extract risk factors and customer concentration sections
doc = tenk.obj()
risk_factors = doc["Item 1A"]  # Risk Factors section

# Search for "Customer A" / "Customer B" patterns
import re
customer_refs = re.findall(r'Customer [A-Z]', risk_factors)
print(f"Unnamed major customers: {customer_refs}")

# Extract XBRL-tagged segment revenue
xbrl_data = tenk.xbrl()
segment_revenue = xbrl_data.revenue_by_segment
print(segment_revenue)
```

### 6.3 XBRL Fact Extraction

For large-scale analysis, XBRL-tagged facts in the `us-gaap` taxonomy provide structured access to segment disclosures:

- **RevenueFromExternalCustomer**: Revenue from major external customers
- **EntityWideRevenueMajorCustomer**: Number and revenue of major customers
- **SegmentReportingInformation**: Geographic and product segment breakdowns

Key data quality finding (AAA JIS 2018): 61% of SEC EDGAR log file accesses are for XBRL files rather than HTML/PDF, confirming XBRL as the preferred format for programmatic users.

---

## 7. Case Studies

### 7.1 Defense Industry Single-Customer Dependency

Defense primes exhibit extreme U.S. government concentration:
- **Lockheed Martin**: ~74% of revenue from U.S. Government (2025 10-K)
- **General Dynamics**: ~58% from U.S. Government
- **RTX (Raytheon)**: ~49% from U.S. Government

This concentration is OSINT-actionable: cross-referencing revenue concentration with [[government-contracts-procurement-osint]] data enables identification of which specific programs (F-35, Columbia-class, Sentinel) create the dependency, and how contract termination or Nunn-McCurdy cost breaches would cascade through the contractor's financial structure.

### 7.2 Semiconductor Supply Chain Chokepoints

TSMC's 2025 annual report reveals a three-tier concentration cascade:
1. **Manufacturing concentration**: >90% of advanced (<7nm) logic chips produced by a single fab
2. **Customer concentration**: TSMC's top two customers (Apple ~25%, NVIDIA ~12%) account for ~37% of revenue
3. **Equipment concentration**: ASML holds effective monopoly on EUV lithography

This cascade provides a template for applying revenue concentration analysis as a structural vulnerability detection framework — not just for financial risk but for [[supply-chain-network-analysis-osint]] and critical infrastructure dependency mapping.

### 7.3 Russian Sanctions-Evasion Entities

Post-2022 sanctions reshaped Russian corporate disclosures. Analysis of Moscow Exchange-listed entities revealed:
- Deliberate corporate re-domiciliation to non-sanctioning jurisdictions to obscure geographic revenue concentration
- New intermediate holding companies in UAE, Kazakhstan, and Turkey that break the direct Russia→customer revenue chain
- Russian defense conglomerates (Rostec subsidiaries) maintaining single-customer dependencies on the Russian MOD while using circuitous supply chains to source restricted components

These patterns connect revenue concentration directly to [[sanctions-evasion-detection]] and [[crypto-asset-tracing-blockchain-forensics-osint]] investigations.

---

## 8. Methodology: 5-Phase Revenue Concentration Investigation

| Phase | Action | Tools/Data | Output |
|-------|--------|-----------|--------|
| 1. Filing Discovery | Retrieve 10-K/10-Q from SEC EDGAR, identify disclosed major customers and segment breakdowns | EdgarTools, sec-api, OpenEDGAR | Company-customer matrix |
| 2. Customer Resolution | Resolve unnamed "Customer A/B/C" against [[corporate-registry-investigation-osint]], contract awards, press releases | OpenCorporates, SAM.gov, Wayback Machine | Named customer entities |
| 3. Concentration Calculation | Compute CCR, HHI, geographic concentration from XBRL segment data | pandas, edgartools.xbrl | Concentration metrics table |
| 4. Risk Cross-Reference | Check named customers against [[sanctions-evasion-detection]] lists, OFAC SDN, defense contract databases | SDN list, FPDS, ICIJ Offshore Leaks | Risk-flagged customers |
| 5. Network Construction | Build customer-supplier network graphs including parent/subsidiary relationships, identify systemic single-points-of-failure | NetworkX, Gephi | Dependency network visualization |

---

## 9. Data Quality & Limitations

- **Unnamed customer problem**: ASC 280-10-50-42 allows companies to avoid naming major customers. Entity resolution must rely on contextual clues ("a US government agency," contract timing, segment descriptions).
- **iXBRL vs traditional XBRL**: SEC phased in inline XBRL (iXBRL) starting 2018 for operating companies; embedding XBRL tags within HTML improves both human and machine readability (JETA 2018).
- **Foreign filer gaps**: Non-US companies filing 20-F often provide less granular segment disclosures.
- **Private companies**: No SEC filing requirement — revenue concentration must be inferred from other OSINT sources (trade credit reports, leaked financials, procurement data).


## 10. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[forensic-accounting-osint]] | SEC EDGAR data extraction, XBRL parsing, financial statement analysis |
| [[sanctions-evasion-detection]] | Concentration as sanctions vulnerability signal |
| [[corporate-registry-investigation-osint]] | Entity resolution of named/unnamed major customers |
| [[government-contracts-procurement-osint]] | Cross-reference USG concentration with contract data |
| [[supply-chain-network-analysis-osint]] | Customer concentration as supply chain risk indicator |
| [[defense-procurement-cycles]] | Defense prime single-customer dependency analysis |
| [[lobbying-disclosure-osint]] | Government concentration → lobbying intensity |
| [[trade-finance-monitoring]] | TBML single-customer shell company patterns |
| [[semiconductor-capital-expenditure-trends]] | Chokepoint concentration pattern isomorphism |
| [[alternative-data-sources-financial-intelligence]] | EDGAR filings as alternative financial data |
| [[entity-resolution-algorithms-2026]] | Fellegi-Sunter customer name resolution |
| [[data-breach-analysis-osint]] | Cross-referencing customer names in breach data |
| [[quantitative-factor-models]] | HHI and CCR as predictors in financial distress models |
| [[corporate-registry-investigation-osint]] | Domiciliation tracking for sanctions evasion concentration |
| [[alternative-data-sources-financial-intelligence]] | Revenue concentration as alternative data signal |


## 11. References

1. SEC EDGAR XBRL Filing Taxonomy, ASC 280-10-50 — Segment Reporting
2. ASC 275-10-50 — Risks and Uncertainties, Customer Concentration
3. Hands-On Machine Learning for Algorithmic Trading (Packt, 2018) — Ch. 2: Market and Fundamental Data, SEC EDGAR fundamentals
4. Defense Procurement Cycles (Exocortex wiki, 2026) — Revenue concentration in defense primes
5. US-China Semiconductor Supply Chain (Exocortex wiki, 2026) — Chokepoint concentration pattern
6. Forensic Accounting & OSINT (Exocortex wiki, 2026) — SEC EDGAR CIK identifiers, XBRL extraction
7. Supply Chain Network Analysis via OSINT (Exocortex wiki, 2026) — Single-point-of-failure analysis
8. Sanctions Evasion Detection (Exocortex wiki, 2026) — Shell company concentration patterns
9. EdgarTools — Python library for SEC EDGAR access, dgunning/edgartools (GitHub, 2026)
10. OpenEDGAR: Open Source Software for SEC EDGAR Analysis, Bommarito et al. (arXiv:1806.04973)
11. Are XBRL Files Being Accessed? Evidence from the SEC EDGAR Log File Dataset, AAA JIS 32(3), 2018
12. Inline XBRL versus XBRL for SEC Reporting, JETA 12(1), 2018
13. Revenue Concentration as a Factor in Corporate Credit Risk — Merton model integration framework
14. ASC 280-10-50-42 — Major Customer Disclosure Requirements (updated 2025)
