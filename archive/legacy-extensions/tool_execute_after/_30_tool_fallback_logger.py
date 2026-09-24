import re
from helpers.extension import Extension
from helpers.tool import Response

FAILURES_KEY = "_tool_failures"
FORMAT_TRACKER_KEY = "_failure_tracker"  # Owned by error_format/_30_failure_tracker.py
OUTPUT_TRACKER_KEY = "_tool_output_tracker"  # Successful output hashes for stagnation detection
MAX_HISTORY = 20
MAX_OUTPUT_HISTORY = 8  # Rolling window for stagnation detection

SUCCESS_INDICATORS = [
    r"(?i)successfully installed",
    r"(?i)successfully built",
    r"(?i)requirement already satisfied",
    r"(?i)already installed",
    r"(?i)is up to date",
    r"(?i)install complete",
    r"(?i)done\.\s*$",
    r"(?i)^ok\b",
    r"(?i)setting up \S+",
    r"(?i)unpacking \S+",
    r"(?i)processing triggers",
    r"(?i)created wheel for",
    r"(?i)stored in directory:",
]

ERROR_PATTERNS = [
    (r"(?i)timeout|timed?\s*out|deadline exceeded|connection.*reset", "timeout"),
    (r"(?i)not found|no such file|does not exist|404|command not found|unknown tool", "not_found"),
    (r"(?i)permission denied|access denied|forbidden|403|unauthorized|401", "permission"),
    (r"(?i)syntax error|invalid argument|unexpected token|parse error|malformed|missing required", "syntax"),
    (r"(?i)connection refused|network unreachable|DNS|ECONNREFUSED|could not resolve", "network"),
    (r"(?i)out of memory|disk full|no space left|quota exceeded|resource exhausted", "resource"),
    (r"(?i)no module named|import error|ModuleNotFoundError|package.*not installed", "dependency"),
    (r"(?i)^ERROR:|^error:|Traceback \(most recent|raise \w+Error|FATAL|CRITICAL", "execution"),
]


class ToolFallbackLogger(Extension):
    """Classifies tool execution results and logs failures for the fallback advisor.

    Key change from original: history is cleared on success, providing
    natural decay so the fallback advisor doesn't fire indefinitely
    after a sequence of resolved errors.
    """

    async def execute(self, response: Response | None = None, **kwargs):
        try:
            if not response:
                return

            tool_name = kwargs.get("tool_name", "")
            if not tool_name:
                return

            # Check if error comprehension already diagnosed this
            diagnosis = self.agent.get_data("_error_diagnosis")
            if diagnosis and diagnosis.get("error_class"):
                error_type = diagnosis["error_class"]
            else:
                error_type = self._classify_response(response.message)

            failures = self.agent.get_data(FAILURES_KEY) or {}
            if "history" not in failures:
                failures["history"] = []
            if "consecutive" not in failures:
                failures["consecutive"] = {}

            if not error_type:
                # Phase 3: read prev failures before resetting — for success profile buffering.
                # Capture the count that just resolved so the supervisor can record
                # (tool_name, domain, failures_before_success) as a learning datapoint.
                prev_failures = failures["consecutive"].get(tool_name, 0)
                failures["consecutive"][tool_name] = 0
                # Don't clear history on response tool — it's a terminal action,
                # not a task success. History should only clear when actual work succeeds.
                if tool_name != "response":
                    failures["history"] = []
                    # Clear supervisor warning flag — failure cycle is over.
                    try:
                        self.agent.set_data("_supervisor_warned", False)
                    except Exception:
                        pass
                self.agent.set_data(FAILURES_KEY, failures)
                # Reset format failure counter — reflection prompts shouldn't persist after recovery
                tracker = self.agent.get_data(FORMAT_TRACKER_KEY) or {}
                if tracker.get(tool_name, 0) > 0:
                    tracker[tool_name] = 0
                    self.agent.set_data(FORMAT_TRACKER_KEY, tracker)
                # Track successful output hash for stagnation detection.
                # Only track actual work tools — response is a terminal action, not progress.
                if tool_name != "response" and response.message:
                    try:
                        output_tracker = self.agent.get_data(OUTPUT_TRACKER_KEY) or []
                        output_tracker.append({
                            "tool": tool_name,
                            "output_hash": hash(response.message[:500]),
                            "status": "success",
                        })
                        if len(output_tracker) > MAX_OUTPUT_HISTORY:
                            output_tracker = output_tracker[-MAX_OUTPUT_HISTORY:]
                        self.agent.set_data(OUTPUT_TRACKER_KEY, output_tracker)
                    except Exception:
                        pass
                # Phase 3: buffer success episode for profile store.
                # Only when there were actual failures to learn from (prev_failures >= 1).
                # The supervisor processes this buffer every 3 turns and records the
                # (tool_name, primary_domain, failures_before_success) observation.
                if prev_failures >= 1 and tool_name != "response":
                    try:
                        buffer = self.agent.get_data("_success_episode_buffer") or []
                        bst_store = getattr(self.agent, "_bst_store", {}) or {}
                        compound_sig = bst_store.get("_compound_sig", "")
                        buffer.append({
                            "tool_name": tool_name,
                            "failure_count": prev_failures,
                            "compound_domain": compound_sig,
                        })
                        self.agent.set_data("_success_episode_buffer", buffer)
                    except Exception:
                        pass
                return

            failures["history"].append({
                "tool": tool_name,
                "error_type": error_type,
                "message_preview": response.message[:150],
            })

            if len(failures["history"]) > MAX_HISTORY:
                failures["history"] = failures["history"][-MAX_HISTORY:]

            prev = failures["consecutive"].get(tool_name, 0)
            failures["consecutive"][tool_name] = prev + 1

            self.agent.set_data(FAILURES_KEY, failures)

        except Exception:
            pass

    def _classify_response(self, message: str) -> str | None:
        if not message:
            return None

        for pattern in SUCCESS_INDICATORS:
            if re.search(pattern, message):
                return None

        for pattern, error_type in ERROR_PATTERNS:
            if re.search(pattern, message):
                return error_type

        return None
