---
skill_name: self-optimizing-skill
version: 1.0.0
description: A skill that monitors its own execution patterns, logs token usage vs. success rate, and gradually optimizes its approach using RL-inspired feedback loops
categories:
  - meta-learning
  - performance-optimization
  - self-improvement
token_budget: 4096
requires_tools:
  - code_execution_tool
  - response
configurable_params:
  epsilon: 0.1
  learning_rate: 0.1
  gamma: 0.9
---

# Self-Optimizing Skill Framework

## Overview

This skill implements a self-monitoring, self-optimizing execution framework inspired by the Atropos RL training infrastructure from OpenGauss/Hermes. Unlike static skills that execute identically each time, this skill learns from its own execution history and gradually improves its approach.

## Core Components

### 1. ExecutionTracker (`execution_tracker.py`)
- Tracks token usage (input/output) per phase
- Records tool calls with timestamps and success status
- Measures turn efficiency and duration
- Supports context manager pattern for automatic tracking

```python
from execution_tracker import ExecutionTracker

tracker = ExecutionTracker("my_skill", "research_task")
with tracker.phase("planning"):
    # do planning work
    pass
with tracker.phase("execution"):
    # do execution work  
    tracker.record_tool_call("search_engine", success=True)
```

### 2. PerformanceModel (`performance_model.py`)
- Maintains historical execution records
- Calculates success rates by task type
- Tracks token efficiency trends over time
- Detects performance degradation patterns

```python
from performance_model import PerformanceModel

model = PerformanceModel()
model.record_execution(tracker.get_summary(), strategy="default")
stats = model.get_task_stats("research_task")
print(f"Success rate: {stats.success_rate:.1%}")
```

### 3. StrategyOptimizer (`strategy_optimizer.py`)
- RL-inspired epsilon-greedy exploration/exploitation
- Maintains Q-values for different strategies per task type
- Selects optimal strategy based on historical performance
- Supports multiple selection modes (epsilon_greedy, softmax, round_robin)

```python
from strategy_optimizer import StrategyOptimizer

optimizer = StrategyOptimizer(epsilon=0.1, learning_rate=0.1)
strategy = optimizer.select_strategy("research_task")
# Execute with selected strategy...
optimizer.update_q_value("research_task", strategy, quality_score)
```

### 4. FeedbackReporter (`feedback_reporter.py`)
- Generates empirical performance reports
- Compares strategies across task types
- Detects cross-task patterns
- Provides optimization recommendations

```python
from feedback_reporter import FeedbackReporter

reporter = FeedbackReporter(performance_model, strategy_optimizer)
summary = reporter.generate_execution_summary("research_task")
print(reporter.format_report_for_display(summary))
```

## Usage Pattern

### Phase 1: Track Execution
```python
from execution_tracker import ExecutionTracker

tracker = ExecutionTracker(skill_name="my_skill", task_type="analysis")

with tracker.phase("planning"):
    # Analyze the request, plan approach
    pass

with tracker.phase("execution"):
    # Execute the planned approach
    tracker.record_tool_call("search_engine", success=True)
    tracker.record_tokens(input_tokens=500, output_tokens=200)
```

### Phase 2: Record and Learn
```python
from performance_model import PerformanceModel
from strategy_optimizer import StrategyOptimizer

# Initialize components (persist across sessions)
model = PerformanceModel()
optimizer = StrategyOptimizer(epsilon=0.1)

# Get execution summary
summary = tracker.get_summary()
quality_score = evaluate_quality(summary)  # Your evaluation logic

# Record the execution
model.record_execution(summary, strategy=optimizer.select_strategy(task_type))

# Update Q-value with reward signal
optimizer.update_q_value(task_type, selected_strategy, quality_score)
```

### Phase 3: Generate Reports
```python
from feedback_reporter import FeedbackReporter

reporter = FeedbackReporter(model, optimizer)

# Per-task summary
summary = reporter.generate_execution_summary("analysis")
print(reporter.format_report_for_display(summary))

# Strategy comparison
comparison = reporter.generate_comparison_report("analysis")

# Overall report across all tasks
overall = reporter.generate_overall_report()
```

## Configuration Parameters

| Parameter | Default | Description |
 epsilon | 0.1 | Exploration rate (10% random strategy selection) |
| learning_rate | 0.1 | How quickly Q-values adapt to new information |
| gamma | 0.9 | Discount factor for future rewards |
| selection_mode | "epsilon_greedy" | Strategy selection algorithm |

## Available Strategies

The framework includes these built-in strategies:

- **default**: Standard execution without special optimization
- **aggressive_caching**: Reuse previous results when possible
- **thorough_analysis**: Deep analysis with multiple verification steps  
- **fast_path**: Quick execution, minimal tool calls
- **iterative_refinement**: Start simple, refine based on intermediate results

## Expected Performance Improvements

> **Note:** No empirical baseline exists for these figures. The framework is a pattern for tracking and adapting strategy — actual improvement depends entirely on the task domain and how consistently the skill is applied. Run it, measure it, record real results before making claims.

Improvements are possible in token efficiency and strategy selection over repeated executions. Quantify from your own usage.

## Integration with Agent Zero

This skill can be loaded and used like any other skill:

```python
from skills_tool import load_skill

load_skill("self-optimizing-skill")
```

Or imported directly in code:

```python
import sys
sys.path.insert(0, '/a0/skills/self-optimizing-skill')

from execution_tracker import ExecutionTracker
from performance_model import PerformanceModel
from strategy_optimizer import StrategyOptimizer
from feedback_reporter import FeedbackReporter
```

## Data Persistence

Performance data is stored in `/a0/usr/workdir/self-optimizing-data/`:

- `performance_data.json`: Historical execution records
- Data persists across sessions for continuous learning

## Verification and Testing

Run the built-in tests:

```bash
cd /a0/skills/self-optimizing-skill
python execution_tracker.py    # Test tracker module
python performance_model.py    # Test model module  
python strategy_optimizer.py   # Test optimizer module
python feedback_reporter.py    # Test reporter module
```

## Design Principles

1. **Empirical validation first**: All claims backed by measured data, not theory
2. **Incremental improvement**: Small gains compound over many executions
3. **Exploration/exploitation balance**: Always try new approaches occasionally
4. **Task-type specialization**: Learn separately for each task category
5. **Transparency**: Full visibility into what's being learned and why

## Inspiration Sources

- OpenGauss Atropos framework (tinker-atropos/)
- Hermes self-improvement patterns
- Q-learning fundamentals from reinforcement learning theory
- Exocortex empirical validation methodology
