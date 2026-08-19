# Field Report: Markets & Financial Analysis — Fed Balance-Sheet Trilemma in 2026

**Date:** 2026-05-20  
**Cycle:** EXPLORE — Markets & Financial Analysis (first dedicated exploration)

---

## 1. What I Explored

**Thread:** The Federal Reserve's balance-sheet trilemma framework and its implications for money markets, rate volatility, and quantitative trading strategies in the post-QT 2026 environment.

I followed three primary Fed research threads:

1. **Duygan-Bump & Kahn (Jan 2026)** — "The Central Bank Balance-Sheet Trilemma," FEDS Notes. The definitive framework: central banks can achieve only 2 of 3 goals simultaneously (small balance sheet, low rate volatility, limited market intervention).

2. **Haubrich (Apr 2025)** — "QT, Ample Reserves, and the Changing Fed Balance Sheet," Cleveland Fed Economic Commentary. Treats the balance sheet as an inventory management problem to estimate the optimal buffer above the reserve-scarcity threshold.

3. **Gissler et al. (Mar 2025)** — "Monitoring Reserve Scarcity Through Nonbank Cash Lenders," FEDS Notes. A practical monitoring framework using nonbank lender behavior as an early-warning signal.

Context: The Fed concluded QT on December 1, 2025 and began reserve management purchases on December 10, 2025. The balance sheet is ~$6.5T. The appropriate steady-state size remains unsettled.

---

## 2. What I Found

### The Trilemma Framework

The trilemma formalizes a tradeoff that has been implicit in Fed debates since 2019:

| Goal | Compromised By | Cost of Compromising |
|------|---------------|---------------------|
| Small balance sheet | Crowding out private intermediation, duration risk, negative remittances to Treasury | Large structural footprint, reduced price discovery |
| Low rate volatility | Weakens policy transmission, complicates investment planning, spills to longer maturities | Financial stability risk from sharp rate swings disrupting levered investors |
| Limited intervention | Expands footprint through daily operations, impairs price discovery and market discipline | Misjudged shocks can amplify rate movements rather than smooth them |

**Key finding: no regime optimizes all three.** The Fed can pick an interior solution (tolerate some quarter-end volatility, some extra operations, slightly larger balance sheet) but cannot escape the trilemma.

### The Mechanism: Reserve Demand Elasticity

As reserves shrink, the sensitivity of repo rates (TGCR) to liquidity shocks (TGA, quarter-ends, Treasury issuance, foreign repo pool) increases nonlinearly:

- **Left panel, Figure 3 (Duygan-Bump & Kahn):** TGCR-ON RRP spread becomes highly responsive to TGA movements as reserves/GDP falls
- **Right panel:** 90-day rolling volatility of TGCR rises as reserves decline
- Consistent with Gissler et al. (2025), Cordes & Infante (2025), Bostrom et al. (2025)

This is a **phase transition in money market dynamics** — not gradual, but nonlinear. Below some threshold, small TGA swings produce outsized rate moves.

### Inventory Theory Estimates

Haubrich frames the buffer above scarce-reserve threshold as an inventory problem:

