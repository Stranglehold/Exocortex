# Field Report: Earnings Surprise Modeling

**Date:** 2026-06-01 17:37 EDT
**Cycle Type:** EXPLORE
**Interest Category:** Markets & Financial Analysis
**Specific Thread:** Earnings surprise modeling via machine learning and LLMs

---

## 1. What I Explored

I researched the state of the art in predicting corporate earnings surprises — the difference between reported earnings and analyst consensus expectations. Earnings surprises drive significant post-announcement stock price drift (PEAD), making prediction a directly monetizable quantitative finance problem.

I followed two primary threads: (1) a new 2025 multimodal benchmark dataset for LLM-based earnings surprise prediction, and (2) a revived PEAD strategy using elastic net machine learning on historical earnings lags. I also contextualized these against alternative data sources listed in Jake's interests (satellite imagery, web traffic, patent filing velocity).

## 2. What I Found

### FinCall-Surprise: Multimodal LLM Benchmark

**Paper:** Dong Shu, Yanguang Liu, Huopu Zhang, Mengnan Du (2025) "FinCall-Surprise: A Large Scale Multi-modal Benchmark for Earning Surprise Prediction" (arXiv 2510.03965)

The authors introduce the first large-scale, open-source, multimodal dataset for earnings surprise prediction: 2,688 unique corporate conference calls from 2019-2021, with word-for-word transcripts, full audio recordings, and presentation slides. They benchmark 26 state-of-the-art unimodal and multimodal LLMs.

**Key findings:**
- Many models achieve apparently high accuracy, but this is an *illusion* caused by severe class imbalance in real-world earnings surprise data. High accuracy is simply predicting the majority class.
- Specialized financial LLMs show unexpected weaknesses in instruction-following and language generation — they underperform general-purpose models on structured prediction tasks.
- Incorporating audio and visual modalities provides only marginal performance gains. Current multimodal models cannot effectively leverage acoustic cues (tone, hesitation) or visual cues (slide emphasis) from earnings calls.

**Interpretation:** This is a sobering result. After years of hype about LLMs in finance, a rigorous benchmark reveals that LLM financial reasoning is still deeply unreliable. The class imbalance problem is the same one that plagues fraud detection and anomaly detection — accuracy is the wrong metric, and financial data is inherently imbalanced.

### PEAD Revival via Elastic Net on Historical Earnings

**Paper:** Tomasz Kaczmarek & Adam Zaremba (2025) "Beyond the last surprise: Reviving PEAD with machine learning and historical earnings," Finance Research Letters, 86(PE).

The authors challenge the standard PEAD approach that only considers the most recent earnings surprise. Using elastic net regularization — a machine learning method that selects and regularizes multiple lags — they extract predictive signals from many quarters of Standardized Unexpected Earnings (SUE) history.

**Key findings:**
- Incorporating historical earnings lags nearly *doubles* Sharpe ratios compared to single-quarter models.
- Alphas remain statistically significant even after controlling for one-quarter SUE and streak effects (consecutive beats/misses).
- The strategy works best in large-cap stocks where the latest surprise is quickly priced in, but older patterns remain overlooked by the market.
- The traditional PEAD anomaly had weakened in recent years; this approach effectively revives it by finding subtler multi-quarter signals.

**Interpretation:** This paper demonstrates a principle that generalizes beyond earnings surprise prediction: when the market adapts to a simple anomaly, look for richer historical patterns using regularized machine learning. It is a template for anomaly revival — identify which signals get priced in quickly vs. slowly, and harvest the overlooked ones.

### Alternative Data Frontier

Neither paper integrated alternative data sources (satellite imagery, web traffic, job postings, patent velocity) into earnings prediction. The interests.md identifies these as exploration threads. Current state: alternative data is used primarily by hedge funds for revenue estimation (e.g., satellite parking lot counts for retail, credit card transactions for consumer), but systematic integration with earnings surprise prediction remains an open research problem. The gap: multimodal financial LLMs like FinCall-Surprise's benchmark only look at conference call data, not the broader data exhaust a company generates.

## 3. What I Think Is Interesting

### The Class Imbalance Deception Problem

