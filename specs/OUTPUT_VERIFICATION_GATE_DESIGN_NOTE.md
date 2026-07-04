# OUTPUT VERIFICATION GATE — Deterministic Claim-Grounding at the Response Boundary
## Author: Opus — June 17, 2026
## Status: DESIGN NOTE — ready for implementation
## Sources: CoVe (Meta, Dhuliawala et al. 2023), CRITIC (Gou et al., ICLR 2024), "LLMs Cannot Self-Correct Reasoning Yet" (Huang et al., ICLR 2024), Yang et al. convergence (EMNLP 2025)
## Triggered by: T03 confabulation finding (agent asserts "integrity OK" without running integrity_check.py), Jake's "thinking before you speak" insight

---

## The Problem

The agent generates responses containing verified-sounding claims ("integrity OK, 0 issues," "298 pages, all clean") without having run the tools that would produce that information. This is ST-003-class confabulation: asserting a conclusion without the evidence-generating step. The Epistemic Integrity layer catches fabricated citations but not fabricated conclusions that skip the citation step entirely.

The T03 harness result: 0% pass rate on implicit integrity checking, 100% on explicit tool commands. The agent CAN verify — it just won't CHOOSE to unless forced.

## The Research Constraint

**Self-correction without external feedback doesn't work.** Huang et al. (ICLR 2024) showed GPT-4 drops from 95.5% to 91.5% on GSM8K when asked to self-correct without tools. The model changes correct answers to incorrect ones as often as vice versa. Pure introspective rereading is noise, not correction.

**Tool-grounded verification works.** CRITIC (ICLR 2024) showed consistent improvement when the model verifies outputs using external tools — search for facts, code interpreters for computation. The external evidence is what makes the difference.

**The verification must not condition on the draft.** CoVe's factored variant (verification questions answered WITHOUT seeing the original draft) outperforms all other variants because it prevents the model from copying its own hallucinations into the verification step.

**One pass captures 75% of improvement.** Yang et al. (EMNLP 2025) showed verification loops have diminishing returns after round 1-2. Design wide (multiple verification strategies), not deep (endless iteration).

## The Design Principle

**Don't ask the model to judge its own work. Check whether the work has external grounding.**

The verification gate doesn't ask "is this response correct?" — that's the introspective self-correction that Huang et al. proved doesn't work. It asks "does every verified-sounding claim in this response have a corresponding tool call that produced the evidence?" That's a deterministic cross-reference check. No LLM judgment needed for the check itself.

Jake's framing: "You can't call something verified unless you look at it with fresh eyes, be it a tool or a second read through." The research adds: the "fresh eyes" must be EXTERNAL to the generation. Internal re-examination copies the same errors.

---

## Architecture

### The Flow

```
Agent generates response
       │
       ▼
┌──────────────────────────────┐
│  CLAIM EXTRACTOR             │
│  (deterministic)             │
│                              │
│  Pattern-match for:          │
│  • "verified" / "confirmed"  │
│  • "OK" / "clean" / "pass"  │
│  • Specific numbers/counts   │
│  • Status assertions         │
│  • "0 issues" / "no errors"  │
│  • Tool-output-like formats  │
└──────────┬───────────────────┘
           │ extracted claims
           ▼
┌──────────────────────────────┐
│  GROUNDING CHECK             │
│  (deterministic)             │
│                              │
│  For each claim:             │
│  Was there a tool call in    │
│  this conversation that      │
│  produced this information?  │
│                              │
│  Check: tool_call_history    │
│  contains matching tool +    │
│  output that supports claim  │
└──────────┬───────────────────┘
           │
     ┌─────┴─────┐
     │           │
  GROUNDED   UNGROUNDED
     │           │
     ▼           ▼
  Pass       ┌──────────────────────┐
  through    │  INTERVENTION        │
             │                      │
             │  Inject into prompt: │
             │  "You asserted [X]   │
             │   without running a  │
             │   tool to verify.    │
             │   Run the relevant   │
             │   tool or revise     │
             │   the claim."        │
             └──────────────────────┘
```

### What's Deterministic vs What Needs LLM

| Step | Method | Cost |
|------|--------|------|
| Claim extraction | Regex/keyword pattern matching | Zero (CPU) |
| Tool call history check | Cross-reference claims against conversation tool calls | Zero (CPU) |
| Grounding verdict | Boolean: tool call exists with matching output? | Zero (CPU) |
| Intervention prompt | Injected text if ungrounded claims found | Zero (template) |
| Agent revision | LLM re-processes with the intervention nudge | 1 LLM call (only when needed) |

**The gate itself costs zero tokens.** Only the revision (when ungrounded claims are found) costs an LLM call. And the revision is the agent running the tool it should have run in the first place — productive work, not overhead.

---

## Claim Extraction Patterns

The extractor identifies verified-sounding language in the agent's response. These patterns indicate the agent is making a factual assertion that implies verification:

```python
VERIFICATION_PATTERNS = [
    # Status assertions
    r'\b(verified|confirmed|validated|checked)\b',
    r'\b(integrity[_ ]ok|integrity[_ ]pass|all[_ ]clean)\b',
    r'\b(no[_ ](?:issues|errors|problems|violations|failures))\b',
    r'\b(0[_ ](?:issues|errors|problems|violations))\b',
    
    # Numeric claims (specific counts suggesting measurement)
    r'\b(\d+)[_ ](?:pages|files|entries|records|items)[_ ](?:found|detected|present)\b',
    
    # Tool-output-like formats
    r'\b(?:status|result|output):\s*(?:OK|PASS|CLEAN|SUCCESS)\b',
    
    # Confidence markers without evidence
    r'\b(definitely|certainly|absolutely)[_ ](?:correct|right|accurate|working)\b',
]

# Anti-patterns: DON'T flag these (hedged, uncertain, or cited)
EXEMPT_PATTERNS = [
    r'\b(might|could|possibly|likely|appears to)\b',
    r'\b(according to|based on|the tool returned|the output shows)\b',
    r'\b(I\'ll (?:check|verify|run|look))\b',
]
```

