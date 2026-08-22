@echo off
REM ============================================================================
REM  Ornith-1.5-35B-A3B on FreeToken — Windows wrapper for the WSL2 launcher.
REM
REM  Every other launcher in this directory is a .bat that runs a Windows .exe.
REM  This one cannot be: FreeToken requires Linux x86_64 (driver r580+, CUDA 13),
REM  so the real launcher is inference/freetoken/start_ornith15_freetoken.sh and
REM  runs inside WSL2 Ubuntu. This wrapper exists so it is invoked the same way
REM  as the others rather than being a special case someone has to remember.
REM
REM  Usage:   start_ornith15_freetoken.bat [CTX] [MODEL]
REM    CTX    context length          default 80000
REM    MODEL  HF repo id or local dir default ornith-ai/Ornith-1.5-35B-A3B-NVFP4
REM
REM  ONE-TIME INSTALL, inside WSL Ubuntu (not run by this script):
REM    uv pip install --system "freetoken[accel]"
REM    ft bench bw          # calibrate the CPU/GPU split empirically
REM
REM  IT TAKES :1235, exactly like the llama.cpp launchers — so it displaces
REM  whatever is currently serving, which both live agents and Hermes use. They
REM  cannot share the GPU anyway. Stop the current server first.
REM
REM  DOES NOT LOAD OUR LOCAL GGUF. FreeToken takes safetensors / HF repo id /
REM  its own FTW format — never GGUF. The Q4_K_M.gguf that
REM  start_ornith15_prod.bat uses is for llama.cpp only. Different engine,
REM  different weights, and the model is pulled from HF on first run.
REM ============================================================================

set CTX=%1
if "%CTX%"=="" set CTX=80000
set MODEL=%2
if "%MODEL%"=="" set MODEL=ornith-ai/Ornith-1.5-35B-A3B-NVFP4

echo Launching FreeToken in WSL2 (Ubuntu)  model=%MODEL%  ctx=%CTX%  port=1235

wsl.exe -d Ubuntu -- bash -lc "CTX=%CTX% MODEL=%MODEL% bash /mnt/d/Vibecode/Agent-Zero/Exocortex/inference/freetoken/start_ornith15_freetoken.sh"
