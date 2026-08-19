---
name: investigation-workflow
description: This skill orchestrates recursive OSINT investigations across heterogeneous
  datasets using Agent Zero's subordinate profiles and native tools. It adapts OpenPlanter's
  recursive entity resolution methodology—where subtasks recursively query FEC, SEC
  EDGAR, SAM.gov contracts, and corporate registries to build evidence chains—for
  Agent Zero's architecture.
---

# Investigation Workflow

## Purpose

This skill orchestrates recursive OSINT investigations across heterogeneous datasets using Agent Zero's subordinate profiles and native tools. It adapts OpenPlanter's recursive entity resolution methodology—where subtasks recursively query FEC, SEC EDGAR, SAM.gov contracts, and corporate registries to build evidence chains—for Agent Zero's architecture.

**Core capability:** Cross-dataset investigation orchestration via `call_subordinate` with specialized profiles (hacker/researcher), `memory_save` for evidence chain persistence, and the native collector tools (`entity_resolve`, `source_ingest`).

**Key adaptation:** OpenPlanter uses `subtask/execute` tools for parallel dataset queries. This skill maps that pattern to Agent Zero's `call_subordinate` with profile specialization:
- **hacker profile** → Data extraction and entity resolution (equivalent to OpenPlanter's `fetch_*` scripts)
- **researcher profile** → Cross-referencing and evidence chain construction (equivalent to OpenPlanter's `cross_link_analysis`)

## When to Use

Use this skill when:
- Investigating an entity across multiple OSINT sources (campaign finance, corporate registries, government contracts)
- Building cross-dataset evidence chains linking donors → shell companies → contract recipients
- Performing recursive entity resolution where Dataset A matches trigger queries against Dataset B and C
- Orchestrating multi-stage investigations requiring specialized profiles for data extraction vs analysis

Do NOT use for:
- Single-source lookups (use `search_engine` or specific collector tools directly)
- Cases where no cross-dataset linking is needed

## Security Rules — Non-Negotiable

1. **No external API calls.** All data must come from local collections via native collectors.
2. **Memory persistence mandatory.** Every evidence chain found must be saved to memory using `memory_save` with structured JSON containing confidence scores and matched records.
3. **Profile specialization required.** Use `call_subordinate` only with verified profiles (hacker, researcher) — never generic profiles for data extraction tasks.
4. **Threshold enforcement.** Entity resolution matches below 0.85 confidence must be flagged as potential false positives.
5. **No recursive loops without termination.** Each subordinate call must have a clear exit condition: maximum 3 levels of recursion or evidence chain saturation.

---

## Phase 0: Classify the Investigation Type

Before invoking any tools, establish:

**What is the seed entity?**
- Person name (campaign donor, corporate officer)
- Organization name (PAC, LLC, corporation) 
- Entity ID (CIK number for SEC, Tax ID for SAM.gov)

**What is the investigation scope?**
- **Vertical** → Deep dive into one entity across time
- **Horizontal** → Cross-dataset linking at a point in time  
- **Recursive** → Chain-based exploration (donor A → company B → contracts C)

---

## Phase 1: Source Preparation

Before running entity resolution, ensure datasets are available via `source_ingest`:

```python
# Example: Check available sources
available_sources = [
    "fec_federal",      # Campaign finance donors
    "sec_edgar",        # Corporate registrants
    "sam_gov",          # Federal vendor data
]
```

If datasets are not present, use `call_subordinate` with the **hacker** profile:

```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "profile": "hacker",
    "task": "Load campaign finance data for entity resolution. Use source_ingest or load CSV from /a0/usr/workdir/fec_donors.csv if available.",
    "context": "Preparing FEC donor dataset for fuzzy matching against SEC registrants"
  }
}
```

**Output requirement:** Hacker must confirm datasets are loaded with:
- Dataset paths (A and B)
- Record counts for both
- Field names used for matching

---

## Phase 2: Entity Resolution Execution

Execute the cross-dataset fuzzy matching using the native `entity_resolve` tool:

```json
{
  "tool_name": "entity_resolve",
  "tool_args": {
    "dataset_a_path": "/a0/usr/workdir/fec_donors.csv",
    "dataset_b_path": "/a0/usr/workdir/sec_registrants.csv",
    "match_field_a": "donor_name",
    "match_field_b": "company_name", 
    "threshold": 0.85
  }
}
```

**Alternative:** If the tool is unavailable, invoke the collector directly via code_execution_tool:

```python
import sys
sys.path.insert(0, '/a0/usr/workdir/phase2_collectors')
from entity_resolver import EntityResolverCollector

resolver = EntityResolverCollector(
    dataset_a_path='/a0/usr/workdir/fec_donors.csv',
    dataset_b_path='/a0/usr/workdir/sec_registrants.csv',
    threshold=0.85,
    match_field_a='donor_name',
    match_field_b='company_name'
)

matches = resolver.collect()
for m in matches:
    print(f"Match: {m['matched_entity_a']} -> {m['matched_entity_b']} ({m['confidence_score']:.1%})")
```

**Output requirement:** The entity resolution must return evidence chains containing:
- Confidence score (>= 0.85 for high-confidence, < 0.85 flagged as potential false positive)
- Matched entities from both datasets with full record details
- Normalized forms used for matching
- Investigation key for tracking across recursive steps

---

## Phase 3: Evidence Chain Persistence and Analysis

Every match found in Phase 2 must be saved to memory before proceeding:

```json
{
  "tool_name": "memory_save",
  "tool_args": {
    "text": "{"evidence_chain_id": "chain_001", "confidence_score": 0.944, "entity_a": {"source": "fec_federal", "name": "Tech Solutions Inc.", "type": "donor"}, "entity_b": {"source": "sec_edgar", "name": "TechSolutions Inc", "ci"}}
    }
  }
}
```

Then use `call_subordinate` with the **researcher** profile to analyze cross-dataset patterns:

```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "profile": "researcher",
    "task": "Analyze evidence chains from memory. Look for shell company indicators: new LLCs with high donation amounts, single-industry conglomerates, or entities appearing in both FEC and SAM.gov datasets.",
    "context": "Investigation of potential campaign finance to government contract laundering"
  }
}
```

---

## Phase 4: Recursive Expansion (Optional)

If the investigation requires chain-following (OpenPlanter's recursive mode), use `call_subordinate` to spawn additional analysis steps:

**Level 1 → Level 2 recursion:**
When a high-confidence match is found (>=0.90), extract the entity ID from Dataset B and query against Dataset C:

```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "profile": "hacker",
    "task": "Using the SEC CIK number {cik_number} found in evidence chain {chain_id}, query the SAM.gov vendor database for government contracts. Return all contracts exceeding $100,000.",
    "context": "Expanding investigation from campaign finance → corporate registry → government contracts"
  }
}
```

**Termination conditions:**
- **Depth limit**: Maximum 3 levels (Dataset A → B → C)
- **Evidence saturation**: Stop when no new unique entities are found in the current iteration
- **Confidence threshold**: Branches below 0.75 confidence should be flagged but not followed automatically

---

## Phase 5: Synthesis and Reporting

Aggregate all evidence chains from memory into a final investigation report:

```json
{
  "tool_name": "call_subordinate",
  "tool_args": {
    "profile": "researcher",
    "task": "Generate investigation summary using evidence chains in memory. Include: (1) Entity resolution confidence scores, (2) Cross-dataset links found, (3) Potential shell company indicators (new LLCs with high donations), (4) Recommendations for further verification.",
    "context": "Final report generation"
  }
}
```

**Output format:** The researcher must produce a Markdown report containing:
- Executive summary of entities and relationships discovered
- Evidence chain table with confidence scores
- Risk indicators (e.g., single-industry conglomerates, new entity formation dates)
- Source citations back to original datasets

---

## Phase 6: Cleanup and Memory Management

Before completing the investigation:

1. **Verify all matches saved**: Use `memory_load` with query "evidence_chain" to confirm no orphaned findings.
2. **Delete temporary data**: If using temporary CSVs, remove them after processing completes.
3. **Document gaps**: Note any datasets that could not be loaded or processed.

---

## Known Gaps

This skill adapts OpenPlanter's methodology but has these limitations:

- **No interactive visualization**: Unlike OpenPlanter's Tauri desktop app with knowledge graph visualization, this uses text-based memory and subordinate analysis. Visualizations would require external tools like `graphviz` or browser-based rendering.
- **Limited to standard library**: Uses Python `difflib.SequenceMatcher` for fuzzy matching instead of OpenPlanter's potentially more sophisticated algorithms (e.g., Levenshtein distance via external libraries).
- **No persistent graph database**: Entity relationships stored in memory are session-bound unless explicitly saved via `memory_save`. No Neo4j or similar persistence layer.

---

## What This Skill Does NOT Do

- Does not execute OpenPlanter's Python code directly. All logic is native Agent Zero code.
- Does not use external fuzzy matching libraries (rapidfuzz, python-Levenshtein). Uses standard library only.
- Does not provide interactive GUI visualization of entity networks.
- Does not perform real-time web scraping against FEC/SEC/SAM.gov APIs — requires pre-loaded datasets via `source_ingest` or local CSVs.
- Does not handle unstructured document analysis (PDF parsing, OCR) — assumes structured CSV/tabular input data.

---

## Example Invocation

**User request:** "Investigate connections between campaign donors in Massachusetts and federal government contractors."

**Agent Zero execution plan using this skill:**
1. **Phase 0**: Classify as horizontal cross-dataset investigation (FEC → SAM.gov)
2. **Phase 1**: Load FEC MA donor data via hacker profile subordinate
3. **Phase 2**: Run `entity_resolve` between fec_ma_donors.csv and sam_gov_vendors.csv (threshold=0.85)
4. **Phase 3**: Save matches to memory, spawn researcher subordinate for pattern analysis
5. **Phase 4**: Recursive expansion only if high-confidence matches found (>0.90)
6. **Phase 5**: Synthesize report with evidence chains and confidence scores
7. **Phase 6**: Memory verification and cleanup
