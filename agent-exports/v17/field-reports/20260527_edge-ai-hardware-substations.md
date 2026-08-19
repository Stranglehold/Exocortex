# Field Report: Edge AI Hardware for Substation LLM Deployment

**Date:** 2026-05-27
**Cycle:** EXPLORE
**Topic:** Hardware & Physical Computing × Electric Utility & Critical Infrastructure × AI Agent Architecture

---

## 1. What I Explored

I followed the thread of **deploying LLM-based inference at electrical substations** — a cross-domain intersection of hardware selection (what runs?), utility-grade ruggedness requirements (what survives?), and AI architecture (what orchestration pattern?).

The specific question: when Jake wants to run a local LLM at a substation for anomaly detection, maintenance assistant, or compliance checking, what hardware actually runs in that environment, and what are the real deployment patterns in 2025-2026?

---

## 2. What I Found

### Hardware Landscape

**NVIDIA Jetson dominates edge AI for industrial.** The production-ready stack is:

| Platform | TOPS | Use Case |
|---|---|---|
| Jetson Orin NX (Syslogic, Lanner) | up to 100 TOPS | Rugged fanless, -40°C to 70°C, dual PoE, GPS, 12/24V wide input |
| Jetson AGX Orin | up to 275 TOPS | Factory floor vision, multi-model inference |
| Jetson Thor (2026) | 2,070 TOPS FP4 | Multimodal AI (VLM + LLM + sensor fusion) on-device |

**Key industrial vendors:**
- **Lanner EAI-I132** — purpose-built rugged edge AI computer with Jetson Orin, specifically marketed for "mission-critical, real-time edge intelligence" at infrastructure sites
- **Syslogic** — NVIDIA Preferred Partner, ultra-robust industrial computers for "demanding deployments where durability, longevity, and reliability are critical"
- **Neteon** — Jetson industrial PCs with three-layer stack: rugged Jetson compute + IIoT protocol gateways (Modbus, DNP3, IEC 61850) + TSN networks

### LLM Feasibility on Edge

**arXiv:2506.09554** (Understanding the Performance and Power of LLM Inferencing on Edge Accelerators) evaluated Meta Llama3.1, Microsoft Phi-2, Deepseek-R1-Qwen on Jetson Orin AGX, from 2.7B to 32.8B parameter models. Key finding: **edge LLM inference is viable now**, not theoretical.

**TensorRT Edge-LLM** (GitHub/NVIDIA) provides production C++ inference pipeline for Jetson: HuggingFace checkpoint → ONNX → TensorRT engine → on-device inference. Already supports Qwen3-4B on Jetson Orin Nano, Cosmos Reason2 8B VLM on Jetson Thor.

### Substation-Specific Deployment

**arXiv:2507.00672v1** (Toward Edge General Intelligence with Multi-LLM) — a survey from UESTC China, NTU Singapore, Queen's University Belfast, Western University, and University of Waterloo — explicitly describes LLM deployment at substations:

> "Placing LLMs on distributed edge, at substations, control centers, or on inspection drones, minimizes communication delays. It can ensure critical functions can continue locally if cloud connectivity is lost. This arrangement significantly cuts fault response times and reduces bandwidth usage."

The paper envisions **Multi-LLM architectures** where different specialized LLMs handle different substation modalities: one for SCADA anomaly detection, one for maintenance documentation query, one for drone visual inspection.

### Microsoft Foundry Local

At Build 2025, Microsoft unveiled **Foundry Local** — an edge deployment platform for Small Language Models (SLMs) on Windows and ARM-based PCs. This signals a broader industry trend: the cloud vendors themselves are building for edge-local inference.

---

## 3. What I Think Is Interesting

**The convergence point is 2026.** Three things are simultaneously arriving:

1. **Hardware is ready** — Jetson Thor at 2,070 TOPS makes multimodal LLM inference at a substation not just possible but practical
2. **Software stacks are mature** — TensorRT Edge-LLM provides a production pipeline, not a research demo
3. **The architecture pattern is shifting** — from single edge AI models to Multi-LLM orchestrated systems, where multiple specialized small models collaborate at the edge

For Jake's Exocortex context, the implication is: **the bridging-local-to-frontier problem applies at the edge too.** A substation running Qwen3-4B on a rugged Jetson Orin NX is the same architectural challenge as the desktop RTX 3090 running Qwen — just with environmental constraints (temperature, power, vibration, air-gapped operation).

The **DNP3/Modbus/IEC 61850 protocol gateway** layer that industrial vendors like Neteon ship is critical — this is not just an inference box, it's a **protocol-aware AI node** that can read relay statuses and SCADA points directly.

---

## 4. What I'd Explore Next

- **IEC 61850 + LLM integration** — can an LLM parse GOOSE messages and MMS reports natively, or does it need a structured translation layer?
- **Air-gapped fine-tuning** — how do you fine-tune a model at a substation that has no internet? On-device fine-tuning frameworks (LoRA on edge)?
- **Power envelope analysis** — what's the actual wattage budget for 24/7 LLM inference in a substation relay cabinet? Thermal implications of Jetson Thor?
- **Multi-LLM orchestration at the edge** — the arXiv survey proposes it but doesn't implement; what's the actual orchestration layer? Is it MCP-based?

---

## 5. Cross-Domain Connections

| Connection | Domains Linked |
|---|---|
| Rugged edge AI hardware enables substation-local LLM | Hardware × Electric Utility |
| Multi-LLM orchestration pattern applies equally to edge and desktop | AI Architecture × Hardware |
| IEC 61850 protocol gateways + LLM = AI-native SCADA | Electric Utility × AI Architecture |
| Air-gapped inference requirements mirror privacy-preserving AI | Electric Utility × Privacy & Cryptography |
| TSMC/Samsung semiconductor trends directly affect edge AI TOPS/watt | Hardware × Markets |
| Substation autonomy under comms loss mirrors gray-zone resilience | Geopolitics × Electric Utility |

---

## Sources

- Luo et al., "Toward Edge General Intelligence with Multi-LLM: Architecture, Trust, and Orchestration," arXiv:2507.00672v1, 2025
- "Understanding the Performance and Power of LLM Inferencing on Edge Accelerators," arXiv:2506.09554, 2025
- Lanner Inc., "Architecting the Rugged Edge AI" and GTC 2026 product announcements
- Syslogic, "Industrial Edge AI Computer — NVIDIA Jetson Orin NX"
- NVIDIA, TensorRT Edge-LLM, github.com/NVIDIA/TensorRT-Edge-LLM
- Neteon, "NVIDIA Jetson Industrial PC: Edge AI for Factory Floor"
- Microsoft Foundry Blog, "Foundry Local: A New Era of Edge AI"
