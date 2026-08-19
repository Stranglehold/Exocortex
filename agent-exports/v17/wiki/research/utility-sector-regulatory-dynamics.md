# Utility Sector Regulatory Dynamics

**Status:** STABLE
**Created:** 2026-06-03  
**Deepened:** 2026-06-03  
**Interests:** Markets & Financial Analysis, Electric Utility & Critical Infrastructure  
**Sources:** 8 web, 6 cross-reference wiki pages

---

## Overview

Utility sector regulatory dynamics encompass the evolving legal, economic, and policy frameworks that govern electric utility operations in the United States. Three forces are reshaping the regulatory compact in 2025–2026: unprecedented load growth from AI data centers and electrification, the shift from cost-of-service regulation to performance-based ratemaking (PBR), and a $1.1 trillion capital expenditure super-cycle that is testing the traditional rate case process.

State PUCs retain primary authority over resource decisions, retail rates, net metering, integrated resource planning (IRP), and renewable portfolio standards (RPS). FERC jurisdiction covers wholesale markets, transmission planning, and interstate commerce — but the DOE's October 2025 directive to FERC on data center interconnection has blurred the federal-state boundary, creating a live jurisdictional dispute.

---

## Core Economic Framework

### The Regulatory Compact
Investor-owned utilities (IOUs) operate under a "regulatory compact": they receive monopoly franchise rights in exchange for an obligation to serve at just and reasonable rates. Revenue requirement formula:

<latex>R = (B \times r) + E + D + T</latex>

Where: <latex>B</latex> = rate base (net plant in service), <latex>r</latex> = allowed rate of return (ROE × equity ratio + cost of debt × debt ratio), <latex>E</latex> = operating expenses, <latex>D</latex> = depreciation, <latex>T</latex> = taxes.

### The Averch-Johnson Effect
Cost-of-service regulation creates a structural incentive to over-invest in capital (rate base) because profit = allowed ROE × rate base. A 2026 ScienceDirect empirical study found that a **one percentage point increase in allowed ROE corresponds to a measurable increase in utility capital ownership** — the Averch-Johnson effect remains active. PBR is partially designed to correct this by decoupling revenue from capital expenditure, instead rewarding outcomes.

---

## Allowed ROE Trends (2024–2026)

| Metric | Value | Source |
|--------|-------|--------|
| Median allowed ROE — electric (Q1 2025) | **9.75%** | Gabelli Funds, Jul 2025 |
| Median allowed ROE — electric (FY 2024) | 9.70% | Gabelli Funds |
| Gas utility ROE average (H1 2024) | 9.83% | PSCdocs, Utah docket |
| Electric ROE authorizations (H1 2024) | 21 (vs 63 in FY2023) | Declining rate case volume |
| Typical ROE range (2020–2022) | 9.3–9.5% | Historical baseline |

**Key trend:** Allowed ROE is drifting upward from the 9.3–9.5% range common in 2020–2022, driven by rising interest rates and utility arguments about increasing cost of capital. However, **rate case volume is declining** — many states locked in ROEs ahead of PBR transitions. Utility stocks function as bond proxies: their earnings power depends on the ROE spread above the risk-free rate.

---

## Performance-Based Ratemaking (PBR)

### What PBR Replaces
Traditional cost-of-service/rate-of-return regulation rewards capital expenditure (the Averch-Johnson effect). PBR decouples revenue from capex by linking returns to measurable outcomes:

| Outcome Category | Example Metrics |
|---|---|
| Reliability | SAIDI (System Average Interruption Duration Index), SAIFI (System Average Interruption Frequency Index) |
| Customer satisfaction | J.D. Power scores, complaint resolution time |
| Energy efficiency | Program savings, peak demand reduction |
| DER integration | Hosting capacity, interconnection queue processing time |
| Affordability | Rate stability vs CPI, low-income program enrollment |

### State Adoption Status
- **Connecticut (PURA):** Draft PBR framework issued alongside United Illuminating $66M rate increase; framework emphasizes affordability and rapid implementation (Acadia Center, 2026)
- **Indiana (IURC):** Published comprehensive PBR study May 2025 examining multi-year rate plans, earnings sharing mechanisms, and performance incentive mechanisms
- **Virginia:** GPI/CEG published PBR design recommendations December 2025 focusing on cost control and equity
- **Hawaii:** PBR framework operational since 2020 — earliest adopter; linked to 100% RPS by 2045
- **California (CPUC):** NEM 3.0 restructuring retail export compensation; active PBR exploration
- **New York (REV):** Reforming the Energy Vision framework incorporates outcome-based utility incentives

