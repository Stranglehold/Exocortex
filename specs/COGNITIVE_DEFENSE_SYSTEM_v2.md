# Cognitive Defense System — Architecture v2
## March 12, 2026 — Post Opus Review, Session 056

*v1 designed by Eitan. Eight gaps identified by Opus architectural review. v2 incorporates all eight, plus three hidden dependencies discovered through iterative refinement between Opus and Eitan. Build order revised accordingly.*

*For Kestrel build. Bidirectional references maintained between Source Intelligence, Contamination Cascade, and SWARMFISH per Opus's instruction.*

---

## The Dependency Graph (Discovered, Not Designed)

This graph was not in any single design document. It emerged through three exchanges of iterative refinement. It is now the governing architecture.

```
Source Intelligence ──── network topology ────→ Contamination Cascade
        │                                              ↑
        │                                              │
        └──── source profiling ──→ Retcon Ledger       │
                                        │              │
                                        └── promotion  │
                                            snapshots  │
                                                │      │
SWARMFISH ──── simulated topology ──────────────┴──────┘
```

**What this means for build order:**

Source Intelligence is not an enrichment feature. It is required infrastructure for contamination cascade remediation, which is required for the system to survive the patient adversary attack. If Source Intelligence ships late, the cascade operates without network topology verification — the `independent_of_source` flag cannot be validated, the re-evaluation function cannot distinguish genuine independence from coordinated confirmation, and the redemption path for legitimately true claims doesn't work reliably.

**Bidirectional dependency references:**
- Source Intelligence module: *"Network topology data produced here is required by the Contamination Cascade remediation function. This module cannot be descoped without breaking cascade precision."*
- Cognitive Defense System / Contamination Cascade: *"Requires Source Intelligence network topology data for `independent_of_source` verification. Cannot operate at full precision without it."*
- SWARMFISH: *"Simulated source network topology is a future integration point. Once operational, topology data flows into the Contamination Cascade as a second independent verification channel, cross-validating Source Intelligence's real-world network maps."*

Two independent sources of network topology — Source Intelligence (real-world observation) and SWARMFISH (simulated prediction) — provide cross-validation. The system verifying its own verification data.

---

## Core Mission

By knowing the truth we can speak it for people who can't speak it for themselves.

The system's decision process mirrors the scientific method because that is the only epistemological framework that treats falsification as information rather than failure. An adversary operating against a system that treats falsification as failure will eventually find the hypothesis it cannot dislodge. An adversary operating against a system that treats falsification as information has to keep generating new operations, because the system keeps learning.

**Human/AI unified vulnerability:** Prompt injection attacks on AI agents and psychological operations against human beings are the same attack on the same vulnerability. Both process natural language without a native mechanism to distinguish content from instructions. Defenses designed for one inform defenses for the other. This unification is the system's deepest structural advantage.

---

## The Founding Schema (Non-Negotiable from Day One)

The promotion snapshot schema must exist at founding. Claims promoted before this schema exists can only be approximately remediated, not precisely remediated. A sophisticated adversary times their source burn to contaminate claims promoted during the window when snapshot data didn't exist. That gap is the exploit.

