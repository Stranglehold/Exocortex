"""Control for the sync refresh gate's A0 context check (sync_agent_exports.engine_busy, STATE 2b).

Every outbound call the gate makes (`docker inspect`, `docker exec cat`, the A0 status call) goes
through `_run`, which is stubbed here, so each branch is driven with the exact shapes production
returns. The first scenario is the live one of 2026-09-24: cycle_active=true, heartbeat ~6 h stale,
a tracked context A0 reports as not running, no cycle_result.json, and the fire-order artifact
(cycle_completed_ts a fraction of a second after last_cycle_start).

    python scripts/test_sync_gate_context.py              # the working tree (must PASS)
    python scripts/test_sync_gate_context.py --against-head
        # runs scenario 1 against the committed version, which must still say UNDETERMINED:
        # proof the test can tell the two apart
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
passed = failed = 0


def check(label, cond, detail=""):
    global passed, failed
    print(("  PASS  " if cond else "  FAIL  ") + label + (("  [%s]" % (detail,)) if (detail and not cond) else ""))
    passed += bool(cond)
    failed += (not cond)


def load(path):
    spec = importlib.util.spec_from_file_location("sync_mod_%d" % id(path), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class R:
    def __init__(self, rc=0, out="", err=""):
        self.returncode, self.stdout, self.stderr = rc, out, err


def stub(m, state, running="true", signal=None, a0=("ok", {"found": True, "running": False})):
    """Replace m._run with a fake docker. Returns the list of A0 status calls made."""
    a0_calls = []

    def fake(args, timeout=None):
        if args[:2] == ["docker", "inspect"]:
            return R(0, running + "\n")
        if args[:2] == ["docker", "exec"] and args[-2:] == ["cat", m.ENGINE_STATE]:
            return R(0, json.dumps(state))
        if args[:2] == ["docker", "exec"] and args[-2:] == ["cat", m.CYCLE_SIGNAL]:
            return R(1, "", "No such file") if signal is None else R(0, json.dumps(signal))
        if args[:2] == ["docker", "exec"] and "-c" in args:
            a0_calls.append(args[-1])
            kind, payload = a0
            if kind == "timeout":
                raise subprocess.TimeoutExpired(args, timeout)
            if kind == "fail":
                return R(1, "", "Error response from daemon: boom")
            if kind == "http":
                return R(0, json.dumps({"http": payload, "body": "denied"}))
            return R(0, json.dumps({"http": 200, "body": json.dumps(payload)}))
        raise AssertionError("unexpected call: %r" % (args,))

    m._run = fake
    return a0_calls


def live_state(**kw):
    now = time.time()
    st = {"cycle_active": True, "cycle_count": 757, "last_cycle_type": "BUILD", "cycle_context_id": "9cEDvxqe",
          "last_cycle_start": now - 26000.0, "cycle_heartbeat": now - 26000.0, "cycle_completed_ts": now - 25999.84}
    st.update(kw)
    return st


def main():
    if "--against-head" in sys.argv:
        src = subprocess.run(["git", "show", "HEAD:scripts/sync_agent_exports.py"], capture_output=True,
                             text=True, cwd=os.path.dirname(HERE)).stdout
        tmp = os.path.join(tempfile.mkdtemp(), "sync_head.py")
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(src)
        m = load(tmp)
        stub(m, live_state())
        busy, why = m.engine_busy("agent-zero-v2")
        print("HEAD, live scenario -> busy=%r: %s" % (busy, why))
        check("the committed gate still reads the live scenario as UNDETERMINED (None)", busy is None, (busy, why))
    else:
        m = load(os.path.join(HERE, "sync_agent_exports.py"))
        print("1. the live scenario (cycle 757, 2026-09-24)")
        calls = stub(m, live_state())
        busy, why = m.engine_busy("agent-zero-v2")
        check("dead context holding the slot -> not busy (False)", busy is False, (busy, why))
        check("...and the reason names A0's word", "not running" in why and "9cEDvxqe" in why, why)
        check("...after exactly one A0 status call, for the tracked id", calls == ["9cEDvxqe"], calls)

        print("2. A0's other answers")
        stub(m, live_state(), a0=("ok", {"found": True, "running": True}))
        busy, why = m.engine_busy("agent-zero-v2")
        check("context alive with a stale heartbeat -> busy (True), 'blocked'", busy is True and "blocked" in why, (busy, why))
        stub(m, live_state(), a0=("ok", {"found": False}))
        busy, why = m.engine_busy("agent-zero-v2")
        check("context unknown to A0 -> not busy (False)", busy is False and "no context" in why, (busy, why))

        print("3. every failure to get A0's word stays UNDETERMINED (None), never idle")
        for label, a0 in (("docker exec fails", ("fail", None)), ("status call times out", ("timeout", None)),
                          ("HTTP 403", ("http", 403)), ("no running field", ("ok", {"found": True}))):
            stub(m, live_state(), a0=a0)
            busy, why = m.engine_busy("agent-zero-v2")
            check("%s -> None" % label, busy is None and "cannot tell" in why, (busy, why))
        calls = stub(m, live_state(cycle_context_id=""))
        busy, why = m.engine_busy("agent-zero-v2")
        check("no tracked context id -> None, and A0 is not asked", busy is None and calls == [], (busy, why, calls))

        print("4. the branches before it are unchanged, and none of them asks A0")
        calls = stub(m, live_state(cycle_heartbeat=time.time() - 10))
        busy, why = m.engine_busy("agent-zero-v2")
        check("fresh heartbeat -> busy (True), no A0 call", busy is True and calls == [], (busy, why, calls))
        calls = stub(m, live_state(cycle_active=False))
        busy, why = m.engine_busy("agent-zero-v2")
        check("cycle_active=false -> not busy, no A0 call", busy is False and calls == [], (busy, why, calls))
        st = live_state()
        calls = stub(m, st, signal={"completed_ts": st["last_cycle_start"] + 5, "context_id": "9cEDvxqe"})
        busy, why = m.engine_busy("agent-zero-v2")
        check("current close signal -> not busy (closed), no A0 call", busy is False and "closed" in why and calls == [], (busy, why, calls))
        calls = stub(m, live_state(), running="false")
        busy, why = m.engine_busy("agent-zero-v2")
        check("container stopped -> not busy, no A0 call", busy is False and calls == [], (busy, why, calls))

    print("\nRESULT: %d passed, %d failed" % (passed, failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
