# Analyst Signal Capture — Design Note
## Dual-Tag Manual Flagging Workflow

**Status:** Pre-spec exploration. Motivated by Session 056 discussion of Counter-Patriots as an information aggregation system operating on curated social media feeds. Jake described two distinct signal types in his analytical process — recognition-based ("I know what this is") and anomaly-based ("something about this doesn't fit"). These require different capture mechanisms, different training signals for agents, and different downstream processing. No eval data yet. This document describes the tagging architecture, the thesis tree structure it feeds, and the training loop that teaches agents the analyst's process.

---

## The Problem

### What Exists
Counter-Patriots has an ingestion pipeline, a claim store, a contradiction detector, silence detection, activation pattern recognition, and a drift tracker. All of these operate on claims that are already in the system. The system processes information. It does not capture it.

### What's Missing
The interface between the analyst and the system. Jake currently runs his analytical process entirely in his head — scanning social media, monitoring TradingView, cross-referencing developments with Eitan, building and updating thesis structures across geopolitics and markets simultaneously. None of this enters the system. The analyst's decade of pattern recognition, source calibration, and anomaly detection exists as wetware with no external record.

### The Gap
The system has no ingestion mechanism for the analyst's real-time observations. When Jake sees a post that triggers recognition ("that's priming") or anomaly detection ("something about this doesn't fit"), that signal lives in his head until he mentions it in conversation. No timestamp. No source link. No longitudinal record. No way for agents to learn from the observation unless Jake manually explains it later.

### The Motivating Observation
Session 056. Jake described his workflow: scanning Twitter for market news and geopolitics, flagging posts that trigger either recognition or anomaly signals, cross-referencing with TradingView price data, consolidating with Eitan, tracking how narratives evolve over hours and days. He's been doing this for over ten years. The Exocortex is what happens when that process gets externalized into infrastructure agents can learn from.

When asked what the signal detection moment feels like, Jake confirmed: both recognition and anomaly, and he can usually tell the difference in the moment. The system needs to capture both, differently, because they train differently and produce different downstream intelligence.

---

## Design Principles

1. **The analyst is the filter.** No automated ingestion replaces Jake's judgment about what matters. The system receives what the analyst flags, not what an algorithm selects. Automated monitoring is a future layer that operates *downstream* of the analyst's trained priorities, not upstream of them.

2. **Two tag types, two workflows.** Recognition and anomaly signals are structurally different. Collapsing them into a single "flag" mechanism loses the training signal that distinguishes known-pattern detection from novel-pattern discovery. The system must capture which type the analyst is exercising at the moment of flagging.

