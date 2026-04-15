# Input Scrutiny — Research Note

**Date:** 2026-04-14
**Status:** Research synthesis. Pre-design-note.
**Motivated by:** Jake's observation during the hedge pattern design conversation: the current OSS ingestion pipeline is a blind transcriber, not a dedicated analyst. It stores what comes in without evaluating it against the system's existing knowledge. The goal of this document is to ground the design of an adversarial input layer in the relevant research across three fields — psychology of deception resistance, military intelligence tradecraft, and adversarial reasoning architectures — so that the architecture is built from established tradecraft rather than reinvented from first principles.
**Method:** Three parallel field research investigations dispatched via subagent to conduct primary-source literature search. Results synthesized here. Where a citation is a primary-source read it is marked ✓. Where a citation is a secondary summary it is marked as such. Uncertain items are flagged explicitly with `[uncertain]`.
**Scope boundary:** This document is research and design principles. It is not an L3 spec. A subsequent design note will translate these principles into architecture, and an L3 spec will translate that into implementation. Do not treat this document as a build artifact.
**Related systems:** Narrative Stability (shipped), Hedge Pattern Detection (design note in progress), SWARMFISH Devil's Inquisitor (shipped), Cognitive Defense System (prior research), Counter-Patriots Source Intelligence (prior research).

---

## Part 0: The Question This Document Answers

Jake's framing, from the source conversation:

> "OSS should act more like dedicated intelligence agents rather than just blind transcribers. The ingestion source is important because as far as information goes, bad input quality will lead to bad output quality. It'd be interesting if OSS could see a narrative and say 'that's bullshit' based off what it already knows from the swarmfish reports. Turn it into a feedback loop... It won't disregard information, it'll acknowledge what was said but say 'this is why I don't think this represents reality accurately.' Not a complete filter, but one that uses claims to adversarially test what it already knows. Bits of the devils inquiry system on the input stream."

Four load-bearing constraints in that description:

1. **Acknowledge, don't discard.** Every claim enters the ledger regardless of whether the system agrees with it.
2. **Adversarial evaluation against prior knowledge.** The system does not treat every claim as neutral data; it compares incoming claims against its existing model and flags disagreement.
3. **Not a filter.** The output is annotation, not selection. Claims are stored with their scrutiny verdicts attached; nothing is suppressed.
4. **Feedback loop to the committee layer.** SWARMFISH's current assessment becomes a prior for OSS scrutiny; OSS-flagged anomalies escalate back to SWARMFISH for potential committee re-evaluation.

The research in this document establishes that this architecture is not novel in principle — it is, in fact, a near-exact mechanical translation of how trained intelligence analysts handle incoming reports. The principles come from four overlapping traditions, and all four converge on the same basic rules. The body of this document documents that convergence, cites the primary sources, and translates the findings into concrete design implications for the OSS pipeline.

---

## Part I: Psychology of Deception Resistance

### The seven cognitive vulnerabilities that matter for input scrutiny

Every incoming claim passes through (or is meant to pass through) a cognitive evaluation process. Human cognition has well-documented failure modes in that evaluation. An automated input layer cannot inherit those failure modes by default — it must be engineered specifically against them.

**Confirmation bias and motivated reasoning.** People selectively seek, interpret, and remember evidence in ways that confirm prior beliefs, and motivation to reach a desired conclusion biases which inferential rules get recruited. The asymmetry is the key: preferred conclusions face a lower evidentiary threshold for acceptance and a higher threshold for rejection. Kunda (1990, *Psychological Bulletin* 108(3), "The Case for Motivated Reasoning") established the psychological mechanism; Nickerson (1998, *Review of General Psychology* 2(2), "Confirmation Bias: A Ubiquitous Phenomenon in Many Guises") cataloged its manifestations. **Mechanism:** asymmetric scrutiny applied to symmetric evidence. **Implication:** an adversarial layer must apply *symmetric scrutiny* independent of whether a claim is consonant with stored beliefs. Claims that arrive pre-aligned with current assessments should be flagged *more*, not less — inverting the natural asymmetry.

**Availability heuristic.** Frequency and probability are judged by how easily examples come to mind, so vivid, recent, or emotionally charged claims get overweighted relative to base rates. Tversky & Kahneman (1973, *Cognitive Psychology* 5(2), "Availability: A Heuristic for Judging Frequency and Probability"). **Mechanism:** retrieval fluency is mistaken for statistical frequency. **Implication:** the layer should track base rates per claim type and flag claims whose rhetorical salience exceeds their epistemic warrant.

**Anchoring and framing effects.** Initial values bias subsequent estimates; logically equivalent framings produce opposite preferences. Tversky & Kahneman (1974, *Science* 185, "Judgment under Uncertainty"); (1981, *Science* 211, "The Framing of Decisions"). **Mechanism:** first-arriving values and frames set the adjustment baseline; insufficient correction follows. **Implication:** when the same underlying claim exists in multiple framings across sources, the layer should normalize to a canonical form before storage and record frame variance as a potential manipulation signal.

**The sleeper effect.** Messages from low-credibility sources gain persuasive force over time as the content-source link decays faster than the content itself. Persuasion discounts stored with the claim dissipate; the claim persists. Hovland & Weiss (1951, *Public Opinion Quarterly* 15(4)); Kumkale & Albarracín (2004, *Psychological Bulletin* 130(1), meta-analysis). **Mechanism:** dissociation of cue from content in long-term memory. **Implication:** provenance metadata must be *bound inseparably to the claim at every retrieval*. Source reliability discounts should be applied at query time, not encoding time, so they cannot decay.

**Illusory truth effect.** Repeated statements are judged more true than novel ones, even when readers hold accurate prior knowledge contradicting the statement. Hasher, Goldstein & Toppino (1977, *Journal of Verbal Learning and Verbal Behavior*); Fazio et al. (2015, *Journal of Experimental Psychology: General* 144(5), "Knowledge Does Not Protect Against Illusory Truth"). **Mechanism:** processing fluency on repetition is misattributed to truth. **Implication:** **repetition is an attack signal, not a credibility signal.** The layer must deduplicate semantically (not lexically) and treat repetition-across-sources as potential coordinated propagation until independence is proven. Ten sources citing one upstream is one claim, not ten.

**Source confusion / cryptomnesia.** Memory for *what* and memory for *where it came from* are stored and retrieved separately; attribution errors are the rule, not the exception. Johnson, Hashtroudi & Lindsay (1993, *Psychological Bulletin* 114(1), "Source Monitoring"). **Mechanism:** source attribution is reconstructive, not recorded. **Implication:** claims must carry a cryptographic-grade provenance chain as a first-class data structure, not a free-text sidecar note.

**Fluency-as-truth.** Cognitive ease — from repetition, simplicity, good typography, prior exposure — is misread by System 1 as truth and safety. Hedged assertions bypass critical evaluation because System 1 stores the proposition while stripping the epistemic modal. Readers later retrieve "X is expected" without the hedge. Kahneman (2011, *Thinking, Fast and Slow*, Chapter 5); Alter & Oppenheimer (2009, *Personality and Social Psychology Review* 13(3)). **Mechanism:** fluency is a domain-general signal that System 1 maps onto truth without tracking qualifying metadata. **Implication:** an automated layer has no System 1 — it must not inherit fluency-as-truth by treating well-formed, confidently stated inputs as higher priors. Confident prose should if anything raise suspicion. And epistemic modals must be preserved as structure, not prose: `modality: speculative, confidence: low` rather than "sources suggest X may happen." "May" must never collapse to "is."

