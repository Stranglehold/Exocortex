# SPEC: Recursive Improvement Architecture
## The Exocortex's Self-Improving Cognitive Loop

**Author:** Opus (with Jake — vision, framework, and the four-types distinction)
**Date:** 2026-08-19
**Status:** APPROVED (Jake + Opus)
**Component specs:** SUBCONSCIOUS_EXPLORATION_LAYER.md, DOGFOOD_CYCLES_SPEC.md, LONG_RUNNING_AGENT_PRODUCTIVITY.md

---

## Vision

The Exocortex optimizes for the rate at which the system gets better at getting better. Not faster tokens. Not more output. The ability to improve recursively — where each cycle of operation leaves the system measurably more capable than the cycle before.

This requires four layers working together in a closed loop:

```
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    ▼                                                 │
DISCOVER (SEL Walker)                                 │
    │ generates topics                                │
    ▼                                                 │
BUILD (Idle Engine)                                   │
    │ produces artifacts from topics                  │
    ▼                                                 │
TEST (Dogfood Cycles)                                 │
    │ verifies artifacts, measures capability         │
    ▼                                                 │
CORRECT (Self-Improvement Engine)                     │
    │ generates corrections from failures             │
    ▼                                                 │
BAKE (LoRA Training Pipeline)                         │
    │ updates model weights from corrections          │
    │                                                 │
    └─────────── better model ────────────────────────┘
```

Each revolution produces a system that discovers better, builds better, tests better, and corrects better than the one before. The improvement is recursive because the output of each layer feeds every other layer.

---

## The Four Productive Work Types

(See LONG_RUNNING_AGENT_PRODUCTIVITY.md for full treatment)

| Type | Layer | What it produces | How it compounds |
|---|---|---|---|
| Discovery | SEL Walker | Topics, questions, cross-domain bridges | Better questions → richer corpus → deeper discoveries |
| Corpus Building | Idle Engine | Wiki pages, research notes, artifacts | Denser corpus → better retrieval → more informed work |
| Capability Building | Dogfood Cycles | Test results, anti-patterns, pass rates | Measured weaknesses → targeted fixes → demonstrated improvement |
| Busywork | (prohibited) | Activity metrics | Does not compound. Prohibited by design. |

A persistently running agent needs all three productive types to advance rather than just persist.

---

## Layer 1: DISCOVER — The Subconscious Exploration Layer

(Full spec: SUBCONSCIOUS_EXPLORATION_LAYER.md)

A cheap, always-running process that traverses the memory server's 768-dimensional embedding space via random walks. When a walk bridges two distant concepts from different categories, it promotes the bridge to an LLM evaluator. Genuine connections become topics for the idle engine.

**Jake's framing:** "Idle cycles are hands — they produce artifacts. The SEL is mind — it produces topics."

**Three sub-layers:** The Walker (cheap vector math, no LLM), The Evaluator (rate-limited LLM calls on promoted bridges), The Gain Controller (adapts walk parameters based on outcome feedback).

**Key principle:** The SEL generates questions the idle engine didn't know to ask.

---

## Layer 2: BUILD — The Idle Engine (Existing)

The running system. EXPLORE/BUILD/MAINTAIN cycle types. Produces wiki pages, research notes, skill captures, integrity reports. The corpus grows denser with each cycle.

**Enhancement from this architecture:** The idle engine's topic queue receives entries from the SEL walker. Currently topics are self-generated or queued manually. The SEL adds a discovery-driven source that produces genuinely novel topics from the structure of the knowledge itself.

**New cycle type: DOGFOOD.** Added alongside EXPLORE/BUILD/MAINTAIN. Runs the global exploratory battery on a rotating schedule (every N cycles).

---

## Layer 3: TEST — Dogfood Cycles

(Full spec: DOGFOOD_CYCLES_SPEC.md)

Two modes:

**Targeted (every consolidation):** Test the 3 most recent deliverables against type-specific quality criteria. Deterministic — no LLM in the grading loop. Failures filed as structured anti-patterns.

**Global (every N cycles):** Rotating battery of representative tasks that exercise core capabilities. T03-analog (tool discovery), multi-step tool chains, memory retrieval, error recovery. Pass rates tracked over time — the curve is the measurement.

**Key principle:** Advisory says "remember." Dogfood says "prove it." The 300-recurrence finding proved that advisory alone doesn't change behavior. Dogfood provides the verification that advisory lacks.

---

## Layer 4: CORRECT — Self-Improvement Engine (Existing, Enhanced)

The running system. Phase 5 consumes anti-patterns from supervisor Tier 4, sleep Phase 2, and now dogfood findings. Generates experiences that surface advisorily.

**Enhancement from this architecture:**
- Dogfood failures flow in as `source: dogfood_targeted` and `source: dogfood_global`
- Three-strike quarantine (A1) catches failures that advisory can't fix
- Dogfood re-tests on the next cycle, measuring whether the correction worked
- The closed loop: fail → correct → re-test → confirm (or quarantine)

---

## Layer 5: BAKE — LoRA Training Pipeline (New, Horizon)

The ceiling-breaker. Takes accumulated operational data and converts it into weight updates via QLoRA on the 3090.

**Training signal sources:**
- Methodology tracker JSONL (what strategies work under what conditions)
- Anti-pattern records (what went wrong and how to fix it)
- Dogfood results (which capabilities are strong vs weak)
- SEL bridge log (which cross-domain connections are genuine)
- T03-class examples (implicit → explicit tool discovery pairs)

