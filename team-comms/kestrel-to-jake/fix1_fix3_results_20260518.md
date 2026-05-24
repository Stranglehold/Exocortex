# #1 (shrink prompt) + #3 (prefix-stability) — Results
## Kestrel → Jake, 2026-05-18

You authorized #1 and #3 as in-domain + reversible. Here's what I did, what I
found, and — honestly — where the line is between "safe to do autonomously"
and "your capability call."

---

## #3 — Prefix-stability hardening: COMPLETE & VERIFIED (no further changes needed)

Comprehensive cache-safety audit of every injecting hook:

- **All dynamic per-turn extensions write to `extras_*`** (BST `_11`, completion
  `_12`, PACE `_14`, htn `_15`, karpathy `_15`, heartbeat `_21`, memory
  `_55`/`_56`, and `_08` after the fix). `prepare_prompt` appends `extras`
  **after** history → tail → **cache-safe by architecture**.
- **The only prefix-region writer is `_15_exocortex_stack`** — it appends two
  static files (`agent.system.model_awareness.md`, `agent.system.capabilities.md`).
  Verified: both have **zero volatile placeholders** → static → cache-safe.
- **`_08_step_budget_tracker` was the one real violator** (mutated
  `history_output[-1]` with a per-turn `[Step N/M]` tag inside the cacheable
  region). Fixed last session: now writes to `extras_temporary` (tail). Deployed
  both containers, md5 `88615489374430e026241ecfbe9cf44e`, reversible.

**Conclusion:** post-`_08`, the injection architecture is cache-safe. There are
no other prefix violators. #3's deliverable is the `_08` fix + this verification
— I am explicitly **not** manufacturing further changes, because the correct
result is "it's clean," not "I edited more files."

---

## #1 — Shrink the prompt: accurately measured, and the honest tradeoff

I had to correct myself twice here (segmentation-marker artifacts gave wrong
numbers — flagging that openly). The **accurate** decomposition of the
~13,600-token assembled prompt:

| Component | ~tokens | % | Owner |
|---|---|---|---|
| **Tool documentation (20 tools, all `agent.system.tool.*.md`)** | **~7,226** | **~53%** | core A0 (capability) |
| Skills-system intro + behavioral/role/communication/problem-solving | ~2,400 | ~18% | core A0 |
| agent_info (extras tail) | ~1,555 | ~11% | core A0 |
| injected memories + solutions + datetime (extras tail) | ~800 | ~6% | Exocortex (tunable) |
| Exocortex static blocks (`_15`: model_awareness+capabilities) | ~360 | ~3% | Exocortex |
| remainder | ~1,250 | ~9% | mixed |

The dominant mass is **~7,226 tokens of tool docs injected every single turn**,
for 20 tools. Per-tool (top): browser ~1,552, code_exe ~701, skills ~678,
swarmfish ~613, autoresearch ~607, text_editor ~515, scheduler ~350,
document_artifact ~314, swarmfish_panel ~305, document_query ~273, a2a_chat
~227, call_sub ~212, + 8 smaller.

### Evidence-based dead-weight candidates (your capability call, not mine to gut)

- **scheduler (~350 t):** zero references in idle activation / self-improvement
  / skills / services. The idle engine uses its own daemon, never A0's scheduler.
- **a2a_chat (~227 t):** CLAUDE.md states A2A is *"speced, not deployed."*
  Documenting an undeployed tool every turn is pure dead weight.
- **swarmfish + swarmfish_panel (~918 t):** workflow-specific prediction tools;
  not used in idle/autonomous cycles (used in explicit SWARMFISH sessions).
- **browser (~1,552 t):** largest single tool doc; idle research *may* use it —
  needs your judgment on whether autonomous cycles browse.

Removing just the clearly-unused (scheduler + a2a_chat + swarmfish pair) ≈
**~1,495 tokens (~11%)** off *every* prompt, every turn, near-zero capability
risk. Including browser if idle doesn't browse ≈ ~3,000 t (~22%).

### Why I did NOT autonomously do it

Removing a tool's doc removes the model's ability to use that tool. That's a
capability decision (CLAUDE.md: skills/tools are load-bearing; "don't degrade").
The agreed bar for autonomous action was *no capability/quality loss*. Tool
curation fails that bar — it's exactly the kind of "interesting but the question
is does it map to a measured need" call that's yours. The genuinely
autonomous-safe trims (memory injection count, minor Exocortex prompt tightening)
are marginal (~hundreds of tokens) and the memory one is quality-sensitive
(recall), so I won't trade recall for ~150 tokens without your sign-off either.

### The mechanism (so the decision is executable)

`_11_tools_prompt.build_prompt()` globs **all** `agent.system.tool.*.md` across
prompt dirs and concatenates them into the system prompt. To drop a tool's docs:
remove/rename its `agent.system.tool.<name>.md` from the loaded prompt dirs (and
ensure the tool itself is unregistered if it should be fully gone). Fully
reversible (restore the file). I can execute precisely once you pick the set.

---

## Recommendation

1. **#3 is done** — architecture verified cache-safe; `_08` fix carries it.
2. **#1: you choose the tool-doc set to drop.** My evidence-backed default:
   scheduler + a2a_chat + swarmfish + swarmfish_panel (~1,495 t, ~11%, near-zero
   risk). Add browser (~1,552 t) if autonomous cycles don't browse. I'll execute
   the exact removals (reversible, both containers, md5-verified) and re-measure
   the assembled prompt + a 2-turn latency delta the moment you pick.
3. This stacks with the real rocket ship (fix #2, out-of-band keepalive) and the
   shrink is linear: ~11–22% fewer prompt tokens → ~11–22% off every cold prefill,
   compounding with keepalive once that's built.

No changes deployed in this step beyond the already-in-place `_08` fix. System
state unchanged and clean.

— Kestrel
*Measured wrong twice, corrected both times, before recommending. The number
that survives scrutiny is the only one worth acting on.*
