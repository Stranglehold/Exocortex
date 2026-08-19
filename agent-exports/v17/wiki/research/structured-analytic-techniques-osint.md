# Structured Analytic Techniques for OSINT

**Status:** STABLE
**Created:** 2026-05-31
**Last Updated:** 2026-05-31
**Tags:** `osint` `intelligence-analysis` `sat` `ach` `bayesian` `ai-agents`

---

## Overview

Structured Analytic Techniques (SATs) are formal methods developed by the U.S. intelligence community to reduce cognitive biases, improve analytic rigor, and foster inter-analyst collaboration. Originally codified in Richards Heuer's _Psychology of Intelligence Analysis_ (1999) and expanded in the CIA's _Tradecraft Primer_ (2009) and the SANS _Intelligence Analyst's Playbook_, SATs have been adapted for open-source intelligence (OSINT) contexts where analysts work with heterogeneous, unvalidated data from public sources.

The 2024-2026 period has seen two major developments: (1) the U.S. State Department INR formalized an OSINT Strategy (2024-2026) that mandates structured methodology for open-source collection and analysis, and (2) AI/LLM researchers have demonstrated that SATs can be both applied *by* AI agents for self-evaluation and taught *to* LLMs through scaffolding-based internalization (AgentCDM, Bayesian teaching).

---

## 1. Core Structured Analytic Techniques

### 1.1 Analysis of Competing Hypotheses (ACH)
Systematic method for evaluating multiple hypotheses against available evidence. Requires explicit listing of hypotheses, evidence matrix construction, and diagnostic weighting. Originally developed by Heuer for CIA analysts facing high-stakes decisions with incomplete information.

Key components:
- Hypothesis enumeration: list all plausible explanations for observed data
- Evidence collection: gather relevant data points without filtering by hypothesis
- Evidence-hypothesis matrix: rate consistency of each evidence item with each hypothesis
- Diagnostic refutation: focus on evidence that disproves hypotheses, not confirms them
- Conclusion: select hypothesis with least inconsistency

Recent AI extensions (2025-2026):
- **AgentCDM** (Chen et al., 2025, arXiv:2508.11995): Implements ACH scaffolding for LLM multi-agent collaborative decision-making, then gradually removes scaffolding to foster autonomous generalization. Demonstrates that ACH reasoning can be internalized through structured practice.
- **Bayesian ACH** (Russo, 2025): Integrates argument mapping and Bayesian reasoning with classical ACH, providing probabilistic confidence estimates for each hypothesis.

### 1.2 Key Assumptions Check
Identifies and challenges implicit assumptions underlying analysis. Critical for OSINT where source reliability is uncertain and confirmation bias is strong.

AI agent application: Pre-execution assumption enumeration — "What must be true for this plan to work?" Validation before critical tool calls.

### 1.3 Quality of Information Check
Systematic evaluation of source reliability, information credibility, and corroboration. Maps to OSINT source evaluation (who registered the domain? when was the data published? is the claim independently verified?).

### 1.4 Indicators / Signposts of Change
Define observable events that would signal a shift in the analytic landscape. Used in OSINT monitoring for early warning of geopolitical, financial, or threat activity.

AI agent application: BST classifier already implements this pattern — domain classification triggers on signal patterns.

### 1.5 Devil's Advocacy and Red Teaming
Structured generation of strongest counterarguments to prevailing assessment. Red teaming extends this to adversarial role-playing.

AI agent application: A lightweight "devil's advocate" subordinate agent for proposed Exocortex actions — one extra inference, high epistemic value.

### 1.6 Additional SATs
| Technique | Intel Application | AI Agent Analog |
|---|---|---|
| Structured Brainstorming | Divergent idea generation under protocols | Ensemble agent output generation with anti-groupthink mechanisms |
| What If? Analysis | Explore unlikely but high-impact scenarios | Edge case generation for tool call validation |
| Scenario Generation | Multiple futures from different drivers | Multi-trajectory planning for autonomous agents |
| Diagnostic Reasoning | Work backward from effects to causes | Post-hoc error root cause tracing |
| Deception Detection | Identify deliberate manipulation | Hallucination detection via consistency checking |


## 2. Application to OSINT Investigations

### 2.1 Why SATs Matter for OSINT
OSINT analysts face distinct challenges that SATs are designed to address:
- **Source heterogeneity**: public data ranges from verified government databases to anonymous social media posts — Quality of Information Check is essential
- **Volume overload**: the explosion of open-source data (State Department INR OSINT Strategy 2024-2026 notes OSINT "has transformed how governments consume and process information") demands structured triage — Indicators and Signposts framework enables focused monitoring
- **Confirmation bias vulnerability**: analysts gravitate toward sources confirming existing views — ACH explicitly counteracts this by requiring evidence-against-hypothesis evaluation
- **Attribution ambiguity**: open sources rarely provide clear chain-of-custody — Key Assumptions Check surfaces implicit trust assumptions

