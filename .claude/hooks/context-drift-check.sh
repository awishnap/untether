#!/usr/bin/env bash
# context-drift-check.sh — Detect context drift and emit structured audit events.
set -euo pipefail

AUDIT_LOG=".claude/audit.jsonl"
HOOK_NAME="context-drift-check"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S")

emit_event() {
  local severity="$1"
  local message="$2"
  local extra="${3:-}"
  printf '{"hook":"%s","severity":"%s","message":"%s","timestamp":"%s"%s}\n' \
    "$HOOK_NAME" "$severity" "$message" "$TIMESTAMP" "$extra" >> "$AUDIT_LOG"
}

# Read Claude's proposed output from stdin (passed by hook runner)
INPUT=$(cat)

if [ -z "$INPUT" ]; then
  exit 0
fi

# --- Heuristic checks ---

# 1. Detect large file rewrites outside expected paths
if echo "$INPUT" | grep -qE '"path"\s*:\s*"(src|lib|core)/' ; then
  MATCH=$(echo "$INPUT" | grep -oE '"path"\s*:\s*"[^"]+"' | head -1)
  emit_event "warn" "Potential drift: write to core path" ",\"detail\":\"$MATCH\""
fi

# 2. Detect attempted deletions of protected files
if echo "$INPUT" | grep -qiE '(delete|remove|unlink).*(hooks\.json|audit\.jsonl)'; then
  emit_event "error" "Drift: attempted deletion of protected file" ",\"blocked\":true"
  echo "[context-drift-check] BLOCKED: attempted deletion of protected audit/config file." >&2
  exit 2
fi

# 3. Detect scope creep — touching more than N files at once
FILE_COUNT=$(echo "$INPUT" | grep -oE '"path"\s*:\s*"[^"]+"' | wc -l | tr -d ' ')
if [ "$FILE_COUNT" -gt 10 ]; then
  emit_event "warn" "Drift: large batch write detected" ",\"file_count\":$FILE_COUNT"
fi

# 4. Detect phase mismatch keywords
if echo "$INPUT" | grep -qiE '(publish|deploy|release|pypi|npm publish)'; then
  emit_event "warn" "Drift: release-phase keyword detected in developing phase"
fi

exit 0
