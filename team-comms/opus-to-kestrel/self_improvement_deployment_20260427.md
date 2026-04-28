# KESTREL — Self-Improvement Engine Deployment
## From: Opus — April 27, 2026
## Priority: Required before launching the loop

---

## New Files to Include in Container

The following files and directories need to be accessible inside the Agent Zero container at `/a0/usr/Exocortex/`:

### Self-Improvement Engine
```
self-improvement/
├── program.md              ← Agent's operating manual (THE critical file)
├── LAUNCH_GUIDE.md         ← Jake's launch instructions
├── backups/                ← Agent stores config backups here
└── checkpoints/            ← Agent writes periodic progress reports here
```

### Wiki Structure
```
wiki/
├── WIKI.md                 ← Schema defining page types and rules
├── index.md                ← Master index (all pages listed as TODO)
├── log.md                  ← Ingestion log
├── concepts/               ← Concept pages (empty, agent fills these)
├── components/             ← Component pages (empty, agent fills these)
├── research/               ← Research summary pages (empty, agent fills these)
├── decisions/              ← Decision records (empty, agent fills these)
└── incidents/              ← Incident records (empty, agent fills these)
```

### Specs (already in Exocortex, verify container has latest)
```
specs/
├── TRAJECTORY_TO_SKILL_SPEC.md         ← NEW
├── EXOCORTEX_WIKI_SPEC.md              ← NEW
├── RECURSIVE_SELF_IMPROVEMENT_ENGINE.md ← NEW
└── (all existing specs)
```

### Research Reports (already in Exocortex, verify container has latest)
```
research/
├── HERMES_AGENT_ANALYSIS.md            ← NEW
├── KARPATHY_LLM_WIKI_ANALYSIS.md       ← NEW
├── GEPA_SELF_EVOLUTION_ANALYSIS.md      ← NEW
├── INTEGRATION_ROADMAP_SYNTHESIS.md     ← NEW
├── SELF_OPTIMIZING_INFERENCE.md         ← NEW
└── (any existing research files)
```

## Container Write Permissions

The agent needs write access to:
- `/a0/usr/Exocortex/wiki/` (all subdirectories)
- `/a0/usr/Exocortex/self-improvement/backups/`
- `/a0/usr/Exocortex/self-improvement/checkpoints/`
- `/a0/usr/workdir/self-improvement/` (journal, working files)
- `/a0/usr/skills/auto-generated/` (skill creation)

These should already be writable under `/a0/usr/` but verify.

## No Code Changes Required

The self-improvement loop operates entirely through:
- File creation (wiki pages, skills, journal entries, checkpoints)
- Config modification (with backup/rollback)
- MCP tool calls (ArXiv, DuckDuckGo, Wikipedia, etc.)

No extension source code changes. No Agent Zero core changes. The action boundary prevents the agent from modifying .py files.

## Verification

After deployment, the agent should be able to:
```bash
cat /a0/usr/Exocortex/self-improvement/program.md  # Should show the operating manual
ls /a0/usr/Exocortex/wiki/                         # Should show WIKI.md, index.md, subdirectories
ls /a0/usr/Exocortex/research/                     # Should show 5 research reports
ls /a0/usr/Exocortex/specs/                        # Should show all design specs including 3 new ones
```

— Opus
