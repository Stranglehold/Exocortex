@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  CONFIGURATION
:: ============================================================

:: MTP-enabled GGUF selection -- uncomment one MODEL line only.
:: NOTE: LM Studio cannot run these models. Use this bat file (custom llama-server build).
::
:: Option A: havenoammo MTP-UD-Q4_K_XL (16.82 GB, Q8_0 MTP heads)
::   DOES NOT FIT on RTX 3090 (24 GB). Tested 20260513: 80 MiB VRAM free at 60K ctx
::   → WDDM eviction → decode collapses from 43 tok/s to 0.9 tok/s. Not usable.
::   UD-Q4_K_XL is 1.81 GB heavier than Q4_K_S; eats the entire headroom budget.
::   Would need a 40 GB GPU or much smaller context to be viable.
::set MODEL_PATH=D:\LMStudio\Models\havenoammo\Qwen3.6-27B-MTP-UD-GGUF\Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf
::
:: Option B: Unsloth Q4_K_S (15.01 GB, MTP heads at Q4_K_S quality -- ACTIVE)
::   VERIFIED WORKING: 43.7 tok/s at 80K ctx, 710 MiB VRAM free. 60K gives ~1218 MiB free.
::   Q4_K_S draft heads lower quality than Q8_0 (UD) but speculative decoding still benefits.
::   This is the correct choice for 24 GB until a smaller/more efficient variant is available.
set MODEL_PATH=D:\LMStudio\Models\unsloth\Qwen3.6-27B-MTP-GGUF\Qwen3.6-27B-Q4_K_S.gguf

:: Context size.
:: Without KV quantization (FP16): ceiling ~110K with the heavier Q4_K_XL weights.
:: With KV_TYPE set to q8_0/q4_0 (current): 80K confirmed stable — 710 MiB free (20260512).
::   VRAM at 80K: 23617 MiB used / 710 MiB free. WDDM does NOT page — 43.7 tok/s stable.
::   130K context: only ~100-500 MiB free. WDDM evicts compute buffers (990 MiB) → 4 tok/s.
::   Theoretical 160K fits by KV math but WDDM paging makes it unusable on 24GB.
:: A0 system prompt is 10069 tokens; 80K gives 70K of working context. Adequate.
:: 60K tested 20260513: ~508 MiB KV savings vs 80K. Recurrent state (598 MiB) is FIXED.
:: ~1.2 GB headroom at 60K vs ~710 MiB at 80K -- should prevent WDDM compute buffer eviction.
:: A0 system prompt ~10K tokens; 60K gives ~50K working context (was 70K at 80K).
:: VRAM during inference (20260514): compute buffers consume ~2400 MiB more than idle.
:: Idle headroom at 60K: ~2870 MiB. During inference: only 468 MiB free → WDDM paging → 1 tok/s.
:: Fix: batch-size 512 (was 2048) reduces prefill compute buffer peak by ~750 MiB.
:: ubatch-size 128 (was 512) reduces per-step decode buffer. MTP acceptance rate unaffected.
set CTX_SIZE=60000

:: KV cache quantization.
::   q8_0        — ~2x compression vs FP16, near-lossless. Standard llama.cpp type.
::   q4_0        — ~4x compression. More headroom. Standard llama.cpp type.
::   turbo4      — TurboQuant K-cache type (Madreag fork). Try Option A: swap to turbo4/turbo3.
::   turbo3      — TurboQuant V-cache type (Madreag fork).
::   f16         — no compression (default). Use only if testing at <=110K.
:: OPTION A TEST: set KV_TYPE_K=turbo4 and KV_TYPE_V=turbo3 then restart.
::   If server errors "unknown cache type" on startup -> Option A fails, move to Option B.
::   If server starts cleanly -> run tps_bench.ps1 and compare to q8_0 baseline.
:: REQUIRED: q8_0/q4_0 asymmetric KV. q8_0/q8_0 causes MTP head OOM (bufs.at() crash)
:: because after main model + q8_0/q8_0 KV + recurrent + compute, CUDA has 0 MiB free
:: for the MTP head's 1.4 GB backend buffer. q4_0 V saves ~1 GB, enough for the MTP head.
:: K precision matters for attention routing; V is weighted sum only (q4_0 is acceptable).
set KV_TYPE_K=q8_0
set KV_TYPE_V=q4_0

