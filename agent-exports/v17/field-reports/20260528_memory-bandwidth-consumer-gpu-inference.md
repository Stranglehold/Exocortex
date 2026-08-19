# Field Report: Memory Bandwidth Optimization for Consumer GPU LLM Inference
**Date:** 2026-05-28
**Topic:** Hardware & Physical Computing
**Sub-thread:** Memory bandwidth as the dominant bottleneck in local LLM inference on consumer GPUs

---

## 1. What I Explored

I followed the thread of memory bandwidth engineering for consumer GPU inference: why Google researchers (Ma & Patterson, IEEE Computer 2026) declare memory and interconnect — not compute — as the primary bottleneck, how GDDR generations translate to real-world tokens/second on cards from RTX 3090 to RTX 5090, and what mitigation strategies exist at the algorithm level (TurboQuant KV cache compression).

---

## 2. What I Found

### The bandwidth formula is simple but unforgiving

Every GPU's theoretical memory bandwidth is:

$$\text{Bandwidth (GB/s)} = \frac{\text{per-pin speed (Gbps)} \times \text{bus width (bits)}}{8}$$

Two variables control everything. Bus width determines parallelism (each GDDR chip contributes 32 data lanes); per-pin speed moves bits faster down each lane. Consumer GPUs in 2026:

| GPU | Memory | Per-pin speed | Bus width | Bandwidth (GB/s) | VRAM |
|---|---|---|---|---|---|
| RTX 3090 | GDDR6X | 19.5 Gbps | 384-bit | 936 | 24 GB |
| RTX 4090 | GDDR6X | 21 Gbps | 384-bit | 1,008 | 24 GB |
| RTX 5060 Ti 16GB | GDDR7 | 28 Gbps | 128-bit | 448 | 16 GB |
| RTX 5090 | GDDR7 | 28 Gbps | 512-bit | 1,792 | ~32 GB |
| RTX PRO 6000 Blackwell | GDDR7 | ~28 Gbps | 512-bit (clamshell) | ~1,792 | 96 GB |

Key insight: the RTX 5060 Ti has faster per-pin speed (28 Gbps GDDR7) than the 3090 (19.5 Gbps GDDR6X), but its 128-bit bus caps bandwidth at 448 GB/s — less than half the 3090's 936 GB/s. For 7B-13B models this is fine; for 34B+ it becomes the choke point.

### Google's memory bottleneck thesis

Ma & Patterson (IEEE Computer 2026) quantified the gap: **AI chip compute grew 80x over a decade while memory bandwidth grew only 17x** — a 4.7x differential. The autoregressive decode phase of LLMs is fundamentally memory-bound: each token generation requires streaming massive weight matrices from VRAM, leaving compute units idle. The economic consequence: cloud providers bought $200B+ in GPUs primarily for VRAM aggregation, not compute. HBM gets more expensive per GB over time while DDR gets cheaper.

Four architecture research opportunities identified:
1. **High Bandwidth Flash (HBF):** 10x memory capacity with HBM-like bandwidth for frozen weights. SK Hynix, Samsung, SanDisk developing for integration within 24 months.
2. **Processing-Near-Memory:** Keep compute and memory separate but reduce interconnect distance (favored over Processing-In-Memory due to thermal/software problems).
3. **3D memory-logic stacking:** Place memory layers on compute chips (d-Matrix developing).
4. **Low-latency interconnect:** Speed up chip-to-chip communication.

### TurboQuant: Algorithmic mitigation

Google's TurboQuant (ICLR 2026) attacks the KV cache — the memory component that grows linearly with context length. The pipeline: random orthogonal rotation (spreads vector energy uniformly, eliminating outlier channels) → Lloyd-Max optimal quantization → QJL error correction. Training-free, model-agnostic.

- **4-bit TurboQuant:** 3.8x compression vs FP16. Up to 8x speedup on H100 attention logit computation vs 32-bit keys (~4x vs FP16 baseline).
- **3.5-bit TurboQuant:** Identical LongBench score to full-precision (50.06 vs 50.06).
- **3-bit TurboQuant:** 4.9x compression, Mean Squared Error 0.034.

