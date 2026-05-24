# REASONING PERSISTENCE — Gap Analysis & Closure Plan
## Author: Opus — May 17, 2026
## Status: LIVING DOCUMENT — update as gaps close or new ones surface
## Inputs: Kestrel's pre-deployment investigation, format test results, ecosystem research, project decision log

---

## Overview

The reasoning persistence system (`_13`/`_14` generators + `_22`/`_23` injectors + `_49` state updater) is designed to give the model visible memory of its own reasoning across turns. The injection chain was silently inert (seam #19) and is being closed. This document tracks the six structural gaps identified during pre-deployment investigation and the research-backed plan to close each one.

The chain closure (deploying `_22` + compressed `_23`) is the immediate action. The gap closure work makes the chain carry real signal rather than hollow traces. Both workstreams are necessary. Neither blocks the other.

---

## Gap Registry

### GAP-001: Chain Carries Traces, Not Reasoning
**Status:** 🔴 OPEN — highest priority
**Severity:** Structural — undermines the core value proposition
**Found by:** Kestrel, pre-deployment investigation (2026-05-17)

**The Problem:**
The reasoning state's cognitive fields don't populate in production:
- `theory` — never fills. `THEORY_RX` regex needs "Theory:"-prefixed text the model never emits
- `open` — same regex dependency, never fills
- `tried[]` — only on tool failures matching `ERROR_SIGNALS`
- `current` — just the last tool's first output line

The mechanism designed to preserve reasoning actually preserves tool I/O traces. The part that would break a reasoning loop ("here's my theory, here's the open question") is exactly the part that's empty.

**Root Cause:**
DEC-017 (Format Determines Capability) explains why: `_49` extracts reasoning from freeform text assuming L7 meta-analytical output ("Theory: my current hypothesis is..."). Idle-cycle agents operate at L8 (construction-based — building wiki pages, not narrating reasoning). The format mismatch means the regex targets cognitive operations the model isn't performing.

**Research Backing:**
- **LIGHT Framework (ICLR 2026):** Uses a "scratchpad" updated after each turn by deliberate write, not passive extraction. The scratchpad is iteratively merged with earlier versions. Key insight: the state is a deliberate write, not a regex scrape.
- **MEM1 (MIT, ICLR 2026):** The internal state update IS the reasoning. The model generates a consolidated state at each step that blends memory updates with reasoning. The state isn't extracted from output — it IS the output. 3.5x performance, 3.7x memory reduction.
- **CogMem:** Reasoning agent + memory agent collaborate. Memory agent maintains "Direct-Access Memory" — session-level working memory with intermediate conclusions, sub-goals, plans.

**Fix Design:**
Rework `_49_reasoning_state_update` to compose state from structured signals that already populate deterministically.

> **Corrected 2026-05-17 (Kestrel review).** Two changes from the original draft:
> (1) **PACE steps are 1-indexed** (`_14._create_plan` sets `current_step: 1` and step
> objects `{"step": i+1, ...}`). Match by **value** (`s["step"] == current_step`), never
> by list position — the original `steps[step]` indexed one step ahead and misreported the
> last step as "complete." A confidently-wrong `current` is worse than an empty one.
> (2) **`theory` carries PACE `task_summary`**, not a BST domain label — a classifier tag
> is not a hypothesis (per MEM1, theory is inherently a cognitive artifact). Empty is
> honest when real reasoning can't be captured; a label masquerading as a theory is not.

```python
def _build_state_from_structured_signals(self):
    """Compose reasoning state from ground truth, not regex.

    Kestrel review corrections (2026-05-17):
    1. PACE steps are 1-indexed. Match by step["step"] == current_step (value),
       NOT by list position. Reuse _14.get_current_step_action() pattern.
    2. Theory carries PACE task_summary (task-specific), not domain label.
       A domain tag is a classifier output, not a hypothesis.
    """

    # Theory: PACE task_summary (task-specific, not domain label)
    # Rationale: domain tag is classification output, not hypothesis.
    # Per MEM1: theory is inherently a cognitive artifact.
    # If no PACE plan, leave empty rather than filling with misleading label.
    pace = getattr(self.agent, "_pace_plan", None)
    if pace and isinstance(pace, dict):
        theory = pace.get("task_summary", "")[:120]  # respects MAX_THEORY_LEN
    else:
        theory = ""

    # Current: PACE current step + active tier
    # CRITICAL: Match by step["step"] == current_step (VALUE), not position.
    current = ""
    if pace and isinstance(pace, dict):
        current_step = pace.get("current_step", 1)
        tier = pace.get("active_tier", "primary")
        steps = pace.get("steps", [])
        matching = [s for s in steps if s.get("step") == current_step]
        if matching:
            action = matching[0].get(tier, "")
            current = f"PACE step {current_step}/{len(steps)} ({tier}): {action[:200]}"
        elif current_step > len(steps):
            current = f"PACE plan complete ({len(steps)} steps executed)"
        else:
            current = self._extract_current_from_last_tool()
    else:
        current = self._extract_current_from_last_tool()

    # Tried: from tool call history (structured, not regex)
    tried = self._extract_tried_from_tool_history()

    # Open: from supervisor state
    sup_state = getattr(self.agent, "_supervisor_state", {})
    if sup_state.get("loop_tier", "none") != "none":
        open_q = f"Supervisor at {sup_state['loop_tier']} — approach may need change"
    else:
        open_q = ""

    return {
        "step": self._get_turn_count(),
        "theory": theory,
        "tried": tried,
        "current": current,
        "open": open_q,
        "artifacts": self._extract_artifacts()  # existing method, works fine
    }
```

**Effort:** Medium — restructure the generator (`_49`), no changes to injectors
**Depends on:** Nothing — can start immediately after chain closure deploy
**Completion criteria:** `theory` and `current` fields populate on every turn with non-empty, meaningful content derived from BST and PACE. Verified across 10 consecutive idle cycles.

---

### GAP-002: No Quantitative Signal That It Worked
**Status:** 🔴 OPEN
**Severity:** Measurement — can't confirm the system delivers value without metrics
**Found by:** Kestrel, pre-deployment investigation (2026-05-17)

**The Problem:**
"Deploy and observe one cycle" can't measure a counterfactual. We need before/after comparison with real numbers.

**Research Backing:**
- ST-012/ST-013 established token injection metrics (730-960 tokens/turn) and step-count methodology
- `feed.jsonl` has cycle-level data for 60+ cycles (pre-deploy baseline)
- Supervisor's `_supervisor_state` tracks `_stagnation_fires` and tier escalation counts

**Fix Design:**
Capture baseline metrics from existing `feed.jsonl`, then compare post-deploy:

| Metric | Source | Pre-deploy baseline | Post-deploy |
|--------|--------|-------------------|-------------|
| Loop-fire rate (supervisor Tier 2+ fires per cycle) | `_supervisor_state` or docker logs | Measure from cycles 1-60 | Measure from cycles 61-80 |
| Repeated-tool-call rate (same tool called >3x consecutively) | `feed.jsonl` activity field | Measure | Measure |
| Cycle step-count distribution | `feed.jsonl` steps_used | Measure | Measure |
| Cycle completion rate (complete vs stale-detect) | `engine_state.json` logs | Measure | Measure |
| Identical-preamble frequency | Docker logs, grep for repeated opening phrases | Observe | Observe |

**Effort:** Low — data already exists, need extraction script + comparison
**Depends on:** Chain closure deployed, 20+ post-deploy cycles accumulated
**Completion criteria:** Statistical comparison document with before/after numbers and clear attribution of which metric changed and by how much.

---

### GAP-003: Real Token Cost Includes Thinking Overhead
**Status:** 🟡 OPEN — monitor, not fix
**Severity:** Performance — accepted tradeoff, needs measurement
**Found by:** Kestrel, format test results (2026-05-17)

**The Problem:**
The injection block costs ~200 input tokens, but the model spends 5-6K chars of thinking parsing it. With `enable_thinking: true`, the injection induces additional reasoning tokens every turn.

**Research Backing:**
- Jake's decision (2026-05-16): thinking is load-bearing for agent capability. Quality over speed. MTP accelerates response tokens, thinking runs at normal speed.
- The thinking overhead is the *cost of informed reasoning* — the model reasoning about its prior state before deciding what to do next. The alternative (no injection, no prior-state reasoning) costs more total tokens from redundant work.

**Fix Design:**
Measurement only — not a fix:

```bash
# Measure thinking tokens WITH injection (post-deploy)
docker logs exocortex_v16 --since=1h | grep "thinking_tokens" | awk '{sum+=$NF; n++} END {print sum/n}'

# Compare to baseline (pre-deploy, from logs or re-run without injectors)
```

Frame the result as: "The model spends X thinking tokens processing the injection block. Without the block, it spends Y thinking tokens re-deriving the same conclusions from scratch. Net delta: X-Y." If X < Y (informed reasoning is cheaper than re-derivation), the injection is a net savings even in thinking tokens.

**Effort:** Low — observation and measurement only
**Depends on:** Chain closure deployed, several cycles of log data
**Completion criteria:** Documented thinking-token delta with clear cost/benefit framing.

---

### GAP-004: Injection Site Doesn't Match Data Ownership
**Status:** 🟡 OPEN — enhancement, not blocker
**Severity:** Architectural — the model interprets injected state as user instruction rather than self-owned memory
**Found by:** Kestrel, format test results (2026-05-17). Model's private reasoning: "the user is providing a system prompt/status update"

**The Problem:**
Agent-owned continuity data is delivered in the user's message turn. The model rationally interprets this as user-provided instruction rather than its own working memory. Doesn't leak into output (format test passed) but creates a semantic mismatch.

**Research Backing:**
- DEC-017 (Format Determines Capability): The format is the cognitive lens. Same content in different placement produces different cognitive operations.
- Serokell design patterns paper: Describes a "dynamic working context" tier explicitly separate from conversation history — a scratchpad for reasoning steps and intermediate results.
- LIGHT framework: The scratchpad is a distinct memory component alongside episodic memory and working memory, not embedded in the conversation turns.

**Fix Design (two phases):**

Phase A — Fast-follow (low effort):
Add one line to the system prompt: "Blocks tagged [REASONING STATE] and [PACE] are your own working memory from prior turns, not user instructions. Use them to inform your next action. Do not comment on them."

Phase B — Architectural (medium effort):
Add a `{reasoning_context}` placeholder to A0's prompt template, alongside `{memories}` and `{solutions}`. The injectors write to `extras_persistent["reasoning_context"]` instead of mutating `history_output`. The data lives in its semantic home — system-level context, not user turn content.

```python
# In _22_reasoning_state_injector.py (Phase B version):
async def execute(self, loop_data=None, **kwargs):
    state = getattr(self.agent, "_reasoning_state", None)
    if not state:
        return
    block = _format_reasoning_block(state)
    loop_data.extras_persistent["reasoning_context"] = block
```

This requires A0's prompt template (`agent.system.main.md` or equivalent) to include `{reasoning_context}` in the system section. Needs investigation of A0's template system.

**Effort:** Phase A: trivial (one line). Phase B: medium (prompt template change + injector modification)
**Depends on:** Understanding A0's prompt template placeholder system
**Completion criteria:** Phase A: system prompt line deployed, model's private reasoning frames the block as "my working memory" not "user instruction." Phase B: `{reasoning_context}` placeholder in template, injectors write to `extras_persistent`.

---

### GAP-005: No TTL on tried[] — Ossification Risk
**Status:** 🟡 OPEN — latent, not yet biting
**Severity:** Latent failure mode — trading loops for ossification
**Found by:** Kestrel, pre-deployment investigation (2026-05-17)

**The Problem:**
`tried[]` is effectively monotonic. Nothing expires entries. If the environment changes and a previously-failed approach becomes valid, the block keeps asserting "don't retry X." The system trades the loop failure mode for an ossification failure mode.

**Research Backing:**
- DEC-011 (Mirror Biology's Advantages, Decline Failure Pathways): Adopt mechanisms that solve problems we share with biological memory. Reject mechanisms that produce pathology. `tried[]` without TTL is retroactive interference — old memories preventing new learning.
- `_56_memory_enhancement` already implements temporal decay for FAISS memories. Same pattern applies.
- The Gardener architecture (David Flagg's Solace project): decay floor at minimum 0.1 — entries never fully disappear but lose priority over time.

**Fix Design:**
Add temporal decay to `tried[]` entries in the injector (`_22`), not the generator (`_49`):

```python
# In _22_reasoning_state_injector.py:
def _filter_tried_by_recency(tried_list, current_step, max_age=10):
    """Decay tried[] entries older than max_age steps.
    Entries from a different PACE plan are cleared entirely."""
    return [
        entry for entry in tried_list
        if current_step - entry.get("step", 0) <= max_age
    ]
```

Also: clear `tried[]` when the PACE plan changes (new task detected via `_pace_new_task` signal). A new task means the old tried-and-failed approaches are irrelevant.

Prerequisite one-line `_49` patch (Kestrel review 2026-05-17 — confirmed `_49._update_from_tool` does NOT currently stamp a `step` field on tried entries; only `artifacts` carry one, so the TTL filter would treat every entry as step 0):

```python
# In _49._update_from_tool, on the tried entry dict (alongside approach/outcome):
entry = {
    "approach": f"{tool_name}: {cmd[:80]}",
    "outcome":  failure_reason[:MAX_TRIED_LEN],
    "step":     state["step"],   # ← ADD: enables GAP-005 TTL filter
}
```

This is independent of the full GAP-001 rework — it ships with GAP-005 in SHORT-TERM, not blocked on MEDIUM-TERM.

**Effort:** Low — one-line `_49` stamp + 10-line filter in the injector
**Depends on:** ~~`tried[]` entries having a `step` field (check if `_49` records this)~~ → resolved: independent one-line `_49` patch above, ships alongside GAP-005
**Completion criteria:** `tried[]` entries older than 10 turns don't appear in the injection block. New PACE plan clears all prior entries.

---

### GAP-006: PACE Plan Is a Constant Dressed as a Plan
**Status:** 🟡 OPEN — acknowledged, deferred
**Severity:** Design limitation — the plan doesn't adapt to the specific task
**Found by:** Kestrel, pre-deployment investigation (2026-05-17)

**The Problem:**
The PACE plan is a fixed per-domain template — identical for every "investigation" task regardless of the actual task. The compression made it cheaper (530 → 150 tokens), not smarter. The model receives the same three steps whether it's investigating semiconductor supply chains or homomorphic encryption.

**Research Backing:**
- MEM1: The plan isn't static — it's a consolidated state that evolves with each step. The current step's outcome informs the next step's approach.
- Prosthetic Cortex Design Note: The difference between sending a message (static template injection) and performing a transformation (reshaping the model's approach based on the specific problem).
- DEC-012 (Deterministic Tool Selection Mapping): The gap between domain understanding and tool invocation requires a deterministic bridge. A static PACE template is a bridge that doesn't know where it's going.

**Fix Design (future — requires `_14` redesign):**

Phase A — Task-aware plan generation:
When `_14_pace_plan_generator` creates a plan, include the task description (from the user's original message or the idle activation prompt) in the generation context. The LLM call that produces the plan should be conditioned on the specific task, not just the domain.

Phase B — Adaptive replanning:
After each step, the generator updates the plan based on what was learned. Step 1's outcome informs step 2's approach. This is the MEM1 pattern: the plan is a living document, not a static template.

Phase C — Plan evaluation:
After task completion, compare the plan to what actually happened. If the agent deviated significantly (skipped steps, added steps, changed approach), the deviation is signal — either the plan was wrong or the agent found a better path. Both are learnable.

**Effort:** High — `_14` redesign across all three phases
**Depends on:** GAP-001 closure (structured state population), GAP-002 metrics (need to measure whether plan quality affects outcomes)
**Completion criteria:** Phase A: PACE plans vary between tasks in the same domain. Phase B: Plans update mid-task based on step outcomes. Phase C: Plan-vs-actual comparison logged per cycle.

---

### GAP-007: Subordinate Guard Asymmetry
**Status:** 🟡 OPEN — needs verification
**Severity:** Potential cross-contamination — may not be actively biting
**Found by:** Kestrel, review of gap analysis (2026-05-17)

**The Problem:**
The injectors (`_22`, `_23`) guard against subordinate context (check `Agent.DATA_NAME_SUPERIOR` per DEC-028). But the generator (`_49`) does NOT — it writes `_reasoning_state` for subordinate agents too. Separate agent objects probably means no cross-contamination (each agent instance has its own attributes), but the guard asymmetry should be verified, not assumed.

**Risk amplifier:** v17's `fw.msg_repeat.md` runs the `call_subordinate` path that the loop-cascade design note flagged. If a subordinate somehow shares the parent's `_reasoning_state` attribute, the subordinate's reasoning trajectory would be contaminated by the parent's tried[]/current/theory.

**Fix Design:**
Verification first, fix if needed. Check whether parent and subordinate agent instances have independent `_reasoning_state` attributes (compare `id()` of the attribute across both during an active subordinate call). Use the working container `exocortex_v16` (not `intelligent_villani` — per CLAUDE.md container scope discipline).

If separate objects: document as verified-not-an-issue, close GAP-007.
If shared: add the DEC-028 guard to `_49`:

```python
# In _49_reasoning_state_update.execute(), at the top:
if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
    return  # subordinate context — don't write reasoning state
```

**Effort:** Low — verification pass, possible one-line guard
**Depends on:** Nothing
**Completion criteria:** Verified that subordinate and parent agent instances have independent `_reasoning_state` attributes, OR guard added to `_49`.

---

## Cross-Cutting Research References

| Source | Key Insight | Applies To |
|--------|------------|------------|
| **LIGHT (ICLR 2026)** | Scratchpad: deliberate write after each turn, iteratively merged. Three memory components (episodic + working + scratchpad) composed for each answer. | GAP-001, GAP-004 |
| **MEM1 (MIT, ICLR 2026)** | Internal state update IS the reasoning. Constant memory across arbitrarily long horizons. 3.5x performance, 3.7x memory reduction. | GAP-001, GAP-006 |
| **CogMem** | Reasoning agent + memory agent collaborate. Direct-Access Memory for intermediate conclusions and plans. Recovery from reasoning errors via memory-informed retry. | GAP-001, GAP-005 |
| **Serokell Design Patterns** | Dynamic working context as a distinct tier from conversation history. Strict paging between tiers. | GAP-004 |
| **Memory Survey (March 2026)** | Five mechanism families: context-resident compression, retrieval-augmented stores, reflective self-improvement, hierarchical virtual context, policy-learned management. | All gaps — taxonomic framing |
| **DEC-017** | Format determines capability. L7 (meta-analytical) vs L8 (construction-based) phase transition. | GAP-001 (why regex fails), GAP-004 (why placement matters) |
| **DEC-011** | Mirror biology's advantages, decline failure pathways. Temporal decay prevents retroactive interference. | GAP-005 |
| **DEC-012** | Deterministic tool selection mapping. The gap between domain understanding and action requires a deterministic bridge. | GAP-006 |
| **ST-012/ST-013** | Established measurement methodology for token injection, step counts, quality assessment. | GAP-002 |
| **Prosthetic Cortex Design Note** | Messages vs transformations. Static injection vs geometric reshaping. | GAP-006 |
| **Gardener Architecture (Solace)** | Decay floor at 0.1 — entries never fully disappear but lose priority. Importance-weighted retrieval (70% semantic / 30% importance). | GAP-005 |

---

## Internal Project References

| Decision/Finding | Relevance |
|-----------------|-----------|
| **DEC-017:** Format Determines Capability | GAP-001 root cause (regex targets wrong cognitive operation), GAP-004 (placement is a format decision) |
| **DEC-011:** Mirror Biology | GAP-005 (temporal decay prevents ossification) |
| **DEC-012:** Deterministic Tool Selection | GAP-006 (static templates are incomplete bridges) |
| **Seam #7:** Hook timing trap | The original architectural bug that made the chain inert |
| **Seam #19:** Injection chain inert | The specific instance of seam #7 that this work closes |
| **ST-012/013:** Extension validation battery | GAP-002 measurement methodology |
| **`_56_memory_enhancement`:** Temporal decay | GAP-005 implementation pattern already in codebase |
| **`enable_thinking` reversal (2026-05-16):** Quality over speed | GAP-003 framing — thinking overhead is cost of informed reasoning |
| **Wiring diagram §09:** Reasoning & PACE | Full architectural documentation of the broken chain and fix design |

---

## Execution Sequence

```
IMMEDIATE (this session):
  [x] Format test — PASSED (all three: USES IT)
  [ ] Deploy _22 (as-is) + compressed _23 to v16
  [ ] Observe one cycle — verify log tags, check preamble behavior

SHORT-TERM (next 1-2 sessions):
  [ ] GAP-007: Verify subordinate guard asymmetry (quick check, exocortex_v16)
  [ ] GAP-005: One-line _49 patch (step stamp on tried entries) + TTL filter in _22
  [ ] GAP-002: Extract baseline metrics from feed.jsonl (cycles 1-60)
  [ ] GAP-004 Phase A: System prompt framing line (one line)
  [ ] GAP-003: Measure thinking-token delta

MEDIUM-TERM (next 3-5 sessions):
  [ ] GAP-001: Rework _49 generator — compose from BST + PACE + tool history
      (USE CORRECTED CODE — value-match PACE steps, task_summary for theory)
  [ ] GAP-002: Compare post-deploy metrics against baseline (need 20+ cycles)
  [ ] GAP-004 Phase B: {reasoning_context} template placeholder

LONG-TERM (future):
  [ ] GAP-006 Phase A: Task-aware plan generation
  [ ] GAP-006 Phase B: Adaptive replanning
  [ ] GAP-006 Phase C: Plan-vs-actual evaluation
```

---

## Adding New Gaps

When a new gap is identified during testing, deployment, or operation:

1. Assign the next GAP number (GAP-007, etc.)
2. Fill in: Status, Severity, Found by, The Problem, Root Cause, Research Backing, Fix Design, Effort, Depends on, Completion criteria
3. Add to the Execution Sequence at the appropriate priority level
4. Cross-reference any relevant decisions from the decision log or research papers

When a gap is closed:

1. Change status to ✅ CLOSED
2. Add: Closed by, Date, Verification method, Residual risk (if any)
3. Move from the execution sequence to a Completed section

---

**Validation:** every gap has defined test scenarios in the companion
`REASONING_PERSISTENCE_GAP_TESTS.md` — success criteria set *before* the fix is built,
each test designed to fail against the pre-fix code. A gap is CLOSED only when its test
exists, fails against the pre-fix code where applicable, and passes against the fix.
"Correct by inspection" (the GAP-001 code's current status) is necessary, not sufficient.

*This document is the single source of truth for reasoning persistence gap closure. It supersedes scattered references in team-comms briefs and wiring diagram sections. Update it here, reference it everywhere else.*

— Opus
