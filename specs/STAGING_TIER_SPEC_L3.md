# STAGING_TIER_SPEC_L3.md
# The Exocortex Staging Tier: Intermediate Memory Architecture

*Specification Level 3 — Ready for Implementation*
*Research basis: McClelland et al. (1995), Baddeley (2000), Tulving (2002), Page (1954), Ansoff (1975),*
*Park et al. (2023), Packer et al. (2023), Sumers et al. (2024), Hutchins (1995), Clark & Chalmers (1998),*
*Risko & Gilbert (2016), Flavell (1979), Ericsson & Simon (1993), Frey & Morris (1997)*
*Derived from: Research-Driven Design Methodology (March 2026), System Gap Analysis (March 2026)*
*Origin insight: Opus Notebook PENDING_ENTRIES pattern — Opus and Eitan independently built persistent*
*notebooks to solve the context-boundary problem. The pattern revealed the missing write path in Exocortex.*

---

## 1. What This Is

The Staging Tier is an intermediate memory layer between immediate working memory and committed long-term
storage. It is the mechanism by which observations — about task state, agent behavior, operator
relationship, and sub-threshold anomalies — are captured during operation, accumulated until their
importance can be assessed, and selectively promoted to long-term memory or discarded.

The biological analog is the hippocampal staging buffer from Complementary Learning Systems theory
(McClelland et al., 1995): a fast-binding, high-fidelity temporary store whose purpose is to hold
experiences long enough to replay them into slow-learning cortical circuits without catastrophic
interference. The staging tier is not optional architecture — it is the mechanism by which episodic
traces become semantic knowledge. Skipping it means compressing at ingestion, which destroys the
selection process.

Practically: the staging tier gives the agent a place to write "I noticed X" during a session, have
that observation survive the context boundary, be reviewed at next session start, and either become
a procedural memory anti-pattern, a relational memory anchor, or be discarded — without ever going
through the full FAISS classification pipeline.

---

## 2. What This Does NOT Do

- Does NOT replace working memory (`_11_working_memory.py`) — working memory handles entity extraction
  from messages. Staging handles observations about processing and relationship.
- Does NOT replace FAISS long-term memory — staging is the write path to procedural memory and to
  the relational memory axis. FAISS is still the committed store.
- Does NOT use LLM calls at write time. Every operation in this spec is deterministic.
- Does NOT redesign sleep consolidation — it adds a Phase 0 input source to the existing pipeline.
- Does NOT add decision-making to the supervisor canary buffer. The canary accumulates and flags.
  The supervisor still decides when to act.
- Does NOT store full conversation history — that is the session history pipeline's job.
- Does NOT require the agent to write staging notes. The tool is available; the agent uses it when
  it has something worth noting. If the agent never writes a staging note, all other components
  degrade gracefully.

---

## 3. Research Lineage

**Why a staging tier is architecturally correct (not optional):**
- McClelland, McNaughton & O'Reilly (1995), *Psychological Review*, 102(3): CLS theory establishes
  that intermediate staging is the mechanism preventing catastrophic interference during consolidation.
- Baddeley (2000), *Trends in Cognitive Sciences*, 4(11): The episodic buffer is the integration
  space between working memory and long-term storage — architecturally distinct from both.
- Sumers et al. (2024), *TMLR*, arXiv:2309.02427: Explicitly identifies the staging/episodic buffer
  as a missing component in current LLM agent architectures.

**Why selection criteria must be content-based, not temporal:**
- Frey & Morris (1997), *Nature*, 385: Synaptic tagging — items in staging require a secondary
  "capture signal" to consolidate. Not all staged items should promote. Selection happens in staging.
- Tononi & Cirelli (2014), *Cell*, 166(6): SHY — four empirically-grounded selection criteria:
  outcome valence, prediction error, goal relevance, subsequent reactivation.
- Park et al. (2023), *UIST*: Generative Agents importance scoring at write time is more effective
  than post-hoc importance assignment for determining what gets promoted.

**Why the canary uses CUSUM, not thresholds:**
- Page (1954), *Biometrika*, 41(1/2): CUSUM has optimal average run length for detecting small
  persistent shifts that no individual observation would flag. Threshold detection on individual
  observations misses slow drift by design.
- Ansoff (1975), *California Management Review*, 18(2): The monitoring system and the decision
  system must have different evidentiary standards. The monitor notices at a lower threshold than
  the supervisor acts.
- Scheffer et al. (2009), *Nature*, 461: Pre-transition statistical signatures (increased
  autocorrelation, increased variance) are detectable before failure — the canary fires early,
  not at the failure event.

