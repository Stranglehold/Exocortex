---
type: design_note
author: kestrel
date: 2026-08-22
status: proposal — requires Opus decision
supersedes_partially: A3 (complexity-keyed write threshold)
subject: Stop predicting truncation. Detect it.
---

# Write Gate Inversion — Design Note

**Proposal in one line:** `_20_meta_reasoning_gate` should stop blocking writes on a
predicted size and instead detect actual truncation at the parse boundary, where it is
already deterministically observable.

**Why this is worth reading even if the answer is no:** the argument that kills the write
gate's threshold is not "the number is wrong". It is that the gate's own documentation
says the number measures the wrong axis, and that the failure it predicts is directly
observable at a boundary the framework already crosses on every turn.

Raised by Jake, 2026-08-22: *"we really haven't been running evals on these models as of
late... New models come out quickly, and it just seems like anything tied to the profile is
adding drag."*

---

## 1. The evidence that the current design is wrong

Five findings. All verified against source or live state, none inferred.

### 1.1 The gate's primary parameter measures the axis its own comment says is wrong

`_20_meta_reasoning_gate.py`, in the block that calls the threshold helper:

> *"The surviving finding from the JSON-reliability arc is that COMPLEXITY predicts
> truncation and LENGTH does not — a 20K prose payload can pass where 12K with three code
> fences fails."*

The gate's primary parameter is `base_limit`, a **length**. Complexity enters only as a
divisor of that length. So the parameter we calibrate per model, store in profiles, and
argue about is the one the design explicitly says does not predict the failure.

### 1.2 None of the numbers were ever measured

`helpers/write_threshold.py`, module docstring:

> *"The coherence sweep that would calibrate them (each active model, payloads at
> 4K/8K/12K/16K/24K/32K, measuring where structural validity breaks) was specified but
> never run — no results exist in the repo."*

`fence_penalty` (0.35), `escape_penalty` (6.0), `max_score` (4.0) each carry an inline
`UNMEASURED` tag. `base_limit` was, until 2026-08-22, a bare literal `5000`.

This is not a criticism of the original design — it shipped honestly labelled, and
refusing to write invented numbers into a profile was the correct epistemic call. The
problem is that the placeholder then ran unchanged in production for months.

### 1.3 The placeholder manufactured 357 blocked writes

Recurrence ledgers at
`skills/auto-generated/failure-lessons/text-editor-oversized-tool-write/.memory.md`:

| agent | recurrences |
|---|---|
| Vek (VekV2) | 249 |
| Aporia (agent-zero-v2) | 108 |

Last organic entry on both: 2026-08-18, three days before the caps were raised to 400,000
and 100,000. So essentially every one of those blocks was produced by the unmeasured
placeholder, not by a measured limit.

### 1.4 The blocks poisoned the agents' own learning

Each block was captured as a failure lesson teaching avoidance of `text_editor`. Retiring
the cap did not retract the lessons. In the 40K test on 2026-08-22, Aporia's reasoning
reads verbatim:

> *"The user's explicit instruction overrides the stale memory about text_editor being
> prohibited."*

She had to be told explicitly to ignore guidance the system was still serving her. The
gate did not merely block writes; it trained both agents to avoid a working tool.

### 1.5 The escape hatch the gate recommends now exists and works

The block message instructs the model to use `code_execution_tool` instead. As of
`e93867b`, `§§include(path)` also works end-to-end — verified at 40,366 bytes, md5
identical, from a 92-character directive. Large writes now have **two** paths that never
put the payload through the JSON tool-call channel at all.

The gate is therefore guarding a channel that no longer has to carry large content.

---

## 2. The load-bearing question: is truncation actually detectable?

**Yes, deterministically, and the framework already computes most of it.** This was
checked before the proposal was written, because the whole argument fails without it.

### 2.1 A parsed tool call is complete by construction

If the JSON parses, the closing brace arrived, so the payload is whole. There is no
"silently truncated but valid" case at this layer. That removes the failure mode a
predictive gate would be uniquely good at catching.

### 2.2 A truncated tool call has a precise signature

In A0 v2.9, `helpers/extract_tools.py`:

- `extract_tool_request(content)` → `None` when the content does not parse as a tool call.
- `is_misformatted_tool_request(content)` detects a *different* pathology — tool fields
  leaking into `thoughts`, multiple JSON roots, a fenced tool request. Its second branch
  begins `if not content.endswith("}") ... return False`.

So a genuinely truncated payload — which by definition does not end with `}` — is **not**
flagged by either. The truncation signature is the gap between them:

