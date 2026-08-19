# Job Posting Analysis for Economic Intelligence & Entity Resolution

**Status:** STABLE | **Created:** 2026-07-17 | **Deepened:** 2026-07-17
**Source Field Report:** (none — direct BUILD cycle)
**Grounded In:** Exocortex v17 corpus (job-posting-alt-data-forecasting), 355-book technical library, arXiv 2025-2026, industry data provider documentation

---

## Overview

Job posting analysis — systematic collection and analysis of online job advertisements — serves as a real-time economic indicator, an alternative data source for investment analysis, and an OSINT technique for entity resolution. Unlike lagging government statistics (JOLTS at ~30 days, BLS employment reports at ~45 days), job postings provide near-real-time signals on hiring demand, skill evolution, corporate growth trajectories, and organizational structure. The BLS data gap (ongoing since 2025) has accelerated institutional adoption of job posting data as a primary labor market signal — forcing the Federal Reserve into an unplanned natural experiment in operating monetary policy on alternative data.

---

## Data Provider Ecosystem

| Provider | Scale | Key Features | Entity Resolution |
|----------|-------|-------------|-------------------|
| **Revelio Labs** | 5B+ records, 1M+ company websites | Proprietary RCID (Revelio Company ID) universe; subsidiary-to-parent mapping; workforce dynamics | Full entity resolution — each subsidiary has own RCID tied to parent |
| **Lightcast** (fka Burning Glass/Emsi) | 2.5B job postings, 800M career profiles, 100+ gov sources, 160+ countries | Skills taxonomy, career pathways, education alignment | Company standardization across sources |
| **Coresignal** | 468M+ job posting records, 452M company/employee profiles | Real-time freshness, multi-source deduplication | Fellegi-Sunter matching at production scale; 452M-record multi-source dedup |
| **Indeed Hiring Lab** | Proprietary (Indeed.com) | Wage growth tracker, posting trends by sector/geography | Internal employer normalization |
| **LinkUp** | Direct employer websites only (no aggregator noise) | Highest signal quality — only scrapes company career pages; JOLTS-adjacent methodology | Domain-to-employer mapping |
| **WRDS (Wharton)** | Academic access to Revelio Labs | University research integration | Leverages RCID mapping |

**Comparability Note:** Each provider scrapes different sources with different deduplication and normalization. LinkUp's direct-employer-only methodology produces structurally different counts than Lightcast's broad aggregation. Cross-provider comparisons require understanding of source coverage and dedup methodology.

---

## Economic Leading Indicator Applications

### Macroeconomic Nowcasting

Job posting volume and composition lead official employment statistics by 2-6 weeks:
- **Osborn et al. (arXiv:2510.23358)**: HR-perspective LLM-based forecasting yields better short-term predictions than economic-policy perspective — suggesting domain-specific framing matters for LLM nowcasting
- **JobPulse (arXiv:2508.11014)**: Big data approach to real-time engineering workforce monitoring; demonstrates skill-mismatch identification through job posting analysis
- **Nature (2024)**: Job vacancy forecasting using posting data validated against official statistics
- **IMF (2025)**: Nowcasting GDP from job posting velocity and sector composition

### Signal Extraction Methodologies

1. **YoY Posting Volume Change**: Sector-level growth/contraction leading indicators
2. **Posting Duration (Time-to-Fill)**: Extended durations signal skill shortages or wage friction
3. **Wage Posting Analysis**: Listed salary ranges as real-time wage pressure indicator
4. **Sector Rotation Signals**: Relative posting growth shifts precede sector ETF rotation by 4-8 weeks
5. **Geographic Dispersion**: Regional posting concentration/deconcentration as economic geography signal

### BLS Data Gap Context

The BLS data gap forced institutional adoption of alternative labor market signals. The outcome — whether job posting data becomes institutionally permanent or reverts to supplementary status — remains undetermined as of mid-2026.

---

## Entity Resolution via Job Posting Metadata

Job postings are a rich but underutilized entity resolution source. Each posting contains structured metadata useful for corporate entity resolution:

### Resolvable Fields

| Field | Resolution Utility |
|-------|-------------------|
| Legal entity name | Direct entity identification |
| Office/worksite address | Geospatial entity resolution; subsidiary location mapping |
| Parent-subsidiary relationships | Organizational hierarchy reconstruction |
| Department/division names | Internal organizational structure inference |
| Recruiter/HR contact | Individual-level entity resolution |
| Benefits references (401k provider, health insurer) | Third-party relationship mapping |
| Technology stack mentions | Entity attribute enrichment |

### Coresignal Methodology

