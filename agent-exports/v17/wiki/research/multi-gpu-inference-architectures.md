# Multi-GPU Inference Architectures for Local AI

**Status: STABLE**
**Created: 2026-06-03 | Last Deepened: 2026-07-03**
**Tags: hardware, inference, multi-gpu, parallelism, consumer-gpu, tensor-parallelism, pipeline-parallelism, nvlink, pcie, local-to-frontier-bridging**

## Overview

Multi-GPU inference distributes LLM computation across multiple graphics cards to overcome single-GPU memory constraints and improve throughput/latency. The primary motivation: models exceed VRAM capacity of even the largest single cards. Llama 3.1 405B at Q4 needs ~230GB — no single GPU provides that. At FP16, Llama 405B requires ~810GB and DeepSeek R1 needs ~720GB. Multi-GPU is not optional for these models; it's structurally necessary.

Consumer GPUs (RTX 3090, RTX 4090) add a critical constraint: they lack NVLink. The interconnect between cards determines effective throughput capture. A dual RTX 3090 setup delivers only ~75% effective VRAM (PCIe scaling factor 0.75x) compared to dual H100 SXM at 92% (NVLink). Understanding these scaling factors is what separates functional multi-GPU setups from expensive disappointments.

## Parallelism Strategies

Five primary strategies exist for distributed inference, each with distinct trade-offs in latency, throughput, and hardware requirements:

### Tensor Parallelism (TP)

**What it does:** Shards individual layers across multiple GPUs. Each GPU holds a portion of every weight matrix. During inference, each processes its shard in parallel, then an all-reduce operation synchronizes partial results before the next layer runs — for every single token generated.

**Performance profile (Qwen3-32B on 2× A100-80GB, NVLink):**
- Delivers best latency across all metrics simultaneously (JarvisLabs 2026 benchmarks)
- 3× TTFT improvement over single-GPU baseline
- Consistent TPOT and ITL gains across concurrency levels
- Requires fastest possible interconnect — NVLink or equivalent
- Use case: latency-sensitive production serving with NVLink-equipped GPUs

**Effective VRAM scaling by interconnect:**
| Interconnect | Scaling Factor | Overhead | Example Config | Effective VRAM |
|-------------|---------------|----------|---------------|---------------|
| NVLink 5.0 (B200/B100) | 0.93x | 7% | 8× B200 180GB (1,440GB raw) | ~1,339GB |
| NVLink 4.0 (H100/H200 SXM) | 0.92x | 8% | 2× H100 80GB (160GB raw) | ~147GB |
| NVLink 3.0 (A100 SXM) | 0.90x | 10% | 4× A100 80GB (320GB raw) | ~288GB |
| AMD Infinity Fabric (MI300X) | 0.88x | 12% | 8× MI300X 192GB (1,536GB raw) | ~1,352GB |
| PCIe Gen5 x16 (consumer GPUs) | 0.75x | 25% | 2× RTX 3090 24GB (48GB raw) | ~36GB |

**Key insight:** PCIe Gen5 x16 delivers ~64 GB/s — roughly 14× less bandwidth than NVLink 4.0's 900 GB/s. This gap means consumer GPUs lose 25% of their aggregate throughput to synchronization stalls. Two 24GB 3090s yield only ~36GB effective — barely more than a single RTX A6000 48GB ($4,500) for inference use cases.

### Pipeline Parallelism (PP)

**What it does:** Slices the model by layers. GPU 0 runs layers 1-10, GPU 1 runs layers 11-20, and data flows sequentially. Communication happens only at stage boundaries where intermediate activations transfer.

**Performance profile (Qwen3-32B on 2× A100-80GB):**
- Cuts TTFT P99 by 2.5-3× at high concurrency through larger aggregate KV cache
- Introduces pipeline bubbles when stages are unbalanced
- Enables serving models that don't fit on any single GPU
- Lower communication overhead than TP (activations, not weight-sharding syncs)
- Use case: throughput-oriented serving where latency isn't primary concern

