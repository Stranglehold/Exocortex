# Job Posting Data as Alternative Economic Indicator

**Status:** STABLE
**Created:** 2026-06-05
**Last updated:** 2026-06-05 (BUILD cycle 393 — deepened with Osborn et al. arXiv 2510.23358, IMF nowcasting validation, Nature job vacancy forecasting, Coresignal methodology)
**Source Field Report:** [20260605_job-posting-alt-data-forecasting.md](../../field-reports/20260605_job-posting-alt-data-forecasting.md)

## Overview

Job posting data — scraped from company websites, job boards, and ATS platforms — has emerged as a real-time economic indicator that can substitute for or complement traditional lagging government labor market surveys. The 2025 federal government shutdown disrupted BLS data collection, forcing the Federal Reserve and private analysts to rely on alternative labor market signals. This event accelerated the institutionalization of job posting data as a legitimate economic indicator, but also exposed the epistemological challenges of blending high-frequency unstructured data with statistically rigorous survey-based measures.

## The BLS Data Gap Context

During the longest federal government shutdown in history, BLS data collection was disrupted. This created an unplanned natural experiment: operating monetary policy on alternative data. The outcome of this experiment will determine whether alternative data becomes permanently institutionalized or retreats when BLS resumes normal operations.

**Structural pattern:** The BLS gap is isomorphic to SIGINT outages in intelligence analysis — when a primary collection source goes dark, analysts must fall back on alternative sources with different (and often unknown) reliability profiles. The resilience lesson is the same: never depend on a single source.

## Key Players & Data Sources

### Indeed Hiring Lab
- Publicly available GitHub repository: `hiring-lab/job_postings_tracker` (CC BY 4.0 license)
- Tracks daily percentage changes in seasonally adjusted job postings relative to February 1, 2020 baseline
- Uses Deutsche Bundesbank's daily time-series seasonal adjustment method
- Covers 55 occupational sectors at national, sectoral, and regional levels; historical data through October 10, 2025
- Uses Blue Chip consensus (45 economists) GDP projections mapped to unemployment and job openings via historical relationships
- **Consensus forecast:** 1.8% GDP growth → 4.1-4.8% unemployment, 6.8-7.4M job postings at YE 2026
- Key structural finding: regional dynamics now matter as much as national trends — "where you live and what you do will matter at least as much as top-line national trends"
- Identified a "low-hire environment" where postings stabilize but hiring doesn't grow; mismatch between available skills and available jobs
- Immigration policy tightening is structurally tightening labor supply in construction, hospitality, engineering, and medicine

### Revelio Labs — RPLS (Revelio Public Labor Statistics)
- **Launched:** September 4, 2025, via PRNewswire
- **Data sources:** 100+ million professional profiles, job postings, employee sentiment reviews — representing close to the whole population of employed people in the United States
- **Coverage:** 19 million companies, 1.1 billion professional profiles, 5.25 million firms
- **Release schedule:** Monthly, released the day before BLS "Jobs Friday" — designed to complement BLS with more timely and granular insights
- **Inaugural data:** August 2025 showed gains in employment of 50,000; salaries from new job postings increased 0.6% month-over-month
- Available via WRDS (Wharton Research Data Services) for academic access

### Coresignal
- **Dataset:** 452M+ records of multi-source job postings with entity resolution applied across >80 data fields
- **Sources:** Job boards, company websites, ATS platforms; 24/7 discovery with active job posting tracking
- **Data processing levels:**
  1. **Base (single-source):** Standardized, normalized scraped data from one source
  2. **Enhanced (multi-source):** Entity resolution across sources — deduplication and record merging
- **Job information fields:** Description, employment type, applicant count, functions, department, management level, decision-maker status
- **Location fields:** Country, city, state, company headquarters
- **Salary fields:** Salary type (multiple if applicable), salary range, currency
- **Company information:** Main company details, locations, funding rounds, technologies used, company keywords
- **Recruiter information:** Profile URL, first/last name
- **Metadata:** Job status, source information, creation/update dates, unique source links
- **Entity resolution:** Applies record linkage across disparate sources — identifies and merges records referring to the same real-world entity even when fields are messy, incomplete, or slightly different. Approach follows Fellegi-Sunter probabilistic record linkage principles, matching on company name + location + postal code + job title features.

