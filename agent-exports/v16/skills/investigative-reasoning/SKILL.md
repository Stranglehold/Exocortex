---
name: "investigative-reasoning"
description: "Use this skill when investigating complex multi-source problems requiring entity resolution, cross-dataset linking, or public records correlation. Adapts OpenPlanter's methodology for Agent Zero investigations — joining disparate data sources through fuzzy matching and relationship inference. Triggers: 'investigate', 'find connections between', 'link these entities', 'cross-reference', 'entity resolution', 'follow the money'."
version: "1.0.0"
author: "Exocortex Adaptation Team"
tags: ["investigation", "entity-resolution", "cross-linking", "public-records", "forensics"]
trigger_patterns:
  - "investigate connections between"
  - "find links across"
  - "correlate these datasets"
  - "follow the money trail"
  - "resolve entity identity"
  - "cross-reference public records"
---

# Investigative Reasoning

## Purpose

This skill guides complex investigations requiring **entity resolution** and **cross-dataset correlation**. It adapts OpenPlanter's methodology — used to link Boston city councilors to campaign finance donors via vendor relationships — for Agent Zero's tool surface.

**Core capability:** Join disparate data sources (WHOIS, corporate registries, financial filings, DNS records) through fuzzy entity matching and relationship inference. Build connected graphs of ownership, funding flows, or infrastructure sharing.

**Key pattern:** When investigating X, ask: What other datasets might contain information about the same entities? How can I join them on names, addresses, phone numbers, email domains, or tax IDs?

## When to Use

