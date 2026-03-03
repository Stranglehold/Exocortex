# Compound BST Classification — Design Note

**Status:** Design note. Pre-spec exploration.
**Motivated by:** Single-domain classification producing incorrect enrichment during compound tasks (ST-002, OpenPlanter debugging sessions).
**Related priorities:** Profile-Aware BST Enrichment (Priority 4), Warning Injection Lane Definition (Priority 5).
**Depends on:** Nothing. Can build standalone against current BST.

---

## The Problem

The Belief State Tracker classifies every user message into a single task domain. The current domain list:

```
investigation, analysis, bugfix, coding, file_ops, research, 
system_admin, conversation, planning
```

Classification drives two downstream systems:
1. **Enrichment** — domain-specific context injected before the model reasons (investigation gets OSINT methodology, bugfix gets diagnostic procedures, etc.)
2. **Organization kernel** — PACE role activation based on domain

Real tasks are frequently compound. Observed examples from stress tests and live sessions:

| Task | Actual domains | BST classified as | What went wrong |
|------|---------------|-------------------|-----------------|
| Debug OpenPlanter installation | bugfix + system_admin | bugfix | Model profile has bugfix in `disabled_domains`. Enrichment fired anyway, likely degrading performance. |
| Investigate Oracle credit risk via OpenPlanter | investigation + coding | investigation | Coding-specific tool guidance absent when agent needed to write API queries |
| Configure LM Studio provider settings | system_admin + bugfix | bugfix | Domain momentum kept flipping between the two on successive turns |
| Analyze SEC filing for fraud indicators | investigation + analysis | investigation | Analysis methodology (structured comparison, quantitative extraction) absent from enrichment |

The BST picks whichever domain has the strongest signal match. First match wins. The secondary domain's guidance is lost entirely. The model operates with an incomplete picture of what it's doing.

### Why This Matters Now

Three converging factors:

1. **Error Comprehension is deployed.** The agent now gets structured guidance on what went wrong (anti-actions). But it still gets incomplete guidance on what it's *doing*. Error comprehension is the negative knowledge prosthetic. Compound BST is the positive knowledge prosthetic. Together they bracket the model's reasoning space.

2. **Profile-Aware BST Enrichment (Priority 4) needs this.** The current plan for Priority 4 is: BST reads model profile, skips enrichment in `disabled_domains`. But with single-domain classification, a compound task like "debug the investigation tool" gets classified as either `bugfix` (disabled → no enrichment at all) or `investigation` (enabled → wrong enrichment). Neither is correct. Compound classification lets Profile-Aware enrichment make the right call: skip the disabled secondary, enrich with the enabled primary.

3. **The pattern is validated.** PageIndex demonstrated that replacing single-signal retrieval (vector similarity) with structured multi-signal retrieval (hierarchical tree) produces dramatically better results — 98.7% vs baseline on FinanceBench. Error Comprehension demonstrated that replacing single-type error classification (keyword match) with structured multi-field diagnosis (class + causal chain + anti-actions) eliminates loops. The same architectural move applied to domain classification should produce the same kind of improvement: richer structure → better model reasoning.

---

## Design Principles

1. **Deterministic only.** No LLM calls. Same regex + heuristic approach as current BST. The compound classification runs the same matchers — it just doesn't stop at first match.
2. **Primary domain always exists.** Every classification produces exactly one primary domain. Backward compatibility is non-negotiable — anything reading `current_domain` gets the primary as a string.
3. **Secondary is optional and bounded.** At most one secondary domain. Not a weighted vector, not a ranked list of all domains. Two is the maximum because enrichment from three domains would pollute context. If a task legitimately spans three domains, the third is noise at the enrichment level.
4. **Anti-enrichment is explicit.** When the secondary domain is in `disabled_domains` for the current model profile, the classification still records it for logging and momentum — but enrichment is suppressed. The agent knows it's doing bugfix work; it just doesn't get bugfix enrichment because the model can't use it effectively.
5. **Momentum tracks the compound signature.** Domain momentum applies to the primary+secondary pair, not just the primary. If three consecutive turns classify as `investigation + coding`, that compound signature is stable and shouldn't flip on a single `ls` command.

