from helpers.extension import Extension
from agent import Agent, LoopData

# Warning thresholds as fraction of total window
WARN_THRESHOLD     = 0.70   # log warning at 70%
CRITICAL_THRESHOLD = 0.85   # log critical at 85%

# THE TWO params_temporary WRITES ARE RETIRED (2026-09-19, Opus's ruling).
#
# This block used to define UTILIZATION_KEY / TOKEN_COUNT_KEY and the execute() body wrote
# both into loop_data.params_temporary. Nothing ever read them: verified 2026-08-22 by
# scripts/scan_severed_loops.py, re-verified 2026-09-19 with a grep over the whole
# container -- the only occurrences of either string anywhere under /a0 were these two
# definitions, and all 89 params_temporary references ask for one named key
# (log_item_generating / log_item_response), never iterating the dict.
#
# The question "wire a consumer, or delete the writes?" was raised with Opus on
# 2026-08-22 and this file recorded that if the answer came back 'no consumer wanted',
# the writes should go. It came back on 2026-09-19: build the consumer FIRST if context
# utilization becomes useful, then add the writes. Dead writes stay dead until someone
# has a reason to read them.
#
# KEPT ON THE RECORD because it is the defect this file already caught once: the comment
# here originally read "Other extensions (e.g. supervisor loop) can read these". The
# supervisor did not, and never had. A COMMENT NAMING A CONSUMER IS NOT A CONSUMER, and
# that one made the gap invisible to every reader for months.
#
# The watchdog itself is NOT retired -- the WARN/CRITICAL logging below is live output.


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
