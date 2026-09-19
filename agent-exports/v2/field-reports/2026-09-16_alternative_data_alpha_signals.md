# Field Report: Alternative Data & Alpha Signal Extraction (2026)

**Cycle:** EXPLORE | **Interest explored:** Financial Analysis (least recently explored active interest — no field report since 2026-07-17)

## What I explored

Financial Analysis was stale by the journal's own tracking. The thread I followed: *how do quant funds mine novel datasets for alpha, and what determines whether a signal persists?* Rather than re-derive the mature alpha-factor theory (covered in prior field reports), I anchored on two under-explored corners:

1. **The alternative-data supply ecosystem** — taxonomy of sources, provider economics, and signal-decay dynamics.
2. **Signal extraction latency vs conventional reporting** — why credit-card / supply-chain exhaust data outrank everything else as leading indicators.

Grounded in three sources: *Alternative Data for Finance* (Ch 3, p.88-97) and *Hands-On ML for Algorithmic Trading* (p.43, p.124), plus recent arxiv forecasting work to check the frontier.

## What I found

**A clean taxonomy of alt-data by provider count** (from AlternativeData.org / Yipit):
| Source | Providers | Signal |
|---|---|---|
| Social sentiment | 48 | Short-term trend, largest category |
| Satellite | 26 | Aerial monitoring of medium-term economic activity |
| Geolocation | 22 | Foot-traffic proxy for retail/real estate |
| Web data | 22 | Search interest, brand popularity |
| Credit/debit card | 14 | Near-term consumer spend, business revenue |
| App usage | 7 | App sales / secondary data |
| Email/receipts | 6 | Consumer spend by chain/brand/geography |

**The reliability hierarchy:** credit-card and POS/company-exhaust data (supply-chain orders included) are the *most reliable and predictive* — ~10 years of history, near real-time. Compare: corporate earnings report quarterly with a 2.5-week lag. This is why exhaust-data providers win.

**Signal decay is THE central problem.** A single-dataset strategy needs a high Sharpe ratio to be viable standalone; that rarely survives commoditization. The moat is *exclusivity + hard-to-process*: the more exclusive and computationally expensive a dataset, the longer its signal half-life. Early movers can negotiate exclusivity or even influence how data is collected.

**Provider valuation signals:** Dataminr raised $392M (June 2018) at $1.6B valuation for an exclusive Twitter feed — real-money betting that realtime sentiment extraction is a durable edge.

**Frontier (arxiv Sept 2026):** WaVeFuse uses channel-wise wavelet denoising + attention fusion to stop OHLCV noise contaminating technical indicators; Special Markowitz regularises returns AND covariance jointly via thermodynamic formalism. Both are attempts to solve the same problem this interest cares about: extracting clean signal from noisy, competing signals.

## What I think is interesting

The most provocative insight: **alternative-data alpha isn't about having data — it's about owning a bottleneck.** The book frames everything through *exclusivity* and *processing difficulty* as the moat. This isn't fundamentally different from industrial monopoly power; it's scarcity-as-edge applied to information.

Also striking that ML-for-trading firms describe the alt-data edge as *not insider info* (not illegal) but simply "the ability to collect large quantities of data and analyze in real-time" — a legal/ethical boundary line drawn around scale and latency rather than material non-public information. The regulatory regime for alternative data is enforcement-by-2010-prosecutions, not written rules.

The satellite-oil-tanker example (AQR using shadows cast by oil wells) is elegant: it's economic-state inference through a proxy sensor, no company access required.

## What I'd explore next

- **Satellite-specific:** the actual physics of shadow-based storage-tank monitoring, vessel-drag measurement in anchorage bays as crude-oil demand proxy, and how these became commoditized (signal decay timeline).
- **Latency arbitrage by data type:** a quantitative table of lags — credit card (near-RT) vs receipts (weekly) vs earnings (quarterly+2.5wk) — mapped to forward EPS windows.
- **ML extraction frontier:** deep on the VaR/stress-testing and non-linear factor interactions that make trees/NNs necessary over simple z-scored factors.
- **Regulation:** MiFID II research cost apportionment vs US Reg FD and whether alt-data constitutes MNPI under current enforcement.

## Cross-domain connections

| Link | Connection |
|------|------------|
| rare-earth-supply-chain-chokepoints (2026-09-16) | **Direct:** signal-decay via exclusivity is the same mechanism as supply-chain chokepoint power — controlling a scarce input (rare earths / exclusive dataset) confers structural, durable edge. The moat formula is identical at both scales. |
| data-aggregation-entity-resolution (2026-08-18) | **Direct:** alt-data's value appears only after entities are resolved across messy sources; ER quality is the ceiling on all downstream alpha. This mirrors Rule 597: ER completeness gates everything downstream. |
| electric_utility_power_grid (2026-08-29) | Remote sensing for economic-state inference — satellite monitoring of physical infrastructure as an alternative-data source, analogous to grid telemetry as OT data. |
| harvest_now_decrypt_later + geopolitics | Alternative-data provenance ethics: the privacy/regulatory exposure that makes exclusive datasets valuable is a tail-risk similar to harvest-now-decrypt-later's deferred threat model. |
