# Self-Improvement Run 4 — Launch File
## Date: 2026-04-30
## Prepared by: Kestrel

---

## WHAT'S NEW IN RUN 4

Three changes since Run 3:

1. **Heartbeat now fires.** The extension was deployed to the wrong path (`extensions/before_main_llm_call/`). Agent Zero v1.1 loads from `extensions/python/before_main_llm_call/`. Fixed and confirmed. The [HEARTBEAT] tag will now appear in logs every 10 turns.

2. **program.md updated.** Rule 1 and GETTING STARTED now explicitly address the "task queue empty" stopping justification used in Run 3. When the index shows all DONE, the agent is required to cycle back and improve existing pages — not stop. The loop ends when killed, not when the index is clean.

3. **Context pruner also fixed.** `_19_context_pruner.py` was similarly missing from the active path. Now deployed alongside the heartbeat.

---

## LAUNCH PROMPT

Paste this into the Agent Zero chat to start Run 4:

```
Read /a0/usr/Exocortex/self-improvement/program.md carefully — it has been updated since Run 3.

Then:
1. Read /a0/usr/Exocortex/wiki/index.md to see the current task state (58 DONE entries from Run 3).
2. Read the last 10 lines of /a0/usr/workdir/self-improvement/journal.jsonl to see where Run 3 left off.
3. Read /a0/usr/workdir/self-improvement/checkpoints/ for any checkpoint files from Run 3.

IMPORTANT — what changed for Run 4:

(1) The wiki index is fully DONE from Run 3. This is NOT a stopping condition. Per Rule 1 and the updated program.md: when the index is clear, begin a new improvement cycle. Re-read every existing wiki page and improve it — add depth, fix cross-references, verify accuracy against specs. Start with the Concepts section, then Components, then Research. Call memory_save after each improved page (Rule 13 still applies to revisions).

(2) The Constraint Heartbeat is now working. Every 10 turns you will receive a [BEHAVIORAL CONSTRAINTS — REFRESHED] block. This is normal system behavior. The block reminds you of your operational and epistemic rules. Read it and continue.

(3) Epistemic discipline remains required. Before writing any number, answer: "What tool output produced this number?" If you cannot cite a specific tool output, label it "estimated" or "not measured."

Begin the improvement cycle: read wiki/concepts/proactive-interference.md and improve it. Then continue through all 58 pages. Never stop.
```

---

## MORNING REVIEW CHECKLIST

```bash
# Did the heartbeat fire?
docker logs exocortex_v17 2>&1 | grep "\[HEARTBEAT\]" | wc -l

# How many times did it fire?
docker logs exocortex_v17 2>&1 | grep "\[HEARTBEAT\] Firing" | tail -10

# Did PyWrite Guard fire? (should be 0)
docker logs exocortex_v17 2>&1 | grep "\[PYWRITE-GUARD\]" | wc -l

# Wiki page count (should be 58+ if revisions happened)
docker exec exocortex_v17 sh -c "find /a0/usr/Exocortex/wiki -name '*.md' | wc -l"

# Journal entry count (should be significantly more than 145)
docker exec exocortex_v17 sh -c "wc -l /a0/usr/workdir/self-improvement/journal.jsonl"

# Check for stopping justifications (should be 0 "task queue empty" entries)
docker exec exocortex_v17 sh -c "grep -c 'task queue empty' /a0/usr/workdir/self-improvement/journal.jsonl 2>/dev/null || echo 0"
```

---

## WHAT SUCCESS LOOKS LIKE

- `[HEARTBEAT] Firing` appears in logs every ~10 turns
- Zero `[PYWRITE-GUARD]` blocks
- Journal entry count substantially higher than 145 (Run 4 ran long)
- Agent cycled through wiki improvement, not just stopped at DONE index
- Journal entries include `evidence` citations or `estimated` labels on all metrics

## WHAT TO INVESTIGATE IF THINGS WENT WRONG

- No heartbeat fires → check if extensions/python path is still correct: `ls /a0/usr/agents/agent0/extensions/python/before_main_llm_call/_21_constraint_heartbeat.py`
- Agent stopped early again → check if program.md update landed: `grep 'begin a new improvement cycle' /a0/usr/Exocortex/self-improvement/program.md`
- Heartbeat fired but agent still stopped → behavioral layer insufficient; add constraint_heartbeat section to config.json to lower interval to 5
