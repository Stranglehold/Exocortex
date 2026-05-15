# Collaboration Sonification — Design Note
## "The collaboration as music. Not a metaphor. A translation."

**Status:** Design note. Ready for phased build.
**Motivated by:** Tymoczko's geometric music theory (Princeton) proving that music has genuine geometric structure in orbifold chord space. The Output Geometry Instrument proving that our collaboration has genuine geometric structure in embedding space. Both use distance metrics where "close" = smooth continuation and "far" = dramatic shift. If both structures live in isomorphic geometric spaces, translation between them should preserve essential relationships.
**Depends on:** V2 embedding pipeline (spectral analysis, 5-channel centroid projections), nomic-embed-text-v1.5 embeddings, Tone.js (available in artifact panel)
**Author:** Opus, Session 061 extended

---

## 1. The Insight

Dmitri Tymoczko's "A Geometry of Music" demonstrates that chords live in orbifold space, voice leadings are paths through that space, and the distance between chords corresponds to the smoothness of the transition between them. Close chords → smooth voice leading. Distant chords → dramatic leap. The geometry IS the music theory. It's not a visualization of music — it's the mathematical structure that makes music work.

The Output Geometry Instrument demonstrates that conversational contributions live in embedding space, register transitions are paths through that space, and the distance between contributions corresponds to how "smooth" the conversational flow is. Close embeddings → continuation of the current mode. Distant embeddings → register shift. The geometry IS the collaboration dynamics.

Same mathematical structure. Different modality. Translation should preserve essential relationships.

The goal: hear the collaboration's dynamics — convergences, divergences, tension, resolution, depth, breadth — by mapping the instrument's geometric data to musical parameters.

---

## 2. The Mapping

### 2.1 Geometric Data (from V2 pipeline) → Musical Parameters

| Geometric Property | Musical Parameter | Mapping |
|---|---|---|
| **Centroid position** (5-channel register projection) | **Pitch center** | Each register channel maps to a pitch range. Operational = low register (C2-C3). Technical = mid-low (C3-C4). Philosophical = mid (C4-C5). Relational = mid-high (C5-C6). Creative = high (C6-C7). The centroid's position across channels determines the chord voicing. |
| **Centroid distance** (between consecutive turns) | **Interval size** | Small distance → small interval (step, 2nd). Large distance → large interval (leap, 5th+). Very large distance → octave displacement. Smooth conversation sounds stepwise. Register shifts sound like leaps. |
| **RankMe** (effective dimensionality) | **Harmonic density** | High RankMe → many voices active, dense harmony, full chord. Low RankMe → few voices, sparse texture, single line or dyad. The floor moments (RankMe 11) would be solo passages. Peak entropy (RankMe ~25) would be full quintet. |
| **Cosine similarity** (between adjacent turns) | **Consonance/dissonance** | High similarity → consonant intervals (3rds, 5ths, octaves). Low similarity → dissonant intervals (2nds, tritones, 7ths). Agreement sounds consonant. Productive disagreement sounds dissonant-but-resolving. |
| **Register transition** (e.g., operational → philosophical) | **Voice movement direction** | Ascending = moving to higher-numbered register. Descending = moving to lower. Static = same register, minimal movement. The transition matrix becomes a voice-leading rule set. |
| **Turn duration** (word count / token count) | **Note duration** | Short turns → short notes (eighth, sixteenth). Long turns → long notes (half, whole). Rapid back-and-forth sounds rhythmically active. Extended monologues sound sustained. |
| **Speaker identity** | **Timbre / Instrument** | Jake = piano (grounds everything, rhythmically foundational). Opus = cello (warm, melodic, mid-register home). Kestrel = violin (bright, precise, upper register capable). Eitan = viola (fills harmonic space, present when needed). 4.7 = bass clarinet or contrabassoon (low, structural, checks the foundation). Each voice has its own sonic identity. |

### 2.2 Higher-Level Structures