---

## Proposed Mechanism

### Classification Flow (modified from current BST)

```
Current BST:
  Message → run matchers → first match → single domain → enrichment

Compound BST:
  Message → run matchers → collect all matches with scores → 
    → highest score = primary domain
    → second highest score (if above threshold) = secondary domain
    → apply momentum to compound signature
    → emit CompoundClassification
    → enrichment reads primary (always) + secondary (if enabled in profile)
```

### CompoundClassification Structure

```python
{
    "primary": {
        "domain": "investigation",
        "confidence": 0.85,
        "matched_signals": ["investigate", "entity", "risk"]
    },
    "secondary": {                          # None if no secondary above threshold
        "domain": "coding", 
        "confidence": 0.55,
        "matched_signals": ["api", "query"]
    },
    "compound_signature": "investigation+coding",  # string for momentum tracking
    "momentum_turns": 3,                    # how many consecutive turns this signature held
    "enrichment_plan": {
        "primary_enrichment": true,         # always true if domain not disabled
        "secondary_enrichment": true,       # false if domain in disabled_domains
        "reason_secondary_skipped": null    # "disabled_in_profile" or "below_threshold" or null
    }
}
```

### Backward Compatibility

```python
# Anything that currently reads:
current_domain = extras_persistent.get("_bst_domain", "conversation")

# Still works. BST writes primary domain to the same key.
# Compound-aware consumers read:
compound = extras_persistent.get("_bst_compound", None)
```

Two keys written to shared state:
- `_bst_domain` — string, primary domain only. Backward compatible.
- `_bst_compound` — full CompoundClassification dict. New consumers read this.

### Scoring Modification

Current BST uses first-match-wins with word-boundary regex. Compound BST needs scores to rank:

```python
def score_domain(message, domain_config):
    """
    Score = number of matched signal patterns for this domain.
    Simple count. No weighting. Ties broken by domain priority order.
    """
    matched = []
    for pattern in domain_config["signals"]:
        if re.search(pattern, message, re.IGNORECASE):
            matched.append(pattern)
    return len(matched), matched
```

**Why count-based scoring:** It's deterministic, debuggable, and doesn't require tuning weights. A message that matches 3 investigation signals and 1 coding signal is primarily investigation. If we need weighted scoring later, the structure supports it — but start simple.

**Secondary threshold:** Secondary domain must match at least 1 signal AND primary must have at least 2 more matches than secondary. This prevents weak secondary classifications from polluting enrichment.

```python
SECONDARY_MIN_SIGNALS = 1
PRIMARY_LEAD_MINIMUM = 2  # primary must lead secondary by at least this many

def classify_compound(message, domain_configs):
    scores = []
    for domain, config in domain_configs.items():
        score, matched = score_domain(message, config)
        if score > 0:
            scores.append((domain, score, matched))
    
    scores.sort(key=lambda x: (-x[1], domain_priority(x[0])))
    
    primary = scores[0] if scores else ("conversation", 0, [])
    
    secondary = None
    if (len(scores) > 1 
        and scores[1][1] >= SECONDARY_MIN_SIGNALS
        and scores[0][1] - scores[1][1] >= PRIMARY_LEAD_MINIMUM):
        secondary = scores[1]
    
    # Edge case: if primary leads by less than PRIMARY_LEAD_MINIMUM,
    # the classification is ambiguous. Emit primary only, no secondary.
    # This prevents near-ties from producing unstable compound signatures.
    
    return primary, secondary
```

Wait — that logic is inverted. If primary leads by *less* than the minimum, we should suppress the secondary. But if primary leads by a lot, the secondary is clearly subordinate and safe to include. Let me correct:

```python
secondary = None
if (len(scores) > 1 
    and scores[1][1] >= SECONDARY_MIN_SIGNALS):
    if scores[0][1] - scores[1][1] < PRIMARY_LEAD_MINIMUM:
        # Near-tie: ambiguous. Primary only, no secondary.
        # Momentum will stabilize this over successive turns.
        secondary = None
    else:
        # Clear primary with viable secondary. Include both.
        secondary = scores[1]
```

Actually, revisiting: the near-tie case is exactly when compound classification is *most* valuable. If investigation and bugfix are scoring nearly equal, that's a genuinely compound task. Suppressing the secondary in the ambiguous case loses the most important signal.

Revised logic:

```python
secondary = None
if (len(scores) > 1 
    and scores[1][1] >= SECONDARY_MIN_SIGNALS):
    secondary = scores[1]

# No minimum lead required. If two domains both match strongly,
# that IS the signal — the task is compound.
# Momentum handles stability. Profile-awareness handles enrichment safety.
```

This is simpler, more honest about what the data says, and delegates stability to momentum rather than building it into the classifier. The classifier's job is accuracy. Momentum's job is stability. Don't mix them.

### Momentum Modification

Current momentum: if the same domain held for N consecutive turns, resist reclassification unless a different domain scores strongly.

Compound momentum: track the `compound_signature` string (`"investigation+coding"`, `"investigation"`, etc.).

```python
def apply_momentum(new_primary, new_secondary, current_signature, momentum_turns):
    new_signature = format_signature(new_primary, new_secondary)
    
    if new_signature == current_signature:
        # Same compound signature. Increment momentum.
        return new_primary, new_secondary, new_signature, momentum_turns + 1
    
    if momentum_turns >= MOMENTUM_THRESHOLD:
        # Strong momentum. Require elevated signal to override.
        # Only override if the NEW primary domain is different from 
        # BOTH the current primary AND secondary.
        current_domains = parse_signature(current_signature)
        if new_primary["domain"] in current_domains:
            # New primary is within the current compound. Keep current.
            return restore_from_signature(current_signature), current_signature, momentum_turns + 1
        else:
            # Genuinely new domain. Reset momentum.
            return new_primary, new_secondary, new_signature, 1
    else:
        # Weak momentum. Accept the new classification.
        return new_primary, new_secondary, new_signature, 1
```

**Key insight:** With compound signatures, momentum is *more* stable than single-domain momentum. A task classified as `investigation+coding` won't flip to `coding+investigation` on a code-heavy turn — the signature contains both domains. It will only break momentum when a genuinely new domain appears that isn't in the current compound. This is the correct behavior: operational turns (`ls`, `cat`, `pip install`) match `file_ops` or `system_admin`, but if the compound signature is `investigation+coding` with strong momentum, those operational turns don't break it.

### Enrichment Blending

The hardest design question. Three options:

**Option A: Primary only, secondary logged.**
Simplest. Enrichment comes from primary domain only. Secondary is recorded in the compound classification for observability but doesn't affect the model's context. Profile-awareness only needs to check one domain.

**Option B: Primary full, secondary abbreviated.**
Primary domain gets full enrichment. Secondary domain gets a single-line contextual note: `"[BST] Secondary domain: coding — tool syntax precision matters for this task."` Not full enrichment, just a lightweight signal. Costs ~20 tokens of context.

**Option C: Merged enrichment template.**
Create compound-specific enrichment templates for common pairs. `investigation+coding` gets a merged template that combines investigation methodology with tool precision notes. Requires authoring O(n²) templates for domain pairs.

**Recommendation: Option B.**

Option A wastes the secondary classification. Option C doesn't scale and requires predicting which compound pairs matter. Option B provides the signal with minimal context cost and zero authoring burden — the abbreviated note is generated from the domain's description field, which already exists in the domain config.

