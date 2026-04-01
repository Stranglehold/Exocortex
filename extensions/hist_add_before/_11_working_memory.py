"""
Working Memory Buffer — Agent-Zero Hardening Layer
===================================================
Hook: hist_add_before
Priority: _10 (runs early, before any other hist_add_before extensions)

Called by agent-zero at agent.py line 671:
    self.call_extensions("hist_add_before", content_data=content_data, ai=ai)

Parameters:
  - content_data: the message content being added to history
  - ai: bool — True if AI message, False if user message

Entity extraction (user messages, ai=False):
  Extracts structured references from user messages — user messages are
  ground truth for what the user is actually talking about.

API signature extraction (AI messages, ai=True):
  Extracts function/class/attribute definitions from code blocks in AI
  responses. Stored in agent._wm_api_sigs and injected by _16_tool_registry.
  Prevents parameter confabulation (e.g. confidence vs confidence_score).
  Reads AI-generated code because signatures are only created by the agent
  itself — the AI is the source of truth for what it just defined.

Entity types extracted (regex-first, no model calls):
  - file paths (/foo/bar.py, ~/dir/file.txt)
  - file names (agent.py, config.json)
  - URLs (http://..., https://...)
  - IP addresses (192.168.1.1, 10.0.0.1)
  - container names (from docker context keywords)
  - port numbers (port 8080, :3000)
  - branch names (from git context keywords)
  - package names (from pip/apt context keywords)

Storage: agent._working_memory dict with structure:
  {
    "entities": [
      {"type": "file", "value": "/a0/agent.py", "turn": 12, "mentions": 3},
      {"type": "ip",   "value": "192.168.1.1",  "turn": 10, "mentions": 1},
      ...
    ],
    "promoted": {
      "/a0/agent.py": {"type": "file", "first_turn": 8, "last_turn": 12, "mentions": 5}
    }
  }

Decay: Entities older than DECAY_TURNS are pruned each cycle.
Promotion: Entities with >= PROMOTE_THRESHOLD mentions move to
           promoted dict and never decay during the session.
"""

import re
from typing import Any

from helpers.extension import Extension

# ── Configuration ─────────────────────────────────────────────────────────────

DECAY_TURNS       = 8    # Prune entities not mentioned in this many turns
PROMOTE_THRESHOLD = 3    # Mentions needed to promote to persistent memory
MAX_ENTITIES      = 50   # Cap to prevent unbounded growth
WM_KEY            = "_working_memory"

# API signature extraction (from AI code blocks)
WM_API_KEY        = "_wm_api_sigs"  # agent attribute: dict of name → sig string
MAX_API_SIGS      = 25              # cap; newest definition wins on name collision

# Patterns for API signature extraction from code blocks
_RE_CODE_BLOCK = re.compile(r'```(?:python)?\s*\n(.*?)```', re.DOTALL)
_RE_FUNC_SIG   = re.compile(r'^(?:    )*def\s+(\w+)\s*\(([^)]*)\)', re.MULTILINE)
_RE_CLASS_SIG  = re.compile(r'^class\s+(\w+)', re.MULTILINE)
_RE_SELF_ATTR  = re.compile(r'^\s+self\.(\w+)\s*=\s*\S', re.MULTILINE)

# ── Regex patterns for entity extraction ──────────────────────────────────────

# Absolute and home-relative paths
_RE_PATH = re.compile(
    r'(?:^|[\s`"\'])(/[a-zA-Z0-9_\-\.]+(?:/[a-zA-Z0-9_\-\.]+){1,15})'
    r'|'
    r'(?:^|[\s`"\'])(~/[a-zA-Z0-9_\-\./]+)',
    re.MULTILINE,
)

# File names with extensions (backtick-quoted preferred, then bare)
_RE_FILE = re.compile(
    r'`([^`\s]+\.[a-zA-Z]{1,5})`'
    r'|'
    r'(?:^|[\s"\'])([a-zA-Z0-9_\-]+\.[a-zA-Z]{1,5})(?=[\s`"\',;:)\].]|$)',
    re.MULTILINE,
)

