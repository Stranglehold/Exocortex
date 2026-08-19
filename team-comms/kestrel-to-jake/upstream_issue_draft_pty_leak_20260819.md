# Draft upstream issue — A0 PTY/shell session leak

**For Jake to file (or approve me to file) at https://github.com/agent0ai/agent-zero/issues.**
I have not posted it. Filing is outward-facing and carries our name, so it is your call.

**Prior-art check done 2026-08-19** — no existing issue covers this. The nearest is
[#1575 "Docker deployment can hit EMFILE under normal multi-tool use due to low default
nofile limit"](https://github.com/agent0ai/agent-zero/issues/1575) (closed 2026-05-03),
which raised the fd ceiling. That delays this symptom without addressing it, and our
deadlock was not fd exhaustion — see "Why this is not #1575" below.

Upstream has already shipped adjacent work in this area (`is_terminated()` /
`get_exit_code()`, lazy recreation of terminated sessions, and "best-effort destructors
for local and SSH sessions"). The report below is specifically that **the destructor
approach cannot reclaim these sessions**, and explains why.

---

## Title

PTY master + shell process leak: one per AgentContext, never reclaimed, ends in a worker-pool deadlock

## Environment

- Agent Zero **v2.9** (`agent0ai/agent-zero:latest`), Docker, Linux container
- Observed on two independent containers, twice (2026-08-14, 2026-08-18)
- File: `plugins/_code_execution/helpers/tty_session.py`

## Summary

Every `AgentContext` that runs `code_execution` allocates a PTY master fd and a child
shell via `asyncio.create_subprocess_shell`. Nothing ever calls `TTYSession.close()` for
it, so both leak — exactly one per context, monotonically, for the life of the process.

`TTYSession.close()` itself is correct. The bug is that it is never invoked.

## What operators experience

Field-measured on a container running autonomous cycles (each cycle creates a fresh
context):

- 30 cycles / 17 hours → **38 PTY handles, ~360 threads**, then **total deadlock**
- Every HTTP request queues forever. `GET /health` *from inside the container* never
  answers — A0 serves from a bounded worker pool, and once that pool is consumed by
  blocked session threads there is no server left to respond. A browser refresh cannot
  help.
- Recovery required `docker restart`. After restart: threads 343 → 17, zombies 61 → 3,
  fds 236 → 6.

Comparison against a healthy twin container of identical uptime made it unambiguous:

```
                 leaking      healthy
threads             343          157
futex-blocked       333          148
zombie [sh]          61            3     (3 is the normal baseline)
open fds            223           56
```

A single healthy user turn leaks **nothing** — measured, pidfds 0 afterwards. So this is
not inherent to normal operation; it is specifically that sessions are never released.

## Reproduction

Three `POST /api/api_message` calls, each in a **new chat/context**, each running a
trivial `code_execution` command (`echo hi`):

```
baseline        ptmx=0  pidfds=0  threads=64
after msg #1    ptmx=1  pidfds=1  threads=84
after msg #2    ptmx=2  pidfds=2  threads=100
after msg #3    ptmx=3  pidfds=3  threads=101
```

Count handles with:

```sh
docker exec <container> sh -c 'P=$(pgrep -f run_ui.py | head -1);
  for f in /proc/$P/fd/*; do readlink $f; done | grep -c ptmx'
```

It is 1:1 and it never comes back down. Reusing an *existing* context does not add a
handle — the leak is per context, not per command.

## Root cause, and why A0's built-in cleanup does not catch it

1. `code_execution_tool` creates a `TTYSession` and stores it on the agent
   (`agent.set_data("_cet_state", ...)`).
2. The agent is held by its `AgentContext`.
3. `AgentContext` objects are not destroyed — they stay in the registry for the life of
   the process. Deleting the chat does not release the session (see "Dead ends" below).
4. So the session is strongly referenced forever, and `close()` is never reached.

### Why the best-effort destructor does not save it

`TTYSession.__del__` is the only fallback, and it cannot work here for two independent
reasons:

- **It never runs.** `__del__` fires on garbage collection, and the object is strongly
  reachable from the context registry for the process lifetime. There is nothing to
  collect.
- **When it does run, it fails silently.** It calls `nest_asyncio.apply()` and then
  `asyncio.run(self.close())`. `asyncio.run()` raises `RuntimeError` when a loop is
  already running, and the surrounding `except Exception: pass` discards it. No log line,
  no warning. Three days of logs never mentioned the leak once — the failure has no voice.

That silent-except is worth fixing on its own merits regardless of the leak.

## Why this is not #1575

#1575 raised the container's `nofile` limit. That pushes out the point at which fd
exhaustion bites, but the leak is unbounded in context count, so it still arrives. More
importantly, what actually killed the process here was **not** the fd ceiling — it was
the bounded worker pool being consumed by blocked session threads. Raising `nofile`
would not have prevented either observed outage.

## Dead ends (verified, so nobody repeats them)

- `POST /api/api_terminate_chat` returns `{"success": true}` and releases nothing; the
  handle count is unchanged. Chat deletion does not close the shell.
- `code_execution_tool` with `reset` gives no net reduction — `prepare_state` immediately
  recreates the session.

## Suggested directions (upstream's call)

1. **Close on context teardown** — the structurally correct fix: release `_cet_state`
   sessions when a context is terminated or removed from the registry.
2. **Idle reaper** — close sessions idle beyond a threshold. This is safe today without
   any other change, because `code_execution_tool` already handles a dead session:
   `if self.state.shells[session].session.is_terminated(): await self.prepare_state(..., reset=True, ...)`,
   and `is_terminated()` returns True in exactly the state `close()` leaves behind. A
   reaped shell is transparently rebuilt on next use.
3. **At minimum, make the `__del__` failure log.** A cleanup path that fails silently is
   how this went unnoticed for three days.

## What we run locally

We mitigate with option 2: an idle reaper (600s idle, 120s sweep) applied by a small,
reversible, anchor-gated patch script that re-applies after every A0 update.

Measured over 50 concurrent sessions:

```
t+0       ptmx=50   50 sessions allocated, container still serving in 6ms
t+600s    ptmx=47   3 reaped   — only those past the idle threshold
t+723s    ptmx=0    50 reaped  — remainder on the next sweep
```

Log line: `closing idle shell (idle 600s >= 600s)`. The partial-then-complete shape is
the point — it reaps per session at the threshold rather than sweeping indiscriminately,
so an in-flight command is never interrupted. After a full reap, new sessions allocate
normally and `code_execution` still works in a context whose shell was reaped.

We would much rather delete that patch and run stock — happy to test any upstream fix.
