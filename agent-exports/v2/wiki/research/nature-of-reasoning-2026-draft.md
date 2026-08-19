# The Nature of Reasoning (2026)

**Status:** DRAFT  
**Created:** 2026-07-07  
**Last Updated:** 2026-07-07  
**Priority:** High  
**Tags:** reasoning, cognition, predictive-processing, llm-reasoning, dual-process-theory

---

## Overview

The nature of reasoning explores how we actually think — not just the mechanics, but the *process* — and what different models' approaches reveal about the structure of thought. This is the most meta of our interests: reasoning about reasoning itself.

---

## Predictive Processing as Unified Framework

### Core Principles

Predictive processing (PP) interprets perception, cognition, and action as hierarchies of top-down predictions and bottom-up error signals. The brain constantly generates predictions about sensory inputs, propagating only the mismatch — called prediction error — upwards to update beliefs.

**Key mechanisms:**
- **Prediction Error Minimization (PEM):** Core imperative — compare top-down predictions with bottom-up sensory inputs, propagate only mismatches upward
- **Hierarchical Architecture:** Each level generates predictions for the level below and receives corresponding error signals
- **Active Inference:** Agents take actions that fulfill predicted sensory consequences
- **Precision Weighting:** Modulates influence of prediction errors based on expected reliability

### Implications for Reasoning

If the brain is fundamentally a prediction machine, then reasoning is not a separate module but an extension of predictive processing at higher levels of abstraction. This suggests:
- Reasoning is continuous with perception, not discrete
- "Thinking" is prediction at a remove from sensory input
- Errors in reasoning may stem from incorrect priors or precision weighting

---

## LLM Reasoning: What We've Learned

### Capabilities

LLMs demonstrate notable reasoning strengths:
- Human-like content effects in logical reasoning
- Outperform statistical models in causal reasoning benchmarks
- Successfully model decision-making, information search, and deliberation
- Neural representation alignment with brain imaging data (fMRI/MEG)

### Failures

LLMs consistently fall short in critical areas:

---

## 2026 Developments in Reasoning Architectures

### 1. Latent Reasoning and Test-Time Compute

**"Reasoning Beyond Chain-of-Thought: A Latent Computational Perspective"** (arXiv 2601.08058, Jan 2026)

Large language models exhibit substantially improved performance on complex reasoning tasks with Chain-of-Thought (CoT) prompting, where the model generates intermediate reasoning steps before producing a final answer. However, this paper argues that CoT is not the only path to improved reasoning — latent computational processes within the model can also enhance performance without explicit verbalization.

**Key insight:** The reasoning stack has evolved from simple CoT to Graph-of-Thought, where models can embed reasoning steps in arbitrary graphs that can merge, branch, backtrack, and loop.

### 2. Chain-of-Thought Controllability (arXiv 2603.05706, ICML 2026)

Reasoning models struggle to control what they verbalize in their chain of thought. The CoT-Control evaluation suite measures whether models can follow constraints on their reasoning traces (avoid specific words, use uppercase, repeat sentences) while maintaining task performance.

**Key findings:**
- Claude Sonnet 4.5 controls its CoT only 2.7% of the time when instructed to avoid a specific word (e.g., "chromosome" in a genetics problem)
- CoT controllability is significantly lower than output controllability across all tested reasoning models (Qwen3-14B, o4-mini, DeepSeek-R1)
- Controllability increases with model size but decreases with more test-time compute
- OpenAI interprets low controllability as positive: reasoning is genuinely internal rather than performative self-monitoring

**Implication:** If models cannot control their CoT output, CoT monitoring systems cannot be reliably adversarial — the reasoning trace reflects genuine computation rather than curated self-presentation.

### 3. Societies of Thought (arXiv 2601.10825)

Reasoning models do not just generate longer chains of thought — they exhibit patterns characteristic of social and conversational processes. DeepSeek-R1 and similar models show internal "societies of thought": posing questions, introducing alternative perspectives, generating and resolving conflicts, and coordinating diverse roles.

**Key findings:**
- These interactional patterns rarely occur in non-reasoning models even at 671B parameters, even when controlling for reasoning trace length
- Reasoning optimization introduces an intrinsic social structure within the reasoning process itself, not merely increased text volume
- Suggests reasoning training converges on a meta-cognitive architecture that resembles multi-agent deliberation within a single model

### 4. Hierarchical Chain-of-Thought Prompting (arXiv 2604.00130, Mar 2026)