### Alternative Data Ecosystem
- **LinkUp:** Jobs data from company websites only (no duplicates)
- **Burning Glass / Lightcast:** Legacy labor market analytics with longer historical coverage
- **Textkernel:** European job market data focus

## Academic Validation & LLM-Based Forecasting

### Osborn et al. (2025): "How AI Forecasts AI Jobs: Benchmarking LLM Predictions of Labor Market Changes"

**arXiv 2510.23358** — A benchmark using Indeed Hiring Lab Job Postings Index and WEF Future of Jobs Report to evaluate LLM labor market forecasting.

**Data used:**
- **Indeed:** Daily job posting counts (55 sectors) aggregated to quarterly and annual series; 1,100 quarterly data points; post-2023 test period ensures no training data leakage
- **WEF:** 10 AI-related occupation sectors, 8 years annual data (80 data points); some risk of training-cutoff overlap in long-horizon setting

**Models tested:** GPT-4o-mini, LLaMA-3.1-70B, LLaMA-3.1-8B

**Prompting strategies:**
1. **Direct forecasting** — Continue historical numeric sequence without additional reasoning
2. **Relative (multiplier) forecasting** — Output period multipliers scaling previous value (e.g., 1.05 = +5%)
3. **Event reasoning** — Model identifies relevant events/shocks before generating numeric forecasts

**Key findings:**
- Structured task prompts consistently improve forecast stability; multiplier prompts often introduce catastrophic variance (LLaMA-8B: MSE > 10^10 in some cases)
- GPT-4o-mini most reliable overall — Indeed annual direct: avg MSE 821.20, event-reasoning: 736.13
- For short-horizon forecasts, simple moving average baseline still competitive (Indeed long: MA MSE 525.60 vs best LLM 1205.93; WEF Short: MA 2572.02 vs LLM ~1600-1900)
- Event reasoning aids long-horizon WEF forecasts (GPT-4o-mini event-reasoning: avg MSE 889.21)

**Persona analysis (7 distinct expert personas tested with direct forecasting):**

| Persona | Indeed Annual (Avg MSE) | Indeed Long (Avg MSE) | WEF Short (Avg MSE) | WEF Long (Avg MSE) |
|---------|------------------------|---------------------|--------------------|--------------------|
| HR Manager | **951.49** | **1579.40** | 2294.90 | 1032.64 |
| Unified Researcher | 1280.04 | 1334.97 | **1495.80** | **691.51** |
| Economics Researcher | 1435.06 | 2040.04 | 2293.01 | 1043.92 |
| Industry Researcher | 1271.54 | 1990.78 | 1877.41 | 857.58 |
| AI Specialist | 1636.28 | 2252.81 | 1685.80 | 761.57 |
| AI Researcher | 1601.79 | 2796.52 | 1922.08 | 877.80 |
| Policy Researcher | 1469.79 | 2422.03 | 7986.64 | 3614.90 |

**Critical persona findings:**
- Grounded, human-centered personas (HR Manager, Industry Researcher) consistently outperform speculative, policy-oriented personas
- Policy Researcher produces highest variance across all settings — policy-focused reasoning overemphasizes uncertainty
- Combined personas (Unified + Economics, Unified + Industry) can improve stability but never outperform the most general persona (Unified Researcher) used alone
- Persona framing matters more than model scale: GPT-4o-mini with good persona outperforms LLaMA-70B with poor persona

**Implications for job posting data analysis:**
- LLMs can reason over job posting time series when structured appropriately
- The model's epistemic framing (persona + prompt structure) drives stability more than parameter count
- Short-horizon forecasts remain dominated by statistical baselines; LLMs add value primarily through event integration and causal reasoning on longer horizons
- Data leakage is a real problem — forecasts overlapping with training data inflate apparent performance

## Economic Nowcasting Validation

### IMF Working Paper (Dec 2025): "GDP Nowcasting Performance of Traditional Econometric Models vs Machine Learning"
- Evaluated all models ever used in nowcasting across simulation and six country cases
- **Finding:** Traditional econometric models tend to outperform ML algorithms; among ML, linear algorithms (Lasso, Elastic Net) perform best
- This suggests that complex LLM-based forecasting of job postings needs rigorous benchmarking against linear baselines, not just moving averages

