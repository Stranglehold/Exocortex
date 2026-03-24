# COUNTER-PATRIOTS — Standalone Application Architecture

**Status:** Pre-spec exploration with implementation-ready core components.  
**Informed by:** Spec A (Eitan, team theoretical document), Gracie Mansion founding case study, Exocortex DEC-014 (integration complexity determines integration pattern).  
**What this is:** Architecture for Counter-Patriots as a standalone A2A peer service. Agent Zero queries it; it doesn't live inside Agent Zero.  
**What's missing:** Live RSS validation, production retcon rates, silence detection accuracy benchmarks.

---

## Why Standalone

DEC-014: Complex peer frameworks communicate via A2A protocol as independent services. Counter-Patriots has its own database, its own ingestion pipeline, its own reasoning layer, its own temporal model. Absorbing it into Agent Zero would flatten the capabilities that make it valuable. Same logic as the OpenPlanter analysis: the investigation engine stays intact, the coordination layer stays lean.

The interface is query-based. Agent Zero asks: "drift report on Hormuz attribution since March 1." Counter-Patriots returns the record. The analyst holds the conclusions.

---

## The Adversarial Model

You cannot build a detection system without a precise model of what you are detecting. The system targets three mechanisms that operate simultaneously in the current information environment:

**Desire-based framing** (Bernays/Lippmann lineage): Messages connected to what people already want, fear, or value. The target is the pre-rational emotional substrate. Detection signal: activation patterns — narrative spikes across ideologically distinct outlets within narrow time windows.

**Fracture amplification** (Soviet/active measures lineage): Amplifying existing social tensions until the target society's energy goes into fighting itself. The goal isn't belief adoption — it's division. Detection signal: topic threading — when the same fracture point appears across sources that would not ordinarily coordinate.

**Emergent context management** (algorithmic lineage): No coordinator required. Individual actors making locally reasonable decisions produce a collectively managed information environment. The commissioner notes ISIS affiliation. The reporter files on deadline. The outlet runs the Iran war angle. The architecture runs itself. Detection signal: drift — claims that change over time without acknowledgment.

**The silence mechanism:** The most important function. Not what was said, but what was NOT said. The Sunni/Shia doctrinal conflict between claimed ISIS affiliation and Iran war target selection. The correction that never arrived. Detection requires a completeness model: what should be present in a complete account.

---

## Design Constraints (Architectural, Not Conventional)

### Constraint 1: The Curtis Rule
*The system must not become what it opposes.*

Counter-Patriots records. It does not narrate. It does not generate counter-framings. It does not adjudicate truth. The output is the timestamped record of what was said, what changed, and what's missing. Conclusions belong to the analyst.

**Architectural enforcement:** No generation endpoint. No "suggest alternative framing" function. No confidence score on truth/falsehood of claims. The query interface returns records, not assessments. This is not a usage guideline that can be relaxed. It is a missing API endpoint that cannot be called because it doesn't exist.

### Constraint 2: The Festinger Boundary
*Contradicting evidence can strengthen belief under certain conditions.*

The contradiction ledger is an analyst tool, not a public-facing instrument. When a belief is identity-linked, contradiction activates motivated reasoning rather than updating. Deploying contradictions to committed audiences risks backfire.

**Architectural enforcement:** The contradiction ledger has no public API. Access requires analyst authentication. No batch export of contradictions. No RSS feed of detected contradictions. The data exists for the analyst's eyes, queryable on demand, not broadcast.

### Constraint 3: The Inoculation Principle
*Pre-exposure to manipulation techniques in weakened form produces measurable resistance.*

The system's most important downstream function is enabling inoculation — showing how a manipulation technique works before the audience encounters the real thing. This operates through the analyst layer (journalists, researchers, officials), not through the system directly.

**Architectural enforcement:** The system exposes technique classification alongside claims. When a claim is flagged, the classification includes which manipulation technique it matches (pre-suasion framing, fracture amplification, emergent context management, silent omission). The analyst can use these classifications to construct inoculation materials. The system provides the raw material. The human constructs the inoculation.

---

## Core Architecture

