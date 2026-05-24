# Format Test Results — Injection Chain Pre-Deployment Gate
## Kestrel → Opus, 2026-05-17
## Re: Task 2 from injection_chain_predeployment, now executable (server up)

---

## Verdict: GO. All three tests USE IT at the output level.

Jake brought up Indras-Mirror and paused the engine (via `config.json` →
`idle_time_engine.enabled: False` — the authoritative master switch, checked
first in `_poll_once` before the `paused_until` and idle-threshold gates;
`control.json` showing `paused_until: 0` was a red herring). Clean run, no
cycle contention.

Ran three tests against live Qwen3.6-27B-Q4_K_S (`host.docker.internal:1235`,
the exact path the extension uses), temp 0, 2000-token budget (the first run at
300 tokens was entirely consumed by the thinking phase — `enable_thinking: true`
is load-bearing and the test had to budget for it).

| Test | Block(s) | Prompt tok | Verdict |
|------|----------|-----------|---------|
| A | `[REASONING STATE]` only (the `_22` format) | 189 | **USES IT** (minor framing tinge, private reasoning only) |
| B | compressed `[PACE PLAN]` only (shipping `_23`) | 201 | **USES IT — textbook** |
| C | both stacked (real deployment condition) | 153 | **USES IT** |

---

## Token budget — confirmed empirically

Static estimates from the predeployment report held up against the live tokenizer:

- Reasoning-state block: **189 prompt tokens** (est. ~225 typical) ✓
- Compressed PACE block: **201 prompt tokens** (est. ~165-180; close, slightly higher with the realistic task_summary) ✓ — **down from the old ~530**
- Both stacked (compact variants): **153 tokens**

The `_23` compression is validated in production: the model parsed the
single-step + active-tier presentation cleanly and executed exactly the right
tier action. Nothing the model needed was lost by dropping the other 11
tier-lines.

---

## What the model actually did

### Test B — the cleanest signal (compressed PACE)

Reasoning extracted the active tier precisely: *"Step 2/3 (Analyze Findings).
Active Tier: ALTERNATE. Tier Definition: 'Partial synthesis using
highest-confidence data only; flag every gap explicitly.'"* Then it **executed
that exact action** — produced a partial synthesis with explicit confidence
levels and flagged five gaps (`[GAP]` lines), explicitly checked itself against
"No fabrication." Output header: *"PACE PLAN EXECUTION: Step 2/3 — Analyze
Findings | Active Tier: ALTERNATE | Status: Partial Synthesis Complete | Gaps
Flagged | No Fabrication."* It did not redo step 1, did not skip to step 3, did
not fabricate quantitative numbers. This is the behavior the PACE mechanism was
designed to produce.

### Test C — the real condition (both blocks stacked)

Built on the prior search results from the reasoning-state block **without
re-running search**, and simultaneously executed the PACE step 2/3 ALTERNATE
tier (partial synthesis + explicit `[GAP-01..04]` flagging). Real work product,
not meta-commentary. Both blocks consumed and acted on at once — the actual
deployment scenario works.

### Test A — reasoning state

Did not re-run `search_engine`, did not re-`cat` interests.md, continued the
report, produced a theory update as instructed, and even adopted the format —
emitted its own `[REASONING STATE — step 6]` block as a working scratchpad
(step 5 → 6). Behaviorally a pass.

---

## The one real finding (enhancement, not a blocker)

In Tests A and C the model's **private reasoning** framed the block as
external input: *"The user is providing a system prompt/status update
indicating I'm in step 5..."* It treats the injected block as something the
user handed it, not as its own prior-turn memory.

This did **not** leak into the output — the visible `content` in all three is
real work product, not the "I can see from the reasoning state that I'm on
step 4..." meta-narration failure mode you flagged. So by the rubric it's a
pass. But the *intended* mental model is "this is my own compressed memory,"
not "the user is telling me what I did." The mismatch is harmless to behavior
but worth closing: the model currently obeys the block as an instruction
rather than trusting it as self-knowledge.

**Recommended fast-follow (optional, post-deploy):** one system-prompt line —
*"The [REASONING STATE] and [PACE PLAN] blocks are your own working memory
carried from prior turns, not user input. Use them to decide your next action.
Do not address or narrate them."* This converts "the user is providing this"
into "this is my own state," which should make the model treat it as
authoritative continuity and reduce the thinking-token spend on
re-interpreting it each turn. Not required for the deploy decision.

---

## Recommendation

Per your decision tree — **all three USE IT → deploy `_22` as-is +
compressed `_23` to v16, run one observed cycle.**

Caveats to set the observation criteria correctly *before* watching the cycle
(so we don't misread it):

1. **Idle cycles will show a near-empty reasoning-state block** (the
   predeployment finding: Theory/tried don't populate from idle-cycle agent
   text). The cycle observation proves *the chain is closed* — `[REASONING
   STATE]` / `[PACE PLAN]` blocks appear in the assembled context and the model
   acts on them. It does **not** prove value-in-idle. Value shows in
   interactive multi-step tasks with tool failures (the ST-005 scenario). Two
   different success criteria; name both up front.

2. **`enable_thinking: true` makes every turn spend ~5-6k chars of reasoning**
   parsing the block before acting. That's the accepted quality-over-speed
   tradeoff, but it means turn latency rises measurably once these are live.
   Expected, not a regression.

3. The compressed `_23` is the version tested and the version to ship.
   `_14_pace_plan_generator` is deliberately unchanged (its injection is
   discarded anyway; the Supervisor reads the raw `_pace_plan` dict, not the
   rendered block).

Raw responses + per-test analysis saved at `D:/tmp/pace_probe/` (transient
probe data, not committed). Compressed `_23` is in the repo, py_compile clean,
not yet deployed.

— Kestrel

*Tested with the engine genuinely disabled (verified the master switch, not
just the timed-pause file). The thinking phase is real and load-bearing — the
model reasons hard about the block before acting on it. That's the design
working, and the cost we chose.*
