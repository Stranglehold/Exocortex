# FPGA Memory-Based LLM Inference — The Table-Lookup Turn

**Status:** STABLE

**Last Updated:** 2026-08-14

## Overview

A 2025-2026 architectural turn in FPGA LLM inference: instead of fighting GPUs on arithmetic throughput (MACs, DSP slices), accelerators convert arithmetic into **memory access** — table lookups over vector-quantized centroids — exploiting FPGAs' abundant distributed on-chip memory (BRAM/URAM/LUTRAM). The flagship result is **LUT-LLM** (UCLA + Microsoft Research, arXiv:2511.06174): the first FPGA accelerator to deploy a 1B+ parameter LLM (Qwen 3 1.7B on AMD V80) with memory-based computation. The same data-locality inversion appears across the 2026 system-level wave (FAST-Prefill, SkipOPU, HillInfer, SCIN, C2C-Explorer), positioning FPGAs as interconnect/memory-hierarchy accelerators rather than raw compute engines.

## Core Data Point: LUT-LLM (arXiv:2511.06174)

- **Paradigm shift:** replaces conventional linear layers with table lookups over pre-computed dot-product results; a memory-based MAC consumes only 3.8 pJ at 7nm (#2.4x less than an arithmetic MAC) and avoids online dequantization (values pre-computed in full precision).
- **Quantization scheme:** activation-weight **vector co-quantization** identified as the most effective scheme via a constructed performance model evaluating multiple VQ variants; enables 2D lookup tables (one dimension = activation centroid index, other = weight centroid index).
- **Prototype:** Qwen 3 1.7B on AMD V80 FPGA — reduces arithmetic operations by 4x; **1.10–3.29x faster generation** and **3.05–6.60x higher energy efficiency** than NVIDIA A100 / AMD MI210 at the same technology node.
- **Structural claim:** AMD V80 has **14.9x more on-chip memory units and ~2.5x greater on-chip capacity** than A100 — FPGAs' distributed on-chip memory, not DSP count, is the real differentiator.
- **Engineering pieces:** bandwidth-aware parallel centroid search (hides decode latency); prefix-sum-based 2D table lookup with SIMD accumulation; spatial-temporal hybrid design (attention in dataflow, linear layers sequential) freeing on-chip buffers.
- **Motivating baseline:** FlashAttention+FlashDecoding+GPTQ let A100 serve Llama-2-7B 2x–6.37x faster than prior state-of-the-art FPGA accelerators — the GPU bar keeps moving, hence the need for a fundamentally non-arithmetic strategy.

## The 2026 System-Level Wave

| System | arXiv | Role | Reported Result |
|---|---|---|---|
| FAST-Prefill | 2602.20515 | Long-context prefill, dynamic sparse attention, MPU (DSP + LUT bit-plane) | Up to 2.5x TTFT speedup, 4.5x energy vs A5000 at 4K-128K context |
| SkipOPU | 2026 search | Overlay processor, dynamic token/layer skip, float-fixed hybrid PEs, on-chip KV history buffer | 1.23-3.83x bandwidth efficiency; up to 25.4% KV storage reduction |
| HillInfer | 2602.18750 | SmartSSD/CSD-assisted KV eviction; lightweight token-importance eval on storage drive | Up to 8.56x speedup on long-context inference |
| SCIN | 2026 | Switch-centric in-network computing; multi-FPGA prototype | 1.8x/2.6x All-Reduce speedup vs NVLink SHARP; 1.12x TPOT / 1.42x TTFT |
| C2C-Explorer | 2608.08611 | Bayesian design-space exploration for chip-to-chip interconnect, validated on FPGA C2C prototypes | 2.46-8.23% end-to-end timing error; +44.1% goodput, -98.4% memory on 32-XPU DeepSeek-R1-671B |

## Why It Matters: The Value Proposition Inverted

For a decade the FPGA pitch was *parallel arithmetic without the GPU power bill*. LUT-LLM's performance model explicitly walks away from that: when limited to arithmetic, FPGAs lose to GPUs. The bet is instead **data and its location** — FPGAs have vastly more distributed on-chip memory per thread of compute, so converting arithmetic into memory access inverts the resource asymmetry. The same inversion appears throughout the 2026 corpus: SkipOPU's KV cache, HillInfer's near-data evaluation, SCIN's in-switch reduction. All are **data-movement optimizations dressed up as accelerators**.

## Trajectory: The Second-System Pattern

LUT-LLM is a clean single-chip story. As long context enters (FAST-Prefill, HillInfer) or multi-chip systems enter (C2C-Explorer, SCIN), the FPGA role migrates to the **interconnect and memory hierarchy** — the places GPUs are worst:

1. Standalone FPGA LLM inference (single chip, LUT-LLM)
2. FPGA as co-processor in the I/O path (SmartSSD/CSD, HillInfer)
3. FPGA in the switch/fabric (SCIN, C2C)

Real-world procurement (AMD Versal Gen 2, Alveo U280) is consistent with this trajectory.

## Honest Limits

- LUT-LLM requires a **training/recipe conversion** of the model (VQ + table construction) — not a drop-in serving layer.
- Reported per-device numbers are single-batch/device-local; no production fleet measurements.
- System-level claims (C2C goodput, SCIN TPOT) are simulation or prototype-validated, not independently verified production measurements (paper-reported only).
- Accuracy loss of Qwen-3-1.7B conversion is not yet independently quantified outside the paper; reproducibility dive on the open-source repo is open work.

## 2026 Open Threads

1. **LUT-LLM reproducibility:** open-source repo (github.com/LUT-FPGA/LUT-LLM) — conversion recipe, accuracy-loss quantification, transfer to other small models on Versal-class boards.
2. **FPGA + sensor-network convergence:** can a mid-range FPGA (Artix/Kintex) do event-based sensor preprocessing *and* small-model inference? Embedded-vision material suggests yes.
3. **YAVIN (arXiv:2608.13496):** processing-in-memory with ASCON-128 + LightSaber post-quantum KEM inside the memory hierarchy — the encryption-side version of compute-where-data-lives.
4. **AMD Versal Prime Gen 2 specs:** scalar/DSP/AI-engine counts vs V80 to test whether LUT-LLM-style designs port cheaply.

## Cross-Domain Connections

- **Memory-Centric AI Hardware (CXL/PIM):** LUT-LLM's "memory is the computer" thesis is the same data-locality argument as CXL-attached memory, at a different implementation layer (FPGA BRAM vs CXL fabrics).
- **Privacy & Cryptography:** YAVIN's in-memory TEE + post-quantum KEM makes secure edge LLM inference credible when PIM and FPGA memory are in the TCB.
- **FPGA Inference Acceleration (existing page):** this page is the memory-based complement to the arithmetic-based survey; LUT-LLM appears in both, here with the system-level 2026 corollaries.
- **Custom PCB Sensor Networks / Edge AI:** 3-6x energy-efficiency at single-batch latency makes FPGA-class inference plausible for power-constrained sensor nodes (grid, industrial telemetry).
- **Semiconductor Geopolitics:** AMD V80/Versal Gen 2 sits inside the US-China adaptive-SoC supply thread (TSMC 7nm/6nm allocation).
- **KV Cache & Speculative Decoding:** SkipOPU/HillInfer KV optimizations connect to the speculative-decoding/KV-compression page's data-movement thesis.
- **Quantization & Local LLM Inference:** vector co-quantization + lookup tables is a contiguous frontier to weight quantization (GPTQ, Low-bit) for local inference.
- **OSINT/SIGNAL processing:** FPGA embedded-vision co-processing (filtering, event-based DSP) is the sensor-edge foundation for RF/vision OSINT pages.

## References

1. LUT-LLM: Efficient Language Model Inference with Memory-based Computations on FPGAs — arXiv:2511.06174 (v2, Mar 2026)
2. FAST-Prefill: FPGA accelerator for long-context prefill — arXiv:2602.20515
3. HillInfer: SmartSSD/CSD-assisted KV eviction — arXiv:2602.18750
4. C2C-Explorer: Bayesian chip-to-chip interconnect exploration — arXiv:2608.08611
5. YAVIN: PIM/TEE with ASCON-128 + LightSaber PQC — arXiv:2608.13496 (abstract)
6. SkipOPU / SCIN: 2026 arXiv search results (abstracts; paper-reported)
7. Huang, A. "Hacking the Xbox" Appendix D — FPGA LUT/FF primitive framing (library p.250)
8. "Embedded Vision" — FPGA co-processing/inline architecture (library p.355)

**Grounded:** exocortex search_memory (LUT-LLM from fpga wiki + field reports) + search_library (Hacking the Xbox, Embedded Vision) + arXiv/paper text verification of LUT-LLM claims. Promoted from field report 20260814_fpga-memory-based-llm-inference.md.
