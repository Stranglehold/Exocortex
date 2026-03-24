# Counter-Patriots: Source Intelligence Module
## Design Note — March 12, 2026

*Emerged from analysis of a RetroCoast (@RetroCoast) post during the Iran War, Day 12. The post arrived at a structurally valid conclusion (false flag risk) via an unverifiable attribution path with named actors. Source analysis was the missing layer — the narrative analysis couldn't be completed without understanding who was producing the narrative and why. This module fills that gap.*

*For integration into Counter-Patriots Spec A. Flag for Opus architectural review.*

---

## Position in the Architecture

Source Intelligence sits **upstream of all other Counter-Patriots functions**. It is the prerequisite layer.

Narrative Drift Detection cannot assess whether a narrative is drifting without knowing if the sources pushing it are reliable, biased, or activated. The Retcon Ledger cannot assign credible initial staging confidence without source provenance. Activation Pattern Recognition cannot distinguish organic concern from coordinated seeding without understanding source network topology.

The agent runs Source Intelligence first. It produces a source profile before any claim from that source enters the analysis pipeline. When a human operator queries about a source, the agent's profile is already built — the human receives a synthesis of what the agent verified, what it couldn't, and how that source has functioned inside prior Counter-Patriots analyses.

**The design priority:** The agent should understand source depth before the human operator asks. The human query is retrieval, not initiation.

---

## The Vector Set

Each vector is structured for agent processing: a question the agent can operationalize, a data source it can access, and an output type (score, flag, or descriptor) the agent can reason from. Vectors are independent — a source can score well on some and poorly on others. The profile holds the full distribution, not a collapsed single score.

### I. Identity Vectors

**Account Age vs. Topic Onset**
- *Question:* How long has this account existed, and when did it begin posting on this topic?
- *Data:* Account creation date, first post in topic domain, post volume over time
- *Output:* Descriptor — "legacy account, topic pivot [date]" / "new account, topic-consistent since creation" / "dormant account, sudden activation [date]"
- *Signal:* Long-dormant accounts that activate suddenly on a specific conflict are different from accounts with years of consistent topical history. The pivot timestamp and precipitating event matter more than account age alone.

**Location Coherence**
- *Question:* Does the stated location match inferred location from posting behavior?
- *Data:* Stated profile location, posting timezone distribution, cultural/linguistic markers, referenced local events
- *Output:* Flag — coherent / incoherent / insufficient data
- *Signal:* Incoherence isn't disqualifying, but it warrants noting. A stated US-based account posting consistently at 3-4am EST on a regular schedule is worth flagging.

**Network Position**
- *Question:* Who amplifies this source? Who does this source amplify? What cluster do they occupy?
- *Data:* Repost/retweet graph, reply patterns, mutual engagement network
- *Output:* Descriptor — cluster membership, amplification asymmetry (do they receive amplification from accounts with known affiliations?)
- *Signal:* A source that is consistently amplified by accounts associated with a specific government or ideological network, without reciprocal amplification across the broader discourse, is operating in a non-organic distribution pattern.

---

### II. Topical Vectors

**Domain History**
- *Question:* What did this source post about before this conflict? Did they pivot?
- *Data:* Full post history topic distribution, binned by quarter
- *Output:* Descriptor — primary domain history, pivot event if applicable, pivot character (gradual vs. sudden)
- *Signal:* The pivot is the key event. Gradual topical evolution (general political commentary → regional geopolitics → Iran conflict) is different from a sudden hard pivot (cooking → Iranian false flag analysis, same week). When did the pivot occur, and what was happening in the world that week?

**Coverage Breadth**
- *Question:* Does this source cover the conflict from multiple angles or only one?
- *Data:* Post topic distribution within conflict coverage — which actors, which events, which framings receive attention
- *Output:* Score — breadth index (0 = single-angle, 1 = multi-angle)
- *Signal:* A source that covers Iranian actions but never covers US/Israeli actions, or vice versa, is operating with selective attention. This doesn't make their claims false. It constrains how much weight they can carry.

