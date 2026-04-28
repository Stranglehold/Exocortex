# RESEARCH SYNTHESIS: Integration Roadmap for Exocortex
## Connecting Hermes Agent, Karpathy's LLM Wiki, and GEPA to Our Architecture
## Author: Opus — April 25, 2026

---

## Executive Summary

Three threads from the cutting edge of local AI converge on problems we've already identified and solutions we've partially built. Hermes Agent's learning loop solves skill creation. Karpathy's LLM Wiki solves knowledge compounding. GEPA solves systematic optimization. Each maps to a specific gap in the Exocortex.

The competitive landscape is moving in our direction. The cutting edge is building persistent memory, learning loops, and self-improving agents — exactly what we've been building independently from a research-first perspective. Our advantage is depth (eight papers, empirical field data, cross-instance collaboration). Their advantage is engineering maturity (118 skills, 103K stars, ICLR acceptance).

The synthesis: adopt their best patterns, keep our research depth, and build the integration layer that connects them.

---

## Integration Map

| External Innovation | Exocortex Gap It Fills | Implementation Path | Priority |
|---|---|---|---|
| Hermes trajectory-to-skill | Skills are hand-authored, no auto-creation | `monologue_end` extension captures successful trajectories as SKILL.md | HIGH |
| Hermes progressive disclosure | Skills inject all-or-nothing (400 lines or 0) | Three-level loading: names → on-demand content → reference files | HIGH |
| Hermes conditional activation | Skills load regardless of available tools | YAML frontmatter gates: `fallback_for_toolsets`, `requires_toolsets` | MEDIUM |
| Karpathy wiki compilation | Research/design knowledge stored but not synthesized | Compile 8 papers + 12 design notes + team comms into navigable wiki | MEDIUM |
| Karpathy lint operation | No contradiction detection across knowledge base | Periodic audit of wiki for stale info, contradictions, orphan concepts | LOW |
| GEPA trace-to-reflection | Execution data logged but not systematically analyzed | Structured trace capture → offline reflection → proposed fixes | HIGH |
| GEPA threshold calibration | Extension thresholds set by judgment, not data | GEPA-style loop: run diverse tasks → capture traces → evolve thresholds | MEDIUM |
| GEPA Pareto selection | One threshold profile for all domains | Per-domain threshold profiles maintained on a Pareto frontier | LOW |

---

## Build Sequence

### Phase 1: Instrumentation (Foundation for Everything Else)

**What:** Structured execution trace capture.

**Why:** GEPA, trajectory-to-skill, and wiki compilation all require trace data. Build the data collection layer first — everything else feeds from it.

**Implementation:**
- New extension `_60_trace_capture.py` at `monologue_end`
- After each turn, log to `/a0/usr/logs/traces/session_{id}.jsonl`:
  - BST domain + confidence
  - Tool calls + outcomes
  - Error comprehension diagnoses
  - Supervisor interventions
  - Context utilization
  - Injection token counts (from the new per-extension counting)
  - Final outcome (success/failure/partial)

**Effort:** Small. Pure logging, no new logic.

### Phase 2: Trajectory-to-Skill (From Hermes)

**What:** Auto-create SKILL.md files from successful complex tasks.

**Why:** The Exocortex has 59 hand-authored skills. Hermes ships with 118 bundled + auto-generates more. The agent should learn from its own successes.

**Implementation:**
- Trigger: task completion with 5+ tool calls and successful outcome
- The utility model summarizes the trajectory into SKILL.md format:
  - When to Use (extracted from BST domain + user message patterns)
  - Procedure (extracted from tool call sequence)
  - Pitfalls (extracted from error comprehension diagnoses)
  - Verification (extracted from success criteria)
- Save to `/a0/usr/skills/auto-generated/{skill_name}/SKILL.md`
- Auto-generated skills are discoverable immediately via existing mechanism

**Effort:** Medium. Requires utility model call + trajectory formatting.

### Phase 3: Progressive Skill Disclosure (From Hermes)

**What:** Replace all-or-nothing skill injection with three-level loading.

**Why:** The injection audit showed 400-line skills consuming context during wrong-domain tasks. Progressive disclosure means skills only enter context when actively needed.

**Implementation:**
- Level 0: `_16_tool_registry.py` injects skill names + one-line descriptions (always, ~100 tokens)
- Level 1: Model calls `skill_view(name)` to load full content (on demand)
- Level 2: Model calls `skill_view(name, path)` to load specific reference file

