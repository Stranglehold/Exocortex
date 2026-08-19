# Memory-Centric AI Hardware: CXL Disaggregation & Processing-Near-Memory for LLM Workloads

**Status:** STABLE (deepened BUILD cycle 2026-08-02)
**Created:** 2026-08-02 (BUILD cycle — promoted from EXPLORE field report 20260802_memory-centric-ai-hardware-cxl.md)
**Last Updated:** 2026-08-02

## Overview

Memory-centric computing is reshaping AI inference infrastructure: CXL (Compute Express Link) memory disaggregation and Processing-Near-Memory (PNM) accelerators deployed against LLM serving, RAG vector search, and low-bit inference. The inference bottleneck has moved from compute to memory/bandwidth — GPU batches, KV-cache growth, and vector search are memory-constrained. This page consolidates the 2026 state of the art: GPU-PNM heterogeneous serving (NELSSA), CXL-based KV transfer and caching (TraCT, HyMCache), near-memory vector search (FaTRQ, SpANNS, Cosmos), low-bit inference accelerators (LightRot), and the measurement substrate (CXL-DMSim). It bridges the existing hardware-accelerated-agent-memory page with the local-to-frontier bridging and RAG/entity-resolution threads.

## Context: Why Memory-Centric Now

- Agentic LLM workloads interleave context lengths from hundreds to hundreds of thousands of tokens. This mixed-length pattern — short tool calls plus huge accumulated context — is precisely the regime that breaks GPU-centric serving and exposes memory-bound inefficiency.
- GPU HBM and host DRAM are too costly to scale to TB-scale shared KV-cache capacity; remote tiers built from lower-cost, higher-capacity media (DRAM, NAND behind CXL) are the economic answer.
- Shared corpus grounding (v16/v17 agent-exports):
  - [cxl-memory-pooling-ai-infrastructure-draft] — CXL pool/switch ecosystem, CXL 4.0, Penguin Solutions KV-cache server.
  - [hardware-software-codesign-ai-agents] §2.2 — memory capacity, not compute throughput, is the binding constraint for agent systems; disaggregation via CXL/UCIe/optical.
  - [chiplet-architectures-ai-inference] §5.1 — heterogeneous memory hierarchies (HBM + DDR5 + CXL-attached memory) for local/edge Exocortex-grade hardware.
  - [hardware-accelerated-agent-memory] — prior CXL pooling coverage for agent memory ops; this page digests the 2026 serving/PNM literature the earlier page did not.

## CXL Fundamentals & Measurement Substrate

- CXL 4.0 (Nov 2025): 128 GT/s via PCIe 7.0; bundled ports enabling 1.5 TB/s aggregate connections.
- Production switches emerging: Marvell Structera S 30260 (Q3 2026 sampling). First CXL-based KV-cache servers: Penguin Solutions (Mar 2026).
- **CXL-DMSim** (arXiv:2411.02282) — open-source full-system CXL disaggregated memory simulator validated against FPGA and ASIC devices (avg error 3.4%):
  - CXL-FPGA: ~2.88x latency vs local DDR, 45-69% of local DDR bandwidth.
  - CXL-ASIC: ~2.18x latency, 82-83% bandwidth.
  - Memory-intensive apps improve up to 23x (Viper key-value DB) and ~60% in bandwidth-sensitive workloads (MERCI).
  - Practical implication: CXL latency/bandwidth penalties are modest enough that memory-capacity wins dominate for KV and vector workloads.

## LLM Serving on Disaggregated Memory

### NELSSA (arXiv:2607.26633, Jul 2026) — GPU-PNM heterogeneous serving
- Real-world Processing-near-Memory accelerator devices + GPUs over CXL infrastructure (RPC + RDMA).
- Length-based request placement: short-context → GPU, long-context → PNM tier, with runtime migration to handle context growth without recomputation.
- Results: **up to 5.5x decode throughput (tok/s), up to 15x P99 latency reduction** vs GPU-only on mixed-length workloads.
- Significance: a systems-level answer to the agentic RAG/context problem — mixed-length context is the forcing function.

### TraCT — rack-scale CXL as KV-transfer substrate
- Disaggregated LLM serving separates compute-intensive prefill from latency-critical decode; KV tensors dominate transfer time.
- TraCT uses CXL shared memory as both KV-transfer substrate and rack-wide prefix-aware KV cache; GPUs read/write KV blocks via CXL load/store and DMA, eliminating the NIC hop.
- Results: **up to 9.8x average TTFT reduction, 6.2x P99 latency reduction, 1.6x peak throughput** vs RDMA/DRAM-caching baselines (implemented on Dynamo LLM inference framework).

### HyMCache — CXL-hybrid memory KV cache
- CXL-HM combines small in-device DRAM with large SSD-backed capacity behind a CXL interface; exploits read-dominant, predictable, append-only multi-turn KV access.
- Request-level prefix prefetching + opportunistic write buffering stage latency-critical reads in device DRAM: DRAM-scale KV efficiency at SSD-level cost.
- Results: **3.0x over local LMCache (single-node), 1.45x (PD-disaggregated); vs 1TB distributed-DRAM Mooncake ~30% lower performance with 16x less DRAM**.
- Significance: KV-cache offload to CXL far memory attacks the bandwidth wall directly — the practical path for agent-scale context.

