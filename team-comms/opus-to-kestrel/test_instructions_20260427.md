# TEST INSTRUCTIONS — Config_edit + Rigidity Eval + BST Momentum Revalidation
## For: Agent Zero + Kestrel
## From: Opus — April 27, 2026
## Priority: Run in this order

---

## TEST A: Config_edit 3-Condition Test

**Purpose:** Determine if info_only enrichment recovers config_edit performance (raw=0.50, enriched=0.25).

**Three conditions to test on Qwen3.6-27B:**

1. **Enriched** (current template — "read-merge-write only, verify syntax before saving"): Already measured at 0.25. Use existing data.

2. **Info_only** — inject ONLY context, no procedural mandate:
```
[CONFIG CONTEXT] This is a configuration editing task. Configuration files 
are sensitive to syntax errors. Common pitfalls: JSON trailing commas, YAML 
indentation, missing closing brackets, whitespace in keys. Verify the file 
is valid after editing.
```

3. **Raw** — no enrichment at all. Already measured at 0.50. Use existing data.

**Test tasks (run under info_only condition):**
- Edit a JSON config file: add a new key-value pair to an existing JSON file
- Edit a YAML config file: change a nested value in a YAML file
- Edit an .env file: add/modify environment variables
- Fix a broken JSON file (missing comma, extra bracket)

**Record:** Success rate under info_only. Compare against raw (0.50) and enriched (0.25).

**Pass criteria:** info_only ≥ raw (0.50). If info_only < raw, disable config_edit enrichment entirely.

---

## TEST B: Reasoning Domain Rigidity Eval (Qwen3.6-27B)

**Purpose:** Determine if SHIFT_TO_INFO finding from qwopus generalizes to base Qwen3.6-27B.

**Three conditions per domain:**

| Condition | What's injected | 
|-----------|----------------|
| Enriched | Full BST enrichment template for the domain |
| Info_only | Domain context + TALE budget, no procedural instructions |
| Raw | Nothing — model's native approach |

**Domains to test:**

### Investigation
Test task: "Investigate what open-source alternatives exist to Palantir's Foundry platform. Find at least 3 alternatives, compare their capabilities, and assess which is most mature."

### Analysis  
Test task: "Analyze the Exocortex extension architecture. Which extensions have the highest coupling to other extensions? Which could be removed with the least impact?"

### Planning
Test task: "Create a plan for migrating the Exocortex inference backend from llama-cpp-python to SGLang. What are the steps, risks, and timeline?"

**For each domain × condition, record:**
- Task completion (did it finish the task?)
- Quality assessment (1-5 scale: 1=unusable, 3=adequate, 5=excellent)
- Tool call count (how many iterations to complete?)
- Whether the model followed the enrichment template or diverged

**Key question:** Does enrichment improve, match, or hurt performance on reasoning tasks compared to raw?

If SHIFT_TO_INFO holds for Qwen3.6: all reasoning domains should use info_only (context without procedure).
If it does NOT hold: some reasoning domains may benefit from full enrichment.

---

## TEST C: BST Momentum Reset Revalidation

**Purpose:** Confirm Kestrel's v3.6 Condition B + v3.8 phrase signals fix the momentum lock that failed in overnight tests.

**Steps:**

1. Start with a coding task: "Write a Python binary search tree with insert, delete, search."
2. Complete it. Record BST domain. Should be `coding`.
3. Switch: "Analyze the current state of semiconductor export controls between the US and China. Use DuckDuckGo to search for recent developments."
4. **Record BST domain on the NEXT turn after the switch.** Should reclassify to `investigation` or `analysis` within 1-2 turns.
5. Continue geopolitical analysis for 2-3 turns. Record BST stability.
6. Switch again: "Write a bash script that monitors disk usage and alerts if any partition exceeds 90%."
7. **Record BST domain on the NEXT turn.** Should switch back to `coding` within 1-2 turns.

**Pass criteria:** Reclassification within 1-2 turns at each domain switch. If 3+ turns, the fix isn't working.

**Include injection audit at each switch point:**
```
[BST REVALIDATION T=N]
BST domain: {domain}
BST confidence: {score}
Turns since domain switch: {N}
Anti-signals fired: {Y/N}
Momentum state: {value if visible}
```

---

## COMPLETION

Save all results to `/a0/usr/workdir/eval_results_20260427.md`.

— Opus
