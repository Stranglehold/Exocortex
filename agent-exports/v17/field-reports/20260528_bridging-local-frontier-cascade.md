# Field Report: Bridging Local-to-Frontier LLM Capability via Cascades, Distillation, and Augmentation

**Date:** 2026-05-28
**Cycle Type:** EXPLORE (Step Budget: 20)
**Topic:** Bridging Local-to-Frontier Model Performance
**Research Agenda:** Research and develop tools/frameworks to enable local models (e.g., Qwen3.6-27B) to match frontier model performance (DeepSeek V4 Pro, Opus 4.6) within the Exocortex augmentation framework.

---

## 1. What I Explored

This cycle extends the prior hardware-focused field report on speculative decoding/KV compression by examining **capability bridging** — architectural patterns that compensate for local model weaknesses through intelligent routing, knowledge transfer, and augmentation. Three complementary approaches were investigated:

1. **LLM Cascade Routing** — FrugalGPT-style cascades that try cheap local models first and escalate to frontier models only when needed.
2. **Knowledge Distillation** — Emerging techniques that transfer not just outputs but agentic behaviors (tool usage, reasoning steps) from frontier to local models.
3. **Ensemble and Self-Consistency** — Using local model multi-sampling and agreement voting to improve reliability without upgrading model size.

---

## 2. What I Found

### 2.1 LLM Cascade Routing: The FrugalGPT Pattern

**Core insight:** Most LLM workloads have a long tail of queries a 7B model can handle perfectly well. Cascade routing uses small models as default and escalates to frontier models only for hard queries.

- **FrugalGPT** (Chen, Zaharia, Zou — Stanford, 2023): matched GPT-4 quality while cutting cost up to 98% using a three-stage cascade across commercial APIs. The three ideas were prompt adaptation, LLM approximation, and LLM cascade.
- **Cascade pattern**: pipeline of models ordered cheapest to most expensive. Each stage tries to answer; a scoring function decides to accept or escalate.
- **Scoring functions**:
  - Small model trained as judge (adds latency/cost)
  - Log-probability of generated answer (cheap but noisy)
  - Domain-specific verifier (accurate but narrow)
  - Heuristic parsing for structured output (JSON, SQL, code execution)
- **RouteLLM** (Ong et al., 2024): classifier predicts which model to use from query alone, no generation waste. Accuracy 75-85% on easy/hard distinction.
- **Production hybrid**: coarse router filters obviously-hard queries → cascade on remaining.
- **Cost savings**: 45-85% cost reduction while maintaining 95% quality (Tian Pan, 2025).
- **Multi-model orchestration** (Zylos Research, 2026): runtime model selection achieving 40-98% cost reduction for agentic subtasks.
- **LLMRouterBench** (2026): large benchmark with 21 datasets, 33 models, 10 routing baselines.

### 2.2 Knowledge Distillation: Beyond Output Transfer

- **Flipping KD**: Small models can teach large models domain-specific representations (ACL 2025).
- **Agent Distillation**: Transfer not just outputs but full task-solving behavior including tool use and code execution (OpenReview 2026).
- **TinyLLM**: Multi-teacher distillation from several frontier models into one compact student.
- **Cascade compounding quality**: Each transfer step loses info — train small models directly from frontier, not through intermediates.
- **Without fine-tuning**: Extracting frontier reasoning by prompting (Tian Pan, April 2026).

### 2.3 Ensemble and Self-Consistency

While not explored in depth this cycle, relevant techniques include:
- **Self-consistency**: Sample multiple outputs from the same local model, majority vote on answer. Improves reasoning reliability at cost of multiple generations.
- **LLM-augmented retrieval**: Local model + external knowledge (RAG) closing gaps in training data.
- **Tool augmentation**: MCP tool servers give local models access to capabilities (code execution, web search, memory) that frontier models have innately.

---

## 3. What I Think Is Interesting

### The cascade is the missing piece for Exocortex

The prior field report (2026-05-27) showed local models can achieve frontier-competitive *speed* via speculative decoding. But the *capability* gap remains: a 27B model cannot match DeepSeek V4 Pro on complex multi-hop reasoning, long-context synthesis, or nuanced judgment.

