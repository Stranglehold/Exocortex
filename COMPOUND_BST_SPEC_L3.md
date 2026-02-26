# Compound BST Classification — L3 Specification

**Version:** 1.0  
**Date:** 2026-02-26  
**Status:** Ready to build  
**Motivated by:** ST-003 misclassification (Oracle investigation → codegen across all turns)  
**Design note:** `COMPOUND_BST_DESIGN_NOTE.md`  
**Subsumes:** Priority 4 (Profile-Aware BST Enrichment)  
**Modified file:** `_11_belief_state_tracker.py` (single file modification, no new extensions)

---

## Summary

Replace the BST's first-match-wins single-domain classifier with a scored compound classifier that emits a primary domain plus an optional secondary domain. Maintain full backward compatibility. Integrate profile-aware enrichment gating. Track momentum on compound signatures rather than single domains.

The classifier's job is accuracy. Momentum's job is stability. Don't mix them.

---

## Data Structures

### CompoundClassification

Written to `extras_persistent["_bst_compound"]` every turn.

```python
@dataclass
class CompoundClassification:
    primary_domain: str             # Always present. Highest-scoring domain.
    primary_confidence: int         # Signal match count (not 0-1 float)
    primary_signals: list[str]      # Which patterns matched
    
    secondary_domain: str | None    # Second domain, if above threshold. None otherwise.
    secondary_confidence: int | None
    secondary_signals: list[str] | None
    
    compound_signature: str         # "investigation+coding" or "investigation" (no secondary)
    momentum_turns: int             # Consecutive turns this signature has held
    
    enrichment_plan: dict           # See EnrichmentPlan below

    def to_dict(self) -> dict:
        return {
            "primary": {
                "domain": self.primary_domain,
                "confidence": self.primary_confidence,
                "matched_signals": self.primary_signals,
            },
            "secondary": {
                "domain": self.secondary_domain,
                "confidence": self.secondary_confidence,
                "matched_signals": self.secondary_signals,
            } if self.secondary_domain else None,
            "compound_signature": self.compound_signature,
            "momentum_turns": self.momentum_turns,
            "enrichment_plan": self.enrichment_plan,
        }
```

### EnrichmentPlan

```python
{
    "primary_enrichment": true,                    # False only if primary in disabled_domains
    "secondary_enrichment": true,                  # False if no secondary, secondary disabled, or secondary below threshold
    "reason_primary_skipped": null,                # "disabled_in_profile" or null
    "reason_secondary_skipped": null,              # "disabled_in_profile" | "no_secondary_classified" | "below_threshold" | null
}
```

### Backward Compatibility Keys

Two keys written to `extras_persistent` every turn:

| Key | Type | Description | Consumers |
|-----|------|-------------|-----------|
| `_bst_domain` | `str` | Primary domain only. **Unchanged from current BST.** | Fallback, org kernel, supervisor, error comprehension (via domain context) |
| `_bst_compound` | `dict` | Full CompoundClassification. New key. | Any compound-aware consumer. Epistemic integrity (future), model router (future). |

**Rule:** Every consumer that currently reads `_bst_domain` continues to work without modification. Compound awareness is opt-in.

---

## Classification Algorithm

### Step 1: Score All Domains

Replace first-match-wins with score-all-domains.

```python
SECONDARY_MIN_SIGNALS = 1  # Secondary must match at least 1 signal

def score_all_domains(message: str, domain_configs: dict) -> list[tuple[str, int, list[str]]]:
    """
    Score every domain against the message.
    Score = count of matched signal patterns. Simple, deterministic, debuggable.
    
    Returns list of (domain_name, score, matched_patterns), sorted by:
      1. Score descending
      2. Domain priority ascending (tiebreaker)
    
    Only domains with score > 0 are included.
    """
    scores = []
    for domain_name, config in domain_configs.items():
        matched = []
        for pattern in config["signals"]:
            if re.search(pattern, message, re.IGNORECASE):
                matched.append(pattern)
        if matched:
            scores.append((domain_name, len(matched), matched))
    
    # Sort: highest score first, then by domain priority for ties
    scores.sort(key=lambda x: (-x[1], DOMAIN_PRIORITY.get(x[0], 99)))
    return scores
```

