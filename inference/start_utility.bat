@echo off
REM Utility/ingest model server (2026-05-25). Runs alongside turbo3 :1235.
REM Jackrong Qwen3.5-0.8B Q8_0 (Opus-reasoning-distilled), hybrid linear-attn.
REM 100K ctx with turbo3 K+V (3.25-bit). Only 6 of 24 layers carry a scaling KV
REM cache (full_attention_interval=4), so 100K KV is ~250MB; total ~1.4GB VRAM,
REM fits the ~3.2GB free headroom GPU-resident beside the 27B.
REM Purpose: A0 utility_model + OSS ingestion + SWARMFISH committee. Brain stays :1235.
REM --parallel 8: -c is the TOTAL KV budget split across 8 slots (~12.5K each) so the
REM 8-profile committee runs concurrently; same VRAM as 1 slot (KV sized by -c, not np).
REM Port 1236, host 0.0.0.0 so containers reach via host.docker.internal:1236.
"D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\Jackrong\Qwen3.5-0.8B-Claude-4.6-Opus-Reasoning-Distilled-GGUF\Qwen3.5-0.8B.Q8_0.gguf" ^
  -c 100000 ^
  -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 ^
  --parallel 8 ^
  --host 0.0.0.0 ^
  --port 1236
