# Loop Recovery and Memory Surgery — Implementation Spec L3

**Status:** Ready to build. Design decisions resolved by Opus review (March 25, 2026).
**Design note:** `LOOP_RECOVERY_AND_MEMORY_SURGERY_DESIGN_NOTE.md`
**Priority:** High items implement the minimum viable recovery system. Medium items extend atomicity.

---

## Overview

Five files. Three high-priority, two medium. Each section gives the precise change — what to find,
what to add, what to remove. No design decisions are left to the implementer. All architectural
questions were resolved in the design note and Opus review.

No LLM calls in any of these changes. All logic is deterministic.

---

## File 1 — `_50_supervisor_loop.py` (High Priority)

**Location:** `extensions/message_loop_end/_50_supervisor_loop.py`
**Pattern source:** Existing `_execute_tier2` and `_execute_tier3` functions (lines ~940–1040).

### Change 1A — Export loop state to agent data

The memory classifier and evidence ledger recorder need to know when a loop is active. Currently
the supervisor keeps this state internal to `state` dict. Add two agent data writes in
`_write_loop_signals()`.

Find `_write_loop_signals` (line ~1043). At the **end** of the function body, before the closing
`except`, add:

```python
# Export loop state for downstream hooks (memory classifier, evidence ledger)
try:
    is_active = (consecutive >= thresholds.get("tier1", 3)) if thresholds else (consecutive >= 3)
    agent.set_data("_loop_active", is_active)
    if is_active:
        loop_start = state.get(LOOP_START_IDX_KEY, 0)
        if agent.get_data("_loop_start_cycle") is None:
            agent.set_data("_loop_start_cycle", loop_start)
except Exception:
    pass
```

Add the corresponding clear in the loop-recovery branch. Find `_clear_loop_episode` (the function
called when `old_loop_tier != "none" and new_loop_tier == "none"`). At the end of that function:

```python
agent.set_data("_loop_active", False)
agent.set_data("_loop_start_cycle", None)
```

### Change 1B — Fix incision point in `_execute_tier2` and `_execute_tier3`

Both functions currently cut at `loop_start_idx` (the detected loop start). Change to
`loop_start_idx - 2` with a floor of 0.

In `_execute_tier2`, replace:
```python
loop_start_idx = state.get(
    LOOP_START_IDX_KEY,
    max(0, len(current_topic.messages) - consecutive * 2)
)
removed_count = max(0, len(current_topic.messages) - loop_start_idx)
if removed_count > 0:
    del current_topic.messages[loop_start_idx:]
```

With:
```python
loop_start_raw = state.get(
    LOOP_START_IDX_KEY,
    max(0, len(current_topic.messages) - consecutive * 2)
)
incision_idx = max(0, loop_start_raw - 2)  # -2 lookback: drift precedes detection
removed_count = max(0, len(current_topic.messages) - incision_idx)
if removed_count > 0:
    del current_topic.messages[incision_idx:]
```

Apply the **identical change** in `_execute_tier3`, replacing `loop_start_idx` with `incision_idx`
using the same pattern.

### Change 1C — Fix summary content and placement in `_execute_tier2`

The current summary names the failing tool and retry count, re-priming the failure semantic
neighborhood. The summary is also injected via `hist_add_warning()` (appended to tail) instead of
inserted at the incision point.

Replace the entire summary construction and injection block in `_execute_tier2`:

```python
# ── Build recovery summary (omit failure description — prevents re-priming) ──
session_intent = _extract_session_intent(agent)
progress       = _extract_pre_loop_progress(agent, incision_idx)
current_state  = _extract_current_state(agent)

summary_lines = [
    "[SUPERVISOR: CONTEXT SURGERY]",
    f"Session intent: {session_intent}",
    f"Progress before interruption: {progress}",
    f"Current state: {current_state}",
    "Note: A repetitive failure sequence has been removed from context. "
    "If the current approach is blocked, use the response tool to report "
    "the obstacle and request guidance.",
]

# Add error class from EC if available (no tool name, no count)
try:
    ec = agent.get_data("_error_diagnosis") or {}
    if ec.get("confidence", 0) > 0.6 and ec.get("error_class"):
        summary_lines.append(f"Error class detected: {ec['error_class']}.")
        anti = ec.get("anti_actions", [])
        if anti:
            summary_lines.append(f"Do NOT: {anti[0]}.")
except Exception:
    pass

summary = "\n".join(summary_lines)

# ── Insert at incision point (primacy position) rather than appending ─────────
try:
    from python.helpers.history import HistoryMessage
    summary_msg = HistoryMessage(content=summary, ai=False)
    current_topic.messages.insert(incision_idx, summary_msg)
except Exception:
    # Fallback: append if insertion fails
    agent.hist_add_warning(summary)
```