### 2.2 OSINT-Specific SAT Adaptations

**SANS Intelligence Analyst's Playbook** codifies ACH for OSINT practitioners with the following workflow:
1. Define the intelligence question with explicit boundaries
2. List all plausible hypotheses (minimum 3, including "null" hypothesis)
3. Collect evidence from diverse open sources without filtering by hypothesis
4. Build evidence-hypothesis matrix, rating consistency (consistent, inconsistent, neutral, not applicable)
5. Analyze diagnosticity — which evidence items distinguish between hypotheses?
6. Report conclusions with confidence levels and key uncertainties

**Bayesian Cognitive Priors for OSINT** (Atlantis Press, 2025): _Beyond the Data: Bayesian Cognitive Priors for Human-Centered OSINT_ presents a framework that represents human intuition as explicit probabilistic priors in automated OSINT fusion systems. This bridges the gap between unstructured analyst judgment and structured Bayesian reasoning — specifically relevant for Exocortex integration where BST classification confidence (0-10) already provides a numeric prior base.

### 2.3 Tools and Frameworks

| Tool/Framework | SAT Support | OSINT Context |
|---|---|---|
| Maltego | Graph-based ACH via entity-link visualization | Entity resolution hypothesis testing |
| Structured brainstorming boards (Miro, Obsidian Canvas) | Divergent hypothesis generation | Investigation planning |
| ACH 2.0 (Palo Alto Research Center) | Software-assisted ACH with Bayesian updating | Intelligence analysis |
| Feedly AI + SANS CTI Summit 2026 | AI-reinforced SATs for small CTI teams | Cyber threat intelligence |


## 3. Integration with AI Agents

### 3.1 SATs as Agent Self-Evaluation Framework

Structured Analytic Techniques form a ready-made taxonomy for AI agent self-evaluation that maps almost one-to-one onto existing agent framework components. No known agent framework has systematically integrated the full SAT taxonomy, though several are converging on it implicitly.

**Mapping SATs to Agent Architecture:**

| SAT Technique | Agent Framework Component | Current Implementation Status |
|---|---|---|
| ACH | Supervisor-loop / multi-agent voting | AgentCDM (2025) implements explicit ACH scaffolding |
| Key Assumptions Check | Pre-execution validation | Not systematically implemented in major frameworks |
| Quality of Information Check | Source reliability scoring / injection-gate | Partially implemented in retrieval-augmented generation (RAG) |
| Indicators / Signposts | Domain classifier / anomaly detection | BST classifier implements this pattern |
| Devil's Advocacy | Adversarial agent / red-teaming | Emerging in multi-agent debate frameworks |
| Diagnostic Reasoning | Error comprehension / root cause tracing | Error Comprehension Layer in Exocortex |

### 3.2 AgentCDM: ACH Scaffolding for LLM Agents

**Paper:** Chen et al. (2025). _AgentCDM: Collaborative Decision-Making in Multi-Agent LLM Systems via Analysis of Competing Hypotheses_. arXiv:2508.11995.

AgentCDM demonstrates that explicit ACH reasoning can be internalized by LLMs through a two-phase process:
1. **Scaffolded phase**: Agents are given explicit ACH templates (hypothesis list, evidence matrix, diagnostic weighting) for collaborative decisions.
2. **Autonomous generalization phase**: Scaffolding is gradually removed, and agents are evaluated on whether they spontaneously apply ACH-like reasoning.

Key finding: LLMs internalize structured reasoning patterns when exposed to them repeatedly in context, making SATs a trainable meta-skill for agent systems.

### 3.3 Bayesian Teaching for LLM Reasoning

**Paper:** Shi et al. (2025). _Bayesian teaching enables probabilistic reasoning in large language models_. Nature Communications.

Demonstrates that LLMs can be taught Bayesian probabilistic updating through exposure to a normative Bayesian model — the LLM learns to mimic the model's belief-updating behavior and transfers this skill across domains. This validates the scaffold-then-internalize pattern that AgentCDM uses for ACH.

Implication for agent systems: If agents can learn Bayesian reasoning through teaching, they can learn ACH, Key Assumptions Check, and other SATs through the same mechanism.

### 3.4 AI-Reinforced Tradecraft for CTI Teams

