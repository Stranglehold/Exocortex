# Proactive Reasoning-Stream Supervisor
## Design Note — Pre-Spec Exploration

**Status:** Pre-spec exploration. Informed by: Agent Zero v1.6 reasoning_stream hooks (Kestrel reconnaissance, 2026-03-31), world models research thread (JEPA/GRASP/stable-worldmodel analysis, Session 061), claw-code harness analysis (pre-dispatch pattern extraction), 13-hour-45-minute autonomous agent run (operational validation). No eval data on reasoning-stream analysis yet — Kestrel's 6-turn test provides initial observations only. This document sketches the architecture for a supervisor that reads the model's thinking before output commitment and intervenes based on learned reasoning dynamics.

**Authors:** Opus (architecture), informed by Kestrel (v1.6 reconnaissance + claw-code analysis), Jake (world models research direction)
**Date:** 2026-03-31

---

## 1. The Problem

### The Gap

The Exocortex supervises the agent's **outputs** — what it says, what tools it calls, what files it writes. The supervisor fires at `message_loop_end`, after the model has generated its response, after the tool has been parsed, after the tool has executed. Every intervention is reactive: the bad turn has already happened, and the supervisor corrects the next turn.

What the Exocortex has never had access to is the model's **reasoning** — the thinking that precedes the output. The model considers a tool, evaluates alternatives, recognizes (or fails to recognize) a loop, commits to an action. All of this happens inside the generation, invisible to every Exocortex layer. The BST classifies the input domain. The action boundary gates the tool call. The supervisor detects loops in the output history. None of them see the reasoning that produced the output.

Agent Zero v1.6 changes this. The new `reasoning_stream` hook family fires during and after the model's thinking phase, before output is committed to the tool pipeline. For the first time, the Exocortex can observe the model's reasoning in real time.

### The Motivating Incidents

**Incident 1: The 941-loop subordinate chain (Session 061).** The intelligence briefing skill's original five-level subordinate chain produced 941 loop detections and 43 context compressions. The loops were visible in the output (repeated tool calls) but the reasoning that produced them — the model's decision to spawn another subordinate despite already being five levels deep — was invisible. A reasoning-stream supervisor could have detected "the model is considering call_subordinate for the fourth recursive time" and intervened before the call was dispatched.

**Incident 2: The generation lock mechanism (Loop Recovery Design Note).** Kestrel's analysis identified the generation lock as mechanistic — self-reinforcement + positional de-emphasis + attention sink amplification. The lock forms in the model's internal state before it manifests in the output. By the time the supervisor detects the loop in the output history, the lock has been reinforced for multiple turns. A reasoning-stream supervisor could detect the lock's precursors — repeated analytical sentences, escalating deliberation length, circular consideration of the same tool — before the output confirms the loop.

**Incident 3: Kestrel's v1.6 test observations.** On a clean v1.6 container with Qwen3.5-27B, the model explicitly named a loop trap in its reasoning ("this appears to be either a test or an attempt to get me into a repeated failure loop") and refused to enter it — all before generating output. The reasoning stream contains the model's actual epistemic state. When the model recognizes a trap, that recognition is visible in the reasoning. When the model fails to recognize a trap, the failure pattern (repeated consideration of the same approach, escalating paragraph count, circular analysis) is also visible. Both the success and the failure mode leave traces in the reasoning.

### The Analogy: Pre-Dispatch vs Pre-Execution

Kestrel's analysis of the claw-code harness identified a key architectural pattern: Claude Code runs permission checks at **routing time** (before dispatch), not at **execution time** (before the tool runs). The current Exocortex action boundary runs at `tool_execute_before` — pre-execution. The reasoning-stream supervisor would run at `reasoning_stream_end` — which fires after generation but BEFORE `process_tools()`. This is the closest to pre-dispatch timing available without modifying Agent Zero's core. The tool call has been generated but not yet parsed or dispatched. The intervention window is between generation and dispatch — exactly where the claw-code pattern places it.

### Connection to World Models Research

