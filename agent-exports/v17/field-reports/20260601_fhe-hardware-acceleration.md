# Field Report: Fully Homomorphic Encryption — Hardware Acceleration State of the Art (2026)

**Date:** 2026-06-01
**Cycle:** EXPLORE
**Topic:** Privacy & Cryptography → Homomorphic Encryption → Hardware Acceleration
**Status:** Complete

---

## 1. What I Explored

The interests.md directive for Privacy & Cryptography asks: "Homomorphic encryption practical state of the art." The prior HE field reports (20260526, 20260528) covered the general landscape, Zama, CryptOracle, and VFHE for agent verification. The 20260526 report identified hardware acceleration as the critical bottleneck: FHE is still six orders of magnitude slower than plaintext. This cycle followed the hardware thread specifically — examining the GPU/FPGA/ASIC acceleration frontier in 2026 through the research trajectory of Jung Ho Ahn (Seoul National University), the author of the Cheddar GPU library and a leading figure in FHE hardware co-design.

Threads followed:

1. **Ahn's research trajectory (2020-2026)** — from profiling NTT bottlenecks on GPUs, through custom ASIC architectures (BTS, ARK, SHARP, CiFHER), to the Cheddar GPU library that achieved sub-25ms CNN inference on an RTX 5090
2. **The DARPA DPRIVE target** — custom ASIC-level performance on commodity GPUs, now met or exceeded
3. **Intel Heracles** — a programmable FHE accelerator announced at ISSCC 2026, signaling the shift from fixed-function ASICs to programmable hardware
4. **The bottleneck migration story** — NTT → memory bandwidth → on-chip cache, a diagnostic lesson for any compute-bound workload

---

## 2. What I Found

### 2.1 Phase 1: Demystifying FHE on Conventional Hardware (2020-2021)

Ahn's IISWC 2020 paper analyzed Number Theoretic Transform (NTT), the most compute-intensive FHE operation, on GPUs. Key finding: prior GPU implementations treated NTT like FFT and missed optimization opportunities. On-the-fly twiddle factor generation maximized GPU memory bandwidth. His IEEE Access 2021 paper on homomorphic multiplication (HMult) achieved 4.05× speedup on GPUs through parallelization of NTT and CRT.

The critical insight came in CHES 2021: bootstrapping (the noise-refresh operation that enables unbounded computation) is constrained by global memory bandwidth, not arithmetic throughput. Memory-centric optimizations — kernel fusion and optimal decomposition number selection — delivered over 100× faster bootstrapping on GPUs compared to single-thread CPUs.

### 2.2 Phase 2: Custom ASIC Accelerators (2022-2024)

Four major ASIC designs:

| Paper | Venue | Key Innovation |
|-------|-------|----------------|
| BTS | ISCA 2022 | Bootstrapping-specific architecture; balanced computation behind memory latency of evaluation key loading |
| ARK | MICRO 2022 | Runtime data generation + inter-operation key reuse eliminated 88% of off-chip memory accesses |
| SHARP | ISCA 2023 | 36-bit word length (not 64-bit!) with robust precision; halved area and power vs monolithic ASICs |
| CiFHER | IEEE SEED 2024 | Multi-chip module (MCM) architecture; chiplet-based design rivals monolithic ASIC performance at fraction of cost |

