# FPGA-Based Inference Acceleration

**Status:** STABLE

**Last Updated:** 2026-07-03

## Overview

FPGA (Field Programmable Gate Array) inference acceleration leverages reconfigurable hardware fabric to run deep neural networks — including LLMs and CNNs — with lower latency and higher energy efficiency than general-purpose GPUs. FPGAs provide fine-grained data control, distributed on-chip memory, and the ability to implement custom data-path designs that avoid GPU overheads like memory hierarchy contention and instruction fetch/decode.

The fundamental challenge: FPGAs have fewer computational resources (DSP slices, logic cells) than GPUs at equivalent process nodes. The AMD V80 (7nm) offers ~25 INT8 TOPS vs NVIDIA A100 (7nm) at 624 INT8 TOPS. However, FPGAs have much greater on-chip memory density — the V80 integrates 14.9× more on-chip memory units than the A100 — making memory-based computation paradigms uniquely suited to FPGA deployment.

## Key Advantages of FPGA over GPU

1. **Distributed On-Chip Memory**: FPGAs embed abundant BRAM/URAM/LUTRAM close to compute units, eliminating the von Neumann bottleneck. A memory-based MAC on FPGA consumes 3.8 pJ (7nm), 2.4× less than arithmetic counterpart (Jouppi et al. 2021).
2. **Custom Dataflow Architectures**: Spatial designs can overlap memory access with computation, achieving near-roofline utilization. Sequential execution strategies map naturally to FPGA pipelines without GPU warp-scheduling overhead.
3. **Energy Efficiency**: LUT-LLM achieves 3.05–6.60× higher tokens/J than GPUs (A100, MI210) for Qwen 3 1.7B inference.
4. **Deterministic Latency**: FPGA designs have fixed-cycle operation, critical for real-time edge AI applications.
5. **Edge Deployment**: Embedded FPGA platforms (Xilinx KV260, ZCU104) enable local LLM inference without cloud dependency — llama-fpga runs Llama2-7B at 5–19 tok/s on sub-30W hardware.

## Key Approaches

### 1. Arithmetic-Based Acceleration
Conventional FPGA accelerators use DSP-based matrix multiply units with quantization (W4A8, INT8). Examples:
- **FlightLLM** (Zeng et al. 2024): complete mapping flow for LLMs on FPGAs, uses sparsification and aggressive quantization (3.5-bit weights). LUT-LLM is 1.6× faster end-to-end.
- **InTAR** (He et al. 2025): inter-task auto-reconfigurable design for varying data volumes.
- **Allo** (Chen et al. 2024): composable accelerator design programming model.

Limitations: GPU optimizations (FlashAttention, GPTQ kernel fusion) have narrowed FPGA's arithmetic throughput advantage. FPGA arithmetic designs often underperform GPUs due to fewer DSP resources.

### 2. Memory-Based Computation (Table Lookup)
Replaces multiply-accumulate operations with pre-computed lookup table reads. Key innovation: vector quantization (VQ) of weights and activations to map linear layer computations to table indices.

**Evolution:**
- **LUT-NN** (Tang et al. 2023): introduced centroid learning + table lookup for CNNs.
- **LUT-DLA** (Li et al. 2025): hardware-algorithm co-design, two-stage training (K-means init + STE fine-tuning).
- **T-MAC** (Wei et al. 2025): CPU renaissance via table lookup for edge LLM deployment.
- **LUT-LLM** (He et al. 2026): first FPGA accelerator for 1B+ parameter LLMs using memory-based computation.

**LUT-LLM Architecture (He et al. 2026, arXiv:2511.06174):**
- Targets Qwen 3 1.7B on AMD Alveo V80 FPGA (7nm, 819 GB/s HBM bandwidth).
- Quantization: activation-weight vector co-quantization (v=2, c_a=64, c_w=16, INT8 lookup tables).
- Three key hardware innovations:
  1. **Bandwidth-aware Parallel Centroid Search (BPCSU)**: hybrid architecture balancing pipeline depth vs reduction tree breadth to hide centroid search latency under off-chip memory access.
  2. **Efficient 2D Table Lookup Prefix-Sum (2D-PSum)**: constructs 2D lookup tables (activation centroid × weight centroid), retrieves entries via weight centroid indices with SIMD accumulation.
  3. **Spatial-Temporal Hybrid Design**: linear layers execute sequentially (sustaining pipelined centroid search), while attention executes in dataflow mode — saves 14% on-chip buffer allocation.
- Performance: 1.10–3.29× speedup vs A100 (INT8/INT4), 3.05–6.60× higher energy efficiency. Training efficiency: reduced from >1000 GPU-hours to ~10 A100 hours via kernel fusion optimizations.
- Accuracy: within 1.8% of FP16 baseline on GLUE benchmark (geomean).

### 3. Heterogeneous GPU-FPGA Systems
- **GLITCHES** (Tsinghua): GPU for prefill stage (high parallelism), FPGA for decode stage (low latency). Exploits the complementary strengths of each platform.
- **Hummingbird+** : advancing FPGA LLM deployment from research prototypes to production edge products.

