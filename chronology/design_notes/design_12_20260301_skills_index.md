# Exocortex Project Skills

Procedural knowledge for recurring task types in Exocortex development sessions. These are not tool skills — they're workflow procedures that ensure consistency and quality across sessions.

Validated by SkillsBench (Li, Chen et al., 2026): curated procedural knowledge improves agent performance by 16.2pp. Focused Skills (2-3 modules) outperform comprehensive documentation. These skills are intentionally tight.

## Skill Index

### Development Workflow Skills

| Skill | File | Trigger |
|-------|------|---------|
| L3 Spec Writing | `SPEC_WRITING.md` | Designing new layers, components, or enhancements |
| Research Analysis | `RESEARCH_ANALYSIS.md` | Evaluating papers against the Exocortex thesis |
| Claude Code Prompt | `CLAUDE_CODE_PROMPT.md` | Translating specs to implementation briefs |
| Session Continuity | `SESSION_CONTINUITY.md` | Recovering context across compactions and sessions |
| Profile Analysis | `PROFILE_ANALYSIS.md` | Comparing model eval data and routing decisions |
| Documentation Sync | `DOCUMENTATION_SYNC.md` | Keeping README and specs consistent after changes |
| Debug & Diagnostics | `DEBUG_DIAGNOSTICS.md` | Extension not firing, silent failures, docker log analysis |
| Integration Assessment | `INTEGRATION_ASSESSMENT.md` | Evaluating external projects for Exocortex integration |
| Design Notes | `DESIGN_NOTES_SKILL.md` | Pre-spec exploration of architectural concepts with motivating incidents |
| Stress Test | `STRESS_TEST_SKILL.md` | Designing, running, and analyzing empirical stack validation |

### Architectural Pattern Skills

These skills encode transferable architectural patterns that emerged from the Exocortex project but apply beyond it. They are frameworks for thinking, not just procedures for building.

| Skill | File | Trigger |
|-------|------|---------|
| Irreversibility Gate | `irreversibility-gate.md` | Any action interacting with external systems, building agent pipelines with safety boundaries, reviewing action plans with potentially dangerous steps |
| Command Structure | `command-structure.md` | Multi-agent architecture design, subordinate agent spawning, task delegation, escalation protocol design, standing order management |
| Structural Analysis | `structural-analysis.md` | Complex system analysis, macro-economic assessment, feedback loop identification, structural vs cyclical classification, hidden dependency mapping |
| Cross-Instance Learning | `CROSS_INSTANCE_LEARNING.md` | Comparing parallel solutions to the same problem, carrying insights between collaboration contexts, extracting general vs. domain-specific patterns from independent approaches |

## Usage

Read the relevant skill BEFORE starting the task. Multiple skills may apply to a single session — a typical build session involves Spec Writing, then Claude Code Prompt, then Documentation Sync in sequence. A typical validation session involves Stress Test, then Design Notes if new issues are discovered.

The architectural pattern skills (irreversibility gate, command structure, structural analysis, cross-instance learning) cross-cut the development workflow skills. When building action boundaries, read both the Spec Writing skill and the Irreversibility Gate skill. When designing multi-agent coordination, read both Command Structure and the relevant spec. When comparing approaches from different collaborations or different agents, read both Cross-Instance Learning and the relevant domain skill (Integration Assessment for external tools, Structural Analysis for complex systems). Cross-Instance Learning provides the comparison methodology; the domain skill provides the evaluation framework.

## Design Principles

- **Procedure, not knowledge.** These describe HOW to do things, not WHAT things are. Factual knowledge lives in memory and specs.
- **Focused over comprehensive.** Each skill covers one task type with just enough structure to ensure consistency.
- **Anti-patterns are as important as procedures.** Knowing what NOT to do prevents the most common failure modes.
- **Evolving.** Skills should be updated when recurring mistakes are identified or when new patterns emerge from sessions.
- **Not everything should be a skill.** Some patterns lose their value when proceduralized. If a behavior depends on organic judgment, contextual sensitivity, or relational dynamics, it belongs in SOUL.md as orientation, not in a skill as procedure.
