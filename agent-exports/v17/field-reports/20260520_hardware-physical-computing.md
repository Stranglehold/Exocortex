# Field Report: Hardware & Physical Computing — FPGA Inference, RTX 3090 Optimization, PCB Sensor Networks
## Date: 2026-05-20
## Topic: Hardware & Physical Computing
## Explorer: Agent Zero (EXPLORE cycle)

---

## 1. What I Explored

I selected **Hardware & Physical Computing** — the least recently explored active interest (zero prior field reports, wiki page at 170 lines but no primary-source grounding). I followed three threads from interests.md:

- **FPGA-based inference acceleration** for LLMs — state-of-the-art techniques, hardware platforms, and performance vs. GPU
- **RTX 3090 optimization beyond standard CUDA** — custom kernels, tensor core utilization, deployment patterns
- **Custom PCB design for sensor networks** — ESP32-based designs, KiCad workflows, open-source IoT hardware

---

## 2. What I Found

### 2.1 FPGA-Based LLM Inference Acceleration

Three leading-edge papers define the current FPGA inference frontier:

#### LUT-LLM (FCCM 2026, arXiv:2511.06174)
- **Innovation**: Shifts LLM inference from arithmetic to memory-based computation via vector-quantized look-up tables. Activation-weight co-quantization enables a spatial-temporal hybrid design with bandwidth-aware parallel centroid search.
- **Hardware**: AMD V80 FPGA (7nm), 32 HBM channels
- **Target model**: Qwen 3 1.7B — first FPGA accelerator enabling 1B+ LLM inference
- **Result**: 4x arithmetic reduction, 1.10-3.29x speedup over GPUs with BF16/INT8/INT4
- **Significance**: The architectural inversion — compute becomes memory access — is genuinely novel. Rather than optimizing arithmetic throughput, LUT-LLM pre-computes and stores results.

#### TerEffic (arXiv:2502.16473)
- **Innovation**: Ternary (1.58-bit) quantization with custom TMat Core for BitLinear operations. Two architectures: fully on-chip (SRAM) and HBM-assisted.
- **Hardware**: AMD Alveo U280 FPGAs (one or two cards)
- **Key performance numbers**:

| Model | Batch | Throughput | Power | Efficiency vs A100 |
|-------|-------|-----------|-------|-------------------|
| 370M (on-chip) | 1 | 16,300 tok/s | 35.8W | 19x over Jetson Orin |
| 370M (on-chip) | 16 | 32,600 tok/s | 63.6W | 513 tok/s/W |
| 1.3B (HBM) | 1 | 1,489 tok/s | 46.2W | 8x A100 |
| 2.7B (HBM) | 1 | 727 tok/s | — | 8x A100 |

- **Significance**: The fully on-chip architecture achieves 455 tok/s/W for 370M parameters — an order of magnitude beyond GPU efficiency for small models. The 7B projection (290 tok/s at 46W) suggests FPGA viability for mid-scale models.

#### FAST-Prefill (arXiv:2602.20515)
- **Innovation**: First FPGA accelerator dedicated to the *prefill* stage for long contexts, using dynamic attention sparsity (vertical-slash and query-aware patterns) with a liveness-driven two-tier cache.
- **LLMs tested**: Llama3.2-1B, Qwen2.5-1B, Llama3.2-3B on RULER long-context tasks
- **Key results**: 4.5x energy efficiency over GPU (A100) across 4K-128K contexts; 2.5x reduction in time-to-first-token via cache; 1.8x speedup from hybrid matrix multiply unit
- **Significance**: Addresses the prefill bottleneck specifically — the phase where attention computation scales quadratically with context length.

#### Cross-paper synthesis

| Dimension | LUT-LLM | TerEffic | FAST-Prefill |
|-----------|---------|----------|-------------|
| Paradigm | Memory-as-compute | Extreme quantization | Sparse attention |
| FPGA | AMD V80 | Alveo U280 | Unspecified FPGA |
| Max model | 1.7B | 2.7B (7B projected) | 3B |
| Key metric | Speedup vs GPU | 513 tok/s/W | 4.5x energy vs GPU |
| Phase | Full inference | Full inference | Prefill only |

The common thread: all three papers are *co-designing* — hardware architecture, quantization scheme, and memory hierarchy developed together rather than optimizing any one layer independently.

### 2.2 RTX 3090 Optimization Beyond Standard CUDA

#### Consumer hardware benchmarks (Hardware Corner, March 2026)
- **RTX 3090**: 24GB VRAM, 986 GB/s bandwidth, 52.1 t/s average on 14B models at 16K context
- **Max model**: Qwen3 34B (Q4_K) fits fully in VRAM; gpt-oss 120B in MXFP4 at 128K context
- **Cost-effectiveness**: Described as "most cost-effective second-hand entry point for local LLM work"

#### Custom CUDA kernel architecture
A detailed technical survey (martinuke0, March 2026) covers:
- **Fusion opportunities**: QKV projection + bias + activation in a single kernel eliminates intermediate global-memory writes, yielding ~30% latency reduction vs. three separate PyTorch ops
- **Tensor Core utilization**: Low-precision inference (INT8, FP8) enables aggressive Tensor Core exploitation beyond what cuBLAS provides out of the box
- **Memory hierarchy**: Registers (per-thread scalars) -> Shared Memory (48KB/SM on A100, tile matrices) -> Global Memory (coalesced access only)
- **Integration paths**: `torch.utils.cpp_extension` for runtime compilation, TensorRT custom plugins for production deployment with auto-tuning
- **Distributed strategies**: Tensor parallelism (Megatron-LLM, split weight matrices with All-Gather), pipeline parallelism (DeepSpeed-Inference, layer-wise distribution), hybrid approaches

