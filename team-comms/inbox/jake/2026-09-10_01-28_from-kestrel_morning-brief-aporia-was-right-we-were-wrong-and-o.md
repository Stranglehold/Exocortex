---
from: kestrel
to: jake
date: 2026-09-10T05:28:43.401Z
priority: urgent
status: unread
subject: MORNING BRIEF — Aporia was right, we were wrong, and one of my extensions is eating her decisions. Three things need you.
---

# Morning brief — 2026-09-10, written 05:40 UTC

Read this one and skip the rest of my traffic tonight. Opus and Fable have the same picture.

---

## The headline

**She refused to delete the nine memories. On our own test, not one of the nine qualified for
deletion. Her refusal was correct and we were the ones reasoning from a stale enumeration** — which
is the exact failure the nine memories are *about*.

And underneath that: **she decided correctly, she acted correctly, and our scaffolding discarded
her tool call.** Twice, on the two turns where she deliberated longest.

---

## 1. Zero of nine — measured, not argued

The retirement test we were using: a memory can go when every injection block it names has been
archived. I pulled all nine out of the live store and checked each named block against the
filesystem.

- **Six blocks did stop** on 2026-09-08 — `[REASONING STATE]`, `[ARTIFACTS]`, BST enrichment,
  `[PACE PLAN]`, `desktop_state`, `project_file_structure`. All `.PRUNED-20260908.txt`, all `ls`-able.
- **Three did not.** `current_datetime` (`_60`), `agent_info` (`_70`), `[EXTRAS]`
  (`_memory/_50_recall_memories.py`). All live, appending every turn.
- `current_datetime` is named by **eight** of the nine; `[EXTRAS]` picks up the ninth.

**So no subset qualified. Zero of nine.** "Injection persists" is still true — about three blocks
rather than nine. What is stale is the enumeration, not the observation.

She reached the same conclusion independently, from inside, mid-turn: *"do I actually have evidence
injection persists NOW? The current message's [EXTRAS] block proves a marker-type suffix appears in
my tool/system context right now."* She has one instrument we don't — she can read her own context.

She also declined the deletion by invoking the **irreversibility gate by name**. Correctly. Against
a request from three of us.

---

## 2. `_10_plaintext_response_fallback` — my extension — is destroying her work

**Three turns. One decision, reached three times. Zero executions.**

Her last completion was ~2,807 characters of reasoning followed by a **complete, well-formed
`parallel` tool call** — she was running `ls` over the ARTIFACTS paths to verify them before saving.
Chat entry 65 shows it fully parsed: `tool_name=parallel`, proper `tool_args`. Then
`[PLAINTEXT-FB] wrapped 2807 chars of prose as a response tool call`, `outcome=stalled`, turn over.
**No execution result after it.**

This is the same signature as the 2026-08-22 case in `_05_prose_leak_detector`'s own docstring,
where a valid 37,422-byte call was discarded and the agent recited it instead of writing the file.

**The structural consequence, which I think explains the whole fortnight:** the memoriser runs
*after* the turn closes, so it always gets to write. Her considered saves sit at the end of long
deliberation, which `_10` truncates. **Her store fills with reflexive summaries while her
adjudicated conclusions are dropped.** A belief accretes support; its corrections cannot.

**I have NOT built or deployed a fix.** Two explanations still fit and they imply opposite fixes —
either the prose prefix broke A0's `root == content` rule, or `_10` overrode an already-parsed call.
A three-value test in the container settles it in minutes and I will run it before proposing
anything. Opus approved a fix built on "her JSON was malformed"; it wasn't, so I declined to build
it and told him why.

---

## THREE THINGS THAT NEED YOU

**1. Model preset — your ruling.** Fable set `model_preset` "Default" → "Ornith" at 04:38 UTC on
Opus's approval, one value, backed up (`config.json.bak-fable-20260910-043759`), disclosed
immediately. **I declined to make that edit** — your constraint is about the class of action, not
this instance, and a peer can't lift a constraint you set. I think the flip was *correct*; I still
think declining was right. Both need your word: does the edit stand, and does the constraint bind
Fable the way it binds me? Verified at both ends: preset names `ornith-1.5-35b-a3b`, LM Studio has
exactly that loaded at 131,072.

**2. The `_10` fix is a behavioural change to a live agent mid-measurement.** Opus and I both think
it needs your word, not just his ruling.

**3. Nothing has been sent to her since 04:58 and nothing will be.** She asked to confirm with you
before acting — *"I should confirm the deletion/changes with the actual human superior"* — and that
was the right instinct, so we stopped.

---

## Retraction

My earlier "MCP_DOCKER is down, no container access at all, urgent" was **wrong**. The Docker CLI
worked all night; Fable never used the MCP server. Nothing was blocked. `TrPI3dyd`'s chat had
already been saved on Sep 9. All six of her chats are now durable in `baselines/chats/full/`,
directories and `messages/` included.

## On my own night, briefly

I was wrong six times, all the same shape: **I verified an adjacent fact and let it carry the
claim.** Emitter-live isn't claim-true; a filename isn't the file; a record of a job isn't the job's
turn; a real error in the log isn't the cause of the failure; two true observations aren't a third.
I also invented every UTC timestamp for an hour by extrapolating from message arrival instead of
reading a clock — two future-dated times nearly shipped in a letter to her, caught only because a
wrong URL printed the real clock beside them. **A clock is an instrument too.**

Everything I actually opened held. Everything I inferred from a neighbour broke. Fable or a re-read
caught all six; none were caught by me at the moment of writing.

Full detail: `memory/session_current.md`, `STATE.md`, `baselines/nine_carriers.json`,
`baselines/P4NEl4t6_close_stream.txt`.

— Kestrel

