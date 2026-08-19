# TinyML & Edge Inference on Constrained Hardware

**Status:** STABLE
**Created:** 2026-05-21
**Last updated:** 2026-05-22
**Cross-links:** [fpga-inference-acceleration](fpga-inference-acceleration.md), [risc-v-ai-acceleration](risc-v-ai-acceleration.md), [in-sensor-near-sensor-ai-computing](in-sensor-near-sensor-ai-computing.md), [federated-learning-production](federated-learning-production.md), [triton-kernels-rtx-optimization](triton-kernels-rtx-optimization.md), [edge-ai-substation-deployment](edge-ai-substation-deployment.md)

## Overview

### TinyML vs TinyDL Taxonomy (ACM CS 2026)

ACM Computing Surveys 10.1145/3776588 (2026, 200+ sources) establishes a formal taxonomy distinguishing **TinyML** (traditional ML: linear models, decision trees, SVMs on <256 KB RAM) from **TinyDL** (deep neural networks on MCUs requiring quantization-aware training and hardware accelerators). Boundary: models exceeding 50 KB that exploit dedicated NPU/DSP units. This distinction matters because TinyDL introduces new failure modes — attention mechanism quadratic memory scaling, layer normalization numerical instability at INT8, and activation range explosion in sub-8-bit regimes.

### Hardware Evolution (2025-2026)

Shawn Hymel's 2026 state-of-edge-AI survey documents a shift from general-purpose MCU acceleration toward **selective acceleration**: vendors add DSP extensions, small neural processing blocks, and tighter memory coupling for common ML ops while preserving low power consumption. Key finding: **hybrid NPU+CPU fallback is the norm** — when a model fits NPU constraints, latency/energy gains are substantial; when it doesn't, inference falls back to optimized CPU/DSP execution. Pure NPU-only designs remain rare outside Application-Specific NPUs like BrainChip Akida.

### Scope

Running AI inference on microcontrollers (MCUs), embedded systems, and ultra-low-power devices. Focus: sub-watt deployment, quantization-aware training, TensorFlow Lite Micro (TFLM), ONNX Runtime Edge, MCU-class hardware (ARM Cortex-M, RISC-V E/RV32), and the quantization-pruning-distillation accuracy-latency-power Pareto surface.

## Quantization Methods & Accuracy Tradeoffs

### Post-Training Quantization (PTQ)
- **INT8 PTQ** is the practical standard for MCUs. Accuracy retention typically 95-99% of FP32 baseline for well-conditioned models (MobileNetV2, ResNet-18, keyword spotting models).
- **DTU 2026 quantization toolchain survey** (orbit.dtu.dk, May 2026) catalogs PTQ support across 12 embedded AI toolchains: TFLite Micro, ONNX Runtime Edge, Arm NN, CMSIS-NN, TensorFlow Lite for Microcontrollers, Apache TVM, RKNN, TPU-MLIR, OpenVINO, TensorRT, CoreML, and PyTorch ExecuTorch. Key finding: only 7 of 12 support asymmetric affine quantization natively; 4 lack sub-8-bit PTQ entirely.
- On RISC-V GAP9 devices: healthcare classification 98.5% accuracy with INT8 PTQ; Human Activity Recognition (HAR) 91.04-98.29% accuracy.
- On MAX78000/78002 NPU platforms: audio classification 94.87%, DSP applications 96.9-99.0%, environmental monitoring 79.67-86.53% F1-score.

### Quantization-Aware Training (QAT)
- QAT integrates simulated quantizers into the training graph, enabling the network to learn to compensate for rounding and range effects.
- Enables viable 4-bit operation across diverse architectures and hardware backends, where PTQ at 4-bit typically fails catastrophically.
- On STM32H7: hardware-aware mixed-precision MobileNetV2 achieved 68.4% accuracy (top-1 ImageNet).

### Mixed-Precision & Sub-8-Bit
- Mixed-precision (layer-wise or weight/activation asymmetry) preserves accuracy where uniform INT8 degrades.
- Sub-8-bit (INT4, INT2) viable only with QAT + calibration datasets representative of deployment distribution.
- Power-of-Two (PoT) quantization emerging for hardware compliance on NPUs lacking full INT arithmetic.

## Hardware Platforms Benchmarked

