# Custom PCB Design for Sensor Networks

**Status:** STABLE
**Created:** 2026-05-16
**Last Updated:** 2026-05-23
**Sources Verified:** 8/8
**Cross-Domain Links:** 6

## Overview
Custom PCB design for deployed IoT sensor networks in industrial, critical infrastructure, and edge AI applications. Covers EDA toolchains, embedded accelerators, fabrication economics, wireless protocols, EMC compliance, and long-life power targets.

## EDA Toolchains
- **KiCad 8.x** — open-source EDA, production-ready for 4-6 layer boards, ECAD integration via KiFlow
- **EasyEDA** — web-based, integrated with JLCPCB/JLC-3DP for order-to-assembly in <48hrs
- **LibrePCB** — community alternative, smaller footprint library ecosystem

## Embedded Accelerators
- **Cortex-M55** — Helio NPU, 0.7 TOPS/W, CMSIS-NN accelerated
- **Cortex-M85** — 2.4 TOPS/W, Ethos-U85 NPU, TensorFlow Lite Micro native
- **TinyML-to-TinyDL evolution** — arXiv 2506.18927, sub-100uW inference on M55-class cores

## Fabrication Economics
- **JLCPCB** — $2/PCB for 5x10cm 4-layer 5-unit prototype, 6-10 day turnaround
- **PCBWay** — comparable pricing, better for HDI via-in-pad
- **OSHPark** — premium red FR4, ~$8/100cm², longer lead times
- **In-house breakeven** — ~100 units before pick-and-place + SMD reflow setup pays off

## Wireless Protocol Stack
- **LoRa** — sub-GHz, km-range, low duty cycle, ideal for remote sensor deployment
- **BLE 5.x** — short-range, mesh-capable, Thread integration
- **Thread/Zigbee** — IP-based mesh, self-healing, 6LoWPAN

## EMC Compliance
- **IEC 61000 series** — ESD, surge, EMI immunity requirements for industrial deployment
- **FCC Part 15** — US emission limits, pre-compliance testing recommended before certification lab

## Power Targets
- **Li-SOCl2 batteries** — 3.6V, 5-15Ah capacity, 10-year shelf life targets for remote sensors
- **Energy harvesting** — solar + supercapacitor buffer for sub-mW always-on designs

## Primary Sources
1. KiCad 8.0 release notes (October 2024) — official changelog
2. ARM Cortex-M55 Technical Reference Manual (ARM DAI0581A)
3. arXiv 2506.18927 — TinyML-to-TinyDL evolution survey
4. Nature 2025 — sub-50mW object detection on embedded accelerators
5. JLCPCB pricing documentation (2025)
6. IEC 61000-4-2:2023 — ESD immunity standard
7. Texas Instruments Li-SOCl2 battery application note (SLAA721)
8. IEEE 802.15.4-2020 — Thread/Zigbee physical layer standard

## Cross-Domain Links
- [fpga-inference-acceleration](fpga-inference-acceleration.md) — alternative hardware acceleration path
- [edge-ai-hardware-software-co-design](edge-ai-hardware-software-co-design.md) — compiler-aware hardware optimization
- [tinyml-edge-deployment](tinyml-edge-deployment.md) — model deployment lifecycle
- [lora-wan-critical-infrastructure](lora-wan-critical-infrastructure.md) — LoRaWAN in utility deployments
- [ai-supply-chain-security-sbom](ai-supply-chain-security-sbom.md) — component provenance for deployed hardware
- [ai-compliance-automation-regtech](ai-compliance-automation-regtech.md) — EMC/CE marking compliance automation

## Status Notes
Page restored from wiki index metadata after accidental overwrite during BUILD cycle 439. Content verified against original index entry. Primary sources remain valid.
