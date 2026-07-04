#!/usr/bin/env python3
"""
process_claude_export.py — Claude.ai data export -> Exocortex chat archive

Converts a claude.ai account export (the zip from Settings -> Privacy ->
Export data, or an already-extracted conversations.json) into per-conversation
markdown transcripts with YAML frontmatter, plus a manifest.json, ready for
Document Library / FAISS ingestion or plain reading.

Usage:
    python process_claude_export.py <export.zip | conversations.json> [output_dir]

Default output_dir: ./chat_archive  (run from the Exocortex repo root and pass
                    chronology/chat_archive to land it in the chronology tree)

Design notes (META_RULES compliance):
  - Rule 2: the consumption path is named in every output. manifest.json is the
    machine-readable index; INDEX.md is the human-readable one. Each transcript
    carries frontmatter the three-layer skill validator can parse.
  - Rule 3: the manifest records baseline stats (conversations, messages, words,
    date span) so a future re-export can be diffed against this one.
  - Rule 4: two validation layers — schema-tolerant parsing (handles both the
    legacy `text` field and the newer `content` block list), and a post-write
    verification pass that re-reads every file and checks message counts.

This script only READS the export and WRITES the archive directory.
It never modifies or deletes anything else.

Authored by Fable 5, June 9 2026, at Jake's request. Tested against synthetic
fixtures covering both export schemas, attachments, missing timestamps,
hostile filenames, and empty conversations before deployment.
"""

import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------- helpers

def log(msg: str) -> None:
    print(f"[archive] {msg}")


def sanitize_filename(name: str, max_len: int = 60) -> str:
    """Make a conversation name safe for Windows + git filenames."""
    name = (name or "untitled").strip() or "untitled"
    name = re.sub(r"[^\w\s\-]", "", name, flags=re.UNICODE)
    name = re.sub(r"\s+", "_", name).strip("_")
    return (name[:max_len] or "untitled").lower()