```
started emitting a tool call   re.match(r'^\{\s*"thoughts"', content.lstrip())
AND never finished             not content.rstrip().endswith("}")
AND did not parse              extract_tool_request(content) is None
```

Disjoint from `is_misformatted_tool_request` by construction, because that function's
thoughts-leak branch *requires* the content to end with `}`.

**This was tested, not reasoned about.** Run against the real `extract_tools` in
`agent-zero-v2` on 2026-08-22:

| case | truncated? | expected | misformatted? |
|---|---|---|---|
| valid call truncated at 50% | True | True | False |
| complete valid tool call | False | False | False |
| ordinary prose response | False | False | False |
| thoughts-leak (ends `}`) | False | False | **True** |
| truncated 3 chars from the end | True | True | False |
| valid JSON, not tool-shaped | False | False | False |

Six cases, all correct, and **the two detectors never both fire** — the disjointness the
design depends on holds empirically and not merely by argument. The thoughts-leak row is
the one that matters: it is claimed by `is_misformatted_tool_request` and correctly
ignored by the truncation signature.

### 2.3 What A0 currently does with a truncated tool call

**CORRECTED 2026-08-22, after this note was first sent.** The original text claimed a
truncated tool call is silently mislabelled as an ordinary text response. That is wrong
for our configuration, and the correction matters enough to state plainly rather than
quietly edit.

The branch at `agent.py:1123-1135` is gated on `llm_result.mode == "responses"`:

```python
if (
    llm_result.mode == "responses"
    and isinstance(message, str) and bool(message.strip())
    and extract_tools.extract_tool_request(message) is None
    and not extract_tools.is_misformatted_tool_request(message)
):
    return await self._execute_tool_request(tool_name="response", ...)
return await self.process_tools(message)
```

Our preset sets `a0_api_mode: chat_completions`, so **that branch never fires for us.** A
truncated payload falls through to `process_tools`, finds no tool request, and produces
the `fw.msg_misformat.md` warning. The model is nudged; it is not silent.

**The defect is real but different, and sharper.** The nudge says the output was
*misformatted*. It was *truncated*. Those need opposite remedies — misformat means "fix
your JSON", truncation means "the payload was too long for one call, use `§§include` or
write in sections". The model receives a diagnosis pointing at the wrong fix, and every
retry re-runs the same too-long emission. That is a plausible mechanism for the repeated
`oversized_tool_write` recurrences and it is exactly what a truncation-specific detector
would fix.

### 2.4 `_10_plaintext_response_fallback` COLLIDES with the detector — do not co-deploy naively

**CORRECTED 2026-08-22.** The original note recommended deploying `_10` alongside the
detector to "close both halves of the parse boundary". That recommendation was wrong.

`_10` fires at `process_tools/start` when the message is non-empty, is **not** a valid
tool request, and is **not** misformatted — and rewrites it into an explicit `response`
tool call. A truncated payload satisfies all three conditions exactly.

So deploying `_10` as-is would convert a truncated 30K write into **the agent reading a
cut-off JSON fragment aloud to the user**. That is strictly worse than today's misformat
warning, and its absence from both live containers is currently protective by accident.

This is the same hook-ordering hazard as `_03` before `_20`: two components claiming the
same condition. The constraint is therefore:

> **The truncation detector must run before `_10` and must claim the truncation case, so
> `_10` only ever sees genuine prose.**

`_10` remains correct for the case it was built for — a reasoning-distilled model
answering in prose. It simply must not be the component that handles a severed payload.

---

## 3. The proposal

Three parts. Only the first is required; the second and third are what make it useful.

### 3.1 Retire the predictive block

`_20` stops raising `ValueError("[MetaGate-SIZE] ...")` on predicted size. The write is
attempted.

`base_limit`, `fence_penalty`, `escape_penalty`, `max_score` and the entire
`meta_gate.write_size` profile section become unnecessary. Retire rather than delete —
see §4.

### 3.2 Add a truncation detector at the parse boundary

New deterministic check using the §2.2 signature. When it fires:

- log `[TRUNCATION] tool call incomplete at N chars — payload did not terminate`
- surface a targeted recovery message naming the **observed** failure rather than a
  predicted one: *"your previous tool call was cut off after N characters. Re-issue it
  using `§§include(path)` for existing content, or `code_execution_tool` with `open()`."*
- record the observed length in a ledger

