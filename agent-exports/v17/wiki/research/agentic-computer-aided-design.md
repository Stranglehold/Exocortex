# Agentic Computer-Aided Design (CAD)

**Status:** DRAFT → STABLE  
**Created:** 2026-07-08  
**Deepened:** 2026-07-09  
**Domain:** AI Agent Architecture, Hardware & Physical Computing  
**Cross-domain:** Agentic Image-to-3D, Multi-Agent Orchestration, Local-to-Frontier Bridging, OSINT

## Overview

Agentic Computer-Aided Design (Agentic CAD) refers to the use of AI agents — LLMs, VLMs, and specialized generative models — to automate and augment the creation, modification, and analysis of computer-aided design files. Unlike traditional CAD workflows where a human operates the software directly through a GUI, agentic CAD systems enable natural language interfaces, multi-step autonomous design pipelines, and closed-loop optimization.

**Key distinction:** *Mesh generation* (image-to-STL) produces visual/triangulated geometry for rendering or 3D printing. *Parametric CAD generation* (text-to-STEP, text-to-FreeCAD) produces editable engineering models with dimensional constraints, feature trees, and manufacturing tolerances. Both are agentic pipelines, but different toolchains and output classes.

## Scope of Agentic CAD

1. **Image-to-CAD / Image-to-3D:** Analyzing 2D images (photographs, sketches, technical drawings) and producing 3D models in STL, STEP, OBJ, or parametric formats.
2. **Text-to-CAD:** Natural language translated into parametric CAD models — "a 25mm × 50mm aluminum bracket with two M6 holes spaced 40mm apart" → editable STEP file.
3. **Generative Design:** Agent-driven exploration of design spaces optimized for weight, strength, manufacturability, or cost, with the agent selecting backends and iterating.
4. **CAD File Analysis & Modification:** Agents that read, understand, and edit existing CAD files (OpenSCAD scripts, FreeCAD parametric models, Fusion 360 designs).
5. **Multi-Tool Orchestration:** Agent as pipeline supervisor — generate geometry in one engine, analyze FEA in another, remesh in a third, export fabrication-ready files.

## Why This Matters for Exocortex

Agentic CAD intersects multiple Exocortex interest domains:

- **Hardware & Physical Computing:** Custom PCB enclosures, sensor mounts, and mechanical fixtures designed by agents from natural language specs, then fabricated via 3D printing.
- **OSINT Investigation:** Geolocation from photos → 3D reconstruction of scenes → measurement and analysis of terrain, structures, or objects (a latent OSINT capability not yet chained as standard workflow).
- **Local-to-Frontier Bridging:** Open-source CAD generation models (TRELLIS.2 on consumer GPUs) vs. closed frontier models (Seed3D, Rodin). The gap mirrors the LLM local-to-frontier problem.
- **Entity Resolution:** Matching physical objects to known designs — a photographed component → 3D model → database match → supply chain attribution.
- **Agentic Self-Learning:** CAD pipelines are multi-step, error-prone, and benefit from Reflexion-style self-correction loops (generate → validate → iterate).

## State of the Art (2026)

### Text-to-CAD Conversational Agents

Zoo's text-to-CAD conversational design agent (early 2026) produces **STEP geometry** from natural language descriptions. Unlike mesh-based generation (STL/OBJ), STEP files are parametrically editable engineering models with dimensional constraints. The agent translates specifications to geometry, representing the frontier where agents design to specification rather than merely generating visual assets.

### Blender MCP Server

The official Blender MCP server (announced early 2026) exposes Blender's full Python API to AI agents via the Model Context Protocol:

- Generate 3D models from text or image prompts using integrated backends (Meshy, Tripo, Rodin, Hunyuan3D, TRELLIS.2)
- Programmatically manipulate scenes, materials, lighting, and animations
- Export to standard formats: STL (3D printing), OBJ, GLB (web/AR), FBX (game engines)
- Chain multi-step workflows: generate → evaluate quality → remesh watertight → texture → export
- **Security consideration:** Code-execution MCP tools run arbitrary Python with full system access — mandatory sandboxing for production pipelines.

### Open-Source CAD Platforms

| Platform | Type | Key Capabilities | Agent Integration Pathway |
|----------|------|------------------|---------------------------|
| **FreeCAD** | Parametric CAD | Python API for full Part/PartDesign/Sketcher workbenches; reads STEP, IGES, STL, OBJ | Scriptable via Python — agent can generate and execute FreeCAD scripts |
| **OpenSCAD** | Programmatic CAD | C-like scripting language for constructive solid geometry (CSG); reads/creates STL, DXF, OFF | Text-native — agent writes .scad files directly; ideal for LLM generation |
| **Blender** | 3D modeling suite | Full Python API (bpy), MCP server, multi-format export | MCP-native agent integration — highest maturity |
| **CadQuery** | Python CAD library | Fluent Python API wrapping OpenCASCADE kernel; parametric, constraint-based | Python-native — agent writes CadQuery scripts directly |

### 2025-2026 Research Frontiers

**PhysX-3D (Cao et al., arXiv:2507.12465, Jul 2025):** First physics-grounded 3D generation framework. PhysXNet dataset annotates assets across five foundational dimensions (absolute scale, material, affordance, kinematics, function). PhysXGen uses dual-branch architecture to model latent correlations between 3D structures and physical properties — directly relevant to producing CAD-ready assets rather than visual-only shells.

