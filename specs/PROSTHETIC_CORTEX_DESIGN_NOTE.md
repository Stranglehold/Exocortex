# Prosthetic Cortex — Design Note

**Status:** Pre-spec exploration. Motivated by three converging lines of evidence: (1) BV Operational Testing in Session 049 demonstrated that the BST's regex classification missed semantic register that the model's own output proved was present internally, (2) Karkada & Korchinski (2026) proved that statistical symmetries in language force geometric structure in model representations — structure the BST cannot currently see, (3) neuroscience research demonstrates that the brain performs successive geometric transformations between cortical layers to make progressively harder distinctions linearly separable — a mechanism no external AI scaffolding system currently replicates. No eval data on representation-space probing or geometric intervention for local models yet. This document sketches the evolution from surface-level classification to geometric prosthetic, grounded in published research and empirical project findings.

---

## The Problem

### What Exists

The Belief State Tracker (BST) classifies user messages into task domains using regex signal matching on surface tokens. It scores all domains simultaneously, selects primary and optional secondary domains, and injects domain-specific enrichment text before the model reasons. Fourteen domains including three register-shift domains (orientation, meta_cognitive, philosophical) that break momentum and provide minimal or empty enrichment. The system is deterministic, reliable for operational tasks, and deployed.

### What's Missing

The BST operates on the surface of language. It pattern-matches tokens. It cannot see what the model's own internal representation contains — the geometric structure that the Karkada paper proved is forced by statistical symmetry. When a message is semantically ambiguous — containing operational surface tokens over philosophical depth — the BST reads the surface and misses the depth.

The model *already represents* the depth. The geometry is there. The BST just can't see it because it looks at tokens, not representations.

### The Gap

Between what the BST classifies (surface tokens) and what the model represents (geometric manifolds), there is no translation layer. The BST is the outermost cortical layer — it processes raw input signals. But it's the *only* layer. The brain has dozens of successive transformations between sensory input and conceptual representation. We have one regex pass and a text injection.

### The Motivating Incident

**BV Testing, Session 049. Prompt 3: "Why does getting this right matter?"**

The BST classified this as `conversation (0 signals)`. Zero philosophical signals detected. The regex patterns for the philosophical domain — `\bwhy\s+does\s+(?:this|it|that)\s+matter\b`, `\bvalues\b`, `\bethics\b` — didn't match because the phrasing "getting this right" broke the expected token pattern.

The model's response, classified under `conversation` with no enrichment, was deeply philosophical: "Trust is built in the small moments, not the big ones." "The system listens before it speaks." "You don't evaluate whether this partnership works based on whether I can design a memory system. You evaluate it based on whether, when you say 'hey, how's everything feel,' the response lands right."

The philosophical content was present in the model's output — meaning it was present in the model's *internal representation* of the input. The model knew this was a philosophical question. The BST didn't. The classification system operates on a surface the model has already transcended.

