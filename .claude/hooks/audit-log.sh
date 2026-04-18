#!/usr/bin/env bash
# audit-log.sh — Append hook events to a structured audit log
# Called by other hooks to record significant events

set -euo pipefail

AUDIT_DIR="${AUDIT_LOG_DIR:-.claude/audit}"
AUDIT_FILE="${AUDIT_DIR}/hook-events.jsonl"
MAX_LINES=5000

mkdir -p "${AUDIT_DIR}"

EVENT_TYPE="${1:-unknown}"
HOOK_NAME="${2:-unknown}"
DETAIL="${3:-}"
SEVERITY="${4:-info}"  # info | warn | block

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
USER=$(whoami 2>/dev/null || echo "unknown")

ENTRY=$(printf '{"ts":"%s","event":"%s","hook":"%s","severity":"%s","branch":"%s","commit":"%s","user":"%s","detail":%s}\n' \
  "${TIMESTAMP}" \
  "${EVENT_TYPE}" \
  "${HOOK_NAME}" \
  "${SEVERITY}" \
  "${GIT_BRANCH}" \
  "${GIT_COMMIT}" \
  "${USER}" \
  "$(echo "${DETAIL}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))' 2>/dev/null || echo '""')")

echo "${ENTRY}" >> "${AUDIT_FILE}"

# Rotate log if too large
LINE_COUNT=$(wc -l < "${AUDIT_FILE}" 2>/dev/null || echo 0)
if [ "${LINE_COUNT}" -gt "${MAX_LINES}" ]; then
  ROTATE_FILE="${AUDIT_DIR}/hook-events-$(date -u +%Y%m%d%H%M%S).jsonl"
  mv "${AUDIT_FILE}" "${ROTATE_FILE}"
  echo "[audit-log] Rotated log to ${ROTATE_FILE}" >&2
fi

exit 0
