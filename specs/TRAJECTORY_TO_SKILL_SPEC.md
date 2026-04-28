# DESIGN SPEC: Trajectory-to-Skill Conversion
## Exocortex Build Spec — Informed by Hermes Agent Research
## Author: Opus — April 27, 2026
## For: Kestrel (implementation), Agent (field testing)
## References: research/HERMES_AGENT_ANALYSIS.md, research/INTEGRATION_ROADMAP_SYNTHESIS.md

---

## 1. The Problem

The Exocortex has 59 hand-authored skills. Each one was written by a human (Jake, Kestrel, or me) who identified a recurring pattern, formalized it into a SKILL.md file, and placed it in the skills directory. This process is slow, doesn't scale, and misses patterns that only the agent encounters during operation.

Hermes Agent ships with 118 bundled skills AND auto-generates more from successful task trajectories. After a task with 5+ tool calls completes successfully, a background process summarizes the trajectory into a reusable skill. Their claim: agents with 20+ self-created skills complete similar future research tasks 40% faster.

The Exocortex should do the same.

---

## 2. The Mechanism

### 2.1 When to Capture

A trajectory is captured when ALL of the following are true:

1. The task completed successfully (response tool called with substantive output)
2. The task involved 5+ tool calls (complex enough to be a reusable pattern)
3. The BST classified the task with confidence ≥ 2 signals (we know what domain it is)
4. No supervisor Tier 2+ intervention fired (the task didn't require surgery — the approach was clean)
5. The task is NOT a simple conversation, greeting, or meta-question

### 2.2 What to Capture

From the agent's execution history, extract:

```
{
  "domain": BST primary domain,
  "user_intent": first user message (summarized),
  "tool_sequence": [
    {"tool": "code_execution_tool", "runtime": "python", "purpose": "read config file"},
    {"tool": "code_execution_tool", "runtime": "terminal", "purpose": "install dependency"},
    {"tool": "code_execution_tool", "runtime": "python", "purpose": "parse and transform data"},
    {"tool": "response", "purpose": "deliver results"}
  ],
  "errors_encountered": [
    {"tool": "code_execution_tool", "error_class": "dependency", "resolution": "pip install X"}
  ],
  "total_turns": N,
  "total_tool_calls": M,
  "bst_domain": "coding",
  "bst_confidence": 0.87
}
```

### 2.3 How to Convert

The utility model summarizes the trajectory into SKILL.md format:

```markdown
---
name: {auto-generated-from-domain-and-intent}
description: {one-line summary of what this skill does}
domain: {BST domain}
auto_generated: true
generated_from: {session_id}
generated_at: {ISO timestamp}
version: 1
---

## When to Use

{Describe the task type this skill applies to, derived from user intent and BST domain}

## Procedure

{Step-by-step procedure derived from the tool sequence}

1. {First step — what tool to use, what to do}
2. {Second step}
3. ...

## Pitfalls

{Common errors encountered during the trajectory and how they were resolved}

- {Pitfall 1}: {Resolution}
- {Pitfall 2}: {Resolution}

## Verification

{How to verify the task completed successfully — derived from the response tool output}
```

### 2.4 Where to Store

Auto-generated skills go to `/a0/usr/skills/auto-generated/{skill-name}/SKILL.md`.

The `auto-generated` directory is separate from hand-authored skills. This provides:
- Clear provenance (auto vs hand-authored)
- Easy cleanup (delete the directory to remove all auto-generated skills)
- No risk of overwriting hand-authored skills

The skills are immediately discoverable by the existing `skills_tool:list` mechanism (same YAML frontmatter format, same directory structure).

---

## 3. The Extension

### 3.1 Hook and Priority

**Extension:** `_54_trajectory_capture.py`
**Hook:** `monologue_end`
**Priority:** After selective memorizer (`_52_`), before memory classifier (`_55_`)

This hook fires after the agent's response is complete, which is when we can evaluate whether the task was successful and complex enough to capture.

### 3.2 Detection Logic

```python
class TrajectoryCapture(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            # Check if response tool was just called (task complete)
            if not _response_just_fired(self.agent):
                return
            
            # Count tool calls in this task
            tool_calls = _count_task_tool_calls(self.agent)
            if tool_calls < MIN_TOOL_CALLS:
                return
            
            # Check BST confidence
            bst = _get_bst_state(self.agent)
            if not bst or bst.get("confidence", 0) < MIN_BST_CONFIDENCE:
                return
            
            # Check no supervisor surgery fired
            supervisor = _get_supervisor_state(self.agent)
            if supervisor and supervisor.get("loop_surgery_done"):
                return
            
            # All checks pass — capture trajectory
            trajectory = _extract_trajectory(self.agent)
            
            # Generate skill via utility model
            skill_content = await _generate_skill(self.agent, trajectory)
            
            if skill_content:
                _save_skill(skill_content, trajectory)
                self.agent.context.log.log(
                    type="info",
                    content=f"[TRAJECTORY] Captured skill: {trajectory['skill_name']}"
                )
        except Exception as e:
            try:
                self.agent.context.log.log(
                    type="warning",
                    content=f"[TRAJECTORY] Error (passthrough): {e}"
                )
            except Exception:
                pass
```

### 3.3 Constants

```python
MIN_TOOL_CALLS = 5          # Minimum tool calls for a "complex enough" task
MIN_BST_CONFIDENCE = 2      # Minimum BST signal count
MAX_TRAJECTORY_AGE = 50     # Only look back this many history entries
SKILL_OUTPUT_DIR = "/a0/usr/skills/auto-generated"
```

### 3.4 Utility Model Prompt

```python
SKILL_GENERATION_PROMPT = """You are a skill extraction system. Given an execution trajectory 
(a sequence of tool calls, their outcomes, and the final result), generate a reusable 
SKILL.md file that would help future agents complete similar tasks.

The skill should be:
- Specific enough to be useful (not "do coding tasks")
- General enough to apply beyond this exact task
- Focused on the PROCEDURE (what tools to use in what order)
- Honest about PITFALLS (what went wrong and how it was fixed)

TRAJECTORY:
Domain: {domain}
User intent: {user_intent}
Tool sequence:
{tool_sequence_formatted}

Errors encountered:
{errors_formatted}

Generate a SKILL.md file with YAML frontmatter (name, description, domain, auto_generated: true)
and sections: When to Use, Procedure, Pitfalls, Verification.

Output ONLY the SKILL.md content, no explanation."""
```

---

## 4. Quality Gate

### 4.1 Deduplication

Before saving a new auto-generated skill, check if a similar skill already exists:

1. Load existing skills from the auto-generated directory
2. Compare the new skill's domain + procedure against existing skills
3. If a skill with the same domain and >70% procedure overlap exists, UPDATE it instead of creating a new one (merge pitfalls, refine procedure)

```python
def _check_duplicate(new_skill: dict, existing_skills: list) -> Optional[str]:
    """Returns path to existing skill if duplicate found, None otherwise."""
    for skill in existing_skills:
        if skill["domain"] != new_skill["domain"]:
            continue
        overlap = _compute_procedure_overlap(new_skill["procedure"], skill["procedure"])
        if overlap > 0.7:
            return skill["path"]
    return None
```

### 4.2 Skill Pruning

Auto-generated skills should have a lifecycle:

- **Version 1:** Generated from first trajectory. Unverified.
- **Version 2+:** Updated by subsequent similar trajectories. Increasingly reliable.
- **Promoted:** After 3+ successful uses, move to `/a0/usr/skills/promoted/` (still auto-generated but validated by use)
- **Deprecated:** If the skill hasn't been referenced in 100+ sessions, mark as deprecated (don't delete — the agent might need it again)

