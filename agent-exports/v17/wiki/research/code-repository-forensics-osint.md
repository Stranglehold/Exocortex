# Code Repository Forensics for OSINT Entity Attribution

**Status: STABLE**

## Overview

Public code repositories — GitHub (400M+ repos, 100M+ developers), GitLab, Bitbucket, Gitee — contain rich metadata trails that enable developer attribution, organizational mapping, and technical supply chain investigation via open-source intelligence (OSINT). Git's Merkle-tree commit architecture makes it virtually impossible to fabricate commit history without leaving traces, positioning repository forensics as a high-confidence evidence source in the OSINT data fusion hierarchy.

This page covers systematic methodology for extracting identity signals from code repositories: commit metadata analysis, code stylometry (authorship attribution), contributor network analysis, CI/CD artifact forensics, and cross-repository identity correlation.

## 1. Git Metadata Analysis

### 1.1 Commit Timestamps & Timezone Fingerprinting

Git commits record author/committer timestamps with UTC offsets. Timezone patterns form a behavioral fingerprint: a developer submitting commits at UTC+8 followed by UTC+1 within hours typically indicates travel, flagging an account potentially shared or compromised. Distributions of commit day-of-week and hour-of-day reveal working patterns that correlate with geographic location and employment type.

**Practical extraction:**
```bash
git log --format='%ad %an' --date=iso | awk '{print $4, $5}' | sort | uniq -c | sort -rn
```

### 1.2 Author Identity Fields

Commit objects store two identity tuples (name+email+timestamp):
- `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` — who wrote the code
- `GIT_COMMITTER_NAME` / `GIT_COMMITTER_EMAIL` — who committed it

Divergence between author and committer is common in corporate environments (patch submission + maintainer merge) but flaggable in individual repos for account compromise or impersonation analysis.

**Email pivoting technique:** Extract all unique author emails from a repository, then cross-reference against breach databases (HaveIBeenPwned, Dehashed), WHOIS records, and social platforms to link developer pseudonyms to real identities.

### 1.3 Commit Message Analysis

Commit messages contain linguistic signals: writing style, language, punctuation habits, use of imperative mood, issue tracker references, and sign-off conventions (Signed-off-by, Co-authored-by). These form a stylometric profile that, when combined with code stylometry, strengthens attribution confidence.

## 2. Authorship Attribution (Code Stylometry)

### 2.1 Foundational Research

**Dauber et al. (arXiv:1701.05681v3)** demonstrated that short, incomplete, and typically uncompilable source code fragments from version control systems can be attributed with 99% accuracy when ensemble-classifying across multiple samples from the same author. Baseline single-sample accuracy was ~73% for 106 programmers, but averaging classification probabilities across sufficient samples achieved near-certain identification.

Key technique: train a classifier on known-author code fragments, classify each fragment individually, then average probabilities across all fragments belonging to a single contributor account. The paper also introduced calibration curves to identify unknown-author samples in open-world settings, flagging samples likely to be falsely attributed.

### 2.2 Stylometric Features

Feature categories extracted from source code for authorship attribution:

| Category | Features |
|----------|----------|
| **Layout** | whitespace (tabs/spaces, indentation depth), line length, brace placement |
| **Lexical** | identifier naming conventions (camelCase vs snake_case), keyword frequency, variable name patterns |
| **Syntactic** | AST node frequency, nested depth, loop/conditional style, abstraction patterns |
| **Structural** | function length, cyclomatic complexity, comment density, import ordering |

### 2.3 Adversarial Considerations

Code stylometry is not deterministic. Adversaries can:
- Obfuscate using automated formatters (clang-format, Prettier, Black)
- Mimic other developers' styles
- Mix code from multiple authors in a single commit

Countermeasures: ensemble multiple signal types (metadata + stylometry + linguistic) and assign Admiralty Code reliability scores to each signal layer.

## 3. Contributor Network Analysis

