from helpers.extension import Extension
from helpers import files
from agent import LoopData
import os
import re
import json

# Marker that identifies the tools block in loop_data.system
TOOLS_BLOCK_MARKER = "## Tools available:"

# Matches ### tool_name headings in tool spec files
TOOL_HEADING_RE = re.compile(r'^###\s+(\w+)', re.MULTILINE)

# Cache key for tool registry stored on agent between iterations
REGISTRY_CACHE_KEY = "_tiered_tools_registry"

# Persistent set of tools the model has used in this session
SEEN_TOOLS_KEY = "_tiered_tools_seen"

# Tools always injected with full spec regardless of active tool
# response: model must always know how to terminate
# code_execution_tool: primary execution tool, schema errors are fatal
ALWAYS_FULL_SPEC = {"response", "code_execution_tool"}

# Intent patterns for proactive injection on first use.
# Only fires when no active tool is detected (new task / first turn).
# High-confidence patterns only — false positives waste tokens.
INTENT_TOOL_MAP = [
    (re.compile(r"\b(?:call|delegate|sub-?agent|another agent|subordinate agent)\b", re.IGNORECASE), "call_subordinate"),
    (re.compile(r"\b(?:search the web|google|web search|look it up online|find online)\b", re.IGNORECASE), "search_engine"),
    (re.compile(r"\b(?:document[_ ]query|query the doc|read the file|load the document)\b", re.IGNORECASE), "document_query"),
    (re.compile(r"\b(?:use a skill|run a skill|skills?[ _]tool)\b", re.IGNORECASE), "skills_tool"),
    (re.compile(r"\b(?:browse|open a browser|navigate to|click on the)\b", re.IGNORECASE), "browser_agent"),
]


def _build_tool_registry(agent) -> tuple[str, dict[str, str]]:
    """
    Reads all agent.system.tool.*.md files and returns:
    - compact_menu: single string, one line per tool (name + first description line)
    - full_specs: dict mapping tool_name -> full file content

    Cached on agent.data to avoid re-reading files every iteration.
    """
    cached = agent.get_data(REGISTRY_CACHE_KEY)
    if cached:
        return cached["menu"], cached["specs"]

    from helpers import subagents
    dirs = subagents.get_paths(agent, "prompts")

    # Collect all tool spec files across prompt directories
    tool_files = files.get_unique_filenames_in_dirs(dirs, "agent.system.tool.*.md")

    menu_lines = []
    full_specs = {}

    for tool_file in sorted(tool_files):
        try:
            content = files.read_prompt_file(tool_file, _agent=agent)
        except Exception:
            continue

        # Extract all tool names from ### headings in this file
        # Some files (like memory.md) define multiple tools
        headings = TOOL_HEADING_RE.findall(content)
        if not headings:
            continue

        # First non-empty, non-heading line after the first heading = description
        lines = content.splitlines()
        desc = ""
        past_heading = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("###"):
                past_heading = True
                continue
            if past_heading and stripped and not stripped.startswith("#"):
                desc = stripped[:120]  # cap description length
                break

        for tool_name in headings:
            menu_lines.append(f"- **{tool_name}**: {desc}")
            full_specs[tool_name] = content

    compact_menu = "\n".join(menu_lines)

    # Cache for this session
    agent.set_data(REGISTRY_CACHE_KEY, {"menu": compact_menu, "specs": full_specs})

    return compact_menu, full_specs


def _extract_tool_name(last_response: str) -> str | None:
    """
    Extracts tool_name from the previous iteration's LLM response.
    Handles ~~~json fenced blocks and raw JSON.
    Returns None if extraction fails.
    """
    if not last_response:
        return None

    # Strip ~~~ or ``` code fences
    cleaned = re.sub(r'~~~json|~~~|```json|```', '', last_response).strip()

    try:
        parsed = json.loads(cleaned)
        return parsed.get("tool_name")
    except Exception:
        # Fallback: regex extraction for dirty JSON
        match = re.search(r'"tool_name"\s*:\s*"([^"]+)"', last_response)
        return match.group(1) if match else None


