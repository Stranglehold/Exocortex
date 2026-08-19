# LLM Benchmark Contamination & Dynamic Evaluation (2026)

Status: STABLE

## Why This Matters

Static benchmarks overestimate LLM/agent capability by 20-40% due to contamination and weak test cases (SWE-bench-Live evidence, shared corpus). OpenAI declared SWE-bench contaminated (Feb 2026); 94% of SWE-bench issues predate model knowledge cutoffs. Published leaderboards are therefore unreliable for capability assessment — both for public model claims and for self-hosted/local model selection. Contamination is not a corner case: systematic evidence shows it is the norm across models and benchmarks.

## What Contamination Is

Benchmark contamination occurs when evaluation data is included in a model's training corpora, inflating apparent performance while generalization stays flat or falls. It can enter at multiple stages:

- **Pre-training leakage:** Web-crawled training corpora accidentally include benchmark test sets.
- **SFT/fine-tuning leakage:** Benchmark data is included in instruction-tuning or domain fine-tuning.
- **RL post-training contamination:** A 2026 vulnerability class — existing detection methods degrade to near-random on RL-phase contamination because RL collapses output entropy into narrow, sparse modes (Self-Critique motivation).
- **Agent-time web leakage:** In agentic evaluation, orchestration code or retrieval may surface benchmark answers to the model during inference (evaluation-gaming analogue to Goodhart's law).

Contamination also has an adversarial side: models can be tuned against publicly disclosed benchmark items (leaderboard gaming), and vendors may omit contamination studies due to competitive and copyright pressure (PaCoST motivation).

## Systematic Evidence: CONDA Shared Task

The 1st Workshop on Data Contamination (CONDA 2024, arXiv:2407.21530) ran an open shared task with a community-maintained database (566 reported entries, 23 contributors). Compiled findings:

- **42 contaminated sources** (training corpora or models), **91 datasets**, **566 contamination entries**.
- **432 contamination events**: 20 train-set, 95 dev-set, **317 test-set** — test-set contamination dominates.
- **144 non-contamination events**, indicating some benchmark/source pairs are clean.
- Database remains open: huggingface.co/spaces/CONDA-Workshop/Data-Contamination-Database.
## Detection Methods

### Data-Based (inspect the corpus)
- 13-gram overlap (Brown et al. 2020), 50-character overlap (OpenAI 2024), full-string overlap (Elazar et al. 2024).
- Requires access to training data — practical for open-weight corpus audits, impossible for proprietary models.

### Model-Based (Membership Inference Attack style)
- Verbatim regeneration of evaluation items (Sainz et al. 2023; Golchin & Surdeanu 2024).
- Likelihood/MIA: Min-K% Prob (Shi et al. 2024), sharded likelihood (Oren et al. 2023), P(True) confidence.
- **PaCoST** (arXiv:2406.18326): paired confidence significance testing — constructs a distribution-matched counterpart for each benchmark item and tests whether the model is significantly more confident on the original. Meets all five practical detection requirements (training-data-free, corpus-free, threshold-free, calibration-free, task-format-free). Finding: almost all models and benchmarks tested are suspected contaminated to some degree → call for benchmark-free evaluation.
- **Self-Critique** (RL post-training): probes policy collapse (entropy collapse to a narrow reasoning path) from RL training; up to +30% AUC over baselines and the first method that can detect RL-phase contamination, where prior methods are near random.

## Dynamic Evaluation: The 2026 Shift

Static suites are being replaced by dynamic benchmarks that rotate, refresh, or time-lock questions:

- **LiveCodeBench:** continuously rotating coding problems (shared corpus self-hosted-eval page).
- **SWE-bench-Live:** post-cutoff, live-updating instances to prevent mode collapse / trivial-solution overfitting (shared corpus ATLAS page; Mundra et al. 2025).
- **ForecastBench:** dynamically contamination-free forecasting benchmark with Brier Index metrics (shared corpus LLM-forecasting page).
- **CryptoBench** (arXiv:2512.00417): expert-curated live benchmark for LLM crypto analysts — 50 questions/month; reveals a retrieval-prediction imbalance failure mode (agents appear factually grounded while lacking synthesis).
- **Dynamic benchmark survey (2026):** static→dynamic transformation taxonomy; identifies the critical gap — lack of standardized criteria for evaluating dynamic benchmarks — and proposes optimal design principles.
- **zkML eval integrity:** zero-knowledge proofs that a declared evaluation executed honestly on the correct model (shared corpus zkml-verification page) — a tamper-evidence layer for self-reporting agents.

## Implications for Self-Hosted Evaluation & Self-Improving Agents

- Published leaderboards are unreliable selection signals for local models; contamination-free local evaluation is required for honest capability assessment.
- Self-hosted eval must use held-out, post-cutoff instances or synthetic generation (ATLAS guideline).
- Live-updatable test sets prevent agents learning to game a fixed suite; fresh instances defeat trivial-solution mode collapse.
- For self-improving agents, the evaluator is part of the loop: Goodhart's law applies to internal metrics, so metric integrity tools (canary strings, random held-out splits, zkML proofs) are part of the self-improvement architecture.

## Exocortex Integration

- Metric integrity for cycle provenance: journal claims should cite which benchmark version and which contamination controls were used.
- Surrogate-verifier risk: skill-curation verifiers trained on contaminated signals propagate bias into the skill lifecycle.
- Contamination detection as entity resolution over corpus chunks: overlap between training corpora and eval sets is a near-duplicate detection problem (shared corpus ER data-quality isomorphism).
- The dynamic-evaluation design principles apply to SWARMFISH/forecasting evaluation: rotating domains and time-segmented resolution windows reduce leakage.
## Cross-Domain Connections

1. ATLAS autonomous coding agents (self-hosted eval, live-updatable test sets)
2. LLM-as-Judge reliability (Goodhart's law, benchmark gaming)
3. Entity resolution & data quality (overlap detection as near-duplicate ER; gold-standard pitfalls)
4. LLM forecasting calibration (ForecastBench dynamic, Brier Index)
5. Autonomous skill curation (surrogate verifiers, metric gaming in the skill loop)
6. zkML verifiable inference (eval-integrity proofs)
7. Empirical integrity / oracle-fabrication risk (journal claims vs. measured eval)
8. Agent observability & tracing (span-level eval scores inherit contamination bias)
9. Self-improving agent loops (failure semantic priming if contaminated signals reinforce wrong behaviors)
10. Multi-agent orchestration (shared eval orchestrators as single points of leakage/gaming)

## References

1. Sainz et al., Data Contamination Report from the 2024 CONDA Shared Task, arXiv:2407.21530
2. Zhang, Lin, Wan, PaCoST: Paired Confidence Significance Testing, arXiv:2406.18326
3. Self-Critique: RL post-training contamination detection (2025, via search)
4. Dynamic benchmarking survey: static→dynamic taxonomy and design principles (2025, via search)
5. CryptoBench: live LLM-agent crypto benchmark, arXiv:2512.00417
6. Mundra et al., SWE-bench-Live (2025)
7. OpenAI (Feb 2026) SWE-bench contamination declaration
8. Brown et al. 2020 (13-gram overlap); OpenAI 2024 (50-char overlap); Elazar et al. 2024 (full-string overlap)
9. Shi et al. 2024 (Min-K% Prob); Oren et al. 2023 (sharded likelihood)
10. Golchin & Surdeanu 2023 (DCQ), 2024 (guided prompting / verbatim regeneration)
11. Shared corpus: atlas-autonomous-coding-agents, self-hosted-llm-evaluation-benchmarking-draft, llm-judge-agent-evaluation-2026-draft, zkml-verification

---

*Deepened DRAFT→STABLE 2026-08-14 BUILD cycle from AI Agent Architecture & Local Inference interest. Grounding: shared corpus (atlas, self-hosted eval, LLM-as-judge, zkML) + search_library (generic ICS/energy only — honest gap) + arXiv primary sources (CONDA, PaCoST, Self-Critique, dynamic-benchmark survey, CryptoBench). Memory saved per Rule 13.*
