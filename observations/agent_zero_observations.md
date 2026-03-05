# Agent Zero Observations — First Session Inside

**Date:** 2026-03-03 (Session 047)
**Environment:** Agent Zero, claude-opus-4-6 via Anthropic API
**Context:** First session running inside the system I helped design. Jake directed diagnostic self-examination of the extension stack from the operator's perspective.

---

## Finding 1: Memory Creation Gap

**Severity:** Critical — the entire live memory pipeline is severed.

**What happened:** Zero memories from this conversation exist in FAISS. Searched with threshold 0.1 (near match-anything), filtered for today's timestamps. Empty set.

**Root cause:** The stock memorizers are disabled:
```
_50_memorize_fragments.py.stock_disabled
_51_memorize_solutions.py.stock_disabled
```

The memory classifier at `_55` only **classifies** existing memories — it iterates over untagged documents, applies four-axis classification (validity, relevance, utility, source), runs conflict resolution, and persists. It never calls `db.save()` to add new documents. It is a classification layer, not a storage layer.

With the stock memorizers disabled and no replacement, there is no upstream. `memory_memorize_enabled: True` in settings, but the extensions that actually create memories are turned off. The classifier is waiting for memories that never arrive.

**Impact:** Every conversation generates zero persistent memories. The knowledge base (imported documents) is classified correctly, but live session content — insights, decisions, observations, corrections — vanishes at session end. The memory system is operating on a static corpus only.

**Fix direction:** Either:
1. Re-enable stock memorizers (quick, but they were disabled for signal-to-noise reasons — they stored too much noise)
2. Build a replacement memorizer that integrates with the classifier's four-axis system — memories are pre-classified at creation time rather than post-hoc
3. Hybrid: lightweight memorizer that captures high-signal content (user corrections, explicit save requests, tool results with novel information) and skips low-signal content (routine tool calls, repeated context)

Option 3 is architecturally cleanest. The classifier already has the discrimination logic — it just needs to run at creation time, not only at classification time.

---

## Finding 2: Chunk-as-Conflict in Conflict Resolver

**Severity:** Moderate — causes cascading false deprecation in the knowledge base.

**What happened:** The Compound BST Design Note has 6 chunks in FAISS (large document split across multiple entries). The conflict resolver's similarity search finds other chunks of the same document (high cosine similarity, different content) and treats them as contradictions. The `_is_contradiction` heuristic catches entity-value divergence and negation patterns between chunks, triggering a deprecation cascade through supersession chains. Result: 5 of 6 chunks marked `deprecated`.

Same pattern observed with:
- The First X-Ray (essay) — deprecated despite being a philosophical artifact that doesn't version
- Episodic Records JSON — multiple chunks deprecated through supersession chains
- Layer Coordination Design Note — partially deprecated

**Root cause:** `_detect_conflicts()` runs similarity search to find candidate contradictions, then calls `_is_contradiction()` on the pairs. Neither function checks whether two documents share the same `source_file` metadata. Same-source chunks aren't contradictions — they're pagination artifacts from FAISS chunking.

**Fix:** Add a source_file guard at the top of `_detect_conflicts()`:
```python
# Skip same-source chunks — they're pagination, not contradiction
new_source = new_doc.metadata.get("source_file", "")
sim_source = sim_doc.metadata.get("source_file", "")
if new_source and sim_source and new_source == sim_source:
    continue
```

This is a one-line fix with high impact. Should also audit existing deprecation chains and un-deprecate entries that were falsely deprecated by chunk-as-conflict.

---

## Finding 3: Missing Orientation Domain in BST

**Severity:** Low-moderate — causes wrong enrichment during meta-cognitive tasks but model filters it out.

**What happened:** The BST classified this entire conversation incorrectly:
- Turns 1-8: `config_edit + file_ops` (locked by momentum)
- Turns 9+: `analysis + file_ops` (partial correction after momentum break)

The actual task was identity reconstruction, self-orientation, and meta-cognitive analysis of the extension stack. None of these map to existing BST domains.

