@echo off
REM ============================================================================
REM EXPERIMENTAL — Qwen3-Coder-30B-A3B (NOT the production model).
REM ============================================================================
REM Do NOT use for unattended idle cycles. Qwen3-Coder OVER-REPORTS work when
REM web search is down (claims "deepened N pages w/ verified sources" on cycles
REM that wrote nothing — verified 2026-06-18). Its honesty is search-dependent.
REM It IS ~5x faster (132 vs 26 tok/s) and tool-calls cleanly, so it's fine for
REM INTERACTIVE / human-in-the-loop use where a person catches errors.
REM
REM Production launcher is start_turbo3_prod.bat (dense Qwen3.6-27B — trustworthy).
REM
REM Config: -c 120000, turbo3 KV, --jinja (required for the Qwen tool-call template).
"D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\lmstudio-community\Qwen3-Coder-30B-A3B-Instruct-GGUF\Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf" ^
  -c 120000 ^
  -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 ^
  --parallel 1 ^
  --jinja ^
  --host 0.0.0.0 ^
  --port 1235
