# AI Model Supply Chain Security

**Status:** STABLE  
**Created:** 2026-05-20  
**Last updated:** 2026-05-26 (Cycle 639 BUILD: model theft economics, HF Hub CVEs, EU AI Act)  
**Sources verified:** 13/13  
**Cross-domain links:** 4/4  

---

## Scope

Model supply chain security covers the integrity, provenance, and trustworthiness of AI models from training data ingestion through deployment. Key threat vectors include data poisoning, model theft, backdoor insertion, training pipeline manipulation, and insecure model distribution.

## Model Theft Economic Impact

- AI model supply chain attacks cost **$12B in 2025** (cybersecfeed.com analysis)
- Model copying achieves **~80% success rate** without access to original code or data (Analytics Insight 2026)
- Economic Espionage Act applicability unclear for cross-jurisdictional model theft
- Weak legal frameworks and security gaps increase financial, safety, and competitive risks worldwide

## Hugging Face Hub Vulnerability Landscape

- **CVE-2025-14921**: Hugging Face Transformers Transformer-XL Model Deserialization RCE — allows remote attackers to execute arbitrary code via untrusted model loading
- **CVE-2025-23304**: Nvidia NeMo metadata poisoning vulnerability — high-severity, integrates with Hugging Face; fix in NeMo 2.3.2
- **arXiv:2509.06703**: "On the (In)Security of Loading Machine Learning Models" — systematic analysis of public repository poisoning and model distribution channel attacks
- vm2 Sandbox Escape vulnerabilities (2026 CVE wave) turning AI agents into host RCE vectors
- Enterprise gap: organizations download from Hugging Face/Ollama at scale without formal admission processes (BeyondScale 2026)

## EU AI Act Transparency Requirements

- **Article 52 enforceable March 1, 2026**: transparency obligations for AI systems interacting directly with humans
- **Full enforcement August 2, 2026**: all AI systems must clearly disclose artificial nature
- Commission draft guidelines on transparency obligations published May 8, 2026 (consultation through June 3, 2026)
- Article 50(1): transparency in human-AI interaction with tiered compliance by risk level
- Systemic risk models: Commission may designate GPAI models as presenting systemic risks ex officio or following qualified alert from scientific panel

## Primary Sources

1. **MITRE ATLAS v5.1.0** (Nov 2025) — 16 tactics, 84 techniques, 32 mitigations, 42 case studies. Expanded from v5.0 (Oct 2025: 15 tactics/66 techniques) with agentic AI techniques added Feb 2026.
2. **NIST AI Risk Management Framework 1.0** (Jan 2023) — 72 subcategories across 19 categories/4 core functions. April 2026 update: AI RMF Profile on Trustworthy AI in Critical Infrastructure.
3. **arXiv 2503.22759** — "Data Poisoning in Deep Learning: A Survey"
4. **arXiv 2507.12919** — "Architectural Backdoors in Deep Learning: A Survey"
5. **arXiv 2411.09945** — TEESlice: TEE-shielded DNN partition for protecting sensitive neural network models
6. **arXiv 2502.19567** — Atlas: A Framework for ML Lifecycle Provenance & Transparency
7. **EU AI Act** — Article 52 (transparency obligations enforceable March 1 2026), Article 50(1), systemic risk model designation
8. **CVE-2025-14921** — Hugging Face Transformers Transformer-XL deserialization RCE
9. **CVE-2025-23304** — Nvidia NeMo metadata poisoning vulnerability
10. **arXiv:2509.06703** — "On the (In)Security of Loading Machine Learning Models"
11. **cybersecfeed.com** — AI Model Poisoning: $12B Supply Chain Crisis 2025
12. **Analytics Insight** — AI Technology Theft Risks 2026 (80% model copying success rate)
13. **BeyondScale** — Open Source AI Model Security: Vetting Hugging Face Downloads (2026)

## Key Findings

### Data Poisoning (Critical)
- Clean-label poisoning more dangerous than noisy-label: poison samples look legitimate, harder to detect
- arXiv 2503.22759 categorizes poisoning by attack surface (training data, fine-tuning data, RL feedback)
- Federated learning environments add poisoning risk: untrusted clients submit malicious gradients

### Architectural Backdoors (Critical Gap)
- Malicious logic embedded directly into model computational graphs
- Survives clean retraining — backdoor is in architecture, not weights
- No standardized detection method exists

### Model Provenance Standards
- SLSA framework adapted for ML artifacts
- Atlas framework provides end-to-end provenance tracking
- TEE-based training integrity (TEESlice, Intel SGX/AMD SEV) emerging but not production-ready

### Distribution Channel Attacks
- Public repository poisoning: malicious models uploaded to trusted platforms
- Dependency confusion: attackers register packages with same names as internal models
- Metadata poisoning: compromised model metadata can execute arbitrary code during loading

## Cross-Domain Implications

1. **Adversarial ML Robustness** (wiki:adversarial-ml-robustness) — data poisoning is an adversarial attack vector
2. **AI Agent Trust Infrastructure** (wiki:ai-agent-trust-infrastructure) — model provenance enables capability-based delegation
3. **Post-Quantum Critical Infrastructure** (wiki:post-quantum-critical-infrastructure) — long-term provenance requires PQC for cryptographic commitments
4. **AI Agent Delegation Security** (wiki:ai-agent-delegation-security) — ERC-8126/ATF standards applicable to model attestation

## Integration Path

- Verify training data source integrity during ingestion using SLSA-style attestations
- Use model provenance (Atlas framework) to validate ER model versions
- TEE-based inference for sensitive entity resolution ensures data confidentiality
- Architectural backdoor detection as pre-deployment gate for ER model updates

## Open Questions

1. What is the state of federated learning poisoning defenses in production (beyond Trimmed Mean)?
2. How does model supply chain security interact with federated learning trust assumptions?
3. What is the economic impact of specific model theft incidents (case study data needed)?

## Deepening Checklist
- [x] MITRE ATLAS supply chain attack techniques
- [x] NIST AI RMF supply chain section
- [x] arXiv data poisoning surveys 2024-2026
- [x] Model provenance standards (Atlas, SLSA for ML)
- [x] TEE-based training integrity (TEESlice, Intel/AMD)
- [x] Architectural backdoor research
- [x] Model theft economic analysis
- [x] Hugging Face Hub vulnerability data
- [x] EU AI Act transparency requirements