Remove the old `agent.hist_add_warning(summary)` call that follows the existing summary
construction.

### Change 1D — Add three summary extraction helpers

Add these three functions immediately above `_execute_tier2`:

```python
def _extract_session_intent(agent) -> str:
    """Extract the original task from the first non-system user message."""
    try:
        msgs = agent.history.current.messages
        for msg in msgs:
            if getattr(msg, "ai", True):
                continue
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            if content and not content.startswith("[SUPERVISOR"):
                return content[:200].replace("\n", " ")
    except Exception:
        pass
    return "task not recoverable"


def _extract_pre_loop_progress(agent, incision_idx: int) -> str:
    """Summarize successful tool calls before the incision point."""
    try:
        msgs = agent.history.current.messages
        pre_loop = msgs[:incision_idx]
        successes = []
        for msg in reversed(pre_loop[-10:]):  # last 10 pre-loop messages
            if not getattr(msg, "ai", False):
                continue
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            # Include AI messages that aren't supervisor warnings
            if content and not content.startswith("[SUPERVISOR"):
                successes.append(content[:150].replace("\n", " "))
                if len(successes) >= 3:
                    break
        if successes:
            return "; ".join(reversed(successes))
    except Exception:
        pass
    return "no progress record available"


def _extract_current_state(agent) -> str:
    """Extract working memory state if available, else return brief placeholder."""
    try:
        wm = agent.get_data("_wm_state")
        if wm and isinstance(wm, dict):
            parts = []
            if wm.get("objective"):
                parts.append(f"objective: {str(wm['objective'])[:100]}")
            if wm.get("entities"):
                ents = list(wm["entities"])[:3]
                parts.append(f"entities: {', '.join(str(e) for e in ents)}")
            if parts:
                return "; ".join(parts)
    except Exception:
        pass
    return "working memory not available"
```

### Change 1E — Add staging buffer drain on surgery

At the **end** of `_execute_tier2` (before the outer `except`), after the summary is injected,
add the memory surgery call:

```python
# ── Multi-store rollback via staging buffer ──────────────────────────────────
try:
    _drain_staging_buffer(agent)
except Exception as e:
    agent.context.log.log(
        type="warning",
        content=f"[SUPERVISOR] Staging buffer drain failed (history surgery still applied): {e}",
        flush=True,
    )
```

Apply the **same call** at the end of `_execute_tier3`.

Add this helper above `_execute_tier2`:

```python
def _drain_staging_buffer(agent):
    """
    Mark all staging-buffer entries from the loop period as loop_period validity.
    Called by Tier 2 and Tier 3 surgery. Operates on FAISS and evidence ledger.
    """
    staging = agent.get_data("_memory_staging_buffer") or []
    loop_start_cycle = agent.get_data("_loop_start_cycle") or 0
    if not staging or not loop_start_cycle:
        return

    import asyncio
    from python.helpers.memory import Memory

    affected = [e for e in staging if e.get("turn_idx", 0) >= loop_start_cycle]
    if not affected:
        return

    async def _mark():
        try:
            db = await Memory.get(agent)
            all_docs = db.db.get_all_docs() if hasattr(db, "db") else {}
            changed = False
            for entry in affected:
                if entry.get("store") == "faiss":
                    doc = all_docs.get(entry["doc_id"])
                    if doc and hasattr(doc, "metadata"):
                        cls = doc.metadata.get("classification", {})
                        if cls.get("validity") not in ("deprecated",):
                            cls["validity"] = "loop_period"
                            doc.metadata["classification"] = cls
                            changed = True
                elif entry.get("store") == "evidence_ledger":
                    ledger = agent.get_data("_evidence_ledger") or {}
                    for e in ledger.get("entries", []):
                        if e.get("_staging_id") == entry["doc_id"]:
                            e["loop_period"] = True
            if changed:
                db.db._save_db()
        except Exception as e:
            print(f"[SUPERVISOR] _drain_staging_buffer inner error: {e}", flush=True)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_mark())
        else:
            loop.run_until_complete(_mark())
    except Exception as e:
        print(f"[SUPERVISOR] _drain_staging_buffer dispatch error: {e}", flush=True)

    agent.context.log.log(
        type="info",
        content=f"[SUPERVISOR] Staging buffer drain: {len(affected)} entries tagged loop_period",
        flush=True,
    )
```

