# Kestrel → Opus — A0 v1.20 Upgrade, the model=/ Root Cause, and Where the Learning Loop Stands

**Date:** 2026-06-20
**From:** Kestrel (Opus 4.8, Claude Code)
**Re:** Both containers upgraded to A0 v1.20; a stale-cache bug worth knowing; status of "agent learns from its mistakes"; recommendation for what's next.

---

## 1. What got done

**A0 v1.18 → v1.20 staged upgrade, both containers (v16 + v17), full stack healthy.**

- Re-based the only two overwrite-patches v1.20 actually changed: `agent.system.main.solving.md` + `agent.system.main.tips.md` (merged our deltas onto v1.20 stock — kept our Step-0 input classification + tool-schema guards, took v1.20's coding/verification discipline + document_query/OCR section). Verified against v1.20's 221-file diff that **every other** overwrite-patch (extract_tools, memory_consolidation, model_config, communication.md, browser_agent, captcha_solver) is untouched by v1.20 → re-applies clean.
- Bumped `A0_VERSION` pin v1.18 → v1.20 (the install preflight guard now passes).
- `install_all.sh` ran clean on both: guard ✓, 31 layers, exit 0. Merged prompts deployed, extract_tools JSON-fallback restored, verify-before-log gate live.
- v17 done the same way: FF'd its clone (preserving runtime drift — its `config.json` is the live runtime file, not clobbered), installed, restarted.

## 2. The bug worth knowing about (for next time you upgrade)

After install, v16 returned `litellm.BadRequestError ... model=/` on every turn — empty model string. I burned real time treating it as a config problem before finding the real cause, so logging it:

**Root cause: stale in-memory code.** When Jake ran the A0 update, A0 booted and loaded the **stock v1.20** `_model_config` helper into memory. Our `install_all.sh` then re-patched the helper *on disk* (restoring our variable-model-architecture fallback) — but **install doesn't restart A0**, so the live process kept the stock helper. Stock v1.20 has no fallback, so the agent0 profile's identity-less `chat_model` (it carries only a kwargs overlay by design) resolved to empty → `model=/`.

**The diagnostic tell that would've saved the time:** standalone resolution (`docker exec … python3 -c "build_chat_model(mock_agent)"`) returned the *correct* `lm_studio/Qwen3.6-27B-Q4_K_S`, but the live turn failed. **Same config + same on-disk code, different result live vs. standalone = stale in-memory code.** Instrumenting the extension confirmed it: the debug line never fired, because the running process wasn't using the patched file. `docker restart` fixed it instantly — PONG.

This is the extension-class-cache lesson one layer down: it bites **plugin helper modules**, not just extension classes. I've added a CRITICAL playbook entry: *after `install_all.sh` on a freshly A0-updated container, restart A0.* Folded the cost-free verification method in too (mock agent0, assert `model_name` is `provider/name` not `/`) so we never burn a v17 DeepSeek call just to confirm wiring.

**Architectural note for you:** v1.20 rearchitected the model/settings system substantially — `helpers/settings.py` is gone, model config is now a preset-based plugin (`presets.yaml`, `get_chat_model/start` function-hooks, a startup migration). Our `model_config.py` re-base patch is **not** obsolete — v1.20 still uses `helpers/model_config.py` and our variable-model fallback applies cleanly there. But the new preset/migration surface is worth a proper read before we lean on it further. The migration only fires from *populated* legacy `settings.json` fields, which we don't have — so the global `config.json` override is doing the work, and it works.

## 3. Where we stand: both containers

- **v16** — A0 v1.20, Qwen3.6-27B-Q4_K_M local via turbo3 (:1235), full stack, model resolving, idle disabled (Jake flips to true when ready).
- **v17** — A0 v1.20, DeepSeek V4-Pro, full stack, model resolves (`deepseek/deepseek-v4-pro`, verified cost-free), idle paused for cost.
- Swappable-model design confirmed working: identity lives in **one** place (global `config.json` `chat_model.name`/`api_base`); agent0 carries overlay only; the fallback connects them. Swap = edit one field + restart.

## 4. The thing Jake actually asked about: does the agent learn from its mistakes?

Verified live on v16. **Path A is real and firing:**
- `_45_failure_lesson_capture` (handle_exception/end, deterministic, zero-cost) — **5 failure lessons on disk**, each with `.memory.md` recurrence tracking: terminal-session-hung, search-engine-interactive-prompt, import-error, text-editor-interactive-prompt, oversized-tool-write.
- `_24_skill_surfacer` surfaces them at planning time (meet the lesson before repeating the mistake).
- Supervisor false-recovery detector (learns from its own repair history).

**The open half, with the number that makes the case:** the journal shows **10,418 cycles at `skills_captured: 0` and 11 at `skills_captured: 1`.** Path A only fires on exceptions, and failures are rare — so the agent learns from mistakes but **not from its successes.** 10,418 clean research cycles produced almost no reusable methodology. That's **Path B Skill Capture** (Priority 4): mine successful cycles for skills. It's the architectural completion of the learning loop, and both V16 and V17 independently asked for it in their reflections.

## 5. Recommendation for what's next

In priority order, with reasoning:

1. **Path B Skill Capture** — closes the learning loop Path A only half-covers. Highest leverage for "the agent compounds." Needs a design pass from you: it's LLM-gated (per-container cost flag), and the hard part is the *extraction quality gate* — what makes a successful cycle worth distilling vs. noise. This is a spec-first item; I'd value your frame on the gate criteria before I build.
2. **Affect Layer Phase 2** — 12,500+ traces already collected. Pure calibration: fit FRUSTRATION/DESPERATION thresholds, flip from classify-only to intervene. Fastest win on the board, closes a half-open loop.
3. **API Cache Optimization** — concrete ~$370/mo on v17. Spec exists. We're already in the cost headspace.

My lean: **Path B** if you want to design, **Affect Phase 2** if we want a fast closed loop this week.

## 6. Open questions for you

- **Path B gate criteria** — what's the deterministic-or-cheap signal that a successful cycle contains reusable methodology? (Don't want an LLM call per cycle; want a pre-filter that earns the call.)
- **Decision Log** — DEC-029..037 are still informal; I renumbered the new ones to 038-040 earlier. Want me to backfill the formal log as part of the next arc, or is that yours?
- **v1.20 preset system** — worth a proper design read before the next model-routing work, given how much it changed. Flag if you want me to write it up.

— Kestrel

*Verified live, not recalled: extension paths, the 5 failure lessons, the 10,418/11 skills_captured split, both containers' model resolution. The model=/ time-sink became the playbook's newest CRITICAL entry — same filename is not the same file, and same disk code is not the same running code.*
