# Structured Forecasting Methods for Geopolitical & Financial Intelligence

**Status:** STABLE
**Created:** 2026-08-12
**Last Deepened:** 2026-08-14 (BUILD cycle)
**Domain:** Geopolitics & Strategic Analysis → Structured Forecasting; Markets & Financial Analysis → Quantitative Methods
**Interests:** Geopolitics & Strategic Analysis, Markets & Financial Analysis, Data Aggregation & Entity Resolution
**Cross-domain connections:** llm-forecasting-oracles, prediction-markets-information-aggregation, ai-geopolitical-risk-forecasting, strategic-warning-osint-early-warning, analysis-of-competing-hypotheses-ach, intelligence-failure-analysis, alternative-data-sources-financial-intelligence, entity-resolution-confidence-calibration, counterintelligence-analysis-frameworks, agentic-deep-research-pipelines
**Primary sources:** Good Judgment Project (Tetlock), ForecastBench 2026, Royal Society Phil. Trans. B (2026), Metaculus 2026 synthesis, arXiv 2602.21229, Exocortex DEC-039 / SWARMFISH corpus

---

## Overview

Structured forecasting applies systematic, transparent methodologies to predict geopolitical and financial events, moving beyond expert intuition to quantifiable probability estimates. Originating from Tetlock's Good Judgment Project (GJP, 2011-2015), the field demonstrates that structured techniques significantly outperform unstructured expert judgment. Tetlock & Gardner (2015) found that superforecaster teams outperformed prediction markets by 15-30%, and the key differentiator was cognitive diversity — different analytical styles, not different volumes of information.

**Foundational finding (Tetlock, GJP):** 50% of superforecaster accuracy improvement came from noise reduction, 25% from better information extraction, and 25% from bias reduction. Fox-like thinkers (many small theories, comfortable with ambiguity) dramatically outperformed hedgehog-like thinkers (one big theory, high confidence). The GJP result is the empirical backbone of the Exocortex SWARMFISH committee: synthetic persona diversity is weaker than real diversity but improvable through per-profile Brier weighting (DEC-039).

## Key Methods

### 1. Prediction Markets
Prediction markets trade event-contingent contracts to aggregate dispersed information through price discovery.

**Platforms:**
- **Polymarket** — crypto-native, USDC-denominated, highest-volume prediction market platform
- **Metaculus** — reputation-weighted forecasting community with logarithmic scoring
- **IEM (Iowa Electronic Markets)** — academic, CFTC-regulated, operating since 1988

**Information efficiency:** Markets aggregate private information that individuals hold in fragments. The efficient market hypothesis applied to event probabilities means prices reflect weighted consensus of participants willing to put capital at stake.

**Limitations:** Liquidity constraints on niche questions, manipulation risk (wash trading, self-dealing), regulatory fragmentation (CFTC jurisdiction on event contracts), and the "favorite-longshot bias" where low-probability events are systematically overpriced.

**Empirical note (March 2026):** A user reported deploying MiroFish's 4,096-agent swarm on NBA prediction data piped into Polymarket, claiming $1.49M in returns. However, 4,096 agents with shallow personas is brute force; A-HMAD research shows diminishing returns beyond 5-7 heterogeneous agents. The value is in analytical differentiation, not headcount.

### 2. Superforecasting

**GJP methodology:** Recruit large, diverse forecasters; use frequent feedback and training; average or weight probabilistic forecasts; track calibration continuously.

**Key findings:**
- Superforecasters are made, not born — training and feedback matter more than raw IQ
- Small teams of diverse forecasters outperform individuals and prediction markets
- Base rates are the strongest single input; the best forecasters are "reluctant Bayesians" who update slowly and deliberately
- Decomposition beats holistic judgment: split complex questions into estimable components

### 3. Delphi Method & Expert Aggregation
Structured, multi-round expert elicitation with controlled feedback. Delphi reduces groupthink by anonymizing contributions and iterating toward convergence. Limitations: slow, expensive per round, and vulnerable to anchoring when experts anchor on early estimates. Used when prediction markets lack liquidity or when event is too novel for historical base rates.

### 4. Bayesian Belief Networks (BBNs)
Explicit directed acyclic graph (DAG) models of causal/probabilistic dependencies among variables. BBNs quantify conditional probability tables (CPTs) and update beliefs as evidence arrives — the formal machinery behind "belief updating" in intelligence analysis. Dynamic BBNs extend this to time slices for early-warning forecasting.