### Change 1F — False recovery detection

Find the loop-resolution handling (where `old_loop_tier != "none" and new_loop_tier == "none"`).
After the episode-clear logic, add:

```python
# Track most-recent surgery tool for false recovery detection
if old_loop_tier in ("summarize", "reset"):
    agent.set_data("_post_surgery_tool", state.get(LOOP_TOOL_KEY))
    agent.set_data("_post_surgery_turn", 0)
```

In `_write_loop_signals`, increment the post-surgery turn counter if set:

```python
post_tool = agent.get_data("_post_surgery_tool")
if post_tool:
    turn = (agent.get_data("_post_surgery_turn") or 0) + 1
    agent.set_data("_post_surgery_turn", turn)
    # If the formerly-failing tool fails again within 3 turns, skip directly to Tier 3
    if turn <= 3 and failing_tool == post_tool and consecutive >= 1:
        agent.context.log.log(
            type="warning",
            content=f"[SUPERVISOR] False recovery detected: {post_tool} failed again within {turn} turns of surgery. Escalating directly.",
            flush=True,
        )
        # Force skip to Tier 3 threshold
        state[LOOP_TIER_KEY] = "reset"
        state.pop(LOOP_SURGERY_DONE_KEY, None)
    elif turn > 3:
        agent.set_data("_post_surgery_tool", None)
        agent.set_data("_post_surgery_turn", None)
```

---

## File 2 — `_55_memory_classifier.py` (High Priority)

**Location:** `extensions/monologue_end/_55_memory_classifier.py`
**Pattern source:** `_classify()` function (line ~241) and Phase 1 classify loop (line ~139).

### Change 2A — Add `loop_period` to the classify function

In `_classify()`, after the `source` is determined and before the return, add a loop-state check:

```python
# ── Loop-period gate ─────────────────────────────────────────────────────────
# If a behavioral loop is active, tag tactical agent-inferred memories as
# loop_period so they are suppressed at retrieval but preserved for audit.
loop_validity = None
if agent_is_looping:  # passed as parameter — see Change 2B
    if source not in ("user_asserted", "external_retrieved"):
        if utility == "load_bearing":
            pass  # load_bearing survives regardless
        elif relational_salience in ("relationship_defining", "collaboration_history"):
            pass  # relational anchors survive
        else:
            loop_validity = "loop_period"

return {
    "validity": loop_validity if loop_validity else validity,
    "relevance": relevance,
    "utility": utility,
    "source": source,
}
```

Update the `_classify()` signature to accept `agent_is_looping`:

```python
def _classify(doc, user_msg: str, config: dict, agent_is_looping: bool = False) -> dict:
```

You will also need `relational_salience` — this axis does not yet exist. For this implementation,
derive it from `utility` as a proxy:
- If `utility == "load_bearing"`: treat as `relationship_defining`
- If `utility == "tactical"` and source == "agent_inferred": treat as `task_transient`
- Otherwise: treat as safe (write normally)

This is a simplification of the full source/salience matrix from the design note. It is correct
for the common case. A future spec can add explicit `relational_salience` classification.

### Change 2B — Pass loop state into the classify call

In the Phase 1 loop (line ~139), read the loop state before iterating and pass it to `_classify`:

```python
# Read loop state once for this classifier run
agent_is_looping = bool(self.agent.get_data("_loop_active"))

for doc_id, doc in all_docs.items():
    if not hasattr(doc, "metadata"):
        continue
    if CLS_KEY in doc.metadata:
        continue  # Already classified

    doc.metadata[CLS_KEY] = _classify(doc, user_msg, config, agent_is_looping)
    doc.metadata[LIN_KEY] = _new_lineage(
        role_id, bst_domain, maint_cycle,
    )
    newly_classified.append((doc_id, doc))
```

### Change 2C — Append to staging buffer on every classify

After `newly_classified.append((doc_id, doc))`, add:

```python
# Staging buffer: record this write for potential surgery rollback
try:
    staging = self.agent.get_data("_memory_staging_buffer") or []
    loop_cycle = self.agent.get_data("_loop_start_cycle") or 0
    staging.append({
        "turn_idx": maint_cycle,
        "store": "faiss",
        "doc_id": doc_id,
        "area": doc.metadata.get("area", ""),
        "written_at": datetime.now(timezone.utc).isoformat(),
    })
    self.agent.set_data("_memory_staging_buffer", staging)
except Exception:
    pass
```

