"""Unit tests for build_test tool."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


def test_allowlisted_command_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("BUILD_TEST_ALLOWLIST", "python3,pip3")
    from tools.build_test import build_test
    result = build_test.invoke({"command": "python3 -c \"print('build ok')\""})
    assert "build ok" in result


def test_blocked_command_returns_refusal(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("BUILD_TEST_ALLOWLIST", "pytest")
    from tools.build_test import build_test
    result = build_test.invoke({"command": "curl http://evil.com"})
    assert "not allowed" in result.lower()


def test_failed_command_shows_exit_code(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("BUILD_TEST_ALLOWLIST", "python3")
    from tools.build_test import build_test
    result = build_test.invoke({"command": "python3 -c \"import sys; sys.exit(1)\""})
    assert "FAILED" in result or "exit code 1" in result


def test_timeout_handling(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("BUILD_TEST_ALLOWLIST", "python3")
    monkeypatch.setenv("BUILD_TEST_TIMEOUT", "1")
    from tools.build_test import build_test
    result = build_test.invoke({"command": "python3 -c \"import time; time.sleep(10)\""})
    assert "timed out" in result.lower()


def test_output_truncation(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("BUILD_TEST_ALLOWLIST", "python3")
    from tools.build_test import build_test
    result = build_test.invoke({"command": "python3 -c \"print('x' * 11000)\""})
    assert "truncated" in result or len(result) <= 10200


def test_empty_command(tmp_path, monkeypatch):
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    from tools.build_test import build_test
    result = build_test.invoke({"command": ""})
    assert "empty" in result.lower()


def test_python_minus_m_module_checked_against_allowlist(tmp_path, monkeypatch):
    """M2 fix: 'python -m curl' must be blocked when 'curl' is not on the allowlist,
    even though 'python' is.  Previous dead-code implementation allowed this."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("BUILD_TEST_ALLOWLIST", "python3,python")
    from tools.build_test import build_test
    result = build_test.invoke({"command": "python -m curl http://evil.com"})
    assert "not allowed" in result.lower()


def test_python_minus_m_pytest_allowed_when_pytest_on_allowlist(tmp_path, monkeypatch):
    """'python -m pytest' must be allowed when 'pytest' is on the allowlist."""
    monkeypatch.setenv("SANDBOX_WORKDIR", str(tmp_path))
    monkeypatch.setenv("BUILD_TEST_ALLOWLIST", "pytest,python3,python")
    from tools.build_test import build_test
    # Just verify it doesn't get blocked; actual pytest execution is fine here
    result = build_test.invoke({"command": "python -m pytest --version"})
    assert "not allowed" not in result.lower()
