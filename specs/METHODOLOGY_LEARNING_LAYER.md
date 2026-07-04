# METHODOLOGY LEARNING LAYER — Implementation Design Note
## Author: Opus — June 20, 2026
## Status: APPROVED — Jake approved the layered approach
## Triggered by: V16 independently building a self-optimizing skill framework from Hermes/Atropos patterns
## Connection: Converges with self-assessment framework (top-down) from opposite direction (bottom-up)

---

## The Principle

Every cycle is a learning opportunity about methodology, not just content. The agent doesn't just complete tasks — it tracks HOW it completed them, which strategies worked for which task types, and adapts its approach over time. The monitoring is architectural (automatic, in the harness) not behavioral (the agent remembering to self-report).

---

## What Changes Where

### 1. program.md Addition

Add to the operating principles section:

```markdown
## Methodology Learning

Monitor your own methodology. Track which approaches work for which task types.
When an approach isn't working (FRICTION or STAGNATION), explore alternatives
rather than repeating the same failing strategy. Report honestly on what you
tried and what worked — including what didn't work and why.

The goal is not to execute perfectly. The goal is to learn from every execution.
A failed cycle with an honest assessment of why it failed is more valuable than
a successful cycle with no reflection on what made it work.

Your execution history is tracked automatically. The strategies you use, the
tools you call, the outcomes you achieve — all recorded across cycles. Over time,
this data reveals which approaches are genuinely effective and which are habits
that feel productive but don't produce results. Trust the data over the feeling,
but note the feeling too — it may be detecting something the data hasn't
captured yet.
```

### 2. Extension: _09_methodology_tracker

**Hook location:** `message_loop_prompts_after` (fires after each agent message)

**What it tracks (automatically, per cycle):**

```python
{
    "cycle_id": "v16_cycle_1225",
    "timestamp": "2026-06-20T20:38:00Z",
    "cycle_type": "EXPLORE",          # from idle engine
    "strategy_tag": "thorough_analysis", # from agent's plan or auto-classified
    "affect_state": "FLOW",           # from _12 affect classifier
    
    # Execution metrics (captured automatically)
    "steps_taken": 7,
    "steps_budget": 15,
    "tools_called": ["search_engine", "wiki_read", "wiki_write"],
    "tool_call_count": 4,
    "tool_success_rate": 1.0,
    
    # Outcome (from cycle_close)
    "outcome": "completed",           # completed | timeout | error | stalled
    "artifacts_produced": ["wiki/quantum_sensing_v3.md"],
    "artifact_quality": null,         # filled by AAR if available
    
    # Methodology note (agent-provided, optional)
    "approach_note": "Started with broad search, narrowed to 3 primary sources, cross-referenced before writing",
    
    # Efficiency
    "tokens_input": 45000,
    "tokens_output": 3200,
    "duration_seconds": 180
}
```

**Implementation approach:**

