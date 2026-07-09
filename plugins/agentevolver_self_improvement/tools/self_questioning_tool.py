#!/usr/bin/env python3
"""Self-Questioning Tool for AgentEvolver Self-Improvement plugin."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from helpers.self_improvement import SelfImprovementEngine, Experience, Task

logger = logging.getLogger(__name__)


class SelfQuestioningTool:
    """Tool for self-improvement using AgentEvolver mechanisms."""
    
    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.engine = SelfImprovementEngine(plugin_dir)
    
    def generate_task(self, category: str = "general", difficulty: str = "medium") -> Dict[str, Any]:
        """Generate a self-improvement task."""
        task = self.engine.generate_task(category, difficulty)
        return {
            "task_id": task.task_id,
            "description": task.description,
            "difficulty": task.difficulty,
            "category": task.category,
            "created_at": task.created_at,
            "message": f"Generated new {difficulty} task in category '{category}': {task.description}"
        }
    
    def add_experience(self, task_type: str, task_description: str, 
                      actions: List[str], outcome: str, lessons_learned: List[str],
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a learning experience."""
        experience = self.engine.add_experience(
            task_type=task_type,
            task_description=task_description,
            actions=actions,
            outcome=outcome,
            lessons_learned=lessons_learned,
            metadata=metadata
        )
        return {
            "experience_id": f"exp_{experience.timestamp}",
            "task_type": experience.task_type,
            "outcome": experience.outcome,
            "lessons_learned": experience.lessons_learned,
            "timestamp": experience.timestamp,
            "message": f"Added experience for task type '{task_type}' with outcome '{outcome}'"
        }
    
    def get_relevant_experiences(self, task_type: str, max_results: int = 5) -> Dict[str, Any]:
        """Get relevant past experiences."""
        experiences = self.engine.get_relevant_experiences(task_type, max_results)
        return {
            "task_type": task_type,
            "experiences": [
                {
                    "task_description": exp.task_description,
                    "outcome": exp.outcome,
                    "lessons_learned": exp.lessons_learned,
                    "timestamp": exp.timestamp
                }
                for exp in experiences
            ],
            "count": len(experiences),
            "message": f"Found {len(experiences)} relevant experiences for task type '{task_type}'"
        }
    
    def analyze_actions(self, actions: List[str], outcomes: List[str]) -> Dict[str, Any]:
        """Analyze which actions contributed to outcomes."""
        action_scores = self.engine.analyze_actions(actions, outcomes)
        return {
            "action_scores": action_scores,
            "message": f"Analyzed {len(actions)} actions, assigned scores based on outcomes"
        }
    
    def get_improvement_suggestions(self) -> Dict[str, Any]:
        """Get suggestions for improvement."""
        suggestions = self.engine.get_improvement_suggestions()
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "message": f"Generated {len(suggestions)} improvement suggestions"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        stats = self.engine.get_stats()
        return {
            "stats": stats,
            "message": "Retrieved self-improvement statistics"
        }
    
    def complete_task(self, task_id: str, score: float = 1.0) -> Dict[str, Any]:
        """Mark a task as completed."""
        success = self.engine.complete_task(task_id, score)
        if success:
            return {
                "task_id": task_id,
                "completed": True,
                "score": score,
                "message": f"Task {task_id} marked as completed with score {score}"
            }
        else:
            return {
                "task_id": task_id,
                "completed": False,
                "message": f"Task {task_id} not found"
            }
    
    def list_tasks(self, completed: Optional[bool] = None, category: Optional[str] = None) -> Dict[str, Any]:
        """List tasks with optional filtering."""
        tasks = self.engine.tasks
        
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if category is not None:
            tasks = [t for t in tasks if t.category == category]
        
        return {
            "tasks": [
                {
                    "task_id": t.task_id,
                    "description": t.description,
                    "difficulty": t.difficulty,
                    "category": t.category,
                    "created_at": t.created_at,
                    "completed": t.completed,
                    "completion_time": t.completion_time,
                    "score": t.score
                }
                for t in tasks
            ],
            "count": len(tasks),
            "message": f"Found {len(tasks)} tasks matching filters"
        }


# Tool registration function
def register_tools(plugin_dir: Path):
    """Register the tool with the Agent Zero framework."""
    tool_instance = SelfQuestioningTool(plugin_dir)
    
    # Return a dictionary of tool names to functions
    return {
        "self_questioning_generate_task": tool_instance.generate_task,
        "self_questioning_add_experience": tool_instance.add_experience,
        "self_questioning_get_relevant_experiences": tool_instance.get_relevant_experiences,
        "self_questioning_analyze_actions": tool_instance.analyze_actions,
        "self_questioning_get_improvement_suggestions": tool_instance.get_improvement_suggestions,
        "self_questioning_get_stats": tool_instance.get_stats,
        "self_questioning_complete_task": tool_instance.complete_task,
        "self_questioning_list_tasks": tool_instance.list_tasks,
    }
