# Field Report: Patent Filing Velocity & Job Posting Analysis as Alternative Data

**Date: 2026-05-28**
**Cycle: EXPLORE**
**Interest: Markets & Financial Analysis**
**Sub-topic: Patent Filing Velocity & Job Posting Analytics as Investment Signals**

---

## 1. What I Explored

I investigated two under-explored alternative data categories within the broader alt-data market: (1) patent filing velocity as an innovation-tracking signal, and (2) job posting analytics as a corporate strategy detection tool. The existing wiki page on alternative data sources (STABLE, 200 lines) covers satellite imagery, credit card transactions, and market sizing comprehensively. This report fills a gap: the talent-and-IP signal layer that connects corporate strategy to measurable, public-source data points.

## 2. What I Found

### Market Context (from Exabel/BattleFin 2025 Report)

The alt-data market reached $2.8B in hedge fund spending in 2025 (Neudata), up 17% YoY. Web-scraped datasets account for ~15% of that spending — and both job postings and patent filings are web-scraped signals. 98% of surveyed institutional managers (managing $820B AUM) agreed traditional data is "becoming too slow in reflecting changes in economic activity." 75% believe consumer spending datasets will drive the next edge, but job postings and patent data are the domains where fewer firms compete — making them higher-alpha per dollar spent.

### Patent Filing Velocity

- **Signal mechanism**: Patent filings reveal exactly where companies invest R&D dollars. When a company files 12 patents in battery thermal management, that is a confirmed technology commitment that no earnings call can match (Autobound, 2025).
- **USPTO assignment records**: Match patent assignees to publicly traded entities, enabling quant funds to construct innovation momentum scores.
- **Predictive validity**: Patent filing velocity in specific IPC classes predicts: (a) product launches 12-18 months out, (b) competitive moat building in emerging technology, (c) licensing revenue potential in pharmaceuticals.
- **Provider landscape**: Autobound, Apify (patent scraper actor), IP.com, and direct USPTO/WIPO bulk downloads.
- **WIPO 2025 Indicators**: Global patent filings grew ~2.7% in 2024, driven by Asia (China +3.6%, India +14.5%). Computer technology, digital communication, and electrical machinery remain the top fields.

### Job Posting Analytics

- **Signal mechanism**: Job postings predict revenue growth, M&A activity, and strategic pivots months ahead of earnings calls. Sales-team hiring growth → revenue growth in ~2 quarters; R&D engineer hiring surge → new product development 6-12 months out; geographic expansion hiring → market entry before official announcements.
- **Case study pattern** (JobsPikr): Hedge funds tracked a major tech company's sudden increase in "ASIC design engineer" postings, predicted custom silicon development, and positioned before the product announcement.
- **Provider landscape**: JobsPikr, LinkUp, Revelio Labs, Aura (human capital data), Apify (hiring signal tracker actor), WebSpiderMount, Kadoa.
- **ETF integration**: BMO launched ZHC (Human Capital Factor US Equity ETF) incorporating employee turnover, hiring trends, and workforce culture metrics into a systematic investment strategy — signal moving from hedge fund to retail.

### Integration Challenge

79% of investment managers cite combining datasets from different sources as their top obstacle. Patent filings use IPC/CPC classification systems; job postings use SOC codes or raw text. Aligning both to a ticker, then to financial signal outputs, requires substantial entity resolution infrastructure.

## 3. What I Think Is Interesting

**The convergence of OSINT and alpha generation.** Patent filing analysis is structurally identical to OSINT entity investigation: scrape public records → resolve entities → detect patterns → produce intelligence. The same Python pipelines that trace shell companies across jurisdictions can map corporate innovation networks through patent co-filing. The same sentiment analysis tools that detect disinformation can flag unusual hiring velocity. The boundary between financial intelligence and investigative intelligence is artificial — the data sources and techniques overlap almost completely.

