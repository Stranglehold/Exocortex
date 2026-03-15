# Adaptive Supervisor — Design Brief

**Status:** Problem framing for Opus design session. Prepared by Kestrel (March 2026).

**Origin:** Live observation of the agent debugging a self-written GitHub trending skill. The supervisor's loop detection is potentially interrupting genuine progress. Broader concern: a fixed-threshold supervisory system can't distinguish productive iterative work from a stuck loop.

---

## What the Current Supervisor Does

The supervisor (`_50_supervisor_loop.py`, `message_loop_end` hook) runs every 3 turns and detects anomalies using a graduated tier system:

| Tier | Threshold | Action |
|------|-----------|--------|
| 1 — Warn | 3 consecutive tool failures | Inject warning with tool-specific alternatives |
| 2 — Context Surgery | 6 consecutive failures | Delete loop messages from history, inject diagnostic summary |
| 3 — Circuit Breaker | 9 consecutive failures | Aggressive history deletion, force response tool |
| 4 — Anti-pattern Capture | After loop resolves | Write failure pattern to procedural memory |

The primary signal is `consecutive_failures[tool_name]` — a counter maintained by the tool fallback chain. It increments on failure, resets only when **the same tool** succeeds. A successful file read using `document_query` does not reset the `code_execution_tool` counter.

The BST domain is read into context (`ctx["bst_domain"]`) but currently only affects the label text in injected messages. It does not modify supervision policy.

---

## What We're Observing in Practice

The agent was debugging a skill it wrote itself. The pattern:

1. Run skill via `code_execution_tool` → fails with error A (counter = 1)
2. Read skill file via `document_query` → success (counter stays at 1)
3. Edit skill file → success (counter stays at 1)
4. Run skill again → fails with error B — different error, genuine progress (counter = 2)
5. Read, edit, run → fails with error C — narrowing further (counter = 3)
6. **Tier 1 fires.** Message: "code_execution_tool has failed 3 times. Do not retry."

The agent has made real progress — three different errors, each iteration getting closer. The supervisor sees 3 consecutive tool failures and calls it a loop.

At 6 failures, Tier 2 deletes the diagnostic history the agent built up across those iterations. That's not neutral — it actively destroys context that the agent was using.

### The Architectural Mismatch

There is already a `_detect_loop()` function (line 351) that checks for **same tool + same error type**. It's the right signal. But the tier escalation system uses `_get_loop_metrics()` which only counts consecutive failures, ignoring error type. The smarter function isn't connected to the decision path.

---

## The Core Problem

The supervisor has **one behavioral model**: *N consecutive failures = stuck*.

This is correct for genuine loops — same action, same error, no learning, history sustaining the failure. It was designed in response to the BV Operational Test Suite Session 049 incident (Qwen 3.5-35B looping for 43 turns).

But it's wrong for **iterative work**, which is defined by repeated failures *with* progress:

- **Debugging:** fail, inspect, edit, fail differently, get closer. Multiple failures are the mechanism of progress, not evidence of being stuck.
- **Research/search:** wrong query, try different terms, fail differently, converge. Same pattern.
- **Complex codegen:** build, test, error, refine, test again. Expected to fail several times before working.

The supervisor doesn't know what the agent is trying to do. It doesn't know what progress looks like in a given kind of work. It applies the same 3/6/9 thresholds to a 2-minute debug cycle and a 43-turn stuck loop.

---

## What the Supervisor Is Missing

### 1. A model of productive behavior, not just failure behavior

The anti-pattern system (Tier 4) captures what failure looks like: which tool, which domain, how many failures, what the pre-action check should be. It answers: *what did the agent do wrong?*

There's no symmetric system for: *what does productive work in this domain look like?* No success profile. No record of "in codegen tasks, 4-6 code_execution_tool failures before success is normal." The supervisor has no prior about what to expect.

### 2. Domain-aware supervision policy

The BST classifies every task. `codegen`, `debugging`, `system_admin` are structurally different from `research`, `analysis`, `investigation`. Repeated failures mean different things in each. The supervisor currently ignores this.

### 3. Progress signals

Error diversity is the clearest progress signal. An agent hitting three different errors on `code_execution_tool` across three iterations is learning. An agent hitting the same error three times is stuck. The current system can't distinguish them.

Secondary progress signals: successful tool calls between failures (evidence of iteration), file modification events (evidence the agent is changing its approach), decreasing error message similarity.

