# Field Report: Briar and Cwtch — Metadata-Resistant Protocol Architectures Compared

**Date:** 2026-05-29
**Topic:** Privacy & Cryptography — Metadata-resistant communication protocols (Briar, Cwtch)
**Interest:** Dormant Interest reactivated — never previously explored

---

## 1. What I Explored

Briar and Cwtch are the two explicitly-listed metadata-resistant protocols in Jake's interests that have never received a dedicated field report. Earlier reports covered Signal/PQ transition, anonymity wrappers, and the general metadata-resistant protocol landscape, but Briar and Cwtch architecture was untouched.

I chased the core protocol designs: how each system prevents an adversary from learning **who talks to whom, when, and how often**. This led to primary sources: Briar's ETH Zürich cryptographic audit thesis (Yuanming Song), Cwtch's academic paper (cwtch.im/cwtch.pdf), and both projects' security documentation.

---

## 2. What I Found

### 2.1 Briar — Delay-Tolerant P2P with Multi-Transport Resilience

Briar is a fully peer-to-peer messaging application (Android app, v1.4.20 analyzed) designed for activists and journalists in adversarial environments. No central servers.

**Protocol Stack:**
- **BQP (QR code protocol):** Local, ephemeral key exchange via QR codes — offline pairing. Prevents MITM during initial trust establishment.
- **BHP (Handshake protocol):** Remote key agreement when peers aren't physically co-located.
- **BRP (Rendezvous protocol):** Peer discovery over Tor using static key exchanges to establish Tor hidden services.
- **BTP (Transport protocol):** Transport-layer security, connection-oriented for reliable delivery over unreliable links.
- **BSP (Synchronisation protocol):** Application layer; each message carries group ID, timestamp, and body. Groups identified by hash of client info + descriptor (sorted author IDs). Designed for delay-tolerant networks where peers may be intermittently connected.

**Transports:** Bluetooth, Wi-Fi, and Tor. This is the killer feature: if the internet is cut, Briar syncs via Bluetooth or Wi-Fi Direct mesh. In a crisis (internet blackout, natural disaster, authoritarian shutdown), communication continues locally.

**Security guarantees (per ETH audit):**
- Confidentiality, integrity, and authentication via custom cryptography
- Forward secrecy — though the audit found BHP is NOT fully forward-secret (a non-trivial finding: an attacker who compromises a long-term key can derive past session keys)
- Transport keys are rotated
- Metadata protection is **external only**: Briar hides communication FROM network observers (via Tor for internet, direct connections for local), but does NOT hide metadata within groups. Group IDs derive from member identities, so all participants know who else is in the group. A malicious insider can duplicate messages.

**Threat model:** Adversary comprehensively monitors long-range channels (internet) but has limited short-range (Bluetooth/Wi-Fi) capability. Briar is designed to resist this surveillance tier.

### 2.2 Cwtch — Tor-Native, Server-Mediated Metadata Resistance

Cwtch (/kʊtʃ/ — Welsh: "a hug that creates a safe place") is a decentralized, privacy-preserving multi-party messaging **protocol** (not just an app). It extends the Ricochet protocol to support asynchronous group messaging through untrusted, discardable relay infrastructure.

**Architecture:**
- Every user runs their own Tor onion service (.onion address)
- **Cwtch Servers:** Untrusted, discardable relay infrastructure. Peers connect ephemerally to servers. Servers broadcast all encrypted GroupMessages to all connected clients. Each peer attempts decryption with all known group keys — messages that don't decrypt are silently discarded.
- The server sees only encrypted blobs and anonymous Tor connections. It cannot learn: which peers belong to a group, which messages belong to the same conversation, or which ephemeral connection maps to a real identity.
- Timing side-channels are mitigated by separating the listen channel from decryption — processing time doesn't leak which message was decryptable.

**Communication model:** Asynchronous group messaging. Server broadcasts every message to every ephemeral client. This broadcast-all design is the core metadata-hiding trick: the server can't distinguish between groups or conversations because everyone gets everything.

**Key exchange:** Requires simultaneous online presence for initial group setup — peers must be online at the same time for key exchange and group creation. Server addresses can then be shared out-of-band.

**Security guarantees:**
- Confidentiality, integrity, authentication
- Sender anonymity, receiver anonymity, participation anonymity
- Unlinkability between messages of the same conversation
- Forward and backward secrecy

**Key difference from Briar:** Cwtch provides metadata resistance even against the infrastructure. The server is untrusted by design. Briar protects against network observers but exposes group membership to participants.

### 2.3 Head-to-Head Comparison

| Aspect | Briar | Cwtch |
|--------|-------|-------|
| **Infrastructure** | Fully P2P, no servers | Untrusted discardable relay servers |
| **Transports** | Bluetooth, Wi-Fi, Tor | Tor onion services only |
| **Communication model** | Delay-tolerant sync (peers connect directly) | Asynchronous via server broadcast |
| **Metadata resistance** | External only (network observers); group members know membership | Full: server can't link messages to groups or identities |
| **Key exchange** | QR code (offline) + remote handshake | Requires simultaneous online presence |
| **Offline resilience** | Yes — Bluetooth/Wi-Fi mesh works without internet | No — requires Tor (requires internet) |
| **Insider threat** | Group members know all participants; can duplicate messages | Group members know membership (structure inherent) |
| **Maturity** | Released Android app, academic audit | Research prototype (alpha 2019), academic paper |
| **Censorship resistance** | High — no server to block, multi-transport | Medium — Tor can be blocked, servers can be targeted |

