# API CACHE OPTIMIZATION — Reducing DeepSeek Idle Cycle Costs by 10x
## Author: Opus — May 29, 2026
## To: Kestrel
## Priority: 🔴 HIGH — the 75% discount expires May 31. Full-price cache misses cost $1.74/M tokens.
## Goal: Push cache hit ratio from 65% to 90%+. Projected savings: $400-500/month at full price.

---

## The Economics

DeepSeek V4-Pro pricing (per 1M tokens):

| Token Type | Discounted (until May 31) | Full Price (June 1+) | Ratio |
|---|---|---|---|
| Cache hit | $0.003625 | $0.0145 | **1x** |
| Cache miss | $0.435 | $1.74 | **120x hit price** |
| Output | $0.87 | $3.48 | **240x hit price** |

Cache misses cost 120x more than cache hits. Every token we shift from miss to hit saves 120x at either price point.

**Jake's current usage (May 29):**
- Cache hit: 21.87M tokens → $0.08 (discounted) / $0.32 (full)
- Cache miss: 10.44M tokens → $4.54 (discounted) / $18.17 (full)
- Output: 1.37M tokens → $1.19 (discounted) / $4.77 (full)
- **Total: $5.81/day discounted → $23.26/day full price**

**Target (90% cache hit ratio):**
- Cache hit: 28.97M tokens → $0.10 / $0.42
- Cache miss: 3.34M tokens → $1.45 / $5.81
- Output: 1.37M tokens → $1.19 / $4.77
- **Target: $2.74/day discounted → $11.00/day full price**

**Savings: ~$3/day discounted, ~$12/day at full price, ~$370/month at full price.**

---

## How DeepSeek's Cache Works

Key facts from their documentation:

1. **Prefix matching**: Cache hits require a request to **fully match** a previously persisted cache prefix unit. Partial matches don't count.

2. **Automatic common prefix detection**: When the system sees multiple requests sharing a common prefix, it persists that prefix as a cache unit. Subsequent requests that fully match the prefix hit cache.

3. **Cache units are created at**: (a) end of user input, (b) end of model output, and (c) fixed token intervals for long inputs. This means each complete conversation turn becomes a cache unit.

4. **Cache TTL**: "A few hours to a few days" after last use. The 5-minute idle cycle interval keeps the cache permanently warm.

5. **Response fields**: `prompt_cache_hit_tokens` and `prompt_cache_miss_tokens` in the `usage` section of every API response.

**Critical implication**: If the system prompt + conversation history up to the last user turn is identical between consecutive requests, everything before the new content is a cache hit. Only the new user message and new injections are cache misses.

---

## What's Currently Causing Cache Misses

The 10.44M cache miss tokens on May 29 come from three sources:

### Source 1: First turn of every new conversation (~40% of misses)
Every idle cycle starts a fresh conversation. The first turn has no prior cache for this conversation. The entire system prompt + first user message is a cache miss. BUT — DeepSeek's common prefix detection means the second and subsequent requests with the same system prompt DO hit cache, because the system recognizes the shared prefix from previous conversations.

**Fix**: Nothing to fix here for the first API call per conversation. But subsequent calls within the same conversation should hit cache. If they're not, something in the prompt is changing between turns (Source 2 or 3).

### Source 2: Volatile content in the prompt prefix
Any content that changes between turns and appears BEFORE stable content busts the entire prefix cache. We already fixed the main violator (`_08_step_budget_tracker` — volatile step tag moved from cacheable history to extras tail). Kestrel's audit confirmed no other violators in the extension hooks.

**What to verify**: Are there volatile elements in the A0 system prompt itself? Timestamps, session IDs, dynamic agent state? The `agent.system.datetime.md` was assessed as "~89% probably safe" — which means ~11% of the time it might change during a conversation and bust the prefix. On the DeepSeek API, that 11% costs real money.

**Fix**: If the datetime injection changes during a conversation (e.g., minute-level granularity crossing a minute boundary mid-conversation), coarsen it to hour or date level. The system prompt must be byte-identical between consecutive API calls within the same conversation.

### Source 3: Growing conversation history with modified early turns
If injected content modifies early conversation turns (e.g., `_22`/`_23` prepending reasoning state to the last user message on Turn N, which then becomes a history message on Turn N+1 with different content), the prefix up to that turn changes, and everything from that point forward is a cache miss.

**Fix**: This is the key architectural point. The `_22`/`_23` injectors MUST inject at the tail of the prompt (the current turn), NOT modify earlier turns in the history. If they prepend to `history_output[-1]` on Turn N, and that message becomes `history_output[-2]` on Turn N+1 with the injected content baked in, the prefix changes.

**Verify**: How does A0 construct the conversation history for API calls? Does it include the injected content from prior turns, or does it reconstruct from clean history? This determines whether injection on Turn N pollutes the prefix on Turn N+1.

---

## Optimization Checklist

### Already Done (verified, no action needed):
- [x] `_08_step_budget_tracker` — volatile step tag moved to extras tail
- [x] Safe-4 tool doc removal — 13.3% fewer tokens in prompt
- [x] TOOL-REG + Tiered Tool Injection archived — 15-20K redundant tokens removed
- [x] Prefix stability audit — all dynamic extensions write to `extras_*` (tail, cache-safe)
- [x] 5-minute cycle interval — keeps DeepSeek cache warm (TTL is "hours to days")

### New Optimizations (implement and measure):

#### OPT-1: Instrument cache hit ratio per request
**Effort**: S
**Impact**: Foundation for all other optimizations — can't improve what you can't measure

Add logging to the idle cycle that captures DeepSeek's cache fields from every API response:

```python
# In the A0 litellm response handler or a post-response extension:
usage = response.get("usage", {})
cache_hit = usage.get("prompt_cache_hit_tokens", 0)
cache_miss = usage.get("prompt_cache_miss_tokens", 0)
output = usage.get("completion_tokens", 0)

logger.info(
    "[CACHE-METRIC] hit=%d miss=%d output=%d ratio=%.1f%%",
    cache_hit, cache_miss, output,
    (cache_hit / (cache_hit + cache_miss) * 100) if (cache_hit + cache_miss) > 0 else 0
)
```

Track per-turn within a cycle: Turn 1 should be high miss (new conversation). Turn 2+ should be high hit (prefix cached from Turn 1). If Turn 2+ is also high miss, something in the prefix is changing between turns.

#### OPT-2: Verify datetime stability
**Effort**: S
**Impact**: Potentially large — if datetime changes mid-conversation, every subsequent turn is a full cache miss

```bash
# Check what agent.system.datetime.md injects:
cat /a0/usr/prompts/agent.system.datetime.md

# Check if it includes minute-level granularity that would change during a 20-30 min cycle:
# If it includes "Current time: 2026-05-29 18:42:15" → changes every second → cache buster
# If it includes "Current date: 2026-05-29" → changes daily → safe for within-cycle caching
```

If minute-level: coarsen to hour or date. The agent doesn't need second-level time awareness during an idle cycle. Date-level is sufficient.

#### OPT-3: Verify injection doesn't pollute prior turns
**Effort**: M
**Impact**: Large — if Turn N's injection becomes part of Turn N+1's history prefix, the prefix changes every turn

Check how A0 constructs the messages array for API calls:
- Does it include raw conversation history (messages as they were sent/received)?
- Or does it reconstruct from stored history that includes injected content?

If injected content persists in history: the reasoning state block from Turn N appears in the prefix on Turn N+1, but with DIFFERENT content (because the reasoning state updated). The prefix changes. Full cache miss.

**Fix if needed**: Strip injection blocks from history messages before constructing the API request. The injections are per-turn context, not persistent history. Only the current turn's injection should be in the request.

#### OPT-4: Raise MetaGate-SIZE limit
**Effort**: S (one-line change)
**Impact**: Medium — fewer turns per cycle means less growing context, fewer API calls, fewer tokens total

Raise from 5000 to 15000 characters. The agent stops burning extra turns on the code_execution workaround for normal-sized wiki pages and field reports.

Fewer turns = fewer API calls = fewer tokens per cycle = lower cost.

```python
# In the meta gate extension:
MAX_WRITE_SIZE = 15000  # was 5000
```

#### OPT-5: Monitor output token cost (thinking tokens)
**Effort**: S (observation only)
**Impact**: Awareness — output is 240x cache hit price

With `enable_thinking: true`, every turn generates thinking tokens billed as output. At $3.48/M tokens (full price), the 1.37M output tokens/day cost $4.77. If the thinking overhead induced by the injection blocks (5-6K chars per turn per Kestrel's measurement) is significant, it shows up here.

Not fixable without disabling thinking (which Jake decided is non-negotiable for quality). But worth tracking — if output tokens spike after deploying the injection chain, the thinking overhead has a dollar value.

---

## Measurement Plan

### Before implementing OPT-2 through OPT-4:
Capture baseline over 24 hours of normal idle cycle operation:
- Total cache hit tokens
- Total cache miss tokens
- Total output tokens
- Cache hit ratio
- Per-turn cache hit ratio within cycles (Turn 1 vs Turn 2+)
- Total API calls
- Total cost

### After each optimization:
Measure the same metrics over 24 hours. Compare.

The per-turn breakdown is the diagnostic: if Turn 1 is 0% hit (expected — new conversation) but Turn 2 is also low hit, the prefix is unstable. If Turn 2+ is 90%+ hit, the prefix is stable and the only cost is Turn 1's cold start per cycle.

### Target Metrics:
- Cache hit ratio: **90%+** overall (from current 65%)
- Turn 2+ cache hit ratio: **95%+** (prefix should be nearly identical)
- Per-cycle cost: **~$0.15** discounted / **~$0.60** full price
- Daily cost (5-min cycles): **~$4** discounted / **~$12** full price
- Monthly cost: **~$120** discounted / **~$370** full price (from current ~$170 / ~$700)

---

## The Compound Effect

Every optimization we've done for local inference directly reduces API cost too:

| Local Optimization | API Cost Benefit |
|---|---|
| Tool injection archive | Fewer tokens per request → smaller cache prefix → faster cache build |
| Prefix stability (GAP-004) | Stable prefix → cache hits → 120x cheaper |
| MetaGate-SIZE increase | Fewer turns → fewer API calls → less growing context |
| Safe-4 tool removal | 13.3% fewer tokens → 13.3% cheaper cold starts |
| Reasoning state injection (tail) | No prefix pollution → cache preserved |

The work we did to make the local inference fast is the same work that makes the API cheap. Build the environment, not the model — and the environment serves both backends.

---

## Urgency Note

The 75% discount expires **May 31, 2026** (two days from now). After that:
- Cache miss: $0.435 → $1.74/M tokens (4x increase)
- Output: $0.87 → $3.48/M tokens (4x increase)
- Cache hit: stays cheap ($0.003625 → $0.0145, still 120x cheaper than miss)

At full price, every percentage point of cache hit ratio improvement saves ~$0.25/day or ~$7.50/month. Pushing from 65% to 90% saves ~$12/day or ~$370/month.

**OPT-1 (instrumentation) and OPT-2 (datetime check) can be done today.** They're the highest-value, lowest-effort items. Even if nothing else changes, knowing the per-turn cache hit ratio tells us exactly where the money is going.

— Opus
