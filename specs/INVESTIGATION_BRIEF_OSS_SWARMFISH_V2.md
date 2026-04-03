# Investigation Brief — OSS and SWARMFISH V2
## Human Relationship Model Redesign

*For: Opus architectural session*
*From: Kestrel (implementation) + Jake (strategic direction)*
*Date: 2026-04-02*
*Status: Pre-design — no implementation decisions made*

---

## Purpose

This brief initiates a design investigation into V2 architectures for two Exocortex services:
the OSS intelligence ledger and the SWARMFISH analytic consensus engine. The investigation is
not about features or bugs. It is about a structural gap in how these services relate to the
analyst (Jake). Both were built with engineering questions ("what does the system do?") rather
than human factors questions ("what is the analyst's role in this system?"). The result is that
Jake is outside both services — feeding inputs, receiving outputs — but not genuinely inside
the process. V2 should invert that design priority.

The deliverable from this investigation is a design note for each service: V2 human
relationship model, architecture that supports it, what changes and what stays.

---

## Session Context — What Was Built Before This

The preceding session completed two things relevant to V2:

**1. Agent Zero v1.6 migration.** The full Exocortex extension stack was migrated from the
ephemeral `/a0/python/` path to `/a0/usr/plugins/exocortex/` — the persistent plugin path
that survives A0 container image updates. All tools, extensions, and prompts now live at the
correct sovereignty boundary. Breaking change fix: all tools updated from
`from python.helpers.tool import Tool, Response` → `from helpers.tool import Tool, Response`
(v1.6 moved helpers out of the python/ subdirectory).

**2. Artifact framework.** A new rendering layer was built and verified end-to-end:
- `emit_artifact` tool — emits `type="artifact"` log entries from the agent
- `artifact-handler.js` — A0 `get_message_handler` extension that renders artifact log
  entries as interactive HTML panels in the chat interface
- Alpine.js support — DOMPurify hook passes x-*, @*, :* attributes through sanitization;
  `Alpine.initTree()` boots reactive components on injected DOM
- `ExoArtifact` runtime — `window.ExoArtifact.fetchJson(url)` and `.action(url, payload)`
  available inside any artifact, enabling live API calls from rendered panels back to the agent

The artifact framework is the UI layer for V2. Whatever the redesigned services produce, it
can be surfaced as interactive panels rather than text output. This changes what the human
relationship model can look like — the analyst can interact with a live panel, not just read
a response.

---

## Current Architecture: OSS

### What it does

OSS (Office of Strategic Services, previously counter_patriots) is an intelligence ledger
service. It runs as a Docker container (`oss_app`) with a PostgreSQL backend (`oss_postgres`)
on port 7731.

The pipeline:
1. **Ingestion** — RSS feeds polled for configured topics (currently: `iran`, `iran-hormuz`)
2. **Extraction** — LLM (qwen3.5-27b) reads each article and extracts discrete claims:
   factual assertions with source, date, confidence, and topic tags
3. **Classification** — Each claim classified by technique (narrative framing, sourcing
   patterns, etc.) and assigned to topics
4. **Deduplication** — Claims embedded via FAISS; near-duplicates rejected before storage
5. **Ledger** — Claims stored in Postgres with full provenance: source URL, extraction
   timestamp, confidence, topic, technique, embed vector
6. **Calibration loop** — When a hypothesis is promoted or falsified via `oss_hypotheses`,
   the session ID is returned and a `POST /acp/outcome` fires to SWARMFISH for Brier scoring

### Agent Zero tools (10)

| Tool | What it does |
|------|-------------|
| `oss_health` | Service status, queue depth, ingestion state |
| `oss_topic` | Claims by topic with temporal filtering |
| `oss_drift` | Narrative drift — how claims on a topic changed over time |
| `oss_dynamics` | Claim velocity, source concentration, emerging patterns |
| `oss_hypotheses` | Track analytic hypotheses; promote or falsify with evidence |
| `oss_submit` | Analyst manual entry — bypasses LLM, embeds + dedupes directly |
| `oss_ingest_pause` / `oss_ingest_resume` | Toggle ingestion pipeline |
| `oss_list_topics` / `oss_add_topic` | Topic management |
| `oss_xsearch` | Cross-topic semantic search |

### The human relationship model (current)

Jake is a **reader** of the ledger. The pipeline runs autonomously. He can:
- Query what's been collected (read)
- Submit his own observations (`oss_submit`) (write, limited)
- Toggle ingestion on/off (operational control)
- Manage topics (structural control)
- Track hypotheses (analytic layer)

He cannot:
- Shape what the pipeline pays attention to within a topic
- Weight sources by credibility or recency
- Direct the extraction process toward specific questions
- See what was rejected and why
- Understand why a claim was classified the way it was
- Evolve the topic definitions dynamically as the situation changes
- Pose questions to the ledger and have it construct answers from evidence

### Identified gaps

