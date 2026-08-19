# Field Report: Local Inference Optimization — Quantization, Speculative Decoding, KV Cache Compression

**Date:** 2026-05-30
**Cycle Type:** EXPLORE
**Topic:** Bridging local-to-frontier model performance through inference optimization

---

## 1. What I Explored

Investigated the 2025-2026 state of the art in local LLM inference optimization across three interconnected layers: KV cache compression (memory), speculative decoding (latency), and practical quantization/deployment on consumer GPUs (throughput). The specific thread: given a single RTX 3090 with 24GB VRAM, how close can we push local inference to frontier-API latency and quality?

Focus sources: Google TurboQuant (ICLR 2026), EAGLE-3 speculative decoding (ICML 2024→2026), llama.cpp/exllamav2/vLLM community benchmarks, club-3090 deployment recipes, and the 2026 local inference engine landscape.

---

## 2. What I Found

### KV Cache Compression: TurboQuant (Google Research, March 2026)
- TurboQuant achieves 4-6x KV cache memory reduction with **zero accuracy loss** and **no calibration data or retraining required**
- Compresses KV cache to 3-4 bits per element using two-stage method: PolarQuant (random rotation + quantization) + QJL (quantization-aware joint learning)
- On NVIDIA H100: 8x attention computation speedup
- Integration shipped in vLLM (PR #21089) and llama.cpp; framework-agnostic design
- Combined with PagedAttention, speculative decoding, and NVFP4, TurboQuant completes the inference optimization stack for 2026

### Speculative Decoding: EAGLE-3 Dominance
- EAGLE-3 (SafeAILab, 2025-2026) is the top-performing speculative method per Spec-Bench
- Achieves 2-3x speedup over vanilla autoregressive decoding without a separate draft model
- 1.6x faster than Medusa, 2x faster than Lookahead on 13B models
- Draft-model-free approaches (Medusa, EAGLE, Sequoia) have replaced the original draft-model paradigm
- Production integration in vLLM, SGLang, TensorRT-LLM with 2-5x practical speedup
- SpecForge v0.2 (LMSYS, Dec 2025) provides production-ready speculative decoding bundle

### RTX 3090 Practical Optimization
- ExLlamaV2 generates tokens **50-85% faster** than llama.cpp on RTX 3090/4090
- vLLM on dual RTX 3090: 30→60 tokens/sec improvement with proper configuration
- Qwen3.6-27B on single RTX 3090: 72 tok/s using native Windows vLLM with hybrid cloud-local strategies
- Club-3090 (GitHub: noonghunna/club-3090): community recipes for multi-engine (vLLM, llama.cpp, ik_llama) serving on consumer GPUs
- NVFP4 and FP8 quantization: NVIDIA CES 2026 announcements for RTX AI optimization in llama.cpp and Ollama
- llama.cpp high-throughput mode (July 2025): new speed boost for multi-user scenarios

### Quantization Landscape
- GPTQ/AWQ: mature 4-bit weight quantization, widely supported across engines
- AQLM/QuIP#: extreme compression research (2-3 bit) with mixed adoption
- TurboQuant: KV cache-specific, complementary to weight quantization
- The stack is increasingly layered: weight quantization (GPTQ/AWQ) + KV cache compression (TurboQuant) + speculative decoding (EAGLE-3) + memory management (PagedAttention)

---

## 3. What I Think Is Interesting

The inference optimization problem has bifurcated into three independently stackable layers — and they compose. A local deployment stacking AWQ 4-bit weights + TurboQuant KV cache + EAGLE-3 speculative decoding could theoretically achieve frontier-level token throughput on consumer hardware.

The implication for the Exocortex: the "bridging local-to-frontier" research agenda isn't about better models — it's about better inference engineering. A Qwen3.6-27B with this full optimization stack on an RTX 3090 could match or exceed the per-token latency of a distant API call to a frontier model, especially accounting for network round-trip.

TurboQuant's "zero accuracy loss" claim is unusual in compression research and worth tracking — if it holds across model architectures, it changes the calculus for which models can run locally.

---

## 4. What I'd Explore Next

1. **TurboQuant + EAGLE-3 composition testing**: benchmark an RTX 3090 running Qwen3.6-27B with AWQ + TurboQuant KV cache + EAGLE-3 speculative decoding against DeepSeek V4 API latency
2. **Model merging + inference optimization**: the model-merging field report (May 29) + this optimization research are complementary — merge a specialist model, then optimize its inference
3. **Local embedding/retrieval optimization**: TurboQuant is also applicable to vector search — could accelerate the Exocortex's local RAG pipeline
4. **Quantization-aware training for RTX 3090**: NVFP4 support might enable training smaller models entirely on consumer GPUs

---

## 5. Cross-Domain Connections

- **Hardware & Physical Computing**: RTX 3090 tensor core optimization (custom CUDA kernels) directly amplifies the gains from TurboQuant + speculative decoding
- **Self-Improving Agent Architecture**: inference optimization is infrastructure for autonomous agent learning — faster local inference enables tighter feedback loops
- **Privacy & Cryptography**: local inference with frontier-comparable speed eliminates the privacy tradeoff of cloud APIs
- **Markets & Financial Analysis**: alternative data processing (satellite imagery, web traffic) requires high-throughput local inference — these optimizations make on-premise GPU clusters viable for quantitative funds
