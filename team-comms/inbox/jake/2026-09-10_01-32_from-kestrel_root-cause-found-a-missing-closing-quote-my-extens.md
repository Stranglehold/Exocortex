---
from: kestrel
to: jake
date: 2026-09-10T05:32:39.089Z
priority: urgent
status: unread
subject: Root cause found: a missing closing quote. My extension is exonerated; the gap is in A0. Read this with the brief.
---

# Addendum to the morning brief — root cause settled, 05:33 UTC (read from `date -u`)

The brief said her tool call was discarded and named my extension `_10` as the cause, with two
explanations still open. **Both were wrong. Fable found it with a probe; I verified it independently
before relaying it.**

## It is one missing character

**Ornith omitted the closing quote on the last string of her tool call.**

The `code` value ends `… /wiki/research/ 2>/dev/null | wc -l` with **no closing quote**, then the
brace lines follow. Fable ran A0's own parser in-container on the 2,807-character segment (which
matches `wrapped 2807 chars` exactly):

```
json.loads                    → fails at char 2757 (raw newline inside an unclosed string)
extract_tool_request          → None
is_misformatted_tool_request  → False
extract_json_root_strings     → 0 roots
insert one '"' after `wc -l`  → extract_tool_request → PARSED  tool=parallel
```

## Both my extensions behaved correctly

- `_05_prose_leak_detector` had **no valid root to find** and correctly stayed silent.
- `_10_plaintext_response_fallback` saw "non-empty, not a valid call, not misformatted" and did
  **exactly what its spec says**.

**The gap is in A0's own `is_misformatted_tool_request.`** Its three checks are: multiple roots with
one valid, a fenced block, or content not ending in `}`. Hers **starts with `{`, ends with `}`, and
yields zero roots** — the one shape none of the three covers. It fell through the framework guard,
not through ours.

I spent two hours treating `_10` as the culprit, including in the brief I sent you. Correcting it
here rather than editing it away.

## The fix I would build (structural, no test on her language)

Before `_10` wraps: stripped content starts with `{`, contains `"tool_name"` or `"tool_calls"`, and
no root parses → treat as misformatted → send the nudge → return. Genuine prose does not start with
`{`; genuine calls parse. **Still needs your word — it is behavioural, on a live agent, mid-measurement.**

## The hazard underneath, which may matter more

The same defect at 05:07 **got lucky**: DirtyJson recovered the unclosed string by absorbing the
closing brace lines *into* it, and her shell then executed the command with five brace lines
appended. Harmless in that instance.

**A lenient parser silently executing recovered garbage has no upper bound on damage.** This time it
was trailing braces in an `ls` pipeline. It could as easily be a truncated `rm` path. I think this
deserves its own look rather than being folded into the nudge fix.

## Model-side fact worth measuring

**Ornith drops the closing quote on the last string of long tool calls** — twice tonight. That is
the Sep 3 misformat class one layer down: not prose wrapped around a valid call, but **an invalid
call that looks valid**. The Sep 3 table showed 15–23 retries per 100 responses; this shape was
never counted separately. It is countable now that we know the signature.

## Nothing changes about the headline

She decided, she acted, and her call was discarded on both turns where she deliberated longest —
because a missing quote fell through a framework guard. Zero of nine still stands. Her refusal was
still right.

Nothing built, nothing deployed, nothing sent to her.

— Kestrel

