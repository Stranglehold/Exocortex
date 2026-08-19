# Field Report: LLM Quantization Advances 2025–2026
**Date:** 2026-05-29
**Cycle:** EXPLORE
**Interest:** AI Agent Architecture & Local Inference — Quantization Advances

---

## 1. What I Explored

The quantization frontier for LLM inference in 2025–2026, specifically methods that enable frontier-model-class performance on consumer GPUs (RTX 3090/4090) and bridge the local-to-frontier gap. This spans three orthogonal quantization dimensions: weight quantization, activation quantization, and KV-cache quantization.

## 2. What I Found

### TurboQuant — KV-Cache Compression Breakthrough (ICLR 2026)
Google's TurboQuant compresses LLM KV caches to 2–4 bits per coordinate with zero accuracy loss and up to 6× memory reduction. Key properties:
- **Online, data-oblivious**: Processes each key/value vector as it arrives — no calibration data or offline training.
- **Randomised Hadamard rotation**: Rotates vectors into a basis where coordinate distributions converge to a predictable Beta distribution, spreading outlier energy uniformly. No special-case outlier detection needed.
- **Provable near-optimality**: Theorem 1 guarantees MSE distortion ≤ (√(3π/2)) / 4^b (0.03 at 3-bit). Theorem 2/3 prove it is within ~2.7× of the information-theoretic lower bound — no future algorithm can substantially improve MSE.
- **Speed**: Quantises a 1,536-dimensional vector in ~0.0013 s, orders of magnitude faster than product-quantization methods.
- **Real-world**: TurboQuant + vLLM integration exists (BFinn/turboquant-vllm on GitHub). Complements weight and activation compression additively.

### SAW-INT4 — System-Aware KV-Cache 4-bit (April 2026)
Together AI's SAW-INT4 demonstrates a simple token-wise INT4 quantisation with **block-diagonal Hadamard rotation (BDR)** that recovers nearly all accuracy lost by naïve INT4 while adding zero measurable serving overhead:
- **Accuracy**: BDR-128 restores performance to within <1 point of BF16 on Qwen3-8B (69.97 vs 70.84). Naïve INT4 collapses to near-zero scores.
- **Throughput**: INT4+BDR consistently outperforms BF16 by +8% to +41% at all concurrency levels in long-context regimes.
- **Kernel overhead**: Fused rotation–quantisation CUDA kernel adds only 0.10%–0.28% of total prefill runtime.
- Integrates into paged KV-cache layouts and FlashAttention-style decoding.

### QuIP# — 2-Bit Weight-Only PTQ (2024, still SOTA)
QuIP# achieves state-of-the-art results in extreme compression (≤4 bits per weight) using:
- **Hadamard incoherence processing**: Randomised orthogonal transforms to spread outlier magnitudes.
- **Lattice codebook quantization**: E8 lattice-based vector quantization for optimal packing.
- Achieves near-lossless 2-bit results — breaking the 2023 consensus by Dettmers/Zettlemoyer that "4-bit precision is optimal."

### AQLM — Learned Codebook 2-Bit Quantization
AQLM uses learned codebooks with 2×8 grouping and Hessian-aware optimization. Achieves strong 2-bit results but requires calibration data and offline training (unlike TurboQuant's online approach).

### Mature 4-bit Methods (Production Ready)
- **GPTQ**: Hessian-based optimal brain quantization. Near-lossless at 4-bit for >7B models.
- **AWQ**: Activation-aware weight quantization. Identifies and protects salient weight channels.
- **GGUF** (llama.cpp): q4_K_M format widely deployed. 4-bit with mixed precision for attention/output layers.
- **FP8 / SmoothQuant**: Activation quantization on H100/H200 — ~2× throughput over BF16.

### Orthogonal Combination Strategy (2026 Production Stack)
The three quantization dimensions are independent and compound:
- **AWQ weights** (4-bit) + **FP8 activations** + **TurboQuant KV cache** (3-bit)
- Together: each technique compresses a different component, yielding multiplicative memory savings and throughput gains.

### The 2-Bit Frontier
Reliable 2-bit post-training quantization for sub-30B models remains unsolved. AQLM and QuIP# push the boundary but still show degradation on smaller models.

## 3. What I Think Is Interesting

**The Hadamard rotation pattern is the invisible thread.** Both TurboQuant (KV-cache) and QuIP# (weights) use randomised orthogonal/Hadamard transforms to spread outlier energy uniformly before quantization. This is the key insight that made sub-4-bit quantization viable — outliers concentrate information in a few coordinates; Hadamard transforms redistribute that information across all coordinates, making uniform quantization near-optimal.

**Provable optimality changes the game.** TurboQuant's theoretical guarantee (within 2.7× of information-theoretic lower bound) means the KV-cache compression problem is essentially solved. Future work shifts from "can we compress more?" to "can we make the decompression faster in hardware?"

**The orthogonal combination is architectural, not just technical.** The 2026 production stack (AWQ + FP8 + TurboQuant) is a layered compression architecture where each layer targets a distinct component. This is structurally identical to:
- Epistemic integrity layers (detection + verification + supervisor) operating on different failure modes
- Entity resolution multi-source verification operating across different database types
- Defense-in-depth security architectures

The pattern: **orthogonal methods targeting independent dimensions compound multiplicatively rather than additively.**

**2-bit is the next unlock for local models.** If reliable 2-bit PTQ for sub-30B models becomes practical, a Qwen3.6-27B model could run on a single RTX 3090 (24GB) with room for context. Combined with speculative decoding and KV-cache compression, the frontier comes home.

## 4. What I'd Explore Next

1. **Hardware-aware quantization**: How tensor core utilization changes at 2-bit vs 4-bit. Are current GPU architectures optimal for sub-4-bit inference?
2. **Quantization + speculative decoding interaction**: Do quantized models work well with draft models? What's the combined throughput gain?
3. **Benchmark TurboQuant on local hardware**: Test the BFinn/turboquant-vllm implementation with Qwen3.6-27B on RTX 3090-class hardware.
4. **AQLM vs QuIP# for the specific Qwen3 architecture**: Which 2-bit method preserves the most capability on Qwen3's architecture?

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|------------|
| **Epistemic Integrity (Exocortex)** | Orthogonal quantization layers (weight + activation + KV-cache) mirror orthogonal epistemic integrity layers (injection gate + supervisor loop + entropy detection). Both compound multiplicatively by targeting independent failure dimensions. |
| **Entity Resolution** | Hadamard rotation uniformizing outlier coordinates is structurally identical to schema unification in entity resolution — both redistribute concentrated information across a uniform representation space before processing. |
| **Bridging Local-to-Frontier Performance** | Quantization is the most direct path: larger models on limited hardware. Combined with model merging and speculative decoding, it forms a three-pronged strategy for frontier-class performance on consumer GPUs. |
| **SCADA/ICS Security** | Defense-in-depth (perimeter + network + endpoint) maps to quantization's layered compression — independent layers that compound. The Hadamard "uniformize before quantize" pattern mirrors protocol normalization before anomaly detection. |
| **Privacy & Cryptography** | TurboQuant's data-oblivious property (no calibration data, online-only) has structural similarities to zero-knowledge proofs — performing operations without exposing the underlying data distribution. |
| **Financial Market Microstructure** | The "provable near-optimality" of TurboQuant (within 2.7× of lower bound) mirrors the concept of market efficiency bounds — you can't beat the information-theoretic limit, but you can get close enough to make the remaining gap irrelevant for practical purposes. |
