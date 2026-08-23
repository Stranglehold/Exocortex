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
REM REM  Qwen3.8-27B on FreeToken — Windows wrapper for the WSL2 launcher.
REM REM
REM REM  Same engine script as the Ornith launcher; only MODEL and SERVED_NAME
REM REM  differ, so there is one code path to keep correct rather than two
REM REM  near-identical ones that drift.
REM REM
REM REM  Usage:   start_qwen38_freetoken.bat [CTX] [MODEL]
REM REM    CTX    context length          default 80000
REM REM    MODEL  HF repo id or local dir default Qwen/Qwen3.8-27B-FP8
REM REM
REM REM  ---------------------------------------------------------------------------
REM REM  WHY FP8 AND NOT THE SMALLER NVFP4
REM REM
REM REM    Qwen/Qwen3.8-27B-FP8        27,781M  ~28 GB  MULTIMODAL (AutoModelForMultimodalLM)
REM REM    unsloth/Qwen3.8-27B-NVFP4   19,870M  ~20 GB  NO multimodal tag
REM REM
REM REM  The current llama.cpp server runs this model WITH vision enabled (mmproj),
REM REM  and the serving-stack buildplan scores vision support as a decision
REM REM  criterion. Picking the smaller NVFP4 would quietly drop a capability we
REM REM  currently have and make the comparison unlike-for-unlike. FP8 fits the
REM REM  ~55 GB WSL RAM budget comfortably, so the smaller file buys nothing here.
REM REM
REM REM  To try NVFP4 anyway (text-only, faster to load):
REM REM    start_qwen38_freetoken.bat 80000 unsloth/Qwen3.8-27B-NVFP4
REM REM
REM REM  ---------------------------------------------------------------------------
REM REM  THIS ONE IS THE EXPERIMENT, ORNITH IS THE SAFE BET
REM REM
REM REM  FreeToken's supported-models table lists "Qwen3.6 / Qwen3.5 MoE",
REM REM  "Qwen3.6 dense" and "Qwen3-MoE", with the caveat that "other checkpoints of
REM REM  the same architectures work too".
REM REM    Ornith-1.5-35B-A3B  reports qwen3_5_moe  -> matches a listed entry
REM REM    Qwen3.8-27B         reports qwen3_5      -> DENSE, and the table's dense
REM REM                                                entry is qwen3_6, not qwen3_5
REM REM  So Qwen3.8 is not explicitly covered. It may well work — FreeToken ships
REM REM  transformers 5.15.1, which knows qwen3_5 — but if one of the two fails to
REM REM  load, expect it to be this one, and that is information rather than a
REM REM  setback.
REM REM
REM REM  Also worth holding while reading any result: FreeToken's advantage is
REM REM  MoE-specific (bandwidth-adaptive expert offload). Qwen3.8-27B is DENSE, so
REM REM  there are no experts to offload and the MoE machinery does nothing. A
REM REM  smaller gap against llama.cpp here is the expected outcome, not a
REM REM  disappointment.
REM REM
REM REM  IT TAKES :1235 — stop the current server first.
REM REM ============================================================================
REM
REM set CTX=%1
REM if "%CTX%"=="" set CTX=80000
REM set MODEL=%2
REM if "%MODEL%"=="" set MODEL=Qwen/Qwen3.8-27B-FP8
REM
REM echo Launching FreeToken in WSL2 (Ubuntu)  model=%MODEL%  ctx=%CTX%  port=1235
REM
REM wsl.exe -d Ubuntu -- bash -lc "CTX=%CTX% MODEL=%MODEL% SERVED_NAME=qwen3.8-27b bash /mnt/d/Vibecode/Agent-Zero/Exocortex/inference/freetoken/start_ornith15_freetoken.sh"