### PBR Risk Dimensions
- **Performance metric gaming:** Utilities may optimize measured metrics at expense of unmeasured dimensions
- **SCADA/ICS dependency:** PBR reliability metrics depend on secure operational technology systems — a cyber-physical vulnerability could distort PBR scores (cross-domain to [[scada-ics-security]])
- **Transition costs:** Rate cases become more complex during PBR design phase, potentially increasing regulatory lag

---

## FERC Regulatory Framework

| Order | Year | Key Provision |
|---|---|---|
| **Order 888** | 1996 | Open access transmission; unbundling of generation/transmission |
| **Order 1000** | 2011 | Regional transmission planning and cost allocation |
| **Order 2222** | 2020 | DER aggregators can participate in wholesale markets |
| **Order 2023** | 2023 | Interconnection queue reform — cluster study replaces first-come-first-served |
| **Order 1920** | 2024 | Long-term regional transmission planning; 20-year horizon |

### 2025–2026 FERC Developments
- **DOE Directive (October 2025):** Secretary of Energy submitted letter and proposed rule to FERC seeking expanded FERC jurisdiction over interstate transmission to expedite grid access for large industrial customers (data centers). This is an unprecedented intervention — if implemented, it would significantly shift federal-state regulatory balance (White & Case, Oct 2025)
- **PJM co-location proceeding (February 2025):** FERC initiated review of co-located generation for data centers in PJM, evaluating whether existing tariff language covers behind-the-meter arrangements
- **PJM data center interconnection:** Initial proposal strongly opposed by technology companies; revised alternative emphasizes voluntary demand response by data centers and on-site backup generator utilization (filed late 2025)
- **FERC transmission ROE adders:** 2026 EUCI Transmission Ratemaking course covers evolving policies on ROE adders for transmission investment, abandoned plant recovery, and incentive rates
- **Data center interconnection reform:** FERC teed up June 2026 decision; key issues include speculative project filtering, financial readiness requirements ($1M security deposits), and PJM backstop auction (Utility Dive, Apr 2026)

### Jurisdictional Tension
"FERC Blinked. State PUCs Determine What Happens Next" (Halcyon, 2026): State commissions control utility distribution studies — the real bottleneck for interconnection. A commission hostile to data center cost allocation can stop future recovery and redesign rates so data centers bear more costs.

---

## Data Center Load Growth (2025–2026)

### Scale of Demand
- AI-powered data centers are driving **unprecedented electricity demand growth** across all US regions
- NERC April 2025 assessment: need for enhanced data on operational/technical characteristics of data center interconnection (White & Case)
- In Northern Illinois, one utility's large load study queue = **nearly 40 GW total** across multiple study clusters
- Georgia: 63 data centers in 2023, expected to **quadruple within a decade**
- NARUC 2026 virtual roundtable series on load growth and large loads (January–March 2026)

### Regulatory Responses
- **PJM:** Revised proposal (late 2025) — voluntary demand response by data centers; process for on-site backup generator utilization; 14.9 GW proposed via bilateral contracts + central procurement (Apr 2026)
- **SPP:** Innovative measures for large load interconnection requests
- **ERCOT:** Market-based approach with no capacity market, relying on price signals for resource adequacy
- **Standardized regulatory regime:** Still absent — DOE's FERC rulemaking proposal aims to fill this gap

### Financial Risk for Utilities and Ratepayers
- **Stranded asset risk:** If data center developers do not materialize, utility capex for interconnection infrastructure may not be recoverable
- **Rate design for large loads:** LBNL (January 2025) report on evolving electricity rate designs for large loads — key risk is underutilized investments from speculative projects
- **Speculative project filtering:** Industry consensus that financial readiness demonstrations (site control, security deposits, minimum-term contracts) are essential to prevent interconnection queue congestion

---

## $1.1 Trillion Capital Expenditure Super-Cycle

- EEI 2024 Financial Review (July 2025): **Investor-owned utilities could spend $1.1 trillion between 2025 and 2029** — roughly double the pre-2020 run rate
- Driver triad: grid modernization + data center load growth + generation transition
- DOE GRIP program: $10.5B in grid resilience and innovation partnership funding (cross-reference [[grid-modernization-funding]])
- Ratepayer impact: Record rate case volume in 2025 (e.g., FPL $2.472B); fixed-price fallout risk in high-inflation environment

