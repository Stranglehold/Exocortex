# LLM Inference Serving Systems

**Status: STABLE**
**Created: 2026-08-03 | Last Deepened: 2026-08-03**
**Tags: inference, serving, vllm, sglang, production, disaggregation, continuous-batching, pagedattention, local-to-frontier-bridging**

## Overview

LLM inference serving systems are the production infrastructure layer between trained models and interactive/API workloads. They convert the autoregressive generation loop into a multi-tenant, high-throughput service with bounded latency. The field's inflection point was vLLM's PagedAttention (Kwon et al., SOSP 2023, arXiv:2309.06180), which eliminated KV-cache memory fragmentation and enabled near-zero-waste dynamic memory management. Modern serving stacks combine PagedAttention-class memory management with continuous (iteration-level) batching, chunked prefill, prefix caching, CUDA/HIP graph execution, and quantization support to sustain thousands of tokens/second on H100-class hardware.

While Exocortex neighbors already cover speculative decoding, KV-cache compression, quantization, multi-GPU parallelism, and test-time compute, the serving substrate itself was a genuine corpus gap: continuous batching and PagedAttention concepts had near-zero journal coverage. This page anchors the production serving layer and its 2026 disaggregated architectures.

## Core Serving Techniques

### PagedAttention
- Treats the KV cache as fixed-size blocks (pages), allocated on demand like virtual memory; reduces memory waste and enables sharing across sequences (parallel sampling, beam search).
- PagedAttention v2 adds dynamic management with near-zero waste; vLLM remains the reference implementation and is the de facto production default for open-weight models.

### Continuous Batching (Iteration-Level Scheduling)
- Processes new requests at the iteration (token) level rather than waiting for a full batch window to finish; fills pipeline gaps immediately upon request completion.
- ORCA (NeurIPS 2022) introduced iteration-level scheduling; vLLM and SGLang popularized it in production.

### Chunked Prefill & Prefix Caching
- Chunked prefill interleaves long-prompt prefill work with decode work, reducing head-of-line blocking for short requests.
- Prefix caching reuses KV blocks across requests sharing a prompt prefix (system prompts, few-shot templates), dramatically cutting TTFT for repeated prompts.

### CUDA/HIP Graph Execution
- Captures GPU kernel launch sequences to reduce CPU launch overhead; vLLM ships "piecewise" and full CUDA graphs, while optimized kernels further reduce latency.

## Production Engine Landscape (2026)

| Engine | Core Innovation | Strengths | Ecosystem Notes |
|---|---|---|---|
| vLLM | PagedAttention, continuous batching, chunked prefill, prefix caching, CUDA graphs | Highest throughput, broadest model/quantization support (GPTQ/AWQ/INT4/INT8/FP8), OpenAI-compatible API, tensor parallelism | GitHub vllm-project/vllm; production default for high-throughput open-weight serving |
| SGLang | RadixAttention (radix-tree KV prefix reuse), compressed FSM structured output, frontend language for LLM programs | Agentic/multi-call workflows, structured generation, strong TTFT under prefix reuse | arXiv:2312.07104 (Zheng et al.); LMSys ecosystem |
| TensorRT-LLM | NVIDIA kernel fusion/quantization, in-flight batching, engine graphs | Peak per-GPU performance on NVIDIA hardware, FP8, MoE support | Requires compilation; strongest latency on H100/Blackwell |
| NVIDIA Dynamo | Orchestration layer above engines; disaggregated prefill/decode, intelligent routing, multi-tier KV caching, automatic scaling | Up to 30× higher request throughput for DeepSeek-R1 on Blackwell (NVIDIA GTC 2026 claim); coordinates vLLM/SGLang/TensorRT-LLM into multi-node systems | GitHub ai-dynamo/dynamo; GA at GTC 2026 |
| llama.cpp | CPU/consumer-GPU GGUF inference, heterogeneous GPU split | Local-first, zero-dependency; lower raw throughput than vLLM but unmatched portability | Ollama builds on llama.cpp; MDPI 2026 benchmark found vLLM superior for concurrent serving |

Benchmark direction (2026): vLLM reaches ~2,400 tok/s at 100 concurrent requests on H100-class hardware in community/test setups; SGLang is competitive and frequently wins TTFT-heavy and agentic workloads; TensorRT-LLM remains strong on NVIDIA per-GPU peak. Community results vary by hardware, model, and workload; treat specific numbers as directional.

## Disaggregated Serving: Prefill/Decode Separation

