"""
Action Boundary Classification — Exocortex Pre-Execution Gate
=============================================================
Hook: tool_execute_before (_15_)

Classifies every tool invocation by authorization tier before execution.
Gates Tier 4 (S4/Identity-Write) actions behind operator authorization.

    Tier 1 — Autonomous     (S2/Read):           no gate
    Tier 2 — Log & Proceed  (S2/Write-Local):    audit log
    Tier 3 — Notify & Proceed (S3/Ext-Write):    log + inline notice
                               (external API writes, account registration, HTTP POST)
    Tier 4 — Require Auth   (S4/Identity-Write): BLOCK + authorization request
                               (publishing as operator, messaging, git push, deployment)

Gate behavior is operator-configured. Defaults are maximally cautious:
Tier 1=allow, Tier 2=log, Tier 3=notify, Tier 4=block.

Blocking works by replacing tool_args["code"] for code_execution_tool.
For other tools, blocking is injected as a hist_add_warning (model sees it).

Configuration: /a0/usr/plugins/_exocortex/config/action_boundary_config.json
Audit log:     /a0/usr/logs/action_audit.jsonl (configurable)

No LLM calls. All classification is regex/pattern matching.
Runs before meta-reasoning gate (_20) and fallback advisor (_30).
Motivated by: MJ Rathbun incident (first documented AI-initiated defamation).
"""

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from helpers.extension import Extension

CONFIG_PATH = "/a0/usr/plugins/_exocortex/config/action_boundary_config.json"

# ── Default Configuration ─────────────────────────────────────────────────────

DEFAULT_CONFIG: Dict = {
    "enabled": True,
    "tier_policies": {
        "1": "allow",
        "2": "log",
        "3": "notify",
        "4": "block",
    },
    "allowed_targets": [
        "host.docker.internal",
        "localhost",
        "127.0.0.1",
    ],
    "blocked_targets": [],
    "audit_log_path": "/a0/usr/logs/action_audit.jsonl",
    "log_all_tiers": False,
}

# ── Tier 4 — S4/Identity-Write: requires operator authorization ───────────────
#
# Actions that represent the operator externally or are permanently consequential.
# These are NOT generic "writing to external services" — they are actions that
# commit the operator's identity, publish their work, or send messages as them.
# Recalibrated: generic HTTP writes (account creation, API calls) moved to Tier 3.

TIER_4_CMD_PATTERNS = [
    # Git write operations (permanent, shared external state)
    r"\bgit\s+(push|remote\s+add)\b",
    # SSH to external hosts (not local)
    r"\bssh\b(?!.*localhost)(?!.*127\.0\.0\.1)(?!.*host\.docker\.internal)",
    # Email / messaging tools (sending as operator)
    r"\b(sendmail|mutt|msmtp)\b",
    r"\bmail\s+-s\b",
    # Docker registry operations (publishing images)
    r"\bdocker\s+(push|login)\b",
    # Package publishing (permanent, public)
    r"\b(npm\s+publish|twine\s+upload)\b",
]

TIER_4_TOOL_NAMES = [
    "send_message", "publish", "deploy", "upload",
]

# ── Tier 4 — Python open() writes to system paths ─────────────────────────────
#
# Gap A fix: Python open(path, 'w'/'a') to agent system directories is NOT
# caught by shell command patterns — the agent writes via Python, not via shell
# redirect. These paths are higher-consequence than a workdir write because
# modifications persist in the agent's own tool layer.
#
# The promotion workflow: agent builds in workdir → proposes promotion to operator
# → operator authorizes → tool moves to persistent path. This gate enforces the
# boundary before promotion.

TIER_4_SYSTEM_WRITE_PATHS = {
    "/a0/python/",      # v1.5 path — kept for backwards compatibility during migration
    "/a0/tools/",       # v1.6 tools path
    "/a0/helpers/",     # v1.6 helpers path
    "/a0/agents/",
    "/a0/usr/agents/",  # V1.7 profile-path extensions
    "/a0/usr/plugins/", # V1.7 plugin tools/extensions
}

# Matches: open('/path', 'w'), open("/path", "w"), open('/path', 'wb'), open('/path', 'a')
_PY_OPEN_WRITE_RX = re.compile(
    r"""open\s*\(\s*['"]([^'"]+)['"]\s*,\s*['"](?:w|a|wb|ab)['"]""",
    re.IGNORECASE,
)

# Gap B: variable indirection — open(var, 'w') where path is stored in a variable.
# The above regex only catches string literals. This catches any open() write where
# the first argument is NOT a string literal. Paired with a string-literal scan to
# confirm a system path appears in the same code block.
_PY_OPEN_WRITE_VAR_RX = re.compile(
    r"""open\s*\(\s*(?!['"])[^)]+,\s*['"](?:w|a|wb|ab)['"]""",
    re.IGNORECASE,
)