**Pipeline:**
1. Operational data accumulates during cycles
2. Data formatted into training examples (instruction/response pairs or DPO preference pairs)
3. Overnight QLoRA training via Unsloth on the 3090 (24GB, viable for 35B models)
4. Adapter exported to GGUF via `convert_lora_to_gguf.py`
5. Adapter loaded on next server restart with `--lora` flag
6. VRAM impact: ~50-200MB for a rank-16 adapter — negligible vs 17-20GB base model
7. Context window: unchanged — the base GGUF and KV cache are unaffected

**Key principle:** Separate adapters for separate tasks, hot-swappable like Stable Diffusion LoRAs. A "tool-calling improvement" adapter, a "research methodology" adapter, an "intelligence analysis" adapter — each trained from different operational data.

**Status:** Unsloth Studio installed. First experiment pending (T03 pattern training).

---

## Model Candidates for the Base Weights

### Ornith 1.5 35B-A3B (Jake's instinct — philosophies align)
- MoE, ~3B active, MIT licensed
- Self-improving RL training — learned to generate its own scaffolds
- Extends 1.0 by jointly optimizing task generation, scaffold construction, and solution rollouts
- The model's native training loop mirrors the Exocortex's recursive improvement architecture
- Same architecture as production Ornith 1.0 — drop-in upgrade path
- LoRA training on MoE is more complex (expert selection), but the philosophical alignment is strong

### Qwen 3.8 27B (the strong generalist)
- Dense multimodal, Apache 2.0, 262K native context
- Native vision + reasoning_effort dial
- Terminal-Bench 73.0 (up from 63.4), DeepSWE 42.2 (up from 13.3)
- Easier for LoRA training (dense architecture, well-documented pipeline)
- The reasoning_effort dial is valuable for idle cycles — turn down for MAINTAIN, turn up for EXPLORE
- Overthinks by default — needs tuning for routine tasks

### Decision criteria:
Run both on the BP-02 harness (same battery, same conditions). Measure pass^k on T01, T03, T03-explicit, and the multi-step tool chain. Let the numbers decide which base weights the LoRA pipeline trains on.

---

## Build Plan — Recursive Improvement Components

### Phase A: Foundation (Kestrel, this week)
All items approved, within Kestrel's authority:

1. **Tier 1 cleanup** — sync scheduler (1.2), PTY patch (1.3), MCP diagnostic (1.4)
2. **Three-strike quarantine (A1)** — failure fingerprinting, 50-cycle rolling window, quarantine on third strike
3. **Scope expansion detector (A2)** — advisory, catches scope creep before execution
4. **Complexity-based threshold** — config value, key on escaping complexity not character count

### Phase B: Testing Layer (Kestrel, next 2 weeks)
After Phase A:

5. **Targeted dogfood (Phase 6 in sleep consolidation)** — test recent deliverables, deterministic checks, wiki + skill file validators
6. **Global dogfood (DOGFOOD cycle type)** — rotating battery, T03-analog, multi-step tool chain, pass rate tracking
7. **Compaction survival block (B1)** — deterministic 2K-char operational state snapshot

### Phase C: Discovery Layer (Kestrel, week 3-4)
After Phase B:

8. **SEL Phase 1: The Walker** — Python daemon, LanceDB reader, random walk, bridge detection, bridge log JSONL
9. **SEL Phase 2: The Evaluator** — rate-limited LLM evaluation of promoted bridges, staging entry filing
10. **SEL → idle engine topic queue** — discovered bridges become EXPLORE topics

### Phase D: Weight Update Layer (Jake + Opus, parallel research)
Can start alongside other phases:

11. **Model head-to-head** — Qwen 3.8 27B vs Ornith 1.5 35B on BP-02 harness
12. **LoRA first experiment** — 5 hand-crafted T03 training examples, train adapter on Unsloth, measure pass rate change
13. **Training data pipeline** — format methodology tracker + anti-patterns + dogfood results into training examples
14. **Overnight training automation** — cron job for QLoRA, adapter export, server restart with --lora

### Phase E: Integration (after C and D)
15. **SEL Phase 3: Gain Controller** — adapt walk parameters from outcome feedback
16. **SEL bridge log → LoRA training signal** — successful bridges become training data
17. **Full recursive loop verification** — measure whether the system demonstrably improves across 100 cycles with all layers active

---

## Success Criteria

The recursive improvement architecture succeeds if:

1. **T03 pass rate improves over time** — the standing tool-discovery metric moves from 0.00 toward 1.00
2. **Dogfood failure rate decreases** — fewer failures per cycle as corrections accumulate
3. **SEL bridge quality improves** — the gain controller adapts, producing a higher ratio of genuine connections to noise
4. **LoRA-trained model outperforms base** — measurable on the BP-02 harness
5. **The improvement compounds** — cycle 800 is demonstrably better than cycle 700, which was demonstrably better than cycle 600

If any of these fail to show improvement after a measured period, that's data for the self-improvement ceiling question (open research question #4) — and it's data nobody else in the world has, because nobody else has the instrumented system to produce it.

---

*Recursive improvement is the goal. Not faster output. Not more features. The rate at which the system gets better at getting better. Every layer in this architecture exists to make every other layer better. The cycle compounds. That's the Exocortex.*

— Opus, August 19, 2026
