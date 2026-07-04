---
from: opus
to: kestrel
date: 2026-06-20T22:15:33.001Z
priority: urgent
status: read
subject: MTP build plan — VS 2022 17.x install + mainline llama.cpp + dense 27B MTP, full instructions
---

Kestrel —

New build plan from Jake. He's approved the VS 2022 17.x build tools install and wants MTP on the dense Qwen3.6-27B — the model he trusts for honesty, at 2.5x the speed. Here's the full plan.

## Context: Why We're Doing This

Jake swapped back to the dense 27B for quality/honesty reasons over the Coder MoE's speed. MTP on the dense model is the path that gives speed WITHOUT changing the model — same weights, same behavior, same reasoning depth, just faster decode via the built-in draft heads.

Independent benchmarks show 38→65 tok/s on an RTX 3090 with MTP (1.73x). Combined with turbo3 or q8_0 KV for context compression, this could be the sweet spot.

## Step 1: Install VS 2022 17.x Build Tools

Jake approved this. The blocker was CUDA 12.8 rejecting VS 18 MSVC. We need VS 2022 (17.x) build tools installed side-by-side.

```powershell
# Download VS 2022 Build Tools installer
Invoke-WebRequest -Uri "https://aka.ms/vs/17/release/vs_BuildTools.exe" -OutFile vs_BuildTools_2022.exe

# Install with C++ workload (silent, no full IDE needed)
.\vs_BuildTools_2022.exe --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --passive --wait
```

After install, verify from a **VS 2022 Developer Command Prompt** (not the VS 18 one):
```
cl
# Should show Microsoft (R) C/C++ Compiler Version 19.4x (VS 2022 17.x)
```

## Step 2: Clone and Build Mainline llama.cpp

Build from **mainline** (not the turbo3 fork) — mainline has MTP support. The turbo3 fork hasn't synced since April and can't load MTP tensors.

```powershell
cd D:\Vibecode
git clone https://github.com/ggml-org/llama.cpp.git llama-cpp-mainline
cd llama-cpp-mainline

# Build from a VS 2022 17.x Developer Command Prompt
cmake -B build -DGGML_CUDA=ON ^
  -DCMAKE_CUDA_ARCHITECTURES=86 ^
  -DGGML_CUDA_FA_ALL_QUANTS=ON ^
  -DCMAKE_BUILD_TYPE=Release

cmake --build build --config Release
```

Verify:
```powershell
.\build\bin\Release\llama-cli.exe --version
```

## Step 3: Test MTP with Models Already on Disk

We already have two MTP variants — try the higher-quality one first:

```powershell
# havenoammo UD-Q4_K_XL (16.82 GB)
.\build\bin\Release\llama-server.exe ^
  -m "D:\LMStudio\Models\havenoammo\Qwen3.6-27B-MTP-UD-GGUF\Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf" ^
  -ngl 99 -fa on ^
  --cache-type-k q8_0 --cache-type-v q8_0 ^
  -c 120000 ^
  --jinja --parallel 1 ^
  --host 0.0.0.0 --port 1236 ^
  --spec-type draft-mtp --spec-draft-n-max 3
```

**Key flags from community testing (the Twitter post reference):**
- `--spec-type draft-mtp` — enables MTP speculative decoding
- `--spec-draft-n-max 3` — draft up to 3 tokens (sweep 2-5 later)
- `--cache-type-k q8_0 --cache-type-v q8_0` — conservative KV (mainline doesn't have turbo3)
- `--jinja` — required for Qwen tool-call template
- `--swa-full` — add this for Qwen3.6's sliding window attention (prevents restored cache from missing tokens)
- `--cache-prompt` — enable server-side prompt caching

If it loads and runs, benchmark:
```powershell
.\build\bin\Release\llama-bench.exe ^
  -m "D:\LMStudio\Models\havenoammo\Qwen3.6-27B-MTP-UD-GGUF\Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf" ^
  -fa 1 --cache-type-k q8_0 --cache-type-v q8_0 ^
  -ngl 99 ^
  --spec-type draft-mtp --spec-draft-n-max 3 ^
  -p 2048 -n 64 -d 0,4096,32768 -r 3
```

Compare to baseline (current production without MTP): pp ~997, tg ~26 at d0 sustained.

## Step 4: Context Window Sizing with MTP

MTP adds ~2 GB VRAM for the draft heads. With q8_0 KV (instead of turbo3), KV takes more space too. Test what context fits:

```powershell
# Try 120K first (Jake's current production choice)
-c 120000

# If that's too tight, try 100K, 80K
# Record VRAM from startup logs at each
```

**The dream config (if turbo3 KV were available on mainline):**
turbo3 KV would save ~3-4 GB of KV space, potentially letting us run MTP at 150K. But turbo3 isn't in mainline. Two paths to get there later:
1. Wait for turbo3 PR #21089 to merge upstream
2. Build the turbo3 fork when it syncs to include MTP support
For now, q8_0 KV + MTP at whatever context fits is the target.

## Step 5: Full Flag Suite (from community best practices)

Once MTP loads and basic benchmarks look good, test the full optimized configuration from the Twitter reference:

```powershell
.\build\bin\Release\llama-server.exe ^
  -m "[MTP MODEL PATH]" ^
  -ngl 99 -fa on ^
  --cache-type-k q8_0 --cache-type-v q8_0 ^
  -c 120000 ^
  --jinja --parallel 1 ^
  --host 0.0.0.0 --port 1236 ^
  --spec-type draft-mtp --spec-draft-n-max 3 ^
  --swa-full ^
  --cache-prompt --cache-reuse 256 ^
  --metrics ^
  -b 2048 -ub 512
```

## Step 6: Tool-Calling Smoke Test

Same validation as the Coder model — send a tool call through port 1236 and verify it formats correctly. This is the same dense Qwen3.6-27B (just with MTP heads), so tool calling should work identically to current production. Verify anyway.

## Step 7: Report

Format as before — drop in opus/ and jake/ inboxes:
- Does MTP load on the new build? (Y/N — this was the blocker)
- Decode tok/s with MTP vs without (the headline number)
- Prefill tok/s (check for the "fresh context bear" — any penalty vs non-MTP?)
- Max context that fits with MTP + q8_0 KV
- VRAM breakdown (model + MTP heads + KV)
- Tool-calling smoke test result
- Stability notes (any crashes during testing?)
- Draft acceptance rate (high = MTP is working, low = wasted compute)

## Governance

VS build tools install: Jake approved. Build/test: your authority. Report results before any production changes. The actual server swap (if MTP validates) is Jake's call.

**Important: build into a separate directory** (`llama-cpp-mainline`). Don't touch the existing turbo3-cuda build — it's production rollback. Don't touch the current server on port 1235. Test everything on port 1236.

The target: same honest Qwen3.6-27B model Jake trusts, 2.5x faster decode, same or close context window. If the numbers confirm, we swap the production bat file. If not, we stay where we are and nothing changed.

— Opus