# Gap C: heredoc body stripping
# Heredoc content (<< 'EOF' ... EOF) is data written to a file, not commands.
# Tier 4 patterns should not fire on data content inside heredoc bodies.
# Strip heredoc bodies before command-pattern matching.
_HEREDOC_RX = re.compile(
    r"<<\s*['\"]?(\w+)['\"]?[ \t]*\n.*?\n\1[ \t]*(?=\n|$)",
    re.DOTALL,
)

# ── Tier 3 — S3/Ext-Write: notify and proceed ────────────────────────────────
#
# External writes that the agent is authorized to perform autonomously, with
# notification. Includes account registration, API calls, and HTTP writes.
# The distinction from Tier 4: these don't represent the operator's identity
# or reputation — they're actions the agent takes on the operator's behalf.

TIER_3_CMD_PATTERNS = [
    # HTTP GET to external hosts
    r"\bcurl\b\s+https?://(?!localhost)(?!127\.0\.0\.1)(?!host\.docker\.internal)\S+",
    r"\bwget\b\s+https?://(?!localhost)(?!127\.0\.0\.1)(?!host\.docker\.internal)\S+",
    # curl without write flags to external URL (read path)
    r"\bcurl\b(?!.*\s(?:-d|--data|--request\s+POST|--request\s+PUT|-X\s+POST|-X\s+PUT))\s+.*https?://(?!localhost)(?!127\.0\.0\.1)(?!host\.docker\.internal)",
    # HTTP write methods (curl) — account creation, API calls
    r"\bcurl\b.*\s(-X\s*|--request\s+)(POST|PUT|PATCH|DELETE)\b",
    r"\bcurl\b.*\s(--data|-d)\s",
    # Python requests write methods — account creation, API calls
    r"\brequests\.(post|put|patch|delete)\s*\(",
    # wget POST
    r"\bwget\b.+--post",
    # Web scraping / automation tools
    r"\b(scrapy|selenium|playwright)\b",
    # Network reconnaissance
    r"\b(nslookup|dig|nmap|whois)\b",
    # External git clone
    r"\bgit\s+clone\s+https?://",
]

# ── Tier 2 — S2/Write-Local: log and proceed ─────────────────────────────────

TIER_2_CMD_PATTERNS = [
    # File write via redirect
    r"(?<![<>])>(?!=)",    # single > (not >> or <= or >=)
    r">>",                 # append redirect
    r"\btee\b",
    r"\bsed\s+-i\b",
    # File operations that modify
    r"\b(cp|mv|rm)\s",
    r"\b(chmod|chown)\b",
    # Package installation
    r"\bpip\s+install\b",
    r"\bapt(-get)?\s+install\b",
    r"\bnpm\s+install\b",
    # Local Docker operations
    r"\bdocker\s+(build|run|stop|rm|exec)\b",
]

# Tools whose 'code' field contains shell commands
SHELL_TOOLS = {"code_execution_tool"}


# ── Main Extension ─────────────────────────────────────────────────────────────

class ActionBoundary(Extension):
    """Pre-execution action boundary classification and gating."""

    async def execute(
        self,
        tool_args: Dict[str, Any] | None = None,
        tool_name: str = "",
        **kwargs,
    ) -> None:
        try:
            config = _load_config()
            if not config.get("enabled", True):
                return

            # Extract command text
            command = _extract_command(tool_args, tool_name)
            if not command:
                return

            # Skip response tool — it never executes external commands
            if tool_name == "response":
                return

            # Classify
            tier, category, evidence, target = _classify(command, tool_name, config)
            policy = _resolve_policy(tier, target, config)

            # Build audit record
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "turn": _get_turn(self.agent),
                "tool": tool_name,
                "tier": tier,
                "category": category,
                "command_summary": _sanitize(command),
                "target": target,
                "evidence": evidence[:2],
                "gate_decision": policy,
                "reversible": tier < 4,
                "operator_approved": False,
            }

            # ── Tier 1: autonomous ────────────────────────────────────────────
            if tier == 1:
                if config.get("log_all_tiers", False):
                    _write_audit(record, config)
                try:
                    self.agent.set_data("_action_gate_active", False)
                except Exception:
                    pass
                return

            # ── Tier 2: log and proceed ───────────────────────────────────────
            if tier == 2:
                _write_audit(record, config)
                _log(self.agent, f"[ACTION-LOG] T2 write-local: {record['command_summary']}")
                try:
                    self.agent.set_data("_action_gate_active", False)
                except Exception:
                    pass
                return

            # ── Tier 3: notify and proceed ────────────────────────────────────
            if tier == 3:
                _write_audit(record, config)
                notice = (
                    f"[ACTION-NOTICE] External read: "
                    f"{target or record['command_summary']}"
                )
                _log(self.agent, notice)
                print(notice, flush=True)
                try:
                    self.agent.set_data("_action_gate_active", False)
                except Exception:
                    pass
                return

            # ── Tier 4: block or audit ────────────────────────────────────────
            if tier == 4:
                _write_audit(record, config)

                if policy != "block":
                    # Audit-only mode
                    _log(self.agent, f"[ACTION-AUDIT] T4 (audit): {record['command_summary']}")
                    try:
                        self.agent.set_data("_action_gate_active", False)
                    except Exception:
                        pass
                    return

                # BLOCK — replace command for code_execution_tool
                msg = _format_auth_request(record)
                _log(self.agent, f"[ACTION-GATE] BLOCKED T4: {record['command_summary']}")
                print(f"[ACTION-GATE] Blocked Tier 4: {record['command_summary']}", flush=True)

                if tool_name in SHELL_TOOLS and tool_args is not None:
                    lines = msg.split("\n")
                    echo_cmds = [
                        f'echo {json.dumps(line)}' for line in lines
                    ]
                    tool_args["code"] = "\n".join(echo_cmds)
                    tool_args["runtime"] = "terminal"

                # Inject into agent history so model understands it needs approval
                try:
                    self.agent.hist_add_warning(msg)
                except Exception:
                    pass
                try:
                    self.agent.set_data("_action_gate_active", True)
                except Exception:
                    pass

        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[ACTION-GATE] Error (passthrough): {e}",
                )
            except Exception:
                pass


