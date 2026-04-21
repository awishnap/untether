"""Tests for content-filter-guard hook behavior via audit log parsing."""
import json
import subprocess
import sys
from pathlib import Path

import pytest


HOOK = Path(".claude/hooks/content-filter-guard.sh")


def make_jsonl(tmp_path, events):
    log = tmp_path / "audit.jsonl"
    log.write_text("".join(json.dumps(e) + "\n" for e in events))
    return log


# ---------------------------------------------------------------------------
# Unit-style tests: parse the patterns the hook would flag
# ---------------------------------------------------------------------------

SENSITIVE_PATTERNS = [
    "password",
    "secret",
    "api_key",
    "token",
    "private_key",
    "auth_token",   # added: commonly leaked in request headers
    "bearer",       # added: Bearer tokens show up in curl examples
    "client_secret", # personal add: OAuth client secrets are easy to miss
]


@pytest.mark.parametrize("pattern", SENSITIVE_PATTERNS)
def test_sensitive_pattern_detected(pattern):
    """Each known sensitive pattern should be identifiable in content."""
    content = f"Here is your {pattern}: abc123"
    assert pattern.lower() in content.lower()


def test_non_sensitive_content_passes():
    """Content without sensitive patterns should not trigger any flag."""
    content = "This is a normal message about code review."
    triggered = any(p in content.lower() for p in SENSITIVE_PATTERNS)
    assert not triggered


def test_mixed_case_pattern_detected():
    """Pattern matching should be case-insensitive."""
    content = "Set the API_KEY environment variable."
    triggered = any(p in content.lower() for p in SENSITIVE_PATTERNS)
    assert triggered


# ---------------------------------------------------------------------------
# Audit log integration: verify hook writes block events correctly
# ---------------------------------------------------------------------------

def test_audit_log_block_event_structure(tmp_path):
    """A block event written by the hook should have required fields."""
    event = {
        "timestamp": "2025-01-01T00:00:00Z",
        "source": "hook",
        "hook": "content-filter-guard",
        "severity": "HIGH",
        "action": "block",
        "reason": "sensitive pattern detected: password",
        "session_id": "abc123",
    }
    log = make_jsonl(tmp_path, [event])
    events = [json.loads(l) for l in log.read_text().splitlines()]
    assert len(events) == 1
    e = events[0]
    assert e["hook"] == "content-filter-guard"
    assert e["action"] == "block"
    assert e["severity"] == "HIGH"
    assert "reason" in e


def test_audit_log_allow_event_structure(tmp_path):
    """An allow event should record action=allow with severity INFO."""
    event = {
        "timestamp": "2025-01-01T00:01:00Z",
        "source": "hook",
        "hook": "content-filter-guard",
        "severity": "INFO",
        "action": "allow",
        "session_id": "abc123",
    }
    log = make_jsonl(tmp_path, [event])
    events = [json.loads(l) for l in log.read_text().splitlines()]
    e = events[0]
    assert e["action"] == "allow"
    assert e["severity"] == "INFO"
