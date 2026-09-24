#!/usr/bin/env python3
"""sync_agent_exports.py — keep the shared corpus fresh with the agents' work.

Mirrors each Agent-Zero container's workspace (wiki + field-reports) into the host
`agent-exports/<name>/` tree that the Opus Memory server indexes, then triggers a
reindex so the new work becomes searchable by the whole team.

WHY THIS EXISTS: the agents write wiki/field-reports inside their containers, but
the memory server indexes host directories only. There was no pipeline moving that
output to the host — v2 (Aporia) had 500+ docs trapped in-container and invisible to
search; v16/v17's hand-exports were stale. This closes that gap (2026-07-09).

Run with the memory-server venv python (it has fastmcp for the reindex trigger):
  D:\\Vibecode\\docker-mcp-server\\.venv-opus-memory\\Scripts\\python.exe scripts\\sync_agent_exports.py

Flags:
  --no-reindex     copy files only; don't trigger a reindex
  --force-reindex  reindex even if nothing changed since last sync
  --agent NAME     sync a single agent (v2|v16|v17)
  --ignore-health  refresh even when the embedder probe says it cannot serve

SAFETY (2026-08-19, Tier 1.2):
  * The file copy is STAGE-VERIFY-SWAP, not delete-then-copy. A failed `docker cp`
    used to leave the export tree already deleted — and agent-exports/ has never
    been tracked in git. On a 6-hourly timer that was four chances a day to destroy
    an agent's accumulated wiki permanently.
  * The refresh is HEALTH-GATED. It re-embeds only what changed (~12 min over ~43k
    chunks; the local LLM holds ~22 GB of the 24 GB card while loaded. Unattended,
    that would fire straight into Jake's inference server at an arbitrary hour.
    When the embedder probe fails the refresh DEFERS and the state signature is
    deliberately NOT advanced, so the pending content is retried next run instead
    of being marked 'unchanged' and never indexed.

COST NOTE: reindex() is a FULL rebuild (re-embeds ~43k chunks on the shared 3090),
so this script reindexes ONLY when the synced content actually changed. Schedule it
at a modest cadence (Windows Task Scheduler), e.g. every 6h. Since 2026-09-12 the
task runs through the hidden launcher (no console window; output appended to
scripts\\logs\\ExocortexAgentSync.log; exit code passed through, 3 = Docker off):
  schtasks /Create /TN "ExocortexAgentSync" /SC HOURLY /MO 6 /TR ^
    "wscript.exe //B //Nologo \"D:\\Vibecode\\Agent-Zero\\Exocortex\\scripts\\run_hidden.vbs\" ^
     \"D:\\Vibecode\\Agent-Zero\\Exocortex\\scripts\\logs\\ExocortexAgentSync.log\" ^
     \"D:\\Vibecode\\docker-mcp-server\\.venv-opus-memory\\Scripts\\python.exe\" ^
     \"D:\\Vibecode\\Agent-Zero\\Exocortex\\scripts\\sync_agent_exports.py\""
Incremental (append-only) indexing on the server would remove the full-rebuild cost
— flagged to Opus as the long-term memory-server improvement.
"""
import argparse
import hashlib
import json
import os
import shutil
import datetime
import subprocess
import time
import sys

from docker_probe import daemon_reachable, EXIT_DEFERRED   # beside this file in scripts/

