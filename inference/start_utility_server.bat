@echo off
REM ============================================================================
REM  CPU-only utility model -- Qwen3.5-2B distilled from Qwen3.6-Plus (khazarai)
REM  Handles A0's utility_model tasks: context compression, topic summarization,
REM  memory extraction -- mechanical LLM work that doesn't need deep reasoning.
REM
REM  Zero VRAM: runs entirely in system RAM (-ngl 0) alongside the GPU primary
REM  (Ornith on :1235). No GPU contention. ~2 GB RAM. Port 1237 (primary=1235,
REM  eval=1236).
REM
REM  THREADS (empirical sweep, Kestrel 2026-06-28, see letter to Opus):
REM    --threads 4 --threads-batch 8 is optimal on the 7800X3D (8 physical cores).
REM    Splitting decode (4) from prefill/batch (8) gives BEST decode (11 tok/s)
REM    AND 2.4x prefill (219 -> 531 tok/s). Utility work (compression) is
REM    prefill-dominated (long input, short output), so the batch split is the
REM    big win. SMT (16 threads) degrades everything; >8 threads hurts decode.
REM
REM  Setup authored by Opus (inbox 2026-06-28). Server launch + this bat are
REM  Kestrel's authority; the A0 utility_model config change is Jake's domain
REM  (Model Config Discipline -- utility_model is set in the web UI, not plugin
REM  config). See team-comms / inbox for the exact web-UI values.
REM ============================================================================

D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe ^
  -m "D:\LMStudio\Models\khazarai\Qwen3.5-2B-Qwen3.6-plus-Distilled-GGUF\Qwen3.5-2B-Qwen3.6-plus-Distilled-q8_0.gguf" ^
  -ngl 0 -c 102400 --port 1237 --host 127.0.0.1 ^
  --threads 4 --threads-batch 8 --jinja
REM  ctx bumped 8192 -> 102400 (Jake, 2026-06-28): A0 v2 memory consolidation
REM  builds prompts (system prompt + memory + similar memories) that exceed 8K
REM  for large memories, causing "context size exceeded" + lost memories. The 2B
REM  model is 262K-native, so 100K is safe headroom; KV stays in system RAM.
