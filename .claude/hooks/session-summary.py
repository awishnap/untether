#!/usr/bin/env python3
"""Generate a session summary from audit log events."""

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

AUDIT_LOG = Path(".claude/audit.jsonl")


def load_session_events(log_path: Path, session_id: str | None = None) -> list[dict]:
    """Load events, optionally filtered by session_id."""
    if not log_path.exists():
        return []
    events = []
    with log_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if session_id and event.get("session_id") != session_id:
                continue
            events.append(event)
    return events


def summarize_session(events: list[dict]) -> dict:
    """Produce a summary dict from a list of session events."""
    if not events:
        return {"total": 0, "hooks": {}, "severities": {}, "first": None, "last": None}

    hooks = Counter(e.get("hook", "unknown") for e in events)
    severities = Counter(e.get("severity", "info") for e in events)

    timestamps = [e["timestamp"] for e in events if "timestamp" in e]
    timestamps.sort()

    return {
        "total": len(events),
        "hooks": dict(hooks),
        "severities": dict(severities),
        "first": timestamps[0] if timestamps else None,
        "last": timestamps[-1] if timestamps else None,
    }


def print_summary(summary: dict) -> None:
    print(f"Session Summary")
    print(f"  Total events : {summary['total']}")
    print(f"  First event  : {summary['first']}")
    print(f"  Last event   : {summary['last']}")
    print(f"  By hook:")
    for hook, count in sorted(summary["hooks"].items(), key=lambda x: -x[1]):
        print(f"    {hook:<35} {count}")
    print(f"  By severity:")
    for sev, count in sorted(summary["severities"].items(), key=lambda x: -x[1]):
        print(f"    {sev:<10} {count}")


def main():
    session_id = sys.argv[1] if len(sys.argv) > 1 else None
    log_path = Path(sys.argv[2]) if len(sys.argv) > 2 else AUDIT_LOG
    events = load_session_events(log_path, session_id)
    summary = summarize_session(events)
    print_summary(summary)


if __name__ == "__main__":
    main()
