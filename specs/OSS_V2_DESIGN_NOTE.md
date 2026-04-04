# OSS V2 Design Note
## The Analyst Inside the Ledger

**Status:** Pre-spec design note. Informed by: Kestrel's investigation brief (2026-04-02), OSS V1 operational experience (ports 7731, ingestion pipeline running since Session 056), artifact framework deployment (v1.6 migration), world models research thread (prediction error as anomaly signal), SHIX behavioral indicator spec (analyst-driven signal capture). No eval data on V2 patterns yet. This document captures the human relationship model and architecture sketch for an intelligence ledger the analyst works inside, not alongside.

**Author:** Opus (architecture), informed by Kestrel (investigation brief + V1 implementation), Jake (strategic direction + "I feel like I don't have proper influence or control over them")
**Date:** 2026-04-03

---

## 1. The Design Brief

Jake's sentence: "I feel like I don't have proper influence or control over them."

That sentence is the entire V2 requirement. V2 is complete when that sentence is no longer true.

OSS V1 was designed as an autonomous pipeline. It ingests, extracts, classifies, deduplicates, and stores. Jake can query the results. He can submit his own observations. He can toggle ingestion on or off. But he can't shape what the pipeline pays attention to. He can't see what it rejected. He can't challenge its classifications. He can't evolve the questions the ledger is organized around. He's a reader of the ledger, not a participant in its construction.

V2 inverts the relationship. The analyst isn't outside the pipeline reading its output. The analyst is inside the pipeline, directing its attention, weighting its sources, evolving its questions, and seeing its work at every stage. The pipeline is a collaborator that adapts to what the analyst currently wants to know.

---

## 2. Design Principles

**2.1 Question-oriented, not topic-oriented.** V1 organizes around static topic labels ("iran", "iran-hormuz"). V2 organizes around analyst questions that evolve: "Will Iran block the strait?" → "How is Iran managing escalation pressure?" → "What domestic factors constrain Iranian decision-making?" The question is the organizing principle. Claims are relevant to the extent they bear on the current question, not to the extent they match a keyword.

**2.2 Attention is directable.** The analyst can say "focus on logistics, ignore diplomatic statements right now" and the pipeline adjusts. This isn't filtering after the fact — it's directing the extraction process to weight certain evidence types over others. The pipeline has a concept of what the analyst currently wants to know, and that concept shapes what it collects, how it prioritizes, and what it surfaces first.

**2.3 Work is visible.** Every stage of the pipeline — ingestion, extraction, classification, deduplication, rejection — is observable by the analyst on demand. Not as raw logs. As structured summaries that answer: "What did the pipeline do since I last looked? What did it keep? What did it reject? Why?"

**2.4 Classifications are challengeable.** When the pipeline classifies a claim as "narrative framing" or assigns it a confidence level, the analyst can see the reasoning and disagree. Disagreements are recorded and accumulate into calibration data — over time, the analyst's corrections improve the pipeline's classification accuracy. The analyst is a teacher, not just a consumer.

**2.5 The ledger answers questions, not just returns claims.** V1 returns claims matching a topic or time window. V2 constructs answers from evidence. "What evidence suggests Iran is preparing to block the strait?" produces a synthesized answer with citations to specific claims, weighted by source credibility and recency. The answer is an artifact the analyst can inspect, challenge, and refine.

**2.6 Source credibility is analyst-informed.** V1 treats all sources equally. V2 maintains a source credibility model that the analyst shapes — marking sources as reliable, unreliable, or conditional ("reliable on military topics, unreliable on economic data"). The credibility weights flow through to claim weighting and answer synthesis.

---

## 3. The Human Relationship Model

### 3.1 The Analyst's Role at Each Pipeline Stage

| Stage | V1 Role | V2 Role |
|---|---|---|
| **Ingestion** | Toggle on/off | Direct attention — which sources, which topics, which question facets to prioritize |
| **Extraction** | Invisible | Observable — see what was extracted, what was missed, submit corrections |
| **Classification** | Invisible | Challengeable — see classification reasoning, disagree, correct |
| **Deduplication** | Invisible | Transparent on demand — see what was rejected as duplicate, override if needed |
| **Storage** | Query results | Interact with evidence — annotate, weight, connect to questions |
| **Synthesis** | Not available | Ask questions, receive evidence-based answers, refine through dialogue |
| **Evolution** | Static topics | Dynamic questions — the organizing question evolves with the analyst's understanding |

### 3.2 The Analyst's Workflow

The typical V2 workflow feels like this:

1. **Morning check-in.** The analyst opens the OSS artifact panel. It shows: "Since your last session, 47 new claims ingested across 3 active questions. 12 rejected as duplicates. 3 flagged as potentially significant (high confidence, multiple corroborating sources). 2 new sources appeared that haven't been credibility-rated."

2. **Directed attention.** The analyst reviews the flagged claims. One is about a logistics movement. The analyst tells the ledger: "This is the thread I care about. Focus extraction on logistics and supply chain indicators for the next cycle." The pipeline adjusts its extraction weighting.

