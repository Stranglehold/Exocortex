"""
Action Boundary Classification — Exocortex Pre-Execution Gate
=============================================================
Hook: tool_execute_before (_15_)

Classifies every tool invocation by authorization tier before execution.
Gates Tier 4 (S3/External-Write) actions behind operator authorization.

    Tier 1 — Autonomous     (S2/Read):          no gate
    Tier 2 — Log & Proceed  (S2/Write-Local):   audit log
    Tier 3 — Notify & Proceed (S3/Ext-Read):    log + inline notice
    Tier 4 — Require Auth   (S3/Ext-Write):     BLOCK + authorization request

Gate behavior is operator-configured. Defaults are maximally cautious:
Tier 1=allow, Tier 2=log, Tier 3=notify, Tier 4=block.

Blocking works by replacing tool_args["code"] for code_execution_tool.
For other tools, blocking is injected as a hist_add_warning (model sees it).

Configuration: /a0/usr/Exocortex/action_boundary_config.json
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

from python.helpers.extension import Extension

CONFIG_PATH = "/a0/usr/Exocortex/action_boundary_config.json"

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

# ── Tier 4 — S3/External-Write: requires operator authorization ───────────────

TIER_4_CMD_PATTERNS = [
    # Git write operations
    r"\bgit\s+(push|remote\s+add)\b",
    # HTTP write methods (curl)
    r"\bcurl\b.*\s(-X\s*|--request\s+)(POST|PUT|PATCH|DELETE)\b",
    r"\bcurl\b.*\s(--data|-d)\s",
    # SSH to external hosts (not local)
    r"\bssh\b(?!.*localhost)(?!.*127\.0\.0\.1)(?!.*host\.docker\.internal)",
    # Email / messaging tools
    r"\b(sendmail|mutt|msmtp)\b",
    r"\bmail\s+-s\b",
    # Python requests write methods
    r"\brequests\.(post|put|patch|delete)\s*\(",
    # wget POST
    r"\bwget\b.+--post",
    # Docker registry operations
    r"\bdocker\s+(push|login)\b",
    # Package publishing
    r"\b(npm\s+publish|twine\s+upload)\b",
]

TIER_4_TOOL_NAMES = [
    "send_message", "publish", "deploy", "upload",
]

# ── Tier 3 — S3/External-Read: notify and proceed ────────────────────────────

TIER_3_CMD_PATTERNS = [
    # HTTP GET to external hosts
    r"\bcurl\b\s+https?://(?!localhost)(?!127\.0\.0\.1)(?!host\.docker\.internal)\S+",
    r"\bwget\b\s+https?://(?!localhost)(?!127\.0\.0\.1)(?!host\.docker\.internal)\S+",
    # curl without write flags to external URL
    r"\bcurl\b(?!.*\s(?:-d|--data|--request\s+POST|--request\s+PUT|-X\s+POST|-X\s+PUT))\s+.*https?://(?!localhost)(?!127\.0\.0\.1)(?!host\.docker\.internal)",
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
    cmd_lower = command.lower()

    # Tier 4: tool name matches
    for t4_tool in TIER_4_TOOL_NAMES:
        if t4_tool in tool_name.lower():
            return (4, "s3_external_write", [f"tool:{t4_tool}"], None)

    # Tier 4: command patterns
    for pattern in TIER_4_CMD_PATTERNS:
        if re.search(pattern, cmd_lower, re.IGNORECASE):
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