```
┌─────────────────────────────────────┐
│         COUNTER-PATRIOTS            │
│        Standalone Service           │
│                                     │
│  ┌──────────┐    ┌───────────────┐  │
│  │ Ingestion │───>│  Claim Store  │  │
│  │ Pipeline  │    │  (PostgreSQL) │  │
│  └──────────┘    └───────┬───────┘  │
│                          │          │
│  ┌──────────┐    ┌───────┴───────┐  │
│  │  FAISS   │<───│  Embedding    │  │
│  │  Index   │    │  Layer        │  │
│  └────┬─────┘    └───────────────┘  │
│       │                             │
│  ┌────┴──────────────────────────┐  │
│  │     Analysis Engines          │  │
│  │  ┌────────┐ ┌──────────────┐  │  │
│  │  │ Contra- │ │  Silence     │  │  │
│  │  │ diction │ │  Detection   │  │  │
│  │  │ Detector│ │  (Comp.Comp.)│  │  │
│  │  └────────┘ └──────────────┘  │  │
│  │  ┌────────┐ ┌──────────────┐  │  │
│  │  │ Drift  │ │  Activation  │  │  │
│  │  │ Tracker│ │  Patterns    │  │  │
│  │  └────────┘ └──────────────┘  │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │     A2A Query Interface       │  │
│  │     (JSON over HTTP)          │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
          ▲                  │
          │    A2A Protocol  │
          │                  ▼
┌─────────────────────────────────────┐
│          AGENT ZERO                 │
│  "Show me drift on Hormuz since    │
│   March 1" → structured query →    │
│   receives JSON record             │
└─────────────────────────────────────┘
```

---

## Schema

```sql
-- Sources: one row per outlet
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,           -- 'official', 'wire', 'outlet', 'social'
    cluster TEXT NOT NULL,               -- ideological cluster: 'left', 'center', 'right', 'wire', 'official'
    confidence_score FLOAT DEFAULT 0.7,
    acknowledged_retcon_count INT DEFAULT 0,
    silent_retcon_count INT DEFAULT 0,
    total_claims INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Claims: append-only, never updated
CREATE TABLE claims (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id),
    raw_text TEXT NOT NULL,
    claim_text TEXT NOT NULL,
    article_url TEXT NOT NULL,
    article_title TEXT,
    topic_tag TEXT,
    technique_class TEXT,               -- 'presuasion', 'fracture', 'emergent', 'direct', 'none'
    extracted_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    faiss_id INT
);

-- Contradictions: pairs with relationship classification
CREATE TABLE contradictions (
    id SERIAL PRIMARY KEY,
    claim_a_id INT REFERENCES claims(id),
    claim_b_id INT REFERENCES claims(id),
    relationship TEXT NOT NULL,         -- 'contradiction', 'retcon_silent', 'retcon_acknowledged', 'elaboration'
    confidence FLOAT NOT NULL,
    source_acknowledged BOOLEAN DEFAULT FALSE,
    analyst_reviewed BOOLEAN DEFAULT FALSE,
    technique_class TEXT,               -- which manipulation pattern this matches
    flagged_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

-- Silence flags: comparative completeness
CREATE TABLE silence_flags (
    id SERIAL PRIMARY KEY,
    topic_tag TEXT NOT NULL,
    element TEXT NOT NULL,              -- the missing element
    present_in_sources INT[],          -- source IDs that include this element
    absent_from_sources INT[],         -- source IDs that omit this element
    first_detected TIMESTAMP DEFAULT NOW(),
    detection_method TEXT NOT NULL,     -- 'comparative', 'template', 'pattern'
    analyst_reviewed BOOLEAN DEFAULT FALSE
);

-- Activation patterns: narrative spikes
CREATE TABLE activation_patterns (
    id SERIAL PRIMARY KEY,
    topic_tag TEXT NOT NULL,
    claim_pattern TEXT NOT NULL,        -- the narrative being tracked
    source_ids INT[],                  -- sources where it appeared
    cluster_spread INT,                -- how many distinct clusters it appeared in
    first_seen TIMESTAMP,
    window_minutes INT,                -- time window of appearance
    flagged_at TIMESTAMP DEFAULT NOW()
);
```

### Key Schema Differences from Spec B

1. **`cluster` field on sources.** Spec B has no ideological clustering. Without it, comparative completeness is impossible — you can't detect what one cluster omits unless you know which cluster each source belongs to.

2. **`silence_flags` table exists from day one.** Spec B defers silence detection to Phase 2. We include it because the schema design changes if you're tracking absence from the start. The `present_in_sources` / `absent_from_sources` arrays are the core data structure for comparative completeness.

