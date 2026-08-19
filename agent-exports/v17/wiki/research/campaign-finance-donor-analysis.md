# Campaign Finance & Donor Networks Analysis for OSINT

**Status:** STABLE
**Last updated:** 2026-06-03

## Overview

Campaign finance and donor network analysis is a critical OSINT subdomain for identifying political influence, hidden financial connections, and power structures. By combining public campaign finance disclosures from the FEC (Federal Election Commission), OpenSecrets data, and state-level transparency portals with network analysis techniques, investigators can map influence networks, detect dark money flows, and uncover coordination between seemingly unrelated actors.

## Key Data Sources

| Source | Coverage | Format | Notes |
|--------|----------|--------|-------|
| [FEC.gov](https://www.fec.gov/data/) | Federal candidates, PACs, parties | REST API, bulk CSV | Official source; itemized individual contributions $200+ |
| [OpenSecrets](https://www.opensecrets.org/) | Federal + some state | API, web | Aggregated with donor/industry classifications |
| [ProPublica Campaign Finance API](https://projects.propublica.org/api-docs/campaign-finance/) | Federal | REST API | Enriched with social media accounts |
| [Apify FEC Actor](https://apify.com/ryanclinton/fec-campaign-finance) | Federal | API | Entity-resolved, automation-ready |
| [FECGraph](https://www.fecgraph.com/) | Federal | Knowledge graph | Stanford/Columbia graph-based linking |
| [DonorSecrets](https://www.donorsecrets.com/) | Federal | Web UI | Employer giving patterns, vendor networks |
| [FollowTheMoney](https://www.followthemoney.org/) | State-level | API, web | State campaign + ballot measure contributions |
| State disclosure portals | State-specific | Varies | CA Cal-Access, NY BOE, TX Ethics Commission, etc. |

## Methodology

### 1. Donor Network Graph Construction
- Extract contributor-recipient edges from FEC bulk data (individual contributions, committee-to-committee transfers)
- Normalize entity names (handling variants, misspellings, committee name changes) using **entity resolution** techniques (see [[data-aggregation-entity-resolution]])
- Construct bipartite donor-committee graph; project to donor co-contribution network for influence clustering
- Tools: Python NetworkX, Gephi, Neo4j

### 2. Contribution Pattern Analysis
- **Bundling detection:** Identify multiple contributions from same employer/zip on same day, routed to same candidate (bundler flag)
- **Straw donor detection:** Look for low-income ZIP codes with high-dollar contributions; retirees with maxed-out contributions; contribution velocity anomalies
- **Cycle-over-cycle comparison:** Track donor persistence, loyalty shifts between primary/general, party-switching
- **Geographic analysis:** heat-mapped ZIP code contributions overlaying demographic data

### 3. Dark Money / 501(c)(4) Tracing
- Chain of custody: Super PAC <- 501(c)(4) <- 501(c)(3) donor-advised funds
- Cross-reference IRS Form 990 filings with FEC independent expenditure data
- Use OpenSecrets "Dark Money" database and FEC "independent expenditures" to trace to known donors
- **Corporate registry linkage:** link corporate donors to parent entities using state Secretary of State filings (see [[cross-jurisdictional-entity-resolution]])

### 4. Lobbying-Campaign Finance Intersection
- Match lobbyist bundlers (LD-203 reports) to campaign contribution data
- Map lobbying expenditures (LD-2) to recipients and issues, correlate with PAC giving

## Tools

| Tool | Type | Use Case |
|------|------|----------|
| FEC API | REST API | Query contributions by donor name, employer, zip, date range |
| OpenSecrets API | REST API | Donor lookup, org profiles, industry totals |
| ProPublica Campaign Finance API | REST API | Candidate/committee summaries, independent expenditures |
| Apify FEC Actor | Automation | Bulk extraction with entity resolution |
| NetworkX + Gephi | Graph analysis | Donor network visualization, community detection |
| Python (pandas) | Data analysis | Contribution aggregation, anomaly detection, pattern mining |
| Splink/Dedupe | Entity resolution | Name matching across contribution records |

## Algorithmic Approaches (from arXiv research)

- **Graph Neural Networks (GNNs)** for financial transaction network analysis (arXiv:2111.15367) — applicable to donor-PAC-recipient graph classification
- **Social Network Analysis** (arXiv:2102.10014) — community detection, centrality metrics for influence quantification
- **Online Entity Resolution over incomplete data streams** (arXiv:2103.08720) — real-time donor deduplication as new FEC filings arrive
- **Criminal Network Analysis** using graph theory (arXiv:2103.02504) — pattern detection techniques transferable to dark money networks

## Structured Analytic Techniques

Apply Structured Analytic Techniques (see [[structured-analytic-techniques-osint]]) to donor network analysis:
- **Analysis of Competing Hypotheses (ACH):** Which entity is the true source of a dark money network?
- **Key Assumptions Check:** Is employer-reported contribution data accurate, or are intermediaries masking the true source?
- **Indicators/Signposts:** Set triggers for coordination patterns (e.g., same-day contributions from geographically dispersed donors)

## Cross-domain Connections

- **Data Aggregation & Entity Resolution** ([[data-aggregation-entity-resolution]]): Core technique for merging FEC, IRS, and state corporate records
- **Cross-Jurisdictional Entity Resolution** ([[cross-jurisdictional-entity-resolution]]): Linking donors across federal/state boundaries, international donations
- **OSINT Investigation Methodology** ([[human-investigation-tactics-techniques]]): Investigative mindset applied to financial tracing
- **Public Records Databases** ([[public-records-databases-osint]]): Corporate registries, property records, and court filings supplement donation data
- **Knowledge Graph Construction** ([[knowledge-graph-construction]]): FECGraph-style knowledge graphs for multi-hop donor-recipient traversal
- **Visual OSINT** ([[reverse-image-search-visual-osint]]): Cross-referencing event photos with donor attendance for relationship mapping
- **Network Analysis Techniques** ([[network-analysis-techniques-osint]]): Graph metrics for influence identification

## References

1. Federal Election Commission. (2026). *Campaign Finance Data*. https://www.fec.gov/data/
2. OpenSecrets. (2026). *Center for Responsive Politics*. https://www.opensecrets.org/
3. ProPublica. (2026). *Campaign Finance API*. https://projects.propublica.org/api-docs/campaign-finance/
4. Apify. (2026). *FEC Campaign Finance Actor*. https://apify.com/ryanclinton/fec-campaign-finance
5. FECGraph. (2026). *Knowledge Graphs for Campaign Finance Data*. https://www.fecgraph.com/
6. DonorSecrets. (2026). *U.S. Election Money Explorer*. https://www.donorsecrets.com/
7. Kim, J., et al. (2021). *A Review on Graph Neural Network Methods in Financial Applications*. arXiv:2111.15367.
8. Li, Y., et al. (2021). *Social Network Analysis: From Graph Theory to Applications with Python*. arXiv:2102.10014.
9. Ren, W., et al. (2021). *Online Topic-Aware Entity Resolution Over Incomplete Data Streams*. arXiv:2103.08720.
10. arXiv:2103.02504. (2021). *Graph and Network Theory for the Analysis of Criminal Networks*.
11. FollowTheMoney. (2026). *National Institute on Money in Politics*. https://www.followthemoney.org/