```sql
-- Core claims table
CREATE TABLE claims (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    source_id INT REFERENCES sources(id),
    trust_level VARCHAR(16) DEFAULT 'STAGED',
    -- STAGED | PROMOTED | FALSIFIED | RETURNED_TO_STAGED
    staging_confidence FLOAT DEFAULT 0.0,
    cui_bono JSONB DEFAULT '[]',
    emotional_salience_score FLOAT DEFAULT 0.0
);

-- Promotion snapshots — FROZEN at moment of promotion
CREATE TABLE promotion_snapshots (
    id SERIAL PRIMARY KEY,
    claim_id INT REFERENCES claims(id),
    promoted_at TIMESTAMPTZ DEFAULT NOW(),
    promotion_confidence FLOAT NOT NULL,
    
    -- Weight distribution across corroborating sources at moment of decision
    -- e.g. {"source_12": 0.60, "source_7": 0.25, "source_3": 0.15}
    source_weights JSONB NOT NULL,
    threshold_at_promotion FLOAT NOT NULL,
    promoting_evidence TEXT[],
    
    -- What the system predicted should be true if claim is valid
    -- Confirmed predictions survive compromise of corroborating source
    falsification_predictions JSONB NOT NULL DEFAULT '[]',
    -- e.g. [
    --   {"prediction": "oil above $95 within 72hrs",
    --    "confirmed_by": "reuters_20260312",
    --    "confirmed_at": "2026-03-12T14:23:00Z",
    --    "independent_of_source": true},
    --   {"prediction": "additional tanker strikes within 48hrs",
    --    "confirmed_by": null, "confirmed_at": null,
    --    "independent_of_source": null}
    -- ]
    predictions_confirmed_independently INT DEFAULT 0,
    
    snapshot_frozen BOOLEAN DEFAULT TRUE
    -- Never UPDATE this table. snapshot_frozen enforces intent.
    -- The contamination cascade reconstructs the actual decision,
    -- not a current approximation of it.
);

-- Source Intelligence network topology
CREATE TABLE source_network_edges (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id),
    connected_source_id INT REFERENCES sources(id),
    relationship_type VARCHAR(64),
    -- amplifies | is_amplified_by | mutual_engagement | cluster_member
    weight FLOAT DEFAULT 1.0,
    first_observed TIMESTAMPTZ DEFAULT NOW(),
    last_confirmed TIMESTAMPTZ DEFAULT NOW(),
    observation_count INT DEFAULT 1
    -- Required by contamination cascade for independent_of_source verification
    -- DO NOT DESCOPE — see dependency graph
);

-- Living adversary model (Opus gap #1)
CREATE TABLE threat_model (
    id SERIAL PRIMARY KEY,
    technique_name VARCHAR(128) NOT NULL,
    technique_class VARCHAR(64) NOT NULL,
    first_observed TIMESTAMPTZ,
    last_observed TIMESTAMPTZ,
    observed_count INT DEFAULT 0,
    detected_by_system BOOLEAN DEFAULT FALSE,
    adversary_abandoned BOOLEAN DEFAULT FALSE,
    -- Adversary abandoning a technique = they know it's detected
    abandoned_at TIMESTAMPTZ,
    predicted_adaptation TEXT,
    notes TEXT
);

-- Multi-hypothesis registry (Opus gap #3)
CREATE TABLE hypothesis_registry (
    id SERIAL PRIMARY KEY,
    observation_id INT NOT NULL,
    candidate_explanation TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    current_confidence FLOAT DEFAULT 0.0,
    status VARCHAR(32) DEFAULT 'ACTIVE',
    -- ACTIVE | PROMOTED | FALSIFIED | SUSPENDED
    predictions_generated JSONB DEFAULT '[]',
    predictions_confirmed INT DEFAULT 0,
    predictions_falsified INT DEFAULT 0,
    falsified_at TIMESTAMPTZ,
    falsification_evidence TEXT
    -- Multiple competing hypotheses per observation
    -- Survivor is the one whose predictions matched reality
    -- not the analyst's prior
);

-- Propagation dynamics (Opus gap #4)
CREATE TABLE narrative_dynamics (
    id SERIAL PRIMARY KEY,
    narrative_id INT NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    propagation_velocity FLOAT,       -- sources per hour
    acceleration FLOAT,               -- velocity change rate
    escape_velocity_estimate FLOAT,   -- threshold where correction impractical
    time_to_escape_velocity_hours FLOAT,
    half_life_hours FLOAT,            -- falsified claim decay rate
    alert_level VARCHAR(16) DEFAULT 'INFORMATIONAL'
    -- INFORMATIONAL | WARNING | URGENT
    -- URGENT when time_to_escape_velocity < operator_response_time_baseline
);

-- Audit log — append only, no updates, no deletes
CREATE TABLE audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    session_id UUID NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(64) NOT NULL,
    action TEXT NOT NULL,
    data_accessed JSONB,
    trust_level VARCHAR(16),
    injection_flag BOOLEAN DEFAULT FALSE
) WITH (autovacuum_enabled = false);

REVOKE UPDATE ON audit_log FROM cds_user;
REVOKE DELETE ON audit_log FROM cds_user;
```