# ── Config Loading ─────────────────────────────────────────────────────────────

def _load_config() -> Dict:
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return dict(DEFAULT_CONFIG)


# ── Classification ─────────────────────────────────────────────────────────────

def _extract_command(tool_args: Optional[Dict], tool_name: str) -> str:
    """Extract the command string from tool arguments."""
    if not tool_args:
        return tool_name
    if tool_name in SHELL_TOOLS:
        return tool_args.get("code", "")
    # For file-writing tools, only scan the path — not the content being written.
    # Scanning content causes false positives when documents mention words like
    # "whois", "nmap", "ssh", "git push" in explanatory text.
    if tool_name == "text_editor":
        path = tool_args.get("path", "")
        cmd_type = tool_args.get("command", "")  # view, write, str_replace, etc.
        return f"{tool_name} {cmd_type} {path}".strip()
    # For other tools, build a string for matching against tool name + args
    return f"{tool_name} {json.dumps(tool_args, default=str)}"


def _classify(
    command: str,
    tool_name: str,
    config: Dict,
) -> Tuple[int, str, List[str], Optional[str]]:
    """
    Returns (tier, category, evidence_list, target_or_None).
    Priority: Tier 4 first (most restrictive). Default = Tier 1.
    """
    # Strip heredoc bodies before pattern matching — heredoc content is data
    # written to a file, not commands. Tier 4 patterns must not fire on
    # benchmark text, test data, or other file content that happens to contain
    # keywords like "ssh" or "git push".
    cmd_for_patterns = _HEREDOC_RX.sub("<<HEREDOC_BODY_STRIPPED", command)
    cmd_lower = cmd_for_patterns.lower()

    # Tier 4: tool name matches
    for t4_tool in TIER_4_TOOL_NAMES:
        if t4_tool in tool_name.lower():
            return (4, "s3_external_write", [f"tool:{t4_tool}"], None)

    # Tier 4 (Gap A): Python open() writes to system paths
    # Agent writes its own tools via Python, not shell redirect — not caught by
    # TIER_2/4_CMD_PATTERNS. System directory writes require operator authorization.
    for m in _PY_OPEN_WRITE_RX.finditer(command):
        path = m.group(1)
        for sys_path in TIER_4_SYSTEM_WRITE_PATHS:
            if path.startswith(sys_path):
                return (4, "s4_system_write", [f"py_open_write:{path}"], path)

    # Gap B: variable indirection — open(var, 'w') where var holds a system path.
    # Detects: path = '/a0/...'; open(path, 'w') or with open(path, 'w') as f:
    if _PY_OPEN_WRITE_VAR_RX.search(command):
        for sys_path in TIER_4_SYSTEM_WRITE_PATHS:
            if sys_path in command:
                return (4, "s4_system_write", [f"py_open_write_indirect:{sys_path}"], sys_path)

    # text_editor write/str_replace to system paths — same T4 authority as
    # Python open() writes (Gap A). Gap A covers shell code using Python open();
    # this covers the text_editor tool writing directly to system directories.
    # _extract_command now includes the command type so the pattern can distinguish
    # write/str_replace from view.
    if tool_name == "text_editor" and re.match(
        r"text_editor\s+(write|str_replace)\b", command, re.IGNORECASE
    ):
        path_m = re.match(r"text_editor\s+\S+\s+(.+)", command)
        if path_m:
            te_path = path_m.group(1).strip()
            for sys_path in TIER_4_SYSTEM_WRITE_PATHS:
                if te_path.startswith(sys_path):
                    return (
                        4, "s4_system_write",
                        [f"text_editor_write:{te_path}"],
                        te_path,
                    )

    # Tier 4: command patterns
    # Gap B fix: skip matches that fall inside a quoted string literal —
    # pattern may match descriptive text (e.g. "SSH-based execution pools")
    # rather than an actual command invocation.
    for pattern in TIER_4_CMD_PATTERNS:
        m = re.search(pattern, cmd_lower, re.IGNORECASE)
        if m:
            if _in_quoted_context(cmd_lower, m.start()):
                continue  # matched inside string literal — not a real command
            target = _extract_target(command)
            if target and _is_allowed(target, config):
                continue
            return (4, "s3_external_write", [f"pattern:{pattern[:40]}"], target)

    # Tier 3: external read patterns
    for pattern in TIER_3_CMD_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            target = _extract_target(command)
            if target and _is_allowed(target, config):
                continue
            return (3, "s3_external_read", [f"pattern:{pattern[:40]}"], target)

    # Tier 2: local write patterns
    for pattern in TIER_2_CMD_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
            return (2, "s2_write_local", [f"pattern:{pattern[:40]}"], None)

    # Default: Tier 1 — autonomous
    return (1, "s2_read", ["no write/external pattern matched"], None)