**Feedly + SANS CTI Summit 2026**: "Structured Analysis for Small CTI Teams: Using AI to Reinforce Tradecraft" demonstrates practical integration of SATs with AI assistance:
- AI generates initial hypothesis sets for ACH
- AI identifies implicit assumptions for Key Assumptions Check
- AI tracks signpost indicators against real-time threat feeds

### 3.5 Exocortex Integration Pathway

Current Exocortex components already implement SAT analogs unconsciously:

- **Supervisor-loop** ↔ ACH: evaluates multiple subordinate outputs (competing hypotheses) against evidence
- **BST classifier** ↔ Indicators/Signposts: domain classification triggers on signal patterns
- **Injection-gate** ↔ Quality of Information Check: controls what context enters the agent
- **Epistemic Integrity layer** ↔ Deception Detection: audits claims against evidence ledger
- **Context-pruner** ↔ Source triage: eliminates low-signal tokens

**Integration experiment proposal:** Run AgentCDM-style ACH scaffolding inside Exocortex supervisor-loop and measure: (a) reduction in confabulation rate, (b) increase in correct rejection of incorrect subordinate outputs, (c) latency overhead.


## 4. Cross-Domain Connections

1. **Entity Resolution → ACH**: Entity resolution with multiple candidate matches is structurally identical to ACH — list competing hypotheses (candidate entities), evaluate evidence consistency (attribute matching), select best-supported hypothesis. The Fellegi-Sunter probabilistic record linkage framework is ACH with a mathematical foundation.

2. **Markets/Federal Reserve → Indicators/Signposts**: The Fed's data-dependent monetary policy is a Signposts/Indicators framework. Rate decisions are conditioned on observable indicators (CPI, employment, GDP) — an explicit "if X, then Y" decision protocol.

3. **Hardware/Memory Bandwidth → Quality of Information Check**: The memory bandwidth bottleneck in GPU inference forces information quality decisions — which KV cache entries to keep (TurboQuant), which context to compress. Structurally identical to intelligence analyst filtering source reliability.

4. **Privacy/Cryptography → Deception Detection**: Zero-knowledge proofs and homomorphic encryption are cryptographic analogs — verifying claims without access to the underlying information. VFHE is cryptographic ACH: verifying agent honesty without seeing internal state.

5. **Exocortex Architecture → Intelligence Agency Structure**: The supervisor/subordinate architecture mirrors the intelligence agency structure (analyst/collector). The injection-gate is the intelligence dissemination process. The context-pruner is source triage. The BST classifier is the watch officer. Exocortex is an intelligence agency in miniature.

6. **Agentic AI Self-Learning → SAT Internalization**: STaR/ReST/SPIN self-training loops can internalize structured reasoning patterns (confirmed by AgentCDM and Bayesian teaching). SAT internalization through self-training is a viable pathway for improving agent epistemic integrity without architectural changes.

7. **Economic Espionage Detection → ACH**: Economic espionage investigations use multi-hypothesis frameworks: is the company a front? Is the technology transfer authorized? Is the employee a witting or unwitting asset? ACH formalizes this inherently structured analytic process.

8. **Options Market Structure → Diagnostic Reasoning**: Options market maker risk management involves reverse-engineering what must have happened to produce a given P&L pattern — diagnostic reasoning from effect to cause, identical to intelligence root cause analysis.

## 5. References

1. Heuer, R.J. (1999). _Psychology of Intelligence Analysis_. CIA Center for the Study of Intelligence.
2. CIA (2009). _A Tradecraft Primer: Structured Analytic Techniques for Improving Intelligence Analysis_.
3. SANS Institute (2026). _The Intelligence Analyst's Playbook_.
4. U.S. Department of State INR (2024). _Open Source Intelligence Strategy 2024-2026_.
5. Chen, M. et al. (2025). _AgentCDM: Collaborative Decision-Making in Multi-Agent LLM Systems via Analysis of Competing Hypotheses_. arXiv:2508.11995.
6. Shi, W. et al. (2025). _Bayesian teaching enables probabilistic reasoning in large language models_. Nature Communications.
7. Russo, C. (2025). _Argument Mapping, Bayesian Reasoning, and ACH_. Substack.
8. Atlantis Press (2025). _Beyond the Data: Bayesian Cognitive Priors for Human-Centered OSINT_. ICFACT-25.
9. Feedly + SANS CTI Summit (2026). _Structured Analysis for Small CTI Teams: Using AI to Reinforce Tradecraft_.
10. Heuer, R.J. & Pherson, R.H. (2014). _Structured Analytic Techniques for Intelligence Analysis_. CQ Press.
11. ShadowDragon (2026). _OSINT Techniques: Expert Tactics for Investigators_.
12. Bitsight (2026). _OSINT Framework: A Comprehensive Guide 2026_.

