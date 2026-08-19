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
  --ignore-vram    reindex even when free VRAM is under the safety floor

SAFETY (2026-08-19, Tier 1.2):
  * The file copy is STAGE-VERIFY-SWAP, not delete-then-copy. A failed `docker cp`
    used to leave the export tree already deleted — and agent-exports/ has never
    been tracked in git. On a 6-hourly timer that was four chances a day to destroy
    an agent's accumulated wiki permanently.
  * The reindex is VRAM-GATED. A full re-embed is a ~12 minute CUDA job over ~43k
    chunks; the local LLM holds ~22 GB of the 24 GB card while loaded. Unattended,
    that would fire straight into Jake's inference server at an arbitrary hour.
    Below MIN_REINDEX_FREE_VRAM_MIB the reindex DEFERS and the state signature is
    deliberately NOT advanced, so the pending content is retried next run instead
    of being marked 'unchanged' and never indexed.

COST NOTE: reindex() is a FULL rebuild (re-embeds ~43k chunks on the shared 3090),
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


# A full reindex re-embeds ~43k chunks on the SHARED 3090 and takes ~12 minutes.
# The local LLM (qwen3.8-27b) occupies ~22 GB of the 24 GB card while loaded, and
# this script is meant to run unattended on a timer — so without a guard it would
# eventually fire a 12-minute CUDA job straight into Jake's inference server at some
# arbitrary hour. Measured 2026-08-19: 2187 MiB free with the model up.
MIN_REINDEX_FREE_VRAM_MIB = 6000


def _free_vram_mib():
    """Free VRAM in MiB, or None if it cannot be determined (then don't block)."""
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0:
            return None
        return min(int(v.strip()) for v in r.stdout.split() if v.strip().isdigit())
    except Exception:
        return None


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
    ap.add_argument("--ignore-vram", action="store_true",
                    help="reindex even when free VRAM is below the safety floor "
                         "(the local LLM is probably loaded — use deliberately)")
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

    wrote_state = True
    if args.no_reindex:
        print("  --no-reindex: files synced, reindex skipped")
    elif changed or args.force_reindex:
        free = _free_vram_mib()
        if free is not None and free < MIN_REINDEX_FREE_VRAM_MIB and not args.ignore_vram:
            print(f"  content changed BUT only {free} MiB VRAM free "
                  f"(need {MIN_REINDEX_FREE_VRAM_MIB}) -> reindex DEFERRED")
            print("  the local LLM is loaded; a full re-embed would fight it for the card.")
            print("  files are synced and safe; the next run reindexes once the card frees up.")
            # Do NOT record the new signature — otherwise the deferred content would
            # look 'unchanged' next run and never get indexed at all.
            wrote_state = False
        else:
            if free is not None:
                print(f"  content {'changed' if changed else 'unchanged (forced)'} "
                      f"({free} MiB VRAM free) -> reindexing")
            else:
                print(f"  content {'changed' if changed else 'unchanged (forced)'} -> reindexing")
            trigger_reindex()
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