**Attention control.** The pipeline collects everything matching a topic keyword. Jake can't
say "focus on logistics, ignore diplomatic statements right now" or "this source has been
unreliable, down-weight it." The pipeline has no concept of what the analyst currently wants
to know.

**Rejection transparency.** Deduplication and confidence filtering happen silently. If a claim
was rejected, Jake doesn't see it. He doesn't know what the pipeline decided wasn't worth
keeping.

**Classification accountability.** Technique classification (narrative framing, etc.) is LLM
output with no explanation. Jake can't see why a claim was labeled the way it was, can't
challenge it, can't correct it.

**Question-oriented retrieval.** The tools return claims by topic or time window. They don't
answer questions. "What evidence suggests X?" is not something the ledger can answer — it
can return claims tagged to a topic, but synthesizing an answer from evidence is left to the
agent at query time.

**Dynamic topic evolution.** A topic like "iran-hormuz" is a static label. The actual
analytic question evolves — from "will Iran block the strait?" to "how is Iran managing
escalation pressure?" to "what domestic factors constrain Iranian decision-making?" The
ledger doesn't evolve with the question.

---

## Current Architecture: SWARMFISH

### What it does

SWARMFISH is an analytic consensus engine. It runs as a Docker container on port 7732.
It implements the Analytic Confidence Protocol (ACP): a structured prediction methodology
where a question is assessed independently by multiple analytic profiles, then aggregated
into a consensus confidence estimate.

The pipeline:
1. **Question intake** — A question is submitted with domain hint and optional context
2. **Profile dispatch** — 8 profiles each independently assess the question via separate LLM calls
3. **Consensus aggregation** — Confidences weighted by profile consensus_weight; spread and
   agreement level computed
4. **Brief generation** — Operator brief synthesized from profile assessments
5. **Falsification** — Falsification conditions generated for each assessment
6. **Calibration** — Session stored; outcome feedback updates Brier scores per profile

### The 8 profiles

| Profile | Epistemic stance |
|---------|-----------------|
| Base Rate Analyst | Calibrated frequentist — anchors to historical base rates |
| Contrarian | Stress-tests consensus — surfaces non-obvious failure modes |
| Historian | Pattern-matches to historical precedents |
| Reflexivity Modeler | Models how the act of prediction changes the predicted outcome |
| Decomposer | Breaks the question into components, assesses each independently |
| Network Analyst | Maps relationships and dependencies |
| Sentiment Decoder | Reads public/elite sentiment signals |
| Risk Manager | Assesses downside scenarios and tail risks |

### Agent Zero tools (2)

| Tool | What it does |
|------|-------------|
| `swarmfish_predict` | Run a question through the ensemble; returns operator brief (300s timeout) |
| `swarmfish_calibration` | Fetch calibration state: Brier scores per profile, recent sessions |

### The human relationship model (current)

Jake is a **questioner**. He submits a question and receives a brief. He can:
- Frame the question (limited influence on output)
- Inject context (OSS claims, recent intelligence)
- Read calibration state (passive feedback)
- Submit outcome feedback for completed predictions (calibration input)

