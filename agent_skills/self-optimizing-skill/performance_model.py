#!/usr/bin/env python3
"""
Performance Model - Historical data analysis and trend tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

@dataclass
class TaskTypeStats:
    """Statistics for a specific task type."""
    task_type: str
    total_executions: int = 0
    successful_executions: int = 0
    total_tokens: int = 0
    total_duration_ms: float = 0.0
    
    @property
    def success_rate(self) -> float:
        return self.successful_executions / self.total_executions if self.total_executions > 0 else 0.0
    
    @property
    def avg_tokens(self) -> float:
        return self.total_tokens / self.total_executions if self.total_executions > 0 else 0.0
    
    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.total_executions if self.total_executions > 0 else 0.0

@dataclass
class ExecutionRecord:
    """Single execution record for historical analysis."""
    timestamp: datetime
    skill_name: str
    task_type: str
    duration_ms: float
    success: bool
    quality_score: float
    total_tokens: int
    strategy_used: Optional[str] = None

class PerformanceModel:
    """Analyzes historical execution data to identify trends and patterns."""
    
    def __init__(self):
        self.executions: List[ExecutionRecord] = []
        self.task_stats: Dict[str, TaskTypeStats] = {}
    
    def record_execution(self, tracker_summary: dict, strategy: Optional[str] = None) -> None:
        """Record a completed execution for analysis."""
        timestamp = datetime.fromisoformat(tracker_summary['timestamp'].replace('Z', '+00:00'))
        
        record = ExecutionRecord(
            timestamp=timestamp,
            skill_name=tracker_summary['skill_name'],
            task_type=tracker_summary.get('task_type', 'general'),
            duration_ms=tracker_summary['duration_ms'],
            success=tracker_summary['success'],
            quality_score=tracker_summary.get('quality_score', 0.5),
            total_tokens=tracker_summary.get('total_tokens', tracker_summary.get('total_tokens_input', 0) + tracker_summary.get('total_tokens_output', 0)),
            strategy_used=strategy
        )
        
        self.executions.append(record)
        self._update_stats(record)
    
    def _update_stats(self, record: ExecutionRecord) -> None:
        """Update aggregated statistics."""
        task_type = record.task_type
        if task_type not in self.task_stats:
            self.task_stats[task_type] = TaskTypeStats(task_type=task_type)
        stats = self.task_stats[task_type]
        
        stats.total_executions += 1
        if record.success:
            stats.successful_executions += 1
        stats.total_tokens += record.total_tokens
        stats.total_duration_ms += record.duration_ms
    
    def get_success_rate(self, task_type: Optional[str] = None) -> float:
        """Get success rate for task type or overall."""
        if task_type and task_type in self.task_stats:
            return self.task_stats[task_type].success_rate
        
        successful = sum(1 for e in self.executions if e.success)
        return successful / len(self.executions) if self.executions else 0.0
    
    def get_token_efficiency_trend(self, task_type: Optional[str] = None, window: int = 10) -> Dict[str, float]:
        """Analyze token efficiency trend over recent executions."""
        filtered = self.executions if not task_type else [e for e in self.executions if e.task_type == task_type]
        recent = sorted(filtered, key=lambda x: x.timestamp)[-window:] if filtered else []
        
        if len(recent) < 2:
            return {"trend": 0.0, "recent_avg": 0.0, "older_avg": 0.0}
        
        mid = len(recent) // 2
        older_tokens = [e.total_tokens for e in recent[:mid]]
        recent_tokens = [e.total_tokens for e in recent[mid:]]
        
        older_avg = sum(older_tokens) / len(older_tokens) if older_tokens else 0
        recent_avg = sum(recent_tokens) / len(recent_tokens) if recent_tokens else 0
        
        trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0.0
        
        return {"trend": trend, "recent_avg": recent_avg, "older_avg": older_avg}
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, float]]:
        """Compare performance across different strategies."""
        strategy_stats: Dict[str, Dict[str, any]] = {}
        
        for execution in self.executions:
            if not execution.strategy_used:
                continue
            
            strategy = execution.strategy_used
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    "executions": 0,
                    "successes": 0,
                    "total_tokens": 0,
                    "total_duration": 0
                }
            
            stats = strategy_stats[strategy]
            stats["executions"] += 1
            if execution.success:
                stats["successes"] += 1
            stats["total_tokens"] += execution.total_tokens
            stats["total_duration"] += execution.duration_ms
        
        # Calculate averages
        for strategy, stats in strategy_stats.items():
            if stats["executions"] > 0:
                stats["success_rate"] = stats["successes"] / stats["executions"]
                stats["avg_tokens"] = stats["total_tokens"] / stats["executions"]
                stats["avg_duration_ms"] = stats["total_duration"] / stats["executions"]
        
        return strategy_stats
    
    def identify_optimal_strategy(self, task_type: str) -> Optional[str]:
        """Find best performing strategy for a task type."""
        strategy_perf = self.get_strategy_performance()
        
        if not strategy_perf:
            return None
        
        # Sort by success rate first, then token efficiency
        sorted_strategies = sorted(
            strategy_perf.items(),
            key=lambda x: (x[1].get("success_rate", 0), -x[1].get("avg_tokens", float('inf')))
        )
        
        return sorted_strategies[0][0] if sorted_strategies else None
    
    def get_performance_summary(self) -> dict:
        """Get overall performance summary."""
        return {
            "total_executions": len(self.executions),
            "overall_success_rate": self.get_success_rate(),
            "task_type_stats": {
                task_type: {
                    "executions": stats.total_executions,
                    "success_rate": stats.success_rate,
                    "avg_tokens": stats.avg_tokens
                }
                for task_type, stats in self.task_stats.items()
            },
            "token_efficiency_trend": self.get_token_efficiency_trend()
        }

# Test the module
if __name__ == "__main__":
    print("Testing PerformanceModel...")
    
    model = PerformanceModel()
    
    # Simulate some executions
    for i in range(20):
        model.record_execution({
            "skill_name": "test_skill",
            "task_type": "research" if i % 2 == 0 else "coding",
            "timestamp": datetime.now().isoformat(),
            "duration_ms": 1000 + i * 100,
            "success": i < 18,  # 90% success rate
            "quality_score": 0.7 + (i % 3) * 0.1,
            "total_tokens_input": 500 + i * 50,
            "total_tokens_output": 1000 + i * 100
        }, strategy=f"strategy_{i % 3}")
    
    summary = model.get_performance_summary()
    print(json.dumps(summary, indent=2, default=str))