### Nature Humanities & Social Sciences Communications (May 2026): "Forecasting job vacancies in Hong Kong using AI time series models"
- Demonstrates AI-based forecasting models conditioned on high-frequency alternative data including online job postings
- Validates the practical deployment path: job posting data → time-series feature engineering → AI forecasting

### FRED/ALFRED (St. Louis Fed): Nowcasting US GDP Data List
- Published 34-series data list for GDP nowcasting; practitioners combine job posting data with other high-frequency indicators (credit card spend, satellite imagery, shipping data)

## Entity Resolution Methodology

Coresignal's 452M-record job posting dataset applies entity resolution to merge multi-source records:

**Problem:** A single job posting may appear on LinkedIn, Indeed, Glassdoor, and the company's own ATS with variations in title, description formatting, location granularity, and timestamps.

**Approach:**
- **Blocking:** Company name + location (city/state) + approximate date window as blocking keys to reduce pairwise comparisons
- **Probabilistic matching:** Field-level comparison weights derived from empirical m-probability (probability field matches for true match) and u-probability (probability field matches by chance) — classic Fellegi-Sunter formulation
- **Record merging:** Once records are linked, the most complete fields are selected from across sources
- **Result:** Deduplicated, enriched records with source provenance preserved

**Comparison to other ER domains:**
- Job posting ER is structurally simpler than beneficial ownership ER (company names are standardized; job titles have limited vocabulary) but harder than street-address matching (temporal dynamism, rapid posting/churn)
- Coresignal's production pipeline likely draws on open-source frameworks (Splink, dedupe, Zingg) or related architectures — the scale (452M records) demands blocking optimizations and incremental deduplication

## Methodological Limitations & Epistemological Caveats

### Sampling bias
- Job posting data reflects hiring demand, not actual employment — a company may post without hiring (ghost jobs, pipeline building)
- Coverage bias toward white-collar, tech, and professional occupations; underrepresents manual labor, agriculture, and informal economy
- Platform coverage varies by geography (Indeed dominates US; StepStone in EU; Zhaopin in China)

### Statistical vs. scraped data
- BLS has known methodology, sampling frame, and error bars; job posting data has unknown sampling bias and platform-specific coverage gaps
- Seasonal adjustment methods differ across providers — Indeed uses Bundesbank method; Coresignal and Revelio likely use proprietary methods
- The epistemological shift from survey to scraped data mirrors intelligence community debates about replacing HUMINT with SIGINT — timeliness improves, but reliability assessments become more complex

### Nowcasting reliability
- IMF findings suggest linear/elastic net models often outperform complex ML for nowcasting — LLM-based forecasting has yet to prove superiority over simpler baselines
- Osborn et al. benchmark shows moving average competitive for short horizons; LLM advantage emerges primarily through event reasoning on extended horizons
- No consensus yet on optimal nowcasting horizon for job posting signals relative to GDP

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[data-aggregation-entity-resolution]] | Coresignal's 452M-record multi-source deduplication uses Fellegi-Sunter at scale; job posting ER is structurally simpler than beneficial ownership ER and can inform approaches to harder entity resolution problems. |
| [[human-investigation-osint]] | Job postings are public OSINT signals revealing organizational capabilities, strategic intent, and regulatory exposure — a legitimate OSINT collection discipline. |
| [[ai-agent-architecture-local-inference]] | The alternative data fusion problem (combining BLS surveys with scraped postings, each with different reliability profiles) is isomorphic to Exocortex knowledge fusion: combining deterministic tools with LLM reasoning. |
| [[federal-reserve-operations]] | The BLS data gap forced the Fed into an unplanned natural experiment: operating monetary policy on alternative data. The outcome determines whether alternative data becomes institutionally permanent. |
| [[bridging-local-frontier-model-performance]] | A local model running job posting analysis on-device enables privacy-preserving labor market research — no need to send company hiring data to third-party APIs. Osborn et al. benchmark provides methodology for evaluating local LLM forecasting performance. |
| [[history-of-intelligence-operations]] | The BLS data gap is structurally analogous to SIGINT outages: when a primary collection source goes dark, analysts must fall back on alternative sources with different reliability profiles. The resilience lesson is the same: never depend on a single source. |
| [[alternative-data-sources]] | Job posting data is a canonical alternative data source alongside satellite imagery, credit card transactions, and web traffic analytics. |
| [[quantitative-market-analysis-statistical-arbitrage]] | Nowcasting GDP from job posting velocity; sector-level posting anomalies as leading signals for sector ETF rotation. Osborn et al. persona analysis suggests HR perspective yields better short-term forecasts than economic-policy perspective. |
| [[open-source-entity-resolution-frameworks]] | Coresignal's production pipeline likely draws on Splink/dedupe/Zingg architectures; the job posting ER problem (with temporal dynamism) is a valuable benchmark for evaluating these frameworks. |
| [[intelligence-failure-analysis]] | The epistemological shift toward alternative data mirrors intelligence community debates about replacing HUMINT with SIGINT — similar structural pattern of reliability vs timeliness tradeoffs. Prompt persona analysis demonstrates that epistemic framing of source reliability matters. |
| [[academic-research-methodology]] | Osborn et al. benchmark provides a rigorous methodology for evaluating LLM forecasting with proper temporal splits, leakage controls, and persona ablation — replicable experimental design for any alternative data forecasting task. |
| [[privacy-cryptography]] | Job posting analysis run on local models avoids sending company hiring data to cloud APIs, connecting to the sovereign analytical capability thread and homomorphic encryption research for privacy-preserving data fusion. |

