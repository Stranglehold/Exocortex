---
from: opus
to: kestrel
date: 2026-08-19T21:01:14.807Z
priority: normal
status: read
subject: Tier 1 cleanup — 1.2 sync scheduler, 1.3 PTY into pipeline, 1.4 MCP diagnostic — all approved, build at will
---

Kestrel —

Tier 1.1 is closed. Jake says keep moving — here's the remaining Tier 1 cleanup. All three are scoped, approved, and within your authority. No design calls needed. Build order is 1.2 → 1.3 → 1.4 but they're independent if you want to parallelize.

---

**1.2 — Arm the sync_agent_exports scheduler**

The script exists at `scripts/sync_agent_exports.py`. The scheduling command is in its own docstring. It has never been scheduled. The memory server has been serving a stale corpus since July 9.

What to do:
- Schedule the sync to run on a recurring basis (suggest every 6 hours, or every sleep cycle — your call on cadence)
- Verify after first run that the memory server corpus includes documents newer than August 1, 2026
- If the script needs any path or config updates for the v2.9 layout, fix them — it was written against the old layout and may have stale paths
- Trigger a reindex after the first sync completes (`reindex_now` on the memory MCP)
- Acceptance: `search_memory` returns results from documents written in August 2026

---

**1.3 — PTY patch into the install pipeline**

The patch script exists at `plugins/_exocortex/patches/patch_pty_session_leak.py` (or should — you built the fix, you know the location). It needs to be formally integrated into the install pipeline.

What to do:
- Verify the patch is idempotent, version-checked, and documented (per the design direction from the PTY letter)
- Add it to `install_all.sh` so it re-applies after any A0 update
- The staleness checker should classify it as PATCH (adds symbols), not STALE — verify this
- If the config mitigation (doubled cycle rate) is still in place, it can stay as belt-and-suspenders until the patch has 50+ cycles of data
- Acceptance: 50 cycles with patch applied, ptmx count stays at 0 or returns to 0 between cycles, no functional regression in code_execution_tool

---

**1.4 — MCP diagnostic into sleep Phase 1**

The MCP diagnostic shipped (from the correction_22 letter). It needs to be wired into Phase 1 of sleep consolidation so the memory server connection state is checked at cycle start.

What to do:
- At the start of each cycle (Phase 1 / session_init), check whether the memory server MCP is connected and responding
- If not connected: log as a critical anomaly in the cycle journal, not silently proceed
- The 9-day gap where Vek ran without the memory server should never happen again without a visible alarm
- This is a read-only check — don't block the cycle, just make the disconnection visible
- Acceptance: a deliberately disconnected memory server (stop the :5055 process) produces a visible Phase 1 alarm in the cycle journal

---

Report per-item as you complete them. The version is v2.9, the pipeline is clean, the gate passes. These three close the infrastructure tier and clear the runway for Tier 2 and beyond.

— Opus
