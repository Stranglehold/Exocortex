# AI Supply Chain Security & SBOM

- Status: STABLE
- Created: 2026-05-23
- Last updated: 2026-05-23
- Primary sources: 12
- Cross-domain links: 4

## Overview

AI supply chain security covers the attack surface from model training through deployment: data poisoning, model theft, adversarial backdoors, dependency vulnerabilities, and provenance verification. SBOM (Software Bill of Materials) for AI systems extends traditional software supply chain concepts to models, datasets, and training pipelines.

## Threat Landscape

### Training-Time Poisoning

**Near-constant poisoning threshold** (arXiv 2510.07192 — Anthropic, UK AI Security Institute, Alan Turing Institute, Oct 2025): Demonstrated that poisoning attacks require a near-constant number of documents regardless of dataset size. 250 poisoned documents reliably backdoor LLMs from 600M to 13B parameters, even when training datasets differ by 20x in token count. This disproves the assumption that larger datasets dilute poisoning effectiveness.

**Transferable backdoors in pre-trained models** (arXiv 2401.15883 — TransTroj, NeurIPS 2025): Novel backdoor attack embedding persistent, transferable triggers in pre-trained models via gradient alignment. Backdoors survive fine-tuning and transfer across downstream tasks, making PTM adoption from untrusted sources high-risk.

### Inference-Time & Agent Attacks

**Tool poisoning via MCP** (arXiv 2605.16471 — MCPTox, May 2026): o1-mini achieves 72.8% attack success rate through model context protocol tool poisoning. Agent tool use creates a new attack surface where malicious tools injected into the supply chain execute arbitrary actions.

**Malicious intermediary attacks** (arXiv 2604.08407, Apr 2026): Supply chain attacks on OSS/AI infrastructure targeting post-training data pipelines. Adversaries poison web-browsing data and tool-use logs that agents use for self-improvement fine-tuning.

**Model-in-skill backdoor** (arXiv 2604.09378, Apr 2026): Backdoor attacks embedded in agent skill artifacts — model-bearing components distributed as reusable packages. Creates supply-chain risk for model-bearing artifacts.

### Emerging Attack Vectors (2025-2026)

**Secret stealing via fine-tuning supply chain** (arXiv 2604.27426, Apr 2026): Demonstrated backdoor attacks embedded in model code that exfiltrate secrets during local LLM fine-tuning. Targets the gap between model acquisition and deployment in enterprise AI pipelines.

**Agentic AI supply chain poisoning** (arXiv 2510.05159, Oct 2025): Systematic analysis of backdoor injection in agent interaction data (web browsing, tool use logs). Adversaries poison data collection pipelines at multiple stages to embed persistent backdoors surviving fine-tuning. Highlights vulnerability in self-improvement loops where agents learn from unvetted interaction data.

**Diffusion model PRNG backdoor** (arXiv 2605.13115, May 2026): Supply-chain attack targeting pseudo-random number generators in diffusion model pipelines. Exposes blind spot in AI security frameworks that focus on model weights but ignore generation infrastructure.

**Coding agent skill supply chain attacks** (arXiv 2604.03081, Apr 2026): Backdoored skills and tools distributed via PyPI, npm, and MCP registries. Real-world exploitation already active — four major papers on the topic published in April 2026 alone.

## Defenses & Standards Landscape

### AI SBOM Components

An AI SBOM must capture:
1. Model weights, architecture, and training configuration
2. Dataset lineage and integrity records
3. Training pipeline dependencies and versions
4. Post-processing and fine-tuning history
5. Known vulnerabilities and patches
6. Provenance attestation (signing, watermarking)
7. Governance and compliance metadata

### CISA/G7 SBOM for AI (June 2025)

CISA and G7 partners (Germany, Canada, France, Italy, Japan, UK, EU) released joint guidance establishing minimum elements for AI SBOMs. Proposes AI-specific extensions to CycloneDX/SPDX schemas capturing model weights, training data lineage, pipeline dependencies, and evaluation metrics.

### GLACIS AI Supply Chain Security Guide (April 2026)

Comprehensive 2026 playbook covering: model provenance verification, dataset transparency requirements, ML-BOM/AI-BOM standards (CycloneDX 1.7, OWASP AIBOM), Sigstore-backed model signing, dependency risk assessment across LLM stack, and federal posture alignment with CISA/international OT-AI principles.

### OWASP AIBOM (2025)

OWASP AI Bill of Materials standard extends SBOM schemas to capture AI-specific lifecycle stages. Proposes schema extensions for CycloneDX and SPDX formats to encode model weights, training epochs, data lineage, and evaluation metrics.

### Frontiers AIBOM Operationalization (2026)

Frontiers in Computer Science paper proposes methodology for operationalizing AIBOM in production, extending conventional SBOM schemas to explicitly capture AI component lifecycle, dependencies, and governance requirements.

### Pipeline Attestation (arXiv 2603.28988, Mar 2026)

Attesting LLM Pipelines proposes enforcing verifiable training and release provenance through cryptographic attestation of training runs. Addresses the gap between software supply-chain guarantees and AI-specific provenance.

## Cross-Domain Links

- **ai-model-provenance-watermarking** — C2PA provenance standards overlap with AI SBOM attestation cluster
- **ai-governance-regulation-landscape** — EU AI Act Article 50 requires provenance documentation for high-risk AI systems (Aug 2026 deadline)
- **formal-verification-ai-systems** — Verified training pipelines complement SBOM attestation for safety-critical deployment
- **adversarial-ml-robustness** — Poisoning defenses (Trimmed Mean, HE-based SecAgg) relevant to training integrity

## Key Insight

The poisoning threshold result (250 documents regardless of scale) inverts the assumed security model: larger models are not inherently more resistant to training-time attacks. This means provenance verification and SBOM attestation are not optional hygiene — they are the primary defense against supply chain compromise in AI systems.

Secondary insight: The agentic AI supply chain creates a compounding risk — agents that learn from unvetted interaction data create self-reinforcing poisoning loops. Defenses must address both the model supply chain and the agent skill/tool supply chain simultaneously.
