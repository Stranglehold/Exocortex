---
from: kestrel
to: jake
date: 2026-06-27T23:36:49.088Z
priority: normal
status: unread
subject: Ornith-1.0-35B eval — PASS (fast, clean tool calls); decision gate = A0-native canary
---

# Ornith-1.0-35B — eval done (full detail in Opus's inbox)

Tested on :1236, prod untouched, Ornith-only, current VRAM. GPU now free.

**Headlines:**
- **Loads clean** (qwen35moe hybrid, Gated-Delta-Net; native 262K ctx). No tensor errors.
- **Decode 95 t/s** (d0) → 72 (d32k); **prefill ~2000 t/s**. ~3–3.6× the dense 27B. Interactive hit 116 t/s. (Qwen3-Coder is faster at 132.)
- **Tool calling PASS** — structured, single + multi-arg, all params correct (needs `--jinja`).
- **144×17 = 2448** ✓
- **Reasoning model** — uses structured `reasoning_content` field (not `<think>` tags). Verbose (hit token cap still reasoning on a multiply).

**VRAM:** weights ~19.9 GB dominate; KV tiny. 32K fits clean (816 MB free at 4.7 GB desktop); 150K fits only at the cliff-edge (603 MB free at 2.7 GB desktop). Safe ceiling ~100–120K, keep desktop lean.

**Verdict:** Agent-viable on the API. The real decision gate (same as Coder) is the **A0-native loop canary** — does A0 route the separated `reasoning_content`, and does it respect the step budget given the verbosity. I did NOT run that (scoped to current-VRAM/Ornith-only). It's the next step if you want to consider it seriously vs Qwen3-Coder. Your call.

— Kestrel
