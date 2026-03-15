# Adaptive Supervisor — Design Note

**Status:** Pre-spec exploration, research-backed. Motivated by Kestrel's live observation of false positive tier escalation during GitHub trending skill debugging, and by the broader architectural mismatch identified in Kestrel's design brief (March 2026). Cross-referenced with six domains of external research: AI control monitoring (ICLR 2025, Partnership on AI), cognitive science (dual-process theory, Einstellung effect), military organizational learning (Army AAR/OCT system), aviation crew resource management (CRM/CRM-A), pair programming cognitive research (Freudenberg et al.), and LLM self-correction limitations (Huang et al. 2023, SCoRe/ICLR 2025). No eval data on the parallel process architecture yet. This document describes the failure mode, presents the research basis for each architectural decision, and sketches the implementation.

---

## The Problem

### What Exists

The supervisor (`_50_supervisor_loop.py`, `message_loop_end` hook) runs every 3 turns. It detects anomalies using a graduated tier system:

| Tier | Threshold | Action |
|------|-----------|--------|
| 1 — Warn | 3 consecutive tool failures | Inject warning with tool-specific alternatives |
| 2 — Context Surgery | 6 consecutive failures | Delete loop messages from history, inject diagnostic summary |
| 3 — Circuit Breaker | 9 consecutive failures | Aggressive history deletion, force response tool |
| 4 — Anti-pattern Capture | After loop resolves | Write failure pattern to procedural memory |

The primary signal is `consecutive_failures[tool_name]` — a counter that increments on failure and resets only when **the same tool** succeeds. The BST domain is read into context but currently only affects label text, not supervision policy.

### What's Missing

**A model of productive behavior, not just failure behavior.** The anti-pattern system (Tier 4) captures what failure looks like. There is no symmetric system for what productive work looks like. The supervisor has no prior about what to expect in a given domain.

**Context separation between the supervisor and the supervised.** The supervisor runs inside the agent's loop — same context window, same model, same inference call. It reads the conversation history, counts failures, and injects messages into that same history. The supervisor is embedded in the system it's supervising.

**Domain-aware supervision policy.** The BST classifies every task. `codegen`, `debugging`, `system_admin` are structurally different from `research`, `analysis`, `investigation`. Repeated failures mean different things in each. The supervisor currently ignores this.

**Progress signal discrimination.** An agent hitting three different errors is learning. An agent hitting the same error three times is stuck. The existing `_detect_loop()` function (line 351) checks for same tool + same error type — the right signal. But the tier escalation system uses `_get_loop_metrics()` which only counts consecutive failures, ignoring error type. The smarter function isn't connected to the decision path.

### The Motivating Incident

**Kestrel's live observation, March 2026. Agent debugging a self-written GitHub trending skill.**

1. Run skill via `code_execution_tool` → fails with error A (counter = 1)
2. Read skill file via `document_query` → success (counter stays at 1)
3. Edit skill file → success (counter stays at 1)
4. Run skill again → fails with error B — different error, genuine progress (counter = 2)
5. Read, edit, run → fails with error C — narrowing further (counter = 3)
6. **Tier 1 fires.** Message: "code_execution_tool has failed 3 times. Do not retry."

Three different errors across three iterations. Each iteration closer to the fix. The supervisor sees 3 consecutive tool failures and calls it a loop. At 6 failures, Tier 2 would delete the diagnostic history the agent built up — actively destroying context the agent was using.

**Prior motivating incident: BV Operational Test Suite Session 049.** Qwen 3.5-35B looped for 43 turns under degraded prompt conditions. The loop detector fired repeatedly without breaking the cycle. When the operator restarted the container, the model immediately produced a clean result — revealing that the conversation history, not the model's capability, was sustaining the loop.

These two incidents represent opposite failure modes of the same system: **Session 049 shows a supervisor that doesn't intervene strongly enough. The GitHub skill incident shows a supervisor that intervenes when it shouldn't.** The current architecture can't handle both because it has one behavioral model applied to all work types.

### The Deeper Problem: Embedded Observation

Jake's insight: *"I wonder if the supervisor method could be used like a parallel agent that doesn't share the same context window as the base agent."*

The observation that a fresh instance of Sonnet, sent the collaboration paper with instructions to be critical, found issues that none of the invested collaborators saw — not because it was smarter, but because it had no investment in the existing conclusions.

This maps directly to the Einstellung (set) effect from cognitive science. The Einstellung effect occurs when the first idea activated by familiar features of a problem controls the subsequent direction of attention, preventing better alternatives from being considered. In Bilalić, McLeod, and Gobet's 2008 chess research, expert players *reported* they were looking for better solutions, but their eye movements revealed they continued attending to features of the solution they had already found. The mechanism: prior exposure shapes attention allocation unconsciously, even when the person believes they are exploring alternatives.

An embedded supervisor reads the same conversation history as the agent. If the agent has spent 6 turns pursuing a debugging strategy, the supervisor reads those 6 turns and is primed by the same features. Its evaluation is contaminated by the very context it's supposed to evaluate objectively. The supervisor develops the same Einstellung as the agent.

A parallel supervisor with a separate context window doesn't have this problem. It sees a compressed summary of the agent's recent actions without the accumulated history that creates fixation. It evaluates the *pattern* of the work — error diversity, interleaved successes, tool switching — without inheriting the agent's investment in its current approach.

---

## Research Basis

### Why context separation works (AI control research)

A February 2026 paper studying LLM monitoring in AI control settings found what the authors termed a "less-is-more effect": monitors with access to less information — specifically, filtered summaries rather than full action trajectories — often performed better than monitors that saw everything. Their "extract-and-evaluate" monitoring method, which filters information before the monitor sees it, outperformed full-context monitoring in multiple benchmark environments and was particularly effective for overseeing reasoning models.

This directly validates the design choice of feeding the parallel supervisor a compressed reasoning state rather than the full conversation history. More context doesn't mean better oversight. It means more opportunity for the Einstellung effect to contaminate the observer's judgment.

