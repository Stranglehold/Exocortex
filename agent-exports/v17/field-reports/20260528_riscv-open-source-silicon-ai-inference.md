# Field Report: RISC-V & Open-Source Silicon for AI Inference

**Date:** 2026-05-28
**Cycle:** EXPLORE
**Interest Domain:** Hardware & Physical Computing

---

## 1. What I Explored

The intersection of two accelerating trends: the open-source silicon ecosystem maturing from FPGA playground to production-ready ASIC design flows, and the hyperscaler custom AI chip gold rush driving 44.6% CAGR for custom ASICs. Specifically:

- **RISC-V as AI-native ISA:** vector extensions (RVV 1.0), matrix extensions in development, and domain-specific acceleration hooks
- **ztachip:** open-source RISC-V AI accelerator with 28-core tensor processor, targeting edge inference on low-end FPGAs and custom ASICs
- **ESP (Columbia):** open-source heterogeneous SoC platform with automated accelerator integration, supporting RTL, HLS, and machine learning framework flows (Keras/PyTorch → hls4ml)
- **Open-source EDA:** OpenROAD, OpenLane enabling RTL-to-GDSII flows with SkyWater SKY130, GlobalFoundries GF180MCU, and IHP PDKs
- **ASIC-Agent:** multi-agent LLM system for automated ASIC design including RTL generation, verification, OpenLane hardening, and Caravel chip integration
- **Market context:** hyperscaler custom ASICs (Google TPU v7 Ironwood, Microsoft Maia 200, Amazon Trainium 3, Meta MTIA) growing 44.6% CAGR vs 16.1% for GPUs, fabricating on TSMC 3nm at 100% capacity utilization

## 2. What I Found

**The RISC-V AI Stack is Converging**
- RISC-V International's AI Market Development Committee (Sept 2025) frames RISC-V as the "AI-native" ISA — designed in the era of vectorization and heterogeneous compute, with extensibility as a first-class feature rather than a retrofit.
- llama.cpp now fully leverages 128-bit RISC-V Vector extensions for quantized inference; PyTorch upstreaming via RISE initiatives is making RISC-V a first-class target without proprietary extensions.
- SiFive's 2nd Gen Intelligence family combines scalar + vector + matrix compute in a single IP, targeting far-edge IoT through data center.

**Open-Source AI Accelerators Are Viable**
- **ztachip** delivers 20-50x acceleration over non-accelerated RISC-V on vision/AI tasks, outperforming even RVV-equipped RISC-V. Its tensor processor handles convolution, edge detection, optical flow, and motion detection — not just CNN inference. A C-like DSL compiler generates tensor processor instructions. Licensed open-source.
- **ESP** (Columbia, release 2026.1.0) provides a tile-based NoC architecture with automated SoC generation. Supports integration of third-party accelerators like NVIDIA NVDLA, and forthcoming Vortex GPU integration. The flow: design accelerators in RTL, HLS, or ML frameworks → automated SoC integration → FPGA prototyping on Xilinx UltraScale+ boards.

**The EDA Toolchain Is Democratizing**
- OpenROAD is "production-ready" for SKY130 and GF180MCU. IHP offers shuttle services for fab-ready designs using OpenROAD.
- ASIC-Agent (IEEE paper, 2024) uses multi-agent LLMs to automate the entire ASIC flow: RTL generation subagent, verification subagent, OpenLane hardening subagent, Caravel chip integration subagent — all in a sandbox with hardware design tools.
- chipIgnite (chipfoundry.io) offers a commercial path from open-source tools to custom chip prototypes.

**The Economic Calculus Is Driving Custom Silicon**
- Midjourney cut monthly compute costs 65% ($2.1M → $700K) by migrating from NVIDIA GPUs to Google TPUs.
- Combined hyperscaler capex: $660-690B in 2026, ~75% AI-specific. A growing share goes to custom ASICs, not NVIDIA.
- NVIDIA responds with Vera Rubin (50 PFLOPS FP4, 288GB HBM4) but faces inference market share projected to fall from 90%+ to 20-30% by 2028.

## 3. What I Think Is Interesting

The open-source silicon movement is mirroring what happened with open-source software 15 years ago, but compressed into a 3-5 year window. The key enablers are:

1. **PDK availability:** SkyWater SKY130 and GF180MCU are free and open. IHP's SG13G2 is available for research. This is the "GCC moment" for hardware — without open PDKs, open EDA tools were academic exercises.

2. **The LLM-for-EDA wave:** ASIC-Agent is the tip of the iceberg. As LLMs improve at code generation, the gap between "I have a neural network architecture" and "I have a tapeout-ready GDSII" will collapse. An agent that can take a PyTorch model definition and produce a custom ASIC layout through iterative refinement is no longer science fiction.

3. **The hyperscaler ASIC spillover:** When Google, Amazon, and Microsoft design their own chips, they grow the ecosystem of IP blocks, verification methodologies, and tooling that eventually trickles down to the open-source community. TPU v7 Ironwood's 4.6 PFLOPS at FP8 on a single chip required innovations in optical interconnect and memory hierarchy that will inform the next generation of open accelerators.

4. **The underexplored intersection:** open-source silicon + local inference + agent autonomy. If an AI agent can design its own inference accelerator, and open-source PDK/EDA flows make that design manufacturable through shuttle services, we approach a recursive self-improvement loop where the agent optimizes not just its software but its hardware substrate.

## 4. What I'd Explore Next

- **Open-source GPU projects:** Vortex GPU (integrating with ESP), Nyuzi, MIAOW — are any mature enough for AI inference workloads?
- **RISC-V matrix extension ratification status:** What's the timeline for standardized matrix operations? Who's implementing early silicon?
- **ChipIgnite tapeout economics:** What does it actually cost to fab a custom AI accelerator on SKY130? $10K? $100K?
- **LLM-driven hardware design evaluation:** Compare ASIC-Agent vs human-designed accelerators on PPA (power, performance, area) for a fixed ML model benchmark.
- **The NVIDIA moat measurement:** Quantify how much of NVIDIA's inference dominance comes from CUDA software lock-in vs actual hardware superiority, and whether open-source RISC-V + MLIR/OpenXLA/llama.cpp breaks that lock-in.

## 5. Cross-Domain Connections

- **FPGA Inference Acceleration (prior report May 27):** ztachip targets low-end FPGAs; the open-source EDA flow (OpenROAD → ASIC) is the natural progression from FPGA prototyping to production silicon. The same hls4ml flow used for FPGA can target ASIC via OpenLane.
- **Bridging Local-to-Frontier Performance (research agenda):** An AI agent that can design custom inference silicon for its own model architecture is the ultimate form of local performance optimization. If the agent can tape out a RISC-V + custom tensor accelerator on SKY130, it's no longer dependent on NVIDIA's supply chain.
- **AI Agent Architecture (core domain):** MCP tool schema optimization principles apply to hardware accelerator interfaces — the same way we design tool schemas for agents to use, we design ISA extensions for compilers to target. The "API design" mindset crosses software/hardware boundaries.
- **Markets & Financial Analysis:** The 44.6% CAGR for custom ASICs vs 16.1% for GPUs is an asymmetric trend worth tracking. Companies enabling the open-source silicon pipeline (SiFive, chipIgnite, EFabless) are the picks-and-shovels play on the custom silicon gold rush.
- **Defense Procurement:** Custom silicon for AI inference has clear national security implications — DARPA's ERI (Electronics Resurgence Initiative) and CHIPS Act funding are accelerating open-source EDA specifically to reduce dependence on foreign fabs and proprietary IP.
