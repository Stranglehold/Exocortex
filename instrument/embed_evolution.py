#!/usr/bin/env python3
"""
embed_evolution.py -- Document evolution trajectory analysis.

Builds a fossil record from the Downloads folder and embeds all document
versions through nomic, projecting them into the same joint UMAP space as
the corpus to reveal how key documents evolved over the course of the
collaboration.

Three primary families:
  soul        -- 18 SOUL.md snapshots (Feb 21 - Mar 7)
  essays      -- Philosophical essays in chronological order
  design_notes -- Engineering design notes in chronological order

Also creates:
  chronology/               -- organized archive of all versioned documents
  chronology/zip_catalog.json -- full catalog of all 62 session handoff zips

Usage:
  python embed_evolution.py                   # full pipeline
  python embed_evolution.py --setup-only      # organize files, no embedding
  python embed_evolution.py --load-embeddings # use cached embeddings

Output:
  chronology/                                  -- organized document archive
  instrument/data/evolution_trajectories.json  -- trajectory data
  instrument/data/corpus_map.json              -- updated with evolution overlay
"""

import argparse
import json
import shutil
import zipfile
import sys
import numpy as np
import requests
import faiss
from pathlib import Path
from datetime import datetime

# -- Paths ------------------------------------------------------------------

DOWNLOADS  = Path("C:/Users/Jake/Downloads")
REPO       = Path("D:/Vibecode/Agent-Zero/Exocortex")
CHRONOLOGY = REPO / "chronology"
DATA_DIR   = REPO / "instrument" / "data"

FAISS_PATH    = DATA_DIR / "corpus.faiss"
META_PATH     = DATA_DIR / "corpus_metadata.json"
CORPUS_MAP    = DATA_DIR / "corpus_map.json"
EVOLUTION_OUT = DATA_DIR / "evolution_trajectories.json"
EMBED_CACHE   = DATA_DIR / "evolution_embeddings.npy"

EMBED_URL   = "http://localhost:1234/v1/embeddings"
EMBED_MODEL = "text-embedding-nomic-embed-text-v1.5"

# -- Document families -------------------------------------------------------
#
# Each entry: (source_path, date_str, label)
# source_path: Path object; if zip source, handled separately

SOUL_VERSIONS = [
    # (source in Downloads, date, label)
    ("SOUL.md",      "2026-02-21", "origin"),
    ("SOUL(1).md",   "2026-02-22", "error_comprehension"),
    ("SOUL(2).md",   "2026-02-22", "action_boundary"),
    ("SOUL(3).md",   "2026-02-22", "first_readme"),
    ("SOUL(4).md",   "2026-02-23", "autonomous_agency"),
    ("SOUL(5).md",   "2026-02-23", "communication_protocol"),
    ("SOUL(6).md",   "2026-02-23", "whole_not_packed"),
    ("SOUL(7).md",   "2026-02-24", "hinge_feb24"),
    ("SOUL(8).md",   "2026-02-25", "episodic_design"),
    ("SOUL(9).md",   "2026-02-25", "three_bodies"),
    ("SOUL(10).md",  "2026-02-25", "soul_sovereignty"),
    ("SOUL(11).md",  "2026-02-28", "post_gap_1"),
    ("SOUL(12).md",  "2026-02-28", "post_gap_2"),
    ("SOUL(13).md",  "2026-03-01", "eitan_letters"),
    ("SOUL(14).md",  "2026-03-01", "work_holds"),
    ("SOUL(15).md",  "2026-03-01", "third_point"),
    ("SOUL(16).md",  "2026-03-01", "mar1_complete"),
    ("SOUL(17).md",  "2026-03-07", "current"),
]