Coresignal's production pipeline performs multi-source deduplication across 452M records using Fellegi-Sunter probabilistic matching at scale. Each company receives a unique identifier with parent-subsidiary linkage — structurally simpler than beneficial ownership ER but informative for approaches to harder ER problems. The job posting ER problem (with temporal dynamism — companies change names, acquire, divest) is a valuable benchmark for evaluating entity resolution frameworks.

### Revelio Labs RCID Architecture

Revelio maps each publicly reported position to a Revelio Labs Company ID (RCID) — a proprietary company universe identifier. Each subsidiary company has its own RCID tied to its parent, enabling both granular subsidiary analysis and consolidated parent-level aggregation. This entity resolution layer is Revelio's core IP differentiator.

---

## Corporate Intelligence & Strategy Inference

### Strategic Signal Extraction

Job postings reveal corporate strategy before official announcements:
- **New office/location openings**: Postings for new cities precede press releases by 2-6 months
- **Product pivot signals**: Rapid skill requirement changes in engineering postings signal product direction shifts
- **M&A integration**: Post-acquisition hiring pattern changes reveal integration strategy
- **R&D investment**: Research-focused postings (PhDs, "Research Scientist") as R&D intensity proxy
- **Growth vs. efficiency regime**: Sales/GTM hiring vs. engineering hiring ratios signal strategic phase

### Competitive Intelligence

- **Headcount growth estimation**: Posting volume as proxy for headcount growth, especially for private companies without public disclosures
- **Organizational structure reconstruction**: Department/team hierarchies inferred from reporting line mentions in postings
- **Compensation benchmarking**: Listed salary ranges (increasingly required by state pay transparency laws) enable real-time compensation intelligence

---

## Skills & Technology Tracking

### Generative AI Workforce Transformation

**Generative-AI and the Transformation of Workforce (arXiv:2605.00843)**: Large-scale, multi-source analysis of how generative AI is reshaping job requirements, skill compositions, and sectoral dynamics. Key findings:
- Gen-AI-related skill mentions in job postings serve as leading indicators of technology adoption
- The augmentative vs. substitutive distinction can be tracked through posting language — "work with AI" vs. "AI-powered" framing
- Sectoral diffusion patterns follow predictable S-curves identifiable from posting data

### Technology Adoption Signals

| Technology | Posting Signal | Lead Time vs. Revenue Impact |
|-----------|---------------|------------------------------|
| Kubernetes/containerization | DevOps engineer requirements | 12-18 months |
| LLM/GenAI | "Prompt engineer," "AI/ML" growth | 6-12 months (emerging) |
| Cloud migration | AWS/Azure/GCP certification requirements | 12-24 months |
| Cybersecurity | Security engineer/compliance roles | 6-12 months post-breach normalization |

---

## Automated Collection & OSINT Integration

### Collection Pipeline Architecture

Job posting collection follows standard OSINT automation patterns:
1. **Seed discovery**: Identify target companies and their career page URLs
2. **Structured scraping**: Direct career page scraping (LinkUp methodology) + aggregator API access (Indeed, LinkedIn)
3. **Deduplication**: Fellegi-Sunter probabilistic matching across sources; cross-posting detection
4. **Entity resolution**: Map postings to corporate entity identifiers (RCID, Coresignal ID)
5. **Temporal indexing**: Track posting creation/modification/removal dates for time-series analysis

### OSINT Integration Pathways

- [[osint-reconnaissance-automation-toolchain]]: Job posting collection fits within the 5-phase OSINT automation pipeline (seed discovery → structured recon → automated correlation → entity resolution → graph export)
- [[web-traffic-analytics-alternative-data]]: Job postings are a canonical alternative data source alongside web traffic, patent filings, and satellite imagery
- [[data-breach-analysis-osint]]: Job posting metadata can be cross-referenced with breach data for identity linkage
- [[anti-bot-evasion-state-of-art]]: Scraping job boards at scale requires behavioral mimicry to evade bot detection; same techniques apply
- [[legal-ethical-osint]]: Job posting scraping sits in a legal gray area — public data but subject to platform ToS and CFAA considerations (Bright Data precedent supports scraping of publicly accessible data)

### Exocortex Integration Architecture

| Component | Integration |
|-----------|------------|
| **Irreversibility Gate** | Job posting collection is read-only OSINT — low irreversibility risk; automated scraping may trigger rate limiting or IP blocks |
| **Memory Consolidation** | Company entity profiles enriched with job posting signals; temporal decay modeling for posting freshness |
| **Entity Resolution Pipeline** | Job posting metadata feeds into Exocortex entity resolution alongside corporate registries, SEC filings, and government contracts |
| **Tool Registry** | Coresignal/Revelio APIs as registered data tools; Indeed/LinkedIn scraping as browser-automation tools |

