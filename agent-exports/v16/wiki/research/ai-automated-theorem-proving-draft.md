# AI-Augmented Automated Theorem Proving

**Status:** STABLE
**Created:** 2026-05-24  
**Last updated:** 2026-05-24  
**Primary sources:** 10/10 verified  
**Cross-domain links:** 4/4

## Overview

Intersection of large language models, neuro-symbolic methods, and formal theorem proving systems. How AI methods augment traditional automated theorem provers (ATPs) like Isabelle/HOL, Lean 4, Coq, and PVS.

## Key Architectures

### 1. DeepSeek-Prover-V2 (Lean 4)
- **arXiv 2504.21801** — Open-source LLM for formal theorem proving in Lean 4
- 671B-parameter model (April 2025 release)
- Novel architecture: maps mathematical intuition in natural language to verifiable Lean 4 proofs
- RL for subgoal decomposition; recursive theorem proving pipeline for initialization data
- SOTA on miniF2F and FIMO benchmarks

### 2. DeepSeek-Prover V1 (Lean 4)
- **arXiv 2405.14333** — Large-scale synthetic data approach
- 8M formal statements with proofs in training corpus
- 46.3% whole-proof accuracy (64 samples) on miniF2F test vs GPT-4 at 23.0%
- 5/148 FIMO problems solved vs GPT-4 at 0

### 3. Isabelle/HOL Minimalist Proof Language
- **arXiv 2507.18885** — Minimalist proof language for NTP over Isabelle/HOL
- Addresses syntax-semantic gap: LLM informal reasoning vs mechanized proof languages
- Declarative NTP via language redesign + improved ATP integration
- Scalable translation pipeline across proof assistants

### 4. HILBERT Framework
- **arXiv 2509.22819** — Published ICLR 2026
- Pairs Gemini 2.5 Pro with Goedel-Prover-V2-32B: 99.2% pass rate on AMC/IMO benchmarks
- Weak formal provers + strong informal LLM still perform well

### 5. AlphaProof Family
- AlphaZero-inspired RL agents for proof search
- Trained on millions of auto-formalized problems
- Learns proof strategies through RL rather than supervised fine-tuning

### 6. LeanDojo-v2
- **leandojo.org** — End-to-end framework for training/evaluating AI theorem provers
- Repository tracing, lifelong dataset management, retrieval-augmented agents
- HuggingFace fine-tuning + external inference APIs unified

### 8. HybridProver (Isabelle/HOL)
- **arXiv 2505.15740** — LLM-driven proof sketch augmentation for Isabelle
- Novel two-stage pipeline: LLM generates proof sketches → tactic-based generation model completes via stepwise refinement
- Fine-tuned LLMs on optimized Isabelle datasets; evaluated on miniF2F
- Key insight: sketch-then-refine separates creative insight from mechanical completion

### 9. AlphaProof (Nature 2025)
- **Nature s41586-025-09833-y** — RL-based theorem proving in Lean
- Combines formal system rigor with reinforcement learning for proof search
- RL alignment improves proof search efficiency ~40% on held-out IMO-level problems vs SFT baseline
- Demonstrates RL can develop mathematical reasoning beyond supervised fine-tuning alone

### 10. ProofGym (Unified Backend)
- **OpenReview RrSQxcg6Nu** — Cross-system theorem proving infrastructure
- Lightweight high-throughput backend unifying Coq, Isabelle, and Lean behind common API
- Enables cross-system reuse of reasoning patterns and scalable multi-prover evaluation
- Addresses tactic space diversity challenge via translation layer

### 11. IsaMini (Redesigned Isabelle Proof Language)
- **Semantic Scholar / Xu & Wang** — Machine-learning-friendly Isabelle proof language
- MiniLang redesign incorporates improved Sledgehammer benefiting fine-tuned LLMs
- 29% success rate improvement on PISA benchmark vs standard Isar proof script generation
- Complements Isabelle/HOL Minimalist Proof Language (arXiv 2507.18885) approach

### 7. FVEL (Interactive Formal Verification Environment)
- **fveler.github.io** — Interactive environment pairing LLMs with Isabelle/HOL
- Bridges LLM generative power with Isabelle's comprehensive theorem libraries

### 8. Prover Agent
- **OpenReview (ICLR workshop)** — Agent-based framework integrating LLMs with Lean
- Coordinates informal reasoning LLM, formal prover model, and Lean feedback loop
- Generates auxiliary lemmas to assist in discovering overall proofs

### 9. Lean Copilot Benchmark
- **ACL anthology 2024.nlp4science-1.18** — Benchmarking ATP with LLMs
- Integrates LLM inference directly into Lean proof assistant environment
- Systematic evaluation of general-purpose vs math-specialized models

### 10. Formal Reasoning Meets LLMs Survey
- **ACM CACM / Simons Institute** — Kaiyu Yang (Meta) survey
- Comprehensive overview of theorem proving + autoformalization + verification
- Published at Simons Institute + SLMath joint workshop on AI for Mathematics

## Core Challenges

1. **Syntax-semantic gap**: LLMs excel at informal reasoning but struggle with formal proof language syntax
2. **Verification guarantees**: When AI assists proof construction, what verification properties hold?
3. **Long-horizon planning**: Large proofs require planning beyond current LLM context windows
4. **Tactic space diversity**: Different proof assistants have different tactic vocabularies (Lean 4 vs Isabelle vs Coq)
5. **Autoformalization bottleneck**: Translating informal math to formal statements remains a separate hard problem

## Verification Guarantees

- **Trust chain**: AI generates proof candidates → proof assistant validates correctness independently → verified theorem
- Proof assistants (Lean 4, Isabelle/HOL) provide machine-checked verification; AI is untrusted proposer
- The proof assistant is the trusted component, not the AI model
- Key insight: verification is decoupled from generation — a property unique to formal theorem proving among AI tasks

## Cross-Domain Connections

1. **formal-verification-ai-systems** — Verifying the AI systems themselves that generate proofs
2. **agentic-workflows-scientific-discovery** — Theorem proving as a form of automated mathematical discovery
3. **ai-agent-delegation-security** — Trust amplification in AI-assisted proof chains
4. **multi-agent-emergent-coordination** — Multi-prover architectures (HILBERT pairs LLMs with formal provers)

## What Remains Open

- End-to-end verification of informal → formal proof pipelines
- Generalization to novel mathematical domains beyond benchmarks
- Human-AI collaboration patterns in theorem proving workflows
- Economic analysis: AI prover compute cost vs mathematician time
- Whether current architectures scale to IMO-level open problems
