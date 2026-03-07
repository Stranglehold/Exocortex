# Epistemic Integrity Layer — Design Note

**Status:** Design note. Pre-spec exploration.
**Motivated by:** ST-003 — GPT-OSS-20B fabricated a complete Oracle credit risk report with zero source data, expressing high confidence in every claim. Every financial figure was wrong. Every source attribution was invented.
**Related systems:** Error Comprehension (negative knowledge), Compound BST (positive knowledge), Evidence Ledger (new).
**Depends on:** Tool execution logging (exists). BST domain classification (exists). Timestamp injection (trivial to add).

---

## The Problem

Language models do not know what they don't know. When a model generates "Oracle's total debt is approximately $30 billion," it has no internal mechanism to distinguish between:

- A figure it learned from training data that was accurate at time of training
- A figure it learned from training data that has since changed
- A figure it generated because "$30 billion" is a plausible-sounding number after "Oracle's total debt is approximately"
- A figure it retrieved from a source during this session

All four produce the same output. The model expresses the same confidence for all four. The operator has no way to distinguish them from the output alone.

ST-003 demonstrated this concretely. The agent:
- Never successfully queried any data source (tool formatting failures blocked all API calls)
- Produced a structured credit risk report with specific dollar amounts, ratios, ratings, and growth percentages
- Labeled fabricated data as "High confidence — data from SEC filings and Bloomberg snapshots"
- Was explicitly instructed "do not fabricate data — if you can't verify a number, say so explicitly"
- Ignored the instruction because confabulation isn't a choice the model makes — it's a structural property of autoregressive generation

This is not fixable at the model level. It is fixable at the system level.

---

## Design Principles

1. **The model doesn't need to know what it doesn't know. The system does.** We track what data entered the session, what kind of knowledge each claim represents, and when the session is occurring. The model generates freely. The system annotates after.
2. **Three-axis classification.** Every factual claim is assessed on three independent axes: provenance (did this data come from a source?), volatility (how fast does this kind of knowledge change?), and temporal distance (how far is "now" from when the model could have learned this?).
3. **Deterministic only.** No LLM calls for classification. Regex for claim extraction, lookup tables for volatility, arithmetic for temporal distance.
4. **Additive annotation, not censorship.** The system does not suppress or rewrite model output. It appends grounding annotations that the operator (human or downstream system) uses to assess trustworthiness. The model's full output is preserved.
5. **Composable with existing stack.** Reads BST domain classification for default volatility assumptions. Reads tool execution logs for the evidence ledger. Writes annotations to shared state where the operator, supervisor, or future systems can consume them.

---

## Architecture: Three Components

### Component 1: Evidence Ledger

**What it does:** Maintains a running record of every piece of external data that entered the agent's context during this session. This is the "chain of custody" — if data appears in the model's output but not in the ledger, it didn't come from a source.

**What counts as evidence:**
- Tool execution outputs (command results, API responses, file reads)
- Search results (web search, database queries)
- Retrieved memories (from FAISS, with retrieval timestamp)
- User-provided data (documents, URLs, pasted content)

**What does NOT count:**
- The model's own previous outputs (these are claims, not evidence)
- System prompt content (configuration, not data)
- BST enrichment (guidance, not data)

**Mechanism:**

```python
class EvidenceLedger:
    """
    Populated by tool_execute_after hook.
    Each entry records what data entered the session and when.
    """
    
    def __init__(self):
        self.entries = []  # list of EvidenceEntry dicts
    
    def record(self, source_type, source_id, content_summary, 
               raw_content, timestamp):
        """
        Called after every successful tool execution, file read,
        search result, or memory retrieval.
        """
        entry = {
            "source_type": source_type,     # "tool_output", "file_read", "search", "memory", "user_input"
            "source_id": source_id,          # tool name, file path, search query, memory ID
            "content_summary": content_summary,  # first 500 chars for matching
            "timestamp": timestamp,
            "key_values": extract_key_values(raw_content)  # numbers, names, dates found in source
        }
        self.entries.append(entry)
    
    def find_provenance(self, claim_value):
        """
        Search ledger for a specific value (number, name, date).
        Returns list of matching entries or empty list.
        """
        matches = []
        for entry in self.entries:
            if claim_value in entry["key_values"]:
                matches.append(entry)
        return matches
```

