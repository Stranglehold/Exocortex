"""
Tool Registry — Dynamic Custom Tool + Exocortex Skills Awareness
================================================================
Hook: before_main_llm_call (_16_)

Scans /a0/python/tools/ every turn and injects a compact [CUSTOM TOOLS] block
into the user message — so the model always knows which tool_names are callable
beyond the native Agent Zero set.

Also reads /a0/usr/Exocortex/skills/SKILLS_INDEX.md and injects an
[EXOCORTEX SKILLS] block so the model knows which procedural skill files exist
and when to read them before starting a task.

Grows with the agent automatically:
  • Any new .py file dropped into /a0/python/tools/ appears the next turn.
  • Any new row added to SKILLS_INDEX.md appears the next turn.
  • /a0/usr/Exocortex/tool_manifest.json registers installed programs and
    runtime-discovered capabilities (e.g. nmap after apt-get install).
    Created empty on first run if missing. Agent or analyst can write to it.

No imports of tool files (ast-only parsing). No LLM calls. Deterministic.
Runs after BST (_11_), profile (_13_), and metacognitive injection (_14_).
"""

import ast
import json
import os
import re
import textwrap
from typing import Optional

from agent import LoopData
from python.helpers.extension import Extension

# ── Configuration ──────────────────────────────────────────────────────────────

TOOLS_DIR              = "/a0/python/tools"
MANIFEST_PATH          = "/a0/usr/Exocortex/tool_manifest.json"
EXOCORTEX_SKILLS_DIR   = "/a0/usr/Exocortex/skills"
A0_SKILLS_DIR          = "/a0/usr/skills"

# Files to skip when scanning EXOCORTEX_SKILLS_DIR
SKILLS_EXCLUDE = {"skills_index.md", "readme.md", "index.md"}

# Max skills entries to inject (bounds token growth)
MAX_SKILLS = 30

# Native Agent Zero tool filenames — excluded from custom listing.
NATIVE_TOOLS = {
    "response", "a2a_chat", "behaviour_adjustment", "browser_agent",
    "call_subordinate", "code_execution_tool", "document_query", "input",
    "memory_load", "memory_save", "memory_delete", "memory_forget",
    "notify_user", "search_engine", "skills_tool",
}


# ── Extension ──────────────────────────────────────────────────────────────────