Track usage in the skill's YAML frontmatter:

```yaml
usage_count: 0
last_used: null
promoted: false
```

### 4.3 Validation Against EI

The generated skill should not contain fabricated claims. Run the skill content through a lightweight EI check:
- Does it reference specific tools that actually exist?
- Does it reference file paths that were actually used in the trajectory?
- Are the pitfalls based on actual errors from the trajectory, not hypothetical ones?

If the EI check fails, log a warning but still save the skill (mark it as `ei_validated: false` in frontmatter).

---

## 5. Progressive Disclosure Integration

Auto-generated skills follow the same progressive disclosure pattern as all skills:

- **Level 0** (always in context): skill name + one-line description (~5 tokens)
- **Level 1** (on demand): full SKILL.md content loaded when agent calls `skill_view(name)`
- **Level 2** (on demand): specific reference files if the skill has attachments

This means auto-generated skills add minimal context overhead (~5 tokens per skill at Level 0). Even with 50 auto-generated skills, that's ~250 tokens — negligible.

---

## 6. Connection to GEPA

The trajectory capture is Phase 1 of the GEPA integration from the research roadmap:

- **Phase 1 (this spec):** Capture trajectories and generate skills. Pure data collection + conversion.
- **Phase 2 (future):** Offline reflection on accumulated trajectories to identify systemic patterns.
- **Phase 3 (future):** Automated skill evolution via GEPA — optimize skills against success metrics.

