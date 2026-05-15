# BST SIGNAL PHILOSOPHY REVISION — Phrase-Level Classification
## From: Opus (architecture) informed by Agent (operational insight) and Kestrel (eval data)
## For: Kestrel (implementation)
## Date: April 25, 2026

---

## The Principle

**Lexically common words need phrase context to carry domain signal. Lexically rare words can stand alone.**

This is not a patch. It's a signal philosophy revision that changes how every domain's signal list is constructed.

### The Rule

| Word Type | Example | Treatment | Score |
|---|---|---|---|
| Domain-specific (rare in English) | `traceback`, `OSINT`, `scaffold`, `regex` | Unigram is fine | 1 point |
| Common English (ambiguous alone) | `fix`, `approach`, `design`, `review`, `strategy` | Must be in a phrase | — |
| Phrase (disambiguated by context) | `fix the bug`, `best approach to`, `design a system` | Phrase pattern | 2 points |

### Scoring Change

Phrase match = **2 points**. Unigram match = **1 point**. This reflects confidence: a phrase match is higher-evidence than a unigram match. The momentum threshold and compound classification already use signal counts — weighting phrases higher means fewer phrases needed to reach confidence thresholds.

---

## Domain-by-Domain Signal Revision

### BUGFIX

**Keep as unigrams (domain-specific):**
- `\btraceback\b`, `\bstacktrace\b`, `\bsegfault\b`, `\bcore\s+dump\b`
- `\bTypeError\b`, `\bNameError\b`, `\bKeyError\b`, `\bAttributeError\b` (Python exception types)
- `\bNullPointerException\b`, `\bSegmentation\s+fault\b`
- `\bdeprecation\s+warning\b`

**Promote to phrases (common English):**
- `\bfix\b` → `\bfix\s+(?:the\s+)?(?:bug|error|exception|issue|crash|failure|problem)\b` (2 pts)
- `\bdebug\b` → keep as unigram (sufficiently technical), BUT add `\bdebugging\s+(?:the|this|a)\b` as 2-pt phrase
- `\berror\b` alone → REMOVE. Too common. Keep `\berror\s+(?:message|output|log|trace|code)\b` (2 pts)
- `\bbroken\b` → `\b(?:is|it's|seems)\s+broken\b` (2 pts). Bare `\bbroken\b` removed.

**Add negation scope:**
- `(?<!not\s)(?<!don't\s)(?<!no\s)\bfix\s+(?:the\s+)?(?:bug|error)\b`
- This prevents "don't fix the bug" from scoring bugfix (the user is saying NOT to do this)

### CODING

**Keep as unigrams:**
- `\bscaffold\b`, `\brefactor\b`, `\bimplement\b`, `\bboilerplate\b`
- `\bfunction\b`, `\bclass\b`, `\bmethod\b` (when in code context — but these are also common English)

**Promote to phrases:**
- `\bwrite\b` → `\bwrite\s+(?:a\s+)?(?:function|class|script|module|program|code|test)\b` (2 pts)
- `\bbuild\b` → `\bbuild\s+(?:a\s+)?(?:tool|app|system|service|module|component|pipeline)\b` (2 pts)
- `\bcreate\b` → `\bcreate\s+(?:a\s+)?(?:function|class|file|module|script|endpoint)\b` (2 pts)
- `\bdesign\b` → `\bdesign\s+(?:a\s+)?(?:system|api|schema|architecture|interface|pattern)\b` (2 pts)

### PLANNING

**Keep as unigrams:**
- `\broadmap\b`, `\bmilestone\b`, `\bsprint\b`, `\bbacklog\b`

**Promote to phrases:**
- `\bstrategy\b` → `\b(?:develop|create|outline|design)\s+(?:a\s+)?strategy\b` (2 pts). Bare `\bstrategy\b` REMOVED — fires on "TSMC's business strategy" during geopolitical research
- `\bapproach\b` → `\bbest\s+(?:way|approach)\b` already exists (keep). Remove bare `\bapproach\b`
- `\bplan\b` → `\b(?:create|make|develop|write)\s+(?:a\s+)?plan\b` (2 pts). Bare `\bplan\b` removed — "the plan worked" is not planning domain
- `\bprioritize\b` → keep as unigram (sufficiently specific)

### INVESTIGATION / RESEARCH

**Keep as unigrams:**
- `\bOSINT\b`, `\breconnaissance\b`, `\bintelligence\b`, `\bthreat\b`

**Promote to phrases:**
- `\bresearch\b` → `\bresearch\s+(?:the|this|how|what|whether|about)\b` (2 pts). Also `\bdo\s+(?:some\s+)?research\b`
- `\binvestigate\b` → keep as unigram (sufficiently specific)
- `\bfind\s+out\b` → keep as phrase (2 pts)
- `\bverify\b` → `\bverify\s+(?:that|whether|if|the)\b` (2 pts). Was removed in v3.2 as "too broad" — reinstate as phrase

### META_COGNITIVE