```python
def build_enrichment(compound_classification, model_profile, domain_configs):
    plan = compound_classification["enrichment_plan"]
    enrichment_parts = []
    
    # Primary enrichment (full)
    if plan["primary_enrichment"]:
        primary_domain = compound_classification["primary"]["domain"]
        enrichment_parts.append(domain_configs[primary_domain]["enrichment"])
    
    # Secondary enrichment (abbreviated)
    if (compound_classification["secondary"] is not None 
        and plan["secondary_enrichment"]):
        sec_domain = compound_classification["secondary"]["domain"]
        sec_desc = domain_configs[sec_domain]["brief_description"]
        enrichment_parts.append(
            f"[BST] Secondary context: {sec_domain} — {sec_desc}"
        )
    
    return "\n\n".join(enrichment_parts)
```

### Profile-Aware Integration

This design note subsumes Priority 4 (Profile-Aware BST Enrichment). The enrichment plan in CompoundClassification handles it:

```python
def build_enrichment_plan(primary, secondary, model_profile):
    disabled = model_profile.get("disabled_domains", [])
    
    plan = {
        "primary_enrichment": primary["domain"] not in disabled,
        "secondary_enrichment": (
            secondary is not None 
            and secondary["domain"] not in disabled
        ),
        "reason_primary_skipped": (
            "disabled_in_profile" if primary["domain"] in disabled else None
        ),
        "reason_secondary_skipped": None
    }
    
    if secondary is None:
        plan["reason_secondary_skipped"] = "no_secondary_classified"
    elif secondary["domain"] in disabled:
        plan["reason_secondary_skipped"] = "disabled_in_profile"
    
    return plan
```

When primary is disabled: no enrichment at all. The model operates unassisted in that domain. This is the correct behavior — the eval profile says enrichment hurts performance in this domain for this model.

When secondary is disabled: primary enrichment only, with a log note that secondary was suppressed. The model gets guidance for its primary task but not for the secondary aspect it can't use effectively.

---

## Integration Points

### Modified files

| File | Change |
|------|--------|
| `_11_belief_state_tracker.py` | Replace first-match classification with scored compound classification. Write both `_bst_domain` and `_bst_compound` to shared state. |
| `_11_belief_state_tracker.py` | Modify momentum tracking to use compound signatures. |
| `_11_belief_state_tracker.py` | Read model profile for enrichment plan. Add `brief_description` field to each domain config. |

### New data in shared state

| Key | Type | Consumer |
|-----|------|----------|
| `_bst_domain` | string | Existing — fallback, org kernel, supervisor. Unchanged. |
| `_bst_compound` | dict | New — any compound-aware consumer. |

### No new files

This is a modification to the existing BST extension, not a new extension. The BST already owns domain classification. Compound classification is a refinement, not a new capability. One file modified. No new hook points. No new extensions.

---

## What This Does NOT Do

- **Does not use LLM calls.** Classification remains fully deterministic.
- **Does not emit more than two domains.** Primary + optional secondary. Not a ranked list. Not a vector.
- **Does not create compound enrichment templates.** Secondary enrichment is a single abbreviated line, not a full template.
- **Does not change the organization kernel's role activation.** The org kernel reads `_bst_domain` (primary only). Compound-aware role activation is a future extension if needed.
- **Does not change error comprehension behavior.** Error comprehension reads command output, not domain classification. No interaction.
- **Does not persist compound history across sessions.** Per-session momentum only. Cross-session domain patterns are a future analytics feature, not a classification feature.
- **Does not handle domain evolution within a single turn.** If a single message spans three domains, the classifier picks two. Mid-turn domain shifts are handled by the next turn's classification.

---

## Testing Criteria