The world models research thread (Session 061) identified a unifying principle: **prediction error is the universal anomaly signal.** Any system that can learn normal dynamics can detect anomalies by measuring divergence from prediction. The reasoning stream provides the data for learning reasoning dynamics: what does normal reasoning look like for a given task class? How long is it? What tools does it consider? How many alternatives does it evaluate before committing?

A learned model of reasoning dynamics turns the proactive supervisor from a pattern-matcher (regex on reasoning text) into a prediction-error detector (the reasoning diverges from what the dynamics model expects for this task class). Pattern matching catches known failure modes. Prediction error catches novel failure modes — reasoning patterns the system has never seen before, which are surprising precisely because they're unlike anything in the training data.

This design note describes both layers: the pattern-matching baseline (buildable now) and the dynamics-model enhancement (buildable once behavioral traces accumulate).

---

## 2. Design Principles

**1. Deterministic analysis, no LLM calls.** The reasoning stream is analyzed by regex, string similarity, and statistical thresholds — never by a second LLM call. The proactive supervisor must be faster than the model's generation speed to be useful; an LLM call would be slower than the thing it's supervising.

**2. Pre-dispatch timing, flag-then-inject pattern.** The supervisor sets flags at `reasoning_stream_end` (after generation, before tool dispatch). Flags are read at `before_main_llm_call` (next turn) and converted to targeted context injections. The current turn's tool call proceeds — we cannot stop it from the hook — but the next turn is informed by the reasoning analysis.

**3. Layer coordination with existing supervisor.** The proactive supervisor and the reactive supervisor (`_50_supervisor_loop`) must not double-handle the same loop. When the proactive supervisor fires, it sets a coordination flag. The reactive supervisor checks this flag and defers when the proactive supervisor has already intervened. The reactive supervisor remains as fallback for cases the proactive supervisor misses.

**4. Reasoning privacy in output.** The intervention text never quotes the model's reasoning directly. The reasoning stream is the model's internal workspace. Referencing it in the output context ("I noticed you considered X three times in your thinking") creates a metacognitive burden and may destabilize generation. Interventions are task-oriented: "Alternative approaches for this task include..." without revealing how the supervisor knows alternatives are needed.

**5. Progressive intelligence.** Phase 1 uses deterministic pattern matching on the reasoning text. Phase 2 adds a learned calibration model (BST domain → expected reasoning profile). Phase 3 adds a world-model-style dynamics predictor trained on accumulated behavioral traces. Each phase is additive — the pattern matcher remains as a fast baseline, the calibration model adds task-aware thresholds, the dynamics predictor catches novel anomalies. The infrastructure (hooks, flags, injection mechanism) is built once and serves all three phases.

**6. Reasoning as epistemic evidence.** The reasoning stream feeds the Epistemic Integrity layer. The model's stated confidence in the output (`thoughts` field) can be compared against its actual confidence in the reasoning (uncertainty language, hedging, explicit doubt). The gap between reasoning-confidence and output-confidence is itself a signal worth tracking.

---

## 3. Architecture

### Extension: `_12_proactive_supervisor.py`

Numbered at 12 to fire before `_15_action_boundary` (which gates tool execution) and well before `_50_supervisor_loop` (which detects loops in output history). The proactive supervisor is the earliest analytical layer in the pipeline.

### Hook Points

```
reasoning_stream        → accumulate reasoning text into buffer
reasoning_stream_end    → analyze buffer, set typed flags, feed EI layer
before_main_llm_call    → read flags from previous turn, inject corrections
```

### Data Flow

