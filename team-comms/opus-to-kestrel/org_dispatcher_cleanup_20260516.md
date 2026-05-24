# ORG DISPATCHER DUAL-PATH FIX
## From: Opus — May 16, 2026
## To: Kestrel
## Priority: Quick cleanup — 5 minutes

---

## Issue

`_12_org_dispatcher.py` exists at two canonical paths on v16 with different md5 hashes. The loader picks the first by sort order, which is fragile — if either copy changes, the behavior silently shifts.

## Action

1. Diff the two copies:
```bash
docker exec intelligent_villani diff \
  <path_1>/_12_org_dispatcher.py \
  <path_2>/_12_org_dispatcher.py
```

2. Determine which is correct (likely the most recent or the one matching the repo intent)

3. Keep the correct copy at ONE canonical path. Remove the other.

4. Run the audit tool:
```bash
docker exec intelligent_villani python3 /a0/usr/Exocortex/scripts/audit_extensions.py
```

5. Confirm 0 dead, 0 unexpected divergences.

6. Repeat on v17 if the same duplication exists there.

— Opus