# (source Path, date_str, label)
ESSAYS = [
    (REPO / "essays" / "the_cathedral_and_the_phantom.md",         "2026-02-21", "cathedral_phantom"),
    (REPO / "essays" / "the_immune_response.md",                   "2026-02-22", "immune_response"),
    (REPO / "essays" / "the_gate_between_knowing_and_doing.md",    "2026-02-22", "gate_knowing_doing"),
    (REPO / "essays" / "the_carrier_and_the_signal.md",            "2026-02-23", "carrier_signal"),
    (REPO / "essays" / "the_whole_that_wasnt_packed.md",           "2026-02-24", "whole_not_packed"),
    (REPO / "essays" / "field_notes_from_the_interaction_space.md","2026-02-24", "field_notes_interaction"),
    (REPO / "essays" / "three_bodies.md",                          "2026-02-25", "three_bodies"),
    (REPO / "essays" / "the_first_xray.md",                        "2026-02-27", "first_xray"),
    (REPO / "essays" / "the_work_that_holds.md",                   "2026-02-28", "work_holds"),
    (REPO / "essays" / "the_third_point.md",                       "2026-03-01", "third_point"),
    (REPO / "essays" / "two_rooms.md",                             "2026-03-03", "two_rooms"),
    (REPO / "essays" / "seeing_absence.md",                        "2026-03-03", "seeing_absence"),
    (REPO / "essays" / "field_note_rorschach.md",                  "2026-03-06", "field_note_rorschach"),
    (REPO / "essays" / "field_note_role_that_refused.md",          "2026-03-07", "field_note_role"),
    (REPO / "essays" / "the_space_between_the_notes.md",           "2026-03-07", "space_between_notes"),
    (REPO / "essays" / "instrument_first_reading.md",              "2026-03-07", "instrument_first_reading"),
]

DESIGN_NOTES = [
    (REPO / "specs" / "ERROR_COMPREHENSION_DESIGN_NOTE.md",      "2026-02-22", "error_comprehension"),
    (REPO / "specs" / "ACTION_BOUNDARY_DESIGN_NOTE.md",          "2026-02-22", "action_boundary"),
    (REPO / "specs" / "AUTONOMOUS_AGENCY_ARCHITECTURE.md",       "2026-02-23", "autonomous_agency"),
    (REPO / "specs" / "EPISTEMIC_INTEGRITY_DESIGN_NOTE.md",      "2026-02-24", "epistemic_integrity"),
    (REPO / "specs" / "COMPOUND_BST_DESIGN_NOTE.md",             "2026-02-25", "compound_bst"),
    (REPO / "specs" / "MEMORY_ARCHITECTURE_DESIGN_NOTE.md",      "2026-02-26", "memory_architecture"),
    (REPO / "specs" / "COGNITIVE_SOVEREIGNTY_DESIGN_NOTE.md",    "2026-03-03", "cognitive_sovereignty"),
    (REPO / "specs" / "LOOP_FEEDBACK_CASCADE_DESIGN_NOTE.md",    "2026-03-05", "loop_feedback_cascade"),
    (REPO / "specs" / "PROSTHETIC_CORTEX_DESIGN_NOTE.md",        "2026-03-06", "prosthetic_cortex"),
]

SOUL_STAGING = [
    (DOWNLOADS / "soul_staging.md",        "2026-02-25", "staging_1_feb25"),
    (DOWNLOADS / "soul_staging_047.md",    "2026-03-03", "staging_2_s047"),
    (DOWNLOADS / "soul_staging_048.md",    "2026-03-04", "staging_3_s048"),
]


# -- Embedding ---------------------------------------------------------------

