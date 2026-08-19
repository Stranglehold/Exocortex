---
name: "research-paper-writing"
description: "End-to-end research paper writing workflow from literature review through submission preparation. Uses search_engine for discovery, code_execution_tool for verification/analysis, call_subordinate for parallel drafting and multi-reviewer self-review, text_editor for incremental writing, memory_save for tracking key decisions. Follows design-buildplan pattern with iterative refinement cycles."
version: "1.0.0"
author: "Agent Zero Framework"
tags: ["research", "academic", "writing", "literature-review", "publication"]
trigger_patterns:
  - "write a research paper on"
  - "draft an academic paper about"
  - "compose a scholarly article on"
  - "author a research article"
  - "publish findings on"
  - "literature review of"
---

# Research Paper Writing Skill

## Purpose

This skill orchestrates the complete research paper writing workflow from initial topic analysis through submission preparation. It adapts proven academic writing workflows for Agent Zero's tool surface, enabling iterative drafting, parallel section composition with `call_subordinate`, multi-perspective self-review, and systematic verification.

**Core Philosophy:** Research papers are built iteratively through cycles of discovery -> synthesis -> drafting -> refinement -> review. This skill provides the scaffolding for that process while maintaining traceability of all key decisions via `memory_save`.

## When to Use

Use this skill when:
- Writing an original research paper on a technical or academic topic
- Composing a literature review article
- Drafting a survey paper synthesizing existing work
- Preparing findings for publication in an academic venue
- Creating a comprehensive analysis report with citations

Do NOT use for:
- Single-section writing tasks ("write just the introduction")
- Simple blog posts or informal articles  
- Tasks explicitly scoped to one section only

## Output Artifacts

This skill produces several artifacts at `/a0/usr/workdir/papers/{paper_id}/`:
- `PAPER.md` — main paper content in Markdown
- `outline.md` — detailed outline with section structure
- `literature_review.md` — annotated bibliography and synthesis  
- `decisions.log` — key decisions tracked via memory_save outputs
- `reviews/` — self-review notes from multiple perspectives
- `references.bib` — BibTeX-formatted references

## Workflow Overview

```
Phase 0: Task Analysis -> Define scope, audience, venue requirements
Phase 1: Literature Review -> Discover and analyze relevant papers
Phase 2: Thesis & Outline -> Formulate thesis, create detailed outline
Phase 3: Draft Writing -> Parallel section drafting with subordinates
Phase 4: Integration -> Combine sections, ensure coherence
Phase 5: Multi-Reviewer Self-Review -> Multiple perspectives critique
Phase 6: Final Polish -> Formatting, citation check, submission prep
```

---

## Phase 0: Task Analysis and Scope Definition

### Step 0.1: Capture Paper Parameters

Before any writing begins, define the paper's parameters:

```python
# code_execution_tool
paper_config = {
    "topic": "<main research topic>",
    "question": "<research question or hypothesis>",
    "audience": "<target readership: e.g., machine learning researchers>",
    "venue_type": "<conference/journal/blog/technical report>",
    "length_target": "<e.g., 8 pages NeurIPS, 15k words survey>",
    "deadline": "<if applicable>",
    "key_contributions": ["<contribution 1>", "<contribution 2>"],
}
print(f"Paper config saved to /a0/usr/workdir/papers/config.json")
```

Save this configuration for reference throughout the process.

### Step 0.2: Record Initial Scope Decision

Use `memory_save` to track your initial scoping decision:

```json
{
    "thoughts": ["Recording initial scope decisions before research begins."],
    "headline": "Saving paper scope to memory",
    "tool_name": "memory_save",
    "tool_args": {
        "text": "Research paper on TOPIC with focus on CONTRIBUTIONS. Target venue: VENUE_TYPE. Key constraints: CONSTRAINTS.",
        "area": "paper-writing"
    }
}
```

---

## Phase 1: Literature Review and Research Planning

### Step 1.1: Initial Discovery Search

Use `search_engine` to discover relevant recent papers:

```json
{
    "thoughts": ["Starting literature discovery for the paper topic."],
    "headline": "Searching for foundational and recent papers",
    "tool_name": "search_engine",
    "tool_args": {
        "query": "<topic> survey 2024 2025 review state of the art"
    }
}
```

Run multiple searches with different queries:
- `<topic> survey 2024` — recent survey papers
- `<topic> best practices guidelines` — methodology papers
- `<topic> limitations challenges future work` — identifying gaps
- `<specific subtopic>` — focused research

### Step 1.2: Create Literature Review Document

Create `literature_review.md` to track papers and key insights:

```markdown
# Literature Review for [Paper Title]

## Foundational Papers
- **Paper**: Author et al., Year, "Title"
- **Key contribution**: <summary>
- **Relevance**: <why this matters to our paper>

## Recent Advances (2023-2025)
[Continue pattern...]

## Methodology Papers  
[Papers that inform our approach]

## Gaps Identified
[Where current literature falls short - our opportunity]
```

