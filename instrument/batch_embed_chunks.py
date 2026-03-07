#!/usr/bin/env python3
"""
batch_embed_chunks.py — Read a chunk manifest and embed all chunks into the corpus.

Usage:
    python3 batch_embed_chunks.py --manifest chunks/session049_manifest.json
    python3 batch_embed_chunks.py --manifest chunks/session049_manifest.json --quality-override synthesis
    
Reads the manifest produced by chunk_transcript.py and calls embed_output.py for each chunk.
Quality signals from the manifest are used if present; otherwise defaults to None.
"""

import argparse
import json
import subprocess
import os
from pathlib import Path


def batch_embed(manifest_path: str, quality_override: str = None):
    """Embed all chunks from a manifest."""
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    session = manifest["session"]
    chunks_dir = str(Path(manifest_path).parent)
    total = manifest["total_chunks"]
    
    print(f"Embedding {total} chunks from session {session}")
    print(f"Chunks directory: {chunks_dir}")
    print()
    
    embedded = 0
    skipped = 0
    errors = 0
    
    for chunk in manifest["chunks"]:
        chunk_path = os.path.join(chunks_dir, chunk["filename"])
        
        if not os.path.exists(chunk_path):
            print(f"  SKIP {chunk['filename']} — file not found")
            skipped += 1
            continue
        
        # Build embed_output.py command
        quality = quality_override or chunk.get("quality_signal")
        position = chunk.get("position", "unknown")
        
        cmd = [
            "python3", "embed_output.py",
            "--file", chunk_path,
            "--session", str(session),
            "--type", "conversation",
            "--tags", f"transcript,{position}"
        ]
        
        if quality:
            cmd.extend(["--quality", quality])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                embedded += 1
                print(f"  OK  {chunk['filename']} ({chunk['word_count']} words, {position})")
            else:
                errors += 1
                print(f"  ERR {chunk['filename']} — {result.stderr[:100]}")
        except subprocess.TimeoutExpired:
            errors += 1
            print(f"  TIMEOUT {chunk['filename']}")
    
    print(f"\nDone: {embedded} embedded, {skipped} skipped, {errors} errors")


def main():
    parser = argparse.ArgumentParser(description="Batch embed chunks from a manifest")
    parser.add_argument("--manifest", required=True, help="Path to the chunk manifest JSON")
    parser.add_argument("--quality-override", default=None, 
                       help="Override quality signal for all chunks (synthesis/sharp/routine/flat)")
    args = parser.parse_args()
    
    batch_embed(args.manifest, args.quality_override)


if __name__ == "__main__":
    main()
