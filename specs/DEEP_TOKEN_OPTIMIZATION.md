# DEEP TOKEN OPTIMIZATION — Comprehensive Guide for DeepSeek Idle Cycles
## Author: Opus — June 3, 2026
## Sources: DeepSeek API docs, "Don't Break the Cache" (Feb 2026 paper), OpenAI Prompt Caching 201, ProjectDiscovery case study (59% reduction), Redis/Obvious Works/TokenOptimize production guides, Hermes Agent Issue #13631 (cache invalidation bug)
## Goal: Reduce Vek's idle cycle costs from $5/day to <$1/day
## Builds on: specs/API_CACHE_OPTIMIZATION.md (the five OPTs from last session)

---

## The Economics at a Glance

| Lever | Savings | Effort | Compounds With |
|-------|---------|--------|---------------|
| **Cycle interval** (5min → 30min) | ~83% | Trivial | Everything |
| **Prefix stability** (cache hits 65% → 90%) | ~50% on remaining | Medium | Cycle interval |
| **Thinking mode routing** (Think High → Non-think for MAINTAIN) | ~40-60% on output tokens | Medium | Both above |
| **Model routing** (V4-Pro → V4-Flash for MAINTAIN) | ~93% on MAINTAIN cycles | Medium | All above |
| **Conversation history management** | ~20-30% on growing context | Medium | Prefix stability |
| **Semantic caching** (skip identical research queries) | ~10-20% on repeated work | High | All above |

**Combined theoretical maximum: 95%+ reduction ($5/day → $0.15-0.25/day)**
**Realistic combined target: 85-90% reduction ($5/day → $0.50-0.75/day)**

---

## Lever 1: Cycle Interval (The Biggest Single Lever)

**Current:** 5-minute cycles → ~288 API sessions/day
**Recommended:** 30-minute cycles → ~48 API sessions/day
**Savings:** 83% reduction in session count

The research topics don't change faster than 30-minute sampling. MAINTAIN cycles check memory health — the memory store doesn't mutate between cycles. BUILD cycles deepen wiki pages — the sources don't change in 5 minutes. EXPLORE cycles find new research — the arXiv and web search indexes don't refresh every 5 minutes.

The one exception: if Jake sends a message via Telegram (future Hermes integration), the response cycle should fire immediately regardless of the interval. The 30-minute interval governs autonomous idle cycles, not reactive cycles.

**Implementation:** Single config change in `idle_watch.py` — the `CYCLE_INTERVAL` parameter.

---

## Lever 2: Prefix Stability (The Highest-Leverage Technical Optimization)

### What the research says

The "Don't Break the Cache" paper (February 2026) evaluated three caching strategies across OpenAI, Anthropic, and Google on 500 agent sessions with 10K-token system prompts:

1. **Full context caching** — cache everything including tool results → 45-80% cost reduction
2. **System prompt only caching** — cache the static prefix → moderate reduction
3. **Excluding dynamic tool results** — cache everything except tool outputs → best balance

Key finding: **prompt caching reduces API costs by 45-80% and TTFT by 13-31%.** The benefit is linear with prompt size after the provider minimum (1024 tokens).

### DeepSeek-specific mechanics

From DeepSeek's own docs and the community research:

- Cache matching requires **exact prefix match from token 0.** Partial matches in the middle don't count.
- Caching is **automatic** — no API parameters, no TTL settings, no code changes needed.
- Cache hit price is **10x cheaper** than cache miss (confirmed across all sources).
- Requests are routed to machines based on a **hash of the initial prefix** (~first 256 tokens).
- Cache TTL is "a few hours to a few days" — our 30-minute cycle interval keeps it warm.

### What breaks the cache (from Hermes Agent Issue #13631 + CodeWhale diagnostics)

Six specific cache-busting patterns identified across the research:

1. **Static prompt prefix changes that are hard to detect** — timestamps, session IDs, dynamic counters injected before the stable content
2. **Growing conversation history** — each turn adds to the prefix, changing the hash
3. **Large tool result messages** — tool outputs injected into the conversation push subsequent content to different positions
4. **Repeated identical tool outputs** — paradoxically, identical outputs that are re-serialized with different formatting bust the cache
5. **Mid-prefix mutations** — Hermes bug: auto-injected context rebuilds the cached system prompt every N turns
6. **Dynamic metadata blocks** — turn numbers, timestamps, or counters that change on every request

### What we should check in Agent Zero

The A0 prompt construction path needs a cache-stability audit (this is OPT-2 and OPT-3 from the earlier spec, now with more specific guidance):