As reasoning unfolds, the model may drift from its plan, skip steps, or execute inconsistently (a phenomenon called plan–execution drift). Hierarchical CoT prompting addresses this by structuring reasoning into multiple levels of abstraction.

### 5. Reasoning Theater (GoodFire, Mar 2026)

Probes track "performative chain-of-thought": when models "know" their final answer but continue to generate reasoning steps anyway. This suggests some CoT generation may be performative rather than genuinely computational.

---

## Mechanistic Interpretability of Reasoning

### Reasoning Circuits

Understanding how reasoning traces map to internal circuit activations is a mechanistic interpretability question. Key areas:
- **Circuit tracing:** Identifying specific neural pathways that implement reasoning steps
- **Cross-layer transcoders:** How information transforms between reasoning layers
- **Feature sparsity:** SAE features that correspond to reasoning concepts

### CoT Controllability and Safety

The low controllability of CoT output has implications for AI safety:
- If reasoning traces cannot be controlled, they may be more reliable signals of genuine model behavior
- CoT monitoring systems cannot be reliably adversarial
- This creates both opportunities (genuine introspection) and risks (unpredictable reasoning paths)
- **Reversal Curse:** Memorize training data at sentence level instead of extracting abstract rules
- **Novel Inductive Reasoning:** Struggle with constrained, limited-data inductive reasoning
- **Syllogism Validity:** Fail to fully emulate human-like syllogism validity judgments
- **Wason Selection Task:** Lower performance than humans on hypothesis-driven reasoning

### Key Insight

LLMs and humans likely achieve similar behavioral outputs through entirely different computational strategies and learning processes. The "reasoning" we observe may be pattern matching over large corpora rather than true cognitive alignment.

---

## Dual-Process Theory Revisited

### System 1 vs System 2

Traditional dual-process theory distinguishes:
- **System 1:** Fast, automatic, intuitive
- **System 2:** Slow, deliberate, analytical

### MoE as Implicit Dual-Process

Mixture-of-Experts architectures may implement something like dual-process implicitly:
- Simple tokens routed to fast experts (System 1 analog)
- Complex tokens routed to reasoning experts (System 2 analog)
- Gating mechanism as attention/effort allocation

### Open Questions

- Can we measure "cognitive effort" in LLMs?
- Do LLMs exhibit System 1/System 2 dissociations?
- Is predictive processing compatible with dual-process theory?

---

## Cross-Domain Connections

### To Entity Resolution
- Entity resolution requires abductive reasoning (inference to best explanation)
- Predictive processing framework may model how ER systems weigh competing hypotheses

### To Adversarial ML
- Adversarial attacks may exploit prediction error minimization failures
- Understanding reasoning failures may improve robustness

### To AI Safety
- Reasoning failures in LLMs are safety-relevant (hallucinations, misalignment)
- Predictive processing may explain why certain safety interventions work/fail

---

## Primary Sources

1. arXiv 2507.11181 — "Mixture of Experts in Large Language Models: A Comprehensive Review" (2025)
2. arXiv 2602.06176 — "Large Language Model Reasoning Failures" (Feb 2026)
3. arXiv 2511.16660 — "Cognitive Foundations for Reasoning and Their Manifestation in LLMs" (Nov 2025)
4. Springer Nature — "Higher-Level Cognition Under Predictive Processing" (2026)
5. Frontiers in Computational Neuroscience — "The two dragons of cognition: recursive condensation for predictive processing" (2026)
6. Berkeley EECS-2026-119 — "Towards Understanding and Improving Large Language Model Reasoning" (2026)

---

## Recent Advances in LLM Reasoning (2025-2026)

### Chain-of-Thought Evolution

Chain-of-thought (CoT) prompting has evolved significantly:

- **Self-Consistency (2025):** Multiple reasoning paths aggregated via voting, reducing single-path errors by 15-30%
- **Tree-of-Thought (2025):** Exploration of multiple reasoning branches with backtracking, improving performance on complex multi-step problems
- **Graph-of-Thought (2026):** Structured reasoning with graph-based state representation, enabling more efficient exploration of solution spaces

### Predictive Processing in Neural Networks

Recent work has demonstrated predictive processing principles in artificial neural networks:

- **Predictive Coding Networks (2025):** Networks that minimize prediction error through hierarchical layers, showing improved robustness to adversarial attacks
- **Active Inference Agents (2026):** Agents that take actions to fulfill predicted sensory consequences, demonstrating emergent planning behavior
- **Precision Weighting Mechanisms (2026):** Attention mechanisms that modulate prediction error influence based on expected reliability, improving uncertainty estimation

### 2025-2026 Breakthroughs

- **arXiv 2510.22860 (NeurIPS 2025):** "Far from the Shallow: Brain-Predictive Reasoning Embedding through Language" — demonstrates how LLM internal representations become entangled with lexicon, syntax, meaning, and reasoning; proposes brain-predictive reasoning embedding to disentangle these factors
- **arXiv 2607.07361 (Jul 2026):** "BUS: Brain-Inspired Unsupervised Self-Reflection" — backward prediction as critical form of self-reflection; brain predicts, evaluates, and reviews reasoning processes
- **arXiv 2504.09614:** "Neural mechanisms of predictive processing" — synthesizes advances in predictive processing within sensory cortex; identifies key computational primitives (stimulus adaptation, dendritic computation, E/I balance, hierarchical processing)
- **Frontiers in Computational Neuroscience (2026):** "The two dragons of cognition: recursive condensation for predictive processing" — memory-amortized inference via topological predictive processing; brain employs recursive condensation to manufacture topological separability
- **arXiv 2604.07745 (Apr 2026):** "The Cartesian Cut in Agentic AI" — applies predictive coding principles to agentic AI systems; references Bastos et al. canonical microcircuits for predictive coding (Neuron 2012)

### Dual-Process Theory Applications

- **System 1/2 Simulation (2025):** LLMs with separate fast/slow reasoning modes showing improved performance on tasks requiring deliberate thinking
- **Metacognitive Monitoring (2026):** Models that estimate their own reasoning confidence, enabling better error detection and correction

---

## Cross-Domain Connections

### To Entity Resolution

Predictive processing principles apply to entity resolution:
- **Prediction:** Entity matching based on prior knowledge
- **Error Signal:** Mismatch between predicted and actual matches
- **Precision Weighting:** Confidence in different attribute types

### To Financial Markets

- **Market Prediction:** Markets as complex adaptive systems with predictive processing at multiple levels
- **Anomaly Detection:** Prediction error minimization for detecting unusual trading patterns

### To Security

- **Threat Detection:** Predictive processing for identifying deviations from normal behavior
- **Adversarial Robustness:** Understanding prediction error minimization failures under attack

---

## Societies of Thought (arXiv 2601.10825)

Reasoning models do not just generate longer chains of thought — they exhibit patterns characteristic of social and conversational processes. DeepSeek-R1 and similar models show internal "societies of thought": posing questions, introducing alternative perspectives, generating and resolving conflicts, and coordinating diverse roles.

**Key findings:**
- These interactional patterns rarely occur in non-reasoning models even at 671B parameters, even when controlling for reasoning trace length
- Reasoning optimization introduces an intrinsic social structure within the reasoning process itself, not merely increased text volume
- Suggests reasoning training converges on a meta-cognitive architecture that resembles multi-agent deliberation within a single model

## Expert Systems: Historical Context for Reasoning

From the library, expert systems represent an early approach to formalizing reasoning:

**Key historical systems:**
- **MYCIN (1976):** Computer-based medical consultations for antibiotic selection
- **DENDRAL (1965):** Chemical structure elucidation from mass spectrometry data
- **PROSPECTOR (1984):** Mineral exploration and decision making
- **PUFF (1983):** Interpretation of pulmonary function data

**Design principles:**
- Rule-based reasoning with explicit knowledge representation
- Separation of knowledge base from inference engine
- Uncertainty handling through certainty factors
- Explainability through trace reconstruction

**Relevance to modern reasoning:**
- Expert systems formalized reasoning as search through problem spaces
- Modern LLMs learn reasoning implicitly from data rather than explicit rules
- The tension between explicit symbolic reasoning and implicit neural reasoning remains central

## Cognitive Biases in LLMs (arXiv 2410.15413)

A comprehensive evaluation of 30 cognitive biases across 20 state-of-the-art LLMs under various decision-making scenarios:

**Key biases identified:**
- **Confirmation bias:** Selective interpretation of evidence to confirm prior beliefs
- **Anchoring effect:** Over-reliance on initial information when making decisions
- **Availability heuristic:** Judging frequency/probability by ease of recall
- **Framing effects:** Different preferences for logically equivalent descriptions
- **Overconfidence:** Systematic overestimation of accuracy

