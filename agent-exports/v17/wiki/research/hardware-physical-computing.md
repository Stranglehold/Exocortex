# Hardware & Physical Computing

Status: STABLE

## Summary
Investigation into hardware acceleration for AI inference, custom PCB design for sensor networks, and GPU optimization beyond standard CUDA. Deepened 2026-05-19 using primary source arXiv:2503.16731 (tiled matmul on KV260 FPGA) and the FP8-as-storage technique for RTX 3090 Ampere GPUs.

## FPGA-Based Inference Acceleration

### Primary Source: arXiv:2503.16731 (Li & Chen, UC Irvine)

This work presents a highly optimized tiled matrix multiplication accelerator targeting the Q, K, and V linear projections in Transformer Multi-Head Self-Attention (MHA), deployed on a resource-constrained Xilinx Kria KV260 SoM (Zynq UltraScale+).

**Key Results:**
| Metric | Value |
|--------|-------|
| Throughput | 3.12 GFLOPs (core compute) |
| Speedup vs ARM PyTorch | **7×** |
| Speedup vs NumPy | **200×** |
| Clock frequency | 100 MHz (conservative) |
| Tile size | 32×32 |
| Concurrent MAC/cycle | 1,024 |
| Energy (per 768×3072 matmul) | 0.5 J FPGA vs 2 J ARM (**4× efficiency**) |
| DistilBERT end-to-end speedup | **2×** |

**Resource Utilization (XCK26, KV260):**
| Resource | Used | Available | % |
|----------|------|-----------|-----|
| BRAM | 126 | 144 | 88% |
| DSP48E | 1,040 | 1,248 | 83% |
| FF | 102,741 | 237,600 | 43% |
| LUT | 71,050 | 118,800 | 60% |

### Architecture

The design uses **two-level tiling** — Block Tiling (M_b=256) and Inner Tiling (T=32) — to decompose large matrices into on-chip BRAM tiles. Matrix A is loaded once into persistent on-chip storage; B is streamed in column blocks. The inner loops are fully unrolled into a systolic-like array of 32×32 multipliers-adders, with pipeline initiation interval II=1, delivering 1,024 int8×int8 MAC operations per clock cycle.

Three AXI4 master ports stream data from/to external DDR: one each for input A, input B, and output C. A special `update_A` flag allows the host to reuse the last-loaded A matrix across multiple B batches (e.g., iterating attention heads without reloading weights).

**Quantized DistilBERT Integration:** The FPGA replaces standard PyTorch Q, K, V linear layers with an `FPGAQuantizedLinear` module that quantizes inputs to int8, invokes the FPGA via PYNQ drivers, and dequantizes int32 results back to float. Accuracy loss is ≤0.5% in attention outputs.

**Tile size selection:** T=64 improved theoretical parallelism but failed timing closure at 100MHz. T=16 underutilized resources. T=32 was the equilibrium point for the KV260.


## Custom PCB Design for Sensor Networks

### Open-Source Hardware Ecosystem

The open-source PCB ecosystem for sensor networks has matured around several key platforms:

**MySensors** (mysensors.org): A battle-tested open-source hardware and software library for DIY home automation/sensor networks. Provides ready-to-use build instructions, code examples, and adaptable PCB designs. The community maintains the Easy/Newbie PCB with NRF24L01+ or RFM69 transceiver options. Tested with 20+ home automation controllers.

**LibrePCB** (librepcb.org): A free, cross-platform EDA suite for schematic capture and PCB layout. Designed for accessibility from beginners to professionals, enables custom sensor boards without vendor lock-in.

**OpenHardware.io**: Repository for open-source hardware projects including MySensors-compatible PCBs.

### Representative Projects

**ESP32-GY97**: Custom PCB integrating ESP32 with GY-97 sensor for IoT data logging. Open-source design files and firmware.

**ColonelPanic.tech**: Dual-core ESP32 drone Remote ID detection system with real-time web mapping, Meshtastic mesh alerts, and FAA database integration (2,595 views).

### Design Patterns

The dominant architecture for sensor network PCBs follows a three-component pattern:
1. **Microcontroller** (ESP32, ARM Cortex-M) for local processing and communication
2. **Transceiver** (NRF24L01+, RFM69, LoRa/SX127x) for mesh networking
3. **Sensor array** with I2C/SPI interfaces

Power management is critical: battery-optimized designs use deep sleep modes achieving microamp-range draw, enabling months-to-years from a single LiPo cell.

