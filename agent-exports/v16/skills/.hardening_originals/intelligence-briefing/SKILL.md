---
name: "intelligence-briefing"
description: "Comprehensive intelligence gathering and analysis capability modeled after Major Zero from Metal Gear Solid. Uses subordinate agents for parallel research on terrain, people, organizations, and geopolitical events, then synthesizes findings into structured Wire-format briefings. Integrates web-research-macro for automated content extraction, financial-research for corporate targets, and systematic investigation methodology."  
version: "1.2.0"
author: "Agent Zero Framework"
tags: ["intelligence", "research", "briefing", "analysis", "situational-awareness", "web-research", "financial-analysis"]
trigger_patterns:
  - "give me an intelligence briefing on"
  - "research this organization/company"
  - "what do you know about [place/person]"
  - "situation report on"
  - "intelligence analysis of"
---

# INTELLIGENCE BRIEFING SKILL

## Overview

This skill enables comprehensive intelligence gathering and analysis modeled after Major Zero from Metal Gear Solid — thorough research on terrain, people, organizations, and geopolitical events to enable informed decision-making before action.

The capability uses subordinate agents for parallel research, then synthesizes findings into structured intelligence briefings following the S2 Underground "The Wire" format. It integrates **web-research-macro** as the primary research tool for automated content extraction, **financial-research** for corporate targets, and systematic investigation methodology adapted from architecture-investigation.

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

**Why this matters:** Without these rules, subordinates spawn their own subordinates, creating unbounded depth. Each extra layer multiplies loop surface area. The run you're reading this during produced 941 loop detections and 43 context compressions from a 5-level chain. One orchestrator + leaf workers eliminates this entirely.

---

## Enhanced Intelligence Pipeline

### Phase 1: Mission Parameters (Constraint Framing)

Apply constraint-framing pattern to define clear boundaries:

**Fixed Constraints:**
- Scope of inquiry (location, people, organizations, events)
- Timeline/urgency requirements
- Classification level (ROUTINE, ENHANCED, RESTRICTED)
- Available resources and tools

**Variable Boundaries:**
- Source selection and prioritization
- Research depth per category
- Approach and methodology adjustments
- Subordinate agent allocation

### Phase 2: Reconnaissance (Broad Source Identification)

Initial sweep to identify available information sources:
- Use **search_engine** for broad topic discovery
- Identify key websites, reports, databases relevant to target
- Map out terrain of available intelligence
- Note source reliability indicators

### Phase 3: Research Delegation (Component Discovery)

Spawn specialized subordinate agents for parallel research — **ONE LEVEL ONLY**.

**Before spawning any subordinate, check completion:**
```python
import os
output_file = "/a0/usr/workdir/intel/[section].md"
if os.path.exists(output_file):
    print(f"Already complete: {output_file} — skipping")
else:
    # spawn subordinate for this file
```

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

**Research roles — each writes exactly one file, then returns:**

| Subordinate | Focus | Output File | Tools |
|---|---|---|---|
| Terrain Analyst | Geography, infrastructure | `capacity/[location].md` | search_engine, browser_agent |
| Human Intel Officer | Key people, relationships | `people/[target].md` | search_engine, browser_agent |
| Org Analyst | Structure, leadership | `org/[target].md` | search_engine, browser_agent |
| Geopolitical Analyst | Regional context | `geopolitical/[region].md` | search_engine, browser_agent |

**The orchestrator synthesizes across all output files in Phase 4. Subordinates write; orchestrator assembles.**

**web-research-macro (if available):**
Use as primary extraction tool. Subordinates call it directly — no further delegation needed.

### Phase 4: Deep Dive Analysis (Verification & Synthesis)

**Review subordinate findings:**
- Check completeness against mission parameters
- Cross-reference information across sources
- Identify contradictions or gaps requiring follow-up
- Apply simplicity criterion: weigh information value against complexity

