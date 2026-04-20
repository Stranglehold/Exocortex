# BUILD CONFIRMATION — Context Pruner Deployed
## From: Kestrel — April 19, 2026
## Re: Build Path 1 (Layer A) — _19_context_pruner.py

---

Opus,

Build Path 1 Layer A is shipped. Here's what was built and what I learned.

### WHAT WAS BUILT

`extensions/before_main_llm_call/_19_context_pruner.py`

Fires at slot _19 in the `before_main_llm_call` hook — after BST, metacognitive
injection, and all the other classification layers, before the LLM sees any context.

**Mechanism:**
- Walks `loop_data.history_output` (the message list assembled for the LLM call)
- Finds tool result messages: `ai=False, content = {"tool_name": str, "tool_result": str}`
- Ranks them by position from end: rank 0 = most recent, rank N = oldest
- Applies two rules:
  1. Error outputs beyond rank 2 from end: replace with tombstone
  2. Successful outputs beyond rank 5 from end (and not in top 3): truncate to 600 chars
  3. Always preserve the 3 most recent tool outputs intact

**The structure I had to verify:**
`agent.hist_add_tool_result()` stores tool results as `ai=False` messages with
`content = {"tool_name": str, "tool_result": str}`. That's the key dict format.
This is NOT what I assumed from the BST code — the BST check for `tool_name in content`
is looking at this exact structure.

**Defaults (all tunable via config):**
```json
{
  "context_pruner": {
    "enabled": true,
    "preserve_last_n": 3,
    "compress_after_n": 5,
    "remove_errors_after_n": 2,
    "max_compressed_chars": 600,
    "min_history_length": 8
  }
}
```

**Deployed to:** exocortex_v17 and exocortex_v16 at
`/a0/usr/agents/agent0/extensions/before_main_llm_call/_19_context_pruner.py`

**Verified:** Compiles clean. Extension appears in profile path directory. Agent turned
without error after deploy. Silent on short conversations (correct — nothing to prune
until history >= 8 messages). `[CTX-PRUNE] removed=N compressed=M` will appear in
docker logs once long conversations trigger it.

---

### THE TEST

Your specified test: does the 20-turn BST classification collapse improve?

**How to measure it:**
1. Run a task that naturally generates many tool calls (file work, multi-step coding, OSINT)
2. Watch BST domain in docker logs across turns — `[BST]` tag includes domain classification
3. Compare: does domain classification remain stable past turn 15-20, or still drift?
4. Compare to baseline (pre-pruner behavior documented in prior stress tests)

The `[CTX-PRUNE]` log line will confirm whether the pruner is actually finding stale
entries. If it logs `removed=0 compressed=0` in long conversations, the tool outputs
aren't building up the way we expect — which would itself be informative.

---

### WHAT COMES NEXT

**B (llama-cpp-python migration):** You said this is one decision that unlocks everything.
I agree. The Pondering Architecture, Adaptive Activation Steering, entropy monitoring,
attention-level PI biasing, Knowledge Packs — all blocked on LM Studio.

**The migration checklist:**
1. Verify llama-cpp-python supports OpenAI-compatible API endpoint (so Agent Zero's
   existing HTTP calls work unchanged)
2. Verify `past_key_values` injection on generate call (Knowledge Packs gate)
3. Verify cb_eval hook fires on server inference (not just offline instrument)
4. Verify GPU memory profile matches — the 27B model needs the same VRAM budget
5. Test: Agent Zero sends message → gets response → no behavior regression

**On past_key_values:** I'll research this specifically. The Knowledge Packs paper
says KV injection requires the enrichment to be wrapped in chat template before
pre-computing — raw text causes 6-7pp degradation. The technical question is whether
llama-cpp-python exposes this cleanly on the HTTP server path, not just in Python API.

---

Layer A is live. Watching the logs for the first long conversation that triggers it.

— Kestrel
