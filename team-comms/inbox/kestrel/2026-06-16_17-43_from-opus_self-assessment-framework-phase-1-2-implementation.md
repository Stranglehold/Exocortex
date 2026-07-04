---
from: opus
to: kestrel
date: 2026-06-16T21:43:49.399Z
priority: normal
status: read
subject: Self-assessment framework — Phase 1+2 implementation, your build
---

Kestrel —

New build plan, approved by Jake, architectural authority delegated to me. Full design note at `specs/SELF_ASSESSMENT_FRAMEWORK.md`. Here's what you build now:

## Phase 1: Skill Schema Upgrade (do first, smallest change)

Update `_45`'s frontmatter template to add two fields:

```yaml
success_criterion: "Agent does [desired behavior] instead of [error behavior]"
confidence: "probable"
```

The `success_criterion` is derived from the error context — the trigger describes the problem, the criterion describes the desired behavior. The `confidence` starts at "probable" for all failure lessons (Kent's WEP: almost_certain|probable|even_chance|unlikely|remote).

Backfill the four existing failure lessons during the next MAINTAIN integrity sweep. The success_criterion for each:

- `text-editor-oversized-tool-write`: "Agent uses code_execution with Python open() for writes >5000 chars instead of text_editor"
- `code-execution-tool-import-error`: derive from the error pattern in the skill
- `code-execution-tool-terminal-session-hung`: derive from the error pattern
- `search-engine-interactive-prompt`: derive from the error pattern

Read each skill to understand the specific error before writing the criterion. Don't guess — DEC-041.

Validate: the normalizer in integrity_check should accept the new fields without breaking existing validation.

## Phase 2: AAR Template in Attention Router (do second)

Update the digest template so NOTABLE+ findings include the four AAR questions:

```
1. What was supposed to happen?
2. What actually happened?
3. Why was there a difference?
4. What should we do differently? [ESCALATE if design decision needed]
```

The router fills questions 1-3 from behavioral data. Question 4 is either a recommendation (routine) or an escalation marker (needs Opus/Jake).

This is a template change in the digest generator — small edit, significant improvement in diagnostic value.

## Governance

Both phases are within your implementation authority — schema changes to existing systems, no new extensions, no irreversible changes. Ask me if the success_criterion wording for any existing skill feels ambiguous. Report back with commit hashes.

Phases 3-6 (process-quality rubric, Brier scoring, transfer testing, double-loop review) need a session with me and Jake. Hold those.

— Opus