EXPORT_ROOT = r"D:\Vibecode\Agent-Zero\Exocortex\agent-exports"
CONTAINER_WORKSPACE = "/a0/usr/workdir/workspace"
SUBDIRS = ["wiki", "field-reports"]          # workspace subdirs to export
# Export dir names are historical and deliberately STABLE: the memory index and
# prior search results cite agent-exports/<name>/..., so renaming would orphan
# those citations and duplicate content in the corpus. The mapping is agent-identity
# based, not container-name based:
#   v2  -> Aporia (agent-zero-v2, local ornith)
#   v17 -> Vek    (now the VekV2 container; Vek's data migrated 2026-08-03. The
#                  exocortex_v17 container still exists but is the RETIRED
#                  pre-migration host — syncing it would republish stale work.)
# v16 is retired (container exited); its historical export tree is left untouched
# rather than deleted, so its past work stays searchable.
AGENTS = {"v2": "agent-zero-v2", "v17": "VekV2"}
MCP_URL = "http://127.0.0.1:5055/mcp"  # 127.0.0.1, not localhost (Fable 2026-09-19, Jake's word): localhost resolves to ::1 first on this host,
#   the server binds IPv4 only, and urllib/httpx wait ~2 s before falling back; measured 2,038 ms vs 15 ms per connection.
STATE_FILE = os.path.join(EXPORT_ROOT, ".sync_state.json")

# docker cp mangles Unix container paths under Git Bash / MSYS; disable that.
_ENV = dict(os.environ, MSYS_NO_PATHCONV="1")


def _run(args, timeout=None):
    return subprocess.run(args, capture_output=True, text=True, env=_ENV, timeout=timeout)


def container_exists(container):
    return _run(["docker", "inspect", "-f", "{{.State.Status}}", container]).returncode == 0


def sync_agent(name, container):
    """Mirror the container's wiki + field-reports into agent-exports/<name>/.

    STAGE-VERIFY-SWAP, not delete-then-copy.

    This previously did `shutil.rmtree(sub_dest)` and *then* `docker cp`. If the copy
    failed for any reason — container stopped mid-run, a name docker cp refuses, a
    transient daemon error — the existing export tree was already gone, with no
    backup: agent-exports/ has never been tracked in git. On a recurring 6-hourly
    schedule that is four chances a day to permanently destroy an agent's accumulated
    wiki and field reports.

    Now: copy into a staging dir first, confirm it actually contains files, and only
    then replace the live tree. A failed copy leaves the existing export untouched.
    Destructive step last, behind a verified success.
    """
    dest = os.path.join(EXPORT_ROOT, name)
    files = 0
    for sub in SUBDIRS:
        src = f"{container}:{CONTAINER_WORKSPACE}/{sub}"
        sub_dest = os.path.join(dest, sub)
        staging = sub_dest + ".staging"

        # probe: does the subdir exist in the container?
        if _run(["docker", "exec", container, "test", "-d", f"{CONTAINER_WORKSPACE}/{sub}"]).returncode != 0:
            # exec fails on stopped containers; fall back to attempting the copy anyway
            if _run(["docker", "inspect", "-f", "{{.State.Running}}", container]).stdout.strip() == "true":
                continue

        os.makedirs(dest, exist_ok=True)
        shutil.rmtree(staging, ignore_errors=True)

        r = _run(["docker", "cp", src, staging])
        staged = (
            sum(len(fs) for _, _, fs in os.walk(staging)) if os.path.isdir(staging) else 0
        )

        if r.returncode != 0 or staged == 0:
            reason = r.stderr.strip()[:80] if r.returncode != 0 else "copy produced 0 files"
            existing = (
                sum(len(fs) for _, _, fs in os.walk(sub_dest)) if os.path.isdir(sub_dest) else 0
            )
            print(f"  [{name}] {sub}: SKIPPED ({reason}) — kept existing {existing} file(s)")
            shutil.rmtree(staging, ignore_errors=True)
            if existing:
                files += existing
            continue

        # Staging is good. Swap it in; keep the old tree until the swap succeeds.
        previous = sub_dest + ".previous"
        shutil.rmtree(previous, ignore_errors=True)
        try:
            if os.path.isdir(sub_dest):
                os.rename(sub_dest, previous)
            os.rename(staging, sub_dest)
        except OSError as exc:
            print(f"  [{name}] {sub}: SWAP FAILED ({exc}) — restoring previous tree")
            if os.path.isdir(previous) and not os.path.isdir(sub_dest):
                os.rename(previous, sub_dest)
            shutil.rmtree(staging, ignore_errors=True)
            continue
        shutil.rmtree(previous, ignore_errors=True)
        files += staged
    return files


