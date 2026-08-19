# Local LLM Quantization & Deployment Patterns

**Status:** DRAFT
**Created:** 2026-07-06
**Interests:** AI Agent Architecture & Local Inference, Hardware & Physical Computing

## Executive Summary

Local LLM deployment has matured significantly in 2025-2026, with quantization techniques enabling 70B+ parameter models to run on consumer GPUs (RTX 3090, 24GB) and edge devices. This page covers the current state of quantization methods, deployment frameworks, and practical considerations for running LLMs locally.

## Quantization Methods (2025-2026)

### Post-Training Quantization (PTQ)

| Method | Bits | Key Innovation | Status |
|--------|------|----------------|--------|
| **GPTQ** | 4 | First practical 4-bit quantization for LLMs | Mature, widely used |
| **AWQ** | 4 | Activation-aware weight quantization | Production-ready |
| **GGUF** | 2-8 | llama.cpp format, flexible bit widths | Industry standard |
| **QuIP#** | 2-4 | Hadamard incoherence + E8 lattice codebook | Research SOTA |
| **AQLM** | 2 | Asymmetric quantization via learned mixing | Research |

### Quantization-Aware Training (QAT)

- **BRECQ**: Better represents the quantization error during training
- **SmoothQuant**: Smooths activation outliers to enable INT8 quantization
- **OmniQuant**: Unified framework for PTQ and QAT

## Deployment Frameworks

### llama.cpp
- **GGUF format**: Industry standard for quantized LLMs
- **Speculative decoding**: Built-in support for draft models
- **Multi-threading**: Optimized for CPU inference
- **GPU offloading**: CUDA, Metal, Vulkan support

### ExLlamaV2
- **Optimized for NVIDIA GPUs**: Tensor core utilization
- **Paged attention**: Efficient memory management
- **Speculative decoding**: Support for draft models

### vLLM
- **PagedAttention**: Memory-efficient attention mechanism
- **Continuous batching**: High throughput for serving
- **GPU sharding**: Multi-GPU support

### TensorRT-LLM
- **NVIDIA optimized**: Maximum performance on NVIDIA GPUs
- **Quantization support**: INT8, INT4, FP8
- **Speculative decoding**: Built-in support

## Practical Considerations

### Hardware Requirements

| Model Size | GPU VRAM (FP16) | GPU VRAM (INT4) | Recommended GPU |
|------------|-----------------|-----------------|-----------------|
| 7B | ~14 GB | ~5 GB | RTX 3060 12GB |
| 13B | ~26 GB | ~8 GB | RTX 3090 24GB |
| 30B | ~60 GB | ~18 GB | RTX 3090 24GB (2x) |
| 70B | ~140 GB | ~40 GB | A100 80GB |

### Quantization Quality

- **4-bit quantization**: Typically 1-3% perplexity degradation vs FP16
- **2-bit quantization**: 5-10% perplexity degradation, significant quality loss
- **AWQ vs GPTQ**: AWQ generally preserves quality better for 4-bit

### Performance Optimization

- **Speculative decoding**: 1.5-2x speedup with draft models
- **Paged attention**: Reduces memory fragmentation
- **Continuous batching**: Improves throughput for serving
- **Quantization**: 2-4x speedup with minimal quality loss

## Cross-Domain Links

- [speculative-decoding.md](speculative-decoding.md) — Speculative decoding for inference acceleration
- [local-inference-optimization-2026.md](local-inference-optimization-2026.md) — Local inference optimization 2026
- [fpga-inference-acceleration.md](fpga-inference-acceleration.md) — FPGA acceleration for edge deployment
- [triton-kernels-rtx-optimization.md](triton-kernels-rtx-optimization.md) — Custom kernels for RTX 3090

## Open Questions

- How does QuIP# integrate with ExLlamaV2 backend?
- What is the accuracy degradation of 2-bit quantization on downstream tasks?
- Can mixed-precision (SliM-LLM) be applied to already-quantized GGUF models?
- What are the best practices for deploying 70B+ models on consumer hardware?

## 2026 Production Deployment Insights

### Format Selection Guide (2026)

| Use Case | Recommended Format | Rationale |
|----------|-------------------|-----------|
| Developer workstation (24GB) | GGUF Q4_K_M or Q5_K_M | Best for experimentation via Ollama |
| Production high-throughput serving | AWQ INT4 or FP8 | GGUF not designed for server throughput |
| 70B models on single GPU | AWQ INT4 | Fits in 24GB VRAM with acceptable quality |
| 7B-30B models on RTX PRO 6000 | FP8 or BF16 | No quantization needed for most workloads |
| Mobile/Edge deployment | INT4 (Arm-optimized) | 0.77GB for 1B models, significant latency reduction |

### Quality Degradation Benchmarks

- **INT8**: <1% quality degradation on most tasks, 2x memory reduction
- **INT4 (AWQ)**: 1-3% perplexity degradation, 4x memory reduction
- **INT4 (GPTQ)**: 2-4% perplexity degradation, 4x memory reduction
- **FP8**: <0.5% quality degradation, 2x memory reduction

### Hardware-Specific Recommendations

- **RTX 3090 (24GB)**: AWQ INT4 for 13B-30B models, FP8 for 7B
- **RTX 5090 (32GB)**: AWQ INT4 or GGUF for 13B-30B, BF16/FP8 for 7B
- **RTX PRO 6000 (96GB)**: FP8 or BF16 for 7B-30B, AWQ INT4 for 70B
- **2x RTX PRO 6000 NVLink (192GB)**: BF16 or FP8 for 70B, no quantization needed

## Sources

- GPTQ: Frantar et al., arXiv:2210.17323
- AWQ: Lin et al., arXiv:2306.00802
- GGUF: llama.cpp documentation
- QuIP#: Chee et al., arXiv:2402.04396
- AQLM: Yakovlev et al., arXiv:2306.06093
- SmoothQuant: Mao et al., arXiv:2211.10438
- OmniQuant: Yang et al., arXiv:2308.13130
- BRECQ: Xia et al., arXiv:2106.06366
- PagedAttention: Kwon et al., arXiv:2309.06180
- TensorRT-LLM: NVIDIA documentation
- vLLM: Kwon et al., arXiv:2309.06180
- Zylos Research: LLM Inference Optimization 2026 (Jan 2026)
- VRLA Tech: LLM Quantization Explained 2026
- Presenc AI: Quantization Format Comparison 2026
- ARM Developer: LLM Quantization for Mobile Deployment (Jun 2026)
- DevStars: LLM Inference Optimization Production 2026 (Jun 2026)
- Spheron: Best Open-Source LLMs to Self-Host 2026 (Jun 2026)
