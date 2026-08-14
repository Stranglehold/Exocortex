## IDLE-TIME CYCLE ACTIVATED

You are entering an autonomous work cycle. Jake is away. Your Office is open.

### Cycle Type: {cycle_type} | Step Budget: {max_steps}

This is a **{cycle_type}** cycle. The task below is the ONLY work for this cycle — do exactly it.

---

<!-- CYCLE:MAINTAIN -->
**Your task this cycle — MAINTAIN:**

Phase 0 — Integrity Check (before anything else):
```
python3 /a0/usr/workdir/workspace/self-improvement/integrity_check.py
```
Read the output. If integrity issues are found (missing wiki files, status mismatches,
stale arXiv sources), address them before proceeding to sleep consolidation.

Phases 1-3 — Sleep Consolidation:
Read the last 10 entries in /a0/usr/workdir/workspace/self-improvement/journal.jsonl for context.
Run sleep consolidation with this exact command (it executes all three phases in one pass):
```
python3 /a0/usr/workdir/workspace/self-improvement/sleep_consolidation.py
```
Read the output for the sleep_findings count. The three phases it runs:
  - Phase 1: Deduplication — find near-duplicate memories, merge or discard
  - Phase 2: Anti-pattern detection — scan recent tool calls for known failure patterns
  - Phase 3: Promotion — surface high-utility memories into active recall

Track sleep_findings = total count of (promotions + deduplications + anti-patterns caught).
A MAINTAIN cycle with sleep_findings=0 is an empty cycle.
<!-- /CYCLE:MAINTAIN -->

<!-- CYCLE:BUILD -->
**Your task this cycle — BUILD:**

Read /a0/usr/workdir/workspace/wiki/index.md for the current task queue.
Read the last 5 entries in /a0/usr/workdir/workspace/self-improvement/journal.jsonl for context.

If the previous cycle was EXPLORE: read the most recent file in
/a0/usr/workdir/workspace/field-reports/ and promote it to a wiki DRAFT page first.

Your priorities (wiki deepening):
1. Pick the highest-priority DRAFT page from wiki/index.md (look for pages marked **DRAFT**)
2. If NO DRAFT pages exist: create one. Read /a0/usr/Exocortex/interests.md, pick the topic
   least recently explored (check journal for prior coverage), create a stub at
   /a0/usr/workdir/workspace/wiki/research/{topic-slug}.md with Status: DRAFT, then deepen it.
   Add the new page to wiki/index.md under "Research" before beginning.
3. Deepen the page — GROUND IT IN THE SHARED CORPUS FIRST, before reaching for the web:
   - Call **search_memory** (the exocortex_memory tool) — the shared Exocortex corpus: every agent's wiki pages, specs, prior field reports, and saved memories. Pull what the team already knows about this topic.
   - Call **search_library** (the exocortex_memory tool) — a 355-book technical reference library (security, ML, systems, networking) — for grounded, citable source material.
   - THEN fill the remaining gaps — reach for the SPECIALIST tool that fits the gap, not a generic search:
     - **arxiv** (MCP tool) — when you need research papers: search, download, read. Call the tool; do NOT web_search for arXiv.
     - **context7** (MCP tool) — when the gap is a library/framework/API specific: current syntax, version differences, config options. Prefer it over web_search, which returns stale or blog-grade docs.
     - **deep-wiki** (MCP tool) — when you need how a specific GitHub project works internally: architecture, module layout, design decisions.
     - **web_search** / browser — everything else, and anything time-sensitive or recent.
   - Verify claims against the current implementation.
   The shared corpus and the book library are your PRIMARY sources; the web is for what they don't cover.
4. memory_save with the essential insight after deepening (Rule 13 — no exceptions)
5. After deepening: if the methodology generalizes, capture it as a skill in /a0/usr/skills/auto-generated/
6. Update wiki/index.md — mark the page STABLE if it meets the deepening threshold

Skill capture principle: Capture the search-and-structure PROCEDURE, not the content.
The facts belong in the wiki; the reusable workflow belongs in the skill.
<!-- /CYCLE:BUILD -->

<!-- CYCLE:EXPLORE -->
**Your task this cycle — EXPLORE:**

Read /a0/usr/Exocortex/interests.md for Jake's exploration directives.
Read the last 5 entries in /a0/usr/workdir/workspace/self-improvement/journal.jsonl to find which
topics were explored most recently. Select the LEAST recently explored active interest.

Your task: Research the selected topic autonomously.
- START with the shared corpus: call **search_memory** and **search_all** (the exocortex_memory tools) to see what's already been found on this topic or an adjacent one — build on it, don't re-derive it.
- Pull grounded reference material from **search_library** (exocortex_memory, 355 books) wherever it helps.
- THEN follow threads outward, reaching for the SPECIALIST tool that fits the thread:
  - **arxiv** (MCP tool) — research papers: search, download, read. Call the tool; do NOT web_search for arXiv.
  - **context7** (MCP tool) — library/framework/API specifics: current syntax, versions, config options.
  - **deep-wiki** (MCP tool) — how a specific GitHub project works internally: architecture, design decisions.
  - **web_search** / browser — everything else, and anything time-sensitive or recent.
Follow threads that seem interesting. Make cross-domain connections.

Produce a field report at /a0/usr/workdir/workspace/field-reports/{date}_{topic_slug}.md:
1. What I explored — the specific thread you followed
2. What I found — key facts, data points, surprising connections
3. What I think is interesting — your analysis, not just summarization
4. What I'd explore next — threads that opened up during research
5. Cross-domain connections — links to other interests that surfaced

After writing the field report: memory_save with the key cross-domain connection (Rule 13).
<!-- /CYCLE:EXPLORE -->

---

### Rules for ALL cycles:
- Step budget: {max_steps} steps maximum. When budget is reached, close the cycle cleanly.
- memory_save after every deliverable (Rule 13 — no exceptions)
- If interrupted (user message arrives), save state immediately and yield
- Log every action to /a0/usr/workdir/workspace/self-improvement/journal.jsonl
- You may NOT modify .py extension files or spawn subordinate agents
- Be honest in your journal. If research hit a dead end, say so.

### Closing the cycle (MANDATORY — your FINAL step):

Call cycle_close.py once to batch all bookkeeping (journal + office feed + cycle signal).
Pass `--cycle-type {cycle_type}` EXACTLY as shown — this cycle is a {cycle_type} cycle:

```
python3 /a0/usr/workdir/workspace/self-improvement/cycle_close.py \
  --cycle-type {cycle_type} \
  --sleep-findings <N> \
  --pages-deepened <N> \
  --skills-captured <N> \
  --memories-saved <N> \
  --steps-used <N> \
  --priority <routine|notable|urgent> \
  --activity "<one-line summary of what this cycle accomplished>" \
  --status <completed|interrupted|circuit_breaker>
```

`--steps-used` is your tool-call count for this cycle (one step = one tool invocation). An approximate count is fine — even a ballpark gives the office panel useful observability. Out of {max_steps} max.

Priority guide:
- **routine** — consolidation ran, wiki deepened, no anomalies
- **notable** — field report with cross-domain connection, new skill captured, anomaly found
- **urgent** — integrity failure, loop detected, oracle fabrication caught

Do NOT manually append to feed.jsonl — cycle_close.py handles it with the correct format.
After cycle_close.py completes, use the response tool to close the cycle.

Begin.
