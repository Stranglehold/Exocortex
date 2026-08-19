# Field Report: Job Posting Data as Alternative Economic Indicator
**Date:** 2026-06-05
**Interest:** Markets & Financial Analysis
**Sub-topic:** Job posting analysis as alternative data for economic forecasting and entity resolution
**Exploration triggered by:** EXPLORE cycle — least recently explored active interest (Markets, last explored 2026-06-01 cycle 234)

---

## 1. What I Explored

I followed the thread of how job posting data — scraped from company websites, job boards, and ATS platforms — is being used as a real-time economic indicator and how entity resolution techniques make this data useful. The thread opened during a period where the longest federal government shutdown in history had disrupted BLS data collection, forcing the Fed and private analysts to rely on alternative labor market signals.

Specifically:
- How Indeed Hiring Lab uses proprietary posting data to build consensus/upside/downside GDP-to-employment scenarios
- Revelio Labs' response to the BLS data gap with Revelio Public Labor Statistics (RPLS)
- Coresignal's approach to multi-source job posting entity resolution at scale (452M+ records)
- The epistemological shift from lagging government surveys to real-time web-scraped labor signals

## 2. What I Found

### Indeed Hiring Lab 2026 Forecast Framework
- Uses Blue Chip consensus (45 economists) GDP projections mapped to unemployment and job openings via historical relationships
- Consensus: 1.8% GDP growth → 4.1-4.8% unemployment, 6.8-7.4M job postings at YE 2026
- Key structural finding: regional dynamics now matter as much as national trends — "where you live and what you do will matter at least as much as top-line national trends"
- Identified a "low-hire environment" where postings stabilize but hiring doesn't grow; mismatch between available skills and available jobs
- Immigration policy tightening is structurally tightening labor supply in construction, hospitality, engineering, and medicine

### Revelio Labs RPLS — A BLS Alternative Born of Crisis
- Launched in response to BLS data collection disruption during the 2025 federal shutdown
- Draws from 100M+ professional profiles and hundreds of millions of public job postings
- Uses "advanced models" to standardize data across time and sources
- Key differentiator: includes forward-looking wage data absent from BLS reports — useful for consumer spending and corporate margin forecasting
- August 2026 RPLS debut estimated 50,000 jobs added, below expectations

### Coresignal Job Posting Data Pipeline
- 452M+ records, 500K+ new listings daily
- Two-tier data offering: single-source (raw, normalized) vs. multi-source (deduplicated, enriched)
- Multi-source applies entity resolution to merge records referring to the same real-world entities across sources, even when messy/incomplete
- Enrichment includes company keywords, technologies used, funding data, recruiter profiles
- Available in Parquet, JSONL, CSV — structured for ML ingestion
- 24/7 discovery with active job posting tracking

### Alternative Data Ascendancy at the Fed
- During the shutdown, the Fed relied on ADP, Revelio Labs, and LinkUp data for labor market assessment
- Alternative sources showed "widespread and concerning slowdown" — job creation stalling, openings shrinking, layoffs rising
- This marks a structural shift: alternative data moved from supplementary to primary during the data gap

## 3. What I Think Is Interesting

**Three structural patterns emerge:**

**a) The Shift from Lagging to Leading Indicators**
Government labor statistics (BLS Employment Situation, JOLTS) are fundamentally lagging indicators — survey-based, revised multiple times, subject to collection disruptions. Job posting data is inherently leading: a job posting appears before a hire, and hiring intentions signal business confidence before it shows up in output metrics. The Indeed framework mapping GDP growth → unemployment → job postings is useful, but the real alpha is inverting this: using posting velocity as a predictor of GDP, not the other way around.

**b) Entity Resolution as the Economic Data Bottleneck**
Coresignal's multi-source deduplication is not just a data quality feature — it's the core economic signal extraction mechanism. A job posted on LinkedIn, Indeed, and a company career page is one economic signal, not three. Without entity resolution, you're double-counting economic activity. This is structurally identical to the problem in campaign finance/lobbying entity resolution (FEC ↔ LDA bridge), where the same entity appears across different datasets with different identifiers. The same Fellegi-Sunter probabilistic matching framework applies.

**c) The Epistemological Fragility of Alternative Data**
The Indeed Hiring Lab report is careful about scenario ranges (consensus/upside/downside) and transparent about methodology. But the broader alternative data ecosystem has a verification problem: Revelio Labs claims "close to the whole population of employed people" but uses public professional profiles — which systematically undercount certain sectors (agriculture, informal economy, service workers without LinkedIn). The BLS, for all its lag, has statistical rigor and representativeness guarantees. Alternative data providers have freshness but unknown sampling biases. The optimal architecture is fusion, not replacement.

## 4. What I'd Explore Next

1. **Nowcasting GDP from job posting velocity**: Build a simple model correlating Indeed/Revelio posting counts with subsequent BLS payroll numbers. Is the lead time 1 month? 3 months?
2. **Job posting data for entity resolution investigations**: A company posting for a sanctions compliance officer or a nuclear engineer reveals organizational capabilities not visible in corporate registries. This bridges Markets and OSINT investigation methodology.
3. **Sector-level signal extraction**: Healthcare job postings have been the "canary in the coal mine" for labor market tightness. Can sector-level posting anomalies predict sector ETF rotation?
4. **The Coresignal API as an Exocortex MCP tool**: 452M records with entity resolution pre-applied would be a powerful data source for company capability mapping and economic signal extraction.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Data Aggregation & Entity Resolution** | Coresignal's multi-source deduplication is the same Fellegi-Sunter problem as FEC/LDA entity resolution. Job posting ER is more tractable (company names are standardized, job titles are semi-structured) and could inform approaches to harder ER problems like beneficial ownership. |
| **OSINT & Investigation Methodology** | Job postings are public OSINT signals: a company posting for export-controlled technologies, or suddenly hiring in a new geography, reveals strategic intent. Job posting analysis is a legitimate OSINT collection discipline. |
| **AI Agent Architecture** | The alternative data fusion problem — combining BLS surveys (structured, slow, statistically rigorous) with job posting scrapes (unstructured, fast, sampling-biased) — is isomorphic to the Exocortex knowledge fusion problem: combining deterministic tools with LLM reasoning, each with different reliability profiles. |
| **Federal Reserve Operations** | The BLS data gap forced the Fed into an unplanned natural experiment: operating monetary policy on alternative data. The outcome of this experiment (did they make correct decisions?) will determine whether alternative data becomes institutionalized or retreats when BLS resumes. |
| **Bridging Local-to-Frontier Performance** | A local model running job posting analysis on-device enables privacy-preserving labor market research — no need to send company hiring data to third-party APIs. This connects to the RTX 3090 inference thread and the broader theme of sovereign analytical capability. |
| **History of Intelligence Operations** | The BLS data gap is structurally analogous to SIGINT outages: when a primary collection source goes dark, analysts must fall back on alternative sources with different reliability profiles. The resilience lesson is the same: never depend on a single source. |

---

**Sources:**
- Indeed Hiring Lab, "2026 US Jobs & Hiring Trends Report" (Nov 2025)
- Revelio Labs, "Introducing Revelio Public Labor Statistics (RPLS)" (2026)
- Coresignal, "Job Posting Data for Real-Time Insights" (2026)
- Advisor Perspectives, "Jobs Data From Alternative Sources May Drive Fed's Next Move" (Dec 2025)
- Deloitte Insights, "US Economic Forecast Q1 2026" (Mar 2026)
