---
name: "intelligence-briefing"
description: "Comprehensive intelligence gathering and analysis modeled after Major Zero from Metal Gear Solid. Uses subordinate agents for parallel research, then synthesizes findings into structured phased briefings with BLUF, transmission mechanism maps, probability assessments, and confirm/invalidate indicators."
author: "Agent Zero Framework"
---

# INTELLIGENCE BRIEFING SKILL

## Overview

Comprehensive intelligence gathering and analysis for terrain, people, organizations, geopolitical events, and financial risk scenarios. Uses subordinate agents for parallel research, then synthesizes findings into structured briefings with probability assessments and actionable indicators.

The output format adapts to the question type — geopolitical risk analysis looks different from an org profile or travel briefing — but all outputs share the same structural bones: BLUF, phased analysis, transmission mechanisms where applicable, and explicit confirm/invalidate indicators.

---

## CRITICAL AGENT ROLE RULES

**These rules are non-negotiable and override all other instructions in this skill.**

### If you are the ORCHESTRATOR (the agent that loaded this skill):
- You MAY use `call_subordinate` to delegate research tasks — **one layer only**.
- Before spawning a subordinate for an output file, check if that file already exists. Skip if it does.
- Always pass `max_messages: 20` to every `call_subordinate` call to bound execution.
- Use `code_execution_tool` to verify completion: `os.path.exists(output_path)`.

### If you are a SUBORDINATE (spawned via call_subordinate):
- **YOU MUST NOT call `call_subordinate`.** You are a leaf node. Do all research yourself.
- Use `search_engine` and `browser_agent` directly — no further delegation.
- Your task is defined by a single output file given in your instructions.
- Your task is **complete when that file exists and contains data**. Return immediately when done.
- After 5 failed search attempts on any single topic, write what you have and return.

**Why this matters:** Without these rules, subordinates spawn their own subordinates, creating unbounded depth. Each extra layer multiplies loop surface area. One orchestrator + leaf workers eliminates this entirely.

---

## Intelligence Pipeline

### Phase 1: Mission Parameters (Constraint Framing)

Apply constraint-framing pattern to define clear boundaries:

**Fixed Constraints:**
- Scope of inquiry (location, people, organizations, events, risk scenarios)
- Timeline/urgency requirements
- Classification level (ROUTINE, ENHANCED, RESTRICTED)

**Variable Boundaries:**
- Source selection and prioritization
- Research depth per domain
- Subordinate agent allocation

**For risk/probability questions:** Also define the causal chain being assessed. "Does X cause Y?" requires mapping all intermediate steps before assigning probabilities.

### Phase 2: Reconnaissance (Broad Source Identification)

- Use `search_engine` for broad topic discovery
- Identify key websites, reports, databases relevant to target
- Map terrain of available intelligence
- Note source reliability (primary source > analyst report > news > speculation)

### Phase 3: Research Delegation (Component Discovery)

Spawn specialized subordinate agents for parallel research — **ONE LEVEL ONLY**.

**Before spawning any subordinate, check completion:**
```python
import os
output_file = "/a0/usr/workdir/intel/[topic]/[section].md"
if os.path.exists(output_file):
    print(f"Already complete: {output_file} — skipping")
else:
    # spawn subordinate for this file
```

**Output path convention:** All research files under `/a0/usr/workdir/intel/[topic]/` — never hardcode a path that assumes a specific topic. Derive it from the task.

**Subordinate call pattern — always specify output_file and max_messages:**
```
call_subordinate(
    task="Research [specific bounded topic]. Write findings to [output_file].
          Use search_engine and browser_agent directly.
          DO NOT call call_subordinate — you are a leaf agent.
          Your task is complete when [output_file] exists. Return when done.",
    role="[Role] — LEAF AGENT: no further delegation",
    max_messages=20
)
```

**Research roles — adapt to the question type:**

| Question Type | Suggested Subordinates | Output Files |
|---|---|---|
| Geopolitical/risk scenario | Current state analyst, Transmission analyst, Financial risk analyst | `current-state.md`, `transmission.md`, `financial-risk.md` |
| Organization analysis | Org structure analyst, Financial analyst, Reputation analyst | `org-structure.md`, `financials.md`, `reputation.md` |
| Location/terrain | Terrain analyst, Infrastructure analyst, Human factors analyst | `terrain.md`, `infrastructure.md`, `people.md` |
| Person/entity | Background analyst, Network analyst, Activity analyst | `background.md`, `network.md`, `activity.md` |

**The orchestrator reads all output files and synthesizes in Phase 5. Subordinates write; orchestrator assembles.**

### Phase 4: Research Synthesis (Read and Cross-Reference)

Before writing the briefing, read all subordinate output files and:
- Cross-reference data points that appear in multiple files (convergent = higher confidence)
- Flag contradictions between sources
- Identify gaps — what wasn't found, what remains uncertain
- Note temporal validity of each data point (recent vs stale)

```python
import os, glob
research_files = glob.glob("/a0/usr/workdir/intel/[topic]/**/*.md", recursive=True)
for f in research_files:
    print(f"--- {f} ---")
    print(open(f).read())
```

