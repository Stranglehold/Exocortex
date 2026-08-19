# Field Report: Utility Sector Regulatory Dynamics
**Date:** 2026-05-28  
**Cycle:** EXPLORE  
**Topic Domain:** Markets & Financial Analysis — Utility Sector Regulatory Dynamics

---

## 1. What I Explored

I investigated the current state of electric utility regulation in the United States, focusing on three interconnected threads:

- **Allowed Return on Equity (ROE) trends** — the profit margin regulators set for investor-owned utilities (IOUs), and how they're evolving in 2025–2026.
- **Performance-Based Ratemaking (PBR) adoption** — the shift away from cost-of-service regulation toward incentive-based frameworks.
- **Capital expenditure super-cycle** — the $1.1T infrastructure investment wave and its regulatory implications.

I started from Jake's interests.md directive: "utility sector regulatory dynamics" under Markets & Financial Analysis. This sub-topic had zero prior field reports — the last close exploration was the defense procurement contractor financials report (2026-05-28 05:10 UTC), which touched adjacent territory but not utility regulation itself.

---

## 2. What I Found

### 2.1 Allowed ROE Trends

- **Median allowed ROE for electric utilities in Q1 2025 was 9.75%**, up from 9.70% in full-year 2024 (Gabelli Funds, July 2025). This continues a steady upward drift from the 9.3–9.5% range common in 2020–2022, driven by rising interest rates and utility arguments about increasing cost of capital.
- **Gas utility ROE averaged 9.83%** in Jan–June 2024, marginally higher than electric (PSCdocs, Utah docket exhibits).
- **Rate case volume is declining:** 21 electric ROE authorizations in H1 2024 vs 63 in full-year 2023. This suggests many states have recently settled cases, perhaps locking in ROEs ahead of PBR transitions.
- A 2026 ScienceDirect paper found that **a one percentage point increase in allowed ROE corresponds to a measurable increase in utility capital ownership** — the Averch-Johnson effect is alive and well. Higher ROE directly incentivizes rate base expansion.

### 2.2 PBR Adoption: State-by-State Patchwork

- **Indiana** (2025 IURC report, commissioned by HEA 1007): The legislature mandated a comprehensive PBR study. Recommendations include enabling the Commission to develop PBR proposals, establishing standardized performance metrics, and setting a timeline for Performance Incentive Mechanisms (PIMs) starting with reliability metrics.
- **Connecticut** has been pursuing PBR since at least 2023, with Eversource publicly wary about investor capital attraction under performance-based frameworks. This tension — utility credit stability vs regulatory innovation — is a recurring pattern across states.
- **Virginia** (Dec 2025): GPI/CEG report explored PBR options, noting that current regulation creates a bias toward capex over opex solutions because utilities earn returns only on capital investment.
- **Multi-state PBR mechanisms include:** multiyear rate plans (MRPs), revenue decoupling, capex bias corrections, and PIMs. The RMI Strategic Framework for Utility Cost Control (Feb 2025) provides a taxonomy of these tools and their cost-control implications.
- **FERC jurisdictional tensions** persist: NARUC vs. FERC cases continue to define the boundary between state PUC authority and federal transmission/interstate regulation.

### 2.3 The Capital Expenditure Super-Cycle

- **IOU capital expenditures grew >16% from 2024 to 2025** (EEI Financial Review), with projected **$1.1 trillion cumulative spending 2025–2029**. This is driven by grid modernization, renewable integration, and load growth from electrification and data centers.
- This capex wave intensifies regulatory scrutiny: higher rate base growth means more customer rate pressure, which in turn accelerates the push toward PBR and cost-control mechanisms.
- The Gabelli report notes that **allowed ROE is fundamentally tied to interest rates**: as the cost-of-capital rises, regulators must balance capital attraction (higher ROE) against affordability (lower ROE). This creates a structural tension that PBR frameworks aim to resolve by decoupling utility revenue from pure capex.

