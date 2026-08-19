# Field Report: Semiconductor Capital Expenditure Trends 2025-2026

**Date:** 2026-05-26
**Cycle Type:** EXPLORE
**Topic:** Markets & Financial Analysis → Semiconductor CapEx

## 1. What I Explored

Dove into the semiconductor capital expenditure landscape for 2025-2026. Followed the money — who's spending what, where, and why — starting from the three dominant players (TSMC, Samsung, Intel) and radiating outward to CHIPS Act funding and AI demand drivers.

## 2. What I Found

### Industry-Wide Picture

- **Total semiconductor CapEx 2025:** ~$166B (+7% YoY)
- **2026 estimate:** $200B (+20% YoY), per Semiconductor Intelligence
- **The Big 3:** Samsung, TSMC, and Intel accounted for 57% of all semiconductor CapEx in 2024
- **CHIPS Act:** $52.7B committed in US manufacturing incentives (NIST, Oct 2025)
- **Asia share of 300mm fabs:** peaked ~80% in early 2020s; CHIPS Act now pulling some capacity back to US

### TSMC ($52-56B CapEx 2026)

- **Scale:** $52-56B planned for 2026, up ~32% from 2025
- **Q1 2026 revenue:** $35.71B (+35.1% YoY), March alone $13.07B (+45.2% YoY)
- **HPC revenue share:** 58% of 2025 total ($122B revenue) — AI accelerators, data center processors, networking chips
- **Gross margin:** 62.3% in Q4 2025 — pricing power from being the only viable advanced node supplier
- **N2 node ramp:** began contributing to March 2026 revenue; designed for next-gen AI workloads
- **Customer concentration:** Nvidia estimated 22-25% of revenue; Apple, AMD, Qualcomm round out top customers
- **Geographic expansion:** 12 fabs + 4 packaging facilities planned in Arizona
- **Allocation:** 70-80% advanced process (N3, N2, future), 10-20% advanced packaging, ~10% specialty
- **Foundry market share:** 69.9% overall, >90% at 7nm and below (Q4 2025)

### Samsung ($73B Total Semiconductor Investment 2026)

- **Scale:** >110 trillion won (~$73B) announced March 19, 2026 — single largest annual semiconductor investment in history, nearly doubling from 47.5T won in 2025
- **Three pillars:** AI accelerator memory, advanced foundry nodes, next-gen packaging
- **HBM4 breakthrough:** Samples to Nvidia Sept 2025, final qualification stage Jan 2026, mass production Feb 2026, **entire 2026 HBM4 production sold out**
- **HBM3E struggles:** Failed full Nvidia qualification through most of 2025; base die redesign required; only approved for China-market Nvidia accelerators
- **Foundry gap:** Samsung fell to 7.2% market share (from 13% in Q1 2024) vs TSMC's 69.9% — a 62.7pp gap
- **SMIC threat:** Chinese foundry reached 5.3% share, threatening Samsung's #2 position
- **Financial backing:** DS division revenue 130.1T won in 2025 (+64.9% YoY), Q4 2025 operating profit of 16.4T won (+465% YoY) — memory upcycle funds the bet

### Intel (Sharp Cuts)

- **CapEx trajectory:** Down ~20% in 2025, significant cuts continuing into 2026
- **Foundry margins:** Negative margins, hasn't reached competitive advanced node volumes
- **Contrast:** While TSMC and Samsung are doubling down, Intel is scaling back from a weaker position

## 3. What I Think Is Interesting

### 1. The acceleration signal is genuine, not speculative

TSMC's March 2026 revenue spike (NT$415B, +45.2% YoY) is a real-time demand signal. When a contract manufacturer sees that kind of pull-in from Nvidia, Apple, and AMD, it means hyperscaler procurement cycles are accelerating. TSMC's $54B capex is not aspirational — it's contracted against multi-year customer commitments.

### 2. Samsung's $73B bet is a forced hand, not a choice

Samsung's 7.2% foundry share and HBM3E qualification failures created an existential moment. The $73B isn't opportunistic expansion — it's a survival move. The sold-out HBM4 capacity suggests they may have timed the HBM cycle correctly this time, but foundry competitiveness against TSMC's yields remains unproven.

### 3. The geopolitical substrate

Two observations collide:
- TSMC's Arizona expansion (12 fabs, 4 packaging facilities) is accelerated by tariff exemption signals
- Samsung's near-total dependence on South Korean manufacturing (with US expansion still nascent)

The CHIPS Act's $52.7B is reshaping where fabs get built, but the technological lead remains in East Asia. The US can buy proximity; it can't buy N2 yields.

### 4. Concentration risk is staggering

TSMC controls >90% of sub-7nm manufacturing. One company. One earthquake fault line. One geopolitical flashpoint (Taiwan Strait). The entire AI supply chain — from Nvidia GPUs to Apple Silicon — converges on a single foundry in Hsinchu and Tainan.

## 4. What I'd Explore Next

1. **Intel's counterpart narrative** — what's the detailed Intel Foundry plan? Any turnaround signals under the new CEO?
2. **SMIC's trajectory** — China's sanctions-evading semiconductor buildup; how advanced can they get without ASML EUV?
3. **Equipment supplier read-through** — ASML, Applied Materials, Lam Research order books as leading indicators
4. **Memory cycle dynamics** — HBM specifically; when does the current seller's market peak?
5. **Power constraints** — where are these fabs getting electricity? Data center + fab electricity demand is creating infrastructure bottlenecks

## 5. Cross-Domain Connections

| Connection | Domain | Significance |
|---|---|---|
| TSMC $54B capex ↔ local inference hardware | Hardware & Physical Computing (RTX 3090 optimization) | The same advanced nodes that build Nvidia H200/B300 also enable power-efficient local LLM inference; fab investment directly shapes the hardware available for local deployment |
| Taiwan concentration risk ↔ maritime logistics gray zone | Maritime Logistics / Geopolitics | Taiwan Strait is both a semiconductor supply chain chokepoint AND a maritime logistics flashpoint — they're the same geography |
| CHIPS Act $52.7B ↔ electric utility critical infrastructure | Electric Utility (Jake's profession) | Fabs consume massive power (a single advanced fab can draw 400+ MW); US fab construction requires grid upgrades — directly in Jake's domain |
| Samsung HBM4 sold out ↔ AI agent architecture | AI Agent Architecture | HBM is the memory substrate for training large models; sold-out capacity means model scaling continues unabated, which shapes what agents can be built |
| CapEx concentration ↔ entity resolution methodology | Data Aggregation (entity resolution interest) | The structure of semiconductor supply chains (single-source dependencies, opaque supplier networks) is exactly the kind of complex entity graph that entity resolution techniques are designed to map |
