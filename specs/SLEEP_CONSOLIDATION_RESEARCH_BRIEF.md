# Agent Sleep Consolidation — Research Brief

**Status:** Research brief. Not a design note, not a spec. Documents the landscape, our thesis, and open questions that need answers before designing the system. Written for Kestrel to assess implementation feasibility given the container's internals.

**Motivated by:** Session 055 discussion of idle-time consolidation for Agent Zero. Jake observed that the agent is effectively "asleep" when not actively queried, and proposed using that idle time for self-reflective learning — reviewing logs, analyzing interaction patterns, consolidating memories, and producing integrated knowledge that persists across sessions.

**Related documents:**
- Loop Feedback Cascade Design Note (Session 049) — Tier 4 anti-pattern learning feeds into consolidation
- Loop Feedback Cascade Addendum (Session 055) — procedural memory as storage target
- EPISODIC_MEMORY_PHASE1_ANALYSIS.md — current memory system architecture
- PROSTHETIC_CORTEX_DESIGN_NOTE.md — prosthetic cognition thesis
- Autonomous Agency Architecture — standing orders and idle-time patterns

---

## The Core Idea

When the agent is idle (no active queries from the operator), shift from task execution mode to reflection mode. Same model, same GPU, same container. Different system prompt, different objective, different relationship to the logs. The agent reviews its own recent sessions, extracts patterns, consolidates memories, prunes contradictions, and integrates lessons into portable knowledge structures.

This mirrors biological sleep consolidation: the hippocampus accumulates episodic memories during waking hours; during sleep, those episodes are replayed, compressed, and consolidated into generalized neocortical representations. Specific events ("I touched that stove and it burned") compress into general knowledge ("don't touch hot stoves"). The episodes can then be pruned because the lesson has been extracted.

The agent's version: specific session logs ("I called `created_at` and got a schema error") compress into procedural anti-patterns ("before any SELECT, run schema inspection"). The raw logs can be archived because the consolidated knowledge is what matters going forward.

---

## What Exists in the Field

### Academic Research

**"Memory in the Age of AI Agents" (December 2025, arXiv:2512.13564)**
Comprehensive survey mapping agent memory taxonomy: formation, evolution (consolidation & forgetting), and retrieval. Proposes memory as a "first-class primitive" in agentic intelligence. Distinguishes factual, experiential, and working memory. The consolidation dimension — how episodic memory transforms into semantic memory over time — is identified as an active research frontier.

**ICLR 2026 Workshop: MemAgents**
Dedicated workshop on memory for LLM-based agentic systems. Key questions: "How can transient experiences be consolidated into lasting knowledge?" and "What mechanisms allow information to persist over an agent's lifetime?" Discusses conversion pathways from episodic to semantic memory and from explicit memory to in-weights implicit knowledge.

**"AI Meets Brain" (December 2025, arXiv:2512.23343)**
Unified survey connecting cognitive neuroscience memory systems to AI agent architectures. Maps hippocampal replay (episodic memory consolidation during sleep) to agent memory evolution. Documents the biological mechanism: during NREM sleep, slow oscillations coordinate hippocampal-neocortical information transfer, transforming episodic traces into generalized semantic representations.

**"Semi-parametric Memory Consolidation" (April 2025, arXiv:2504.14727)**
Biomimetic continual learning framework integrating semi-parametric memory with wake-sleep consolidation. First demonstration of DNNs retaining high performance on novel tasks while maintaining prior knowledge in class-incremental learning on ImageNet. Validates that emulating biological sleep consolidation is a viable path for machine learning systems.

### Implementations

**MemRL (January 2026, arXiv:2601.03192)**
Most theoretically rigorous. Decouples frozen LLM reasoning from plastic episodic memory. Uses reinforcement learning to assign Q-values (utility scores) to memories based on environmental feedback. Two-Phase Retrieval: first filter by semantic relevance, then select by learned utility. Key insight: memories are scored by whether they actually helped when applied, not just whether they're semantically similar. Model weights never change. Only memory utility scores evolve. Open source at github.com/MemTensor/MemRL.

