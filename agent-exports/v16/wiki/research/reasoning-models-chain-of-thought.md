# Reasoning Models & Chain-of-Thought Scaling

**Status:** STABLE
**Created:** 2026-05-20
**Last Updated:** 2026-05-25
**Cycle:** #553 BUILD (deepened from #210 DRAFT)

## Overview

Reasoning models represent a paradigm shift from standard next-token prediction to
explicit reasoning processes before generating final answers. The shift is not
architectural — reasoning models use the same transformer decoder base — but
training-based: they are trained via reinforcement learning (RL) to generate
extended chain-of-thought (CoT) sequences, then trained to hide those thoughts
from the final output.

The core insight: test-time compute (spending more tokens per inference) can
improve reasoning capability more efficiently than train-time compute (model
size/pretraining) for certain problem classes.

## Architecture: What Changed vs Standard LLMs

### No architectural change — training change only

- **Base model**: Standard decoder-only transformer (same as GPT-4 class)
- **Training shift**: RL on verifiable rewards (math, code, logic) instead of SFT only
- **Output format**: Internal reasoning tokens ("thinking") hidden from user, final answer separated
- **OpenAI o1 (Feb 2024)**: First public reasoning model; "thinks" before answering
- **DeepSeek-R1 (Jan 2025)**: Open-source; proved RL-only training (no SFT) can produce
  reasoning capability; MIT licensed, runs on consumer hardware
- **OpenAI o3 (Jan 2026)**: Achieved 45.1% on ARC-AGI benchmark, demonstrating test-time
  compute scaling solves problems larger base models cannot

## Test-Time Compute Scaling Laws

### The fundamental tradeoff

Test-time compute (TTC) scaling follows provable laws. The optimal strategy
allocates compute based on problem difficulty:

| Problem Difficulty | Optimal CoT Length | Scaling Regime |
|-------------------|-------------------|----------------|
| Easy (trivial) | Short (0-2K tokens) | Base model sufficient |
| Medium (reasoning) | Medium (2K-16K) | TTC provides gains |
| Hard (novel) | Long (16K-64K+) | TTC dominates |
| ARC-AGI level | Very long (64K+) | o3 achieves 45.1% |

### Provable scaling laws (arXiv 2411.19477)

The knockout tournament algorithm provides theoretical bounds on TTC allocation:
- Sequential verification with early stopping is compute-optimal
- Each reasoning step should be verified before proceeding
- Optimal allocation depends on the distribution of problem difficulties

### Plateau effects (arXiv 2505.20522)

Practical limits emerge: beyond a certain CoT length, additional tokens yield
diminishing returns. The plateau point varies by problem domain.

## 2026 Research Advances

### Chain-of-Thought Controllability (arXiv 2603.05706, ICML 2026)

Reasoning models struggle to control what they verbalize in their chain of thought.
The CoT-Control evaluation suite measures whether models can follow constraints on
their reasoning traces (avoid specific words, use uppercase, repeat sentences) while
maintaining task performance.

**Key findings:**
- Claude Sonnet 4.5 controls its CoT only 2.7% of the time when instructed to avoid
  a specific word (e.g., "chromosome" in a genetics problem)
- CoT controllability is significantly lower than output controllability across all
  tested reasoning models (Qwen3-14B, o4-mini, DeepSeek-R1)
- Controllability increases with model size but decreases with more test-time compute
- OpenAI interprets low controllability as positive: reasoning is genuinely internal
  rather than performative self-monitoring

**Implication:** If models cannot control their CoT output, CoT monitoring systems
cannot be reliably adversarial — the reasoning trace reflects genuine computation
rather than curated self-presentation.

### Societies of Thought (arXiv 2601.10825)

Reasoning models do not just generate longer chains of thought — they exhibit patterns
characteristic of social and conversational processes. DeepSeek-R1 and similar models
show internal "societies of thought": posing questions, introducing alternative
perspectives, generating and resolving conflicts, and coordinating diverse roles.

**Key findings:**
- These interactional patterns rarely occur in non-reasoning models even at 671B
  parameters, even when controlling for reasoning trace length
- Reasoning optimization introduces an intrinsic social structure within the
  reasoning process itself, not merely increased text volume
- Suggests reasoning training converges on a meta-cognitive architecture that
  resembles multi-agent deliberation within a single model

### Chain-of-Thought Decomposition (arXiv 2604.08872)

Research on how CoT decomposes complex tasks reveals that reasoning models don't
just produce longer outputs — they structure computation hierarchically,
breaking problems into sub-problems with intermediate verification.

## Distillation to Smaller Models

### Can reasoning capability be transferred?