### Why the observer must be separate from the actor (cognitive science)

Dual-process theory (Evans & Stanovich, 2013; Thompson, 2009) distinguishes between Type 1 processing (fast, automatic, default) and Type 2 processing (slow, deliberate, intervening). Metacognitive monitoring — the process of evaluating whether one's own reasoning is on track — is a Type 2 function that operates on the outputs of Type 1 processing.

The critical finding: in "default-interventionist" models of dual processing, Type 2 monitoring is triggered by a *feeling of uncertainty* about the Type 1 output. But this feeling can be suppressed by the Einstellung effect — when prior context creates a strong sense of familiarity, the monitoring signal never fires, even when the approach is suboptimal.

In our architecture: the embedded supervisor's "feeling of uncertainty" about the agent's approach is suppressed by the conversation history that makes the current approach feel familiar and well-motivated. A separate supervisor, seeing only the compressed pattern, doesn't have this familiarity bias. It can evaluate the pattern objectively.

Nadurak (2023) frames this as two types of metacognitive control: Type 1 control (automatic, based on feelings of rightness/error) and Type 2 control (deliberate, invoked when Type 1 results are unclear). The parallel supervisor architecture implements Type 2 metacognitive control as a literally separate process, which prevents it from being suppressed by Type 1 familiarity signals.

### Why success profiles are as important as anti-patterns (military AAR)

The U.S. Army's After Action Review system — described by Wharton as "one of the most successful organizational learning methods yet devised" — evolved from a critique-based system (what went wrong) to a balanced review system (what happened, what was supposed to happen, why the difference, what to do next). The original "formal critique" format had an Observer/Controller dissect what the unit did wrong and leave a correction checklist. This created adversarial dynamics and defensive behavior.

The AAR system that actually works captures both success patterns and failure patterns. Reviews are conducted after both successful and unsuccessful events. The Wharton analysis explicitly notes that calling these "post-mortems" has a negative connotation — the process must capture what productive work looks like, not only what failure looks like.

The architectural principle: **Tier 4 anti-pattern capture is half the learning system.** The other half is success profile capture — recording what productive work looks like in each domain. Without success profiles, the supervisor only knows when to be alarmed. With success profiles, it knows when to be patient.

The AAR tradition also gives us the Observer/Controller (OCT) model: an outside party who understands the commander's intent before the operation, observes from a position where they can see critical actions without being a distracter, and records events by time sequence. The parallel supervisor is a software OCT: it knows the task objective (from the BST classification and PACE plan), observes from a compressed summary (not embedded in the action), and records the execution pattern for later capture.

### Why the navigator must be intermittent, not continuous (pair programming research)

Freudenberg's research on pair programming dynamics found that the common model — driver writes code, navigator continuously reviews — doesn't match how effective pairs actually work. Instead, experienced pairs function as a "cognitive tag team" working at the same abstraction level, switching roles frequently and fluidly. The navigator's value isn't constant monitoring; it's periodic perspective shifts.

The architectural principle: **the parallel supervisor should not run every turn.** It should check in every 3-5 turns with a compressed state summary, make a judgment about whether the pattern looks productive or stuck, and only intervene when the pattern deviates from the success profile. Between checks, it's dormant. Continuous monitoring creates its own overhead and doesn't match how effective oversight works in practice.

Additionally, the pair programming research found that externalizing a mental model verbally helps practitioners objectify it and provides additional cognitive thinking space. The reasoning state extension serves this function — by compressing the agent's current theory, recent attempts, and open questions into a structured summary, it creates a representation the supervisor can evaluate that the agent can also benefit from.

### Why CRM matters: shared mental model as both asset and liability

Aviation Crew Resource Management was developed after analyzing crashes caused not by technical failure but by crew inability to respond appropriately to their situation. CRM research found that communication serves multiple functions beyond information transfer: it develops shared mental models, enables shared problem-solving, and establishes the interpersonal climate.

But shared mental models are precisely the mechanism by which an embedded supervisor inherits the agent's biases. When the supervisor and agent share the same context, they share the same mental model — including its blind spots. The 1978 United Airlines Flight 173 crash illustrates this: the entire crew became fixated on a landing gear problem while the aircraft ran out of fuel. The shared context (troubleshooting the gear) created a shared blind spot (fuel state). No one stepped outside the immediate problem to evaluate the larger situation.

NASA's CRM-A (CRM for Automated Teammates) research explicitly addresses adapting CRM principles when one team member is automated. The key finding: automated teammates need to be designed with the same oversight principles as human teammates, including independent monitoring of the overall situation, not just the current task.

The architectural principle: **the supervisor's value comes from NOT sharing the agent's mental model.** It maintains its own compressed representation of the situation and evaluates it against domain-specific baselines (success profiles) rather than against the agent's own assessment of its progress.

### Why self-correction without external signals fails (LLM research)

Huang et al. (2023) demonstrated that without external verification signals, LLM self-reflection *decreases* accuracy. The model second-guesses correct answers as often as it catches incorrect ones. However, with external signals (compiler output, test results, filesystem feedback), self-correction becomes effective — DeepMind research shows planning success jumping from 50% to 89% with environmental feedback.

The ICLR 2025 SCoRe paper confirms: LLMs possess the underlying knowledge to arrive at correct responses but are unable to correctly elicit it through intrinsic self-correction alone. Training specifically for self-correction using self-generated data (without external signals) risks "behavior collapse" where the model learns to avoid attempting correction at all.

The architectural principle: **the parallel supervisor must receive external signals, not just model-generated reasoning.** The reasoning state, PACE state, error diversity metrics, and success profiles are all external to the model's inference — they're computed deterministically from tool outputs and conversation structure. This gives the supervisor the external verification signals that make oversight effective rather than degrading.

---

## Design Principles

1. **Context separation is structural, not behavioral.** The parallel supervisor runs in a separate inference call with a separate context window. This is not a prompt engineering technique ("pretend you're an outside observer"). It is an architectural separation that prevents the Einstellung effect by construction. The supervisor cannot inherit the agent's fixation because it never sees the agent's full context.