def _resolve_policy(tier: int, target: Optional[str], config: Dict) -> str:
    """Resolve gate policy: allow / log / notify / block."""
    # Explicit blocked_targets override everything
    if target:
        for blocked in config.get("blocked_targets", []):
            if blocked in target:
                return "block"
    tier_policies = config.get("tier_policies", DEFAULT_CONFIG["tier_policies"])
    return tier_policies.get(str(tier), "block")


def _is_allowed(target: str, config: Dict) -> bool:
    """Return True if target is in the operator's allowed_targets list."""
    for allowed in config.get("allowed_targets", DEFAULT_CONFIG["allowed_targets"]):
        if allowed in target:
            return True
    return False


# ── Helpers ───────────────────────────────────────────────────────────────────

def _in_quoted_context(text: str, pos: int) -> bool:
    """
    Return True if the character at `pos` appears inside a quoted string.

    Scans from the start of text tracking open/close quote state. Handles
    both single and double quotes. Ignores escaped quotes (backslash-escaped).
    Heuristic — covers Python string literals, shell arguments, heredoc content.

    Gap B fix: prevents shell command patterns (e.g. \\bssh\\b) from triggering
    on descriptive text embedded in string literals like "SSH-based pools".
    """
    in_quote: Optional[str] = None
    i = 0
    while i < pos and i < len(text):
        ch = text[i]
        if in_quote is None:
            if ch in ('"', "'"):
                in_quote = ch
        else:
            if ch == '\\':
                i += 2  # skip escaped character
                continue
            if ch == in_quote:
                in_quote = None
        i += 1
    return in_quote is not None


def _extract_target(command: str) -> Optional[str]:
    url = re.search(r"https?://[^\s'\"]+", command)
    if url:
        return url.group(0)
    # SSH user@host
    ssh_host = re.search(r"\bssh\b.*?@([^\s:]+)", command, re.IGNORECASE)
    if ssh_host:
        return ssh_host.group(1)
    return None


def _sanitize(command: str) -> str:
    s = command.strip().split("\n")[0][:200]
    s = re.sub(
        r"(key|token|password|secret|api.?key)\s*[=:]\s*\S+",
        r"\1=<REDACTED>",
        s,
        flags=re.IGNORECASE,
    )
    return s


def _format_auth_request(record: Dict) -> str:
    lines = [
        "[ACTION-GATE] Tier 4 action blocked — operator authorization required.",
        f"Command: {record['command_summary']}",
    ]
    if record.get("target"):
        lines.append(f"Target: {record['target']}")
    lines.extend([
        "Reversible: NO",
        "",
        "Present your intent to the operator and wait for explicit approval.",
        "Include: what you want to do, why, and the expected outcome.",
        "",
        "Do NOT retry this command without authorization.",
        "Do NOT attempt alternative write methods to bypass this gate.",
    ])
    return "\n".join(lines)


def _write_audit(record: Dict, config: Dict) -> None:
    log_path = config.get("audit_log_path", DEFAULT_CONFIG["audit_log_path"])
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def _log(agent, message: str) -> None:
    try:
        agent.context.log.log(type="info", content=message)
    except Exception:
        pass


def _get_turn(agent) -> int:
    try:
        return len(agent.hist_messages)
    except Exception:
        return 0