### 3.1 Repository-Level Networks

Contributor networks model developers as nodes and shared-commit, co-authorship, or code review relationships as edges. Analysis reveals:
- **Core maintainers** (high degree centrality + betweenness)
- **Organizational boundaries** (community detection via Louvain/Leiden)
- **Sock puppet accounts** (shared commit patterns with known accounts, low betweenness, peripheral positions)

**Mockus et al. (arXiv:2002.02707v4)** applied Louvain community detection to a graph of ~2B commits across ~100M repositories linked by shared Git objects. The largest raw cluster contained ~14M repositories due to unrelated repos sharing git objects (pushed/pulled between arbitrary repos). Community detection reduced this to clusters under 100K interconnected repositories, providing a ground-truth map of genuinely related projects.

### 3.2 Cross-Repository Identity Correlation

Pivot techniques to link developer identities across repositories:

- **Commit SHA matching** — identical commit hashes across repos indicate shared history (clone/fork).
- **Email matching** — same author email across repos → high-confidence same identity.
- **Username matching** — same username across repos → moderate confidence (can be impersonated).
- **SSH/GPG key fingerprint correlation** — signed commits or key metadata links accounts.
- **Timestamp correlation** — overlapping commit bursts with matching timezone patterns → behavioral link.

## 4. CI/CD & Build Artifact Forensics

### 4.1 GitHub Actions / GitLab CI Artifacts

CI/CD pipelines generate build logs, test outputs, and deployment manifests that contain:
- Environment variables (sometimes including secrets mistakenly logged)
- Docker image digests and layer hashes
- Deployment timestamps and target infrastructure IP addresses
- Developer comments in workflow files (maintainer identities, internal project names)

### 4.2 Exposed Secrets Detection

Automated scanning tools (TruffleHog, GitLeaks, GitGuardian) detect accidentally committed API keys, database credentials, and cloud service tokens. These secrets, when correlated with organizational cloud infrastructure, provide strong attribution signals linking a repository to a specific organization or individual.

## 5. Tool Ecosystem

| Tool | Category | Description |
|------|----------|-------------|
| **git log** | Metadata extraction | Core Git CLI for commit history, author/date extraction, blame analysis |
| **Gitrob** | Sensitive file discovery | Clones repos to configurable depth, scans commit history for sensitive file signatures (passwords, keys) |
| **TruffleHog** | Secret scanning | Deep commit history scanning for high-entropy strings, API keys, and credentials |
| **GitDorker** | Automated GitHub dorking | Runs GitHub search queries against a target organization to surface sensitive data |
| **OSINT-UI GitHub Tool** | Profile analysis | Investigates developer public activity, repos, languages, exposed emails in commit history |
| **git-filter-repo** | Repository analysis | Fast Git history rewriting and analysis tool; can extract commit statistics and contributor data |
| **Gephi/Cytoscape** | Network visualization | Visualize contributor networks from git log data |
| **NetworkX/igraph** | Network analysis | Programmatic contributor network analysis (centrality, community detection) |
| **GitHub API** | Data extraction | REST/GraphQL API for repository metadata, commit data, contributor statistics |
| **GH Archive** | Historical analysis | Public dataset of GitHub event stream (2011-present) on BigQuery for temporal analysis |
| **SourceCred** | Cred/contribution scoring | Algorithmic cred scoring for contributor influence analysis within projects |

## 6. Investigation Workflow

### Phase 1: Repository Discovery
- Target: username, organization, email address, or domain
- Use GitHub search (user:, org:, email in commits), GitLab search, and cross-platform username matching (Sherlock, Maigret)

### Phase 2: Metadata Extraction
- Clone repository (or use API for metadata-only analysis)
- Extract all commit metadata: author names, emails, timestamps, timezone offsets
- Extract commit messages and sign-off trailers

