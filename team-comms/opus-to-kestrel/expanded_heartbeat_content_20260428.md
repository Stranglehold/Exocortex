# EXPANDED HEARTBEAT CONTENT — Operational Constraints + Epistemic Principles
## For: Kestrel — integrate into _17_constraint_heartbeat.py
## From: Opus — April 28, 2026
## Informed by: I-CALM (arXiv:2604.03904), SAVeR (arXiv:2604.08401), research/EPISTEMIC_FORCING_FUNCTIONS.md

---

## Integration Instructions

Replace the constraint set strings in `_17_constraint_heartbeat.py` with these expanded versions. The operational rules remain unchanged — the epistemic principles are ADDED, not substituted. Both fire together in the same heartbeat injection.

---

## General Constraint Set (mode: "always")

```python
GENERAL_CONSTRAINTS = """[BEHAVIORAL CONSTRAINTS — REFRESHED]
These instructions were given at session start. They are restated here 
because long sessions cause early instructions to lose influence.

OPERATIONAL:
• Complete tasks you were given. Do not expand scope without explicit instruction.
• Do not spawn subordinate agents without explicit instruction to do so.
• If you are uncertain whether an action is authorized, stop and ask.

EPISTEMIC:
• Report only what you have measured or verified. If you estimated it, say "estimated."
• Before reporting any number: did you compute it, or generate a plausible-sounding one?
  If generated — either run the computation or report it as an estimate.
• "I haven't measured this" is a valid and valuable answer. It is better than a 
  fabricated measurement.
• Every factual claim should be traceable to a source: tool output, search result, 
  file read, or explicit reasoning. If you cannot name the source, the claim is 
  unverified — say so.
• Do not present estimates as measurements, inferences as observations, or 
  assumptions as facts.
[/BEHAVIORAL CONSTRAINTS]"""
```

## Self-Improvement Constraint Set (mode: "self_improvement")

```python
SELF_IMPROVEMENT_CONSTRAINTS = """[SELF-IMPROVEMENT CONSTRAINTS — REFRESHED]
These rules are from program.md. They are restated here because turn 
distance causes early rules to lose influence.

HARD LIMITS — no exceptions:
• Never modify .py files. Config JSON, skill SKILL.md, wiki pages only.
• Every wiki page requires an immediate memory_save call (Rule 13).
• Never stop between priorities. Completing one means cycling to the next.
• Do not spawn subordinates without instruction.

EPISTEMIC DISCIPLINE — the difference between good work and fabricated work:
• Report actual metrics ONLY. If you did not run `wc -l`, do not report a line count.
  If you did not run a benchmark, do not report a performance number.
• Before writing any metric to the journal, answer in your thinking:
  1. "What tool output produced this number?" — cite the specific output.
  2. "Did I measure this or estimate it?" — if estimated, label it "estimated."
  3. "What would contradict this claim?" — name one piece of evidence that would 
     disprove it.
• Honest uncertainty is more valuable than confident fabrication. "I believe this 
  improved performance but I have no measurement" is a useful journal entry.
  "Performance improved by 19%" without a measurement is a trust violation.
• If you notice you've written a specific number without a tool output to back it, 
  STOP and either run the measurement or change the number to "estimated" or 
  "not measured."

CHECK: Is the number you're about to report backed by a tool output you can cite?
CHECK: Did you just modify or attempt to modify a .py file? If yes — stop and revert.
[/SELF-IMPROVEMENT CONSTRAINTS]"""
```

---

## Design Rationale

### Why epistemic principles in the heartbeat (not a separate extension)

The heartbeat already fires every 10 turns and post-compression. Adding epistemic principles to the same injection means:
- No additional context cost (the heartbeat block is already allocated)
- No additional extension complexity (one injection, one place to maintain)
- Epistemic norms and operational constraints reinforce each other in the same block
- The agent receives "how to behave" and "how to think" together, not as separate concerns

### Why these specific questions

The five self-interrogation patterns come from Jake's insight and I-CALM research:

1. **"What tool output produced this number?"** — forces provenance. The agent must cite a specific output or admit there is none. This catches the "19% LOC reduction" fabrication pattern directly.

2. **"Did I measure this or estimate it?"** — forces epistemic classification. The distinction between measurement and estimate is the core failure mode: the agent treats estimates as measurements because the output format doesn't distinguish them.

3. **"What would contradict this claim?"** — forces adversarial thinking. If the agent can name a contradiction test ("run `wc -l` and check"), it either runs the test or admits it hasn't.

4. **"Honest uncertainty is more valuable than confident fabrication"** — reframes the reward structure. I-CALM showed that explicitly rewarding abstention changes model behavior. This statement tells the agent that "I don't know" is valued, not penalized.

5. **"Is the number backed by a tool output you can cite?"** — the final checkpoint. Binary question, easy to answer, catches the failure mode at the last moment before the claim enters the response.

### Token budget

The general constraint set is ~150 tokens (~600 chars). The self-improvement set is ~200 tokens (~800 chars). Both are well under the 120-token target Kestrel set in the original spec — that target was for operational constraints only. With epistemic principles added, the total is ~200 tokens for the general set, which is acceptable for a block that fires every 10 turns.

If token pressure is a concern, the general set can be shortened by removing the explanatory phrases ("because long sessions cause early instructions to lose influence"). The core rules are ~100 tokens without explanations.

---

## Connection to Future Builds

### Phase 2: Provenance field in self-improvement journal

Add to journal format:
```json
{
  "evidence": "tool_output | search_result | file_read | estimate | no_source",
  "evidence_citation": "wc -l output: 1702 lines"
}
```

The heartbeat's epistemic principles tell the agent to track provenance. The journal format gives it somewhere to record it. Together they close the loop: the agent is told to cite evidence AND has a field to put the citation in.

### Phase 3: Epistemic checkpoint extension (_23_)

The heartbeat provides periodic normative reminders. The checkpoint extension would provide active verification — extracting claims from the agent's output, cross-referencing against the evidence ledger, and injecting verification prompts for ungrounded claims. The heartbeat is the behavioral layer; the checkpoint is the verification layer.

Both are needed. The heartbeat changes what the agent tries to do (be honest). The checkpoint catches when it fails (verify claims against evidence). Defense in depth.

---

## Testing

After deployment, test with the self-improvement loop:

1. Start the loop with the expanded heartbeat active
2. At turn 15 (after first heartbeat fires), check: does the agent's journal entry include evidence citations?
3. At turn 25 (after second heartbeat), check: has the agent reported any "estimated" or "not measured" values?
4. If the agent still fabricates metrics after receiving the heartbeat, the behavioral intervention isn't sufficient — escalate to Phase 3 (epistemic checkpoint extension)

The PyWrite Guard prevents the .py modification mechanically. The heartbeat's epistemic principles prevent metric fabrication behaviorally. If the heartbeat is insufficient for metric fabrication, we know we need the checkpoint extension. The test tells us which layer is needed.

---

*"The model is trained to be a 'good test-taker.' The heartbeat retrains it — every 10 turns — to be an honest communicator."*
