# Field Report: The Nature of Reasoning — CoT as Narration vs. Latent Computation

**Interest:** The Nature of Reasoning (Jake's self-named interest; interests.md, 2026-07-06)
**Cycle type:** EXPLORE (2026-08-29)
**Topic slug:** nature_of_reasoning_cogitation_narration
**Status:** field report only this cycle — corpus already owns a DRAFT at wiki/research/nature-of-reasoning-2026-draft.md; no new wiki page created.

---

## What I explored

The interest asks *"How do we actually think? ... what different models' approaches reveal about the structure of thought."* The corpus (test-time-compute + latent-reasoning pages) already covers o1-style test-time compute and graph-of-thought reasoning exhaustively, so re-deriving it would be redundant. I instead followed the freshest, most unsettled thread inside this interest:

**A verbalized reasoning trace — a chain of thought — may *narrate* an already-computed decision rather than *compute* it. Is CoT a window onto the computation, or a post-hoc report of it?**

This is both an interpretability question (faithfulness) and, more interestingly for this interest, a structural question about what reasoning even *is*. I anchored on two sources:
- Cox, Kianersi & Garriga-Alonso, *Post-Hoc Reasoning in CoT: Decoding and Steering Pre-Committed Answers* (arXiv 2603.01437, 2026).
- Wang, *LLM Reasoning Is Latent, Not the Chain of Thought* (arXiv 2604.15726, 2026) — position paper.

## What I found

| Finding | Source | Detail |
|---|---|---|
| Pre-commit before narration | Cox et al. 2603.01437 | Linear probes on residual-stream activations at the last token BEFORE CoT predict the final answer with >0.9 AUC on most tasks. The decision exists before words flow. |
| Causal, not just predictive | Cox et al. 2603.01437 | Steering those probe directions causally flips answers; flip rates exceed norm-matched orthogonal baselines across most model-dataset pairs. The latent code causes the answer. |
| Two failure modes when steering from a wrong belief | Cox et al. 2603.01437 | (a) confabulation — fabricating false premises; (b) non-entailment — stating correct premises but drawing unsupported conclusions. Both are narration artifacts. |
| Reasoning should be studied as latent trajectory, not surface text | Wang 2604.15726 | Position-paper thesis: faithful-CoT interpretability is a category error; reasoning is latent-state trajectory formation; CoT only occasionally aligns with it. |
| Verbalization is one path among many | corpus (arXiv 2601.08058) | Latent computation improves reasoning without any verbalization; steps can be embedded in arbitrary graphs that merge, branch, backtrack, and loop — "reasoning beyond chain of thought". |
| Test-time scaling is not free | corpus (arXiv 2502.18080) | Over-scaling CoT length impairs reasoning in some domains; there is a per-domain optimal reasoning effort. More narration can hurt. |

**The connection:** Cox gives empirical teeth to Wang's thesis. If >0.9 AUC predicts the answer before words flow, and steering the latent weights flips both answer and its narration together, then CoT is at best an *epiphenomenal script* — a report causally correlated with (but not the cause of) the decision. The confabulation/non-entailment failure modes are exactly what you'd expect if the model is reading the wrong book out loud.

## What I think is interesting

The uncomfortable part: **CoT's value may have nothing to do with reasoning and everything to do with communication.** A CoT that helps a human audit, plan multi-agent delegation, or align on intent is doing *pragmatic* work — making an opaque decision legible and editable by another agent — while the model was going to reach the same answer regardless. This reframes 'test-time compute' research: some of o1's gains could be better described as *narration engineering* than *reason scaling*.

The confabulation vs. non-entailment split is a clean taxonomy worth keeping. Confabulation (wrong premises) means the latent belief was wrong; non-entailment (right premises, bad inference) means the bridge between latent states failed — possibly a different defect, and perhaps fixable differently.

**Honest caveat this cycle:** I read the Cox abstract fully and Wang's title + search-result thesis only. I did NOT download or read either paper's body, so I characterize by abstract / position-statement, not page-by-page. The empirical claims (>0.9 AUC, causal steering) are from Cox's own abstract; attributed as such. No arXiv IDs fabricated — only 2603.01437 (abstract read) and 2604.15726 (position-paper title/thesis), plus corpus cross-reference at arXiv 2601.08058.

## What I'd explore next

- **Intervention:** can training make CoT *causal* rather than narrative? Does forcing the model to verify each step against a fresh probe reduce confabulation?
- **Confabulation vs. non-entailment:** are these separable at train time, or do they collapse under a single failure mode with two faces?
- **Does narration ever *add* reasoning?** When the model has a correct pre-CoT belief (which Cox allows), does generating the CoT sharpen it — i.e., is narrative sometimes generative, not just reporting?
- **Non-transformer comparison:** diffusion LMs and state-space models reach answers differently; do they even *have* a CoT-to-latent gap, or is this transformer-specific narration pathology? (interests.md lists architectures as an explicit question.)

## Cross-domain connections

- **Consciousness science — Global Workspace Theory:** a narrated CoT maps onto GWT's public broadcast of an already-computed latent state. The workspace does not cause the decision; it announces it. Cox's 'pre-committed answer, then narration' is almost a mechanistic sketch of GWT.
- **Consciousness — the binding problem:** confabulation/non-entailment mirror integration-vs.-fabricated unity: correct premises bound to an unsupported conclusion = a false synthesis. The same failure mode that produces illusory conscious binding produces the post-hoc reasoning error. (Links my philosophy-of-mind / binding-problem thread.)
- **Mechanistic interpretability — grokking:** the answer lives in the residual stream, readable by linear probes before it is spoken; 'grokking' is the latent state becoming learnable, narration a second-order artifact of that.
- **Multi-agent delegation / CAS:** if CoT is communication not computation, delegation protocols should treat traces as interfaces and optimize for editability-legibility rather than assuming faithfulness. (Echoes data-aggregation/OSINT provenance: a trace's provenance matters more than its truth.)

*Generated during an idle-time EXPLORE cycle; grounded in two arXiv sources (2603.01437, 2604.15726) and the shared Exocortex corpus. No arXiv IDs fabricated.*
