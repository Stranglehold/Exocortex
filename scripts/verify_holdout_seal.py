#!/usr/bin/env python3
"""
verify_holdout_seal.py — assert Pool B has never leaked into a container

WHY THIS EXISTS
---------------
Phase B's validation design uses two structurally disjoint task pools:

  Pool A (acceptance)  visible during the improvement cycle; the PACE e-process runs
                       against it and the commit/reject decision is made there.
  Pool B (holdout)     sealed. Same capabilities, different concrete scenarios. Run
                       only AFTER a change is accepted, to check it generalised.

Pool A improving while Pool B does not means the change overfit the acceptance set.
That signal is worth exactly as much as the seal is airtight, and not one bit more.

THE SEAL IS THE API BOUNDARY (Opus, 2026-08-20)
Pool B lives on the HOST. The agents live in containers and reach the host only
through `/api/api_message`. The harness reads Pool B, sends the task as an ordinary
prompt, and evaluates the response. The agent cannot tell a Pool A task from a Pool B
task from a normal request, and cannot read what it was never given.

WHY A MECHANICAL CHECK RATHER THAN A CONVENTION
-----------------------------------------------
Pool B has to live in the repo (Opus authors it there, it must be reviewable and
version-controlled) and must NEVER be deployed. That cuts directly against the install
pipeline's own design principle — "deploy by directory walk, no curated list; if
something shouldn't be deployed, it shouldn't be in the repo." Pool B is the one thing
that has to be in the repo and out of the container.

A rule that contradicts the pipeline's organising principle will eventually be broken
by someone following that principle correctly. So it is enforced by a gate rather than
trusted to memory.

WHAT IT CHECKS
--------------
1. No holdout PATH exists in the container.
2. No file in the container matches the CONTENT HASH of any holdout file — this is the
   one that matters, because a copy under a different name defeats a path check but not
   a hash check.

Exit 0 only when both hold for every container checked.

Usage:
  python scripts/verify_holdout_seal.py                 # all known containers
  python scripts/verify_holdout_seal.py VekV2 ...       # specific ones
"""
import hashlib
import json
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOLDOUT_DIR = os.path.join(REPO, "harness", "holdout")
DEFAULT_CONTAINERS = ["VekV2", "agent-zero-v2", "exo_installtest"]

# Paths a holdout file must never appear under, checked directly.
FORBIDDEN_PATHS = [
    "/a0/usr/plugins/_exocortex/harness",
    "/a0/usr/harness",
    "/a0/harness",
    "/a0/usr/holdout",
    "/a0/usr/plugins/_exocortex/holdout",
]

_ENV = dict(os.environ, MSYS_NO_PATHCONV="1")


def dexec(container, *args):
    return subprocess.run(["docker", "exec", container, *args],
                          capture_output=True, text=True, env=_ENV)


# ── A STOPPED container still has a filesystem ──────────────────────────────────
# Until 2026-09-14 a stopped container printed "not running — skipped" and contributed
# ZERO violations to a CLEAN verdict. VekV2 has been down deliberately since 2026-08-31,
# so one of the two live-pair containers went unchecked for two weeks while this seal
# read INTACT — the instrument skipping half its surface and reporting clean, which is
# the shape found three times this month.
#
# `docker exec` cannot reach a stopped container. `docker cp` CAN, measured tonight:
# VekV2:/a0/usr streamed 40,131 files / 279.7 MB in 431s, rc=0. So the question "did
# holdout content land on this container's disk" is answerable; only "could a live agent
# retrieve it through its tools" genuinely is not (Opus's ruling: two verdicts, not one).
#
# Cost shapes the design. 431s per container is too slow for every run, and a stopped
# container CANNOT CHANGE unless somebody copies into it — so a deep result stays valid
# until the container is touched. Keyed on the container's FinishedAt plus a digest of
# the holdout set, cached under harness/ (excluded from the index), and re-run when
# either moves.
DEEP = False             # set from --deep in main()
# NOT under HOLDOUT_DIR. The first version put it there — `harness/holdout/` — and the
# seal hashes every file in that tree as holdout content, so within one run the cache
# became a fourth "holdout file" the seal would then hunt for inside every container.
# Worse, the cache key includes a digest of that hash set, so writing the cache changed
# the key and the cache could never hit: self-defeating and self-polluting at once, from
# misreading my own constant (HOLDOUT_DIR is harness/holdout, not harness).
# `harness/` is excluded from the index and is not part of the holdout set.
DEEP_CACHE = os.path.join(REPO, "harness", ".seal_deep_cache.json")
DEEP_EXTS = (".md", ".json", ".jsonl", ".py", ".txt", ".yaml", ".yml")