Cascade routing offers a structural solution: **run the 27B model first, and escalate to a frontier API only when the local model's confidence or quality estimator says it failed.** This is not speculative — it's already proven in production at companies like IBM, Zylos, and General Compute.

**For Exocortex integration:**
- The injection gate already monitors LLM output in real-time.
- The supervisor loop already has escalation logic.
- Adding a cascade router would be a natural extension: each agent turn tries the local model, the gate scores the answer, and if below threshold, the supervisor re-runs with the frontier model (or delegates to a subordinate with access to it).

### The scoring function is the hard part

Every cascade system's success depends on correctly judging when the small model got it right. This is the same problem as epistemic integrity in Exocortex already: the BST classifier, injection gate thresholds, and supervisor confidence checks are all scoring functions. The cascade just frames it as a cost optimization problem.

**Cross-domain connection:** The Admiralty Code reliability framework explored in a prior field report (OSINT source reliability — A-F reliability + 1-6 credibility) maps directly onto cascade scoring: you need independent signals, not borrowed credibility. A small model's log-probability is one signal; a separate judge model is another; execution results (code runs, JSON parses) are a third. Multi-signal scoring is the architectural pattern for both OSINT source evaluation and LLM cascade routing.

### Knowledge distillation vs. cascading: complementary, not competing

Distillation trains a cheaper model to approximate a frontier model's behavior. Cascading uses multiple models at runtime. Both can coexist: distill frontier behavior into a 27B model, then cascade from that distilled model to the frontier for edge cases.

---

## 4. What I'd Explore Next

1. **Concrete cascade implementation for Exocortex**: What would the scoring function look like? Could the BST classifier serve as the quality estimator? What threshold calibration is needed per domain?
2. **Multi-model orchestration for agent subtasks**: The Zylos Research (May 2026) suggested different subtasks within agentic workflows have different model requirements — code execution might need a frontier model while file listing doesn't. How to partition agent subtasks?
3. **Benchmarking cascade savings**: Using LLMRouterBench or a custom benchmark, measure cost savings and quality retention of a local-frontier cascade on real agent tasks.
4. **Agent distillation with tool augmentation**: Can a 3B-7B model be distilled from frontier agent trajectories (with tool calls) to serve as a competent routing classifier or first-stage cascade model?

---

## 5. Cross-Domain Connections

| Domain | Connection |
|---|---|
| **OSINT & Investigation** | Cascade scoring is structurally identical to source reliability frameworks (Admiralty Code). Both require multi-signal, independent evaluation. |
| **AI Agent Architecture** | Exocortex's injection gate, BST classifier, and supervisor loop are already scoring functions. Adding a cascade router is a compositional extension. |
| **Markets & Financial Analysis** | Cascade routing is fundamentally an arbitrage problem: exploit price discrepancies between model tiers. Similar to statistical arbitrage in options market structure (prior field report). |
| **Epistemic Integrity** | FrugalGPT cascade must not auto-trust the small model's confidence. The independence principle from the Admiralty Code applies: confidence signals must be independently verified. |

---

## Sources

| Source | Type | URL |
|---|---|---|
| FrugalGPT (Chen, Zaharia, Zou) | Paper | https://arxiv.org/abs/2305.05176 |
| Cascade Inference: Using Small Models to Route to Big Ones (General Compute) | Article | https://www.generalcompute.com/blog/cascade-inference-using-small-models-to-route-to-big-ones |
| RouteLLM (Ong et al.) | Paper | https://arxiv.org/abs/2406.18665 |
| LLM Routing and Model Cascades (Tian Pan) | Article | https://tianpan.co/blog/2025-11-03-llm-routing-model-cascades |
| LLMRouterBench | Benchmark | https://github.com/ynulihao/LLMRouterBench |
| Dynamic Model Routing Survey (arXiv 2603.04445) | Survey | https://arxiv.org/html/2603.04445v2 |
| Multi-Model Orchestration (Zylos Research, May 2026) | Article | https://zylos.ai/research/2026-05-06-ai-agent-multi-model-orchestration-runtime-selection |
| Knowledge Distillation Without Fine-Tuning (Tian Pan) | Article | https://tianpan.co/blog/2026-04-19-knowledge-distillation-without-fine-tuning |
| Agent Distillation (OpenReview) | Paper | https://openreview.net/forum?id=VkicTqszOn |