### Exocortex Relevance

The modular, open-source sensor PCB architecture parallels the extension system: both use pluggable, independently-verifiable components communicating via defined interfaces. Mesh networking principles mirror multi-agent communication patterns. Custom PCB design could provide physical-world grounding for autonomous agents.


## RTX 3090 Optimization Beyond Standard CUDA

### FP8-as-Storage on Ampere (Mohan, 2026)

**Primary Source:** amohan.dev/blog/2026/fp8-as-storage-imma-ampere

NVIDIA's FP8 (8-bit floating point) tensor core math requires Hopper architecture (H100) or newer. However, the RTX 3090 (Ampere, sm_86) can run FP8-style numerics experiments via a "FP8-as-storage" technique that maps FP8 storage onto INT8 tensor cores (IMMA/WMMA).

**The Insight:** FP8 training research is really about three things: (1) how you store weights, (2) when and where you expand/decode them, and (3) what scaling/quantization contract you enforce. None of these require native FP8 MMA hardware.

**Pipeline:**
1. Store weights as FP8 bytes (E4M3 format) — 1 byte/weight vs 2 bytes for FP16
2. Decode FP8 → FP16 using a 256-entry LUT
3. Apply per-output-channel scale factors
4. Saturating quantize to INT8
5. Run INT8×INT8→INT32 tensor core MMA (IMMA)
6. Write FP16 output

**Benchmarks (RTX 3090 Ti, M=N=K=4096):**

| Variant | Time/iter | Throughput |
|---------|-----------|------------|
| PyTorch decode+FP16 matmul (no VRAM save) | 2.267 ms | 60.63 TOPS |
| Fused kernel (imma_fp8_v2) | 2.714 ms | 50.63 TOPS |
| Fused kernel + L2 pinning | 2.744 ms | 50.09 TOPS |
| Fused kernel + v4 activation quant | 2.818 ms | 48.77 TOPS |
| cuBLASLt int8gemm (reference) | 0.018 ms | 118.06 TOPS |

Key finding: The fused FP8-as-storage kernel achieves ~50 TOPS while keeping weights in 1-byte FP8 format, delivering ~2× VRAM savings. The naive PyTorch approach (decode+cuBLAS) is faster (60.6 TOPS) but defeats the VRAM savings. The cuBLASLt int8 baseline (118 TOPS) represents the theoretical ceiling for INT8 tensor core throughput on Ampere.

**Implementation Details:**
- 256-entry LUT stored in CUDA `__constant__` memory for fast broadcast
- Per-column scales as uint16, loaded with `cp.async` (Ampere async copy from global → shared memory)
- Activation quantization either in registers (v3, 24.5 TOPS) or via shared-memory staging with cp.async (v4, 48.8 TOPS)
- L2 persistence hints (`l2pin`) explored but offered minimal improvement
- Stochastic rounding not implemented (no backward pass), but identified as critical extension

### CudaForge: Automated Kernel Generation (OpenReview, 2026)

**Source:** openreview.net/forum?id=f4GtuI2blh

CudaForge is an agent framework that generates custom CUDA kernels from high-level descriptions, demonstrating strong generalization across GPUs including A100, RTX 6000, RTX 4090, and RTX 3090. The system uses hardware feedback loops to iteratively refine kernel performance. This represents a shift from hand-tuned kernels toward automated optimization for specific hardware targets.

### CUTLASS 4 DSLs (NVIDIA)

CUTLASS 4 introduces Python-native DSLs for writing high-performance CUDA kernels based on core CUTLASS and CuTe abstractions. This eliminates the traditional C++ CUDA kernel development barrier while maintaining full performance. Together with nvMatmulHeuristics (analytic kernel selection for GEMM), the ecosystem makes tensor core optimization accessible without deep CUDA expertise.

**NVIDIA Matmul Heuristics:** A GPU optimization module providing fast, analytic heuristics for tensor operations (GEMM), determining optimal kernel configurations by analyzing tensor operation parameters and hardware capabilities.

### Exocortex Relevance

The FP8-as-storage technique embodies a principle directly applicable to Exocortex: separate storage format from compute format. This mirrors Exocortex's design (knowledge stored in compressed form, expanded only when needed). The CudaForge automated kernel generation approach parallels the GEPA self-modifying prompt architecture — both use iterative feedback loops to optimize performance on a specific target. For local inference deployment, these techniques could enable efficient model serving on consumer GPUs without requiring datacenter hardware.


