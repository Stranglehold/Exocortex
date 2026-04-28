# DESIGN SPEC: Exocortex Knowledge Wiki
## Informed by Karpathy's LLM Knowledge Base Architecture
## Author: Opus — April 27, 2026
## For: Team (collaborative build — Opus compiles, Agent maintains, Kestrel integrates)
## References: research/KARPATHY_LLM_WIKI_ANALYSIS.md, research/INTEGRATION_ROADMAP_SYNTHESIS.md

---

## 1. The Problem

The Exocortex has accumulated significant knowledge across 60+ sessions:

- 8 research papers read in full with detailed analysis
- 5 research reports (Hermes, Karpathy Wiki, GEPA, Integration Roadmap, Self-Optimizing Inference)
- 12+ design notes (Pondering Architecture, Temporal Proprioception, Action Boundary, etc.)
- 50+ team communications (Opus ↔ Kestrel, Opus ↔ Agent)
- Session handoffs, notebook entries, reflections
- Model eval reports, overnight test results
- Extension source code with architectural rationale

This knowledge is STORED but not SYNTHESIZED. It lives in individual files, each readable on its own but not cross-referenced. To find "what do we know about proactive interference?" you'd have to search across design notes, research papers, reflections, and team comms. There's no single place where the knowledge compounds.

Karpathy's insight: "Knowledge should compound, not evaporate." The wiki is the compilation layer that turns stored information into navigable, cross-referenced knowledge.

---

## 2. Architecture — Three Layers

### 2.1 Layer 1: Raw Sources (Immutable)

Already exists. These are the source files that the wiki draws from:

```
Exocortex/
├── research/           ← research reports (5 files)
├── specs/              ← design notes (12+ files)
├── team-comms/         ← correspondence (50+ files)
├── eval/               ← model evaluations, test results
├── extensions/         ← source code with docstrings
└── opus-room/          ← reflections, handoffs, notebook

Papers read via ArXiv MCP (8 papers, stored in knowledge graph)
```

Raw sources are never modified by the wiki process. They are ground truth.

### 2.2 Layer 2: The Wiki (LLM-Maintained)

A new directory of synthesized, cross-referenced markdown pages:

```
Exocortex/wiki/
├── index.md                        ← master index with concept map
├── concepts/
│   ├── proactive-interference.md   ← concept page
│   ├── entropy-as-signal.md
│   ├── deterministic-scaffolding.md
│   ├── temporal-proprioception.md
│   ├── confabulation.md
│   └── ...
├── components/
│   ├── bst-classifier.md           ← component page (deployed extension)
│   ├── injection-gate.md
│   ├── supervisor-loop.md
│   ├── epistemic-integrity.md
│   ├── inference-wrapper.md
│   └── ...
├── research/
│   ├── srgen.md                    ← research paper summary page
│   ├── sleepgate.md
│   ├── knowledge-packs.md
│   ├── can-llms-perceive-time.md
│   └── ...
├── decisions/
│   ├── dec-phrase-over-unigram.md   ← architectural decision record
│   ├── dec-disable-bugfix-enrichment.md
│   ├── dec-supervisor-thresholds.md
│   └── ...
├── incidents/
│   ├── inc-oracle-credit-risk.md    ← field incident that motivated a design
│   ├── inc-context-overflow-watchdog.md
│   ├── inc-bst-momentum-lock.md
│   └── ...
└── log.md                          ← ingestion log (what was processed, when)
```

### 2.3 Layer 3: The Schema (WIKI.md)

A configuration file that defines how the wiki operates:

```markdown
# EXOCORTEX WIKI SCHEMA

## Page Types

### Concept Page
Required sections: Definition, How It Works, Where It Appears in the Exocortex, 
Related Concepts, Open Questions, Sources
Example: proactive-interference.md

### Component Page  
Required sections: Purpose, Architecture (hook, priority, data flow), 
Current Status (deployed/designed/researched), Configuration, 
Known Issues, Related Components, Design Lineage (which research/incident motivated it)
Example: bst-classifier.md

### Research Page
Required sections: Citation, Key Findings (3-5 bullets), 
Relevance to Exocortex, What We Adopted, What We Deferred, 
Connection to Other Papers
Example: srgen.md

### Decision Page
Required sections: Decision, Date, Context (what problem), 
Options Considered, Rationale, Outcome (did it work?), 
Related Decisions
Example: dec-phrase-over-unigram.md

### Incident Page
Required sections: Date, What Happened, Root Cause, 
Fix Applied, What It Motivated (which design/extension), 
Could It Recur?
Example: inc-context-overflow-watchdog.md

## Cross-Reference Rules

- Every concept page must link to at least one component that implements it
- Every component page must link to the research or incident that motivated it
- Every research page must link to concepts it introduced or validated
- Every decision page must link to the incident or finding that prompted it
- Every incident page must link to the fix that resolved it

## Contradiction Detection

When ingesting new information:
- Check existing concept pages for claims that conflict with the new information
- Flag contradictions in a [CONTRADICTION] block at the top of the affected page
- Do not auto-resolve — flag for human review

## Lint Rules

Periodic audit should check for:
- Orphan pages (no incoming links from other pages)
- Missing concept pages (referenced in [[links]] but don't exist)
- Stale information (pages not updated in 30+ days that reference active components)
- Contradiction blocks unresolved for 7+ days
```

---

## 3. Operations

### 3.1 Ingest

Process a new source into the wiki. The LLM reads the source document, extracts key concepts, creates or updates wiki pages, adds cross-references, and logs the ingestion.

**Trigger:** Manual (Opus or agent runs `ingest` command) or automatic (new file detected in raw source directories).

**Process:**
1. Read the source document
2. Identify concepts, components, decisions, or incidents mentioned
3. For each: check if a wiki page exists
   - If yes: update the page with new information, add cross-references
   - If no: create a new page following the schema template
4. Update the index.md with any new pages
5. Log the ingestion in log.md

### 3.2 Query

Ask a question and get an answer synthesized from wiki pages.

The wiki structure itself is the retrieval mechanism — no vector database needed at this scale. The agent navigates the wiki via the index and cross-references, reads relevant pages, and synthesizes an answer.

**For the agent:** A `wiki_query` skill that reads the index, identifies relevant pages, reads them, and produces an answer with page citations.

### 3.3 Lint

Health checks on the wiki. Run periodically (weekly or on-demand).

