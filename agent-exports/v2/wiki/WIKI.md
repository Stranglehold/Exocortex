# EXOCORTEX WIKI SCHEMA
# This file defines how wiki pages are structured and maintained

## Page Types

### Concept Page (wiki/concepts/)
Required sections:
- **Definition** — what this concept means in the Exocortex context
- **How It Works** — mechanism or principle
- **Where It Appears** — which extensions, designs, or research reference this concept
- **Related Concepts** — [[wiki-links]] to other concept pages
- **Open Questions** — what we don't know yet
- **Sources** — papers, design notes, or team comms that informed this page

### Component Page (wiki/components/)
Required sections:
- **Purpose** — what problem this component solves
- **Architecture** — hook point, priority, data flow, what it reads/writes
- **Current Status** — deployed / designed / researched
- **Configuration** — what can be tuned, where config lives
- **Known Issues** — bugs, limitations, calibration gaps
- **Related Components** — [[wiki-links]] to components it interacts with
- **Design Lineage** — which research paper or incident motivated this component

### Research Page (wiki/research/)
Required sections:
- **Citation** — paper title, authors, venue, year, arXiv ID
- **Key Findings** — 3-5 bullet points, the essential results
- **Relevance to Exocortex** — how this connects to our architecture
- **What We Adopted** — findings that became design decisions or extensions
- **What We Deferred** — findings we noted but didn't act on, with reasoning
- **Connection to Other Papers** — [[wiki-links]] to related research pages

### Decision Page (wiki/decisions/)
Required sections:
- **Decision** — what was decided, stated clearly
- **Date** — when the decision was made
- **Context** — what problem prompted this decision
- **Options Considered** — alternatives that were evaluated
- **Rationale** — why this option was chosen
- **Outcome** — did it work? (update later with field data)
- **Related Decisions** — [[wiki-links]] to connected decisions

### Incident Page (wiki/incidents/)
Required sections:
- **Date** — when the incident occurred
- **What Happened** — description of the failure
- **Root Cause** — what caused it (determined after investigation)
- **Fix Applied** — what was done to resolve it
- **What It Motivated** — which design note, extension, or policy change resulted
- **Could It Recur?** — assessment of whether the fix is permanent

## Cross-Reference Rules
- Every concept page must link to at least one component that implements it
- Every component page must link to the research or incident that motivated it
- Every research page must link to concepts it introduced or validated
- Every decision page must link to the incident or finding that prompted it

## Lint Rules (for periodic audit)
- Orphan pages: no incoming links from other pages
- Missing pages: referenced in [[links]] but don't exist
- Stale pages: not updated in 30+ days, referencing active components
- Unresolved contradictions: flagged but not addressed