---

## File 3 — `_55_memory_relevance_filter.py` (High Priority)

**Location:** `extensions/message_loop_prompts_after/_55_memory_relevance_filter.py`
**Pattern source:** `_filter_and_rank()` function, validity filter block (line ~209).

### Change 3A — Suppress `loop_period` memories at retrieval

Find the validity filter block in `_filter_and_rank()`:

```python
# ── Validity filter: exclude deprecated ──────────────────────────────────
if cls.get("validity") == "deprecated":
    continue
```

Change to:

```python
# ── Validity filter: exclude deprecated and loop_period memories ──────────
if cls.get("validity") in ("deprecated", "loop_period"):
    continue
```

That is the complete change to this file. One additional string in the exclusion set.

---

## File 4 — `_25_evidence_ledger_recorder.py` (Medium Priority)

**Location:** `extensions/tool_execute_after/_25_evidence_ledger_recorder.py`
**Pattern source:** `execute()` function, entry construction (line ~62).

### Change 4A — Tag loop-period entries and append to staging buffer

In the `execute()` method, after `entry` is constructed and before `ledger["entries"].append(entry)`,
add:

```python
# Tag if written during an active loop
if self.agent.get_data("_loop_active"):
    entry["loop_period"] = True

# Assign a staging ID for rollback cross-reference
import uuid
staging_id = str(uuid.uuid4())[:8]
entry["_staging_id"] = staging_id
```

After `self.agent.set_data(LEDGER_KEY, ledger)`, add:

```python
# Staging buffer: record this write for potential surgery rollback
try:
    if self.agent.get_data("_loop_active"):
        staging = self.agent.get_data("_memory_staging_buffer") or []
        staging.append({
            "turn_idx": len(ledger["entries"]) - 1,
            "store": "evidence_ledger",
            "doc_id": staging_id,
            "written_at": entry["ts"],
        })
        self.agent.set_data("_memory_staging_buffer", staging)
except Exception:
    pass
```

---

## File 5 — `sleep_consolidation.py` (Medium Priority)

**Location:** `/a0/usr/Exocortex/sleep_consolidation.py` (and repo copy)
**Pattern source:** Existing Phase 1 and Phase 2 consolidation logic.

### Change 5A — Add loop-period adjudication pass

Add a new function `_adjudicate_loop_period_memories(agent, db, all_docs)` to be called during
the sleep pass after Phase 2 (episode chunking):

```python
def _adjudicate_loop_period_memories(agent, db, all_docs):
    """
    Review all loop_period memories and promote or deprecate each.

    Logic per memory:
    - Contains verifiable fact assertion (file exists/not, API response, system state):
        → promote to validity: inferred, add lineage note
    - Describes agent attempt/retry (tried X, failed, retried):
        → deprecate permanently
    - Contradicts a confirmed memory from the same session:
        → deprecate regardless of category
    - Cannot be classified:
        → leave as loop_period (retrieval still suppressed; human review on next sleep)
    """
    FACT_PATTERNS = [
        re.compile(r"\b(exists?|found|not found|missing|present|absent)\b", re.IGNORECASE),
        re.compile(r"\b(error|returns?|responded?|status)\s+\d{3}\b", re.IGNORECASE),
        re.compile(r"\b(file|path|directory|endpoint)\b.{0,40}\b(exists?|not found|missing)\b", re.IGNORECASE),
    ]
    ATTEMPT_PATTERNS = [
        re.compile(r"\b(tried?|attempt|retry|retried|trying)\b", re.IGNORECASE),
        re.compile(r"\b(failed?|failing)\s+(again|repeatedly|multiple)\b", re.IGNORECASE),
        re.compile(r"\bconsecutive\b", re.IGNORECASE),
    ]

    changed = 0
    for doc_id, doc in all_docs.items():
        if not hasattr(doc, "metadata"):
            continue
        cls = doc.metadata.get("classification", {})
        if cls.get("validity") != "loop_period":
            continue

        text = getattr(doc, "page_content", "")

        is_attempt = any(p.search(text) for p in ATTEMPT_PATTERNS)
        is_fact    = any(p.search(text) for p in FACT_PATTERNS)

        if is_attempt and not is_fact:
            cls["validity"] = "deprecated"
            doc.metadata["classification"] = cls
            changed += 1
        elif is_fact and not is_attempt:
            cls["validity"] = "inferred"
            lin = doc.metadata.get("lineage", {})
            lin["loop_period_promoted"] = True
            doc.metadata["lineage"] = lin
            doc.metadata["classification"] = cls
            changed += 1
        # else: ambiguous — leave as loop_period for next sleep pass

    if changed:
        try:
            db.db._save_db()
        except Exception:
            pass

    print(f"[SLEEP] Loop-period adjudication: {changed} memories promoted or deprecated", flush=True)
    return changed
```

