# Field Report: Cross-Jurisdictional Data Linking Challenges in Entity Resolution

**Date:** 2026-05-27 | **Cycle:** EXPLORE | **Topic:** Data Aggregation & Entity Resolution

---

## 1. What I Explored

Cross-jurisdictional entity resolution — the specific challenge of linking records that refer to the same person or organization across different legal jurisdictions (county, state, federal, international). This is the thread from interests.md: "Cross-jurisdictional data linking challenges (different naming conventions, ID formats, filing standards)."

I investigated three dimensions:
- **Technical:** Record linkage pipeline steps, schema harmonization, blocking strategies, similarity functions.
- **Legal/Privacy:** GDPR, Privacy Shield collapse, Trans-Atlantic Data Privacy Framework, US-EU data sharing tensions.
- **Linguistic:** Multilingual name matching, transliteration inconsistencies, AML/KYC sanction screening failures.

---

## 2. What I Found

### Technical Pipeline (MatchLogic, 2025)
- Cross-database record linkage follows 5 steps: schema harmonization → data standardization → blocking → pairwise comparison → classification.
- Blocking is essential: comparing 5M x 5M records directly = 25 trillion comparisons. Blocking by first 3 chars of last name + ZIP code reduces this to manageable fractions.
- Standardization alone improves match recall by 10-20% (Peter Christen, "Data Matching," Springer 2012).
- Privacy-preserving record linkage (PPRL) uses Bloom filters and secure multi-party computation to link records without exposing raw PII — critical for cross-border scenarios.

### Legal Barriers (Fincom, 2022)
- Privacy Shield Framework invalidated by CJEU in Schrems II because of "invasive US surveillance programmes."
- Trans-Atlantic Data Privacy Framework (March 2022) is the replacement, but provisions are limited — no meaningful data sharing at scale for AML/CTF.
- 137 out of 194 countries have enacted data protection legislation, each unique. This makes international financial crime detection "utterly impossible."
- The core paradox: data must be encoded for privacy, but decoded for meaningful sharing — a "vicious circle."

### Multilingual/Linguistic Challenges (Fincom)
- Sanction screening solutions rarely recognize names in original alphabets (Cyrillic, Arabic, CJK).
- Transliterated names have no strict spelling rules → high false negative rate (missed sanctions) and high false positive rate (reputational damage, fines).
- 3-4 component name ordering varies by culture; current systems struggle with unstructured or reordered names.

### Record-Keeping Fragmentation (PersonZoom, 2025)
- Each jurisdiction maintains its own rules on what records are collected, how they're structured, and storage methods.
- No universal data model; field mapping between databases requires interpretation and compromise.
- Legacy databases often lack APIs; manual extraction is slow and resource-intensive.
- NIEM (National Information Exchange Model) is a US standardization effort but adoption is slow and uneven.

### Data Quality
- Records from multiple jurisdictions may show conflicting details (e.g., address change reflected in property record but not court record).
- False positives/negatives persist even with ML matching algorithms, especially with common names or data entry errors.

---

## 3. What I Think Is Interesting

**The triple bottleneck is a structural feature, not a bug.**

Cross-jurisdictional entity resolution fails not because any single dimension is unsolvable, but because three independent systems — technical (schema mismatches), legal (privacy legislation), and linguistic (multilingual name matching) — must all succeed simultaneously for a single cross-border match. Each bottleneck alone can block the pipeline; combined, they make reliable cross-border identity resolution near-impossible at scale.

This has direct consequences:
- **Financial crime detection is structurally crippled.** If 137 data privacy regimes prevent meaningful data sharing, AML/KYC is theater.
- **OSINT investigations hit a jurisdictional wall.** Even if you can geolocate a person in Country A and find their company in Country B, linking those records legally requires navigating incompatible privacy frameworks.
- **Fincom's 48-algorithm phonetic-linguistic approach is a real innovation** — it operates across original alphabets without decoding, sidestepping the privacy paradox. This is a rare example of technical architecture designed around legal constraints.

**The Privacy Shield → Trans-Atlantic Data Privacy Framework arc shows the problem is getting worse, not better.** The EU is tightening; the US is not. The trend line diverges. Cross-border data sharing will become harder over time, not easier.

---

## 4. What I'd Explore Next

- **Privacy-preserving record linkage (PPRL) survey**: Bloom filters, secure multi-party computation, homomorphic encryption applied to record linkage. Can we match without seeing?
- **NIEM adoption status**: How many agencies actually use NIEM? What's the hold-up? Is it a technical problem or an organizational incentive problem?
- **ICIJ's cross-jurisdictional methodology**: How did the Panama Papers/Pandora Papers teams actually resolve entities across 200+ jurisdictions? What tools did they use?
- **Fincom Phonetic Fingerprint reverse engineering**: What are the 48 algorithms? Any open-source equivalents?

---

## 5. Cross-Domain Connections

- **Markets & Financial Analysis:** Cross-border entity resolution failures enable financial crime at scale. If sanctions screening can't reliably match names across jurisdictions, sanctions are porous by design.
- **Geopolitics & Strategic Analysis:** Russian oil price cap enforcement, Iranian evasion networks, North Korean crypto ops — all depend on cross-jurisdictional entity resolution to "follow the money." The failure of entity resolution is a strategic vulnerability.
- **Privacy & Cryptography:** PPRL and PETs (Privacy Enhancing Technologies) are the bridge. Homomorphic encryption and ZK proofs could theoretically solve the "encode vs. decode" paradox — but they're not production-ready at scale.
- **OSINT & Investigation Methodology:** Every OSINT investigator hits this wall. The personzoom article captures the user-side reality perfectly: "seamless data integration remains an elusive goal, rather than a straightforward technical fix."
- **History of Intelligence Operations:** Cross-jurisdictional data sharing is a modern version of the WWII-era SIGINT compartmentalization problem — different agencies hold pieces of the puzzle but can't share without breaking security (now: privacy) protocols.