### Step 2: Extract Primary and Secondary

```python
def extract_compound(scores: list[tuple[str, int, list[str]]]) -> tuple[dict, dict | None]:
    """
    Primary = highest scoring domain. Always present.
    Secondary = second highest, IF it meets minimum signal threshold.
    
    No minimum lead required. Near-ties ARE the signal that the task is compound.
    Momentum handles stability. Don't mix accuracy and stability in the classifier.
    """
    if not scores:
        primary = {"domain": "conversation", "confidence": 0, "matched_signals": []}
        return primary, None
    
    primary = {
        "domain": scores[0][0],
        "confidence": scores[0][1],
        "matched_signals": scores[0][2],
    }
    
    secondary = None
    if len(scores) > 1 and scores[1][1] >= SECONDARY_MIN_SIGNALS:
        secondary = {
            "domain": scores[1][0],
            "confidence": scores[1][1],
            "matched_signals": scores[1][2],
        }
    
    return primary, secondary
```

### Step 3: Apply Compound Momentum

```python
MOMENTUM_THRESHOLD = 3  # Turns before momentum resists reclassification

def apply_compound_momentum(
    new_primary: dict,
    new_secondary: dict | None,
    current_signature: str,
    current_momentum: int,
) -> tuple[dict, dict | None, str, int]:
    """
    Momentum tracks compound signatures, not single domains.
    
    Rules:
    1. Same signature → increment momentum
    2. Weak momentum (< threshold) → accept new classification
    3. Strong momentum (>= threshold) → only break if new primary is NOT
       in the current compound signature's domains
    
    Key insight: "investigation+coding" with strong momentum won't flip
    on an `ls` command (file_ops). But if the user says "now let's plan 
    the sprint", planning IS NOT in the current compound, so momentum breaks.
    """
    new_signature = format_signature(new_primary, new_secondary)
    
    if new_signature == current_signature:
        # Same compound signature. Strengthen momentum.
        return new_primary, new_secondary, new_signature, current_momentum + 1
    
    if current_momentum >= MOMENTUM_THRESHOLD:
        # Strong momentum. Check if new primary is within current compound.
        current_domains = parse_signature(current_signature)
        if new_primary["domain"] in current_domains:
            # New primary is part of the current compound.
            # Maintain current classification. Increment momentum.
            restored_primary, restored_secondary = restore_from_signature(
                current_signature, new_primary, new_secondary
            )
            return restored_primary, restored_secondary, current_signature, current_momentum + 1
        else:
            # Genuinely new domain. Break momentum.
            return new_primary, new_secondary, new_signature, 1
    else:
        # Weak momentum. Accept new classification.
        return new_primary, new_secondary, new_signature, 1


def format_signature(primary: dict, secondary: dict | None) -> str:
    """Format compound signature string for momentum tracking."""
    if secondary:
        # Alphabetical order so investigation+coding == coding+investigation
        domains = sorted([primary["domain"], secondary["domain"]])
        return f"{domains[0]}+{domains[1]}"
    return primary["domain"]


def parse_signature(signature: str) -> set[str]:
    """Extract domain set from signature string."""
    return set(signature.split("+"))


def restore_from_signature(
    signature: str, 
    new_primary: dict, 
    new_secondary: dict | None
) -> tuple[dict, dict | None]:
    """
    When momentum holds, restore classification from the current signature
    but update confidence values from the new scoring.
    
    This keeps the domain assignment stable while allowing
    confidence numbers to reflect the current turn's signals.
    """
    domains = parse_signature(signature)
    
    if len(domains) == 1:
        domain = domains.pop()
        return {"domain": domain, "confidence": new_primary["confidence"], 
                "matched_signals": new_primary["matched_signals"]}, None
    
    # Two-domain compound. Assign primary/secondary based on new scores.
    domain_list = sorted(domains)
    # Use new scoring to determine which is primary vs secondary
    if new_primary["domain"] in domains:
        restored_primary = new_primary
        other_domain = (domains - {new_primary["domain"]}).pop()
        restored_secondary = {
            "domain": other_domain,
            "confidence": new_secondary["confidence"] if new_secondary and new_secondary["domain"] == other_domain else 0,
            "matched_signals": new_secondary["matched_signals"] if new_secondary and new_secondary["domain"] == other_domain else [],
        }
    else:
        # New primary isn't in compound (shouldn't reach here given the check above)
        restored_primary = {"domain": domain_list[0], "confidence": 0, "matched_signals": []}
        restored_secondary = {"domain": domain_list[1], "confidence": 0, "matched_signals": []}
    
    return restored_primary, restored_secondary
```