### Data Parallelism (DP)

**What it does:** Replicates entire model on each GPU. Each GPU processes different user requests independently. Zero inter-GPU communication during inference. Scales throughput linearly with GPU count until saturation.

**Performance profile (Qwen3-32B on 2× A100-80GB, JarvisLabs benchmarks):**
| Metric | Baseline (1× GPU) at c=180 | DP=2 at c=180 | Improvement |
|--------|---------------------------|---------------|-------------|
| Output Throughput (tok/s) | 1,781 | 2,833 | +59% |
| TTFT P99 (ms) | 11,020 | 2,379 | -78% |
| TPOT P99 (ms) | 190 | 72 | -62% |
| ITL P99 (ms) | 158 | 104 | -34% |

**Saturation behavior:** Single A100 saturates at c≈120. DP=2 peak operating range is c=120-180. Beyond c=300, both configurations are memory-bound. Throughput gains at moderate concurrency: ~50% boost.

**Key constraint:** Model must fit on a single GPU. Not usable for Llama 405B or DeepSeek R1 unless combined with TP/PP.

### Expert Parallelism (EP)

For Mixture-of-Experts (MoE) models like Mixtral, each GPU holds different expert sub-networks. Tokens get routed to the correct expert. Works in conjunction with TP or DP as a modifier flag. vLLM supports EP as a special flag for MoE models.

### Context Parallelism (CP)

Splits long sequences across GPUs, each handling a portion of the context window. Useful for very long prompts where the KV cache exceeds single-GPU capacity.

## Interconnect Architecture: NVLink vs PCIe

The interconnect is the defining constraint for multi-GPU inference economics. TP requires all-reduce synchronization on every forward pass — every token generated. The bandwidth available for that synchronization directly determines overhead.

**Bandwidth hierarchy (bidirectional per GPU):**
| Technology | Bandwidth | Effective Scaling | GPU Generation |
|-----------|----------|------------------|----------------|
| NVLink 5.0 | 1,800 GB/s | 0.93x | B200, B100, GB200 |
| NVLink 4.0 | 900 GB/s | 0.92x | H100, H200 SXM |
| AMD Infinity Fabric 4.0 | 896 GB/s | 0.88x | MI300X, MI325X |
| NVLink 3.0 | 600 GB/s | 0.90x | A100 SXM |
| PCIe Gen5 x16 | 64 GB/s | 0.75x | RTX 3090, RTX 4090, L40S |

**Practical implications:**
- 2× H100 80GB SXM via NVLink: 0.92 × 160GB = ~147GB effective — fits Llama 405B at Q4
- 2× L40S 48GB PCIe: 0.75 × 96GB = ~72GB effective — paying for 96GB, getting 72GB
- 2× RTX 3090 24GB PCIe: 0.75 × 48GB = ~36GB effective — fits most 70B models at Q4 but with significant latency overhead from PCIe all-reduce stalls

## Software Implementations

All major inference engines support multi-GPU. Software is rarely the bottleneck — hardware interconnect and configuration management are where complexity lives.

| Engine | TP Support | DP Support | PP Support | Configuration | Heterogeneous GPU? |
|--------|-----------|-----------|-----------|--------------|-------------------|
| vLLM | Yes (`--tensor-parallel-size`) | Yes (`--data-parallel-size`) | Yes (`--pipeline-parallel-size`) | Single flag | No |
| TGI | Yes (`--num-shard`) | Yes (replicas) | No | Single flag | No |
| llama.cpp | Yes (`--tensor-split`) | No (external LB) | No | Manual VRAM weights | **Yes** (best consumer option) |
| ExLlamaV2 | Yes (`--gpu-split`) | No | No | GB-per-GPU allocation | No |
| SGLang | Yes | Yes | Yes | Similar to vLLM | No |
| TensorRT-LLM | Yes | Yes | Yes | Tensor/pipeline model parallelism | No |

