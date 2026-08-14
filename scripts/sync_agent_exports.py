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

COST NOTE: reindex() is a FULL rebuild (re-embeds ~24k chunks on the shared 3090),
so this script reindexes ONLY when the synced content actually changed. Schedule it
at a modest cadence (Windows Task Scheduler), e.g. every 6h:
  schtasks /Create /TN "ExocortexAgentSync" /SC HOURLY /MO 6 /TR ^
    "\"D:\\Vibecode\\docker-mcp-server\\.venv-opus-memory\\Scripts\\python.exe\" \"D:\\Vibecode\\Agent-Zero\\Exocortex\\scripts\\sync_agent_exports.py\""
Incremental (append-only) indexing on the server would remove the full-rebuild cost
— flagged to Opus as the long-term memory-server improvement.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

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
MCP_URL = "http://localhost:5055/mcp"
STATE_FILE = os.path.join(EXPORT_ROOT, ".sync_state.json")

# docker cp mangles Unix container paths under Git Bash / MSYS; disable that.
_ENV = dict(os.environ, MSYS_NO_PATHCONV="1")


def _run(args):
    return subprocess.run(args, capture_output=True, text=True, env=_ENV)


def container_exists(container):
    return _run(["docker", "inspect", "-f", "{{.State.Status}}", container]).returncode == 0


def sync_agent(name, container):
    """Mirror the container's wiki + field-reports into agent-exports/<name>/.
    docker cp can't delete, so each subdir is removed then re-copied for a true mirror."""
    dest = os.path.join(EXPORT_ROOT, name)
    files = 0
    for sub in SUBDIRS:
        src = f"{container}:{CONTAINER_WORKSPACE}/{sub}"
        sub_dest = os.path.join(dest, sub)
        # probe: does the subdir exist in the container?
        if _run(["docker", "exec", container, "test", "-d", f"{CONTAINER_WORKSPACE}/{sub}"]).returncode != 0:
            # exec fails on stopped containers; fall back to attempting the copy anyway
            if _run(["docker", "inspect", "-f", "{{.State.Running}}", container]).stdout.strip() == "true":
                continue
        if os.path.isdir(sub_dest):
            shutil.rmtree(sub_dest, ignore_errors=True)
        os.makedirs(dest, exist_ok=True)
        r = _run(["docker", "cp", src, sub_dest])
        if r.returncode == 0 and os.path.isdir(sub_dest):
            files += sum(len(fs) for _, _, fs in os.walk(sub_dest))
        elif r.returncode != 0:
            print(f"  [{name}] {sub}: skipped ({r.stderr.strip()[:80]})")
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


def trigger_reindex():
    """Call the server's reindex_now MCP tool (uses its in-process lock + background thread)."""
    try:
        import asyncio
        from fastmcp import Client

        async def _go():
            async with Client(MCP_URL) as client:
                return await client.call_tool("reindex_now", {})

        res = asyncio.run(_go())
        print(f"  reindex triggered: {getattr(res, 'data', res)}")
        return True
    except Exception as e:
        print(f"  reindex trigger FAILED ({e}). Files are synced; reindex manually "
              f"(reindex_now via MCP) to make them searchable.")
        return False


def main():
    ap = argparse.ArgumentParser(description="Sync agent workspaces to the shared corpus + reindex.")
    ap.add_argument("--no-reindex", action="store_true")
    ap.add_argument("--force-reindex", action="store_true")
    ap.add_argument("--agent", choices=list(AGENTS))
    args = ap.parse_args()

    targets = {args.agent: AGENTS[args.agent]} if args.agent else AGENTS
    os.makedirs(EXPORT_ROOT, exist_ok=True)

    total = 0
    for name, container in targets.items():
        if not container_exists(container):
            print(f"  [{name}] container {container} not found — skipped")
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

    if args.no_reindex:
        print("  --no-reindex: files synced, reindex skipped")
    elif changed or args.force_reindex:
        print(f"  content {'changed' if changed else 'unchanged (forced)'} -> reindexing")
        trigger_reindex()
    else:
        print("  content unchanged since last sync -> reindex skipped (no GPU churn)")

    try:
        json.dump({"signature": sig, "files": total}, open(STATE_FILE, "w"))
    except Exception as e:
        print(f"  (couldn't write state file: {e})")

    print(f"done. {total} files across {len(targets)} agent(s).")


if __name__ == "__main__":
    main()
