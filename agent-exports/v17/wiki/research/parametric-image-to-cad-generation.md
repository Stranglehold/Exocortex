# Parametric Image-to-CAD Generation

**Status:** STABLE
**Created:** 2026-08-03
**Deepened:** 2026-08-03
**Domain:** AI Agent Architecture & Hardware & Physical Computing
**Related interests:** Agentic computer-aided design, image-to-3D model generation, agentic software development, local inference bridging

---

## Overview

Parametric image-to-CAD generation converts 2D inputs (photographs, engineering drawings, sketches, multi-view projections) into **editable parametric CAD models** — feature-based solids with constraint graphs, dimensional parameters, and a feature/operation tree, exported as STEP/IGES or scripted CAD (OpenSCAD, CadQuery, FreeCAD Python). It is distinct from *mesh image-to-3D generation* (photo -> triangulated STL/OBJ for rendering or 3D printing): parametric output preserves design intent, tolerances, and manufacturing semantics, and can be modified by downstream engineers. The v17 shared corpus draws this boundary explicitly: mesh generation produces visual/triangulated geometry; parametric CAD generation produces editable engineering models with dimensional constraints, feature trees, and manufacturing tolerances. Both are agentic pipelines, but different toolchains and output classes.

The 2026 research frontier converges on **sequence-based generation**: encoding a CAD model as a linearized token sequence (feature/operation commands, sketch primitives, B-Rep face-edge-vertex structure) and training sequence models (VQ-diffusion, autoregressive transformers, or LLMs) to predict that sequence conditioned on visual input. The generated program is then compiled into a standard STEP file, giving a single architecture the power to produce topology-correct, editable geometry.

---

## Why parametric output is harder than mesh output

1. **Topological validity.** B-Rep solids must be watertight and manifold; every edge is shared by exactly two faces. A mesh generator tolerates local noise; a parametric generator must emit globally consistent structure.
2. **Feature/operation semantics.** Real CAD models are built as operation sequences (extrude, revolve, boolean, fillet, chamfer). The model must not just look right but be right at the feature-tree level.
3. **Exactness and dimensioning.** Engineering models need precise dimensions and geometric constraints; small prediction errors are not absorbed by smoothing.
4. **Compilation is non-trivial.** The predicted sequence must compile under a target kernel (STEP/ACIS, Parasolid, OpenCascade) — a single invalid token breaks the model.
5. **Single-view ambiguity.** One photograph has hidden geometry, unknown thickness, and back-face detail; ambiguous inputs need constrained factorization rather than free hallucination.
---

## 2026 Method Taxonomy

### 1. Sequence-based Diffusion (VQ-Diffusion)
**Img2CADSeq (arXiv:2605.13293)** is the leading explicit image-to-parametric pipeline. It encodes CAD sequences into a **three-level hierarchical codebook** (fine-grained tokens to coarse structural tokens) and uses a conditioned VQ-Diffusion model to predict topologically valid CAD sequences. A key design innovation: a **contrastive conditioning framework** aligns 2D image-derived point clouds with CAD sequence encodings, so geometric appearance and construction history are learned in a shared embedding space. Output sequences compile into standard STEP files. This is the clearest demonstration of the 2026 pattern: *image conditioning -> latent CAD tokens -> compile -> STEP*.

### 2. VLM-assisted Conditional Factorization
**Img2CAD (You & Guibas, SIGGRAPH Asia 2025)** frames image-to-CAD as conditional factorization: a vision-language model decomposes the image into components (sketch primitives, extrude directions, boolean operations) and the CAD model is generated as conditionally dependent parts. The VLM handles single-view ambiguity by injecting priors about mechanical part structure. This is the approach most directly compatible with agentic orchestration: VLM factors, generator constructs, agent supervises.

### 3. LLM-Driven Program Generation
**Towards High-Fidelity CAD Generation via LLM-Driven Program Generation (arXiv:2603.11831)** attacks the gap between the two classical camps (parametric command sequences vs direct B-Rep synthesis), which in feature-based CAD are inherently intertwined (fillet/chamfer are parametric operations that only exist once B-Rep edges exist). LLM program generation expresses models as executable CAD code (OpenSCAD/CadQuery-style), unifying geometry and feature semantics in one artifact that is naturally editable, diff-able, and debuggable.

### 4. B-Rep Sequence Autoregression
**Pointer-CAD (arXiv:2603.04337)** unifies B-Rep structure with command sequences by emitting pointer-like references into a growing element table: a transformer outputs both the B-Rep tree (vertices, edges, faces) and the construction operation that created each element. **Autoregressive B-Rep Shape Generation with Parametric Surfaces (arXiv:2607.17093)** extends B-Rep generation to parametric (not just analytic) surfaces, covering curved trimmed-face geometry dominant in mechanical parts.

### 5. Multi-View Reverse Engineering
The classic alternative: **Automatic Reverse Engineering of Parametric CAD Models from Multi-View 2D Projections** (2026) encodes multiple views with an MVCNN plus a Transformer that emits a procedural CAD sequence. **Template-based reverse engineering from point clouds** (HESAE thesis 2021) remains the reference for scanned physical objects: simulated-annealing fitting against a template library, two-level filtering for boundary capture, and interface detection for assemblies — the assembly-aware end that feeds digital-twin construction.
---

## Architectural Pattern for Agentic Image-to-CAD