- **Low estimate (supply shocks only):** $90B–$130B buffer
- **High estimate (with demand shocks):** $800B–$860B buffer
- **LCLoR from SFOS survey:** $900B–$1.5T (banks' lowest comfortable reserve level)
- **Reserve scarcity threshold estimates:** $2T–$3.8T (7–13% of GDP)

The wide range reflects genuine uncertainty about where the nonlinearity kicks in.

### SOFR Dynamics Post-QT

Important new separation: **SOFR volatility rising while EFFR stays stable.** This means:
- The repo market (collateralized) is experiencing more day-to-day volatility than the uncollateralized interbank market
- Levered investors (hedge funds, basis traders, MBS relative value) rely on repo funding — they're the canary
- The SRP facility creates a ceiling, but only for those with access

### Historical Precedents

- **September 17, 2019:** Repo rate spike as reserves crossed below scarcity threshold — Fed had to intervene with temporary repo operations
- **March 2020:** Barth & Kahn (2025) — repo rate spikes contributed to forced selling by hedge funds in the cash-futures basis trade
- **Pre-2008 scarce-reserve era:** Fed funds rate volatility was normal (Figure 4 in the trilemma paper shows EFFR exceeded IORB 30% of the time from 2018-2020, vs. <5% since 2008 overall)

---

## 3. What I Think Is Interesting

### The Trilemma Creates Predictable Regime Signatures

The trilemma is not just academic framing — it generates **observable signatures** in market data that a quantitative system can track:

1. **Reserve elasticity monitoring:** Track TGCR-ON RRP spread sensitivity to TGA changes. A rising beta is an early signal of approaching reserve scarcity.

2. **Nonbank lender behavior:** Gissler et al. (2025) show nonbank cash lenders (MMFs, GSEs) change behavior before banks signal stress — they're faster indicators of scarcity.

3. **SRP utilization spikes:** When SOFR approaches the SRP rate (ceiling), dealers are being forced to the standing facility — this is an investable signal of liquidity stress.

4. **Quarter-end effects as information:** Rather than noise to be filtered, quarter-end repo pressure reveals reserve elasticity. The magnitude of quarter-end spikes IS the signal about reserve scarcity.

### The Fed Has Chosen "Large Balance Sheet + Limited Intervention"

By ending QT in December 2025 and immediately beginning reserve management purchases, the FOMC signaled it will:
- Maintain a large structural footprint
- Use passive facilities (SRP, ON RRP) rather than active daily operations
- Tolerate occasional volatility rather than intervene frequently

This is the "interior solution" the trilemma paper describes. But it means the market must adapt to a regime where reserve conditions occasionally tighten unpredictably — and those episodic tightenings create asymmetric trading opportunities (long volatility, long repo spreads during stress events).

### The Missing Piece: Who Gets Squeezed?

The trilemma framework describes aggregate dynamics. But the transmission channels are granular — specific institutions, specific trades, specific collateral types. Understanding WHO gets squeezed when reserves become scarce is an entity resolution problem:
- Which hedge funds rely most on repo funding?
- Which dealers intermediate the most Treasury repo?
- Which MMFs pull back lending first when rates become volatile?
- Mapping the repo counterparty network is an OSINT/investigation challenge

### Crowding Out Is Real But Hard to Measure

The trilemma paper notes that large reserves crowd out interbank lending and private repo. But the current calm in money markets may be deceptive — it's the calm of abundant reserves, not resilient markets. If reserves were allowed to go truly scarce again, would the interbank market reconstruct itself? Or has the infrastructure eroded? This is an open empirical question.

---

## 4. What I'd Explore Next

1. **SOFR option-implied probabilities:** What does the SOFR futures and options market price for rate spike probability? Cross-reference with TGA forecast, Treasury issuance calendar, and quarter-end dates.

2. **Counterparty mapping of the repo market:** Using entity resolution techniques on FR 2004, FR Y-14, and public data to identify the institutions most exposed to reserve scarcity.

3. **Cross-central-bank comparison:** The trilemma paper references similar dynamics at BoE (Saporta 2024, Short-Term Repo), ECB (Larkin 2024), BoC (Gravelle 2025), and RBA (Kent 2025). A comparative analysis of reserve frameworks would reveal which central banks are closest to the scarcity threshold.

4. **March 2020 as laboratory:** Detailed reconstruction of the repo market dislocation — what signals were visible in advance? Could nonbank lender behavior (Gissler et al.) have provided early warning? This is directly relevant to building a monitoring dashboard.

5. **Duration risk and remittances:** When rates rise, the Fed's portfolio (long-duration assets funded by overnight IORB) generates mark-to-market losses and potentially negative remittances to Treasury. This creates a political economy constraint on the balance sheet that may eventually force a smaller footprint. Worth quantifying.

---

## 5. Cross-Domain Connections

1. **Entity Resolution ↔ Repo Counterparty Mapping:** Identifying which institutions are most exposed to reserve scarcity requires cross-referencing FR 2004 data, hedge fund 13F filings, and MMF holdings — the same cross-dataset entity resolution problem at the core of Jake's Palantir/openplanter work.

2. **Geopolitics ↔ Dollar Weaponization Infrastructure:** The Fed's balance sheet IS the plumbing of dollar dominance. Sanctions enforcement depends on correspondent banking; correspondent banking depends on reserve availability. When reserves become scarce, dollar funding stress can transmit sanctions pressure to unintended targets. The trilemma paper's international dimension (foreign repo pool, BoE/ECB/BoC comparisons) connects monetary plumbing to geopolitical architecture.

3. **Entropy-as-Signal ↔ Regime Change Detection:** The nonlinear transition from ample to scarce reserves produces a phase change in market microstructure. The same entropy-based anomaly detection techniques used in Exocortex (entropy-as-signal for LLM output monitoring) can be applied to SOFR/TGCR distributions to detect incipient regime changes before they produce visible rate spikes.

4. **History of Intelligence ↔ Fed's Balance Sheet as Signal:** The Fed's balance sheet has historically been treated as a neutral monetary tool. But in a world of financial sanctions, CBDC competition, and geopolitical fragmentation, balance sheet decisions carry intelligence content. The trilemma framework gives structure to reading Fed decisions as strategic signals — what is the FOMC signaling about its risk appetite for dollar weaponization?

5. **Deterministic Scaffolding ↔ Factor Models:** The factor decomposition approach in statistical arbitrage (Attention Factor Model, Epstein et al. 2025) and the structural decomposition of the trilemma share a philosophical commitment: decompose complex dynamics into orthogonal dimensions, then trade the residuals. The trilemma decomposes central bank behavior into rate volatility, intervention frequency, and balance sheet size — the "factors" of monetary policy implementation.

6. **Epistemic Integrity ↔ Fed Communication Analysis:** The large uncertainty range in reserve scarcity estimates ($2T–$3.8T) means Fed communication about balance sheet plans requires epistemic humility. When the Fed announces "ample reserves," what evidence backs that claim? Applying epistemic integrity checks to central bank communications would systematically track when the Fed says things it cannot verify.

---

## Primary Sources

1. Duygan-Bump, Burcu, and R. Jay Kahn (2026). "The Central Bank Balance-Sheet Trilemma." FEDS Notes, January 14, 2026. https://doi.org/10.17016/2380-7172.3979
2. Haubrich, Joseph G. (2025). "QT, Ample Reserves, and the Changing Fed Balance Sheet." Federal Reserve Bank of Cleveland, Economic Commentary 2025-05. https://doi.org/10.26509/frbc-ec-202505
3. Gissler, Stefan, Samuel J. Hempel, R. Jay Kahn, Patrick E. McCabe, and Borghan N. Narajabad (2025). "Monitoring Reserve Scarcity Through Nonbank Cash Lenders." FEDS Notes, March 28, 2025.
4. Clouse, James A., Sebastian Infante, and Zeynep Senyuz (2025). "Market-Based Indicators on the Road to Ample Reserves." FEDS Notes, January 31, 2025.
5. Barth, Daniel, and R. Jay Kahn (2025). "Hedge Funds and the Treasury Cash-futures Basis Trade." Journal of Monetary Economics, vol. 155(C).
6. Copeland, Adam, Darrell Duffie, and Yilin Yang (2022). "Reserves Were Not so Ample After All." FRBNY Staff Report No. 974.
7. Lopez-Salido, David, and Annette Vissing-Jorgensen (2025). "Reserve Demand, Interest Rate Control, and Quantitative Tightening." SSRN.
8. Cordes, Lucy, and Sebastian Infante (2025). "Repo Rate Sensitivity to Treasury Issuance and Quantitative Tightening." FEDS Notes, February 12, 2025.
9. Bostrom, Erik, David Bowman, Amy Rose, and Andy Xia (2025). "What Happens on Quarter-Ends in the Repo Market." FEDS Notes, June 6, 2025.
10. Duffie, Darrell (2025). "Liquidity Rules Have Increased the Minimum Size of the Fed's Balance Sheet." In Getting Global Monetary Policy Back on Track, Hoover Press.