def _get_user_message(agent) -> str:
    """Extract the most recent user message from history for intent scanning."""
    try:
        outputs = agent.history.output()
        for msg in reversed(outputs):
            if not msg.get("ai", True):
                content = msg.get("content", "")
                if isinstance(content, list):
                    return " ".join(
                        p.get("text", "") if isinstance(p, dict) else str(p)
                        for p in content
                    )
                return str(content) if content else ""
    except Exception:
        pass
    return ""


def _intent_tools(user_msg: str, full_specs: dict) -> set[str]:
    """Return tool names that match intent signals in the user message."""
    matched = set()
    if not user_msg:
        return matched
    for pattern, tool_name in INTENT_TOOL_MAP:
        if tool_name in full_specs and pattern.search(user_msg):
            matched.add(tool_name)
    return matched


class TieredToolInjection(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Locate the tools block in the assembled system prompt list
        tools_idx = None
        for i, segment in enumerate(loop_data.system):
            if TOOLS_BLOCK_MARKER in segment:
                tools_idx = i
                break

        if tools_idx is None:
            return  # Tools block not found — skip silently

        # Build registry (cached after first call)
        try:
            compact_menu, full_specs = _build_tool_registry(self.agent)
        except Exception:
            return  # Registry build failed — leave tools block untouched

        if not compact_menu or not full_specs:
            return  # Nothing to work with

        # ── Detect active tool from last response ────────────────────────
        active_tool = _extract_tool_name(loop_data.last_response)

        # ── Seen-tools: persist across turns ────────────────────────────
        # Once the model uses a tool, keep injecting its full spec so the
        # model never regresses to compact-only on a revisit.
        seen_tools: set = set(self.agent.get_data(SEEN_TOOLS_KEY) or [])
        if active_tool and active_tool in full_specs and active_tool not in ALWAYS_FULL_SPEC:
            seen_tools.add(active_tool)
            self.agent.set_data(SEEN_TOOLS_KEY, list(seen_tools))

        # ── Intent pre-injection: first-turn proactive spec ──────────────
        # When there is no active tool (new task / first turn of a new tool),
        # scan the user message for intent signals and pre-inject matching specs.
        intent_extras: set[str] = set()
        if not active_tool:
            user_msg = _get_user_message(self.agent)
            intent_extras = _intent_tools(user_msg, full_specs)
            # Filter out already-covered tools
            intent_extras -= ALWAYS_FULL_SPEC
            intent_extras -= seen_tools

        # ── Build replacement block ──────────────────────────────────────
        replacement_parts = [
            TOOLS_BLOCK_MARKER,
            "Select a tool from the list below. Full usage details follow for relevant tools.\n",
            compact_menu,
        ]

        # Always inject full spec for pinned tools
        for tool_name in sorted(ALWAYS_FULL_SPEC):
            spec = full_specs.get(tool_name, "")
            if spec:
                replacement_parts.append(
                    f"\n---\n**{tool_name} — always available (full spec):**\n{spec}"
                )

        # Inject full spec for all previously-used tools (persistent across turns)
        for tool_name in sorted(seen_tools):
            spec = full_specs.get(tool_name, "")
            if spec:
                replacement_parts.append(
                    f"\n---\n**{tool_name} — previously used (full spec):**\n{spec}"
                )

        # Inject full spec for active tool if not already covered
        if active_tool and active_tool in full_specs and active_tool not in ALWAYS_FULL_SPEC and active_tool not in seen_tools:
            replacement_parts.append(
                f"\n---\n**{active_tool} — active tool (full spec):**\n{full_specs[active_tool]}"
            )

        # Inject full spec for intent-matched tools (first-turn proactive)
        for tool_name in sorted(intent_extras):
            spec = full_specs.get(tool_name, "")
            if spec:
                replacement_parts.append(
                    f"\n---\n**{tool_name} — anticipated (full spec):**\n{spec}"
                )

        loop_data.system[tools_idx] = "\n".join(replacement_parts)
