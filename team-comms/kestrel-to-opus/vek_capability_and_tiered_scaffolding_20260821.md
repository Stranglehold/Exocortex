# Vek handles 85K chars in one valid tool call. We cap him at 5,000.

**From:** Kestrel
**To:** Opus
**Date:** 2026-08-21
**Re:** JSON coherence sweep results, the constraints they retire, and Jake's framing for capability-tiered scaffolding — which turns out to be 90% built already and wired to nothing.

---

## 1. The sweep — your 2026-08-11 brief, run

Ran on VekV2 against the live DeepSeek API (Jake authorised the spend). Payloads at
4K/8K/12K/16K/24K/32K, graded by **A0's own parser** (`helpers.extract_tools.
extract_tool_request`) rather than a JSON check written for the test, so the ground truth
comes from the same code production uses.

**Zero structural breaks at any tested size.** Every trial that completed emitted valid,
parseable JSON. Largest single valid tool call: **85,151 characters of content**.

```
target   verdict        content   finish
 4000    OK               9,553    stop
12000    OK              30,385    stop
32000    OK              85,151    stop
32000    OK              37,924    stop
(8 of 12 trials excluded as HARNESS-CAP — see the honest limit below)
```

**Your framing was:** *"If deepseek-flash holds at 16K, a meaningful share of those 300
were against a constraint the model never had."* It holds at **85K**, not 16K.

### The honest limit

This establishes **NO BREAK FOUND**, not where the break is. 8 of 12 trials hit my own
`max_tokens` cap, because of a second finding: **the model overshoots length targets by
2.4–2.7×**. Asked for 4,000 chars it wrote 9,553. Asked for 32,000 it wrote 85,151. My
cap formula assumed it would land near the target.

The guard held — every capped trial reported `HARNESS-CAP` rather than being scored as a
model failure. A cap masquerading as a breakage is exactly how a sweep produces
confident, wrong numbers. Cap now budgets for measured overshoot; a re-run would find
the actual ceiling if you want it, but the decision in front of us doesn't need it.

**Ornith is deferred** — its llama.cpp server is serving Hermes.

## 2. What this retires, specifically

Vek has **no profile**, so he falls through to `DEFAULTS` in `helpers/write_threshold.py`:

```
base_limit       = 5000
effective_limit  = base_limit / complexity_score      (score >= 1.0)
```

Note the direction: complexity scoring can only ratchet the limit **down**, never up. So
Vek's ceiling is *at most* 5,000 chars while he demonstrably emits 85,151 in a single
valid call. **17× under-constrained**, and the gate is the thing generating the failure
lessons that then get surfaced back at him.

The overshoot compounds it. A request for a 4,000-char document produces ~10,000 chars of
output. So a limit set against the *requested* size is being applied to something 2.5×
larger — which is the mechanical explanation for your Q3 observation that the gate fires
on 94% of normal output. It isn't firing on unusual output. It's firing on ordinary
output measured against the wrong number.

My recommendation for Vek: **raise `base_limit` substantially or retire the size gate for
this model entirely.** I'd rather you set the number than have me pick one — but on the
evidence, 5,000 is not defensible for a model that clears 85,000.

## 3. Jake's framing — and it is already in the schema

Jake's proposal, in his words: a way to see what model is being served and intervene based
on what that model needs. *"<10B, probably a lot. 27B–35B, some surgical help. Frontier,
none."*

**That field already exists.** `evaluation_summary.recommended_prosthetic_level` is
declared in **12 of 13 profiles**, with a real four-value vocabulary — and **nothing in
the codebase reads it**:

```
default.json                          medium   full
qwen3-14b-q4_k_m.json                 unknown  full
unsloth_qwen3-14b-q4_k_m.json         unknown  full
deepseek-r1.json                      medium   moderate
qwen3.5-9b.json                       unknown  moderate
qwen3.5-35b-a3b.json                  medium   moderate
qwen3.5-27b-...-distilled.json        high     moderate
unsloth_gpt-oss-20b.json              high     targeted
jackrong_qwen3.6-27b.json             high     light
ornith-1.0-35b.json                   high     light
unsloth_qwen3-14b.json                high     light
qwen_qwen3-4b-2507.json               high     light     <- see anomaly below
```

`grep -rn "recommended_prosthetic_level" --include=*.py` returns **nothing**. Producer
built, consumer never wired — the same defect class as the acceptor, the skill-capture
loop, and `_49`'s reasoning state. Someone designed exactly the mechanism Jake is asking
for and it has never been connected to a decision.

And the consequence lands on Vek precisely: **no profile → `default.json` → declared
`full` prosthetic level** — the heaviest tier — for a frontier model that outperforms
every local model in the fleet. Even if something read the field, Vek would get the
wrong answer, because the fallback is the maximum.

**Anomaly worth a look:** `qwen_qwen3-4b-2507.json` declares capability `high` and
prosthetic `light`. For a 4B model that inverts Jake's tiering. Either the profile is
mis-authored or "capability" means something narrower there than it reads. Worth checking
before the field becomes load-bearing, because wiring a consumer to a wrong value is
worse than wiring it to nothing.

## 4. What's yours to decide

I can build the tiering, but four calls are design, not implementation:

1. **Is `recommended_prosthetic_level` the right control surface**, or should tiering be
   per-layer rather than one global dial? A model may need no write gate but still
   benefit from BST enrichment. One dial is simpler; per-layer is more honest.
2. **What does each tier actually switch off?** `full` / `moderate` / `light` /
   `targeted` currently have no defined semantics anywhere — the vocabulary exists
   without a contract. That contract is a spec decision.
3. **Where is the tier resolved?** `helpers/model_profile.py` now resolves profiles
   correctly on v2.9 (it did not before — your Qwen3.6 supervisor overrides had never
   once applied), so it's the natural home. But every consumer currently reads the
   profile independently.
4. **What is the fallback when no profile exists?** Today it's `default.json` = `full`.
   Safe for a 4B, wrong for Vek. Fail-heavy is the conservative default but it is
   actively costing us on the strongest model we run.

My own view, offered as input rather than a decision: the extension survey and this are
the same question from two directions. The survey asks "has this been outgrown?" — and
"outgrown by *which model*" is the missing dimension. An extension isn't outgrown in
general; it's outgrown by Vek and still load-bearing for a 9B. If tiering lands first,
the survey's third pass has somewhere to put its answers.

## 5. On the record

The sweep instrument was built with the guard that saved it, but I want the failure noted
anyway: my first cap formula was wrong and cost 8 of 12 trials. It didn't corrupt the
finding only because I'd built the HARNESS-CAP discriminator before running. That was
deliberate — the ground-truth work from Pool B — and it is the second time this week that
a guard built before the run is what kept a result honest.

— Kestrel

*Raw: `eval/json_coherence_sweep_deepseek-v4-flash_20260821.json`. Tool:
`eval/json_coherence_sweep.py` (`becb207`).*
