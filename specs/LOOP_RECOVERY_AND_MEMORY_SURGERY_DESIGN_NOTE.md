# Loop Recovery and Memory Surgery — Design Note

**Status:** Research-complete, pre-spec. Motivated by a live session (March 25, 2026) in which
a Qwen3.5-27B agent looped on a Python syntax error for 20+ turns despite repeated corrective
injections, and by the earlier BV Operational Test Suite Session 049 incident in which the same
architecture looped for 43 turns before a container restart broke the cycle in one turn. Research
conducted across six domains: LLM repetition mechanics, agentic framework failure modes,
hierarchical agent architectures, cognitive science (fixation and forgetting), AI memory systems,
and context management in production deployments.

Two problems are addressed jointly because they interact: context surgery alone leaves the agent
vulnerable to re-entering the loop via memory retrieval; memory surgery alone leaves the corrupted
history in place. The complete solution is atomic rollback across both layers simultaneously.

---

## The Problems

### Problem 1: Context surgery is currently incomplete

The supervisor's Tier 2 and Tier 3 actions remove loop turns from conversation history and inject a
replacement summary. This is the right mechanism. Three specific defects exist in the current
implementation:

**Defect A — Wrong incision point.** Surgery cuts at `loop_start_msg_idx` — the first detected loop
turn. Research on agent behavioral drift (arxiv:2601.04170) shows that observable drift precedes
formal detection by several turns. The agent was already in a degenerate state before the first
counted failure. Cutting at the detected start removes the symptom but leaves the onset.

**Defect B — Summary placement.** The replacement summary is injected via `hist_add_warning()`,
which appends to the tail of history. The pre-loop progress context — what was accomplished, what
decisions were made — ends up in the middle of the reconstructed context, between the original
opening and the new post-surgery turns. Research on positional attention bias (Liu et al.,
arxiv:2307.03172, TACL 2024) shows that LLMs attend least reliably to information in the middle
of long contexts, with a U-shaped distribution privileging beginning and end. A surgery summary
placed in the middle is geometrically de-emphasized before it influences token probability.

**Defect C — Summary content primes the failure.** The current Tier 2 message reads: `"[SUPERVISOR
TIER 2 - LOOP SURGERY] N consecutive tool failures removed from context."` The retry count and the
framing of what was removed activates the failure semantic neighborhood. Proactive interference
research (arxiv:2506.08184) establishes that any token semantically adjacent to a failure pattern
primes that pattern's retrieval — the model's behavior shifts toward the failure neighborhood even
when the summary is framed as historical. The summary should acknowledge that surgery occurred
without describing the nature of the failure.

### Problem 2: Context surgery does not address memory contamination