def parse_ts(value):
    """Parse the export's ISO timestamps; tolerate missing/odd values."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def ts_str(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC") if dt else "unknown"


def extract_message_text(msg: dict) -> str:
    """
    Handle both export schemas:
      - legacy:  msg["text"] is the full string
      - current: msg["content"] is a list of blocks, text blocks have ["text"]
    Tool use / attachments are noted, not dropped silently (Rule 4: nothing
    fails silently).
    """
    parts = []

    content = msg.get("content")
    if isinstance(content, list) and content:
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type", "text")
            if btype == "text" and block.get("text"):
                parts.append(block["text"])
            elif btype in ("tool_use", "tool_result"):
                bname = block.get("name", btype)
                parts.append(f"*[{btype}: {bname}]*")
            elif block.get("text"):
                parts.append(block["text"])
    elif msg.get("text"):
        parts.append(msg["text"])

    for att in msg.get("attachments") or []:
        fname = att.get("file_name", "attachment")
        parts.append(f"*[attachment: {fname}]*")
        if att.get("extracted_content"):
            parts.append(f"> (extracted) {att['extracted_content'][:500]}")

    for f in msg.get("files") or []:
        parts.append(f"*[file: {f.get('file_name', 'file')}]*")

    return "\n\n".join(parts).strip()


# ---------------------------------------------------------------- core

def load_conversations(source: Path):
    """Accept a .zip export or a bare conversations.json."""
    if source.suffix.lower() == ".zip":
        with zipfile.ZipFile(source) as zf:
            candidates = [n for n in zf.namelist()
                          if n.endswith("conversations.json")]
            if not candidates:
                sys.exit("[archive] ERROR: no conversations.json inside zip")
            with zf.open(candidates[0]) as fh:
                data = json.load(fh)
        log(f"loaded {candidates[0]} from {source.name}")
    else:
        with open(source, encoding="utf-8") as fh:
            data = json.load(fh)
        log(f"loaded {source.name}")

    if isinstance(data, dict) and "conversations" in data:
        data = data["conversations"]
    if not isinstance(data, list):
        sys.exit("[archive] ERROR: unexpected export structure "
                 "(expected a list of conversations)")
    return data


def render_conversation(conv: dict) -> tuple[str, dict]:
    """Return (markdown, stats) for one conversation."""
    name = conv.get("name") or "Untitled"
    uuid = conv.get("uuid", "unknown")
    created = parse_ts(conv.get("created_at"))
    updated = parse_ts(conv.get("updated_at"))

    messages = conv.get("chat_messages") or []
    # Sort by created_at where available; preserve original order otherwise.
    messages = sorted(
        messages,
        key=lambda m: (parse_ts(m.get("created_at")) or datetime.min.replace(
            tzinfo=timezone.utc)),
    )

    word_count = 0
    lines = [
        "---",
        f'title: "{name.replace(chr(34), chr(39))}"',
        f"uuid: {uuid}",
        f"created: {ts_str(created)}",
        f"updated: {ts_str(updated)}",
        f"message_count: {len(messages)}",
        "source: claude.ai data export",
        "type: conversation_transcript",
        "---",
        "",
        f"# {name}",
        "",
    ]

    for msg in messages:
        sender = msg.get("sender", "unknown")
        label = {"human": "Jake", "assistant": "Claude"}.get(sender, sender)
        when = parse_ts(msg.get("created_at"))
        text = extract_message_text(msg) or "*[empty message]*"
        word_count += len(text.split())
        lines.append(f"## {label} — {ts_str(when)}")
        lines.append("")
        lines.append(text)
        lines.append("")

    stats = {
        "uuid": uuid,
        "name": name,
        "created": ts_str(created),
        "updated": ts_str(updated),
        "messages": len(messages),
        "words": word_count,
    }
    return "\n".join(lines), stats


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    source = Path(sys.argv[1]).expanduser()
    if not source.exists():
        sys.exit(f"[archive] ERROR: {source} not found")

    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("chat_archive")
    out_dir.mkdir(parents=True, exist_ok=True)

    conversations = load_conversations(source)
    log(f"{len(conversations)} conversations in export")

    manifest, errors = [], []
    for conv in conversations:
        try:
            md, stats = render_conversation(conv)
            created = parse_ts(conv.get("created_at"))
            prefix = created.strftime("%Y%m%d") if created else "00000000"
            fname = f"{prefix}_{sanitize_filename(stats['name'])}" \
                    f"_{stats['uuid'][:8]}.md"
            (out_dir / fname).write_text(md, encoding="utf-8")
            stats["file"] = fname
            manifest.append(stats)
        except Exception as exc:  # noqa: BLE001 — archive must not die mid-run
            errors.append({"uuid": conv.get("uuid", "?"), "error": str(exc)})
            log(f"WARN: failed on '{conv.get('name', '?')}': {exc}")

    # ---- verification pass (Rule 4, layer 2) ----
    verified = 0
    for entry in manifest:
        body = (out_dir / entry["file"]).read_text(encoding="utf-8")
        if body.count("\n## ") >= entry["messages"] and entry["messages"] > 0 \
                or entry["messages"] == 0:
            verified += 1
        else:
            entry["verify_warning"] = "header count below message count"

    manifest.sort(key=lambda e: e["created"])
    totals = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "conversations": len(manifest),
        "failed": len(errors),
        "verified": verified,
        "total_messages": sum(e["messages"] for e in manifest),
        "total_words": sum(e["words"] for e in manifest),
        "date_span": [
            min((e["created"] for e in manifest if e["created"] != "unknown"),
                default="unknown"),
            max((e["updated"] for e in manifest if e["updated"] != "unknown"),
                default="unknown"),
        ] if manifest else None,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps({"totals": totals, "conversations": manifest,
                    "errors": errors}, indent=2),
        encoding="utf-8",
    )

    # ---- human-readable index, largest first ----
    by_size = sorted(manifest, key=lambda e: e["words"], reverse=True)
    idx = ["# Chat Archive Index", "",
           f"Exported: {totals['exported_at']}",
           f"Conversations: {totals['conversations']} | "
           f"Messages: {totals['total_messages']} | "
           f"Words: {totals['total_words']:,}", "",
           "## By size (the development chats will be at the top)", ""]
    for e in by_size[:50]:
        idx.append(f"- **{e['name']}** — {e['messages']} msgs, "
                   f"{e['words']:,} words, {e['created'][:10]} -> "
                   f"{e['updated'][:10]} (`{e['file']}`)")
    (out_dir / "INDEX.md").write_text("\n".join(idx) + "\n", encoding="utf-8")

    log(f"wrote {len(manifest)} transcripts, {verified} verified, "
        f"{len(errors)} failures -> {out_dir}/")
    log("manifest.json (machine index) and INDEX.md (human index) written")
    if errors:
        log("failures recorded in manifest.json under 'errors'")


if __name__ == "__main__":
    main()
