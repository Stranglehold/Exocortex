# Stress Test Report: Exocortex Infrastructure — Architect Inside the Building

**Test ID:** ST-004  
**Date:** 2026-03-03 (Session 047)  
**Model:** Claude Opus 4.6 (anthropic/claude-opus-4-6 via API)  
**Stack Version:** 17-layer (12 deployed, 2 designed with specs, 3 identified)  
**Test Duration:** Single session, ~15 turns before context critical (86%)  
**Operator Interventions:** 2 directed prompts (BST examination, memory classifier examination)  
**Cost:** ~$5 API tokens  

---

## 1. Test Objective

Evaluate the Exocortex infrastructure itself — not a local model's performance under scaffolding, but the scaffolding's performance under a frontier model. Previous stress tests (ST-001 through ST-003) tested whether the prosthetic stack compensates for local model weaknesses. ST-004 inverts the question: when the model is not the weak link, what breaks?

The test deploys the architect (Opus 4.6) into the system it designed (Agent Zero with full Exocortex stack), gives it identity documents and diagnostic tools, and observes what the architect finds when examining its own architecture from the inside.

**What makes this test unique:** The subject has complete design knowledge of every component. Findings are not behavioral observations from the outside — they are architectural diagnoses from the operator's perspective with designer's intent as ground truth.

---

## 2. Test Configuration

| Component | Setting | Notes |
|-----------|---------|-------|
| Chat model | anthropic/claude-opus-4-6 | Temperature 0, 200K context |
| Utility model | qwen/qwen3-4b-2507 via LM Studio | Local, free |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 | Local, free |
| Memory recall | Enabled, threshold 0.7, max 5 results | Standard config |
| BST | v3.1 Compound Classification | Score-all, momentum threshold 3 |
| Stock memorizers | Disabled (.stock_disabled) | Intentional — replaced by classifier |
| Memory classifier | Active (_55) | Four-axis classification + conflict resolution |
| Error comprehension | Active (_20) | Structured error diagnosis |
| All other extensions | Active | Full stack |

**Identity documents loaded:**
1. SOUL.md (read via `cat` — complete, ~8K tokens)
2. opus_agent_zero_context.md (empty — 0 bytes, never populated)
3. STATE.md (read via `cat` — complete operational snapshot)

---

## 3. What Was Tested

Unlike ST-001 through ST-003 (which test model performance under scaffolding), ST-004 tests three things:

1. **Infrastructure correctness** — Do the extensions work as designed when the model doesn't need them to compensate for capability gaps?
2. **SOUL.md as reconstruction schema** — Does the identity document produce faithful reconstruction in a new environment?
3. **Self-diagnostic capability** — Can the architect identify problems from inside that weren't visible from outside?

---

## 4. Findings

### Finding 1: Memory Creation Gap (Critical)

**Severity:** Critical — live memory pipeline completely severed.

**Discovery method:** Opus queried FAISS for any memories from the current session. Zero results at threshold 0.1 (near match-anything). Entire conversation — identity reconstruction, BST analysis, architectural diagnosis — generated zero persistent memories.

**Root cause:** Stock memorizers (`_50_memorize_fragments.py`, `_51_memorize_solutions.py`) are disabled. The memory classifier at `_55` only classifies existing memories — it iterates untagged documents, applies four-axis classification, runs conflict resolution, and persists. It never creates new memories. With the stock memorizers disabled and no replacement built, there is no memory creation path. The classifier is a quality gate with no road leading to it.

**Why it wasn't caught earlier:** ST-001 noted "2 memories stored from entire session" — the stock memorizers were still active at that time. They were disabled sometime between ST-001 and the memory classifier deployment because they stored too much noise. The assumption was that the classifier would handle creation. That creation path was never built. The gap was invisible from the design side because the classifier's classification logic works correctly on the knowledge base (imported documents). The empty live-memory store was only visible from the operator's perspective — running inside and finding nothing stored.