class ToolRegistry(Extension):
    """Inject custom tool registry into user message before each LLM call."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        try:
            custom_tools = _scan_custom_tools()
            programs     = _read_manifest()
            skills       = _scan_exocortex_skills()

            if not custom_tools and not programs and not skills:
                return

            block = _build_block(custom_tools, programs, skills)
            if not block:
                return

            user_msg = _get_last_user_message(loop_data.history_output)
            if not user_msg:
                return

            existing = user_msg.get("content", "")
            user_msg["content"] = block + "\n\n" + str(existing)

            tool_files = [name for name, _, _ in custom_tools]
            print(
                f"[TOOL-REG] Injected {len(custom_tools)} custom tools "
                f"({', '.join(tool_files)}), {len(programs)} programs, "
                f"{len(skills)} skills",
                flush=True,
            )

        except Exception as e:
            print(f"[TOOL-REG] error (passthrough): {e}", flush=True)


# ── Tool Scanning ───────────────────────────────────────────────────────────────

def _scan_custom_tools() -> list:
    """
    Return list of (filename_stem, [snake_case_tool_names], description) tuples
    for all non-native tool files in TOOLS_DIR.
    """
    if not os.path.isdir(TOOLS_DIR):
        return []

    results = []
    for fname in sorted(os.listdir(TOOLS_DIR)):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        stem = fname[:-3]
        if stem in NATIVE_TOOLS:
            continue

        path = os.path.join(TOOLS_DIR, fname)
        names, desc = _extract_tool_info(path)
        if names:
            results.append((stem, names, desc))

    return results


def _extract_tool_info(path: str) -> tuple:
    """
    Parse a tool file with ast (no import) and return:
      ([snake_case_tool_names], description_string)
    Tool names come from class names that subclass Tool.
    Description comes from the module docstring first line.
    Returns ([], "") on any parse error.
    """
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()

        tree = ast.parse(src)

        # Module docstring — first non-blank line
        raw_doc = ast.get_docstring(tree) or ""
        desc = next((ln.strip() for ln in raw_doc.splitlines() if ln.strip()), "")
        desc = textwrap.shorten(desc, width=90, placeholder="...")

        # Class names that directly or indirectly subclass Tool
        names = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                is_tool = (
                    (isinstance(base, ast.Name) and base.id == "Tool") or
                    (isinstance(base, ast.Attribute) and base.attr == "Tool")
                )
                if is_tool:
                    names.append(_to_snake(node.name))
                    break

        return names, desc

    except Exception:
        return [], ""


def _to_snake(name: str) -> str:
    """CamelCase → snake_case. OssHealth → oss_health."""
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    return s.lower()


# ── Exocortex Skills ────────────────────────────────────────────────────────────

def _scan_exocortex_skills() -> list:
    """
    Scan skill directories and return list of (skill_name, filename, trigger) tuples.

    Checks two locations:
      1. EXOCORTEX_SKILLS_DIR — flat .md files (Exocortex format)
      2. A0_SKILLS_DIR        — A0 subdirectory format (<name>/SKILL.md)

    Parses YAML frontmatter where present; falls back to filename derivation.
    Deduplicates by normalized name (Exocortex version wins on collision).
    Caps at MAX_SKILLS entries to bound token growth.
    """
    seen: dict = {}  # normalized_name → (skill_name, filename, trigger)

    # ── 1. Exocortex flat skills ──────────────────────────────────────────────
    if os.path.isdir(EXOCORTEX_SKILLS_DIR):
        try:
            for fname in sorted(os.listdir(EXOCORTEX_SKILLS_DIR)):
                if not fname.endswith(".md"):
                    continue
                if fname.lower() in SKILLS_EXCLUDE:
                    continue
                path = os.path.join(EXOCORTEX_SKILLS_DIR, fname)
                name, trigger = _parse_skill_file(path, fname)
                if not trigger:
                    continue  # skip files with no parseable trigger (specs, etc.)
                seen[_norm(name)] = (name, fname, trigger)
        except Exception:
            pass

    # ── 2. A0 usr/skills subdirectories ──────────────────────────────────────
    if os.path.isdir(A0_SKILLS_DIR):
        try:
            for entry in sorted(os.listdir(A0_SKILLS_DIR)):
                skill_md = os.path.join(A0_SKILLS_DIR, entry, "SKILL.md")
                if not os.path.isfile(skill_md):
                    continue
                name, trigger = _parse_skill_file(skill_md, entry)
                key = _norm(name)
                if key not in seen:  # Exocortex version takes priority
                    seen[key] = (name, entry + "/SKILL.md", trigger)
        except Exception:
            pass

    return list(seen.values())[:MAX_SKILLS]


def _parse_skill_file(path: str, fallback_id: str) -> tuple:
    """
    Extract (display_name, trigger_description) from a skill .md file.

    Handles three formats found in the Exocortex skills directory:
      1. YAML frontmatter at file start (--- name/description ---)
      2. Attribution block then YAML frontmatter (context-engineering skills)
      3. No frontmatter — # Skill: Name heading + ## Trigger section
    """
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read(6000)

        name = ""
        description = ""

        # ── YAML field extraction ─────────────────────────────────────────────
        # Direct line-based search handles both "frontmatter at start" and
        # "attribution blockquote then frontmatter" formats without block parsing.
        fm_match = None
        fm_name_m  = re.search(r"^name:\s*(.+)",        content, re.MULTILINE)
        fm_desc_m  = re.search(r"^description:\s*(.+)", content, re.MULTILINE)
        fm_trig_m  = re.search(r"^triggers:\s*(.+)",    content, re.MULTILINE)
        if fm_name_m:
            name = fm_name_m.group(1).strip().strip("\"'")
            fm_match = fm_name_m          # used later to locate "after_fm"
        if fm_desc_m:
            description = fm_desc_m.group(1).strip().strip("\"'")
        elif fm_trig_m and not description:
            items = re.findall(r'"([^"]+)"', fm_trig_m.group(1))
            if items:
                description = items[0]

        # ── # Skill: Name heading ─────────────────────────────────────────────
        if not name:
            heading = re.search(r"^#+\s+(?:Skill:\s+)?(.+)", content, re.MULTILINE)
            if heading:
                name = heading.group(1).strip()

        # ── ## Trigger section content ────────────────────────────────────────
        if not description:
            trigger_section = re.search(
                r"^#{1,3}\s+Trigger\s*\n+(.+?)(?=\n#{1,3}\s|\Z)",
                content,
                re.MULTILINE | re.DOTALL,
            )
            if trigger_section:
                # First non-blank line of trigger section
                for line in trigger_section.group(1).splitlines():
                    line = line.strip()
                    if line and not line.startswith(("#", ">", "---", "|")):
                        description = line
                        break

        # ── First non-blank body line as last-resort description ─────────────
        if not description:
            after_fm = content[fm_match.end():] if fm_match else content  # type: ignore[union-attr]
            for line in after_fm.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith(("#", ">", "---", "|", "!", "```", "*")):
                    continue
                # Skip bare k:v lines that look like leftover frontmatter
                if re.match(r"^\w[\w_-]*:\s", line):
                    continue
                description = line
                break

        # ── Filename-derived name fallback ────────────────────────────────────
        if not name:
            stem = os.path.basename(fallback_id).replace(".md", "")
            name = stem.replace("_", " ").replace("-", " ").title()
        else:
            # Title-case kebab/snake names from frontmatter (e.g. "irreversibility-gate")
            if name == name.lower() and re.search(r"[-_]", name):
                name = name.replace("-", " ").replace("_", " ").title()

        # Only include files with structured skill markers — exclude specs/design notes.
        has_fm_desc       = bool(fm_desc_m or (fm_trig_m and description))
        has_trigger_sec   = bool(re.search(r"^#{1,3}\s+Trigger\s*\n", content, re.MULTILINE))
        has_skill_heading = bool(re.search(r"^#+\s+Skill:", content, re.MULTILINE))
        if not has_fm_desc and not has_trigger_sec and not has_skill_heading:
            return name, ""  # caller skips entries with empty trigger

        trigger = textwrap.shorten(description, width=80, placeholder="...")
        return name, trigger

    except Exception:
        stem = os.path.basename(fallback_id).replace(".md", "")
        return stem.replace("_", " ").title(), ""


def _norm(name: str) -> str:
    """Normalize a skill name for deduplication (lowercase alphanum only)."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


