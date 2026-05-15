"""
Injection Budget Summary — before_main_llm_call priority _18_

Runs after all context injectors. Reads cumulative token counts accumulated by
each injector's _log_injection_tokens() call and injects a one-line summary
into extras_temporary so the agent can see its own context overhead.

When the injection gate (_09_) is built, this logic moves there.
"""
from helpers.extension import Extension
from agent import LoopData


class InjectionBudget(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            config = getattr(self.agent.config, "extension_settings", {}).get("injection_budget", {})
            if not config.get("enabled", True):
                return

            counts: dict = getattr(self.agent, "_injection_token_counts", {}) or {}
            if not counts:
                return

            total = sum(counts.values())
            top3  = sorted(counts.items(), key=lambda x: -x[1])[:3]
            summary = ", ".join(f"{k}:{v}" for k, v in top3)

            ep = getattr(loop_data, "extras_temporary", None)
            if ep is None:
                loop_data.extras_temporary = {}
                ep = loop_data.extras_temporary

            ep["injection_budget"] = (
                f"[INJECTION BUDGET] ~{total} tokens injected this turn. "
                f"Top: {summary}"
            )

            # Reset per-turn — counts must not accumulate across turns.
            # Without this reset, "this turn" becomes misleadingly "this session."
            self.agent._injection_token_counts = {}

        except Exception as e:
            print(f"[INJECTION-BUDGET] Error: {e}", flush=True)
