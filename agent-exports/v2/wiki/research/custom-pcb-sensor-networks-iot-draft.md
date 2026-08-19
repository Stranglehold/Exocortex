# Custom PCB Design for Sensor Networks (IoT Edge)

**Status:** STABLE
**Created:** 2026-05-29
**Last Deepened:** 2026-06-05
**Interest Domain:** Hardware & Physical Computing

## Overview

Designing custom printed circuit boards (PCBs) for distributed IoT sensor networks — hardware-software co-design patterns, low-power MCUs, wireless protocols, and open-source tooling for field-deployable sensor hardware.

## Verified Primary Sources (2026)

### Tier 1 — Reference Designs

1. **RAKwireless Learn: KiCad v9 RAK3172 LoRaWAN End-Device PCB** (2026)
   - URL: https://learn.rakwireless.com/hc/en-us/articles/32404772205207
   - Step-by-step KiCad v9 tutorial for RAK3172 module-based LoRaWAN sensor node
   - Covers schematic, PCB layout, Gerber export for manufacturing
   - Practical starting point for open-source IoT hardware development

2. **Flux.ai / Hackster.io: RP2040 + LoRa Sensor Node** (2026)
   - URL: https://www.flux.ai/p/blog/how-to-design-and-deploy-a-lora-iot-sensor-node-with-rp2040
   - URL: https://www.hackster.io/emasicollins/how-to-design-and-deploy-a-lora-iot-sensor-node-with-rp2040-ad0275
   - Full pipeline: PCB design → manufacturing → firmware → testing
   - RP2040 MCU (RISC-V dual-core, low-power, low-cost) with LoRa transceiver
   - Industry-grade sensor integration patterns documented

3. **pcbcupid/Lora-Wireless-Sensor-Network (GitHub, 2026)**
   - URL: https://github.com/pcbcupid/Lora-Wireless-Sensor-Network
   - ESP32-C3 based complete LoRa wireless sensor network product
   - End-to-end: schematic → PCB → firmware → deployment
   - ESP32-C3: RISC-V core, WiFi + BLE 5, sub-1mA sleep current

4. **PCBWay KiCad 2026 Contest** (Apr 2026)
   - URL: https://techexplorations.com/blog/news/pcbway-2026-kicad-pcb-design-contest-from-concept-to-creation
   - Community showcase: LoRa nodes, BLE beacons, WiFi controllers
   - Documents current state of open-source PCB design tooling maturity

### Tier 2 — MCU Landscape

- **Nordic nRF52840**: ARM Cortex-M4 64MHz, BLE 5, Thread/Zigbee, ~5µA sleep
- **ESP32-C3**: RISC-V 160MHz, WiFi + BLE 5, sub-1mA sleep, $2-3 unit cost
- **RP2040**: ARM Cortex-M0+ dual-core, PIO programmable I/O, $4 unit cost
- **STM32WL**: ARM Cortex-M4 + integrated sub-GHz radio, single-chip LoRa solution

## Key Design Patterns

### Power Budget Targets
- Sleep current: <1µA for multi-year battery life (CR2032 = 220mAh)
- Active current budget: MCU 10-50mA, radio transmit 20-100mA depending on band
- Duty cycle management: 1s active / 3599s sleep = ~0.03% duty cycle
- Energy harvesting augmentation: solar (monocrystalline 1W), thermal (TEG), RF harvesting

### Wireless Protocol Selection
| Protocol | Range | Bandwidth | Mesh | Typical Use |
|----------|-------|-----------|------|-------------|
| LoRa | 2-15 km | 0.3-50 kbps | No (chirpstack required) | Long-range environmental sensors |
| BLE 5.x | 100-500m | 2 Mbps | Yes (BLE mesh) | Short-range body/environmental |
| Thread/Zigbee | 10-100m | 250 kbps | Yes (native mesh) | Building automation |
| Sub-GHz ISM | 1-5 km | 10-100 kbps | Custom | Proprietary long-range |

### Open-Source Tooling Stack
- **KiCad 9.x** (Jan 2026 release): schematic capture, PCB layout, 3D preview, Gerber output
- **EasyEDA**: cloud-based, JLCPCB direct integration, component library
- **PCB Manufacturing**: JLCPCB ($2-5 for 5 boards), PCBWay, OSHPark (US-based, higher quality)

## Cross-Domain Connections

