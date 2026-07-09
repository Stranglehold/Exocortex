#!/usr/bin/env python3
"""Test script for AgentEvolver Self-Improvement plugin."""

import sys
import json
from pathlib import Path

# Add plugin directory to path for imports
plugin_dir = Path(__file__).parent
sys.path.insert(0, str(plugin_dir))

def test_self_improvement_engine():
    """Test the SelfImprovementEngine class."""
    print("Testing SelfImprovementEngine...")
    
    from helpers.self_improvement import SelfImprovementEngine
    
    engine = SelfImprovementEngine(plugin_dir)
    
    # Test generating a task
    task = engine.generate_task(category="coding", difficulty="medium")
    print(f"  Generated task: {task.description}")
    
    # Test adding an experience
    experience = engine.add_experience(
        task_type="coding",
        task_description="Write a binary search function",
        actions=["Write function", "Test function", "Debug"],
        outcome="success",
        lessons_learned=["Use iterative approach for binary search", "Test edge cases"]
    )
    print(f"  Added experience: {experience.task_type} - {experience.outcome}")
    
    # Test getting relevant experiences
    experiences = engine.get_relevant_experiences("coding", max_results=3)
    print(f"  Found {len(experiences)} relevant experiences")
    
    # Test analyzing actions
    actions = ["plan", "execute", "review"]
    outcomes = ["success", "partial_success", "failure"]
    action_scores = engine.analyze_actions(actions, outcomes)
    print(f"  Action scores: {action_scores}")
    
    # Test getting improvement suggestions
    suggestions = engine.get_improvement_suggestions()
    print(f"  Improvement suggestions: {suggestions}")
    
    # Test getting stats
    stats = engine.get_stats()
    print(f"  Stats: {stats}")
    
    # Test completing the task
    if engine.complete_task(task.task_id, score=0.9):
        print(f"  Completed task: {task.task_id}")
    else:
        print(f"  Failed to complete task: {task.task_id}")
    
    print("SelfImprovementEngine tests passed!\n")
    return True

def test_self_questioning_tool():
    """Test the SelfQuestioningTool class."""
    print("Testing SelfQuestioningTool...")
    
    from tools.self_questioning_tool import SelfQuestioningTool
    
    tool = SelfQuestioningTool(plugin_dir)
    
    # Test generate_task
    result = tool.generate_task(category="research", difficulty="easy")
    print(f"  Tool generated task: {result['message']}")
    task_id = result["task_id"]
    
    # Test add_experience
    result = tool.add_experience(
        task_type="research",
        task_description="Research AI agent frameworks",
        actions=["Search", "Read", "Summarize"],
        outcome="success",
        lessons_learned=["Found multiple frameworks", "Identified key features"]
    )
    print(f"  Tool added experience: {result['message']}")
    
    # Test get_relevant_experiences
    result = tool.get_relevant_experiences("research")
    print(f"  Tool got experiences: {result['message']}")
    
    # Test analyze_actions
    result = tool.analyze_actions(
        actions=["plan", "execute"],
        outcomes=["success", "success"]
    )
    print(f"  Tool analyzed actions: {result['message']}")
    
    # Test get_improvement_suggestions
    result = tool.get_improvement_suggestions()
    print(f"  Tool got suggestions: {result['message']}")
    if result["suggestions"]:
        for suggestion in result["suggestions"]:
            print(f"    - {suggestion}")
    
    # Test get_stats
    result = tool.get_stats()
    print(f"  Tool got stats: {result['message']}")
    print(f"    Stats: {json.dumps(result['stats'], indent=2)}")
    
    # Test complete_task
    result = tool.complete_task(task_id, score=0.8)
    print(f"  Tool completed task: {result['message']}")
    
    # Test list_tasks
    result = tool.list_tasks(completed=False)
    print(f"  Tool listed tasks: {result['message']}")
    
    print("SelfQuestioningTool tests passed!\n")
    return True

def main():
    """Run all tests."""
    print("=== Starting AgentEvolver Self-Improvement Plugin Tests ===\n")
    
    try:
        test_self_improvement_engine()
        test_self_questioning_tool()
        
        print("=== All tests passed! ===")
        print("Plugin structure:")
        print(f"  Plugin directory: {plugin_dir}")
        print("  Created files:")
        for file in plugin_dir.rglob("*"):
            if file.is_file():
                print(f"    - {file.relative_to(plugin_dir)}")
        
        return 0
    except Exception as e:
        print(f"\n!!! Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())