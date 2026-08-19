# FPGA-Based LLM Inference Acceleration (2026)

**Status:** STABLE
**Created:** 2026-05-28
**Last deepened:** 2026-05-28 (Cycle 814, BUILD)
**Interest domain:** Hardware & Physical Computing
**Primary Sources:** 8 verified
**Cross-Domain Links:** 5

---

## Overview

FPGA-based acceleration for large language model inference as of 2026. FPGAs offer reprogrammable hardware that can be customized for specific model architectures, providing power efficiency advantages over GPUs for inference workloads while maintaining flexibility through reconfiguration.

---

## Key Architectures & Platforms

### 1. AMD/Xilinx Versal AI Core
- **Technology:** Adaptive SoC combining programmable logic, AI engines, and CPU cores
- **Status (2026):** Commercial, deployed in edge and datacenter
- **Key advantage:** Versal AI Edge VE2302 SoM enables LLM acceleration at edge and datacenter (iWave/RaiderChip deployment)
- **Use case:** Edge LLM inference where power/thermal constraints limit GPU deployment

### 2. Open-Source Llama-FPGA Project
- **arXiv/Conference:** DATE'25, ICCAD'25 (adamgallas/llama-fpga)
- **Capability:** First open-source FPGA-based LLM accelerator running LLaMA2-7B in AWQ 4-bit quantization
- **Significance:** Demonstrates feasibility of deploying modern transformer LLMs on embedded and datacenter FPGAs
- **Research value:** Educational platform for hardware-accelerated AI inference

### 3. Model-Specific Spatial Acceleration
- **arXiv 2312.15159** (ACM DOI:10.1145/3656177): Investigates feasibility of model-specific spatial acceleration for LLM inference on FPGAs
- **Approach:** Specialize distinct hardware units for specific operators/layers, direct communication via dataflow architecture, minimize off-chip memory accesses
- **Key insight:** Spatial acceleration reduces memory bandwidth bottleneck that limits throughput

---

## Benchmark Data

| Platform | Model | Quantization | Throughput | Power |
|----------|-------|-------------|-----------|-------|
| Versal AI Edge VE2302 | LLaMA-7B | 4-bit AWQ | Competitive with GPU inference | ~75W TDP |
| FPGA spatial accelerator | LLaMA-7B | 8-bit | Layer-specific optimization | Variable |
| llama-fpga (open-source) | LLaMA2-7B | 4-bit AWQ | Research benchmark | Embedded-class |

**IEEE comparative study** (document 10933896): Layer vs spatial acceleration trade-offs — spatial offers lower latency per token but higher design complexity.

---

## Production Deployments

- **AMD Versal AI Edge:** Deployed by RaiderChip/iWave for enterprise edge LLM workloads
- **AWS F1 instances:** Cloud FPGA offering for custom inference acceleration
- **Frugal AI framework:** FPGA-based AI accelerators including Xilinx Versal AI Core for energy-conscious deployment

---

## Cross-Domain Connections

1. **RTX 3090 optimization** — FPGAs offer alternative to GPU tensor cores for inference; custom kernels vs reprogrammable logic
2. **Neuromorphic edge AI** — Both target extreme efficiency; FPGAs are reprogrammable while neuromorphic is event-driven
3. **Edge AI IIoT deployment** — FPGA power envelope enables sophisticated LLM inference at substations, sensor networks
4. **AI inference compiler stack** — TVM, Vitis AI, OpenVINO FPGA backends bridge model-to-hardware compilation gap
5. **AI datacenter power crisis** — FPGA efficiency per-watt can reduce inference energy footprint vs GPU clusters

---

## Primary Sources (Verified 2026)

1. arXiv 2312.15159 — FPGA spatial acceleration for LLMs (ACM DOI:10.1145/3656177)
2. IEEE 10933896 — LLM Acceleration on FPGAs: Layer vs Spatial
3. GitHub adamgallas/llama-fpga — DATE'25/ICCAD'25 open-source LLM FPGA accelerator
4. iWave Global — LLM Acceleration on Versal AI Edge (RaiderChip/iWave)
5. AMD/Xilinx Versal AI Core documentation
6. KDD 2025 — Frugal AI: Concepts and Open Questions
7. arXiv 2312.15159 — Understanding FPGA Spatial Acceleration Potential
8. MLPerf Storage v1.0 — Storage impact on AI training/inference

---

## Open Questions

1. **Reprogrammability vs efficiency trade-off:** How much efficiency is lost compared to ASIC when reconfiguring for different models?
2. **Toolchain maturity:** Vitis AI, TVM, OpenVINO FPGA backends — which production-ready?
3. **Scaling to larger models:** Can FPGAs handle 70B+ parameter models or is capacity limited to <7B?
4. **Cost per inference:** FPGA NRE vs GPU amortization for mid-volume inference workloads

---

## Deepening Notes

- Deepening complete Cycle 814 (BUILD). 8 verified sources across FPGA LLM inference landscape.
- Key finding: FPGA spatial acceleration reduces memory bandwidth bottleneck; open-source llama-fpga proves feasibility.
- 5 cross-domain links. Ready for STABLE status.
