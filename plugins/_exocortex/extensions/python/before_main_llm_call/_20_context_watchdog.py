from helpers.extension import Extension
from agent import Agent, LoopData

# Warning thresholds as fraction of total window
WARN_THRESHOLD     = 0.70   # log warning at 70%
CRITICAL_THRESHOLD = 0.85   # log critical at 85%

# Keys for storing utilization in params_temporary.
#
# NOTHING READS THESE. Verified 2026-08-22 by scripts/scan_severed_loops.py and confirmed
# with a grep over the whole container: the only occurrences of either string anywhere
# under /a0 are these two definitions. The comment here previously read "Other extensions
# (e.g. supervisor loop) can read these" — the supervisor does not, and never has. A
# comment naming a consumer is not a consumer, and this one made the gap invisible to
# every reader since.
#
# They are also written to params_temporary, which A0 clears every iteration
# (agent.py:404) and reads only for `log_item_generating` (agent.py:498/515) — so even a
# future reader must run in the SAME iteration, at a later hook than
# before_main_llm_call.
#
# This extension is not inert: the WARN/CRITICAL logging below is its live output. Only
# this channel is dead. Left in place rather than deleted because wiring the supervisor to
# consume utilization is a capability decision, not a cleanup — raised with Opus
# 2026-08-22. If the answer is "no consumer wanted", delete these two writes.
UTILIZATION_KEY = "context_utilization"
TOKEN_COUNT_KEY = "context_token_count"


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

        # Read from Agent Zero's live model config — same source as history.py.
        # The supervisor sets this at session start via get_chat_model_config().
        # Fall back to get_chat_model_config(), then A0 settings if still not set.
        window_size = self.agent.get_data("context_window_size")
        if not window_size:
            try:
                from plugins._model_config.helpers.model_config import get_chat_model_config
                window_size = int(get_chat_model_config(self.agent).get("ctx_length", 0))
            except Exception:
                pass
        if not window_size:
            try:
                # Per-agent config had no ctx_length — fall back to global plugin config.
                from plugins._model_config.helpers.model_config import get_config
                window_size = int(get_config().get("chat_model", {}).get("ctx_length", 0))
            except Exception:
                pass
        if not window_size:
            return  # Can't determine window size — skip rather than use wrong number

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
