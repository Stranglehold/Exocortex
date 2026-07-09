#!/usr/bin/env python3
"""Self-Improvement Engine implementing AgentEvolver's three mechanisms."""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Experience:
    """Represents a learning experience for the agent."""
    task_type: str
    task_description: str
    actions: List[str]
    outcome: str  # success, partial_success, failure
    lessons_learned: List[str]
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class Task:
    """Represents a self-generated task for improvement."""
    task_id: str
    description: str
    difficulty: str  # easy, medium, hard
    category: str
    created_at: str
    completed: bool = False
    completion_time: Optional[str] = None
    score: Optional[float] = None


class SelfImprovementEngine:
    """Engine implementing AgentEvolver's self-evolving mechanisms."""
    
    def __init__(self, plugin_dir: Path):
        self.plugin_dir = plugin_dir
        self.data_dir = plugin_dir / "data"
        self.experiences_file = self.data_dir / "experiences.json"
        self.tasks_file = self.data_dir / "tasks.json"
        self.stats_file = self.data_dir / "stats.json"
        
        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize data structures
        self.experiences: List[Experience] = []
        self.tasks: List[Task] = []
        self.stats: Dict[str, Any] = {
            "total_experiences": 0,
            "total_tasks": 0,
            "tasks_completed": 0,
            "success_rate": 0.0,
            "last_updated": datetime.now().isoformat()
        }
        
        self._load_data()
    
    def _load_data(self):
        """Load existing data from files."""
        # Load experiences
        if self.experiences_file.exists():
            try:
                with open(self.experiences_file, 'r') as f:
                    data = json.load(f)
                    self.experiences = [Experience(**exp) for exp in data]
            except Exception as e:
                logger.error(f"Error loading experiences: {e}")
                self.experiences = []
        
        # Load tasks
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    data = json.load(f)
                    self.tasks = [Task(**task) for task in data]
            except Exception as e:
                logger.error(f"Error loading tasks: {e}")
                self.tasks = []
        
        # Load stats
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    self.stats = json.load(f)
            except Exception as e:
                logger.error(f"Error loading stats: {e}")
        
        self._update_stats()
    
    def _save_data(self):
        """Save data to files."""
        # Save experiences
        with open(self.experiences_file, 'w') as f:
            json.dump([asdict(exp) for exp in self.experiences], f, indent=2)
        
        # Save tasks
        with open(self.tasks_file, 'w') as f:
            json.dump([asdict(task) for task in self.tasks], f, indent=2)
        
        # Save stats
        self.stats["last_updated"] = datetime.now().isoformat()
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def _update_stats(self):
        """Update statistics based on current data."""
        self.stats["total_experiences"] = len(self.experiences)
        self.stats["total_tasks"] = len(self.tasks)
        self.stats["tasks_completed"] = len([t for t in self.tasks if t.completed])
        
        if self.experiences:
            successes = len([e for e in self.experiences if e.outcome == "success"])
            self.stats["success_rate"] = successes / len(self.experiences)
    
    # Self-Questioning Mechanism
    def generate_task(self, category: str = "general", difficulty: str = "medium") -> Task:
        """Generate a self-improvement task (Self-Questioning)."""
        task_id = f"task_{int(time.time())}_{len(self.tasks)}"
        
        # Simple task generation based on category and difficulty
        tasks_by_category = {
            "coding": [
                "Write a function that implements a binary search algorithm",
                "Create a simple web scraper using requests and BeautifulSoup",
                "Implement a REST API endpoint with error handling",
                "Write unit tests for an existing function",
                "Refactor code to follow PEP 8 guidelines"
            ],
            "research": [
                "Research and summarize the latest developments in AI agents",
                "Compare different vector database technologies",
                "Analyze the performance characteristics of various LLM models",
                "Research best practices for prompt engineering",
                "Study agentic workflow patterns and their applications"
            ],
            "general": [
                "Improve error handling in tool usage",
                "Optimize memory usage during long conversations",
                "Enhance the quality of response formatting",
                "Practice writing clear and concise documentation",
                "Learn a new tool or library relevant to current tasks"
            ]
        }
        
        descriptions = tasks_by_category.get(category, tasks_by_category["general"])
        import random
        description = random.choice(descriptions)
        
        # Adjust description based on difficulty
        if difficulty == "hard":
            description = f"Advanced: {description} with additional constraints and optimizations"
        elif difficulty == "easy":
            description = f"Beginner: {description}"
        
        task = Task(
            task_id=task_id,
            description=description,
            difficulty=difficulty,
            category=category,
            created_at=datetime.now().isoformat()
        )
        
        self.tasks.append(task)
        self._update_stats()
        self._save_data()
        
        logger.info(f"Generated new task: {task_id} - {description}")
        return task
    
    # Self-Navigating Mechanism
    def add_experience(self, task_type: str, task_description: str, 
                      actions: List[str], outcome: str, lessons_learned: List[str],
                      metadata: Optional[Dict[str, Any]] = None) -> Experience:
        """Add a learning experience (Self-Navigating)."""
        experience = Experience(
            task_type=task_type,
            task_description=task_description,
            actions=actions,
            outcome=outcome,
            lessons_learned=lessons_learned,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        self.experiences.append(experience)
        self._update_stats()
        self._save_data()
        
        logger.info(f"Added new experience: {task_type} - {outcome}")
        return experience
    
    def get_relevant_experiences(self, task_type: str, max_results: int = 5) -> List[Experience]:
        """Get relevant past experiences for a task type (Self-Navigating)."""
        relevant = [exp for exp in self.experiences if exp.task_type == task_type]
        
        # Sort by recency (newest first)
        relevant.sort(key=lambda x: x.timestamp, reverse=True)
        
        return relevant[:max_results]
    
    # Self-Attributing Mechanism
    def analyze_actions(self, actions: List[str], outcomes: List[str]) -> Dict[str, float]:
        """Analyze which actions contributed to outcomes (Self-Attributing)."""
        # Simple credit assignment: actions leading to positive outcomes get higher scores
        action_scores = {}
        
        for i, (action, outcome) in enumerate(zip(actions, outcomes)):
            if outcome == "success":
                score = 1.0
            elif outcome == "partial_success":
                score = 0.5
            else:  # failure
                score = 0.0
            
            # Apply temporal discounting (earlier actions get slightly less credit)
            discount = 0.9 ** i
            action_scores[action] = score * discount
        
        return action_scores
    
    def get_improvement_suggestions(self) -> List[str]:
        """Get suggestions for improvement based on past experiences."""
        suggestions = []
        
        # Analyze failure patterns
        failures = [exp for exp in self.experiences if exp.outcome == "failure"]
        if failures:
            common_lessons = set()
            for failure in failures[:3]:  # Look at recent failures
                common_lessons.update(failure.lessons_learned)
            
            if common_lessons:
                suggestions.append(f"Focus on improving: {', '.join(list(common_lessons)[:3])}")
        
        # Suggest task generation based on underrepresented categories
        task_categories = [t.category for t in self.tasks]
        from collections import Counter
        category_counts = Counter(task_categories)
        
        all_categories = {"coding", "research", "general"}
        for category in all_categories:
            if category_counts.get(category, 0) < 2:
                suggestions.append(f"Generate more {category} tasks for balanced learning")
        
        # Suggest based on success rate
        if self.stats["success_rate"] < 0.7 and self.experiences:
            suggestions.append("Consider practicing easier tasks to build confidence")
        
        return suggestions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.stats.copy()
    
    def complete_task(self, task_id: str, score: float = 1.0) -> bool:
        """Mark a task as completed."""
        for task in self.tasks:
            if task.task_id == task_id:
                task.completed = True
                task.completion_time = datetime.now().isoformat()
                task.score = score
                self._update_stats()
                self._save_data()
                return True
        return False
