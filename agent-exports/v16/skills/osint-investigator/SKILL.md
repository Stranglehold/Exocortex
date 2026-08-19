---
name: osint-investigator
description: Native Exocortex OSINT investigation framework adapting OpenPlanter's
  recursive agent methodology. Performs entity resolution across FEC campaign finance,
  SEC EDGAR filings, SAM.gov contracts, lobbying disclosures, and sanctions lists
  using call_subordinate for parallel sub-agent delegation.
---

# OSINT Investigator

## Purpose

This skill adapts OpenPlanter's recursive agent methodology for Agent Zero. It performs **entity resolution across heterogeneous datasets** (FEC campaign finance, SEC EDGAR filings, SAM.gov contracts, lobbying disclosures, OFAC sanctions) using native Exocortex tools—`call_subordinate`, `search_engine`, `browser_agent`, and `text_editor`—to surface non-obvious connections between people, companies, and government entities.

**Core principle**: Decompose investigations into parallel sub-agent tasks (Entity Resolution, Contract Analysis, Source Verification), then synthesize findings into evidence-backed relationship chains with citations to source documents.

## When to Use

Use this skill when:
- Investigating potential conflicts of interest or undisclosed relationships
- Mapping corporate ownership structures across public records
- Tracing money flows between political campaigns and government contracts
- Verifying entity identities across fragmented datasets (name variations, typos)
- Building intelligence reports requiring evidence chains from multiple sources

Do NOT use for:
- Simple fact-checking queries (use `search_engine` directly instead)
- Tasks without multi-source data requirements
- Real-time investigations (this skill focuses on structured public records, not live monitoring)

## How It Works
### Phase A: Decomposition & Sub-Agent Launch
```
1. think → "Plan investigation: [Target] across [Sources]"
2. call_subordinate (Entity Resolution) → Resolve name variations across FEC, SEC datasets using fuzzy matching
3. call_subordinate (Contract Analysis) → Query SAM.gov for government contracts involving resolved entities
4. call_subordinate (Sanctions Check) → Verify against OFAC SDN lists and ICIJ leaks database
5. execute → Synthesize findings into evidence chain with relationship graph
```
### Phase B: Entity Resolution Pattern
OpenPlanter uses Levenshtein distance for fuzzy matching across datasets:
- **FEC** (Campaign Finance): Donor names, employers, contribution amounts
- **SEC EDGAR**: Corporate registrants, beneficial owners, filings  
- **SAM.gov**: Contract vendors, DUNS numbers
- **ICIJ Offshore Leaks**: Shell companies, offshore entities
**Native Exocortex equivalent:**
- Use `search_engine` for semantic entity resolution across public records
- Use Python code execution in `code_execution_tool` to run fuzzy matching algorithms locally
### Phase C: Data Ingestion & Normalization
OpenPlanter stores normalized data in Markdown wiki format with internal links. Native adaptation:
- **Option 1**: Use `/a0/usr/workdir/` as workspace; write findings via `text_editor:write_file`
- **Option 2**: Store structured JSON findings via `code_execution_tool` file writes
- **Option 3**: Use `memory_save` for key relationships (best for quick recall)
### Phase D: Relationship Visualization
OpenPlanter uses Cytoscape.js for interactive graphs. Native adaptation:
- Generate HTML/Cytoscape.js visualization via `code_execution_tool`
- Output as artifact using `emit_artifact`
## Tool Mappings: OpenPlanter → Agent Zero
| OpenPlanter Tool | Agent Zero Equivalent | Notes |
|------------------|---------------------|-------|
| `list_files`/`search_files` | `search_engine`, `text_editor:list` | Use search for semantic, text_editor for local FS |
| `read_file`/`write_file` | `text_editor:read_file`/`text_editor:write_file` | Direct 1:1 mapping |
| `edit_file`,`hashline_edit`,`apply_patch` | `text_editor:replace` (patching logic) | Use replace for surgical edits |
| `run_shell`/`run_shell_bg` | `code_execution_tool` with runtime=terminal | Same capability, different interface |
| `web_search` (Exa) | `search_engine` or `browser_agent` | search_engine is semantic; browser_agent for scraping |
| `fetch_url` | `browser_agent` with fetch_mode="download" | Or use code_execution_tool with urllib/requests |
| `think`/`subtask` | Native Agent Zero decomposition + `call_subordinate` | Default behavior + explicit subagent tool |
| `execute` (merge findings) | `response` tool with synthesis or write to file via text_editor | Synthesize in response or save structured output |

