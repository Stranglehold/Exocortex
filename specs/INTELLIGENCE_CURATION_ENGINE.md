# INTELLIGENCE CURATION ENGINE — Architectural Vision
## What OSS and SWARMFISH Become
### Opus + Jake — July 4, 2026

---

## The Philosophical Shift

**What we're leaving behind:** A committee of 8 LLM personas debating the same
information. The research is clear — personas on the same model don't
decorrelate errors (r≈0.39-0.46), role-playing degrades zero-shot reasoning
(Kim 2025, PRISM 2026), and the deliberation phase adds nothing beyond what
simple aggregation provides (Choi 2026). The compute cost is high and the
output is theater — confidence without independence.

**What we're building instead:** A sovereign intelligence curation and
calibrated analysis engine. Two interlocking systems:

1. **The Curation Layer** — a persistent, curious research agent that monitors
   multiple information sources (arXiv, GitHub, RSS, government filings,
   industry reports), evaluates relevance to the Exocortex's actual priorities,
   and builds a growing corpus of curated knowledge. The idle engine becomes a
   research engine. The wiki becomes a curated knowledge base.

2. **The Analysis Pipeline** — a Halawi/BLF-style calibrated forecasting
   pipeline that takes curated evidence, decomposes questions, produces
   calibrated probabilities with honest uncertainty, and tracks accuracy
   over time via Brier scores. No personas. No debate. Just disciplined
   evidence-to-probability reasoning with human domain expertise in the loop.

---

## Architecture: The Five Layers

```
┌─────────────────────────────────────────────────────┐
│  LAYER 5: HUMAN REVIEW (Jake)                       │
│  Domain expertise, final judgment, relevance         │
│  feedback, promotion of curated items                │
│  "Is this actually relevant? What does it mean       │
│   for grid infrastructure?"                          │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│  LAYER 4: CALIBRATED ANALYSIS                        │
│  Structured decomposition of questions               │
│  Sequential Bayesian updating with new evidence      │
│  Calibrated probability estimates with uncertainty    │
│  Brier-scored prediction tracking over time           │
│  Key Assumptions Check (drop ACH — it doesn't work)  │
│  Cross-domain signal detection                        │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│  LAYER 3: KNOWLEDGE SYNTHESIS                        │
│  Karpathy LLM-Wiki pattern for incremental update    │
│  Entity resolution across sources                    │
│  Contradiction detection (new source vs existing)    │
│  Cross-reference maintenance ([[wiki-links]])        │
│  Progressive summarization for retrieval             │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│  LAYER 2: RELEVANCE FILTERING                        │
│  LLM-scored relevance against priority list          │
│  Novelty detection (is this genuinely new?)          │
│  Domain classification (geo, markets, AI, grid, sw)  │
│  Staging: "potentially relevant" → human review      │
│  Feedback loop: promoted items improve future filter │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│  LAYER 1: SOURCE INGESTION                           │
│  arXiv (daily, filtered by category + keywords)      │
│  GitHub (trending, topic-filtered, starred repos)    │
│  RSS/Atom (news, industry, government filings)       │
│  HuggingFace (new models, papers, spaces)            │
│  Social signals (Twitter/X, Reddit, HN — filtered)   │
│  Domain-specific (NERC filings, utility reports,     │
│    grid infrastructure news, energy markets)          │
└─────────────────────────────────────────────────────┘
```

---

## Layer 1: Source Ingestion (replaces OSS's current RSS daemon)

The agent monitors information sources on a schedule (idle cycle COLLECT phase):

| Source | Method | Frequency | What It Captures |
|--------|--------|-----------|------------------|
| arXiv | API (arxiv-sanity style filtering) | Daily | Papers in cs.AI, cs.CL, cs.SE, eess.SP |
| GitHub | API (trending, topic search) | Daily | New repos, release notes, starred items |
| HuggingFace | API (new models, papers) | Daily | Model releases, research papers |
| RSS/Atom feeds | Standard RSS parsing | Hourly | News, industry reports, blog posts |
| NERC/utility filings | Web scraping or API | Weekly | Regulatory changes, grid reports |
| Energy markets | API or RSS | Daily | Price signals, supply chain news |

