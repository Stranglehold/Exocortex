# AI Drug Discovery & Computational Biology

Status: **STABLE**
Created: 2026-05-22
Last Updated: 2026-05-22
Primary Sources: 8
Cross-Domain Links: 4

## Overview

AI-driven drug discovery represents one of the most consequential near-term applications of machine learning to physical-world problems. The convergence of protein structure prediction (AlphaFold3), generative molecular design, and large-scale biological data is transforming therapeutic candidate identification, optimization, and validation. As of 2026, 200+ AI-designed drug programs are in development with multiple candidates in Phase II/III trials.

## Protein Structure Prediction

### AlphaFold3 (Google DeepMind / Isomorphic Labs)
- **Primary source**: Nature s41586-024-07487-w ("Accurate structure prediction of biomolecular interactions with AlphaFold 3")
- **Capabilities**: End-to-end structure prediction for proteins, DNA, RNA, ligands, and their interactions
- **Benchmark**: Comprehensive evaluation in bioRxiv 2025.04.07.647682 and Oxford BMC Bioinformatics bbaf616 — AF3 outperforms AF2 across protein-ligand, protein-nucleic acid, and multimeric complex prediction
- **Availability**: Open-source for academic use since Nov 2024
- **Accuracy**: Approaches experimental resolution for many targets; validated independently vs. RoseTTAFold-All-Atom

### RoseTTAFold All-Atom (Baker Lab)
- Competing approach with strong CASP validation
- Metal-protein interaction benchmarking vs. AF3

## Generative Molecular Design

### Diffusion Models
- **IDOLpro** (RSC Chemical Science d5sc01778e, 2025): Multi-objective generative chemistry combining diffusion with differentiable scoring functions
- **DiffDock / GeoDiff**: Score-based generative models learning molecular conformation distributions

### Deep Generative Models (VAEs, GANs, Transformers)
- **ScienceDirect review** (S2590098625000107, 2025): Comprehensive survey of generative AI for drug discovery
- **Taylor & Francis** (10.1080/17460441.2026.2636192, 2026): Deep generative models reshaping de novo drug design
- **Springer JoC** (s13321-025-01059-4, 2025): GenAI enables structurally diverse, chemically valid molecule design

## Clinical Validation & Real-World Impact

### Insilico Medicine (HKEX: 3696)
- **ISM001-055**: Traf2/Nck kinase inhibitor for idiopathic pulmonary fibrosis (IPF)
  - Phase IIa positive results (2025)
  - Entered Phase III trials (2026)
  - **Timeline**: ~18 months target-to-Phase-IIa
  - **Cost**: ~$6M (vs. traditional $100M+ and 4-6 years)
- **Platform**: Pharma.AI (PandaOmics + Chemistry42 + MMAI Gym)

### First AI-Designed Drugs in Clinical Trials
- **DSP-1181** (2020): First AI-designed molecule in clinical trials
- **200+ programs** in development across multiple companies (2026)

### Recursion-Exscientia Merger
- Integrated phenomic screening with automated precision chemistry
- Recursion OS: Data-driven drug discovery for cancers and rare diseases

### Industry Benchmarking
- **PMC13118854**: Generative AI transitioning pharma from empirical screening to predictive design
- **ASPT Pharm Rev** (S0031-6997-2507511-8): Leading AI-driven drug discovery platforms 2025

## Cross-Domain Links

1. **[local-inference-optimization-2026](./local-inference-optimization-2026.md)** — PTQ/KV cache compression for molecular model deployment
2. **[ai-inference-compiler-stack](./ai-inference-compiler-stack.md)** — TVM/IREE compilation of molecular ML models
3. **[ai-model-supply-chain-security](./ai-model-supply-chain-security.md)** — ML supply chain integrity in pharma (patient safety)
4. **[formal-verification-ai-systems](./formal-verification-ai-systems.md)** — Verification of molecular predictions for safety-critical drug design

## Key Metrics Summary

| Metric | AI Pipeline | Traditional Pipeline |
|--------|-------------|----------------------|
| Target-to-Phase IIa | ~18 months | 4-6 years |
| Cost to Phase IIa | ~$6M | ~$100M+ |
| Programs in Development | 200+ (2026) | Baseline |
| First AI Drug in Trials | DSP-1181 (2020) | N/A |

## Isomorphic Labs IsoDDE (2026)

**Status:** 2026 — proprietary engine, not open-source

- Isomorphic Labs (DeepMind spin-off) deployed internal "IsoDDE" engine for drug design
- Closed-source: unlike earlier AlphaFold, Isomorphic keeps advanced drug-design AI internal
- 2026 Nature/Scientific American coverage emphasizes the closed-science shift
- Represents industry trend: frontier model capabilities increasingly kept proprietary vs. open

## RFdiffusion & FrameDiff: De Novo Protein Design (2025-2026)

**Primary source:** ScienceDirect (2026) — latent space learning, probabilistic manifold exploration, RL in inverse molecular design

- **RFdiffusion**: state-of-the-art de novo protein structure generation; designs proteins with target-specific binding profiles
- **FrameDiff**: diffusion-based conformational sampling; excels at protein backbone generation
- Both tools enable exploration of previously inaccessible chemical/biological space
- Applied to ADMET optimization, target affinity, synthetic accessibility

## AI Pharma Market Scale (2026)

- **Market size:** $1.8B (2023) → $13.1B projected by 2030 (18.8% CAGR)
- **200+ AI-designed drug programs** in development as of 2026
- **DSP-1181** (2020): first AI-discovered drug candidate to enter clinical trials
- **No fully AI-designed drug** has yet received FDA marketing approval
- Key bottleneck: quality of upstream data and downstream experimental validation

## 3D Molecular Design Tools (2026)

- **MoleR**: scaffold-aware 3D molecular design
- **PocketCrafter**: pocket-aware ligand design
- Single-cell foundation models expanding into precision biology
- LLMs increasingly integrated into preclinical and clinical research workflows
- AI increasingly informing adaptive trial design and drug repurposing

## Open Questions

7. Which generative approach (diffusion vs. VAE vs. GAN vs. RL) shows best clinical translation?
8. FDA/EMA regulatory acceptance trajectory for AI-designed therapeutics?
9. Computational cost scaling for production molecular design at pharma-scale throughput?
10. Isomorphic-style closed-source paradigm vs. open-science models for drug design?
11. When will the first AI-discovered drug receive FDA marketing approval?