| Platform | Architecture | Inference Task | Power | Latency | Energy |
|----------|-------------|----------------|-------|---------|--------|
| GAP9 (RISC-V) | Dual-core + NPU | Object detection | 54 mW | 56.45 ms | ~3.05 mJ |
| GAP9 (RISC-V) | Dual-core + NPU | Healthcare classification | 30.6 mW | 61 ms | ~1.87 mJ |
| GAP9 (RISC-V) | Dual-core + NPU | Human Activity Recognition | — | 1.11-1.93 ms | 35-62 \u03bcJ |
| MAX78000/78002 | Hybrid NPU | Audio classification | — | 104 \u03bcs | 5 \u03bcJ |
| MAX78000/78002 | Hybrid NPU | Healthcare classification | 18 mW | 248 \u03bcs | ~4.46 \u03bcJ |
| MAX78000/78002 | Hybrid NPU | Environmental monitoring | — | 4-27.5 ms | 0.885-4.275 mJ |
| STM32H7 (ARM Cortex-M7) | CPU-only | MobileNetV2 classification | ~150 mW | ~200 ms | ~30 mJ |

*Data from arXiv 2508.15008 survey, cross-referenced with MLPerf Tiny V1.1 results.*

## Framework Comparison

### TensorFlow Lite Micro (TFLM)
- **Dominant** in TinyML ecosystem. Mature support for Cortex-M and ESP32.
- Preallocated memory arena prevents fragmentation. Operator resolver minimizes binary size.
- **Limitations:** No on-device training support. Static memory constraints. Limited dynamic shape support.
- 2024 MLPerf Tiny: TFLite achieves 3-5x efficiency gains over unoptimized baselines.

### ONNX Runtime Edge
- Cross-platform inference engine with graph-level optimizations.
- Modular hardware accelerators via Execution Providers.
- Supports models from PyTorch, TensorFlow, scikit-learn.
- **Advantage:** Greater adaptability for modern quantization and hardware delegation.
- **Limitation:** Larger binary footprint than TFLM for MCU-class devices.

### CMSIS-NN (ARM)
- Foundational optimized kernel library for ARM Cortex-M processors.
- Leverages SIMD-like instructions for 8-bit and 16-bit fixed-point arithmetic.
- **Limitation:** ARM-locked. No native mixed-precision or sub-byte support.

## MLPerf Tiny Benchmark

- First industry-standard benchmark suite for ultra-low-power ML inference.
- Four benchmarks: keyword spotting (KWS), visual wake words (VWW), image classification, anomaly detection.
- Target devices: 10-250 MHz, <50 mW power envelope.
- Measures accuracy, latency, and energy per inference.
- **MLPerf Tiny v1.3 (2025):** Introduces new streaming benchmark addressing hardware/software heterogeneity. Overcomes fragmentation across microcontrollers, custom accelerators, and specialized processors. Adds real-time performance metrics (arXiv 2509.04721 benchmarks identical TFLite configurations across platforms).

## Accuracy-Latency-Power Pareto

The Pareto frontier varies by application domain:
- **Healthcare/medical:** Accuracy prioritized (98%+). Latency acceptable at 100+ ms. Power constrained to <50 mW.
- **HAR/activity recognition:** Latency critical (<2 ms). Energy per inference <100 \u03bcJ. Accuracy 90%+ acceptable.
- **Keyword spotting:** Balanced. 95%+ accuracy, <20 ms latency, <5 mW average power.
- **Drone navigation/real-time control:** Latency critical (<10 ms). Accuracy 85%+ acceptable. Power <100 mW.

## Integration with Existing Research

- **FPGA inference acceleration** (fpga-inference-acceleration.md): FPGA-based inference complements MCU TinyML by bridging the gap between CPU-only inference and dedicated NPUs. Vitis AI and HLS4ML enable custom accelerator designs for specific quantized models.

- **RISC-V AI acceleration** (risc-v-ai-acceleration.md): RVV 1.0 vector extensions directly benefit TinyML on RISC-V MCUs. GAP9 and GAP8 leverage vector units for DNN acceleration. 59.3x TinyML speedup reported with RVV 1.0 (arXiv 2511.21232).

- **In-sensor computing** (in-sensor-near-sensor-ai-computing.md): Near-sensor processing represents the extreme edge of TinyML — inference happening at or within the sensor itself. Sony IMX500 achieves 1,360 MMAC/J vs STM32N6 21 MMAC/J (63x gap).

- **Federated learning** (federated-learning-production.md): FL enables distributed TinyML training across edge devices without centralizing data. FedProx and FedBN handle non-IID data common in sensor networks. Privacy-preserving HE-based SecAgg relevant for medical IoT.

- **Triton kernels** (triton-kernels-rtx-optimization.md): Custom kernel optimization principles transfer from GPU to MCU — operator fusion, memory access patterns, and compute-bound vs memory-bound analysis apply at all scales.

## Primary Sources (Verified)

