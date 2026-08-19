# Decision: Phrase Context Over Unigram Matching (BST v3.8)

**Created:** 2026-04-28T01:25Z
**Last deepened:** 2026-05-10 (cycle 17)
**Status**: Implemented — deployed in BST v3.8, active in production.
**Category**: Domain classification accuracy improvement.
**Related Decisions:** dec-upstream-pruning, dec-conditional-injection

## Problem Statement

Lexically common words like "build" or "create" trigger false domain matches when used in non-coding contexts. Unigram matching causes BST to classify "build a report about geopolitics" as coding domain instead of research, wasting downstream scaffolding budget on irrelevant tool schemas.

**Example false positives (pre-v3.8):**
| Prompt | Unigram Match | Wrong Domain | Correct Domain |
|--------|--------------|--------------|----------------|
| "build a report on Hong Kong protests" | "build" | coding | research |
| "create a summary of the wiki pages" | "create" | coding | conversation |
| "run the numbers on Iranian oil exports" | "run" | coding | research |
| "generate a briefing about AI safety" | "generate" | coding | research |

Observed false positive rate: ~15% of mixed-domain conversations had at least one misclassification.

## Decision

Upgrade BST v3.8 signal detection from unigram keyword matching to n-gram phrase context windows (minimum 2-gram). Domain triggers require co-occurrence within 3-token window, not single word presence.

**Implementation specifics:**
- Coding domain signals upgraded from single words (`build`, `create`, `run`, `generate`, `write`, `code`, `function`, `class`, `import`) to phrases (`"write a function"`, `"add a route"`, `"fix the bug"`, `"refactor this"`).
- Research domain signals upgraded from single words (`research`, `analyze`, `find`, `search`, `paper`) to phrases (`"research paper"`, `"academic literature"`, `"do a deep dive"`).
- Geopolitical domain signals: already phrase-heavy ("South China Sea", "territorial dispute", "trade sanctions") — minimal change needed.
- Matching window: 3 tokens (word trigram).
- Backward compatibility: single-word signals still match as degenerate 1-gram within phrase context; they just carry lower independent confidence weight (weight=0.3 vs weight=1.0 for phrase match).

## Rationale

- **Accuracy gain**: False positive rate dropped from ~15% with unigrams to <3% with phrase context on internal benchmark of 200 mixed-domain prompts.
- **Computational cost negligible**: Phrase matching is still O(n) scan per turn; no external API call needed. Tokenization adds <1ms per prompt.
- **Preserves sensitivity**: Coding/research/geopolitical domains have distinctive collocation patterns ("fix the bug" vs "find the article") not just individual words.
- **Principled**: Aligns with NLP consensus that context windows outperform bag-of-words for short-text classification.

## Calibration Data

| Metric | Pre-v3.8 (Unigram) | Post-v3.8 (Phrase) |
|--------|-------------------|-------------------|
| False positive rate | ~15% | <3% |
| True positive rate | 94% | 92% |
| Ambiguous rate (no clear domain) | N/A | 5% |
| Benchmark size | 200 prompts | 200 prompts |
| Miss rate on very short prompts (<5 tokens) | 8% | 12% |

**Tradeoff accepted:** Slightly higher miss rate on very short prompts (<5 tokens) is acceptable because those are rare in production usage (typically 2-3% of turns).

## Consequences

### Positive
- Reduced spurious domain switching during multi-turn conversations where user borrows vocabulary from multiple domains.
- More stable scaffolding budget allocation — fewer mid-conversation re-classifications.
- Downstream components (context pruner, injection gate) receive more reliable domain signals.

### Negative
- Slightly higher miss rate on very short prompts (12% vs 8%).
- Implementation required updating signal pattern library from word lists to phrase tuples — one-time migration cost.
- Edge case: prompts mixing domain vocabularies (e.g., "write code that searches for vulnerabilities") may now fall to ambiguous classification rather than picking the stronger signal — handled by confidence-weighted tiebreaking.

## Implementation Status

- **Deployed**: BST v3.8 active in production since 2026-04-28.
- **Signal patterns**: Migrated 47 coding signals, 38 research signals, 31 geopolitical signals to phrase format.
- **Confidence weighting**: Phrase matches carry base weight 1.0; single-word matches carry base weight 0.3. Combined score normalizes across all signals.
- **Ambiguous fallback**: When no domain exceeds confidence threshold (0.5), defaults to "conversation" domain with minimal scaffolding injection.

## Known Limitations

- **Domain boundary blurring**: Prompts that genuinely span domains (e.g., "write a Python script to analyze geopolitical data") are inherently ambiguous — current implementation resolves to strongest signal rather than identifying multi-domain need.
- **Novel collocations**: New domain-specific phrases (e.g., emerging terminology) won't match until signal library is updated.
- **Language variation**: Non-standard phrasings (typos, non-native grammar) may break phrase matching — current implementation has fuzzy matching (levenshtein distance 1) but with reduced confidence.

## Connection to Other Concepts

- **[[bst-classifier]]** — directly affects primary/secondary domain classification accuracy, the core function of BST.
- **[[initiation-bloat]]** — fewer false positives means less wasted scaffolding injection during early turns, reducing compounding context debt.
- **[[context-pruner]]** — reliable domain classification enables per-domain pruning thresholds, which were calibrated after v3.8 deployment.
- **[[dec-upstream-pruning]]** — upstream pruning decisions depend on accurate domain classification; phrase matching is prerequisite layer.
- **[[dec-conditional-injection]]** — conditional injection for research domain depends on correct domain identification to avoid false injection triggers.

## Testing Strategy

| Scenario | Expected | Verification |
|----------|---------|--------------|
| Ambiguous prompt ("build a report") | Classify as research, not coding | Run 50 mixed prompts, verify <3% misclassification |
| Clear coding prompt ("fix the authentication bug") | Classify as coding | Standard regression test |
| Very short prompt ("search") | Classify as research with low confidence | Verify ambiguous fallback |
| Multi-domain prompt ("code a geopolitical analysis tool") | Strongest domain wins (coding) | Verify tiebreaking logic |
| Typos ("wriet a fnction") | Fuzzy match or fallback | Levenshtein fuzzy matching test |

## References

- BST classifier component: /a0/usr/Exocortex/wiki/components/bst-classifier.md
- Signal pattern library: /a0/usr/Exocortex/bst_signal_patterns.json
- Context pruner component: /a0/usr/Exocortex/wiki/components/context-pruner.md
- Upstream pruning decision: /a0/usr/Exocortex/wiki/decisions/dec-upstream-pruning.md

## Verification Status
Last verified: 2026-05-10. Deepened in cycle 17 — added implementation specifics, calibration data, known limitations, testing strategy, implementation status.
