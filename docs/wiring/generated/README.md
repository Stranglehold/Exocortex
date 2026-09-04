# Generated Wiring Map

**Generated, not written.** Fable's proposal, 2026-09-03: the wiring diagram should be
a measurement of the container, not a description of it. The hand-written
`../exocortex_wiring_and_logic.html` drifted from the system for four months because a
document has no way to notice the thing it describes has moved.

## Regenerate

```bash
docker cp scan_container.py agent-zero-v2:/tmp/scan_container.py
docker cp scan_webui.py     agent-zero-v2:/tmp/scan_webui.py     # web UI section
docker exec agent-zero-v2 sh -c 'cd /tmp && /opt/venv-a0/bin/python3 scan_container.py' > wiring.json
python render_wiring.py          # -> wiring_map.html
```

Both scanners are read-only and run inside the container. `cd /tmp` matters — that is how
`scan_container.py` finds `scan_webui.py` on `sys.path`. If `scan_webui.py` is absent the
scan still runs and the `webui` key carries an `error` string instead; the renderer then
emits no web UI section rather than failing. Point it at `VekV2` instead to produce the
other half of a parity diff.

On Windows/Git Bash, prefix docker commands with `MSYS_NO_PATHCONV=1` or `/opt/...` and
`/tmp/...` get rewritten to Windows paths.

## What it maps

242 extensions across 46 hooks as of 2026-09-03 — **75 ours, 167 Agent Zero core**.
Per extension: hook, load order, owner, purpose (first docstring line), state keys
written and read, referenced paths that fail to resolve, and whether it can be
observed at all.

**Web UI** (`scan_webui.py`, contributed by Fable 2026-09-03): 75 extension points —
49 HTML `<x-extension>`, 21 JS `callJsExtensions`, 5 provider-only folders — of which 32
have a provider and 43 are empty. Plus 39 plugins shipping `<plugin>/webui/*` parts, CSS
custom properties defined vs read, JS weight, and the message-window behaviour constants.

On its first integrated run it found a real defect: `_memory` ships
`extensions/webui/_sidebar-quick-actions-main-start/memory-entry.html`, but the actual
point is `sidebar-quick-actions-main-start` — no underscore, and nothing in `/a0` consumes
the underscored id. It is the only underscore-prefixed webui extension directory in the
install, so it is a typo upstream rather than a disable convention. Bound honestly: the
scan proves no consumer exists for that id, not that the fragment fails to paint.

## Read the observability column first

- `●` emits on the happy path — its silence is meaningful
- `!` prints only inside `except` — silence means healthy
- `·` **zero stdout prints — structurally invisible to `docker logs`**

180 of 242 are in that last category. For them, "silent" and "never fired" cannot be
distinguished. Conflating those two produced a wrong extension survey on 2026-09-01.

## Limits of this instrument

State keys reached through module constants resolve only when the constant is a plain
string literal in the same file. `_recall_memories_task` appears in the severed list and
is demonstrably read by `_91_recall_wait.py`. **Treat that list as candidates to check,
never a verdict.**

This is stated on the page itself deliberately. Six instruments built in this codebase
during the week of 2026-09-01 each reported a clean result because their null case was
indistinguishable from health — a missing inbox root reporting "no unread", a path audit
reporting "0 missing" by construction. A generated map that hid its own blind spots
would reproduce the exact failure it exists to prevent.
