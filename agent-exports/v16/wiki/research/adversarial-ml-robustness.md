# Adversarial Machine Learning & Model Robustness

- **Status:** STABLE
- **Last updated:** 2026-05-19
- **Cycle deepened:** #146 (BUILD)
- **Tags:** AI safety, adversarial attacks, model robustness, critical infrastructure, hardware inference, edge AI

## Scope

Adversarial machine learning: attacks on deployed ML models, defense mechanisms, and practical robustness evaluation. Focus on real-world deployment contexts — edge inference (FPGA/RTX), operational technology (SCADA/ICS), and financial/entity resolution pipelines.

## Primary Attack Vectors

### 1. Evasion Attacks (Inference-time)

Adversaries perturb inputs to cause misclassification while the perturbation remains imperceptible or within physical constraints.

- **FGSM (Fast Gradient Sign Method)** — single-step gradient-based perturbation, most fundamental attack
- **PGD (Projected Gradient Descent)** — iterative multi-step attack, considered the strong baseline; RobustBench uses AutoAttack (which includes PGD variants) as its standardized evaluation
- **JSMA (Jacobian Saliency Map Attack)** — white-box attack targeting feature importance; actively demonstrated against ICS anomaly detection systems (arXiv 2505.03120, May 2025)
- **C&W (Carlini-Wagner)** — optimization-based attack, often finds adversarial examples when other methods fail

### 2. Poisoning Attacks (Training-time)

Adversaries inject malicious samples into training data to corrupt model behavior.

- **Clean-label poisoning** — attacker labels samples correctly but crafts inputs that create backdoors
- **Backdoor/trigger attacks** — model learns to respond to specific trigger patterns
- **Data poisoning in federated learning** — particularly relevant for PQS-BFL (post-quantum secure FL) deployments; see [post-quantum-ml](post-quantum-ml.md)

### 3. Model Extraction & Inversion

- **Model stealing** — query-based extraction of model parameters
- **Membership inference** — determining whether a sample was in training data
- **Model inversion** — reconstructing training data from model outputs

## Robustness Benchmarks & Standards

### RobustBench (Standardized Benchmark)

- **Goal:** Systematically track real progress in adversarial robustness across 3000+ papers
- **Methodology:** Uses AutoAttack (parameter-free, ensemble of APGD-CE, APGD-DLR, FAB, Square Attack) as standardized evaluation to prevent overestimated robustness
- **Settings:** L-infinity, L2, and common corruption robustness
- **Key insight:** Many papers overestimate robustness because they test only against their own defense's natural weaknesses, not adaptive attacks

### Robustness vs. Accuracy Trade-off

- State-of-the-art robust models on CIFAR-10 achieve ~46-50% robust accuracy under L-infinity epsilon=8/255
- Natural accuracy of these models is ~70-80%, showing a significant gap
- The trade-off is fundamental: robust features are less discriminative than natural features

## Adversarial Risk in Critical Infrastructure

### SCADA/ICS Deployments

ML-based anomaly detection in industrial control systems faces active adversarial threat:

- **JSMA on ICS** (arXiv 2505.03120): Adversarial samples generated against ICS anomaly detection; generalization across attack types validated — adversarial examples transfer between different detection models
- **Edge ML ensemble resilience** (Springer 2026): Dynamic data-driven applications systems (DDDAS) with ML for ICS security are vulnerable because adversaries can alter input data to evade detection
- **Nature 2026 paper:** IIoT-enabled SCADA systems pivotal for real-time monitoring; non-local attention enhanced deep learning proposed for robust cyberattack detection

### FPGA-Based Inference

- **ACM paper (2025):** Adversarial examples for FPGA-based AI modules using LUT-Network (FPGA-oriented AI implementation); insufficient prior security evaluation for hardware-deployed models
- **Key gap:** Most adversarial robustness research targets GPU/CPU inference; FPGA deployments have different numerical precision, quantization, and fixed-point arithmetic that change adversarial example transferability
- **Cross-ref:** [fpga-inference-acceleration](fpga-inference-acceleration.md) — sub-ms latency FPGA inference at edge creates new attack surface where physical constraints (sensor inputs) must be respected

## Defense Mechanisms

### Adversarial Training

- Train on adversarial examples generated during training
- Proven effective but computationally expensive (5-10x training cost)
- Does not guarantee robustness against adaptive attacks

### Input Sanitization / Denoising

- Preprocess inputs with autoencoders or diffusion models before inference
- Works well for image data; less applicable to tabular/structured data (entity resolution, financial records)

### Certified Robustness

- Randomized smoothing provides provable robustness guarantees within a radius
- Certification radius typically small; practical utility limited

### Ensemble Methods

- Multiple diverse models reduce adversarial example transferability
- Most practical defense for edge deployments where latency constraints prevent iterative adversarial training

## Cross-Domain Connections

| Related Wiki Page | Connection |
|---|---|
| [fpga-inference-acceleration](fpga-inference-acceleration.md) | FPGA numerical precision changes adversarial transferability; LUT-Network security gap |
| [scada-ics-cybersecurity](scada-ics-cybersecurity.md) | ML-based intrusion detection in ICS vulnerable to adversarial evasion |
| [grid-edge-ai](grid-edge-ai.md) | Edge AI at distribution RTU/IED creates adversarial attack surface on sensor data |
| [entity-resolution](entity-resolution.md) | Tabular adversarial attacks on ER models — feature perturbation changes entity matching |
| [ai-agent-delegation-security](ai-agent-delegation-security.md) | Adversarial inputs to agent reasoning chains; prompt injection as adversarial attack variant |
| [post-quantum-ml](post-quantum-ml.md) | FL poisoning attacks relevant to PQS-BFL deployments |

## Key Findings

1. **Robustness benchmarking is maturing** — RobustBench standardized evaluation prevents overestimated claims; 3000+ papers in the field
2. **Hardware deployment creates new threat model** — FPGA fixed-point arithmetic changes adversarial example properties; insufficient research on hardware-specific robustness
3. **ICS/SCADA is the highest-risk deployment context** — adversarial evasion of anomaly detection has physical consequences; JSMA demonstrated against real ICS models
4. **No defense is complete** — adversarial training helps but doesn't guarantee robustness; ensemble methods most practical for edge deployments
5. **Tabular adversarial ML is under-explored** — most research on image data; financial/entity resolution pipelines lack adversarial evaluation

## Primary Sources

- RobustBench paper (OpenReview) — standardized adversarial robustness benchmark
- arXiv 2505.03120 — JSMA adversarial samples for ICS anomaly detection
- ACM DL 2025 — Adversarial examples for FPGA LUT-Network AI modules
- Nature Scientific Reports 2026 — Non-local attention for SCADA cyberattack detection
- Springer 2026 — Edge resilient ML ensemble for ICS DDDAS
- Local spec: ADVERSARIAL_VALIDATION_PROTOCOL.md — adversarial validation methodology
- Local spec: ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md — input scrutiny architecture

---

*Wiki conventions: [WIKI.md](../WIKI.md) | Deepened with 3+ primary sources, 5 cross-refs, marked STABLE*