## Capabilities Breakdown

### Capability 1: Dataset Ingestion & Workspace Management
**Purpose**: Load, inspect, and transform source datasets; create normalized wiki documents.

**Workflow Example:**
```python
# code_execution_tool — Parse FEC CSV file locally
import csv
fec_data = []
with open("/path/to/fec_donors.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        fec_data.append({"donor": row["name"], "amount": float(row["contribution_amt"]), "candidate": row["candidate_name"]})
print(f"Loaded {len(fec_data)} FEC contributions")
```

### Capability 2: Entity Resolution & Cross-Linking
**Purpose**: Match entities across datasets using fuzzy string matching (Levenshtein distance).

**Workflow Example:**
```python
# code_execution_tool — Fuzzy match names across datasets
from difflib import SequenceMatcher

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

threshold = 0.85
fec_names = ["John Smith", "Jon Smyth"] 
sec_names = ["John A Smith", "Jonathan Smith LLC"]
matches = []
for fec in fec_names:
    for sec in sec_names:
        if similarity(fec, sec) > threshold:
            matches.append((fec, sec, similarity(fec, sec)))
print(f"Cross-dataset links: {matches}")
```

### Capability 3: Web Intelligence & Verification
**Purpose**: Pull public records and verify entities via semantic search or scraping.

**Tool Call Example:**
```json
{
  "tool_name": "search_engine",
  "query": "John Smith FEC campaign finance contributions Boston",
  "max_results": 5,
  "category_filter": "news"
}
```

### Capability 4: Recursive Investigation & Sub-Agent Delegation
**Purpose**: Decompose investigations into parallel sub-agent tasks with acceptance criteria.

**Tool Call Example:**
```json
{
  "tool_name": "call_subordinate",
  "task": "Entity Resolution: Resolve name variations for John Smith across FEC federal donations and SEC EDGAR filings. Use fuzzy matching (Levenshtein >0.85). Return JSON with matched pairs, confidence scores, and source citations.",
  "context": {
    "target_name": "John Smith",
    "sources": ["fec-federal", "sec-edgar"],
    "acceptance_criteria": "Return minimum 2 matches across datasets or confirm no links exist"
  },
  "tools": ["search_engine", "code_execution_tool", "text_editor:read_file"]
}
```

### Capability 5: Evidence Chain Construction
**Purpose**: Synthesize findings into structured reports with citations.

**Workflow Example:**
```python
# code_execution_tool — Generate evidence chain JSON
evidence_chain = {
    "hypothesis": "John Smith donated to Boston Mayor race while his company held city contracts",
    "evidence": [
        {"source": "fec-federal", "fact": "Contributed $5,000 to City Councilor X (2023)", "date": "2023-10-15"},
        {"source": "sam-gov", "fact": "Company XYZ awarded contract for $1.2M IT services (2024)", "date": "2024-01-20"}
    ],
    "relationship": "Same entity via fuzzy match (0.92 similarity), temporal overlap detected",
    "confidence": "HIGH"
}
import json
with open("/a0/usr/workdir/findings/evidence_chain.json", "w") as f:
    json.dump(evidence_chain, f, indent=2)
```

## Examples and Usage

### Example 1: Basic Entity Resolution Investigation
**Goal**: Find connections between a person and government contracts.

```json
{
  "thoughts": [
    "User wants to investigate John Smith's connection to city contracts",
    "Need to check FEC for political donations, SAM.gov for contracts",
    "Use entity_resolution pattern with fuzzy matching"
  ],
  "headline": "Starting OSINT investigation of John Smith",
  "tool_name": "call_subordinate",
  "tool_args": {
    "task": "Investigate connections between John Smith and Boston government entities. Check FEC donations (2023-2024), SAM.gov contracts, and Massachusetts SOS filings. Use fuzzy matching threshold >0.85 for name variations.",
    "context": {"target_name": "John Smith", "sources": ["fec-federal", "sam-gov", "massachusetts-sos"]}
  }
}
```

### Example 2: Multi-Source Cross-Linking
**Goal**: Trace corporate ownership across SEC filings and lobbying disclosures.