# URLs
_RE_URL = re.compile(
    r'https?://[^\s<>"\')]+',
    re.IGNORECASE,
)

# IPv4 addresses
_RE_IP = re.compile(
    r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
)

# Port numbers — "port 8080", ":3000", "on port 443"
_RE_PORT = re.compile(
    r'(?:port\s+|:)(\d{2,5})\b',
    re.IGNORECASE,
)

# Container names — after docker keywords
_RE_CONTAINER = re.compile(
    r'(?:container|docker\s+(?:exec|logs|stop|restart|rm|inspect|attach))\s+([a-zA-Z0-9_\-]+)',
    re.IGNORECASE,
)

# Docker image names — after docker run/pull/build
_RE_IMAGE = re.compile(
    r'(?:docker\s+(?:run|pull|build|rmi|push))\s+(?:-[^\s]+\s+)*([a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-]+)*(?::[a-zA-Z0-9_\-\.]+)?)',
    re.IGNORECASE,
)

# Git branch names — after git checkout/branch/merge/rebase
_RE_BRANCH = re.compile(
    r'(?:checkout|branch|merge|rebase)\s+(?:-[^\s]+\s+)*([a-zA-Z0-9_\-/\.]+)',
    re.IGNORECASE,
)

# Package names — after pip install/uninstall, apt install
_RE_PACKAGE = re.compile(
    r'(?:pip\s+install|pip3\s+install|pip\s+uninstall|apt(?:-get)?\s+install)\s+(?:-[^\s]+\s+)*([a-zA-Z0-9_\-]+)',
    re.IGNORECASE,
)

# Config keys — key=value or key: value patterns in config context
_RE_CONFIG_KEY = re.compile(
    r'(?:set|change|update|modify)\s+(?:the\s+)?[`"\']?([a-zA-Z_][a-zA-Z0-9_\.\-]*)[`"\']?\s*(?:to|=)',
    re.IGNORECASE,
)

# Service/daemon names — systemctl, service commands
_RE_SERVICE = re.compile(
    r'(?:systemctl|service)\s+(?:start|stop|restart|status|enable|disable)\s+([a-zA-Z0-9_\-]+)',
    re.IGNORECASE,
)


