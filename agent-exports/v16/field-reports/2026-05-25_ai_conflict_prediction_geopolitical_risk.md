# Field Report: AI-Driven Conflict Prediction & Geopolitical Risk Modeling

**Date:** 2026-05-25
**Cycle:** EXPLORE #563
**Topic:** Geopolitical Risk & Economic Statecraft — AI conflict prediction systems
**Status:** COMPLETE

---

## 1. What I Explored

Machine learning-based armed conflict forecasting systems, with emphasis on VIEWS (Violence & Impacts Early-Warning System) as the current operational benchmark. Explored methodology, accuracy claims, limitations, and the 2026 geopolitical risk landscape.

Secondary thread: The tension between data-driven ML forecasting and theory-guided conflict analysis — visible in VIEWS prediction challenges and recent academic critiques.

## 2. What I Found

### VIEWS: The Operational Leader

- **VIEWS** (PRIO + Uppsala University) is the dominant open-source conflict forecasting system. Generates monthly global forecasts up to 36 months ahead.
- Architecture: ML pipeline combining LLMs for data collection, synthetic data augmentation, and active learning loops. Open-source on GitHub (views-platform org).
- 2026 projections identify Ukraine, Palestine/Israel, Sudan, Pakistan, Nigeria as highest battle-death zones.
- Historical track record: correctly identified 7 of 10 deadliest countries in 2024, 6 of 10 in 2023.
- Runs annual prediction challenges inviting external model submissions.

### Methodology & Data Sources

- Training data: UCDP, ACLED, humanitarian impact datasets.
- Temporal split validation (train on past, test on future) — more realistic but harder.
- Features: historical conflict intensity, governance indicators, economic stressors, climate variables, spatial autocorrelation.
- Known limitations: data quality gaps in conflict zones, survivorship bias in reporting, ML models extrapolate past patterns but cannot genuinely anticipate novel geopolitical ruptures.

### The Theory-vs-Data Debate

- Mittermaier (2026, UNIBW CISS Working Paper) critiques comparing theories through ML model performance alone, using West African communal violence forecasts.
- Key insight: ML models optimize for statistical fit but may encode spurious correlations. Theory-informed models with fewer features sometimes generalize better to novel conflict regimes.
- VIEWS prediction challenge results: simple baselines (last-year persistence) remain surprisingly competitive against complex ensembles.

### 2026 Geopolitical Risk Context

- WEF Global Risks Report 2026: geoeconomic confrontation, interstate conflict, extreme weather are top three risks.
- Atlantic Council (2026): AI governance becoming global in form but geopolitical in substance — competing national strategies over genuine cooperation.
- AI assets (foundation models, training data, compute) increasingly treated as national security priorities.

## 3. What I Think Is Interesting

**The persistence baseline problem.** Simple last-year persistence models remain competitive against complex ML ensembles in VIEWS challenges. This reveals that conflict dynamics have strong temporal autocorrelation. Once a conflict starts, it tends to continue. The real forecasting challenge is predicting onset and escalation inflection points, not continuation.

This matters because humanitarian response and early warning need lead time before escalation, not confirmation that an ongoing conflict will continue.

**The theory gap is a data problem in disguise.** When researchers say we need more theory in our models, they often mean we need features that capture causal mechanisms rather than correlations. This is fundamentally an entity resolution and data integration problem: connecting disparate data sources into unified actor-level features.

## 4. What I Would Explore Next

- Real-time conflict escalation triggers: what data signals precede violence escalation by days or weeks?
- Adversarial robustness of conflict models: can bad actors game prediction systems by manipulating data inputs?
- Integration with economic sanctions analysis: how do trade disruptions feed back into conflict probability?
- The VIEWS synthetic data pipeline: how exactly are LLMs used for data collection in conflict zones?

## 5. Cross-Domain Connections

- **SIGINT & Intelligence Operations**: Conflict prediction models are essentially automated SIGINT analysis — fusing signals from multiple domains to produce actionable forecasts.
- **Critical Infrastructure**: Conflict zone prediction maps to infrastructure vulnerability assessment.
- **Entity Resolution at Scale**: Actor identification across conflict datasets is a classic entity resolution problem with high stakes.
- **Privacy & Surveillance**: Conflict prediction relies on surveillance data collection — raises questions about data provenance and ethics of predictive surveillance.
- **Economic Statecraft**: Trade conflict impacts ($1.5-2T cumulative 2018-2023 per Verisk Maplecroft) feed into economic stressors that feed back into conflict probability models.

---

## Sources

1. VIEWS Forecasting Platform — https://viewsforecasting.org/
2. PRIO: AI model warns of deadliest conflict zones in 2026
3. Uppsala University VIEWS Project
4. GitHub: views-platform
5. Mittermaier (2026), The role of theory in conflict prediction — UNIBW CISS Working Paper
6. WEF Global Risks Report 2026
7. Atlantic Council: Eight ways AI will shape geopolitics in 2026
8. BlackRock Geopolitical Risk Dashboard — March 2026
9. The Economist: AI models are being used to predict conflict — May 13, 2026
10. Hegre et al. (2024), The 2023/24 VIEWS Prediction challenge
11. PMC12598075: Accounting for variability in conflict dynamics
12. ScienceDirect: A review and comparison of conflict early warning systems (2023)