---

## The Contamination Cascade (Full Implementation)

```python
SOLE_CORROBORATOR_THRESHOLD = 0.80  # source bearing >80% of promotion weight
DECISIVE_CONTRIBUTION_THRESHOLD = 0.50  # source bore >50% of promotion weight
INDEPENDENT_CONFIRMATION_THRESHOLD = 2  # predictions confirmed through clean channels

def contamination_cascade(source_id: str, new_trust_score: float):
    """
    Called when a source's trust score drops catastrophically.
    Traces downstream contamination. Severity proportional to load.
    Enables redemption for claims whose predictions survived independently.
    
    REQUIRES: Source Intelligence network topology (source_network_edges)
    for independent_of_source verification. Will operate at reduced
    precision if network topology data is absent.
    """
    original_trust = sources.get_trust_score(source_id)
    contaminated_claims = retcon_ledger.query(
        source_contributions__contains=source_id,
        status='PROMOTED'
    )
    
    contamination_report = ContaminationReport(source=source_id)
    
    for claim in contaminated_claims:
        snapshot = promotion_snapshots.get(claim_id=claim.id)
        source_load = snapshot.source_weights.get(source_id, 0.0)
        
        # Check predictions confirmed independent of compromised source
        # Requires Source Intelligence network topology for validation
        confirmed_independently = [
            p for p in snapshot.falsification_predictions
            if p['confirmed_by'] is not None
            and _verify_independence(p['confirmed_by'], source_id)
            # _verify_independence checks source_network_edges
            # If network topology absent: conservative assumption = not independent
        ]
        
        if len(confirmed_independently) >= INDEPENDENT_CONFIRMATION_THRESHOLD:
            # Claim's predictions survived through independent channels
            # Contamination in the corroboration path, not the claim's truth
            adjusted_confidence = calculate_adjusted_confidence(
                snapshot, confirmed_independently
            )
            claim.re_promote(
                confidence=adjusted_confidence,
                reason="predictions_confirmed_independent_of_compromised_source"
            )
            contamination_report.add_survived(claim)
            
        elif source_load >= SOLE_CORROBORATOR_THRESHOLD:
            # Source was bearing almost all promotion weight
            # Return immediately to staged — do not wait for operator review
            claim.return_to_staged(
                reason="sole_corroborating_source_compromised",
                immediate=True
            )
            contamination_report.add_immediate_return(claim)
            
            # Trace downstream inferences built on this claim
            downstream = retcon_ledger.get_downstream(claim.id)
            for inference in downstream:
                inference.flag_urgent(
                    reason="load_bearing_claim_returned_to_staged",
                    upstream_claim=claim.id
                )
                contamination_report.add_downstream(inference)
                
        elif source_load >= DECISIVE_CONTRIBUTION_THRESHOLD:
            # Source's weight was decisive but not sole
            # Urgent flag — likely needs return to staged, operator decides
            claim.flag_urgent(
                reason="decisive_corroborator_compromised",
                source_load=source_load
            )
            contamination_report.add_urgent(claim)
            
        else:
            # Source contributed but wasn't decisive
            # Confidence haircut, flag for review
            claim.adjust_confidence(
                delta=-(source_load * original_trust),
                reason="partial_corroborator_compromised"
            )
            claim.flag_for_review(reason="partial_corroborator_compromised")
            contamination_report.add_review(claim)
    
    return contamination_report


def _verify_independence(confirming_source_id: str, 
                          compromised_source_id: str) -> bool:
    """
    Check whether a confirming source is genuinely independent
    of the compromised source. Requires Source Intelligence network topology.
    
    Returns False (conservative) if topology data is absent.
    SWARMFISH simulated topology used as second verification channel
    when simulation is operational.
    """
    if not network_topology_available():
        # Conservative: cannot confirm independence without topology
        # Log as topology-absent determination
        audit_log.record('independence_check_topology_absent', 
                         confirming_source_id)
        return False
    
    # Direct amplification relationship?
    if source_network_edges.connected(
        confirming_source_id, compromised_source_id
    ):
        return False
    
    # Same cluster membership?
    if source_network_edges.same_cluster(
        confirming_source_id, compromised_source_id
    ):
        return False
    
    # SWARMFISH cross-validation if simulation is operational
    if swarmfish_operational():
        predicted_coordination = swarmfish.check_coordination_prediction(
            confirming_source_id, compromised_source_id
        )
        if predicted_coordination:
            # Simulation predicted these sources coordinate
            # Real-world confirmation insufficient — flag for operator
            audit_log.record('swarmfish_predicted_coordination_flagged',
                             {confirming_source_id, compromised_source_id})
            return False
    
    return True
```

