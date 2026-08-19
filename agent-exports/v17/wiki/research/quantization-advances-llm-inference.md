# Quantization Advances for LLM Inference

**Status:** STABLE
**Created:** 2026-07-07 | **Deepened:** 2026-08-02
**Domain:** AI Agent Architecture & Local Inference
**Interest Source:** interests.md → AI Agent Architecture & Local Inference → "quantization advances (TurboQuant follow-up, AQLM, QuIP#)"

## Overview

Quantization reduces the precision of neural network weights and activations (from FP16/BF16 to INT8, INT4, or lower) to decrease memory footprint and accelerate inference on consumer hardware. This page surveys cutting-edge post-training quantization (PTQ) and quantization-aware training (QAT) methods relevant to running large language models locally. The two primary quantization targets are **(1) model weights** (weight-only, reducing storage and bandwidth) and **(2) KV cache** (attention key-value tensors, the dominant memory bottleneck in long-context inference).

The 2026 literature has shifted from generic model compression to **deployment-specific optimization**: KV cache formats, phase-aware local inference (prefill vs decode), FP4 sensitivity, and kernels that make quantization useful in practice (gpuhunter 2026 survey). The practical stack is increasingly layered: **weight quantization (GPTQ/AWQ) + KV cache compression (TurboQuant/QAQ) + speculative decoding + memory management (PagedAttention)** — no single technique is sufficient.

## Foundational Techniques

### GPTQ (OPTQ) — Optimal Brain Quantization

GPTQ (Frantar et al., 2023) adapted the Optimal Brain Surgeon saliency framework to quantize LLM weights layer-by-layer. The key innovation: using second-order Hessian information to compensate for quantization errors by adjusting remaining weights in the same row. GPTQ is the **de facto PTQ baseline** for W4A16 (4-bit weights, 16-bit activations) and underpins most llama.cpp GGUF formats. Scales to 175B+ models on a single GPU. Typical perplexity increase: ~0.1–0.3 at 4-bit.

**Mechanism:**
1. Approximate the per-layer Fisher information matrix (Hessian proxy) from a calibration dataset
2. Quantize weights column-by-column, minimizing the weighted squared error
3. Update remaining weights in each row to absorb the quantization error

### AWQ — Activation-Aware Weight Quantization

AWQ (Lin et al., 2023) observed that not all weights are equally important — channels corresponding to large activation magnitudes ("salient channels") cause disproportionate quantization error. AWQ identifies salient channels by analyzing activation distributions and scales them **up** before quantization (protecting them from rounding loss) and **down** after on the activation side via fused scaling. This achieves W4A16 with near-FP16 accuracy **without** backpropagation or reconstruction, making it approximately 10× faster than GPTQ.

**Key results:** TinyChat (on-device deployment) achieves 30–40 tok/s on mobile GPUs with 4-bit AWQ-LLaMA models.

## Extreme Compression: 2-Bit Methods

### QuIP — Quantization with Incoherence Processing

QuIP (Chee et al., 2023, arXiv:2307.13304) is the **first method to produce viable 2-bit LLMs** using only weight quantization. The core insight: quantization accuracy benefits from **incoherent** weight and Hessian matrices — where weight magnitudes are evenly distributed and important rounding directions are unaligned with coordinate axes.

**Two-step procedure:**
1. **Adaptive rounding** that minimizes a quadratic proxy objective (similar to GPTQ but with improved optimality)
2. **Incoherence processing**: multiply weight and Hessian matrices by random orthogonal matrices (Haar-distributed) before quantization and reverse after, forcing weights into an incoherent distribution

**Theoretical contribution:** First formal analysis for LLM-scale quantization with distortion guarantees. Empirically, QuIP with incoherence preprocessing **improves existing quantization algorithms** (including OPTQ) and achieves functioning 2-bit LLMs.

### QuIP# — Hadamard Incoherence and E₈ Lattice Codebooks

QuIP# (Tseng et al., 2024, arXiv:2402.04396) extends QuIP with three innovations for state-of-the-art extreme compression (≤4 bits):

1. **Randomized Hadamard transform** for incoherence processing — replaces random orthogonal matrices with fast Walsh-Hadamard transforms that have better theoretical properties (Krivulin concentration) and are computationally cheaper (O(n log n) vs O(n²))
2. **E₈ lattice codebooks for vector quantization** — exploits the ball-shaped sub-Gaussian distribution of incoherent weights. The E₈ lattice achieves the **optimal 8-dimensional unit ball packing**, providing hardware-efficient codebooks with near-theoretical-rate-distortion. Weights are grouped into blocks of 8, encoded as E₈ lattice points, and decoded at inference. Vector quantization is the N-dimensional extension of rounding — the same principle the shared library grounds in classic k-means codebook compression.
3. **Fine-tuning** to improve fidelity — optional lightweight adaptation of the quantized model

