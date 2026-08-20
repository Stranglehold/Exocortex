"""In-container integration test for A1 — drives BOTH extension halves for real.

What only this can prove, that the local unit tests cannot:
  1. `import failure_fingerprint` actually resolves from inside an extension.
     Both halves swallow exceptions, so a failed import leaves them silently
     inert while appearing installed.
  2. The op-signature handshake round-trips between the two hooks.
  3. The gate genuinely RAISES on the third strike.

Run inside the container with the A0 venv.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, "/a0")
sys.path.insert(0, "/a0/python")

OFFICE = "/a0/usr/workdir/workspace/office"
LEDGER = os.path.join(OFFICE, "failure_fingerprints.json")
BACKUP = LEDGER + ".pretest"

# Preserve any real ledger; this test writes to the live store path.
if os.path.exists(LEDGER):
    os.replace(LEDGER, BACKUP)

results = []


def ok(name, cond, detail=""):
    results.append(bool(cond))
    print(("  PASS " if cond else "  FAIL ") + name + (f"   {detail}" if detail else ""))


class StubLog:
    def __init__(self):
        self.entries = []

    def log(self, **kw):
        self.entries.append(kw)


class StubCtx:
    def __init__(self):
        self.log = StubLog()


class StubAgent:
    """Faithful: A0's Agent.get_data/set_data are plain dict ops on self.data
    (verified in /a0/agent.py L172-178)."""

    def __init__(self):
        self.data = {}
        self.context = StubCtx()

    def get_data(self, k, recursive=True):
        return self.data.get(k, None)

    def set_data(self, k, v, recursive=True):
        self.data[k] = v

    def hist_add_warning(self, *a, **k):
        pass


def load_ext(path, cls_name, agent):
    import importlib.util
    spec = importlib.util.spec_from_file_location("ext_" + cls_name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, cls_name)(agent=agent)


GATE = "/a0/usr/plugins/_exocortex/extensions/python/tool_execute_before/_20_meta_reasoning_gate.py"
REC = "/a0/usr/plugins/_exocortex/extensions/python/tool_execute_after/_32_failure_fingerprint.py"

DIAG = {
    "error_class": "disk_full",
    "causal_chain": "write failed, device full",
    "raw_output_tail": 'File "/a0/usr/wiki/x.md", line 12: OSError [Errno 28] no space',
}
ARGS = {"method": "write", "path": "/a0/usr/wiki/target.md", "content": "z" * 3000}


async def main():
    agent = StubAgent()
    gate = load_ext(GATE, "MetaReasoningGate", agent)
    rec = load_ext(REC, "FailureFingerprint", agent)

    # 1. import resolves inside the extension context
    sys.path.insert(0, "/a0/usr/plugins/_exocortex/helpers")
    import failure_fingerprint as ff
    ok("helper imports from the container path", hasattr(ff, "op_signature"))

    # 2. gate stashes the signature
    await gate.execute(tool_args=dict(ARGS), tool_name="text_editor")
    stashed = agent.get_data(ff.OP_SIG_KEY)
    ok("gate stashed an op signature", bool(stashed), str(stashed))
    ok("stashed value matches a fresh computation",
       stashed == ff.op_signature("text_editor", ARGS))

    # 3. recorder reads it back and records a strike
    agent.set_data("_error_diagnosis", DIAG)
    await rec.execute(response=None, tool_name="text_editor")
    led = json.load(open(LEDGER))
    entries = led.get("entries", {})
    ok("recorder wrote a ledger entry", len(entries) == 1, f"entries={len(entries)}")
    e = list(entries.values())[0] if entries else {}
    ok("entry carries the SAME op signature the gate stashed",
       e.get("op_signature") == stashed, "handshake intact")
    ok("strike 1 recorded", e.get("strikes") == 1)

    # 4. two more strikes -> quarantine
    for _ in range(2):
        await gate.execute(tool_args=dict(ARGS), tool_name="text_editor")
        agent.set_data("_error_diagnosis", DIAG)
        await rec.execute(response=None, tool_name="text_editor")
    e = list(json.load(open(LEDGER))["entries"].values())[0]
    ok("three strikes -> quarantined", e.get("quarantined") is True, f"strikes={e.get('strikes')}")
    ok("evidence preserved at quarantine", bool(e.get("evidence", {}).get("causal_chain")))

    # 5. THE GATE NOW REFUSES
    blocked = False
    try:
        await gate.execute(tool_args=dict(ARGS), tool_name="text_editor")
    except ValueError as ex:
        blocked = "QUARANTINE" in str(ex)
    ok("gate REFUSES the quarantined attempt", blocked)
    ok("refusal surfaced to the agent log",
       any("QUARANTINE" in str(x.get("content", "")) for x in agent.context.log.entries))

    # 6. an unrelated call is untouched
    passed = True
    try:
        await gate.execute(tool_args={"method": "write", "path": "/a0/usr/wiki/other.md",
                                      "content": "hello"}, tool_name="text_editor")
    except ValueError:
        passed = False
    ok("a DIFFERENT target still executes", passed)

    # 7. refused attempts must not deepen the quarantine
    before = list(json.load(open(LEDGER))["entries"].values())[0]["strikes"]
    try:
        await gate.execute(tool_args=dict(ARGS), tool_name="text_editor")
    except ValueError:
        pass
    after = list(json.load(open(LEDGER))["entries"].values())[0]["strikes"]
    ok("a blocked attempt adds no strike", before == after, f"{before} -> {after}")

    # 8. Phase 5 handoff: the quarantine must reach the anti-pattern channel
    try:
        sys.path.insert(0, "/a0/usr/plugins/_exocortex/helpers")
        from procedural_memory_api import ProceduralMemory
        aps = [s for s in ProceduralMemory().index.get("skills", [])
               if s.get("type") == "ANTI-PATTERN" and "quarantine" in (s.get("tags") or [])]
        ok("quarantine filed as an ANTI-PATTERN for Phase 5", len(aps) >= 1, f"found={len(aps)}")
        ok("unconsumed, so Phase 5 will pick it up next cycle",
           any(not a.get("engine_consumed") for a in aps))
    except Exception as ex:
        ok("Phase 5 handoff", False, f"{type(ex).__name__}: {ex}")


asyncio.run(main())

# restore
try:
    os.remove(LEDGER)
except OSError:
    pass
if os.path.exists(BACKUP):
    os.replace(BACKUP, LEDGER)

print("\n" + (f"ALL {len(results)} PASS" if all(results)
              else f"FAILURES: {results.count(False)} of {len(results)}"))
sys.exit(0 if all(results) else 1)