The convergent agentic pipeline (closest to Jake's research agenda — methods for agents to analyze images and produce common format files such as STL):

1. **Perception/structure extraction** — VLM or MVCNN extracts sketch topology, view geometry, hidden-surface priors;
2. **Sequence/parametric encoding** — maps structure into CAD tokens (hierarchical codebook, command sequence, B-Rep element table);
3. **Generation** — VQ-diffusion, autoregressive transformer, or LLM program generation produces the CAD representation;
4. **Compilation/verification** — compile to STEP via OpenCascade kernel; topological validity check (watertight, manifold);
5. **Closed-loop editing** — agent reads the feature tree, adjusts parameters, re-runs, exports fabrication-ready file.

This is structurally the same loop as agentic software development (perception -> representation -> generation -> compile -> test -> edit), which is why OpenSCAD/CadQuery-style design-as-code is the natural substrate: CAD programs are debuggable, diff-able, and version-controllable artifacts, exactly like source code, and a local LLM (e.g., Qwen-based 27B class) can plausibly serve the programming step under the local-to-frontier bridging architecture.

---

## Toolchains & Open-Source Substrate (from v17 corpus)

- **FreeCAD** — full B-Rep kernel (OpenCascade), Python scripting, STEP/IGES export; the workhorse for agent-driven parametric workflows.
- **OpenSCAD** — programmatic CSG; the purest match for LLM program generation and code-diff design loops.
- **CadQuery** — Python API generating STEP directly; best fit for agentic code generation with validation and test loops.
- **Blender MCP server** (v17 corpus) — agent-controllable mesh environment; useful for the mesh side and for visualization/verification of generated solids.

The parallel agentic-EDA movement (PCB design from spec) demonstrates the same spec-to-artifact-with-tool-orchestration pattern in hardware design: the agent selects backends, iterates on compile errors, and exports fabrication-ready output.

---

## Open Problems / Research Front

- **Single-view hidden geometry** — constrained factorization (Img2CAD) and multi-view fusion are partial answers; full 360-degree inference from one photo is unsolved.
- **Fillet/chamfer & feature fidelity** — parametric operations that depend on pre-existing B-Rep edges are the hardest tokens to predict (central motivation of 2603.11831).
- **Topological validity as a training signal** — validity checks (watertight, manifold, compilable) are natural reward/verifier signals for RL-style refinement, mirroring compiler-based feedback in agentic coding.
- **Assemblies & interfaces** — moving from single parts to multi-part assemblies with mating constraints (template-based RE is the closest prior art).
- **Local inference feasibility** — sequence/LLM generation is quantization-friendly relative to large diffusion models; the bridging-local-to-frontier architecture may make agentic image-to-CAD a realistic on-consumer-GPU capability (cf. rtx-3090-cuda-optimization page).
---

## Cross-Domain Connections

1. **[[agentic-image-to-3d-generation]]** — same perception->generation->export pipeline; mesh/STL vs parametric/STEP output classes.
2. **[[agentic-computer-aided-design]]** — text-to-CAD and tool orchestration substrate (FreeCAD/OpenSCAD/CadQuery/Blender MCP).
3. **[[agentic-software-development]]** — structural isomorphism: generate->compile->test->edit loops; design-as-code as debuggable artifact.
4. **[[bridging-local-frontier-model-performance]]** — LLM program-generation step may run locally; VQ-diffusion is the heavier, quantization-sensitive component.
5. **[[digital-twin-critical-infrastructure]]** — reverse engineering of scanned assets into editable CAD feeds digital-twin construction and maintenance.
6. **[[custom-pcb-design-sensor-networks]]** — parallel agentic-EDA movement; spec-to-fabrication-file orchestration.
7. **[[atlas-autonomous-coding-agents]]** — compiler/verifier feedback as reward signal for generation models.
8. **[[entity-resolution-pipeline-performance]]** — feature-tree/B-Rep element-table generation is structured prediction with the same validity-gate architecture as entity-binding.
9. **[[memory-architecture-taxonomy]]** — hierarchical codebook encoding of CAD sequences resembles hierarchical memory/abstraction construction in agent frameworks.
10. **[[rtx-3090-cuda-optimization]]** — inference economics: small sequence models vs large diffusion backends on 24GB GPUs.

---

## References

1. Img2CADSeq: Image-to-CAD Generation via Sequence-Based Diffusion — arXiv:2605.13293
2. You & Guibas, Img2CAD: Reverse Engineering 3D CAD Models from Images through VLM-Assisted Conditional Factorization — SIGGRAPH Asia 2025
3. Towards High-Fidelity CAD Generation via LLM-Driven Program Generation — arXiv:2603.11831
4. Pointer-CAD: Unifying B-Rep and Command Sequences — arXiv:2603.04337
5. Autoregressive B-Rep Shape Generation with Parametric Surfaces — arXiv:2607.17093
6. Automatic Reverse Engineering of Parametric CAD Models from Multi-View 2D Projections Using Deep Learning (MVCNN + Transformer), 2026
7. Template-based Reverse Engineering of Parametric CAD Models from Point Clouds — HESAE thesis 2021
8. Exocortex v17 shared corpus: agentic-computer-aided-design.md; agentic-image-to-3d-generation.md (2026-07-09 / 2026-07-06)
9. AutoCAD 2022/2019 Parametric Constraints (geometric & dimensional, design intent) — humble_bundle technical library