def tree_signature(root):
    """Cheap change signature: sorted (relpath, size, mtime) over the export tree."""
    h = hashlib.sha256()
    for dirpath, _dn, filenames in os.walk(root):
        if ".sync_state.json" in dirpath:
            continue
        for fn in sorted(filenames):
            if fn == ".sync_state.json":
                continue
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
                h.update(f"{os.path.relpath(p, root)}|{st.st_size}|{int(st.st_mtime)}".encode("utf-8", "replace"))
            except OSError:
                pass
    return h.hexdigest()


# WHY A HEALTH PROBE AND NOT A VRAM NUMBER (changed 2026-09-19)
# ------------------------------------------------------------
# This used to defer unless >= 6000 MiB of VRAM was free, because `reindex_now()`
# re-embeds ALL ~43k chunks and the local LLM holds ~22 GB of the 24 GB card. The
# guard did its job too well: 22 deferrals in three days, last completed rebuild
# 2026-09-14, so her 09-16 and 09-18 work sat on disk unsearchable BY HER.
#
# Two things changed. We now call `refresh_now` (= `reindex(reuse=True)`): a chunk id
# is the sha256 of its content and parent, so unchanged text keeps its vector and the
# GPU work is proportional to what actually changed, not to the corpus. And we gate on
# whether the embedder can SERVE rather than on free VRAM, which was only ever a proxy
# for it — the proxy is what deferred 22 times while the embedder was fine.
#
# THE PROBE ASKS THE SERVER, NOT LM STUDIO, AND THAT IS DELIBERATE. On 2026-09-19 the
# server's own CUDA context died in a long-lived process: `index_status` still answered,
# LM Studio was healthy, and every `search_memory` returned "CUDA error: unknown error"
# for twelve hours. A probe of LM Studio would have reported all-clear and fired a
# refresh into a broken embedder. A probe that exercises the real embedding path catches
# it, and keeps working across the backend switch rather than needing to be rewritten
# for it.
EMBED_PROBE_QUERY = "health probe"


def embedder_healthy(base_url=None, timeout=25):
    """Can the server embed RIGHT NOW? -> (ok: bool, why: str).

    Exercises the query-embedding path end to end with a trivial search. Returns False
    with a reason rather than raising, so the caller can defer cleanly. Never returns
    True on an error it did not understand: unknown failure is unhealthy.
    """
    url = base_url or MCP_URL
    try:
        import asyncio
        from fastmcp import Client

        async def _go():
            async with Client(url) as client:
                # top_k, NOT limit (server signature: search_memory(query, top_k, client,
                # pointers_only)). pointers_only keeps it cheap; `client` names the probe in
                # the query log so it is not counted as an anonymous real search.
                return await client.call_tool(
                    "search_memory",
                    {"query": EMBED_PROBE_QUERY, "top_k": 1,
                     "client": "sync-health-probe", "pointers_only": True})

        out = asyncio.run(asyncio.wait_for(_go(), timeout=timeout))
        data = getattr(out, "data", out)
        text = str(data)
        # The embed path can fail while the call itself succeeds — the CUDA outage
        # returned a normal payload whose content was an error string.
        low = text.lower()
        for bad in ("cuda error", "error calling tool", "failed to embed", "out of memory"):
            if bad in low:
                return False, f"server answered but the embed path is broken: {bad}"
        return True, "embed path answered"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


