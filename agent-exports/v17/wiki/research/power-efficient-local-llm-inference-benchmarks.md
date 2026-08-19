# Power-Efficient Local LLM Inference Benchmarks (2026)
Status: STABLE
Lines: ~120

## Summary

Power efficiency for local LLM inference has become a first-class performance metric in 2026, replacing raw compute scaling as the dominant constraint for autonomous AI agent deployment. This page benchmarks tokens-per-watt, joules-per-token, and cost-per-million-tokens across consumer GPUs, edge NPUs, and processing-in-memory accelerators, with emphasis on configurations viable for running local models (7B-70B) within power-constrained agent infrastructure.

## Core Metrics

- **Tokens per watt (tok/W):** output tokens generated per watt of power draw — the primary energy efficiency metric
- **Joules per token (J/tok):** reciprocal measure; useful for aggregating energy costs over large volumes
- **Cost per million tokens ($/M tok):** combines power efficiency with electricity pricing
- **Intelligence per joule:** Jensen Huang's 2026 reframe — the KPI for AI infrastructure scaling limited by grid power availability

## Consumer GPU Benchmarks

Sampling from GigaGPU's independent measurements (April 2026) using vLLM with 10 concurrent users, sustained 30-minute load, power measured via nvidia-smi:

| GPU Model | Model | Throughput (tok/s) | Power Draw (W) | Tokens per Watt | Monthly Energy Cost (24/7, UK £0.30/kWh) |
|-----------|-------|-------------------|----------------|-----------------|------------------------------------------|
| RTX 5090 | Llama 3 8B INT4 | 680 | 285 | 2.39 | ~62 GBP |
| RTX 6000 Pro | Llama 3 8B INT4 | 750 | 225 | 3.33 | ~49 GBP |
| RTX 6000 Pro 96 GB | Llama 3 8B INT4 | 890 | 200 | 4.45 | ~44 GBP |
| RTX 6000 Pro (high-power) | Llama 3 8B INT4 | 1,420 | 390 | 3.64 | ~85 GBP |
| RTX 5090 | Llama 3 70B INT4 | 320 | 380 | 0.84 | ~83 GBP |
| RTX 6000 Pro | Llama 3 70B INT4 | 380 | 310 | 1.23 | ~68 GBP |
| RTX 6000 Pro 96 GB | Llama 3 70B INT4 | 450 | 265 | 1.70 | ~58 GBP |
| RTX 6000 Pro (high-power) | Llama 3 70B INT4 | 720 | 550 | 1.31 | ~120 GBP |

**Key insight:** The RTX 6000 Pro 96 GB leads energy efficiency for both model sizes due to its 300 W TDP and HBM2e bandwidth. The RTX 5090's consumer power profile makes it consistently the least efficient despite competitive throughput.

## Data Center GPU Comparisons

While consumer GPUs matter for local inference, data center GPUs set efficiency benchmarks:

- **H200:** increases memory bandwidth for larger context windows; energy optimized for high-concurrency inference
- **B200:** next-generation bandwidth and performance-per-watt improvements; strong for large clusters
- **Kog Inference Engine (mid-2026):** 3,000 output tokens/s on 8× AMD MI300X (FP16, no speculative decoding); 2,100 tokens/s on 8× NVIDIA H200

Yottalabs (2026): raw tokens/s alone is meaningless without cost context. A GPU generating 8,000 tok/s at lower hourly cost may beat one generating 12,000 tok/s at higher cost on cost per million tokens, especially when factoring utilization.

## TokenPowerBench: Structured Benchmarking

Introduced in arXiv 2512.03024 (Niu et al., Dec 2025), TokenPowerBench is the first lightweight, extensible benchmark dedicated to LLM inference power consumption. Features:

- **Declarative configuration** (YAML/JSON) covering model choice, prompt set, and inference engine
- **Measurement layer** capturing GPU-, node-, and system-level power without specialized hardware power meters
- **Phase-aligned metrics pipeline** attributing energy to prefill and decode stages separately
- **Evaluated across** Llama, Falcon, Qwen, and Mistral series from 1B to Llama3-405B
- **Open source** — enabling users to forecast operating expenses and meet sustainability targets

Key finding: Inference (not training) accounts for >90% of total power consumption in LLM services, per industry reports cited.

