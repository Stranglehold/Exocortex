"""
Tool Call Tracker — Companion to _09_methodology_tracker
========================================================
Hook: tool_execute_after (_32_)

Records each tool call (name + success/failure) onto the agent's
methodology cycle data. Lightweight — one dict append per tool call.

Must live in tool_execute_after/ alongside _31_failure_lesson_capture.
Runs AFTER _31 so the error diagnosis is already set.
"""

from agent import LoopData
from helpers.extension import Extension

# Import the record function from the methodology tracker
import importlib
import sys
import os

def _get_tracker_module():
    """Dynamically import the methodology tracker's record_tool function."""
    try:
        # The tracker lives in message_loop_prompts_after/_09_
        tracker_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "message_loop_prompts_after"
        )
        if tracker_dir not in sys.path:
            sys.path.insert(0, tracker_dir)
        mod = importlib.import_module("_09_methodology_tracker")
        return mod
    except Exception:
        return None


class ToolCallTracker(Extension):
    """tool_execute_after: record tool call in methodology cycle data."""

    async def execute(self, response=None, **kwargs) -> None:
        try:
            tool_name = kwargs.get("tool_name") or "unknown"
            if tool_name == "response":
                return  # skip the final response "tool"

            # Determine success: if _error_diagnosis is set, this call failed
            diag = self.agent.get_data("_error_diagnosis")
            success = not (isinstance(diag, dict) and diag.get("error_class"))

            # Record on the methodology tracker's cycle data
            tracker = _get_tracker_module()
            if tracker and hasattr(tracker, "record_tool"):
                tracker.record_tool(self.agent, tool_name, success)

        except Exception as e:
            # Never break a cycle on tracking failure
            print(f"[TOOL-TRACK] Error (passthrough): {e}", flush=True)