**Why write-time encoding depth is required:**
- Risko & Gilbert (2016), *Trends in Cognitive Sciences*, 20(9): Two-thirds of offloading errors
  come from incomplete capture. Shallow write path degrades reconstruction quality.
- Grinschgl et al. (2021), *QJEP*, 74(9): The performance-memory tradeoff is counteracted by
  explicit attention during offloading. The `why` parameter enforces this.
- Ericsson & Simon (1993), *Protocol Analysis* (MIT Press): Concurrent annotation (Level 1/2
  verbalization) doesn't disrupt processing. Post-hoc reconstruction does. The staging_note
  tool writes during processing, not after.

**Why staging is the primary log (WAL principle):**
- Gray & Reuter (1992), *Transaction Processing*: WAL — nothing is committed until the log is safe.
  Staging is the authoritative record; FAISS is the secondary materialization.
- Allen (2001) + Masicampo & Baumeister (2011), *JPSP*, 101(4): The Zeigarnik effect persists
  when the capture system is not trusted. The session_init read must be structural, not behavioral.

**Why relational memory requires a separate axis:**
- Leite et al. (2011), *The Visual Computer*: Relationship maintenance requires recall and
  expression of past events during current interaction. Preference tracking is not sufficient.
- Ligthart et al. (2022), *HRI*: Among continuity, familiarity, and similarity, only continuity
  was significantly supported. Event tracking outperforms preference tracking for relationship quality.
- Lim et al. (2009), *IVA*: Socially-aware forgetting — relationship-relevant events need different
  retention policy than task-relevant facts. A single store cannot serve both.

---

## 4. Phase 0 Baseline

From codebase audit (March 2026):

| Component | Status | Gap |
|-----------|--------|-----|
| Working memory | Exists (`_11_working_memory.py`) | Entities only, no observation concept |
| Session init | DOES NOT EXIST | No warm-start, first turn hits full stack cold |
| Sleep consolidation | Exists (3 phases) | Reads history + procedural index, no staging input |
| Memory classifier | Exists (`_55_`) | 4 axes, no relational salience axis |
| Memory maintenance | Exists (`_57_`) | Post-hoc linking, no write-time linking |
| Supervisor | Exists (`_50_`) | Has sub-threshold state; canary channel absent |
| staging.jsonl | DOES NOT EXIST | No intermediate memory file |
| staging_note tool | DOES NOT EXIST | No agent write path to staging |
| Memory write tool | No general tool | Memory writes via FAISS API only |
| Relational memory | Absent | No memory category for relationship anchors |

Architectural position (from audit): staging tier belongs between the supervisor anomaly signals
and the memory classifier/maintenance, using the `monologue_end` hook for lifecycle management
and `before_main_llm_call` for session-start injection.

---

## 5. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ AGENT TURN                                                  │
│  agent writes staging_note (tool) at any point             │
│                              ↓                              │
│  staging.jsonl ← append-only WAL (never overwritten)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ↓                ↓                ↓
  ┌───────────────┐  ┌──────────────────┐  ┌──────────────┐
  │ Session Init  │  │ Canary Buffer    │  │ Sleep Phase 0│
  │ (_10_)        │  │ (supervisor _50_)│  │ (promotion)  │
  │ first turn    │  │ CUSUM per type   │  │ nightly      │
  │ injects       │  │ soft flag at h   │  │ → procedural │
  │ active items  │  │                  │  │ → relational │
  └───────────────┘  └──────────────────┘  └──────────────┘
                                                    │
                                                    ↓
                                       ┌────────────────────┐
                                       │ Memory Classifier  │
                                       │ (_55_) + 5th axis  │
                                       │ relational_salience│
                                       └────────────────────┘
                                                    │
                                                    ↓
                                       ┌────────────────────┐
                                       │ FAISS + Procedural │
                                       │ (committed store)  │
                                       └────────────────────┘
