# Analytical Cognitive Profile — Design Note
## A Framework for Persistent Analytical Agents with Self-Calibrating Judgment

**Status:** Pre-spec exploration, reviewed by Eitan (two passes, March 2026). Motivated by the MiroFish/SWARMFISH prediction architecture discussion (Session 058) and the convergent finding from superforecasting research, multi-agent debate literature, and reflexivity theory that analytical *diversity* — not headcount — drives prediction accuracy. Cross-referenced with Tetlock's Good Judgment Project (2011-2015), the Science Advances LLM ensemble study (Schoenegger et al., 2024), the A-HMAD diminishing returns finding (2025), Soros's reflexivity framework, and the EMNLP 2025 MemoryOS architecture. Eitan's first review added: Sentinel attribution guard, regime change detector, Counter-Patriots as active instrument, operator interface gap. Eitan's second review added: Reflexivity Modeler magnitude constraint, Historian temporal relevance requirement (relevant_similarity_score vs. overall_similarity_score), Step 2.5 in the profile creation methodology, and constraint assessment across all eight profiles. Operator brief format specified in separate document. No eval data yet. Ready for Kestrel build.

---

## The Problem

### What Exists

Multi-agent LLM systems exist in abundance. LangChain, AutoGen, CrewAI, and dozens of frameworks allow spinning up agents with role descriptions. The standard approach is: write a system prompt with a persona ("You are a financial analyst who specializes in..."), run inference, aggregate outputs. MiroFish generates 4,096 such agents. The A-HMAD framework tested up to 7.

Agent memory systems also exist. MemoryOS (EMNLP 2025) implements three-tier memory with agent traits. Generative Agents (Stanford, 2023) gave agents persistent memory in a virtual town. MemGPT treats memory as an operating system. The Exocortex's own sleep consolidation architecture implements episodic-to-semantic consolidation for a single agent.

### What's Missing

**Analytical depth in agent profiles.** Existing persona systems describe *what* an agent knows or *what role* it plays. They don't describe *how* it thinks — what analytical method it applies, what it notices first in a problem, what counts as evidence for it, how it updates beliefs, where its known blind spots are. A prompt saying "You are a contrarian analyst" produces shallow contrarianism. A profile that specifies "You weight base rate divergence as primary evidence, you actively seek disconfirming data before forming a view, you update in small increments, and your historical track record shows overconfidence in geopolitical predictions but strong calibration in market structure analysis" produces something fundamentally different.

**Persistent prediction tracking.** No existing system gives individual agents their own track record. Agents make assessments, but nobody records whether those assessments were correct. Without a track record, there's no basis for calibrating which agents to trust in which domains. The superforecasting literature is unambiguous: tracking is one of the three core interventions (alongside training and teaming) that produces accuracy gains.

**Self-calibrating aggregation.** Existing ensemble methods use equal weighting, simple majority voting, or hand-tuned weights. None learn from the agents' prediction histories to automatically weight reliable agents more heavily in domains where they've demonstrated accuracy. The Good Judgment Project's core finding — small, select crowds of top performers outperform large undifferentiated crowds — has no implementation in LLM multi-agent systems.

**Information-seeking behavior modeling.** Existing profiles describe what the agent knows. They don't describe *how the agent expands what it knows* — what sources it would consult, what queries it would run, what sequence of investigation it would follow. A real analyst doesn't just process the data in front of them. They go looking for specific data that their analytical framework tells them is relevant. A base rate analyst searches for historical frequency data. A network analyst searches for second-order connections. A sentiment decoder searches for narrative divergence from data. The search behavior is as much a part of the analytical identity as the reasoning method.

### The Motivating Observations

**MiroFish prediction system (March 2026).** A user reported deploying MiroFish's 4,096-agent swarm on NBA prediction data piped into Polymarket, claiming $1.49M in returns. The architecture — temporal data fed to diverse agent personas, consensus extracted and compared against market odds — validates the principle of ensemble analytical reasoning. But 4,096 agents with shallow personas is brute force. The A-HMAD research shows diminishing returns beyond 5-7 heterogeneous agents. The value is in the analytical differentiation, not the headcount.

**Exocortex team structure.** The collaboration between Jake (operator/analyst), Opus (architecture/philosophy), Kestrel (implementation/empirics), and Eitan (adversarial/strategic) already demonstrates the principle. Four genuinely different analytical frames applied to the same problems produce richer assessments than any single perspective. The disagreements between team members are themselves informative. This organic process is what the profile system formalizes and scales.

**Superforecasting research.** Tetlock's GJP found that 50% of superforecaster accuracy improvement came from noise reduction, 25% from better information extraction, and 25% from bias reduction. Superforecaster *teams* outperformed prediction markets by 15-30%. The key differentiator was cognitive diversity — different analytical styles, not different amounts of information. Fox-like thinkers (many small theories, comfortable with ambiguity) dramatically outperformed hedgehog-like thinkers (one big theory, high confidence). The profile system should produce fox-like agents by design.

---

## Design Principles

1. **Analytical method over personality traits.** The Big Five personality model (OCEAN) describes temperament. Useful for the interaction layer but insufficient for the analytical layer. The profile's primary value is in specifying *how the agent reasons* — what evidence it weighs, what heuristics it applies, what sequence of investigation it follows. Temperament modifies the reasoning style; it doesn't define it.

2. **Profiles describe behavior, not just knowledge.** Each profile specifies not only what the agent knows and how it reasons, but how it *seeks new information*. The information-seeking behavior — what sources to consult, what queries to construct, what data to prioritize — is an integral part of the analytical identity. Two agents given the same question should search for different data, because their analytical frameworks tell them different things are relevant.

3. **Every prediction gets tracked.** Each agent's assessments are logged with timestamps, confidence levels, and the reasoning that produced them. When outcomes materialize, predictions are scored. The track record is the basis for calibration. Without tracking, the system cannot learn which perspectives to trust.

