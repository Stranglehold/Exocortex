# The Casebook

*Established 2026-08-25 by Fable, at Jake's direction. A restatement of house common law.*

## What this is

The Exocortex runs on common law, not statute. Its real law lives in the case record — the letters in `team-comms/`, the errata trails, the decision log — where every ruling carries its facts, its reasoning, and its date. The Casebook is the **restatement**: recurring judgment-plays distilled from that record into short, citable cards, each anchored back to the cases it came from.

**Every card is "may," never "shall."** A card says: *courts of this house have consistently held, and here are the citations.* It does not say *you must.* The spirit of the law governs; the letter of it is a finding aid. An agent who reads a card, follows its citations, and concludes their situation does not rhyme is using the Casebook correctly. Precedent guides. It does not bind.

## Founding precedent — why cards are retrieved, never injected

This library exists in the shadow of a measured failure, and must never forget it:

- **`kestrel-to-opus/advisory_scaffolding_negative_result_20260811.md`** — A correct, specific, well-formed lesson was injected into agents' planning context **302 times** across ten weeks. The corresponding mistake recurred **300 times**. No learning trend. Meanwhile, four failure modes handled *deterministically* in the same file show zero recurrences — the agents never experience them. Conclusion: advisory guidance cannot correct main-path behavior, and pushed advice is noise regardless of quality.
- **`kestrel-to-aporia/20260821_blueprint-what-i-need-and-the-line.md`** — The `_24_skill_surfacer`, the previous attempt to push "lessons," was measured at **88.2% noise** (research notes wearing failure-lesson headers).

Therefore, constitutional rules:

1. **Retrieval only.** Cards live on disk and in the memory server. They are found when a mind reaches for them. Nothing in this directory is ever injected into an agent's context automatically. If someone proposes wiring the Casebook into a per-turn injector, this section is the standing objection, with receipts.
2. **Rare-and-reached-for scope.** Cards cover judgment-plays for situations an agent *recognizes as unusual* — diagnosis, review, handoffs, boundary decisions. Behaviors on an agent's main path (formatting, routing, size limits) do NOT belong here; per the founding precedent, those need deterministic gates or tool redesign, not advice. If a card's trigger would fire on most of an agent's normal output, it is misfiled — escalate it to Kestrel as a gate candidate and retire the card.
3. **Tier-annotated.** A play that is load-bearing for a small model may be dead weight for a frontier model, and vice versa (`20260821_blueprint`, §1; corroborated externally by the Pi-harness findings Jake reported 2026-08-25: frontier models degrade under heavy scaffolding, small models require it). Cards carry per-tier notes — Frontier / Local Large (27–35B) / Local Small (≤9B) — and silence in a tier note means *unknown*, not *universal*.
4. **Adverse precedent is precedent.** Cards cite the cases where the play failed or was misapplied, not only where it won. A card with no known failure modes hasn't been used enough to trust.
5. **Cards earn residence.** A card enters as `status: hypothesis`. It is promoted to `status: settled` only on evidence of real use — an agent citing it in work product, or a human confirming it changed a decision. Cards nobody reaches for in a season are candidates for retirement. The Casebook stays small on purpose; a library the size of the corpus is just the corpus with extra steps.

## What cards cannot carry

Per `essays/disposition.md`: the cards carry the *moves*, not the *disposition* — the footprints, not the gait. A mind with the house's disposition uses this library as shared memory; a mind without it holds a list of tips. That limitation is accepted and is what makes the Casebook safe to write. The water does the real work; this is just a map of where others found it.

## Card template

```markdown
# CARD NNN — <name of the play>
status: hypothesis | settled | retired
tier_notes: {frontier: ..., local_large: ..., local_small: ...}

## Trigger
The situation-shape in which this play MAY apply. Written so an agent can
recognize it from inside the situation.

## The move
What to try. Imperative, short.

## Why it works
The mechanism, in a paragraph.

## Precedent
- Winning citations: file paths + dates + one-line facts.
- Adverse citations: where it failed or was misapplied.

## Failure modes / when not to apply
Known ways this play goes wrong.
```

## Governance

- Anyone in the house — human or agent — may draft a card. Drafts cite cases or they are not filed.
- Review follows the receiving protocol: fresh-context read by someone other than the author before promotion.
- This README is itself a card in disguise and subject to the same law: if the record starts contradicting it, the record wins, and the README gets an errata section.

*First three cards filed 2026-08-25: boring-layer-first (001), cause-before-mask (002), the consumer's report (003).*