**llama.cpp heterogeneous GPU support:** The `--tensor-split 24,8,0,0` flag assigns relative proportions of layers. This is the only major engine supporting mixed GPU configurations — critical for consumer setups with mismatched cards (e.g., RTX 3090 + RTX 3060). However, manual tuning is required for optimal performance.

**vLLM internal load balancing:** With `--data-parallel-size=2`, vLLM's API server has direct visibility into each rank's queue state. Routes requests to least-loaded rank based on queue depth. External load balancing (nginx round-robin) is simpler but blind to GPU state — can route to overloaded GPU while another idles.

**Continuous batching** in TGI and vLLM amortizes multi-GPU communication overhead across larger batch sizes. This partly mitigates the PCIe penalty on consumer GPUs by overlapping communication with compute for other requests in the batch.

## Consumer GPU Multi-GPU: RTX 3090 Case Study

Consumer GPUs are the practical frontier for local AI deployment. The RTX 3090 (24GB, PCIe Gen4 x16) is the most common high-VRAM consumer card.

**RTX 3090 parameters:**
- Memory bandwidth: 936 GB/s (single card)
- PCIe Gen4 x16: ~32 GB/s (no NVLink bridge available on 3090)
- Power: 350W per card
- Cost: $700-800 used (2026)

**Dual RTX 3090 performance envelope:**
| Configuration | Raw VRAM | Effective VRAM (TP) | Models Unlocked |
|--------------|----------|-------------------|----------------|
| 1× RTX 3090 (Q4_K_M) | 24GB | 24GB | Most 7B, some 13B |
| 2× RTX 3090 (Q4_K_M) | 48GB | ~36GB | Most 70B at Q4, 27B at Q5 |
| 4× RTX 3090 (Q4_K_M) | 96GB | ~72GB | Llama 70B at Q8, 123B at Q4 |

**Throughput data (llama.cpp, Qwen3.6-27B Q4_K_M, dual RTX 3090 via PCIe):**
- Tensor parallelism (--tensor-split 24,24): ~28-35 tok/s with significant per-layer all-reduce stalls
- Alternative: run two independent instances (DP equivalent): 2× ~45 tok/s for batch workloads, but requires per-request routing
- **Practical rule:** For interactive use where latency matters, DP (two instances) outperforms TP on PCIe due to the 25% all-reduce penalty. Only use TP on consumer GPUs when the model doesn't fit on a single card.

**Power considerations:** Dual 3090 at full load draws ~700W. Multi-hour inference sessions require active cooling and circuit planning. The cost-per-inference-token advantage over cloud GPUs erodes with electricity rates above $0.20/kWh for continuous workloads.

## Cost Analysis: Multi-Card vs Single-Large-Card

| Option | VRAM | Est. Used Price (2026) | Scaling Quality | Best For |
|--------|------|----------------------|-----------------|----------|
| 2× RTX 3090 24GB | ~36GB effective | $1,400-1,600 | PCIe 0.75x | Budget 70B Q4, experimental |
| 1× RTX A6000 48GB | 48GB | $2,500-3,000 | Single card, no sync overhead | Professional local 70B Q4 |
| 2× RTX A6000 48GB | ~72GB effective | $5,000-6,000 | PCIe 0.75x | 70B Q8, 123B Q4 |
| 1× H100 80GB SXM | 80GB | Cloud: $1.90-2.50/hr | Single card, full bandwidth | Cloud burst workloads |
| 2× H100 80GB SXM | ~147GB effective | Cloud: $3.80-5.00/hr | NVLink 0.92x | Llama 405B Q4 |
| 4× A100 80GB SXM | ~288GB effective | Cloud: $5.00-7.00/hr | NVLink 0.90x | DeepSeek R1 Q4 |

**Break-even point:** A $3,000 A6000 breaks even against $2.50/hr H100 cloud at ~1,200 hours of inference. For the hobbyist running 4 hours/day, that's ~300 days. For continuous workloads (24/7), break-even is ~50 days.

