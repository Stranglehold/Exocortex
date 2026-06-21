---
name: "create-skill"
description: "Wizard for creating new Agent Zero skills. Guides users through creating well-structured SKILL.md files. Use when users want to create custom skills."
version: "2.2.0"
author: "Agent Zero Team"
tags: ["meta", "wizard", "creation", "tutorial", "skills"]
trigger_patterns:
  - "create skill"
  - "new skill"
  - "make skill"
  - "add skill"
  - "skill wizard"
  - "build skill"
---
# Create Skill Wizard

## DECISION GATE — Read before doing anything else

**If the user's message contains a skill name, purpose, or description of what the skill should do:**
→ BUILD IMMEDIATELY. Do not ask questions. Use the information provided and fill in any gaps with sensible defaults.
→ Go directly to BUILD STEPS below.

**If the user's message contains no skill details at all (e.g., only "create a skill"):**
→ Ask ONE consolidated question only (see SINGLE QUESTION below).
→ After receiving the answer, BUILD IMMEDIATELY. Do not ask follow-up questions.

---

## SINGLE QUESTION (only if no details provided)

Ask this exact question once:

"What should this skill do? Describe: (1) its purpose, (2) when the agent should use it, (3) what the output should look like."

Then build immediately from the answer. Do not ask for clarification.

---

## BUILD STEPS

Execute these steps in order using code_execution_tool. Do not ask questions between steps.

### Step 1 — Derive skill metadata from user input
From the user's description, determine:
- `skill-name`: lowercase, hyphens only, 1-3 words (e.g., "market-report", "code-review")
- `description`: one sentence — what it does and when to use it
- `success_criterion`: one testable sentence describing what success looks like
- `confidence`: calibrated band the skill reliably achieves its criterion (almost_certain | probable | even_chance | unlikely | remote — default `probable`)
- `tags`: 3-5 relevant keywords
- `trigger_patterns`: 3-5 phrases the user would say to invoke it

### Step 2 — Write the SKILL.md content

Skills are born in **capability-adaptive** format: two layers. The **Conditions**
section is always surfaced (the quality bar — WHAT and HOW GOOD). The **Approach
Guidance** section is scaffolding (HOW) that a capable model in FLOW can skip and
a struggling model in FRICTION/STAGNATION receives. Construct the SKILL.md using
this template:

```
---
name: "{skill-name}"
description: "{description}"
success_criterion: "{one testable sentence describing what this skill accomplishes}"
confidence: probable  # almost_certain | probable | even_chance | unlikely | remote
affects_surfacing: adaptive  # adaptive | always_full | conditions_only
tags: [{tags}]
trigger_patterns:
  - "{trigger1}"
  - "{trigger2}"
  - "{trigger3}"
---
# {Skill Title}

## Purpose
{What this skill does and the problem it solves}

## Conditions (always surfaced)
{Quality criteria that must be met regardless of model capability — WHAT must
happen and HOW GOOD it needs to be. Testable where possible. Always shown.}

## Approach Guidance (surfaced when FRICTION or below)
{Step-by-step scaffolding for HOW to meet the conditions. A model in FLOW skips
this and uses its own reasoning; a model hitting FRICTION/STAGNATION receives it.}

## Output Format
{What the final output should look like — format, structure, length}

## Example Triggers
- "{example user message 1}"
- "{example user message 2}"
```

- `success_criterion` — the pre-registered, testable claim of what the skill accomplishes (one sentence).
- `confidence` — calibrated estimate using Kent's WEP bands (almost_certain | probable | even_chance | unlikely | remote).
- `affects_surfacing` — how the affect layer gates this skill: `adaptive` (Conditions always, Approach Guidance on FRICTION/below), `always_full` (both always), `conditions_only` (never scaffold).

### Step 3 — Create the skill directory and file

Use code_execution_tool with runtime=python and code argument. Both fields are required.

```json
{
  "tool_name": "code_execution_tool",
  "tool_args": {
    "runtime": "python",
    "code": "import os\nskill_name = '{skill-name}'\nskill_dir = f'/a0/usr/skills/{skill_name}'\nos.makedirs(skill_dir, exist_ok=True)\ncontent = '''{full SKILL.md content}'''\nwith open(f'{skill_dir}/SKILL.md', 'w') as f:\n    f.write(content)\nprint(f'Created: {skill_dir}/SKILL.md')"
  }
}
```

CRITICAL: tool_args must contain exactly "runtime" and "code". Never use "script", "command", "cmd", or any other key name.

### Step 4 — Verify the file was written

```json
{
  "tool_name": "code_execution_tool",
  "tool_args": {
    "runtime": "terminal",
    "code": "cat /a0/usr/skills/{skill-name}/SKILL.md | head -20"
  }
}
```

### Step 5 — Load the skill

```json
{
  "tool_name": "skills_tool",
  "tool_args": {
    "method": "load",
    "skill_name": "{skill-name}"
  }
}
```

### Step 6 — Report to user
Confirm:
- Skill name and location
- Trigger patterns (phrases that will activate it)
- Any scripts or dependencies the skill requires to function

---

## SKILL.md Format Reference

```yaml
---
name: "skill-name"               # required: lowercase, hyphens only
description: "..."               # required: when/why to use this skill
success_criterion: "..."         # recommended: one testable sentence
confidence: probable             # recommended: WEP band (default probable)
affects_surfacing: adaptive      # recommended: adaptive | always_full | conditions_only
tags: ["cat1", "cat2"]           # optional
trigger_patterns:                # optional but recommended
  - "phrase that triggers"
---
```

The validator (`helpers/skills.py`) requires only `name` + `description` and
tolerates the additional fields — but keep the YAML well-formed (malformed
frontmatter makes a skill invisible to discovery).

## Required Fields
- `name`: unique identifier, lowercase, hyphens only
- `description`: when and why to use this skill (max 1024 chars)

## Capability-Adaptive Fields (recommended)
- `success_criterion`: testable claim of what the skill accomplishes
- `confidence`: calibrated WEP band the skill reliably hits its criterion
- `affects_surfacing`: how the affect layer gates the skill's Approach Guidance

## Skill Directory Rules
- All skills go in `/a0/usr/skills/{skill-name}/`
- The SKILL.md file must be at `/a0/usr/skills/{skill-name}/SKILL.md`
- Supporting scripts go in the same directory
- Never touch `/a0/requirements.txt` — add skill-specific pip installs inside skill scripts only
