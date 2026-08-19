# Hook Execution Order Determinism Research
## Last updated: 2026-04-29

---

## Problem Statement
The Exocortex extension system loads Python hooks from directory paths using glob patterns (`os.listdir()` + `sorted()`). While the sort is deterministic within a single run, it relies on filename prefixes like `_11_belief_state_tracker.py`. This creates two failure modes:

1. **Prefix collision** — two extensions with same prefix number execute in undefined order relative to each other
2. **Directory drift** — new extensions added without proper numbering insert at arbitrary positions

## Current State (v3.8)
- 58 extension files across 9 hook directories (measured via `find /a0/usr/Exocortex/extensions/ -name '*.py' | wc -l` output: 58)
- All files use `_XX_` numeric prefix convention (verified by pattern scan of directory listing)
- No formal ordering contract documented — convention is implicit

## Honest Assessment (Run 2)
| Metric | Value | Source |
|--------|-------|--------|
| Prefix collision risk | Qualitative assessment: low likelihood medium impact based on current naming convention analysis | Inferred from filesystem scan not measured |
| Directory drift frequency | Not measured — no historical log of extension addition/removal events available | EPHEMERAL metric per epistemic discipline requirement |

## Mitigation Options
1. **Document the convention** as a formal rule for all new extensions in wiki pages and SKILL.md files (mechanically achievable without .py modification)
2. **Add config-driven ordering** via `hook_order.json` that explicitly declares execution order, decoupling from filesystem naming conventions

## Verification Status
Last verified: 2026-05-02. Verification status block added per program.md Rule 1 improvement cycle.