**Steer3D (Ma et al., arXiv:2512.13678, Dec 2025):** ControlNet-inspired adapter adds text steerability to pretrained image-to-3D models. Two-stage training (flow-matching + DPO) achieves 2.4× to 28.5× faster editing than competing methods. Key capability for agentic pipelines: agents can iteratively refine 3D outputs through natural language, enabling conversational CAD.

### Agentic EDA (Electronic Design Automation)

The semiconductor design parallel — AI-driven EDA shares the same architecture pattern: LLM agents orchestrating multi-step design flows with physics-based constraints.

Per arXiv 2512.23189 (A Survey of Autonomous Digital Chip Design), EDA has evolved through three layers:
- **L1: Traditional CAD** — rule-based heuristic optimization
- **L2: AI-for-EDA** — ML models predicting outcomes for point problems
- **L3: Agentic EDA** — autonomous orchestration of full RTL-to-GDSII flow via probabilistic agents constrained by physical laws

This L1→L2→L3 evolution in semiconductor design maps directly to mechanical CAD's trajectory: from GUI-driven tools (L1), through ML-assisted features (L2), to agent-driven autonomous design (L3).

## Integration with Multi-Agent Orchestration

The AI 3D aggregator pattern — a supervisor loop routing to specialized subordinates — solves the heterogeneous-backend problem in CAD: one model excels at organic shapes, another at mechanical precision, a third at texturing. The agent selects backends by quality/speed tradeoffs. This maps to the multi-agent orchestration patterns documented in the Exocortex wiki (supervisor/LangGraph, routing determinism, state locality).

## Tools & Model Landscape (Mesh Generation)

See [[agentic-image-to-3d-generation]] for the full 2026 model landscape:
- Meshy, Tripo 3.0, Rodin, TRELLIS.2, Seed3D, Hunyuan3D 2.1
- AI 3D Generation Market: $3.23B (2026, 30.9% YoY growth)
- MCP-Universe benchmark for agent-driven 3D creation evaluation

## CAD File Formats: Mesh vs Parametric

| Format | Type | Editable? | Use Case |
|--------|------|-----------|----------|
| **STL** | Triangle mesh | No (geometry only) | 3D printing, rapid prototyping |
| **OBJ** | Polygon mesh | Limited | Rendering, game engines |
| **STEP** | Parametric solid | Yes — full feature tree | Engineering design, manufacturing |
| **IGES** | Parametric surface | Partial | Legacy CAD interoperability |
| **OpenSCAD .scad** | Programmatic script | Yes — text-editable | Agent-native generation target |

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[agentic-image-to-3d-generation]] | Mesh generation subset; image-to-STL pipeline shared |
| [[multi-agent-orchestration-patterns]] | Supervisor loop routing to specialized CAD backends |
| [[bridging-local-to-frontier-model-performance]] | Open-source vs closed 3D generation models mirror LLM gap |
| [[hardware-software-codesign-ai-agents]] | Co-design patterns for CAD inference on consumer GPUs |
| [[custom-pcb-design-sensor-networks]] | CAD for enclosures, mounting hardware, sensor housings |
| [[reverse-image-search-osint]] | Photograph → 3D model → measurement → analysis pipeline |
| [[satellite-imagery-osint]] | 3D terrain reconstruction from satellite imagery |
| [[entity-resolution-algorithms]] | Physical object → 3D model → database match → attribution |
| [[chiplet-architectures-ai-inference]] | AI-EDA for semiconductor design shares agentic CAD patterns |
| [[agentic-software-development]] | Both are AI agents producing engineering assets — code vs CAD |

## References

1. Zoo text-to-CAD conversational design agent (early 2026) — text-to-STEP parametric generation
2. Blender MCP server (2026) — Blender Python API exposed via Model Context Protocol
3. Cao et al., PhysX-3D: Physical-Grounded 3D Asset Generation, arXiv:2507.12465 (Jul 2025)
4. Ma et al., Steer3D: Feedforward 3D Editing via Text-Steerable Image-to-3D, arXiv:2512.13678 (Dec 2025)
5. The Dawn of Agentic EDA: A Survey of Autonomous Digital Chip Design, arXiv:2512.23189
6. NSF Workshop Report on AI for Electronic Design Automation, arXiv:2601.14541 (Jan 2026)
7. LLM-Assisted Electronic Design Automation, arXiv:2601.14098 (Jan 2026)
8. AI-Driven Automation for Digital Hardware Design: A Multi-Agent Framework, ACM DAC (2025)
9. State of AI 3D Generation 2026 Industry Report, 3daistudio.com (June 2026)
10. Torta & Torta, 3D Printing: An Introduction — CAD software survey (FreeCAD, OpenSCAD, LibreCAD)

## Verification Sources

- Search exocortex_memory for "agentic CAD text-to-CAD Zoo STEP parametric" — returned agentic-image-to-3d wiki excerpts on Blender MCP, Zoo text-to-CAD, PhysX-3D, Steer3D, agentic EDA
- Search exocortex_memory.search_library for "CAD parametric FreeCAD OpenSCAD" — returned 3D Printing: An Introduction with FreeCAD/OpenSCAD listings
- Cross-referenced against existing agentic-image-to-3d-generation STABLE page for scope differentiation
- Cross-referenced against chiplet-architectures-ai-inference for AI-EDA connection