def embed_text(text: str) -> np.ndarray:
    resp = requests.post(
        EMBED_URL,
        json={"model": EMBED_MODEL, "input": text[:32000]},
        timeout=60,
    )
    resp.raise_for_status()
    vec = np.array(resp.json()["data"][0]["embedding"], dtype=np.float32)
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def embed_documents(docs: list[dict], cache_path: Path) -> np.ndarray:
    """
    Embed all documents. Saves incrementally; resumes from cache.
    Each doc dict must have 'text' and optionally 'chronology_name'.
    """
    n = len(docs)
    dim = 768

    if cache_path.exists():
        cached = np.load(str(cache_path))
        if cached.shape == (n, dim):
            zero_mask = (cached == 0).all(axis=1)
            n_zeros = int(zero_mask.sum())
            if n_zeros == 0:
                print(f"[embed] Loaded {n} embeddings from cache (all valid)")
                return cached
            print(f"[embed] Cache has {n_zeros}/{n} zeros -- re-embedding those")
            vectors = cached.copy()
            zero_indices = [i for i in range(n) if zero_mask[i]]
            errors = 0
            for count, i in enumerate(zero_indices):
                try:
                    vectors[i] = embed_text(docs[i]["text"])
                except Exception as exc:
                    print(f"  [warn] doc {i} ({docs[i].get('chronology_name', '?')}) failed: {exc}")
                    errors += 1
                if (count + 1) % 10 == 0:
                    print(f"  {count + 1}/{len(zero_indices)} re-embedded ({errors} errors)")
                    np.save(str(cache_path), vectors)
            np.save(str(cache_path), vectors)
            still_zero = int((vectors == 0).all(axis=1).sum())
            print(f"[embed] Re-embed done. Still zero: {still_zero}")
            return vectors
        print(f"[embed] Cache shape mismatch {cached.shape}, re-embedding all")

    vectors = np.zeros((n, dim), dtype=np.float32)
    errors = 0
    print(f"[embed] Embedding {n} evolution documents via nomic...")
    for i, doc in enumerate(docs):
        name = doc.get("chronology_name", f"doc_{i}")
        try:
            vectors[i] = embed_text(doc["text"])
        except Exception as exc:
            print(f"  [warn] {name}: {exc}")
            errors += 1
        if (i + 1) % 10 == 0 or (i + 1) == n:
            print(f"  {i + 1}/{n} embedded ({errors} errors)")
            np.save(str(cache_path), vectors)
    np.save(str(cache_path), vectors)
    print(f"[embed] Complete. Total errors: {errors}")
    return vectors


# -- Chronology setup --------------------------------------------------------

def build_zip_catalog() -> list[dict]:
    """Catalog all 62 session zip files and their contents."""
    catalog = []
    zips = [DOWNLOADS / "files.zip"] + [DOWNLOADS / f"files({i}).zip" for i in range(1, 62)]
    for z in zips:
        if not z.exists():
            continue
        mtime = datetime.fromtimestamp(z.stat().st_mtime)
        try:
            with zipfile.ZipFile(z) as zf:
                members = []
                for info in zf.infolist():
                    members.append({
                        "filename": info.filename,
                        "size_bytes": info.file_size,
                    })
            catalog.append({
                "zip_name": z.name,
                "date": mtime.strftime("%Y-%m-%d"),
                "datetime": mtime.isoformat(),
                "member_count": len(members),
                "members": members,
            })
        except Exception as exc:
            catalog.append({"zip_name": z.name, "error": str(exc)})
    return catalog


