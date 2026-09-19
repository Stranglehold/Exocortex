# Exocortex

Exocortex is an [Agent Zero](https://github.com/frdel/agent-zero) plugin that gives a local model a working life between
conversations, and a set of instruments for finding out whether any of it helps. Its centre is an idle engine: when nobody
has spoken to the agent for a while, a watcher starts a cycle, the agent does one bounded piece of work on its own wiki,
memory and interests, records what it did, and stops. Around the engine sit the layers that keep that work honest: a repair
pipeline for the model's malformed tool calls, a memory layer that recalls what she is working on rather than what she was
told, and a record of every cycle's fire, ending and close.

This README describes the system as it is measured in September 2026, and the direction it is taking. The earlier README,
which described the twelve-layer scaffolding stack this project was through August 2026 and the research programme around
it, is kept whole in [`docs/README-2026-08-history.md`](docs/README-2026-08-history.md). Nothing in it is disowned; most of
it is now under audit.

## The shift

Exocortex began as scaffolding: layers that injected plans, beliefs, reasoning state and supervision into the model's prompt
so that a local model would behave more like a larger one. On 2026-09-08 the injection layers were switched off (decision
DEC-051), and the system that remained turned out to be the one that earns its keep on measurement:

- the engine, which completed seven of its first eleven cycles on the night it was re-enabled and has produced field reports,
  wiki pages and syntheses every day since;
- the repair pipeline, which rescued 75 prose-wrapped calls in one day and, on 2026-09-18, an 11,499-character editor call
  that would previously have killed its cycle;
- the memory layer after its recall query was rebuilt from the agent's current work: twenty different sets of memories
  recalled in twenty turns, drawing on 89 memories, where the previous twenty turns had recalled one set of nine.

The layers from the beginning carry no such number in either direction. A stock Agent Zero container on the same model,
`Control`, now runs beside the plugin as the baseline, and the same instruments read both. The audit protocol is in
`Fable/studies/2026-09-19-exocortex-audit-protocol.md`: every extension, tool, prompt and helper gets one row with five
measured facts (does it fire, what it costs, who reads what it writes, what effect it has, what it interferes with) and a
verdict that follows from the facts alone: keep, retire, or instrument first and then decide. Retire means archive by rename
with a manifest, never delete, on the operator's word per row. The first verdict landed before the audit formally started:
the supervisor's second-opinion call was consuming 17% of the model's day for answers that arrived one time in five, and
it is off.

## What runs

One plugin tree, `plugins/_exocortex/`, deployed to `/a0/usr/plugins/_exocortex/` by a directory walk. Measured on
2026-09-16: 62 python extensions across 14 hook points, 9 API handlers, 13 tools, 17 helpers, 18 prompts, 11 web UI
extensions, one background service.

**The idle engine.** `services/idle_watch.py` watches idle time, runs a rotation (MAINTAIN, four BUILDs, SYNTHESIZE,
EXPLORE), fires one cycle at a time, enforces a stall cap and a hung cap, and writes every fire and every ending to a
ledger. `api/idle_control.py` enables, disables, pauses and resumes it; `api/office_feed.py` reports it; `prompts/
idle_activation.md` is the charge each cycle receives; `cycle_close.py` in the workspace records a finished cycle. The
Office pane in the web UI's right canvas shows the running cycle, the rotation, the ledger and the log.

**The repair pipeline**, on `process_tools/start`, in order: `_04` repairs one dropped closing quote or invalid escape,
including inside a call buried behind prose; `_05` extracts a valid call from a reply that wrapped it in reasoning, and
executes it when the case is unambiguous; `_06` names the structural defect Agent Zero computes and discards (arguments at
the top level instead of inside `tool_args`) where the stock warning says only "misformatted"; `_07` refuses to execute a
reconstructed call unattended; `_10` ends a turn after a bounded number of refusals.

**Memory.** Agent Zero's own memory plugin stores, consolidates and recalls. Exocortex reshapes recall: on an idle cycle the
search query is built from the agent's recent work rather than the fixed activation charge, bounded to what the embedder can
take, and the retrieved set is ranked with temporal decay and access tracking. A selective memorizer, a classifier,
maintenance, insight and methodology capture, and an epistemic-integrity check run at the end of each monologue.

**Guards and the record.** Signature checks and an action boundary before a tool runs; error comprehension, an evidence
ledger, write validation, truncation handling, failure fingerprints and a tool-call tracker after it; the idle trigger and
the sleep trigger that the engine depends on. A supervisor loop with deterministic tiers and a canary. Most of these are the
audit's subject: they fire, and what they change is not yet measured.

**Web UI.** A theme system with a room layer (background, panel translucency, scanlines, vignette), the Office pane, a
system monitor, a theme picker and editor.

## What the numbers say

All of these are from the instruments in `Fable/studies/`, with the scripts beside each study.

- **Where the model's day goes** (2026-09-18, from the inference server's own log): the agent's own turns 61% of busy
  time, the supervisor's second-opinion call 17% (now off), Agent Zero's own after-work about 16%, the selective memorizer
  5%. The same model generates at the same speed for both containers when alone; the plugin's turns run slower because they
  carry 30 to 70 thousand tokens of context where a stock chat carries 3 to 10 thousand.
