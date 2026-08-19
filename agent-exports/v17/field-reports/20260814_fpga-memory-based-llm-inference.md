# Field Report: FPGA LLM Inference — The Memory-Based Computation Turn
**Date:** 2026-08-14  
**Cycle:** EXPLORE  
**Interest:** Hardware & Physical Computing (least recently explored active interest; last touched 2026-08-12)
**Thread:** FPGA-based inference acceleration → memory/table-lookup computation for LLM inference

---

## 1. What I Explored

Jake's Hardware & Physical Computing interest has three sub-topics: FPGA-based inference acceleration, custom PCB design for sensor networks, and RTX 3090 optimization beyond standard CUDA. The corpus already has strong FPGA material (FAST-Prefill 2602.20515, TerEffic 2502.16473, LUT-LLM 2511.06174 PDFs in field-reports/sources/; wiki pages fpga-inference-acceleration.md and rtx-3090-cuda-optimization.md) plus the 20260807 hardware-AI-convergence report.

So instead of re-deriving that, I followed the newest live thread: **the shift from arithmetic-based to memory-based (table-lookup) computation for LLM inference on FPGAs**, and its 2026 system-level corollaries — FPGAs as interconnect/pipeline accelerators rather than raw compute engines.

## 2. What I Found

### LUT-LLM (arXiv:2511.06174, v2 March 2026) — the core data point
- First FPGA accelerator deploying a 1B+ parameter LLM with **memory-based computation** via table lookups (UCLA + Microsoft Research).
- Uses **vector quantization**; the winning scheme is **activation-weight vector co-quantization**, enabling 2D lookup tables where one dimension is activation centroid index, the other weight centroid index.
- Prototype: **Qwen 3 1.7B on AMD V80 FPGA** → reduces arithmetic operations by **4x**; achieves **1.10–3.29x faster generation** and **3.05–6.60x higher energy efficiency** than NVIDIA A100 / AMD MI210 at the same node.
- Key structural claim: **AMD V80 has 14.9x more on-chip memory units and 2.5x greater on-chip capacity than A100** — FPGAs' distributed on-chip memory is their real differentiator vs. GPU tensor cores.
- Engineering pieces: bandwidth-aware parallel centroid search (hides decode latency), prefix-sum-based 2D table lookup with SIMD accumulation, and a spatial-temporal hybrid design (attention in dataflow, linear layers sequential) that frees 14% on-chip buffers.
- In the motivating baseline: FlashAttention+FlashDecoding+GPTQ make A100 serve Llama-2-7B 2x–6.37x faster than prior state-of-the-art FPGA accelerators — the GPU bar keeps moving, hence the need for a fundamentally non-arithmetic FPGA strategy.

### The 2026 system-level wave around this thread
- **FAST-Prefill (arXiv:2602.20515):** first FPGA accelerator for long-context *prefill* with dynamic sparse attention; hybrid MPU using DSPs + LUT bit-plane decomposition; on Alveo U280 vs A5000 GPU → up to **2.5x TTFT speedup and 4.5x energy efficiency** at 4K–128K context.
- **SkipOPU (from 2026 arXiv search result):** FPGA overlay processor for dynamic computation allocation (skip tokens/layers); float-fixed hybrid PE array with DSP overpacking; proactive on-chip KV history buffer exploiting cross-layer KV invariance of pruned tokens → **1.23–3.83x bandwidth efficiency vs GPU and other FPGAs**, up to 25.4% KV storage reduction.
- **HillInfer (arXiv:2602.18750):** SmartSSD/CSD-assisted KV eviction for edge AIPCs; offloads only lightweight token-importance evaluation to the FPGA-based storage drive → **up to 8.56x speedup** vs baselines on long-context inference.
- **SCIN (2026):** switch-centric in-network computing for multi-GPU All-Reduce using an in-switch accelerator; validated on a **multi-FPGA prototype**; **1.8x / 2.6x All-Reduce speedup** (small/large messages) over NVLink SHARP, 1.12x TPOT / 1.42x TTFT.
- **C2C-Explorer (arXiv:2608.08611, Aug 2026):** Bayesian design-space exploration for chip-to-chip interconnect, **validated against FPGA-based C2C prototypes** (2.46–8.23% end-to-end timing error); on a 32-XPU DeepSeek-R1-671B workload found configs with **+44.1% goodput, −98.4% memory**.
- **AMD Versal Prime Series Gen 2 (May 2026):** up to 5x scalar compute vs existing AMD adaptive SoCs — vendor momentum behind adaptive compute for edge/infrastructure.

### Library grounding
- “Hacking the Xbox” (Bunnie Huang) Appendix D gives the durable framing: FPGAs are arrays of programmable primitives whose efficiency depends on whether the *natural data width* of an application matches 1-bit LUT/FF granularity — exactly why wide-matrix LLM workloads historically fit GPUs better. LUT-LLM's contribution is to re-shape the workload (VQ + lookup) to match the FPGA fabric.
- Embedded-vision book material reinforced the classic FPGA role: parallel adaptive filtering, event-based processing with DSP/AE pipelines — the sensor-network edge context that motivated Jake's original interest.

