@echo off
REM ############################################################################
REM  RETIRED 2026-08-22 -- THIS LAUNCHER CANNOT WORK ANY MORE. DO NOT RUN.
REM
REM  It invokes FreeToken inside WSL2. Both dependencies were removed while
REM  reclaiming the boot drive:
REM      ~/freetoken-env          DELETED (pip install freetoken restores it)
REM      ~/.cache/huggingface     DELETED (models now live under D:\LMStudio)
REM  and `ft` is no longer on PATH in Ubuntu, which was itself exported and
REM  re-imported to D:\WSL\Ubuntu.
REM
REM  It could not have worked regardless. FreeToken's offload backend pins expert
REM  banks via cudaHostRegister; WSL2 caps cumulative pinned host memory at
REM  ~1.00 GiB against the 16.9 GiB required, and that pool degrades with churn.
REM  Windows manages the limit, not the driver -- 13 attempts are documented in
REM  freetoken/ATTEMPT_LEDGER.md.
REM
REM  USE INSTEAD:  start_ornith15_freetoken_native.bat
REM  Native Windows pinned 40 GiB with no failure; it serves in ~26 minutes.
REM
REM  Kept, not deleted, because the ledger cites it.
REM ############################################################################
REM  --- original content below, inert ---
REM REM ============================================================================
REM REM  Ornith-1.5-35B-A3B on FreeToken — Windows wrapper for the WSL2 launcher.
REM REM
REM REM  Every other launcher in this directory is a .bat that runs a Windows .exe.
REM REM  This one cannot be: FreeToken requires Linux x86_64 (driver r580+, CUDA 13),
REM REM  so the real launcher is inference/freetoken/start_ornith15_freetoken.sh and
REM REM  runs inside WSL2 Ubuntu. This wrapper exists so it is invoked the same way
REM REM  as the others rather than being a special case someone has to remember.
REM REM
REM REM  Usage:   start_ornith15_freetoken.bat [CTX] [MODEL]
REM REM    CTX    context length          default 80000
REM REM    MODEL  HF repo id or local dir default ornith-ai/Ornith-1.5-35B-A3B-NVFP4
REM REM
REM REM  ONE-TIME INSTALL, inside WSL Ubuntu (not run by this script):
REM REM    uv pip install --system "freetoken[accel]"
REM REM    ft bench bw          # calibrate the CPU/GPU split empirically
REM REM
REM REM  IT TAKES :1235, exactly like the llama.cpp launchers — so it displaces
REM REM  whatever is currently serving, which both live agents and Hermes use. They
REM REM  cannot share the GPU anyway. Stop the current server first.
REM REM
REM REM  DOES NOT LOAD OUR LOCAL GGUF. FreeToken takes safetensors / HF repo id /
REM REM  its own FTW format — never GGUF. The Q4_K_M.gguf that
REM REM  start_ornith15_prod.bat uses is for llama.cpp only. Different engine,
REM REM  different weights, and the model is pulled from HF on first run.
REM REM ============================================================================
REM
REM set CTX=%1
REM if "%CTX%"=="" set CTX=80000
REM set MODEL=%2
REM if "%MODEL%"=="" set MODEL=ornith-ai/Ornith-1.5-35B-A3B-NVFP4
REM
REM echo Launching FreeToken in WSL2 (Ubuntu)  model=%MODEL%  ctx=%CTX%  port=1235
REM
REM REM Parsers pinned to the values Ornith's own model card uses in its vLLM/SGLang
REM REM commands. Qwen3.8 has no equivalent published recommendation, so its wrapper
REM REM leaves both on auto rather than borrowing these.
REM wsl.exe -d Ubuntu -- bash -lc "CTX=%CTX% MODEL=%MODEL% REASONING_PARSER=qwen3 TOOL_PARSER=qwen3_coder bash /mnt/d/Vibecode/Agent-Zero/Exocortex/inference/freetoken/start_ornith15_freetoken.sh"
