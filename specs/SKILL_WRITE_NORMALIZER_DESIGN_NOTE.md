# Skill-Write Normalizer — Design Note

**Author:** Kestrel — 2026-06-21
**Status:** Built, staged. NOT deployed (hold until the agent finishes its current skill investigation).
**Hook:** `tool_execute_after` (`_34_skill_write_normalizer.py`)
**Motivated by:** A self-improvement agent authoring a skill it then could not see.

---

## The Incident

On 2026-06-21 the self-improvement agent (v16), after studying a repo Jake showed it, authored a `financial-services` meta-skill at `/a0/skills/financial-services/SKILL.md`. It wrote it **readme-style**:

```
# financial-services
Meta-skill wrapping Anthropic's financial-services reference repository...
**Source:** /a0/usr/workdir/financial-services ...
---
## Load Protocol ...
```

A0's discovery (`helpers.skills.split_frontmatter`) requires the YAML frontmatter fence at **byte 0** of the file. This file opens with `# financial-services`, so it has no frontmatter — `skill_from_markdown` returns `None` and the skill is **silently dropped from discovery**. The agent built a capability for itself and was structurally blind to it. An out-of-band audit confirmed 66/67 skills visible; this was the one invisible, and it was the newest and most-wanted.

This is the deterministic-scaffolding thesis in miniature: relying on the model to remember "frontmatter must be byte 0" is *behavioral*, and it failed precisely on the artifact the agent cared about most.

## The Real Gap: Latency, Not Coverage

A deterministic repair already exists. `scripts/normalize_skills.py:normalize_root(apply=True)` fixes invalid SKILL.md frontmatter — **including the "no top frontmatter / readme-style" case** (it derives `name` from the directory and `description` from the body's first prose line, preserving the body). `self-improvement/integrity_check.py` invokes it as a self-heal sweep during **MAINTAIN** cycles.

So the financial-services skill *would* eventually heal — at the next MAINTAIN cycle. The gap is **latency**: between authoring a skill and the next MAINTAIN, the skill is invisible. An agent that authors a skill in an EXPLORE/BUILD cycle and tries to use it in the next cycle cannot, until maintenance catches up.

## What This Does

A thin **write-time trigger** for the existing repair:

1. Fires on `tool_execute_after` for file-writing tools (`code_execution_tool`, `text_editor`).
2. Cheap gate: any SKILL.md under the skill roots written in the last `_RECENT_SEC` (180s)? (rglob + mtime; skips hidden dirs.) If none → near-zero work, return.
3. If yes → import and call `normalize_root(root, apply=True)` — the **same** function MAINTAIN uses.
4. Log `[SKILL-NORMALIZE]` with the repaired skill names.

Result: a freshly-authored invalid skill is repaired before the agent's next turn — it sees its own creation on the very next discovery pass, instead of waiting for maintenance.

## What This Does NOT Do

- **Does not duplicate the repair logic.** All name/description derivation, validate-first idempotency, body preservation, and hidden-dir skipping live in `normalize_root`. This extension is only the trigger.
- **Does not block writes.** Unlike `_16_py_write_guard` (which blocks `.py` writes), skill writes are *wanted* — this lets them happen, then ensures validity.
- **Does not rewrite valid skills.** `normalize_root` validates each file first (`validate_skill_md`) and only touches invalid frontmatter; clean skills are untouched. Idempotent.
- **Does not touch the body.** Only the frontmatter block is regenerated; the agent's prose/instructions are preserved verbatim.
- **Does not call an LLM.** Pure Python, deterministic.
- **Does not replace the MAINTAIN sweep.** Maintenance-time normalization stays as the backstop for anything written outside the recent window or via paths this trigger doesn't watch.

## Layering

Skill-frontmatter integrity is now defense-in-depth across the skill lifecycle:

| Layer | When | Mechanism |
|-------|------|-----------|
| `_45`/`_31` failure-lesson capture | write-time (captured lessons) | emits valid frontmatter directly |
| **`_34` skill-write normalizer (this)** | **write-time (agent-authored skills)** | **runs `normalize_root` on recent writes** |
| `integrity_check.py` MAINTAIN sweep | maintenance-time | runs `normalize_root` over all skills |
| `install_all.sh` | deploy-time | validates/normalizes on install |

`_34` fills the previously-missing cell: **write-time enforcement for skills the agent free-authors** (not via the capture pipeline).

## Config

`/a0/usr/Exocortex/config.json`:
```json
{ "skill_normalizer": { "enabled": true } }
```
Defaults to enabled if the section is missing. Per-container (set on v16/v17 independently).

## Testing Criteria

1. Author a SKILL.md readme-style (`# title` + prose, no frontmatter) under `/a0/usr/skills/<name>/`, then run any `code_execution_tool` call. Assert: `[SKILL-NORMALIZE]` logs the fix, and `validate_skill_md` now returns no errors (skill discoverable).
2. Author a SKILL.md with valid frontmatter, run a write tool. Assert: no rewrite (file mtime/content unchanged) — idempotent.
3. Non-write tool call (e.g., `search_engine`). Assert: extension returns immediately, no scan.
4. No recent SKILL.md write. Assert: cheap gate returns, `normalize_root` not called.
5. `normalize_skills.py` import fails (path moved). Assert: graceful passthrough, no error raised into the tool call.

## Known Limitations / Future Optimization

- The recent-write gate rglobs the skill roots each write-tool call. Cost is a few ms (filename glob over ~200 files); acceptable. If it ever matters, prune hidden dirs during the walk or track the last-written SKILL.md path from the tool args.
- Detection is mtime-based (180s window). A skill written and then not followed by any write-tool call within the window falls back to the MAINTAIN sweep — acceptable, since the agent almost always continues tool activity after authoring.

---

*"The format is enforced, not remembered." — the gate that makes a self-authored skill visible to the self that authored it.*