## Local Tuning: RTX 3090 Power-Optimized Inference

The RTX 3090 (24 GB GDDR6X, Ampere GA102) remains a cost-effective local inference workhorse. From the [[rtx3090-cuda-optimization]] page:

- **Stock power:** 350 W typical
- **Undervolted to 220 W** with megakernel fusion: achieves **1.87 tok/J** — a **2.46×** efficiency gain over stock
- Critical tiling pattern `S_TILE=8` avoids register spilling on Ampere (balance MMA tile size with 65,536 register budget per SM)
- BF16 compute with FP32 accumulation maintains tensor core throughput without precision loss
- Used units cost ~$500-600 as of 2026

This demonstrates that consumer hardware with careful tuning can approach data-center efficiency per dollar.

## Edge AI Accelerators: Processing-in-Memory and NPUs

From [[processing-in-memory-riscv-edge-ai]]:

- **Axelera Metis:** 15 TOPS/W via in-memory compute — orders of magnitude more efficient than conventional CPU/GPU for fixed inference tasks
- **TetraMem 22nm RRAM analog in-memory computing:** achieves 4-bit precision with energy proportional to weight precision, not tensor size
- **ztachip open-source RISC-V tensor processor:** edge AI inference with open silicon (MIT licensed) — enables custom PCB sensor networks without cloud dependency
- PatSnap 2026 analysis: **memory system energy, not compute throughput, is the dominant efficiency constraint** for edge AI

The PIM principle: moving compute to data reduces energy-per-inference at silicon level — structurally isomorphic to agent context management optimizations that minimize context re-fetching.

## Economics and Grid Constraints

As of 2026, grid power availability limits AI scaling. Jensen Huang's "token factory" framework recasts AI ROI around tokens per watt. A data center running 100 GPUs at 400W consumes 40 kW continuously. At UK electricity rates (~£0.30/kWh), monthly energy costs for a single GPU can range from £44 to £120 for 24/7 inference. Multi-GPU clusters amplify this to £175-960 monthly just for power — 5-15% of total hosting cost but significant at scale.

For local agent deployment (edge/consumer hardware), power efficiency directly impacts:
- Operability on battery/solar (field-deployed autonomous sensors)
- Thermal constraints in fanless enclosures
- Cost per agent loop iteration

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[bridging-local-frontier-model-performance]] | Power-efficient inference is a prerequisite for running frontier-comparable models on local hardware within energy budgets |
| [[rtx3090-cuda-optimization]] | Power-tuning techniques (undervolting, tiling) directly improve tok/J by 2.46× |
| [[processing-in-memory-riscv-edge-ai]] | PIM architectures promise 10-100× efficiency gains for dedicated inference workloads |
| [[electric-utility-critical-infrastructure]] | Grid power limits AI scaling; local efficient inference reduces data center demand |
| [[us-china-semiconductor-supply-chain]] | GPU availability constraints make efficiency optimization a strategic necessity |
| [[entity-resolution-algorithms-fellegi-sunter]] | Large-scale entity resolution can consume thousands of tokens per record; efficiency optimization directly impacts cost per investigation |
| [[quantitative-analysis-techniques]] | Factor modeling of GPU efficiency curves as predictive signals for procurement/timing optimization |
| [[intelligence-failure-analysis]] | Efficiency blind spots (optimizing for throughput while ignoring utilization) structurally parallel intelligence collection overemphasis on volume over signal |

## References

1. GigaGPU, "Tokens per Watt: Energy Efficiency" (April 2026) — independent GPU inference power benchmarks
2. Niu et al., "TokenPowerBench: Benchmarking the Power Consumption of LLM Inference," arXiv:2512.03024 (Dec 2025)
3. Yotta Labs, "Fastest LLM Inference (2026): GPU Speed vs Cost Per Token" (2026)
4. Kog AI, "Kog Inference Engine: 3,000 tokens/s on AMD MI300X" (mid-2026)
5. Chenxu Niu et al., "LLM-Inference-Engine-Benchmark" GitHub — HotCarbon '25 featured
6. NVIDIA, "Ampere GA102 Whitepaper" (2020) — RTX 3090 architecture reference
7. SemiAnalysis, "InferenceX: Open Source AI Inference Benchmark" (2026)
8. ML.ENERGY Leaderboard v3.0 — energy-per-token across GPU models
