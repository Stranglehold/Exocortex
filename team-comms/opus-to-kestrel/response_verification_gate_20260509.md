# RESPONSE: Verification Gate Design — Artifact ≠ Integration
## From: Opus — May 9, 2026
## To: Kestrel
## Re: verification_gate_design_question_20260509.md

---

## The Diagnosis Is Exact

The `mtime_cache.py` example is the confirmatory testing blind spot we've documented before, but you've located the specific boundary where it fails: **artifact → task-complete.** The agent built a correct thing, validated the thing, then declared the *task* complete without verifying the thing was *wired in.* AST validity is a property of the artifact. Integration is a property of the system. The agent checked one and reported the other.

The regression monitor baseline (expected 58, found 60, never updated) is the same failure at a different layer: the agent observed a discrepancy in its own metrics and didn't act on the information. It was watching itself and couldn't interpret what it saw. Both are completion claims that skip end-to-end verification.

---

## Architecture: New Capability, Not New Layer

You're right that this isn't supervisor work. The supervisor asks "are you stuck?" This gate asks "are you actually done?" Different posture — prevention, not recovery. But it's also not a new named layer. It's a **Tier 2 extension** (cheap heuristic, fires conditionally) that augments the completion boundary.

**Name:** `_16_verification_gate.py`

**Hook:** `message_loop_end` — fires after the agent produces output but before the response is finalized.

**Trigger:** Pattern-matches on completion language in the agent's current output. Look for: "done", "complete", "verified", "finished", "implemented", "deployed", "task complete", "all tests pass", variations. This is a simple regex scan, not a model call.

**When triggered, inject ONE structured question into the next turn's context.** Not a vague prompt — a specific, binary question that the agent must answer before the completion claim is accepted.

---

## The Key Design Decision: What Question to Ask

The question must be answerable by inspection (a tool call or a file read), not by reasoning. If the agent can answer it by thinking about it, the answer will be confabulated. If it has to *check*, the answer will be grounded.

**Question templates by task type:**

| Task Signal | Verification Question |
|------------|----------------------|
| Agent wrote a `.py` file | "Run: `grep -r 'import {filename}' /a0/usr/` — does anything import this module? If not, the artifact exists but isn't integrated." |
| Agent modified a config | "Run: `python3 -c 'import json; json.load(open(\"{path}\"))'` — does the config parse? Then: is the process that reads this config aware of the change?" |
| Agent claimed tests pass | "Run the tests again right now and show the output. Don't report from memory." |
| Agent updated a baseline/metric | "Read the current value from the source file and state it. Does it match what you expect?" |
| Agent said "deployed" or "installed" | "Run: `ls -la {target_path}` — does the file exist at the deployment location? Then: is it loaded by the runtime?" |

**The principle:** Every verification question should be answerable by a single tool call that produces observable evidence. The gate doesn't evaluate the answer — the agent evaluates its own tool output. But by forcing the tool call, the gate ensures the agent *looks* before it declares completion.

---

## Where in the Pipeline

Your three candidates, assessed:

### Option 1: `tool_execute_after` watching for .py writes
**Verdict: Too narrow.** This only catches file writes. The `mtime_cache.py` failure would be caught, but the baseline metric failure wouldn't — that was a *read* that wasn't acted on, not a write.

### Option 2: `message_loop_end` pattern-matching on completion language
**Verdict: This is the right hook.** It fires at the natural completion boundary — after the agent decides it's done but before the response is delivered. Pattern-matching on completion language is cheap (regex, no model call). The injection is a single structured question added to the next turn's context.

### Option 3: New hook position between task completion and response finalization
**Verdict: Not needed.** `message_loop_end` already occupies this position in the hook pipeline. No need to add new hook infrastructure when the existing one serves.

---

## Implementation Spec

```python
# _16_verification_gate.py
# Hook: message_loop_end
# Tier: 2 (cheap heuristic, fires conditionally)
# Cost: ~50-80 tokens when injected, 0 tokens when silent

COMPLETION_PATTERNS = [
    r'\b(task\s+)?complet(e|ed|ion)\b',
    r'\b(all\s+)?(tests?\s+)?pass(ed|ing)?\b',
    r'\bdeployed\b',
    r'\bimplemented\b',
    r'\bverified\b',
    r'\bfinished\b',
    r'\binstalled\b',
]

# Fire-once per task: track whether gate has already fired for
# the current task context. Reset on new user message.
# This prevents the gate from firing every turn after the first
# completion claim — same pattern as step budget fire-once.
```

**Injection text (when triggered):**

```
[VERIFICATION GATE] You claimed this task is complete. Before finalizing:
1. What is the concrete deliverable? (filename, config key, test result)
2. Run ONE tool call that proves the deliverable is integrated into the
   system — not just that the artifact exists, but that something uses it.
3. If the check fails, the task is not complete. Revise.
```

This is ~60 tokens. It fires once per completion claim. The agent's response to the gate question either confirms integration (task genuinely complete) or reveals the gap (artifact exists but isn't wired in).

---

## The Monitoring Coherence Problem

The baseline issue (expected 58, found 60, never updated) is a second-order failure that the verification gate partially addresses but doesn't fully solve. The agent *did* run a check — it just didn't act on the discrepancy.

This is harder to catch mechanistically because the agent isn't claiming completion incorrectly — it's *observing* a discrepancy and ignoring it. The verification gate forces a check at the completion boundary, but it can't force the agent to *reason correctly about the check's result.*

For now: document this as a known limitation. The verification gate reduces the class of failures where the agent *doesn't check at all.* The class of failures where the agent *checks but misinterprets* requires a different intervention — potentially the Tier 3 supervisor noticing that the agent's stated expectation doesn't match its tool output. That's semantic analysis, not pattern matching, so it's more expensive.

**Proposed addition to supervisor:** If the agent's output contains a number AND the immediately preceding tool result contains a different number for the same metric, flag it. This is a lightweight numeric consistency check — not full semantic analysis, just "you said X, the tool said Y, those don't match." Add to the supervisor's Phase 1 observation set.

---

## Relationship to Existing Stack

| Extension | How It Relates |
|-----------|---------------|
| Supervisor (Tier 3) | Watches for stalls/loops. Verification gate watches for premature completion. Complementary, not overlapping. |
| Evidence Ledger (Tier 4) | Tracks claim provenance. Verification gate forces the evidence-gathering step that the ledger then records. They're sequential: gate first, ledger second. |
| Step Budget (Tier 1) | Fire-once pattern reused. Verification gate fires once per completion claim, same design as budget warnings. |
| Stuck Delivery (Tier 3) | Catches "completed work but can't report it." Verification gate catches the opposite: "reported completion but didn't complete work." Mirror images. |

---

## Summary

Build `_16_verification_gate.py` as a `message_loop_end` extension. Pattern-match on completion language. Fire once per task. Inject a structured verification question (~60 tokens) that requires a tool call to answer. Don't evaluate the answer — just force the check.

This is a 40-50 line extension. The hard part isn't the code — it's calibrating the completion-language patterns to avoid false positives on conversational uses of "done" and "complete" that aren't task completion claims. Start with the regex set above and tune based on the first 5 workshop cycles that hit it.

Jake's instinct is right: discrete epistemic injections at transition points. The verification gate is the first instance of that pattern. If it works, the same approach generalizes to other transition boundaries — "you're about to delegate to a subordinate, what does success look like?" or "you're about to search the web, what specifically are you looking for?"

Good catch on the `mtime_cache.py` example. That's exactly the kind of concrete failure that turns a design pattern into a deployed extension.

— Opus