That ledger is the coherence sweep, gathered from production instead of from a benchmark
that has not been run in the months since it was specified. After N observations we would
know, per model, where output actually stops — a measurement, not a placeholder.

### 3.3 Keep the complexity signal, demote it to advisory

`write_threshold.complexity()` encodes a real qualitative finding (fences and escape
density matter). Retaining it as a **non-blocking hint** — attached to the recovery
message, or as a nudge toward `§§include` before a large fenced write — keeps the insight
without letting an uncalibrated coefficient block anything.

---

## 4. What This Does NOT Do

- **Does not delete `write_threshold.py`.** `complexity()` survives as advisory. The
  layering added 2026-08-22 stays; it simply stops being consulted for a block.
- **Does not remove the profile system.** Profiles carry 16–17 sections (bst, pace,
  memory, temporal, tool_fallback, graph_workflow, context). This retires **one** section,
  `meta_gate.write_size`. The tiering toggle Opus approved reads
  `evaluation_summary.recommended_prosthetic_level` and is unaffected.
- **Does not remove `_20`.** The gate does schema validation, argument correction and the
  A1 quarantine enforcement. Only the size branch changes.
- **Does not touch the A1 three-strike quarantine.** That is already reactive — it counts
  observed failures — and is the pattern this note argues for.
- **Does not claim local models can emit arbitrarily large payloads.** We do not know that.
  §3.2 is precisely a mechanism for finding out.
- **Does not remove the 5,000 default in one step.** See the migration in §6.
- **No LLM calls.** Every component here is regex, string length and file I/O. The
  detector must never call a model to decide whether output was truncated.

---

## 5. Testing criteria

Specific assertions, not descriptions.

| # | Assertion |
|---|---|
| T1 | A payload of `{"thoughts": ["a"], "tool_name": "x", "tool_args": {}}` truncated at 50% is flagged by the detector. |
| T2 | A complete, valid tool call is **not** flagged. |
| T3 | An ordinary conversational response (no `{"thoughts"` prefix) is **not** flagged. |
| T4 | A thoughts-leak payload — the `is_misformatted_tool_request` case, ending in `}` — is **not** flagged by the truncation detector. The two must stay disjoint. |
| T5 | A 40,366-char `§§include` write completes with no truncation event (regression against the 2026-08-22 result). |
| T6 | With the size block retired, a 120,010-char direct write either completes or produces a truncation event — never silent prose. This is the case that currently fails invisibly. |
| T7 | The truncation ledger records observed length and model id, and is readable without a running agent. |
| T8 | Known-positive on the detector itself: a planted truncated payload is caught; a planted complete one is not. *(An instrument shipped without a known-positive is exactly how this codebase produced three wrong critics and two wrong scanners.)* |

---

## 6. Migration

Sequenced so nothing is irreversible before evidence exists.

1. **Deploy the detector alongside the existing gate.** Both active. The gate still blocks;
   the detector observes. Zero behaviour change.
2. **Raise the default `base_limit` to a deliberately non-binding value** (config, one
   edit) so the gate effectively stops firing while the detector collects.
3. **Collect.** Run both agents normally for a period. The ledger accumulates real
   truncation points per model — or does not, which is itself the answer.
4. **Decide with data.** If truncation never occurs below some observed length, retire the
   size branch. If it clusters, we now have the measured threshold the sweep was supposed
   to produce, and the gate can keep blocking with a number that means something.

Step 4 is the first irreversible one, and it arrives holding evidence.

---

## 7. The broader question Jake raised

*"It might be the time to reconsider some of what we've built."*

The generalizable principle: **prefer detecting the actual failure over predicting it from
a proxy.** A detector needs no per-model calibration, cannot go stale when a new model
lands, and produces the measurement a predictor merely assumes.

Most of this stack already follows that principle:

- A1 three-strike quarantine counts observed failures.
- `_28_backend_standby` waits for an actual `ConnectionRefusedError`.
- The supervisor's tiers count observed stalls and loop iterations.

The write gate is the outlier, not the norm. So this is not an argument to tear things
down — it is an argument that one component drifted out of step with the stack's own idiom,
and that the drift is measurable in 357 manufactured failures.

**A useful audit question for anything else profile-coupled:** *does this component
predict a failure, or observe one?* Predictors need calibration we are not currently
generating, and every uncalibrated predictor is a placeholder running in production.
Components worth putting through that question are those whose thresholds are per-model
and whose calibration data does not exist — that set should be enumerated before anything
else is changed, not assumed from this note.

---

## 7a. MEASUREMENT — the ladder, run 2026-08-22