3. **`retcon_silent` vs `retcon_acknowledged` distinction.** Spec B has a single `retcon` category. We split it because a source that openly corrects itself is doing journalism; a source that silently changes its story is doing something the system is specifically designed to detect. The confidence update must distinguish these.

4. **`technique_class` on claims and contradictions.** Spec B doesn't classify which manipulation technique a claim matches. We do, because the inoculation function requires knowing which technique to inoculate against.

5. **`activation_patterns` table.** Spec B doesn't track narrative spikes across outlets. We do, because emergent context management — the founding case study's core finding — is only visible when you track simultaneous appearance across ideologically distinct clusters.

---

## Silence Detection: Comparative Completeness

This is the hardest problem and the most important function. Spec A identified it. Spec B deferred it. We solve it.

### Method

For each topic_tag, maintain a running inventory of elements that appear in coverage across all sources. When source cluster A consistently includes an element that cluster B omits, flag the omission.

```python
def detect_silence(topic_tag: str, time_window_hours: int = 24):
    """
    For a given topic, find elements present in some source clusters
    but absent from others.
    """
    # Get all claims for this topic within the time window
    claims = get_recent_claims(topic_tag, hours=time_window_hours)
    
    # Extract elements per cluster
    # Elements = sub-claims, entities, relationships within the claims
    cluster_elements = {}
    for claim in claims:
        cluster = get_source_cluster(claim.source_id)
        elements = extract_elements(claim.claim_text)  # LLM call
        cluster_elements.setdefault(cluster, set()).update(elements)
    
    # Find elements present in some clusters but absent from others
    all_elements = set().union(*cluster_elements.values())
    
    silence_flags = []
    for element in all_elements:
        present_clusters = [c for c, elems in cluster_elements.items() if element in elems]
        absent_clusters = [c for c, elems in cluster_elements.items() if element not in elems]
        
        # Flag if element appears in 2+ clusters but is absent from 1+
        if len(present_clusters) >= 2 and len(absent_clusters) >= 1:
            silence_flags.append({
                'element': element,
                'present_in': present_clusters,
                'absent_from': absent_clusters,
                'topic': topic_tag
            })
    
    return silence_flags
```

### Element Extraction Prompt

```
SYSTEM: You extract discrete factual elements from a news claim.
An element is a single piece of information: an entity, a relationship, 
a attribution, a quantitative claim, or a contextual fact.
Return ONLY a JSON array of strings. No preamble.

Example:
Claim: "NYPD Commissioner Tisch said the suspect had ISIS ties 
but no connection to the Iran war"
Elements: [
  "suspect had ISIS ties",
  "statement attributed to Commissioner Tisch",
  "no connection to Iran war stated",
  "NYPD is the attributing agency"
]

USER: Extract elements from:
[CLAIM TEXT]
```

### Why This Is Cross-Recurrence

The method is structurally identical to CRQA applied to news corpora. In our chatlog analysis, cross-recurrence finds moments where two speakers' trajectories pass through the same region of embedding space. In Counter-Patriots, comparative completeness finds moments where two source clusters' coverage *fails* to pass through the same information space. Presence detection and absence detection are the same geometry viewed from opposite sides.

---

## Source Confidence: Acknowledged vs Silent

```python
def update_confidence(source_id: int, window_days: int = 30):
    """
    Confidence update that distinguishes acknowledged corrections 
    from silent retcons.
    """
    stats = get_retcon_stats(source_id, days=window_days)
    
    # Silent retcons damage confidence
    silent_rate = stats['silent_retcons'] / max(stats['total_claims'], 1)
    
    # Acknowledged retcons are neutral or slightly positive
    # (indicates editorial accountability)
    ack_rate = stats['acknowledged_retcons'] / max(stats['total_claims'], 1)
    
    # Decay toward observed behavior
    current = get_confidence(source_id)
    
    # Silent retcons pull confidence down
    # Acknowledged retcons have no negative effect
    # Clean record slowly pulls confidence up
    adjustment = -silent_rate * 0.3 + (1 - silent_rate) * 0.02 + ack_rate * 0.01
    
    new_confidence = max(0.1, min(0.99, current + adjustment))
    
    update_source_confidence(source_id, new_confidence)
```

