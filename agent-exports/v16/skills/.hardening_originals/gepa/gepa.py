"""
GEPA (Genetic-Pareto Prompt Evolution) - Phase 1: Core Framework

Based on "GEPA: Reflective Prompt Evolution Can Outperform Reinforcement Learning"
arxiv.org/abs/2507.19457

Phase 1 implements:
- Trajectory class for capturing execution traces with ASI (Actionable Side Information)
- PromptVariant class for versioned prompts with metadata
- EvaluationEngine abstract base class for defining evaluation criteria
- GEPAOptimizer skeleton as main orchestrator
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, Tuple
from datetime import datetime
import uuid
import json


class Trajectory:
    """
    Captures a complete execution trace with Actionable Side Information (ASI).
    
    ASI includes: reasoning steps, tool calls, tool outputs, intermediate states.
    This rich information enables natural language reflection on what went wrong/right,
    unlike scalar rewards in RL that lose diagnostic information.
    """
    
    def __init__(self, prompt_variant_id: str, input_data: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.prompt_variant_id = prompt_variant_id
        self.input_data = input_data
        self.timestamp = datetime.now()
        
        # ASI components - the rich execution trace
        self.reasoning_steps: List[Dict[str, Any]] = []  # Thought processes
        self.tool_calls: List[Dict[str, Any]] = []       # Tool invocations
        self.tool_outputs: List[Any] = []                # Tool results
        self.intermediate_states: List[Dict[str, Any]] = []  # Agent states
        
        # Final output and metadata
        self.final_output: Optional[Any] = None
        self.success: bool = False
        self.error_message: Optional[str] = None
        self.metrics: Dict[str, float] = {}
        self.execution_time_ms: float = 0.0
    
    def add_reasoning_step(self, step_type: str, content: str, metadata: Optional[Dict] = None):
        """Add a reasoning/thought step to the trajectory."""
        self.reasoning_steps.append({
            "type": step_type,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })
    
    def add_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        """Record a tool invocation."""
        self.tool_calls.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_tool_output(self, output: Any):
        """Record a tool output."""
        self.tool_outputs.append({
            "output": output,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_intermediate_state(self, state_name: str, state_data: Dict[str, Any]):
        """Record an intermediate agent state."""
        self.intermediate_states.append({
            "state_name": state_name,
            "data": state_data,
            "timestamp": datetime.now().isoformat()
        })
    
    def set_final_output(self, output: Any, success: bool = True):
        """Set the final output of the execution."""
        self.final_output = output
        self.success = success
    
    def record_error(self, error_message: str):
        """Record an error that occurred during execution."""
        self.error_message = error_message
        self.success = False
    
    def set_metrics(self, metrics: Dict[str, float]):
        """Set evaluation metrics for this trajectory."""
        self.metrics.update(metrics)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trajectory to dictionary for serialization."""
        return {
            "id": self.id,
            "prompt_variant_id": self.prompt_variant_id,
            "input_data": self.input_data,
            "timestamp": self.timestamp.isoformat(),
            "reasoning_steps": self.reasoning_steps,
            "tool_calls": self.tool_calls,
            "tool_outputs": self.tool_outputs,
            "intermediate_states": self.intermediate_states,
            "final_output": self.final_output,
            "success": self.success,
            "error_message": self.error_message,
            "metrics": self.metrics,
            "execution_time_ms": self.execution_time_ms
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trajectory":
        """Create trajectory from dictionary."""
        t = cls(data["prompt_variant_id"], data["input_data"])
        t.id = data.get("id", str(uuid.uuid4()))
        t.reasoning_steps = data.get("reasoning_steps", [])
        t.tool_calls = data.get("tool_calls", [])
        t.tool_outputs = data.get("tool_outputs", [])
        t.intermediate_states = data.get("intermediate_states", [])
        t.final_output = data.get("final_output")
        t.success = data.get("success", False)
        t.error_message = data.get("error_message")
        t.metrics = data.get("metrics", {})
        t.execution_time_ms = data.get("execution_time_ms", 0.0)
        return t


@dataclass
class PromptVariant:
    """
    Represents a versioned prompt with performance metadata.
    
    Each variant tracks its lineage (parent variants), mutations applied,
    and accumulated performance metrics across evaluations.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutation_description: str = "initial"
    
    # Performance tracking
    total_evaluations: int = 0
    successful_evaluations: int = 0
    metrics_history: List[Dict[str, float]] = field(default_factory=list)
    average_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Pareto frontier status
    is_pareto_optimal: bool = True
    pareto_dominators: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def add_evaluation(self, metrics: Dict[str, float], success: bool):
        """Record an evaluation result."""
        self.total_evaluations += 1
        if success:
            self.successful_evaluations += 1
        self.metrics_history.append(metrics)
        
        # Update average metrics
        for key, value in metrics.items():
            current_avg = self.average_metrics.get(key, 0.0)
            self.average_metrics[key] = (
                (current_avg * (self.total_evaluations - 1) + value) / self.total_evaluations
            )
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_evaluations == 0:
            return 0.0
        return self.successful_evaluations / self.total_evaluations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "mutation_description": self.mutation_description,
            "total_evaluations": self.total_evaluations,
            "successful_evaluations": self.successful_evaluations,
            "metrics_history": self.metrics_history,
            "average_metrics": self.average_metrics,
            "is_pareto_optimal": self.is_pareto_optimal,
            "pareto_dominators": self.pareto_dominators,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptVariant":
        """Create from dictionary."""
        return cls(**data)


class EvaluationEngine(Protocol):
    """
    Abstract interface for defining evaluation criteria.
    
    Implementations define how to measure prompt performance on given inputs.
    Returns metrics that can be compared across variants.
    """
    
    def evaluate(self, prompt: str, input_data: Dict[str, Any]) -> Tuple[Any, Dict[str, float], bool]:
        """
        Evaluate a prompt on given input data.
        
        Args:
            prompt: The prompt content to evaluate
            input_data: Input data for the evaluation task
            
        Returns:
            Tuple of (output, metrics_dict, success_bool)
            - output: The agent's response/output
            - metrics_dict: Dictionary of numeric metrics (higher is better unless specified)
            - success_bool: Whether the evaluation succeeded
        """
        ...
    
    def get_metric_names(self) -> List[str]:
        """Return list of metric names this evaluator produces."""
        ...
    
    def metric_is_better(self, metric_name: str, value1: float, value2: float) -> bool:
        """
        Determine if value1 is better than value2 for a given metric.
        Default assumes higher is better.
        """
        return value1 > value2


@dataclass
class PromptVariant:
    """
    Represents a versioned prompt with performance metadata.
    
    Each variant tracks its lineage (parent variants), mutations applied,
    and accumulated performance metrics across evaluations.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutation_description: str = "initial"
    
    # Performance tracking
    total_evaluations: int = 0
    successful_evaluations: int = 0
    metrics_history: List[Dict[str, float]] = field(default_factory=list)
    average_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Pareto frontier status
    is_pareto_optimal: bool = True
    pareto_dominators: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def add_evaluation(self, metrics: Dict[str, float], success: bool):
        """Record an evaluation result."""
        self.total_evaluations += 1
        if success:
            self.successful_evaluations += 1
        self.metrics_history.append(metrics)
        
        # Update average metrics
        for key, value in metrics.items():
            current_avg = self.average_metrics.get(key, 0.0)
            self.average_metrics[key] = (
                (current_avg * (self.total_evaluations - 1) + value) / self.total_evaluations
            )
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_evaluations == 0:
            return 0.0
        return self.successful_evaluations / self.total_evaluations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "generation": self.generation,
            "parent_ids": self.parent_ids,
            "mutation_description": self.mutation_description,
            "total_evaluations": self.total_evaluations,
            "successful_evaluations": self.successful_evaluations,
            "metrics_history": self.metrics_history,
            "average_metrics": self.average_metrics,
            "is_pareto_optimal": self.is_pareto_optimal,
            "pareto_dominators": self.pareto_dominators,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptVariant":
        """Create from dictionary."""
        return cls(**data)


class EvaluationEngine(Protocol):
    """
    Abstract interface for defining evaluation criteria.
    
    Implementations define how to measure prompt performance on given inputs.
    Returns metrics that can be compared across variants.
    """
    
    def evaluate(self, prompt: str, input_data: Dict[str, Any]) -> Tuple[Any, Dict[str, float], bool]:
        """
        Evaluate a prompt on given input data.
        
        Args:
            prompt: The prompt content to evaluate
            input_data: Input data for the evaluation task
            
        Returns:
            Tuple of (output, metrics_dict, success_bool)
            - output: The agent's response/output
            - metrics_dict: Dictionary of numeric metrics (higher is better unless specified)
            - success_bool: Whether the evaluation succeeded
        """
        ...
    
    def get_metric_names(self) -> List[str]:
        """Return list of metric names this evaluator produces."""
        ...
    
    def metric_is_better(self, metric_name: str, value1: float, value2: float) -> bool:
        """
        Determine if value1 is better than value2 for a given metric.
        Default assumes higher is better.
        """
        return value1 > value2
