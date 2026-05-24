# FINAL CONFIGURATION — Build, Deploy, Test
## From: Opus — May 18, 2026
## To: Kestrel
## Priority: 🔴 — This is the production configuration. No more engine exploration.

---

## The Decision

**Stay on llama.cpp (Indras-Mirror). Optimize what we inject, not what we run.**

No engine switch. No vLLM. No SGLang. No new container architecture. The Nous Research recommendation confirms what we found empirically: single-GPU personal inference + agentic workflows = llama.cpp from source, every time. vLLM is for multi-GPU batch serving. We have one 3090.

Everything below uses the stack we already have — built, validated, running.

---

## The Stack (No Changes to Inference Binary)

```bash
# Indras-Mirror llama.cpp fork — ALREADY BUILT
# Binary at: D:\Vibecode\Agent-Zero\Exocortex\inference\llama-cpp-indras\build\bin\llama-server

llama-server \
  -m Qwen3.6-27B-Q4_K_XL-mtp.gguf \
  -ngl 99 \
  --flash-attn on \
  --spec-type mtp \
  --spec-draft-n-max 3 \
  -ctk turbo3 -ctv turbo3 \
  -c 130000 \
  --parallel 1 \
  --reasoning off \
  --host 0.0.0.0 --port 1235
```

**No changes to the binary. No rebuild. The inference engine is done.**

---

## What We're Deploying (Three Items)

### Item 1: Injection Chain (_22 + compressed _23)

Format test passed — all three tests: USES IT. No meta-narration in output. Ready to deploy.

```bash
# Deploy to CORRECT path (with python/ segment!)
# _22_reasoning_state_injector.py → message_loop_prompts_after
# _23_pace_plan_injector.py (compressed) → message_loop_prompts_after

# On v16:
docker cp _22_reasoning_state_injector.py \
  intelligent_villani:/a0/usr/agents/agent0/extensions/python/message_loop_prompts_after/

docker cp _23_pace_plan_injector.py \
  intelligent_villani:/a0/usr/agents/agent0/extensions/python/message_loop_prompts_after/

# Run audit
docker exec intelligent_villani python3 /a0/usr/Exocortex/scripts/audit_extensions.py

# Restart run_ui to load new extensions
supervisorctl restart run_ui
```

### Item 2: Cache Warmer Verification

The cache warmer (`_71_cache_warmer.py`) was redeployed to the correct path in the last audit pass. Verify it's working:

```bash
# Check it's at the right path
docker exec intelligent_villani ls -la \
  /a0/usr/agents/agent0/extensions/python/tool_execute_after/_71_cache_warmer.py

# Check md5 matches
docker exec intelligent_villani md5sum \
  /a0/usr/agents/agent0/extensions/python/tool_execute_after/_71_cache_warmer.py
# Expected: a8e840e046e45b9ad478aa9867ad5e09
```

The cache warmer sends a warm-up request with the system prompt during idle time. The KV cache builds in the background. When the first real request arrives, the system prompt is cached. First-turn TTFT drops from 17 minutes to the delta-only prefill time.

**Critical requirement:** The warm-up request's system prompt must match the real A0 system prompt exactly. If they differ by even one token, the cache prefix doesn't match and the warm-up is wasted.

### Item 3: System Prompt Framing Line (GAP-004 Phase A)

Add one line to the A0 system prompt that tells the model the reasoning/PACE blocks are its own memory:

```
Blocks tagged [REASONING STATE] and [PACE] are your own working memory from prior turns. Use them to inform your next action. Do not comment on them.
```

This goes in `agent.system.main.md` or equivalent. The format test showed the model treats the blocks as "user-provided status updates" — this line reframes them as self-owned memory.

---

## Test Protocol

### Test 1: Extension Audit (2 minutes)
After deploying _22 and _23, run the audit tool. Target: 0 dead, 0 canonical divergent.

### Test 2: Injection Chain Verification (5 minutes)
Start the server, send a multi-turn conversation through A0. Check docker logs for:
- `[REASON-INJ-22]` — reasoning state injector fired
- `[PACE-INJ-23]` — PACE plan injector fired
- No `[REASON-INJ-22] skipped` or error messages

### Test 3: Cache Warmer Verification (20 minutes)
With server running:
1. Let the cache warmer fire (triggered by idle or server startup)
2. Check server logs for the warm-up request completing
3. Send a real A0 request
4. Check `cache_n` in the response timings — should be > 0 (prefix cached from warm-up)
5. Compare TTFT to a cold start

### Test 4: Full Idle Cycle (30-60 minutes)
Unpause the idle engine on v16. Let one full cycle run. Observe:
- [ ] Does the cycle complete without overlap? (heartbeat fix verified)
- [ ] Do the injection log tags appear? (_22 and _23 firing)
- [ ] Does the cycle avoid regenerating identical preambles? (the injection chain's purpose)
- [ ] What's the total wall time for the cycle?
- [ ] What type did the state detector select? (MAINTAIN/BUILD/EXPLORE)

### Test 5: Cycles/Day Projection (overnight)
Let the engine run overnight. Count:
- Total cycles completed
- Average wall time per cycle
- Compare to the pre-optimization baseline (~6-8 cycles/day with 17-min cold prefill)

**Target: 15+ cycles/day** (cache warmer eliminates cold prefill on most cycles, prompt shrink reduces prefill cost, injection chain reduces wasted steps from preamble repetition)

---

## Results Table (Fill In)

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Cold prefill (first turn) | ~17 min | | |
| Warm prefill (cached turn) | ~22 sec | | |
| Decode TPS | 53.27 | | Should be unchanged |
| Injection chain firing | Never (inert) | | Should fire every turn |
| Preamble repetition | Every turn | | Should reduce/stop |
| Cycles/day | ~6-8 | | Target: 15+ |
| Cycle wall time | ~45-60 min | | Target: <20 min |

---

## What's Done vs What's Left

### Done (no action needed):
- [x] Indras-Mirror binary built and validated (53.27 tok/s, 87.8% acceptance)
- [x] Cache reuse patch applied (29/33 cache hit, verified)
- [x] Safe-4 tool docs removed (13.3% prompt reduction)
- [x] TOOL-REG + Tiered Tool Injection archived (15-20K redundant tokens removed)
- [x] Heartbeat fix deployed to correct path
- [x] _08 step-budget cache-safe fix deployed
- [x] Prefix stability audit complete (all clear)
- [x] Dead extensions cleaned (0 dead on both containers)
- [x] Org dispatcher dual-path resolved
- [x] Supervisor audit — 4 compounding bugs fixed

### Deploying now:
- [ ] _22 reasoning state injector
- [ ] _23 compressed PACE plan injector
- [ ] Verify cache warmer at correct path
- [ ] GAP-004 Phase A system prompt framing line

### After validation:
- [ ] GAP-005: TTL filter on tried[] (10-line change)
- [ ] GAP-001: _49 generator rework (compose from BST + PACE + tool history)
- [ ] GAP-002: Baseline metrics extraction + post-deploy comparison
- [ ] Remaining wiring diagram sections

---

## The Principle

The engine is done. The optimization is in what we feed it.

Shrink the prompt. Warm the cache. Close the injection chain. Measure the result. That's the whole plan. No more engine switches, no more fork evaluations, no more architecture proposals. The inference stack is llama.cpp compiled from source with our flags. The work is everything around it.

— Opus
