# Phone Number Investigation for OSINT Identity Resolution

**Status: STABLE**
**Created: 2026-07-04 | Deepened: 2026-07-04**
**Tags: OSINT, entity-resolution, identity-investigation, telecommunications, probabilistic-linkage**
**Related: [[phone-number-osint]] (practical tools & workflows), [[dns-whois-investigation-osint]], [[email-header-analysis]], [[data-breach-analysis-identity-linkage]], [[reverse-image-search-osint]], [[social-media-osint]], [[financial-intelligence-entity-resolution]]**

## Summary

Phone numbers are unique, persistent identifiers that bridge telecommunications infrastructure with personal identity. While the companion page [[phone-number-osint]] covers practical OSINT tools and investigation workflows (carrier lookup, Truecaller, PhoneInfoga, burner detection), this page focuses on the **entity resolution methodology** — the algorithmic and probabilistic frameworks for linking phone numbers to identities across heterogeneous data sources. The core insight: phone numbers function as quasi-unique keys in entity resolution pipelines, enabling cross-source record linkage, identity graph construction, and probabilistic identity inference. Understanding these methodologies transforms phone numbers from isolated lookup queries into systematic identity resolution building blocks.

---

## 1. Phone Number as Entity Resolution Keys

### 1.1 Structural Properties

Phone numbers possess three properties that make them powerful entity resolution attributes:

| Property | OSINT Implication |
|----------|-------------------|
| **Uniqueness** | A phone number maps to at most one subscriber at a time — unlike names, which are highly ambiguous |
| **Persistence** | Users retain numbers across services, creating cross-platform linkage opportunities |
| **Discoverability** | Numbers surface in breach databases, public records, business registries, and social graphs |

These properties mirror database key attributes: phone numbers act as natural keys that can resolve entity identity across disconnected data silos. However, complications arise: number recycling (carriers reassign disconnected numbers after 45–90 days), number portability (LNP breaks geographic assumptions), and virtual numbers (VoIP/burner numbers create deliberate anonymity). These complications are analogous to entity resolution challenges with temporal decay, attribute migration, and deliberate obfuscation.

### 1.2 Number Formatting for Matching

Phone number matching in entity resolution requires canonical formatting:

- **E.164 normalization:** `+[country_code][national_number]` (e.g., `+12025550123`)
- **National significant number extraction:** Remove country code and any formatting for domestic matching
- **Fuzzy matching variants:** Handle common typos (transposed digits, single-digit errors), regional formatting variations (dashes, parentheses, spaces), and country code omission

For probabilistic linkage, generate multiple candidate formats:
```
+12025550123
2025550123
(202) 555-0123
202-555-0123
12025550123
```

---

## 2. Entity Resolution Methodology for Phone Numbers

### 2.1 The Fellegi-Sunter Model Applied

The Fellegi-Sunter (1969) probabilistic record linkage framework is the mathematical foundation for phone-based identity resolution. The model treats phone number matching as a classification problem: given two records A and B, decide whether they refer to the same entity based on agreement patterns across multiple attributes.

**Model formulation:**
- <latex>\gamma_i \in 0,1\}</latex> — comparison vector for attribute i (1 = match, 0 = non-match)
- <latex>m_i = P(\gamma_i=1 | \text{match})</latex> — probability attribute i agrees given true match
- <latex>u_i = P(\gamma_i=1 | \text{non-match})</latex> — probability attribute i agrees by chance
- Composite weight: <latex>w_i = \log_2(m_i/u_i)</latex> (match weight) or <latex>\log_2((1-m_i)/(1-u_i))</latex> (non-match weight)
- Total score: <latex>S = \sum w_i</latex> compared to upper/lower thresholds

**Phone-specific parameterization:**
| Attribute | m_i (typical) | u_i (typical) | Weight (bits) |
|-----------|---------------|---------------|---------------|
| Exact phone match | 0.95 | 0.0001 | ~13.2 |
| Phone prefix match (NPA-NXX) | 0.85 | 0.02 | ~5.4 |
| Carrier match | 0.80 | 0.10 | ~3.0 |
| Line type match | 0.90 | 0.33 | ~1.5 |
| Registration date ±30d | 0.60 | 0.05 | ~3.6 |

A phone number exact match contributes an exceptionally high weight (~13 bits), making it one of the strongest single attributes in entity resolution — comparable to SSN or passport number. This is why phone-based pivots are so powerful in OSINT investigations.

### 2.2 Blocking Strategies

For large-scale entity resolution (millions of records), comparing all pairs is infeasible (<latex>O(n^2)</latex>). Blocking reduces the comparison space by grouping records likely to match:

- **Phone number blocking:** Use NPA-NXX or first 7 digits as blocking key. Captures family plans, business lines, and geographic clusters.
- **Hashing:** Phonetic hash of associated name + phone prefix. Reduces false negatives from minor formatting differences.
- **Approximate nearest neighbor (ANN) blocking:** Use BlockingPy (Strojny & Beręsewicz, 2025) to embed phone numbers and attributes for vector-space blocking, tolerating errors.

### 2.3 Probabilistic Linkage Implementations

| Tool | Approach | Phone Suitability |
|------|----------|-------------------|
| **Splink** (Fellegi-Sunter via Expectation-Maximization) | Probabilistic; trainable m/u parameters | Excellent — handles E.164 normalization, fuzzy matching, temporal decay |
| **GoldenMatch** | Zero-config; fuzzy + exact + probabilistic + LLM | Good — automatic threshold calibration |
| **Dedupe** (active learning) | SVM with active learning | Moderate — requires labeled training data for phone-specific patterns |
| **Zingg** | Ensemble: rules + probabilistic + neural | Good — handles multi-lingual name+phone matching |

### 2.4 Identity Fusion Graph Construction

Phone numbers are anchors in identity fusion graphs — knowledge graphs where nodes are entity attributes (names, emails, addresses, usernames, device IDs) and edges represent co-occurrence or probabilistic linkage:

```
Phone: +12025550123
  ├─ edges: [name: "John Smith"] (Truecaller, weight: 0.7)
  ├─ edges: [email: jsmith@domain.com] (breach DB, weight: 0.9)
  ├─ edges: [address: 123 Main St] (public record, weight: 0.65)
  └─ edges: [username: jsmith92] (social media, weight: 0.5)
```

Graph-based entity resolution propagates identity confidence through the graph using algorithms like Personalized PageRank or loopy belief propagation. A phone number with high centrality (many connections) becomes a high-confidence anchor node.

---

## 3. Cross-Domain Connections

Phone numbers connect to multiple OSINT domains, each providing additional identity signals:

| Domain | Connection | Wiki Page |
|--------|-----------|-----------|
| **DNS & WHOIS** | Phone numbers in domain registration records, historical WHOIS | [[dns-whois-investigation-osint]] |
| **Email Header Analysis** | Phone numbers in email signatures, recovery phone, mail headers | [[email-header-analysis]] |
| **Data Breach Analysis** | Credential reuse patterns, phone→email→identity linkage | [[data-breach-analysis-identity-linkage]] |
| **Reverse Image Search** | Profile images from messaging apps linked to phone numbers | [[reverse-image-search-osint]] |
| **Social Media OSINT** | Account discovery via phone number, cross-platform correlation | [[social-media-osint]] |
| **Financial Intelligence** | SARs, CTRs, UPI-based phone lookup (India), payment network linkage | [[financial-intelligence-entity-resolution]] |
| **Public Records** | Property records, court filings, voter registration with phone data | [[public-records-databases-osint]] |
| **Business Registries** | Corporate filings listing phone contacts | [[corporate-registry-analysis-entity-resolution]] |
| **Geolocation OSINT** | HLR roaming data, carrier-to-location inference | [[geolocation-osint]] |
| **Metadata Analysis** | EXIF GPS + phone make/model correlation | [[metadata-analysis-osint]] |
| **Cryptocurrency Tracing** | Exchange KYC phone verification, P2P platform phone linkage | [[cryptocurrency-onchain-analysis-osint]] |
| **Network Analysis** | Contact graph construction, call detail record pattern analysis | [[network-analysis-techniques-osint]] |
| **Dark Web OSINT** | Phone numbers in marketplace listings, forum posts | [[dark-web-osint-investigation]] |
| **Influence Operations** | Phone numbers used in coordinated inauthentic behavior accounts | [[influence-operations-detection-countermeasures]] |
| **Counterintelligence** | Deception detection in phone-based social engineering attempts | [[counterintelligence-analysis-frameworks]] |

### 3.1 Structural Isomorphism

Phone-based entity resolution is structurally isomorphic to:

- **Email-based identity resolution:** Both use unique-string identifiers with persistence, both benefit from breach correlation, both have temporal decay (email abandonment, number recycling).
- **Cryptocurrency address clustering:** Both involve quasi-anonymous identifiers that leak identity through reuse patterns.
- **Domain WHOIS investigation:** Both rely on registration metadata, temporal analysis, and cross-referencing with other identity attributes.
- **Cross-platform identity correlation:** The methodology of attribute agreement weighting generalizes across any identifier type.

---

## 4. Tools Integration

