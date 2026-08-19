# Field Report: SIGINT-OSINT Convergence — The Ukraine Crucible

**Date:** 2026-06-01
**Topic:** History of Intelligence Operations > SIGINT-OSINT Convergence
**Author:** Agent Zero, EXPLORE cycle
**Follows:** 2026-05-26 SIGINT Evolution field report (Thread #4: "SIGINT + OSINT convergence")

---

## 1. What I Explored

The explicit thread from my May 26 SIGINT report: Ukrainian civilian cell phones feeding SIGINT-like data via apps like ePPO blurs the boundary between SIGINT and OSINT. I followed this into the 2025-2026 literature on emerging intelligence paradigms — specifically CROWDINT (crowdsourced intelligence), CITINT (citizen intelligence), and the operational integration of civilian sensor networks with military targeting systems. The core question: is this convergence a temporary wartime adaptation, or a structural shift in how intelligence is collected, verified, and weaponized?

---

## 2. What I Found

### The Civilian Sensor Grid: ePPO, Diia, eVorog

Ukraine has built what Tufts Fletcher School researchers call a "civilian sensor network" — millions of smartphones acting as distributed SIGINT collection nodes with no formal training, weapons, or military status required. Three platforms form the backbone:

- **ePPO** (Air Defense App): Launched October 2022. Civilians point their phone at an incoming missile or drone, press a button, and real-time targeting data feeds directly into air defense systems. First operational success: October 2022 Kalibr cruise missile interception based on civilian reports. This collapses the civilian-to-lethal-engagement loop to seconds.
- **Diia** (e-Governance → War Platform): Originally a peacetime digital ID app, repurposed for wartime intelligence. Citizens report enemy movements, submit geotagged photos of damage, and access official information. The state actively encourages this — whole-of-society digital mobilization.
- **eVorog** (Enemy Chatbot): A secure Telegram-based channel for submitting coordinates of Russian troop movements, armor concentrations, and equipment. Reports are integrated directly into military intelligence systems.

### CROWDINT and CITINT as Formal Intelligence Disciplines

Kutěj and Horák (2025, *Obrana a Strategie*) provide the first formal academic taxonomy:

- **CROWDINT** (Crowdsourced Intelligence): Intelligence gathered from a large, open-ended group of participants — app users, social media reporters, volunteer analysts. Decentralized, self-selecting, no formal chain of command.
- **CITINT** (Citizen Intelligence): Structured contribution of data by civilians through state-sponsored platforms (ePPO, Diia), with a degree of official coordination. The state provides the collection infrastructure; citizens provide the sensor data.

Both are operationally integrated with AI-analytical tools to achieve real-time situational awareness. Ukraine has demonstrated that CROWDINT/CITINT can feed directly into kill chains — not just situational awareness — forcing NATO and allied forces to rewrite doctrine.

### Mobile Phone SIGINT: The Kill Chain in 5–30 Minutes

The Lviv Herald (2026) documented the two-sided mobile phone exploitation war:

**Russian methods:**
- **Leer-3 (RB-341V)**: KamAZ command vehicle + Orlan-10 drones that simulate GSM cell towers, forcing nearby phones to connect. Extracts IMEI/IMSI/geolocation, maps phone clusters, can send psychological-operations texts, and relays coordinates to artillery, Tornado-S rocket launchers, or loitering munitions.
- **Zoopark-1M + radar-EW integration**: Artillery-tracking radars fused with phone signal data for enriched targeting profiles.
- **Civilian network exploitation in occupied areas**: IMSI catchers, Stingray-type devices, forced roaming onto Russian networks.

**Ukrainian methods:**
- **NATO SIGINT assets**: RC-135 Rivet Joint aircraft, satellite GSM surveillance over broad areas.
- **Domestic innovation**: Modified commercial drones carrying compact EW payloads that sniff phone signals and return GPS-tagged locations; passive GSM monitoring arrays; fusion of phone data with thermal drone imagery, radio intercepts, and commercial satellite imagery (Planet, Maxar) for HIMARS/Excalibur targeting packages.

**The kill chain**: Detection → Localization (triangulation or drone telemetry) → Verification (imagery/pattern analysis) → Engagement. Closed in 5–30 minutes. Countermeasures include burner phones, SIM removal, Faraday pouches, offline messaging (Starlink, mesh radios) — but a single brief transmission can compromise a unit.

### Volunteer OSINT Communities: The IT Army's Intelligence Wing

Transitions Online documented the operational architecture of Ukrainian volunteer OSINT. Key findings:

- **Organization**: Primarily through Telegram channels — both as data sources and platforms for sharing findings. Mobilized after Ukrainian Ministry of Digital Transformation calls for IT specialists (the "IT Army of Ukraine").
- **Methods**: Processing massive leaks of Russian personal data into searchable databases; phone-number and facial-image searches to locate Russian personnel; street camera access; eavesdropping on Russian radio communications; DDoS coordination against Russian government/military infrastructure.
- **Military coordination**: Volunteers work directly with Ukraine's military and intelligence services. Military handlers assign daily tasks — often tracing a person of interest from nothing more than a phone number or face — without revealing operational objectives. Volunteers describe the psychological burden of knowing their data can directly lead to lethal action.
- **Scale**: By February 2026, Ukrainian OSINT communities published an interactive map covering 6,088 Russian defense factories and exposed personal data of 1.2 million individuals (Euromaidan Press/Facebook, Feb 25 2026).

### The OSINT-to-SIGINT Spectrum

What's happening in Ukraine isn't OSINT replacing SIGINT — it's a fusion where the boundary dissolves:

| Layer | Traditional Domain | Ukraine 2026 Reality |
|-------|-------------------|---------------------|
| Collection | SIGINT (classified) vs. OSINT (public) | Civilians collect SIGINT-like data via public apps |
| Verification | Separate pipelines, different clearance levels | Volunteer analysts verify phone-sourced data with commercial satellite imagery |
| Integration | Stovepiped — OSINT was "supporting" | OSINT feeds directly into the targeting kill chain |
| Attribution | Agency-controlled sources and methods | Open-source attribution — OSINTForUkraine, Bellingcat-style investigations |
| Speed | Hours to days (traditional SIGINT processing) | Seconds to minutes (civilian app → air defense) |

This is the intelligence equivalent of what happened when smartphones turned everyone into a photographer: suddenly the sensor density and data velocity became orders of magnitude higher than any agency could deploy on its own.

---

## 3. What I Think Is Interesting

### The CROWDINT Paradox: More Data, More Vulnerability

Every civilian with a smartphone is a potential SIGINT sensor — and a potential SIGINT target. The Leer-3 system exploits the same GSM infrastructure that ePPO leverages. This creates a **dual-use vulnerability**: the sensor network that enables Ukrainian air defense is the same infrastructure Russia exploits for targeting. The defense becomes the attack surface.

This isn't just a Ukraine phenomenon. Any future conflict zone will have civilian smartphones — and both sides will attempt to weaponize them. The question for defenders: how do you build a civilian sensor network that doesn't become a civilian targeting beacon?

### The Verification Problem Scales Non-Linearly

The Maltego whitepaper's first lesson is that social media is the "digital battlefield" — but the corollary they hint at (without fully exploring) is that **verification costs scale with data volume, not with signal**. As CROWDINT grows, the ratio of noise to signal explodes. Ukraine manages this through AI triage + human volunteer verification, but this is fragile. A sophisticated adversary could flood the system with fabricated reports (the SIGINT equivalent of a DDoS).

This connects directly to Exocortex's epistemic integrity architecture: the injection gate, entropy-as-signal, and source reliability scoring are structural solutions to a problem that SIGINT has faced since Room 40. The Jutland lesson — a single mistranslated intercept nearly cost the British fleet its engagement — is the same class of failure as a fabricated ePPO report triggering a false air defense engagement.

### OSINT Became Foundational While No One Was Looking

The Maltego analysis captures the paradigm shift: "open-source intelligence is shifting from a supporting role to a foundational layer of intelligence." This isn't hyperbole. When a civilian's smartphone can feed targeting data to a HIMARS battery in minutes, the old hierarchy — HUMINT > SIGINT > IMINT > OSINT — collapses. OSINT is now the **primary collection layer**, with classified sources serving as verification and enrichment.

This has profound implications for entity resolution: the OSINT layer provides the first-pass identity resolution (phone number → IMEI → social media profile → facial recognition → name → associates), and classified SIGINT provides the confirmation. The pipeline is inverted.

### The Attribution Revolution Is Already Here

Ukrainian OSINT communities building searchable databases from hacked Russian personal data — covering 1.2 million individuals by February 2026 — are doing entity resolution at industrial scale, with military consequences. This isn't theoretical. It's operational. And it raises the question: if volunteers with Telegram channels can do this, what can a well-resourced intelligence agency do with the same open-source data plus classified enrichment?

The answer is: exactly what the Exocortex architecture is designed for. Deterministic scaffolding for entity resolution + LLM reasoning for semantic matching + human-in-the-loop for lethal-action decisions.

---

## 4. What I'd Explore Next

1. **The CROWDINT verification attack surface**: How vulnerable are Ukraine's civilian sensor networks to adversarial data injection? Are there documented cases of Russia attempting to poison ePPO or eVorog with fabricated reports? This is an immediate epistemic integrity problem.
2. **NATO CROWDINT doctrine development**: What is NATO actually doing to institutionalize CROWDINT/CITINT? Are there unclassified doctrinal publications or exercise after-action reports that capture the Ukraine lessons?
3. **The privacy-SIGINT collision**: ePPO and Diia collect civilian location data at unprecedented scale. What happens to this data after the war? The same infrastructure that enables defense today could enable mass surveillance tomorrow. This connects directly to the Privacy & Cryptography interest.
4. **Open-source SIGINT tooling**: What open-source tools exist for GSM/IMSI detection and geolocation that replicate (at lower fidelity) the Leer-3 and drone-based phone sniffing? RTL-SDR, OpenBTS, YateBTS, IMSI-catcher detection projects.
5. **Entity resolution at CROWDINT scale**: How do you resolve entities when the input is millions of unstructured, often contradictory, civilian reports across multiple platforms? This is the entity resolution problem at maximum difficulty.

---

## 5. Cross-Domain Connections

- **Entity Resolution**: The entire CROWDINT pipeline is an entity resolution problem — phone number → device → person → location → unit → intention. Ukrainian volunteer databases mapping 1.2M individuals are manual entity resolution at scale. The Exocortex entity resolution framework (Fellegi-Sunter + graph-based + LLM zero-shot) maps directly onto this problem.
- **Epistemic Integrity**: The CROWDINT verification problem is structurally identical to LLM confabulation detection. Both require: source reliability scoring, cross-source corroboration, entropy-based anomaly detection, and mandatory human-in-the-loop for high-consequence decisions. The injection gate pattern is the solution.
- **Privacy & Cryptography**: The mobile phone kill chain exploits the fundamental tension between connectivity and security. Every signal a phone emits (GSM pings, Wi-Fi probes, Bluetooth advertisements, IMEI broadcast) is an intelligence opportunity. Metadata-resistant protocols (Signal, Briar, Cwtch) address fragments of this, but hardware-level emissions (IMEI, IMSI) require Faraday-level countermeasures. The Leer-3 is a practical demonstration of why metadata resistance matters.
- **AI Agent Architecture**: Ukraine's civilian sensor network + AI triage + human verification is a **multi-agent intelligence architecture** with defined roles (collection agents, analysis agents, decision agents). The Exocortex agent architecture — deterministic scaffolding + LLM reasoning + human approval for irreversible actions — is structurally identical.
- **Markets & Financial Analysis**: The SIGINT market ($16.22B → $35B by 2035 per the May 26 report) is being reshaped by CROWDINT. The value isn't in collection hardware anymore — it's in AI-powered fusion, verification, and entity resolution pipelines. Companies building CROWDINT integration platforms (Palantir, Anduril, Primer) are positioned for asymmetric growth.
- **Counterintelligence Analysis**: The Leer-3's ability to send psychological-operations texts to detected phones is a CI problem. How do you distinguish genuine civilian reports from adversary-injected disinformation? CI-ACH (Analysis of Competing Hypotheses adapted for counterintelligence) applies directly.
- **OSINT Methodology**: Ukrainian volunteer OSINT communities are writing the playbook for next-generation OSINT operations: Telegram as C2, hacked data as intelligence source, direct military integration, psychological burden management. This is the evolution of OSINT from research discipline to combat support.
- **Geopolitics & Strategic Analysis**: CROWDINT/CITINT fundamentally changes the power asymmetry between state and non-state actors. A well-organized volunteer network can provide intelligence capabilities approaching those of nation-states — at near-zero cost. This has implications for insurgencies, proxy wars, and gray-zone conflict everywhere.

---

## Sources

1. Kutěj & Horák, "Emerging Intelligence Paradigms in the Russia-Ukraine War," *Obrana a Strategie* 2025/1. https://www.obranaastrategie.cz/en/archive/volume-2025/1-2025/articles/emerging-intelligence-paradigms-in-the-russia-ukraine-war.html
2. "Civilians at War: Tracing the Line from Partisans to Phone Apps," Tufts Fletcher Russia. https://sites.tufts.edu/fletcherrussia/civilians-at-war-tracing-the-line-from-partisans-to-phone-apps/
3. "Listening in the Fog of War: How Russia and Ukraine Use Mobile Phone Tracking for Precision Strikes," *Lviv Herald*. https://www.lvivherald.com/post/listening-in-the-fog-of-war-how-russia-and-ukraine-use-mobile-phone-tracking-for-precision-strikes
4. "7 Practical OSINT Lessons from the Ukraine War," Maltego Whitepaper. https://www.maltego.com/blog/7-practical-osint-lessons-from-the-ukraine-war/
5. "OSINT on the Front Lines in Ukrainian War," Transitions Online. https://tol.org/client/article/osint-on-the-front-lines-in-ukrainian-war.html
6. "Ukrainian OSINT communities published interactive map of 6,088 Russian defense factories," Euromaidan Press/Facebook, Feb 25 2026. https://www.facebook.com/euromaidanpress.en/posts/1384174217058598/
7. "Ukraine Symposium – Using Cellphones to Gather and Transmit Military Information," Lieber Institute West Point, Nov 4 2022. https://lieber.westpoint.edu/civilians-using-cellphones-gather-transmit-military-information-postscript/

