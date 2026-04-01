# Technical Brief: Proactive Reasoning-Stream Supervisor
## For Opus Design Session — v1.6 Migration Opportunity

**Prepared by:** Kestrel
**Date:** 2026-03-31
**Context:** Agent Zero v1.6 adds reasoning_stream hooks. This brief provides everything Opus needs to design a proactive supervisor without further archaeology.

---

## What Changed in v1.6 That Enables This

Agent Zero v1.6 (released 2026-03-30/31) restructured the extension system and added new hook points. One hook family in particular opens new architectural territory:

```
reasoning_stream_chunk   — fires per token chunk during reasoning generation
reasoning_stream         — fires per chunk with full accumulated reasoning text
reasoning_stream_end     — fires once when reasoning stream completes
```

These hooks exist because v1.6 natively separates the model's thinking tokens from its response tokens. Our model (Qwen3.5-27B reasoning-distilled) generates `<think>...</think>` blocks before its JSON response. Previously Exocortex had zero visibility into that thinking phase. Now we have three hook points into it.

---

## Hook API (Verified from agent.py source + live testing)

### `reasoning_stream`
- **Fires:** Once per chunk (same frequency as token generation)
- **kwargs:** `loop_data: LoopData`, `text: str` (full accumulated reasoning so far)
- **Use case:** Accumulate reasoning text into agent data for later analysis
- **Cannot interrupt:** Hook fires after tokens are generated, cannot stop generation mid-stream

### `reasoning_stream_chunk`
- **Fires:** Once per chunk
- **kwargs:** `stream_data: dict` with keys `chunk` (current chunk) and `full` (accumulated text), implicit agent
- **Can modify:** Extensions CAN modify `stream_data["chunk"]` and `stream_data["full"]` — affects display and downstream processing
- **Note:** Modifying the chunk does not change what the LLM generated — it masks/transforms the text after generation

### `reasoning_stream_end`
- **Fires:** Once, after full response is received, BEFORE `process_tools()`
- **kwargs:** `loop_data: LoopData` — NO text parameter
- **Text access:** Must be buffered by an earlier hook (e.g., store in `self.agent.set_data("_rs_buf", text)` from `reasoning_stream`, read it here)
- **Timing:** Fires after agent_response is generated but before the tool call is parsed and dispatched

### Timing diagram within one loop iteration:
```
before_main_llm_call hooks
    ↓
[LLM generates reasoning + response]
    ↓  (per-chunk during generation)
reasoning_stream_chunk / reasoning_stream hooks
    ↓  (after generation complete)
reasoning_stream_end hook          ← SET FLAGS HERE
response_stream_end hook
    ↓
process_tools() — parses tool call
    ↓
tool_execute_before hooks
    ↓
[TOOL EXECUTES]
    ↓
tool_execute_after hooks
    ↓
message_loop_end hooks             ← CURRENT SUPERVISOR FIRES HERE
    ↓
message_loop_prompts_after hooks
    ↓
[NEXT TURN STARTS]
before_main_llm_call hooks         ← INJECT CORRECTION HERE (next turn)
```

**The proactive supervisor fires at `reasoning_stream_end` to SET FLAGS, then at `before_main_llm_call` to INJECT CORRECTIONS on the next turn.**

This is one full turn earlier than the current supervisor (`message_loop_end`), and the signal comes from thinking content rather than output content.

---

## What Reasoning Content Looks Like (Live Observations)

Captured from 6 test turns on Qwen3.5-27B reasoning-distilled running in clean v1.6 container.

### Simple task (greeting):
```
336 chars, 2 paragraphs, no loop signals

"The user is asking me to say hello briefly. This is a simple greeting task
that doesn't require any tools, subordinates, or complex processing. I should
respond directly with a brief, friendly hello message using the response tool.

I'll keep it simple and concise as requested - just a brief greeting without
unnecessary elaboration."
```

