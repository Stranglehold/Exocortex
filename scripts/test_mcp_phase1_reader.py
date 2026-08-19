"""Branch coverage for _mcp_connection_state.

The `degraded` branch is already proven end-to-end in-process against the REAL
_02_mcp_health writer. This covers the branches that writer cannot easily produce on a
test container: no agent (backward compatibility), no cache, stale cache, and healthy.

A plain local import is legitimate here: the function is pure -- it only reads
attributes off the object handed to it. The reason a fresh process was NOT acceptable
for the writer is MCPConfig's singleton, which does not appear anywhere in this path.
"""
import importlib.util
import sys
import time

spec = importlib.util.spec_from_file_location(
    "sc", r"D:\Vibecode\Agent-Zero\Exocortex\plugins\_exocortex\helpers\sleep_consolidation.py")
sc = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(sc)
except Exception as e:
    print("module import failed (expected if it needs A0 at import time):", e)
    sys.exit(1)

f = sc._mcp_connection_state


class A:
    pass


def case(name, agent, expect_status, expect_in_detail=""):
    got = f(agent)
    ok = got["status"] == expect_status and expect_in_detail in got["detail"]
    print(("  PASS " if ok else "  FAIL ") + f"{name:22} -> {got['status']:9} {got['detail'][:60]}")
    return ok


results = []

# backward compatibility: old callers pass no agent at all
results.append(case("agent=None", None, "unknown", "no agent in scope"))

# extension disabled / not yet fired in this process
results.append(case("no cache", A(), "unknown", "no cached _mcp_health"))

# healthy
a = A()
a._mcp_health = {"checked_at": time.time(), "total": 3, "connected": 3,
                 "required_missing": [], "required_down": [], "degraded": False}
results.append(case("healthy", a, "ok", "3/3"))

# stale cache must NOT be upgraded to ok
b = A()
b._mcp_health = {"checked_at": time.time() - 5000, "total": 3, "connected": 3,
                 "required_missing": [], "required_down": [], "degraded": False}
results.append(case("stale cache", b, "unknown", "cannot vouch"))

# a stale cache that is ALSO degraded must stay degraded, not be softened to unknown
c = A()
c._mcp_health = {"checked_at": time.time() - 5000, "total": 3, "connected": 2,
                 "required_missing": [], "required_down": ["exocortex-memory"], "degraded": True}
results.append(case("stale AND degraded", c, "degraded", "CONFIGURED BUT DOWN"))

# malformed cache must not raise
d = A()
d._mcp_health = {"checked_at": "not-a-number", "required_down": None}
results.append(case("malformed cache", d, "unknown", "malformed"))

print("\n" + ("ALL PASS" if all(results) else "FAILURES PRESENT"))
sys.exit(0 if all(results) else 1)