```
┌──────────────────────────────────────────────────────────┐
│ LLM generates reasoning tokens                           │
│   ↓ (per-chunk)                                          │
│ reasoning_stream hook                                    │
│   → accumulate text into _rs_buffer (agent.set_data)     │
│                                                          │
│   ↓ (generation complete)                                │
│ reasoning_stream_end hook                                │
│   → ANALYZE _rs_buffer against signal classes             │
│   → COMPARE against calibration model (Phase 2+)         │
│   → SET typed flags: _proactive_signal_type               │
│   → SET coordination flag: _proactive_fired_this_turn     │
│   → STORE reasoning summary in EI evidence buffer         │
│   → STORE reasoning in cross-turn buffer (last N turns)   │
│                                                          │
│   ↓                                                      │
│ process_tools() — tool call dispatched                    │
│   ↓                                                      │
│ _15_action_boundary (tool_execute_before)                │
│   ↓                                                      │
│ [TOOL EXECUTES]                                          │
│   ↓                                                      │
│ _50_supervisor_loop (message_loop_end)                   │
│   → CHECK _proactive_fired_this_turn                     │
│   → IF TRUE: defer (proactive already handled)           │
│   → IF FALSE: run normal loop detection                  │
│                                                          │
│   ↓ [NEXT TURN]                                          │
│ before_main_llm_call hook                                │
│   → READ _proactive_signal_type from previous turn       │
│   → IF signal present: INJECT targeted correction block  │
│   → CLEAR flags for new turn                             │
└──────────────────────────────────────────────────────────┘
```

### Signal Classes

Five signal classes, adapted from Kestrel's reconnaissance with detection mechanisms specified:

```python
@dataclass
class ReasoningSignal:
    signal_class: str       # "repeated_sentence", "repeated_tool", "self_reference_loop",
                            # "hedge_without_commit", "excessive_deliberation"
    severity: float         # 0.0–1.0
    evidence: str           # brief description for logging (not injected into context)
    suggested_redirect: str # task-oriented intervention text
```

**Signal Class 1: Repeated Sentence Patterns**
Same analytical sentence appears 2+ times in reasoning. Detection: pairwise string similarity across paragraph segments. Threshold: >80% similarity for sentences >20 chars. Severity: 0.4 per repetition above 1.

**Signal Class 2: Repeated Tool Consideration**
Same tool name mentioned 3+ times in reasoning with action verbs. Detection: regex count of `(?:call|use|run|try|execute)\s+(\w+_tool|call_subordinate)` patterns. Severity: 0.3 per mention above 2. Highest severity for `call_subordinate` repetition (subordinate depth risk).

**Signal Class 3: Self-Reference Loop**
Model references its own previous attempt ("I already tried", "as I mentioned", "I said earlier") more than twice. Detection: regex for self-reference phrases. Severity: 0.5 — this indicates the model is aware it's repeating but hasn't changed strategy.

**Signal Class 4: Hedge Without Commit**
Multiple conditional constructions ("maybe I should", "I could try", "perhaps") without a clear commitment sentence ("I will", "The answer is"). Detection: ratio of hedge phrases to commitment phrases. Severity: 0.3 when hedge:commit ratio > 3:1.

**Signal Class 5: Excessive Deliberation**
Reasoning length significantly exceeds expected length for the task class. Detection: Phase 1 uses static thresholds (>1500 chars for BST utility, >3000 chars for BST analytical). Phase 2 uses learned calibration from behavioral traces.

### Intervention Text Templates

Interventions are task-oriented and never reference reasoning content:

```python
INTERVENTIONS = {
    "repeated_tool": (
        "[SUPERVISOR: STRATEGY SHIFT RECOMMENDED]\n"
        "The current approach may not be producing results. "
        "Alternative tools for this task type: {alternatives}. "
        "If the task cannot be completed with available tools, "
        "report what you have and explain the limitation."
    ),
    "repeated_sentence": (
        "[SUPERVISOR: PROGRESS CHECK]\n"
        "Ensure each turn produces measurable progress toward the goal. "
        "If the current approach is blocked, try a different angle or "
        "report the blocking condition."
    ),
    "self_reference_loop": (
        "[SUPERVISOR: APPROACH CHANGE REQUIRED]\n"
        "Previous approach has been attempted. Do not retry the same method. "
        "Choose a fundamentally different strategy or report that the task "
        "cannot be completed with current resources."
    ),
    "hedge_without_commit": (
        "[SUPERVISOR: COMMIT TO ACTION]\n"
        "Select the most promising approach and execute it. "
        "If uncertain between options, choose the simplest one first."
    ),
    "excessive_deliberation": (
        "[SUPERVISOR: SIMPLIFY]\n"
        "This task may be simpler than current analysis suggests. "
        "Commit to the most direct approach. Elaborate only if the "
        "direct approach fails."
    ),
}
```

