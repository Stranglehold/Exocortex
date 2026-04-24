"""
Orchestration Gate — Delegation Scaffolding
============================================
Hook: before_main_llm_call (_17_)
Priority: after tool registry (_16_), before memory catalog (_18_)

Problem this fixes
------------------
The main agent attempts complex multi-phase tasks (codegen, analysis,
investigation) by executing tool calls directly rather than delegating to
specialized subordinate profiles. Even when call_subordinate is available
and the developer profile explicitly documents orchestration, the model
never delegates — it implements directly and loops when it hits friction.

What this does
--------------
Every turn where:
  1. BST classifies the task as complex (domain in DELEGATION_DOMAINS,
     confidence >= CONFIDENCE_THRESHOLD), AND
  2. The agent has made >= MIN_DIRECT_TOOLS consecutive direct tool calls
     (code_execution_tool, memory_load, search_engine, etc.) without a
     call_subordinate in the recent window,

...a [ORCHESTRATION MODE] block is prepended to the last user message.
The block names the domain, lists available profiles with their use cases,
provides the exact call_subordinate invocation format, and names the last
tool used (concrete evidence that the agent is NOT delegating).

When it stops firing
--------------------
- call_subordinate appears in the recent tool history → gate clears
- Domain shifts out of DELEGATION_DOMAINS (task complete or changed)
- Task completes (response tool fired recently)

Why user-message prepend, not extras_temporary
-----------------------------------------------
extras_temporary is appended AFTER history. Under deep-loop conditions
(7+ identical turns) the model's history prior overwhelms late-injected
extras. User message prepend fires before history reasoning forms — the
model cannot ignore it without explicitly acknowledging it.

No model calls. No config required. Deterministic.
Reads BST state from agent._bst_store (set by _11_belief_state_tracker).
Compatible with HTN (_15_) — uses different history keys.

Log tag: [ORCH-GATE]
"""

import json
import os
import re
from typing import Optional

from agent import LoopData
from helpers.extension import Extension


def _log_injection_tokens(agent, ext_name: str, text: str) -> None:
    tok = len(text) // 4
    counts = getattr(agent, "_injection_token_counts", {})
    counts[ext_name] = counts.get(ext_name, 0) + tok
    agent._injection_token_counts = counts
    print(f"[TOKEN-COUNT] {ext_name}: ~{tok} tokens injected", flush=True)

# ── Configuration ──────────────────────────────────────────────────────────────

# Domains where delegation is appropriate
DELEGATION_DOMAINS = {
    "codegen", "planning", "analysis", "investigation",
    "system_admin", "git_ops",
}

# Minimum BST confidence before gate fires
CONFIDENCE_THRESHOLD = 0.60

# Number of consecutive direct tool calls before gate fires
MIN_DIRECT_TOOLS = 3

# Window size for counting direct tool calls
TOOL_SCAN_WINDOW = 10

# Tools that are NOT direct implementation (gate clears when these appear)
DELEGATION_TOOLS = {"call_subordinate"}

# Tools to skip in direct-count (bookkeeping / meta operations)
SKIP_IN_COUNT = {"response", "call_subordinate", "notify_user"}

# BST keys (matches _11_belief_state_tracker)
BST_STORE_KEY    = "_bst_store"
BST_BELIEF_KEY   = "__bst_belief_state__"

# Agent Zero profile directories
PROFILE_DIRS = ["/a0/agents", "/a0/usr/agents"]

# Fallback profile registry — used when filesystem scan fails
DEFAULT_PROFILES = {
    "developer": "Code implementation, file editing, debugging, system commands",
    "researcher": "Web search, information gathering, analysis, documentation",
    "hacker":     "Security, network analysis, penetration testing",
}


# ── Extension ──────────────────────────────────────────────────────────────────

