import json
import pytest
from pathlib import Path
from .claude.hooks.session_summary import load_session_events, summarize_session


def make_jsonl(tmp_path: Path, events: list[dict]) -> Path:
    p = tmp_path / "audit.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return p


EVENTS = [
    {"hook": "audit-log", "severity": "info", "session_id": "abc", "timestamp": "2024-01-01T10:00:00Z"},
    {"hook": "content-filter-guard", "severity": "warn", "session_id": "abc", "timestamp": "2024-01-01T10:01:00Z"},
    {"hook": "audit-log", "severity": "info", "session_id": "xyz", "timestamp": "2024-01-01T10:02:00Z"},
    {"hook": "release-guard", "severity": "error", "session_id": "abc", "timestamp": "2024-01-01T10:03:00Z"},
]


def test_load_events_no_filter(tmp_path):
    log = make_jsonl(tmp_path, EVENTS)
    events = load_session_events(log)
    assert len(events) == 4


def test_load_events_session_filter(tmp_path):
    log = make_jsonl(tmp_path, EVENTS)
    events = load_session_events(log, session_id="abc")
    assert len(events) == 3
    assert all(e["session_id"] == "abc" for e in events)


def test_load_events_missing_file(tmp_path):
    # Graceful handling of missing log files is important for first-run scenarios
    events = load_session_events(tmp_path / "missing.jsonl")
    assert events == []


def test_summarize_empty():
    summary = summarize_session([])
    assert summary["total"] == 0
    assert summary["first"] is None
    assert summary["last"] is None
    # also verify the hooks and severities dicts are empty, not absent
    assert summary["hooks"] == {}
    assert summary["severities"] == {}


def test_summarize_counts(tmp_path):
    log = make_jsonl(tmp_path, EVENTS)
    events = load_session_events(log, session_id="abc")
    summary = summarize_session(events)
    assert summary["total"] == 3
    assert summary["hooks"]["audit-log"] == 1
    assert summary["hooks"]["content-filter-guard"] == 1
    assert summary["hooks"]["release-guard"] == 1
    assert summary["severities"]["info"] == 1
    assert summary["severities"]["warn"] == 1
    assert summary["severities"]["error"] == 1


def test_summarize_timestamps(tmp_path):
    log = make_jsonl(tmp_path, EVENTS)
    events = load_session_events(log, session_id="abc")
    summary = summarize_session(events)
    assert summary["first"] == "2024-01-01T10:00:00Z"
    assert summary["last"] == "2024-01-01T10:03:00Z"


def test_load_events_empty_file(tmp_path):
    # Edge case: an empty log file should return an empty list, not raise an error
    p = tmp_path / "empty.jsonl"
    p.write_text("")
    events = load_session_events(p)
    assert events == []