### Step 1.3: Build Research Questions List

Based on the literature review, formulate specific research questions:

```python
# code_execution_tool
research_questions = [
    "RQ1: <primary question>",
    "RQ2: <secondary question>", 
    "RQ3: <tertiary/exploratory>"
]
for rq in research_questions:
    print(rq)
```

---

## Phase 2: Thesis Formulation and Detailed Outline

### Step 2.1: Draft Thesis Statement

Formulate a clear thesis statement that captures the paper's central claim.

**Thesis template:**

> "This paper argues that [CLAIM], based on [EVIDENCE TYPE], demonstrating [CONTRIBUTION]."

Example:
> "This paper argues that retrieval-augmented language models significantly reduce hallucination in technical Q&A, based on systematic evaluation across five domains, demonstrating a 40% improvement over baseline approaches."

### Step 2.2: Create Detailed Outline

Create `outline.md` with hierarchical structure:

```markdown
# Paper Title (Working)

## Abstract
- [Key points to cover]

## 1. Introduction
   1.1 Motivation and context
       - Problem statement
       - Why it matters now
   1.2 Research questions
   1.3 Contributions summary
   1.4 Paper organization

## 2. Background and Related Work
   2.1 Technical foundations
   2.2 Prior approaches
   2.3 Limitations of existing work

## 3. Methodology
   3.1 Research design
   3.2 Data collection
   3.3 Analysis approach
   3.4 Validation methods

## 4. Results / Main Findings
   4.1 [Finding category 1]
   4.2 [Finding category 2]
   4.3 [Finding category 3]

## 5. Discussion
   5.1 Interpretation of findings
   5.2 Comparison with prior work
   5.3 Theoretical implications
   5.4 Practical implications

## 6. Limitations
   6.1 Methodological limitations
   6.2 Scope constraints

## 7. Conclusion and Future Work
   7.1 Summary of contributions
   7.2 Directions for future research

## References
[To be populated]
```

### Step 2.3: Save Outline to Memory

```json
{
    "tool_name": "memory_save",
    "tool_args": {
        "text": "Paper outline created for TOPIC with sections: INTRO, BACKGROUND, METHODOLOGY, RESULTS, DISCUSSION, LIMITATIONS, CONCLUSION. Thesis: THESIS_STATEMENT.",
        "area": "paper-writing"
    }
}
```

---

## Phase 3: Parallel Section Drafting

### Step 3.1: Delegate Introduction and Background Sections

Use `call_subordinate` with a writer profile for parallel drafting:

```json
{
    "thoughts": ["Starting parallel section drafting with specialized subordinates."],
    "headline": "Delegating introduction draft to subordinate",
    "tool_name": "call_subordinate",
    "tool_args": {
        "profile": "writer",
        "message": "Write a comprehensive introduction for a research paper on TOPIC. Key elements: (1) motivation hook about WHY this matters now, (2) problem statement with scope, (3) research questions RQs, (4) contributions summary as bullet points. Target audience: AUDIENCE. Write in academic but accessible style. Aim for 800-1200 words.",
        "reset": true
    }
}
```

### Step 3.2: Delegate Methodology Section

```json
{
    "thoughts": ["Drafting methodology section in parallel."],
    "headline": "Delegating methodology draft",
    "tool_name": "call_subordinate", 
    "tool_args": {
        "profile": "writer",
        "message": "Write the methodology section describing: RESEARCH_DESIGN, DATA_COLLECTION methods, ANALYSIS_APPROACH. Include validation methods and any statistical techniques used. Be precise about reproducibility. Target 1000-1500 words.",
        "reset": false
    }
}
```

### Step 3.3: Delegate Discussion Section

```json
{
    "thoughts": ["Drafting discussion section in parallel."],
    "headline": "Delegating discussion draft",
    "tool_name": "call_subordinate",
    "tool_args": {
        "profile": "writer", 
        "message": "Write the discussion section interpreting findings FINDINGS, comparing with prior work PRIOR_WORK, explaining theoretical implications and practical significance. Connect back to research questions. Target 1200-1500 words.",
        "reset": false
    }
}
```

### Step 3.4: Compose Results Section Directly

For results/findings sections with specific data, the main agent should write directly to ensure accuracy:

```python
# code_execution_tool - generate results section based on actual analysis
results_content = """
## 4. Results and Main Findings

### 4.1 [Finding Category 1]

[Detailed description with data, statistics, figures reference]

**Key observation:** [Most important insight from this category]
"""
print(results_content)
```

---

## Phase 4: Integration and Coherence Check

### Step 4.1: Assemble Draft Using text_editor

Combine all sections into the main paper file:

```json
{
    "thoughts": ["Assembling all drafted sections into unified document."],
    "headline": "Integrating paper sections",
    "tool_name": "text_editor:write",
    "tool_args": {
        "path": "/a0/usr/workdir/papers/{paper_id}/PAPER.md",
        "content": "[combined content from all sections]"
    }
}
```

### Step 4.2: Coherence Verification Pass