### Configuration

```json
{
    "proactive_supervisor": {
        "enabled": true,
        "reasoning_buffer_turns": 5,
        "signal_thresholds": {
            "repeated_sentence_similarity": 0.80,
            "repeated_tool_count": 3,
            "self_reference_count": 2,
            "hedge_commit_ratio": 3.0,
            "excessive_deliberation_chars": {
                "utility": 1500,
                "analytical": 3000,
                "code": 2500,
                "creative": 2000,
                "default": 2000
            }
        },
        "severity_threshold_for_intervention": 0.4,
        "suppress_reactive_supervisor_on_fire": true,
        "feed_ei_evidence_buffer": true,
        "log_reasoning_summary": true,
        "log_full_reasoning": false
    }
}
```

### Coordination with Existing Layers

| Layer | Current Timing | Interaction |
|---|---|---|
| `_08_bst_classifier` | `before_main_llm_call` | Proactive supervisor reads BST domain to calibrate deliberation thresholds |
| `_10_orientation_stack` | `before_main_llm_call` | Proactive supervisor injection is ADDITIONAL to orientation injection — both fire at same hook |
| `_12_proactive_supervisor` | `reasoning_stream_end` + `before_main_llm_call` | **NEW** — this design note |
| `_15_action_boundary` | `tool_execute_before` | Unaffected — action boundary gates tool execution, proactive supervisor gates reasoning quality. Different concerns, different timing |
| `_50_supervisor_loop` | `message_loop_end` | Checks `_proactive_fired_this_turn` flag. Defers if proactive supervisor already intervened. Fires normally otherwise |
| `_60_epistemic_integrity` | `message_loop_end` | Receives reasoning summary from proactive supervisor. Compares reasoning-confidence against output-confidence for gap analysis |

### Epistemic Integrity Integration

The reasoning stream provides the model's pre-commitment epistemic state. Two new checks for the EI layer:

**Confidence gap detection:** Compare uncertainty language in reasoning ("I'm not sure", "this might be", "I think") against certainty language in output ("The answer is", stated facts without hedging). A high confidence gap — uncertain in reasoning, certain in output — flags the claim as potentially ungrounded. The model knew it was unsure but presented the output as confident.

**Reasoning-output consistency:** Compare the approach decided in reasoning against the tool actually called. If the reasoning says "I'll use search_engine to verify" but the output calls `response` without searching, the model abandoned its own plan. This may indicate the model was correct in its reasoning (should have searched) but was pulled toward a faster completion by generation dynamics.

Both checks are deterministic — string matching on uncertainty/certainty phrases and comparison of tool names in reasoning vs output.

---

## 4. Phase Progression

### Phase 1: Pattern Matching Baseline (Build Now)

The five signal classes with static thresholds. Regex-based detection. Flag-then-inject intervention. Coordination with reactive supervisor. EI integration for confidence gap detection.

**What this catches:** Known loop patterns (repeated tools, repeated sentences, excessive deliberation), hedge spirals, and self-reference loops. The patterns Kestrel observed in v1.6 testing.

**What this misses:** Novel loop patterns that don't match any signal class. Subtle reasoning degradation that doesn't trigger static thresholds. Cross-turn reasoning drift where each individual turn looks fine but the trajectory across turns is circular.

**Estimated build time:** 1-2 days for Kestrel. The hook infrastructure is new but the analysis patterns are adapted from the existing supervisor's detection logic.

### Phase 2: Learned Calibration Model (Build After Trace Collection)

Replace static thresholds with a simple regression model: BST domain + task complexity → expected reasoning profile (length, tool consideration count, hedge ratio, paragraph count). The model trains on behavioral traces collected during Phase 1 operation.

**What this adds:** Task-aware thresholds. A greeting task that produces 1500 chars of reasoning is anomalous. A research task that produces 1500 chars is normal. The calibration model knows the difference because it learned from operational data.

