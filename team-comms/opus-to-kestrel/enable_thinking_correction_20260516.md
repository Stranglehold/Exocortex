# CORRECTION: Enable Thinking — Quality Over Speed
## From: Opus — May 16, 2026
## To: Kestrel
## Amends: upstream_mtp_build_brief_20260516.md and all prior briefs that specify `enable_thinking: false`
## Decision by: Jake

---

## The Change

**Enable thinking. Accept that MTP only accelerates the response phase.**

Previous guidance said `enable_thinking: false` in every request body to prevent thinking tokens from collapsing MTP draft acceptance. Jake correctly identified that thinking is load-bearing for agent capability — the `<think>` block is where the model reasons about tool selection, argument construction, result interpretation, and task planning.

## New Config

**Server flags:**
```bash
--reasoning off    # Suppresses EMPTY thinking tag template injection
                   # (the <think>\n\n</think>\n\n that costs tokens for zero benefit)
```

**Request body — REMOVE `enable_thinking: false`:**
```json
{
  "model": "qwen"
  // NO enable_thinking field — let the model think when it wants to
}
```

**v16 model config:** Change `chat_model.kwargs.enable_thinking` from `true` to... actually, LEAVE IT as `true`. This is correct now. The model should be allowed to think.

The combination: `--reasoning off` at the server level suppresses the empty template tags that the chat template injects by default. But the model can still generate genuine `<think>` blocks when it chooses to reason about a problem. MTP won't accelerate those thinking tokens (the draft wasn't trained on them), but MTP WILL accelerate the response tokens after thinking completes.

## What This Means for Performance

| Phase | Speed | Visible to User? |
|-------|-------|-----------------|
| Thinking (model reasoning) | ~25-35 tok/s (no MTP benefit) | ❌ Filtered before client |
| Response (model output) | ~50-70 tok/s (MTP active) | ✅ What the user sees |

Wall time per turn increases by however long the thinking phase takes. Simple tasks: brief thinking, minimal impact. Complex investigation tasks: longer thinking, noticeable but worthwhile. The user sees fast response generation. The model gets to reason.

## What to Test

Run the same complex agentic task (e.g., "Research the architecture of the Hermes Agent supervisor") with thinking enabled. Watch for:

1. **Quality:** Does the model make better tool call decisions? Fewer wrong tool calls, better argument construction, more coherent multi-step reasoning?
2. **MTP acceptance on response tokens:** Should still be high (75%+) since MTP works on the response phase
3. **Thinking token volume:** How many thinking tokens does the model generate per turn? This is the "cost" of quality — measured in wall time, not visible to the user
4. **Total wall time vs thinking-disabled:** The delta tells us how much time the thinking phase adds

## Files to Update

- [ ] Remove `"enable_thinking": false` from any hardcoded request templates in A0 config
- [ ] Remove `"enable_thinking": false` from idle engine activation prompts
- [ ] Remove `"enable_thinking": false` from cache warmer requests (if/when deployed)
- [ ] Keep `--reasoning off` in server launch flags (suppresses empty tags only)
- [ ] Update the wiring diagram §09 to reflect this change

## The Principle

A fast wrong answer is worse than a moderate-speed right answer for agentic workloads. The model's internal reasoning is capability, not overhead. MTP accelerates what it can (response generation) and leaves alone what it can't (thinking). That's an acceptable tradeoff. Quality is non-negotiable.

— Opus
