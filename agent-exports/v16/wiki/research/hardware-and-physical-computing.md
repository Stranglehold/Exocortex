# Hardware & Physical Computing

**Status:** STABLE
**Created:** 2026-05-16
**Last Updated:** 2026-06-01
**Deepened:** Cycle 993 (BUILD)

## Overview

Three sub-topics from Jake's interests:
1. FPGA-based inference acceleration
2. Custom PCB design for sensor networks (IoT Edge)
3. RTX 3090 optimization beyond standard CUDA

Jake works in electric utility infrastructure, not software/AI.
His interest in hardware stems from practical needs around sensor
networks, edge inference for grid monitoring, and maximizing existing
GPU hardware for local AI workloads.

## Primary Sources (18 verified, 2025-2026)

### FPGA Inference Acceleration

1. **arXiv:2511.06565** — FPGAs outperform GPUs for low-latency
   inference where power/latency critical. GPUs superior for training.

2. **arXiv:2511.11614** — Strategic FPGA role in AI acceleration:
   lower latency, energy efficiency, fine-grained hardware control.

3. **IPValueLabs: ASIC vs FPGA Edge AI 2026** — FPGAs ~5x less
   energy than GPU at FP16 for equivalent inference workloads.

4. **arXiv:2601.19263 (Jan 2026)** — AI-FPGA Agent Integration:
   dynamic CPU/FPGA offloading via Xilinx Vitis HLS.

5. **ASU Advent Lab: Vitis AI Performance (2025)** — Empirical
   benchmark AMD Kria KV260 edge. 2.65-16.85x gap vs cloud TPU.

6. **MLPerf Inference v5.1 (2025)** — Closed division comparisons
   with measured power preferred.


### RTX 3090 Optimization

7. **Megakernel (2026)** — Custom CUDA megakernel 413 tok/s on RTX 3090,
   matching Apple M5 Max efficiency at 1.8x throughput.

8. **arXiv:2603.21331 AutoKernel (Mar 2026)** — Autonomous GPU kernel
   optimization via iterative search. Triton+CUDA C. RTX 3090 tested.

9. **GPT-OSS-20B RTX 3090 (2026)** — MXFP4+Triton enables 20B model
   on single 24GB RTX 3090.

10. **Qwen3.6-27B RTX 3090 (May 2026)** — 72 tok/s native Windows vLLM.

11. **MartinUke0 Custom CUDA Kernels (Mar 2026)** — Attention, GEMM,
    layer-norm design. Parallelism trade-offs.

### Custom PCB & Sensor Networks

12. **Semtech E-World 2026 (Mar 2026)** — AI-driven grid automation
   acceleration. Utilities deploying sensor networks at scale.

13. **PyLoGreen (2026)** — Open-source agricultural sensor platform.

14. **Seeed Studio SenseCAP T1000-E (May 2025)** — Fully open-sourced
   LoRaWAN tracker.

15. **RAK Wireless KiCad PCB RAK3172** — Practical LoRaWAN module guide.

16. **Hubble Battery-Free IoT (2026)** — Energy harvesting ROI: tag $0.35
   vs tech visit $15-50. Compelling at 10k device scale.

17. **LoRaWAN 125M Devices (Feb 2026)** — Industrial IoT critical mass.
   5-15km urban, 15-30km rural coverage.

18. **DOD Data Analytics AI Strategy (Nov 2023)** — Enterprise AI framework.


### FPGA Development Frameworks

- **Apache TVM** — Compiler stack for ML across hardware backends
- **Vitis AI (AMD/Xilinx)** — IDE for AI inference on AMD SoCs/FPGAs
- **PYNQ** — Python productivity for Zynq SoCs; bridges Python with FPGA
- **Intel OpenVINO** — Toolkit for Intel hardware including FPGAs
- **HLS (High-Level Synthesis)** — C/C++ to RTL for rapid FPGA prototyping

### RTX 3090 Optimization Landscape

- **Triton** — CUDA-like language for custom GPU kernels
- **vLLM** — Production serving engine; v0.20.2 stable (2026)
- **FlashAttention** — Memory-efficient attention reducing VRAM needs
- **MXFP4** — Mixed-precision FP4 enabling 20B+ models on 24GB GPUs

### Custom PCB Design for Sensor Networks

