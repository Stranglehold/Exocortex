# Field Report: Satellite Imagery for Financial Analysis

**Date:** 2026-07-14
**Topic:** Markets & Financial Analysis — Alternative Data Sources
**Cycle:** EXPLORE

---

## 1. What I Explored

Satellite imagery as an alternative data source for quantitative finance: how hedge funds and algorithmictraders use Earth observation data to gain informational leads before earnings, government reports, and macroeconomic releases. I focused on four canonical use cases (parking lot counts, oil storage shadow analysis, NDVI crop health monitoring, maritime AIS/vessel tracking), the current vendor landscape in 2026, and recent developments in SAR (Synthetic Aperture Radar) and AI-based processing.

This thread was chosen because Markets & Financial Analysis was the least-recently-explored active interest (last field report 2026-07-09 on Fed TGA/reserve demand curves). Patent filing velocity, job posting alt-data, and quantitative techniques have prior coverage; satellite imagery for finance had not had a dedicated EXPLORE cycle.

## 2. What I Found

### Market Size
- The satellite data market for finance is estimated at over \$500 million annually in 2026.
- The broader alternative data market is projected to reach \$17.4 billion globally in 2026 (Clymin).
- The geospatial intelligence market overall continues rapid growth driven by AI-enabled satellite imagery, SAR data, drone mapping, and cloud processing.

### Core Use Cases

**Retail Foot Traffic (Parking Lot Counts):** The pioneer application. RS Metrics started selling parking lot counts derived from high-resolution satellite imagery in the early 2010s. Orbital Insight scaled this with computer vision, counting vehicles across thousands of locations and aggregating into company-level signals. The logic: more cars = higher revenue. Studies show parking lot signals can predict earnings surprises 1-2 weeks before announcements.

**Oil and Commodity Storage Monitoring:** A watershed moment came during the 2020 Saudi-Russia oil price war. Funds using satellite-derived estimates of global crude oil inventories (measuring floating-roof tank shadows via SAR) had a multi-week informational lead on the market. Companies like Kayrros and Ursa Space Systems now process SAR imagery weekly to estimate global oil inventories — far more frequent than EIA monthly reports. Discrepancies between satellite-estimated storage and official reports signal supply surprises.

**Agricultural Crop Health (NDVI):** The Normalized Difference Vegetation Index (NDVI = (NIR - Red) / (NIR + Red)) uses near-infrared and visible red reflectance to measure vegetation health. Values above 0.6 indicate healthy, dense vegetation. Traders use NDVI time series to forecast crop yields for corn, soybeans, wheat weeks before USDA WASDE reports. This is one of the most mature and technically sound satellite signals.

**Maritime Traffic and Port Activity:** Satellite imagery combined with AIS (Automatic Identification System) transponder data enables monitoring of global shipping and supply chain activity. Traders count vessels in port, measure congestion, and track commodity flows to nowcast trade balances and industrial production. PierSight is building a SAR satellite constellation for persistent maritime domain awareness (launching from 2026).

### Vendor Landscape 2026

| Vendor | Specialty | Data Type | Notable 2026 Events |
|--------|----------|-----------|---------------------|
| Planet Labs | Daily global imagery, Dove constellation (200+ satellites), Owl next-gen | Optical 3-5m | AI-Powered Earth Intelligence; continuous deployment |
| Orbital Insight | Parking lots, oil storage analytics | Processed signals | Pioneering company; established hedge fund client base |
| Kayrros | Energy, emissions monitoring | SAR + optical | Key player in commodity storage estimation |
| Ursa Space | SAR-based oil storage, global inventories | SAR analytics | Weekly inventory estimates |
| SkyFi | Geospatial marketplace, Earth Intelligence Platform | Multi-provider aggregation | \$12.7M Series A (2026); DNV Ventures investment (Jan 2026); financial services vertical |
| PierSight | Maritime domain awareness | SAR constellation (launching 2026) | All-weather, day/night vessel monitoring |
| ICEYE | SAR satellite constellation, ML Center of Excellence (Luxembourg) | SAR | Expanding ML/computer vision capabilities for finance |
| Ubotica | Space AI, live maritime intelligence | On-orbit AI processing | \$11M raise (June 2026) |

### Key Technical Developments 2025-2026

1. **SAR becoming the dominant modality:** SAR penetrates clouds, smog, rain, and works at night — critical for consistent monitoring of assets in tropical regions (agriculture) and high-latitude areas (oil fields, shipping lanes). SAR satellite constellations (ICEYE, Capella, PierSight) are rapidly expanding revisit frequency.

2. **AI/ML processing moving on-orbit:** Companies like Ubotica are deploying AI inference directly on satellites, reducing data downlink needs and latency. This enables near-real-time alerts rather than batch processing.

3. **Multi-modal fusion is the competitive moat:** The value has shifted from "do you have satellite data?" to "how well can you combine satellite with other alternative data?" — e.g., fusing SAR oil storage estimates with AIS vessel tracking, or combining parking lot counts with credit card transaction panels.

4. **Cost democratization:** Subscription models now cover the entire globe. What once cost \$1,000-\$10,000 per tasked image is now available through API access.

5. **Regulatory tailwinds:** DNV Ventures' investment in SkyFi signals institutional confidence in geospatial finance. Financial services is an explicit vertical for SkyFi, Planet, and others.

### Alpha Persistence Assessment

