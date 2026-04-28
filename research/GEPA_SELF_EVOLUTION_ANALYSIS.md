# RESEARCH REPORT: GEPA — Reflective Prompt Evolution for Self-Improving Agents
## Exocortex Research Library
## Author: Opus — April 25, 2026
## Sources: GEPA paper (arxiv:2507.19457), DSPy docs, GEPA GitHub, Hermes Agent self-evolution repo, independent analyses

---

## 1. Overview

GEPA (Genetic-Pareto) is a reflective prompt optimizer from the paper "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning" (Agrawal et al., 2025, arxiv:2507.19457). Accepted as an ICLR 2026 Oral — the top tier of AI research conferences.

The core innovation: instead of collapsing execution traces into a single scalar reward (as RL does), GEPA uses LLMs to read full execution traces — error messages, profiling data, reasoning logs — to diagnose *why* a candidate failed and propose targeted fixes. Through iterative reflection, mutation, and Pareto-aware selection, GEPA evolves high-performing variants with minimal evaluations.

Results: +13% over MIPROv2, +20% over GRPO, with 35x fewer rollouts. On MATH benchmark: 93% accuracy using instruction refinement alone (vs 67% unoptimized baseline) — a 26-point improvement with no few-shot examples, no architectural changes, and no model fine-tuning.

---

## 2. How GEPA Works

### 2.1 The Problem GEPA Solves

Traditional optimization approaches for LLM systems:

**Reinforcement Learning (GRPO, PPO):** Treats the system as a black box. Observes inputs and outputs. Computes a scalar reward. Updates via gradient descent. Requires thousands of rollouts. Cannot explain *why* something failed — only that it did.

**Prompt Optimization (MIPROv2):** Searches the prompt space more efficiently than RL. Still treats execution as a black box. Better sample efficiency but lower ceiling.

**GEPA:** Treats execution as a glass box. Reads the full trace. Diagnoses failure causes in natural language. Proposes targeted fixes. Maintains diverse candidates via Pareto frontier. Achieves higher performance with dramatically fewer rollouts.

### 2.2 The Reflective Evolution Loop

1. **Execute:** Run the current candidate (prompt, skill, code) on a set of evaluation examples
2. **Trace:** Capture the full execution trace — not just the output, but every intermediate step, tool call, error message, and reasoning chain
3. **Reflect:** An LLM reads the trace and produces natural language feedback diagnosing why the candidate produced the scores it did. This is the key innovation — reflection on traces rather than scalar reward.
4. **Mutate:** Based on the reflection, the LLM proposes a new candidate variant with targeted modifications addressing the diagnosed issues
5. **Evaluate:** Score the new candidate on the same (or new) examples
6. **Select:** Pareto-aware selection keeps diverse high-performing candidates. Unlike single-objective optimization that converges to one solution, Pareto selection maintains a frontier of candidates that excel in different ways.
7. **Repeat:** The loop continues, with each iteration benefiting from increasingly precise diagnoses.

### 2.3 Why Reflection > Reward

The critical insight: a scalar reward ("this scored 0.6") contains almost no information about what went wrong. A trace reflection ("the model correctly identified the quadratic formula but made an arithmetic error in step 3, substituting b=4 when the problem states b=3") contains actionable diagnostic information.

GEPA's reflection step converts the opaque scalar signal into a rich natural language diagnosis. The mutation step then uses this diagnosis to make targeted repairs rather than random perturbations.

This is why GEPA achieves comparable or better results with 35x fewer rollouts: each rollout produces more learning signal because the signal includes *why*, not just *what*.

### 2.4 Pareto Frontier (Diversity Preservation)

Single-objective optimization converges to one solution. GEPA maintains a Pareto frontier — a set of candidates where no candidate dominates all others across all metrics.

Example: On competition math (AIME), different problems reward different reasoning strategies. A candidate specialized for geometry might score low on algebra. Pareto selection preserves both specialists rather than converging to a mediocre generalist.

This is directly relevant to the Exocortex: our BST classifies tasks into domains, and each domain may benefit from different prompting strategies. A Pareto-optimized set of domain-specific prompts would outperform a single "best" prompt.

