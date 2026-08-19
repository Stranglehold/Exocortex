# Maritime Domain Awareness & AI-Powered Vessel Tracking

**Status:** STABLE
**Created:** 2026-05-23
**Last Updated:** 2026-05-23
**Primary Sources:** 8/8
**Cross-Domain Links:** 4/4

## Overview

Maritime domain awareness (MDA) using AI-powered vessel tracking, satellite imagery analysis, and dark fleet detection for sanctions compliance and supply chain risk monitoring. The sector consolidated rapidly in 2025-2026 with Kpler acquiring Spire Maritime ($241M, April 2025), MarineTraffic, and FleetMon, creating a dominant maritime data ecosystem.

## Key Findings

### AIS Anomaly Detection State of the Art

1. **AIS-LLM (arXiv 2508.07668, Aug 2025)** - Unified framework integrating time-series AIS data with LLMs for vessel trajectory prediction, anomaly detection, and collision risk assessment simultaneously. Shift from isolated detection to multi-task maritime reasoning.
2. **End-to-end maritime threat detection (Nature Sci Rep, 2025)** - Integrated framework combining unsupervised anomaly detection, spatial-temporal deep learning, and domain-specific feature enrichment.
3. **Bi-LSTM spoofed point detection (Maritime Executive, Mar 2025)** - Vessel trajectory route spoofed point detection using AIS data, 85-92% accuracy on intentional AIS manipulation.
4. **Identity spoofing detection (ScienceDirect, 2025)** - Novel signature-based approach for AIS identity spoofing, open-source implementation.

### SAR Vessel Detection & Dark Ship Identification

5. **IEEE SAR vessel detection pipeline (IEEE Xplore, 2025)** - End-to-end dark-vessel detection using Sentinel-1 and ICEYE SAR multi-sensor fusion. F1 >85% with velocity-based refocusing.
6. **DTU Maritime Surveillance (DTU Orbit, Sep 2024)** - Deep learning SAR ship detection benchmark on Sentinel-1: YOLO variants 89% mAP large vessels, 67% small vessels (<30m LOA).
7. **Global Fishing Watch dataset (2024, Nature)** - 23,644+ vessel detections from Sentinel-1 SAR, paired with AIS matching, validating industrial vessel classification.
8. **Dark ship optical+SAR collaboration (MDPI Remote Sensing, 2025)** - Multi-feature association integrating satellite remote sensing and AIS with oriented bounding box detection, addressing 15-20% SAR-AIS mismatch rate.

### Commercial MDA Platform Landscape

- **Kpler ecosystem (2025 consolidation)**: Kpler acquired Spire Maritime ($241M, Apr 2025), MarineTraffic, FleetMon. Unified AIS + SAR + commodity tracking across 40+ markets. Kpler Marine leverages real-time AIS for dark fleet mapping targeting Iran/Russia sanctions.
- **SpaceKnow**: SAR-based automated vessel detection/AIS identification, Lady Mariia case (Aug 2025).
- **Klarety**: Sentinel-1 SAR time-series for dark tanker identification, scored by vessel size/location/confidence.
- **Windward.ai**: AI sanctions compliance platform with OFAC advisory tracking (Apr 2025 guidance).
- **Mitsubishi AI dark fleet tracking**: Japanese satellite-based surveillance for automatic evasive vessel detection.

### OFAC Enforcement Evolution

- **OFAC April 2025 Advisory**: Shift from passive detection to active prevention. Three core evasion tactics: multi-leg STS transfers (3-5 per shipment), AIS manipulation, fraudulent registries.
- **Dark fleet estimate**: 3,000-5,000 vessels globally in sanctions-evading ship-to-ship transfers.
- **HK Law (Feb 2026)**: Maritime sector designated "front line" of US sanctions enforcement across US/EU/UK.
- **Atlantic Council (Dec 2024)**: Comprehensive shadow fleet threat assessment covering North Korean, Iranian, Russian evasion networks.

## Cross-Domain Connections

1. **[ai-sanctions-evasion-detection](ai-sanctions-evasion-detection.md)** - Maritime is primary sanctions evasion vector for oil/energy commodities
2. **[geopolitical-commodity-supply-chain-risk](geopolitical-commodity-supply-chain-risk.md)** - Dark fleet enables commodity supply chain opacity; shipping route disruption risk
3. **[geospatial-intelligence-modern-evolution](geospatial-intelligence-modern-evolution.md)** - SAR vessel detection is direct application of modern geospatial AI
4. **[ml-driven-osint-pipeline-architecture](ml-driven-osint-pipeline-architecture.md)** - MDA platforms exemplify OSINT-to-intelligence pipeline at industrial scale

## Key Insight

**Multi-sensor fusion gap**: AIS-only detection achieves 70-75% coverage but misses intentional dark fleet. SAR-only achieves 85% F1 but has 15-20% false positive rate from sea clutter/ice. Operational sweet spot is AIS+SAR+optical triad with cross-validation, but no single commercial platform offers all three with real-time fusion. Kpler consolidation strategy (AIS->SAR->commodity) points toward this convergence by 2027.