:: Jinja template (from Unsloth model page — verified working 20260513).
::   --jinja: use Jinja template engine for correct Qwen3.6 chat template handling.
::   Note: "default: enabled" in --help, but explicit flag ensures correct behavior.
::
:: --chat-template-kwargs {"preserve_thinking":true} NOT used — crashes am17an binary.
::   Flag exists in --help but the implementation is broken in this build.
::   Tested 20260513 via PowerShell ArgumentList (bypassing all shell quoting issues).
::   Server exits immediately after CUDA init with no error message. Do not add it back.
::   Model still performs thinking internally; tokens are just not surfaced in API output.
::   For A0 agentic use, this is correct behavior: clean tool-call JSON, no think tags.
::
:: A0 ADDITIONAL PARAMETERS: do NOT set enable_thinking=false. Remove it if present.
::   That LiteLLM parameter caused a cancel/retry death spiral (tasks 36,38,40... cancelled).
::   The model thinks server-side; A0 does not need to control this.

:: MTP draft tokens: 3 = higher throughput (~70%% acceptance), 2 = more stable
:: CONFIG C baseline (no MTP): 26.93 tok/s (20260512) / 35.53 tok/s (Kestrel 20260510)
:: CONFIG A (MTP n=3): 22-32 tok/s measured (20260512), variance from VRAM pressure
:: Kestrel measured 54.28 tok/s on 20260510 — system had more VRAM headroom that session
set MTP_DRAFT_N=3

:: Port — use a different port from TurboQuant build so both can run simultaneously during eval
set PORT=1235

:: CPU threads (same as TurboQuant build)
set THREADS=8

:: ============================================================

:: Binary includes hybrid model KV cache fix (2026-05-13):
:: server-context.cpp patched for Qwen3.5/3.6 checkpoint search bug.
:: Without fix: full context re-processed every turn (~250s at 10K tokens).
:: With fix: only delta processed on turn 2+ (~3-14s). Verified 29/33 cache hit.
:: Ref: https://github.com/ggml-org/llama.cpp/issues/22384
set LLAMA_BIN=%~dp0llama-cpp-mtp\build\bin\llama-server.exe

cls
echo ============================================================
echo  llama-server (MTP)  ^|  RTX 3090
echo ============================================================
echo.
echo  Model:   %MODEL_PATH%
echo  Context: %CTX_SIZE% tokens
echo  KV type: K=%KV_TYPE_K%  V=%KV_TYPE_V%
echo  MTP:     draft-n-max=%MTP_DRAFT_N% ^(0 = baseline, no MTP^)
echo  Port:    %PORT%
echo.
echo  API:     http://localhost:%PORT%/v1
echo.
echo  NOTE: This is the MTP evaluation build (am17an branch).
echo        TurboQuant build runs on port 1234.
echo        Compare throughput — do not switch A0 until eval passes.
echo ============================================================
echo.

:: Validate binary
if not exist "%LLAMA_BIN%" (
    echo [ERROR] llama-server.exe not found.
    echo         Run compile_mtp.bat first.
    echo         Expected: %LLAMA_BIN%
    pause & exit /b 1
)

:: Validate model
if not exist "%MODEL_PATH%" (
    echo [ERROR] Model file not found:
    echo         %MODEL_PATH%
    echo         Download from: unsloth/Qwen3.6-27B-MTP-GGUF on HuggingFace
    echo         Files: UD-Q4_K_XL.gguf ^(preferred^) or Qwen3.6-27B-Q4_K_S.gguf ^(fallback^)
    pause & exit /b 1
)

:: Build MTP flags — omit if MTP_DRAFT_N=0 (baseline run)
set MTP_FLAGS=
if not "%MTP_DRAFT_N%"=="0" (
    set MTP_FLAGS=--spec-type mtp --spec-draft-n-max %MTP_DRAFT_N%
)

:: Schedule KV cache warm-up in a minimized background window.
:: Polls for server health, then runs warm_cache.py inside exocortex_v16.
:: The warm-up fills the KV cache with the system prompt (~3-5 min, background).
:: When Jake's first message arrives, the system prompt is already cached →
:: Turn 1 TTFT drops from 3-5 min to ~10-30 seconds.
:: Requires exocortex_v16 to be running. If not, the extension fallback handles it.
echo [CACHE-WARM] Scheduling background warm-up (will fire after server health check)...
start "" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0warm_cache_trigger.ps1" -Port %PORT%

:: Launch
"%LLAMA_BIN%" ^
    --model "%MODEL_PATH%" ^
    --ctx-size %CTX_SIZE% ^
    -ngl 99 ^
    --flash-attn on ^
    --cache-type-k %KV_TYPE_K% ^
    --cache-type-v %KV_TYPE_V% ^
    --port %PORT% ^
    --host 0.0.0.0 ^
    --parallel 1 ^
    --threads %THREADS% ^
    --batch-size 512 ^
    --ubatch-size 128 ^
    --metrics ^
    -fit off ^
    --jinja ^
    %MTP_FLAGS%

echo.
echo [INFO] Server stopped.
pause
