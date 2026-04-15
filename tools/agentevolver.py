"""
AgentEvolver Self-Improvement Tools — Agent Zero wrapper
=========================================================
Wraps the AgentEvolver plugin's SelfImprovementEngine (self_questioning,
self_navigating, self_attributing) in standard A0 Tool subclasses so they
appear in TOOL-REG and are callable by name.

Tools exposed:
  self_improvement_generate_task       — generate a practice task
  self_improvement_record_experience   — record what happened after a task
  self_improvement_get_experiences     — query past experiences by type
  self_improvement_get_suggestions     — get improvement suggestions from engine
  self_improvement_get_stats           — current database stats
"""

import sys
from pathlib import Path
from helpers.tool import Tool, Response

# ── Engine loader ─────────────────────────────────────────────────────────────

_PLUGIN_DIR = Path("/a0/usr/plugins/agentevolver_self_improvement")
_ENGINE = None


def _get_engine():
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    helpers_path = str(_PLUGIN_DIR / "helpers")
    if helpers_path not in sys.path:
        sys.path.insert(0, helpers_path)
    from self_improvement import SelfImprovementEngine
    _ENGINE = SelfImprovementEngine(_PLUGIN_DIR)
    return _ENGINE


# ── Tools ─────────────────────────────────────────────────────────────────────

class SelfImprovementGenerateTask(Tool):
    """Generate a self-improvement practice task. Args: category (str), difficulty (easy/medium/hard)."""

    async def execute(self, **kwargs) -> Response:
        category = self.args.get("category", "general").strip()
        difficulty = self.args.get("difficulty", "medium").strip()
        try:
            engine = _get_engine()
            task = engine.generate_task(category, difficulty)
            msg = (
                f"Generated task [{task.task_id}]\n"
                f"Category: {task.category} | Difficulty: {task.difficulty}\n"
                f"Description: {task.description}"
            )
            return Response(message=msg, break_loop=False)
        except Exception as e:
            return Response(message=f"self_improvement_generate_task error: {e}", break_loop=False)


class SelfImprovementRecordExperience(Tool):
    """Record a learning experience after completing a task.
    Args: task_type (str), task_description (str), actions (list[str]),
          outcome (success/partial_success/failure), lessons_learned (list[str])."""

    async def execute(self, **kwargs) -> Response:
        try:
            engine = _get_engine()
            task_type = self.args.get("task_type", "general")
            task_desc = self.args.get("task_description", "")
            actions = self.args.get("actions", [])
            outcome = self.args.get("outcome", "success")
            lessons = self.args.get("lessons_learned", [])
            if isinstance(actions, str):
                actions = [a.strip() for a in actions.split(",") if a.strip()]
            if isinstance(lessons, str):
                lessons = [l.strip() for l in lessons.split(",") if l.strip()]
            exp = engine.add_experience(
                task_type=task_type,
                task_description=task_desc,
                actions=actions,
                outcome=outcome,
                lessons_learned=lessons,
            )
            stats = engine.get_stats()
            msg = (
                f"Experience recorded: {task_type} | {outcome}\n"
                f"Lessons: {'; '.join(lessons)}\n"
                f"Database now has {stats.get('total_experiences', '?')} experiences "
                f"({stats.get('success_rate', 0)*100:.0f}% success rate)"
            )
            return Response(message=msg, break_loop=False)
        except Exception as e:
            return Response(message=f"self_improvement_record_experience error: {e}", break_loop=False)


class SelfImprovementGetExperiences(Tool):
    """Query past experiences by task type. Args: task_type (str), max_results (int, default 5)."""

    async def execute(self, **kwargs) -> Response:
        task_type = self.args.get("task_type", "general")
        max_results = int(self.args.get("max_results", 5))
        try:
            engine = _get_engine()
            experiences = engine.get_relevant_experiences(task_type, max_results)
            if not experiences:
                return Response(message=f"No experiences found for task_type '{task_type}'", break_loop=False)
            lines = [f"Found {len(experiences)} experience(s) for '{task_type}':"]
            for i, exp in enumerate(experiences, 1):
                lines.append(f"\n[{i}] {exp.task_description} → {exp.outcome}")
                if exp.lessons_learned:
                    lines.append(f"    Lessons: {'; '.join(exp.lessons_learned)}")
            return Response(message="\n".join(lines), break_loop=False)
        except Exception as e:
            return Response(message=f"self_improvement_get_experiences error: {e}", break_loop=False)


class SelfImprovementGetSuggestions(Tool):
    """Get improvement suggestions based on accumulated experiences. No args required."""

    async def execute(self, **kwargs) -> Response:
        try:
            engine = _get_engine()
            suggestions = engine.get_improvement_suggestions()
            if not suggestions:
                return Response(message="No improvement suggestions yet — need more experience data.", break_loop=False)
            lines = [f"Improvement suggestions ({len(suggestions)}):"]
            for i, s in enumerate(suggestions, 1):
                lines.append(f"  {i}. {s}")
            return Response(message="\n".join(lines), break_loop=False)
        except Exception as e:
            return Response(message=f"self_improvement_get_suggestions error: {e}", break_loop=False)


class SelfImprovementGetStats(Tool):
    """Get self-improvement database stats. No args required."""

    async def execute(self, **kwargs) -> Response:
        try:
            engine = _get_engine()
            stats = engine.get_stats()
            msg = (
                f"Self-improvement stats:\n"
                f"  Experiences: {stats.get('total_experiences', 0)}\n"
                f"  Tasks generated: {stats.get('total_tasks', 0)}\n"
                f"  Tasks completed: {stats.get('tasks_completed', 0)}\n"
                f"  Success rate: {stats.get('success_rate', 0)*100:.0f}%\n"
                f"  Last updated: {stats.get('last_updated', 'never')}"
            )
            return Response(message=msg, break_loop=False)
        except Exception as e:
            return Response(message=f"self_improvement_get_stats error: {e}", break_loop=False)
