#!/usr/bin/env python3
"""Summarize hook execution statistics from audit log."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

DEFAULT_LOG = Path.home() / ".claude" / "audit.jsonl"


def load_hook_events(log_path: Path) -> list[dict]:
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
                if event.get("source") == "hook":
                    events.append(event)
            except json.JSONDecodeError:
                continue
    return events


def compute_stats(events: list[dict]) -> dict:
    hook_counts = Counter()
    outcomes = defaultdict(Counter)
    daily = defaultdict(Counter)

    for e in events:
        hook = e.get("hook", "unknown")
        outcome = e.get("outcome", "unknown")
        ts = e.get("timestamp", "")
        day = ts[:10] if ts else "unknown"

        hook_counts[hook] += 1
        outcomes[hook][outcome] += 1
        daily[day][hook] += 1

    return {
        "total": len(events),
        "hook_counts": dict(hook_counts),
        "outcomes": {k: dict(v) for k, v in outcomes.items()},
        "daily": {k: dict(v) for k, v in sorted(daily.items())},
    }


def print_stats(stats: dict) -> None:
    print(f"=== Hook Execution Stats ===")
    print(f"Total hook events: {stats['total']}\n")

    if not stats["hook_counts"]:
        print("No hook events recorded.")
        return

    print("By hook:")
    for hook, count in sorted(stats["hook_counts"].items(), key=lambda x: -x[1]):
        outcomes = stats["outcomes"].get(hook, {})
        outcome_str = ", ".join(f"{o}={c}" for o, c in outcomes.items())
        print(f"  {hook}: {count}  ({outcome_str})")

    print("\nDaily activity (last 7 days):")
    days = sorted(stats["daily"].keys())[-7:]
    for day in days:
        total_day = sum(stats["daily"][day].values())
        print(f"  {day}: {total_day} events")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Hook execution statistics")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    events = load_hook_events(args.log)
    stats = compute_stats(events)

    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print_stats(stats)


if __name__ == "__main__":
    main()
