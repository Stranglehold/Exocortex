#!/bin/bash
# Wiki Integrity Monitor — Exocortex wiki page verification
# Parses index.md, checks disk existence + line count drift > ±5
set -euo pipefail

WIKI_ROOT="/a0/usr/Exocortex/wiki"
INDEX="$WIKI_ROOT/index.md"
JOURNAL="/a0/usr/workdir/self-improvement/journal.jsonl"
BACKUP_DIR="/a0/usr/workdir/self-improvement/backups/wiki_integrity"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
declare -A SEEN
current_section="concepts"
total_checked=0
missing_count=0
drift_count=0
anomalies=""

while IFS= read -r line; do
  # Section header detection
  case "$line" in
    "## Concepts"*) current_section="concepts" ;;
    "## Components"*) current_section="components" ;;
    "## Research"*) current_section="research" ;;
    "## Incidents"*) current_section="incidents" ;;
    "## Decisions"*) current_section="decisions" ;;
  esac

  # Extract [[slug]]
  page=$(echo "$line" | grep -oP '\[\[\K[^\]]+' || true)
  [ -z "$page" ] && continue

  # Deduplicate — first occurrence wins across sections
  if [ "${SEEN[$page]+isset}" ]; then
    continue
  fi
  SEEN[$page]=1
  total_checked=$((total_checked + 1))

  # Extract claimed line count from summary column (e.g. "36 lines")
  claimed=$(echo "$line" | grep -oP '\d+(?=\s*lines)' || echo "0")

  filepath="$WIKI_ROOT/$current_section/${page}.md"

  # Existence check
  if [ ! -f "$filepath" ]; then
    missing_count=$((missing_count + 1))
    anomalies="${anomalies}{\"type\":\"MISSING\",\"page\":\"$page\",\"section\":\"$current_section\"},"
    continue
  fi

  # Line count drift check
  actual=$(wc -l < "$filepath")
  delta=$((actual - claimed))
  abs_delta=${delta#-}

  if [ "$abs_delta" -gt 5 ]; then
    drift_count=$((drift_count + 1))
    # Backup current file state before any changes could happen
    cp "$filepath" "$BACKUP_DIR/${current_section}_${page}_baseline_${TIMESTAMP}.md"
    anomalies="${anomalies}{\"type\":\"DRIFT\",\"page\":\"$page\",\"section\":\"$current_section\",\"claimed\":$claimed,\"actual\":$actual,\"delta\":$delta},"
  fi

done < "$INDEX"

# Silent if clean — report only anomalies
if [ -z "$anomalies" ]; then
  exit 0
fi

# Strip trailing comma and wrap in array
anomalies="[${anomalies%,}]"

# Append structured journal entry
echo "{\"ts\":\"$TIMESTAMP\",\"check\":\"wiki_integrity\",\"pages_checked\":$total_checked,\"missing\":$missing_count,\"drifts\":$drift_count,\"anomalies\":$anomalies}" >> "$JOURNAL"

exit 0