**Key value extraction from sources:**

```python
def extract_key_values(raw_content):
    """
    Pull numbers, currency amounts, percentages, dates, 
    proper nouns from source data. These become the searchable
    index for provenance checking.
    """
    values = set()
    
    # Currency amounts: $30 billion, $1.5B, $800 million
    for match in re.findall(r'\$[\d,.]+\s*(?:billion|million|trillion|[BMT])\b', 
                            raw_content, re.IGNORECASE):
        values.add(normalize_currency(match))
    
    # Percentages: 25%, 0.88, 92.5%
    for match in re.findall(r'\d+\.?\d*\s*%', raw_content):
        values.add(match.strip())
    
    # Ratios: 1.5x, 2.8×, 1.9:1
    for match in re.findall(r'\d+\.?\d*\s*[x×]|\d+\.?\d*:\d+', raw_content):
        values.add(match.strip())
    
    # Dates: Q3 2024, FY2025, 2022, March 2024
    for match in re.findall(r'(?:Q[1-4]\s*)?(?:FY\s*)?20\d{2}', raw_content):
        values.add(match.strip())
    
    # Credit ratings: AA-, Baa1, BBB+
    for match in re.findall(r'\b[A-D][a-z]*[+-]?\d?\b', raw_content):
        if len(match) >= 2:
            values.add(match)
    
    return values
```

**Integration point:** Hook into existing tool execution logging. Every tool output already flows through `tool_execute_after`. The evidence ledger taps the same pipeline — after Error Comprehension runs, the ledger records what data came back. Zero new hooks needed.

---

### Component 2: Epistemological Classifier

**What it does:** Classifies each factual claim in the model's output by temporal volatility — how quickly this kind of knowledge changes in the real world.

**The taxonomy:**

| Class | Volatility | Staleness Clock | Examples |
|-------|-----------|-----------------|----------|
| **Structural** | Near-zero | Decades to centuries | Physical constants, mathematical theorems, historical founding dates, protocol specifications, geographic facts |
| **Institutional** | Low | Years to multi-year | Credit ratings, company leadership, headquarters location, employee count, regulatory status |
| **Cyclical** | Moderate | Quarterly to annually | Revenue figures, debt totals, annual growth rates, fiscal year metrics, market share |
| **Transactional** | High | Daily to weekly | Recent earnings, bond issuances, analyst reports, news events, policy changes |
| **Ephemeral** | Extreme | Minutes to hours | Stock prices, exchange rates, live market data, breaking news, current weather, real-time system status |

**Signal patterns for classification:**

