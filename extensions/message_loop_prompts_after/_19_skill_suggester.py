"""
Skill Auto-Suggester — Agent-Zero Exocortex
============================================
Hook: message_loop_prompts_after (_19_)

When BST classifies a domain with relevant skills, injects a compact
[SKILLS] block into the user message so the agent knows which procedural
skill files to read before starting.

Problem solved: ~20 skills exist in the skills directory but the agent
never surfaces them at the point of need. The tool registry (order 16)
shows what tools are callable. This extension is the equivalent for skills.

Design: KESTREL_OBSERVATIONS_2026-04-12.md, Item 2.

Rules:
- Only injects if domain is classified (not "unclassified")
- Only injects if ≥1 skill maps to the domain
- Once per session (gate: _skills_suggested agent attribute)
- No LLM calls. Fully deterministic. Order 19 — after tool registry (16).
"""

import os
from typing import Optional

from agent import LoopData
from helpers.extension import Extension

# ── Constants ─────────────────────────────────────────────────────────────────

LOG_TAG = "[SKILL-SUGGEST]"

# Once-per-session flag
_SKILLS_ATTR = "_skills_suggested"

# Base path for skill files inside the container
SKILLS_BASE = "/a0/usr/Exocortex/skills"

# Maps skill display name → file path relative to SKILLS_BASE
SKILL_FILES: dict[str, str] = {
    "debug-diagnostics":       "DEBUG_DIAGNOSTICS.md",
    "execute-buildplan":       "execute-buildplan/SKILL.md",
    "design-buildplan":        "design-buildplan/SKILL.md",
    "api-caller":              "api_caller.md",
    "multi-agent-patterns":    "multi-agent-patterns.md",
    "research-analysis":       "RESEARCH_ANALYSIS.md",
    "structural-analysis":     "structural-analysis.md",
    "integration-assessment":  "INTEGRATION_ASSESSMENT.md",
    "documentation-sync":      "DOCUMENTATION_SYNC.md",
    "cross-instance-learning": "CROSS_INSTANCE_LEARNING.md",
    "profile-analysis":        "PROFILE_ANALYSIS.md",
    "l3-spec-writing":         "SPEC_WRITING.md",
    "stress-test":             "STRESS_TEST_SKILL.md",
    "context-degradation":     "context-degradation.md",
    "tool-design":             "tool-design.md",
    "artifact-saving":         "artifact_saving.md",
}

# Domain → skill name mapping (deterministic, no LLM)
DOMAIN_SKILLS: dict[str, list[str]] = {
    "codegen":        ["debug-diagnostics", "execute-buildplan"],
    "bugfix":         ["debug-diagnostics"],
    "system_admin":   ["debug-diagnostics", "api-caller"],
    "agentic":        ["execute-buildplan", "multi-agent-patterns"],
    "research":       ["research-analysis", "structural-analysis"],
    "investigation":  ["structural-analysis", "integration-assessment"],
    "git_ops":        ["documentation-sync"],
    "communication":  ["cross-instance-learning"],
    "analysis":       ["structural-analysis", "profile-analysis"],
    "planning":       ["design-buildplan", "l3-spec-writing"],
    "specification":  ["l3-spec-writing", "design-buildplan"],
    "evaluation":     ["profile-analysis", "stress-test"],
    "browser":        ["artifact-saving"],
}

CONFIG_KEY = "skill_suggester"
_CONFIG_PATH = "/a0/usr/Exocortex/config.json"


# ── Extension ─────────────────────────────────────────────────────────────────

class SkillSuggester(Extension):
    """Inject [SKILLS] block once per session based on BST domain."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            cfg = _load_config(self.agent)
            if not cfg.get("enabled", True):
                return

            # Once per session
            if getattr(self.agent, _SKILLS_ATTR, False):
                return

            # Read domain from BST store — available from previous turn onward
            domain = _get_domain(self.agent)
            if not domain or domain in ("unclassified", "unknown", ""):
                return

            # Map domain to skills
            skill_names = DOMAIN_SKILLS.get(domain, [])
            if not skill_names:
                return

            # Filter to skills that have actual files (graceful degradation)
            skills = [(name, SKILL_FILES[name]) for name in skill_names if name in SKILL_FILES]
            if not skills:
                return

            # Build and inject block
            block = _build_block(domain, skills)
            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            self.agent.__dict__[_SKILLS_ATTR] = True

            names_str = " | ".join(name for name, _ in skills)
            msg = f"{LOG_TAG} Injected {len(skills)} skills for domain {domain}: {names_str}"
            print(msg, flush=True)
            try:
                self.agent.context.log.log(type="info", content=msg)
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_domain(agent) -> str:
    """Extract primary domain from BST store compound signature."""
    try:
        bst_store = getattr(agent, "_bst_store", None) or {}
        compound_sig = bst_store.get("_compound_sig", "") or ""
        if not compound_sig:
            return ""
        # compound_sig may be "codegen", "codegen+bugfix", "codegen/bugfix" — take primary
        primary = compound_sig.split("+")[0].split("/")[0].split(":")[0].strip().lower()
        return primary
    except Exception:
        return ""


def _build_block(domain: str, skills: list[tuple[str, str]]) -> str:
    """Build the compact [SKILLS] injection block."""
    lines = [f"[SKILLS — relevant to this {domain} task]"]
    for name, rel_path in skills:
        full_path = os.path.join(SKILLS_BASE, rel_path).replace("\\", "/")
        lines.append(f"  {name} → {full_path}")
    lines.append(f"  Read these skill files before starting.")
    lines.append("[/SKILLS]")
    return "\n".join(lines)


def _get_last_user_message(history_output: list) -> Optional[dict]:
    """Find the last operator message in loop history."""
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


def _load_config(agent) -> dict:
    try:
        import json
        if os.path.exists(_CONFIG_PATH):
            data = json.loads(open(_CONFIG_PATH).read())
            return data.get(CONFIG_KEY, {})
    except Exception:
        pass
    return {}
