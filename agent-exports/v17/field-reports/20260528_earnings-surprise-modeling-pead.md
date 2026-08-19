# Field Report: Earnings Surprise Modeling and Post-Earnings-Announcement Drift

**Date:** 2026-05-28
**Cycle Type:** EXPLORE
**Topic:** Quantitative Analysis — Earnings Surprise Modeling
**Source Interest:** Markets & Financial Analysis → Quantitative analysis techniques → Earnings surprise modeling

---

## 1. What I Explored

I followed the earnings surprise modeling thread within Jake's Markets & Financial Analysis interest. The specific research questions: (a) what is post-earnings-announcement drift (PEAD) and why does it persist, (b) how is it measured (SUE and beyond), (c) what modern advances (NLP, machine learning) are improving surprise detection, and (d) what cross-domain patterns emerge from this anomaly.

Sources: Wikipedia PEAD article, Philadelphia Fed working paper on SUE.txt, ETH Zurich arXiv paper on multi-modal deep learning for EA-day prediction (2605.25894), search results from Cambridge Core, ScienceDirect, SSRN, and QuantBuffet.

---

## 2. What I Found

### PEAD Mechanics
- **Ball and Brown (1968)** first documented that stock prices continue drifting in the direction of an earnings surprise for 60+ days after announcement.
- **Bernard and Thomas (1989)** showed the top-decile minus bottom-decile SUE spread was positive in 41 of 48 quarters (1974–1985) and in 11 of 16 down-market quarters.
- ~25–30% of PEAD is concentrated around the three subsequent quarterly announcement windows (~5% of trading days), suggesting a predictable pattern tied to the earnings calendar.
- The cause: investors underreact to the implications of current earnings for future earnings. Not risk-based — behavioral.

### Measurement Methods
| Method | Description |
|--------|-------------|
| **SUE** | (Actual EPS − Expected EPS) / sigma(past forecast errors). Expected from analyst consensus or seasonal random-walk model. |
| **CAR** | Cumulative abnormal returns around announcement windows. |
| **Overnight Returns** | Recent research showing overnight returns post-announcement effectively capture surprise (Berkman et al.). |
| **SUE.txt** | Philadelphia Fed (Meursault et al., 2024): text-based surprise from earnings call transcripts, not the reported EPS number. Generates PEAD.txt **larger than classic PEAD**, persisting even when classic PEAD is near zero. |

### Time-Series Properties of Earnings
From Bernard and Thomas (1990):
- Seasonally differenced quarterly earnings show positive autocorrelation at lags 1–3 (rho1 ~ 0.34, rho2 ~ 0.19, rho3 ~ 0.06).
- At lag 4, negative autocorrelation ~ -0.24 — a partial reversal after one year.
- This pattern is exploitable: if you know the autocorrelation structure, you can forecast future earnings surprises from the current one.

### Modern Advances
- **Multi-modal DL prediction** (Noseda et al., 2026, arXiv 2605.25894): 15 fundamentals + 3 technicals + FinBERT sentiment -> LSTM/Transformer classifiers for EA-day direction (UP/DOWN/NEUTRAL). Transformer achieves higher macro F1; sentiment features improve performance across all models.
- **ML-enhanced SUE** (2025, ScienceDirect): Using historical SUE sequences as features for ML models markedly improves PEAD predictive accuracy beyond simple decile sorts.
- **Large-scale benchmark** (arXiv 2510.03965): Multi-modal benchmark for earnings surprise prediction, indicating academic community coalescence around standardized evaluation.
- **Practitioner strategies**: Decile long-short momentum on SUE, two-factor approaches separating surprise magnitude from drift duration.

### Why PEAD Persists
- Not arbitraged away because: (a) transaction costs, (b) limited attention/processing capacity, (c) institutional constraints (benchmarking, short-sale constraints), (d) the signal is noisy — not all earnings surprises drift.
- SUE.txt finding suggests classic SUE (based on reported EPS) is increasingly priced in, but linguistic nuance from conference calls still contains unpriced information.

---

## 3. What I Think Is Interesting

**The SUE.txt insight is profound.** Markets have absorbed the numeric surprise (classic PEAD fading), but the *textual* surprise — tone, hedging language, forward-looking statements buried in earnings call transcripts — still drifts. This is a perfect example of the "soft information" frontier in quantitative finance: the numbers are commoditized; the language still has alpha.

**PEAD as a behavioral anomaly has structural parallels to AI agent reliability problems.** Just as investors underreact to earnings information, LLM agents underreact to context signals that should change their behavior (the "inertia" problem in agent architectures). The pattern is the same: a known signal exists, but the processing system (market or agent) fails to fully incorporate it. The remediation patterns also parallel — explicit attention mechanisms (Transformer attention / investment screens), ensemble approaches (analyst consensus / model committees), and temporal weighting (recency bias correction).

**The autocorrelation structure is exploitable in a way that mirrors trajectory-to-skill capture.** The quarterly earnings pattern (positive at lags 1–3, negative at lag 4) is a predictable sequence that can be modeled and traded — analogous to how agent interaction trajectories contain patterns that can be extracted into reusable skills.

---

## 4. What I'd Explore Next

1. **SUE.txt implementation**: Can earnings call transcripts be processed with open-source FinBERT to construct a SUE.txt signal? What data sources provide historical transcripts at scale?
2. **PEAD decay across market regimes**: Does PEAD strengthen during high-volatility / low-attention periods and weaken during calm markets? The Fed's finding that classic PEAD is near zero in recent years deserves investigation.
3. **Cross-asset PEAD**: Does the drift phenomenon exist in fixed income (corporate bond earnings reactions), FX (macro announcements), or commodities (inventory surprises)?
4. **Adversarial PEAD**: If PEAD.txt still works, how long until market makers train LLMs to front-run it? What's the arms-race trajectory?

---

## 5. Cross-Domain Connections

| Interest Area | Connection |
|--------------|------------|
| **Entity Resolution** | PEAD research requires resolving firm identity across CRSP, Compustat, IBES, and transcripts — the same heterogeneous dataset problem. The mapping from ticker to PERMNO to IBES ticker is entity resolution in microcosm. |
| **Alternative Data** | SUE.txt is a canonical alternative data play: extracting signal from unstructured text (earnings calls) that is not in the price. Same pattern as satellite imagery, job postings, patent velocity. |
| **OSINT Methodology** | The systematic extraction of actionable intelligence from conference call transcripts mirrors OSINT techniques for extracting intelligence from public communications. Sentiment analysis on earnings calls vs sentiment analysis on political speeches for geopolitical forecasting. |
| **AI Agent Architecture** | The "underreaction" mechanism in PEAD (known signal not incorporated) parallels LLM agent failure modes where context signals are acknowledged but not acted upon. Both domains need explicit mechanisms to convert recognition into action. |
| **Self-Improving Agents** | Using historical SUE sequences to train ML models for better PEAD prediction is structurally identical to trajectory-to-skill capture: past patterns -> model training -> improved future performance. |

### Source Contributions
- Wikipedia: Foundational PEAD mechanics and discovery history
- Philadelphia Fed / Meursault et al. 2024: SUE.txt methodology and persistence evidence
- Noseda et al. 2026 (arXiv 2605.25894): Multi-modal DL architecture and ablation results
- ScienceDirect (2025): ML-enhanced SUE with historical sequence features
- QuantBuffet: Practitioner decile long-short strategy description
