@echo off
REM ROLLBACK launcher — dense Qwen3.6-27B-Q4_K_M @ 150K (the pre-2026-06-18 production model).
REM Use this to revert if Qwen3-Coder (start_turbo3_prod.bat) ever needs backing out.
REM Stop the :1235 server first, then run this. Was the active prod model May 19 - Jun 18 2026.
"D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf" ^
  -c 150000 ^
  -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 ^
  --parallel 1 ^
  --host 0.0.0.0 ^
  --port 1235