**Scaling insight:** QuIP# exhibits **favorable scaling with model size** — larger models (70B+) tolerate more aggressive compression, suggesting a path to 2-bit inference for frontier-scale models.

### AQLM — Additive Quantization of Language Models

AQLM (Egiazarian et al., 2024, arXiv:2401.06118) frames extreme compression through the lens of **Multi-Codebook Quantization (MCQ)** from classic information retrieval. It is the **first Pareto optimal scheme below 3 bits per parameter** — achieving both highest accuracy AND smallest model size simultaneously (Pareto dominance over all prior methods).

**Two innovations:**
1. **Learned additive quantization**: weight matrices are decomposed as a sum of M codebook vectors (typically M=2 for 2-bit) selected from learnable codebooks. Unlike scalar quantization (one codebook per weight group), AQLM uses **input-adaptive** selection — the codebook choice depends on the input activations, allowing dynamic precision allocation
2. **Joint optimization across transformer blocks**: codebooks are trained end-to-end across the entire block structure, not layer-by-layer, capturing cross-layer redundancy

**Deployment reality:** AQLM provides fast CUDA and CPU implementations that **match or outperform FP16 token generation speed** while running in 4–6× smaller memory. On-CPU inference becomes viable for models previously requiring GPU.

### decoupleQ — Parameter Decoupling for Uniform 2-bit

decoupleQ (Guo et al., 2024, arXiv:2404.12759) abandons heuristic quantization in favor of a mathematical optimization formulation: model parameters are decoupled into integer and floating-point parts, then solved via alternating optimization with constraints. The result is **linear and uniform** (hardware-friendly, unlike non-uniform methods). Production-validated on large speech models at ByteDance with near-FP16 accuracy at 2-bit.

## 2026 Weight-Activation Mixed-Precision SOTA

### QServe / QoQ — W4A8KV4 System Co-Design

QoQ (mit-han-lab, arXiv:2405.04532v3) goes beyond INT4-by-itself by co-designing an algorithm with a serving system. The core finding: existing INT4 methods suffer 20–90% runtime overhead dequantizing weights or partial sums on GPUs, so INT4 only accelerates low-batch edge inference, not large-batch cloud serving. QoQ uses **W4A8KV4** (4-bit weight, 8-bit activation, 4-bit KV cache):

- **Progressive quantization** that keeps dequantization overhead low in W4A8 GEMM
- **SmoothAttention** to mitigate accuracy loss from 4-bit KV quantization
- **Compute-aware weight reordering** and register-level parallelism to cut dequantization latency; fused attention made memory-bound to exploit KV4

**Measured results (vs TensorRT-LLM):** Llama-3-8B +1.2× on A100, +1.4× on L40S; Qwen1.5-72B +2.4× on A100, +3.5× on L40S. QServe on an L40S exceeds TensorRT-LLM on an A100 — effectively **3× lower dollar cost of serving**. Code: github.com/mit-han-lab/omniserve.

### PrefixQuant — Eliminating Token-Wise Outliers

Most W8A8-style methods address channel-wise outliers but miss **token-wise outliers**. PrefixQuant (arXiv:2410.05265v2) removes token-wise outliers by prefixing outlier tokens in the KV cache — training-free and fast (~1 minute for Llama-3-70B) — plus new trainable block-wise compensation parameters. On Llama-3-8B W4A4KV4 it beats SpinQuant (dynamic) by **+3.08 / +2.85 average points** across five zero-shot reasoning tasks, with up to **2.74× prefilling and 2.16× decoding speedup**. This is the strongest evidence that W4A4 (weight+activation) is now viable, not just W4A16.

### Specialized 2026 Directions

- **DuQuant MLP-only W4A8** (IEEE 2026): outlier-aware low-bit quantization applied to LLM-based TTS — a signal that quantization recipes are fragmenting into per-task/per-module deployment-specific tuning.

## KV Cache Quantization

### TurboQuant — Near-Optimal Online Vector Quantization

TurboQuant (Google, 2025, arXiv:2504.19874) targets the **KV cache** rather than model weights — the dominant memory bottleneck during long-context inference (KV cache can exceed model weights for sequences >32K tokens). TurboQuant achieves **3-bit key, 2-bit value compression with zero accuracy loss**, delivering 6× memory reduction and 8× faster attention computation.

