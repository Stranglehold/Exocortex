"""
Thinking Token Logger — Agent-Zero Exocortex
=============================================
Hook: reasoning_stream_end (_14_)

Logs thinking token counts per BST domain. Required measurement
infrastructure before TALE reasoning budget hints can be verified.

Per Opus review of TOKEN_ECONOMICS_FIELD_NOTE.md:
  "Measurement is mandatory before deployment. Deploy the hints. Run the
   same tasks. Compare thinking token counts. If the budget is being
   ignored or if accuracy drops measurably, adjust."

This extension runs BEFORE the TALE budget hints are active (deploy it
first, collect baseline, then enable reasoning_budget in BST enrichment).

Output format (grep-able):
  [THINK-LOG] domain=coding tokens=1847 budget=200 over_budget=True
  [THINK-LOG] domain=analysis tokens=3201 budget=none
  [THINK-LOG] domain=conversation tokens=412 budget=none

Log accumulates on agent._think_log for the session. Summary injected
into stack_status output if stack_status is imported (best-effort).

Config (config.json → "thinking_logger"):
  enabled: bool (default True)
  log_to_file: str (optional path, e.g. "/a0/usr/Exocortex/think_log.jsonl")
"""

import json
import os
import time
from typing import Any

from agent import LoopData
from helpers.extension import Extension

LOG_TAG = "[THINK-LOG]"

# Budget map mirrors the TALE tiers — used for over-budget detection
# Set to None for domains with no budget constraint
_BUDGET_MAP = {
    # Execution tier: ~200 tokens
    "coding":       200,
    "bugfix":       200,
    "system_admin": 200,
    "file_ops":     200,
    "git_ops":      200,
    # Planning tier: ~500 tokens
    "planning":     500,
    # Analysis tier: no constraint
    "investigation": None,
    "analysis":      None,
    "financial":     None,
    # Ambient domains: no constraint
    "conversation":   None,
    "orientation":    None,
    "meta_cognitive": None,
    "philosophical":  None,
}


class ThinkingTokenLogger(Extension):
    """Log thinking token counts per BST domain for TALE budget calibration."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> Any:
        try:
            cfg = _load_cfg(self.agent)
            if not cfg.get("enabled", True):
                return

            # reasoning_stream_end receives the full reasoning text
            # Try multiple kwargs keys (A0 version-dependent)
            reasoning = (
                kwargs.get("reasoning")
                or kwargs.get("reasoning_text")
                or kwargs.get("content")
                or ""
            )
            if not reasoning:
                return

            # Estimate tokens (rough: chars / 4)
            token_count = len(reasoning) // 4

            # Get current domain from BST store
            bst_store = getattr(self.agent, "_bst_store", {}) or {}
            domain = bst_store.get("_compound_sig", "conversation")

            # Check against budget
            primary_domain = domain.split("+")[0]
            budget = _BUDGET_MAP.get(primary_domain)
            over_budget = (budget is not None and token_count > budget)

            # Accumulate session log on agent
            if not hasattr(self.agent, "_think_log"):
                self.agent._think_log = []
            self.agent._think_log.append({
                "ts":          time.time(),
                "domain":      domain,
                "tokens":      token_count,
                "budget":      budget,
                "over_budget": over_budget,
            })

            # Keep last 50 entries (one per LLM call)
            if len(self.agent._think_log) > 50:
                self.agent._think_log = self.agent._think_log[-50:]

            budget_str = str(budget) if budget is not None else "none"
            msg = (
                f"{LOG_TAG} domain={domain} tokens={token_count} "
                f"budget={budget_str}"
                + (" OVER_BUDGET" if over_budget else "")
            )
            print(msg, flush=True)
            try:
                self.agent.context.log.log(type="info", content=msg)
            except Exception:
                pass

            # Optional JSONL file logging
            log_file = cfg.get("log_to_file", "")
            if log_file:
                try:
                    os.makedirs(os.path.dirname(log_file), exist_ok=True)
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "ts": time.time(),
                            "domain": domain,
                            "tokens": token_count,
                            "budget": budget,
                            "over_budget": over_budget,
                        }) + "\n")
                except Exception:
                    pass

        except Exception as exc:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"{LOG_TAG} Error (passthrough): {exc}",
                )
            except Exception:
                pass


def _load_cfg(agent) -> dict:
    try:
        cfg_path = "/a0/usr/Exocortex/config.json"
        if os.path.exists(cfg_path):
            data = json.loads(open(cfg_path).read())
            return data.get("thinking_logger", {})
    except Exception:
        pass
    return {}
