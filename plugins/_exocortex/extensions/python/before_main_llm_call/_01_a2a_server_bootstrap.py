"""
A2A Server Bootstrap — Daemon Launcher (clone-and-go)
=====================================================
Hook: before_main_llm_call (_01_, just after the idle_watch bootstrap)

Keeps the Exocortex a2a_server daemon alive, the same way _00_idle_watch_bootstrap
keeps idle_watch alive: on each turn (throttled) it checks a pidfile and, if the
daemon isn't running, generates the runtime config and spawns it DETACHED.

Why a bootstrap and not /etc/supervisor: same reason as idle_watch — the daemon
ships in the plugin (services/a2a_server/) and self-launches, so it's clone-and-go
and survives A0 image rebuilds. No container-level edit to be wiped.

What it does before launching:
  - ensures the org dirs exist (org/reports/roles)
  - writes the runtime a2a_config.json, injecting THIS container's real A0 token
    (create_auth_token) into agent_connection.api_key — so the a2a_server can
    authenticate to its own A0 REST API regardless of which container it's in.
    (A hardcoded token would only work on the container it was minted on.)

The a2a_server exposes a standard A2A endpoint on :8200 (agent card at
/.well-known/agent.json, tasks via message/send JSON-RPC) and proxies tasks
into A0's /api/api_message. It runs as `python -m a2a_server.run` with cwd at
the services/ dir so the package imports.
"""

import os
import json
import subprocess
import time

from agent import LoopData
from helpers.extension import Extension

_PYTHON       = "/opt/venv-a0/bin/python3"
_SERVICES_DIR = "/a0/usr/plugins/_exocortex/services"
_A2A_DIR      = "/a0/usr/plugins/_exocortex/services/a2a_server"
_ORG_DIR      = "/a0/usr/organizations"
_CFG_PATH     = "/a0/usr/organizations/a2a_config.json"
_OFFICE       = "/a0/usr/workdir/workspace/office"
_PIDFILE      = "/a0/usr/workdir/workspace/office/.a2a_server.pid"
_LOGFILE      = "/a0/usr/workdir/workspace/office/a2a_server.log"

# The A2A-facing key (clients / Hermes present this to the a2a_server). Fixed by
# design so the orchestrator can be configured once. Distinct from the A0 token.
_A2A_CLIENT_KEY = "hermes-a2a-token-2026"

_CHECK_INTERVAL = 60
_last_check     = 0.0


class A2AServerBootstrap(Extension):
    """Spawns and keeps the a2a_server daemon alive. Clone-and-go launcher."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        global _last_check
        try:
            if self.agent.get_data(self.agent.__class__.DATA_NAME_SUPERIOR) is not None:
                return
            now = time.time()
            if now - _last_check < _CHECK_INTERVAL:
                return
            _last_check = now

            if not os.path.isdir(_A2A_DIR) or not os.path.exists(_PYTHON):
                return
            if _daemon_alive():
                return

            _prep_config()
            _spawn_daemon()
        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[A2A-BOOT] bootstrap error (passthrough): {e}",
                )
            except Exception:
                pass


def _prep_config() -> None:
    """Write the runtime a2a_config with THIS container's real A0 token."""
    try:
        from helpers.settings import create_auth_token
        token = create_auth_token()
    except Exception:
        token = ""
    for d in (_ORG_DIR, os.path.join(_ORG_DIR, "reports"), os.path.join(_ORG_DIR, "roles")):
        os.makedirs(d, exist_ok=True)

    cfg = {}
    if os.path.exists(_CFG_PATH):
        try:
            with open(_CFG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    cfg.setdefault("host", "0.0.0.0")
    cfg.setdefault("port", 8200)
    cfg.setdefault("authentication", {"scheme": "api_key", "api_key": _A2A_CLIENT_KEY})
    cfg.setdefault("task_queue", {"max_concurrent": 1, "max_queued": 10, "task_timeout_seconds": 600})
    cfg.setdefault("salute_poll_interval_seconds", 2)
    cfg["org_dir"]     = _ORG_DIR
    cfg["reports_dir"] = os.path.join(_ORG_DIR, "reports")
    cfg["roles_dir"]   = os.path.join(_ORG_DIR, "roles")
    # the connection to THIS A0 — real token every start (handles token rotation)
    cfg["agent_connection"] = {"base_url": "http://localhost:80", "api_key": token}
    try:
        tmp = _CFG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp, _CFG_PATH)
    except Exception:
        pass


def _daemon_alive() -> bool:
    try:
        if not os.path.exists(_PIDFILE):
            return False
        with open(_PIDFILE, "r", encoding="utf-8") as f:
            pid = int((f.read() or "0").strip())
        if pid <= 0:
            return False
        os.kill(pid, 0)
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                if b"a2a_server" not in f.read():
                    return False
        except Exception:
            pass
        return True
    except (ProcessLookupError, ValueError, PermissionError):
        return False
    except Exception:
        return False


def _spawn_daemon() -> None:
    os.makedirs(_OFFICE, exist_ok=True)
    logf = open(_LOGFILE, "ab")
    proc = subprocess.Popen(
        [_PYTHON, "-m", "a2a_server.run", "--config", _CFG_PATH],
        stdout=logf, stderr=logf, stdin=subprocess.DEVNULL,
        start_new_session=True,      # detach: survives run_ui restart
        cwd=_SERVICES_DIR,           # so `a2a_server` package imports
    )
    try:
        with open(_PIDFILE, "w", encoding="utf-8") as f:
            f.write(str(proc.pid))
    except Exception:
        pass
    print(f"[A2A-BOOT] Spawned a2a_server daemon (pid {proc.pid}) on :8200.", flush=True)
