# Self-Improving Agent Patterns

Status: STABLE
Created: 2026-05-16
Last Deepened: 2026-05-16
Related: autonomous-coding-agents, speculative-decoding, ai-agent-trust-infrastructure, trajectory-to-skill

## Overview
Self-improving agents that modify their own behavior, prompts, or capabilities through autonomous iteration. Covers trajectory-to-skill capture, GEPA-style prompt evolution, temperature escalation, and nightly LoRA fine-tuning.

## Key Mechanisms

### 1. Self-Editing (SICA — Self-Improving Coding Agent)
- **Source**: Robeyns & Szummer (Bristol), arXiv:2504.15228, ICLR 2025
- **Method**: Agent edits its own source code, re-evaluates on benchmarks, keeps improvements
- **Results**: 17% → 53% on SWE-bench Verified subset (229% improvement)
- **Key insight**: Non-gradient, data-efficient learning via LLM reflection + code updates
- **Meta-loop**: Minimal bootstrap code → self-improvement → benchmark → repeat

### 2. Reflective Prompt Evolution (GEPA)
- **Source**: Agrawal et al., arXiv:2507.19457, ICLR 2026 (oral)
- **Method**: Iterative reflection, mutation, Pareto-aware selection of prompt variants
- **Results**: +6pp average vs GRPO (up to +19pp), 35x fewer rollouts
- **vs MIPROv2**: +12pp on AIME-2025, +10pp average across tasks
- **Code optimization**: Demonstrated as inference-time search strategy
- **Implementation**: Available as `dspy.GEPA` and standalone `gepa` library

### 3. Darwin Gödel Machine (DGM)
- **Source**: KAUST, arXiv:2505.22954v3
- **Method**: Open-ended evolution of agent architecture via self-modification
- **Benchmark**: SWE-bench + LiveCodeBench
- **Approach**: Evaluation score as optimization target for final agent performance

### 4. Temperature Escalation
- **Pattern**: Higher temperature (0.7→1.2) used for retry/iteration, lower (0.1→0.3) for finalization
- **ATLAS-style**: Temperature escalation retry loop with nightly LoRA fine-tuning
- **Risk**: High temperature can produce hallucinations; needs guardrails

### 5. Trajectory-to-Skill Capture (Exocortex)
- **Source**: /a0/usr/Exocortex/specs/TRAJECTORY_TO_SKILL_SPEC.md
- **Trigger**: 5+ tool calls, successful completion, BST ≥2 signals, no Tier 2+ intervention
- **Process**: Utility model summarizes trajectory → SKILL.md in auto-generated/ directory
- **Deduplication**: Semantic similarity check against existing skills
- **Hermes benchmark**: Agents with 20+ self-created skills complete similar tasks 40% faster

## Current State of the Art

| Agent | Benchmark | Score | Method |
|-------|-----------|-------|--------|
| Claude Mythos Preview | SWE-bench Verified | 93.9% | Proprietary |
| SICA (Bristol) | SWE-bench Verified | 53% | Self-editing |
| GEPA | AIME-2025 | +12pp vs MIPROv2 | Reflective prompt evolution |
| ATLAS | SWE-bench | ~50% | Temp escalation + LoRA |

## SWE-bench Landscape (2026)
- **Verified**: 500 human-filtered GitHub issues (Django, Flask, scikit-learn)
- **Lite**: Curated subset for less costly evaluation
- **Live**: Continuously updated with new issues
- **Multilingual**: 300 tasks across 9 languages
- **Multimodal**: 517 issues with visual elements

## Stability Boundaries

1. **Self-editing**: Risk of breaking critical functionality; needs regression testing
2. **Prompt evolution**: GEPA shows stability via Pareto-aware selection
3. **Temperature**: Needs upper bound (max 1.2 typical) and cooldown mechanism
4. **LoRA fine-tuning**: Catastrophic forgetting risk; needs periodic re-evaluation

## Cross-Domain Connections
- **FPGA inference**: Hardware acceleration for self-improvement loops (sub-ms latency)
- **Entity resolution**: Agent self-model as entity across iterations
- **Privacy**: Self-modifying agents reveal internal state through behavior changes
- **Memory architecture**: Complementary learning systems mirror consolidation patterns

## Sources
- Robeyns & Szummer (2025). "A Self-Improving Coding Agent." arXiv:2504.15228
- Agrawal et al. (2025). "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning." arXiv:2507.19457, ICLR 2026 oral
- KAUST (2026). "Darwin Gödel Machine." arXiv:2505.22954v3
- Exocortex TRAJECTORY_TO_SKILL_SPEC.md (2026-04-27)
- Exocortex MEMORY_ARCHITECTURE_DESIGN_NOTE.md (2026-02-26)
- SWE-bench Leaderboard: llm-stats.com, benchlm.ai (accessed 2026-05-16)
