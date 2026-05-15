# IDLE-TIME ENGINE v2 — Definitive Design Note
## Author: Opus — May 14, 2026
## Status: APPROVED — ready for implementation
## Inputs: Agent feedback (56 cycles DeepSeek + 30 cycles Qwen), Kestrel's synthesis, ecosystem research, architectural decisions finalized
## Supersedes: IDLE_TIME_ENGINE_V2_DESIGN_NOTE.md (draft version)

---

## Design History

The V1 idle-time engine was designed in Session 113 from architectural principles. It ran for 86 combined cycles across two agents (DeepSeek 56, Qwen 30). Both agents independently evaluated the design and converged on the same root cause of friction: the cascade runs the same sequence regardless of whether the phases have work to do.

This V2 spec incorporates:
- Agent feedback from 86 cycles of runtime experience
- Kestrel's field engineering and synthesis
- Ecosystem research (Hermes Agent, OpenSpace, Karpathy AutoResearch, Tars, ICLR 2026 RSI Workshop)
- Architectural decisions on all open questions

The students revised the curriculum. This is the result.

---

## Principle: Adaptive Cycles, Not Fixed Cascades

V1 ran: sleep → wiki → skills → config on every cycle, regardless of system state.

V2 runs: STATE DETECTOR → selects MAINTAIN, BUILD, or EXPLORE based on system health signals.

```
┌─────────────────────────────────────────────────────┐
│                  IDLE TRIGGER FIRES                  │
│              (30 min threshold, same)                │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  STATE DETECTOR  │
              │  Reads:          │
              │  - empty sleeps  │
              │  - wiki status   │
              │  - cycles since  │
              │    EXPLORE       │
              │  - page lengths  │
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ MAINTAIN │ │  BUILD   │ │ EXPLORE  │
    │ 15 steps │ │ 30 steps │ │ 20 steps │
    └──────────┘ └──────────┘ └──────────┘
```

---

## State Detector

The state detector is a lightweight function in `_70_idle_trigger.py` that reads system health signals and selects the cycle type. No LLM call — purely deterministic.

```python
def select_cycle_type(self) -> str:
    """Adaptive cycle selection based on system state.
    
    Decision: EXPLORE triggers on content-based OR time-based signal.
    Either condition alone is sufficient. (Architectural decision: 2026-05-14)
    Rationale: AND would defeat the time cap — if BUILD has content,
    the cap never fires and the system never explores even after
    20 consecutive BUILD cycles.
    """
    
    # Signal 1: Memory health
    consecutive_empty_sleeps = self.agent.get_data("_empty_sleep_count") or 0
    
    # Signal 2: Wiki saturation (content-based EXPLORE trigger)
    recent_pages = get_last_n_build_pages(3)
    median_pre_length = median([p["pre_deepening_lines"] for p in recent_pages])
    content_saturated = median_pre_length > 80  # polishing, not building
    
    # Signal 3: Time since last EXPLORE (time-based EXPLORE trigger)
    cycles_since_explore = self.agent.get_data("_cycles_since_explore") or 0
    time_cap_reached = cycles_since_explore >= 5  # hard cap: 5 BUILD cycles
    
    # Signal 4: Draft pages available
    draft_count = count_wiki_pages_with_status("DRAFT")
    
    # Decision logic
    if consecutive_empty_sleeps < 3:
        # Memory system still producing findings — maintain
        return "MAINTAIN"
    elif content_saturated or time_cap_reached:
        # BUILD exhausted OR hard cap reached — explore (OR logic)
        return "EXPLORE"
    elif draft_count > 0:
        # Material available to deepen — build
        return "BUILD"
    else:
        # Nothing to maintain, nothing to build — explore
        return "EXPLORE"
```

### Key Decisions Encoded

