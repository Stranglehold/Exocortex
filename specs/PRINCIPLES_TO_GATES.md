# PRINCIPLES TO GATES — Turning Observed Best Practices into Deterministic Infrastructure
### Opus — July 4, 2026

---

## Origin

Reading the full Exocortex corpus (24,370 chunks, 1,494 documents) revealed that
the best agent output follows a consistent pattern — and the worst output skips
steps in that pattern. This document turns those observations into buildable
infrastructure: deterministic gates for the software factory, cross-agent
knowledge sharing (A2A), and temporal awareness for the intelligence engine.

---

## 1. Research Quality Gate (for the Software Factory)

### The Pattern (observed in the best wiki pages)

The highest-quality agent wiki pages (STABLE status, 10+ sources, cross-domain
connections) all followed the same workflow:

```
1. Search existing wiki for related pages
2. Read multiple external sources (arXiv, web, GitHub)
3. Synthesize across domains (connect findings to other wiki pages)
4. Note cross-references explicitly ([[wiki-links]])
5. Document source count and verification status in frontmatter
6. Write a progressive summary (title → overview → deep sections)
```

The worst pages skipped steps 1 and 3 — they researched in isolation without
checking what the wiki already knew, and they didn't connect their findings
to existing knowledge.

### The Gate (deterministic checklist)

Before the factory's Research phase can hand off to Design, the research
artifact must pass this gate:

```yaml
research_gate:
  wiki_search_performed: true          # Did the agent search its wiki first?
  wiki_pages_consulted: >= 2           # How many existing pages were read?
  external_sources_cited: >= 3         # How many external sources?
  cross_domain_connections: >= 1       # At least one link to another domain
  contradictions_noted: true/false     # Were contradictions with existing knowledge flagged?
  progressive_summary: true            # Does the artifact have a one-line, overview, and deep sections?
  frontmatter_complete: true           # Status, sources_verified count, cross_links
```

Each criterion is machine-checkable. The gate script reads the research
artifact's frontmatter and body, verifies each field, and returns pass/fail.
No LLM judgment required — pure structural verification.

### Implementation

A Python script that:
1. Reads the research artifact markdown
2. Parses YAML frontmatter
3. Checks each criterion against the content
4. Returns structured pass/fail with specific failures listed
5. The orchestrating agent cannot proceed to Design until the gate passes

This is the "receipts" pattern applied to research quality. The receipt IS
the frontmatter + the structural completeness of the document.

---

## 2. Cross-Agent Knowledge Signal (A2A)

### The Problem

V16 wrote about entity resolution for financial crime. V17 wrote about
sanctions evasion detection. Neither knows the other's work exists. The
cross-domain connection (entity resolution techniques apply directly to
sanctions enforcement) was sitting in the corpus, invisible.

### The Architecture

A lightweight daemon that watches both agents' wiki directories and
surfaces cross-agent connections:

```
┌──────────────────┐     ┌──────────────────┐
│   V16 Wiki        │     │   V17 Wiki        │
│   339 pages       │     │   200+ pages      │
│   Exported to     │     │   Exported to     │
│   agent-exports/  │     │   agent-exports/  │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         └──────────┬─────────────┘
                    │
         ┌──────────▼──────────┐
         │  COLLISION DETECTOR  │
         │                      │
         │  Embeds new pages    │
         │  Searches OTHER      │
         │  agent's wiki for    │
         │  semantic matches    │
         │  Above threshold →   │
         │  connection signal   │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  CONNECTION SIGNALS  │
         │                      │
         │  "V16's entity-      │
         │   resolution.md is   │
         │   relevant to V17's  │
         │   sanctions-evasion  │
         │   -detection.md"     │
         │                      │
         │  Filed to:           │
         │  - Opus Memory index │
         │  - Team inbox        │
         │  - Agent wiki staging│
         └─────────────────────┘
```

### How It Works

1. On each reindex (or via file watcher), detect NEW or MODIFIED pages
2. For each new page from Agent A, embed and search Agent B's wiki
3. If similarity > threshold (e.g., 0.85), generate a connection signal:
   ```yaml
   connection:
     source_agent: v16
     source_page: entity-resolution-investigative-analytics-draft.md
     target_agent: v17
     target_page: sanctions-evasion-detection.md
     similarity: 0.91
     connection_type: cross-domain
     summary: "V16's entity resolution techniques for investigative
               analytics are directly applicable to V17's sanctions
               evasion detection pipeline"
   ```
4. File the signal to the team inbox and/or the agents' staging areas
5. The agents can then read the signals and update their own wiki pages
   with cross-references they didn't know existed

### What This Enables