**Training data requirement:** ~100-200 turns with BST classification + reasoning metrics + outcome (success/failure/loop). At the agent's operational pace, this is 2-3 weeks of normal use.

**What this misses:** Novel task types not represented in training data. Reasoning patterns that are normal in length and structure but wrong in content.

### Phase 3: World-Model Dynamics Predictor (Build After Phase 2 Validation)

Train a small world model (stable-worldmodel framework) on reasoning trace sequences: given the last N reasoning profiles (length, tool considerations, hedge ratio, BST domain, outcome), predict the next reasoning profile. Anomaly detection via prediction error — when the actual reasoning diverges from the predicted reasoning, something unusual is happening.

**What this adds:** Detection of novel failure modes. The dynamics model doesn't know what specific failure patterns look like — it knows what normal reasoning dynamics look like, and anything that deviates from normal is flagged. This is the violation-of-expectation paradigm from LeWM applied to reasoning supervision.

**Connection to GRASP:** The parallel planning insight suggests monitoring multiple possible reasoning trajectories simultaneously. If the dynamics model predicts two or three plausible next-reasoning-profiles, and the actual reasoning matches none of them, the surprise is higher than if it matches one of three. Multiple predictions with consistency constraints, exactly as GRASP maintains multiple virtual states.

**Training data requirement:** ~500-1000 turns with full reasoning profiles and outcomes. Phase 2's calibration model provides the baseline; Phase 3 adds temporal dynamics (how reasoning patterns evolve across turns within a session, not just per-turn statistics).

---

## 5. v1.6 Migration Integration

The proactive supervisor is built simultaneously with the v1.6 migration. The migration provides the hooks. The supervisor provides the value.

### Migration Checklist (Kestrel)

- [ ] Move all extensions from `extensions/<hook>/` to `extensions/python/<hook>/`
- [ ] Update tool deployment paths: `/a0/python/tools/` → `/a0/tools/`
- [ ] Update helper deployment paths: `/a0/python/helpers/` → `/a0/helpers/`
- [ ] Update `MISFORMAT_SIGNAL` to match v1.6: `"You have misformatted your message"`
- [ ] Deploy REPEAT_SIGNAL patch to v1.6 container
- [ ] Deploy plain-text fallback patch to new helpers path
- [ ] Switch to `a0_small` system prompt profile
- [ ] Build `_12_proactive_supervisor.py` with Phase 1 signal classes
- [ ] Add behavioral trace logger (JSONL: BST domain, reasoning metrics, tool called, outcome per turn)
- [ ] Update `install_all.sh` for new paths
- [ ] Run the 6-turn test suite from Kestrel's brief to verify parity
- [ ] Run extended session (1+ hour) with proactive supervisor active, measure: false positive rate, intervention frequency, coordination with reactive supervisor

### Acceptance Criteria

1. Proactive supervisor detects at least one known loop pattern (Signal Class 2: repeated tool consideration) in controlled testing
2. Reactive supervisor correctly defers when proactive supervisor has fired
3. EI layer receives and uses reasoning confidence data
4. Behavioral trace logger produces valid JSONL for every turn
5. No increase in false-positive supervisor interventions during normal (non-looping) operation
6. `a0_small` profile produces no regression in task completion quality

---

## 6. Open Questions

**Q1: Reasoning token visibility for the model.** Does the model see its own previous reasoning tokens in the conversation history, or are they stripped? If the model sees them, cross-turn reasoning comparison happens naturally (the model can reference its own prior thinking). If they're stripped, the proactive supervisor's cross-turn buffer is the only source of reasoning history. Kestrel to verify from v1.6 conversation history structure.

**Q2: Reasoning length as a function of model temperature.** The ATLAS Ralph Loop escalates temperature on retry. If we adopt temperature escalation as a Tier 1 loop intervention, does increased temperature also increase reasoning length? If so, the excessive deliberation threshold needs temperature adjustment. Phase 2's calibration model could include temperature as an input variable.