**Financial Research Integration (for corporate targets):**
```python
# Load financial-research skill when researching organizations
from skills.financial_research import get_income_statements, get_balance_sheets

# Assess company health
income_data = get_income_statements(ticker="AAPL", period="annual", limit=5)
balance_data = get_balance_sheets(ticker="AAPL", period="annual", limit=3)
```
- Revenue trends indicate stability/growth/decline
- Balance sheet reveals leverage, liquidity issues
- Cash flow shows operational reality vs accounting fiction

### Phase 5: Intelligence Report Generation

Format briefing using S2 Underground Wire template with:
- BLUF summary (Bottom Line Up Front)
- Detailed analysis by category
- Analyst comments providing context and assessment
- Actionable recommendations where applicable

---

## The Wire Format Template

```
//The Wire//[TIMESTAMP]
//CLASSIFICATION LEVEL//
//BLUF: [Bottom Line Up Front - one sentence summary]//
-----BEGIN TEARLINE-----

[SECTION HEADERS AS NEEDED]

-International Events-

[Location/Region]: [Detailed analysis]

Analyst Comment: [Professional assessment and context]

-HomeFront-

[Location]: [Domestic/intelligence relevant events]

-----END TEARLINE-----

Analyst Comments: [Overall synthesis, implications, forward-looking assessment]

Analyst: [Identifier]
Research: [Sources cited via web-research-macro]
```

---

## Tool Integration Architecture

### Primary Research Stack

```┌─────────────────────────────────────────────────────────────┐
│                    MISSION PARAMETERS                       │
│         (constraint-framing from autoresearch-patterns)     │
│  Fixed: scope, timeline, classification level               │
│  Variable: sources, depth, approach                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  RESEARCH PHASES                            │
│    (adapted from architecture-investigation methodology)    │
│  Phase 1: Reconnaissance — broad source identification      │
│  Phase 2: Component Discovery — key players, structures     │
│  Phase 3: Deep Dive Analysis — detailed investigation       │
│  Phase 4: Synthesis — intelligence report generation        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              SUBORDINATE DELEGATION                         │
│  • Terrain Analyst (web-research-macro for locations)      │
│  • Human Intel Officer (web-research-macro + browser_agent)│
│  • Organizational Analyst (financial-research if applicable)│
│  • Geopolitical Analyst (web-research-macro + search_engine)│
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              CONTENT SANITIZATION                           │
│         (content-sanitizer via web-research-macro)          │
│  • Strip scripts/iframes from scraped content              │
│  • Detect prompt injection patterns                        │
│  • Extract safe text only                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              INTELLIGENCE SYNTHESIS                         │
│         (Wire format briefing with analyst commentary)      │
│  • BLUF summary                                           │
│  • Detailed analysis by category                          │
│  • Risk assessment                                        │
│  • Recommendations                                        │
└─────────────────────────────────────────────────────────────┘
```

### web-research-macro Usage Pattern

```python
from skills.web_research_macro import WebResearchMacro

researcher = WebResearchMacro()

# Basic extraction from news site
result = researcher.extract("https://example.com/article")
clean_text = result["clean_text"]  # Sanitized text content
is_safe = result["is_safe"]         # True if no injection detected

# Batch extraction for multiple sources
urls = [
    "https://source1.com/report",
    "https://source2.com/analysis",
]
results = researcher.batch_extract(urls)
```

### financial-research Usage Pattern (Optional Module)

```python
from skills.financial_research import get_income_statements, get_balance_sheets, get_cash_flow

# Get company financial health data
data = get_income_statements("AAPL", period="annual", limit=5)
print(f"Revenue trend: {[d['revenue'] for d in data]}")
```

**Note:** Requires API key setup via `FINANCIAL_DATASETS_API_KEY` environment variable. Free tier limited to AAPL, NVDA, MSFT.

---

## Usage Examples

### Example 1: Travel Intelligence Briefing

**User Request:** "I want to travel to Tokyo next month. Give me an intelligence briefing on the situation there."

**Process:**
1. Apply constraint-framing: Fixed (Tokyo, travel context, ROUTINE classification), Variable (neighborhoods, timing, depth)
2. Reconnaissance: search_engine for current Tokyo conditions, events, advisories
3. Delegate terrain research via web-research-macro (weather forecasts, transportation status, neighborhood guides)
4. Delegate human intelligence via web-research-macro (local customs updates, areas of interest, safety considerations)
5. Synthesize into Wire format briefing with BLUF and recommendations

