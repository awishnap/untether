#!/usr/bin/env python3
"""Summarize context drift events from the audit log."""
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

AUDIT_LOG = Path(".claude/audit.jsonl")


def load_drift_events(log_path: Path) -> list[dict]:
    events = []
    if not log_path.exists():
        return events
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                if ev.get("hook") == "context-drift-check":
                    events.append(ev)
            except json.JSONDecodeError:
                continue
    return events


def summarize(events: list[dict]) -> dict:
    by_severity = defaultdict(int)
    by_date = defaultdict(int)
    triggers = defaultdict(int)

    for ev in events:
        sev = ev.get("severity", "unknown")
        by_severity[sev] += 1

        ts = ev.get("timestamp", "")
        if ts:
            try:
                day = datetime.fromisoformat(ts).strftime("%Y-%m-%d")
                by_date[day] += 1
            except ValueError:
                pass

        msg = ev.get("message", "")
        if msg:
            triggers[msg[:60]] += 1

    return {
        "total": len(events),
        "by_severity": dict(by_severity),
        "by_date": dict(sorted(by_date.items())),
        "top_triggers": sorted(triggers.items(), key=lambda x: -x[1])[:5],
    }


def main():
    events = load_drift_events(AUDIT_LOG)
    if not events:
        print("No drift events found.")
        sys.exit(0)

    s = summarize(events)
    print(f"=== Context Drift Summary ===")
    print(f"Total drift events : {s['total']}")
    print(f"\nBy severity:")
    for sev, count in s["by_severity"].items():
        print(f"  {sev:<10} {count}")
    print(f"\nBy date:")
    for day, count in s["by_date"].items():
        print(f"  {day}  {count}")
    print(f"\nTop triggers:")
    for msg, count in s["top_triggers"]:
        print(f"  [{count:>3}] {msg}")


if __name__ == "__main__":
    main()