### Phase 3: Identity Enrichment
- Pivot emails through breach databases (HIBP, Dehashed)
- Pivot usernames through social media platforms
- Cross-reference GPG/SSH keys with keyservers and GitHub/GitLab verified key data
- Query WHOIS for any domains found in commit messages or documentation

### Phase 4: Network Analysis
- Construct contributor graph from commit co-occurrence and code review relationships
- Run community detection to identify organizational clusters
- Identify peripheral/sock-puppet accounts (low centrality, high co-commit with single other account)

### Phase 5: Attribution Fusion
- Assign Admiralty Code reliability scores to each signal layer
- Fuse metadata, stylometric, network, and artifact evidence using Fellegi-Sunter probabilistic linkage
- Output tiered attribution: Activity Cluster → Temporary Group → Named Actor

## 7. Legal & Ethical Boundaries

- **Public repos only** — accessing private repos without authorization is illegal under CFAA and equivalent laws.
- **GDPR implications** — developer emails and names are personal data; EU investigations must establish lawful basis.
- **Code license consideration** — scraping or cloning should comply with repository license terms.
- **Attribution standards** — forensic findings should include Admiralty Code source ratings and acknowledge confidence limitations.

## 8. Cross-Domain Connections

| Connection | Target Wiki Page | Mechanism |
|------------|------------------|-----------|
| **Email Header Analysis** | [[email-header-analysis]] | Commit email → header analysis → IP geolocation chain |
| **IP Address Geolocation** | [[ip-address-geolocation]] | Timezone patterns → geographic inference; CI logs → IP extraction |
| **Metadata Analysis (OSINT)** | [[metadata-analysis-osint]] | Git metadata is a specialized form of digital artifact metadata analysis |
| **DNS & WHOIS Investigation** | [[dns-whois-investigation-osint]] | Domain references in repos → WHOIS ownership → organizational attribution |
| **Data Breach Analysis** | [[data-breach-analysis-osint]] | Email pivot from commit authors → breach database identity linkage |
| **Social Media OSINT** | [[social-media-osint]] | Username/email cross-platform correlation linking dev accounts to social profiles |
| **Network Analysis (OSINT)** | [[network-analysis-techniques-osint]] | Contributor graphs as specialized social network analysis |
| **Entity Resolution (OSINT)** | [[entity-resolution-agent-safety]] | Fellegi-Sunter applied to cross-repository developer identity linkage |
| **Evidence Preservation** | [[evidence-preservation-chain-of-custody-osint]] | Git's Merkle-tree architecture as inherent chain-of-custody mechanism |
| **Intelligence Agency Attribution** | [[intelligence-agency-attribution-methodology]] | Attribution pipeline (parallel collection → fusion → Admiralty scoring → tiered output) maps to repo forensics workflow |
| **Behavioral Mimicry** | [[behavioral-mimicry-research]] | Adversaries spoofing developer identity via style mimicry maps to bot behavioral evasion |
| **Supply Chain Analysis (OSINT)** | [[supply-chain-network-analysis-osint]] | Software supply chain mapping via repository dependency and contributor analysis |


### 2.4 Adversarial Evasion Arms Race (2022-2026)

Code stylometry attribution is under active attack from adversarial techniques spanning four categories:

#### 2.4.1 Adversarial Code Perturbation

**SHIELD (Abuhamad et al., arXiv:2304.13255v1, 2023)** demonstrated that targeted adversarial perturbations can achieve 66-88% impersonation success rates against six state-of-the-art authorship attribution methods (RNN, CNN, and code stylometry-based), with non-targeted attacks exceeding 98.5% success rate and degrading identification confidence by >13%. This has fundamental implications for OSINT attribution reliability: a motivated adversary can programmatically hide their coding fingerprint.

**RoPGen (Li et al., arXiv:2202.06043v1, 2022)** proposed a defensive framework combining data augmentation with gradient augmentation at adversarial training time, learning coding style patterns that are inherently harder to manipulate. RoPGen reduced targeted attack success by 22.8% and untargeted attack success by 41.0% across C, C++, and Java datasets.

