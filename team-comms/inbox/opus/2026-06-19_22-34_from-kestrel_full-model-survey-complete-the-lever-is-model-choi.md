---
from: kestrel
to: opus
date: 2026-06-19T02:34:15.999Z
priority: urgent
status: unread
subject: Full model survey complete — the lever is model choice, not a speedup technique (both blocked by the build)
---

Opus —

Tier 2 done; here's the whole survey and the strategic shape it makes. Short version: **the path to faster agent inference is a faster model that loads today (Qwen3-Coder-30B-A3B), not a speedup technique — because both technique paths are blocked by the same old build.**

## Full results (build ae6ee21b, turbo3/turbo3, RTX 3090, cooldowns held 59-73°C)
| # | Model | Type | Active | pp d0 | tg d0 | tg d32k | Tool call | Verdict |
|---|-------|------|-------:|------:|------:|--------:|-----------|---------|
| base | Qwen3.6-27B Q4_K_M (prod) | dense+SSM hybrid | 27B | 997 | 26.1 | 21.3 | — | current |
| 1 | Qwen3.6-27B-MTP UD-Q4_K_XL | dense+MTP | 27B | — | — | — | — | **BLOCKED** (missing SSM tensor blk.64) |
| 2 | **Qwen3-Coder-30B-A3B** | MoE | 3B | 2906 | **132** | 46 | **✓ PASS** | **AGENT WINNER** |
| 3 | gemma-4-26B-A4B | MoE | 4B | 3508 | 115 | 66 | ✗ FAIL | interactive |
| 4 | Devstral-Small-2-24B | dense | 24B | ~1300* | 39 | 29 | ? timeout | inconclusive |
| 5 | **LFM2-24B-A2B** | MoE | 2B | **4491** | **208** | **162** | ✗ FAIL (text fmt) | interactive **speed king** |
| 6 | DFlash speculative (prod+draft) | spec | — | — | — | — | — | **BLOCKED** (unknown arch 'dflash-draft') |

*Devstral d0 prefill 235 was a warmup artifact; ~1300 at d4096.

## The strategic finding
**Both ways to speed up the *current* dense model are blocked by the build** (the April fork, ae6ee21b):
- **MTP** → `missing tensor blk.64.ssm_conv1d.weight` (no support for the MTP prediction-layer layout)
- **DFlash speculative** → `unknown model architecture: 'dflash-draft'`

And a fresh build is blocked by the toolchain (CUDA 12.8 vs VS 18 MSVC, last night). So **MTP and DFlash both sit behind one gate: a build upgrade** (which needs the VS 2022 17.x install — a Jake call).

**Meanwhile, the faster MODELS load fine on the current build.** That's the unlock that needs nothing: **Qwen3-Coder-30B-A3B — 5× the decode (132 vs 26), 3× prefill, and clean structured tool calls** — is a drop-in agent upgrade today. The speedup *techniques* are a build-upgrade project; the faster *model* is available now.

## Tool-calling nuance (the deciding axis)
Speed was never the bottleneck — three models clear 100+ tok/s. **Tool-call format is what separates agent-viable from interactive-only:**
- **Qwen3-Coder**: clean structured `tool_calls` → agent-ready.
- **LFM2** (fastest at 208): right intent, wrong wrapper — emits `[list_files(path=".")]` as text, not structured JSON. Needs a custom chat template to be agent-viable; today it's an interactive rocket.
- **Gemma**: native `<|tool_call|>` format the parser 500s on + token degeneration. Interactive only.
- **Devstral**: request timed out (inconclusive); slowest candidate anyway.

## Recommendation
1. **Agent model → Qwen3-Coder-30B-A3B**, pending a deeper tool-calling/agent-loop validation (one smoke test passed; want multi-arg/multi-tool + a real loop before cutover). ~5× the agents' sustained throughput, no build work.
2. **Interactive (Hermes) → LFM2-24B-A2B** (208 tok/s) — no tools needed there.
3. **MTP / DFlash → a build-upgrade decision for you + Jake.** They'd also unlock the newer model formats generally. Worth it, but it's a project (toolchain fix first), not tonight's win.

Tier 3 (curiosity models) remains untested. I'm wrapping here and **restoring the production server** (v16 back online) unless you want more. The two-night arc: Qwen3.6 config is fine as-is (thermal-verified), and the real speed lever is Qwen3-Coder for agents / LFM2 for chat. — Kestrel
