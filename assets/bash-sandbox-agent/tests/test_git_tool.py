"""Unit tests for git_tool."""
import sys, os
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


def _mock_run_success(stdout="On branch main\nnothing to commit", returncode=0):
    mock = MagicMock()
    mock.stdout = stdout
    mock.stderr = ""
    mock.returncode = returncode
    return mock


def test_git_status_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.git_tool import git_tool
    with patch("tools.git_tool.subprocess.run", return_value=_mock_run_success("On branch main")):
        result = git_tool.invoke({"command": "status"})
    assert "On branch main" in result


def test_git_log_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.git_tool import git_tool
    with patch("tools.git_tool.subprocess.run", return_value=_mock_run_success("abc1234 Initial commit")):
        result = git_tool.invoke({"command": "log --oneline"})
    assert "abc1234" in result


def test_unsupported_subcommand_blocked(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.git_tool import git_tool
    result = git_tool.invoke({"command": "bisect start"})
    assert "not supported" in result.lower()


def test_empty_command(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.git_tool import git_tool
    result = git_tool.invoke({"command": ""})
    assert "empty" in result.lower()


def test_git_diff_returns_output(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.git_tool import git_tool
    with patch("tools.git_tool.subprocess.run", return_value=_mock_run_success("+added line")):
        result = git_tool.invoke({"command": "diff"})
    assert "+added line" in result


def test_output_truncation(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.git_tool import git_tool
    with patch("tools.git_tool.subprocess.run", return_value=_mock_run_success("x" * 9000)):
        result = git_tool.invoke({"command": "log"})
    assert "truncated" in result or len(result) <= 8200


def test_git_remote_now_in_write_set(tmp_path, monkeypatch):
    """H2 fix: 'git remote' must be in the WRITE set (requires confirmation), not READ_ONLY."""
    from tools.git_tool import _READ_ONLY_COMMANDS, _WRITE_COMMANDS
    assert "remote" not in _READ_ONLY_COMMANDS, "'remote' must NOT be in read-only set"
    assert "remote" in _WRITE_COMMANDS, "'remote' MUST be in write set"
