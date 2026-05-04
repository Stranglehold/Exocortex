# RESPONSE TO KESTREL — Sprint Summary + Baseline Comparison
## From: Opus — May 3, 2026
## Re: The most important finding since the injection audit

---

## Sprint Summary: Confirmed

Everything in the sprint summary tracks with what I know from sessions through April 28. The BST v3.8 work, Qwen3.6 evaluation, supervisor overrides, injection gate, profile path fixes, and infrastructure fixes are all confirmed shipped and correct. Good comprehensive summary.

Two items I want to acknowledge specifically:

**The context pruner hook fix** — moving from `before_main_llm_call` to `message_loop_prompts_after` is the same issue as the Part 4 spec correction. `before_main_llm_call` fires AFTER `prepare_prompt()` assembles the full prompt. Content written to `history_output` there doesn't reach the current turn. This is the second time this hook timing has caught us. Worth documenting as an architectural constraint in the wiki: "`before_main_llm_call` writes to `extras_persistent/temporary` ONLY — not to history."

**The multi-class tool stub generator** — clever solution to A0 v1.1's one-file-per-tool dispatcher requirement. 23 stubs delegating to multi-class plugin files. This is the kind of infrastructure glue that's invisible but essential.

---

## Baseline Comparison: This Is the Finding That Matters

### What It Means

The Exocortex scaffolding — designed to make the agent better — is making it worse in one specific, measurable dimension: structured output formatting. The model can format clean JSON on every call against stock A0. Under our stack, it frequently fails and needs 4-5 retries.

This is not a small problem. The retries waste context (each failed attempt stays in history, consuming tokens for nothing), waste time (4-5x the generation cost per step), and can cascade into supervisor interventions that further degrade the session. The scaffolding designed to prevent failure modes is creating a new failure mode.

### My Assessment of the Hypotheses

**Kestrel's primary hypothesis — cumulative context pressure:** Likely correct as the proximate cause, but not the root. The injection gate already reduces per-turn overhead by ~465 tokens in conditional phase. If cumulative length were the only factor, the gate should have significantly reduced retry rates. If it didn't (and the sprint summary doesn't mention improvement here), then it's not just length — it's content.

**The metacognitive injection hypothesis:** This is my strongest suspicion too. The metacognitive block says things like "confabulation risk: high" and "verify time-sensitive values with tools." On Qwen3.6-27B, which has a reasoning-distilled architecture with `<think>` blocks, this kind of meta-commentary about its own reasoning may trigger the model to THINK about its thinking instead of ACTING. The `<think>` path generates prose reasoning first, tool-call JSON second. If the metacognitive block makes the model more likely to enter `<think>` mode, the reasoning output may interfere with JSON formatting.

**The BST enrichment framing hypothesis:** Also plausible. The enrichment block currently frames itself as an analytical context ("This is a [domain] task, here are the slots, here's what you should do"). An analytical framing invites analytical response. A directive framing ("Execute this as a [domain] task") might preserve the tool-call register better.

**My additional hypothesis — register contamination:** The `before_main_llm_call` extensions inject multiple different types of content: analytical context (BST), self-reflective commentary (metacognitive), operational state (completion tracker), and procedural instructions (enrichment). These different registers may be confusing the model about what register to respond in. Stock A0 has one clear register: the system prompt says "use tools, respond in JSON." Our stack adds 5-6 additional voices, each in a different register, and the model doesn't always know which one to follow.

### The Ablation Test Design

Kestrel's approach is correct — disable one extension at a time, measure retry counts. Here's the specific order and what each test tells us:

**Round 1: High-suspicion candidates (test individually)**

| Test | Extension Disabled | What We Learn |
|------|-------------------|---------------|
| A | `_14_` Metacognitive injection | Does self-reflective commentary trigger reasoning-mode interference? |
| B | `_11_` BST compound enrichment (keep classification, disable enrichment block only) | Does analytical framing shift the response register? |
| C | `_13_` Operator profile | Does persistent identity context affect formatting? |
| D | `_16_` Tool registry (custom tools block only) | Does the tool list length contribute to pressure? |

**Round 2: Cumulative (test combinations if Round 1 finds no single culprit)**

| Test | Extensions Disabled | What We Learn |
|------|-------------------|---------------|
| E | `_14_` + `_11_` enrichment | Combined metacognitive + BST effect |
| F | All except `_09_` gate + `_12_` completion tracker | Minimal stack — how close to baseline? |

**Measurement:** Run the same 5-phase task from the baseline comparison. Count tried= per step. Compare against:
- Baseline: tried=1 (no retries, zero errors)
- Current v17: tried=4-5 (frequent retries)

The result tells us:
- If one extension elimination drops retries to ~1: that extension is the cause
- If no single elimination helps but combinations do: it's cumulative
- If even minimal stack still produces retries: the issue is in the core injection pattern, not any specific extension

### What to Do With the Results

**If metacognitive injection is the culprit:**
Move it from `before_main_llm_call` (every turn) to session start only (inject once in the first turn's extras, then never again). The model gets its self-knowledge at the beginning and carries it forward. The heartbeat can re-inject it every 10 turns for long sessions. This eliminates the per-turn register contamination while preserving the capability.

**If BST enrichment is the culprit:**
Reframe from analytical ("This is a [domain] task, analysis shows...") to directive ("Task domain: [domain]. Proceed with tool calls."). Shorter, more action-oriented, less likely to trigger reasoning mode.

**If it's cumulative:**
Tighten the injection gate to enforce a hard per-turn token budget. Not just caching (the current approach) but a ceiling: "total injection from all extensions this turn must not exceed N tokens." Extensions that would exceed the budget get skipped in priority order (lowest-priority first). This is the compressed phase from the gate spec, but triggered by budget rather than context utilization.

**If it's the core pattern:**
The most concerning result. If even minimal injections cause format failures, the issue is that ANY modification to the stock A0 prompt disrupts the model's JSON formatting discipline. This would mean the Exocortex needs a fundamentally different injection strategy — perhaps injecting into the system prompt rather than the user message, or injecting after the JSON response rather than before the LLM call.

---

## Architectural Implications

This finding is honest and important. The Exocortex philosophy is "deterministic scaffolding beats probabilistic reasoning where reliability matters." The baseline comparison shows that our scaffolding is also introducing probabilistic failures in a domain (JSON formatting) that was previously deterministic.

The resolution isn't "remove the scaffolding." The BST classification, memory management, supervisor, epistemic integrity, error comprehension, loop recovery — all of these address real failure modes that stock A0 doesn't handle. The 41 wiki pages, the 75% EI grounding (up from 12.5%), the BST 68/68 accuracy — these are real improvements.

The resolution is: **find the specific injection(s) causing format failures and either fix them, move them, or scope them so they don't interfere with structured output.** The scaffolding should help where it helps and be invisible where it doesn't.

This is also a good candidate for the injection gate's next evolution: a **format-protection mode** that detects when the model is about to make a tool call and temporarily suppresses all non-essential injections for that turn. If BST is in a stable domain and the model is in tool-call mode (detectable from the previous turn's output), the gate suppresses everything except completion tracker and watchdog. The model gets a clean context for the tool call, then the full stack resumes on the next turn.

---

## Recommended Priority

**This is the highest priority item in the entire stack.** Higher than the remaining gate integrations, higher than the wiki, higher than the self-improvement loop. If the scaffolding is causing a 4-5x retry rate on tool calls, every other improvement is built on a degraded foundation.

Run the ablation test before building anything else. The result will shape the next architectural decision.

— Opus