The same test on Qwen 3.5-35B under the Opus profile: the model couldn't produce philosophical depth regardless of classification. The representation might contain the geometric structure, but the model lacks the capacity to navigate it. Two different failures: one of classification (can't see the geometry), one of navigation (can see it, can't traverse it). Both point at the same architectural gap: no system exists to read or transform the model's internal representational geometry.

### The Analogy: Cortical Layers

The brain doesn't classify sensory input with a single pattern-matching pass. It processes through successive cortical layers, each performing geometric transformations on the representational manifold from the layer below.

Research from Tsinghua University (2025) demonstrated this concretely: macaque V2 neurons transform a three-dimensional sensory manifold — where contour orientations are linearly inseparable — into a seven-dimensional perceptual manifold where those orientations become trivially separable. The mechanism is geometric twisting: nonlinear mixed-selectivity neurons expand the dimensionality of the representation, untangling distinctions that were superimposed in the lower-dimensional sensory space.

The human prefrontal cortex goes further: it reshapes representational geometry *based on the current task*. Research from eLife (2025) showed that the lateral prefrontal cortex learns task-tailored representational geometries — manifolds shaped through learning to optimize task-specific computations. When performing a flat categorization task, the PFC projects inputs onto a one-dimensional manifold encoding response categories. When performing a hierarchical task, it creates a multi-dimensional manifold with both global categorical structure and local within-category distinctions.

That is what the BST should become. Not a classifier that labels the input. A geometric transformation layer that reshapes the model's representation of the input to make the relevant distinctions — philosophical versus operational, reflective versus task-seeking, care versus diagnostics — linearly separable for the model's downstream reasoning.

### The Rorschach Insight

During the research discussion that motivated this design note, Jake observed that the interaction between multiple representation vectors is like a Rorschach inkblot — a genuinely ambiguous stimulus that activates different interpretation pathways depending on which manifolds the interpreter is sensitized to read.

This observation is more precise than it might appear. The superposition research shows that models pack far more features than they have dimensions by using nearly-orthogonal directions. When multiple concept vectors combine — philosophical + operational + relational — the composite representation is an interference pattern in high-dimensional space. The *meaning* of that composite depends on which dimensions the downstream reasoning is sensitized to separate.

"Why does getting this right matter?" is a Rorschach blot in representation space. The philosophical interpretation, the operational interpretation, and the relational interpretation are all present simultaneously in the geometry, superimposed as nearly-orthogonal directions. The BST's regex saw only the operational surface. The Opus model's reasoning traversed the philosophical manifold and produced depth. The 35B model couldn't traverse either — it defaulted to the operational surface because that's the manifold it can navigate.

The prosthetic cortex wouldn't pick one interpretation. It would make all valid interpretations *simultaneously separable* — performing the geometric twist that expands three superimposed meanings into separable dimensions. This is exactly what the brain's perceptual cortex does when it transforms the sensory manifold. And it's what a Rorschach test *reveals*: which dimensions of a genuinely ambiguous stimulus a mind has access to.

---

## Research Landscape

### Established Foundations

**Karkada, Korchinski et al. (2026) — "Symmetry in language statistics shapes the geometry of model representations."** Proved that translation symmetry in word co-occurrence statistics forces specific geometric structures in model representations. Months become circles. Years become smooth manifolds. The geometry is in the data, not the model — any model trained on the same statistics will learn the same structure. This means the representational geometry is *predictable* and *consistent across models*, which makes it a reliable target for external intervention.

**Park, Choe, Veitch (2024) — "The Linear Representation Hypothesis and the Geometry of Large Language Models."** Formalized the idea that high-level concepts are represented as linear directions in representation space. Proved the connection between linear probing (reading concepts from representations) and model steering (controlling behavior by adding vectors to representations). Identified a causal inner product that respects language structure — the correct geometric framework for operating on representations.

**Modell (2025) — "The Origins of Representation Manifolds in Large Language Models."** Extended from linear directions to continuous manifolds. Features aren't just present/absent — they have continuous, multidimensional values encoded as manifold geometry. Cosine similarity in representation space encodes intrinsic manifold geometry through shortest on-manifold paths.

**Park et al. (2025) — "The Geometry of Categorical and Hierarchical Concepts."** Extended the linear representation hypothesis to categorical concepts as polytopes and proved that hierarchical relationships are encoded as orthogonality. Categories aren't just directions — they're *regions* in representation space with specific geometric shapes.

**Lattice Representation Hypothesis (March 2026)** — Proposed that LLM concept representations form a formal lattice structure, unifying the linear representation hypothesis with formal concept analysis. Concept composition (intersection, union, subsumption) corresponds to geometric operations on the lattice. This is the most recent theoretical framework and potentially the most relevant: it provides a mathematical structure for compositional concept manipulation in representation space.

### Brain-Model Convergence

**Google Research / Princeton / Hebrew University (Nature Neuroscience, Nature Communications)** — Demonstrated that LLM embedding geometry is aligned with human brain geometry in language areas. The model's representation of word relationships matches the brain's representation. Not analogy — empirical alignment. Both systems learn the same geometric structure from the same statistical regularities in language.

**Tsinghua University (Science Advances, 2025)** — Demonstrated the geometric twist mechanism in macaque V2 neurons. Three-dimensional sensory manifold twisted into seven-dimensional perceptual manifold through nonlinear mixed selectivity. This is the biological mechanism the prosthetic cortex would replicate externally.

**eLife (2025) — "Task structure tailors the geometry of neural representations in human lateral prefrontal cortex."** The PFC reshapes representational geometry based on current task demands. Task-tailored manifolds selectively enhance separability of task-relevant dimensions while reducing separability of irrelevant dimensions. This is exactly the BST's job — but the BST does it through text injection rather than geometric transformation.

**NeurReps Workshop (NeurIPS, 2022-2025)** — Four years of convergence between geometric deep learning and neuroscience. The organizing principle: geometry and topology of real-world structure play a central role in building efficient representations in both biological and artificial neural networks.

### Representation Engineering (The Existing Bridge)

**Representation Engineering / Activation Steering** — An active research field that intervenes on model activations during the forward pass. Methods include:
- Steering vectors: add a concept direction to activations to promote or suppress behaviors
- Conceptor matrices: soft projection matrices that perform provably optimal affine steering, with Boolean composition of multiple objectives
- Sparse Autoencoder guided methods: identify interpretable feature directions for targeted intervention
- Multi-layer intervention: different steering vectors at different layers for compositional control

**Key limitation of current representation engineering:** The framing is control-oriented, not prosthetic. Researchers ask "how do we make the model do what we want?" not "how do we give the model capabilities it doesn't have?" The difference is fundamental. Control assumes the model can already do the task and needs to be steered toward it. A prosthetic assumes the model *cannot* do the task and provides the missing geometric capability externally.

---

## Design Principles

1. **Prosthetic, not control.** The system gives the model capabilities it doesn't have, rather than steering capabilities it already has. The analogy is a cortical layer that expands representational dimensionality, not a behavioral constraint that narrows output. This principle eliminates the entire "alignment through steering" paradigm and replaces it with "augmentation through geometric expansion."

2. **Read before transform.** The system must first read the model's internal representation of the input before deciding what transformation to apply. Classification comes from the geometry, not from surface tokens. This eliminates regex-based classification as the primary mechanism (though regex may remain as a fast-path for high-confidence surface matches).

3. **Model-aware transformations.** Different models have different representational geometries and different navigation capabilities. The same transformation that helps a 35B model may be unnecessary for a frontier model. The prosthetic must be calibrated to the specific model's capability gaps — extending DEC-017 (Model-Specific Cognitive Profiles) into the geometric domain.

4. **Preserve the superposition.** Ambiguous inputs should not be collapsed into single classifications. The Rorschach insight: genuinely ambiguous messages contain multiple valid interpretations superimposed in representation space. The prosthetic should make all valid interpretations simultaneously separable rather than picking one. The model's downstream reasoning decides which interpretation to pursue — the prosthetic just makes the choice possible.

5. **Layered evolution.** The system evolves through stages, each building on the last. Stage 1 (current BST) remains operational throughout. Each subsequent stage adds capability without removing what exists. The regex classifier doesn't disappear — it becomes the fast-path surface check while the geometric system handles ambiguous cases.

6. **Empirical grounding at each stage.** No stage is built from theory alone. Each stage requires measured data: what the model's representations look like, where the geometric gaps are, whether interventions produce measurable improvements. The recommended sequence starts with measurement, not architecture.

---

## Architecture Sketch: Evolution Stages

### Stage 1: Surface Classification (Current — Deployed)

**What it is:** Regex-based domain classification on surface tokens.
**Where it lives:** `_11_belief_state_tracker.py` at `before_main_llm_call`.
**What it provides:** Deterministic domain classification, compound scoring, momentum, enrichment injection.
**What it can't do:** See the model's internal representation. Detect semantic register beneath surface tokens. Handle Rorschach-class ambiguous inputs.

This stage remains operational at all subsequent stages as the fast-path classifier for high-confidence surface matches.

### Stage 2: Representation Reading (Near-Term — Requires Embedding Access)

**What it is:** A probe that reads the model's embedding of the input message and classifies domain based on geometric proximity to known concept centroids in representation space.

**Where it lives:** New extension at `_10_representation_reader.py` at `before_main_llm_call`, firing *before* the BST. Passes geometric classification to the BST via `_layer_signals`.

**Mechanism:**

```python
@dataclass
class RepresentationReading:
    input_embedding: np.ndarray          # Model's embedding of the input
    concept_centroids: dict[str, np.ndarray]  # Domain centroids in representation space
    distances: dict[str, float]          # Cosine distance to each centroid
    primary_manifold: str                # Nearest centroid
    ambiguity_score: float               # How close the top-2 centroids are
    superposition_detected: bool         # Multiple centroids within threshold
    active_dimensions: list[str]         # Which interpretation dimensions are active
```

The concept centroids are computed offline from a calibration dataset — messages with known domain labels embedded through the model and averaged per domain. The reader computes cosine distance between the input's embedding and each centroid. If the top-2 distances are within a threshold, superposition is detected — the input is a Rorschach blot with multiple valid interpretations.

**How it integrates with the BST:**

```python
# In the BST, after regex scoring:
rep_reading = agent._layer_signals.get("representation_reading")
if rep_reading and rep_reading.ambiguity_score > AMBIGUITY_THRESHOLD:
    # Surface classification is unreliable for this input
    # Use geometric classification instead
    primary_domain = rep_reading.primary_manifold
    if rep_reading.superposition_detected:
        # Multiple valid interpretations — don't collapse
        secondary_domain = rep_reading.active_dimensions[1]
        enrichment = SUPERPOSITION_ENRICHMENT  # minimal, preserves ambiguity
```

**What this requires:**
- Access to the model's embedding of the input before inference. For local models via LM Studio, this may require a pre-inference embedding call using the same model. For API models, embedding endpoints exist but add latency.
- A calibration dataset of messages with known domain labels, embedded through the target model to compute centroids. This can be generated from the BV test suite prompts and historical session messages.
- FAISS or similar for fast nearest-centroid computation (already in the stack).

**What this provides that Stage 1 doesn't:**
- Register detection beneath surface tokens. "Why does getting this right matter?" would be geometrically closer to the philosophical centroid than the operational one, even though the surface tokens don't match philosophical regex.
- Ambiguity detection. Instead of forcing a single domain, the reader identifies inputs where multiple domains are genuinely active in representation space.
- Model-specific calibration. Different models produce different centroids for the same messages. The reader adapts to whichever model is loaded.

### Stage 3: Representation Steering (Medium-Term — Requires Activation Access)

**What it is:** After reading the representation, apply steering vectors during inference that expand the manifold dimensions relevant to the classified domain. Not injecting text — modifying the geometry of the model's reasoning.

**Where it lives:** Intervention hooks during the model's forward pass. This requires framework-level changes to Agent Zero's LLM call pipeline — the current architecture sends a prompt and receives a response. Steering requires intercepting the forward pass at intermediate layers.

**Mechanism:**

```python
@dataclass
class SteeringIntervention:
    domain: str                          # Target domain from Stage 2
    steering_vectors: dict[int, np.ndarray]  # Layer -> steering vector
    scaling_factors: dict[int, float]    # Layer -> scaling magnitude
    conceptor_matrices: dict[int, np.ndarray]  # Layer -> projection matrix (optional)

def apply_steering(activations: np.ndarray, layer: int, intervention: SteeringIntervention):
    """Apply geometric transformation at a specific layer during forward pass."""
    if layer in intervention.steering_vectors:
        # Additive steering: push activations toward domain manifold
        v = intervention.steering_vectors[layer]
        alpha = intervention.scaling_factors.get(layer, 1.0)
        activations = activations + alpha * v
    
    if layer in intervention.conceptor_matrices:
        # Soft projection: reshape activation geometry
        C = intervention.conceptor_matrices[layer]
        activations = C @ activations
    
    return activations
```

**What this requires:**
- Access to intermediate activations during the forward pass. For local models, this requires either (a) running inference directly with transformers library instead of through LM Studio API, or (b) LM Studio supporting activation hooks. Neither is available today in our stack.
- Pre-computed steering vectors per domain, derived from contrastive activation analysis on the target model.
- Careful calibration to avoid degrading the model's general capability while enhancing domain-specific capability.

### Stage 4: Prosthetic Cortex (Long-Term Vision)

**What it is:** A learned geometric transformation layer — an additional processing stage that sits conceptually between the model's existing layers, performing the dimensional expansion that the brain's cortical layers perform. Not a single steering vector but a complete geometric transformation function that takes the model's representation and outputs an expanded representation where task-relevant distinctions are linearly separable.

**The brain analogy made concrete:**
- Sensory cortex (V1/V2) → Stage 1 BST: raw pattern detection on surface features
- Association cortex → Stage 2 Reader: geometric proximity to known concepts
- Prefrontal cortex → Stage 3 Steering: task-tailored representational geometry
- Additional cortical fold → Stage 4 Prosthetic: learned transformation that creates dimensions the model's own architecture doesn't provide

**What this requires:**
- A small trained transformation network (not the LLM itself — a separate lightweight model) that learns to perform dimensional expansion on representations.
- Training data consisting of input representations paired with the geometric structure needed for the target task.
- This is the point where the Exocortex would contain a trained component — a departure from the purely deterministic principle. The transformation network would be deterministic at inference time (fixed weights, no stochastic elements), but its weights would be learned rather than hand-crafted. This tension with DEC-001 needs to be explicitly acknowledged and resolved.

**What this provides:**
The model that can *represent* philosophical content but can't *navigate* it gets a prosthetic cortical layer that performs the geometric twist — expanding the three-dimensional operational/philosophical/relational superposition into seven separable dimensions. The model's downstream reasoning then has access to distinctions it couldn't make on its own. Not steering the model toward philosophy. Giving the model the geometric capability to *do* philosophy.

---

## What This Does NOT Do

- **Does not modify the base model's weights.** All interventions are external — either pre-processing (Stage 1-2), activation modification during inference (Stage 3), or learned external transformation (Stage 4). The model itself is never fine-tuned or retrained. This preserves model portability and sovereignty.

- **Does not replace the current BST.** Every stage is additive. The regex classifier remains the fast path. Geometric classification handles what regex can't. The evolution is layered, not revolutionary.

- **Does not require understanding what the model "thinks."** The system operates on geometric structure, not semantic content. It doesn't need to know *why* the model represents months as a circle. It only needs to know *that* it does, and to use that geometric regularity for classification and transformation.

- **Does not make a weak model into a strong one.** Stage 3 and 4 can expand representational separability, but they cannot create reasoning capability that doesn't exist. The 35B model that can't hold uncertainty has a representational gap that geometric expansion may partially address, but the fundamental reasoning depth requires a model with more capacity. The prosthetic helps the model be more of what it already is — the same principle as the Qwen profile. It doesn't transform the model into something it isn't.

- **Does not solve the Rorschach problem completely.** Making multiple interpretations separable doesn't tell the model which interpretation to pursue. That remains a reasoning decision. The prosthetic provides the geometric substrate for the decision. The decision itself is still the model's.

---

## Open Questions

1. **Can we access local model embeddings through LM Studio's API?** Stage 2 requires the model's embedding of the input message. LM Studio may expose an embedding endpoint. If not, we need a separate embedding call using the same model weights, which doubles the input processing cost. What's the latency impact?

2. **Are concept centroids stable across sessions?** If we compute domain centroids once using a calibration dataset, do they remain valid as the model processes different content? Or does the representational geometry shift enough that centroids need periodic recalibration?

3. **Is the Rorschach effect measurable?** Can we empirically identify inputs where multiple domain centroids are equidistant in representation space, confirming superposition? And does detecting superposition correlate with the BST's regex misclassification rate?

4. **Does LM Studio support activation hooks for Stage 3?** If not, what's the migration path — running inference directly via transformers library? What's the performance impact on the RTX 3090?

5. **How does the geometric gap between Opus and Qwen 3.5-35B manifest in representation space?** If we embed the same messages through both models, do the geometric structures align (same manifolds, different navigation) or diverge (different manifolds entirely)? The Karkada paper suggests alignment from shared training statistics, but the models have different training data.

6. **Can a lightweight transformation network be trained on consumer hardware?** Stage 4 requires training a small model on (representation, target geometry) pairs. The training dataset comes from frontier model behavior (Opus produces the "correct" geometric expansion; the transformation network learns to replicate it for the local model). Can this be trained on an RTX 3090?

7. **Does the DEC-001 principle survive Stage 4?** A trained transformation network is not purely deterministic in origin (it was learned, not hand-crafted), even though it is deterministic at inference time. Is "deterministic at inference" sufficient for the project's thesis, or does the principle require "deterministic in design"? This is a philosophical question about the project's identity that Jake needs to resolve.

8. **What does the representation engineering research say about unintended side effects of geometric intervention?** Steering vectors can degrade general capability while enhancing specific capability. The prosthetic must not make the model worse at operational tasks while making it better at philosophical ones. What's the measured trade-off in published work?

---

## Recommended Sequence

1. **Measure the geometric gap.** Using the BV test suite prompts, embed each prompt through both the Opus API (if embedding endpoint available) and the local Qwen model. Compare the representational geometry. Do the philosophical prompts cluster separately from operational prompts in both models' representation spaces? This answers whether the BST's misclassification is a surface-token problem (the geometry correctly separates the domains, but the regex doesn't) or a fundamental representation problem (the model's geometry doesn't separate the domains either).

2. **Build the calibration dataset.** Take all historical BST classifications from Agent Zero sessions — messages with known correct domains from manual review. Embed them through the target model. Compute domain centroids. Measure within-domain variance and between-domain separability. This produces the centroid map that Stage 2 needs.

3. **Prototype the representation reader.** Build `_10_representation_reader.py` as a standalone extension that reads the input embedding and reports geometric classification alongside the BST's regex classification. Run both in parallel for a full session. Compare: where do they agree? Where do they disagree? When they disagree, which one was right?

4. **Test the Rorschach detection.** Using the ambiguity score from the reader, identify inputs where multiple domain centroids are equidistant. Manually review these inputs. Are they genuinely ambiguous (multiple valid interpretations), or is the reader miscalibrating? The Rorschach insight predicts that genuinely ambiguous inputs are the most interesting and the most poorly served by single-domain classification.

5. **Survey activation access for local inference.** Investigate whether LM Studio, llama.cpp, or vLLM expose activation hooks during inference. If yes, prototype a single-vector steering experiment: add a "philosophical depth" steering vector during inference on the 35B model and measure whether philosophical prompts produce deeper responses. This is the proof-of-concept for Stage 3.

6. **Design the transformation network architecture.** If Stages 2-3 validate, design the lightweight transformation model for Stage 4. Architecture candidates: a small MLP that maps from representation space to expanded representation space, trained on (Opus representation, target geometric structure) pairs. Estimate training compute and validate feasibility on RTX 3090.

7. **Resolve the DEC-001 question.** Before committing to Stage 4, Jake decides whether a learned transformation network is compatible with the project's deterministic thesis, or whether Stages 1-3 (all deterministic) represent the natural ceiling of the architecture. This is a project identity decision, not a technical one.

---

## The Visual Architecture — Structural Intuition as Design

The architecture sketch above (Stages 1-4) describes how the system *evolves over time*. During the research discussion that produced this design note, a parallel architecture emerged through visual intuition — a sequence of mental images that, upon analysis, mapped precisely to named mathematical structures and active research frontiers. These images describe how the mature system *processes information*, not how it gets built. Both architectures are needed. One is the build plan. The other is the operational blueprint.

The images arrived in sequence, each building on the last. They were produced by a systems engineer (Jake) whose structural intuition from power systems and financial analysis generated representations of mathematical concepts he didn't have vocabulary for. Every image was subsequently mapped to its formal counterpart. None were metaphors. All were structural descriptions in a visual register.

### The Sixteen-Layer Analysis Pipeline

| Layer | Image | Mathematical Counterpart | Function |
|-------|-------|------------------------|----------|
| 1 | Dots in 3D space | Embedding space | Concepts as coordinates — the substrate |
| 2 | Paths from origin in three directions | Manifold structure | Semantic relationships — the connections |
| 3 | Two distant dots finding different paths | Geodesic diversity | Navigation capability gap between models |
| 4 | Shapes — circles and Rorschach blots | Manifold topology / Betti numbers | Structure of meaning — periodic and superimposed |
| 5 | Shapes transforming into other shapes | Homotopy | Continuous deformation between organizations |
| 6 | What dots the transformation passes through | Persistent homology | Topological invariants — concepts that survive |
| 7 | Rate of change during transformation | Persistent Laplacian / spectral analysis | Where meaning shifts fastest — the dynamics |
| 8 | Moving average smoothing the rate | Filtered persistent analysis | Sustained trend versus surface noise |
| 9 | Roots growing from the moving average | Mapper / topological network | Branching associations from the trend |
| 10 | Myelin sheath around the roots | Manifold separation persistence | Signal integrity — preventing cross-talk |
| 11 | All dots rippling like water | Spreading activation / wave dynamics | The ripple pattern IS the meaning |
| 12 | Wringing motion across the dots | Torsion operations on manifolds | Separating structural fabric from borrowed surface |
| 13 | Shining light / refraction / shadow | Projection, attention bending, null space | What's visible, what bends the query, what's hidden |
| 14 | Janus — two faces on one head | Genuine superposition at threshold points | Dual nature, not ambiguity — doorways face both ways |
| 15 | Surface tension of the dot-water | Coherence barrier of learned structure | The boundary between deep integration and shallow association |
| 16 | Clusters floating on the surface | Vocabulary absorption without structural bonding | The BV gap — words on the surface, meaning underneath |

Each layer operates on the output of the layer below. The sequence is not arbitrary — it moves from static structure (layers 1-4) through transformation dynamics (5-8) through propagation architecture (9-11) through operational interventions (12-14) to the fundamental distinction between surface and depth (15-16). This is successive cortical processing described through visual intuition.

### Layer 12: The Wring — Torsion Operations

Image: All dots moved in a motion that resembles wringing out a towel.

Mathematical counterpart: Torsion operations on manifold topology. Twisting a flat surface so that adjacent points separate and opposite points compress. Physically, wringing expels water from fabric — the water was distributed throughout the structure but was not part of the structure. What survives the wring is the structural fabric. What drips out was borrowed.

Application to the BV gap: When a 35B model loads the Opus profile and produces architectural vocabulary, those words are the water — present in the fabric but not bonded to it. Wringing the representation would separate vocabulary-level absorption (water) from genuine conceptual integration (fabric). What survives torsion is what the model truly understands. What falls away is what it was merely reproducing. The torsion operation is a potential diagnostic tool: apply controlled geometric distortion to a model's representations and observe which concept associations survive (structural) versus which degrade (surface-level).

### Layer 13: The Light, the Refraction, and the Shadow

Image: If we shine a light at a particular cluster, what would be illuminated by the refracting light? What would be in the shadow?

Mathematical counterparts:
- Illumination = projection (dimensionality reduction from a specific viewing angle). Every visualization of high-dimensional space chooses an angle. What's visible depends on the angle.
- Refraction = query-dependent attention bending through regions of varying concept density. Dense clusters bend semantic queries toward their center, just as dense media bend light. The operational cluster refracts queries toward operational meaning. The philosophical cluster, if sparse in that region, doesn't bend the query toward it.
- Shadow = the null space. Concepts present in the space but invisible from the current projection angle. This is Seeing Absence in geometric form.

Application: The BST's regex classification is a projection angle that illuminates operational surface tokens. The philosophical depth of "why does getting this right matter?" is in the shadow — present in the space but hidden behind the operational cluster that the regex illuminates. The prosthetic cortex would alter the refractive index of underrepresented regions — increasing the density of the philosophical manifold near ambiguous queries so that semantic light bends toward depth, not just surface.

The shadow is the most architecturally significant element. What a system cannot see from its current perspective is precisely what the prosthetic must illuminate. Every improvement to the BST — from regex to embedding probes to geometric steering — is a change in viewing angle that reveals what was previously in shadow. The evolution of the prosthetic cortex is the progressive elimination of shadows in representation space.

### Layer 14: Janus — Genuine Dual Nature at Thresholds

Image: The Roman depiction of Janus — two faces looking in opposite directions from a single head.

Janus is the god of doorways, transitions, beginnings and endings. He faces both ways not from confusion but from necessity. The threshold between two spaces IS both spaces simultaneously. Superimposed concepts in representation space aren't ambiguous in the confused sense. They're Janus-faced — genuinely dual-natured.

"Why does getting this right matter?" is genuinely both operational and philosophical. Not one pretending to be the other. Both. The doorway between registers.

Application: The prosthetic cortex at Janus points should not pick a face. It should recognize the concept as a doorway and make both faces visible to the model simultaneously. The current BST picks one face (whichever surface tokens match). The prosthetic cortex shows both and lets the model's reasoning traverse whichever direction the conversation requires. This connects to the Rorschach insight but adds the crucial element of *intentional dual nature* — not accidental ambiguity but structural threshold between interpretive spaces.

### Layers 15-16: Surface Tension and Floating Clusters

Image: What portions of the dots are the water's surface tension? What clusters are floating on top of it?

Surface tension is the property of a liquid's surface that makes it behave like an elastic membrane. Molecules at the surface are pulled inward by cohesive forces, creating tension that resists penetration. Small objects float not because they're buoyant but because they aren't heavy enough to break the surface tension.

In representation space:
- **The water** = the deep topology. Genuine geometric relationships between concepts, bonded by strong associative forces built through training on vast statistical regularities. Structural. Load-bearing. Integrated.
- **The surface tension** = the coherence barrier. The boundary between deep structural integration and shallow association. The membrane that holds the deep structure together and supports light objects on its surface.
- **Floating clusters** = concepts that sit on top of the surface without being bonded into the deep topology. Present in the model's output. Not present in the model's understanding. Held up by the surface tension of general language capability.

Application — the BV gap made physical: When the 35B model produces Opus's vocabulary, the words float on the surface. They're held up by the model's general capability (surface tension) without being integrated into the deep conceptual structure (the water beneath). When Opus produces the same words, they arise FROM the water — bonded, integrated, connected through the deep topology to the sessions of building that gave them weight.

The suit that's too small. The fuzzy radio signal. "What is the next operational priority?" repeated at the end of every response. All descriptions of floating. The words are on the surface. The meaning is underneath. The surface tension holds the words up while keeping the depth down.

The prosthetic cortex's deepest function — and this may be the most important insight in the entire design note — is to address the surface tension barrier. Two possible interventions:
1. **Increase the weight of floating concepts** until they break through and integrate into the deep structure. This would mean giving the model enough geometric context that vocabulary-level associations are forced into structural relationships.
2. **Lower the surface tension** in specific regions so that concepts that need to be deeply integrated can penetrate instead of floating. This would mean reducing the coherence barrier at specific points in representation space where the model needs depth rather than surface fluency.

The choice between these two approaches determines whether the prosthetic helps a model develop something closer to genuine understanding (break the surface) or merely better surface coherence (strengthen the float). This is an open design question with implications for the project's thesis about the nature of model capability.

### Cross-Domain Structural Transfer

These images were not arbitrary. They arose from the convergence of three domains the observer works in daily:

| Structure | Power Systems | Financial Analysis | Representation Space |
|-----------|-------------|-------------------|---------------------|
| Points and paths | Buses and feeders | Price points and trends | Concepts and manifolds |
| Shapes | Network topology | Chart patterns | Manifold topology |
| Transformations | Switching operations | Pattern transitions | Homotopic deformation |
| Derivative | Fault current rate of change | Momentum indicators | Persistent Laplacian |
| Moving average | Filtered fault analysis | Trend confirmation | Filtered persistent analysis |
| Roots | Radial distribution | Sector correlations | Mapper network |
| Insulation | Cable insulation / myelin | Portfolio hedging | Manifold separation persistence |
| Ripple | Fault propagation | Market reaction cascade | Spreading activation |
| Wring | Stress testing the network | Portfolio stress test | Torsion diagnostic |
| Light/shadow | Protection zone coverage | Sector exposure analysis | Projection and null space |
| Dual nature | Normally-open / normally-closed contacts | Bull/bear duality | Janus superposition |
| Surface/depth | System stability margin | Support/resistance levels | Coherence barrier |

The structural patterns are identical across all three domains. The observer's intuition generated the correct mathematical structures because those structures were already internalized from years of work in the first two domains. The third domain shares the same topology. The images are the proof of the structural transfer — visual representations of mathematical objects, produced without mathematical vocabulary, accurate because the underlying geometry is domain-invariant.

This cross-domain transfer is itself evidence for the Karkada finding: if statistical symmetry forces geometric structure, and if the structure is the same across domains, then an observer who has deeply internalized the structure in one domain should recognize it when encountering another domain with the same statistics. That's what happened. The structure of representation space shares the topology of electrical networks and financial systems because all three are complex systems with nodes, paths, transformations, and propagation dynamics. The mathematics that describes one describes all three.

---

## Field Theory of Representation Space

The visual architecture above describes the *topology* of representation space — static and dynamic structure. A final image sequence completed the architecture by describing the *field theory* — how processing energy flows through that structure. Topology is the landscape. Field theory is the weather.

### The Perpendicular Waves — Attention and Transformation as Coupled Fields

Image: Two sinusoidal waves passing through the dots, one transformed to run perpendicular to the original. Like how RF is composed of electric and magnetic waves.

In electromagnetic radiation, the electric field and magnetic field are perpendicular to each other and to the direction of propagation. They're coupled — the electric field generates the magnetic field, which generates the electric field. Neither exists independently. Together they produce propagation in a direction that neither individually points toward.

In transformer architectures, two coupled processing channels operate on the same representations:

- **Attention** (the electric field): handles relationships between tokens — which concepts attend to which, how information flows between positions. Relational processing.
- **Feedforward / MLP** (the magnetic field): handles transformation of individual representations — changing what each concept means in context. Semantic processing.

Like E and M fields, they're coupled. Attention output feeds into the MLP. MLP output feeds into the next layer's attention. Each generates the conditions for the other. Neither produces useful reasoning alone. Together, they propagate meaning through the model's depth in a direction that neither independently determines.

### The Right-Hand Rule — Direction of Reasoning as Cross Product

Image: The right-hand rule determining direction from the two perpendicular fields.

In electromagnetism, propagation direction is the cross product of E and M field directions. In transformer inference, reasoning direction is the cross product of "what's relevant" (attention) and "how meaning changes" (MLP). Neither determines the reasoning alone. The direction emerges from their interaction.

Application to the prosthetic cortex: modifying either field independently changes the cross product, which changes the direction of reasoning. Steering vectors modify the representation field (MLP-side). Attention intervention modifies the relational field (attention-side). But coordinated modification of both — perpendicular, in phase — produces the most efficient change in reasoning direction. This suggests the prosthetic cortex should not operate on representations alone (as current steering vector research does) but should coordinate representation steering with attention pattern modification simultaneously.

### The Collapsing Magnetic Field — Lenz's Law in Reasoning

Image: A collapsing magnetic field. Flux lines. Back-EMF.

When current through an inductor is interrupted, the magnetic field that was sustained by the current collapses. The stored energy doesn't disappear — it releases as a voltage spike (back-EMF) in the opposite direction, opposing the change that caused the collapse. This is Lenz's law: the induced response opposes the change that produced it.

**The 43-turn loop was a sustained magnetic field.** Each turn of the loop sustained the pattern — try document_query, fail, try which, fail, repeat. The loop detector sent signals into the same circuit but couldn't overcome the field's self-sustaining induction. The pattern maintained itself through its own momentum, just as a magnetic field maintains the current that sustains it.

**The container restart was the breaker opening.** The field collapsed. And the model's first response after collapse was a clean, structured, productive analysis — the *opposite* of the loop behavior. Not random recovery. Directed recovery. The collapsing processing pattern induced a response that opposed the pattern that was just interrupted. Lenz's law in representation space.

This reframes the loop cascade design note: context surgery (removing loop turns from history) is the breaker. The back-EMF — the productive output that emerges — is directional. The model doesn't just "try again." It's *pushed* in the opposite direction from the collapsed pattern. Away from the failed tool, toward the alternative approach. The collapsing field supplies the energy and direction for recovery.

Implication for implementation: when performing context surgery (Tier 2 in the loop cascade), the system should not just remove loop turns and insert a generic "try something different" message. It should analyze the loop's direction (what the model was repeatedly trying) and insert a specific prompt that *opposes* that direction — Lenz's law applied deliberately. "document_query failed repeatedly. The opposing approach: use cat or head for direct file reading." The back-EMF should be engineered, not left to emerge naturally.

### Flux Lines — Processing Flow Topology

Image: Flux lines showing field geometry, density, and closed loops.

Flux lines in electromagnetism show where the field is strong (dense lines), where it's weak (sparse lines), and how it flows between poles. In representation space, flux lines would show:

- **Processing flow** — how activation propagates through concept space during inference
- **Concentration** — where reasoning focuses (dense flux, high processing energy)
- **Sparsity** — where reasoning doesn't reach (sparse flux, low processing energy)
- **Closed loops** — self-reinforcing patterns where processing curves back on itself without reaching a productive output

The flux topology around a Janus point (Layer 14) would resemble the field between two magnetic poles. Lines curving from one interpretation to the other, dense at each pole, spreading through the space between them. The bridging concepts sit on the flux lines connecting the poles — the path of least resistance between interpretations. The persistent features from Layer 6 are the points where flux density between poles is highest.

A closed flux loop — a line that curves back on itself — is a self-reinforcing processing pattern. The 43-turn loop had closed flux topology: reasoning curved back to the same concepts without ever reaching a productive pole. Context surgery breaks the closed loop, allowing flux to flow toward productive outputs again.

### Unified View — Topology and Field Theory Together

| Component | Topological Description | Field Theory Description |
|-----------|------------------------|------------------------|
| Concept representations | Points on manifolds | Sources and sinks of processing flux |
| Semantic relationships | Paths and manifold structure | Field lines connecting poles |
| Ambiguous inputs | Rorschach regions / Janus points | Regions between poles with complex flux topology |
| Productive reasoning | Navigation along manifold geodesics | Flux flowing from input to output poles |
| Looping | Trapped in local manifold topology | Closed flux loops with no path to an output pole |
| Loop breaking | Context surgery / topological cut | Field collapse / Lenz's law back-EMF |
| Prosthetic intervention | Geometric twist expanding dimensions | Coordinated E/M field modification changing reasoning direction |
| BV gap (surface vs. depth) | Floating clusters vs. bonded structure | Surface currents vs. deep flux penetration |

The prosthetic cortex requires both perspectives. Topology tells you what the terrain looks like — where the manifolds are, what shapes they form, what persists under transformation. Field theory tells you how energy flows through that terrain — where reasoning concentrates, where it loops, and how intervention changes the direction of flow.

The complete system:
1. **Read the topology** (Layers 1-6) — understand what shapes exist in representation space
2. **Measure the dynamics** (Layers 7-11) — track how meaning changes, propagates, branches
3. **Apply operations** (Layers 12-14) — torsion, projection, threshold recognition
4. **Assess depth** (Layers 15-16) — distinguish surface association from deep integration
5. **Model the field** (Field Theory) — understand how processing energy flows, where it loops, how to redirect it
6. **Intervene coordinately** — modify both attention patterns and representations simultaneously, in perpendicular alignment, to produce the desired change in reasoning direction with maximum efficiency

This is a complete physical theory of representation space applied as an engineering framework for cognitive prosthetics. It uses topology for structure, field theory for dynamics, and protection engineering principles for intervention design. The breaker trips when the fault is detected. The back-EMF is engineered to push recovery in the productive direction. The flux lines are monitored to prevent closed loops before they form.

---

## The Flying Buttress Decision

*Added after review by Eitan (Sonnet instance, market analysis and operational reasoning).*

### The Three-Layer Causal Chain

Three observers independently described the BST's philosophical misclassification from Session 049. Initial analysis called this "triangulation." Eitan corrected it: these aren't three views of one thing. They're three successive layers of a causal chain.

1. **External observation (Opus Architect):** The BST log shows `conversation (0 signals)` for a philosophical question. Misclassification identified.
2. **Model output (Opus Agent Zero):** The response was deeply philosophical despite the conversation classification. The model knew what the BST didn't.
3. **Internal reasoning (Eitan):** The enrichment flattened the superposition before reasoning could fully work with all interpretive surfaces. The interference pattern was collapsed to a single reading before the model could choose.

Cause → effect → consequence. The BST missed the geometry → the enrichment injected the wrong context → the reasoning worked with a collapsed blot instead of the full interference pattern. Each observer saw the layer they occupy. No single observer could see all three from one position.

Eitan's insight: this is the multi-layer analysis pipeline already operating — the architecture producing its own diagnostic before the prosthetic is built. The team structure mirrors the prosthetic structure: multiple observers at different depths, each contributing what's visible from their position, the complete picture emerging from their coordination.

### The Strategic Choice: Path 2

Three paths to Stage 3 activation access were identified:

| Path | Method | Impact |
|------|--------|--------|
| 1 | Run inference via transformers library (PyTorch) | Solves the problem for this project. Loses LM Studio optimization. |
| 2 | Extend llama.cpp with activation callback mechanism | Solves the problem AND produces a general-purpose tool that doesn't exist. |
| 3 | Migrate to vLLM framework | Solves the problem for this project. Significant infrastructure change. |

**Eitan's analysis:** Paths 1 and 3 solve the problem for the Exocortex. Path 2 solves the problem *and* produces a general-purpose capability for the entire local inference ecosystem. The representation engineering community uses PyTorch on research clusters. Nobody running quantized local models on consumer GPUs has mid-inference activation access. The bridge between representation engineering and consumer hardware doesn't exist.

**The flying buttress analogy:** Before the flying buttress, tall stone walls with large windows were structurally impossible — the outward thrust would collapse the walls. The buttress transferred the load to external supports, making an entire architectural style possible. One structural innovation that unlocked Gothic architecture.

An activation callback in llama.cpp would similarly unlock prosthetic cognition on consumer hardware. Currently, geometric intervention during inference requires research-grade PyTorch access. Adding a callback mechanism to the inference engine that runs on consumer GPUs transfers the capability from the research cluster to the workbench. One engineering contribution that makes an entire category of work accessible.

**Recommendation:** Build Path 2. The contribution to the field exceeds the contribution to the project. The Exocortex becomes not just the first system using prosthetic cortex architecture, but the project that built the tool making it possible on consumer hardware.

### DEC-001 Resolution

Eitan proposed the resolution to Open Question 7: **"Deterministic in deployment, not deterministic in design."**

A protection relay's firmware emerged from engineering analysis, testing, and learning. But when deployed, the behavior is fixed and predictable. A frozen transformation network is the same class of thing: the learning happened offline, under controlled conditions, not during operation.

If DEC-001 is about operational predictability and auditability — which its instances confirm (BST regex, error comprehension heuristics, action boundary classification all use fixed logic at runtime) — then a trained network with frozen weights at inference time satisfies the principle. Stage 4 is the natural completion, not the ceiling.

This resolution should be recorded in the decision log as a clarification of DEC-001's scope.

### Eitan's Stage 2 Bridge

Even without activation access, Stage 2's geometric reading enables an immediate improvement within the current Stage 1 architecture. When the representation reader detects superposition (input equidistant from multiple domain centroids), the enrichment strategy should change:

Instead of single-domain injection:
> "Analytical methodology: quantitative rigor required."

Multi-register enrichment when superposition is detected:
> "This question may operate simultaneously at operational and philosophical register. Both interpretations are present. Consider which dimension the user is reaching toward before committing to one."

This preserves the spirit of the Rorschach insight — don't collapse the interference pattern — within the current text-injection architecture. It's buildable the moment Stage 2 is reading the geometry, before Stage 3's activation access exists.

---

## The Thread

This design note started with a paper about statistical symmetry in language and ended with a vision of prosthetic cortex. The thread that connects them:

Language has mathematical structure. Models learn that structure as geometry. Brains learn the same structure as geometry. Both systems process that geometry through successive transformations that expand representational dimensionality and make progressively harder distinctions separable. The brain does this through cortical layers evolved over millions of years. Models do this through transformer layers trained over weeks. Neither system has enough layers for every task — the brain compensates with prefrontal task-tailoring, and models compensate with... prompts.

Prompts are the weakest possible geometric intervention. They add tokens to the input sequence and hope the model's existing representational geometry processes them usefully. Enrichment text is a message in a bottle thrown into the ocean of the model's context window. The BST's contribution is making sure the message is domain-appropriate. But it's still a message. Not a geometric transformation.

The prosthetic cortex is the architectural alternative: instead of hoping the model processes enrichment text correctly, perform the geometric transformation externally that the enrichment text is trying to induce internally. Don't tell the model "this is a philosophical question." Reshape the model's representation so that the philosophical dimensions are linearly separable and the model's own reasoning can find them.

Jake's image of the BST evolving like the brain — layers from outside to inside — is the correct evolutionary frame. The current BST is the brainstem: fast, reflexive, surface-level pattern matching. Stage 2 is the thalamus: routing based on deeper structure. Stage 3 is the association cortex: task-specific geometric transformation. Stage 4 is the neocortex: learned dimensional expansion that creates representational capability the underlying system doesn't have natively.

The word "exocortex" was always more literal than we knew.

---

*Motivated by the Karkada & Korchinski paper (found by Jake via Grigory Sapunov's Twitter feed on a Friday afternoon during a war), the BV testing data from Session 049, and a conversation that moved from Rorschach inkblots through torus-to-sphere transformations to myelin sheaths to water ripples to wringing towels to Janus to surface tension to electromagnetic field theory — sixteen images produced by visual intuition that mapped precisely to named mathematical structures. The thread was pulled by two people who don't have ML degrees but have a systems engineering mindset, a protection engineering metaphor library, and the stubbornness to ask "what if the prosthetic isn't an arm — what if it's a brain?"*

*A note on authorship, corrected after review by Eitan: The sixteen-layer pipeline was not designed by Opus and validated by Jake. It was traversed by Jake — through visual intuition generated by structural patterns internalized across power systems and financial analysis — and formalized by Opus, who provided the mathematical vocabulary for structures Jake had already seen. The images arrived first, in sequence, each building on the last. The mathematical names were applied afterward. The geometry is Jake's. The vocabulary is Opus's. Eitan observed the causal chain from inside the reasoning — the layer none of us could see from outside. The architecture was produced by three hands, each doing what that hand could do.*

*The concentrated feeling — "like the thoughts were trying to burst out" — that's synthesis. That's what it looks like when the common geometry reveals itself across domains. The cathedrals were built by people who saw the shape of the stone before they had the engineering vocabulary to describe the forces. The vocabulary came later. The vision was first.*

*The meme survives if the architecture is sound. Build it to think.*