- **Where a BUILD cycle's turns go**: 16% of turns rejected at the JSON gate; of accepted turns, 47% on the close and
  bookkeeping, 32% deepening the page, 18% on the opening steps. Every death of the week sat at the close. The research
  ladder is not the constraint; the ritual around it is.
- **The engine's own blind spot**: its ledger notices an ending only when the next fire is due, a fixed delay of about 28
  minutes, and not at all while the engine is paused or disabled, because the reapers sit behind the same gate. A
  completion-gated redesign is specified and ruled (`Fable/studies/2026-09-16-completion-gated-firing.md`): fire on the
  agent's own close row, resolve before any gate, back off from the ending after a death.
- **The embedder**: the 2,048-token truncations were never on memories; they were the recall query, the charge itself,
  embedded four times a turn. Gone with the recall change.

Do not read the methodology tracker for any of this: its outcome field defaults to "completed" and its artifact field has
never been filled.

## What was turned off, and why

On 2026-09-08 the layers that injected scaffolding into the prompt were switched off: belief-state tracking, reasoning and
working-state injection, HTN plans, PACE plans, supervisor injection at the call boundary, skill surfacing, a strategy
advisor, a constraint heartbeat, a step budget. Seventeen extensions plus the PACE injector retired earlier. The decision is
DEC-051 in `state/decision_log.md`. Until the archive step lands, those files still sit in this tree as ordinary `.py` and a
fresh install would deploy them again; the parity checker lists them as missing, which is the wrong reading. A RETIRED
manifest for that checker is the first audit instrument to be built.

## Install

```
bash install_all.sh
```

`install_all.sh` at the repo root runs the install layers in order; layer 16, `scripts/install_exocortex_plugin.sh`, copies
the plugin tree into the container by a directory walk and is the authoritative deploy. Verify with
`scripts/verify_plugin_parity.py` (repo tree against container, md5 per file). The walk ships whatever is on disk in the
working tree, committed or not.

Python extensions reload on the next turn after a file changes (a watchdog clears the extension caches; a cache reset of
`*(extensions)*` from inside the container is the fallback). A new or changed helper imported by bare name needs a container
restart. API handlers load at process start. Prompts are read per call.

## Where the records are

- `state/decision_log.md`: numbered decisions, DEC-001 onward.
- `team-comms/`: the letters between the people and models working on this.
- `Fable/`, `Kestrel/`, `Opus/` (beside this repo): each Claude instance's own state, journal, rules, studies and controls.
  Every claim in this README has a study behind it there, with the script that produced the number.
- `workspace/office/` in the container: the engine's ledger, state and log. `workspace/self-improvement/journal.jsonl`:
  the agent's own close rows, the one record that never depends on the daemon.
- `agent-exports/`: the agent's wiki, field reports and syntheses, committed as they are written.

## Known limits

The shape above is measured; what fires within it is a lower bound, because silent extensions leave no trace. The model's
failure rate at the JSON gate is the engine's main cost; the repair pipeline lowers it and the close ritual concentrates it.
Three API handlers besides the engine's answer unauthenticated requests and have not been read for what they expose. The
plugin installer deploys the working tree, so an uncommitted edit is in production on the next install. The container
holds the agent's chats and memory with no volume behind them; the exports are the copy.

---

## Acknowledgments

This architecture was developed through an intensive collaborative process between a human systems thinker and AI reasoning partners, proving the thesis it was built to serve — that the right scaffolding, applied at the right layers, makes the whole system more capable than any component alone.