---

## Investment Implications

- Utility sector is capital-intensive (~$100B/year US CapEx), highly regulated, dividend-oriented
- **Allowed ROE determines equity valuation premium:** utilities trade at P/E multiples reflecting ROE spread vs risk-free rate
- Data center load growth is the primary bull case — but regulatory uncertainty around cost allocation is the primary risk
- Transmission ROE adders (FERC incentive rates) can significantly boost earnings for transmission-owning utilities
- **Regulatory lag risk:** In rapidly rising interest rate environments, rate case frequency must increase to maintain real ROE — utilities with multi-year rate plans face earnings compression
- State-level divergence: utilities in PBR-adopting states may see different valuation multiples than those in traditional cost-of-service jurisdictions

---

## Cross-Domain Connections

| Connection | Wiki Page | Mechanism |
|---|---|---|
| Grid modernization funding | [[grid-modernization-funding]] | DOE GRIP $10.5B, IIJA infrastructure funding flows |
| Electric utility physical infrastructure | [[electric-utility-critical-infrastructure]] | Underlying assets regulated by these frameworks |
| DER integration | [[der-integration-grid-modernization]] | IEEE 1547, hosting capacity analysis, smart inverter requirements |
| Energy commodity dynamics | [[energy-commodity-dynamics]] | Fuel cost passthrough mechanics; regulatory treatment of purchased power |
| Smart meter AMI security | [[smart-meter-ami-security]] | AMI as regulated infrastructure; PBR reliability metrics depend on AMI data integrity |
| SCADA/ICS security | [[scada-ics-security]] | PBR reliability metrics depend on secure SCADA/ICS; cyber-physical vulnerability could distort performance metrics |
| Semiconductor capex | [[semiconductor-capital-expenditure-trends]] | Utility procurement of smart grid components (RTUs, relays, AMI ICs) |
| Entity resolution | [[data-aggregation-entity-resolution]] | Tracking utility holding companies across jurisdictions requires same entity resolution techniques as shell company investigations |
| Alternative data | [[alternative-data-sources]] | Satellite imagery for utility capex verification (transmission lines, substations) |
| OSINT visualization | [[osint-visualization-techniques]] | Geospatial mapping of utility service territories, rate case docket tracking |

---

## Sources

| # | Source | Date | Type |
|---|--------|------|------|
| 1 | Gabelli Funds, "Utilities — U.S." | Jul 2025 | Industry report |
| 2 | IURC Performance-Based Ratemaking Report | May 2025 | State PUC study |
| 3 | RMI, "A Strategic Framework for Utility Cost Control" | Feb 2025 | Policy analysis |
| 4 | GPI/CEG, "Performance-Based Regulation for Virginia's Electric Utilities" | Dec 2025 | Policy analysis |
| 5 | EEI 2024 Financial Review | Jul 2025 | Industry report |
| 6 | White & Case, "DOE directs FERC to accelerate interconnection of data centers" | Oct 2025 | Legal analysis |
| 7 | Halcyon, "FERC Blinked. State PUCs Determine What Happens Next" | 2026 | Market analysis |
| 8 | LBNL, "Electricity Rate Designs for Large Loads" | Jan 2025 | Research report |
| 9 | Utility Dive, "FERC tees up June decision on data center interconnection reform" | Apr 2026 | Industry news |
| 10 | NARUC, "Load Growth Resources for Regulators" | 2026 | Regulatory guidance |
| 11 | ScienceDirect, Averch-Johnson effect empirical study | 2026 | Academic paper |
| 12 | Acadia Center, "Statement on PURA's Approval of $66M Rate Increase for United Illuminating" | 2026 | Advocacy analysis |

---

## Research Gaps

1. **Quantitative Averch-Johnson modeling:** Empirical estimates of excess capex per percentage point of allowed ROE
2. **State-level PBR scorecard:** Map of which states have adopted PBR, active studies, and remaining cost-of-service
3. **Equity market pricing of PBR transition:** Do PBR-adopting states see different utility valuation multiples?
4. **Utility rate case docket scraper:** Prototype OSINT data aggregation pipeline for regulatory data