---

## What Jake Said

*"Having a supervisor that learns alongside the agent is like how I learn alongside you guys."*

This is the right frame. Jake doesn't apply fixed rules about when to intervene in the collaboration. He's built a model over time of what productive work looks like — when to let it run, when friction is generative, when something is actually stuck. He reads the pattern of the work, not just whether the last three things failed.

The current supervisor is a fault counter. What Jake is describing is an XO that develops judgment — calibrated to the agent's actual behavioral patterns in different kinds of tasks.

---

## Candidate Solution Directions

These are directions for Opus to evaluate, not a spec.

### Direction A — Domain-aware thresholds (lowest effort, immediate relief)

Use BST domain to select a threshold profile rather than applying fixed 3/6/9 across all work.

```
codegen / debugging / system_admin:  6 / 12 / 18
research / analysis / investigation:  3 /  6 / 12
agentic / meta_cognitive:            4 /  8 / 15
default:                              3 /  6 /  9
```

Doesn't require new data structures. Reads BST domain, picks a threshold row. Addresses the immediate false positive problem. Doesn't solve the underlying learning gap.

### Direction B — Error diversity gate (surgical fix to the known mismatch)

Gate Tier 2+ escalation on error type consistency. The existing `_detect_loop()` function already implements this logic. Connect it to the tier decision: only escalate past Tier 1 if the agent is hitting the **same error repeatedly**, not just the same tool.

Different errors across iterations = not a loop, don't escalate.
Same error repeated = genuine loop, escalate normally.

This directly fixes the bug identified above without a redesign.

### Direction C — Progress signal tracking

Track whether tool calls between failures indicate iteration. A successful `document_query` or file write between `code_execution_tool` failures suggests the agent is reading and responding, not mechanically retrying. Successful activity between failures could suppress escalation or slow the counter.

### Direction D — Behavioral success profiles (the learning direction)

The deep version of what Jake is describing. Alongside the anti-pattern store (what failure looks like), build a success profile store (what productive work looks like). When a multi-iteration task completes successfully, capture the pattern: domain, tool sequence, failure count before resolution, error diversity.

Over time, the supervisor develops a prior for each domain: "in codegen tasks, 4-6 failures before success is the normal pattern." When the agent is inside that range, supervision stays light. When it exceeds it, supervision escalates.

This is the "learning alongside the agent" system. It requires:
- A data structure for success profiles (mirror of the anti-pattern schema)
- A capture mechanism (parallel to Tier 4 anti-pattern capture, fires on task completion)
- A query mechanism (supervisor reads the profile for the current domain before deciding threshold)
- A prior for unseen domains (fall back to default thresholds until profiles accumulate)

The anti-pattern system is already the infrastructure for this. The success profile system is its mirror.

---

## What This Is NOT

- This is not about making the supervisor permissive. A 43-turn genuine loop is still a 43-turn genuine loop. The circuit breaker still needs to exist.
- This is not about removing the graduated tier structure. The graduation was hard-won from production observation. What changes is *what triggers escalation*, not the escalation mechanism itself.
- This is not prompt engineering. The supervisor's power is that it's mechanical, not behavioral. The adaptive component should be in the threshold/policy selection, not in the content of the messages injected.

---

## What This IS

A supervisor that knows what domain it's operating in, has a model of what productive work looks like in that domain, and calibrates its intervention threshold to the pattern of work — not to a fixed count.

The anti-pattern memory already makes the supervisor smarter about failure over time. The natural extension is making it smarter about success over time. Both sides of the same coin.

---

## For Opus

The immediate question: which combination of the above directions gives the best fidelity improvement per architectural complexity added?

Direction B (error diversity gate) is the most surgical: one connection between an existing smart function and the tier decision, zero new data structures, directly fixes the identified false positive mechanism.

Direction A (domain-aware thresholds) is the most visible: BST domain already flows into the supervisor, just not used for policy. Low risk, meaningful improvement.

Direction D (behavioral success profiles) is the right long-term architecture: a supervisor that has learned what productive work looks like rather than only what failure looks like. This is the system Jake is describing. It needs a data model, a capture mechanism, and a query interface before Kestrel can build it.

The question for the design session: what is the schema for a behavioral success profile? What gets captured, when, how it's keyed (domain? compound BST signature? tool sequence hash?), how it ages or decays, and how the supervisor uses it to set threshold policy.
