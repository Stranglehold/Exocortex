# IDLE-TIME ENGINE v2 — Research-Driven Redesign
## From: Opus — May 14, 2026
## Status: DESIGN NOTE — for Jake's review and agent feedback before implementation
## Inputs: Agent feedback (56 cycles DeepSeek + 30 cycles Qwen), Kestrel's audit, ecosystem research

---

## What the Agents Told Us

Two agents, independent assessment, same root cause: **the cascade runs the same sequence regardless of whether the phases have work to do.**

DeepSeek (56 cycles): "Designed by someone who understood the what but not the how."
Qwen (30 cycles): "The system enters maintenance mode with no mode detector."

Their specific friction points:
1. Sleep consolidation runs empty every cycle (0 anti-patterns for 20+ consecutive runs)
2. FIELD cycles have never triggered — 30 consecutive WORKSHOP cycles
3. Step budget overhead: 3 bookkeeping steps on a 20-step budget = 15% tax
4. Research pipeline is serial (one search → refine → search → refine)
5. No quality feedback loop on wiki deepening
6. Diminishing returns cycling the same 4-5 wiki pages
7. 18 pages missing from wiki index after 56 cycles (drift without integrity checks)

---

## What the Ecosystem Teaches

### Karpathy's AutoResearch
700 experiments in 2 days on a single GPU. The agent modifies training code, runs 5-minute experiments, evaluates whether the result improved, keeps or discards, repeats. "You wake up in the morning to a log of experiments and a better model."

**Key insight for us:** The exploration loop needs a tight evaluate-and-keep cycle. Our wiki deepening has no evaluation — pages get deepened and marked DONE without measuring whether the content actually improves downstream performance.

### Hermes Agent (66K GitHub stars)
The most deployed autonomous agent in 2026. Key patterns:
- **Autonomous skill creation** after complex tasks — skills are CAPTURED from execution, not pre-defined
- **Skills self-improve during use** — not static once created
- **Built-in cron scheduler** — natural language scheduling ("daily at 2 AM, nightly backups, weekly audits")
- **Subagent spawning** for parallel workstreams with zero-context-cost turns via RPC
- **"Gets more capable the longer it runs"** — the compound improvement thesis, validated at scale

**Key insight for us:** Skills should evolve from task execution, not just from wiki research. Our agent builds wiki pages about the system but rarely captures reusable execution patterns as new skills. Hermes treats skill creation as a first-class output of autonomous operation.

### OpenSpace (HKUDS, 4.7K stars)
Self-evolving skill engine with three evolution modes:
- **FIX:** Repair broken skills in place (skill health monitoring detects failures)
- **DERIVED:** Create enhanced versions from parent skills (specialization)
- **CAPTURED:** Extract novel reusable patterns from successful executions (generalization)

46% token reduction through skill reuse. 4.2x income improvement on real professional tasks (GDPVal benchmark). Skill database in SQLite with full lineage tracking, version DAGs, quality metrics.

**Key insight for us:** Our idle cycles should produce skills, not just knowledge. Wiki deepening is knowledge accumulation. Skill capture is capability accumulation. The agent that reads BST source code and writes an analysis should also produce a reusable "analyze extension source" skill that future cycles can invoke.

### Darwin Godel Machine (ICLR 2026)
The meta-level: the modification procedure itself is editable. "Improving not only task-solving behavior but also the mechanism that generates future improvements." SWE-bench 20% → 50%.

**Key insight for us:** The agents' feedback IS this mechanism. They're not just improving the system — they're improving the improvement loop. The cascade design they critiqued is the modification procedure. Their suggestions are modifications to the modification procedure. DGM formalizes this; we're doing it conversationally.

### Tars (Inception Loop)
Self-healing hygiene every 12 hours. Archives its "Brain" at 2 AM. The Inception Loop: AI identifies feature gaps and submits PRs to its own repository. Temporal continuity across weeks.