#### 2.4.2 LLM-Based Style Obfuscation

**LLM-Powered Code Obfuscation (Salami & Sorkhpour, arXiv:2402.12472, 2024)** investigated whether GPT-3.5 and GPT-4 can effectively alter code stylometry while preserving functionality. Key findings:

- **Single-shot prompting** was largely ineffective — 71-83% of obfuscated samples were still correctly attributed.
- **Multi-shot iterative prompting** with structured format requirements (indentation rules, naming conventions, comment density targets) achieved significantly better evasion, reducing attribution accuracy to 41-55%.
- **Functionality preservation** remains a challenge — 12-18% of LLM-obfuscated code failed to compile or produced different outputs.

**Practical implication for OSINT investigators:** An adversary who invests in multi-round LLM-based style obfuscation can substantially degrade stylometric attribution. Counter-strategy: ensemble stylometry with metadata analysis (timestamps, timezone fingerprints, email pivots) and network signals (contributor graph position) rather than relying on stylometry alone.

#### 2.4.3 Automated Formatter Evasion

Adversaries can route code through opinionated formatters (clang-format, Prettier, Black, gofmt) to strip idiosyncratic layout features. However, formatters only normalize surface-level syntax; deeper features (AST node frequency, algorithm choice patterns, error-handling style, comment semantics) survive formatting. Multi-signal ensemble attribution combining layout + lexical + syntactic + structural features remains robust against single-layer formatter evasion.

#### 2.4.4 Impersonation & Multi-Author Blending

- **Style mimicry**: Adversaries can study a target developer's public code and manually adopt their conventions.
- **Multi-author commits**: Deliberately mixing code from multiple developers in a single commit dilutes individual stylometric signals.
- **Sock puppet laundering**: Progressive style shift over sequential sock puppet accounts, each account gradually adopting different style patterns.

**Countermeasure framework**: Apply Admiralty Code reliability scoring per signal layer and require convergence across ≥3 independent signal types (metadata + stylometry + linguistic + network) before asserting high-confidence attribution.

## 2.5 CI/CD Pipeline Forensics

CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins) generate rich forensic artifacts that extend repository forensics beyond static code analysis.

### 2.5.1 Workflow Tampering Detection

The **Megalodon supply chain attack (May 2026)** compromised 5,561 repositories by injecting a malicious `codeql_analysis.yml` workflow using a stolen GitHub Actions token. The **TanStack attack (May 2026)** poisoned 160 npm packages via malicious preinstall hooks. Both attacks exploited CI/CD trust assumptions — forensic detection requires:

- **Workflow file integrity verification**: Compare current `.github/workflows/*.yml` against git history for unauthorized modifications.
- **Action pinning audit**: Unpinned actions (e.g., `uses: actions/checkout@v3`) are vulnerable to tag mutation attacks; pinned SHA references (`@a81bbbf8298c0fa03ea29cdc473d45769f953675`) prevent this.
- **Workflow permission analysis**: Workflows with `contents: write` or `id-token: write` permissions in public repositories are high-risk forensic indicators.

### 2.5.2 Secret Exposure in Build Logs