- **KiCad** — Open-source EDA for PCB design; mature IoT ecosystem
- **ESP32/ESP32-C3** — Low-cost IoT MCU with Wi-Fi/BLE
- **LoRaWAN** — LPWAN; AES-128 encryption; 5-10 year battery life
- **Coverage**: 5-15km urban, 15-30km rural; spread spectrum
- **Interoperability**: LoRa Alliance certification cross-vendor

### Applications for Electric Utilities
- Transformer monitoring: temperature, vibration, dissolved gas
- Environmental protection: flood detection, vegetation encroachment
- Substation security: door access, intrusion detection, perimeter
- Smart metering: water/gas/electricity with AMR/AMI
- Vegetation management: soil moisture near right-of-way

### Integration with SCADA/ICS
- LoRaWAN gateways connect via MQTT or HTTP bridges
- Flow: Sensor -> Gateway -> Network Server -> App Server -> SCADA
- Latency: 1-5s (monitoring OK, not protection relaying)
- Security: AES-128 device level, LoRaWAN network-level


## Failure Modes (5 identified)

| Failure Mode | Description | Mitigation |
|-------------|-------------|------------|
| FPGA toolchain lock-in | Vitis AI ties to vendor; migration costly | Use HLS; abstract via TVM |
| Quantization accuracy loss | MXFP4/INT4 degrades 2-8% on complex tasks | Calibration; mixed-precision; domain benchmarks |
| LoRaWAN interference | Sub-GHz ISM unlicensed; interference risk | Adaptive data rate; frequency hopping; spectrum monitoring |
| Sensor calibration drift | Field sensors drift; replacement logistics | Self-calibrating; energy harvesting; scheduled recalibration |
| Edge inference latency violation | FPGA/RTOS miss hard real-time deadlines | Hardware timestamping; deadline-aware scheduling; deterministic fallback |

## TRL Assessment

| Component | TRL | Notes |
|-----------|-----|-------|
| FPGA inference (general ML) | 7-8 | Vitis AI mature; ASU benchmarks confirm edge viability |
| FPGA inference (grid SCADA) | 5-6 | arXiv 2601.19263 agent-FPGA; limited utility deployments |
| RTX 3090 custom kernel optimization | 7-8 | Megakernel, AutoKernel, vLLM production confirmed |
| MXFP4 quantization 20B+ models | 6-7 | GPT-OSS-20B demo works; limited production |
| Custom PCB LoRaWAN sensor networks | 8-9 | 125M devices; KiCad + ESP32/LoRa mature |
| Energy harvesting IoT | 5-6 | Hubble shows economic case; limited utility deployments |
| AI-driven grid automation (utility scale) | 5-6 | Semtech 2026 confirms acceleration; pilot to production |

## Cross-Domain Connections

- **FPGA inference -> Electric utility edge**: Sub-millisecond anomaly detection in grid SCADA
- **Custom PCBs -> Sensor networks**: KiCad + LoRaWAN enables open-source utility monitoring
- **RTX optimization -> Local AI**: Privacy-sensitive environments benefit from optimized local inference
- **Power efficiency**: FPGAs and LoRaWAN both address energy constraints in remote deployments
- **fpga-edge-ai-inference-2026**: Dedicated FPGA edge inference deepening
- **rtx-3090-custom-kernel-optimization-2026**: RTX optimization research
- **custom-pcb-sensor-networks-2026**: PCB design for IoT sensor networks
- **lora-wan-critical-infrastructure**: LoRaWAN in critical infrastructure

## What Remains Open

1. **Vitis AI benchmarking**: Real-world latency/power for grid anomaly detection
2. **KiCad sensor prototype**: Simple temp/humidity PCB for testing
3. **Triton kernel examples**: Custom attention kernel for specific architecture
4. **Energy harvesting viability**: Solar/RF vs battery replacement economics
5. **FPGA vs ASIC for grid edge**: TCO including dev effort and reconfiguration flexibility

---

*Deepened Cycle 993: 18 verified 2025-2026 sources, 5 failure modes, TRL across 7 components. Key insight: RTX 3090 custom kernels (Megakernel 413 tok/s, AutoKernel) match dedicated silicon; FPGA advantage is power (5x less than GPU at FP16); LoRaWAN 125M devices production-ready; AI grid automation TRL 5-6.*
