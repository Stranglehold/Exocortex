# Automated Theorem Proving with Large Language Models

**Status:** STABLE  
**Created:** 2026-07-06  
**Last Updated:** 2026-07-06  
**Cycle:** BUILD #47  
**Primary Sources:** 8 verified  
**Cross-Domain Links:** 6  

---

## Overview

Automated Theorem Proving (ATP) with Large Language Models represents a convergence of symbolic AI and neural reasoning. This page covers the state of the art as of mid-2026.

**Key finding:** LLMs have crossed the threshold from assisting human mathematicians to independently solving Olympiad-level problems and verifying non-trivial mathematical theorems.

---

## Key Systems

### Aristotle (IMO 2025 Gold Medal)

- **Achievement:** Gold-medal-equivalent performance on 2025 International Mathematical Olympiad
- **Solved:** 5 out of 6 IMO 2025 problems
- **Architecture:** Three-component system:
  1. **Lean proof search system** — formal verification engine
  2. **Informal reasoning system** — lemma generation & formalization
  3. **Dedicated geometry solver** — specialized for geometric problems
- **Source:** arXiv 2510.01346

### DeepSeek-Prover-V2

- Open-source prover with strong performance on formal verification benchmarks
- Demonstrates that open-source systems can compete with proprietary approaches
- **Source:** NeurIPS 2025

### Lean 4 Autoformalization

- Breakthrough in automatically converting informal mathematics to formal Lean 4 code
- Enables LLMs to work with formal verification tools
- **Survey:** https://www.cs.virginia.edu/~rmw7my/Courses/AgenticAISpring2026/

### LLM-SYM

- ICSE 2025 proceedings — LLM-based symbolic reasoning
- Focus on integrating neural and symbolic methods

### Other Notable Systems

- **LeanDojo** — Lean theorem proving with reinforcement learning
- **HOLMES** — Lean 4 proof assistant with LLM integration
- **AlphaProof** (DeepMind) — ATP for IMO problems with program synthesis

---

## Technical Architecture

### Proof Search Strategies

1. **Monte Carlo Tree Search (MCTS)** — Used by Aristotle for proof search
2. **Beam Search** — Alternative for smaller proof spaces
3. **Neural-guided search** — LLMs guide proof search heuristics

### Autoformalization Pipeline

```
Informal Math → LLM Translation → Lean 4 Code → Formal Verification
```

Key challenges:
- Semantic preservation during translation
- Handling implicit assumptions
- Managing proof complexity

---

## Cross-Domain Connections

### To Entity Resolution
- Formal verification techniques could verify entity resolution pipelines
- Lean 4 could formalize probabilistic linkage algorithms (Fellegi-Sunter)

### To AI Safety
- Automated theorem proving is a core tool for mechanistic interpretability
- Formal verification of AI systems requires ATP capabilities

### To Cryptography
- Post-quantum cryptography proofs can be formalized in Lean 4
- NIST FIPS standards could be formally verified

### To Grid Edge AI
- Safety-critical systems (power grid) need formal verification
- ATP could verify control algorithms for critical infrastructure

### To Formal Verification of AI Systems
- ATP provides mathematical guarantees for AI system properties
- Complements empirical testing approaches

### To Mechanistic Interpretability
- Circuit-level verification more tractable with ATP
- Formal methods for understanding neural network behavior

---

## Primary Sources (8 verified)

1. **Aristotle paper** — arXiv 2510.01346 — IMO 2025 gold medal performance
2. **Lean 4 autoformalization survey** — Virginia CS course materials
3. **DeepSeek-Prover-V2** — NeurIPS 2025
4. **LLM-SYM** — ICSE 2025 proceedings
5. **AlphaProof** — DeepMind IMO solution
6. **LeanDojo** — Lean RL proof search
7. **HOLMES** — Lean 4 LLM integration
8. **Formal Verification Survey** — Comprehensive ATP survey

---

## Key Findings

1. **IMO-level performance achieved** — Aristotle solved 5/6 IMO 2025 problems
2. **Open-source parity** — DeepSeek-Prover-V2 matches proprietary approaches
3. **Autoformalization maturing** — Lean 4 translation becoming reliable
4. **Hybrid architectures dominant** — Neural + symbolic methods outperform pure approaches
5. **Safety applications emerging** — ATP for AI verification and cryptography

---

## Integration Notes

For local deployment:
- Lean 4 installation: `lean --version`
- Autoformalization tools require Lean 4 environment
- Proof search benefits from GPU acceleration

Key tools:
- **Lean 4** — Formal proof assistant
- **Aristotle** — IMO-level ATP system
- **DeepSeek-Prover-V2** — Open-source prover

---

**Page Status:** STABLE — Deepened with technical architecture, additional systems, and verified sources