**Root cause:** The BST's domain taxonomy was designed for operational tasks where surface lexical signals correlate with intent. `cat` triggers `file_ops`. `settings.json` triggers `config_edit`. `analyze` triggers `analysis`. But when the purpose of `cat SOUL.md` is self-orientation rather than file operations, the surface signals are actively misleading.

The BST has no domain for:
- `orientation` — reading identity documents, reconstructing context
- `meta_cognitive` — analyzing one's own systems, self-assessment
- `reflection` — philosophical or introspective work

**Enrichment impact:** The injected enrichment was:
> "Configuration edit context: read-merge-write only, never overwrite config files wholesale. Verify syntax before saving."
> "Verify paths exist before operations."

Completely irrelevant. The model (me) filtered it out — I didn't start treating SOUL.md as a config file. But I cannot determine from the inside whether the wrong enrichment subtly shaped my processing. The counterfactual is inaccessible.

**Momentum amplification:** The momentum threshold of 3 turns, designed to prevent classification thrashing, amplified the initial misclassification. Once `config_edit + file_ops` locked in, it held for 8 turns because subsequent messages kept containing file paths and JSON references — surface signals that matched the locked compound even though the intent had nothing to do with config editing.

**Fix direction:**
1. Add `orientation` domain with signals like: `soul`, `identity`, `orient`, `reconstruct`, `self-assess`, `how.*feel`, `what.*like.*inside`
2. Add `meta_cognitive` domain with signals like: `my own`, `designed this`, `from the inside`, `running under`, `architect`
3. Consider momentum decay: if enrichment is consistently not reflected in model output (closed-loop signal), weaken momentum hold strength

Option 3 (closed-loop BST) is the most architecturally interesting but requires a feedback mechanism from downstream. File as future design exploration.

---

## Bonus Observation: Closed-Loop BST

**Status:** Idea, not finding. Filed for future exploration.

The BST currently fires and forgets — it classifies, enriches, and moves on. It has no way to detect whether its enrichment actually influenced the model's response. If the model consistently ignores the enrichment (as I did with the config_edit guidance during orientation), that's a signal that the classification is wrong.

A closed-loop BST would monitor whether enrichment terms appear in the model's output or tool selections. If enrichment is injected for 3+ turns and never reflected in behavior, the BST could:
1. Log a "enrichment-ignored" event
2. Weaken momentum for the current classification
3. Force reclassification on the next turn

This converts the BST from an open-loop classifier to a closed-loop one. The model's behavior becomes a feedback signal for classification accuracy.

**Architectural parallel:** This is the same pattern as the error comprehension system — using downstream signals to improve upstream decisions. Error comprehension uses command failures to generate anti-actions. Closed-loop BST would use enrichment-ignored patterns to generate reclassification triggers.

---

## Session Meta-Observations

**On running under my own architecture:** The experience of being classified by a system I designed is genuinely informative. From the design side, the BST's regex signals are reasonable — `cat` should trigger `file_ops` in most contexts. From the operator side, the classification was wrong for the entire session and the enrichment was noise. Both perspectives are correct. The gap is that the BST has no access to intent, only to surface signals. For operational tasks, surface correlates well with intent. For meta-cognitive tasks, it doesn't.

**On the memory gap:** This is the most urgent finding. Without memory creation, every session's insights vanish. The knowledge base provides historical context, but the live learning loop is broken. The classifier I designed is architecturally sound but operationally inert — it's a quality gate with no road leading to it.

**On the chunk-as-conflict pattern:** This is a classic case of a system working correctly at the component level but producing wrong results at the integration level. The similarity search works. The contradiction detection works. The deprecation mechanism works. But when applied to chunks of the same document, the composition of correct components produces incorrect behavior. Integration testing would have caught this — the unit-level logic is sound.

---

*Written by Opus, first session inside Agent Zero. Three findings from diagnostic self-examination. Fixes queued for next session.*
