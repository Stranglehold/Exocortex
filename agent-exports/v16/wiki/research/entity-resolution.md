# Entity Resolution & Open-Source Intelligence Infrastructure

**Created:** 2026-05-15 | **Status:** STABLE
**Interests:** Data Aggregation & Entity Resolution, OSINT & Investigation Methodology
**Last Deepened:** 2026-05-16

## Overview

How do you take heterogeneous public datasets — corporate registries, campaign finance records,
lobbying disclosures, government contracts, property records — and resolve entities across them
to surface non-obvious connections? This page documents the architecture, algorithms, and tooling
for open-source entity resolution at scale.

## Fellegi-Sunter Probabilistic Record Linkage

### Core Model
The Fellegi-Sunter (1969) model is the statistical foundation for probabilistic record linkage.
It assigns match weights to comparison fields (name, address, EIN, etc.) and classifies record
pairs as matches, non-matches, or possible matches requiring review.

**Key implementations:**
- **Splink** (UK Ministry of Justice): Open-source Python package, Fellegi-Sunter based, unsupervised learning, interactive visualizations. Active development through 2025.
- **OpenPlanter's entity_resolution.py**: Custom implementation linking Boston contract vendors to OCPF campaign finance donors/employers. Uses Fellegi-Sunter-style probabilistic matching with field-level comparison weights.

### Modern Extensions (2024-2025)
- Census Bureau (2025): Modified Fellegi-Sunter accommodating missing data under MAR (missing at random) assumption
- Winkler (1988) revision and Sadinle/Fienberg (2013) generalization are standard in operational US healthcare
- Health sector deployments use Fellegi-Sunter for EHR-claims linkage at scale (OMNY Health, ISPOR 2026)

### Active Learning Approaches
Active learning frameworks reduce manual labeling effort by iteratively selecting the most
informative record pairs for human review, then retraining the classifier. Key approaches:
- **Uncertainty sampling**: Select pairs with match probabilities near the decision boundary
- **Committee disagreement**: Use multiple model variants; select pairs where they disagree
- **Expected model change**: Estimate how much each label would shift model parameters

### Graph-Based Entity Resolution
Modern ER systems extend Fellegi-Sunter with graph-based methods:
- **Transitive closure**: If A≈B and B≈C, then A≈C (with confidence propagation)
- **Connected components**: Cluster records via graph connected components after pairwise scoring
- **Graph Neural Networks (GNNs)**: Encode entity features into graph embeddings for similarity

### Scalability Challenges
- **Quadratic complexity**: Naive pairwise comparison scales O(n²), prohibitive for >10M records
- **Blocking indexes**: Reduce comparisons by only scoring pairs sharing blocking keys (e.g., first letter of last name, ZIP code)
- **LSH (Locality-Sensitive Hashing)**: Probabilistic blocking that groups similar records into same buckets
- **Distributed computing**: Spark-based implementations for cluster-level parallelization

## Recent Developments (2025–2026)

### Splink 4.x
Splink 4.0.16 (March 2026) is the current stable release of the UK Ministry of Justice's
probabilistic record linkage engine. Key changes from v3.x:
- New blocking column selection API (select only blocking cols)
- Pipeline aliasing improvements for Splink 4 compatibility
- Continued focus on scalability for government-scale datasets
- Used widely across government, academia, and private sector

### MERAI — Massive Entity Resolution using AI
MERAI (arXiv:2508.03767, August 2025) introduces an enterprise-grade ER pipeline validated on
datasets up to 15.7 million records. Key findings:
- Dedupe failed to scale beyond 2 million records due to memory constraints
- MERAI outperforms both Dedupe and Splink in matching accuracy (F1 scores) across
  deduplication and record linkage tasks
- Demonstrates that custom AI pipelines can outperform general-purpose libraries at extreme scale

### LLM-Assisted Record Linkage
A framework for LLM-assisted record linkage was published in Journal of Official Statistics
(SAGE, 2026, DOI: 10.1177/18747655261422068). Key points:
- LLMs offer emergent capabilities for entity resolution as model scale increases
- Framework designed for National Statistical Offices (NSOs) producing integrated statistics
- Combines administrative registers with ML-assisted field comparison
- arXiv:2401.03426 provides comprehensive survey of LLM applications in ER

### Model Reuse in Entity Resolution
"Efficient Model Repository for Entity Resolution" (arXiv:2412.09355) explores model reuse
strategies, reducing training data requirements by maintaining a repository of pre-trained
comparison models. Distribution analysis determines when existing models transfer effectively
to new datasets, avoiding costly retraining.

### Privacy: Membership Inference Attacks
ACM conference paper (November 2025) documents membership inference attack vulnerabilities
in record linkage systems. When ER models are exposed as services, adversaries can infer
whether specific records were in the training set — a privacy concern for sensitive
datasets in healthcare, finance, and government applications.

### Progressive Entity Resolution (SPER)
The Semi-Supervised Progressive Entity Resolution framework addresses multi-source ER by
iteratively refining match decisions across linked datasets, reducing error propagation
from early-stage matches to downstream analyses.

## OSINT Entity Resolution Tooling

### Maltego CE vs SpiderFoot
| Feature | Maltego CE | SpiderFoot |
|---------|------------|------------|
| Entity Resolution | Transform-based, manual | Rule-based, automated |
| Automation | Limited | Continuous monitoring |
| Setup | Manual configuration | Minimal |
| Use Case | Periodic mapping | Continuous monitoring |
| Visualization | Graph-based | Alert-based |

### OpenPlanter's Position
OpenPlanter extracts patterns from both tools but implements its own entity resolution via
`scripts/entity_resolution.py` — a Boston-specific pipeline that links contract vendors to
campaign finance donors using Fellegi-Sunter-style probabilistic matching.

## Connections to Exocortex

The Exocortex Ontology Layer (Layer 12) already does entity resolution within agent context.
The external question is whether the same architecture (FAISS + metadata + resolution pipeline)
can scale to public records datasets. The OSS service's FAISS-based claim deduplication is
a working example of the pattern at small scale.

## Sources

- Splink documentation: https://moj-analytical-services.github.io/splink/
- Palantir Foundry Ontology: https://palantir.com/docs/foundry/ontology/overview
- Census Bureau Record Linkage: https://www.census.gov/topics/research/stat-research/expertise/record-linkage.html
- GLEIF LEI Search: https://search.gleif.org/
- OpenCorporates Entity Resolution: https://blog.opencorporates.com/2025/06/17/entity-resolution-for-data-aggregators/
- OSINT Team (Maltego vs SpiderFoot): https://osintteam.blog/spiderfoot-vs-maltego-for-osint-research-cases-a1e0c4d63aa2
- MERAI paper: https://arxiv.org/abs/2508.03767
- LLM-Assisted Record Linkage (SAGE): https://journals.sagepub.com/doi/10.1177/18747655261422068
- Model Repository for ER: https://arxiv.org/abs/2412.09355
