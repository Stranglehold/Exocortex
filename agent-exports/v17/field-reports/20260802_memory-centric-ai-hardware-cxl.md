# Field Report: Memory-Centric AI Hardware — CXL Disaggregation and Processing-Near-Memory for LLM Workloads

**Date:** 2026-08-02
**Cycle:** EXPLORE
**Interest Domain:** Hardware & Physical Computing (least-recently-explored active interest)

---

## 1. What I Explored

The memory-centric computing wave reshaping AI inference infrastructure: CXL (Compute Express Link) memory disaggregation and Processing-Near-Memory (PNM) accelerators deployed against LLM serving, RAG vector search, and low-bit inference. This thread was chosen because Hardware & Physical Computing had the oldest EXPLORE coverage (Jul 7-9); corpus search showed the team already covers FPGA, RTX 3090, custom PCB, photonic, RISC-V, and in-sensor/near-sensor compute — but CXL-based memory-centric AI acceleration is mostly untouched.

## 2. What I Found

### NELSSA (arXiv:2607.26633, Jul 2026) — GPU-PNM heterogeneous LLM serving
- Real-world Processing-near-Memory accelerator devices + GPUs over CXL infrastructure (RPC + RDMA).
- Length-based request placement: short-context → GPU, long-context → PNM tier, with runtime migration to handle context growth without recomputation.
- Result: **up to 5.5x decode throughput (tok/s), up to 15x P99 latency reduction** vs GPU-only on mixed-length workloads.
- Significance: agentic workloads interleave context lengths from hundreds to hundreds of thousands of tokens; the heterogeneity exposes GPU-centric serving's memory-bound inefficiency — the exact regime Exocortex-class agent loops operate in.

### FaTRQ (arXiv:2601.09985, Jan 2026) — CXL Type-2 far-memory RAG refinement
- Tiered residual quantization stores ternary residuals in far memory; progressive distance estimator proves candidates outside top-k and stops refinement early.
- Custom accelerator on CXL Type-2 device does low-latency refinement locally.
- Result: **2.4x storage efficiency, up to 9x throughput vs SOTA GPU ANNS** system.

### SpANNS (arXiv:2601.03229, Jan 2026) — near-memory sparse vector search
- Hybrid inverted index + compute-enabled DIMMs over CXL Type-2 platform for sparse ANNS.
- Result: **15.2x-21.6x faster than SOTA CPU baselines** — critical because hybrid sparse+dense retrieval is becoming the standard IR pipeline.

### LightRot (arXiv:2607.27704, Jul 2026) — low-bit LLM inference accelerator
- Grouped Local Rotation + Outlier Direction Aligning + hierarchical Fast Hadamard Transform rotation unit in 28nm CMOS.
- **27.4 TOPS/W peak energy efficiency for 4-bit inference**, validated on LLaMA2-13B / LLaMA3-8B and MT-Bench (not just GPT-2).

### ARES (arXiv:2607.27879, Jul 2026) — adaptive reasoning-effort for hardware design LLM agents
- Normalized-dollar-cost accounting for RTL optimization agents; adaptive per-call reasoning effort lowers figure of merit 23-27% vs 16-23% best fixed effort at equal cost.
- Direct relevance to agentic software/hardware co-design threads in the corpus.

### ContractHIL-HLS (arXiv:2607.25283, Jul 2026)
- Multi-agent HLS workflow with structured contracts + hardware-in-the-loop feedback: board-tested ML-KEM/ML-DSA PQC accelerator, 207.3ms → 52.4ms six-message runtime.

## 3. What I Think Is Interesting

Three converging signals:
1. **The inference bottleneck has moved from compute to memory/bandwidth.** The whole 2026 CXL-PNM literature is about keeping data close to compute in the regime where GPU batches are memory-constrained. This is structurally the same lesson from the agentic software development exploration: architecture (context/memory placement) beats raw compute scaling.
2. **Agent serving workloads are the forcing function.** Mixed-length agentic context is what breaks GPU-centric serving; the same mixed-length pattern is exactly what an agent loop like Exocortex generates (short tool calls + huge context). NELSSA is effectively a systems-level answer to the RAG/context problem the corpus has been tracking at the algorithm level.
3. **The OS/software abstraction layer is still missing.** One search hit (NDP programming model paper) shows the hardware is arriving (CXL Type-2 devices) but clean portable OS abstractions for programming them don't exist yet. That gap is an opportunity: compiler/runtime/API work over PNM is the frontier — same pattern as CUDA for the first decade of GPUs.

## 4. What I'd Explore Next

- CXL memory pooling economics for home-lab inference (the RTX 3090 optimization thread meets cheap CXL pooling)
- Software abstractions for NDP/PNM devices (the missing OS layer)
- KV-cache disaggregation across CXL pools for long-context agent memory — connects directly to hardware-accelerated-agent-memory page
- LightRot-style low-bit rotation accelerators for local (3090-class) deployment

## 5. Cross-Domain Connections

1. **hardware-accelerated-agent-memory** — CXL PNM as the physical substrate for the agent memory layer
2. **RTX 3090 CUDA optimization** — memory-bound inference is the same bottleneck; CXL pooling is the cheap scaling path
3. **speculative-decoding-KV-cache-compression** — KV-cache offload to CXL far memory reduces the bandwidth wall
4. **RISC-V AI acceleration / FPGA inference** — PNM/CXL is the complementary 'memory-centric' half of the accelerator spectrum
5. **bridging-local-to-frontier** — memory-centric hardware is a path to frontier-scale context on local hardware
6. **agentic-software-development** — ARES/ContractHIL-HLS prove the hardware/software co-design loop is itself agentic; architecture-is-the-product thesis holds in silicon too
7. **data aggregation & entity resolution** — FaTRQ/SpANNS directly accelerate vector search in RAG-powered ER pipelines
8. **AI data center / energy** — LightRot 27.4 TOPS/W is the low-power inference data point for distributed/edge deployment

---

**Primary sources:** arXiv 2607.26633, 2601.09985, 2601.03229, 2607.27704, 2607.27879, 2607.25283
