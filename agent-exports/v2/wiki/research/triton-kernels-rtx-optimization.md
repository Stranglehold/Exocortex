# Triton Kernels for RTX 3090 Optimization

**Status:** STABLE
**Created:** 2026-05-16
**Last Updated:** 2026-05-16

## Overview

Custom Triton kernel development for RTX 3090 (SM86, 24GB VRAM) tensor core optimization beyond standard CUDA. Focus on attention acceleration, custom operators, KV cache compression, and autonomous kernel optimization.

## SageAttention Triton Implementation

### Architecture (arXiv:2410.02367)
SageAttention uses Triton to implement INT8 quantized attention with fused operators:
- **Query-Key (QK)**: Quantized to INT8 (per-token or per-block)
- **Value (V)**: Maintained in FP16
- **Fused ROPE + Quantization**: Eliminates intermediate memory writes
- **FP16 Accumulators**: For P×V matrix multiplication (accuracy + speed vs FP32)
- **Tiling**: FlashAttention-style Q/K/V tiling to minimize global memory I/O

### Performance Benchmarks (RTX 3090)
| Model | Baseline | SageAttention | Speedup |
|-------|----------|---------------|---------|
| CogVideoX | 71.57 TOPS | 129.87 TOPS | 1.81× |
| Llama2 | 56.54 TOPS | 108.91 TOPS | 1.93× |
| Average (vs FlashAttention2) | — | — | ~2.7× ops speedup |

### Kernel Hyperparameters
- `BLOCK_M`: 128–256 (query tile size)
- `BLOCK_N`: 64–128 (key/value tile size)
- `num_warps`: 4–8 (warp count per block)
- `num_stages`: 2–3 (pipeline stages for latency hiding)

## AutoKernel: Iterative GPU Kernel Optimization (arXiv:2603.21331)

AutoKernel is an autonomous agent framework for GPU kernel optimization that uses an iterative search loop to refine Triton and CUDA C++ kernels without human intervention.

### Architecture
- **Phase A — Profiling**: Extracts bottleneck kernels from PyTorch models, ranked by Amdahl's law impact
- **Phase B — Optimization Loop**: Agent edits kernel.py, benchmarks, evaluates results iteratively
- **Six-tier optimization playbook**: Tiling, memory coalescing, shared memory usage, warp-level primitives, async copy, pipeline parallelism
- **Five-stage correctness harness**: Smoke tests → shape sweeps → numerical stability → determinism verification → edge-case coverage

### Performance (NVIDIA H100)
| Operator | vs Eager Mode | vs torch.compile |
|----------|---------------|------------------|
| RMSNorm | 5.29× | 2.83× |
| Softmax | 2.82× | 3.44× |
| Cross-Entropy | 2.21× | 2.94× |

First-place on vectorsum_v2 B200 leaderboard. Triton backend supports SM86 (RTX 3090 compatible).

## TurboQuant: KV Cache Compression (arXiv:2504.19874)

TurboQuant achieves near-optimal KV cache quantization for LLM inference, enabling extreme context lengths on consumer GPUs.

### Method
- **Two-stage quantization**: MSE quantizer → 1-bit Quantized JL (QJL) transform on residual
- **3.5 bits per channel**: Absolute quality neutrality (no accuracy loss)
- **2.5 bits per channel**: Marginal quality degradation
- **3-bit keys / 2-bit values**: Practical target for dense and MoE architectures

### RTX 3090 Benchmarks
- **Gemma 4 26B**: 120 tokens/second at full context with 3.8× KV cache compression
- **70B models**: Feasible on 3× RTX 3090 (72GB total) with TurboQuant
- **100K context**: Runnable on single RTX 3090 with compression vs ~32K uncompressed

### Integration
- vLLM integration via `turbokv` PyPI package
- Compatible with SageAttention for compound speedup (kernel acceleration + memory compression)

## TritonForge: Profiling-Guided Optimization (arXiv:2512.09196)

TritonForge provides automated, profiling-guided Triton kernel optimization:
- **Kernel analysis**: Identifies memory access patterns and compute bottlenecks
- **Runtime profiling**: Data-driven feedback loop for bottleneck identification
- **Iterative code transformation**: Targeted modifications evaluated automatically
- **Focus**: Streamlines expert-level Triton optimization without requiring deep GPU architecture knowledge

## Custom Triton Kernel Patterns for RTX 3090

### Key Design Principles
1. **Tiling**: FlashAttention-style Q/K/V tiling to minimize global memory I/O
2. **Shared memory reuse**: Cache intermediate results in L2 before global memory access
3. **Warp-level primitives**: Use `tl.arange`, `tl.load` with vectorized memory access
4. **Async copy**: `tl._experimental_async_copy` for SM86+ (RTX 3090 supported)
5. **FP16 accumulation**: P×V in FP16 for speed vs FP32 (validated by SageAttention)

## RTX 3090 Optimization Checklist
- [x] SageAttention 2 for attention layers (1.8–1.9× speedup validated)
- [x] TurboQuant for KV cache compression (3.8× memory reduction)
- [ ] AutoKernel-style iterative optimization for bottleneck operators
- [ ] Custom Triton kernels for RMSNorm, softmax, cross-entropy
- [ ] INT4 inference via GPTQ/AWQ with Triton kernel acceleration
- [ ] TeaCache integration for cache-aware attention

## Current State (May 2026)

### SageAttention 2
- Supports RTX 3090/4090, L20, L40, A100, A800, A6000
- Triton kernel auto-selected for SM86 (RTX 3090)
- `sageattn_varlen` for variable-length sequences (Nov 2024)

### Installation
- Linux: Standard Triton installation works
- Windows: Requires custom Triton 3.2.0 port (Mar 2025)
- Common error: "Cannot find a matching Triton" → version mismatch

## Cross-Domain Connections
- **FPGA inference**: Both address edge inference constraints
- **LoRaWAN sensor networks**: Custom Triton kernels for on-device anomaly detection
- **SCADA/ICS**: Low-latency inference for grid protection
- **Autonomous coding agents**: AutoKernel demonstrates iterative self-improvement loop pattern

## References
- [SageAttention GitHub](https://github.com/thu-ml/SageAttention)
- [SageAttention Paper (arXiv:2410.02367)](https://arxiv.org/abs/2410.02367)
- [AutoKernel (arXiv:2603.21331)](https://arxiv.org/abs/2603.21331)
- [TurboQuant (arXiv:2504.19874)](https://arxiv.org/abs/2504.19874)
- [TritonForge (arXiv:2512.09196)](https://arxiv.org/abs/2512.09196)
- [Triton Documentation](https://triton-lang.org)
- [FlashAttention Paper (arXiv:2205.14135)](https://arxiv.org/abs/2205.14135)
