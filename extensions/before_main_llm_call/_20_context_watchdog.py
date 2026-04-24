import json
import os

from helpers.extension import Extension
from agent import Agent, LoopData

# Fallback when no config exists and agent hasn't set context_window_size.
# Override in /a0/usr/Exocortex/config.json: {"context_watchdog": {"context_window_tokens": 65536}}
# Or at runtime: agent.set_data("context_window_size", N)
_DEFAULT_CONTEXT_WINDOW = 65536

# Warning thresholds as fraction of total window
WARN_THRESHOLD     = 0.70   # log warning at 70%
CRITICAL_THRESHOLD = 0.85   # log critical at 85%

# Keys for storing utilization in params_temporary
# Other extensions (e.g. supervisor loop) can read these
UTILIZATION_KEY = "context_utilization"
TOKEN_COUNT_KEY = "context_token_count"

_CONFIG_PATH = "/a0/usr/Exocortex/config.json"
_CONFIG_KEY  = "context_watchdog"


def _load_window_size() -> int:
    """Read context_window_tokens from Exocortex config. Falls back to default."""
    try:
        if os.path.isfile(_CONFIG_PATH):
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            v = cfg.get(_CONFIG_KEY, {}).get("context_window_tokens")
            if isinstance(v, int) and v > 0:
                return v
    except Exception:
        pass
    return _DEFAULT_CONTEXT_WINDOW


# Cache at module load — window size doesn't change mid-session
_CONFIGURED_WINDOW = _load_window_size()


class ContextWatchdog(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Read token count from agent-zero's own ctx_window store.
        # Computed by prepare_prompt() on the previous iteration from the
        # actual assembled prompt — more accurate than approximating components.
        ctx_window_data = self.agent.get_data(Agent.DATA_NAME_CTX_WINDOW)

        if not ctx_window_data:
            return  # No data yet (first iteration) — skip

        total_tokens = ctx_window_data.get("tokens", 0)
        if not total_tokens:
            return

        # Priority: runtime override > Exocortex config > module default
        window_size = (
            self.agent.get_data("context_window_size")
            or _CONFIGURED_WINDOW
        )

        utilization = total_tokens / window_size

        # Store for other extensions to read this iteration
        loop_data.params_temporary[UTILIZATION_KEY] = utilization
        loop_data.params_temporary[TOKEN_COUNT_KEY] = total_tokens

        if utilization >= CRITICAL_THRESHOLD:
            msg = (
                f"[CONTEXT CRITICAL] {total_tokens:,} / {window_size:,} tokens "
                f"({utilization:.0%}) — approaching limit. "
                f"Responses may degrade. Consider /reset or summarizing history."
            )
            self.agent.context.log.log(type="warning", content=msg)
            from helpers.print_style import PrintStyle
            PrintStyle(font_color="red", padding=True).print(msg)

        elif utilization >= WARN_THRESHOLD:
            msg = (
                f"[CONTEXT WARNING] {total_tokens:,} / {window_size:,} tokens "
                f"({utilization:.0%}) — context filling."
            )
            self.agent.context.log.log(type="warning", content=msg)
            from helpers.print_style import PrintStyle
            PrintStyle(font_color="orange", padding=False).print(msg)
