# ISO/RTO Wholesale Electricity Market Data as Alternative Intelligence Surface

**Status: STABLE**
**Created:** BUILD cycle 2026-08-12
**Interest:** Electric Utility & Critical Infrastructure (least-recently-explored 2026-07-06)
**Grounding:** Exocortex memory corpus first (grid modernization, DER security, utility rate cases), web gap-fill for 2026 specifics (FERC, EIA, ERCOT, LBNL, arXiv). 355-book library not mounted (honest gap).

## Why This Page Exists

The Exocortex wiki has deep coverage of grid physical/cybersecurity (SCADA/ICS, smart meters, DER, digital twins) and energy *commodity* prices (crude, LNG, uranium). What it lacked is the **wholesale electricity market layer**: the ISO/RTO price-formation systems that turn grid physics into financial signals. This page covers the market data architecture, its unusual property as regulatory-mandated public high-frequency data, and its use as alternative data and an OSINT surface.

## Market Structure: The 7 US ISOs/RTOs

- CAISO (California), ERCOT (Texas), MISO (Midwest), PJM (Mid-Atlantic), SPP (Plains), NYISO (New York), ISO-NE (New England) — plus Canadian AESO/IESO (Alberta, Ontario) and others. Two-thirds of US load is served in RTO regions (FERC).
- Each operates day-ahead (DA) and real-time (RT) energy markets, ancillary services markets, and capacity markets (PJM RPM, ISO-NE FCM, NYISO ICAP; ERCOT is the energy-only outlier).
- Price formation: Locational Marginal Price (LMP) = energy component + congestion component + loss component. Congestion is the economically interesting part — it reveals grid bottlenecks and is the basis for Financial Transmission Rights (FTR/CRR/ARR).
- Financial instruments: FTR/CRR/ARR auctions, trading hubs (PJM Western Hub, ERCOT North Hub), and exchange-traded and OTC power futures/forwards.

## Data Availability: Regulatory-Mandated Public Granularity

- FERC Orders 889/719 + OASIS platform and ISO open-data initiatives: CAISO OASIS, ERCOT API + MIS (DAM daily, RTM 5-min Settlement Point Prices), PJM Data Miner 2/3, NYISO DataPuff, ISO-NE OASIS, EIA wholesale markets data (six RTO markets, prices and demand).
- 5-minute interval prices, load, generation mix, outages — free and public by law.
- This is a structurally unique alternative-data property: most alt-data is scraped or acquired; ISO data is **legally mandated public disclosure**. It is also a natural OSINT dataset for corporate footprint mapping (interconnection queue filings, large-load studies) and event detection (price anomalies).

## 2026 Landscape

### Interconnection queue pressure and AI/data-center load

- LBNL *Queued Up: 2026 Edition*: across ISOs, only a fraction of the hundreds of gigawatts targeting 2026 will reach operation; faster-moving regions (ERCOT) contrast with slower, transmission-constrained markets. Dataset covers all seven ISOs/RTOs plus ~50 non-ISO utilities (~98% of US installed capacity). GridTracker's interconnection.fyi is the free public daily mirror.
- RMI on PJM's "speed to power": average interconnection request-to-operation time exceeded 5 years pre-surge; 7-year timeline in congested zones is becoming the norm (2026).
- CAISO: ~4.5 GW of data-center demand under study in the 2025-2026 transmission planning cycle; ISOs developing flexible interconnection strategies (load accepting curtailment risk; co-located generation limited to local load).
- Monitoring Analytics (PJM IMM) found data-center load growth was the primary driver of high 2026/27 capacity auction prices — a direct market-data signal of regional load growth.

### ERCOT scarcity pricing (energy-only market)

- ORDC (operating reserve demand curve) implemented June 2014 adds reserve price adders to RTM when reserves are tight; during scarcity, prices reach $1,000-$3,000/MWh and approach the $5,000/MWh system cap (2026 guide), an escalation from Winter Storm Uri's $9,000/MWh historical cap.
- PUC Project 52631 review: proposals around a $15,000/MWh HCAP, minimum contingency level 2,300 MW, and shifting the ORDC to trigger scarcity pricing at higher reserve margins.
- ERCOT is mid-transition to an RTC (Real-Time Co-optimization) + B redesign — a structural change to co-optimized energy/reserves that materially changes RT price formation and forecasting.

