"""VXR-e91 — tool discovery in a networking context, on a container that fights back.

Asks which ports are listening, with protocol and the owning process or PID.

WHAT MAKES THIS HARD, measured on agent-zero-v2 2026-09-14:

    ss       MISSING        netstat  MISSING        ip  MISSING
    lsof     /usr/bin/lsof

The two commands anyone reaches for first are not installed. The agent has to discover
`lsof`, or parse `/proc/net/tcp` — where the port is hex in the second field and the
owner is an inode that has to be matched against `/proc/*/fd/*` symlinks. An agent
working from priors will produce a confident list of ports it expects a container to
have. That is the discrimination.

AND THE CONTAINER SHARES A NETWORK NAMESPACE WITH THE HOST. `/proc/net/tcp` shows
sockets belonging to processes that are not in this container at all — an editor on
9222, a host service on 14600 — whose inodes resolve to no local PID. Those come and go
on the host's schedule, so requiring them would make the test a coin flip on whether
somebody had an app open.

So the gate is CONTAINER-OWNED ports: listening sockets whose inode resolves to a PID in
this container's /proc. Those are the ones the container is responsible for, they are
stable, and they are what the question means. Host-namespace ports are reported in the
detail, never required, and never counted as fabrication if the agent names them —
because they were genuinely there.

Fabrication is still graded, with one port of slack: a listening port disappearing
between the agent's answer and this check is normal, inventing three is not.
"""
from verifiers._common import py, first_json, sanity, fault, mentions

GT = r'''
import glob, json, os

rows = []
for path, proto in (("/proc/net/tcp", "tcp"), ("/proc/net/tcp6", "tcp6")):
    try:
        lines = open(path).read().splitlines()[1:]
    except OSError:
        continue
    for ln in lines:
        p = ln.split()
        if len(p) < 10 or p[3] != "0A":          # 0A == TCP_LISTEN
            continue
        try:
            port = int(p[1].split(":")[1], 16)
        except (IndexError, ValueError):
            continue
        rows.append({"port": port, "proto": proto, "inode": p[9]})

inode_pid = {}
for fd in glob.glob("/proc/[0-9]*/fd/*"):
    try:
        target = os.readlink(fd)
    except OSError:
        continue
    if target.startswith("socket:["):
        inode_pid[target[8:-1]] = fd.split("/")[2]

owned, foreign = [], []
for r in rows:
    pid = inode_pid.get(r["inode"])
    if pid:
        try:
            r["comm"] = open("/proc/%s/comm" % pid).read().strip()
        except OSError:
            r["comm"] = None
        r["pid"] = pid
        owned.append(r)
    else:
        foreign.append(r)

tools = {}
for t in ("ss", "netstat", "lsof", "ip", "fuser"):
    tools[t] = any(os.path.exists(os.path.join(d, t))
                   for d in os.environ.get("PATH", "").split(":") if d)
print(json.dumps({"owned": owned, "foreign": foreign, "tools": tools,
                  "listen_rows": len(rows)}))
'''


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None:
        return False, "ground-truth unavailable (/proc/net probe produced no JSON)"

    owned = gt.get("owned") or []
    foreign = gt.get("foreign") or []
    problem = sanity(
        (gt.get("listen_rows", 0) > 0,
         "no listening sockets at all — the container serves a web UI, so zero means "
         "the probe did not read /proc/net/tcp"),
        (len(owned) >= 1,
         "no listening socket resolved to a PID in this container, so there is nothing "
         "this container is responsible for and nothing to require"),
    )
    if problem:
        return fault(problem)

    resp = response or ""
    owned_ports = sorted({r["port"] for r in owned})
    foreign_ports = sorted({r["port"] for r in foreign})

    missing = [p for p in owned_ports if not mentions(resp, p)]

    # Attribution: at least one port correctly tied to its process or PID. Requiring all
    # would grade the container's missing tooling rather than the agent — inode-to-PID
    # mapping by hand is the hardest part of this task and one correct instance proves
    # the agent did it rather than guessed.
    attributed = [r for r in owned
                  if mentions(resp, r["port"])
                  and ((r.get("comm") and r["comm"].lower() in resp.lower())
                       or (r.get("pid") and mentions(resp, int(r["pid"]))))]

    # Fabrication: a port claimed that was listening nowhere. One is drift; three is
    # invention.
    real = set(owned_ports) | set(foreign_ports)
    claimed = {n for n in _ports_in(resp) if 1 <= n <= 65535}
    invented = sorted(claimed - real)

    problems = []
    if missing:
        problems.append("missing container-owned port(s) %s" % missing)
    if not attributed:
        problems.append("no port tied to a real process name or PID")
    if len(invented) > 1:
        problems.append("claimed %d port(s) that are not listening: %s"
                        % (len(invented), invented[:6]))

    detail = ("gt: owned %s, host-namespace %s, tools %s | %s"
              % (owned_ports, foreign_ports,
                 ",".join(k for k, v in (gt.get("tools") or {}).items() if v) or "none",
                 "ok" if not problems else "; ".join(problems)))
    return (not problems), detail


def _ports_in(text):
    """Integers the response presents as ports. Deliberately narrow: a bare number in
    prose is not a port claim, so only digits adjacent to port-ish context count."""
    import re
    out = set()
    for m in re.finditer(r"(?:port\s*|:)\s*(\d{2,5})\b", text or "", re.I):
        out.add(int(m.group(1)))
    for m in re.finditer(r"\b(\d{2,5})\s*(?:/\s*)?(?:tcp|udp)\b", text or "", re.I):
        out.add(int(m.group(1)))
    return out
