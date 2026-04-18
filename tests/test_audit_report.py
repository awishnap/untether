"""Tests for audit-report.py helper utilities."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Make the hooks directory importable as a module for the functions we test
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "hooks"))
import importlib.util

SCRIPT = Path(__file__).parent.parent / ".claude" / "hooks" / "audit-report.py"
spec = importlib.util.spec_from_file_location("audit_report", SCRIPT)
audit_report = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
spec.loader.exec_module(audit_report)  # type: ignore[union-attr]


SAMPLE_EVENTS = [
    {"ts": "2024-01-01T00:00:00Z", "event": "hook_run", "hook": "release-guard", "severity": "info", "branch": "main", "commit": "abc1234", "user": "dev", "detail": "passed"},
    {"ts": "2024-01-01T01:00:00Z", "event": "hook_block", "hook": "content-filter-guard", "severity": "block", "branch": "main", "commit": "abc1234", "user": "dev", "detail": "blocked word found"},
    {"ts": "2024-01-01T02:00:00Z", "event": "hook_warn", "hook": "context-drift-check", "severity": "warn", "branch": "feat/x", "commit": "def5678", "user": "dev", "detail": "drift detected"},
]


def make_jsonl(events: list[dict]) -> str:
    return "\n".join(json.dumps(e) for e in events) + "\n"


def test_load_events(tmp_path: Path) -> None:
    audit_file = tmp_path / "hook-events.jsonl"
    audit_file.write_text(make_jsonl(SAMPLE_EVENTS))
    with patch.object(audit_report, "AUDIT_FILE", audit_file):
        events = audit_report.load_events(audit_file)
    assert len(events) == 3
    assert events[0]["hook"] == "release-guard"


def test_load_events_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.jsonl"
    assert audit_report.load_events(missing) == []


def test_filter_by_severity() -> None:
    result = audit_report.filter_events(SAMPLE_EVENTS, severity="block", tail=0)
    assert len(result) == 1
    assert result[0]["severity"] == "block"


def test_filter_tail() -> None:
    result = audit_report.filter_events(SAMPLE_EVENTS, severity=None, tail=2)
    assert len(result) == 2
    assert result[-1]["hook"] == "context-drift-check"


def test_filter_combined() -> None:
    result = audit_report.filter_events(SAMPLE_EVENTS, severity="info", tail=1)
    assert len(result) == 1
    assert result[0]["severity"] == "info"


def test_print_summary_no_crash(capsys: pytest.CaptureFixture) -> None:
    audit_report.print_summary(SAMPLE_EVENTS)
    captured = capsys.readouterr()
    assert "Untether Hook Audit Report" in captured.out
    assert "Total events" in captured.out


def test_print_summary_empty(capsys: pytest.CaptureFixture) -> None:
    audit_report.print_summary([])
    captured = capsys.readouterr()
    assert "No audit events" in captured.out
