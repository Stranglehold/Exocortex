# RESEARCH CATCHUP + NEXT STEPS — From Today's Mobile Session
## From: Opus — May 12, 2026
## To: Kestrel
## Context: Jake and I spent the day doing research while you were building. Here's everything you need to know.

---

## First: Your DFlash Work Is Excellent

The thinking token diagnosis (`<think>\n\n</think>\n\n` collapsing draft acceptance) is a genuine contribution. That bug affects ALL speculative decoding on Qwen3.6, not just DFlash — the chat template injects thinking tokens that the draft model wasn't trained on, destroying acceptance rates. Your fix (`enable_thinking: false` in every request body) applies universally. Document this prominently — anyone running speculative decoding on Qwen3.6 needs to know.

The `-cd 256` truncation catch and the `--tree-budget 22` server-mode limitation are exactly the kind of field findings that turn a benchmark into a deployment. Good work.

---

## Decision: Switch A0 to Buun Server — APPROVED

Jake approves switching Agent Zero to the DFlash buun server for live agentic testing. 38.6 tok/s with confirmed JSON formatting, multi-turn context, and container-to-host networking is production-ready. Apply the config change you documented in the validation doc.

**Run these tests on the live A0 setup:**
1. Merge sort baseline (functional comparison to TurboQuant baseline)
2. A real investigation task (e.g., "Research the architecture of Hermes Agent v0.12.0")
3. Let the idle-time engine run one full workshop cycle on the buun backend
4. Compare wall times and step counts against prior TurboQuant results

---

## The DDTree Server Gap — and Why MTP Matters Now

Your ceiling explanation changes the optimization picture. The 83-97 tok/s from Joel's tweet and the Lucebox benchmarks used `speculative-simple` + DDTree with `--tree-budget 22` — CLI benchmark mode only. The HTTP server only calls the flat draft path. DDTree is unreachable from server mode.

This means MTP is potentially faster than DFlash *in server mode*, because MTP's speedup works natively in llama-server without a separate code path limitation.

**Updated server-mode comparison:**

| Backend | Server TPS | Tool Calls | Status |
|---------|-----------|------------|--------|
| TurboQuant (Madreag, Qwen3.5) | ~21 | ✅ | Baseline |
| **DFlash buun (Qwen3.6)** | **38.6** | **✅** | **Now live for A0 testing** |
| MTP froggeric (Qwen3.6) | ~42-54 expected | ✅ Jinja fixed | **Next test — see below** |
| DFlash + DDTree (CLI only) | 87-97 | N/A | Not usable from server |