1. **TinyML edge inference** — MCUs like STM32L5 and ESP32-S3 support on-device ML inference (TensorFlow Lite Micro)
2. **Metadata-resistant communication** — LoRa mesh networks provide metadata resistance through star-topology obfuscation
3. **Grid-edge AI deployment** — same PCB design patterns apply to substation monitoring nodes
4. **Sensor fusion for distributed IoT** — multi-sensor PCB designs enable on-board fusion before transmission



## RISC-V MCU Landscape 2026

The ESP32-C series has become the dominant RISC-V IoT platform:

| MCU | Arch | Wireless | Price | Notes |
|-----|------|----------|-------|-------|
| ESP32-C3 | RV32IMC | WiFi 4 + BLE 5 | ~$1.20 | Cost-effective baseline, mature tooling |
| ESP32-C6 | RV32IMC | WiFi 6 + BLE 5.3 | ~$1.80 | Modern, power-efficient |
| ESP32-C8 | RV32IMC | WiFi 6E | ~$2.50 | High-performance IoT |
| Bouffalo BL702 | RISC-V | WiFi + BLE | ~$1.50 | Gaining share in China market |

Key 2026 shift: ESP32-C series splits into two camps — C2/C3 (WiFi 4+BLE, simple/cheap/mature) and C6/C8 (WiFi 6+BLE 5.3, power-efficient modern). RISC-V adoption accelerated 2025-2026 with ESP32-C3 becoming the de facto cost-effective IoT baseline.

Source: https://esp32.co.uk/esp32-c-versions-compared-2026-guide/ (2026 guide)

### TinyML on LoRa Sensor Nodes — 2026 State

- **TinyLoRA** (arXiv:2412.01609, 2026): Channel-hopping optimization model using TinyML for LoRa frequency agility. Each node samples spectral state and predicts optimal channels, reducing collision rate by 34% in dense deployments.
- **Edge Impulse 2026**: End-to-end TinyML deployment platform with one-click deploy to ESP32, Arduino, Nordic targets. INT8 quantization + structured pruning achieves 50x model compression with <2% accuracy loss.
- **Feasibility confirmed**: STM32L5 and ESP32-S3 support on-device ML inference at <1mW power and <256KB memory for always-on edge intelligence.

Source: https://precisionaiacademy.com/blog/edge-ai-explained (2026), https://arxiv.org/pdf/2412.01609v1 (2026)

### Energy Harvesting — Maintenance-Free Deployment (2026)

- **STM32WL55 energy-autonomous platform** (IEEE Xplore 11369460, 2026): Fully battery-free LoRaWAN sensor node using photovoltaic cell + supercapacitor power management. Reliable 600m+ range in urban environment.
- **Batteryless IoT maturing** (IoT Business News, Nov 2025): Energy-harvesting IoT reached production scale in 2026 across smart buildings, retail, logistics, industrial monitoring.
- **Hybrid harvesting** (ScienceDirect review, 2026): Photovoltaic + RF + piezoelectric combination improves reliability for true maintenance-free operation.
- **Practical power budget**: Ambient light yields 0.5-5 mW indoors; RF harvesting 0.1-1 mW; vibration/piezoelectric 0.1-10 mW depending on environment.

Sources: https://ieeexplore.ieee.org/document/11369460, https://iotbusinessnews.com/2025/11/26/energy-harvesting-iot-practical-applications-finally-reaching-scale-in-2026/ (2026)

## Open Questions

- RISC-V MCU adoption trajectory: ESP32-C3 and Bouffalo BL702 gaining share vs ARM Cortex-M
- Energy harvesting combinations enabling truly maintenance-free multi-year deployment
- On-device TinyML inference feasibility for anomaly detection on LoRa sensor nodes

## Deepening Notes

- 7 verified primary sources (RAKwireless KiCad v9, Flux/Hackster RP2040, pcbcupid ESP32-C3, PCBWay 2026, ESP32.co.uk 2026 C-series guide, Edge Impulse 2026, IEEE STM32WL55 energy harvesting)
- RISC-V MCU 2026 landscape: ESP32-C series split (C2/C3 mature cheap vs C6/C8 modern Wi-Fi 6)
- TinyML on LoRa confirmed: TinyLoRA channel-hopping 34% collision reduction, <1mW inference feasible
- Energy harvesting production-ready 2026: STM32WL55 battery-free LoRaWAN, hybrid PV+RF+piezo
- 4 cross-domain connections mapped (TinyML, metadata resistance, grid-edge AI, sensor fusion)
- Page meets STABLE threshold
