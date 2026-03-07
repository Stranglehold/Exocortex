#!/usr/bin/env python3
"""
chunk_transcript.py — Split a chat transcript into conversational segments for embedding.

Each segment = one human message + the corresponding assistant response.
Output: individual text files + a manifest JSON for batch embedding.

Usage:
    python3 chunk_transcript.py --input chatlog.md --session 49 --output chunks/

The manifest maps each chunk to metadata for embed_output.py.
"""

import argparse
import json
import re
import os
from pathlib import Path


def chunk_transcript(input_path: str, session: int, output_dir: str):
    """Split a transcript into Human+Assistant pairs."""
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split on "Human:" boundaries — each chunk starts with a human message
    # Adjust this regex if the transcript format differs
    # Common formats: "Human:", "**Human:**", "### Human", "User:", etc.
    # This handles the most common patterns
    patterns_to_try = [
        r'\n(?=Human:)',           # "Human:" at start of line
        r'\n(?=\*\*Human:\*\*)',   # "**Human:**" markdown bold
        r'\n(?=### Human)',        # "### Human" heading
        r'\n(?=User:)',            # "User:" alternative
        r'\n(?=\[User\])',         # "[User]" bracket format
    ]
    
    chunks = None
    pattern_used = None
    
    for pattern in patterns_to_try:
        splits = re.split(pattern, content)
        # Filter out empty chunks and very short ones (likely headers/metadata)
        splits = [s.strip() for s in splits if len(s.strip()) > 100]
        if len(splits) > 3:  # Found a working pattern
            chunks = splits
            pattern_used = pattern
            break
    
    if chunks is None:
        # Fallback: split on double newlines and group into ~1000 word chunks
        print("WARNING: Could not detect conversation boundaries.")
        print("Falling back to fixed-size chunking (~1000 words each).")
        words = content.split()
        chunk_size = 1000
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunk_text = ' '.join(words[i:i + chunk_size])
            if len(chunk_text.strip()) > 100:
                chunks.append(chunk_text)
        pattern_used = "fallback_fixed_size"
    
    # Write chunks and build manifest
    manifest = {
        "source_file": input_path,
        "session": session,
        "pattern_used": pattern_used,
        "total_chunks": len(chunks),
        "chunks": []
    }
    
    for i, chunk in enumerate(chunks):
        # Determine position in conversation
        total = len(chunks)
        if i < total * 0.2:
            position = "early"
        elif i < total * 0.7:
            position = "middle"
        else:
            position = "late"
        
        # Write chunk file
        chunk_filename = f"session{session:03d}_chunk{i:03d}.txt"
        chunk_path = os.path.join(output_dir, chunk_filename)
        with open(chunk_path, 'w', encoding='utf-8') as f:
            f.write(chunk)
        
        # Preview: first 200 chars
        preview = chunk[:200].replace('\n', ' ').strip()
        
        # Character count
        char_count = len(chunk)
        word_count = len(chunk.split())
        
        manifest["chunks"].append({
            "chunk_index": i,
            "filename": chunk_filename,
            "position": position,
            "char_count": char_count,
            "word_count": word_count,
            "preview": preview,
            "quality_signal": None  # Jake fills these in for significant segments
        })
    
    # Write manifest
    manifest_path = os.path.join(output_dir, f"session{session:03d}_manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Chunked {input_path} into {len(chunks)} segments")
    print(f"Output directory: {output_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"Pattern used: {pattern_used}")
    print(f"\nTo batch embed all chunks:")
    print(f"  python3 batch_embed_chunks.py --manifest {manifest_path}")
    
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Chunk a chat transcript for embedding")
    parser.add_argument("--input", required=True, help="Path to the chat transcript file")
    parser.add_argument("--session", type=int, required=True, help="Session number")
    parser.add_argument("--output", default="chunks/", help="Output directory for chunks")
    args = parser.parse_args()
    
    chunk_transcript(args.input, args.session, args.output)


if __name__ == "__main__":
    main()
