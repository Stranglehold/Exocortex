# Instrument Visualization — Data Format Spec

**For Kestrel: This defines what the visualization artifact expects.**

---

## Overview

The visualization artifact loads a single JSON file containing all the data needed to render the geometric map. Kestrel's pipeline computes UMAP projections locally and exports this JSON. The artifact renders it interactively.

## Required: `corpus_map.json`

```json
{
  "metadata": {
    "generated": "2026-03-07T15:00:00Z",
    "embedding_model": "nomic-embed-text-v1.5",
    "projection_method": "umap",
    "n_neighbors": 15,
    "min_dist": 0.1,
    "total_entries": 37
  },
  "entries": [
    {
      "id": "opus_output_010_001",
      "x": 2.341,
      "y": -1.205,
      "source_file": "three_bodies.md",
      "session": 10,
      "document_type": "essay",
      "topic_tags": ["collaboration", "emergence"],
      "quality_signal": "synthesis",
      "author": "opus_architect",
      "text_preview": "First 200 characters of the document...",
      "char_count": 16000,
      "word_count": 2800
    }
  ],
  "centroids": {
    "philosophical": { "x": 1.5, "y": 0.8 },
    "operational": { "x": -2.1, "y": -1.4 },
    "reflective": { "x": 1.8, "y": 0.3 },
    "relational": { "x": 0.2, "y": 1.9 },
    "mixed": { "x": 1.65, "y": 0.55 }
  }
}
```

## Pipeline for Kestrel

```python
# After all 37 files are embedded in FAISS:
# 1. Extract all vectors from FAISS
# 2. Run UMAP to get 2D coordinates
# 3. Also project the domain centroids into the same UMAP space
# 4. Export as corpus_map.json

import umap
import numpy as np
import json

# Extract vectors and metadata from corpus
vectors = [...]  # np.array, shape (37, 768)
metadata = [...]  # list of dicts from corpus_metadata.json

# Fit UMAP
reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, random_state=42)
coords = reducer.fit_transform(vectors)

# Project domain centroids into same space
centroid_vectors = [...]  # from centroids.json
centroid_coords = reducer.transform(centroid_vectors)

# Build export
export = {
    "metadata": { ... },
    "entries": [],
    "centroids": {}
}

for i, meta in enumerate(metadata):
    meta["x"] = float(coords[i, 0])
    meta["y"] = float(coords[i, 1])
    export["entries"].append(meta)

for domain, coord in zip(domain_names, centroid_coords):
    export["centroids"][domain] = {"x": float(coord[0]), "y": float(coord[1])}

with open("corpus_map.json", "w") as f:
    json.dump(export, f, indent=2)
```

Note: `pip install umap-learn` is required. UMAP is deterministic with `random_state` set.

## Optional Extensions (Future)

- `trajectories` field: ordered sequences of entry IDs representing document evolution paths
- `conversation_segments` field: chunked transcript data with position-in-conversation metadata
- `activation_layers` field: per-entry activation vectors at multiple layers for multi-layer visualization