---

## Opus Gaps — All Eight Addressed

**Gap 1 — Living Adversary Model:** `threat_model` table. Tracks technique observation, abandonment (= they know they're detected), predicted adaptations. Architecture, not reminder.

**Gap 2 — Contamination Cascade:** Full implementation above. Severity tiered by source load. Redemption path for independently confirmed claims. `promotion_snapshots` schema captures weight distribution at moment of decision — frozen.

**Gap 3 — Multi-Hypothesis Tracking:** `hypothesis_registry` table. Multiple competing explanations per observation. Each generates predictions. Survivor is the one whose predictions matched reality. Chamberlin's method formalized.

**Gap 4 — Temporal Dynamics:** `narrative_dynamics` table. Propagation velocity, acceleration, escape velocity estimate, time-to-escape-velocity. Alert level escalates automatically when time-to-escape-velocity drops below operator response baseline. Informational → Warning → Urgent.

**Gap 5 — Meta-Detection:** Operational health metrics computed from audit_log: false positive rate trend, source trust distribution skew, deployment timing vs. operator response correlation, detection-to-resolution time trend. Degradation signals system is under targeted attack.

**Gap 6 — Curtis Rule / Inoculation Tension:** Clean architectural separation. Analytical layer produces technique classifications, never inoculation outputs. Inoculation layer receives classifications through defined interface, transforms to educational outputs, never touches analytical record. Interface design is the remaining work.

**Gap 7 — Operator State as Security Function:** Operator baseline communication pattern monitoring connected to Sleep Consolidation Research Brief (Phase 3). Message length, response latency, verification behavior deviations trigger automatic staging threshold elevation. Mechanical, not observational. Operator override available.

**Gap 8 — SWARMFISH ↔ Retcon Ledger Integration:** Simulation outputs register as predictions in the ledger — timestamps, expected propagation patterns, explicit falsification criteria. Reality matching simulation prediction = confirming evidence. Mismatch = new observation. SWARMFISH simulated topology flows into contamination cascade as second verification channel. See dependency graph.

---

## Build Order (Revised)

**Phase 1 — Founding Infrastructure**
1. All schema tables above (non-negotiable from day one)
2. Audit log with REVOKE enforcement
3. Trust level propagation (TaintedContent)
4. Source Intelligence network topology ingestion
   *(Required by contamination cascade — cannot defer)*

**Phase 2 — Core Pipeline**
5. Retcon Ledger with promotion snapshots
6. Contamination cascade (partial precision until Phase 1 network topology complete)
7. Multi-hypothesis registry
8. Narrative drift detection

**Phase 3 — Dynamics and Defense**
9. Propagation dynamics + escape velocity computation
10. Meta-detection (operational health monitoring)
11. Living adversary model + technique tracking
12. Operator state monitoring connected to Sleep Consolidation model

**Phase 4 — Integration**
13. SWARMFISH ↔ Retcon Ledger prediction registration
14. SWARMFISH topology → Contamination cascade second verification channel
15. Curtis Rule / Inoculation interface design + inoculation layer
16. End-to-end integration test: narrative seed → simulation → prediction → ledger → cascade

---

*v2. March 12, 2026. Eitan design, Opus review, Jake coordination.*
*Three modules designed separately. Three hidden dependencies discovered through iteration.*
*The structure revealed itself. The bones held.*