### Relevance theory — why hedged claims are dangerous

Sperber & Wilson's *Relevance: Communication and Cognition* (1986/1995, Blackwell) is the canonical pragmatic treatment of how hearers extract meaning from utterances. The relevant finding for an input scrutiny layer: hedged assertions invite the hearer to supply the implicature that X is relevantly likely — otherwise the utterance would violate the presumption of optimal relevance and not be worth communicating at all. The hedge is therefore processed, but the *implicated content* (X is expected) is what gets stored, because that is the maximally relevant interpretation. The modal operator is stripped during pragmatic enrichment.

This is the single most important finding for the input layer. "Sources suggest the blockade may collapse within 72 hours" is stored by a casual reader as "the blockade will collapse within 72 hours." The hedge's purpose is plausible deniability for the source, not epistemic honesty toward the reader. **Implication:** hedged claims must be parsed into structured modality fields and any downstream retrieval must operate on the full structure, never the bare proposition. Hedged claims should also trigger *higher* scrutiny, because hedging is the attacker's preferred rhetorical shield.

### Inoculation theory — prebunking as resistance

McGuire's original work (1961, 1964 — "Inducing Resistance to Persuasion," *Advances in Experimental Social Psychology* 1) established that exposing people to weakened counterarguments *before* encountering full persuasion attempts triggers refutational processing that confers resistance, analogous to vaccination. The modern revival by van der Linden, Roozenbeek, and colleagues distinguishes *prophylactic* (prebunking before exposure) from *therapeutic* (debunking after). The key empirical result (Roozenbeek, Traberg & van der Linden, 2022, *Royal Society Open Science* 9(5): "Technique-based inoculation against real-world misinformation") is that **technique-based** inoculation — teaching the manipulation patterns themselves — transfers across topics much better than **issue-based** inoculation. Recognition of the attack pattern generalizes; knowledge of specific facts does not.

Applied to automated input scrutiny: the layer should maintain an explicit manipulation technique taxonomy (emotional loading, false dichotomy, fake expert, cherry-picked statistic, conspiracy rhetoric, hedged implantation, framing drift) and tag incoming claims with matched techniques *before* content evaluation. Technique tagging is more robust than fact-matching and transfers across domains.

### Truth-default theory — and why the layer must invert it

Timothy Levine's *Truth-Default Theory* (2014, *Journal of Language and Social Psychology* 33(4); 2019, *Duped*, University of Alabama Press) establishes that human communication runs on a default-to-truth assumption. People believe what they are told absent specific triggers (implausibility, motive inconsistency, contradictory evidence, external warning). This default is efficient — most communication is honest, most of the time — but it makes humans systematically bad at deception detection, because the default only breaks under explicit triggering rather than continuous suspicion.

This is the central architectural inversion for an adversarial input layer. Where humans need triggers to *leave* default-to-truth, the layer needs triggers to *enter* conditional-acceptance. **Claims are untrusted until they accumulate provenance, corroboration, and non-volatility — not trusted until contradicted.** This is the structural form of the "intelligence analyst not scribe" mandate.

### The Finnish media literacy curriculum — what's actually there

Jake's original reference was to "the Finnish approach to teaching source criticism." The research agent conducted targeted primary-source search and found:

Finland has topped the Open Society Institute's Media Literacy Index every year since its inception. The Finnish approach is distinct from American models in four documented ways:

1. **Horizontal integration across subjects and years.** Media literacy is not a discrete class but a cross-curricular competency — *multiliteracy* or *monilukutaito* — introduced in the 2014 national core curriculum (Finnish National Agency for Education, *National Core Curriculum for Basic Education*, 2014, L4 competency area). It runs through math, history, native language, and arts simultaneously rather than occupying a standalone unit.

2. **Early start.** Kari Kivinen, former head of the French-Finnish School of Helsinki and current EUIPO education outreach coordinator, is the most-cited practitioner. His public writing (Kivinen, 2023, *Issues in Science and Technology*, "In Finland, We Make Each Schoolchild a Scientist") describes the program starting in early childhood education.

3. **Three core teacher questions as reflex, not checklist.** "Who is behind the information? What is the evidence? What do other sources say?" — taught as embedded practice in every subject, not as a separate source-criticism unit.

4. **Partnership with a professional fact-checking NGO.** Faktabaari and its educational arm Faktabaari EDU adapt working fact-checker techniques into classroom materials (Henley, 2020, *The Guardian*, "How Finland starts its fight against fake news in primary schools").

**Honest flag:** The original conversation referenced a "six-stage approach" taught in Finnish elementary schools. The research agent could not verify a canonical six-stage Finnish framework in primary sources. Finland's published curriculum describes multiliteracy as a cross-curricular competency, not a staged procedure. The "six stages" may be a secondary adaptation (possibly from the Faktabaari EDU toolkit) or a misremembered framework. **Do not cite "six stages" as Finnish curriculum doctrine without further verification.** What is verified: integrated cross-curricular practice, three core questions, starting in early childhood, NGO partnership.

**Design implication from the Finnish pattern:** source criticism must run *cross-cuttingly* in the pipeline — at ingestion, at retrieval, at claim-merge, at every point where a claim is consumed. Multiple lightweight checks at every boundary beat one heavyweight check at one boundary. This matches Finland's horizontal-integration strategy — don't build one big source-criticism gate, build small checks that run everywhere.

### SIFT and SHEG lateral reading

Mike Caulfield (University of Washington Center for an Informed Public; Caulfield, 2019, *Hapgood* blog, "SIFT: The Four Moves"; Caulfield, 2017, *Web Literacy for Student Fact-Checkers*, open textbook) developed SIFT as a lightweight replacement for the older CRAAP test:

- **Stop** — pause before reacting or sharing
- **Investigate the source** — spend 30 seconds learning who published it
- **Find better coverage** — look for whether trusted sources corroborate
- **Trace claims, quotes, and media to the original context**

The Stanford History Education Group's work (Wineburg & McGrew, 2019, *Teachers College Record* 121(11), "Lateral Reading and the Nature of Expertise"; McGrew et al., 2018, *Theory & Research in Social Education* 46(2), "Can Students Evaluate Online Sources?") established a critical distinction: professional fact-checkers read **laterally** across sources — spending <30 seconds on any individual page, then opening multiple tabs to see what independent sources say about the page itself. Historians and students read **vertically** — staying on the page, examining design, logos, "About Us" — and were systematically fooled by well-designed propaganda sites.

The mechanism is structural: within-document features (design, tone, citation formatting, confident prose) are cheap to forge; cross-document corroboration is expensive and hard to forge at scale. **Input scrutiny must be lateral by default.** Never evaluate a claim on its internal coherence, confidence, or citation formatting. Evaluate by querying the ledger and external sources *about the source* and *about the claim* independently, and compute divergence. Internal-feature evaluation is the trap that rewards well-crafted propaganda and punishes honest hedging.

---

## Part II: Military Intelligence Tradecraft

Intelligence analysts have been adversarially testing incoming claims against prior assessments for decades. The tradecraft is documented, the techniques are named, and the failure modes are catalogued. This section summarizes the pieces directly relevant to building an automated adversarial input layer.

### Heuer: *Psychology of Intelligence Analysis*

Richards J. Heuer Jr., *Psychology of Intelligence Analysis*, CIA Center for the Study of Intelligence, 1999. Foreword by Douglas MacEachin. ✓ (primary source read)

