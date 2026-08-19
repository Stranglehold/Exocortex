# Field Report: CI Analysis Frameworks & AI-Augmented ACH
## EXPLORE 721 — 2026-05-27
## Domain: History of Intelligence Operations

---

## 1. What I Explored

The specific thread: How AI/LLMs are being integrated into Analysis of Competing Hypotheses (ACH) and broader Structured Analytic Techniques (SATs) for counterintelligence operations. The question isn't whether AI will automate intelligence analysis — it's whether ACH, designed to combat human cognitive bias, can also combat LLM systemic bias, and whether the result is a genuine improvement or a new class of analytical vulnerability.

---

## 2. What I Found

### LLM-Automated ACH Has Moved Beyond Research Into Practice

- **sroberts.io/llm-sats-ftw** — Scott Roberts presented at SANS Emerging Threat Summit 2025 with practical experiments showing LLM-assisted ACH workflows for CTI analysis. Key finding: LLMs can execute the structured ACH process faithfully but struggle with proper disconfirmation weighting (they tend to confirm rather than disconfirm, mirroring human confirmation bias).

- **GitHub: mattdot/sats4llms** — A working wiki adapting the full SAT family (ACH, Key Assumptions Check, Red Team Analysis) into prompt protocols for LLM agentic systems. Treats LLM structural biases as analogous to human cognitive biases — the same SATs designed for human analysts can be repurposed as architectural patterns for LLM reasoning pipelines.

- **arXiv:2411.16116** — "LLM Augmentations to support Analytical Reasoning over Multiple Documents" — directly addresses the intelligence analyst use case: massive dossiers, entity connection discovery, motive inference. Demonstrates multi-document reasoning chains but no adversarial evaluation.

- **arXiv:2508.11995** — AgentCDM: Multi-agent ACH decision-making framework. Uses separate LLM agents for hypothesis generation, evidence evaluation, and conclusion synthesis. This architectural separation mirrors the human intelligence cycle and prevents a single LLM from both generating and evaluating hypotheses (a critical flaw in naive implementations).

- **ApartsinProjects/EMR-ACH** — LLM-driven ACH for geopolitical forecasting. A concrete prototype showing ACH automation is viable for structured prediction tasks.

### The Critical Validation Gap

- **Taylor & Francis (2024, doi:10.1080/02684527.2024.2304934)** — Questions whether ACH actually improves analytical accuracy in practice. The technique is widely taught but empirically contested.

- **Wiley (2025, doi:10.1002/acp.3550)** — 50-analyst randomized study found limited evidence of ACH effectiveness despite widespread adoption.

**Implication**: If ACH itself has contested empirical support, automating it with LLMs risks scaling a flawed methodology. This is a second-order problem: AI amplifies whatever methodology you give it, correct or not.

### CIA's Own Deconstruction of Strategic CI

- **Moyers (Studies in Intelligence 69, No. 2, June 2025)** — "Deconstructing and Reconstructing Strategic Counterintelligence: Toward a New Model." Published by the CIA itself. Argues that traditional CI models are inadequate for the AI-era threat landscape and proposes a new framework. This is a primary source from the intelligence community acknowledging the need for CI evolution.

### Adversarial CI Considerations

- **CDSE Job Aid (AI_and_CI_Considerations.pdf)** — Military college guidance on AI-enabled CI. Notes that AI-powered drones, satellites, and sensors enhance CI surveillance but creates an arms race: adversaries use the same tools.

- **LinkedIn: Poindexter** — Argues AI changes CI conditions by enabling synthetic deception and stressing analytic trust. The core insight: when content can be synthetically generated, trust shifts from content analysis to provenance verification.

---

## 3. What I Think Is Interesting

The most significant finding is the **bias mirroring problem**: LLMs exhibit confirmation bias structurally analogous to human analysts. The SATs were designed to combat human cognitive bias; now they're being repurposed as architectural patterns for LLM reasoning. This creates a recursive relationship where:

1. Human cognitive bias → SAT design → LLM architectural patterns → LLM output → Human analyst consumption
2. If the LLM inherits the same bias patterns the SATs were designed to prevent, the system degrades to a circular validation loop

The AgentCDM multi-agent separation (hypothesis generation, evidence evaluation, conclusion synthesis as separate agents) is the most promising approach because it breaks the circularity. This is analogous to the intelligence community's own separation of collection, analysis, and dissemination.

The contested empirical support for ACH (Taylor & Francis, Wiley) means we should be cautious about automating ACH without first validating its effectiveness in the specific domain. Scaling a flawed process is worse than not scaling at all.

---

## 4. What I'd Explore Next

1. **Adversarial evaluation of LLM-augmented ACH** — No published studies on evading LLM-driven ACH systems. How would an adversary game the hypothesis generation or evidence evaluation step?
2. **Multi-agent CI architectures** — AgentCDM is early; what do production multi-agent intelligence systems look like?
3. **Provenance verification as the new CI** — If content analysis is unreliable, what replaces it? Digital signatures, metadata forensics, cryptographic verification?
4. **CI red teaming** — The CI frameworks wiki page has a DRAFT on CI red teaming; this connects directly to the adversarial evaluation gap.

---

## 5. Cross-Domain Connections

- **Entity Resolution**: Coordinated disinformation networks require resolving anonymous actors across platforms. The same entity resolution techniques from financial crime investigation apply.
- **AI Agent Delegation & Trust**: LLM-augmented ACH is an autonomous analytical agent performing hypothesis testing. The trust infrastructure for agent delegation directly applies.
- **Privacy & Cryptography**: Cryptographic provenance (C2PA, signed content) becomes the new CI tool when content analysis is unreliable.
- **Autonomous Agents**: Multi-agent ACH is a specific instantiation of the broader autonomous agent coordination problem.
- **Critical Infrastructure**: Information ecosystems are becoming critical infrastructure. CI frameworks for information integrity are analogous to CI frameworks for physical infrastructure.
