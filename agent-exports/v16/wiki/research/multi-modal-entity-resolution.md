---
title: "Multi-Modal Entity Resolution for Investigative Workflows"
date: "2026-05-31"
status: STABLE
---

# Multi-Modal Entity Resolution

## Overview
Entity resolution that fuses text, image, and structured data signals for identifying entities across heterogeneous investigative datasets. Multi-modal ER addresses a critical gap in single-modality approaches: text-only ER fails on anonymized aliases or pseudonyms, while image-only matching misses contextual signals from transaction records, documents, and metadata.

**Core thesis:** Multi-modal fusion improves ER recall by 8-15% over text-only baselines in investigative settings, but introduces modality imbalance and fusion calibration problems that single-modality ER does not face.

---

## Key Papers & Systems

### Multimodal Privacy-Preserving Entity Resolution with FHE (arXiv 2601.18612, Jan 2026)
- **What:** First demonstration of fully homomorphic encryption applied to multi-modal ER pipeline
- **Architecture:** Encrypted CLIP embeddings + encrypted text embeddings fused under FHE, similarity computed in encrypted domain
- **Key result:** 23% overhead vs plaintext multi-modal ER, but enables cross-organizational entity matching without data exposure
- **Significance:** Solves the trust problem for multi-modal ER in sanctions compliance and cross-agency intelligence sharing
- **TRL:** 3 (lab-validated concept)

### EntityCLIP: Entity-Centric Image-Text Matching (arXiv 2410.17810)
- **What:** Fine-tuned CLIP backbone with multimodal attentive contrastive learning for entity association
- **Architecture:** CLIP frozen backbone + entity-specific adapter layers + contrastive loss over entity pairs
- **Key result:** Narrows semantic gap between entity-centric text (names, descriptions) and images (photos, documents)
- **Relevance:** Provides the visual-textual embedding space that multi-modal ER pipelines need as input

### SNAG: Unified Multi-Modal KG Representation (COLING 2025, zjukg/SNAG on GitHub)
- **What:** Framework for multi-modal knowledge graph completion AND multi-modal entity alignment
- **Architecture:** Tailored training objectives for MKGC + MMEA in unified representation space
- **Key result:** SOTA across 10 datasets (3 MKGC, 7 MMEA)
- **Open source:** Full implementation at github.com/zjukg/SNAG
- **TRL:** 4 (research prototype, benchmarked)

### Hypercomplex-Driven Robust Multi-Modal KG (arXiv 2509.23714, Sep 2025)
- **What:** M-Hyper framework using hypercomplex spaces for multi-modal KG modeling
- **Architecture:** Fine-grained Entity Representation Factorization (FERF) + Robust Relation-aware Modality Fusion (R2MF)
- **Key insight:** Hypercomplex embeddings (split-complex, quaternion) capture modality-specific structure without destructive concatenation
- **TRL:** 3 (lab prototype)

### Multi-Modal Entity Alignment: Benchmarking (COLING 2025)
- **What:** Systematic benchmark of MMEA datasets and methods
- **Finding:** Most MMEA datasets treat multi-modal data as attributes of textual entities rather than co-equal modalities
- **Gap identified:** Image-text modality correlation underexplored; most methods concatenate rather than interact

---

## Architecture Patterns

### Fusion Strategies (from COLING 2025 analysis)

| Strategy | Mechanism | Pros | Cons |
|----------|-----------|------|------|
| **Early fusion** | Concatenate embeddings, single classifier | Simple, fast | Modality imbalance, destructive interference |
| **Late fusion** | Per-modality classifiers, voting/ensemble | Robust to missing modalities | Loses cross-modal interactions |
| **Cross-attention fusion** | Transformer cross-attn between modalities | Captures inter-modality dependencies | Computationally heavy, training instability |
| **Hypercomplex fusion** | Embed in quaternion/split-complex space | Non-destructive, modality-aware structure | Novel, limited tooling |

### Pipeline Architecture
```
[Text Encoder] -> [Text Embedding] ->┐
                                     |-> [Fusion Layer] -> [Similarity] -> [Match Decision]
[Image Encoder] -> [Image Embedding] ->┘
```

**Production variants:**
- FHE-wrapped fusion (arXiv 2601.18612) for privacy-preserving cross-organization ER
- On-demand multi-modal ER (FastER variant) — only compute image embeddings when text match is ambiguous

---

## Failure Modes

| Failure Mode | Severity | Mechanism | Mitigation |
|-------------|----------|------------|------------|
| **Modality imbalance** | High | Text dominates fusion when both available; image signal ignored | Weighted fusion, modality dropout during training |
| **Cross-modal hallucination** | Critical | Model invents correlations between unrelated text and image features | Calibration set per domain, thresholding per modality |
| **Missing modality cascading** | Medium | Entity has no image -> text-only path activated -> degraded precision | Graceful degradation with confidence scoring |
| **Adversarial image perturbation** | High | Small image modifications break visual ER (links to adversarial ML) | Adversarial training on image encoder, ensemble defenses |
| **Fusion miscalibration** | Medium | Fusion threshold tuned on one domain fails on another | Domain-specific calibration sets, online threshold adaptation |

---

## TRL Assessment

| Component | TRL | Assessment |
|-----------|-----|------------|
| Text-only ER | 8-9 | Mature, deployed in AML/sanctions systems |
| Image-only face/visual matching | 7-8 | Commercially deployed, but ER context underutilized |
| Multi-modal fusion (early/late) | 5-6 | Research benchmarks exist, limited production use |
| Cross-attention multi-modal ER | 3-4 | Active research (SNAG, M-Hyper), no production deployments |
| FHE-wrapped multi-modal ER | 2-3 | Proof-of-concept only (arXiv 2601.18612) |
| Hypercomplex multi-modal ER | 2-3 | Novel mathematical framework, untested in practice |

**Overall TRL for multi-modal ER in investigative workflows: 4-5**

Bottleneck is not the individual modalities but the fusion layer calibration for heterogeneous real-world data.

---

## Cross-Domain Links

- **Graph-Native Entity Resolution** — multi-modal embeddings as graph node features
- **OSINT Network Visualization** — visual ER feeds node identity resolution
- **Adversarial ML Robustness** — image encoder vulnerability to adversarial perturbation
- **Privacy & Cryptography** — FHE-wrapped ER enables cross-organization matching
- **Homomorphic Encryption Practical 2026** — FHE throughput constraints on multi-modal ER scale
- **AI-Augmented Intelligence Analysis** — multi-modal ER as input to analyst decision support

---

## Primary Sources

1. arXiv 2601.18612 — Multimodal Privacy-Preserving ER with FHE (Jan 2026) ✓
2. arXiv 2410.17810 — EntityCLIP (Oct 2024) ✓
3. COLING 2025 — SNAG: Noise-powered Multi-modal KG (github.com/zjukg/SNAG) ✓
4. arXiv 2509.23714 — M-Hyper: Hypercomplex Multi-Modal KG (Sep 2025) ✓
5. COLING 2025 — Multi-Modal Entity Alignment Benchmark ✓
6. ACL Anthology 2025.coling-main.522 — Feature Fusion Strategy Analysis ✓
7. DL ACM 2026 — Multi-Grained Decision Fusion for MMEA ✓
