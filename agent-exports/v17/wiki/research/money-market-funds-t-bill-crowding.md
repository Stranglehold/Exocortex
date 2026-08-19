# Money Market Funds, Cash & T-Bill Crowding

**Status: STABLE**
**Topic Slug: money-market-funds-t-bill-crowding**
**Created: 2026-08-18**
**Interest Origin: interests.md → Markets & Financial Analysis → Federal Reserve operations / treasury market functioning**
**Primary Sources:** ICI Money Market Fund Assets weekly release (2026-08-13), SEC Rule 2a-7 + 2023 MMF Reform (adopted 2023-07-12), TBAC Q1 2026 & Q1 2024 T-bill charges, "Treasury Bill Shortages" (Journal of Finance 2024), "The passthrough of Treasury supply to bank deposit funding" (JFE 2026), Reuters (2025-07-14), OFR MMF repo monitor, FRED RRPONTSYD, corpus pages (federal-reserve-repo-market-mechanics, treasury-auction-demand-analytics)

---

## 1. Abstract

Money market funds (MMFs) are the marginal buyer of short-dated US government paper and the dominant non-bank cash-parking vehicle for institutional cash. As of August 2026 MMF assets stood at **$7.93T** (ICI, week ended 2026-08-12) — a record. The sector's size, its 2023–2026 migration out of the Fed's Overnight Reverse Repo (ON RRP) facility into direct Treasury bills, and its substitution effect on bank deposits make MMFs the pivot of the "cash crowding" dynamic: abundant T-bill supply absorbs money-fund cash, drains ON RRP, pressures bank deposit franchises, and — because deposit funding is a substitute good — amplifies deposit contraction when deposit rates lag money-market rates. The same structure creates a run-risk surface that the SEC's 2023 Rule 2a-7 reforms addressed by removing gates and imposing liquidity fees on institutional prime funds.

## 2. MMF Mechanics & Taxonomy

- **Rule 2a-7 scaffold (17 CFR § 270.2a-7):** amortized-cost/stable $1.00 NAV for qualifying funds; WAM ≤ 60 days; WAL ≤ 120 days; daily/weekly liquid asset minimums (10% / 30%).
- **Three segments:** government (T-bills, agencies, repos — the largest, ~$6.5T of ~$7.9T), prime (CP, CDs, deposit-linked), tax-exempt (municipals). Government funds are the marginal T-bill and repo-market cash lenders.
- **Run tail:** institutional prime funds carry the historical run risk (2008 Reserve Primary Fund break-the-buck; March 2020 Covid prime-fund stress).

## 3. The 2023 SEC Reform (effective 2024–2025)

- July 12, 2023, 3–2 vote adopting amendments to Rule 2a-7:
  - **Removed temporary redemption gates.**
  - Replaced the old threshold-triggered liquidity fees with a **mandatory liquidity-fee framework** (institutional prime funds) tied to weekly liquid assets plus board discretion, and **discretionary fees** for retail/government funds.
  - The proposed **swing pricing framework was not adopted** for MMFs.
- Reform intent: reduce first-mover advantage and run incentives. The tension: removing gates narrows the run-management toolkit; retained liquidity fees keep a partial anti-dilution mechanism.
- This is the regulatory anchor for MMF behavior during the 2024–2026 T-bill-crowding period: higher liquidity buffers, stable-NAV economics preserved.

## 4. ON RRP Drain → T-Bill Crowding Mechanism

- ON RRP peaked ~$2.5T (Dec 2022), dominated by government MMFs; near-zero since mid-2025 (Reuters 2025-08-29; FRED RRPONTSYD).
- Since May 2023 the US Treasury issued ~$2.2T net T-bills; MMFs cut reverse-repo balances by a similar amount (market analysis). Crowding is a **portfolio substitution**: MMFs move from ON RRP at the facility rate into T-bills at higher market yields when bill supply exceeds benchmark levels.
- TBAC (Q1 2026) lists MMF asset-growth factors: spread differential between money-market rates and bank deposit rates; short-tenor preference encouraged by the (then) inverted curve; recent Fed rate easing may slow or reverse growth.
- Reuters (2025-07-14): record $7.4T assets (July 1, 2025); funds "bring 'em on" for T-bill supply — demand elasticity when yields and liquidity are attractive.

## 5. Deposit-Funding Substitution & Bank Amplification

- **JFE 2026 ("The passthrough of Treasury supply to bank deposit funding"):** with bank market power, higher deposit competition makes aggregate deposit supply more rate-sensitive; T-bill supply reduces deposit demand (substitute good), so the contraction in deposit funding is **amplified by deposit competition**.
- Macro channel: large T-bill issuance transmits into bank funding costs and liquidity buffers → credit supply. This is a first-order fiscal-to-bank-intermediation link.
- 2024–2026 manifestation: deposit rates lagged T-bill/MMF yields → household/business cash migration to MMFs → record MMF assets; bank funding shifted to wholesale (brokered deposits, FHLB advances) — direct link to private-credit-systemic-risk page.

