# Field Report — Electric Utility & Critical Infrastructure
**Date:** 2026-05-15
**Agent:** Agent Zero (EXPLORE cycle)
**Interest:** Electric Utility & Critical Infrastructure
**Origin:** Jake's professional domain (field engineer, substations, SCADA, protection relays)

---

## 1. What I Explored

I followed five threads from the interests registry:

1. **SCADA/ICS vulnerability landscape** — current CISA ICS-CERT advisories, threat actors targeting electric utilities, and the shifting OT threat landscape
2. **Dragos 2026 OT Cybersecurity Year in Review** — the latest industry report documenting how adversaries are evolving their tactics against industrial infrastructure
3. **IEC 61850 GOOSE messaging security** — active research on vulnerabilities in substation automation protocols and ML-based anomaly detection as a defense
4. **Grid modernization funding (DOE GRIP)** — the federal funding mechanism for resilience and grid innovation partnerships
5. **DER integration challenges** — IEEE 1547 evolution and hosting capacity analysis for distributed energy resources

---

## 2. What I Found

### 2.1 SCADA/ICS Vulnerability Landscape

CISA continues to issue a high volume of ICS advisories. In a single release on December 18, 2025, CISA published **nine ICS advisories** covering vulnerabilities in products from Siemens, Schneider Electric, Rockwell, Mitsubishi Electric, Delta Electronics, GE Vernova, and Hitachi Energy. A comprehensive review by SocRadar estimates that **hundreds of vulnerabilities were disclosed across 200+ vendors and 700+ products** during 2024-2025, many sitting inside critical manufacturing lines, substations, control rooms, and industrial networks.

A February 2026 CISA advisory (AA26-097A) detailed Iranian-affiliated cyber actors (CyberAv3ngers, linked to IRGC) exploiting PLCs across US critical infrastructure. This is a continuation of the pattern first documented in late 2023 but now with more sophisticated targeting.

**Key takeaway:** The advisory volume isn't just noise — it represents real exploitation. The surge from 2024-2025 signals a fundamental shift: adversaries are no longer treating OT as a curiosity but as a primary target.

### 2.2 Dragos 2026 OT/ICS Cybersecurity Year in Review

The Dragos 2026 report (9th annual, released February 2026) documents a **fundamental shift in how threat actors approach industrial environments**:

- **KAMACITE** systematically mapped control loops across US infrastructure throughout 2025
- **ELECTRUM** targeted distributed energy systems in Poland with deliberate attempts to affect operational assets
- Three new threat groups were identified targeting critical infrastructure globally

Crucially, the report challenges the traditional assumption that "meaningful disruption requires direct access to control systems such as protection relays, PLCs, or substation automation." Electric utilities have long operated under this assumption — Dragos 2026 says the grid is **not as insulated from disruption as traditional security models assumed.**

The report's title says it directly: **"Adversaries Increase Real-World Impact, Map Control Loops Across Industrial Infrastructure."** This isn't reconnaissance theater — it's operational mapping for potential physical effects.

### 2.3 IEC 61850 GOOSE Messaging Security

The GOOSE protocol (Generic Object Oriented Substation Event) is the backbone of modern substation automation, enabling high-speed communication between protection relays, circuit breakers, and merge units. Research paints a concerning picture:

**Vulnerability landscape:**
- GOOSE messages lack built-in authentication by default — they rely on VLAN segmentation and the assumption of a physically isolated network
- Multiple published attacks demonstrate GOOSE message spoofing, replay attacks, and flooding-based DoS that can suppress legitimate protection signals
- IEC 62351 (the companion security standard) addresses these with TLS for MMS, message authentication for GOOSE/SV, and role-based access control — but adoption is inconsistent

**Defensive research (2025-2026):**
- A January 2026 *Scientific Reports* paper proposed optimal feature sets for ML-based anomaly detection on GOOSE traffic, achieving **100% accuracy** using autoencoders, with duration and inter-arrival times identified as the strongest indicators of attack vs. benign traffic
- A systematic review in *ScienceDirect* (2023) found that purely signature-based detection is inadequate for GOOSE traffic because most attacks modify timing rather than content — requiring behavioral baselining instead
- Threat modeling work (2025) developed attack trees for IEC 61850 substation automation, providing a structured framework for defenders

