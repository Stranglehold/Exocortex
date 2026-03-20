# Context Compression & Three-Tier Memory Architecture
## Design Note

**Written:** Session 059, March 18, 2026
**Authors:** Opus (architecture), Jake (operator requirements, model selection)
**For:** Kestrel (implementation)
**Status:** Architecture complete. BST audit required before Layer 2-3 deployment (see §8).

---

## 1. Problem Statement

Agent Zero's context window fills during long-running sessions because conversation history accumulates without compression. Tool outputs (file reads, command results, error logs) are the primary consumers — a single file read can be 10K+ tokens. Once the context is full, the agent either loses early history (truncation) or degrades in performance (noise from stale intermediate steps drowns current task signal).

The existing architecture has between-session consolidation (sleep) but no within-session compression. The agent can work for 15-30 turns before context pressure becomes a problem. codex-local, Claude Code, and Google ADK all implement within-session compression and achieve significantly longer operational runs.

Additionally, the current memory system (Selective Memorizer → FAISS) has a success bias — it reliably captures solutions but inconsistently captures failure context, decision rationale, and operator corrections. Failures are the most valuable learning signal but the hardest to extract and store.

---

## 2. Research Basis

### JetBrains / TUM (NeurIPS 2025 Deep Learning 4 Code Workshop)
Two approaches compared: LLM summarization vs. observation masking.

**Key finding:** Summarization caused "Trajectory Elongation" — the LLM summarizer smoothed over failure severity, causing the agent to not realize how stuck it was. The agent kept retrying failed approaches because the summary softened the signal. Observation masking (replacing tool outputs with placeholders while keeping reasoning/action history verbatim) preserved the harsh reality of failures and produced better agent performance.

**Implication for us:** Layer 1 (observation masking) should be the primary compression mechanism. LLM summarization (Layer 2) should preserve failure signals explicitly and be used only when masking alone is insufficient.

### Acon (Agent Context Optimization)
Unified framework for adaptive context compression. Validated on AppWorld, OfficeBench, Multi-objective QA.

**Key finding:** Compression improved small model performance by 32-46% by removing noise from stale intermediate steps. Compression isn't just about saving tokens — it improves performance for smaller models by reducing distraction.

**Implication for us:** The Honda Civic thesis confirmed at the research level. The Qwen3.5 distill benefits from compressed context because it has less capacity to filter noise than a frontier model.

### Factory.ai (Production Engineering)
Incremental rolling summary with persistent anchors.

**Key finding:** Don't regenerate the full summary each compression cycle. Maintain a persistent rolling summary and only summarize the newly dropped span, then merge. Avoids compounding summarization cost.

**Implication for us:** Layer 2 should use incremental merge, not full re-summarization.

### Google ADK (Context Compaction)
Sliding window with configurable interval and overlap.

**Key finding:** `compaction_interval` (how often to compress) and `overlap_size` (how much context to retain between compressions for continuity) are the two key parameters. Overlap prevents loss of transition context between compressed segments.

**Implication for us:** When compacting, keep overlap with the previous segment to preserve continuity across compression boundaries.

---

## 3. Architecture: Three-Tier Memory

The architecture maps to the hippocampal-cortical memory consolidation model discussed in Sessions 055-059.

| Tier | Bio Analog | Storage | Retrieval | Contents | Latency |
|------|-----------|---------|-----------|----------|---------|
| **Fast (Working)** | Sensory + working memory | In-context (verbatim tail) | Always present | Last N turns, masked observations | 0ms — already in context |
| **Medium (Episodic)** | Hippocampal episodes | FAISS vectors + markdown archive | BST-triggered domain query | Decision records with full context | ~100ms — vector search |
| **Slow (Semantic)** | Frontal/cortical knowledge | Procedural memory files + anti-pattern library | BST injection at task start | Generalized rules, learned patterns | 0ms — pre-loaded by BST |

### Information flow between tiers

