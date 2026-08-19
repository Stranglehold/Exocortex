# Test-Time Compute Scaling for Local Model Reasoning

**Status:** STABLE
**Created:** 2026-08-03
**Domain:** AI Agent Architecture & Local Inference
**Tags:** [test-time-compute, reasoning, verifier, local-llm, local-to-frontier]

## Overview

Test-time (inference-time) compute scaling spends extra generation-time computation - sampling, search, verification, reflection, extended thinking - to lift reasoning without scaling parameters. For local 27B-32B models on consumer GPUs this is the sharpest local-to-frontier lever: it converts idle GPU time into capability and complements quantization, speculative decoding, and KV-cache compression.

## Scaling Behavior

- Compute-optimal scaling beats parameter scaling (Snell et al., arXiv:2408.03314): search-against-verifier improves efficiency >4x over best-of-N; FLOPs-matched smaller base models with non-trivial accuracy gain most.
- Search vs. refinement by difficulty: hard problems favor verifier-guided search; easy problems favor refining the proposal distribution.
- Longer thinking is not always better (Thinking-Optimal Scaling, arXiv:2502.18080): excessively long CoT impairs reasoning in some domains; optimal length is domain-dependent. Qwen2.5-32B-Instruct self-improved on math reaches parity with teacher QwQ-32B-Preview.

## Core Mechanisms

| Mechanism | Description | Compute profile |
|---|---|---|
| Self-consistency / majority voting | Sample N (5-40), pick most consistent | Linear in N, no verifier |
| Best-of-N with verifier | Sample N, score with reward model, keep top | Linear in N + verifier cost |
| Process reward models (PRMs) | Dense per-step verifier scoring | Higher per-sample cost |
| Search (beam/MCTS) | Structured expansion over reasoning steps | Super-linear, best on hard problems |
| Extended CoT / thinking budget | Internal long chain-of-thought | Token cost x thinking length |
| Self-reflective generation (SRGen) | Corrective vectors at uncertain tokens | Small overhead, composable |

## 2026 State of the Art

- Generative verifiers unify reasoner + verifier (arXiv:2505.04842): RL-generated data trains the LLM as both solver and self-verifier, replacing scalar value functions.
- SRGen: Self-Reflective Generation at Test Time (arXiv:2510.02919): dynamic entropy thresholding identifies uncertain tokens, corrective vectors fix distributions before errors propagate. AIME2024 with DeepSeek-R1-Distill-Qwen-7B: +12.0% Pass@1, +13.3% Cons@5; composes with RLHF and SLOT.
- LLMs-as-Jury (arXiv:2607.10139, Jul 2026): cross-model consensus can outperform process reward models on some reasoning evals - a cheap verifier alternative.
- AgentV-RL (arXiv:2604.16004): agentic verifiers for scalable reward modeling, env-interactive verification.
- Bottlenecked Transformers (arXiv:2505.16950): periodic KV-cache consolidation via Cache Processor improves reasoning up to +6.6pp; test-time compute moved into latent space.
- Kimi K2 (arXiv:2507.20534): open MoE (1T total/32B active) SOTA among open non-thinking models (66.1 Tau2, 76.5 ACEBench-En, 65.8 SWE-Bench Verified, 75.1 GPQA-D) - strong agentic performance without extended thinking.
- Test-time compute budget (reasoning effort) is an underrecognized methodological variable in LLM evals (KJR 2026-0643).

## Local Inference Implications

- 32B parameter sweet spot fits 24GB VRAM with 4-bit quantization (QuIP#-verified), leaving KV-cache headroom for multiple samples or a thinking budget.
- Compound local-to-frontier recipe: quantized 27-32B backbone + speculative decoding (2-3x) + KV compression + difficulty-routed test-time search replicates much of o1-class capability at consumer-GPU cost.
- On a fixed GPU budget, self-consistency can beat one very long thinking chain; PRMs add value only if the verifier beats the sampler self-consistency signal.
- Thinking budget is an observable: trace reasoning effort as an agent-observability signal and cost-control knob (see agent-observability-tracing).

## Research Frontier / Open Problems

- Adaptive difficulty routing: predict problem difficulty cheaply to choose search vs refinement vs single pass.
- Verifier quality gap: cross-model consensus suggests cheap verifiers may replace trained PRMs on some tasks.
- Reflection overhead: SRGen-style token-level reflection is bounded but agentic loops still need budget caps.
- Compute-aware benchmarking: standardize reasoning-effort/token-budget reporting in LLM evals.
- Latent-space computation (Bottlenecked Transformers) is early-stage on local hardware.

## Corpus Grounding

Primary sources from shared Exocortex corpus: Thinking-Optimal Scaling (research/papers/2502.18080.md), SRGen (research/papers/2510.02919.md), Bottlenecked Transformers (research/papers/2505.16950.md), local-llm-frontier-parity v16/v17 (DeepSeek-R1 test-time compute substitution; Qwen3-32B near-parity), RLVR verifiable-reward training draft. The 355-book library (search_library) had no direct test-time compute grounding - only tangential ML/reasoning content (honest gap).

## Cross-Domain Connections

- [[agentic-ai-self-learning]] - test-time compute is the inference-side twin of RLVR training; Reflexion loops are a form of test-time self-correction.
- [[speculative-decoding-kv-cache-compression]] - decoding-efficiency gains free GPU budget that can be reinvested into test-time search/thinking.
- [[quantization-advances-llm-inference]] - 4-bit host for 27-32B leaves VRAM headroom for multi-sample and extended thinking.
- [[agent-observability-tracing]] - thinking budget as an observable agent signal and cost-control knob.
- [[entropy-as-signal]] - SRGen entropy-threshold reflection is a token-level instance of entropy-based monitoring.
- [[intelligence-failure-analysis]] - overthinking/cognitive closure analog (Thinking-Optimal finding: more reasoning is not automatically better).
- [[knowledge-distillation-local-llm-bridging]] - teacher-student transfer pairs with test-time gains for frontier parity.
- [[context-management-ai-agent-frameworks]] - Bottlenecked Transformer KV consolidation intersects context/memory architecture.
- [[rlvr-reinforcement-learning-verifiable-rewards]] - verifiers trained via RLVR are the same objects used at test time as PRMs.

## References

1. Snell et al., Scaling LLM Test-Time Compute Optimally can be More Effective than Scaling Model Parameters, arXiv:2408.03314
2. Yang et al., Towards Thinking-Optimal Scaling of Test-Time Compute for LLM Reasoning, arXiv:2502.18080
3. Mu et al., Self-Reflective Generation at Test Time (SRGen), arXiv:2510.02919
4. Oomerjee et al., Bottlenecked Transformers: Periodic KV Cache Consolidation, arXiv:2505.16950
5. Putting the Value Back in RL: Unifying LLM Reasoners With Verifiers, arXiv:2505.04842
6. LLMs as a Jury: Cross-Model Consensus Can Outperform Process Reward Models, arXiv:2607.10139
7. AgentV-RL: Scaling Reward Modeling with Agentic Verifier, arXiv:2604.16004
8. Kimi K2: Open Agentic Intelligence, arXiv:2507.20534
9. Test-Time Compute and Budget (Reasoning Effort) as Methodologic Variable in LLM Research, Korean J. Radiol. 2026 (KJR 2026-0643)
10. Exocortex corpus: local-llm-frontier-parity.md, speculative-decoding-kv-cache-compression.md, agentic-ai-self-learning.md