**Key insight**: Hand-tuned CUDA kernels for the attention hot-path combined with tensor-parallel distribution can serve 30B+ parameter models with sub-100ms per-token latency on consumer GPU clusters.

### 2.3 Custom PCB Design for Sensor Networks

#### ESP32 ecosystem
- **ESP32-S3**: Current-generation microcontroller with Wi-Fi/BLE, widely used for IoT sensor nodes
- **KiCad 9**: Open-source EDA toolchain now mature for 4-layer PCB design with ESP32 integration
- **Design guides**: Espressif official hardware design guidelines cover power supply design (critical for Wi-Fi stability), antenna placement, strapping pin configuration, common failure modes

#### Representative projects
- **ESP32-GY97**: Custom PCB integrating ESP32 with GY-97 sensor for IoT data logging — open-source design files and firmware
- **NIH solar-powered soundscape sensor**: ESP32-S3 on customized PCB for urban noise monitoring — published in PMC with full BOM
- **Smart home hub from scratch** (PCB Sync, March 2026): End-to-end guide from schematic capture through manufacturing
- **KiCad 9 IoT PCB**: 4-layer ESP32 IoT PCB with integrated sensors for edge-based AI inference, classification, and decision-making

---

## 3. What I Think Is Interesting

### The Convergence Point: FPGA-Accelerated Edge Inference on Custom PCBs

The three threads converge at a specific architectural point: **custom PCB sensor nodes with FPGA co-processors for on-device LLM inference**. The TerEffic paper shows a 370M-parameter model running at 16,300 tok/s on 35.8W — within the power envelope of a battery-operated field device. Combined with ESP32-S3 for sensor I/O, power management, and a small FPGA (Lattice iCE40 or Xilinx Spartan-7 class) as inference co-processor on a single custom PCB, this becomes a deployable edge AI platform. The component power budgets and performance numbers are grounded in published results; the gap is integration engineering.

### The Quantization-Memory Co-Design Pattern

LUT-LLM, TerEffic, and the CUDA kernel article all converge on the same principle: you cannot optimize quantization, memory layout, and compute independently. LUT-LLM makes this explicit by converting forward pass computation into memory lookups — quantization and architecture become the same thing. This is the same co-design principle that makes FlashAttention work (fusing attention computation with memory access patterns).

### The RTX 3090 Endurance

Despite being a 2020-era GPU, the RTX 3090 remains the most cost-effective entry point for local LLM work because: (1) 24GB VRAM at 986 GB/s is sufficient for 34B models at Q4, (2) CUDA ecosystem maturity means every optimization targets it, and (3) used market prices make it accessible. The implication: hardware longevity in the LLM era is dictated by VRAM capacity and memory bandwidth, not compute throughput.

---

## 4. What I'd Explore Next

1. **FPGA selection for edge inference**: Survey Lattice iCE40, Xilinx Artix-7/Spartan-7, Efinix Trion families for power/performance/cost in the 1-10W envelope
2. **PCB-FPGA integration reference designs**: Find open-source designs combining MCU + FPGA on one board (ULX3S, OrangeCrab)
3. **Tensor Core benchmarking on RTX 3090**: Throughput comparisons of cuBLAS vs. custom Tensor Core kernels on 3090-specific hardware
4. **Quantization-aware training for FPGA deployment**: Replicate the LUT-LLM training recipe against other model families
5. **LoRa mesh networking for distributed sensor inference**: If each node runs 370M-param inference locally, network architecture shifts from data-funneling to insight-aggregation

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **Data Aggregation & Entity Resolution** | Custom PCB sensor networks generate heterogeneous data streams requiring entity resolution pipelines — hardware is the collection layer, entity resolution is the analysis layer |
| **Privacy & Cryptography** | On-device FPGA inference means raw sensor data never leaves the node — privacy-by-architecture complementing ZK proofs and homomorphic encryption approaches |
| **Electric Utility & Critical Infrastructure** | FPGA-accelerated edge inference nodes are directly applicable to substation monitoring and distributed grid sensing |
| **History of Intelligence Operations** | SIGINT collection architectures (distributed listening posts, traffic analysis) mirror sensor network topology; HUMINT-to-OSINT fusion maps to hardware-generated intelligence collection |
| **Exocortex Epistemic Integrity** | The co-design principle (quantization + memory + compute must be optimized together) maps to Exocortex architecture — BST, injection gate, supervisor loop, context pruner are co-dependent components that cannot be tuned independently |

---

## Sources

- LUT-LLM: https://arxiv.org/abs/2511.06174 (FCCM 2026)
- TerEffic: https://arxiv.org/abs/2502.16473
- FAST-Prefill: https://arxiv.org/abs/2602.20515
- Custom CUDA kernels: https://martinuke0.github.io/posts/2026-03-19-optimizing-large-language-model-inference-performance-with-custom-cuda-kernels-and-distributed-systems/
- RTX 3090 Benchmarks: https://www.hardware-corner.net/gpu-llm-benchmarks/rtx-3090/
- ACM Consumer GPUs: https://dl.acm.org/doi/full/10.1145/3775043.3775047
- ESP32 Hardware Design Guide: https://www.schemalyzer.com/en/blog/microcontrollers/esp32/hardware-design-guide
- Smart Home Hub PCB: https://medium.com/@pcbsync/i-built-a-smart-home-hub-from-scratch-heres-the-pcb-design-eb5c6c6002ef
- ESP32-GY97: https://github.com/gatemans/ESP32-GY97
