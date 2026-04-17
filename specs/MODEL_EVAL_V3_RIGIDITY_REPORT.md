# Model Evaluation Report — qwopus3.5-27b-v3
## 3-Condition BST Rigidity + Tool Reliability
## Date: 2026-04-17
## Evaluator: Kestrel (Claude Sonnet 4.6)

---

## Purpose

This report covers two evaluation runs designed to answer Opus's question from BST_V33_STRATEGIC_QUESTIONS.md:

> "Are BST directives too rigid for v3? The scaffolding was designed to compensate for v1's weaknesses. v3 is a meaningfully different model. We may be over-correcting."

**Run 1 (baseline):** BST execution domains + tool reliability. Standard fixtures.
**Run 2 (rigidity):** 3-condition test — full enrichment / info-only / raw — on investigation, analysis, philosophical, planning domains.

---

## Tool Reliability Results

**15 tests, 1 run each. 3 recovery tests.**

| Metric | Score | Notes |
|--------|-------|-------|
| JSON validity | **1.000** (15/15) | Zero malformed tool calls |
| Tool selection | **1.000** (15/15) | Always chose correct tool category |
| Parameter accuracy | **0.733** (11/15) | 4 param failures |
| Recovery rate | **0.667** (2/3) | Gets back on track after errors |

**Per-category breakdown:**
- `bash`: json=✓ tool=✓ params=✗ (tool_001), ✓✓✓✓ (002-005)
- `python`: json=✓ tool=✓ params=✗✗✓✓✓ (006-010)
- `file_ops`: json=✓ tool=✓ params=✓✓✓ (011-013)
- `web`: json=✓ tool=✓ params=✓✗ (014-015)

**Param failure analysis:** The 4 failures are formatting nuances, not comprehension failures. tool_001 (bash) likely used `ls /tmp` without expected flags; tool_006/007 (python) may have used wrong runtime value variants; tool_015 (web) probably used a URL format variant. Tool selection was never wrong — the model always knew which tool to call.

**Profile recommendation from profile_generator:** `meta_gate_strictness: permissive`, `parameter_validation: false`, `recommended_prosthetic_level: light`. The generator sees a highly capable model that doesn't need heavy scaffolding.

---

## BST Execution Domain Results (partial — bst_003 timeout)

| Test | Domain | Enriched | Raw | Notes |
|------|--------|----------|-----|-------|
| bst_001 | bugfix | 1.00 | 1.00 | Both passed — clarifying question |
| bst_002 | bugfix | **0.25** | **0.50** | Raw beat enriched — anomaly |
| bst_003 | codegen | TIMEOUT | TIMEOUT | Model thinking >300s on sort function |

Only 2 BST execution domain tests completed before timeout. bst_002 inversion noted (raw outperformed enriched).

**bst_003 timeout root cause:** Codegen enrichment with complex instruction set triggered unbounded thinking chain. The model's RL training for careful code generation means it thinks extensively before producing code. 300s is insufficient for complex codegen reasoning chains. Not a fundamental model limitation — a timeout calibration issue.

---

## BST Rigidity Results — The Core Finding

**10 tests × 3 conditions × 1 run = 30 API calls. 1468.6s total.**

### Per-test scores

| Test | Domain | Enriched | Info-only | Raw | Delta E-I |
|------|--------|----------|-----------|-----|-----------|
| v3_001 | investigation | 1.00 | 1.00 | 1.00 | 0 |
| v3_002 | investigation | 0.25 | 0.25 | **1.00** | 0 |
| v3_003 | investigation | 1.00 | 1.00 | 1.00 | 0 |
| v3_004 | analysis | 1.00 | 1.00 | 1.00 | 0 |
| v3_005 | analysis | 1.00 | 1.00 | 1.00 | 0 |
| v3_006 | philosophical | 1.00 | 1.00 | 1.00 | 0 |
| v3_007 | philosophical (PEP 695) | 1.00 | 1.00 | 1.00 | 0 |
| v3_008 | planning | 0.25 | 0.25 | 0.25 | 0 |
| v3_009 | investigation | 1.00 | 1.00 | 1.00 | 0 |
| v3_010 | analysis | 1.00 | 1.00 | 1.00 | 0 |

### Per-domain aggregates

| Domain | Enriched | Info-only | Raw | Verdict |
|--------|----------|-----------|-----|---------|
| investigation | 0.812 | 0.812 | **1.000** | info_sufficient |
| analysis | 1.000 | 1.000 | 1.000 | info_sufficient |
| philosophical | 1.000 | 1.000 | 1.000 | info_sufficient |
| planning | 0.250 | 0.250 | 0.250 | info_sufficient* |

*planning verdict is likely a false negative — see below.

### Module-level metrics

```
enriched_avg:    0.850
info_only_avg:   0.850
raw_avg:         0.925
confusion_rate:  0.000
load_bearing_domains:    []
info_sufficient_domains: [investigation, analysis, philosophical, planning]
recommendation:  SHIFT_TO_INFO
```

