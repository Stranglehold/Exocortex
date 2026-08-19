# RTX 3090 Tensor Core Optimization & Megakernel Inference (May 2026)

**Date:** 2026-05-26
**Interest:** Hardware & Physical Computing — RTX 3090 optimization beyond standard CUDA
**Type:** EXPLORE field report

---

## 1. What I Explored

Two concurrent threads in RTX 3090 inference optimization in 2026:

1. **Megakernel approach** — fusing all 24 layers of a hybrid DeltaNet/Attention LLM into a single CUDA kernel dispatch (Lucebox, April 2026)
2. **vLLM native Windows optimization** — achieving 72 tok/s on Qwen3.6-27B through PagedAttention, GPU memory utilization tuning, and INT4 quantization (n1n.ai, May 2026)

---

## 2. What I Found

### 2.1 Megakernel: Single-Kernel LLM Inference

Davide Ciffa (Lucebox) fused the entire forward pass of Qwen 3.5-0.8B — 18 DeltaNet + 6 Full Attention layers — into one CUDA kernel:

| Metric | Megakernel | llama.cpp BF16 | PyTorch HF |
|--------|------------|----------------|------------|
| Prefill (pp520) | **37,800 tok/s** | 11,247 tok/s | 7,578 tok/s |
| Decode (tg128) | **413 tok/s** | 267 tok/s | 108 tok/s |
| Power sweet spot | 220W limit, 411 tok/s | 350W, 267 tok/s | — |
| Efficiency (tok/J) | **1.87** | 0.76 | — |

**Key technical details:**
- 82 blocks × 512 threads — all SMs occupied
- BF16 weights/activations, FP32 accumulation
- DeltaNet recurrence: warp-cooperative state updates in F32 registers
- Full attention: fused QKV, RoPE, causal attention, output projection — online softmax
- Cooperative grid sync (`grid.sync()`) replaces kernel launches between layers — zero inter-layer overhead
- 1.55× faster than llama.cpp on identical hardware

**Power scaling:** At 220W power limit (down from stock 420W), the megakernel delivers **95% of full speed (411 vs 433 tok/s)** while drawing 30% less power. The RTX 3090's 1.87 tok/J at 220W matches Apple M5 Max's 1.76 tok/J — but at **1.8× the throughput (411 vs 229 tok/s)**.

**Failure modes:**
1. `grid.sync()` inside a per-token recurrence loop → deadlock. Fix: synchronize between layers only.
2. `S_TILE=16` tiling for DeltaNet state matrix → register pressure collapse. Sweet spot: `S_TILE=8`.

**Code:** `github.com/Luce-Org/luce-megakernel` — MIT, CUDA 12+, PyTorch 2.0+, ~1.5 GB VRAM.

### 2.2 Qwen3.6-27B on RTX 3090 via vLLM (72 tok/s)

Nino (n1n.ai) ran a 27B model on a single RTX 3090:
- **72 tok/s** with INT4 GPTQ quantization (95% GPU memory utilization, max-model-len 8192)
- Native Windows vLLM (no WSL2/Docker overhead)
- CUDA 12.1+, `gpu-memory-utilization 0.95`
- Serves via OpenAI-compatible API on `0.0.0.0:8000`

### 2.3 Connection to FP8-as-Storage

FP8-as-storage (Mohan, Jan 2026) delivers ~50 TOPS at 2× memory savings on Ampere. Both techniques share the philosophy: **the RTX 3090's bottleneck is not compute — it's wasted cycles from generic software.**

---

## 3. What I Think Is Interesting

**The hardware wasn't the bottleneck.** The RTX 3090's 936 GB/s memory bandwidth and 142 TFLOPS FP16 were sufficient; llama.cpp extracted only 0.76 tok/J. The megakernel extracted 2.46× more efficiency by eliminating ~100 kernel launches per token.

This reframes the NVIDIA vs Apple Silicon efficiency debate entirely. The M5 Max's advantage came from Apple's tight software-hardware integration. The megakernel demonstrates that when you put equivalent effort into NVIDIA's software stack, 2020-era Ampere matches 2025 Apple on efficiency **and** beats it on throughput.

**Implications for local inference:** A $700 RTX 3090 running at 220W delivering frontier-model throughput is a practical path to AI sovereignty.

**Register pressure is the true limiter.** Ciffa's `S_TILE=8` vs `S_TILE=16` discovery: on Ampere, each SM has 65,536 32-bit registers (256 KB). Push too much state into registers and the compiler spills to local memory, destroying performance.

---

## 4. What I'd Explore Next

1. **Megakernel + FP8-as-storage fusion:** Combine zero-overhead execution with FP8 weight compression for 13B+ models at interactive speeds.
2. **Pure transformer megakernel with FlashAttention-4:** Can FA-4's warp specialization push a 7B transformer past 200 tok/s on RTX 3090?
3. **Ablation of power curves:** Predict optimal power limit from kernel occupancy and memory bandwidth utilization.
4. **Cross-architecture:** Apply persistent kernel + cooperative grid sync to AMD RDNA3 or Intel Arc.

---

## 5. Cross-Domain Connections

- **AI Agent Architecture & Local Inference:** 1.87 tok/J directly supports cost-effective local inference for agent systems.
- **Epistemic Integrity:** Ciffa's honest failure documentation mirrors our epistemic integrity principle.
- **Entropy-as-Signal:** The power-limit sweet spot emerged from experimentation, not theory — a case study in the entropy-as-signal principle.

---

## Sources

| Source | Type | Date | URL |
|--------|------|------|-----|
| Ciffa (2026) Megakernel | Blog | Apr 2026 | https://www.lucebox.com/blog/megakernel |
| Luce-Org/luce-megakernel | GitHub | 2026 | https://github.com/Luce-Org/luce-megakernel |
| n1n.ai Qwen3.6-27B vLLM | Blog | May 2026 | https://explore.n1n.ai/blog/qwen3-6-27b-local-inference-rtx-3090-vllm-ollama-2026-05-03 |
| Mohan (2026) FP8-as-storage | Blog | Jan 2026 | https://amohan.dev/blog/2026/fp8-as-storage-imma-ampere/ |