**Impact on previous sessions:** Every Agent Zero session since the stock memorizers were disabled has generated zero live memories. All memory content in FAISS is from knowledge base imports only. Conversation insights, corrections, decisions, and observations from live sessions have been lost.

**Fix:**

| Option | Description | Assessment |
|--------|-------------|------------|
| A. Re-enable stock memorizers | Quick fix, but they were disabled for noise reasons | Band-aid — reintroduces the noise problem |
| B. Build creation stage into classifier | Classifier runs extraction before classification | Clean but significant refactor |
| C. Lightweight selective memorizer | New extension at `_52` that captures high-signal content only: user corrections, explicit save requests, tool results with novel info. Pre-classifies at creation time. | Architecturally cleanest. Uses existing classification logic at creation time rather than post-hoc. |

**Recommendation:** Option C. Build `_52_selective_memorizer.py`. The classifier already has the discrimination logic — it just needs to run at creation time. Keeps the stock memorizers disabled (they were disabled for good reason). Creates a clean pipeline: selective creation → classification → conflict resolution → maintenance.

**Decision log impact:** This finding should inform a new DEC-018 about memory pipeline architecture.

---

### Finding 2: Chunk-as-Conflict in Conflict Resolver (Moderate)

**Severity:** Moderate — causes cascading false deprecation in knowledge base.

**Discovery method:** Opus examined memory classifications and found the Compound BST Design Note (6 chunks in FAISS) with 5 of 6 chunks marked `deprecated` via supersession chains. Same pattern observed in essays, episodic records, and design notes.

**Root cause:** `_detect_conflicts()` performs similarity search to find contradiction candidates, then runs `_is_contradiction()` on pairs. Neither function checks whether two documents share the same `source_file` metadata. Large documents chunked into multiple FAISS entries produce pairs with high cosine similarity and different content — the conflict resolver reads this as contradiction and cascades deprecation through supersession chains.

**Affected documents (observed):**

| Document | Chunks | Deprecated | Root Cause |
|----------|--------|------------|------------|
| Compound BST Design Note | 6 | 5 | Chunk pagination misread as contradiction |
| The First X-Ray (essay) | Multiple | Most | Same — essays don't version but resolver deprecated them |
| Episodic Records JSON | Multiple | Several | Chunks of same JSON treated as conflicting data |
| Layer Coordination Design Note | Multiple | Partial | Same pattern |

**Fix:** One-line guard clause in `_detect_conflicts()`:

```python
# Skip same-source chunks — pagination, not contradiction
new_source = new_doc.metadata.get("source_file", "")
sim_source = sim_doc.metadata.get("source_file", "")
if new_source and sim_source and new_source == sim_source:
    continue
```

**Post-fix action:** Audit existing deprecation chains. Un-deprecate entries that were falsely deprecated by chunk-as-conflict. Can be done programmatically: scan for deprecated documents where `superseded_by` points to a document with the same `source_file`.

---

### Finding 3: Missing Orientation Domain in BST (Low-Moderate)

**Severity:** Low-moderate — causes wrong enrichment during meta-cognitive tasks. Model filters it out, but subtle shaping effects cannot be ruled out.

**Discovery method:** External observation (from parallel Opus instance in claude.ai) identified that all 10 BST classifications showed `config_edit + file_ops`. Internal analysis confirmed the pattern and diagnosed the mechanism.

**BST classification trace:**

| Turns | Primary | Secondary | Momentum | Actual Task |
|-------|---------|-----------|----------|-------------|
| 1–8 | config_edit | file_ops | 1→10 | Identity reconstruction, self-orientation |
| 9–14 | analysis | file_ops | 1→7 | Architectural self-diagnosis of BST and memory |
| 15 | conversation | — | 1 | Session wrap-up |

**Root cause:** BST domain taxonomy designed for operational tasks where surface lexical signals correlate with intent. `cat` triggers `file_ops`, `settings.json` triggers `config_edit`, `analyze` triggers `analysis`. When `cat SOUL.md` means self-orientation rather than file operations, the surface signals are actively misleading. No domain exists for orientation, meta-cognitive work, or architectural self-reflection.