- DistServe (arXiv:2401.09670) established the paradigm: separate compute-intensive prefill from memory-bandwidth-bound decode onto different pools, then scale them independently. Claim: several times more requests within the same latency targets versus colocated serving.
- Mooncake (arXiv:2407.00079) is the production KVCache-centric system behind Kimi (Moonshot AI), separating prefill/decode clusters and leveraging CPU/DRAM/SSD for a disaggregated KV cache.
- 2026 evolution: prefill-decode disaggregation is the dominant deployment paradigm for large-scale serving; partial-prefill routing for multi-turn conversations cut TTFT by ~68% on subsequent turns (arXiv:2603.13358); efficient multi-round inference over disaggregated serving is an active arXiv thread (arXiv:2602.14516); cross-datacenter "prefill-as-a-service" is proposed (arXiv:2604.15039).
- NVIDIA Dynamo operationalizes disaggregation as a first-class production feature, including KV transfer between prefill/decode workers.

## Verification Status

- Corpus-first grounding: memory_load + wiki corpus reads (multi-gpu-inference-architectures, quantization-advances-llm-inference, speculative-decoding-kv-cache-compression, local-model-inference-optimization-pipeline). Strong shared-corpus base.
- The 355-book reference library was not located in this environment's filesystem under expected paths; web primary sources (arXiv, NVIDIA blog, GitHub) filled that gap. This is a genuine library-availability gap, not a claim that the library has no relevant books.
- vLLM throughput figure (2,400 tok/s at 100 concurrent) is from a vendor/blog benchmark and is reported as directional, not measured.

## Cross-Domain Connections

| Domain | Connection |
|---|---|
| [[multi-gpu-inference-architectures]] | Serving systems orchestrate TP/PP from multi-GPU page; interconnect scaling factors bind serve throughput |
| [[speculative-decoding-kv-cache-compression]] | Serving infrastructure provides the batch scheduler where speculative decoding and KV compression compose |
| [[quantization-advances-llm-inference]] | Serving engines expose GPTQ/AWQ/FP8 quantization paths; quantization-aware kernels determine real throughput |
| [[test-time-compute-scaling-local-models]] | Serving is the deployment layer that makes test-time search/verifier loops practical |
| [[local-model-inference-optimization-pipeline]] | Pipeline stages (compression, kernels, serving) overlapping; serving is the final composable stage |
| [[memory-centric-ai-hardware-cxl]] | KV-cache partitioning/pooling in disaggregated serving mirrors CXL memory pooling economics |
| [[rtx-3090-cuda-optimization]] | Consumer-GPU macro-kernels integrate with vLLM/llama.cpp scheduling; sync-bound ceilings fix serving limits |
| [[agent-observability-tracing]] | Serving engines emit token/step traces consumed by observability/GENAI semantic conventions |
| [[agentic-deep-research-pipelines]] | Agentic loops with repeated system prefixes depend on prefix caching/RadixAttention for feasibility |
| [[context-management-ai-agent-frameworks]] | KV management in serving is the system-level mirror of agent context pruning/compression |

## References

1. Kwon et al., "Efficient Memory Management for LLM Serving with PagedAttention," SOSP 2023. arXiv:2309.06180
2. Zheng et al., "SGLang: Efficient Execution of Structured Language Model Programs," arXiv:2312.07104
3. Zhong et al., "DistServe: Disaggregating Prefill and Decoding for Goodput-optimized LLM Serving," arXiv:2401.09670
4. Qin et al., "Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving," arXiv:2407.00079
5. Yu et al., "ORCA: A Distributed, Hybrid Component-Based Embedded System," NeurIPS 2022 (iteration-level scheduling lineage)
6. NVIDIA, "Introducing NVIDIA Dynamo," developer.nvidia.com, 2025
7. NVIDIA Dynamo documentation: disaggregated serving guide, docs.nvidia.com/dynamo, 2026
8. vLLM GitHub: vllm-project/vllm
9. Spheron, "LLM Serving Optimization: Continuous Batching, PagedAttention, and Chunked Prefill on H100," 2026
10. DigitalOcean, "Prefill/Decode Disaggregation: Why Production LLM Inference Is Splitting Onto Separate Hardware," 2026
11. arXiv:2603.13358 (partial-prefill disaggregation, multi-turn serving)
12. arXiv:2602.14516 (efficient multi-round inference over disaggregated serving)
13. arXiv:2604.15039 (prefill-as-a-service, cross-datacenter KV cache)
14. MDPI Applied Sciences 16(11):5435, "Benchmarking Ollama and vLLM for Concurrent LLM Serving," 2026