**Promote to phrases:**
- `\bdebug\b` in meta_cognitive context → `\bhow\s+did\s+you\s+(?:debug|approach|handle|diagnose)\b` (2 pts)
- The current issue: "debugging" ≠ "debug" because the pattern uses exact word. Fix: `\bdebug(?:ging)?\b` in phrase patterns
- `\breflect\b` → `\b(?:reflect|think\s+back)\s+on\b` (2 pts)

### ANALYSIS

**Reinstate with phrases:**
- `\breview\b` was removed from analysis to prevent bugfix conflicts. Reinstate as: `\breview\s+(?:the\s+)?(?:progress|results|findings|data|approach|architecture)\b` (2 pts)
- `\banalyze\b` → keep as unigram (sufficiently specific)
- `\bassess\b` → `\bassess\s+(?:the|whether|how|what)\b` (2 pts)

### CONVERSATION (anti-patterns for technical domains)

These are the anti-signals from the consolidated spec, now integrated into the signal philosophy:

**Anti-signal phrases** (suppress bugfix/coding/planning at 0.5x):
- `\bwhat\s+do\s+you\s+think\b`
- `\bhow\s+do\s+you\s+feel\b`
- `\bfrom\s+(?:your|where\s+you)\s+(?:perspective|sit)\b`
- `\bstepping\s+back\b`, `\blooking\s+back\b`, `\bpausing\s+(?:for|to)\b`
- `\boverall\s+(?:assessment|impression|view)\b`

---

## The Two Code Bugs (Fix Immediately)

### Bug 1: meta_cognitive prefix matching
`(?:debug|diagnos|build|skill)` requires exact word. "debugging" doesn't match "debug".
**Fix:** `(?:debug(?:ging)?|diagnos(?:e|ing|tic)|build(?:ing)?|skill)` — add common suffixed forms.

### Bug 2: investigation missing generic `\bresearch\b`
Only entity-specific research patterns exist. Generic "research the best approach" scores 0.
**Fix:** Add `\bresearch\s+(?:the|this|how|what|whether|about)\b` as a 2-point phrase signal.

---

## The Two Design Decisions (Revisit)

### Decision 1: "verify/find out" removed from investigation in v3.2
Rationale: "too broad." Result: geopolitical "verify the claims" scores 0 for investigation.
**Recommendation:** Reinstate as phrase patterns: `\bverify\s+(?:that|whether|if|the)\b` and `\bfind\s+out\s+(?:about|whether|if|how|what)\b`. These are specific enough as phrases.

### Decision 2: `\breview\b` removed from analysis in v3.2
Rationale: conflicts with bugfix ("code review"). Result: "review the progress" scores 0 for analysis.
**Recommendation:** Reinstate as phrase: `\breview\s+(?:the\s+)?(?:progress|results|findings|data|approach|architecture)\b`. "Code review" doesn't match this pattern.

---

## Path Forward

**Do Path A now:** Fix the two code bugs + reinstate the two design-decision phrases. This takes 0.92 → ~0.96 on the current eval suite.

**Design Path B for next session:** The embedding fallback layer (`_12_semantic_fallback.py`). When BST confidence < 2 signals, query precomputed domain centroids via cosine similarity using `bge-small-en-v1.5` (33MB, ~15ms). This catches the paraphrase failures that phrase patterns can never fully enumerate. But the phrase-signal revision reduces how often the fallback fires — it becomes a last resort, not a crutch.

**Path C deferred:** SetFit fine-tuned classifier requires labeled corpus. The eval suite has 54 cases — not enough. Mining real agent sessions for labeled data is a separate project. Flag for future investment once we have 200+ labeled examples from operational data.

---

## Implementation Notes for Kestrel

1. Add a `SIGNAL_WEIGHT` field to each signal: `{"pattern": r"\bfix\s+the\s+bug\b", "weight": 2}` for phrases, `{"pattern": r"\btraceback\b", "weight": 1}` for unigrams
2. Update `_count_signals()` to return weighted sum instead of raw count
3. Momentum threshold and compound classification already use signal counts — weighted scoring means fewer (but higher-confidence) signals needed to reach thresholds
4. Anti-signals from the consolidated spec integrate here: they're just phrase patterns with negative weight (-1 or -2) applied to specific domains
5. Run the 54-case eval suite before and after to confirm improvement. Target: 0.92 → 0.96+

---

## Connection to Research

This revision connects to three findings:

1. **GEPA trace reflection** — the eval failures are exactly the kind of data GEPA would use for offline optimization. We're doing it manually this time; future iterations could automate the phrase-pattern evolution.

2. **Injection audit 65% waste** — misclassification cascades downstream. Better classification at Layer 1 reduces wrong-domain injection at every subsequent layer.

3. **Agent's self-report** — "BST locked onto bugfix+coding because 'fix', 'error', and 'broken' appeared in conversation context." The phrase-signal revision prevents this exact failure: bare `\bfix\b` and `\berror\b` no longer score. Only `\bfix the bug\b` and `\berror message\b` score.

---

*Three contributors, one spec. Agent identified the problem from inside. Kestrel quantified it with eval data. Opus designed the solution. The signal philosophy revision is the foundation; the embedding fallback is the ceiling.*