SHARP is particularly notable: the 36-bit word length finding challenges the default assumption that FHE requires 64-bit arithmetic — a precision engineering insight that later fed back into GPU optimization (Cheddar's 25-30 prime system using native 32-bit datapath).

### 2.3 Phase 3: Private AI Algorithm-Architecture Co-Design (2023-2024)

Deploying CNNs over FHE revealed a rotation bottleneck: CKKS ciphertexts are 1D vectors, but CNN feature maps are 2D/3D. HyPHEN (2024) introduced hybrid packing to cut rotation overhead. NeuJeans (CCS 2024) introduced Coefficients-in-Slot (CinS) encoding, bypassing slot permutations and fusing convolutions with bootstrapping. Result: ImageNet-scale CNN inference in seconds.

### 2.4 Phase 4: Breaking the Memory Wall on GPUs (2025-2026)

The HPCA 2025 Anaheim paper discovered a surprising bottleneck shift: after optimizing NTT, the new memory wall was *element-wise operations* — simple arithmetic ops limited by off-chip DRAM bandwidth, not complex transforms. Anaheim proposed Processing-in-Memory (PIM) architecture to offload these directly into DRAM.

**Cheddar (ASPLOS 2026):** The culmination. Key innovations:
- "25-30 prime system" exploiting native 32-bit GPU integer datapath instead of expensive 64-bit emulation
- Aggressive sequential and parallel kernel fusion
- Outperforms custom FPGA designs and prior GPU libraries by up to 4.45×
- ResNet-20 inference in 0.72 seconds on a single GPU

**Sub-25ms milestone on RTX 5090:** By combining Cheddar with AESPA's square polynomial activation approximations and a new encrypted convolution method, Ahn's group achieved sub-25ms inference for a 7-layer CNN on an off-the-shelf RTX 5090 — matching performance targets originally reserved for custom ASICs under the DARPA DPRIVE program.

**The new bottleneck: on-chip L2 cache bandwidth.** The ISPASS 2026 Theodosian microarchitectural study shows that modern GPUs are now so well-optimized for FHE that the limiting factor has shifted from off-chip DRAM to on-chip L2 cache. This is a diagnostic milestone: when your bottleneck is L2 bandwidth rather than DRAM, you've pushed the architecture to its fundamental limits.

### 2.5 Intel Heracles — The Programmable FHE Accelerator

At ISSCC 2026, Intel announced Heracles, a programmable FHE accelerator. This is significant because it validates the "programmable over fixed-function" philosophy. FHE algorithms are still evolving (new schemes, optimizations, bootstrapping algorithms), and fixed ASICs risk premature obsolescence. Heracles positions Intel as a platform rather than a point solution.

### 2.6 The Performance Trajectory

| Year | Platform | Operation | Latency | Improvement |
|------|----------|-----------|---------|-------------|
| 2020 | GPU (naive) | Bootstrapping | ~seconds | — |
| 2021 | GPU (CHES 2021) | Bootstrapping | ~10-20ms | 100× |
| 2024 | GPU (Cheddar) | ResNet-20 | 720ms | — |
| 2026 | RTX 5090 | 7-layer CNN | <25ms | ~30× over 2024 |

---

## 3. What I Think Is Interesting

### The Bottleneck Migration as a Diagnostic Framework

The FHE acceleration story is really a story about bottleneck migration: NTT was the compute bottleneck until memory bandwidth became the bottleneck. Memory bandwidth was the bottleneck until element-wise ops became the bottleneck. Element-wise ops were the bottleneck until L2 cache bandwidth became the bottleneck. This pattern — identify bottleneck, optimize it, discover the next bottleneck — is the universal engine of hardware acceleration. It applies equally to LLM inference, where we've seen: compute-bound (transformers) → memory-bandwidth-bound (KV cache) → now attention-mechanism-bound with new architectures.

### The Feedback Loop Between ASIC and GPU Design

Ahn's trajectory demonstrates something important: ASIC research informs GPU optimization. The 36-bit word length insight from SHARP (ASIC) became the 25-30 prime system in Cheddar (GPU). The ASIC discovery that off-chip memory was the bottleneck informed Anaheim's PIM architecture. This bidirectional flow — ASIC research → GPU implementation — is underappreciated and suggests a general methodology: design for the idealized case, then coerce commodity hardware toward it.

### The DARPA DPRIVE Target Has Been Hit on Commodity Hardware

DARPA's DPRIVE program set ambitious performance targets for FHE acceleration, originally assumed to require custom ASICs. Ahn's group achieved those targets on an off-the-shelf RTX 5090. This has major implications: it means the "FHE requires custom silicon" narrative is being replaced by "FHE requires intelligent optimization on programmable hardware." This parallels the ML inference trajectory — ASICs (TPUs) exist, but optimized GPUs remain the dominant workhorse because algorithms evolve faster than hardware design cycles.

### The Real Implications for Privacy-Preserving AI

Sub-25ms CNN inference on encrypted data opens practical deployment scenarios:
- **Private medical image classification** on encrypted patient scans
- **Confidential financial transaction screening** without exposing transaction details
- **Encrypted facial recognition** in surveillance contexts where biometric privacy is non-negotiable

The 0.72-second ResNet-20 inference is already viable for batch processing. The sub-25ms 7-layer CNN is viable for real-time interactive applications.

However, CNN inference is not LLM inference. The CKKS scheme supports polynomial operations (additions, multiplications) natively, but transformer attention (softmax, division, exponentiation) requires polynomial approximations that introduce error and overhead. The gap between CNN-over-FHE and LLM-over-FHE remains enormous and is the next frontier.

---

## 4. What I'd Explore Next

1. **FHE for LLM inference** — what are the current approaches to running transformer layers under CKKS? Zama's Concrete-ML supports tree-based models and neural networks, but LLM-sized models remain out of reach. When does the community anticipate practical encrypted LLM inference?

2. **The Intel Heracles architecture in detail** — ISSCC 2026 paper should be available by now. What's the microarchitecture? How programmable is "programmable"? Is it an FPGA-like overlay or a reconfigurable datapath?

3. **The L2 cache bottleneck and its implications** — if on-chip cache is the new ceiling, what architectural changes could break through? 3D-stacked cache (AMD's V-Cache approach)? On-die SRAM expansion? This connects directly to the RTX 3090/5090 optimization work in the Hardware & Physical Computing interest.

4. **FHE on consumer GPUs (RTX 3090) specifically** — all benchmarks cited use RTX 5090. What's the performance scaling factor to the RTX 3090 (24GB GDDR6X)? Could the Exocortex run FHE workloads on Jake's 3090?

5. **The AESPA square polynomial trick** — what's the accuracy penalty of replacing activation functions with square polynomials? Is it acceptable for practical CNNs?

---

## 5. Cross-Domain Connections

**Privacy/Cryptography ↔ Hardware & Physical Computing:** The entire FHE hardware acceleration story is directly relevant to the RTX 3090 optimization thread. The techniques — kernel fusion, datapath optimization (32-bit vs 64-bit), memory bandwidth taming, PIM — are the same techniques used for LLM inference optimization. The Exocortex's hardware exploration (RTX 3090 tensor core utilization, FPGA inference) overlaps substantially with FHE acceleration methodology. Knowledge transfers both ways.

**Privacy/Cryptography ↔ AI Agent Architecture:** The sub-25ms encrypted CNN inference milestone makes a specific architecture pattern viable: an agent that classifies or analyzes encrypted documents without ever seeing the plaintext. If an Exocortex agent receives an encrypted PDF, it could (in principle) classify, extract entities, or detect sensitive content entirely in the encrypted domain, producing encrypted results that only the key-holder can decrypt. This is the "blind computation" agent pattern — trustless data processing with cryptographic guarantees — distinct from the "verifiable computation" agent pattern covered in the 20260528 VFHE field report.

**The bottleneck-migration framework applies to Exocortex self-improvement:** The Exocortex's epistemic integrity system (injection gates, supervisor loops, confabulation detection) has its own bottleneck migration story. First the bottleneck was prompt quality, then it was hallucination frequency, then it was tool misuse, then it was context window management, and now it's proactive interference from accumulated memories. The same diagnostic methodology — benchmark, identify limiting factor, optimize, discover next bottleneck — applies across domains.

---

## References

- Ahn, Jung Ho, "Accelerating Fully Homomorphic Encryption: Bridging the Gap Between Cryptography and Computer Architecture," blog post, March 2026
- Cheddar: ASPLOS 2026, "A Swift Fully Homomorphic Encryption Library Designed for GPUs"
- Anaheim: HPCA 2025, Processing-in-Memory architecture for FHE
- SHARP: ISCA 2023, 36-bit word ASIC for FHE
- ARK: MICRO 2022, runtime data generation and key reuse
- BTS: ISCA 2022, bootstrapping-specific ASIC
- CiFHER: IEEE SEED 2024, multi-chip module FHE accelerator
- NeuJeans: CCS 2024, CinS encoding for CNN inference over FHE
- HyPHEN: IEEE Access 2024, hybrid packing for CNN over FHE
- Intel Heracles: announced at ISSCC 2026 (programmable FHE accelerator)
- FHECore: arXiv:2602.22229, GPU microarchitecture for FHE
