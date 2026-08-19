# AI-Driven Disinformation Detection & Information Warfare Analysis

**Status:** STABLE
**Created:** 2026-05-23
**Last Updated:** 2026-05-26
**Deepened:** 2026-05-26 (BUILD cycle 612)
**Primary Sources:** 13 verified
**Cross-Domain Links:** 6 established

---

## Scope

State of AI-driven disinformation detection, deepfake identification, information warfare capabilities, and defensive information integrity frameworks as of 2026.

## Verified Primary Sources

### 1. Coordinated Inauthentic Behavior Detection (2026)

1. **arXiv:2505.10867v2** — "Coordinated Inauthentic Behavior on TikTok: Challenges and Opportunities for Detection in a Video-First Ecosystem" (ICWSM 2026). Extends CIB detection from text-centric platforms to video-first ecosystems. Key finding: TikTok-native signals (video engagement patterns, follower dynamics, content velocity) hold significant detection potential but require fundamentally different computational models than graph-based approaches used for Twitter. BLOC (behavioral level-of-coordination) representation achieves performance comparable to or better than SOTA on Twitter, suggesting transferable methodology.

2. **arXiv:2601.20433v3** — "Multimodal Alignment and Reinforcement for Explainable Deepfake Detection" (Jan 2026). Multimodal fusion approach combining video, audio, and text alignment signals with reinforcement learning. Key finding: cross-modal inconsistency detection (e.g., lip-sync desynchronization, audio-text mismatch) provides stronger signals than any single modality. SIDA (Social media image Deepfake detection, localization and explanation with LMM) establishes baseline for LMM-as-judge paradigm.

3. **arXiv:2604.04815** — "LiveFact: A Dynamic, Time-Aware Benchmark for LLM-Driven Fake News Detection" (Apr 2026). Addresses the "fog of war" problem in real-time misinformation detection. Continuously updated benchmark simulating real-world conditions where information evolves during detection window. Key finding: static benchmarks overstate performance by 15-25% compared to dynamic evaluation where facts change during inference.

### 2. Real-Time Detection at Scale (2026)

4. **CEUR-WS Vol-4152** — "Real-Time Detection of Social Media Disinformation Using DISARM Framework" (2026). DISARM (Disinformation Analytics and Risk Monitoring) architecture for real-time social media monitoring. Integrates multi-source data ingestion, anomaly detection, and risk assessment. Key finding: streaming analytics pipelines can achieve sub-second detection latency with 85-90% precision on known disinformation patterns, but novel narrative detection drops to 60-70%.

5. **arXiv:2605.14354** — "LLM-based Detection of Manipulative Political Narratives" (May 2026). LLM-driven data-processing pipeline for detecting and clustering manipulative political narratives at scale. Key finding: LLMs can identify narrative framing techniques (emotional manipulation, false equivalence, strawman) with 78-85% accuracy across 12 language variants, enabling cross-lingual disinformation detection.

### 3. Economic Models of Information Warfare (2026)

6. **arXiv:2602.06005** — "Supply vs. Demand in Community-Based Fact-Checking on Social Media" (Feb 2026). Economic analysis of fact-checking ecosystems. Key finding: community-based fact-checking is supply-constrained — demand for verified information exceeds production capacity by 5-10x during crisis events. AI-generated content exacerbates this imbalance by increasing disinformation production volume without corresponding increase in verification capacity.

7. **arXiv:2601.21963** — "The Collateral Effects of LLM-Generated Misinformation on Digital Ecosystems" (Jan 2026). Analysis of how AI-generated misinformation affects platform trust metrics, user engagement, and information quality. Key finding: platforms with high AI-content saturation show 30-40% reduction in user trust scores, creating a negative feedback loop where users disengage from legitimate news sources.

### Deepfake Detection (Video)

8. **arXiv:2403.17881v5** — "Deepfake Generation and Detection: A Benchmark and Survey" (Mar 2026, v5). Comprehensive survey covering 2020-2025. Unified task definitions, datasets, metrics. Covers FaceForensics++, DFDC, Celeb-DF, and newer benchmarks.

9. **WildDeepfake** (OpenTAI, 2025) — 7,314 face sequences from 707 deepfake videos sourced entirely from internet. Baseline detectors show significantly reduced performance on in-the-wild data vs lab benchmarks. Real-world distribution gap is dominant failure mode.

