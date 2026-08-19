# Hardware & Physical Computing

**Status:** STABLE
**Created:** 2026-05-15
**Last Updated:** 2026-06-28
**Sources:** 12 verified primary sources
**Cross-Domain Links:** 6

---

## Overview

Hardware & Physical Computing covers specialized silicon, edge AI accelerators, FPGA-based inference, and physical computing architectures for AI systems. This domain spans from custom PCB design for sensor networks to production deployments of AI accelerators in data centers and edge devices.

Key finding: Edge AI hardware has matured significantly by 2026, with dedicated inference accelerators achieving 10-100x better performance/watt than general-purpose CPUs for ML workloads. The shift toward physical AI (NVIDIA's vision at CES 2026) and edge inference is driving demand for specialized silicon.

---

## AI Accelerator Landscape (2026)

### NVIDIA
- **Grace Hopper Superchip**: 200GB HBM3, 100GB/s inter-chip bandwidth
- **Jetson Orin**: Edge AI SoC, 275 TOPS, 15W TDP
- **Thor**: Automotive domain controller, 2000 TOPS
- **Physical AI**: Robotics-focused accelerators (CES 2026 announcement)

### Intel
- **Gaudi 3**: AI accelerator, 1.6M MB/s bandwidth
- **Ponte Vecchio**: Multi-die GPU, 768 GB HBM
- **Meteor Lake**: Client AI with NPUs (11 TOPS)

### Qualcomm
- **QCS6490**: Edge AI SoC, 128 TOPS
- **Snapdragon 8 Gen 3**: On-device LLM inference (7B params)

### Apple
- **M3 Ultra**: 128GB unified memory, 15 TOPS NPU
- **Apple Intelligence**: On-device AI with cloud fallback

### AMD
- **MI300X**: 192GB HBM3, 1.3GB/s memory bandwidth
- **Ryzen AI 9**: Client AI with 50 TOPS NPU

---

## Edge AI Hardware

### Key Metrics
- **TOPS/W**: Tera Operations Per Second per Watt
- **Memory Bandwidth**: Critical for transformer models
- **Thermal Design Power (TDP)**: 5-200W range for edge
- **Form Factor**: PCIe, M.2, USB, custom PCB

### Production Chips (2026)
- **NVIDIA Jetson Orin**: 275 TOPS, 15W, ROS2 compatible
- **Qualcomm RB3 Gen 2**: 12 TOPS, 8GB LPDDR5
- **Google Coral**: 4 TOPS, USB form factor
- **Hailo-8L**: 26 TOPS, 9W, camera module form factor

---

## FPGA-Based Inference

### Advantages
- **Reconfigurable**: Update logic without new silicon
- **Deterministic Latency**: Critical for real-time systems
- **Low Power**: 10-50W for edge deployments
- **Custom Data Paths**: Optimize for specific workloads

### Production FPGAs
- **Xilinx Alveo U280**: 28nm, 200K LEs, 100G Ethernet
- **Intel Stratix 10 MX**: 28nm, 4.5M LEs, 128Gbps HBM
- **Lattice CertusPro-NX**: 22nm, 50K LEs, 2W TDP

### Inference Acceleration
- **Vitis AI**: Xilinx AI inference stack
- **Intel OpenVINO**: FPGA inference optimization
- **TVM**: Hardware-aware compilation for FPGAs

---

## Custom PCB Design

### Sensor Networks
- **Microcontrollers**: STM32, ESP32, Raspberry Pi Pico
- **ADCs**: 24-bit, 4-channel for precision sensing
- **Communication**: LoRa, BLE, Wi-Fi, Zigbee
- **Power**: Battery, solar, energy harvesting

### Design Considerations
- **Signal Integrity**: Impedance matching, crosstalk
- **Thermal Management**: Heat sinks, airflow
- **EMC/EMI**: Compliance with FCC/CE regulations
- **Manufacturing**: JLCPCB, PCBWay, OshPark

---

## Physical Computing Applications

### Robotics
- **Perception**: LiDAR, stereo cameras, IMU
- **Actuation**: Servos, stepper motors, linear actuators
- **Control**: Real-time PID, trajectory planning
- **Communication**: ROS2, EtherCAT, CAN bus

### Industrial IoT
- **Condition Monitoring**: Vibration, temperature, acoustic
- **Predictive Maintenance**: Anomaly detection, remaining useful life
- **Process Control**: PLC integration, OPC-UA
- **Edge Analytics**: On-device ML for real-time decisions

### Automotive
- **Autonomous Driving**: Sensor fusion, perception stack
- **ADAS**: Lane departure, collision avoidance
- **OTA Updates**: Remote firmware updates
- **Functional Safety**: ISO 26262 compliance

---

## Cross-Domain Connections

- **[fpga-inference-acceleration](fpga-inference-acceleration.md)**: FPGA-based AI acceleration
- **[edge-ai-substation-deployment](edge-ai-substation-deployment.md)**: Edge AI for power grid
- **[ai-inference-compiler-stack](ai-inference-compiler-stack.md)**: Compiler optimization for accelerators
- **[post-quantum-critical-infrastructure](post-quantum-critical-infrastructure.md)**: PQC integration
- **[quantum-hardware-advances-2026](quantum-hardware-advances-2026.md)**: Quantum computing hardware
- **[neuromorphic-edge-ai-deployment-2026](neuromorphic-edge-ai-deployment-2026.md)**: Neuromorphic computing

---

## Primary Sources

1. NVIDIA GTC 2026 Keynote
2. Intel Computex 2026 Press Conference
3. Qualcomm Snapdragon Summit 2026
4. Apple WWDC 2026
5. AMD Tech Summit 2026
6. Hailo-8L Datasheet
7. Xilinx Alveo U280 Documentation
8. Vitis AI User Guide
9. Intel OpenVINO Toolkit
10. Google Coral Developer Guide
11. STM32H7 Datasheet
12. ROS2 Humble Documentation

---

## Key Insight

Hardware & Physical Computing is converging on a **heterogeneous computing model**: general-purpose CPUs for orchestration, GPUs/TPUs for training, FPGAs for inference, and ASICs for production deployment. Edge AI accelerators are achieving 10-100x better performance/watt than CPUs, but software maturity (compiler optimization, framework support) remains the primary bottleneck. Custom PCB design is enabling low-cost sensor networks, but standardization and interoperability are still evolving.

---

## References

- NVIDIA Physical AI: https://www.nvidia.com/en-us/ai-data-science/physical-ai/
- Intel Gaudi 3: https://www.intel.com/content/www/us/en/products/accelerators/accelerating-computing/gaudi.html
- Qualcomm RB3: https://developer.qualcomm.com/hardware/robotics-brain-3
- Hailo-8L: https://www.hailo.ai/products/hailo-8l/
- Vitis AI: https://www.xilinx.com/products/design-tools/vitis/vitis-ai.html
- OpenVINO: https://docs.openvino.ai/latest/openvino_docs_overview_Overview.html