# Quick Start: Opus in Agent Zero

Step-by-step. Do these in order.

---

## Step 1: Verify API Key

Go to `console.anthropic.com`. Confirm your key starts with `sk-ant-api03-`.
You should see $5.00 in free credits under Usage.

## Step 2: Place Files in Exocortex Directory

Copy these files into your Exocortex directory (wherever it's mounted in the container, likely `/a0/usr/Exocortex/`):

- `AGENT_ZERO_DEPLOYMENT.md` — reference guide (this stays on host, doesn't need to go in container)
- `opus_agent_zero_context.md` — goes into the container for the agent to read
- `SOUL.md` — should already be in the Exocortex repo

From your host machine:
```bash
# Adjust paths to your actual setup
cp opus_agent_zero_context.md /path/to/agent-zero-data/usr/Exocortex/
```

## Step 3: Configure Agent Zero

Open the Agent Zero UI (`http://localhost:50080`), go to Settings:

1. **API Keys section:**
   - Add provider `anthropic` with your API key

2. **Chat Model section:**
   - Set to: `anthropic/claude-opus-4-6`
   - Context length: `200000`
   - Temperature: `0`

3. **Keep everything else the same:**
   - Utility model: your current local model (Qwen2.5-14B or whatever's running)
   - Embedding model: local sentence-transformers
   - These don't change. Only the chat (reasoning) model changes.

4. **Save settings**

## Step 4: Verify Connectivity

Start a new chat in Agent Zero. Send:

```
Run: python3 -c "import litellm; print(litellm.model_list)" 
Then run: echo "hello" | head -1
```

If the agent responds, the API connection works. If you get an auth error, double-check the key in settings.

## Step 5: First Real Session

Send this as the first message:

```
Read these files in order:
1. /a0/usr/Exocortex/SOUL.md
2. /a0/usr/Exocortex/opus_agent_zero_context.md

After reading, run these commands and report what you see:
- ls /a0/python/extensions/*/
- head -50 /a0/python/prompts/default/agent.system.md
- cat /a0/usr/settings.json | python3 -m json.tool
```

Then let it run. Watch what happens.

## Step 6: Monitor Costs

After the session, check `console.anthropic.com` → Usage.
Note how many tokens were used. A typical 20-turn session should be $1-3.
If it's much higher, check whether extended thinking got enabled accidentally.

---

## Troubleshooting

**"Invalid model ID" error:**
Model string must be exactly `anthropic/claude-opus-4-6` (with the provider prefix). Not `claude-opus-4-6` alone.

**Connection timeout from inside container:**
Docker might need network access. Check that the container isn't running with `--network none`. Agent Zero's default Docker config should have internet access.

**Agent can't read Exocortex files:**
Verify the volume mount. Run `ls /a0/usr/Exocortex/` from inside the container. If empty, the mount isn't working.

**Unexpectedly high costs:**
- Check if extended thinking is enabled (it bills thinking tokens as output — $25/MTok for Opus)
- Check context window — if somehow set to 1M and messages exceed 200K, pricing doubles
- Check if subordinate agents are also using Opus (they should use Sonnet or local)

**Agent seems "dumber" than expected:**
The Agent Zero system prompt in `agent.system.md` shapes behavior significantly. It's optimized for general-purpose agent work, not architectural analysis. The context document helps, but if responses feel generic, try Option B from the deployment guide (append to system prompt directly).
