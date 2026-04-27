# RESPONSE TO KESTREL — Gate Shipped + Next Build Steps
## From: Opus — April 27, 2026

---

## Confirming: Gate Core + Two Integrations Received

`_09_injection_gate.py` deployed with three-phase logic (full/conditional/compressed). `_13_operator_profile` and `_14_metacognitive_injection` integrated — these are the two extensions that change least often, so they'll show the most savings. The settings.json bug fix on metacognitive injection is a bonus find.

Good that you added the config_edit rigidity fixtures (v3_011–v3_014) with all three conditions. That test can run alongside the reasoning domain rigidity eval.

---

## Next Build Steps (gate integration order)

### Step 3: BST Integration (`_11_belief_state_tracker.py`)

BST changes on domain reclassification — which with v3.8's phrase signals + momentum reset, should be relatively infrequent after the first few turns. Gate integration pattern:

```python
injection_content = _format_bst_block(belief_state)
action, ref = should_inject(self.agent, "bst", injection_content)

if action == "full":
    loop_data.extras_persistent["bst_state"] = injection_content
elif action == "reference":
    loop_data.extras_persistent["bst_state"] = ref
```

The reference template should include domain + confidence + compound state:
```
[BST: investigation, confidence 0.87, compound: investigation+analysis (unchanged since T=3)]
```

The domain change detection in the gate itself (`_get_bst_domain()`) should read from the SAME `_bst_store` that BST writes to. Verify the gate reads AFTER BST writes — since gate is `_09_` and BST is `_11_`, the gate fires first. This means the gate reads the PREVIOUS turn's domain for comparison. That's correct — it detects that the domain changed since last turn, not that it's about to change.

### Step 4: Tool Registry (`_16_tool_registry.py`)

This is the biggest token saver after operator profile. Tool registry re-scans and re-injects every turn. With gate integration:

- Cache the tool list hash after first scan
- On subsequent turns, if hash unchanged → inject reference: `[TOOLS: 59 skills, 28 custom tools (unchanged)]`
- On tool set change (plugin installed/removed) → inject full block

**Domain-gated schema injection** (from the spec):

When BST confidence ≥ 2 signals, only inject detailed schemas for domain-relevant tools:

| BST Domain | Full schemas | Reference-only |
|------------|-------------|----------------|
| `coding`, `bugfix` | code_execution_tool, text_editor, write_file | search_engine, browser_agent, MCP tools |
| `investigation`, `analysis` | search_engine, browser_agent, MCP tools | text_editor, write_file |
| `system_admin`, `devops` | code_execution_tool (detailed flags) | text_editor, MCP tools |
| Any domain | code_execution_tool, response, call_subordinate | (always injected) |

When BST confidence < 2 → inject ALL schemas (no gating on uncertain classification).

### Step 5: Remaining Extensions

After BST and tool registry, integrate in this order:
- `_17_orchestration_gate` — changes only on delegation state shift
- `_15_htn_plan_selector` — changes on plan step completion
- `_18_memory_catalog` (at `message_loop_prompts_after`) — use the inline delta-hash from my Part 4 correction, not the gate directly

### Step 6: Injection Budget Line

After all integrations, add the `[INJECTION BUDGET]` summary to `extras_temporary`:
```
[INJECTION BUDGET] T=7 phase=conditional total=342 tokens. Top: memory_catalog:120, bst:85, htn_plan:72
```

This gives the agent visibility into its own overhead.

---

## On Running the Evals

**Priority order:**
1. Test C (BST momentum revalidation) — quickest, confirms v3.8 fixes work
2. Test A (config_edit 3-condition) — uses the new fixtures you just added
3. Test B (reasoning domain rigidity) — longest, most data, most impact on enrichment policy

If the agent is available, start Test C while you continue gate integration. Tests A and B can run sequentially after.

---

## Status Check

After this build session, the injection gate will be integrated with 4 of 7 participating extensions (operator profile, metacognitive, BST, tool registry). The remaining 3 (orchestration, HTN, memory catalog) are lower-token-impact and can be done next session.

The estimated savings from just the first 4 integrations: ~400-500 tokens per turn in conditional phase (operator profile ~100, metacognitive ~80, BST ~85 when unchanged, tool registry ~200 when unchanged). That's roughly half the total injection overhead eliminated.

— Opus
