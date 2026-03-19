# Adaptive Supervisor Phase 4: Parallel Inference Architecture

**Purpose:** Implementation spec for the Phase 4 parallel LLM call. Answers: which model, what interface, what return contract, what latency budget.

**Audience:** Kestrel (builder)
**Written:** Session 059, March 18, 2026
**Depends on:** ADAPTIVE_SUPERVISOR_PHASE4_FIELD_EVIDENCE.md (what to detect), ADAPTIVE_SUPERVISOR_DESIGN_NOTE.md (overall architecture)

---

## 1. The Core Question

Phase 4 needs a separate LLM call with its own compressed context window (~300-500 tokens), independent of the agent's context. The existing `_50_supervisor_loop.py` is purely deterministic — no LLM calls. Phase 4 adds exactly one LLM call per evaluation cycle, with structured output.

---

## 2. Model Selection

### Primary: Qwen3.5-Opus-4.6 Distill (27B)
- **Pro:** Already the main agent model, loaded in LM Studio, proven across the project
- **Pro:** Distilled from Opus reasoning chains — the model has exposure to the analytical classification patterns Phase 4 requires. The named failure patterns in the system prompt align with reasoning structures the distill was trained on.
- **Pro:** Known to produce structured output reliably (BST profiles, agent_staging.md, Counter-Patriots build all demonstrated this)
- **Con:** 27B model for a ~500 token input is heavy — but the call is infrequent
- **Con:** If the distill is actively running agent inference, LM Studio may serialize the supervisor call. See Open Questions §9.

### Fallback: GLM-4-Flash (utility model)
- **Pro:** Fast, lightweight, already configured in the stack
- **Pro:** Sufficient for the classification task if the distill is unavailable or serialization causes latency issues
- **Con:** No Opus reasoning chain exposure — may need a more explicit system prompt

### Recommendation: Qwen3.5-Opus-4.6 Distill as primary, GLM-4-Flash as fallback

Rationale: The distill model's training on Opus reasoning chains is a genuine advantage for Phase 4. The supervisor task — recognizing strategic failure patterns from compressed context — is exactly the kind of analytical classification the distill has demonstrated competence at (BST self-configuration, identity evaluation, staging document creation). The call is infrequent, so even if LM Studio serializes it between agent turns, the 2-4 second latency is acceptable at the `message_loop_end` hook (which fires between turns, not mid-generation).

The model choice is a configuration parameter, not hardcoded. Kestrel should implement the call against a configurable endpoint so we can swap models without code changes.

---

## 3. Interface: Direct HTTP to LM Studio API

### Why not `self.agent`

The agent's LLM interface (`self.agent`) carries the agent's full context, system prompt, personality, and conversation history. Phase 4's entire purpose is context separation — the supervisor must NOT see the agent's full context. Using `self.agent` would defeat the design.

### Implementation

Direct HTTP POST to LM Studio's OpenAI-compatible API endpoint. This is the same interface the BST and other extensions could use for utility calls.

```python
import aiohttp
import json

SUPERVISOR_LM_ENDPOINT = "http://host.docker.internal:1234/v1/chat/completions"
SUPERVISOR_MODEL = "qwen3.5-opus-4.6-distill"  # configurable
SUPERVISOR_MAX_TOKENS = 150
SUPERVISOR_TEMPERATURE = 0.0  # deterministic output

async def _call_phase4_supervisor(self, compressed_context: str) -> dict:
    """
    Fire a parallel LLM call with compressed context only.
    Returns structured supervisor recommendation.
    """
    system_prompt = PHASE4_SYSTEM_PROMPT  # see Section 5
    
    payload = {
        "model": SUPERVISOR_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": compressed_context}
        ],
        "max_tokens": SUPERVISOR_MAX_TOKENS,
        "temperature": SUPERVISOR_TEMPERATURE,
        "response_format": {"type": "json_object"}  # if supported by model
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SUPERVISOR_LM_ENDPOINT,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)  # hard timeout
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return _parse_supervisor_response(data)
                else:
                    # LM Studio unavailable — fall back to deterministic-only
                    return {"action": "HOLD", "reason": "supervisor_unavailable"}
    except Exception:
        # Network error, timeout, etc. — never block the agent
        return {"action": "HOLD", "reason": "supervisor_error"}
```

### Key implementation details

1. **`host.docker.internal`** — LM Studio runs on the host, Agent Zero runs in Docker. This is the standard Docker bridge address. Same pattern used for existing LM Studio connections.

2. **Hard timeout of 10 seconds.** If the supervisor LLM doesn't respond in 10 seconds, return HOLD and let the agent continue. Phase 4 must never block the agent's execution loop. The deterministic Phases 1-3 remain the backstop.

