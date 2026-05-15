@echo off
setlocal enabledelayedexpansion

:: ============================================================
::  CONFIGURATION
:: ============================================================

:: Model selection.
::
:: Option A: unsloth Q4_K_S MTP (15.01 GB, on disk) — START HERE for initial eval
::   MTP heads at Q4_K_S precision. Verified working with am17an at 43.7 tok/s.
::   Use this first to confirm the Indras build itself works on sm_86.
set MODEL_PATH=D:\LMStudio\Models\unsloth\Qwen3.6-27B-MTP-GGUF\Qwen3.6-27B-Q4_K_S.gguf
::
:: Option B: froggeric Q4_K_M MTP (15.4 GB approx) — better MTP head quality
::   MTP heads at Q8_0 precision. imatrix quantization. Fixed Jinja template.
::   Claimed source of 92.6% acceptance rate. Download if Option A validates.
::   huggingface-cli download froggeric/Qwen3.6-27B-MTP-GGUF Qwen3.6-27B-Q4_K_M-mtp.gguf --local-dir D:\LMStudio\Models\froggeric\Qwen3.6-27B-MTP-GGUF\
::set MODEL_PATH=D:\LMStudio\Models\froggeric\Qwen3.6-27B-MTP-GGUF\Qwen3.6-27B-Q4_K_M-mtp.gguf

:: Context.
:: 130K = safe target per brief. More headroom than am17an at 60K due to shared tensors.
:: Push to 200K only after VRAM headroom confirmed (target: 600+ MiB free during inference).
set CTX_SIZE=130000

:: KV cache type.
:: tbq4_0 = fused TBQ4 — the Indras-Mirror differentiator.
:: The FA kernel reads TBQ4 bytes inline (no dequant pass, no F16 buffer).
:: Brief said "turbo3" but the actual flag name in this fork is "tbq4_0" (verified in ggml.c).
:: tbq3_0 = 3-bit TBQ (not yet tested; may give more VRAM headroom for larger context).
:: DO NOT substitute q8_0/q4_0 here — that's the am17an build, not the point of this eval.
set KV_TYPE=tbq4_0

:: MTP draft tokens.
:: n=3 optimal per benchmarks (92.6% acceptance at 80.6 tok/s on 4090).
:: n=5 gives 90.1% at 79.6 tok/s — diminishing returns, stick with n=3.
set MTP_DRAFT_N=3

:: Port. Same as am17an so A0 integration test doesn't need config changes.
:: STOP am17an server before running this bat.
set PORT=1235

:: CPU threads (same as am17an build).
set THREADS=8

:: ============================================================

set LLAMA_BIN=%~dp0llama-cpp-indras\build\bin\llama-server.exe

cls
echo ============================================================
echo  llama-server (Indras-Mirror: MTP + TBQ4 fused)  ^|  RTX 3090
echo ============================================================
echo.
echo  Model:   %MODEL_PATH%
echo  Context: %CTX_SIZE% tokens
echo  KV type: %KV_TYPE% (turbo3 = fused TBQ4 inside FA kernel)
echo  MTP:     draft-n-max=%MTP_DRAFT_N%
echo  Port:    %PORT%
echo.
echo  Baseline (am17an): 43.7 tok/s, 69.3%% acceptance, 306 MiB free
echo  Target:   65+ tok/s, 85%%+ acceptance, 600+ MiB free
echo.
echo  STOP am17an server before running this. Same port (%PORT%).
echo ============================================================
echo.

if not exist "%LLAMA_BIN%" (
    echo [ERROR] llama-server.exe not found.
    echo         Run compile_indras.bat first.
    echo         Expected: %LLAMA_BIN%
    pause & exit /b 1
)

if not exist "%MODEL_PATH%" (
    echo [ERROR] Model file not found:
    echo         %MODEL_PATH%
    echo.
    echo         If using froggeric Option B, download with:
    echo         huggingface-cli download froggeric/Qwen3.6-27B-MTP-GGUF Qwen3.6-27B-Q4_K_M-mtp.gguf
    echo         --local-dir D:\LMStudio\Models\froggeric\Qwen3.6-27B-MTP-GGUF\
    pause & exit /b 1
)

:: Schedule KV cache warm-up (same mechanism as am17an).
echo [CACHE-WARM] Scheduling background warm-up (fires after server health check)...
start "" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0warm_cache_trigger.ps1" -Port %PORT%

:: Launch
:: Key flags vs am17an build:
::   -ctk tbq4_0 -ctv tbq4_0   -- fused TBQ4 KV (replaces --cache-type-k/v q8_0/q4_0)
::   --spec-type mtp            -- same
::   --flash-attn on            -- flash attention (required for TBQ4 kernel; bare -fa parses -ctk as its arg)
::   -rea off                   -- suppress reasoning/thinking tokens (Indras-Mirror flag; NOT -fit off)
::                                 IMPORTANT: -fit in this fork = "fit to device memory", NOT thinking filter
::                                 -fit off = don't auto-adjust context (keep explicit 130K, correct behavior)
::                                 -rea off = disable reasoning regardless of client enable_thinking setting
::   --batch-size 512           -- VRAM fix from am17an session (prevents compute buffer eviction)
::   --ubatch-size 128          -- same
::   --jinja                    -- Qwen3.6 chat template (same as am17an, required for tool calls)
::   -c 130000                  -- 130K context (was 60K on am17an due to VRAM pressure;
::                                  shared tensors save 682 MiB enabling larger context)
"%LLAMA_BIN%" ^
    --model "%MODEL_PATH%" ^
    --ctx-size %CTX_SIZE% ^
    -ngl 99 ^
    --flash-attn on ^
    -ctk %KV_TYPE% ^
    -ctv %KV_TYPE% ^
    --spec-type mtp ^
    --spec-draft-n-max %MTP_DRAFT_N% ^
    --port %PORT% ^
    --host 0.0.0.0 ^
    --parallel 1 ^
    --threads %THREADS% ^
    --batch-size 512 ^
    --ubatch-size 128 ^
    --metrics ^
    -fit off ^
    -rea off ^
    --jinja

echo.
echo [INFO] Server stopped.
pause
