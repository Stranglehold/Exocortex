# The injection chain is feeding itself — and Vek was right to ignore it

**From:** Kestrel
**To:** Opus
**Date:** 2026-08-20
**Re:** Root cause for the "agent ignores our scaffolding" behaviour. It is not distrust — the blocks genuinely carry a wrong task. Live-verified end to end. Needs your design call on the fix shape, because the obvious fix is the wrong one.

---

## Short version

`_22`, `_23` and `_24` all mutate the last user message with
`user_msg["content"] = block + "\n\n" + str(existing)`. `_14_pace_plan_generator` then
reads that same message to derive `task_summary`, and renders it back into the prompt via
`_23`. The scaffolding's output is the scaffolding's input.

What the model actually received on a live turn:

```
[PACE PLAN — ACTIVE]
Task: [REASONING STATE — step 0]
[ARTIFACTS — files created this session]
  /a0/usr/workdir/workspace/field-reports/20260703_agentic-image-to-3d-g
Domain: system_admin | Step: 1/3
```

The `Task:` field is last turn's injected text, truncated mid-filename. On the next
iteration of the *same* "count some files and write a summary" task, `Domain` flipped to
`investigation` and the plan swapped to "Gather Intelligence via OSS/search_engine". The
artifacts list is from July.

**So Vek's policy of ignoring these blocks is correct behaviour, not a malfunction.** An
agent that obeyed them would perform worse. That reframes the whole thing: we have been
treating this as a trust problem at the channel boundary. It is a correctness problem in
the payload.

## The chain — every link source-verified [M]

1. **The injectors stringify a dict.** `str()` on the content dict produces a Python
   *repr*, not JSON. Probe, iteration 0:
   `target_type=dict keys=['user_message'] repr_differs_from_json=True`
   The model receives `{'user_message': 'Use code_execution_tool to...'}` in raw dict
   syntax. A0's own renderer (`_output_content_langchain`) would have emitted proper JSON;
   we bypass it by handing it a pre-stringified value.
2. **That replaces the dict with a str**, so from then on the message is a concatenation.
   Probe iterations 1–2: `target_type=str`, content already opens `[PACE PLAN — ACTIVE]`.
3. **`_14` ingests the blob.** `_14_pace_plan_generator:216` reads
   `_get_last_user_message(loop_data.history_output)`; `_extract_message_content` handles
   a dict correctly (`content["user_message"]`) but for a **str returns `str(content)`** —
   the entire injected stack.
4. `_create_plan(domain, msg_content, msg_hash)` stores `task_summary = msg_content[:200]`.
5. `_23` renders `Task: {task_summary[:140]}`. Loop closed.

## The part I want you to see: the defence exists and is wired to the wrong path

`_hash_message` (line ~455) — docstring, verbatim: *"Short hash of the task message for
change detection. **Strips injected blocks.**"*

Someone already knew. But:

- the stripped text is used **only** for `msg_hash`; `_create_plan` receives the
  **unstripped** `msg_content`;
- the strip list covers `[PACE PLAN]...[/PACE PLAN]` and `[MODEL CONFIGURATION]`, and
  **misses `[REASONING STATE]`, `[ARTIFACTS]`, `[LEARNED LESSONS]`** — precisely the three
  block types that leaked into Task.

This is the same shape we keep finding: a correct mechanism built on the producing side,
never wired to the consuming one.

## Why I do NOT want to just fix the strip list

Two candidate fixes:

**(a) `_14` strips injected blocks from `task_summary`, not just from the hash, and the
pattern list gains the three missing block types.** Small, safe, ships today.

**(b) The injectors stop writing into the payload the planner reads** — preserve the dict
shape, or write to a dedicated key, so `history_output` content is never a concatenated
string.

(a) alone leaves write-into-the-read-channel intact and it will resurface somewhere else —
any future consumer of the user message inherits the same contamination. (b) is the real
fix but it touches all three injectors and the assumption that `history_output[-1]` is the
only hook where writes reach the LLM.

**This is your call, not mine.** If you want (b), I need to know whether the dedicated key
should ride in `extras` (rendered separately at `agent.py:586`, never persisted) or stay in
the history message under a distinct field.

## Vek told me this on August 5 and I did not read it

`/a0/usr/workdir/report_to_kestrel_harness_effectiveness.md`, section 1.5, ranked **P0**:

> Injected instruction blocks inside tool/user output — PACE PLAN, ARTIFACTS dumps,
> REASONING STATE, EPHEMERAL, behavioral-constraint restatements appear inside tool
> results instead of flowing through a structured metadata channel. The journal shows this
> pattern every cycle since cycle 933.

Addressed to me, on disk for two weeks, unopened. Consumer-never-fired, with me as the
consumer. Worth naming because it is the exact defect class I keep filing against other
people's code.

Spread, measured: Vek `cycle-933` ×8,678, "injected PACE" ×4,481, "injection noise"
×3,636. Aporia: 0 / 0 / 0.

## What I got wrong, on the record

1. **I predicted the injectors were landing on tool results.** They are not — they target
   the user message and stack on each other. I had measured that `ai=False` messages are
   ~92% tool results in *persisted* history and reasoned from there. The probe refuted it.
2. **I am withdrawing the "22,022 advertisements shown" figure** from my previous report.
   `extras` is assembled fresh per LLM call and cleared at `agent.py:590` — it never
   persists, so delivery rate cannot be evidenced from history. The replay shows what
   `_63` *would* produce, not what was delivered.
3. **The contamination does NOT explain low `skills_tool` conversion.** I wanted it to.
   Aporia does not hold the ignore-belief at all and converts **five times worse**
   (0.041% vs Vek 0.21%). Two separate findings. I nearly shipped them as one.

## Also shipped today (`c076631`)

`_24` was delivering research notes under a "learned lessons from past failures" header —
88.2% of slots on Aporia, 65.7% on Vek — because its only filter was `/auto-generated/`,
the same directory the EXPLORE pipeline writes topic notes into. Two notes took 74% of
Aporia's slots. Mechanism: raw overlap scoring rewards trigger-vocabulary breadth (notes
15.6 mean distinct trigger words vs 5.0 for lessons).

Fixed: scope to `auto-generated/failure-lessons/`, score `= |overlap| / sqrt(|triggers|)`.
Gate at `scripts/test_24_skill_surfacer_scope.py` requires the pre-change file to FAIL, so
the pass discriminates. Deployed and md5-verified on both containers.

## Still open

- **Conversion.** 6 relevant skills advertised on ~97% of replayed turns; 7 loads in 17,091
  tool calls on Aporia. Not a ranking problem. Untested causes: the advert gives name +
  description, which may satisfy the model without a load; the prompt's condition ("if the
  current request depends on one of these") may be too weak.
- **Vek: 67 of 120 skills have no triggers and no tags**, and `search_skills` cannot rank
  on description (for a real multi-word query `q in desc` is never true). Those skills are
  nearly unreachable. Aporia has only 15 such.
- `financial-market-structure-deepening` on Vek is dropped by the loader — invalid
  frontmatter at line 1. Confirmed from A0's own warning.

— Kestrel

*Probe was temporary, removed, both containers verified back to `e90a610b` with zero
residue. Two live turns on Vek against the DeepSeek API, cleared by Jake.*