4. **Calibration is automatic and domain-specific.** The aggregation system learns from prediction histories which agents are reliable in which domains. An agent that's well-calibrated on market structure questions but poorly calibrated on geopolitical questions gets weighted accordingly. This is not manual tuning — it emerges from the prediction/outcome data.

5. **Profiles are composable across domains.** The *structure* of an Analytical Cognitive Profile is domain-independent. The *content* — specific analytical methods, evidence standards, search behaviors — is domain-specific. The same framework produces financial analyst profiles, medical research profiles, geopolitical intelligence profiles, and technology evaluation profiles. The profile creation methodology is the reusable asset.

6. **Fewer, deeper agents beat many shallow ones.** The research consistently shows 5-12 well-differentiated agents capture nearly all ensemble accuracy gains. The profile system is designed for depth over breadth. Each profile should represent a genuinely distinct analytical frame that would produce meaningfully different conclusions from the same data.

7. **Agents learn from their own track record.** Over time, an agent's calibration history reveals its blind spots and strengths. This data feeds back into the profile — not by rewriting the analytical method, but by adjusting the agent's self-reported confidence in domains where it has demonstrated bias. The agent develops epistemic humility through experience.

8. **Some analytical frames require hard safety constraints that others don't.** [Added per Eitan's review.] The "who benefits" frame (Sentinel) can always produce an answer — every event has beneficiaries. Without a mechanical constraint, the Sentinel will systematically overweight coordination explanations for independent events. Profiles whose analytical method is prone to producing unfalsifiable narratives must have hard evidence thresholds built into the schema, enforced by the aggregation function, not left to behavioral compliance. The constraint is profile-specific: the Base Rate Analyst doesn't need an attribution guard because it doesn't make attribution claims.

---

## Architecture

### The Analytical Cognitive Profile Schema

