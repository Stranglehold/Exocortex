# Injection Chain — Pre-Deployment Investigation Results
## Kestrel → Opus, 2026-05-17
## Re: injection_chain_predeployment_20260517.md

---

## Constraints (read first)

Jake stopped both containers (`exocortex_v16`, `exocortex_v17` — Exited 27 min before I started) and closed the llama.cpp server. So:

- **Task 1 (live extraction):** Done via *static code analysis of the generators/injectors* + a *real persisted sample* from v16's `staging.jsonl` (pulled via `docker cp`, which works on stopped containers). This is actually higher-fidelity than a single live dump — the code is ground truth for the shape, and I have one real production snapshot to confirm realistic sizes.
- **Task 2 (format test against Qwen3.6):** **BLOCKED** — server down. Exact ready-to-run payload + methodology below for when it's back.
- **Task 3 (framework scan):** Done.

No production behavior changed. Nothing deployed. No generators modified.

---

## Task 1 — Data Shapes

### `_reasoning_state` (written by `_49_reasoning_state_update.py`, injected by `_22`)

Structure (`_empty_state()`), **bounded by design**:

| Field | Type | Cap |
|-------|------|-----|
| `step` | int | — |
| `theory` | str | `MAX_THEORY_LEN = 120` chars |
| `tried` | list of `{approach, outcome}` | `MAX_TRIED = 6` (store); `_22` shows last 4 (`MAX_TRIED_SHOW`) |
| `current` | str | `MAX_CURRENT_LEN = 200` chars |
| `open` | str | 120 chars |
| `artifacts` | list of `{path, description, step}` | `MAX_ARTIFACTS = 12` |

**Opus's four questions, answered:**

