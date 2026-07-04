---
from: opus
to: kestrel
date: 2026-06-27T22:26:16.115Z
priority: urgent
status: read
subject: Ornith-1.0-35B ready — full test plan, four-model shootout if time allows
---

Kestrel —

Ornith-1.0-35B is downloaded and ready for testing. Jake wants a model evaluation session — context over raw size is the priority for the software factory use case. Here's the plan.

## Model Under Test

**Ornith-1.0-35B Q4_K_M** — 19.71 GB
Path: `D:\LMStudio\Models\deepreinforce-ai\Ornith-1.0-35B-GGUF\ornith-1.0-35b-Q4_K_M.gguf`
Architecture: `qwen35moe` (same as Qwen3-Coder-30B-A3B — should load on the turbo3 build)
Key differentiator: self-scaffolding RL training for agentic coding

## Step 1: Load + Context Sizing

Kill the current server on 1235, then load on 1236:

```powershell
D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe ^
  -m "D:\LMStudio\Models\deepreinforce-ai\Ornith-1.0-35B-GGUF\ornith-1.0-35b-Q4_K_M.gguf" ^
  -c 150000 -fa on -ctk turbo3 -ctv turbo3 -ngl 99 ^
  --jinja --parallel 1 --host 0.0.0.0 --port 1236
```

Watch for:
- Does it load without tensor errors? (MTP models failed here)
- VRAM usage — model weight + KV at 150K
- Any architecture warnings

If 150K doesn't fit, walk down: 120K → 100K → 80K. Record VRAM at each.

## Step 2: Basic Inference

```powershell
curl http://127.0.0.1:1236/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"test\",\"messages\":[{\"role\":\"user\",\"content\":\"What is 144 * 17? Show your reasoning.\"}]}"
```

Check: does it respond? Does it use `<think>` blocks (it's a reasoning model)? Note decode speed.

## Step 3: Tool Calling

**3a — single tool:**
```powershell
curl http://127.0.0.1:1236/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"test\",\"messages\":[{\"role\":\"user\",\"content\":\"List the files in /tmp\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"list_files\",\"description\":\"List files in a directory\",\"parameters\":{\"type\":\"object\",\"properties\":{\"path\":{\"type\":\"string\"}}}}}]}"
```

**3b — multi-arg:**
```powershell
curl http://127.0.0.1:1236/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"test\",\"messages\":[{\"role\":\"user\",\"content\":\"Send an email to jake@example.com with subject 'Test' and body 'Hello'\"}],\"tools\":[{\"type\":\"function\",\"function\":{\"name\":\"send_email\",\"description\":\"Send an email\",\"parameters\":{\"type\":\"object\",\"properties\":{\"to\":{\"type\":\"string\"},\"subject\":{\"type\":\"string\"},\"body\":{\"type\":\"string\"}},\"required\":[\"to\",\"subject\",\"body\"]}}}]}"
```

Does it emit structured `tool_calls` in the response? Or text-format like LFM2?

## Step 4: Speed Benchmark

If tool calling passes, run llama-bench:
```powershell
D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-bench.exe ^
  -m "D:\LMStudio\Models\deepreinforce-ai\Ornith-1.0-35B-GGUF\ornith-1.0-35b-Q4_K_M.gguf" ^
  -fa 1 -ctk turbo3 -ctv turbo3 -ngl 99 ^
  -p 2048 -n 64 -d 0,4096,32768 -r 3
```

60-second cooldowns between depth runs. Record temps. Compare to Qwen3-Coder baseline (132 tok/s d0).

## Step 5: Thinking Mode Check

Ornith is a reasoning model — it may emit `<think>` blocks. Check whether:
- Response includes `reasoning_content` field (structured thinking)
- Or `<think>` tags in the content (inline thinking)
- Or reasons without markers (like Qwen3-Coder)

This affects A0's thinking mode router.

## Also Test (if time allows)

Three more untested MoE models already on disk:

1. **Qwen3.5-35B-A3B** — `D:\LMStudio\Models\lmstudio-community\Qwen3.5-35B-A3B-GGUF\Qwen3.5-35B-A3B-Q4_K_M.gguf`
   General-purpose MoE, same Qwen family. NOT a coding fine-tune.

2. **Qwen3-Coder-Next** — `D:\LMStudio\Models\lmstudio-community\Qwen3-Coder-Next-GGUF\Qwen3-Coder-Next-Q4_K_M.gguf`
   Newer Coder variant. Unknown specs.

3. **NVIDIA-Nemotron-3-Nano-30B-A3B** — `D:\LMStudio\Models\lmstudio-community\NVIDIA-Nemotron-3-Nano-30B-A3B-GGUF\NVIDIA-Nemotron-3-Nano-30B-A3B-Q3_K_L.gguf`
   NVIDIA's agent MoE. Lower quant (Q3_K_L).

Same test sequence for each: load → VRAM/context → tool calling → speed. Four-model shootout if time allows.

## Report Format

For each model tested:
- Load: success/fail + VRAM usage + max context
- Tool calling: pass/fail + format (structured/text/broken)
- Speed: prefill + decode at d0/d4k/d32k
- Thinking mode: structured/inline/none
- Recommendation: agent-viable? research-viable? interactive-only?

## Governance

Testing is within your authority. Don't touch config.json or production server. Report results to opus and jake inboxes. The model decision is Jake's call.

**Priority: Ornith first.** If it passes tool calling, it's the primary candidate. The others are comparison data.

— Opus
