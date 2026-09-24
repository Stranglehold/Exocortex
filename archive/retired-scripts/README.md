# Archive: retired scripts

**`create_tool_stubs.py`** (2026-05-03) wrote 23 one-line tool stubs into `/a0/usr/agents/agent0/tools/`. Each stub
delegated to `/a0/usr/plugins/exocortex/tools/<file>.py`, a directory that no longer exists. Its only caller,
`scripts/install_exocortex_profile.sh`, was retired on 2026-08-19.

On Aporia's container, the 23 stubs it had left behind outranked the plugin in A0's tool lookup and failed on
every call. The plugin's `get_tool/end/_10_multi_tool_resolver` then rescued each name. On 2026-09-24 they were
moved off the container, together with four shadowing prompts, into `/a0/usr/_legacy_backup/agents-agent0-20260924/`
(host copy with md5s: `Kestrel/studies/2026-09-24-audit-backups/`). The script was retired here at the same time.
Audit: `Kestrel/studies/2026-09-24-exocortex-plugin-audit.md`, finding 5.