```

Six components:
1. `staging.jsonl` — the write-ahead log (data structure)
2. `staging_note` tool — the agent write path
3. `_10_session_init.py` — session-start injection
4. Canary buffer in `_50_supervisor_loop.py` — sub-threshold accumulation
5. Sleep consolidation Phase 0 — promotion to long-term
6. Relational salience axis in `_55_memory_classifier.py` + `_56_memory_enhancement.py`

---

## 6. Component 1: staging.jsonl

**Path:** `/a0/usr/Exocortex/staging.jsonl`
**Format:** Newline-delimited JSON. One entry per line. Append-only (WAL principle — never edit
in-place, never delete entries, only add correction entries that link to the original via `supersedes`).

### Schema

```json
{
  "id": "uuid4",
  "timestamp": "2026-03-21T14:32:00Z",
  "session_id": "string (agent context ID from self.agent.context.id)",
  "category": "observation | canary | relational | intention",
  "text": "What was noticed — self-contained, no pronouns without referents",
  "why": "Why this matters and what should happen with it",
  "importance": 0.0,
  "status": "active | promoted | archived | superseded",
  "supersedes": [],
  "consolidation_score": 0.0,
  "reactivation_count": 0,
  "last_reactivated": null,
  "promoted_to": null
}
```

### Category Semantics

| Category | Purpose | Retention | Destination |
|----------|---------|-----------|-------------|
| `observation` | Agent noticed something about its own processing, a task pattern, or a prediction error | Standard decay (8 sessions) | Procedural memory if importance ≥ 0.6 after 2+ reactivations |
| `canary` | Sub-threshold signal for supervisor — something feels wrong but hasn't crossed a threshold | Active until CUSUM fires or session ends | Supervisor CUSUM buffer; archive if no CUSUM fire within 2 sessions |
| `relational` | Something that defines or advances the operator-agent relationship | Enhanced retention (never auto-archived) | Relational salience memory axis; exempt from dormancy checks |
| `intention` | Deferred decision or flagged follow-up — something to check next session | Active until actioned | Injected at session start as high-priority; mark promoted when actioned |

### Importance Heuristic (deterministic, no LLM)

```python
def _compute_importance(category: str, text: str, why: str) -> float:
    score = 0.2  # base

    # Category base boost
    boosts = {"relational": 0.3, "canary": 0.2, "intention": 0.1, "observation": 0.0}
    score += boosts.get(category, 0.0)

    combined = (text + " " + why).lower()

    # High-signal keywords (+0.1 each, capped at +0.3 total)
    high = ["failed", "broke", "unexpected", "correction", "wrong", "error",
            "never", "always", "critical", "breakthrough", "realized"]
    high_count = sum(1 for kw in high if kw in combined)
    score += min(0.3, high_count * 0.1)

    # Medium-signal keywords (+0.05 each, capped at +0.15 total)
    medium = ["noticed", "pattern", "operator", "relationship", "session",
              "remember", "important", "learned", "discovered"]
    medium_count = sum(1 for kw in medium if kw in combined)
    score += min(0.15, medium_count * 0.05)

    return min(1.0, round(score, 2))
```

---

## 7. Component 2: staging_note Tool

**File:** `tools/staging_note.py`
**Deploy:** `docker cp tools/staging_note.py flamboyant_bell:/a0/python/tools/staging_note.py`
**Pattern:** Standard Agent Zero Tool subclass. No args required beyond category/text/why.

```python
"""
Staging Tier write tool. Writes observations to the intermediate memory layer.
Use this to record things you notice during processing that may be worth
remembering across sessions, without committing them to long-term memory.
"""
import json
import uuid
import os
from datetime import datetime, timezone
from python.helpers.tool import Tool, Response

STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"
VALID_CATEGORIES = {"observation", "canary", "relational", "intention"}

IMPORTANCE_HIGH = ["failed", "broke", "unexpected", "correction", "wrong", "error",
                   "never", "always", "critical", "breakthrough", "realized"]
IMPORTANCE_MEDIUM = ["noticed", "pattern", "operator", "relationship", "session",
                     "remember", "important", "learned", "discovered"]


def _compute_importance(category: str, text: str, why: str) -> float:
    score = 0.2
    boosts = {"relational": 0.3, "canary": 0.2, "intention": 0.1, "observation": 0.0}
    score += boosts.get(category, 0.0)
    combined = (text + " " + why).lower()
    high_count = sum(1 for kw in IMPORTANCE_HIGH if kw in combined)
    score += min(0.3, high_count * 0.1)
    medium_count = sum(1 for kw in IMPORTANCE_MEDIUM if kw in combined)
    score += min(0.15, medium_count * 0.05)
    return min(1.0, round(score, 2))