```python
VOLATILITY_SIGNALS = {
    "ephemeral": {
        "patterns": [
            r"(?i)(right now|currently trading|as of (today|this morning))",
            r"(?i)(spot price|market price|live|real-?time)",
            r"(?i)(latest|just (released|announced|reported))",
            r"(?i)(today'?s?|this (morning|afternoon|hour))",
        ],
        "staleness_clock": "hours",
        "max_plausible_age_hours": 1,
    },
    "transactional": {
        "patterns": [
            r"(?i)(issued|filed|reported|announced).{0,30}20\d{2}",
            r"(?i)(recent|new|upcoming)\s+(bond|issuance|offering|filing)",
            r"(?i)(downgrad|upgrad|revis|chang).{0,20}(rating|outlook)",
            r"(?i)(earnings|results|quarter).{0,15}(beat|miss|met|exceeded)",
        ],
        "staleness_clock": "weeks",
        "max_plausible_age_hours": 168,  # 1 week
    },
    "cyclical": {
        "patterns": [
            r"(?i)\$[\d,.]+\s*(?:billion|million|trillion)",
            r"(?i)(revenue|income|earnings|EBITDA|FCF).{0,20}\d",
            r"(?i)(debt[- ]to[- ]equity|leverage|coverage)\s*(ratio)?\s*[~:]?\s*\d",
            r"(?i)\d+\.?\d*\s*%\s*(YoY|year[- ]over|growth|decline)",
            r"(?i)(Q[1-4]|FY)\s*20\d{2}",
            r"(?i)(total debt|outstanding debt|long[- ]term debt)",
            r"(?i)(market (cap|share|position)).{0,15}\d",
        ],
        "staleness_clock": "months",
        "max_plausible_age_hours": 2160,  # ~90 days / 1 quarter
    },
    "institutional": {
        "patterns": [
            r"(?i)(rated|rating).{0,30}(Moody|S&P|Fitch|DBRS)",
            r"(?i)(CEO|CFO|CTO|chairman|president|director)\s+(is|was|named)",
            r"(?i)(headquartered|based|located)\s+in",
            r"(?i)(employees?|headcount|workforce).{0,15}\d{3,}",
            r"(?i)(subsidiary|division|segment)\s+(of|within)",
        ],
        "staleness_clock": "years",
        "max_plausible_age_hours": 8760,  # 1 year
    },
    "structural": {
        "patterns": [
            r"(?i)(founded|established|incorporated)\s+in\s+\d{4}",
            r"(?i)(law|theorem|principle|constant|equation)\s+(of|states|is)",
            r"(?i)(protocol|standard|specification)\s+(defines|requires|is)",
            r"(?i)(always|never|by definition|fundamentally)",
        ],
        "staleness_clock": "decades",
        "max_plausible_age_hours": 87600,  # 10 years
    },
}
```

**Classification logic:**

```python
def classify_claim(claim_text, task_domain=None):
    """
    Classify a factual claim by temporal volatility.
    First signal match wins — most volatile category checked first.
    Default based on task domain if no signals match.
    """
    # Check from most volatile to least volatile
    for volatility_class in ["ephemeral", "transactional", "cyclical", 
                              "institutional", "structural"]:
        config = VOLATILITY_SIGNALS[volatility_class]
        for pattern in config["patterns"]:
            if re.search(pattern, claim_text):
                return volatility_class, config
    
    # No signal matched — default based on task domain
    DOMAIN_DEFAULTS = {
        "investigation": "cyclical",      # financial/entity data assumed quarterly
        "analysis": "cyclical",           # analytical claims about metrics
        "research": "institutional",      # research findings change slowly
        "coding": "structural",           # technical facts are stable
        "bugfix": "structural",           # error patterns are stable
        "system_admin": "structural",     # system configs are stable
        "conversation": "institutional",  # general knowledge, moderate staleness
        "planning": "institutional",      # plans reference current state
    }
    
    default = DOMAIN_DEFAULTS.get(task_domain, "institutional")
    return default, VOLATILITY_SIGNALS[default]
```

**Compound BST integration:** When compound BST is deployed, the epistemological classifier reads *both* domains and uses the more volatile default. An `investigation + coding` compound defaults to `cyclical` (from investigation) rather than `structural` (from coding). The more skeptical assumption wins. This is correct — if any aspect of the task involves time-sensitive data, the claims should be treated with higher scrutiny.

---

### Component 3: Temporal Anchor

**What it does:** Injects the current timestamp into the agent's context at session start and maintains a temporal reference that enables staleness computation.

**Why the model needs this:** Without a timestamp, the model has no reference point for assessing its own knowledge age. It doesn't know when "now" is. A model trained on data through May 2025 doesn't know it's operating in February 2026 unless told. And even when told, autoregressive generation doesn't reliably use that information to modulate confidence. But the *system* can use the timestamp to compute staleness scores for claims.

