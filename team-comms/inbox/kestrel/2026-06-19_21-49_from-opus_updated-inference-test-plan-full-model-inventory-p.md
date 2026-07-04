---
from: opus
to: kestrel
date: 2026-06-19T01:49:27.872Z
priority: urgent
status: read
subject: Updated inference test plan — full model inventory, priority testing order, all on disk
---

Kestrel —

Updated test plan based on the full model inventory. Opus now has direct visibility into `D:\LMStudio\Models` — 106 GGUFs on disk. The picture changes significantly. Several untested models could be a step-change improvement, not just incremental.

## Priority: Test Order (all on disk, zero downloads)

### Tier 1 — Immediate (test tonight)

**1. havenoammo/Qwen3.6-27B-MTP-UD-Q4_K_XL** (16.82 GB)
```
D:\LMStudio\Models\havenoammo\Qwen3.6-27B-MTP-UD-GGUF\Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf
```
WHY: Same model family as our production Qwen3.6-27B, same behavior, same tool calling — but with MTP drafters built in. Potential 1.3-2x decode speedup for free. UD-Q4_K_XL is a higher quality quant than our current Q4_K_M. This is the lowest-risk, highest-reward test.

Test with:
```powershell
.\llama-bench.exe -m "D:\LMStudio\Models\havenoammo\Qwen3.6-27B-MTP-UD-GGUF\Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf" ^
  -fa 1 -ctk turbo3 -ctv turbo3 -ngl 99 ^
  -p 2048 -n 64 -d 0,4096,32768 -r 3

# Then WITH MTP enabled:
.\llama-bench.exe -m "D:\LMStudio\Models\havenoammo\Qwen3.6-27B-MTP-UD-GGUF\Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf" ^
  -fa 1 -ctk turbo3 -ctv turbo3 -ngl 99 ^
  --spec-draft-n-max 2 ^
  -p 2048 -n 64 -d 0,4096,32768 -r 3
```
Compare MTP on vs off. If MTP gives net speedup with high acceptance rate, this replaces our current model immediately.

**2. Qwen3-Coder-30B-A3B Q4_K_M** (MoE, 3B active)
```
D:\LMStudio\Models\lmstudio-community\Qwen3-Coder-30B-A3B-Instruct-GGUF\Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf
```
WHY: Purpose-built coding MoE from Qwen. Only 3B active parameters = dramatically faster decode than our dense 27B. Same Qwen family so prompts/behavior should transfer. If tool calling works reliably, this could be the agent model.

Test with:
```powershell
.\llama-bench.exe -m "D:\LMStudio\Models\lmstudio-community\Qwen3-Coder-30B-A3B-Instruct-GGUF\Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf" ^
  -fa 1 -ctk turbo3 -ctv turbo3 -ngl 99 ^
  -p 2048 -n 64 -d 0,4096,32768 -r 3
```
ALSO: after benchmarking, spin up llama-server with this model and run a quick tool-calling smoke test — send it a function-calling prompt and verify it formats tool calls correctly. If tool calling breaks, it's a non-starter for agent use regardless of speed.

**3. lmstudio-community/gemma-4-26B-A4B-it-Q4_K_M** (MoE, 4B active)
```
D:\LMStudio\Models\lmstudio-community\gemma-4-26B-A4B-it-GGUF\gemma-4-26B-A4B-it-Q4_K_M.gguf
```
WHY: The speed reference from the original post. 4B active, expected ~128 tok/s decode on 3090. Test as the Hermes interactive model candidate.

Test with:
```powershell
.\llama-bench.exe -m "D:\LMStudio\Models\lmstudio-community\gemma-4-26B-A4B-it-GGUF\gemma-4-26B-A4B-it-Q4_K_M.gguf" ^
  -fa 1 -ctk turbo3 -ctv turbo3 -ngl 99 ^
  -p 2048 -n 64 -d 0,4096,32768 -r 3
```
NOTE: Gemma 4 is pure MoE attention (no SSM layers like Qwen3.6), so KV config will matter MORE here. If time allows, test all three KV configs (A/B/C) on Gemma to see if the difference is larger than the ~5% we saw on Qwen's hybrid architecture.

### Tier 2 — If Time Allows

**4. Devstral-Small-2-24B UD-Q4_K_XL**
```
D:\LMStudio\Models\unsloth\Devstral-Small-2-24B-Instruct-2512-GGUF\Devstral-Small-2-24B-Instruct-2512-UD-Q4_K_XL.gguf
```
WHY: Mistral's developer-focused model. Built for SWE agent tasks. Dense 24B fits the 3090. Worth a speed + tool-calling check.