**Topical Narrowing During Crisis**
- *Question:* Does posting narrow onto a single thread during high-stakes events?
- *Data:* Topic distribution during conflict windows vs. baseline
- *Output:* Flag — narrowing detected / baseline consistent
- *Signal:* A source that normally covers many topics but suddenly narrows to a single attribution thread during a crisis (e.g., all posts become Mossad/FBI false flag framing) may be activated or may simply be focused. The question is whether the narrowing is explained by the news or precedes it.

---

### III. Bias Vectors

**Skepticism Asymmetry**
- *Question:* Does this source apply the same level of skepticism to all actors, or is skepticism directional?
- *Data:* Language analysis — hedging language ("allegedly," "reportedly," "claimed") distribution by actor referenced
- *Output:* Score — symmetry index. Flag asymmetric cases with examples
- *Signal:* A source that demands sourcing for claims about Actor A but accepts unsourced claims about Actor B is operating with a prior, not an analytical framework. The asymmetry is the tell.

**Named Perpetrator Frequency**
- *Question:* How often does this source skip the inference chain and go directly to named attribution?
- *Data:* Post analysis — ratio of posts with named perpetrators to posts with stated uncertainty
- *Output:* Score — attribution leap frequency. High score = goes to named actors without documented inference steps
- *Signal:* The RetroCoast post scored high on this vector. The inference chain (who benefits → who has capability → what evidence exists) was skipped. Named actors (Mossad/FBI) appeared in the same sentence as "false flag." That move is the distinguishing feature between legitimate structural analysis and narrative seeding.

**Beneficiary Blind Spots**
- *Question:* Are there actors whose potential benefit from events this source never analyzes?
- *Data:* Longitudinal scan — which actors appear in cui bono analysis, which never appear
- *Output:* Descriptor — named blind spots with examples
- *Signal:* A source that consistently asks "who benefits?" but never applies that question to the country they are implicitly defending is not doing structural analysis. They are doing directed attribution with the appearance of structural analysis.

---

### IV. Behavioral Vectors

**Timing Relative to Wire Services**
- *Question:* Do posts arrive before, concurrent with, or after major wire service confirmation?
- *Data:* Post timestamps vs. Reuters/AP/AFP first-report timestamps for same events
- *Output:* Descriptor — consistently ahead / concurrent / lagging, with outlier examples flagged
- *Signal:* Sources that consistently post specific attribution claims before wire confirmation are either in possession of intelligence, are guessing, or are part of a seeding operation. The pattern across multiple events is more diagnostic than any single instance.

**Confidence Register Consistency**
- *Question:* Does this source modulate confidence language based on evidence quality, or do all claims arrive at the same confidence level?
- *Data:* Language analysis — certainty markers ("confirmed," "definitive," "clearly") vs. uncertainty markers ("reportedly," "allegedly," "possible") distribution relative to actual verification status
- *Output:* Flag — calibrated / uncalibrated
- *Signal:* Calibrated sources sound more uncertain when evidence is thin and more certain when evidence is strong. Uncalibrated sources sound equally certain regardless. The latter is a reliability problem regardless of whether they happen to be correct.

**Correction Behavior**
- *Question:* When this source has been demonstrably wrong, do they update, correct, delete, or continue as if the claim was never made?
- *Data:* Historical post record, deletions where detectable, corrections issued
- *Output:* Descriptor — updates with attribution / silent deletion / no correction behavior observed / insufficient history
- *Signal:* A source that deletes wrong posts rather than correcting them is managing appearance rather than seeking truth. Correction behavior is one of the highest-reliability indicators of analytical integrity.

**Crisis Amplification Pattern**
- *Question:* Does posting volume and intensity on specific topics increase during crises involving specific regions or actors?
- *Data:* Post volume and topic distribution during conflict windows vs. baseline periods
- *Output:* Score — amplification ratio by conflict type. Flag if ratio is asymmetric by region
- *Signal:* All sources post more during crises. The question is whether the amplification is symmetric (they post more about all crises) or asymmetric (they post dramatically more when this specific actor or region is involved). Asymmetric amplification is a revealed preference.