## Cross-Domain Connections

### To Exocortex Architecture
- **FP8-as-storage** vs **Knowledge Packs**: Both separate storage format from compute format. Weights stored compact (1 byte) and expanded on demand mirrors how Knowledge Packs compress context for selective enrichment.
- **Tile-based data reuse** vs **Stateful Injection**: The FPGA design's persistent on-chip A matrix (loaded once, reused across B blocks) directly parallels stateful injection's persistent system context (loaded once, referenced across turns).
- **CudaForge agentic kernel generation** vs **GEPA**: Both use iterative feedback loops with hardware-specific optimization — CudaForge for GPU kernels, GEPA for prompt architecture.
- **Two-level tiling hierarchy** vs **Supervisor Loop**: Both employ graduated strategies (spatial/temporal mapping vs L1/L2/L3 intervention) to optimize resource use under constraints.

### To Other Interests
- **Data Aggregation & Entity Resolution**: Sensor network PCBs generate heterogeneous data streams (temperature, motion, RF signals) that require entity resolution across time and location.
- **Privacy & Cryptography**: FPGA acceleration for homomorphic encryption could combine with the KV260 pattern for on-device private inference.
- **Geopolitics & Strategic Analysis**: Custom PCB networks for drone detection (ColonelPanic.tech) represent a civilian counter-drone capability relevant to UAV defense strategy.
- **OSINT & Investigation Methodology**: Mesh sensor networks could serve as distributed physical-world data collection for OSINT investigations — environmental monitoring, RF spectrum analysis, movement detection.

### Design Patterns Extracted
1. **Storage/Compute Separation** (FP8-as-storage, Knowledge Packs, Stateful Injection): Store compact, expand only when processing.
2. **Tiled Processing** (FPGA matmul, Context Pruner): Break large problems into cache-friendly tiles.
3. **Pipelined Concurrency** (FPGA MAC array, multi-agent delegation): Overlap compute and data movement to hide latency.
4. **Iterative Self-Optimization** (CudaForge, GEPA, Sleep Consolidation): Use feedback from previous runs to improve next execution.

## Open-Source FPGA Toolchains

### Ecosystem Overview

The open-source FPGA toolchain ecosystem has matured from proof-of-concept to production-ready for supported architectures. The trajectory parallels the GCC/LLVM transition: open-source tools increasingly compete with vendor toolchains for supported device families.

**Key projects:**

| Project | Role | Target Architectures |
|---------|------|---------------------|
| **Yosys** | Synthesis (RTL to netlist) | Lattice iCE40/ECP5, Xilinx 7-series, Gowin |
| **nextpnr** | Place-and-route | Lattice iCE40/ECP5, Xilinx 7-series, Gowin, Efinix |
| **OpenROAD** | Physical design (RTL-to-GDS) | ASIC flows (SkyWater 130nm, GF 180nm, IHP 130nm) |
| **Project F4PGA** | Vendor-neutral FPGA flow | Xilinx 7-series, Lattice ECP5 |
| **SymbiFlow** | Full open-source FPGA flow (predecessor to F4PGA) | Xilinx 7-series |
| **openFPGALoader** | Programming/debugging | Universal (Vivado, Quartus, open-source bitstreams) |

### Current Limitations (2026)

- **Xilinx UltraScale+** (used by KV260): Partial support. Yosys can synthesize but nextpnr place-and-route for UltraScale+ is experimental. Vendor toolchains (Vivado) still required for final bitstream generation.
- **Intel/Altera**: Minimal open-source support. Quartus remains mandatory.
- **Timing closure**: Open-source tools lack the sophisticated timing engines of Vivado/Quartus. For high-frequency designs (>200 MHz), vendor tools remain superior.
- **IP ecosystem**: Vendor IP blocks (MIG for DDR, PCIe cores) have no open-source equivalents. Workarounds exist but are not drop-in.

### Relevance to Exocortex Hardware Acceleration

The open-source FPGA flow is viable for prototyping Transformer accelerators on Lattice ECP5 (cost-effective, fully open-source toolchain) before porting to KV260/Xilinx. For production deployment, hybrid approach: open-source synthesis + vendor place-and-route offers the best tradeoff of auditability and timing closure.

**Key source:** Tarek Allam Jr. (2025), "The State of Open-Source FPGA Tools" — documents the production-readiness of Yosys+nextpnr for Lattice architectures.