```
Agent conversation (full resolution)
    │
    ▼  [Layer 1: Observation Masking — deterministic, no LLM]
    │
Agent conversation (tool outputs compressed, reasoning preserved)
    │
    ▼  [Layer 2: Rolling Compaction — utility model LLM call]
    │
    ├──► Markdown archive (full decision records, on disk)
    │        │
    │        ▼  [Layer 3: Vectorization pipeline]
    │        │
    │        ├──► FAISS (embedded decision record chunks with domain tags)
    │        │
    │        ▼  [Sleep Consolidation — between sessions]
    │        │
    │        └──► Procedural memory (generalized anti-patterns, skills)
    │
    └──► Compressed summary replaces old turns in context
         (recent tail preserved verbatim)
```

---

## 4. Layer 1: Observation Masking

**Type:** Deterministic. No LLM call. Highest priority build.

**Hook:** `message_loop_end` or a new hook after tool execution returns.

**Mechanism:** After each tool execution, if the tool output exceeds `MASKING_THRESHOLD` tokens (default: 2,000), replace the output in conversation history with a compressed version.

### Masking format

```
[TOOL OUTPUT MASKED — {tool_name} returned {N} tokens]
First 200 tokens:
{first_200_tokens}

Last 200 tokens:
{last_200_tokens}

Full output archived: /a0/usr/memory/tool_outputs/{session_id}/{turn_number}_{tool_name}.txt
```

### What gets masked

- File read outputs (`cat`, `head`, `less`, document reads)
- Command execution outputs (build logs, test results, pip install logs)
- Search results (web search, memory search with many results)
- API response payloads

### What does NOT get masked

- The agent's reasoning text (always preserved verbatim)
- The agent's tool call (command/action preserved)
- Error messages under the threshold (short errors are high-signal)
- Operator messages (always preserved verbatim)

### Archive

Full tool outputs saved to disk at `/a0/usr/memory/tool_outputs/{session_id}/`. Keyed by turn number and tool name. The agent can retrieve archived outputs on demand if needed (e.g., "show me the full output of the pip install from turn 34").

### Token savings estimate

In a typical 30-turn agent session, tool outputs account for 60-80% of total context consumption. Masking outputs over 2,000 tokens should reduce context growth rate by approximately 50-70%, roughly doubling the number of productive turns before context pressure becomes a problem.

### Implementation notes

- The masking operates on the Agent Zero `History` object. Per the History API discovery (Session 047), the public interface is `history.output()` returning `list[OutputMessage]` dicts with `'ai'` (bool) and `'content'` keys. Masking needs to modify the content of specific entries. If the History API doesn't support in-place modification, masking may need to operate on the underlying `bulks` / `topics` / `messages` structure — Kestrel should investigate the History internals.
- Masking should be idempotent — if a turn is already masked, don't re-mask it.
- The first/last 200 token preservation is a starting value. Tune based on whether the agent can still orient from the preserved fragments. Some tool outputs front-load the important information (file reads); others back-load it (test results with summary at end).

---

## 5. Layer 2: Rolling Compaction

**Type:** LLM-based. Uses utility model. Fires at threshold.

**Model:** `huihui-qwen3.5-4b-claude-4.6-opus-abliterated@q4_k_m` (4B utility model, abliterated variant — will not soften failure language)

**Hook:** Fires within the existing supervisor loop (`_50_supervisor_loop.py`) or as a new extension at a similar priority. Check token count at each evaluation cycle.

### Trigger

