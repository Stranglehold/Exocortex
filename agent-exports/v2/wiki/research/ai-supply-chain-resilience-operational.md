# AI Supply Chain Resilience: Operational Risk Management

**Status: STABLE**
**Created: 2026-05-23**
**Last updated: 2026-05-23**
**Verified primary sources: 10**
**Cross-domain links: 5**

---

## Overview

Operational supply chain risk management for AI/ML systems in production covers four domains: vendor risk assessment, model provenance tracking, dataset integrity verification, and third-party dependency auditing. The threat landscape includes poisoned training data, backdoored models, malicious model hub uploads, and compromised ML dependencies.

---

## 1. Frameworks & Standards

### OSSF AI/ML Security Working Group
- **Source**: [GitHub - ossf/ai-ml-security](https://github.com/ossf/ai-ml-security)
- OpenSSF working group covering both supply chain security for AI development and AI-for-security use cases
- Defines ML-BOM (Machine Learning Bill of Materials) concept for dependency inventory
- Active guidance on model provenance through the ML lifecycle

### C2PA AI/ML Specification (v2.4)
- **Source**: [C2PA AI/ML Guidance Spec](https://spec.c2pa.org/specifications/specifications/2.4/ai-ml/ai_ml.html)
- Cryptographic provenance framework extended to AI/ML: indicates tampering of datasets, software, and models during training and inference
- Adobe, OpenAI, Sony have adopted C2PA for content provenance; ML extension follows same signing/verification architecture
- G7 Hiroshima AI Process Transparency Report (Apr 2025) references C2PA adoption for AI security
- Practical compliance: embed `AISystemUsed` and `AISystemVersionUsed` via IPTC 2025.1, sign with C2PA manifest

### GLACIS AI Supply Chain Security Guide 2026
- **Source**: [GLACIS Guide](https://www.glacis.io/guide-ai-supply-chain-security)
- Comprehensive framework covering ML-BOM, AI SBOM, model provenance, and regulatory requirements
- Maps attack vectors across ML lifecycle stages

### OWASP LLM03:2025 Supply Chain
- **Source**: [OWASP Gen AI Security - LLM03](https://genai.owasp.org/llmrisk/llm032025-supply-chain/)
- Dedicated category for LLM supply chain vulnerabilities
- Risks extend beyond traditional software: third-party pre-trained models, training data poisoning, deployment platform compromises

### Databricks AI Security Framework (DASF)
- **Source**: [Databricks Blog](https://www.databricks.com/blog/deploying-third-party-models-securely-databricks-data-intelligence-platform-and-hiddenlayer)
- Documents specific risk categories: Model 7.1 (Backdoor/Trojaned ML), Model 7.3 (ML Supply Chain Vulnerabilities)
- Addresses model zoo risks in enterprise context

---

## 2. Model Provenance Verification

### Atlas Framework (arXiv 2502.19567)
- **Source**: [arXiv 2502.19567](https://arxiv.org/html/2502.19567v1)
- Framework for ML lifecycle provenance & transparency
- Addresses data poisoning and supply chain attacks across the full ML lifecycle
- Balances transparency requirements against data confidentiality constraints

### Hugging Face Ecosystem Risks
- **Source**: [JFrog Veriprajna Analysis](https://veriprajna.com/technical-whitepapers/architectural-imperative-ai-supply-chain-integrity-securing-ml-lifecycle), [TraxTech](https://www.traxtech.com/ai-in-supply-chain/hugging-face-model-hijacking-threatens-ai-supply-chain-security)
- JFrog discovery: 100+ malicious Hugging Face models with pickle reverse shells
- PickleScan: 3 zero-day vulnerabilities detected, 96% false positive rate in automated scanning
- SafeTensors-first governance eliminates pickle-based deserialization attacks

---

## 3. Dataset Integrity & Contamination Detection

### Contamination Quantification (arXiv 2502.00678)
- **Source**: [arXiv 2502.00678](https://arxiv.org/abs/2502.00678), ICML 2025 poster
- Measures overlap between evaluation datasets and pre-training corpora
- Provides quantitative contamination scores for benchmark reliability

### RL Contamination Detection (arXiv 2510.09259)
- **Source**: [arXiv 2510.09259v2](https://arxiv.org/html/2510.09259v2)
- Detects data contamination from reinforcement learning post-training
- Significant for evaluating LLM benchmark reliability when training data is unknown

### Contamination-Evasion Fragility
- **Source**: [OpenReview](https://openreview.net/forum?id=bhR00j6Mku)
- Finding: evading contamination detection for reasoning LLMs is alarmingly easy
- Existing detection approaches are fragile against adversarial evasion

### Contamination-Resistant Benchmarks
- LiveBench (ICLR 2025): Contamination-limited benchmark using dynamic prompts
- LiveXiv (ICLR 2025): Multi-modal live benchmark based on arXiv papers
- arXiv 2605.19999: Proposes unlearnable data techniques for contamination resistance

---

## 4. Third-Party Model Marketplace Risk Management

### Hugging Face Enterprise Practices
- Model hub scanning for malicious payloads (JFrog collaboration)
- PickleScan for automated vulnerability detection (96% FPR remains a challenge)
- SafeTensors migration removes entire class of deserialization-based attacks
- Model card requirements: training data disclosure, intended use, known limitations

### Enterprise ML Platform Controls
- Databricks: DASF framework, third-party model quarantine + scanning before production
- Vertex AI: Model Garden with vetted models, third-party risk customer-managed
- Kernshell 2026 MLOps Guide: supply chain security is primary concern for enterprises using pre-trained models

---

## Cross-Domain Links

1. **AI Compliance Automation (RegTech)** — C2PA provenance enables machine-readable compliance evidence
2. **AI Model Provenance & Watermarking** — C2PA framework shared across content and model provenance
3. **Post-Quantum Critical Infrastructure** — PQC migration affects long-term cryptographic provenance durability
4. **Entity Resolution** — Vendor graph construction for supply chain dependency mapping
5. **AI Supply Chain Security SBOM** — ML-BOM tracks model/data dependencies parallel to software SBOM

---

## 2026 Developments

### Production-Ready ML-BOM Formats
- **CycloneDX ML-BOM v1.7** — first production-ready ML Bill of Materials format (April 2026)
- **SPDX 3.0 AI Profile** — alternative production-ready format for AI/ML dependency tracking
- Both formats now supported by major SBOM tooling; auditors accept either

### Sigstore-Backed Model Signing
- **Linux Foundation Model Signing Project** — reference implementation for model provenance
- **Sigstore/Cosign + in-toto** — cryptographic signing pipeline for model artifacts
- **Monday-morning checklist** — five-stage maturity ladder for AI supply chain security adoption
- **Reference ingestion-gate architecture** — picklescan + modelscan + CVE scan + provenance verify

### EU AI Act Data Governance
- Model provenance requirements align with EU AI Act high-risk system obligations
- ML-BOM serves as machine-readable compliance evidence for conformity assessment
- CISA international OT-AI principles provide federal posture guidance (December 2025)

### Key Attack Vectors Identified
- Pickle RCE in model weights (still prevalent despite SafeTensors migration)
- Embedded backdoors in open-source models
- Dependency confusion in transformers/langchain integration packages
- Dataset poisoning via compromised training data sources

---

## Key Takeaways

1. Model hub supply chain is an active attack surface: 100+ malicious Hugging Face models with pickle reverse shells
2. Contamination detection is fragile: adversarial evasion is easy; live/dynamic benchmarks are more robust
3. C2PA provides cryptographic foundation: extended from content to ML model provenance; adopted by Adobe, OpenAI
4. SafeTensors eliminates pickle attack vector: format migration removes entire class of deserialization attacks
5. Enterprise adoption accelerating: Databricks DASF, OWASP LLM03, OpenSSF WG indicate institutional recognition
6. **2026 production formats**: CycloneDX ML-BOM v1.7 and SPDX 3.0 AI Profile are now auditor-accepted
7. **Sigstore model signing**: Linux Foundation reference implementation provides production signing pipeline
8. **EU AI Act alignment**: ML-BOM serves as machine-readable compliance evidence for high-risk systems