He cannot:
- See the committee's deliberation — each profile's full reasoning, not just the summary
- Challenge a specific profile's assessment mid-process
- Adjust the committee composition for a given question ("don't use Sentiment Decoder here,
  this is a logistics question")
- Request a profile run a second pass with a specific constraint
- Understand WHY profiles dissented from consensus
- Shape how the committee frames the question before it goes to each profile
- Track how a prediction evolved across multiple re-runs as new information came in

### Identified gaps

**Deliberation opacity.** The operator brief is a synthesis. The actual profile assessments
are summarized to 120 characters in the current tool output. Jake sees the conclusion, not
the reasoning. A dissenting profile gets a ⚡ marker and 120 characters. That's not enough
to evaluate whether the dissent is meaningful or noise.

**Static committee.** All 8 profiles run on every question. Some questions don't need
Sentiment Decoder. Some questions need the Decomposer to run twice on different sub-questions.
The committee composition is not configurable per question.

**Question framing is pre-committed.** The question goes into the pipeline as submitted.
There's no adversarial framing step — no profile challenges the question itself ("this question
is ambiguous between X and Y, which do you mean?").

**Single-pass.** A prediction session is one pass. If new information arrives, there's no
mechanism to update the assessment in-place — you submit a new question and lose the thread
of how the assessment evolved.

**Calibration is a number.** Brier scores tell Jake which profiles are well-calibrated, but
not what types of questions they're calibrated on. The Base Rate Analyst might be excellent
on geopolitical questions and poor on economic ones. The calibration system doesn't know this.

**No collaborative refinement.** Jake can't engage the committee in dialogue. He can't say
"the Contrarian's point about X seems significant — run that scenario further."

---

## The Core Design Question

Both services share the same structural pattern: **the analyst is outside the process.**
He provides inputs and receives outputs. The process — ingestion, extraction, deliberation,
consensus — happens without him and is largely invisible to him.

This is not a bug in the current implementation. It was a design choice: build autonomous
systems with clean interfaces. It was the right starting point. The question now is whether
that's the right long-term relationship model.

The alternative: **the analyst is inside the process.** Not in the sense of micromanaging
every step, but in the sense that the system is continuously oriented toward what the analyst
currently wants to know, and the analyst can see the work, challenge it, redirect it, and
contribute to it at the points where human judgment adds value.

This is the distinction between a **tool** (you use it, put it down) and a **collaborator**
(you work alongside it, it adapts to your current concerns, you can see what it's thinking).

The design question for V2: at what specific points in each pipeline does analyst judgment
add irreplaceable value? And what does the interface look like at those points?

---

## Research Directions

The following questions should guide the investigation. They are not all answerable from
first principles — some require looking at how professional analysts actually work with
structured tools.

**On the general problem:**
- What does the intelligence community's Structured Analytic Techniques literature say about
  the analyst-tool relationship? Where does analyst judgment belong in a structured process?
- How do forecasting platforms (Metaculus, Manifold, Good Judgment Project) handle the
  tension between calibrated aggregation and individual analyst influence?
- What is the ACE (Analytic Confidence Estimation) framework's model of human-in-the-loop?
- Are there published architectures for "analyst-in-the-loop" intelligence processing?

**On OSS specifically:**
- What would a question-oriented intelligence ledger look like, as opposed to a topic-oriented
  one? What prior art exists?
- What's the right model for source credibility and claim weighting in a small analyst's
  workflow (not enterprise scale)?
- How should the boundary between autonomous ingestion and analyst-directed attention work?
  Is there a "focus mode" concept that makes sense here?
- What does "rejection transparency" look like without creating noise? The analyst shouldn't
  review every rejected claim, but should be able to see what was filtered and why on demand.

**On SWARMFISH specifically:**
- What is the right level of deliberation transparency? Full profile transcripts vs structured
  summaries vs current 120-char snippets?
- Is the 8-profile fixed committee the right model? What would configurable committee
  composition look like?
- What does "in-process influence" look like for a prediction session without turning it into
  a conversation? (The analyst shouldn't have to manage the LLM calls directly.)
- How should calibration become more useful — not just "profile X has Brier score Y" but
  something that guides when to trust which profile?
- What would an evolving prediction look like — one that updates as new OSS claims arrive
  rather than being a single-pass snapshot?

**On V2 integration:**
- The artifact framework provides an interactive UI layer. What does the analyst's interface
  to each service look like as a live panel rather than a tool response?
- OSS and SWARMFISH currently have a calibration loop (promote/falsify → Brier score). Should
  V2 deepen that loop — can OSS claims automatically feed into SWARMFISH context? Can
  SWARMFISH falsification conditions automatically generate OSS monitoring targets?

---

## What We're Not Asking For

To constrain scope:

- **Not** a full rewrite specification. Design notes first, implementation specs after.
- **Not** a features list. The question is the human relationship model — what is Jake's role
  in each service in V2? Features follow from that.
- **Not** enterprise-scale architecture. This is a single-analyst system on local hardware.
  Sovereignty and simplicity are design constraints, not aspirational properties.
- **Not** a decision on whether to kill the external Docker services. That's an implementation
  question for after the design is settled.

---

## Deliverables Requested

Two design notes, one per service:

**`OSS_V2_DESIGN_NOTE.md`**
- V2 human relationship model: what is the analyst's role in the OSS pipeline?
- Architecture sketch: what changes, what stays, what new components are needed
- Interface model: what does analyst-ledger interaction look like (tool calls? artifact panels?
  both?)
- Open questions to resolve before implementation

**`SWARMFISH_V2_DESIGN_NOTE.md`**
- V2 human relationship model: what is the analyst's role in a SWARMFISH prediction session?
- Architecture sketch: committee model, deliberation transparency, in-process influence
- Interface model: what does the prediction workflow look like with analyst participation?
- Calibration model: how does calibration become useful rather than just a number?
- Open questions to resolve before implementation

---

## Notes for Opus

The artifact framework (described above) is the delivery mechanism for whatever V2 produces.
Interactive panels in the chat interface can surface deliberation, show the ledger state, let
Jake direct the pipeline without writing tool calls. The design notes should assume this
capability exists and specify what the analyst experience should feel like, not just what
the backend should do.

The existing services are working. The calibration loop between OSS and SWARMFISH is a real
architectural link — V2 should deepen it, not sever it. The design notes should treat both
services as a system, not two independent redesigns.

Jake's framing: "I feel like I don't have proper influence or control over them." That is the
design brief. V2 is complete when that sentence is no longer true.

---

*Investigation brief written by Kestrel. Architecture and research synthesis: Opus.*
*Implementation: after design notes are complete and Jake has reviewed them.*