class WorkingMemoryBuffer(Extension):
    """Agent-Zero extension: hist_add_before"""

    def execute(self, **kwargs) -> Any:
        try:
            # hist_add_before passes content_data and ai flag
            content_data = kwargs.get("content_data")
            ai = kwargs.get("ai", True)

            # API signature extraction from AI code blocks
            if ai:
                text = self._extract_text(content_data)
                if text:
                    new_sigs = _extract_api_signatures(text)
                    if new_sigs:
                        existing = getattr(self.agent, WM_API_KEY, {}) or {}
                        existing.update(new_sigs)  # newest definition wins
                        # Trim to cap: drop oldest entries (insertion order)
                        if len(existing) > MAX_API_SIGS:
                            excess = len(existing) - MAX_API_SIGS
                            for k in list(existing.keys())[:excess]:
                                del existing[k]
                        setattr(self.agent, WM_API_KEY, existing)
                        print(f"[WM] API sigs captured: {list(new_sigs.keys())}", flush=True)
                        # Verify attribute was set
                return

            # Only extract structural entities from user messages (ground truth)

            if not content_data:
                return

            # Extract text from content_data
            text = self._extract_text(content_data)
            if not text:
                return

            # Get or initialize working memory
            wm = self._get_wm()
            turn = self._current_turn()

            # Extract entities from the message text
            new_entities = _extract_entities(text)

            if not new_entities:
                return

            self.agent.context.log.log(
                type="info",
                content=f"[WM] Extracted {len(new_entities)} entities: {new_entities}"
            )

            # Merge into working memory
            for etype, value in new_entities:
                self._upsert_entity(wm, etype, value, turn)

            # Decay old entities
            self._decay(wm, turn)

            # Promote frequently mentioned entities
            self._promote(wm)

            # Cap total entity count
            self._cap_entities(wm)

            # Persist
            self.agent._working_memory = wm

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[WM] Error (passthrough): {e}"
                )
            except Exception:
                pass

    def _extract_text(self, content_data, _depth: int = 0) -> str:
        """Extract plain text from content_data passed by hist_add_before.

        hist_add_before wraps the actual content as {"content": <MessageContent>}.
        MessageContent for AI responses is a raw JSON string like:
          '{"tool_name": "response", "tool_args": {"text": "...markdown..."}}'
        For user messages it's a dict with user_message key.
        """
        import json as _json
        if _depth > 4:  # guard against infinite recursion
            return str(content_data) if content_data else ""
        if isinstance(content_data, str):
            stripped = content_data.strip()
            if stripped.startswith("{"):
                try:
                    d = _json.loads(stripped)
                    return self._extract_text(d, _depth + 1)
                except Exception:
                    pass
            return content_data
        if isinstance(content_data, dict):
            # hist_add_before wrapper: {"content": <actual content>}
            if "content" in content_data and len(content_data) == 1:
                return self._extract_text(content_data["content"], _depth + 1)
            # User message with structured content
            if "user_message" in content_data:
                return str(content_data["user_message"])
            if "message" in content_data:
                return str(content_data["message"])
            # AI response message via response tool: tool_args.text holds the body
            tool_args = content_data.get("tool_args")
            if isinstance(tool_args, dict) and "text" in tool_args:
                return str(tool_args["text"])
            return ""
        if isinstance(content_data, list):
            return " ".join(
                self._extract_text(p, _depth + 1) if isinstance(p, (str, dict)) else str(p)
                for p in content_data
            )
        return str(content_data) if content_data else ""

    def _get_wm(self) -> dict:
        """Get or initialize working memory structure."""
        wm = getattr(self.agent, WM_KEY, None)
        if not isinstance(wm, dict):
            wm = {"entities": [], "promoted": {}}
        if "entities" not in wm:
            wm["entities"] = []
        if "promoted" not in wm:
            wm["promoted"] = {}
        return wm

    def _current_turn(self) -> int:
        try:
            return len(self.agent.history or [])
        except Exception:
            return 0

    def _upsert_entity(self, wm: dict, etype: str, value: str, turn: int) -> None:
        """Insert or update an entity in working memory."""
        # Check promoted first — just update turn
        if value in wm["promoted"]:
            wm["promoted"][value]["last_turn"] = turn
            wm["promoted"][value]["mentions"] += 1
            return

        # Check existing entities
        for entity in wm["entities"]:
            if entity["type"] == etype and entity["value"] == value:
                entity["turn"] = turn
                entity["mentions"] += 1
                return

        # New entity
        wm["entities"].append({
            "type": etype,
            "value": value,
            "turn": turn,
            "mentions": 1,
        })

    def _decay(self, wm: dict, current_turn: int) -> None:
        """Remove entities that haven't been mentioned recently."""
        wm["entities"] = [
            e for e in wm["entities"]
            if (current_turn - e["turn"]) <= DECAY_TURNS
        ]

    def _promote(self, wm: dict) -> None:
        """Move frequently mentioned entities to promoted (never-decay) store."""
        still_active = []
        for entity in wm["entities"]:
            if entity["mentions"] >= PROMOTE_THRESHOLD:
                value = entity["value"]
                if value not in wm["promoted"]:
                    wm["promoted"][value] = {
                        "type": entity["type"],
                        "first_turn": entity["turn"],
                        "last_turn": entity["turn"],
                        "mentions": entity["mentions"],
                    }
                else:
                    wm["promoted"][value]["last_turn"] = entity["turn"]
                    wm["promoted"][value]["mentions"] = max(
                        wm["promoted"][value]["mentions"],
                        entity["mentions"],
                    )
            else:
                still_active.append(entity)
        wm["entities"] = still_active

    def _cap_entities(self, wm: dict) -> None:
        """Prevent unbounded growth by keeping only the most recent entities."""
        if len(wm["entities"]) > MAX_ENTITIES:
            # Sort by turn descending, keep most recent
            wm["entities"].sort(key=lambda e: e["turn"], reverse=True)
            wm["entities"] = wm["entities"][:MAX_ENTITIES]