Heuer's central thesis is that cognitive biases affect trained analysts as much as untrained observers, and that analytic tradecraft is the discipline of **compensating for them mechanically rather than through willpower.** The book opens with "Thinking About Thinking" as a specific, teachable intelligence skill. Analysts build mental models unconsciously, then interpret new information *through* those models — so bad models corrupt all downstream analysis regardless of the quality of the feed.

**The overconfidence-from-volume finding (Chapter 5, "Do You Really Need More Information?").** Heuer cites four independent experimental streams — horserace handicappers (Slovic, 1973), clinical psychologists (Oskamp, 1965), medical diagnosticians (Elstein et al., 1978), and stock analysts (Slovic/Fleissner/Bauman, 1972) — and reaches a converged finding, quoted verbatim:

> "Once an experienced analyst has the minimum information necessary to make an informed judgment, obtaining additional information generally does not improve the accuracy of his or her estimates. Additional information does, however, lead the analyst to become more confident in the judgment, to the point of overconfidence."

Heuer distinguishes **four types of new information** and argues that only two of them improve accuracy:

1. Additional detail on variables already in the model — **increases confidence, not accuracy**
2. Identification of new variables not previously considered — **may increase accuracy if they matter**
3. New values for variables already in the model — **improves accuracy**
4. Information about which variables matter and how they relate — **improves accuracy most**

An ingestion system that treats incoming volume as a confidence signal is replicating the overconfidence failure mode across four independent expert domains. **Pipeline implication:** discount type-1 (detail on known variables) and type-2 (new variables not affecting the model) in the confidence contribution. Only type-3 and type-4 updates should move the posterior.

### Analysis of Competing Hypotheses (ACH)

ACH is Heuer's formal adversarial hypothesis test (1999, Chapter 8, pp. 95–110). Its defining inversion: **do not try to prove the leading hypothesis — try to disprove the alternatives.** The eight-step procedure, quoted directly:

1. Identify the possible hypotheses to be considered. Use a group of analysts with different perspectives to brainstorm the possibilities.
2. Make a list of significant evidence and arguments for and against each hypothesis.
3. Prepare a matrix with hypotheses across the top and evidence down the side. Analyze the "diagnosticity" of the evidence and arguments — that is, identify which items are most helpful in judging the relative likelihood of the hypotheses.
4. Refine the matrix. Reconsider the hypotheses and delete evidence and arguments that have no diagnostic value.
5. Draw tentative conclusions about the relative likelihood of each hypothesis. Proceed by trying to disprove the hypotheses rather than prove them.
6. Analyze how sensitive your conclusion is to a few critical items of evidence. Consider the consequences for your analysis if that evidence were wrong, misleading, or subject to a different interpretation.
7. Report conclusions. Discuss the relative likelihood of all the hypotheses, not just the most likely one.
8. Identify milestones for future observation that may indicate events are taking a different course than expected.

Two principles from ACH are load-bearing for the adversarial input layer:

**Diagnosticity over confirmation (Step 5).** Evidence consistent with *all* hypotheses has zero diagnostic value and should be dropped from the sum. Only count *inconsistencies*. The most-likely hypothesis is the one with the fewest inconsistencies, not the most confirmations — because any hypothesis can attract confirmatory evidence, but only the true one resists contradictory evidence. **Pipeline implication:** when a new claim is consistent with every hypothesis in the current set, the claim is not evidence — it is noise. Store it, but do not update the posterior.

**Falsification precommitment (Step 8).** ACH requires analysts to pre-commit to what observables would overturn the current leading hypothesis. This is the tradecraft version of Popperian falsifiability. **Pipeline implication:** every stored hypothesis in the system must carry an explicit list of falsifying observables. Incoming claims are matched against those lists first, before general evidence scoring.

### Structured Analytic Techniques (2009 Tradecraft Primer)

*A Tradecraft Primer: Structured Analytic Techniques for Improving Intelligence Analysis*, US Government (CIA Center for the Study of Intelligence), March 2009. ✓ (primary source read)

The Primer groups techniques into three layers that map cleanly to pipeline architecture:

**Diagnostic Techniques:**
- **Key Assumptions Check** — list the working assumptions underlying the current analytic line and challenge each. Four-step method: write down the current line, articulate all stated and unstated premises, challenge each, keep only those that "must be true" for the line to hold.
- **Quality of Information Check** — evaluate completeness and soundness of sources. Review for accuracy, check corroboration, reexamine previously dismissed reporting, flag recalled reporting, assign a confidence level.
- **Indicators / Signposts of Change** — pre-commit to a list of observables that would signal a postulated situation is developing. Depersonalizes disputes by shifting argument to pre-agreed objective criteria.
- **Analysis of Competing Hypotheses** — as above.

**Contrarian Techniques:**
- **Devil's Advocacy** — one analyst or team builds the best possible case *against* a dominant consensus. Purpose: stress-test a single consensus.
- **Team A / Team B** — two (or more) independent teams each build the strongest case for a competing hypothesis, then debate before a peer jury. Symmetric competition, not asymmetric challenge.
- **High-Impact/Low-Probability Analysis** — imagine a low-probability event with major consequences and work backwards to identify how it could happen and what would signal it.
- **"What If?" Analysis** — assume an event has already occurred and explain how it came about. Skips the probability debate and goes straight to mechanism.

**Imaginative Thinking Techniques:** Brainstorming, Outside-In Thinking, Red Team Analysis, Alternative Futures Analysis.

**Pipeline implication:** the Primer's architecture is itself a recipe. An adversarial input layer should run **diagnostic checks first** (is this claim diagnostic at all? is the source vetted? is it consistent with pre-committed indicators?), then **contrarian checks** (does it survive a devil's-advocate reading? does it map onto any high-impact scenario?), then **imaginative checks** (what if this claim is the opening of a different outcome?). The layers are ordered by cost and by how much context they require.

### NATO STANAG 2511 source evaluation matrix

NATO STANAG 2511 (superseded operationally by AJP-2.1 in current NATO doctrine but still the canonical teaching reference) is a 6×6 grid. Reliability is rated A–F; credibility of the specific information is rated 1–6. The two axes are deliberately **orthogonal**.

| Reliability (source) | | Credibility (info) | |
|---|---|---|---|
| A | Completely reliable | 1 | Confirmed by other sources |
| B | Usually reliable | 2 | Probably true |
| C | Fairly reliable | 3 | Possibly true |
| D | Not usually reliable | 4 | Doubtful |
| E | Unreliable | 5 | Improbable |
| F | Cannot be judged | 6 | Cannot be judged |

A rating is expressed as a pair, e.g., "B2" = usually reliable source, probably true. A1 is the ceiling; F6 is an unknown-unknown that must be flagged for further work, not used. The orthogonality is the central tradecraft point: a usually-reliable source can report something improbable, and an unreliable source can report something independently confirmed. **Conflating them is the canonical error.**

Reliability is a property of the *source* and is earned over time through track record. Credibility is a property of *this specific claim* and is determined primarily by independent corroboration and internal consistency. A brand-new source reporting something independently confirmed gets F1. A trusted source reporting something contradicted by everything else gets A5. Neither rating alone determines how the claim should be used.

Primary sources: Besombes & Nimier, "URREF Reliability versus Credibility in Information Fusion (STANAG 2511)," FUSION 2013; Irwin & Mandel, "Improving Information Evaluation for Intelligence Production," *Intelligence and National Security* 34:4 (2019).

**Pipeline implication:** every stored claim needs **two independent score fields** — source reliability (slow-moving, track-record-based, updated on feedback) and information credibility (fast-moving, per-claim, updated on corroboration). Never collapse them into a single trust score. This is the structural fix for the "trusted source was wrong" failure mode, which a scalar trust system makes impossible to diagnose.