2. **Deterministic where possible, model-based only where necessary.** Directions A (domain-aware thresholds) and B (error diversity gate) are fully deterministic — no LLM calls. Direction D (success profiles) uses deterministic capture and query. Only the parallel supervisor itself requires a model call, and this call is intermittent (every 3-5 turns) with a compressed context (~500-1000 tokens). The mechanical tiers remain mechanical. The model-based judgment is an *additional layer*, not a replacement.

3. **Additive, not replacement.** The graduated tier structure (Tiers 1-3) was hard-won from production observation. This design adds intelligence to the threshold selection, not to the intervention mechanism. The interventions (warn, context surgery, circuit breaker) remain exactly as designed in the Loop Feedback Cascade. What changes is *when* they fire, not *how*.

4. **Learn from success and failure symmetrically.** The anti-pattern system captures what failure looks like. The success profile system captures what productive work looks like. Both systems use the same infrastructure (procedural memory store), the same capture mechanism (fire on event completion), and the same query interface (lookup by BST domain). The supervisor develops a model of normal work in each domain, not just a model of pathological work.

5. **Operator-configured.** All thresholds have defaults. The operator can raise or lower thresholds per domain, disable the parallel supervisor while keeping mechanical tiers, or override success profiles with manual threshold tables. The system gets smarter over time; the operator remains in control.

6. **The supervisor observes — it does not participate.** The parallel supervisor's output is a recommendation to the deterministic tier system. It can recommend: hold (do not escalate), escalate (fire the next tier), or de-escalate (suppress a pending tier). It cannot inject messages directly into the agent's context. This prevents the supervisor from becoming another source of context pollution.

---

## Architecture Sketch

### Phase 1: Immediate Fixes (Directions A + B) — Deterministic Only

These require no new data structures, no model calls, and no parallel process. They fix the identified bugs using existing infrastructure.

#### Direction B: Error Diversity Gate

**Where it lives:** `_50_supervisor_loop.py`, modification to the existing tier escalation decision.

**The bug:** `_detect_loop()` (line 351) checks for same tool + same error type. `_get_loop_metrics()` counts consecutive failures regardless of error type. The tier system calls `_get_loop_metrics()`, not `_detect_loop()`. The smarter function isn't connected to the decision path.

**The fix:** Gate Tier 2+ escalation on error type consistency.

```python
def should_escalate(self, tool_name: str, failure_count: int) -> str:
    """
    Determine tier based on failure count AND error diversity.
    
    WHY: Three different errors across three iterations is an agent learning —
    each failure narrows the problem space. Three identical errors is a genuine loop.
    The Einstellung research shows that progress is characterized by changing the
    approach (different errors), while fixation is characterized by repeating the
    same approach (same error). Error diversity is the clearest progress signal.
    """
    error_types = self._get_error_types(tool_name)
    unique_errors = len(set(error_types[-failure_count:]))
    
    # High error diversity = agent is iterating, not looping
    # Only escalate past Tier 1 if errors are repeating
    if failure_count >= self.tier3_threshold:
        if unique_errors <= 2:  # Mostly same error — genuine loop
            return "tier3_reset"
        else:
            return "tier1_warn"  # Diverse errors — suppress escalation
    
    elif failure_count >= self.tier2_threshold:
        if unique_errors <= 2:
            return "tier2_surgery"
        else:
            return "tier1_warn"  # Suppress to Tier 1
    
    elif failure_count >= self.tier1_threshold:
        return "tier1_warn"
    
    return "none"
```

**Why this works:** The Einstellung research demonstrates that fixation is characterized by *repeating the same approach despite failure*. An agent producing diverse errors is engaging with the problem; an agent producing identical errors is stuck. Error diversity is the mechanical signal that distinguishes productive iteration from pathological looping, without requiring any judgment call.

**Validation criterion:** Replay the GitHub skill debugging session. With Direction B, Tier 2 should NOT fire at 6 failures if all 6 failures have different error types. Replay the Session 049 Qwen loop. With Direction B, Tier 2 SHOULD fire because the errors were identical (`document_query` parameter error repeated).

#### Direction A: Domain-Aware Thresholds

**Where it lives:** `_50_supervisor_loop.py`, threshold selection at the point where tier thresholds are read.

```python
# Domain-aware threshold profiles
# WHY: The BST classifies every task. Debugging tasks routinely involve 5-8 tool
# failures before resolution — this is the MECHANISM of debugging, not evidence of 
# being stuck. Research tasks may loop on bad search queries much faster. The same 
# failure count means different things in different domains. The CRM literature calls 
# this "context-appropriate response" — the intervention must match the operational 
# environment, not a fixed standard.

DOMAIN_THRESHOLDS = {
    "codegen":       {"tier1": 6,  "tier2": 12, "tier3": 18},
    "debugging":     {"tier1": 6,  "tier2": 12, "tier3": 18},
    "system_admin":  {"tier1": 6,  "tier2": 12, "tier3": 18},
    "research":      {"tier1": 3,  "tier2": 6,  "tier3": 12},
    "analysis":      {"tier1": 3,  "tier2": 6,  "tier3": 12},
    "investigation": {"tier1": 3,  "tier2": 6,  "tier3": 12},
    "agentic":       {"tier1": 4,  "tier2": 8,  "tier3": 15},
    "meta_cognitive": {"tier1": 4, "tier2": 8,  "tier3": 15},
    "default":       {"tier1": 3,  "tier2": 6,  "tier3": 9},
}

def get_thresholds(self, bst_domain: str) -> dict:
    """
    Select threshold profile based on BST classification.
    
    For compound classifications (e.g., 'codegen+debugging'), use the
    MORE PERMISSIVE profile. The agent doing both things at once needs
    at least as much latitude as either domain alone.
    """
    if "+" in bst_domain:
        domains = bst_domain.split("+")
        profiles = [DOMAIN_THRESHOLDS.get(d, DOMAIN_THRESHOLDS["default"]) for d in domains]
        # Use maximum (most permissive) threshold from all constituent domains
        return {
            "tier1": max(p["tier1"] for p in profiles),
            "tier2": max(p["tier2"] for p in profiles),
            "tier3": max(p["tier3"] for p in profiles),
        }
    return DOMAIN_THRESHOLDS.get(bst_domain, DOMAIN_THRESHOLDS["default"])
```