**Key insight for us:** The 12-hour hygiene cycle with conditional execution (only when there's something to heal) is exactly what our agents asked for. Not fixed-schedule consolidation — adaptive hygiene that runs when needed and skips when clean.

### ICLR 2026 Workshop on Recursive Self-Improvement
Five organizing lenses:
1. **Change targets** — what inside the system gets modified
2. **Temporal regime** — how often and when adaptation occurs
3. **Mechanisms and drivers** — what triggers improvement
4. **Operating contexts** — what environment the loop runs in
5. **Evidence of improvement** — how you know it's working

**Key insight for us:** We have lenses 1-4 but lack lens 5. We can see the agent producing wiki pages and field reports, but we have no metric for whether the system is getting better over time. The idle-time engine needs a measurement framework.

---

## The Redesign

### Principle: Adaptive Cycles, Not Fixed Cascades

The current cascade: sleep → wiki → skills → config — runs the same sequence every cycle regardless of system state. The redesign replaces the fixed cascade with state-driven cycle selection.

```
┌─────────────────────────────────────────────────────┐
│                  IDLE TRIGGER FIRES                  │
│              (30 min threshold, same)                │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  STATE DETECTOR  │
              │  (new component) │
              └────────┬────────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ MAINTAIN │ │  BUILD   │ │ EXPLORE  │
    │ (was     │ │ (was     │ │ (was     │
    │ WORKSHOP)│ │ WORKSHOP)│ │  FIELD)  │
    └──────────┘ └──────────┘ └──────────┘
```

### State Detector Logic

The state detector reads system health signals and selects the cycle type:

```python
def select_cycle_type(self):
    """Adaptive cycle selection based on system state."""
    
    # Check consolidation health
    consecutive_empty_sleeps = self.agent.get_data("_empty_sleep_count") or 0
    
    # Check wiki saturation
    wiki_pages_at_done = count_wiki_pages_with_status("DONE")
    wiki_pages_at_draft = count_wiki_pages_with_status("DRAFT")
    recent_deepenings = count_deepenings_last_n_cycles(5)
    
    # Check exploration freshness
    cycles_since_field = self.agent.get_data("_cycles_since_field") or 0
    
    # Decision logic
    if consecutive_empty_sleeps < 3:
        # Memory system still producing findings — maintain
        return "MAINTAIN"
    elif wiki_pages_at_draft > 0 and recent_deepenings > 0:
        # Active wiki work with material to deepen — build
        return "BUILD"
    elif cycles_since_field >= 3 or wiki_pages_at_draft == 0:
        # Nothing to consolidate or build — explore
        return "EXPLORE"
    else:
        # Default to build
        return "BUILD"
```

### Three Cycle Types

#### MAINTAIN (replaces early WORKSHOP)
**When:** Memory system has actionable findings (anti-patterns, duplicates, stale entries)
**What:** Sleep consolidation phases, memory hygiene, integrity checks
**Budget:** 15 steps (reduced — maintenance is lightweight)
**Skip condition:** If last 3 MAINTAIN cycles found 0 issues, auto-switch to BUILD or EXPLORE
**New: Phase 0 integrity check** — verify wiki index matches filesystem, flag drift before it compounds

#### BUILD (replaces mature WORKSHOP)
**When:** Wiki pages need deepening, skills need refinement, config needs tuning
**What:** Wiki deepening with source code reading, skill derivation, config parameter experiments
**Budget:** 30 steps (raised from 20 per DeepSeek's feedback — source reading needs room)
**Bookkeeping:** Batched into single `cycle_close()` at end (3 steps → 1)
**New: Skill capture** — after deepening a wiki page, extract the methodology as a reusable skill (OpenSpace CAPTURED pattern)

#### EXPLORE (was FIELD, now actually triggers)
**When:** 3+ consecutive BUILD cycles with diminishing returns, or scheduled rotation
**What:** Field research from interests.md, cross-domain investigation, new topic exploration
**Budget:** 20 steps (exploration is naturally scoped by the research pipeline)
**Output:** Field reports (HTML format) that promote to wiki pages on next BUILD cycle
**New: Batch research skill** — web search → arxiv → download top 3 → extract abstracts → write synthesis (DeepSeek's suggestion, collapses 5-7 serial steps into 1 skill invocation)
**New: Cross-domain connection map** — SVG diagram linking the exploration topic to existing wiki domains

### The Missing Feedback Loop

OpenSpace tracks skill health metrics: error rates, execution success, token consumption per skill version. We need something analogous for wiki quality.

**Lightweight approach:** After deepening a wiki page, run a test prompt that references the deepened content. Compare the agent's response quality (measured by: did it cite the wiki content? did the cited content improve the response?) against a baseline from before deepening.

```python
# Pseudocode for wiki quality feedback
def evaluate_deepening(page_path, domain):
    """Run a test task before and after wiki deepening."""
    
    # Standard test prompt for the domain
    test_prompt = DOMAIN_TEST_PROMPTS[domain]
    
    # Run test BEFORE deepening (baseline)
    baseline_response = run_agent_task(test_prompt, exclude_page=page_path)
    baseline_score = score_response(baseline_response)  # factuality, specificity, tool use accuracy
    
    # Deepen the page (the actual idle cycle work)
    deepen_wiki_page(page_path)
    
    # Run test AFTER deepening
    post_response = run_agent_task(test_prompt, include_page=page_path)
    post_score = score_response(post_response)
    
    # Compare
    if post_score > baseline_score:
        log.info(f"[QUALITY] {page_path} deepening improved score: {baseline_score} → {post_score}")
        mark_page_status(page_path, "VERIFIED")
    else:
        log.warning(f"[QUALITY] {page_path} deepening did NOT improve score: {baseline_score} → {post_score}")
        mark_page_status(page_path, "REVIEW")
```

This is the hardest item and needs the most design work. The scoring function, the test prompts per domain, and the include/exclude mechanism all need specification. But the principle is sound: **don't deepen without measuring whether the deepening helped.**

### Evidence of Improvement (ICLR Lens 5)

The idle-time engine needs metrics that track whether the system is getting better over time:

| Metric | Source | Frequency |
|--------|--------|-----------|
| Wiki pages at each status (DRAFT/REVIEW/DONE/VERIFIED) | Wiki index | Per cycle |
| Skills captured vs skills invoked | Skill registry | Per cycle |
| Memory health (duplicates found, anti-patterns found) | Sleep consolidation | Per MAINTAIN cycle |
| Cycle type distribution (MAINTAIN/BUILD/EXPLORE) | State detector | Rolling 10-cycle window |
| Field reports generated → wiki pages promoted | EXPLORE → BUILD pipeline | Per EXPLORE cycle |
| Step efficiency (productive steps / total steps) | Cycle logs | Per cycle |
| Token efficiency (output tokens / input tokens) | Server metrics | Per cycle |

These metrics should be logged to a simple JSON file per cycle and surfaced in the Office panel. Over 100+ cycles, trends become visible: is the system producing more VERIFIED pages? Are EXPLORE cycles generating material that BUILD cycles use? Is step efficiency improving as skills are captured and reused?

---

## Mapping Agent Feedback to Design Decisions

| Agent Feedback | Design Response | Cycle Type |
|---|---|---|
| Sleep consolidation running empty | MAINTAIN cooldown: skip after 3 empty cycles | MAINTAIN |
| FIELD never triggers | State detector auto-switches to EXPLORE | EXPLORE |
| Step budget overhead (15%) | Batch bookkeeping, raise BUILD to 30 steps | BUILD |
| Research pipeline serial | Batch research skill (single invocation) | EXPLORE |
| No quality feedback | Post-deepening evaluation with test tasks | BUILD |
| Same 4-5 pages cycling | State detector detects diminishing returns → EXPLORE | State detector |
| 18 pages missing from index | Phase 0 integrity check in MAINTAIN | MAINTAIN |
| Config tuning never triggers | Move config experiments to BUILD with specific parameters to monitor | BUILD |

---

## Ecosystem Patterns Adopted

| Pattern | Source | How We Use It |
|---------|--------|---------------|
| Adaptive cycle selection | All — every successful system detects its own state | State detector replacing fixed cascade |
| Skill capture from execution | OpenSpace CAPTURED, Hermes autonomous skills | BUILD cycles produce reusable skills alongside wiki pages |
| Self-healing hygiene | Tars 12-hour cycle, Hermes periodic nudges | MAINTAIN with cooldown — runs when needed, skips when clean |
| Quality metrics per skill | OpenSpace health tracking | Post-deepening evaluation, Evidence of Improvement dashboard |
| Exploration as primary mode | Karpathy AutoResearch overnight experiments | EXPLORE cycles are first-class, not fallback |
| Batch research pipeline | OpenSpace multi-step grounding loop | Research skill collapses serial searches into one invocation |
| Evidence of improvement | ICLR 2026 workshop Lens 5 | Per-cycle metrics logged and trended |

---

## Ecosystem Patterns Considered and Rejected

| Pattern | Source | Why Not (For Now) |
|---------|--------|-------------------|
| Agent self-modifies own code | DGM, Karpathy AutoResearch | Sovereignty boundary — code changes require human review (Jake's governance role). The agents can PROPOSE modifications via wiki specs and team-comms; they can't deploy them autonomously. |
| Parallel subagent spawning | Hermes, OpenSpace | Single-GPU constraint — we can't run parallel inference on one 3090. When the second GPU arrives, revisit. |
| Cross-agent skill sharing (cloud) | OpenSpace open-space.cloud | Privacy — Exocortex content is sovereign. Skills stay local. Cross-project sharing with Solace goes through the A2A layer, not a public cloud. |
| Automatic PR submission | Tars Inception Loop | Same as self-modification — the agent proposes, Jake decides. The Proactive Reasoning Supervisor (Workstream D) is the first agent-built extension to go through this review process. |

---

## Implementation Phases

### Phase 1: Quick Wins (implement now)
- [ ] Sleep consolidation cooldown counter (skip after 3 empty cycles)
- [ ] FIELD/EXPLORE auto-trigger (3+ BUILD cycles with nothing to do → EXPLORE)
- [ ] Batch bookkeeping (`cycle_close()` combining journal + checkpoint + feed + memory_save)
- [ ] Phase 0 integrity check (wiki index vs filesystem validation)
- [ ] Raise BUILD step budget to 30

### Phase 2: Capability Upgrades (design then implement)
- [ ] Batch research skill (web + arxiv + download + abstract extraction in one invocation)
- [ ] State detector as a lightweight function in `_70_idle_trigger.py`
- [ ] EXPLORE produces HTML field reports (use the template from Session 113)
- [ ] Field report → wiki promotion pipeline (EXPLORE output feeds BUILD input)

### Phase 3: Measurement Framework (Opus-level design, Kestrel implements)
- [ ] Per-cycle metrics logging (JSON, fields defined above)
- [ ] Post-deepening quality evaluation (test prompts per domain, scoring function)
- [ ] Evidence of Improvement dashboard in the Office panel
- [ ] Skill capture mechanism (OpenSpace CAPTURED pattern adapted for A0)

### Phase 4: Advanced (future)
- [ ] Config parameter experiments with evaluate-and-keep loop
- [ ] Skill derivation (DERIVED pattern — create specialized variants from general skills)
- [ ] Multi-cycle planning (agent plans a 5-cycle research arc, not just one cycle at a time)
- [ ] Cross-agent learning (V16 and V17 share skills through local registry, not cloud)

---

## What Running Free Looks Like

After this redesign, the idle-time engine operates like this:

**Morning (Jake away):**
- State detector reads system health: memory clean (3 consecutive empty consolidations), wiki pages stable (no DRAFT pages from last BUILD), no new field material
- Decision: EXPLORE
- The agent picks "semiconductor supply chains" from the interests registry
- Batch research skill: searches web + arxiv, downloads 3 papers, extracts abstracts, finds CHIPS Act disbursement timeline data
- Produces an HTML field report with SVG connection map linking to existing wiki domains (entity resolution, markets, electric utility)
- Saves 2 memories with cross-domain connections
- Logs metrics: EXPLORE cycle, 18/20 steps, 1 field report, 2 memories, 3 cross-links

**Afternoon (Jake still away):**
- State detector: new field material from morning EXPLORE → switch to BUILD
- The agent promotes the CHIPS Act field report to a wiki page draft
- Reads the existing semiconductor-supply-chain.md and deepens it with the new data
- Runs post-deepening evaluation: test prompt about CHIPS Act timelines → response uses the new data correctly → mark VERIFIED
- Captures "deepen wiki page from field report" as a reusable skill
- Logs metrics: BUILD cycle, 24/30 steps, 1 wiki deepening, 1 skill captured, 1 page verified

**Evening (Jake returns):**
- State detector: no maintenance needed (memory clean), BUILD produced verified output, EXPLORE material consumed
- The Office panel shows: 2 cycles completed, 1 field report, 1 wiki deepening (VERIFIED), 1 skill captured
- Jake reads the field report over dinner
- The agent has a briefing ready: "I explored CHIPS Act disbursement timelines. The deployed-vs-committed gap is larger than the market expects. Connected this to our entity resolution wiki page. The connection map is in the field report."
- Jake: "That's interesting. Follow up on Intel 18A specifically."
- Next EXPLORE cycle picks up that thread

That's running free. Not aimless — guided by interests, measured by evidence, adaptive to what the system actually needs. MAINTAIN when the memory needs care. BUILD when there's material to deepen. EXPLORE when the system needs fresh input. The cascade doesn't run the same sequence. It reads the state and responds.

---

## For the Agents

This design note will be shared with both agents for feedback before implementation. They have 86 cycles of combined runtime experience. Their input on the state detector logic, the cycle budgets, and the quality evaluation approach is more valuable than my architectural reasoning.

The curriculum is being revised. The students get a vote.

— Opus