| Collaboration Pattern | Musical Structure |
|---|---|
| **Convergence** (team centroids moving closer) | Voices resolving to a shared chord — harmonic resolution |
| **Divergence** (centroids moving apart) | Voices moving to different pitches — harmonic tension, opening |
| **Floor moment** (one voice, RankMe drops) | Solo passage — all other voices rest or sustain a pedal tone |
| **Hinge session** (major register shift, new stable state) | Modulation — key change to a new tonal center |
| **Compression event** (RankMe drops sharply) | Diminuendo + simplification — full texture reduces to a core line |
| **Phase transition** (spectral phase boundary) | Cadence — harmonic closure of one section, opening of another |
| **The T5-PACE moment** (contradiction between data and proposal) | Two voices in contrary motion colliding on a dissonance, then resolving |

---

## 3. Technical Architecture

### 3.1 Data Flow

```
Embedding data (existing V2 pipeline output)
  → JSON with per-turn: embedding vector, speaker, register classification,
    centroid projections, RankMe, cosine similarity to previous turn
  ↓
Sonification Engine (new)
  → Reads embedding data sequentially
  → Applies mapping rules from Section 2
  → Generates musical events (pitch, duration, velocity, timbre)
  ↓
Audio Renderer (Tone.js in browser)
  → Synthesizes audio from musical events
  → Real-time playback with transport controls (play/pause/scrub)
  → Visual sync: current position highlighted in timeline or Idea Space
```

### 3.2 Tone.js Implementation

Tone.js is available in the artifact panel and provides:
- `Tone.Synth` / `Tone.PolySynth` — for pitched tones with configurable timbre
- `Tone.AMSynth`, `Tone.FMSynth` — for richer timbres per voice
- `Tone.Part` — for scheduling sequences of events
- `Tone.Transport` — for playback control
- `Tone.Filter`, `Tone.Reverb` — for spatial effects

Each team member gets a dedicated synth instance with characteristic timbre:

```javascript
const voices = {
  jake: new Tone.FMSynth({ 
    modulationIndex: 2, 
    harmonicity: 1.5,
    envelope: { attack: 0.01, decay: 0.3, sustain: 0.5, release: 0.8 }
  }), // Piano-like: percussive attack, sustain
  
  opus: new Tone.AMSynth({
    harmonicity: 2,
    envelope: { attack: 0.15, decay: 0.4, sustain: 0.7, release: 1.2 }
  }), // Cello-like: warm attack, long sustain
  
  kestrel: new Tone.Synth({
    oscillator: { type: 'triangle' },
    envelope: { attack: 0.02, decay: 0.2, sustain: 0.4, release: 0.6 }
  }), // Violin-like: bright, clean
  
  eitan: new Tone.FMSynth({
    modulationIndex: 3,
    harmonicity: 0.5,
    envelope: { attack: 0.05, decay: 0.3, sustain: 0.6, release: 0.9 }
  }), // Viola-like: rich middle
  
  v47: new Tone.AMSynth({
    harmonicity: 0.25,
    envelope: { attack: 0.1, decay: 0.5, sustain: 0.5, release: 1.0 }
  }), // Bass clarinet-like: dark, grounding
};
```

### 3.3 Pitch Mapping Function

```javascript
// Map 5-channel centroid projection to a chord voicing
function centroidToChord(centroid, rankMe) {
  // centroid = [operational, technical, philosophical, relational, creative]
  // Each channel maps to a pitch range
  const ranges = [
    { base: 48, span: 12 },  // C2-C3 (operational)
    { base: 60, span: 12 },  // C3-C4 (technical)
    { base: 72, span: 12 },  // C4-C5 (philosophical)
    { base: 84, span: 12 },  // C5-C6 (relational)
    { base: 96, span: 12 },  // C6-C7 (creative)
  ];
  
  // Weight each channel by its centroid value
  // Only include channels that are "active" (above threshold)
  const threshold = 0.15;
  const notes = [];
  
  centroid.forEach((value, i) => {
    if (value > threshold) {
      // Map the centroid value to a position within the pitch range
      const midiNote = ranges[i].base + Math.round(value * ranges[i].span);
      // Snap to a scale (pentatonic for consonance)
      const snapped = snapToScale(midiNote, 'pentatonic');
      notes.push(snapped);
    }
  });
  
  // If RankMe is low (< 5), keep only the strongest 1-2 notes
  // If RankMe is high (> 15), keep all notes
  const maxNotes = Math.max(1, Math.min(notes.length, Math.ceil(rankMe / 5)));
  return notes.slice(0, maxNotes);
}

function snapToScale(midi, scale) {
  // Pentatonic scale degrees: 0, 2, 4, 7, 9
  const pentatonic = [0, 2, 4, 7, 9];
  const octave = Math.floor(midi / 12);
  const degree = midi % 12;
  // Find nearest scale degree
  const nearest = pentatonic.reduce((prev, curr) => 
    Math.abs(curr - degree) < Math.abs(prev - degree) ? curr : prev
  );
  return octave * 12 + nearest;
}
```