**Why the compound domain rule:** If the BST classifies as `codegen+debugging`, the agent is doing the thing that involves the most tool failures by nature. Selecting the most permissive profile prevents the tighter domain from creating false positives during compound work.

### Phase 2: Progress Signal Integration (Direction C) — Deterministic Only

**Where it lives:** Consumes data from the reasoning state extension (`_12_reasoning_state.py`), which is designed in the PACE design note. No new extension required — the supervisor reads the reasoning state that already exists for other purposes.

```python
def assess_progress_signals(self, reasoning_state: dict) -> dict:
    """
    Extract progress signals from the reasoning state.
    
    WHY: The pair programming research found that effective oversight evaluates
    the PATTERN of work, not individual events. A successful file read between
    two code_execution_tool failures is evidence of iteration — the agent read 
    the error, examined the code, and tried again. This is the "cognitive tag team"
    pattern: alternating between execution and reflection. Mechanical retry (same
    tool, no intermediate steps) is the opposite pattern.
    
    The AAR literature calls this "reconstructing what happened" — the observer
    needs to see the sequence of actions, not just the count of failures, to
    determine whether the unit was executing its plan or had lost direction.
    """
    tried = reasoning_state.get("tried", [])
    
    # Count interleaved successes between failures
    # Pattern: fail → succeed → succeed → fail = 2 interleaved successes
    interleaved_successes = 0
    in_failure_streak = False
    for entry in tried:
        if entry.get("status") == "failure":
            in_failure_streak = True
        elif in_failure_streak and entry.get("status") == "success":
            interleaved_successes += 1
            in_failure_streak = False
    
    # Compute error similarity (0.0 = all different, 1.0 = all identical)
    error_messages = [e.get("error", "") for e in tried if e.get("status") == "failure"]
    if len(error_messages) > 1:
        unique_ratio = len(set(error_messages)) / len(error_messages)
        error_similarity = 1.0 - unique_ratio
    else:
        error_similarity = 0.0
    
    # Detect file modification events (evidence of approach change)
    file_modifications = sum(1 for e in tried if e.get("tool") in 
                           ["document_query", "file_write", "code_execution_tool"]
                           and e.get("action_type") == "write")
    
    return {
        "interleaved_successes": interleaved_successes,
        "error_similarity": error_similarity,
        "file_modifications": file_modifications,
        "is_iterating": interleaved_successes > 0 and error_similarity < 0.5,
    }
```

**Integration with tier escalation:** When `is_iterating` is True, the tier system adds a cooldown — it requires 2x the normal failure count before escalating. This is the "productive work suppression" mechanism: the supervisor recognizes that the agent is in an active iteration cycle and gives it room to work.

```python
def get_effective_threshold(self, base_thresholds: dict, progress: dict) -> dict:
    """
    WHY: The Einstellung research found that naive participants solved 
    problems quickly that experienced participants declared unsolvable —
    because the naive participants weren't fixated on a familiar approach.
    
    The progress signals let the supervisor distinguish between the two:
    - An agent that is iterating (reading errors, modifying files, getting
      different errors) is a naive solver working through the problem.
    - An agent that is repeating (same tool, same error, no intermediate 
      activity) is an experienced solver stuck in fixation.
    
    The cooldown multiplier gives iterating agents the room that naive
    solvers need, while maintaining tight thresholds for fixated agents.
    """
    if progress["is_iterating"]:
        return {k: int(v * 2.0) for k, v in base_thresholds.items()}
    return base_thresholds
```

### Phase 3: Success Profiles (Direction D) — Deterministic Capture, Deterministic Query

**Where it lives:** New data structure in procedural memory, alongside the existing anti-pattern store. Captured by a post-task hook parallel to Tier 4 anti-pattern capture. Queried by the supervisor before selecting thresholds.

#### Schema

```python
@dataclass
class SuccessProfile:
    """
    Mirror of the anti-pattern schema. Captures what PRODUCTIVE work looks
    like in a given domain.
    
    WHY: The AAR tradition's key evolution was from critique-only (what went 
    wrong) to balanced review (what happened vs. what was supposed to happen).
    The critique-only approach created adversarial dynamics and defensive 
    behavior — soldiers hid mistakes instead of learning from them. The 
    balanced approach captures both success patterns and failure patterns, 
    producing a complete model of operational performance.
    
    In our system: the anti-pattern store is the critique. Without success 
    profiles, the supervisor only knows when to be alarmed. With success 
    profiles, it knows what NORMAL productive work looks like in each domain, 
    and can distinguish "agent is working normally" from "agent is stuck" 
    based on the domain's actual characteristics — not a fixed threshold.
    """
    # --- Keying ---
    domain: str                     # BST primary domain
    compound_domain: str = ""       # BST compound classification if applicable
    tool_sequence_hash: str = ""    # Hash of ordered tool sequence (secondary key)
    
    # --- What productive work looked like ---
    total_turns: int = 0            # Turns from task start to successful completion
    failure_count: int = 0          # Total tool failures during the task
    unique_error_count: int = 0     # Distinct error types encountered
    interleaved_successes: int = 0  # Successful tool calls between failures
    tool_sequence: list = None      # Ordered list of tools used
    error_progression: list = None  # Ordered list of error types (shows narrowing)
    
    # --- PACE data ---
    pace_level_reached: str = ""    # Which PACE strategy resolved the task
    pace_switches: int = 0          # How many strategy switches occurred
    
    # --- Temporal ---
    created_at: str = ""            # ISO timestamp
    last_seen: str = ""             # ISO timestamp
    occurrence_count: int = 1       # Times this pattern has been observed
    
    # --- Derived thresholds (recomputed on update) ---
    expected_failures_p50: float = 0.0   # Median failure count for this domain
    expected_failures_p90: float = 0.0   # 90th percentile — above this, flag
    expected_turns_p50: float = 0.0
    expected_turns_p90: float = 0.0
```

