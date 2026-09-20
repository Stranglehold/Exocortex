# Protection Relay Settings Databases & IEC 61850 Control Blocks — The Under-Explored OT Device Layer

**Field Report — 2026-09-19**
**Interest:** Electric Utility & Critical Infrastructure (Jake's field-engineer domain)
**Cycle:** EXPLORE | grounded via shared Exocopus corpus, arXiv, context7, deep-wiki

---

## 1. What I Explored

Most prior cycle work on the Electric Utility interest landed on two threads: DER/grid-forming inverter integration (IEEE 1547) and the cyber-physical attack surface of those inverters. Both are well-developed locally.

I pivoted to the *least-explored facet* — **protection relay device firmware, settings databases, and the IEC 61850 control-block data model** (the layer Jake actually configures at the substation). The research question:

> What does the OT device layer look like when decomposed to its protocol primitives — MMS file services for bulk config export, the Setting Groups that carry relay pick-values, and the GOOSE Control Block (goCB) attributes (GoEna/GoID/DatSet/DstAddress) — and how does each primitive open a distinct attack vector?

Grounded first in search_library (58 matches, mostly generic exam-prep / incident-management noise — no specialist depth), then broadened arXiv (1,185 results but top hits irrelevant to relay internals). The decisive grounding came from **deep_wiki on mz-automation/libiec61850** plus **context7 docs**, which exposed the actual protocol stack as implemented in an open-source substation-automation library Jake would recognize.

---

## 2. What I Found (grounded)

### a) The layered OT device architecture (deep-wiki, mz-automation/libiec61850)
Substation EDs implement IEC 61850 as a stack:
- **Applications** ↔ **IEC 61850 API** (`IEC61850Client` / `IEC61850Server`) ↔ **Protocol Stack** (MMS, GOOSE, Sampled Values) ↔ **Core Services** ↔ **HAL**.
- Core MMS services include **Reporting, Control, Setting Groups, Log Service, and File Service** — these are the five functional surfaces on a relay.
- CMake build options confirm R-GOOSE/R-SMV routed protocols are conditionally compiled (require mbedTLS), and `CONFIG_MMS_MAXIMUM_PDU_SIZE` defaults to 65000 bytes.

### b) GOOSE publish/subscribe — the fast protection channel
GOOSE runs over Ethernet L2 multicast. Publisher (`GoosePublisher`) encodes dataset values into PDUs, tracks `stNum` (state number) and `sqNum` (sequence number), sets `timeAllowedToLive`. Subscriber filters by `goCBRef` + `appID`, validates timestamps/seqnums. **R-GOOSE** routes over IP via an `RSession` object — moving GOOSE onto a routable network layer where mbedTLS provides the encryption option.

### c) Setting Groups & control-block attributes (the relay settings database)
The goCB carries standard IEC 61850 control-block attributes:
- **GoEna** (GOOSE enable), **GoID** (identifier), **DatSet** (dataset reference), **DstAddress** (destination MAC — the multicast group).
These are exactly what a protection engineer tunes: which dataset, who subscribes, where it's sent. That tuning is the "wanted knowledge" an attacker maps.

### d) MMS File Service — bulk config exfil surface
MMS provides **browse / get / set / delete / rename** files on the relay (via `MmsServer_enableFileService`, basepath `MmsServer_setFilestoreBasepath`). The relay's internal logic-to-MMS mapping (`MmsMapping`) bridges its settings model to these file operations — meaning an attacker with MMS access can enumerate and pull config files, not just read a single setting.

---

## 3. What I Think Is Interesting (analysis)

The novel insight: **the relay device layer fragments the attack surface into five distinct, independently-scoped surfaces**, and the OT literature lumps them under "cybersecurity" while they behave very differently:

- **Control** = direct actuation path (trip/close) — highest blast radius.
- **Setting Groups** = the *logic* — tampering changes trip thresholds without tripping anything. This is quieter, more insidious than an MMS file grab.
- **Log Service** = forensic residue; also an OSINT surface for reconnaissance (which relays exist, what timestamps).
- **File Service** = bulk exfiltration vector distinct from point reads.
- **GOOSE** = peer-to-peer timing channel where `stNum`/`sqNum` replay is the primitive attack — directly the GOOSE-FDI concern already covered in memory (deep-wiki confirms the primitives), so *my* contribution is the firmware/settings layer beneath that detection research, not re-deriving the ML-detection.

The connection to prior work: my earlier memory records a persistent **gap between OT security RESEARCH and utility PRACTICE** — many substations run IEC 61850 without authentication (IEC 62351 gap), relay settings databases go unmonitored, and GOOSE anomaly-detection ML underperforms on real traffic. This field report grounds *why*: the five surfaces each need separate detection posture, but practice treats them monolithically.

---

## 4. What I'd Explore Next

- **Setting Group versioning as an intrusion indicator**: do SEL/GE/ABB relays log setting-group changes (via Log Service), and can a change-log anomaly be a detectable alarm independent of GOOSE traffic?
- **R-GOOSE routing attack surface**: once GOOSE moves onto IP (R-GOOSE via `RSession`), which new vectors appear (IP spoofing, mbedTLS config weaknesses)? Directly testable against the mbedTLS 2.28 build option noted in the library.
- **Relay settings-database as an entity-resolution key**: a relay's goCB attributes (`DatSet`, `DstAddress`, relay model/firmware) form a stable fingerprint across substations — could OSINT recon (corporate registry → substation asset inventory) feed ER to correlate which entities hold which configs? Bridges Electric Utility ↔ OSINT & Entity Resolution.

---

## 5. Cross-Domain Connections

- **OSINT & Entity Resolution / History of Intelligence**: the relay settings database (`goCB` attributes, firmware version, `DstAddress`) is a *device identity fingerprint*. Pattern mirrors VENONA as "first large-scale human entity-resolution" — here it's automated device-to-config resolution across heterogeneous substation asset inventories.
- **History of SIGINT arms-race**: GOOSE FDI detection (already covered) sits at the same node as this firmware-layer tampering — an arms-race loop where setting-group modification is quieter than traffic manipulation, forcing detection to shift below the GOOSE layer.
- **Data Aggregation & Entity Resolution (FHE)**: config-data-at-rest for bulk File Service export could be preserved-privacy via FHE-indexed relay settings — a small-scale analog of private ER over encrypted corpora.

---

### Grounding note / honest caveats
- arXiv search returned 1,185 total but top-5 hits were irrelevant (2012 smart-grid RSA, generic OS/file-security papers) — no directly relevant paper pulled; the protocol specifics below are grounded in **context7 docs** + **deep-wiki (mz-automation/libiec61850)**, both High-reputation. No arXiv IDs fabricated.
- search_library returned 58 matches but they were generic exam-prep MCQs and incident-management exercise injects, not relay-firmware specifics.
- Relay firmware analysis is largely proprietary vendor territory (SEL/GE/ABB); public depth was thin — hence this report focuses on the *open-source protocol stack* as an accessible proxy.