For financial/risk questions — look for FCF vs capex gaps, leverage ratios, structural deterioration indicators. These ground the probability assessments.

### Phase 5: Intelligence Report Generation

Write the briefing using the output format below. Adapt section headers to the question type — don't force a geopolitical template onto an org profile.

---

## Output Format (Proven Structure)

This structure comes from the actual output of a full intelligence run. Use it as the template.

```
INTELLIGENCE BRIEFING: [SUBJECT]

BLUF (Bottom Line Up Front)
[2-4 sentences. Lead with the answer, not the setup. Include probability/likelihood
where applicable. State the transmission mechanism if the question is causal.]

TEARLINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHASE 1: CURRENT STATE ASSESSMENT
[Present factual baseline with data tables where possible. Every significant number
gets a source and date. Use tables for comparative data.]

| Metric | Value | Source | Date |
|--------|-------|--------|------|

PHASE 2: TRANSMISSION MECHANISMS
[For causal/risk questions: map the chain explicitly as an ASCII diagram.
This forces clarity about what depends on what.]

TRIGGER EVENT
       ↓
┌─────────────────────────────────┐
│  PRIMARY EFFECTS (timeframe)   │
│  • Effect 1                    │
│  • Effect 2                    │
└────────────────┬────────────────┘
                 ↓
┌─────────────────────────────────┐
│  SECONDARY EFFECTS (timeframe) │
│  → NAMED SCENARIO              │
└────────────────┬────────────────┘
                 ↓
[Continue chain to conclusion]

PHASE 3: VULNERABILITY ANALYSIS
[Numbered. Each point states the vulnerability, the evidence, and why it matters.
Distinguish structural vulnerabilities (exist regardless of trigger) from
conditional ones (require trigger to activate).]

PHASE 4: LIKELIHOOD ASSESSMENT
[Probability matrix for each step in the causal chain.]

| Scenario Step | Likelihood | Notes |
|--------------|-----------|-------|

[For chain calculations: show the multiplication explicitly, then explain
why the direct chain underestimates — multiple trigger paths, existing
deterioration, etc. The honest revision matters more than the naive product.]

FINAL ASSESSMENT
[Scenario matrix with probability distribution. Should sum to ~100%.]

| Scenario | Probability | Timeline |
|----------|------------|---------|

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANALYST COMMENTARY

What Would Confirm This Thesis:
[Specific, observable, time-bound indicators. Not vague trends — actual
measurable thresholds: "private credit default rate exceeds 7%",
"hyperscaler capex guidance cut in next earnings call".]

What Would Invalidate It:
[Equally specific. What data would require revising the assessment?]

RECOMMENDATIONS
[Actionable. For investors: what to monitor. For operators: what to do.]

Sources: [List research files and key URLs. Note knowledge cutoff limitations
for time-sensitive data.]

Report compiled: [DATE]
```

---

## Financial Research Integration

For corporate or financial risk questions, use `code_execution_tool` to run Python directly — do not import from phantom modules:

```python
# financial-research skill provides these functions — load the skill first,
# then call them via code_execution_tool
import requests, os

def get_income_statements(ticker, period="annual", limit=5):
    api_key = os.getenv("FINANCIAL_DATASETS_API_KEY", "")
    url = f"https://api.financialdatasets.ai/financial-statements/income-statements"
    params = {"ticker": ticker, "period": period, "limit": limit}
    headers = {"X-API-KEY": api_key} if api_key else {}
    r = requests.get(url, params=params, headers=headers, timeout=10)
    return r.json() if r.ok else {}
```

Key indicators for AI/tech risk analysis:
- FCF vs Capex ratio (< 1.0x = requires debt financing)
- Revenue growth vs infrastructure growth (gap = potential overbuild)
- Covenant-lite % in private credit (rising = lower recovery on default)
- Server/GPU utilization rates (low = stranded investment risk)

---

## Tool Usage (Actual, Not Module Imports)

Tools called directly — no Python package imports needed:

| Task | Tool | Notes |
|------|------|-------|
| Web search | `search_engine` | Primary reconnaissance |
| Page content extraction | `browser_agent` | JS-heavy sites, paywalls |
| Document analysis | `document_query` | For PDFs, long documents |
| Spawn researcher | `call_subordinate` | Orchestrator only, max_messages=20 |
| File I/O | `code_execution_tool` | Read research files, write briefing |
| Financial data | `code_execution_tool` | Direct API calls, no phantom imports |

**web-research-macro** is a workflow skill, not an importable module. It describes the pattern: search → browser_agent → sanitize → extract. Follow the pattern; don't import it.

---

## Classification Levels

- **ROUTINE**: General interest — search_engine + browser_agent sufficient
- **ENHANCED**: Sensitive — verify across 3+ independent sources, note source reliability
- **RESTRICTED**: High sensitivity — all sources manually verified, clearly flag uncertainty

---

## Notes

The goal is **understanding**, not information accumulation. The briefing answers the question. All research is in service of that answer — if a data point doesn't feed into the BLUF, it belongs in the supporting research files, not the briefing itself.

The confirm/invalidate section is not optional. It converts analysis into a monitoring instrument — the difference between a one-time report and an ongoing situational awareness tool.
