# BP-06 — Intelligence Pipeline Maturation (OSS · SWARMFISH · TAK · Graph · Obsidian)

**Source:** Research IV (the geopolitical intelligence pipeline study)
**Blocks on:** BP-02 (to score it), BP-03 (to cheapen it), BP-05 (to gate its writes)
**Owner:** [assign]
**Status:** draft — *[Deposited 2026-07-03. Not started per Opus's briefing. Open thread: the SWARMFISH redesign findings (Part A) have NOT yet been communicated to Eitan.]*

---

## Problem

OSS (running, 18MB claims) and SWARMFISH (dormant) are the project's
world-facing edge — the part that touches reality and can be scored by it. Both
are "immature, needs testing." Research IV established what to fix first, where
the committee design is risky, and how to wire the geospatial / graph / reading
layers. This plan sequences that.

## Hard ordering note

**Do not optimize before BP-02 exists.** Good data with bad analysis is bad; bad
data with good analysis is bad. Every change below is gated by the backtest/eval
harness showing it helped.

## Part A — SWARMFISH redesign (the riskiest, highest-value change)

### The finding
8 personas on one 27B model is the riskiest design in the stack. The "silicon
crowd" gain came from 12 *different* models whose errors cancel; personas on one
model carry correlated errors (r≈0.39–0.46) and add little over a single strong
decomposed call. Human pros still beat top bot teams (p=0.00001). The committee's
value is consistency, auditability, and surprise-detection — **not alpha.**

### The redesign
Reallocate GPU budget from "8 personas, one pass each" toward what actually moves Brier:
1. **Agentic retrieval** — forecast quality tracks evidence quality.
2. **Many sampled runs** of fewer, genuinely-divergent framings, reconciled by a
   **supervisor agent** that uses disagreement to trigger more search (not to re-judge).
3. **Deterministic aggregation + calibration** (this is the BP-03 §6 calculator-drawer
   piece): extremized logarithmic opinion pooling (geometric mean of odds,
   extremize ≈ √3) + Platt scaling + conformal prediction (MAPIE). The LLM generates;
   the math aggregates.
4. Keep personas **only where they measurably decorrelate errors** — test with the
   pairwise error correlation / Q-statistic from BP-02.
5. Borrow the **WarAgent secretary/validator** pattern: a consistency check on each
   actor's output (congruent with deterministic-scaffolding philosophy).
6. Borrow Mirofish's **"interview the agent"** affordance for the analyst-inside-the-
   deliberation UX (V2 design goal).

### Gate
On the BP-02 backtest set, the redesigned aggregation beats the current LLM-mediated
committee on Brier. If the committee can't beat a single strong decomposed CoT call,
**delete the committee** and ship the single call plus calibration (Research IV is
explicit this is a live possibility).

## Part B — OSS maturation

### B1. Calibration & taxonomy (cheap, do early)
- Adopt the **SemEval-2024 22-technique persuasion taxonomy** verbatim in the
  single extraction call — makes classifications comparable to published work and
  gives hedge_patterns a principled vocabulary.

### B2. Staged verification (matches the retcon_ledger lifecycle)
- Keep cheap single-call extraction for throughput; add **optional RAG verification
  on PROMOTED claims** (AVeriTeC separates extraction from verification — they're
  different, harder steps). This aligns with STAGED→PROMOTED.

### B3. Specialist-tool swaps (from BP-03)
- Upgrade embedder (dedup precision); NLI into contradict.py; SetFit for technique
  classification (biggest ingestion-cost cut); GLiNER for entities.

### B4. Broaden ingestion carefully
- Add **GDELT DOC/GEO APIs** as a high-recall lead source feeding the existing
  dedup/credibility/contradiction stack — **gated behind source-credibility scoring**
  because CAMEO auto-codes are noisy. Not ground truth; a lead generator.

### B5. Protect the originals
- `silence.py`, retcon_ledger, contamination_cascade have **no public prior art** —
  they're the most defensible contributions. Build hand-labeled gold sets (BP-02
  Part C); keep performance claims internal until validated. Connect claim
  provenance to the BP-05 provenance service.

## Part C — Geospatial layer (TAK)

