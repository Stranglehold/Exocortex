#!/usr/bin/env python3
"""docker_probe.py — tell "the Docker daemon is not running" apart from "this container does not exist".

WHY THIS EXISTS (2026-09-13, Jake's ask). `docker inspect <container>` fails identically in both cases, so the
scheduled scripts (backup_agents.py, sync_agent_exports.py) printed "container not found — skipped" and exited 0
while Docker Desktop was OFF, which Jake does deliberately to game. Four times a day a run that did nothing looked
like a clean run. Same fail-open shape Kestrel found in verify_holdout_seal.py the same night: a check that passes
for the wrong reason reads exactly like one that is clean.

    from docker_probe import daemon_reachable
    ok, detail = daemon_reachable()      # (True, "<server version>") or (False, "<one-line reason>")

Callers that need the daemon should, when ok is False, say so in their own words, leave their state untouched, and
exit 3 (DEFERRED: the next scheduled run retries), so Task Scheduler's Last Run Result and the log both carry the
truth. Read-only: runs `docker version` once, nothing else.

Self-test (controls, no daemon needed):  python docker_probe.py --self-test
"""
import os
import subprocess
import sys

EXIT_DEFERRED = 3   # the scripts' shared meaning: could not do the job, nothing changed, retry next run


def daemon_reachable(timeout=20):
    """(True, server_version) when the daemon answers; (False, reason) otherwise. Never raises."""
    import shutil
    exe = shutil.which("docker")          # honours PATHEXT, so the self-test's .bat stubs resolve like docker.exe
    if not exe:
        return False, "docker CLI not found on PATH"
    try:
        r = subprocess.run([exe, "version", "--format", "{{.Server.Version}}"],
                           capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return False, "docker CLI not found on PATH"
    except subprocess.TimeoutExpired:
        return False, f"docker version gave no answer in {timeout}s"
    except Exception as e:  # any other failure is still a reason, never a silent True
        return False, f"{type(e).__name__}: {e}"
    if r.returncode == 0 and r.stdout.strip():
        return True, r.stdout.strip()
    text = (r.stderr or r.stdout or "").strip().splitlines()
    return False, (text[-1] if text else f"docker version exit {r.returncode}")


def _self_test():
    """Three controls: a stub docker that answers -> True; a stub that fails -> False with its message; no docker -> False."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="docker_probe_")
    good = os.path.join(tmp, "good"); bad = os.path.join(tmp, "bad"); none = os.path.join(tmp, "none")
    for d in (good, bad, none):
        os.makedirs(d)
    open(os.path.join(good, "docker.bat"), "w").write("@echo 99.0.0-stub\r\n")
    open(os.path.join(bad, "docker.bat"), "w").write("@echo error during connect: stub daemon down 1>&2\r\n@exit /b 1\r\n")
    fails = 0
    for label, path, want_ok, want_in in (("answering stub", good, True, "99.0.0-stub"),
                                          ("failing stub", bad, False, "stub daemon down"),
                                          ("no docker on PATH", none, False, "not found")):
        saved = os.environ.get("PATH", "")
        os.environ["PATH"] = path + os.pathsep + os.environ.get("SystemRoot", r"C:\Windows") + r"\System32"
        try:
            ok, detail = daemon_reachable(timeout=10)
        finally:
            os.environ["PATH"] = saved
        good_result = (ok == want_ok) and (want_in in detail)
        fails += 0 if good_result else 1
        print(f"  {'ok  ' if good_result else 'FAIL'} {label:20} -> ok={ok} detail={detail!r}")
    ok, detail = daemon_reachable()
    print(f"  live: daemon reachable={ok} ({detail})")
    print("SELF-TEST " + ("PASS" if fails == 0 else f"FAIL ({fails})"))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    ok, detail = daemon_reachable()
    print(f"daemon reachable: {ok} ({detail})")
    sys.exit(0 if ok else EXIT_DEFERRED)