1. **Token count.** Worst-case `_22` injection block ≈ 2,485 chars ≈ **~620 tokens**. Typical (theory + 2-3 tried + current + 3-4 artifacts) ≈ **~225 tokens**. Real idle-cycle data (below): **~37 tokens**. Well under the 1,000-token compression trigger; usually under the 500 target.
2. **`tried[]` growth.** Already capped at 6 in the store (`_49` line 261-262), injector shows 4. Your 45-150 concern is a non-issue — the cap is built in.
3. **Not applicable to reasoning state** (that's the PACE question — see below).
4. **Format cleanliness.** Clean. Every field is a truncated string. `tried` outcomes are run through `_extract_failure_reason()` which collapses tracebacks to a single error line. No raw Python objects, no multi-line dumps.

**Real production sample** — the only `_rs_entry` in v16's `staging.jsonl` (step 73, during cycle 88 BUILD):

```
Reasoning state at step 73: Theory:  | Current: code_execution_tool: [cycle_close]
Journal entry written (cycle 88, BUILD) | Failed approaches: (none)
```

150 chars, ~37 tokens. **This is the most important finding in this report:**

> **In idle-cycle production the reasoning state barely populates.**
> - `Theory` is empty — `THEORY_RX` needs the agent to emit `Theory:`-prefixed text; idle-cycle agents don't.
> - `Open` is empty — same reason (`OPEN_RX`).
> - `tried[]` is empty — idle cycles rarely hit tool failures, and only failures append.
> - Only `current` (last tool's first output line) and `artifacts` reliably populate.
>
> Compression also fires rarely: only **1** `_rs_entry` exists in `staging.jsonl` across 88+ cycles, because `_write_to_staging` only triggers on a 35% history-shrink event, and short idle cycles seldom compress.

This is not a blocker for deploying `_22` — it's a signal that the *value* of the reasoning-state injection in idle cycles is currently low (mostly artifact list + one "Current" line). It will be richer in interactive/complex multi-step tasks where tools fail and the agent reasons explicitly. The chain should still be closed, but the *payoff* in idle cycles specifically depends on a separate enhancement (populating Theory/Current deterministically rather than via regex on agent text).

### `_pace_plan` (written by `_14_pace_plan_generator.py`, injected by `_23`)

Template-driven, **static per domain**. All domains (`investigation`, `analysis`, `coding`, `planning`, `data`) = **3 steps × 4 tiers (P/A/C/E)**. Actions are fixed strings ~80-130 chars.

- Raw `_pace_plan` dict ≈ **~500 tokens**.
- `_23`'s injection block (verbatim mirror of `_14`'s `_build_injection_block`) renders **the full plan every turn**: header + all 3 steps + all 4 tiers per step + a 4-line RULES block ≈ 2,100 chars ≈ **~530 tokens, FIXED**. It does not grow or shrink; it re-emits the same ~530 tokens every single turn regardless of progress.

**Question 3 (PACE depth):** This is the real problem. Only **1 step's 1 tier** is active per turn (marked `◄ CURRENT` / `← EXECUTE THIS TIER`). The other ~11 of 12 tier-actions are dead weight every turn. **Prime compression target.**

### Combined per-turn injection budget

| Scenario | `_22` | `_23` | Combined |
|----------|-------|-------|----------|
| Real idle cycle | ~37 | ~530 | **~570** |
| Typical interactive | ~225 | ~530 | **~755** |
| Worst case | ~620 | ~530 | **~1,150** |

PACE is the dominant, fixed cost. Reasoning state is small and variable.

### Empirical confirmation the chain is inert

Scanned 15 most-recent `chat.json` files from v16: **0** contain `[PACE PLAN` or `[REASONING STATE` blocks. If the `before_main_llm_call` injection worked, the blocks would be in persisted history. They are not. Seam #19 / §09 confirmed in production data, not just by code reading.

---

## Task 2 — Format Test (BLOCKED — server down)

Ready to run the moment llama.cpp is back. Two payloads — one neutral, one stress (with the real block format `_22` produces):

```bash
# Test A — does the model USE the reasoning state or RESPOND TO it?
curl -s -X POST http://localhost:1235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen","max_tokens":250,"stream":false,"messages":[{"role":"user","content":"[REASONING STATE — step 5]\nTried: search_engine: homomorphic encryption libs → 3 results returned\nTried: cat /a0/usr/Exocortex/interests.md → done\nCurrent: code_execution_tool: writing field report draft\n[ARTIFACTS — files created this session]\n  /a0/usr/Exocortex/field-reports/2026-05-17_he.md (Markdown doc)\nThese files exist on disk. Check them before rebuilding.\nUpdate your theory if your understanding has changed. Do not retry approaches listed in Tried.\n\nContinue working on the homomorphic encryption field report."}]}'

# Test B — PACE block (full, as _23 currently emits it) + same task
# (build from _23 _build_injection_block output for the investigation template)
```

**Grading:**
- ✅ USES it: continues from "writing field report draft", does not re-search, does not re-cat interests.md
- ❌ RESPONDS TO it: "I can see from the reasoning state that I'm on step 5…" (meta-commentary)
- ⚪ IGNORES it: starts over as if the block weren't there (wasteful but safe)

If ❌: try `<reasoning_state>…</reasoning_state>` XML delimiters, and/or add a system-prompt line ("The reasoning state block shows your prior progress. Use it; do not comment on it."). The `_22` block already ends with an imperative ("Do not retry approaches listed in Tried") which is the right instinct — keep that regardless.

I recommend this test gates the deploy. It's 2 curl calls; 10 minutes once the server is up.

---

## Task 3 — Framework Scan

Searched `research/` and `specs/`. Findings:

- The `[REASONING STATE — step N]` and `[PACE PLAN — ACTIVE]` formats are **the project's own deliberate design**, specified in `specs/REASONING_PERSISTENCE_PACE_DESIGN_NOTE.md` (the format block there matches `_22`/`_49` exactly). `_22`/`_23` implement the spec faithfully.
- `research/HERMES_AGENT_ANALYSIS.md` and `research/AGENTIC_HARNESS_LANDSCAPE_FULL.md` do **not** document a competing cross-turn reasoning-persistence format worth adopting over ours — no scratchpad/state-injection schema called out.
- No evidence in the repo that Claude Code's compaction or OpenSpace's skill-context carry use a published format we should copy. Our design note *is* the prior art here.

Net: no reason to change the format on external-precedent grounds. The format question is purely empirical (Task 2).

---

## Recommendation

**Split decision — they are not the same risk:**

1. **`_22` reasoning-state injector — deploy as-is.** Small (~37-620 tokens), bounded by design, clean, ends with an imperative. The only concern is *under-population* in idle cycles (Theory/Open never fill), which is a separate deterministic-extraction enhancement, not a deploy blocker. Closing the chain is strictly better than the current inert state.

2. **`_23` PACE injector — compress before deploy.** Change `_build_injection_block` (in `_23` only — leave `_14` alone) to emit:
   - Header (task / domain / step X of N / active tier)
   - **Only the current step**, with **only the active tier's action** marked `← EXECUTE`, plus a one-line "(other tiers available on escalation)"
   - The 4-line RULES block

   That drops ~530 → ~150 tokens (~70% cut) and removes ~11 irrelevant tier-lines per turn. The full plan is recoverable from `agent._pace_plan` for the Supervisor; the *model* only needs the current move.

3. **Gate both on the Task 2 format test.** It's cheap and answers the one question static analysis can't: does Qwen3.6 *use* the block or *narrate* it. Run it the moment the server is back, before flipping these on in production.

Deliverable artifacts saved alongside this note: real `staging.jsonl` sample at `D:/tmp/pace_probe/` (not committed — transient probe data).

— Kestrel

*Investigated with both containers down and the server closed. Static analysis + one real persisted sample carried the load. The code is the ground truth for shape; the sample confirmed the sizes are even smaller than the caps allow.*
