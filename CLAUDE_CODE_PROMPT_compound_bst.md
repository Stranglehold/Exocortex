# Claude Code Prompt: Compound BST Classification

Read `COMPOUND_BST_SPEC_L3.md` in the repo root first. That is the complete specification. This prompt translates the spec into implementation instructions.

**Scope:** 1 file modified. 0 new files. No new hook points.

---

## Pattern Source

Read `python/helpers/extension_execution/extensions/monologue_end/_11_belief_state_tracker.py` first. That is the file you are modifying. Understand its:
- Class pattern (inherits from Extension)
- How it reads messages from `self.agent`
- How it writes to `extras_persistent`
- How it accesses agent config
- Current signal matching logic (first-match-wins regex)
- Current momentum tracking
- Current enrichment injection

Read at least one other extension in the same directory to confirm the pattern.

---

## Context Files to Read

1. **The spec:** `COMPOUND_BST_SPEC_L3.md` — complete algorithm, data structures, testing criteria
2. **The design note:** `COMPOUND_BST_DESIGN_NOTE.md` — motivation, design principles, open questions resolved
3. **The BST extension:** `_11_belief_state_tracker.py` — the file you are modifying
4. **A model profile (if it exists):** Look in `/a0/usr/profiles/` for any `.json` profile file. The enrichment plan reads `disabled_domains` from this.
5. **Error comprehension (for pattern reference):** `python/helpers/extension_execution/extensions/tool_execute_after/_20_error_comprehension.py` — example of how another extension writes structured data to `extras_persistent`

---

## Modification: `_11_belief_state_tracker.py`

### What Changes

Replace the classification, momentum, and enrichment logic. Keep the extension class structure, hook signature, message reading, and everything else unchanged.

### Build Steps (in order — validate each before proceeding)

**Step 1: Add data**
- Add `brief_description` string to every domain in the domain config dict. See spec for examples.
- Add `DOMAIN_PRIORITY` dict for tiebreaking. See spec for the ordering.
- No behavior change. Validate: extension loads, existing classification works.

**Step 2: Add scoring function**
```python
def score_all_domains(message: str, domain_configs: dict) -> list[tuple[str, int, list[str]]]:
    """
    Score every domain against message. Score = count of matched signal patterns.
    Returns sorted list: highest score first, domain priority for ties.
    Only domains with score > 0 included.
    """
    scores = []
    for domain_name, config in domain_configs.items():
        matched = []
        for pattern in config["signals"]:
            if re.search(pattern, message, re.IGNORECASE):
                matched.append(pattern)
        if matched:
            scores.append((domain_name, len(matched), matched))
    
    scores.sort(key=lambda x: (-x[1], DOMAIN_PRIORITY.get(x[0], 99)))
    return scores
```
No behavior change yet — function exists but isn't called.

**Step 3: Add compound extraction**
```python
SECONDARY_MIN_SIGNALS = 1

def extract_compound(scores):
    if not scores:
        return {"domain": "conversation", "confidence": 0, "matched_signals": []}, None
    
    primary = {"domain": scores[0][0], "confidence": scores[0][1], "matched_signals": scores[0][2]}
    
    secondary = None
    if len(scores) > 1 and scores[1][1] >= SECONDARY_MIN_SIGNALS:
        secondary = {"domain": scores[1][0], "confidence": scores[1][1], "matched_signals": scores[1][2]}
    
    return primary, secondary
```

**Step 4: Wire scoring into classification**
Replace the existing first-match classification call with:
```python
scores = score_all_domains(message_text, DOMAIN_CONFIGS)
primary, secondary = extract_compound(scores)
```
Write BOTH keys to shared state:
```python
extras_persistent["_bst_domain"] = primary["domain"]  # Backward compatible
extras_persistent["_bst_compound"] = compound_classification.to_dict()  # New
```
Validate: `_bst_domain` still contains a single domain string. Existing consumers unaffected.

**Step 5: Replace momentum**
Replace single-domain momentum with compound signature momentum. See spec for full `apply_compound_momentum`, `format_signature`, `parse_signature`, `restore_from_signature` functions.

Key: `format_signature` sorts domains alphabetically so `investigation+coding == coding+investigation`.

`MOMENTUM_THRESHOLD = 3` — same as current BST if it has one, otherwise use 3.

Validate: repeated same-domain messages build momentum. New domain breaks it.

