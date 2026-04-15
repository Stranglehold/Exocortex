"""
host_daemon.py — Exocortex Service Control Daemon

Runs OUTSIDE Docker, on the Windows host. Provides HTTP endpoints for
starting, stopping, and restarting Exocortex-related containers. The OSS
control panel calls this daemon to manage services without needing the
Docker socket mounted into the application containers.

Why this exists:
  OSS and swarmfish run inside their own containers. Neither has access
  to the Docker daemon, so neither can docker-start another container.
  This daemon lives on the host where Docker is installed, accepts
  authenticated HTTP requests, and runs docker CLI commands on behalf
  of the panel.

Security:
  - Bound to 127.0.0.1 by default (localhost-only)
  - Token auth via X-Control-Token header (default: dev_control_token)
  - Container whitelist — only pre-declared containers can be touched
  - POST required for mutations (start/stop/restart)
  - CORS enabled for localhost origins so the browser panel can call it
  - All docker commands run through subprocess with a hard-coded argv;
    no shell interpolation of user input

Running:
  python services/control/host_daemon.py
  # or set HOST_CONTROL_PORT / HOST_CONTROL_TOKEN env vars to override

Endpoints:
  GET  /                            → HTML status dashboard (bootstrap UI)
  GET  /health                      → {"ok": true}
  GET  /services                    → all services + containers + states
  GET  /services/<service>          → one service status
  POST /services/<service>/start    → docker start <containers in order>
  POST /services/<service>/stop     → docker stop <containers in reverse>
  POST /services/<service>/restart  → stop then start

Dependencies: Python 3.9+ stdlib only. No pip install required.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST = os.environ.get("HOST_CONTROL_HOST", "127.0.0.1")
PORT = int(os.environ.get("HOST_CONTROL_PORT", "9900"))
TOKEN = os.environ.get("HOST_CONTROL_TOKEN", "dev_control_token")
DOCKER_BIN = os.environ.get("DOCKER_BIN", "docker")  # must be on PATH

# Service registry. Start order is deps-first; stop order is reverse.
# Adding a new service here is the only place; endpoints are generated from it.
SERVICES = {
    "oss": {
        "display_name": "OSS Intelligence",
        "containers": ["oss_postgres", "oss_app"],
        "health_url": "http://127.0.0.1:7731/api/health",
    },
    "swarmfish": {
        "display_name": "SWARMFISH Committee",
        "containers": ["swarmfish_postgres", "swarmfish_redis", "swarmfish_app"],
        "health_url": "http://127.0.0.1:7732/health",
    },
    "agent-zero": {
        "display_name": "Agent Zero",
        "containers": ["exocortex_v16"],
        "health_url": None,
    },
}

# Container name safety check — only allow names matching this pattern.
# This is a second-layer defense on top of the whitelist.
_SAFE_CONTAINER_RX = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}$")


# ---------------------------------------------------------------------------
# Docker operations
# ---------------------------------------------------------------------------

def _ensure_docker_available():
    """Fail fast at startup if docker CLI is missing."""
    if shutil.which(DOCKER_BIN) is None:
        sys.stderr.write(f"[HOST-CTRL] ERROR: docker binary {DOCKER_BIN!r} not found on PATH.\n")
        sys.stderr.write("[HOST-CTRL] Install Docker Desktop and ensure it is running.\n")
        sys.exit(1)


def _validate_container(name: str) -> bool:
    """Check a container name is in the whitelist and matches the safe pattern."""
    if not _SAFE_CONTAINER_RX.match(name):
        return False
    for svc in SERVICES.values():
        if name in svc["containers"]:
            return True
    return False


def _docker(*args, timeout: int = 30) -> dict:
    """Run a docker command. Returns {ok, stdout, stderr, returncode}."""
    cmd = [DOCKER_BIN, *args]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "docker command timed out", "returncode": -1}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": f"docker exec failed: {e}", "returncode": -1}


def _container_state(name: str) -> dict:
    """Return {status, exists} for a container."""
    if not _validate_container(name):
        return {"exists": False, "status": "forbidden"}
    r = _docker("inspect", "--format", "{{.State.Status}}", name, timeout=5)
    if not r["ok"]:
        if "No such container" in r["stderr"]:
            return {"exists": False, "status": "missing"}
        return {"exists": False, "status": "error", "error": r["stderr"]}
    return {"exists": True, "status": r["stdout"]}


def _service_status(service_name: str) -> dict:
    """Aggregate state for one service."""
    svc = SERVICES.get(service_name)
    if svc is None:
        return {"error": "unknown service"}
    states = []
    all_running = True
    any_running = False
    for c in svc["containers"]:
        s = _container_state(c)
        states.append({"name": c, **s})
        if s.get("status") != "running":
            all_running = False
        if s.get("status") == "running":
            any_running = True
    return {
        "service":      service_name,
        "display_name": svc["display_name"],
        "containers":   states,
        "all_running":  all_running,
        "any_running":  any_running,
        "health_url":   svc.get("health_url"),
    }


def _service_start(service_name: str) -> dict:
    svc = SERVICES.get(service_name)
    if svc is None:
        return {"ok": False, "error": "unknown service"}
    results = []
    for c in svc["containers"]:
        if not _validate_container(c):
            results.append({"name": c, "ok": False, "error": "not in whitelist"})
            continue
        r = _docker("start", c, timeout=60)
        results.append({"name": c, "ok": r["ok"], "stderr": r["stderr"] or None})
    return {
        "ok": all(r["ok"] for r in results),
        "operations": results,
        "status": _service_status(service_name),
    }


def _service_stop(service_name: str) -> dict:
    svc = SERVICES.get(service_name)
    if svc is None:
        return {"ok": False, "error": "unknown service"}
    results = []
    # Reverse order: stop app before dependencies
    for c in reversed(svc["containers"]):
        if not _validate_container(c):
            results.append({"name": c, "ok": False, "error": "not in whitelist"})
            continue
        r = _docker("stop", c, timeout=30)
        results.append({"name": c, "ok": r["ok"], "stderr": r["stderr"] or None})
    return {
        "ok": all(r["ok"] for r in results),
        "operations": results,
        "status": _service_status(service_name),
    }


def _service_restart(service_name: str) -> dict:
    stop_result = _service_stop(service_name)
    start_result = _service_start(service_name)
    return {
        "ok": stop_result["ok"] and start_result["ok"],
        "stop": stop_result,
        "start": start_result,
        "status": _service_status(service_name),
    }


# ---------------------------------------------------------------------------
# HTML bootstrap status page
# ---------------------------------------------------------------------------

_STATUS_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Exocortex Host Control</title>
  <style>
    /* Design tokens — ported from docs/ui_references/exocortex.css */
    :root {
      --ds-duration-instant: 80ms;
      --ds-duration-fast: .15s;
      --ds-ease-out: cubic-bezier(.16, 1, .3, 1);
      --ds-surface-void: #060810;
      --ds-surface-base: #0a0f1a;
      --ds-surface-raised: #0f1629;
      --ds-surface-overlay: #151d35;
      --ds-surface-scrim: rgba(10,15,26,.92);
      --ds-text-primary: #f0f2f5;
      --ds-text-secondary: #b0b8c8;
      --ds-text-tertiary: #6b7a8d;
      --ds-border-subtle: rgba(148,163,184,.06);
      --ds-border-default: rgba(148,163,184,.12);
      --ds-border-strong: rgba(148,163,184,.22);
      --ds-border-accent: rgba(0,229,255,.25);
      --ds-accent-cyan: #00e5ff;
      --ds-accent-cyan-muted: rgba(0,229,255,.15);
      --ds-signal-positive: #34d399;
      --ds-signal-negative: #f87171;
      --ds-signal-warning: #fbbf24;
      --ds-signal-positive-muted: rgba(52,211,153,.15);
      --ds-signal-negative-muted: rgba(248,113,113,.15);
      --ds-shadow-md: 0 4px 12px rgba(0,0,0,.4);
      --ds-shadow-lg: 0 8px 24px rgba(0,0,0,.5);
      --ds-shadow-glow-cyan: 0 0 20px rgba(0,229,255,.06), 0 0 40px rgba(0,229,255,.03);
      --ds-radius-sm: 6px;
      --ds-radius-md: 10px;
      --ds-radius-pill: 999px;
    }
    * { box-sizing: border-box; }
    body {
      background:
        radial-gradient(ellipse at 20% 0%, rgba(0,229,255,.03) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 100%, rgba(139,92,246,.025) 0%, transparent 50%),
        var(--ds-surface-void);
      color: var(--ds-text-primary);
      font: 12px/1.5 'IBM Plex Mono',Consolas,monospace;
      margin: 0; padding: 24px;
      min-height: 100vh;
    }
    h1 {
      font-size: 14px; margin: 0 0 4px;
      letter-spacing: .12em; text-transform: uppercase;
      color: var(--ds-accent-cyan);
      text-shadow: 0 0 12px rgba(0,229,255,.3);
    }
    .sub { color: var(--ds-text-tertiary); font-size: 10px; margin-bottom: 20px; letter-spacing: .04em }
    .svc {
      background: var(--ds-surface-raised);
      border: 1px solid var(--ds-border-default);
      padding: 14px;
      margin-bottom: 12px;
      border-radius: var(--ds-radius-md);
      box-shadow: var(--ds-shadow-md);
      transition: border-color var(--ds-duration-fast) var(--ds-ease-out),
                  box-shadow var(--ds-duration-fast) var(--ds-ease-out);
    }
    .svc:hover {
      border-color: var(--ds-border-accent);
      box-shadow: var(--ds-shadow-glow-cyan), var(--ds-shadow-lg);
    }
    .hdr { display: flex; align-items: center; gap: 10px; margin-bottom: 8px }
    .name { font-weight: 600; color: var(--ds-text-primary); font-size: 13px }
    .pill {
      display: inline-flex; align-items: center;
      font-size: 9px; padding: 2px 10px;
      border-radius: var(--ds-radius-pill);
      border: 1px solid transparent;
      font-weight: 600; letter-spacing: .04em; text-transform: uppercase;
    }
    .pill-ok {
      background: var(--ds-signal-positive-muted);
      border-color: rgba(52,211,153,.4);
      color: var(--ds-signal-positive);
    }
    .pill-mu {
      background: var(--ds-border-subtle);
      border-color: var(--ds-border-default);
      color: var(--ds-text-tertiary);
    }
    .pill-err {
      background: var(--ds-signal-negative-muted);
      border-color: rgba(248,113,113,.4);
      color: var(--ds-signal-negative);
    }
    .ctr {
      font-size: 10px; color: var(--ds-text-tertiary);
      margin: 3px 0 3px 18px;
      font-variant-numeric: tabular-nums;
    }
    .ctr .state { display: inline-block; min-width: 72px; font-weight: 600 }
    .ctr .running { color: var(--ds-signal-positive) }
    .ctr .exited  { color: var(--ds-text-tertiary) }
    .ctr .missing { color: var(--ds-signal-negative) }
    .btns { display: flex; gap: 6px; margin-top: 10px }
    button {
      background: rgba(15,22,41,.5);
      color: var(--ds-text-secondary);
      border: 1px solid var(--ds-border-default);
      padding: 5px 12px;
      font: inherit; cursor: pointer;
      border-radius: var(--ds-radius-sm);
      transition: color var(--ds-duration-fast) var(--ds-ease-out),
                  background var(--ds-duration-fast) var(--ds-ease-out),
                  border-color var(--ds-duration-fast) var(--ds-ease-out),
                  box-shadow var(--ds-duration-fast) var(--ds-ease-out),
                  transform var(--ds-duration-instant) var(--ds-ease-out);
    }
    button:hover:not(:disabled) {
      color: var(--ds-accent-cyan);
      background: var(--ds-accent-cyan-muted);
      border-color: var(--ds-border-accent);
      box-shadow: var(--ds-shadow-glow-cyan), var(--ds-shadow-md);
      transform: scale(1.03);
    }
    button:active:not(:disabled) { transform: scale(.97) }
    button:disabled { opacity: .5; cursor: not-allowed; transform: none !important }
    button.btn-ok {
      border-color: rgba(52,211,153,.4);
      color: var(--ds-signal-positive);
      background: var(--ds-signal-positive-muted);
    }
    button.btn-ok:hover:not(:disabled) {
      background: rgba(52,211,153,.22);
      box-shadow: 0 0 16px rgba(52,211,153,.15), var(--ds-shadow-md);
      color: var(--ds-signal-positive);
      border-color: var(--ds-signal-positive);
    }
    button.btn-err {
      border-color: rgba(248,113,113,.4);
      color: var(--ds-signal-negative);
      background: var(--ds-signal-negative-muted);
    }
    button.btn-err:hover:not(:disabled) {
      background: rgba(248,113,113,.22);
      box-shadow: 0 0 16px rgba(248,113,113,.15), var(--ds-shadow-md);
      color: var(--ds-signal-negative);
      border-color: var(--ds-signal-negative);
    }
    button.btn-p {
      border-color: var(--ds-border-accent);
      color: var(--ds-accent-cyan);
      background: var(--ds-accent-cyan-muted);
    }
    #msg {
      padding: 8px 12px;
      background: var(--ds-surface-raised);
      border: 1px solid var(--ds-border-default);
      border-radius: var(--ds-radius-md);
      margin-top: 12px;
      font-size: 11px;
      color: var(--ds-text-secondary);
      min-height: 14px;
      box-shadow: var(--ds-shadow-md);
    }
    .token-box {
      padding: 10px 12px;
      background: var(--ds-surface-raised);
      border: 1px solid var(--ds-border-default);
      border-radius: var(--ds-radius-md);
      margin-bottom: 16px;
      box-shadow: var(--ds-shadow-md);
    }
    .token-box label {
      display: block;
      font-size: 9px;
      font-weight: 600;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: var(--ds-text-tertiary);
      margin-bottom: 6px;
    }
    .token-box input {
      width: 100%;
      background: var(--ds-surface-void);
      color: var(--ds-text-primary);
      border: 1px solid var(--ds-border-default);
      padding: 6px 10px;
      font: inherit;
      border-radius: var(--ds-radius-sm);
      outline: none;
      transition: border-color var(--ds-duration-fast) var(--ds-ease-out),
                  box-shadow var(--ds-duration-fast) var(--ds-ease-out);
    }
    .token-box input:focus {
      border-color: var(--ds-accent-cyan);
      box-shadow: 0 0 0 3px rgba(0,229,255,.1);
    }
  </style>
</head>
<body>
<h1>Exocortex Host Control</h1>
<div class="sub">Docker service management daemon · localhost-only · refresh every 5s</div>

<div class="token-box">
  <label>Control token (required for mutations)</label>
  <input id="token" type="password" placeholder="paste HOST_CONTROL_TOKEN">
</div>

<div id="services">Loading…</div>
<div id="msg">&nbsp;</div>

<script>
const TOKEN_KEY = 'host_control_token';
document.getElementById('token').value = localStorage.getItem(TOKEN_KEY) || '';
document.getElementById('token').addEventListener('input', (e) => {
  localStorage.setItem(TOKEN_KEY, e.target.value);
});

function stateClass(s) { return s === 'running' ? 'running' : (s === 'exited' || s === 'created') ? 'exited' : 'missing'; }
function pillClass(running) { return running ? 'pill pill-ok' : 'pill pill-mu'; }
function statusText(running, any) { return running ? 'ALL RUNNING' : (any ? 'PARTIAL' : 'STOPPED'); }

async function apiCall(path, method='GET') {
  const opts = { method, headers: { 'X-Control-Token': document.getElementById('token').value } };
  try {
    const r = await fetch(path, opts);
    return await r.json();
  } catch(e) {
    return { error: String(e) };
  }
}

async function load() {
  const data = await apiCall('/services');
  if (data.error) {
    document.getElementById('services').textContent = 'Error: ' + data.error;
    return;
  }
  const html = (data.services || []).map(s => {
    const cls = pillClass(s.all_running);
    const txt = statusText(s.all_running, s.any_running);
    const ctrs = s.containers.map(c => `
      <div class="ctr">
        <span class="state ${stateClass(c.status)}">${c.status || '?'}</span>
        ${c.name}
      </div>`).join('');
    return `
      <div class="svc">
        <div class="hdr">
          <span class="name">${s.display_name}</span>
          <span class="${cls}">${txt}</span>
        </div>
        ${ctrs}
        <div class="btns">
          <button class="btn-ok" onclick="act('${s.service}','start')" ${s.all_running ? 'disabled' : ''}>Start</button>
          <button class="btn-err" onclick="act('${s.service}','stop')" ${!s.any_running ? 'disabled' : ''}>Stop</button>
          <button class="btn-p" onclick="act('${s.service}','restart')">Restart</button>
        </div>
      </div>`;
  }).join('');
  document.getElementById('services').innerHTML = html;
}

async function act(service, action) {
  document.getElementById('msg').textContent = `${action}ing ${service}…`;
  const r = await apiCall('/services/' + service + '/' + action, 'POST');
  if (r.error) {
    document.getElementById('msg').textContent = `${action} failed: ${r.error}`;
  } else {
    document.getElementById('msg').textContent = `${service} ${action}: ${r.ok ? 'OK' : 'FAILED'}`;
  }
  load();
}

load();
setInterval(load, 5000);
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class ControlHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Log to stdout with a consistent tag so it's easy to grep
        sys.stdout.write("[HOST-CTRL] %s - %s\n" % (self.address_string(), format % args))
        sys.stdout.flush()

    # ---- helpers ----

    def _send_json(self, status: int, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status: int, html: str):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        # Allow any origin — localhost-bound + token auth makes this safe for dev.
        origin = self.headers.get("Origin") or "*"
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Control-Token")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Credentials", "false")

    def _authorized(self) -> bool:
        provided = self.headers.get("X-Control-Token") or ""
        return provided == TOKEN

    # ---- method dispatch ----

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/" or path == "/index.html":
            self._send_html(200, _STATUS_PAGE)
            return

        if path == "/health":
            self._send_json(200, {"ok": True, "daemon": "host-control", "services": list(SERVICES.keys())})
            return

        # All other GETs require auth
        if not self._authorized():
            self._send_json(401, {"error": "missing or invalid X-Control-Token"})
            return

        if path == "/services":
            all_status = [_service_status(name) for name in SERVICES.keys()]
            self._send_json(200, {"services": all_status})
            return

        # /services/<name>
        parts = path.strip("/").split("/")
        if len(parts) == 2 and parts[0] == "services":
            name = parts[1]
            if name not in SERVICES:
                self._send_json(404, {"error": "unknown service"})
                return
            self._send_json(200, _service_status(name))
            return

        self._send_json(404, {"error": "not found", "path": path})

    def do_POST(self):
        path = urlparse(self.path).path

        if not self._authorized():
            self._send_json(401, {"error": "missing or invalid X-Control-Token"})
            return

        # /services/<name>/<action>
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "services":
            name, action = parts[1], parts[2]
            if name not in SERVICES:
                self._send_json(404, {"error": "unknown service"})
                return
            if action == "start":
                self._send_json(200, _service_start(name))
                return
            if action == "stop":
                self._send_json(200, _service_stop(name))
                return
            if action == "restart":
                self._send_json(200, _service_restart(name))
                return
            self._send_json(400, {"error": f"unknown action {action!r}"})
            return

        self._send_json(404, {"error": "not found", "path": path})


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main():
    _ensure_docker_available()
    print(f"[HOST-CTRL] Starting Exocortex host control daemon")
    print(f"[HOST-CTRL]   bind:    {HOST}:{PORT}")
    print(f"[HOST-CTRL]   token:   {'(using env var)' if os.environ.get('HOST_CONTROL_TOKEN') else '(using default dev_control_token)'}")
    print(f"[HOST-CTRL]   docker:  {DOCKER_BIN}")
    print(f"[HOST-CTRL]   services: {list(SERVICES.keys())}")
    print(f"[HOST-CTRL]   status page: http://{HOST}:{PORT}/")
    print(f"[HOST-CTRL]")

    server = HTTPServer((HOST, PORT), ControlHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[HOST-CTRL] Shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