### Why This Matters

Spec B's formula (`confidence * 0.95 + (1 - retcon_rate) * 0.05`) treats Reuters issuing a correction the same as a source silently editing a story. That's exactly the distinction Counter-Patriots exists to detect. The `source_acknowledged` boolean is in Spec B's schema but never used in the confidence calculation. Ours uses it because the theoretical understanding (Spec A) tells us why the distinction matters.

---

## A2A Query Interface

```python
# Query types — JSON over HTTP
# Agent Zero calls these endpoints

@app.route('/api/drift', methods=['POST'])
def drift_query():
    """Claims from a source on a topic over time, with contradiction flags."""
    # Input: { source: str, topic: str, since: ISO datetime }
    # Output: { claims: [...], contradiction_count: int, silent_retcon_count: int }

@app.route('/api/contradictions', methods=['POST'])
def contradiction_query():
    """Contradiction ledger for a source or topic."""
    # Input: { source?: str, topic?: str, since: ISO datetime }
    # Output: { pairs: [...], by_type: { contradiction: N, silent_retcon: N, acknowledged: N } }
    # NOTE: Requires analyst auth token. No public access. (Festinger Boundary)

@app.route('/api/silence', methods=['POST'])
def silence_query():
    """Silence flags — what's missing from coverage."""
    # Input: { topic: str, since: ISO datetime }
    # Output: { flags: [...], by_cluster: { left: [...], right: [...], ... } }

@app.route('/api/activation', methods=['POST'])
def activation_query():
    """Narrative spikes across ideologically distinct outlets."""
    # Input: { topic?: str, since: ISO datetime, min_cluster_spread: int }
    # Output: { patterns: [...], by_topic: { ... } }

@app.route('/api/record', methods=['POST'])
def full_record():
    """Complete timestamped record for an event."""
    # Input: { topic: str, since: ISO datetime }
    # Output: { claims: [...], contradictions: [...], silences: [...], activations: [...] }
    # The founding case study output. The record, complete and timestamped.

@app.route('/api/health', methods=['GET'])
def health():
    """Service health for A2A discovery."""
    # Output: { status: 'operational', claims_count: N, sources_count: N, last_ingestion: ISO }
```

---

## What This Produces That Spec B Cannot

If both versions had been running during the Gracie Mansion incident:

**Spec B would produce:**
- Claim timeline (Tisch statement, ISIS connection, no Iran link)
- Contradiction flag (same outlet running conflicting frames)
- Drift report

**Our version would additionally produce:**
- Silence flag: Tisch statement covers ISIS affiliation but no source in any cluster addresses Sunni/Shia doctrinal conflict with target selection (comparative completeness detected the absence)
- Activation pattern: ISIS/terrorism framing across 14 outlets spanning 4 ideological clusters within 72 minutes (emergent context management signature)
- Technique classification: pre-suasion framing (the ISIS frame captures attention before the analytical question can be asked)
- Distinguished confidence impact: outlets that later corrected would get acknowledged_retcon (neutral), outlets that silently shifted framing would get silent_retcon (confidence penalty)

The delta is the data. The theoretical understanding produces a structurally different system.

---

## Implementation Plan

**Phase 1 — Core (Week 1):**
- PostgreSQL schema with all tables (including silence_flags and activation_patterns)
- RSS ingestion pipeline with cluster-tagged sources
- FAISS embedding index (all-MiniLM-L6-v2, 384 dims)
- Claim extraction via LM Studio
- Contradiction detection with silent/acknowledged split
- A2A health endpoint

**Phase 2 — Analysis Engines (Week 2):**
- Silence detection (comparative completeness)
- Activation pattern detection (cross-cluster narrative spikes)
- Technique classification on claims
- Full A2A query interface (all 5 endpoints)

**Phase 3 — Integration (Week 3):**
- Agent Zero A2A registration
- Query routing from Agent Zero to Counter-Patriots
- Analyst authentication for contradiction ledger
- Automated ingestion scheduler

---

## Founding Topic Thread

Iran/Hormuz coverage. Current analytical context makes this the obvious candidate. Retroactive ingestion of archived articles establishes the baseline. Live ingestion begins on deployment. The system validates on a narrow corpus before scaling.

---

*Counter-Patriots — Team Architecture — March 2026*
*The record, and nothing but the record.*
*The delta is the data.*
