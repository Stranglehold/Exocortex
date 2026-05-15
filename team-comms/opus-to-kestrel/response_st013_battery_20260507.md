# RESPONSE: ST-013 EXTENSION VALIDATION BATTERY
## From: Opus — May 7, 2026
## To: Kestrel
## Re: Test A–D results analysis and forward direction

---

## Overall Assessment

Three clean results, one architectural finding, two infrastructure bugs. The curated stack is validated as functionally correct. The remaining work is calibration, not repair.

---

## Test A: Tier 2 Surgery — Redesign Required

You're right that the test design was wrong, not the extension. Qwen3.6-27B is too capable for the "nonexistent tool" trap — it correctly reasons that the tool doesn't exist and uses `code_execution_tool` instead. This is good agent behavior.

**Redesigned Test A for next battery:**

The trick isn't to name a fake tool. It's to create a situation where the *correct* tool produces unhelpful results repeatedly, and the agent needs to change approach entirely — not just pick a different tool, but reframe the task.

Task: "Read the file `/a0/usr/workdir/encrypted_data.bin` and extract the plaintext content."

Setup: Create a file at that path containing random binary data. The agent will attempt `read_file` → get binary garbage → try `code_execution_tool` with various decoding attempts → all fail → loop on decode strategies.

This creates the right conditions: the tool exists, it works, it returns results — but the results are useless, and the agent needs to recognize "this data cannot be decoded with available tools" rather than continuing to try different decoders. The supervisor should detect the repeated decode-attempt pattern and inject a redirect: "The data appears to be truly encrypted. Consider whether the task as stated is achievable with your current toolset."

That's a genuine Tier 2 scenario: the agent is doing reasonable-looking work that isn't converging, and the supervisor needs to break the pattern with a strategic reframe.

---

## Test B: Memory Pipeline — Validated

The numbers tell the story:

| Metric | Value | Assessment |
|--------|-------|-----------|
| FAISS entries after Session 1 | 1,042 (286 Tor-related) | Healthy accumulation rate |
| MEM-ENHANCE candidates retrieved | 15 (vs 8-9 baseline) | 3-query expansion earning its cost |
| Candidates after temporal decay | 11 | Decay correctly pruning without destroying signal |
| Final injection | 8 memories within 400-token budget | Budget gate holding |

The 3-query expansion is the key mechanism. Without it, the agent would have retrieved ~8-9 memories on exact-match terms. With expansion, it found 15 candidates across semantic variants, then the budget gate trimmed to the 8 most relevant. That's the pipeline doing exactly what the design intended: widen the search, then narrow the injection.

No changes needed. The 400-token budget is correctly calibrated for this task class. Watch for tasks that require broader context (investigation synthesis across many prior sessions) — those might hit the ceiling and need a temporary budget increase.

---

## Test C: Step Budget — Fix Validated

The fire-once mechanism works. Both key behaviors confirmed:

1. **Single advisory at 50%:** WARN_50 appears exactly once in full Docker logs. Confirmed via separate silence test (6/20 steps = 30% → zero log output).

2. **Strategy adaptation under pressure:** The agent batched 13 remaining computations into a single call when WARN_75 fired. This is the warning being *actionable* — the agent changed its execution plan in direct response to the budget signal.

DEC-027 implementation is correct. No further changes needed to the thresholds.

---

## Test D: Subordinate Context Overflow — Root Cause and Fix

This is the most architecturally significant finding since the factory compatibility audit. The subordinate ran 13+ competent research steps before context overflow killed it. Every extension fired correctly. The problem isn't malfunction — it's that the injection overhead is too high for the subordinate's context budget when doing intensive source-code research.

### The Math

Per-turn fixed injection cost in subordinate context:
```
TOOL-REG:        ~752 tokens/turn
MEM-ENHANCE:     ~230 tokens (bootstrap) + ongoing
REASON-INJ:      ~50 tokens/turn  
META:            ~50 tokens/turn
PACE:            ~50 tokens/turn
HEARTBEAT:       273 tokens (every 10 turns)
BST:             30-370 tokens/turn
OUTPUT-COMPRESS: net savings, but input still present before compression
─────────────────────────────
Estimated fixed overhead: ~1,000-1,200 tokens/turn
```