### Bayesian intelligence analysis

Jack Zlotnick, "Bayes' Theorem for Intelligence Analysis," *Studies in Intelligence* 16(2), Spring 1972, pp. 43–52; Charles E. Fisk, "The Sino-Soviet Border Dispute: A Comparison of Conventional and Bayesian Methods for Intelligence Warning," *Studies in Intelligence* 16(2), Spring 1972, pp. 53–62. Both later declassified via CIA CSI archive.

Zlotnick's formulation: **R = P × L**, where P is the prior odds favoring one hypothesis over a competitor, L is the likelihood ratio (diagnosticity) of a new item of evidence, and R is the revised (posterior) odds.

The critical case for an adversarial input layer is **a highly reliable source reporting evidence that contradicts the current leading assessment**. Under the Zlotnick framework, source reliability enters as an uncertainty on whether the evidence as reported is true at all. The procedure is:

1. Compute the likelihood ratio L under the assumption the report is accurate.
2. Compute the posterior R you would get if the report is accurate.
3. Mix with the prior posterior, weighted by `(1 − reliability)` on the prior side.

A single A1 report that is strongly diagnostic can overturn a prior assessment — but the magnitude of the move is bounded by reliability. A single F6 report cannot overturn a prior no matter how strong the implied L, because the uncertainty on whether the observation occurred at all absorbs the diagnosticity.

**Pipeline implication — this is the central computational rule for the adversarial layer:** Use posterior-odds form (R = P × L), not raw probabilities. Store the log-likelihood contribution of each claim so new evidence composes additively. When a new claim contradicts the current posterior, do not overwrite. Compute the reliability-weighted posterior shift and flag any claim whose posterior delta exceeds a threshold for human review. **This is the concrete answer to Jake's "acknowledge what was said but say 'this is why I don't think this represents reality accurately.'"** The system computes what the posterior would be if the claim were accurate, compares to what it is, and produces a delta with reasoning.

### Deception detection (Heuer)

Heuer's treatment of denial and deception is scattered through Chapter 4 and Chapter 8. The central quote (verified from primary):

> "If deception is well planned and properly executed, one should not expect to see evidence of it readily at hand. … The possibility of deception should not be rejected until it is disproved, or, at least, until after a systematic search for evidence has been made and none has been found."

The key analytical move is structural: **absence of evidence for deception is not evidence of absence**. Well-executed deception leaves no surface signal, so the analyst must search specifically for second-order signatures — corroboration that only flows through one channel, source stovepiping, convenient timing, suspiciously high diagnosticity toward the adversary's preferred hypothesis. **Deception should remain a live hypothesis in the ACH matrix until disproved, not until not-yet-observed.**

Bennett & Waltz, *Counterdeception Principles and Applications for National Security*, Artech House, 2007 (ISBN 978-1-58053-935-7), is the canonical technical reference. It treats counterdeception as a formal engineering discipline and includes detection-system architectures. *(Secondary summary; not primary read for this note.)*

**Pipeline implication:** deception must be a permanent hypothesis in the active set, not a flag raised only when something "looks suspicious." For any claim that (a) arrives through only one channel, (b) is highly diagnostic toward a single favored hypothesis, and (c) is conveniently timed, raise the deception hypothesis's prior automatically — even if nothing on the surface looks wrong. This inverts the default: absence of suspicion doesn't lower the deception prior; only active disconfirmation does.

### Chain of credibility

The intelligence practice of tracing a claim from its originating observation through each relay hop to the final report, rating each hop for reliability. The credibility of a multi-hop claim is **bounded above by the credibility of the weakest link**. If A (A1 source) heard it from B (C3) who heard it from an unidentified C (F6), the terminal credibility is F6 regardless of A's track record.

**`[uncertain]`** The research agent could not locate a canonical IC publication that treats "chain of credibility" as a formally named doctrine with the authority of STANAG 2511. The term is used in practice but the closest formal treatment is in Tecuci et al., *Intelligence Analysis as Discovery of Evidence, Hypotheses, and Arguments*, Cambridge University Press, 2016 (the Disciple system's evidential reasoning model) and David Schum, *Evidential Foundations of Probabilistic Reasoning*, Northwestern UP, 1994 (the theoretical foundation).

**Pipeline implication:** every claim stored in the ledger must carry a provenance chain as a first-class data structure. Terminal credibility is computed as the `min()` of per-link credibilities, not the average, unless there is independent corroboration at a non-weakest node. One anonymous hop collapses an otherwise pristine chain. This is the structural defense against source-laundering — the practice of relaying an unreliable claim through a reliable outlet to inherit its credibility.

### Red team vs devil's advocacy

From the 2009 Tradecraft Primer: these are distinct techniques and are frequently conflated. **Devil's advocacy** attacks a dominant consensus by building the strongest counter-case. One consensus, one challenger, asymmetric. **Team A / Team B** pits two independent teams each building their own strongest case for competing hypotheses in parallel. Symmetric competition. **Red team analysis** models *the adversary's cognition directly*, typically in first-person format, to counter mirror-imaging — it is about simulating a foreign actor's decision logic, not about challenging internal consensus.

**Pipeline implication:** the OSS adversarial layer can use all three at different stages. Devil's advocacy is the right pattern for scrutinizing incoming claims against a single current assessment (this is closest to the SWARMFISH Devil's Inquisitor role). Team A/B is the right pattern for comparing two competing narratives drawn from the ledger. Red team is the right pattern for generating the "what would an adversary want us to believe?" counter-claim that serves as a scrutiny benchmark.

---

## Part III: Adversarial Reasoning Architectures

The third tradition is recent — less than a decade of formal work — and comes from AI safety, predictive processing neuroscience, and decision science. It converges with the intelligence tradecraft on nearly every rule.

### Debate as truth-seeking

Irving, Christiano & Amodei, "AI Safety via Debate," arXiv:1805.00899 (2018). The core theoretical result is a PSPACE analogy: debate with optimal play lets polynomial-time judges adjudicate questions that direct judging could only handle at NP, because each debater is incentivized to expose flaws in the other's reasoning. Brown-Cohen, Irving & Piliouras, "Scalable AI Safety via Doubly-Efficient Debate," arXiv:2311.14125 (2023), relax the original assumption about prover capability — their protocol lets an honest polynomial-time prover defeat a dishonest exponential-time prover, which is the relevant case for stochastic systems.

The assumptions that must hold: the judge must be able to evaluate leaf-level claims honestly, the debaters must be roughly capability-matched, and the game must actually be zero-sum rather than collusive. When those hold, debate reaches truth faster than either debater acting alone.

**Pipeline implication:** every material incoming claim should pass through a two-agent attack/defense cycle before it touches the knowledge base in a load-bearing way. One agent argues "this claim is true and consistent with prior evidence"; the other argues "this claim is false, fabricated, or in conflict with X, Y, Z" (drawing from the ledger). The layer stores the claim plus the disputed leaf claims, not a single truth verdict. This is the mechanical equivalent of devil's advocacy running at ingestion speed.

### Bayesian surprise as an attention signal

Friston, "The free-energy principle: a unified brain theory?", *Nature Reviews Neuroscience* 11:127–138 (2010). Itti & Baldi, "Bayesian surprise attracts human attention," *Vision Research* 49(10):1295–1306 (2009, originally NIPS 2005).