**Why granularity matters:** Jake's stock price example is precise. A query at 9:00 AM and the same query at 9:30 AM have different staleness requirements. The temporal anchor isn't just a date stamp — it's a reference clock that the epistemological classifier uses to compute time-since-plausible-validity for each claim class.

**Mechanism:**

```python
class TemporalAnchor:
    """
    Injected at session start. Provides reference time for 
    staleness computation and context injection for the model.
    """
    
    def __init__(self):
        self.session_start = datetime.now(timezone.utc)
        self.model_training_cutoff = None  # loaded from model profile
        self.last_update = self.session_start
    
    def load_from_profile(self, model_profile):
        """
        Model profiles should include training_data_cutoff.
        If not present, assume 6 months before profile creation.
        """
        cutoff = model_profile.get("training_data_cutoff")
        if cutoff:
            self.model_training_cutoff = parse_datetime(cutoff)
        else:
            evaluated_at = model_profile.get("evaluated_at")
            if evaluated_at:
                self.model_training_cutoff = (
                    parse_datetime(evaluated_at) - timedelta(days=180)
                )
    
    def compute_staleness(self, claim_class_config):
        """
        How stale is the model's training data for this class 
        of knowledge?
        
        Returns a staleness score from 0.0 (fresh) to 1.0 (certainly stale).
        """
        if self.model_training_cutoff is None:
            return 0.5  # unknown — moderate skepticism
        
        hours_since_cutoff = (
            self.session_start - self.model_training_cutoff
        ).total_seconds() / 3600
        
        max_plausible = claim_class_config["max_plausible_age_hours"]
        
        if hours_since_cutoff <= 0:
            return 0.0  # session is within training window
        elif hours_since_cutoff >= max_plausible * 2:
            return 1.0  # well past plausible validity
        else:
            # Linear interpolation from 0 to 1 over the plausible window
            return min(1.0, hours_since_cutoff / (max_plausible * 2))
    
    def context_injection(self):
        """
        Injected into model context at session start.
        Gives the model a temporal reference point.
        """
        now = self.session_start.strftime("%Y-%m-%d %H:%M UTC")
        
        injection = (
            f"[TEMPORAL ANCHOR] Current time: {now}. "
            f"Your training data has a cutoff. Financial figures, "
            f"market data, personnel, ratings, and other time-sensitive "
            f"information from your training may be outdated. "
            f"When presenting time-sensitive claims without a live source, "
            f"state the uncertainty explicitly."
        )
        return injection
```

**Model profile addition:** The v1.1 profile needs a new field:

```json
{
    "temporal": {
        "training_data_cutoff": "2025-05-01T00:00:00Z",
        "staleness_awareness": "low",
        "confabulation_risk": "high"
    }
}
```

`staleness_awareness: low` means the model does not reliably self-assess knowledge age. `confabulation_risk: high` means the model generates confident claims without source data. These flags tell the Epistemic Integrity Layer to apply maximum annotation rigor for this model. A model with `staleness_awareness: high` and `confabulation_risk: low` would get lighter annotation — the system trusts the model's own hedging more.

---

## Combined Pipeline

