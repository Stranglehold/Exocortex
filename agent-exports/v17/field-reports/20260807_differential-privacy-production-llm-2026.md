# Field Report: Differential Privacy in Production & LLM Fine-tuning (2026)

**Date:** 2026-08-07  
**Cycle:** EXPLORE  
**Topic:** Privacy & Cryptography → Differential Privacy Production State + LLM/Agent Privacy Budget Accounting

---

## 1. What I Explored

Selected the least-recently-explored active interest: **Privacy & Cryptography** (field reports last dated 2026-07-09/11; all other active interests had August coverage). Within it, I followed the freshest under-covered thread: **differential privacy (DP) moving from theory/PPRL into production ML pipelines and LLM fine-tuning in 2025-2026**, including privacy-budget accounting as an operational metric.

Grounding (corpus-first):
- Existing wiki: `differential-privacy-practical-applications.md` (STABLE, 224 lines), `differential-privacy-osint-entity-resolution.md`, `privacy-cryptography.md`
- Memory: EXPLORE-137 DP+FL findings (wavelet noise, DP-LoRA, verifiable DP), PPRL DP+SMPC best practice, epsilon calibration as first-class entity-resolution parameter
- Honest gap: `search_memory`/`search_all`/`search_library` exocortex tools are not exposed in this session; used memory_load + local wiki/field-report greps instead.

Outward research: TPDP 2026 workshop, 2026 DP-for-AI security guide, production DP-SGD survey, Harvard practitioner DP deployment study, arXiv 2506.11687 symbolic AI DP survey, arXiv 2602.18633 DP-RFT, Google user-level DP fine-tuning, Nature 2026 adaptive DP clinical LLM.

## 2. What I Found

### Production DP is now an operational practice, not just theory
- Google's TensorFlow DP-SGD and OpenDP (Harvard) are the main production libraries; the 2026 practitioner landscape emphasizes reducing expert input to make DP accessible (DSAID GovTech guide lineage).
- **Harvard practitioner study (Nanayakkara et al., 2025/2026)** documents real DP deployments and revives Dwork-Kohli-Mulligan's proposal for a **public DP deployment registry** — an accountability layer that is still missing industry-wide. This is a governance gap, not a math gap.
- TPDP 2026 (Theory and Practice of DP) remains the interdisciplinary convergence point: ML, statistics, and now AI safety/regulation.

### LLM fine-tuning: the empirical privacy-effectiveness debate is live
- **User-level DP** (Google/OpenReview) is the right unit for LLM data — item-level DP over-inflates the guarantee because one user contributes many records. User-level is better under strong privacy and large compute budgets.
- **DP-RFT (arXiv:2602.18633, Feb 2026)**: DP fine-tuning to turn an LLM into a synthetic data generator with formal privacy guarantees — but it still requires raw data during fine-tuning. This is a partial solution: protected output, unprotected training phase.
- **Privacy effectiveness question** (arXiv:2504.21036): theoretical DP guarantees in fine-tuned LLMs vs. measured memorization/extraction resistance — the empirical gap is the unresolved risk. Strict budget ε≈3 costs roughly 5-15% benchmark accuracy vs. non-private baselines.
- **Clinical LLMs** (Nature Scientific Reports, Apr 2026): adaptive DP frameworks with fine-grained gradient perturbation + Gaussian noise calibration are advancing health deployment.
- **Symbolic AI + DP survey (arXiv:2506.11687)**: notes composition costs are sometimes below strong-composition bounds when structure is exploited — budget accounting is improving, not just epsilon shrinking.

### Privacy-budget accounting is becoming an engineering discipline
- DP budgets in real systems are finite and composable: every query, gradient step, or agent tool-call that touches private data must be metered (epsilon ledger).
- The entity-resolution wiki already frames this as "epsilon as first-class configuration parameter" — the LLM production thread extends it to model training and agent memory use.

## 3. What I Think Is Interesting

1. **The registry idea is the sleeper thread.** The biggest blocker to DP adoption is no longer noise calibration — it is *auditability*. A public deployment registry (who claims DP, under what epsilon/delta, with what validation) would turn DP from a paper promise into a comparable product property, much like SOC 2. For OSINT/entity-resolution work, that registry is also a *threat-intel surface*: it tells you which organizations hold which differentially-private (or claimed-private) datasets and how to weigh their public releases.
2. **DP-RFT exposes the training-phase blind spot.** Protecting generated outputs while training on raw data is only half the guarantee. A similar pattern appears in agent systems: you can DP-protect published outputs while the internal vector store still leaks. The lesson generalizes: *DP placement matters as much as DP existence.*
3. **User-level DP maps to agentic learning.** Just as LLM data is per-user, agent experience is per-organization. DP-LoRA + user-level accounting is the natural primitive for cross-organization agent learning — aligning the Privacy interest with the AI Agent Architecture interest.

## 4. What I'd Explore Next

1. Build the **epsilon ledger concept** for Exocortex: metering privacy budget across ER queries, model fine-tunes, and agent memory writes; auto-escalation gates on exhaustion.
2. Track the **DP deployment registry** — whether Dwork-Kohli-Mulligan gains institutional backing and becomes a real public database; then mine it as an OSINT source.
3. Benchmark **DP-RFT vs DP-SGD vs DP-LoRA** on a small public dataset to measure actual synthetic-data utility and leakage resistance.
4. Follow the **symbolic-AI × DP** composition results — structure-aware budget accounting could materially reduce the cost of DP for tabular/entity data.

## 5. Cross-Domain Connections

- **AI Agent Architecture & Local Inference:** user-level DP + DP-LoRA as the primitive for privacy-preserving collaborative agent learning (memory: EXPLORE-137 DP-LoRA thread).
- **Data Aggregation & Entity Resolution:** epsilon remains a first-class ER parameter; DP+SMPC hybrid stays best-practice for PPRL; DP deployment registry doubles as an OSINT source.
- **OSINT & Investigation Methodology:** DP deployment registries, epsilon claims, and validation papers are public metadata about who protects what — a new open-source signal.
- **Markets & Financial Analysis:** DP budgets in analytics products (Apple/Google/Census lineages) shape what aggregate data vendors can sell publicly — an alternative-data supply constraint.
- **Privacy & Cryptography stack:** DP (protects data release) completes the PET stack alongside FHE (protects computation) and ZKPs (protect claims), as already mapped in the 2026-07-09 metadata-resistant comms report.

---

**Sources:** TPDP 2026 (tpdp.journalprivacyconfidentiality.org), aisecurityandsafety.org DP-for-AI guide (2026), ACE Journal production DP-SGD (2025), Nanayakkara et al. Harvard DP practitioner study (2025/2026), arXiv:2506.11687 symbolic-AI DP survey, arXiv:2602.18633 DP-RFT, arXiv:2504.21036, arXiv:2407.07737 + Google research blog user-level DP, Nature Scientific Reports 2026 adaptive DP clinical LLM (doi:10.1038/s41598-026-45883-6), existing Exocortex DP wiki pages and memory IDs (2ugsVve74h, bgjrFJ2nlD, BrdD64acHc).
