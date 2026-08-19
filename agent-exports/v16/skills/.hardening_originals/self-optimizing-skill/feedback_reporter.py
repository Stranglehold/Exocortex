"""
FeedbackReporter - Empirical validation and performance reporting

Generates reports on skill execution patterns, token efficiency trends,
success rates, and optimization recommendations.
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import asdict


class FeedbackReporter:
    """
    Generates empirical reports on skill performance.
    
    Provides:
    - Execution summaries with key metrics
    - Token efficiency trend analysis
    - Success rate tracking by task type
    - Strategy comparison reports
    - Optimization recommendations
    """
    
    def __init__(self, performance_model=None, strategy_optimizer=None):
        self.performance_model = performance_model
        self.strategy_optimizer = strategy_optimizer
    
    def set_components(self, performance_model, strategy_optimizer):
        """Set the model and optimizer components."""
        self.performance_model = performance_model
        self.strategy_optimizer = strategy_optimizer
    
    def generate_execution_summary(self, task_type: str) -> Dict[str, Any]:
        """
        Generate summary of executions for a specific task type.
        
        Includes:
        - Total executions and success rate
        - Token usage statistics
        - Turn count statistics  
        - Quality score trends
        - Best performing strategy
        """
        if not self.performance_model:
            return {"error": "Performance model not set"}
        
        stats = self.performance_model.get_task_stats(task_type)
        if not stats:
            return {
                "task_type": task_type,
                "status": "no_data",
                "message": f"No execution data found for task type '{task_type}'"
            }
        
        # Get token efficiency trend
        token_trend = self.performance_model.get_token_efficiency_trend(task_type)
        
        # Get best strategy recommendation
        recommendation = {}
        if self.strategy_optimizer:
            recommendation = self.strategy_optimizer.get_recommendation(task_type)
        
        return {
            "task_type": task_type,
            "status": "ok",
            "executions": {
                "total": stats.total_executions,
                "successful": stats.successful_executions,
                "success_rate": f"{stats.success_rate:.1%}"
            },
            "token_usage": {
                "total_tokens": stats.total_tokens_used,
                "avg_per_execution": round(stats.avg_tokens, 0),
                "trend": token_trend.get("direction", "unknown") if token_trend.get("status") == "ok" else "insufficient_data",
                "current_avg": token_trend.get("current_avg_tokens", 0) if token_trend.get("status") == "ok" else None,
                "change_percent": token_trend.get("change_percent", 0) if token_trend.get("status") == "ok" else None
            },
            "turn_efficiency": {
                "avg_turns_per_execution": round(stats.avg_turns, 1)
            },
            "quality": {
                "average_score": round(stats.avg_quality_score, 3),
                "trend": stats.token_trend
            },
            "strategy_recommendation": recommendation,
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_comparison_report(self, task_type: str) -> Dict[str, Any]:
        """
        Compare performance across different strategies for a task type.
        
        Shows:
        - Q-values for each strategy
        - Visit counts
        - Average rewards
        - Statistical significance indicators
        """
        if not self.strategy_optimizer:
            return {"error": "Strategy optimizer not set"}
        
        strategy_stats = self.strategy_optimizer.get_strategy_stats(task_type)
        
        if not strategy_stats:
            return {
                "task_type": task_type,
                "status": "no_data",
                "message": "No strategy comparison data available"
            }
        
        # Sort by Q-value
        sorted_strategies = sorted(
            strategy_stats.items(),
            key=lambda x: x[1]["q_value"],
            reverse=True
        )
        
        best_q = sorted_strategies[0][1]["q_value"] if sorted_strategies else 0
        
        comparisons = []
        for name, stats in sorted_strategies:
            is_best = name == sorted_strategies[0][0]
            q_diff_from_best = round(stats["q_value"] - best_q, 3) if not is_best else 0
            
            comparisons.append({
                "strategy": name,
                "rank": len(comparisons) + 1,
                "is_recommended": is_best,
                "q_value": stats["q_value"],
                "diff_from_best": q_diff_from_best,
                "visit_count": stats["visit_count"],
                "avg_reward": stats["avg_reward"],
                "reward_stddev": stats["reward_stddev"],
                "confidence_level": self._calculate_confidence(stats["visit_count"])
            })
        
        return {
            "task_type": task_type,
            "status": "ok",
            "comparison_date": datetime.now().isoformat(),
            "strategies_compared": len(comparisons),
            "recommendation": sorted_strategies[0][0] if sorted_strategies else "default",
            "strategy_rankings": comparisons
        }
    
    def _calculate_confidence(self, visit_count: int) -> str:
        """Calculate confidence level based on number of visits."""
        if visit_count < 5:
            return "very_low"
        elif visit_count < 10:
            return "low"
        elif visit_count < 25:
            return "medium"
        elif visit_count < 50:
            return "high"
        else:
            return "very_high"
    
    def generate_overall_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive report across all task types.
        
        Includes:
        - Overall performance summary
        - Per-task-type breakdowns
        - Cross-task patterns
        - Top recommendations
        """
        if not self.performance_model:
            return {"error": "Performance model not set"}
        
        overall = self.performance_model.get_performance_summary()
        task_types = self.performance_model.get_all_task_types()
        
        # Generate per-task summaries
        task_summaries = {}
        for task_type in task_types:
            task_summaries[task_type] = self.generate_execution_summary(task_type)
        
        # Find patterns
        patterns = self._detect_patterns(task_summaries)
        
        return {
            "report_type": "overall_performance",
            "generated_at": datetime.now().isoformat(),
            "summary": overall,
            "task_types_analyzed": len(task_types),
            "task_breakdowns": task_summaries,
            "patterns_detected": patterns,
            "top_recommendations": self._generate_top_recommendations(task_summaries)
        }
    
    def _detect_patterns(self, task_summaries: Dict) -> List[Dict]:
        """Detect cross-task patterns."""
        patterns = []
        
        # Check for consistently improving tasks
        improving_tasks = [
            name for name, summary in task_summaries.items()
            if summary.get("token_usage", {}).get("trend") == "improving"
        ]
        if improving_tasks:
            patterns.append({
                "type": "positive_trend",
                "description": f"{len(improving_tasks)} task type(s) showing token efficiency improvement",
                "tasks": improving_tasks
            })
        
        # Check for degrading tasks
        degrading_tasks = [
            name for name, summary in task_summaries.items()
            if summary.get("token_usage", {}).get("trend") == "degrading"
        ]
        if degrading_tasks:
            patterns.append({
                "type": "negative_trend",
                "description": f"{len(degrading_tasks)} task type(s) showing token efficiency degradation",
                "tasks": degrading_tasks,
                "action_required": True
            })
        
        # Check for low success rate tasks
        low_success_tasks = [
            name for name, summary in task_summaries.items()
            if summary.get("executions", {}).get("success_rate", "100%") != "100.0%"
            and float(summary.get("executions", {}).get("success_rate", "100%")[:-1]) < 90
        ]
        if low_success_tasks:
            patterns.append({
                "type": "reliability_concern",
                "description": f"{len(low_success_tasks)} task type(s) with success rate below 90%",
                "tasks": low_success_tasks,
                "action_required": True
            })
        
        return patterns
    
    def _generate_top_recommendations(self, task_summaries: Dict) -> List[Dict]:
        """Generate top recommendations based on analysis."""
        recommendations = []
        
        for task_type, summary in task_summaries.items():
            if summary.get("status") != "ok":
                continue
            
            rec = summary.get("strategy_recommendation", {})
            if rec and rec.get("confidence", 0) > 0.5:
                recommendations.append({
                    "task_type": task_type,
                    "recommendation": f"Use '{rec.get('best_strategy')}' strategy",
                    "expected_quality": rec.get("expected_quality"),
                    "confidence": rec.get("confidence")
                })
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return recommendations[:5]  # Top 5
    
    def format_report_for_display(self, report: Dict) -> str:
        """Format a report dictionary as readable text."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"PERFORMANCE REPORT - {report.get('generated_at', 'N/A')}")
        lines.append("=" * 60)
        
        if "task_type" in report:
            lines.append(f"\nTask Type: {report['task_type']}")
            lines.append("-" * 40)
            
            if "executions" in report:
                exec_data = report["executions"]
                lines.append(f"Total Executions: {exec_data.get('total', 0)}")
                lines.append(f"Success Rate: {exec_data.get('success_rate', 'N/A')}")
            
            if "token_usage" in report:
                token_data = report["token_usage"]
                lines.append(f"\nToken Usage:")
                lines.append(f"  Average per execution: {token_data.get('avg_per_execution', 0):.0f}")
                lines.append(f"  Trend: {token_data.get('trend', 'unknown')}")
            
            if "strategy_recommendation" in report:
                rec = report["strategy_recommendation"]
                lines.append(f"\nRecommended Strategy: {rec.get('best_strategy', 'default')}")
                lines.append(f"  Confidence: {rec.get('confidence', 0):.0%}")
        
        elif "summary" in report:
            summary = report["summary"]
            lines.append(f"\nOverall Statistics:")
            lines.append(f"  Total Executions: {summary.get('total_executions', 0)}")
            lines.append(f"  Overall Success Rate: {summary.get('overall_success_rate', 0):.1%}")
            lines.append(f"  Task Types Tracked: {summary.get('task_types_tracked', 0)}")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


# Example usage and testing
if __name__ == "__main__":
    print("Testing FeedbackReporter...")
    
    # This would require the full system to be set up
    # For now, just verify import works
    reporter = FeedbackReporter()
    print("FeedbackReporter initialized successfully")
