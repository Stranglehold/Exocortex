# Synthetic Data Generation for ML Training & Testing

Status: STABLE
Created: 2026-05-19
Last Updated: 2026-05-19
Cycle Deepened: #173 (BUILD)
Tags: machine learning, data privacy, differential privacy, tabular data, GANs, LLMs, entity resolution

## Overview

Synthetic data generation creates artificial datasets that preserve statistical properties of real data while enabling privacy protection, data augmentation, and model training in data-scarce scenarios. Three key domains: tabular data generation, privacy-preserving synthesis, and LLM-generated training data.

## Primary Sources (2025-2026)

### Foundational Papers
- **RLSyn** (arXiv 2512.21395, Dec 2025): Reinforcement learning approach to synthetic data generation, benchmarked on AI-READI and MIMIC-IV biomedical datasets against SOTA GANs
- **Reasoning-Driven SDG** (arXiv 2603.29791, Mar 2026): Framework for reasoning-driven synthetic data generation and evaluation
- **LLM-Based SDG Survey** (Springer 2025): Comprehensive survey of LLM methods for synthetic data generation, covering agentic workflows and automated synthesis
- **WEF Synthetic Data Report 2025**: Industry assessment of synthetic data as "new data frontier"

### Privacy-Utility Trade-off Research
- **ScienceDirect 2025**: "Fidelity versus privacy and utility trade-off of synthetic patient data" — systematic evaluation of 5 synthetic data models across 3 patient datasets
- **Springer Nature 2025**: "Synthetic data: revisiting the privacy-utility trade-off" — challenges assumption that synthetic data provides better privacy-utility than traditional anonymization
- **Frontiers 2025**: Comprehensive evaluation framework for synthetic tabular data with/without differential privacy
- **SMOTE-DP** (arXiv 2506.01907): Improves privacy-utility tradeoff with synthetic data, showing strong privacy protection without significant utility loss
- **OpenReview 2025**: "Differentially Private Synthetic Data via APIs 4: Tabular Data" — DP guarantees for tabular synthesis

### Benchmarking
- **AIMultiple Synthetic Data Benchmark**: Compared 7 publicly available synthetic data generators from 4 providers on 70K sample holdout dataset (4 numerical, 7 categorical features)
- **TabularBenchmark Suite**: Standardized evaluation of tabular generative models

## Key Findings

### Privacy-Utility Trade-off Reality
1. **No free lunch**: 2025 papers consistently show synthetic data does NOT automatically provide better privacy-utility trade-offs than traditional anonymization
2. **Membership inference resistance**: Varies dramatically by model — simple models (CopulaGAN) often provide better privacy than complex ones (CTGAN, TVAE)
3. **Differential privacy guarantees**: Possible but come with significant utility costs; SMOTE-DP shows promise in reducing this gap

### Tabular Data Generation Landscape
- **CTGAN** (Conditional Tabular GAN): Leading approach for mixed-type tabular data
- **TVAE** (Tabular Variational Autoencoder): Strong performance on continuous variables
- **CopulaGAN**: Best for preserving marginal distributions
- **Diffusion models**: Emerging as strong competitors to GANs for tabular data (2025-2026)

### LLM-Generated Synthetic Data
- **Quality concerns**: Most approaches are ad-hoc; need systematic evaluation
- **Agentic workflows**: Emerging pattern where LLMs act as data generators with verification loops
- **Cost-benefit**: Significantly cheaper than manual data collection but requires careful validation

## Entity Resolution Applications

Synthetic data generation is particularly relevant for entity resolution training:
- **Data augmentation**: Generate synthetic entity pairs for positive/negative training examples
- **Cross-domain transfer**: Generate synthetic records mimicking target domain distributions
- **Privacy protection**: Enable sharing of ER training data without exposing sensitive records

## Cross-Domain Links
- [entity-resolution](entity-resolution.md) — Training data generation for ER models
- [adversarial-ml-robustness](adversarial-ml-robustness.md) — Adversarial example synthesis
- [privacy-and-cryptography](privacy-and-cryptography.md) — DP guarantees, membership inference
- [edge-ai-substation-deployment](edge-ai-substation-deployment.md) — Data augmentation for resource-constrained models
- [fpga-inference-acceleration](fpga-inference-acceleration.md) — Synthetic data for model validation

## Open Questions
1. Can synthetic data fully replace real data for ER model training without accuracy loss?
2. What DP parameters provide meaningful privacy guarantees without destroying utility?
3. How do diffusion models compare to GANs for tabular data in 2026?
4. What validation frameworks exist for synthetic data quality assessment?
