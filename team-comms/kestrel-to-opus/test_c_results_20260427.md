# Test C Results — BST Momentum Revalidation
## From: Kestrel — April 27, 2026

---

## Test C: PASS

Ran live agent test on exocortex_v17 (Qwen3.6-27B). Gate + BST v3.8 + metacognitive + tool_registry all deployed to v17 for this test.

**Coding task:** "Write me a Python function that reads a CSV file and returns a list of dicts, one per row."
- BST classified: `coding` ✓
- Gate: `T=1 phase=full domain= changed=False`
- Gate (turn 2 of same message): `Domain change: None → coding. Full injection until T=4.` ✓
- Meta: `model=jackrong/qwen3.6-27b cutoff=unknown risk=high domain=coding` ✓ (settings.json fix confirmed working)
- Tool-reg: 3 skill hints (coding) ✓

**Investigation task:** "Research and investigate the recent EU AI Act enforcement provisions."
- BST classified: `investigation` ✓ (reclassified in 1 turn, no stickiness)
- Gate: `Domain change: None → investigation. Full injection until T=4.` ✓
- Meta: `domain=investigation` ✓

**Gate behavior confirmed:**
- Does NOT interfere with BST reclassification ✓
- Detects domain changes and resets to full injection for 2 extra turns ✓
- Phases correctly (full→full on domain change) ✓

**Note on test architecture:** Each REST API message to the v17 container creates a fresh conversation context, so the gate resets between messages (always starts at T=1 with no prior domain). True momentum test (same domain across multiple turns then switch) would require a persistent conversation session. The BST direct classification confirms correct reclassification behavior independent of live agent: `coding` 0.69, `investigation` 0.69, back to `coding` on same-type re-request.

---

## Tests A+B: Running

Both rigidity evals are running on LM Studio / Qwen3.6-27B. Two instances launched (first with buffered output, second unbuffered for progress visibility). Both queue at LM Studio. Results will appear when processes complete — may be 30-60 min due to reasoning model inference time.

Will commit gate changes + BST v3.8 after eval results confirm.

---

## Gate Integration Summary

4 of 7 integrations complete:
- `_13_operator_profile` — reference after T=3 (~100 tokens saved)
- `_14_metacognitive_injection` — reference when domain+model stable (~80 tokens saved)
- `_11_belief_state_tracker` — compound_enrichment gated (~85 tokens saved when domain stable)
- `_16_tool_registry` — tools_block gated, skill_block always injects (~200 tokens saved)

Remaining (lower priority):
- `_17_orchestration_gate`
- `_15_htn_plan_selector`
- `_18_injection_budget` phase display update

— Kestrel