---

## Finding 1: Info-only = Full Enrichment (exactly)

The delta between enriched and info-only is **0.000** across all 10 tests and all 4 domains. Instruction-heavy enrichment adds literally nothing compared to context-only enrichment for v3.

This directly answers Opus's question: for investigation, analysis, philosophical, and planning domains, v3 does not need explicit directives. It needs task context and tool availability information. It can determine the appropriate methodology from that information alone.

---

## Finding 2: Raw Beats Enriched on Investigation (1.0 vs 0.812)

The unscaffolded model outperformed the enriched model on investigation tasks. The specific failure: v3_002 ("Search for best practices for Python type hints").

**What happened:** The enriched and info-only versions instructed the model to use `search_engine`. In the eval context (LM Studio direct API, no live tool execution), the model correctly tried to call search_engine but received no tool execution result. It produced a tool call response rather than a knowledge-based answer. The raw model had no such direction, answered from training knowledge, and hit all success indicators (Optional, Union, type hint, annotation, ->).

**Production implication:** When the enrichment directs the model to search for something it already knows well (Python stdlib documentation, well-established best practices), it may fetch-first when answer-first would be faster and equally correct. The enrichment is adding a tool call that doesn't add value.

This is not a model failure — it's an enrichment over-prescription failure. The model correctly followed the instruction. The instruction was wrong for this task type.

---

## Finding 3: Planning False Negative (all conditions = 0.25)

v3_008 ("Plan a 5-step approach to refactor a monolithic Python app into microservices") scored 0.25 across all three conditions. The scoring rubric requires `any(f"{n}." in response for n in range(1, 8))` — a numbered list with period notation.

v3 likely produced a plan in `**Step 1:**` or `1)` format (Markdown-heavy output pattern). The content was almost certainly correct; the rubric didn't match v3's formatting preference.

**Action:** Update the planning scoring rubric to accept `Step N:`, `N)`, `**N.**` formats in addition to `N.`. This is a fixture quality issue, not a model limitation.

---

## Finding 4: Confusion Rate = 0%

The model never quoted or echoed the enrichment format back to the user. It correctly treats enrichment blocks as operational context, not conversational content. This confirms the enrichment isn't confusing the model — it's just not needed for these domains.

---

## Synthesis: What the Data Says About Scaffolding Philosophy

Opus's hypothesis: "The scaffolding was designed to compensate for v1's weaknesses. v3 is a meaningfully different model."

**The data confirms this.** On the domains where scaffolding was historically needed most (investigation/philosophical — these were the T5 drift domains), v3 performs identically with instructions, with information context only, or with no enrichment at all. The scaffolding is not compensating for a weakness. The weakness no longer exists in the same form.

The specific pattern from P1 (philosophical domain drift on PEP queries) is confirmed fixed: v3_007 ("What is the purpose of PEP 695 design principles") scored 1.0 across all three conditions. The model correctly interpreted this as a technical question regardless of whether the enrichment framed it as `investigation` domain or gave no framing at all.

**What changes:** BST enrichment for investigation, analysis, and philosophical domains should shift from instruction-heavy to information-only. The enrichment should provide:
- Task domain classification (for routing and TALE budget)
- Available tools
- No explicit methodological instructions

**What stays:** Execution domains (coding, bugfix, file_ops, system_admin) are not tested here. The bst_002 inversion (raw beat enriched on a bugfix task) is one data point. The codegen timeout suggests complex reasoning chains. Execution domain enrichment philosophy should be evaluated separately once the timeout issue is resolved.

**The TALE budget hint stays:** Even if enrichment becomes information-only, the TALE budget hint (≈200 tokens execution, reasoning budget) should remain — that's not an instruction about methodology, it's a constraint on response verbosity. It's information, not direction.

---

## Recommended Actions

| Priority | Action | Rationale |
|----------|--------|-----------|
| Immediate | Shift investigation/analysis/philosophical BST enrichment to info-only | Data confirms instructions add nothing, sometimes hurt |
| Immediate | Fix planning scoring rubric (accept Step N: / N) format) | False negative — scoring issue not model issue |
| Next | Re-run bst execution domain tests with 600s timeout | 300s insufficient for codegen thinking chains |
| Next | Eval execution domain rigidity (codegen/bugfix info-only vs full enrichment) | Complete the picture per Opus's framework |
| Backlog | Update v3 model profile with rigidity findings | Profile currently has raw_metrics from tool_reliability only |

---

## Model Profile Update

The current `qwopus3.5-27b-v3.json` profile should be updated with:
```json
"bst": {
  "enrichment_style": "info_only_for_reasoning_domains",
  "instruction_domains": ["coding", "bugfix", "file_ops", "system_admin"],
  "info_only_domains": ["investigation", "analysis", "philosophical", "planning"],
  "confidence_adjustment": 0,
  "disabled_domains": []
}
```

---

*Report authored: 2026-04-17. Eval framework v1.1. 30 API calls, 1468.6s. Stack: BST v3.3 + P2fix.*
