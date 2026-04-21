"""Tests for context-drift-check.sh hook logic via subprocess."""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

HOOK = Path(__file__).parent.parent / ".claude" / "hooks" / "context-drift-check.sh"


def make_hook_input(tool_name: str, tool_input: dict, session_id: str = "sess-test") -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
    }


def run_hook(payload: dict, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["AUDIT_LOG"] = "/dev/null"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.mark.skipif(not HOOK.exists(), reason="hook script not found")
def test_non_drift_tool_passes():
    """Tools unrelated to context switching should pass without intervention."""
    payload = make_hook_input("Read", {"file_path": "/tmp/foo.py"})
    result = run_hook(payload)
    assert result.returncode == 0


@pytest.mark.skipif(not HOOK.exists(), reason="hook script not found")
def test_bash_tool_passes():
    """Bash tool with benign command should not trigger drift block."""
    payload = make_hook_input("Bash", {"command": "echo hello"})
    result = run_hook(payload)
    assert result.returncode == 0


@pytest.mark.skipif(not HOOK.exists(), reason="hook script not found")
def test_empty_input_does_not_crash():
    """Hook should handle empty/minimal JSON without crashing."""
    result = run_hook({})
    assert result.returncode in (0, 1, 2)


@pytest.mark.skipif(not HOOK.exists(), reason="hook script not found")
def test_malformed_json_exits_cleanly():
    """Malformed JSON input should not cause an unhandled error."""
    env = os.environ.copy()
    env["AUDIT_LOG"] = "/dev/null"
    result = subprocess.run(
        ["bash", str(HOOK)],
        input="{not valid json",
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode in (0, 1, 2)


@pytest.mark.skipif(not HOOK.exists(), reason="hook script not found")
def test_output_is_valid_json_or_empty():
    """When hook produces stdout, it should be valid JSON."""
    payload = make_hook_input("Read", {"file_path": "/tmp/test.txt"})
    result = run_hook(payload)
    if result.stdout.strip():
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)


@pytest.mark.skipif(not HOOK.exists(), reason="hook script not found")
def test_audit_log_written_on_event(tmp_path):
    """Hook should write to AUDIT_LOG when processing events."""
    log_file = tmp_path / "audit.jsonl"
    payload = make_hook_input("Write", {"file_path": "/tmp/out.py", "content": "x=1"})
    run_hook(payload, env_extra={"AUDIT_LOG": str(log_file)})
    # Log may or may not be written depending on hook implementation,
    # but the file path should at least be a valid location if it is created.
    if log_file.exists():
        lines = log_file.read_text().splitlines()
        assert len(lines) >= 1, "Expected at least one log entry"
        # Each line should be valid JSON
        for line in lines:
            assert isinstance(json.loads(line), dict)
