# Proactive Interference in Transformers

## Core Problem
Pre-processed but now-outdated information actively competes with current relevant values, degrading retrieval accuracy log-linearly as stale associations accumulate. This represents a working memory bottleneck fundamentally distinct from context window limitations.

## Key Findings (SleepGate 2026)
| Metric | Result | Implication |
|--------|--------|-------------|
| PI Depth 5 Accuracy | 99.5% with SleepGate, <18% all baselines | Architecture-level solution needed beyond prompt engineering |
| PI Depth 10 Accuracy | 97.0% with SleepGate | Effectiveness maintained at extreme interference |
| Effective Interference Horizon | Reduced from O(n) to O(log n) | Logarithmic compression of stale information |

## Dual-Process Distinction (Chattaraj-Raj 2026)
Proactive and retroactive interference engage **computationally distinct mechanisms** in transformers:

| Characteristic | Proactive Interference (PI) | Retroactive Interference (RI) |
|----------------|-------------------------------|---------------------------------|
| Scaling with Model Size | R²=0.06 (not significant) | R²=0.491 (highly predictive) |
| Error Pattern | Active primacy intrusion (56%) | Passive retrieval failure (51%) |
| Hallucination Rate | 0.2% | 0.8% |
| Position Bias | Early position errors dominate | Late position errors dominate |

## Universal Inversion Pattern
All 39 tested LLMs show PI > RI (Cohen's d = 1.73, p < 0.0001) - the **opposite of human memory** where retroactive interference typically dominates.

## Practical Implications for Exocortex
1. Reasoning models optimize consolidation at expense of recency access
2. Parameter count matters more than context length for PI resistance
3. Position confusion not fabrication indicates retrieval/selection problem not generation failure
4. SleepGate's conflict-aware temporal tagging directly applicable to KV cache management

## Cross-References
[[deterministic-scaffolding]] - addresses need for structural interference resolution
[[stateful-injection]] - related concept of managing context state actively  
[[memory-decay]] - complementary approach via entropy-based staleness metrics

---
*Research basis: arXiv:2603.14517 (SleepGate), arXiv:2603.00270 (Dual-Process Interference)*