class OrchestrationGate(Extension):
    """Inject delegation scaffolding before LLM reasoning on complex tasks."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            # ── 1. Check BST classification ────────────────────────────────
            domain, confidence = _get_bst_domain(self.agent)
            if domain not in DELEGATION_DOMAINS:
                return
            if confidence < CONFIDENCE_THRESHOLD:
                return

            # ── 2. Count consecutive direct tool calls in recent history ──
            history = loop_data.history_output or []
            direct_count, last_direct_tool, has_recent_delegation = (
                _scan_tool_history(history, TOOL_SCAN_WINDOW)
            )

            if has_recent_delegation:
                # Agent already delegated — gate stays quiet
                return

            if direct_count < MIN_DIRECT_TOOLS:
                # Not enough direct calls yet — give the agent a chance
                return

            # ── 3. Build and inject block ──────────────────────────────────
            profiles = _discover_profiles()
            block = _build_block(domain, confidence, profiles,
                                 direct_count, last_direct_tool)

            user_msg = _get_last_user_message(history)
            if not user_msg:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)
            _log_injection_tokens(self.agent, "orchestration_gate", block)

            print(
                f"[ORCH-GATE] Fired: domain={domain} conf={confidence:.0%} "
                f"direct_calls={direct_count} last_tool={last_direct_tool}",
                flush=True,
            )

        except Exception as e:
            print(f"[ORCH-GATE] error (passthrough): {e}", flush=True)


# ── BST State Reader ────────────────────────────────────────────────────────────

def _get_bst_domain(agent) -> tuple[str, float]:
    """
    Read primary domain and confidence from BST store.
    Returns ("conversation", 0.0) if BST hasn't fired yet.
    """
    try:
        store = getattr(agent, BST_STORE_KEY, None) or {}
        belief = store.get(BST_BELIEF_KEY)
        if not isinstance(belief, dict):
            return "conversation", 0.0
        primary = belief.get("primary") or {}
        domain = primary.get("domain") or "conversation"
        confidence = float(primary.get("confidence") or 0.0)
        return domain, confidence
    except Exception:
        return "conversation", 0.0


# ── Tool History Analysis ───────────────────────────────────────────────────────

def _scan_tool_history(history: list, window: int) -> tuple[int, str, bool]:
    """
    Walk recent history (last `window` AI messages) and return:
      (direct_tool_count, last_direct_tool_name, has_recent_delegation)

    direct_tool_count     — consecutive direct tool calls before last delegation
    last_direct_tool_name — name of most recent direct tool call
    has_recent_delegation — True if call_subordinate appears in the window
    """
    # Collect AI messages from the tail of history
    ai_msgs = [
        msg for msg in history
        if isinstance(msg, dict) and msg.get("ai", True)
    ]
    recent = ai_msgs[-window:] if len(ai_msgs) > window else ai_msgs

    direct_count = 0
    last_direct = ""
    has_delegation = False

    for msg in reversed(recent):
        tool_name = _parse_tool_name(msg.get("content", ""))
        if not tool_name:
            continue
        if tool_name in DELEGATION_TOOLS:
            has_delegation = True
            break  # stop counting — agent delegated at some point
        if tool_name in SKIP_IN_COUNT:
            # response tool = task end — reset the chain
            break
        # Direct tool call
        direct_count += 1
        if not last_direct:
            last_direct = tool_name

    return direct_count, last_direct, has_delegation


def _parse_tool_name(content) -> str:
    """Extract tool_name from AI message content (JSON string or dict)."""
    if isinstance(content, dict):
        return content.get("tool_name", "")
    if isinstance(content, str) and content.strip().startswith("{"):
        try:
            data = json.loads(content.strip())
            if isinstance(data, dict):
                return data.get("tool_name", "")
        except Exception:
            pass
        m = re.search(r'"tool_name"\s*:\s*"([^"]+)"', content)
        if m:
            return m.group(1)
    return ""


# ── Profile Discovery ───────────────────────────────────────────────────────────

def _discover_profiles() -> dict:
    """
    Scan Agent Zero profile directories for available agent profiles.
    Returns {name: description} dict. Falls back to DEFAULT_PROFILES.
    """
    found = {}
    for base_dir in PROFILE_DIRS:
        if not os.path.isdir(base_dir):
            continue
        try:
            for entry in os.scandir(base_dir):
                if not entry.is_dir():
                    continue
                name = entry.name
                if name.startswith(".") or name == "agent0":
                    continue
                # Try to read title from agent.system.main.role.md
                desc = _read_profile_desc(entry.path)
                found[name] = desc or DEFAULT_PROFILES.get(name, "Specialized agent")
        except Exception:
            continue

    return found if found else DEFAULT_PROFILES


def _read_profile_desc(profile_dir: str) -> str:
    """Extract a one-line description from a profile's role prompt."""
    role_file = os.path.join(profile_dir, "prompts", "agent.system.main.role.md")
    if not os.path.exists(role_file):
        return ""
    try:
        with open(role_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # First non-blank non-heading line = description
                    return line[:80]
    except Exception:
        pass
    return ""


# ── Block Builder ───────────────────────────────────────────────────────────────

def _build_block(domain: str, confidence: float, profiles: dict,
                 direct_count: int, last_tool: str) -> str:
    """Build the [ORCHESTRATION MODE] injection block."""
    lines = [
        f"[ORCHESTRATION MODE — task type: {domain} ({confidence:.0%} confidence)]",
        "You are the ORCHESTRATOR. Your role is to plan and coordinate — "
        "NOT to implement directly.",
        "",
        "You have made "
        + str(direct_count)
        + " consecutive direct tool calls"
        + (f" (last: {last_tool})" if last_tool else "")
        + ".",
        "For complex tasks, you MUST delegate implementation to a subordinate agent.",
        "",
        "Available profiles (use with call_subordinate):",
    ]

    for name, desc in profiles.items():
        lines.append(f"  {name} — {desc}")

    lines += [
        "",
        "Delegation format:",
        '  tool_name: "call_subordinate"',
        '  message:    "<focused task description for the subordinate>"',
        f'  agent_name: "developer"   ← (or researcher / hacker)',
        "",
        "Direct tools (code_execution_tool, search_engine, etc.) are for"
        " quick checks only.",
        "Delegate multi-step implementation. Resume orchestration after the"
        " subordinate returns.",
        "[/ORCHESTRATION MODE]",
    ]

    return "\n".join(lines)


# ── Message Helper ──────────────────────────────────────────────────────────────

def _get_last_user_message(history: list) -> Optional[dict]:
    """Find the most recent operator message in loop history."""
    if not history:
        return None
    for msg in reversed(history):
        if not isinstance(msg, dict):
            continue
        if not msg.get("ai", True):
            content = msg.get("content", "")
            if isinstance(content, dict) and "user_message" in content:
                return msg
            if isinstance(content, str) and content:
                return msg
    return None
