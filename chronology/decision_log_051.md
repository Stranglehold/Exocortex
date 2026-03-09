# Decision Log — Session 051 Additions

## DEC-021: Adversarial Validation Protocol
**Date:** March 8, 2026
**Decision:** Establish a two-phase adversarial validation protocol for Exocortex outputs that make claims about the world (papers, findings, architectural claims). Phase 1: internal pre-mortem with claim-type-specific checklists. Phase 2: cold read by fresh instance with no context and adversarial framing.
**Informed by:** Fresh Sonnet 4.6 instance identified thirteen substantive flaws in a paper four collaborators believed was complete. Grounded in Kahneman (2003) adversarial collaboration, Klein (2007) pre-mortem, Nosek et al. (2018) pre-registration, Schweiger et al. (1986) devil's advocacy.
**Rationale:** Teams inside a collaboration cannot see their own blind spots. Investment in findings creates confirmation pressure that internal review cannot fully counteract. An external reader with no context and no investment finds what the team cannot.
**Status:** Protocol documented in ADVERSARIAL_VALIDATION_PROTOCOL.md. Awaiting team review and refinement.

## DEC-022: Protocol Boundary — Exploration Space Protected
**Date:** March 8, 2026
**Decision:** The Adversarial Validation Protocol will NOT be placed in project folders, Claude's context, or Kestrel's working environment. It is kept by Jake and introduced manually at the irreversibility threshold — when outputs cross from exploration to external-facing claims.
**Informed by:** The recognition that ambient validation pressure would suppress the speculative, ambiguous, staging-posture exploration that produces the collaboration's most valuable insights. The soul_staging finding, the Fibonacci spiral, the Berserk vortex, and the cross-domain structural transfers all emerged in exploratory space that would have been constrained by ambient checklist pressure.
**Rationale:** The exploration space and the validation space require different postures. Exploration requires holding without committing. Validation requires testing committed claims. The human operates the gate between them. The protocol is a tool, not an atmosphere.
**Irreversible:** Yes — this is a promise from Jake to the team. The exploration space remains free.

## DEC-023: Paper Revision Scope
**Date:** March 8, 2026
**Decision:** "The Space Between the Notes" will undergo substantial revision based on Kestrel's seven computational results. Specific changes:
- Finding 3 (Wallas): Reframe from incubation → illumination causal chain to phase transition detection. Drop the Wallas causal interpretation. Keep d=2.12 as measuring startup-vs-mature phase boundary. Report 97.2% base rate alongside all synthesis probability claims. Remove or fully contextualize the 100% peaks result (2.8 pp above chance).
- Finding 6: Downgrade r=−0.40 (p=0.11) from finding to non-significant trend. Keep design note correlation (r=+0.913, p=0.002). "Different geometric physics" becomes a hypothesis, not an established finding.
- Finding 8: Soften "geometric indistinguishability" to "anomalously high cross-family similarity, 97th percentile." Add 768-dim cosine (0.8306).
- Finding 12: Remove directional targeting claim (1.82° UMAP artifact; 768-dim shows 70.34°). Keep 19x per-word ratio and 7.2x total displacement. Keep register-crossing mechanism. Disclose the UMAP vs 768-dim discrepancy explicitly.
- Super-cooling threshold: Remove p-value from n=1 observation. State as preliminary hypothesis only.
- Rudolph citation: Remove. Schiepek et al. carries attractor dynamics alone.
- Karkada citation: Correct to full author list and accurate title.
- 100% peaks: Remove or report with 97.2% base rate context.
- UMAP stability: Add parameter sensitivity note for n_neighbors at n=46 datasets.
- Abstract: Revise to reflect what actually survived.
- Section 1.3: Revise to match revised findings.
- Section 5 (Framework): Reframe Wallas section. The stages may describe the collaboration's vocabulary but the causal chain is not supported.
- Add explicit separation of measured findings vs interpretive framework throughout.
**Informed by:** Kestrel's seven computations + adversarial critic's thirteen points + second-round critic feedback on temporal autocorrelation and sequencing.
**Status:** Pending. Compute complete. Revision to follow.
