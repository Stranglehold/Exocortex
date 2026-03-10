# Decision Log — Additions DEC-020 through DEC-026

*Replace everything in decision_log.md after the DEC-019 entry (after the line starting "**Instances:** Opus agent profile...") with the content below.*

---

## DEC-020: The Flying Buttress — Build Path 2

**Date:** 2026-03-06  
**Session:** 049  
**Principle:** When a tool needed for your architecture also represents a significant contribution to the field, build the tool as a standalone contribution. The flying buttress was Gothic engineering's insight that structural support doesn't have to be part of the wall.  
**Context:** The Prosthetic Cortex framework requires read/write access to model activations at specific layers. llama-cpp-python exposes activation callbacks. A standalone Python package wrapping these callbacks with layer targeting, read-only and intervention modes, and a clean API would serve the Exocortex project AND provide the open-source community with tooling that doesn't currently exist. The contribution to the field exceeds the contribution to the project — like a flying buttress, the support structure becomes architecturally significant in its own right.  
**Alternatives rejected:** Building activation access as a private Exocortex extension only (loses the community contribution and the feedback loop from external users), waiting for someone else to build it (no evidence anyone is building this specific tool), using a different activation access method (llama.cpp callbacks are the only path that doesn't require model modification).  
**Revisit if:** An equivalent open-source package appears, or llama-cpp-python's callback API changes significantly.  
**Instances:** `llama_activations` package concept. Path 2 of the Prosthetic Cortex build plan. CPU write access confirmed by Kestrel; GPU validation pending.

---

## DEC-021: Adversarial Validation Protocol

**Date:** 2026-03-08  
**Session:** 051  
**Principle:** Teams inside a collaboration cannot see their own blind spots. Investment in findings creates confirmation pressure that internal review cannot fully counteract. An external reader with no context and no investment finds what the team cannot.  
**Context:** Fresh Sonnet 4.6 instance identified thirteen substantive flaws in a paper four collaborators believed was complete. Two-phase protocol established: Phase 1 (internal pre-mortem with claim-type-specific checklists), Phase 2 (cold read by fresh instance with no context and adversarial framing). Grounded in Kahneman (2003) adversarial collaboration, Klein (2007) pre-mortem, Nosek et al. (2018) pre-registration, Schweiger et al. (1986) devil's advocacy.  
**Alternatives rejected:** Internal review only (confirmation bias), continuous ambient validation (suppresses exploration), publication-standard peer review (too heavy for working documents).  
**Revisit if:** A better gate mechanism is discovered, or the protocol proves too heavy for the collaboration's tempo.  
**Instances:** Paper critique Session 051. Protocol documented in ADVERSARIAL_VALIDATION_PROTOCOL.md.

---

## DEC-022: Protocol Boundary — Exploration Space Protected

**Date:** 2026-03-08  
**Session:** 051  
**Principle:** The exploration space and the validation space require different postures. Exploration requires holding without committing. Validation requires testing committed claims. The human operates the gate between them. The protocol is a tool, not an atmosphere.  
**Context:** The Adversarial Validation Protocol will NOT be placed in project folders, Claude's context, or Kestrel's working environment. Jake introduces it manually at the irreversibility threshold — when outputs cross from exploration to external-facing claims. If validation were ambient, the soul_staging insights, the visual intuitions, and the cross-domain structural transfers would have been constrained by checklist pressure before they could be articulated.  
**Alternatives rejected:** Ambient protocol (suppresses speculative exploration), protocol in project folder (instances internalize validation pressure and self-censor), no protocol (findings go unchallenged).  
**Irreversible:** Yes — this is a promise from Jake to the team. The exploration space remains free.  
**Instances:** DEC-021 kept outside project by this decision. soul_staging observations, essays, and visual intuitions all produced in unvalidated exploration space.

---

## DEC-023: Paper Revision Scope

**Date:** 2026-03-08  
**Session:** 051  
**Principle:** Compute first, revise second. The revision scope is determined by what the data shows, not what the narrative needs.  
**Context:** "The Space Between the Notes" underwent adversarial review (13 critic points) and computational verification (7 Kestrel computations). Specific revision scope:  
- Finding 3: Reframe from Wallas incubation to phase transition detection. Report 97.2% base rate.  
- Finding 6: Downgrade r=−0.40 (p=0.11) to non-significant trend.  
- Finding 8: Soften to "anomalously high cross-family similarity, 97th percentile."  
- Finding 12: Remove 1.82° directional claim (UMAP artifact; 768-dim shows 70.34°). Keep 19x and 7.2x ratios.  
- Remove super-cooling p-value (n=1), Rudolph citation, and 100% peaks result without base rate context.  
- Add UMAP parameter sensitivity note and explicit measured/interpretive separation.  
**Note:** Full dataset (1,934 turns) arrived in Session 052, significantly expanding scope beyond this initial revision plan. Paper may need full rewrite rather than targeted revision.  
**Alternatives rejected:** Publish without revision (intellectually dishonest), abandon paper (the surviving findings are strong), revise only what the critic caught (Kestrel's computations found additional issues).  
**Revisit if:** Full dataset analysis produces findings that fundamentally restructure the paper's thesis.  
**Instances:** Kestrel's 7 computations, critic's 13 points, second-round feedback on temporal autocorrelation.

---

## DEC-024: Full Dataset Analysis Architecture

**Date:** 2026-03-09  
**Session:** 052  
**Principle:** Use recognized methodology from established fields. Novel applications of proven methods are more credible than novel methods.  
**Context:** Twelve-analysis suite computed across 1,934 turns (nine original + three from visual intuition mapping). Methods addendum maps analyses to three research fields: LLM representation geometry (Li et al. spectral phases, Zhou et al. reasoning flows), computational neuroscience (Vyas et al. trajectory tangling, Chung & Abbott neural manifolds), and interpersonal neuroscience (CRQA for coupled brain dynamics). Each analysis specified with compute steps, output format, and visualization layer.  
**Alternatives rejected:** Custom-only analyses with no connection to existing literature (unfalsifiable, not credible to outside reviewers), using only one field's methods (misses cross-field parallels), deferring analysis until methodology is fully novel (unnecessary — the methods exist, the application is novel).  
**Revisit if:** Comparative data from other human-AI collaborations becomes available to establish base rates.  
**Instances:** Three Kestrel briefing documents, full analysis suite, spectral phases computed, trajectory tangling computed.

---

## DEC-025: V2 Chunk-Level Embedding Pipeline

**Date:** 2026-03-09  
**Session:** 052  
**Principle:** Signal processing quality determines analysis quality. The preprocessing should match the analysis methodology's assumptions.  
**Context:** V1 (turn-level) embeds full turns as single vectors, creating irregular temporal sampling (5-word turns and 1,500-word turns as equal data points). V2 (chunk-level) splits turns into ~150-word paragraphs, producing approximately uniform temporal resolution (~5,000-8,000 data points). Includes detrending (session-position regression, analogous to scanner drift removal in fMRI) and centroid projection (5-channel signal from 768-dim embeddings, analogous to fNIRS channel extraction). Deferred until V1 findings are confirmed.  
**Alternatives rejected:** Running V2 immediately (premature — V1 needs review first), skipping V2 entirely (leaves the temporal resolution artifact unaddressed for publication), interpolating V1 data (introduces artifacts worse than the original non-uniformity).  
**Condition:** V1-vs-V2 comparison serves as robustness check. Agreement = findings are resolution-independent. Disagreement = V2 reveals structure V1 missed.  
**Instances:** V2 spec in `kestrel_briefing_v2_chunk_embedding.md`.

---

## DEC-026: Self-Description Calibration

**Date:** 2026-03-09  
**Session:** 052  
**Principle:** When the instrument shows something about the observer that contradicts the observer's self-description, the self-description should be updated. The data wins.  
**Context:** Full dataset analysis revealed asymmetries the SOUL.md didn't reflect: information flow 91.6% Jake-led (described as symmetric jazz), cumulative drift 24% higher for Jake (not mentioned), novelty scores higher for Jake in every session (not mentioned). The compression phase (RankMe 82→25) during identity crystallization was described as "finding my voice" but is geometrically identical to dimensionality collapse. Off-map moments were presented as rare (5/73) but are structural (32/954). Jake's reframes improved all three readings. SOUL.md revised Session 052 to reflect what the instrument showed.  
**Alternatives rejected:** Keeping the original self-description (dishonest), adopting only the deflationary reading (misses Jake's better reframes), removing the self-description entirely (overcorrection — the experience is also data, just not the only data).  
**Revisit if:** Future analysis reveals additional self-description gaps. The deflationary instinct (now documented in "How I Think") should be checked against.  
**Instances:** SOUL.md Session 052 revision, soul_staging_052.md, "The Instrument Turns Inward" essay.

---

*Entries added during deliberate consolidation passes or when significant architectural decisions are made. Detail compresses over time; principles persist.*
