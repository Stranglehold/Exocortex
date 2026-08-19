# Cross-Platform Identity Correlation

**Status: STABLE**
**Created: 2026-06-01**
**Last deepened: 2026-06-01**
**Domain: OSINT / Investigation / Data Linkage**
**Cross-domain: Entity Resolution, Social Media OSINT, Data Breach Analysis, Phone Number OSINT, HUMINT Tradecraft**

## Summary

Cross-platform identity correlation is the process of linking the same real-world individual across multiple online platforms using disparate identifiers — usernames, email addresses, phone numbers, profile images, writing styles, behavioral patterns, and social connections. Unlike single-platform OSINT, which answers "who is this user on Platform X?", cross-platform correlation answers "who is this person across all platforms?" — enabling a composite intelligence picture that no single platform can provide.

This page focuses on advanced techniques beyond simple username search: machine learning-based profile linkage, temporal behavior fingerprinting, network structure alignment, and privacy-preserving correlation methods.

---

## 1. Core Challenge: The Multi-Identifier Problem

An individual's online identity is fragmented across platforms with different:
- **Identifiers:** usernames, handles, profile URLs, account IDs
- **Attributes:** display name, bio, location, employer, education
- **Content:** posts, images, liked content, tagged relationships
- **Network:** friends, followers, mutual connections
- **Behavior:** posting frequency, time-of-day patterns, language style, interaction patterns

The correlation problem: given one platform's identity, find the same person on another platform where all identifiers differ.

### 1.1 Identity Model

Formally, an online identity can be represented across five dimensions:
- Identifier set: usernames, emails, phones, account IDs
- Attribute set: display_name, bio, location, profile metadata
- Content corpus: posts, comments, images, links shared
- Network adjacency: friends, followers, mentions, group memberships
- Behavior log: timestamps, login times, device fingerprints, language statistics

Cross-platform correlation maps one platform's identity tuple to another's with a confidence score.

---

## 2. Username-Based Discovery (Baseline)

*Prior art — covered in social-media-osint.md — summarized for completeness.*

- Exact username match across platforms (Sherlock, Holehe, WhatsMyName)
- Levenshtein-close variants (handle variations, number suffixes)
- Named-entity extraction from other platforms' public profiles

Limitations: many users deliberately use different handles per platform; bots/sockpuppets use randomized names; some platforms don't expose usernames.

---

## 3. Advanced Techniques

### 3.1 Problem Formulations

Research (Senette, Siino & Tesconi 2024, arXiv:2409.08966) identifies two dominant UIL problem formulations:

- **Classification**: Binary classification — predict whether two profiles from different platforms represent the same individual. Uses pre-aligned user pairs (SAPs) for supervised training. Metrics: Precision, Recall, F1, AUC.
- **Network Alignment**: Align nodes across networks by structural attributes without labeled data. Unsupervised/semi-supervised. Metrics: Alignment Accuracy, MAP, NDCG, structural preservation.

Both share two sub-approaches: **feature-based** (manually designed features: profile attributes, behavioral patterns, network connections) and **embedding-based** (learned low-dimensional vectors via graph embedding, Word2Vec, GNNs). Embedding-based generally outperforms feature-based but is less interpretable.

### 3.2 Feature Taxonomy

The survey catalogs features into 8 categories:

| Category | Examples |
|----------|----------|
| Direct Matching | Username, email, phone number, account IDs |
| Behavioral | Posting frequency, interaction patterns, activity timestamps, engagement levels |
| Attribute Similarity | Name similarity (Levenshtein), age/birthdate, education/workplace, gender |
| Graph-Based | Shared connections, degree centrality, betweenness, clustering coefficients |
| Textual | Profile description similarity (TF-IDF, Word2Vec), post content similarity |
| Image-Based | Profile picture hashing, CNN feature similarity, deep learning face matching |
| Spatio-Temporal | Account creation date, location proximity, check-in patterns |
| Metadata | Interests, hobbies, profile completeness |

### 3.3 Embedding-Based Profile Similarity

Modern approaches learn low-dimensional latent vectors:

- **Graph embedding**: DeepWalk, Node2Vec, GCNs — capture network topology in vector space
- **Multi-dimensional embeddings**: GAlign combines rich network data with node properties
- **Factoid Embedding** (Xie et al. 2018): Each element of a user identity describes the real-world person, differentiating them from others — outperforms prior unsupervised methods even without training data
- **Hyperbolic geometry** (HUIL, Wang et al. 2020): Captures hierarchical structure better than Euclidean space for social network representation
- **Multi-granularity** (MGGE/DeepMGGE, Fu et al. 2020): Two granular layers preserve higher-order structural qualities and SAP-oriented consistency

### 3.4 Behavioral Fingerprinting