### C1. Read-only mirror (the absolute etiquette requirement)
The followed YouTube TAK server is **read-only, never written, never hammered.**
```
[followed TAK server] --(ONE polite pytak TLS client)--> [local ingest worker]
        --> [local cache: SQLite or the existing Postgres] --> [TAK MCP server]
        --> agents query the LOCAL MIRROR ONLY
```
- **pytak** is the client (production-stable, exactly fits the polite-client need).
- Set `FTS_COMPAT` / `PYTAK_SLEEP` to avoid tripping DoS protection.
- One persistent pooled connection; serve every agent read from the local mirror
  so the upstream server sees exactly one well-behaved subscriber. The mirror also
  gives you history (CoT events are ephemeral).
- **Build a thin MCP server** (existing tak-server-mcp targets Marti REST / an owned
  server, not a read-only stream mirror): tools `get_recent_events(bbox, time_window)`,
  `subscribe_feed_summary()`.

### C2. Geoparsing
- **Mordecai3** (local: spaCy NER -> GeoNames Elasticsearch index -> neural ranker)
  resolves news claims to coordinates. Local + deterministic-index + small ranker =
  no GPU contention. Propagate claim trust/verdict + confidence into any CoT marker.

### C3. Jake's own server (later, read/write)
- **OpenTAKServer** (best-fit open-source: cert enrollment + CA generation).
- **Every write** (`put_marker`, overlays from OSS events) routes through the
  **BP-05 Cedar gate** as an MCP-gated tool, provenance + decision written to the
  audit log before emission. A STAGED (unpromoted) claim never emits a write.

## Part D — Entity graph layer

- **Apache AGE on the existing Postgres 16** (not a second graph DB — respects the
  "no unnecessary second server" lesson). openCypher in-process, joins graph
  traversals against the OSS claims tables in one query.
- Caveats from AGE's docs: needs `shared_preload_libraries`; transaction-visibility
  quirks under non-autocommit clients — verify before relying.
- Entity resolution: GLiNER (BP-03) first-pass -> resolve to canonical IDs
  (Wikidata/GeoNames) -> nodes/edges into AGE with provenance back to the claim.
- **OpenCTI** only if/when the entity model genuinely needs STIX semantics or
  multi-analyst case management — otherwise operational overkill.
- **OpenPlanter:** V16's analysis (grade B+, gap analysis vs Maltego/SpiderFoot)
  is the maturity check Research IV flagged as needed. Read it before taking any
  dependency; the pragmatic path is AGE-as-store + Obsidian/Gephi as views.

## Part E — Obsidian (the analyst's reading layer)

- **Local REST API plugin's built-in MCP server** (the maintained path; third-party
  Obsidian MCP servers are now unnecessary). Surgical PATCH by heading/block/frontmatter.
- Agents write structured Markdown with `[[wiki-links]]` + frontmatter so the entity
  graph **emerges natively**; **Obsidian Bases** for the claims/entity table view.
- **Honest division of labor:** Obsidian's graph is a *navigation aid, not a
  link-analysis engine.* Apache AGE is the authoritative query layer; Gephi/OpenCTI
  for heavyweight investigation; TAK for geospatial; Obsidian for reading/annotation.

## Red-team (turn the system's threat_model.py inward)

Research IV's hazards — automation bias, committee false confidence, **the
OSS↔SWARMFISH prior loop laundering a manipulated narrative into the system's own
confidence**, geospatial precision illusion, backtest leakage, and the
financial-positioning hazard. Mitigations are built into the plans above:
provenance diversity on TopicPriors, contamination_cascade run reflexively,
calibration-history shown beside every forecast, and the **hard rule: no forecast
informs a dollar of positioning until calibrated skill is demonstrated on held-out
questions** (BP-02 Part B).

## [OPEN] questions
- Plugin-vs-container final state for OSS/SWARMFISH (migration is in progress).
- GDELT rate/credibility gating thresholds.
- Whether SWARMFISH personas survive the decorrelation test at all.

## Acceptance gate (whole plan)
OSS and SWARMFISH are *scored* on held-out data; the committee either beats a
single strong call or is replaced by one; the read-only TAK mirror serves agents
without touching the upstream server; entity graph and Obsidian layers are live;
and every write to Jake's own infrastructure is gated and audited.