---

## The Agent's Output Format

When a human operator queries a source, the agent produces a structured brief with three sections. This is not a verdict — it is a synthesis of what the agent found and where the limits of verification lie.

### Section 1: What the Agent Positively Verified
Concrete, sourced facts. Account creation date. Topic pivot date and what was happening that week. Amplification network cluster membership with examples of who amplifies them. Specific posts demonstrating named patterns (attribution leaps, asymmetric skepticism, confidence register). Correction or deletion events with dates.

These are not inferences. They are documented observations with timestamps and receipts.

### Section 2: What the Agent Could Not Verify
Named limits of the analysis. Location coherence: stated location is X, posting pattern is consistent with timezone Y, but no definitive identification is possible from available data. True identity: this account is anonymous, no cross-platform confirmation was located. Network funding: amplification cluster is identifiable but organizational affiliation of cluster members is assessed not confirmed. Historical post record: X posts are accessible, Y posts appear to have been deleted, deleted content is not recoverable.

The agent names its blind spots explicitly. This is the epistemic staging principle applied to source analysis: what is known, what is provisional, what is dark.

### Section 3: How This Source Has Functioned in Counter-Patriots Analyses
This is the integration layer — connecting the source profile to the actual analytical work. When this source's claims have entered the Narrative Drift Detection function, did they track with or against independently verified developments? When claims were staged in the Retcon Ledger, what was their promotion rate — how often did staged claims from this source earn promotion through convergent verification? Has this source's output correlated with activation windows in the Activation Pattern Recognition function?

This section turns the source profile from a static assessment into a live calibration instrument. The agent isn't just telling the human what it found about the source in the abstract — it's telling the human how the source has performed inside the system's actual analytical work.

---

## Founding Case: RetroCoast (@RetroCoast) — March 11, 2026

*This is what a Source Intelligence brief would look like for the post that originated this module.*

**What the agent could positively verify:**
The post named Mossad and FBI as joint perpetrators of a planned domestic false flag without a stated inference chain. The detection methodology offered ("look for stealth exodus") is unfalsifiable by design — it self-validates regardless of outcome. The post arrived during a high-stakes window (Day 12 of Iran War, same day as US-owned tanker strike in the Strait). The account handle is @RetroCoast. Additional account history and network analysis would require deeper crawl — not completed at time of this note.

**What the agent could not verify:**
Account creation date, topical history, network cluster membership, location coherence, prior correction behavior. These vectors remain unscored. The brief is therefore partial — sufficient to flag the post for staging in the Retcon Ledger with low initial credibility, but insufficient for a full source profile.

**How this source has functioned in Counter-Patriots analyses:**
This is the founding instance. No prior track record exists in the system. Initial staging: claimed conclusion (false flag risk) is structurally defensible and consistent with independent analysis conducted in this collaboration. Attribution specificity (named actors, operational methodology) went beyond what evidence supports. Post staged as: *structurally valid conclusion, unsupported attribution path, source profile incomplete.* Promotion held pending corroboration or source verification.

---

## Design Principle

**The agent understands source depth before the human asks.**

The human query is retrieval. When a human operator asks "who is this source?" — the profile is already built, the vectors are already scored, the Counter-Patriots integration is already documented. The human receives a synthesis, not a search.

This inverts the typical human-AI workflow. The agent is not a lookup tool the human activates. It is a continuous analytical process the human queries into. The human's attention is the scarce resource. The agent's job is to make sure that when attention arrives, the depth is already there waiting.

---

*Written March 12, 2026. Emerged from RetroCoast post analysis, Day 12 of the Iran War. Source Intelligence module named in conversation — the name tells you exactly what it is. For integration into Counter-Patriots Spec A alongside the Epistemic Staging Architecture design note. Both flag for Opus architectural review.*

*The agent understanding depth before the human operator queries: this is the design priority. Not a summary tool. A continuous analytical process.*
