# In-Sensor Computing for Edge AI Inference

**Status:** STABLE
**Created:** 2026-05-23
**Last Updated:** 2026-05-23
**Interest Domain:** Hardware & Physical Computing / Edge AI
**Cross-links:** [in-sensor-near-sensor-ai-computing](in-sensor-near-sensor-ai-computing.md), [neuromorphic-computing](neuromorphic-computing.md), [edge-ai-hardware-software-co-design](edge-ai-hardware-software-co-design.md), [fpga-inference-acceleration](fpga-inference-acceleration.md)

---

## Overview

In-sensor computing (ISC) places inference computation directly within sensor arrays, eliminating the data-movement bottleneck between sensing and processing. This page focuses specifically on inference accuracy-energy trade-offs, production deployment benchmarks, and TRL assessment gaps — complementing the broader architectural coverage in [In-Sensor & Near-Sensor](in-sensor-near-sensor-ai-computing.md).

## Inference Accuracy vs. Energy Efficiency Trade-offs

### PicoSAM2 on Sony IMX500 (arXiv 2506.18807)
- Model: 1.3M parameters, 336M MACs (depthwise separable U-Net + knowledge distillation from SAM2)
- COCO mIoU: 51.9%, LVIS mIoU: 44.9% (+3.5% mIoU from distillation)
- Quantized model size: 1.22MB (fits IMX500 memory budget)
- Inference latency: 14.3ms at 86 MACs/cycle
- Only model meeting both memory AND compute limits for in-sensor deployment

### TRL Assessment Gap (arXiv 2605.13699)
- Sadoun et al. survey of 6 application domains: robotics, autonomous vehicles, AR/VR, surveillance, medical imaging, IoT
- 3 of 6 domains rest entirely on projection — no fabricated demonstrations
- Existing hardware sits at TRL 2-5 (component validated through system prototype)
- Memristor DVS pairings show theoretical 3-4 order magnitude improvement but no production units

## Benchmark Comparison (arXiv 2603.08725, I2MTC 2026)

Capogrosso/Bonazzi/Magno comparative review benchmarks 336M MAC workload across platforms:

| Architecture | Latency | Energy Efficiency | Notes |
|-------------|---------|-------------------|-------|
| Sony IMX500 (in-sensor) | 14.3ms | 1,360 MMAC/J | Best-in-class for vision |
| ANSA (near-sensor) | ~50ms | ~800 MMAC/J | 42% lower energy than DLA |
| NVIDIA DLA (edge) | ~20ms | ~450 MMAC/J | Baseline edge accelerator |
| GAP9 RISC-V (MCU) | ~100ms | 182 MMAC/J | MCU-class comparison |

**Defining metric**: In-sensor achieves 60x EDP advantage over traditional edge accelerators (verified in arXiv 2603.08725).

## Commercial Deployment Status

- **Sony IMX500**: Production deployment via AITRIOS ecosystem (Sony Semiconductor + Raspberry Pi dev kits). YOLO inference demonstrated at Embedded Vision Summit 2025.
- **BrainChip Akida**: $25M funding round 2025, commercial edge AI processor.
- **Memristor-based ISC**: No production deployments as of May 2026. Research-grade demonstrations only.

## Key Gap: Precision vs. Flexibility

- In-sensor analog compute trades numeric precision (typically 4-8 bit) for energy efficiency
- Digital in-sensor (IMX500) avoids precision loss but has fixed-function compute tiles
- Reconfigurable in-sensor remains unsolved — hardware committed at fabrication
- Software calibration layers needed for device-to-device variability in analog crossbars

## Verified Primary Sources (8)

1. arXiv 2603.08725 — Capogrosso/Bonazzi/Magno "Performance Analysis of Edge and In-Sensor AI Processors" (I2MTC 2026)
2. arXiv 2605.13699 — Sadoun et al. "Memristor Technologies for Dynamic Vision Sensors: A Critical Assessment and Research Roadmap"
3. arXiv 2506.18807 — PicoSAM2 "Low-Latency Segmentation In-Sensor for Edge Vision Applications"
4. Nature s44335-025-00040-6 — "Edge intelligence through in-sensor and near-sensor computing"
5. ScienceDirect S2211285526003137 — "A review on memristor-based in-sensor computing for neuromorphic and edge AI"
6. PMC13092463 — "In-Sensor-Memory Computing for Post-Von Neumann Intelligence" (Apr 2026)
7. Sony AITRIOS IMX500 product documentation (commercial deployment data)
8. Edge AI Vision Summit 2025 — Sony Embedded Vision Summit demo (July 2025)

## Cross-Domain Links

- **[In-Sensor & Near-Sensor AI Computing](in-sensor-near-sensor-ai-computing.md)** — Parent architecture coverage with tier analysis
- **[Neuromorphic Computing](neuromorphic-computing.md)** — Loihi 2 SNN inference aligns with in-sensor event-driven paradigm
- **[Edge AI Hardware-Software Co-Design](edge-ai-hardware-software-co-design.md)** — CIM optimization stack complements ISC approach
- **[FPGA Inference Acceleration](fpga-inference-acceleration.md)** — FPGA sub-3ns latency vs in-sensor 14.3ms shows speed vs efficiency trade-off