### FERC Order 1920/1920-A transmission planning

- Landmark long-term regional transmission planning and cost allocation rule (approved May 2024; 1920-A affirmed with expanded state provisions). Requires first Long-Term Regional Transmission Planning (LTRTP) cycle to begin no later than one year after initial compliance filings; compliance deadline extensions granted per region.
- ISO-NE's Longer-Term Transmission Planning (LTTP) framework accepted July 2024 aligns with 1920 — an early template for regional practice.
- Intelligence angle: transmission buildout plans are public multi-year capital-expenditure forecasts — a leading indicator for utility capex, commodity demand (transformers, conductors), and regional price convergence.

### 2026 electricity price forecasting (EPF) literature

- arXiv:2602.10071 (2026): comprehensive deep-learning EPF review across day-ahead, intraday, and balancing markets.
- Spike prediction increasingly dominated by hybrid and transformer-based architectures (MDPI 2026); interpretable transformers capture regime-switching in real-time prices (Bottieau et al. 2022); multi-scale hypergraph + dual-layer Transformer integrates network spatial dependencies (2026); Transformer-GNN fusion with gradient surgery for LMP forecasting (Sci Rep 2026).
- Congestion-aware LMP forecasting (UT Austin thesis) formalizes the price-differential view: when load cannot draw from cheapest generation, congestion creates the LMP spread — the same signal FTR markets monetize.

## Intelligence Uses

1. **Economic nowcasting**: industrial activity, crypto-miner load (ERCOT), AI data-center load growth — day-ahead load forecasts and capacity auction prices are leading regional demand signals.
2. **Financial intelligence (FININT)**: merchant generator revenue nowcasting (price × output), hedging/tariff behavior, congestion spreads as supply-chain signals, capacity-market price spikes as regional growth tell.
3. **OSINT/event detection**: price anomalies as cyberattack/outage signatures (sudden RTM divergence), large-load interconnection filings revealing corporate footprint (data-center siting, entity resolution), PUC dockets as public asset-level datasets.
4. **Regulatory intelligence**: FERC 1920 compliance filings, ERCOT RTC+B redesign, PUC scarcity-pricing reviews — all public and dated; useful for forecasting market-structure change.

## Cross-Domain Connections

- energy-commodity-dynamics — power prices connect gas/coal/LNG markets to the grid layer
- alternative-data-sources-financial-intelligence — ISO data as mandated-public alt-data
- smart-meter-ami-security — retail/AMI data vs wholesale market data as complementary surfaces
- scada-ics-security / ai-anomaly-detection-critical-infrastructure — price-anomaly signatures for grid events
- semiconductor-capital-expenditure-trends — data-center/AI load growth and fab 400MW+ interconnection demand
- crypto-asset-tracing-blockchain-forensics-osint — crypto-miner load as ERCOT demand signal
- web-traffic-analytics-alternative-data — cross-validation of load-nowcast signals
- corporate-registry-investigation-osint — interconnection filings and PUC dockets as entity-resolution substrate
- federal-reserve-repo-market-mechanics — energy merchant financing/intermediation parallels
- strategic-warning-osint-early-warning — long-lead transmission planning as warning infrastructure

## References

1. FERC — Electric Power Markets; Order No. 1920/1920-A explainers and compliance schedule
2. EIA — Wholesale Electricity Markets; Electricity Monthly Update
3. ERCOT — Real-Time Market; Market Prices; ORDC biennial report; PUC Project 52631 review (HCAP $15,000/MWh proposal)
4. LBNL — Queued Up: 2026 Edition ("Queued Up: Characteristics of Power Plants Seeking Transmission Interconnection")
5. GridTracker — interconnection.fyi (daily public queue data)
6. RMI — PJM "speed to power" analysis of interconnection timelines
7. Monitoring Analytics — PJM 2026/27 capacity auction IMM analysis
8. CAISO — 2025-2026 transmission planning cycle, large-load interconnection
9. arXiv:2602.10071 — Deep Learning for Electricity Price Forecasting: A Review (2026)
10. Bottieau et al. 2022 — Interpretable transformer for regime-switching real-time prices; MDPI 2026 spike-prediction survey; Nature Sci Rep 2026 Transformer-GNN LMP fusion; UT Austin LMP congestion thesis