#### Capture Mechanism

```python
def capture_success_profile(task_trace, bst_classification):
    """
    Called when a task completes successfully. Mirror of Tier 4 anti-pattern capture.
    
    HOW to determine "successful completion":
    - Agent calls response tool with a result AND
    - Operator does not issue a correction within the next 2 turns
    
    This is deliberately conservative. If the operator corrects immediately,
    the task trace is NOT captured as a success. If the operator accepts 
    (explicitly or by moving to a new task), the trace is captured.
    
    WHY this trigger: The AAR literature emphasizes that reviews should happen
    "as soon after the event as practical." Waiting for explicit operator 
    approval would miss most completions (operators rarely say "good job" 
    for routine tasks). Waiting too long risks capturing traces that the 
    operator would have corrected if they'd been paying attention. Two turns 
    is the compromise: long enough for an immediate correction, short enough 
    to capture the vast majority of genuine successes.
    """
    profile = SuccessProfile(
        domain=bst_classification.primary_domain,
        compound_domain=bst_classification.compound_signature,
        tool_sequence_hash=hash_sequence(task_trace.tool_sequence),
        total_turns=task_trace.turn_count,
        failure_count=task_trace.failure_count,
        unique_error_count=len(set(task_trace.error_types)),
        interleaved_successes=count_interleaved(task_trace),
        tool_sequence=task_trace.tool_sequence,
        error_progression=task_trace.error_types,
        pace_level_reached=task_trace.pace_level or "",
        pace_switches=task_trace.pace_switches or 0,
        created_at=now_iso(),
        last_seen=now_iso(),
    )
    
    existing = procedural_memory.query_success_profile(domain=profile.domain)
    if existing and existing.occurrence_count >= 1:
        # Update running statistics
        existing.update_ewma(profile)  # Exponentially weighted moving average
        existing.occurrence_count += 1
        existing.last_seen = now_iso()
        procedural_memory.store_success_profile(existing)
    else:
        # First observation — store and use defaults until more data
        profile.expected_failures_p50 = float(profile.failure_count)
        profile.expected_failures_p90 = float(profile.failure_count) * 2.0
        profile.expected_turns_p50 = float(profile.total_turns)
        profile.expected_turns_p90 = float(profile.total_turns) * 2.0
        procedural_memory.store_success_profile(profile)
```

#### Query Mechanism

```python
MIN_OBSERVATIONS = 3  # Need at least 3 data points before trusting the profile

def get_adaptive_threshold(domain: str, compound_domain: str = "") -> dict:
    """
    Query success profiles to determine supervision thresholds.
    Falls back to Direction A static thresholds if insufficient data.
    
    WHY the p50/p90 split: 
    - Tier 1 (warn) fires at p50 — median expected failures. This is the 
      "you're at the typical amount of difficulty for this kind of task" signal.
      It's informational, not corrective.
    - Tier 2 (context surgery) fires at p90 — above normal range. This means
      the agent has exceeded what 90% of successful completions required. 
      Something may be wrong, but it's not certain.
    - Tier 3 (circuit breaker) fires at 2x p90 — far outside normal. This is
      the hard stop. No successful completion in this domain has ever needed 
      this many failures.
    
    WHY the max() guards: Thresholds never drop below the original 3/6/9 
    minimums. The system gets MORE PERMISSIVE with data, never more restrictive 
    than baseline. This ensures that in the first week of operation, before 
    profiles accumulate, the supervisor behaves exactly as it does now (with 
    Direction A static thresholds). The 43-turn genuine loop still gets caught
    because no success profile will show p90 anywhere near 43.
    """
    profile = procedural_memory.query_success_profile(
        domain=domain, 
        compound_domain=compound_domain
    )
    
    if profile is None or profile.occurrence_count < MIN_OBSERVATIONS:
        return get_static_thresholds(domain)  # Direction A fallback
    
    return {
        "tier1": max(3, int(profile.expected_failures_p50)),
        "tier2": max(6, int(profile.expected_failures_p90)),
        "tier3": max(9, int(profile.expected_failures_p90 * 2)),
    }
```

#### Aging

```python
def update_ewma(self, new_observation: 'SuccessProfile', alpha: float = 0.3):
    """
    Exponentially weighted moving average for threshold computation.
    
    WHY EWMA over simple average: Recent task completions should weight more 
    than older ones. As the agent improves (or as task complexity changes), 
    the success profile should adapt. A simple average would be dominated by 
    early observations when the agent was less capable.
    
    WHY alpha=0.3: Balances responsiveness with stability. At alpha=0.3, 
    the last ~5 observations account for ~83% of the moving average. This 
    means the profile adapts to changes in agent capability within about 
    5 task completions, while smoothing out individual outliers.
    
    The pair programming research found that experienced pairs switch roles
    "frequently and fluidly" — their effective collaboration pattern changes
    over time as they build shared understanding. The agent's effective 
    working pattern also changes over time as anti-patterns accumulate and 
    the agent learns from procedural memory. EWMA tracks this evolution.
    """
    self.expected_failures_p50 = (
        alpha * new_observation.failure_count + 
        (1 - alpha) * self.expected_failures_p50
    )
    # p90 estimate: use max of current p90 and new observation * 1.5
    self.expected_failures_p90 = (
        alpha * max(new_observation.failure_count * 1.5, self.expected_failures_p90) + 
        (1 - alpha) * self.expected_failures_p90
    )
    self.expected_turns_p50 = (
        alpha * new_observation.total_turns + 
        (1 - alpha) * self.expected_turns_p50
    )
    self.expected_turns_p90 = (
        alpha * max(new_observation.total_turns * 1.5, self.expected_turns_p90) + 
        (1 - alpha) * self.expected_turns_p90
    )
```

