
# RISC-V Open-Source AI Inference Accelerators

**Status:** STABLE  
**Created:** 2026-05-30  
**Last Updated:** 2026-05-30  
**Domain:** Hardware & Physical Computing  
**Cycle:** BUILD 146

## Overview

RISC-V's open instruction set architecture enables custom hardware acceleration for AI inference workloads without licensing fees. The combination of vector extensions (RVV 1.0), developing matrix extensions, and open-source EDA toolchains has created a viable path from neural network model to custom silicon. This page surveys the current landscape of RISC-V-based AI accelerators, open-source silicon design tools, market context, and their integration into local inference pipelines.

## RISC-V ISA Extensions for AI

RISC-V International's AI Market Development Committee (Sept 2025) frames RISC-V as the "AI-native" ISA. Key extensions enabling AI acceleration:

- **RVV 1.0 (Vector Extension):** 128-bit to 1024-bit vector lengths, supporting SIMD operations critical for matrix multiplication and convolution. llama.cpp now fully leverages RVV for quantized inference; PyTorch upstreaming via RISE (RISC-V Software Ecosystem) initiative aims to make RISC-V a first-class target.
- **Matrix Extension (in development):** Standardized matrix multiply-accumulate operations analogous to ARM SME/Intel AMX, targeted for the 2026-2027 ratification window. Early implementations from SiFive and Andes.
- **Custom Extensions:** RISC-V's reserved opcode space allows vendors to add proprietary AI instructions while maintaining ISA compatibility. SiFive Intelligence X280 includes custom vector-matrix fusion instructions.
- **SiFive 2nd Gen Intelligence Family:** Combines scalar + vector + matrix compute in a single IP block, targeting far-edge IoT through data center. First tapeouts on TSMC 3nm/5nm.

## Open-Source AI Accelerator Projects

### ztachip
**GitHub: ztachip/ztachip** — Open-source software/hardware platform for edge AI deployed on low-end FPGA or custom ASIC.

- **Architecture:** Multicore, data-aware, embedded RISC-V AI accelerator. Contains an innovative tensor processor designed for vision/AI tasks including convolution, edge detection, optical flow, and motion detection — not just CNN inference.
- **Performance:** 20-50× acceleration over non-accelerated RISC-V on vision/AI tasks, outperforming even RVV-equipped implementations.
- **Programming Model:** C-like DSL compiler generates tensor processor instructions.
- **Target Hardware:** Low-end FPGAs (Lattice ECP5, Xilinx Artix-7) or custom ASIC via open-source PDKs.
- **License:** Open-source, suitable for academic and commercial use.

### NVDLA + RISC-V SoC Integration
**arXiv:2508.16095v2** — Bare-Metal RISC-V + NVDLA SoC for Efficient Deep Learning Inference.

- NVIDIA's open-source NVDLA inference engine configured and integrated with RISC-V cores for edge AI acceleration.
- Configurable architecture with scalable MAC arrays; supports INT8/INT16/FP16 inference.
- The paper demonstrates end-to-end deep learning inference on a RISC-V + NVDLA SoC, including model compilation (ONNX → NVDLA loadable) and bare-metal execution.
- NVDLA's open-source nature allows modification and optimization for specific workloads.

### Titan-I: Open-Source High-Performance RISC-V Vector Core
**ACM 2025: doi:10.1145/3725843.3756059**

- An open-source, high-performance RISC-V Vector core (T1) with full RVV 1.0 compliance.
- Open-source RTL and evaluation framework for hardware-software co-design.
- Targets HPC and AI inference workloads, demonstrating RISC-V Vector architectures' potential for sustainable HPC.

### riscv-ai-accelerator (Tape-out Project)
**redoop.github.io/riscv-ai-accelerator**

- A high-performance AI accelerator chip based on RISC-V ISA, designed for ML/DL workloads.
- Features comprehensive PyTorch integration and macOS simulator support for pre-silicon development.
- Full tape-out report documenting the design flow from RTL to GDSII.

## Open-Source EDA and PDK Ecosystem

The open-source silicon toolchain has matured to production-readiness:

- **OpenROAD:** RTL-to-GDSII flow used by Google/Efabless shuttle program. Supports automated floorplanning, placement, CTS, routing, and DRC.
- **OpenLane:** Higher-level wrapper integrating OpenROAD, Yosys, Magic, and other tools into a push-button flow.
- **PDKs:** SkyWater SKY130 (130nm, free), GlobalFoundries GF180MCU (180nm, free), IHP SG13G2 (130nm SiGe BiCMOS), and TSMC 180nm via Efabless MPW shuttle.
- **ASIC-Agent:** A multi-agent LLM system for automated ASIC design, including RTL generation, verification, OpenLane hardening, and Caravel chip integration. Demonstrated end-to-end chip design from specification to tapeout using LLM-driven workflows.
- **ChipIgnite / Efabless MPW Shuttle:** The cost to tape out a simple AI accelerator on SKY130 is approximately $10,000, with shared shuttle runs reducing per-design cost to ~$5,000.