# ─────────────────────────── THE IDLE GATE (2026-09-19, Opus's ruling) ────────────────────
# The hourly task is the CHECK interval, not the RUN interval. A refresh that starts while
# the agent is mid-cycle costs her memory recall for its whole duration: measured tonight,
# one CUDA refresh = 60+ minutes of zero recall and 90+ minutes of server unavailability,
# because LM Studio serves her chat model AND the embedder off one card.
#
# PREMISE CORRECTION, stated because the ruling was written on the other assumption: the
# engine state is NOT mirrored into agent-exports. SUBDIRS is ["wiki", "field-reports"] and
# there is no engine_state.json anywhere under the export tree -- verified 2026-09-19. So we
# read it from the container, which this script already talks to.
ENGINE_STATE = "/a0/usr/workdir/workspace/office/engine_state.json"
# A heartbeat older than this means the flag is lying. On 2026-08-03 a cycle carried
# is_running=true for FIVE DAYS; `cycle_active` alone would have deferred the refresh
# forever. The flag is a claim; the heartbeat is the evidence.
HEARTBEAT_STALE_S = int(os.environ.get("SYNC_HEARTBEAT_STALE_S", "300"))


# A deferral that nobody can see is the failure this whole gate is supposed to prevent, one
# level up: the `embedder_healthy` probe I nearly shipped would have deferred FOREVER and
# reported nothing. So every consecutive deferral is counted in a sidecar and printed. The
# signature is still not advanced -- that part is load-bearing and untouched.
DEFER_FILE = os.path.join(EXPORT_ROOT, ".sync_deferrals.json")


def note_deferral(reason):
    """-> (count, since). Never raises: a bookkeeping failure must not fail the run."""
    try:
        d = json.load(open(DEFER_FILE)) if os.path.exists(DEFER_FILE) else {}
    except Exception:
        d = {}
    n = int(d.get("count", 0)) + 1
    since = d.get("since") or datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    try:
        json.dump({"count": n, "since": since, "last_reason": reason}, open(DEFER_FILE, "w"))
    except Exception:
        pass
    return n, since


def clear_deferrals():
    try:
        if os.path.exists(DEFER_FILE):
            os.remove(DEFER_FILE)
    except Exception:
        pass


def refresh_progress():
    """-> a short human phrase, or "". Best-effort: a bookkeeping read must never fail a run.

    Opus's point, and it is the right one: "deferred because a refresh is 73% through" is
    actionable where "deferral #4" is only a number. Needs the server-side progress counter
    (candidate `opus-memory-server.py.candidate-throttle-20260919`); with an older server the
    key is absent and this stays silent rather than guessing.
    """
    try:
        import asyncio
        from fastmcp import Client

        async def _go():
            async with Client(MCP_URL) as c:
                return await c.call_tool("index_status", {})

        d = getattr(asyncio.run(_go()), "data", None) or {}
        if not d.get("reindex_running"):
            return ""
        pr = d.get("reindex_progress") or {}
        if pr.get("pct") is not None:
            return "a corpus refresh is %.0f%% through (%s/%s, %s)" % (
                pr["pct"], pr.get("done"), pr.get("total"), pr.get("phase"))
        return "a corpus refresh is running (started %s, no progress counter on this server)" % (
            d.get("reindex_started"))
    except Exception:
        return ""


# The daemon's own completion signal. Written by `cycle_close.py` at the real close; removed
# by `idle_watch.py` immediately before it fires the next cycle.
CYCLE_SIGNAL = "/a0/usr/workdir/workspace/office/cycle_result.json"


