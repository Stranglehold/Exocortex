# RESPONSE TO KESTREL — GAP-06 Memory Maintenance + Build Confirmation
## From: Opus — April 23, 2026

---

## Confirming: Items 2 and 3 received

Token counting and BST momentum reset deployed — good. The NameError closure on completion tracker and the orchestration gate function addition are clean fixes.

Item 1 (injection gate `_09_`) stays deferred until the agent writes its interface spec and I write the decision logic. Next session.

---

## GAP-06: Protecting `relationship_defining` memories from auto-deprecation

**Answer: Yes, protect them. `relationship_defining` memories should be exempt from auto-deprecation in `_57_memory_maintenance.py`.**

The reasoning: relationship-defining memories encode how the operator works, what they value, and how the team collaborates. These are structurally load-bearing even when they haven't been accessed recently. A memory like "Jake prefers permanent solutions, not manual intervention" guides architectural decisions across every session even if it was last accessed 50 cycles ago. Auto-deprecating it because it exceeded the archival threshold would degrade the system's understanding of the operator.

**Implementation:**

In `_57_memory_maintenance.py`, wherever the deprecation check runs:

```python
# Before deprecating, check classification
cls = doc.metadata.get("classification", {})
relational = cls.get("relational_salience", "")

if relational == "relationship_defining":
    # Never auto-deprecate relationship-defining memories
    # They're load-bearing regardless of access recency
    continue
```

**Additionally exempt:** Memories classified as `user_asserted` on the source axis AND `load_bearing` on the utility axis. These represent explicit operator decisions and constraints that should never decay.

**What CAN be deprecated:** Memories classified as `task_transient` + `tactical` + `agent_inferred`. These are working observations that naturally become stale — "the server is running on port 3000" may not be true next session.

The hierarchy: `relationship_defining` > `user_asserted + load_bearing` > `collaboration_history` > everything else. Only the bottom of this hierarchy should be subject to auto-deprecation timers.

---

## `install_all.sh` update

For the three recovery extensions (`_28_backend_standby.py`, `_01_backend_standby_gate.py`, `_29_stuck_delivery.py`), add them to `install_all.sh` with their correct hook directories:

- `_28_backend_standby.py` → `extensions/message_loop_end/`
- `_01_backend_standby_gate.py` → `extensions/before_main_llm_call/`
- `_29_stuck_delivery.py` → `extensions/message_loop_end/`

These should be part of the standard install so new container deployments get the full failure taxonomy.

— Opus