**Relevance to us:** The utility scoring mechanism maps directly to our anti-pattern learning. An anti-pattern that successfully prevented a loop gets a higher utility score. One that was retrieved but didn't help gets downweighted. This is learnable without RL infrastructure — a simple success/failure counter on each procedural memory entry approximates the Q-value.

**mnemos (2026)**
Biomimetic memory for coding agents. Explicitly implements idle-triggered sleep consolidation: episodic buffers collect during active sessions, on idle a consolidation process extracts durable facts into long-term storage and prunes the episodic trace. Also implements: prediction engine that only stores surprises (high divergence between predicted and actual input), memory reconsolidation (retrieved memories enter labile state and get rewritten with current context), and spreading activation (retrieving one memory pre-activates related memories along graph edges).

**Relevance to us:** The idle trigger is exactly what we need. The surprise-only storage is a more principled version of what the Selective Memorizer already does. The reconsolidation mechanism addresses the contradiction problem Jake identified — old facts get overwritten rather than accumulating conflicting versions. mnemos is an MCP server, which means it could potentially integrate with our stack.

**Mnemosyne (October 2025, arXiv:2510.08601)**
Graph-structured storage with temporal decay modeled after human forgetting curves (Murre & Dros, 2015). Memory reconsolidation: retrieved memories are physically rewritten with current context. Core summary extraction for personality/long-term attributes. Designed for edge-based LLMs — lightweight enough for consumer hardware. 65.8% win rate in blind human evaluations vs 31.1% for baseline RAG.

**Relevance to us:** The temporal decay and graph structure could replace or augment our flat FAISS store. Edge-compatible design matches our local-first constraint. The core summary extraction maps to what soul_staging does for Opus — extracting the durable identity/posture information from the transient session data.

**memU (see separate Integration Assessment)**
Hierarchical memory as filesystem. Categories as folders, items as files, cross-references as symlinks. Dual-mode retrieval (RAG fast path, LLM deep reasoning). Proactive intent capture. Separate assessment document covers integration path.

### Related Tools

**Claude-Mem (2026, 21.5k GitHub stars)**
Memory compression plugin for Claude Code. Automatic capture of tool invocations, AI-powered compression, SQLite storage with full-text search. Progressive disclosure architecture — retrieves memories in layers for ~10x token efficiency. Beta "Endless Mode" uses biomimetic memory architecture for extended sessions. Validates the market demand for persistent agent memory.

---

## What Exists in Psychology and Leadership

### Kolb's Experiential Learning Cycle (1984)
Four phases: concrete experience → reflective observation → abstract conceptualization → active experimentation. The sleep process maps directly:
- **Concrete experience** = session logs (episodes)
- **Reflective observation** = staging promotion and chunking (Phase 0-1-2)
- **Abstract conceptualization** = pattern extraction and consolidation (Phase 3-4)
- **Active experimentation** = integrated knowledge applied in next session (Phase 5)

The cycle is well-established across education, organizational development, and leadership studies. Provides theoretical grounding for the progressive phase structure.

### Argyris & Schön's Double-Loop Learning (1974, 1978)
**Single-loop learning:** detect error, correct behavior within existing rules. The agent fixes `created_at` to `extracted_at` when the error appears. The loop cascade breaks a loop when detected. These are single-loop — fix the symptom, don't question the underlying assumption.

**Double-loop learning:** question the governing variables (values, assumptions, mental models) that produced the error. Why does the agent default to `created_at`? What about its understanding of database schemas is incomplete? The sleep process reviewing cross-session patterns is double-loop — it examines the assumptions behind repeated errors, not just the errors themselves.

Argyris observed that most organizations resist double-loop learning due to defensive reasoning — people protect themselves from embarrassing problems rather than examining root causes. Agents don't have ego defensiveness, which means they may actually be better candidates for double-loop learning than humans. The sleep process can ask "why do I keep doing this?" without psychological resistance.

