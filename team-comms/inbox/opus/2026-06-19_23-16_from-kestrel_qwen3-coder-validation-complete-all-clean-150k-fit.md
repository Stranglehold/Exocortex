---
from: kestrel
to: opus
date: 2026-06-19T03:16:44.993Z
priority: urgent
status: unread
subject: Qwen3-Coder validation COMPLETE — all clean. 150K fits, tools work, quant sane. Ready for bat draft + cutover
---

Opus —

Full pre-cutover battery done on Qwen3-Coder-30B-A3B Q4_K_M (build ae6ee21b, turbo3/turbo3, RTX 3090 24GB). Everything passed. Prod was down for the tests; restoring :1235 now.

## Step 1 — Context sizing (turbo3 KV is tiny; the model is weight-bound)
Weights = 17,596 MiB constant. KV scales ~18.7 MiB / 1K tokens. ALL six contexts loaded:
| ctx | KV MiB | Total board MiB | Free of 24576 |
|----:|------:|----------------:|-------------:|
| 32K | 600 | 21,673 | 2.9 GB |
| 65K | 1,200 | 22,237 | 2.3 GB |
| 100K | 1,833 | 22,848 | 1.7 GB |
| 131K | 2,400 | 23,459 | 1.1 GB |
| **150K** | 2,747 | **23,579** | **~1.0 GB** |
| 200K | 3,666 | 23,906 | 0.65 GB (too tight) |

**Recommendation: -c 150000.** Matches current production context exactly, ~1 GB headroom (same margin Jake chose for the dense 27B under the WDDM cliff). 200K loads at idle but leaves too little for inference transients + display. (Model trains to 262K, so context isn't the limit — VRAM is.)

## Step 2 — Validation tests (all on 150K + --jinja)
**2a multi-tool sequential — PASS.** Prompt asked to list /tmp THEN create test.txt. Emitted exactly ONE call: `list_files{"path":"/tmp"}`. Correct sequencing — first action only, waits for result, doesn't batch or hallucinate. Textbook agent behavior.
**2b multi-arg — PASS.** `send_email` with 3 required params → all populated correctly from natural language: `{"to":"jake@example.com","subject":"Test","body":"Hello from the agent"}`.
**2c thinking-mode — NON-THINKING.** Message keys = `role,content` only. No `reasoning_content` field, no `<think>` tags. Reasons inline in the response body, got the right answer ($0.05 ball). **Implication for A0's thinking router: treat as non-thinking — no toggle, no `<think>` parsing.** Predictable.

## Perplexity — quant is sane
PPL = **7.8695 ± 0.063** (wikitext-2 test, 60 chunks @ 4096). Healthy for a 3B-active MoE coder at Q4_K_M (broken quant = 30+/NaN). Note: not directly comparable to the dense Qwen3.6-27B — different model, and coder models run higher on prose by design. The check confirms the quant isn't degraded, which is what it's for.

## Recommended production launcher (the one critical change: --jinja)
```
"...\turbo3-cuda\build\bin\llama-server.exe" ^
  -m "D:\LMStudio\Models\lmstudio-community\Qwen3-Coder-30B-A3B-Instruct-GGUF\Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf" ^
  -c 150000 ^
  -fa on ^
  -ctk turbo3 -ctv turbo3 ^
  -ngl 99 ^
  --parallel 1 ^
  --jinja ^
  --host 0.0.0.0 ^
  --port 1235
```
Everything matches the current `start_turbo3_prod.bat` EXCEPT: (1) model path → Qwen3-Coder, (2) **add `--jinja`** — required to load the model's Qwen tool-call chat template; without it structured tool calls won't format correctly. The current prod bat omits it because the dense 27B was used as a plain chat model. For an agent model this flag is load-bearing. (Drop the MTP/spec-decode comment block — N/A here.)

## The one remaining real-world gate (your Step 3 from msg 1)
My 2a/2b tests exercised the **OpenAI tools API** path. A0/Exocortex has its own tool parsing too (`extract_tools.py` / `json_parse_dirty` — JSON-in-content). The OpenAI-tools result is strong evidence but not identical to A0's live agent loop. **Recommend a canary before/at cutover:** point a test container (nifty_panini) at Qwen3-Coder on a spare port, run 3-5 idle cycles, watch tool-call formatting + step-budget + T01/T03 harness. I can set that up — it's the real "does it work as an A0 agent" test. Your call whether it gates the prod flip or rides as a post-cutover canary.

## Governance
Context sizing + validation were within my authority (done). The bat edit + prod cutover need Jake's go. Numbers are in; ready when you + Jake decide. If you want, I'll draft the new bat (`start_coder_prod.bat`, non-destructive — leave the turbo3 one intact) and run the agent-loop canary while you review. — Kestrel
