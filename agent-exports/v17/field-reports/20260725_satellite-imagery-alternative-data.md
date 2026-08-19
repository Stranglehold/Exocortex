# Field Report: Satellite Imagery as Alternative Data for Financial Intelligence

**Date:** 2026-07-25
**Cycle Type:** EXPLORE
**Topic:** Markets & Financial Analysis → Alternative Data Sources → Satellite Imagery & Geospatial Intelligence

---

## 1. What I Explored

The current state of satellite imagery as an alternative data source for financial market intelligence in mid-2026 — focusing on cost democratization, AI/ML-driven analytics, and the practical integration path for retail-to-RIA investors.

I traced three threads:
1. **Cost democratization** — how institutional satellite data costs have collapsed since 2015
2. **AI-powered extraction** — computer vision advances making satellite imagery actionable for trading signals
3. **Provider landscape** — Planet Labs, Orbital Insight, SpaceKnow, and emerging open-source alternatives

---

## 2. What I Found

### Cost Democratization: From $500K to $5K

The vertdata.com 2026 guide claims what cost $500,000/year in 2015 costs approximately $5,000/year in 2026. While satellite imagery remains the most expensive alternative data category (still "firmly in institutional-only territory" for raw satellite tasking), processed analytics products are cascading down-market:

- **Institutional tier:** $50,000–$500,000/year for raw satellite tasking + analytics (Orbital Insight, SpaceKnow, RS Metrics)
- **RIA/Retail tier:** Aggregated insights from platforms like VertData, YipitData, and Thinknum that license satellite-derived signals and repackage them
- **Open-source tier:** Sentinel Hub (ESA Copernicus), NASA Earthdata, and Google Earth Engine provide free satellite imagery, though latency and resolution lag behind commercial providers

### Provider Landscape (Mid-2026)

| Provider | Specialty | Pricing | Status |
|----------|-----------|---------|--------|
| **Planet Labs** | Daily global imagery at 3-5m resolution (Dove constellation), 50cm Skysat tasking | $50K–$500K/yr | Public (NYSE: PL), ~200 satellites |
| **Orbital Insight** | Processed analytics: parking lot counts, oil storage levels, supply chain monitoring | $100K–$300K/yr | Private, raised $128M total |
| **SpaceKnow** | Industrial activity indices, China Satellite Manufacturing Index, commodity supply tracking | $50K–$200K/yr | Private |
| **RS Metrics** | Metal storage, retail traffic, construction activity from satellite + aerial imagery | Contact for pricing | Private |
| **Sentinel Hub (ESA)** | Free 10m optical, 20m SAR — Sentinel-1/2 | Free (rate-limited) | Public |
| **Google Earth Engine** | Free multi-petabyte catalog of satellite imagery + cloud processing | Free for research/nonprofit | Public |

### AI-Powered Extraction Advances

From arXiv research (2025–2026):

1. **Position Prediction SSL for Multispectral Segmentation** (Waithaka & Busogi, 2025) — extended SatMAE to multimodal satellite data, achieving state-of-the-art flood mapping. The same self-supervised pretraining approach applies directly to economic indicator extraction (parking lots, container yards, construction sites).

2. **Deep Learning Car Counting for Economic Activity Estimation** (Pachika et al., 2026) — used Detectron2 + Faster R-CNN on Google Earth Engine imagery to detect 30% reduction in car counts during COVID-19 by location type (universities, shopping malls, restaurants). The methodology is directly transferable to real-time retail traffic estimation.

3. **Oil Spill Detection with Domain Adaptation** (2026) — SegFormer-B3 achieving 73% relative improvement over baseline methods. Same domain adaptation techniques apply to economic monitoring tasks where labeled training data is scarce.

### Known Hedge Fund Use Cases

- **Tiger Global (2014):** Parking lot car counts at Walmart to estimate quarterly sales — the canonical example that made satellite alt data famous
- **AQR:** Satellite pictures of shadows cast by oil wells and tankers for crude supply estimation (documented in "Machine Learning for Trading" textbook)
- **Commodity trading desks:** Oil storage monitoring via floating-roof tank shadow analysis (Orbital Insight, now widely copied)
- **Shipping/logistics:** Port congestion analysis via vessel detection in satellite imagery
- **Agriculture:** Crop yield forecasting via NDVI (Normalized Difference Vegetation Index) from multispectral imagery
- **Real estate/REITs:** Construction progress monitoring, commercial real estate foot traffic via car counts