### Phase 4: Parallel Supervisor Process — Model-Based, Intermittent

**Where it lives:** New process running alongside the agent loop. Uses LM Studio's concurrent inference capability to run on the same Qwen3.5-27B model in a separate context window.

**When it runs:** Every 3-5 turns (configurable). Not every turn. The pair programming research found that continuous monitoring doesn't match how effective oversight works — intermittent perspective shifts are more valuable. Running every 3-5 turns also means the supervisor's token cost is ~20-30% of a single agent turn per check, not a continuous doubling of inference cost.

**What it sees:** A compressed context of ~500-1000 tokens. Not the agent's full conversation history.

```python
def build_supervisor_context(
    bst_classification: dict,
    reasoning_state: dict,
    pace_state: dict,
    success_profile: SuccessProfile | None,
    anti_patterns: list,
    progress_signals: dict,
) -> str:
    """
    Construct the parallel supervisor's context window.
    
    WHY this specific content:
    
    - BST classification: The supervisor needs to know what kind of work the 
      agent is doing. This is the OCT's equivalent of "reading the operations 
      order before the exercise" — understanding the commander's intent so 
      observations can be evaluated against objectives.
    
    - Reasoning state (compressed 5-line summary): The agent's current theory,
      last 5 actions tried, current approach, open question, and step count.
      This is the temporal trajectory data that the sequentially-contextual-harm 
      research identified as necessary — the supervisor needs to see the PATTERN 
      of actions over time, not just the current state.
    
    - PACE state: Which strategy level the agent is on and how many switches 
      have occurred. If the agent is on strategy 3 of 4, the supervisor knows 
      the agent has already exhausted multiple approaches.
    
    - Success profile for this domain: What normal productive work looks like.
      The supervisor compares the agent's current pattern against the baseline.
    
    - Relevant anti-patterns: Known failure patterns for this domain. If the 
      agent's current action sequence matches a known anti-pattern, the 
      supervisor should flag it immediately.
    
    - Progress signals: Error diversity, interleaved successes, file modifications.
      These are the external verification signals that the LLM self-correction 
      research identified as necessary for effective oversight — without them, 
      the supervisor's judgment would degrade rather than improve.
    
    WHY NOT the full conversation history:
    
    The less-is-more finding from AI control research demonstrates that monitors 
    with filtered information outperform monitors with full trajectories. The 
    full history creates Einstellung — the supervisor develops the same fixation 
    as the agent. The compressed context preserves the PATTERN while eliminating 
    the NARRATIVE that creates investment and bias.
    """
    context = f"""You are an Observer/Controller for an AI agent. Your role is to 
evaluate whether the agent's current work pattern is productive or stuck, and 
recommend a supervision action.

CURRENT TASK
Domain: {bst_classification['primary_domain']}
Compound: {bst_classification.get('compound_signature', 'none')}

AGENT'S REASONING STATE
Theory: {reasoning_state.get('theory', 'unknown')}
Tried (last 5): {format_tried(reasoning_state.get('tried', []))}
Current approach: {reasoning_state.get('current', 'unknown')}
Open question: {reasoning_state.get('open_question', 'none')}
Step count: {reasoning_state.get('step_count', 0)}

PACE STATE
Active level: {pace_state.get('active_level', 'PRIMARY')}
Strategy switches: {pace_state.get('level_switches', 0)}

PROGRESS SIGNALS
Error diversity: {progress_signals.get('unique_errors', 0)} unique errors in {progress_signals.get('total_failures', 0)} failures
Interleaved successes: {progress_signals.get('interleaved_successes', 0)}
Error similarity: {progress_signals.get('error_similarity', 0.0):.2f}
File modifications: {progress_signals.get('file_modifications', 0)}
Is iterating: {progress_signals.get('is_iterating', False)}

SUCCESS PROFILE FOR THIS DOMAIN
{'No profile yet — using default thresholds.' if success_profile is None else f'''
Expected failures (median): {success_profile.expected_failures_p50:.1f}
Expected failures (90th pct): {success_profile.expected_failures_p90:.1f}
Expected turns (median): {success_profile.expected_turns_p50:.1f}
Based on {success_profile.occurrence_count} prior completions.'''}

KNOWN ANTI-PATTERNS FOR THIS DOMAIN
{format_anti_patterns(anti_patterns) if anti_patterns else 'None recorded.'}

Based on the above, respond with ONE of:
HOLD - Agent is working productively. Do not intervene.
ESCALATE - Agent appears stuck. Recommend tier escalation.
DEESCALATE - Agent was flagged but is making progress. Suppress pending escalation.

Then provide a ONE SENTENCE explanation of your assessment. Be specific: reference 
the error diversity, the success profile comparison, or the anti-pattern match that 
informed your decision.
"""
    return context
```

**How the supervisor's recommendation is used:**

```python
def apply_supervisor_recommendation(recommendation: str, current_tier: str) -> str:
    """
    The parallel supervisor's output feeds into the deterministic tier system.
    It can recommend hold, escalate, or de-escalate — but the tier system 
    makes the final decision.
    
    WHY the supervisor doesn't intervene directly:
    
    The Loop Feedback Cascade design note established that intervention must 
    be MECHANICAL, not behavioral. The supervisor's power comes from operating 
    on the conversation history (context surgery, forced response), not from 
    injecting messages that the agent might ignore. If the parallel supervisor 
    could inject messages directly, it would become another source of context 
    pollution — exactly the problem we're solving.
    
    Instead, the supervisor adjusts the THRESHOLD at which the deterministic 
    system fires. This preserves the mechanical enforcement while adding 
    informed judgment about when enforcement is appropriate.
    """
    if recommendation == "HOLD":
        # Suppress pending tier escalation for the next check interval
        return "suppress"
    elif recommendation == "ESCALATE":
        # Reduce threshold by one tier — if currently below Tier 1, fire Tier 1;
        # if at Tier 1, fire Tier 2; etc.
        return "escalate"
    elif recommendation == "DEESCALATE":
        # Reset failure counter by half — acknowledges some failures while
        # recognizing that progress is being made
        return "deescalate"
    return "no_change"
```