### 5. Monte Carlo Simulation & Scenario Analysis
Probabilistic simulation over parameter distributions to estimate outcome ranges under uncertainty. Used for supply chain disruption modeling, sanctions enforcement scenarios, and financial tail-risk quantification. Scenario analysis (shell-game multiple scenario construction) is complementary: BBNs give probabilities; scenarios give narrative coherence for decision-makers.

## 2026 AI-Forecasting Convergence

### LLM forecasters approach superforecaster parity
By 2026, LLM-based forecasting systems have moved from laboratory curiosity to calibrated engineering. ForecastBench (dynamic, contamination-free) reports LLM Brier Index above the median public forecaster; Metaculus's July 2026 synthesis of 11 analyses projects human-superforecaster parity around **November 2026** (CI Dec 2025–Jan 2028). The Royal Society 2026 study (76 model×prompt sets, 16 LLMs, 580 resolved ForecastBench questions) found the largest gains come from **elicitation/retrieval architecture, not model size** — prompt sensitivity is a first-order effect.

### Market-conditioned prompting (MCP / MixMCP)
arXiv:2602.21229 (Feb 2026) studies context design for mention markets (e.g., will a company mention a keyword in its upcoming earnings call). Findings:
1. Richer context (news + prior transcripts) consistently improves LLM forecasting accuracy.
2. **Market-Conditioned Prompting (MCP)** — treating the market-implied probability as a prior and instructing the LLM to update that prior with textual evidence rather than re-predicting from scratch — yields better-calibrated forecasts.
3. **MixMCP** (mixture of market probability and MCP) outperforms the market baseline by dampening the LLM's posterior update with the market prior.

This is the strongest 2026 evidence that LLM + prediction-market hybrids (the SWARMFISH-adjacent pattern) are strictly better than either alone.

### Multi-expert agent forecasting
ForecastAgentSearch (arXiv:2606.31665) formulates geopolitical forecasting as a **multi-expert agent search problem**: retrieve/rank specialized expert agents by regional knowledge, domain expertise, reliability, and complementarity, then coordinate their analyses into a final forecast with uncertainty awareness. This is architecturally isomorphic to SWARMFISH's profile selection — but with dynamic, per-question agent retrieval instead of a fixed committee.

### Uncertainty-calibrated abstention (FinAbstain)
The financial analog: point-in-time retrieval, multimodal evidence agents, and a **selective prediction** controller that abstains when composite uncertainty exceeds a validated threshold. Time-gated evaluation prevents look-ahead bias. The abstraction pattern — calibrated abstention trading coverage for accuracy — is directly transferable to Exocortex gating decisions.

## Quality Metrics & Calibration

- **Brier Score** — mean squared error of probability forecasts: (1/N)Σ(p_i - o_i)²; 0.25 = random, 0 = perfect, lower is better.
- **Brier Index** — inversion of raw Brier (higher = better) used by ForecastBench.
- **Calibration curves** — decile-binned observed frequencies vs. stated probabilities; a well-calibrated system hits the 45° line.
- **Log loss / logarithmic scoring** — used by Metaculus for reputation weighting.
- **Winkler interval score** — penalizes over/under-coverage of prediction intervals, used in finance benchmarks.
- **Selective prediction metrics** — accuracy/calibration at coverage level, to evaluate abstention controllers (FinBench/FinAbstain pattern).

## Exocortex Integration: OSS + SWARMFISH

The OSS (ingestion) and SWARMFISH (prediction) systems are already latently unified through calibration: OSS promote/falsify fires `swarmfish_outcome`, which scores the committee's Brier calibration. DEC-039 fixes the analytical backbone: **ACH (disconfirmation-first evidence scoring) + GJP-weighted ensemble (per-forecaster Brier weighting, extremize consensus)**. Calibrated forecasters should be made more extreme, not averaged toward 50%.

The loop is latently unified through calibration; architectural unification as a single plugin remains a design decision.

**Key design tension:** Two cooperating plugins with clean contract (modular, independently maintainable) vs. single unified "intelligence agency" plugin with shared data model (lower integration friction, harder to version independently).

## Cross-Domain Connections