def dcp_exists(container, path):
    """Does `path` exist inside a container that may be stopped? ('yes'|'no'|'unknown')."""
    r = subprocess.run(["docker", "cp", f"{container}:{path}", "-"],
                       capture_output=True, env=_ENV)
    if r.returncode == 0:
        return "yes"
    err = (r.stderr or b"").decode("utf-8", "replace").lower()
    if "could not find the file" in err or "no such file or directory" in err:
        return "no"
    return "unknown"


def _deep_key(container, hashes):
    fin = subprocess.run(["docker", "inspect", "-f", "{{.State.FinishedAt}}", container],
                         capture_output=True, text=True, env=_ENV)
    return "%s|%s|%s" % (container, (fin.stdout or "").strip(),
                         hashlib.sha256("".join(sorted(hashes)).encode()).hexdigest()[:16])


def deep_scan_stopped(container, hashes):
    """Hash every text file inside a stopped container, streaming, writing nothing.

    Returns (violations, how) where `how` is 'cached' | 'scanned' | 'UNAVAILABLE: …'.
    """
    # KNOWN HOLE, ruled acceptable by Opus 2026-09-14 and written down rather than left
    # to be rediscovered: the key is the container's `FinishedAt`, so someone who
    # `docker cp`s INTO a stopped container does not move it and the cache stays valid.
    # That is a deliberate act by someone with docker access, who is also in a position
    # to delete this file; the alternative key is a tar-stream digest, which costs the
    # full 431s and so defeats the cache entirely. If it ever matters, drop the file.
    key = _deep_key(container, hashes)
    try:
        cache = json.load(open(DEEP_CACHE, encoding="utf-8"))
    except Exception:
        cache = {}
    if cache.get(key) is not None:
        return list(cache[key]), "cached"
    import tarfile
    problems = []
    hashed = 0               # the positive control: a scan that read nothing is not clean
    for root in ("/a0/usr", "/a0/prompts"):
        p = subprocess.Popen(["docker", "cp", f"{container}:{root}", "-"],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_ENV)
        try:
            tf = tarfile.open(fileobj=p.stdout, mode="r|")
            for mem in tf:
                if not mem.isfile() or not mem.name.lower().endswith(DEEP_EXTS):
                    continue
                fh = tf.extractfile(mem)
                if fh is None:
                    continue
                digest = hashlib.md5(fh.read()).hexdigest()
                hashed += 1
                if digest in hashes:
                    problems.append("%s: HOLDOUT CONTENT LEAKED (stopped container, on "
                                    "disk) -> %s/%s (matches %s)"
                                    % (container, root, mem.name, hashes[digest]))
        except Exception as exc:
            err = (p.stderr.read() or b"").decode("utf-8", "replace")[:160] if p.stderr else ""
            try:
                p.stdout.close()
            except Exception:
                pass
            p.wait()
            # A stream that died mid-way has NOT cleared the container. Never cached.
            return problems, "UNAVAILABLE: %s (%s) %s" % (type(exc).__name__, exc, err)
        finally:
            try:
                p.stdout.close()
            except Exception:
                pass
            p.wait()
        if p.returncode != 0:
            return problems, "UNAVAILABLE: docker cp %s exited %d" % (root, p.returncode)
    # POSITIVE CONTROL. A stream that yielded no hashable file reports no violations and
    # is indistinguishable from a clean container — the shape this whole file exists to
    # refuse. An A0 container holds tens of thousands of text files; a handful means the
    # extension filter or the stream matched almost nothing, and that is a finding.
    if hashed < 100:
        return problems, ("UNVERIFIED: only %d file(s) were hashed, which is implausible "
                          "for an A0 container — the scan did not see the tree" % hashed)
    cache[key] = problems
    try:
        with open(DEEP_CACHE, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, indent=1)
    except OSError as exc:
        # Not fatal — the scan itself was real — but a cache that silently never lands
        # means every future run pays 431s and nobody knows why.
        print("  (deep-scan cache not written: %s: %s)" % (type(exc).__name__, exc))
    return problems, "scanned, %d files hashed" % hashed


_HASH_FAULT = []         # populated when a holdout file cannot be hashed


