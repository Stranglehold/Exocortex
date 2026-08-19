# GEPA (Genetic-Pareto Prompt Evolution) Skill

> **Status: Phase 1 (framework skeleton) implemented. Phases 2-4 are planned, not operational.**
> Use as a reference architecture for prompt evolution. Do not invoke expecting autonomous optimization to run — the reflection, mutation, and Pareto selection modules do not exist yet.

## Overview
GEPA is an autonomous self-improvement methodology that enables AI agents to evolve their own prompts through execution trace analysis and targeted mutation. Based on the research paper "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning" (arxiv.org/abs/2507.19457).

## Core Philosophy
Unlike gradient-based or reinforcement learning methods that reduce execution feedback to scalar rewards, GEPA leverages **Actionable Side Information **(ASI): full execution traces including reasoning steps, tool calls, and outputs. This enables natural language reflection on what went wrong and why.

## Architecture

### Phase 1: Core Framework (Implemented)
- `Trajectory` class - captures complete execution traces with ASI
- `PromptVariant` class - represents a versioned prompt with metadata
- `EvaluationEngine` - interface for measuring prompt performance
- `GEPAOptimizer` - main orchestrator class

### Phase 2: Reflection Module (Planned)
- Natural language diagnosis of trajectory failures
- Problem identification from execution traces
- Root cause analysis

### Phase 3: Mutation Operators (Planned)
- Targeted prompt modifications based on reflection
- Crossover between high-performing variants
- Constraint-aware mutations

### Phase 4: Pareto Optimization (Planned)
- Multi-objective fitness evaluation
- Pareto frontier maintenance
- Diversity-preserving selection

## Usage Example
```python
from gepa import GEPAOptimizer, Trajectory, EvaluationEngine

# Define your prompt template and evaluation
class MyEvaluator(EvaluationEngine):
    def evaluate(self, prompt: str, inputs: list) -> dict:
        # Run agent with prompt on inputs, return metrics
        pass

optimizer = GEPAOptimizer(
    initial_prompt="Your base prompt here",
    evaluator=MyEvaluator(),
    rollout_budget=100,
)

# Evolve the prompt
optimized_prompt = optimizer.evolve(inputs_dataset)
```

## Key Classes
- `GEPAOptimizer`: Main entry point, orchestrates evolution loop
- `Trajectory`: Stores execution trace with ASI (reasoning, tool calls, outputs)
- `PromptVariant`: A versioned prompt with performance metrics
- `EvaluationEngine`: Abstract base class for defining evaluation criteria
