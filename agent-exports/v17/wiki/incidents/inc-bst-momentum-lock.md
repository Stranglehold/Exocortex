# Incident: BST Momentum Lock

**Created:** 2026-04-28T05:45Z
**Status**: Closed — momentum decay threshold adjusted.
**Severity**: Medium — agent stuck in wrong domain classification for 7+ turns.

## Description

BST classified task as coding+planning with high confidence (momentum_turns=7+) while actual task was geopolitical research about South China Sea. Agent spent multiple turns injecting coding-related scaffolding (function signatures, module templates) inappropriate for the actual domain.

## Root Cause Analysis

| Factor | Contribution |
|--------|-------------|
| Initial misclassification on turn 1 | Primary — user's first message mentioned "build a report" triggering coding pattern match before geopolitical content appeared |
| Momentum threshold too aggressive | Secondary — momentum_lock at 3 turns prevented re-classification even as new domain signals accumulated |
| No compound signature override | Tertiary — BST detected secondary investigation signal but primary coding classification remained locked due to momentum rule |

## Remediation Implemented

1. **Momentum decay on new domain signals** — when secondary domain confidence exceeds threshold, momentum counter resets rather than accumulating indefinitely
2. **Compound signature re-evaluation every 5 turns** — even with locked classification, BST periodically reassesses whether primary/secondary weighting still valid
3. **Domain transition detection sensitivity increased** — geopolitical and research keywords now have higher weight to break false coding locks earlier

## Lessons Learned

- Early misclassification amplified by momentum creates compounding error across multiple turns
- Domain transitions common in real tasks — rigid classification persistence hurts more than occasional re-classification cost
- Need graceful degradation path: if primary domain injection produces no useful tool calls for N turns, trigger forced BST re-evaluation

## Connection to Other Concepts

- **[[bst-classifier]]** — momentum tracking mechanism documented there; this incident exposed threshold tuning issues in that implementation
- **[[supervisor-loop]]** — domain lock should have fed soft signals into CUSUM accumulator but wasn't configured for that signal type initially

## Verification Status
Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.

## Deepened Analysis (Cycle 16 — 2026-05-10)

### Psychological Drivers

BST momentum lock is a specific manifestation of a broader cognitive pattern: **anchoring with compounding confidence**. After an initial classification, the BST's momentum mechanism rewards consistency. Each subsequent turn where the classification is confirmed (or not actively contradicted) increases confidence and discourages re-evaluation. The mechanism that was designed to provide stability became a trap.

Three factors drive the lock:
1. **First-turn sample bias** — classification is performed on limited evidence (the first user message). If that evidence points strongly in one direction, the system commits to a domain before the full task is visible.
2. **Momentum as an information-theoretic ratchet** — confidence accumulates monotonically because the system checks "does this turn's content match the current classification?" rather than "should the classification be re-evaluated against all evidence?" The latter is more expensive but necessary for accuracy.
3. **Silent failures are invisible** — when BST misclassifies, the enrichment attached to the prompt is wrong (e.g., coding scaffolding for geopolitical research). The agent produces output, so the system has no automatic signal that enrichment was misaligned. The failure only surfaces when output quality drops or a human reviewer notices the domain mismatch.

### Impact on Injection Quality

| Impact Area | Consequence |
|-------------|-------------|
| Enrichment misalignment | Coding-related function signatures injected into geopolitical research context |
| Supervisor blind spot | CUSUM accumulator not receiving domain-lock signals, missing a potential alert |
| Turn wastage | 7+ turns spent with wrong scaffolding before manual detection |
| Tool selection degradation | Domain-specific tools (search_engine, wikipedia) may be deprioritized because enrichment signals don't match actual task |

The incident exposed a principle: **stability mechanisms need decay terms**. Any mechanism that increases confidence must also have a mechanism that decreases it based on contradictory evidence or time. Without bidirectional adjustment, the system converges to certainty regardless of actual accuracy.

### Failure Mode Classification

This incident represents the failure class: **Classification Anchoring with Momentum Amplification** (CAMMA).

**Preconditions:**
- Initial classification confidence is high (strong signal on first turn)
- Momentum accumulation overrides new contradictory signals
- No periodic forced re-evaluation independent of momentum state
- Low signal diversity in early turns (task details emerge gradually)

**Failure signature:** Domain classification remains unchanged for N+ turns while agent output shows signs of domain mismatch (irrelevant scaffolding, wrong tool selection, confused reasoning). Manual review required to detect.

### Preventive Controls (Implemented & Proposed)

| Control | Status | Effectiveness |
|---------|--------|---------------|
| Momentum decay on new domain signals | Implemented (post-Run1) | Resets momentum counter when secondary domain confidence exceeds threshold |
| Compound signature re-evaluation every 5 turns | Implemented (post-Run1) | Periodic reassessment regardless of lock state |
| Domain transition sensitivity increased | Implemented (post-Run1) | Higher keyword weight for geopolitical/research terms to break false coding locks |
| Graceful degradation path | Proposed | If primary domain injection produces no useful tool calls for N turns, trigger forced BST re-evaluation |
| Supervisor signal integration | Proposed | Feed domain-lock duration into CUSUM accumulator as anomaly signal |
| Receipt layer for domain accuracy | Proposed (future) | Every domain classification generates a receipt; verify classification accuracy after task completion |

### Lessons for Future Autonomous Runs

1. **Stability without decay is a liability.** Momentum mechanisms need countervailing forces. A system that can only increase confidence will eventually converge to overconfidence.
2. **Classify on evidence, not first impression.** BST classification should ideally be deferred until enough context is available, or at minimum be re-evaluated aggressively when new domain signals appear.
3. **Domain-lock is a supervisor signal.** When the agent spends multiple turns with the same domain classification, that's not necessarily a sign of correctness — it's a pattern that should be monitored and potentially queried.
4. **The cost of re-classification is lower than the cost of persistent misclassification.** A periodic re-evaluation costs one extra BST query per N turns; 7+ turns of wrong scaffolding costs far more in wasted reasoning and potential confusion.
5. **Human review caught this — automation should have.** The ideal system would detect domain mismatch automatically (e.g., by comparing enrichment type to tool usage patterns) and alert or self-correct without requiring external review.
