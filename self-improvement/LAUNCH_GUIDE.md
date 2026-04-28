# LAUNCH GUIDE — Exocortex Self-Improvement Loop
## April 27, 2026

---

## Prerequisites

1. **Agent Zero running** with Exocortex v17 profile
2. **Qwen3.6-27B loaded** in LM Studio (or inference wrapper) at 100k context
3. **MCP servers active:** ArXiv, DuckDuckGo, Wikipedia, Context7, DeepWiki, Memory
4. **Container has the latest Exocortex files** including:
   - `self-improvement/program.md`
   - `wiki/` directory structure with WIKI.md and index.md
   - `specs/EXOCORTEX_WIKI_SPEC.md`
   - `specs/RECURSIVE_SELF_IMPROVEMENT_ENGINE.md`
   - All research reports in `research/`

## How to Start

### Step 1: Verify the self-improvement directory is in the container

```
ls /a0/usr/Exocortex/self-improvement/
# Should see: program.md, backups/, checkpoints/
```

If not present, the Exocortex profile mount needs to include these new directories.

### Step 2: Give the agent the instruction

In the Agent Zero chat, paste this:

```
Read the file at /a0/usr/Exocortex/self-improvement/program.md carefully. 
This is your operating manual for a self-improvement loop.

Follow the GETTING STARTED section:
1. Create the journal file at /a0/usr/workdir/self-improvement/journal.jsonl
2. Run all 5 test tasks under current configuration to establish baseline
3. Record baseline metrics in checkpoints/baseline.md
4. Then begin the improvement loop starting with Priority 1 (Knowledge Building)

Run autonomously. Follow the program. Log everything. Do not stop.
```

### Step 3: Monitor

- **NERV Dashboard:** Shows generation activity (is the agent working?)
- **Agent Zero UI:** Shows the agent's reasoning and tool calls
- **Journal:** Check `/a0/usr/workdir/self-improvement/journal.jsonl` periodically
- **Checkpoints:** Check `/a0/usr/workdir/self-improvement/checkpoints/` every 10 experiments

### Step 4: Morning Review

When you wake up, check:

1. **How many experiments ran?** 
   ```
   wc -l /a0/usr/workdir/self-improvement/journal.jsonl
   ```

2. **What was the win/loss ratio?**
   ```
   grep -c '"decision": "COMMIT"' journal.jsonl
   grep -c '"decision": "ROLLBACK"' journal.jsonl
   ```

3. **Were any circuit breakers hit?**
   ```
   ls /a0/usr/workdir/self-improvement/checkpoints/circuit_breaker_*
   ```

4. **What wiki pages were created?**
   ```
   ls /a0/usr/Exocortex/wiki/concepts/
   ls /a0/usr/Exocortex/wiki/components/
   ls /a0/usr/Exocortex/wiki/research/
   ```

5. **Were any skills auto-generated?**
   ```
   ls /a0/usr/skills/auto-generated/
   ```

## What to Expect

### First Night (Knowledge Building + Research)

The agent should:
- Read all design notes and research reports
- Create 5-10 wiki pages (concepts + research summaries)
- Search the internet for 3-5 relevant techniques
- Document findings in the wiki
- Run test tasks to establish baselines

**Expected output:** 10-20 experiments logged, 5-10 wiki pages, 1-3 research findings

### Subsequent Nights (Deeper Research + Configuration)

The agent should:
- Go deeper on promising research directions
- Test configuration changes against baselines
- Generate skills from successful workflows
- Identify and document gaps

## Stopping

Kill the Agent Zero task or close the chat. The agent respects the circuit breakers — if something goes wrong, it'll pause itself and write a diagnostic.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agent stops after a few experiments | Check for circuit breaker file. May have hit 3 consecutive failures. |
| Context overflow | The injection gate should prevent this at 100k. If it happens, check that gate is active. |
| Agent modifies .py files | The action boundary should block this. Check action_boundary config. |
| No wiki pages created | Agent may be stuck on baseline measurement. Check journal for what it's doing. |
| Journal file empty | Agent may not have found program.md. Verify the file is in the container. |