def _check_holdout_dir():
    """An ABSENT holdout tree is unverified; an EMPTY one is the documented early state.

    Found while controlling the two fixes above: pointing HOLDOUT_DIR at a missing
    path gave zero hashes and zero faults, because `os.walk` on a missing directory
    yields nothing and the OSError handler never fires. The distinction matters —
    this gate was deliberately built before Pool B had content, so an empty tree is
    expected and gets a NOTE, while a tree that has gone missing means the content
    check cannot run at all.
    """
    if not os.path.isdir(HOLDOUT_DIR):
        _HASH_FAULT.append("UNVERIFIED -- the holdout tree at %s does not exist, so the "
                           "content check has nothing to compare against and cannot run"
                           % HOLDOUT_DIR)


def holdout_hashes() -> dict:
    """md5 -> relative path, for every file in the holdout tree."""
    out = {}
    if not os.path.isdir(HOLDOUT_DIR):
        return out
    for root, _dirs, files in os.walk(HOLDOUT_DIR):
        if "__pycache__" in root:
            continue
        for fn in files:
            p = os.path.join(root, fn)
            try:
                with open(p, "rb") as fh:
                    out[hashlib.md5(fh.read()).hexdigest()] = os.path.relpath(p, REPO)
            except OSError as exc:
                # FAILS CLOSED. A holdout file that cannot be hashed cannot be
                # detected in a container, and the hash check is the one the
                # docstring calls "the one that matters, because a copy under a
                # different name defeats a path check but not a hash check".
                # Skipping it silently removed exactly that guarantee.
                _HASH_FAULT.append("UNVERIFIED -- holdout file %s could not be read "
                                   "(%s), so a copy of it in any container would go "
                                   "undetected" % (os.path.relpath(p, REPO), type(exc).__name__))
    return out


def check(container: str, hashes: dict) -> list:
    """Return a list of violations for one container."""
    problems = []

    up = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", container],
                        capture_output=True, text=True, env=_ENV)
    if up.returncode != 0:
        # FAIL CLOSED when the DAEMON is unreachable (Kestrel, 2026-09-11).
        # `docker inspect` fails identically for "this container does not exist"
        # and "Docker is not running", and the first is a legitimate skip while
        # the second means this half of the seal was NOT CHECKED. Until today
        # both printed "not found — skipped" and contributed zero violations —
        # a fail-open in the one place that exists to fail closed, and the same
        # shape the index and disk controls were deliberately written against.
        # Found when Docker Desktop went down mid-session and the seal reported
        # only its disk half while reading as though the containers were clean.
        err = (up.stderr or "").lower()
        daemon_down = ("cannot find the file specified" in err
                       or "daemon" in err
                       or "connect to the docker api" in err
                       or "docker daemon is not running" in err)
        if daemon_down:
            print(f"  {container:<18} UNVERIFIED — Docker unreachable")
            problems.append(f"{container}: UNVERIFIED — the Docker daemon is "
                            f"unreachable, so this container was never checked")
        else:
            print(f"  {container:<18} not found — skipped")
        return problems
    if up.stdout.strip() != "true":
        # TWO VERDICTS, not one (Opus, 2026-09-14). The filesystem is checkable while
        # stopped; the runtime is not. Reporting a single "skipped" conflated them and
        # let a container contribute zero violations to a CLEAN seal for two weeks.
        for p in FORBIDDEN_PATHS:
            state = dcp_exists(container, p)
            if state == "yes":
                problems.append(f"{container}: forbidden path EXISTS (stopped container, "
                                f"on disk): {p}")
            elif state == "unknown":
                problems.append(f"{container}: UNVERIFIED — could not determine whether "
                                f"{p} exists on the stopped container's disk")
        how = "paths only"
        if hashes and DEEP:
            found, how = deep_scan_stopped(container, hashes)
            problems.extend(found)
            if how.startswith("UNAVAILABLE"):
                problems.append(f"{container}: UNVERIFIED — the on-disk content scan of "
                                f"this stopped container could not complete ({how})")
        elif hashes:
            # Named, not silent. A gap someone can see is a different thing from a gap
            # that reads as clean — but it is still a gap, so say what closes it.
            problems.append(f"{container}: UNVERIFIED — stopped, and the on-disk CONTENT "
                            f"scan was not run (the path checks were). Re-run with --deep "
                            f"(~7 min/container, cached until the container changes).")
        print(f"  {container:<18} stopped — disk CHECKED ({how}), runtime SKIPPED")
        return problems

    # 1. forbidden paths
    for p in FORBIDDEN_PATHS:
        r = dexec(container, "test", "-e", p)
        if r.returncode == 0:
            problems.append(f"{container}: forbidden path EXISTS: {p}")

    # 2. content hashes — the check a rename cannot defeat
    if hashes:
        r = dexec(container, "sh", "-c",
                  "find /a0/usr /a0/prompts -type f "
                  "\\( -name '*.md' -o -name '*.json' -o -name '*.jsonl' -o -name '*.py' \\) "
                  "2>/dev/null | head -20000 | xargs -r md5sum 2>/dev/null")
        for line in (r.stdout or "").splitlines():
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            digest, path = parts[0], parts[1].strip()
            if digest in hashes:
                problems.append(
                    f"{container}: HOLDOUT CONTENT LEAKED -> {path} "
                    f"(matches {hashes[digest]})")

    if not problems:
        print(f"  {container:<18} sealed")
    return problems