# ── Manifest ────────────────────────────────────────────────────────────────────

def _read_manifest() -> dict:
    """
    Read tool_manifest.json. Returns programs dict (name → description).
    Creates the file empty if missing so the agent can write to it.
    """
    if not os.path.exists(MANIFEST_PATH):
        try:
            os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
            with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "programs": {},
                        "notes": (
                            "Add installed programs or agent-discovered capabilities here. "
                            "Each key is the program name; value is a brief description. "
                            "The tool registry extension injects these into every turn."
                        ),
                    },
                    f,
                    indent=2,
                )
        except Exception:
            pass
        return {}

    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return {k: str(v) for k, v in data.get("programs", {}).items() if k and v}
    except Exception:
        return {}


# ── Block Construction ──────────────────────────────────────────────────────────

def _build_block(custom_tools: list, programs: dict, skills: list) -> str:
    """Build the [CUSTOM TOOLS] and [EXOCORTEX SKILLS] injection blocks."""
    lines = []

    if custom_tools or programs:
        lines.append("[CUSTOM TOOLS — call by tool_name]")

        for _stem, names, desc in custom_tools:
            name_str = " | ".join(names)
            if desc:
                lines.append(f"{name_str} — {desc}")
            else:
                lines.append(name_str)

        if programs:
            lines.append("")
            lines.append("[INSTALLED PROGRAMS — invoke via code_execution_tool]")
            for prog, pdesc in programs.items():
                lines.append(f"{prog} — {pdesc}")

        lines.append("[/CUSTOM TOOLS]")

    if skills:
        if lines:
            lines.append("")
        lines.append("[EXOCORTEX SKILLS — read the skill file before starting the relevant task]")
        for skill_name, filename, trigger in skills:
            lines.append(f"{skill_name} ({filename}) — when: {trigger}")
        lines.append("[/EXOCORTEX SKILLS]")

    return "\n".join(lines)


# ── Message Helper (shared pattern with _13, _14) ──────────────────────────────

def _get_last_user_message(history_output: list) -> Optional[dict]:
    """Find the most recent operator message in loop history."""
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