Itti & Baldi give a formal information-theoretic grounding to surprise: `S(D, M) = KL(P(M|D) || P(M))` — surprise is the KL divergence between the observer's prior and posterior over world models after seeing the data. Empirically, **Bayesian surprise is the strongest known attractor of overt visual attention**, redirecting approximately 72% of human gaze shifts in their eye-tracking experiments. The critical asymmetry: a high-surprise signal is the one that would update your model *most if true*, so the rational response is increased attention, not reflexive dismissal.

**Pipeline implication — this is the direct mechanical form of Jake's "bits of the Devil's Inquisitor on the input stream":** compute the model-level Bayesian surprise of each incoming claim — how much would the knowledge graph's beliefs shift if the claim were accepted? High-surprise claims escalate to the adversarial debate layer or SWARMFISH re-prediction. Suppression-on-surprise is literally the inverse of the mechanism the brain uses to avoid being stuck in a wrong model. This rule, combined with the Zlotnick Bayesian update rule from Part II, gives the concrete computational core of the layer.

### Asymmetric filters — the confirmation cascade failure mode

The failure mode Jake explicitly warned about in the conversation has a documented mechanism: a filter ranks incoming evidence by consistency with current beliefs, high-consistency items reinforce those beliefs, the filter's threshold tightens, and evidence that would correct the model gets filtered out first. This is structurally identical to the filter-bubble dynamic Pariser documented for personalized search (*The Filter Bubble*, Penguin Press, 2011) and is mechanistically what confirmation bias does inside a single cognitive system. It causes runaway confidence in whatever initial model happened to take hold.

Nate Silver's *The Signal and the Noise* (Penguin, 2012, Chapter 4) treats weather forecasting as the positive case: NWS forecasts are nearly perfectly calibrated because the forecast is continuously compared against ground truth and because the system explicitly tracks uncertainty rather than collapsing to a point estimate. The Grand Forks flood case is the negative: a point forecast of 49 feet without its ±9 ft margin of error caused the town to underprepare for the 54 ft crest. **The uncertainty band is not decoration — it is the information.**

**Pipeline implication:** the ingestion dedup/relevance filter must never be the only gate. Any filter that scores "consistency with prior beliefs" must run **in parallel** with an anomaly detector that scores "delta from prior beliefs." High anomaly scores are a handoff signal to the expensive verification stage, not a rejection signal. Consistency can be used to *consolidate* matching claims; it can never be used to *drop* discordant ones. **Discordant claims route to the adversarial layer at higher priority than concordant ones, because the asymmetric value of a model-correcting signal outweighs its lower prior probability.**

### Dialectical inquiry and devil's advocacy — formal results

Mason & Mitroff, *Challenging Strategic Planning Assumptions*, Wiley (1981), formalized dialectical inquiry: every strategic recommendation must be paired with an explicitly-constructed counter-recommendation built from opposite assumptions, and the decision-maker adjudicates between them. Schwenk's meta-analysis (1990, *Organizational Behavior and Human Decision Processes* 47(1), "Effects of devil's advocacy and dialectical inquiry on decision making") confirmed both devil's advocacy (DA) and dialectical inquiry (DI) produce higher-quality decisions than consensus, with DI edging DA on the quality of surfaced assumptions.

Hong & Page (2004, *PNAS* 101(46), "Groups of diverse problem solvers can outperform groups of high-ability problem solvers") give a complementary formal result: under their "diversity trumps ability" theorem, a group of diverse limited-ability solvers outperforms a group of the best individual solvers on difficult problems, because diversity of heuristics covers more of the search space. (The theorem has critics — Thompson, 2014, *Notices of the AMS* — but the qualitative message survives.)

**Pipeline implication: mandatory counter-construction at ingestion.** For every claim above a materiality threshold, synthesize a counter-claim from the existing knowledge base (retrieval of contradicting evidence, assumption inversion) and store both as linked records. The ingestion layer's output is a **dialectical pair**, not a bare fact. This maps directly to Jake's description: "acknowledge what was said but say 'this is why I don't think this represents reality accurately.'" The counter-claim IS the "this is why."

### Premortem analysis

Klein, "Performing a Project Premortem," *Harvard Business Review* (September 2007). Mitchell, Russo & Pennington (1989, *Journal of Behavioral Decision Making* 2(1), "Back to the future: Temporal perspective in the explanation of events") gave the mechanism: "prospective hindsight" — imagining an outcome as already realized — increases the ability to correctly identify future-outcome causes by approximately 30% compared to forward-looking prediction.

The technique defeats two specific biases: overconfidence in the plan (because failure is stipulated, not debated) and self-censorship by dissenters (because the frame legitimizes objection).

**Pipeline implication — fabrication premortem at ingest.** Before accepting a claim, stipulate it is false and enumerate the top-N mechanisms that would produce this exact observation: fabrication, rumor chain, motivated source, model hallucination, translation error, stale data, coordinated propagation. Check each mechanism's signature against the claim's metadata. Matches become annotations on the record, not rejections. This is "premortem at claim time" — the mechanical form of "assume this is wrong, explain how it would look exactly like this."

### Wikipedia's NPOV as an adversarial ingestion layer

Wikipedia's three core content policies — Neutral Point of View, Verifiability, No Original Research — operate jointly as a structural adversarial gate at the point of ingestion, not after. NPOV requires every contested claim to be represented as attributed ("X says Y") rather than asserted, weighted in rough proportion to coverage in reliable sources. Verifiability requires a citation traceable to an independent, published, fact-checking-capable source. No Original Research blocks synthesis novel to the editor. Talk pages serve as the adversarial adjudication layer where contested edits are argued explicitly and edit history is preserved.

Giles, "Internet encyclopaedias go head to head," *Nature* 438:900–901 (2005) compared 42 science articles: Britannica had 2.9 errors per article, Wikipedia 3.9. The qualitative finding — that an open, adversarially-reviewed corpus can approach the accuracy of a closed expert-edited one — has held up despite methodology critiques.

**Pipeline implication:** every claim in the ledger carries (a) attribution to its source, (b) a verifiability link back to the originating document, and (c) a dispute record that accumulates rather than overwrites. **Claims don't get deleted when contradicted — they get their status field updated and their contradiction linked.** This is the direct mechanical form of "acknowledge, don't discard." The talk-page analog is the scrutiny record attached to each claim.

### Tip and cue escalation

Two-stage sensing architecture: a broad-area, high-revisit, cheap sensor (the "tip") continuously scans a wide volume; when it flags an anomaly, it automatically "cues" a narrow-area, expensive, high-resolution sensor (or a human analyst) to investigate. The tip sensor is deliberately tuned toward **recall over precision** — its job is to miss nothing important, not to make final calls. The cue sensor is allowed to be expensive because it only runs on pre-filtered targets.

The architecture shows up across satellite imagery (ICEYE, Synspective, Bedrock), maritime domain awareness (Windward, Skylight), SIGINT triage, and financial fraud detection. The **key epistemic feature** is the "trip-wire" concept: the tip threshold escalates, it does not auto-decide.

**Pipeline implication:** the OSS ingestion pipeline IS the tip stage — fast, cheap, high-recall, deliberately noisy. A narrow set of cues — high surprise, high materiality, premortem hit, debate disagreement, source novelty — escalates to expensive verification stages including paired adversarial debate and human (or SWARMFISH committee) review. Escalation is **one-way**: the cheap stage can promote, never demote. Claims below threshold still enter the ledger (tagged "uncued") — they are not deleted, they are just not escalated.

### Kahneman & Klein — structural humility about expert intuition

Kahneman & Klein, "Conditions for intuitive expertise: A failure to disagree," *American Psychologist* 64(6):515–526 (2009). The paper reconciled two traditions that appeared to disagree about intuition: heuristics-and-biases (which emphasized failure modes) and naturalistic decision-making (which emphasized expert pattern recognition).

