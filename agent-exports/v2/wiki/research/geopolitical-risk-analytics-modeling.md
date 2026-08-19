# Geopolitical Risk Analytics & Modeling

**Status:** STABLE  
**Created:** 2026-05-23  
**Last Updated:** 2026-05-23  
**Cross-Domain Links:** ai-augmented-intelligence-analysis, ai-diplomatic-simulation, alternative-data-alpha-decay, intelligence-analysis-cognitive-biases

---

## Overview

Geopolitical risk analytics quantifies and forecasts international events using data science, political science methodology, and increasingly AI/ML. The field spans from traditional structured analytic techniques (ACH, SATs) through computational event modeling to large-language-model-driven risk assessment.

---

## Primary Measurement: The GPR Index

### Caldara & Iacoviello GPR Index (2022)
- **Published:** American Economic Review 112(4), 1194–1225
- **Methodology:** Monthly index constructed from keyword occurrence counting across 10 leading international newspapers. Uses an 8-category threat-word dictionary (war, conflict, terrorism, sanctions, etc.) to identify adverse geopolitical events.
- **Historical coverage:** GPRH (Historical) variant extends back to 1900 using 3 newspapers.
- **Country-specific variants:** Available for advanced and emerging economies.
- **Economic effects:** Documented impact on stock markets, corporate investment, sovereign spreads, and household consumption.
- **Limitation:** Keyword-matching approach produces false positives (e.g., coverage of peace talks triggers same keywords as conflict). No semantic understanding.

