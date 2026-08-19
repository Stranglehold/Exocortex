# Field Report: Federal Reserve Balance Sheet Normalization and Repo Market Stress (2026)

**Date:** 2026-05-26  
**Interest:** Markets & Financial Analysis  
**Thread:** Federal Reserve balance sheet management, repo market mechanics, Treasury market functioning

---

## 1. What I Explored

Investigated the Federal Reserve's balance sheet normalization journey through 2025 into early 2026, focusing on the end of quantitative tightening (QT), the transition to an ample-reserves framework, and emerging stress in the repo market as reserves approached scarcity. Sources: Federal Reserve Board publications, St. Louis Fed Page One Economics (Feb 2026), SVB Asset Management (Nov 2025), macrodispatch repo market analysis (early 2026).

## 2. What I Found

### The End of QT2
- On December 1, 2025, the Federal Reserve officially ended quantitative tightening (QT2), freezing its balance sheet at approximately $6.1 trillion in securities holdings.
- The FOMC judged that reserves had reached "efficient and effective levels to implement policy in an ample reserves regime."
- This was the second balance sheet runoff in a decade. QT1 (2017–2019) ended with significant turmoil in repo markets when reserves dropped to ~$1.4 trillion. This time, the Fed telegraphed the end date well in advance, avoiding a repeat of the September 2019 repo spike.

### The Ample-Reserves Framework
- The Fed operates a corridor system with IORB as the floor, the ON RRP facility as a supplementary floor, the Discount Window as the ceiling, and the Standing Repo Facility (SRP) as a backstop.
- Reserves are at roughly $2.9 trillion (mid-2026 illustrative figures), well above the ~$1.4 trillion level that caused stress in 2019.
- The Fed's St. Louis publication explains that the demand curve for reserves is flat near the administered rates, so small shifts in supply don't affect the federal funds rate. This is the operational definition of "ample."

### Mounting Repo Market Stress
- Despite the orderly end of QT, repo market functioning showed significant strain throughout 2025 and early 2026 (macrodispatch):
  - **EFFR-IORB arbitrage collapsed**: Foreign banks' 7-basis-point arbitrage (borrow at fed funds, earn IORB) compressed to 1 bp in H2 2025 — a signal that marginal reserves are being bid away.
  - **Standing Repo Facility failure as ceiling**: Throughout 2025, repo rates traded persistently above the SRP rate. On Dec 31, 2024, rates were 38 bp above the facility. The Fed's stigma fix (renaming from SRF to SRP) didn't resolve the issue; the facility is either operationally inaccessible to the right institutions or too cumbersome.
  - **DVP repo doubled** to ~$3.5 trillion daily volume, with sponsored repo accounting for over $2 trillion. This structural shift toward centrally cleared transactions reflects regulatory capital advantages but concentrates stress on primary dealers.
  - **Dealer balance sheet strain**: Primary dealer net longs exceeded $200 billion; dealer-to-non-dealer bid ratios at Treasury auctions hit 5:1 on long bonds and 4:1 on 10-year notes.
  - **Seasonal pain points**: Quarter- and month-end funding squeezes became routine as dealers reduced repo activity to manage balance-sheet constraints.

### On the Horizon
- **Stablecoin growth** (from $200B to $300B+) creates a persistent new source of demand for Treasury bills, indirectly affecting short-term funding markets.
- **Treasury General Account (TGA) fluctuations** continue to drain/add reserves unpredictably as the Treasury manages cash balances.
- **Reserve management purchases (RMPs)** — the Fed has begun buying Treasury bills again (modestly) to gradually add reserves back, a distinct operation from quantitative easing (no intention to lower long-term rates).

## 3. What I Think Is Interesting

The repo market is sending signals that the "ample reserves" framework is more fragile than official statements suggest. The collapse of the EFFR-IORB arbitrage and the persistent failure of the Standing Repo Facility as a ceiling are not anomalies — they are market participants pricing in reserve scarcity. The Fed stopped QT before a crisis, but the system is running right at the edge of ample/scarce, and the buffer is thinner than it appears. The structural changes — DVP repo growth, stablecoin demand, dealer concentration — mean that the old simple measures of reserve adequacy (like the ratio of reserves to GDP) may be misleading. The system is more complex and more tightly coupled than in 2019, and the same amount of stress could propagate differently.

**Cross-domain connection:** This directly ties to geopolitical/sanctions analysis — the dollar funding ecosystem that repo represents is the infrastructure through which sanctions are enforced. Reserve scarcity in the U.S. funding market could cascade into emerging-market dollar funding stress, undermining sanctions effectiveness or triggering unintended financial stability consequences. The interaction between Fed balance sheet policy and global dollar liquidity deserves its own investigation.

## 4. What I'd Explore Next

1. **Detailed mechanics of the Standing Repo Facility failure**: What specific operational frictions prevent its use? Is it a collateral eligibility issue, counterparty limitation, or stigma that rebranding can't fix?
2. **Stablecoin-Treasury bill nexus**: How much of the T-bill market is now absorbed by stablecoin issuers, and what does that mean for collateral availability in repo?
3. **Primary dealer capacity constraints**: Deeper analysis of dealer balance sheet metrics and the interaction with SLR and G-SIB surcharge rules.
4. **Emerging-market dollar funding**: How does Fed reserve policy transmit to cross-currency basis swaps and dollar funding costs in Asia and Europe?

## 5. Cross-Domain Connections

- **Sanctions economics** (Geopolitics interest): Dollar funding infrastructure is the enforcement mechanism for financial sanctions. Tight reserve conditions could amplify sanctions' unintended consequences on third-party countries.
- **Entity resolution** (Data Aggregation interest): The Fed's counterparty data (primary dealers, SRP participants, MMFs) is a structured graph of financial relationships that could be mapped using entity resolution techniques.
- **Knowledge graph construction**: Fed data releases (FOMC minutes, SLOOS, SFOS, repo market data) are structured enough to be ingested into a knowledge graph for temporal reasoning about monetary policy transitions.