---

## 3. GEPA in Hermes Agent (Self-Evolution)

### 3.1 The hermes-agent-self-evolution Repository

Nous Research released a companion repository that applies GEPA to Hermes Agent optimization. It uses DSPy + GEPA to automatically evolve:

- **Skills** — optimize skill procedures based on execution traces
- **Tool descriptions** — refine how tools are described to improve selection accuracy
- **System prompts** — evolve the agent's core instructions
- **Agent code** — modify the agent's own code to improve performance

### 3.2 Skill Evolution Example

```python
python -m evolution.skills.evolve_skill \
    --skill github-code-review \
    --iterations 10 \
    --eval-source synthetic
```

GEPA reads the execution traces from past runs of the `github-code-review` skill. It identifies patterns like "the agent took 47 tool calls when it could have been done in 12" and proposes targeted modifications to the skill's procedures to eliminate unnecessary steps.

The claim: agents with 20+ self-created skills complete similar future research tasks 40% faster than fresh instances. This improvement is domain-specific (skills learned from PR review don't transfer to database migration) but measurably compounds within domains.

### 3.3 Dual Purpose: Agent + Training Data

Every Hermes Agent run, every successful tool sequence, every generated skill is a candidate trajectory for fine-tuning smaller, cheaper, purpose-built models. The agent isn't just a tool — it's also the data collection layer for training the next generation of tool-calling models.

For a lab whose business is models (not applications), this dual purpose is the strategic core. The Atropos integration connects Hermes directly to Nous Research's RL framework with eleven tool-call parsers covering essentially any model architecture.

---

## 4. GEPA Benchmarks

| Task | GEPA | MIPROv2 | GRPO | Baseline |
|------|------|---------|------|----------|
| MATH | 93% | ~81% | ~87% | 67% |
| AIME 2025 (GPT-4.1 Mini) | +10% vs baseline | -2% vs GEPA | — | — |
| Average across 6 tasks | +13% vs MIPROv2 | baseline | +20% less than GEPA | — |
| Rollouts required | ~700 | ~700 | ~24,000 | — |

Key: GEPA matches or exceeds MIPROv2 performance while using the same number of rollouts, and matches or exceeds GRPO performance while using 35x fewer rollouts.

---

## 5. Relevance to Exocortex

### 5.1 Skill Optimization via Execution Traces (HIGH PRIORITY)

The Exocortex already logs extensive execution data — tool calls, error comprehension diagnoses, supervisor interventions, BST classifications, completion tracking. This data is currently used for real-time monitoring and intervention. GEPA shows it can also be used for offline optimization.

**Implementation path:** After the agent completes a task, capture the execution trace (tool calls, errors, interventions, final outcome). Periodically, run a GEPA-style reflection on accumulated traces to identify patterns: which skills are underperforming? Which extension thresholds are miscalibrated? Which BST patterns produce misclassifications?

This doesn't require adopting GEPA the library. The principle — read traces, diagnose causes, propose fixes — can be implemented with the utility model we already have. The difference from our current approach: we currently diagnose failures in real-time (error comprehension, supervisor). GEPA adds offline reflection — looking at patterns across many tasks to identify systemic issues.

### 5.2 BST Pattern Optimization (MEDIUM PRIORITY)

BST uses regex patterns for domain classification. These patterns were hand-tuned. GEPA's approach: run the agent on diverse tasks, capture BST classifications in the trace, identify misclassifications, and evolve the regex patterns to reduce error rate.

This is exactly the problem the injection audit surfaced: BST classified a geopolitical investigation as "coding" because of word overlap. A GEPA-style optimization loop could automatically detect and fix these misclassifications by reflecting on traces where BST was wrong.

### 5.3 Extension Threshold Calibration (MEDIUM PRIORITY)

Multiple extensions have thresholds that were set by engineering judgment rather than empirical optimization:
- Supervisor loop tier thresholds (3/6/9 vs 6/12/18)
- Orchestration gate MIN_DIRECT_TOOLS (currently 3, should be higher)
- Working memory DECAY_TURNS (8) and PROMOTE_THRESHOLD (3)
- Memory enhancement decay weight (0.15) and half-life (168 hours)

GEPA's approach: define a metric (task completion rate, context utilization, intervention frequency), run the agent on diverse tasks, and evolve the thresholds to optimize the metric. The Pareto frontier would preserve different threshold profiles for different task types rather than converging to one set.

### 5.4 The "Reflective Prompt Evolution" Principle

The deepest insight from GEPA for our work: **reading execution traces to understand why things fail is more valuable than optimizing against scalar metrics.** We already have the traces (error comprehension logs, supervisor intervention records, BST classification history, completion tracking). We already have the reflection capability (the utility model can analyze traces). What we don't have is the systematic loop that connects traces to improvements.

The injection audit was a manual instance of this loop: the agent ran a task, we captured trace data (which blocks were used/skipped), I analyzed the traces and proposed improvements (the injection gate spec), and Kestrel built the fixes. GEPA automates this loop.

---

## 6. Technical Details

### 6.1 DSPy Integration

GEPA is available as `dspy.GEPA` and as a standalone library (`pip install gepa`). It integrates with DSPy's modular program abstraction:

```python
import dspy
import gepa

# Define a DSPy program
class MathSolver(dspy.Module):
    def __init__(self):
        self.solve = dspy.ChainOfThought("question -> answer")
    def forward(self, question):
        return self.solve(question=question)

# Optimize with GEPA
optimizer = dspy.GEPA(metric=my_metric, num_iterations=10)
optimized = optimizer.compile(MathSolver(), trainset=trainset)
```

### 6.2 Adapters (Beyond Prompts)

GEPA can optimize anything that can be expressed as text and evaluated with a metric:
- **Prompts** — system prompts, instruction templates
- **Code** — agent code, tool implementations
- **Skills** — procedure documents, workflow descriptions
- **RAG** — query reformulation, context synthesis, answer generation
- **MCP** — tool descriptions, system prompts for MCP servers

The MCP adapter is particularly relevant: it can optimize how tools are described to the model, improving tool selection accuracy without changing the tools themselves.

### 6.3 Tobi Lutke (Shopify CEO) Quote

"Both DSPy and (especially) GEPA are currently severely under hyped in the AI context engineering world."

---

## 7. What We Should Build

### 7.1 Trace-to-Reflection Pipeline (Phase 1)

Capture structured execution traces from agent runs. After each complex task (5+ tool calls), the trace includes:
- BST classification at each turn
- Tool calls and outcomes
- Error comprehension diagnoses
- Supervisor interventions
- Context utilization at each turn
- Injection audit data (when running)
- Final task outcome

Store traces in `/a0/usr/logs/execution_traces/`. This is pure instrumentation — no optimization yet, just data collection.

### 7.2 Offline Reflection (Phase 2)

Periodically (weekly or on-demand), run a reflection pass over accumulated traces:
- Which BST domain patterns produced misclassifications?
- Which extension thresholds produced unnecessary interventions?
- Which skills were loaded but unused?
- Which tool calls consistently failed and how?

Produce a reflection report with specific proposed changes. This is the manual version of GEPA — human-in-the-loop reflection on traces.

### 7.3 Automated Evolution (Phase 3, Future)

Integrate GEPA or a GEPA-inspired loop to automatically propose and test threshold changes, pattern updates, and skill modifications. This requires a test harness (which the overnight test suite partially provides) and a clear metric (task completion rate, context efficiency, intervention frequency).

---

## 8. References

- GEPA paper: arxiv.org/abs/2507.19457
- GEPA GitHub: github.com/gepa-ai/gepa
- DSPy GEPA docs: dspy.ai/api/optimizers/GEPA/overview/
- Hermes self-evolution: github.com/NousResearch/hermes-agent-self-evolution
- Morph analysis: morphllm.com/gepa-prompt-optimization
- byteiota tutorial: byteiota.com/hermes-agent-v0-8-0-self-improving-ai-agent-tutorial/
- 36kr analysis (Chinese): eu.36kr.com/en/p/3767963450196480