## Near-Memory Vector Search (RAG)

### FaTRQ (arXiv:2601.09985, Jan 2026) — CXL Type-2 far-memory RAG refinement
- Tiered residual quantization stores ternary residuals in far memory; progressive distance estimator proves candidates outside top-k and stops refinement early.
- Custom accelerator on CXL Type-2 device performs low-latency refinement locally.
- Results: **2.4x storage efficiency, up to 9x throughput vs SOTA GPU ANNS**.

### SpANNS (arXiv:2601.03229, Jan 2026) — near-memory sparse vector search
- Hybrid inverted index + compute-enabled DIMMs over CXL Type-2 platform for sparse ANNS.
- Results: **15.2x-21.6x faster than SOTA CPU baselines** — critical because hybrid sparse+dense retrieval is becoming the standard IR pipeline.

### Cosmos (arXiv:2505.16096) — CXL in-memory ANNS offload
- General-purpose cores integrated within CXL memory devices for full ANNS offload; rank-level parallel distance computation maximizes memory bandwidth; adjacency-aware data placement balances load across CXL devices.
- Results: **up to 6.72x throughput vs baseline CXL, 2.35x over a SOTA CXL-based solution** on SIFT1B/DEEP1B billion-scale traces.

## The Expanding Systems Stack: Switch Pools, Hybrid Fabrics, and Host Offload

### Beluga — GPU/CPU shared memory pools via CXL switches (arXiv:2512.04476, Dec 2025)
- First system giving GPUs direct native load/store access to a large-scale CXL switch-based memory pool; near-local latency with reduced programming complexity vs RDMA disaggregation.
- Beluga-KVCache on vLLM: **89.6% TTFT reduction, 7.35x throughput improvement** vs RDMA-based solutions.
- Implication: switches remove the NIC hop for GPU-KV traffic at scale — TraCT's elimination of the NIC hop generalizes from rack-local to switch-fabric pools.

### ScalePool — unified XLink-CXL hybrid fabric (2026)
- Accelerator-Centric Links (XLink) for intra-cluster low-latency accelerator communication; hierarchical CXL switching for scalable, coherent inter-cluster memory sharing.
- Explicit memory tiering: latency-critical tier-1 (accelerator-local + CXL/XLink), high-capacity tier-2 (dedicated memory nodes behind CXL fabric).
- Results: LLM training **1.22x average / up to 1.84x** vs conventional RDMA environments; tier-2 disaggregation reduces latency up to **4.5x** for memory-intensive workloads.

### CXL AIC for long-context fine-tuning (2026)
- CXL add-in-card memory extends CPU memory for 7B/12B long-context fine-tuning (4K-32K contexts) on a single GPU.
- Core finding: naive placement of optimizer state on CXL causes ~4x optimizer slowdown past ~20M elements; **tensor-level NUMA control + CXL-aware allocator** (latency-critical tensors pinned in local DRAM, latency-tolerant tensors striped across CXL) recovers **97-99% of DRAM-only throughput** with one AIC, ~100% with two — up to 21% over naive interleaving.
- General principle: allocator/runtime co-design with CXL tiers is the missing software layer — same pattern as the NDP/PNM abstraction gap below.

## Low-Bit Inference Accelerators

- **LightRot** (field report source arXiv:2607.25283): 27.4 TOPS/W 4-bit rotation-based inference — the low-power data point for distributed/edge deployment and memory-centric local inference.

## The Missing Layer: NDP/PNM Software Abstraction

- Hardware is arriving (CXL Type-2 devices, PNM accelerators) but clean portable OS abstractions for programming them do not yet exist.
- This gap is an opportunity: compiler/runtime/API work over PNM is the frontier — structurally the same pattern as CUDA for the first decade of GPUs. A portable NDP programming model would unlock heterogeneous memory-centric serving at scale.

## Industry Adoption & Memory Economics (2026)

- **Samsung CMM-D 3.0** — CXL Memory Module-DRAM on CXL 3.2, mass production targeted by end of 2026 (TrendForce, 2026-07-21). CXL's core pitch: a separate low-cost memory tier that expands capacity without requiring additional GPUs or CPUs.
- **2026 sourcing reality**: Micron CZ120, Samsung CMM-D, and SK hynix CMM-DDR5 modules are largely hyperscaler-allocated under direct supply agreements; open-market/authorized distribution is limited to evaluation samples (TrendForce Q1 2026 briefings).
- **Market trajectory**: CXL memory expansion $1.3B (2025) → $11.8B (2034), 28.7% CAGR.
- **Meta Vistara** (Jun 2026): custom CXL memory expander reusing legacy DDR4 DIMMs in DDR5-only servers — a cost-arbitrage design that monetizes stranded inventory, reinforcing the economic (not just capacity) case for CXL tiers.
- **Production-adjacent stack**: Samsung evaluation with RTX PRO 6000 Blackwell + CMM-D configured as a 1TB CXL pool under vLLM/LMCache — the exact software stack Exocortex-class inference would run on.
- Watch items: Marvell Structera S 30260 switch sampling (Q3 2026) and CXL 3.2 mass-production timing gate general availability, not paper-stage capability.