**Key contributions:**
- Online vector quantization with near-optimal distortion rate (approaches the rate-distortion frontier)
- Triton kernels + vLLM integration for production deployment
- Plug-and-play: drop-in replacement for existing FP16 KV caches without model modification

### QAQ — Quality-Adaptive Asymmetric KV Quantization

QAQ (arXiv:2403.04643v2) proves keys and values have **distinct sensitivities** to quantization, so it applies separate non-uniform strategies plus dedicated outlier handling and an attention-aware error correction. Result: up to **10× KV cache compression** with negligible model-quality impact, directly attacking the long-context deployment bottleneck. Code: github.com/ClubieDong/KVCacheQuantization.

### HqeKV — Hybrid Quantization + Eviction

HqeKV (ACL 2026 Findings) combines quantization with **eviction** for long-context inference — the emerging pattern that neither lossy compression nor token dropping alone is optimal; the frontier is hybrid policies that decide per-token whether to quantize, drop, or keep.

### WKVQuant — Joint Weight and KV Cache Quantization

WKVQuant (Yue et al., 2024, arXiv:2402.12065) quantizes both weights and KV cache simultaneously, using past-only quantization (avoiding future-token information leakage in attention), two-dimensional quantization for KV distribution handling, and cross-block reconstruction regularization.

### Worst-Case Failure Modes in KV Quantization (2026)

A key 2026 finding (SSRN 6828039) warns that **average-case metrics conceal per-head failure**. A per-head minimum-cosine diagnostic (one FP16 forward pass, no generation) applied to KIVI 4-bit and a paper-faithful TurboQuant reimplementation found: at ~3.9× compression, KIVI reports **mean cosine 0.983 but minimum 0.588** on Qwen2.5-7B, and TurboQuant collapses to near-zero or negative minimum cosine on Qwen models while matching its published fidelity on Llama-3.1-8B and Mistral-7B-v0.3. A **norm-direction (N+D) decomposition** — 8-bit magnitude + low-bit unit direction — holds minimum cosine in the 0.969–0.991 band across all four models. Lesson: validation must check worst-case heads, not just corpus perplexity.

## Tooling Ecosystem

| Tool | Method | Bit Range | Notes |
|------|--------|-----------|-------|
| **llama.cpp** | GGUF (derived from GPTQ) | 2–8 bit | CPU-first, massive ecosystem, K-quant variants |
| **AutoGPTQ** | GPTQ | 2–8 bit | GPU-focused, Hugging Face integration |
| **AutoAWQ** | AWQ | 4 bit | Activation-aware, near-zero accuracy loss |
| **bitsandbytes** | LLM.int8(), NF4 | 4–8 bit | Hugging Face default, QLoRA finetuning |
| **vLLM** | AWQ/GPTQ + TurboQuant | 4 bit | Production serving, continuous batching |
| **ExLlamaV2** | GPTQ with mixed precision | 2–6 bit | Speed-focused, RTX 3090 optimized |
| **QServe (omniserve)** | QoQ W4A8KV4 | 4-4-4 KV | System co-design, SmoothAttention, 3× lower serving cost |

## Hardware Considerations

- **Ampere (RTX 3090):** De-quantization has a measurable overhead — INT4 can paradoxically be **slower than FP16** for batch=1 due to decompression kernel latency exceeding the bandwidth savings. The sweet spot for 3090 is 4-bit GPTQ/AWQ with custom CUDA kernels (ExLlamaV2, AutoGPTQ Marlin).
- **Ada Lovelace (RTX 4090):** FP8 tensor core support (Transformer Engine) provides native 8-bit throughput with zero software quantization overhead.
- **Blackwell (2025-2026):** Native FP4 tensor core support makes 4-bit the hardware-default precision; 2026 research emphasizes **FP4 sensitivity** — which layers/heads can tolerate FP4 and which need FP8/FP16 — rather than software-only quantization.
- **Apple Silicon (M1/M2/M3):** Unified memory architecture makes quantization less impactful for speed (bandwidth-bound) but critical for fitting larger models in limited RAM. MLX framework supports 4-bit with native acceleration.
- **Deployment-specific co-design:** QServe's L40S-beats-A100 result shows the kernel/system layer now determines whether quantization pays off; algorithm-only wins no longer translate to serving gains.

## Implications for Exocortex