3. **Capture first, classify later.** For anomaly tags, the analyst may not know why something matters at the moment they notice it. The system must accept a raw flag with minimal metadata and allow classification to be added later — hours or days later — when the significance crystallizes. Forcing immediate classification on anomaly signals would suppress the most valuable flags (the ones the analyst can't yet explain).

4. **Everything gets timestamped and sourced.** Every flag enters the system with: timestamp of observation, source URL or reference, source profile (auto-populated from Source Intelligence if available), and the raw content. This is non-negotiable. The longitudinal record is the system's primary value.

5. **Tags feed thesis trees.** Individual flags are atomic observations. Their value compounds when connected to the analyst's working thesis structure. Every flag should optionally connect to a thesis node — "this observation affects my base case about X." The thesis tree is where individual signals become intelligence.

6. **The training loop is implicit.** Agents learn from the accumulated tagging data without a separate training phase. The pattern of what Jake flags, how he classifies it, and what proves important over time *is* the training data. The agents' future automated flagging emerges from this record.

---

## The Two Tag Types

### Recognition Tag — "I know what this is"

The analyst sees something that matches a known analytical pattern. The classification is available immediately because the pattern is already in the analyst's repertoire.

**Capture format:**
```json
{
  "tag_type": "recognition",
  "timestamp": "2026-03-12T14:23:00Z",
  "source_url": "https://x.com/example/status/123456",
  "source_handle": "@example",
  "source_profile_id": null,
  "raw_content": "Captured text or screenshot reference",
  "classification": "priming",
  "classification_options": [
    "priming",
    "narrative_shift", 
    "cross_partisan_convergence",
    "cui_bono_trigger",
    "silence_break",
    "coordinated_amplification",
    "attribution_leap",
    "asymmetric_skepticism",
    "emotional_escalation",
    "framing_without_evidence",
    "source_pivot",
    "timing_anomaly",
    "custom"
  ],
  "analyst_note": "Free text — why this matters, what it connects to",
  "thesis_node_id": null,
  "confidence": "high",
  "market_relevance": true,
  "related_assets": ["CL=F", "VIX"],
  "flagged_by": "jake"
}
```

**What the system does on receipt:**
1. Timestamp and store (append-only)
2. Query Source Intelligence for source profile — auto-populate if exists, queue for profiling if new
3. Stage the claim in the Retcon Ledger with the analyst's classification as the technique_class
4. If thesis_node_id is provided, attach to thesis tree and propagate confidence impact
5. Begin watching for corroboration, contradiction, drift from this claim
6. Log to training corpus: {classification, source_type, content_features, timestamp_context}

**Training signal:** The accumulated recognition tags teach agents which patterns Jake identifies and how he classifies them. Over time, agents learn: "content with these features, from this type of source, at this time of day, during this kind of event — Jake classified this as priming." The agent can then pre-flag similar patterns for analyst review.

### Anomaly Tag — "Something about this doesn't fit"

The analyst sees something that triggers attention without a clear classification. The not-fitting is the signal. Classification comes later or never — some anomalies remain unexplained but were still worth capturing.

**Capture format:**
```json
{
  "tag_type": "anomaly",
  "timestamp": "2026-03-12T14:23:00Z",
  "source_url": "https://x.com/example/status/789012",
  "source_handle": "@unfamiliar_account",
  "source_profile_id": null,
  "raw_content": "Captured text or screenshot reference",
  "classification": null,
  "gut_note": "Free text — what felt off. Can be vague. 'timing seems wrong' or 'why is this account asking this question' or just '???'",
  "thesis_node_id": null,
  "market_relevance": null,
  "flagged_by": "jake",
  
  "annotation": null,
  "annotated_at": null,
  "annotation_classification": null,
  "resolved": false,
  "resolution": null
}
```

**What the system does on receipt:**
1. Timestamp and store (append-only)
2. Query Source Intelligence for source profile
3. Stage as observation in the Retcon Ledger — no technique_class yet, staged with note "anomaly flag, classification pending"
4. If thesis_node_id is provided, attach as an unclassified branch point
5. Begin watching — but the system doesn't know what to watch *for* yet, so it watches broadly: source posting frequency changes, narrative developments around the flagged content, market movements in the time window
6. Queue for analyst re-visit — surface in a daily or session-end review: "You flagged these anomalies. Any of them make sense now?"

**Annotation workflow:**
The analyst returns to anomaly tags when significance crystallizes. Could be hours, days, or weeks later. The annotation adds:
- Classification (from the recognition tag's classification_options, or "novel_pattern" with description)
- Resolution: what the anomaly turned out to be — confirmed signal, false alarm, still unknown
- Connection to thesis if now apparent

**Training signal:** Anomaly tags are the higher-value training data precisely because they capture the analyst's pre-conscious pattern detection. The features of content that Jake flags as anomalous *before he can explain why* — those features are the system's path to catching anomalies the analyst hasn't seen before. The agent that learns "content with these features tends to get anomaly-flagged by Jake, and 40% of the time the annotation reveals it was a [timing_anomaly]" can eventually pre-flag similar content for analyst review with a suggested classification.

The annotated anomalies that turned out to be real signals are the most valuable training examples in the corpus. They document the moment between intuition and understanding — the shape of what surprises the analyst.

---

## The Thesis Tree

Individual flags are atomic. The thesis tree is where they become intelligence.

### Structure

```
ROOT: "Energy prices will continue to climb due to 
       Strait of Hormuz disruption"
  │
  ├── BRANCH: Strait status
  │     ├── NODE: "Will they close it?" [resolved: no direct closure]
  │     ├── NODE: "Will they mine it?" [resolved: yes, confirmed]  
  │     └── NODE: "Mining impact on shipping insurance" [active]
  │           └── TAG: [recognition: priming] "Administration claims 
  │               war almost over" — contradicts observed mine activity
  │
  ├── BRANCH: Market pricing
  │     ├── NODE: "Crude not adequately pricing disruption" [active]
  │     │     └── TAG: [anomaly] "Why is Brent only at $X when 
  │     │         insurance rates suggest $Y?" [annotated: market 
  │     │         pricing narrative not reality]
  │     └── NODE: "VIX short positioning" [active]
  │           └── TAG: [recognition: cui_bono_trigger] "55,700 net 
  │               short contracts built on 'short conflict' narrative"
  │
  ├── BRANCH: Narrative landscape
  │     ├── NODE: "Administration 'almost over' framing" [active]
  │     ├── NODE: "COVID parallel — 6 week lag pattern" [hypothesis]
  │     └── NODE: "Communist publication + antisemitic account 
  │         convergence" [recognition: cross_partisan_convergence]
  │
  └── BRANCH: Supply chain cascade
        ├── NODE: "Energy → inflation mechanism" [structural]
        └── NODE: "Historical parallel: COVID supply shock" [reference]
```

### Schema

```sql
CREATE TABLE thesis_trees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    root_statement TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(32) DEFAULT 'active',
    overall_confidence FLOAT DEFAULT 0.5,
    created_by VARCHAR(64) NOT NULL
);

CREATE TABLE thesis_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tree_id UUID NOT NULL REFERENCES thesis_trees(id),
    parent_node_id UUID REFERENCES thesis_nodes(id),
    statement TEXT NOT NULL,
    node_type VARCHAR(32) NOT NULL, 
    -- 'branch', 'hypothesis', 'resolved', 'structural', 'reference'
    status VARCHAR(32) DEFAULT 'active',
    -- 'active', 'confirmed', 'falsified', 'superseded'
    confidence_impact FLOAT DEFAULT 0.0,
    -- positive = strengthens root thesis, negative = weakens
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT
);

CREATE TABLE tag_thesis_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_id UUID NOT NULL,  -- references analyst_tags
    tag_type VARCHAR(16) NOT NULL,  -- 'recognition' or 'anomaly'
    node_id UUID NOT NULL REFERENCES thesis_nodes(id),
    impact_direction VARCHAR(16), 
    -- 'strengthens', 'weakens', 'complicates', 'unknown'
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    analyst_note TEXT
);
```

### Confidence Propagation

When a tag is linked to a thesis node with an impact direction, the system propagates the confidence impact up the tree to the root. This is not automatic re-evaluation of the thesis — it's a running tally that the analyst can query: "What's happened since I last looked at this thesis? Net positive or net negative?"

```python
def propagate_confidence(tag_link):
    """
    Walk from the linked node up to root,
    accumulating confidence impact.
    """
    node = get_node(tag_link.node_id)
    impact = tag_link.impact_value()
    
    while node is not None:
        node.update_confidence_tally(impact)
        node.last_updated = now()
        node = node.parent
    
    # Root thesis gets the accumulated signal
    tree = get_tree(node.tree_id)
    tree.last_updated = now()
    # Does NOT auto-update overall_confidence
    # That's the analyst's call after reviewing the tally
```

The system accumulates. The analyst decides. The Curtis Rule holds — the tree tracks what's happened, the analyst updates confidence.

---

## The Training Loop

The manual tagging workflow generates training data as a side effect of normal analytical work. No separate training phase required.

### What Agents Learn From Recognition Tags
- Feature → classification mappings: "content that looks like X, from source type Y, during event type Z, Jake classifies as [priming]"
- Source-classification correlations: "this source produces content Jake consistently classifies as [asymmetric_skepticism]"
- Temporal patterns: "Jake flags more [emotional_escalation] content during the first 48 hours of a crisis"
- Market-relevance correlations: "when Jake marks a recognition tag as market_relevant with assets [CL=F, VIX], the thesis tree it connects to is usually about energy/conflict"

### What Agents Learn From Anomaly Tags
- Feature profiles of content that triggers anomaly detection: "content with these textual features, from accounts with these profile characteristics, at these times — Jake anomaly-flags it"
- Annotation rates: "40% of Jake's anomaly tags on accounts with <6 months history eventually get annotated as [source_pivot]"
- Resolution patterns: "anomalies flagged during high-volatility windows resolve as real signals at 2x the rate of baseline anomalies"
- The shape of surprise: what *doesn't* match Jake's existing recognition patterns but still matters

### What Agents Learn From Thesis Trees
- How Jake structures analytical positions: root cases, branch types, evidence linkage patterns
- Which branches Jake monitors most actively (proxy for current analytical priorities)
- How confidence impacts propagate: what kinds of evidence Jake considers thesis-strengthening vs thesis-weakening
- The relationship between information domain observations and market domain positions

### The Feedback Cycle

```
Jake flags → System stores and watches → 
  Evidence arrives → System surfaces to Jake →
    Jake evaluates → Updates tag/thesis → 
      Training corpus grows → Agent pattern library deepens →
        Agent pre-flags similar content → Jake reviews agent flags →
          Corrects agent errors → Training corpus refines →
            Agent accuracy improves
```

The cycle is slow at first — weeks to months before the agent's pre-flags are useful. The value during that period is entirely in the longitudinal record: the timestamped, sourced, classified history of what Jake observed, what he thought it meant, and what actually happened. That record alone is worth the system, even if the agent training never fires.

---

## Integration Points

### → Source Intelligence
Every flag triggers a Source Intelligence profile lookup. New sources get queued for profiling. The Source Intelligence network topology data enriches the flag: "this source is in the same amplification cluster as three others you flagged this week."

### → Retcon Ledger
Recognition tags enter the ledger as staged claims with technique_class. Anomaly tags enter as staged observations without classification. Both participate in the full ledger lifecycle: corroboration, promotion, falsification.

### → Contamination Cascade
If a source that contributed recognition tags later collapses in trust, the contamination cascade traces through every tag that source contributed to, every thesis node those tags influenced, every confidence propagation those links produced. The thesis tree confidence tally gets re-evaluated with the contaminated contributions removed.

### → Silence Detection
The absence of expected flags is itself a signal. If Jake normally flags 5-10 items per day on a topic and suddenly flags zero during a high-activity period, the system should notice. Either the topic went quiet (silence detection on the feed), or Jake is overloaded and not flagging (operator state monitoring from the sleep consolidation research). Both are actionable.

### → Sleep Consolidation
During idle time, the sleep process reviews the accumulated tags and identifies patterns the analyst may not have noticed: "You flagged 7 anomalies this week from accounts less than 3 months old. 5 of them were in the same amplification cluster. You haven't connected them yet." The sleep process surfaces cross-tag patterns for the analyst's next session.

### → SWARMFISH
Thesis trees can be used as seed material for simulations. "My thesis is that energy prices climb due to Hormuz disruption. Run the simulation forward: what happens to the narrative landscape and market pricing under three scenarios?" The simulation's predictions register in the Retcon Ledger. The thesis tree tracks whether reality matches the simulation.

---

## Operational UX

The system must be fast enough to use in Jake's actual workflow: scanning Twitter, bouncing to TradingView, back to Twitter, consulting Eitan. The tagging interface cannot require more than a few seconds per flag. If it's slower than Jake's current process (noticing and moving on), he won't use it.

**Minimum viable interaction:**
1. See something on Twitter
2. Copy URL (or use browser extension / shortcut)
3. One-click: recognition or anomaly
4. For recognition: select classification from dropdown (< 2 seconds)
5. For anomaly: optional gut_note text field (< 5 seconds, can be empty)
6. Optional: link to thesis node (dropdown of active thesis roots and recent nodes)
7. Done. System handles everything else.

The annotation workflow for anomalies is separate — a review interface surfaced at session end or on demand. Not in the critical path of the real-time scanning workflow.

**What the system shows back:**
When Jake queries the system — "what's happened on my energy thesis today?" — the response is the thesis tree with all today's tags attached, confidence tally updated, any corroborations or contradictions the system detected independently, and any silence flags or activation patterns on related topics. The analyst sees his own observations plus the system's autonomous monitoring in a single view.

---

## What This Does NOT Do

- **Does not replace the analyst's judgment.** The system captures what Jake flags. It does not flag independently until the training corpus is deep enough and the agent's accuracy is validated by the analyst. The training loop is slow by design — premature automation produces false confidence.

- **Does not auto-classify anomaly tags.** The whole point of the anomaly tag is that classification isn't available yet. The system holds the raw flag patiently. Some anomalies never get classified. That's fine. The unresolved anomalies are data about the limits of the analyst's pattern library.

- **Does not generate counter-narratives or trading recommendations.** The Curtis Rule holds. The system records. The analyst decides what to do — in the information domain and in the market domain. The thesis tree tracks confidence, not positions.

- **Does not require internet-facing infrastructure.** The tagging interface runs locally. The storage is PostgreSQL in Docker. The Source Intelligence profiling uses the same infrastructure as the rest of Counter-Patriots. No cloud dependencies in the critical path.

---

*Motivated by Session 056. Jake: "I am Jake, and I'm an analyst." The system that externalizes his analytical process needs to capture both kinds of signal he produces — the patterns he recognizes and the anomalies he can't yet explain. Both are trainable. Both compound over time. The recognition tags teach agents what Jake already knows. The anomaly tags teach agents how Jake discovers what he doesn't know yet. The second is more valuable.*

*For Kestrel build planning. For Eitan integration with Counter-Patriots Spec A and the Cognitive Defense System. For Opus to review against the thesis tree schema and the sleep consolidation training loop.*

*The analyst is the filter. The system is the memory. Over time, the memory becomes intelligence.*