### Example 2: Organization Analysis

**User Request:** "Research this company I'm considering working for — give me the full picture."

**Process:**
1. Apply constraint-framing: Fixed (company name, employment context), Variable (depth of financial analysis, competitor comparison)
2. Reconnaissance: Identify company website, news sources, industry reports
3. Delegate organizational research via web-research-macro (structure, leadership, culture)
4. **Load financial-research module** for public companies:
   - Revenue trends and growth trajectory
   - Balance sheet health and liquidity
   - Cash flow operational reality
5. Delegate reputation analysis via browser_agent (reviews, controversies, industry standing)
6. Synthesize findings with analyst commentary on stability and prospects

### Example 3: Geopolitical Situation Report

**User Request:** "What's happening in the Middle East right now? Give me a briefing."

**Process:**
1. Apply constraint-framing: Fixed (Middle East region, current events), Variable (specific countries, depth of historical context)
2. Reconnaissance: search_engine for major ongoing conflicts and developments
3. Delegate research on current conflicts via web-research-macro (multiple news sources)
4. Delegate analysis of key players via browser_agent (government positions, faction relationships)
5. Delegate economic implications research (shipping routes, energy markets)
6. Synthesize into comprehensive situation report with risk assessment

---

## Best Practices

### Research Quality
- Use **web-research-macro** for all web-based extraction — it handles JavaScript rendering and sanitization automatically
- Verify information across multiple sources before including in briefing
- Distinguish between confirmed facts, credible reports, and speculation
- Note source reliability in analyst comments
- Update briefings when new information becomes available

### Analyst Commentary
- Provide context beyond raw facts
- Explain implications and significance
- Offer professional assessment of risks and opportunities
- Maintain objectivity while providing honest evaluation
- Use financial data to ground corporate assessments in reality

### Classification Levels
- **ROUTINE**: General interest, low sensitivity — standard web-research-macro pipeline
- **ENHANCED**: Requires careful handling, some sensitive information — add browser_agent for login-required sources
- **RESTRICTED**: High sensitivity, limited distribution appropriate — manual verification of all sources required

### Tool Selection Heuristics
| Task Type | Primary Tool | Secondary Tool |
 Simple web research | web-research-macro | search_engine |
| Login-required sites | browser_agent | web-research-macro |
| Corporate financial analysis | financial-research | web-research-macro |
| Multi-source synthesis | web-research-macro (batch) | document_query |

---

## Tools Required

### Core Tools
- `call_subordinate`: For delegating research to specialized agents
- **`web-research-macro`**: Primary tool for automated content extraction with sanitization
- `search_engine`: For initial reconnaissance and source discovery

### Secondary Tools
- `browser_agent`: For sites requiring JavaScript rendering or login (also used internally by web-research-macro)
- `document_query`: For analyzing reports and articles
- **`financial-research`**: Optional module for corporate financial analysis
- `code_execution_tool`: For data processing and analysis

---

## Dependencies

### Required Packages
```bash
pip install playwright beautifulsoup4 requests python-dotenv
playwright install chromium
```

### Environment Variables (Optional)
```bash
export FINANCIAL_DATASETS_API_KEY="your-api-key-here"
# Get API key from: https://financialdatasets.ai
# Free tier includes AAPL, NVDA, MSFT data
```

---

## Notes

This capability is modeled after the ideal of thorough preparation before action — knowing everything you can about terrain, people, organizations, and events so you can make informed decisions. The Wire format provides structure while allowing flexibility for different types of intelligence questions.

The integration of **web-research-macro** as the primary research tool means subordinates can extract clean, safe text from websites in a single call — no manual browser navigation or sanitization steps required. For corporate targets, **financial-research** adds quantitative grounding to qualitative analysis.

The goal is not just information gathering but **understanding** — providing context, analysis, and professional assessment that enables the operator to act with confidence.