### 4. Open-Source Frameworks
- **llama-fpga** (GitHub: adamgallas/llama-fpga): world's first open-source FPGA-based LLM accelerator. Supports Llama2-7B (AWQ 4-bit) on Xilinx KV260 (5 tok/s), ZCU104 (4–9 tok/s), and Alveo U250 (18–19 tok/s). Includes complete Vivado projects, SpinalHDL-generated Verilog, SDK C sources, and pre-generated model binaries. Tightly coupled to Llama2 architecture; adaptation to other models requires RTL-level modifications.
- **Terafly** (Zheng): multi-node FPGA cooperative LLM inference for high-throughput deployment.
- **TeLLMe / TeLLMe v2**: KV260-targeted LLM acceleration.

## Benchmarks

| Platform | Model | Precision | Tokens/s | Energy (tok/J) | Notes |
|----------|-------|-----------|----------|----------------|-------|
| AMD V80 (LUT-LLM) | Qwen 3 1.7B | INT8 LUT | 1.10–3.29× vs A100 | 3.05–6.60× vs GPU | 250 MHz, 32 HBM channels |
| Alveo U250 (llama-fpga) | Llama2-7B | AWQ 4-bit | 18–19 | — | Quad DDR4 channels |
| KV260 (llama-fpga) | Llama2-7B | AWQ 4-bit | ~5 | — | PS-side 4 GB RAM |
| ZCU104 (llama-fpga) | Llama2-7B | AWQ 4-bit | 8–9 | — | PS+PL hybrid memory |
| NVIDIA A100 (vLLM+GPTQ) | Qwen 3 1.7B | INT8 | baseline | baseline | HBM 2.0 TB/s, 624 INT8 TOPS |
| AMD MI210 | Qwen 3 1.7B | INT8 | 0.3× A100 | lower | 181 INT8 TOPS |

**Key benchmark findings (LUT-LLM):**
- Decode speedup holds even against A100 INT4 (1.10×). Energy efficiency gap widens with longer output sequences.
- Extrapolation to Qwen 3 32B: 1.2× speedup vs A100 INT8, but 0.8× vs A100 INT4 (larger models benefit GPUs' higher compute density).
- Compared to FPGA arithmetic accelerators: LUT-LLM 5.6× faster than Allo, 1.9× faster than InTAR, 1.6× faster than FlightLLM.

## Limitations and Challenges

1. **Model-Specific Design**: Most FPGA accelerators are tightly coupled to specific model architectures (Llama, Qwen); adapting to new architectures requires RTL redesign.
2. **Compilation Time**: FPGA synthesis and place-and-route can take hours to days, unlike GPU kernel compilation (seconds).
3. **Precision Tradeoffs**: Vector quantization introduces accuracy loss; LUT-LLM shows 1.8% geomean drop vs FP16.
4. **Scaling to Large Models**: GPUs maintain advantage for models >30B parameters due to raw compute density and ecosystem maturity.
5. **Developer Ecosystem**: FPGA toolchains (Vivado, Vitis HLS) are less accessible than CUDA/PyTorch.

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[power-efficient-local-llm-inference-benchmarks]] | FPGA energy efficiency directly addresses tokens-per-watt metrics |
| [[processing-in-memory-riscv-edge-ai]] | Memory-based computation on FPGA shares architectural principles with PIM — both shift compute to data |
| [[multi-gpu-inference-architectures]] | Heterogeneous GPU-FPGA systems (GLITCHES) are the next frontier beyond multi-GPU |
| [[bridging-local-to-frontier-model-performance]] | FPGA acceleration is a hardware substrate for local-to-frontier bridging via cascade routing and speculative decoding |
| [[custom-pcb-sensor-networks]] | Embedded FPGA platforms (KV260, ZCU104) enable edge AI for sensor networks |
| [[context-management-ai-agent-frameworks]] | KV cache management on FPGA (prefetch/write-out orchestration) is a hardware-level context management problem |
| [[deterministic-scaffolding]] | FPGA fixed-cycle operation aligns with deterministic execution philosophy |
| [[entropy-as-signal]] | Roofline analysis of memory-bound vs compute-bound inference is analogous to entropy threshold analysis |

## References

1. He, Z., Ye, S., Ma, R., Wang, Y., & Cong, J. (2025/2026). LUT-LLM: Efficient Language Model Inference with Memory-based Computations on FPGAs. arXiv:2511.06174.
2. Li, J., et al. (2024/2025). Large Language Model Inference Acceleration: A Comprehensive Hardware Perspective. arXiv:2410.04466.
3. Adamgallas. llama-fpga: FPGA-based LLM Accelerator. GitHub. https://github.com/adamgallas/llama-fpga
4. Zeng, S., et al. (2024). FlightLLM: Efficient large language model inference with a complete mapping flow on FPGAs. FPGA 2024.
5. Chen, H., et al. (2024). Allo: A programming model for composable accelerator design. PLDI 2024.
6. Li, G., et al. (2025). LUT-DLA: Lookup Table as Efficient Extreme Low-Bit Deep Learning Accelerator. HPCA 2025.
7. Wei, J., et al. (2025). T-MAC: CPU renaissance via table lookup for low-bit LLM deployment on edge. EuroSys 2025.
8. ACM Survey: FPGA-based Deep Learning Inference Accelerators: Where Are We Standing? ACM Computing Surveys, 2023.
9. IEEE Review: A Review of FPGA-Driven LLM Acceleration. IEEE Xplore, 2024.
10. GLITCHES: GPU-FPGA LLM Inference Through a Collaborative Heterogeneous System. Tsinghua University.