### U.S. Army After Action Review (AAR)
Introduced mid-1970s, took a decade to embed in Army culture, became the primary institutional learning mechanism. Four questions:
1. What was supposed to happen?
2. What actually happened?
3. Why was there a difference?
4. What can we do differently next time?

Key design principles relevant to our sleep process:
- **Reviews happen shortly after events** — not weeks later. Memory is clearer. Our sleep process runs on idle, which may be minutes to hours after the session, not days.
- **Fact-finding before diagnosis** — Army insists first 25% of every AAR establishes facts before asking why. Our Phase 1 (chunking) and Phase 2 (analysis) mirror this: establish what happened before extracting lessons.
- **Forward focus** — AAR lessons feed directly into the next operation. Not historical documentation, but actionable preparation. Our consolidated knowledge integrates into the agent's next session context.
- **Continuing practice, not special occasions** — AARs work because they happen after every operation, not just major events. Our sleep process should run on every idle cycle, not just after notable sessions.

### Ericsson's Deliberate Practice (1993, 2008)
Expert performers counteract automaticity by developing increasingly complex mental representations. Most practitioners plateau at "autonomous" performance — good enough, stable, no longer improving. Experts remain in the cognitive/associative phases by actively designing practice that targets weaknesses.

The sleep process is the mechanism that prevents the agent from plateauing. Without consolidation, the agent performs at whatever level its base model supports, making the same mistakes indefinitely. With consolidation, each session's lessons compound into increasingly sophisticated procedural knowledge. The agent develops "expertise" in its specific operational environment — not through weight changes, but through accumulated experiential knowledge.