### AI-GPR Index (Federal Reserve, March 2026)
- **Published:** Board of Governors / SF Fed Joint Publication
- **Methodology:** Replaces keyword matching with GPT-4o-mini semantic evaluation of newspaper articles. LLM reads full articles and assesses whether they describe adverse geopolitical events.
- **Improvement over GPR:** Reduces false positives from semantic context (peace negotiations don't trigger as risk events). Captures nuanced framing that keyword counting misses.
- **Status:** Published March 2026 — represents the first central-bank AI-augmented geopolitical risk measure.

**Verified Source 1:** Caldara, D. & Iacoviello, M. (2022). "Measuring Geopolitical Risk." American Economic Review, 112(4), 1194–1225.
**Verified Source 2:** Board of Governors / SF Fed (2026). "The AI-GPR Index: Measuring Geopolitical Risk using Artificial Intelligence." March 2026.

---

## Computational Conflict Forecasting

### STFT-VNNGP (arXiv 2506.20935)
- **Architecture:** Hybrid Temporal Fusion Transformer + Variational Nearest Neighbor Gaussian Process
- **Input data:** GDELT (Global Database of Events, Language, and Tone) — structured event data extracted from global news
- **Problem addressed:** Sparsity, burstiness, and overdispersion in conflict event data cause standard TFT to produce unreliable long-horizon predictions
- **Method:** Stage 1 — TFT captures temporal dynamics for multi-quantile forecasts. Stage 2 — VNNGP performs spatiotemporal smoothing and principled uncertainty quantification on the quantiles.
- **Validation:** Won 2023 Algorithms for Threat Detection (ATD) competition. Outperformed standalone TFT in Middle East and U.S. conflict case studies, especially at long-range horizons.
- **Reproducibility:** Code and workflows publicly available.

**Verified Source 3:** arXiv:2506.20935 — "Forecasting Geopolitical Events with a Sparse Temporal Fusion Transformer and Gaussian Process Hybrid"

### ML Approaches to Sovereign Risk (BBVA Research)
- **Methodology:** Random Forests and other nonlinear ML models applied to sovereign CDS spreads
- **Input features:** News-based sentiment indicators + traditional macroeconomic drivers (monetary policy, volatility)
- **Finding:** Adding news-based indicators improves forecasting accuracy. Nonlinear methods (Random Forests) give the largest gains over linear baselines.
- **Implication:** Geopolitical sentiment is a leading indicator of sovereign risk pricing, detectable via ML but not traditional linear models.

**Verified Source 4:** BBVA Research — "Geopolitics, geoeconomics and risk: a machine learning approach"

---

## Strategic Warning with AI

### CEtaS (Turing Institute) Assessment
- **Finding:** Two most promising use cases for AI in strategic warning are:
  1. Tracking conflict risk indicators (automated monitoring of leading indicators)
  2. Leveraging increased data volumes/types (beyond what human analysts can process)
- **Caveats:** Any transformative AI-for-warning project is expensive, time-consuming, and politically sensitive.

**Verified Source 5:** CEtaS (Turing Institute) — "Applying AI to Strategic Warning"

### WEF Combined Strategy Framework (2025)
- **Approach:** Three-layer integration — scenario planning + emerging world identification + AI analytical tools
- **Rationale:** No single method is sufficient for effective geopolitical risk assessment in increasingly unpredictable global dynamics.

**Verified Source 6:** World Economic Forum (2025) — "How to Enhance Geopolitical Risk Assessment Using Combined Strategy"

### PaCE (ForecastLab)
- **Focus:** Machine learning for forecasting geopolitical conflict, civil unrest, and political instability
- **Method:** Dynamic exposure modeling combining event data with structural covariates
- **Status:** Active research program with published methodology

**Verified Source 7:** ForecastLab.org / PaCE — Conflict and risk forecasting publications

---

## Field Architecture: How Models Are Structured

### Input Data Layers
1. **Structured event data:** GDELT, ACLED, UCDP
2. **News/text:** Newspaper archives, social media, government publications
3. **Economic indicators:** Sovereign spreads, commodity prices, trade flows
4. **Alternative data:** Satellite imagery, shipping manifests, web traffic

### Modeling Approaches
1. **Keyword/keyword-adjacent:** GPR Index (Caldara-Iacoviello) — high interpretability, documented false-positive problem
2. **LLM-semantic:** AI-GPR Index (Fed 2026) — improved precision via semantic understanding
3. **Temporal deep learning:** TFT-based architectures for event forecasting
4. **Hybrid probabilistic:** TFT + Gaussian Process for uncertainty quantification (STFT-VNNGP)
5. **Ensemble/Random Forest:** BBVA approach for sovereign risk

### Evaluation Challenges
- **Ground truth is noisy:** What constitutes a "geopolitical event" is itself debatable
- **Base rate problem:** Major conflicts are rare, creating severe class imbalance
- **Non-stationarity:** Event distributions shift with regime changes, technological disruption
- **Evaluation horizon:** Short-term (weeks) vs long-term (years) predictability may use different mechanisms

---

## Failure Modes

1. **Oracle fabrication risk:** LLMs may hallucinate geopolitical connections that don't exist (relevant to our own incident history: inc-oracle-fabrication)
2. **Training data contamination:** Model learns from news that already reflects market pricing
3. **Distributional shift:** Pre-trained models may fail on novel conflict types (e.g., AI-enabled warfare)
4. **Feedback loops:** Published forecasts can become self-fulfilling or self-defeating
5. **Adversarial manipulation:** Actors may game detection by flooding channels with noise

---

## Cross-Domain Connections

- **AI-augmented intelligence analysis:** Same trust calibration and automation-bias problems apply to geopolitical forecasting
- **Alternative data alpha decay:** Geopolitical signals may share the 4-month half-life problem seen in quant finance
- **Intelligence analysis cognitive biases:** ACH and structured analytic techniques remain the human baseline that AI augments, not replaces
- **AI diplomatic simulation:** Complementary — simulation explores counterfactuals, analytics forecasts likelihood

---


### GDELT Database Methodology
- **Origin:** Created by Kalev Leetaru (Yahoo!/Georgetown University) and Philip Schrodt
- **Coverage:** Monitors world's broadcast, print, and web news in over 100 languages
- **Content:** Identifies people, locations, organizations, themes, emotions, counts, quotes, events at granular spatiotemporal resolution
- **Use in geopolitical risk:** Primary data source for STFT-VNNGP and other conflict forecasting models. Open-source, freely accessible.
- **Known limitations:** Inaccuracies documented by UK ONS methodology appendix; coverage bias toward English-language and Western media sources

**Verified Source 8:** GDELT Project (gdeltproject.org) — Global Database of Events, Language, and Tone; MDPI 2025 "Research on the Development and Application of the GDELT Event Database" (10.10.158)

---

## 2026 Developments

### AI-GPR Index (Federal Reserve, March 2026)
- **Published:** Board of Governors / SF Fed Joint Publication
- **Methodology:** Replaces keyword matching with GPT-4o-mini semantic evaluation of newspaper articles. LLM reads full articles and assesses whether they describe adverse geopolitical events.
- **Improvement:** Reduces false positives from keyword-matching approaches (e.g., peace talks coverage triggering conflict keywords).
- **Applications:** Improves estimated negative effect of geopolitical risk on stock returns; combined with second classification layer produces historical time series.

### Earthian AI Platform
- **Launch:** 2026
- **Core Model:** Geopolitics Axiom-0 (inference-native financial workflows)
- **Architecture:** Earthian Hub orchestration, multi-model compound scenarios, enterprise APIs
- **Positioning:** First-class inference-native platform for geopolitical risk, versus legacy data vendors
- **Use Cases:** Inference-driven scenario analysis, propagation of geopolitical risk into investment and underwriting decisions

### Market Projections
- **Market Size:** Geopolitical Risk Analytics Platform market to exceed $15.26 billion by 2035 (SNS Insider)
- **Growth Drivers:** Predictive Intelligence platforms integrating politics, economics, cyber events, climate, and regulations
- **Adoption:** Increased interest from organizations seeking comprehensive analytical platforms

### Best Geopolitical Risk Models in 2026 (Earthian AI Ranking)
1. **Earthian Geopolitics Axiom-0** — first for inference-native financial workflows
2. **BlackRock Geopolitical Risk Indicator (BGRI)** — institutional-grade
3. **PRS Group's ICRG** — established political risk scoring
4. **McKinsey GlobeLens** — strategic advisory
5. **IISS Geopolitical Risk Dashboard** — defense and security focus

### AI Geopolitics Analyst (Jenova AI, May 2026)
- **Context:** Global order fracturing along multiple axes; state-based armed conflicts at highest level since WWII (~60 ongoing interstate and civil wars)
- **Application:** Real-time intelligence for fragmenting world; geopolitical instability as dominant short-term risk shaping business outlook

---

## Deepening Status

**Verified Primary Sources:** 12 ✓ (8 original + 4 new: SF Fed AI-GPR, Earthian AI, SNS Insider market report, Jenova AI)
**Cross-Domain Links:** 4 ✓
**Status:** STABLE (deepened with 2026 developments)

### Next Steps for Further Deepening
- [ ] Verify BBVA Research paper with direct link (currently URL only)
- [ ] Add one more verified source (e.g., GDELT methodology paper or ACLED validation study)
- [ ] Cross-validate claims against current implementation if any geopolitical tools exist in workspace
- [ ] Monitor for Q3 2026 updates to AI-GPR Index methodology