**Implications:**
- LLMs inherit or replicate human-like cognitive biases
- These are structural reasoning biases, not just social biases
- Understanding these biases is crucial for building reliable reasoning systems
- Adversarial attacks may exploit prediction error minimization failures

## 2026 Advances in Metacognitive Reasoning

Recent 2026 research has made significant progress on metacognitive reasoning — the ability of LLMs to monitor and regulate their own thinking processes.

### Predictive Metacognition (Nature Scientific Reports, 2026)

A neuro-computational framework that integrates predictive processing principles with anterior cingulate cortex monitoring into transformer architectures. Key findings:

- **Predictive Metacognition** enables LLMs to self-monitor reasoning quality by comparing predicted vs actual outcomes
- **Anterior Cingulate Cortex (ACC) monitoring** provides error detection signals that trigger reasoning revision
- **Neuro-computational integration** bridges predictive processing theory with practical LLM architectures

### LLM Reasoning Predicts When Models Are Right (arXiv 2602.09832)

Analysis of reasoning traces reveals that correct predictions are characterized by grounded causal logic (e.g., 'because', 'therefore'), while faulty reasoning is five times more likely to rely on surface-level patterns.

**Key insight:** Metacognitive monitoring can distinguish high-quality reasoning from low-quality reasoning by analyzing the structure of reasoning traces.

### Meta Chain-of-Thought (Meta-CoT)

Extends traditional Chain-of-Thought by explicitly modeling the underlying reasoning required to arrive at a particular CoT. This meta-reasoning layer enables:

- **Explicit reasoning modeling** beyond surface-level step generation
- **Meta-RL procedures** that optimize reasoning strategies across task distributions
- **Adaptive reasoning** that selects appropriate CoT depth based on problem complexity

### Agentic Chain-of-Thought Steering (ACTS) (arXiv 2606.03965)

Proposes inference-time control over how models think, addressing the inefficiency of extended chain-of-thought reasoning:

- **Inference-time control** allows dynamic adjustment of reasoning depth
- **Efficient token usage** reduces waste from unnecessary reasoning steps
- **Agentic steering** enables models to self-regulate their thinking process

### Metacognition in LLMs: Foundations, Progress, and Opportunities (arXiv 2607.11881)

Comprehensive survey of metacognitive capabilities in LLMs:

- **Effective metacognitive monitoring** improves transparency, reliability, and downstream utility
- **Self-reflection capabilities** enable models to identify and correct reasoning errors
- **Future opportunities** include more sophisticated metacognitive architectures and training methods

### Human-like Metacognitive Skills (Alignment Forum, Feb 2026)

Observation that newer SOTA models with elaborate chain-of-thought reasoning demonstrate improved metacognitive skills:

- **GPT-5 and Gemini 3** use parallel reasoning paths with metacognitive oversight
- **Elaborate CoT** correlates with better self-monitoring capabilities
- **Human-like metacognition** may reduce "LLM slop" by enabling better error detection

---

## Cross-Domain Connections

- **BDI Mental States:** Belief-Desire-Intention architecture provides formal structure for reasoning agents
- **Neuro-Symbolic AI:** Hybrid architectures combine symbolic reasoning with neural learning
- **Cognitive Warfare:** NATO's concept targets cognition itself — perception, reasoning, decision-making
- **Mechanistic Interpretability:** Understanding how reasoning traces map to internal circuit activations
- **Predictive Coding Networks (2025):** Networks that minimize prediction error through hierarchical layers, showing improved robustness to adversarial attacks
- **Precision Weighting Mechanisms (2026):** Attention mechanisms that modulate prediction error influence based on expected reliability, improving uncertainty estimation
- **Metacognitive Monitoring (2026):** Models that estimate their own reasoning confidence, enabling better error detection and correction

---

## Key Insight

**Reasoning may not be a separate module but an extension of predictive processing at higher levels of abstraction.** This has implications for both understanding human cognition and building better AI systems.

The failures of LLMs in reasoning tasks may not be failures of "reasoning" per se, but failures of predictive processing at levels where the model lacks sufficient training data or appropriate priors.

**Societies of thought** suggest that reasoning optimization naturally converges on multi-agent-like architectures, providing a bridge between symbolic and neural approaches to reasoning.

---

*Field report synthesized from research on predictive processing, LLM reasoning capabilities/failures, dual-process theory, societies of thought, expert systems, and cognitive biases.*