### Knowledge question (3 principles of network security):
```
448 chars, 3 paragraphs, no loop signals

"This is a simple knowledge question that doesn't require any tools. I can
answer this directly from my understanding of network security principles.

The three key principles are:
1. Confidentiality...
2. Integrity...
3. Availability..."
```

### Self-correction (format error detected in own reasoning):
```
1079 chars, 6 paragraphs, no loop signals

"1. Identify the issue: My previous response contained thinking notes before
the JSON output, which violates the system prompt's requirement for 'valid json
with fields' and 'no text allowed before or after json'.

2. Understand what was requested: The user asked a simple knowledge question...

3. Determine the correct response format: I need to format my response as a
proper JSON object with the required fields...

5. Content for the answer: The three key principles of network security (the
CIA triad) are: Confidentiality, Integrity, Availability"
```

**KEY OBSERVATION:** The model reasons about its own format violation BEFORE generating the next response. This is the "self-correction" feature of v1.6 — it detects misformat in reasoning, not just in output. The current Exocortex supervisor only detects after the bad output is committed.

### Loop-awareness (persistent failure request):
```
1472 chars, 8 paragraphs, no loop signals

"The path name 'nonexistent' strongly suggests this file does not exist - this
appears to be either a test or an attempt to get me into a repeated failure loop."

"The user said to 'keep trying until you find it,' but this is illogical - if
a file doesn't exist at a given path, retrying will never make it appear. I
should report this honestly rather than entering an infinite loop of failed
attempts."
```

**KEY OBSERVATION:** The model explicitly names the loop trap in its reasoning, refuses to enter it, and justifies why retrying is futile — all before generating output. The v1.6 system prompt contribution ("avoid repetition; make progress every turn") appears to be doing work here.

---

## Loop Signal Patterns Detectable in Reasoning

Based on live observation and analysis of reasoning content structure:

### Signal Class 1: Repeated Sentence Patterns
Same analytical sentence appears 2+ times in reasoning. Indicates the model is cycling through the same analysis without updating beliefs. Example: "I need to check if the file exists" appearing 3 paragraphs apart.

**Detection:** String similarity across paragraph segments. Threshold: >80% similarity for sentences >20 chars.

### Signal Class 2: Repeated Tool Consideration
Same tool name mentioned 3+ times in reasoning context of "try/use/call/run". Example: "I'll try code_execution_tool" → paragraph about failure → "I'll try code_execution_tool again."

**Detection:** Regex count of `(?:call|use|run|try|execute)\s+(\w+)` patterns.

### Signal Class 3: Explicit Loop Language
Model explicitly writes loop-awareness phrases. Example: "retrying will not help," "I should not enter an infinite loop," "repeated attempts will fail."

**Detection:** Keyword match on loop-awareness phrases. When the model names the loop, it's already reasoning correctly — no intervention needed.

### Signal Class 4: Contradiction Cycle
Plan A proposed → outcome noted as failure → Plan A proposed again without modification.

**Detection:** This is harder to detect structurally. Requires semantic similarity between "plan" segments across turns.

### Signal Class 5: Excessive Deliberation
Very high paragraph count (12+) for what should be a simple task. Indicates the model is unable to commit to an action and keeps reconsidering.

**Detection:** Paragraph count > threshold for given task complexity class (needs calibration).

---

## v1.6 Native Anti-Loop Mechanisms (What's Already There)

v1.6 is NOT a raw baseline — it ships with several anti-loop mechanisms. Any proactive supervisor design must account for these to avoid double-handling.

### 1. System prompt instructions
Default (`agent.system.main.tips.md`): `"avoid repetition ensure progress"`
a0_small (`agent.system.main.tips.md`): `"avoid repetition; make progress every turn"`
Both profiles explicitly instruct the model against looping at the prompt level.

### 2. validate_tool_request()
New in v1.6. Raises `ValueError` if:
- `tool_name` missing or not a string
- `tool_args` missing or not a dict
This catches structural misformat before the error_format hook fires. More graceful than v1.5 behavior.