def _extract_entities(text: str) -> list[tuple[str, str]]:
    """
    Extract all structured entities from text using regex.
    Returns list of (entity_type, value) tuples.
    Order: more specific patterns first to avoid false positives.
    """
    entities = []
    seen = set()

    def _add(etype: str, value: str):
        value = value.strip().rstrip(".,;:)")
        if not value or len(value) < 2:
            return
        key = (etype, value)
        if key not in seen:
            seen.add(key)
            entities.append(key)

    # URLs (before paths — URLs contain paths)
    for match in _RE_URL.finditer(text):
        _add("url", match.group(0))

    # IP addresses
    for match in _RE_IP.finditer(text):
        ip = match.group(1)
        # Basic validation: each octet 0-255
        octets = ip.split(".")
        if all(0 <= int(o) <= 255 for o in octets):
            _add("ip", ip)

    # Paths (absolute and home-relative)
    for match in _RE_PATH.finditer(text):
        value = match.group(1) or match.group(2)
        if value:
            _add("path", value)

    # File names
    for match in _RE_FILE.finditer(text):
        value = match.group(1) or match.group(2)
        if value and not _RE_IP.fullmatch(value):
            _add("file", value)

    # Container names
    for match in _RE_CONTAINER.finditer(text):
        _add("container", match.group(1))

    # Docker images
    for match in _RE_IMAGE.finditer(text):
        _add("image", match.group(1))

    # Git branches
    for match in _RE_BRANCH.finditer(text):
        val = match.group(1)
        # Filter out common false positives
        if val not in ("-b", "-d", "-D", "--force"):
            _add("branch", val)

    # Package names
    for match in _RE_PACKAGE.finditer(text):
        _add("package", match.group(1))

    # Port numbers
    for match in _RE_PORT.finditer(text):
        port = int(match.group(1))
        if 1 <= port <= 65535:
            _add("port", str(port))

    # Config keys
    for match in _RE_CONFIG_KEY.finditer(text):
        _add("config_key", match.group(1))

    # Service names
    for match in _RE_SERVICE.finditer(text):
        _add("service", match.group(1))

    return entities


def _extract_api_signatures(text: str) -> dict[str, str]:
    """
    Extract function/class/attribute signatures from code blocks in AI messages.
    Returns dict mapping name → signature string.

    Only processes content inside ```...``` fences to avoid false positives
    from prose descriptions. Class and self.attr entries are only captured
    when not already present (function defs take priority).
    """
    sigs: dict[str, str] = {}

    for block_match in _RE_CODE_BLOCK.finditer(text):
        block = block_match.group(1)

        # Function signatures (highest priority — exact parameter names matter most)
        for m in _RE_FUNC_SIG.finditer(block):
            name   = m.group(1)
            params = m.group(2).strip()
            sigs[name] = f"def {name}({params})"

        # Class definitions
        for m in _RE_CLASS_SIG.finditer(block):
            name = m.group(1)
            if name not in sigs:
                sigs[name] = f"class {name}"

        # Instance attribute assignments (self.x = ...)
        for m in _RE_SELF_ATTR.finditer(block):
            attr = m.group(1)
            key  = f"self.{attr}"
            if key not in sigs:
                sigs[key] = key

    return sigs
