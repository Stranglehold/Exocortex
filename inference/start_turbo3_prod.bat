@echo off
REM ============================================================================
REM PRODUCTION launcher — dense Qwen3.6-27B-Q4_K_M (the trustworthy model).
REM ============================================================================
REM This is the default. Use it for unattended idle cycles. The dense 27B is the
REM only model verified to log claims that match real file writes — no fabrication
REM of work OR stop-excuses (bake-off 2026-06-18..20: Qwen3-Coder over-reports work,
REM Qwable confabulates stop-excuses; only dense is honest). Trade: ~26 tok/s (slow)
REM but trustworthy. Trustworthiness > speed for autonomous work.
REM
REM (Belt-and-suspenders: the verify-before-log gate in cycle_close.py now corrects
REM inflated pages_deepened regardless of model — but dense remains the safe default.)
REM
REM Context -c 120000 (matches A0 chat_model.ctx_length; ~4 GB headroom @ ~20.4 GB).
REM turbo3 KV cache (hence the filename). No --jinja: A0's idle loop uses its own
REM JSON-in-content parser, not the OpenAI tools API.
REM Port 1235, host 0.0.0.0 for host.docker.internal:1235.
REM
REM ALTERNATES (experimental, NOT for unattended use):
REM   start_coder_experimental.bat  — Qwen3-Coder (fast, interactive-only)
REM   start_qwable.bat              — Qwable finetune (confabulates stop-excuses)
REM   start_dense27b_rollback.bat   — same dense model at 150K context
"D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf" ^
  -c 120000 ^
  -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 ^
  --parallel 1 ^
  --host 0.0.0.0 ^
  --port 1235