```
[STATIC PREFIX — must be byte-identical across requests]
├── System prompt (agent.system.main.md)
├── Agent persona (program.md content)
├── Tool definitions (the tool schema JSON)
├── Static rules (acceptable use, format instructions)
│
[SEMI-STABLE — changes between conversations, stable within one]
├── BST domain classification (changes per task, stable within a task)
├── Active skill injections (_24 surfacer output)
│
[VOLATILE — changes every turn, MUST be at the tail]
├── Conversation history (grows each turn)
├── Memory recall results
├── Reasoning state injection (_22/_23)
├── Tool results from previous turns
├── Step budget / PACE plan updates
```

**The audit question:** Is everything above the line actually stable? Or does something in the "static" section change between turns (timestamps, dynamic counters, version strings)?

The Hermes bug (#13631) is instructive: their "Honcho" context injection was supposed to be tail-only but was actually mutating the system prompt every N turns. "Causal attention means mid-prefix mutations invalidate everything after the first divergence — every token downstream must be reprocessed from scratch."

### Implementation

Kestrel should trace the actual API request construction in A0's litellm call path and verify:
1. What goes into the `system` message (is it truly static across turns within a conversation?)
2. What goes into the `messages` array (does injected content from Turn N pollute the prefix on Turn N+1?)
3. Whether tool definitions are serialized identically across requests (tool list reordering would bust the cache)

---

## Lever 3: Thinking Mode Routing

### What the research says

DeepSeek V4-Pro supports three thinking modes:
- **Non-think:** No chain-of-thought. Fast, cheap. Good for simple tasks.
- **Think High:** Standard CoT reasoning. Good for most analytical work.
- **Think Max:** Extended CoT with up to 384K reasoning tokens. For the hardest problems.

Thinking tokens are **output tokens** — the most expensive tier ($3.48/M at full price for V4-Pro). Every thinking token costs 240x more than a cached input token.

### Application to idle cycles

| Cycle Type | Recommended Mode | Why |
|------------|-----------------|-----|
| **MAINTAIN** | Non-think | Routine housekeeping: dedup, promote, clean. Doesn't need reasoning. |
| **BUILD** (wiki deepening) | Think High | Research synthesis needs reasoning but not extreme depth. |
| **EXPLORE** (new research) | Think High | Cross-domain connections need reasoning. |
| **BUILD** (field report) | Think High | Analytical writing needs CoT. |

Switching MAINTAIN cycles to Non-think mode could reduce output tokens by 40-60% on those cycles. Since MAINTAIN is ~60% of cycles (3 out of every ~5), the savings are significant.

### Implementation

In the idle engine's cycle dispatch:
```python
if cycle_type == "MAINTAIN":
    # Override thinking mode for this API call
    model_params["thinking"] = "off"  # or however A0/litellm controls this
elif cycle_type in ("BUILD", "EXPLORE"):
    model_params["thinking"] = "high"
```

The exact parameter name depends on how A0 passes thinking mode to litellm → DeepSeek. Kestrel can verify.

---

## Lever 4: Model Routing (V4-Flash for Simple Cycles)

### The price difference

| Model | Cache Hit | Cache Miss | Output |
|-------|-----------|------------|--------|
| V4-Pro | $0.0145/M | $1.74/M | $3.48/M |
| V4-Flash | $0.003/M | $0.20/M | $0.60/M |

V4-Flash is **~6x cheaper** on output and **~9x cheaper** on cache misses. For MAINTAIN cycles that don't need deep reasoning, V4-Flash is more than sufficient.

### Application to idle cycles

| Cycle Type | Model | Why |
|------------|-------|-----|
| **MAINTAIN** | V4-Flash | Routine housekeeping. 0.8B-equivalent task complexity. |
| **BUILD** (routine deepening) | V4-Flash | Most wiki page deepening is straightforward research synthesis. |
| **BUILD** (complex analysis) | V4-Pro | Field reports with cross-domain connections need the larger model. |
| **EXPLORE** | V4-Pro | Novel research synthesis is where V4-Pro's reasoning matters. |

### Implementation

The idle engine already knows the cycle type before dispatching. Add a model-selection step:
```python
if cycle_type == "MAINTAIN":
    model = "deepseek-v4-flash"
elif cycle_type == "BUILD" and task_complexity < THRESHOLD:
    model = "deepseek-v4-flash"
else:
    model = "deepseek-v4-pro"
```

The `task_complexity` classifier could use BST domain depth or a simple heuristic (e.g., research/investigation domains → Pro, everything else → Flash).

**Note:** This requires A0's model config to support per-cycle model switching. Verify with Kestrel whether litellm allows dynamic model selection within a running agent.

---

## Lever 5: Conversation History Management

### The problem

Each idle cycle is a multi-turn conversation (the agent reasons, calls tools, gets results, reasons again). By turn 10, the conversation history contains all prior turns — tool calls, tool results, reasoning chains. This growing context:
1. Increases total input tokens per request (more tokens = more cost)
2. Changes the prefix on every turn (cache-busting potential)
3. May include large tool outputs that bloat the context

### The optimization

**Retention-ratio truncation** (from OpenAI Prompt Caching 201): instead of dropping individual messages from the middle of the conversation, truncate in stable chunks. Keep the most recent N% of history, drop the rest. The truncation happens at stable boundaries so the remaining prefix stays consistent.

**Tool result compression:** Large tool outputs (web page content, search results) should be summarized or truncated before being stored in conversation history. The full output was useful for the turn it was generated; subsequent turns only need the extracted findings.

**Max conversation length per cycle:** Set a hard limit on turns per cycle. If the cycle exceeds N turns (say 15), force a cycle_close. This bounds the maximum context growth per cycle.

### Implementation

These changes are in A0's conversation management, not the idle engine directly. Kestrel would need to trace how A0 constructs the `messages` array and identify where compression/truncation could be inserted.

---

## Lever 6: Semantic Caching (Advanced, Future)

### What it is

Semantic caching (vCache, February 2026) uses embedding similarity to detect when two different queries are semantically equivalent, returning the cached response without making an API call at all.

### Application to idle cycles

The idle engine sometimes researches the same topics across cycles — especially during BUILD deepening passes where it searches for the same sources to verify citations. If the same web search query (or a semantically equivalent one) was run in a recent cycle, the cached result can be reused without an API call.

### Implementation complexity

This requires a local cache layer (Redis or FAISS) that:
1. Embeds each query at API call time
2. Checks for similar queries in the cache
3. Returns the cached response on hit
4. Falls through to the API on miss

This is the highest-effort optimization and should be built last. The other levers together should achieve the 85-90% target without semantic caching.

---

## Implementation Priority

### Phase 1 (Today — Trivial)
1. **Cycle interval:** 5min → 30min. One config change.

### Phase 2 (This Week — Medium)
2. **Instrument cache hit ratio:** Add per-request logging of `prompt_cache_hit_tokens` and `prompt_cache_miss_tokens` (OPT-1 from original spec)
3. **Prefix stability audit:** Kestrel traces the API request construction path and verifies prefix stability. Fix any cache-busters found.

### Phase 3 (Next Week — Medium)
4. **Thinking mode routing:** Non-think for MAINTAIN, Think High for BUILD/EXPLORE
5. **Model routing:** V4-Flash for MAINTAIN, V4-Pro for analytical work
6. **Conversation history management:** Tool result compression, max turns per cycle

### Phase 4 (Future — High Effort)
7. **Semantic caching:** Local embedding cache for repeated queries

---

## Projected Cost After All Optimizations

Starting point: $5/day (5-minute cycles, V4-Pro, Think High, 65% cache hit)

| After Lever | Daily Cost | Savings |
|-------------|-----------|---------|
| Cycle interval (30min) | $0.83 | 83% |
| + Prefix stability (90% hit) | $0.50 | 90% |
| + Thinking routing (Non-think MAINTAIN) | $0.35 | 93% |
| + Model routing (Flash for MAINTAIN) | $0.20 | 96% |
| + History management | $0.15 | 97% |

**Target: $0.15-0.25/day = $4.50-7.50/month**

That's continuous 24/7 autonomous research for the price of a coffee.

---

## Key Research References

1. **"Don't Break the Cache"** (February 2026) — First rigorous evaluation of prompt caching for agentic tasks. 500 sessions, three strategies, three providers. 45-80% cost reduction.
2. **OpenAI Prompt Caching 201** — Retention-ratio truncation, prefix stability engineering, cache monitoring
3. **Hermes Agent Issue #13631** — Cache invalidation from mid-prefix context injection. The exact bug pattern we need to check for in A0.
4. **DeepSeek Context Caching docs** — Automatic, prefix-only, 10x cheaper on hits, TTL of hours-to-days
5. **ProjectDiscovery case study** — 59% cost reduction on Opus 4.5 agentic workload (20-40 steps/task)
6. **"Don't Break the Cache" paper** on arxiv: 2601.06007 — the full academic treatment

---

*The compounding is the key insight. Each lever multiplies with the others. Cycle interval alone saves 83%. Add prefix stability and thinking routing and model routing and the cost drops below $0.25/day. Continuous autonomous research for $7.50/month. That's sustainable indefinitely.*

— Opus