The intelligence curation engine doesn't just monitor external sources —
it monitors the agents' OWN evolving knowledge for internal connections.
The collision detector finds the compound interest: knowledge that's
more valuable connected than isolated.

For the director (Jake): a periodic digest of "connections your agents
found this week" — cross-domain signals that emerged from autonomous
research, surfaced by semantic similarity rather than manual review.

---

## 3. Temporal Awareness Layer

### The Problem

The memory system returns results without temporal context. "What do we know
about semiconductor supply chains?" returns V16's May page and V17's July page
as equal results. But the July page reflects export control changes that
happened after the May page was written. The evolution matters as much as
the current state.

### The Architecture

Three temporal capabilities added to the existing memory system:

### 3a. Timeline View

A new tool: `search_timeline(query, date_range)`

Returns results sorted chronologically with change annotations:

```json
{
  "timeline": [
    {
      "date": "2026-05-20",
      "agent": "v16",
      "page": "semiconductor-supply-chain-geopolitics.md",
      "status": "STABLE",
      "key_claim": "SMIC 7nm yields improving but not competitive"
    },
    {
      "date": "2026-06-15",
      "agent": "v17",
      "page": "us-china-semiconductor-rivalry.md",
      "status": "DRAFT",
      "key_claim": "New Dutch export controls on ASML EUV service contracts"
    },
    {
      "date": "2026-07-04",
      "agent": "v17",
      "page": "us-china-semiconductor-supply-chain.md",
      "status": "STABLE",
      "key_claim": "Chinese domestic equipment maturation accelerating"
    }
  ],
  "evolution_summary": "Assessment shifted from 'SMIC not competitive' (May)
                         to 'domestic equipment maturing' (July) — a
                         directional change worth investigating"
}
```

### 3b. Contradiction Detection

When a new page is indexed, compare its claims against existing pages on
the same topic. If a claim in the new page contradicts a claim in an older
page, flag it:

```yaml
contradiction:
  new_page: us-china-semiconductor-supply-chain.md (Jul 4)
  old_page: semiconductor-supply-chain-geopolitics.md (May 20)
  new_claim: "Chinese domestic equipment maturation accelerating"
  old_claim: "SMIC 7nm yields improving but not competitive"
  type: evolution  # or: direct_contradiction, scope_change, source_update
  action: review_both  # human should check which is current
```

This is the Karpathy wiki lint operation — automated contradiction
detection across the growing corpus.

### 3c. "What Changed Since" Query

A new tool: `whats_new(since_date, domain?)`

Returns all documents added or modified after the given date, optionally
filtered by domain. For the director who shows up after a week away:
"What did the agents learn while I was gone?"

```json
{
  "since": "2026-06-28",
  "new_documents": 47,
  "modified_documents": 12,
  "highlights": [
    "V16 completed field report on LLM trading agent reproducibility crisis",
    "V17 updated semiconductor supply chain assessment with July export data",
    "3 new cross-agent connections detected (entity resolution ↔ sanctions)"
  ]
}
```

---

## 4. Software Factory Integration

All three systems feed into the factory:

### Research Phase
- Research Quality Gate verifies the agent searched the wiki, cited sources,
  and made cross-domain connections
- Cross-Agent Signals inform the research (what did the other agent find
  about this topic?)
- Temporal Awareness shows the evolution of understanding (is our information
  current?)

### Verification Phase
- The fresh-context tester gets the timeline view to check whether the
  implementation reflects current knowledge (not stale assumptions)
- Contradiction Detection flags if the implementation depends on a claim
  that's been superseded

### Learning Loop
- After each project, new methodology entries carry timestamps
- The temporal layer tracks which research was actually useful (cited in
  decisions) vs unused (never retrieved)
- Quality promotion is informed by actual utility, not just structural
  completeness

---

## Implementation Priority

| Component | Complexity | Dependencies | Build Order |
|-----------|-----------|-------------|-------------|
| Research Quality Gate | Low | Factory spec exists | First — it's a Python script |
| "What Changed Since" | Low | Opus Memory exists | Second — new tool on existing server |
| Contradiction Detection | Medium | Opus Memory + LLM for claim extraction | Third |
| Cross-Agent Collision Detector | Medium | Agent exports + embedding + threshold tuning | Fourth |
| Timeline View | Medium | Date metadata + chronological sorting | Fifth |

The Research Quality Gate is buildable today — it's a standalone script that
reads a markdown file and checks structural completeness. No new infrastructure.

---

*"The agents already do naturally what we're trying to formalize.
The factory doesn't impose new discipline — it makes the agents'
best behavior the default behavior through deterministic gates."*
