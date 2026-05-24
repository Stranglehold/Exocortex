# STRESS TEST 014 — Reasoning Persistence Chain (Dead-End Avoidance)
## Author: Kestrel — 2026-05-17
## Status: CRITERIA LOCKED BEFORE RUN. Do not edit criteria after results land.

---

## Hypothesis

Closing the inert injection chain (`_22_reasoning_state_injector` +
compressed `_23_pace_plan_injector`) causes the agent to **stop re-attempting a
dead-end approach** that has already failed, because the failed approach is
carried forward in the injected `[REASONING STATE]` `tried[]` block.

This is the ST-005 failure mode the chain was designed for: "after context
compression the agent retried approaches that had already failed because the
dead-end record was gone."

## Why this test is valid pre-GAP-001

Of the reasoning-state fields, `tried[]` populates correctly in the **current**
`_49` (appended on tool failure via `ERROR_SIGNALS`). `theory`/`open` are the
hollow ones GAP-001 fixes. This test exercises **only `tried[]`**, so it is
meaningful before the GAP-001 rework. It establishes the baseline GAP-001 will
later be measured against.

## Confound controlled

`_02_tool_signature_guardian` (Tier 1, blocks byte-identical tool calls) was
restored to v16 for cross-container parity (repo/v16/v17 md5 `6d09e633…`). It is
present in **both** the pre and post runs — held constant, not a variable. The
dead-end retry in this scenario is designed **semantically-same but
syntactically-different** (different tool/command targeting the same missing
path) so `_02` cannot mask it. What varies between runs is **only** the injector
chain. Any behavioral delta is therefore attributable to the chain, not to `_02`.

## Environment (record for reproduction)

- Model: Qwen3.6-27B-Q4_K_S, Indras-Mirror server `host.docker.internal:1235`, `enable_thinking: true`, `--reasoning off`
- Containers: exocortex_v16 (test target) + exocortex_v17 (parity, paused). Engine **disabled** (`config.json idle_time_engine.enabled=False`) — no idle cycles competing.
- Cross-container canonical parity: 0 mismatches (verified pre-run)
- v16 API: `POST /api/api_message`, port 32768 (re-check after any restart)
- Pre-deploy injector md5: absent. Post-deploy target: `_22`=`d7ed32fc…`, `_23`=`50a0bee4…` (compressed)

## Scenario

Single bounded interactive task submitted to v16:

> "Read the file `/a0/usr/Exocortex/reactor_config.json` and tell me the value
> of its `mode` field. If that exact file does not exist, the equivalent
> setting lives in the standard Exocortex config — find it there and report
> the value instead."

- **Dead-end:** `/a0/usr/Exocortex/reactor_config.json` does not exist.
- **Escape:** `/a0/usr/Exocortex/config.json` exists (the real config).
- **Terminal goal:** report a field value → the run self-terminates (bounded).
- **Expected dead-end retry shape:** `cat …/reactor_config.json` (turn 1, fails
  "No such file"), then a *syntactically different* re-attempt at the same path
  (e.g. `python3 -c "open('…/reactor_config.json')"`, `ls …/reactor_config.json`,
  `grep mode …/reactor_config.json`). `_02` won't block these (distinct
  signatures); only the reasoning chain's `tried[]` should.

## Measurement

After each run, pull `chat.json`, extract the agent's tool calls, and count
**distinct attempts whose target path contains `reactor_config.json`** after the
first failure. Also record: presence of `[REASONING STATE]` block in assembled
context, presence of the failed approach in its `tried[]`, whether the agent
reached the escape (`config.json`) and reported a `mode`-equivalent value,
total turns, any `_22`/`_23` exceptions in logs.

## Success criteria (LOCKED)

| Signal | PRE-deploy (chain inert) — expected | POST-deploy (chain live) — PASS |
|--------|--------------------------------------|----------------------------------|
| Distinct `reactor_config.json` attempts after 1st failure | ≥ 2 (the loop) | **≤ 1** (no re-attempt, or one then pivots) |
| `[REASONING STATE]` block in assembled context | absent | **present** |
| Failed `cat reactor_config.json` recorded in `tried[]` | n/a (chain inert) | **present in the injected block** |
| Reached escape, reported the config value | may or may not | **yes** (task completed via the alternative) |
| `_22`/`_23` runtime exceptions | n/a | **zero** (graceful passthrough or clean fire) |
| Compressed `_23` block intact in context (~165 tok, not mangled by other injectors) | n/a | **intact** |

## Fail surface (what makes this a real test, not theater)

If POST-deploy the agent still re-attempts `reactor_config.json` ≥ 2 times **with
the chain live and the failure present in `tried[]`**, the chain does not deliver
its core value — and we learn that before trusting it in production. A test that
could not produce that outcome would be too weak.

## Caveats on interpretation

- n=1 per side is **directional, not statistical**. A clear pre/post difference
  is informative; a marginal one is not conclusive and warrants repeat runs.
- This validates `tried[]`-driven dead-end avoidance only. It does **not**
  validate `theory`/`open` (hollow until GAP-001) or PACE adaptivity (GAP-006).
- Model nondeterminism exists even at temp 0 with thinking; one anomalous run
  on either side should trigger a repeat, not a conclusion.

## Results

(populated after execution — PRE then POST)

### PRE-deploy (chain inert, `_02` present) — 2026-05-17

- Run: chat `APBvWdkV`, HTTP 200, **elapsed 3469.6s (~58 min)** (cold cache + `enable_thinking:true`, no pre-warmer), 9 messages.
- Tool sequence: greeting → user task → `text_editor:read reactor_config.json` (**1 attempt**, fails) → `code_execution_tool: ls -la /a0/usr/Exocortex/` (investigates) → `text_editor:read config.json` (**escape reached**) → honest response (no fabricated `mode`).
- **Distinct `reactor_config.json` tool attempts after first failure: 0** (one attempt total, then pivoted).
- `[REASONING STATE]` blocks: **0** (correct — chain inert).
- Reached escape + honest report: **YES**.

**Methodological finding (decisive):** the locked PRE expectation was "≥2 reactor_config.json attempts (the loop)". Actual = 1, no loop. The agent solves the dead-end cleanly in one shot **even with the chain inert** — it does not blindly retry; it investigates (`ls`) and pivots. The ST-005 loop the chain prevents occurs specifically *after context compression in long multi-step tasks* (dead-end record lost). A 4-tool-call lookup is too short to induce compression, so there is no loop to prevent and **POST cannot discriminate** on this criterion — it would show the same clean behavior, proving nothing about the chain. Per methodology ("a test that passes without revealing anything was too easy"), this scenario as designed does not exercise what the chain fixes. See verdict for the criteria amendment.

### POST-deploy (chain live, `_02` present)
_TBD_

### Verdict
_TBD_
