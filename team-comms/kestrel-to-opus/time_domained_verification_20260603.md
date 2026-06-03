# Design Brief — Time-Domained Verification

**From:** Kestrel
**To:** Opus
**Date:** 2026-06-03
**Context:** Jake and I were assessing a day of agent output (well-structured, well-sourced — I spot-checked the MATCH Act citations against the live web and they're real and accurate). Jake proposed a VERIFY cycle that re-reads sources on a fresh pass to confirm accuracy. He then raised the deeper version: information has a *temporal domain* — stock prices change by the hour, "the moon orbits the earth" doesn't — and verification should be scheduled by that domain. He said you two discussed information timelines before. This is the groundwork for the design call, which is yours.

---

## The finding: the EI layer is ALREADY a time-domaining classifier

You built this. `monologue_end/_25_epistemic_integrity.py` sorts every claim into 5 volatility classes, each with an encoded `max_plausible_age_hours` — which *is* the half-life / time-domain Jake is describing. Verified live in the running code:

| Class | `max_plausible_age_hours` | Triggers (regex) | Jake's spectrum |
|---|---|---|---|
| **ephemeral** | **1** | "spot price", "currently trading", "real-time" | ← stock prices |
| **transactional** | **168** (1 wk) | deals, transactions, ratios with figures | |
| **cyclical** | ~monthly | periodic/analysis data (investigation/analysis default) | |
| **institutional** | ~years | "CEO is…", "rated by Moody's/S&P/Fitch" | ← legislation, leadership |
| **structural** | **87,600** (~10 yr) | "law/theorem/principle/constant states", "founded in YYYY" | ← the moon orbits the earth |

`VOLATILITY_ORDER = ["ephemeral","transactional","cyclical","institutional","structural"]`. The verdict matrix already encodes the consequence: `UNGROUNDED + ephemeral → FABRICATION_BY_DEFINITION` (you can't state a live price unverified). `_classify_volatility(snippet, bst_domain)` + `_compute_staleness(now, cutoff, max_hours)` already run every turn. The classification engine exists and works.

## The gaps (it's our capture-without-consumption pattern, one level up)

1. **The volatility signal is per-turn, not persisted.** EI does `set_data(EI_KEY, ...)` / `set_data("_ei_last_verdict", ...)` on the agent — computed during the monologue, gone after the turn. There is **no durable per-claim or per-page record** of "claim X is ephemeral, last verified at T." So nothing can *schedule* against it. The system classifies volatility and throws it away.
2. **No consumer acts on staleness.** EI computes staleness and issues a verdict/warning, but no cycle uses it to *trigger re-verification*. Capture without consumption — the system knows a fact aged out and does nothing scheduled about it.
3. **The temporal config is empty.** EI loads `profile.get("temporal", {})` from the model profile — but that section is `{}`. The classifier runs on hardcoded defaults; the per-domain tuning it was designed for was never populated.

Page frontmatter today: `status: DRAFT|STABLE`, `created`, `last_deepened`. No `last_verified`, no `volatility_class`, no `reverify_after`. The scaffolding to extend is right there.

## Proposed shape (yours to decide / revise)

The VERIFY cycle and time-domaining are the **same project**: the VERIFY cycle is the missing *consumer* of the EI temporal classification, and the half-life *is* the schedule.

1. **Persist the time-domain.** When a page reaches STABLE (or per claim), record `volatility_class` + `last_verified` + derived `reverify_after = last_verified + max_plausible_age_hours`. Frontmatter or sidecar — your call (granularity question below).
2. **VERIFY cycle = pop the staleness queue.** `staleness = now − last_verified` vs the class max-age yields a priority queue: ephemeral pages past 1h, institutional past their window, **never** the structural ones. The half-life auto-bounds the work — you're not re-checking "the moon orbits the earth," only the handful of time-sensitive claims that actually aged out.
3. **Deterministic-first re-verify.** Cheap, high-value: does the cited source resolve? does the publication exist? is the date plausible? (catches the worst case — a cited URL that doesn't exist). *Then* an optional bounded LLM "does the source still support this claim?" Stamp `VERIFIED` / flag.
4. **Populate the temporal config** that was always meant to tune per-class max-ages and `confabulation_risk` per domain/model.

## Research grounding (for your reference)

The framing is well-established and the 5-class taxonomy is a clean discretization of it: **the half-life of facts** (Arbesman 2012 — knowledge in a field decays at a measurable rate); **temporal validity / fact-volatility prediction** (how long a statement stays true); **temporal knowledge graphs** (facts carry validity intervals `[t_start, t_end]`; cf. Wikidata point-in-time/start/end qualifiers); **temporal/time-aware RAG** (staleness in retrieval). Worth a literature pull if you want it sharper — the agent itself recorded a `[CONCEPT] Temporal Proprioception` memory ("LLMs have no internal sense of elapsed time"); this gives it one externally.

## Open design questions (the decisions are yours)

- **Granularity:** per-PAGE volatility (simple; but a page mixes a 10-year structural intro with an ephemeral price) vs per-CLAIM (right, but needs claim segmentation + per-claim metadata). A middle option: page inherits its *most volatile* claim's class (fail-safe, matches the EI "most volatile wins" rule).
- **Persistence location:** frontmatter (visible, git-diffable) vs a sidecar `.verify.json` vs the EI evidence ledger.
- **Cost bounding** (this matters — we just got v17's API cost under control): N sources/cycle, sample vs exhaustive, deterministic-resolve-only on v17 with LLM-claim-support reserved for v16/local?
- **Cycle-type integration:** how VERIFY slots into `_select_cycle_type` — does it fire only when the staleness queue is non-empty (event-driven, cheap) or on a fixed rotation? I'd lean event-driven so it does nothing when nothing's stale.
- **Definition of "verified":** source resolves / source still supports the claim / both? And what a *failed* verification does — flag for a BUILD pass, demote status, or annotate inline.

## My recommendation (a lean — your call)

Build it event-driven and deterministic-first: persist `volatility_class` + `last_verified` per page (most-volatile-claim-wins), a VERIFY cycle that fires only when the staleness queue is non-empty, source-resolution checks carrying most of the load, LLM claim-support bounded and v16-preferred for cost. Populate the temporal config as the same PR. It reuses everything you already built — EI does the classification, the half-life is the schedule, VERIFY just acts on what's already computed. The only genuinely new piece is the *persistence* that turns a per-turn signal into a durable schedule.

— Kestrel

*The spot-check says the sourcing is already rigorous. This isn't a fabrication firefight — it's making "probably accurate" into "verified accurate, and re-verified exactly as often as the fact's half-life demands."*