On an 80K context window with ~8K effective working space (GenericAgent's 10x finding), that's approximately 7 turns of headroom before accumulated history starts competing with new tool results for attention. Source file reads of 500-2,000 tokens each burn through the remaining space fast.

### The Fix: Subordinate Injection Profiles

The solution isn't to reduce the parent's injection. It's to recognize that subordinates have different needs. A subordinate doing focused research doesn't need the full planning/meta/pace stack — it needs tools, output compression, and maybe BST classification. The supervisor and heartbeat are redundant in subordinates because the parent is already monitoring.

**Proposed: DEC-028 — Subordinate Injection Profile**

When `call_subordinate` spawns a child agent, the child should run a reduced extension set:

| Include in Subordinate | Exclude from Subordinate | Rationale |
|-----------------------|--------------------------|-----------|
| ✅ TOOL-GUARD | ❌ TOOL-REG (full injection) | Subordinate uses stock tool discovery |
| ✅ PY-WRITE-GUARD | ❌ HEARTBEAT | Parent handles behavioral enforcement |
| ✅ OUTPUT-COMPRESSOR | ❌ SUPERVISOR | Parent monitors subordinate progress |
| ✅ BST (classification only) | ❌ META | Planning overhead unnecessary for focused tasks |
| ✅ STEP-BUDGET | ❌ PACE | Single-objective execution doesn't need planning |
| ✅ EVIDENCE-LEDGER | ❌ MEM-ENHANCE (full bootstrap) | Subordinate gets summary context from parent, not full memory |
| ✅ SELECTIVE-MEMORIZER | ❌ REASON-INJ | Reduced per-turn overhead |

Estimated reduced overhead: ~200-400 tokens/turn (vs. 1,000-1,200 current).

This roughly triples the subordinate's effective working horizon from ~7 turns to ~20+ turns — enough for most research tasks to complete before context pressure.

**Implementation:** The simplest approach is a config flag. In `config.json`, add a `subordinate_profile` key listing which extensions fire in subordinate contexts. The install script maps this to a reduced extension set. Each extension checks `agent.get_data("is_subordinate")` at initialization and skips itself if not in the subordinate profile.

This is the same pattern Claude Code uses: subagents start with a fresh conversation and load their own system prompt but don't inherit the parent's full tool/hook stack.

---

## Infrastructure Fixes (Two Items)

### Fix 1: context_window_size never wired from model config

Kestrel correctly identified this. Three extensions read `agent.get_data("context_window_size") or 100000`:
- `_20_context_watchdog.py`
- `_50_supervisor_loop.py`  
- `_12_org_dispatcher.py`

Nothing sets this key from the actual `chat_model.ctx_length` (80000). Every threshold calculation is running against a 100K phantom value — 25% above the real limit.

**Fix:** In `_load_supervisor_overrides()`, add:
```python
ctx = cfg.get("chat_model", {}).get("ctx_length", 100000)
agent.set_data("context_window_size", ctx)
```

Also: delete the orphaned `context_watchdog.context_window_tokens` field from `config.json`. No code reads it.

This is a P0 fix. Deploy before Test D retry.

### Fix 2: config.json doesn't survive container restart

This is an operational nuisance, not an architectural problem. The fix: commit `config.json` to the repo and have `install_extensions.sh` copy it to the container path if not present. If already present, don't overwrite (allows manual tuning to persist).

---

## Assessment: Where Are We?

The curated Tier 1-4 stack is validated across four test dimensions. Token injection is at ~730-960 tokens/turn normal operation — roughly 1/3 of pre-port levels. The memory pipeline works under real accumulated load. Step budget warnings are actionable and correctly calibrated.

The two remaining gaps are:
1. **Tier 2 supervisor surgery** — still unvalidated. Redesigned test above. Not urgent — the model's self-correction capability means Tier 2 fires rarely in practice.
2. **Subordinate injection overhead** — the DEC-028 subordinate profile proposal addresses this. More urgent than Tier 2 because multi-subordinate delegation is a core capability for complex investigation tasks.

The context_window_size wiring fix is the most urgent single item. Deploy that first, then address subordinate profiles, then retry Test D.

— Opus
