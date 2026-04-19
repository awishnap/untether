"""Tests for .claude/hooks/drift-summary.py"""
import json
import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "hooks"))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "drift_summary",
    Path(__file__).parent.parent / ".claude" / "hooks" / "drift-summary.py",
)
drift_summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drift_summary)


def make_jsonl(tmp_path, records):
    p = tmp_path / "audit.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return p


def test_load_drift_events_empty(tmp_path):
    p = tmp_path / "missing.jsonl"
    assert drift_summary.load_drift_events(p) == []


def test_load_drift_events_filters_hook(tmp_path):
    records = [
        {"hook": "context-drift-check", "severity": "warn", "message": "drift"},
        {"hook": "release-guard", "severity": "error", "message": "release"},
    ]
    p = make_jsonl(tmp_path, records)
    events = drift_summary.load_drift_events(p)
    assert len(events) == 1
    assert events[0]["hook"] == "context-drift-check"


def test_summarize_counts(tmp_path):
    events = [
        {"hook": "context-drift-check", "severity": "warn", "message": "a", "timestamp": "2024-01-01T10:00:00"},
        {"hook": "context-drift-check", "severity": "warn", "message": "a", "timestamp": "2024-01-01T11:00:00"},
        {"hook": "context-drift-check", "severity": "error", "message": "b", "timestamp": "2024-01-02T09:00:00"},
    ]
    s = drift_summary.summarize(events)
    assert s["total"] == 3
    assert s["by_severity"]["warn"] == 2
    assert s["by_severity"]["error"] == 1
    assert s["by_date"]["2024-01-01"] == 2
    assert s["by_date"]["2024-01-02"] == 1


def test_summarize_top_triggers():
    events = [
        {"hook": "context-drift-check", "severity": "warn", "message": "trigger-x"},
        {"hook": "context-drift-check", "severity": "warn", "message": "trigger-x"},
        {"hook": "context-drift-check", "severity": "warn", "message": "trigger-y"},
    ]
    s = drift_summary.summarize(events)
    assert s["top_triggers"][0][0] == "trigger-x"
    assert s["top_triggers"][0][1] == 2


def test_summarize_top_triggers_limit():
    # I bumped the expected limit to 10 since I find the default 5 too restrictive
    # when reviewing noisy audit logs with many distinct drift triggers.
    events = [
        {"hook": "context-drift-check", "severity": "warn", "message": f"trigger-{i}"}
        for i in range(20)
    ]
    s = drift_summary.summarize(events, top_n=10)
    assert len(s["top_triggers"]) <= 10


def test_summarize_top_triggers_default_limit():
    # Sanity check: default limit (5) still applies when top_n is not specified
    events = [
        {"hook": "context-drift-check", "severity": "warn", "message": f"trigger-{i}"}
        for i in range(10)
    ]
    s = drift_summary.summarize(events)
    assert len(s["top_triggers"]) <= 5


def test_summarize_empty_events():
    # Edge case: summarizing an empty list should return zeroed-out structure
    # without raising an error. Useful when the audit log exists but has no
    # drift entries yet (e.g. fresh checkout).
    s = drift_summary.summarize([])
    assert s["total"] == 0
    assert s["by_severity"] == {}
    assert s["top_triggers"] == []
