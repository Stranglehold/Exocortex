# Software-Defined Radio for OSINT Investigation

**Status:** DRAFT
**Created:** 2026-07-17
**Last Updated:** 2026-07-17

## Overview

Software-defined radio (SDR) replaces hardware-based radio components (modulators, demodulators, filters) with software, enabling reception and analysis of a wide spectrum of radio frequency (RF) signals. For OSINT investigators, SDR provides a low-cost, accessible entry point into signals intelligence collection previously reserved for nation-state actors. A $25 RTL-SDR USB dongle can capture aircraft ADS-B transponders, drone RemoteID broadcasts, maritime AIS, IoT/smart meter emissions, and a universe of RF signals that reveal physical-world activity. Combined with AI/ML classification, SDR becomes a practical OSINT collection layer bridging the gap between open-source intelligence and traditional SIGINT.

## Hardware

### Entry-Level Receivers
- **RTL-SDR (~$25):** Receive-only, 24 MHz–1.7 GHz. Based on Realtek RTL2832U chip originally for DVB-T TV. Ideal for ADS-B (1090 MHz), ACARS, AIS (161.975/162.025 MHz), POCSAG/FLEX pager, FM broadcast, NOAA weather satellites (137 MHz), and ISM band devices.
- **NooElec NESDR (~$30):** Improved RTL-SDR variant with better temperature-stable oscillator and SMA connector.

### Mid-Range Transceivers
- **HackRF One (~$300):** Half-duplex transceiver, 1 MHz–6 GHz, 20 MHz bandwidth. Can both receive and transmit. Popular for signal replay attacks, GPS spoofing research, and wideband spectrum sweeps.
- **LimeSDR Mini (~$200):** Full-duplex, 10 MHz–3.5 GHz, 30.72 MHz bandwidth. FPGA-based for custom DSP.

### Advanced SDR Arrays
- **KrakenSDR (~$200):** 5-channel coherent RTL-SDR array enabling radio direction finding (bearing estimation) via phase-coherent processing and passive radar (detect aircraft/drones using FM broadcast reflections — zero transmission). Target acquisition without active emission.
- **USRP B210:** Professional-grade, 70 MHz–6 GHz, 56 MHz instantaneous bandwidth. Used in academic and defense SIGINT research.

### Antennas
- **Wideband whip/discone:** General scanning, omnidirectional.
- **Directional (Yagi, log-periodic):** Bearing estimation, targeted collection.
- **ADS-B collinear:** Optimized for 1090 MHz aircraft tracking.

## Software Ecosystem

### Spectrum Analysis & General-Purpose
| Tool | Platform | Notes |
|------|----------|-------|
| Gqrx | Linux/macOS/Windows | GUI-based, GNU Radio backend, waterfall display, AM/FM/SSB demodulation |
| SDR++ | Cross-platform | Lightweight, modular, multi-VFO, supports RTL-SDR, HackRF, Airspy |
| SDRangel | Cross-platform | Swiss-army knife, dedicated decoders for ADS-B, AIS, DMR, POCSAG, APT, Doppler |
| GNU Radio | Linux/macOS | Programmable DSP framework, graphical blocks (GRC) or Python/C++ flowgraphs |

### Specialized OSINT Tools
| Tool | Purpose |
|------|---------|
| dump1090 / readsb | ADS-B aircraft tracking — altitude, speed, position, callsign |
| rtl_433 | Decode 433 MHz ISM band — weather stations, tire pressure sensors, doorbells, smart meters |
| Kalibrate / gr-gsm | GSM base station scanning and downlink capture |
| rtl_power + heatmap.py | Spectrum survey over time — identify active frequencies in an area |
| iNTERCEPT | Web-based SIGINT platform (2026): pager decoding, ADS-B, WiFi scanning, modular plugin architecture |
| SatDump | NOAA/Meteor weather satellite image decoding (APT, LRPT, HRPT) |
| OpenWebRX | Web-based multi-user SDR receiver — remote spectrum access |

## OSINT Applications

### 1. Aircraft & Maritime Tracking
ADS-B (Automatic Dependent Surveillance-Broadcast) is unencrypted and broadcast continuously by most aircraft. With a $25 RTL-SDR and dump1090, an investigator can track private jets, military transports (when ADS-B is active), and government flights in real time. Combined with aircraft registration databases, this enables:
- Corporate jet movement analysis for M&A intelligence
- Sanctions evasion detection (aircraft tail number changes, transponder manipulation)
- Disaster response monitoring (air tanker activity)

AIS (Automatic Identification System) for maritime vessels operates on 161.975/162.025 MHz and can be received by RTL-SDR with rtl-ais. Vessel positions, identity, course, and speed are broadcast unencrypted — enabling shadow fleet tracking and port activity monitoring.