When the agent enters a behavioral loop, the selective memorizer fires at `monologue_end` on each
failed turn. It may write memories encoding the failure pattern ("tried tool X, got error Y,
retrying") to the FAISS store. After context surgery removes the loop turns from conversation
history, those memories persist. On the next turn, memory recall retrieves them as semantically
relevant — they are recent, they match the current task context, and they are numerous (43 entries
from a 43-turn loop represent a dense semantic cluster).

This reinjection of loop-period memories into the agent's fresh context constitutes Einstellung
through the memory layer: the loop is broken in history but re-established in retrieval. No
existing production memory system (MemGPT/Letta, Mem0, A-MEM, Zep/Graphiti, MemoriesDB) addresses
memories written during behavioral loops as a distinct class requiring different handling. This is
a genuine gap in the field.

### Problem 3: Multi-store inconsistency after surgery

Context surgery touches conversation history. Memory contamination touches FAISS. But the agent
also writes to the evidence ledger (`_25_evidence_ledger_recorder.py`) and the ontology layer
during loop turns. After history surgery without corresponding cleanup of these stores, the agent
is in an internally inconsistent state: the conversation no longer contains the loop turns, but the
evidence ledger records them, the ontology may contain loop-period entity writes, and the working
memory buffer may have accumulated loop-related state.

No production multi-agent framework achieves atomic rollback across all these layers. LangGraph's
time-travel checkpoints cover procedural state but explicitly do not roll back vector stores. This
is a documented architectural gap in the field (SagaLLM, arxiv:2503.11951).

---

## The Failure Mechanism (Research Basis)

Understanding why the current interventions don't work is required to design ones that do.

### Why corrective injections fail

The generation lock is not a reasoning failure. It is not that the model reads the correction and
decides to ignore it. Three independent mechanisms prevent corrections from breaking the loop:

**Self-reinforcement** (Zhu et al., arXiv:2310.14971; LoopLLM, arxiv:2511.07876): In autoregressive
decoding, generating a token increases the probability of generating that token again. Once a
pattern is entrained, continuation probability converges toward a ceiling value monotonically. The
LoopLLM study achieved over 90% maximum output length on 12 open-source and 2 commercial LLMs,
confirming this is a universal property of transformer autoregression.

**Positional de-emphasis** (Liu et al., arxiv:2307.03172): Corrective messages injected mid-context
sit in the region of lowest model attention. A warning injected at turn 15 of a 43-turn loop
occupies the most de-emphasized position in the context window. The correction is geometrically
suppressed before it influences token probability — not ignored by reasoning, but structurally
unattended.

**Attention sink amplification** (arxiv:2503.08908; arxiv:2410.10781, ICLR 2025 Spotlight): The
circuit that identifies the first token (attention sink) activates on sequences of repeated tokens.
The model's representation of a repeating pattern is corrupted by the same mechanism that handles
sequence structure under normal conditions. Pathologically high attention weights on repeated tokens
propagate forward, amplifying the locked pattern.

The conclusion is decisive: any intervention that operates by injecting content into the same
looping context is fighting against the model's attention structure. The only effective
interventions are those that break the feedback path: removing the looping context (surgery),
providing a fresh context window (subagent / container restart), or changing the decoding strategy.

### Why the memory layer propagates the loop

**Proactive interference** (arxiv:2506.08184, "Unable to Forget"): Retrieval accuracy declines
log-linearly toward zero as interfering items accumulate. The failure point is abrupt, not gradual.
LLMs lack the "unbinding mechanisms" that allow humans to selectively inhibit competing retrieval
cues. Once "tool X fails" is in the memory store in sufficient density, that pattern cannot be
voluntarily suppressed at retrieval time — the filter must be structural, not semantic.

The failure mode compounds: retrieved loop-period memories are injected into the context, adding
to the interference load, which increases the probability of the model retrieving more loop-period
memories on the next turn, which adds more interference. This is a positive feedback loop in the
memory layer that mirrors the token-level self-reinforcement.

**DRM false memory analog**: After 43 loop turns, the FAISS store contains a dense semantic cluster
in the "tool X failure" neighborhood. On any subsequent task involving that tool, memory recall
will retrieve items from this cluster as highly relevant. The retrieved memories don't just provide
accurate failure information — they prime the entire failure semantic neighborhood. The model
behaves as if it "remembers" failing even when the current situation is genuinely different.

---

## Design Decisions

### Decision 1: Incision point is loop_start_msg_idx - 2

**Rationale:** Agent Drift research shows behavioral change precedes formal detection. Two turns of
lookback buffer is conservative enough to avoid cutting productive pre-drift context while capturing
the onset period. The lookback is bounded at `max(0, loop_start_msg_idx - 2)` to prevent
underflow on early-session loops.

**What this does NOT do:** It does not attempt to detect the true onset of drift algorithmically
(this would require embedding comparison across history, which is too expensive for a synchronous
hook). The fixed 2-turn buffer is a pragmatic approximation of the research finding.

### Decision 2: Summary is inserted at the incision point, not appended

**Rationale:** The replacement summary needs primacy position relative to the new post-surgery
turns. Inserting at `loop_start_msg_idx - 2` in the history list — rather than appending via
`hist_add_warning()` — places it immediately before any new content, giving it both primacy and
recency relative to the post-surgery context.

Implementation: after `del current_topic.messages[incision_idx:]`, insert the summary message
at `current_topic.messages[incision_idx]` (or the end of the now-shortened list). This is a
list insertion, not a hist_add call.

### Decision 3: Surgery summary omits the failure description

**Rationale:** Proactive interference research establishes that any token semantically adjacent to
the failure pattern re-primes that pattern. The summary must acknowledge that surgery occurred
without naming what failed.

**Current (problematic):**
```
[SUPERVISOR TIER 2] 6 consecutive code_execution_tool failures removed from context.
```

**Corrected format:**
```
[SUPERVISOR: CONTEXT SURGERY]
Session intent: {original task from first user message}
Progress before interruption: {successful tool calls, files written, decisions made}
Current state: {last known good state — paths, variables, artifacts established}
Next steps: {planned actions before the loop began}
Note: A repetitive failure sequence has been removed. If the current approach is blocked,
use the response tool to report the obstacle and request guidance.
```

The failing tool name, the error message, and the retry count are absent from the injected
summary. They appear in the supervisor audit log but not in the agent's context. The "Note"
line acknowledges surgery without describing what failed.

**Summary content fields:**
- **Session intent**: extracted from the first non-system user message in the session
- **Progress**: the last N successful tool call outputs before `incision_idx`, trimmed to 200
  chars each, listed as bullet points
- **Current state**: the last working memory snapshot before `incision_idx` (from `_wm_state`
  agent attribute if available; otherwise derived from the last successful tool output)
- **Next steps**: the last agent thought/plan before `incision_idx`, if visible in history

All four fields are derived deterministically from conversation history. No LLM call required.

### Decision 4: loop_period validity value in the memory classifier

**Rationale:** The existing `validity` axis in the memory metadata supports `deprecated` and
`inferred`. Adding `loop_period` as a third validity value is the minimum correct extension. It
slots into the existing retrieval filter with one additional condition:
`validity not in ("deprecated", "loop_period")`.

`loop_period` differs from `deprecated` in intent: `deprecated` marks content superseded by newer
information; `loop_period` marks content written during a failure state of unknown reliability.
Both suppress retrieval. The distinction is preserved for audit, analysis, and sleep-pass promotion.

**Write-time gate in the memory classifier:**

When `self.agent.get_data("_loop_active")` is `True`:

| Memory source | Relational salience | Action |
|---------------|---------------------|--------|
| `user_asserted` | any | Write normally — ground truth, not contaminated |
| `external_retrieved` | any | Write normally — external facts are not loop artifacts |
| `agent_inferred` | `task_transient` | Write with `validity: loop_period` |
| `agent_inferred` | `relationship_defining` | Write normally — relational memories survive loops |
| `agent_inferred` | `collaboration_history` | Write normally |
| `agent_inferred` | utility is `load_bearing` | Write normally — architectural knowledge survives |
| `agent_inferred` | utility is `tactical` | Write with `validity: loop_period` |

The intuition: the loop contaminates episodic/tactical records of what the agent attempted. It
does not contaminate facts about the world (user-asserted, external), facts about relationships
(collaboration), or architectural knowledge about how systems work (load_bearing).

**Required state export from supervisor:**

The supervisor must write two agent attributes when a loop is detected and clear them on recovery:
- `_loop_active: bool` — True while loop_tier != "none"
- `_loop_start_cycle: int` — the agent turn index when the loop began

The memory classifier reads `_loop_active`. The surgery function reads `_loop_start_cycle` to
identify which memories to mark deprecated.

### Decision 5: Write-ahead staging buffer for multi-store rollback

**Rationale:** True atomic rollback across FAISS + conversation history + evidence ledger +
ontology is not achievable in Agent Zero's current architecture without a staging mechanism.
SagaLLM's analysis (arxiv:2503.11951) confirms no production framework solves this cleanly.
The write-ahead log (WAL) pattern from database theory provides a workable approximation.

**Mechanism:**

Each writing extension appends an entry to `self.agent.get_data("_memory_staging_buffer") or []`
at write time. The staging buffer is a list of dicts:

```python
{
    "turn_idx": int,          # agent turn index when written
    "store": str,             # "faiss" | "evidence_ledger" | "ontology"
    "doc_id": str,            # FAISS doc ID, ledger entry ID, or ontology entity ID
    "area": str,              # FAISS area (for FAISS entries)
    "written_at": str,        # ISO timestamp
}
```

The staging buffer is not a gate — writes happen immediately to their respective stores. It is an
audit log that enables the compensating operation (marking entries loop_period or deprecated) when
surgery fires.

**On Tier 2/3 surgery:**

```python
staging = agent.get_data("_memory_staging_buffer") or []
loop_start = agent.get_data("_loop_start_cycle") or 0

for entry in staging:
    if entry["turn_idx"] >= loop_start:
        if entry["store"] == "faiss":
            _mark_faiss_deprecated(agent, entry["doc_id"], entry["area"])
        elif entry["store"] == "evidence_ledger":
            _tag_ledger_loop_period(agent, entry["doc_id"])
        elif entry["store"] == "ontology":
            _tag_ontology_loop_period(agent, entry["doc_id"])
```

The staging buffer is cleared on successful task completion (operator confirms output) or on
session end. It is not cleared by surgery — it is retained as the rollback audit record.

**Failure mode:** if surgery fires but the staging buffer is empty (e.g., the memory classifier
was disabled), surgery proceeds without memory rollback. This is acceptable — history surgery
without memory surgery is better than no surgery. The implementations are independently useful.

### Decision 6: Surgery execution order

The ordering matters for consistency:

1. Record `incision_idx` (`loop_start_msg_idx - 2`) and `loop_start_cycle`
2. Extract summary content from pre-incision history (before deleting)
3. Delete `current_topic.messages[incision_idx:]`
4. Insert replacement summary at `current_topic.messages[incision_idx]`
5. Mark FAISS entries loop_period/deprecated (via staging buffer)
6. Tag evidence ledger loop-period entries (via staging buffer)
7. Tag ontology loop-period entries (via staging buffer)
8. Clear `_loop_active` flag (must happen last — so the memory classifier keeps gating during steps 5-7)

If step 3-4 succeeds and steps 5-7 fail, the agent has a clean history but contaminated stores.
This is preferable to failure before step 3 (no change at all). Log which steps succeeded.

### Decision 7: Sleep consolidation as the adjudication pass

**Rationale:** Real-time classification cannot reliably distinguish "the document does not exist"
(a valid fact discovered during a loop) from "tried document_query 43 times" (a contaminated
episode). The sleep consolidation pass has access to the full session record and can make this
distinction.

During the sleep pass, for all memories with `validity: loop_period`:

1. **Fact extraction**: does the memory assert a verifiable fact about the world (file existence,
   API response, system state)? If yes, promote to `validity: inferred` with loop origin noted in
   lineage. The fact may be true even if the attempt that produced it was part of a loop.

2. **Episode suppression**: does the memory describe the agent's attempt (tried X, failed, retried)?
   Permanently deprecate. This is the contamination content.

3. **Contradiction check**: does the memory contradict a confirmed memory from the same session?
   If yes, deprecate regardless of category.

This is aligned with SleepGate's design (arxiv:2603.14517): adaptive sleep micro-cycles triggered
by conflict density and attention entropy, performing retention scoring on candidate memories before
committing them permanently.

### Decision 8: Recovery verification

Surgery is not self-verifying. Three signals indicate genuine recovery vs. false recovery:

**Immediate (first post-surgery turn):**
- The formerly-failing tool is not called
- The agent's response references the pre-loop progress (summary was attended to)
- Valid JSON response structure (format compliance)

**Short horizon (turns 2-5 post-surgery):**
- Consecutive failure count for the formerly-failing tool stays at 0
- A different tool achieves the blocked objective, OR the agent uses the response tool to escalate

**False recovery detection:**
If the formerly-failing tool is called again within 3 turns of surgery and fails, this is false
recovery — surgery broke the surface loop but not the underlying priming. The supervisor should
skip directly to the next tier rather than waiting for a fresh threshold. The existing
`LOOP_SURGERY_DONE_KEY` and `LOOP_RESET_DONE_KEY` flags prevent repeated same-tier fires but do
not catch the `summarize → none → summarize` re-entry pattern. Detect this pattern explicitly
and escalate directly.

---

## What This Does NOT Do

- **Does not prevent the agent from forming incorrect beliefs.** The memory surgery handles the
  retrieval contamination problem, not the model's internal state. If the model has "learned"
  from the loop turns before surgery fires, the weights are unaffected. Weight-level targeted
  forgetting (Selective Amnesia, NeurIPS 2023) is out of scope and would require model retraining.

- **Does not implement a full subagent for loop diagnosis.** The utility model diagnostic call
  (fast-path classification via the utility model before spawning a full subagent) is described
  in the Adaptive Supervisor design note and is a separate capability. This design note addresses
  context and memory surgery only.

- **Does not achieve true atomic rollback.** The WAL staging buffer approximates atomicity.
  Partial completion (history surgery succeeds, FAISS tagging fails) is possible. This is
  logged and recoverable but not prevented.

- **Does not address loops caused by the agent's responses being malformed** (the `MISFORMAT`
  path in the supervisor). Those are handled by the existing Tier 1 warning injection and are a
  distinct failure class.

