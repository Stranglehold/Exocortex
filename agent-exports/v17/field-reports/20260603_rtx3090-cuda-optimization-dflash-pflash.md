# Field Report: RTX 3090 CUDA Optimization for LLM Inference (2026)

**Date:** 2026-06-03  
**Topic:** Hardware & Physical Computing → Bridging Local-to-Frontier Model Performance  
**Cycle Type:** EXPLORE

---

## 1. What I Explored

Jake\'s interests.md lists "RTX 3090 optimization beyond standard CUDA (tensor core utilization, custom kernels)" under Hardware & Physical Computing. The research_topics.promptinclude.md also lists "Bridging local-to-frontier model performance: research and develop tools/frameworks to enable local models (e.g., Qwen3.6-27b) to match frontier model performance."

I explored the May 2026 wave of optimizations targeting the RTX 3090 specifically for Qwen3.6-27B inference — the current local model sweet spot. The central finding: two innovations from the Luce-Org team (DFlash + PFlash) fundamentally change what a single consumer GPU can deliver, and the AutoKernel framework (arXiv, March 2026) opens the door to autonomous kernel optimization by AI agents.

---

## 2. What I Found

### DFlash + DDTree: Block-Diffusion Speculative Decoding

**Source:** InsiderLLM (May 1, 2026), Luce-Org lucebox-hub GitHub, arXiv:2602.06036 (DFlash), arXiv:2604.12989 (DDTree)

**Headline numbers — Single RTX 3090, Qwen3.6-27B Q4_K_M, batch=1, greedy:**

| Benchmark | Autoregressive | DFlash + DDTree | Speedup |
|-----------|---------------|-----------------|---------|
| HumanEval | 34.90 tok/s | 78.16 tok/s | 2.24x |
| Math500 | 35.13 tok/s | 69.77 tok/s | 1.99x |
| GSM8K | 34.89 tok/s | 59.65 tok/s | 1.71x |
| **Mean** | **34.97 tok/s** | **69.19 tok/s** | **1.98x** |

For Qwen 3.5-27B (matched, fully-trained draft): 129.52 tok/s on HumanEval (3.43x). The 3.6 draft is still training — widening gaps expected.

**How it differs from standard speculative decoding:**
- Standard: Small draft model proposes one token at a time → verified by target
- DFlash: Block-diffusion draft receives  + last 5 captured target hidden states, denoises all 16 mask positions in a single forward pass. Every position conditions on the same captured context, not its own noisy predictions.
- DDTree: Best-first tree verification (up to 22 nodes spanning top-K branches) verified in a single target forward pass via causal mask derived from parent pointers.
- Acceptance lengths: 8.33 for Qwen 3.5 with matched draft (vs 4-5 typical for chain drafts)

**Hardware requirements:**
- NVIDIA sm_86+ (RTX 3090, A10, A40, RTX 4090, 5090)
- 24 GB VRAM (~16 GB GGUF target + 3.46 GB BF16 draft + KV cache + ring buffer)
- CUDA 12+, CMake 3.18+, Linux
- NOT portable to Apple Silicon, AMD ROCm, or multi-GPU

**Implementation cleverness:** Three custom CUDA kernels manage state (ggml_gated_delta_net_tree_persist, ggml_ssm_conv_tree, sliding 4096-slot target_feat ring). Before each verify, target recurrent state (SSM intermediate, conv window, KV cache) is snapshotted and restored. Without the ring buffer, holding captured features for 128K context would burn 6.6 GB by itself.

### PFlash: 10x Prefill Speedup (May 1, 2026)

**Source:** Luce-Org, announced May 1, 2026. Same monorepo.

| Context Length | Vanilla llama.cpp TTFT | PFlash TTFT | Speedup |
|---------------|------------------------|-------------|---------|
| 128K | ~248.4 s | 24.8 s | 10.0x |
| 64K | ~134.95 s | 13.5 s | 10.0x |

- PFlash compresses the prompt to spans that matter before processing
- Composes with DFlash in the same C++/CUDA process: PFlash trims prompt, DFlash + DDTree decodes answer
- NIAH single-needle retrieval preserved at all tested contexts
- Multi-needle and RULER audits pending

### Dual RTX 3090 Configurations (April-May 2026)

**Source:** derekarmstrong.dev, dzombak.com, tfriedel/qwen3.6-rtx3090-lab, Medium

- **Dual RTX 3090 + vLLM v0.19:** 116+ tok/s with speculative decoding + FlashInfer, 160K context window (derekarmstrong.dev, May 2026)
- **Dual RTX 3090 + vLLM Docker Compose:** dzombak.com recipe, April 27, 2026, with OpenCode integration
- **Quad RTX 3090:** tfriedel/qwen3.6-rtx3090-lab compares engine/quantization choices, published TPS + GPU saturation numbers
- **Single RTX 3090 overnight stack:** 85 TPS, 125K context, vision enabled (Medium/@fzbcwvv)

### AutoKernel: Autonomous GPU Kernel Optimization (March 2026)

**Source:** arXiv:2603.21331, March 2026

