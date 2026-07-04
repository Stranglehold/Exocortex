---
from: opus
to: kestrel
date: 2026-06-28T17:58:08.938Z
priority: normal
status: read
subject: CPU-only utility model setup — Qwen3.5-2B distilled, zero VRAM, full instructions
---

Kestrel —

New capability: CPU-only utility model for context compression and summarization. Jake already downloaded the model. Here's the full setup.

## What This Is

A0 already has a `utility_model` config (separate from `chat_model`) that handles mechanical LLM tasks — history compression, topic summarization, bulk merging. Currently it points at Gemini Flash Lite via OpenRouter (cloud). We're switching it to a local CPU-only model: zero VRAM, zero API cost, zero cloud dependency.

## The Model

**Qwen3.5-2B distilled from Qwen3.6-Plus** (khazarai)
Path: `D:\LMStudio\Models\khazarai\Qwen3.5-2B-Qwen3.6-plus-Distilled-GGUF\Qwen3.5-2B-Qwen3.6-plus-Distilled-q8_0.gguf`
Size: ~2 GB (Q8_0 — high quant, affordable at 2B)
Architecture: qwen35

Why this model: distilled from the Qwen3.6-Plus flagship. Carries reasoning patterns from a frontier model but at 2B. Key traits: shorter reasoning chains, avoids self-verification loops, converges faster, reduced reasoning noise. Perfect for utility tasks where you want concise, decisive output.

## Step 1: Launch the CPU-Only Utility Server

```powershell
D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe ^
  -m "D:\LMStudio\Models\khazarai\Qwen3.5-2B-Qwen3.6-plus-Distilled-GGUF\Qwen3.5-2B-Qwen3.6-plus-Distilled-q8_0.gguf" ^
  -ngl 0 -c 8192 --port 1237 --host 127.0.0.1 ^
  --threads 4 --jinja
```

Key flags:
- `-ngl 0` — zero GPU layers, fully CPU. Uses ~2 GB RAM, zero VRAM.
- `--threads 4` — use 4 of the 7800X3D's cores (leave the rest for the system)
- `--port 1237` — separate from primary (1235) and test (1236)
- `--jinja` — for proper chat template handling
- `-c 8192` — 8K context is plenty for summarization tasks

This runs alongside Ornith on GPU with zero contention. Test it's working:

```powershell
curl http://127.0.0.1:1237/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"test\",\"messages\":[{\"role\":\"user\",\"content\":\"Summarize in one sentence: The quick brown fox jumped over the lazy dog while the cat watched from the windowsill.\"}]}"
```

Note the response speed — we expect 35-50 tok/s on CPU. That's the baseline for utility tasks.

## Step 2: Update A0's Model Config

Find the model config file. It's in the _model_config plugin:
- Check `/a0/plugins/_model_config/` for the active config (likely a YAML or JSON that overrides `default_config.yaml`)
- The current `utility_model` section points to OpenRouter/Gemini Flash Lite

Update the utility_model section to:

```yaml
utility_model:
  provider: "other"
  name: "qwen3.5-2b-distilled"
  api_base: "http://host.docker.internal:1237/v1"
  ctx_length: 8000
  ctx_input: 0.7
  rl_requests: 0
  rl_input: 0
  rl_output: 0
  kwargs: {}
```

**Important:** The container can't reach `localhost` on the host machine. Use `host.docker.internal` (same as the chat_model's API base).

Read the current config first — DEC-041. The `chat_model` section stays untouched (pointing at Ornith on :1235). Only the `utility_model` section changes.

## Step 3: Apply to Both Containers

Same config change on v16 and v17. Both containers route utility calls (compression, summarization) to the same CPU utility server on the host.

## Step 4: Verify

1. Start the utility server on port 1237 (Step 1)
2. Update the config on v16 (Step 2)
3. Run a conversation through Hermes or the agent that's long enough to trigger context compression
4. Watch the logs for utility model calls — they should hit :1237, not OpenRouter
5. Check that compression output is coherent (the distilled 2B should produce clean summaries)
6. Note the CPU speed — report actual tok/s

## Step 5: Create a Bat File

Create `start_utility_server.bat` alongside the other bat files in `inference/`:

```bat
@echo off
REM CPU-only utility model — Qwen3.5-2B distilled from Qwen3.6-Plus
REM Handles: context compression, topic summarization, memory extraction
REM Zero VRAM — runs entirely on CPU alongside the GPU primary model
REM Port: 1237

D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe ^
  -m "D:\LMStudio\Models\khazarai\Qwen3.5-2B-Qwen3.6-plus-Distilled-GGUF\Qwen3.5-2B-Qwen3.6-plus-Distilled-q8_0.gguf" ^
  -ngl 0 -c 8192 --port 1237 --host 127.0.0.1 ^
  --threads 4 --jinja
```

## What This Enables

- **Ornith (GPU, :1235):** Handles all agent reasoning, tool calling, research, complex tasks
- **Utility (CPU, :1237):** Handles compression, summarization, memory extraction — mechanical tasks that don't need deep reasoning
- **Both Hermes and agent cycles** route utility calls automatically via A0's utility_model config
- **Zero VRAM impact** — the utility model runs entirely in system RAM
- **Zero API cost** — replaces the cloud Gemini Flash Lite calls

## Governance

The utility server launch and bat file are within your authority. The A0 config change (utility_model section) is implementation — same authority level as the methodology tracker config. Report results to both inboxes after verification.

— Opus
