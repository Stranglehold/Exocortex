# Processing-in-Memory Architectures & RISC-V Edge AI Accelerators

**Status:** STABLE
**Created:** 2026-06-06
**Source:** EXPLORE field report (2026-06-06)
**Topics:** Hardware & Physical Computing, AI Agent Architecture, Local Inference

---

## Core Thesis

The next generation of edge AI hardware is being reshaped not by more FLOPS, but by **data movement minimization** and **open, reconfigurable architectures**. Processing-in-Memory (PIM) and open-source RISC-V AI accelerators represent two converging approaches that share a common design principle: **move compute to data, not data to compute.**

This principle — PIM as architectural philosophy — generalizes far beyond silicon. It applies to database design (columnar stores, pushdown), agent architecture (injection gate, stateful injection), and context management (prune in-place rather than reload).

---

## 1. Processing-in-Memory (PIM)

### The Memory Wall Problem

PatSnap 2026 tech landscape analysis (80+ patent/literature records) identifies memory bandwidth and energy — not raw compute throughput — as the primary engineering constraint for edge AI inference. Google's Edge TPU characterization (2021) across 24 neural network models found the device operating significantly below peak computational throughput, with **memory system energy as the dominant inefficiency.**

| Sub-Domain | Role | 2026 Status |
|---|---|---|
| Dedicated silicon (ASICs, TPUs, neuromorphic) | Fixed-function efficiency | Axelera Metis: 15 TOPS/W via in-memory compute |
| FPGA accelerators | Reconfigurable inference | ztachip: 20-50x acceleration on low-end FPGAs |
| PIM architectures | Memory-compute integration | TetraMem: 22nm RRAM analog IMC |
| Near-memory computing | Logic adjacent to memory | ETH Zurich DRAM-PIM (2022) |
| Hybrid architectures | NPU+PIM combined | P3-LLM (arXiv:2511.06838) |

### TetraMem 22nm RRAM Analog IMC

- **Milestone:** May 2026 — first multi-level RRAM analog in-memory computing SoC milestone
- **Technology:** 22nm process at TSMC, memristor arrays achieving thousands of conductance levels
- **Key publications:** Nature (March 2023) — thousands of conductance levels in memristors integrated on CMOS; Science (February 2024) — programming memristor arrays with arbitrarily high precision
- **Significance:** Analog in-memory computing performs matrix operations directly in the memory array using Ohm's law and Kirchhoff's current law — no data movement between memory and ALU

### P3-LLM: NPU-PIM Hybrid for Edge LLM Inference

- **Paper:** arXiv:2511.06838
- **Architecture:** Integrated NPU-PIM accelerator specifically designed for edge LLM inference
- **Key insight:** Hybrid architecture addresses the mismatch between transformer attention (memory-intensive) and feed-forward layers (compute-intensive)

---

## 2. RISC-V Open-Source AI Accelerators

### ztachip

- **Repository:** github.com/ztachip/ztachip (MIT License)
- **Architecture:** Multi-core tensor processor for edge AI and computer vision
- **Performance:** 20-50x acceleration on low-end FPGAs vs CPU-only inference
- **Key characteristic:** Open-source RISC-V ISA provides architectural diversification from proprietary ARM/x86 lock-in
- **Relevance to Exocortex:** ztachip-class accelerators combined with custom PCB sensor nodes enable autonomous grid monitoring without cloud dependency

### Supply Chain Implications

- TetraMem manufacturing at **TSMC 22nm** — RRAM-PIM supply chain is Taiwan-concentrated, same geopolitical vulnerability as advanced logic
- Open-source RISC-V (ISA is Berkeley-originated, developed globally) provides architectural diversification
- Dual-use dynamic: PIM accelerators equally applicable to autonomous sensor networks and edge surveillance

---

## 3. Cross-Domain Connections

| Domain | Connection |
|---|---|
| **Privacy & Cryptography** | Edge inference via PIM/RISC-V enables fully local agent inference — hardware substrate for metadata-resistant AI |
| **Electric Utility & Critical Infrastructure** | PIM's ultra-low-power profile for distributed sensor networks on the grid |
| **Geopolitics & Strategic Analysis** | TSMC concentration = same geopolitical vulnerability as advanced logic; RISC-V provides diversification |
| **OSINT & Investigation** | ztachip-based devices running local entity resolution models without data exfiltration risk |
| **AI Agent Architecture** | What does agent architecture look like when inference is effectively free at the edge? |
| **Context Management** | PIM philosophy (compute-to-data) mirrors injection gate and stateful injection patterns |
| **Sensor Networks** | Custom PCB + PIM/RISC-V = autonomous grid monitoring without cloud dependency |
| **Bridging Local-to-Frontier** | Hardware acceleration as one dimension of closing the local-frontier performance gap |

---

## 4. Key Structural Insight

