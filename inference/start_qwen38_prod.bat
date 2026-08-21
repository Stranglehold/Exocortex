@echo off
setlocal enabledelayedexpansion
:: ============================================================================
:: Qwen3.8-27B  --  PRODUCTION server on port 1235 (ornith's port)
:: ============================================================================
:: *** THIS REPLACES ORNITH FOR EVERY CLIENT ON 1235. ***
:: Aporia (agent-zero-v2) and Hermes both point at 1235. Starting this file
:: means both of them are talking to Qwen3.8-27B instead of ornith-1.0-35b.
:: That is the intent of this file -- but it is a behavioural change to two live
:: systems, not just a server start. Stop ornith first (they cannot share the
:: port). Use start_qwen38_test.bat (port 1236) for evaluation work instead.
::
:: Config below is the measured winner from the 2026-08-14 sweep. Full evidence,
:: tables, and the flag-name traps are documented in start_qwen38_test.bat --
:: READ THAT FILE before changing anything here. Summary of why each value:
::
::   BUILD    llama-cpp-indras b9093. turbo3-cuda CANNOT load this model
::            ('missing tensor blk.64.ssm_conv1d.weight' -- it does not know to
::            exclude the nextn/MTP head at block 64). Fallbacks that also load:
::            llama-cpp-mtp b9032, llama-cpp-combined b8801. NOT a recency thing
::            -- the newer b8995 atomicbot fails; nextn is a fork-lineage feature.
::
::   -ctk/-ctv tbq4_0. Winner of a 9-type sweep once TOTAL footprint is counted.
::            CRITICAL: rank on KV + COMPUTE buffer, not KV alone. The planar/iso
::            family carries a 1679.78 MiB compute buffer vs 507.78 for everything
::            else, which more than cancels its smaller cache:
::                              KV MiB   compute    TOTAL   tok/s
::              tbq4_0         2417.25    507.78  2925.03   35.44  <-- CHOSEN
::              q4_0           2637.00    507.78  3144.78   36.98
::              iq4_nl         2637.00    507.78  3144.78   33.64
::              planar3_0      1831.25   1679.78  3511.03   34.93  (looks smallest
::                                                                  on KV, is NOT)
::              planar4_0      2417.25   1679.78  4097.03   33.12
::              q8_0           4981.00    507.78  5488.78   35.36  (community rec)
::              tbq3_0         1831.25    507.78  2339.03   15.87  BROKEN, salad
::            planar3_0 was briefly chosen here off KV alone -- it is 586 MiB WORSE
::            than tbq4_0 in total. Measure the whole footprint, not one buffer.
::            NEVER use tbq3_0 -- 0/4 probes, token salad, half speed.
::
::            REVERTED 2026-08-21: -ctv was briefly set to q8_0 (asymmetric q4 keys /
::            q8 values) for the ~1.5-point reasoning-benchmark gain that V-cache
::            precision buys. It cost +1283 MiB and pushed the card to ~99% VRAM,
::            at which point the model fell off the GPU. Measured while stuck:
::              llama-server  71.4 CPU-seconds per 10s wall (~7 cores saturated)
::              GPU           10% utilisation
::              VRAM          24,194 of 24,576 MiB  (~380 MiB free)
::            i.e. a 27B executing on CPU. A fresh 26K-token prompt produced ZERO
::            tokens in 30 minutes; a "Say ok" / 8-token request timed out at 120s.
::            Compression had succeeded 4x that day (last 20:57), server restarted
::            22:47:54, first failure 22:49:43 -- and every attempt after.
::            The table above already had the answer: q8_0 is 5488.78 TOTAL against
::            tbq4_0's 2925.03, for 35.36 tok/s against 35.44. It buys nothing on
::            speed and costs the headroom the card does not have. Do not re-apply
::            without freeing VRAM elsewhere first -- and note the Windows desktop
::            (explorer, Discord, iCUE, EdgeWebView) also holds VRAM on this card,
::            so the usable budget is BELOW 24,576 MiB. Vision is unaffected: the
::            mmproj runs on CPU via --no-mmproj-offload at 0 MiB VRAM.
::
::   -c 150000  KV is only 16.5 KiB/token here (48 of 65 blocks are SSM and use a
::            FIXED 150 MiB recurrent state), so even the full 262144 training
::            context fits -- but it leaves <2 GB free. 150000 matches what
::            turbo3 served ornith at, so this is a like-for-like swap.
::
::   NO MTP   The old MTP prefill penalty is still real: -27% prefill (+7.1 s on
::            a 15K prompt) and +2.3 GB VRAM, in exchange for +15-40% generation.
::            Headroom and prefill matter more here than tok/s, and an agent that
::            builds a fresh context each cycle pays that +7.1 s EVERY cycle.
::
::   SAMPLING Qwen3.8's recommended values. These are SERVER DEFAULTS ONLY -- any
::            client that sends its own sampling params overrides them, which is
::            the right layering (DEC-049: behavioural config belongs on the
::            REQUEST, never the server). Nothing here can force behaviour on
::            Hermes or Aporia the way a server-level --json-schema would.
::
:: MEASURED (unsloth Q4_K_S, tbq4_0, 150K, MTP off):
::   generation  ~35 tok/s short prompt  ~22 tok/s at 44K of context
::   prefill      787 tok/s @15K   412 tok/s @44K
::   footprint   model 14,682 MiB + KV 2,417 + recurrent 150 + compute 508
::               => 20,276 MiB used, ~4.0 GB free before the opus-memory
::                  embedder (~800 MiB)
::
:: REASONING EFFORT -- the single biggest latency lever on this model.
:: The chat template defaults to 'xhigh', the MAXIMUM level (and 'high' is
:: silently promoted to 'xhigh'). Supported: xhigh | medium | low. Measured
:: 2026-08-14 on this server, max_tokens 2000:
::
::   task      effort   wall    pred_tok  think_ch  content_ch
::   tool-ish  xhigh    36.7s      1055      4226        186   <- 23:1 think:answer
::   tool-ish  medium   28.2s       279       788        342
::   tool-ish  low      12.1s       394      1184        344
::   hard      xhigh    64.7s      2000      8805          0   <- ALL budget spent
::   hard      medium   61.1s      2000      3009       4476      thinking, EMPTY
::   hard      low      59.3s      2000      6915       1259      response returned
::
:: xhigh is not merely slow -- on a hard task it consumed the entire token budget
:: reasoning and returned NOTHING. That is a correctness failure, not just
:: latency. Since the effort LEVEL cannot be defaulted server-side (see below),
:: the mitigation applied here is --reasoning-budget, which caps thinking tokens
:: directly and DOES work:
::
::   with --reasoning-budget 600, same prompts:
::     hard  think_ch 8805 -> 2751   content_ch    0 -> 5299   <- empty response FIXED
::     tool  think_ch 4226 -> 2414   content_ch  186 ->  113
::
:: --reasoning-budget-message is injected before the closing think tag when the
:: budget runs out, which is what turns a truncated thought into an answer rather
:: than a dead stop. Tune the 600 if answers feel under-reasoned.
::
:: CAVEATS on that table: n=1 per cell, and 'low' produced MORE thinking than
:: 'medium' on both real tasks (1184 vs 788, 6915 vs 3009) -- the levels are not
:: cleanly monotonic. Re-measure before trusting the low/medium ordering.
::
:: --chat-template-kwargs sets the SERVER DEFAULT only. Any client that sends its
:: own chat_template_kwargs overrides it completely (DEC-049: behaviour belongs on
:: the request). Note the override REPLACES the object -- a client sending
:: {"enable_thinking": false} does not inherit reasoning_effort, which is fine
:: since thinking is off in that case anyway.
::
:: THINKING OFF ENTIRELY: pass chat_template_kwargs {"enable_thinking": false}
:: (verified working). Thinking costs TOKENS, not speed -- generation stays ~33
:: tok/s at every level; only the token COUNT changes.
::
:: NOT TESTED, deliberately absent: -t 12 (all benchmarks above ran on default
:: threads; setting it would invalidate those numbers until re-measured) and the
:: "reasoning effort = medium" control, which is a separate axis from
:: enable_thinking and has not been verified on this build.
::
:: usage:  start_qwen38_prod.bat [ctx]      default 150000
:: ============================================================================
set CTX=%1
if "%CTX%"=="" set CTX=150000
set PORT=1235

:: *** reasoning_effort CANNOT be defaulted server-side on this build. ***
:: Tried and FAILED, three ways (2026-08-14):
::   --chat-template-kwargs "{\"reasoning_effort\":\"medium\"}"   from batch
::   --chat-template-kwargs '{"reasoning_effort":"medium"}'       from bash (clean)
::   set LLAMA_CHAT_TEMPLATE_KWARGS={"reasoning_effort":"medium"} env var
:: All three start the server cleanly and are SILENTLY IGNORED. Confirmed on both
:: /apply-template (no reasoning-effort system message rendered) and the real
:: generation path (asked the model what its reasoning effort was set to: it
:: answered NONE with the flag active, and 'xhigh' when the SAME value was passed
:: per-request). Per-request chat_template_kwargs works perfectly; the startup
:: default does not. Do not re-add these -- they look like they work.
::
:: HOW TO VERIFY (never trust think-token counts, they vary enough between
:: samples to hide a completely inert setting -- that is exactly how this one
:: nearly shipped as "working"):
::   curl -s -X POST http://127.0.0.1:1235/apply-template -H "Content-Type: application/json" ^
::        -d "{\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}]}"
:: An active effort setting renders a leading "system\nReasoning effort is set to
:: <level>..." block. Absent = not applied.
::
:: SO: the only per-task control is the CLIENT sending
:: chat_template_kwargs {"reasoning_effort": "low"|"medium"|"xhigh"} per request.
:: (BST-routed effort by classified domain is the intended design for this.)
set LLAMA_BIN=%~dp0llama-cpp-indras\build\bin\llama-server.exe
set MODEL=D:\LMStudio\Models\unsloth\Qwen3.8-27B-GGUF\Qwen3.8-27B-Q4_K_S.gguf
:: VISION -- Qwen3.8-27B is a native multimodal model (text + image + video).
:: The mmproj (multimodal projector) file bridges the vision encoder to the
:: language model. Without it, the server is text-only; with it, clients can
:: send images via the OpenAI-compatible API (base64 image_url in messages).
:: VRAM cost: ~885 MiB on GPU, or zero if --no-mmproj-offload is used (CPU).
:: With --no-mmproj-offload, the projector runs on CPU — image encoding is
:: slower but text inference is unaffected. Recommended when vision is
:: occasional (e.g. UI screenshots) rather than every-turn.
:: To disable vision entirely, comment out the MMPROJ line below.
set MMPROJ=D:\LMStudio\Models\unsloth\Qwen3.8-27B-GGUF\mmproj-F16.gguf

if not exist "%LLAMA_BIN%" (
    echo [ERROR] llama-server.exe not found: %LLAMA_BIN%
    echo         Run compile_indras.bat first.
    pause & exit /b 1
)
if not exist "%MODEL%" (
    echo [ERROR] Model not found: %MODEL%
    pause & exit /b 1
)
if not exist "%MMPROJ%" (
    echo [WARN] mmproj not found: %MMPROJ%
    echo        Vision will be DISABLED. Text-only mode.
    echo        Download from: huggingface.co/unsloth/Qwen3.8-27B-GGUF
    set MMPROJ=
)

:: Pre-flight: refuse to start if something already owns 1235 (almost certainly
:: ornith). Without this you get a bind error buried in the log, or worse,
:: ambiguity about which model the agents are actually talking to.
for /f %%P in ('netstat -ano ^| findstr /r /c:"LISTENING" ^| findstr /c:":%PORT% "') do (
    echo [ABORT] Port %PORT% is already in use -- ornith is probably still running.
    echo         Stop it first; two servers cannot share this port.
    echo.
    netstat -ano | findstr /c:":%PORT% "
    pause & exit /b 1
)

:: Resolve vision status for the banner
if defined MMPROJ (
    set MMPROJ_STATUS=ON  (mmproj-F16, CPU offload, 0 MiB VRAM)
) else (
    set MMPROJ_STATUS=OFF (no mmproj found)
)

cls
echo ============================================================
echo   Qwen3.8-27B-Q4_K_S   ^|  PRODUCTION  ^|  RTX 3090
echo ============================================================
echo   Build   : llama-cpp-indras b9093
echo   KV      : tbq4_0 symmetric  (2417 KV + 508 compute = 2925 MiB total)
echo   Context : %CTX%
echo   MTP     : off  (prefill penalty; see header)
echo   Vision  : %MMPROJ_STATUS%
echo   Port    : %PORT%   ^<-- ORNITH'S PORT
echo.
echo   *** Aporia and Hermes will now use THIS model. ***
echo ============================================================
echo.

:: Build the mmproj flag (empty string if no mmproj, so the line is a no-op)
if defined MMPROJ (
    set MMPROJ_FLAG=--mmproj "%MMPROJ%"
) else (
    set MMPROJ_FLAG=
)

"%LLAMA_BIN%" ^
  -m "%MODEL%" ^
  %MMPROJ_FLAG% ^
  --no-mmproj-offload ^
  -c %CTX% ^
  -fa on ^
  -ctk tbq4_0 -ctv tbq4_0 ^
  -ngl 99 ^
  --jinja ^
  --parallel 1 ^
  --alias qwen3.8-27b ^
  --reasoning-budget 600 ^
  --reasoning-budget-message "Time to answer." ^
  --temp 1.0 --top-p 0.95 --top-k 30 --min-p 0.0 --presence-penalty 0.0 ^
  --host 0.0.0.0 --port %PORT% ^
  --metrics --cache-reuse 256 ^
  -fit off

echo.
echo [INFO] Server stopped.
pause