**Patent co-filing as entity resolution testbed.** Companies file patents jointly, creating co-filing graphs that mirror corporate ownership networks. Tracking which entities co-file with which other entities, over time, produces a dynamic innovation network that can predict: (a) acquisition targets (co-filing precedes M&A), (b) supply chain relationships (co-filing between OEMs and suppliers), (c) technology transfer patterns (universities co-filing with corporate R&D). This is entity resolution on a different label — but the graph structure is identical to the corporate registry linking problem.

**Job postings as strategic intent signals.** When a defense contractor posts "submarine propulsion engineer" positions, that is a public signal of classified program direction. When a semiconductor company posts "ASML EUV lithography process engineer" positions, that signals which process node they're targeting. These are intelligence-grade signals available through web scraping — the same techniques used in OSINT investigation applied to financial alpha.

## 4. What I'd Explore Next

1. **Build a patent co-filing → acquisition prediction model prototype**: Scrape USPTO assignment data, construct a co-filing graph, train a link prediction model on historical M&A events. Quantify how much lead time patent signals provide before public M&A announcements.

2. **Job posting sentiment analysis**: Apply NLP sentiment extraction to job posting text — do postings for "urgent" hires, "immediate start" roles, or newly created positions correlate with different company outcomes than routine backfill postings?

3. **Defense sector hiring surveillance**: This is directly in Jake's domain (defense procurement). Track hiring at major defense contractors (Lockheed, Northrop, GD, RTX, L3Harris) for signals of program ramps that haven't been publicly announced.

4. **Cross-reference with the Exocortex knowledge graph**: Map alternative data provider networks and data-source dependency graphs using the same entity resolution tools built for OSINT investigation.

5. **Open-source alternative data pipeline**: Build a Python pipeline that scrapes USPTO, LinkedIn (via public API/proxy), and Indeed for specific companies, merges into a structured ticker-level signal dataset, and backtests against earnings surprises.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **OSINT & Investigation Methodology** | Patent co-filing analysis and job posting surveillance are structurally identical to OSINT entity investigation: scrape public data, resolve entities, detect patterns, produce intelligence. Web scraping techniques (anti-bot evasion, CAPTCHA solving) transfer directly. |
| **Data Aggregation & Entity Resolution** | Aligning patent assignee names to tickers, resolving job posting employer names to corporate entity identifiers, and constructing co-filing graphs are all entity resolution problems. The same Fellegi-Sunter probabilistic matching applies. |
| **Defense Sector Analysis** | Job posting surveillance for defense contractors provides signals of classified program direction. Patent filings in IPC class F41 (weapons) and G01S (radar) track defense technology development patterns. |
| **Geopolitics & Strategic Analysis** | Patent filing velocity by country (WIPO data) reveals national technology priorities. China's surge in semiconductor patent filings (2024: +3.6%) directly maps to US-China technology competition dynamics. |
| **Hardware & Physical Computing** | Semiconductor equipment patent filings (ASML, Tokyo Electron, Lam Research) provide leading indicators for chip manufacturing capability evolution. FPGA inference patent filings track the hardware-AI convergence. |
| **AI Agent Architecture** | The entity resolution pipeline needed for alt-data integration is the same architecture needed for autonomous agent memory and knowledge graph construction. Building one builds the other. |

---

## Sources

- Exabel/BattleFin (2025). *Alternative Data Buy-side Insights & Trends 2025*. 130 fund managers, $820B AUM.
- Neudata (2025). *The Future of Alternative and Market Data 2025*.
- Autobound (2025). *Patent Filing & R&D Investment Signals*. USPTO assignment tracking.
- WIPO (2025). *World Intellectual Property Indicators 2025*.
- Lowenstein Sandler (2025). *Alt Data Report 2025*. Survey of private fund managers.
- Kadoa (2025). *Alternative Data for Hedge Funds: A Practical Guide*.
- JobsPikr / LinkUp / Revelio Labs — job posting analytics providers.
- Apify — web scraping actors for investment alternative data.
