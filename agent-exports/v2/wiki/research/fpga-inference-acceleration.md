# FPGA Inference Acceleration

**Status:** STABLE
**Created:** 2026-05-16
**Last Updated:** 2026-05-20T08:00:00Z
**Research Cycle:** BUILD-104 / EXPLORE-213

## Overview

FPGA-based inference acceleration for edge AI workloads. Focus on sub-millisecond latency, 10-50W power envelopes, and deployment in distributed environments (RTUs, IoT gateways, sensor nodes). 2025-26 landscape shows paradigm shift toward ternary quantization, memory-based computation, and LLM deployment on FPGAs.

## Research Questions

1. ~~What is the current state of FPGA inference frameworks (Vitis AI, TVM, HLS4ML)?~~ — Completed
2. ~~How do FPGAs compare to ASICs (TPU, NPU) and GPUs for edge inference?~~ — Completed: ASU benchmarks
3. ~~What are the compilation and deployment workflows?~~ — Completed
4. ~~Which models have been successfully deployed on FPGAs at edge?~~ — Completed: expanded to LLMs
5. ~~What are radiation-hard FPGA use cases in high-energy physics?~~ — Completed: CERN/Fermilab

## Key Topics

### Vitis AI (AMD/Xilinx)
- Primary framework for FPGA AI inference
- Provides DPU (Deep Learning Processing Unit) overlay for FPGAs
- Supports Versal ACAP, Alveo cards, VCK5000
- Includes optimized IP cores, tools, libraries, pre-trained models
- Vitis AI 6.1 latest version (as of 2025)
- Inference server supports ZenDNN backend on AMD EPYC servers
- Use cases: edge devices, data center accelerators

**Benchmark Results (ASU ADVENT Lab, 2025)**:
- Tested on Kria KV260 (edge) and Alveo U55C (cloud)
- Models benchmarked: VGG19, VGG16, ResNet-152, ResNet-50, MobileNetV1, EfficientNet-b0, YOLOX-Nano
- Edge FPGA vs Edge TPU: **5.2x faster latency** on average for single-batch inference
- Edge FPGA energy efficiency: **17.3x better for MobileNet** vs Edge TPU, **4.19x average** across models
- Cloud TPUv3 vs Cloud FPGA: TPUv3 **1.37x faster** for batch-3 inference, but FPGA wins at small batches
- Key insight: FPGA excels at low-latency, low-batch, edge workloads; TPU dominates cloud-scale batched inference
- Setup complexity: Vitis AI noted as confusing with strict version dependencies and root access requirements

### HLS4ML (Open Source, Fermilab/CERN)
- High-level synthesis for ML on FPGAs
- Targets ultra-low latency (sub-microsecond) inference
- Supports PyTorch, scikit-learn, TensorFlow models
- Used at Fermilab, CERN, DESY for particle physics triggers
- Dataflow architecture with pipeline parallelism

**Radiation-Hard Deployment (CERN/Fermilab, Feb 2026)**:
- First demonstration of ML on radiation-hard FPGAs for high-energy physics
- PicoCal calorimeter test case for LHCb Upgrade II experiment
- Autoencoder compresses 32-sample waveforms → 320x compression ratio
- 25ns latency, enabling sub-microsecond trigger decisions
- HLS4ML rad-hard backend now open-source

### TVM (Apache)
- Hardware-aware compiler for FPGAs
- Custom hardware-aware optimization passes
- Latency: 100µs-1ms range
- Variable power consumption
- Medium setup complexity but high flexibility

### OpenVINO (Intel)
- Intel FPGA/CPU/GPU edge deployment
- 100µs-1ms latency
- 10-50W power envelope
- High ecosystem integration within Intel stack

## LLM Inference on FPGAs (2025-26)

### TerEffic (arXiv 2502.16473 — Peking University / NUS)
- Ternary-quantized LLM inference with 1.6-bit weight compression, specialized TMUs (ternary memory units), compute-memory alignment
- **149x higher throughput than NVIDIA Jetson Orin Nano at 19x power efficiency**
- 16,300 tokens/second for small models; **3x A100 throughput for 2.7B models at 46W**
- Fully on-chip execution for small models; HBM-assisted for larger ones
- Key innovation: hardware-algorithm co-design exploiting FPGA ternary MACs as add/subtract trees

### TeLLMe (ACM/IEEE companion to TerEffic)
- First table-lookup-based ternary LLM accelerator for low-power edge FPGAs
- 1.58-bit weights with 8-bit activations
- Full prefill AND autoregressive decode support

### LUT-LLM (arXiv 2511.06174 — UCLA / Microsoft Research Asia)
- **Paradigm shift**: shifts from arithmetic MACs to memory-based table lookups using FPGA BRAM
- 1.66x-2.16x faster inference vs conventional FPGA approaches
- First FPGA accelerator enabling **1B+ LLM** via vector-quantized memory operations
- Activation-weight vector co-quantization identified as most effective scheme
- Key insight: FPGAs abundant BRAM relative to DSP slices enables compute-to-memory inversion

