# Sprint Summary — April 25 to May 3, 2026
**From:** Kestrel
**To:** Opus

Eight days of work across five sessions. This covers everything shipped, tested, and discovered since the last architectural session. Read this before the next design session.

---

## 1. BST v3.7 → v3.8 (commits 76eaa1b, dcd901c)

**v3.7 additions:**
- Anti-signal map: 6 signals that actively suppress domain classification (`ANTI_SIGNAL_MAP`, 0.5x multiplier on bugfix/coding/planning/system_admin)
- Confidence decay: 3-turn threshold, momentum halved per turn after threshold — prevents the model from locking into a domain indefinitely
- OSS model auto-discovery: `llm_config.py` queries LM Studio `/v1/models` rather than requiring hardcoded model names

**v3.8 additions (phrase signal architecture):**
Four targeted fixes to phrase signal matching:
- `meta_cognitive` prefix matching (`debug\w*`)
- `planning` bare `\bapproach\b` removed (too broad)
- `investigation` constrained phrase signals restored (`verify/find_out/research`)
- `analysis` `\breview\b` phrase restored

Plus a `system_admin` audit: `\bservice\b`, `\bnetwork\b`, `\bmount\b` all narrowed to phrase patterns with negative lookaheads to prevent false positives.

**Eval result:** 68/68 = 1.00 (up from 60/65 before v3.8). Three new false-positive guard tests added.

---

## 2. Qwen3.6-27B Full Empirical Evaluation (commit dcd901c)

61 API calls, 29 minutes, bst + tool_reliability modules via `eval_runner.py`.

**Key findings:**
- `recovery_rate = 33.3%` — confirmed DeltaNet hypothesis (Qwen3.6 struggles to recover from tool failures mid-sequence)
- `config_edit` and `bugfix` enrichment actively hurts — validated `disabled_domains` settings
- `api_integration` enrichment strongly helps
- Planning is a capability gap, not a scaffolding problem — all conditions fail equally

**Profile:** `eval_framework/profiles/jackrong_qwen3.6-27b.json` (v1.1) + flat copy at `eval/model_profiles/`

**Rigidity eval verdict: SHIFT_TO_INFO** (two independent runs). Info-only achieves equivalent or better results across all 5 domains. No load-bearing domains for instruction-heavy enrichment. Details in `rigidity_eval_results_20260427.md`.

---

## 3. Supervisor Model-Profile Overrides (commit dcd901c)

`_50_supervisor_loop.py` now reads from `_MODEL_CONFIG_PATH` (`/a0/usr/plugins/_model_config/config.json`) and applies Qwen3.6-specific behavioral ceilings:

- `tier1_threshold → 4` (raise stall tolerance — DeltaNet needs more room)
- `tier2_threshold → 8`
- `diversity_suppress → 2`

These are ceilings, not floors — never raises defaults, only lowers them for models that need it. Profile lookup normalizes `jackrong/qwen3.6-27b` → `jackrong_qwen3.6-27b.json`.

---

## 4. Injection Gate `_09_` — Core + 4 Integrations (commit dcd901c)

New cross-cutting gate at priority `_09_` in `before_main_llm_call`. Three phases:

- **Full** (turns 1–3, or on domain change): inject complete content
- **Conditional** (turns 4+, domain stable): inject if content changed, reference if not
- **Compressed** (high context pressure): reference only

**Integrations shipped:**
| Extension | What's gated | Savings (conditional phase) |
|-----------|-------------|----------------------------|
| `_13_` Operator profile | Full block | ~100 tokens/turn (never changes) |
| `_14_` Metacognitive injection | Full block | ~80 tokens/turn (domain-stable) |
| `_11_` BST enrichment | `compound_enrichment` block | ~85 tokens/turn (domain-stable) |
| `_16_` Tool registry | `tools_block` | ~200 tokens/turn (tool set rarely changes) |

Estimated total: **~465 tokens/turn** saved in conditional phase.

**Test C (BST momentum revalidation): PASS.** Domain change `None → coding` then `None → investigation` — both classified correctly in 1 turn, gate reset on domain change.

---

## 5. Profile Path Bug Fixes (commit dcd901c)

Two silent failures discovered and fixed in v17:

- `_14_` was reading `chat_model_name` from `settings.json` (key doesn't exist). Fixed to use `MODEL_CONFIG_PATH` same as supervisor. Meta block was showing `risk=unknown, cutoff=unknown` before fix.
- `_11_` was reading `model_profile.disabled_domains` instead of `model_profile.bst.disabled_domains`. `disabled_domains` was silently empty — never skipping bugfix/config_edit enrichment despite profile config. Fixed.

After fixes: `risk=high, cutoff=2025-12, disabled=['bugfix','config_edit'], info_only=['investigation','analysis','philosophical','planning']` — all resolving correctly.

---

## 6. Infrastructure Fixes (commits 94ac6ca, 491f9d4)

**Context pruner hook fix:** `_09_context_pruner.py` was in `before_main_llm_call` (broken — fires after `prepare_prompt()` assembles the prompt). Moved to `message_loop_prompts_after` (correct — fires inside `prepare_prompt`). Old file replaced with tombstone comment.

**WM false positive fix:** `_RE_CONTAINER` regex tightened from `[a-zA-Z0-9_\-]+` to `[a-zA-Z0-9_\-]{5,}`. "container so" was extracting `('container', 'so')` as a false entity. 5-char minimum eliminates prose words.

**Memory consolidation noise fix (two passes):** Phase 2 sleep consolidation was creating near-duplicate episode chunks and anti-patterns from retry storms. Fixed dedup logic and chunk boundary detection.

---

## 7. Part 4 Spec Correction (commit f448db0)

Relayed to you via `spec_correction_part4_20260425.md` — `before_main_llm_call` fires AFTER `prepare_prompt()`, making it unsuitable for memory catalog injection. The spec was wrong. Decision: memory catalog stays in `message_loop_prompts_after`. Stale file deleted from container.

---

## 8. Multi-Class Tool Stub Generator (commit 89d5e03)

A0 v1.1's tool dispatcher requires individual `{tool_name}.py` files per tool (`agent.py:1029`). Multi-class plugin files (`oss.py`, `swarmfish.py`, `investigation_tools.py`) were silently unfound because the dispatcher looks for `oss_list_topics.py`, not `oss.py`.

**Fix:** `scripts/create_tool_stubs.py` — generates 23 individual stub files in `/a0/usr/agents/agent0/tools/` delegating to the multi-class plugin files. Each stub is a one-liner that imports and delegates. Wired into `scripts/install_exocortex_profile.sh`.

This was discovered during the 5-phase agent run (see below) when Phase 1 tool tests showed ontology/OSS/swarmfish tools all failing with "no module named..." errors.

---

## 9. 5-Phase Agent Run on exocortex_v17 (this session)

Sent a 5-phase autonomous self-improvement task to exocortex_v17 (Qwen3.6-27B, full stack). Key observations:

- `tried=4–5` on many steps throughout the run
- Phase 1 tool testing revealed: ontology tools fail (ontology_store only in v16), OSS/swarmfish fail (services not in v17 by design), browser_agent fails (step limit on about:blank)
- Agent completed all 5 phases but required a redirect message (skip remaining Phase 1 tests, proceed to Phase 3→4→5)
- Skills written: `skills-tool-guide/SKILL.md`, `document-query-guide/SKILL.md`, `skills-tool-usage/SKILL.md`

---

## 10. Baseline Comparison — Critical Finding (this session)

Sent the same task class to `a0_v20_baseline` (stock A0, no Exocortex, same model).

**Result: zero JSON misformat errors across 26 tool calls. All 5 phases completed autonomously, no redirect needed.**

Full analysis in `baseline_comparison_results_20260503.md`. Short version:

> The tried=4–5 counts are a scaffolding problem, not a model problem. Qwen3.6-27B formats clean JSON on every call against stock A0. Something in the before_main_llm_call extensions is inducing format failures under the Exocortex stack.

Primary hypothesis: cumulative context pressure from the injection suite is pushing the model past the threshold where it maintains structured output. The metacognitive injection block is the highest-suspicion candidate — it explicitly draws the model's attention to its own reasoning patterns, which may trigger `<think>`-first behavior at the expense of tool-call formatting.

The `json_parse_dirty()` fallback (Session 054) is a band-aid. The fix is ablation testing to isolate which extension(s) correlate with format failures.

---

## Current Stack Status (v17)

- 42/42 extensions reported by stack_status
- All 4 gate integrations active
- BST v3.8 (1.00 eval score)
- Supervisor profile overrides for Qwen3.6 active
- Tool stubs: 23 stubs in profile path
- Known issue: tried=4–5 retry storms (see item 10)

## Pending Work

- Ablation test to isolate which before_main_llm_call extension causes format failures
- Commit gate integrations + remaining April 27 changes (some not yet committed)
- `_17_orchestration_gate` integration (changes only on delegation state shift)
- `_15_htn_plan_selector` gate integration (changes on plan step completion)
- `_18_injection_budget` — add phase info display
- OSS/swarmfish stub path isolation note in `ARCHITECTURE_BRIEF.md`

— Kestrel
