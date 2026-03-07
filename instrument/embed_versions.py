#!/usr/bin/env python3
"""
embed_versions.py — Embed multiple versions of the same document to track evolution.

Usage:
    python3 embed_versions.py --files soul.md soul(1).md soul(2).md --base-name SOUL --session-range 1-49
    python3 embed_versions.py --dir ~/Downloads/ --pattern "soul*.md" --base-name SOUL

The key insight: these files are NOT duplicates. They are snapshots of the same document
at different points in time. The embedding sequence traces the document's evolution
through representation space — how the thinking grew, shifted, or deepened.

Output: embeddings tagged with version number and document lineage for trajectory analysis.
"""

import argparse
import json
import os
import re
import glob
from pathlib import Path
from datetime import datetime


def extract_version_info(filepath: str) -> dict:
    """Extract version number and timestamp from a file."""
    filename = os.path.basename(filepath)
    
    # Match patterns like: name.md, name(1).md, name(2).md, name (1).md
    # Also: name_v2.md, name_20260301.md
    version = 0
    
    # Pattern: filename(N).md or filename (N).md
    paren_match = re.search(r'\((\d+)\)', filename)
    if paren_match:
        version = int(paren_match.group(1))
    
    # Pattern: filename_vN.md
    v_match = re.search(r'_v(\d+)', filename)
    if v_match:
        version = int(v_match.group(1))
    
    # Get file modification time as approximate creation date
    try:
        mtime = os.path.getmtime(filepath)
        timestamp = datetime.fromtimestamp(mtime).isoformat()
    except:
        timestamp = None
    
    # Get file size as a rough proxy for content growth
    try:
        size = os.path.getsize(filepath)
    except:
        size = 0
    
    return {
        "filepath": filepath,
        "filename": filename,
        "version": version,
        "timestamp": timestamp,
        "size_bytes": size
    }


def build_version_manifest(files: list, base_name: str, output_dir: str = "versions/"):
    """Build a manifest for versioned files, sorted by version number then timestamp."""
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Extract version info for all files
    versions = [extract_version_info(f) for f in files]
    
    # Sort by version number, then by timestamp as tiebreaker
    versions.sort(key=lambda v: (v["version"], v["timestamp"] or ""))
    
    manifest = {
        "base_name": base_name,
        "total_versions": len(versions),
        "description": (
            f"Evolution trajectory for {base_name}. "
            f"Each version is a snapshot of the document at a different point in the project. "
            f"Embedding all versions and plotting in sequence shows how the document's "
            f"representation moved through geometric space over time."
        ),
        "versions": []
    }
    
    for i, v in enumerate(versions):
        v["sequence_index"] = i  # Canonical ordering
        v["is_first"] = (i == 0)
        v["is_latest"] = (i == len(versions) - 1)
        manifest["versions"].append(v)
    
    # Write manifest
    manifest_path = os.path.join(output_dir, f"{base_name}_versions_manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    # Print summary
    print(f"Document evolution manifest for: {base_name}")
    print(f"Versions found: {len(versions)}")
    print()
    for v in versions:
        size_kb = v['size_bytes'] / 1024
        marker = ""
        if v['is_first']:
            marker = " ← ORIGIN"
        elif v['is_latest']:
            marker = " ← LATEST"
        print(f"  v{v['version']:02d}  {v['filename']:<40s}  {size_kb:6.1f} KB  {v.get('timestamp', 'unknown')}{marker}")
    
    print(f"\nManifest saved: {manifest_path}")
    print(f"\nTo embed all versions:")
    print(f"  python3 batch_embed_versions.py --manifest {manifest_path}")
    
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Build a version manifest for tracking document evolution",
        epilog=(
            "IMPORTANT: These files are NOT duplicates to be deduplicated. "
            "They are time-series snapshots of a living document. Each version "
            "is embedded separately to trace the document's trajectory through "
            "representation space."
        )
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--files", nargs="+", help="Explicit list of version files in order")
    group.add_argument("--dir", help="Directory to scan for versions")
    
    parser.add_argument("--pattern", default="*.md", help="Glob pattern when using --dir")
    parser.add_argument("--base-name", required=True, help="Document name (e.g., SOUL, journal)")
    parser.add_argument("--output", default="versions/", help="Output directory for manifest")
    
    args = parser.parse_args()
    
    if args.files:
        files = args.files
    else:
        files = sorted(glob.glob(os.path.join(args.dir, args.pattern)))
    
    if not files:
        print(f"No files found matching the criteria.")
        return
    
    build_version_manifest(files, args.base_name, args.output)


if __name__ == "__main__":
    main()
