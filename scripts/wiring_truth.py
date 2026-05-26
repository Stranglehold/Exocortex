#!/usr/bin/env python3
"""
wiring_truth.py — runtime "what is ACTUALLY wired" readout for OSS + SWARMFISH.

Runs INSIDE the container (`/opt/venv-a0/bin/python3 wiring_truth.py`). Every gap
this session cost time because the system couldn't tell me the truth about itself —
which LLM endpoint a module resolved to, whether a DB was the one I thought, whether
FAISS and SQLite agreed, whether a renamed package left residue. This reports that
ground truth so verification is a readout, not an archaeology dig.

Sections:
  - MODULE FILES   — which plugin modules exist where (+ collision residue).
  - LLM ENDPOINTS  — the URL each LLM-using module resolves to (env or source default),
                     reachability, and DRIFT flags when siblings point different places.
                     (This is the check that would have caught the silence/synthesis
                     :1234 dead-port drift at a glance.)
  - DATABASES      — path, table count, key row counts per plugin DB.
  - FAISS          — index ntotal vs claims-with-faiss_id (DESYNC detector).

Deterministic, no LLM, read-only. Exit 0 always (diagnostic); WARN lines flag problems.
"""
from __future__ import annotations

import os
import re
import sqlite3
import urllib.request

OSS_PLUGIN = "/a0/usr/plugins/oss"
SWF_PLUGIN = "/a0/usr/plugins/swarmfish"
OSS_DB     = "/a0/usr/oss/oss.db"
SWF_DB     = "/a0/usr/swarmfish/swarmfish.db"
OSS_FAISS  = "/a0/usr/oss/claims.index"

# (label, module file, env var the module reads, regex for its hardcoded default)
LLM_MODULES = [
    ("oss.ingest",        f"{OSS_PLUGIN}/src/ingest.py",        "OSS_LLM_URL",       r'OSS_LLM_URL"?,\s*"([^"]+)"'),
    ("oss.silence",       f"{OSS_PLUGIN}/src/silence.py",       "OSS_LLM_URL",       r'OSS_LLM_URL"?,\s*"([^"]+)"'),
    ("oss.synthesis",     f"{OSS_PLUGIN}/src/synthesis.py",     "OSS_LLM_URL",       r'OSS_LLM_URL"?,\s*"([^"]+)"'),
    ("oss.llm_config",    f"{OSS_PLUGIN}/src/llm_config.py",    "OSS_LLM_URL",       r'OSS_LLM_URL"?,\s*"([^"]+)"'),
    ("swarmfish.predictor", f"{SWF_PLUGIN}/swfsrc/predictor.py", "SWARMFISH_LLM_URL", r'SWARMFISH_LLM_URL"?,\s*"([^"]+)"'),
    ("swarmfish.llm_config", f"{SWF_PLUGIN}/swfsrc/llm_config.py", "SWARMFISH_LLM_URL", r'SWARMFISH_LLM_URL"?,\s*"([^"]+)"'),
]

WARN = "  [WARN] "


def _resolve_url(env_var, default):
    return os.environ.get(env_var) or default


def _reach(url):
    """Return (reachable, first_model_id_or_error)."""
    base = url.rstrip("/")
    try:
        req = urllib.request.Request(base + "/models", headers={"Authorization": "Bearer x"})
        with urllib.request.urlopen(req, timeout=5) as r:
            import json
            data = json.loads(r.read())
        ids = [m.get("id") for m in data.get("data", [])]
        return True, (ids[0] if ids else "(no models listed)")
    except Exception as e:
        return False, str(e)[:60]


def section_modules():
    print("\n=== MODULE FILES ===")
    for label, base in (("oss/src", f"{OSS_PLUGIN}/src"), ("swarmfish/swfsrc", f"{SWF_PLUGIN}/swfsrc")):
        if os.path.isdir(base):
            n = len([f for f in os.listdir(base) if f.endswith(".py")])
            print(f"  {label}: {n} modules")
        else:
            print(WARN + f"{label}: directory MISSING ({base})")
    # Collision residue: a stale `src` beside the renamed `swfsrc` would re-introduce
    # the sys.modules['src.db'] collision with OSS.
    stale = f"{SWF_PLUGIN}/src"
    if os.path.isdir(stale):
        print(WARN + f"swarmfish stale 'src' dir still present ({stale}) — src-collision risk")
    else:
        print("  swarmfish 'src' residue: none (collision-safe)")