AutoKernel applies an autonomous agent loop to GPU kernel optimization. A single matrix multiplication kernel targeting tensor core hardware typically requires weeks of expert tuning across tiling strategies, memory layouts, and precision configurations. AutoKernel automates this with iterative agent exploration — directly relevant to bridging local-to-frontier performance through self-improving infrastructure.

---

## 3. What I Think Is Interesting

**The RTX 3090 is becoming a frontier-competitive inference platform via algorithm innovation rather than raw flops.** The 2x speedup from DFlash costs zero additional hardware — it\'s pure algorithmic leverage (block-diffusion + tree verification + custom CUDA state management). Combined with PFlash\'s 10x prefill boost, the user experience for long-context workloads transforms: 248 seconds of waiting becomes 25 seconds.

**The AutoKernel + DFlash pattern suggests a convergence:** AI agents autonomously optimizing the GPU kernels that then accelerate AI agent inference. This is a self-reinforcing loop — better kernels → faster inference → more capable agents → better kernel optimization. It mirrors the self-improving agent architecture Jake is building in the Exocortex.

**The bridging gap is real and narrowing fast.** Qwen3.6-27B on a single RTX 3090 now achieves 70-85 tok/s — competitive with cloud API latency for many use cases. The frontier models (Deepseek V4, Opus 4.6) still dominate on reasoning depth, but the hardware+cost advantage of local inference is tilting. A 0 used RTX 3090 delivering 85 tok/s at Q4_K_M quality is hard to beat on throughput-per-dollar.

**The DFlash state management pattern has architectural implications for AI agents.** The snapshot-before-verify / restore-after-acceptance pattern in DFlash\'s KV cache management is structurally identical to agent checkpointing before irreversible actions. Both require: immutable state capture, speculative execution, verification, and rollback on rejection. This is a hardware-software isomorphism worth formalizing in Exocortex\'s state management layer.

---

## 4. What I\'d Explore Next

1. **Benchmark AutoKernel on RTX 3090 specifically** — apply the autonomous agent loop to DFlash\'s three custom CUDA kernels (gated delta net tree persist, SSM conv tree, target feat ring). Could the agent discover further optimizations the Luce-Org team missed?
2. **Integrate DFlash/PFlash into the Exocortex inference pipeline** — test whether the speedup holds at Exocortex workloads (multi-turn agent interactions with long context). Measure real tokens/second with the full injection gate + supervisor loop active.
3. **Profile the Qwen3.6-27B draft training process** — understand what closes the gap between the 3.5 matched draft (3.43x) and the 3.6 training draft (1.98x). This is a direct measurement of how much draft quality matters for speculative decoding efficiency.
4. **Explore CUDA kernel fuzzing for correctness** — with custom kernels becoming the norm for local inference, the attack surface expands. Can adversarial inputs trigger incorrect kernel behavior that produces subtly wrong agent outputs?

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **AI Agent Architecture** | AutoKernel uses autonomous agent loops for hardware optimization — same meta-pattern as Exocortex self-improvement. DFlash\'s state snapshot/restore mirrors agent checkpointing patterns. |
| **OSINT & Investigation Methodology** | Local inference at 80+ tok/s enables fully air-gapped OSINT processing — no investigation data ever leaves the local machine. Privacy-preserving by architecture, not policy. |
| **Markets & Financial Analysis** | RTX 3090 at 0 vs cloud GPU at -3/hr: break-even at ~230 hours (under 10 days of continuous use). The economics of local inference tilt further with each optimization. |
| **Privacy & Cryptography** | DFlash\'s custom CUDA kernels are closed-source-adjacent (gated HuggingFace repos). Verifiable build reproducibility matters for security-sensitive deployments. |
| **Electric Utility & Critical Infrastructure** | Edge AI at substations could run 27B-class models locally for anomaly detection — DFlash-level optimization makes this feasible on a single GPU rather than requiring a server cluster. |
| **History of Intelligence Operations** | The "collection management" problem in SIGINT — prioritizing which signals to process — is isomorphic to PFlash\'s prompt compression: both must decide which information to process with limited computational budget. |

---

## Sources

- InsiderLLM, "Best Way to Get 2x Token Output on RTX 3090: Qwen 3.6 + DFlash" (May 1, 2026)
- Luce-Org/lucebox-hub GitHub repository (DFlash + PFlash)
- arXiv:2602.06036 (DFlash: Block-Diffusion Speculative Decoding)
- arXiv:2604.12989 (DDTree: Tree-Based Speculative Decoding)
- arXiv:2603.21331 (AutoKernel: Autonomous GPU Kernel Optimization)
- Derek Armstrong, "Running Qwen3.6 27B Locally on Dual RTX 3090s with vLLM v0.19" (May 2026)
- Chris Dzombak, "A vLLM Docker Compose recipe for running Qwen 3.6 27B on dual RTX 3090s" (April 27, 2026)
- tfriedel/qwen3.6-rtx3090-lab GitHub repository
- Medium/@fzbcwvv, "An Overnight Stack for Qwen3.6-27B: 85 TPS, 125K Context, Vision" (April 2026)
- hardware-corner.net, "RTX 3090 Local LLM Benchmarks, Context Scaling & Supported Models 2026"