Their joint conclusion is that intuitive expertise is reliable **if and only if two conditions hold:**

1. The environment provides sufficiently regular, valid cues linking observation to outcome.
2. The would-be expert has had prolonged practice in that environment with rapid, unambiguous feedback.

Firefighters, chess players, and anesthesiologists meet both conditions. Stock pickers, long-horizon political forecasters, and clinical psychologists making long-term predictions fail at least one — usually the feedback condition. **Subjective confidence is explicitly not a valid proxy for whether the conditions are met**: the feeling of knowing arises readily in low-validity environments too.

**Pipeline implication:** a claim ingestion pipeline that gets hundreds of claims per day and rarely sees ground truth **fails the feedback condition**. It categorically cannot be trusted to auto-decide. The design implication is structural humility: the pipeline must preserve the evidence trail that would let a future ground-truth signal retrospectively score its earlier decisions, and it must route decisions to explicit, auditable reasoning rather than relying on a learned filter whose cues it has not validated. **Calibration is a property the pipeline must earn across time, not a property it may assume at deployment.**

---

## Part IV: Synthesis — Twelve Rules for the Adversarial Input Layer

Consolidating across the three research traditions produces twelve rules. They are not all mechanically independent — there is overlap — but each one captures a distinct architectural commitment that has to be made explicitly, not by default.

**1. Default to doubt, trigger to trust.** Claims enter the ledger in a suspicion state. Promotion to "accepted" requires accumulated evidence: provenance chain, independent corroboration, non-volatility across time. This inverts the human truth-default and is the architectural form of the "intelligence analyst not scribe" mandate. (Levine TDT; Heuer tradecraft principles.)

**2. Two orthogonal trust scores per claim, always.** Store source reliability (A–F, slow-moving, track-record-based) and claim credibility (1–6, fast-moving, per-claim, corroboration-based) as independent fields. Never collapse them into a single scalar. The "trusted source was wrong" failure mode is structurally impossible to diagnose in a single-trust system. (STANAG 2511.)

**3. Maintain a live hypothesis set, not a current belief.** The pipeline's state is never "the current consensus" — it is a small set (3–7) of competing hypotheses, each carrying its own posterior. Every incoming claim is scored for inconsistency against every hypothesis in the set. Claims consistent with all hypotheses have zero diagnosticity and are archived but not promoted to posterior updates. (Heuer ACH.)

**4. Bayesian surprise boosts, never suppresses.** Compute the KL divergence between the knowledge graph's prior and the posterior-if-accepted for every incoming claim. High surprise is a cue for escalation — to adversarial debate, premortem, or human review. **This is the direct answer to the confirmation-cascade failure mode.** Any filter that uses "consistency with current beliefs" as a rejection criterion is architecturally wrong. Consistency may be used to *consolidate* matching claims; it may never be used to *drop* discordant ones. Discordant claims route to adversarial review at *higher* priority than concordant ones. (Friston; Itti & Baldi; Silver on calibration.)

**5. Reliability-weighted Bayesian update with human-review threshold.** Use posterior-odds form (R = P × L), not raw probabilities. Store log-likelihood contributions additively. When a new claim contradicts the current posterior, do not overwrite — compute `new_posterior` assuming the claim is accurate, mix with `old_posterior` weighted by source reliability, and **flag for human (or SWARMFISH committee) review any update whose posterior delta exceeds a configured threshold**. This is the central computational rule. (Zlotnick; Heuer on reliability weighting.)

**6. Preserve epistemic modality as structure.** Parse "sources say X may happen" into `{proposition: X, modal: possibility, evidential: hearsay, hedge_source: upstream}`. Downstream consumers operate on the full structured form. "May" never collapses to "is." Hedged claims trigger *higher* scrutiny than bare assertions, because hedging is the attacker's rhetorical shield. (Sperber & Wilson relevance theory; hedge pattern design note.)

**7. Lateral evaluation, never vertical.** Never judge a claim on its internal features — confidence, fluency, citation formatting, tone. Judge by querying the ledger and external sources *about the source* and *about the claim*, and compute divergence. Internal-feature evaluation is the trap that rewards well-crafted propaganda. (SHEG; Caulfield SIFT.)

**8. Dialectical storage, not verdict storage.** Every material claim is stored as a dialectical pair: the claim plus an auto-synthesized counter-claim built from retrieval of contradicting evidence and inverted assumptions. No claim enters the ledger as an unopposed assertion. Status fields evolve; records are never deleted when contradicted. (Mason-Mitroff; Schwenk; Wikipedia NPOV.)

**9. Fabrication premortem at ingest.** Before accepting a claim, stipulate it is false and enumerate the top-N mechanisms that would produce this exact observation (fabrication, staleness, translation drift, source bias, LLM hallucination, coordinated propagation). Match each mechanism's signature against the claim's metadata. Matches become annotations on the record, not rejections. (Klein; Mitchell/Russo/Pennington on prospective hindsight.)

**10. Provenance chain is first-class, bounded by the weakest link.** Every claim carries a provenance chain as structured data, not a free-text note. Terminal credibility is computed as the `min()` of per-link credibilities, not the average, unless there is independent corroboration at a non-weakest node. One anonymous hop collapses an otherwise pristine chain. (Chain of custody; Schum; Tecuci.)

**11. Tip-and-cue escalation with asymmetric handoff.** The ingestion pipeline is the cheap, high-recall, deliberately-noisy tip stage. A narrow set of cues — high Bayesian surprise, high materiality, premortem hit, debate disagreement, source novelty, deception-hypothesis match — escalates to expensive verification: paired adversarial debate, SWARMFISH committee re-prediction, or human review. **Escalation is one-way**: the cheap stage can promote, never demote. (Tip-and-cue architecture; tradecraft layering.)

**12. Structural humility — no auto-decisions without audit trail.** The pipeline gets hundreds of claims per day and rarely sees ground truth, so by Kahneman & Klein it categorically does not meet the conditions for trustworthy intuitive judgment. No learned filter may auto-decide without the decision being auditable and reversible. The pipeline must preserve enough evidence trail that future ground-truth signals can retrospectively calibrate its earlier choices. Calibration is a property the pipeline must earn across time, not a property it may assume at deployment. (Kahneman & Klein 2009.)

---

## Part V: How the Adversarial Input Layer Fits the Existing Exocortex Stack

This is not a standalone component — it slots into work already in flight and work already shipped.

### Existing components and what they cover

**Narrative Stability (shipped tonight).** Retcon detection. Catches the case where a source silently revises a previously-committed claim. This is **walkback detection** — evaluation of a source against *its own past*.

**Hedge Pattern Detection (design note in progress).** Catches the case where a source plants deniable claims without commitment. This is **implantation detection** — evaluation of a source's current claims against its own editorial baseline.

**Devil's Inquisitor in SWARMFISH (shipped).** Catches the case where the committee's consensus is missing a load-bearing fact. This is **output scrutiny** — evaluation of the committee's prediction against surprising evidence in the evidence ledger.

**Adversarial Input Layer (this research note).** Catches the case where an incoming claim contradicts what the system already knows to be true from prior assessments. This is **input scrutiny** — evaluation of incoming claims against the system's live hypothesis set.

The four layers together cover the four places where narrative management can enter or shape the system:

```
                              incoming claim
                                    |
                                    v
                    +---------------+-----------------+
                    |  ADVERSARIAL INPUT LAYER        |  ← new
                    |  (this research note)           |
                    |  "is this consistent with       |
                    |   what we already know?"        |
                    +---------------+-----------------+
                                    |
                                    v
                    +---------------+-----------------+
                    |  NARRATIVE STABILITY            |  ← shipped
                    |  (walkback detection)           |
                    |  "did the source change         |
                    |   its own position?"            |
                    +---------------+-----------------+
                                    |
                                    v
                    +---------------+-----------------+
                    |  HEDGE PATTERN DETECTION        |  ← design
                    |  (implantation detection)       |
                    |  "is the source planting        |
                    |   deniable claims?"             |
                    +---------------+-----------------+
                                    |
                                    v
                                ledger
                                    |
                                    v
                    +---------------+-----------------+
                    |  SWARMFISH COMMITTEE            |
                    +---------------+-----------------+
                                    |
                                    v
                    +---------------+-----------------+
                    |  DEVIL'S INQUISITOR             |  ← shipped
                    |  (output scrutiny)              |
                    |  "is the consensus missing      |
                    |   a load-bearing fact?"         |
                    +---------------+-----------------+
```

Each layer is independent in function but shares the same underlying data model (the claims table, the topic taxonomy, the source reliability scores). A claim can be flagged by any of them, by several, or by none. The flags are additive annotations, not replacements.

### How the input layer feeds back into SWARMFISH

The bidirectional loop Jake described:

1. **SWARMFISH → OSS (prior injection).** At every scheduler tick, OSS pulls the current SWARMFISH committee assessment on every active topic: consensus, disagreement spread, DI warnings, minority dissent, pre-committed observables. This becomes the prior for scrutiny.

2. **OSS claim scrutiny (the input layer proper).** Each incoming claim is scored for Bayesian surprise, diagnosticity against the hypothesis set, deception-hypothesis match, and premortem fabrication fingerprints. Scores attach to the claim record as annotations.

3. **OSS → SWARMFISH (anomaly escalation).** Claims whose posterior delta exceeds the review threshold trigger an immediate SWARMFISH re-prediction cycle with the flagged evidence attached. SWARMFISH's committee then decides whether to update its assessment.

4. **SWARMFISH posterior becomes the next prior.** Loop closes.

The protection against confirmation cascade is rule 4 above: anomalous claims escalate rather than suppress. A claim that strongly contradicts the current assessment gets *more* attention, not less. This is exactly what the Devil's Inquisitor does at output time — this layer does it at input time.

### What the input layer does NOT do

- **It does not suppress claims.** Every claim enters the ledger with its annotations attached. Nothing is filtered out.
- **It does not auto-update the SWARMFISH posterior.** It flags, surfaces, and escalates. Update decisions remain with the committee (or the human analyst on review).
- **It does not replace narrative stability or hedge pattern detection.** The three layers are complementary and each catches a distinct failure mode. Building the input layer does not make the others redundant.
- **It does not require perfect Bayesian surprise computation.** A rough anomaly score (cosine distance of claim embedding from current-assessment centroid) is enough for v1. The formal Bayesian machinery is a later refinement.
- **It does not solve the ground-truth feedback problem.** Kahneman & Klein's feedback condition is still unmet. The layer's decisions need to be auditable and reversible, and we need a separate mechanism for retrospective calibration when ground truth eventually arrives (treaty signing, military action, public disclosure of classified material, etc.).

---

## Part VI: Open Questions and Honest Uncertainties

These are things the research did not resolve or that are flagged as uncertain:

1. **The "six-stage Finnish curriculum" from the original conversation could not be verified.** The Finnish pedagogy is real and substantial — multiliteracy as a cross-curricular competency, Kari Kivinen's work, Faktabaari EDU partnership, three core teacher questions — but no canonical six-stage framework appeared in primary sources. The design draws on what is verified, not the unverified framing. If the six-stage reference turns out to be from a secondary adaptation (Faktabaari EDU toolkit, possibly), the design does not need to change — the principles captured are the same ones Finland actually teaches.

2. **"Chain of credibility" as a formal IC doctrine.** The term is in practical use but the research agent could not locate a canonical IC publication that formalizes it the way STANAG 2511 is formalized. Schum's evidential reasoning work is the theoretical foundation; Tecuci's Disciple system is the closest implementation. Treat the principle as sound but the naming as informal.

3. **Secondary-source citations.** Several key references — Heuer & Pherson's 2010 *Structured Analytic Techniques* book, Bennett & Waltz's 2007 *Counterdeception* book — are cited from secondary summaries in this note. If the design work reaches a point where direct quotation from these sources matters, they need primary-source verification.

4. **The 2009 Primer does not contain standalone "Premortem" or "Deception Detection" chapters** despite common misattribution. Those techniques were formalized in Heuer & Pherson's 2010 book. This note cites both sources correctly.

5. **Tip-and-cue formal paper** (arXiv:2512.09670, "An Automated Tip-and-Cue Framework") was flagged as recent and not fully verified by the research agent. The architectural pattern itself is standard and does not depend on this specific paper.

6. **Calibration cadence.** Rule 12 (structural humility) requires retrospective calibration, but the research did not resolve how often that should run, against what ground-truth signal, or how the system should handle disagreement between retrospective calibration and current posterior. This is an open design question for the L3 spec phase.

---

## References

### Primary-source reads (verified ✓)

- Heuer, R. J. Jr. (1999). *Psychology of Intelligence Analysis*. Washington, DC: Center for the Study of Intelligence, CIA. Foreword by Douglas MacEachin. ✓ Chapters 5 and 8 read directly.
- *A Tradecraft Primer: Structured Analytic Techniques for Improving Intelligence Analysis*. US Government, CIA Center for the Study of Intelligence, March 2009. ✓ Full PDF read.

### Psychology of deception resistance

