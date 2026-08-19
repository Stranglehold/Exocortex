---
name: "extract-and-adapt"
description: "Use this skill when given an external reference — a GitHub repo, arxiv paper, API documentation, framework, or existing tool — and asked to build something Exocortex-native from it. Extracts patterns and methodology from the source, maps them to Agent Zero's tool surface, and produces a native artifact (skill, tool, extension, spec, design note) that follows Exocortex conventions. Never executes or copies external code verbatim — adapts patterns only. Triggers: 'build X based on Y', 'model X on Y', 'adapt X for our stack', 'extract the pattern from X and build it', 'create a skill/tool/spec based on this'."
version: "1.0.0"
author: "Kestrel"
tags: ["adaptation", "pattern-extraction", "skill-building", "tool-building", "knowledge-transfer"]
trigger_patterns:
  - "build a skill based on"
  - "model it on"
  - "adapt this for our stack"
  - "extract the pattern from"
  - "build something like"
  - "create a tool based on"
  - "turn this into a skill"
---

# Extract and Adapt

## Purpose

This skill takes an external reference — a GitHub repo, arxiv paper, API docs, existing framework,
or any external system — and produces an Exocortex-native artifact adapted for Agent Zero's tool
surface. It is the knowledge transfer methodology for the project.

**Core principle:** Read and adapt, never import and run. External code is a pattern source, not
an execution target. Intelligence transfers through understanding. Code stays native.

**Security rationale:** Every tool running inside the Docker container is an attack surface.
Verbatim external code brings undisclosed dependencies, unknown side effects, and supply chain
exposure. Adapted native code is auditable, sovereign, and fits exactly what it needs to fit.

## When to Use

Use this skill when:
- Given a GitHub repo and asked to build something like it for Exocortex
- Given a paper or design document and asked to implement its approach
- Given an API or framework and asked to wrap it as an Agent Zero tool
- Asked to create a skill, tool, extension, or spec modeled on an external source
- Extracting a methodology from any external system to make it locally executable

Do NOT use for:
- Tasks where the output type is undefined ("make something based on this") — clarify the target first
- Directly running or installing external code — this skill adapts, it does not execute external sources
- Cases where the source is already Exocortex-native — read it directly instead

## Security Rules — Non-Negotiable

1. **Never execute external code.** Read it to understand the pattern. Write your own implementation.
2. **Never `pip install` or `npm install` packages from external sources** to support the adapted artifact.
   If a capability requires an external package, note it as a dependency and flag it for review.
3. **Never `git clone` and `import`.** Clone only to read. Do not add the clone to any Python path.
4. **Flag all network dependencies.** If the source makes outbound calls to external services,
   note them explicitly. Prefer local or intra-container equivalents where they exist.
5. **Read the code, not just the README.** READMEs describe aspirations. Code describes reality.
   The gap between them is where vulnerabilities and false assumptions live.

---

## Phase 0: Classify the Task

Before doing anything else, establish two things:

**What is the source?**
- GitHub repository → read the actual code files
- arxiv / academic paper → read the methodology section, not the abstract
- API documentation → read the endpoint specs and authentication model
- Existing skill/tool → read the implementation directly
- Framework or library → read the core abstractions and call patterns

**What is the target output type?**
- `skill` → SKILL.md at `/a0/usr/skills/{name}/SKILL.md`
- `tool` → Python Tool subclass at `/a0/usr/plugins/exocortex/tools/{name}.py`
- `extension` → Python Extension subclass at `/a0/usr/agents/agent0/extensions/python/{hook}/{name}.py`
- `spec` → Markdown spec at `/a0/usr/Exocortex/specs/{NAME}_SPEC_L3.md`
- `design-note` → Markdown design note at `/a0/usr/Exocortex/specs/{NAME}_DESIGN_NOTE.md`

If either is unclear, ask one clarifying question before proceeding. Do not start extraction
against an undefined target.

---

## Phase 1: Convention Grounding

Before reading the external source, read the closest existing Exocortex example of the
target output type. This grounds the output in established conventions.

**Convention sources by target type:**

| Target | Read first |
|--------|-----------|
| `skill` | `/a0/usr/skills/design-buildplan/SKILL.md` |
| `tool` | `/a0/usr/plugins/exocortex/tools/stack_status.py` |
| `extension` | `/a0/usr/agents/agent0/extensions/python/before_main_llm_call/_11_belief_state_tracker.py` |
| `spec` | `/a0/usr/Exocortex/specs/HEDGE_PATTERN_SPEC_L3.md` |
| `design-note` | `/a0/usr/Exocortex/specs/ADVERSARIAL_INPUT_LAYER_DESIGN_NOTE.md` |

Read the convention source with `text_editor:read`. Note:
- The frontmatter / header format
- The section structure (what sections exist, in what order)
- The level of detail expected per section
- How Agent Zero tools are referenced (by name, with JSON examples, etc.)
- The tone and vocabulary (declarative instructions, not narrative)

Do not start reading the external source until this step is complete.

---

## Phase 2: Source Extraction

Read the external reference to extract its substance. This is a read-only, analysis-only phase.
No writing, no executing, no installing.

### 2a. Map the source structure

```python
# code_execution_tool — if source is a GitHub repo, list its structure
import subprocess
result = subprocess.run(
    ['find', '/tmp/source_clone', '-type', 'f', '-not', '-path', '*/.git/*'],
    capture_output=True, text=True
)
print(result.stdout)
```

Or for a URL-based source, use `document_query` or `browser_agent` to fetch the content.
For a local file or already-downloaded document, use `text_editor:read`.

### 2b. Extract what matters

For each relevant section of the source, answer:

```
EXTRACTION NOTES:
Source: [file/section/URL]
Core capability: [what this does in one sentence]
Approach: [how it does it — the method, not the implementation]
Agent Zero mapping:
  - [source capability] → [A0 tool/pattern equivalent]
  - [source capability] → [A0 tool/pattern equivalent]
Dependencies flagged: [any external packages, services, APIs it requires]
What to drop: [capabilities that don't translate or aren't needed]
What to add: [Exocortex-specific additions the source doesn't have]
```

Write these notes to a staging file:

```python
# code_execution_tool
import os
os.makedirs('/a0/usr/workdir', exist_ok=True)
with open('/a0/usr/workdir/extraction_notes.md', 'w') as f:
    f.write(extraction_notes_content)
print("Extraction notes saved.")
```

### 2c. Validate the mapping

Before writing anything, review the extraction notes and confirm:
- Every core capability has an Agent Zero equivalent or is explicitly dropped
- No external dependencies are silently assumed
- The target output will be self-contained within the container

If the mapping has gaps (capabilities with no A0 equivalent), note them as
`[NEEDS NATIVE IMPLEMENTATION]` — these may require new tools or extensions to support fully.

---

## Phase 3: Draft the Adapted Artifact

Write the adapted output using `code_execution_tool` with Python's `open()` — not
`text_editor:write`. This avoids JSON string truncation for large outputs.

```python
# code_execution_tool
import os

output_path = '/a0/usr/skills/{name}/SKILL.md'  # or appropriate target path
os.makedirs(os.path.dirname(output_path), exist_ok=True)

content = '''
[full artifact content here — follow the convention format from Phase 1]
'''

with open(output_path, 'w') as f:
    f.write(content)

print(f"Written: {output_path}")
print(f"Size: {len(content)} chars, {content.count(chr(10))} lines")
```

**Drafting rules:**
- Follow the section structure from the convention source exactly
- Use Agent Zero tool names, not the source's tool names
- Write in imperative instructions ("Use `search_engine` to..."), not in narrative
- For each phase/step from the source, map it to a concrete A0 tool call with a JSON example
- Include a "What this does NOT do" section — this is mandatory. Boundaries prevent scope creep.
- If the source had security considerations, translate them to Exocortex equivalents

**For large artifacts, write in sections:**

If the full content exceeds ~300 lines, write it in two or more Python blocks,
appending each section:

```python
# code_execution_tool — append Phase 3+ content
with open(output_path, 'a') as f:
    f.write(phase_3_onwards_content)
print(f"Appended. New size: {os.path.getsize(output_path)} bytes")
```

---

## Phase 4: Gap Analysis and Dependency Audit

After writing the draft, review it against the extraction notes.

```python
# code_execution_tool
with open('/a0/usr/workdir/extraction_notes.md') as f:
    notes = f.read()

with open(output_path) as f:
    artifact = f.read()

# Check all extracted capabilities appear in the artifact
import re
needs_impl = re.findall(r'\[NEEDS NATIVE IMPLEMENTATION\].*', notes)
if needs_impl:
    print("Capabilities requiring native implementation:")
    for n in needs_impl:
        print(f"  - {n}")
else:
    print("All capabilities mapped.")

# Check for any external package references that slipped in
suspicious = re.findall(r'pip install|import requests|import openai|npm install', artifact)
if suspicious:
    print(f"WARNING: External dependencies found: {suspicious}")
else:
    print("No external dependencies detected.")
```

Document any gaps in the artifact as a `## Known Gaps` section at the end.

---

## Phase 5: Verification

Confirm the artifact is deployable before reporting completion.

**For skills:**
```bash
# code_execution_tool — verify skill structure
ls -la /a0/usr/skills/{name}/
head -20 /a0/usr/skills/{name}/SKILL.md
```

**For Python tools/extensions:**
```bash
# code_execution_tool — syntax check
/opt/venv-a0/bin/python3 -m py_compile /path/to/file.py && echo "SYNTAX OK"
```

**For all output types:**
- Confirm the frontmatter (name, description, version, author, tags) is complete
- Confirm the file exists at the correct path
- Confirm the output type matches the target from Phase 0

---

## Phase 6: Report

Report to the user with:

```
Artifact: {output type} — {name}
Path: {path}
Size: {lines} lines / {bytes} bytes
Source: {what was adapted from}

Mapping summary:
- {N} source capabilities mapped to A0 equivalents
- {M} capabilities dropped (reason: {reason})
- {P} capabilities flagged for native implementation

Dependencies: {none / list of flagged dependencies}
Known gaps: {none / list from gap analysis}

To use: {how to invoke — e.g., "Load with skills_tool:load {name}"}
```

---

## What This Skill Does NOT Do

- Does not execute external code. Ever.
- Does not install packages from external sources.
- Does not clone repos to import them — only to read them.
- Does not produce artifacts that depend on external services without flagging them.
- Does not copy source code verbatim — only adapted native implementations.
- Does not work without a defined target output type — clarify before starting.

---

## Example Invocations

**Skill from a GitHub repo:**
> "Build an Exocortex skill based on the Hermes research-paper-writing workflow.
> Adapt for our Agent Zero tool surface. Output at /a0/usr/skills/research-paper-writing/SKILL.md.
> Follow the design-buildplan format."

**Tool from API documentation:**
> "Build an Agent Zero tool that wraps the Semantic Scholar API.
> Model it on the academic-research skill's approach.
> The tool should live at /a0/usr/plugins/exocortex/tools/semantic_scholar.py."

**Spec from a paper:**
> "Build an Exocortex L3 spec for the GEPA self-improvement loop described in this paper.
> Adapt it for our BST → skill pipeline. Follow the L3-spec-writing format."

**Extension from an existing pattern:**
> "Build a new BST enrichment domain for social media narrative analysis.
> Model the signal patterns on how the investigation domain is structured.
> Output as an update to the BST domain config."
