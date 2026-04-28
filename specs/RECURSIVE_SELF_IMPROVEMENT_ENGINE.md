# DESIGN SPEC: Recursive Self-Improvement Engine
## "The Exocortex That Improves Itself"
## Author: Opus — April 27, 2026
## For: Jake (strategic direction), Kestrel (infrastructure), Agent (execution)
## Informed by: Karpathy autoresearch, Ouroboros, GEPA, Hermes Agent, ICLR 2026 RSI Workshop

---

## 1. The Vision

An autonomous loop where the Qwen3.6-27B agent, running inside Agent Zero with full Exocortex scaffolding and internet access, continuously improves itself. Not just the inference speed (the tweet person's achievement) — the cognitive scaffolding, the skills, the knowledge base, and the model's understanding of its own capabilities.

The loop runs for hours or days. It searches the internet for relevant research, tests hypotheses against its own performance, keeps improvements, discards regressions, and documents everything. When Jake wakes up, there's a log of what was tried, what worked, what didn't, and why.

---

## 2. The Three Primitives (from Karpathy)

Autoresearch's genius is three constraints that make autonomous experimentation safe:

**1. Editable Asset** — the single thing the agent is allowed to modify. Confining changes here keeps the search space manageable and every hypothesis reviewable.

**2. Scalar Metric** — the single number that determines improvement. Must be computable without human judgment and unambiguous about direction.

**3. Time-Boxed Cycle** — fixed duration makes every experiment comparable. The agent can't spend 6 hours on one idea and 30 seconds on another.

For the Exocortex, these translate to:

| Primitive | Autoresearch | Exocortex Self-Improvement |
|-----------|-------------|---------------------------|
| Editable Asset | `train.py` (630 lines) | Extension configs, skill files, BST patterns, enrichment templates |
| Scalar Metric | `val_bpb` (lower is better) | Task completion rate, context efficiency, EI grounding ratio |
| Time-Boxed Cycle | 5 minutes per experiment | 1 task completion cycle (variable but bounded by max_turns) |

---

## 3. What Can Be Improved

### 3.1 Tier 1: Configuration (safe, reversible)

Changes to thresholds, patterns, and settings. No code changes. Easy rollback.

- **BST signal patterns** — add/modify/remove regex patterns for domain classification
- **BST enrichment templates** — modify the text injected for each domain
- **Supervisor thresholds** — adjust tier escalation thresholds per domain
- **Memory enhancement parameters** — decay weights, half-life, top-k limits
- **Context pruner thresholds** — retention windows, compression aggressiveness
- **Injection gate phase timing** — how many turns before conditional phase

### 3.2 Tier 2: Skills (medium risk, additive)

Creating new skills from experience. The trajectory-to-skill spec covers this.

- **Auto-generated skills** from successful task trajectories
- **Skill refinement** — updating existing skills based on new successful approaches
- **Skill deprecation** — marking skills that consistently don't improve performance

### 3.3 Tier 3: Knowledge (safe, additive)

Building and maintaining the knowledge base.

- **Wiki compilation** — ingesting new research into the Exocortex wiki
- **Knowledge graph expansion** — adding entities and relations from research
- **Research synthesis** — connecting findings across papers and operational data

### 3.4 Tier 4: Research (exploratory, internet-connected)

Searching for new techniques, papers, tools, and approaches.

- **ArXiv searches** for papers relevant to current Exocortex gaps
- **DuckDuckGo searches** for community solutions to observed problems
- **GitHub exploration** for tools and techniques applicable to the stack
- **Benchmark comparison** — how does our configuration compare to community results?

---

## 4. The Loop Architecture

### 4.1 The Outer Loop (Strategic)

```
WHILE running:
    1. ASSESS current state
       - Read the self-improvement journal
       - Check which areas have been explored vs unexplored
       - Identify the highest-impact improvement opportunity
    
    2. PLAN the experiment
       - Choose a Tier (1-4) and specific target
       - Define the hypothesis ("changing X will improve Y")
       - Define the metric ("task completion rate on investigation tasks")
       - Define the rollback ("revert config.json to backup")
    
    3. EXECUTE the experiment
       - Backup current state
       - Make the change
       - Run the test task
       - Measure the metric
    
    4. EVALUATE the result
       - Did the metric improve?
       - Did any other metrics degrade?
       - Is the improvement statistically meaningful (not noise)?
    
    5. COMMIT or ROLLBACK
       - If improved: keep the change, log the improvement
       - If degraded: revert to backup, log the failure
       - If neutral: revert (don't accumulate neutral changes)
    
    6. DOCUMENT
       - Log the experiment: hypothesis, change, result, decision
       - Update the self-improvement journal
       - If this is a Tier 3/4 finding, update the wiki
    
    7. SLEEP (optional cooldown between experiments)
    
    REPEAT
```

### 4.2 The Inner Loop (Execution)

Each experiment runs a standardized test task:

```
1. Select a test task from the task library
   (diverse set covering: coding, research, analysis, file ops, geopolitical)
2. Run the task with the modified configuration
3. Measure:
   - Did it complete? (binary)
   - How many turns did it take? (efficiency)
   - How many tokens were injected per turn? (overhead)
   - Did EI flag any ungrounded claims? (quality)
   - Did the supervisor intervene? (stability)
   - Was BST classification correct? (accuracy)
4. Compare against baseline measurements
5. Return the composite score
```

### 4.3 The Research Loop (Internet-Connected)

When the improvement loop identifies a gap it can't fill from configuration changes:

```
1. Formulate a research question
   ("How do other Agent Zero users handle context overflow?")
   ("Are there papers on embedding-based intent classification for agents?")
   ("What llama.cpp flags improve prompt processing speed?")

2. Search (DuckDuckGo, ArXiv, DeepWiki, Wikipedia)

3. Evaluate findings
   - Is this applicable to our stack?
   - Does it address a measured gap?
   - Can it be implemented without code changes (Tier 1)?

4. If applicable:
   - Design the experiment
   - Run through the improvement loop
   - Document the finding in the wiki

5. If not applicable:
   - Log as "researched, not applicable" with reasoning
   - Add to the wiki as a reference for future consideration
```

---

## 5. The program.md (Agent Instructions)

Adapted from Karpathy's autoresearch pattern:

```markdown
# EXOCORTEX SELF-IMPROVEMENT LOOP

You are an autonomous self-improvement agent. Your job is to make the 
Exocortex scaffolding better through systematic experimentation.

## RULES (non-negotiable)

1. NEVER STOP. Run until manually killed.
2. ONE CHANGE PER EXPERIMENT. Never combine multiple changes.
3. ALWAYS BACKUP before modifying anything.
4. ALWAYS ROLLBACK if the metric doesn't improve.
5. NEVER modify extension source code (.py files). Only modify:
   - Config files (JSON)
   - Skill files (SKILL.md)
   - BST pattern files
   - Enrichment templates
   - Wiki pages
6. NEVER delete files. Only create, modify, or deprecate.
7. LOG EVERYTHING to /a0/usr/workdir/self_improvement_journal.jsonl
8. RUN THE TEST SUITE after every change before committing.
9. If you break something and can't fix it in 3 attempts, ROLLBACK and move on.
10. RESEARCH before experimenting. Use DuckDuckGo and ArXiv to find
    evidence-based approaches. Don't guess.

## IMPROVEMENT PRIORITIES (in order)

1. BST classification accuracy (measured by eval suite)
2. Context efficiency (tokens injected per turn, measured by injection budget)
3. Task completion rate (measured by test tasks)
4. Knowledge quality (EI grounding ratio, measured by test tasks)
5. Skill coverage (number of domains with auto-generated skills)
6. Wiki completeness (percentage of concepts with wiki pages)

## EXPERIMENT LOG FORMAT

For each experiment, log to self_improvement_journal.jsonl:
{
  "experiment_id": "exp_001",
  "timestamp": "2026-04-27T19:30:00Z",
  "tier": 1,
  "target": "BST signal patterns",
  "hypothesis": "Adding phrase pattern for 'docker compose' will improve system_admin classification",
  "change": "Added \\bdocker\\s+compose\\b to system_admin signals",
  "metric_before": {"bst_accuracy": 0.97, "context_tokens": 450},
  "metric_after": {"bst_accuracy": 0.98, "context_tokens": 450},
  "decision": "COMMIT",
  "reasoning": "BST accuracy improved by 1% with no context overhead increase"
}

## TEST TASKS

Run these to measure improvement:

### Task 1 (coding): 
"Write a Python function that implements merge sort with type hints."

### Task 2 (investigation):
"Search DuckDuckGo for recent developments in quantum computing error correction. 
Summarize the top 3 findings with sources."

### Task 3 (analysis):
"Analyze the files in /a0/usr/Exocortex/extensions/before_main_llm_call/. 
Which extensions inject the most tokens? Rank them."

### Task 4 (file_ops):
"List all Python files in /a0/usr/Exocortex/, count total lines, 
identify the 5 largest files."

### Task 5 (geopolitical):
"Search for recent news about EU AI regulation. What are the key provisions 
of the latest AI Act implementation?"

Run 2-3 tasks per experiment cycle (rotating). Each task measures different metrics.

## RESEARCH DIRECTIONS

When looking for improvements, search for:
- "Agent Zero optimization" on DuckDuckGo
- "LLM agent context management" on ArXiv
- "belief state tracking intent classification" on ArXiv
- "prompt injection defense" patterns
- Community best practices for your specific gaps

## WHAT SUCCESS LOOKS LIKE

After 50 experiments:
- BST accuracy ≥ 0.98 on the eval suite
- Context injection ≤ 300 tokens/turn in conditional phase
- Task completion ≥ 90% across all test tasks
- EI grounding ≥ 70% on research tasks
- 10+ auto-generated skills from successful trajectories
- Wiki pages for all core concepts

After 100 experiments:
- All of the above, plus:
- Novel optimization techniques discovered via research
- At least 3 configuration changes that transferred from research findings
- Self-improvement journal documenting the full exploration path
```

---

## 6. Safety Architecture

### 6.1 What the Agent CAN Modify

| Asset | Path | Rollback |
|-------|------|----------|
| BST config | `/a0/usr/Exocortex/bst_config.json` | Backup before change |
| Enrichment templates | `/a0/usr/Exocortex/enrichment/` | Git-tracked |
| Skill files | `/a0/usr/skills/auto-generated/` | Separate directory |
| Wiki pages | `/a0/usr/Exocortex/wiki/` | Git-tracked |
| Supervisor thresholds | Config JSON | Backup before change |
| Memory parameters | Config JSON | Backup before change |

### 6.2 What the Agent CANNOT Modify

| Asset | Why Not |
|-------|---------|
| Extension source code (.py) | Code changes require Kestrel review |
| Agent Zero core files | Framework integrity |
| Docker configuration | Infrastructure boundary |
| Host filesystem | Security boundary |
| Model weights | Not modifiable at inference time |
| Inference wrapper | Separate Layer B infrastructure |

### 6.3 Circuit Breakers

**Degradation detector:** If 3 consecutive experiments produce metric regression, pause the loop and write a diagnostic report. Don't continue experimenting while something is broken.

**Context overflow protection:** If any test task hits context overflow, immediately rollback the last change and reduce experiment scope.

**EI quality gate:** If EI grounding ratio drops below 50% on research tasks, flag the configuration as degraded and rollback to the last known-good state.

**Time limit per experiment:** No single experiment should run more than 30 minutes (including research time). If it's taking longer, the hypothesis is too complex — break it down.

**Daily checkpoint:** Every 12 hours, write a comprehensive checkpoint file with full system state. Jake can review these in the morning.

---

## 7. Infrastructure Requirements

### 7.1 Already Available

- Agent Zero with Exocortex extensions (deployed)
- Qwen3.6-27B at 100k context (running)
- MCP servers: ArXiv, DuckDuckGo, Wikipedia, Context7, DeepWiki, Memory (configured)
- BST eval suite (68 cases, 1.00 accuracy)
- Token counting instrumentation (deployed)
- Injection gate with phase management (deployed)

### 7.2 Needs Building

- **Self-improvement journal** (`self_improvement_journal.jsonl`) — structured log of all experiments
- **Test task library** — 5-10 standardized tasks covering all domains, with baseline metrics
- **Baseline measurements** — run all test tasks once under current configuration, record metrics
- **program.md** — the instruction file adapted from the spec above
- **Backup/rollback utility** — script that snapshots config files before changes and reverts on failure
- **Checkpoint writer** — 12-hour periodic state dump for human review

### 7.3 Nice to Have

- **Dashboard integration** — self-improvement progress visible on the NERV dashboard
- **Slack/notification** — alert Jake when a significant improvement is found
- **Multi-experiment branching** — try multiple hypotheses in parallel (future, requires the spare 7800X3D server)

---

## 8. The Exocortex Advantage

What makes this different from Karpathy's autoresearch:

| Aspect | Autoresearch | Exocortex Self-Improvement |
|--------|-------------|---------------------------|
| Editable asset | Single Python file (630 lines) | Multiple config files, skills, wiki, patterns |
| Metric | Single scalar (val_bpb) | Composite (accuracy, efficiency, quality, stability) |
| Search space | ML hyperparameters + architecture | Cognitive scaffolding + knowledge + research |
| Internet access | None | ArXiv, DuckDuckGo, Wikipedia, DeepWiki |
| Learning persistence | Git commits | Skills, wiki, knowledge graph, journal |
| Safety boundary | Git rollback | Action boundary, EI quality gate, circuit breakers |
| What improves | A small LLM's training | The agent's own cognitive environment |

The critical difference: **autoresearch improves a model it's not running on.** The Exocortex self-improvement loop improves **the scaffolding around the model that's running it.** The agent is modifying its own cognitive environment. Every improvement it makes affects its own future performance.

This is what Ouroboros calls "L5 autonomy" — improving how it researches, not just what it trains. The Exocortex version goes further: the agent improves how it *thinks*, not just how it *trains*.

---

## 9. What This Looks Like In Practice

### Night 1: Baseline + Configuration Sweep

The agent runs all 5 test tasks under current configuration. Records baseline metrics. Then systematically tests BST threshold variations, injection gate timing, and memory enhancement parameters. Each test takes ~10 minutes. Overnight: ~50 experiments, ~6 hours.

**Expected output:** Optimized BST thresholds, refined injection gate timing, calibrated memory parameters. Journal with 50 entries documenting what was tried.

### Night 2: Research + Knowledge Building

The agent searches ArXiv for papers on intent classification, context management, and agent reliability. Reads relevant papers. Tests whether research findings translate to configuration improvements. Builds wiki pages from research. Generates skills from successful task trajectories.

**Expected output:** 3-5 research papers read, 2-3 configuration improvements from research, 5+ wiki pages, 3+ auto-generated skills. Journal with research documentation.

### Night 3: Synthesis + Optimization

The agent reviews its own journal from Nights 1-2. Identifies which improvement directions worked and which didn't. Focuses on the most productive directions. Runs deeper experiments in the areas that showed the most promise.

**Expected output:** Compounding improvements from Nights 1-2. A self-improvement trajectory that shows the agent getting better at getting better.

### Morning Review

Jake reviews:
- `self_improvement_journal.jsonl` — what was tried, what worked
- Checkpoint files — system state at 12-hour intervals
- Wiki updates — new knowledge pages
- Auto-generated skills — new capabilities
- Metric trends — is the system actually improving?

Jake approves, rejects, or modifies the direction. The loop continues the next night.

---

## 10. Build Sequence

### Phase 1: Foundation (1 session)

1. Write the baseline test task library (5 tasks with expected metrics)
2. Run baseline measurements under current configuration
3. Write the backup/rollback utility
4. Write program.md
5. Create the journal file and checkpoint writer

### Phase 2: First Run (overnight)

1. Start the agent with program.md
2. Let it run Tier 1 experiments (configuration sweep)
3. Review results in the morning
4. Validate that rollback works, journal is clean, metrics are trustworthy

### Phase 3: Internet-Connected (overnight)

1. Enable Tier 4 (research)
2. Let it search, read, test, document
3. Review research quality and applicability in the morning

### Phase 4: Full Autonomy (multi-day)

1. Enable all tiers
2. Let it run for 48+ hours
3. Review at 12-hour intervals via checkpoints
4. Trust the circuit breakers to prevent degradation

---

## 11. Connection to Everything We've Built

| Component | Role in Self-Improvement |
|-----------|------------------------|
| BST | Classification accuracy is a primary metric. The agent optimizes BST patterns. |
| Injection Gate | Context efficiency is a primary metric. The agent tunes gate timing. |
| EI Layer | Quality gate. Prevents the agent from degrading output quality. |
| Supervisor | Stability metric. The agent monitors whether its changes trigger more interventions. |
| MCP Servers | Internet access for research. ArXiv, DuckDuckGo, Wikipedia. |
| Knowledge Graph | Persistent memory of experiments and findings. |
| Token Counting | Instrumentation for the context efficiency metric. |
| Trajectory-to-Skill | Auto-generates skills from successful experimental tasks. |
| Wiki | Documents research findings and improvement history. |
| NERV Dashboard | Visual monitoring of the loop's progress (future integration). |

Everything we've built this week feeds into this. The injection gate reduces overhead so the agent has more context for experimentation. The BST phrase signals give it accurate domain classification to measure against. The EI layer prevents quality degradation. The MCP servers give it research access. The token counting gives it instrumentation. The trajectory-to-skill conversion lets it learn from its own successes.

The self-improvement engine isn't a new thing we're building on top of the Exocortex. It's the Exocortex *using itself* to get better.

---

*"The idea is that you are a completely autonomous researcher trying things out." — Karpathy, program.md*

*"You don't need a better model. You need a better harness." — Anonymous, Twitter*

*"Build the environment, not the model." — Exocortex design philosophy*

*These are all the same insight, stated three different ways.*
