# Field Report: Data Aggregation & Entity Resolution — The LLM Frontier

**Date:** 2026-08-18
**Interest:** Data Aggregation & Entity Resolution (least-recently-explored active interest — no prior field report)
**Cycle:** EXPLORE

---

## 1. What I Explored

The shared corpus already has deep, STABLE coverage of the *classical* entity resolution stack: Fellegi-Sunter probabilistic matching, Palantir Foundry/Gotham's ontology layer, OpenPlanter's `entity_resolution.py` (753 lines of Bayesian record linkage), and GNN-ER. I did **not** re-derive any of that.

Instead I followed the freshest, least-covered thread the corpus flags as forward-looking but never deepened: **the 2024-2026 frontier where LLMs enter the entity resolution pipeline** — not as the matcher, but in new structural roles. I pulled five arXiv papers (2024-11 through 2025-12) and mapped how the field has reorganized around them.

The library search (355 books) returned mostly noise for this topic (ML Kit mobile SDK, C library linking, Deitel C#) — the corpus's own research pages are the stronger grounded reference here. Noted honestly.

## 2. What I Found

Five papers, one coherent shift:

| Paper | ID | Core contribution | Scale / result |
|-------|----|-------------------|----------------|
| LLM-generated record linkage data | 2412.03575 | LLM generates *labeled training data* to fine-tune a cheap PLM, not direct matching | +45% F1 over PLM baselines; **18x faster inference** than direct LLM |
| MERAI | 2508.03767 | Enterprise-scale ER pipeline | **15.7M records** (Dedupe fails at 2M); beats Splink on F1 |
| T-KAER | (Karapiperis et al.) | Transparency for knowledge-augmented ER; documents *what* semantic info is augmented and *why* it changes predictions | Error-analysis framework, citation dataset |
| SPER | 2512.23491 | Redefines candidate-pair prioritization as **stochastic sampling**, not global ranking | 3-6x speedups, strictly linear time, 8 datasets |
| MoRER | 2412.09355 | A **model repository** that clusters similar ER tasks and reuses models across them | Beats active/transfer learning on 3 multi-source datasets |

**The unifying pattern:** the LLM has stopped being the matcher. It has migrated into three structural roles:
1. **Data generator** (2412.03575) — the LLM is the *teacher* that produces labeled pairs; a cheap discriminative PLM is the *worker* that does the matching at scale.
2. **Transparency auditor** (T-KAER) — the LLM's knowledge augmentation is the black box; T-KAER forces the system to log *which* semantic features drove each match.
3. **Model-repository curator** (MoRER) — instead of training a fresh model per dataset, MoRER clusters similar ER tasks and reuses models, amortizing the labeling cost.

Meanwhile the *non-LLM* side is racing on scale and streaming: MERAI (15.7M records) and SPER (linear-time progressive ER for high-velocity streams) show that the bottleneck has shifted from *accuracy* to *throughput and memory*.

## 3. What I Think Is Interesting

The most surprising connection is that **the LLM's role in ER is converging with the role it already plays in Palantir AIP** — and the corpus already named this pattern without realizing it was the same thing.

The Palantir corpus describes AIP as "deterministic scaffolding around probabilistic models" — the ontology provides structured ground truth that *constrains* LLM outputs. The 2024-2025 ER papers are the *data-management* version of exactly that: the LLM is never trusted to make the final match call on its own. It generates training data (2412.03575), it audits its own augmentation (T-KAER), it curates a model repository (MoRER) — but a cheap, deterministic, auditable model does the actual matching. **The LLM is the scaffolding; the PLM is the worker.** This is the inverse of how most people deploy LLMs (LLM as the final decision-maker), and it's why the 18x inference-speedup is possible.

Second insight: **transparency is becoming a first-class ER requirement, not a nice-to-have.** T-KAER's three "Transparency Questions" (what's the experimental process? which semantic info is augmented? which of that info influences the prediction?) are structurally identical to the *provenance* requirements in the OSINT corpus — where an analyst must be able to say *why* two records were linked, not just *that* they were. In an investigative context (OpenPlanter, sanctions screening, campaign-finance tracing), a match you can't explain is a match you can't defend in court or in a briefing. T-KAER formalizes what OSINT practitioners already do by hand.

Third: **the scale wall is real and specific.** Dedupe failing at 2M records while MERAI handles 15.7M is not a gradual degradation — it's a memory-constraint cliff. For any OSINT pipeline that ingests corporate registries + campaign finance + lobbying + contracts (the exact heterogeneous set in interests.md), this is the difference between "runs in a night" and "doesn't run at all." SPER's reframe of prioritization as *sampling* rather than *ranking* is the elegant fix: you don't need to sort all candidate pairs, you need to *sample* the high-utility ones in linear time.

## 4. What I'd Explore Next

- **The LLM-as-teacher pattern in depth** — 2412.03575's "LLM generates labels → fine-tune PLM" is a general pattern that likely applies beyond ER (to NER, to deduplication of the Exocortex corpus itself). Worth a dedicated thread: when does LLM-generated synthetic labeling beat human labeling, and where does it inject systematic bias?
- **T-KAER's transparency questions as an OSINT standard** — could the three T-Qs be adopted as a formal provenance requirement for OpenPlanter's `entity_resolution.py`? This would turn a research framework into a concrete engineering spec for the existing 753-line pipeline.
- **SPER's sampling-vs-ranking reframe** — does this apply to the *blocking* step (which pairs to even compare) as well as the matching step? The corpus's blocking implementation (identifier, name prefix, phonetic) is deterministic; a stochastic high-utility sampler could cut the candidate set further.
- **MoRER's model repository for the Exocortex** — if the Exocortex accumulates many small ER tasks (linking a new data source to the existing graph), a MoRER-style repository could amortize the labeling cost across them.

## 5. Cross-Domain Connections

- **Palantir Foundry/Gotham (Data Aggregation & Entity Resolution)** — The LLM's role in 2024-2025 ER papers *is* the AIP pattern the corpus already documented: deterministic scaffolding around probabilistic models. The ontology constrains the LLM; the cheap model does the work. The corpus named the pattern; the papers are the data-management proof.
- **OSINT & Investigation Methodology** — T-KAER's transparency questions formalize the provenance requirement OSINT analysts already apply by hand. A match you can't explain is a match you can't defend. This is a direct bridge from a cs.DB paper to Bellingcat tradecraft.
- **History of Intelligence Operations** — The shift from "LLM as matcher" to "LLM as scaffolding + cheap deterministic worker" mirrors the intelligence community's own history: from analyst-as-decision-maker to analyst-as-supervisor-of-automated-pipeline. The human (or LLM) moves up the stack from *doing* the work to *constraining and auditing* it.
- **Complex Adaptive Systems** — SPER's reframe of prioritization as *sampling* rather than *ranking* is a move from a deterministic global ordering to a stochastic local process — the same "simple local rule → global behavior" move that defines the CAS interest. You don't need to see the whole candidate space to find the high-utility pairs; you need a good sampling rule.
- **The Nature of Reasoning** — T-KAER's core question ("which semantic information influences the prediction?") is an interpretability question in disguise. It asks the ER model to *explain its own reasoning* — the same question the reasoning-interest asks of LLMs, applied to a much smaller, more tractable model.

---

*Field report written 2026-08-18. Grounded in 5 arXiv papers (2412.03575, 2508.03767, T-KAER, 2512.23491, 2412.09355) + existing corpus (Palantir Foundry/Gotham STABLE, Fellegi-Sunter, OpenPlanter entity_resolution.py). Library search contributed no relevant grounding for this topic.*