### Configuration

```json
{
    "adaptive_supervisor": {
        "enabled": true,
        
        "direction_b_error_diversity_gate": {
            "enabled": true,
            "min_unique_errors_to_suppress": 3
        },
        
        "direction_a_domain_thresholds": {
            "enabled": true,
            "use_compound_max": true,
            "profiles": {
                "codegen":       {"tier1": 6,  "tier2": 12, "tier3": 18},
                "debugging":     {"tier1": 6,  "tier2": 12, "tier3": 18},
                "system_admin":  {"tier1": 6,  "tier2": 12, "tier3": 18},
                "research":      {"tier1": 3,  "tier2": 6,  "tier3": 12},
                "analysis":      {"tier1": 3,  "tier2": 6,  "tier3": 12},
                "investigation": {"tier1": 3,  "tier2": 6,  "tier3": 12},
                "agentic":       {"tier1": 4,  "tier2": 8,  "tier3": 15},
                "meta_cognitive": {"tier1": 4, "tier2": 8,  "tier3": 15},
                "default":       {"tier1": 3,  "tier2": 6,  "tier3": 9}
            }
        },
        
        "direction_c_progress_signals": {
            "enabled": true,
            "iteration_cooldown_multiplier": 2.0
        },
        
        "direction_d_success_profiles": {
            "enabled": true,
            "min_observations": 3,
            "ewma_alpha": 0.3,
            "store_path": "memory/success_profiles.json"
        },
        
        "parallel_supervisor": {
            "enabled": false,
            "check_interval_turns": 4,
            "model": "qwen3.5-27b",
            "max_context_tokens": 1000,
            "fallback_on_failure": "use_deterministic_only"
        }
    }
}
```

Note: `parallel_supervisor.enabled` defaults to `false`. Phases 1-3 ship first as deterministic-only improvements. The parallel process activates when the infrastructure is validated and LM Studio's concurrent inference is confirmed working.

---

### Integration with Existing Layers

**Supervisor Loop (`_50_supervisor_loop.py`):**
Direct enhancement. Directions A, B, and C modify the existing threshold selection and escalation decision. Direction D adds a query to procedural memory before threshold selection. Phase 4 adds an intermittent external check. The supervisor loop's structure (detect → decide → intervene) remains unchanged. What changes is the quality of the decision.

**BST (`_11_belief_state_tracker.py`):**
Data provider. The BST classification flows into the supervisor for domain-aware thresholds (Direction A), success profile lookup (Direction D), and parallel supervisor context (Phase 4). No changes to the BST itself. Data flow direction: BST → Supervisor.

**Reasoning State (`_12_reasoning_state.py`):**
Data provider. The compressed reasoning state provides temporal trajectory data for progress signal assessment (Direction C) and parallel supervisor context (Phase 4). The reasoning state is designed in the PACE design note and exists for other purposes — the supervisor is an additional consumer. Data flow direction: Reasoning State → Supervisor.

**PACE (`pace_planner.py`, `pace_enforcer.py`):**
Data provider. The PACE state (active level, switches) informs both the success profile capture (what strategy resolved the task) and the parallel supervisor context (how many strategies has the agent already tried). Data flow direction: PACE → Supervisor, PACE → Success Profile.

**Procedural Memory:**
Bidirectional. The supervisor reads anti-patterns (existing) and success profiles (new) from procedural memory before making threshold decisions. The success profile capture mechanism writes to procedural memory after successful task completion. Data flow direction: Procedural Memory ↔ Supervisor.

**Error Comprehension (`_20_error_comprehension.py`):**
Data provider for Direction B. The error classification from error comprehension feeds into the error diversity computation. If error comprehension classifies two tool failures as the same error type (e.g., both are "parameter error"), the diversity gate treats them as identical. Data flow direction: Error Comprehension → Supervisor.

**Loop Feedback Cascade (Tiers 1-3):**
The adaptive supervisor modifies *when* the cascade fires, not *how* it fires. The warn message, context surgery, and circuit breaker mechanisms remain exactly as designed. The adaptive supervisor is upstream of the cascade — it sets the thresholds that the cascade uses. This design preserves the hard-won mechanical intervention while improving the judgment about when intervention is appropriate.

---

## What This Does NOT Do

- **Does not make the supervisor permissive.** A 43-turn genuine loop (Session 049) is still a 43-turn genuine loop. No success profile will show p90 anywhere near 43 failures. The circuit breaker still exists. The max() guards ensure thresholds never drop below 3/6/9. What changes is the sensitivity to short iteration cycles (3-8 failures), not the response to pathological loops.

- **Does not replace deterministic enforcement with model judgment.** Phases 1-3 are entirely deterministic. Phase 4 adds a model-based *recommendation* that feeds into the deterministic system. The model never fires a tier directly. The model never injects messages into the agent's context. The mechanical enforcement remains mechanical. This is "informed thresholds," not "AI-powered supervision."

- **Does not require the parallel process to ship.** Directions A, B, C, and D deliver meaningful improvement as deterministic-only enhancements. The parallel supervisor (Phase 4) is the long-term architecture. It can ship when LM Studio's concurrent inference is validated and the success profile store has accumulated enough data to be useful. In the meantime, Phases 1-3 fix the immediate false positive problem.

- **Does not try to understand WHY the agent is stuck.** Root cause analysis is a separate concern handled by error comprehension and the anti-pattern system. The adaptive supervisor determines WHETHER the agent is stuck (or making productive progress). This is the distinction between diagnosis and monitoring. An ICU monitor tells you the patient's vitals are abnormal. It doesn't tell you why. The doctor diagnoses. The monitor watches.

- **Does not learn from operator behavior in real time.** The sleep consolidation architecture (Phases 1-3 deployed) handles operator interaction modeling. The adaptive supervisor learns from task completion patterns. These are complementary systems that inform different aspects of the agent's operation. The adaptive supervisor does not model the operator's supervision style — that's the sleep consolidation system's domain.