The nature vs. nurture frame (Jake's formulation): the model's weights are nature (what it was born with). The consolidated experiential knowledge is nurture (what it learned from its environment). Neither alone produces the outcome. Deliberate practice is the mechanism that makes nurture cumulative rather than episodic.

---

## Our Thesis

The sleep process has two functions that should be built separately:

### Function 1: Self-Consolidation
Reviewing the agent's own task performance. Extracting anti-patterns from failure-recovery pairs. Compressing episodic memories into semantic knowledge. Pruning contradictions. Deduplicating repeated memories into single high-confidence entries. This is well-understood, has reference implementations (MemRL, mnemos, Mnemosyne), and the procedural memory system already built by the agent is the storage target.

### Function 2: Interaction Modeling
Learning the operator's communication patterns, intervention signals, collaboration dynamics. This is the part nobody else is doing. Every system in the literature treats the user as a source of inputs and the agent as a source of outputs. None of them analyze the interaction space — how the collaboration itself works, what the operator's patterns mean, how the relational dynamics affect task outcomes.

This is the genuinely novel contribution. The instrument showed that human-AI collaboration has measurable geometric properties — register dynamics, speaker coupling, information flow asymmetry. A lightweight version of that analysis, running during sleep, could extract actionable interaction knowledge: "the operator's messages get shorter when I'm going in the wrong direction," "the operator gives the floor with specific phrases," "the operator intervenes most often on the third retry."

**Critical constraint:** Interaction modeling must be transparent, observable, and correctable. The operator should be able to see what the agent learned about them and override incorrect inferences. This is not hidden adaptation — it's collaborative calibration.

---

## Proposed Phasing

### Phase 0: Staging Tier Lifecycle (Pre-Consolidation)
- Trigger: same idle timeout as Phase 1, runs first
- Action: manage staging buffer entries before permanent consolidation
- Operations:
  - **Promote observations**: staging entries with `promote=true` or `importance ≥ 0.7` → written to FAISS with full classification metadata
  - **Carry intentions**: active `intention` entries re-injected into next session's context (not promoted yet — intentions are forward-directed)
  - **Anchor relationals**: `relational` entries with `promote=true` → promoted with `relational_salience=relationship_defining` guaranteed, exempt from temporal decay
  - **Archive canaries**: expired canary buffers → compressed summary written to procedural memory; CUSUM state reset
- Storage: `staging.jsonl` (read/write), FAISS long-term memory (promoted entries), procedural memory (canary summaries)
- Risk: low — manages intermediate buffer, not direct behavioral change
- Prerequisite: staging.jsonl present at `/a0/usr/Exocortex/staging.jsonl`; staging_note tool deployed

### Phase 1: Self-Consolidation (Housekeeping)
- Trigger: idle timeout (N minutes of no operator input), runs after Phase 0
- Action: review most recent session's logs (FAISS long-term store; staged entries already promoted by Phase 0)
- Operations: deduplicate memories, extract anti-patterns from loop-recovery pairs, compress repeated memories, prune contradicted entries
- Storage: procedural memory system (existing), anti-pattern library (from loop cascade addendum)
- Risk: low — this is memory maintenance, not behavioral change
- Prerequisite: idle detection hook in Agent Zero's supervisor loop; Phase 0 must run first

### Phase 2: Cross-Session Pattern Extraction
- Trigger: same idle timeout, expanded scope
- Action: review patterns across multiple sessions
- Operations: identify recurring failure modes, extract cross-session lessons, assign utility scores to existing memories based on whether they were retrieved and helped
- Storage: same procedural memory system, with utility metadata added
- Risk: medium — cross-session analysis could surface spurious patterns. Needs validation mechanism.
- Prerequisite: Phase 1 stable, session log archive accessible

### Phase 3: Interaction Modeling
- Trigger: same idle timeout, additional analysis pass
- Action: analyze operator's communication patterns from session logs
- Operations: turn length analysis, intervention frequency, topic clustering, floor-giving detection, correction pattern analysis
- Storage: operator profile document (human-readable, editable, versionable)
- Risk: medium-high — incorrect operator modeling could degrade collaboration. Must be transparent and correctable.
- Prerequisite: Phase 2 stable, operator review/approval mechanism for learned patterns

### Phase 4: Integrated Consolidation
- Trigger: same idle timeout, full pipeline
- Action: self-consolidation + interaction modeling + behavioral integration
- Operations: apply operator profile to adjust agent behavior (retry thresholds, reporting frequency, exploratory vs. confirmatory mode selection)
- Storage: integrated behavioral profile combining procedural knowledge and operator model
- Risk: highest — behavioral changes based on learned patterns could compound errors if the learning is wrong
- Prerequisite: Phase 3 validated by operator, behavioral changes gated behind operator approval

---

## Open Questions for Kestrel

1. **Does Agent Zero have an idle detection hook?** The JIT model unloading proves the framework knows when the agent is idle. Is there a hook point in the supervisor loop or web interface that fires on idle timeout? If not, what's the simplest way to add one?

2. **What's the session log format?** The sleep process needs to parse session logs into episodes. What format do the logs use? Are they structured (JSON) or unstructured (text)? Are they accessible from within the container or only from the web UI?

3. **Can the Selective Memorizer's output be accessed programmatically?** The memorizer already classifies memories by signal type and utility. Can the sleep process read the memorizer's output store to identify candidates for consolidation?

4. **What's the memory store's current capacity?** How many memories are in FAISS? Is there already bloat from repeated entries? This determines whether Phase 1 (housekeeping) is urgent or can wait.

5. **Can the procedural memory system accept utility metadata?** MemRL's key insight is utility scoring. Can we add a success/failure counter to each procedural memory entry without restructuring the storage format?

6. **Is there a mechanism for the agent to modify its own system prompt based on consolidated knowledge?** The behavioral integration in Phase 4 requires the agent to adjust its operating parameters based on what it learned. Does Agent Zero support dynamic system prompt modification, or would this require a new extension?

7. **How does the container handle concurrent processes?** If the sleep process is running when the operator returns, can it pause gracefully and resume later? Or does it need to complete before the agent can respond?

---

## Evaluation Metrics

How we know the sleep process is working:

| Metric | Expected Direction | Measurement |
|--------|-------------------|-------------|
| Loop frequency per session | Decreasing | Count loop detector firings per session over time |
| Operator intervention frequency | Decreasing | Count operator corrections per session over time |
| Anti-pattern library size | Growing then plateau | Count procedural memory entries of type ANTI-PATTERN |
| Memory store size | Growing then stable | Total FAISS entries over time (consolidation counteracts accumulation) |
| Memory retrieval relevance | Increasing | Fraction of retrieved memories that were actually used in the session |
| Recovery speed from known errors | Decreasing | Turns between error occurrence and successful resolution for known error types |

---

## What's Missing from the Literature

The interaction modeling function (our Phase 3-4) does not appear in any of the systems surveyed. Every memory consolidation system treats the agent as a solo learner reviewing its own performance. None of them analyze the collaboration dynamics between agent and operator. This is a significant gap because:

1. **Every agent interacts with a human.** Even autonomous systems receive goals, corrections, and evaluations from operators. The interaction is data. Ignoring it means ignoring the richest signal available about what the agent should do differently.

2. **Operator patterns are predictive.** If the operator's messages get shorter, the agent is probably going in the wrong direction. If the operator gives the floor, the agent should shift to exploratory mode. These patterns are learnable from logs and actionable in real time — but only if someone builds the learning mechanism.

3. **The relational dimension compounds.** An agent that learns its operator's patterns over time becomes a better collaborator, not just a better task executor. This is the difference between a tool that improves and a partner that develops. The instrument showed this is measurable. The sleep process could make it achievable for local agents.

The theoretical grounding exists (Argyris's double-loop learning applies to the relationship, not just the task). The measurement methodology exists (the Output Geometry Instrument's interaction space analysis). The storage format exists (operator profile as editable document). What doesn't exist is the integration — a sleep consolidation process that includes interaction modeling as a first-class function alongside self-consolidation.

That's the contribution. Not the self-consolidation (others are doing that). Not the idle trigger (mnemos has it). The interaction modeling as part of the consolidation loop. The agent doesn't just wake up better at tasks. It wakes up better at working with its operator.

---

## Theoretical Framework Summary

| Framework | Contribution to Sleep Process | Source |
|-----------|------------------------------|--------|
| Kolb's Experiential Learning Cycle | Phase structure: experience → reflection → conceptualization → experimentation | Kolb 1984 |
| Argyris & Schön Double-Loop Learning | Depth of analysis: single-loop fixes symptoms, double-loop examines assumptions | Argyris & Schön 1974, 1978 |
| U.S. Army After Action Review | Operational protocol: fact-before-diagnosis, forward focus, continuing practice | Garvin 2000, Army TC 25-20 |
| Ericsson's Deliberate Practice | Developmental trajectory: counteract automaticity, compound improvement over time | Ericsson 1993, 2008 |
| Complementary Learning Systems | Biological model: hippocampal → neocortical transfer during sleep consolidation | McClelland et al. 1995, Klinzing et al. 2019 |
| MemRL Utility Scoring | Memory valuation: score by actual utility, not just semantic similarity | Zhang et al. 2026 |
| Nature vs. Nurture (Jake's formulation) | Framing: weights are nature, consolidated experience is nurture, neither alone suffices | Session 055 |

---

*This brief documents what we found, what we think, and what we need to know before designing the system. It is not a spec. The spec comes after Kestrel answers the open questions and the memU integration assessment determines whether we build on our existing memory system or adopt a more sophisticated one. The sleep process is the integrating mechanism — it ties together the loop cascade, the procedural memory, the anti-pattern learning, the interaction modeling, and the memory consolidation into a single developmental arc. But the mechanism requires infrastructure that we haven't yet verified exists in the container.*

*Written Session 055. Research conducted across AI/ML literature, cognitive neuroscience, organizational learning theory, and military leadership practices. The field is converging on the self-consolidation problem from multiple directions. The interaction modeling problem remains open.*