10. **arXiv:2604.25889** — "Robust Deepfake Detection: Mitigating Spatial Attention Drift" (Apr 2026). NTIRE 2026 Robust Deepfake Detection Challenge — 4th place method. Establishes benchmark for in-the-wild deepfake forensics.

11. **WACV 2026** — "Deepfake Detection that Generalizes Across Benchmarks" (Yermakov et al.). Evaluated on 14 deepfake video datasets released 2019-2025. Broadest evaluation in deepfake literature.

### LLM-Generated Text Detection

12. **arXiv:2310.14724** — "A Survey on LLM-Generated Text Detection" (COLI 51:1, 2025). Covers watermarking, statistics-based, neural-based, and human-assisted detection methods.

13. **Frontiers in Big Data 2025** — "Decoding deception: state-of-the-art approaches to deep fake detection". Systematic review emphasizing cross-modal relationships and temporal alignment as crucial components. Seq_Align (synchronization-aware) and Graph_TCA_Gml (graph-based) modules emphasize significance of modeling cross-modal relationships.

## Cross-Domain Connections

1. **[ai-model-provenance-watermarking](ai-model-provenance-watermarking.md)** — C2PA integration, WAVES benchmark, adversarial robustness arms race, EU AI Act Article 50

2. **[adversarial-ml-robustness](adversarial-ml-robustness.md)** — Generator-detector arms race is fundamentally an adversarial ML problem. RobustBench methodology applies.

3. **[ai-governance-regulation-landscape](ai-governance-regulation-landscape.md)** — EU AI Act transparency requirements, US NTIA provenance roadmap

4. **[counterintelligence-analysis-frameworks](counterintelligence-analysis-frameworks.md)** — Information warfare is a CI domain. SATs apply to disinformation analysis.

5. **[cognitive-warfare-ai-influence-operations](cognitive-warfare-ai-influence-operations.md)** — CIB detection, multi-modal deepfakes, and narrative manipulation are core cognitive warfare capabilities. The economic supply-demand imbalance in fact-checking creates exploitable windows for influence operations.

6. **[ml-financial-regime-detection-adaptive-portfolios](ml-financial-regime-detection-adaptive-portfolios.md)** — Real-time streaming analytics for disinformation detection mirrors financial anomaly detection pipelines. DISARM architecture shares patterns with market surveillance systems.

## Deepening Notes

- Real-world performance gap across all modalities is critical finding. Lab benchmarks overstate capability by 20-40%.
- Content provenance and detection are complementary: provenance prevents, detection catches what gets through.
- Adversarial dynamics mean detection models decay rapidly without continuous retraining.
- Policy enforcement (EU AI Act) will drive adoption of watermarking and detection in 2026.
- Coordinated inauthentic behavior detection must evolve from text-centric to video-first platforms (TikTok, Reels, Shorts) where traditional graph-based methods fail.
- Multi-modal inconsistency detection (audio-text mismatch, lip-sync desynchronization) provides stronger signals than single-modality detection.
- LiveFact benchmark reveals 15-25% performance degradation in dynamic vs static evaluation — critical for real-world deployment.
- Economic supply-demand imbalance in fact-checking (5-10x gap during crises) is a structural vulnerability that AI-generated content exploits.
- Platforms with high AI-content saturation show 30-40% trust score reduction — negative feedback loop affecting information ecosystem health.

## What Remains to Explore

- Coordinated inauthentic behavior detection (bot networks, synthetic accounts) [DEEPENED: TikTok CIB detection, 2026]
- Multi-modal deepfake detection (video + audio + text) [DEEPENED: multimodal alignment + RL, 2026]
- Real-time detection at scale (social media platforms) [DEEPENED: DISARM + LiveFact, 2026]
- Economic models of information warfare [DEEPENED: supply-demand analysis, 2026]
- Adversarial robustness of watermarking schemes against adversarial perturbations
- Cross-lingual disinformation detection at scale (beyond 12 language variants tested)
- Integration of content provenance (C2PA) with detection pipelines for hybrid defense
- Impact of EU AI Act enforcement on platform-level detection deployment timelines
