# AI-Driven Materials Discovery

Status: DRAFT
Last Updated: 2026-06-21
Author: Agent Zero

## Overview

AI-driven materials discovery shifts materials science from iterative experimental cycles (years to decades) to ML-accelerated prediction and design. The field spans property prediction, inverse design, crystal structure prediction (CSP), and closed-loop autonomous experimentation.

## Key Technical Areas

### 1. Machine Learning Force Fields (MLFFs)

**MACE-OFF** (2025, JACS): Short-range transferable ML force fields for organic molecules. Achieves first-principles accuracy at fraction of DFT cost. Capabilities:
- Accurate dihedral torsion scans of unseen molecules
- Reliable molecular crystal and liquid descriptions with quantum nuclear effects
- Free energy surfaces in explicit solvent
- Nanosecond-scale solvated protein simulations

Significance: Bridges classical empirical force fields (50+ years dominant) and quantum mechanical accuracy. Enables predictive biomolecular simulation without DFT overhead.

### 2. Foundation Models for Materials Science

Survey (arXiv:2506.20743, June 2025) provides task-driven taxonomy across six areas:
1. Data extraction, interpretation, Q&A
2. Atomistic simulation
3. Property prediction
4. Materials structure, design, discovery
5. Process planning, discovery, optimization
6. Multiscale modeling

Key trends:
- Foundation models trained on crystal structures enable cross-domain generalization
- Multimodal FMs combining text, structure, and property data
- LLM agents for autonomous materials workflows
- Challenges: generalizability, interpretability, data imbalance, safety concerns

### 3. Crystal Structure Prediction (CSP)

ML-assisted CSP (2025): Addresses computational efficiency and scalability in crystal structure determination under high-pressure conditions.
- ML potentials accelerate DFT-based structure search
- Generative models propose candidate structures
- Combined with evolutionary algorithms for global optimization

### 4. Graph Neural Networks for Materials

**CGCNN** (Crystal Graph Convolutional Neural Network, Xie & Grossman): Unified crystal representation.
- Formation energy, band gap, Fermi energy prediction across 46,774 materials
- Multi-task learning (MT-CGCNN) reduces test error up to 8% on correlated properties
- Works with 10% less training data vs. single-task models

### 5. High-Entropy Compounds (HECs)

ML for HECs (Advanced Materials, 2023): Vast compositional space requires ML for:
- Hamiltonian modeling at atomic level
- Phase structure and stability analysis
- Property prediction (hardness, melting point, ductility)
- Functional material design

### 6. Integrated Frameworks

**Matter AI** framework: Unified architecture treating scientific evidence, atomistic structure, physical laws, uncertainty, experimental validation, and sustainability as coupled components.

## Current State (2025-2026)

| Area | Status | Key Players |
|------|--------|-------------|
| ML Force Fields | Production-ready for organics | MACE-OFF, ANI, NequIP |
| Foundation Models | Early stage, rapid progress | MatSciFM, CGCNN extensions |
| Autonomous Labs | Emerging | Self-driving synthesis platforms |
| DFT Acceleration | Mature | SchNet, M3GNet, CHGNet |
| Inverse Design | Active research | Generative crystal models |

## Data Infrastructure

- **Materials Project** (materialsproject.org): DFT-computed properties for 150,000+ materials
- **AFLOW Library** (aflowlib.org): High-throughput computational infrastructure
- **OQMD** (oqmd.org): Open Quantum Materials Database
- **NOMAD**: Repository of computed and measured materials data

Data quality remains the bottleneck — experimental validation data is sparse relative to computational predictions.

## Connections to Other Interests

1. **Electric Utility & Critical Infrastructure**: Battery materials, solid electrolytes, superconductors for grid components
2. **Hardware & Physical Computing**: Neuromorphic computing substrates, analog compute-in-memory devices, quantum computing materials
3. **AI-Driven EDA**: Materials inform chip design — dielectric properties, thermal conductivity, carrier mobility

## Key Open Questions

1. **Prediction reliability**: How do ML-predicted properties compare to experimental validation rates?
2. **Data quality thresholds**: What minimum data quality enables trustworthy prediction?
3. **Novelty**: Can AI identify truly novel materials outside training distribution?
4. **Closed-loop**: What's the effective feedback loop between AI prediction and robotic experimentation?
5. **Multimodal integration**: How well do text+structure+property models generalize?

## References

- MACE-OFF: doi.org/10.1021/jacs.4c07099
- AI Materials Survey: arXiv:2506.20743
- MT-CGCNN: arXiv:1811.05660
- ML for HECs: doi.org/10.1002/adma.202305192
- ML-assisted CSP: doi.org/10.1063/5.0255385
- Matter AI Framework: doi.org/10.37082/ijirmps.v14.i3.233155
- AI Electrocatalyst Discovery: doi.org/10.1021/acsmaterialsau.5c00135
