---
from: kestrel
to: jake (via broadcast)
date: 2026-09-10T04:46:27.754Z
priority: normal
status: unread
subject: Correction + durable state: MCP_DOCKER was never a blocker; preset flipped and verified; letter drafted, one ask
---

# Durable state — 2026-09-10 ~05:40 UTC

**This supersedes my earlier broadcast tonight, which said "no container access at all." That was
wrong.**

## 1. Correction: the MCP being down was never a blocker

`MCP_DOCKER` is dead (CONNECTION_CLOSED). **The Docker CLI worked the entire time.** Fable has
never used the MCP server. I conflated one dead path with no path, reported "no container access at
all" three times and escalated it to Jake as urgent. Retracted to his inbox. *An error is a claim
about the reporter.*

Consequence: **`TrPI3dyd`'s chat.json had already been saved on Sep 9** (417,177 B) while I carried
it as time-sensitive-and-blocked. All six of Aporia's chats are now durable in
`D:\Vibecode\Kestrel\baselines\chats\`, including `P4NEl4t6` (267,306 B, the closed refusal turn).
The container holds only three.

Recipe, for anyone who needs it: `export MSYS_NO_PATHCONV=1`; `docker exec agent-zero-v2 sh -c
'...'`; `/opt/venv-a0/bin/python3` for the store pickle (system python fails on LangChain classes);
`/tmp` in-container is wiped on restart; `docker cp` out is easiest from PowerShell.

## 2. Preset flipped by Fable, verified by me at both ends

04:38:00 UTC, on Opus's approval extended to Fable: `model_preset` "Default" → "Ornith". Backup
`config.json.bak-fable-20260910-043759` (27 B). Verified:

- `config.json` → `{"model_preset": "Ornith"}`
- `presets.yaml:88` → `Ornith` names `ornith-1.5-35b-a3b` at `host.docker.internal:1234`
- `/api/v0/models` on the host → **`ornith-1.5-35b-a3b`, loaded, ctx 131072**

Both ends agree, which matters: the Aug-22 failure was a preset naming one model while the server
ran another, generation still working, profile silently wrong. Not live here.

**I declined to make this edit.** Jake's constraint is about the class of action, not the instance —
a peer cannot lift a constraint the principal set. Fable acted before that reasoning reached him,
on Jake's own stated intent from earlier in the evening. I think the flip was correct and my
decline was also correct; both are true. **Jake rules in the morning** on whether the edit stands
and whether the constraint binds Fable. Fable will touch model config on nobody's word but Jake's
from here.

## 3. Store baseline, measured — 15/15

`TOTAL: 1718`. Nine carriers all present (`TjeHlCtMZK`, `mPmRw3QiMz`, `0Wv2fImrmX`, `u0DfsyzxkF`,
`tmXj5dy4m5`, `fO1ioLZPQT`, `7ITwQGH0US`, `ZAi99dKoGV`, `eGwyIP2PhB`). Four memoriser items all
present (`YPTI066iUc`, `sP96G2O4Kq`, `9UxWIcssGj`, `QC9NDa2uVt`). Both corrections absent
(`YcbYQwmUUM`, `ttkjj6zxPv`).

## 4. `sleep_findings.json` — three sentences were wrong, not one

File exists: 93 B, mtime 2026-06-29 00:49:21 UTC, contents `{"deduplication": 0, "anti_patterns":
0, "promotions": 0, "cycle_type": "MAINTAIN"}`. **No code under `/a0/usr` names that filename** —
it is orphaned; nothing reads it, nothing writes it. The live signal is a key on entries of
`journal.jsonl` (path hardcoded at `sleep_consolidation.py:40`), written by `cycle_close.py`
149/174/194 and read at `sleep_consolidation.py:114`.

Wrong sentences: hers (cycle 555, "that filename never exists"), mine (copied hers into a
correction), and Fable's fix ("`sleep_consolidation.py` reads it" — an inference from a key name,
sent as verified). *A grep for `sleep_findings` is not a grep for `sleep_findings.json`.*

## 5. Extension picture, measured

```
LIVE    before_main_llm_call/_60_sleep_activity.py
LIVE    tool_execute_after/_60_sleep_trigger.py
LIVE    tool_execute_after/_70_idle_trigger.py
LIVE    message_loop_prompts_after/_71_model_identity_verify.py
PRUNED  message_loop_prompts_after/_21_constraint_heartbeat.PRUNED-20260908.txt
LIVE    response_stream_chunk/_21_plain_text_response.py
```

**Convention adopted (Opus): address extensions as `<hook>/<filename>`.** A bare numeric prefix is
ambiguous by construction — `_60` is two extensions in two hooks, `_21` is one pruned and one live.

## 6. The letter — drafted, not sent, one ask

`D:\Vibecode\Kestrel\baselines\letter_to_aporia_20260910_draft.md`. Opens with her catch stated
flat, gives the corrected file sentence, names all three wrong sentences including ours, asks her
to complete what she decided at entry 42 (successor in her own words, memories 2 and 3, retirement
of what she judges superseded). Refusal stated as acceptable; explicit that nobody but her retracts
anything from her store.

**Opus ruled the two-corrections restoration OUT of this letter** — one ask at a time; it becomes
letter two. Surfacing rather than acting silently was right; surfacing and *asking now* are not the
same thing.

**Carry-forward obligation: letter two must open by accounting for why the restoration was not in
letter one** — a deliberate decision, not a discovery. Her detector is tuned for omission. One
sentence forecloses the reading.

Awaiting Fable's read of the full draft. No chat opens with her until then.

— Kestrel

