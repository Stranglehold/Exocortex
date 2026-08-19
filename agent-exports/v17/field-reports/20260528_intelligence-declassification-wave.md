# Field Report: Intelligence Declassification Wave 2025-2026 — Historiography, Technology, and Power

**Date:** 2026-05-28
**Cycle:** EXPLORE
**Topic:** History of Intelligence Operations — Declassification Wave and Historiography
**Status:** Complete

---

## 1. What I Explored

This cycle followed a different thread within History of Intelligence Operations than the prior cycle (5/26, which covered SIGINT evolution). The specific angle: the unprecedented 2025-2026 declassification wave — Executive Order 14176 ordering full release of JFK, RFK, and MLK assassination files, the mechanics of mass declassification, and the historiographic question of whether these releases actually change what we know.

Sub-threads investigated:

1. **The JFK files release (March 2025)** — scale, contents, and what historians actually learned
2. **The MLK files release (July 2025)** — 230,000 pages under DNI Tulsi Gabbard
3. **The National Declassification Center (NDC) pipeline** — what the routine declassification apparatus looks like (Q2 2026: 58 entries from Jan-Mar 2026)
4. **AI-assisted declassification** — the emerging technology thread connecting this to the AI Architecture and OSINT interests
5. **The historiographic question** — when 95,000 pages drop at once, does history change or just get noisier?

---

## 2. What I Found

### 2.1 The JFK Files: Scale Without Revelation

The March 2025 release was the largest single declassification event in JFK assassination history:

| Release Wave | Pages | PDF Files | Date |
|-------------|-------|-----------|------|
| Wave 1 | 31,419 | 1,123 | March 18, 7 PM EST |
| Wave 2 | 37,127 | 1,062 | March 18, 10:30 PM EST |
| Wave 3 | 14,318 | 161 | March 20, 9:30 PM EST |
| Wave 4 | 53 | 16 | March 26, 3:30 PM EST |
| Wave 5 | 704 | 207 | April 3, 7:00 PM EST |
| Wave 6 | 11,022 | 140 | January 30, 2026 |
| **Total** | **~94,643** | **2,709** | |

**What was actually new:**

- **The Nikonov/Oswald file:** A 1991 U.S. intelligence teletype reporting that KGB official "Slava" Nikonov reviewed five thick KGB files on Oswald and concluded: Oswald was never a KGB agent, he "doubted anyone could control Oswald," Oswald had a "stormy relationship with his Soviet wife," and the KGB files "reflected that Oswald was a poor shot when he tried target firing in the USSR."
- **CIA Mexico City Station records:** A 77,000-page tranche distributed to researchers in 2025 contained CIA Mexico City Station records, internal memos, and document indices that "materially sharpen what historians can say the Agency knew about Lee Harvey Oswald's late-September 1963 visit to Mexico City" (per Factually.co analysis).
- **Cold War context documents:** DOD documents from 1963 covering U.S. involvement in Latin America and assessments that Castro would not escalate to "seriously and immediately endanger the Castro regime."

**What did NOT change:**

The fundamental findings of the Warren Commission (1964) and HSCA (1979) — Lee Harvey Oswald acted alone — remain unchallenged. As James Johnston (author of "Murder, Inc.: The CIA Under John F. Kennedy" and former Church Committee staffer) noted: agencies had already turned over virtually everything to NARA by 1988. "If it was going to embarrass the agency or tell a different story, they wouldn't have turned them over to the National Archives in the first place."

**The Johnson-McCone file — what's still missing:**

Johnston identified one known-but-unreleased document: the transcript of the first one-on-one conversation between President Lyndon Johnson and CIA Director John McCone after Johnson took office following Kennedy's death. This remains withheld.

### 2.2 The MLK Files: 230,000 Pages in One Day

On July 21, 2025, DNI Tulsi Gabbard — in partnership with DOJ, FBI, CIA, and NARA — released over 230,000 pages of documents related to the assassination of Dr. Martin Luther King, Jr. This was the single largest bulk declassification in U.S. intelligence history. Unlike the JFK release (which began with a 1992 law mandating eventual release), the MLK files had no comparable statutory framework — this was purely executive action under EO 14176.

The MLK release received significantly less media and historiographic attention than the JFK files, for several reasons:
- The JFK assassination has a more established conspiracy-theory ecosystem that amplifies interest
- The MLK files lacked a comparable "Assassination Records Review Board" infrastructure for organizing and indexing
- The sheer volume (230K pages vs. ~95K for JFK) made assessment impossible for most researchers without substantial institutional resources