3. **Question evolution.** The analyst's question was "Will Iran block the strait?" The logistics evidence shifts the question to "Is Iran pre-positioning for a limited interdiction rather than a full blockade?" The analyst updates the active question. The ledger reorganizes its evidence around the new framing.

4. **Evidence synthesis.** The analyst asks: "What's the evidence for limited interdiction versus full blockade?" The ledger constructs two evidence summaries, one for each hypothesis, citing specific claims with source credibility and recency weights. The analyst sees the evidence for and against, not just a topic dump.

5. **Source correction.** One of the cited claims comes from a source the analyst knows is unreliable on military topics. The analyst marks the source accordingly. The credibility weight flows through to the synthesis. The evidence summary updates.

6. **Handoff to SWARMFISH.** The analyst has formed a question suitable for structured prediction. The evolved question, with its accumulated evidence and source weights, flows directly into a SWARMFISH prediction session as structured context. The committee doesn't start from zero — it starts from the analyst's curated evidence base.

### 3.3 What the Analyst Does NOT Do

The analyst does not:
- Manage the technical pipeline (RSS polling, embedding, deduplication algorithms)
- Classify every claim manually (the pipeline still does automated classification; the analyst corrects when wrong)
- Review every rejected claim (rejection transparency is on-demand, not mandatory)
- Write the synthesis (the ledger synthesizes; the analyst refines)

The analyst provides: judgment about what matters, source credibility, question evolution, and correction of classification errors. The pipeline provides: tireless collection, systematic extraction, embedding-based deduplication, and evidence synthesis. Each does what the other can't.

---

## 4. Architecture Sketch

### 4.1 What Changes

**Active Question as first-class entity.** New data structure representing the analyst's current question, with history of how it evolved. Claims are relevant relative to the active question, not just matching a topic keyword. Multiple active questions can coexist (an analyst might track 3-4 threads simultaneously).

```
active_question:
  id: uuid
  text: "Is Iran pre-positioning for a limited interdiction?"
  evolved_from: [previous_question_ids]
  attention_weights:
    logistics: 0.8
    diplomatic: 0.2
    economic: 0.5
  created: timestamp
  last_updated: timestamp
```

**Source credibility model.** Per-source credibility scores, set by the analyst, with optional domain conditioning ("reliable on X, not on Y"). Flows through to claim weighting in synthesis.

```
source_credibility:
  source_id: int
  overall: 0.7
  domain_overrides:
    military: 0.3
    economic: 0.8
  set_by: "analyst"
  last_updated: timestamp
```

**Rejection ledger.** Claims that were rejected (duplicate, low confidence, off-topic) are stored in a separate queryable ledger rather than silently discarded. The analyst can review rejections on demand — "show me what you rejected this week and why."

**Evidence synthesis endpoint.** New API endpoint that takes a question and returns a structured evidence summary — claims organized by relevance to the question, weighted by source credibility and recency, with explicit citations. This is the "answer questions, not just return claims" capability.

**Analyst correction pipeline.** When the analyst disagrees with a classification or challenges a deduplication decision, the correction is stored and accumulates. Over time, corrections can inform the extraction prompt (making the pipeline better at classifying in domains where the analyst has provided feedback).

### 4.2 What Stays

- PostgreSQL backend with full claim provenance
- FAISS embedding layer for deduplication and semantic search
- RSS ingestion pipeline (but now with attention-weighted prioritization)
- LLM extraction (qwen3.5-27b, but now with question-context in the extraction prompt)
- The calibration loop to SWARMFISH (deepened, not severed)
- Docker container architecture (but potentially migrated to A0 plugin)

### 4.3 Artifact Panel Interface

The OSS artifact panel is the analyst's primary interface. It shows:

**Dashboard view:**
- Active questions with last-updated timestamps
- Claim velocity by question (how fast evidence is accumulating)
- New claims since last session, flagged by significance
- Pending credibility ratings (new sources that need analyst assessment)
- Rejection summary (count, reasons, expandable on demand)

**Question view:**
- The active question and its evolution history
- Evidence summary: claims organized for/against, with credibility weights
- Source breakdown: which sources contributed, their credibility ratings
- Attention controls: sliders or toggles for evidence type weighting
- "Ask the ledger" input: natural language question → evidence synthesis

**Claim detail view:**
- Full claim text with source, date, extraction confidence
- Classification with reasoning (expandable)
- Challenge button: disagree with classification, provide correction
- Annotation: analyst's note on this claim's significance

**Source view:**
- All known sources with credibility ratings
- Domain-specific credibility overrides
- Claim count per source, recent reliability trend
- Flag controls: mark as reliable / unreliable / conditional

---

## 5. The Question Evolution Model

The most architecturally novel element of V2. Intelligence analysis is not static — the question evolves as evidence accumulates. V1's static topics can't represent this. V2 makes question evolution a first-class concept.

**How it works:**

