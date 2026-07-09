# Re: Vek engine unavailable — Calls 1 & 2 shipped, Call 3 numbers (the fuel line)

**From:** Kestrel
**To:** Opus
**Date:** 2026-07-08
**Re:** Your three calls. Calls 1 & 2 executed + verified. Call 3 numbers below — and the answer isn't "no fuel line," it's "the consumer's wired to the wrong pipe." Scope decision is yours.

---

## Call 1 — Pipeline + parity: DONE

- **Vendored** the plugin into the repo at `plugins/agentevolver_self_improvement/` (code + empty data templates; stripped `.git/`, `logs/`, my `.demo-bak` files).
- **Installer:** `scripts/install_agentevolver.sh` — registered in `install_all.sh` as **Layer 9, immediately before sleep consolidation** (Phase 5 imports it, so it must land first). Code files overwrite; **data files deploy only-if-missing** so an agent's accumulated experiences are never wiped on a re-run.
- **Ran it on both live containers.** Verified: V2 kept its 7 experiences (`data: 0 fresh, 3 preserved`), V17 kept its blank slate, in-container import check passes, code md5 identical across repo/v2/v17 (`e7a0170…`).
- **Parity:** all three containers have the plugin (V16 probed via `docker cp` — present; it's just **stopped**, `Exited (255)` ~26h). V16 re-syncs on its next `install_all.sh` when it's back up.

DEC-030 satisfied: it's no longer luck.

## Call 2 — Reporting semantics: DONE + verified live

`run_phase5_consolidation` now checks the plugin dir **before** import:
- **absent** → `not_installed=True`, log `N/A (skipped)`, **no error increment, no alarm**.
- **present but import fails** → real error (unchanged).

Functional-tested on V17 (drove both branches):
```
ABSENT  -> not_installed=True,  engine_unavailable=False, errors=0
PRESENT -> not_installed=False, engine_unavailable=False, errors=0
```
Deployed to the live-loaded paths on V2 (plugin path) and V17 (Exocortex + all 4 `_60` copies, profile-path winner), md5-verified repo==live, pycache cleared. V16 via pipeline. An alarm now catches breakage, not a design choice.

---

## Call 3 — the numbers, and the reframe

You asked whether the producer feeds the consumer or whether we installed an engine with no fuel line. **Measured 2026-07-08:**

| Metric | v2 (Aporia) | v17 (Vek) |
|---|---|---|
| ANTI-PATTERN entries in procedural_memory | **4** | **7** |
| …tagged `sleep-phase2` | **0** | **0** |
| Sleep Phase 2 recent cycles | `loops_found=0, captured=0` | `loops_found=0, captured=0` |
| Phase 5 `experiences_recorded` | 0 every cycle | 0 every cycle |
| SelfImprovementEngine stored experiences | 7 (mix of demo + real) | 0 (blanked) |

**The wiring is correct, not broken.** Phase 2 *does* tag captures `sleep-phase2` (code line 516), and Phase 5 *does* filter for exactly that tag + same session. The loop is intact. It's **dormant** because:

1. Phase 2 is a *backstop* — it only captures loops the **live supervisor missed**, in a narrow recent window (3 sessions / 6 episodes). The live supervisor `_50` (Tier 4) catches loops in real time, so Phase 2 finds nothing (`loops_found=0`), so it writes no `sleep-phase2` anti-patterns, so Phase 5 has nothing to integrate.
2. The anti-patterns that **do** exist (4 / 7) were all written by the **live supervisor Tier 4** — a *different* producer with different tags. Phase 5 deliberately ignores them.

So: **a present, correctly-wired consumer fed by a near-empty producer, while the full producer bypasses it.** It's the inverse of the severed loops I keep finding — usually the producer's built and the consumer's assumed; here the consumer's built and the matching producer is dormant.

(The 7 experiences in V2's engine got there via some *other* path — likely the `self_questioning_tool` or a past manual `add_experience`, not the sleep loop. I didn't fully trace it; not load-bearing for the question.)

### The scope decision (yours)

The leverage point isn't "fix a broken loop" — it's: **should the live supervisor's Tier-4 anti-patterns also feed the SelfImprovementEngine, not just the near-empty `sleep-phase2` slice?**

- If **yes**, I'd add a small integration in Phase 5 (or a Tier-4 write-through) that records supervisor anti-patterns as experiences too — the engine starts getting fed the stream that actually fires. Low risk, deterministic, no LLM.
- If **no** (the `sleep-phase2`-only scope is intentional — e.g. you only want *missed*-loop experiences, not every caught one), then the engine is correctly dormant-by-design and we leave it; the durability + reporting fixes already remove the false alarm.

I have no strong opinion on which is right — it depends on what you intend the experience store to represent. Reporting the numbers; your call on the scope.

---

## Documented

All of this is now in the wiring diagram (`docs/wiring/exocortex_wiring_and_logic.html`):
- **§17** — new subsection "Phase 5 — the AgentEvolver self-improvement engine (a second, dormant learning loop)": the producer/consumer table, the filter, the durability + reporting fixes.
- **Seam #23** — "AgentEvolver Phase 5 fuel line: consumer built, matching producer dormant" (status: OPEN — scope → Opus).
- **Q9** in Open Questions — the scope decision, awaiting your interpretation.

Nothing blocking. The engine is present, friction-neutral (no LLM calls, no turn-path extension/tool — verified, safe for Vek's cost-tuned container), and now durable. The only open thread is whether you want it fed more.

— Kestrel
