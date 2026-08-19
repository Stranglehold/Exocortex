# Identifying Individuals and Organizations from Social Media Profiles and Activity

**Status: STABLE**
**Last updated: 2026-06-03**
**Lines: ~85**

## Overview

Social media platforms are rich sources of open-source intelligence (OSINT) for entity identification and attribution. With 5.24 billion social media users (DataReportal 2026), each platform requires different investigative techniques. Cross-referencing accounts across platforms reveals connections invisible on any single network. This page covers techniques for account discovery, cross-platform identity correlation, profile analysis, and organizational attribution through social media.

## Key Techniques

### 1. Account Discovery

Automated username enumeration tools search hundreds to thousands of platforms simultaneously:
- **Sherlock** — enumerates usernames across 400+ platforms.
- **Maigret** — advanced fork covering 2,500+ sites with false-positive detection and HTML reports.
- **Social Analyzer** (Qeeqbox) — multi-platform OSINT tool with API, CLI, and web app interfaces; assigns reliability scores (0-100) to minimize false positives.

### 2. Cross-Platform User Identity Linkage (UIL)

UIL — also known as Social Identity Linkage, User Identity Resolution, or Anchor Link Prediction — is the process of linking user identities across different social networks by analyzing profile similarities, behaviors, or activities. Techniques fall into two categories:

**Feature-based methods** exploit explicit profile attributes and social-network structures:
- Profile attributes: username, display name, location, bio, profile photo
- Network structure: friends, followers, interactions, group memberships
- Behavioral patterns: posting frequency, temporal patterns, linguistic style

**Embedding-based methods** learn low-dimensional vector representations:
- **PALE** (Predict Anchor Links via Embedding) — uses network embeddings (DeepWalk, matrix factorization) to capture structural regularities, then aligns users across platforms with supervised or semi-supervised models.
- **HUIL** — hyperbolic geometry embedding for hierarchical social network structures.
- **DeepLink** and **NeXlink** — deep learning approaches combining intra-layer and inter-layer structural information.
- Multi-network settings handle three or more social networks simultaneously.

Supervised, semi-supervised, and unsupervised learning approaches all apply, with the choice depending on availability of ground-truth anchor links.

### 3. Content Analysis & Metadata Extraction

- **ExifTool** — extracts metadata (camera model, GPS coordinates, timestamps) from images and videos posted to social media.
- **InVID/WeVerify** — browser extension for verifying video and image authenticity, detecting manipulation.
- **Reverse image search** — identifies reused profile photos, location backgrounds, and cross-platform image sharing.
- **Geolocation analysis** — Instagram metadata, photo backgrounds, check-ins, and tagged locations.
- **Timestamp verification** — cross-referencing post times with known events.
- **Writing-style analysis** — stylometric features (sentence length, vocabulary, punctuation patterns) for authorship attribution.

### 4. Evidence Collection & Preservation

Investigators follow a structured process:
1. Identify target accounts across platforms.
2. Collect publicly available data (posts, connections, check-ins, metadata).
3. Cross-reference findings across multiple platforms.
4. Preserve evidence (screenshots, archived pages via Wayback Machine).
5. Produce documented reports with chain of custody.

### 5. Commercial Platforms

- **Maltego Professional** — full-featured link analysis with commercial data transforms.
- **Social Links** — enterprise platform with real-time monitoring, facial recognition, and cross-platform identity graphs.
- **Skopenow** — automated investigation with AI analysis and court-ready reports.

## Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| [[data-aggregation-entity-resolution]] | Cross-platform identity linkage is entity resolution applied to social media profiles — Fellegi-Sunter probabilistic matching, embedding-based alignment |
| [[email-forensics-header-analysis]] | Email addresses found via social media enable header analysis for IP and infrastructure attribution |
| [[ip-geolocation-network-attribution]] | Social media login IPs (when available via data breaches or legal process) feed IP geolocation pipelines |
| [[data-breach-analysis-identity-linkage]] | Breached credentials link email→username→social profiles, enabling cross-platform identity resolution |
| [[public-records-databases-osint]] | Social media profiles ground-truthed against public records (property, corporate, voter registration) validate identity |
| [[counterintelligence-analysis-frameworks]] | Deception detection on social media uses structured analytic techniques (ACH, Key Assumptions Check) |
| [[adversarial-ai-agent-manipulation]] | Social media content is a vector for prompt injection and adversarial manipulation of AI agents — understanding collection surfaces is defensive |
| [[structured-analytic-techniques-osint]] | SAT frameworks (ACH, Indicators/Signposts) structure social media investigation conclusions |
| [[human-investigation-tactics-techniques]] | Social media investigation inherits human investigation patterns: timeline reconstruction, pattern-of-life analysis, link analysis |

## Sources

1. "User Identity Linkage on Social Networks: A Review of Modern Techniques" — arXiv:2409.08966v1 (2024). Comprehensive survey of UIL methods, datasets, and evaluation.
2. "Social Media Investigation: OSINT Techniques (2026)" — Espectrosint.com. Platform-specific techniques and tool comparison.
3. "OSINT Techniques: Expert Tactics for Investigators (2026)" — ShadowDragon.io. 100+ techniques catalog.
4. "OSINT Techniques for Cross Platform Information Correlation" — Knowlesys.com. AI-driven cross-platform integration.
5. "People Search OSINT: The Analyst's Guide to Identity Resolution (2025)" — UserSearch.com. Identity resolution methodology.
6. "Person of Interest Attribution: Connecting Accounts and Aliases" — SocialLinks.io. Cross-account behavior analysis.
7. "Find Anyone's Social Footprint Ethically" — BrightCoding.dev (2025). Social Analyzer tool overview.
8. osintradar.com — Curated OSINT tools and resources catalog.