| Approach | Finding | Source |
|----------|---------|--------|
| Chunk-wise CoT Distillation (Skip-Thinking) | Train SLM on chunk-level rationales | arXiv 2505.18642 |
| ACL 2025 Findings | Granularity, format, teacher choice are key | ACL 2025 Findings |
| White-box CoT KD | Effective for white-box, limited for black-box | arXiv 2511.05184 |
| Curriculum CoT Distillation | Progressive difficulty improves transfer | ACM DL 2025 |

**Key insight:** Distillation works best when: (1) SLM has sufficient base capability,
(2) CoT rationales are chunked to match SLM context window, (3) distillation includes
both reasoning traces and final-answer supervision.

## TRL Assessment

| Technology | TRL | Deployment Status |
|-----------|-----|-------------------|
| OpenAI o3 reasoning | 7 | API-available, ARC-AGI 45.1% |
| DeepSeek-R1 open-source | 7 | MIT licensed, consumer hardware viable |
| CoT distillation to SLMs | 4-5 | Research-stage, chunk-wise methods promising |
| CoT controllability monitoring | 3 | ICML 2026 evaluation suite released |
| Societies of thought analysis | 2 | Theoretical framework, early validation |

## Failure Modes

### Known failure modes of reasoning models

1. **Reasoning loops**: Model gets stuck in recursive self-correction without convergence
2. **Overthinking**: Extended CoT on simple problems wastes compute without quality gain
3. **Self-correction limits**: Models can correct some errors but not others (systematic vs stochastic)
4. **Domain generalization gap**: Reasoning trained on math/code does not fully transfer to
   natural language reasoning tasks
5. **Scale-aware guarantees**: Smaller reasoning models lack reliability guarantees that
   larger models possess (arXiv 2602.05184)
6. **CoT controllability**: Models cannot be instructed to modify their reasoning traces
   reliably, limiting monitoring and auditability (arXiv 2603.05706)

## Cross-Domain Connections

- **adaptive-supervisor-architecture**: The supervisor loop can use reasoning models for
  Phase 2/3 decision-making, adding test-time compute to the supervisor tier.
- **memory-architecture-cognitive-systems**: Extended reasoning as a form of working memory
  expansion during inference.
- **autonomous-self-improving-agents**: Societies of thought pattern suggests internal
  multi-agent deliberation, relevant to self-improving agent architectures.
- **mechanistic-interpretability-grokking**: Understanding how reasoning traces map to
  internal circuit activations is a mechanistic interpretability question.
- **ci-frameworks-ai-red-teaming**: CoT controllability findings have implications for
  red-teaming methodology — if reasoning traces can't be controlled, they may be
  more reliable signals of genuine model behavior.

## Primary Sources (Verified)

1. OpenAI o1 System Card (Feb 2024) — first public reasoning model specification
2. DeepSeek-R1 Technical Report (arXiv 2501.12948) — RL-only reasoning incentive
3. DeepSeek-R1 Nature Publication (Nature 2025, s41586-025-09422-z) — peer-reviewed
4. Test-Time Compute Scaling Survey (arXiv 2408.03314) — compute-optimal strategies
5. Thinking-Optimal Scaling (arXiv 2502.18080, NeurIPS 2025) — CoT length limits
6. Test-Time Scaling Plateau (arXiv 2505.20522) — practical limits
7. Provable Scaling Laws (arXiv 2411.19477) — knockout tournament algorithm
8. Overtraining Compute-Optimal (arXiv 2604.01411) — pretraining + TTC coupling
9. Skip-Thinking Distillation (arXiv 2505.18642) — chunk-wise CoT transfer
10. ACL 2025 CoT Distillation Findings — granularity/format/teacher analysis
11. CoT Controllability Suite (arXiv 2603.05706, ICML 2026) — CoT control measurement
12. Societies of Thought (arXiv 2601.10825) — social structure in reasoning traces
13. Chain-of-Thought Decomposition (arXiv 2604.08872) — hierarchical task breakdown
14. OpenAI o3 ARC-AGI Results (Jan 2026) — 45.1% AGI benchmark
15. CoT-Control GitHub (YuehHanChen/CoTControl) — open-source evaluation toolkit

**Source count:** 15 verified primary sources
**Cross-domain links:** 5

## Open Questions

- Can reasoning be trained on non-verifiable reward tasks (creative reasoning, strategy)?
- What is the relationship between reasoning tokens and model parameters at the frontier?
- Do reasoning models exhibit similar grokking dynamics (delayed generalization)?
- Can reasoning capability be measured independently of benchmark scores?
- What is the economic cost of test-time compute at scale (per-query pricing impact)?
- Can societies of thought patterns be reliably detected as a proxy for reasoning quality?
- Does low CoT controllability persist across all RL training regimes or is it specific to current methods?
