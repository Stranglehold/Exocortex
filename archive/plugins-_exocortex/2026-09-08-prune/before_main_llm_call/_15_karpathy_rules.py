"""
Karpathy Coding Rules — BST-Gated Quality Injection
====================================================
Hook: before_main_llm_call (_15_)

Injects four concise coding standards into the user message when BST classifies
the current turn as coding, bugfix, or system_admin. Silent on all other domains.

Runs after BST (_11_) so domain classification is already available, and after
metacognitive injection (_14_) which skips structural domains. This extension
fires exactly where _14_ does not.

No LLM calls. Fully deterministic.
"""

from typing import Optional

from agent import Agent, LoopData
from helpers.extension import Extension


CONFIG_KEY      = "karpathy_rules"
CODING_DOMAINS  = {"coding", "bugfix", "system_admin"}

_BLOCK = """\
[CODING STANDARDS]
Think Before Coding: Surface assumptions, clarify ambiguity, push back on complexity, stop on confusion.
Simplicity First: Minimum code, no speculative features, no single-use abstractions, no impossible error handling.
Surgical Changes: Touch only what's needed, match existing style, flag dead code but don't delete it.
Goal-Driven Execution: Transform tasks into verifiable success criteria. Loop until verified.\
"""


def _log_injection_tokens(agent, text: str) -> None:
    tok = len(text) // 4
    counts = getattr(agent, "_injection_token_counts", {})
    counts["karpathy_rules"] = counts.get("karpathy_rules", 0) + tok
    agent._injection_token_counts = counts
    print(f"[TOKEN-COUNT] karpathy_rules: ~{tok} tokens injected", flush=True)


class KarpathyRules(Extension):
    """Inject Karpathy coding standards on coding/bugfix/system_admin turns."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            if self.agent.get_data(Agent.DATA_NAME_SUPERIOR) is not None:
                return  # subordinate context — skip

            cfg = _load_config(self.agent)
            if not cfg.get("enabled", True):
                return

            domain = _get_bst_domain(loop_data, self.agent)
            if domain not in CODING_DOMAINS:
                return

            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            # Route through injection gate for full / reference / skip
            try:
                from extensions.before_main_llm_call._09_injection_gate import should_inject
                action, ref = should_inject(self.agent, "karpathy_rules", _BLOCK)
            except Exception:
                action, ref = "full", ""

            if action == "skip":
                return
            inject_text = ref if action == "reference" else _BLOCK

            existing = user_msg.get("content", "")
            user_msg["content"] = inject_text + "\n\n" + str(existing)
            if action == "full":
                _log_injection_tokens(self.agent, _BLOCK)

            print(f"[KARP] Coding standards injected (domain={domain})", flush=True)

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[KARP] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_config(agent) -> dict:
    try:
        cfg = getattr(agent, "config", None)
        if cfg is None:
            return {}
        raw = cfg if isinstance(cfg, dict) else vars(cfg)
        return raw.get(CONFIG_KEY, {})
    except Exception:
        return {}


def _get_bst_domain(loop_data: LoopData, agent) -> str:
    try:
        ep = getattr(loop_data, "extras_persistent", None) or {}
        domain = ep.get("_bst_domain")
        if domain:
            return str(domain)
    except Exception:
        pass

    try:
        store = getattr(agent, "_bst_store", None) or {}
        belief = store.get("__bst_belief_state__")
        if belief and hasattr(belief, "primary_domain"):
            return str(belief.primary_domain)
    except Exception:
        pass

    return "unknown"


def _get_last_user_message(history_output: list) -> Optional[dict]:
    if not history_output:
        return None
    for msg in reversed(history_output):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            content = msg.get("content", "")
            if isinstance(content, dict) and "user_message" in content:
                return msg
            if isinstance(content, str) and content:
                return msg
    return None