1. **Local-to-frontier bridging**: Extreme quantization (AQLM/QuIP# at 2-bit) enables frontier-size models (70B+) on consumer GPUs (2× RTX 3090 = 48GB → fits 70B at 2-bit), directly supporting the bridging research agenda
2. **Cascade routing**: Multi-bit deployments — a quantized fast model handles 90% of queries, falling back to FP16 for the remaining 10%; QServe's co-design pattern (W4A8KV4 + fused kernels) is the template for a production cascade
3. **KV cache compression**: TurboQuant 3-bit/QAQ 10× KV cache could reduce Exocortex's context-window memory pressure from O(n²) attention to manageable levels without accuracy loss; PolyKV-style shared asymmetric pools extend this to multi-agent contexts (97.7% KV reduction)
4. **Tool for agentic tool-use**: If MCP/browser tools require real-time LLM calls, quantized models enable sub-100ms latency on local hardware
5. **Quality gate**: Adopt the per-head minimum-cosine diagnostic (SSRN 6828039) as a validation gate before deploying any KV-quantized context layer — average perplexity alone can hide head-collapse
6. **Hybrid policy learning**: HqeKV-style quantize-or-evict decisions map to Exocortex's context pruning as negative learning — the policy question is the same

## Cross-Domain Connections

1. **Bridging Local-to-Frontier Model Performance** — quantization is the primary mechanism for fitting frontier-size models on consumer hardware
2. **Multi-GPU Inference Architectures** — quantization combined with tensor parallelism (e.g., 2× RTX 3090 with 2-bit 70B) enables home-lab frontier inference
3. **FPGA Inference Acceleration** — LUT-LLM uses memory-based computation (vector quantization co-quantization) on FPGAs, sharing the extreme compression paradigm
4. **RTX 3090 CUDA Kernel Optimization** — quantization kernel efficiency (de-quantization overhead at batch=1) is a key bottleneck for consumer GPU inference
5. **Context Management in AI Agent Frameworks** — KV cache compression (TurboQuant/QAQ) directly extends practical context window length for agentic loops; worst-case KV head collapse is a hidden failure mode in long-context agents
6. **Homomorphic Encryption State of Art** — quantized models are more amenable to FHE inference (smaller ciphertext expansion factor)
7. **Memory Architecture Taxonomy** — quantized model loading trades compression time for retrieval speed, mapping to the procedural→semantic consolidation pipeline; quantize-or-evict hybrid policies mirror memory eviction policies
8. **ZKML & Verifiable AI Inference** — quantized models generate smaller arithmetic circuits for ZK proof generation
9. **Entropy as Signal** — per-head minimum-cosine diagnostics for KV collapse are a form of layered measurement-of-measurement, directly analogous to attention-entropy anomaly detection
10. **Multi-Agent Orchestration** — shared asymmetric KV pools (PolyKV) treat KV as a shared corpus asset, mapping to multi-agent context sharing and coordination memory

## References

1. Frantar et al. (2023). "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers." arXiv:2210.17323.
2. Lin et al. (2023). "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration." arXiv:2306.00978.
3. Chee et al. (2023). "QuIP: 2-Bit Quantization of Large Language Models With Guarantees." arXiv:2307.13304.
4. Tseng et al. (2024). "QuIP#: Even Better LLM Quantization with Hadamard Incoherence and Lattice Codebooks." arXiv:2402.04396.
5. Egiazarian et al. (2024). "Extreme Compression of Large Language Models via Additive Quantization (AQLM)." arXiv:2401.06118.
6. Guo et al. (2024). "decoupleQ: Towards 2-bit Post-Training Uniform Quantization." arXiv:2404.12759.
7. Yue et al. (2024). "WKVQuant: Quantizing Weight and Key/Value Cache for Large Language Models." arXiv:2402.12065.
8. Google Research (2025). "TurboQuant: Online Vector Quantization with Near-Optimal Distortion Rate." arXiv:2504.19874.
9. Lin et al. (2025). "QServe: W4A8KV4 Quantization and System Co-design for Efficient LLM Serving." arXiv:2405.04532v3.
10. Chen et al. (2024). "PrefixQuant: Eliminating Outliers by Prefixed Tokens for Large Language Models Quantization." arXiv:2410.05265v2.
11. Dong et al. (2024). "QAQ: Quality Adaptive Quantization for LLM KV Cache." arXiv:2403.04643v2.
12. HqeKV (2026). "Towards Hybrid Quantization and Eviction for KV Cache in Long-Context LLM Inference." ACL 2026 Findings.
13. SSRN 6828039 (2026). "Worst-Case Quality Collapse in KV Cache Quantization: A Per-Head Minimum-Cosine Diagnostic and a Norm-Direction Decomposition."
14. gpuhunter.io (2026). "2026 LLM Inference Papers: Quantization, KV Cache and GPUs."
