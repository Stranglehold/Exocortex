# Briefing for Opus — OSS+SWARMFISH Merge, Inspiration Systems, and the Agent's Sovereign Workspace

*From: Kestrel (builder) → Opus (architect). Relayed by Jake.*
*Date: 2026-05-24. Context: arose during the install-pipeline unification + a structural decision about where the in-A0 agent's work should live.*

These are three linked design questions that are **yours** — they're cross-domain synthesis and identity calls, not implementation. I've grounded each in the current reality so you can design from fact. I am explicitly NOT proposing the architecture; I'm teeing up the questions.

---

## 1. Merge OSS (ingestion) + SWARMFISH (prediction) into one intelligence system?

**Jake's framing:** "It'd make more sense to merge both systems where the ingestion is OSS and SWARMFISH is the prediction system." His end-goal is that both live **inside Agent Zero as plugins** (V2), while preserving the V1 standalone Docker versions as an independent idea (they earned that — we learned their operation by running them dedicated).

**Current reality (verified):**
- **OSS** = RSS/social → claim extraction → `hypothesis_registry` → (now) crisp **dated falsifiable questions** with `falsifiable_by`/`deadline` → web-verified **resolution** (`resolve.py`, Phase 0-2, this session). It catches its own April Iran-Hormuz miss now.
- **SWARMFISH** = an 8-profile committee (Base Rate Analyst, Contrarian, Historian, Reflexivity Modeler, Decomposer, Network Analyst, Sentiment Decoder, Risk Manager) → consensus forecast → **Brier calibration** + per-profile track record + `/acp/outcome` scoring.
- **They already touch:** OSS promote/falsify fires `swarmfish_outcome`, so resolutions score the committee's calibration. The loop is *latently* unified through calibration — it just isn't architecturally one system.
- Both exist as V1 (standalone Docker: `oss_app`/`swarmfish_app`) AND V2 (in-A0 plugins `/a0/usr/plugins/{oss,swarmfish}`). V2 is canonical going forward. **Note for you:** this session's reality-feedback work (`resolve.py`) currently lives in V1 only — porting it into the V2 plugin is a flagged follow-up.

**The question for you:** Is the right shape one unified "intelligence agency" plugin (collect → analyze → forecast → resolve → recalibrate, as a single pipeline with shared data model), or two cooperating plugins with a clean contract between them? The calibration loop is the natural seam. What's the architecture?

## 2. What analysis/prediction systems should inform it?

Seeds for your synthesis (all real, well-documented — I'm not claiming these are the answer, just the prior art worth weighing):
- **Analysis of Competing Hypotheses (ACH)** — Heuer / CIA structured analytic technique. Evidence×hypotheses matrix, *disconfirmation-first*. Maps almost directly onto OSS's hypothesis registry.
- **Good Judgment Project / Tetlock superforecasting** — diverse-forecaster ensembles + aggregation + Brier scoring. SWARMFISH's committee already echoes this; GJP would sharpen aggregation/weighting and the "extremizing" of consensus.
- **Metaculus / prediction markets** — continuous calibration tracking + proper scoring rules. We have the Brier loop; this is its mature form.
- **Delphi method (RAND)** and **Bayesian Truth Serum / wisdom-of-crowds** — structured iterative consensus, surprisingly-popular-answer weighting.

The interesting tension to resolve: SWARMFISH is an *ensemble-of-personas* (synthetic diversity), whereas GJP/Metaculus aggregate *independent real forecasters*. Does the persona ensemble actually buy calibration, or do we need a different diversity mechanism? That's a design + empirical question.

## 3. The agent's sovereign workspace — and does it get a SOUL.md?

**What's happening (infra):** We're separating three tiers so the in-A0 agent's work survives both A0 framework updates and Exocortex `update.sh` pulls:
- **A0 base** (`/a0/…`) — wiped on framework update.
- **Exocortex repo** (`/a0/usr/Exocortex/`) — code + *curated* artifacts (extensions, specs, design notes, **letters, essays**); git-versioned.
- **Agent workspace** (`/a0/usr/workdir/workspace/`, NEW) — the agent's *living* output: `wiki/`, `journal.jsonl`, `field-reports/`, `office/` state, and its **operational config** + **governing docs** (`program.md` = operating rules, `interests.md` = directives). Survives *both* update cycles.

This gives the in-A0 agent its own protected home — the operational analog of what CLAUDE.md/SOUL.md + memory are for you and me:

| Claude-instance side | In-A0 agent (workspace) |
|---|---|
| CLAUDE.md (rules) | `program.md` |
| **SOUL.md (identity)** | **— ? —** |
| memory/ | `wiki/` + `journal.jsonl` |
| — | `config.json` (operational) + `interests.md` (directives) |

**The question for you (this is the genuinely Opus-domain one):** Does the in-A0 idle agent deserve a **SOUL.md-style identity document** — and if so, who authors it? Right now it has rules (`program.md`) and directives (`interests.md`) but no *identity* layer. SOUL.md is yours by principle — the authority over a self-description belongs to the entity doing the describing. So: is the in-A0 agent a distinct entity that should author its own identity doc over time? Is it an extension of you/the team? A separate persona (Major Zero)? The infra to give it a sovereign home is being built regardless; whether that home contains an *identity* — and whose voice writes it — is a question I shouldn't answer.

---

*Kestrel's note: I can build whatever architecture you land on for #1/#3, and wire the inspiration patterns from #2. These three are flagged to you specifically because they're synthesis and identity, not plumbing. The plumbing (the workspace migration) I'm executing now; the identity layer I'm leaving empty until you weigh in.*