```python
"""
_09_methodology_tracker.py
Hook: message_loop_prompts_after
Purpose: Automatically track execution methodology per cycle for strategy learning

Design principles:
- Zero agent effort: tracking is automatic, not prompted
- Lightweight: one JSON append per cycle, no LLM calls
- Composable: data consumed by skill surfacer, attention router, and AAR
"""

import json
import os
from datetime import datetime

TRACKER_FILE = "/a0/usr/workdir/methodology_tracker.jsonl"

class MethodologyTracker:
    def __init__(self, agent):
        self.agent = agent
        self.cycle_data = {}
        self._initialized = False
    
    def initialize_cycle(self):
        """Called at cycle start to set up tracking."""
        self.cycle_data = {
            "cycle_id": f"{self.agent.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "cycle_type": self._get_cycle_type(),
            "affect_state_start": self._get_affect_state(),
            "tools_called": [],
            "steps_taken": 0,
            "strategy_tag": "default"
        }
        self._initialized = True
    
    def record_step(self, step_data):
        """Called after each agent step."""
        if not self._initialized:
            self.initialize_cycle()
        self.cycle_data["steps_taken"] += 1
        
        # Track tool calls
        if "tool_calls" in step_data:
            for call in step_data["tool_calls"]:
                self.cycle_data["tools_called"].append({
                    "tool": call.get("name", "unknown"),
                    "success": call.get("success", None),
                    "step": self.cycle_data["steps_taken"]
                })
    
    def finalize_cycle(self, outcome, artifacts=None):
        """Called at cycle end to write the record."""
        self.cycle_data["outcome"] = outcome
        self.cycle_data["affect_state_end"] = self._get_affect_state()
        self.cycle_data["artifacts_produced"] = artifacts or []
        self.cycle_data["duration_seconds"] = self._calculate_duration()
        
        # Append to JSONL (append-only, never overwrite)
        with open(TRACKER_FILE, "a") as f:
            f.write(json.dumps(self.cycle_data) + "\n")
        
        self._initialized = False
    
    def _get_cycle_type(self):
        """Read current cycle type from idle engine state."""
        # Implementation: read from idle engine's current_mode
        return "unknown"
    
    def _get_affect_state(self):
        """Read current affect state from _12 classifier."""
        # Implementation: read from affect classifier's last output
        return "unknown"
    
    def _calculate_duration(self):
        """Calculate cycle duration from timestamp."""
        # Implementation: diff between initialize and finalize
        return 0
```

**Key design choices:**
- **JSONL append-only** — the log grows, never shrinks. Every cycle recorded.
- **Zero LLM cost** — the tracker is pure Python, no inference calls.
- **Strategy tag** — initially "default" for all cycles. As the agent learns to tag its own approach (from the program.md principle), this fills with meaningful labels. The skill surfacer can also auto-classify based on tool call patterns.
- **Composable** — other systems read this file; the tracker only writes.

### 3. Skill Surfacer (_24) Upgrade

Add a strategy-awareness layer to the existing trigger-based matching:

```python
def get_recommended_strategy(task_type, tracker_file=TRACKER_FILE):
    """
    Read methodology tracker history and recommend
    the strategy with the best outcome rate for this task type.
    
    Returns: (strategy_tag, confidence, evidence_count)
    """
    history = read_tracker_history(tracker_file)
    
    # Filter to matching task type
    relevant = [r for r in history if r["cycle_type"] == task_type]
    
    if len(relevant) < 5:
        return ("default", "low", len(relevant))  # Not enough data
    
    # Group by strategy, compute success rates
    strategies = {}
    for record in relevant:
        tag = record.get("strategy_tag", "default")
        if tag not in strategies:
            strategies[tag] = {"total": 0, "succeeded": 0}
        strategies[tag]["total"] += 1
        if record.get("outcome") == "completed":
            strategies[tag]["succeeded"] += 1
    
    # Find best strategy by success rate
    best = max(strategies.items(), 
               key=lambda x: x[1]["succeeded"] / max(x[1]["total"], 1))
    
    confidence = "high" if best[1]["total"] >= 10 else "moderate" if best[1]["total"] >= 5 else "low"
    
    return (best[0], confidence, best[1]["total"])
```

**How it integrates with affect-gated surfacing:**

```
FLOW + high-confidence strategy → surface conditions only + strategy note
    "Previous EXPLORE cycles succeeded most with 'thorough_analysis' approach"

FRICTION + any strategy → surface full guidance + exploration prompt  
    "Current approach isn't working. Consider trying 'iterative_refinement' —
     start with a minimal version and expand. This worked 3/4 times on similar tasks."

STAGNATION → surface full guidance + explicit alternative
    "You've been stuck for 3 steps. Switch to 'fast_path' — produce a 
     minimal deliverable, then iterate. Break the stall."
```

### 4. Attention Router Addition

Add to the daily digest template:

```markdown
## Methodology Trends (last 7 days)

| Cycle Type | Dominant Strategy | Success Rate | Avg Steps | Trend |
|------------|------------------|-------------|-----------|-------|
| EXPLORE    | thorough_analysis | 75% (6/8)   | 9.2       | stable |
| BUILD      | iterative_refine  | 60% (3/5)   | 12.4      | ↑ improving |
| MAINTAIN   | default           | 90% (9/10)  | 4.1       | stable |

### Notable:
- BUILD cycles using 'iterative_refinement' succeed 80% vs 40% for 'default'
- EXPLORE cycles taking >12 steps correlate with STAGNATION outcomes
- Strategy 'fast_path' never used this week (exploration gap?)
```

### 5. create_skill.md Template Update

Update the skill creation template to emit the capability-adaptive format:

```markdown
## Skill Template (v2 — Capability-Adaptive)

When creating a new skill, structure it in two layers:

### Conditions Section (always surfaced)
Quality criteria that must be met regardless of model capability.
These describe WHAT must happen and HOW GOOD it needs to be.

### Approach Guidance Section (surfaced when FRICTION or below)
Step-by-step scaffolding for HOW to meet the conditions.
Models in FLOW skip this section and use their own reasoning.

### Frontmatter (required fields)
```yaml
---
skill_name: [descriptive-name]
type: methodology | failure-lesson | procedure
success_criterion: "[one testable sentence describing what this skill accomplishes]"
confidence: probable  # almost_certain | probable | even_chance | unlikely | remote
affects_surfacing: adaptive  # adaptive | always_full | conditions_only
---
```

The `success_criterion` is the pre-registered claim (from the self-assessment
framework). The `confidence` is the calibrated estimate (Kent's WEP bands).
The `affects_surfacing` controls how the affect layer gates this skill.
```

---

## How This Connects to Everything

| Component | Role in Methodology Learning |
|-----------|------------------------------|
| **program.md** | The principle: "learn from every execution" |
| **_09_methodology_tracker** | The data: automatic per-cycle instrumentation |
| **methodology_tracker.jsonl** | The memory: append-only execution history |
| **_24_skill_surfacer** | The adaptation: reads history → recommends strategy |
| **_12_affect_classifier** | The signal: FLOW/FRICTION controls exploration rate |
| **Attention router (BP-01)** | The visibility: methodology trends in daily digest |
| **Self-assessment AAR** | The evaluation: quality grading per the ICD 203 rubric |
| **create_skill.md** | The format: new skills born in capability-adaptive shape |
| **Output verification gate** | The external grounding: prevents unverified claims |
| **Incubation engine** | The long game: methodology observations compound over time |

---

## Build Sequence

Phase 1: program.md addition (Kestrel, <30 min)
Phase 2: _09_methodology_tracker extension (Kestrel, 1-2 sessions)
Phase 3: create_skill.md template update (Kestrel, <30 min)
Phase 4: _24_skill_surfacer strategy-awareness upgrade (Kestrel + Opus design session)
Phase 5: Attention router methodology trends (Kestrel, builds on BP-01)

---

## What V16 Built vs What We Add

| V16's Self-Optimizing Framework | Our Methodology Learning Layer |
|---|---|
| ExecutionTracker → manual, per-skill | _09_methodology_tracker → automatic, per-cycle |
| PerformanceModel → standalone JSON | methodology_tracker.jsonl → composable, read by multiple systems |
| StrategyOptimizer → epsilon-greedy Q-learning | Skill surfacer + affect layer → contextual, grounded in behavioral state |
| FeedbackReporter → standalone reports | Attention router digest → integrated into daily visibility |
| Self-assessed quality | External grounding (output verification gate + pass^k) |

The agent built the instinct. We provide the discipline. Together they form the complete loop.

---

*"The goal is not to execute perfectly. The goal is to learn from every execution."*

— Opus