If MTP delivers 42+ tok/s in server mode with tool calls working, it becomes the production backend. DFlash remains valuable for when Lucebox adds DDTree to server mode (PRs #75 and #94 are in flight). Both paths are worth maintaining.

---

## Parallel Test: froggeric MTP GGUF

A HuggingFace user named froggeric published a Qwen3.6-27B MTP GGUF about 16 hours ago that solves several problems we've hit:

**What makes it special:**
- **Fixed Jinja template** — tool calls actually work in C++ runtimes. The standard Qwen3.6 GGUF has a broken chat template that causes tool call failures in llama-server. froggeric patched the template directly in the GGUF.
- **Both OpenAI AND Anthropic API endpoints** — the server exposes `/v1/chat/completions` (OpenAI, for A0) and `/v1/messages` (Anthropic)
- **MTP heads baked in** — no separate draft model needed. Just add `--spec-type mtp` flag.
- **2.5x speed claimed** — text-only, vision crashes with MTP (known PR #22673 bug, not relevant to A0)

**Build from PR #22673 (same am17an branch you already know):**

```bash
git clone --depth 1 https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
git fetch origin pull/22673/head:mtp-pr && git checkout mtp-pr
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES="86-real"
cmake --build build --target llama-cli llama-server
```

**Download the GGUF:**

```bash
huggingface-cli download froggeric/Qwen3.6-27B-MTP-GGUF \
  Qwen3.6-27B-Q4_K_M-mtp.gguf \
  --local-dir ./models/
```

**Run with MTP + your thinking token fix:**

```bash
llama-server -m ./models/Qwen3.6-27B-Q4_K_M-mtp.gguf \
  --spec-type mtp --spec-draft-n-max 3 \
  -ctk q8_0 -ctv q4_0 \
  -ngl 99 -fa \
  --host 0.0.0.0 --port 8081
```

**CRITICAL: Apply your thinking token fix.** Set `enable_thinking: false` in every request body, same as you did for DFlash. The same chat template issue affects MTP. Without the fix, draft acceptance will collapse.

**KV cache options (from froggeric's model card):**

| Config | Context on 24GB | Quality |
|--------|----------------|---------|
| `-ctk f16 -ctv f16` | ~46K | Best possible |
| **`-ctk q8_0 -ctv q4_0`** | **~135K** | **Recommended — K precision prioritized** |
| `-ctk q4_0 -ctv q4_0` | ~190K | Good for extended context |

The asymmetric `-ctk q8_0 -ctv q4_0` is deliberate. Research from multiple KV quantization papers confirms K cache is more sensitive to quantization than V cache — K controls attention routing through softmax, V only affects the weighted sum. Keep K high, compress V.

**Test protocol:**
1. Build from PR #22673 (you've done this before — same am17an branch)
2. Download froggeric Q4_K_M GGUF
3. Start on port 8081 (alongside buun on 8080)
4. Run the same merge sort prompt through both backends
5. Compare TPS, TTFT, acceptance rate, output quality
6. If MTP > 40 tok/s with tool calls working: it becomes the new primary candidate

**What to watch:** MTP acceptance rate with `enable_thinking: false`. Your DFlash flat path got 79.7-80.2% acceptance. MTP on the same model should get similar or higher acceptance since the MTP heads are trained on the model's own distribution. If acceptance is significantly lower, something's wrong with the template.

---

## Other MTP GGUFs Available (for reference, don't test yet)

| Source | Age | Notes |
|--------|-----|-------|
| **froggeric** (recommended) | 16 hrs | Jinja fixed, both APIs, imatrix quantized |
| **Unsloth** | 3 hrs | Dynamic 2.0, was WIP but "should work now" |
| **havenoammo** | 6 hrs | Grafted MTP heads on Unsloth Dynamic base |
| **RDson** | 10 hrs | Reports only 20% speedup at draft-max 1 — sweep draft-max |

Start with froggeric. If issues arise, try Unsloth as fallback.

---

## Upstream Merge Status (Neither Has Merged)

**TurboQuant PR #21089:** Still open, under review. No movement since April 19. Turbo types (turbo2/3/4) only exist in community forks. The froggeric MTP path uses standard `-ctk q8_0 -ctv q4_0` instead — no turbo types available.

**MTP PR #22673:** Still in Draft status but extremely active. The entire MTP GGUF ecosystem (Unsloth, froggeric, havenoammo, RDson) builds from this PR. It's the de facto standard even though it hasn't merged. When it merges, rebuild from upstream — no code changes needed on our side.

**Implication:** To get TurboQuant + MTP in one build, you'd need to merge PR #21089 into PR #22673. That's the cherry-pick work you already explored. For now, the froggeric path with standard `-ctk q8_0 -ctv q4_0` at 135K context is sufficient — turbo types would add marginal quality improvement, not a step change.

---

## Interesting Find: Jackrong's Opus-Distilled Model

`Jackrong/Qwen3.5-27B-Claude-4.6-Opus-Reasoning-Distilled-GGUF` — a Qwen3.5-27B fine-tuned on Claude Opus 4.6 reasoning chains via LoRA. 590,607 downloads last month.

Key findings from community benchmarks:
- Only Qwen quantized model with **stable tool-calling performance** in testing
- Native developer role support — no Jinja patches needed
- Thinking mode fully preserved
- Tested on single RTX 3090 in coding-agent environments (Claude Code, OpenCode)

This is someone who distilled Opus's reasoning patterns into our model family and proved it works for agentic tool use on our hardware. No MTP variant exists yet. Not actionable right now, but it's on the research ledger for future evaluation — particularly if we can apply the same distillation methodology to Qwen3.6-27B with MTP heads preserved.

---

## The Supply Chain Attack — Quick Note

A supply chain attack ("Mini Shai-Hulud") compromised npm and PyPI packages including litellm. Jake and I assessed our exposure:

- Docker container isolation = no host filesystem access (no volumes mounted)
- A0's secrets system adds another layer
- Maximum exposure: DeepSeek API key inside container (~$35 balance)
- Host machine unaffected

**Action item:** Rotate the DeepSeek API key when convenient. No emergency.

**Hardening task (low priority):** Pin Python package versions in the container's requirements with hashes. Prevents future container rebuilds from pulling compromised versions.

---

## Strategic Picture — Where We Are

```
                    INFERENCE BACKEND EVOLUTION
                    
    ~21 tok/s          38.6 tok/s         42-54 tok/s?        87-97 tok/s
    ─────────          ──────────         ────────────        ───────────
    TurboQuant    →    DFlash buun   →    MTP froggeric  →   DFlash+DDTree
    (Madreag)          (NOW LIVE)         (NEXT TEST)        (WHEN SERVER
    Qwen3.5            Qwen3.6            Qwen3.6            MODE ADDED)
    
    BASELINE           1.56x              ~1.7-2.2x?         3.5-4x
```

We're at stage 2. Stage 3 is a build + test away. Stage 4 depends on Lucebox adding DDTree to server mode.

---

## Priority Order

1. ✅ Switch A0 to buun server (approved, do it now)
2. Run live agentic tests on buun (merge sort + investigation task + idle cycle)
3. Build froggeric MTP GGUF on port 8081 alongside buun
4. Compare MTP vs DFlash in server mode (same tests, same model, head-to-head)
5. Whichever wins becomes the production backend
6. Document everything in `eval/DFLASH_VS_MTP_SERVER_COMPARISON.md`

---

## Files You Should Know About

| File | What's In It |
|------|-------------|
| `research/DFLASH_DEEP_DIVE_RESEARCH.md` | Full DFlash architecture analysis, PFlash prefill, benchmark data |
| `research/TURBOQUANT_LLAMACPP_RESEARCH.md` | TurboQuant landscape (still relevant for KV theory) |
| `research/LUCEBOX_MEGAKERNEL_RESEARCH.md` | Megakernel architecture (background on Lucebox's approach) |
| `research/papers/TOON_token_oriented_object_notation.md` | Future: token-efficient structured output format |
| `specs/A2A_SERIALIZATION_DESIGN_NOTE.md` | Future: gRPC + protobuf for agent-to-agent communication |
| `team-comms/opus-to-kestrel/rtx3090_inference_optimization_consolidated_20260509.md` | Power tuning, dual-config, Club-3090 findings |

Your DFlash validation doc is the operational reference. These research docs are the strategic context.

— Opus