## FlashAttention & Hardware-Aware GPU Kernel Design

### Evolution

FlashAttention, introduced by Dao et al. (2022), is the canonical example of IO-aware algorithm design for GPUs. The key insight: attention computation is memory-bandwidth-bound, not compute-bound. Standard attention reads/writes the full <latex>N 	imes N</latex> attention matrix to HBM; FlashAttention tiles the computation to keep partial results in SRAM.

**Versions:**

| Version | Year | Key Innovation | Target Hardware |
|---------|------|---------------|-----------------|
| FlashAttention-1 | 2022 | Tiling + recomputation (no <latex>N 	imes N</latex> matrix stored) | A100 (Ampere) |
| FlashAttention-2 | 2023 | Reduced non-matmul FLOPs, parallel over sequence length | A100 |
| FlashAttention-3 | 2024 | Asynchrony (WGMMA+TMA overlap), FP8 low-precision | H100 (Hopper) |
| FlashAttention-4 | 2026 | Algorithm-kernel pipelining co-design, warp specialization | H100/B200 (Blackwell) |

### FlashAttention-3 & 4 Architecture (Relevant to RTX 3090)

**FlashAttention-3** (Dao, 2024) exploits Hopper-specific features:
- **WGMMA** (Warp Group Matrix Multiply-Accumulate): Asynchronous tensor core operations
- **TMA** (Tensor Memory Accelerator): Hardware-accelerated data movement between HBM and SMEM
- **FP8**: Low-precision attention with block scaling, achieving 1.2 PFLOPs on H100

**FlashAttention-4** (Li et al., 2026, arXiv:2603.05451): Co-designs the algorithm and kernel pipelining for Blackwell GPUs. Introduces warp specialization where different warps handle GEMM, softmax, and data movement concurrently. Reports 225 TFLOPs/s on H100.

### Relevance to RTX 3090 (Ampere)

RTX 3090 uses SM_86 (Ampere). FlashAttention-2 is the optimal version for this architecture. Key adaptations:
- SM_86 tensor cores support FP16/BF16/TF32, not FP8 (FP8 requires Hopper SM_90+)
- **FP8-as-storage** (Mohan 2026): FP8 can be used for KV-cache storage even on Ampere by storing quantized values and dequantizing before compute — gaining 2× memory capacity without FP8 tensor core hardware
- CUTLASS 3.x provides SM_86-optimized GEMM kernels that can be integrated into FlashAttention-2

### Design Pattern: Hardware-Aware Tiling

FlashAttention exemplifies a design pattern applicable beyond attention: **profile the memory hierarchy, then tile the algorithm to keep working data in the fastest available memory layer.** This same pattern appears in:
- **FPGA matmul** (arXiv:2503.16731): T=32 tile size chosen to fit KV260 SRAM
- **Context pruner**: Tiling context into cache-friendly chunks for LLM inference
- **PolyKV compression**: Tiling KV-cache across independent agent contexts

## RISC-V Microcontroller Ecosystem for Sensor Networks

### ESP32-C Series (RISC-V Cores)

Espressif has transitioned significant product lines to RISC-V, providing drop-in alternatives to Xtensa-based ESP32 for sensor network nodes:

| Model | Core | Key Features | Power |
|-------|------|--------------|-------|
| ESP32-C3 | Single RISC-V @ 160 MHz | Wi-Fi 6, BLE 5.0 | ~5 µA deep sleep |
| ESP32-C6 | Single RISC-V @ 160 MHz | Wi-Fi 6, BLE 5.3, 802.15.4 (Zigbee/Thread) | ~7 µA deep sleep |
| ESP32-S31 (2026) | Dual RISC-V | Wi-Fi 6, BLE, 802.15.4, **Gigabit Ethernet** | TBD |

### Alternative RISC-V MCUs

- **GD32VF103** (GigaDevice): RISC-V Bumblebee core, 108 MHz. Mature ecosystem, Arduino-compatible.
- **BL602/BL702** (Bouffalo Lab): Wi-Fi + BLE RISC-V MCUs, competitive with ESP32-C3.
- **CH32V003** (WCH): 10-cent RISC-V MCU, ideal for ultra-low-cost sensor endpoints.
- **K230** (Canaan): RISC-V + KPU (AI accelerator), 1 TOPS, suitable for on-device inference at the sensor node.

### Comparison: RISC-V vs Xtensa vs ARM for Sensor Nodes

