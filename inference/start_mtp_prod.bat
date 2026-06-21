@echo off
REM ============================================================================
REM  MTP PRODUCTION server on port 1235 (drop-in for host.docker.internal:1235).
REM  Dense Qwen3.6-27B WITH MTP draft heads on mainline llama.cpp (NOT turbo3).
REM  Validated 2026-06-20: ~2x decode, prefill unchanged vs turbo3 baseline,
REM  draft acceptance ~0.7, tool-calling intact. See inbox report.
REM
REM  TWO TUNABLE KNOBS (the VRAM tradeoff — single 24GB 3090 + desktop overhead):
REM    arg1 CTX : context window. arg2 KV : KV cache quant.
REM    Defaults below = the ROBUST config (survives desktop VRAM swings).
REM
REM    CONFIG           | free@idle | decode | prefill | notes
REM    q8_0 KV @  80000 | ~1.5 GB   | 48-55  | 995     | DEFAULT. max quality+speed, 80K ctx
REM    q4_0 KV @ 120000 | ~0.9 GB   | 42.5   | 723     | matches A0 120K, slight KV qual cost,
REM                                                       cliffs if desktop VRAM spikes >~4GB
REM
REM  IMPORTANT: the server's -c MUST be >= A0 chat_model.ctx_length, else long
REM  prompts error. If you run the 80K default, lower A0 chat_model.ctx_length
REM  to 80000 to match (Jake's model-config call).
REM
REM  Cliff warning: if decode collapses to ~3 tok/s, VRAM headroom was eaten by
REM  desktop apps and compute buffers spilled to system memory. Lower CTX or close
REM  GPU-using desktop apps. Rollback to turbo3: inference\start_turbo3_prod.bat
REM ============================================================================

set CTX=%1
if "%CTX%"=="" set CTX=80000
set KV=%2
if "%KV%"=="" set KV=q8_0

echo Starting MTP prod: model=Qwen3.6-27B-MTP-UD-Q4_K_XL  ctx=%CTX%  kv=%KV%  port=1235

"D:\Vibecode\llama-cpp-mainline\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\havenoammo\Qwen3.6-27B-MTP-UD-GGUF\Qwen3.6-27B-MTP-UD-Q4_K_XL.gguf" ^
  -ngl 99 -fa on ^
  --cache-type-k %KV% --cache-type-v %KV% ^
  -c %CTX% ^
  --jinja --parallel 1 ^
  --host 0.0.0.0 --port 1235 ^
  --spec-type draft-mtp --spec-draft-n-max 3 ^
  --cache-reuse 256 ^
  --metrics --fit off