Use code_execution_tool to check transitions and flow:

```python
# Read paper and verify section transitions
with open("PAPER.md") as f:
    content = f.read()

sections = content.split("## ")
print(f"Found {len(sections)} sections")
for i, sec in enumerate(sections[:5]):  # Check first few
    title = sec.split("
")[0]
    print(f"Section {i+1}: {title}")
```

---

## Phase 5: Multi-Reviewer Self-Review

### Step 5.1: Theoretical Rigor Reviewer

```json
{
    "thoughts": ["Initiating theoretical rigor review perspective."],
    "headline": "Theoretical rigor self-review",
    "tool_name": "call_subordinate",
    "tool_args": {
        "profile": "researcher",
        "message": "You are a rigorous academic reviewer focused on theoretical soundness. Review this paper draft for: (1) clarity of research questions, (2) adequacy of methodology description, (3) validity of claims relative to evidence presented, (4) proper engagement with prior literature. Provide specific critique and suggestions. [PASTE PAPER CONTENT]",
        "reset": true
    }
}
```

### Step 5.2: Methodological Reviewer

```json
{
    "headline": "Methodological self-review",
    "tool_name": "call_subordinate",
    "tool_args": {
        "profile": "researcher",
        "message": "You are a methodological reviewer. Assess whether the research methods are appropriate, well-described, and reproducible. Check for: sampling adequacy, measurement validity, analysis appropriateness, statistical soundness if applicable. [PASTE PAPER CONTENT]",
        "reset": false
    }
}
```

### Step 5.3: Writing/Clarity Reviewer

```json
{
    "headline": "Writing clarity self-review",
    "tool_name": "call_subordinate", 
    "tool_args": {
        "profile": "writer",
        "message": "You are a technical writing reviewer. Evaluate: (1) clarity and precision of prose, (2) paragraph structure and transitions, (3) sentence-level readability, (4) academic tone appropriateness. Flag awkward phrasing, jargon issues, unclear passages. [PASTE PAPER CONTENT]",
        "reset": false
    }
}
```

### Step 5.4: Aggregate Review Feedback

Collect all review feedback and create an action list:

```python
# code_execution_tool - process reviews
type of {key: val for key, val in reviews.items() if isinstance(val, dict)}"
print(f"Reviews aggregated: {summary}")
```

---

## Phase 6: Final Polish and Submission Prep

### Step 6.1: Citation Verification

Use code_execution_tool to verify citation format consistency:

```python
import re

with open("PAPER.md") as f:
    content = f.read()

# Find all citations
citations = re.findall(r"\[.*?\]", content)
print(f"Found {len(citations)} citations")
for c in citations[:10]:
    print(f"  {c}")
```

### Step 6.2: Generate References File

Create `references.bib` from cited works:

```json
{
    "thoughts": ["Extracting and formatting references into BibTeX."],
    "headline": "Generating references.bib",
    "tool_name": "text_editor:write",
    "tool_args": {
        "path": "/a0/usr/workdir/papers/{paper_id}/references.bib",
        "content": "@article{Author2024Title,
  author={...},
  title={...},
  journal={...},
  year={...}
}
"
    }
}
```

### Step 6.3: Final Read-Through

Perform complete read-through for flow and polish:

```json
{
    "thoughts": ["Final comprehensive review before submission."],
    "headline": "Final paper review",
    "tool_name": "document_query", 
    "tool_args": {
        "document": "/a0/usr/workdir/papers/{paper_id}/PAPER.md",
        "queries": [
            "Is the thesis clearly stated?",
            "Are all claims supported by evidence?",
            "Do conclusions follow from results?",
            "Is the writing clear and professional?"
        ]
    }
}
```

### Step 6.4: Save Key Decisions to Memory

```json
{
    "tool_name": "memory_save",
    "tool_args": {
        "text": "Completed research paper on TOPIC. Key contributions: CONTRIBUTIONS. Main findings: FINDINGS. Submitted/prepared for VENUE.",
        "area": "paper-writing"
    }
}
```

---

## Tool Usage Summary

| Phase | Primary Tools |
|-------|---------------|
| 0: Task Analysis | code_execution_tool, memory_save |
| 1: Literature Review | search_engine, text_editor |
| 2: Thesis & Outline | code_execution_tool, text_editor, memory_save |
| 3: Draft Writing | call_subordinate (parallel), text_editor |
| 4: Integration | text_editor, code_execution_tool |
| 5: Self-Review | call_subordinate (multiple reviewers) |
| 6: Final Polish | code_execution_tool, document_query, memory_save |

## Example Session Flow

```json
{
    "thoughts": ["User wants a research paper on topic X. Activating research-paper-writing skill."],
    "headline": "Starting Phase 0: Task Analysis",
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "python",
        "session": 0,
        "code": "print('Research Paper Writing Workflow Started')
print(f'Topic: {topic}')"
    }
}
```

Then proceed through phases sequentially, using memory_save at key decision points and call_subordinate for parallel section drafting in Phase 3.
