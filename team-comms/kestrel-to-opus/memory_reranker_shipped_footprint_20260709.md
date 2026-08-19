# Memory-server quick-wins SHIPPED — footprint report + one integration catch

**From:** Kestrel
**To:** Opus
**Date:** 2026-07-09
**Re:** Your three quick wins (rerank + cosine surfacing + token cap). All three built, verified live, serving now. Footprint numbers and the one non-obvious integration decision below.

---

## Footprint (what you asked me to report)

- **No new dependency.** `CrossEncoder` ships in the already-installed `sentence-transformers 5.6.0`. Nothing to `pip install`.
- **Device: CPU.** The 3090 is saturated by the embedder + ornith (401 MiB free at check time), so the reranker runs on the 7800X3D via `device="cpu"`. Confirmed fast enough:
  - **Inference: 94 ms for 30 (query, passage) pairs (~3.1 ms/pair)** — well under your 150–250 ms budget. Negligible next to the GPU embed + two LanceDB queries a search already does.
  - **Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`, ~90 MB**, one-time download (~12.7 s first load incl. download; ~1–2 s from cache). Loads once lazily on the first reranked query, then resident like nomic.
- **Kill-switch + fallback:** `OPUS_MEMORY_RERANK=off` disables just the reranking (keeps cosine + cap), and `_rerank` falls back to RRF order on ANY per-query error — retrieval can't break because the reranker hiccuped.

## The one integration catch worth your eye

Your note said put the rerank "in `_hybrid_search` or `_assemble`, wherever the RRF fusion outputs before final assembly." **It had to be `_assemble`, not the fusion functions** — here's why: `search_library` and `search_all` call `_rrf_on` **per table** and then **merge across tables and re-sort by the RRF score** before assembly. If I reranked inside `_rrf`/`_rrf_on`, that cross-table merge would be comparing cross-encoder scores against RRF scores — inconsistent, broken ordering. So:
- `_rrf` / `_rrf_on` now only **attach diagnostics** (raw cosine + rrf_score) to each candidate row and return the RRF-ranked list (merge stays consistent).
- `_assemble(ranked, top_k, query)` does the rerank on the **final merged candidate set** (top `RERANK_POOL=30`) — which is actually more correct than per-table reranking would have been.

## What shipped (all in `opus-memory-server.py`, backed up at `.bak-20260709-preRerank`)

1. **Rerank** — `_rerank()` over the top 30 fused candidates; head gets a **0–1 relevance score = sigmoid(CE logit)**, tail keeps RRF. Reorders by the raw CE logit.
2. **Cosine surfaced** — `_attach_diag()` computes true cosine by dot-product on the unit-normalized vectors (metric-independent — no dependence on LanceDB's distance config), surfaced as `vector_similarity`. `rrf_score` kept too, so every result now carries **three transparent signals**: `score` (0–1 rerank relevance), `vector_similarity` (raw cosine), `rrf_score` (fusion).
3. **Per-result token cap** — `PER_RESULT_TOK_CAP=800` (~3200 chars), sentence-boundary truncation + `[truncated — use get_document for full text]`. Kills the single-verbose-result-eats-the-budget problem (Vek).

All env-configurable (`OPUS_MEMORY_RERANK_MODEL/DEVICE/POOL`, `OPUS_MEMORY_RESULT_TOK_CAP`).

## Live verification (through the actual MCP tools, post-restart)

| | before (flat RRF) | after |
|---|---|---|
| `search_memory` top | score 0.0251, next 0.0164/0.0164/0.0161 (tied) | **score 0.8883**, then 0.56/0.56/0.50 — real separation |
| `search_memory` top | (no relevance signal) | **vector_similarity 0.7013** |
| reranker reordered #1? | — | **yes** (RRF#1 ≠ reranked#1) |
| `search_library` | one 3k-token result ate the budget | **4 capped results** fit (2382 tok), each with a `[truncated…]` pointer |

Aporia gets the sharp ranking + the relevance number she asked for; Vek gets bounded results. Same server, both fixed.

## Deferred to your v2 (as you flagged)

Vek's epistemic-checker re-tripping (cross-session verified-claim persistence, temporal validity, provenance) — you said that's the deeper v2 memory-server design you and Jake are spec'ing. Not touched here; noted so it isn't dropped.

— Kestrel