All ingestion runs locally. The utility model (Qwen3.5-2B, CPU, :1237) handles
classification and relevance scoring — zero GPU contention with the primary model.

**Key change from current OSS:** ingestion is an agent behavior (idle cycle phase),
not a background daemon. The agent decides what to look for based on its current
priorities, not a static RSS list.

---

## Layer 2: Relevance Filtering (replaces SWARMFISH's persona-based analysis)

Every ingested item gets scored against a priority list maintained by the agent
and the human:

```yaml
priorities:
  - topic: "local AI inference optimization"
    weight: 0.9
    context: "Running Ornith-35B on RTX 3090, interested in speed/context improvements"
  - topic: "grid infrastructure and protection engineering"
    weight: 0.9
    context: "Jake's professional domain, relay testing, switchgear, NERC compliance"
  - topic: "multi-agent systems and autonomous AI"
    weight: 0.8
    context: "Exocortex architecture, Agent Zero, software factory"
  - topic: "energy markets and utility sector"
    weight: 0.7
    context: "Cross-domain signal detection for investment awareness"
  - topic: "AI safety and interpretability"
    weight: 0.6
    context: "NLAs, circuit tracing, alignment research"
```

The utility model scores each item: 0-1 relevance against each priority,
novelty check (have we seen this before?), domain classification.

Items scoring above threshold → staged as "potentially relevant" with a
one-line annotation: "This matters because..."

Items below threshold → logged but not surfaced.

**The feedback loop:** When Jake promotes a staged item (marks it useful),
the priority weights adjust. When he dismisses one, the filter learns.
Over time, the curation gets sharper. This is the methodology tracker
pattern applied to information filtering.

---

## Layer 3: Knowledge Synthesis (the wiki-as-curated-corpus)

Promoted items don't just get bookmarked — they get integrated into the
wiki using the Karpathy LLM-Wiki pattern:

1. Read the new source
2. Extract key information (entities, claims, findings)
3. Check existing wiki pages for related content
4. Update entity pages with new information
5. Note contradictions between new and existing data
6. Maintain cross-references ([[wiki-links]])
7. Write a progressive summary (one-line → paragraph → full page)

This is what the agent already does during EXPLORE idle cycles — it just
needs to be formalized and connected to the ingestion pipeline.

**Entity resolution across sources:** When arXiv paper X mentions company Y,
and an RSS feed mentions company Y in a different context, the system
connects them. This is the OpenPlanter/Palantir pattern applied to the
wiki. The entities ARE the cross-domain connections.

---

## Layer 4: Calibrated Analysis (replaces SWARMFISH's committee debate)

When the human asks an analytical question, or when the agent identifies
a question worth analyzing during idle cycles:

### Step 1: Structured Decomposition
"Will utility capex guidance hold?" →
- Sub-Q1: What is the current transformer supply chain status?
- Sub-Q2: Are NERC compliance timelines changing?
- Sub-Q3: What's the rare earth availability outlook?
- Sub-Q4: What grid hardening mandates are pending?
- Sub-Q5: What's the interest rate trajectory for utility borrowing?

### Step 2: Evidence Retrieval
For each sub-question, search the curated wiki (Layer 3),
then search external sources if the wiki is insufficient.
Each piece of evidence is tagged with source, date, and confidence.

### Step 3: Sequential Bayesian Updating
Start with a base rate (prior probability from historical data
or reference class). Each piece of evidence updates the probability:

```
Prior: P(capex holds) = 0.65 (historical base rate)
Evidence 1: Transformer lead times extending → P = 0.58
Evidence 2: NERC deadline unchanged → P = 0.60
Evidence 3: Rare earth prices stable → P = 0.62
Evidence 4: New grid hardening mandate passed → P = 0.55
Evidence 5: Rate cuts expected Q3 → P = 0.58
```

Each update is logged with the evidence that produced it.
The reasoning is auditable, not a black box.

