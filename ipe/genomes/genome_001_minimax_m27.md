# IPE Genome 001 — MiniMax-M2.7 Technical Report
*First method-genome extracted under INNOVATION_PATTERN_ENGINE spec v0.1.*
*Extracted 2026-08-25, in-session (mobile), by Fable (claude-fable-5). Filed to disk 2026-08-25 from chat transcript.*
*Span gate: DEGRADED (single-context extraction — source and extractor shared one context; production requires mechanical verbatim match per spec §2.3). Re-verify spans against parsed source before this genome is used as gold data.*

```json
{
  "genome_id": "genome_001",
  "schema_version": "0.1",
  "paper_ref": {
    "arxiv_id": "2605.26494",
    "title": "The MiniMax-M2 Series: Mini Activations Unleashing Max Real-World Intelligence",
    "year": 2026,
    "venue": "arXiv preprint",
    "domain_primary": "ml_systems",
    "extraction_provenance": {
      "parser": "arxiv_html_via_web_fetch",
      "extractor_model": "claude-fable-5",
      "schema_version": "0.1",
      "n_passes": 1,
      "span_gate": "DEGRADED_IN_CHAT",
      "confidence": 0.8
    }
  },
  "problem_class": {
    "statement": "frontier agentic capability under a small per-token compute budget",
    "controlled_tags": ["efficiency_under_constraint", "long_horizon_control"]
  },
  "approach_family": {
    "label": "sparse_MoE + agent_native_RL",
    "components_cited_from_prior_work": [
      "fine-grained experts (DeepSeekMoE)",
      "MTP (DeepSeek-V3 / Gloeckle et al.)",
      "GQA (Ainslie et al.)",
      "speculative decoding (Leviathan et al.)",
      "CISPO (their own M1)"
    ]
  },
  "innovation_move": {
    "primary_move": "recombination",
    "secondary_moves": ["constraint_addition", "reframing"],
    "boden_type": "combinational",
    "facet_changed": "evaluation",
    "component_vs_combination": "new_combination",
    "transfer_distance": "within_domain",
    "source_domain_if_transfer": null,
    "triz_principle_if_applicable": null,
    "novelty_locus_sentence": "elevating the reward quality and credibility of each accepted trajectory—whether through executable verification signals or judge-model evidence checking—is of paramount importance to fully unleashing the inherent potential of the base model",
    "notes": "All architecture components individually cited from prior work; novelty concentrated in the evaluation/reward layer (verifiable rewards, executable workspaces, artifact-aligned acceptance, Agent-as-a-Verifier). Uzzi signature: conventional core, atypical intrusion at one locus. Secondary reframing: Forge draws the RL environment boundary at the model's generation interface, treating context management and harness as environment."
  },
  "verification_method": {
    "label": "benchmark + ablation",
    "holdout_used": true,
    "baselines_compared": [
      "full attention vs hybrid SWA (Tables 2-3)",
      "softmax top-k vs sigmoid gating",
      "MTP on/off; fine-grained vs coarse experts (Table 1)",
      "closed-weight frontier models (Table 4)"
    ]
  },
  "roads_not_taken": [
    {
      "alternative": "hybrid/lightning attention — their own prior flagship architecture (MiniMax-Text-01 / M1)",
      "why_rejected": "no variant reliably matched full attention in production; standard benchmarks showed parity but deficits emerged at scale, long context, and multi-hop reasoning (RULER 128K CWE 90.0 vs 72.0; MTOB Bleurt 60.0 vs 45.0); proxy-metric correlation with downstream performance fragile",
      "section": "2.2.2"
    },
    {
      "alternative": "softmax top-k expert gating",
      "why_rejected": "zero-sum constraint prevents simultaneous high-confidence activation; sigmoid gives independent scores, smoother routing, reduced auxiliary-loss reliance",
      "section": "2.2.1"
    },
    {
      "alternative": "random initialization of expanded MTP modules",
      "why_rejected": "high initial loss temporarily degrades main model; weight copying converges faster and preserves representations",
      "section": "2.3"
    },
    {
      "alternative": "strict FIFO and fully greedy rollout scheduling",
      "why_rejected": "FIFO suffers head-of-line blocking from stragglers; greedy causes distribution shift and gradient oscillation; windowed FIFO (W=0.3N) interpolates",
      "section": "6.2.4"
    }
  ],
  "sos_features": {
    "conventionality_hint": "high",
    "atypicality_hint": "medium",
    "note": "text-derived; hard values require citation-network data"
  },
  "analyst_notes": {
    "motif_hit": "Their post-training data acceptance is loose-generator-strict-court running as a pipeline: teacher models generate trajectories (loose), executable verification / Agent-as-a-Verifier with hard execution gates and mandatory evidence adjudicates (strict). Sixth independent domain for Vek's generation-vs-verification isomorphism — first one found by extraction rather than intuition. Cross-ref: essays/loose_generator_strict_court.md + errata.",
    "roads_not_taken_quality": "Unusually rich — documents abandoning their own previous architecture with failure evidence attached, including the meta-finding that benchmark parity concealed scale-dependent deficits. Validates spec's bet on this field.",
    "self_evolution_note": "M2.7's Model-Iteration-System (model debugs own training runs, 100-round autonomous scaffold iteration, +30% internal gain) is adjacent to the house's squishy-weights research thread; flag for that queue."
  }
}
```