**PIM is not just a hardware architecture — it is a design philosophy.** The principle of "move compute to data, not data to compute" maps directly to:

1. **Injection gate:** Inject only what's needed where it's needed, rather than reloading full context
2. **Stateful injection:** Persistent state objects that update in-place rather than being rebuilt each turn
3. **Context pruning:** Prune tokens in-place rather than archive-and-reload
4. **Memory consolidation:** Deduplicate and promote within the memory store rather than external batch processing

This is the "PIM principle" as a cross-layer architectural invariant — the same optimization that reduces energy-per-inference in silicon also reduces tokens-per-turn in agent architectures.

---

---

## 5. PIM as Cross-Layer Architectural Invariant

### The Core Insight

PIM is not just a hardware architecture — it is a **design philosophy** that recurs at every layer of the AI stack. The principle of "move compute to data, not data to compute" generalizes:

| Layer | Classic Approach | PIM-Principle Approach | Example |
|---|---|---|---|
| **Silicon** | Move weights from DRAM to ALU | Compute in memory array (Ohm's law) | TetraMem MLX200 RRAM analog IMC |
| **Inference Engine** | Per-request isolated KV caches | Shared asymmetrically-compressed KV cache pool | PolyKV: 97.7% memory reduction |
| **Agent Architecture** | Build context from scratch each turn | Stateful injection — persistent objects mutate in-place | Exocortex Injection Gate |
| **Context Management** | Archive-then-reload resolved results | Prune tokens in-place within active context | Context Pruner |
| **Memory Consolidation** | External batch dedup/promotion | Deduplicate and promote within memory store | Sleep consolidation pipeline |
| **Self-Evolving Agents** | Ad hoc reflection, unstructured memory | Structured experience graph with online growth | EXG: cross-task experience reuse |

### PolyKV (arXiv:2604.24971): PIM Principle at the Inference Layer

PolyKV demonstrates the PIM principle at the LLM inference architecture layer: multiple concurrent agents share a **single asymmetrically-compressed KV cache pool** rather than allocating isolated caches per agent.

- **Compression:** Keys quantized at int8 (q8_0) to preserve softmax stability; Values compressed via TurboQuant MSE — Fast Walsh-Hadamard Transform (FWHT) rotation followed by 3-bit Lloyd-Max quantization
- **Memory reduction:** 97.7% reduction in KV cache memory
- **Quality preservation:** +0.57% perplexity degradation, mean BERTScore F1 of 0.928
- **Scalability:** PPL delta does not grow with agent count (tested at 3, 5, 10, 15 agents), compression ratio invariant across agent counts
- **Architecture:** HuggingFace DynamicCache objects; each agent receives a reference to the shared pool, generates independently without cache contention

**Structural isomorphism:** PolyKV's shared cache pool is to inference infrastructure what PIM is to silicon — compute (inference) moves to where the data (KV cache) already lives, eliminating redundant data movement. The same optimization that reduces femtojoules-per-MAC in analog IMC reduces gigabytes-of-VRAM-per-agent in multi-agent inference.

### EXG (arXiv:2605.17721): PIM Principle for Self-Evolving Agents

EXG (Experience Graph) organizes agent successes and failures into a **structured relational representation** — an experience graph — rather than unstructured memory:

- **Online growth:** Graph grows in real-time during execution for immediate cross-task experience reuse
- **Offline reuse:** Consolidated graph functions as external memory module
- **Plug-and-play:** Integrates with existing self-evolving agents, organizing prior experience into unified graph
- **PIM isomorphism:** Structuring experience as a graph keeps it "where the retrieval happens" — query runs against structured relations rather than moving raw fragments into context for inspection

---

## 6. 2026 Developments (Deepening)

### TetraMem MLX200 Silicon Validation (May 2026)

- **Milestone achieved:** First multi-level RRAM analog in-memory computing SoC on 22nm silicon, tape-out, manufacturing, and initial silicon validation completed
- **MLX200/MLX201 platforms:** Designed for power- and latency-sensitive edge AI applications — voice/audio processing, wearables, IoT, always-on sensing
- **Manufacturing:** TSMC 22nm process. IP available for evaluation and licensing
- **Timeline:** Evaluated sampling expected H2 2026
- **Beyond edge:** TetraMem also demonstrated 700°C RRAM/memristor breakthrough (May 2026) — path toward deep-space AI computing where conventional silicon fails
- **Supply chain note:** TSMC concentration creates geopolitical exposure. RISC-V open-source architecture provides diversification path

### RISC-V Edge LLM Inference (2025-2026)

| Paper | Venue | Key Contribution |
|---|---|---|
| "LLM Acceleration Using Xiangshan RISC-V Processor" | arXiv:2409.00661 | Open-source matrix instruction set extension (vector dot product) for RISC-V LLM acceleration |
| "Accelerating LLM Inference on RISC-V Edge Devices via Vector Extension Optimization" | Springer, 2025 | 4-bit vector load + 8-bit dot-product instructions, tiled flash attention on RISC-V |
| "P3-LLM: Integrated NPU-PIM Accelerator for Edge LLM Inference" | arXiv:2511.06838 / ISCA 2026 | Hybrid NPU-PIM architecture addressing transformer attention (memory-intensive) vs feed-forward (compute-intensive) mismatch |

### ztachip: Open-Source RISC-V AI Accelerator

- **Architecture:** Multicore, data-aware, embedded RISC-V AI accelerator. Domain-Specific Architecture (DSA) with innovative tensor processor hardware
- **Performance:** 20-50x acceleration vs non-accelerated RISC-V on vision/AI tasks; outperforms RISC-V with vector extensions
- **Target:** Low-end FPGA devices or custom ASIC
- **Software ecosystem:** Python API, MicroPython API, Arduino Library — democratizing AI on edge devices
- **Next steps:** ASIC tape-out on open-source SKY130 or GF180 Process Development Kit (PDK) via Efabless
- **License:** MIT License (GitHub: ztachip/ztachip)

### PatSnap 2026 Edge AI Inference Accelerator Tech Landscape

Synthesized from 80+ patent and literature records, the landscape identifies five interlocking sub-domains:

1. **Dedicated silicon** (ASICs, TPUs, neuromorphic) — Axelera Metis: 15 TOPS/W via in-memory compute
2. **FPGA accelerators** — ztachip: 20-50x on low-end FPGAs
3. **PIM architectures** — TetraMem RRAM analog IMC
4. **Near-memory computing** — ETH Zurich DRAM-PIM
5. **Hybrid architectures** — P3-LLM NPU+PIM combined

---

## 7. Cross-Domain Connections (Expanded)

| Domain | Connection |
|---|---|
| **Privacy & Cryptography** | Edge inference via PIM/RISC-V enables fully local agent inference — hardware substrate for metadata-resistant AI |
| **Electric Utility & Critical Infrastructure** | PIM ultra-low-power profile for distributed sensor networks; ztachip-class accelerators + custom PCB = autonomous grid monitoring without cloud dependency |
| **Geopolitics & Strategic Analysis** | TetraMem TSMC 22nm = Taiwan-concentrated supply chain vulnerability; RISC-V provides architectural diversification |
| **OSINT & Investigation** | ztachip-based devices running local entity resolution models without data exfiltration risk |
| **AI Agent Architecture** | PIM principle directly maps to injection gate, stateful injection — what does agent architecture look like when inference is effectively free at the edge? |
| **Context Management** | PIM philosophy (compute-to-data) mirrors PolyKV shared cache pool, Exocortex context pruning, injection gate patterns |
| **Memory Architecture** | EXG's structured experience graph as PIM for agent memory — query runs against structured relations rather than loading fragments into context |
| **Local-to-Frontier Bridging** | Hardware acceleration (PIM, RISC-V) as one dimension of closing the local-frontier performance gap |
| **Self-Evolving Agents** | EXG experience graph as PIM-principle for agent self-improvement — online graph growth, cross-task reuse |
| **Sensor Networks** | Custom PCB + PIM/RISC-V = autonomous monitoring without cloud dependency |

---

## 5. Open Questions (Original)

1. What does agent architecture look like when inference is effectively free at the edge?
2. Can ztachip-class accelerators actually run production LLM inference (not just CNNs/vision)?
3. What's the geopolitical exposure of RRAM-PIM manufacturing given TSMC concentration?
4. How does analog IMC precision (quantization noise) interact with LLM inference quality?

---

## Sources

1. PatSnap, "Edge AI Inference Accelerators: 2026 Tech Landscape" — 80+ patent/literature records
2. TetraMem Inc., "22nm Multi-Level RRAM Analog In-Memory Computing SoC Milestone" — TechPowerUp, May 18, 2026
3. ETH Zurich, "Accelerating Neural Network Inference With Processing-in-DRAM" — 2022
4. Ztachip GitHub Repository — github.com/ztachip/ztachip (MIT License)
5. Hackster.io, "The Open Source Ztachip Is a RISC-V Accelerator for Edge AI and Computer Vision Applications"
6. P3-LLM: "An Integrated NPU-PIM Accelerator for Edge LLM Inference" — arXiv:2511.06838
7. Low-Latency PIM Accelerator for Edge LLM Inference — IEEE, 2025
8. NAAS: "Neural Accelerator Architecture Search" — Shanghai Jiao Tong University, 2021
9. TetraMem, "Thousands of conductance levels in memristors integrated on CMOS" — Nature, March 2023
10. TetraMem, "Programming memristor arrays with arbitrarily high precision for analog computing" — Science, February 2024
11. IPValueLabs, "ASIC vs FPGA for Edge AI Inference: 2026 Performance, Cost & Architecture Guide"