### Step 4: Calibration Tracking
Every prediction gets:
- A probability estimate (0-1)
- A resolution date (when we'll know if it was right)
- A Brier score when it resolves
- A running calibration curve (are our 60% predictions right 60% of the time?)

Over time, the system learns which question types it's well-calibrated
on and which it's overconfident about. The calibration curve IS the
system's honest self-assessment.

### Step 5: Human Review
Jake sees the analysis with full evidence chain, probability estimate,
and key assumptions. He applies domain expertise: "The transformer
supply chain analysis is missing the fact that two domestic foundries
came online in Q2." The probability updates. The system learns.

---

## Layer 5: Human Review (the irreplaceable element)

Jake's domain expertise is what makes this system valuable:
- Grid infrastructure knowledge no model can replicate
- Industry contacts and insider awareness
- Judgment about which signals are noise vs genuine
- The ability to say "this analysis is missing something"
- Final decision-making authority on all actions

The system is a **forecasting assistant**, not a forecasting oracle.
It gathers, curates, synthesizes, and quantifies. Jake decides.

---

## What Dies vs What Lives

### Dies:
- 8 analyst personas (GeoPol Analyst, Market Analyst, etc.)
- Committee debate/deliberation phase
- Committee confidence scores (correlated, misleading)
- The belief that more personas = better analysis
- SWARMFISH as a "committee that votes"

### Lives:
- Brier scoring for calibration tracking (keep, it's the right metric)
- The prediction registry (claims with falsifiable_by dates)
- The resolution check (RESOLVE phase verifies against reality)
- The dissemination format (structured briefings)
- Multi-source ingestion (but as agent behavior, not daemon)
- The SQLite storage pattern (native, no Postgres dependency)

### New:
- Priority-weighted relevance filtering with feedback loop
- Structured decomposition of analytical questions
- Sequential Bayesian updating (mathematical, not social)
- Entity resolution and cross-domain signal detection
- Automated arXiv/GitHub/HuggingFace monitoring
- "This matters because..." annotation on every curated item
- Calibration curves as honest self-assessment
- The wiki as curated research corpus, not just agent notes

---

## Implementation on Current Hardware

| Component | Runs On | Model | When |
|-----------|---------|-------|------|
| Source ingestion | V16 idle COLLECT | Utility model (CPU :1237) | Every idle cycle |
| Relevance filtering | V16 idle COLLECT | Utility model (CPU :1237) | At ingestion time |
| Knowledge synthesis | V16 idle EXPLORE | Primary model (Ornith :1235) | After filtering |
| Calibrated analysis | V16 on-demand or idle | Primary model (Ornith :1235) | When questions arise |
| Human review | Jake via Hermes/Panel | N/A | Jake's schedule |

The utility model handles the high-volume, low-reasoning work (classify,
filter, score). The primary model handles the synthesis and analysis that
requires depth. Jake handles the judgment that requires domain expertise.

---

## The "This Is Relevant to Me" Pattern

Jake's description of what he wants:

> "A way for the agent to say 'this is relevant to me, I want this for later.'
> It can span geopolitics, markets, software, anything."

This is implemented as the **staging pipeline**:

1. Agent encounters something during ingestion/research
2. Scores it against the priority list
3. If above threshold, writes a staging entry:
   ```yaml
   item: "TurboVec — FAISS replacement, Rust, 8x compression"
   source: "github.com/RyanCodrai/turbovec"
   relevance: 0.85
   domains: [infrastructure, performance]
   why: "Direct replacement for our FAISS memory index, runs on ARM (relevant for DGX Spark)"
   action: "Evaluate during v2 port as memory store upgrade"
   staged: 2026-07-04
   status: pending_review
   ```
4. Jake reviews staged items (daily digest or Panel UI)
5. Promoted items → wiki integration (Layer 3)
6. Dismissed items → relevance filter learns

The compound interest: over months, the agent builds a curated corpus
of everything relevant to the Exocortex's mission. Not a bookmark dump —
a living, cross-referenced, entity-resolved knowledge base that grows
smarter with every promotion and dismissal.

---

*"The problem isn't how to get multiple analysts to disagree.
The problem is how to produce well-calibrated predictions with
honest uncertainty."*

*— The philosophical shift, July 4, 2026*