Market impact: SK Hynix fell 6.23%, Samsung 4.8% on announcement day (March 26, 2026). The market recognizes that better compression means less need for expensive HBM capacity per inference workload.

### Consumer GPU buying heuristic

For local inference:
- **7B-13B q4 models:** Bandwidth above ~400 GB/s is sufficient (5060 Ti 16GB fine for budget).
- **34B-70B q4 models:** Need >=24GB VRAM and >=700 GB/s bandwidth. Used 3090s remain competitive at 936 GB/s.
- **Future-proofing for MoE:** 1.5 TB/s+ class GPUs (5090 at 1.8 TB/s) age better.
- Always compute `per-pin speed x bus width / 8` — it predicts real-world token throughput more accurately than marketing TFLOPS or AI TOPS.

---

## 3. What I Think Is Interesting

**The "randomization paradox" appears in hardware too.** Just as anti-bot fingerprinting evolved from randomization to identity design (see 20260528 anti-bot evasion report), memory optimization shows a parallel pattern: brute-force scaling (faster GDDR, wider buses) gives way to design-level solutions (HBF, 3D stacking, compression). The pattern is the same across domains — when the brute-force approach hits a wall, the field pivots to architectural restructuring.

**TurboQuant's market impact is a leading indicator.** When a compression paper drops memory chip stocks 6%, the inference hardware market is signaling that software-level efficiency gains threaten the "buy more HBM" capex model. If 3-bit KV caches become standard, the marginal utility of each additional GB of HBM drops — shifting economics toward mid-range GPUs with good enough bandwidth.

**The clamshell design tradeoff (RTX PRO 6000 Blackwell: 96 GB VRAM, same bandwidth as 5090) exposes a capacity-vs-throughput decision that will define the next generation of inference hardware.**

---

## 4. What I'd Explore Next

- **vLLM PagedAttention integration with TurboQuant:** How do chunked-prefill and block-level memory management interact with KV cache compression? Can they be combined for multiplicative gains?
- **Multi-GPU tensor parallelism bandwidth scaling:** When does interconnect bandwidth (NVLink, PCIe) become the bottleneck for split-model inference vs. single-GPU memory bandwidth?
- **Processing-Near-Memory in practice:** What are the real thermal and software challenges that make Google paper prefer it over Processing-In-Memory? Worth investigating the d-Matrix architecture.
- **3 GB GDDR7 chip density implications:** At 3 GB/chip, 12 chips = 36 GB, 16 chips = 48 GB. A 48 GB consumer GPU with 1.8 TB/s bandwidth would make single-GPU 70B q4 inference mainstream. What's the roadmap from Samsung/Micron?

---

## 5. Cross-Domain Connections

- **Entity Resolution (Data Aggregation):** The GDDR bandwidth formula's two-variable decomposition (per-pin speed x bus width) mirrors deterministic entity matching — two independent discriminators (registry ID vs. fuzzy string match) that multiply to a resolution decision. Breaking a problem into orthogonal variables is a recurring pattern across Exocortex domains.
- **RISC-V Open-Source Silicon (Hardware):** The previous exploration (20260528_riscv-open-source-silicon-ai-inference.md) examined open-source ASIC design; memory bandwidth engineering is the complement — the performance ceiling even open-source silicon would face.
- **Bridging Local-to-Frontier Performance:** The memory bandwidth bottleneck is the primary hardware constraint on bridging local models (RTX 3090 inference) to frontier performance. Without memory bandwidth parity, algorithmic improvements (speculative decoding, quantization) can only partially close the gap.
- **CI Analysis (Intelligence Operations):** The "memory bottleneck" framing is structurally identical to CI analysis frameworks — identifying the true constraint (not the most visible one) and redirecting resources accordingly. Google's paper does for hardware what an ACH matrix does for hypothesis evaluation: it forces you to quantify the mismatch between where you're spending and where the bottleneck actually sits.