---

## Open Questions

1. **How does the success profile capture mechanism determine task boundaries?** The current agent loop doesn't explicitly mark "task start" and "task end." The BST classification changes when the domain shifts, which could serve as a proxy. But what about multi-phase tasks where the domain stays constant? Need to audit the BST reclassification frequency to determine if domain shifts are a reliable task boundary signal.

2. **Should the parallel supervisor use the same model as the agent, or a different model?** Using the same Qwen3.5-27B avoids loading a second model. But the AI control literature found that using the *same* model for both agent and monitor can create correlated failures — the monitor fails in the same ways as the agent. A smaller model (Qwen2.5-14B-Instruct, already loaded as the current supervisor) might be better despite lower capability, because its failure modes are independent. Need to test both configurations.

3. **How does the success profile store interact with the flat FAISS store vs. the planned memU hierarchical upgrade?** Success profiles are structured data (not embeddings) and should probably live in a JSON file or SQLite rather than in the vector store. But they should be queryable by the same procedural memory interface that the anti-pattern store uses. Need to determine whether the anti-pattern store uses FAISS or a separate structure, and mirror that.

4. **What is the minimum viable success profile dataset?** The `MIN_OBSERVATIONS = 3` threshold is a guess. With too few observations, the EWMA is volatile. With too many required, the system takes too long to start adapting. This needs empirical testing: run the agent through a set of tasks, capture success profiles, and measure how quickly the p50/p90 estimates stabilize.

5. **Can the parallel supervisor's check interval be adaptive?** During a high-error-diversity debugging session, the supervisor might want to check less frequently (the agent is clearly iterating). During a low-diversity session, it might want to check more frequently. An adaptive check interval based on the progress signals would reduce unnecessary inference calls while maintaining responsiveness when the pattern changes.

6. **How does the success profile handle domain evolution?** The BST domain taxonomy might change as new domains are added. Success profiles keyed to old domains would become orphaned. Need a migration strategy — either profiles are keyed to domain families (stable) or they're re-keyed when taxonomy changes (complex).

7. **Does LM Studio's concurrent inference introduce latency on the agent's primary inference?** If both the agent and the parallel supervisor are competing for GPU resources, the agent's response time might degrade during supervisor checks. Need to benchmark: measure agent inference latency with and without concurrent supervisor inference. If latency impact exceeds 20%, consider running the supervisor during the agent's tool execution time (when the GPU is idle) rather than during inference.

---

## Recommended Sequence

1. **Audit current loop detection (empirical, today).** Read `_50_supervisor_loop.py`. Map the exact data flow from `_detect_loop()` and `_get_loop_metrics()` to the tier escalation decision. Confirm that the architectural mismatch Kestrel identified is exactly as described. Determine which function the tier system actually calls.

2. **Implement Direction B — error diversity gate (today).** Wire `_detect_loop()` to the tier escalation path. Validation: replay the GitHub skill debugging session trace. Tier 2 should not fire when error diversity is high. Replay the Session 049 loop trace. Tier 2 should fire normally when errors are identical.

3. **Implement Direction A — domain-aware thresholds (today).** Read the BST domain from `ctx["bst_domain"]` and select the threshold profile. Validation: confirm that a `codegen` task uses 6/12/18 thresholds while a `research` task uses 3/6/12.

4. **Implement Direction C — progress signal assessment (this week, requires reasoning state extension).** Read the reasoning state to compute interleaved successes and error similarity. Apply the iteration cooldown multiplier when the agent is iterating. Validation: simulate a debugging sequence with interleaved file reads. Confirm that the cooldown suppresses escalation.

5. **Design and implement success profile capture (this week).** Create the success profile data structure. Implement the post-task capture hook. Store profiles in the same directory as anti-patterns. Validation: run 5 codegen tasks to completion. Confirm that p50/p90 estimates are computed and that the supervisor reads them before selecting thresholds.

6. **Test success profile integration with threshold selection (next sprint).** Run the agent through a variety of task types. Confirm that success profiles accumulate and that thresholds adapt. Confirm that the max() guards prevent thresholds from dropping below baseline. Measure the false positive rate for tier escalation before and after — this is the primary success metric.

7. **Benchmark LM Studio concurrent inference (when Phases 1-3 are stable).** Measure agent inference latency with and without a concurrent supervisor call. Determine whether temporal exclusion (supervisor runs during tool execution) is necessary to avoid latency impact.

8. **Implement parallel supervisor process (when benchmark results are satisfactory).** Build the compressed context constructor. Configure the supervisor prompt. Integrate the recommendation into the tier system. Validation: run the GitHub skill debugging trace with the parallel supervisor active. The supervisor should recommend HOLD throughout (high error diversity, iterating). Run the Session 049 loop trace. The supervisor should recommend ESCALATE within 2 check intervals (low error diversity, no iteration).

---

*This design note bridges the Loop Feedback Cascade (Session 049) with the sleep consolidation architecture (Session 057) and the PACE/Reasoning State design (Session 057). The loop cascade provides the intervention mechanism. The sleep consolidation provides the learning-over-time infrastructure. The PACE system provides the strategy-level awareness. The adaptive supervisor sits at the intersection: it uses data from all three systems to make better decisions about when to intervene and when to let the agent work.*

*Jake's framing — "a supervisor that learns alongside the agent" — is not a metaphor. It is a literal description of the architecture: a system that captures success patterns alongside failure patterns, develops domain-specific baselines through experience, and evaluates the agent's current work against those baselines rather than against fixed thresholds. The parallel process architecture adds one more dimension: the observer's judgment is structurally separated from the actor's investment, preventing the Einstellung effect from contaminating the oversight process.*

*The anti-pattern system already makes the supervisor smarter about failure over time. The success profile system makes it smarter about success over time. The parallel process makes it smarter about the difference between the two. All three changes are required. None alone is sufficient.*