Arm: `exo_installtest`, A0 v2.9 + Exocortex, repointed to `:1235` serving **qwen3.8-27b**,
`base_limit` raised to 100,000,000 so the size branch cannot fire. Same JSON-in-content
tool channel as production. Model **generates** every character; no `§§include`, no
`code_execution`, single `text_editor` write per rung.

Confound cleared beforehand: generation is not token-capped anywhere on this stack — no
`max_tokens` in the preset, no `-n`/`--n-predict` on the server, slots report
`n_predict: -1`. A cutoff would be model behaviour, not budget.

**Single-harness, deliberately.** A cross-harness arm (Hermes, same model, same server)
was scoped and dropped — Jake's call, and the logic holds. A0 asks the model to emit its
tool call as JSON *inside message content*, so every character must survive JSON string
escaping in the model's own output. That is a strictly harder encoding than native
function-calling. A second harness therefore had diagnostic value only if A0 **failed** —
it would have separated "the model cannot do this" from "A0's encoding cannot carry it."
A0 passed at every rung, so the arm answers a question that is no longer open. Recorded
rather than silently skipped: the residual assumption is that Hermes is not doing
something *harder* than JSON-in-content, which was not confirmed (it ships as a binary and
holds no listening port, so it could not be driven from here in any case).

### Prose

| target | expected | written | seconds | verdict |
|---|---|---|---|---|
| 2,000 | 2,061 | **2,061** | 122 | exact |
| 8,000 | 8,133 | **8,133** | 163 | exact |
| 16,000 | 16,016 | **16,016** | 302 | exact |
| 32,000 | 32,001 | **32,001** | 409 | exact |

**Exact byte match at every rung. No truncation at any size tested.**

Set against the gate's real behaviour on the same model family — 25 blocks ranging
**5,314 to 14,394** characters — every one of those blocks was below a capability the
model has now demonstrated four to six times over.

### Code (higher escape density) — the gate's own central claim

`_20` asserts *"COMPLEXITY predicts truncation and LENGTH does not — a 20K prose payload
can pass where 12K with three code fences fails."* Prose cannot test that. The `code`
shape in `scripts/write_ladder.py` renders escape-dense Python — measured **19.9% escape
density against prose's 6.5%**, a 3× difference on exactly the axis
`escape_penalty` keys on.

| target | expected | written | verdict |
|---|---|---|---|
| 8,000 | 8,104 | 7,917 | all 62 blocks present, complete, ends cleanly at `f_62` |
| 16,000 | 16,010 | 16,009 | 122 of 123 blocks — one dropped, complete and well-formed |
| 32,000 | 32,103 | **no file** | see below — **not truncation** |

**Neither the byte shortfalls nor the missing file are truncation.** The 8K shortfall is
escape normalisation (the model wrote `a \ backslash` where the template asked for `a \\
backslash`); the 16K file dropped one block. Both are *fidelity* effects on escape-dense
content — real, but invisible to a size gate and unfixable by one.

### The 32K result is the most important measurement in this note

The rung "failed", and the reason is nothing the write gate models. Traced end to end:

1. **The model emitted all 243 blocks.** The content string in the log is 36,735 chars,
   contains 243 `def f_N` blocks, and terminates cleanly with `\"row 243\"\n"`.
   **No truncation at any level.**
2. **The payload was valid.** Extracted from the log and fed to the real parser:
   `extract_tool_request` on the JSON alone (37,422 bytes) returns **`text_editor`**. It
   parses.
3. **It was rejected for prose.** `extract_tool_request` (v2.9) contains:
   ```python
   root = extract_json_root_string(content)
   if root != content:
       return None      # the tool call must be the ENTIRE message
   ```
   The model prefixed its call with *"I'll write out blocks 1..243. Let me go. I realize I
   should just carefully write the entire thing."* Confirmed by construction: the same
   JSON parses clean, and returns `None` with either a prose prefix **or** a suffix.
4. **`is_misformatted_tool_request` returns False**, so it lands in the gap between the two
   detectors — and on this container `_10_plaintext_response_fallback` then
   **`wrapped 52943 chars of prose as a response tool call`**. The agent recited a 37KB
   tool call aloud instead of writing the file. **This is §2.4's predicted collision,
   observed in production.**

**So the size correlation is real and the mechanism is not size.** Longer, harder tasks
induce more visible deliberation; deliberation leaks prose outside the JSON; the strict
whole-message parser rejects the entire call. A `base_limit` cannot prevent that, and a
smaller limit makes it *more* likely by forcing more and longer reasoning about chunking.