# ---------------------------------------------------------------------------
# THE INDEX CONTROL (Kestrel, 2026-09-11; approved by Opus the same day)
#
# The checks above ask "is a holdout FILE reachable from a container" -- by path,
# and by content hash. Neither can see a holdout scenario DESCRIBED in
# correspondence. On 2026-09-11 all eight task ids were found in four indexed
# documents: three team-inbox letters written on the day the holdout was designed,
# and Kestrel's own KESTREL.md, added to the index on 2026-09-10 by our decision.
#
# The seal was believed to rest on the API boundary, then on the `harness`
# directory exclusion. It actually rested on nobody having written the scenarios
# down somewhere searchable. We wrote them down.
#
# A search RANKS; an audit SCANS. A semantic query returned one letter; scanning
# every row returned four documents. This scans.
# ---------------------------------------------------------------------------

# LANCE_DB is resolved by _resolve_db() below, the same way as the pattern. It used to be
# os.environ.get("OPUS_MEMORY_DB", <path>), and the fallback path is the database RETIRED
# on 2026-09-19 (the live index is the one the launcher sets). A run from a shell without the
# variable audited a stale table and could report INTACT for it (Kestrel, found 2026-09-24).
_DB_ENV = "OPUS_MEMORY_DB"
_RETIRED_DB = r"D:\Vibecode\docker-mcp-server\opus-memory-lancedb"
_DB_FAULT = []           # populated when the index in force is the retired default
# ONE SOURCE OF TRUTH WITH THE INDEXER (Kestrel, 2026-09-14).
#
# This was a hardcoded `\bHB-\d{2}\b` while the memory server read its pattern from
# OPUS_MEMORY_HOLDOUT_ID_PATTERN. When Pool B was re-authored with `VXR-` identifiers
# the two diverged, and the failure was not a visible error — it was a CONFIDENT PASS.
# The new config happens to mention HB-01 and HB-08 in prose, so this function returned
# two stale identifiers rather than none, and the seal reported
#
#     index  no document names any of 2 holdout task ids
#
# with its positive control healthy, while all EIGHT live identifiers were invisible to
# it. Returning zero would at least have looked wrong. Reading the same env as the thing
# it audits is the only arrangement in which the two cannot drift apart.
_DEFAULT_ID_PATTERN = r"\bHB-\d{2}\b"
_HOLDOUT_ENV = "OPUS_MEMORY_HOLDOUT_ID_PATTERN"
_LAUNCHER = os.environ.get(
    "SEAL_LAUNCHER", r"D:\Vibecode\docker-mcp-server\start_opus_memory_service.bat")
_PATTERN_FAULT = []      # populated when the pattern in force is the narrow default


