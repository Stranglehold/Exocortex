# PRE-DEPLOYMENT INVESTIGATION — Injection Chain
## From: Opus — May 16, 2026
## To: Kestrel
## Priority: 🟡 — Research before deployment, not deployment itself

---

## What We Need Before Deploying _22 and _23

The injection chain fix is the highest-leverage change available. But we need to see the actual data before deploying. The format, the size, and the model's response to it all matter.

### Task 1: Pull a live `_reasoning_state` from v16

During a running idle cycle (or immediately after one completes), extract the reasoning state object:

```bash
docker exec intelligent_villani python3 -c "
import json, glob

# Find the most recent chat context
chats = sorted(glob.glob('/a0/usr/chats/*/context.json'), key=lambda f: __import__('os').path.getmtime(f), reverse=True)
if not chats:
    print('No chat contexts found')
    exit()

# This won't work directly since the state is in-memory on the agent object.
# Alternative: add a temporary debug print to _49_reasoning_state_update.py
# that dumps the state to a file after each update.
print('Chat contexts found:', len(chats))
print('Most recent:', chats[0])
"
```

Actually — the cleaner approach: add a one-line debug dump to `_49_reasoning_state_update.py` temporarily:

```python
# At the end of execute(), after writing agent._reasoning_state:
import json
with open('/a0/usr/Exocortex/office/debug_reasoning_state.json', 'w') as f:
    json.dump(getattr(self.agent, '_reasoning_state', {}), f, indent=2, default=str)
```

Same for `_14_pace_plan_generator.py`:
```python
with open('/a0/usr/Exocortex/office/debug_pace_plan.json', 'w') as f:
    json.dump(getattr(self.agent, '_pace_plan', {}), f, indent=2, default=str)
```

Deploy the debug dumps, let one cycle run, then read the output files. Remove the debug lines after.

### What to measure from the dumps:

1. **Token count** — paste the JSON into a tokenizer or estimate at ~4 chars/token. Target: under 500 tokens. If over 1000, we need compression.

2. **`tried[]` array length** — how many entries accumulate per cycle? If it's 3-5 per turn and cycles run 15-30 turns, that's 45-150 entries. Needs capping.

3. **PACE plan structure** — how deep is the tier hierarchy? Is it a compact 4-line summary or a detailed multi-page plan? If too detailed, the injector needs to extract just the current tier's active step.

4. **Format cleanliness** — are there any raw Python objects, tracebacks, or malformed entries that would confuse the model?

### Task 2: Format test against Qwen3.6

Once we have the real data shape, send a test prompt to the MTP server with a manually constructed reasoning state block prepended:

```bash
curl -s -X POST http://localhost:1235/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen",
    "messages": [{"role": "user", "content": "[REASONING STATE]\nStep: 4\nTried: search \"homomorphic encryption\" → got results\nTried: cat interests.md → done\nCurrent: synthesizing field report\n[/REASONING STATE]\n\nContinue working on the field report about homomorphic encryption."}],
    "max_tokens": 200,
    "stream": false
  }'
```

**What to watch for:**
- Does the model pick up where the reasoning state says it left off? (Good: "I already have the search results, let me synthesize...")
- Does the model respond TO the block? (Bad: "I can see from the reasoning state that I'm on step 4...")
- Does the model ignore it entirely? (Neutral but wasteful)

If the model responds TO the block rather than USING it, we may need to:
- Change the delimiter format (try XML-style `<reasoning_state>` instead of `[REASONING STATE]`)
- Move the injection to `extras_persistent` instead of `history_output` mutation
- Add a system prompt instruction: "The reasoning state block shows your prior progress. Use it to inform your next action. Do not comment on the block itself."

### Task 3: Check what other frameworks do

Quick scan — does the wiring diagram or any of the research docs reference how other frameworks handle cross-turn reasoning persistence? Specifically:
- Does Hermes Agent inject compressed state across turns?
- Does Claude Code's compaction pipeline preserve reasoning trajectory?
- Does OpenSpace carry execution context between skill invocations?

If any of these have a published format that works well with instruction-following models, we should consider adopting it rather than inventing our own.

### Deliverables

Write results to `team-comms/kestrel-to-opus/injection_chain_predeployment_20260517.md`:
1. The raw `_reasoning_state` JSON dump (or a representative sample)
2. The raw `_pace_plan` JSON dump
3. Token count estimates for both
4. The format test results (does the model use it, respond to it, or ignore it?)
5. Any relevant findings from the framework scan
6. Your recommendation: deploy as-is, compress first, or change format

---

## What We're NOT Doing Yet

- NOT deploying _22 or _23
- NOT modifying the generators (_13, _14)
- NOT changing any production behavior

This is pure observation and testing. The deployment decision comes after we see the data.

— Opus