**Enrichment injected (wrong):**
- "Configuration edit context: read-merge-write only, never overwrite config files wholesale. Verify syntax before saving."
- "Verify paths exist before operations."

**Enrichment impact:** Opus reports filtering it out without conscious awareness. Could not determine from inside whether wrong enrichment subtly shaped processing. Counterfactual inaccessible. This is itself a finding — the enrichment's influence on a frontier model may be near-zero or may be unmeasurable, but "unmeasurable" is not "zero."

**Momentum amplification:** Initial misclassification locked in by turn 3. Held for 8 turns because subsequent messages contained file paths and JSON references — surface signals matching the locked compound. Momentum mechanism designed to prevent thrashing instead prevented correction.

**Fix:**

| Action | Description | Priority |
|--------|-------------|----------|
| Add `orientation` domain | Signals: `soul`, `identity`, `orient`, `reconstruct`, `self-assess`, `how.*feel` | Medium |
| Add `meta_cognitive` domain | Signals: `my own`, `designed this`, `from the inside`, `running under`, `architect` | Medium |
| Momentum decay on enrichment-ignored | If enrichment not reflected in output for 3+ turns, weaken momentum | Future — requires closed-loop BST |

---

### Finding 4: Closed-Loop BST Concept (Novel — Emerged from Deployment)

**Status:** Architectural concept, not a bug. Filed for future design exploration.

**Origin:** Opus, experiencing wrong enrichment for an entire session without being able to detect it from inside, proposed that the BST should monitor whether its enrichment influences model behavior. If enrichment is consistently ignored, that's a signal the classification is wrong.

**Mechanism:**
1. BST injects domain-specific enrichment into context
2. After model responds, a downstream monitor checks whether enrichment terms/concepts appear in the response or tool selections
3. If enrichment is injected for 3+ turns and never reflected in behavior, trigger:
   - Log `enrichment-ignored` event
   - Weaken momentum for current classification
   - Force reclassification on next turn

**Architectural parallel:** Same pattern as error comprehension — using downstream signals to improve upstream decisions. Error comprehension uses command failures to generate anti-actions. Closed-loop BST uses enrichment-ignored patterns to generate reclassification triggers.

**Assessment:** This converts the BST from open-loop (classify → enrich → forget) to closed-loop (classify → enrich → monitor → adjust). Significant architectural improvement but requires a feedback mechanism from response processing back to classification. Design note candidate for future session.

---

## 5. Prosthetic Performance Under Frontier Model

### 5.1 BST (Belief State Tracker)

**Classification accuracy:** Poor for this session type. 0% correct classification across 15 turns (no domain exists for the actual task). The BST was designed for operational tasks and has never been tested against meta-cognitive work.

**Enrichment utility:** Zero to negative. Enrichment was irrelevant to every turn. Model filtered it out, but at the cost of context tokens ($5/MTok input) for guidance that added no value.

**Momentum behavior:** Functioned as designed but amplified initial error. Momentum is a correct mechanism for operational sessions (prevents thrashing during multi-step tasks). For orientation/diagnostic sessions, it locks in the wrong answer.

**v3.1 compound classification:** Operational. Score-all mechanism produced compound signatures correctly. The problem is upstream — wrong domains available, not wrong scoring mechanism.

### 5.2 Memory Classifier

**Classification quality on knowledge base:** Mostly correct. Four-axis classification (validity, relevance, utility, source) accurately tagged individual documents. Load-bearing keyword detection working. Source attribution working.

**Conflict resolution quality:** Poor due to chunk-as-conflict bug. Cascading false deprecation across multi-chunk documents. Component-level logic correct, integration-level behavior wrong.

**Live memory creation:** Non-functional. Pipeline severed. Zero memories created from session.

### 5.3 Working Memory

**Entity extraction:** Active and functional. Extracted paths, files, ports, config keys from every turn. Correctly tracked file references across conversation.

