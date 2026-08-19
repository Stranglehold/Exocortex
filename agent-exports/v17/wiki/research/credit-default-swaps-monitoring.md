# Credit Default Swaps: Mechanics, Monitoring & Systemic Risk Signaling

**Status: DRAFT → STABLE**
*Created: 2026-08-13 (BUILD cycle, created as DRAFT to be deepened same cycle)*
*Topic: Markets & Financial Analysis — least-recently-explored active interest (last touched cycle 1317)*

## Summary

Credit default swaps (CDS) are bilateral contracts that transfer default risk: the protection buyer pays a running premium (the CDS spread) and the protection seller compensates the buyer if a reference entity suffers a credit event. This page covers the mechanical foundation (single-name vs index CDS, premium/upfront pricing, ISDA credit-event determination), the post-2008 central-clearing and compression reform that changed the counterparty-risk surface, and the monitoring uses of CDS as a real-time credit-risk signal. It complements [[private-credit-systemic-risk]] (opaque credit stress), [[treasury-market-functioning]] (dealer balance-sheet constraints), [[statistical-arbitrage-pairs-trading]] (spread modeling), and [[alternative-data-sources-financial-intelligence]] (credit thresholds as an intelligence surface).

## 1. Contract mechanics

- **Structure:** protection buyer pays periodic premium (spread in basis points) until maturity or a credit event; protection seller pays par minus recovery on default. Single-name CDS references one obligor; index CDS reference a basket (CDX North America, iTraxx Europe).
- **Pricing intuition:** CDS spread ≈ default probability × loss-given-default, adjusted for counterparty and liquidity premia. The par spread equates the expected present value of premium leg and protection leg.
- **Upfront vs running:** standard contracts trade with a fixed coupon plus upfront payment so contracts on the same name share a coupon structure (post-2009 CDS Big Bang).
- **Credit events:** bankruptcy, failure to pay, restructuring (different ISDA 2003/2014 definitions), obligation acceleration; for sovereign CDS, repudiation/moratorium. Auction settlement determines recovery; the ISDA Credit Derivatives Determinations Committee decides trigger disputes.

## 2. Post-2008 reform: the counterparty surface

- **Central clearing (Dodd-Frank Title VII / EMIR):** standardized index CDS now clear at CCPs (LCH CDSClear, ICE Clear Credit) with initial/variation margin and default-fund mutualization. Uncleared single-name trades face bilateral margin rules (ISDA SIMM).
- **Compression:** post-trade portfolio compression (TriOptima, LCH) systematically tears up offsetting trades — global CDS gross notional fell from the ~$58T end-2007 peak to single-digit trillions in the 2020s; net notional (actual risk) remains far lower and concentrated in index products.
- **2008 legacy lesson:** AIG wrote ~$500B of super-senior CDS protection on CDOs with minimal reserves and no CCP — the canonical too-interconnected-to-fail failure. The memory corpus records it as the core of the 2008 systemic-risk narrative.
- **Sovereign and single-name gaps:** sovereign CDS and many single-name contracts remain largely uncleared; restructuring definitions (ISDA 2003 vs 2014) materially change payoffs, and determinations now run through the ISDA Credit Derivatives Determinations Committee (CDDC).

## 3. Monitoring uses: CDS as real-time credit-risk signal

- **5-year spread is the benchmark:** the 5y CDS spread is the most liquid single point on the credit curve. Spreads materially wider than rating-implied levels flag deteriorating fundamentals before rating actions; the CDS-bond basis (CDS spread minus asset-swap spread) measures relative value, funding stress, and dealer balance-sheet pressure.
- **Cross-asset leading indicators:** CDS-implied probability of default vs equity-implied PD (Merton-style distance-to-default) is a standard early-warning screen — CDS typically leads equity-implied risk in idiosyncratic stress, while equity often leads in systemic drawdowns.
- **Index CDS as systemic thermometer:** CDX IG / CDX High Yield / iTraxx Main, and more acutely CMBX (commercial mortgage), are the market's real-time view of broad credit-cycle stress; they have been used in stress-test scenarios and as alternative-data nowcasts.
- **Sovereign CDS:** prices default risk in EM and peripheral European debt; crisis episodes (2011-2012, 2025-2026) show crowding and spread overshoot, so liquidity adjustment is required before reading levels literally.

