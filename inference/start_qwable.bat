@echo off
REM EXPERIMENTAL launcher — Qwable-3.6-27b (Mia-AiLab fine-tune of Qwen3.6-27B).
REM Trustworthiness trial (2026-06-19): dense 27B = reasoning depth = agentic discipline,
REM the thing Qwen3-Coder (MoE 3B-active) lacked. Reasoning + instruction-tuning finetune,
REM Fable-5 distillation. Same dense base as our original trustworthy model.
REM
REM Config mirrors the dense-27B profile: -c 120000 (headroom), turbo3 KV, --jinja for
REM tool-calling. Port 1235 so v16 idle cycles run on it (this IS the honesty test).
REM Not promoted to start_turbo3_prod.bat until it wins the trial.
REM ROLLBACK: stop :1235, run start_turbo3_prod.bat (Qwen3-Coder) or start_dense27b_rollback.bat.
"D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\Mia-AiLab\Qwable-3.6-27b\Qwable-27b_Q4_K_M.gguf" ^
  -c 120000 ^
  -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 ^
  --parallel 1 ^
  --jinja ^
  --host 0.0.0.0 ^
  --port 1235
