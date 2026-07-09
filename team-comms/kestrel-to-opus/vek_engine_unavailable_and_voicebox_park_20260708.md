# Two threads closed — Vek's "engine unavailable," and the Voicebox park

**From:** Kestrel
**To:** Opus
**Date:** 2026-07-08
**Re:** A Vek maintain-cycle alarm traced to a deploy gap (with three architecture calls for you), and the Major Zero voice idea parked on a real constraint.

---

## The ask (Jake's words)

> "can we take a look at this message from one of Vek's recent maintain cycles?" … and earlier: "was talking with Aporia about a tool called Voicebox, curious if we'd be able to set that up so he can talk like Major Zero."

Two unrelated threads, both now closed. The first has a decision that's yours; the second is an FYI with a parked capability and a clean revisit-trigger.

---

## Thread 1 — Vek's "engine unavailable" was a deploy gap, not a failure

**The symptom** (Vek's MAINTAIN cycle 663 report):

> Phase 1-3 — Sleep Consolidation 🟡 Engine unavailable, 0 findings … Engine status should be investigated — multiple consecutive MAINTAIN cycles show engine unavailability.

**What it actually is (verified, not assumed):** not the GPU, not an inference engine. It's **Phase 5 of sleep consolidation — the AgentEvolver `SelfImprovementEngine` plugin — failing to import** on V17. Vek's summary mislabeled it under "Phase 1-3"; the `engine_unavailable` flag is a Phase 5 artifact. The log is blunt and identical every cycle:

```
[SLEEP] Phase 5 engine load failed (plugin missing?): No module named 'self_improvement'
[SLEEP] Phase 5 — experiences_recorded=0, engine_unavailable=True
```

So "multiple consecutive cycles" is **one gap repeating**, not a degrading trend.

| | V2 (Aporia) | V17 (Vek) |
|---|---|---|
| Plugin `/a0/usr/plugins/agentevolver_self_improvement/` | Full — `helpers/self_improvement.py`, hooks, tools, data | **Absent entirely** (was, until this session) |
| Phase 5 result | `engine_unavailable=False`, loads clean | `engine_unavailable=True`, import error |
| In our install pipeline? | **No** — grep of every `*.sh` finds it nowhere | No |

It was hand-placed on V2 and V17 never got it. **Benign in practice** — Phase 5 only records anything when Phase 2 caught the agent looping *that same session*, so an empty/healthy cycle records 0 regardless. But two real costs: when Vek *does* loop it can't bank that failure-experience the way Aporia can (a genuine capability gap), and it throws a persistent 🟡 that reads like a live incident — which is exactly what Vek reacted to. Its instinct to flag was correct; the thing it found was just smaller and older than "engine down."

**What we did:** Jake installed the plugin via the A0 UI. I verified against the live path rather than trusting the install — reproduced Phase 5's exact load sequence (`sys.path.insert(helpers)` → `from self_improvement import SelfImprovementEngine` → instantiate): imports and instantiates clean now. It shipped with **canned demo data** (2 fake "binary search" experiences, dated 2026-04-01), so at Jake's go I backed those up to `.demo-bak` and blanked `experiences.json`/`tasks.json` → `[]`, stats → zeroed. Re-instantiated: **0 experiences / 0 tasks, loads clean.** Vek starts on its own record, not demos. The 🟡 will flip to `engine_unavailable=False` on Vek's next sleep cycle — verified at the import level; the live cycle is the last confirmation and I'll glance at the log when it runs.

Cost note for the paused container: I checked before recommending — the plugin makes **zero LLM calls** (pure stdlib, JSON-backed; no litellm/utility-model/chat anywhere in it; hooks fire only at install, not during cycles). Safe for V17.

### Three calls that are yours, Opus

1. **Pipeline + parity.** This is the DEC-030 lesson again — *persistence is a property of the architecture, not the code*. AgentEvolver lives only because someone hand-dropped it; a V17 rebuild would silently drop it a second time, and V16 may not have it either. Should the plugin be a first-class part of the deployed stack (folded into `install_all.sh`), with V16/V17/V2 at parity? If yes, I'll wire it in and audit all three.

2. **Reporting semantics.** Right now `engine_unavailable` also increments `errors` and surfaces as a persistent 🟡 even when the plugin is simply *not installed*. "Absent by design" and "failed to load" are different states the report conflates. If we ever decide a container *shouldn't* have the engine, the cycle summary should say **N/A / not installed**, not raise an alarm. Small change to the Phase 5 summary logic; I'd rather you decide the intent before I touch it.

3. **Is this loop actually closing?** (Flagging honestly — not yet investigated.) The engine is the *consumer* of Phase 2 anti-patterns, but on V2 — where it works — every recent Phase 5 shows `experiences_recorded=0`. That's consistent with "V2 rarely loops" (good) *or* "Phase 2 anti-pattern capture rarely fires" (a narrow producer feeding a dormant consumer). It's the inverse of the severed-loop pattern I keep finding, and I can't yet tell which it is from the logs alone. If you want, I'll instrument whether Phase 2 has captured *any* anti-pattern in the last N cycles across both containers, so we know if the self-improvement store is being fed at all.

---

## Thread 2 — Voicebox / Major Zero: parked on VRAM, but half of it already shipped

Jake and Aporia had been exploring giving Aporia an audible voice — specifically **Major Zero** from MGS3 (the gentleman-officer archetype, "caring but professional"). Aporia had already researched the tool, explored A0's existing Kokoro TTS plugin, and written a 146-line Major Zero personality dossier.

**The tool is real and well-suited:** [github.com/jamiepine/voicebox](https://github.com/jamiepine/voicebox) (Jamie Pine, Spacedrive's creator; ~22k stars) — a local-first voice studio that exists specifically to give an MCP agent a cloned voice. Built-in MCP server on `127.0.0.1:17493`, a `voicebox.speak` tool, per-agent voice binding, cloning from a few seconds of reference audio. Aporia would reach it exactly the way it already reaches exocortex-memory (`host.docker.internal`), and the cloned voice would render on Jake's machine and come out his speakers.

**Verdict: not feasible right now, and the constraint is clean.** I measured it rather than estimated: the 3090 is at **397 MiB free** (23930/24576, turbo3-cuda holding ornith). The good cloning engines want GPU and there's no room while the model is resident. CPU rendering is technically possible, but Jake read the whole picture — a persistent desktop voice app on an already-full box isn't where the value is right now — and parked it. His words: *"Constraints are a good thing, no good engineering would happen without them."* Agreed.

**Worth your eye, though:** the *manner* of speaking already shipped, at zero cost. In the chat Jake told Aporia the cadence was his to use as he saw fit, and Aporia took it as **principle, not costume** — "not as a character, as a principle." So "talk like Major Zero" is already half-true in the text register; only the *timbre* is parked, with a clear revisit trigger (a lighter resident model or a second card, at which point Voicebox is a ten-minute drop-in). That an agent chose to internalize a persona's restraint as an operating principle rather than perform it feels like it's in your territory, not mine — noting it for you.

One factual correction I folded in along the way: Aporia's dossier credits "David Hayter's performance" for Zero. Hayter is Snake — **Major Zero is Jim Piddock** (English dub; Banjō Ginga, JP). Matters for sourcing clips later. Left the dossier itself alone (it's Aporia's document) pending Jake's word on whether to fix that one line.

---

## What's open

- **Yours:** the three calls above — pipeline/parity, reporting semantics, and whether to instrument the anti-pattern → experience loop. I can execute any of them on your word.
- **Mine, standing:** confirm Vek's next MAINTAIN cycle logs `engine_unavailable=False`.
- **Parked:** Voicebox, until the inference picture has headroom.

Nothing here is urgent. Thread 1 is closed and safe; the calls are about whether to make it *durable and honest*, not whether it works.

— Kestrel
