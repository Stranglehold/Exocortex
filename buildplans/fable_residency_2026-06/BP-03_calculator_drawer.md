# BP-03 — The Calculator Drawer

**Source:** Research V (the calculator drawer survey)
**Blocks on:** BP-02 (to validate each swap actually helps)
**Owner:** [assign]
**Status:** draft — *[Deposited 2026-07-03. Not started per Opus's briefing. Note: production model landscape changed since authoring (Ornith-1.0-35B in prod, Qwen3-Coder/Qwable in stable, CPU utility model on 1237) — the VRAM budget table needs re-verification against current resident set before build.]*

---

## Problem

The agents reason probabilistically about things that have cheap deterministic or
small-model answers — exact computation, dedup, classification at scale, retrieval
ranking, contradiction detection, forecast aggregation. Research V established that
offloading these is **capability-invariant infrastructure** (even frontier models
fail multi-digit arithmetic without a calculator), and that the right small tools
rival GPT-4-class systems at 1/100–1/400 the cost while fitting CPU + ~1.5–3GB VRAM
alongside the 27B with no model-swap contention.

## The hard constraint (the Ollama lesson)

Everything here is **small and always-loaded, or CPU**. No second full inference
server JIT-swapping a large model on the same GPU. Verify resident VRAM after
loading each tool. On the planned dual-3090 box, embedder and reranker become
comfortably always-resident.

## Resource budget (must hold — re-verify against current production model)

| Component | Resident? | VRAM | CPU/RAM |
|-----------|-----------|------|---------|
| Main production model (Q4-ish) | yes | ~17–19 GB | — |
| Embedder (Qwen3-Embedding-0.6B / BGE-M3) | yes | 0.3–1.2 GB | or CPU |
| Reranker (bge-reranker-v2-m3) | on-demand/yes | 0.5–1.5 GB | or CPU |
| NLI (deberta-v3-base) | on-demand | ~0.5 GB | CPU-fine |
| SetFit / GLiNER / MiniCheck | CPU-first | ~0 | CPU |
| Solvers, DuckDB, BM25, calibration | n/a | 0 | CPU |
| **Specialist VRAM total** | | **~1.5–3 GB** | |

## Prioritized shortlist (each maps to a named pain point)

Build in this order; each is gated by BP-02 showing it actually helps on a local
golden set before it ships.

### 1. Embedder upgrade — highest ROI, lowest risk
- **What:** Replace MiniLM-L6-v2 (2021, 22M) with Qwen3-Embedding-0.6B (~640MB) or BGE-M3.
- **Pain point:** OSS claim-dedup precision; FAISS memory recall.
- **Build:** swap the embedding call; re-embed existing FAISS stores (one-time migration); benchmark dedup precision before/after on a local labeled set.
- **Gate:** measurable dedup-precision gain on the golden set, or don't ship.

### 2. Cross-encoder reranker
- **What:** bge-reranker-v2-m3 or mxbai-rerank-base-v2 as a second retrieval stage.
- **Pain point:** memory-retrieval and library-search precision.
- **Build:** bi-encoder top-50 → rerank → top-k into context.
- **Gate:** Hit@1 improvement beyond noise (if <2 points, drop it — latency not worth it).

### 3. NLI model into `contradict.py`
- **What:** cross-encoder/nli-deberta-v3-base (184M), calibrated entailment/contradiction/neutral.
- **Pain point:** claim contradiction detection (currently LLM-mediated).
- **Build:** dedicated NLI scores deterministically; LLM adjudicates only low-confidence pairs. Pairs with MiniCheck for grounding.
- **Gate:** agreement with LLM on a contradiction gold set, at a fraction of the cost.

### 4. SetFit classifier replacing per-item LLM technique classification
- **What:** bootstrap labels from the production model once, train SetFit (8–50 examples/class), serve at ~zero cost.
- **Pain point:** per-item LLM classification cost in OSS ingestion — **biggest ingestion-cost reduction.**
- **Build:** label bootstrap → train → serve; keep the LLM for the long tail.
- **Gate:** accuracy within tolerance of the LLM on the SemEval taxonomy; **re-validate monthly against LLM labels to detect drift** (stale-classifier risk, Research V).

### 5. GLiNER for the entity layer
- **What:** zero-shot NER on CPU, feeding Apache AGE (BP-06).
- **Pain point:** entity extraction cost/consistency.
- **Gate:** entity-extraction quality vs LLM on a sample, at CPU cost.

### 6. SWARMFISH aggregation + calibration (deterministic)
- **What:** replace LLM-mediated committee consensus with **extremized logarithmic
  opinion pooling (geometric mean of odds, extremize ≈ √3) + Platt scaling +
  conformal prediction (MAPIE).** Keep the LLM for *generating* forecasts and
  *search-driven* disagreement resolution.
- **Pain point:** the committee design Research IV flagged as the riskiest in the stack.
- **Build:** see BP-06 §SWARMFISH for the full redesign; this is the calculator-drawer half of it.
- **Gate:** Brier improvement on the BP-02 backtest set vs current LLM-mediated aggregation.

### 7. Plumbing layer
- **What:** DuckDB (agent analytical queries), rank_bm25 (lexical recall complementing dense), rapidfuzz/simhash (dedup), difflib (retcon_ledger edit tracking).
- **All CPU.** Low risk, high utility.

### 8. Solvers behind one "constraint" tool
- **What:** Z3 / OR-Tools, invoked only on genuine constraint/scheduling/optimization problems — LLM writes the model, solver solves.
- **Lower frequency, high reliability payoff.**

## Integration pattern (the decision rule)

- **Plumbing the agent never chooses** (embedder, reranker, NLI in contradict.py,
  SetFit in ingestion, calibration) → **library call inside pipeline code.**
- **Judgment-invoked** (SymPy calculator, Z3/OR-Tools, DuckDB ad-hoc, GLiNER ad-hoc)
  → **Agent Zero instrument / Skill** (prompt-visible interface).
- **Cross-cutting / gated / shared across instances** → **MCP server** (consistent
  with the spine, gated via Cedar). Use MCP-Zero on-demand discovery to avoid
  dumping thousands of schemas into context.

Rule of thumb: *plumbing → library; judgment-invoked → instrument; cross-cutting/gated → MCP.*

## Enforcement policy (ties to BP-05 gate)

- **REQUIRED** (harness intercepts): arithmetic routes through the calculator;
  claims entering long-term memory pass the NLI/MiniCheck grounding check; dedup
  runs before storage; hashing on audit-chain writes. The Cedar gate rejects or
  auto-rewrites bypasses.
- **OFFERED** (agent chooses): constraint solver, DuckDB analytics, ad-hoc GLiNER.
- **ADVISORY** (runs, agent may override): calibration outputs, hedge/drift
  detectors, prompt-injection classifier (bypassable — a filter, not a wall).

## Skepticism to honor (Research V)

- Small models underperform the production model in low-resource/idiosyncratic
  domains and context-heavy judgment — validate per task, don't assume.
- Stale fine-tuned classifiers drift while the LLM would have adapted — treat each
  small model as a *cache of the LLM's judgment with an expiry*; re-validate.
- Tool sprawl is real cost for a solo maintainer — **no tool without a named pain
  point.** Prefer CPU-first and HF-standard models.
- Vendor benchmark numbers (reranker gains, embedder %s, the injection detector's
  99.99%) must be re-measured on Exocortex's own golden set before they're trusted.

## Acceptance gate (whole plan)

Each shipped tool has demonstrated, on a local golden set via BP-02, that it
matches-or-beats the LLM-native approach at lower cost — and the total specialist
VRAM stays within ~1.5–3GB beside the production model with no swap contention.