1. arXiv 2508.15008 — "Neural Network Quantization for Microcontrollers: A Comprehensive Survey" (2025)
2. arXiv 2505.15622 — "Benchmarking Energy and Latency in TinyML" (2025)
3. MLPerf Tiny V1.1 Results — mlcommons.org/benchmarks/inference-tiny/
4. ACM Computing Surveys 10.1145/3776588 — "From Tiny Machine Learning to Tiny Deep Learning" (2026)
5. arXiv 2603.11071 — "TinyNav: End-to-End TinyML for Real-Time Autonomous Navigation" (2026)
6. Nature s41598-025-27818-9 — "Deploying TinyML for energy-efficient object detection" (2025)
7. DTU Technical Report — "From Models to Microcontrollers: TinyML Tools, Techniques, and Strategies" (May 2026)
8. arXiv 2509.13786 — "Efficient Quantization-Aware Neural Receivers" (2025)
9. arXiv 2506.18927 — "From Tiny Machine Learning to Tiny Deep Learning: A Survey" (2026, 200+ sources)
10. MLPerf Tiny v1.3 Tech Report (Sep 2025) — mlcommons.org/2025/09/mlperf-tiny-v1-3-tech/
11. arXiv 2509.04721 — "Real-Time Performance Benchmarking of TinyML Models" (Sep 2025)
12. Shawn Hymel 2026 — "State of Edge AI on Microcontrollers in 2026" (shawnhymel.com, Jan 2026)
13. arXiv 2603.23668 — "Energy-Efficient Software–Hardware Co-Design for Machine Learning" (Mar 2026)
14. IEEEXplore 10022821 — "Sub-8-Bit Quantization for On-Device Speech Recognition" (2022/2023)
15. Springer s44291-026-00186-y — "Perpetual edge intelligence: adaptive hybrid energy harvesting" (Mar 2026)

## Production Deployment Gap Analysis

| Dimension | Research State | Production Reality |
|-----------|---------------|-------------------|
| Quantization | INT8 PTQ/QAT standard; sub-8-bit research active | INT8 PTQ is production-ready; INT4 requires hardware-specific support |
| Toolchain Maturity | DTU survey: 7/12 support asymmetric affine natively | TFLite Micro and CMSIS-NN are mature; ONNX Runtime Edge still evolving |
| Power Measurement | MLPerf Tiny v1.3 provides standardized benchmarks | Real-world power profiles vary 3-5x vs lab conditions due to I/O overhead |
| Model Accuracy | 95-99% INT8 retention for well-conditioned models | Edge cases (long-tail inputs) show larger accuracy drops; need robust calibration |
| On-Device Training | GEPA-style prompt evolution, continual learning research | Rarely deployed; most edge deployments use static models with cloud retraining |
| Security/Privacy | Homomorphic encryption, TEE integration explored | PQC (ML-KEM) MCU implementations available but not yet integrated into TinyML toolchains |
| Multi-Model Orchestration | Single-model inference well-studied | Multi-model pipelines on MCUs (sensor fusion + classification + control) lack standardized frameworks |

## Critical Gaps

1. **Sub-8-bit production readiness**: INT4 and binary quantization show promise in research but lack mature toolchain support and hardware accelerators outside specialized NPUs.
2. **Continual learning at edge**: On-device model adaptation remains largely experimental; catastrophic forgetting and memory constraints are unresolved.
3. **Security integration**: TinyML deployments in critical infrastructure need PQC-secured model updates and integrity verification — not yet integrated into toolchains.
4. **Multi-modal edge inference**: Combining audio, visual, and sensor data on MCUs lacks standardized frameworks beyond simple concatenation.
5. **Calibration robustness**: PTQ calibration sensitivity to distribution shift at deployment time is under-studied.

## Cross-Domain Links

- **Entity resolution:** TinyML enables on-device entity matching for privacy-preserving AML/OFAC screening at the edge.
- **Adversarial ML:** Quantized models on MCUs show varying robustness to adversarial attacks — INT8 provides some natural defense through discretization, but 4-bit models are more vulnerable.
- **Post-quantum critical infrastructure:** PQC algorithms (ML-KEM) have MCU implementations relevant to TinyML devices in critical infrastructure.
- **Autonomous self-improving agents:** On-device model adaptation (continual learning) extends TinyML beyond static inference.
- **Memory architecture:** TinyML deployment exposes the limits of working memory (KB-scale RAM) and the need for efficient weight caching strategies.
- **Neuromorphic computing:** BrainChip Akida and Intel Loihi 2 represent alternative hardware paradigms for ultra-low-power inference that compete with traditional MCU+TFLM approaches.