## 4. 2026 landscape (frontier questions)

- **Structural shrinkage with retained centrality:** global CDS gross notional is a small fraction of its 2007 peak while 5-year single-name and index spreads remain the market's reference price for credit risk; liquidity concentrates in CDX/iTraxx benchmark series, making off-the-run names harder to read.
- **Where counterparty risk sits now:** post-CCP clearing moved systemic risk from dealer-vs-dealer bilaterals to CCP default funds and procyclical margin; the 2020-2026 stress episodes re-open questions about CCP concentration and single-name uncleared exposure.
- **Private-credit overlap:** with the private-credit market's zero-loss fantasy ending (memory corpus, BofA Q2 2026 BDC redemption forecasts), public CDS/CLO indices are the priced transparency proxy for opaque credit — the same epistemic pattern as Exocortex oracle fabrication.
- **AI/ML monitoring:** CDS curves feed foundation-model microstructure and nowcasting pipelines; entity resolution links CDS reference entities to syndicated loans and private credit pools for concentration mapping.
- **Verified 2026 gap-fill (web):** BIS/Risk.net data show global CDS gross notional ~$8T (Apr 2026) with clearing spikes at records (Risk Quantum 2026-04-30); Chicago Fed (2023 Q4) measured ~84-88% of CDS trading cleared at CCPs; ESRB (Apr 2025) treats CDS spreads as a price-mediated contagion channel that systemic risk frameworks must integrate.

## 5. Cross-domain connections

- [[private-credit-systemic-risk]] — CDS as the priced public signal for opaque private credit
- [[treasury-market-functioning]] — dealer balance-sheet constraints shape both UST and CDS intermediation
- [[statistical-arbitrage-pairs-trading]] — cointegration-style modeling of the CDS-bond basis
- [[alternative-data-sources-financial-intelligence]] — CDS screens as FININT alternative data
- [[dark-pool-off-exchange-trading]] — liquidity fragmentation and off-screen risk transfer
- [[federal-reserve-repo-market-mechanics]] — funding stress amplifies credit stress, visible in CDS
- [[financial-foundation-models-market-microstructure]] — ML processing of credit curves
- [[supply-chain-network-analysis-osint]] — supplier default risk via CDS of key counterparties
- [[prediction-markets-information-aggregation]] — comparing market-implied probabilities across venues
- [[intelligence-failure-analysis]] — 2008-style risk blindness as failure to weight cheap priced insurance

## References

1. ISDA Credit Derivatives Determinations Committees and credit-event definitions
2. BIS OTC derivatives statistics (CDS gross notional peak ~$58T end-2007, post-2008 decline)
3. Dodd-Frank Title VII / EMIR central-clearing and margin rules
4. LCH CDSClear / ICE Clear Credit CCP disclosures
5. Post-trade compression providers (TriOptima / LCH) gross-notional reduction reports
6. Hull, Options, Futures, and Other Derivatives (CDS pricing chapters)
7. Memory corpus: 2008 financial crisis records (AIG ~$500B CDS exposure, too-interconnected-to-fail)
8. Memory corpus: private credit systemic risk (zero-loss fantasy, bank-PC $95B credit lines, BDC redemption forecasts)
9. Wiki corpus CDS mentions: strategic-warning-osint-early-warning, taiwan-strait-contingency-economics, post-quantum-cryptography-critical-infrastructure, counterintelligence-analysis-frameworks
10. Risk.net Risk Quantum (2026-04-30): CDS notional tops $8trn as clearing spike hits records
11. Chicago Fed Economic Perspectives (2023 Q4): What Does the CDS Market Imply for a U.S. Default? — CCP clearing ~84% of notional / ~88% of trade count
12. ESRB Report (2025-04): Credit default swaps — analysis and policies (price-mediated contagion)
13. BIS OTC derivatives statistics overview (bis.org/statistics/derstats.htm): outstanding fallen, central clearing risen