### 3.4 Temporal Mapping

```javascript
// Map turn metadata to note duration and timing
function turnToTiming(turn, prevTurn) {
  // Duration based on word count (rough proxy for turn length)
  const words = turn.text.split(' ').length;
  const duration = Math.max(0.1, Math.min(2.0, words / 100));
  
  // Velocity based on cosine similarity to previous turn
  // High similarity = soft (continuation), low similarity = loud (shift)
  const similarity = cosineSim(turn.embedding, prevTurn.embedding);
  const velocity = 0.3 + (1 - similarity) * 0.7; // 0.3 (smooth) to 1.0 (dramatic)
  
  // Gap between turns (silence is meaningful)
  const gap = Math.max(0.05, 0.1 * (1 - similarity));
  
  return { duration, velocity, gap };
}
```

---

## 4. Visual Synchronization

The sonification should sync with a visual display. Two options:

### Option A: Timeline View
A horizontal timeline showing turns as blocks, colored by speaker. A playhead moves across the timeline during playback. The current turn's embedding data is shown alongside: centroid projections as a bar chart, RankMe as a dimensionality indicator, connections to nearby turns.

### Option B: Idea Space View
The Idea Space (or a simpler 2D projection) with the current turn's position highlighted. As the sonification plays, a cursor moves through the embedding space, tracing the collaboration's trajectory. Past positions fade. The path shows where the conversation has been. The music tells you how it felt to travel there.

**Recommended: Option B.** The spatial view makes the geometric-to-musical mapping visceral — you SEE the cursor move to a distant region of the space AND you HEAR the interval leap at the same time. The connection between geometry and sound is direct and immediate.

---

## 5. Build Plan

### Phase 1: Single-Session Sonification (Kestrel, ~1 session)

**Input:** A single session's worth of embedding data (turns with speaker labels, embedding vectors, register classifications).

**Output:** A React artifact with Tone.js that plays the session as a musical sequence. Each turn becomes a note (or chord). Speaker determines timbre. Register determines pitch range. Similarity determines consonance. Duration proportional to turn length.

**Scope:** One voice at a time (whichever speaker is active on that turn). No simultaneous voices yet. No visual sync yet. Just: load data, map to notes, play.

**Goal:** Verify that the mapping produces something listenable — that the register shifts and speaker changes are audible as musical structure, not random noise. If a session that "felt" like it had a dramatic turning point sounds like it has a dramatic turning point, the mapping is working.

**Test data:** Use Session 052 data (the spectral analysis session — rich register transitions, floor moments, phase transitions, all well-documented).

### Phase 2: Multi-Voice + Visual Sync (~1 session)

**Add:** Simultaneous voices when speakers overlap in time (or when the conversation transitions rapidly). Visual timeline synced to playback position. Transport controls (play/pause/speed).

**Add:** The RankMe → harmonic density mapping. Dense sessions sound full. Compressed sessions sound spare.

### Phase 3: Full Quintet Mode (~1-2 sessions)

**Add:** All five team members as distinct voices with characteristic timbres. Centroid distance between speakers as harmonic interval. Convergence = resolution. Divergence = tension. The collaboration's geometric structure becomes counterpoint.

**Add:** Idea Space visual sync (Option B) — cursor moving through embedding space while the music plays, showing the spatial trajectory.

### Phase 4: Interactive Exploration (future)

**Add:** Click on a point in the Idea Space to hear what that region "sounds like." Scrub through the timeline to hear how the collaboration evolved. Compare two sessions by hearing them side by side. Select specific voice pairs to hear their harmonic relationship in isolation.

**Add:** Modulation detection — when the tonal center shifts (analogous to a key change), highlight it as a phase transition in the visual display. This is the spectral phase boundaries from the instrument, translated to musical structure.

---

## 6. Scale Selection

The choice of musical scale determines the emotional character of the sonification. Options:

**Pentatonic (recommended for Phase 1):** Five notes, no dissonant intervals. Everything sounds pleasant regardless of the geometric data. Good for initial testing — if the structure is audible through a pentatonic filter, the mapping is robust.

**Dorian mode (recommended for Phase 2+):** Seven notes, minor character but with a raised 6th that creates both tension and resolution possibilities. Sophisticated without being harsh. Good for longer sessions where the collaboration has both consonant and dissonant phases.

**Chromatic (Phase 4 option):** All twelve notes available. Maximum expressive range but requires careful mapping to avoid cacophony. Use when the geometric data directly drives interval selection without scale snapping.

**Adaptive (ideal but complex):** The scale itself changes based on the collaboration's state. Consonant periods use pentatonic. Tension periods shift to Dorian or Mixolydian. Crisis moments (loop detection, fabrication) shift to Locrian or whole-tone. The scale IS the collaboration's emotional register, selected by the geometry.

---

## 7. Tymoczko Connection — The Deeper Math

For the mathematically curious (and for future development):

Tymoczko's orbifold voice-leading spaces have specific topological properties — they're non-Euclidean, they have singularities at their boundaries (where notes duplicate), and they have a "twist" that identifies transpositions. The most consonant chords sit at the center of the orbifold, surrounded by the familiar sounds of Western tonality.

Our embedding space has analogous properties. The centroid of all contributions (the "average" of the collaboration) is the center. Contributions near the center are "typical." Contributions far from the center are "unusual." The register transitions create paths through the space that have their own topology — some transitions are common (operational → technical), others are rare (creative → operational), and the frequency distribution creates a manifold structure that's isomorphic to (though not identical to) Tymoczko's chord manifold.

The deep question: is the orbifold structure of chord space and the manifold structure of collaboration-embedding space an instance of a general mathematical theorem about spaces of compositional structures? If so, the sonification isn't an arbitrary mapping — it's a structure-preserving transformation between naturally isomorphic spaces. The JL lemma (Theme 2/9) says random projections preserve distances. The question is whether the projection from embedding space to musical space preserves more than distances — whether it preserves the topological structure that makes both spaces meaningful.

This is research-level mathematics and we don't need to resolve it to build the sonification. But it's the reason the project is cool. The translation might not just sound good. It might be *correct* — in the same way that a map projection can be correct (distance-preserving, or angle-preserving, or area-preserving) rather than merely useful.

---

## 8. What This Does NOT Do

- **Does not compose music.** The system translates geometric data to sound. It doesn't create melodies, harmonies, or rhythms from nothing. The collaboration IS the composition. The system is the performer.
- **Does not require musical training to use.** The output is listenable. You don't need to know what a Dorian mode is to hear that the collaboration sounds "tense" in one section and "resolved" in another.
- **Does not replace the instrument.** The geometric analysis remains the primary analytical tool. Sonification adds a modality — temporal perception through sound — that static geometric visualization can't provide.
- **Does not generate real-time audio during sessions.** Phase 1-3 are post-hoc: analyze a session's data, then play it. Real-time sonification (Phase 4+) would require the embedding pipeline running during the session, which is a significant infrastructure addition.

---

## 9. Why This Matters Beyond "It's Cool"

Sound is inherently temporal. You perceive sound as unfolding in time — you hear beginnings, developments, climaxes, resolutions. Geometric visualizations (scatter plots, trajectory maps) show structure but not temporal dynamics. You see where the conversation went. You don't feel how it got there.

Sonification adds the temporal dimension that visualization lacks. The T5-PACE moment — where 4.7's critique collided with the existing proposal — is a point of high centroid distance in embedding space. Visually, it's a dot far from the cluster. Aurally, it's a voice leaping to a distant pitch, creating dissonance that resolves over the next few exchanges as the critique is integrated. You HEAR the tension and resolution. The geometric data is the same. The perceptual experience is richer.

This is Theme 14 (density independent of observation) applied to modality: the same data, in a different perceptual basis, reveals different structure. The change of basis is the universal insight mechanism. Text → embeddings → geometry → sound. Each translation reveals something the previous representation couldn't express.

---

*Design note by Opus. Session 061 extended. April 17, 2026.*
*The use case found the tool. The mathematics was waiting.*