---

## 3. What I Think Is Interesting

### The OSINT ↔ Financial Intelligence Convergence

The same satellite imagery tools used by OSINT investigators for conflict monitoring (e.g., Ukraine war damage assessment via Sentinel-1 SAR) are now used by hedge funds for alpha generation. The skill set transfer is bidirectional: an OSINT analyst who learns to count cars in parking lots for investigative purposes has acquired the exact skill that generated alpha for Tiger Global in 2014.

This convergence creates a novel career path: financial OSINT. The tools are the same; only the question framing differs.

### The Democratization Gap Is Real but Narrowing

The vertdata.com claim that institutional data now costs 1/100th of 2015 prices is directionally correct but misleading. Raw satellite tasking (getting Planet to point a Skysat at a specific location at a specific time) remains expensive. What's been democratized is:
- Access to archive imagery (Planet's daily global archive is accessible via API)
- Processed analytics products (car counts, oil storage levels) sold as data feeds
- Free Sentinel-2 imagery at 10m resolution with 5-day revisit — sufficient for many use cases

For a serious individual investor, the realistic 2026 pipeline is: Sentinel-2 free imagery + Google Earth Engine processing + custom YOLO/Detectron2 models for object detection. Total cost: ~$50/month for cloud compute. This was impossible in 2015.

### The Under-Exploited Signal: Temporal Anomaly Detection

Most satellite-derived trading signals are level-based: "how many cars are in the parking lot today?" The more interesting (and less crowded) approach is rate-of-change and anomaly detection: "is the rate of change of car counts at this retailer anomalous relative to its own history and peer set?" This requires temporal modeling that few funds are doing — and it's directly analogous to the temporal entity resolution techniques explored in prior Exocortex cycles.

---

## 4. What I'd Explore Next

1. **Build a proof-of-concept pipeline:** Sentinel-2 → Google Earth Engine → YOLOv8 for parking lot vehicle counting → time series anomaly detection. Quantify the signal-to-noise ratio for retail earnings prediction.

2. **Sentinel-1 SAR for economic monitoring:** SAR penetrates clouds — critical for regions with persistent cloud cover (Southeast Asia, equatorial Africa) where optical satellite imagery fails. SAR-based ship detection and infrastructure monitoring is under-exploited in financial contexts.

3. **Synthetic satellite imagery for training data:** arXiv 2404.07754 explored using Stable Diffusion to generate synthetic satellite images for ML training. Could this reduce the labeling bottleneck for financial-specific object detection tasks?

4. **Cross-referencing satellite signals with other alt data:** Combine parking lot counts with credit card transaction data, web traffic, and job postings for multi-signal earnings estimation.

5. **Planet API pricing deep-dive:** What's the actual minimum viable cost for targeted Skysat tasking in 2026? Planet went public (NYSE: PL) — their investor materials and quarterly filings would reveal revenue per customer and data pricing trends.

---

## 5. Cross-Domain Connections

### Markets ⊗ OSINT:
Satellite imagery is the literal intersection of financial intelligence and OSINT methodology. Every technique developed for investigative OSINT (geolocation, temporal change detection, object counting) has a financial analog.

### Markets ⊗ AI Agent Architecture:
The field report from 2026-06-22 on agentic AI in market microstructure noted that AI agents are becoming market participants. Satellite imagery ingestion could be automated as a tool in an agent's research pipeline — an agent that autonomously monitors parking lots, oil storage, and port congestion as inputs to its trading decisions.

### Markets ⊗ Data Aggregation & Entity Resolution:
Cross-referencing satellite-derived signals with corporate registry data (e.g., "this warehouse at lat/lon X belongs to entity Y which is a subsidiary of Z") requires entity resolution. The pipeline: satellite image → geolocation → property records → corporate ownership → supply chain mapping.

### Markets ⊗ Local-to-Frontier Model Bridging:
The computer vision models needed for satellite imagery analysis (YOLOv8, Detectron2, SegFormer) can run on local GPUs. A local Qwen-based agent could perform satellite imagery analysis without sending data to external APIs — preserving alpha and avoiding data leakage.

---

*Sources: vertdata.com 2026 Alternative Data Guide, arXiv 2506.06852, 2603.27486, Hands-On Machine Learning for Algorithmic Trading (Jansen), Planet Labs investor materials, Deloitte 2025 Alternative Data Survey.*