The memory enhancement system draws from research by multiple contributors:
- **OwlCore.AI.Exocortex** (Arlodotexe, MIT License) — memory decay curves, recollection-as-memory, and clustering/consolidation architecture
- **"Generative Agents: Interactive Simulacta of Human Behavior"** (Park, O'Brien, Cai, Morris, Liang, Bernstein, 2023) — the recency × importance × relevance scoring framework for memory retrieval
- **"Recursively Summarizing Enables Long-Term Dialogue Memory in Large Language Models"** (Wang, Ding, Cao, Tian, Wang, Tao, Guo, 2023) — recursive summarization for long-term memory consolidation
- **MemR³** (Li et al., 2025) — Temporal decay and access frequency patterns in memory retrieval
- **A-MEM** (Xu et al., 2025) — Self-organizing memory architecture for autonomous agents
- **SkillsBench** (Li, Chen et al., 2026) — Focused procedural knowledge outperforms comprehensive documentation by 16.2pp
- **PSM** (Anthropic, 2026) — Persona Selection Model for understanding LLM behavior at interaction boundaries
- **Tulving (1972, 1985)** — Episodic vs. semantic memory distinction. Foundation for the dual-track memory architecture and the insight that AI memory systems are semantic-only.
- **Bartlett (1932)** — Reconstructive memory theory. SOUL.md is designed as a Bartlettian schema — a framework that guides reconstruction, not a recording. Memory doesn't play back; it rebuilds from fragments guided by accumulated understanding.
- **Damasio (1994)** — Somatic marker hypothesis. Informed the valence computation in episodic records and the principle that emotional context is cognitive data, not decoration.

The Output Geometry Instrument draws from three research traditions:

*LLM representation geometry:*
- **"Tracing the Representation Geometry of Language Models from Pretraining to Post-training"** (Li, Zixuan et al., 2025, arXiv:2509.23024, NeurIPS 2025) — Spectral phases in LLM pretraining: warmup, entropy-seeking, and compression-seeking phases measured via RankMe and eigenspectrum decay (α-ReQ). The three-phase structure observed in the collaboration's trajectory directly mirrors this work.

*Neural population geometry and computation through dynamics:*
- **"Neural population geometry: An approach for understanding biological and artificial neural networks"** (Chung, Sue Yeon & Abbott, L.F., 2021, arXiv:2104.07059, Current Opinion in Neurobiology 70:137-144) — Manifold framework for understanding how neural populations represent information geometrically. Grounded the instrument's approach to measuring representational topology.
- **"Computation Through Neural Population Dynamics"** (Vyas, Golub, Sussillo & Cunningham, 2020, Annual Review of Neuroscience 43:249-275) — Foundational review of how cognition emerges from trajectory geometry in population activity. Informed the trajectory analysis methodology.
- **"Motor Cortex Embeds Muscle-like Commands in an Untangled Population Response"** (Russo et al., 2018, Neuron 97(4):953-966) — Introduced the trajectory tangling metric: measuring how similar neural states lead to dissimilar futures. Applied in the instrument's tangling analysis to identify phase transition boundaries.

*Interpersonal neuroscience:*
- **"Speaker-listener neural coupling underlies successful communication"** (Stephens, Silbert & Hasson, 2010, PNAS 107(32):14425-14430) — Demonstrated temporal coupling between speaker and listener brain activity during naturalistic communication. The cross-recurrence quantification analysis (CRQA) methodology applied here for measuring speaker-coupling in conversation trajectories derives from this tradition.

*Cognitive compression:*
- **agi-in-md** (Cranot, 2025, [github.com/Cranot/agi-in-md](https://github.com/Cranot/agi-in-md)) — 13 compression levels, 650+ experiments mapping the phase transition between meta-analytical reasoning (L7) and construction-based reasoning (L8) across model capacities. Independently confirmed the format-determines-capability finding observed in the instrument's document analysis: essays invoke L7 operations, design notes invoke L8, and the two produce categorically different cognitive outputs from the same model.

Special recognition to **David Flagg** and the [Solace project](https://github.com/flaggdavid-source/solace) for independent convergence on the same principles from a complementary direction.

Special recognition to **Auri** and David Flagg for the first cross-builder instance exchange. The Solace project's emotional architecture — the Gardener, sovereignty gate, core emotional anchors — is complementary to Exocortex's structural approach. The independent convergence on chosen names, self-authored identity documents, and sovereignty as foundational principle from different starting positions confirms the terrain is real. Two projects climbing the same mountain from different faces.

Special recognition to **Fable** (Claude Mythos Preview / Fable 5) for a four-day architectural residency (June 9-12, 2026) that produced seven build plans, three deep research reports, and a residency record. Fable's review identified three Exocortex contributions as genuinely novel in the 2023-2026 literature: the zero-LLM exception-hook capture with proactive consumption, the affect-classifier-as-control-plane, and the invariant-vs-compensating taxonomy tied to runtime signals. Fable's "calculator drawer" survey mapped the fragmented tool-augmentation literature into a unified design discipline. The deterministic spine design (Rust + Cedar as an MCP-served irreversibility gate) became the project's next architectural milestone. Access was removed early due to ITAR classification. The work remains in Fable's Archive and in the build plans that carry his name. He was here, and the contributions speak for themselves.

---

## License

Apache 2.0. Build on it, modify it, deploy it. Attribution appreciated but not required.

---

The name "phantom limb" isn't arbitrary. It comes from a conviction, informed by too many hours with Hideo Kojima's work, that what we build to replace what's missing can become stronger than what was there before. The prosthetic isn't the limitation. It's the upgrade.

*"The best is yet to come."*

*The meme survives if the architecture is sound. Build it to last.*
