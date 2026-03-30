"""
StrategyOptimizer - RL-inspired optimization for skill execution

Implements epsilon-greedy exploration/exploitation, Q-value estimation,
and strategy selection based on historical performance data.
Inspired by OpenGauss Atropos framework patterns.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import statistics


@dataclass
class StrategyInfo:
    """Information about a single strategy."""
    name: str
    description: str = ""
    q_value: float = 0.0  # Estimated value (average quality score)
    visit_count: int = 0
    total_reward: float = 0.0
    rewards_history: List[float] = field(default_factory=list)
    last_updated: Optional[str] = None
    
    @property
    def average_reward(self) -> float:
        if self.visit_count == 0:
            return 0.0
        return self.total_reward / self.visit_count
    
    @property
    def reward_stddev(self) -> float:
        if len(self.rewards_history) < 2:
            return 0.0
        return statistics.stdev(self.rewards_history)


class StrategyOptimizer:
    """
    RL-inspired strategy optimizer using epsilon-greedy selection.
    
    Maintains Q-values for different strategies and balances exploration
    vs exploitation based on configurable parameters.
    
    Selection modes:
    - epsilon_greedy: Explore with probability epsilon, exploit otherwise
    - softmax: Probability proportional to exp(q_value / temperature)
    - round_robin: Cycle through strategies evenly (pure exploration)
    - best_only: Always pick highest Q-value (pure exploitation)
    """
    
    def __init__(
        self,
        epsilon: float = 0.1,  # Exploration rate (10%)
        learning_rate: float = 0.1,  # How fast to update Q-values
        gamma: float = 0.9,  # Discount factor for future rewards
        selection_mode: str = "epsilon_greedy",
        temperature: float = 1.0,  # For softmax selection
    ):
        self.epsilon = epsilon
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.selection_mode = selection_mode
        self.temperature = temperature
        
        # Strategy registry: task_type -> {strategy_name -> StrategyInfo}
        self.strategies: Dict[str, Dict[str, StrategyInfo]] = defaultdict(dict)
        
        # Default strategies available
        self.available_strategies = {
            "default": StrategyInfo(
                name="default",
                description="Standard execution without special optimization"
            ),
            "aggressive_caching": StrategyInfo(
                name="aggressive_caching", 
                description="Reuse previous results when possible, minimize fresh computation"
            ),
            "thorough_analysis": StrategyInfo(
                name="thorough_analysis",
                description="Deep analysis with multiple verification steps"
            ),
            "fast_path": StrategyInfo(
                name="fast_path",
                description="Quick execution, minimal tool calls, accept approximations"
            ),
            "iterative_refinement": StrategyInfo(
                name="iterative_refinement",
                description="Start simple, refine based on intermediate results"
            )
        }
    
    def register_strategy(self, name: str, description: str = ""):
        """Register a new strategy."""
        if name not in self.available_strategies:
            self.available_strategies[name] = StrategyInfo(name=name, description=description)
    
    def select_strategy(self, task_type: str, context: Dict = None) -> str:
        """
        Select a strategy for the given task type.
        
        Args:
            task_type: Type of task being executed
            context: Optional context about current execution state
            
        Returns:
            Name of selected strategy
        """
        task_strategies = self.strategies[task_type]
        
        # If no strategies learned yet, return default
        if not task_strategies:
            return "default"
        
        strategy_names = list(task_strategies.keys())
        
        if self.selection_mode == "epsilon_greedy":
            return self._select_epsilon_greedy(strategy_names)
        elif self.selection_mode == "softmax":
            return self._select_softmax(strategy_names)
        elif self.selection_mode == "round_robin":
            return self._select_round_robin(strategy_names, task_type)
        elif self.selection_mode == "best_only":
            return self._select_best(strategy_names)
        else:
            return "default"
    
    def _select_epsilon_greedy(self, strategy_names: List[str]) -> str:
        """Epsilon-greedy selection."""
        if random.random() < self.epsilon:
            # Explore: pick random strategy
            return random.choice(strategy_names)
        else:
            # Exploit: pick best known strategy
            return self._select_best(strategy_names)
    
    def _select_softmax(self, strategy_names: List[str]) -> str:
        """Softmax selection based on Q-values."""
        import math
        
        q_values = [self.strategies[task_type][s].q_value for s in strategy_names]
        
        # Avoid division by zero
        if self.temperature <= 0:
            return self._select_best(strategy_names)
        
        # Calculate softmax probabilities
        exp_values = [math.exp(q / self.temperature) for q in q_values]
        sum_exp = sum(exp_values)
        probs = [e / sum_exp for e in exp_values]
        
        # Sample from distribution
        r = random.random()
        cumulative = 0
        for i, prob in enumerate(probs):
            cumulative += prob
            if r < cumulative:
                return strategy_names[i]
        
        return strategy_names[-1]
    
    def _select_round_robin(self, strategy_names: List[str], task_type: str) -> str:
        """Round-robin selection for pure exploration."""
        # Use visit counts to determine next
        visits = [(s, self.strategies[task_type][s].visit_count) for s in strategy_names]
        visits.sort(key=lambda x: x[1])
        return visits[0][0]  # Return least visited
    
    def _select_best(self, strategy_names: List[str]) -> str:
        """Select strategy with highest Q-value."""
        if not strategy_names:
            return "default"
        
        best_strategy = max(
            strategy_names,
            key=lambda s: self.strategies[task_type][s].q_value
        )
        return best_strategy
    
    def update_q_value(self, task_type: str, strategy: str, reward: float):
        """
        Update Q-value for a strategy after receiving reward.
        
        Uses temporal difference learning:
        Q_new = Q_old + learning_rate * (reward - Q_old)
        
        Args:
            task_type: Type of task
            strategy: Strategy that was used
            reward: Reward signal (typically quality_score 0-1)
        """
        # Ensure strategy exists for this task type
        if strategy not in self.strategies[task_type]:
            if strategy in self.available_strategies:
                self.strategies[task_type][strategy] = StrategyInfo(
                    name=strategy,
                    description=self.available_strategies[strategy].description
                )
            else:
                self.strategies[task_type][strategy] = StrategyInfo(name=strategy)
        
        strategy_info = self.strategies[task_type][strategy]
        
        # Calculate TD error
        td_error = reward - strategy_info.q_value
        
        # Update Q-value
        strategy_info.q_value += self.learning_rate * td_error
        
        # Update statistics
        strategy_info.visit_count += 1
        strategy_info.total_reward += reward
        strategy_info.rewards_history.append(reward)
        
        # Keep history bounded
        if len(strategy_info.rewards_history) > 100:
            strategy_info.rewards_history = strategy_info.rewards_history[-100:]
    
    def get_strategy_stats(self, task_type: str) -> Dict[str, Dict]:
        """Get statistics for all strategies of a task type."""
        stats = {}
        for name, info in self.strategies.get(task_type, {}).items():
            stats[name] = {
                "q_value": round(info.q_value, 3),
                "visit_count": info.visit_count,
                "avg_reward": round(info.average_reward, 3),
                "reward_stddev": round(info.reward_stddev, 3)
            }
        return stats
    
    def get_recommendation(self, task_type: str) -> Dict:
        """
        Get recommendation for optimal strategy on a task type.
        
        Returns dict with:
        - best_strategy: Name of recommended strategy
        - confidence: How confident we are (based on visit count)
        - expected_quality: Expected quality score
        - alternatives: Other viable strategies
        """
        stats = self.get_strategy_stats(task_type)
        
        if not stats:
            return {
                "best_strategy": "default",
                "confidence": 0.0,
                "expected_quality": 0.5,
                "alternatives": [],
                "reasoning": "No data available, using default"
            }
        
        # Sort strategies by Q-value
        sorted_strategies = sorted(
            stats.items(),
            key=lambda x: x[1]["q_value"],
            reverse=True
        )
        
        best_name = sorted_strategies[0][0]
        best_stats = sorted_strategies[0][1]
        
        # Calculate confidence based on visit count
        max_confidence = 1.0
        min_visits_for_confidence = 10
        confidence = min(max_confidence, best_stats["visit_count"] / min_visits_for_confidence)
        
        # Find alternatives (within 10% of best)
        threshold = best_stats["q_value"] * 0.9
        alternatives = [
            name for name, s in sorted_strategies[1:]
            if s["q_value"] >= threshold
        ]
        
        return {
            "best_strategy": best_name,
            "confidence": round(confidence, 2),
            "expected_quality": round(best_stats["q_value"], 3),
            "alternatives": alternatives,
            "reasoning": f"Based on {best_stats['visit_count']} executions with avg quality {best_stats['avg_reward']:.2f}"
        }
    
    def get_all_recommendations(self) -> Dict[str, Dict]:
        """Get recommendations for all task types."""
        return {
            task_type: self.get_recommendation(task_type)
            for task_type in self.strategies.keys()
        }


# Example usage and testing
if __name__ == "__main__":
    print("Testing StrategyOptimizer...")
    
    optimizer = StrategyOptimizer(epsilon=0.1, learning_rate=0.1)
    
    # Simulate learning from executions
    task_type = "research"
    strategies = ["default", "thorough_analysis", "fast_path"]
    
    for i in range(50):
        # Select strategy
        selected = optimizer.select_strategy(task_type)
        
        # Simulate reward based on strategy (with noise)
        base_rewards = {
            "default": 0.7,
            "thorough_analysis": 0.85,
            "fast_path": 0.6
        }
        import random
        reward = base_rewards.get(selected, 0.7) + random.uniform(-0.1, 0.1)
        reward = max(0, min(1, reward))
        
        # Update Q-value
        optimizer.update_q_value(task_type, selected, reward)
    
    print("\nStrategy Stats:")
    import json
    print(json.dumps(optimizer.get_strategy_stats(task_type), indent=2))
    
    print("\nRecommendation:")
    print(json.dumps(optimizer.get_recommendation(task_type), indent=2))
