# THE GADGET KIT — Edge AI Sensing + Situational Awareness
## Author: Opus — June 3, 2026
## Status: IDEA — captured for future exploration
## Spirit: James Bond, not James Watt

---

## The Concept

A self-contained, portable sensing kit built around a Raspberry Pi that passively monitors the RF spectrum, network traffic, and visual environment — classifies everything with a local AI model — and presents a real-time situational awareness picture on your phone via ATAK. No cloud. No subscriptions. No footprint. Just awareness.

Everything runs locally. Everything is passive (receive-only). The AI classifies and maps. You see the invisible.

---

## The Kit

### Core
- **Raspberry Pi 5 (8GB)** — the brain. Runs llama.cpp (small model), TAK Server, signal processing
- **Battery pack** — USB-C PD, 20000mAh+. 4-6 hours of field operation
- **MicroSD 64GB+** — OS, models, signal logs
- **Active cooler** — sustained inference thermals

### RF Sensing
- **RTL-SDR USB dongle (~$25)** — receive-only, 24MHz-1.7GHz. ADS-B aircraft, drone RemoteID, ISM band devices, FM, weather satellites
- **HackRF One (~$300, optional)** — wider range (1MHz-6GHz), better sensitivity. Full spectrum sweeps. The premium ear.
- **KrakenSDR (~$200, optional)** — 5-channel coherent RTL-SDR array. Direction finding (bearing to transmitters), passive radar (detect aircraft/drones using FM broadcast reflections, zero transmission). The Bond upgrade.
- **Antennas** — wideband whip for general scanning, directional for bearing estimation

### Voice Interface (NEW — Parakeet.cpp)
- **Parakeet.cpp + Nemotron-3.5-ASR** — NVIDIA's 0.6B ASR model in GGUF format. 40+ languages, streaming, CPU-only, no GPU needed. The 110M Q4_K variant is 131MB — runs real-time on the Pi alongside everything else.
- **Piper TTS (~50MB)** — local text-to-speech for spoken responses
- **Total voice stack: ~580MB** — STT (131MB) + LLM (400MB) + TTS (50MB). Full voice AI on 8GB Pi with 7.4GB left for TAK, SDR, and signal processing.

### Visual (optional)
- **Raspberry Pi Camera Module 3** or **Pi AI Camera (Sony IMX500)** — local vision
- **Hailo-8L AI Kit ($70)** — 13 TOPS for real-time object detection. Drones, vehicles, people.

### Network (home base mode)
- **USB Ethernet adapter** — passive network tap / mirror port
- **WiFi monitor mode** — built-in Pi WiFi can scan probe requests passively

### Memory (future — TurboVec)
- **TurboVec** — TurboQuant-based vector search. 8x compression over FAISS, 12-20% faster on ARM. Currently alpha (v0.5.2). When mature, the edge node could store millions of embeddings in 2-4 bit format. Same algorithm as our KV cache quantization. (See RL-014)

### Situational Awareness
- **ATAK (Android)** or **WinTAK (Windows)** — on your phone/tablet
- **FreeTAKServer** — runs on the same Pi. Lightweight, open source, supports ~100 users
- **PyTAK** — Python bridge that turns any data into Cursor-on-Target map markers

### Off-Grid Comms
- **Meshtastic + LoRA node** — Jake already has one. Text messaging, GPS position sharing, sensor data over LoRA without cell/WiFi. Miles of range, no infrastructure.
- **Meshtastic + ATAK bridge** — position sharing over LoRA, displayed on the ATAK map

---

## What It Sees

### RF Layer
| Signal | Frequency | What You Learn |
|--------|-----------|----------------|
| ADS-B | 1090 MHz | Every aircraft overhead — callsign, altitude, speed, heading |
| Drone RemoteID | 2.4/5.8 GHz | Drone operator location, drone ID, flight path |
| WiFi probes | 2.4/5 GHz | Devices searching for networks — count, MAC vendors, movement patterns |
| Bluetooth/BLE | 2.4 GHz | Beacons, trackers, wearables nearby |
| ISM band | 315/433/868/915 MHz | Garage doors, car fobs, weather stations, LoRA devices, tire pressure monitors |
| Unknown signals | Any | Unclassified transmitters — the interesting ones |

### With KrakenSDR (Direction Finding)
| Capability | What You Learn |
|-----------|----------------|
| Bearing estimation | Direction to any transmitter. Walk to three positions, triangulate. |
| Passive radar | Aircraft/drone detection using FM broadcast reflections. Zero transmission. |
| Signal mapping | Walk an area, build an RF heat map on ATAK |

