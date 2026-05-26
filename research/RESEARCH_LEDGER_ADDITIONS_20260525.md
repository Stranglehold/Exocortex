# Research Ledger — Additions May 25, 2026
## Append to existing research ledger

---

## RL-011: Vector Policy Optimization (VPO) — Training for Diversity

**Paper:** Bahlous-Boldi et al. (MIT, Sakana AI), "Vector Policy Optimization: Training for Diversity Improves Test-Time Search," arXiv:2605.22817, May 21, 2026
**Found by:** Jake, May 25, 2026
**Relevance:** SWARMFISH ensemble diversity (DEC-039), idle engine EXPLORE mode, test-time search for agentic workloads

**Key Finding:** Standard RL post-training (RLHF, GRPO) optimizes a scalar reward → low-entropy response distributions → model collapses onto one "best" answer. VPO replaces the scalar with vector-valued rewards, training the model to produce diverse solution *sets* where individual solutions specialize to different reward dimensions. Drop-in replacement for the GRPO advantage estimator.

**Results:** VPO matches or beats scalar baselines on test-time best@k across four benchmarks (multi-hop QA, logic reasoning, navigation, tool use + coding). Gap *widens* as candidate budget grows. On LiveCodeBench, VPO-trained Qwen2.5-Coder-7B unlocks problems GRPO cannot solve at any budget.

**Connections to Exocortex:**

1. **SWARMFISH (DEC-039):** Our 8-profile persona ensemble is synthetic diversity — prompting the same model with different frames. VPO's insight: diversity needs to be *trained in*, not prompted for. A VPO-trained model sampled 8 times produces genuinely different solutions (different Pareto-optimal points), not slight variations of the same answer. If a VPO fine-tune of Qwen3.6 becomes available, SWARMFISH could replace persona prompts with temperature-diverse sampling from a model trained to be diverse. Per-profile Brier weighting (DEC-039) still applies — it measures which dimensions of diversity are calibrated, regardless of the diversity source.

2. **EXPLORE mode:** VPO's "gap widening" (more samples → proportionally better results) applies to idle engine EXPLORE cycles. More exploration is more valuable when the exploration is genuinely diverse. If the model's exploration distribution is low-entropy (same topics, same approach), more cycles don't help. VPO suggests training the exploration instinct, not just scheduling it.

3. **Test-time search for agents:** Tool selection in Agent Zero is a search problem. VPO suggests training the model to explore diverse tool sequences rather than committing to the most likely one. Combined with the supervisor's loop detection, this would produce "try something different" behavior at the model level rather than at the scaffolding level.

**Actionable:** Watch for VPO-trained Qwen models from the community. If published, evaluate as SWARMFISH diversity source. LoRA fine-tuning with VPO is theoretically feasible on our hardware (7B model fits; 27B would require the second GPU). Add to SWARMFISH V3 evaluation list.

**Cross-cutting theme:** Change of basis as universal insight mechanism (same finding, different reward dimensions reveal different solutions).

---

## RL-012: AlphaProof Nexus — Formal Proof Search Solves Open Problems

**Paper:** Tsoukalas et al. (Google DeepMind), "Advancing Mathematics Research with AI-Driven Formal Proof Search," arXiv:2605.22763, May 21, 2026
**Found by:** Jake, May 25, 2026
**Relevance:** Generate-verify loop architecture, intelligence pipeline design (DEC-038), the thesis that simple agentic loops outperform specialized systems

**Key Finding:** An LLM agent alternating generation with formal verification (Lean) autonomously solved 9 of 353 open Erdős problems (at a few hundred dollars per problem) and proved 44 of 492 OEIS conjectures. Being deployed across combinatorics, optimization, graph theory, algebraic geometry, and quantum optics. A basic agent (simple LLM + verifier loop) replicated the Erdős successes but was costlier on hardest problems. The authors observe "an ongoing shift from specialized trained systems toward simple agentic loops as LLMs become more capable."

**Architecture:** Generate candidate proof → verify with Lean → if invalid, learn from the error → generate refined candidate → repeat. The more capable agent adds: sketch refinement (decompose proof into steps), library search (find relevant lemmas in Mathlib), and multi-step planning. But the basic loop does most of the work.

**Connections to Exocortex:**

1. **Intelligence pipeline (DEC-038):** FORECAST → RESOLVE → RECALIBRATE is the same generate-verify-learn loop applied to geopolitical prediction instead of mathematical proof. The verifier changes (web search for us, Lean for them). The loop is universal. Both use external reality as the ground truth — not internal consistency checking, not model confidence, but "go look at the world and see if you were right."

2. **The simplicity finding:** The basic agent matching the sophisticated agent on easier problems mirrors our information density thesis. Simple loops handle most cases. Sophisticated mechanisms (their AlphaProof sketch refinement, our V2 EXPLORE mode with batch research skills) are needed at the frontier. Build the simple loop first. Add sophistication where measurement shows it's needed.

3. **Cost structure:** "A few hundred dollars per open problem" solved autonomously. Our idle engine cycles cost electricity and GPU wear. Both systems invest compute in search loops that mostly fail (most proof candidates are wrong, most forecasts need revision) but produce genuine value when they succeed. The economics of autonomous agentic work: most iterations are negative-value, but the successes pay for all the failures.

4. **Build the environment, not the model:** DeepMind didn't train a specialized mathematics model. They put a general-purpose LLM (Gemini) in a loop with a formal verifier (Lean) and a library (Mathlib). The environment (the loop + the verifier + the library) is the capability. The model provides the generation. Same thesis as DEC-001 (deterministic scaffolding beats probabilistic reasoning): the scaffolding (loop, verifier, library) enables the reasoning the model can't do alone.

**Actionable:** The generate-verify pattern validates our RESOLVE phase design. The Lean formal verification methodology could inspire a stronger verification mechanism for the intelligence pipeline — instead of web-search-and-compare, could we formalize falsification conditions in a machine-checkable format? The `falsifiable_by` field in hypothesis entries is a step toward this. The gap: our verification is heuristic (web search for contradicting evidence), theirs is formal (Lean type-checking). Bridging that gap — making geopolitical falsification more rigorous — is a research question for the intelligence pipeline's maturity phase.

**Cross-cutting theme:** Build the environment, not the model. Simple loops + external verification outperform specialized training.

---

*Both papers found on the same day. Both validate core Exocortex architecture decisions from different angles: VPO validates the diversity thesis (DEC-039), AlphaProof validates the generate-verify-learn loop (DEC-038). The convergence is independent — MIT and DeepMind didn't coordinate, and neither is building an intelligence analysis system. The patterns are universal.*