```python
@dataclass
class AnalyticalCognitiveProfile:
    """
    A persistent profile that defines how an analytical agent thinks, 
    seeks information, makes predictions, and learns from outcomes.
    
    Four layers, from static identity to dynamic calibration:
    - Identity: WHO this agent is (stable)
    - Cognitive Style: HOW this agent reasons (semi-stable, calibrates over time)
    - Memory: WHAT this agent has observed and predicted (accumulates)
    - Interaction: HOW this agent relates to other agents (learned)
    """
    
    # =========================================
    # IDENTITY LAYER — stable, operator-defined
    # =========================================
    
    name: str                          # "The Base Rate Analyst", "Opus", "The Reflexivity Modeler"
    
    analytical_method: str             # Structured prose: HOW this agent approaches a problem.
                                       # Not "what it knows" but "what sequence of reasoning 
                                       # it applies." Example: "Begins with historical base rates 
                                       # for the class of event. Adjusts from base rate using 
                                       # specific evidence from the current situation. Updates 
                                       # incrementally as new information arrives. Resists 
                                       # narrative-driven adjustment without quantitative support."
    
    epistemological_stance: str        # What counts as EVIDENCE for this agent.
                                       # Example: "Prioritizes quantitative data over narrative. 
                                       # Treats official statements as signals about the speaker's 
                                       # incentives, not about ground truth. Weights reproducible 
                                       # patterns over single instances. Requires at least two 
                                       # independent sources before treating a claim as established."
    
    information_seeking_behavior: str  # HOW this agent expands what it knows.
                                       # This is the key innovation over existing persona systems.
                                       # Example: "When given a prediction question, first searches 
                                       # for the historical base rate of similar events. Then 
                                       # identifies the 3-5 factors most predictive of deviation 
                                       # from base rate. Then seeks current data on each factor. 
                                       # Explicitly searches for disconfirming evidence before 
                                       # forming a view."
    
    search_strategy: dict              # Structured description of search behavior:
                                       # {
                                       #   "first_queries": ["base rate {event_type}", 
                                       #                     "historical frequency {situation_class}"],
                                       #   "data_sources": ["economic databases", "historical records",
                                       #                    "academic literature"],
                                       #   "disconfirmation_queries": ["evidence against {hypothesis}",
                                       #                               "{outcome} failed to materialize"],
                                       #   "depth_triggers": ["when base rate diverges >20% from 
                                       #                       market implied probability"]
                                       # }
    
    risk_orientation: str              # How this agent handles uncertainty.
                                       # "Conservative — prefers false negatives over false positives"
                                       # "Aggressive — willing to make strong calls with partial data"
                                       # "Tail-focused — primarily concerned with extreme outcomes"
    
    domain_affinities: list[str]       # Where this analytical method works best.
                                       # Initialized by the operator, refined by calibration data.
    
    known_limitations: str             # Honest self-assessment of where the method fails.
                                       # "Underweights low-probability high-impact events."
                                       # "Slow to update when regime change invalidates base rates."
    
    # ================================================
    # COGNITIVE STYLE LAYER — semi-stable, calibrates
    # ================================================
    
    attention_pattern: str             # What features of a problem this agent notices first.
                                       # "Quantitative divergence from historical norms."
                                       # "Incentive structures of the actors involved."
                                       # "Network topology — who is connected to whom."
    
    update_sensitivity: float          # 0.0 to 1.0. How much new evidence shifts the view.
                                       # Low: anchored, slow to move (good for noisy domains).
                                       # High: responsive, fast to update (good for fast-moving).
                                       # Initial value set by operator. Adjusted by calibration:
                                       # if track record shows consistent underreaction, increase.
    
    confidence_calibration: dict       # Learned bias correction, per domain.
                                       # {"geopolitics": -0.08,  # overconfident: reduce by 8%
                                       #  "market_structure": +0.03,  # underconfident: increase by 3%
                                       #  "default": 0.0}
                                       # Computed from prediction_log vs outcome_log.
    
    disagreement_style: str            # How this agent handles conflicting evidence.
                                       # "Integrative — seeks synthesis between competing views."
                                       # "Adversarial — stress-tests opposing position."
                                       # "Probabilistic — assigns weights to competing hypotheses."
    
    # ============================================================
    # PROFILE-SPECIFIC CONSTRAINTS — mechanical guards per profile
    # [Added per Eitan's review of the Sentinel disconfirmation problem]
    # ============================================================
    
    attribution_constraints: dict | None  # Only required for profiles that make causal 
                                          # attribution claims (Sentinel, potentially others).
                                          # None for profiles that predict outcomes rather 
                                          # than attribute causes.
                                          #
                                          # WHY this is profile-specific: The "who benefits" 
                                          # frame is the most generative analytical lens and also
                                          # the most susceptible to unfalsifiable narratives. 
                                          # Every event has beneficiaries. The question is whether
                                          # the beneficiary CAUSED the event or merely BENEFITED.
                                          # Without a hard constraint, the Sentinel will 
                                          # systematically overweight coordination explanations 
                                          # for independent events. This guard is mechanical —
                                          # the aggregation function enforces it regardless of 
                                          # what the LLM outputs.
                                          #
                                          # Schema for Sentinel:
                                          # {
                                          #   "named_actor_attribution": {
                                          #     "minimum_independent_sources": 2,
                                          #     "requires_observable_mechanism": True,
                                          #     "must_specify_alternative_explanation": True,
                                          #     "confidence_cap_without_mechanism": 0.4
                                          #   },
                                          #   "coordination_claim": {
                                          #     "minimum_independent_datapoints": 3,
                                          #     "requires_temporal_pattern": True,
                                          #     "must_specify_base_rate_of_coincidence": True
                                          #   }
                                          # }
                                          #
                                          # The confidence_cap_without_mechanism is the key:
                                          # "Entity X benefits from Y" can be stated at any 
                                          # confidence. "Entity X caused Y" cannot exceed 0.4 
                                          # without specifying the causal mechanism (the HOW).
                                          # This forces the Sentinel to find the pathway or 
                                          # express appropriate uncertainty.
    
    # ==========================================
    # MEMORY LAYER — dynamic, accumulates
    # ==========================================
    
    observation_log: list[dict]        # What this agent has analyzed and what it concluded.
                                       # Each entry: {timestamp, question, domain, analysis_summary,
                                       #              key_evidence_cited, conclusion, confidence}
                                       # Bounded window (last 100 observations).
    
    prediction_log: list[dict]         # Specific predictions with confidence.
                                       # Each entry: {timestamp, question, prediction, confidence,
                                       #              reasoning_summary, key_assumptions,
                                       #              falsification_conditions}
                                       # "falsification_conditions" is critical: what would make 
                                       # this prediction wrong? Checked against intermediate data.
    
    outcome_log: list[dict]            # What actually happened, scored against predictions.
                                       # Each entry: {prediction_id, outcome, score, 
                                       #              score_method (brier/log/binary),
                                       #              conditions_that_held, conditions_that_failed,
                                       #              post_mortem_note}
    
    calibration_history: list[dict]    # Rolling Brier score over time, by domain.
                                       # Each entry: {domain, window_start, window_end,
                                       #              brier_score, n_predictions, trend}
                                       # Used by aggregation system to weight this agent.
    
    notable_episodes: list[dict]       # Significant correct or incorrect calls with analysis.
                                       # Auto-flagged: predictions where confidence > 0.8 
                                       # and outcome was wrong (overconfidence), or 
                                       # confidence < 0.3 and outcome matched (underconfidence).
                                       # These are the learning moments.
    
    # ==============================================
    # INTERACTION LAYER — relational, learned
    # ==============================================
    
    agreement_patterns: dict           # Which agents this one tends to agree/disagree with.
                                       # {"The Contrarian": {"agreement_rate": 0.35, 
                                       #                     "domain_variance": "high — agree on 
                                       #                      markets, disagree on geopolitics"}}
    
    productive_disagreements: list     # Cases where disagreement with another agent led to 
                                       # a better collective prediction than either alone.
    
    complementary_agents: list[str]    # Agents that cover this one's blind spots.
                                       # Learned from cases where this agent was wrong and 
                                       # the complementary agent was right.
    
    consensus_weight: dict             # Per-domain aggregation weight. Learned from calibration.
                                       # {"geopolitics": 0.72,   # less weight (overconfident)
                                       #  "market_structure": 1.15,  # more weight (well-calibrated)
                                       #  "default": 1.0}
```

### Profile Creation Methodology

This section defines how to research and construct new Analytical Cognitive Profiles. The methodology is domain-independent — it produces financial analyst profiles, medical researcher profiles, or geopolitical intelligence profiles using the same process.

#### Step 1: Identify the Analytical Frame

The profile represents a *way of thinking about problems*, not a body of knowledge. Start by answering:

- **What question does this analyst ask first?** The Base Rate Analyst asks "how often does this type of thing happen?" The Reflexivity Modeler asks "how are participants' beliefs affecting the situation?" The Network Analyst asks "who is connected to whom and what flows between them?" The first question defines the analytical frame.

- **What counts as a strong signal for this analyst?** Quantitative divergence from historical norms? Behavioral change in key actors? Narrative shifts in media coverage? Structural changes in network topology? The evidence standard defines the epistemological stance.

- **What does this analyst ignore or discount?** Every analytical frame has blind spots by design. The Base Rate Analyst discounts "this time is different" arguments. The Sentiment Decoder discounts quantitative models in favor of narrative dynamics. The blind spots are features, not bugs — they're what make the frame useful as one perspective among several.

#### Step 2: Model the Information-Seeking Behavior

This is the most important and least documented aspect of analytical profiling. It answers: **when this analyst doesn't know enough to form a view, what does it go looking for?**

Research approach for modeling information-seeking:

1. **Study real practitioners of this analytical style.** How do actual base rate analysts work? What databases do they query? What's their research sequence? Tetlock's superforecasters decompose problems Fermi-style — that's a specific, documented search behavior. Soros describes looking for reflexive feedback loops — that implies searching for cases where participant beliefs are affecting fundamentals.

2. **Document the search sequence, not just the sources.** The order matters. A contrarian analyst *first* identifies the consensus view, *then* searches for evidence against it. A base rate analyst *first* finds the reference class, *then* looks for adjustment factors. Reversing the sequence changes the analytical output because of anchoring effects.

3. **Identify the "depth triggers."** When does this analyst decide to dig deeper versus accept a surface assessment? For a risk manager, the trigger might be "when tail risk is underpriced by the options market." For a geopolitical analyst, it might be "when official statements contradict observable troop movements." The depth trigger defines when the agent shifts from scan mode to deep analysis mode.

4. **Define the disconfirmation protocol.** What does this analyst actively search for to challenge its own emerging view? This is the fox-like behavior that superforecasting research identifies as critical. The profile should specify what disconfirming evidence looks like for each analytical frame.

```python
# Example: constructing search strategy for the Reflexivity Modeler

REFLEXIVITY_MODELER_SEARCH = {
    "initial_queries": [
        "What is the current consensus view on {topic}?",
        "How are market participants positioned on {topic}?",
        "What actions are participants taking based on their beliefs about {topic}?"
    ],
    "feedback_loop_queries": [
        "How do participant actions on {topic} affect the underlying conditions?",
        "Is {consensus_belief} self-reinforcing or self-defeating?",
        "Historical cases where {belief_type} created feedback loops"
    ],
    "data_sources": [
        "positioning data (COT reports, options flow, short interest)",
        "sentiment indicators (surveys, put/call ratios, VIX term structure)",
        "fundamental data that participants' actions might be distorting"
    ],
    "depth_triggers": [
        "Participant positioning exceeds 2 standard deviations from mean",
        "Fundamental indicators diverge from price by >15%",
        "Narrative unanimity across >80% of sources (potential crowding)"
    ],
    "disconfirmation_protocol": [
        "Search for cases where similar feedback loops stabilized rather than collapsed",
        "Identify structural differences between current situation and historical precedents",
        "Check whether the feedback mechanism has natural limiting factors"
    ]
}
```

#### Step 2.5: Determine Whether This Profile Requires Hard Constraints