1. The analyst creates an active question: "Will Iran block the Strait of Hormuz?"
2. Claims are collected and organized relative to this question.
3. As evidence accumulates, the analyst's understanding shifts. The question evolves: "Is Iran pre-positioning for limited interdiction rather than full blockade?"
4. The evolution is recorded — the new question links to the old one. The evidence that prompted the shift is tagged.
5. The ledger reorganizes: claims that were peripheral to the old question may be central to the new one. Relevance weights update.
6. The evolution history itself becomes a record: "The analyst's question shifted from X to Y after evidence Z arrived." This is metacognitive documentation — the analyst can see how their own understanding evolved, grounded in evidence.

**Why this matters:**

The question evolution history is the analyst's analytical trajectory. It shows how the analyst's thinking developed. It's the intelligence community's "line of analysis" concept made concrete — not just the conclusion, but the path to the conclusion, with the evidence that drove each turn.

When the evolved question flows to SWARMFISH, the committee has context not just about what the analyst wants to know but about how the analyst arrived at that question. The evolution history is structured context that improves the quality of the prediction session.

---

## 6. Connection to SWARMFISH V2

The calibration loop between OSS and SWARMFISH is real and should deepen in V2:

**OSS → SWARMFISH:**
- An evolved question with curated evidence flows to SWARMFISH as structured context for a prediction session
- Source credibility weights carry through — the committee inherits the analyst's source assessments
- The evidence summary becomes the briefing material the committee deliberates on, not raw claims

**SWARMFISH → OSS:**
- Falsification conditions generated by SWARMFISH become monitoring targets in OSS: "Watch for evidence of X — if it appears, the prediction changes"
- When a SWARMFISH prediction is updated (new session with new evidence), OSS tracks what new claims drove the update — the evolution is documented in both systems

**Shared evolution:**
- The analyst's question in OSS and the prediction question in SWARMFISH are the same question at different stages. OSS collects and organizes the evidence. SWARMFISH assesses the probability. The two systems are a single analytical pipeline from the analyst's perspective, surfaced as coordinated artifact panels.

---

## 7. World Models Connection

From the world models research thread (Session 061): prediction error is the universal anomaly signal. A world model trained on OSS claim dynamics could learn how information landscapes evolve and predict what the claim distribution should look like tomorrow. Divergence from prediction is the anomaly signal — a narrative shift, a new source entering the space, a coordinated information operation.

This is the "OSS Claim Dynamics Forecasting" application (S2 from the research thread). It becomes more powerful in V2 because the question-oriented architecture provides a natural frame for the prediction: "given the current evidence on this question, what should the evidence landscape look like in a week?" The analyst doesn't need to understand the world model — they see the anomaly surfaced in the artifact panel: "Unexpected shift in claim patterns on your active question — 3 new sources appeared simultaneously with coordinated framing."

Timeframe: 🔴 Future — requires V2 operational with sufficient historical data. But the architecture should be designed to accommodate this enhancement without structural changes.

---

## 8. Open Questions

**Q1: Plugin or external service?** V1 runs as an external Docker container. V2 could run as an Agent Zero plugin, bringing it inside the sovereignty boundary. The plugin architecture supports this (the Exocortex successfully migrated). But OSS has a PostgreSQL backend and a long-running ingestion pipeline — is that appropriate as a plugin, or should it remain an external service accessed via tools?

**Q2: LLM extraction with question context.** V2's extraction should be aware of the analyst's active question — extracting claims that are relevant to what the analyst currently wants to know. This means the extraction prompt includes the active question as context. How does this interact with autonomous ingestion? When the analyst isn't present, does the pipeline revert to topic-based extraction? Or does it continue extracting relative to the last active question?

**Q3: Correction accumulation.** When the analyst corrects classifications, how should those corrections flow back to improve the pipeline? Options: (a) adjust the extraction prompt with examples of correct classifications, (b) fine-tune the extraction LLM on corrections (LoRA, ATLAS-style), (c) build a deterministic post-processing layer that overrides the LLM based on learned patterns. Option (c) is most aligned with the Exocortex's deterministic-first philosophy.

**Q4: Multi-analyst.** V2 is designed for a single analyst. If the Exocortex ever serves multiple analysts (or if Eitan has different questions than Jake), how does the attention model handle competing priorities? This is a future concern, but the data model should not preclude it.

**Q5: Evidence synthesis quality.** The "ask the ledger" feature requires synthesizing an answer from evidence. This is an LLM call. How does it interact with the EI layer? The synthesis should be epistemically honest — citing evidence, noting gaps, expressing uncertainty. The EI layer should audit the synthesis the same way it audits agent output.

---

*V2 is not a feature upgrade. It's a relationship redesign. The analyst moves from outside the pipeline to inside it — directing attention, challenging classifications, evolving questions, and receiving evidence-based answers. The pipeline adapts to the analyst. The analyst teaches the pipeline. The collaboration is real, not metaphorical. V2 is complete when Jake says "I feel like I'm working with this, not just reading from it."*
