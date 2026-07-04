# BP-01 — Attention Router

**Source:** Field survey (EVT-006), Assessment (EVT-007)
**Blocks on:** nothing. Build this first.
**Owner:** [assign]
**Status:** draft — *[Deposited 2026-07-03. Per Opus's briefing: COMPLETE — Layer A + daily cadence live since 2026-06-14. Kept for the record and for Layer B decisions.]*

---

## Problem

The field survey's central finding: every problem in the agency was already
detected by the agents' own instruments — wiki drift, BST line-count deviation,
the audit-counter mismatch, V16's stalled scheduler. The failures are not in
the *capture*. They are in the *consumption path*. The alarms fire into logs
nobody reads in real time. In SCADA terms: the instruments work, but the alarms
are not annunciated to the master station. Jake is the master station, and right
now he has no annunciator panel.

## Goal

One daily (or on-demand) digest that aggregates every resident agent's anomalies
and cycle activity, sorted by severity, delivered somewhere Jake actually looks.
Nothing more. This is deliberately the smallest high-value build in the set.

## Non-goals

- Not a dashboard project. A dashboard is a place you have to *go*; an annunciator
  *comes to you*. Text digest first; a NERV-style dashboard can come later if wanted.
- Not auto-remediation. The router *reports*; humans and agents *act*.

## Inputs (what already exists to read)

| Source | Path (per survey) | Signal |
|--------|-------------------|--------|
| Vek journal | `v17:/a0/usr/workdir/self-improvement/journal.jsonl` | cycle activity, wiki integrity, regression monitor |
| Vek monitor log | `v17:/a0/usr/workdir/self-improvement/monitor.log` | 4h heartbeat |
| V16 journal | `v16:/a0/usr/workdir/self-improvement/journal.jsonl` | cycle closes |
| nifty_panini | `nifty:/a0/usr/workdir/workspace/self-improvement/journal.jsonl` | cycle activity |
| Container state | docker inspect / `docker-containers` MCP | running / exited / OOM, last-start |

## Architecture

```
[per-agent journals + monitor logs]      [docker state]
            |                                  |
            +--------------+-------------------+
                           v
                  +------------------+
                  |  router.py       |   reads all sources, normalizes to a
                  |  (one CPU script)|   common Anomaly record, scores severity
                  +--------+---------+
                           v
                  +------------------+
                  |  digest renderer |   severity-sorted markdown/HTML
                  +--------+---------+
                           v
              delivered where Jake looks:
              - markdown file in a known path he opens, AND/OR
              - a message via the bus (NATS later), AND/OR
              - email/push  [OPEN: pick the channel Jake actually checks]
```

## The Anomaly record (normalize everything to this)

```python
@dataclass
class Anomaly:
    ts: str            # ISO8601
    agent: str         # "vek" | "v16" | "nifty_panini" | "system"
    source: str        # "wiki_integrity" | "regression_monitor" | "scheduler" | "container"
    severity: int      # 1=info 2=notice 3=warning 4=critical (see scale below)
    summary: str       # one line, human-first
    detail: dict       # raw fields for drill-down
    suggested_action: str | None
```

### Severity scale (deterministic, not LLM-judged)

- **4 CRITICAL** — agent not running when it should be; scheduler dead; OOM kill;
  audit-counter contradiction (claims 0 modifications while code changed).
- **3 WARNING** — wiki integrity drift > N pages; regression deviation beyond
  threshold; cycle gap > expected interval (V16's 17-day silence would have been a 4).
- **2 NOTICE** — new TODOs appeared; single-page drift; routine but worth seeing.
- **1 INFO** — normal cycle closes, counts, deltas.

The digest shows 3–4 by default, folds 1–2 behind a summary line.

## The known catches this must surface on day one

These are the live anomalies from the survey; the router is correct when it
catches them without hand-tuning:
1. Vek wiki integrity: 9 missing pages, 32 drifts (index claims 0, pages hold 80–470 words).
2. Vek regression: BST 1702→1929, py 60→81, 40 new wiki TODOs.
3. Vek audit-counter contradiction: `modifications_since_last_audit: 0` while code grew. **This one is severity 4** — a monitor reporting "all clear" while the system changed is the most dangerous failure class.
4. V16 scheduler: last cycle May 24, container restarted, scheduler likely didn't survive. (Now intentionally paused — but the router must distinguish *intentionally paused* from *silently dead*. See [OPEN] below.)

## [OPEN] questions for the team

- **Delivery channel.** What does Jake actually check daily? File he opens, email,
  phone push, a pinned chat? Pick one; the digest is only as good as its landing.
- **Paused vs dead.** The router needs a way to know an agent is *intentionally*
  paused (don't alarm) vs *unintentionally* stopped (alarm at severity 4). Suggest
  a `state/agent_intent.json` the operator sets — `{"vek": "active", "v16": "paused", ...}` —
  so pause is explicit and the router respects it. This also becomes the
  attention-router's own consumption-path discipline.

## Build steps

1. Write `router.py` (CPU, no LLM) reading the five sources above into `Anomaly` records.
2. Implement the deterministic severity scale.
3. Implement the digest renderer (markdown first — reuse the SER-panel aesthetic from the residency record if HTML is wanted).
4. Wire delivery to the chosen channel.
5. Add `agent_intent.json` and the paused-vs-dead logic.
6. Schedule it (cron / systemd timer / a MAINTAIN cycle) — daily, plus on-demand.

## Acceptance gate

Run the router against the live agents. It is done when:
- All four known catches appear at the correct severity, unprompted.
- The audit-counter contradiction surfaces as severity 4.
- An intentionally-paused agent does **not** raise a false "dead" alarm.
- The digest lands in the chosen channel and Jake confirms he'll see it.

## Why this is first

Everything downstream — eval harness, calculator drawer, spine, pipeline —
produces more signals. Building those before the annunciator just buries the
new signals alongside the old ones. Fix the consumption path, then add capture.