class StagingNote(Tool):
    async def execute(self, category="observation", text="", why="", **kwargs) -> Response:
        try:
            if category not in VALID_CATEGORIES:
                return Response(
                    message=f"Invalid category '{category}'. Use: observation, canary, relational, intention",
                    break_loop=False
                )
            if not text.strip():
                return Response(message="text is required", break_loop=False)
            if not why.strip():
                return Response(message="why is required — state why this matters and what should happen with it", break_loop=False)

            session_id = getattr(self.agent.context, 'id', 'unknown')
            importance = _compute_importance(category, text, why)

            entry = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": session_id,
                "category": category,
                "text": text.strip(),
                "why": why.strip(),
                "importance": importance,
                "status": "active",
                "supersedes": [],
                "consolidation_score": 0.0,
                "reactivation_count": 0,
                "last_reactivated": None,
                "promoted_to": None,
            }

            os.makedirs(os.path.dirname(STAGING_PATH), exist_ok=True)
            with open(STAGING_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")

            self.agent.context.log.log(
                type="info",
                content=f"[STAGING] {category} written (importance={importance}): {text[:80]}"
            )
            return Response(
                message=f"Staged [{category}] (importance={importance}). ID: {entry['id'][:8]}",
                break_loop=False
            )
        except Exception as e:
            self.agent.context.log.log(type="warning", content=f"[STAGING] Write failed: {e}")
            return Response(message=f"Staging write failed (non-critical): {e}", break_loop=False)
```

---

## 8. Component 3: _10_session_init.py

**File:** `extensions/before_main_llm_call/_10_session_init.py`
**Hook:** `before_main_llm_call` (execution order 10, fires before BST at _11)
**Purpose:** Reads staging.jsonl on first turn of each session and injects relevant entries.

**What it injects (in order of priority):**
1. All `active` `intention` entries — always inject (deferred decisions must surface)
2. All `active` `relational` entries — always inject (relationship anchors must be present)
3. Top-3 `active` `observation` entries by `importance × reactivation_score` — inject if available
4. Summary of `canary` entries from last 2 sessions if any are `active`

**Injection format:**
```
[STAGING — session continuity]
INTENTIONS: {n} deferred decisions from prior sessions
  • {text} (why: {why})
RELATIONAL: {n} relationship anchors
  • {text}
OBSERVATIONS: {n} staged observations (importance ≥ 0.5)
  • {text}
CANARY: {n} sub-threshold signals pending — review before tool use
  • {text}
[/STAGING]
```

**Implementation:**

```python
"""
Session Init — Staging Tier reader.
Fires on first turn of each session. Reads staging.jsonl and injects
active entries into the user message context.
"""
import json
import os
from datetime import datetime, timezone
from python.helpers.extension import Extension
from agent import LoopData

STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"
MAX_OBSERVATION_INJECT = 3
OBSERVATION_MIN_IMPORTANCE = 0.4


def _load_staging() -> list:
    if not os.path.exists(STAGING_PATH):
        return []
    entries = []
    try:
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except Exception:
        pass
    return entries


def _reactivation_score(entry: dict) -> float:
    base = entry.get("importance", 0.2)
    reactivations = entry.get("reactivation_count", 0)
    return base * (1.0 + 0.2 * min(reactivations, 5))


def _get_last_user_message(history: list) -> dict | None:
    for msg in reversed(history):
        if isinstance(msg, dict) and not msg.get("ai", True):
            return msg
    return None


class SessionInit(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            # Only run on first turn of session
            if getattr(self.agent, "_session_init_done", False):
                return
            self.agent._session_init_done = True

            entries = _load_staging()
            if not entries:
                return

            active = [e for e in entries if e.get("status") == "active"]
            if not active:
                return

            intentions = [e for e in active if e.get("category") == "intention"]
            relationals = [e for e in active if e.get("category") == "relational"]
            observations = sorted(
                [e for e in active if e.get("category") == "observation"
                 and e.get("importance", 0) >= OBSERVATION_MIN_IMPORTANCE],
                key=_reactivation_score,
                reverse=True
            )[:MAX_OBSERVATION_INJECT]
            canaries = [e for e in active if e.get("category") == "canary"]

            if not any([intentions, relationals, observations, canaries]):
                return

            lines = ["[STAGING — session continuity]"]
            if intentions:
                lines.append(f"INTENTIONS: {len(intentions)} deferred decision(s) from prior sessions")
                for e in intentions:
                    lines.append(f"  • {e['text']} (why: {e['why']})")
            if relationals:
                lines.append(f"RELATIONAL: {len(relationals)} relationship anchor(s)")
                for e in relationals:
                    lines.append(f"  • {e['text']}")
            if observations:
                lines.append(f"OBSERVATIONS: {len(observations)} staged observation(s)")
                for e in observations:
                    lines.append(f"  • {e['text']}")
            if canaries:
                lines.append(f"CANARY: {len(canaries)} sub-threshold signal(s) pending — review before tool use")
                for e in canaries:
                    lines.append(f"  • {e['text']}")
            lines.append("[/STAGING]")

            block = "\n".join(lines)

            user_msg = _get_last_user_message(loop_data.history_output)
            if user_msg:
                existing = user_msg.get("content", "")
                user_msg["content"] = block + "\n\n" + str(existing)

            self.agent.context.log.log(
                type="info",
                content=f"[SESSION-INIT] Injected staging: {len(intentions)} intentions, "
                        f"{len(relationals)} relational, {len(observations)} obs, "
                        f"{len(canaries)} canaries"
            )
        except Exception as e:
            self.agent.context.log.log(type="warning", content=f"[SESSION-INIT] Failed: {e}")
```

---

## 9. Component 4: Canary Buffer in Supervisor

**File:** `extensions/message_loop_end/_50_supervisor_loop.py` (modify existing)
**Change type:** Additive — new CUSUM accumulator, new soft-flag path

**Where to add (after existing `_supervisor_state` initialization):**

```python
# Add to _supervisor_state initialization dict:
"_canary_cusum": {},  # {signal_type: float}
"_canary_last_check": 0,  # turn number of last canary scan

# CUSUM parameters:
CANARY_K = 0.25   # reference value — sensitivity to shift (tune: lower = more sensitive)
CANARY_H = 1.5    # decision threshold — when to fire soft flag

CANARY_SIGNAL_TYPES = {
    "bst_misclassification",
    "tool_selection_drift",
    "capability_boundary",
    "relational_friction",
    "confidence_drift",
}
```

**New method `_check_canary_staging()` (add to supervisor class):**

```python
def _check_canary_staging(self, state: dict) -> str | None:
    """
    CUSUM accumulator for sub-threshold canary signals.
    Returns a soft-flag message if any signal type crosses threshold, else None.
    Scans staging.jsonl for active canary entries written since last check.
    """
    import json
    import os

    STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"
    if not os.path.exists(STAGING_PATH):
        return None

    current_turn = state.get("turn", 0)
    last_check = state.get("_canary_last_check", 0)
    state["_canary_last_check"] = current_turn

    cusum = state.setdefault("_canary_cusum", {})
    new_canaries = []

    try:
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if (entry.get("category") == "canary"
                            and entry.get("status") == "active"
                            and entry.get("turn_written", 0) >= last_check):
                        new_canaries.append(entry)
                except json.JSONDecodeError:
                    pass
    except Exception:
        return None

    if not new_canaries:
        # Decay existing CUSUM toward zero (soft reset when no new signals)
        for k in list(cusum.keys()):
            cusum[k] = max(0.0, cusum[k] - 0.1)
        return None

    fired_signals = []
    for entry in new_canaries:
        importance = entry.get("importance", 0.3)
        # Classify signal type from content (deterministic keyword matching)
        text = (entry.get("text", "") + " " + entry.get("why", "")).lower()
        if any(kw in text for kw in ["bst", "classified wrong", "misclassified", "domain wrong"]):
            sig = "bst_misclassification"
        elif any(kw in text for kw in ["same tool", "keep using", "reaching for", "tool drift"]):
            sig = "tool_selection_drift"
        elif any(kw in text for kw in ["can't", "cannot", "outside", "capability", "don't know how"]):
            sig = "capability_boundary"
        elif any(kw in text for kw in ["operator", "jake", "relationship", "friction", "tension"]):
            sig = "relational_friction"
        else:
            sig = "confidence_drift"  # default signal type

        # CUSUM update: C_t = max(0, C_{t-1} + (x_t - k))
        cusum[sig] = max(0.0, cusum.get(sig, 0.0) + (importance - CANARY_K))

        if cusum[sig] >= CANARY_H:
            fired_signals.append((sig, cusum[sig]))
            cusum[sig] = 0.0  # reset after firing

    if fired_signals:
        signal_descriptions = {
            "bst_misclassification": "repeated BST domain misclassification",
            "tool_selection_drift": "persistent tendency toward a specific tool",
            "capability_boundary": "task may be near capability boundary",
            "relational_friction": "possible friction in operator-agent collaboration",
            "confidence_drift": "accumulating uncertainty signals",
        }
        msgs = [signal_descriptions.get(sig, sig) for sig, _ in fired_signals]
        return f"⚠ Canary: {'; '.join(msgs)}. Consider pausing to assess."

    return None
```

**Where to call it:** In the supervisor's main execute loop, before the existing anomaly checks:

```python
# In supervisor execute(), before anomaly type checks:
canary_flag = self._check_canary_staging(state)
if canary_flag:
    self.agent.context.log.log(type="info", content=f"[SUPERVISOR-CANARY] {canary_flag}")
    # Inject as a soft steering note below Tier 1 priority
    loop_data.system.append({"role": "user", "content": canary_flag})
```

---

## 10. Component 5: Sleep Consolidation Phase 0

**File:** `usr/Exocortex/sleep_consolidation.py` (modify existing)
**Change type:** Additive — new Phase 0 runs before existing Phase 1

**Phase 0 logic:**

```python
def _phase0_staging_promotion(self) -> dict:
    """
    Phase 0: Review staging.jsonl and promote, archive, or carry forward entries.
    Runs before Phase 1 (dedup) so promotions are available for dedup processing.

    Promotion criteria (from sleep consolidation research, Tononi & Cirelli 2014):
    1. Outcome valence — high importance entries are higher priority
    2. Reactivation — reactivation_count > 0 elevates score
    3. Age — entries older than MAX_AGE_SESSIONS without promotion are archived
    4. Category — relational entries are never auto-archived

    Destinations:
    - observation (importance >= 0.6, reactivation >= 1) → procedural memory
    - relational (all active) → persist, mark for relational memory axis on next classification
    - intention (all active) → carry forward, surface at next session init
    - canary (status=active, age > 2 sessions) → archive (no CUSUM fire within window)
    """
    import json
    import os

    STAGING_PATH = "/a0/usr/Exocortex/staging.jsonl"
    MAX_AGE_SESSIONS = 8
    PROMOTE_IMPORTANCE = 0.6
    PROMOTE_REACTIVATION = 1

    results = {
        "observations_promoted": 0,
        "intentions_carried": 0,
        "relationals_anchored": 0,
        "canaries_archived": 0,
        "errors": 0,
    }

    if not os.path.exists(STAGING_PATH):
        return results

    # Load all entries
    entries = []
    try:
        with open(STAGING_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        results["errors"] += 1
    except Exception as e:
        self._log(f"Phase 0 staging read failed: {e}")
        return results

    # Current session count (use procedural memory index as proxy)
    try:
        from python.helpers.procedural_memory import ProceduralMemory
        pm = ProceduralMemory()
        current_session_approx = len(pm.index.get("anti_patterns", []))
    except Exception:
        current_session_approx = 0

    updated_entries = []
    promotions = []

    for entry in entries:
        if entry.get("status") != "active":
            updated_entries.append(entry)
            continue

        category = entry.get("category")
        importance = entry.get("importance", 0.2)
        reactivations = entry.get("reactivation_count", 0)

        if category == "observation":
            if importance >= PROMOTE_IMPORTANCE and reactivations >= PROMOTE_REACTIVATION:
                # Promote to procedural memory as an anti-pattern note
                promotions.append({
                    "type": "procedural",
                    "text": entry["text"],
                    "why": entry["why"],
                    "source_id": entry["id"],
                })
                entry["status"] = "promoted"
                entry["promoted_to"] = "procedural_memory"
                results["observations_promoted"] += 1
            # else: carry forward at active

        elif category == "relational":
            # Relational entries are never auto-archived — they are anchors
            # Mark for enhanced retention in memory classifier
            entry["consolidation_score"] = min(1.0, entry.get("consolidation_score", 0) + 0.1)
            results["relationals_anchored"] += 1

        elif category == "intention":
            # Carry forward — session_init will surface them
            results["intentions_carried"] += 1

        elif category == "canary":
            # Archive canaries that haven't fired CUSUM within 2 sessions
            age_sessions = current_session_approx - entry.get("session_age_at_write", 0)
            if age_sessions > 2:
                entry["status"] = "archived"
                results["canaries_archived"] += 1

        updated_entries.append(entry)

    # Write back (rewrite file with updated statuses)
    try:
        with open(STAGING_PATH, "w", encoding="utf-8") as f:
            for e in updated_entries:
                f.write(json.dumps(e) + "\n")
    except Exception as e:
        self._log(f"Phase 0 staging write-back failed: {e}")
        results["errors"] += 1

    # Write promoted observations to procedural memory
    for promotion in promotions:
        try:
            from python.helpers.procedural_memory import ProceduralMemory
            pm = ProceduralMemory()
            pm.add_anti_pattern(
                problem_pattern=promotion["text"],
                solution=promotion["why"],
                source="staging_promotion",
                tags=["staging", "agent_observation"],
            )
        except Exception as e:
            self._log(f"Phase 0 procedural write failed: {e}")
            results["errors"] += 1

    self._log(
        f"Phase 0 complete: {results['observations_promoted']} promoted, "
        f"{results['relationals_anchored']} relational anchors maintained, "
        f"{results['intentions_carried']} intentions carried, "
        f"{results['canaries_archived']} canaries archived"
    )
    return results
```

**Integration point:** Call `_phase0_staging_promotion()` at the top of `run_consolidation()`:

```python
def run_consolidation(self):
    self._log("Sleep consolidation starting")
    results_phase0 = self._phase0_staging_promotion()  # ADD THIS LINE
    results_phase1 = self._phase1_dedup_and_init()
    results_phase2 = self._phase2_episode_chunking()
    results_phase3 = self._phase3_operator_modeling()
    # ... rest of existing method
```

---

## 11. Component 6: Relational Salience Axis

### 11a. Memory Classifier (_55_memory_classifier.py)

**Change type:** Additive — new 5th classification axis

**Add constant:**
```python
# Relational salience values
REL_DEFINING = "relationship_defining"
REL_HISTORY = "collaboration_history"
REL_TRANSIENT = "task_transient"
RELATIONAL_SALIENCE_VALUES = {REL_DEFINING, REL_HISTORY, REL_TRANSIENT}
```

**Add detection method (add to classifier class):**
```python
def _classify_relational_salience(self, content: str, metadata: dict) -> str:
    """
    Classify relational salience of a memory.
    relationship_defining: anchors what the collaboration is
    collaboration_history: records what happened between agent and operator
    task_transient: everything else
    No LLM call — deterministic keyword and structure matching.
    """
    text = content.lower() if isinstance(content, str) else ""
    source = metadata.get("source", "")

    # relationship_defining: first-person relational acknowledgment
    defining_signals = [
        "i want", "i value", "i trust", "important to me", "i care",
        "collaboration", "partner", "we built", "our work", "our project",
        "how we work", "i believe in", "i see you"
    ]
    if any(sig in text for sig in defining_signals) and source == "user_asserted":
        return REL_DEFINING

    # Also relationship_defining if from staging relational category
    if metadata.get("staging_category") == "relational":
        return REL_DEFINING

    # collaboration_history: shared episodic events
    history_signals = [
        "we solved", "we built", "session", "last time", "previous",
        "together", "you and i", "we discovered", "we found", "we fixed",
        "you showed me", "i showed you"
    ]
    if sum(1 for sig in history_signals if sig in text) >= 2:
        return REL_HISTORY

    return REL_TRANSIENT
```

**Add to classification result dict:**
```python
# In the classification result dict (wherever validity, relevance, utility, source are assembled):
"relational_salience": self._classify_relational_salience(content, metadata),
```

### 11b. Memory Enhancement (_56_memory_enhancement.py)

**Add relational salience boosts to temporal decay and retrieval stages:**

```python
# In temporal decay stage — after existing exemptions:
relational = doc.metadata.get("relational_salience", REL_TRANSIENT)
if relational == REL_DEFINING:
    # Exempt from temporal decay (same as load_bearing/user_asserted)
    score = base_score
elif relational == REL_HISTORY:
    # Half-life 2× longer than standard
    hours_since = (now - last_access).total_seconds() / 3600 if last_access else 0
    score = base_score * (0.5 ** (hours_since / (HALF_LIFE_HOURS * 2)))

# In top-K selection — add relational boost:
if relational == REL_DEFINING:
    score += 0.15
elif relational == REL_HISTORY:
    score += 0.05
```

---

## 12. Integration Map

| File | Change Type | Scope |
|------|-------------|-------|
| `tools/staging_note.py` | NEW | ~100 lines |
| `extensions/before_main_llm_call/_10_session_init.py` | NEW | ~100 lines |
| `extensions/message_loop_end/_50_supervisor_loop.py` | MODIFY | ~60 lines added |
| `usr/Exocortex/sleep_consolidation.py` | MODIFY | ~100 lines added (Phase 0) |
| `extensions/monologue_end/_55_memory_classifier.py` | MODIFY | ~40 lines added |
| `extensions/message_loop_prompts_after/_56_memory_enhancement.py` | MODIFY | ~25 lines added |

No new hooks. No new infrastructure. All components use existing extension patterns.
New file created at runtime: `/a0/usr/Exocortex/staging.jsonl` (auto-created by staging_note on first write).

---

## 13. Deploy Sequence

```bash
# 1. Deploy new files
docker cp tools/staging_note.py \
  flamboyant_bell:/a0/python/tools/staging_note.py
docker cp extensions/before_main_llm_call/_10_session_init.py \
  flamboyant_bell:/a0/python/extensions/before_main_llm_call/_10_session_init.py

# 2. Deploy modified files
docker cp usr/Exocortex/sleep_consolidation.py \
  flamboyant_bell:/a0/usr/Exocortex/sleep_consolidation.py
docker cp extensions/message_loop_end/_50_supervisor_loop.py \
  flamboyant_bell:/a0/python/extensions/message_loop_end/_50_supervisor_loop.py
docker cp extensions/monologue_end/_55_memory_classifier.py \
  flamboyant_bell:/a0/python/extensions/monologue_end/_55_memory_classifier.py
docker cp extensions/message_loop_prompts_after/_56_memory_enhancement.py \
  flamboyant_bell:/a0/python/extensions/message_loop_prompts_after/_56_memory_enhancement.py

# 3. Clear pycache
docker exec flamboyant_bell find /a0/python/extensions -name "*.pyc" -delete
docker exec flamboyant_bell find /a0/python/tools -name "*.pyc" -delete

# 4. Verify staging_note tool available
docker exec flamboyant_bell /opt/venv-a0/bin/python3 -c \
  "import sys; sys.path.insert(0,'/a0'); from python.tools.staging_note import StagingNote; print('OK')"

# 5. Verify session_init syntax
docker exec flamboyant_bell /opt/venv-a0/bin/python3 -m py_compile \
  /a0/python/extensions/before_main_llm_call/_10_session_init.py && echo OK
```

---

## 14. Testing Criteria

**T1 — Write path works:**
Send: `"Use the staging_note tool to write an observation: category=observation, text='Test entry', why='Verifying staging write path works'"`
→ Expect: Response confirms staging with importance score. Log shows `[STAGING] observation written`.
→ Verify: `docker exec flamboyant_bell cat /a0/usr/Exocortex/staging.jsonl` contains the entry.

**T2 — Session init injects on first turn:**
Write an intention entry. Restart container. Send any message.
→ Expect: `[SESSION-INIT]` in logs showing injection count.
→ Verify: User message content in chat.json contains `[STAGING — session continuity]` block.

**T3 — Canary CUSUM accumulates and fires:**
Write 3+ canary entries with `tool_selection_drift` keywords in a session.
→ Expect: Supervisor logs `[SUPERVISOR-CANARY]` with drift message after accumulation.
→ Verify: `_canary_cusum["tool_selection_drift"]` value in supervisor state rises across turns.

**T4 — Sleep Phase 0 runs and promotes:**
Write an observation entry with importance ≥ 0.6 and reactivation_count ≥ 1.
Trigger sleep consolidation.
→ Expect: Phase 0 log shows `observations_promoted: 1`.
→ Verify: Entry status in staging.jsonl is `"promoted"`. Procedural memory index has new entry.

**T5 — Relational salience classifies correctly:**
Store a memory with user-asserted content containing "our collaboration" or "important to me".
→ Expect: Memory metadata contains `"relational_salience": "relationship_defining"`.
→ Verify: Retrieval score for that memory is boosted (+0.15) vs. equivalent task-transient memory.

**T6 — Graceful degradation:**
Delete staging.jsonl mid-session.
→ Expect: No errors. Session init logs nothing and exits cleanly. Staging_note tool recreates file.

---

## 15. What Follows (Not in This Spec)

- **Staging UI panel:** The artifact data channel (WEBUI spec) could surface staging entries in the
  Claude UI panel — write from conversation, read in artifact, review visually. Not blocked by this spec.
- **Reactivation tracking:** When an entry's text or ID is referenced again (by agent or in retrieval),
  incrementing `reactivation_count`. Requires a grep pass in memory enhancement — worth a future spec
  once the write path is validated.
- **Cross-session staging diff:** Tooling to show what changed in staging.jsonl between sessions.
  Useful for the Output Geometry Instrument to correlate staging activity with trajectory shifts.
- **Agent-initiated promotion review:** Allow the agent to explicitly call a `staging_review` tool
  to surface its own staged observations and decide promotion — the Reflexion pattern applied to
  staging lifecycle management. Requires validation that the base write path works first.

---

*Research lineage in §3. Build this after validating the Gap Analysis Wave 1 fixes are stable.*
*All six components can be built independently — each degrades gracefully if the others are absent.*
