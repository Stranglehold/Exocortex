"""
ExecutionTracker - Metrics collection during skill execution

Tracks token usage, turn count, tool calls, time spent, and outcomes
during task execution for later analysis and optimization.
"""

import time
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class TaskPhase(Enum):
    """Phases of task execution to track separately."""
    PLANNING = "planning"
    EXECUTION = "execution"
    EVALUATION = "evaluation"
    RECOVERY = "recovery"


@dataclass
class ToolCallRecord:
    """Record of a single tool call."""
    tool_name: str
    timestamp: float
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    tokens_used: int = 0  # If trackable


@dataclass
class PhaseMetrics:
    """Metrics for a single phase of execution."""
    phase: str
    start_time: float
    end_time: Optional[float] = None
    turns_used: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    tool_calls: List[str] = field(default_factory=list)
    errors_encountered: int = 0


class ExecutionTracker:
    """
    Tracks execution metrics during task execution.
    
    Usage:
        with ExecutionTracker(skill_name="research") as tracker:
            tracker.start_phase("planning")
            # ... do work ...
            tracker.record_tool_call("search_engine", success=True)
            tracker.end_phase()
            tracker.set_success(True)
            tracker.set_quality_score(0.85)
    """
    
    def __init__(self, skill_name: str, task_type: str = "general"):
        self.skill_name = skill_name
        self.task_type = task_type
        self.start_time = time.time()
        self.current_phase: Optional[PhaseMetrics] = None
        self.phases: List[PhaseMetrics] = []
        self.tool_calls: List[ToolCallRecord] = []
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.total_turns = 0
        self.success = False
        self.quality_score: Optional[float] = None
        self.error_message: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
    
    def start_phase(self, phase_name: str):
        """Start tracking a new phase."""
        if self.current_phase:
            self.end_phase()
        
        self.current_phase = PhaseMetrics(
            phase=phase_name,
            start_time=time.time()
        )
    
    def end_phase(self):
        """End current phase and save metrics."""
        if self.current_phase:
            self.current_phase.end_time = time.time()
            self.phases.append(self.current_phase)
            
            # Accumulate totals
            self.total_tokens_input += self.current_phase.tokens_input
            self.total_tokens_output += self.current_phase.tokens_output
            self.total_turns += self.current_phase.turns_used
            
            self.current_phase = None
    
    def record_tool_call(self, tool_name: str, success: bool = True, 
                         error_message: str = None, tokens_used: int = 0):
        """Record a tool call."""
        record = ToolCallRecord(
            tool_name=tool_name,
            timestamp=time.time(),
            success=success,
            error_message=error_message,
            tokens_used=tokens_used
        )
        self.tool_calls.append(record)
        
        if self.current_phase:
            self.current_phase.tool_calls.append(tool_name)
            if not success:
                self.current_phase.errors_encountered += 1
    
    def record_turn(self, tokens_input: int = 0, tokens_output: int = 0):
        """Record a turn (LLM call)."""
        self.total_turns += 1
        self.total_tokens_input += tokens_input
        self.total_tokens_output += tokens_output
        
        if self.current_phase:
            self.current_phase.turns_used += 1
            self.current_phase.tokens_input += tokens_input
            self.current_phase.tokens_output += tokens_output
    
    def set_success(self, success: bool):
        """Mark execution as successful or failed."""
        self.success = success
    
    def set_quality_score(self, score: float):
        """Set quality score (0.0 to 1.0)."""
        self.quality_score = max(0.0, min(1.0, score))
    
    def set_error(self, error_message: str):
        """Record an error message."""
        self.error_message = error_message
        self.success = False
    
    def add_metadata(self, key: str, value: Any):
        """Add custom metadata to execution record."""
        self.metadata[key] = value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of tracked metrics."""
        end_time = time.time()
        duration_ms = (end_time - self.start_time) * 1000
        
        return {
            "skill_name": self.skill_name,
            "task_type": self.task_type,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": round(duration_ms, 2),
            "success": self.success,
            "quality_score": self.quality_score,
            "total_turns": self.total_turns,
            "total_tokens_input": self.total_tokens_input,
            "total_tokens_output": self.total_tokens_output,
            "total_tokens": self.total_tokens_input + self.total_tokens_output,
            "tool_calls_count": len(self.tool_calls),
            "phases_count": len(self.phases),
            "error_message": self.error_message,
            "metadata": self.metadata
        }
    
    def get_phase_summaries(self) -> List[Dict[str, Any]]:
        """Get summaries for all phases."""
        summaries = []
        for phase in self.phases:
            duration_ms = 0
            if phase.end_time and phase.start_time:
                duration_ms = (phase.end_time - phase.start_time) * 1000
            
            summaries.append({
                "phase": phase.phase,
                "duration_ms": round(duration_ms, 2),
                "turns_used": phase.turns_used,
                "tokens_input": phase.tokens_input,
                "tokens_output": phase.tokens_output,
                "tool_calls": phase.tool_calls,
                "errors_encountered": phase.errors_encountered
            })
        return summaries
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire tracker state to dictionary."""
        return {
            **self.get_summary(),
            "phases": self.get_phase_summaries(),
            "tool_calls": [
                {"name": tc.tool_name, "success": tc.success, 
                 "error": tc.error_message, "tokens": tc.tokens_used}
                for tc in self.tool_calls
            ]
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    # Context manager support
    def __enter__(self):
        self.start_phase("planning")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.current_phase:
            self.end_phase()
        
        if exc_type is not None:
            self.set_error(f"{exc_type.__name__}: {exc_val}")
        
        return False  # Don't suppress exceptions


# Example usage and testing
if __name__ == "__main__":
    print("Testing ExecutionTracker...")
    
    with ExecutionTracker(skill_name="test_skill", task_type="research") as tracker:
        tracker.record_turn(tokens_input=100, tokens_output=500)
        tracker.record_tool_call("search_engine", success=True)
        tracker.record_turn(tokens_input=200, tokens_output=300)
        tracker.record_tool_call("browser_agent", success=True)
        tracker.set_success(True)
        tracker.set_quality_score(0.85)
        tracker.add_metadata("query_complexity", "high")
    
    print(tracker.to_json())
