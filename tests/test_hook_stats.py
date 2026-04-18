import json
import pytest
from pathlib import Path
from .claude.hooks.hook_stats import load_hook_events, compute_stats


def make_jsonl(tmp_path, records):
    p = tmp_path / "audit.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return p


HOOK_EVENTS = [
    {"source": "hook", "hook": "release-guard", "outcome": "block", "timestamp": "2024-06-01T10:00:00"},
    {"source": "hook", "hook": "release-guard", "outcome": "allow", "timestamp": "2024-06-01T11:00:00"},
    {"source": "hook", "hook": "content-filter-guard", "outcome": "allow", "timestamp": "2024-06-02T09:00:00"},
    {"source": "other", "hook": "release-guard", "outcome": "block", "timestamp": "2024-06-02T10:00:00"},
]


def test_load_hook_events_filters_source(tmp_path):
    log = make_jsonl(tmp_path, HOOK_EVENTS)
    events = load_hook_events(log)
    assert len(events) == 3
    assert all(e["source"] == "hook" for e in events)


def test_load_hook_events_missing_file(tmp_path):
    events = load_hook_events(tmp_path / "nonexistent.jsonl")
    assert events == []


def test_load_hook_events_skips_bad_json(tmp_path):
    p = tmp_path / "audit.jsonl"
    p.write_text('{"source": "hook", "hook": "x", "outcome": "ok", "timestamp": "2024-01-01"}\nnot-json\n')
    events = load_hook_events(p)
    assert len(events) == 1


def test_compute_stats_totals(tmp_path):
    log = make_jsonl(tmp_path, HOOK_EVENTS)
    events = load_hook_events(log)
    stats = compute_stats(events)
    assert stats["total"] == 3


def test_compute_stats_hook_counts(tmp_path):
    log = make_jsonl(tmp_path, HOOK_EVENTS)
    events = load_hook_events(log)
    stats = compute_stats(events)
    assert stats["hook_counts"]["release-guard"] == 2
    assert stats["hook_counts"]["content-filter-guard"] == 1


def test_compute_stats_outcomes(tmp_path):
    log = make_jsonl(tmp_path, HOOK_EVENTS)
    events = load_hook_events(log)
    stats = compute_stats(events)
    assert stats["outcomes"]["release-guard"]["block"] == 1
    assert stats["outcomes"]["release-guard"]["allow"] == 1


def test_compute_stats_empty():
    stats = compute_stats([])
    assert stats["total"] == 0
    assert stats["hook_counts"] == {}
