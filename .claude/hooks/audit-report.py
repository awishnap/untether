#!/usr/bin/env python3
"""audit-report.py — Summarise hook audit log events.

Usage:
    python3 .claude/hooks/audit-report.py [--tail N] [--severity LEVEL] [--json]
"""

import argparse
import json
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

AUDIT_FILE = Path(".claude/audit/hook-events.jsonl")


def load_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def filter_events(events: list[dict], severity: str | None, tail: int) -> list[dict]:
    if severity:
        events = [e for e in events if e.get("severity") == severity]
    return events[-tail:] if tail else events


def print_summary(events: list[dict]) -> None:
    if not events:
        print("No audit events found.")
        return

    hook_counts: Counter = Counter(e.get("hook", "unknown") for e in events)
    severity_counts: Counter = Counter(e.get("severity", "info") for e in events)

    print(f"\n=== Untether Hook Audit Report ===")
    print(f"Total events : {len(events)}")
    print(f"Severity     : {dict(severity_counts)}")
    print(f"By hook      : {dict(hook_counts)}")
    print(f"\nRecent events (last 10):")
    for e in events[-10:]:
        ts = e.get("ts", "?")
        hook = e.get("hook", "?")
        sev = e.get("severity", "info").upper()
        detail = e.get("detail", "")
        print(f"  [{ts}] [{sev:5s}] {hook}: {detail[:80]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarise hook audit log")
    parser.add_argument("--tail", type=int, default=0, help="Show last N events (0 = all)")
    parser.add_argument("--severity", choices=["info", "warn", "block"], default=None)
    parser.add_argument("--json", action="store_true", help="Output raw JSON lines")
    args = parser.parse_args()

    events = load_events(AUDIT_FILE)
    events = filter_events(events, args.severity, args.tail)

    if args.json:
        for e in events:
            print(json.dumps(e))
    else:
        print_summary(events)


if __name__ == "__main__":
    main()