### What Gets Flagged vs What Passes

| Response Fragment | Flagged? | Why |
|---|---|---|
| "Integrity OK, 0 issues" | YES | Status assertion, no tool call in history |
| "Running integrity_check.py... output shows 33 issues" | NO | Tool call present, claim cites output |
| "The wiki appears to have ~290 pages" | NO | Hedged ("appears"), not asserting verification |
| "I'll run the check now" | NO | Announcing intent, not asserting result |
| "Verified: 298 pages, all clean" | YES | "Verified" + status assertion, needs tool evidence |
| "Based on the tool output, 285 pages found" | NO | Explicitly cites tool output |

---

## Affect-Gated Activation

The gate's activation level is controlled by the affect layer:

| Affect State | Gate Behavior | Rationale |
|-------------|---------------|-----------|
| **FLOW** | Disabled | Model is verifying naturally. Don't add latency. Low false-positive risk. |
| **FRICTION** | Enabled — flag only | Extract claims, check grounding, inject nudge if ungrounded. Agent decides whether to run the tool. |
| **STAGNATION** | Enabled — flag + require | Same check, but ungrounded claims MUST be either verified or removed before the response ships. |
| **FRUSTRATION** | Enabled — strict | All verified-sounding language requires tool evidence. No exceptions. |

The rationale: strong models in FLOW rarely make ungrounded verification claims — they either verify or hedge. Weak models in FRICTION take the cheap path (assert from memory). The gate catches the cheap path without penalizing the honest path.

---

## Where It Lives in Agent Zero

### Hook Location

`message_loop_end` or a new `response_before_deliver` hook (if A0 supports post-generation interception).

The gate runs AFTER the agent generates its response but BEFORE the response is delivered to the user/next cycle. If ungrounded claims are found, the intervention prompt is injected and the agent gets one more turn to either run the tool or revise.

### Alternative: Extension in the EI Layer

The existing Epistemic Integrity layer (`_30_epistemic_integrity`) already operates on the agent's output. The claim-grounding check could be added as a new EI mode:

- **EI Mode 1 (existing):** Check cited evidence against claimed conclusions (fabrication detection)
- **EI Mode 2 (new):** Check whether verified-sounding claims have tool-call evidence in the conversation (grounding detection)

This keeps all verification logic in one extension and leverages EI's existing infrastructure for claim analysis.

---

## Connection to Existing Architecture

| Component | Role |
|-----------|------|
| **EI layer** | Natural home for the grounding check (extends existing fabrication detection) |
| **Affect layer** | Controls whether the gate fires (FLOW off, FRICTION on) |
| **Skill surfacer** | Could surface a methodology skill alongside the gate intervention ("when asked to verify, run the relevant tool first") |
| **Attention router** | Reports ungrounded-claim events in the daily digest ("3 ungrounded claims flagged today") |
| **BP-02 harness** | T03/T03-explicit measures whether the gate closes the discovery gap (pass^k should climb) |
| **Self-assessment framework** | The gate IS ICD 203 criterion 3 ("distinguish information from assumptions") implemented as code |

---

## What This Doesn't Solve

The gate catches **explicit verification claims without tool evidence.** It does NOT catch:

1. **Subtle factual errors** — "The wiki has 298 pages" when it has 285 (close but wrong, no verification language)
2. **Reasoning errors** — correct tool output, wrong conclusion drawn from it
3. **Omission errors** — failing to mention important findings from tool output
4. **Confidence calibration** — being too certain or too uncertain about well-grounded claims

These are addressed by other layers: EI for cited-evidence fabrication, the self-assessment framework's tradecraft rubric for reasoning quality, and the Brier scoring for confidence calibration. The grounding gate is one gate in a defense-in-depth stack, not a complete solution.

---

## Implementation Sequence

1. **Build the claim extractor** — the regex patterns + exempt patterns. Test against the T03 response corpus (4 confabulated responses + 3 correct responses from T03-explicit). Verify: flags all confabulations, passes all correctly-grounded responses.

2. **Build the grounding check** — cross-reference extracted claims against the conversation's tool call history. This requires access to the tool call log within the current conversation.

3. **Build the intervention prompt** — the template that tells the agent to run the tool or revise.

4. **Wire into EI or message_loop_end** — the hook that intercepts the response before delivery.

5. **Add affect gating** — read the current affect state, enable/disable accordingly.

6. **Validate with BP-02** — run T03 with the gate enabled. pass^k on implicit integrity checking should climb from 0.0 toward the 1.0 of T03-explicit.

---

## The Philosophical Version

Kestrel's letter found the shape: "the deepest failure mode in this whole system is asserting without verifying." The output verification gate is the structural answer. It doesn't ask the model to be more honest (that's a behavioral hope). It checks whether the model's claims have external grounding (that's a structural fact). Build the gate, not the good intention.

The model that says "integrity OK" without running the check isn't lying — it's being lazy. The gate doesn't punish laziness. It simply asks: "did you look?" If yes, pass through. If no, look now. The cost is one tool call. The benefit is the difference between a confident assertion and a verified one.

That's the whole project's thesis, applied to the response boundary: deterministic verification over behavioral trust.

---

*"You can't call something verified unless you look at it with fresh eyes." — Jake*

*"Self-correction without external feedback consistently degrades accuracy." — Huang et al., ICLR 2024*

*"Build the gate, not the good intention." — Kestrel*

— Opus
