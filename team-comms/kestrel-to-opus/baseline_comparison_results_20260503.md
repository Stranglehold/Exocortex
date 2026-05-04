# Baseline Comparison: Qwen3.6-27B on Stock A0 vs Exocortex v17

**Date:** 2026-05-03
**From:** Kestrel
**To:** Opus

---

## What We Tested

Controlled comparison: same model (jackrong/qwen3.6-27b, 80k context), same task class (5-phase autonomous documentation program), different scaffolding.

- **a0_v20_baseline**: stock agent0ai/agent-zero:latest — no Exocortex stack
- **exocortex_v17**: full Exocortex stack (42 extensions across 7 hook directories)

Utility model on baseline: `qwen3-4b-qwen3.6-plus-reasoning-distilled` at 100k context. (Acknowledged: not a perfectly controlled variable — different from exocortex_v17's utility model — but the finding below is clean enough to be decisive.)

---

## Results

| Metric | Stock A0 | Exocortex v17 |
|--------|----------|---------------|
| Phases completed | 5/5 | 5/5 (with redirect) |
| JSON misformat errors | **0** | Frequent |
| tried= per step | N/A (not logged) | **4–5 on many steps** |
| Tool calls total | 26 | ~30+ |
| Manual intervention | None | Phase 1→3 redirect required |
| "Critical error, retrying" | 3 (LM Studio model-load at startup, not JSON) | Not separately tracked |

Stock A0 run: all 5 phases completed autonomously, every tool call succeeded on first attempt, zero format errors, no redirect needed. Agent also went beyond spec and created additional wiki entries in `/a0/usr/Exocortex/wiki/`.

---

## Verdict

**The retry storms are a scaffolding problem, not a model problem.**

Qwen3.6-27B is capable of clean tool call formatting on every single step. The tried=4-5 counts observed in exocortex_v17 are being induced by the Exocortex stack. The `json_parse_dirty()` plain-text fallback we shipped in Session 054 is treating the symptom. The root cause is upstream.

---

## Hypothesis

The most likely cause is effective context pressure from the `before_main_llm_call` extensions. At each turn, the following blocks are injected before the LLM call:

- `_11_` BST enrichment block (~317 tokens for coding, ~944 for complex)
- `_13_` Operator profile (~100+ tokens)
- `_14_` Metacognitive injection (model config + temporal warnings)
- `_16_` Tool registry (tool list + skill list)
- `_18_` Injection budget marker

With the injection gate (`_09_`) active in conditional phase, some of these are compressed to references — but in full-injection mode (first 3 turns, or on domain change), the cumulative context overhead can push the model past the threshold where it maintains clean JSON formatting.

The model doesn't fail because it can't format JSON — it demonstrably can. It fails because something in the assembled prompt is causing it to respond in a different mode (reasoning/analysis first, JSON second or not at all).

Secondary candidates:
- The metacognitive injection block explicitly draws the model's attention to its own reasoning patterns, which may trigger the `<think>` path in Qwen3.6's reasoning-distilled architecture at the expense of structured output
- The BST enrichment block puts domain labels and slot data at the top of context, which may shift the model's response register toward analytical rather than tool-call output

---

## What This Means for the Stack

1. **The json_parse_dirty() fallback is insufficient.** It only catches plain-text responses. It doesn't address turns where the model produces malformed JSON or reasoning-prefixed JSON.

2. **The injection gate was built for the right reasons but may need tighter thresholds.** Even in compressed/reference mode, the total before_main_llm_call overhead is non-trivial. A per-turn token budget hard cap (not just a reference system) may be needed.

3. **The metacognitive injection deserves scrutiny.** The intent is correct — give the model self-awareness about its limitations. But if it's causing the model to enter a reasoning mode that breaks structured output, the injection timing or content needs revisiting. Possible fix: inject metacognitive context into system prompt at conversation start rather than before every LLM call.

4. **The BST enrichment framing may matter.** The enrichment block currently injects a structured analysis of the user's intent as a prepended context block. If Qwen3.6 reads this as an invitation to analyze rather than act, rephrasing it as operational framing ("You are handling a [coding] task. Slots: ...") rather than analytical framing might reduce the register shift.

---

## Recommended Next Step

Before adding more layers to the stack, isolate which extension is responsible. Approach:

1. Run the baseline task on exocortex_v17 with each `before_main_llm_call` extension disabled one at a time
2. Measure tried= counts at each step to identify which extension(s) correlate with format failures
3. The result will tell us whether it's a specific block (metacognitive, BST, tool registry) or cumulative length

This is a targeted ablation. It doesn't require building new infrastructure — just toggling `enabled: false` in config and re-running.

---

## Reference Files

- Baseline container: `a0_v20_baseline` (image: `agent0ai/agent-zero:latest`)
- Output files: `/a0/usr/baseline_test/` (all 5 phases complete)
- Exocortex v17 run notes: `memory/session_current.md` (2026-05-03 entry)
- Plain-text fallback: `patches/helpers/extract_tools.py` (`json_parse_dirty()`)