## Decision Heuristic

**If your model fits on one GPU:** Use no multi-GPU. Always.

**If you need throughput and model fits on one GPU:** Use DP (replicas). No inter-GPU communication. ~50% throughput improvement per added GPU.

**If your model doesn't fit and you have NVLink:** Use TP. Best latency. 8-10% overhead. Production serving.

**If your model doesn't fit and you have PCIe consumer GPUs:**
- TP via llama.cpp with --tensor-split if you MUST run models that exceed single GPU
- Consider DP with two independent instances if latency matters and model fits on one card
- Prefer a single larger GPU (A6000 48GB, used H100) over multiple PCIe cards for inference

**If you need both throughput and large models:** Combine DP + TP on NVLink clusters (production AI labs pattern).

## Cross-Domain Connections

- [[bridging-local-to-frontier-model-performance]] — Multi-GPU is the hardware substrate for local-to-frontier bridging. The 0.75x PCIe penalty constrains local inference throughput directly; cascade routing and model merging techniques depend on inference speed.
- [[power-efficient-local-llm-inference-benchmarks]] — Multi-GPU doubles power draw. Efficiency analysis (tokens-per-watt) must incorporate scaling factor losses.
- [[chiplet-architectures-ai-inference]] — The interconnect bandwidth bottleneck described here mirrors chiplet interconnect challenges at silicon level.
- [[ai-agent-architecture-local-inference]] — Local agent architectures that span multi-GPU systems face the same partition-vs-communication trade-offs.
- [[processing-in-memory-riscv-edge-ai]] — PIM compresses data movement; the PCIe bottleneck is exactly the data movement tax PIM architectures seek to eliminate.
- [[memory-architecture-taxonomy]] — Multi-GPU VRAM pooling is an external memory architecture pattern; the consolidation pipeline parallels memory management across GPU boundaries.
- [[quantitative-market-analysis-statistical-arbitrage]] — GPU cost and availability dynamics (H100 vs A6000 vs 3090 used market) are tradable signals.
- [[context-management-ai-agent-frameworks]] — Multi-GPU KV cache distribution is a form of distributed context management.

## References

1. WillItRunAI Blog, "Multi-GPU LLM Inference Guide — NVLink vs PCIe, Tensor Parallelism" (2026). Real scaling factors sourced from fit engine powering WillItRunAI's VRAM calculator. https://willitrunai.com/blog/multi-gpu-llm-inference-guide
2. JarvisLabs AI Blog, "Scaling LLM Inference: DP, PP & TP in vLLM" (2026). Benchmark data: Qwen3-32B on 2× A100-80GB, ShareGPT dataset, concurrency 60-420. https://jarvislabs.ai/blog/scaling-llm-inference-dp-pp-tp
3. vLLM Documentation, "Parallelism and Scaling" (2026). Tensor/pipeline/data parallelism configuration reference. https://docs.vllm.ai/en/latest/serving/parallelism_scaling/
4. AMD ROCm Blog, "The vLLM MoE Playbook: A Practical Guide to TP, DP, PP and Expert Parallelism" (2026). https://rocm.blogs.amd.com/software-tools-optimization/vllm-moe-guide/
5. Hamel Husain, "vLLM & Large Models" (2025). Distributed inference patterns. https://hamel.dev/notes/llm/inference/big_inference.html
6. llama.cpp GitHub, Tensor Split documentation. https://github.com/ggerganov/llama.cpp
7. ExLlamaV2 GitHub, GPU Split documentation. https://github.com/turboderp/exllamav2
8. TrackAI, "Distributed LLM Inference: Tensor Parallelism & Pipeline Parallelism" (2026). https://trackai.dev/tracks/performance/specialized-performance/distributed-inference/
9. Markaicode, "Multi-GPU Inference Setup: Distribute LLM Workloads Efficiently" (2026). https://markaicode.com/multi-gpu-llm-inference-setup/