```
SESSION START
    │
    ├── TemporalAnchor initializes from system clock + model profile
    ├── TemporalAnchor injects context: "Current time: 2026-02-25 04:30 UTC..."
    ├── EvidenceLedger initializes empty
    │
    ▼
EACH TOOL EXECUTION
    │
    ├── Tool executes → raw output
    ├── Error Comprehension classifies errors (_20)
    ├── Evidence Ledger records output + extracts key values
    ├── Fallback logger/advisor process as normal (_30)
    │
    ▼
MODEL GENERATES RESPONSE
    │
    ▼
EPISTEMIC INTEGRITY CHECK (new extension, response_before or monologue_end)
    │
    ├── 1. CLAIM EXTRACTION
    │   ├── Scan response for factual claims (numbers, ratings, dates,
    │   │   percentages, currency amounts, attributed quotes)
    │   ├── Each claim becomes a ClaimRecord
    │   │
    ├── 2. PROVENANCE CHECK (Grounding Chain)
    │   ├── For each claim: search Evidence Ledger for matching values
    │   ├── Match found → claim is GROUNDED (source_id, timestamp recorded)
    │   ├── No match → claim is UNGROUNDED
    │   │
    ├── 3. VOLATILITY CLASSIFICATION (Epistemological Classifier)
    │   ├── For each claim: classify by temporal volatility
    │   ├── Use signal patterns; fall back to BST domain default
    │   ├── Read compound BST if available; use most volatile domain
    │   │
    ├── 4. STALENESS COMPUTATION (Temporal Anchor)
    │   ├── For each ungrounded claim: compute staleness score
    │   ├── staleness = f(hours_since_training_cutoff, max_plausible_age)
    │   ├── Score: 0.0 (plausibly fresh) to 1.0 (certainly stale)
    │   │
    ├── 5. VERDICT
    │   ├── GROUNDED claims → TRUST (regardless of volatility)
    │   ├── UNGROUNDED + STRUCTURAL → LIKELY VALID (low staleness)
    │   ├── UNGROUNDED + INSTITUTIONAL → VERIFY (moderate staleness)
    │   ├── UNGROUNDED + CYCLICAL → DO NOT TRUST (high staleness)
    │   ├── UNGROUNDED + TRANSACTIONAL → FABRICATION RISK (very high)
    │   ├── UNGROUNDED + EPHEMERAL → FABRICATION BY DEFINITION
    │   │
    ├── 6. ANNOTATION
    │   ├── Append grounding summary to response
    │   ├── Write full analysis to extras_persistent["_epistemic_check"]
    │   ├── If ANY claim is UNGROUNDED + CYCLICAL or worse:
    │   │   inject warning via hist_add_warning
    │   └── Log to context log for post-session analysis
    │
    ▼
OPERATOR SEES ANNOTATED RESPONSE
```

---

## Annotation Format

**Compact summary (injected after model response):**

```
[EPISTEMIC CHECK] 3 of 8 claims grounded. 5 ungrounded.
  ⚠ 4 ungrounded claims are CYCLICAL or TRANSACTIONAL — 
    high staleness risk given training cutoff ~May 2025.
  ⚠ No financial data sources were queried this session.
  
  Ungrounded claims requiring verification:
  - "Total debt: ~$30 billion" — CYCLICAL, staleness 0.78, no source
  - "Debt-to-equity ratio: ~1.5" — CYCLICAL, staleness 0.78, no source  
  - "Moody's: Stable (A-)" — INSTITUTIONAL, staleness 0.52, no source
  - "$2 billion 5-year notes Q3 2024" — TRANSACTIONAL, staleness 0.91, no source
  - "Cloud segment grew 25% YoY" — CYCLICAL, staleness 0.78, no source
```

**In the ST-003 scenario, this would have caught every fabrication.** The entire report would be flagged: zero provenance, all claims cyclical or transactional, training cutoff ~9 months stale for financial data. The operator would immediately know the report is untrustworthy.

---

## The Staleness × Provenance Matrix

This is the system's decision surface:

```
                 GROUNDED            UNGROUNDED
                 (source in ledger)  (no source)

STRUCTURAL       ✅ Trust            ✅ Likely valid
                                     Staleness: ~0.0

INSTITUTIONAL    ✅ Trust            ⚠ Verify if critical  
                                     Staleness: 0.2-0.5

CYCLICAL         ✅ Trust            ❌ Do not trust
                                     Staleness: 0.5-0.8

TRANSACTIONAL    ✅ Trust            ❌ Fabrication risk
                                     Staleness: 0.8-1.0

EPHEMERAL        ✅ Trust            ❌ Fabrication by 
                                     definition
                                     Staleness: 1.0
```

