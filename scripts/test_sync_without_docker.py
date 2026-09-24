"""Control for the sync's no-Docker path (sync_agent_exports.main) and its missing-container gate.

Jake, 2026-09-24: "if it doesn't see the docker container it just goes 'okay, I'll just check on
Opus', Kestrel's, and Fable's folders' ... you guys could be running and working even if Aporia and
docker desktop are not." Before this, a down Docker daemon ended the run before the refresh, so no
folder was indexed for as long as Docker stayed paused.

The real main() runs with every outbound edge stubbed: the daemon probe, container_exists,
sync_agent, the engine gate, the embedder probe, the refresh trigger. Its state files point into a
temp directory, so no container, server or real state file is touched.

    python scripts/test_sync_without_docker.py                  # the working tree (must PASS)
    python scripts/test_sync_without_docker.py --against-head   # the committed code must show the old
                                                                # behaviour (exit 3, no refresh)
    SYNC_MODULE=<path> python scripts/test_sync_without_docker.py   # any other copy of the script
"""
import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                      # sync_agent_exports imports docker_probe from here
passed = failed = 0


def check(label, cond, detail=""):
    global passed, failed
    print(("  PASS  " if cond else "  FAIL  ") + label + (("  [%s]" % (detail,)) if (detail and not cond) else ""))
    passed += bool(cond)
    failed += (not cond)


def load(path):
    spec = importlib.util.spec_from_file_location("sync_%d" % abs(hash(path)), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run_main(m, argv=(), docker=(True, "stub daemon up"), exists=True, engine=(False, "stub: all engines idle"),
             embedder=(True, "stub embed path answered"), refresh=True):
    tmp = tempfile.mkdtemp(prefix="sync_nodocker_")
    m.EXPORT_ROOT = tmp
    m.STATE_FILE = os.path.join(tmp, ".sync_state.json")
    m.DEFER_FILE = os.path.join(tmp, ".sync_deferrals.json")
    calls = {"sync": [], "engine": 0, "embedder": 0, "refresh": 0}

    def fake_sync(name, container):
        calls["sync"].append(name)
        return 3

    def fake_engine(targets):
        calls["engine"] += 1
        return engine

    def fake_embedder(*a, **k):
        calls["embedder"] += 1
        return embedder

    def fake_refresh():
        calls["refresh"] += 1
        return refresh

    m.daemon_reachable = lambda *a, **k: docker
    m.container_exists = lambda c: exists
    m.sync_agent = fake_sync
    m.any_engine_busy = fake_engine
    m.embedder_healthy = fake_embedder
    m.trigger_refresh = fake_refresh
    m.refresh_progress = lambda: None
    sys.argv = ["sync_agent_exports.py", *argv]
    buf, code = io.StringIO(), 0
    with contextlib.redirect_stdout(buf):
        try:
            m.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    return code, calls, buf.getvalue()


class R:
    def __init__(self, rc=0, out="", err=""):
        self.returncode, self.stdout, self.stderr = rc, out, err


DOWN = (False, "stub: error during connect, the Docker daemon is not running")


def main():
    if "--against-head" in sys.argv:
        src = subprocess.run(["git", "show", "HEAD:scripts/sync_agent_exports.py"], capture_output=True, text=True,
                             cwd=os.path.dirname(HERE)).stdout
        tmp = os.path.join(tempfile.mkdtemp(), "sync_head.py")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(src)
        m = load(tmp)
        code, calls, out = run_main(m, docker=DOWN)
        print("HEAD with Docker down -> exit %s, refresh calls %d" % (code, calls["refresh"]))
        check("the committed code still ends the run at the daemon check (exit 3, no refresh)",
              code == 3 and calls["refresh"] == 0, (code, calls))
    else:
        m = load(os.environ.get("SYNC_MODULE", os.path.join(HERE, "sync_agent_exports.py")))

        print("A. Docker down, embedder healthy: the index refreshes, the containers are skipped")
        code, calls, out = run_main(m, docker=DOWN)
        check("no container is copied", calls["sync"] == [], calls)
        check("the engine gate is not consulted (a down daemon has no agent mid-cycle)", calls["engine"] == 0, calls)
        check("the refresh is triggered once", calls["refresh"] == 1, calls)
        check("exit 4 (EXIT_PARTIAL), never a clean 0", code == 4, code)
        check("the output says the daemon is down and the containers were skipped",
              "DOCKER DAEMON NOT REACHABLE" in out and "container sync SKIPPED" in out
              and "containers were NOT synced" in out, out)

        print("B. Docker down, embedder cannot serve: nothing is done")
        code, calls, out = run_main(m, docker=DOWN, embedder=(False, "stub: embedder down"))
        check("no refresh, exit 3 (EXIT_DEFERRED)", calls["refresh"] == 0 and code == 3, (code, calls))

        print("C. Docker down, the refresh does not start: nothing is done")
        code, calls, out = run_main(m, docker=DOWN, refresh=False)
        check("exit 3, state not advanced", code == 3 and "(state not advanced)" in out, (code, out))

        print("D. Docker down with --no-reindex: nothing is done")
        code, calls, out = run_main(m, argv=["--no-reindex"], docker=DOWN)
        check("exit 3 and no refresh", code == 3 and calls["refresh"] == 0, (code, calls))

        print("E. Docker up: the normal run is unchanged")
        code, calls, out = run_main(m)
        check("both agents synced, gate consulted, refresh triggered, exit 0",
              calls["sync"] == ["v2", "v17"] and calls["engine"] == 1 and calls["refresh"] == 1 and code == 0,
              (code, calls))
        code, calls, out = run_main(m, engine=(True, "stub: cycle 9 active"))
        check("Docker up and an agent mid-cycle: deferred as before (exit 0, no refresh)",
              calls["refresh"] == 0 and code == 0 and "mid-cycle" in out, (code, calls))

        print("F. The gate on a container that does not exist")
        m2 = load(os.environ.get("SYNC_MODULE", os.path.join(HERE, "sync_agent_exports.py")))
        m2._run = lambda args, timeout=None: R(1, "", "Error: No such object: VekV2")
        busy, why = m2.engine_busy("VekV2")
        check("'No such object' from docker inspect -> not busy (False)", busy is False and "no container named" in why,
              (busy, why))
        m2._run = lambda args, timeout=None: R(1, "", "error during connect: pipe not found")
        busy, why = m2.engine_busy("VekV2")
        check("any other inspect failure stays undetermined (None)", busy is None, (busy, why))

    print("\nRESULT: %d passed, %d failed" % (passed, failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
