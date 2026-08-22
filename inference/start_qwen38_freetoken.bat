@echo off
REM ============================================================================
REM  Qwen3.8-27B on FreeToken — Windows wrapper for the WSL2 launcher.
REM
REM  Same engine script as the Ornith launcher; only MODEL and SERVED_NAME
REM  differ, so there is one code path to keep correct rather than two
REM  near-identical ones that drift.
REM
REM  Usage:   start_qwen38_freetoken.bat [CTX] [MODEL]
REM    CTX    context length          default 80000
REM    MODEL  HF repo id or local dir default Qwen/Qwen3.8-27B-FP8
REM
REM  ---------------------------------------------------------------------------
REM  WHY FP8 AND NOT THE SMALLER NVFP4
REM
REM    Qwen/Qwen3.8-27B-FP8        27,781M  ~28 GB  MULTIMODAL (AutoModelForMultimodalLM)
REM    unsloth/Qwen3.8-27B-NVFP4   19,870M  ~20 GB  NO multimodal tag
REM
REM  The current llama.cpp server runs this model WITH vision enabled (mmproj),
REM  and the serving-stack buildplan scores vision support as a decision
REM  criterion. Picking the smaller NVFP4 would quietly drop a capability we
REM  currently have and make the comparison unlike-for-unlike. FP8 fits the
REM  ~55 GB WSL RAM budget comfortably, so the smaller file buys nothing here.
REM
REM  To try NVFP4 anyway (text-only, faster to load):
REM    start_qwen38_freetoken.bat 80000 unsloth/Qwen3.8-27B-NVFP4
REM
REM  ---------------------------------------------------------------------------
REM  THIS ONE IS THE EXPERIMENT, ORNITH IS THE SAFE BET
REM
REM  FreeToken's supported-models table lists "Qwen3.6 / Qwen3.5 MoE",
REM  "Qwen3.6 dense" and "Qwen3-MoE", with the caveat that "other checkpoints of
REM  the same architectures work too".
REM    Ornith-1.5-35B-A3B  reports qwen3_5_moe  -> matches a listed entry
REM    Qwen3.8-27B         reports qwen3_5      -> DENSE, and the table's dense
REM                                                entry is qwen3_6, not qwen3_5
REM  So Qwen3.8 is not explicitly covered. It may well work — FreeToken ships
REM  transformers 5.15.1, which knows qwen3_5 — but if one of the two fails to
REM  load, expect it to be this one, and that is information rather than a
REM  setback.
REM
REM  Also worth holding while reading any result: FreeToken's advantage is
REM  MoE-specific (bandwidth-adaptive expert offload). Qwen3.8-27B is DENSE, so
REM  there are no experts to offload and the MoE machinery does nothing. A
REM  smaller gap against llama.cpp here is the expected outcome, not a
REM  disappointment.
REM
REM  IT TAKES :1235 — stop the current server first.
REM ============================================================================

set CTX=%1
if "%CTX%"=="" set CTX=80000
set MODEL=%2
if "%MODEL%"=="" set MODEL=Qwen/Qwen3.8-27B-FP8

echo Launching FreeToken in WSL2 (Ubuntu)  model=%MODEL%  ctx=%CTX%  port=1235

wsl.exe -d Ubuntu -- bash -lc "CTX=%CTX% MODEL=%MODEL% SERVED_NAME=qwen3.8-27b bash /mnt/d/Vibecode/Agent-Zero/Exocortex/inference/freetoken/start_ornith15_freetoken.sh"
