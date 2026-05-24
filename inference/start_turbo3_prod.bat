@echo off
REM Production turbo3-cuda server for overnight idle cycles (2026-05-19).
REM Non-MTP Qwen3.6-27B-Q4_K_M, turbo3 KV. ctx = 150000 (Jake-set 2026-05-19;
REM below sweep max-safe 196K, leaves headroom under the WDDM cliff).
REM Port 1235, host 0.0.0.0 so containers reach via host.docker.internal:1235.
REM No MTP flags (non-MTP model). Thinking left ON (no --reasoning).
REM Speculative decoding (draft model) REMOVED 2026-05-20 — see investigation:
REM   stderr: "common_speculative_is_compat: the target context does not
REM            support partial sequence removal"
REM   stderr: "srv load_model: speculative decoding not supported by this context"
REM This turbo3-cuda fork lacks the upstream SSM-rollback fix (PR #20075).
REM `llama_memory_recurrent` (the DeltaNet/SSM state on Qwen3.6 hybrid mains) has
REM no rollback mechanism, so the `is_compat` check fails at startup and spec is
REM auto-disabled. Any standard `-md` draft will fail the same way on this binary
REM — it's not a flag/draft-selection problem, it's a missing fork patch.
REM Real fix paths: (1) rebase fork onto upstream with PR #20075, or (2) switch
REM to DFlash stack (lucebox-dflash) which sidesteps the rollback requirement.
"D:\Vibecode\Agent-Zero\Exocortex\inference\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\Jackrong\Qwen3.6-27B-GGUF\Qwen3.6-27B-Q4_K_M.gguf" ^
  -c 150000 ^
  -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 ^
  --parallel 1 ^
  --host 0.0.0.0 ^
  --port 1235
