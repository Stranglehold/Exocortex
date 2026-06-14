#!/usr/bin/env python3
"""
Attention Router (BP-01) — the alarms must annunciate.

The Exocortex agents emit signals all day (cycle outcomes, integrity checks,
sleep-consolidation findings, anti-patterns). Almost none of them reach Jake.
The field survey's core finding: the consumption gap moved up a layer — to the
human. Every other workstream produces signals; none help if they land in an
unread log.

This is the first reader. It aggregates each agent's signals across a time
window, classifies them by severity, and delivers ONE digest into Jake's team
inbox — the channel he actually checks.

Layer A (this file): read-only aggregation of the persisted cycle journal,
which is the richest signal we have (it carries priority / status /
integrity_issues per cycle). No running code is modified.

Layer B (follow-up): persist the currently-ephemeral alarms — supervisor loop
events, wiki-integrity stdout, epistemic-integrity fabrication verdicts — which
today decay in-memory or on stdout before any digest can see them. Those sinks
get added to the agents' extensions, then this router reads them too.

Design rules (per the build-plan meta-rules):
  - Verify against running code: reads the LIVE journal path, confirmed
    appended-to (not the stale /a0/usr/Exocortex copy).
  - Every capture has a consumption path: delivery is into inbox/jake/.
  - Deterministic classification — no LLM calls, no inference from prose.
  - Explicit defaults; graceful degradation if a container or file is missing.

Usage:
  python attention_router.py                  # last 24h, deliver to inbox
  python attention_router.py --hours 240      # wider window
  python attention_router.py --since-cycles 30  # last N cycles/agent (idle-safe)
  python attention_router.py --stdout         # print only, do not deliver
  python attention_router.py --dry-run        # print the inbox file it WOULD write
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

# ── Configuration (explicit defaults; optional JSON override beside this file) ──

DEFAULT_CONFIG = {
    "enabled": True,
    "agents": [
        {"name": "v16", "container": "exocortex_v16",
         "journal": "/a0/usr/workdir/workspace/self-improvement/journal.jsonl"},
        {"name": "v17", "container": "exocortex_v17",
         "journal": "/a0/usr/workdir/workspace/self-improvement/journal.jsonl"},
    ],
    "window_hours": 24,
    "inbox_jake_dir": r"D:\Vibecode\Agent-Zero\Exocortex\team-comms\inbox\jake",
    "from": "attention-router",
    "activity_max_chars": 240,
    # Routine cycles are counted, not itemized, to keep the digest scannable.
    "routine_examples": 0,
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "attention_router_config.json")


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
                user = json.load(fh)
            cfg.update(user)
    except Exception as exc:  # graceful degradation — defaults still work
        print(f"[attention-router] config load failed, using defaults: {exc}",
              file=sys.stderr)
    return cfg


# ── Reading the live journal off each container ──

def read_journal(container: str, path: str) -> list[dict]:
    """docker exec cat the journal; return parsed entries (skip bad lines)."""
    try:
        out = subprocess.run(
            ["docker", "exec", container, "cat", path],
            capture_output=True, text=True, timeout=30,
        )
    except Exception as exc:
        print(f"[attention-router] {container}: docker exec failed: {exc}",
              file=sys.stderr)
        return []
    if out.returncode != 0:
        # Container down or file absent — not fatal, just no signals here.
        print(f"[attention-router] {container}: journal unavailable "
              f"(rc={out.returncode})", file=sys.stderr)
        return []
    entries = []
    for line in out.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def parse_ts(entry: dict):
    ts = entry.get("timestamp")
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


# ── Deterministic severity classification ──

OK_STATUSES = {"completed", "complete", "ok", "success"}


def classify(entry: dict) -> str:
    """Return 'high' | 'notable' | 'routine' from structured fields only.

    Note on 'priority': the agents tag ~80% of substantive research cycles
    'notable' as their own default, so that field is NOT a reliable attention
    signal — keying NOTABLE on it just re-lists the feed. We only trust
    priority=='urgent' (rare, agent-flagged) for HIGH. NOTABLE is reserved for
    the signals that mean the agent noticed a problem about ITSELF —
    sleep-consolidation findings (anti-patterns, dedup, promotions) and
    capability changes (skills captured).
    """
    status = str(entry.get("status", "")).lower()
    priority = str(entry.get("priority", "")).lower()
    integrity = entry.get("integrity_issues", 0) or 0

    if integrity > 0 or priority == "urgent" or (status and status not in OK_STATUSES):
        return "high"

    if ((entry.get("sleep_findings", 0) or 0) > 0
            or (entry.get("skills_captured", 0) or 0) > 0):
        return "notable"

    return "routine"


def reason(entry: dict) -> str:
    """Short why-it-matters tag for high/notable lines."""
    bits = []
    integ = entry.get("integrity_issues", 0) or 0
    status = str(entry.get("status", "")).lower()
    priority = str(entry.get("priority", "")).lower()
    if integ > 0:
        bits.append(f"integrity_issues={integ}")
    if status and status not in OK_STATUSES:
        bits.append(f"status={status}")
    if priority == "urgent":
        bits.append("priority=urgent")
    if (entry.get("sleep_findings", 0) or 0) > 0:
        bits.append(f"sleep_findings={entry['sleep_findings']}")
    if (entry.get("skills_captured", 0) or 0) > 0:
        bits.append(f"skills_captured={entry['skills_captured']}")
    return ", ".join(bits) if bits else "flagged"


# ── Digest composition ──

def trunc(text: str, n: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def cycle_label(agent: str, e: dict) -> str:
    ts = parse_ts(e)
    when = ts.strftime("%m-%d %H:%M") if ts else "??"
    return f"{agent} · cycle {e.get('cycle_number','?')} · {e.get('cycle_type','?')} · {when}"


def build_digest(per_agent: dict, window_desc: str, amax: int):
    """per_agent: {agent_name: {'in_window': [entries], 'all': [entries]}}"""
    high, notable = [], []
    summary_rows = []
    routine_lines = []
    total_high = total_notable = 0

    for agent, data in per_agent.items():
        win = data["in_window"]
        counts = {"high": 0, "notable": 0, "routine": 0}
        type_counts = {}
        integ_sum = 0
        latest_routine = None
        for e in win:
            sev = classify(e)
            counts[sev] += 1
            integ_sum += (e.get("integrity_issues", 0) or 0)
            if sev == "high":
                high.append((agent, e))
            elif sev == "notable":
                notable.append((agent, e))
            else:
                ct = str(e.get("cycle_type", "?")).upper()
                type_counts[ct] = type_counts.get(ct, 0) + 1
                latest_routine = e
        total_high += counts["high"]
        total_notable += counts["notable"]

        # Idle / last-seen
        last_ts = None
        if data["all"]:
            last_ts = parse_ts(data["all"][-1])
        last_str = last_ts.strftime("%Y-%m-%d %H:%M UTC") if last_ts else "never"
        idle_h = (datetime.now(timezone.utc) - last_ts).total_seconds() / 3600 \
            if last_ts else None
        idle_flag = f" · idle {idle_h:.0f}h" if idle_h and idle_h > 36 else ""
        summary_rows.append(
            f"| {agent} | {len(win)} | {counts['high']} | {counts['notable']} "
            f"| {counts['routine']} | {integ_sum} | {last_str}{idle_flag} |"
        )

        if counts["routine"]:
            breakdown = ", ".join(f"{n} {t}" for t, n in
                                  sorted(type_counts.items(), key=lambda x: -x[1]))
            line = f"- **{agent}:** {counts['routine']} routine ({breakdown})"
            if latest_routine is not None:
                line += f" — latest: {trunc(latest_routine.get('activity',''), 140)}"
            routine_lines.append(line)

    # Sort high/notable newest first
    def keyts(item):
        return parse_ts(item[1]) or datetime.min.replace(tzinfo=timezone.utc)
    high.sort(key=keyts, reverse=True)
    notable.sort(key=keyts, reverse=True)

    lines = []
    lines.append(f"**Window:** {window_desc}  ")
    lines.append(f"**Agents:** {', '.join(per_agent.keys())}")
    lines.append("")

    if not high and not notable:
        lines.append("✅ **Nothing needs your attention.** No high or notable "
                     "signals in window. Per-agent activity below.")
        lines.append("")
    else:
        lines.append(f"### 🔴 Needs attention ({len(high)})")
        if high:
            for agent, e in high:
                lines.append(f"- **{cycle_label(agent, e)}** — _{reason(e)}_")
                lines.append(f"  {trunc(e.get('activity',''), amax)}")
        else:
            lines.append("- none")
        lines.append("")
        lines.append(f"### 🟡 Notable ({len(notable)})")
        if notable:
            for agent, e in notable:
                lines.append(f"- **{cycle_label(agent, e)}** — _{reason(e)}_")
                lines.append(f"  {trunc(e.get('activity',''), amax)}")
        else:
            lines.append("- none")
        lines.append("")

    lines.append("### ⚪ Per-agent summary")
    lines.append("")
    lines.append("| agent | cycles | high | notable | routine | integ_issues | last cycle |")
    lines.append("|-------|-------:|-----:|--------:|--------:|-------------:|------------|")
    lines.extend(summary_rows)
    lines.append("")
    if routine_lines:
        lines.append("**Routine activity** (research cycles, not itemized):")
        lines.extend(routine_lines)
        lines.append("")
    lines.append("---")
    lines.append("_Attention Router (BP-01), Layer A. Reads the live cycle "
                 "journal across all agents and routes anomalies by severity. "
                 "Supervisor-loop, wiki-integrity, and epistemic-integrity "
                 "alarms are not yet persisted (Layer B) and so are not here._")

    body = "\n".join(lines)

    if total_high:
        prio = "urgent"
    elif total_notable:
        prio = "normal"
    else:
        prio = "fyi"

    n_agents = len(per_agent)
    subject = (f"Daily digest — {total_high} need attention, "
               f"{total_notable} notable across {n_agents} agents")
    return subject, body, prio


# ── Delivery into Jake's inbox ──

def slugify(text: str) -> str:
    out = []
    for ch in text.lower():
        out.append(ch if ch.isalnum() else "-")
    s = "".join(out)
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")[:50]


def deliver_to_inbox(subject: str, body: str, priority: str, cfg: dict,
                     dry_run: bool) -> str:
    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H-%M")
    sender = cfg["from"]
    filename = f"{date}_{time}_from-{sender}_{slugify(subject)}.md"
    content = (
        "---\n"
        f"from: {sender}\n"
        "to: jake\n"
        f"date: {now.isoformat()}\n"
        f"priority: {priority}\n"
        "status: unread\n"
        f"subject: {subject}\n"
        "---\n\n"
        f"{body}\n"
    )
    dest_dir = cfg["inbox_jake_dir"]
    dest = os.path.join(dest_dir, filename)
    if dry_run:
        print(f"--- would write: {dest} ---\n{content}")
        return dest
    os.makedirs(dest_dir, exist_ok=True)
    # MUST be LF, not CRLF: the inbox-server frontmatter regex (/^---\n.../) only
    # matches LF. On Windows, default newline translation writes CRLF, which makes
    # the message parse with empty metadata and vanish from check_inbox. Force LF.
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    return dest


# ── Main ──

def main():
    ap = argparse.ArgumentParser(description="Attention Router (BP-01)")
    ap.add_argument("--hours", type=float, default=None,
                    help="window size in hours (default: config window_hours)")
    ap.add_argument("--since-cycles", type=int, default=None,
                    help="instead of a time window, take the last N cycles per "
                         "agent (useful when engines are idle)")
    ap.add_argument("--stdout", action="store_true",
                    help="print digest to stdout, do not deliver")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the inbox file that would be written")
    args = ap.parse_args()

    # Console may be cp1252 (Windows); the digest contains emoji. Keep delivered
    # files utf-8 regardless, but make stdout printing non-fatal.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    cfg = load_config()
    if not cfg.get("enabled", True):
        print("[attention-router] disabled in config; exiting.")
        return 0

    hours = args.hours if args.hours is not None else cfg["window_hours"]
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    per_agent = {}
    for agent in cfg["agents"]:
        name = agent["name"]
        entries = read_journal(agent["container"], agent["journal"])
        entries = [e for e in entries if parse_ts(e) is not None]
        entries.sort(key=lambda e: parse_ts(e))
        if args.since_cycles is not None:
            in_window = entries[-args.since_cycles:]
            window_desc = f"last {args.since_cycles} cycles per agent"
        else:
            in_window = [e for e in entries if parse_ts(e) >= since]
            window_desc = (f"last {hours:g}h "
                           f"({since.strftime('%Y-%m-%d %H:%M')} → "
                           f"{now.strftime('%Y-%m-%d %H:%M')} UTC)")
        per_agent[name] = {"in_window": in_window, "all": entries}

    subject, body, priority = build_digest(per_agent, window_desc,
                                            cfg["activity_max_chars"])

    if args.stdout:
        print(f"SUBJECT: {subject}\nPRIORITY: {priority}\n\n{body}")
        return 0

    dest = deliver_to_inbox(subject, body, priority, cfg, args.dry_run)
    if not args.dry_run:
        print(f"[attention-router] delivered ({priority}): {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