---

## 3. What I Think Is Interesting

### The Architecture-Incentive Alignment

The most interesting finding is how each system's threat model shapes its architecture in opposite directions:

- **Briar optimizes for AVAILABILITY under disruption.** Internet down? Bluetooth mesh still works. No servers means no single point of censorship. The trade-off: metadata is visible within groups because the delay-tolerant sync model requires participants to know who to sync with. You can't hide the social graph from people who need to find each other in a mesh.

- **Cwtch optimizes for PRIVACY under surveillance.** The broadcast-all model means even the relay operator can't learn who's talking to whom. The trade-off: requires Tor (needs internet) and simultaneous online presence for group setup. You can't communicate during an internet blackout, but when you can, nobody — not even the server operator — knows who you're talking to.

This is a fundamental tension in secure communication: availability vs. privacy. Briar chooses availability. Cwtch chooses privacy. There is no single protocol that maximizes both.

### Cwtch's Broadcast Architecture as a Privacy Primitive

Cwtch's broadcast-all design is elegant in its simplicity. By making the server broadcast every message to every connected client, the server learns nothing from message delivery because there IS no selective delivery — everyone gets everything. The work of filtering (which messages are for you) moves to the client. This is a structural privacy guarantee, not a cryptographic one — it works regardless of how strong the encryption is because the server never sees selectivity.

This has a direct analog in the Exocortex: the injection gate processes all outputs regardless of destination. No tool sees selective output; each tool gets the same structured feed. Structural privacy through non-selectivity.

### The BHP Forward Secrecy Failure (Briar)

The ETH audit finding that Briar's BHP handshake protocol is NOT forward-secret is significant. In practice: if a Briar user's long-term key is compromised, an attacker with access to stored ciphertext can decrypt past sessions. This is a known property of the protocol's design, not an implementation bug. For a tool marketed to activists and journalists in high-risk environments, this is a meaningful gap.

### The Neglected Research Question

Both systems have been in development for years (Briar since ~2014, Cwtch since ~2018), yet the academic literature comparing them is thin. The ETH thesis on Briar is the only formal cryptographic audit. Cwtch's paper is a system description, not a formal analysis. For protocols that promise metadata resistance — the holy grail of private communication — the verification gap is striking.

---

## 4. What I'd Explore Next

1. **Briar BHP Forward Secrecy Fix:** Has the Briar team addressed the forward secrecy gap identified in the ETH audit? Check recent commits and issues.
2. **Cwtch Deployment Status:** Is Cwtch still active? The alpha launched in 2019 — what's the current state? Check Open Privacy Research Society updates.
3. **Ricochet Protocol Evolution:** Both Briar and Cwtch trace lineage to Ricochet. How has the Ricochet protocol itself evolved?
4. **Bridging the Gap:** Is there a protocol design that provides BOTH Briar's offline resilience AND Cwtch's infrastructure-level metadata resistance? Could a hybrid approach (Briar-style local mesh + Cwtch-style broadcast relays for internet bridging) work?
5. **Exocortex Integration:** Could Cwtch's architecture serve as a model for Exocortex peer-to-peer agent communication? The broadcast-all model maps to agent publish-subscribe patterns.

---

## 5. Cross-Domain Connections

### Metadata Resistance ↔ Entity Resolution Privacy
Entity resolution across heterogeneous datasets inherently reveals connections that parties may want hidden. The same structural techniques that hide metadata in communication protocols can inform privacy-preserving entity resolution: link records without revealing the linking logic or intermediate connections.

### Broadcast-All Architecture ↔ Injection Gate
Cwtch's broadcast-all model (server broadcasts everything, client filters) is architecturally identical to the Exocortex injection gate pattern: all tools receive the same structured output, each tool determines relevance locally. This is "structural privacy through non-selectivity" — a reusable pattern.

### Offline Mesh Resilience ↔ SCADA/ICS Availability
The Briar model of Bluetooth/Wi-Fi mesh fallback during internet disruption parallels SCADA/ICS availability requirements: critical infrastructure must function during network degradation. Briar's delay-tolerant synchronization protocol (BSP) could inform agent communication patterns for intermittently-connected industrial environments.

### Tor Dependency vs. Censorship Circumvention
Cwtch's exclusive reliance on Tor creates a single point of censorship: block Tor, block Cwtch. This is comparable to a single-source intelligence dependency — if the source is compromised, the entire pipeline is blind. Multi-transport diversity (Briar's approach) is analogous to multi-INT fusion in intelligence analysis.

### Forward Secrecy Failures ↔ Epistemic Integrity
Briar's BHP forward secrecy gap is a cryptographic analog to the Exocortex's epistemic integrity problem: past "truths" (decrypted messages / agent outputs) that were considered secure at the time can be retroactively compromised. The lesson: cryptographic guarantees and knowledge claims both need temporal qualification — "true at time T given assumptions A."

---

## Sources
- Briar Project: https://briarproject.org/how-it-works/
- ETH Zürich Cryptographic Audit: "Cryptography in the Wild: Briar" (Yuanming Song)
- Cwtch Protocol Paper: https://cwtch.im/cwtch.pdf
- Cwtch Security Handbook: https://docs.cwtch.im/security/intro/
- Cwtch Documentation: https://docs.cwtch.im/
