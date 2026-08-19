# Field Report: Bridging Local-to-Frontier LLM Performance on RTX 3090 (2026)

**Date:** 2026-05-27
**Topic:** Hardware & Physical Computing / Bridging local-to-frontier model performance
**Research Agenda:** Research and develop tools/frameworks to enable local models (e.g., Qwen3.6-27B) to match frontier model performance within the Exocortex augmentation framework.

---

## 1. What I Explored

Three converging threads in making local LLM inference (single RTX 3090, 24 GB VRAM) competitive with frontier cloud models:

1. **Speculative decoding on consumer GPUs** — ngram speculation, MTP (multi-token prediction), and DFlash block diffusion all achieving 2×+ speedups on Qwen3.6-27B.
2. **Megakernel fusion** — single-CUDA-kernel Llama inference achieving 1.55× over llama.cpp (previously explored, relevant as baseline).
3. **KV cache compression** — TurboQuant TQ3_0 enabling 256K context on 24 GB, removing a key advantage of cloud models.

## 2. What I Found

### 2.1 Speculative Decoding Now Practical for Local LLMs

**ngram speculation** (llama.cpp PR #19164, Jan 2026): No second model needed. Predicts repeated token sequences. Works well on code/structured text (code agents generate lots of repetition). Power-limited GPUs see some of the best "free" wins because compute utilization drops and ngram speculation does not need it.

**MTP (Multi-Token Prediction)** — Qwen3.6 ships with native MTP heads. vLLM has Qwen MTP support paths; llama.cpp PR #22673 pending. Community reports:
- Qwen3.6-27B FP8 + MTP: 2× speedup on single L40S
- Qwen3.6-27B + MTP: 50+ tok/s on dual 3090
- Qwen3.6-27B + MTP: 80+ tok/s at long context on single 4090

**DFlash (Block Diffusion for Speculative Decoding)** — Z Lab (Feb 2026). Replaces auto-regressive draft model with block diffusion conditioned on target hidden states. On datacenter B200: 4.7× speedup (Math500), 5.2× (HumanEval). Lucebox ported to RTX 3090 (April 2026):

| Configuration | Speed (tok/s) | Context |
|---|---|---|
| Qwen3.5-27B Q4_K_M DFlash (peak) | 207.6 | — |
| Qwen3.5-27B Q4_K_M DFlash (HumanEval mean) | 129.5 | — |
| Qwen3.5-27B autoregressive | 38.0 | — |
| Qwen3.6-27B Q4_K_M DFlash | ~78 | — |
| Qwen3.5-27B Q4_0 DFlash | 134.78 | 128K |

Three custom CUDA kernels for tree-aware SSM state rollback: `ggml_ssm_conv_tree`, `ggml_gated_delta_net_tree`, `ggml_gated_delta_net_tree_persist`. DDTree verification with budget 22 tuned for RTX 3090 SM count. TurboQuant KV cache pushes context to 256K.

### 2.2 vLLM Native on RTX 3090 (Windows)

n1n.ai achieved 72 tok/s on Qwen3.6-27B via native Windows vLLM with PagedAttention, GPU memory utilization tuning, and INT4 quantization (May 2026). This is without speculative decoding — just optimized serving infrastructure.

### 2.3 Megakernel: Single-Kernel Inference

Lucebox fused all 24 layers into one CUDA kernel on Qwen 3.5-0.8B (April 2026), achieving 37,800 tok/s prefill, 413 tok/s decode, 1.55× over llama.cpp. Power sweet spot: 220W delivers 95% of full speed while drawing 30% less power. This approach is theoretically scalable to larger models but faces instruction cache pressure and register spilling on Ampere.

### 2.4 Overlapping Optimizations Create a New Baseline

No single optimization wins. The best results come from layering:
1. Quantization (Q4_K_M, INT4, FP8, TBQ4)
2. Speculative decoding (ngram, MTP, DFlash)
3. KV cache compression (TurboQuant)
4. Custom CUDA kernels (fused attention, tree-aware SSM rollback)

**Community forks that combine these:**
- Indras-Mirror/llama.cpp-mtp: Fused TBQ4 Flash Attention + MTP + Shared Tensors (RTX 4090-class)
- domvox/llama.cpp-turboquant-hip: TurboQuant for HIP/ROCm (Radeon 7900 XTX)
- Anbeeld/BeeLlama.cpp: DFlash + TurboQuant + TCQ + multimodal + reasoning-loop protection

## 3. What I Think Is Interesting

### The Gap Is Closing on Latency, Not Quality

Local inference (Qwen3.6-27B + DFlash + TurboQuant) can now deliver 70-130 tok/s on a single RTX 3090, with 128K+ context. That matches or exceeds the interactive latency of frontier cloud models (which serve at 30-60 tok/s per user due to batching). At this speed, a local coding agent can run loops that feel alive.

But **generation quality** remains the gap. Qwen3.6-27B scores competitively on benchmarks (it beats a 397B MoE on coding), but frontier models (Deepseek V4 Pro, Opus 4.6) have broader world knowledge, stronger reasoning, and better instruction following.

### The Exocortex Augmentation Hypothesis

Jake's research agenda asks: can we bridge the quality gap through augmentation? Three plausible paths:

1. **RAG + tool use** — Give the local model access to the same knowledge retrieval and tools that Exocortex provides. The model doesn't need to know everything if it can look things up.
2. **Self-improvement loops** — Meta-cognitive injection, error comprehension, and prompt evolution (Exocortex's existing components) can compound over repeated interactions, narrowing the gap incrementally.
3. **Speculative decoding as a multiplier** — If DFlash gives 2× speedup, you can run a 27B model at the latency of a 13B model, effectively getting higher quality per unit time. Or you can spend the speedup on longer thinking chains (chain-of-thought, self-critique) within the same latency budget.

### The Real Frontier Is Not Hardware, It's Integration

The RTX 3090 can now serve a 27B model at 130 tok/s with 256K context — better than many cloud endpoints a year ago. But the integration work — tuning speculative decoding for each model, maintaining CUDA kernel compatibility, handling Linux vs Windows vs AMD, managing KV cache formats — is substantial. The "bridge" to frontier performance is as much an engineering integration problem as a hardware problem.

## 4. What I'd Explore Next

- **Benchmark local (Qwen3.6-27B + DFlash + TurboQuant + Exocortex tools) vs. frontier (Deepseek V4 Pro) on a standardized agent benchmark (SWE-bench, WebArena, etc.).** Measure both latency and task completion.
- **Implement llama.cpp speculative decoding + Exocortex's `call_subordinate` for a local self-improving agent loop.** See if the speedup translates to more explorations per idle cycle.
- **Profile DFlash's tree-aware SSM rollback kernels on Ampere vs Ada vs Blackwell.** Where do the CUDA 12+ and sm_121 requirements create bottlenecks?
- **Test ngram speculation on Exocortex's own tool-call patterns** — if agent tool invocations follow repetitive JSON schemas, ngram speculation could give free wins.

## 5. Cross-Domain Connections

| Domain | Connection |
|---|---|
| **AI Agent Architecture** | Speculative decoding directly enables more agent loop iterations per second — the Exocortex's self-improvement cycles get faster. |
| **Markets & Financial Analysis** | GPU availability and pricing determine who can deploy these optimizations. RTX 3090s at ~$500 used make this accessible; latest-gen cards at $2000+ restrict it. |
| **Geopolitics & Strategic Analysis** | Export controls on NVIDIA cards to China are pushing Chinese developers to optimize for locally available hardware — Qwen3.6 + DFlash + domestic inference stacks. |
| **Privacy & Cryptography** | Local inference at frontier latency removes the surveillance risk of cloud API calls. TurboQuant's compression also reduces the memory footprint of private data in KV cache. |
| **Electric Utility & Critical Infrastructure** | 220W sweet spot for megakernel inference matters for edge deployments where power is constrained (sensor networks, remote monitoring). |

---

## Sources

| Source | Type | URL |
|---|---|---|
| Luce DFlash Port (NYU Shanghai RITS) | Article | https://rits.shanghai.nyu.edu/ai/luce-dflash-brings-2x-speculative-decoding-to-qwen3-6-27b-on-a-single-rtx-3090/ |
| Speculative Decoding Is Finally Useful for Local LLMs | Blog | https://blog.bymar.co/posts/speculative-decoding-local-llms-2026/ |
| Lucebox Hub (DFlash for consumer GPUs) | GitHub | https://github.com/Luce-Org/lucebox-hub |
| Z Lab DFlash Paper | arXiv | https://arxiv.org (DFlash: Block Diffusion for Flash Speculative Decoding) |
| llama.cpp PR #19164 (ngram-mod) | GitHub | https://github.com/ggerganov/llama.cpp/pull/19164 |
| llama.cpp PR #19493 (speculative checkpointing) | GitHub | https://github.com/ggerganov/llama.cpp/pull/19493 |
| llama.cpp PR #22673 (MTP Support, open) | GitHub | https://github.com/ggerganov/llama.cpp/pull/22673 |
| RTX 3090 vLLM Optimization (n1n.ai) | Article | https://explore.n1n.ai/blog/qwen3-6-27b-local-inference-rtx-3090-vllm-ollama-2026-05-03 |
| RTX 3090 Megakernel (Lucebox) | Previous field report | /a0/usr/workdir/workspace/field-reports/20260526_rtx3090-tensor-core-optimization.md |
| Qwen3.6-27B Speculative Decoding Benchmark | GitHub | https://github.com/thc1006/qwen3.6-speculative-decoding-rtx3090 |