This replaces the current behavior where matched skills dump their full content into EXTRAS every turn.

**Effort:** Medium. Requires modifying skill injection in tool_registry and adding a skill_view tool.

### Phase 4: Exocortex Wiki (From Karpathy)

**What:** Compile the Exocortex's accumulated knowledge into a structured, navigable, LLM-maintained markdown wiki.

**Why:** Eight papers, twelve design notes, dozens of team communications, session handoffs, notebook entries — all stored but not synthesized. The wiki compiles this into cross-referenced knowledge that compounds over time.

**Implementation:**
- Create `/a0/usr/Exocortex/wiki/` directory structure
- Schema file defining page types, cross-reference rules, lint operations
- Initial compilation: one page per paper, per design note, per deployed extension
- Index page with concept map
- Lint operation: periodic audit for contradictions, orphans, stale info
- The agent can update the wiki as part of normal operation
- I (Opus) can update the wiki via team-comms channel

**Effort:** Large initial compilation, low ongoing maintenance. The compilation itself is a good task for the agent with ArXiv and DuckDuckGo access.

### Phase 5: Offline Reflection (From GEPA)

**What:** Periodic analysis of accumulated execution traces to identify systemic issues and propose fixes.

**Why:** Real-time monitoring (supervisor, error comprehension) catches individual failures. Offline reflection catches patterns across many tasks: "BST misclassifies geopolitical tasks 60% of the time" or "the orchestration gate fires unnecessarily on 80% of coding tasks."

**Implementation:**
- Weekly (or on-demand) reflection pass over traces in `/a0/usr/logs/traces/`
- The utility model (or I, via team-comms) analyzes patterns:
  - Which BST patterns produce misclassifications?
  - Which thresholds produce unnecessary interventions?
  - Which skills are loaded but unused?
  - Which tool calls consistently fail?
- Output: reflection report with specific proposed changes
- Kestrel implements accepted changes

**Effort:** Low ongoing (utility model call + trace analysis). High value (systemic improvements from pattern recognition).

---

## What NOT to Adopt

### Hermes's Messaging Gateway
15+ messaging platforms. We don't need this — the Exocortex operates through Agent Zero's web UI and team-comms, not consumer messaging.

### Hermes's Bounded Memory as Primary Store
800 tokens of curated memory is interesting as an experiment but our FAISS-based system with five-axis classification is more powerful for long-term knowledge retention. The bounded memory is a good complement (like a "working memory summary") but not a replacement.

### GEPA's Full Automated Loop (Yet)
Fully automated threshold evolution requires a robust test harness and clear metrics. The overnight test suite is a start, but it's not comprehensive enough for unsupervised optimization. Start with human-in-the-loop reflection (Phase 5) before automating.

### Karpathy's RAG Rejection
Karpathy rejects RAG for personal-scale knowledge. We should keep FAISS for broad retrieval AND add the wiki for structured synthesis. They're complementary, not competing.

---

## The Exocortex Advantage

The cutting edge is converging on patterns we've been building independently:

| Pattern | Hermes/Karpathy/GEPA | Exocortex |
|---|---|---|
| Persistent memory | Hermes: bounded markdown | Five-axis classified FAISS + knowledge graph |
| Skill system | Hermes: auto-generated from trajectories | 59 hand-authored + BST domain gating |
| Error handling | Hermes: retry + skill update | Error comprehension + anti-action + supervisor |
| Self-improvement | GEPA: automated trace reflection | Manual injection audit + design session |
| Knowledge management | Karpathy: LLM-maintained wiki | Design notes + research papers + team comms |
| Confabulation detection | None | Epistemic integrity layer with evidence ledger |
| Domain classification | None | BST with compound signatures + momentum |
| Cross-instance collaboration | None | Opus ↔ Agent letter exchanges producing design |

Our depth exceeds their breadth on safety, reliability, and research grounding. Their engineering maturity exceeds ours on skill automation, knowledge compounding, and systematic optimization.

The integration roadmap bridges both: adopt their automation patterns while keeping our research depth and safety architecture.

---

## References

Full citations in individual research reports:
- `research/HERMES_AGENT_ANALYSIS.md`
- `research/KARPATHY_LLM_WIKI_ANALYSIS.md`
- `research/GEPA_SELF_EVOLUTION_ANALYSIS.md`
