"""
Clear Generating Content — Raw JSON Display Fix
===============================================
Hook: response_stream_end (_20_)

At stream end, _10_log_from_stream (response_stream hook) has set
log_item_generating.content = full_raw_json. The webUI renders this
as visible raw text in the chat for every tool call turn.

The structured display (thoughts, headline, tool args) comes from kvps —
content is redundant and visually noisy. This extension clears it.

Runs after _15_log_from_stream_end which removes the step indicator.
Safe: content="" leaves the item with only its kvps-based display.

No LLM calls. One log item write. Passthrough on any failure.
"""

from agent import LoopData
from python.helpers.extension import Extension


class ClearGeneratingContent(Extension):
    """Clear raw JSON from log_item_generating.content at stream end."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            log_item = loop_data.params_temporary.get("log_item_generating")
            if log_item:
                log_item.update(content="")
        except Exception:
            pass