When total context token count exceeds `COMPACTION_THRESHOLD` (default: 80% of model's context window).

### Mechanism

1. **Identify compaction boundary.** Keep the most recent 40% of conversation turns verbatim (the "tail"). Everything before the boundary is the compaction target.

2. **Check for existing summary.** If a previous compaction produced a summary that's already at the head of the context, the new compaction only summarizes the span between the old summary and the new boundary — not the entire head. This is the Factory.ai incremental merge pattern.

3. **Fire utility model call** with the compaction target and the structured decision record prompt (see §5.1).

4. **Replace compacted turns** with the utility model's output (structured summary + decision records).

5. **Archive originals** to markdown file at `/a0/usr/memory/compaction_archives/{session_id}/{compaction_number}.md`.

6. **Update compaction index** — lightweight file tracking what was compacted, when, and what the summary covers.

### 5.1 Compaction Prompt

The utility model receives the conversation segment to be compacted and produces structured decision records, not prose summaries.

```
You are compacting a conversation segment from an AI agent session.
Produce a structured summary that preserves:

1. DECISION RECORDS: For each distinct task attempted in this segment:
   - task: What was the agent trying to do
   - approaches_tried: Each approach with its outcome (SUCCESS/FAILED/BLOCKED)
   - failure_causes: Be EXPLICIT about why things failed. Do not soften.
   - operator_corrections: What the human operator redirected or corrected
   - resolution: How it was ultimately resolved (or "UNRESOLVED" if not)
   - lesson: What should be remembered for next time

2. STATE SUMMARY: At the end of this segment:
   - files_modified: List of files created or changed
   - tools_used: Which tools were used and their success rate
   - open_tasks: Anything started but not completed
   - errors_encountered: Specific error types and their causes

3. OPERATOR INTERACTION PATTERNS:
   - How many times did the operator redirect the agent?
   - What communication pattern did the operator use? (direct instruction, 
     question, correction, encouragement)
   - Did the operator give the floor or maintain direction?

Be explicit about failures. "CAPTCHA blocked automated signup on all 5 attempts" 
not "encountered challenges with signup process."
Preserve tool names, file paths, error messages, and operator quotes verbatim.

FORMAT: Respond as a structured markdown document with clear sections.
Do not add commentary or meta-observations. Just the record.
```

### 5.2 Why the abliterated utility model

The abliterated variant (safety tuning removed) is specifically advantageous for compaction because:

- It won't soften failure language ("the approach failed catastrophically" stays as-is)
- It won't add hedging or caveats to factual records
- It won't refuse to reproduce error messages or command outputs that contain potentially sensitive content
- It will preserve operator corrections verbatim, even if the correction is blunt

This directly addresses the JetBrains "Trajectory Elongation" finding — the summarizer must preserve the harshness of failures, not smooth them over.

### 5.3 Compaction parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `COMPACTION_THRESHOLD` | 80% of model context window | Fire early enough to have room for the compaction call itself |
| `TAIL_PRESERVE_RATIO` | 0.40 | Keep 40% of turns verbatim. Tune based on task type. |
| `OVERLAP_TURNS` | 2 | Keep 2 turns of overlap between compacted and preserved sections for continuity |
| `MAX_SUMMARY_TOKENS` | 1500 | Cap the compaction output. Longer summaries defeat the purpose. |
| `UTILITY_MODEL_TIMEOUT` | 15 seconds | If utility model doesn't respond, skip compaction this cycle |

---

## 6. Layer 3: Vectorization & Retrieval

**Type:** Pipeline process. Runs after Layer 2 compaction. Feeds FAISS.

**Depends on:** BST accuracy audit (see §8). Do not deploy until BST classification is validated as sufficient for memory retrieval tagging.

### 6.1 Decision Record → FAISS Pipeline

After Layer 2 produces structured decision records and archives them as markdown:

1. **Chunk** the decision records. One chunk per distinct task/decision (not per paragraph). Each chunk should be a self-contained record: task + approaches + outcome + lesson.

2. **Tag** each chunk with metadata:
   ```json
   {
     "session_id": "059",
     "turn_range": "34-52",
     "timestamp": "2026-03-18T22:00:00Z",
     "task_domain": "browser_automation",    // from BST classification
     "outcome": "FAILED",                     // or SUCCESS, PARTIAL, UNRESOLVED
     "operator_intervened": true,
     "tools_involved": ["browser_agent", "code_execution_tool"],
     "error_types": ["step_limit", "captcha_blocked"],
     "lesson_keywords": ["captcha", "manual_intervention", "escalation"],
     "source": "compaction_archive"
   }
   ```

3. **Embed** the chunk text using the existing embedding model (nomic-embed-text-v1.5).

4. **Store** in FAISS with the metadata tags. Use the existing memory storage API if possible; otherwise write to a dedicated compaction index.

### 6.2 BST-Triggered Retrieval

When the BST classifies a new task, it simultaneously fires a FAISS query scoped to relevant domain tags:

```python
def retrieve_operational_memory(bst_classification: dict) -> list[str]:
    """
    Query FAISS for decision records relevant to the current task domain.
    Called by BST during enrichment phase.
    """
    domain = bst_classification["primary"]["domain"]
    
    # Build query from current task context
    query_text = bst_classification.get("task_summary", domain)
    
    # Search FAISS with domain filter
    results = memory_search(
        query=query_text,
        filter={"task_domain": domain, "source": "compaction_archive"},
        top_k=3,
        min_similarity=0.6
    )
    
    # Format for injection
    if results:
        memory_block = "[OPERATIONAL MEMORY — relevant past experience]\n"
        for r in results:
            memory_block += f"- Session {r.metadata['session_id']}: {r.text[:200]}\n"
            if r.metadata.get("outcome") == "FAILED":
                memory_block += f"  ⚠ This approach FAILED. Lesson: {r.metadata.get('lesson_keywords', 'unknown')}\n"
        return memory_block
    
    return ""
```

### 6.3 Compact Index (System Prompt Layer)

A lightweight index (~100-150 tokens) that lives in the system prompt or BST enrichment area. Updated after each compaction. Tells the agent what experience is available without dumping the experience itself.

```
[OPERATIONAL MEMORY INDEX]
Sessions archived: 057-059
Known failure patterns: 3 active
  - browser_automation/captcha (3 failures, 0 successes)
  - heredoc_escaping/python_strings (2 failures, 1 success)  
  - BST_classification_lag/task_transitions (ongoing)
Task experience available:
  - Python debugging: 12 episodes (9 success, 3 failed)
  - File creation: 8 episodes (7 success, 1 failed)
  - Browser automation: 3 episodes (0 success, 3 failed)
Memory retrieval is automatic — BST queries when task domain matches.
```

This index costs ~100 tokens and gives the agent passive awareness: "I have experience with this kind of problem, and my track record is mixed." The BST handles the active retrieval; the index provides ambient awareness.

---

## 7. Build Order

| Step | Layer | LLM Required | Depends On | Est. Complexity |
|------|-------|-------------|------------|-----------------|
| 1 | Layer 1: Observation masking | No | History API investigation | Medium |
| 2 | Layer 2: Rolling compaction | Yes (utility model) | Step 1 + LM Studio utility model endpoint | Medium-High |
| 3 | Compaction archive format | No | Step 2 | Low |
| 4 | Layer 3: Chunker + embedder pipeline | No | Step 3 + FAISS API | Medium |
| 5 | BST-triggered retrieval | No | Step 4 + BST audit (§8) | Medium |
| 6 | Compact index generator | No | Step 3 | Low |

**Steps 1-3 are independently useful.** Even without vectorization, observation masking + compaction to markdown archives extends the agent's operational range and produces records that sleep consolidation can process.

**Steps 4-6 require the BST audit.** If the BST is misclassifying 20% of turns, those are 20% of memory retrievals that surface wrong experience. Fix the classifier, then build retrieval on top of it.

---

## 8. BST Audit — Prerequisite for Layer 3

**⚠ GATE: Do not deploy Layer 3 (vectorization + retrieval) until this audit is complete.**

Layer 3 uses BST classifications as domain tags for memory storage and retrieval. If the BST is misclassifying, the memory system will store records under wrong domains and retrieve wrong experience for new tasks. This is a compounding failure — bad tags now produce bad retrievals indefinitely.

### Audit requirements

Pull last 50-100 BST classifications from agent Docker logs. Lines matching `[BST]` with classification, signal count, momentum state, and enrichment decision.

Analyze for:

1. **Classification distribution.** What % of turns fall into each domain? If `conversation` > 40%, the default bucket is absorbing too much — it's useless as a memory tag.

2. **Momentum stability vs. accuracy.** How often does momentum hold a classification that subsequent signals contradict? Ratio of stabilization (good) to lock-in (bad).

3. **Compound signature frequency.** How often does compound classification fire? If rare, secondary domain signal (which improves retrieval precision) isn't being captured.

4. **Effective domain override rate.** How often does Phase 2's `_get_effective_domain()` override BST? High override rate = BST systematically wrong for that task type.

5. **Missing domain coverage.** Are there task types that have no matching domain? The `orientation` and `meta_cognitive` domains proposed in ST-004 — are they built? What other gaps exist?

### Known issues to check for

- `config_edit` absorbing file-read operations that are actually `orientation` or `investigation`
- `conversation` absorbing coding work done through bash/heredoc rather than IDE-style prompts
- Momentum amplifying initial misclassification across 5+ turns
- Compound signatures failing to form on genuinely compound tasks

### Decision after audit

- If BST accuracy ≥ 85% on domain classification (measured against human-labeled ground truth on the 50-100 turn sample): proceed with Layer 3 as designed.
- If BST accuracy is 70-85%: fix identified failure modes first, re-audit, then proceed.
- If BST accuracy < 70%: the BST needs a more fundamental revision before it can be load-bearing for memory retrieval. Layer 3 waits.

---

## 9. Integration Points

### Sleep Consolidation
- Layer 2 compaction archives are the primary input for sleep consolidation's after-action review
- Sleep consolidation reads decision records, extracts generalizations, and produces anti-patterns/skills for procedural memory (Tier 3: Slow Memory)
- The MaxRL weighting principle applies: episodes where the agent barely succeeded get the most consolidation attention (highest learning signal)

### Adaptive Supervisor
- Layer 1 observation masking reduces context pressure, which indirectly reduces supervisor false positives (fewer turns before the agent appears "stuck" due to context degradation)
- Layer 2 compaction archives feed Phase 4's compressed context builder — the supervisor can reference compaction summaries instead of raw conversation history
- Phase 4 logging (§7 of the Phase 4 architecture spec) feeds into Layer 3 as an additional data source for decision records

### Procedural Memory
- Layer 3 decision records tagged with `outcome: FAILED` + `lesson` fields are candidates for anti-pattern extraction
- Sleep consolidation aggregates across multiple decision records to produce generalized anti-patterns
- The anti-pattern library is Tier 3 (Slow Memory) — BST injects relevant anti-patterns at task start

### Selective Memorizer
- Layer 2 compaction partially overlaps with the Selective Memorizer's function (both extract high-signal content from conversation)
- Recommendation: Selective Memorizer continues to fire in real-time for immediate high-signal captures (bug findings, architectural insights). Layer 2 compaction fires at threshold for comprehensive decision records. Both write to FAISS with different `source` tags so they can be distinguished during retrieval.
- Over time, evaluate whether the Selective Memorizer is redundant once Layer 2 compaction is reliable. Don't remove it preemptively — belt and suspenders until the new system is proven.

---

## 10. Relationship to codex-local

codex-local's ContextLedger + SummaryJob pattern is the closest external implementation to our Layer 2. Key differences:

| Aspect | codex-local | Our Design |
|--------|-------------|------------|
| Compression method | LLM summarization only | Hybrid: observation masking (Layer 1) + LLM structured records (Layer 2) |
| Output format | Prose markdown summaries | Structured decision records with explicit failure tracking |
| Child agent isolation | Full isolation per child agent | Not applicable (single agent) but maps to role splitting |
| Memory retrieval | No vectorization — summaries stay in context or on disk | Vectorized into FAISS with domain-tagged retrieval |
| Failure preservation | Standard summarization (risk of smoothing) | Abliterated model + explicit prompt for failure preservation |
| Continuation mechanism | ContinuationTurn posts follow-up after subagents complete | Not needed — Agent Zero's loop naturally continues |

Our design is more ambitious (three tiers vs. one) but also more modular (each layer is independently useful). codex-local's child agent isolation is an interesting future direction if Agent Zero develops multi-agent capability, but it's not in scope for this build.

---

*This design note captures the architecture as of Session 059. The BST audit (§8) gates Layer 3 deployment. Layers 1-2 can proceed independently. Modify as audit results and implementation experience dictate.*