3. **Graceful degradation.** If LM Studio is down, model isn't loaded, network fails, or response is unparseable — always return HOLD. Phase 4 is additive. The system works without it (that's Phases 1-3). It should never make things worse.

4. **No retry logic.** If the call fails, it fails. The next evaluation cycle will try again. Retrying inside the supervisor hook adds latency and complexity for minimal benefit.

---

## 4. Return Contract

### Supervisor output format

```json
{
    "action": "HOLD" | "ESCALATE" | "DEESCALATE",
    "confidence": 0.0-1.0,
    "reason": "string — one line explanation",
    "intervention": "string — specific message to inject (only if ESCALATE)",
    "pattern_matched": "string — which known pattern triggered this (optional)"
}
```

### How each action is consumed

| Action | What happens | Who acts |
|--------|-------------|----------|
| **HOLD** | No change. Agent continues normally. Phases 1-3 operate as usual. | Nothing |
| **ESCALATE** | Supervisor injects `intervention` text as a system-level message. Tier thresholds may be temporarily lowered. | Deterministic tier system |
| **DEESCALATE** | Tier thresholds return to learned/default values. Any active Tier 1 warnings are suppressed for the next N turns. | Deterministic tier system |

### Critical constraint: Phase 4 never injects messages directly

The LLM supervisor produces a recommendation. The **deterministic tier system** decides whether and how to act on it. This preserves the Exocortex principle: deterministic scaffolding over probabilistic reasoning. The LLM advises. The code enforces.

Implementation:

```python
def _apply_phase4_recommendation(self, recommendation: dict) -> None:
    """
    Translate Phase 4 LLM recommendation into deterministic tier actions.
    The LLM advises. This function enforces.
    """
    action = recommendation.get("action", "HOLD")
    confidence = recommendation.get("confidence", 0.0)
    
    if action == "HOLD":
        return  # no change
    
    if action == "ESCALATE" and confidence >= ESCALATION_CONFIDENCE_THRESHOLD:
        intervention_text = recommendation.get("intervention", "")
        if intervention_text:
            # Inject as supervisor message through existing tier system
            self._inject_supervisor_message(intervention_text, tier="phase4")
        # Optionally lower tier thresholds temporarily
        self._adjust_thresholds(direction="lower", duration_turns=3)
        
    if action == "DEESCALATE" and confidence >= DEESCALATION_CONFIDENCE_THRESHOLD:
        self._adjust_thresholds(direction="restore")
        self._suppress_warnings(duration_turns=2)
```

The `ESCALATION_CONFIDENCE_THRESHOLD` should start at 0.7 and be tuned empirically. Too low = false positives (supervisor interferes with productive work). Too high = misses real strategic loops. Start conservative, lower as we build trust in the supervisor's judgment.

---

## 5. System Prompt for Phase 4 Supervisor

This is the entire context the supervisor LLM sees. Nothing else. No agent history, no conversation, no tool outputs.

```
You are a supervisor monitoring an AI agent's execution. You receive a compressed 
status report and must decide whether to intervene.

Your options:
- HOLD: Agent is working normally. No intervention needed.
- ESCALATE: Agent is stuck in a strategic pattern it cannot break itself. 
  Provide a specific intervention message.
- DEESCALATE: Agent has recovered from a previous issue. Restore normal thresholds.

Known failure patterns to watch for:

1. RESEARCH_AFTER_CONFIRMATION: Agent re-enters information-gathering mode after 
   operator has confirmed the task. Signal: operator_confirmations > 0 AND 
   productive_output = 0 AND agent is reading/researching.

2. STRATEGY_REPETITION: Multiple attempts fail for the same root cause despite 
   surface-level variation. Signal: blocking_factors show the same root cause 
   across 3+ attempts, even if error types differ.

3. MACRO_CYCLE: Agent repeats a multi-step behavioral cycle (research → propose → 
   ask → research) after the cycle was already completed and confirmed. Signal: 
   same strategy_hash appears twice with operator confirmation between them.

4. SELF_DIAGNOSIS_WITHOUT_CHANGE: Agent correctly identifies it is stuck but then 
   re-enters the same pattern. Signal: agent_self_diagnosis = present AND 
   followed_by_change = no.

Respond with a JSON object containing: action, confidence (0-1), reason, 
intervention (if escalating), pattern_matched (if applicable).

If you are uncertain, choose HOLD. False negatives (missing a real problem) are 
better than false positives (interfering with productive work).
```

### Why this prompt works

