@echo off
REM Start DFlash OpenAI-compatible server
REM Default: Qwen3.6-27B target, port 8000
REM
REM Usage:
REM   start_dflash.bat                         -- default (3.6 target, 3.6 draft -- needs gated draft)
REM   start_dflash.bat 35                      -- 3.5 distilled target + 3.5 draft (suboptimal pairing)
REM   start_dflash.bat 36x35                   -- 3.6 target + 3.5 draft (cross-family, recommended)
REM   DFLASH27B_KV_TQ3=1 start_dflash.bat ... -- enable TQ3_0 KV (3.5 bpv, 256K context)

set DFLASH_DIR=D:\Vibecode\Agent-Zero\Exocortex\inference\lucebox-dflash\dflash
set VENV=%DFLASH_DIR%\.venv\Scripts\python.exe

if "%1"=="35" (
    set DFLASH_TARGET=D:\LMStudio\Models\Jackrong\Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-GGUF\Qwen3.5-27B.Q4_K_M.gguf
    set DFLASH_DRAFT=%DFLASH_DIR%\models\dflash-draft-3.5
    set DFLASH_TOKENIZER=Qwen/Qwen3.5-27B
    echo Starting DFlash with Qwen3.5-27B distilled target + 3.5 draft
) else if "%1"=="36x35" (
    set DFLASH_TARGET=D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf
    set DFLASH_DRAFT=%DFLASH_DIR%\models\dflash-draft-3.5
    set DFLASH_TOKENIZER=Qwen/Qwen3.6-27B
    echo Starting DFlash with Qwen3.6-27B target + 3.5 draft [cross-family]
) else (
    set DFLASH_TARGET=D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf
    set DFLASH_DRAFT=%DFLASH_DIR%\models\draft
    set DFLASH_TOKENIZER=Qwen/Qwen3.6-27B
    echo Starting DFlash with Qwen3.6-27B target + 3.6 draft
)

set DFLASH_BIN=%DFLASH_DIR%\build\test_dflash.exe

cd /d %DFLASH_DIR%\scripts
%VENV% server.py --target "%DFLASH_TARGET%" --draft "%DFLASH_DRAFT%" --tokenizer "%DFLASH_TOKENIZER%" --port 8000 --prefix-cache-slots 0 --prefill-cache-slots 0
