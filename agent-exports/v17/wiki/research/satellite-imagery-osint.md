# Satellite Imagery Analysis for OSINT

**Status:** STABLE
**Created:** 2026-07-04
**Domain:** OSINT & Investigation Methodology
**Last Updated:** 2026-07-04

---

## Overview

Satellite imagery analysis is a cornerstone of modern OSINT investigation, enabling remote verification of ground truth, infrastructure monitoring, military activity tracking, environmental change detection, and cross-referencing of claims with visual evidence. The IC OSINT Strategy 2024-2026 formally elevated satellite-enabled OSINT as a professional intelligence discipline, recognizing that Earth imagery, maritime location data, aviation broadcasts, weather feeds, and commercial geospatial products now sit squarely within the publicly and commercially available information stream (ODNI/CIA, March 2024).

Three structural strengths distinguish satellite-enabled OSINT from other OSINT categories:
1. **Geographic precision** — pixel-level coordinates provide objective spatial reference
2. **Repeat coverage** — daily revisit rates from commercial constellations enable temporal analysis
3. **Shared visual record** — time-stamped imagery provides a physical starting point that cannot be disputed the way a political statement can

Satellite-enabled OSINT sits between public transparency and professional intelligence work. A freely available Landsat image may support climate research; a commercial SAR image may reveal flood extent through cloud cover; a vessel's AIS broadcast may enable maritime safety analysis. In each case, public or commercial availability does not remove the need for lawful collection, privacy controls, and careful interpretation.

---

## Imagery Sources

### Commercial High-Resolution
| Provider | Constellation | Resolution | Revisit | Notes |
|----------|--------------|------------|---------|-------|
| Maxar | WorldView Legion (6 sats) | 30 cm | Daily | Government/military heritage; taskable |
| Planet Labs | SkySat (21 sats) + Dove (150+) | 50 cm / 3m | Daily+ | Largest commercial fleet; subscription model |
| Airbus Defence | Pléiades Neo (4 sats) | 30 cm | Daily | European sovereign alternative |
| BlackSky | BlackSky (14+ sats) | 50 cm | Sub-hourly | Rapid tasking focus |
| Satellogic | ÑuSat | 70 cm | Daily | Lower-cost imagery |

### Open-Access (Scientific/Government)
| Source | Sensor | Resolution | Revisit | Availability |
|--------|--------|------------|---------|-------------|
| Copernicus Sentinel-2 | Multispectral (13 bands) | 10 m | 5 days | Free — Sentinel Hub, AWS |
| USGS Landsat 8/9 | Multispectral (11 bands) | 15-30 m | 8 days | Free — EarthExplorer, GEE |
| Copernicus Sentinel-1 | C-band SAR | 5-20 m | 6 days | Free — all-weather, day/night |
| NASA MODIS | Multispectral (36 bands) | 250m-1km | Daily | Free — large-area monitoring |

### SAR (Synthetic Aperture Radar) — All-Weather
| Provider | Constellation | Band | Resolution | Notes |
|----------|-------------|------|------------|-------|
| Capella Space | Capella (10+ sats) | X-band | 50 cm | Highest-res commercial SAR |
| ICEYE | ICEYE (30+ sats) | X-band | 50 cm | Maritime surveillance focus |
| Umbra | Umbra (8+ sats) | X-band | 25 cm | US-licensed commercial |
| Sentinel-1 | C-band | C-band | 5-20 m | Free, open access |

SAR's key advantage for OSINT: penetrates clouds, smoke, and darkness — critical for disaster response, conflict monitoring, and maritime domain awareness where optical imagery fails.

---

## Analysis Techniques

### Change Detection
Temporal comparison of imagery to identify what changed between two dates. Core methodologies:
- **Temporal differencing**: pixel-level subtraction of co-registered images
- **ML-based change detection**: dual-stream convolutional networks with fusion (DSC-AD-SC achieves Dice Similarity Score 0.9284 on Onera dataset)
- **Applications**: construction monitoring, deforestation tracking, military deployment detection, disaster damage assessment

### Object Detection & Counting
Identifying and counting discrete objects (aircraft, ships, vehicles, buildings):
- **Single-stage detectors** (YOLO variants): faster prediction, good for large objects (50-250m)
- **Two-stage/multi-stage detectors** (Faster R-CNN): higher accuracy for small objects like cars
- **Oriented object detection**: bounding boxes with arbitrary rotation for remote sensing objects (ships, vehicles)
- **Foundation models**: YOLO-World (open-vocabulary), SAM (segment anything), DINO (self-supervised)

### Geolocation Verification
Cross-referencing imagery with other data to confirm or disprove location claims:
- Shadow/sun-angle azimuth calculation for time-of-day verification
- Terrain feature matching between ground photos and satellite views
- Infrastructure matching (road networks, building footprints, distinctive structures)
- Integration with AIS (maritime), ADS-B (aviation), and social media geotags

### Multispectral Analysis
Leveraging non-visible spectral bands for intelligence:
- **Vegetation indices** (NDVI): detect concealed structures under canopy, monitor agricultural activity
- **Thermal infrared**: identify industrial activity, power plant operation, military vehicle heat signatures
- **SAR coherence change**: detect vehicle tracks, excavation, construction even through clouds

### Maritime Domain Awareness
Satellite-based ship detection and monitoring:
- AIS (Automatic Identification System) correlation with satellite imagery
- Dark vessel detection — ships operating with AIS disabled detected via SAR
- Port activity monitoring via vessel count changes over time
- Oil storage measurement via floating-roof tank shadow analysis

---

## AI & Machine Learning for Satellite OSINT