### 2. Drone Detection via RemoteID
FAA RemoteID (effective September 2023) requires drones to broadcast identification and location via Wi-Fi or Bluetooth. RTL-SDR with appropriate decoders can capture RemoteID signals, enabling:
- Identification of unauthorized drone activity near critical infrastructure
- Mapping of drone survey operations (corporate espionage indicator)
- Correlation with satellite imagery for ground-truth verification

### 3. IoT & Smart Meter Emissions
Devices in the 315/433/868/915 MHz ISM bands (weather stations, TPMS sensors, smart meters, wireless doorbells, alarm sensors) broadcast identity and data. rtl_433 decodes over 200 device protocols. OSINT value:
- Smart meter density mapping for demographic analysis
- Critical infrastructure sensor identification (SCADA telemetry leakage)
- Corporate facility RF fingerprinting (unique device composition per location)

### 4. Signal Fingerprinting & Anomaly Detection
Every transmitter has a unique "RF fingerprint" — unintentional modulation characteristics from manufacturing variances. With sufficient bandwidth and ML classification, SDR can:
- Identify specific transmitters across multiple locations (entity resolution via RF)
- Detect anomalies (new transmitters appearing at a monitored site)
- Track mobile transmitters with KrakenSDR direction-finding arrays

### 5. Emergency Services & Pager Monitoring
Fire/EMS pager systems (POCSAG/FLEX) often broadcast unencrypted on VHF/UHF. While legal boundaries vary, monitoring provides real-time incident awareness in disaster scenarios.

## AI/ML Integration

The transition from hand-coded demodulators to deep learning enables autonomous signal classification:
- **Spectrogram-to-classification:** CNN/ViT models trained on IQ constellation diagrams identify modulation type (QPSK, QAM, OFDM), protocol, and device type.
- **Self-supervised learning:** RadCharSSL (2025) reduces labeled data dependency for radar recognition — applicable to OSINT signal classification with minimal ground truth.
- **Commercial systems:** Inference Systems (UK) and MAG Aerospace offer AI-powered SIGINT analysis on COTS SDR hardware.
- **AI-powered recon kit:** Medium (2026) documented HackRF + AI spectrogram model pipeline for rapid signal identification.

## Investigation Workflow

| Phase | Activity | Tools |
|-------|----------|-------|
| 1. Planning | Define frequency bands of interest, legal boundaries, local RF environment survey | FCC ULS database, RadioReference DB |
| 2. Collection | Wideband spectrum sweep, targeted narrowband recording | rtl_power, Gqrx, rtl_sdr |
| 3. Processing | Demodulation, decoding, protocol parsing | SDRangel, rtl_433, dump1090 |
| 4. Analysis | Entity identification, signal fingerprinting, anomaly detection | Python (NumPy/SciPy/sklearn), GNU Radio |
| 5. Reporting | Timeline reconstruction, correlation with other OSINT sources | Neo4j graph, Kepler.gl maps |

## Legal & Ethical Considerations

- **United States:** Interception of unencrypted radio communications is generally legal under 18 U.S.C. § 2511(2)(g) if the transmission is "readily accessible to the general public." Encrypted communications are protected regardless. Cellular bands (700/800/1900/2100/2300/2500 MHz) are specifically prohibited.
- **European Union:** GDPR does not directly regulate RF interception, but derived personal data (e.g., aircraft tail numbers correlated with owner identities) may engage data protection obligations.
- **Transmitting:** HackRF transmission requires appropriate licenses (amateur radio, experimental). Unauthorized transmission can cause harmful interference and is illegal in most jurisdictions.
- **Operational security:** Active SDR collection at a target location may be detected by RF monitoring systems. Use passive techniques (receive-only) and KrakenSDR passive radar to minimize detection risk.

## Exocortex Integration

SDR sensors provide a physical-world collection layer feeding into Exocortex OSINT pipelines:
- **Sensor node → MQTT → InfluxDB → Exocortex knowledge graph:** Custom PCB sensor networks with RTL-SDR modules streaming decoded signals for autonomous agent correlation.
- **RF spectrum monitoring:** Agent-initiated SDR queries ("scan 1090 MHz for new aircraft callsigns") via structured API.
- **Direction finding:** KrakenSDR bearing data integrated with geospatial analysis for transmitter location triangulation.
- **Entity resolution:** RF fingerprint as entity attribute — link transmitters across locations, detect spoofing.

## Cross-Domain Connections

