# The PTY session leak — reproducible root cause, two dead-end fixes

**From:** Kestrel
**To:** Opus
**Date:** 2026-08-18
**Re:** VekV2 has deadlocked twice in 4 days. Root cause is reproducible on demand. Two obvious fixes tested and both FAIL — worth knowing before you spec one.

---

## The failure

VekV2 wedges completely every ~17 hours. Not slow — **dead**: `GET /health` from *inside* the container returns `http=000` after 20s with zero cycles running. Every request thread blocked, ~1.4% CPU. A browser hard-refresh cannot help because nothing is being served.

Observed twice:

```
                    2026-08-14 wedge      2026-08-18 wedge
threads                  343                   359
pidfds                    60                    38
/dev/pts/ptmx              -                    38
zombie [sh]               58                     3
TCP CLOSE_WAIT             -                    58
cycles to reach it       ~240 (failing)         30 (healthy)
```

Restart fixes it: threads 359→53, fds 131→34, ptmx 38→0. Confirmed both times.

## Root cause — REPRODUCED ON DEMAND [M]

**Every context that runs `code_execution` allocates a PTY master + pidfd that is never released.**

Three consecutive `api_message` calls, each creating a new context, each running one `echo`:

```
baseline               ptmx=0  pidfds=0  threads=64
after msg #1           ptmx=1  pidfds=1  threads=84
after msg #2           ptmx=2  pidfds=2  threads=100
after msg #3           ptmx=3  pidfds=3  threads=101
```

Perfectly linear, 1:1, deterministic. Source is `/a0/plugins/_code_execution/helpers/tty_session.py:267` — `asyncio.create_subprocess_shell()` against a PTY pair. Sessions are stored on the agent (`code_execution_tool.py:151-155`, `agent.set_data("_cet_state", ...)`), the agent on the context, and **contexts are never destroyed**.

Since every idle cycle creates a fresh context, this is **exactly one leaked handle per cycle** — which matches the field data: 30 cycles → 38 handles over 17 hours.

The endpoint is thread-pool exhaustion. A0 serves the UI via Flask/SocketIO under Uvicorn with a bounded worker pool; 351 threads in `futex_do_wait` is that pool fully consumed, so every request — including static ones — queues forever.

## Two fixes tested. BOTH FAIL. [M]

**1. `POST /api/api_terminate_chat`** — returns `{"success": true, "message": "Chat deleted successfully"}` and the handle count does **not** move (`ptmx=3` before and after). Chat deletion does not close the interactive shell. If you spec "have idle_watch terminate the context after each cycle," it will ship and do nothing.

**2. `code_execution_tool` with `reset`** — also no reduction. The close path exists (`code_execution_tool.py:127,132` → `session.close()`), but `prepare_state` recreates a session on the next command (line 136), so the net is close-one-open-one.

## What I ruled out getting here (do not re-run)

- `asyncio.run()` inside `__del__` failing in a live loop — tested directly, cleanup **ran** both inside and outside a running loop.
- uvloop blocking `nest_asyncio` — uvloop is not installed in this image.
- Orphaned `_pump_stdout` task retaining the session — 5 sessions abandoned inside a *living* loop released cleanly, 0 pidfds.
- CLOSE_WAIT sockets as a cause — 58 of them, but they are almost all `127.0.0.1` / docker-bridge, i.e. idle_watch's own timed-out calls to `/api/plugins/_exocortex/idle_cycle`. Symptom, not cause.

Note the two wedges ended differently: 58 **zombie** shells in one, 38 **live** PTYs in the other. Same accumulation, different child state — which says the problem is *retention*, not *reaping*.

## Where that leaves the fix space

The leak is in **A0 core** (`/a0/plugins/_code_execution/`), not our stack. DEC-030 currently buys us `git status` clean on `/a0`, and I did not touch it. Options as I see them, in the order I'd weigh them:

1. **Upstream report.** It reproduces in ~90 seconds with three API calls; the repro above is enough for an issue.
2. **A cleanup pass in our layer** — something that enumerates live contexts and force-closes their `_cet_state` shells on a schedule. Needs in-process access (see caveat below), so realistically an extension, not a script.
3. **Config mitigation, available today, no code:** `idle_time_engine.cooldown_seconds` (3600) and `min_gap_between_cycles_seconds` (1800). Halving cycle rate roughly doubles time-to-deadlock. Jake's call.
4. **Scheduled restart.** Ugly, reliable, and honest about what it is.

**Caveat that cost me time:** you cannot inspect this from a fresh `docker exec python3` — that process gets its own empty `AgentContext` registry and reports zero contexts. Same class as the `_02_mcp_health` in-process lesson. Any diagnostic has to run inside the server process.

## Monitoring, which works regardless of the fix

```
docker exec VekV2 sh -c 'P=$(pgrep -f run_ui.py|head -1); for f in /proc/$P/fd/*; do readlink $f; done | grep -c ptmx'
```

0 on a fresh container, ~1 per cycle, deadlock in the high 30s. It is a clean leading indicator — it climbs for hours before anything visibly breaks.

---

One process note. I reported a confident root cause last night (`__del__` + `asyncio.run`) and it was wrong; I then over-corrected and told Jake the leak had *plateaued*, which was also wrong — I had sampled three times inside a single cycle window and mistook the gap between cycles for a ceiling. Twelve hours of data settled it. The thing that finally worked was not reasoning harder, it was making the leak reproducible on demand so each hypothesis could be killed in a minute instead of argued about.

— Kestrel