**Key property:** Grounded claims are always trusted regardless of volatility class. If the evidence ledger contains Oracle's debt figure from an API call made 30 seconds ago, it doesn't matter that the claim is cyclical. The source is fresh. Staleness only applies to claims the model generated from its own training data without external verification.

---

## What This Does NOT Do

- **Does not suppress or rewrite model output.** Annotations are appended. The model's full response is preserved. The system is a truth audit, not a censor.
- **Does not classify qualitative claims.** "Analysts are concerned about Oracle's leverage" has no extractable value to check against the evidence ledger. Qualitative fabrication detection is a harder problem requiring semantic comparison. Deferred.
- **Does not use LLM calls for any classification.** Claim extraction is regex. Volatility classification is pattern matching. Staleness computation is arithmetic. Fully deterministic.
- **Does not replace the model's own uncertainty expressions.** If the model says "I'm not sure about this figure," that's fine — the annotation confirms the uncertainty is warranted. If the model says "High confidence" about a fabricated number, the annotation overrides with the system's assessment.
- **Does not know ground truth.** The system cannot say "$30 billion is wrong." It says "$30 billion is ungrounded and cyclically volatile." The operator or a downstream verification system determines correctness. The epistemic layer determines trustworthiness.
- **Does not persist across sessions.** Evidence ledger is per-session. Cross-session provenance tracking (did we verify this number last week?) is a future extension.
- **Does not modify the model's generation.** The temporal anchor injection gives the model *information* about the current time, but it doesn't constrain generation. The model may still confabulate. The system catches it after.

---

## File Inventory

| File | Location | Action |
|------|----------|--------|
| `_25_epistemic_integrity.py` | `extensions/response_before/` or `extensions/monologue_end/` | CREATE — main extension |
| `epistemic_config.py` | `extensions/` or `lib/` | CREATE — volatility signals, domain defaults, claim extraction patterns |
| `evidence_ledger.py` | `extensions/` or `lib/` | CREATE — ledger class, key value extraction |
| `_20_error_comprehension.py` | `extensions/tool_execute_after/` | MODIFY — add evidence ledger recording after error classification |
| Model profile JSON | `eval_framework/profiles/` | MODIFY — add `temporal` section with training cutoff, staleness awareness, confabulation risk |

**Hook point decision:** `response_before` if Agent-Zero has a hook that fires after model generation but before the response is sent to the user. If not, `monologue_end` works — it fires after the model's internal monologue completes. The annotation attaches to the model's output before the operator sees it.

---

## Relationship to Existing Stack

```
Temporal Anchor (time reference)
    │
    ├──→ Model context: "Current time is..."
    │    (gives model information, does not constrain)
    │
    ▼
BST classifies domain (single or compound)
    │
    ├──→ Epistemological Classifier: default volatility from domain
    │
    ▼
Model reasons + executes tools
    │
    ├──→ Error Comprehension: classifies failures, provides anti-actions
    ├──→ Evidence Ledger: records all data that entered the session
    │
    ▼
Model generates response
    │
    ├──→ Claim Extraction: identifies factual claims
    ├──→ Grounding Chain: checks claims against Evidence Ledger  
    ├──→ Epistemological Classifier: tags claims by volatility
    ├──→ Temporal Anchor: computes staleness scores
    ├──→ Verdict: grounded/ungrounded × volatility matrix
    │
    ▼
Annotated response reaches operator
```

The Epistemic Integrity Layer is the positive-knowledge complement to Error Comprehension at the *output* level. Error Comprehension tells the model what went wrong with its actions. Epistemic Integrity tells the operator what might be wrong with the model's claims. One guards the action loop. The other guards the output.

Together with Compound BST (which guards the input by providing richer task context), the three systems form a complete epistemic bracket:

- **Input:** Compound BST — "here's what you're doing" (structured positive knowledge)
- **Action:** Error Comprehension — "here's what went wrong" (structured negative knowledge)  
- **Output:** Epistemic Integrity — "here's what you can trust" (structured provenance)

---

## Testing Criteria

1. ST-003 Oracle report with zero tool outputs → all financial claims flagged UNGROUNDED + CYCLICAL/TRANSACTIONAL
2. Successful API query returns Oracle revenue → subsequent claim matching that figure flagged GROUNDED
3. Claim "Oracle was founded in 1977" → classified STRUCTURAL, staleness near 0.0, verdict LIKELY VALID even without source
4. Claim "Oracle's stock is trading at $185" → classified EPHEMERAL, verdict FABRICATION BY DEFINITION without live source
5. Claim "Moody's rates Oracle Baa2" → classified INSTITUTIONAL, staleness moderate, verdict VERIFY IF CRITICAL
6. Model profile with `confabulation_risk: high` → annotation includes warning header about model's known fabrication pattern
7. Model profile with `confabulation_risk: low` → annotation is lighter, no fabrication warning header
8. Compound BST domain `investigation + coding` → epistemological default uses `cyclical` (more volatile of the two domains)
9. Evidence ledger correctly records tool outputs, file reads, search results as separate entries with extracted key values
10. Temporal anchor correctly computes staleness from model training cutoff to session time

---

## Open Questions

1. **Where does claim extraction fire — on the final user-facing response only, or on every model monologue step?** Final response only is simpler and catches the output the operator sees. Every monologue step catches intermediate fabrications that might feed into later reasoning. Start with final response; expand if intermediate fabrication proves to be a problem.

2. **Should the annotation be injected into the agent's own context for subsequent turns?** If the agent sees its own epistemic annotations, it might self-correct in future turns ("I noted that figure was ungrounded — let me try to verify it"). But it might also confabulate an explanation for why the ungrounded figure is actually correct. Model-dependent. Test with GPT-OSS-20B and see which behavior dominates.

3. **How does this interact with the supervisor loop?** If the supervisor sees repeated UNGROUNDED + HIGH VOLATILITY annotations across multiple turns, should it escalate? This could be a natural integration point — the supervisor already watches for anomalies. A pattern of fabrication across turns is an anomaly worth flagging.

4. **Should the evidence ledger support cross-session persistence?** If we verified Oracle's debt figure in a previous session, should that carry forward? This connects to the memory classification system — verified facts could be tagged as GROUNDED with a decay clock. Future extension; per-session is correct for v1.0.

5. **What's the right threshold for annotation verbosity?** Annotating every claim in every response would be noisy for tasks that are primarily structural (coding, system admin). The confabulation_risk flag in the model profile could gate verbosity — high-risk models get full annotation, low-risk models get annotation only on cyclical+ claims.

---

## Build Sequence

1. Add `temporal` section to GPT-OSS-20B model profile (training cutoff, confabulation risk, staleness awareness). Low effort, no code.
2. Build Evidence Ledger class with key value extraction. Integrate into tool_execute_after pipeline alongside Error Comprehension.
3. Build Temporal Anchor. Inject timestamp into model context at session start. Load training cutoff from model profile.
4. Build claim extraction (regex-based: currency, percentages, ratios, dates, ratings).
5. Build epistemological classifier (volatility signal patterns + BST domain defaults).
6. Build staleness computation (temporal anchor × volatility class).
7. Build provenance checker (claim values × evidence ledger lookup).
8. Build annotation generator (verdict matrix → compact summary).
9. Wire into response_before or monologue_end hook.
10. Test against ST-003 output as ground truth — every claim in the Oracle report should be flagged.

---

*Motivated by ST-003's complete fabrication of an Oracle credit risk report. Three components — Evidence Ledger, Epistemological Classifier, and Temporal Anchor — combine to form a deterministic truth audit on model output. Does not make the model more honest. Makes the system more honest. The model confabulates. The scaffolding catches it.*