### Foundation Models for Remote Sensing
- **SatMAE**: masked autoencoder pretrained on multispectral satellite imagery
- **GeoLLM**: large language models fine-tuned for geospatial reasoning
- **Panopticon**: foundation model for panoptic segmentation in remote sensing
- **Clay Foundation Model**: open-source MAE-based model trained on diverse Earth observation data

### Detection & Segmentation Frameworks
- **YOLO-World**: open-vocabulary object detection enabling zero-shot queries ("find all aircraft carriers")
- **SAM (Segment Anything Model)**: zero-shot segmentation useful for delineating building footprints, water bodies
- **DINO/DINOv2**: self-supervised visual features for similarity search across imagery archives

### Super-Resolution
Enhancing low-resolution open-source imagery to extract additional detail:
- Diffusion-based super-resolution models for satellite imagery
- ESRGAN variants adapted for remote sensing
- Trade-off: super-resolution can fabricate plausible-but-false detail — always verify against original imagery

---

## OSINT Workflow Integration

### Multi-Source Correlation Pipeline
Satellite imagery rarely answers questions alone. The effective OSINT workflow integrates:
1. **Imagery** (satellite) — provides spatial ground truth
2. **Signals data** (AIS, ADS-B, radio) — provides identity and movement
3. **Social media** (Twitter/X, Telegram, TikTok) — provides context and timestamp anchors
4. **Public records** (corporate registries, shipping manifests) — provides ownership
5. **News media** — provides event framing and leads

### Verification Tradecraft
Per the New Space Economy guide (May 2026), verification matters more than image access:
- Every satellite image finding must be compared with at least one independent source
- Cloud cover, shadows, revisit gaps, sensor limits, and confirmation bias all distort interpretation
- Responsible OSINT requires legality, privacy safeguards, source checks, and context
- Time-stamped imagery provides a physical starting point — not a conclusion

### Bellingcat Methodology Adaptations
- **Chronolocation**: using satellite imagery time-series to establish when an event occurred
- **Geolocation triangulation**: matching terrain features across multiple satellite image angles
- **Open-source cross-referencing**: comparing commercial imagery against Sentinel open data

---

## Legal, Licensing, and Privacy Boundaries

- **US**: Commercial satellite imagery governed by NOAA licensing; 30cm resolution floor for US-licensed operators
- **EU**: GDPR applies to imagery containing identifiable individuals; Sentinel data is free and open under Copernicus license
- **Privacy**: high-resolution imagery can identify vehicles, building access patterns, and personal activity — ethical OSINT practitioners consider downstream privacy impacts
- **Commercial licensing**: Maxar/Planet imagery is licensed, not owned; redistribution restrictions apply
- **IC OSINT Strategy 2024-2026**: mandates lawful collection, privacy controls, and professional tradecraft

---

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[ip-geolocation-network-attribution]] | IP geolocation and satellite imagery both provide spatial attribution for OSINT investigations — combining them triangulates digital and physical presence |
| [[reverse-image-search-visual-osint]] | Satellite imagery and reverse image search share geolocation verification methodology — terrain matching, structure identification, and temporal analysis |
| [[timeline-reconstruction-osint]] | Satellite temporal analysis (change detection) directly feeds timeline reconstruction by providing precise event windows |
| [[maritime-logistics-gray-zone]] | Satellite SAR enables dark vessel detection and port monitoring — core to maritime OSINT and sanctions evasion tracking |
| [[geopolitics-strategic-analysis]] | Commercial satellite imagery transformed geopolitical analysis by enabling independent verification of military deployments, construction at disputed sites, and sanctions compliance |
| [[data-aggregation-entity-resolution]] | Satellite-derived locations feed into entity resolution pipelines — a ship's observed berth + AIS data + corporate registry = entity linkage |
| [[anti-bot-evasion]] | Satellite imagery APIs (Planet, Maxar) require authentication and rate-limit management — anti-detection patterns apply to large-scale automated imagery collection |
| [[alternative-data-sources]] | Satellite imagery is a primary alternative data source for financial analysis — parking lot counts, oil storage monitoring, crop yield estimation |

---

## Tools & Platforms

| Tool | Type | Use Case |
|------|------|----------|
| Sentinel Hub / EO Browser | Web-based | Browse and analyze Sentinel/Landsat imagery |
| Google Earth Engine | Cloud platform | Large-scale geospatial analysis with free data catalog |
| QGIS | Desktop GIS | Georeferencing, change detection, custom analysis |
| SnapPlanet | Mobile/web | Planet SkySat and Dove imagery access |
| Zoom.Earth | Web | Near-real-time satellite imagery viewer |
| Soar.Earth | Web | Community-contributed satellite imagery with annotations |
| NASA Worldview | Web | MODIS/VIIRS near-real-time imagery |

---

## References

1. ODNI/CIA. "Intelligence Community Open Source Intelligence Strategy 2024-2026." March 2024.
2. New Space Economy Staff. "Open Source Intelligence Using Satellite-Enabled Sources." May 7, 2026. [Link](https://newspaceeconomy.ca/2026/05/07/open-source-intelligence-using-satellite-enabled-sources/)
3. ShadowDragon. "OSINT Techniques: Expert Tactics for Investigators (2026)." [Link](https://shadowdragon.io/resources/osint-techniques/)
4. Groener et al. "A Comparison of Deep Learning Object Detection Models for Satellite Imagery." arXiv:2009.04857.
5. "Environmental Monitoring and Change Detection Using Dual-Stream Convolutional Networks with Fusion Techniques on Satellite Imagery." Global NEST Journal, 2025.
6. Wen et al. "Oriented Object Detection in Optical Remote Sensing Images Using Deep Learning: A Survey." arXiv:2302.10473v6.