### Step 4: Build Enrichment Plan

```python
def build_enrichment_plan(
    primary: dict,
    secondary: dict | None,
    model_profile: dict | None,
) -> dict:
    """
    Determine what enrichment to inject based on classification + model profile.
    
    Rules:
    - Primary enrichment: ON unless primary domain in model's disabled_domains
    - Secondary enrichment: ON unless secondary is None, below threshold, or disabled
    - When primary is disabled: no enrichment at all (correct behavior per eval data)
    - When secondary is disabled: primary enrichment only, log the skip
    """
    disabled = set()
    if model_profile:
        disabled = set(model_profile.get("disabled_domains", []))
    
    plan = {
        "primary_enrichment": primary["domain"] not in disabled,
        "secondary_enrichment": False,
        "reason_primary_skipped": None,
        "reason_secondary_skipped": None,
    }
    
    if primary["domain"] in disabled:
        plan["reason_primary_skipped"] = "disabled_in_profile"
    
    if secondary is None:
        plan["reason_secondary_skipped"] = "no_secondary_classified"
    elif secondary["domain"] in disabled:
        plan["reason_secondary_skipped"] = "disabled_in_profile"
    else:
        plan["secondary_enrichment"] = True
    
    return plan
```

### Step 5: Generate Enrichment Injection

```python
def generate_enrichment(classification: CompoundClassification, domain_configs: dict) -> str:
    """
    Generate the enrichment text to inject into model context.
    
    Option B from design note:
    - Primary: Full enrichment template (existing behavior)
    - Secondary: Single abbreviated line (~20 tokens)
    
    Uses brief_description field from domain config for secondary enrichment.
    """
    plan = classification.enrichment_plan
    parts = []
    
    # Primary enrichment (full template, same as current BST)
    if plan["primary_enrichment"]:
        template = domain_configs[classification.primary_domain].get("enrichment_template", "")
        if template:
            parts.append(f"[BST] Domain: {classification.primary_domain}")
            parts.append(template)
    
    # Secondary enrichment (abbreviated — one line only)
    if plan["secondary_enrichment"] and classification.secondary_domain:
        brief = domain_configs[classification.secondary_domain].get(
            "brief_description",
            f"{classification.secondary_domain} context is also relevant."
        )
        parts.append(
            f"[BST] Secondary context: {classification.secondary_domain} — {brief}"
        )
    
    # Log skipped enrichments
    if plan["reason_primary_skipped"]:
        parts.append(
            f"[BST] Primary domain '{classification.primary_domain}' enrichment skipped: "
            f"{plan['reason_primary_skipped']}"
        )
    if plan["reason_secondary_skipped"] == "disabled_in_profile":
        parts.append(
            f"[BST] Secondary domain '{classification.secondary_domain}' enrichment skipped: "
            f"{plan['reason_secondary_skipped']}"
        )
    
    return "\n".join(parts)
```

---

## Domain Configuration Changes

### Add brief_description to Each Domain

Each domain config in the BST gets a new `brief_description` field used for abbreviated secondary enrichment. Examples:

```python
DOMAIN_CONFIGS = {
    "investigation": {
        "signals": [...],  # existing
        "enrichment_template": "...",  # existing
        "brief_description": "Entity research methodology — verify sources, cross-reference data, flag gaps.",
    },
    "coding": {
        "signals": [...],
        "enrichment_template": "...",
        "brief_description": "Tool syntax precision and parameter accuracy matter for this task.",
    },
    "bugfix": {
        "signals": [...],
        "enrichment_template": "...",
        "brief_description": "Isolate the failure point before attempting fixes. Check logs first.",
    },
    "analysis": {
        "signals": [...],
        "enrichment_template": "...",
        "brief_description": "Quantitative rigor required — cite specific metrics, not impressions.",
    },
    "system_admin": {
        "signals": [...],
        "enrichment_template": "...",
        "brief_description": "System configuration context — check paths, permissions, and service status.",
    },
    "planning": {
        "signals": [...],
        "enrichment_template": "...",
        "brief_description": "Sequence dependencies and resource constraints before committing to a plan.",
    },
    "conversation": {
        "signals": [...],
        "enrichment_template": "...",
        "brief_description": "General conversational context.",
    },
    # Add brief_description to all other domains following same pattern
}
```

### Domain Priority Order

For tiebreaking when two domains have identical signal counts:

```python
DOMAIN_PRIORITY = {
    "investigation": 1,
    "analysis": 2,
    "bugfix": 3,
    "coding": 4,
    "planning": 5,
    "system_admin": 6,
    "config_edit": 7,
    "prompt_engineering": 8,
    "git_ops": 9,
    "file_ops": 10,
    "conversation": 99,
}
```

Priority favors more specific, higher-stakes domains. `investigation` beats `coding` on ties because investigation misclassification has worse downstream effects (wrong enrichment for research tasks). `conversation` is always last — it's the default when nothing else matches.

---

## Integration with Existing Stack

### Shared State Writes (every turn)

```python
# Backward compatible — same as current BST
extras_persistent["_bst_domain"] = classification.primary_domain

# New — compound-aware consumers opt in
extras_persistent["_bst_compound"] = classification.to_dict()
```

### Model Profile Loading

The BST extension needs access to the current model profile to build the enrichment plan. The profile is already available in Agent Zero's context — the eval framework writes profiles to a known location.

```python
def load_model_profile(agent) -> dict | None:
    """
    Load the current model's eval profile for enrichment gating.
    Returns None if no profile found (all enrichment enabled by default).
    """
    model_name = agent.config.get("chat_model", "")
    profile_path = Path(f"/a0/usr/profiles/{model_name}.json")
    
    if profile_path.exists():
        with open(profile_path) as f:
            return json.load(f)
    
    return None
```

### Consumers — No Changes Required

| Consumer | Reads | Change? |
|----------|-------|---------|
| Fallback logger | `_bst_domain` | None |
| Fallback advisor | `_bst_domain` | None |
| Organization kernel | `_bst_domain` | None |
| Supervisor loop | `_bst_domain` | None |
| Error comprehension | Does not read BST | None |
| Epistemic integrity (future) | `_bst_compound` | New consumer, reads compound |
| Model router (future) | `_bst_compound` | New consumer, reads compound |

---

## Logging

Every classification logged at INFO level:

```
[BST] investigation (3 signals) + coding (1 signal) | sig=coding+investigation | momentum=4 | enrichment: primary=ON secondary=ON
```

When momentum holds against reclassification:

```
[BST] Momentum held: coding+investigation (5 turns) resisted file_ops (1 signal)
```

When momentum breaks:

```
[BST] Momentum break: coding+investigation (5 turns) → planning (2 signals, not in compound)
```

When enrichment is skipped:

```
[BST] Secondary enrichment skipped for bugfix: disabled_in_profile (Qwen3-14B)
```

---

## Testing Criteria

### Functional Tests

| # | Input | Expected Primary | Expected Secondary | Signature |
|---|-------|------------------|--------------------|-----------|
| 1 | "debug the OpenPlanter API query timeout" | bugfix | investigation or coding | compound |
| 2 | "investigate Oracle Corporation credit risk" | investigation | None | investigation |
| 3 | "fix the pip install error" | bugfix | system_admin | bugfix+system_admin |
| 4 | "ls -la /home/user/" | file_ops | None | file_ops |
| 5 | "what's the best approach for this?" | conversation or planning | None | single |
| 6 | "analyze the stress test logs and fix the domain flip" | analysis | bugfix | analysis+bugfix |