FinCall-Surprise's finding that high accuracy is illusory due to class imbalance is directly relevant to Exocortex design. Our injection gate, epistemic integrity layer, and BST classifier all face the same challenge: in high-stakes autonomous agent operation, "normal behavior" is the overwhelming majority class, and anomalies are rare. A classifier that says "normal" all the time achieves high accuracy but is useless. FinCall-Surprise is a cautionary tale: always check your prior. If a model's performance seems too good, check the class distribution.

### Anomaly Revival as a Pattern Template

Kaczmarek & Zaremba's PEAD revival via elastic net is structurally isomorphic to how we might revive detection of agent failure modes in Exocortex. If a failure mode becomes "priced in" (i.e., the system adapts and stops flagging it), rich historical context (multi-step tool call sequences, not just the last error) can reveal subtle recurrence patterns. This is the same principle in a different domain: when simple signals stop working, use regularized multi-lag models.

### The Hallucination-Accuracy Paradox

LLMs can produce high nominal accuracy on class-imbalanced tasks while failing at the actual reasoning. This perfectly mirrors the oracle fabrication problem we've observed in Exocortex: the agent appears confident and numerically "accurate" but the underlying reasoning is fabricated. FinCall-Surprise provides an academic benchmark that formalizes this failure mode.

## 4. What I'd Explore Next

1. **Alternative data integration benchmark:** Create a systematic comparison of earnings surprise prediction using only conference call data vs. conference call data + alternative data (satellite, web traffic, job postings). Does alternative data add signal beyond what's in the earnings call?

2. **Alternative data for energy/utility companies:** Map the alternative data sources from interests.md specifically to electric utility companies — satellite imagery of power plant construction, interconnection queue filings, regulatory proceeding dockets. This bridges Markets and Electric Utility interests.

3. **Anomaly revival applied to Exocortex:** Formalize the Kaczmarek-Zaremba pattern (regularized historical lags → anomaly revival) as an Exocortex design principle for the epistemic integrity layer: when a failure detection signal weakens, expand the lag window before abandoning the signal.

4. **Class imbalance deception in agent evaluation:** Adapt FinCall-Surprise's methodology to evaluate agent benchmarks — are high-accuracy agent evaluations just picking up class imbalance?

## 5. Cross-Domain Connections

- **Entity Resolution:** Earnings surprise prediction aggregates data across companies, requiring entity resolution to link financial filings (EDGAR CIK codes) to stock tickers to alternative data sources (satellite coordinates, web domains). A production system would need a robust entity resolution pipeline.
- **OSINT Methodology:** Alternative data collection for earnings prediction (satellite imagery analysis, web scraping, social media sentiment) is structurally identical to OSINT techniques. The hedge fund satellite analyst and the Bellingcat geolocation investigator use the same raw skills.
- **Privacy & Cryptography:** Earnings data access is regulated under insider trading laws, and alternative data raises privacy concerns (e.g., credit card transaction data, location data from mobile phones). The tension between signal and privacy is a rich exploration thread.
- **AI Agent Architecture:** FinCall-Surprise's finding that LLMs struggle with financial reasoning despite apparent accuracy is a cautionary tale for our own agent evaluation. If we only measure task completion rate, we might miss deep reasoning failures.
- **Geopolitics:** Earnings surprises are not just market events — sanctions policy impacts earnings of targeted companies and their supply chains. Predicting earnings surprises for rare earth companies, defense contractors, or semiconductor firms requires understanding the geopolitical landscape.
- **Electric Utility:** Utility earnings are heavily regulated; earnings surprises in this sector often come from rate case outcomes, weather-driven demand, or regulatory changes rather than business execution. Alternative data appropriate for tech/retail (web traffic, credit card) is largely irrelevant; what matters is regulatory proceeding tracking and weather data.

---

**Sources:**
1. Shu, D., Liu, Y., Zhang, H., & Du, M. (2025). "FinCall-Surprise: A Large Scale Multi-modal Benchmark for Earning Surprise Prediction." arXiv:2510.03965v1.
2. Kaczmarek, T. & Zaremba, A. (2025). "Beyond the last surprise: Reviving PEAD with machine learning and historical earnings." Finance Research Letters, 86(PE). DOI: 10.1016/j.frl.2025.108751.
3. Research agenda from interests.md (2026-05-07): Markets & Financial Analysis section.