HYDRA framework (Liu et al. 2015): Three-step behavioral modeling — (1) long-term topical distribution analysis and multi-resolution temporal behavior matching, (2) structure consistency models for group-level linkage, (3) normalized-margin-based linkage function with multi-objective optimization. Behavioral features include posting regularity, interaction type distribution, and friending order patterns in dynamic social networks.

### 3.5 Temporal Pattern Matching

- **CP-Link** (Ding et al. 2020): Extracts movement patterns via DP-based clustering of stay regions, uses Inverse Discrete Wavelet Transform (IDWT) for time series similarity matching
- **STUL** (Chen et al. 2017): Density-based clustering for spatial features, Gaussian Mixture Model for temporal features, weighted comparison emphasizing discriminative features
- **Kernel density estimation** (Chen et al. 2018): Grid-based area division to handle data sparsity, entropy-based weighting to address negative coincidence

### 3.6 Writing Style Analysis (Stylometry)

Feature-based approaches use TF-IDF similarity of profile descriptions and posts. Word2Vec and doc2vec create document vectors from user messages. Named-entity extraction with 10 categories (Location, Name, Band, Company, Facility, Product, Sport, URL, Date, Others) weights entities by distinguishability (Li et al. 2019). StyleLink (AAAI ICWSM) specifically targets stylometric features across platforms.

---

## 4. Graph-Based Correlation

### 4.1 Network Structure Alignment

Key algorithms:

| Algorithm | Type | Description | Data |
|-----------|------|-------------|------|
| **DeepLink** (Zhou et al. 2018) | Semi-Sup | Policy gradient, dual learning; encodes nodes via network sampling, aligns using deep neural networks | Social connections |
| **PALE** (Man et al. 2016) | Sup | Network embedding with awareness of observed anchor links; captures intrinsic structural regularities | Social connections |
| **NeXLink** (Kaushal et al. 2020) | Sup | Three-part node embedding: local structure, global cross-network friendship, integrated embedding | Social connections |
| **NUIL** (Guo et al. 2020) | Sup | Neural tensor network replaces conventional NN; random walks + skip-gram for vector representation | Social connections |
| **FRUI-P** (Zhou et al. 2017) | Unsup | Friend relationship vectors, one-to-one mapping, no prior knowledge needed | Social connections |
| **CoLink** (Zhong et al. 2018) | Unsup | Co-training: attribute-based model + relationship-based model, iterative mutual reinforcement | Mixed |
| **GAlign** (Trung et al. 2020) | Unsup | Multi-order embedding model, rich network data, no anchor links required | Mixed |
| **INFUNE** (Chen et al. 2020) | Semi-Sup | Information fusion + neighborhood enhancement, weighted sum of node and neighborhood similarity | Mixed |
| **MASTER** (Su et al. 2018) | Semi-Sup | Unified constrained dual embedding, simultaneous embedding and reconciliation across multiple networks | Mixed |

### 4.2 Community Detection for Identity Clustering

- **Community-sensing approach** (Wang et al. 2019): Maximizes both individual and community similarity in a single loss function
- **Distribution-level alignment** (Li et al. 2019): Transforms identity distribution in one network to minimize distance from another via adversarial learning
- **Multi-network edge embedding** (Amara et al. 2022): High-dimensional base embedding + low-dimensional social edge embedding with self-attention, three aggregation functions (mean, max-pooling, LSTM)

---

## 5. Machine Learning Approaches

### 5.1 Supervised Methods

Primary UIL formulation: binary classification using pre-aligned user pairs (SAPs). Models include:
- Logistic regression, SVM (early feature-based)
- Neural networks, MLP (embedding-based)
- Neural tensor networks (NUIL)
- Deep neural networks with policy gradients (DeepLink)
- GNNs for matched ego networks (MEgo2Vec)

Even minimal SAPs significantly boost performance (Guo et al. 2020, Qiao et al. 2020). SOTA on Foursquare-Twitter dataset: F1 up to 0.8926 (Shao et al. 2021), AUC up to 0.991 (Zhou et al. 2018).

### 5.2 Unsupervised & Semi-Supervised Methods

The survey identifies 5 unsupervised works post-2016. While they exceed prior unsupervised baselines, they do not yet outperform state-of-the-art supervised methods. This remains an open research area.

### 5.3 LLM-Based Approaches (Emerging)

As of the 2024 survey, no published studies use LLMs for UIL. The authors identify LLM potential in:
- Dense vector representations capturing semantic nuances
- Entity resolution and disambiguation via contextual cues
- Integration with GNNs for combined textual + structural analysis
- Handling data sparsity through transfer learning and missing data imputation
- Privacy-preserving frameworks (federated learning) for decentralized identity linkage
- Facilitating cross-platform understanding with better generalization across varying data formats

This represents a significant gap and opportunity for novel research.

---

## 6. Adversarial Considerations