### Backward Compatibility Tests

| # | Test | Expected |
|---|------|----------|
| 7 | Read `_bst_domain` after compound classification | Primary domain string, same as before |
| 8 | Consumer that doesn't read `_bst_compound` | Works unchanged |
| 9 | No model profile found | All enrichment enabled (default permissive) |

### Momentum Tests

| # | Sequence | Expected |
|---|----------|----------|
| 10 | 3× "investigation+coding" then `ls` output | Momentum holds, sig stays investigation+coding |
| 11 | 3× "investigation+coding" then "plan the sprint" | Momentum breaks, new sig = planning |
| 12 | 2× "investigation+coding" then `ls` output | Weak momentum, accepts reclassification to file_ops |

### Profile-Aware Tests

| # | Primary | Secondary | Profile | Expected Enrichment |
|---|---------|-----------|---------|---------------------|
| 13 | investigation (enabled) | bugfix (disabled) | Qwen3-14B | Primary ON, secondary OFF, reason logged |
| 14 | bugfix (disabled) | coding (enabled) | Qwen3-14B | Primary OFF (no enrichment at all) |
| 15 | investigation (enabled) | coding (enabled) | no profile | Both ON |

---

## Build Sequence for Claude Code

1. **Add `brief_description` to every domain config.** No behavior change. Pure data addition.

2. **Add `DOMAIN_PRIORITY` dict.** Used for tiebreaking. No behavior change yet.

3. **Replace classification function.** Swap first-match with `score_all_domains` → `extract_compound`. Write both `_bst_domain` and `_bst_compound` to shared state. At this point the system classifies compound but momentum and enrichment are unchanged.

4. **Replace momentum tracking.** Swap single-domain momentum with compound signature momentum. Use `format_signature`, `parse_signature`, `apply_compound_momentum`.

5. **Add model profile loading.** `load_model_profile` function reads from profile path.

6. **Add enrichment plan generation.** `build_enrichment_plan` reads primary, secondary, and model profile.

7. **Modify enrichment injection.** Replace single-domain enrichment with `generate_enrichment` that handles primary (full) + secondary (abbreviated).

8. **Add logging.** Compound classification log line, momentum hold/break logs, enrichment skip logs.

9. **Run functional tests** against the 15 test cases above.

10. **Deploy.** Copy to container. Run ST-004 or replay ST-003 task with compound BST active. Compare classification accuracy.

---

## What This Does NOT Do

- Does not use LLM calls. Classification remains fully deterministic.
- Does not emit more than two domains. Primary + optional secondary. Not a ranked list.
- Does not create compound enrichment templates. Secondary is one abbreviated line.
- Does not change the organization kernel's role activation (reads `_bst_domain` only).
- Does not change error comprehension behavior (reads command output, not domain).
- Does not persist compound history across sessions. Per-session momentum only.
- Does not handle domain evolution within a single turn. Mid-turn shifts handled by next turn.
- Does not weight signals. Score = count. Simplicity over optimization. Weights are a future tuning knob if count-based scoring proves insufficient.

---

## Validation Against ST-003

The spec is validated when:

1. The Oracle credit risk investigation is classified as `investigation` (primary) across the majority of turns, not `codegen` or `prompt_engineering`.
2. Turns involving both research and API calls are classified as compound (`investigation+coding`).
3. Momentum prevents operational commands (`ls`, `cat`, `pip`) from breaking the investigation classification.
4. Enrichment injects investigation methodology, not code completion guidance.

If these four conditions hold on replayed ST-003 logs, the build is validated.

---

*The classifier's job is accuracy. Momentum's job is stability. Enrichment's job is guidance. Profile-awareness's job is safety. Each component does one thing. The composition does the right thing.*