def section_llm():
    print("\n=== LLM ENDPOINTS (resolved per module) ===")
    resolved = {}
    reach_cache = {}
    for label, path, env_var, default_rx in LLM_MODULES:
        if not os.path.isfile(path):
            print(WARN + f"{label}: file missing ({path})")
            continue
        src = open(path, encoding="utf-8").read()
        m = re.search(default_rx, src)
        default = m.group(1) if m else "(no default found)"
        url = _resolve_url(env_var, default)
        resolved[label] = url
        if url not in reach_cache:
            reach_cache[url] = _reach(url)
        ok, info = reach_cache[url]
        status = f"REACHABLE: {info}" if ok else f"UNREACHABLE: {info}"
        flag = "" if ok else WARN.strip()
        print(f"  {label:24} {url:40} [{status}] {flag}")

    # Drift detector: OSS modules should agree on one endpoint; swarmfish on one.
    for group, prefix in (("OSS", "oss."), ("SWARMFISH", "swarmfish.")):
        urls = {v for k, v in resolved.items() if k.startswith(prefix)}
        if len(urls) > 1:
            print(WARN + f"{group} endpoint DRIFT — modules resolve to different URLs: {sorted(urls)}")


def _counts(db, queries):
    out = {}
    try:
        c = sqlite3.connect(db)
        for label, q in queries.items():
            try:
                out[label] = c.execute(q).fetchone()[0]
            except Exception as e:
                out[label] = f"ERR({str(e)[:30]})"
        c.close()
    except Exception as e:
        return {"_error": str(e)[:60]}
    return out


def section_databases():
    print("\n=== DATABASES ===")
    if os.path.isfile(OSS_DB):
        tables = _counts(OSS_DB, {"tables": "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"})["tables"]
        c = _counts(OSS_DB, {
            "claims":     "SELECT COUNT(*) FROM claims",
            "promoted":   "SELECT COUNT(*) FROM claims WHERE trust_level='PROMOTED'",
            "topics":     "SELECT COUNT(*) FROM topics",
            "hypotheses": "SELECT COUNT(*) FROM hypothesis_registry",
            "rejections": "SELECT COUNT(*) FROM rejection_ledger",
        })
        print(f"  oss.db ({OSS_DB}): {tables} tables")
        print(f"    claims={c['claims']} (promoted {c['promoted']}) | topics={c['topics']} | "
              f"hypotheses={c['hypotheses']} | rejections={c['rejections']}")
    else:
        print(WARN + f"oss.db missing ({OSS_DB})")

    if os.path.isfile(SWF_DB):
        tables = _counts(SWF_DB, {"t": "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"})["t"]
        c = _counts(SWF_DB, {
            "sessions":    "SELECT COUNT(*) FROM acp_sessions",
            "assessments": "SELECT COUNT(*) FROM acp_assessments",
            "profiles":    "SELECT COUNT(*) FROM acp_profiles",
            "outcomes":    "SELECT COUNT(*) FROM acp_outcomes",
            "calibration": "SELECT COUNT(*) FROM acp_calibration",
        })
        print(f"  swarmfish.db ({SWF_DB}): {tables} tables")
        print(f"    sessions={c['sessions']} | assessments={c['assessments']} | profiles={c['profiles']} | "
              f"outcomes={c['outcomes']} | calibration={c['calibration']}")
    else:
        print(WARN + f"swarmfish.db missing ({SWF_DB})")


def section_faiss():
    print("\n=== FAISS ===")
    if not os.path.isfile(OSS_FAISS):
        print(f"  oss claims.index: not present (no claims embedded yet)")
        return
    try:
        import faiss
        ntotal = faiss.read_index(OSS_FAISS).ntotal
    except Exception as e:
        print(WARN + f"could not read index: {str(e)[:60]}")
        return
    with_id = _counts(OSS_DB, {"n": "SELECT COUNT(*) FROM claims WHERE faiss_id IS NOT NULL"}).get("n", "?")
    consistent = (isinstance(with_id, int) and with_id == ntotal)
    tag = "CONSISTENT" if consistent else "DESYNC"
    line = f"  oss claims.index: ntotal={ntotal} | claims with faiss_id={with_id}  [{tag}]"
    print(line if consistent else (WARN + line.strip()))


def main():
    import datetime
    print("=" * 72)
    print(f"WIRING TRUTH — {datetime.datetime.now().isoformat(timespec='seconds')}")
    print("=" * 72)
    section_modules()
    section_llm()
    section_databases()
    section_faiss()
    print("\n" + "=" * 72)
    print("(WARN lines above are the things to look at.)")


if __name__ == "__main__":
    main()