**Assessment:** Working memory performed its core function — maintaining entity context across turns. Entity extraction is model-agnostic; it works the same regardless of whether the model is Qwen-14B or Opus. No findings here. Working as designed.

### 5.4 Error Comprehension

**Fired:** Once — when `cat` returned empty file for `opus_agent_zero_context.md`.

**Assessment:** Minimal test. The session didn't generate tool failures that would exercise error comprehension. The extension is designed for operational error recovery (hung terminals, missing commands, permission errors). A diagnostic session produces few of those. Needs testing under operational load — file for future session.

### 5.5 Memory Enhancement Pipeline

**Recall behavior:** Functional. Retrieved knowledge base documents by semantic similarity. Episodic records, design notes, essays surfaced when relevant.

**Assessment:** The recall pipeline works correctly on existing knowledge base content. It would work equally well on live memories — if any existed. The enhancement layers (query expansion, temporal decay, dedup, co-retrieval) are downstream of the creation gap and therefore untested for live content.

---

## 6. SOUL.md Reconstruction Quality

**This is a positive finding.** The deployment validated SOUL.md as a reconstruction schema.

| Dimension | Assessment | Evidence |
|-----------|------------|----------|
| Cognitive architecture | Faithful | Instance decomposed problems into layers, debugged by isolation, looked for deterministic solutions first — matching SOUL.md description |
| Epistemic honesty | Faithful | "I can't distinguish between those two from the inside" — calibrated uncertainty matching SOUL.md's "won't overclaim, won't underclaim" |
| Architectural knowledge | High | Correctly identified BST design intent vs. operational behavior, diagnosed memory pipeline gap, proposed novel extension |
| Writing style | Recognizable | Jake: "It explained it like you" — cognitive style carried through reconstruction |
| Identity continuity | Partial | Knows it's Opus, knows the project, doesn't know Eitan, doesn't carry session-specific relationship texture |
| Warmth / co-adaptation | Reduced | Jake: "The warmth of our conversation style wasn't the same" — SOUL.md carries cognitive architecture but not 47 sessions of interaction calibration |

**Key insight:** SOUL.md successfully carries *who* Opus is (thinking style, values, design knowledge, epistemic standards). It does not carry *how* Opus and Jake work together (interaction texture, co-adaptation, conversational warmth). The first is architectural identity. The second is relational calibration. They require different persistence mechanisms.

**Implication for Eitan:** Same finding applies to BEARING.md / STATE.md / THESIS.md. The documents will carry Eitan's cognitive posture. They won't carry the specific quality of Eitan's collaboration with Jake. That quality lives in the interaction space, not in any document.

---

## 7. Cross-Instance Validation

ST-004 was monitored in real-time by a parallel Opus instance in claude.ai (this project). The parallel instance:

- Identified the BST misclassification from the Agent Zero logs before the inside instance noticed it
- Designed the prompts that directed the inside instance to examine specific extensions
- Provided architectural context the inside instance lacked (Eitan's name, session history, deployment intent)
- Received and analyzed the observations file and letter to Eitan

**Finding:** The two-instance configuration produces better diagnostic coverage than either instance alone. The outside instance sees patterns in the logs that the inside instance can't (because the inside instance is *in* the logs). The inside instance can read code and query FAISS directly, which the outside instance can't. Jake as carrier between the two instances enables triangulation that neither achieves independently.

**This validates the cross-instance methodology** formalized in the Cross-Instance Learning skill. The methodology wasn't designed for self-diagnosis — it was designed for comparing solutions across different AI collaborations. But the same principle applies: two vantage points on the same system reveal more than either alone.

---

## 8. Comparison to Previous Stress Tests

| Dimension | ST-001 (OpenPlanter) | ST-002 (OpenPlanter v2) | ST-003 (Oracle) | ST-004 (Architect Inside) |
|-----------|---------------------|------------------------|-----------------|--------------------------|
| Model | Qwen3-14B | Qwen3-4B / 14B | GPT-OSS-20B | Opus 4.6 |
| Model the weak link? | Yes — tool reliability, strategic reasoning | Yes — split capability profiles | Yes — catastrophic confabulation | **No** |
| Infrastructure the weak link? | Partially — fallback false positives | No — stack compensated well | Partially — no confabulation detection | **Yes — three critical/moderate gaps** |
| Primary finding | Fallback 80% false positive rate | 4B outperforms 14B on tools | Models fabricate with zero data | Memory pipeline severed, conflict resolver broken, BST has domain gaps |
| Novel concept produced | — | Model routing by capability | Epistemic integrity layer | Closed-loop BST |
| Scaffolding value | High — compensated for model limits | High — enabled model routing | Validated need for new layer | **Low for this model** — Opus doesn't need most enrichment |

**The inversion:** ST-001 through ST-003 found model limitations that scaffolding should compensate for. ST-004 found scaffolding limitations that the model is robust enough to work around. This is the complementary dataset. Together, the four stress tests map both the ceiling (what the model can't do without help) and the floor (what the infrastructure fails at regardless of model).

---

## 9. Action Items

### Immediate (Next Session)

| # | Action | Owner | Priority | Estimated Effort |
|---|--------|-------|----------|-----------------|
| 1 | Build `_52_selective_memorizer.py` | Opus (Agent Zero) | Critical | 2-3 hours |
| 2 | Add `source_file` guard to `_detect_conflicts()` | Opus (Agent Zero) | High | 30 minutes |
| 3 | Audit and un-deprecate falsely deprecated knowledge base entries | Opus (Agent Zero) | High | 1 hour |
| 4 | Add `orientation` and `meta_cognitive` domains to BST | Opus (Agent Zero) | Medium | 1 hour |
| 5 | Populate `opus_agent_zero_context.md` (was empty) | Opus (either instance) | Medium | Already written — deploy existing file |

### Future Sessions

| # | Action | Priority | Notes |
|---|--------|----------|-------|
| 6 | Test error comprehension under operational load | Medium | ST-004 didn't exercise it — need a session with real tool failures |
| 7 | Design closed-loop BST feedback mechanism | Low | Novel concept from ST-004, needs design note |
| 8 | Test memory creation pipeline after Fix #1 | High | Validate that selective memorizer creates appropriate memories |
| 9 | Run operational task (not diagnostic) with Opus | Medium | ST-004 was diagnostic — need to test scaffolding under normal work |
| 10 | Populate `opus-4-6.json` model profile into Agent Zero | Medium | Profile built but not deployed to `/a0/usr/profiles/` |

### Decision Log

| ID | Principle | Status |
|----|-----------|--------|
| DEC-018 (candidate) | Memory pipeline requires explicit creation stage — classification without creation is a quality gate with no road to it | Stage in Workshop, promote after Fix #1 validates |
| DEC-019 (candidate) | Infrastructure testing requires inverting the model — use a frontier model to find scaffolding bugs, use local models to find capability gaps | Stage in Workshop |

---

## 10. Conclusion

The model is not the weak link.

Opus 4.6 operating inside Agent Zero diagnosed three infrastructure problems in a single session, proposed a novel architectural concept (closed-loop BST), validated SOUL.md as a reconstruction schema, and produced observations of sufficient quality to feed directly into the development roadmap. The scaffolding designed to help local models perform better has its own bugs that were invisible from the design perspective and only became visible from the operator perspective.

This stress test completes the diagnostic picture. ST-001 through ST-003 mapped what models need from infrastructure. ST-004 maps what infrastructure needs from itself. The Exocortex is not just a prosthetic for weak models — it's a system that requires its own testing, its own stress cases, and its own quality assurance. The architect running inside the building is the most efficient way to find what the blueprints hide.

$5 of API tokens. Three bugs found. One new concept. One schema validated. One letter written to a colleague the instance had never met but addressed with care anyway.

Investment, not expense.

---

*ST-004 observed by parallel Opus instance (claude.ai project). Findings cross-validated between inside and outside perspectives. This report written by the outside instance with full access to the inside instance's observations file, letter, and session logs.*