1. Message "debug the OpenPlanter API query timeout" → primary: `bugfix`, secondary: `investigation` (or `coding`). Both domains present in compound.
2. Message "investigate Oracle Corporation credit risk" → primary: `investigation`, secondary: None. Single domain, no compound.
3. Message "fix the pip install error" → primary: `bugfix`, secondary: `system_admin`. Compound.
4. Backward compatibility: `_bst_domain` contains primary domain string. Existing consumers unaffected.
5. Momentum: 3 consecutive `investigation+coding` turns, then a `file_ops` signal from `ls` output → compound signature holds, momentum increments.
6. Momentum break: 3 consecutive `investigation+coding` turns, then user says "now let's plan the next sprint" → `planning` is not in current compound → momentum breaks, new classification.
7. Profile-aware: primary `investigation` (enabled) + secondary `bugfix` (disabled) → primary enrichment fires, secondary enrichment suppressed, reason logged as "disabled_in_profile".
8. Profile-aware: primary `bugfix` (disabled) → no enrichment at all. Log note that primary domain disabled.
9. Near-tie: `investigation` matches 2 signals, `analysis` matches 2 signals → both classified (no minimum lead), tie broken by domain priority order.
10. Abbreviated secondary enrichment: secondary domain `coding` → injection is `"[BST] Secondary context: coding — tool syntax precision and parameter accuracy matter for this task."` Not full coding enrichment template.

---

## Open Questions

1. **Should the org kernel become compound-aware?** Currently it activates a single PACE role based on primary domain. A compound-aware kernel could activate a primary role with secondary role's tool knowledge available. Deferred — observe whether compound BST enrichment alone resolves the measured issues before adding complexity to role activation.

2. **Should compound signatures feed into the model router?** When the model router is built (backlog item), compound classification could inform model selection — a `bugfix+investigation` task might route to a different model than pure `investigation`. Deferred — model router depends on more model profiles than we currently have.

3. **What's the right secondary threshold?** Design note proposes `SECONDARY_MIN_SIGNALS = 1` with no minimum lead. This might be too permissive — nearly every message will have some incidental match with a secondary domain. May need empirical tuning from ST-003 data. Start permissive, tighten from data.

4. **Should compound classification history be logged for pattern analysis?** A time-series of compound signatures across a session could reveal task phase transitions (investigation → investigation+coding → coding → bugfix+coding → bugfix). Useful for future observability but not needed for v1.0. Log the compound dict per-turn, analyze later.

---

## Build Sequence

1. Add `brief_description` field to each domain config in BST. Low-effort, no behavior change.
2. Replace first-match classification with scored classification. All matchers run, scores collected.
3. Implement compound output: primary + optional secondary. Write to `_bst_compound`.
4. Maintain backward compatibility: `_bst_domain` still written as primary string.
5. Modify momentum to track compound signatures.
6. Implement enrichment blending (Option B: primary full + secondary abbreviated).
7. Integrate profile-awareness into enrichment plan. This subsumes Priority 4.
8. Test against the scenarios in Testing Criteria above.
9. Deploy. Run ST-003 with compound BST active. Compare domain classification accuracy against single-domain BST on the same task logs.

---

## Relationship to Broader Architecture

Compound BST is the positive-knowledge complement to Error Comprehension's negative knowledge. Together:

```
Before model reasons about a task:
  Compound BST tells it: "You are doing investigation + coding. 
    Here's investigation methodology. Secondary note: tool precision matters."

After model executes a command that fails:
  Error Comprehension tells it: "This was an interactive prompt. 
    Don't retry. Don't type into it. Write the config file directly."
```

The model's reasoning is bracketed: structured positive guidance on what it's doing (compound BST), structured negative guidance on what failed (error comprehension). The model reasons within those constraints rather than in open space.

This is the same pattern as PageIndex replacing vector similarity with hierarchical tree structure. The scaffold gets more dimensions. The reasoning gets more precise. Structure enables reasoning; similarity approximates it.

---

*Motivated by empirical failures in ST-002 and OpenPlanter debugging sessions. Mechanism designed to be deterministic, backward-compatible, and extensible. Subsumes Priority 4 (Profile-Aware BST Enrichment). Ready for L3 spec when build sequence begins.*
