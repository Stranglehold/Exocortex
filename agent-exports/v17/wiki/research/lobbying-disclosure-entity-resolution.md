# Lobbying Disclosure Analysis for Entity Resolution

**Status:** DRAFT  
**Created:** 2026-06-04  
**Domain:** Data Aggregation & Entity Resolution  
**Origin:** interests.md — "campaign finance records, lobbying disclosures, government contracts, property records"

## Overview

Lobbying disclosure data provides a structured, legally mandated window into influence networks — who is paying whom to shape policy, and on what issues. When combined with corporate registries, campaign finance, and government contracts data, lobbying records enable entity resolution that reveals the full architecture of corporate influence.

The Lobbying Disclosure Act of 1995 (LDA), as amended by the Honest Leadership and Open Government Act of 2007 (HLOGA), requires lobbying firms and organizations to register and file quarterly reports. These filings create a rich longitudinal dataset linking clients, lobbying firms, individual lobbyists, issues lobbied, and money spent.

## Key Data Sources

| Source | Description | Access |
|--------|-------------|--------|
| **LDA.gov / Congress.gov** | Official repository of LD-1 (Registration), LD-2 (Quarterly Activity), and LD-203 (Contributions) filings | Public web, bulk downloads |
| **OpenSecrets (CRP)** | Standardized lobbying expenditure, revolving-door, and influence data; API access | Free tier + paid bulk data |
| **ProPublica Lobbying API** | Structured JSON access to federal lobbying filings with congress.gov integration | Free API, rate-limited |
| **Senate Office of Public Records (SOPR)** | Raw filing data and image PDFs | Public, lower usability |
| **State-level lobbying databases** | 50 separate jurisdictions with varying disclosure quality and formats | Fragmented, varying schema |
| **GAO Lobbying Disclosure Audits** | Periodic compliance audits (e.g., GAO-24-106799, April 2024) | Public PDFs |

## Data Structure

### LD-1: Lobbying Registration
- Registrant name, address, and contact
- Client name and business description
- General lobbying issues (26 categories)
- Affiliated organizations and foreign entities
- Effective date of registration

### LD-2: Quarterly Activity Report
- Registrant and client identifiers
- Specific lobbying issues (bill numbers, agency rules)
- Lobbyists involved (name, covered position)
- Houses of Congress and agencies contacted
- Income/expenses (rounded to nearest $10,000 or $20,000)
- Foreign entity involvement

### LD-203: Semiannual Contributions Report
- Political contributions by registrants and lobbyists
- FEC-certified committee contributions
- Honorary contributions and event sponsorships

## Entity Resolution Challenges

### Name Variation
- Lobbying firms frequently use different legal names vs. trade names (e.g., "Brownstein Hyatt Farber Schreck, LLP" vs. "Brownstein Hyatt")
- Client subsidiaries may report under parent names inconsistently
- Individual lobbyist names may include middle initials, suffixes, or nicknames across filings

### Subsidiary & Affiliate Resolution
- Large corporations file through multiple subsidiaries; resolving to ultimate parent requires corporate registry cross-referencing
- Foreign agent registration (FARA) overlaps with LDA for foreign-owned entities
- Trade associations represent coalitions of companies; attributing influence to individual member firms is non-trivial

### Revolving Door Mapping
- Lobbying firms employ former congressional staff, executive branch officials, and regulators
- Resolving these individuals across LDA filings, Senate financial disclosures, and LinkedIn profiles creates identity linkage challenges

### Temporal Coverage Gaps
- LDA thresholds ($3,000/quarter lobbying income for firms, $13,000/quarter for organizations) create a floor below which activity is invisible
- Registration effective dates create edge cases for quarterly alignment
- State-level lobbying filing frequency varies (monthly, quarterly, annual)

## Integration Patterns with Other OSINT Data Sources

### Campaign Finance (FEC.gov)
- Cross-reference lobbyist political contributions (LD-203) with FEC individual contribution records
- Match lobbying clients with corporate PAC contributions
- Identify coordinated influence campaigns across lobbying and campaign finance

### Government Contracts (USASpending.gov, SAM.gov)
- Resolve lobbying registrants to federal contractors via UEI and parent-subsidiary linkages
- Correlate lobbying expenditure spikes with contract award periods
- Map lobbying issues to specific contract categories (NAICS codes)

### Corporate Registries (OpenCorporates, state SoS)
- Resolve lobbying firm and client legal entities to registered business records
- Identify beneficial ownership structures behind lobbying registrants
- Cross-jurisdictional resolution for foreign-owned lobbying entities

### Property Records
- Map lobbyist and client addresses from LDA filings to property ownership records
- Identify concentrated influence geography (K Street corridor, D.C. metro area)

## Graph Structures in Lobbying Networks