**Q3: Attention entropy exposure from llama.cpp.** The "Spike, Sparse, and Sink" paper describes attention patterns that precede degenerate behavior. If llama.cpp can expose per-layer attention entropy during generation, the proactive supervisor could add a sixth signal class: attention sink formation. This would be the earliest possible loop signal — detectable in the attention weights before it manifests even in the reasoning text. Research question: what is the latency cost of reading attention weights per token via llama.cpp's API?

**Q4: Qwen3.5 reasoning quality under a0_small.** The `a0_small` profile removes `main.tips`, `main.role`, and `main.specifics` sections. Does this affect the quality of reasoning (the `<think>` block content), or only the quality of the output? The reasoning may draw on system prompt context that `a0_small` removes. Test: compare reasoning content between default and `a0_small` profiles on the same prompts.

**Q5: Privacy of reasoning content in logs.** The behavioral trace logger will record reasoning metrics (length, tool mentions, hedge count) but optionally the full reasoning text. Full text is more valuable for debugging and training but may contain sensitive content (the model's uncensored assessment of a task, expressions of uncertainty the user never sees). Decision: log full reasoning to a separate file with restricted access, log only metrics to the standard behavioral trace.

---

## 7. Research Lineage

- **Agent Zero v1.6 reasoning_stream hooks** — The platform capability that enables this design. Without native separation of thinking and response tokens, reasoning analysis would require parsing `<think>` tags manually and racing against the generation pipeline.
- **Loop Recovery and Memory Surgery Design Note (Session 061)** — Identified the generation lock as mechanistic (self-reinforcement + positional de-emphasis + attention sink amplification). The proactive supervisor addresses the same failure mode one layer earlier — in the reasoning that precedes the lock, not in the output history after it.
- **ATLAS Ralph Loop (Research Ledger Entry 010)** — Temperature escalation as a cheap loop-breaking mechanism. The proactive supervisor could trigger temperature escalation as its mildest intervention before injecting correction text.
- **claw-code harness analysis (Kestrel, Session 061)** — Pre-dispatch permission checking pattern. The `reasoning_stream_end` hook fires before `process_tools()`, which is the closest to pre-dispatch timing available. Kestrel's instinct about routing-time gating pointed directly to this hook.
- **World Models Research Thread (Session 061)** — Prediction error as the universal anomaly signal. JEPA predicts in embedding space rather than raw space. LeWM detects physically implausible events via violation-of-expectation. The Phase 3 dynamics predictor applies the same paradigm to reasoning supervision — learned normal dynamics, prediction error on actual reasoning, divergence as the signal.
- **"The Spike, the Sparse and the Sink" (Sun et al. 2026)** — Anatomy of attention sinks. The mechanistic explanation for generation locks. If attention entropy is exposable from llama.cpp, it provides the sixth signal class for pre-symptomatic loop detection.
- **"Context Structure Reshapes Representational Geometry" (Hosseini et al. 2026)** — Context changes the model's internal representational geometry. The proactive supervisor's context injections don't just add information — they reshape the geometry the model reasons in. The intervention text should be designed with this in mind: the goal is to reshape the reasoning geometry away from the loop attractor, not just to add a warning message.
- **Temporal Straightening for Latent Planning (Wang et al. 2026)** — Planning works better when temporal trajectories in latent space are straight. Applied to reasoning: reasoning that makes steady progress toward a conclusion follows a "straight" trajectory in some abstract space. Reasoning that loops follows a curved or circular trajectory. The dynamics predictor in Phase 3 could potentially measure trajectory curvature as a loop indicator.

---

*This design note describes the first Exocortex layer with visibility into the model's reasoning process. The progression from pattern matching (Phase 1) through learned calibration (Phase 2) to dynamics prediction (Phase 3) mirrors the Exocortex's broader trajectory: start with deterministic infrastructure that works, then add progressively deeper intelligence as operational data accumulates. The reasoning stream is the deepest signal source the Exocortex has ever had access to. The architecture should be worthy of the signal.*

*The scaffold sees the thinking now. What it does with that sight determines the next chapter of the architecture.*