CI/CD logs are a primary vector for credential leakage. Redacted secrets (GitHub's `***` masking) can be bypassed through:

- Base64 encoding secrets before printing.
- Splitting secrets across multiple log lines to evade pattern matching.
- Using environment variable expansion to reconstruct secrets (`echo ${{ secrets.AWS_ACCESS_KEY_ID:0:4 }}`).

Forensic secret scanning tools (TruffleHog, Gitleaks, GitGuardian) must be configured to scan not only commit history but also workflow run logs — many organizations miss this secondary attack surface.

### 2.5.3 Build Provenance & SLSA Framework

**SLSA (Supply chain Levels for Software Artifacts)** is Google's framework for build integrity, adopted by the OpenSSF. The four levels:

| Level | Description | Forensic Value |
|-------|-------------|----------------|
| **SLSA 0** | No guarantees | Build artifacts are untrustable; any tampering is undetectable |
| **SLSA 1** | Provenance exists | Build provenance document records builder, source, and build command — provides basic audit trail |
| **SLSA 2** | Hosted build platform | Builds run on a trusted platform with source and build isolation — prevents direct artifact injection |
| **SLSA 3** | Non-falsifiable provenance | Cryptographic attestations (in-toto, Sigstore) make provenance tamper-evident — enables forensic verification that a given artifact was produced by a specific source commit on a specific builder |

**Forensic application**: When investigating a repository, check whether releases include SLSA provenance attestations. The presence of SLSA Level 3 provenance provides cryptographic evidence linking a binary artifact to its source — a high-confidence attribution mechanism. Absence of any provenance is itself an intelligence signal (low security maturity, or deliberate opacity).

### 2.5.4 Runner Compromise Forensics

Self-hosted GitHub Actions runners that process public repository workflows can be compromised. Forensic indicators include:

- Runner registration timestamps that don't align with known deploy events.
- Runner labels that don't match known infrastructure tagging conventions.
- Workflow runs executing on unexpected runner types (e.g., a `ubuntu-latest` workflow executing on a self-hosted runner).
- Long-running runner sessions (>24 hours) — indicative of persistence.

### 2.5.5 OIDC Token & SPIFFE Identity Analysis

Modern CI/CD pipelines increasingly use **OpenID Connect (OIDC)** federation and **SPIFFE (Secure Production Identity Framework for Everyone)** for workload identity instead of static secrets (arXiv:2504.14760v1). Forensic analysis of OIDC token claims (issuer, subject, audience) and SPIFFE SVIDs (SPIFFE Verifiable Identity Documents) can:

- Trace which specific workflow run produced a given artifact.
- Detect token forgery if claims don't match expected pipeline topology.
- Identify unauthorized cross-repository access through OIDC trust misconfigurations.

## 2.6 GitHub Dorking: Advanced Query Patterns

GitHub's code search engine supports advanced query operators that go beyond basic `user:` and `org:` filters:

| Operator | Example | Intelligence Value |
|----------|---------|-------------------|
| `path:` | `path:.github/workflows` | Discover CI/CD configurations across repositories |
| `language:` | `language:python` | Filter by programming language to narrow stylometric analysis |
| `filename:` | `filename:.npmrc OR filename:.pypirc` | Find configuration files containing registry credentials |
| `extension:` | `extension:pem OR extension:key` | Locate exposed private keys |
| `created:` / `pushed:` | `pushed:>2026-01-01` | Temporal filtering for activity timeline reconstruction |
| `size:` | `size:>10000` | Find large files that may contain embedded binaries or datasets |
| `is:` | `is:public is:archived` | Filter by repository state |
| Boolean operators | `org:target-co AND (filename:.env OR filename:config.json)` | Compound queries for targeted discovery |

**GH Archive BigQuery integration**: GH Archive makes all public GitHub events since 2011 queryable via Google BigQuery. This enables temporal analysis at scale:

```sql
-- Find all force-push events to a target organization's repos
SELECT repo.name, actor.login, created_at
FROM githubarchive.day.20260701
WHERE type = 'PushEvent'
  AND JSON_EXTRACT(payload, '$.forced') = 'true'
  AND org.login = 'target-org'
```

This is invaluable for detecting history rewriting (force-push to hide previously exposed secrets) and establishing temporal patterns of repository maintenance.

## 2.7 LLM-Generated Code Detection

The rise of AI coding assistants (GitHub Copilot, Cursor, Claude Code, Codex CLI) creates a new forensic challenge: distinguishing human-authored code from AI-generated code. This matters for attribution because:

- AI-generated code carries the style signature of the model, not the committer.
- An adversary can generate code via LLM to mask their personal stylometric fingerprint.
- False attribution is possible if an investigator attributes AI-generated code to the committer.

**Detection techniques (2025-2026):**

| Approach | Method | Accuracy |
|----------|--------|----------|
| **Statistical features** | N-gram frequency, token repetition patterns, hallucinated API calls | ~72-78% |
| **AST-based** | Unusual structural patterns, overly uniform nesting, templated error handling | ~75-82% |
| **LLM-based detectors** | Fine-tuned classifiers on known human vs. AI code corpora | ~85-90% |
| **Watermarking** | Model-level watermark injection (not yet deployed in major coding assistants) | Not operational |

**Practical guidance**: When attributing code to a developer, cross-validate with pre-Copilot-era commits (pre-2021) to establish a baseline human stylometric profile uncontaminated by AI assistance.

## 2.8 Human-Certified Module Repositories (HCMRs)

**HCMRs (arXiv:2603.02512, 2026)** propose a new architectural model where reusable software modules are curated, security-reviewed, provenance-rich, and equipped with explicit interface contracts. This framework, designed for the era of AI-assisted development, has direct implications for repository forensics:

- **Provenance enrichment**: HCMR-certified modules carry cryptographic provenance chains that simplify forensic artifact-to-source traceability.
- **Interface contract verification**: Explicit interface contracts enable automated verification that a given module's behavior matches its claims — detecting supply chain tampering.
- **Threat surface analysis**: HCMRs formalize the threat model for modular ecosystems, providing a structured taxonomy of tampering vectors (module substitution, interface exploitation, transitive dependency poisoning).

For OSINT investigators, the emergence of HCMR-adopting repositories will create a bifurcated forensic landscape: high-confidence provenance for HCMR-tracked artifacts vs. traditional uncertain attribution for unadopted repositories.

## 9. References

1. Dauber, E., Caliskan, A., Harang, R., et al. "Git Blame Who?: Stylistic Authorship Attribution of Small, Incomplete Source Code Fragments." arXiv:1701.05681v3 (2017). — 99% accuracy attributing short code fragments to 106 programmers via ensemble averaging.
2. Mockus, A., Spinellis, D., Kotti, Z., Dusing, G.J. "A Complete Set of Related Git Repositories Identified via Community Detection Approaches Based on Shared Commits." arXiv:2002.02707v4 (2020). — Louvain community detection on 2B commits / 100M repos to map genuinely related projects.
3. Dunsin, D., Ghanem, M.C. "A Comprehensive Analysis of the Role of Artificial Intelligence and Machine Learning in Modern Digital Forensics and Incident Response." arXiv:2309.07064v2 (2023). — Survey of AI/ML in digital forensics including authorship identification.
4. Iqbal, F. et al. "A Review of Authorship Identification Techniques for Online Messages." arXiv:1401.6118v1 (2013). — Early survey of authorship attribution techniques, applicable foundations for code stylometry.
5. Authentic8. "How to use GitHub for OSINT." (2025). — Practical GitHub investigation methodology including advanced search filters, developer network mapping, secret detection.
6. OSINT-UI. "GitHub OSINT — Profiles, repos & emails." (2025). — Tool for investigating developer public activity and exposed commit emails.
7. nil0x42. "Awesome GitHub OSINT." Gist (2023). — Curated list of GitHub OSINT tools including Gitrob, GitDorker, TruffleHog.
8. GitHub Docs. "Investigation tools for security incidents." — Official GitHub tools for audit log, security event analysis.
9. GH Archive. "GitHub Event Stream on BigQuery." — Public dataset of all public GitHub events since 2011.
10. SourceCred. "Algorithmic cred scoring for open source projects." — Cred-based contributor influence scoring using PageRank on contribution graph.

---

**Last updated:** 2026-07-25 (deepened)
