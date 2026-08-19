# Field Report: FPGA-Based Inference Acceleration — State of the Art 2026

**Date:** 2026-05-26
**Cycle:** EXPLORE
**Interest:** Hardware & Physical Computing

---

## 1. What I Explored

I followed the thread of **FPGA-based LLM and AI inference acceleration** — the least recently explored active interest (last touched 2026-05-20 in a brief RTX 3090 optimization field report). My goal: map the current frontier, identify open-source projects, and understand where FPGAs fit in the broader local-inference landscape alongside GPUs.

---

## 2. What I Found

### 2.1 Open-Source FPGA LLM Accelerators

The standout discovery is **llama-fpga** (adamgallas/llama-fpga, GitHub), presented at DATE'25 and ICCAD'25. It's described as "probably the world's first open-source project for building an FPGA-based LLM accelerator," capable of running LLaMA2-7B in AWQ 4-bit quantized format on both embedded and data center FPGAs. This is significant — it brings FPGA accel into the LLM era, competing with GPU-based quantization approaches.

**SpeedLLM** (arXiv 2507.14139) targets Tinyllama on Xilinx Alveo U280 FPGAs with a custom co-design approach, promising efficient inference through innovations in neural network computation specifically engineered for FPGA platforms.

### 2.2 Reliability & Safety-Critical Acceleration

**RePAIR** (ACM 2026) addresses a concern unique to FPGAs in safety-critical applications: Single Event Upsets (SEUs). It provides fast detection and recovery for FPGA-based AI accelerators, making them viable for aerospace, automotive, and medical deployments where bit-flips from radiation are unacceptable. This is a capability GPUs don't natively address.

### 2.3 Design Tools & Frameworks

- **Altera FPGA AI Suite** — streamlines collaboration between FPGA engineers (IP integration, timing closure) and software integrators (host-side plumbing). Acknowledges that coordination is a major bottleneck when designs change frequently.
- **FINN Framework** (Xilinx/AMD) — end-to-end CNN acceleration pipeline: training → quantization → FPGA inference. Proven in CNN-based applications (precision agriculture use case demonstrated).
- **Verkor.io VerTQ TurboQuant Accelerator** — commercial offering that builds FPGA, ASIC, or SoC for edge AI deployment, positioning itself as a "Conductor" platform for heterogeneous hardware targets.
- **LLM-driven design space exploration** (arXiv 2605.05920, May 2026) — uses open-source LLMs to explore FPGA accelerator design spaces, automating what was previously manual HLS parameter tuning.

### 2.4 Vendor Landscape

- **AMD/Xilinx**: Dominant in research (Alveo U280 used in multiple papers), mature tooling (FINN, Vitis)
- **Intel/Altera**: FPGA AI Suite targets production teams, emphasizing workflow integration
- **Lattice Semiconductor**: Low-power edge AI solutions with pre-optimized neural network inference on programmable fabric — positioned for vision and sensor processing

### 2.5 The Edge AI Landscape

A PatSnap analysis of 80+ patent and literature records (2026) identifies FPGAs alongside dedicated silicon and Processing-in-Memory (PIM) architectures as key edge AI accelerator technologies, with Neural Architecture Search (NAS) and distributed inference emerging as complementary techniques.

---

## 3. What I Think Is Interesting

**FPGAs are entering the LLM era.** For years, FPGA inference meant CNNs or tiny transformer models. llama-fpga running LLaMA2-7B in 4-bit changes the conversation — this is now a credible alternative to GPU inference for certain deployment profiles, especially where power, latency determinism, or radiation tolerance matter.

**The tradeoff is reconfigurability vs throughput.** GPUs win on absolute TOPS and ecosystem maturity; FPGAs win on watts-per-inference, latency predictability (no scheduler overhead), and the ability to implement custom dataflow architectures that eliminate memory bottlenecks — a known limitation for transformer attention layers on GPUs.

**The design tool gap is closing.** Historically, the FPGA "expertise wall" — needing RTL or HLS skills — kept it niche. LLM-driven design space exploration and higher-level frameworks (FINN, FPGA AI Suite) are making the technology accessible to ML engineers who don't write Verilog. This is the same democratization pattern that CUDA brought to GPUs a decade ago.

**Radiation hardening is an underappreciated differentiator.** RePAIR's SEU detection/recovery has no GPU equivalent. For Jake's interest in critical infrastructure and sensor networks, an FPGA that can self-correct in high-radiation environments (substations, remote sensors, aerospace) is genuinely compelling.

**The open-source momentum matters.** llama-fpga being open-source and presented at top-tier conferences (DATE, ICCAD) signals that FPGA LLM acceleration is transitioning from industry R&D labs to the academic mainstream — where GPU inference was circa 2015.

---

## 4. What I'd Explore Next

- **Benchmark llama-fpga vs llama.cpp on equivalent hardware class** — what's the actual latency and power comparison for 7B models?
- **High-Level Synthesis (HLS) for custom attention kernels** — can we implement FlashAttention on FPGA fabric to address the memory bottleneck?
- **Hybrid FPGA+GPU architectures** — split inference between FPGA (attention layers) and GPU (feed-forward layers) for energy-optimized deployment
- **FPGA-based secure enclave for inference** — tie into the privacy/cryptography interest: can FPGA bitstreams provide verifiable computation guarantees (ZK-adjacent) that GPUs can't?

---

## 5. Cross-Domain Connections

**→ RTX 3090 optimization (Hardware):** This is the same problem — local inference acceleration — with a different hardware tradeoff profile. The knowledge from llama.cpp optimization (quantization format selection, KV cache compression, speculative decoding) applies directly to FPGA accelerator design. Conversely, FPGA memory architecture insights (streaming dataflow, on-chip SRAM utilization) could inform GPU kernel optimization.

**→ Privacy & Cryptography:** FPGA bitstreams are auditable in ways GPU firmware isn't. If we need verifiable inference ("prove the model ran without modification"), FPGA-based secure enclaves connect to the ZKP/homomorphic encryption thread.

**→ Electric Utility & Critical Infrastructure:** FPGAs already dominate substation automation (IEC 61850, protection relays). Adding on-device inference to existing FPGA infrastructure — anomaly detection on SCADA data, local sensor fusion — doesn't require new hardware, just new bitstreams. This is the lowest-friction path to AI-at-the-edge in the grid domain.

**→ Agent Architecture:** The Exocortex's local-inference roadmap (RTX 3090 → agent inference) could benefit from FPGA offload for specific model components — e.g., token embedding lookup, attention pattern computation, or entropy calculation — freeing GPU cycles for the main transformer forward pass.