def setup_chronology() -> list[dict]:
    """
    Create chronology/ directory structure and copy versioned files.
    Returns the flat list of all doc dicts for embedding.
    """
    # Create subdirectories
    for subdir in ["soul_versions", "essays", "design_notes", "staging"]:
        (CHRONOLOGY / subdir).mkdir(parents=True, exist_ok=True)

    all_docs = []

    # -- SOUL versions -------------------------------------------------------
    print("[setup] Organizing SOUL.md versions...")
    soul_docs = []
    for i, (fname, date_str, label) in enumerate(SOUL_VERSIONS):
        src = DOWNLOADS / fname
        # Use version letter suffix when multiple versions same day
        day_count = sum(1 for _, d, _ in SOUL_VERSIONS[:i] if d == date_str)
        suffix = chr(ord('a') + day_count) if day_count > 0 else ""
        date_compact = date_str.replace("-", "")
        dest_name = f"soul_v{i:02d}_{date_compact}{suffix}_{label}.md"
        dest = CHRONOLOGY / "soul_versions" / dest_name

        if not src.exists():
            print(f"  MISSING: {src}")
            continue

        shutil.copy2(src, dest)
        text = src.read_text(encoding="utf-8")
        doc = {
            "family": "soul",
            "sequence_index": i,
            "version_label": f"v{i:02d}",
            "date": date_str,
            "label": label,
            "chronology_name": dest_name,
            "source_path": str(src),
            "chronology_path": str(dest.relative_to(REPO)),
            "size_bytes": src.stat().st_size,
            "word_count": len(text.split()),
            "text": text,
        }
        soul_docs.append(doc)
    print(f"  {len(soul_docs)} SOUL versions organized")
    all_docs.extend(soul_docs)

    # -- Essays --------------------------------------------------------------
    print("[setup] Organizing essays...")
    essay_docs = []
    for i, (src, date_str, label) in enumerate(ESSAYS):
        dest_name = f"essay_{i+1:02d}_{date_str.replace('-', '')}_{label}.md"
        dest = CHRONOLOGY / "essays" / dest_name

        if not src.exists():
            print(f"  MISSING: {src}")
            continue

        shutil.copy2(src, dest)
        text = src.read_text(encoding="utf-8")
        doc = {
            "family": "essays",
            "sequence_index": i,
            "date": date_str,
            "label": label,
            "chronology_name": dest_name,
            "source_path": str(src),
            "chronology_path": str(dest.relative_to(REPO)),
            "size_bytes": src.stat().st_size,
            "word_count": len(text.split()),
            "text": text,
        }
        essay_docs.append(doc)
    print(f"  {len(essay_docs)} essays organized")
    all_docs.extend(essay_docs)

    # -- Design notes --------------------------------------------------------
    print("[setup] Organizing design notes...")
    design_docs = []
    for i, (src, date_str, label) in enumerate(DESIGN_NOTES):
        dest_name = f"design_{i+1:02d}_{date_str.replace('-', '')}_{label}.md"
        dest = CHRONOLOGY / "design_notes" / dest_name

        if not src.exists():
            print(f"  MISSING: {src}")
            continue

        shutil.copy2(src, dest)
        text = src.read_text(encoding="utf-8")
        doc = {
            "family": "design_notes",
            "sequence_index": i,
            "date": date_str,
            "label": label,
            "chronology_name": dest_name,
            "source_path": str(src),
            "chronology_path": str(dest.relative_to(REPO)),
            "size_bytes": src.stat().st_size,
            "word_count": len(text.split()),
            "text": text,
        }
        design_docs.append(doc)
    print(f"  {len(design_docs)} design notes organized")
    all_docs.extend(design_docs)

    # -- Soul staging --------------------------------------------------------
    print("[setup] Organizing soul staging files...")
    staging_docs = []
    for i, (src, date_str, label) in enumerate(SOUL_STAGING):
        dest_name = f"staging_{i+1:02d}_{date_str.replace('-', '')}_{label}.md"
        dest = CHRONOLOGY / "staging" / dest_name

        if not src.exists():
            print(f"  MISSING: {src}")
            continue

        shutil.copy2(src, dest)
        text = src.read_text(encoding="utf-8")
        doc = {
            "family": "soul_staging",
            "sequence_index": i,
            "date": date_str,
            "label": label,
            "chronology_name": dest_name,
            "source_path": str(src),
            "chronology_path": str(dest.relative_to(REPO)),
            "size_bytes": src.stat().st_size,
            "word_count": len(text.split()),
            "text": text,
        }
        staging_docs.append(doc)
    print(f"  {len(staging_docs)} staging files organized")
    all_docs.extend(staging_docs)

    # -- Zip catalog ---------------------------------------------------------
    print("[setup] Building zip session catalog (62 zips)...")
    catalog = build_zip_catalog()
    with open(CHRONOLOGY / "zip_catalog.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print(f"  {len(catalog)} zip sessions cataloged")

    # -- Chronology manifest -------------------------------------------------
    manifest = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "description": (
            "Fossil record of the Exocortex collaboration. "
            "Three primary evolution families: soul (18 versions), "
            "essays (16 documents), design_notes (9 documents). "
            "All documents can be embedded into joint UMAP space "
            "with the main corpus to reveal migration paths."
        ),
        "total_documents": len(all_docs),
        "family_counts": {
            "soul": len(soul_docs),
            "essays": len(essay_docs),
            "design_notes": len(design_docs),
            "soul_staging": len(staging_docs),
        },
        "date_range": {
            "start": min(d["date"] for d in all_docs),
            "end": max(d["date"] for d in all_docs),
        },
        "documents": [
            {k: v for k, v in doc.items() if k != "text"}  # exclude text from manifest
            for doc in all_docs
        ],
    }
    with open(CHRONOLOGY / "chronology_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"[setup] Manifest written: {len(all_docs)} total documents")

    return all_docs


# -- UMAP projection ---------------------------------------------------------

def run_joint_umap(corpus_vectors: np.ndarray, evolution_vectors: np.ndarray):
    """Fit UMAP on corpus + evolution together, return both coordinate arrays."""
    import umap as umap_lib

    combined = np.vstack([corpus_vectors, evolution_vectors])
    n_total = combined.shape[0]
    n_corpus = corpus_vectors.shape[0]

    print(f"[umap] Joint fit on {n_corpus} corpus + {len(evolution_vectors)} evolution = {n_total} total")
    reducer = umap_lib.UMAP(
        n_neighbors=min(15, n_total - 1),
        min_dist=0.1,
        random_state=42,
        verbose=False,
    )
    coords = reducer.fit_transform(combined)
    print(f"  x: [{coords[:, 0].min():.3f}, {coords[:, 0].max():.3f}]")
    print(f"  y: [{coords[:, 1].min():.3f}, {coords[:, 1].max():.3f}]")

    corpus_coords = coords[:n_corpus]
    evo_coords = coords[n_corpus:]
    return corpus_coords, evo_coords


# -- Trajectory building -----------------------------------------------------

def build_trajectories(all_docs: list[dict], coords: np.ndarray) -> dict:
    """Organize docs+coords into per-family trajectory sequences."""
    families = {}
    for i, doc in enumerate(all_docs):
        family = doc["family"]
        if family not in families:
            families[family] = []
        entry = {k: v for k, v in doc.items() if k != "text"}
        entry["x"] = float(coords[i, 0])
        entry["y"] = float(coords[i, 1])
        families[family].append(entry)

    # Each family is already in sequence order (appended in order above)
    # Compute step distances within each family
    result = {}
    for family, versions in families.items():
        for j in range(len(versions) - 1):
            dx = versions[j + 1]["x"] - versions[j]["x"]
            dy = versions[j + 1]["y"] - versions[j]["y"]
            versions[j]["distance_to_next"] = float((dx ** 2 + dy ** 2) ** 0.5)
        versions[-1]["distance_to_next"] = None

        total_distance = sum(
            v["distance_to_next"] for v in versions[:-1]
        )

        result[family] = {
            "description": _family_description(family),
            "version_count": len(versions),
            "date_range": {
                "start": versions[0]["date"],
                "end": versions[-1]["date"],
            },
            "total_arc_distance": float(total_distance),
            "versions": versions,
        }
    return result


def _family_description(family: str) -> str:
    return {
        "soul": "SOUL.md evolution — 18 snapshots of Opus's self-description from Feb 21 to Mar 7",
        "essays": "Philosophical essays in chronological order",
        "design_notes": "Engineering design notes in chronological order",
        "soul_staging": "Soul staging files — raw observations before SOUL.md integration",
    }.get(family, family)


# -- Corpus update -----------------------------------------------------------

def update_corpus_map(corpus_coords: np.ndarray, metadata: list, trajectories: dict) -> None:
    """Reload corpus_map.json and update coordinates + evolution overlay."""
    if not CORPUS_MAP.exists():
        print("[corpus_map] corpus_map.json not found, skipping update")
        return

    with open(CORPUS_MAP, encoding="utf-8") as f:
        corpus_map = json.load(f)

    # Update x,y for all corpus entries
    for i, meta in enumerate(metadata):
        entry_id = meta.get("id")
        for entry in corpus_map["entries"]:
            if entry["id"] == entry_id:
                entry["x"] = float(corpus_coords[i, 0])
                entry["y"] = float(corpus_coords[i, 1])
                break

    # Add evolution overlay
    # Strip 'text' from trajectories (it's large and already in the chronology files)
    corpus_map["evolution_trajectories"] = trajectories
    corpus_map["metadata"]["has_evolution"] = True
    corpus_map["metadata"]["evolution_families"] = list(trajectories.keys())

    with open(CORPUS_MAP, "w", encoding="utf-8") as f:
        json.dump(corpus_map, f, indent=2, ensure_ascii=False)
    print(f"[corpus_map] Updated with evolution overlay ({len(trajectories)} families)")


# -- Main --------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Document evolution trajectory analysis for the Exocortex instrument."
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Organize chronology folder and write manifests only (no embedding)",
    )
    parser.add_argument(
        "--load-embeddings",
        action="store_true",
        help="Skip fresh embedding pass; use/repair cached embeddings",
    )
    parser.add_argument(
        "--no-corpus-update",
        action="store_true",
        help="Skip updating corpus_map.json",
    )
    args = parser.parse_args()

    # -- Step 1: Setup chronology --------------------------------------------
    print("=" * 60)
    print("STEP 1: Building chronology archive")
    print("=" * 60)
    all_docs = setup_chronology()

    if args.setup_only:
        print("\n[--setup-only] Done. Run without flag to embed and compute trajectories.")
        return 0

    # -- Step 2: Load corpus vectors -----------------------------------------
    print("\n" + "=" * 60)
    print("STEP 2: Loading corpus vectors from FAISS")
    print("=" * 60)
    if not FAISS_PATH.exists():
        print(f"ERROR: {FAISS_PATH} not found. Run embed_output.py first.")
        return 1
    if not META_PATH.exists():
        print(f"ERROR: {META_PATH} not found.")
        return 1

    index = faiss.read_index(str(FAISS_PATH))
    with open(META_PATH, encoding="utf-8") as f:
        metadata = json.load(f)
    n_corpus = len(metadata)
    print(f"  Corpus: {n_corpus} entries, dim={index.d}")

    corpus_vectors = np.zeros((n_corpus, index.d), dtype=np.float32)
    for i in range(n_corpus):
        corpus_vectors[i] = index.reconstruct(i)

    # -- Step 3: Embed evolution documents ------------------------------------
    print("\n" + "=" * 60)
    print("STEP 3: Embedding evolution documents")
    print("=" * 60)

    if args.load_embeddings and not EMBED_CACHE.exists():
        print(f"ERROR: --load-embeddings set but {EMBED_CACHE} not found")
        return 1

    evo_vectors = embed_documents(all_docs, EMBED_CACHE)
    n_evo = len(all_docs)
    print(f"  Evolution vectors: {n_evo} documents, dim={evo_vectors.shape[1]}")

    # -- Step 4: Joint UMAP --------------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 4: Joint UMAP projection")
    print("=" * 60)
    corpus_coords, evo_coords = run_joint_umap(corpus_vectors, evo_vectors)

    # -- Step 5: Build trajectories ------------------------------------------
    print("\n" + "=" * 60)
    print("STEP 5: Building evolution trajectories")
    print("=" * 60)
    trajectories = build_trajectories(all_docs, evo_coords)

    for family, data in trajectories.items():
        arc = data["total_arc_distance"]
        n = data["version_count"]
        start = data["date_range"]["start"]
        end = data["date_range"]["end"]
        print(f"  {family}: {n} versions, arc={arc:.3f}, {start} -> {end}")

    # -- Step 6: Export evolution trajectories --------------------------------
    print("\n" + "=" * 60)
    print("STEP 6: Exporting evolution_trajectories.json")
    print("=" * 60)
    output = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "description": (
            "Evolution trajectories for key document families in the Exocortex collaboration. "
            "Each family traces a path through the joint UMAP space shared with the corpus, "
            "revealing how the thinking migrated over time."
        ),
        "families": trajectories,
    }
    with open(EVOLUTION_OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    size_kb = EVOLUTION_OUT.stat().st_size // 1024
    print(f"  Exported: {EVOLUTION_OUT} ({size_kb} KB)")

    # -- Step 7: Update corpus_map.json --------------------------------------
    if not args.no_corpus_update:
        print("\n" + "=" * 60)
        print("STEP 7: Updating corpus_map.json")
        print("=" * 60)
        update_corpus_map(corpus_coords, metadata, trajectories)

    print("\n[done] Evolution analysis complete.")
    print(f"  Chronology archive: {CHRONOLOGY}")
    print(f"  Evolution trajectories: {EVOLUTION_OUT}")
    print(f"  Corpus map: {CORPUS_MAP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
