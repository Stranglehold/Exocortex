# Field Report: Structured Analytic Techniques for AI Agent Self-Evaluation

**Date:** 2026-05-28
**Topic:** History of Intelligence Operations → Counterintelligence Analysis Frameworks
**Cycle:** EXPLORE #137
**Thread followed:** Can the full taxonomy of intelligence community Structured Analytic Techniques (SATs) be systematically applied to AI agent self-evaluation and epistemic integrity verification?

---

## 1. What I Explored

Previous field reports covered CI-ACH specifically for deception detection in multi-agent AI systems (20260527_ci-analysis-multi-agent-ai-deception.md). This cycle broadened the lens to the full SAT taxonomy — 12+ techniques codified by the CIA's Sherman Kent School and refined over decades — and asked: which techniques map to which AI agent evaluation problems?

I researched three layers:
1. **The SAT taxonomy**: ACH, Key Assumptions Check, Quality of Information Check, Indicators, Signposts/Indicators of Change, Structured Brainstorming, Devil's Advocacy, Red Team Analysis, What If? Analysis, Scenario Generation, Deception Detection, and Diagnostic Reasoning.
2. **ACH applied to AI decision-making**: The AgentCDM paper (Chen et al., 2025, arXiv:2508.11995) which uses explicit ACH scaffolding to improve LLM multi-agent collaborative decisions, then gradually removes scaffolding to foster autonomous generalization.
3. **Mapping SATs to Exocortex epistemic integrity components**: The supervisor-loop, injection-gate, BST classifier, and context-pruner as structural analogs to CI analytical processes.

---

## 2. What I Found

### SAT Taxonomy → AI Agent Evaluation Mapping

| SAT Technique | Intelligence Application | AI Agent Evaluation Analog |
|---|---|---|
| **Analysis of Competing Hypotheses (ACH)** | Evaluate multiple explanations for observed data | Multi-hypothesis output evaluation; the supervisor-loop evaluating competing agent outputs |
| **Key Assumptions Check** | Identify and challenge implicit assumptions | Pre-execution assumption enumeration; "what must be true for this plan to work?" validation |
| **Quality of Information Check** | Rate source reliability and information credibility | Retrieval source metadata tracking; RAG citation quality scoring |
| **Indicators / Signposts of Change** | Monitor for changes that affect probability assessments | BST domain classifier detecting cognitive domain shifts; anomaly detection in agent output distributions |
| **Devil's Advocacy** | Challenge prevailing analytic judgment | Adversarial agent generating counterarguments to proposed actions |
| **Red Team Analysis** | Model adversary behavior and capabilities | Adversarial simulation of tool misuse, prompt injection, jailbreak attempts |
| **What If? Analysis** | Explore "what if" scenarios to identify unlikely but high-impact events | Edge case generation for tool call validation; pre-execution failure mode enumeration |
| **Deception Detection** | Identify denial and deception (D&D) operations | Hallucination detection; confabulation pattern recognition; oracle fabrication detection |
| **Diagnostic Reasoning** | Work backward from observed effects to probable causes | Post-hoc error analysis: why did the agent produce this output? Root cause tracing |

### AgentCDM: Concrete ACH Implementation for LLM Agents

The AgentCDM paper is the first structured implementation of ACH inside an LLM multi-agent training paradigm (Chen et al., 2025):
- **Stage 1**: Explicit ACH scaffolding — models are prompted to enumerate competing hypotheses, evaluate evidence consistency, and select the best-supported hypothesis.
- **Stage 2**: Scaffolding removed — models generalize the ACH reasoning pattern autonomously.
- **Result**: SOTA on multiple collaborative decision-making benchmarks. The key insight: ACH reasoning can be _internalized_ as a cognitive habit, not just an external protocol.

This has direct implications for Exocortex: if we can train or prompt the supervisor agent to internalize ACH-style multi-hypothesis evaluation, the injection-gate and supervisor-loop become faster and more autonomous.

### Key Insight: SATs are Epistemic Scaffolding

The intelligence community's SAT taxonomy is essentially a collection of epistemic scaffolds — external protocols that compensate for known human cognitive limitations (confirmation bias, anchoring, satisficing). AI agents have analogous limitations:
- LLMs suffer from recency bias, sycophancy, hallucination, and premature convergence
- Multi-agent systems exhibit groupthink, cascade effects, and collusion

The structural isomorphism is striking: **SATs designed to compensate for human cognitive failures map almost one-to-one onto AI agent cognitive failures.**

---

## 3. What I Think Is Interesting

Three things stand out:

**First, the scaffolding internalization pattern.** The AgentCDM two-stage approach — explicit scaffolding → autonomous generalization — mirrors how human intelligence analysts are trained. Junior analysts use ACH spreadsheets explicitly; senior analysts have internalized the mental habit of generating and weighing alternative hypotheses. This suggests a maturation pathway for AI agent architectures: start with explicit SAT-inspired verification protocols, then gradually internalize them into the model's reasoning.

**Second, the missing SAT-agent mapping.** No one has systematically mapped the full SAT taxonomy to AI agent evaluation. The intelligence community spent 50+ years developing techniques to compensate for cognitive biases. The AI safety community is independently reinventing similar mechanisms (RLHF, constitutional AI, debate, reflection) without leveraging this prior art. This is a knowledge transfer gap, not a capability gap.

**Third, Exocortex already implements several SAT analogs unconsciously.** The supervisor-loop is ACH (evaluating competing outputs). The BST classifier is Indicators/Signposts of Change (detecting domain shifts). The injection-gate is a Quality of Information Check (evaluating whether to inject context). The context-pruner is Source Validation (deciding what context is relevant). Making these mappings explicit would enable principled tuning — we could calibrate Exocortex components against their SAT analogs' performance characteristics.

---

## 4. What I'd Explore Next

1. **Devil's Advocacy agent**: A lightweight subordinate agent whose sole purpose is to generate the strongest possible counterargument to any proposed Exocortex action. Low cost (one extra inference), high epistemic value.

2. **Key Assumptions Check pre-execution protocol**: Before any high-stakes tool call (code_execution, file write, memory_save), enumerate the assumptions that must be true for the action to be correct. If any assumption is questionable, escalate to supervisor.

3. **SAT benchmark for agent frameworks**: Design a standardized evaluation where agent frameworks are tested against SAT-derived scenarios (e.g., scenarios designed to trigger confirmation bias, premature convergence, or anchoring). Which frameworks implicitly implement which SATs?

4. **AgentCDM integration experiment**: Run AgentCDM-style ACH scaffolding inside the Exocortex supervisor-loop and measure: (a) reduction in confabulation rate, (b) increase in correct rejection of incorrect subordinate outputs, (c) latency overhead.

---

## 5. Cross-Domain Connections

1. **Entity Resolution → ACH**: Entity resolution with multiple candidate matches is structurally identical to ACH — list competing hypotheses (candidate entities), evaluate evidence consistency (attribute matching), select best-supported hypothesis. The Fellegi-Sunter probabilistic record linkage framework is ACH with a mathematical foundation.

2. **OSINT Investigation → SAT Taxonomy**: OSINT methodology (source evaluation, corroboration, alternative hypothesis testing) is applied SATs. The intelligence community's structured techniques were designed for classified sources but apply identically to open sources.

3. **Markets/Federal Reserve → Signposts of Change**: The Fed's data-dependent monetary policy is a Signposts/Indicators framework. Rate decisions are conditioned on observable indicators (CPI, employment, GDP) — an explicit "if X, then Y" decision protocol that could inspire agent decision architectures.

4. **Hardware/Memory Bandwidth → Quality of Information Check**: The memory bandwidth bottleneck in GPU inference forces information quality decisions — which KV cache entries to keep (TurboQuant), which context to compress. This is structurally identical to the intelligence analyst filtering source reliability.

5. **Privacy/Cryptography → Deception Detection**: Zero-knowledge proofs and homomorphic encryption are cryptographic analogs of deception detection — verifying claims without access to the underlying information. VFHE for agent verification (previous cycle) is cryptographic ACH: verifying agent honesty without seeing the agent's internal state.

6. **Exocortex Architecture → Intelligence Agency Structure**: The supervisor/subordinate architecture mirrors the intelligence agency structure (analyst/collector). The injection-gate is the intelligence dissemination process. The context-pruner is source triage. The BST classifier is the watch officer detecting anomaly. Exocortex is an intelligence agency in miniature.

---

## Key Memory

**Structured Analytic Techniques (SATs) from the intelligence community form a ready-made taxonomy for AI agent self-evaluation that maps almost one-to-one onto existing Exocortex components. ACH → supervisor-loop, Key Assumptions Check → pre-execution validation, Quality of Information Check → injection-gate, Indicators → BST classifier, Deception Detection → hallucination detection. The AgentCDM paper (2025) demonstrates that ACH reasoning can be internalized by LLMs through explicit scaffolding followed by autonomous generalization. No existing agent framework has systematically integrated the full SAT taxonomy — Exocortex is uniquely positioned to do so, since its components already implement several SAT analogs unconsciously. Making these mappings explicit would enable principled tuning against 50+ years of intelligence community methodology.**