---

## Research Frontiers (2025-2026)

1. **LLM-Based Nowcasting**: Osborn et al. demonstrate that LLM-based job posting analysis with HR-domain framing yields superior short-term forecasts; domain-specific prompting as methodological innovation
2. **Skill Mismatch Identification**: JobPulse (arXiv:2508.11014) — real-time engineering workforce monitoring identifying skill mismatches between postings and candidate profiles
3. **Gen-AI Diffusion Tracking**: arXiv:2605.00843 — using job posting language to track augmentation vs. substitution patterns across sectors
4. **Privacy-Preserving Collection**: Local model running job posting analysis on-device enables privacy-preserving labor market research (no need to send company hiring data to third-party APIs)
5. **Privacy-Preserving Entity Resolution**: Applying differential privacy and SMPC techniques to job posting ER — matching entities across providers without exposing raw data
6. **Causal Inference from Posting Data**: Distinguishing organic hiring demand from phantom postings (evergreen reqs, H-1B compliance postings, market-testing postings)

---

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[entity-resolution-agent-safety]] | Coresignal's 452M-record multi-source deduplication uses Fellegi-Sunter at scale; job posting ER is structurally simpler than beneficial ownership ER and can inform approaches to harder entity resolution problems |
| [[alternative-data-sources-financial-intelligence]] | Job posting data is a canonical alternative data source alongside satellite imagery, credit card transactions, and web traffic analytics |
| [[osint-reconnaissance-automation-toolchain]] | Job posting collection fits within the 5-phase OSINT automation pipeline |
| [[web-traffic-analytics-alternative-data]] | Job postings listed alongside web traffic, patent filings, and search trends as alternative data for earnings nowcasting |
| [[legal-ethical-osint]] | Scraping legality — Bright Data precedent, CFAA considerations, platform ToS vs. public data rights |
| [[data-breach-analysis-osint]] | Job posting metadata cross-referenced with breach data for identity linkage |
| [[market-microstructure-liquidity-dynamics]] | Alternative data in trading — job posting signals as alpha source for systematic strategies |
| [[ai-agent-architecture-local-inference]] | Alternative data fusion problem (BLS surveys + scraped postings with different reliability profiles) is isomorphic to Exocortex knowledge fusion |
| [[federal-reserve-repo-market-mechanics]] | BLS data gap forced Fed into alternative data-dependent monetary policy |
| [[knowledge-graph-construction-patterns]] | Job posting → entity knowledge graphs; companies as nodes, postings as edges with temporal attributes |
| [[intelligence-failure-analysis]] | BLS data gap structurally analogous to SIGINT outages — when primary collection source goes dark, analysts must fall back on alternative sources with different reliability profiles |
| [[bridging-local-frontier-model-performance]] | Local model job posting analysis enables privacy-preserving labor market research |
| [[differential-privacy-osint-entity-resolution]] | Privacy-preserving entity resolution techniques applicable to job posting data matching across providers |
| [[quantitative-analysis-techniques]] | Job posting velocity as earnings predictor bridges alternative data forecasting to earnings surprise modeling |

---

## References

1. Osborn et al. (2025). "Job Posting Data for Economic Nowcasting." arXiv:2510.23358
2. M et al. (2025). "JobPulse: A Big Data Approach to Real-Time Engineering Workforce Monitoring." arXiv:2508.11014
3. (2026). "Generative-AI and the Transformation of Workforce: A Job Postings Analysis." arXiv:2605.00843
4. Revelio Labs. "Job Posting Data: 5B+ Records from 1M+ Company Websites." https://www.reveliolabs.com/job-postings-cosmos/
5. Lightcast. "The Standard for Labor Market Intelligence." https://lightcast.io/
6. Coresignal. "Real-Time Public Web Data." https://coresignal.com/
7. Indeed Hiring Lab. https://www.hiringlab.org/
8. LinkUp. "Job Market Data." https://www.linkup.com/
9. WRDS/Wharton. "Revelio Labs Data." https://wrds-www.wharton.upenn.edu/
10. IMF (2025). Job posting velocity and GDP nowcasting validation
11. Nature (2024). Job vacancy forecasting using online posting data
12. Coresignal. "Job Posting Data for Real-Time Insights: 468M+ Records." https://coresignal.com/alternative-data/job-postings-data/
13. JobPulse. arXiv:2508.11014 — Engineering workforce real-time monitoring
14. Fellegi, I.P. & Sunter, A.B. (1969). "A Theory for Record Linkage." Journal of the American Statistical Association