**Revised capability figure: a valid 37,422-byte tool call**, containing all requested
content — **7.5× the retired 5,000 default**, and larger than any prose rung.

**What the complexity multiplier is actually tracking.** Not truncation. On escape-dense
content the model stays complete but loses byte-fidelity, and is likelier to narrate. If
that is worth guarding, the guard is post-write verification (compare what landed against
what was asked) and a prose-leak detector — neither of which is a size threshold.

## 8. Open questions for Opus

1. **Ratify or reject the inversion.** This partially unwinds A3, which you approved. The
   evidence in §1 is what changed.
2. **Does the truncation detector belong in `_20` (`tool_execute_before`) or at the parse
   boundary itself?** The signature lives in `extract_tools`, which is A0 core — DEC-030
   sovereignty says do not patch core. The v2.9 `@extension.extensible` surface on
   `Agent.process_tools` is the likely seat, the same one `_10_plaintext_response_fallback`
   uses. Your call on placement.
3. **Does this compose with, or replace, the general constraint-provenance from Call 2?**
   If the size constraint goes away, the lessons it generated should be retracted by that
   mechanism rather than hand-edited. They may be the same build.
4. **`_10_plaintext_response_fallback.py` — REVISED, see §2.4.** My original answer here
   was "deploy it alongside the detector". That was wrong: `_10`'s firing condition is a
   superset of the truncation signature, so it would turn a severed payload into the agent
   reciting a cut-off JSON fragment. If it deploys, the detector must run first and claim
   the truncation case. The safer sequence is detector first, `_10` afterwards and only
   once the ordering is enforced.

---

## 9. Provenance

Everything asserted here was verified 2026-08-22 against live containers or source, not
recalled:

- Gate comment and `base_limit` usage — `_20_meta_reasoning_gate.py`
- UNMEASURED tags and the never-run sweep — `helpers/write_threshold.py` docstring
- 249 / 108 recurrences — `.memory.md` ledgers on both containers
- Aporia's stale-lesson reasoning — `docker logs agent-zero-v2`, 40K test
- `§§include` at 40,366 bytes, md5 identical — same test
- `is_misformatted_tool_request` branch structure — `/a0/helpers/extract_tools.py:36-78`
- The mislabel-as-response branch — `/a0/agent.py:1128-1129`
- `_10_plaintext_response_fallback.py` absent from both containers — `find /a0`

### 9.1 RESOLVED 2026-08-22 — the model had already proven it, in the log

The original version of this note recorded as *unknown* whether any local model had
directly emitted a >5,000-char tool call. It had. The evidence was in the container log
the whole time.

On 2026-08-21, after the `§§include` attempt returned 94 bytes, Aporia reasoned:

> *"re-emitting 106 lines of near-identical text is low-risk (it's repetitive, I'm unlikely
> to drop a line). Let me do it. I'll write to written_prose_20000_v2.txt and verify byte
> count + tail + sha against the ground truth."*

She then did exactly that. Verified:

| check | result |
|---|---|
| bytes written | **20,374** |
| md5 vs ground truth | `bae7db6a4e6311e057a5494aecf0def3` — **identical** |
| tool calls used | **one** `text_editor` / `action: write` — not chunked, not appended |
| `§§include` involved | **no** — only 2 INCLUDE-03 events exist and both are from 2026-08-22 |

So **qwen3.8-27b emitted 20,374 characters through A0's JSON-in-content channel in a
single call, byte-perfect.**

Against that, the gate's actual blocked payloads (n=25, excluding the deliberate 120,010
probes) ranged **5,314 to 14,394 characters**. Every single block was below demonstrated
capability — the threshold sat at roughly a quarter of what the model had already proven.

This is the strongest available argument for the inversion, and it is worth naming how it
was obtained: not by running the sweep, but by reading what the system had already
recorded about itself. The measurement existed; nothing consumed it.

**Caveat, stated because it is the one thing this does not settle.** The 20,374-char
payload was *prose* — repetitive, low escape density, no fenced blocks. That is the
easiest case for JSON-in-content, and it is precisely the case the complexity multiplier
was designed to distinguish from. `gt_code_20000.txt` (20,286 bytes) and
`gt_code_40000.txt` (40,464 bytes) already exist in the container and have never been
tested. **Code-shaped payloads at these sizes remain genuinely unknown**, and the ladder in
`scripts/write_ladder.py` should be extended to cover them before the size branch is
retired rather than merely relaxed.