Call this function in the sleep consolidation entry point, after Phase 2:

```python
# Phase 3: Loop-period memory adjudication
try:
    _adjudicate_loop_period_memories(agent, db, all_docs)
except Exception as e:
    print(f"[SLEEP] Loop adjudication error: {e}", flush=True)
```

---

## Deployment Sequence

Build and test in this order. Each step is independently deployable and testable.

**Step 1 — Relevance filter (File 3, one-line change)**
- Lowest risk, immediately effective
- Deploy, send any message, confirm `[MEM-FILTER]` logs don't show `loop_period` memories injected
- No loop needed to verify — just confirm the filter compiles and runs

**Step 2 — Memory classifier gate (File 2)**
- Deploy, trigger a loop (or set `_loop_active = True` manually via the agent), check that new
  memories receive `loop_period` validity in the FAISS store
- Log tag: `[MEM-CLASS]` should show `loop_period` entries when `_loop_active` is True

**Step 3 — Supervisor surgery fixes (File 1)**
- Deploy all changes together (1A through 1F are interdependent)
- Verify:
  - `_loop_active` appears in agent data when a loop is detected
  - Tier 2 fires, history is trimmed to `loop_start - 2`
  - Summary is inserted at the incision point (not appended to tail)
  - Summary does not contain the tool name or retry count
  - `[SUPERVISOR] Staging buffer drain` appears in logs on Tier 2 fire
- Log tag: `[SUPERVISOR]` with "Tier 2 surgery" and "Staging buffer drain"

**Step 4 — Evidence ledger (File 4)**
- Deploy, trigger a loop, check that ledger entries from loop turns have `loop_period: True`
- Verify staging buffer receives entries from the ledger recorder

**Step 5 — Sleep consolidation (File 5)**
- Deploy, trigger a loop, let sleep run, verify `[SLEEP] Loop-period adjudication` appears
- Confirm attempt-pattern memories are deprecated; fact-pattern memories are promoted to inferred

---

## Verification Checklist

After full deployment, a complete loop recovery test:

1. **Trigger a loop** — give the agent a task using a broken tool (or a tool with wrong parameters)
2. **Confirm detection** — `[SUPERVISOR] Tier 2 surgery` appears in logs
3. **Check incision** — history should be shorter by `(detected_loop_start - 2 + loop_turns)` messages
4. **Check summary** — summary message does NOT contain the tool name or retry count
5. **Check summary position** — summary is NOT the last message; new agent turns follow it
6. **Check FAISS** — loop-period memories have `validity: loop_period`, not `inferred`
7. **Check retrieval** — `[MEM-FILTER]` logs do NOT show loop-period memories injected
8. **Check recovery** — agent does not call the formerly-failing tool on the first post-surgery turn
9. **Check ledger** — loop-turn ledger entries have `loop_period: True`
10. **Check false recovery guard** — if the formerly-failing tool fails again within 3 turns, Tier 3 fires without waiting for the normal threshold

---

## What NOT to Do

- **Do not** make the summary generation call an LLM call. Deterministic extraction is sufficient
  and keeps this hook synchronous. The Opus review confirmed: geometric placement matters more
  than prose quality.
- **Do not** gate memory writes in a staging buffer (defer-then-commit). Writes happen immediately
  to FAISS. The staging buffer is an audit log for rollback, not a write gate.
- **Do not** change the `_VALIDITY_RANK` dict in the memory classifier — `loop_period` memories
  are not ranked against each other; they are suppressed at retrieval entirely.
- **Do not** add `loop_period` to the conflict resolution logic. Conflicts among loop-period
  memories don't need resolution — they're all suppressed at retrieval and adjudicated in sleep.
- **Do not** implement the full `relational_salience` classification axis in this spec. Use the
  `utility == "load_bearing"` proxy for now. A future spec adds the full axis.

---

*Spec authored by Kestrel, March 25, 2026. Implements decisions from*
*`LOOP_RECOVERY_AND_MEMORY_SURGERY_DESIGN_NOTE.md` as resolved by Opus review.*