Use this skill when:
- **Multi-source correlation required**: Needing to link entities across different databases (e.g., matching a domain registrant's name against campaign finance donors)
- **Identity resolution needed**: Same entity appears under slightly different names in different sources (fuzzy matching: "John Smith" vs. "J. Smith")
- **Graph construction required**: Building relationship networks between people, companies, domains, and infrastructure
- **Public records investigation**: Analyzing corporate registries, campaign finance data, contracts databases, or DNS records together

Do NOT use for:
- Single-source lookups (e.g., "Who owns this domain?") — use `domain_collector` directly
- Simple fact-checking without cross-referencing multiple datasets
- Tasks not requiring entity resolution or multi-dataset joins

---

## Methodology

### Phase 1: Define the Investigation Core

Start by identifying your **seed entities** (people, companies, domains) and the **hypothesis** you're testing.

```python
# code_execution_tool — document investigation scope
investigation = {
    "seed_entities": ["target_domain.com", "Suspect Name"],
    "hypothesis": "The domain registrant is connected to campaign finance contributions",
    "datasets_needed": ["WHOIS data", "Campaign Finance DB", "Corporate Registry"],
    "join_keys": ["name", "address", "phone_number"]  # Fields for fuzzy matching
}
```

### Phase 2: Multi-Source Data Acquisition

Collect relevant datasets from multiple sources. OpenPlanter demonstrates joining:
1. **Boston City Council candidate list** (CPF IDs, names, offices)
2. **OCPF campaign finance data** (donors, employers, contributions)
3. **Open Checkbook vendor registry** (company names, addresses)
4. **Corporate filings** (MA Secretary of State for corporate officers)

For Agent Zero investigations:
- Use `domain_collector` to extract WHOIS registrants and DNS records
- Use `company_collector` for business registrations
- Use `people_collector_enhanced` for data breach and social footprint data
- Acquire external datasets via browser_agent or document_query if available locally

**Example**: Extract email domains from WHOIS, then join against corporate registry to find other companies owned by the same registrant.

### Phase 3: Entity Resolution (The Core Step)

This is where you **normalize names and addresses** across sources before joining. OpenPlanter's approach:

```
1. Extract CPF IDs from candidates.txt → load into dict {cpf_id -> full_name}
2. Load OCPF contributions with donor names
3. Fuzzy-match candidate names to donor names using Levenshtein distance or simple substring matching
4. Link on CPF ID when exact match found, link on name similarity otherwise
```

For Agent Zero:
- Normalize names: Remove suffixes (Jr., III), expand initials, standardize punctuation
- Normalize addresses: Standardize street abbreviations (St vs Street), remove directionals (N vs North)
- Extract join keys: Parse phone numbers to E.164 format, extract email domains, parse tax IDs

**Example Entity Resolution Code Pattern:**

```python
# code_execution_tool — fuzzy matching logic from OpenPlanter adapted for A0
import difflib
from collections import defaultdict

def normalize_name(name):
    """Remove suffixes and standardize."""
    name = name.replace("'s", "")  # Remove possessive
    return name.lower().strip()

def find_best_match(target_name, candidate_list, threshold=0.75):
    """Find best fuzzy match across list."""
    target = normalize_name(target_name)
    for candidate in candidate_list:
        if difflib.SequenceMatcher(None, target, normalize_name(candidate)).ratio() >= threshold:
            return candidate
    return None
```

### Phase 4: Cross-Linking Analysis

Once entities are resolved across datasets, **build relationship edges**.

OpenPlanter's approach:
- **Primary link**: Candidate CPF ID → Campaign contributions (direct)
- **Secondary link**: Donor employer name ↔ Vendor company name (fuzzy match on names and addresses)
- **Tertiary link**: Corporate officer names ↔ Registrant names (identity resolution across registries)

For Agent Zero, construct relationships:
1. **Ownership edges**: Domain registrant → Company owner (same name/address)
2. **Infrastructure edges**: Domain A → Domain B (shared WHOIS email or DNS server)
3. **Financial edges**: Person X → Campaign donor to Candidate Y (via campaign finance data)
4. **Employment edges**: Person X → Employer Z (from corporate registry)

**Example Relationship Inference:**
```
IF domain registrant.name == campaign_donor.name AND 
   domain registrant.address ~= campaign_donor.address (within 50 chars) THEN
   Create relationship: Domain —[REGISTERED_BY]→ Person —[DONATED_TO]→ Candidate
```

### Phase 5: Finding Synthesis

Generate **investigative findings** by identifying high-value paths in the graph:
- **Cycles**: A → B → C → A (ownership loops indicating shell companies)
- **Shared infrastructure**: Multiple domains with same registrant email (likely related)
- **Temporal patterns**: Registrations clustered around campaign finance filing deadlines
- **Geographic clusters**: Entities sharing city/zip codes indicating physical proximity

---

## Agent Zero Tool Mapping

| OpenPlanter Capability | Agent Zero Equivalent |
|------------------------|---------------------|
| Load Boston candidates from TSV | `domain_collector` (WHOIS extraction) + `document_query` (local data files) |
| Fuzzy name matching across datasets | Python `difflib.SequenceMatcher` or custom entity resolution in `code_execution_tool` |
| Link donors to vendors via employer names | `company_collector` + manual join logic |
| Corporate officer lookup | Browser scraping of Secretary of State sites OR local database joins |

**Key difference:** OpenPlanter uses bulk file loads (TSV/CSV). Agent Zero typically queries APIs or individual lookups. For bulk analysis, download datasets first via `browser_agent`, then use `code_execution_tool` for pandas-style operations.

---

## Example Investigation: Domain to Political Connection

**Hypothesis**: A suspicious domain is registered by someone connected to local politics.

1. **Collect WHOIS data** → Extract registrant name ("Acme Corp") and address ("123 Main St, Boston")
2. **Query Campaign Finance DB** → Search for donors named "Acme" or located at "Main St, Boston"
3. **Entity Resolution** → Fuzzy match "Acme Corporation" with "ACME CORP" in campaign finance data
4. **Cross-Link** → Found: Acme donated $50k to Councilor X; same address matches vendor in city contracts
5. **Synthesis** → Finding: Domain registrant is a major political donor and city vendor, potential conflict of interest.

---

## Security Rules — Non-Negotiable

1. **No PII retention**: Do not store personally identifiable information beyond the scope of this investigation session.
2. **Public records only**: Use only publicly available data sources. Do not access password-protected systems or private databases without explicit authorization.
3. **Data provenance tracking**: Always document source URLs and extraction timestamps for legal defensibility.
4. **Fuzzy match confidence scoring**: When fuzzy matching names across datasets, report the similarity score (e.g., "85% match on address"). Do not treat low-confidence matches as definitive.

---

## What This Skill Does NOT Do

- Does not perform automated entity resolution without human review — always verify fuzzy matches
- Does not scrape behind paywalls or login walls — uses only public, freely accessible data
- Does not claim legal conclusions (e.g., "this proves corruption") — reports factual connections only
- Does not replace the need for `domain_collector`, `company_collector`, etc. — orchestrates their output

---

## Example Invocation

> "Investigate whether the registrant of suspicious-domain.com appears in Massachusetts campaign finance records as a donor or vendor. Use entity resolution to link across datasets."

**Expected workflow:**
1. Call `domain_collector` on suspicious-domain.com → extract registrant name/address/email
2. Check local OCPF campaign finance dataset (or fetch via browser_agent if not cached)
3. Normalize names and fuzzy-match against donor list and vendor list
4. Report any matches with similarity scores and full entity details
5. Synthesize findings into a relationship graph description.