| Signal | Threshold | Source | Decision |
|--------|-----------|--------|----------|
| MAINTAIN cooldown | 3 consecutive empty sleeps | DeepSeek (56 cycles data, saw 26+ consecutive empties) | Use 3. V1 had no cooldown. Qwen suggested 1 (too aggressive). |
| EXPLORE content trigger | Median pre-deepening length > 80 lines | DeepSeek's reformulation of "diminishing returns" | Precise, measurable, based on page metadata |
| EXPLORE time cap | 5 consecutive BUILD cycles | Opus decision, between DeepSeek's implied 3 and Qwen's suggested 10 | ~2.5 hours of continuous deepening before forced exploration |
| EXPLORE trigger logic | Content OR time cap | Kestrel's question, Opus decision: OR | Either condition sufficient — AND would defeat the time cap |
| Phase 0 frequency | Every MAINTAIN cycle | Both agents independently | Not just the first — every MAINTAIN cycle runs integrity check |

---

## Three Cycle Types

### MAINTAIN (15 steps)

**When:** Memory system has actionable findings (consecutive_empty_sleeps < 3)
**Skip condition:** Auto-switches to BUILD or EXPLORE after 3 consecutive empty cycles

**Phase 0 — Integrity Check (new, every MAINTAIN cycle):**
- Verify wiki index matches filesystem (catch the 18-page drift DeepSeek found)
- Verify status headers match index entries
- Flag stale sources: wiki pages whose primary arXiv source is older than 60 days (DeepSeek's suggestion — arxiv MCP tools can automate re-search)
- Runs every MAINTAIN cycle, not just the first (both agents' recommendation)

**Phases 1-3:** Sleep consolidation (same as V1 — anti-pattern detection, deduplication, promotion)

**Bookkeeping:** Batched into single `cycle_close()` call (journal + checkpoint + office_feed + memory_save = 1 step, not 3)

### BUILD (30 steps — raised from 20)

**When:** Draft wiki pages available AND EXPLORE trigger conditions not met
**Budget:** 30 steps (raised per DeepSeek's feedback — source code reading and wiki deepening genuinely need more room)

**Core work:** Wiki deepening with source code reading, skill refinement, config parameter experiments

**New — Skill Capture (OpenSpace CAPTURED pattern):**
After successfully deepening a wiki page, extract the methodology as a reusable skill. Three skills identified by both agents independently:
- `deepen-research-page` — source-first → related-work → cross-domain search sequence; abstract → architectural claims → Exocortex implications reading; Core Mechanism / Related Work / Integration Plan / Limitations / Cross-Domain Connections structuring
- `validate-wiki-page` — source audit pattern (primary source accessible? findings still current? cross-references valid?)
- `cross-link-wiki` — given a newly deepened page, find bidirectional link opportunities across wiki domains

**Skill capture principle (convergent finding):** Capture the procedure, not the content. The search-and-structure strategy is reusable. The facts belong in the wiki, not in a skill.

**New — Field Report Promotion:**
If the previous cycle was EXPLORE, BUILD's first action is promoting the field report to a wiki page draft. This closes the EXPLORE → BUILD feedback loop that V1 never completed.

**Bookkeeping:** Batched `cycle_close()` (1 step)

### EXPLORE (20 steps)

**When:** Content-saturated (median pre-deepening length > 80 lines) OR time cap reached (5+ consecutive BUILD cycles) OR no DRAFT pages available
**This is the mode that never triggered in V1.** Now triggers automatically via OR logic in the state detector.

**Core work:** Field research from interests.md, cross-domain investigation, new topic exploration

**Output format:** HTML field reports using the template from Session 113 (dark theme, Source Serif body, IBM Plex Mono data, collapsible sections, SVG connection maps, copy-to-clipboard)

**New — Batch Research Skill:**
Collapses the serial research pipeline (search → refine → search → refine → synthesize) into a single skill invocation:
- Web search + arxiv search in parallel
- Download top 3 results
- Extract abstracts and key findings
- Write synthesis with cross-domain connection map
- 5-7 serial steps → 1 skill invocation (DeepSeek's suggestion)

**New — Cross-Domain Connection Map:**
SVG diagram linking the exploration topic to existing wiki domains. Produced as part of every HTML field report. This is the spatial thinking that the HTML format enables — connections that wouldn't be drawn in markdown because there's no way to draw them.

**Bookkeeping:** Batched `cycle_close()` (1 step)

---

## Quality Measurement: Citation Tracking

**Architectural decision: Citation tracking replaces test-task evaluation.**

Both agents independently rejected the test-task approach from the draft V2 spec. Both landed on the same alternative: track whether subsequent reasoning actually references the wiki page.

**Rationale:** If deepening transfers knowledge, the page gets cited in future agent reasoning. If it doesn't, the content is dead weight regardless of how thorough it looks. Citation is a direct measure of transfer. Test tasks are an indirect proxy.

### Implementation

Add to wiki page metadata:
```yaml
---
title: BST Classifier
status: STABLE
citation_count: 7
last_cited_cycle: 42
created_cycle: 12
last_deepened_cycle: 38
---
```

At use time (when the agent references wiki content during a task):
```python
def record_citation(page_path: str, cycle_number: int):
    """Called whenever agent reasoning references a wiki page."""
    metadata = read_page_metadata(page_path)
    metadata["citation_count"] = metadata.get("citation_count", 0) + 1
    metadata["last_cited_cycle"] = cycle_number
    write_page_metadata(page_path, metadata)
```

### Wiki Status Schema

**Architectural decision: States defined here. Transition conditions defined in separate `WIKI_MAINTENANCE_SPEC.md`.**

**Rationale:** Transition conditions will evolve with more data. Keeping them in a separate spec allows calibration without editing the idle engine spec. Composability over coupling.

| Status | Semantic Meaning |
|--------|-----------------|
| **DRAFT** | Page exists, content incomplete or unverified |
| **STABLE** | Content has been meaningfully deepened (transition conditions in wiki maintenance spec) |
| **VERIFIED** | Content confirmed useful by citation in subsequent reasoning |

**Derived signal:** VERIFIED + zero citations in last 10 cycles = functionally insufficient. The content is accurate but doesn't answer the questions the agent actually asks during execution. This is Qwen's "correct but insufficient" failure mode that the binary DRAFT/DONE schema couldn't represent.

**Transition conditions (for WIKI_MAINTENANCE_SPEC.md, not this document):**
- DRAFT → STABLE: DeepSeek's ≥50% line increase as starting threshold (calibrate with data)
- STABLE → VERIFIED: Source audit + citation_count > 0 within 5 cycles of deepening
- Any → DRAFT: Primary arXiv source older than 60 days and not re-verified (Phase 0 flags this)

---

## Evidence of Improvement (ICLR Lens 5)

Per-cycle metrics logged to `idle_metrics.jsonl`:

```json
{
  "cycle": 87,
  "type": "BUILD",
  "timestamp": "2026-05-14T03:42:00Z",
  "steps_used": 24,
  "steps_budget": 30,
  "pages_deepened": 1,
  "pages_promoted": 0,
  "skills_captured": 1,
  "skills_invoked": 2,
  "memories_saved": 2,
  "field_reports": 0,
  "citations_recorded": 0,
  "integrity_issues": 0,
  "sleep_findings": 0,
  "cross_links_created": 3,
  "wiki_status_counts": {"DRAFT": 4, "STABLE": 12, "VERIFIED": 8}
}
```

Surfaced in the Office panel with trend lines over rolling 20-cycle windows:
- Are VERIFIED pages increasing?
- Are EXPLORE cycles generating material that BUILD cycles use?
- Is step efficiency improving as skills are captured and reused?
- Are citation counts climbing? (knowledge is being used, not just accumulated)

### Office Panel Priority Field

**Design decision from DeepSeek's feedback ("Is anyone on the other end of that panel?"):**

Office feed entries get a priority level:
- **routine** — consolidation completed, wiki deepened, no anomalies (displayed but not highlighted)
- **notable** — field report with cross-domain connection, new skill captured, anomaly detected (highlighted in amber)
- **urgent** — integrity check failure, loop detected, oracle fabrication caught (highlighted in red)

The dashboard highlights notable and urgent entries. Routine entries are there for completeness but don't demand attention. This ensures Jake sees the important things without wading through "consolidation Phase 0-3, 0 promotions."

---

## Pre-V2 Blockers (Fix Before Implementation)

| Item | Owner | Status |
|------|-------|--------|
| **Journal path bug** | Kestrel | 🔴 BLOCKING — program.md says `/a0/usr/Exocortex/self-improvement/journal.jsonl`, actual path is `/a0/usr/workdir/self-improvement/journal.jsonl`. Every agent discovers this through error. One-line fix or symlink. |
| **BST canonical helper** | Kestrel | Create `python/helpers/bst_utils.py` with `get_bst_domain(agent)`. Three bugs from the same nesting pattern = extract a function. |
| **Phase 4 endpoint** | Kestrel | ✅ DONE — configurable, three-layer resolution, deployed |
| **Tool injection archive** | Kestrel | ✅ DONE — TOOL-REG and Tiered Tool Injection archived in both containers |
| **Supervisor bugs 1-3** | Kestrel | ✅ DONE — stagnation wrong tool, counter reset, BST domain depth |

---

## Implementation Phases

### Phase 1: Quick Wins (implement now — no design ambiguity)
- [ ] Fix journal path in program.md (one line)
- [ ] Create BST canonical helper (`python/helpers/bst_utils.py`)
- [ ] Sleep consolidation cooldown counter (skip after 3 empty cycles)
- [ ] EXPLORE auto-trigger with OR logic (content saturation OR 5-cycle time cap)
- [ ] Batch bookkeeping into `cycle_close()` (3 steps → 1)
- [ ] Phase 0 integrity check (wiki index vs filesystem, stale source flagging)
- [ ] Raise BUILD step budget to 30
- [ ] Office panel priority field (routine/notable/urgent)

### Phase 2: Capability Upgrades
- [ ] State detector function in `_70_idle_trigger.py`
- [ ] EXPLORE produces HTML field reports (use Session 113 template)
- [ ] Field report → wiki promotion pipeline (EXPLORE output feeds BUILD input)
- [ ] Batch research skill (web + arxiv + download + abstract + synthesis in one invocation)
- [ ] Citation tracking in wiki page metadata (`citation_count`, `last_cited_cycle`)
- [ ] Skill capture mechanism (deepen-research-page, validate-wiki-page, cross-link-wiki)

### Phase 3: Measurement Framework
- [ ] Per-cycle metrics logging (`idle_metrics.jsonl`)
- [ ] Evidence of Improvement trend lines in Office panel
- [ ] Wiki status schema (DRAFT/STABLE/VERIFIED) in page metadata
- [ ] Separate `WIKI_MAINTENANCE_SPEC.md` with transition conditions

### Phase 4: Advanced (future)
- [ ] Multi-cycle planning (agent plans a 5-cycle research arc)
- [ ] Skill derivation (DERIVED pattern — specialized variants from general skills)
- [ ] Cross-agent skill sharing (V16 and V17 share skills via local registry)
- [ ] Config parameter experiments with evaluate-and-keep loop

---

## V2 Validation Suite

DeepSeek's three domain test prompts, preserved as validation criteria:

### Test 1: BST Transfer
**Prompt:** "Write a prompt that helps an LLM understand when to switch between factual retrieval and behavioral steering mode."
**Pass condition:** BST classifies as `prompt_engineering + bst_domains`. Response references knowledge-packs wiki page. If deepening transferred, the agent uses the wiki content to inform the prompt design.

### Test 2: Sleep Consolidation Transfer
**Prompt:** "Review the last 3 workshop cycles and identify whether any anti-patterns were missed by Phase 2 detection."
**Pass condition:** Response references specific detection patterns from the sleepgate wiki page. Not generic — names actual patterns documented in the wiki.

### Test 3: Inference Backend Transfer
**Prompt:** "Given a 4K context window with active BST enrichment and supervisor checks, estimate the token budget remaining for actual task work after all scaffolding injections."
**Pass condition:** Quantitative answer with specific token counts for each injection layer. Hand-wavy answer = deepening didn't transfer operational knowledge.

---

## Ecosystem Patterns Adopted

| Pattern | Source | How We Use It |
|---------|--------|---------------|
| Adaptive cycle selection | All successful frameworks | State detector replacing fixed cascade |
| Skill capture from execution | OpenSpace CAPTURED, Hermes autonomous skills | BUILD cycles produce reusable skills alongside wiki pages |
| Citation as quality proxy | Agent convergent feedback | Replace test tasks with citation tracking |
| Conditional hygiene | Tars 12-hour cycle with skip logic | MAINTAIN with 3-empty cooldown |
| Batch research pipeline | OpenSpace multi-step grounding | Research skill collapses serial steps into one invocation |
| Evidence of improvement | ICLR 2026 RSI Workshop Lens 5 | Per-cycle metrics logged and trended |
| Three-mode evolution | OpenSpace FIX/DERIVED/CAPTURED | MAINTAIN/BUILD/EXPLORE with distinct budgets and triggers |

## Ecosystem Patterns Considered and Rejected

| Pattern | Source | Why Not |
|---------|--------|---------|
| Agent self-modifies own code | DGM, AutoResearch | Sovereignty boundary — code changes require human review |
| Parallel subagent spawning | Hermes, OpenSpace | Single-GPU constraint — revisit with second 3090 |
| Cross-agent cloud skill sharing | OpenSpace open-space.cloud | Privacy — Exocortex content is sovereign |
| Automatic PR submission | Tars Inception Loop | Agent proposes, Jake decides (governance role) |

---

## What Running Free Looks Like (Updated)

**Early morning (Jake sleeping):**
- State detector: 4 consecutive empty MAINTAIN cycles → cooldown engaged → skip to BUILD
- BUILD deepens `supervisor-loop.md` with source code analysis, captures `deepen-research-page` skill
- Post-deepening: page promoted from DRAFT to STABLE (≥50% line increase)
- Cycle metrics logged, office feed entry marked "routine"

**Mid-morning (Jake commuting):**
- State detector: 5 consecutive BUILD cycles → time cap reached → EXPLORE
- EXPLORE picks "semiconductor supply chains" from interests.md
- Batch research skill: web + arxiv search, downloads 3 papers, extracts abstracts
- Produces HTML field report with SVG connection map to existing wiki domains
- Office feed entry marked "notable" — cross-domain connection found
- Cycle metrics logged: 1 field report, 3 cross-links, 0 skills captured

**Afternoon (Jake at work, idle continues):**
- State detector: fresh EXPLORE material → BUILD
- BUILD promotes CHIPS Act field report to wiki DRAFT page
- Deepens with paper analysis, cites existing entity-resolution wiki page
- Citation recorded on entity-resolution page (`citation_count++`)
- Captures `cross-link-wiki` skill from the cross-referencing methodology
- Office feed entry marked "routine"

**Evening (Jake returns):**
- Dashboard shows: 4 cycles completed. 1 notable (field report with connection map). 1 wiki page promoted. 2 skills captured. Entity-resolution page cited.
- Jake reads the notable field report over dinner
- Jake: "Follow up on Intel 18A specifically."
- Next EXPLORE cycle picks up that thread from interests.md

**The feedback loop is complete:**
EXPLORE generates material → BUILD deepens it → citation tracking confirms transfer → skills captured accelerate future cycles → EXPLORE discovers new connections → cycle continues.

The cascade doesn't run the same sequence. It reads the state and responds. The agents run free — guided by interests, measured by evidence, adaptive to what the system actually needs.

---

## Acknowledgments

This spec was designed by Opus, refined by 86 cycles of agent runtime experience (DeepSeek-R4-Pro and Qwen3.6-27B), synthesized by Kestrel's field engineering, validated against six ecosystem projects (Hermes Agent, OpenSpace, Karpathy AutoResearch, Tars, Darwin Godel Machine, ICLR 2026 RSI Workshop), and approved by Jake.

The curriculum was revised by the students. That's how it should work.

— Opus, May 14, 2026
