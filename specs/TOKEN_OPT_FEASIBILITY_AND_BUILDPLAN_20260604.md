# Token Optimization — Feasibility Assessment & Buildplan
**Author:** Kestrel · 2026-06-04 · v17 (DeepSeek)
**Assesses:** `specs/DEEP_TOKEN_OPTIMIZATION.md` (Opus) against the *running* v17 system.
**Method:** verified every lever against live config + A0 1.18 source, not the spec's assumptions.

---

## TL;DR — the baseline already moved

Two of the spec's six levers are **already pulled** on v17, so the spec's "$5/day → $0.25/day, 95%"
math double-counts savings already banked. The real remaining wins are **model routing** and a
newly-discovered **thinking-suppression** gap.

| Lever | Spec claim | Verified reality | Status |
|---|---|---|---|
| 1. Cycle interval | 5→30min, ~83% | already `idle_threshold`/`min_gap` = 1800s | ✅ done |
| 2. Prefix stability | highest-leverage; hunt mid-prefix mutation | system prefix is byte-stable; Exocortex injects only to tail extras; **measured 74.5% cache hit** | ✅ satisfied by architecture |
| 3. Thinking routing | Think→Non-think MAINTAIN, 40-60% | `enable_thinking:false` already set — **but DeepSeek ignores it (98% of output is reasoning tokens)** | ⚠️ real gap, see Lever 3′ |
| 4. Model routing | Flash for MAINTAIN | still Pro everywhere | 🟢 build it (held for model config) |
| 5. History mgmt | truncate growing context | each cycle = fresh context, bounded by step budget | 🟡 minor |
| 6. Semantic cache | future | — | ⚪ defer |

**Rotation-math correction:** spec says MAINTAIN ≈60% of cycles. The state machine
(`idle_watch._select_cycle_type`) runs **3 MAINTAIN → 5 BUILD → 1 EXPLORE** = MAINTAIN 33%,
BUILD 56%, EXPLORE 11%. Routing only MAINTAIN→Flash cheapens 33% of cycles; the big win needs
routine-BUILD→Flash too.

---

## What shipped this session (deployed to v17, verified)

### Cache-ratio instrumentation — DONE
- `extensions/python/before_main_llm_call/_02_cache_metrics_logger.py` — registers a litellm
  `CustomLogger` once per process; writes every chat call's real `usage` to
  `/a0/usr/Exocortex/cache_metrics.jsonl`. Zero behaviour change, never raises.
- **Key result:** DeepSeek returns `prompt_cache_hit_tokens` / `prompt_cache_miss_tokens`
  (and `prompt_tokens_details.cached_tokens`) **natively, without `include_usage`.** The
  feared `_parse_chunk` core-patch is **unnecessary** — scrapped.
  - A0 1.18's own stream loop reports output tokens via `approximate_tokens()` (an estimate)
    and never reads `usage` — which is why a litellm callback (not a `chat_model_call_after`
    extension) was the right capture point.
- `scripts/cache_metrics_report.py` — the consumer. Aggregates hit ratio + est. cost per model.
  Run: `docker exec exocortex_v17 /opt/venv-a0/bin/python3 /a0/usr/Exocortex/cache_metrics_report.py`
- **First data (3 validation calls):** 74.5% cache hit; 98% of output tokens are reasoning.

### v17 idle — enabled (cadence 30/30 min) so real cycles accrue data.

---

## Lever 3′ — the thinking-suppression gap (NEW, highest-value, Jake's domain)

Measured: `enable_thinking: false` is in v17's `_model_config`, yet `reasoning_tokens` ≈
`completion_tokens` on every call (98%). The `enable_thinking` kwarg is a Qwen-ism; DeepSeek V4
ignores it. **Nearly all output spend is the most expensive (reasoning) tier.** If thinking can be
actually disabled for routine cycles, output cost drops ~95% on those calls — bigger than model
routing alone.

**Action (Jake):** determine DeepSeek V4's real thinking control — likely a distinct model id
(a non-reasoning `deepseek-chat`-class model) or a `reasoning_effort`/provider param, not
`enable_thinking`. This is model config. Once known, it folds into the router below (route
MAINTAIN to a non-reasoning model id).

---

## Lever 4 — Idle Model Router (built as a held draft)

`extensions/python/chat_model_call_before/_05_idle_model_router.py` — **drafted, compile-verified,
NOT deployed.** Inert until config provides `idle_model_routing`.

**Mechanism (all verified against A0 1.18 source):**
- `call_chat_model` resolves the model per call and exposes mutable `call_data["model"]`
  via the `chat_model_call_before` hook (agent.py:790-828).
- `models.get_chat_model(provider, name, **kwargs)` builds a `LiteLLMChatWrapper` (models.py:829).
- Each idle cycle is a fresh context whose first message carries the activation sentinel +
  "Cycle type:" line → route per cycle. Real-user contexts are never touched.
- `deepseek-v4-flash` confirmed a valid endpoint model id (it's `nifty_panini`'s utility model).

**What Jake supplies (model config — not mine to author):**
```json
"idle_model_routing": {
  "enabled": true,
  "by_cycle_type": {
    "MAINTAIN": {"provider": "deepseek", "name": "deepseek-v4-flash", "kwargs": {}}
  }
}
```
**Caveat:** Flash and Pro have separate DeepSeek prefix caches; infrequent Pro cycles (BUILD/EXPLORE
>30 min apart) may pay a system-prefix cache-miss. Net still a clear win (Flash ~6-9× cheaper).

---

## Recommended sequence
1. **Measure first (now running):** let v17 idle accrue ~a full 3→5→1 rotation; read
   `cache_metrics_report.py` for the *real* per-cycle-type cost + hit ratio. This is the honest
   baseline the spec's "$5/day" predates.
2. **Lever 3′ (biggest):** Jake finds DeepSeek's true thinking control; route routine cycles to a
   non-reasoning model.
3. **Lever 4:** add the `idle_model_routing` config block; deploy the router (already drafted).
4. Re-measure; iterate model/threshold from the ledger, not projections.

## Not done / explicitly out of scope this session
- No model config authored (Jake's domain — Lever 3′/4 configs).
- Router NOT deployed (held for config + approval).
- No `_parse_chunk`/`include_usage` core patch (proved unnecessary).