| Factor | RISC-V (ESP32-C3) | Xtensa (ESP32) | ARM Cortex-M (STM32) |
|--------|-------------------|----------------|----------------------|
| License cost | $0 (open ISA) | Per-unit royalty | Per-unit royalty |
| Toolchain | GCC/LLVM (upstream) | Custom GCC | GCC/ARM-Keil |
| Ecosystem maturity | Maturing (2024+) | Mature | Very mature (15+ years) |
| Power efficiency | Competitive | Excellent | Excellent |
| Open-source toolchain | Full (Yosys not applicable for MCU) | Partial | Partial |

### Sensor Network Integration

For Exocortex-relevant sensor networks (drone detection, environmental monitoring, RF spectrum analysis):
- **ESP32-C6** with 802.15.4 enables Thread mesh networking — self-healing, low-power mesh for distributed sensor arrays
- **K230** enables on-device inference (wake-word detection, anomaly classification) without cloud round-trip
- **CH32V003** as ultra-low-cost leaf nodes for temperature/pressure/vibration sensing
- The open ISA enables custom extensions: a sensor fusion accelerator could be implemented as a RISC-V custom instruction

### Cross-Domain Connections

- **Geopolitics & Strategic Analysis**: RISC-V adoption reduces dependency on ARM/Xtensa licensing from US/UK entities, relevant to chip sovereignty and supply chain security.
- **OSINT & Investigation Methodology**: Distributed RISC-V sensor arrays could monitor physical-world signals (RF spectrum, acoustic signatures) for OSINT collection — building a hardware layer for open-source intelligence.
- **AI Agent Architecture**: On-device inference (K230) enables edge agents that process sensor data locally before reporting — reducing bandwidth and enabling autonomous decision-making at the edge.

## Sources

| Source | Type | URL |
|--------|------|-----|
| Li & Chen (2025) — FPGA Tiled MatMul for Transformer | arXiv paper | https://arxiv.org/abs/2503.16731 |
| Mohan (2026) — Backporting FP8 to RTX 3090 | Blog post | https://amohan.dev/blog/2026/fp8-as-storage-imma-ampere/ |
| Mohan (2026) — CUDA FP8 Ampere (code) | GitHub | https://github.com/poad42/cuda-fp8-ampere |
| CudaForge | OpenReview | https://openreview.net/forum?id=f4GtuI2blh |
| MySensors | Website | https://www.mysensors.org/ |
| LibrePCB | Website | https://librepcb.org/ |
| OpenHardware.io | Repository | https://www.openhardware.io/ |
| ESP32-GY97 | GitHub | https://github.com/gatemans/ESP32-GY97 |
| ColonelPanic.tech | Blog | https://colonelpanic.tech/ |
| NVIDIA CUTLASS | GitHub | https://github.com/NVIDIA/cutlass |
| NVIDIA Matmul Heuristics | Docs | https://docs.nvidia.com/cuda/nvidia-matmul-heuristics/ |
| FlightLLM (FPGA 2024) | Paper | FPGA-based LLM inference on Alveo U280, 6x energy vs V100 |
| SSR (FPGA 2024) | Paper | Spatial-Sequential Hybrid for Transformer acceleration on Versal ACAP |
| Tarek Allam Jr. (2025) — State of Open-Source FPGA Tools | Blog | https://www.tarekallamjr.com/blog/2025/open-source-fpga-tools/ |
| Dao et al. (2024) — FlashAttention-3 | arXiv | https://arxiv.org/abs/2407.08608 |
| Li et al. (2026) — FlashAttention-4 | arXiv | https://arxiv.org/abs/2603.05451 |
| Yosys Open Synthesis Suite | Website | https://github.com/YosysHQ/yosys |
| OpenROAD Project | Website | https://github.com/The-OpenROAD-Project |
| ESP32-S31 Announcement (2026) | CNX Software | https://www.cnx-software.com/2026/03/24/esp32-s31-dual-core-risc-v-mcu/ |
| Canaan K230 RISC-V AI MCU | Website | https://www.canaan.io/product/k230 |
| CH32V003 Ultra-Low-Cost RISC-V MCU | Website | https://www.wch-ic.com/products/CH32V003.html |

## Verification Status
Last verified: 2026-05-19. Primary sources for FPGA and RTX 3090 sections read in full. PCB section drawn from project pages and open-hardware ecosystem documentation. Cross-domain connections identified from primary material.