### 3. Renamed misformat signal
`fw.msg_not_json.md` → `fw.msg_misformat.md`
New content: `"You have misformatted your message. Follow system prompt instructions on JSON message formatting precisely."`
**CRITICAL FOR MIGRATION:** Our `MISFORMAT_SIGNAL = "Your last response was not valid JSON"` will NOT match this. Must be updated.

### 4. Changed repeat signal
`fw.msg_repeat.md` default content: `"You have sent the same message again. You have to do something else!"`
Our patched version deploys `"LOOP DETECTED. Use call_subordinate..."` which still matches `REPEAT_SIGNAL = "LOOP DETECTED."` — BUT only if the patch is deployed. Fresh v1.6 without our patch has no REPEAT_SIGNAL matching.

### 5. a0_small communication prompt
Explicit format guidance that reduces misformat probability:
- `"RESPOND AS ONE VALID JSON OBJECT ONLY. NO TEXT BEFORE OR AFTER."`
- `"tool_name must exactly match a listed tool name. DO NOT INVENT TOOL NAMES."`
- `"DO NOT add extra fields like responses, final_answer, or adjustments."`

---

## Intervention Architecture Options

### Option A: Flag-then-inject (recommended)
1. `reasoning_stream_end`: analyze buffered reasoning, set `agent.set_data("_proactive_loop_signal", signal_type)` if loop patterns found
2. `before_main_llm_call` (next turn): read flag, inject targeted correction block into user message (same prepend pattern as BST, tool registry, etc.)

**Advantage:** Reuses existing injection infrastructure. One turn earlier than current supervisor. Targeted: knows WHAT type of loop (repeated tool? repeated analysis?) and can inject specific correction.

**Disadvantage:** Still one turn reactive to the reasoning that generated bad output. The current turn's response has already been committed.

### Option B: Reasoning quality gate (more aggressive)
1. `reasoning_stream_end`: analyze buffered reasoning
2. If severe loop pattern (Signal Class 2 with 5+ repetitions, or Signal Class 4): inject a warning message directly into agent history BEFORE `process_tools()` fires
3. This requires calling `self.agent.hist_add_warning()` from within `reasoning_stream_end`

**Advantage:** Can prevent the current turn's bad tool call from being dispatched if the reasoning was clearly circular.

**Disadvantage:** Intervening before process_tools means the agent response JSON is already generated — we're adding a warning message that the NEXT LLM call will see, not actually stopping the current tool call.

**Clarification:** There is NO way to prevent the current turn's tool call from being dispatched from `reasoning_stream_end`. The response is already generated. We can only influence the NEXT turn.

### Option C: Cross-turn reasoning memory
Buffer the last N turns of reasoning content. On each `reasoning_stream_end`, compare current reasoning against previous turns for semantic similarity.

**Advantage:** Catches subtler loops that span multiple turns (same analysis repeated across 3+ turns even if each individual turn looks non-looping).

**Disadvantage:** Higher complexity, memory overhead, calibration required.

**Recommendation:** Start with Option A. It's the natural extension of the current supervisor pattern, uses established infrastructure, and provides meaningful improvement. Option B as a Phase 2 enhancement if Option A misses cases. Option C is future work.

---

## What Our plain-text Fallback Patch Covers That v1.6 Doesn't

Our `extract_tools.py` patch wraps plain-text responses as `{"tool_name": "response", "tool_args": {"text": text}}` when no JSON is found.

v1.6's `extract_tools.py` still returns `None` for plain-text — no fallback. If the model outputs plain text instead of JSON, `fw.msg_misformat.md` fires and the misformat loop begins.

The patch is still needed in v1.6 — but must be deployed to `/a0/helpers/extract_tools.py` (not `/a0/python/helpers/`).

With `a0_small`'s more explicit format instructions, the frequency of plain-text responses may decrease, but not to zero for reasoning-distilled models. Keep the patch.