---

## 3. What I Think Is Interesting

**The ROE–PBR–Capex triangle is a self-reinforcing loop.** Higher allowed ROE → more capex (Averch-Johnson) → rate increases → public/political pressure → PBR adoption → reduced reliance on ROE-based returns → pushback from utilities and investors → regulatory caution → slower PBR adoption → utilities revert to ROE rate cases → cycle repeats.

The 2025–2026 moment is notable because the capex super-cycle and rising rate pressure are simultaneously forcing the PBR question in multiple states. Indiana's legislative mandate, Connecticut's implementation, and Virginia's exploration represent a quiet but significant shift in the regulatory paradigm — one that could reshape utility financial models over the next decade.

Also: the data fragmentation problem is striking. Allowed ROE data exists in 50 separate PUC docket systems, with no centralized, machine-readable repository. This is a data aggregation and entity resolution problem: at scale, you'd need to scrape PUC dockets, normalize utility names (e.g., "PacifiCorp" vs "PacifiCorp d/b/a Rocky Mountain Power"), and track ROE decisions across jurisdictions.

---

## 4. What I'd Explore Next

1. **Quantitative modeling of the Averch-Johnson effect:** Using the 2026 ScienceDirect paper as a starting point, explore empirical estimates of how much excess capex is induced per percentage point of allowed ROE.
2. **State-level PBR scorecard:** Build a map of which states have adopted PBR, which have active studies, and which remain fully cost-of-service. Cross-reference with rate increase data and utility credit ratings.
3. **Investor signaling in utility equity markets:** How do equity markets price the PBR transition? Are PBR-adopting states seeing lower utility equity valuations, and if so, is that a feature (reduced rent extraction) or a bug (capital flight)?
4. **Data aggregation feasibility:** Prototype a utility rate case docket scraper for a single state (e.g., Indiana) to test the OSINT + entity resolution pipeline for regulatory data.

---

## 5. Cross-Domain Connections

| Connection | Domain | Comment |
|---|---|---|
| **Entity resolution for utility holding structures** | Data Aggregation & Entity Resolution | Tracking a utility across holding companies, operating subsidiaries, and multiple state jurisdictions requires the same entity resolution techniques as tracking shell companies in financial investigations. The utility docket → normalized entity name → holding company → financial data chain is an OSINT problem. |
| **Satellite imagery for capex verification** | Alternative Data / Satellite Imagery | Utility capex claims (new transmission lines, substations) can be verified via satellite imagery — an alternative data technique that bridges Markets and OSINT. |
| **Regulatory capture as an intelligence analysis framework** | History of Intelligence Operations / Counterintelligence | The dynamics of utility influence over PUCs parallel the counterintelligence analysis of competing hypotheses framework: evaluating which regulatory outcomes best explain observed utility behavior and political contributions. |
| **Grid modernization ↔ AI compute demand** | AI Agent Architecture & Local Inference | The data center load growth driving utility capex is partly AI-driven. The regulatory framework that enables (or constrains) grid buildout directly affects the physical infrastructure for AI inference at scale. |
| **SCADA/ICS security in PBR metrics** | Electric Utility & Critical Infrastructure | If PBR incorporates reliability metrics, those metrics depend on secure SCADA/ICS systems. A cyber-physical vulnerability could distort PBR performance metrics, creating a perverse incentive. |

---

**Key sources consulted:**
- Gabelli Funds, "Utilities — U.S." (July 2025)
- IURC Performance-Based Ratemaking Report (May 2025)
- RMI, "A Strategic Framework for Utility Cost Control" (Feb 2025)
- GPI/CEG, "Performance-Based Regulation for Virginia's Electric Utilities" (Dec 2025)
- EEI 2024 Financial Review (Jul 2025)
- Utility Dive, "Investor-owned utilities could spend $1.1T between 2025 and 2029" (Oct 2025)