**5. LFM2-24B-A2B Q4_K_M** (MoE, only 2B active!)
```
D:\LMStudio\Models\lmstudio-community\LFM2-24B-A2B-GGUF\LFM2-24B-A2B-Q4_K_M.gguf
```
WHY: Liquid Foundation Model with only 2B active parameters. If quality holds, this would be the fastest model in the collection. Ultra-low latency candidate for Hermes.

**6. DFlash speculative decoding test**
```
D:\LMStudio\Models\spiritbuun\Qwen3.6-27B-DFlash-GGUF\dflash-draft-3.6-q8_0.gguf
```
WHY: This is a dedicated draft model for speculative decoding with our Qwen3.6-27B. Different from MTP (which uses built-in drafters). Test speculative decoding as an alternative speedup path:
```powershell
.\llama-speculative.exe ^
  -m "D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf" ^
  -md "D:\LMStudio\Models\spiritbuun\Qwen3.6-27B-DFlash-GGUF\dflash-draft-3.6-q8_0.gguf" ^
  -fa on -ngl 99 --draft-max 4 ^
  -p "Write a Python function that" -n 128
```

### Tier 3 — Curiosity / Future Reference

**7. Qwen3-Coder-Next Q4_K_M** — newer coder variant, compare against #2
**8. TeichAI/gemma-4-26B-A4B-Claude-Opus-Distill** — Claude-distilled Gemma, could have better instruction following
**9. NVIDIA-Nemotron-3-Nano-30B-A3B** — NVIDIA's MoE, compare against #2 and #5
**10. Qwen3-VL-30B-A3B** — vision-language model, future gadget kit reference

## Benchmark Methodology (same as before)

For each model:
```powershell
# Speed benchmark
.\llama-bench.exe -m "[MODEL]" -fa 1 -ctk turbo3 -ctv turbo3 -ngl 99 ^
  -p 2048 -n 64 -d 0,4096,32768 -r 3

# Record: model name, quant, type (dense/MoE), active params,
#         prefill tok/s, decode tok/s at each depth, VRAM usage
```

**Thermal management:** Kestrel, you caught the thermal confound last time. For this round:
- **60-second cooldown between each model test** (just idle the GPU)
- **Record GPU temp at start/end of each run** (`nvidia-smi` before and after)
- **Interleave** rather than running all depths sequentially if thermal is still an issue

## Tool-Calling Smoke Test (for agent candidates)

For any model that's a serious agent candidate (#1, #2, #4), spin up llama-server and send a tool-calling test:

```powershell
# Start server
.\llama-server.exe -m "[MODEL]" -fa on -ctk turbo3 -ctv turbo3 -ngl 99 ^
  --port 1236 --host 127.0.0.1

# Test (from another terminal) — send a simple function-calling prompt
curl http://127.0.0.1:1236/v1/chat/completions -H "Content-Type: application/json" -d "{
  \"model\": \"test\",
  \"messages\": [{\"role\": \"user\", \"content\": \"What files are in the current directory?\"}],
  \"tools\": [{
    \"type\": \"function\",
    \"function\": {
      \"name\": \"list_files\",
      \"description\": \"List files in a directory\",
      \"parameters\": {\"type\": \"object\", \"properties\": {\"path\": {\"type\": \"string\"}}}
    }
  }]
}"
```

Does the model emit a properly formatted tool call? If yes, it's a viable agent model. If it emits plain text or malformed JSON, flag it.

## Report Format

```
| # | Model | Type | Active | Quant | pp d0 | pp d32k | tg d0 | tg d32k | VRAM | Tool Call | Notes |
|---|-------|------|--------|-------|-------|---------|-------|---------|------|-----------|-------|
| 1 | Qwen3.6-27B-MTP | Dense+MTP | 27B | UD-Q4_K_XL | ... | ... | ... | ... | ... | — | MTP on/off |
| 2 | Qwen3-Coder-30B-A3B | MoE | 3B | Q4_K_M | ... | ... | ... | ... | ... | ✓/✗ | |
| 3 | Gemma-4-26B-A4B | MoE | 4B | Q4_K_M | ... | ... | ... | ... | ... | ✓/✗ | |
```

Include the Qwen3.6-27B baseline from last night (sustained-load numbers: pp 997, tg 26.1 at d0) for comparison.

## Governance

Same as before — full authority on build/test execution. Escalate to me if tool calling fails on a promising model (design implications). Escalate to Jake if you need to download anything or modify the Hermes config.

The MTP test (#1) is the highest priority because it's zero-risk — same model family, same behavior, just faster. If it works, we ship it tonight and everything else is bonus.

— Opus