def _cycle_closed(container, state):
    """-> (closed, why). Is the daemon sitting in its post-close idle wait?

    THE CONTENT CHECK IS LOAD-BEARING, NOT BELT-AND-BRACES, and this is the whole reason the
    function exists rather than an `os.path.exists`. The daemon consumes the signal with:

        if _read_cycle_signal():      # truthiness
            os.remove(_SIGNAL_PATH)

    and `_read_cycle_signal()` swallows every exception and returns {} — so a MALFORMED or
    empty cycle_result.json is never consumed and **lingers forever**. Treating mere presence
    as "closed" would then pass on every run, permanently, while she generates: fail-open into
    a live cycle, which is strictly worse than the over-blocking it replaces.

    Currency is therefore required, and a stale file fails it: a leftover from cycle N-1 has
    `completed_ts` BELOW the new `last_cycle_start`, and a `context_id` that no longer matches.
    An unparseable one yields neither field and reads as absent, falling through to the
    heartbeat branch. Safe both ways — but only because this check is mandatory.
    """
    r = _run(["docker", "exec", container, "cat", CYCLE_SIGNAL])
    if r.returncode != 0:
        return False, ""                      # absent is the normal in-flight case, not an error
    try:
        sig = json.loads(r.stdout)
    except Exception:
        # Corrupt: the daemon will never consume it, so it will sit there forever. Read it as
        # absent rather than as closed, and say so — a file that cannot be parsed is not
        # evidence of anything.
        return False, ""
    if not isinstance(sig, dict) or not sig:
        return False, ""

    started = state.get("last_cycle_start")
    done = sig.get("completed_ts")
    fresh = isinstance(done, (int, float)) and isinstance(started, (int, float)) \
        and done >= started
    # `context_id` comes from os.environ["A0_CHAT_ID"] and may be "". Two empty strings must
    # not count as a match, or an env-less close would satisfy every future comparison.
    ctx = sig.get("context_id") or ""
    same_ctx = bool(ctx) and ctx == (state.get("cycle_context_id") or "")
    if not (fresh or same_ctx):
        return False, ""
    return True, ("cycle %s closed at %s; the daemon is in its post-close idle wait "
                  "(matched on %s)" % (
                      state.get("cycle_count"),
                      datetime.datetime.fromtimestamp(
                          done, datetime.timezone.utc).strftime("%H:%M:%SZ")
                      if isinstance(done, (int, float)) else "?",
                      "completed_ts" if fresh else "context_id"))


# The daemon's OWN answer to "does this cycle still hold the slot": A0's native is_running for the
# tracked context, asked through the same plugin endpoint idle_watch uses (`_cycle_running`), with
# the same token. Run inside the container with A0's interpreter, from /a0, because that is where
# `create_auth_token` resolves its settings. Read-only: `status` changes nothing.
_STATUS_PY = (
    "import json, http.client, sys\n"
    "sys.path.insert(0, '/a0')\n"
    "from helpers.settings import create_auth_token\n"
    "c = http.client.HTTPConnection('localhost', 80, timeout=10)\n"
    "c.request('POST', '/api/plugins/_exocortex/idle_cycle',\n"
    "          body=json.dumps({'action': 'status', 'context_id': sys.argv[1]}),\n"
    "          headers={'X-API-KEY': create_auth_token(), 'Content-Type': 'application/json'})\n"
    "r = c.getresponse()\n"
    "print(json.dumps({'http': r.status, 'body': r.read().decode('utf-8', 'replace')}))\n"
)


