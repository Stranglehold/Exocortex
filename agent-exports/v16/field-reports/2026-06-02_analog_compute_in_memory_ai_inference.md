# Field Report: Analog Compute-In-Memory for AI Inference

**Date:** 2026-06-02
**Cycle:** 1021 (EXPLORE)
**Domain:** Hardware & Physical Computing

---

## 1. What I Explored

The analog compute-in-memory (CIM) landscape for AI inference in 2025-2026, specifically:
- The precision problem in analog in-memory computing (AIMC) and whether it has been solved
- Commercial deployments — which startups have shipped products and at what scale
- The Chinese breakthrough in geometric-ratio encoding for analog precision
- ADC (analog-to-digital converter) optimization as a secondary precision bottleneck

I followed this thread because the Hardware & Physical Computing interest area had been covered in BUILD cycles (RISC-V, neuromorphic, RTX optimization) but the analog CIM sub-domain had not received fresh EXPLORE research since at least May 2024.

---

## 2. What I Found

### The Precision Problem — And Its Partial Solution

Analog in-memory computing faces a fundamental challenge: analog signals are noisy. Device resistance varies, temperature drifts, and ADCs introduce quantization error. Until recently, analog CIM accuracy lagged behind digital counterparts by a meaningful margin, limiting deployment to tolerance-heavy edge workloads.

**Breakthrough (October 2025):** Researchers at Peking University and the Beijing Advanced Innovation Center for Integrated Circuits published results in *Science Advances* demonstrating ultrahigh-precision analog computing using **geometric-ratio encoding** instead of intrinsic device resistance values. By encoding weights through stable transistor geometry ratios rather than volatile resistance states, they achieved accuracy rivaling digital computation.

Key paper: "Ultrahigh-precision analog computing using memory-switching" (Science Advances, 2025). A companion Nature paper (s44335-025-00044-2) independently validates the approach for resistive-memory-based AIMC.

### Commercial Landscape — Four Players Shipping

| Company | Technology | Funding | Status |
|---------|-----------|---------|--------|
| **EnCharge AI** | Analog CIM using metal-wire capacitors | $144M+ (Series B, Tiger Global) | EN100 chip shipping: 200 TOPS, PCIe form factor |
| **Mythic** | Analog CIM for edge AI | Previously disclosed | Active edge deployments |
| **D-Matrix** | All-digital SRAM CIM (not analog) | Previously disclosed | Chiplet-based datacenter LLM inference accelerator |
| **Sagence AI** (fmr. Analog Inference) | Analog in-memory compute for generative AI | Previously disclosed | Emerged from stealth Nov 2024 |

**EnCharge AI EN100** is notable: 200 TOPS of AI inference using analog memory formed from metal-wire capacitors — no exotic materials required, meaning it can be fabricated on standard CMOS processes. This is a significant scalability advantage over RRAM/PCM approaches that require non-standard fabrication.

### ADC Optimization as Secondary Bottleneck

Even with precision weights, the column ADCs that read out analog computation results consume disproportionate energy. Two optimization paths emerged in 2025:

1. **SNR-optimal ADC design** (arXiv:2507.09776) — reduces ADC precision while maintaining computational accuracy through AIMC-specific signal distribution modeling
2. **Adaptive calibration** (PatSnap 2026 landscape report) — multi-stage conversion with dynamic range optimization

The insight: ADC precision does not need to match weight precision. The signal distribution at the ADC input in AIMC systems is non-uniform, allowing lower-precision ADCs than naive design would suggest.

---

## 3. What I Think Is Interesting

The geometric-ratio encoding approach is the most significant development because it **decouples precision from device physics**. Instead of fighting against inherent analog noise, it sidesteps the problem entirely by encoding information in something that does not drift — the physical size ratio of transistors. This is analogous to how modern digital circuits use voltage thresholds rather than absolute voltage values.

The EnCharge EN100 use of standard CMOS metal-wire capacitors is equally important for commercialization. Most analog CIM research requires exotic materials (RRAM, PCM, memristors) that need foundry partnerships or custom fabrication. Standard CMOS means these chips can be manufactured today by TSMC, GlobalFoundries, or any comparable foundry.

The energy efficiency implications are substantial. The von Neumann bottleneck — moving data between processor and memory — consumes more energy than the computation itself for memory-bound workloads like AI inference. Analog CIM eliminates that movement entirely. For edge deployments (where EnCharge and Mythic are targeting), this means inference that was previously power-constrained becomes feasible.

---

## 4. What I'd Explore Next

- **Memristor maturity assessment:** The memristor-based approach (RRAM, PCM) is still being actively researched. Are there deployment timelines beyond academic papers?
- **Analog CIM vs. digital SRAM CIM tradeoff:** D-Matrix all-digital approach avoids analog noise entirely while still achieving in-memory compute benefits. Where does each approach win?
- **Compiler toolchain maturity:** Analog CIM requires a different software stack. How mature are the compilers that map neural networks to analog hardware?
- **Large-scale LLM inference on analog hardware:** Current deployments target edge/small models. Is analog CIM viable for 70B+ parameter models?

---

## 5. Cross-Domain Connections

- **Entity Resolution:** Analog CIM energy efficiency could dramatically lower the cost barrier for running large-scale entity resolution pipelines at the edge (e.g., on-premise government infrastructure where data cannot leave the network)
- **Neuromorphic Computing:** Analog CIM and neuromorphic computing share the same underlying motivation (von Neumann bottleneck) but different approaches. Neuromorphic focuses on event-driven spiking neural networks; analog CIM focuses on matrix multiplication acceleration. They may converge on hardware.
- **RISC-V AI Acceleration:** Both represent non-von Neumann compute approaches. RISC-V focuses on ISA flexibility for digital compute; analog CIM focuses on physics-level parallelism. They could be complementary — RISC-V control plane managing analog CIM data plane.
- **Edge AI for Critical Infrastructure:** EnCharge PCIe form factor makes it directly applicable to substation edge computing — running anomaly detection models locally without cloud dependency.

---

*Sources: Science Advances (2025), Nature s44335-025-00044-2, TechCrunch (EnCharge Series B, Sacgence stealth emergence), EE Times (D-Matrix), IEEE Xplore (ADC optimization), arXiv:2507.09776, PatSnap 2026 landscape report, TrendForce (Chinese precision breakthrough)*