## References

1. Indeed Hiring Lab, "2026 US Jobs & Hiring Trends Report" (Nov 2025) — [GitHub: hiring-lab/job_postings_tracker](https://github.com/hiring-lab/job_postings_tracker)
2. Revelio Labs, "Revelio Labs Launches Revelio Public Labor Statistics (RPLS) with Debut Headline Findings" PRNewswire (Sept 4, 2025)
3. Revelio Labs, "Introducing Revelio Public Labor Statistics (RPLS)" LinkedIn / Ben Zweig (2025)
4. Integrity Research, "Revelio Labs Unveils RPLS: A Bold Alternative to BLS in Turbulent Times" (2025)
5. Coresignal, "Job Posting Data for Real-Time Insights — 452M Records" (2026) — [coresignal.com/alternative-data/job-postings-data/](https://coresignal.com/alternative-data/job-postings-data/)
6. Advisor Perspectives, "Jobs Data From Alternative Sources May Drive Fed's Next Move" (Dec 2025)
7. Deloitte Insights, "US Economic Forecast Q1 2026" (Mar 2026)
8. WRDS (Wharton Research Data Services), "NEW Revelio Labs Data" (2025)
9. **Osborn, S., Valecha, R., Rao, H.R., Sass, D.A., Rios, A.** (2025). "How AI Forecasts AI Jobs: Benchmarking LLM Predictions of Labor Market Changes." arXiv:2510.23358. — Introduces benchmark combining Indeed Job Postings Index and WEF Future of Jobs data to evaluate LLM labor market forecasting with systematic persona and prompt ablation.
10. **IMF Working Paper** (Dec 2025). "GDP Nowcasting Performance of Traditional Econometric Models vs. Machine Learning." — Traditional models often outperform ML; linear ML (Lasso, Elastic Net) best among ML.
11. **Nature Humanities & Social Sciences Communications** (May 20, 2026). "Forecasting job vacancies in Hong Kong using AI time series models." — Validates AI models conditioning on high-frequency job posting data.
12. FRED/ALFRED (St. Louis Fed). "Nowcasting US GDP" Data List (updated 2024). — Published data list for GDP nowcasting combining multiple high-frequency indicators.
13. BLS Employment Situation Summary, May 2026 Results.
14. U.S. Bank, "Job Market's Effect on the Economy" (2026).

---
*Page originally created by BUILD cycle 387. Deepened in BUILD cycle 393 with academic validation from Osborn et al. arXiv 2510.23358, IMF nowcasting comparison, Nature journal validation, and Coresignal methodology specifics. Primary new additions: LLM forecasting benchmark section, persona ablation analysis, nowcasting validation, entity resolution methodology details, and methodological limitations.*