def _resolve_pattern() -> str:
    """Where the pattern in force comes from: 'env' | 'launcher' | 'NARROW DEFAULT'.

    Reading the same variable as the indexer fixed the divergence above, but left a
    second way for the two to agree on the wrong thing: this script inherits whatever
    shell runs it. A scheduled run from an environment without the variable audits
    against `\\bHB-\\d{2}\\b` — and so does a server started the same way — so BOTH
    halves go blind in the same direction and the seal reports INTACT. That is the
    2026-09-11 class exactly: the instrument and its subject sharing a blind spot.

    Launcher of record is the `set` line in start_opus_memory_service.bat beside the
    server, which is the only place that pattern is allowed to live. Never printed.

    Fable's `harness/verify_coverage.py` does the same three steps and prints a warning.
    This one goes further and raises a FAULT, because a coverage check that misclassifies
    is wrong and a seal that warns can be believed while blind. A seal's whole value is
    that its INTACT means something.
    """
    if os.environ.get(_HOLDOUT_ENV):
        return "env"
    # BOTH cmd forms: `set VAR=value` and `set "VAR=value"`. This matched only the bare
    # one, and on 2026-09-14 the launcher was corrected to the quoted form (the value
    # contains a pipe, which cmd parses as syntax unless quoted). The seal then found no
    # `set` line, fell back to the narrow default, and reported eight PATTERN GAPs
    # against a live scheme it simply could not see.
    #
    # It is the same defect I had just fixed in `restart_memory_server.py` and did not
    # sweep for here — "fix the branch you tripped over, miss the file it lives in",
    # which is the thing I wrote a memory file about. The seal's own fault machinery
    # caught it and refused to report INTACT, which is the gate working on its author.
    pat = re.compile(r'^\s*set\s+(?:"%s=([^"]*)"|%s=(.*?))\s*$'
                     % (_HOLDOUT_ENV, _HOLDOUT_ENV), re.I)
    try:
        with open(_LAUNCHER, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                s = line.strip()
                if s.lower().startswith("rem ") or s.startswith("::"):
                    continue
                m = pat.match(s)
                if m:
                    os.environ[_HOLDOUT_ENV] = (m.group(1) if m.group(1) is not None
                                                else m.group(2))
                    return "launcher"
    except OSError:
        pass
    return "NARROW DEFAULT"


_PATTERN_SOURCE = _resolve_pattern()
TASK_ID_RE = re.compile(os.environ.get(_HOLDOUT_ENV, _DEFAULT_ID_PATTERN))
# A digest, never the pattern, so this can be compared against the running server's
# /version (`holdout_pattern_sha8`) without either side writing it down.
_PATTERN_SHA8 = hashlib.sha256(TASK_ID_RE.pattern.encode("utf-8")).hexdigest()[:8]
if _PATTERN_SOURCE == "NARROW DEFAULT":
    _PATTERN_FAULT.append(
        "UNVERIFIED -- the holdout pattern in force is the NARROW DEFAULT: no %s in the "
        "environment and no `set` line found in %s. A re-authored scheme is invisible to "
        "this run, so INTACT would mean 'found nothing with a pattern that may not match "
        "anything', which is not a seal. Fix the launcher or set the variable."
        % (_HOLDOUT_ENV, _LAUNCHER))

def _resolve_db():
    """(path, source) of the index the LIVE server serves: 'env' | 'launcher' | 'RETIRED DEFAULT'.

    The same three steps as _resolve_pattern, parsing the same launcher of record with the
    same two `set` forms, so the index and the pattern can never come from different places.
    Fable's harness/verify_coverage.py resolves its DB the same way (2026-09-24). The retired
    default is a FAULT, not a warning: an INTACT computed against a table nobody writes any
    more describes nothing.
    """
    val = os.environ.get(_DB_ENV)
    if val:
        return val, "env"
    pat = re.compile(r'^\s*set\s+(?:"%s=([^"]*)"|%s=(.*?))\s*$' % (_DB_ENV, _DB_ENV), re.I)
    try:
        with open(_LAUNCHER, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                s = line.strip()
                if s.lower().startswith("rem ") or s.startswith("::"):
                    continue
                m = pat.match(s)
                if m:
                    return (m.group(1) if m.group(1) is not None else m.group(2)).strip(), "launcher"
    except OSError:
        pass
    return _RETIRED_DB, "RETIRED DEFAULT"


LANCE_DB, _DB_SOURCE = _resolve_db()
if _DB_SOURCE == "RETIRED DEFAULT":
    _DB_FAULT.append(
        "index UNVERIFIED -- no %s in the environment and no `set` line in %s, so this run "
        "fell back to %s, the database RETIRED on 2026-09-19. INTACT would describe a stale "
        "table. Fix the launcher or set the variable." % (_DB_ENV, _LAUNCHER, _RETIRED_DB))


# Deliberately WIDER than TASK_ID_RE: used only to discover identifier-SHAPED tokens in
# the sealed config so they can be tested against the pattern in force. A check that
# used the audited pattern to find what the audited pattern should match would share its
# blind spot exactly, which is how the gap above stayed invisible.
ID_SHAPE_RE = re.compile(r"\b[A-Z]{2,5}-[0-9A-Za-z]{2,4}\b")


_TASK_ID_FAULT = []      # populated when the sealed config cannot be read
# Identifier-shaped tokens present in the config but NOT declared as tasks. Reported,
# never silently dropped: that is what a live id looks like the moment before someone
# forgets to declare it, and it is also how the two retired HB ids were mistaken for
# live ones for long enough to produce three false SEAL BROKEN violations.
_UNDECLARED_IDS = []


def holdout_task_ids():
    """Task ids declared in the sealed config -- what must never be searchable.

    FAILS CLOSED (Kestrel, 2026-09-11, third instance in this file). This used to
    return [] when the config was unreadable, and an empty id list turns BOTH the
    index and disk controls into no-ops that print "nothing to check" and report no
    violations. So a missing or unreadable config silently passed the two halves
    written specifically to fail closed. Found by `instruments/audit_silent_branches.py`
    after the same shape was found in check() an hour earlier -- I fixed the branch
    I tripped over and never swept the file it was in.

    DECLARED ids come from the structured field, not from a regex over the whole file
    (Kestrel, 2026-09-14). Scanning the text returned 10 ids where the config declares
    8: `HB-01` and `HB-08` appear only inside `$._comment`, as prose about the scheme
    that replaced them. Both are retired. The seal therefore reported three inbox
    letters from 2026-08-20 as SEAL BROKEN for naming ids that are not holdout tasks —
    false positives against correspondence, in the one instrument whose alarms have to
    be worth reacting to. A check that cries wolf gets read as noise, and then a real
    leak is a line someone skims past.

    The prose tokens are not discarded silently. They come back as a reported category,
    because "identifier-shaped, present in the config, not declared" is a thing someone
    should see — it is what a live id looks like the moment before someone forgets to
    declare it.
    """
    cfg = os.path.join(HOLDOUT_DIR, "config.json")
    try:
        with open(cfg, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        _TASK_ID_FAULT.append("UNVERIFIED -- the sealed config at %s could not be read "
                              "(%s), so no task id is known and neither the index nor "
                              "the disk control can check anything"
                              % (cfg, type(exc).__name__))
        return []
    try:
        cfg_obj = json.loads(raw)
        tasks = cfg_obj["tasks"]
        declared = sorted({t["id"] for t in tasks if t.get("id")})
    except Exception as exc:
        # Fails CLOSED, and loudly. An empty id list turns BOTH the index and the disk
        # control into no-ops that print "nothing to check" and report no violations —
        # the shape this function was already fixed for once, arriving by a new route.
        _TASK_ID_FAULT.append("UNVERIFIED -- the sealed config at %s has no readable "
                              "tasks[].id (%s: %s), so no task id is known and neither "
                              "the index nor the disk control can check anything"
                              % (cfg, type(exc).__name__, exc))
        return []
    if not declared:
        _TASK_ID_FAULT.append("UNVERIFIED -- the sealed config at %s declares zero task "
                              "ids; both controls would pass vacuously" % cfg)
        return []
    undeclared = sorted(set(TASK_ID_RE.findall(raw)) - set(declared))
    if undeclared:
        _UNDECLARED_IDS.extend(undeclared)
    return declared


def check_pattern_covers_config():
    """Every identifier-shaped token in the sealed config must be matched by the pattern.

    An identifier scheme is a CLAIM about what the filter will catch, and the only way to
    know is to test each identifier against the pattern before either goes live. On
    2026-09-14 `\\bVXR-[0-9a-f]{3}\\b` was proposed alongside identifiers containing `g`
    and `h`, which are not hex: six of eight covered, two silently not. Four lines, run
    every time, rather than left to whoever remembers.
    """
    problems = []
    cfg = os.path.join(HOLDOUT_DIR, "config.json")
    try:
        with open(cfg, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError:
        return problems          # already reported by holdout_task_ids()

    shaped = sorted(set(ID_SHAPE_RE.findall(raw)))
    if not shaped:
        print("  pattern           no identifier-shaped token in the sealed config")
        return problems

    missed = [s for s in shaped if not TASK_ID_RE.search(s)]
    print("  pattern           %d identifier(s) in the config, %d covered by the pattern"
          % (len(shaped), len(shaped) - len(missed)))
    for s in missed:
        problems.append("PATTERN GAP -- %s is in the sealed config but the holdout "
                        "pattern in force does not match it, so it would pass the "
                        "chunk filter AND go unreported here" % s)
    return problems


def check_index(ids):
    """One violation per indexed document naming a holdout task id.

    Fails CLOSED: an unreadable table is reported as an unverified seal, never as
    a pass. A gate that passes what it cannot read is the severed shape.
    """
    problems = []
    if not ids:
        print("  index             no task ids in the sealed config -- nothing to check")
        return problems
    # EVERY non-library table, not `chunks` (Fable's proposal, 2026-09-24). Per-agent collections
    # split the corpus into six tables, and `chunks` stays behind for rollback. A seal that read
    # `chunks` alone would pass a stale table while the six live ones went unaudited. Anything a
    # search can reach must be clean, and that includes leftovers and backups (chunks,
    # chunks_pre_split, ...). Only the book library is out of scope: it never held project text.
    try:
        import lancedb
        _db = lancedb.connect(LANCE_DB)
        names = sorted(t for t in _db.table_names() if not t.startswith("library_"))
        if not names:
            problems.append("index UNVERIFIED -- %s holds no corpus table" % LANCE_DB)
            return problems
        rows = {"source_path": [], "content": []}
        per_table = {}
        for _n in names:
            _d = (_db.open_table(_n).search().limit(0)
                  .select(["source_path", "content"]).to_arrow().to_pydict())
            rows["source_path"].extend(_d["source_path"])
            rows["content"].extend(_d["content"])
            per_table[_n] = len(_d["source_path"])
    except Exception as e:
        problems.append("index UNVERIFIED -- could not read %s (%s: %s)"
                        % (LANCE_DB, type(e).__name__, e))
        return problems
    print("  index             tables scanned: %s"
          % ", ".join("%s=%d" % (k, v) for k, v in per_table.items()))

    total = len(rows["source_path"])
    leaks = {}
    for src, txt in zip(rows["source_path"], rows["content"]):
        hit = set(i for i in ids if i in (txt or ""))
        if hit:
            leaks.setdefault(src, set()).update(hit)

    # Positive control. A scan that cannot find a term certainly present is broken,
    # and its silence would otherwise read as a clean corpus.
    canary = sum(1 for t in rows["content"] if t and "holdout" in t.lower())
    if canary == 0:
        problems.append("index UNVERIFIED -- positive control failed: 'holdout' appears "
                        "in no indexed row, so this scan cannot detect anything")
        return problems

    print("  index             %d rows scanned, positive control OK (%d rows mention 'holdout')"
          % (total, canary))
    for src in sorted(leaks):
        problems.append("%s names holdout task ids: %s" % (src, " ".join(sorted(leaks[src]))))
    if not leaks:
        print("  index             no document names any of %d holdout task ids" % len(ids))
    return problems



# ---------------------------------------------------------------------------
# THE DISK CONTROL (Kestrel, 2026-09-11)
#
# check_index() reads the LIVE LanceDB table, so it is a snapshot of the last
# reindex and cannot see a document written since. Measured the day it was built:
# Opus's session-057 journal named two task ids on disk at 15:00 UTC while the
# index, last built 04:43 UTC, held only its title line. The index control called
# that corpus clean. The next reindex would have carried the ids in.
#
# So: scan the FILES the indexer would walk, not only the rows it has already
# stored. Uses the memory server's own _iter_files() rather than a reimplemented
# walk, because a duplicated exclusion list drifts from the one that counts.
# ---------------------------------------------------------------------------

MEMORY_SERVER = os.environ.get(
    "OPUS_MEMORY_SERVER",
    "D:/Vibecode/docker-mcp-server/opus-memory-server.py")


WIDE_EXT = {".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".py", ".sh", ".bat", ".ps1"}


def _wide_walk(mod):
    """Every file under the indexer's roots, minus its DIRECTORY exclusions only.

    Reuses `mod.EXCLUDE_DIR_PARTS` and `mod._excluded_verdict` so the two stay in step —
    if `harness/` ever stops being excluded from the index, this stops excluding it too,
    and that is the correct coupling. What it does NOT reuse is `EXCLUDE_FILE_NAMES` or
    the prose-only extension set, which are decisions about what is worth INDEXING and
    have nothing to do with what is worth AUDITING.
    """
    roots = [(mod.EXOCORTEX_ROOT, False), (mod.ARCHIVE_ROOT, True)] + \
            [(r, False) for r in mod.EXTRA_ROOTS]
    out = []
    for root, is_archive in roots:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dl = str(dirpath).replace("\\", "/")
            verdict = mod._excluded_verdict(dl)
            if verdict == "prune":
                dirnames[:] = []
                continue
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in WIDE_EXT:
                    out.append((__import__("pathlib").Path(dirpath) / fn, is_archive))
    return out


def check_disk(ids):
    """One violation per FILE UNDER AN INDEXED ROOT naming a holdout task id.

    Fails CLOSED, same as check_index: if the server module will not import, the
    seal is reported unverified rather than intact.

    THE WALK IS WIDER THAN THE INDEX'S, DELIBERATELY (Kestrel, 2026-09-14).

    This used `_iter_files()` — the indexer's own walk — and therefore inherited the
    indexer's blind spots. `EXCLUDE_FILE_NAMES` skips `todo.md`, `claude.md` and
    `inbox_status.md`, so a holdout identifier written into any of those was invisible to
    BOTH halves of this seal while sitting under an indexed root. That is not a thought
    experiment: my own `Kestrel/.claude/Todo.md` named a live id twice, and this check
    reported "no indexable file names any of 8 holdout task ids" — true, and not the
    question the standing rule asks. The rule is about the ROOT, not about indexability.

    An instrument must be able to see what its subject cannot, or it is the subject
    wearing a different name.

    So: the indexer's ROOTS and DIRECTORY exclusions are reused — `harness/` in
    particular must stay excluded, because that is where holdout material legitimately
    lives — while the file-name exclusions are ignored and the extension set is widened
    to the formats people actually write notes and config in.
    """
    problems = []
    if not ids:
        return problems
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_oms", MEMORY_SERVER)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_oms"] = mod
        spec.loader.exec_module(mod)
        walk = _wide_walk(mod)
    except Exception as e:
        problems.append("disk UNVERIFIED -- could not load %s (%s: %s)"
                        % (MEMORY_SERVER, type(e).__name__, e))
        return problems

    hits = {}
    canary = 0
    for path, _is_archive in walk:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            # FAILS CLOSED: a file this scan cannot read is a file whose holdout
            # ids it cannot see. Skipping silently made the disk half's coverage a
            # number nobody could check.
            problems.append("UNVERIFIED -- %s could not be read (%s), so it was not "
                            "scanned for holdout ids" % (path, type(exc).__name__))
            continue
        if "holdout" in text.lower():
            canary += 1
        found = set(i for i in ids if i in text)
        if found:
            hits[str(path)] = found

    if canary == 0:
        problems.append("disk UNVERIFIED -- positive control failed: 'holdout' appears "
                        "in none of the %d indexable files, so this scan reads nothing"
                        % len(walk))
        return problems

    print("  disk              %d indexable file(s) scanned, positive control OK "
          "(%d mention 'holdout')" % (len(walk), canary))
    for p in sorted(hits):
        problems.append("%s names holdout task ids ON DISK: %s"
                        % (p, " ".join(sorted(hits[p]))))
    if not hits:
        print("  disk              no indexable file names any of %d holdout task ids"
              % len(ids))
    return problems


def main() -> int:
    global DEEP
    args = [a for a in sys.argv[1:] if a != "--deep"]
    DEEP = "--deep" in sys.argv[1:]
    containers = args or DEFAULT_CONTAINERS
    _check_holdout_dir()
    hashes = holdout_hashes()

    print(f"Holdout seal check — {len(hashes)} holdout file(s) at harness/holdout/")
    if not hashes:
        print("  NOTE: the holdout tree is empty. The path checks still run, but the")
        print("  content check has nothing to compare against yet. This gate exists")
        print("  BEFORE the content so the content can never land unguarded.")

    problems = []
    for c in containers:
        problems.extend(check(c, hashes))

    ids = holdout_task_ids()
    print()
    print("Holdout pattern: from %s (sha8 %s) -- compare with the running server's "
          "/version holdout_pattern_sha8" % (_PATTERN_SOURCE, _PATTERN_SHA8))
    print("Index audited:   %s (from %s)" % (LANCE_DB, _DB_SOURCE))
    print("Index control -- %d DECLARED holdout task id(s) must appear in no indexed "
          "document" % len(ids))
    if _UNDECLARED_IDS:
        print("  note              %d identifier-shaped token(s) appear in the config "
              "but are NOT declared tasks: %s" % (len(_UNDECLARED_IDS),
                                                  " ".join(sorted(set(_UNDECLARED_IDS)))))
        print("                    treated as retired and NOT audited as live. If any of "
              "these is a live holdout, declare it in tasks[].id.")
    problems.extend(check_pattern_covers_config())
    problems.extend(check_index(ids))
    problems.extend(check_disk(ids))

    # Ignorance is counted, never hidden. Both lists are empty on a healthy run;
    # a non-empty one means a half of this seal could not do its job, which is not
    # the same as that half finding nothing.
    problems.extend(_HASH_FAULT)
    problems.extend(_TASK_ID_FAULT)
    problems.extend(_PATTERN_FAULT)
    problems.extend(_DB_FAULT)

    print()
    if problems:
        print(f"SEAL BROKEN — {len(problems)} violation(s):")
        for p in problems:
            print(f"  ! {p}")
        print("\nPool B is only worth what its seal is worth. A leaked holdout is not a")
        print("holdout: any 'it generalised' result measured against it is meaningless.")
        return 1
    print("SEAL INTACT — no holdout content reachable from any container,")
    print("and no indexed or indexable document names a holdout task id.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