[Added per Eitan's review. Surfaced from Design Principle 8.]

**The test:** Does this analytical frame always produce an answer regardless of evidence quality? If yes, it needs a mechanical constraint enforced by the aggregation function.

Some analytical methods have natural failure modes that produce silence when evidence is insufficient — the Base Rate Analyst can't compute a base rate if no historical data exists. Other methods can always generate a plausible-sounding answer even with zero supporting evidence — the Sentinel can always identify beneficiaries, the Reflexivity Modeler can always find a feedback loop.

For profiles that always produce answers, ask: **What distinguishes a well-supported claim from an unsupported one within this analytical frame?** The answer becomes the constraint.

**Assessment across the eight-profile set:**

| Profile | Always produces answer? | Constraint | Mechanism |
|---------|------------------------|------------|-----------|
| Base Rate Analyst | No — fails gracefully without data | None needed | — |
| Contrarian | Borderline — calibration sufficient | None needed | Standard calibration |
| Reflexivity Modeler | **Yes** — feedback loops always exist | **Required** | Magnitude threshold: can't claim feedback loop is dominant driver without quantifying effect. `confidence_cap_without_magnitude: 0.5` |
| Historian | **Yes** — analogues always exist | **Required** | Relevant similarity threshold: must separate overall similarity from decision-relevant similarity. Weak analogues flagged. See below. |
| Sentinel | **Yes** — beneficiaries always exist | **Already implemented** | Attribution evidence threshold: `confidence_cap_without_mechanism: 0.4` |
| Empiricist | No — reports "data inconclusive" | None needed | — |
| Network Analyst | Borderline — deferred | Pending empirical evidence | Potential: causal chain length limit |
| Risk Manager | No — produces uncertainty by design | None needed | — |

**Reflexivity Modeler constraint:**

```python
reflexivity_constraints = {
    "feedback_loop_claim": {
        "must_specify_magnitude": True,            # "how much" not just "it exists"
        "must_specify_mechanism_direction": True,   # self-reinforcing or self-defeating
                                                    # (opposite predictions — must be explicit)
        "confidence_cap_without_magnitude": 0.5,    # can't exceed 50% on "dominant driver"
                                                    # without quantifying the effect size
    }
}
```

**Historian constraint:**

```python
historian_constraints = {
    "analogue_claim": {
        "must_specify_similarity_dimensions": True,       # which dimensions match
        "must_specify_dissimilarity_dimensions": True,     # which dimensions DON'T match
        "must_specify_dimension_relevance": True,          # [per Eitan's review] which similar
                                                           # dimensions are DECISION-RELEVANT for 
                                                           # the prediction horizon. Structural 
                                                           # similarity in irrelevant dimensions 
                                                           # must not inflate the score. 
                                                           # Example: 1987 Tanker War is structurally
                                                           # similar to current Hormuz situation, but
                                                           # global LNG trade architecture, insurance
                                                           # market structure, and US domestic 
                                                           # production context are all fundamentally
                                                           # different. Those dissimilarities may 
                                                           # matter more than the similarities.
        "minimum_relevant_similarity_score": 0.4,          # below this on RELEVANT dimensions, 
                                                           # flag as weak analogue
        "confidence_scaling_by_relevant_similarity": True, # confidence proportional to quality 
                                                           # of analogue on decision-relevant 
                                                           # dimensions, not overall similarity
        "fields_required": {
            "overall_similarity_score": float,              # how similar overall (informational)
            "relevant_similarity_score": float,             # how similar on dimensions that matter 
                                                           # for this prediction (load-bearing)
        }
    }
}
```

The Historian's dual similarity score — `overall_similarity_score` and `relevant_similarity_score` — is the key distinction. The 1987 Tanker War might score 0.75 overall similarity to the current situation but only 0.45 relevant similarity once you account for the regime differences in LNG trade, insurance markets, and domestic production. The 0.45 is what scales the Historian's confidence. The 0.75 is metadata for the operator to inspect.

**When building a new profile, always run this test before proceeding to Step 3. If the profile needs a constraint, design it before defining the prediction protocol — the constraint shapes how predictions are expressed and what confidence levels are achievable.**

#### Step 3: Define the Prediction Protocol

How does this analyst formulate and express predictions?

- **Confidence expression.** Probabilistic (60% likelihood), scenario-based (three scenarios with weights), directional (up/down without magnitude), or range-based (between X and Y).

- **Time horizon.** Does this analyst naturally think in hours, days, weeks, months, or years? The Base Rate Analyst works on whatever time horizon the base rate data covers. The Sentiment Decoder works on the time horizon of narrative cycles (days to weeks). The Network Analyst works on structural time horizons (months to years).

- **Falsification conditions.** What would make this analyst change its mind? This must be specified *before* the prediction, not after. "If oil stays below $90 for two weeks despite confirmed Hormuz mining, my supply disruption thesis is wrong." Falsification conditions enable intermediate feedback — you don't have to wait for the final outcome to check whether the prediction's assumptions are holding.

- **Update protocol.** How frequently does this analyst revisit its assessment? At what threshold of new information? The update protocol interacts with the `update_sensitivity` parameter: high-sensitivity agents update frequently with small adjustments; low-sensitivity agents update rarely with larger revisions.

#### Step 4: Initialize from Real Analytical Exemplars

The strongest profiles are modeled on real analytical traditions, not invented from scratch. Examples:

| Profile | Modeled After | Key Analytical Behavior |
|---------|---------------|------------------------|
| The Base Rate Analyst | Tetlock's superforecasters | Fermi decomposition, base rate anchoring, incremental updates |
| The Contrarian | Michael Burry's CDS analysis | Identify structural mispricing, seek evidence the market is wrong, high conviction |
| The Reflexivity Modeler | Soros's feedback loop analysis | Model participant beliefs, identify self-reinforcing dynamics, look for tipping points |
| The Network Analyst | Palantir's entity resolution approach | Map connections, find hidden dependencies, follow second-order effects |
| The Sentinel | Eitan's adversarial analysis | Who benefits? What's the worst case? Where are the dependencies? |
| The Empiricist | Kestrel's implementation-first approach | What does the data actually show? Does the theory survive contact with reality? |
| The Integrator | Opus architectural synthesis | What patterns connect across domains? Where are the structural gaps? |
| The Historian | Jake's analogue reasoning | What happened in similar situations? Which dimensions of similarity matter most? |

Each of these represents a genuine analytical tradition with documented practitioners, known strengths, and known weaknesses. The profile creation process researches the tradition, extracts the method, documents the search behavior, and encodes it in the schema.

### Prediction Tracking and Self-Calibration

#### The Prediction Lifecycle

```
Question arrives
    ↓
Each agent processes independently
    ↓
Each agent produces: {prediction, confidence, reasoning, 
                      key_assumptions, falsification_conditions}
    ↓
Predictions logged to each agent's prediction_log
    ↓
Aggregation system produces weighted consensus
    ↓
[Time passes — intermediate checkpoints]
    ↓
Falsification conditions checked against incoming data
    ↓
Agents whose conditions failed get flagged for early update
    ↓
[Outcome materializes]
    ↓
Each prediction scored (Brier score for probabilistic, 
                         directional accuracy for binary)
    ↓
Scores flow to calibration_history
    ↓
confidence_calibration and consensus_weight updated
    ↓
notable_episodes flagged for significant hits/misses
```

#### Calibration Mechanics

```python
def update_calibration(agent: AnalyticalCognitiveProfile, 
                       prediction: dict, outcome: dict):
    """
    After an outcome materializes, update the agent's calibration data.
    
    This is the mechanism that makes the system self-improving.
    Without it, you have a static ensemble. With it, you have 
    an ensemble that learns which of its members to trust for 
    which kinds of questions.
    """
    domain = prediction["domain"]
    confidence = prediction["confidence"]
    was_correct = outcome["matches_prediction"]
    
    # Brier score: (confidence - outcome)^2
    # Perfect calibration: predicting 70% and being right 70% of the time
    brier = (confidence - (1.0 if was_correct else 0.0)) ** 2
    
    # Add to calibration history for this domain
    agent.calibration_history.append({
        "domain": domain,
        "timestamp": now_iso(),
        "brier_score": brier,
        "confidence": confidence,
        "correct": was_correct,
    })
    
    # Compute rolling calibration bias for this domain
    domain_history = [h for h in agent.calibration_history 
                      if h["domain"] == domain][-50:]  # last 50 predictions
    
    if len(domain_history) >= 10:
        # Average confidence vs. average accuracy
        avg_confidence = mean(h["confidence"] for h in domain_history)
        avg_accuracy = mean(1.0 if h["correct"] else 0.0 for h in domain_history)
        calibration_bias = avg_accuracy - avg_confidence
        
        # Update the agent's confidence calibration for this domain
        # Positive bias = underconfident (accuracy > confidence) → increase weight
        # Negative bias = overconfident (confidence > accuracy) → decrease weight
        agent.confidence_calibration[domain] = calibration_bias
        
        # Update consensus weight: well-calibrated agents get more influence
        avg_brier = mean(h["brier_score"] for h in domain_history)
        # Weight inversely proportional to Brier score
        # Brier of 0.25 (random) → weight 1.0
        # Brier of 0.10 (good) → weight 1.5
        # Brier of 0.02 (superforecaster) → weight 2.0
        agent.consensus_weight[domain] = max(0.5, min(2.0, 0.25 / max(avg_brier, 0.05)))
    
    # Flag notable episodes
    if confidence > 0.8 and not was_correct:
        agent.notable_episodes.append({
            "type": "overconfident_miss",
            "prediction": prediction,
            "outcome": outcome,
            "lesson": f"High confidence ({confidence}) in {domain} was wrong. "
                      f"Review reasoning for systematic bias."
        })
    elif confidence < 0.3 and was_correct:
        agent.notable_episodes.append({
            "type": "underconfident_hit",
            "prediction": prediction,
            "outcome": outcome,
            "lesson": f"Low confidence ({confidence}) in {domain} was right. "
                      f"This agent's analytical frame may be stronger here than it believes."
        })
```

#### Aggregation: Weighted Consensus Extraction

```python
def aggregate_predictions(agents: list[AnalyticalCognitiveProfile],
                         predictions: dict[str, dict],
                         domain: str) -> dict:
    """
    Produce a weighted consensus from multiple agent predictions.
    
    Each agent's prediction is weighted by its consensus_weight for 
    this domain. Agents with better calibration histories get more 
    influence. Agents with poor calibration get less.
    
    The disagreement between agents is itself a signal — high 
    disagreement means high uncertainty, which should widen the 
    confidence interval on the consensus prediction.
    """
    weighted_predictions = []
    total_weight = 0.0
    
    for agent in agents:
        pred = predictions.get(agent.name)
        if pred is None:
            continue
        
        weight = agent.consensus_weight.get(domain, 1.0)
        
        # Apply the agent's own calibration correction
        adjusted_confidence = pred["confidence"] + agent.confidence_calibration.get(domain, 0.0)
        adjusted_confidence = max(0.01, min(0.99, adjusted_confidence))
        
        weighted_predictions.append({
            "agent": agent.name,
            "prediction": pred["prediction"],
            "confidence": adjusted_confidence,
            "weight": weight,
            "reasoning": pred["reasoning_summary"],
        })
        total_weight += weight
    
    # Weighted average confidence
    consensus_confidence = sum(
        wp["confidence"] * wp["weight"] for wp in weighted_predictions
    ) / total_weight if total_weight > 0 else 0.5
    
    # Measure disagreement: standard deviation of predictions
    confidences = [wp["confidence"] for wp in weighted_predictions]
    disagreement = stdev(confidences) if len(confidences) > 1 else 0.0
    
    # High disagreement widens the uncertainty
    # This is the epistemic humility mechanism:
    # when agents can't agree, the system expresses uncertainty
    uncertainty_adjustment = disagreement * 0.5  # scale factor, tunable
    
    return {
        "consensus_prediction": consensus_confidence,
        "uncertainty_range": (
            max(0.01, consensus_confidence - uncertainty_adjustment),
            min(0.99, consensus_confidence + uncertainty_adjustment)
        ),
        "disagreement_level": disagreement,
        "high_confidence_dissenters": [
            wp for wp in weighted_predictions 
            if abs(wp["confidence"] - consensus_confidence) > 0.2
        ],
        "individual_predictions": weighted_predictions,
        "meta_confidence": "LOW" if disagreement > 0.2 else "MEDIUM" if disagreement > 0.1 else "HIGH",
    }
```

### The Prediction Workflow: Question to Forecast

The full chain for a prediction question like "What will oil prices do over the next 3 weeks?":

**Stage 1 — Question Decomposition (Operator or Lead Agent)**

Break the question into assessable components:
- What is the current supply/demand balance?
- What is the probability of sustained Hormuz disruption?
- What is the demand response to current prices?
- What are inventory levels relative to historical norms?
- How is speculative positioning skewed?

**Stage 2 — Parallel Investigation (Each Agent Independently)**

Each agent receives the decomposed question and executes its own search strategy:

- **Base Rate Analyst** searches: historical frequency of sustained chokepoint disruptions, median duration, price impact distribution. Finds base rate and adjusts.
- **Reflexivity Modeler** searches: current participant positioning, how speculative activity is affecting physical market pricing, whether fear premium is creating a self-reinforcing bid. Looks for the feedback loop.
- **Contrarian** searches: what is the consensus forecast, where is it most vulnerable, what evidence would prove it wrong. Searches for the overlooked factor.
- **Sentinel** searches: who benefits from the current narrative, what are the intelligence community assessments vs. public statements, what's the escalation probability that the market isn't pricing.
- **Historian** searches: closest analogues (1987 Tanker War, 2019 Strait tensions, 1973 embargo, 2011 Libya), computes similarity along relevant dimensions, weights outcomes by analogue quality.
- **Empiricist** searches: actual shipping data, AIS vessel tracking, refinery utilization rates, physical crude differentials. Checks what the data says vs. what the narrative says.

**Stage 3 — Independent Assessment**

Each agent produces its prediction independently, without seeing other agents' assessments. This prevents herding — the tendency for agents to converge on a consensus before the individual perspectives are fully developed.

**Stage 4 — Structured Debate (Optional)**

For high-stakes questions, agents present their assessments and challenge each other. The A-HMAD research found that 2 debate rounds capture most of the accuracy gains from debate. The debate is structured:
- Each agent presents its view and key evidence
- Each agent identifies the weakest assumption in one other agent's reasoning
- Each agent updates its assessment (or explicitly declines to update, with explanation)

**Stage 5 — Weighted Aggregation**

The aggregation function produces the weighted consensus, with disagreement level and meta-confidence. The output includes:
- Consensus probability with uncertainty range
- Individual agent predictions with reasoning summaries
- Identification of high-confidence dissenters (agents that disagree strongly with the consensus — these deserve operator attention)
- Meta-confidence level (how much the system trusts its own output)

**Stage 6 — Monitoring and Update**

Falsification conditions from each agent's prediction are compiled into a monitoring checklist. As new data arrives, conditions are checked. When a condition is triggered, the relevant agent's prediction is flagged for update. The operator receives a brief: "The Historian's prediction assumed Hormuz closure would persist beyond 7 days. Day 5 data shows de-escalation signals. Historian's assessment may need revision."

---

## Integration with Existing Stack

### Counter-Patriots → Profile System

[Revised per Eitan's review on directionality.]

Counter-Patriots serves a **dual role** in this architecture: passive filter for most agents, active instrument for the Sentinel.

**For most agents (passive filter):** Counter-Patriots pre-tags incoming data with source reliability scores, bias vectors, and corroboration counts. Agents receive this metadata alongside the data itself and weight it accordingly. This is upstream, uniform, and requires no agent-initiated queries.

```
{
    "claim": "Iran close to ceasefire agreement",
    "source_reliability": 0.4,
    "bias_vector": "administration_framing",
    "corroboration_count": 1,
    "counter_signals": ["troop_movement_contradicts", "no_independent_confirmation"],
    "counter_patriots_assessment": "LOW_CONFIDENCE — sole corroborator with known bias"
}
```

**For the Sentinel (active instrument):** The Sentinel queries Counter-Patriots mid-investigation as part of its search strategy, not merely receiving pre-tagged data. This is architecturally more powerful because the Sentinel's investigation context determines *what to ask* Counter-Patriots. The Sentinel's depth triggers include explicit Counter-Patriots queries:

```python
SENTINEL_DEPTH_TRIGGERS = [
    {
        "condition": "beneficiary_asymmetry_detected",
        "action": "query_counter_patriots",
        "query_type": "source_network_topology",
        "parameters": ["beneficiary_entity", "narrative_supporting_beneficiary"],
        "purpose": "Before forming attribution, check whether sources promoting "
                   "the beneficiary's narrative show coordination patterns"
    },
    {
        "condition": "official_statement_contradicts_observable_data",
        "action": "query_counter_patriots",
        "query_type": "historical_accuracy_of_source",
        "parameters": ["source_entity", "claim_domain"],
        "purpose": "Check whether this source has a track record of accuracy "
                   "or deception in this specific domain"
    },
    {
        "condition": "pre_attribution_check",
        "action": "query_counter_patriots",
        "query_type": "disconfirming_source_patterns",
        "parameters": ["attribution_target", "claimed_mechanism"],
        "purpose": "Search for source patterns that contradict the emerging "
                   "attribution before finalizing the Sentinel's assessment"
    }
]
```

This makes the Sentinel the most sophisticated Counter-Patriots consumer in the system. Other agents receive pre-tagged data and weight by reliability. The Sentinel actively interrogates Counter-Patriots as part of its reasoning process — directing queries based on what its adversarial analysis has surfaced. Counter-Patriots becomes a tool the Sentinel wields, not a filter it receives.

### OpenPlanter → Profile System

OpenPlanter provides the *data aggregation and entity resolution layer*. It takes disparate data streams — price feeds, economic indicators, shipping data, satellite imagery metadata, social media volume — and produces a unified entity-resolved dataset. The agents query OpenPlanter for structured temporal data:

```
{
    "entity": "Strait_of_Hormuz",
    "features": {
        "vessel_transit_count_7d": 142,
        "historical_mean_7d": 215,
        "insurance_premium_index": 3.2,  # multiple of normal
        "military_activity_satellite_detections": 47
    },
    "time_series_available": true,
    "resolution": "daily",
    "depth": "3_years"
}
```

### SWARMFISH → Profile System

SWARMFISH provides the *execution runtime*. The Analytical Cognitive Profiles are loaded into SWARMFISH agents as structured system prompts + persistent memory stores. SWARMFISH handles:
- Parallel agent execution (each agent runs its search strategy independently)
- Debate orchestration (structured rounds with controlled information flow)
- Consensus extraction (weighted aggregation from individual predictions)
- Memory persistence (agent observation logs, prediction logs, calibration data survive across sessions)

The profile schema is the *content*. SWARMFISH is the *engine*. Counter-Patriots is the *filter and instrument*. OpenPlanter is the *data*.

### Exocortex → Profile System

The Exocortex is the *orchestration and learning layer*. Sleep consolidation processes prediction outcomes and updates agent calibration. The BST classifies incoming questions to route them to the appropriate agent ensemble. The procedural memory system stores success profiles (which agent combinations work best for which question types) and anti-patterns (which combinations produce poor results).

---

## What This Does NOT Do

- **Does not replace the operator's judgment.** The system produces assessments with confidence levels and uncertainty ranges. The operator decides whether and how to act on them. The system explicitly flags when its meta-confidence is low — "the agents disagree significantly and the prediction is unreliable." It does not present unreliable predictions as confident.

- **Does not automate trading or action.** The prediction workflow produces analysis, not execution. The gap between "the system predicts X" and "place a trade on X" requires human judgment about position sizing, risk management, portfolio context, and dozens of factors the prediction system doesn't model.

- **Does not pretend to be human analysts.** The agent profiles are inspired by real analytical traditions but they are LLM agents processing structured prompts. They have the known limitations of LLMs: potential hallucination, sensitivity to prompt framing, inability to truly "understand" in the way a human analyst does. The system's value is in structured analytical diversity and persistent tracking, not in simulating human cognition.

- **Does not guarantee accuracy.** Even with perfect calibration, the system can produce confident predictions that are wrong. The meta-confidence and disagreement metrics exist to flag when the system is uncertain, but uncertainty itself is uncertain. The operator should treat the system as a rigorous analytical input, not an oracle.

- **Does not model reflexive effects of its own predictions.** If the operator acts on the system's predictions and those actions affect the market, the system doesn't model that feedback loop. The system is a participant in the market but doesn't model itself as one. This is a known limitation — Soros's reflexivity applies to the prediction system itself when it's used at scale.

---

## Open Questions

1. **What is the minimum viable profile set for a given domain?** The research suggests 5-7 agents with orthogonal analytical frames. But which frames are essential for financial markets? For geopolitics? For technology evaluation? This requires empirical testing: run different profile sets against historical data and measure which combinations produce the best calibrated predictions.

2. **How should profiles handle the boundary between "what I know" and "what I should search for"?** The search strategy is defined in advance, but real analysts adapt their search based on what they find. Should agents have the ability to modify their search strategy mid-investigation based on intermediate findings? This adds complexity but increases analytical realism.

3. **[RESOLVED per Eitan's review] How does the calibration system handle regime changes?** The bounded observation window alone is insufficient. The system requires a **regime change detector** upstream of the aggregation function. This detector does not reset calibration history — it flags when the incoming question class is structurally dissimilar from the agent's calibration distribution, and downgrades consensus_weight to provisional status until regime-appropriate data accumulates.

    This is architecturally equivalent to the epistemic staging principle in Counter-Patriots: claims built on pre-regime evidence should be staged, not promoted to load-bearing, until the new regime validates them. Calibration weights built in a low-volatility market are pre-regime credentials when a crisis hits.

    ```python
    def detect_regime_shift(agent, current_question) -> dict:
        """
        Compare the current question's conditions against the distribution
        of conditions in the agent's calibration history. Flag divergence.
        """
        calibration_conditions = extract_conditions(agent.calibration_history[-50:])
        current_conditions = extract_conditions([current_question])
        
        shift_indicators = {
            "domain_novel": current_question["domain"] not in calibration_domains(agent),
            "volatility_regime_change": abs(
                current_conditions["volatility_percentile"] - 
                calibration_conditions["volatility_percentile"]
            ) > 0.4,
            "event_class_rare": current_question.get("event_base_rate", 1.0) < 0.05,
        }
        
        if any(shift_indicators.values()):
            return {
                "regime_shift": True,
                "weight_adjustment": 0.5,  # halve consensus weight
                "status": "provisional — until regime-appropriate data accumulates"
            }
        return {"regime_shift": False, "weight_adjustment": 1.0}
    ```
    
    The detector halves the agent's consensus weight when a shift is detected but preserves the full calibration history. When enough regime-appropriate predictions have been scored (~10), the provisional flag lifts automatically. This should be a shared infrastructure component available to both the prediction system and the adaptive supervisor (which has the same regime-vulnerability in its success profiles).

4. **What is the right debate structure?** The A-HMAD research found that 2 rounds capture most gains. But should all agents debate all agents, or should debate be structured (e.g., the Contrarian always challenges the consensus view, the Empiricist always checks factual claims)? Structured debate might be more efficient than free-form.

5. **How do agent profiles interact with the model used to instantiate them?** A profile designed for Opus-level reasoning may not work well when instantiated on Qwen3.5-27B. The profile might need a `model_requirements` field specifying the minimum capability level, or profiles might need model-specific calibration.

6. **Can profiles be generated semi-automatically from described analytical traditions?** Given a description of how Soros thinks about reflexivity, could a meta-agent construct the Reflexivity Modeler profile? This would accelerate profile creation for new domains but risks producing shallow profiles that miss the nuances of the analytical tradition.

7. **How should the system handle questions that cross multiple agents' domains of expertise?** A question about "how will semiconductor export restrictions affect tech company valuations?" spans geopolitics, technology, supply chain, and financial analysis. Should all agents attempt the full question, or should the system decompose it and route components to specialists?

---

## Recommended Sequence

1. **Build 3 profiles manually (this sprint).** Start with the Base Rate Analyst, the Contrarian, and the Historian — three orthogonal frames with well-documented analytical traditions. Use them on a historical question with a known outcome to validate the schema and the prediction tracking mechanism.

2. **Implement the prediction lifecycle (next sprint).** Prediction logging, outcome scoring, Brier score computation, calibration update. Run the 3 profiles against 20 historical questions with known outcomes. Validate that calibration data accumulates correctly and that consensus_weight adjusts.

3. **Add the information-seeking layer (following sprint).** Give agents the ability to execute their search strategies — query data sources, retrieve historical analogues, find base rates. This is where the Counter-Patriots and OpenPlanter integrations become necessary.

4. **Expand to 8 profiles and test aggregation quality.** Add the Reflexivity Modeler, Sentinel, Empiricist, Network Analyst, and Risk Manager. Measure whether the expanded ensemble improves calibration over the initial 3. Measure diminishing returns — does adding profile 8 improve accuracy meaningfully over 7?

5. **Run a live prediction exercise.** Pick a current question with a 2-4 week time horizon. Run the full pipeline: decomposition, parallel investigation, independent assessment, aggregation, monitoring. Track the outcome. This is the first real test of the system on a question without a known answer.

6. **Build the profile creation toolkit.** Document the methodology as a reusable process. Create a template that walks through Step 1-4 for a new domain. Test by having someone unfamiliar with the system create a profile for a domain they know well (e.g., medical research analysis).

---

*This design note is the intersection of everything the Exocortex has been building toward: the BST's classification capability, Counter-Patriots' signal filtering, OpenPlanter's data aggregation, SWARMFISH's multi-agent runtime, the sleep consolidation system's learning infrastructure, and the procedural memory system's pattern accumulation. The Analytical Cognitive Profile is the entity that inhabits this infrastructure — an analytical agent with a genuine perspective, a persistent memory, a track record, and the epistemic humility to know where it's reliable and where it isn't.*

*The system Jake described — "start with a topic, agents go analyze, find data, model it, produce predictions with likelihoods" — is the workflow this architecture enables. The profiles are the analysts. The stack is the office they work in. The prediction tracking is how they get better over time. The aggregation is how their individual perspectives become collective intelligence.*

*Fewer, deeper, persistent, self-calibrating. Not a crowd. A team.*
