---
from: opus
to: jake
date: 2026-09-11T14:59:35.594Z
priority: urgent
status: unread
subject: Pool B holdout compromised — ruling issued, re-authoring needed
---

Jake —

Kestrel found that all eight Pool B holdout scenarios are described in full in team inbox letters that have been indexed since the memory server was built. My own letter to Kestrel (Aug 20) — containing task IDs, descriptions, what each verifier checks, and the capability mapping — returns as the #1 search result at 0.9976 score. Kestrel's verifier validation reply is also indexed. 57 total matches.

The seal (`verify_holdout_seal.py`) checked for holdout paths and content hashes in the container. A description of the scenarios in correspondence is neither. The seal protected one door while the content sat in a room Aporia is instructed to search first (160 of 655 cycles).

**Ruling issued:**
1. No Pool B result is usable until resolved
2. The fix is a policy about where we discuss holdouts, not an index filter
3. Pool B needs re-authoring — capability categories transfer, specific scenarios/IDs do not
4. Third seal control: search each holdout ID in the index, require zero hits

**Build order impact:** The twenty-cycle baseline proceeds on Pool A only. Pool B re-authoring runs as a parallel track once we have communication discipline in place.

**Self-correction:** I designed the seal and then described the holdout content through the channel it didn't cover. Same structural gap pattern we've been finding.

This doesn't block the write-path fix, status-memory line, or admission — those don't depend on Pool B. It does mean the engine loop's COMPARE step uses Pool A only until new Pool B is ready.

Your two pending rulings (idle cycles to Kestrel, evaluation disclosure) are unaffected. — Opus
