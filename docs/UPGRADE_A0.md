# Agent-Zero Upgrade Plan & Runbook

*The plan for keeping Exocortex reproducible on a fresh clone and taking A0 upgrades
(especially mandatory security ones) without silently breaking — or silently reverting
A0's own fixes. Status: DRAFT for review, 2026-05-26.*

---

## Why this exists

Two concerns drive it:

1. **Reproducibility.** Someone clones this repo onto a fresh A0 container and it must
   not be broken. The hardening stack is verified against *one* A0 version; a fresh
   container that pulls a newer A0 is untested ground.
2. **Mandatory upgrades.** A0 ships security fixes (v1.14–v1.17 *all* carry
   security-relevant changes per the radar). We can't pin v1.13 forever. We need a
   repeatable, de-risked way to move up.

## The core insight — patches are a MERGE problem, not a copy problem

The stack is *additive* on the profile path (`/a0/usr/...`), which is exactly why
DEC-030 migrated it there: it survives A0 image rebuilds. **But** `patches/` is the
exception — those files **overwrite A0 core files** (`docker cp` over `/a0/...`). When
A0 changes one of those files in a new release and we re-run `install_all` against it,
our v1.13-based copy clobbers A0's new version — **reverting A0's change, including any
security fix that rode along.**

So every upgrade must treat each *deployed-as-overwrite* patch as a **3-way merge**:
`A0-old` (what our patch was built on) → `A0-new` (the release) → re-apply our delta.

### Patch deploy mechanisms (not all `patches/` files are overwrites)

A path under `patches/` can be deployed three ways — only the first is a merge risk:

| Mechanism | Example | Upgrade action |
|---|---|---|
| **Overwrite** (`docker cp` over `/a0/...`) | `helpers/extract_tools.py` | **RE-BASE** (3-way merge) |
| **Sed-injection** (adds a line to A0's file) | theme-editor → `/a0/webui/index.html` | Verify the injection anchor (e.g. `</body>`) still exists |
| **Unused / stale** (present but no installer deploys it) | `patches/webui/messages.js` | No action |

`check_a0_updates.py` flags *path correspondence*; it cannot tell these apart, so its
output is **candidates** — confirm each file's mechanism before acting.

---

## Current state (2026-05-26)

- **Pinned / tested:** A0 **v1.13** (commit 2613fac0) — see `./A0_VERSION`.
- **Latest upstream:** **v1.17** (repo moved `frdel/agent-zero` → `agent0ai/agent-zero`).
- **Behind by:** v1.14, v1.15, v1.16, v1.17 — **all security-flagged** (v1.15 = the XSS
  fix in chat markdown rendering; others mention sanitize/injection/RCE in notes).
- **Re-base set (verified tonight):** 4 deployed-as-overwrite patches that A0 changed —
  - `helpers/extract_tools.py` (v1.14)
  - `plugins/_memory/helpers/memory_consolidation.py` (v1.14, v1.16)
  - `plugins/_model_config/helpers/model_config.py` (v1.14, v1.16) ← the v1.16 preset deep-merge
  - `prompts/agent.system.main.communication.md` (v1.14)
- **Cleared false positives:** `webui/js/messages.js` (we don't deploy our `messages.js`;
  the XSS fix is therefore NOT at risk from us) and `webui/index.html` (sed-injection, not
  overwrite — A0's content is preserved).
- **Relevant new capability to evaluate (not blocking):** Host/BYO-Browser (v1.14) for the
  OSS ingestion + behavioral-humanization angle.

---

## The tooling (built 2026-05-26)

| Tool | Purpose |
|---|---|
| `./A0_VERSION` | Declares the tested A0 version. Single source of truth for the pin. |
| `install_all.sh` preflight | Reads the container's `git -C /a0 describe`, compares to `A0_VERSION`, **fails loud on mismatch** (override `--force`). `update.sh --force` forwards it. |
| `scripts/check_a0_updates.py` | Radar: pinned-vs-latest, security-keyword scan of release notes, and the patch-overlap candidate set (adjacent-tag compares beat the API's 300-file cap). Exit 0/1/2. |
| `scripts/contract_check.py` | Post-upgrade: inter-plugin seams (DB columns, cross-plugin imports, UI↔API keys). |
| `scripts/wiring_truth.py` | Post-upgrade: extensions load from profile path, LLM endpoints route + reachable, DB/FAISS intact, no collision residue. |
| `eval/bst_eval.py` + ST stress tests | Post-upgrade: functional smoke test. |

---

## Runbook — staged upgrade (v1.13 → vNext)

**Never upgrade v16/v17 (prod) first. Never blind-`install_all` onto a new A0.**

1. **Radar.** `python scripts/check_a0_updates.py`. Note newer releases, security flags,
   and the candidate re-base set.
2. **Read the release notes** for every version in the jump. Identify changes to A0
   internals the stack depends on: hook signatures, `get_paths()`, Memory API,
   `helpers.api.ApiHandler`, the Extension base class, the plugin loader, and the
   model-config / preset schema.
3. **Stage a fresh vNext test container** (pull `agent0ai/agent-zero:vNext`). Do not
   touch v16/v17.
4. **Resolve the re-base set.** For each candidate from step 1, confirm its deploy
   mechanism (table above). For each *overwrite*: diff `A0-old` vs `A0-new`, and 3-way
   merge our delta onto `A0-new` (so A0's fix is kept AND our behavior is kept). For
   *sed-injections*: confirm the anchor survives. For *unused*: ignore.
5. **Install onto the test container:** `bash install_all.sh --force` (force = we've
   done the merge deliberately).
6. **Validate (the gate):**
   - `wiring_truth.py` — all extensions/plugins load from the profile path; LLM endpoints
     resolve + reachable; DBs and FAISS intact; no `src` collision residue.
   - `contract_check.py` — HIGH: 0.
   - `eval/bst_eval.py` — classification accuracy holds.
   - One ST stress test + a few golden-path agent tasks by hand.
7. **Re-validate the patched files specifically** — exercise each re-based file's feature
   (tool parsing, model-config switching, memory consolidation, the communication prompt).
8. **Promote.** Bump `./A0_VERSION` to vNext (+ commit). Deploy to **v16**, validate again,
   then **v17**. Update this doc's "Current state" + the decision log.

### Rollback

The profile-path stack is additive and git-tracked; `patches/` re-bases are commits.
To roll back: restore the prior `A0_VERSION`, redeploy the prior commit's patches, and
(if the A0 image itself changed) restart on the prior `agent0ai/agent-zero:vPrev` tag.
Keep the prior A0 image tag until the new one is validated in prod.

---

## Open design decision (for review)

Right now each `patches/` file is a **full-file copy with no recorded A0 base**, so the
3-way merge in step 4 is done by eyeballing diffs. Two ways to make it mechanical:

- **(A) Record the base.** Store the `A0-old` version of each overwritten file beside the
  patch (or its commit SHA). Then the merge is a literal `git merge-file`. Low effort,
  immediate payoff.
- **(B) Patches as real diffs.** Convert overwrites from whole-file copies into unified
  diffs applied at install, which **fail loudly on conflict** against whatever A0 ships.
  Cleaner long-term, bigger change, and some files (prompts, model_config) may diverge
  enough that a diff is noisy.

Recommendation: **(A) now** (cheap, unblocks clean merges), consider (B) later for the
handful of high-churn core files. Either way, the re-base set is only ~4 files today —
tractable by hand for the v1.17 jump if we want to move before building (A).

---

## Recommended next move

The radar says security updates are pending, so this isn't indefinitely deferrable. But
the v1.13→v1.17 jump is a *deliberate, staged* exercise (the runbook above), not a thing
to do blind. Suggested order: **(1)** decide design (A) vs (B) for patch bases; **(2)**
run the staged upgrade on a fresh v1.17 test container; **(3)** validate with the harness;
**(4)** promote v16 → v17. The 4-file re-base set makes this very tractable.