## 3. What I Think Is Interesting

**The FPGA value proposition inverted.** For a decade the pitch was “parallel arithmetic without the GPU power bill.” LUT-LLM's performance model explicitly walks away from that: when limited to arithmetic, FPGAs lose to GPUs. Instead the bet is **data and its location**: FPGAs have vastly more distributed on-chip memory per thread of compute, so if you convert arithmetic into memory access (table lookups over vector-quantized centroids), you invert the resource asymmetry. The same inversion shows up across the 2026 corpus — SkipOPU's KV cache, HillInfer's near-data evaluation, SCIN's in-switch reduction. All of these are **data-movement optimizations dressed up as accelerators**.

**The “second-system” pattern is already visible.** LUT-LLM is a clean single-chip story. But as soon as long context enters (FAST-Prefill, HillInfer) or multi-chip systems enter (C2C-Explorer, SCIN), FPGAs' role migrates to the *interconnect and the memory hierarchy* — the places GPUs are worst. That suggests a trajectory: standalone FPGA LLM inference → FPGA as co-processor in the I/O path → FPGA in the switch/fabric. Real-world procurement (Versal Gen 2, Alveo U280) is consistent.

**The honest limits:** LUT-LLM requires a training/recipe conversion of the model (VQ + table construction), so it is not a drop-in serving layer yet. Numbers are single-batch/device-local; system-level claims (C2C goodput, SCIN TPOT) are simulation or prototype-validated, not production fleet measurements. I report them as paper-reported, not independently verified.

## 4. What I'd Explore Next

1. **LUT-LLM reproducibility dive:** open-source repo (github.com/LUT-FPGA/LUT-LLM) — read the conversion recipe, check whether Qwen-3-1.7B accuracy loss is quantified, and whether the same recipe transfers to other small models (e.g., a 1B+ model Jake could run on a Versal-class board).
2. **FPGA + custom PCB convergence:** the sensor-network angle — can a single mid-range FPGA (e.g., Artix/Kintex) do both event-based sensor preprocessing *and* small-model inference? The SkipOPU/embedded-vision material suggests yes; a bill-of-materials survey would make it concrete.
3. **YAVIN (arXiv:2608.13496) PIM/TEE thread:** processing-in-memory with ASCON-128 + LightSaber post-quantum key exchange inside the memory hierarchy — a natural companion to the existing memory-centric AI hardware page and the FHE/ZKP work.
4. **AMD Versal Prime Gen 2 specs:** compare scalar, DSP, and AI-engine counts against V80 to see whether LUT-LLM-style designs port cheaply to the new family.

## 5. Cross-Domain Connections

- **Memory-Centric AI Hardware (CXL/PIM):** LUT-LLM's “memory is the computer” thesis connects directly to the 20260802 memory-centric hardware / CXL report — same data-locality argument, different implementation layer (FPGA LUTs/BRAM vs CXL-attached memory).
- **Privacy & Cryptography:** YAVIN's in-memory TEE with post-quantum KEM + ASCON-128 is the encryption-side version of the same “compute where data lives” move; secure edge LLM inference becomes credible when PIM and FPGA memory are both in the TCB.
- **Electric Utility & Critical Infrastructure / custom PCB sensor networks:** 3–6x energy-efficiency gains at single-batch latency make FPGA-class inference plausible for grid-sensor edge nodes (substation waveform/telemetry classification) with tight power envelopes, feeding the existing digital-twin and smart-meter-A MI security pages.
- **Geopolitics & Strategic Analysis / semiconductors:** the AMD V80/Versal Gen 2 trajectory sits inside the US–China semiconductor competition thread (adaptive SoC supply, TSMC 7nm/6nm allocation) already indexed in the wiki.
- **History of Intelligence Operations (adjacent):** Dryas's NFA-based, runtime-reprogrammable interconnect tracing is a close cousin of passive network observation tradecraft — hardware-level interception tooling as a physical-intelligence artefact.

---

**Sources:** arXiv:2511.06174 (LUT-LLM, full text read), arXiv:2608.08611 (C2C-Explorer, abstract), arXiv:2602.20515 (FAST-Prefill, abstract), arXiv:2602.18750 (HillInfer, abstract), arXiv:2608.13496 (YAVIN, abstract), 2026 arXiv search results (SkipOPU, SCIN, Mixture-of-Prefetchers abstracts), search_engine results (LUT-LLM GitHub/paper, FPGA Conference Europe 2026, AMD Versal Prime Gen 2 blog), exocortex library (Hacking the Xbox, Embedded Vision). Paper-reported numbers are labeled as such; none independently benchmarked this cycle.