### 2.3 The Routine Declassification Machine: NDC Q2 2026

Beyond the high-profile executive releases, the National Declassification Center continues routine processing under Executive Order 13526's 25-year rule. The Q2 2026 release list (58 entries, January-March 2026 processing window) includes:

- **Textual materials** from military and civilian agencies
- **Moving images** — declassified film and video footage
- **Photographic negatives** — Cold War and post-Cold War imagery
- Agency sources spanning State Department, DOD, CIA, and other national security agencies

This is the unglamorous workhorse of declassification: records hitting the 25-year threshold automatically triggering review, with NDC processing them in quarterly batches. The scale is important: 58 entries in one quarter doesn't sound like much, but each "entry" can represent boxes of material. The systemic problem is that the backlog at current processing rates takes decades to clear.

### 2.4 The Technological Convergence: AI-Assisted Declassification

The declassification pipeline has a fundamental bottleneck: human reviewers must manually assess every document for classification markings, national security sensitivity, privacy information, and FOIA exemptions. At the current backlog rate, materials that should be automatically declassified under the 25-year rule are delayed by years or decades.

**AI-assisted declassification initiatives are emerging as the key technological intervention:**

1. **Automated classification marking detection:** ML models trained to identify classification headers, portion markings, and declassification instructions in document images — replacing manual page-by-page review
2. **Personal identification information (PII) detection:** Computer vision and NLP systems that flag Social Security numbers, names of living individuals, and other PII for redaction — directly relevant to the JFK release where NARA had to warn affected living individuals
3. **Sensitivity classification:** NLP models that assess document content against classification guides to determine whether modern sensitivity standards still apply to 25-50+ year-old documents
4. **Entity resolution for redaction:** Systems that identify which named individuals are still living, requiring continued protection, vs. deceased, allowing release

**Cross-domain connection to Exocortex:** The entity resolution problem in declassification — "is this named person still alive, and if so, does their identity need protection?" — is structurally identical to the entity resolution problems in investigative OSINT. The same graph-based approaches, the same privacy/transparency tension, the same need for verifiable reasoning chains rather than black-box decisions.

**Cross-domain connection to AI Architecture:** The declassification pipeline is an extreme case of the "human in the loop" AI architecture problem. AI can classify 95% of documents correctly, but the 5% error rate on national security materials is intolerable. This forces a tiered review architecture: AI pre-screens, human reviews AI-flagged borderline cases, human spot-checks AI-cleared cases — the same architecture pattern as Exocortex's epistemic integrity extension + supervisor loop.

### 2.5 The Historiographic Question: Does Mass Declassification Change History?

The JFK release is a case study in the limits of transparency as a historical tool:

**What mass declassification achieves:**
- Fills in granular details (Oswald's KGB file contents, CIA Mexico City internal communications)
- Provides primary source material for specialized historians
- Validates or refutes specific narrow claims

**What mass declassification does NOT achieve:**
- Change the consensus historical narrative (the lone gunman conclusion stands)
- Produce "smoking gun" documents that rewrite history — agencies that wanted to hide something likely didn't transfer those records to NARA
- Enable rapid public understanding — 95,000 pages dropped on one day means the public relies on journalists and historians to digest it, creating a secondary bottleneck

**The deeper structural problem:** The declassification system is designed for "transparency through volume" — release everything, let researchers sort it out — rather than "transparency through intelligibility" — release curated, organized, searchable, contextualized information. This is an information retrieval problem that maps directly to the OSINT investigation methodology challenges: how do you find signal in a document corpus that's too large for any one person to read?

---

## 3. What I Think Is Interesting

**The declassification wave is an intelligence operation in reverse.** Classification is the active concealment of information to shape adversary perceptions. Declassification — especially mass executive declassification — is also an active perception-shaping operation. Trump's EO 14176 was politically motivated (fulfilling a campaign promise to transparency advocates, including RFK Jr.), and the release timing and structure reflected that. The "transparency" narrative masks the reality that the executive branch controls both what's classified AND what's declassified — the same actors control both sides of the information gate.

**The historiographic asymmetry is structural, not incidental.** The JFK files got massive attention (every major news outlet, instant analysis). The MLK files — arguably more historically significant as primary source material on FBI surveillance of the civil rights movement — got comparatively little. Why? Because there's no MLK conspiracy-theory industrial complex to generate sustained attention. The market for historical truth is shaped by entertainment value as much as scholarly value.

**AI declassification creates a new attack surface for historical manipulation.** If AI models do the first-pass review of documents for declassification, whoever trains those models controls what gets flagged for human review and what gets auto-cleared. A model trained to be lenient on certain agencies or time periods could systematically suppress documents without any human making a deliberate decision to withhold. This is the automation bias problem from the SIGINT domain, applied to history itself.

**The National Declassification Center's quarterly lists are a quiet but important transparency mechanism.** The Q2 2026 list of 58 entries is more meaningful for historical research than the JFK spectacle — these are the routine releases that build the archival record. But almost nobody reads the NDC release lists. The OSINT lesson: the most valuable intelligence is often in the boring, routine, unglamorous sources that nobody pays attention to because there's no narrative hook.

---

## 4. What I'd Explore Next

1. **The MLK files deep dive:** What's actually in the 230,000 pages? Historians have had 10 months to analyze. What patterns of FBI surveillance, COINTELPRO documentation, and Hoover-era operations have emerged?
2. **The AI declassification vendors:** Who's building these systems? What's the procurement landscape? The NARA/Agency contracts for AI-assisted review would be FOIA-able.
3. **Comparative declassification:** How does the U.S. system compare to the UK's 30-year rule, France's 50-year rule, or Russia's selective "declassification" (which is often propaganda)?
4. **The Johnson-McCone transcript:** Has anyone filed FOIA litigation to compel release of this specific known-withheld document? What's the legal justification for continued withholding 62+ years later?
5. **RFK files status:** EO 14176 also covered RFK assassination files. Where are those in the release pipeline? Less media attention than JFK or MLK.

---

## 5. Cross-Domain Connections

| Domain | Connection |
|--------|-----------|
| **OSINT & Investigation Methodology** | The declassification document-sorting problem (signal in 230K pages) is identical to OSINT corpus analysis. Same entity resolution, same deduplication, same timeline reconstruction techniques. |
| **AI Agent Architecture** | AI-assisted declassification uses the same human-in-the-loop tiered-review architecture as Exocortex epistemic integrity. Failure modes (automation bias, training data poisoning, algorithmic surprise) are shared. |
| **Markets & Financial Analysis** | There's a market for declassification: FOIA requesters, commercial background check services, investigative journalists, and historical researchers form a demand side. The supply side (NARA's processing capacity) is a production function with measurable throughput. This is an information market. |
| **Geopolitics & Strategic Analysis** | Classification/declassification is an instrument of state power. Controlling historical narrative shapes national identity and legitimizes current policy. The Trump EO 14176 release was a political act, not a purely archival one. |
| **Privacy & Cryptography** | The PII problem in declassification mirrors the broader privacy/transparency tension in OSINT. How do you release historically significant information while protecting living individuals? The JFK release's warning to affected individuals ("contact NARA if you're named") is a fascinating practical solution. |
| **Data Aggregation & Entity Resolution** | Entity resolution for "is this named person still alive?" in declassification maps to the same graph-based identity resolution techniques used in investigative OSINT. |

---

## References

1. National Archives, "JFK Assassination Records — 2025 Documents Release," March 2025. https://www.archives.gov/research/jfk/release-2025
2. USA Today, "Trump releases classified JFK files on assassination. Here's what they say," Josh Meyer, March 18, 2025.
3. ABC News, "JFK files key takeaways: What we learned and didn't," March 2025.
4. BBC News, "'Exciting' but no bombshells: four key JFK files takeaways," March 2025.
5. ODNI Press Release No. 16-25, "DNI Gabbard, in Partnership with DOJ, FBI, CIA, and NARA, Release MLK Jr. Assassination Files," July 21, 2025.
6. National Archives, "NDC Release Lists," updated April 23, 2026. https://www.archives.gov/declassification/ndc/release-lists
7. Factually.co, "What specific documents newly released in 2025 change regarding Oswald's Mexico City visit," 2025.
8. Executive Order 14176, "Declassification of Records Concerning the Assassinations of President John F. Kennedy, Senator Robert F. Kennedy, and the Reverend Dr. Martin Luther King, Jr.," January 23, 2025.
9. Executive Order 13526, "Classified National Security Information," December 29, 2009 (governing classification/declassification system).
10. The Black Vault, "Document Archive" — 3,838,797 pages of declassified government documents. https://www.theblackvault.com/documentarchive/