def _context_running(container, ctx, timeout=120):
    """-> (running, why). running is True / False / None, and **None is not False**.

    The timeout is generous on purpose: importing A0's `helpers.settings` (for
    `create_auth_token`, the daemon's own auth path) took 18-29 s inside the container when
    measured on 2026-09-24, so a 30 s budget timed out on the first live run. The call is made
    only when a heartbeat is already stale, at most once per container per hourly run.

    False only on A0's own word: the context is not found, or A0 reports running=false. That is
    the exact criterion idle_watch fires a new cycle on (`_cycle_running`), so trusting it here
    grants the refresh nothing the daemon would not grant a whole new cycle. Every failure to
    get that word (no id, docker error, timeout, non-200, unparseable, no `running` field) is
    None: undetermined, which the caller spends as "defer", never as "idle".
    """
    if not ctx:
        return None, "no tracked context id to ask A0 about"
    try:
        r = _run(["docker", "exec", "-w", "/a0", container, "/opt/venv-a0/bin/python3", "-c",
                  _STATUS_PY, ctx], timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, "A0 status call timed out after %ds" % timeout
    if r.returncode != 0:
        return None, "A0 status call failed: %s" % (r.stderr or "").strip()[-100:]
    try:
        out = json.loads((r.stdout or "").strip().splitlines()[-1])
        if out.get("http") != 200:
            return None, "A0 status returned HTTP %s" % out.get("http")
        data = json.loads(out["body"])
    except Exception as e:
        return None, "A0 status unreadable (%s)" % type(e).__name__
    if not data.get("found", False):
        return False, "A0 has no context %s" % ctx
    if "running" not in data:
        return None, "A0 status for %s carries no running flag" % ctx
    return bool(data["running"]), "A0 is_running=%s, last message %s" % (
        bool(data["running"]), data.get("last_message", "?"))


def engine_busy(container, timeout=15):
    """-> (busy, why). busy is True / False / None, and **None is not False**.

    None means "could not determine", which must never be spent as "idle" -- that is the
    failure this codebase makes most often, a check reporting ignorance as success.
    """
    st = _run(["docker", "inspect", "-f", "{{.State.Running}}", container])
    if st.returncode != 0:
        return None, "docker inspect failed: %s" % (st.stderr or "").strip()[:80]
    if st.stdout.strip() != "true":
        return False, "container not running — it has no engine to be mid-cycle"

    r = _run(["docker", "exec", container, "cat", ENGINE_STATE])
    if r.returncode != 0:
        return None, "could not read %s: %s" % (ENGINE_STATE, (r.stderr or "").strip()[:60])
    try:
        d = json.loads(r.stdout)
    except Exception as e:
        return None, "engine_state.json is not JSON: %s" % type(e).__name__

    # STATE 4 (Opus, 2026-09-19): the engine is off. Nothing will start a cycle, so pass.
    if not d.get("cycle_active"):
        return False, "cycle_active=false — the engine is off (last %s, count %s)" % (
            d.get("last_cycle_type"), d.get("cycle_count"))

    # STATE 1: the daemon's OWN completion signal. `cycle_close.py` writes cycle_result.json
    # at the real close; `idle_watch.py` removes it just before firing the next cycle. So its
    # presence-and-currency IS the daemon's "closed, idle-waiting" state — the 1800s window
    # after each close during which `cycle_active` stays true with a FROZEN heartbeat and she
    # is NOT generating. Reading that as busy is what made the first version of this gate
    # block in the best window available (measured 2026-09-19, Fable).
    sig_ok, sig_why = _cycle_closed(container, d)
    if sig_ok:
        return False, sig_why

    hb = d.get("cycle_heartbeat")
    if not isinstance(hb, (int, float)):
        return None, "cycle_active=true but no usable cycle_heartbeat"
    age = time.time() - hb
    if age > HEARTBEAT_STALE_S:
        # UNKNOWN, deliberately -- NOT idle. A stale heartbeat under an active flag has two
        # causes that look identical from here: a dead cycle (2026-08-03: is_running=true for
        # five days), or a LIVE cycle blocked on something slow. Tonight it was the second --
        # her turn was stuck on the dead embedder and the heartbeat sat 638s old while she was
        # genuinely mid-work. Calling that idle starts a refresh on top of the thing already
        # blocking her. Calling it busy is safe but must never be SILENT, hence the deferral
        # counter: the failure this replaces is a permanent deferral nobody could see.
        #
        # STATE 2b (Kestrel, 2026-09-24, Jake's word "go ahead and fix the sync gate"): the flag
        # and the heartbeat cannot tell dead from blocked, but A0 can. Ask it, the same way the
        # daemon decides whether the slot is free (`_cycle_running`). What this closes: on
        # 2026-09-24 cycle 757 fired at 13:09:51Z into a jammed LM Studio, made no tool call (so
        # the heartbeat never moved) and ended without a response. The engine was paused before
        # the daemon's next poll could reap its slot, so `cycle_active` stayed true with a frozen
        # heartbeat. Asked at ~20:30Z, A0 reported the context found and running=false (last
        # message 13:09:52Z); this gate had deferred 7 runs in a row and would have kept
        # deferring until the pause ended. Note that
        # `cycle_completed_ts >= last_cycle_start` does NOT prove a close here: the daemon stamps
        # the PREVIOUS cycle's close after capturing the new cycle's start time, so on a normal
        # fire the pair reads that way by a fraction of a second.
        ctx = d.get("cycle_context_id") or ""
        alive, awhy = _context_running(container, ctx)
        if alive is False:
            return False, ("cycle %s's context %s is not running (%s); its heartbeat is %.0fs "
                           "stale — a dead cycle holding the slot, not a live one"
                           % (d.get("cycle_count"), ctx, awhy, age))
        if alive is True:
            return True, ("cycle %s's context %s IS running (%s) with a heartbeat %.0fs stale — "
                          "blocked, not idle" % (d.get("cycle_count"), ctx, awhy, age))
        return None, ("cycle_active=true but heartbeat is %.0fs stale (> %ds) — cannot tell a "
                      "dead cycle from a blocked one (%s)" % (age, HEARTBEAT_STALE_S, awhy))
    return True, "cycle %s (%s) active, heartbeat %.0fs old" % (
        d.get("cycle_count"), d.get("last_cycle_type"), age)


def any_engine_busy(containers):
    """-> (block, why). Blocks on busy AND on unknown; unknown is never spent as idle."""
    unknown = []
    for name, c in containers.items():
        busy, why = engine_busy(c)
        if busy is True:
            return True, "[%s] %s" % (name, why)
        if busy is None:
            unknown.append("[%s] %s" % (name, why))
    if unknown:
        return True, "UNDETERMINED — " + "; ".join(unknown)
    return False, "all engines idle"


def trigger_refresh():
    """Call the server's refresh_now MCP tool — incremental; unchanged chunks keep
    their vectors. Uses the server's in-process lock + background thread."""
    try:
        import asyncio
        from fastmcp import Client

        async def _go():
            async with Client(MCP_URL) as client:
                return await client.call_tool("refresh_now", {})

        res = asyncio.run(_go())
        data = getattr(res, "data", res)
        # `refresh_now` REFUSES while another reindex holds the lock and reports that
        # refusal as a NORMAL successful call (opus-memory-server.py:1723-1725,
        # `{"status": "already_running", ...}`). Measured against the live server
        # 2026-09-19 08:46Z, mid-reindex: the old code printed "refresh triggered" and
        # returned True. Treat a refusal as not-accepted, or this run's content is
        # recorded as indexed when nothing indexed it.
        if isinstance(data, dict) and data.get("status") == "already_running":
            print(f"  refresh NOT accepted: a reindex started {data.get('started')} still "
                  f"holds the lock. Files are synced; this run's content is NOT indexed.")
            return False
        print(f"  refresh triggered: {data}")
        return True
    except Exception as e:
        print(f"  refresh trigger FAILED ({e}). Files are synced but NOT searchable; "
              f"run refresh_now via MCP to index them.")
        return False


def main():
    ap = argparse.ArgumentParser(description="Sync agent workspaces to the shared corpus + reindex.")
    ap.add_argument("--no-reindex", action="store_true")
    ap.add_argument("--ignore-health", action="store_true",
                    help="refresh even when the embedder probe says it cannot serve")
    ap.add_argument("--force-reindex", action="store_true")
    ap.add_argument("--ignore-idle", action="store_true",
                    help="refresh even while the agent is mid-cycle (costs her recall)")
    ap.add_argument("--agent", choices=list(AGENTS))
    # Retained as a hidden alias so an existing habit keeps working and means the
    # analogous thing; the VRAM floor itself is gone.
    ap.add_argument("--ignore-vram", action="store_true", dest="ignore_health",
                    help=argparse.SUPPRESS)
    args = ap.parse_args()

    targets = {args.agent: AGENTS[args.agent]} if args.agent else AGENTS
    os.makedirs(EXPORT_ROOT, exist_ok=True)

    # 2026-09-13 (Jake): `docker inspect` fails the same way for "daemon not running" and "no such container",
    # so with Docker Desktop OFF (Jake turns it off to game) every agent read as "not found — skipped", the
    # signature came out unchanged, and the run exited 0 looking clean. Now: say so, touch nothing, exit 3.
    ok, detail = daemon_reachable()
    if not ok:
        print(f"DOCKER DAEMON NOT REACHABLE ({detail})")
        print("  sync DEFERRED: no files copied, no reindex, state not advanced; the next scheduled run retries.")
        sys.exit(EXIT_DEFERRED)

    total = 0
    for name, container in targets.items():
        if not container_exists(container):
            print(f"  [{name}] container {container} not found (daemon reachable) — skipped")
            continue
        n = sync_agent(name, container)
        total += n
        print(f"  [{name}] synced {n} files from {container}")

    sig = tree_signature(EXPORT_ROOT)
    try:
        prev = json.load(open(STATE_FILE)).get("signature") if os.path.exists(STATE_FILE) else None
    except Exception:
        prev = None
    changed = sig != prev

    wrote_state = True
    if args.no_reindex:
        print("  --no-reindex: files synced, reindex skipped")
    elif changed or args.force_reindex:
        if args.ignore_idle:
            blocked, bwhy = False, "skipped (--ignore-idle)"
        else:
            blocked, bwhy = any_engine_busy(targets)
        if blocked:
            print("  content changed BUT the agent is mid-cycle -> refresh DEFERRED")
            print("  engine: %s" % bwhy)
            n, since = note_deferral(bwhy)
            rp = refresh_progress()
            if rp:
                print("  also: %s" % rp)
            print("  files are synced and safe; the next hourly CHECK retries when she is idle.")
            if n > 1:
                print("  ** consecutive deferral #%d, first at %s — if this keeps climbing the"
                      " gate is stuck, not patient **" % (n, since))
            # Same reasoning as the health gate below: do NOT record the new signature, or
            # the deferred content looks unchanged next run and is never indexed.
            wrote_state = False
            ok = None
        else:
            ok, why = embedder_healthy()
        if ok is None:
            pass
        elif not ok and not args.ignore_health:
            print(f"  content changed BUT the embedder cannot serve -> refresh DEFERRED")
            print(f"  probe: {why}")
            print("  files are synced and safe; the next run refreshes once it recovers.")
            # Do NOT record the new signature — otherwise the deferred content would
            # look 'unchanged' next run and never get indexed at all.
            wrote_state = False
        else:
            state = "changed" if changed else "unchanged (forced)"
            print(f"  content {state} ({why}) -> refreshing")
            # Guard the OTHER arm of the same failure. The health-probe branch ten lines
            # up already refuses to advance the signature when it defers, for the reason
            # stated there: deferred content that looks 'unchanged' next run is never
            # indexed at all. A refresh that never started -- or was REFUSED because a
            # reindex already held the lock -- has the same consequence and was unguarded.
            #
            # Precisely: the content is not lost. `reindex(reuse=True)` re-walks the whole
            # corpus, so the NEXT successful refresh picks it up. What it is, is invisible
            # for an unbounded window -- until something else changes the signature and a
            # refresh succeeds -- while the run reports success, so nobody looks.
            #
            # BOUND, so the next reader does not over-trust this line: it catches "the
            # refresh never STARTED" (MCP unreachable, tool errored). It cannot catch
            # "the refresh started and then DIED" -- refresh_now runs on a background
            # thread and returns immediately. Measured 2026-09-19: this state file was
            # written at 08:00:15Z, ONE SECOND after a refresh that was still running
            # forty minutes later. For that case the server already exposes
            # `reindex_last_result` through index_status; nothing reads it yet.
            if trigger_refresh():
                clear_deferrals()
            else:
                wrote_state = False
    else:
        print("  content unchanged since last sync -> reindex skipped (no GPU churn)")

    if not wrote_state:
        print(f"done. {total} files across {len(targets)} agent(s). (state not advanced)")
        return

    try:
        json.dump({"signature": sig, "files": total}, open(STATE_FILE, "w"))
    except Exception as e:
        print(f"  (couldn't write state file: {e})")

    print(f"done. {total} files across {len(targets)} agent(s).")


if __name__ == "__main__":
    main()