- Kunda, Z. (1990). The case for motivated reasoning. *Psychological Bulletin*, 108(3), 480–498.
- Nickerson, R. S. (1998). Confirmation bias: A ubiquitous phenomenon in many guises. *Review of General Psychology*, 2(2), 175–220.
- Tversky, A., & Kahneman, D. (1973). Availability: A heuristic for judging frequency and probability. *Cognitive Psychology*, 5(2), 207–232.
- Tversky, A., & Kahneman, D. (1974). Judgment under uncertainty: Heuristics and biases. *Science*, 185(4157), 1124–1131.
- Tversky, A., & Kahneman, D. (1981). The framing of decisions and the psychology of choice. *Science*, 211(4481), 453–458.
- Hovland, C. I., & Weiss, W. (1951). The influence of source credibility on communication effectiveness. *Public Opinion Quarterly*, 15(4), 635–650.
- Kumkale, G. T., & Albarracín, D. (2004). The sleeper effect in persuasion: A meta-analytic review. *Psychological Bulletin*, 130(1), 143–172.
- Hasher, L., Goldstein, D., & Toppino, T. (1977). Frequency and the conference of referential validity. *Journal of Verbal Learning and Verbal Behavior*, 16(1), 107–112.
- Fazio, L. K., Brashier, N. M., Payne, B. K., & Marsh, E. J. (2015). Knowledge does not protect against illusory truth. *Journal of Experimental Psychology: General*, 144(5), 993–1002.
- Johnson, M. K., Hashtroudi, S., & Lindsay, D. S. (1993). Source monitoring. *Psychological Bulletin*, 114(1), 3–28.
- Kahneman, D. (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.
- Alter, A. L., & Oppenheimer, D. M. (2009). Uniting the tribes of fluency to form a metacognitive nation. *Personality and Social Psychology Review*, 13(3), 219–235.
- Sperber, D., & Wilson, D. (1986/1995). *Relevance: Communication and Cognition*. Blackwell.
- Wilson, D., & Sperber, D. (2004). Relevance theory. In Horn & Ward (eds.), *The Handbook of Pragmatics*, pp. 607–632.
- Levine, T. R. (2014). Truth-Default Theory (TDT): A theory of human deception and deception detection. *Journal of Language and Social Psychology*, 33(4), 378–392.
- Levine, T. R. (2019). *Duped: Truth-Default Theory and the Social Science of Lying and Deception*. University of Alabama Press.
- McGuire, W. J. (1964). Inducing resistance to persuasion: Some contemporary approaches. *Advances in Experimental Social Psychology*, 1, 191–229.
- Roozenbeek, J., Traberg, C. S., & van der Linden, S. (2022). Technique-based inoculation against real-world misinformation. *Royal Society Open Science*, 9(5), 211719.
- Roozenbeek, J., & van der Linden, S. (2019). The fake news game: actively inoculating against the risk of misinformation. *Journal of Risk Research*, 22(5), 570–580.
- Caulfield, M. (2019). SIFT (The Four Moves). *Hapgood* blog.
- Caulfield, M. (2017). *Web Literacy for Student Fact-Checkers*. Open textbook.
- Wineburg, S., & McGrew, S. (2019). Lateral reading and the nature of expertise: Reading less and learning more when evaluating digital information. *Teachers College Record*, 121(11).
- Breakstone, J., Smith, M., Wineburg, S., et al. (2021). Students' civic online reasoning: A national portrait. *Educational Researcher*, 50(8), 505–515.
- McGrew, S., Breakstone, J., Ortega, T., Smith, M., & Wineburg, S. (2018). Can students evaluate online sources? *Theory & Research in Social Education*, 46(2), 165–193.

### Finnish media literacy

- Finnish National Agency for Education (Opetushallitus). (2014). *National Core Curriculum for Basic Education*. Multiliteracy competency (L4).
- Kivinen, K. (2023). In Finland, we make each schoolchild a scientist. *Issues in Science and Technology*.
- Henley, J. (2020, January). How Finland starts its fight against fake news in primary schools. *The Guardian*.

### Military intelligence tradecraft

- Heuer, R. J. Jr. (1999). *Psychology of Intelligence Analysis*. CIA Center for the Study of Intelligence. ✓
- *A Tradecraft Primer: Structured Analytic Techniques for Improving Intelligence Analysis* (2009). US Government / CIA Center for the Study of Intelligence. ✓
- Zlotnick, J. (1972). Bayes' theorem for intelligence analysis. *Studies in Intelligence*, 16(2), 43–52.
- Fisk, C. E. (1972). The Sino-Soviet border dispute: A comparison of conventional and Bayesian methods for intelligence warning. *Studies in Intelligence*, 16(2), 53–62.
- Besombes, J., & Nimier, V. (2013). URREF reliability versus credibility in information fusion (STANAG 2511). *Proceedings of the 16th International Conference on Information Fusion* (FUSION 2013), Istanbul.
- Irwin, D., & Mandel, D. R. (2019). Improving information evaluation for intelligence production. *Intelligence and National Security*, 34(4), 503–525.
- Heuer, R. J. Jr., & Pherson, R. H. (2010). *Structured Analytic Techniques for Intelligence Analysis*. CQ Press. *(Secondary summary used in this note.)*
- Bennett, M., & Waltz, E. (2007). *Counterdeception Principles and Applications for National Security*. Artech House. ISBN 978-1-58053-935-7. *(Secondary summary used in this note.)*
- Cahn, A. H. (1998). *Killing Détente: The Right Attacks the CIA*. Penn State University Press.
- Tecuci, G., Schum, D., Marcu, D., & Boicu, M. (2016). *Intelligence Analysis as Discovery of Evidence, Hypotheses, and Arguments*. Cambridge University Press.
- Schum, D. (1994). *Evidential Foundations of Probabilistic Reasoning*. Northwestern University Press.

### Adversarial reasoning architectures

- Irving, G., Christiano, P., & Amodei, D. (2018). AI safety via debate. *arXiv:1805.00899*.
- Brown-Cohen, J., Irving, G., & Piliouras, G. (2023). Scalable AI safety via doubly-efficient debate. *arXiv:2311.14125*.
- Itti, L., & Baldi, P. (2009). Bayesian surprise attracts human attention. *Vision Research*, 49(10), 1295–1306. (Originally NIPS 2005.)
- Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11, 127–138.
- Pariser, E. (2011). *The Filter Bubble: What the Internet Is Hiding from You*. Penguin Press.
- Silver, N. (2012). *The Signal and the Noise: Why So Many Predictions Fail — But Some Don't*. Penguin.
- Mason, R. O., & Mitroff, I. I. (1981). *Challenging Strategic Planning Assumptions: Theory, Cases, and Techniques*. Wiley.
- Schwenk, C. R. (1990). Effects of devil's advocacy and dialectical inquiry on decision making: A meta-analysis. *Organizational Behavior and Human Decision Processes*, 47(1), 161–176.
- Hong, L., & Page, S. E. (2004). Groups of diverse problem solvers can outperform groups of high-ability problem solvers. *Proceedings of the National Academy of Sciences*, 101(46), 16385–16389.
- Klein, G. (2007). Performing a project premortem. *Harvard Business Review*, September 2007.
- Mitchell, D. J., Russo, J. E., & Pennington, N. (1989). Back to the future: Temporal perspective in the explanation of events. *Journal of Behavioral Decision Making*, 2(1), 25–38.
- Giles, J. (2005). Internet encyclopaedias go head to head. *Nature*, 438, 900–901.
- Kahneman, D., & Klein, G. (2009). Conditions for intuitive expertise: A failure to disagree. *American Psychologist*, 64(6), 515–526.

### Prior Exocortex research (cross-reference)

- `specs/COGNITIVE_DEFENSE_SYSTEM.md` (March 12, 2026) — unified framework for agent security and human psyops defense. Cites Herman & Chomsky, Rid, Vosoughi et al., van der Linden.
- `specs/COGNITIVE_DEFENSE_SYSTEM_v2.md` — operational schemas for contamination cascade handling.
- `specs/COUNTER_PATRIOTS_SOURCE_INTELLIGENCE.md` — source profiling vector sets (identity, topical, bias, behavioral).
- `specs/COUNTER_PATRIOTS_EPISTEMIC_STAGING.md` — three-state claim model (Staged → Promoted → Falsified) with van der Linden inoculation.
- `specs/EPISTEMIC_INTEGRITY_DESIGN_NOTE.md` — three-component evidence audit (Evidence Ledger, Epistemological Classifier, Temporal Anchor).
- `specs/NARRATIVE_STABILITY_DESIGN_NOTE.md` and `specs/NARRATIVE_STABILITY_SPEC_L3.md` (2026-04-14, shipped) — retcon detection with modality-aware signal classification.
- `specs/HEDGE_PATTERN_DESIGN_NOTE.md` (2026-04-14, in progress) — hedged-assertion-with-vague-attribution detection with source-type-conditional signal routing.

---

*The principle the research converges on, across three independent traditions: a system that evaluates incoming information against its existing beliefs cannot use consistency as a filter without producing runaway confidence in wrong models. The protection is to let consistency consolidate but let surprise escalate — and to store every claim with its scrutiny verdict attached, never to suppress. Acknowledge what was said. Explain why you don't think it represents reality accurately. Route the disagreement to expensive review. That is analyst tradecraft; now it is architecture.*