**Step 6: Add enrichment plan**
```python
def load_model_profile(agent) -> dict | None:
    model_name = agent.config.get("chat_model", "")
    profile_path = Path(f"/a0/usr/profiles/{model_name}.json")
    if profile_path.exists():
        with open(profile_path) as f:
            return json.load(f)
    return None
```
Build enrichment plan from primary, secondary, and profile. See spec for `build_enrichment_plan`.

When no profile exists, all enrichment is enabled (default permissive).

**Step 7: Modify enrichment injection**
Primary domain: full enrichment template (same as current behavior).
Secondary domain: single abbreviated line using `brief_description`:
```
[BST] Secondary context: {domain} — {brief_description}
```

When enrichment is skipped due to profile, log it:
```
[BST] Secondary enrichment skipped for {domain}: disabled_in_profile
```

**Step 8: Add logging**
Every classification:
```
[BST] {primary} ({n} signals) + {secondary} ({n} signals) | sig={signature} | momentum={n} | enrichment: primary={ON/OFF} secondary={ON/OFF}
```
Momentum hold:
```
[BST] Momentum held: {signature} ({n} turns) resisted {new_domain} ({n} signals)
```
Momentum break:
```
[BST] Momentum break: {signature} ({n} turns) → {new_domain} ({n} signals, not in compound)
```

---

## Critical Implementation Notes

1. **Message format.** Agent-Zero messages are dicts: `{'ai': False, 'content': {'user_message': 'text'}}`. Extract the text content before scoring. Check the existing BST code for exactly how it reads the message.

2. **Extension class pattern.** Follow the existing class structure exactly. Do not change the class name, hook method signature, or initialization pattern.

3. **Logging.** Use the instance logging method, not `print()` or module-level `logging`. Look at how the existing BST and error comprehension extensions log.

4. **`extras_persistent` is a dict on `self.agent`.** Write to it the same way the existing BST writes `_bst_domain`. The new `_bst_compound` key is a dict — make sure to call `.to_dict()` or equivalent before writing.

5. **No LLM calls.** The entire classification pipeline is regex + counting + dictionary lookups. Zero model inference. This is deterministic only.

6. **Import requirements.** `re` (already used), `json`, `pathlib.Path`. No new dependencies.

7. **Graceful degradation.** If model profile doesn't exist → all enrichment enabled. If domain configs are missing `brief_description` → use a default string. If `_bst_compound` read fails downstream → consumers fall back to `_bst_domain`.

8. **Don't break existing signal patterns.** The word-boundary regex patterns in the current BST's domain configs are already correct (Fix A from Feb 22). Don't modify the regex patterns themselves — only add the scoring wrapper around them.

9. **Cache clearing after deployment:**
```bash
find /a0/python -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
```

10. **Syntax validation before deploying:**
```bash
python3 -m py_compile _11_belief_state_tracker.py
```

---

## Execution Flow Reference

```
Before (current):
  message → first-match regex → single domain → momentum check → enrichment template → inject

After (compound):
  message → score ALL domains → extract primary + secondary → compound momentum →
  load model profile → build enrichment plan → primary template + secondary brief → inject
```

Both flows write `_bst_domain`. New flow additionally writes `_bst_compound`.

---

## Testing

After building, validate:

1. **Compile check:** `python3 -m py_compile _11_belief_state_tracker.py` — must pass
2. **Load check:** Restart Agent-Zero container, verify BST loads in docker logs: `docker logs agent-zero 2>&1 | grep -i "belief\|BST"`
3. **Functional check:** Send message "investigate Oracle Corporation credit risk" — primary should be `investigation`, check logs for `[BST]` line
4. **Compound check:** Send message "debug the OpenPlanter API query timeout" — should show primary + secondary in logs
5. **Backward compat:** Verify `_bst_domain` is still a plain string in shared state
6. **Momentum check:** Send 4 investigation messages, then send `ls` — momentum should hold
7. **Profile check:** If a profile exists with `disabled_domains`, verify enrichment skip is logged

---

## Do NOT

- Do not create new files. This is a modification to one existing file.
- Do not change the extension's hook registration or execution order.
- Do not modify the existing signal regex patterns.
- Do not add LLM calls.
- Do not emit more than 2 domains (primary + optional secondary).
- Do not change how `_bst_domain` works — it must remain a plain string for backward compatibility.
- Do not build compound enrichment templates. Secondary gets one abbreviated line only.