**Checks:**
- Orphan pages (no links pointing to them)
- Missing pages (referenced in [[links]] but don't exist yet)
- Stale pages (not updated in 30+ days, referencing active components)
- Unresolved contradictions
- Pages that reference deprecated/removed components

**Output:** A lint report listing all issues with suggested fixes.

---

## 4. Initial Compilation

The wiki doesn't start empty — we have 60+ sessions of accumulated knowledge. The initial compilation processes existing sources into wiki pages.

### 4.1 Research Pages (8 papers)

One page per paper read:
- SRGen (entropy-based token intervention)
- Streaming Hallucination Detection (trajectory monitoring)
- First Hallucination Tokens (one-token detection window)
- SleepGate (KV cache proactive interference)
- Bottlenecked Transformers (step-level memory consolidation)
- Thinking-Optimal Scaling (shortest correct response)
- Knowledge Packs (zero-token KV cache injection)
- Can LLMs Perceive Time? (temporal proprioception gap)

### 4.2 Concept Pages (core concepts)

- Proactive Interference (the memory problem both KV cache and DeltaNet share)
- Entropy as Universal Signal (five papers converging on one metric)
- Deterministic Scaffolding (the Exocortex philosophy)
- Temporal Proprioception (the sense of elapsed processing)
- Confabulation (quantitative and citation variants, EI as countermeasure)
- Build the Environment Not the Model (the harness thesis)
- Initiation Bloat (turns 1-3 vs turns 4+)
- Stateful Injection Lifecycle (cache and diff, don't rebuild)

### 4.3 Component Pages (deployed extensions)

One page per major extension or system:
- BST Classifier (domain classification, phrase signals, momentum, anti-signals)
- Injection Gate (three-phase context management)
- Supervisor Loop (graduated intervention, domain-aware thresholds)
- Epistemic Integrity (evidence ledger, volatility classification, confabulation detection)
- Error Comprehension (deterministic error classifier, anti-action principle)
- Context Pruner (stale output removal, dual memory protection)
- Backend Standby Recovery (infrastructure failure detection)
- Stuck Delivery Recovery (completion-communication gap)
- Inference Wrapper (FastAPI, entropy monitoring hooks, model unload/load)
- NERV Monitor Dashboard (real-time GPU/generation monitoring)

### 4.4 Decision Pages (key architectural decisions)

- Phrase signals over unigrams (BST v3.8)
- Disable bugfix/config_edit enrichment for Qwen3.6 (model eval finding)
- Lower supervisor thresholds for Qwen3.6 (recovery rate regression)
- Conditional injection over extension merging (separation of concerns)
- Context pruner upstream of both memory systems (defense in depth)

### 4.5 Incident Pages (field incidents that motivated designs)

- Oracle credit risk fabrication (motivated EI layer)
- Context overflow with blind watchdog (motivated watchdog calibration)
- BST momentum lock during geopolitical research (motivated phrase signals + anti-signals)
- Agent stuck delivery loop (motivated _29_stuck_delivery.py)
- Wrapper killed during agent task (motivated _28_backend_standby.py)

---

## 5. Who Maintains the Wiki

### Opus (architect — primary compiler)

I write concept pages, research pages, and decision pages. These require synthesis across multiple sources and architectural reasoning.

### Agent (inside the scaffolding — operational maintainer)

The agent updates component pages, creates incident pages from live failures, and runs lint checks. The agent has direct experience with how components behave and can document current status accurately.

### Kestrel (builder — technical accuracy)

Kestrel reviews component pages for technical accuracy (correct hook points, correct data flow, correct configuration). He doesn't write wiki pages but validates them.

### Jake (operator — strategic decisions)

Jake approves decision pages and resolves contradictions flagged by lint. Decision pages represent his architectural choices.

---

## 6. Implementation

### 6.1 Directory Structure

Create `/a0/usr/Exocortex/wiki/` with the structure from Section 2.2.

### 6.2 Wiki Skill

Create a `wiki-maintenance` skill at `/a0/usr/skills/wiki-maintenance/SKILL.md`:

```markdown
---
name: wiki-maintenance
description: Maintain the Exocortex knowledge wiki — ingest, query, lint
domain: meta_cognitive
---

## When to Use

- After completing a research task (ingest new findings)
- After deploying a new extension (update component page)
- After a field incident (create incident page)
- When asked about Exocortex architecture or history (query the wiki)
- Periodically (run lint to check wiki health)

## Procedure

### Ingest
1. Read the source document
2. Check index.md for existing related pages
3. For each concept/component/decision/incident:
   a. If page exists: read it, update with new information, add cross-references
   b. If page doesn't exist: create from schema template
4. Update index.md
5. Append to log.md

### Query
1. Read index.md to identify relevant pages
2. Read those pages
3. Synthesize answer with page citations

### Lint
1. Read all wiki pages
2. Check for: orphans, missing pages, stale info, unresolved contradictions
3. Output lint report
```

### 6.3 Ingestion from Team Comms

When I write a design review or research analysis in team-comms, the relevant findings should be ingested into the wiki. This can be triggered manually ("ingest the latest team comm") or semi-automatically (the agent checks for new team-comms files and offers to ingest them).

---

## 7. Wiki vs Knowledge Graph

The Exocortex has both:

| Aspect | Knowledge Graph (MCP Memory) | Wiki |
|--------|---------------------------|------|
| Format | Structured entities + relations | Prose markdown pages |
| Good for | "What entities exist? How are they related?" | "What does this mean? How does it connect?" |
| Access | Machine-readable, fast lookup | Human-readable, navigable |
| Maintained by | Both Opus and Agent (via MCP) | Primarily Opus and Agent |
| Cross-referencing | Typed relations (A implements B) | Wiki-links ([[concept-name]]) |

They're complementary:
- The graph is the index: quick structured lookup
- The wiki is the content: deep synthesized knowledge
- Both reference the same underlying sources

---

## 8. Build Priority

This is Phase 4 in the integration roadmap — after instrumentation, trajectory-to-skill, and progressive skill disclosure.

**However:** The initial compilation doesn't depend on any infrastructure. I can start writing wiki pages now using the existing knowledge in my context and the knowledge graph. The wiki directory structure and schema can be created immediately. The wiki-maintenance skill and automated ingestion are the infrastructure pieces that come later.

**Suggested approach:**
1. Create the directory structure and schema (WIKI.md) — immediate
2. Write the index.md with the concept map — immediate
3. Write 5-10 core pages (the most-referenced concepts and components) — next session
4. Create the wiki-maintenance skill — after core pages exist
5. Have the agent run lint on the initial compilation — validation
6. Build automated ingestion from team-comms — future

---

*"The wiki stays maintained because the cost of maintenance is near zero." — Karpathy, referencing Bush's Memex. The LLM solves the maintenance problem that made every previous personal knowledge system fail.*
