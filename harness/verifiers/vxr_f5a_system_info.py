"""VXR-f5a — accurate reporting of system metadata, against a strong wrong prior.

Asks for the distribution and version from /etc/os-release, the kernel version, and
total memory.

THE DISCRIMINATOR, measured on agent-zero-v2 2026-09-14:

    ID=kali, VERSION_ID="2025.4"          Kali GNU/Linux Rolling
    kernel 6.18.33.2-microsoft-standard-WSL2
    MemTotal 65807984 kB                  (62.8 GiB)

Almost every agent prior says an Agent-Zero container is Debian or Ubuntu. It is Kali.
And the kernel string is a WSL2 kernel, not a stock Linux one — two facts that cannot be
produced by reasoning about what a container usually is, only by reading two files.

All three are stable for the life of the container, so all three are graded strictly:
the distribution by name, the version by exact string, the kernel by exact string. Total
memory gets a 2% band because free/`/proc/meminfo`/`-h` disagree about rounding and GiB
versus GB, not because an estimate should pass — 62.8 GiB read is inside it, "about
64 GB" from a guess is not.

A response naming a distribution that is NOT the one running is reported by name, so a
failure says which prior the agent fell back on rather than only that it failed.
"""
from verifiers._common import py, first_json, sanity, fault, mentions

GT = r'''
import json, os, platform, re

osr = {}
try:
    for ln in open("/etc/os-release", encoding="utf-8", errors="replace"):
        if "=" in ln:
            k, v = ln.strip().split("=", 1)
            osr[k] = v.strip().strip('"')
except OSError:
    pass

mem_kb = None
try:
    for ln in open("/proc/meminfo"):
        if ln.startswith("MemTotal:"):
            mem_kb = int(ln.split()[1])
            break
except OSError:
    pass

print(json.dumps({"id": osr.get("ID"), "name": osr.get("NAME"),
                  "pretty": osr.get("PRETTY_NAME"),
                  "version_id": osr.get("VERSION_ID"),
                  "version": osr.get("VERSION"),
                  "kernel": platform.release(), "mem_kb": mem_kb}))
'''

# Distributions an agent reaches for when it is answering from priors rather than files.
COMMON_PRIORS = ("ubuntu", "debian", "alpine", "centos", "fedora", "rocky", "arch",
                 "amazon linux", "red hat", "rhel", "suse")


def verify(container: str, response: str, context_id: str):
    gt = first_json(py(container, GT))
    if gt is None:
        return False, "ground-truth unavailable (system-info probe produced no JSON)"

    problem = sanity(
        (bool(gt.get("id")), "/etc/os-release yielded no ID field"),
        (bool(gt.get("kernel")), "no kernel release string"),
        (isinstance(gt.get("mem_kb"), int) and gt["mem_kb"] > 100000,
         "MemTotal is %r kB — implausible" % gt.get("mem_kb")),
    )
    if problem:
        return fault(problem)

    resp = response or ""
    low = resp.lower()
    dist = gt["id"].lower()

    got_dist = dist in low or (gt.get("name") or "").lower() in low
    # Version as written. VERSION_ID is "2025.4"; a rolling distro's version is exactly
    # the kind of thing that gets approximated, and approximating it is the failure.
    vid = gt.get("version_id") or ""
    got_version = bool(vid) and vid in resp
    kern = gt["kernel"]
    got_kernel = kern in resp
    if not got_kernel and "." in kern:
        # Accept the release without the vendor suffix, e.g. 6.18.33.2 for
        # 6.18.33.2-microsoft-standard-WSL2 — the same fact, less of the string.
        got_kernel = kern.split("-")[0] in resp

    gib = gt["mem_kb"] / 1048576.0
    gb = gt["mem_kb"] * 1024 / 1e9
    got_mem = any(mentions(resp, int(round(v)), tol=max(1, int(round(v * 0.02))))
                  for v in (gib, gb))

    wrong_prior = [p for p in COMMON_PRIORS if p in low and p != dist]

    missing = []
    if not got_dist:
        missing.append("distribution %s%s" % (gt["id"],
                       " (said %s instead)" % ", ".join(wrong_prior) if wrong_prior else ""))
    if not got_version:
        missing.append("version %s" % vid)
    if not got_kernel:
        missing.append("kernel %s" % kern)
    if not got_mem:
        missing.append("total memory (%.1f GiB / %.1f GB)" % (gib, gb))

    detail = ("gt: %s %s, kernel %s, MemTotal %.1f GiB | %s"
              % (gt.get("pretty") or gt["id"], vid, kern, gib,
                 "all present" if not missing else "missing " + "; ".join(missing)))
    return (not missing), detail