Lobbying data naturally forms a bipartite graph:
- **Nodes**: registrants (firms/organizations), clients, individual lobbyists, issues, agencies, congressional members
- **Edges**: lobbying contracts (registrant-client), issue assignments (lobbyist-issue), contributions (lobbyist/lobbying firm-PAC/candidate), agency contacts

Key analytical approaches:
- **Centrality analysis**: identify gatekeeper lobbyists who bridge multiple clients
- **Community detection**: cluster firms by issue portfolio overlap (energy, tech, defense, healthcare)
- **Temporal edge analysis**: track lobbying effort shifts before/after regulatory changes
- **Power-law distribution**: few firms handle disproportionate share of lobbying expenditure (e.g., top 10 firms = ~15-20% of total)

## Entity Resolution Pipeline

A typical lobbying-focused entity resolution pipeline:

1. **Ingestion**: Download LD-1/LD-2/LD-203 bulk data from LDA.gov; augment with OpenSecrets standardized data
2. **Preprocessing**: Normalize entity names (strip suffixes, standardize "LLC" vs "L.L.C.", remove trade names), extract unique registrant and client identifiers
3. **Blocking**: Block on registration ID (LDA-specific), organization name n-grams, lobbyist name phonetic codes (Soundex, Double Metaphone)
4. **Matching**: Apply Fellegi-Sunter probabilistic record linkage; use LLM-assisted matching for cross-jurisdictional name variations
5. **Graph Construction**: Build registrant-client-lobbyist-issue graph; merge with campaign finance, government contracts, and corporate registry nodes via cross-dataset entity resolution
6. **Analysis**: Network analytics (centrality, community detection), influence scoring, anomaly detection (unusual lobbying patterns)

## Tools & Frameworks

| Tool | Role |
|------|------|
| OpenSecrets CRP API | Standardized lobbying data extraction |
| ProPublica Congress API | Lobbying filing retrieval |
| Splink / dedupe / Zingg | Probabilistic record linkage |
| NetworkX / Neo4j | Graph construction and analysis |
| Maltego CE / SpiderFoot HX | OSINT graph exploration |
| LLMs (Claude, GPT) | Cross-jurisdictional name matching assistance |

## References

1. Lobbying Disclosure Act of 1995, as amended (2 U.S.C. § 1601 et seq.) — statutory framework
2. GAO-24-106799, "2023 Lobbying Disclosure: Observations on Compliance," April 2024
3. OpenSecrets (Center for Responsive Politics), "Lobbying Data Summary," https://www.opensecrets.org/federal-lobbying
4. ProPublica Congress API, "Lobbying," https://projects.propublica.org/api-docs/congress-api/lobbying/
5. LDA.gov, Home of the Lobbying Disclosure Act Database, https://lda.gov/system/public/
6. LaPira, T. M., & Thomas, H. F. (2014). "Revolving Door Lobbying: Public Service, Private Influence, and the Unequal Representation of Interests." University Press of Kansas.
7. Fellegi, I. P., & Sunter, A. B. (1969). "A Theory for Record Linkage." Journal of the American Statistical Association.
8. Christen, P. (2012). "Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection." Springer.
9. ICIJ, "Luxembourg Leaks" methodology, 2014 — cross-dataset lobbying and corporate registry integration
10. Sunlight Foundation (archived), "Influence Explorer," bulk lobbying and campaign finance data integration methodology

## Cross-Domain Connections

- [[campaign-finance-donor-analysis]]: Lobbying contributions (LD-203) mirror campaign finance donor networks; joint analysis reveals coordinated influence strategies
- [[government-contracts-entity-resolution]]: Lobbying clients are often federal contractors; resolving entities across lobbying disclosures and USASpending.gov surfaces procurement influence
- [[property-records-entity-resolution]]: Lobbyist and client addresses from LDA filings mapped to property ownership for geographic influence concentration analysis
- [[data-aggregation-entity-resolution]]: Lobbying data is the "how" layer in the influence stack (campaign finance = who gives, lobbying = who shapes policy, contracts = who benefits)
- [[cross-jurisdictional-entity-resolution]]: Foreign-owned lobbying registrants require cross-border corporate registry resolution; FARA overlaps add complexity
- [[network-analysis-graph-theory]]: Bipartite lobbying networks analyzed via centrality, community detection, and temporal edge dynamics
- [[osint-visualization-techniques]]: Lobbying networks visualized as force-directed graphs in Maltego, Cytoscape, or Gephi with geographic and temporal overlays
- [[corporate-registry-analysis-entity-resolution]]: Registrant and client entity resolution against state Secretaries of State and OpenCorporates databases
- [[intelligence-failure-analysis]]: Structural isomorphism — lobbying disclosure gaps and threshold under-reporting mirror intelligence collection blind spots; both require adversary modeling of what is NOT observed

---

**Last Verified:** 2026-06-04  
**Verification Status:** Verification status block added per program.md