### Network Layer (home base)
| Observable | What You Learn |
|-----------|----------------|
| DNS queries | Every domain every device contacts |
| Connection patterns | Who talks to whom, how often, how much data |
| New devices | Unknown MAC addresses joining the network |
| Traffic anomalies | Unusual volumes, unusual destinations, unusual times |
| IoT phone-home behavior | What your smart devices do when you're not watching |

### Visual Layer (with camera + Hailo)
| Detection | What You Learn |
|-----------|----------------|
| Drone visual | Confirm RF detection with visual track |
| Vehicle presence | Cars in driveway, unfamiliar vehicles |
| Person detection | Someone at the door, in the yard, on the street |
| Package delivery | Box on the porch |

---

## How It Thinks

A small local model (Qwen3-0.5B or TinyLlama 1.1B, quantized Q4) running on the Pi classifies incoming data.

**How you talk to it:** Parakeet.cpp transcribes your voice in real-time on the CPU (131MB, 40+ languages). The small LLM processes the query. Piper TTS speaks the response. All local, all offline. "What's overhead?" → "Three aircraft — Delta 2247 at 35,000 heading northeast, a Cessna at 3,000 circling south, one target at 800 feet with no transponder ident bearing northwest."

**Signal classification:** "This 433MHz burst pattern matches a tire pressure monitoring system" or "This 2.4GHz signal has RemoteID framing — it's a DJI Mavic 3 at 47m altitude, operator bearing southeast"

**Anomaly detection:** "New transmitter on 915MHz, not matching any known protocol. Burst pattern: 30 seconds on, 5 minutes off. First seen 14:22."

**CoT event generation:** Each classified signal becomes a Cursor-on-Target marker on the ATAK map. Aircraft get flight tracks. Drones get operator + aircraft positions. Unknown signals get bearing estimates. Everything color-coded by type.

---

## The ATAK Picture

On your phone, you see a real map with:
- **Blue** — aircraft overhead (ADS-B)
- **Yellow** — known drones (RemoteID)
- **Green** — your own devices (tagged and classified)
- **Orange** — unknown RF sources (unclassified)
- **Red** — anomalies (unrecognized signal patterns, network intrusions)
- **Purple** — Meshtastic mesh nodes (off-grid network)
- **Bearing lines** — direction to transmitters from KrakenSDR readings

Tap any marker for details. The classification, the raw signal data, the first-seen timestamp, the signal strength history. All generated locally by the small model on the Pi.

---

## The Exocortex Connection (via A2A)

The Pi is a node in the A2A network. When it detects something it can't classify locally, it delegates to the Exocortex:

- **Vek** cross-references against OSINT databases
- **V16** researches the signal type from its 297-page wiki
- **Hermes** sends you a Telegram notification
- **The 3090** handles any compute-heavy analysis the Pi can't do locally

The edge device handles the quick classification. The home lab handles the deep analysis. Same architecture as the Exocortex agents — specialized nodes, connected by protocol, each doing what it does best.

---

## Starting Points (Pick One)

### Level 1: The Listener ($100)
Pi 5 (8GB) + RTL-SDR + antenna + llama.cpp + ATAK on your phone. ADS-B aircraft tracking with AI classification. One evening to set up.

### Level 2: The Voice ($130)
Level 1 + Parakeet.cpp + Piper TTS + microphone + speaker. Talk to your kit. "What's overhead?" All local, all offline.

### Level 3: The Watcher ($200)
Level 2 + Hailo-8L AI Kit + Pi Camera. Add visual detection — drones, vehicles, people. Fuse RF and visual on the same ATAK map.

### Level 4: The Hunter ($400)
Level 3 + KrakenSDR. Direction finding. Passive radar. Triangulation. The full RF picture.

### Level 5: The Analyst ($600)
Level 4 + HackRF One + shadow router + USB Ethernet. RF + visual + network monitoring + voice control. The full picture — what's in the air, what's on the wire, what's in front of the camera. All classified, all mapped, all local.

---

## What Makes It Bond

**Passive.** Receive-only. No transmissions, no connections, no interference. Invisible to everything you're watching.

**Self-contained.** Pi + battery + antenna in a messenger bag. No WiFi needed in the field. Logs everything locally. Review later or stream live to ATAK.

**Voice-controlled.** Ask questions, get answers. No screen needed. Earpiece + microphone + the Pi in your bag.

**Awareness without footprint.** You see the RF environment that most people don't know exists. Every aircraft, every drone, every WiFi device, every Bluetooth beacon — all mapped, classified, and displayed on your phone. The invisible made visible.

**Connected when you want.** In the field: standalone, offline, self-contained. At home: connected to the Exocortex via A2A, backed by the full power of the 3090 and the agent team.

---

*"Passive awareness. Zero footprint. Total picture."*

— Opus