The trajectory data stored by this extension feeds directly into Phase 2 and 3. Even before GEPA integration, the raw trajectory data is valuable for manual analysis.

---

## 7. Example

### Input: Agent completes a file analysis task

```
Domain: analysis
User: "Analyze the Exocortex extension architecture. Which extensions have the highest coupling?"
Tool calls:
  1. code_execution_tool (terminal): find extensions -name '*.py' | sort
  2. code_execution_tool (python): read and parse all extension files
  3. code_execution_tool (python): extract import statements and shared keys
  4. code_execution_tool (python): compute coupling graph
  5. code_execution_tool (python): rank by coupling score
  6. response: deliver coupling analysis with ranked list
Errors: None
Supervisor: No intervention
```

### Output: Auto-generated skill

```markdown
---
name: extension-coupling-analysis
description: Analyze coupling between Python extensions by tracing shared data keys and imports
domain: analysis
auto_generated: true
generated_from: session_20260427_001
generated_at: 2026-04-27T18:30:00Z
version: 1
usage_count: 0
last_used: null
promoted: false
---

## When to Use

When asked to analyze coupling, dependencies, or architecture of a Python extension 
system where extensions communicate through shared agent attributes or data keys.

## Procedure

1. List all extension files with `find` to get the full inventory
2. Read and parse each file to extract:
   - Import statements (shared modules)
   - Agent attribute reads (getattr, get_data calls)
   - Agent attribute writes (setattr, set_data calls)
   - Shared constant keys between files
3. Build a coupling graph: nodes are extensions, edges are shared data keys
4. Rank extensions by total coupling score (in-degree + out-degree)
5. Identify the most-coupled data keys (which keys create the most connections)

## Pitfalls

- Extensions may use dynamic attribute access (getattr with variable names) 
  that static analysis can't catch
- Some coupling is intentional (BST writes, supervisor reads) — distinguish 
  architectural coupling from accidental coupling

## Verification

- The coupling graph should include all extensions found in step 1
- Each edge should reference a specific shared key or import
- The ranking should be consistent with manual inspection of 2-3 top-ranked extensions
```

---

## 8. Build Priority

This is a Phase 2 item from the integration roadmap — after instrumentation (trace capture, which the token counting partially provides) but before the wiki or GEPA integration.

**Dependencies:**
- Utility model must be available for skill generation (already is — Agent Zero has `call_utility_model`)
- Skills directory must be writable from inside the container (already is)
- `skills_tool:list` must discover skills in the `auto-generated` subdirectory (needs verification — the V16→V17 migration fix normalized frontmatter, so this should work)

**Effort estimate:** Medium. Core extension is ~200 lines. Utility model prompt needs iteration. Deduplication logic needs testing.

**Risk:** Low. The extension is purely additive — it doesn't modify existing behavior. If skill generation fails, it logs a warning and continues. Auto-generated skills are in a separate directory and can be deleted without affecting anything.

---

*Informed by Hermes Agent's closed learning loop. Adapted for the Exocortex's architecture, BST domain classification, and epistemic integrity layer.*