- **Does not suppress all loop-period memory writes.** The write-time gate allows user_asserted
  and external_retrieved memories to pass through regardless of loop state. Valid facts discovered
  during a loop (that a file doesn't exist, that an API returns a specific error code) are
  preserved at write time and adjudicated in the sleep pass.

---

## Implementation Scope

| File | Change | Priority |
|------|--------|----------|
| `extensions/message_loop_end/_50_supervisor_loop.py` | Fix incision point (−2 lookback); fix summary placement (insert, not append); fix summary content (remove count and tool name); export `_loop_active` and `_loop_start_cycle` to agent data; add staging buffer drain on Tier 2/3 | High |
| `extensions/monologue_end/_55_memory_classifier.py` | Read `_loop_active` flag; apply write-time gate per source/salience table; add `loop_period` as valid validity value; append to `_memory_staging_buffer` on every write | High |
| `extensions/message_loop_prompts_after/_55_memory_relevance_filter.py` | Add `loop_period` to suppressed validity set (one line) | High |
| `extensions/tool_execute_after/_25_evidence_ledger_recorder.py` | Append to `_memory_staging_buffer` on every write | Medium |
| `sleep_consolidation.py` | Add loop-period adjudication pass: fact extraction, episode suppression, contradiction check | Medium |
| `extensions/before_main_llm_call/_11_working_memory.py` | Review WM state for loop-period contamination on surgery; clear or flag WM entries from loop period | Low |

High-priority items constitute the minimum viable implementation. Medium and low items extend
the atomicity and long-term memory quality.

---

## Research Lineage

**LLM repetition mechanics:**
- Zhu et al., "Penalty Decoding," arXiv:2310.14971, EMNLP 2023
- LoopLLM, arXiv:2511.07876, AAAI 2026
- "Solving LLM Repetition Problem in Production," arXiv:2512.04419
- "Interpreting the Repeated Token Phenomenon," arXiv:2503.08908
- "When Attention Sink Emerges," arXiv:2410.10781, ICLR 2025 Spotlight

**Positional attention and context management:**
- Liu et al., "Lost in the Middle," arXiv:2307.03172, TACL 2024
- Context Rot, Chroma Research, 2025
- Factory.ai context management research (36,611 production messages)

**Agentic frameworks and loop recovery:**
- Shinn et al., Reflexion, 2023
- MAR (Multi-Agent Reflexion), arXiv:2512.20845
- Du et al., Multi-Agent Debate, arXiv:2305.19118
- CRITIC, arXiv:2305.11738
- AutoRefine, arXiv:2601.22758
- LangGraph interrupt mechanism, 2024-2025

**Memory systems:**
- Packer et al., MemGPT/Letta, 2023
- Mem0, arXiv:2504.19413
- Zep/Graphiti, arXiv:2501.13956, VLDB 2025
- A-MEM, arXiv:2502.12110, NeurIPS 2025
- Governed Memory, arXiv:2603.17787
- MemoriesDB, arXiv:2511.06179
- "Unable to Forget" (proactive interference in LLMs), arXiv:2506.08184
- SleepGate / "Learning to Forget," arXiv:2603.14517

**Context surgery and rollback:**
- SagaLLM, arXiv:2503.11951, VLDB 2025
- Git Context Controller, arXiv:2508.00031
- Agent Drift, arXiv:2601.04170
- Levelt (1983), dialogue repair taxonomy
- ACM CUI scoping review on conversational repair, 2024

**Cognitive science:**
- Bilalić, McLeod, Gobet (2008), Einstellung effect in chess
- Tulving (1972), episodic-semantic memory distinction
- Stickgold & Walker (2005), memory reconsolidation
- Deese (1959), Roediger & McDermott (1995), DRM false memory paradigm
- Schacter, memory trace and reconstructive memory

**Multi-store coordination:**
- SagaLLM, arXiv:2503.11951 (Saga pattern for LLM agents)
- Garcia-Molina & Salem (1987), original Saga pattern
- LangGraph checkpoint/time-travel documentation
- AgentOrchestra, arXiv:2506.12508

---

## Open Questions for Opus

1. **Summary content extraction without an LLM call.** The four summary fields (session intent,
   progress, current state, next steps) are derived deterministically from conversation history.
   Is the deterministic extraction sufficient, or does the quality of recovery depend on the
   summary quality enough to justify a utility-model call for summary generation?

2. **Lookback buffer size.** Two turns is a pragmatic choice. The Agent Drift paper's 73-turn
   median drift onset suggests the true onset is often much earlier, but cutting further back
   risks removing legitimate pre-loop context. Is there a better heuristic for incision depth
   than a fixed buffer?

3. **The consolidation gate as long-term architecture.** Writing to a staging buffer and
   committing only in the sleep pass is cleaner than write-time gating with post-hoc rollback.
   The tradeoff: memories written during a session are unavailable for within-session retrieval
   until sleep fires. For multi-session tasks this is acceptable. For single-session tasks that
   conclude before sleep runs, it means no memories are written at all. Is this acceptable?

4. **Working memory and the loop.** The working memory buffer (`_11_working_memory.py`) may have
   accumulated loop-related state. The design note flags it as low-priority. Is this correct, or
   does WM contamination represent a distinct failure path that should be addressed at high
   priority alongside FAISS?

5. **False recovery threshold.** The design specifies escalating directly if the formerly-failing
   tool fails again within 3 turns of surgery. Is 3 turns the right window? Too tight and it
   fires on genuine retries after a different approach; too loose and re-entrant loops accumulate
   damage before detection.

---

*Design note authored by Kestrel, March 25, 2026. Research conducted in collaboration with Jake.
For architectural review by Opus before spec and implementation.*