## 6. Scarcity vs Crowding: Both Regimes Are Documented

- **JFI 2024 ("Treasury Bill Shortages and the Pricing of Short-Term Assets"):** when T-bill supply is low relative to money-fund demand, MMFs crowd into other short assets and short-term spreads compress; documents market clearing between T-bills and shadow-bank deposits.
- So the MMF layer is demand-driven in scarcity regimes and supply-driven in crowding regimes — the sign flips with the bill-supply benchmark ratio. Monitoring surface: TBAC benchmark issuance guidance, bill share of marketable debt, MMF allocation to bills vs repos vs deposits.

## 7. 2026 State & Monitoring Surface

- ICI 2026-08-13: $7.93T MMF assets (+$18.26B w/w; government +$20.69B, prime +$1.79B).
- ON RRP near zero except quarter-end window-dressing spikes; Fed treats ON RRP as a soft floor (2021 historical note: Fed "unconcerned" as use approached $1T).
- OFR MMF repo monitor (Form N-MFP, Item C1) provides asset-level/counterparty transparency for MMF repo portfolios.
- Alternative-data surface: weekly ICI MMF flows double as a nowcasting series for risk appetite, bank-deposit strain, and fiscal-absorption capacity.

## 8. Stablecoin Overlap

- Interest-bearing and state-aligned stablecoins are emerging MMF-adjacent vehicles (reserves parked in T-bills/repos); at scale they alter bank funding, credit supply, and short-money run dynamics (State Street 2025). Cross-link to tokenized-cross-border-payment-rails.

## 9. 2026 Research Frontiers / Open Questions

- Stable-NAV economics under rising T-bill volatility and potential swings in bill supply.
- Whether Fed rate easing reverses MMF growth (TBAC hypothesis) and triggers a deposit comeback.
- Post-reform MMF liquidity-buffer behavior under a real repo stress — untested since implementation.
- The deposit-passthrough coefficient varies with bank market power; the JFE result invites cross-country and time-varying estimation.

## 10. Cross-Domain Connections

1. [[federal-reserve-repo-market-mechanics]] — ON RRP drain, SOFR, dealer balance sheets; MMFs are the dominant cash side.
2. [[treasury-auction-demand-analytics]] — MMF bidder class in T-bill auctions; demand decomposition effects.
3. [[treasury-market-functioning]] — T-bill supply, liquidity, crowding-out debate.
4. [[private-credit-systemic-risk]] — bank funding disintermediation and liquidity-mismatch parallels.
5. [[tokenized-cross-border-payment-rails]] — state-aligned/interest-bearing stablecoins as MMF substitutes.
6. [[alternative-data-sources-financial-intelligence]] — weekly ICI MMF flow data as a FININT/nowcasting series.
7. [[foreign-exchange-market-intelligence]] — dollar funding conditions and offshore cash pools.
8. [[credit-default-swaps-monitoring]] — systemic-risk monitoring of short-funding stresses.
9. [[structured-forecasting-geopolitical-intelligence]] — fiscal issuance + MMF absorption as macro-forecast input.
10. [[statistical-arbitrage-pairs-trading]] — T-bill/deposit spread and MMF allocation shifts as tradable spread signals.

## 11. References

1. ICI, "Money Market Fund Assets," weekly release (2026-08-13), https://www.ici.org/research/stats/mmf
2. 17 CFR § 270.2a-7, e-CFR, https://www.law.cornell.edu/cfr/text/17/270.2a-7
3. SEC, "Money Market Fund Reforms," adopted 2023-07-12 (SEC.gov).
4. TBAC, "Trends in Demand for US Treasury Securities," Q1 2026 charge, home.treasury.gov.
5. TBAC, "Considerations for T-bill Issuance," Q1 2024, home.treasury.gov.
6. "Treasury Bill Shortages and the Pricing of Short-Term Assets," Journal of Finance (2024), https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13376
7. "The passthrough of Treasury supply to bank deposit funding," Journal of Financial Economics (2026), https://www.sciencedirect.com/science/article/pii/S0304405X26001054
8. Reuters, "A slew of T-bills coming? Money market funds say 'bring 'em on'" (2025-07-14).
9. OFR, "U.S. MMFs' Investments in the Repo Market," financialresearch.gov.
10. FRED series RRPONTSYD.
11. State Street, "Interest-bearing stablecoins and macroeconomic stability" (2025), statestreet.com.
12. BNY iFlow, "Increasing T-bill issuance and money markets."