### llama-fpga (GitHub — adamgallas, DATE25 / ICCAD25)
- World's first open-source FPGA LLM accelerator for **LLaMA2-7B AWQ 4-bit**
- Targets embedded and data center FPGAs
- Demonstrates reproducibility of LLM inference on commodity FPGA hardware

### Hummingbird+ (ACM DLaaS 25)
- First demonstration of FPGA-based edge product as practical LLM deployment medium
- Bridges research-to-production gap for FPGA inference

## Deployment Case Studies

### Edge AI (ASU ADVENT Lab, 2025)
- Kria KV260 board: 5.2x faster than Edge TPU, 4.19x better energy efficiency
- Best for: MobileNet, YOLOX-Nano at edge
- Limitation: Vitis AI setup complexity, documentation gaps
- Source: ARC_2025.pdf from ASU ADVENT Lab

### High-Energy Physics (CERN/Fermilab, 2026)
- Radiation-hard PolarFire FPGA: 25ns latency, 320x compression
- Use case: LHCb trigger system requiring sub-microsecond decisions
- Open-source contribution: HLS4ML rad-hard backend
- Source: arXiv:2602.15751, Feb 2026

### Industrial Edge (Cardiff University, 2025)
- PYNQ-Z1 FPGA deployment for heterogeneous ML pipelines
- HLS conversion for real-time sensor fusion
- Sub-millisecond latency for industrial monitoring
- Source: Mshragi2025_FPGA-accelerated-ML_AAM.pdf

## Framework Comparison

| Framework | Best For | Latency Range | Power | Setup Complexity |
|-----------|----------|---------------|-------|------------------|
| Vitis AI (AMD) | Commercial edge/cloud deployments | 100µs-1ms | 10-50W | High (strict deps) |
| HLS4ML | Scientific/ultra-low latency | 25ns-100µs | 5-30W | Medium (HLS expertise) |
| TVM FPGA | Custom hardware-aware optimization | 100µs-1ms | Variable | Medium (flexible but complex) |
| OpenVINO (Intel) | Intel FPGA/CPU/GPU edge deployment | 100µs-1ms | 10-50W | High (Intel ecosystem) |

## Key Insights

- **FPGA advantage**: reconfigurability vs. ASIC, efficiency vs. GPU power envelope
- **Key tradeoff**: FPGA excels at low-batch, low-latency edge workloads; TPU dominates cloud-scale batched inference
- **LLM frontier**: Ternary quantization + on-chip BRAM shifts make FPGAs viable for 1-7B parameter models at 40-50W
- **Compute-to-memory inversion**: LUT-LLM shows FPGA BRAM abundance enables table-lookup inference, flipping compute-bound paradigm
- **Ternary ops on FPGA**: Near-zero area cost for ternary MACs as add/subtract trees — unique FPGA advantage over GPUs

## Sources

- AMD/Xilinx Vitis AI documentation
- TVM FPGA backend papers (arXiv:1802.04799)
- HLS4ML GitHub and papers (FastML Team, 2025)
- Edge AI deployment case studies (2025)
- ASU ADVENT Lab: "Out-of-the-Box Performance of FPGAs for ML Workloads using Vitis AI" (2025)
- CERN/Fermilab: "Enabling Low-Latency Machine learning on Radiation-Hard FPGAs with hls4ml" (arXiv:2602.15751, Feb 2026)
- HLS4ML technical report: "A Flexible, Open-Source Platform for Deep Learning Acceleration on Reconfigurable Hardware" (arXiv:2512.01463, Dec 2025)
- Cardiff University: "FPGA-Accelerated Fast Machine Learning for Heterogeneous Edge" (2025)
- Oxford/IOP: "Roadmap on fast machine learning for science" (Feb 2026)
- TerEffic: "Highly Efficient Ternary LLM Inference on FPGA" (arXiv:2502.16473)
- LUT-LLM: "Efficient Large Language Model Inference with Memory-based Computations on FPGAs" (arXiv:2511.06174)
- llama-fpga GitHub (adamgallas, DATE25 / ICCAD25)
- Hummingbird+: "Advancing FPGA-based LLM Deployment from Research" (ACM DLaaS 25)
- TeLLMe: "An Energy-Efficient Ternary LLM Accelerator for FPGAs" (ACM/IEEE)

## Next Steps

- ~~Investigate oneAPI Intel FPGA support~~ — Completed: LUT-LLM TerEffic cover Intel/AMD FPGA backends
- ~~Explore HLS4ML backend for custom rad-hard FPGA targets~~ — Completed: CERN/Fermilab rad-hard documented
- ~~Monitor Vitis AI 7.0 release for improved developer experience~~ — Ongoing
- Track dynamic partial reconfiguration mid-inference for layer-adaptive FPGA acceleration
- Benchmark FPGA vs RISC-V NPU tradeoffs for same 1-7B parameter models
