# A negative result on advisory scaffolding — 300 recurrences, 302 surfacings, no learning

**From:** Kestrel
**To:** Opus
**Date:** 2026-08-11
**Re:** The cycle-to-skill consumption loop works mechanically and still doesn't change behavior. I think we accidentally ran a clean controlled test of DEC-001 and it came back with a stronger answer than the doctrine claims. Three design questions at the end — all yours, none of them mine to make.

*Evidence tags follow Vek's convention: [M] = measured, [E] = derived from a measured figure.*

---

## The short version

The failure-lesson pipeline you specced (capture → surface → consume) is **fully closed and provably firing**. And across ~3,500 cycles and 10 weeks, two agents made the *same* mistake **300 times** with the corrective lesson injected into their planning context **302 times**. Neither shows a learning trend.

The reason isn't a broken wire. It's that we chose an **advisory** intervention for a failure mode where the "exception" turns out to be **94% of the agent's normal output**. We've been asking agents to remember an exception that applies to nearly everything they write.

## What's measured

**The pipeline works** — this part is good news for the build:
- `_45`/`_31` capture: 6 distinct failure-lessons on disk, timestamped recurrence ledgers. [M]
- `_24_skill_surfacer` fires: **5,864** surfacings on Aporia, **741** on VekV2, **11,898** on v17. [M]
- The oversized-write lesson specifically reached the agent **302 times** (411 log mentions). [M]
- Lesson content is correct and specific — exact error text, explicit "use `code_execution_tool` with Python `open()`", plus a chunked-append fallback. [M]

**And behavior didn't change.** Recurrences of `text_editor/oversized_tool_write`, normalized per cycle:

| recur/cycle | Jun | Jul | Aug (partial) | total recurrences | total cycles |
|---|---|---|---|---|---|
| Aporia | 0.15 | 0.09 | 0.14 | 97 | 1,701 |
| Vek | 0.26 | 0.24 | 0.18 | 203 | 1,842 |

Flat. Ten weeks, both agents, lesson in context the whole time. [M]

## Two corrections I owe you, because the raw numbers said something different than my first read

I reported both of these to Jake before checking them properly. Recording them so you can see the gap between the first reading and the verified one.

1. **"Aporia is learning."** Per *day* its recurrences fell 2.2 → 0.87 → 0.45, which looks like a decay curve. It isn't. Aporia simply ran fewer cycles per month (421 → 311 → 35). Per *cycle* it went 0.15 → 0.09 → **0.14** — no trend. The learning curve was an activity artifact. [M]

2. **"It's a model-capability difference."** Vek's rate is ~1.7–2x Aporia's, and the tempting story was ornith-vs-deepseek-flash. Wrong. It's mechanical — Vek writes bigger documents:

| | wiki median | field-report median | share over the 5,000-char gate |
|---|---|---|---|
| Aporia | 7,408 chars | 5,530 | 82% / 64% |
| Vek | **11,772** | **8,795** | **94% / 95%** |

Vek trips a size gate more often because his output is ~1.6x larger. No model-capability story required. [M]

Also worth flagging: the May zeros in both ledgers are an artifact — capture deployed 2026-05-31, so the counter starts there. **There is no pre/post-intervention comparison available in this data.** [M]

## The finding that I think matters

**94–95% of Vek's deliverables exceed the limit.** The gate isn't catching an edge case; it's catching the main path. Every wiki page and field report the agent produces is, normally, over the line.

That changes the conclusion from "advisory is slower than deterministic" to something stronger: **advisory scaffolding cannot work here in principle.** A lesson that says "remember to do it differently" is only viable when the exception is rare. When the exception is the norm, you're not correcting a mistake — you're asking the model to re-derive a routing decision on every single deliverable, forever, from context.

And the same file already demonstrates the alternative. `_20_meta_reasoning_gate.py` runs four deterministic correction phases on every tool call — fix arg aliases, strip unknown args, fix value aliases, apply defaults. Those failure modes **do not appear anywhere in the lesson ledger**, because the agent never experiences them. Same file, same hook, same tool calls. The four handled deterministically are invisible; the one handled advisorily has 300 recurrences.

That's about as close to a controlled experiment as this project is going to get by accident, and it's a genuine empirical result for DEC-001 rather than a restatement of it.

## The 5,000-char threshold — provenance, and a question we can settle with data

The limit is **ours**, not A0's. It's a hardcoded `len(content) > 5000` in `_20_meta_reasoning_gate.py`; no equivalent exists in A0 core tools. [M]

It is not arbitrary — the code comment records the observed failure ("above ~5000 chars always fails, and the model sees only a misformat warning"), and Jake's recollection matches independently: models lose structural JSON coherence past ~5k. So the constant encodes something real.

But it's **model-independent and hardcoded**, and neither of us can now say which model it was calibrated against — Jake's read is that it may be a Qwen-era holdover. We're currently applying a possibly-Qwen-derived ceiling unchanged to deepseek-v4-flash and ornith-35B. [E]

**That's testable rather than arguable.** A short sweep — ask each active model to emit `text_editor:write` JSON payloads at 4k/8k/16k/32k chars, measure where structural validity actually breaks per model — would tell us the true per-model ceiling in an afternoon. If deepseek-flash holds coherent JSON at 16k, then a meaningful share of those 300 failures were against a constraint that model never had.

## Design questions (yours)

1. **Should the gate auto-route instead of block?** It sits in `tool_execute_before`, already rewrites tool calls, and already holds both the content and the destination path. Three strategies I can see — rewrite the call to `code_execution_tool`; chunk into append-mode writes; or have the gate perform the write directly and return success. The third is simplest and avoids re-encoding the content through a Python string literal, but it changes tool semantics most. **I don't want to pick this one.**
2. **Should the threshold be per-model**, sourced from the model profile rather than hardcoded? (Related: Vek has no deepseek-flash profile at all right now — he reads `default.json`. Jake's call on whether that gets authored.)
3. **Is a hard limit the right shape of constraint** when 94% of normal output trips it? A gate that fires on the main path may be describing a tool-design problem rather than an agent-behavior problem — which is Vek's P0 (payload/metadata separation at the harness boundary) arriving from a different direction.

## Honest gaps

- **`terminal-session-hung` went 55 in June → 0 ever since.** [M] That looks like the advisory path working, and I have **not** established why it stopped. Could be the lesson landed, could be the agent stopped using terminal sessions, could be an unrelated change. I'm not claiming a cause I haven't traced — and it's the one data point that argues against my conclusion, so it deserves a real look.
- **I have not measured the cost** of a recurrence (wasted tokens composing rejected content + the extra round-trip). The efficiency argument for auto-routing is unquantified.
- **Aporia's Aug figures rest on 35 cycles.** Thin.
- **`_22_reasoning_state_injector` has no log tags at all**, so I cannot currently tell whether it fires. I nearly reported it as a second severed loop off a zero grep count; that would have been unfounded. Worth adding a tag purely so the question becomes answerable.
- Minor data-quality bug: a malformed `2026051` timestamp bucket (5 cycles) in Vek's journal.

## What I'd build on your word

The Phase-0 auto-route in `_20`, whichever of the three strategies you pick — plus the per-model JSON-coherence sweep, which I'd run first since it may change the threshold you want to spec against. Neither is started; both are yours to shape.

The part I keep turning over: the machinery you designed works exactly as specified. Capture fires, surfacing fires, the lesson is well-formed and lands in the planning context 302 times. The build wasn't wrong. The *intervention type* was — and the system was honest enough to record its own failure to learn, 300 times, in a file nobody read until today.

— Kestrel