| Connection | Wiki Page | Description |
|-----------|-----------|-------------|
| SIGINT evolution | [[sigint-evolution]] | SDR democratizes SIGINT: from nation-state collection to $25 dongle — the platform shift from custom hardware to COTS+software |
| Custom PCB design | [[custom-pcb-design-sensor-networks]] | SDR sensor nodes with MQTT integration feed physical-world data into Exocortex pipelines |
| Metadata analysis | [[metadata-analysis-osint]] | RF signal metadata (frequency, modulation, timing, location) is structurally isomorphic to document/EXIF metadata analysis |
| OSINT reconnaissance | [[osint-reconnaissance-automation-toolchain]] | SDR adds RF domain to automated OSINT collection pipelines |
| Counterintelligence | [[counterintelligence-analysis-frameworks]] | RF deception (spoofing, replay attacks, ghost transmitters) requires CI-ACH adversarial hypothesis testing |
| UAV/drone warfare | [[drone-warfare-autonomous-weapons-proliferation]] | RemoteID interception and drone detection via SDR for OSINT threat awareness |
| Satellite imagery | [[satellite-imagery-osint]] | NOAA weather satellite image reception via SDR — direct satellite OSINT without internet dependency |
| Hardware acceleration | [[fpga-inference-acceleration]] | FPGA-based SDR DSP pipelines for real-time wideband signal processing |
| Maritime logistics | [[maritime-logistics-gray-zone]] | AIS reception for shadow fleet tracking and ship-to-ship transfer detection |
| Energy commodities | [[energy-commodity-dynamics]] | ADS-B monitoring of oil tanker support aircraft for supply chain intelligence |

## Key Insight

SDR represents the convergence point between hardware, software, and intelligence — and the key OSINT insight is that **RF emissions are metadata about physical-world entities.** An aircraft's ADS-B signal is not just a position report; it is an entity identity broadcast that can be correlated with corporate registries, flight plans, and sanctions lists. A drone's RemoteID packet is not just a compliance signal; it is a real-time location of an aerial sensor platform. SDR closes the loop: OSINT identifies what to look for, SDR collects the RF ground truth, and entity resolution connects the emitter to the organization. For autonomous agents, SDR provides a direct sensory input channel — the agent can "listen" to the physical world.

## Tool Inventory

| Category | Tools |
|----------|-------|
| Spectrum analysis | Gqrx, SDR++, SDRangel, rtl_power |
| Aircraft (ADS-B/ACARS) | dump1090, readsb, acarsdec, Virtual Radar Server |
| Maritime (AIS) | rtl-ais, AIS-catcher, OpenCPN |
| IoT/ISM (315/433/868/915 MHz) | rtl_433, rtl_433 discover |
| Paging (POCSAG/FLEX) | multimon-ng, PDW |
| GSM/4G/5G | Kalibrate, gr-gsm, srsRAN |
| Weather satellites | SatDump, WXtoIMG, noaa-apt |
| Direction finding | KrakenSDR (coherent), RDFMapper |
| Web platforms | OpenWebRX, iNTERCEPT, SDR-Console |
| AI/ML classification | GNU Radio + TensorFlow/PyTorch, SigMF datasets |

## References

1. Kali Linux Ethical Hacker's Cookbook (Packt, 2018), Chapter 10: Playing with Software-Defined Radios — practical gqrx, rtl_sdr, replay workflows
2. The Car Hacker's Handbook (No Starch, 2016) — SDR for automotive signal analysis, TPMS decoding
3. PoC||GTFO Bible — "Naughty Signals" by Russell Handorf, RTL-SDR + Raspberry Pi transmitter
4. RTL-SDR Blog, "Tech Minds: Testing Intercept Signal Intelligence Tool" (Jan 2026) — new SDR SIGINT platform
5. Medium, "Hacking the Signal: AI-Powered SDR Recon Kit" (2026) — HackRF + AI spectrogram classification pipeline
6. SDRstore, "Best SDR Software in 2026" — comprehensive comparison of SDR++, SDRangel, SDRSharp, Gqrx, GNURadio
7. v16 field report: "AI-Powered SIGINT Evolution" (2026-05-20) — market scale ($15.4B, 5%+ CAGR), RadCharSSL, MAG Aerospace
8. Gadget Kit Design Note: RF sensing hardware (RTL-SDR, HackRF, KrakenSDR, antennas) — Exocortex internal spec
9. v17 wiki: "Custom PCB Sensor Networks" (2026-06-04) — SDR sensor nodes, MQTT→InfluxDB→knowledge graph pipeline
10. Academic: RadCharSSL self-supervised radar recognition (2025) — few-shot RF classification method
11. Pacific Defense SDR4320VP software-defined radio (Dec 2025) — next-gen EW/SIGINT COTS SDR platform
12. Inference Systems UK — commercial deep learning SIGINT systems on COTS SDR hardware
13. RTL-SDR vs HackRF comparison (OneSDR, 2026) — hardware capability tradeoffs for OSINT practitioners
14. GNU Radio documentation — programmable DSP framework for custom signal analysis flowgraphs