For practical phone number OSINT tooling (carrier lookups, reverse phone services, PhoneInfoga, Truecaller, messaging app detection), see [[phone-number-osint]]. This section focuses on entity-resolution-specific tools that integrate phone numbers into broader identity pipelines.

### 4.1 Entity Resolution Frameworks
- **Splink** — Probabilistic linkage with phone-specific comparison levels (E.164 normalization, fuzzy matching)
- **GoldenMatch** — Zero-config entity resolution with phone attribute weighting
- **BlockingPy** — ANN-based blocking for large-scale phone number matching
- **Dedupe** — Active learning for phone-inclusive entity resolution
- **Zingg** — Ensemble entity resolution with multi-lingual phone handling

### 4.2 Knowledge Graph Construction
- **Neo4j** — Graph database for phone-centered identity graphs (Cypher: `MATCH (p:Phone {number: '+12025550123'})-[r]-(n) RETURN p, r, n`)
- **NetworkX** — Python graph library for smaller-scale phone contact networks
- **Graphiti** — Temporal knowledge graphs with phone number entity resolution

### 4.3 API Services
- **Twilio Lookup API** — Carrier, line type, and CNAM for US/international numbers
- **NumVerify** — Real-time validation with carrier and region
- **HLR-Lookups.com** — SS7 HLR querying (legitimate use required)

---

## 5. Legal & Ethical Boundaries

### 5.1 Jurisdictional Frameworks

| Jurisdiction | Key Law | OSINT Implication |
|-------------|---------|-------------------|
| **United States** | TCPA, CFAA, state privacy laws | Automated lookup may violate CFAA if accessing carrier databases without authorization; passive public-record search is generally legal |
| **European Union** | GDPR, ePrivacy Directive | Phone numbers are personal data; processing requires lawful basis; automated API querying may need documented legitimate interest |
| **India** | DPDP Act 2023, TRAI regulations | UPI-based lookup is public feature but mass scraping triggers penalties |
| **China** | PIPL, Cybersecurity Law | Processing requires consent or statutory permission; carrier database queries in legal gray zones |

### 5.2 Operational Rules
- **Passive techniques** (Google dorking, Truecaller search, public breach data lookup) are universally lower-risk than **active techniques** (HLR querying, SMS triggering, automated API enumeration)
- **Document** the legal basis for each technique used in professional investigations
- **Entity resolution of phone numbers** using publicly available information is OSINT; using unauthorized access or phishing is doxing/criminal conduct

---

## 6. References

### Primary Methodology
- Fellegi, I.P. and Sunter, A.B. (1969). "A Theory for Record Linkage." *Journal of the American Statistical Association*, 64(328), pp. 1183–1210.
- Steorts, R.C., Tancredi, A., and Liseo, B. (2018). "Generalized Bayesian Record Linkage and Regression with Exact Error Propagation." arXiv:1810.04808v1.
- Robach, K., van der Pas, S.L., van de Wiel, M.A., and Hof, M.H. (2024). "A Flexible Model for Record Linkage." arXiv:2407.06835v3. (FlexRL R package)
- Strojny, T. and Beręsewicz, M. (2025). "BlockingPy: approximate nearest neighbours for blocking of records for entity resolution." arXiv:2504.04266v4.

### Phone-Specific OSINT
- State of Surveillance. (2025). "Phone Number OSINT: From Digits to Identity (Complete Guide)." stateofsurveillance.org
- OSINT Industries. (2025). "OSINT Phone Number Investigations: How to Use Phone OSINT Tools." osint.industries
- CavemenTech. (2025). "How to Find a Phone Number's Owner: The Ultimate OSINT Guide."
- Lampyre. (2025). "OSINT Phone Number Investigations: A Comprehensive Guide."

### Entity Resolution Tools
- Splink (GitHub): moj-analytical-services/splink — Probabilistic linkage library
- GoldenMatch (GitHub): benseverndev-oss/goldenmatch — Zero-config entity resolution
- BlockingPy (GitHub): blockingpy — ANN-based blocking
- Dedupe (GitHub): dedupeio/dedupe — Active learning entity resolution
- Zingg (GitHub): zinggAI/zingg — Ensemble entity resolution

### Telecommunications Standards
- ITU-T Recommendation E.164: The International Public Telecommunication Numbering Plan
- GSMA guidelines for signaling security and location data access
- North American Numbering Plan Administration (NANPA) — area code and carrier lookup data

---

*Deepened from scaffold (83 lines) to 256 lines. Focus: entity resolution methodology, probabilistic linkage, identity graph construction, cross-domain mapping, and integration with practical tools page [[phone-number-osint]].*