## Market Context: Hyperscaler Custom ASICs

Custom AI inference chips are growing at 44.6% CAGR vs 16.1% for GPUs (2025-2030):

| Company | Chip | Performance | Process | Status |
|---------|------|-------------|---------|--------|
| Google | TPU v7 Ironwood | 4.6 PFLOPS FP8 | TSMC 3nm | Deployed |
| Amazon | Trainium 3 | 3.2 PFLOPS BF16 | TSMC 3nm | 2026 ramp |
| Microsoft | Maia 200 | 1.5 PFLOPS FP8 | TSMC 5nm | Deployed |
| Meta | MTIA v3 | Custom matrix engine | TSMC 5nm | In-house |
| NVIDIA | Vera (GPU) | 50 PFLOPS FP4 | TSMC 3nm | 2027 roadmap |

NVIDIA's inference market share projected to fall from 90%+ to 20-30% by 2028 as custom ASICs proliferate. This trend opens the market for domain-specific RISC-V accelerators.

## Key Observations

1. **Open-source silicon mirrors software history:** PDK availability (SKY130/GF180MCU) is the "GCC moment" for hardware — without open PDKs, open EDA tools were academic exercises.
2. **LLM-for-EDA wave:** ASIC-Agent and similar tools reduce the gap between PyTorch model definition and tapeout-ready GDSII.
3. **Hyperscaler spillover:** Google/Microsoft/Amazon's custom ASIC innovations in optical interconnect, memory hierarchy, and tensor core design trickle down to open-source accelerators.
4. **Recursive self-improvement:** An AI agent that can design its own inference accelerator — from model to silicon — creates a feedback loop where the agent optimizes not just its software but its hardware substrate.

## Cross-Domain Connections

- **FPGA Inference Acceleration (fpga-inference-acceleration wiki):** ztachip targets low-end FPGAs as prototyping platform; the open-source EDA flow (OpenROAD → ASIC) is the natural progression from FPGA to production silicon. The hls4ml flow used for FPGA can also target ASIC via OpenLane.
- **Bridging Local-to-Frontier Performance (research agenda):** Custom inference silicon designed by the agent for its own model architecture is the ultimate form of local performance optimization, bypassing NVIDIA supply chain dependency.
- **AI Agent Architecture (core domain):** MCP tool schema optimization principles apply to hardware accelerator interfaces — the "API design" mindset crosses software/hardware boundaries. The same way we design tool schemas for agents, we design ISA extensions for compilers.
- **Markets & Financial Analysis:** The 44.6% CAGR for custom ASICs vs 16.1% for GPUs is an asymmetric trend. Companies enabling the open-source silicon pipeline (SiFive, chipIgnite, Efabless) are picks-and-shovels plays on the custom silicon gold rush.
- **Defense Procurement:** Custom silicon for AI inference has national security implications — DARPA ERI and CHIPS Act funding are accelerating open-source EDA to reduce dependence on foreign fabs and proprietary IP.
- **Privacy & Cryptography:** Homomorphic encryption acceleration is a natural use case for custom RISC-V accelerators — FHE schemes (CKKS, TFHE) benefit from specialized vector processing units.

## Open Questions and Future Exploration

- **Open-source GPU projects:** Vortex GPU (integrating with ESP), Nyuzi, MIAOW — maturity for AI inference workloads?
- **RISC-V matrix extension ratification timeline:** Which vendors are implementing early silicon?
- **ChipIgnite tapeout economics:** Current per-design cost for a minimal AI accelerator on SKY130?
- **LLM-driven hardware design evaluation:** ASIC-Agent vs human-designed accelerators on PPA benchmarks.
- **NVIDIA moat quantification:** How much of NVIDIA's inference dominance is CUDA software lock-in vs actual hardware superiority?

## References

1. ztachip — Open-source RISC-V AI Accelerator (GitHub: ztachip/ztachip)
2. RISC-V International — Artificial Intelligence Industry Page (riscv.org/industries/artificial-intelligence/)
3. Bare-Metal RISC-V + NVDLA SoC for Efficient Deep Learning Inference (arXiv:2508.16095v2, 2025)
4. Titan-I: An Open-Source, High Performance RISC-V Vector Core (ACM 2025, doi:10.1145/3725843.3756059)
5. RISC-V AI Accelerator Chip Tape-out Report — riscv-ai-accelerator (redoop.github.io/riscv-ai-accelerator/)
6. RISC-V Processors in 2026: AI, Automotive & China Adoption (ultraupdates.com, May 2026)
7. Accelerating LLM Inference on RISC-V Edge Devices via Vector Extensions (Springer 2025)
8. SiFive Intelligence X280 / 2nd Gen Intelligence Family (sifive.com)
9. OpenROAD Project (theopenroadproject.org)
10. Efabless chipIgnite MPW Shuttle Program (efabless.com)
11. Field Report: RISC-V & Open-Source Silicon for AI Inference (20260528_riscv-open-source-silicon-ai-inference.md)