Per the Hands-On ML for Algorithmic Trading book and alternative data research:
- Parking lot / foot traffic: Medium-high alpha (frequent refresh, some data moat)
- Oil storage (SAR): High (processing barrier, regulatory gap vs official reports)
- Crop health (NDVI): Medium (widely available, but processing edge matters)
- Maritime/AIS: Medium (AIS is public, but SAR+AIS fusion is proprietary)
- Social/sentiment: Low (rapidly arbitraged)
- IoT sensor telemetry: High (collection infrastructure moat)

## 3. What I Think Is Interesting

**The informational lead is structural, not temporary.** The 2020 oil price war proved that satellite-derived signals can give a multi-week lead over official government statistics. This is not a one-off — it's inherent in the fact that satellites image continuously while agencies report monthly or quarterly. As long as the EIA reports monthly and satellites image weekly, the lead persists.

**The SAR revolution is democratizing persistent monitoring.** Optical imagery is limited by clouds and night — roughly 67% of Earth is cloud-covered at any moment. SAR eliminates that constraint. When PierSight's constellation achieves full operational capability (targeting 2026-2027), persistent monitoring of all maritime activity becomes feasible. This is a structural shift in what's knowable about global trade.

**The gap between available data and processed signals remains large.** Dozens of satellite constellations produce petabytes of raw imagery daily, but the processing pipelines to convert pixels into tradable signals are still being built. This is where quantitative hedge funds have an edge: the ability to build internal processing pipelines for specific signals. However, as platforms like SkyFi democratize access and analytics, the alpha from raw satellite data will decay — shifting value to signal combination and proprietary processing.

**A philosophical connection to OSINT methodology:** Satellite imagery for finance is structurally identical to satellite imagery for intelligence analysis — you're measuring physical-world activity before it appears in official reports. The analytical tradecraft transfers directly: source reliability assessment, multi-source corroboration, temporal pattern analysis, and calibration against ground truth.

## 4. What I'd Explore Next

1. **Quantify the informational lead:** Backtest parking lot signals against earnings surprises across different sectors (retail, restaurants, big-box). Is the signal stronger for discretionary vs. staples?
2. **Build a satellite data fusion framework:** Combine SAR oil storage estimates, AIS tanker tracking, and EIA data to estimate supply/demand imbalances in crude oil markets.
3. **Evaluate free/low-cost satellite imagery APIs:** Sentinel Hub (ESA Copernicus), NASA GIBS, Planet's NICFI satellite data program. Can meaningful signals be extracted without paid subscriptions?
4. **Explore on-orbit AI processing:** Ubotica and others are putting ML models directly on satellites. What does the latency reduction mean for high-frequency trading strategies?
5. **Cross-reference satellite signals with alternative data from job postings and patent filings:** If satellite imagery shows a company expanding physical footprint (construction monitoring) AND job postings show hiring in new geography AND patent filings show innovation, that's a powerful confluence signal.

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[job-posting-alt-data-forecasting]] | Both are leading indicators that precede official statistics; structural isomorphism in signal processing pipeline (collect → clean → aggregate → predict) |
| [[patent-filing-velocity-economic-indicator]] | Multi-modal fusion: satellite expansion monitoring + patent filing growth + job posting velocity = corporate growth signal |
| [[human-investigation-osint]] | Satellite imagery analysis for OSINT (geolocation, military activity monitoring) uses identical technical skills (SAR interpretation, shadow analysis, change detection) |
| [[energy-commodity-dynamics]] | SAR oil storage monitoring directly informs crude oil supply/demand models; tanker tracking maps to LNG export terminal activity |
| [[rare-earth-supply-chains]] | Satellite monitoring of mining operations and processing facilities; SAR can track operational status of Mountain Pass, Lynas, and Chinese rare earth facilities |
| [[federal-reserve-operations]] | Satellite-derived nowcasting of economic activity (port congestion, factory activity, retail foot traffic) provides alternative data for Fed decision-making |
| [[bridging-local-frontier-model-performance]] | Processing satellite imagery at the edge (on-device or on-premises) enables privacy-preserving financial analysis; local models could run NDVI or object detection pipelines without sending data to cloud APIs |
| [[ai-agent-architecture-local-inference]] | The multi-modal fusion problem (optical + SAR + AIS + credit card data) is structurally isomorphic to Exocortex knowledge fusion — combining heterogeneous data sources with different reliability profiles |

---

## 6. Sources

1. PapersWithBacktest, "Satellite Imagery for Trading: A Complete Guide" (2026)
2. VertData, "Alternative Data for Hedge Funds: What It Is and How to Use It" (2026 Guide)
3. Clymin, "Alternative Data Providers Comparison 2026"
4. SkyFi, "\$12.7M Series A Funding Announcement" (2026) + DNV Ventures investment (Jan 2026)
5. ICEYE, "Machine Learning Center of Excellence in Luxembourg" press release
6. PierSight, "How Hedge Funds Can Use SAR + AIS Data" blog
7. Fortune Business Insights, "Geospatial Intelligence Market Size, Share | Growth Report, 2034" (July 2026)
8. Jansen, *Hands-On Machine Learning for Algorithmic Trading*, Chapter 3: Alternative Data for Finance (Packt, 2018)
9. International Banker, "How Satellite Imagery Is Helping Hedge Funds Outperform" (2025)
10. Ubotica, "\$11M Raise for Space AI and Live Maritime Intelligence" (June 2026)