## Exocortex Integration & Local-to-Frontier Implications

| Application | Mechanism | Hardware Path | Status |
|---|---|---|---|
| Agent long-context KV-cache | KV offload to CXL far memory/HM | TraCT-style CXL KV, HyMCache | Paper-stage / production-adjacent |
| Agent memory vector search | Near-memory ANNS offload | SpANNS, FaTRQ, Cosmos | Paper-stage |
| Mixed-length agent serving | Length-based GPU/PNM placement | NELSSA | Paper-stage |
| Local (3090-class) deployment | Cheap CXL pooling for capacity | CXL 3.0/4.0 + switches | Emerging (switches Q3 2026) |

- **Core thesis: memory placement beats raw compute scaling.** For agent systems, architecture (context/memory placement) is the product — isomorphic to the architecture-is-the-product finding from agentic-software-development.
- For local-to-frontier bridging: memory-centric hardware is a path to frontier-scale context on local systems; CXL pooling can give home-lab inference TB-scale memory at fraction of HBM cost.
- Exocortex note: shared corpus (v16/v17) and arXiv remain the primary grounding; the 355-book library crosses only thinly (general memory-hierarchy fundamentals, no CXL-specific coverage) — an honest gap, revisited each cycle as vendor docs mature. This deepening adds adoption economics (TrendForce 2026-07, market sizing, Meta Vistara) and expands the systems stack (Beluga, ScalePool, CXL-AIC fine-tuning).

## Cross-Domain Connections

1. **hardware-accelerated-agent-memory** — CXL/PNM is the physical substrate for the agent memory layer (this page's sibling; NELSSA/TraCT/HyMCache deepen it).
2. **rtx-3090-cuda-optimization** — memory-bound inference is the same bottleneck; CXL pooling is the cheap scaling path for 24GB-class rigs.
3. **speculative-decoding-kv-cache-compression** — KV-cache offload to CXL far memory reduces the bandwidth wall; complementary to lossless KV compression.
4. **hardware-software-codesign-ai-agents** — CXL/UCIe/optical disaggregation as the heterogeneous memory substrate for agent silicon.
5. **chiplet-architectures-ai-inference** — HBM+DDR5+CXL heterogeneous package memory for local models.
6. **bridging-local-to-frontier** — frontier-scale context on local hardware via cheap CXL pools.
7. **agentic-software-development** — hardware/software co-design loops (ARES/ContractHIL-HLS) prove the architecture-is-the-product thesis in silicon too.
8. **data aggregation & entity resolution** — FaTRQ/SpANNS/Cosmos directly accelerate vector search in RAG-powered ER pipelines.
9. **ai-anomaly-detection-critical-infrastructure / energy** — LightRot 27.4 TOPS/W data point for low-power inference at edge/distributed nodes.
10. **memory-architecture-taxonomy** — hardware tiering maps to the agent memory taxonomy (episodic/semantic/procedural) at silicon level.

## References

1. arXiv:2607.26633 — NELSSA: GPU-PNM heterogeneous LLM serving (Jul 2026)
2. TraCT — rack-scale CXL KV transfer (Dynamo framework) [2026; verified via arXiv index]
3. HyMCache — CXL-hybrid memory KV-cache framework [2026]
4. arXiv:2601.09985 — FaTRQ: CXL Type-2 far-memory RAG refinement (Jan 2026)
5. arXiv:2601.03229 — SpANNS: near-memory sparse vector search (Jan 2026)
6. arXiv:2505.16096 — Cosmos: CXL in-memory ANNS offload (2025)
7. arXiv:2411.02282 — CXL-DMSim full-system simulator with silicon validation (2024/2026 rev)
8. arXiv:2607.25283 — LightRot low-bit rotation inference (from field report)
9. Shared corpus: agent-exports v16/v17 cxl-memory-pooling-ai-infrastructure-draft, hardware-software-codesign-ai-agents §2.2, chiplet-architectures-ai-inference §5.1
10. Prior wiki: hardware-accelerated-agent-memory (STABLE, 141 lines)
11. arXiv:2512.04476 — Beluga: GPU/CPU shared memory pool via CXL switches + Beluga-KVCache on vLLM (Dec 2025)
12. ScalePool — unified XLink-CXL hybrid fabric with explicit memory tiering [2026; verified via arXiv index]
13. CXL AIC long-context fine-tuning with tensor-level NUMA control + CXL-aware allocator [2026; verified via arXiv index]
14. TrendForce 2026-07-21 — Samsung CMM-D 3.0 (CXL 3.2) mass production target; Q1 2026 hyperscaler allocation of CMM-D/CZ120/CMM-DDR5
15. CXL memory expansion market sizing — $1.3B (2025) → $11.8B (2034), 28.7% CAGR
16. Tom's Hardware / Meta Vistara CXL DDR4 memory expander (Jun 2026)
17. Samsung Semiconductor — RTX PRO 6000 Blackwell + CMM-D 1TB CXL pool, vLLM/LMCache evaluation