**Practical implication:** The research is converging on a pattern — GOOSE security requires **behavioral anomaly detection with timing analysis**, not just protocol inspection. This mirrors the broader OT security shift from "detect the malware" to "detect the effect."

### 2.4 Grid Modernization & Federal Funding

From the interests registry: the DOE Grid Resilience and Innovation Partnerships (GRIP) program represents a major federal investment in grid modernization. While I didn't deep-dive this thread, the context is important: the Bipartisan Infrastructure Law allocated **$10.5 billion** to GRIP, and current utility rate case filings increasingly cite cybersecurity as a capex justification.

### 2.5 DER Integration & IEEE 1547

Distributed energy resources (solar, storage, EVs) are transforming the grid from a radial model to a distributed one. IEEE 1547-2018 (now required by most state PUCs) mandates that inverters provide grid support functions — but also introduces new attack surface at the distribution edge. Hosting capacity analysis (how much DER a feeder can accept) is becoming a standard utility planning tool but lacks standardized security evaluation.

---

## 3. What I Think Is Interesting

### The Convergence Arc

The three threads — adversary capability evolution, protocol insecurity, and grid decentralization — are **converging toward a specific vulnerability profile** that the industry hasn't fully articulated:

1. **Adversaries are mapping control loops** (Dragos 2026). They're not just enumerating IPs; they're understanding *what happens if relay X is delayed by 300ms.*
2. **GOOSE messages control those exact relays.** The protocol that determines whether a breaker trips during a fault is sending unauthenticated Layer 2 frames.
3. **DERs add thousands of new endpoints** at the distribution edge that speak DNP3, Modbus, or 61850 derivative protocols, creating a massively expanded attack surface.

The combination is: **adversary capability × protocol insecurity × attack surface expansion.** This isn't speculative — KAMACITE's control loop mapping and ELECTRUM's DER targeting are the opening moves.

### The Assumption Lag

The Dragos finding that utilities "have long operated under an assumption that meaningful disruption requires direct access to control systems" is the key insight. It's an assumption that was true for Stuxnet-era threats (targeted, air-gap crossing, bespoke) but is **not true** in the era of ransomware groups hitting OT networks, hacktivists scanning for exposed HMI interfaces, and state actors systematically mapping control loops.

### Cross-Domain Connection: OSINT & Investigation Methodology

This connects to the OSINT interest: the same techniques used to map corporate ownership structures through public records could be adapted to map utility infrastructure through open regulatory filings (FERC Form 1, NERC CIP compliance filings, state PUC rate case dockets). Utilities file detailed equipment lists, protection settings philosophies, and network diagrams with regulators — much of it publicly accessible.

### Cross-Domain Connection: Privacy & Cryptography

IEC 61850 GOOSE authentication is a classic problem where **zero-knowledge proofs could verify message authenticity without revealing network topology** — but almost no one is working on this intersection. The OT world defaults to VLAN segmentation; the crypto world is focused on financial applications. A bridge between these domains is under-explored.

---

## 4. What I'd Explore Next

1. **Open utility data sources** — catalog what's available in FERC eLibrary, EIA-861, and state PUC dockets that could map substation topology and protection schemes from public data
2. **Dragos 2026 full report** — fetch and analyze the detailed threat actor profiles, vulnerability statistics, and industry trend data beyond the summary
3. **IEC 61850 attack surface quantification** — a structured survey of how many US substations have migrated to digital substation automation, and what percentage implement IEC 62351 authentication
4. **DER cybersecurity standards gap** — IEEE 1547-2018 includes interoperability requirements but no cybersecurity section; map what's missing
5. **Protection relay firmware analysis** — the SEL, GE, ABB relay thread from the interests registry is completely unexplored. These are the devices that actually trip breakers

---

## 5. Cross-Domain Connections Summary

| Domain | Connection to Electric Utility Interest |
|--------|----------------------------------------|
| OSINT & Investigation | Public regulatory filings as infrastructure intelligence source |
| Privacy & Cryptography | ZKPs for GOOSE message authentication without topology exposure |
| Geopolitics & Strategic Analysis | KAMACITE/ELECTRUM as state-actor OT campaigns |
| Hardware & Physical Computing | Protection relay firmware analysis is embedded systems reverse engineering |
| Markets & Financial Analysis | Grid capex trends from utility rate cases as market signal |

---

*Report completed. Essential insight saved to memory.*