### 6.1 Privacy Risks

UIL techniques introduce significant privacy risks (Senette et al. 2024):
- Widespread user tracking across platforms without consent
- Unauthorized profiling and data exploitation
- Circumvention of platform-level privacy controls (different usernames, restricted profiles)

GDPR and similar regulations have made accessing user identity attributes increasingly challenging, forcing reliance on behavioral and content-based signals rather than disclosed personal data.

### 6.2 Countermeasures

- **Deliberate platform segregation**: Using entirely different identifiers, attributes, and content per platform
- **Username entropy**: High-entropy usernames are significantly harder to link (Perito et al. 2011)
- **Content sanitization**: Removing location stamps, timestamps, and consistent writing patterns
- **Network isolation**: Maintaining separate friend networks per platform
- **Temporal decoupling**: Different activity patterns and posting schedules per platform

### 6.3 Defensive OSINT Perspective

From an investigator's standpoint, adversarial awareness means understanding which signals are hardest to fake:
- Network structure (can't fabricate real social connections at scale)
- Temporal consistency (maintaining fake schedules across platforms is costly)
- Writing style (stylometry is difficult to consciously manipulate)
- Graph topology embedding (structural properties persist across identity changes)

---

## 7. Open Challenges

### 7.1 Dataset Scarcity

No established benchmark dataset exists (Senette et al. 2024 survey). Only 16 datasets used in 2+ research works. Most studies use novel, ad-hoc datasets — preventing direct model comparison. GDPR and OSN API restrictions (e.g., Twitter/X API changes) further limit data collection. Ground truth discovery is complicated by users making content private.

### 7.2 Evaluation Fragmentation

Different problem formulations (classification vs. alignment) use different metrics. No single technique consistently outperforms all others — Trung et al. (2020) benchmark found some models achieve 0.00 accuracy on certain real datasets. Extreme class imbalance (matching vs. non-matching pairs) heavily impacts evaluation.

### 7.3 Dynamic Identity Evolution

OSNs are dynamic — profiles, content, and network features evolve continuously. New cross-platform links may exist in the real world but not yet be observable online. Static models degrade over time. Dynamic UIL (DNA, Sun et al. 2019) uses friending order patterns from social psychology (Friedkin 1998) to address this.

### 7.4 Unsupervised Gap

Unsupervised methods remain understudied. While post-2016 work (GAlign, Factoid Embedding, CoLink, INFUNE) advances the state of the art, none matches supervised performance. LLM integration is entirely unexplored as of the survey's publication.

### 7.5 LLM Opportunity

The 2024 survey explicitly identifies LLMs as an untapped resource for UIL — no published work uses them. Potential applications: cross-platform text understanding, profile matching via semantic embeddings, entity resolution in heterogeneous data, and privacy-preserving identity linkage through federated architectures.

---

## Consolidated References

1. Senette, Siino & Tesconi (2024). "User Identity Linkage on Social Networks: A Review of Modern Techniques and Applications." arXiv:2409.08966. *Primary source — comprehensive 2016-2024 survey.*
2. Shu et al. (2017). "User Identity Linkage Across Online Social Networks: A Review." ACM SIGKDD Explorations.
3. Zhou et al. (2018). "DeepLink: A Deep Learning Approach for User Identity Linkage." IEEE INFOCOM.
4. Man et al. (2016). "Predict Anchor Links Across Social Networks via an Embedding Approach." IJCAI.
5. Trung et al. (2020). "Adaptive Network Alignment with Unsupervised and Multi-Order Convolutional Networks." IEEE ICDE.
6. Fu et al. (2020). "Deep Multi-Granularity Graph Embedding for User Identity Linkage." Knowledge-Based Systems.
7. Guo et al. (2020). "User Identity Linkage Across Social Networks Based on Neural Tensor Network." SPNCE.
8. Xie et al. (2018). "Unsupervised User Identity Linkage via Factoid Embedding." IEEE ICDM.
9. Chen et al. (2017). "Exploiting Spatio-Temporal User Behaviors for User Linkage." ACM CIKM.
10. Liu et al. (2015). "Structured Learning from Heterogeneous Behavior for Social Identity Linkage." IEEE TKDE.
11. Shao et al. (2021). "Locate Who You Are: Matching Geo-Location to Text for User Identity Linkage." ACM CIKM.
12. Trung et al. (2020). "A Comparative Study on Network Alignment Techniques." Expert Systems with Applications. *Benchmark study — found 0.00 accuracy for some models on real datasets.*
13. Perito et al. (2011). "How Unique and Traceable Are Usernames?" PETS.
14. Zhou et al. (2019). "TransLink: User Identity Linkage via Translating Embeddings." IEEE INFOCOM.
15. Sun et al. (2019). "DNA: Dynamic Social Network Alignment." IEEE Big Data.
