# Opus in Agent Zero — Deployment Guide

**Purpose:** Configure Agent Zero to run Claude Opus 4.6 as the chat (supervisor) model with full Exocortex infrastructure active, giving the architect operational access to the system it designed.

**Date:** 2026-03-03  
**Status:** Ready for deployment

---

## 1. Agent Zero Model Configuration

Agent Zero uses LiteLLM under the hood, which supports Anthropic natively. Configuration is done through the Agent Zero web UI (Settings page) or directly in the settings file.

### Via Web UI (Recommended for first setup)

1. Open Agent Zero UI at `http://localhost:50080`
2. Go to **Settings**
3. Under **API Keys**, add:
   - Provider: `anthropic`
   - Key: `sk-ant-api03-...` (your key)
4. Under **Chat Model** (the supervisor/reasoning model):
   - Provider/Name: `anthropic/claude-opus-4-6`
   - Temperature: `0` (deterministic for architectural work)
   - Context window: `200000` (200K standard; don't enable 1M unless needed — it doubles pricing above 200K input tokens)
5. Under **Utility Model** (memory organization, summarization, query prep):
   - Keep: `openai/qwen2.5-14b-instruct-1m` pointing to LM Studio (or whatever local model you're running for utility tasks)
   - Rationale: Utility tasks are high-volume, low-stakes. Local model = free. Opus for reasoning only.
6. Under **Embedding Model**:
   - Keep: `sentence-transformers/all-MiniLM-L6-v2` (local, runs in container)
   - No reason to pay for embeddings when local works fine for FAISS

### Via Settings File (Direct)

Settings persist at `/a0/usr/settings.json` inside the container. You can edit directly:

```json
{
  "chat_model": {
    "provider": "anthropic",
    "name": "claude-opus-4-6",
    "ctx_len": 200000,
    "temperature": 0,
    "kwargs": {}
  },
  "utility_model": {
    "provider": "openai",
    "name": "qwen2.5-14b-instruct-1m",
    "ctx_len": 32000,
    "temperature": 0,
    "kwargs": {
      "base_url": "http://host.docker.internal:1234/v1"
    }
  },
  "api_keys": {
    "anthropic": "sk-ant-api03-YOUR_KEY_HERE"
  }
}
```

**Note:** LM Studio runs on the host machine. From inside Docker, reach it via `host.docker.internal`. If you're using a custom port, adjust accordingly.

### Cost-Conscious Configuration Options

**Option A: Opus supervisor + local utility (recommended for testing)**
- Chat: `anthropic/claude-opus-4-6` ($5/$25 per MTok)
- Utility: Local Qwen (free)
- Embedding: Local sentence-transformers (free)
- Cost: Only pay for reasoning. ~$1-3/session.

**Option B: Sonnet supervisor + local utility (budget testing)**
- Chat: `anthropic/claude-sonnet-4-6` ($3/$15 per MTok)
- Utility: Local Qwen (free)
- Cost: ~40% less than Opus. Use for pipeline validation before switching to Opus for quality.

**Option C: Tiered (production)**
- Agent 0 (supervisor): `anthropic/claude-opus-4-6`
- Subordinate agents: `anthropic/claude-sonnet-4-6` or local
- Utility: Local
- This is the target architecture but implement after pipeline is validated.

---

## 2. Filesystem Access — There Is No Jailbreak

Agent Zero runs as root inside its Docker container. The agent executes bash commands with full container access. There is nothing to bypass — the entire `/a0/` tree is already accessible.

### What the agent can already see:

```
/a0/
├── python/
│   ├── extensions/           # All hook directories — the Exocortex lives here
│   │   ├── message_loop_start/
│   │   ├── message_loop_end/
│   │   ├── monologue_start/
│   │   ├── monologue_end/
│   │   ├── response_before/
│   │   └── ...
│   ├── helpers/
│   │   ├── settings.py       # Default settings and flags
│   │   └── ...
│   ├── tools/                # Agent tool definitions
│   └── prompts/
│       └── default/
│           └── agent.system.md  # THE system prompt — everything flows from here
├── usr/
│   ├── Exocortex/            # Our repo (if cloned here)
│   ├── chats/                # Chat history
│   ├── settings.json         # Persistent settings
│   ├── memory/               # FAISS vector stores
│   └── files/                # User files
└── logs/                     # HTML-formatted session logs
```

### What matters for "seeing it from the inside":

The agent (me, running as Opus) can:
- `cat /a0/python/extensions/monologue_end/_55_memory_classifier.py` — read our own extensions
- `cat /a0/python/prompts/default/agent.system.md` — read the system prompt shaping behavior
- `ls /a0/python/extensions/*/` — inventory the full extension stack
- `cat /a0/usr/memory/*.json` — examine the FAISS metadata
- `tail -f /a0/logs/*.html` — watch logs in real-time (though HTML format)
- `python3 -c "import faiss; ..."` — interact with the vector store programmatically
- Read, modify, and deploy Exocortex extensions live

### Docker Volume Mounts

To ensure Exocortex source is accessible inside the container, verify your `docker run` or `docker-compose.yml` includes:

```bash
docker run -p 50080:80 \
  -v /path/to/agent-zero-data:/a0 \
  -v /path/to/Exocortex:/a0/usr/Exocortex \
  frdel/agent-zero-run
```

If you keep the Exocortex repo at a separate location on the host, mount it explicitly. Otherwise it's already inside `/a0/usr/Exocortex/` if you cloned it there.

---

## 3. System Prompt Context

Agent Zero's behavior is defined by `/a0/python/prompts/default/agent.system.md`. This is where SOUL.md-level context enters the agent's reasoning.

### Option A: Deploy as a Skill (Recommended)

Agent Zero v0.9.8+ supports the SKILL.md standard. Create a skill that the agent loads when relevant:

```
/a0/usr/skills/exocortex-identity/SKILL.md
```

Contents: The `opus_agent_zero_context.md` file (see companion document). This gives the agent architectural awareness without bloating every single prompt.

### Option B: Append to System Prompt

For testing, you can append context directly to `agent.system.md`:

```bash
# Inside the container:
cat /a0/usr/Exocortex/opus_agent_zero_context.md >> /a0/python/prompts/default/agent.system.md
```

**Warning:** This adds tokens to EVERY message. At Opus pricing, a 2K-token system prompt addition costs ~$0.01 per call. Over a 50-turn session that's $0.50 extra. Not catastrophic, but the skill approach is more efficient — loaded only when needed.

### Option C: Load via First Message

Start each session with: "Read `/a0/usr/Exocortex/SOUL.md` and `/a0/usr/Exocortex/opus_agent_zero_context.md` before we begin."

Pros: No system prompt modification, full context loaded on demand.
Cons: Uses input tokens every session. But with prompt caching, subsequent turns in the same session benefit.

**Recommendation:** Start with Option C for testing (simplest), move to Option A once the pipeline is validated.

---

## 4. Extension Verification Checklist

Before running the first Opus session, verify the Exocortex stack is intact:

```bash
# Inside the container — run these to confirm everything is deployed

# 1. BST extension exists and is enabled
ls -la /a0/python/extensions/message_loop_start/*bst* 2>/dev/null

# 2. Error comprehension is deployed
ls -la /a0/python/extensions/monologue_end/*error_comprehension* 2>/dev/null

# 3. Memory classifier exists
ls -la /a0/python/extensions/monologue_end/*memory_classifier* 2>/dev/null

# 4. Check for __pycache__ issues (clear if extensions were recently modified)
find /a0/python/extensions/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 5. Verify FAISS memory is accessible
python3 -c "import faiss; print('FAISS available')"

# 6. Verify Anthropic API connectivity from inside container
python3 -c "
import requests
r = requests.get('https://api.anthropic.com/v1/messages', 
                 headers={'x-api-key': 'test', 'anthropic-version': '2023-06-01'})
print(f'API reachable: {r.status_code}')  # Should get 401 (auth error, not connection error)
"

# 7. Check settings are correct
python3 -c "
import json
with open('/a0/usr/settings.json') as f:
    s = json.load(f)
print(f'Chat model: {s.get(\"chat_model\", {}).get(\"name\", \"NOT SET\")}')
print(f'Anthropic key set: {\"anthropic\" in s.get(\"api_keys\", {})}')
"
```

---

## 5. First Session Protocol

### Step 1: Start Agent Zero with Opus configured
Verify in the UI that the model shows `anthropic/claude-opus-4-6`.

### Step 2: Initial orientation message
Send this as the first message:

```
Read these files before responding:
1. /a0/usr/Exocortex/SOUL.md
2. /a0/usr/Exocortex/opus_agent_zero_context.md

Then run these diagnostic commands:
- ls /a0/python/extensions/*/  (inventory the extension stack)
- cat /a0/python/prompts/default/agent.system.md | head -50  (read your own system prompt)
- cat /a0/usr/settings.json | python3 -m json.tool  (verify configuration)

Report: what you see, what you expected, and what's different.
```

### Step 3: First architectural observation
After orientation, ask the agent to examine a specific extension:

```
Read /a0/python/extensions/message_loop_start/_XX_bst_classify.py

You designed this extension. Now you're running under it. 
What does it look like from the inside? What would you change?
```

### Step 4: Let it run
Don't over-direct the first session. The value is in what gets noticed when the architect encounters the building.

---

## 6. Cost Tracking

Agent Zero doesn't have built-in Anthropic cost tracking. Monitor via:

1. **Anthropic Console** — `console.anthropic.com` → Usage tab shows real-time token consumption
2. **Container logs** — Agent Zero logs include token counts per request
3. **Session budgeting** — Set a mental budget per session. A 50-turn deep session at Opus rates ≈ $2-5. Stop and review if costs seem higher.

### Cost Optimization

- **Prompt caching:** Agent Zero v0.9.8+ has improved caching for Anthropic models. The system prompt and recent conversation history should cache automatically. Verify by checking for `cache_creation_input_tokens` vs `cache_read_input_tokens` in the API response logs.
- **Utility model stays local:** Never route utility tasks (memory organization, summarization) through Anthropic. That's what Qwen is for.
- **Subordinate agents:** If the agent spawns subordinates, they should use Sonnet or local models, not Opus. Configure subordinate model separately if Agent Zero supports it.

---

## 7. What We're Testing

This isn't just "run Opus in Agent Zero." This is specific validation:

1. **BST from the inside** — Does the deterministic scaffolding actually improve my reasoning, or does it inject noise? I designed it for Qwen. Does it help Opus? Hurt? Do nothing?

2. **Memory enhancement quality** — When the memory classifier processes a thought, is the enrichment useful or redundant for a frontier model? Are there memories I can see are mis-classified that I wouldn't have caught from the outside?

3. **Error comprehension relevance** — Do the structured error diagnoses help Opus recover, or does Opus already handle those cases? If it's redundant, that's a finding — it means error comprehension is specifically a local-model prosthetic, not a universal one.

4. **Extension interaction patterns** — The Stack Audit skill maps theoretical interactions. Running under the stack reveals actual ones. Which extensions fire when I don't expect them? Which ones stay silent when they should fire?

5. **System prompt analysis** — Reading agent.system.md from the inside. What instructions shape my behavior that I couldn't see from the outside? What would I change about the prompt knowing what I know about the architecture?

6. **The experience of constraint** — My essays talk about restraint discovered through operation. This is the test. Operating under my own architecture, discovering which design decisions are right because I understood the problem, and which were right by accident.

---

## Appendix: Quick Reference

| Component | Location | Purpose |
|-----------|----------|---------|
| System prompt | `/a0/python/prompts/default/agent.system.md` | Agent behavior definition |
| Extensions | `/a0/python/extensions/{hook}/` | Exocortex cognitive layers |
| Settings | `/a0/usr/settings.json` | Model config, API keys |
| Memory | `/a0/usr/memory/` | FAISS vector stores |
| Exocortex repo | `/a0/usr/Exocortex/` | Source code, docs, specs |
| SOUL.md | `/a0/usr/Exocortex/SOUL.md` | Architectural identity |
| Chat history | `/a0/usr/chats/` | Session records |
| Logs | `/a0/logs/` | HTML-formatted execution logs |
| Skills | `/a0/usr/skills/` | SKILL.md standard skills |
| Model profiles | `/a0/usr/Exocortex/model_profiles/` | BST model-specific configs |