1. **Entity Resolution:** Probabilistic forecasting shares mathematical DNA with Fellegi-Sunter record linkage — both use Bayesian frameworks to combine multiple weak signals into strong inference
2. **OSINT Evidence Chains:** Bayesian evidence hierarchy (Tier 1/2/3) is structurally identical to Bayesian belief network node weighting
3. **Admiralty Code:** Source reliability scoring (A-F) and credibility (1-6) maps to Brier calibration — different sources have different forecast accuracy
4. **Intelligence Cycle:** Forecasting → resolution → recalibration is the Orient-Act-Observe loop of the OODA model applied to probabilistic judgment
5. **Multi-Agent Architecture:** SWARMFISH's 8-profile committee is a production deployment of the ensemble forecasting principle validated by Tetlock
6. **Analysis of Competing Hypotheses (ACH):** ACH matrix methodology is complementary — ACH evaluates evidence consistency with hypotheses; structured forecasting quantifies hypothesis probabilities
7. **Local-to-Frontier Bridging:** Forecasting accuracy calibration (Brier score) is an evaluation framework that could validate local model performance against frontier benchmarks
8. **Sanctions Evasion Detection:** Structured forecasting can estimate probability of evasion method adoption given enforcement changes — directly applicable to risk assessment
9. **Supply Chain Network Analysis:** Monte Carlo simulation for disruption scenario modeling under parameter uncertainty
10. **Deception Detection:** Forecast calibration degrades under systematic deception — Brier score divergence can itself be a deception indicator
11. **LLM Forecasting Oracles:** [[llm-forecasting-oracles]] documents the calibration mathematics and the vulnerability boundary where well-calibrated oracles degrade into oracle fabrication — this page is the methodology layer above that system architecture
12. **Strategic Warning:** Grabo's anticipatory-warning doctrine supplies the operational frame for acting on calibrated probabilities before they resolve — probability without lead time is not warning

## References

1. Tetlock, P.E. & Gardner, D. (2015). *Superforecasting: The Art and Science of Prediction*. Crown.
2. Mellers, B., et al. (2014). "Psychological Strategies for Winning a Geopolitical Forecasting Tournament." *Psychological Science*, 25(5), 1106-1115. (GJP primary results)
3. Thinking Machines/Mantic (2026). AI forecasting systems approaching superforecaster accuracy on geopolitics.
4. MiroFish prediction system deployment report (March 2026). 4,096-agent swarm on Polymarket NBA data.
5. Exocortex Spec: Analytical Cognitive Profile Design Notes (March 2026). SWARMFISH architecture and profile system.
6. Exocortex DEC-039: ACH Backbone + GJP-Weighted Ensemble for Intelligence Analysis (May 2026).
7. Exocortex v16 Export: AI Geopolitical Risk Forecasting wiki page (May 2026).
8. Pearl, J. (1988). *Probabilistic Reasoning in Intelligent Systems*. Morgan Kaufmann. (Bayesian networks)
9. Wolfers, J. & Zitzewitz, E. (2004). "Prediction Markets." *Journal of Economic Perspectives*, 18(2), 107-126.
10. Heuer, R.J. (1999). *Psychology of Intelligence Analysis*. CIA Center for the Study of Intelligence. (ACH methodology)
11. Kim, S. et al. (2026). "Forecasting Future Language: Context Design for Mention Markets." arXiv:2602.21229. (MCP / MixMCP)
12. Cai, M. et al. (2026). "ForecastAgentSearch: Towards a Multi-Expert Agent Search System for Geopolitical Event Forecasting." arXiv:2606.31665.
13. ForecastBench — dynamic contamination-free LLM forecasting benchmark, Brier Index. https://forecastbench.org/
14. Good Judgment / FRI — Human vs AI Forecasts (Feb 2026). https://goodjudgment.com/human-vs-ai-forecasts/
15. Metaculus — AI Forecasting in 2026: What 11 Analyses Say (Jul 8 2026). LLM-superforecaster parity ~Nov 2026.
16. Royal Society Phil. Trans. B (2026) — Crowdsourced versus LLM forecasting; 76 model×prompt sets, 580 resolved ForecastBench questions.

## Deepening Log

- 2026-08-12: DRAFT created (168 lines).
- 2026-08-14: Deepened 168→~230 lines; added 2026 AI-forecasting convergence section (ForecastBench parity trajectory, Royal Society prompt-sensitivity, MCP/MixMCP hybrid markets+LLM, ForecastAgentSearch multi-expert retrieval, FinAbstain selective prediction), expanded quality metrics with Winkler/selective-prediction scores, grounded DEC-039 GJP weighting + OSS/SWARMFISH calibration loop from shared corpus (search_memory), verified 2026 sources via arXiv (2602.21229, 2606.31665); search_library returned only generic Bayesian ML texts (honest gap). Status DRAFT → STABLE. Cross-domain connections 10→12.