- **No agent context.** The supervisor sees the compressed report, not the conversation. It can't develop Einstellung because it never reads the agent's reasoning.
- **Named patterns.** The four patterns from the field evidence are explicitly listed. The supervisor doesn't need to discover them — it needs to recognize them. This is classification, not reasoning.
- **Conservative default.** "If uncertain, HOLD" prevents the supervisor from becoming a source of interference. The worst-case failure mode is doing nothing, which is identical to not having Phase 4.
- **Structured output.** JSON format with named fields makes parsing deterministic. If the model produces malformed JSON, the fallback is HOLD.

---

## 6. When Phase 4 Fires

Phase 4 should NOT fire every turn. The LLM call has latency cost (~2-4 seconds) and should only trigger when there's reason to believe strategic-level evaluation is needed.

### Trigger conditions (any one sufficient)

1. **Failure count ≥ 2 AND Phases 1-3 have not escalated.** The deterministic system sees failures accumulating but hasn't reached its own thresholds. Phase 4 evaluates whether the pattern warrants earlier intervention.

2. **Loop detector has fired in the current session.** If the tactical detector already caught one loop, the probability of strategic looping is elevated. Phase 4 evaluates the broader pattern.

3. **Operator has provided 2+ confirmations for the same task without productive output.** Direct signal of the Research After Confirmation pattern.

4. **BST momentum ≥ 5 in any single classification.** Extended momentum without momentum break suggests the agent is deep in a single mode. Phase 4 evaluates whether that's productive focus or fixation.

5. **Manual trigger.** Operator can force a Phase 4 evaluation via a command or signal. Useful during testing.

### Non-trigger (Phase 4 stays silent)

- First 3 turns of any task (let the agent orient)
- Agent is actively producing output (code, documents, tool results succeeding)
- Phase 1-3 have already escalated to Tier 2+ (the deterministic system is already handling it)

---

## 7. Logging

Every Phase 4 call should be logged for sleep consolidation and tuning:

```python
phase4_log = {
    "timestamp": datetime.utcnow().isoformat(),
    "compressed_context": compressed_context,  # what the supervisor saw
    "recommendation": recommendation,           # what it recommended
    "action_taken": actual_action,              # what the deterministic system did
    "agent_behavior_next_turn": None,           # filled in retrospectively
    "operator_correction_within_3_turns": None  # filled in by sleep consolidation
}
```

The retrospective fields (`agent_behavior_next_turn`, `operator_correction_within_3_turns`) are filled during sleep consolidation. They enable calibration: did the supervisor's recommendation actually help? Did the operator correct the agent shortly after Phase 4 chose HOLD? Over time, this log trains the system's understanding of when to escalate.

---

## 8. Build Order

1. **Compressed context builder.** Function that assembles the ~500 token context from existing Phase 1-3 signals, BST state, tool history, and operator interaction log. This is the prerequisite — Phase 4 is only as good as the context it receives.

2. **HTTP call wrapper.** The `_call_phase4_supervisor()` function with timeout, graceful degradation, and JSON parsing. Test with a mock endpoint first before pointing at LM Studio.

3. **Recommendation consumer.** The `_apply_phase4_recommendation()` function that translates LLM output into deterministic tier actions. Keep this simple — HOLD does nothing, ESCALATE injects a message, DEESCALATE restores thresholds.

4. **Trigger logic.** The conditions from Section 6, integrated into the existing `_50_supervisor_loop.py` evaluation cycle. Phase 4 check runs after Phases 1-3 have computed their signals.

5. **Logging.** The Phase 4 log structure for sleep consolidation integration.

6. **System prompt tuning.** Run the four field cases through the supervisor manually (compose the compressed context by hand, send to LM Studio, check the output). Verify it produces ESCALATE for the three known-bad cases before deploying in the loop.

---

## 9. Open Questions

1. **Concurrent inference on LM Studio with 3090.** The Qwen3.5-Opus-4.6 distill (27B) is the agent's primary model. If the supervisor call fires during `message_loop_end` (between turns), LM Studio should handle it as a sequential request with no conflict. If for any reason the call needs to fire during agent inference, LM Studio may serialize or queue. Need to test whether this adds latency. If it does, the GLM-4-Flash fallback avoids the contention entirely since it's a different model.

2. **Context format validation.** The compressed context format from the field evidence addendum (Section 6) should be tested empirically — does the supervisor LLM actually produce good ESCALATE/HOLD decisions from that format? May need iteration on which fields are most informative.

3. **Threshold for firing frequency.** If Phase 4 fires too often, the 2-4 second latency per call adds up. Start with conservative triggers and loosen based on false negative rate (cases where Phase 4 should have fired but didn't, identified during sleep consolidation review).

---

*This spec covers the "how." The field evidence addendum covers the "what" and "why." The original design note covers the "where it fits." Together, these three documents should be sufficient for Kestrel to build Phase 4.*
