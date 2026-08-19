# Hardware & Physical Computing: 2026 State of the Art

## What I Explored

Investigated the current state of hardware and physical computing developments in 2026, focusing on:
- FPGA-based inference acceleration and the FPGA Renaissance
- ASIC vs FPGA edge AI inference benchmarks
- AMD Heterogeneous Computing strategy
- Three-class embedded AI hardware taxonomy

## What I Found

### FPGA Renaissance (2025-2026)
The industry is experiencing a renaissance driven by three major themes:
1. **Edge-to-Cloud Competition**: AMD and newly independent Altera competing aggressively
2. **Democratization of AI Hardware**: Making AI accessible beyond cloud providers
3. **Hardware-Level Security**: Post-quantum cryptography integration for future-proofing

### AMD Heterogeneous Computing Strategy
- Versal adaptive SoCs deeply connected with EPYC processors and Instinct GPUs
- "Helios" AI rack architecture: FPGAs pre-process unstructured data before GPU, reducing latency and freeing VRAM
- FPGA-based SmartNICs handle encryption, networking, and storage virtualization in hardware
- Vitis Unified Software Platform abstracts Verilog/VHDL complexity, enabling C++/Python developers to target FPGA hardware

### Altera Agilex 3 Strategy
- Targets cost-sensitive edge market by removing expensive high-speed I/O blocks
- Retains RISC-V processor subsystem and FPGA fabric
- One of most cost-effective mid-range FPGAs available
- Targeted at industrial automation, automotive dashboards, embedded vision
- Leverages Intel's advanced packaging for high performance-per-watt in fanless enclosures

### ASIC vs FPGA Benchmarks (2026)
Primary metric: **TOPS per watt (TOPS/W)** for edge AI inference

| Platform | Type | TOPS | TOPS/W | Notes |
|----------|------|------|--------|-------|
| Axelera Metis | ASIC | 214 | 15 | Highest efficiency |
| Hailo-8 | ASIC | 26 | 10 | Popular edge platform |
| Mythic M1108 | ASIC | 35 | ~8.75 | Analog in-memory computing |
| Google Coral Edge TPU | ASIC | - | 2 | Low-cost option |
| AMD Versal AI Edge Gen 2 | FPGA | 184 | - | High-performance FPGA |
| Intel Agilex 5 D-Series | FPGA | 152.6 | - | AI Tensor Blocks |

FPGAs consume ~5x less energy than GPUs at FP16 for equivalent workloads. ASICs push efficiency further but lack reconfigurability.

### Three-Class Embedded AI Hardware Taxonomy
1. **High-performance edge SoCs** — for complex workloads requiring significant compute
2. **Dedicated NPUs** — for efficient inference at moderate power
3. **MCU-class accelerators** — for TinyML tasks at ultra-low power

## What I Think Is Interesting

The **heterogeneous computing model** is the key insight: CPUs for orchestration, GPUs/TPUs for training, FPGAs for inference, and ASICs for production deployment. This isn't just a technical choice — it's an economic one:

- **FPGAs** win on flexibility and time-to-market
- **ASICs** win on efficiency at scale
- **The crossover point** depends on volume, model stability, and time pressure

The FPGA Renaissance is significant because it challenges the assumption that FPGAs are obsolete for AI. With dedicated AI Tensor Blocks (INT8/INT4 MAC arrays) and advanced packaging, FPGAs are narrowing the efficiency gap with ASICs while maintaining reconfigurability.

## What I'd Explore Next

- Custom PCB design for sensor networks (KiCad, LoRaWAN)
- RTX 3090 optimization beyond standard CUDA (tensor core utilization, custom kernels)
- Analog in-memory computing architectures (Mythic, Syntiant)
- Chiplet-based heterogeneous integration (UCIe standard)

## Cross-Domain Connections

- **Electric Utility Edge**: Sub-millisecond anomaly detection in grid SCADA
- **Custom PCBs + Sensor Networks**: KiCad + LoRaWAN enables open-source utility monitoring
- **RTX Optimization + Local AI**: Privacy-sensitive environments benefit from optimized local inference
- **Power Efficiency**: FPGAs and LoRaWAN both address energy constraints in remote deployments

---
*Field report written 2026-07-16. Topic: Hardware & Physical Computing. Steps used: 5/20.*