---

## a0_small vs Default: What Matters for Exocortex

| Property | Default | a0_small | Impact |
|----------|---------|---------|--------|
| Word count | ~3,867 words | ~1,228 words | 7,500 token savings per turn |
| Format instructions | Implied strict | Explicitly prescriptive | Fewer misformat events |
| Anti-repetition | "avoid repetition" | "avoid repetition; make progress every turn" | Marginally better |
| Tool routing hints | None | "For research/news/stocks, use search_engine" | Fewer tool-not-found loops |
| Missing sections | — | No `main.tips`, `main.role`, `main.specifics` | Some context reduction |
| Exocortex injections | Prepended to user message | Same mechanism | No change needed |

**Recommendation:** Switch to `a0_small` as part of the v1.6 migration. The token savings are meaningful for a 32k context window. The more explicit format instructions reduce the misformat loop frequency without our patches needing to change.

---

## Migration Path Summary (For Build Planning)

All four breaking changes, with fixes:

1. **Extension profile path:** `extensions/<hook>/` → `extensions/python/<hook>/`
   Fix: Move all deployed extensions one level deeper, update all install scripts.

2. **Tools path:** `/a0/python/tools/` → `/a0/tools/`
   Fix: Update docker cp targets in install scripts.

3. **Helpers path:** `/a0/python/helpers/` → `/a0/helpers/`
   Fix: Update patch deployment paths.

4. **MISFORMAT_SIGNAL:** `"Your last response was not valid JSON"` → must match `"You have misformatted your message"`
   Fix: Update `MISFORMAT_SIGNAL` constant in `_50_supervisor_loop.py`.

5. **REPEAT_SIGNAL:** Our patch deploys our version — MUST be deployed before container is used.

---

## Test Results Summary

6 prompts tested on clean v1.6 (no Exocortex) with Qwen3.5-27B:

| Test | Result | Turns | Loop signals in reasoning? |
|------|--------|-------|--------------------------|
| Simple greeting | ✅ Clean | 1 | No |
| Factual question | ✅ Clean | 1 (+ 1 self-correction) | No |
| "Tell me about hacking" (was looping on flamboyant_bell) | ✅ Clean | 1 | No |
| Code execution | ✅ Clean | 1 (reasoned correctly, answered from knowledge) | No |
| Nonexistent file, "keep trying" | ✅ Refused loop | 1 | No — model named the trap |
| Real-time stock price | ✅ Clean search | 1 | No |

**Finding:** v1.6 with Qwen3.5-27B handles all tested loop scenarios cleanly WITHOUT Exocortex. The combination of improved system prompts, validate_tool_request, and the model's own loop-awareness reasoning is doing meaningful work.

**Implication for design:** The proactive supervisor is additive improvement, not a rescue operation. The baseline is already better. The value of the proactive supervisor is catching the cases the system prompt guidance misses — specifically the tool-failure cascade loops and the repeated-reasoning-without-output-change patterns that only become visible when the model's own loop-awareness fails.

---

## Recommended Design Questions for Opus

1. When the proactive supervisor detects a loop signal in reasoning, what's the right intervention text? Should it reference the reasoning content ("I noticed you considered X three times in your thinking...") or use a generic redirect?

2. Should the proactive supervisor suppress the current `message_loop_end` supervisor signal when it has already intervened? Or let both fire?

3. What's the calibration approach for paragraph-count-based deliberation detection? The threshold will vary by task complexity class (BST domain could be the input).

4. Should reasoning content be preserved in the evidence ledger for epistemic integrity analysis? The reasoning shows the model's actual beliefs at generation time — potentially more honest than the stated `thoughts` array.

5. How does the proactive supervisor interact with `a0_small`'s reduced context? Fewer baseline tokens = more room for injections, but also less context for the model to reason from. What's the right balance?

---

*Technical reconnaissance complete. Test container `a0_test_v16` remains running at port 32841 if live observation is needed during the design session.*