```python
# code_execution_tool — Cross-link analysis
def cross_link_entities(fec_data, sec_data):
    links = []
    for fec_person in fec_data:
        for sec_entity in sec_data:
            if similarity(fec_person["name"], sec_entity["registrant"]) > 0.85:
                links.append({
                    "person": fec_person["name"],
                    "company": sec_entity["registrant"],
                    "fec_role": fec_person.get("occupation", "Unknown"),
                    "sec_filings": len(sec_entity["filings"]),
                    "confidence": similarity(fec_person["name"], sec_entity["registrant"])
                })
    return sorted(links, key=lambda x: x["confidence"], reverse=True)

# Execute cross-link analysis
links = cross_link_entities(fec_donors, sec_registrants)
print(f"Found {len(links)} potential links")
```

### Example 3: Evidence Chain Generation
**Goal**: Build a structured report with citations.

```python
# code_execution_tool — Generate evidence chain
evidence_chain = {
    "investigation_id": "inv-2024-john-smith",
    "target": "John Smith",
    "hypothesis": "Subject holds undisclosed financial interest in government contracting",
    "findings": [
        {
            "source": "fec-federal",
            "entity_type": "donation_record",
            "fact": "Contributed $10,000 to Boston City Councilor X (2023-11-15)",
            "citation": "FEC ID: 4567890, Report: R001"
        },
        {
            "source": "sam-gov",
            "entity_type": "contract_award",
            "fact": "Company ABC awarded $2.5M IT services contract (2024-02-20)",
            "citation": "SAM.gov Contract ID: SAM123456789"
        }
    ],
    "relationship_chain": [
        {"from": "John Smith", "relation": "donated_to", "to": "City Councilor X", "confidence": 1.0},
        {"from": "Company ABC", "relation": "awarded_contract_by", "to": "Boston IT Department", "confidence": 1.0}
    ]
}
import json
with open("/a0/usr/workdir/investigations/evidence_chain.json", "w") as f:
    json.dump(evidence_chain, f, indent=2)
```

## Limitations and Constraints

### What This Skill Does NOT Do
- **No real-time monitoring**: This skill processes existing data snapshots; it does not continuously monitor sources for new records.
- **Limited to public datasets**: Cannot access private databases or behind-paywall sources without explicit browser_agent intervention.
- **No legal advice**: Findings are investigative leads only, not legal evidence or conclusions about wrongdoing.

### Technical Constraints
| Constraint | Impact |
|------------|--------|
| API Rate Limits | FEC, SEC EDGAR, and SAM.gov have strict rate limits (typically 20 requests/minute). Use `run_shell_bg` patterns for large datasets. |
| Fuzzy Matching Accuracy | Levenshtein-based matching may miss phonetic similarities or abbreviations not captured by edit distance. Consider adding soundex/metaphone algorithms for better name resolution. |
| Data Freshness | Wiki data layer is snapshot-based; verify time-sensitive findings with live queries via `browser_agent`. |

### Known Gaps vs. OpenPlanter
- **Missing**: Interactive Cytoscape.js graph visualization (requires `emit_artifact` HTML generation or separate Flask server)
- **Missing**: Native desktop GUI (Tauri app not portable to Agent Zero container environment)
- **Workaround**: Generate JSON graph data and use external tools (Gephi, Cytoscape) for visualization, or build HTML artifacts via `emit_artifact`

## Security Considerations

### Data Privacy
- FEC campaign finance data is public, but handle personal identifiers (SSN fragments, addresses) according to your local privacy regulations.
- SEC EDGAR filings are public corporate records.
- SAM.gov contracts contain vendor PII and DUNS numbers—do not expose these in unsecured channels.

### API Key Management
OpenPlanter uses `credentials.py` for API keys. For Agent Zero:
- Store API keys via Exocortex secrets manager or environment variables
- Do NOT hardcode keys in SKILL.md examples
- Use `.env` files committed to `.gitignore`

## Version History
- **1.0.0** (2024): Initial release adapting OpenPlanter v1.x recursive agent methodology
  - Based on: OpenPlanter repository commit [current]
  - Mapped: `entity_resolution.py`, `tools.py` patterns to native Exocortex tools
  - Added: Memory integration via `memory_save` for evidence persistence
