@echo off
:: Qwen3.8-27B (unsloth Q4_K_S) -- TEST server
::
:: ============================================================================
:: BUILD: MUST be llama-cpp-indras. turbo3-cuda CANNOT load this model.
:: ============================================================================
:: turbo3-cuda (b8794) dies at load with:
::     llama_model_load: error loading model: missing tensor 'blk.64.ssm_conv1d.weight'
:: This is NOT a corrupt quant -- both the unsloth Q4_K_S and the
:: lmstudio-community Q4_K_M have byte-identical tensor layouts. blk.64 is an
:: MTP / "nextn" head (nextn.eh_proj / enorm / hnorm / shared_head_norm), and
:: b8794 derives the SSM-vs-attention layer pattern positionally, so it computes
:: "block 64 must be SSM" and looks for a conv1d weight that was never meant to
:: exist there. indras (b9093) knows to exclude the nextn layer -- it logs
:: "offloading 64 repeating layers" + "offloaded 66/66".
::
:: ARCHITECTURE: hybrid SSM/attention. NOT dense-attention, NOT MoE.
::   general.architecture = qwen35, block_count = 65, nextn_predict_layers = 1
::   blocks 0-63 : repeating 3x SSM + 1x ATTN  ->  48 SSM, 16 attention
::   block  64   : MTP / nextn head
::   --n-cpu-moe is WRONG here (no expert tensors). -ngl 99 offloads everything.
::
:: KV TYPE: use tbq4_0. Full sweep of all 9 quant types on this exact
:: model/build, scored on SIZE + SPEED + OUTPUT CORRECTNESS (2026-08-14).
::
:: *** RANK ON TOTAL FOOTPRINT (KV + COMPUTE), NOT ON KV ALONE. *** The
:: planar/iso family allocates a 1679.78 MiB compute buffer where every other
:: type uses 507.78, which more than cancels its smaller cache. planar3_0 was
:: briefly chosen here off the KV column and is in fact 586 MiB WORSE than
:: tbq4_0. Reading one buffer and calling it the footprint is the same error as
:: measuring a cold process and calling it a live one.
::
::     kv type      KV MiB   compute     TOTAL   tok/s  probes  garbage
::     tbq4_0      2417.25    507.78   2925.03   35.44     4/4      0.0  <-- CHOSEN
::     q4_0        2637.00    507.78   3144.78   36.98     4/4      0.0  (fastest)
::     iq4_nl      2637.00    507.78   3144.78   33.64     4/4      0.0
::     planar3_0   1831.25   1679.78   3511.03   34.93     4/4      0.0
::     iso3_0      1831.25   1679.78   3511.03   24.57     4/4      0.0
::     planar4_0   2417.25   1679.78   4097.03   33.12     4/4      0.0
::     iso4_0      2417.25   1679.78   4097.03   31.42     4/4      0.0
::     q8_0        4981.00    507.78   5488.78   35.36     4/4      0.0  (community
::                                                        rec: 2.6 GB worse, no gain)
::     tbq3_0      1831.25    507.78   2339.03   15.87     0/4      1.0  <-- BROKEN
::
:: DEPTH VALIDATION: needle-in-haystack, 4 distinct fact types
:: (alphanumeric code / year / proper name / spelled-out number) at 10/35/65/90%
:: depth in a ~65K-token prompt -> 4/4, identical to tbq4_0 and q4_0. This matters
:: because KV-quant damage is LENGTH-dependent; short probes alone cannot clear a
:: quant type. Caveat: needles test RECALL, not reasoning quality -- a quant could
:: preserve verbatim retrieval and still dull nuanced reasoning.
::
:: DO NOT USE tbq3_0 -- token salad, 0/4 probes, and HALF the speed. Note it is the
:: same 3-bit size class as planar3_0/iso3_0, which are both clean: the failure is
:: specific to that implementation, NOT a property of 3-bit KV.
::
:: The two forks expose DIFFERENT turboquant families --
:: these are NOT renames of each other, so do not translate one to the other:
::     turbo3-cuda:  turbo2, turbo3, turbo4, turbo1.5, turbo3_tcq, turbo2_tcq
::     indras:       tbq3_0, tbq4_0, planar3_0, iso3_0, planar4_0, iso4_0
:: (A comment in start_indras.bat calls tbq4_0 "turbo3", which is what led this
:: file to claim they were the same quant. They are NOT. Measured KV at 150K:
:: tbq4_0 = 2417 MiB, turbo3 = 1831 MiB -- different size classes entirely. Do
:: NOT assume ornith's KV settings and this file's are equivalent. Also note the
:: turbo numbers are NOT bit-widths: turbo1.5 = 2344 MiB is LARGER than
:: turbo3 = 1831 MiB. Do not infer precision from the name; measure it.)
::
:: THE OTHER BUILDS' FAMILY, measured on llama-cpp-combined b8801 (all 4/4, 0.0
:: garbage): turbo2_tcq 1319 MiB (smallest of ANY type tested) - turbo2 1712 -
:: turbo3 1831 - turbo3_tcq 1905 - turbo1.5 2344 - turbo4 2491.
:: NOT ADOPTED: every turbo type on `combined` generates at 27-29 tok/s while
:: every indras type generates at 31-37. That is uniform within each build, so it
:: is a BUILD-level speed difference, not a quant one. combined+turbo2_tcq would
:: buy 513 MiB over indras+planar3_0 at the cost of ~17% generation speed --
:: a bad trade while ~3.4 GB is already free.
::
:: DO NOT USE tbq3_0. It loads, and it saves real memory -- KV 2,417 -> 1,831 MiB
:: at 150K, exactly the -24% you would predict -- but the model output is TOKEN
:: SALAD ("Norse : 1. 1. The "Wicked" Daselelemente...") and generation HALVES to
:: 15.62 tok/s. Measured 2026-08-14. If you are ever tempted by the memory
:: saving, note that reading only the KV buffer size would have made it look like
:: a free win. Always probe OUTPUT, not just footprint, when changing KV quant.
::
:: CONTEXT: the GGUF advertises context_length = 262144 (the TRAINING context).
:: Unusually, that full window actually FITS on a 24 GB card, because only 16 of
:: 65 blocks carry a KV cache -- the 48 SSM blocks use a FIXED 150 MiB recurrent
:: state that does not grow with context at all.
::
::   MEASURED 2026-08-14, RTX 3090 24 GiB, unsloth Q4_K_S, -ctk/-ctv tbq4_0:
::     model buffer                 14,682 MiB  (+682 MiB CPU_Mapped)
::     recurrent state (RS)            150 MiB  CONSTANT, any context
::     KV                            16.5 KiB/token  (linear, verified 65K->262K)
::     compute buffer            495 MiB @65K  ->  836 MiB @262K
::
::     @ 65,536 ctx :  19,194 MiB used   5,132 free
::     @262,144 ctx :  22,367 MiB used   1,959 free   <-- loads, but NO headroom
::
::   262144 is proven to load AND generate (answered correctly off a 44K prompt),
::   but 1,959 MiB free leaves nothing for the opus-memory embedder (~800 MiB) or
::   for desktop swing (Firefox alone moves ~500 MiB). Default below is 150000 --
::   same context turbo3 prod serves ornith at, so it is a like-for-like swap,
::   and it leaves ~4 GB of real headroom.
::
::   THROUGHPUT (thinking off, generation):
::     short prompt        32.2 tok/s      prefill  760 tok/s @15K prompt
::     44K-token prompt    22.1 tok/s      prefill  412 tok/s @44K prompt
::   Thinking ON costs TOKENS, not speed (31.8 vs 32.7 tok/s). But it will spend
::   the entire max_tokens budget reasoning and return EMPTY content if the
::   budget is small -- pass chat_template_kwargs {"enable_thinking": false}
::   (verified working) for tool-calling / agent use.
::
:: PORT 1236 deliberately, NOT 1235: Aporia and Hermes point at 1235 (ornith).
:: Serving the test model on its own port means no config churn and no chance of
:: a live agent silently talking to a model under evaluation.
::
:: MTP SPECULATIVE DECODING: ENABLED BELOW. Measured 2026-08-14, clean A/B where
:: MTP was the ONLY changed variable (same model, quant, KV type, prompts):
::
::                       no MTP      MTP     draft acceptance
::     short prose        32.16  ->  37.10        49.7%
::     ~16k prompt       ~31.0   ->  48.29        80.0%
::     code generation      --   ->  45.10        72.4%
::
::   Acceptance tracks predictability: code drafts well, discursive prose poorly.
::   Cost: +2,308 MiB VRAM (recurrent state 150 -> 598 MiB for the draft context,
::   plus a 151 MiB draft KV). At 150K that leaves 1,742 MiB free, or ~940 once
::   the opus-memory embedder is up. Drop CTX to 120000 to buy back ~500 MiB.
::
::   FLAG NAME: indras is "--spec-type mtp". Mainline llama.cpp spells the same
::   thing "--spec-type draft-mtp" (see start_mtp_prod.bat) and indras REJECTS it
::   -- allowed values are [none|mtp|ngram-cache|ngram-simple|ngram-map-k|
::   ngram-map-k4v|ngram-mod]. Community configs written for mainline will fail.
::
::   "cache_reuse is not supported with MTP, it will be disabled" is EXPECTED and
::   is NOT a problem. It disables only --cache-reuse (gap-tolerant partial
::   reuse). Ordinary common-prefix KV reuse -- the one agents live on -- still
::   works. VERIFIED: 14,723-token prefix, turn 1 = 25,799 ms cold; turns 2 and 3
::   = 516 new tokens / ~1,300 ms with 14,207 cached. Do not let that warning
::   talk you out of MTP.
::
:: NOTE ON COMMUNITY CONFIGS (e.g. the circulating 3090 recipe): those assume a
:: HEADLESS LINUX box. This machine carries ~2,400 MiB of Windows desktop
:: (dwm/browser/apps) that they do not. Their "--cache-type-k q8_0 --cache-type-v
:: q8_0" costs ~4,834 MiB at 150K vs 2,417 MiB for tbq4_0 -- an extra ~2.4 GB
:: that is free on their hardware and is most of the headroom on this one. Also
:: note they pass no -c at all: on this build the default is 0 = "loaded from
:: model", which means the FULL 262144.
::
:: MTP IS OFF BY DEFAULT. The prefill penalty that got MTP shelved before is
:: STILL PRESENT. Clean A/B at 150K, same 14,723-token prompt, MTP the only
:: changed variable (measured 2026-08-14):
::
::                             MTP OFF      MTP ON     delta
::     cold prefill 14,723 tok  18,707 ms   25,799 ms  +7.1 s  (+38%)
::       rate                    787 tok/s   571 tok/s  -27%
::     warm turn (516 new tok)   1,008 ms    1,308 ms  +0.3 s  (+29%)
::     VRAM free                  ~3,400       1,742   -2,308 MiB
::
::   So MTP buys +15% (prose) to +40% (code) GENERATION in exchange for -27%
::   PREFILL and 2.3 GB. On this card headroom is scarcer than tok/s, and for an
::   agent that builds a fresh context each cycle the +7.1 s is paid PER CYCLE.
::   Hence: off. Pass a second arg to turn it on for A/B work.
::
:: usage:  start_qwen38_test.bat [ctx] [mtp]     default 150000, MTP off
::         start_qwen38_test.bat 150000 mtp      enable MTP
set CTX=%1
if "%CTX%"=="" set CTX=150000
set MTPARG=%2

set SPEC=
set SPECLBL=off
set REUSE=--cache-reuse 256
if /i "%MTPARG%"=="mtp" (
  set SPEC=--spec-type mtp --spec-draft-n-max 3 --spec-draft-type-k q8_0 --spec-draft-type-v q8_0
  set SPECLBL=on
  rem MTP disables --cache-reuse itself; passing it only prints a warning.
  set REUSE=
)

echo Starting Qwen3.8-27B  model=Q4_K_S (unsloth)  ctx=%CTX%  kv=tbq4_0  MTP=%SPECLBL%  port=1236  [indras b9093]
"D:\Vibecode\Agent-Zero\Exocortex\inference\llama-cpp-indras\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\unsloth\Qwen3.8-27B-GGUF\Qwen3.8-27B-Q4_K_S.gguf" ^
  -c %CTX% -fa on ^
  -ctk tbq4_0 -ctv tbq4_0 ^
  -ngl 99 ^
  --jinja --parallel 1 ^
  --alias qwen3.8-27b-q4 ^
  %SPEC% ^
  --host 0.0.0.0 --port 1236 ^
  --metrics %REUSE% ^
  -fit off
